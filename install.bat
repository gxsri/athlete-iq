@echo off
title AthleteIQ - Install

echo ============================================
echo   AthleteIQ - Install All Dependencies
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Installing Python dependencies...
cd backend
if exist "venv\" rmdir /s /q venv
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
echo [OK] Python packages installed
echo.

echo [2/2] Installing Node dependencies...
cd ..\frontend
if exist "node_modules\" rmdir /s /q node_modules
call npm install
echo [OK] Node packages installed
echo.

echo ============================================
echo   Installation complete!
echo   Now run: start.bat
echo ============================================
pause
