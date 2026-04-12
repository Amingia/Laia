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
                    if "1h" not in data.get("metrics", {}):
                        print("[Tracker] Estructura antigua detectada. Saneando history.json...")
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

    def record_new_prediction(self, current_price, predictions_obj):
        """Graba una predicción si ha pasado más de 1 hora desde la última foto (3500s por seguridad de cron)"""
        now = time.time()
        if now - self.last_record_time < 3500:
            return

        if not predictions_obj:
            return

        record = {
            "ts": now,
            "current_price": round(current_price, 2),
            "baseline": round(current_price, 2),
            "p_1h": round(predictions_obj["p_1h"], 2), "r_1h": None,
            "p_2h": round(predictions_obj["p_2h"], 2), "r_2h": None,
            "p_4h": round(predictions_obj["p_4h"], 2), "r_4h": None,
            "p_24h": round(predictions_obj["p_24h"], 2), "r_24h": None
        }

        self.data["predictions"].append(record)
        # Limite sano para RAM/Disco de 100 horas de historial flotante
        if len(self.data["predictions"]) > 100:
            self.data["predictions"].pop(0)

        self.last_record_time = now
        self._save_data()
        print(f"[Auditoría] Snapshot de predicción guardada en log. {len(self.data['predictions'])} registros evaluándose.")

    def _evaluate_horizon(self, record, current_price, target_key, real_key, metrics_key):
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

            print(f"[Auditoría] Horizonte +{metrics_key} maduró. IA vs Base: {error_ai:.2f}% | {error_base:.2f}%")
            return True
        return False

    def update_actuals(self, current_price):
        """Dispara evaluación si los timestamps han madurado (+1, +2, +4, +24)"""
        now = time.time()
        modified = False

        for record in self.data["predictions"]:
            time_passed = now - record["ts"]

            if time_passed >= 3600 and time_passed < 7200:
                if self._evaluate_horizon(record, current_price, "p_1h", "r_1h", "1h"):
                    modified = True

            if time_passed >= 7200 and time_passed < 14400:
                if self._evaluate_horizon(record, current_price, "p_2h", "r_2h", "2h"):
                    modified = True

            if time_passed >= 14400 and time_passed < 86400:
                if self._evaluate_horizon(record, current_price, "p_4h", "r_4h", "4h"):
                    modified = True

            if time_passed >= 86400:
                if self._evaluate_horizon(record, current_price, "p_24h", "r_24h", "24h"):
                    modified = True

        if modified:
            self._save_data()

    def get_metrics(self):
        """Devuelve desglose de auditoría por horizonte temporal y un resumen global"""
        results = {}
        total_evals_global = 0

        for horizon, data in self.data["metrics"].items():
            total = data["evals"]
            total_evals_global += total
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

        results["total_evals_global"] = total_evals_global
        return results
