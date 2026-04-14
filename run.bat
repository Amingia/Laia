@echo off
cd /d %~dp0
echo ===================================================
echo     Iniciando BTC Predictive Analytics v16...
echo ===================================================
echo.

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual no existe. Por favor ejecuta install.bat primero.
    pause
    goto :eof
)

call venv\Scripts\activate.bat

echo Arrancando el motor analitico local...
echo El servidor estara disponible en http://localhost:8000
echo La primera carga tardara unos segundos mientras se analiza el mercado.
echo Manten esta ventana abierta. Presiona Ctrl+C para cerrar.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
