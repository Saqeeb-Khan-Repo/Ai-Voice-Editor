# AI Naat Studio (Professional Local-First Vocal Enhancement)

AI Naat Studio is a production-grade, local-first web application specifically engineered for automatic audio enhancement of **Naat**, **Islamic vocal recitations**, and **nasheed** recordings.

It preserves the natural human voice timbre, sacred Arabic/Urdu diction, subtle breathing, and vocal character while transparently removing noise, clearing acoustic room mud, stabilizing dynamic consistency, adding spiritual acoustic space, and mastering to broadcast loudness compliance (EBU R128).

---

## 🌟 Key Capabilities

1. **Acoustic Diagnostic Analysis**: Measures sample rate, channel layout, RMS, peak amplitude (dBFS), integrated loudness (LUFS), true peak (dBTP with 4x polyphase oversampling), crest factor, sibilance energy, clipping overs, and silence regions.
2. **7-Band Spectral Energy Distribution**: Analyzes Sub-bass (<60Hz), Bass (60-250Hz), Low-mids (250-500Hz), Mids (500-2kHz), High-mids (2k-5kHz), Presence (5k-10kHz), and Air (>10kHz).
3. **Intelligent Enhancement Decision Engine**: Never uses arbitrary static settings; automatically assesses whether noise reduction, high-pass filtering, mud notches, de-essing, or compression are justified based on objective acoustic data.
4. **12-Stage Non-Destructive DSP Pipeline**:
   - Stage 1: Audio decoding & integrity check (WAV, MP3, FLAC)
   - Stage 2: Initial diagnostic analysis
   - Stage 3: Spectral gating noise reduction (pure DSP, zero watery chirps) & optional DeepFilterNet adapter
   - Stage 4: 2nd-order high-pass filter (plosive & rumble attenuation)
   - Stage 5: RBJ parametric biquad equalizer (boxiness cut, diction presence, vocal air shelf)
   - Stage 6: Feed-forward soft-knee vocal compressor
   - Stage 7: Dynamic sidechain de-esser
   - Stage 8: Algorithmic Moorer/Schroeder natural room reverberator with pre-delay
   - Stage 9: ITU-R BS.1770 / EBU R128 loudness normalization
   - Stage 10: 4x oversampled lookahead true-peak brickwall limiter (≤ -1.0 dBTP ceiling)
   - Stage 11: Post-processing audio quality verification & safety check
   - Stage 12: Studio master export (24-bit WAV, MP3 320k, FLAC)
5. **Synchronized A/B Auditioning**: Dual interactive WaveSurfer.js waveform players with synchronized playhead seek, volume/mute controls, and quality metrics delta comparison.
6. **100% Local & Privacy-Preserving**: Runs completely on `127.0.0.1`. No external APIs, no remote uploads, no telemetry. Includes a single-click "Clear All Session Data" privacy purge.

---

## 🏗️ Architecture

```
ai-naat-studio/
├── backend/                  # Python 3.11+ FastAPI Service
│   ├── app/
│   │   ├── api/              # REST Endpoints (health, audio, processing, outputs, monitoring, settings)
│   │   ├── audio_engine/     # 12-Stage Audio DSP & Decision Engines
│   │   ├── database/         # SQLite + SQLAlchemy Declarative Models
│   │   ├── models/           # AudioFile, ProcessingJob, AudioOutput
│   │   ├── schemas/          # Pydantic v2 Request & Response Contracts
│   │   ├── workers/          # ThreadPoolExecutor Asynchronous Job Runner
│   │   └── monitoring/       # System Resource & Hardware Telemetry
│   ├── tests/                # 25 Comprehensive Pytest Unit & Integration Tests
│   └── requirements.txt
│
├── frontend/                 # Next.js 14 App Router Workstation
│   ├── src/
│   │   ├── app/              # Layout, Global DAW Styles, Main Workstation Page
│   │   ├── components/       # WaveSurfer.js Audio Player Component
│   │   ├── features/         # Studio, Analysis, Presets, A/B Comparison, History, Monitoring, Settings
│   │   ├── services/         # Typed REST API Client
│   │   └── types/            # TypeScript Domain Interfaces
│   ├── tests/                # Vitest Frontend Tests
│   └── package.json
│
├── storage/                  # Local-First Safe Storage
│   ├── originals/            # Sanitized Raw Input Files
│   ├── processed/            # Mastered Enhanced Audio Outputs
│   └── temporary/            # Resampling & Conversion Caches
│
├── docs/                     # Full Engineering Specifications
├── scripts/                  # Convenient Windows Launchers & Health Checks
```

---

## 🚀 Quick Launch (Windows 11)

### Prerequisites
- Python 3.11 or newer
- Node.js 18+ (verified with v24.16.0)
- FFmpeg (verified with v9.0)

### 1. Preflight Health Check
Run the preflight health script to verify your local dependencies:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\health-check.ps1
```

### 2. Start the Backend API Server
In a PowerShell window:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```
Backend will start on: **`http://127.0.0.1:8000`**  
Interactive API Docs (Swagger): **`http://127.0.0.1:8000/docs`**

### 3. Start the Web Workstation Frontend
In a second PowerShell window:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```
Open your browser to: **`http://localhost:3000`**

---

## 🧪 Automated Testing

Run the combined automated test suite (backend pytest + frontend vitest):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

**Results:**
- Backend: **25 / 25 Passed** (synthetic signals, DSP stages, decision engine, REST API, job lifecycle)
- Frontend: **3 / 3 Passed** (component mounting, acoustic metrics, preset controls)
- Production Build: **Compiled & Static Page Generation Succeeded**

---

## 🔒 Security & Privacy

- **Local Host Isolation**: Backend binds strictly to `127.0.0.1:8000`.
- **CORS Restriction**: Explicitly restricted to `localhost:3000` and `127.0.0.1:3000`.
- **Untrusted File Sanitization**: Filenames are sanitized, MIME headers and magic bytes are verified via `soundfile`, and paths are stored relatively to prevent directory traversal attacks.
- **Data Deletion**: Complete session purge available anytime via the Settings UI or `POST /api/settings/clear-all-data`.

---

## 📄 License & Compliance

- Built with permissive open-source components: MIT (FastAPI, Next.js, React, Tailwind CSS, WaveSurfer.js, Pydantic), BSD-3-Clause (NumPy, SciPy, soundfile), and ISC.
- **No GPL-3.0 dependencies**: Spotify Pedalboard is intentionally excluded to ensure distribution safety.
