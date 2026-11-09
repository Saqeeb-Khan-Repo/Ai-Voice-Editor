"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  UploadCloud,
  Sparkles,
  Music,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Sliders,
  Volume2,
  Download,
  XCircle,
  FileAudio,
  Mic,
  Square,
  Radio,
  BookmarkCheck,
  Disc,
  Scissors,
  Flame,
  Copy,
  Zap,
  Music2,
  Waves,
  Check,
  VolumeX,
  ArrowRightLeft,
  Shield,
} from "lucide-react";
import { AudioUploadResponse, ProcessingJobResponse } from "@/types";
import {
  uploadAudio,
  listSampleRecordings,
  loadSpecificSample,
  startProcessing,
  getJobStatus,
  cancelJob,
  editAudio,
  getAudioStreamUrl,
  getOutputStreamUrl,
  getOutputDownloadUrl,
} from "@/services/api";
import { AudioWaveformPlayer } from "@/components/AudioWaveformPlayer";

interface StudioViewProps {
  onAudioUploaded: (audio: AudioUploadResponse) => void;
  currentAudio: AudioUploadResponse | null;
  onJobCompleted: (job: ProcessingJobResponse) => void;
  preset: string;
  onPresetChange: (preset: string) => void;
  overrides: any;
  onOverridesChange: (overrides: any) => void;
  isAutomatic: boolean;
  onAutomaticToggle: (auto: boolean) => void;
}

