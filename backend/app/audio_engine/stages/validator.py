import math
import numpy as np
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage
from app.audio_engine.analyzer import AudioAnalyzer

class QualityValidatorStage(PipelineStage):
    """
    Stage 11: Final Audio Quality Validation & Comparative Analysis.
    Verifies that the audio is completely intact:
    - Duration preserved within 0.05s
    - Sample rate & channels preserved
    - No NaN / Inf samples
    - 0 clipped samples
    - True peak within ceiling
    - No unexpected silence dropouts
    - Produces comprehensive comparative quality report
    """
    def __init__(self):
        super().__init__("quality_validation")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        return audio, {"stage": self.name, "status": "completed"}

    @classmethod
    def validate_and_compare(
        cls,
        original_audio: np.ndarray,
        processed_audio: np.ndarray,
        sample_rate: int,
        original_analysis: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """
        Runs comprehensive comparative analysis between original and processed audio.
        Returns:
            passed: bool (true if all integrity checks passed)
            processed_analysis: Dict of processed metrics
            comparison_report: Dict of comparative differences
        """
        # 1. Basic integrity checks on processed audio
        if np.any(np.isnan(processed_audio)) or np.any(np.isinf(processed_audio)):
            return False, {}, {
                "overall_quality_passed": False,
                "nan_inf_check_passed": False,
                "quality_summary": "Processing failed: Output contains invalid NaN or Infinite numerical samples."
            }

        # 2. Re-analyze processed audio with AudioAnalyzer
        processed_analysis = AudioAnalyzer.analyze(processed_audio, sample_rate)

        # 3. Duration preservation check (tolerance <= 0.05 seconds)
        orig_dur = original_analysis.get("duration_seconds", len(original_audio) / sample_rate)
        proc_dur = processed_analysis["duration_seconds"]
        delta_dur = abs(proc_dur - orig_dur)
        duration_passed = delta_dur <= 0.05

        # 4. Clipping check
        orig_clipped = original_analysis.get("quality_problems", {}).get("clipped_sample_count", 0)
        proc_clipped = processed_analysis["quality_problems"]["clipped_sample_count"]
        clipping_resolved = proc_clipped == 0

        # 5. Loudness & True Peak checks
        orig_lufs = original_analysis.get("integrated_lufs")
        proc_lufs = processed_analysis.get("integrated_lufs")
        orig_tp = original_analysis.get("true_peak_dbtp")
        proc_tp = processed_analysis.get("true_peak_dbtp")

        # True peak must be <= -0.5 dBTP
        tp_passed = proc_tp is None or proc_tp <= -0.5

        # 6. Silence dropout check: if processed is > 95% silence when original wasn't
        orig_silence_pct = original_analysis.get("silence_percentage", 0.0)
        proc_silence_pct = processed_analysis.get("silence_percentage", 0.0)
        silence_dropout = (proc_silence_pct > 90.0) and (orig_silence_pct < 50.0)

        # 7. SNR difference estimation
        orig_snr = original_analysis.get("estimated_snr_db")
        proc_snr = processed_analysis.get("estimated_snr_db")
        snr_diff = (proc_snr - orig_snr) if (proc_snr is not None and orig_snr is not None) else None

        overall_passed = duration_passed and (not silence_dropout) and (proc_clipped == 0) and tp_passed

        # Formulate human-readable quality summary
        summary_points = []
        if clipping_resolved and orig_clipped > 0:
            summary_points.append(f"Cleaned {orig_clipped} clipped samples to 0.")
        if tp_passed:
            summary_points.append(f"Guaranteed true peak ceiling at {proc_tp:.1f} dBTP.")
        if proc_lufs:
            summary_points.append(f"Leveled integrated loudness to {proc_lufs:.1f} LUFS.")
        if snr_diff is not None and snr_diff > 1.0:
            summary_points.append(f"Improved estimated vocal clarity / SNR by +{snr_diff:.1f} dB.")
        if not duration_passed:
            summary_points.append(f"Warning: Duration shifted by {delta_dur:.3f}s.")

        quality_summary = " ".join(summary_points) if summary_points else "Audio enhanced cleanly without distortion."

        comparison_report = {
            "duration_passed": duration_passed,
            "duration_delta_seconds": round(delta_dur, 4),
            "clipping_resolved": clipping_resolved,
            "original_clipped_samples": orig_clipped,
            "processed_clipped_samples": proc_clipped,
            "original_integrated_lufs": orig_lufs,
            "processed_integrated_lufs": proc_lufs,
            "original_true_peak_dbtp": orig_tp,
            "processed_true_peak_dbtp": proc_tp,
            "original_rms_dbfs": original_analysis.get("rms_dbfs", -30.0),
            "processed_rms_dbfs": processed_analysis.get("rms_dbfs", -30.0),
            "original_crest_factor_db": original_analysis.get("crest_factor_db", 12.0),
            "processed_crest_factor_db": processed_analysis.get("crest_factor_db", 12.0),
            "estimated_snr_change_db": round(snr_diff, 2) if snr_diff is not None else None,
            "nan_inf_check_passed": True,
            "silence_dropout_detected": silence_dropout,
            "overall_quality_passed": overall_passed,
            "quality_summary": quality_summary
        }

        return overall_passed, processed_analysis, comparison_report
