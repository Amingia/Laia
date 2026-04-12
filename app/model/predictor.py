from sklearn.ensemble import RandomForestRegressor
import numpy as np
from app.data.fetcher import calculate_advanced_features

class AnalyticsPredictor:
    def __init__(self):
        # Modelos entrenados independientemente para anclar la predicción con fuerza matemática real.
        self.model_1h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=41)
        self.model_2h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=42)
        self.model_4h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=3, random_state=43)
        self.model_24h = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=4, random_state=44)
        self.is_trained = False

    def train(self, prices):
        if len(prices) < 96:
            return False

        X, y_1h, y_2h, y_4h, y_24h = [], [], [], [], []
        window = 24

        for i in range(len(prices) - window - 24):
            window_prices = prices[i:i+window]
            vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_prices)

            features = [
                window_prices[-1],
                window_prices[-1] - window_prices[-6],
                vol, mom, sma_6, sma_24, acc
            ]
            X.append(features)

            y_1h.append(prices[i+window + 0])
            y_2h.append(prices[i+window + 1])
            y_4h.append(prices[i+window + 3])
            y_24h.append(prices[i+window + 23])

        if len(X) > 0:
            self.model_1h.fit(X, y_1h)
            self.model_2h.fit(X, y_2h)
            self.model_4h.fit(X, y_4h)
            self.model_24h.fit(X, y_24h)
            self.is_trained = True
            return True
        return False

    def _interpolate(self, start_val, end_val, steps):
        """Interpola linealmente sin maquillajes ni ruido random (honestidad matemática)"""
        step_val = (end_val - start_val) / steps
        return [start_val + (step_val * i) for i in range(1, steps + 1)]

    def predict_horizons(self, current_prices):
        """Genera los 24 puntos: Ancla en 1, 2, 4 y 24, e interpola limpiamente el resto."""
        if not self.is_trained or len(current_prices) < 24:
            return None

        window_data = current_prices[-24:]
        vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_data)

        features = [
            window_data[-1],
            window_data[-1] - window_data[-6],
            vol, mom, sma_6, sma_24, acc
        ]

        # Puntos crudos, anclados
        p_now = current_prices[-1]
        p_1h = self.model_1h.predict([features])[0]
        p_2h = self.model_2h.predict([features])[0]
        p_4h = self.model_4h.predict([features])[0]
        p_24h = self.model_24h.predict([features])[0]

        base_vol_pct = max(0.001, vol / 100)

        b_now = 0.0
        b_1h = base_vol_pct * 1.5
        b_2h = base_vol_pct * 2.0
        b_4h = base_vol_pct * 2.5
        b_24h = base_vol_pct * 5.0

        # Construir array de 24 horas uniendo los nodos matemáticamente.
        interpolated_prices = []
        interpolated_bounds = []

        # 1. Del Ahora a +1h (1 paso)
        interpolated_prices.append(p_1h)
        interpolated_bounds.append(b_1h)

        # 2. De +1h a +2h (1 paso)
        interpolated_prices.append(p_2h)
        interpolated_bounds.append(b_2h)

        # 3. De +2h a +4h (2 pasos, index 2 y 3 -> es decir, hora 3 y 4)
        interpolated_prices.extend(self._interpolate(p_2h, p_4h, 2))
        interpolated_bounds.extend(self._interpolate(b_2h, b_4h, 2))

        # 4. De +4h a +24h (20 pasos, index 4 a 23 -> hora 5 a 24)
        interpolated_prices.extend(self._interpolate(p_4h, p_24h, 20))
        interpolated_bounds.extend(self._interpolate(b_4h, b_24h, 20))

        return {
            "p_1h": p_1h,
            "b_1h": b_1h,
            "p_2h": p_2h,
            "b_2h": b_2h,
            "p_4h": p_4h,
            "b_4h": b_4h,
            "p_24h": p_24h,
            "b_24h": b_24h,
            "interpolated_prices": interpolated_prices,
            "interpolated_bounds": interpolated_bounds
        }
