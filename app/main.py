from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import time
import sys
import traceback
from contextlib import asynccontextmanager

from app.data.fetcher import get_current_price, get_historical_data
from app.model.predictor import AnalyticsPredictor
from app.evaluation.internal_tracker import InternalValidator

class AppState:
    def __init__(self):
        self.is_ready = False
        self.is_training = True
        self.is_fallback = False
        self.status_msg = "Iniciando motor..."

        self.current_price = 65000.0
        self.history_data = {"prices": [], "times": []}
        self.predictions_obj = {
            "p_24h": None,
            "p_24h_pct": None,
            "interpolated_prices": [],
            "interpolated_bounds": [],
            "anchor_indices": []
        }
        self.predictor = AnalyticsPredictor()
        self.validator = InternalValidator()
        self.is_running = True
        self.trend = "Analizando..."

state = AppState()

async def execute_warmup():
    print("[V15] INICIANDO SECUENCIA WARM-UP (Max 5s)...")
    state.status_msg = "Descargando histórico de Binance (168h)..."

    initial_data = get_historical_data(168)
    state.history_data = initial_data
    state.is_fallback = initial_data.get("is_fallback", False)

    if state.is_fallback:
        print("[V15 ALERTA] Fallo masivo en Binance. Usando histórico matemático de supervivencia.")
        state.status_msg = "Entrenando IA con datos de supervivencia..."
    else:
        state.status_msg = "Entrenando redes neuronales (1h, 2h, 4h, 24h)..."

    if state.history_data["prices"]:
        success = state.predictor.train(state.history_data["prices"])
        if success:
            print("[V15] Modelos entrenados correctamente.")
            state.status_msg = "Generando proyecciones iniciales..."

            state.current_price = get_current_price()
            pred_result = state.predictor.predict_horizons(state.history_data["prices"])

            if pred_result:
                state.predictions_obj = pred_result
                if not state.is_fallback:
                    state.validator.record_new_prediction(state.current_price, pred_result)
                print("[V15] Proyección lista.")
            else:
                print("[V15 ERROR] El modelo falló al predecir. Arrancando sin predicciones.")
        else:
            print("[V15 ERROR] Entrenamientos fallidos por falta de datos. Arrancando solo con gráfico.")
    else:
        print("[V15 FATAL] No se pudo obtener histórico de ninguna manera. Arrancando en vacío total.")

async def _attempt_binance_recovery():
    print("[V15 Recovery] Intentando reconectar con Binance para sanear histórico...")
    state.status_msg = "Intentando salir del Modo Supervivencia..."

    # Intento agresivo bloqueante leve
    real_data = get_historical_data(168, force_refresh=True)

    if not real_data.get("is_fallback", True):
        print("[V15 ÉXITO] Binance responde. Saneando la memoria de la IA...")
        state.is_fallback = False
        state.is_training = True
        state.status_msg = "Re-entrenando modelos con datos reales de Binance..."

        state.history_data = real_data
        success = state.predictor.train(state.history_data["prices"])

        if success:
            pred = state.predictor.predict_horizons(state.history_data["prices"])
            if pred:
                state.predictions_obj = pred
                state.is_training = False
                state.status_msg = "Streaming Binance Estable"
                print("[V15 ÉXITO] IA recalibrada y recuperada del modo supervivencia.")

