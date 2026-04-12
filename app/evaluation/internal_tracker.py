import json
import os
import time

HISTORY_FILE = "history.json"

class InternalValidator:
    def __init__(self):
        self.filename = HISTORY_FILE
        self.data = self._load_data()
        self.last_record_time = 0

    def _load_data(self):
        default = {
            "predictions": [],
            "metrics": {
                "total_evals": 0,
                "correct_directions": 0,
                "mae_ai": 0.0,
                "mae_baseline": 0.0 # Baseline es "el precio será exactamente igual al de hoy"
            }
        }
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_data(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"[Tracker Error] No se pudo guardar history.json: {e}")

    def record_new_prediction(self, current_price, predictions):
        """
        predictions es el dict del modelo de horizontes: {"p_1h": ..., "p_24h": ...}
        """
        now = time.time()
        # Solo registrar foto de métricas 1 vez cada 50 minutos
        if now - self.last_record_time < 3000:
            return

        if not predictions:
            return

        record = {
            "ts": now,
            "current_price": round(current_price, 2),
            "baseline": round(current_price, 2), # El modelo ingenuo asume que el precio nunca cambiará
            "p_1h": round(predictions["p_1h"], 2), "r_1h": None,
            "p_2h": round(predictions["p_2h"], 2), "r_2h": None,
            "p_4h": round(predictions["p_4h"], 2), "r_4h": None,
            "p_24h": round(predictions["p_24h"], 2), "r_24h": None,
            "evaluated": False
        }

        self.data["predictions"].append(record)
        if len(self.data["predictions"]) > 50:
            self.data["predictions"].pop(0)

        self.last_record_time = now
        self._save_data()

    def update_actuals(self, current_price):
        now = time.time()
        modified = False

        for record in self.data["predictions"]:
            if record["evaluated"]:
                continue

            time_passed = now - record["ts"]

            # Evaluación final 24h
            if record["r_24h"] is None and time_passed >= 86400:
                record["r_24h"] = round(current_price, 2)
                record["evaluated"] = True

                # Acierto de Dirección IA
                pred_diff = record["p_24h"] - record["current_price"]
                real_diff = current_price - record["current_price"]

                if (pred_diff > 0 and real_diff > 0) or (pred_diff < 0 and real_diff < 0):
                    self.data["metrics"]["correct_directions"] += 1

                # MAE de la IA en porcentaje absoluto
                error_pct_ai = abs(current_price - record["p_24h"]) / record["p_24h"] * 100
                self.data["metrics"]["mae_ai"] += error_pct_ai

                # MAE del Baseline (qué hubiera pasado si el usuario no hiciera caso a nadie)
                error_pct_base = abs(current_price - record["baseline"]) / record["baseline"] * 100
                self.data["metrics"]["mae_baseline"] += error_pct_base

                self.data["metrics"]["total_evals"] += 1
                modified = True

        if modified:
            self._save_data()

    def get_metrics(self):
        total = self.data["metrics"]["total_evals"]
        if total == 0:
            return {
                "total": 0,
                "accuracy": None,
                "mae_ai": None,
                "mae_baseline": None,
                "status": "Aún recopilando datos suficientes para evaluar la precisión real"
            }

        acc = (self.data["metrics"]["correct_directions"] / total) * 100
        mae_ai = self.data["metrics"]["mae_ai"] / total
        mae_baseline = self.data["metrics"]["mae_baseline"] / total

        # Conclusión transparente del sistema vs ingenuidad
        if mae_ai < mae_baseline:
            status = "La IA supera al mercado. MAE más bajo que Baseline."
            color = "green"
        elif mae_ai > mae_baseline:
            status = "La IA empeora al mercado. MAE más alto que Baseline."
            color = "red"
        else:
            status = "El modelo no aporta ventaja significativa frente al Baseline."
            color = "yellow"

        return {
            "total": total,
            "accuracy": round(acc, 1),
            "mae_ai": round(mae_ai, 2),
            "mae_baseline": round(mae_baseline, 2),
            "status": status,
            "color": color
        }
