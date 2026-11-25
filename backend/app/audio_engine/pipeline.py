import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Callable
import numpy as np
import soundfile as sf

from app.audio_engine.analyzer import AudioAnalyzer
from app.audio_engine.stages.noise_reduction import NoiseReductionStage
from app.audio_engine.stages.filters import HighPassFilterStage, EqualizerStage
from app.audio_engine.stages.autotune import AutoTuneStage
from app.audio_engine.stages.saturation import WarmTubeSaturationStage
from app.audio_engine.stages.dynamics import CompressorStage, DeesserStage, LimiterStage
from app.audio_engine.stages.doubler import VocalDoublerStage
from app.audio_engine.stages.reverb import NaturalReverbStage
from app.audio_engine.stages.echo import EchoDelayStage
from app.audio_engine.stages.loudness import LoudnessNormalizationStage
from app.audio_engine.stages.validator import QualityValidatorStage

logger = logging.getLogger(__name__)

class AudioEnhancementPipeline:
    """
    16-Stage Studio Audio Enhancement Pipeline for Naat & Vocal Recitations.
    Includes Auto-Tune pitch quantization, Warm Tube Saturation, Stereo Vocal Doubler,
    Studio Echo/Delay, Noise Suppression, Biquad EQ, Dynamics Compression,
    Moorer Reverb, and EBU R128 Loudness Mastering.
    """
    def __init__(self, preferred_nr_backend: str = "auto"):
        self.stage_nr = NoiseReductionStage(preferred_backend=preferred_nr_backend)
        self.stage_hp = HighPassFilterStage()
        self.stage_eq = EqualizerStage()
        self.stage_tune = AutoTuneStage()
        self.stage_sat = WarmTubeSaturationStage()
        self.stage_comp = CompressorStage()
        self.stage_deess = DeesserStage()
        self.stage_doubler = VocalDoublerStage()
        self.stage_reverb = NaturalReverbStage()
        self.stage_echo = EchoDelayStage()
        self.stage_loudness = LoudnessNormalizationStage()
        self.stage_limiter = LimiterStage()
        self.stage_validator = QualityValidatorStage()

    def process_array(
        self,
        audio: np.ndarray,
        sample_rate: int,
        config: Dict[str, Any],
        initial_analysis: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes the full enhancement DSP chain directly on an in-memory NumPy array.
        """
        def update_progress(stage: str, percent: int):
            if cancel_check and cancel_check():
                raise InterruptedError("Processing job cancelled by user")
            if progress_callback:
                progress_callback(stage, percent)

        original_audio = audio.copy()

        # Stage 2: Initial Analysis
        update_progress("analyzing", 10)
        if initial_analysis is None:
            initial_analysis = AudioAnalyzer.analyze(audio, sample_rate)

        # Stage 3: Intelligent Noise Reduction (Hum + Spectral Gating + Adaptive Downward Expander)
        update_progress("denoising", 22)
        audio, meta_nr = self.stage_nr.process(audio, sample_rate, config)

        # Stage 4: High-Pass Filtering & Corrective Equalization
        update_progress("filtering", 32)
        audio, meta_hp = self.stage_hp.process(audio, sample_rate, config)
        update_progress("equalizing", 40)
        audio, meta_eq = self.stage_eq.process(audio, sample_rate, config)

        # Stage 5: Vocal Compression (Transparent optical leveling)
        update_progress("compressing", 52)
        audio, meta_comp = self.stage_comp.process(audio, sample_rate, config)

        # Stage 6: Presence & Tonal Enhancement (Warmth, De-essing, optional Pitch/Doubler)
        update_progress("saturating", 60)
        audio, meta_sat = self.stage_sat.process(audio, sample_rate, config)
        update_progress("deessing", 66)
        audio, meta_deess = self.stage_deess.process(audio, sample_rate, config)
        audio, meta_tune = self.stage_tune.process(audio, sample_rate, config)
        audio, meta_doubler = self.stage_doubler.process(audio, sample_rate, config)

        # Stage 7: Professional Studio Reverb (Early Reflections + Damped Hall Ambience)
        update_progress("reverberating", 78)
        audio, meta_rev = self.stage_reverb.process(audio, sample_rate, config)
        audio, meta_echo = self.stage_echo.process(audio, sample_rate, config)

        # Stage 8: Loudness Normalization (EBU R128)
        update_progress("normalizing", 90)
        audio, meta_loud = self.stage_loudness.process(audio, sample_rate, config)

        # Stage 9: Lookahead True-Peak Limiting
        update_progress("limiting", 94)
        audio, meta_limit = self.stage_limiter.process(audio, sample_rate, config)

        # Stage 15: Final Audio Quality Validation
        update_progress("validating", 96)
        passed, processed_analysis, comparison_report = QualityValidatorStage.validate_and_compare(
            original_audio=original_audio,
            processed_audio=audio,
            sample_rate=sample_rate,
            original_analysis=initial_analysis
        )

        if not passed and not comparison_report.get("nan_inf_check_passed", True):
            raise ValueError("Signal processing produced numerical anomalies (NaN or Inf)")

        return audio, {
            "processed_analysis": processed_analysis,
            "comparison_report": comparison_report,
            "stage_metadata": {
                "noise_reduction": meta_nr,
                "high_pass": meta_hp,
                "equalizer": meta_eq,
                "autotune": meta_tune,
                "tube_saturation": meta_sat,
                "compressor": meta_comp,
                "deesser": meta_deess,
                "vocal_doubler": meta_doubler,
                "reverb": meta_rev,
                "echo": meta_echo,
                "loudness": meta_loud,
                "limiter": meta_limit,
            }
        }

    def process_file(
        self,
        input_path: str,
        output_path: str,
        config: Dict[str, Any],
        initial_analysis: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Executes enhancement pipeline stages on an audio file.
        """
        def update_progress(stage: str, percent: int):
            if cancel_check and cancel_check():
                raise InterruptedError("Processing job cancelled by user")
            if progress_callback:
                progress_callback(stage, percent)

        # Stage 1: Decoding
        update_progress("decoding", 5)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input audio file not found: {input_path}")

        audio, sample_rate = sf.read(input_path, dtype="float32", always_2d=False)

        # Optional Region Trimming & Slicing
        trim_cfg = config.get("trim", {})
        start_sec = float(trim_cfg.get("start_seconds", 0.0) or 0.0)
        end_sec = trim_cfg.get("end_seconds", None)
        if end_sec is not None:
            end_sec = float(end_sec)

        if start_sec > 0.0 or (end_sec is not None and end_sec < float(len(audio) / sample_rate)):
            start_sample = int(start_sec * sample_rate)
            end_sample = int(end_sec * sample_rate) if end_sec is not None else len(audio)
            start_sample = max(0, min(start_sample, len(audio) - int(sample_rate * 0.2)))
            end_sample = max(start_sample + int(sample_rate * 0.2), min(end_sample, len(audio)))
            audio = audio[start_sample:end_sample]
            fade_len = min(int(sample_rate * 0.012), len(audio) // 4)
            if fade_len > 0:
                fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
                fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
                if audio.ndim == 1:
                    audio[:fade_len] *= fade_in
                    audio[-fade_len:] *= fade_out
                else:
                    audio[:fade_len] *= fade_in[:, np.newaxis]
                    audio[-fade_len:] *= fade_out[:, np.newaxis]

        if start_sec > 0.0 or end_sec is not None:
            initial_analysis = None

        audio, result = self.process_array(
            audio=audio,
            sample_rate=sample_rate,
            config=config,
            initial_analysis=initial_analysis,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )

        # Stage 16: Export
        update_progress("exporting", 98)
        output_format = config.get("output_format", "wav").lower()
        self._export_audio(audio, sample_rate, output_path, output_format)

        update_progress("completed", 100)
        return result

    @staticmethod
    def _export_audio(audio: np.ndarray, sample_rate: int, output_path: str, output_format: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if output_format == "wav":
            sf.write(output_path, audio, sample_rate, subtype="PCM_24", format="WAV")
        elif output_format == "flac":
            sf.write(output_path, audio, sample_rate, subtype="PCM_24", format="FLAC")
        elif output_format == "mp3":
            temp_wav = output_path + ".temp.wav"
            try:
                sf.write(temp_wav, audio, sample_rate, subtype="PCM_24")
                cmd = ["ffmpeg", "-y", "-i", temp_wav, "-codec:a", "libmp3lame", "-b:a", "320k", output_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    shutil.copyfile(temp_wav, output_path)
            finally:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
        else:
            sf.write(output_path, audio, sample_rate, subtype="PCM_24")
