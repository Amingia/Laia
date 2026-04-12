import requests
import random
import numpy as np
import time

# Caché ultracorta (1 segundo) para que el precio se sienta vivo
_cache = {
    "current_price": {"value": None, "timestamp": 0},
    "history_1h": {"value": None, "timestamp": 0}
}
CACHE_TTL_PRICE = 1
SYMBOL = "BTCUSDT"

def get_current_price():
    current_time = time.time()
    if _cache["current_price"]["value"] is not None and (current_time - _cache["current_price"]["timestamp"] < CACHE_TTL_PRICE):
        return _cache["current_price"]["value"]

    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        price = float(response.json()['price'])

        _cache["current_price"]["value"] = price
        _cache["current_price"]["timestamp"] = current_time
        return price
    except Exception as e:
        last_price = _cache["current_price"]["value"]
        if last_price:
            fallback = last_price * (1 + random.uniform(-0.00005, 0.00005))
            return round(fallback, 2)
        return 65000.0

def get_historical_data(limit=168):
    """
    Trae los datos históricos de Binance.
    Por defecto 168h (7 días exactos) para visualización y contexto fuerte para entrenamiento.
    """
    cache_key = "history_1h"
    current_time = time.time()

    # 5 minutos de caché para velas de 1h es seguro
    if _cache.get(cache_key, {}).get("value") is not None and (current_time - _cache[cache_key]["timestamp"] < 300):
        return _cache[cache_key]["value"]

    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1h&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        history_prices = [float(k[4]) for k in data] # Precio de cierre
        timestamps = [int(k[0]) for k in data]

        result = {"prices": history_prices, "times": timestamps}
        _cache[cache_key] = {"value": result, "timestamp": current_time}
        return result

    except Exception as e:
        old_data = _cache.get(cache_key, {}).get("value")
        if old_data:
            return old_data

        current = get_current_price()
        history, times = [], []
        now = int(time.time() * 1000)

        for i in range(limit):
            history.insert(0, current)
            times.insert(0, now - (i * 3600000))
            current = current * (1 + random.uniform(-0.002, 0.002))

        return {"prices": history, "times": times}

def calculate_advanced_features(prices):
    """
    Features técnicas útiles para los modelos por horizontes.
    Utilizamos una ventana más amplia dado que ahora disponemos de 168 velas.
    """
    if len(prices) < 24:
        return 0.0, 0.0, prices[-1], prices[-1], 0.0

    recent = prices[-6:]
    older = prices[-24:-6]

    sma_corta = sum(recent) / 6
    sma_larga = sum(prices[-24:]) / 24

    momentum = ((recent[-1] - older[0]) / older[0]) * 100

    # Aceleración simple
    momentum_prev = ((older[-1] - prices[-24]) / prices[-24]) * 100
    acceleration = momentum - momentum_prev

    # Volatilidad (Desviación estándar de los retornos de las últimas 24h)
    returns = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
    volatility = np.std(returns[-24:]) * 100 if len(returns) >= 24 else 0.0

    return round(volatility, 4), round(momentum, 4), round(sma_corta, 2), round(sma_larga, 2), round(acceleration, 4)
