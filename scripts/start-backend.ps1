# AI Naat Studio - Backend Startup Script
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Naat Studio Backend Server...     " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Set-Location $BackendDir

$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment not found! Please run setup first." -ForegroundColor Red
    exit 1
}

Write-Host "Host: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the backend server." -ForegroundColor Yellow

& $PythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
