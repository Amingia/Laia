import requests
import random
import numpy as np
import time

# Variables para sistema de caché
_cache = {
    "current_price": {"value": None, "timestamp": 0},
    "historical_prices": {"value": None, "timestamp": 0}
}
CACHE_TTL = 15  # Segundos de vida de la caché
SYMBOL = "BTCUSDT" # Todo en USD y en Binance

def get_current_price():
    """Obtiene el precio actual de Binance con sistema de caché y fallback"""
    current_time = time.time()

    # Retornar de caché si es válido
    if _cache["current_price"]["value"] is not None and (current_time - _cache["current_price"]["timestamp"] < CACHE_TTL):
        return _cache["current_price"]["value"]

    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = float(data['price'])

        # Guardar en caché
        _cache["current_price"]["value"] = price
        _cache["current_price"]["timestamp"] = current_time
        return price

    except Exception as e:
        print(f"[Aviso] Error obteniendo precio de Binance: {e}")
        # Fallback si Binance falla o bloquea la IP: Simulamos basado en el último conocido o base
        last_price = _cache["current_price"]["value"]
        if last_price:
            fallback_price = last_price * (1 + random.uniform(-0.001, 0.001))
            return round(fallback_price, 2)
        return 65000.0 + random.uniform(-50, 50)

def get_historical_prices(limit=100):
    """Obtiene el histórico (cierre horario) desde Binance con caché para entrenar la IA"""
    current_time = time.time()

    # Histórico tiene un TTL mucho más alto ya que es por horas
    if _cache["historical_prices"]["value"] is not None and (current_time - _cache["historical_prices"]["timestamp"] < 300):
        return _cache["historical_prices"]["value"]

    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1h&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Índice 4 es el precio de cierre en Binance
        history = [float(kline[4]) for kline in data]

        _cache["historical_prices"]["value"] = history
        _cache["historical_prices"]["timestamp"] = current_time
        return history

    except Exception as e:
        print(f"[Aviso] Error obteniendo histórico de Binance: {e}")
        # Fallback: Generar histórico simulado coherente para no romper la app
        current = get_current_price()
        if not current:
            current = 65000.0

        history = []
        price = current
        for _ in range(limit):
            history.insert(0, price)
            price = price * (1 + random.uniform(-0.005, 0.005))

        return history

def calculate_features(prices):
    """
    Calcula indicadores técnicos basados en el precio.
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
    """Simula volumen en USD coherente con la volatilidad actual"""
    base_volume = random.uniform(5000000, 15000000)
    multiplier = 1 + (volatility * 10)
    return round(base_volume * multiplier, 2)

def get_simulated_sentiment(momentum):
    """Simula sentimiento del mercado (0-100)"""
    base = 50
    sentiment = base + (momentum * 8) + random.uniform(-5, 5)
    return round(max(10, min(90, sentiment)), 2)

def get_simulated_onchain(momentum):
    """Simula flujos netos on-chain en USD"""
    base_flow = -momentum * 50000
    flow = base_flow + random.uniform(-100000, 100000)
    return round(flow, 2)
