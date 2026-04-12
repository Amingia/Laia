from sklearn.ensemble import RandomForestRegressor
import numpy as np
import json
import os
import time
from app.data.fetcher import calculate_features

STATS_FILE = "stats.json"

class Predictor:
    def __init__(self):
        # Modelo ajustado para no saltar con el ruido (más estimadores, min_samples_leaf mayor)
        self.model = RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=3, random_state=42)
        self.is_trained = False
        self.last_prediction = None
        self.correction_factor = 1.0

        # Persistencia
        self.stats = self.load_stats()
        self.last_real_price = None

    def load_stats(self):
        default = {
            "total_predictions": 0,
            "correct_directions": 0,
            "mae_acumulado": 0.0,
            "racha_actual": 0,
            "ultima_recalibracion": time.time()
        }
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r") as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_stats(self):
        with open(STATS_FILE, "w") as f:
            json.dump(self.stats, f)

    def train(self, prices):
        if len(prices) < 24:
            return

        X, y = [], []
        window = 5
        for i in range(len(prices) - window):
            window_prices = prices[i:i+window]
            volatility, momentum, sma_c, sma_m, acc = calculate_features(window_prices)
            features = window_prices + [volatility, momentum, sma_c, acc]
            X.append(features)
            y.append(prices[i+window])

        if len(X) > 0:
            self.model.fit(X, y)
            self.is_trained = True

    def predict_next_24h(self, current_prices):
        if not self.is_trained or len(current_prices) < 10:
            last_price = current_prices[-1] if current_prices else 65000
            return [last_price * (1 + np.random.normal(0, 0.0005)) for _ in range(24)]

        predictions = []
        window_data = current_prices[-10:].copy()

        for _ in range(24):
            vol, mom, sma_c, sma_m, acc = calculate_features(window_data)
            features = window_data[-5:] + [vol, mom, sma_c, acc]

            pred = self.model.predict([features])[0]
            pred = pred * self.correction_factor
            predictions.append(pred)

            window_data.pop(0)
            window_data.append(pred)

        self.last_prediction = predictions[0]
        self.last_real_price = current_prices[-1]

        return predictions

    def update_correction(self, actual_price):
        if self.last_prediction is not None and self.last_real_price is not None and actual_price > 0:
            predicted_direction = self.last_prediction - self.last_real_price
            actual_direction = actual_price - self.last_real_price

            error_abs = abs(actual_price - self.last_prediction)

            if predicted_direction != 0 and actual_direction != 0:
                self.stats["total_predictions"] += 1
                self.stats["mae_acumulado"] += error_abs

                # Evaluación de acierto de dirección
                if (predicted_direction > 0 and actual_direction > 0) or (predicted_direction < 0 and actual_direction < 0):
                    self.stats["correct_directions"] += 1
                    self.stats["racha_actual"] += 1 if self.stats["racha_actual"] >= 0 else (1 - self.stats["racha_actual"])
                    # Acierto: Suavizar la corrección
                    self.correction_factor += (1.0 - self.correction_factor) * 0.02
                else:
                    self.stats["racha_actual"] = -1 if self.stats["racha_actual"] >= 0 else self.stats["racha_actual"] - 1
                    # Fallo: Ajustar fuertemente basado en porcentaje de error
                    error_pct = (actual_price - self.last_prediction) / self.last_prediction
                    multiplier = 0.8 if abs(error_pct) > 0.01 else 0.3 # Más agresivo si el error es de >1%
                    self.correction_factor += error_pct * multiplier
                    self.stats["ultima_recalibracion"] = time.time()

                self.save_stats()

        # Hard limit de estabilización
        self.correction_factor = max(0.95, min(1.05, self.correction_factor))

    def get_metrics(self):
        total = self.stats["total_predictions"]
        acc = (self.stats["correct_directions"] / total * 100) if total > 0 else 0.0
        mae = (self.stats["mae_acumulado"] / total) if total > 0 else 0.0

        # Determinar nivel de estabilidad basado en la racha y acierto
        estabilidad = "Estable"
        if acc < 40 or self.stats["racha_actual"] < -3:
            estabilidad = "Recalibrando"
        elif acc > 60 and self.stats["racha_actual"] > 2:
            estabilidad = "Alta Precisión"

        return {
            "accuracy": round(acc, 1),
            "mae": round(mae, 2),
            "total": total,
            "racha": self.stats["racha_actual"],
            "estabilidad": estabilidad,
            "factor_correccion": round(self.correction_factor, 4)
        }
