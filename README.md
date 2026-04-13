# 🚀 BTC Predictive Analytics v13

¡Bienvenido a la versión definitiva v13! Esta plataforma es una herramienta **profesional y analítica**, diseñada bajo el principio de "Cero Maquillaje". Su único objetivo es predecir el movimiento del precio de Bitcoin y demostrarte matemáticamente si el modelo es superior al mercado o no.

---

## 🌟 Novedades V13 - Resiliencia y Flujo Asíncrono

En esta versión hemos eliminado los bloqueos fatales del sistema y blindado la aplicación contra las caídas de Binance. ¡La aplicación **NUNCA** se quedará con la pantalla en blanco!

*   **🛡️ Modo Supervivencia (Anti-Bloqueos):** Si Binance rechaza la conexión en el arranque por restricciones regionales o Rate Limits (Error 451/429), la app ya no colapsará. Inyectará instantáneamente un histórico matemático de supervivencia anclado al precio actual, entrenará la IA de emergencia, y te mostrará el panel completo en el segundo 1 con un **Banner de Advertencia Rojo**. Cada 60 segundos, el sistema intentará reconectar silenciosamente con Binance para sustituir el histórico de mentira por el real.
*   **⏳ Renderizado "Zero-Wait" Asíncrono:** Atrás quedó la espantosa pantalla de "Inicializando motor...". Ahora, en cuanto abres la app, verás el precio de Bitcoin en vivo saltando cada segundo, mientras que en la tarjeta de predicción leerás "Entrenando IA...". La gráfica se irá dibujando con lo que haya, y cuando los 4 modelos acaben su trabajo pesado de trasfondo, la curva predictiva aparecerá de golpe por arte de magia, sin congelar tu PC.
*   **🧠 Red Neuronal de Horizontes Múltiples:** La IA predice puntos exactos a +1h, +2h, +4h y +24h.
*   **📊 Gráfico Fijo Interpolado:** El eje X del gráfico nunca bailará (168h pasado vs 24h futuro). La proyección futura no es un ruido inventado, sino una interpolación matemática lineal (una recta honesta) que une los 4 puntos validados del Random Forest, destacándolos visualmente en el gráfico.
*   **🧐 Auditoría vs Baseline (Naive):** ¿Sirve de algo la IA? La tarjeta de auditoría te muestra en vivo el Error Medio de la IA (MAE) contra el "Baseline Naive" a medida que cada horizonte temporal madura.

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, marca siempre la casilla **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Haz doble clic en el archivo **`install.bat`**.
2.  Una pantalla negra creará el entorno seguro y descargará las librerías matemáticas (`fastapi`, `uvicorn`, `scikit-learn`, `numpy`, `requests`).
3.  Cuando veas "INSTALACION COMPLETADA CON EXITO", puedes pulsar cualquier tecla para cerrar.

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Mantén abierta la ventana negra que aparece. Es el cerebro asíncrono corriendo de fondo.
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`. ¡Verás los datos en vivo inmediatamente!

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis predictivo. NO DEBE utilizarse para operar dinero real. El autor no se hace responsable de pérdidas financieras.*
