@echo off
title GroundTruth.ai Launcher
echo ========================================================
echo Launching GroundTruth.ai (Backend + Frontend)
echo ========================================================
start "" "%~dp0start_backend.bat"
timeout /t 2 >nul
start "" "%~dp0start_frontend.bat"
timeout /t 3 >nul
start http://localhost:5173
echo Launched! Opening browser at http://localhost:5173 ...
