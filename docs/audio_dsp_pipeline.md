# Audio DSP Pipeline & Signal Processing Specification

The enhancement pipeline in AI Naat Studio is composed of 12 distinct, testable, and non-destructive stages specifically calibrated for vocal recitation, Naat, and Islamic vocals.

---

## The 12 Stages

### Stage 1: Input Validation and Decoding
- Decodes raw input audio via `soundfile` or `ffmpeg`.
- Validates sample depth, channels, and duration (minimum 0.2s).
- Converts audio into standardized IEEE 32-bit floating point format with amplitude range $[-1.0, 1.0]$.

### Stage 2: Audio Analysis Engine
- Evaluates the input signal using Short-Time Fourier Transform (STFT) and Welch's Power Spectral Density:
  - **Peak Amplitude (dBFS)**: $20 \log_{10}(\max |x|)$
  - **RMS Level (dBFS)**: $20 \log_{10}\left(\sqrt{\frac{1}{N}\sum x^2}\right)$
  - **Crest Factor (dB)**: $\text{Peak}_{\text{dBFS}} - \text{RMS}_{\text{dBFS}}$
  - **Integrated Loudness (LUFS)**: ITU-R BS.1770-4 K-weighting gating via `pyloudnorm`.
  - **True Peak (dBTP)**: 4x polyphase oversampling interpolation via `scipy.signal.resample_poly` to detect inter-sample overshoots.
  - **Silence & Noise Estimation**: 50ms frame energy evaluation, separating verified quiet pause regions (`measured`) from lowest 10% percentile energy frames (`estimated`).
  - **7-Band Energy Distribution**: Sub-bass (<60Hz), Bass (60-250Hz), Low-mids (250-500Hz), Mids (500-2kHz), High-mids (2k-5kHz), Presence (5k-10kHz), and Air (>10kHz).

### Stage 3: Noise Reduction (Interchangeable Adapter)
- **DeepFilterNet Neural Adapter**: Safe wrapper around optional DeepFilterNet neural models.
- **Spectral Gating Engine (Pure SciPy/NumPy)**: High-performance STFT spectral subtraction utilizing Hann windowing (2048-point FFT, 75% overlap).
- Constructs an adaptive time-frequency gain mask with soft-knee interpolation:
  $$G(f, t) = \max\left(1 - \frac{\alpha}{\text{SNR}(f, t) + 1}, \beta\right)$$
- Gain smoothing across time bins eliminates "musical noise" and watery fluttering artifacts.

### Stage 4: High-Pass Filtering
- 2nd-order Butterworth high-pass filter with cutoff at 60 Hz (Natural Naat) or 80 Hz (if sub-bass rumble is diagnosed).
- Eliminates microphone handling noise, wind rumble, and subsonic plosives without affecting warm vocal fundamentals.

### Stage 5: Parametric Equalization
- Implements Robert Bristow-Johnson Audio EQ Cookbook biquad filters:
  - **Low-Mid Peaking Filter** (300-320 Hz, $Q=1.2$): Gently removes room resonance and boxiness.
  - **Presence Peaking Filter** (3.2 kHz, $Q=1.0$): Enhances diction intelligibility for sacred Arabic and Urdu consonants.
  - **High Air Shelving Filter** (10 kHz, $Q=0.707$): Gently lifts vocal breath and natural openness.

### Stage 6: Dynamic Vocal Compression
- Feed-forward soft-knee compressor with automatic makeup gain.
- Attack: 20-30 ms (preserves initial consonant transients and natural articulation).
- Release: 150-220 ms (smooth recovery without pumping).
- Ratio adaptively chosen based on input crest factor.

### Stage 7: De-Essing
- Sidechain Butterworth bandpass filter centered at 6.5 kHz.
- Detects sharp sibilant bursts on consonants ("seen", "sheen", "tay") and applies dynamic attenuation only to the offending frequency band.

### Stage 8: Natural Reverb (Spiritual Acoustic Space)
- Algorithmic Schroeder/Moorer reverberation architecture:
  - **Pre-delay (20-35ms)**: Separates direct dry vocal from reverberant reflections to ensure lyrics remain crisp and intimate.
  - **Feedback Comb Filters**: 4 parallel comb filters with coprime sample delays and high-frequency damping.
  - **All-pass Filters**: 2 series diffusion stages for smooth, non-metallic decay.
  - **Calibrated Presets**: 8% wet for Natural Naat, 15% wet for Studio Naat, 22% wet for Spacious Naat.

### Stage 9: Loudness Normalization
- Measures integrated loudness using ITU-R BS.1770.
- Applies linear gain scaling to match target broadcast loudness (default: -16.0 LUFS for podcasts and recitation, -15.0 LUFS for studio releases).

### Stage 10: True-Peak Brickwall Limiter
- 5ms lookahead buffer with 4x polyphase oversampling.
- Smooth release envelope prevents inter-sample clipping on DAC reconstruction and lossy MP3/AAC compression, guaranteeing a true peak ceiling $\le -1.0\text{ dBTP}$.

### Stage 11: Audio Quality Verification
- Re-analyzes the final enhanced audio array:
  - Verifies duration is preserved within 0.05 seconds.
  - Verifies sample rate and stereo channel count are preserved.
  - Verifies 0 clipped samples remain.
  - Verifies true peak is strictly below the ceiling.
  - Verifies no NaN or infinite values were produced.
  - Generates a human-readable comparative quality report.

### Stage 12: Studio Master Export
- Exports final audio as 24-bit PCM WAV, MP3 320kbps CBR, or lossless FLAC.
