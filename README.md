# 🚀 BTC Predictive Analytics v10

¡Bienvenido a la versión v10! Esta plataforma es una herramienta **profesional y analítica**, diseñada bajo el principio de "Cero Maquillaje". Su único objetivo es predecir el movimiento del precio de Bitcoin y demostrarte matemáticamente si el modelo es superior al mercado o no.

---

## 🌟 Novedades V10 - Verdad y Auditoría Pura

Hemos rehecho por completo el cerebro de la aplicación para dejar de "dibujar curvas bonitas" y empezar a predecir puntos críticos de forma honesta.

*   **🧠 Red Neuronal de Horizontes Múltiples:** La IA ya no predice 24 horas usando regresiones encadenadas que degradan la precisión. Ahora usa 4 modelos Random Forest entrenados independientemente para predecir exclusivamente +1h, +2h, +4h y +24h.
*   **📊 Gráfico Evolutivo Congelado (-168h a +24h):** El eje X del gráfico nunca bailará. Tienes siempre a la izquierda la última semana de mercado exacta, y a la derecha los cuatro anclajes del futuro unidos por líneas rectas. Lo que ves es lo que la IA predijo de forma estricta, sin curvas suavizadas que confundan el análisis.
*   **🧐 Auditoría vs Baseline (Naive):** ¿Realmente la IA sirve de algo? En el panel derecho verás la comparación cara a cara del *Error Medio Absoluto (MAE)* de la Inteligencia Artificial frente al "Baseline Naive" (un modelo ignorante que asume que el precio de mañana será idéntico al de hoy). Si el MAE de la IA es menor, el panel se vuelve verde: la IA bate al mercado. Si es rojo, la IA lo hace peor que no hacer nada.
*   **📁 Tracking Persistente y en Vivo:** Todos estos cálculos se basan en predicciones pasadas que la aplicación anotó y validó hora a hora, guardándolas en memoria de forma persistente (`history.json`) para que reinicies tu ordenador sin perder la trazabilidad del rendimiento.

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, marca siempre la casilla **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Haz doble clic en el archivo **`install.bat`**.
2.  Una pantalla negra creará el entorno seguro y descargará las librerías matemáticas (Pandas, Scikit-learn, Numpy, Requests) necesarias.
3.  Cuando veas "INSTALACION COMPLETADA CON EXITO", puedes pulsar cualquier tecla para cerrar.
    *Esto solo se hace la primera vez.*

---

## 🚀 Cómo Ejecutar

1.  Haz doble clic en el archivo **`run.bat`**.
2.  Mantén abierta la ventana negra que aparece. Es el cerebro del evaluador corriendo de fondo, pidiendo datos a Binance cada segundo.
3.  Abre tu navegador (Chrome, Edge...) y entra en: `http://localhost:8000`

---

**¡Aviso Legal!**
*Este software es una plataforma de análisis técnico predictivo algorítmico y de Big Data. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones matemáticas avanzadas. El autor no se hace responsable de pérdidas financieras derivadas del uso de este código como oráculo único.*
