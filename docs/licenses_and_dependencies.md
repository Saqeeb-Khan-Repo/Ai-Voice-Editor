# Dependency & License Inventory

AI Naat Studio utilizes strictly permissive open-source dependencies (MIT, BSD-3-Clause, Apache-2.0). Spotify Pedalboard is intentionally excluded due to its copyleft GPL-3.0 license requirements.

## Backend Dependencies

| Package | Version | License | Purpose |
|---|---|---|---|
| `fastapi` | 0.162+ | MIT | REST API Server |
| `uvicorn` | 0.54+ | BSD-3-Clause | ASGI Server |
| `pydantic` | 2.14+ | MIT | Data Validation & Schemas |
| `sqlalchemy` | 2.1+ | MIT | Database ORM |
| `numpy` | 1.26+ | BSD-3-Clause | Array & Numerical Operations |
| `scipy` | 1.17+ | BSD-3-Clause | Digital Signal Processing & Filters |
| `soundfile` | 0.14+ | BSD-3-Clause | Audio File I/O |
| `librosa` | 0.11+ | ISC | Audio Feature Extraction |
| `pyloudnorm` | 0.2+ | MIT | ITU-R BS.1770-4 Loudness Meter |
| `psutil` | 7.2+ | BSD-3-Clause | System Hardware Telemetry |
| `pytest` | 9.2+ | MIT | Automated Testing Suite |

## Frontend Dependencies

| Package | Version | License | Purpose |
|---|---|---|---|
| `next` | 14.2+ | MIT | React Web Framework |
| `react` | 18.3+ | MIT | UI Library |
| `react-dom` | 18.3+ | MIT | React DOM Renderer |
| `wavesurfer.js` | 7.8+ | BSD-3-Clause | Interactive Audio Waveforms |
| `lucide-react` | 0.454+ | ISC | Workstation Icon Set |
| `tailwindcss` | 3.4+ | MIT | Utility CSS Framework |
| `vitest` | 2.1+ | MIT | Frontend Testing Framework |
