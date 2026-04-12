# 🚀 BTC Predictive Analytics v11

¡Bienvenido a la versión definitiva v11! Esta plataforma es una herramienta **profesional y puramente analítica**, diseñada bajo el principio de "Cero Maquillaje". Su único objetivo es predecir el movimiento del precio de Bitcoin en el tiempo y demostrarte matemáticamente si la Inteligencia Artificial es superior a la Inercia del mercado.

---

## 🌟 Novedades V11 - Saneamiento Total y Auditoría Constante

En esta versión hemos eliminado todas las redundancias y dependencias pesadas (adiós a `pandas` y `openpyxl`) para construir el motor analítico definitivo:

*   **🧠 Red Neuronal de Horizontes Múltiples:** La IA no predice usando curvas extrapoladas inventadas. Ahora usa 4 modelos Random Forest entrenados independientemente para predecir puntos exactos a +1h, +2h, +4h y +24h en el futuro.
*   **📊 Gráfico Evolutivo Congelado (-168h a +24h):** El gráfico de análisis es estricto. A la izquierda verás 7 días completos de mercado con el precio histórico de Binance. A la derecha, los 4 nodos de predicción de la IA. El eje no resbala, no pierde contexto y no se deforma.
*   **🧐 Auditoría Desglosada vs Baseline:** ¿Sirve de algo el modelo? En el panel derecho superior verás la comparación cara a cara del *Error Absoluto Medio (MAE)* de la IA frente al MAE de no hacer nada ("Baseline Naive"). **¡Ya no tienes que esperar 24 horas para ver resultados!** A la primera hora de uso, la tarjeta "despertará" para mostrarte el rendimiento del modelo +1H.
*   **📁 Tracking Persistente y Nativo:** Los datos de evaluación interna se almacenan eficientemente en memoria mediante un archivo nativo ligero (`history.json`).

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, marca siempre la casilla **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Haz doble clic en el archivo **`install.bat`**.
2.  Una pantalla negra creará el entorno seguro y descargará las librerías matemáticas estrictamente necesarias (`fastapi`, `uvicorn`, `scikit-learn`, `numpy`, `requests`).
3.  Cuando veas "INSTALACION COMPLETADA CON EXITO", puedes pulsar cualquier tecla para cerrar.
    *Esto solo se hace la primera vez.*

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Mantén abierta la ventana negra que aparece. Es el cerebro del evaluador corriendo de fondo, pidiendo datos a Binance cada segundo y validando su memoria.
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis técnico predictivo algorítmico y de Big Data. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones matemáticas avanzadas. El autor no se hace responsable de pérdidas financieras derivadas del uso de este código como oráculo único.*
