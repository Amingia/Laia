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
        # Estructura limpia y estandarizada por defecto (evita Nulls en el frontend)
        self.predictions_obj = {
            "p_24h": None,
            "p_24h_pct": None,
            "interpolated_prices": [],
            "interpolated_bounds": []
        }
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."

state = AppState()

async def _attempt_binance_recovery():
    print("[Recovery] Intentando reconectar con Binance para sustituir histórico de supervivencia...")
    state.status_msg = "Reconectando con Binance..."

    real_data = get_historical_data(168, force_refresh=True)

    if not real_data.get("is_fallback", True):
        print("[Éxito] Binance ha vuelto. Sustituyendo datos y reentrenando modelos...")
        state.is_fallback = False
        state.is_training = True
        state.status_msg = "Re-entrenando modelos con datos reales..."

        state.history_data = real_data
        success = state.predictor.train(state.history_data["prices"])

        if success:
            pred_result = state.predictor.predict_horizons(state.history_data["prices"])
            if pred_result:
                state.predictions_obj = pred_result
                state.is_training = False
                state.status_msg = "Streaming Binance Activo."
                print("[Éxito] Modelos recalibrados con 100% datos reales.")

async def background_update_task():
    print("[INFO] V14 Debug: Descargando histórico (168h)...")
    state.status_msg = "Conectando al mercado..."

    initial_data = get_historical_data(168)
    state.history_data = initial_data
    state.is_fallback = initial_data.get("is_fallback", False)

    if state.is_fallback:
        print("[Alerta] El sistema arranca con HISTÓRICO DE SUPERVIVENCIA. Se intentará recuperación cada 60s.")
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
                if not state.is_fallback:
                    state.validator.record_new_prediction(state.current_price, pred_result)

                state.is_training = False
                state.status_msg = "Modo Supervivencia Activo" if state.is_fallback else "Streaming Binance Activo"
                print("[INFO] V14: Arranque del Motor Completado.")
            else:
                state.status_msg = "Generando proyección..."
        else:
            state.status_msg = "Recabando datos suficientes..."

    # Loop principal (1.5s)
    while state.is_running:
        try:
            state.current_price = get_current_price()

            if not state.is_training:
                # Si estamos sobre fallback, intentamos reconectar cada minuto
                if state.is_fallback and int(time.time()) % 60 == 0:
                    await _attempt_binance_recovery()
                    continue

                # Actualizar histórico en vivo
                if state.history_data["prices"] and state.history_data["prices"][-1] != state.current_price:
                    state.history_data["prices"].append(state.current_price)
                    state.history_data["times"].append(int(time.time() * 1000))

                    if len(state.history_data["prices"]) > 168:
                        state.history_data["prices"].pop(0)
                        state.history_data["times"].pop(0)

                # Evaluar
                if not state.is_fallback:
                    state.validator.update_actuals(state.current_price)

                # Predecir
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
            print(f"[ERROR] Loop de vida V14: {e}")

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
    """
    ENDPOINT V14 BLINDADO:
    Siempre devuelve una estructura JSON estricta. Cero Nones en arrays.
    El Frontend puede parsearlo sin crashear aunque el backend aún esté calculando.
    """

    # 1. Datos básicos siempre disponibles
    response = {
        "precio_actual": state.current_price if state.current_price else 0.0,
        "is_training": state.is_training,
        "is_fallback": state.is_fallback,
        "status_msg": state.status_msg,
        "tendencia": state.trend if not state.is_training else "Entrenando modelo inicial...",
        "prediccion_24h_usd": 0.0,
        "prediccion_24h_pct": 0.0,
        "evaluacion": state.validator.get_metrics(),
        "chart_data": {
            "history": {
                "prices": state.history_data["prices"],
                "times": state.history_data["times"]
            },
            "prediction": {
                "prices": [],
                "bounds_pct": [],
                "times": [],
                "anchor_indices": []
            }
        }
    }

    # 2. Si ya hay predicción, rellenamos de forma segura
    if not state.is_training and state.predictions_obj and "p_24h" in state.predictions_obj:
        p_24h = state.predictions_obj.get("p_24h", 0)

        if state.current_price and state.current_price > 0:
            p_24h_pct = ((p_24h - state.current_price) / state.current_price) * 100
        else:
            p_24h_pct = 0.0

        response["prediccion_24h_usd"] = round(p_24h, 2)
        response["prediccion_24h_pct"] = round(p_24h_pct, 2)

        now = int(time.time() * 1000)
        hour_ms = 3600000

        # Recuperamos arrays garantizando su existencia (por si están vacíos)
        pred_prices = state.predictions_obj.get("interpolated_prices", [])
        pred_bounds = state.predictions_obj.get("interpolated_bounds", [])

        # Generar timestamps proyectados asumiendo que arranca AHORA y da saltos de 1h
        pred_times = [now + (i * hour_ms) for i in range(1, len(pred_prices) + 1)]

        response["chart_data"]["prediction"] = {
            "prices": pred_prices,
            "bounds_pct": pred_bounds,
            "times": pred_times,
            "anchor_indices": [0, 1, 3, 23] # Coordenadas matemáticas fijas de los 4 Nodos Random Forest
        }

    return response
