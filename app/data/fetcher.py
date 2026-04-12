import requests
import random
import numpy as np
import time

# Caché segmentada por intervalos de Binance
_cache = {
    "current_price": {"value": None, "timestamp": 0},
    "history_15m": {"value": None, "timestamp": 0},
    "history_1h": {"value": None, "timestamp": 0},
    "history_4h": {"value": None, "timestamp": 0},
    "history_1d": {"value": None, "timestamp": 0}
}
CACHE_TTL_PRICE = 15
SYMBOL = "BTCUSDT"

def get_current_price():
    current_time = time.time()
    if _cache["current_price"]["value"] is not None and (current_time - _cache["current_price"]["timestamp"] < CACHE_TTL_PRICE):
        return _cache["current_price"]["value"]

    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        price = float(response.json()['price'])

        _cache["current_price"]["value"] = price
        _cache["current_price"]["timestamp"] = current_time
        return price
    except Exception as e:
        print(f"[Aviso] Error Binance Price: {e}")
        last_price = _cache["current_price"]["value"]
        return round(last_price * (1 + random.uniform(-0.001, 0.001)), 2) if last_price else 65000.0

def get_historical_prices(interval="1h", limit=100):
    """
    Soporta: 15m, 1h, 4h, 1d.
    La caché depende del intervalo para no pedir constantemente velas largas.
    """
    cache_key = f"history_{interval}"
    current_time = time.time()

    # TTL dinámico según intervalo
    ttl_map = {"15m": 60, "1h": 300, "4h": 600, "1d": 3600}
    ttl = ttl_map.get(interval, 300)

    if _cache.get(cache_key, {}).get("value") is not None and (current_time - _cache[cache_key]["timestamp"] < ttl):
        return _cache[cache_key]["value"]

    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        history = [float(k[4]) for k in data] # Precios de cierre
        timestamps = [int(k[0]) for k in data] # Tiempos apertura para el frontend si lo necesita

        _cache[cache_key] = {"value": {"prices": history, "times": timestamps}, "timestamp": current_time}
        return _cache[cache_key]["value"]

    except Exception as e:
        print(f"[Aviso] Error Binance Kline ({interval}): {e}")
        # Fallback de caché vieja o simulación
        old_data = _cache.get(cache_key, {}).get("value")
        if old_data:
            return old_data

        current = get_current_price()
        history = []
        for _ in range(limit):
            history.insert(0, current)
            current = current * (1 + random.uniform(-0.002, 0.002))
        return {"prices": history, "times": []}

def calculate_features(prices):
    """
    Features más avanzadas para mejor predicción y análisis de tendencia.
    """
    if len(prices) < 10:
        return 0.0, 0.0, prices[-1], prices[-1], 0.0

    recent = prices[-5:]
    older = prices[-10:-5]

    sma_corta = sum(recent) / 5
    sma_media = sum(prices[-10:]) / 10

    momentum = ((recent[-1] - recent[0]) / recent[0]) * 100
    older_momentum = ((older[-1] - older[0]) / older[0]) * 100

    # Aceleración: si el momentum actual es mayor que el anterior
    acceleration = momentum - older_momentum

    changes = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
    volatility = np.std(changes[-10:]) * 100 if len(changes) > 10 else 0.0

    return round(volatility, 4), round(momentum, 4), round(sma_corta, 2), round(sma_media, 2), round(acceleration, 4)

def determine_market_state(sma_corta, sma_media, momentum, acceleration):
    if sma_corta > sma_media and momentum > 0.5:
        if acceleration > 0: return "Alcista Fuerte"
        return "Alcista Debilitándose"
    elif sma_corta < sma_media and momentum < -0.5:
        if acceleration < 0: return "Bajista Fuerte"
        return "Bajista Debilitándose"
    else:
        return "Lateral / Indecisión"

def get_simulated_volume(volatility):
    base = random.uniform(5000000, 15000000)
    return round(base * (1 + (volatility * 10)), 2)

def get_simulated_sentiment(momentum):
    base = 50
    sentiment = base + (momentum * 8) + random.uniform(-5, 5)
    return round(max(10, min(90, sentiment)), 2)

def get_simulated_onchain(momentum):
    base_flow = -momentum * 50000
    flow = base_flow + random.uniform(-100000, 100000)
    return round(flow, 2)
