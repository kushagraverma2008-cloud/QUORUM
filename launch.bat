@echo off
setlocal enabledelayedexpansion
title QUORUM // Autonomous War Room - AI Startup Evaluation Engine
color 0B
cls

echo ===============================================================================
echo                QUORUM // WAR ROOM - AI EXPERT COUNCIL PLATFORM
echo ===============================================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=src

:: 1. Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required but not found in your system PATH.
    echo Please install Python from https://www.python.org/downloads/ and ensure
    echo 'Add Python to PATH' is checked during setup.
    pause
    exit /b 1
)

:: 2. Manage Virtual Environment (.venv)
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

:: 3. Fast Dependency Check using Hash Stamp
set "NEEDS_INSTALL=0"
if not exist ".venv\requirements.stamp" (
    set "NEEDS_INSTALL=1"
) else (
    certutil -hashfile requirements.txt SHA256 > "%temp%\req_hash.tmp" 2>nul
    for /f "skip=1 tokens=*" %%A in ('type "%temp%\req_hash.tmp"') do (
        if not defined CURR_HASH set "CURR_HASH=%%A"
    )
    del "%temp%\req_hash.tmp" 2>nul
    set /p SAVED_HASH=<".venv\requirements.stamp"
    if not "!CURR_HASH!"=="!SAVED_HASH!" set "NEEDS_INSTALL=1"
)

if "!NEEDS_INSTALL!"=="1" (
    echo [INFO] Installing / updating dependencies from requirements.txt...
    python -m pip install -q -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed. Please verify requirements.txt.
        pause
        exit /b 1
    )
    certutil -hashfile requirements.txt SHA256 > "%temp%\req_hash.tmp" 2>nul
    for /f "skip=1 tokens=*" %%A in ('type "%temp%\req_hash.tmp"') do (
        if not defined FINAL_HASH (
            set "FINAL_HASH=%%A"
            echo !FINAL_HASH! > ".venv\requirements.stamp"
        )
    )
    del "%temp%\req_hash.tmp" 2>nul
    echo [INFO] Dependencies are up to date.
) else (
    echo [INFO] Dependencies verified (up to date).
)

:: 4. Environment File Setup
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

:: 5. Determine Dev Mode / Reload Flag
set "RELOAD_FLAG="
if /i "%1"=="dev" (
    set "RELOAD_FLAG=--reload"
    echo [MODE] Development mode active (auto-reload enabled).
) else (
    echo [MODE] Production mode active (run 'launch.bat dev' for auto-reload).
)

echo.
echo -------------------------------------------------------------------------------
echo  * Quorum UI:    http://127.0.0.1:8000
echo  * API Docs:     http://127.0.0.1:8000/docs
echo  * Loaded Base:  709 Expert Personas, 8-Pillar Adversarial Deliberation
echo -------------------------------------------------------------------------------
echo.

echo Launching browser and starting server...
start http://127.0.0.1:8000

python -m uvicorn quorum.api.main:app --host 127.0.0.1 --port 8000 %RELOAD_FLAG%
if errorlevel 1 (
    echo.
    echo [ERROR] Quorum server terminated unexpectedly with code %errorlevel%.
    pause
)
