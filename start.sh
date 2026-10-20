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

$PYCMD run.py
