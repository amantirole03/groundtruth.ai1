@echo off
title GroundTruth.ai - Backend Server (Port 8000)
echo ========================================================
echo Starting GroundTruth.ai FastAPI Backend on http://127.0.0.1:8000
echo ========================================================
cd /d "%~dp0backend"
set PYTHONPATH=%~dp0backend;%PYTHONPATH%
"%~dp0backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
