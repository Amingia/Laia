from sklearn.ensemble import RandomForestRegressor
from app.data.fetcher import calculate_advanced_features

class AnalyticsPredictor:
    def __init__(self):
        # 4 Modelos separados con hiperparámetros defensivos para evitar overfit.
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

            # Anclajes en los datos que pasaron (para retro-entrenar)
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

    def predict_horizons(self, current_prices):
        if not self.is_trained or len(current_prices) < 24:
            return None

        window_data = current_prices[-24:]
        vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_data)

        features = [
            window_data[-1],
            window_data[-1] - window_data[-6],
            vol, mom, sma_6, sma_24, acc
        ]

        # Predicción limpia. Cero estocasticidad artificial.
        pred_1h = self.model_1h.predict([features])[0]
        pred_2h = self.model_2h.predict([features])[0]
        pred_4h = self.model_4h.predict([features])[0]
        pred_24h = self.model_24h.predict([features])[0]

        base_vol_pct = max(0.001, vol / 100)

        return {
            "p_1h": pred_1h,
            "b_1h": base_vol_pct * 1.5,
            "p_2h": pred_2h,
            "b_2h": base_vol_pct * 2.0,
            "p_4h": pred_4h,
            "b_4h": base_vol_pct * 2.5,
            "p_24h": pred_24h,
            "b_24h": base_vol_pct * 5.0
        }