async def background_update_task():
    try:
        # Timeout Asesino de 5 Segundos
        await asyncio.wait_for(execute_warmup(), timeout=5.0)
    except asyncio.TimeoutError:
        print("[V15 CRÍTICO] TIMEOUT ALCANZADO (5s). Abortando Warm-up limpio y forzando arranque degradado.")
        state.status_msg = "Timeout de conexión. Arrancando en modo degradado."

        # Inyectar emergencia absoluta si todo petó
        if not state.history_data["prices"]:
            print("[V15 CRÍTICO] Inyectando datos de emergencia absoluta para evitar pantalla blanca.")
            from app.data.fetcher import _generate_fallback_history
            state.history_data = _generate_fallback_history(168)
            state.is_fallback = True

        # Entrenar por las malas con lo que haya
        state.predictor.train(state.history_data["prices"])
        pred = state.predictor.predict_horizons(state.history_data["prices"])
        if pred: state.predictions_obj = pred

    except Exception as e:
        print(f"[V15 ERROR FATAL EN WARM-UP] {e}")
        traceback.print_exc()

    # Pase lo que pase en el warm-up, DESBLOQUEAMOS LA API AQUI OBLIGATORIAMENTE
    print("[V15] API DESBLOQUEADA: is_training=False, is_ready=True")
    state.is_training = False
    state.is_ready = True
    if state.is_fallback:
        state.status_msg = "Modo Supervivencia Activo (Binance Caído)"
    else:
        state.status_msg = "Analizando mercado en tiempo real..."

    # Loop Infinito de Refresco
    while state.is_running:
        if state.is_ready:
            try:
                # 1. Recuperar Conexión si estamos en Fallback (1 vez por minuto)
                if state.is_fallback and int(time.time()) % 60 == 0:
                    await _attempt_binance_recovery()
                    await asyncio.sleep(1.0)
                    continue

                # 2. Precio en vivo
                new_price = get_current_price()
                if new_price and new_price > 0:
                    state.current_price = new_price

                    # 3. Empalme histórico
                    if not state.history_data["prices"] or state.history_data["prices"][-1] != new_price:
                        state.history_data["prices"].append(new_price)
                        state.history_data["times"].append(int(time.time() * 1000))

                        if len(state.history_data["prices"]) > 168:
                            state.history_data["prices"].pop(0)
                            state.history_data["times"].pop(0)

                    # 4. Auditoría (Solo si no hay datos falsos corriendo)
                    if not state.is_fallback:
                        state.validator.update_actuals(state.current_price)

                    # 5. Predecir
                    pred_result = state.predictor.predict_horizons(state.history_data["prices"])

                    if pred_result:
                        state.predictions_obj = pred_result
                        if not state.is_fallback:
                            state.validator.record_new_prediction(state.current_price, pred_result)

                        p_24h = pred_result.get("p_24h")
                        if p_24h:
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
                print(f"[V15 ERROR LOOP FONDO] {e}")

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
    ENDPOINT V15 ANTI-BLOQUEO:
    Si la app acaba de arrancar y el warmup no termina, devuelve is_training=True
    y el Frontend pinta un estado degradado temporal, pero no se congela en blanco.
    Si todo está bien, devuelve la estructura exacta que ChartJS espera.
    """

    response = {
        "precio_actual": state.current_price if state.current_price else 65000.0,
        "is_training": state.is_training,
        "is_fallback": state.is_fallback,
        "status_msg": state.status_msg,
        "tendencia": state.trend if not state.is_training else "Procesando modelo...",
        "prediccion_24h_usd": 0.0,
        "prediccion_24h_pct": 0.0,
        "evaluacion": state.validator.get_metrics() if not state.is_training else None,
        "chart_data": {
            "history": {
                "prices": state.history_data["prices"] if state.history_data["prices"] else [],
                "times": state.history_data["times"] if state.history_data["times"] else []
            },
            "prediction": {
                "prices": [],
                "bounds_pct": [],
                "times": [],
                "anchor_indices": []
            }
        }
    }

    if not state.is_training and state.predictions_obj and "p_24h" in state.predictions_obj:
        p_24h = state.predictions_obj.get("p_24h")
        if p_24h and state.current_price > 0:
            response["prediccion_24h_usd"] = round(p_24h, 2)
            response["prediccion_24h_pct"] = round(((p_24h - state.current_price) / state.current_price) * 100, 2)

        now = int(time.time() * 1000)
        hour_ms = 3600000

        pred_prices = state.predictions_obj.get("interpolated_prices", [])
        pred_bounds = state.predictions_obj.get("interpolated_bounds", [])

        if pred_prices:
            pred_times = [now + (i * hour_ms) for i in range(1, len(pred_prices) + 1)]

            response["chart_data"]["prediction"] = {
                "prices": pred_prices,
                "bounds_pct": pred_bounds,
                "times": pred_times,
                "anchor_indices": [0, 1, 3, 23]
            }

    return response
