from fastapi import FastAPI
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
        self.explicacion = "Iniciando sistema y conectando con Binance..."
        self.predictor = Predictor()
        self.simulator = TradingSimulator(1000.0) # 1000 USD
        self.is_running = True

state = AppState()

async def background_update_task():
    print("[INFO] Iniciando motor de IA en segundo plano...")

    # 1. Obtener histórico de Binance para entrenar
    state.history_prices = get_historical_prices(100)
    if state.history_prices:
        print("[INFO] Entrenando modelo inicial con datos de Binance...")
        state.predictor.train(state.history_prices)

    while state.is_running:
        try:
            # 2. Obtener precio actual (usa caché interna de 15s para evitar rate-limits)
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                # Auto-corrección
                state.predictor.update_correction(new_price)

                # Actualizamos histórico dinámicamente
                if not state.history_prices or state.history_prices[-1] != new_price:
                    state.history_prices.append(new_price)
                    if len(state.history_prices) > 100:
                        state.history_prices.pop(0)

                # 3. Predicciones
                state.predictions = state.predictor.predict_next_24h(state.history_prices)

                # 4. Características avanzadas
                volatility, momentum, sma = calculate_features(state.history_prices)
                sentiment = get_simulated_sentiment(momentum)
                onchain = get_simulated_onchain(momentum)

                # 5. Tomar decisión
                pred_24h = state.predictions[-1] if state.predictions else new_price
                dec, conf, expl = make_decision(new_price, pred_24h, sentiment, onchain, volatility, momentum)

                state.decision = dec
                state.confianza = conf
                state.explicacion = expl

                # 6. Simular Trading en USD
                state.simulator.process_signal(dec, new_price, datetime.datetime.now())

        except Exception as e:
            print(f"[ERROR] Tarea de fondo falló temporalmente: {e}")

        # Refresco del loop: 5 segundos, pero la API real (fetcher) usará caché de 15s.
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
        "balance": state.simulator.get_stats(state.current_price) if state.current_price else None,
        "explicacion": state.explicacion,
        "history_prices": state.history_prices[-24:],
        "ia_accuracy": state.predictor.get_accuracy(),
        "total_predictions": state.predictor.total_predictions
    }
