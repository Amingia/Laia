from sklearn.ensemble import RandomForestRegressor
import numpy as np
import json
import os
import time
from app.data.fetcher import calculate_features

STATS_FILE = "stats.json"

class Predictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=3, random_state=42)
        self.is_trained = False
        self.last_prediction = None
        self.correction_factor = 1.0
        self.stats = self.load_stats()
        self.last_real_price = None

    def load_stats(self):
        default = {
            "total_predictions": 0,
            "correct_directions": 0,
        }
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r") as f:
                    data = json.load(f)
                    # Migración: solo queremos total_predictions y correct_directions
                    return {
                        "total_predictions": data.get("total_predictions", 0),
                        "correct_directions": data.get("correct_directions", 0)
                    }
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

        volatility, _, _, _, _ = calculate_features(window_data)
        vol_factor = max(0.001, volatility / 100)

        for i in range(24):
            vol, mom, sma_c, sma_m, acc = calculate_features(window_data)
            features = window_data[-5:] + [vol, mom, sma_c, acc]

            base_pred = self.model.predict([features])[0]
            corrected_pred = base_pred * self.correction_factor
            noise = np.random.normal(0, vol_factor)
            final_pred = corrected_pred * (1 + noise)

            predictions.append(final_pred)
            window_data.pop(0)
            window_data.append(final_pred)

        self.last_prediction = predictions[0]
        self.last_real_price = current_prices[-1]
        return predictions

    def update_correction(self, actual_price):
        if self.last_prediction is not None and self.last_real_price is not None and actual_price > 0:
            predicted_direction = self.last_prediction - self.last_real_price
            actual_direction = actual_price - self.last_real_price

            if predicted_direction != 0 and actual_direction != 0:
                self.stats["total_predictions"] += 1

                if (predicted_direction > 0 and actual_direction > 0) or (predicted_direction < 0 and actual_direction < 0):
                    self.stats["correct_directions"] += 1
                    self.correction_factor += (1.0 - self.correction_factor) * 0.02
                else:
                    error_pct = (actual_price - self.last_prediction) / self.last_prediction
                    multiplier = 0.8 if abs(error_pct) > 0.01 else 0.3
                    self.correction_factor += error_pct * multiplier

                self.save_stats()

        self.correction_factor = max(0.95, min(1.05, self.correction_factor))

    def get_metrics(self):
        """Devuelve solo lo esencial y comprensible."""
        total = self.stats["total_predictions"]
        acc = (self.stats["correct_directions"] / total * 100) if total > 0 else 0.0

        return {
            "accuracy": round(acc, 1),
            "total": total
        }
