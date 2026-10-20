@echo off
setlocal
cd /d "%~dp0"
title Bitwarden Duplicate Cleaner

echo =========================================================
echo      Bitwarden Duplicate Cleaner - 1-Click Launcher
echo =========================================================
echo.

REM 1. Find a working Python executable (check 'python', then 'py')
set "PYCMD="

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=python"
    goto :PYTHON_FOUND
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py -3"
    goto :PYTHON_FOUND
)

py -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    goto :PYTHON_FOUND
)

echo [ERROR] Python 3.9+ was not found on your system!
echo.
echo Please install Python 3:
echo   1. Download installer from: https://www.python.org/downloads/
echo   2. Run installer and MAKE SURE to check the box:
echo      [x] "Add python.exe to PATH"
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [+] Python detected: %PYCMD%

REM 2. Create virtual environment if .venv does not exist
if exist ".venv\Scripts\python.exe" goto :VENV_READY

echo [*] Setting up isolated Python virtual environment (.venv)...
%PYCMD% -m venv .venv
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create virtual environment with %PYCMD%.
    echo Please ensure the Python 'venv' module is available.
    echo.
    pause
    exit /b 1
)

echo [+] Virtual environment created.
echo [*] Installing required packages into .venv (one-time setup)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies into .venv.
    echo Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo [+] All dependencies installed successfully!
echo.

:VENV_READY
REM 3. Run the application using the virtual environment's python directly
echo [*] Starting Bitwarden Duplicate Cleaner...
".venv\Scripts\python.exe" run.py

echo.
echo =========================================================
echo Application has stopped.
echo =========================================================
pause
