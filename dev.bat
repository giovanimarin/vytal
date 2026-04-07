@echo off
echo Subindo Vytal Dev Environment...

:: Backend (FastAPI)
start "Vytal Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

:: Aguarda 2 segundos para o backend inicializar antes de subir o mobile
timeout /t 2 /nobreak > nul

:: Mobile (Expo)
start "Vytal Mobile" cmd /k "cd /d %~dp0mobile\vytal-app && npx expo start"

echo.
echo Serviços iniciados em janelas separadas:
echo   Backend  → http://localhost:8001
echo   Mobile   → Expo DevTools (escanear QR no celular)
echo.
