# AI Naat Studio API Documentation

All API endpoints are hosted at `http://127.0.0.1:8000/api`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

---

## 1. Health

### `GET /api/health`
Returns system operational status and application version.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "app": "AI Naat Studio",
  "version": "1.0.0",
  "engine": "active"
}
```

---

## 2. Audio Management

### `POST /api/audio/upload`
Uploads raw audio file (`.wav`, `.mp3`, `.flac`), decodes content, verifies integrity, runs objective diagnostic analysis, and returns metadata.
- **Payload**: `multipart/form-data` with `file` field.
- **Response**: `201 Created`
```json
{
  "audio_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "naat_recording.wav",
  "duration_seconds": 182.4,
  "sample_rate": 44100,
  "channels": 2,
  "file_size_bytes": 32174820,
  "analysis": { ... },
  "message": "Audio uploaded and analyzed successfully"
}
```

### `GET /api/audio/{audio_id}`
Returns audio file record.

### `GET /api/audio/{audio_id}/metadata`
Returns audio metadata.

### `GET /api/audio/{audio_id}/analysis`
Returns full objective analysis report.

### `GET /api/audio/{audio_id}/stream`
Streams the original audio file for in-browser playback with byte-range support.

### `DELETE /api/audio/{audio_id}`
Deletes the uploaded audio file and associated database records.

---

## 3. Enhancement Processing

### `POST /api/processing/{audio_id}`
Triggers an asynchronous enhancement job.
- **Request Body**:
```json
{
  "preset": "natural_naat",
  "automatic_mode": true,
  "overrides": {
    "noise_reduction_strength": 0.35,
    "eq_intensity": 1.0,
    "compression_intensity": 0.5,
    "reverb_amount": 0.08,
    "target_lufs": -16.0,
    "output_format": "wav"
  }
}
```
- **Response**: `202 Accepted`

### `GET /api/jobs/{job_id}`
Returns job status, real progress percentage (0-100), current execution stage, and decision log.

### `GET /api/jobs`
Returns list of recent processing jobs.

### `POST /api/jobs/{job_id}/cancel`
Signals cancellation to the running DSP worker.

---

## 4. Mastered Outputs

### `GET /api/outputs/{output_id}/metadata`
Returns output file metrics and comparative before/after quality report.

### `GET /api/outputs/{output_id}/download`
Downloads the mastered audio file.

### `GET /api/outputs/{output_id}/stream`
Streams the mastered audio file for interactive playback.

### `DELETE /api/outputs/{output_id}`
Deletes the output file from local storage.

---

## 5. Telemetry & Hardware Monitoring

### `GET /api/monitoring/overview`
Returns live system resources (CPU, RAM), engine status, storage usage, and error logs.

### `GET /api/monitoring/engine`
Returns subsystem status (DeepFilterNet, Spectral Gating, FFmpeg).

### `GET /api/monitoring/storage`
Returns byte breakdown of local storage directories.

---

## 6. Workstation Settings

### `GET /api/settings`
Returns current workstation configuration.

### `POST /api/settings`
Updates workstation settings.

### `POST /api/settings/clear-all-data`
Permanently erases all session recordings, output masters, and database rows.
