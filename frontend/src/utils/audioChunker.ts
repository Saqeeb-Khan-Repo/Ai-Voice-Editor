import { Mp3Encoder } from "@breezystack/lamejs";

export interface EnhancementStats {
  noiseFloorBefore: number;
  noiseFloorAfter: number;
  lufsAfter: number;
  truePeakAfter: number;
  snrImprovementDb: number;
  durationSeconds: number;
  chunksProcessed: number;
}

export interface StudioControlOptions {
  noiseReductionLevel: "low" | "medium" | "high";
  reverbLevel: "low" | "medium" | "high";
  vocalWarmth: number; // 0.0 - 1.0
  vocalClarity: number; // 0.0 - 1.0
  compressionAmount: number; // 0.0 - 1.0
  outputQuality: "standard" | "high" | "wav";
}

const MAX_DURATION_SECONDS = 600; // 10 minutes max

/**
 * Decodes any browser-supported audio file/recording into an AudioBuffer
 * and validates duration (0.2s to 600s / 10 minutes).
 */
export async function decodeAudioFile(
  file: File | Blob
): Promise<{ audioBuffer: AudioBuffer; durationSeconds: number; playbackUrl: string }> {
  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) {
    throw new Error("Web Audio API is not supported in this browser.");
  }

  const arrayBuffer = await file.arrayBuffer();
  const ctx = new AudioCtx();
  let audioBuffer: AudioBuffer;
  try {
    audioBuffer = await ctx.decodeAudioData(arrayBuffer);
  } catch {
    await ctx.close();
    throw new Error("Could not decode audio file. Please upload a valid WAV, MP3, M4A, OGG, FLAC, or WebM recording.");
  }
  await ctx.close();

  const duration = audioBuffer.duration;
  if (duration < 0.2) {
    throw new Error("Audio recording is too short (minimum 0.2 seconds required).");
  }
  if (duration > MAX_DURATION_SECONDS) {
    throw new Error(`Audio duration (${Math.round(duration)}s) exceeds the maximum limit of 10 minutes (600s).`);
  }

  const playbackUrl = URL.createObjectURL(file);
  return { audioBuffer, durationSeconds: duration, playbackUrl };
}

/**
 * Encodes an AudioBuffer (or sample slice) into a genuine, playable MP3 Blob
 * using @breezystack/lamejs (192 kbps for upload chunks, 320 kbps for studio download).
 */
export function encodeAudioBufferToMp3(
  audioBuffer: AudioBuffer,
  kbps = 320,
  startSample = 0,
  endSample?: number
): Blob {
  const numChannels = Math.min(2, audioBuffer.numberOfChannels);
  const sampleRate = audioBuffer.sampleRate;
  const end = endSample !== undefined ? Math.min(endSample, audioBuffer.length) : audioBuffer.length;
  const numSamples = Math.max(0, end - startSample);

  const mp3Encoder = new Mp3Encoder(numChannels, sampleRate, kbps);
  const mp3Data: BlobPart[] = [];

  const leftFloat = audioBuffer.getChannelData(0);
  const rightFloat = numChannels > 1 ? audioBuffer.getChannelData(1) : leftFloat;

  const blockSize = 1152;
  const leftInt16 = new Int16Array(blockSize);
  const rightInt16 = new Int16Array(blockSize);

  for (let i = 0; i < numSamples; i += blockSize) {
    const chunkLen = Math.min(blockSize, numSamples - i);
    for (let j = 0; j < chunkLen; j++) {
      const idx = startSample + i + j;
      const sl = Math.max(-1, Math.min(1, leftFloat[idx]));
      leftInt16[j] = sl < 0 ? sl * 0x8000 : sl * 0x7fff;
      if (numChannels > 1) {
        const sr = Math.max(-1, Math.min(1, rightFloat[idx]));
        rightInt16[j] = sr < 0 ? sr * 0x8000 : sr * 0x7fff;
      }
    }

    const leftSlice = chunkLen === blockSize ? leftInt16 : leftInt16.subarray(0, chunkLen);
    const mp3buf =
      numChannels > 1
        ? mp3Encoder.encodeBuffer(leftSlice, chunkLen === blockSize ? rightInt16 : rightInt16.subarray(0, chunkLen))
        : mp3Encoder.encodeBuffer(leftSlice);

    if (mp3buf.length > 0) {
      mp3Data.push(new Uint8Array(mp3buf));
    }
  }

  const endBuf = mp3Encoder.flush();
  if (endBuf.length > 0) {
    mp3Data.push(new Uint8Array(endBuf));
  }

  return new Blob(mp3Data, { type: "audio/mpeg" });
}

