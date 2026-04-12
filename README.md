# 🚀 BTC Predictive Analytics v8

¡Bienvenido a la versión definitiva v8! Esta plataforma es una herramienta **profesional y analítica** impulsada por Inteligencia Artificial diseñada exclusivamente para **predecir el movimiento del precio de Bitcoin en las próximas 24 horas**.

No encontrarás aquí herramientas para "jugar a hacer trading", "simuladores" ni "carteras virtuales". Esto es una máquina de datos puros que utiliza un modelo **Random Forest Regressor** enriquecido con *Feature Engineering* (Momentum, Medias Móviles, Aceleración, Volatilidad y Volumen Real) sobre los datos en tiempo real de **Binance**.

---

## 🌟 Novedades V8 - Predicción Analítica Pura

En esta versión hemos transformado el proyecto:

*   **📈 Tiempo Real "Real":** La conexión al mercado de Binance (BTCUSDT) es casi instantánea (polling agresivo optimizado de 2 segundos). Sentirás el sistema vivo.
*   **🧠 Predicción Realista y Orgánica:** Atrás quedaron las predicciones "en línea recta". La IA ahora analiza 300 velas históricas e incorpora inercia de mercado, generando una curva de 24h suave que no da saltos bruscos al conectarse con el precio "AHORA".
*   **📊 Banda de Incertidumbre:** La zona sombreada verde o roja que envuelve la predicción no es aleatoria. Se calcula matemáticamente basándose en la volatilidad real del precio. Si la banda es estrecha, el modelo está seguro; si se ensancha mucho, el mercado está loco.
*   **📁 Validación Científica (Excel Automático):** La IA no solo dice hacia dónde irá el precio, sino que **se somete a examen**. El sistema guarda silenciosamente cada predicción en el archivo `predicciones.xlsx`. A medida que pasan las horas, anota el "Precio Real" que hubo y calcula el Porcentaje de Acierto y el Error Medio (MAE). Podrás ver la precisión real directamente en el Dashboard.

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, marca siempre la casilla **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Haz doble clic en el archivo **`install.bat`**.
2.  Una pantalla negra creará el entorno seguro y descargará las librerías matemáticas (Pandas, Scikit-learn, Openpyxl...) necesarias sin que tengas que hacer nada.
3.  Cuando veas "INSTALACION COMPLETADA CON EXITO", puedes pulsar cualquier tecla para cerrar.
    *Esto solo se hace la primera vez.*

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Mantén abierta la ventana negra que aparece. Es el cerebro del evaluador corriendo de fondo y guardando datos en el Excel.
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis técnico predictivo. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones avanzadas. El autor no se hace responsable de pérdidas financieras derivadas del uso de este algoritmo.*
