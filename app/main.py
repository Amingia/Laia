from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import datetime
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_prices, get_simulated_sentiment, get_simulated_onchain
from app.model.predictor import Predictor
from app.decision.engine import make_decision
from app.simulation.trader import TradingSimulator

# Estado global de la aplicación
class AppState:
    def __init__(self):
        self.current_price = 0
        self.history_prices = []
        self.predictions = []
        self.decision = "HOLD"
        self.confianza = 0.5
        self.explicacion = "Iniciando sistema y recogiendo datos iniciales..."
        self.predictor = Predictor()
        self.simulator = TradingSimulator(1000.0)
        self.is_running = True

state = AppState()

async def background_update_task():
    print("Iniciando motor de IA en segundo plano...")

    # 1. Cargar datos históricos iniciales
    state.history_prices = get_historical_prices(100)
    if state.history_prices:
        print("Entrenando modelo inicial...")
        state.predictor.train(state.history_prices)

    while state.is_running:
        try:
            # 2. Obtener datos reales
            new_price = get_current_price()
            if new_price:
                state.current_price = new_price

                # Auto-corrección de predicciones previas
                state.predictor.update_correction(new_price)

                # Actualizar histórico
                state.history_prices.append(new_price)
                if len(state.history_prices) > 100:
                    state.history_prices.pop(0)

                # 3. Predecir
                state.predictions = state.predictor.predict_next_24h(state.history_prices)
                if state.predictions:
                    state.predictor.last_prediction = state.predictions[0]

                # 4. Datos simulados
                sentiment = get_simulated_sentiment()
                onchain = get_simulated_onchain()

                # 5. Tomar decisión
                pred_24h = state.predictions[-1] if state.predictions else new_price
                dec, conf, expl = make_decision(new_price, pred_24h, sentiment, onchain)

                state.decision = dec
                state.confianza = conf
                state.explicacion = expl

                # 6. Simular Trading
                state.simulator.process_signal(dec, new_price, datetime.datetime.now())

        except Exception as e:
            print(f"Error en tarea de fondo: {e}")

        # Esperar 5 segundos para la siguiente iteración
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar la tarea de actualización continua al arrancar
    task = asyncio.create_task(background_update_task())
    yield
    # Limpiar al cerrar
    state.is_running = False
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Servir archivos del frontend
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
        "history_prices": state.history_prices[-24:] # Para el gráfico, enviamos las últimas 24 muestras
    }
