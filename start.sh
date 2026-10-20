#!/usr/bin/env bash
echo "========================================================="
echo "     Launching Bitwarden Duplicate Cleaner (Local)"
echo "========================================================="
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not found in your PATH."
    exit 1
fi

python3 run.py
