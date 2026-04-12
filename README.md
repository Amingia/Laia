# 🚀 BTC Predictive Analytics v9

¡Bienvenido a la versión definitiva v9! Esta plataforma es una herramienta **profesional y analítica** impulsada por Inteligencia Artificial diseñada exclusivamente para **predecir el movimiento del precio de Bitcoin en las próximas 24 horas**.

No encontrarás aquí herramientas para "jugar a hacer trading", "simuladores" ni "carteras virtuales". Esto es una máquina de datos puros que utiliza un modelo de Machine Learning (**Random Forest Regressor**) enriquecido con *Feature Engineering* (Momentum, Medias Móviles, Aceleración, Volatilidad y Volumen Real) sobre los datos en tiempo real de **Binance**.

---

## 🌟 Novedades V9 - Predicción Analítica Pura y Exacta

En esta versión hemos transformado y corregido todos los vicios del proyecto:

*   **📈 Tiempo Real "Real":** El precio actual de Bitcoin y la proyección gráfica bailan de forma viva y fluida. Se implementó un polling extremadamente optimizado (1.5 segundos) que te da sensación de *WebSocket* directo contra Binance, pero sin problemas de proxy en Windows. Si el precio real cambia, tu pantalla cambia.
*   **🧠 Curva Evolutiva Realista:** Atrás quedaron las predicciones "en línea recta" con saltos estéticos entre pasado y futuro. La IA ahora proyecta una curva suavizada que *continúa perfectamente* el punto exacto del mercado actual. Inyecta la inercia (momentum) y la "texturiza" suavemente con la volatilidad real pasada para una plausibilidad visual total.
*   **📊 Ventana Gráfica de Proporciones Ideales:** Tu vista histórica no se deformará ni desaparecerá. Tienes garantizados los últimos dos días completos (48 horas) de Binance en la zona amarilla, frente a 24 horas en la zona proyectada.
*   **📁 Validación Interna Transparente:** La aplicación *se auto-evalúa* para demostrarte si acierta o miente. Cada predicción horaria se registra internamente en un archivo liviano (`history.json`) que sobrevive aunque apagues tu ordenador. Cuando la hora H se cumple y Binance dictamina el precio real, la app compara, calcula el Porcentaje de Acierto y el Error Absoluto y te lo muestra. Si no hay datos maduros, es sincera y te dice "Aún recopilando...".

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, marca siempre la casilla **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Haz doble clic en el archivo **`install.bat`**.
2.  Una pantalla negra creará el entorno seguro y descargará las librerías matemáticas (Pandas, Scikit-learn, Numpy, Requests) necesarias sin que tengas que hacer nada.
3.  Cuando veas "INSTALACION COMPLETADA CON EXITO", puedes pulsar cualquier tecla para cerrar.
    *Esto solo se hace la primera vez.*

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Mantén abierta la ventana negra que aparece. Es el cerebro del evaluador corriendo de fondo, pidiendo datos a Binance y guardando estadísticas en el registro.
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis técnico predictivo algorítmico y de Big Data. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones matemáticas avanzadas. El autor no se hace responsable de pérdidas financieras derivadas del uso de este código como oráculo único.*
