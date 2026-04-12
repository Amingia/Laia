from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import datetime
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_prices, get_simulated_sentiment, get_simulated_onchain, calculate_features
from app.model.predictor import Predictor
from app.decision.engine import make_decision
from app.simulation.trader import TradingSimulator

class AppState:
    def __init__(self):
        self.current_price = 0
        self.history_prices = []
        self.predictions = []
        self.decision = "HOLD"
        self.confianza = 0.5
        self.explicacion = "Conectando y estabilizando IA..."
        self.market_state = "Evaluando..."
        self.predictor = Predictor()
        self.simulator = TradingSimulator(1000.0)
        self.is_running = True

state = AppState()

async def background_update_task():
    print("[INFO] Iniciando motor IA v4...")

    initial_data = get_historical_prices("1h", 100)
    state.history_prices = initial_data["prices"]
    if state.history_prices:
        state.predictor.train(state.history_prices)

    while state.is_running:
        try:
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                state.predictor.update_correction(new_price)

                if not state.history_prices or state.history_prices[-1] != new_price:
                    state.history_prices.append(new_price)
                    if len(state.history_prices) > 100:
                        state.history_prices.pop(0)

                state.predictions = state.predictor.predict_next_24h(state.history_prices)

                vol, mom, sma_c, sma_m, acc = calculate_features(state.history_prices)
                sentiment = get_simulated_sentiment(mom)
                onchain = get_simulated_onchain(mom)

                pred_24h = state.predictions[-1] if state.predictions else new_price
                dec, conf, expl, m_state = make_decision(
                    new_price, pred_24h, sentiment, onchain, vol, mom, sma_c, sma_m, acc
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
        "prediccion_24h": state.predictions[-1] if state.predictions else state.current_price,
        "prediccion_horas": state.predictions,
        "decision": state.decision,
        "confianza": state.confianza,
        "market_state": state.market_state,
        "balance": state.simulator.get_stats(state.current_price) if state.current_price else None,
        "explicacion": state.explicacion,
        "history_prices": state.history_prices[-24:],
        "ia_metrics": state.predictor.get_metrics()
    }

@app.get("/api/chart")
async def get_chart_data(interval: str = "1h"):
    """Devuelve el histórico para el gráfico con el rango solicitado"""
    # Validar intervalo
    valid_intervals = ["15m", "1h", "4h", "1d"]
    if interval not in valid_intervals:
        interval = "1h"

    data = get_historical_prices(interval, 50) # Últimos 50 puntos
    return data

@app.post("/api/mode")
async def toggle_mode(request: Request):
    data = await request.json()
    is_active = data.get("active", False)
    state.simulator.set_mode(is_active)
    return {"status": "ok", "mode": "active" if is_active else "observacion"}
