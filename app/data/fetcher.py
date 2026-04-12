import requests
import random

def get_current_price():
    try:
        # Usamos la API de CoinDesk que no tiene restricciones regionales para esta demo, o CoinGecko
        # CoinGecko: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur", timeout=5)
        data = response.json()
        return float(data['bitcoin']['eur'])
    except Exception as e:
        print(f"Error obteniendo precio de CoinGecko, simulando fallback: {e}")
        # Retornamos un precio base +- aleatorio si falla
        return 65000.0 + random.uniform(-100, 100)

def get_historical_prices(limit=100):
    """Devuelve una lista de precios simulados o de coingecko para el histórico."""
    try:
        # Para hacer la aplicación totalmente resiliente (ya que CoinGecko a veces limita peticiones),
        # generamos un histórico coherente basado en el precio actual
        current = get_current_price()
        if not current:
            current = 65000.0

        history = []
        price = current
        for _ in range(limit):
            history.insert(0, price)
            # El precio anterior era el actual +- un pequeño %
            price = price * (1 + random.uniform(-0.01, 0.01))
        return history
    except Exception as e:
        print(f"Error generando históricos: {e}")
        return []

def get_simulated_sentiment():
    """Simula sentimiento del mercado (0-100) basado en redes sociales y noticias"""
    return round(random.uniform(20, 80), 2)

def get_simulated_onchain():
    """Simula movimientos de ballenas (flujo neto hacia exchanges)"""
    # Valores negativos = salidas (alcista), positivos = entradas (bajista)
    return round(random.uniform(-5000, 5000), 2)
