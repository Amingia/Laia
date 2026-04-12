from sklearn.ensemble import RandomForestRegressor
import numpy as np
from app.data.fetcher import calculate_advanced_features

class AnalyticsPredictor:
    def __init__(self):
        # 4 Modelos separados independientes para cada horizonte predictivo (sin acumulación de error recursivo)
        # Ajustes: más árboles para estabilidad, pero `min_samples_leaf` conservador para evitar overfit.
        self.model_1h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=41)
        self.model_2h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=42)
        self.model_4h = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=3, random_state=43)
        self.model_24h = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=4, random_state=44)
        self.is_trained = False

    def train(self, prices):
        """
        Entrena los 4 modelos para predecir precios exactamente en su horizonte usando la misma ventana de features (24h atrás)
        """
        if len(prices) < 96: # Se requiere suficiente histórico para features + targets a 24h
            return False

        X, y_1h, y_2h, y_4h, y_24h = [], [], [], [], []
        window = 24

        for i in range(len(prices) - window - 24): # -24 para garantizar que existe el target a +24h
            window_prices = prices[i:i+window]
            vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_prices)

            features = [
                window_prices[-1],
                window_prices[-1] - window_prices[-6],
                vol, mom, sma_6, sma_24, acc
            ]
            X.append(features)

            # Targets futuros reales para la ventana i
            y_1h.append(prices[i+window + 0]) # El array prices es 0-indexed, window es longitud, así que index=window es +1 tick (+1h) si ignoramos el salto. En Binance klines el salto es exacto.
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
        """
        Devuelve exactamente los 4 puntos de anclaje reales sin maquillar con curvas interpoladas internamente.
        """
        if not self.is_trained or len(current_prices) < 24:
            return None

        window_data = current_prices[-24:]
        vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_data)

        features = [
            window_data[-1],
            window_data[-1] - window_data[-6],
            vol, mom, sma_6, sma_24, acc
        ]

        # Puntos crudos, sinceros.
        pred_1h = self.model_1h.predict([features])[0]
        pred_2h = self.model_2h.predict([features])[0]
        pred_4h = self.model_4h.predict([features])[0]
        pred_24h = self.model_24h.predict([features])[0]

        # Incertidumbre (Banda) puramente histórica
        # Para +1h la varianza es la de las últimas 24h.
        # Para +24h la varianza natural es ~ la volatilidad base multiplicada por la raíz del tiempo.
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
