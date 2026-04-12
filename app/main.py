from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import time
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_data
from app.model.predictor import AnalyticsPredictor
from app.evaluation.validator import ExcelValidator

class AppState:
    def __init__(self):
        self.current_price = 0.0
        self.history_data = {"prices": [], "volumes": [], "times": []}
        self.predictions_obj = {"prices": [], "upper_bound": [], "lower_bound": []}
        self.prediction_times = []
        self.predictor = AnalyticsPredictor()
        self.validator = ExcelValidator()
        self.is_running = True
        self.trend = "Analizando..."
        self.mae = None
        self.accuracy = None
        self.total_evals = 0
        self.last_pred_time = 0

state = AppState()

async def background_update_task():
    print("[INFO] Iniciando Motor Predictivo y Evaluador v8...")

    # Base inicial: 300 velas de 1h de Binance
    initial_data = get_historical_data(300)
    state.history_data = initial_data

    if state.history_data["prices"]:
        success = state.predictor.train(state.history_data["prices"], state.history_data["volumes"])
        if success:
            print("[INFO] IA Entrenada con éxito en datos recientes.")

    while state.is_running:
        try:
            # Polling ultra-rápido (2-3s real)
            new_price = get_current_price()
            if new_price and new_price > 0:
                state.current_price = new_price

                # Rellena los huecos del Excel en base al precio actual (Actualización de predicciones pasadas)
                state.validator.update_actuals(new_price)

                # Actualizar el histórico real "en vivo" para la curva
                if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                    state.history_data["prices"].append(new_price)
                    state.history_data["times"].append(int(time.time() * 1000))
                    if len(state.history_data["volumes"]) > 0:
                        state.history_data["volumes"].append(state.history_data["volumes"][-1]) # Simulamos arrastre para el último tick

                    if len(state.history_data["prices"]) > 300:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)
                        if len(state.history_data["volumes"]) > 0:
                            state.history_data["volumes"].pop(0)

                # Generar predicción suavizada de las próximas 24 horas
                pred_result = state.predictor.predict_next_24h(state.history_data["prices"], state.history_data["volumes"])

                if pred_result:
                    state.predictions_obj = pred_result

                    # Tiempos de las predicciones (+1h, +2h, etc)
                    if state.history_data["times"]:
                        last_time = state.history_data["times"][-1]
                    else:
                        last_time = int(time.time() * 1000)
                    state.prediction_times = [last_time + (i * 3600000) for i in range(1, 25)]

                    # Grabar en Excel (Solo ocurre cada 55 mins internamente en el Validator)
                    state.validator.record_new_prediction(state.current_price, state.predictions_obj["prices"])

                    # Determinar tendencia para el dashboard
                    p_24h = state.predictions_obj["prices"][-1]
                    p_change = ((p_24h - state.current_price) / state.current_price) * 100
                    if p_change > 1.0:
                        state.trend = "Fuerte Alza Esperada"
                    elif p_change > 0.1:
                        state.trend = "Leve Subida"
                    elif p_change < -1.0:
                        state.trend = "Fuerte Caída Esperada"
                    elif p_change < -0.1:
                        state.trend = "Leve Bajada"
                    else:
                        state.trend = "Lateral / Indecisión"

                # Cargar métricas en vivo del Excel para UI
                metrics = state.validator.get_live_metrics()
                state.mae = metrics["mae"]
                state.accuracy = metrics["accuracy"]
                state.total_evals = metrics["total_evaluadas"]

        except Exception as e:
            print(f"[ERROR] Loop fondo temporal: {e}")

        await asyncio.sleep(2) # Polling casi en tiempo real a Binance (con su propio caché)

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
    # Estructuramos la respuesta para un frontend analítico y puro

    # Si tenemos predicción a 24h, la extraemos para cálculo rápido en UI
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
                # Solo pasamos las últimas 50 velas a UI para no saturar el navegador, aunque la IA entrena con 300
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
