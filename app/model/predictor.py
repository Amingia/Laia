from sklearn.ensemble import RandomForestRegressor
import numpy as np
from app.data.fetcher import calculate_features

class Predictor:
    def __init__(self):
        # Modelo un poco más robusto pero igual de rápido
        self.model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        self.is_trained = False
        self.last_prediction = None
        self.correction_factor = 1.0

        # Métricas para el Dashboard
        self.total_predictions = 0
        self.correct_directions = 0
        self.last_real_price = None

    def train(self, prices):
        if len(prices) < 24:
            return

        X = []
        y = []
        window = 5
        for i in range(len(prices) - window):
            window_prices = prices[i:i+window]
            # Extraemos las características del histórico
            volatility, momentum, sma = calculate_features(window_prices)
            # Entrenamos con [p1, p2, p3, p4, p5, volatilidad, momentum, sma]
            features = window_prices + [volatility, momentum, sma]

            X.append(features)
            y.append(prices[i+window])

        if len(X) > 0:
            self.model.fit(X, y)
            self.is_trained = True

    def predict_next_24h(self, current_prices):
        if not self.is_trained or len(current_prices) < 5:
            last_price = current_prices[-1] if current_prices else 60000
            return [last_price * (1 + np.random.normal(0, 0.001)) for _ in range(24)]

        predictions = []
        window_data = current_prices[-5:].copy()

        for _ in range(24):
            volatility, momentum, sma = calculate_features(window_data)
            features = window_data + [volatility, momentum, sma]

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
            # Comprobar si acertamos la dirección
            predicted_direction = self.last_prediction - self.last_real_price
            actual_direction = actual_price - self.last_real_price

            # Ignoramos cambios planos
            if predicted_direction != 0 and actual_direction != 0:
                self.total_predictions += 1
                if (predicted_direction > 0 and actual_direction > 0) or (predicted_direction < 0 and actual_direction < 0):
                    self.correct_directions += 1
                    # Acierto -> Estabilizar corrección acercándola a 1.0 suavemente
                    self.correction_factor += (1.0 - self.correction_factor) * 0.05
                else:
                    # Fallo -> Ajuste más agresivo basado en la magnitud del error
                    error = (actual_price - self.last_prediction) / self.last_prediction
                    # Ajuste agresivo si el error es grande
                    multiplier = 0.5 if abs(error) > 0.02 else 0.2
                    self.correction_factor += error * multiplier

        # Limitar la corrección para evitar desestabilización extrema
        self.correction_factor = max(0.90, min(1.10, self.correction_factor))

    def get_accuracy(self):
        if self.total_predictions == 0:
            return 0.0
        return (self.correct_directions / self.total_predictions) * 100
