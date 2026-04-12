from sklearn.ensemble import RandomForestRegressor
import numpy as np

class Predictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        self.last_prediction = None
        self.correction_factor = 1.0

    def train(self, prices):
        if len(prices) < 24:
            return

        X = []
        y = []
        # Usamos las 5 horas anteriores para predecir la siguiente
        window = 5
        for i in range(len(prices) - window):
            X.append(prices[i:i+window])
            y.append(prices[i+window])

        if len(X) > 0:
            self.model.fit(X, y)
            self.is_trained = True

    def predict_next_24h(self, current_prices):
        """Predice las siguientes 24 horas usando modelo autorregresivo simple"""
        if not self.is_trained or len(current_prices) < 5:
            # Fallback a predicción simple si no hay modelo
            last_price = current_prices[-1] if current_prices else 60000
            return [last_price * (1 + np.random.normal(0, 0.001)) for _ in range(24)]

        predictions = []
        window_data = current_prices[-5:].copy()

        for _ in range(24):
            pred = self.model.predict([window_data])[0]
            # Aplicar factor de auto-corrección de la IA
            pred = pred * self.correction_factor
            predictions.append(pred)

            # Actualizar ventana de datos
            window_data.pop(0)
            window_data.append(pred)

        return predictions

    def update_correction(self, actual_price):
        """Auto-corrección: compara la última predicción con el precio real y ajusta"""
        if self.last_prediction is not None and actual_price > 0:
            error = (actual_price - self.last_prediction) / self.last_prediction
            # Ajuste suave basado en el error
            self.correction_factor += error * 0.1

        # Limitar el factor de corrección para que no se desvíe demasiado (entre 0.95 y 1.05)
        self.correction_factor = max(0.95, min(1.05, self.correction_factor))
