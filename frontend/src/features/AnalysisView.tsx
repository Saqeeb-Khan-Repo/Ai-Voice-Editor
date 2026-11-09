"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  BarChart3,
  Waves,
  Volume2,
  Sliders,
  ShieldAlert,
  Sparkles,
  Mic,
  Music,
} from "lucide-react";
import { AudioAnalysisReport } from "@/types";

interface AnalysisViewProps {
  analysis: AudioAnalysisReport | null;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="bg-studio-900 border border-studio-800 rounded-2xl p-12 text-center text-slate-400">
        <Activity size={40} className="mx-auto mb-3 text-studio-600" />
        <h3 className="text-base font-semibold text-white">No Audio Recording Loaded</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
          Upload an audio file in the Studio tab to view automated acoustic metrics, spectral distribution, and diagnostic recommendations.
        </p>
      </div>
    );
  }

  const {
    duration_seconds,
    sample_rate,
    channels,
    peak_amplitude_dbfs,
    rms_dbfs,
    crest_factor_db,
    integrated_lufs,
    true_peak_dbtp,
    silence_percentage,
    silence_regions,
    estimated_snr_db,
    noise_estimation_confidence,
    frequency_bands,
    quality_problems,
    vocal_profile,
    recommendations,
  } = analysis;

  const bandList = [
    { name: "Sub-Bass (<60Hz)", val: frequency_bands.sub_bass_energy_db, desc: "Mic handling / Rumble" },
    { name: "Bass (60-250Hz)", val: frequency_bands.bass_energy_db, desc: "Chest tone / Pitch" },
    { name: "Low-Mids (250-500Hz)", val: frequency_bands.low_mid_energy_db, desc: "Room boxiness / Mud" },
    { name: "Mids (500-2kHz)", val: frequency_bands.mid_energy_db, desc: "Vocal body & vowels" },
    { name: "High-Mids (2k-5kHz)", val: frequency_bands.high_mid_energy_db, desc: "Intelligibility & diction" },
    { name: "Presence (5k-10kHz)", val: frequency_bands.presence_high_energy_db, desc: "Consonants & sibilance" },
    { name: "Air (>10kHz)", val: frequency_bands.air_energy_db, desc: "Breath & openness" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Activity size={20} className="text-cyan-400" /> Objective Audio Quality Analysis
        </h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Comprehensive diagnostic metrics and frequency balance analysis of the vocal recording.
        </p>
      </div>

      {/* Primary Key Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          {
            label: "Integrated Loudness",
            value: integrated_lufs !== null ? `${integrated_lufs.toFixed(1)} LUFS` : "N/A",
            sub: "EBU R128 Standard",
            status: integrated_lufs && integrated_lufs >= -18 && integrated_lufs <= -14 ? "good" : "neutral",
          },
          {
            label: "True Peak",
            value: true_peak_dbtp !== null ? `${true_peak_dbtp.toFixed(1)} dBTP` : `${peak_amplitude_dbfs.toFixed(1)} dBFS`,
            sub: "4x Oversampled",
            status: true_peak_dbtp && true_peak_dbtp > -0.5 ? "warn" : "good",
          },
          {
            label: "RMS Level",
            value: `${rms_dbfs.toFixed(1)} dBFS`,
            sub: "Average Energy",
            status: "neutral",
          },
          {
            label: "Crest Factor",
            value: `${crest_factor_db.toFixed(1)} dB`,
            sub: "Dynamic Range",
            status: crest_factor_db > 16 ? "neutral" : "good",
          },
          {
            label: "Estimated SNR",
            value: estimated_snr_db !== null ? `${estimated_snr_db.toFixed(1)} dB` : "N/A",
            sub: `${noise_estimation_confidence} pause`,
            status: estimated_snr_db && estimated_snr_db > 25 ? "good" : "warn",
          },
          {
            label: "Digital Clipping",
            value: quality_problems.has_clipping ? `${quality_problems.clipped_sample_count} samples` : "0 (Clean)",
            sub: quality_problems.has_clipping ? `${quality_problems.clipped_sample_percentage}% clipped` : "No distortion",
            status: quality_problems.has_clipping ? "error" : "good",
          },
        ].map((item, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border bg-studio-900 ${
              item.status === "error"
                ? "border-rose-500/40"
                : item.status === "warn"
                ? "border-amber-500/40"
                : "border-studio-800"
            }`}
          >
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
              {item.label}
            </div>
            <div
              className={`text-base font-bold font-mono ${
                item.status === "error"
                  ? "text-rose-400"
                  : item.status === "warn"
                  ? "text-amber-400"
                  : "text-white"
              }`}
            >
              {item.value}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">{item.sub}</div>
          </div>
        ))}
      </div>

      {/* Two Column Section: Frequency Distribution & Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frequency Bands */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <BarChart3 size={16} className="text-amber-400" /> Spectral Energy Distribution
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Centroid: {frequency_bands.spectral_centroid_hz.toFixed(0)} Hz
            </span>
          </div>

          <div className="space-y-3">
            {bandList.map((b, i) => {
              // Normalize -60 to -10 dB into 0 to 100%
              const pct = Math.max(5, Math.min(100, ((b.val + 60) / 50) * 100));
              return (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{b.name}</span>
                    <span className="font-mono text-slate-400">{b.val.toFixed(1)} dB</span>
                  </div>
                  <div className="w-full bg-studio-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-amber-400 h-2 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">{b.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Diagnostic Recommendations & AI Reciter Profile */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-5 shadow-lg space-y-4">
          {vocal_profile && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Sparkles size={14} className="text-amber-400" /> AI Reciter Voice Profiler
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">
                  {vocal_profile.vocal_register}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
                <div className="bg-studio-950/60 p-2 rounded-lg border border-studio-800">
                  <span className="text-[10px] text-slate-400 block">Fundamental Pitch (F0)</span>
                  <span className="text-white font-bold">{vocal_profile.estimated_f0_hz} Hz</span>
                </div>
                <div className="bg-studio-950/60 p-2 rounded-lg border border-studio-800">
                  <span className="text-[10px] text-slate-400 block">Vocal Timbre</span>
                  <span className="text-cyan-300 font-bold">{vocal_profile.vocal_timbre}</span>
                </div>
                <div className="bg-studio-950/60 p-2 rounded-lg border border-studio-800 col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-slate-400 block">Recommended Preset</span>
                  <span className="text-amber-400 font-bold capitalize">{vocal_profile.recommended_preset.replace('_', ' ')}</span>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed italic bg-studio-950/40 p-2 rounded-lg">
                &ldquo;{vocal_profile.personalized_reason}&rdquo;
              </p>
            </div>
          )}

          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <Sliders size={16} className="text-cyan-400" /> Automatic Processing Recommendations
          </h3>

          <div className="space-y-2.5">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex items-start gap-3"
              >
                <div className="mt-0.5 text-amber-400 shrink-0">
                  <CheckCircle size={15} />
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{rec}</p>
              </div>
            ))}
          </div>

          {/* Additional details */}
          <div className="pt-3 border-t border-studio-800 text-xs text-slate-400 space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span>Duration:</span>
              <span className="text-slate-200">{duration_seconds}s</span>
            </div>
            <div className="flex justify-between">
              <span>Sample Rate / Layout:</span>
              <span className="text-slate-200">{sample_rate} Hz ({channels === 1 ? "Mono" : "Stereo"})</span>
            </div>
            <div className="flex justify-between">
              <span>Silence Coverage:</span>
              <span className="text-slate-200">{silence_percentage.toFixed(1)}% ({silence_regions.length} pause segments)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
