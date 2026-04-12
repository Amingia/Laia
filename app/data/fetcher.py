import requests
import random
import numpy as np
import time
from datetime import datetime

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
    cache_key = f"history_{interval}"
    current_time = time.time()

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
        timestamps = [int(k[0]) for k in data] # Tiempo de apertura en ms

        _cache[cache_key] = {"value": {"prices": history, "times": timestamps}, "timestamp": current_time}
        return _cache[cache_key]["value"]

    except Exception as e:
        print(f"[Aviso] Error Binance Kline ({interval}): {e}")
        old_data = _cache.get(cache_key, {}).get("value")
        if old_data:
            return old_data

        current = get_current_price()
        history = []
        times = []
        now = int(time.time() * 1000)
        ms_per_interval = {"15m": 900000, "1h": 3600000, "4h": 14400000, "1d": 86400000}.get(interval, 3600000)

        for i in range(limit):
            history.insert(0, current)
            times.insert(0, now - (i * ms_per_interval))
            current = current * (1 + random.uniform(-0.002, 0.002))
        return {"prices": history, "times": times}

def calculate_features(prices):
    if len(prices) < 10:
        return 0.0, 0.0, prices[-1], prices[-1], 0.0

    recent = prices[-5:]
    older = prices[-10:-5]

    sma_corta = sum(recent) / 5
    sma_media = sum(prices[-10:]) / 10

    momentum = ((recent[-1] - recent[0]) / recent[0]) * 100
    older_momentum = ((older[-1] - older[0]) / older[0]) * 100

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
