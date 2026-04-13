import asyncio
from app.data.fetcher import get_historical_data, get_current_price
from app.model.predictor import AnalyticsPredictor

print("1. Probando precio...")
p = get_current_price()
print(f"Precio: {p}")

print("2. Probando historico...")
h = get_historical_data(168)
print(f"Historico len: {len(h['prices'])}")

print("3. Probando predictor...")
pred = AnalyticsPredictor()
res = pred.train(h['prices'])
print(f"Entrenamiento: {res}")

if res:
    out = pred.predict_horizons(h['prices'])
    print(f"Prediccion keys: {out.keys() if out else 'None'}")
