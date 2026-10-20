@echo off
title Bitwarden Duplicate Cleaner
echo =========================================================
echo      Bitwarden Duplicate Cleaner - 1-Click Launcher
echo =========================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed or not found in your PATH.
        echo.
        echo Please download and install Python (3.9 or higher):
        echo   https://www.python.org/downloads/
        echo.
        echo IMPORTANT: During Python installation on Windows, check the box:
        echo   [x] "Add python.exe to PATH"
        echo.
        pause
        exit /b 1
    ) else (
        set PYCMD=py
    )
) else (
    set PYCMD=python
)

REM 1. Create virtual environment if it does not exist
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Creating isolated virtual environment in .venv...
    %PYCMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created.
    echo [*] Installing dependencies inside .venv...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install -r backend\requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies into .venv.
        pause
        exit /b 1
    )
    echo [+] Dependencies installed successfully.
) else (
    call .venv\Scripts\activate.bat
)

REM 2. Run cleaner within the virtual environment
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Server exited with an error.
    pause
)
