from sklearn.ensemble import RandomForestRegressor
import numpy as np
from app.data.fetcher import calculate_advanced_features

class AnalyticsPredictor:
    def __init__(self):
        # RandomForest más denso y estable para análisis de serie temporal
        self.model = RandomForestRegressor(n_estimators=300, max_depth=10, min_samples_leaf=4, random_state=42)
        self.is_trained = False
        self.last_real_price = None
        self.last_prediction_array = []

    def train(self, prices, volumes=None):
        if len(prices) < 48: # Necesitamos histórico decente para features
            return False

        X, y = [], []
        window = 14 # 14 Horas previas como marco de entrada

        for i in range(len(prices) - window - 24): # Entrenar prediciendo el futuro real
            window_prices = prices[i:i+window]
            window_vols = volumes[i:i+window] if volumes else None

            vol, mom, sma_5, sma_14, acc, vol_r = calculate_advanced_features(window_prices, window_vols)

            features = [
                window_prices[-1], # Close price
                window_prices[-1] - window_prices[-2], # Cambio 1h
                vol, mom, sma_5, sma_14, acc, vol_r
            ]
            X.append(features)

            # Y es el precio a 1h vista de esa ventana (para modelo autoregresivo)
            y.append(prices[i+window])

        if len(X) > 0:
            self.model.fit(X, y)
            self.is_trained = True
            return True
        return False

    def predict_next_24h(self, current_prices, current_volumes=None):
        if not self.is_trained or len(current_prices) < 14:
            return None

        predictions = []
        upper_bounds = []
        lower_bounds = []

        window_data = current_prices[-14:].copy()
        window_vols = current_volumes[-14:].copy() if current_volumes else None

        # Volatilidad base para la banda de incertidumbre
        volatility, _, _, _, _, _ = calculate_advanced_features(window_data, window_vols)
        base_uncertainty = max(0.002, volatility / 100) # Mínimo 0.2% de incertidumbre

        # Guardamos el primer punto como el actual para continuidad perfecta
        predictions.append(current_prices[-1])
        upper_bounds.append(current_prices[-1])
        lower_bounds.append(current_prices[-1])

        for i in range(24): # 24 predicciones futuras
            vol, mom, sma_5, sma_14, acc, vol_r = calculate_advanced_features(window_data, window_vols)

            features = [
                window_data[-1],
                window_data[-1] - window_data[-2],
                vol, mom, sma_5, sma_14, acc, vol_r
            ]

            # Predicción cruda del modelo
            raw_pred = self.model.predict([features])[0]

            # Suavizado de curva: El modelo autoregresivo puro tiende a rebotar si hay mucho ruido.
            # Combinamos la predicción con el momentum reciente para que la curva tenga inercia natural.
            momentum_factor = 1 + (mom / 1000) # Muy ligero impacto direccional
            smooth_pred = raw_pred * momentum_factor

            # Cálculo de Banda de Confianza (Se ensancha cuanto más nos alejamos en el tiempo)
            hour_multiplier = 1 + (i * 0.05) # Aumenta un 5% de incertidumbre cada hora proyectada
            current_uncertainty = base_uncertainty * hour_multiplier

            upper = smooth_pred * (1 + current_uncertainty)
            lower = smooth_pred * (1 - current_uncertainty)

            predictions.append(smooth_pred)
            upper_bounds.append(upper)
            lower_bounds.append(lower)

            window_data.pop(0)
            window_data.append(smooth_pred)

            if window_vols:
                window_vols.pop(0)
                window_vols.append(window_vols[-1]) # Simulamos volumen constante en el futuro

        self.last_prediction_array = predictions
        self.last_real_price = current_prices[-1]

        return {
            "prices": predictions,
            "upper_bound": upper_bounds,
            "lower_bound": lower_bounds
        }