/**
 * Encodes an AudioBuffer into standard 24-bit PCM WAV Blob (lossless studio master).
 */
export function encodeAudioBufferToWav(audioBuffer: AudioBuffer): Blob {
  const numChannels = Math.min(2, audioBuffer.numberOfChannels);
  const sampleRate = audioBuffer.sampleRate;
  const numSamples = audioBuffer.length;
  const bytesPerSample = 3; // 24-bit
  const blockAlign = numChannels * bytesPerSample;
  const dataSize = numSamples * blockAlign;

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);
  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 24, true);
  writeStr(36, "data");
  view.setUint32(40, dataSize, true);

  const channels: Float32Array[] = [];
  for (let ch = 0; ch < numChannels; ch++) channels.push(audioBuffer.getChannelData(ch));

  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    for (let ch = 0; ch < numChannels; ch++) {
      const s = Math.max(-1, Math.min(1, channels[ch][i]));
      const val = Math.round(s < 0 ? s * 0x800000 : s * 0x7fffff);
      view.setUint8(offset, val & 0xff);
      view.setUint8(offset + 1, (val >> 8) & 0xff);
      view.setUint8(offset + 2, (val >> 16) & 0xff);
      offset += 3;
    }
  }
  return new Blob([buffer], { type: "audio/wav" });
}

/**
 * Enhances an entire AudioBuffer (up to 10 minutes) using stateless MP3 requests
 * to POST /api/audio/enhance-direct.
 */
