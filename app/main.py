from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import datetime
import time
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_prices, calculate_features
from app.model.predictor import Predictor
from app.decision.engine import make_decision
from app.simulation.trader import TradingSimulator

class AppState:
    def __init__(self):
        self.current_price = 0
        self.history_data = {"prices": [], "times": []}
        self.predictions = []
        self.prediction_times = []
        self.decision = "HOLD"
        self.confianza = 0.5
        self.explicacion = "Conectando y estabilizando IA..."
        self.market_state = "Evaluando..."
        self.predictor = Predictor()
        self.simulator = TradingSimulator(1000.0)
        self.is_running = True

state = AppState()

async def background_update_task():
    print("[INFO] Iniciando motor IA v4 con Tiempos Reales...")

    # Base en velas de 1h para la IA y lógica principal
    initial_data = get_historical_prices("1h", 100)
    state.history_data = initial_data
    if state.history_data["prices"]:
        state.predictor.train(state.history_data["prices"])

    while state.is_running:
        try:
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                state.predictor.update_correction(new_price)

                # Actualizar último precio en el array histórico base
                if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                    state.history_data["prices"].append(new_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 100:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                # Predecir 24h
                state.predictions = state.predictor.predict_next_24h(state.history_data["prices"])

                # Generar tiempos futuros (1 hora por salto ya que la IA entrena en 1h por defecto)
                if state.history_data["times"]:
                    last_time = state.history_data["times"][-1]
                else:
                    last_time = int(time.time() * 1000)
                state.prediction_times = [last_time + (i * 3600000) for i in range(1, 25)]

                vol, mom, sma_c, sma_m, acc = calculate_features(state.history_data["prices"])

                pred_24h = state.predictions[-1] if state.predictions else new_price

                # Valores on-chain simulados fijos (solo para completar firma)
                dec, conf, expl, m_state = make_decision(
                    new_price, pred_24h, 50, 0, vol, mom, sma_c, sma_m, acc
                )

                state.decision = dec
                state.confianza = conf
                state.explicacion = expl
                state.market_state = m_state

                state.simulator.process_signal(dec, new_price, datetime.datetime.now())

        except Exception as e:
            print(f"[ERROR] Loop fondo: {e}")

        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_update_task())
    yield
    state.is_running = False
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/auto")
async def get_state():
    return {
        "precio_actual": state.current_price,
        "decision": state.decision,
        "confianza": state.confianza,
        "market_state": state.market_state,
        "balance": state.simulator.get_stats(state.current_price) if state.current_price else None,
        "explicacion": state.explicacion,
        "ia_metrics": state.predictor.get_metrics(),
        # Para evitar enviar toda la data en cada tick, mandamos solo lo básico.
        # El gráfico real se alimenta de /api/chart
    }

@app.get("/api/chart")
async def get_chart_data(interval: str = "1h"):
    """Devuelve histórico real y predicción unida con tiempos reales"""
    valid_intervals = ["15m", "1h", "4h", "1d"]
    if interval not in valid_intervals:
        interval = "1h"

    data = get_historical_prices(interval, 50)

    # Calcular saltos de tiempo para la predicción según el intervalo solicitado
    ms_per_interval = {"15m": 900000, "1h": 3600000, "4h": 14400000, "1d": 86400000}.get(interval, 3600000)

    # Si tenemos predicciones generadas por la IA base
    pred_prices = state.predictions if state.predictions else []
    pred_times = []

    if data["times"] and pred_prices:
        last_time = data["times"][-1]
        # Ajustamos el número de puntos de predicción al rango para que tenga sentido visualmente
        # (Si estamos en 15m mostramos menos futuro que si estamos en 1d)
        num_points = len(pred_prices)
        pred_times = [last_time + (i * ms_per_interval) for i in range(1, num_points + 1)]

    return {
        "history": data,
        "prediction": {
            "prices": pred_prices,
            "times": pred_times
        }
    }

@app.post("/api/mode")
async def toggle_mode(request: Request):
    data = await request.json()
    is_active = data.get("active", False)
    state.simulator.set_mode(is_active)
    return {"status": "ok", "mode": "active" if is_active else "observacion"}
