from sklearn.ensemble import RandomForestRegressor
import numpy as np
from app.data.fetcher import calculate_advanced_features

class AnalyticsPredictor:
    def __init__(self):
        # RandomForest con n_estimators moderado y muestras hojas ajustadas para no sobrerreaccionar
        self.model = RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=4, random_state=42)
        self.is_trained = False

    def train(self, prices):
        if len(prices) < 48:
            return False

        X, y = [], []
        window = 24

        for i in range(len(prices) - window - 24):
            window_prices = prices[i:i+window]
            vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_prices)

            features = [
                window_prices[-1],
                window_prices[-1] - window_prices[-6], # Diferencia corto plazo
                vol, mom, sma_6, sma_24, acc
            ]
            X.append(features)
            y.append(prices[i+window])

        if len(X) > 0:
            self.model.fit(X, y)
            self.is_trained = True
            return True
        return False

    def predict_next_24h(self, current_prices):
        if not self.is_trained or len(current_prices) < 24:
            return None

        predictions = []
        upper_bounds = []
        lower_bounds = []

        window_data = current_prices[-24:].copy()

        # Volatilidad base del mercado en las últimas 24 horas reales
        base_volatility, _, _, _, _ = calculate_advanced_features(window_data)
        vol_factor = max(0.001, base_volatility / 100) # Base mínima de ruido

        # El primer punto es literalmente el precio "AHORA" para asegurar un empalme perfecto sin saltos en el gráfico
        now_price = current_prices[-1]
        predictions.append(now_price)
        upper_bounds.append(now_price)
        lower_bounds.append(now_price)

        last_prediction = now_price

        for i in range(1, 25): # +1h hasta +24h
            vol, mom, sma_6, sma_24, acc = calculate_advanced_features(window_data)

            features = [
                window_data[-1],
                window_data[-1] - window_data[-6],
                vol, mom, sma_6, sma_24, acc
            ]

            raw_pred = self.model.predict([features])[0]

            # En vez de un Random Walk ruidoso, usamos "inercia" + "volatilidad histórica" para la textura
            # Esto evita que la curva parezca un encefalograma plano, pero no la desvirtúa
            # Simulamos el movimiento con base en la volatilidad real y la desviación de la tendencia
            trend_direction = 1 if raw_pred > last_prediction else -1

            # La inyección estocástica es muy leve y guiada por la tendencia (no es puro ruido)
            market_noise = np.random.normal(0, vol_factor * 0.2) * now_price
            smooth_pred = raw_pred + (market_noise * trend_direction)

            # Banda de Confianza matemática
            # Crece un 4% de incertidumbre base cada hora + el factor de volatilidad actual
            uncertainty_multiplier = 1 + (i * 0.04)
            current_uncertainty = vol_factor * uncertainty_multiplier

            upper = smooth_pred * (1 + current_uncertainty)
            lower = smooth_pred * (1 - current_uncertainty)

            predictions.append(smooth_pred)
            upper_bounds.append(upper)
            lower_bounds.append(lower)

            window_data.pop(0)
            window_data.append(smooth_pred)
            last_prediction = smooth_pred

        return {
            "prices": predictions,
            "upper_bound": upper_bounds,
            "lower_bound": lower_bounds
        }
