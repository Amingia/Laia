# 🚀 IA Bitcoin Predictor & Auto-Trader Pro

¡Bienvenido! Este programa es una herramienta completa impulsada por Inteligencia Artificial que analiza el mercado de Bitcoin en tiempo real, realiza predicciones a futuro y simula estrategias de trading automáticas de forma **altamente realista**.

No necesitas ser un experto en programación o en criptomonedas para hacerlo funcionar. Sigue los pasos a continuación.

---

## 🌟 ¿Qué incluye la versión PRO? (Nuevas Características)

Hemos mejorado significativamente la inteligencia y el realismo del simulador:

*   **🧠 IA más Inteligente:** Ahora el modelo de predicción tiene en cuenta no solo el precio, sino también la **volatilidad, la tendencia a corto plazo (momentum)** y un volumen de mercado correlacionado.
*   **⚖️ Auto-Corrección Dinámica:** Si la IA detecta que se está equivocando por mucho, se auto-corrige de manera agresiva. Si acierta constantemente, estabiliza sus márgenes.
*   **🛑 Adiós al Sobre-Operar (Ruido):** El motor de decisiones ahora requiere **múltiples confirmaciones** para emitir una señal. Además, no recomendará comprar o vender a menos que prevea una ganancia neta superior al 1%.
*   **💸 Simulador Realista:** Las operaciones en el simulador ahora incluyen una **comisión del 0.1%** (similar a Binance) por cada compra/venta, y se ha implementado un sistema de **"enfriamiento" de 3 minutos** tras cada operación para evitar un comportamiento errático.
*   **📊 Dashboard Transparente:** La interfaz ahora te muestra en tiempo real la **Precisión de la IA** (cuántas veces adivina la dirección del mercado) y resalta visualmente en verde o rojo si tu simulador está ganando o perdiendo dinero.

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

*   **`app/data/fetcher.py`**: El recolector de datos y creador de características (calcula volatilidad y momentum).
*   **`app/model/predictor.py`**: El cerebro de IA con Random Forest y el mecanismo de auto-corrección adaptativa.
*   **`app/decision/engine.py`**: El tomador de decisiones exigente y anti-ruido.
*   **`app/simulation/trader.py`**: El contable virtual. Guarda tus 1000€, cobra comisiones realistas y fuerza tiempos de espera.
*   **`app/main.py`**: El director de orquesta que sirve todo vía API.

---

**¡Disfruta experimentando con el mercado cripto!**

*Nota: Este software es educativo y de simulación. NO DEBE utilizarse para operar dinero real sin supervisión ni adaptaciones avanzadas. El autor no se hace responsable de pérdidas financieras.*
