"use client";

import React, { useState } from "react";
import {
  Sliders,
  Activity,
  History,
  HardDrive,
  Settings,
  Scale,
  Sparkles,
  Music,
} from "lucide-react";

import { StudioView } from "@/features/StudioView";
import { AnalysisView } from "@/features/AnalysisView";
import { EnhancementSettingsView } from "@/features/EnhancementSettingsView";
import { BeforeAfterView } from "@/features/BeforeAfterView";
import { HistoryView } from "@/features/HistoryView";
import { MonitoringView } from "@/features/MonitoringView";
import { SettingsView } from "@/features/SettingsView";
import { AudioUploadResponse, ProcessingJobResponse } from "@/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<
    "studio" | "analysis" | "settings_dsp" | "before_after" | "history" | "monitoring" | "settings_env"
  >("studio");

  const [currentAudio, setCurrentAudio] = useState<AudioUploadResponse | null>(null);
  const [activeJob, setActiveJob] = useState<ProcessingJobResponse | null>(null);
  const [preset, setPreset] = useState("studio_naat");
  const [isAutomatic, setIsAutomatic] = useState(true);
  const [overrides, setOverrides] = useState({
    noise_reduction_enabled: true,
    noise_reduction_strength: 0.75,
    noise_reduction_mode: "balanced",
    eq_intensity: 1.0,
    compression_intensity: 0.6,
    reverb_amount: 0.15,
    autotune_enabled: true,
    autotune_strength: 0.65,
    autotune_scale: "chromatic",
    echo_enabled: true,
    echo_amount: 0.15,
    echo_delay_ms: 240,
    echo_feedback: 0.28,
    tube_saturation_enabled: true,
    tube_warmth: 0.35,
    doubler_enabled: false,
    doubler_mix: 0.0,
    doubler_width: 0.8,
    target_lufs: -14.0,
    output_format: "wav",
  });

  const handleAudioUploaded = (uploaded: AudioUploadResponse) => {
    setCurrentAudio(uploaded);
    setActiveJob(null);
  };

  const handleJobCompleted = (job: ProcessingJobResponse) => {
    setActiveJob(job);
  };

  const navTabs = [
    { id: "studio", label: "Studio", icon: Music },
    { id: "analysis", label: "Audio Analysis", icon: Activity },
    { id: "settings_dsp", label: "Enhancement Settings", icon: Sliders },
    { id: "before_after", label: "Before & After", icon: Scale },
    { id: "history", label: "History", icon: History },
    { id: "monitoring", label: "Monitoring", icon: HardDrive },
    { id: "settings_env", label: "Settings", icon: Settings },
  ] as const;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500 selection:text-slate-950">
      {/* Top Application Bar */}
      <header className="border-b border-studio-800 bg-studio-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center text-slate-950 font-black shadow-md shadow-amber-500/10">
              NA
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">AI Naat Studio</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
                  v1.0 Pro
                </span>
              </div>
              <p className="text-[11px] text-slate-400 -mt-0.5 hidden sm:block">
                Professional Local-First Vocal & Recitation Enhancement
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {currentAudio && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg bg-studio-900 border border-studio-800 text-xs font-mono text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                <span className="max-w-[140px] truncate">{currentAudio.filename}</span>
                <span className="text-slate-500">({currentAudio.duration_seconds}s)</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-xs font-mono px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>100% Local</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center gap-1 overflow-x-auto scrollbar-none py-1.5 border-t border-studio-900">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                  isActive
                    ? "bg-studio-800 text-amber-400 font-bold border border-studio-700/80 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-studio-900"
                }`}
              >
                <Icon size={14} className={isActive ? "text-amber-400" : "text-slate-500"} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {activeTab === "studio" && (
          <StudioView
            onAudioUploaded={handleAudioUploaded}
            currentAudio={currentAudio}
            onJobCompleted={handleJobCompleted}
            preset={preset}
            onPresetChange={setPreset}
            overrides={overrides}
            onOverridesChange={setOverrides}
            isAutomatic={isAutomatic}
            onAutomaticToggle={setIsAutomatic}
          />
        )}

        {activeTab === "analysis" && (
          <AnalysisView analysis={currentAudio?.analysis || null} />
        )}

        {activeTab === "settings_dsp" && (
          <EnhancementSettingsView
            preset={preset}
            onPresetChange={setPreset}
            overrides={overrides}
            onOverridesChange={setOverrides}
            isAutomatic={isAutomatic}
            onAutomaticToggle={setIsAutomatic}
          />
        )}

        {activeTab === "before_after" && (
          <BeforeAfterView
            currentAudio={currentAudio}
            activeJob={activeJob}
          />
        )}

        {activeTab === "history" && <HistoryView />}

        {activeTab === "monitoring" && <MonitoringView />}

        {activeTab === "settings_env" && <SettingsView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-studio-900 bg-studio-950 py-4 text-center text-xs font-mono text-slate-500">
        AI Naat Studio • Local-First DSP Audio Architecture • Zero Remote Uploads • ITU-R BS.1770 & EBU R128 Compliant
      </footer>
    </div>
  );
}
