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
        self.is_ready = False
        self.status_msg = "Iniciando motor analítico..."

        self.current_price = 0.0
        self.history_data = {"prices": [], "times": []}
        self.predictions_obj = None
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."

state = AppState()

async def background_update_task():
    print("[INFO] V12 Warm-up: Descargando histórico (168h)...")
    state.status_msg = "Descargando histórico de Binance (168h)..."

    # 1. Warm-up (Síncrono/Bloqueante visualmente)
    initial_data = get_historical_data(168)
    state.history_data = initial_data

    if state.history_data["prices"]:
        state.status_msg = "Entrenando redes neuronales (+1h, +2h, +4h, +24h)..."
        success = state.predictor.train(state.history_data["prices"])

        if success:
            print("[INFO] V12 Warm-up: Modelos entrenados con éxito.")
            state.status_msg = "Generando proyecciones iniciales y conectando en tiempo real..."

            # Generar primera predicción de forma garantizada antes de abrir la API
            state.current_price = get_current_price()
            pred_result = state.predictor.predict_horizons(state.history_data["prices"])

            if pred_result:
                state.predictions_obj = pred_result
                state.validator.record_new_prediction(state.current_price, pred_result)
                state.is_ready = True
                print("[INFO] V12: Arranque completado. API lista para servir datos.")
            else:
                print("[ERROR] Fallo al generar proyección inicial.")
                state.status_msg = "Error al generar proyecciones."
        else:
            print("[ERROR] Fallo al entrenar el modelo.")
            state.status_msg = "Error al entrenar los modelos."
    else:
        print("[ERROR] Fallo al descargar histórico inicial.")
        state.status_msg = "Fallo de conexión inicial con Binance."

    # 2. Bucle principal de actualización (Polling a 1.5s)
    while state.is_running:
        if state.is_ready:
            try:
                new_price = get_current_price()
                if new_price and new_price > 0:
                    state.current_price = new_price

                    # Actualización del histórico al vuelo
                    if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                        state.history_data["prices"].append(new_price)
                        state.history_data["times"].append(int(time.time() * 1000))

                        if len(state.history_data["prices"]) > 168:
                            state.history_data["prices"].pop(0)
                            state.history_data["times"].pop(0)

                    # Evaluación de predicciones pasadas (si han madurado)
                    state.validator.update_actuals(state.current_price)

                    # Predicción en bucle
                    pred_result = state.predictor.predict_horizons(state.history_data["prices"])

                    if pred_result:
                        state.predictions_obj = pred_result
                        state.validator.record_new_prediction(state.current_price, pred_result)

                        p_24h = pred_result["p_24h"]
                        p_change = ((p_24h - state.current_price) / state.current_price) * 100
                        if p_change > 1.0:
                            state.trend = "Fuerte Alza Esperada"
                        elif p_change > 0.1:
                            state.trend = "Leve Subida Esperada"
                        elif p_change < -1.0:
                            state.trend = "Fuerte Caída Esperada"
                        elif p_change < -0.1:
                            state.trend = "Leve Bajada Esperada"
                        else:
                            state.trend = "Lateral / Indecisión"

            except Exception as e:
                print(f"[ERROR] Loop fondo: {e}")

        await asyncio.sleep(1.5)

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
    if not state.is_ready:
        return {"ready": False, "status_msg": state.status_msg}

    p_24h = state.predictions_obj["p_24h"]
    p_24h_pct = ((p_24h - state.current_price) / state.current_price) * 100

    now = int(time.time() * 1000)
    hour_ms = 3600000

    # La interpolación (los 24 puntos) se hará nativamente en el backend para que el Frontend solo la dibuje
    pred_prices = state.predictions_obj["interpolated_prices"]
    pred_bounds = state.predictions_obj["interpolated_bounds"]
    pred_times = [now + (i * hour_ms) for i in range(1, 25)] # +1h hasta +24h

    return {
        "ready": True,
        "precio_actual": state.current_price,
        "tendencia": state.trend,
        "prediccion_24h_usd": round(p_24h, 2),
        "prediccion_24h_pct": round(p_24h_pct, 2),
        "evaluacion": state.validator.get_metrics(),
        "chart_data": {
            "history": {
                "prices": state.history_data["prices"],
                "times": state.history_data["times"]
            },
            "prediction": {
                "prices": pred_prices,
                "times": pred_times,
                "bounds_pct": pred_bounds,
                "anchor_indices": [0, 1, 3, 23] # Los índices de los puntos reales evaluados (+1, +2, +4, +24h)
            }
        }
    }
