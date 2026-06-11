@echo off
title Smart Retail System - Start Server
echo ===================================================
echo             Smart Retail System Start
echo ===================================================
echo.

:: Check which python command is available
set PYTHON_CMD=python
py --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
)

echo Using Python command: %PYTHON_CMD%
echo.
echo Installing and verifying dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] Failed to install packages. Ensure Python is installed and added to PATH.
    echo.
)

echo Starting FastAPI Uvicorn Server...
echo API is available at: http://127.0.0.1:8000/
echo Web dashboard is available at: http://127.0.0.1:8000/dashboard
echo.
%PYTHON_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
