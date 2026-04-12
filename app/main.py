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
        self.predictions_obj = None
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."

state = AppState()

async def background_update_task():
    print("[INFO] Motor Analítico V11 (Cirugía de Saneamiento)...")

    initial_data = get_historical_data(168)
    state.history_data = initial_data

    if state.history_data["prices"]:
        success = state.predictor.train(state.history_data["prices"])
        if success:
            print("[INFO] Modelos (+1h, +2h, +4h, +24h) entrenados en contexto semanal 168h.")

    while state.is_running:
        try:
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                # Empalmamos exactamente el precio nuevo en el último nodo del histórico
                if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                    state.history_data["prices"].append(new_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 168:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                state.validator.update_actuals(state.current_price)

                pred_result = state.predictor.predict_horizons(state.history_data["prices"])

                if pred_result:
                    state.predictions_obj = pred_result

                    # Registrar la predicción. El validador ya ignora llamadas repetidas en la misma hora (3500s).
                    state.validator.record_new_prediction(state.current_price, pred_result)

                    p_24h = pred_result["p_24h"]
                    p_change = ((p_24h - state.current_price) / state.current_price) * 100
                    if p_change > 1.0:
                        state.trend = "Fuerte Alza (H+24)"
                    elif p_change > 0.1:
                        state.trend = "Leve Subida (H+24)"
                    elif p_change < -1.0:
                        state.trend = "Fuerte Caída (H+24)"
                    elif p_change < -0.1:
                        state.trend = "Leve Bajada (H+24)"
                    else:
                        state.trend = "Plano / Lateral (H+24)"

        except Exception as e:
            print(f"[ERROR] Loop fondo: {e}")

        await asyncio.sleep(1.0) # Sincronía a 1s con Binance

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
    if not state.predictions_obj:
        return {"precio_actual": state.current_price, "tendencia": "Entrenando..."}

    p_24h = state.predictions_obj["p_24h"]
    p_24h_pct = ((p_24h - state.current_price) / state.current_price) * 100

    # Generar los arrays futuros limpios y sin NaNs para el gráfico
    now = int(time.time() * 1000)
    hour_ms = 3600000

    pred_prices = [
        state.predictions_obj["p_1h"],
        state.predictions_obj["p_2h"],
        state.predictions_obj["p_4h"],
        state.predictions_obj["p_24h"]
    ]

    pred_times = [
        now + (1 * hour_ms),
        now + (2 * hour_ms),
        now + (4 * hour_ms),
        now + (24 * hour_ms)
    ]

    pred_bounds = [
        state.predictions_obj["b_1h"],
        state.predictions_obj["b_2h"],
        state.predictions_obj["b_4h"],
        state.predictions_obj["b_24h"]
    ]

    return {
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
                "bounds_pct": pred_bounds
            }
        }
    }
