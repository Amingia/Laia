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
            "predictions": [], # Almacenará {"ts": 123, "price": 60k, "pred_1h": 61k, "real_1h": None, ...}
            "metrics": {
                "total_evals": 0,
                "correct_directions": 0,
                "mae_accumulated": 0.0
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

    def record_new_prediction(self, current_price, prediction_array):
        """Guarda la predicción si ha pasado más de 1 hora desde la última (3600s)"""
        now = time.time()
        if now - self.last_record_time < 3500:
            return

        if not prediction_array or len(prediction_array) < 24:
            return

        p_1h = prediction_array[1]
        p_2h = prediction_array[2]
        p_4h = prediction_array[4]
        p_24h = prediction_array[23]

        record = {
            "ts": now,
            "current_price": round(current_price, 2),
            "p_1h": round(p_1h, 2), "r_1h": None,
            "p_2h": round(p_2h, 2), "r_2h": None,
            "p_4h": round(p_4h, 2), "r_4h": None,
            "p_24h": round(p_24h, 2), "r_24h": None,
            "evaluated": False
        }

        self.data["predictions"].append(record)
        # Mantener solo las últimas 50 predicciones en memoria para no inflar el json
        if len(self.data["predictions"]) > 50:
            self.data["predictions"].pop(0)

        self.last_record_time = now
        self._save_data()

    def update_actuals(self, current_price):
        """Verifica si alguna predicción pasada ya cumplió su tiempo para ser evaluada"""
        now = time.time()
        modified = False

        for record in self.data["predictions"]:
            if record["evaluated"]:
                continue

            time_passed = now - record["ts"]

            if record["r_1h"] is None and time_passed >= 3600:
                record["r_1h"] = round(current_price, 2)
                modified = True

            if record["r_2h"] is None and time_passed >= 7200:
                record["r_2h"] = round(current_price, 2)
                modified = True

            if record["r_4h"] is None and time_passed >= 14400:
                record["r_4h"] = round(current_price, 2)
                modified = True

            # Evaluación final a las 24h
            if record["r_24h"] is None and time_passed >= 86400:
                record["r_24h"] = round(current_price, 2)
                record["evaluated"] = True

                # Actualizar métricas globales
                pred_diff = record["p_24h"] - record["current_price"]
                real_diff = current_price - record["current_price"]

                if (pred_diff > 0 and real_diff > 0) or (pred_diff < 0 and real_diff < 0):
                    self.data["metrics"]["correct_directions"] += 1

                # MAE en %
                error_pct = abs(current_price - record["p_24h"]) / record["p_24h"] * 100
                self.data["metrics"]["mae_accumulated"] += error_pct
                self.data["metrics"]["total_evals"] += 1

                modified = True

        if modified:
            self._save_data()

    def get_metrics(self):
        total = self.data["metrics"]["total_evals"]
        if total == 0:
            return {"mae": None, "accuracy": None, "total": 0}

        acc = (self.data["metrics"]["correct_directions"] / total) * 100
        mae = self.data["metrics"]["mae_accumulated"] / total

        return {
            "mae": round(mae, 2),
            "accuracy": round(acc, 1),
            "total": total
        }
