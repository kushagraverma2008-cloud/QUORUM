@echo off
title QUORUM // Autonomous War Room - AI Startup Evaluation Engine
color 0B
cls

echo ===============================================================================
echo                QUORUM // WAR ROOM - AI EXPERT COUNCIL PLATFORM
echo ===============================================================================
echo.
echo [1/4] Initializing environment and paths...
cd /d "%~dp0"
set PYTHONPATH=src

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

echo [2/4] Checking Python runtime...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ and re-run this script.
    pause
    exit /b 1
)

echo [3/4] Readying Quorum AI Engine...
echo.
echo -------------------------------------------------------------------------------
echo  * Quorum UI:    http://localhost:8000
echo  * API Docs:     http://localhost:8000/docs
echo  * Loaded Base:  709 Expert Personas, 36 Distilled Vectors, 8-Pillar Scoring
echo -------------------------------------------------------------------------------
echo.
echo [4/4] Launching browser and starting FastAPI / Uvicorn server...
start http://localhost:8000

python -m uvicorn quorum.api.main:app --host 127.0.0.1 --port 8000 --reload

pause
