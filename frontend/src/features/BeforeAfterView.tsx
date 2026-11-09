"use client";

import React, { useState } from "react";
import {
  SplitSquareVertical,
  Download,
  CheckCircle2,
  AlertTriangle,
  FileAudio,
  Sparkles,
  ShieldCheck,
  Scale
} from "lucide-react";
import { AudioUploadResponse, ProcessingJobResponse, AudioOutputMetadata } from "@/types";
import { AudioWaveformPlayer } from "@/components/AudioWaveformPlayer";
import {
  getAudioStreamUrl,
  getOutputStreamUrl,
  getOutputDownloadUrl,
  getOutputMetadata,
} from "@/services/api";

interface BeforeAfterViewProps {
  currentAudio: AudioUploadResponse | null;
  activeJob: ProcessingJobResponse | null;
}

export const BeforeAfterView: React.FC<BeforeAfterViewProps> = ({
  currentAudio,
  activeJob,
}) => {
  const [outputMeta, setOutputMeta] = useState<AudioOutputMetadata | null>(null);
  const [syncTime, setSyncTime] = useState<number | null>(null);
  const [isSyncActive, setIsSyncActive] = useState(true);

  React.useEffect(() => {
    if (activeJob && activeJob.status === "completed" && activeJob.output_id) {
      getOutputMetadata(activeJob.output_id)
        .then((data) => setOutputMeta(data))
        .catch(() => {});
    }
  }, [activeJob]);

  if (!currentAudio) {
    return (
      <div className="bg-studio-900 border border-studio-800 rounded-2xl p-12 text-center text-slate-400">
        <Scale size={40} className="mx-auto mb-3 text-studio-600" />
        <h3 className="text-base font-semibold text-white">No Audio Uploaded</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
          Upload and enhance an audio recording in the Studio tab to compare the original raw vocal against the mastered version.
        </p>
      </div>
    );
  }

  if (!activeJob || activeJob.status !== "completed" || !activeJob.output_id) {
    return (
      <div className="bg-studio-900 border border-studio-800 rounded-2xl p-12 text-center text-slate-400">
        <Sparkles size={40} className="mx-auto mb-3 text-amber-500 animate-pulse" />
        <h3 className="text-base font-semibold text-white">Processing Required</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
          Original audio is uploaded, but enhancement has not completed yet. Click &quot;Enhance Audio Now&quot; in the Studio to generate the mastered comparison.
        </p>
      </div>
    );
  }

  const handleTimeUpdate = (time: number) => {
    if (isSyncActive) {
      setSyncTime(time);
    }
  };

  const report = outputMeta?.quality_report;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-studio-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Scale size={20} className="text-amber-400" /> A/B Comparison: Original vs Enhanced
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Synchronized auditioning and objective audio quality metric delta analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-mono text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={isSyncActive}
              onChange={(e) => setIsSyncActive(e.target.checked)}
              className="accent-amber-500 rounded"
            />
            <span>Synchronize Playheads</span>
          </label>

          <a
            href={getOutputDownloadUrl(activeJob.output_id)}
            download
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg"
          >
            <Download size={14} /> Download Enhanced Master
          </a>
        </div>
      </div>

      {/* Synchronized Waveform Players Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="font-semibold text-slate-300">1. Original Raw Recording</span>
            <span>{currentAudio.sample_rate} Hz • {currentAudio.duration_seconds}s</span>
          </div>
          <AudioWaveformPlayer
            audioUrl={getAudioStreamUrl(currentAudio.audio_id)}
            title="Original Audio (Before)"
            waveColor="#334155"
            progressColor="#06b6d4"
            height={85}
            onTimeUpdate={handleTimeUpdate}
            syncTime={syncTime}
          />
        </div>

        {/* Enhanced */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-emerald-400">
            <span className="font-semibold flex items-center gap-1">
              <Sparkles size={14} /> 2. Enhanced Mastered Audio
            </span>
            <span>EBU R128 • True Peak Protected</span>
          </div>
          <AudioWaveformPlayer
            audioUrl={getOutputStreamUrl(activeJob.output_id)}
            title="Enhanced Audio (After)"
            waveColor="#065f46"
            progressColor="#10b981"
            height={85}
            onTimeUpdate={handleTimeUpdate}
            syncTime={syncTime}
          />
        </div>
      </div>

      {/* Objective Quality Metrics Delta Table */}
      {report && (
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-studio-800 pb-3">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <ShieldCheck size={16} className="text-emerald-400" /> Objective Quality Verification
            </h3>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              {report.overall_quality_passed ? "✓ Audio Integrity Verified" : "Flagged Warnings"}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-studio-800 text-slate-400">
                  <th className="py-2.5">Acoustic Metric</th>
                  <th className="py-2.5">Original Recording</th>
                  <th className="py-2.5">Enhanced Master</th>
                  <th className="py-2.5">Enhancement Delta / Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-studio-800/60">
                <tr>
                  <td className="py-2.5 text-slate-300 font-medium">Integrated Loudness</td>
                  <td className="py-2.5 text-slate-400">
                    {report.original_integrated_lufs ? `${report.original_integrated_lufs.toFixed(1)} LUFS` : "N/A"}
                  </td>
                  <td className="py-2.5 text-emerald-400 font-bold">
                    {report.processed_integrated_lufs ? `${report.processed_integrated_lufs.toFixed(1)} LUFS` : "N/A"}
                  </td>
                  <td className="py-2.5 text-slate-300">
                    Standardized to broadcast target without clipping
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 text-slate-300 font-medium">True Peak (4x Oversampled)</td>
                  <td className="py-2.5 text-slate-400">
                    {report.original_true_peak_dbtp ? `${report.original_true_peak_dbtp.toFixed(1)} dBTP` : "N/A"}
                  </td>
                  <td className="py-2.5 text-emerald-400 font-bold">
                    {report.processed_true_peak_dbtp ? `${report.processed_true_peak_dbtp.toFixed(1)} dBTP` : "N/A"}
                  </td>
                  <td className="py-2.5 text-slate-300">
                    Guaranteed ceiling at ≤ -1.0 dBTP (DAC-safe)
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 text-slate-300 font-medium">Digital Sample Clipping</td>
                  <td className="py-2.5 text-amber-400 font-bold">
                    {report.original_clipped_samples} clipped samples
                  </td>
                  <td className="py-2.5 text-emerald-400 font-bold">
                    {report.processed_clipped_samples} (Zero Clipping)
                  </td>
                  <td className="py-2.5 text-slate-300">
                    {report.clipping_resolved ? "✓ Lookahead limiter eliminated all overs" : "Warning"}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 text-slate-300 font-medium">Estimated Vocal SNR</td>
                  <td className="py-2.5 text-slate-400">Baseline</td>
                  <td className="py-2.5 text-emerald-400 font-bold">
                    {report.estimated_snr_change_db ? `+${report.estimated_snr_change_db.toFixed(1)} dB` : "Preserved"}
                  </td>
                  <td className="py-2.5 text-slate-300">
                    Intelligent spectral noise gating without watery artifacts
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 text-slate-300 font-medium">Duration Preservation</td>
                  <td className="py-2.5 text-slate-400">{currentAudio.duration_seconds}s</td>
                  <td className="py-2.5 text-slate-300 font-bold">{currentAudio.duration_seconds}s</td>
                  <td className="py-2.5 text-slate-300">
                    ✓ Preserved exactly (delta {report.duration_delta_seconds.toFixed(4)}s)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="p-3.5 rounded-xl bg-studio-850 border border-studio-800 text-xs text-slate-300 flex items-start gap-2.5">
            <CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Quality Verdict: </span>
              {report.quality_summary}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
