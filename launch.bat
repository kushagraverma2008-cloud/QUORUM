@echo off
title QUORUM // Autonomous War Room - AI Startup Evaluation Engine
color 0B
cls

echo ===============================================================================
echo                QUORUM // WAR ROOM - AI EXPERT COUNCIL PLATFORM
echo ===============================================================================
echo.
echo [1/3] Initializing environment and verifying dependencies...
cd /d "%~dp0"

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

echo [2/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ and re-run this script.
    pause
    exit /b 1
)

echo [3/3] Launching FastAPI backend server with Obsidian War Room UI...
echo.
echo -------------------------------------------------------------------------------
echo  * Quorum UI:    http://localhost:8000
echo  * API Swagger:  http://localhost:8000/docs
echo  * Loaded Base:  520+ Expert Personas, 8-Pillar Scoring, 3D Network Graph
echo -------------------------------------------------------------------------------
echo.
echo Launching your default browser in 2 seconds...
start "" timeout /t 2 /nobreak >nul & start http://localhost:8000

python -m uvicorn quorum.api.main:app --host 0.0.0.0 --port 8000 --app-dir src --reload

pause
