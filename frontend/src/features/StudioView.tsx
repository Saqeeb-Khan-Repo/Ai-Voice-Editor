"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  UploadCloud,
  Mic,
  Square,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Download,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Music,
  Check,
  Waves,
  Shield,
  ArrowRightLeft,
  FileAudio,
} from "lucide-react";
import { AudioUploadResponse, ProcessingJobResponse } from "@/types";
import {
  uploadAudio,
  listSampleRecordings,
  loadSpecificSample,
  startProcessing,
  getJobStatus,
  cancelJob,
  getAudioStreamUrl,
  getOutputStreamUrl,
  getOutputDownloadUrl,
} from "@/services/api";
import { AudioWaveformPlayer } from "@/components/AudioWaveformPlayer";

interface StudioViewProps {
  onAudioUploaded: (audio: AudioUploadResponse | null) => void;
  currentAudio: AudioUploadResponse | null;
  onJobCompleted: (job: ProcessingJobResponse) => void;
  preset?: string;
  onPresetChange?: (preset: string) => void;
  overrides?: any;
  onOverridesChange?: (overrides: any) => void;
  isAutomatic?: boolean;
  onAutomaticToggle?: (auto: boolean) => void;
}

export const StudioView: React.FC<StudioViewProps> = ({
  onAudioUploaded,
  currentAudio,
  onJobCompleted,
}) => {
  // 1 & 2: Input Modes (Upload / Record)
  const [activeInputTab, setActiveInputTab] = useState<"upload" | "record">("upload");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Live Microphone Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<any>(null);

  // 4 & 5: Processing Progress & Active Job
  const [activeJob, setActiveJob] = useState<ProcessingJobResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // 7: Synchronized A/B Comparison state
  const [abActiveSource, setAbActiveSource] = useState<"original" | "enhanced">("enhanced");
  const [abIsPlaying, setAbIsPlaying] = useState(false);
  const [abCurrentTime, setAbCurrentTime] = useState(0);
  const [abDuration, setAbDuration] = useState(0);
  const [abVolume, setAbVolume] = useState(0.85);
  const [abIsMuted, setAbIsMuted] = useState(false);
  const originalAudioElRef = useRef<HTMLAudioElement | null>(null);
  const enhancedAudioElRef = useRef<HTMLAudioElement | null>(null);

  // Demo samples for quick evaluation
  const [sampleList, setSampleList] = useState<Array<{ id: string; title: string; description: string }>>([
    {
      id: "burda",
      title: "Qasida Burda Sharif (Classical Recitation)",
      description: "Arabic spiritual ode with natural phrasing and room acoustics.",
    },
    {
      id: "hijaz",
      title: "Faslon Ko Takalluf (Maqam Hijaz)",
      description: "Urdu spiritual Naat vocal with characteristic Eastern minor 2nd intervals.",
    },
    {
      id: "salam",
      title: "Mustafa Jane Rehmat (Warm Salam)",
      description: "Traditional soulful salam in baritone register with chest resonance.",
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

  // Handle uploaded file
  const handleFile = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const response = await uploadAudio(file);
      onAudioUploaded(response);
      setActiveJob(null);
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
      setActiveJob(null);
    } catch (err: any) {
      setUploadError(err.message || "Failed to load demo sample.");
    } finally {
      setIsUploading(false);
    }
  };

  // Live Recording Start/Stop
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

        const recFile = new File([recordedBlob], `Live_Vocal_Recording_${Date.now()}.webm`, {
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

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }
  };

  // 4. One-Click AI Voice Enhancement
  const handleEnhanceVoice = async () => {
    if (!currentAudio) return;
    setIsProcessing(true);
    setUploadError(null);
    try {
      // Natural Studio Preset strictly preserves pitch, Tajweed, emotion, and pauses
      const job = await startProcessing(currentAudio.audio_id, {
        preset: "studio_naat",
        automatic_mode: true,
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
            if (status.status === "failed") {
              setUploadError(status.error_message || "Enhancement processing failed.");
            }
          }
        } catch {
          clearInterval(pollInterval);
          setIsProcessing(false);
        }
      }, 500);
    } catch (err: any) {
      setUploadError(err.message || "Failed to start voice enhancement.");
      setIsProcessing(false);
    }
  };

  const handleCancel = async () => {
    if (activeJob) {
      await cancelJob(activeJob.job_id);
      setIsProcessing(false);
    }
  };

  // Synchronized A/B Playback Engine
  const toggleAbPlay = () => {
    const orig = originalAudioElRef.current;
    const enh = enhancedAudioElRef.current;
    if (!orig || !enh) return;

    if (abIsPlaying) {
      orig.pause();
      enh.pause();
      setAbIsPlaying(false);
    } else {
      // Sync positions
      const targetTime = abCurrentTime;
      orig.currentTime = targetTime;
      enh.currentTime = targetTime;

      // Apply volumes according to A/B mode
      orig.volume = abIsMuted ? 0 : abActiveSource === "original" ? abVolume : 0;
      enh.volume = abIsMuted ? 0 : abActiveSource === "enhanced" ? abVolume : 0;

      Promise.all([orig.play(), enh.play()]).then(() => {
        setAbIsPlaying(true);
      }).catch(() => {
        setAbIsPlaying(false);
      });
    }
  };

  const switchAbSource = (source: "original" | "enhanced") => {
    setAbActiveSource(source);
    const orig = originalAudioElRef.current;
    const enh = enhancedAudioElRef.current;
    if (!orig || !enh) return;

    if (source === "original") {
      orig.volume = abIsMuted ? 0 : abVolume;
      enh.volume = 0;
    } else {
      orig.volume = 0;
      enh.volume = abIsMuted ? 0 : abVolume;
    }
  };

  const handleAbSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setAbCurrentTime(time);
    if (originalAudioElRef.current) originalAudioElRef.current.currentTime = time;
    if (enhancedAudioElRef.current) enhancedAudioElRef.current.currentTime = time;
  };

  const handleAbVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value);
    setAbVolume(vol);
    setAbIsMuted(vol === 0);
    if (originalAudioElRef.current && abActiveSource === "original") {
      originalAudioElRef.current.volume = vol;
    }
    if (enhancedAudioElRef.current && abActiveSource === "enhanced") {
      enhancedAudioElRef.current.volume = vol;
    }
  };

  const toggleAbMute = () => {
    const nextMute = !abIsMuted;
    setAbIsMuted(nextMute);
    if (originalAudioElRef.current) {
      originalAudioElRef.current.volume = nextMute ? 0 : abActiveSource === "original" ? abVolume : 0;
    }
    if (enhancedAudioElRef.current) {
      enhancedAudioElRef.current.volume = nextMute ? 0 : abActiveSource === "enhanced" ? abVolume : 0;
    }
  };

  const restartAb = () => {
    if (originalAudioElRef.current) originalAudioElRef.current.currentTime = 0;
    if (enhancedAudioElRef.current) enhancedAudioElRef.current.currentTime = 0;
    setAbCurrentTime(0);
    if (!abIsPlaying) {
      toggleAbPlay();
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  // Stage labels for clean human-readable progress
  const stageDescriptions: Record<string, string> = {
    decoding: "Decoding original audio file safely...",
    analyzing: "Analyzing voice profile, pitch, and acoustic noise floor...",
    denoising: "Removing background noise, room tone, and preamp hiss...",
    filtering: "High-pass filtering low-frequency rumble...",
    equalizing: "Applying gentle vocal air & scooping boxiness...",
    pitch_correcting: "Preserving natural vocal pitch and intonation...",
    saturating: "Infusing warm analog tube harmonics...",
    compressing: "Applying transparent dynamic optical leveling...",
    deessing: "Taming harsh sibilance frequencies...",
    doubling: "Polishing stereo depth...",
    reverberating: "Applying natural vocal acoustics...",
    echoing: "Polishing vocal atmosphere...",
    normalizing: "Mastering loudness to -14.0 LUFS broadcast standard...",
    limiting: "True-peak lookahead limiting to prevent clipping...",
    validating: "Validating audio quality and speech preservation...",
    exporting: "Generating studio-quality master audio file...",
    completed: "Master enhancement completed successfully!",
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-2">
      {/* Studio Header: Minimal & Clear */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-1">
          <Sparkles size={14} className="text-amber-400" />
          <span>Local AI Vocal Studio • 100% Privacy</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          AI Naat & Quran Vocal Studio
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          One-click studio vocal enhancement. Removes background noise, adds natural warmth and broadcast loudness while strictly preserving your authentic voice, pitch, and emotion.
        </p>
      </div>

      {uploadError && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-2xl p-4 flex items-center gap-3 text-sm shadow">
          <AlertTriangle size={20} className="shrink-0 text-rose-400" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* 1 & 2: INPUT SECTION (UPLOAD AUDIO / RECORD AUDIO) */}
      {!currentAudio && (
        <div className="bg-studio-900 border border-studio-800 rounded-3xl p-6 shadow-2xl space-y-6">
          {/* Tabs for Upload vs Record */}
          <div className="flex items-center justify-center gap-2 p-1.5 bg-studio-950 rounded-2xl max-w-md mx-auto border border-studio-800">
            <button
              type="button"
              onClick={() => setActiveInputTab("upload")}
              className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                activeInputTab === "upload"
                  ? "bg-amber-500 text-slate-950 shadow-md font-extrabold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <UploadCloud size={16} />
              <span>1. Upload Audio</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveInputTab("record")}
              className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                activeInputTab === "record"
                  ? "bg-rose-500 text-white shadow-md font-extrabold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Mic size={16} />
              <span>2. Record Audio</span>
            </button>
          </div>

          {/* 1. Upload View */}
          {activeInputTab === "upload" && (
            <div className="space-y-6">
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-studio-700 hover:border-amber-500/70 rounded-2xl p-10 text-center bg-studio-950/40 hover:bg-studio-950/70 transition cursor-pointer group"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".wav,.mp3,.flac,.webm,.ogg,.m4a"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      handleFile(e.target.files[0]);
                    }
                  }}
                />
                <div className="w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-105 transition shadow-inner">
                  {isUploading ? (
                    <Loader2 className="animate-spin" size={32} />
                  ) : (
                    <UploadCloud size={32} />
                  )}
                </div>
                <h3 className="text-lg font-bold text-white mb-1">
                  {isUploading ? "Uploading & Analyzing Recording..." : "Drop Your Vocal Recording Here"}
                </h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                  Click to browse from your computer. Supports WAV, MP3, FLAC, M4A, or WebM.
                </p>
                <span className="inline-block px-4 py-1.5 rounded-lg text-xs font-semibold bg-studio-800 text-slate-300 border border-studio-700">
                  Select Audio File
                </span>
              </div>

              {/* Instant Evaluation Samples */}
              <div className="pt-2 border-t border-studio-800">
                <span className="text-xs font-mono font-semibold text-slate-400 block mb-3 text-center">
                  Or test immediately with an authentic recitation sample:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {sampleList.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      disabled={isUploading}
                      onClick={() => handleLoadSample(s.id)}
                      className="p-3 text-left rounded-xl bg-studio-950 hover:bg-studio-800 border border-studio-800 hover:border-amber-500/40 transition group"
                    >
                      <span className="text-xs font-bold text-white group-hover:text-amber-400 block truncate">
                        {s.title}
                      </span>
                      <span className="text-[11px] text-slate-400 line-clamp-2 mt-0.5">
                        {s.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 2. Record Live View */}
          {activeInputTab === "record" && (
            <div className="py-6 text-center space-y-6">
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-white">Live Microphone Voice Recorder</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Recite your Naat or Surah directly through your microphone. We will optimize and enhance it.
                </p>
              </div>

              <div className="flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  {isRecording && (
                    <div
                      className="absolute -inset-3 rounded-full bg-rose-500/25 animate-ping pointer-events-none"
                      style={{ animationDuration: "1.5s" }}
                    />
                  )}
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition transform active:scale-95 ${
                      isRecording
                        ? "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/40"
                        : "bg-gradient-to-tr from-rose-500 to-rose-400 hover:brightness-110 text-white shadow-rose-500/30"
                    }`}
                  >
                    {isRecording ? <Square size={26} className="fill-white" /> : <Mic size={32} />}
                  </button>
                </div>

                {isRecording ? (
                  <div className="space-y-1">
                    <div className="text-3xl font-mono font-black text-rose-400">
                      {formatTimer(recordingSeconds)}
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      Recording live... Click square button when finished
                    </span>
                  </div>
                ) : (
                  <span className="text-xs font-mono text-slate-400">
                    Click microphone icon to begin reciting
                  </span>
                )}

                {/* Live VU Meter */}
                {isRecording && (
                  <div className="w-64 max-w-full space-y-1 pt-1">
                    <div className="flex justify-between text-[10px] font-mono text-slate-500">
                      <span>Mic Input Level</span>
                      <span>{audioLevel}%</span>
                    </div>
                    <div className="w-full bg-studio-950 rounded-full h-2 overflow-hidden border border-studio-800">
                      <div
                        className={`h-full transition-all duration-75 rounded-full ${
                          audioLevel > 80
                            ? "bg-rose-500"
                            : audioLevel > 45
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
        </div>
      )}

      {/* WORKFLOW WHEN AUDIO IS LOADED */}
      {currentAudio && (
        <div className="space-y-6">
          {/* Audio Info & Change Option */}
          <div className="bg-studio-900 border border-studio-800 rounded-2xl p-4 flex items-center justify-between shadow">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-studio-800 flex items-center justify-center text-amber-400">
                <FileAudio size={20} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white truncate max-w-xs sm:max-w-md">
                  {currentAudio.filename}
                </h3>
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mt-0.5">
                  <span>{currentAudio.duration_seconds}s</span>
                  <span>•</span>
                  <span>{currentAudio.sample_rate} Hz</span>
                  <span>•</span>
                  <span>{currentAudio.channels === 1 ? "Mono" : "Stereo"}</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                onAudioUploaded(null);
                setActiveJob(null);
              }}
              className="text-xs text-slate-400 hover:text-white underline font-medium"
            >
              Choose Another Recording
            </button>
          </div>

          {/* 3. ORIGINAL AUDIO PLAYER */}
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Music size={14} className="text-cyan-400" /> 3. Original Audio Player
              </span>
              <span className="text-[11px] font-mono text-slate-500">Raw Input</span>
            </div>
            <AudioWaveformPlayer
              audioUrl={getAudioStreamUrl(currentAudio.audio_id)}
              title="Original Recording"
              waveColor="#334155"
              progressColor="#06b6d4"
            />
          </div>

          {/* 4. ENHANCE MY VOICE BUTTON (ONE-CLICK PRIMARY ACTION) */}
          <div className="py-2">
            <button
              type="button"
              disabled={isProcessing}
              onClick={handleEnhanceVoice}
              className={`w-full py-4 px-6 rounded-2xl font-black text-base sm:text-lg tracking-wide transition shadow-2xl flex items-center justify-center gap-3 ${
                isProcessing
                  ? "bg-studio-800 text-slate-500 cursor-not-allowed border border-studio-700"
                  : "bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 text-slate-950 hover:brightness-110 active:scale-[0.99] shadow-amber-500/20"
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  <span>Enhancing Your Voice...</span>
                </>
              ) : (
                <>
                  <Sparkles size={24} />
                  <span>4. Enhance My Voice</span>
                </>
              )}
            </button>
            <p className="text-center text-xs text-slate-400 mt-2 font-mono">
              Preserves 100% of your authentic voice, natural breathing pauses, pitch, and emotion.
            </p>
          </div>

          {/* 5. PROCESSING PROGRESS */}
          {isProcessing && activeJob && (
            <div className="bg-studio-900 border border-amber-500/40 rounded-2xl p-6 shadow-2xl space-y-4 animate-fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="animate-spin text-amber-400" size={20} />
                  <span className="text-sm font-bold text-white capitalize font-mono">
                    5. Processing: {activeJob.current_stage.replace("_", " ")}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono text-amber-400 font-black">
                    {activeJob.progress_percent}%
                  </span>
                  <button
                    onClick={handleCancel}
                    className="text-xs text-rose-400 hover:text-rose-300 font-semibold px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20"
                  >
                    Cancel
                  </button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-studio-950 rounded-full h-3 overflow-hidden border border-studio-800">
                <div
                  className="bg-gradient-to-r from-amber-500 via-amber-400 to-emerald-400 h-3 transition-all duration-300 rounded-full shadow-sm"
                  style={{ width: `${activeJob.progress_percent}%` }}
                />
              </div>

              <p className="text-xs text-slate-400 font-mono">
                {stageDescriptions[activeJob.current_stage] || "Processing vocal audio..."}
              </p>
            </div>
          )}

          {/* COMPLETED ENHANCEMENT: 6, 7 & 8 */}
          {activeJob && activeJob.status === "completed" && activeJob.output_id && (
            <div className="space-y-6 pt-2 animate-fade-in">
              {/* 6. ENHANCED AUDIO PLAYER */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-1">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 size={14} /> 6. Enhanced Audio Player
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                    Studio Master
                  </span>
                </div>
                <AudioWaveformPlayer
                  audioUrl={getOutputStreamUrl(activeJob.output_id)}
                  title="Enhanced Studio Recording"
                  waveColor="#065f46"
                  progressColor="#10b981"
                />
              </div>

              {/* 7. ORIGINAL VS ENHANCED COMPARISON (SYNCHRONIZED A/B) */}
              <div className="bg-gradient-to-tr from-studio-900 via-studio-900 to-studio-850 border border-studio-700 rounded-3xl p-6 shadow-2xl space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-studio-800 pb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                      <ArrowRightLeft size={16} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                        7. Original vs Enhanced Comparison
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Seamless synchronized A/B audition. Switch between sources at the exact same second.
                      </p>
                    </div>
                  </div>

                  {/* Synchronized A/B Selector */}
                  <div className="flex items-center gap-1.5 p-1 bg-studio-950 rounded-xl border border-studio-800 self-start sm:self-auto">
                    <button
                      type="button"
                      onClick={() => switchAbSource("original")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
                        abActiveSource === "original"
                          ? "bg-cyan-500 text-slate-950 shadow"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Original Recording
                    </button>
                    <button
                      type="button"
                      onClick={() => switchAbSource("enhanced")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition flex items-center gap-1 ${
                        abActiveSource === "enhanced"
                          ? "bg-emerald-500 text-slate-950 shadow"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      <Sparkles size={12} />
                      Enhanced Studio
                    </button>
                  </div>
                </div>

                {/* Synchronized Audio Controller */}
                <div className="space-y-3">
                  {/* Hidden Synchronized HTML5 Audio Elements */}
                  <audio
                    ref={originalAudioElRef}
                    src={getAudioStreamUrl(currentAudio.audio_id)}
                    preload="auto"
                    onTimeUpdate={(e) => {
                      const time = (e.target as HTMLAudioElement).currentTime;
                      setAbCurrentTime(time);
                    }}
                    onLoadedMetadata={(e) => {
                      setAbDuration((e.target as HTMLAudioElement).duration);
                    }}
                    onEnded={() => setAbIsPlaying(false)}
                  />
                  <audio
                    ref={enhancedAudioElRef}
                    src={getOutputStreamUrl(activeJob.output_id)}
                    preload="auto"
                    onEnded={() => setAbIsPlaying(false)}
                  />

                  {/* Scrubber */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-mono text-slate-400">
                      <span>Currently Auditioning: <strong className={abActiveSource === "enhanced" ? "text-emerald-400" : "text-cyan-400"}>{abActiveSource === "enhanced" ? "Enhanced Studio Vocal" : "Original Raw Vocal"}</strong></span>
                      <span>
                        {formatTimer(abCurrentTime)} / {formatTimer(abDuration || currentAudio.duration_seconds)}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max={abDuration || currentAudio.duration_seconds}
                      step="0.05"
                      value={abCurrentTime}
                      onChange={handleAbSeek}
                      className="w-full accent-amber-500 h-2 bg-studio-950 rounded-lg cursor-pointer"
                    />
                  </div>

                  {/* Playback & Volume controls */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={toggleAbPlay}
                        className="w-10 h-10 rounded-full flex items-center justify-center bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold transition shadow-md"
                        title={abIsPlaying ? "Pause" : "Play"}
                      >
                        {abIsPlaying ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
                      </button>
                      <button
                        type="button"
                        onClick={restartAb}
                        className="w-8 h-8 rounded-full flex items-center justify-center bg-studio-800 hover:bg-studio-700 text-slate-300 transition"
                        title="Restart"
                      >
                        <RotateCcw size={14} />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={toggleAbMute}
                        className="text-slate-400 hover:text-white transition"
                      >
                        {abIsMuted || abVolume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
                      </button>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={abIsMuted ? 0 : abVolume}
                        onChange={handleAbVolumeChange}
                        className="w-20 accent-amber-500 h-1.5 bg-studio-950 rounded-lg cursor-pointer"
                      />
                    </div>
                  </div>
                </div>

                {/* Objective Improvements Overview */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono pt-2">
                  <div className="p-3 rounded-xl bg-studio-950 border border-studio-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Background Noise</span>
                    <span className="text-emerald-400 font-bold">Deeply Eliminated</span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Breaths Preserved</span>
                  </div>
                  <div className="p-3 rounded-xl bg-studio-950 border border-studio-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Vocal Timbre</span>
                    <span className="text-amber-400 font-bold">Authentic Voice</span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">100% Identity Intact</span>
                  </div>
                  <div className="p-3 rounded-xl bg-studio-950 border border-studio-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Volume Balance</span>
                    <span className="text-emerald-400 font-bold">Leveling Applied</span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Optical Leveler (2.2:1)</span>
                  </div>
                  <div className="p-3 rounded-xl bg-studio-950 border border-studio-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Master Loudness</span>
                    <span className="text-cyan-400 font-bold">-14.0 LUFS</span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">True-Peak -1.0 dBTP</span>
                  </div>
                </div>
              </div>

              {/* 8. DOWNLOAD ENHANCED AUDIO (3 FORMATS) */}
              <div className="bg-studio-900 border border-studio-800 rounded-3xl p-6 shadow-2xl space-y-4">
                <div>
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                    <Download size={16} className="text-emerald-400" />
                    8. Download Enhanced Audio
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Choose your preferred studio export format:
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* WAV 24-bit */}
                  <a
                    href={getOutputDownloadUrl(activeJob.output_id, "wav_24")}
                    download
                    className="p-4 rounded-2xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/60 transition group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-emerald-400 font-mono">WAV 24-bit</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                          Master
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Full dynamic range, lossless studio master. Recommended for archiving and post-production.
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-emerald-500/20 flex items-center justify-between text-xs font-bold text-emerald-400 group-hover:translate-x-0.5 transition">
                      <span>Download WAV 24-bit</span>
                      <Download size={14} />
                    </div>
                  </a>

                  {/* WAV 16-bit */}
                  <a
                    href={getOutputDownloadUrl(activeJob.output_id, "wav_16")}
                    download
                    className="p-4 rounded-2xl bg-studio-950 hover:bg-studio-800 border border-studio-800 hover:border-cyan-500/40 transition group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-cyan-400 font-mono">WAV 16-bit</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-studio-800 text-slate-400">
                          CD Quality
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Universal uncompressed audio. Ideal for car players, older hardware, and CD burning.
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-studio-800 flex items-center justify-between text-xs font-bold text-cyan-400 group-hover:translate-x-0.5 transition">
                      <span>Download WAV 16-bit</span>
                      <Download size={14} />
                    </div>
                  </a>

                  {/* MP3 320 kbps */}
                  <a
                    href={getOutputDownloadUrl(activeJob.output_id, "mp3_320")}
                    download
                    className="p-4 rounded-2xl bg-studio-950 hover:bg-studio-800 border border-studio-800 hover:border-amber-500/40 transition group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-amber-400 font-mono">MP3 320 kbps</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-studio-800 text-slate-400">
                          High Bitrate
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Highest quality MP3 compression. Ideal for WhatsApp, YouTube, and mobile streaming.
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-studio-800 flex items-center justify-between text-xs font-bold text-amber-400 group-hover:translate-x-0.5 transition">
                      <span>Download MP3 320k</span>
                      <Download size={14} />
                    </div>
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
