# AI Naat Studio - System Preflight & Health Check
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  AI Naat Studio Health & Dependency Check       " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Check Python
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (Test-Path $PythonExe) {
    $PyVer = & $PythonExe -c "import sys; print(sys.version.split()[0])"
    Write-Host "[OK] Python Virtualenv: v$PyVer" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Python Virtualenv missing at $PythonExe" -ForegroundColor Red
}

# 2. Check FFmpeg
try {
    $FFmpegOut = & ffmpeg -version 2>&1
    $FFmpegVer = ($FFmpegOut[0] -split ' ')[2]
    Write-Host "[OK] FFmpeg Audio Transcoder: v$FFmpegVer" -ForegroundColor Green
} catch {
    Write-Host "[WARN] FFmpeg not found in PATH" -ForegroundColor Yellow
}

# 3. Check Node.js
try {
    $NodeVer = & node --version
    Write-Host "[OK] Node.js Runtime: $NodeVer" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Node.js not found in PATH" -ForegroundColor Red
}

# 4. Check Core Audio DSP Modules
if (Test-Path $PythonExe) {
    & $PythonExe -c "
import soundfile as sf
import librosa
import pyloudnorm as pyln
import scipy
import numpy as np
print('[OK] Core Audio DSP libraries verified (soundfile, librosa, pyloudnorm, scipy, numpy)')
"
}

# 5. Check DeepFilterNet Adapter Status
if (Test-Path $PythonExe) {
    Set-Location $BackendDir
    & $PythonExe -c "
from app.audio_engine.stages.noise_reduction import DeepFilterNetAdapter, SpectralGatingAdapter
df = DeepFilterNetAdapter()
df_ok, df_reason = df.is_available()
sg = SpectralGatingAdapter()
sg_ok, sg_reason = sg.is_available()
print(f'[*] Neural DeepFilterNet: {df_ok} ({df_reason})')
print(f'[*] Spectral Gating Engine: {sg_ok} ({sg_reason})')
"
}

Write-Host "`nPreflight check completed." -ForegroundColor Cyan
