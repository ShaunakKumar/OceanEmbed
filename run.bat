@echo off
REM ================================================================
REM  OceanEmbed — Quick-Start Script (Windows)
REM  Run this from the OceanEmbed root directory.
REM ================================================================

echo.
echo  ============================================
echo   OceanEmbed - Ocean Temperature Forecasting
echo   Prototype Application v1.0
echo  ============================================
echo.

REM 1. Install Python dependencies
echo [1/2] Installing Python dependencies...
pip install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies. Make sure Python and pip are available.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting OceanEmbed server on http://localhost:8000 ...
echo        Press Ctrl+C to stop.
echo.

REM 2. Launch uvicorn
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
