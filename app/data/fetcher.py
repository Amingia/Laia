import requests
import random
import numpy as np

def get_current_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur", timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data['bitcoin']['eur'])
    except Exception as e:
        print(f"Error obteniendo precio de CoinGecko, simulando fallback: {e}")
        # Retornamos un precio base +- aleatorio si falla, evitando que el sistema colapse
        return 65000.0 + random.uniform(-100, 100)

def get_historical_prices(limit=100):
    """Devuelve una lista de precios simulados coherentes para el histórico inicial."""
    try:
        current = get_current_price()
        if not current:
            current = 65000.0

        history = []
        price = current
        for _ in range(limit):
            history.insert(0, price)
            price = price * (1 + random.uniform(-0.01, 0.01))
        return history
    except Exception as e:
        print(f"Error generando históricos: {e}")
        return [65000.0] * limit

def calculate_features(prices):
    """
    Feature Engineering: Calcula indicadores técnicos adicionales basados en el precio.
    Devuelve: Volatilidad, Momentum, y Media Móvil de los últimos 5 periodos.
    """
    if len(prices) < 5:
        return 0.0, 0.0, prices[-1] if prices else 0.0

    recent_prices = prices[-5:]

    # Media Móvil Simple (SMA)
    sma = sum(recent_prices) / 5

    # Momentum (Diferencia porcentual entre actual y hace 5 periodos)
    momentum = ((recent_prices[-1] - recent_prices[0]) / recent_prices[0]) * 100

    # Volatilidad (Desviación estándar de los cambios porcentuales)
    changes = [(recent_prices[i] - recent_prices[i-1])/recent_prices[i-1] for i in range(1, len(recent_prices))]
    volatility = np.std(changes) * 100 if len(changes) > 0 else 0.0

    return round(volatility, 4), round(momentum, 4), round(sma, 2)

def get_simulated_volume(volatility):
    """Simula volumen coherente: más volatilidad = más volumen"""
    base_volume = random.uniform(1000, 5000)
    multiplier = 1 + (volatility * 5) # Si hay mucha volatilidad, el volumen se multiplica
    return round(base_volume * multiplier, 2)

def get_simulated_sentiment(momentum):
    """Simula sentimiento del mercado (0-100) alineado con el momentum"""
    base = 50
    # Si momentum es positivo, suma al sentimiento; si negativo, resta. Limitado entre 10 y 90
    sentiment = base + (momentum * 5) + random.uniform(-10, 10)
    return round(max(10, min(90, sentiment)), 2)

def get_simulated_onchain(momentum):
    """Simula movimientos de ballenas alineados a la tendencia corta"""
    # Momentum negativo = posibles entradas (positivo), momentum positivo = posibles salidas (negativo)
    base_flow = -momentum * 1000
    flow = base_flow + random.uniform(-2000, 2000)
    return round(flow, 2)