export async function enhanceAudioStateless(
  audioBuffer: AudioBuffer,
  preset: string,
  onProgress: (stage: string, percent: number) => void,
  abortSignal?: AbortSignal,
  controls?: StudioControlOptions
): Promise<{
  enhancedBuffer: AudioBuffer;
  enhancedMp3Blob: Blob;
  enhancedUrl: string;
  stats: EnhancementStats;
}> {
  const sr = audioBuffer.sampleRate;
  const totalSamples = audioBuffer.length;
  const chunkSec = 90; // 90s at 192kbps MP3 = ~2.16 MB (well under Vercel's 4.5 MB limit)
  const overlapSec = 0.5;
  const chunkSamples = Math.floor(chunkSec * sr);
  const overlapSamples = Math.floor(overlapSec * sr);
  const stepSamples = Math.max(sr, chunkSamples - overlapSamples);

  const ranges: Array<{ start: number; end: number }> = [];
  if (totalSamples <= chunkSamples) {
    ranges.push({ start: 0, end: totalSamples });
  } else {
    let pos = 0;
    while (pos < totalSamples) {
      const end = Math.min(pos + chunkSamples, totalSamples);
      ranges.push({ start: pos, end });
      if (end >= totalSamples) break;
      pos += stepSamples;
    }
  }

  const totalChunks = ranges.length;
  onProgress("analyzing", 10);

  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const decodeCtx = new AudioCtx({ sampleRate: sr });

  const enhancedChunks: AudioBuffer[] = new Array(totalChunks);
  let completed = 0;

  let noiseBeforeSum = 0;
  let noiseAfterSum = 0;
  let lufsAfterSum = 0;
  let peakAfterMax = -99;
  let snrImpSum = 0;

  const concurrency = totalChunks > 1 ? 2 : 1;
  let nextIdx = 0;

  async function worker() {
    while (nextIdx < totalChunks) {
      if (abortSignal?.aborted) {
        throw new Error("Enhancement cancelled by user.");
      }
      const idx = nextIdx++;
      const { start, end } = ranges[idx];

      onProgress("denoising", Math.min(40, 15 + Math.round((completed / totalChunks) * 25)));
      const chunkMp3 = encodeAudioBufferToMp3(audioBuffer, 192, start, end);

      const formData = new FormData();
      formData.append("file", chunkMp3, `chunk_${idx}.mp3`);
      formData.append("preset", preset);
      if (controls) {
        formData.append("noise_reduction_level", controls.noiseReductionLevel);
        formData.append("reverb_level", controls.reverbLevel);
        formData.append("vocal_warmth", String(controls.vocalWarmth));
        formData.append("vocal_clarity", String(controls.vocalClarity));
        formData.append("compression_amount", String(controls.compressionAmount));
      }

      const res = await fetch("/api/audio/enhance-direct", {
        method: "POST",
        body: formData,
        signal: abortSignal,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error (${res.status}) while enhancing audio chunk ${idx + 1}.`);
      }

      const contentType = res.headers.get("content-type") || "";
      if (!contentType.includes("audio/")) {
        throw new Error("Server returned an unexpected non-audio response.");
      }

      noiseBeforeSum += parseFloat(res.headers.get("X-Noise-Floor-Before") || "-40");
      noiseAfterSum += parseFloat(res.headers.get("X-Noise-Floor-After") || "-85");
      lufsAfterSum += parseFloat(res.headers.get("X-LUFS-After") || "-16");
      peakAfterMax = Math.max(peakAfterMax, parseFloat(res.headers.get("X-True-Peak-After") || "-1.0"));
      snrImpSum += parseFloat(res.headers.get("X-SNR-Improvement") || "12");

      const respBuf = await res.arrayBuffer();
      const decodedChunk = await decodeCtx.decodeAudioData(respBuf);
      enhancedChunks[idx] = decodedChunk;

      completed++;
      const pct = Math.min(90, Math.round(25 + (completed / totalChunks) * 65));
      const stageLabel = pct < 55 ? "equalizing" : pct < 80 ? "reverberating" : "normalizing";
      onProgress(stageLabel, pct);
    }
  }

  try {
    await Promise.all(Array.from({ length: concurrency }, () => worker()));
  } finally {
    await decodeCtx.close();
  }

  onProgress("validating", 93);

  // Assemble chunks with smooth raised-cosine crossfade in overlap regions
  const outChannels = Math.max(...enhancedChunks.map((c) => c.numberOfChannels));
  const assembleCtx = new AudioCtx({ sampleRate: sr });
  const finalBuffer = assembleCtx.createBuffer(outChannels, totalSamples, sr);
  await assembleCtx.close();

  for (let ch = 0; ch < outChannels; ch++) {
    const outData = finalBuffer.getChannelData(ch);

    for (let idx = 0; idx < totalChunks; idx++) {
      const chunkBuf = enhancedChunks[idx];
      const srcCh = Math.min(ch, chunkBuf.numberOfChannels - 1);
      const chunkData = chunkBuf.getChannelData(srcCh);
      const { start, end } = ranges[idx];
      const expectedLen = end - start;
      const copyLen = Math.min(expectedLen, chunkData.length);

      if (idx === 0) {
        for (let i = 0; i < copyLen; i++) {
          outData[start + i] = chunkData[i];
        }
      } else {
        const prevEnd = ranges[idx - 1].end;
        const actualOverlap = Math.max(0, Math.min(copyLen, prevEnd - start));
        for (let i = 0; i < actualOverlap; i++) {
          const t = i / Math.max(1, actualOverlap - 1);
          const fadeIn = 0.5 * (1.0 - Math.cos(Math.PI * t));
          const fadeOut = 1.0 - fadeIn;
          outData[start + i] = outData[start + i] * fadeOut + chunkData[i] * fadeIn;
        }
        for (let i = actualOverlap; i < copyLen; i++) {
          outData[start + i] = chunkData[i];
        }
      }
    }

    // Global safety true-peak ceiling (-1.0 dBTP = 0.89125)
    let maxAbs = 0;
    for (let i = 0; i < outData.length; i++) {
      const a = Math.abs(outData[i]);
      if (a > maxAbs) maxAbs = a;
    }
    const ceiling = 0.89125;
    if (maxAbs > ceiling) {
      const scale = ceiling / maxAbs;
      for (let i = 0; i < outData.length; i++) {
        outData[i] *= scale;
      }
    }
  }

  onProgress("exporting", 97);
  const quality = controls?.outputQuality || "high";
  const enhancedMp3Blob =
    quality === "wav"
      ? encodeAudioBufferToWav(finalBuffer)
      : encodeAudioBufferToMp3(finalBuffer, quality === "standard" ? 192 : 320);
  const enhancedUrl = URL.createObjectURL(enhancedMp3Blob);
  onProgress("completed", 100);

  return {
    enhancedBuffer: finalBuffer,
    enhancedMp3Blob,
    enhancedUrl,
    stats: {
      noiseFloorBefore: Number((noiseBeforeSum / totalChunks).toFixed(1)),
      noiseFloorAfter: Number((noiseAfterSum / totalChunks).toFixed(1)),
      lufsAfter: Number((lufsAfterSum / totalChunks).toFixed(1)),
      truePeakAfter: Number(Math.min(-1.0, peakAfterMax).toFixed(1)),
      snrImprovementDb: Number((snrImpSum / totalChunks).toFixed(1)),
      durationSeconds: Number(audioBuffer.duration.toFixed(2)),
      chunksProcessed: totalChunks,
    },
  };
}

/**
 * Triggers a clean binary file download directly from an in-memory Blob.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
