"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Sparkles,
  Volume2,
  ShieldCheck,
  Music2,
  Waves,
  Radio,
  Flame,
  Copy,
  Bookmark,
  Trash2,
  PlusCircle,
  Check,
} from "lucide-react";
import { ReciterProfile } from "@/types";
import { listReciterProfiles, createReciterProfile, deleteReciterProfile } from "@/services/api";

interface EnhancementSettingsProps {
  preset: string;
  onPresetChange: (preset: string) => void;
  overrides: {
    noise_reduction_enabled?: boolean;
    noise_reduction_mode?: string;
    noise_reduction_strength: number;
    eq_intensity: number;
    compression_intensity: number;
    reverb_amount: number;
    autotune_enabled?: boolean;
    autotune_strength?: number;
    autotune_scale?: string;
    echo_enabled?: boolean;
    echo_amount?: number;
    echo_delay_ms?: number;
    echo_feedback?: number;
    tube_saturation_enabled?: boolean;
    tube_warmth?: number;
    doubler_enabled?: boolean;
    doubler_mix?: number;
    doubler_width?: number;
    target_lufs: number;
    output_format: string;
  };
  onOverridesChange: (overrides: any) => void;
  isAutomatic: boolean;
  onAutomaticToggle: (auto: boolean) => void;
}

