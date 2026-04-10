@echo off
echo Subindo Vytal Dev Environment...

:: Backend (FastAPI)
start "Vytal Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"

:: Aguarda 3 segundos para o backend inicializar
timeout /t 3 /nobreak > nul

:: Seed de dados de teste
start "Vytal Seed" cmd /k "cd /d %~dp0backend && .venv\Scripts\python scripts/seed_test_data.py && echo. && echo Seed concluido! Pode fechar esta janela. && pause"

:: Aguarda 2 segundos
timeout /t 2 /nobreak > nul

:: Web (Expo)
start "Vytal Web" cmd /k "cd /d %~dp0mobile\vytal-app && npx expo start --web --port 8083"

echo.
echo Servicos iniciados:
echo   Backend  → http://localhost:8002
echo   Web App  → http://localhost:8083
echo.
echo Aguarde o Expo carregar e acesse http://localhost:8083
echo.
