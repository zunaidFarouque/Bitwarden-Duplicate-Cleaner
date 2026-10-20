@echo off
title Bitwarden Duplicate Cleaner
echo =========================================================
echo      Launching Bitwarden Duplicate Cleaner (Local)
echo =========================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH. Please install Python 3.9+.
    pause
    exit /b 1
)

python run.py
pause
