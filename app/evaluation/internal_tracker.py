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
                "1h": {"evals": 0, "correct": 0, "mae_ai": 0.0, "mae_base": 0.0},
                "2h": {"evals": 0, "correct": 0, "mae_ai": 0.0, "mae_base": 0.0},
                "4h": {"evals": 0, "correct": 0, "mae_ai": 0.0, "mae_base": 0.0},
                "24h": {"evals": 0, "correct": 0, "mae_ai": 0.0, "mae_base": 0.0}
            }
        }
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    data = json.load(f)
                    # Saneamiento por si el json viene de la v10 (incompatible)
                    if "1h" not in data.get("metrics", {}):
                        print("[Tracker] Estructura v10 detectada en history.json. Reiniciando a v11.")
                        return default
                    return data
            except Exception as e:
                print(f"[Tracker] Error leyendo history.json: {e}. Creando nuevo.")
                return default
        return default

    def _save_data(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"[Tracker Error] No se pudo guardar history.json: {e}")

    def record_new_prediction(self, current_price, predictions):
        now = time.time()
        # Grabar una predicción cada hora (3500s de margen por si el cron baila un poco)
        if now - self.last_record_time < 3500:
            return

        if not predictions:
            return

        record = {
            "ts": now,
            "current_price": round(current_price, 2),
            "baseline": round(current_price, 2), # El baseline es el precio inalterado
            "p_1h": round(predictions["p_1h"], 2), "r_1h": None,
            "p_2h": round(predictions["p_2h"], 2), "r_2h": None,
            "p_4h": round(predictions["p_4h"], 2), "r_4h": None,
            "p_24h": round(predictions["p_24h"], 2), "r_24h": None
        }

        self.data["predictions"].append(record)
        # Límite de seguridad para no explotar la RAM/JSON (ej. 100 horas de historial pendiente)
        if len(self.data["predictions"]) > 100:
            self.data["predictions"].pop(0)

        self.last_record_time = now
        self._save_data()
        print(f"[Tracker] Nueva foto de predicciones registrada. {len(self.data['predictions'])} en cola.")

    def _evaluate_horizon(self, record, current_price, target_key, real_key, metrics_key):
        """Evalúa un horizonte temporal específico y actualiza las métricas globales si no se había evaluado aún."""
        if record[real_key] is None:
            record[real_key] = round(current_price, 2)

            pred_diff = record[target_key] - record["current_price"]
            real_diff = current_price - record["current_price"]

            if (pred_diff > 0 and real_diff > 0) or (pred_diff < 0 and real_diff < 0):
                self.data["metrics"][metrics_key]["correct"] += 1

            error_ai = abs(current_price - record[target_key]) / record[target_key] * 100
            error_base = abs(current_price - record["baseline"]) / record["baseline"] * 100

            self.data["metrics"][metrics_key]["mae_ai"] += error_ai
            self.data["metrics"][metrics_key]["mae_base"] += error_base
            self.data["metrics"][metrics_key]["evals"] += 1

            print(f"[Tracker] Evaluación {metrics_key} completada. Error IA: {error_ai:.2f}% | Base: {error_base:.2f}%")
            return True
        return False

    def update_actuals(self, current_price):
        now = time.time()
        modified = False

        for record in self.data["predictions"]:
            time_passed = now - record["ts"]

            # Evaluación Parcial +1h (A los 3600 segundos)
            if time_passed >= 3600 and time_passed < 7200:
                if self._evaluate_horizon(record, current_price, "p_1h", "r_1h", "1h"):
                    modified = True

            # Evaluación Parcial +2h (7200s)
            if time_passed >= 7200 and time_passed < 14400:
                if self._evaluate_horizon(record, current_price, "p_2h", "r_2h", "2h"):
                    modified = True

            # Evaluación Parcial +4h (14400s)
            if time_passed >= 14400 and time_passed < 86400:
                if self._evaluate_horizon(record, current_price, "p_4h", "r_4h", "4h"):
                    modified = True

            # Evaluación Final +24h (86400s)
            if time_passed >= 86400:
                if self._evaluate_horizon(record, current_price, "p_24h", "r_24h", "24h"):
                    modified = True

        if modified:
            self._save_data()

    def get_metrics(self):
        """Devuelve el estado de la auditoría estructurado para la UI."""
        results = {}

        for horizon, data in self.data["metrics"].items():
            total = data["evals"]
            if total == 0:
                results[horizon] = {"status": "pending", "evals": 0}
            else:
                acc = (data["correct"] / total) * 100
                mae_ai = data["mae_ai"] / total
                mae_base = data["mae_base"] / total
                color = "green" if mae_ai < mae_base else "red"

                results[horizon] = {
                    "status": "ready",
                    "evals": total,
                    "accuracy": round(acc, 1),
                    "mae_ai": round(mae_ai, 2),
                    "mae_base": round(mae_base, 2),
                    "color": color
                }

        return results
