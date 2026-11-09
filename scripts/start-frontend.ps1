# AI Naat Studio - Frontend Startup Script
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Naat Studio Web Workstation...    " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Set-Location $FrontendDir

Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the web workstation." -ForegroundColor Yellow

cmd /c "npm run dev"