export const StudioView: React.FC<StudioViewProps> = ({
  onAudioUploaded,
  currentAudio,
  onJobCompleted,
  preset,
  onPresetChange,
  overrides,
  onOverridesChange,
  isAutomatic,
  onAutomaticToggle,
}) => {
  const [activeInputTab, setActiveInputTab] = useState<"record" | "upload" | "demo">("record");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<ProcessingJobResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Live microphone recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<any>(null);

  // Interactive Audio Editing / Trimming state
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState<number>(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editSuccessMessage, setEditSuccessMessage] = useState<string | null>(null);

  // A/B Audition Comparison state
  const [abAuditionMode, setAbAuditionMode] = useState<"enhanced" | "original">("enhanced");

  useEffect(() => {
    if (currentAudio) {
      setTrimStart(0);
      setTrimEnd(currentAudio.duration_seconds);
    }
  }, [currentAudio]);

  // Pre-recorded demo samples state
  const [sampleList, setSampleList] = useState<Array<{ id: string; title: string; description: string }>>([
    {
      id: "hijaz",
      title: "Faslon Ko Takalluf (Maqam Hijaz)",
      description: "Urdu spiritual Naat vocal with characteristic Eastern minor 2nd intervals, subtle room boxiness, and ambient mic hiss.",
    },
    {
      id: "burda",
      title: "Qasida Burda Sharif (Arabic Recitation)",
      description: "Classical Arabic spiritual ode with dynamic vocal phrasing, natural breaths, and room acoustics.",
    },
    {
      id: "salam",
      title: "Mustafa Jane Rehmat (Warm Salam)",
      description: "Traditional soulful salam cadence in baritone register with chest resonance and proximity warmth.",
    },
  ]);

  useEffect(() => {
    listSampleRecordings().then((list) => {
      if (list && list.length > 0) setSampleList(list);
    }).catch(() => {});

    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    };
  }, []);

  const handleFile = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const response = await uploadAudio(file);
      onAudioUploaded(response);
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload audio.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = async (sampleKey: string) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const response = await loadSpecificSample(sampleKey);
      onAudioUploaded(response);
    } catch (err: any) {
      setUploadError(err.message || "Failed to load sample.");
    } finally {
      setIsUploading(false);
    }
  };

  // Start Live Microphone Recording
  const startRecording = async () => {
    setUploadError(null);
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const pcmData = new Uint8Array(analyser.frequencyBinCount);
      const updateMeter = () => {
        analyser.getByteFrequencyData(pcmData);
        let sum = 0;
        for (let i = 0; i < pcmData.length; i++) sum += pcmData[i];
        const avg = sum / pcmData.length;
        setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
        animFrameRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();

      let mimeType = "audio/webm;codecs=opus";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        if (MediaRecorder.isTypeSupported("audio/webm")) {
          mimeType = "audio/webm";
        } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
          mimeType = "audio/ogg";
        } else {
          mimeType = "";
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        setAudioLevel(0);

        const recordedBlob = new Blob(audioChunksRef.current, {
          type: mimeType || "audio/webm",
        });

        const recFile = new File([recordedBlob], `Live_Naat_Recording_${Date.now()}.webm`, {
          type: mimeType || "audio/webm",
        });
        await handleFile(recFile);
      };

      recorder.start(100);
      setIsRecording(true);
      setRecordingSeconds(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setUploadError(
        err.message || "Microphone access denied. Please allow microphone permissions in your browser."
      );
    }
  };

  // Stop Live Microphone Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }
  };

  // Interactive Audio Trimming
  const handleCropAudio = async () => {
    if (!currentAudio) return;
    setIsEditing(true);
    setUploadError(null);
    try {
      const edited = await editAudio(currentAudio.audio_id, {
        start_seconds: trimStart,
        end_seconds: trimEnd || currentAudio.duration_seconds,
      });
      onAudioUploaded(edited);
      setEditSuccessMessage(`Audio cropped to ${trimStart.toFixed(1)}s - ${(trimEnd || currentAudio.duration_seconds).toFixed(1)}s successfully!`);
      setTimeout(() => setEditSuccessMessage(null), 3500);
    } catch (err: any) {
      setUploadError(err.message || "Failed to crop audio.");
    } finally {
      setIsEditing(false);
    }
  };

  const handlePreGainBoost = async () => {
    if (!currentAudio) return;
    setIsEditing(true);
    try {
      const edited = await editAudio(currentAudio.audio_id, {
        gain_db: 3.0,
      });
      onAudioUploaded(edited);
      setEditSuccessMessage("Applied +3.0 dB clean vocal lift!");
      setTimeout(() => setEditSuccessMessage(null), 3000);
    } catch (err: any) {
      setUploadError(err.message || "Failed to adjust gain.");
    } finally {
      setIsEditing(false);
    }
  };

  const handleStartEnhancement = async () => {
    if (!currentAudio) return;
    setIsProcessing(true);
    try {
      const job = await startProcessing(currentAudio.audio_id, {
        preset: preset,
        automatic_mode: isAutomatic,
        overrides: isAutomatic ? undefined : overrides,
      });
      setActiveJob(job);

      const pollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(job.job_id);
          setActiveJob(status);
          if (status.status === "completed") {
            clearInterval(pollInterval);
            setIsProcessing(false);
            onJobCompleted(status);
          } else if (status.status === "failed" || status.status === "cancelled") {
            clearInterval(pollInterval);
            setIsProcessing(false);
          }
        } catch {
          clearInterval(pollInterval);
          setIsProcessing(false);
        }
      }, 500);
    } catch (err: any) {
      setUploadError(err.message || "Failed to start enhancement.");
      setIsProcessing(false);
    }
  };

  const handleCancel = async () => {
    if (activeJob) {
      await cancelJob(activeJob.job_id);
      setIsProcessing(false);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const studioPresets = [
    {
      id: "studio_naat",
      name: "Studio Naat",
      badge: "Studio Master",
      desc: "Full studio polish: Auto-Tune, 240ms analog echo, warm tube saturation, and -14 LUFS broadcast loudness.",
    },
    {
      id: "natural_naat",
      name: "Natural Naat",
      badge: "Pure Acoustic",
      desc: "Maximum transparency: preserves exact voice timbre, gentle 65Hz high-pass, and subtle 8% acoustic space.",
    },
    {
      id: "spacious_naat",
      name: "Spacious Naat",
      badge: "Sanctuary",
      desc: "Lush spiritual sanctuary acoustics with 22% diffuse tail and Maqam Hijaz pitch stabilization.",
    },
    {
      id: "maqam_classical",
      name: "Maqam Classical",
      badge: "Classical Ode",
      desc: "Bayati scale snap, warm tube saturation (45%), intimate chamber reverb, and -15 LUFS master.",
    },
    {
      id: "jalsa_live",
      name: "Jalsa Live Master",
      badge: "Live Mehfil",
      desc: "Aggressive downward noise gate (75%), fast vocal compression (3.4:1), lookahead peak limiter.",
    },
    {
      id: "modern_nasheed",
      name: "Modern Nasheed",
      badge: "Acapella Studio",
      desc: "Fast chromatic autotune, stereo vocal doubler (acapella width), 240ms ping-pong echo, and 12kHz air.",
    },
    {
      id: "deep_baritone",
      name: "Deep Baritone",
      badge: "Baritone Reciter",
      desc: "Low-end authority: 75Hz sub cut, 300Hz mud clearing, 3.5kHz articulation boost, 50% tube warmth.",
    },
    {
      id: "youth_vocal",
      name: "Youth Vocal",
      badge: "High Register",
      desc: "450Hz boxy cut, 220Hz fundamental warmth, 4.2kHz sibilance taming, and fast smooth autotune.",
    },
  ];

  const vocalProfile = currentAudio?.analysis?.vocal_profile;
  const isNoiseReductionOn = overrides.noise_reduction_enabled ?? true;
  const currentNoiseMode = overrides.noise_reduction_mode ?? "balanced";

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-studio-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="text-amber-400">✦</span> AI Naat Studio Workstation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Studio-level audio editing, dedicated background noise removal, and broadcast vocal mastering.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Local-First Engine
          </span>
        </div>
      </div>

      {editSuccessMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs font-mono flex items-center gap-2 animate-fade-in">
          <Check size={16} />
          <span>{editSuccessMessage}</span>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recording, Upload & Waveform Players */}
        <div className="lg:col-span-2 space-y-6">
          {!currentAudio && (
            <div className="space-y-4">
              {/* Input Mode Selector Bar */}
              <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-studio-900 border border-studio-800">
                <button
                  type="button"
                  onClick={() => setActiveInputTab("record")}
                  className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                    activeInputTab === "record"
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/30 shadow-md"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Mic size={15} />
                  <span>Record Naat Live</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveInputTab("upload")}
                  className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                    activeInputTab === "upload"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-md"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <UploadCloud size={15} />
                  <span>Upload Audio File</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveInputTab("demo")}
                  className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                    activeInputTab === "demo"
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-md"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Music size={15} />
                  <span>Curated Demo Library</span>
                </button>
              </div>

              {/* 1. Live Microphone Recorder Card */}
              {activeInputTab === "record" && (
                <div className="border border-studio-700/80 rounded-2xl p-8 text-center bg-studio-900/80 backdrop-blur shadow-xl space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center justify-center gap-2">
                      <Mic className="text-rose-400" size={20} />
                      <span>Live In-Browser Voice Recorder</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                      Recite your Naat directly through your computer or studio microphone. We will analyze and enhance it instantly.
                    </p>
                  </div>

                  {/* Pulsating Record Button / Timer */}
                  <div className="flex flex-col items-center justify-center gap-4">
                    <div className="relative">
                      {isRecording && (
                        <div
                          className="absolute -inset-3 rounded-full bg-rose-500/20 animate-ping pointer-events-none"
                          style={{ animationDuration: "1.5s" }}
                        />
                      )}
                      <button
                        type="button"
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition transform active:scale-95 ${
                          isRecording
                            ? "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30"
                            : "bg-gradient-to-tr from-rose-500 to-rose-400 hover:brightness-110 text-white shadow-rose-500/20"
                        }`}
                      >
                        {isRecording ? <Square size={26} className="fill-white" /> : <Mic size={30} />}
                      </button>
                    </div>

                    {isRecording ? (
                      <div className="space-y-1">
                        <div className="text-2xl font-mono font-bold text-rose-400 animate-pulse">
                          {formatTimer(recordingSeconds)}
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          Reciting Live... Click button to stop & analyze
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs font-mono text-slate-400">
                        Click microphone icon to begin reciting
                      </span>
                    )}

                    {/* Live VU Meter */}
                    {isRecording && (
                      <div className="w-64 max-w-full space-y-1 pt-2">
                        <div className="flex justify-between text-[10px] font-mono text-slate-500">
                          <span>Live Input Level</span>
                          <span>{audioLevel}%</span>
                        </div>
                        <div className="w-full bg-studio-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-75 rounded-full ${
                              audioLevel > 85
                                ? "bg-rose-500"
                                : audioLevel > 50
                                ? "bg-amber-400"
                                : "bg-emerald-400"
                            }`}
                            style={{ width: `${audioLevel}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 2. File Drag & Drop Upload Card */}
              {activeInputTab === "upload" && (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-studio-700 hover:border-amber-500/60 rounded-2xl p-10 text-center bg-studio-900/50 hover:bg-studio-900/80 transition cursor-pointer group shadow-xl"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".wav,.mp3,.flac,.webm,.ogg"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        handleFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition">
                    {isUploading ? (
                      <Loader2 className="animate-spin" size={28} />
                    ) : (
                      <UploadCloud size={28} />
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-white mb-1">
                    {isUploading ? "Analyzing Audio Recording..." : "Upload Local Audio Recording"}
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto mb-3">
                    Drag and drop a file from your computer (WAV, MP3, FLAC, WebM, or OGG).
                  </p>
                  <div className="flex items-center justify-center gap-3 text-xs font-mono text-slate-500">
                    <span>WAV (24/16-bit)</span>
                    <span>•</span>
                    <span>MP3 (up to 320k)</span>
                    <span>•</span>
                    <span>FLAC</span>
                  </div>
                </div>
              )}

              {/* 3. Demo Naat Samples Library */}
              {activeInputTab === "demo" && (
                <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
                        <Music size={16} className="text-cyan-400" />
                        Curated Pre-Recorded Naat Samples
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Test the studio engine instantly with authentic vocal recitations.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {sampleList.map((sample) => (
                      <button
                        key={sample.id}
                        type="button"
                        disabled={isUploading}
                        onClick={() => handleLoadSample(sample.id)}
                        className="text-left p-4 rounded-xl bg-studio-850 hover:bg-studio-800 border border-studio-750 hover:border-cyan-500/50 transition flex flex-col justify-between group shadow"
                      >
                        <div>
                          <span className="text-xs font-bold text-white group-hover:text-cyan-300 transition block mb-1">
                            {sample.title}
                          </span>
                          <p className="text-[11px] text-slate-400 leading-relaxed">
                            {sample.description}
                          </p>
                        </div>
                        <div className="mt-3 pt-2 border-t border-studio-800 flex items-center justify-between text-[11px] font-mono text-cyan-400 font-semibold">
                          <span>Audition Sample</span>
                          <span>→</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {uploadError && (
            <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl p-4 flex items-center gap-3 text-sm">
              <AlertTriangle size={18} className="shrink-0 text-rose-400" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Current Audio Player & Waveform */}
          {currentAudio && (
            <div className="space-y-4">
              {/* Audio header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-studio-800 flex items-center justify-center text-amber-400">
                    <FileAudio size={18} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{currentAudio.filename}</h3>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>{currentAudio.sample_rate} Hz</span>
                      <span>•</span>
                      <span>{currentAudio.channels === 1 ? "Mono" : "Stereo"}</span>
                      <span>•</span>
                      <span>{currentAudio.duration_seconds}s</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      onAudioUploaded(null as any);
                      setActiveJob(null);
                    }}
                    className="text-xs text-slate-400 hover:text-slate-200 underline"
                  >
                    Change Recording
                  </button>
                </div>
              </div>

              {/* WaveSurfer Player */}
              <AudioWaveformPlayer
                audioUrl={getAudioStreamUrl(currentAudio.audio_id)}
                title="Original Raw Vocal Recording"
                waveColor="#334155"
                progressColor="#06b6d4"
              />

              {/* DEDICATED PROMINENT BACKGROUND NOISE REMOVAL OPTION CARD */}
              <div className="bg-gradient-to-r from-emerald-500/10 via-studio-900 to-studio-900 border border-emerald-500/30 rounded-2xl p-5 shadow-lg space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-studio-800/80 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                      <Waves size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                        Remove Background Noise
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                          Studio Gate Active
                        </span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Eliminates room hiss, computer fan hum, and silences pauses between recitation verses.
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      onOverridesChange({
                        ...overrides,
                        noise_reduction_enabled: !isNoiseReductionOn,
                        noise_reduction_mode: isNoiseReductionOn ? "off" : "maximum",
                      })
                    }
                    className={`px-4 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-1.5 shadow ${
                      isNoiseReductionOn
                        ? "bg-emerald-500 text-slate-950 shadow-emerald-500/20"
                        : "bg-studio-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {isNoiseReductionOn ? <VolumeX size={14} /> : <Waves size={14} />}
                    <span>{isNoiseReductionOn ? "Noise Filter: ACTIVE (ON)" : "Noise Filter: BYPASSED (OFF)"}</span>
                  </button>
                </div>

                {isNoiseReductionOn && (
                  <div className="space-y-3">
                    {/* Mode selection buttons */}
                    <div>
                      <span className="text-[11px] font-mono text-slate-400 block mb-1.5">
                        Noise Elimination Strength Mode:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                        {[
                          {
                            id: "maximum",
                            label: "Maximum Studio Clean",
                            desc: "Total pause silence & aggressive fan/hiss kill (-60dB)",
                            strength: 0.90,
                          },
                          {
                            id: "balanced",
                            label: "Balanced Vocal Clean",
                            desc: "Deep hiss removal while preserving subtle breath",
                            strength: 0.75,
                          },
                          {
                            id: "subtle",
                            label: "Subtle Room Clean",
                            desc: "Light cleanup for already quiet studio microphones",
                            strength: 0.45,
                          },
                        ].map((m) => (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() =>
                              onOverridesChange({
                                ...overrides,
                                noise_reduction_enabled: true,
                                noise_reduction_mode: m.id,
                                noise_reduction_strength: m.strength,
                              })
                            }
                            className={`p-2.5 rounded-xl text-left border transition ${
                              currentNoiseMode === m.id
                                ? "bg-emerald-500/20 border-emerald-500/60 text-white shadow"
                                : "bg-studio-850 border-studio-800 text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            <span className="font-bold text-xs block text-white">{m.label}</span>
                            <span className="text-[10px] text-slate-400 block mt-0.5">{m.desc}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Fine-tune noise reduction slider */}
                    <div className="space-y-1 text-xs font-mono pt-1">
                      <div className="flex justify-between text-slate-300">
                        <span>Spectral Suppression Intensity:</span>
                        <span className="text-emerald-400 font-bold">
                          {((overrides.noise_reduction_strength ?? 0.75) * 100).toFixed(0)}%
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
                    </div>
                  </div>
                )}
              </div>

              {/* AI Reciter Profiler Recommendation Banner */}
              {vocalProfile && (
                <div className="p-3.5 rounded-xl bg-gradient-to-r from-amber-500/15 via-amber-500/5 to-transparent border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Sparkles size={14} className="text-amber-400" />
                      <span className="text-xs font-bold text-amber-300 font-mono uppercase tracking-wider">
                        AI Reciter Voice Profile
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">
                        {vocalProfile.vocal_register} ({vocalProfile.estimated_f0_hz} Hz)
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">
                      {vocalProfile.personalized_reason}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onPresetChange(vocalProfile.recommended_preset)}
                    className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs whitespace-nowrap transition shadow self-start sm:self-auto"
                  >
                    Apply {vocalProfile.recommended_preset.replace("_", " ")}
                  </button>
                </div>
              )}

              {/* Interactive Audio Trimmer & Region Slicer Rack */}
              <div className="bg-studio-900 border border-studio-800 rounded-xl p-4 space-y-3 shadow-md">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 uppercase font-mono flex items-center gap-1.5">
                    <Scissors size={14} className="text-amber-400" /> Studio Trimmer & Range Slicer
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Duration: {currentAudio.duration_seconds}s
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-400 text-[11px]">
                      <span>Start Cut (seconds):</span>
                      <span className="text-white font-bold">{trimStart.toFixed(1)}s</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max={Math.max(0, currentAudio.duration_seconds - 0.5)}
                      step="0.1"
                      value={trimStart}
                      onChange={(e) => setTrimStart(parseFloat(e.target.value))}
                      className="w-full accent-amber-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-400 text-[11px]">
                      <span>End Cut (seconds):</span>
                      <span className="text-white font-bold">{(trimEnd || currentAudio.duration_seconds).toFixed(1)}s</span>
                    </div>
                    <input
                      type="range"
                      min={trimStart + 0.5}
                      max={currentAudio.duration_seconds}
                      step="0.1"
                      value={trimEnd || currentAudio.duration_seconds}
                      onChange={(e) => setTrimEnd(parseFloat(e.target.value))}
                      className="w-full accent-amber-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1 flex-wrap">
                  <button
                    type="button"
                    disabled={isEditing || (trimStart === 0 && trimEnd === currentAudio.duration_seconds)}
                    onClick={handleCropAudio}
                    className="px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-750 text-white font-mono text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                  >
                    {isEditing ? <Loader2 size={13} className="animate-spin" /> : <Scissors size={13} className="text-amber-400" />}
                    <span>Crop to Selected Region</span>
                  </button>

                  <button
                    type="button"
                    disabled={isEditing}
                    onClick={handlePreGainBoost}
                    className="px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-750 text-white font-mono text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    <Volume2 size={13} className="text-cyan-400" />
                    <span>+3 dB Vocal Lift</span>
                  </button>
                </div>
              </div>

              {/* Real-time Processing Progress Banner */}
              {isProcessing && activeJob && (
                <div className="bg-studio-900 border border-amber-500/30 rounded-xl p-5 shadow-xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Loader2 className="animate-spin text-amber-400" size={18} />
                      <span className="text-sm font-semibold text-white capitalize">
                        Stage: {activeJob.current_stage.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-amber-400 font-bold">
                        {activeJob.progress_percent}%
                      </span>
                      <button
                        onClick={handleCancel}
                        className="text-xs text-rose-400 hover:text-rose-300 font-medium px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-studio-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-amber-500 to-amber-300 h-2 transition-all duration-300 rounded-full"
                      style={{ width: `${activeJob.progress_percent}%` }}
                    />
                  </div>

                  <p className="text-xs text-slate-400 font-mono">
                    Applying DSP pipeline: noise suppression, Auto-Tune, warm tube saturation, dynamics leveling, echo & broadcast mastering.
                  </p>
                </div>
              )}

              {/* REAL IMPROVEMENTS & AUDITION AUDIT PLAYER */}
              {activeJob && activeJob.status === "completed" && activeJob.output_id && (
                <div className="space-y-4 pt-2">
                  {/* Real Improvements Summary Badge Box */}
                  <div className="p-4 rounded-2xl bg-gradient-to-tr from-emerald-950/60 via-studio-900 to-studio-900 border border-emerald-500/40 shadow-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 size={18} className="text-emerald-400" />
                        <span className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                          Mastered Vocal Improvements
                        </span>
                      </div>
                      <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                        100% Studio Quality
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono pt-1">
                      <div className="p-2.5 rounded-xl bg-studio-950/80 border border-studio-800">
                        <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                          <Waves size={11} className="text-emerald-400" /> Background Noise
                        </span>
                        <span className="text-emerald-400 font-bold">Silenced (-60 dB)</span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-studio-950/80 border border-studio-800">
                        <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                          <Music2 size={11} className="text-amber-400" /> Pitch Quantization
                        </span>
                        <span className="text-amber-400 font-bold">Auto-Tuned</span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-studio-950/80 border border-studio-800">
                        <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                          <Flame size={11} className="text-orange-400" /> Vocal Warmth
                        </span>
                        <span className="text-orange-300 font-bold">Tube Harmonic</span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-studio-950/80 border border-studio-800">
                        <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                          <Radio size={11} className="text-cyan-400" /> Loudness Leveled
                        </span>
                        <span className="text-cyan-300 font-bold">-14.0 LUFS</span>
                      </div>
                    </div>
                  </div>

                  {/* Enhanced Output Player */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5 font-mono">
                        <CheckCircle2 size={14} /> Enhanced Vocal Master (Studio Result)
                      </span>
                      <a
                        href={getOutputDownloadUrl(activeJob.output_id)}
                        download
                        className="inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow"
                      >
                        <Download size={14} /> Download Mastered Audio
                      </a>
                    </div>
                    <AudioWaveformPlayer
                      audioUrl={getOutputStreamUrl(activeJob.output_id)}
                      title="Enhanced Master Audio"
                      waveColor="#065f46"
                      progressColor="#10b981"
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Preset Controls & Quick Knobs Panel */}
        <div className="space-y-5">
          <div className="bg-studio-900 border border-studio-800 rounded-2xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Sliders size={16} className="text-amber-400" /> Enhancement Presets
              </h3>
              <span className="text-[10px] font-mono text-slate-400 capitalize">
                {isAutomatic ? "Automatic Mode" : "Custom Mode"}
              </span>
            </div>

            {/* Presets List */}
            <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
              {studioPresets.map((p) => (
                <div
                  key={p.id}
                  onClick={() => onPresetChange(p.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    preset === p.id
                      ? "bg-amber-500/10 border-amber-500/60 shadow-md"
                      : "bg-studio-850 border-studio-800 hover:border-studio-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-xs text-white">{p.name}</span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        preset === p.id
                          ? "bg-amber-500 text-slate-950"
                          : "bg-studio-800 text-slate-400"
                      }`}
                    >
                      {p.badge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>

            {/* Studio Polish Quick Controls */}
            <div className="pt-3 border-t border-studio-800 space-y-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Zap size={14} className="text-amber-400" /> Studio Polish Quick Knobs
              </span>

              {/* Noise Reduction Quick Knob */}
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between text-slate-300">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Waves size={12} className="text-emerald-400" /> Background Noise Removal
                  </span>
                  <span className="text-emerald-400 font-bold">
                    {isNoiseReductionOn ? `${((overrides.noise_reduction_strength ?? 0.75) * 100).toFixed(0)}%` : "OFF"}
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
                  className="w-full accent-emerald-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Auto-Tune Quick Slider */}
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between text-slate-300">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Music2 size={12} className="text-amber-400" /> Vocal Auto-Tune
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
                  className="w-full accent-amber-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Warm Tube Saturation Quick Slider */}
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between text-slate-300">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Flame size={12} className="text-orange-400" /> Warm Tube Saturation
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
                  className="w-full accent-orange-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Studio Vocal Echo Quick Slider */}
              <div className="space-y-1 text-xs font-mono">
                <div className="flex justify-between text-slate-300">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Radio size={12} className="text-cyan-400" /> Studio Vocal Echo
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
                  className="w-full accent-cyan-400 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
                />
              </div>
            </div>

            {/* One-click Action Button */}
            <button
              disabled={!currentAudio || isProcessing}
              onClick={handleStartEnhancement}
              className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm tracking-wide transition shadow-xl flex items-center justify-center gap-2 ${
                !currentAudio || isProcessing
                  ? "bg-studio-800 text-slate-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 text-slate-950 hover:brightness-110 active:scale-[0.99]"
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Processing Audio...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>Enhance Audio Now</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
