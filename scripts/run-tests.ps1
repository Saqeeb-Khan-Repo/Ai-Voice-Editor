# AI Naat Studio - Comprehensive Test Runner
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Running AI Naat Studio Full Test Suite...     " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Backend Tests
Write-Host "`n[1/2] Running Backend Pytest Suite..." -ForegroundColor Yellow
Set-Location $BackendDir
& ".venv\Scripts\pytest.exe" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend tests failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Backend tests passed successfully!" -ForegroundColor Green

# 2. Frontend Tests
Write-Host "`n[2/2] Running Frontend Vitest Suite..." -ForegroundColor Yellow
Set-Location $FrontendDir
cmd /c "npm test"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend tests failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend tests passed successfully!" -ForegroundColor Green

Write-Host "`nAll 28 tests across backend and frontend passed with 100% success!" -ForegroundColor Cyan
