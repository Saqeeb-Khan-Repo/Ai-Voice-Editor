# Windows Installation & Setup Guide

This guide describes how to run AI Naat Studio on a Windows 11 workstation.

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **RAM**: Minimum 8 GB (16 GB or 32 GB recommended).
- **CPU**: Modern multi-core Intel Core i5/i7/i9 or AMD Ryzen 5/7/9.
- **GPU**: Optional. The engine runs on CPU by default.
- **Free Disk Space**: Approximately 1.5 GB for dependencies, models, and audio storage.

---

## Step 1: Install Required Runtimes

1. **Python 3.11**:
   Verify Python is installed:
   ```powershell
   python --version
   ```
2. **Node.js 18 or newer**:
   Verify Node.js is installed:
   ```powershell
   node --version
   ```
3. **FFmpeg**:
   Verify FFmpeg is installed and accessible in your system PATH:
   ```powershell
   ffmpeg -version
   ```

---

## Step 2: Environment Setup

Clone or place the project repository in your desired directory:
```powershell
cd "C:\Users\Saqeeb Khan\.gemini\antigravity\scratch\ai-naat-studio"
```

### Backend Virtual Environment
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Dependencies
```powershell
cd ..\frontend
npm install
```

---

## Step 3: Run Preflight Health Check

Run the automated diagnostic check:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\health-check.ps1
```

---

## Step 4: Launching the Studio

Run the two services in separate PowerShell windows:

**Window 1 (Backend API):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```
Available at: `http://127.0.0.1:8000`

**Window 2 (Web Workstation UI):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```
Available at: `http://localhost:3000`

Open your web browser and navigate to `http://localhost:3000`.
