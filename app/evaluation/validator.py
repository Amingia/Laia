import pandas as pd
import os
from datetime import datetime, timedelta

EXCEL_FILE = "predicciones.xlsx"

class ExcelValidator:
    def __init__(self):
        self.filename = EXCEL_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=[
                "Fecha_Hora_Prediccion",
                "Precio_Real_Actual",
                "Prediccion_1h", "Precio_Real_1h", "Error_1h_Pct",
                "Prediccion_2h", "Precio_Real_2h", "Error_2h_Pct",
                "Prediccion_4h", "Precio_Real_4h", "Error_4h_Pct",
                "Prediccion_24h", "Precio_Real_24h", "Error_24h_Pct",
                "Tendencia_Proyectada", "Acierto_Direccional",
                "MAE_Promedio_Fila"
            ])
            df.to_excel(self.filename, index=False)

    def record_new_prediction(self, current_price, prediction_array):
        """
        Graba una nueva fila (foto) en el Excel con la predicción actual.
        Solo se llamará 1 vez cada hora o cuando el modelo se estabilice fuertemente.
        prediction_array debe tener [now, +1h, +2h... +24h]
        """
        if not prediction_array or len(prediction_array) < 25:
            return

        try:
            df = pd.read_excel(self.filename)

            # Evitar inundar el Excel: Solo registrar si pasó al menos 1 hora desde el último registro
            if not df.empty:
                last_time_str = df.iloc[-1]["Fecha_Hora_Prediccion"]
                last_time = pd.to_datetime(last_time_str)
                if datetime.now() - last_time < timedelta(minutes=55):
                    return # Ya hemos registrado una predicción en la última hora

            p_1h = prediction_array[1]
            p_2h = prediction_array[2]
            p_4h = prediction_array[4]
            p_24h = prediction_array[24]

            tendencia = "Alcista" if p_24h > current_price else "Bajista"

            new_row = {
                "Fecha_Hora_Prediccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Precio_Real_Actual": round(current_price, 2),
                "Prediccion_1h": round(p_1h, 2),
                "Precio_Real_1h": None,
                "Error_1h_Pct": None,
                "Prediccion_2h": round(p_2h, 2),
                "Precio_Real_2h": None,
                "Error_2h_Pct": None,
                "Prediccion_4h": round(p_4h, 2),
                "Precio_Real_4h": None,
                "Error_4h_Pct": None,
                "Prediccion_24h": round(p_24h, 2),
                "Precio_Real_24h": None,
                "Error_24h_Pct": None,
                "Tendencia_Proyectada": tendencia,
                "Acierto_Direccional": None,
                "MAE_Promedio_Fila": None
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(self.filename, index=False)
            print("[Excel] Nueva predicción registrada correctamente.")

        except Exception as e:
            print(f"[Excel Error] No se pudo guardar la nueva predicción: {e}")

    def update_actuals(self, current_price):
        """
        Rellena los huecos vacíos en las filas pasadas (Precio_Real_1h, Precio_Real_2h...)
        calculando si la IA acertó en base a la hora actual.
        """
        try:
            df = pd.read_excel(self.filename)
            if df.empty:
                return

            now = datetime.now()
            modified = False

            for idx, row in df.iterrows():
                row_time = pd.to_datetime(row["Fecha_Hora_Prediccion"])
                time_diff = now - row_time

                # Check 1H
                if pd.isna(row["Precio_Real_1h"]) and time_diff >= timedelta(hours=1) and time_diff < timedelta(hours=1, minutes=15):
                    df.at[idx, "Precio_Real_1h"] = round(current_price, 2)
                    df.at[idx, "Error_1h_Pct"] = abs(current_price - row["Prediccion_1h"]) / row["Prediccion_1h"] * 100
                    modified = True

                # Check 2H
                if pd.isna(row["Precio_Real_2h"]) and time_diff >= timedelta(hours=2) and time_diff < timedelta(hours=2, minutes=15):
                    df.at[idx, "Precio_Real_2h"] = round(current_price, 2)
                    df.at[idx, "Error_2h_Pct"] = abs(current_price - row["Prediccion_2h"]) / row["Prediccion_2h"] * 100
                    modified = True

                # Check 4H
                if pd.isna(row["Precio_Real_4h"]) and time_diff >= timedelta(hours=4) and time_diff < timedelta(hours=4, minutes=15):
                    df.at[idx, "Precio_Real_4h"] = round(current_price, 2)
                    df.at[idx, "Error_4h_Pct"] = abs(current_price - row["Prediccion_4h"]) / row["Prediccion_4h"] * 100
                    modified = True

                # Check 24H (Final Evaluation)
                if pd.isna(row["Precio_Real_24h"]) and time_diff >= timedelta(hours=24):
                    df.at[idx, "Precio_Real_24h"] = round(current_price, 2)
                    df.at[idx, "Error_24h_Pct"] = abs(current_price - row["Prediccion_24h"]) / row["Prediccion_24h"] * 100

                    # Calcular Acierto Direccional (si subió o bajó realmente comparado a la predicción)
                    pred_diff = row["Prediccion_24h"] - row["Precio_Real_Actual"]
                    real_diff = current_price - row["Precio_Real_Actual"]

                    if (pred_diff > 0 and real_diff > 0) or (pred_diff < 0 and real_diff < 0):
                        df.at[idx, "Acierto_Direccional"] = "Sí"
                    else:
                        df.at[idx, "Acierto_Direccional"] = "No"

                    # Promediar errores
                    errors = [df.at[idx, "Error_1h_Pct"], df.at[idx, "Error_2h_Pct"], df.at[idx, "Error_4h_Pct"], df.at[idx, "Error_24h_Pct"]]
                    valid_errors = [e for e in errors if pd.notna(e)]
                    if valid_errors:
                        df.at[idx, "MAE_Promedio_Fila"] = sum(valid_errors) / len(valid_errors)

                    modified = True

            if modified:
                df.to_excel(self.filename, index=False)
                print("[Excel] Actualizado historial con precios reales y errores calculados.")

        except Exception as e:
            print(f"[Excel Error] No se pudo actualizar el histórico: {e}")

    def get_live_metrics(self):
        """Calcula el % de acierto global y el error medio desde el Excel para pasarlo a la UI."""
        try:
            df = pd.read_excel(self.filename)

            # MAE 24h
            mae_24 = df["Error_24h_Pct"].mean() if not df["Error_24h_Pct"].isna().all() else 0.0

            # % Acierto Direccional
            aciertos = df[df["Acierto_Direccional"] == "Sí"].shape[0]
            fallos = df[df["Acierto_Direccional"] == "No"].shape[0]
            total = aciertos + fallos
            accuracy = (aciertos / total * 100) if total > 0 else 0.0

            return {
                "mae": round(mae_24, 2) if mae_24 else None,
                "accuracy": round(accuracy, 1) if total > 0 else None,
                "total_evaluadas": total
            }
        except:
            return {"mae": None, "accuracy": None, "total_evaluadas": 0}
