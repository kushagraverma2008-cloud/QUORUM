#!/usr/bin/env bash
# QUORUM - Linux & macOS Launch Script
set -e

echo "=================================================="
echo "    QUORUM: Adversarial Founder Pre-Mortem Council"
echo "=================================================="

# Check Python 3 availability
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3.10+ is required but was not found."
    exit 1
fi

# Ensure Python version is >= 3.10
PY_VER=$($PY_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[INFO] Using Python $PY_VER ($PY_CMD)"

# Virtual environment setup
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment in $VENV_DIR..."
    $PY_CMD -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Dependency hash check
STAMP_FILE="$VENV_DIR/.requirements_stamp"
REQ_FILE="requirements.txt"
CURRENT_HASH=$(shasum "$REQ_FILE" 2>/dev/null | awk '{print $1}' || md5sum "$REQ_FILE" 2>/dev/null | awk '{print $1}' || echo "force")

if [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE")" != "$CURRENT_HASH" ]; then
    echo "[INFO] Installing / updating production dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    echo "$CURRENT_HASH" > "$STAMP_FILE"
    echo "[INFO] Dependencies up to date."
fi

# Set PYTHONPATH
export PYTHONPATH="src:$PYTHONPATH"

# Mode configuration
DEV_MODE=false
for arg in "$@"; do
    if [ "$arg" == "dev" ]; then
        DEV_MODE=true
    fi
done

# Check GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs -0) 2>/dev/null || true
    fi
fi

if [ -n "$GEMINI_API_KEY" ]; then
    echo "[MODE] GEMINI_API_KEY detected. Starting in LIVE AI mode."
else
    echo "[MODE] No GEMINI_API_KEY detected. Starting in HONEST OFFLINE mode."
fi

# Open browser helper
open_browser() {
    sleep 1.2
    URL="http://localhost:8000"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 || true
    fi
}

open_browser &

echo "[INFO] Starting QUORUM web service on http://localhost:8000 ..."
if [ "$DEV_MODE" = true ]; then
    exec uvicorn quorum.api.main:app --host 127.0.0.1 --port 8000 --reload
else
    exec uvicorn quorum.api.main:app --host 127.0.0.1 --port 8000
fi

