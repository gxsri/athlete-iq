# AthleteIQ Startup Script (PowerShell - Better Unicode support)
$ErrorActionPreference = "Continue"

$base = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $base

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "     AthleteIQ System Startup" -ForegroundColor Yellow
Write-Host "     NSCA-CSCS / CPSS" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found. Install Python 3.11+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}
if (-not $nodeCmd) {
    Write-Host "[ERROR] Node.js not found. Install Node.js 18+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}
if (-not $npmCmd) {
    Write-Host "[ERROR] npm not found. Install Node.js 18+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}
Write-Host "[OK] Python $(& $pythonCmd.Source --version 2>&1)" -ForegroundColor Green
Write-Host "[OK] Node $(& $nodeCmd.Source --version)" -ForegroundColor Green
Write-Host "[OK] npm $(& $npmCmd.Source --version)" -ForegroundColor Green
Write-Host ""

# Backend
Write-Host "[1/3] Backend setup..." -ForegroundColor Yellow
Set-Location "$base\backend"
$needInstall = $false
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "  [..] Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    $needInstall = $true
}
# Check if uvicorn actually installed
$uvTest = & "$base\backend\venv\Scripts\python.exe" -c "import uvicorn" 2>&1
if ($LASTEXITCODE -ne 0) {
    $needInstall = $true
}
if ($needInstall) {
    Write-Host "  [..] Installing core Python packages (1-2 min)..." -ForegroundColor Gray
    & "$base\backend\venv\Scripts\python.exe" -m pip install "uvicorn[standard]" fastapi sqlalchemy asyncpg pydantic numpy scipy 2>&1 | Select-Object -Last 5
}
Write-Host "  [OK] Backend ready" -ForegroundColor Green

Set-Location "$base\frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "  [..] Installing packages (2-5 min)..." -ForegroundColor Gray
    & $npmCmd.Source install 2>&1 | Select-Object -Last 5
}
Write-Host "  [OK] Frontend ready" -ForegroundColor Green

# Start services
Set-Location $base
Write-Host ""
Write-Host "[3/3] Starting services..." -ForegroundColor Yellow

# Ensure uvicorn is installed in backend venv
$uvicornCheck = & "$base\backend\venv\Scripts\pip.exe" show uvicorn 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [..] Installing uvicorn..." -ForegroundColor Gray
    & "$base\backend\venv\Scripts\pip.exe" install uvicorn[standard] 2>&1 | Select-Object -Last 3
}

Write-Host "  Starting backend API on :8000 ..." -ForegroundColor Gray
$apiJob = Start-Process -FilePath "$base\backend\venv\Scripts\python.exe" `
    -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" `
    -WorkingDirectory "$base\backend" `
    -WindowStyle Minimized `
    -PassThru

Start-Sleep 5

# Use full path to npm.cmd from Get-Command
$npmExe = $npmCmd.Source
Write-Host "  Starting frontend dev server on :3000 ..." -ForegroundColor Gray
$webJob = Start-Process -FilePath $npmExe `
    -ArgumentList "run","dev" `
    -WorkingDirectory "$base\frontend" `
    -WindowStyle Minimized `
    -PassThru

Start-Sleep 4

# Check if processes actually started
if ($apiJob.HasExited) {
    Write-Host "[WARN] Backend may have failed to start. Check backend console." -ForegroundColor Yellow
}
if ($webJob.HasExited) {
    Write-Host "[WARN] Frontend may have failed to start. Check: npm run dev" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor Green
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running in background." -ForegroundColor Yellow
Write-Host "Press Ctrl+C or close this window to stop." -ForegroundColor Gray
Write-Host ""

Start-Process "http://localhost:3000"

# Keep window open
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Press ENTER to STOP all services" -ForegroundColor Red
Write-Host "============================================" -ForegroundColor Cyan
Read-Host

# Cleanup
if ($apiJob -and -not $apiJob.HasExited) { Stop-Process $apiJob -Force }
if ($webJob -and -not $webJob.HasExited) { Stop-Process $webJob -Force }
Write-Host "Stopped."