export const EnhancementSettingsView: React.FC<EnhancementSettingsProps> = ({
  preset,
  onPresetChange,
  overrides,
  onOverridesChange,
  isAutomatic,
  onAutomaticToggle,
}) => {
  const [profiles, setProfiles] = useState<ReciterProfile[]>([]);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [newProfileName, setNewProfileName] = useState("");
  const [newProfileDesc, setNewProfileDesc] = useState("");
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const res = await listReciterProfiles();
      setProfiles(res.profiles || []);
    } catch {
      // Backend not reached or offline
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProfileName.trim()) return;
    try {
      const saved = await createReciterProfile({
        name: newProfileName.trim(),
        description: newProfileDesc.trim() || "Custom personalized reciter profile",
        vocal_type: "custom",
        settings: {
          preset: "custom",
          ...overrides,
        },
      });
      setProfiles((prev) => [saved, ...prev]);
      setNewProfileName("");
      setNewProfileDesc("");
      setIsSavingProfile(false);
      setProfileMessage(`Profile '${saved.name}' saved successfully!`);
      setTimeout(() => setProfileMessage(null), 3500);
    } catch (err: any) {
      alert(err.message || "Failed to save profile");
    }
  };

  const handleDeleteProfile = async (id: string, name: string) => {
    if (!confirm(`Delete profile '${name}'?`)) return;
    try {
      await deleteReciterProfile(id);
      setProfiles((prev) => prev.filter((p) => p.id !== id));
    } catch (err: any) {
      alert(err.message || "Failed to delete profile");
    }
  };

  const handleApplyProfile = (prof: ReciterProfile) => {
    if (prof.settings) {
      onOverridesChange({
        ...overrides,
        ...prof.settings,
      });
      if (prof.settings.preset) {
        onPresetChange(prof.settings.preset);
      }
      setProfileMessage(`Applied '${prof.name}' profile!`);
      setTimeout(() => setProfileMessage(null), 3000);
    }
  };

  const presets = [
    {
      id: "studio_naat",
      name: "Studio Naat (Studio Master)",
      tag: "Pro Studio",
      desc: "Full studio-grade polish: Auto-Tune vocal pitch snapping, warm spiritual echo (240ms), 320 Hz boxiness cut, 10 kHz air sparkle, 2.8:1 compression, and broadcast loudness (-14 LUFS).",
    },
    {
      id: "natural_naat",
      name: "Natural Naat",
      tag: "Acoustic",
      desc: "Maximum transparency. Unquantized natural vocal pitch, gentle 65Hz high-pass to clear mic thumps, subtle 8% early acoustic space, and pristine consonant diction.",
    },
    {
      id: "spacious_naat",
      name: "Spacious Naat (Sanctuary)",
      tag: "Sanctuary",
      desc: "Traditional spiritual sanctuary acoustics with lush 22% diffuse tail, analog echo delay, gentle pitch stabilization, and -16.0 LUFS broadcast target.",
    },
    {
      id: "maqam_classical",
      name: "Maqam Classical (Traditional & Soulful)",
      tag: "Classical Ode",
      desc: "Classical Arabic & Urdu odes (Qasida Burda). Bayati scale snapping, warm tube saturation (45%), intimate chamber reverb, and -15.0 LUFS master.",
    },
    {
      id: "jalsa_live",
      name: "Jalsa Live Master (Mehfil & Gathering)",
      tag: "Live Mehfil",
      desc: "High-energy live performance. Aggressive downward noise gate (75%), fast vocal compression (3.4:1), lookahead peak limiter, and -13.5 LUFS loudness.",
    },
    {
      id: "modern_nasheed",
      name: "Modern Nasheed Studio (Owais & Acapella Style)",
      tag: "Acapella Studio",
      desc: "Contemporary vocal production with chromatic pitch snap, lush stereo vocal doubler (acapella chorus width), 240ms ping-pong echo, and crisp 12kHz air.",
    },
    {
      id: "deep_baritone",
      name: "Deep Baritone (Low-End Authority)",
      tag: "Baritone Reciter",
      desc: "Sub-rumble cut at 75Hz, 300Hz mud clearing, 3.5kHz articulation boost, and rich 50% warm tube saturation for commanding vocal depth.",
    },
    {
      id: "youth_vocal",
      name: "Youth Vocal (High-Register Polish)",
      tag: "High Register",
      desc: "Tailored for youthful or high-pitched reciters: 450Hz boxy cut, 220Hz fundamental warmth, harsh 4.2kHz sibilance taming, and fast smooth autotune.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-studio-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders size={20} className="text-amber-400" /> Enhancement Parameters & Presets
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Auto-Tune pitch quantization, warm tube saturation, stereo vocal doubler, spiritual echo, and studio mastering.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-studio-900 border border-studio-700/80 p-1.5 rounded-xl">
          <button
            onClick={() => onAutomaticToggle(true)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              isAutomatic
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Automatic Mode (Default)
          </button>
          <button
            onClick={() => onAutomaticToggle(false)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              !isAutomatic
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Advanced Custom Mode
          </button>
        </div>
      </div>

      {profileMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs font-mono flex items-center gap-2 animate-fade-in">
          <Check size={16} />
          <span>{profileMessage}</span>
        </div>
      )}

      {/* Preset Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Sparkles size={14} className="text-amber-400" /> Studio Vocal Master Presets
          </h3>
          <span className="text-[11px] text-slate-400 font-mono">Select a curated acoustic baseline</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {presets.map((p) => (
            <div
              key={p.id}
              onClick={() => onPresetChange(p.id)}
              className={`p-4 rounded-2xl border cursor-pointer transition flex flex-col justify-between ${
                preset === p.id
                  ? "bg-amber-500/10 border-amber-500/60 shadow-lg"
                  : "bg-studio-900 border-studio-800 hover:border-studio-700"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white text-sm">{p.name}</span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                      preset === p.id ? "bg-amber-500 text-slate-950" : "bg-studio-800 text-slate-400"
                    }`}
                  >
                    {p.tag}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">{p.desc}</p>
              </div>
              <div className="mt-3 pt-2.5 border-t border-studio-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>Status:</span>
                <span className={preset === p.id ? "text-amber-400 font-semibold" : "text-slate-400"}>
                  {preset === p.id ? "Active Selected" : "Click to Select"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Personalized Reciter Profiles Section */}
      <div className="bg-studio-900 border border-studio-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between border-b border-studio-800 pb-3">
          <div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Bookmark size={16} className="text-amber-400" /> Personalized Reciter Profiles
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Save and load custom personalized settings tailored to your specific vocal register.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsSavingProfile(!isSavingProfile)}
            className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow"
          >
            <PlusCircle size={14} />
            <span>Save Current as My Profile</span>
          </button>
        </div>

        {/* Modal/Form to save profile */}
        {isSavingProfile && (
          <form onSubmit={handleSaveProfile} className="p-4 rounded-xl bg-studio-850 border border-studio-750 space-y-3">
            <h4 className="text-xs font-bold text-white uppercase font-mono">Create New Reciter Profile</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Profile Name (e.g. My Studio Signature Voice)"
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                required
                className="bg-studio-950 border border-studio-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
              <input
                type="text"
                placeholder="Description or notes (optional)"
                value={newProfileDesc}
                onChange={(e) => setNewProfileDesc(e.target.value)}
                className="bg-studio-950 border border-studio-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setIsSavingProfile(false)}
                className="px-3 py-1 rounded-lg text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 shadow"
              >
                Save Profile
              </button>
            </div>
          </form>
        )}

        {/* Profiles List */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {profiles.map((prof) => (
            <div
              key={prof.id}
              className="p-3 rounded-xl bg-studio-850 border border-studio-800 flex flex-col justify-between hover:border-studio-700 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">{prof.name}</span>
                  {prof.is_builtin ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-studio-800 text-slate-400">Built-in</span>
                  ) : (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">Personalized</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {prof.description}
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-studio-800/80 flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => handleApplyProfile(prof)}
                  className="text-amber-400 hover:text-amber-300 font-semibold font-mono text-[11px]"
                >
                  Apply Profile →
                </button>
                {!prof.is_builtin && (
                  <button
                    type="button"
                    onClick={() => handleDeleteProfile(prof.id, prof.name)}
                    className="text-slate-500 hover:text-rose-400 transition"
                    title="Delete custom profile"
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Advanced Overrides Panel */}
      <div
        className={`bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-lg space-y-6 transition ${
          isAutomatic ? "opacity-60 pointer-events-none" : "opacity-100"
        }`}
      >
        <div className="flex items-center justify-between border-b border-studio-800 pb-3">
          <div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
              Advanced DSP Parameter Overrides
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Fine-tune Auto-Tune, Warm Tube Saturation, Stereo Vocal Doubler, Echo, and mastering targets.
            </p>
          </div>
          {isAutomatic && (
            <span className="text-xs text-amber-400 font-mono">
              Switch to &apos;Advanced Custom Mode&apos; above to edit
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Auto-Tune Pitch Correction */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Music2 size={14} className="text-amber-400" /> Auto-Tune Pitch Correction
              </span>
              <span className="text-amber-400 font-bold">
                {((overrides.autotune_strength ?? 0.65) * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overrides.autotune_strength ?? 0.65}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  autotune_enabled: parseFloat(e.target.value) > 0.05,
                  autotune_strength: parseFloat(e.target.value),
                })
              }
              className="w-full accent-amber-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="pt-1">
              <label className="text-[10px] font-mono text-slate-400 block mb-1">Scale Quantization</label>
              <select
                value={overrides.autotune_scale ?? "chromatic"}
                onChange={(e) =>
                  onOverridesChange({
                    ...overrides,
                    autotune_scale: e.target.value,
                  })
                }
                className="w-full bg-studio-800 border border-studio-700 rounded-lg px-2.5 py-1 text-xs text-white font-mono focus:outline-none focus:border-amber-500"
              >
                <option value="chromatic">Chromatic (All Notes - Universal)</option>
                <option value="hijaz">Maqam Hijaz (Traditional Islamic Naat)</option>
                <option value="bayati">Maqam Bayati (Spiritual Arabic Cadence)</option>
                <option value="minor">Natural Minor</option>
                <option value="major">Major</option>
              </select>
            </div>
          </div>

          {/* Warm Tube & Tape Saturation */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Flame size={14} className="text-orange-400" /> Warm Tube Saturation
              </span>
              <span className="text-orange-400 font-bold">
                {((overrides.tube_warmth ?? 0.35) * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overrides.tube_warmth ?? 0.35}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  tube_saturation_enabled: parseFloat(e.target.value) > 0.02,
                  tube_warmth: parseFloat(e.target.value),
                })
              }
              className="w-full accent-orange-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>Adds 2nd-order harmonic body</span>
              <span>Triode Tube Mode</span>
            </div>
          </div>

          {/* Stereo Vocal Doubler / Acapella Harmony */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Copy size={14} className="text-purple-400" /> Stereo Vocal Doubler
              </span>
              <span className="text-purple-400 font-bold">
                {((overrides.doubler_mix ?? 0.0) * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="0.5"
              step="0.02"
              value={overrides.doubler_mix ?? 0.0}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  doubler_enabled: parseFloat(e.target.value) > 0.02,
                  doubler_mix: parseFloat(e.target.value),
                })
              }
              className="w-full accent-purple-400 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>Acapella Chorus Width</span>
              <span>{((overrides.doubler_width ?? 0.8) * 100).toFixed(0)}% Width</span>
            </div>
          </div>

          {/* Studio Vocal Echo / Delay */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Radio size={14} className="text-cyan-400" /> Studio Vocal Echo
              </span>
              <span className="text-cyan-400 font-bold">
                {((overrides.echo_amount ?? 0.15) * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="0.4"
              step="0.02"
              value={overrides.echo_amount ?? 0.15}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  echo_enabled: parseFloat(e.target.value) > 0.01,
                  echo_amount: parseFloat(e.target.value),
                })
              }
              className="w-full accent-cyan-400 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>Delay: {overrides.echo_delay_ms ?? 240}ms</span>
              <span>Feedback: {(((overrides.echo_feedback ?? 0.28)) * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Background Noise Suppression */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Waves size={14} className="text-emerald-400" /> Background Noise Removal
              </span>
              <span className="text-emerald-400 font-bold">
                {overrides.noise_reduction_enabled !== false
                  ? `${((overrides.noise_reduction_strength ?? 0.75) * 100).toFixed(0)}%`
                  : "OFF"}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overrides.noise_reduction_strength ?? 0.75}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  noise_reduction_enabled: true,
                  noise_reduction_strength: parseFloat(e.target.value),
                })
              }
              className="w-full accent-emerald-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="grid grid-cols-3 gap-1.5 pt-1 text-[10px] font-mono">
              {["maximum", "balanced", "subtle"].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() =>
                    onOverridesChange({
                      ...overrides,
                      noise_reduction_enabled: true,
                      noise_reduction_mode: m,
                      noise_reduction_strength: m === "maximum" ? 0.90 : m === "balanced" ? 0.75 : 0.45,
                    })
                  }
                  className={`py-1 rounded text-center transition capitalize font-semibold ${
                    (overrides.noise_reduction_mode ?? "balanced") === m
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-studio-800 text-slate-400 hover:text-white"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Compression */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-indigo-400" /> Dynamic Compression
              </span>
              <span className="text-indigo-400 font-bold">
                {(overrides.compression_intensity * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overrides.compression_intensity}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  compression_intensity: parseFloat(e.target.value),
                })
              }
              className="w-full accent-indigo-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>Soft-knee vocal leveling</span>
              <span>Transparent</span>
            </div>
          </div>

          {/* Spiritual Reverb */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold flex items-center gap-1.5">
                <Volume2 size={14} className="text-sky-400" /> Spiritual Reverb
              </span>
              <span className="text-sky-400 font-bold">
                {(overrides.reverb_amount * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overrides.reverb_amount}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  reverb_amount: parseFloat(e.target.value),
                })
              }
              className="w-full accent-sky-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>Moorer Algorithmic Model</span>
              <span>Sanctuary Space</span>
            </div>
          </div>

          {/* Master Loudness Target */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 font-bold">Output Loudness Target</span>
              <span className="text-amber-400 font-bold">{overrides.target_lufs.toFixed(1)} LUFS</span>
            </div>
            <input
              type="range"
              min="-24"
              max="-10"
              step="0.5"
              value={overrides.target_lufs}
              onChange={(e) =>
                onOverridesChange({
                  ...overrides,
                  target_lufs: parseFloat(e.target.value),
                })
              }
              className="w-full accent-amber-500 h-2 bg-studio-800 rounded-lg cursor-pointer"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
              <span>-16 (Acoustic)</span>
              <span>-14 (Broadcast Master)</span>
              <span>-12 (Loud)</span>
            </div>
          </div>

          {/* Export Output Format */}
          <div className="space-y-2 p-3.5 rounded-xl bg-studio-850 border border-studio-800">
            <label className="text-xs font-mono text-slate-200 font-bold block">Master Export Format</label>
            <div className="grid grid-cols-3 gap-2 pt-1">
              {["wav", "mp3", "flac"].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => onOverridesChange({ ...overrides, output_format: fmt })}
                  className={`py-1.5 rounded-lg text-xs font-mono font-bold uppercase transition ${
                    overrides.output_format === fmt
                      ? "bg-amber-500 text-slate-950 shadow"
                      : "bg-studio-800 text-slate-400 hover:text-white"
                  }`}
                >
                  {fmt}
                </button>
              ))}
            </div>
            <span className="text-[10px] font-mono text-slate-400 block pt-1">
              {overrides.output_format === "wav"
                ? "24-bit PCM Lossless Broadcast WAV"
                : overrides.output_format === "mp3"
                ? "320 kbps CBR High-Quality MP3"
                : "Free Lossless Audio Codec (FLAC)"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
