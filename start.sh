#!/usr/bin/env bash
set -e

echo "========================================================="
echo "     Bitwarden Duplicate Cleaner - 1-Click Launcher"
echo "========================================================="
echo ""

if command -v python3 &> /dev/null; then
    PYCMD=python3
elif command -v python &> /dev/null; then
    PYCMD=python
else
    echo "[ERROR] Python is not installed or not found in your PATH."
    echo "Please install Python 3.9+ from https://www.python.org/downloads/ or via your package manager."
    exit 1
fi

# 1. Create virtual environment if it does not exist
if [ ! -f ".venv/bin/activate" ]; then
    echo "[*] Creating isolated virtual environment in .venv..."
    $PYCMD -m venv .venv
    echo "[+] Virtual environment created."
    echo "[*] Installing dependencies inside .venv..."
    source .venv/bin/activate
    python -m pip install --upgrade pip >/dev/null 2>&1 || true
    python -m pip install -r backend/requirements.txt
    echo "[+] Dependencies installed successfully."
else
    source .venv/bin/activate
fi

# 2. Run cleaner within the virtual environment
python run.py
