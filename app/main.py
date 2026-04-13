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
        self.is_training = True
        self.status_msg = "Iniciando motor..."
        self.is_fallback = False

        self.current_price = 0.0
        self.history_data = {"prices": [], "times": []}
        self.predictions_obj = None
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."

state = AppState()

async def _attempt_binance_recovery():
    """Intenta recuperar los datos de Binance si estamos corriendo sobre fallback"""
    print("[Recovery] Intentando reconectar con Binance para sustituir histórico de supervivencia...")
    state.status_msg = "Reconectando con Binance..."

    # Force refresh salta la caché de 5 minutos y ataca a la red
    real_data = get_historical_data(168, force_refresh=True)

    if not real_data.get("is_fallback", True):
        print("[Éxito] Binance ha vuelto. Sustituyendo datos y reentrenando modelos...")
        state.is_fallback = False
        state.is_training = True
        state.status_msg = "Re-entrenando modelos con datos reales..."

        state.history_data = real_data
        success = state.predictor.train(state.history_data["prices"])

        if success:
            state.predictions_obj = state.predictor.predict_horizons(state.history_data["prices"])
            state.is_training = False
            state.status_msg = "Streaming Binance Activo."
            print("[Éxito] Modelos recalibrados. El sistema opera de nuevo con 100% datos reales.")

async def background_update_task():
    print("[INFO] V13 Supervivencia: Descargando histórico (168h)...")
    state.status_msg = "Conectando al mercado..."

    initial_data = get_historical_data(168)
    state.history_data = initial_data
    state.is_fallback = initial_data.get("is_fallback", False)

    if state.is_fallback:
        print("[Alerta] El sistema arranca con HISTÓRICO DE SUPERVIVENCIA. Se intentará recuperación en breve.")
        state.status_msg = "Entrenando IA con datos de supervivencia..."
    else:
        state.status_msg = "Entrenando IA con histórico real..."

    if state.history_data["prices"]:
        success = state.predictor.train(state.history_data["prices"])
        if success:
            print("[INFO] Modelos (1h, 2h, 4h, 24h) inicializados.")
            state.current_price = get_current_price()
            pred_result = state.predictor.predict_horizons(state.history_data["prices"])
            if pred_result:
                state.predictions_obj = pred_result
                # Solo evaluamos contra la realidad si el histórico no es de fallback (para no ensuciar la auditoría con mentiras matemáticas)
                if not state.is_fallback:
                    state.validator.record_new_prediction(state.current_price, pred_result)

                state.is_training = False
                state.status_msg = "Usando Datos Temporales (Fallback)" if state.is_fallback else "Streaming Binance Activo"
                print("[INFO] V13: Arranque del Motor Completado.")
            else:
                state.status_msg = "Error crudo en proyección. Reintentando..."
        else:
            state.status_msg = "Error crítico entrenando modelos. Reintentando..."

    # Loop de vida
    while state.is_running:
        try:
            state.current_price = get_current_price()

            if not state.is_training:
                # Si el sistema está vivo pero en Fallback, cada 60 iteraciones (~1 minuto) intenta reconectar
                if state.is_fallback and int(time.time()) % 60 == 0:
                    await _attempt_binance_recovery()
                    continue

                if state.history_data["prices"] and state.history_data["prices"][-1] != state.current_price:
                    state.history_data["prices"].append(state.current_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 168:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                # Auditoría solo si no estamos sobre datos de mentira
                if not state.is_fallback:
                    state.validator.update_actuals(state.current_price)

                pred_result = state.predictor.predict_horizons(state.history_data["prices"])

                if pred_result:
                    state.predictions_obj = pred_result

                    if not state.is_fallback:
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
            print(f"[ERROR] Loop fondo vivo: {e}")

        await asyncio.sleep(1.0)

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
    """El endpoint SIEMPRE devuelve el precio actual. Nunca bloquea la carga de la página (V13 Resiliente)"""

    response = {
        "precio_actual": state.current_price,
        "is_training": state.is_training,
        "is_fallback": state.is_fallback,
        "status_msg": state.status_msg
    }

    # Si la IA aún está calculando o hubo un fallo masivo que impidió llenar los objetos, devolvemos info parcial
    if state.is_training or not state.predictions_obj:
        # Enviamos el histórico parcial que haya para que el gráfico no esté en blanco total (solo la línea amarilla se irá dibujando)
        response["chart_data"] = {
            "history": {
                "prices": state.history_data["prices"],
                "times": state.history_data["times"]
            },
            "prediction": None
        }
        return response

    p_24h = state.predictions_obj["p_24h"]
    p_24h_pct = ((p_24h - state.current_price) / state.current_price) * 100

    now = int(time.time() * 1000)
    hour_ms = 3600000

    pred_prices = state.predictions_obj["interpolated_prices"]
    pred_bounds = state.predictions_obj["interpolated_bounds"]
    pred_times = [now + (i * hour_ms) for i in range(1, 25)]

    response.update({
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
                "anchor_indices": [0, 1, 3, 23]
            }
        }
    })

    return response
