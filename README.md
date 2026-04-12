# 🚀 IA Bitcoin Predictor & Auto-Trader

¡Bienvenido! Este programa es una herramienta completa impulsada por Inteligencia Artificial que analiza el mercado de Bitcoin en tiempo real, realiza predicciones a futuro y simula estrategias de trading automáticas, ¡todo desde un único panel muy fácil de usar!

No necesitas ser un experto en programación o en criptomonedas para hacerlo funcionar. Sigue los pasos a continuación.

---

## 🌟 Características Principales

*   **📊 Datos en Tiempo Real:** Obtiene el precio real de Bitcoin desde Binance automáticamente cada pocos segundos sin que tengas que recargar la página.
*   **🤖 Predicción con IA:** Utiliza Machine Learning (Random Forest) para predecir hacia dónde irá el precio en las próximas 24 horas. ¡Y aprende de sus errores para auto-corregirse!
*   **🧠 Motor de Decisiones:** Analiza los datos del mercado, simula tendencias de noticias/redes sociales y actividad de "ballenas", para decidir si el mejor movimiento ahora es COMPRAR, VENDER o MANTENER.
*   **💸 Simulador de Trading:** Empieza con 1000€ virtuales. El sistema operará de manera autónoma siguiendo las recomendaciones de la IA, permitiéndote ver cómo le iría a tu dinero real sin tomar riesgos. Todo esto mostrado en un historial de operaciones en vivo.
*   **💻 Panel Intuitivo (Dashboard):** Una interfaz web clara con gráficos, lista para ver en cualquier navegador.

---

## 🛠️ Requisitos Previos

Para ejecutar este programa en tu ordenador con Windows, solo necesitas tener instalado **Python**.

1.  Ve a la página oficial de Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  Descarga la última versión para Windows.
3.  **¡MUY IMPORTANTE!** Durante la instalación, fíjate bien en la primera ventana que aparece y asegúrate de marcar la casilla que dice **"Add Python to PATH"** (o "Add python.exe to PATH") antes de darle a "Install Now".

---

## ⚙️ Cómo Instalar

1.  Asegúrate de que tienes todos los archivos de esta carpeta juntos.
2.  Haz doble clic en el archivo llamado **`install.bat`**.
3.  Verás una pantalla negra (consola) que hará algunas cosas automáticamente. Esto está preparando el programa y descargando lo necesario para que la IA funcione.
4.  Cuando termine, te avisará con un mensaje de "INSTALACION COMPLETADA CON EXITO". Pulsa cualquier tecla para cerrar la ventana.
    *¡Este paso solo tienes que hacerlo la primera vez!*

---

## 🚀 Cómo Ejecutar el Programa

1.  Haz doble clic en el archivo llamado **`run.bat`**.
2.  Se abrirá una pantalla negra que mantendrá funcionando "el cerebro" del programa y la conexión con el mercado. **No cierres esta ventana** mientras quieras usar el programa.
3.  Abre tu navegador de internet favorito (Chrome, Firefox, Edge, etc.).
4.  Escribe en la barra de direcciones superior: `http://localhost:8000` y pulsa Enter.
5.  ¡Listo! Ya deberías estar viendo el panel principal.

---

## 🔍 ¿Cómo funciona por dentro? (Para curiosos)

El proyecto está dividido en varias partes modulares, por si quieres curiosear en el código:

*   **`app/data/fetcher.py`**: El recolector de datos. Se conecta a internet para ver a cuánto está el Bitcoin en el mercado.
*   **`app/model/predictor.py`**: El cerebro de IA. Toma el historial de precios y usa algoritmos matemáticos para intentar adivinar el futuro.
*   **`app/decision/engine.py`**: El tomador de decisiones. Junta la predicción con otros factores simulados para darte el veredicto final.
*   **`app/simulation/trader.py`**: El contable virtual. Guarda tus 1000€, efectúa las compras y ventas ficticias y calcula tus ganancias o pérdidas.
*   **`app/main.py`**: El director de orquesta. Conecta todas las piezas y sirve la página web que ves en el navegador.

---

**¡Disfruta experimentando con el mercado cripto!**

*Nota: Este software es educativo y de simulación. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones avanzadas. El autor no se hace responsable de pérdidas financieras.*
