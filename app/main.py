from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import time
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_data
from app.model.predictor import AnalyticsPredictor
from app.evaluation.internal_tracker import InternalValidator

class AppState:
    def __init__(self):
        self.current_price = 0.0
        self.history_data = {"prices": [], "times": []}
        self.predictions_obj = {"prices": [], "upper_bound": [], "lower_bound": []}
        self.prediction_times = []
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."
        self.mae = None
        self.accuracy = None
        self.total_evals = 0

state = AppState()

async def background_update_task():
    print("[INFO] Motor Analítico Predictor V9...")

    # 100 velas es suficiente para extraer features potentes
    initial_data = get_historical_data(100)
    state.history_data = initial_data

    if state.history_data["prices"]:
        success = state.predictor.train(state.history_data["prices"])
        if success:
            print("[INFO] IA Entrenada con histórico reciente.")

    while state.is_running:
        try:
            # Sincronización ultrarrápida (1s) con la caché de Binance
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                # Actualizamos historial al vuelo para la gráfica continua
                if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                    state.history_data["prices"].append(new_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 100:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                # Intentamos re-evaluar si ha pasado tiempo para validar viejas predicciones
                state.validator.update_actuals(state.current_price)

                # Generar predicción a 24 horas cada tick, conectando siempre con el punto en vivo actual
                pred_result = state.predictor.predict_next_24h(state.history_data["prices"])

                if pred_result:
                    state.predictions_obj = pred_result

                    if state.history_data["times"]:
                        last_time = state.history_data["times"][-1]
                    else:
                        last_time = int(time.time() * 1000)

                    # Generamos los 25 tiempos futuros (+0h a +24h)
                    state.prediction_times = [last_time + (i * 3600000) for i in range(25)]

                    # Registrar nueva "foto" en el tracker para evaluarla en las siguientes 24 horas
                    # Internamente el tracker sabe si ya grabó una hace poco
                    state.validator.record_new_prediction(state.current_price, state.predictions_obj["prices"])

                    p_24h = state.predictions_obj["prices"][-1]
                    p_change = ((p_24h - state.current_price) / state.current_price) * 100
                    if p_change > 1.0:
                        state.trend = "Fuerte Alza Proyectada"
                    elif p_change > 0.1:
                        state.trend = "Leve Subida Proyectada"
                    elif p_change < -1.0:
                        state.trend = "Fuerte Caída Proyectada"
                    elif p_change < -0.1:
                        state.trend = "Leve Bajada Proyectada"
                    else:
                        state.trend = "Mercado Lateral Estable"

                metrics = state.validator.get_metrics()
                state.mae = metrics["mae"]
                state.accuracy = metrics["accuracy"]
                state.total_evals = metrics["total"]

        except Exception as e:
            print(f"[ERROR] Loop fondo temporal: {e}")

        await asyncio.sleep(1.5) # Polling casi en tiempo real

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

@app.get("/api/analysis")
async def get_state():
    pred_24h_price = None
    pred_24h_pct = None
    if state.predictions_obj["prices"]:
        pred_24h_price = state.predictions_obj["prices"][-1]
        pred_24h_pct = ((pred_24h_price - state.current_price) / state.current_price) * 100

    return {
        "precio_actual": state.current_price,
        "tendencia": state.trend,
        "prediccion_24h_usd": round(pred_24h_price, 2) if pred_24h_price else None,
        "prediccion_24h_pct": round(pred_24h_pct, 2) if pred_24h_pct else None,
        "evaluacion": {
            "mae_pct": state.mae,
            "accuracy_pct": state.accuracy,
            "total_evals": state.total_evals
        },
        "chart_data": {
            "history": {
                # Para un encaje perfecto (48h visual), pasamos 48h (si existen)
                "prices": state.history_data["prices"][-48:],
                "times": state.history_data["times"][-48:]
            },
            "prediction": {
                "prices": state.predictions_obj["prices"],
                "upper_bound": state.predictions_obj["upper_bound"],
                "lower_bound": state.predictions_obj["lower_bound"],
                "times": state.prediction_times
            }
        }
    }
