"use client";

import React, { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import { Play, Pause, Volume2, VolumeX, RotateCcw } from "lucide-react";

interface AudioWaveformPlayerProps {
  audioUrl: string;
  title: string;
  waveColor?: string;
  progressColor?: string;
  height?: number;
  onTimeUpdate?: (currentTime: number) => void;
  syncTime?: number | null;
}

export const AudioWaveformPlayer: React.FC<AudioWaveformPlayerProps> = ({
  audioUrl,
  title,
  waveColor = "#334155",
  progressColor = "#f59e0b",
  height = 70,
  onTimeUpdate,
  syncTime,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.85);

  useEffect(() => {
    if (!containerRef.current) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: waveColor,
      progressColor: progressColor,
      cursorColor: "#ffffff",
      cursorWidth: 2,
      height: height,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      normalize: true,
      url: audioUrl,
    });

    ws.on("play", () => setIsPlaying(true));
    ws.on("pause", () => setIsPlaying(false));
    ws.on("timeupdate", (time) => {
      setCurrentTime(time);
      if (onTimeUpdate) onTimeUpdate(time);
    });
    ws.on("ready", (dur) => {
      setDuration(dur);
      ws.setVolume(volume);
    });

    wavesurferRef.current = ws;

    return () => {
      ws.destroy();
    };
  }, [audioUrl, waveColor, progressColor, height]);

  useEffect(() => {
    if (syncTime !== null && syncTime !== undefined && wavesurferRef.current) {
      const current = wavesurferRef.current.getCurrentTime();
      if (Math.abs(current - syncTime) > 0.15) {
        wavesurferRef.current.setTime(syncTime);
      }
    }
  }, [syncTime]);

  const togglePlay = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  };

  const restart = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setTime(0);
      wavesurferRef.current.play();
    }
  };

  const toggleMute = () => {
    if (wavesurferRef.current) {
      const nextMute = !isMuted;
      wavesurferRef.current.setMuted(nextMute);
      setIsMuted(nextMute);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(val);
      setIsMuted(val === 0);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="bg-studio-900 border border-studio-700/60 rounded-xl p-4 shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase font-mono font-semibold tracking-wider text-slate-400">
          {title}
        </span>
        <span className="text-xs font-mono text-slate-400">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      <div ref={containerRef} className="w-full mb-3 rounded overflow-hidden" />

      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={togglePlay}
            className="w-10 h-10 rounded-full flex items-center justify-center bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold transition shadow-md"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
          </button>
          <button
            onClick={restart}
            className="w-8 h-8 rounded-full flex items-center justify-center bg-studio-800 hover:bg-studio-700 text-slate-300 transition"
            title="Restart"
          >
            <RotateCcw size={14} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className="text-slate-400 hover:text-slate-200 transition"
          >
            {isMuted || volume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 accent-amber-500 h-1.5 bg-studio-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
};
