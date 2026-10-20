#!/usr/bin/env bash
set -e

# Change directory to the repository folder
cd "$(dirname "$0")"

echo "========================================================="
echo "     Bitwarden Duplicate Cleaner - 1-Click Launcher"
echo "========================================================="
echo ""

# Find working Python
PYCMD=""
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" &> /dev/null; then
    PYCMD="python3"
elif python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" &> /dev/null; then
    PYCMD="python"
else
    echo "[ERROR] Python 3.9+ was not found on your system."
    echo "Please install Python from https://www.python.org/downloads/ or via your package manager."
    exit 1
fi

echo "[+] Python detected: $PYCMD"

# Create .venv if it doesn't exist
if [ ! -f ".venv/bin/python" ]; then
    echo "[*] Setting up isolated Python virtual environment (.venv)..."
    $PYCMD -m venv .venv
    echo "[+] Virtual environment created."
    echo "[*] Installing required packages into .venv (one-time setup)..."
    .venv/bin/python -m pip install --upgrade pip >/dev/null 2>&1 || true
    .venv/bin/python -m pip install -r backend/requirements.txt
    echo "[+] All dependencies installed successfully!"
    echo ""
fi

# Run using .venv python directly
echo "[*] Starting Bitwarden Duplicate Cleaner..."
.venv/bin/python run.py
