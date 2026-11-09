"use client";

import React, { useEffect, useState } from "react";
import {
  Cpu,
  HardDrive,
  Activity,
  Layers,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Server,
  Zap,
} from "lucide-react";
import { MonitoringOverview } from "@/types";
import { getMonitoringOverview } from "@/services/api";

export const MonitoringView: React.FC = () => {
  const [data, setData] = useState<MonitoringOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      const res = await getMonitoringOverview();
      setData(res);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 4000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading || !data) {
    return <div className="text-center py-12 text-slate-400 text-sm">Gathering live system metrics...</div>;
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-studio-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity size={20} className="text-cyan-400" /> Workstation Telemetry & Hardware Engine
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time hardware utilization, DSP engine health, and local disk storage audit.
          </p>
        </div>
        <button
          onClick={fetchOverview}
          className="text-xs font-mono text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-studio-800 border border-studio-700 transition flex items-center gap-1.5"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* CPU */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>CPU Utilization</span>
            <Cpu size={16} className="text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data.system_resources.cpu_percent.toFixed(1)}%
          </div>
          <div className="w-full bg-studio-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-amber-400 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, data.system_resources.cpu_percent)}%` }}
            />
          </div>
        </div>

        {/* RAM */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>RAM Usage</span>
            <Activity size={16} className="text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data.system_resources.memory_used_mb.toFixed(0)} MB
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            {data.system_resources.memory_percent.toFixed(1)}% of {(data.system_resources.memory_total_mb / 1024).toFixed(1)} GB
          </div>
        </div>

        {/* Active Jobs */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>Active DSP Jobs</span>
            <Zap size={16} className="text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {data.active_jobs_count}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            {data.completed_jobs_count} completed • {data.failed_jobs_count} failed
          </div>
        </div>

        {/* Average Duration */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>Avg Processing Time</span>
            <Layers size={16} className="text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {(data.average_processing_duration_ms / 1000).toFixed(2)}s
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            {data.total_audio_files} files imported
          </div>
        </div>
      </div>

      {/* Grid: Audio Engine Health & Storage Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Engine Diagnostics */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <Server size={16} className="text-amber-400" /> Audio DSP Engine Subsystems
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-semibold block">Spectral Gating Noise Engine</span>
                <span className="text-slate-400 text-[11px]">Pure SciPy STFT with time-frequency soft masks</span>
              </div>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle size={14} /> Active
              </span>
            </div>

            <div className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-semibold block">DeepFilterNet Neural Adapter</span>
                <span className="text-slate-400 text-[11px]">{data.engine_status.deepfilternet_details}</span>
              </div>
              <span className={data.engine_status.deepfilternet_available ? "text-emerald-400 font-bold" : "text-slate-500 font-bold"}>
                {data.engine_status.deepfilternet_available ? "Available" : "DSP Fallback Active"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-semibold block">FFmpeg System Audio Transcoder</span>
                <span className="text-slate-400 text-[11px]">MP3 320k, FLAC, and uncompressed broadcast mastering</span>
              </div>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle size={14} /> v{data.engine_status.ffmpeg_version || "Installed"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-semibold block">Hardware Processing Target</span>
                <span className="text-slate-400 text-[11px]">Guaranteed CPU baseline with zero cloud dependencies</span>
              </div>
              <span className="text-cyan-400 font-bold">
                {data.engine_status.device_mode}
              </span>
            </div>
          </div>
        </div>

        {/* Local Storage Audit */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
            <HardDrive size={16} className="text-cyan-400" /> Local Storage Footprint
          </h3>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="flex justify-between py-1.5 border-b border-studio-800/80">
              <span className="text-slate-400">Original Vocal Recordings:</span>
              <span className="text-slate-200 font-bold">{formatBytes(data.storage_usage.originals_bytes)}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-studio-800/80">
              <span className="text-slate-400">Enhanced Mastered Audio:</span>
              <span className="text-slate-200 font-bold">{formatBytes(data.storage_usage.processed_bytes)}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-studio-800/80">
              <span className="text-slate-400">Temporary Resampling Cache:</span>
              <span className="text-slate-200 font-bold">{formatBytes(data.storage_usage.temporary_bytes)}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-studio-800/80">
              <span className="text-slate-400">SQLite Metadata Database:</span>
              <span className="text-slate-200 font-bold">{formatBytes(data.storage_usage.database_bytes)}</span>
            </div>
            <div className="flex justify-between py-2 border-t border-studio-700 text-sm font-bold">
              <span className="text-amber-400">Total AI Naat Studio Storage:</span>
              <span className="text-amber-400">{formatBytes(data.storage_usage.total_app_storage_bytes)}</span>
            </div>
            <div className="flex justify-between py-1 text-[11px] text-slate-500">
              <span>Local Drive Free Space:</span>
              <span>{formatBytes(data.storage_usage.disk_free_bytes)} of {formatBytes(data.storage_usage.disk_total_bytes)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
