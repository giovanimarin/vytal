@echo off
cd /d "%~dp0"
start "Vytal Backend" cmd /k python scripts/local.py backend
start "Vytal Web" cmd /k python scripts/local.py web
echo Web: http://localhost:3000 - API: http://localhost:8000/docs
echo First run: python scripts/local.py setup
