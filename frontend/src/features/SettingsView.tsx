"use client";

import React, { useEffect, useState } from "react";
import { Settings, Trash2, CheckCircle2, AlertTriangle, ShieldAlert } from "lucide-react";
import { StudioSettings } from "@/types";
import { getStudioSettings, updateStudioSettings, clearAllStudioData } from "@/services/api";

export const SettingsView: React.FC = () => {
  const [settings, setSettings] = useState<StudioSettings | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [clearMessage, setClearMessage] = useState<string | null>(null);

  useEffect(() => {
    getStudioSettings().then(setSettings).catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateStudioSettings(settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch {
      // ignore
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearAll = async () => {
    try {
      const res = await clearAllStudioData();
      setClearMessage(res.message);
      setConfirmClear(false);
      setTimeout(() => setClearMessage(null), 4000);
    } catch {
      setClearMessage("Failed to clear studio data.");
    }
  };

  if (!settings) {
    return <div className="text-center py-12 text-slate-400 text-sm">Loading workstation configuration...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="border-b border-studio-800 pb-5">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Settings size={20} className="text-amber-400" /> Workstation Configuration & Privacy
        </h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Local engine parameters, processing preferences, and data privacy controls.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>Configuration saved successfully.</span>
        </div>
      )}

      {clearMessage && (
        <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 size={16} className="text-cyan-400" />
          <span>{clearMessage}</span>
        </div>
      )}

      {/* Settings Form */}
      <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl space-y-6">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
          Engine Environment Settings
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">
              Maximum Upload Limit (MB)
            </label>
            <input
              type="number"
              min="10"
              max="500"
              value={settings.max_upload_size_mb}
              onChange={(e) =>
                setSettings({ ...settings, max_upload_size_mb: parseInt(e.target.value) || 100 })
              }
              className="w-full bg-studio-800 border border-studio-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
            />
            <p className="text-[10px] text-slate-500">Maximum uncompressed audio file size permitted for upload.</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">
              Default Master Output Format
            </label>
            <select
              value={settings.default_sample_rate}
              onChange={(e) =>
                setSettings({ ...settings, default_sample_rate: parseInt(e.target.value) || 44100 })
              }
              className="w-full bg-studio-800 border border-studio-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
            >
              <option value="44100">44,100 Hz (CD Standard)</option>
              <option value="48000">48,000 Hz (Broadcast / Video)</option>
              <option value="96000">96,000 Hz (High Resolution)</option>
            </select>
            <p className="text-[10px] text-slate-500">Target sample rate for final export.</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">
              Temporary Cache Retention (Hours)
            </label>
            <input
              type="number"
              min="1"
              max="168"
              value={settings.temp_retention_hours}
              onChange={(e) =>
                setSettings({ ...settings, temp_retention_hours: parseInt(e.target.value) || 24 })
              }
              className="w-full bg-studio-800 border border-studio-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
            />
            <p className="text-[10px] text-slate-500">Retention period before temporary resampled chunks are recycled.</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">
              Noise Reduction Engine Mode
            </label>
            <select
              value={settings.active_noise_reducer}
              onChange={(e) =>
                setSettings({ ...settings, active_noise_reducer: e.target.value })
              }
              className="w-full bg-studio-800 border border-studio-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-amber-500"
            >
              <option value="auto">Auto (DeepFilterNet if available, else Spectral Gating)</option>
              <option value="spectral_gating">Spectral Gating (Pure DSP - High Fidelity)</option>
              <option value="passthrough">Passthrough (Bypass Noise Suppression)</option>
            </select>
            <p className="text-[10px] text-slate-500">Active interchangeable model adapter.</p>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition shadow-lg"
        >
          {isSaving ? "Saving..." : "Save Settings"}
        </button>
      </div>

      {/* Danger Zone: Clear Session Data */}
      <div className="bg-studio-900 border border-rose-500/30 rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-sm font-semibold text-rose-400 uppercase tracking-wider font-mono flex items-center gap-2">
          <ShieldAlert size={16} /> Privacy & Local Data Purge
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          Permanent removal of all original vocal audio recordings, enhanced exports, job logs, and database rows.
          Processing operates 100% locally on your computer with no external uploads; this command wipes all local session records completely.
        </p>

        {!confirmClear ? (
          <button
            onClick={() => setConfirmClear(true)}
            className="px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500 hover:text-white text-xs font-bold transition flex items-center gap-2"
          >
            <Trash2 size={14} /> Clear All Session Data
          </button>
        ) : (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 space-y-3">
            <div className="text-xs font-bold text-rose-300 flex items-center gap-2">
              <AlertTriangle size={16} className="text-rose-400" />
              <span>Are you sure? This action is permanent and cannot be undone.</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleClearAll}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition"
              >
                Yes, Permanently Delete All
              </button>
              <button
                onClick={() => setConfirmClear(false)}
                className="px-4 py-1.5 rounded-lg bg-studio-800 text-slate-300 hover:text-white text-xs transition"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
