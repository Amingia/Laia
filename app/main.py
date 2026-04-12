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
        self.predictions_obj = {"prices": [], "upper_bound": [], "lower_bound": []}
        self.prediction_times = []
        self.decision = "HOLD"
        self.confianza = 0.5
        self.explicacion = "Conectando con Binance y estabilizando red neuronal..."
        self.predictor = Predictor()
        self.simulator = TradingSimulator(1000.0)
        self.is_running = True

state = AppState()

async def background_update_task():
    print("[INFO] Iniciando motor IA v7...")

    # 1H Forzado por defecto
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

                if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                    state.history_data["prices"].append(new_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 100:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                state.predictions_obj = state.predictor.predict_next_24h(state.history_data["prices"])

                if state.history_data["times"]:
                    last_time = state.history_data["times"][-1]
                else:
                    last_time = int(time.time() * 1000)
                # 3600000ms = 1h
                state.prediction_times = [last_time + (i * 3600000) for i in range(1, 25)]

                vol, mom, sma_c, sma_m, acc = calculate_features(state.history_data["prices"])

                pred_24h = state.predictions_obj["prices"][-1] if state.predictions_obj["prices"] else new_price

                dec, conf, expl, m_state = make_decision(
                    new_price, pred_24h, 50, 0, vol, mom, sma_c, sma_m, acc
                )

                state.decision = dec
                state.confianza = conf
                state.explicacion = expl

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
        "balance": state.simulator.get_stats(state.current_price) if state.current_price else None,
        "explicacion": state.explicacion,
        "ia_metrics": state.predictor.get_metrics(),
        "chart_data": {
            "history": {
                "prices": state.history_data["prices"][-50:],
                "times": state.history_data["times"][-50:]
            },
            "prediction": {
                "prices": state.predictions_obj["prices"],
                "upper_bound": state.predictions_obj["upper_bound"],
                "lower_bound": state.predictions_obj["lower_bound"],
                "times": state.prediction_times
            }
        }
    }
