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

%PYCMD% run.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Server exited with an error.
    pause
)
