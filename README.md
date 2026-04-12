# 🚀 BTC Predictive Analytics v12

¡Bienvenido a la versión v12! Esta plataforma es una herramienta **profesional y analítica**, diseñada bajo el principio de "Cero Maquillaje" y purgada de cualquier elemento lúdico, falso o engañoso. Su único objetivo es predecir el movimiento del precio de Bitcoin proyectando sus inferencias de forma cruda, para demostrar matemáticamente si la Inteligencia Artificial es superior al mercado ciego o no.

---

## 🌟 Novedades V12 - Saneamiento Total y Auditoría Transparente

En esta versión hemos ejecutado una purga masiva del repositorio. Adiós dependencias infladas, adiós Excel, adiós "simuladores virtuales" y adiós curvas que se mueven de forma irreal hacia la izquierda.

*   **⏳ Warm-up Inteligente (Arranque Seguro):** Al arrancar, el servidor no te servirá una página rota ni "vacía". La API bloquea todas las conexiones hasta que la ingesta de las 168 horas históricas y el entrenamiento de los modelos estén garantizados.
*   **🧠 Red Neuronal de Horizontes Múltiples:** La IA usa 4 modelos Random Forest entrenados independientemente para predecir puntos exactos a +1h, +2h, +4h y +24h.
*   **📊 Gráfico Evolutivo de 192 Horas:** El eje X está **fijo y bloqueado**. A la izquierda, 168 horas de pasado real. A la derecha, 24 horas de futuro, trazando una interpolación matemática lineal (recta pura, no curvas falsas suavizadas) que conecta el AHORA exclusivamente con los cuatro anclajes predichos.
*   **🧐 Auditoría Desglosada vs Baseline:** En la parte superior derecha verás la comparación cara a cara del *Error Medio (MAE)* de la IA frente al MAE de no hacer nada ("Baseline Naive"). **¡Ya no tienes que esperar 24 horas para ver resultados!** En cuanto pasa la primera hora, la tarjeta "+1h" despierta y te evalúa.
*   **📁 Tracking Persistente y Nativo:** Los datos de evaluación interna se almacenan eficientemente en memoria mediante un archivo nativo ligero (`history.json`) que sobrevive entre reinicios.

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

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Espera unos 5 segundos a que la consola negra inicie el "Warm-up" (carga de histórico y entrenamiento).
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis técnico predictivo algorítmico y de Big Data. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones matemáticas avanzadas. El autor no se hace responsable de pérdidas financieras derivadas del uso de este código como oráculo único.*
