from typing import Dict, Any, Optional, Tuple
from app.schemas.processing import ProcessingParametersOverride

class EnhancementDecisionEngine:
    """
    Intelligent decision engine for studio-grade vocal enhancement.
    Configures noise reduction, biquad EQ, Auto-Tune pitch quantization,
    warm tube saturation, vocal compression, de-essing, stereo vocal doubler,
    spiritual reverb, studio echo/delay, trimming, and loudness mastering.
    """

    @classmethod
    def decide(
        cls,
        analysis: Dict[str, Any],
        preset: str = "studio_naat",
        automatic_mode: bool = True,
        overrides: Optional[ProcessingParametersOverride] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        problems = analysis.get("quality_problems", {})
        bands = analysis.get("frequency_bands", {})
        est_snr = analysis.get("estimated_snr_db", 30.0)
        current_lufs = analysis.get("integrated_lufs", -20.0)
        crest_factor = analysis.get("crest_factor_db", 14.0)

        notes = []

        # Preset baselines
        preset_configs = {
            "natural_naat": {
                "base_reverb_wet": 0.08,
                "base_reverb_decay": 1.1,
                "echo_enabled": False,
                "echo_wet": 0.0,
                "echo_delay_ms": 240.0,
                "echo_feedback": 0.20,
                "autotune_enabled": False,
                "autotune_strength": 0.0,
                "autotune_scale": "chromatic",
                "tube_enabled": False,
                "tube_warmth": 0.0,
                "doubler_enabled": False,
                "doubler_mix": 0.0,
                "doubler_width": 0.7,
                "target_lufs": -16.0,
                "comp_ratio": 2.0,
                "comp_attack_ms": 25.0,
                "comp_release_ms": 180.0,
                "air_boost_db": 1.0,
                "noise_strength": 0.40,
            },
            "studio_naat": {
                "base_reverb_wet": 0.13,
                "base_reverb_decay": 1.4,
                "echo_enabled": False,
                "echo_wet": 0.0,
                "echo_delay_ms": 220.0,
                "echo_feedback": 0.15,
                "autotune_enabled": False,  # Strictly preserve natural reciter pitch, Tajweed & emotion
                "autotune_strength": 0.0,
                "autotune_scale": "chromatic",
                "tube_enabled": True,
                "tube_warmth": 0.22,
                "doubler_enabled": False,  # Pure condenser-mic clarity without phasey chorus
                "doubler_mix": 0.0,
                "doubler_width": 0.75,
                "target_lufs": -16.0,  # Broadcast / Podcast studio loudness without pumping
                "comp_ratio": 2.3,     # Transparent optical vocal leveling
                "comp_attack_ms": 22.0,
                "comp_release_ms": 180.0,
                "air_boost_db": 2.5,
                "noise_strength": 0.70, # Clean noise removal preserving full vocal body
            },
            "spacious_naat": {
                "base_reverb_wet": 0.22,
                "base_reverb_decay": 2.2,
                "echo_enabled": True,
                "echo_wet": 0.12,
                "echo_delay_ms": 300.0,
                "echo_feedback": 0.22,
                "autotune_enabled": True,
                "autotune_strength": 0.45,
                "autotune_scale": "hijaz",
                "tube_enabled": True,
                "tube_warmth": 0.25,
                "doubler_enabled": True,
                "doubler_mix": 0.15,
                "doubler_width": 0.85,
                "target_lufs": -16.0,
                "comp_ratio": 2.2,
                "comp_attack_ms": 30.0,
                "comp_release_ms": 220.0,
                "air_boost_db": 1.5,
                "noise_strength": 0.50,
            },
            "maqam_classical": {
                "base_reverb_wet": 0.18,
                "base_reverb_decay": 2.0,
                "echo_enabled": True,
                "echo_wet": 0.10,
                "echo_delay_ms": 260.0,
                "echo_feedback": 0.22,
                "autotune_enabled": True,
                "autotune_strength": 0.40,
                "autotune_scale": "bayati",
                "tube_enabled": True,
                "tube_warmth": 0.45,
                "doubler_enabled": False,
                "doubler_mix": 0.0,
                "doubler_width": 0.75,
                "target_lufs": -15.0,
                "comp_ratio": 2.4,
                "comp_attack_ms": 22.0,
                "comp_release_ms": 160.0,
                "air_boost_db": 2.0,
                "noise_strength": 0.55,
            },
            "jalsa_live": {
                "base_reverb_wet": 0.12,
                "base_reverb_decay": 1.4,
                "echo_enabled": True,
                "echo_wet": 0.18,
                "echo_delay_ms": 220.0,
                "echo_feedback": 0.32,
                "autotune_enabled": True,
                "autotune_strength": 0.70,
                "autotune_scale": "chromatic",
                "tube_enabled": True,
                "tube_warmth": 0.30,
                "doubler_enabled": False,
                "doubler_mix": 0.0,
                "doubler_width": 0.8,
                "target_lufs": -13.5,  # Loud energetic master
                "comp_ratio": 3.4,
                "comp_attack_ms": 12.0,
                "comp_release_ms": 100.0,
                "air_boost_db": 3.0,
                "noise_strength": 0.75,  # Aggressive noise suppression
            },
            "modern_nasheed": {
                "base_reverb_wet": 0.16,
                "base_reverb_decay": 1.6,
                "echo_enabled": True,
                "echo_wet": 0.16,
                "echo_delay_ms": 240.0,
                "echo_feedback": 0.26,
                "autotune_enabled": True,
                "autotune_strength": 0.75,
                "autotune_scale": "chromatic",
                "tube_enabled": True,
                "tube_warmth": 0.40,
                "doubler_enabled": True,
                "doubler_mix": 0.24,
                "doubler_width": 0.9,
                "target_lufs": -14.0,
                "comp_ratio": 2.8,
                "comp_attack_ms": 15.0,
                "comp_release_ms": 130.0,
                "air_boost_db": 3.2,
                "noise_strength": 0.60,
            },
            "youth_vocal": {
                "base_reverb_wet": 0.14,
                "base_reverb_decay": 1.4,
                "echo_enabled": True,
                "echo_wet": 0.12,
                "echo_delay_ms": 230.0,
                "echo_feedback": 0.24,
                "autotune_enabled": True,
                "autotune_strength": 0.65,
                "autotune_scale": "chromatic",
                "tube_enabled": True,
                "tube_warmth": 0.45,
                "doubler_enabled": False,
                "doubler_mix": 0.0,
                "doubler_width": 0.75,
                "target_lufs": -14.5,
                "comp_ratio": 2.6,
                "comp_attack_ms": 20.0,
                "comp_release_ms": 150.0,
                "air_boost_db": 1.5,
                "noise_strength": 0.55,
            },
            "deep_baritone": {
                "base_reverb_wet": 0.16,
                "base_reverb_decay": 1.8,
                "echo_enabled": True,
                "echo_wet": 0.14,
                "echo_delay_ms": 250.0,
                "echo_feedback": 0.28,
                "autotune_enabled": True,
                "autotune_strength": 0.55,
                "autotune_scale": "chromatic",
                "tube_enabled": True,
                "tube_warmth": 0.50,
                "doubler_enabled": False,
                "doubler_mix": 0.0,
                "doubler_width": 0.8,
                "target_lufs": -14.0,
                "comp_ratio": 2.8,
                "comp_attack_ms": 25.0,
                "comp_release_ms": 160.0,
                "air_boost_db": 2.5,
                "noise_strength": 0.60,
            },
        }

        active_preset = preset if preset in preset_configs else "studio_naat"
        base = preset_configs[active_preset]

        # 1. Noise Reduction Decision (Advanced Spectral Subtraction + Downward Voice Expander)
        nr_enabled = True
        if problems.get("has_high_noise_floor", False) or (est_snr is not None and est_snr < 32.0):
            nr_strength = max(0.85, base["noise_strength"])
            nr_mode = "maximum"
            nr_decision = f"Complete studio noise elimination engaged (strength {nr_strength:.2f}, mode: maximum): Silences room hiss, computer hum, and background acoustics down to studio black level."
        elif est_snr is not None and est_snr > 38.0 and not problems.get("has_high_noise_floor", False):
            nr_strength = 0.40
            nr_mode = "subtle"
            nr_decision = f"Subtle noise reduction engaged (strength 0.40): Recording has clean SNR ({est_snr:.1f} dB)."
        else:
            nr_strength = max(0.75, base["noise_strength"])
            nr_mode = "aggressive" if base.get("noise_strength", 0.6) > 0.7 else "balanced"
            nr_decision = f"Studio background noise elimination engaged (strength {nr_strength:.2f}, mode: {nr_mode}): Clears pre-amp hiss and room fan hum with downward noise expander."

        # 2. High-Pass Filter Decision
        if problems.get("has_sub_rumble", False) or bands.get("sub_bass_energy_db", -50) > -20.0:
            hp_cutoff_hz = 80.0
            hp_decision = "High-pass filter engaged at 80 Hz: Sub-bass rumble and handling noise eliminated."
        else:
            hp_cutoff_hz = 72.0
            hp_decision = "Gentle high-pass filter engaged at 72 Hz: Clears subsonic thumps while preserving chest warmth."

        # 3. Parametric Equalization Decision
        eq_mud_gain_db = -3.2 if problems.get("has_boxiness_mud", False) else -2.2
        eq_mud_freq_hz = 320.0
        eq_presence_gain_db = 3.2
        eq_air_gain_db = base["air_boost_db"]
        eq_decision = (
            f"Studio EQ: {eq_mud_gain_db:+.1f} dB mud reduction @ 320 Hz, "
            f"+{eq_presence_gain_db:.1f} dB diction clarity @ 3.5 kHz, +{eq_air_gain_db:.1f} dB air sparkle @ 10 kHz."
        )

        # 4. Auto-Tune Pitch Correction Decision
        tune_enabled = base["autotune_enabled"]
        tune_strength = base["autotune_strength"]
        tune_scale = base["autotune_scale"]
        if tune_enabled:
            tune_decision = f"Vocal Auto-Tune pitch correction engaged ({int(tune_strength * 100)}% strength, {tune_scale.title()} scale): Smooth intonation correction."
        else:
            tune_decision = "Auto-Tune bypassed: Natural unquantized vocal pitch preserved."

        # 5. Warm Tube Saturation Decision
        tube_enabled = base["tube_enabled"]
        tube_warmth = base["tube_warmth"]
        if tube_enabled and tube_warmth > 0.02:
            saturation_decision = f"Warm analog tube saturation engaged (warmth {int(tube_warmth * 100)}%): Adds 2nd-order vocal richness and rounds sharp transients."
        else:
            saturation_decision = "Analog tube saturation bypassed."

        # 6. Dynamic Compression Decision
        comp_ratio = base["comp_ratio"]
        comp_threshold_db = -19.0
        comp_decision = f"Studio vocal leveling (ratio {comp_ratio:.1f}:1, -19 dB threshold): Balanced dynamic consistency."

        # 7. De-essing Decision
        deess_enabled = True
        deess_threshold_db = -18.0
        deess_freq_hz = 6500.0
        deess_decision = "Dynamic de-essing enabled at 6.5 kHz: Tames harsh sibilants on consonants."

        # 8. Stereo Vocal Doubler & Acapella Harmony Decision
        doubler_enabled = base["doubler_enabled"]
        doubler_mix = base["doubler_mix"]
        doubler_width = base["doubler_width"]
        if doubler_enabled and doubler_mix > 0.02:
            doubler_decision = f"Studio vocal doubler engaged ({int(doubler_mix * 100)}% mix, {int(doubler_width * 100)}% width): Creates lush acapella width."
        else:
            doubler_decision = "Vocal doubler bypassed."

        # 9. Spiritual Reverb Decision
        reverb_wet = base["base_reverb_wet"]
        reverb_decay = base["base_reverb_decay"]
        reverb_decision = f"Acoustic chamber reverb: {int(reverb_wet * 100)}% wet mix, {reverb_decay:.1f}s decay with 25ms pre-delay."

        # 10. Studio Vocal Echo / Delay Decision
        echo_enabled = base["echo_enabled"]
        echo_wet = base["echo_wet"]
        echo_delay_ms = base["echo_delay_ms"]
        echo_feedback = base["echo_feedback"]
        if echo_enabled:
            echo_decision = f"Studio vocal echo engaged ({int(echo_wet * 100)}% wet, {int(echo_delay_ms)}ms delay, {int(echo_feedback * 100)}% feedback) with high-cut damping."
        else:
            echo_decision = "Echo / delay bypassed."

        # 11. Region Trim Decision
        trim_start = 0.0
        trim_end = None
        strip_silence = False
        trim_decision = "Full track enhancement (no trimming)."

        # 12. Loudness Normalization Decision
        target_lufs = base["target_lufs"]
        loudness_decision = f"Studio broadcast mastering: Standardized to {target_lufs:.1f} LUFS."

        # 13. True-Peak Limiter
        true_peak_ceiling = -1.0
        limiting_decision = "Lookahead true-peak limiter active at -1.0 dBTP ceiling with 4x oversampling."

        # User overrides
        if overrides:
            if overrides.noise_reduction_enabled is not None:
                nr_enabled = overrides.noise_reduction_enabled
            if overrides.noise_reduction_mode is not None:
                nr_mode = overrides.noise_reduction_mode
            if overrides.noise_reduction_strength is not None:
                nr_strength = overrides.noise_reduction_strength
                nr_decision = f"User override applied: Noise reduction strength = {nr_strength:.2f} (mode: {nr_mode})."
            if overrides.eq_intensity is not None:
                scale = overrides.eq_intensity
                eq_mud_gain_db *= scale
                eq_presence_gain_db *= scale
                eq_air_gain_db *= scale
                eq_decision = f"User override applied: EQ intensity scaled to {scale:.2f}."
            if overrides.autotune_enabled is not None:
                tune_enabled = overrides.autotune_enabled
            if overrides.autotune_strength is not None:
                tune_strength = overrides.autotune_strength
                tune_enabled = tune_strength > 0.02
                tune_decision = f"User override applied: Auto-tune strength = {int(tune_strength * 100)}%."
            if overrides.autotune_scale is not None:
                tune_scale = overrides.autotune_scale
            if overrides.tube_saturation_enabled is not None:
                tube_enabled = overrides.tube_saturation_enabled
            if overrides.tube_warmth is not None:
                tube_warmth = overrides.tube_warmth
                tube_enabled = tube_warmth > 0.02
                saturation_decision = f"User override applied: Tube warmth = {int(tube_warmth * 100)}%."
            if overrides.doubler_enabled is not None:
                doubler_enabled = overrides.doubler_enabled
            if overrides.doubler_mix is not None:
                doubler_mix = overrides.doubler_mix
                doubler_enabled = doubler_mix > 0.02
                doubler_decision = f"User override applied: Vocal doubler mix = {int(doubler_mix * 100)}%."
            if overrides.doubler_width is not None:
                doubler_width = overrides.doubler_width
            if overrides.echo_enabled is not None:
                echo_enabled = overrides.echo_enabled
            if overrides.echo_amount is not None:
                echo_wet = overrides.echo_amount
                echo_enabled = echo_wet > 0.01
                echo_decision = f"User override applied: Echo wet = {int(echo_wet * 100)}%."
            if overrides.echo_delay_ms is not None:
                echo_delay_ms = overrides.echo_delay_ms
            if overrides.echo_feedback is not None:
                echo_feedback = overrides.echo_feedback
            if overrides.compression_intensity is not None:
                comp_ratio = 1.0 + (overrides.compression_intensity * 3.5)
                comp_decision = f"User override applied: Compression ratio = {comp_ratio:.2f}:1."
            if overrides.reverb_amount is not None:
                reverb_wet = overrides.reverb_amount * 0.4
                reverb_decision = f"User override applied: Reverb wet = {int(reverb_wet * 100)}%."
            if overrides.trim_start_seconds is not None or overrides.trim_end_seconds is not None:
                trim_start = overrides.trim_start_seconds or 0.0
                trim_end = overrides.trim_end_seconds
                trim_decision = f"Region trimmed: {trim_start:.2f}s to {f'{trim_end:.2f}s' if trim_end else 'end'}."
            if overrides.strip_silence is not None:
                strip_silence = overrides.strip_silence
                if strip_silence:
                    trim_decision += " | Silence gap stripper enabled."
            if overrides.target_lufs is not None:
                target_lufs = overrides.target_lufs
                loudness_decision = f"User override applied: Loudness target = {target_lufs:.1f} LUFS."
            if overrides.true_peak_ceiling is not None:
                true_peak_ceiling = overrides.true_peak_ceiling

            # Clean Studio Controls mapping
            if overrides.noise_reduction_level is not None:
                lvl = overrides.noise_reduction_level.lower()
                nr_enabled = True
                if lvl == "low":
                    nr_strength, nr_mode = 0.35, "subtle"
                elif lvl == "high":
                    nr_strength, nr_mode = 0.85, "aggressive"
                else:
                    nr_strength, nr_mode = 0.65, "balanced"
                nr_decision = f"Studio Noise Reduction set to {lvl.capitalize()} ({nr_mode}, {int(nr_strength*100)}%)."

            if overrides.reverb_level is not None:
                rlvl = overrides.reverb_level.lower()
                if rlvl == "low":
                    reverb_wet, reverb_decay = 0.06, 1.0
                elif rlvl == "high":
                    reverb_wet, reverb_decay = 0.22, 2.0
                else:
                    reverb_wet, reverb_decay = 0.13, 1.4
                reverb_decision = f"Studio Reverb set to {rlvl.capitalize()} (wet={int(reverb_wet*100)}%, decay={reverb_decay}s)."

            if overrides.vocal_warmth is not None:
                w = float(overrides.vocal_warmth)
                tube_warmth = w * 0.45
                tube_enabled = tube_warmth > 0.02
                saturation_decision = f"Vocal Warmth set to {int(w*100)}%."

            if overrides.vocal_clarity is not None:
                c = float(overrides.vocal_clarity)
                eq_presence_gain_db = 0.5 + (c * 3.5)
                eq_air_gain_db = 0.5 + (c * 3.5)
                eq_decision = f"Vocal Clarity set to {int(c*100)}% (+{eq_presence_gain_db:.1f} dB presence, +{eq_air_gain_db:.1f} dB air)."

            if overrides.compression_amount is not None:
                ca = float(overrides.compression_amount)
                comp_ratio = 1.2 + (ca * 2.6)
                comp_decision = f"Vocal Compression set to {int(ca*100)}% ({comp_ratio:.2f}:1)."

        config = {
            "preset": active_preset,
            "trim": {
                "start_seconds": trim_start,
                "end_seconds": trim_end,
                "strip_silence": strip_silence,
            },
            "noise_reduction": {
                "enabled": nr_enabled and nr_strength > 0.01 and nr_mode != "off",
                "strength": round(nr_strength, 2),
                "mode": nr_mode,
            },
            "high_pass": {
                "enabled": True,
                "cutoff_hz": hp_cutoff_hz,
                "order": 2,
            },
            "equalizer": {
                "enabled": True,
                "mud_cut_gain_db": round(eq_mud_gain_db, 2),
                "mud_cut_freq_hz": eq_mud_freq_hz,
                "presence_boost_gain_db": round(eq_presence_gain_db, 2),
                "presence_freq_hz": 3500.0,
                "air_shelf_gain_db": round(eq_air_gain_db, 2),
                "air_shelf_freq_hz": 10000.0,
            },
            "autotune": {
                "enabled": tune_enabled,
                "strength": round(tune_strength, 2),
                "scale": tune_scale,
            },
            "saturation": {
                "enabled": tube_enabled,
                "warmth": round(tube_warmth, 2),
                "drive": 1.25,
            },
            "compressor": {
                "enabled": True,
                "threshold_db": round(comp_threshold_db, 1),
                "ratio": round(comp_ratio, 2),
                "attack_ms": base["comp_attack_ms"],
                "release_ms": base["comp_release_ms"],
                "knee_db": 4.0,
            },
            "deesser": {
                "enabled": deess_enabled,
                "threshold_db": deess_threshold_db,
                "freq_hz": deess_freq_hz,
            },
            "doubler": {
                "enabled": doubler_enabled,
                "mix": round(doubler_mix, 2),
                "width": round(doubler_width, 2),
            },
            "reverb": {
                "enabled": reverb_wet > 0.01,
                "wet": round(reverb_wet, 3),
                "dry": round(1.0 - (reverb_wet * 0.4), 3),
                "decay_time_seconds": round(reverb_decay, 2),
                "pre_delay_ms": 25.0,
                "damping": 0.4,
            },
            "echo": {
                "enabled": echo_enabled,
                "wet": round(echo_wet, 3),
                "delay_time_ms": round(echo_delay_ms, 1),
                "feedback": round(echo_feedback, 2),
                "damping": 0.45,
            },
            "loudness": {
                "target_lufs": round(target_lufs, 1),
            },
            "limiter": {
                "ceiling_dbtp": round(true_peak_ceiling, 1),
                "release_ms": 50.0,
            },
            "output_format": overrides.output_format if overrides and overrides.output_format else "wav",
        }

        decision_log = {
            "preset_selected": active_preset,
            "noise_reduction_decision": nr_decision,
            "high_pass_decision": hp_decision,
            "eq_decision": eq_decision,
            "autotune_decision": tune_decision,
            "saturation_decision": saturation_decision,
            "compression_decision": comp_decision,
            "deess_decision": deess_decision,
            "doubler_decision": doubler_decision,
            "reverb_decision": reverb_decision,
            "echo_decision": echo_decision,
            "trim_decision": trim_decision,
            "loudness_decision": loudness_decision,
            "limiting_decision": limiting_decision,
            "notes": notes,
        }

        return config, decision_log
