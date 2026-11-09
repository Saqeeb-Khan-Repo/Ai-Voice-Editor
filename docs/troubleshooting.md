# Troubleshooting & Diagnostic Guide

### 1. File Upload Fails with "Unsupported format"
- **Cause**: The audio file format is not `.wav`, `.mp3`, or `.flac`.
- **Solution**: Convert your audio to uncompressed WAV or standard MP3 before uploading.

### 2. Audio Validation Flags Clipping Warning
- **Cause**: The original microphone recording was digitally clipped during recording (gain too high).
- **Solution**: The 12-stage pipeline automatically engages the lookahead true-peak limiter to prevent inter-sample distortion in the final master.

### 3. DeepFilterNet Status Shows "DSP Fallback Active"
- **Cause**: DeepFilterNet requires Rust/Cargo compilation on Windows if prebuilt binary wheels are not present for your specific environment.
- **Solution**: AI Naat Studio automatically falls back to its pure SciPy/NumPy Spectral Gating Engine, which operates with high fidelity and zero phase distortion.

### 4. Port 8000 or 3000 Already in Use
- **Cause**: Another local service is using port 8000 (backend) or 3000 (frontend).
- **Solution**: Stop the conflicting process or change the port in `backend/app/core/config.py` and `frontend/package.json`.
