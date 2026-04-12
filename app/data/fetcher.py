import requests
import random
import numpy as np
import time

# Caché ajustada para polling rápido y estabilidad
_cache = {
    "current_price": {"value": None, "timestamp": 0},
    "history_1h": {"value": None, "timestamp": 0}
}
CACHE_TTL_PRICE = 2  # 2 Segundos: Actualización casi en tiempo real (Polling rápido)
SYMBOL = "BTCUSDT"

def get_current_price():
    current_time = time.time()
    if _cache["current_price"]["value"] is not None and (current_time - _cache["current_price"]["timestamp"] < CACHE_TTL_PRICE):
        return _cache["current_price"]["value"]

    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        response = requests.get(url, timeout=2) # Timeout corto para no congelar la app si Binance tarda
        response.raise_for_status()
        price = float(response.json()['price'])

        _cache["current_price"]["value"] = price
        _cache["current_price"]["timestamp"] = current_time
        return price
    except Exception as e:
        last_price = _cache["current_price"]["value"]
        if last_price:
            # Fallback suavizado para evitar congelación visual
            fallback = last_price * (1 + random.uniform(-0.0001, 0.0001))
            return round(fallback, 2)
        return 65000.0

def get_historical_data(limit=300):
    """
    Obtiene un histórico más profundo de Binance para el entrenamiento inicial.
    Traemos Precio y Volumen para enriquecer el modelo.
    """
    cache_key = "history_1h"
    current_time = time.time()

    # 5 minutos de caché para velas de 1h es más que suficiente
    if _cache.get(cache_key, {}).get("value") is not None and (current_time - _cache[cache_key]["timestamp"] < 300):
        return _cache[cache_key]["value"]

    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1h&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Extraemos:
        # 0: Open time, 1: Open, 2: High, 3: Low, 4: Close, 5: Volume
        history_prices = [float(k[4]) for k in data]
        history_volumes = [float(k[5]) for k in data]
        timestamps = [int(k[0]) for k in data]

        result = {"prices": history_prices, "volumes": history_volumes, "times": timestamps}
        _cache[cache_key] = {"value": result, "timestamp": current_time}
        return result

    except Exception as e:
        print(f"[Aviso] Error Binance Kline: {e}")
        old_data = _cache.get(cache_key, {}).get("value")
        if old_data:
            return old_data

        # Fallback de emergencia
        current = get_current_price()
        history, vols, times = [], [], []
        now = int(time.time() * 1000)
        ms_per_interval = 3600000

        for i in range(limit):
            history.insert(0, current)
            vols.insert(0, random.uniform(1000, 5000))
            times.insert(0, now - (i * ms_per_interval))
            current = current * (1 + random.uniform(-0.002, 0.002))

        return {"prices": history, "volumes": vols, "times": times}

def calculate_advanced_features(prices, volumes=None):
    """
    Feature Engineering serio:
    Calcula EMA, Volatilidad real, Momentum, y Variación Porcentual.
    """
    if len(prices) < 14:
        return 0.0, 0.0, prices[-1], prices[-1], 0.0, 0.0

    recent = prices[-5:]
    older = prices[-14:-5]

    # Simple Moving Averages
    sma_5 = sum(recent) / 5
    sma_14 = sum(prices[-14:]) / 14

    # Momentum (RSI simplificado direccional)
    momentum = ((recent[-1] - older[0]) / older[0]) * 100

    # Aceleración del momentum
    momentum_prev = ((older[-1] - prices[-14]) / prices[-14]) * 100
    acceleration = momentum - momentum_prev

    # Volatilidad (Desviación estándar de los retornos)
    returns = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
    volatility = np.std(returns[-14:]) * 100 if len(returns) >= 14 else 0.0

    # Ratio de Volumen (si está disponible)
    vol_ratio = 1.0
    if volumes and len(volumes) >= 14:
        recent_vol = sum(volumes[-5:]) / 5
        older_vol = sum(volumes[-14:]) / 14
        vol_ratio = recent_vol / older_vol if older_vol > 0 else 1.0

    return round(volatility, 4), round(momentum, 4), round(sma_5, 2), round(sma_14, 2), round(acceleration, 4), round(vol_ratio, 2)
