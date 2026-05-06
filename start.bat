@echo off
chcp 936 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo      AthleteIQ System Startup
echo ============================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found

REM --- Check Node ---
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM --- Backend venv ---
echo [1/3] Setting up backend...
cd "%~dp0backend"
if not exist "venv\Scripts\python.exe" (
    echo [..] Creating venv and installing packages...
    python -m venv venv
    call venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python packages
        pause
        exit /b 1
    )
)

REM --- Frontend modules ---
cd "%~dp0frontend"
if not exist "node_modules" (
    echo [..] Installing Node packages, please wait...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node packages
        pause
        exit /b 1
    )
)

cd "%~dp0"

echo.
echo [2/3] Starting backend API on http://localhost:8000 ...
start "AthleteIQ Backend" /D "%~dp0backend" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [3/3] Starting frontend on http://localhost:3000 ...
ping -n 5 127.0.0.1 >nul
start "AthleteIQ Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

ping -n 6 127.0.0.1 >nul
start "" http://localhost:3000

echo.
echo ============================================
echo   Open http://localhost:3000
echo   API Docs http://localhost:8000/docs
echo ============================================
echo.
echo Waiting for services to start...
echo Close the backend and frontend windows to stop.
echo.
pause
