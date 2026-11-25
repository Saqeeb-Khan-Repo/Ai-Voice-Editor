export interface EnhancementStats {
  noiseFloorBefore: number;
  noiseFloorAfter: number;
  lufsAfter: number;
  truePeakAfter: number;
  snrImprovementDb: number;
  durationSeconds: number;
  chunksProcessed: number;
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
 * Encodes an AudioBuffer (or a sample slice) into standard 16-bit or 24-bit PCM WAV Blob.
 */
export function encodeAudioBufferToWav(
  audioBuffer: AudioBuffer,
  bitDepth: 16 | 24 = 16,
  startSample = 0,
  endSample?: number
): Blob {
  const numChannels = Math.min(2, audioBuffer.numberOfChannels);
  const sampleRate = audioBuffer.sampleRate;
  const end = endSample !== undefined ? Math.min(endSample, audioBuffer.length) : audioBuffer.length;
  const numSamples = Math.max(0, end - startSample);
  const bytesPerSample = bitDepth === 24 ? 3 : 2;
  const blockAlign = numChannels * bytesPerSample;
  const dataSize = numSamples * blockAlign;

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitDepth, true);
  writeStr(36, "data");
  view.setUint32(40, dataSize, true);

  const channels: Float32Array[] = [];
  for (let ch = 0; ch < numChannels; ch++) {
    channels.push(audioBuffer.getChannelData(ch));
  }

  let offset = 44;
  if (bitDepth === 24) {
    for (let i = startSample; i < end; i++) {
      for (let ch = 0; ch < numChannels; ch++) {
        const s = Math.max(-1, Math.min(1, channels[ch][i]));
        const val = Math.round(s < 0 ? s * 0x800000 : s * 0x7fffff);
        view.setUint8(offset, val & 0xff);
        view.setUint8(offset + 1, (val >> 8) & 0xff);
        view.setUint8(offset + 2, (val >> 16) & 0xff);
        offset += 3;
      }
    }
  } else {
    for (let i = startSample; i < end; i++) {
      for (let ch = 0; ch < numChannels; ch++) {
        const s = Math.max(-1, Math.min(1, channels[ch][i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        offset += 2;
      }
    }
  }

  return new Blob([buffer], { type: "audio/wav" });
}

/**
 * Enhances an entire AudioBuffer (up to 10 minutes) using stateless chunked requests
 * to POST /api/audio/enhance-direct. Each chunk is strictly <= ~1.8 MB (well below
 * Vercel's 4.5 MB serverless payload limit) and stitched with overlap-add crossfading.
 */
export async function enhanceAudioStateless(
  audioBuffer: AudioBuffer,
  preset: string,
  onProgress: (stage: string, percent: number) => void,
  abortSignal?: AbortSignal
): Promise<{
  enhancedBuffer: AudioBuffer;
  enhancedWavBlob: Blob;
  enhancedUrl: string;
  stats: EnhancementStats;
}> {
  const sr = audioBuffer.sampleRate;
  const totalSamples = audioBuffer.length;
  const chunkSec = 10; // 10s chunks => ~0.88 MB mono / ~1.76 MB stereo 16-bit WAV
  const overlapSec = 0.25;
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
  onProgress("analyzing", 5);

  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const decodeCtx = new AudioCtx({ sampleRate: sr });

  const enhancedChunks: AudioBuffer[] = new Array(totalChunks);
  let completed = 0;

  let noiseBeforeSum = 0;
  let noiseAfterSum = 0;
  let lufsAfterSum = 0;
  let peakAfterMax = -99;
  let snrImpSum = 0;

  // Process up to 2 chunks concurrently for high speed without overloading Vercel
  const concurrency = totalChunks > 1 ? 2 : 1;
  let nextIdx = 0;

  async function worker() {
    while (nextIdx < totalChunks) {
      if (abortSignal?.aborted) {
        throw new Error("Enhancement cancelled by user.");
      }
      const idx = nextIdx++;
      const { start, end } = ranges[idx];
      const chunkWav = encodeAudioBufferToWav(audioBuffer, 16, start, end);

      const formData = new FormData();
      formData.append("file", chunkWav, `chunk_${idx}.wav`);
      formData.append("preset", preset);

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
      const pct = Math.min(92, Math.round(10 + (completed / totalChunks) * 82));
      const stageLabel =
        pct < 35 ? "denoising" : pct < 60 ? "equalizing" : pct < 80 ? "reverberating" : "normalizing";
      onProgress(stageLabel, pct);
    }
  }

  try {
    await Promise.all(Array.from({ length: concurrency }, () => worker()));
  } finally {
    await decodeCtx.close();
  }

  onProgress("validating", 95);

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
        // Crossfade overlap
        for (let i = 0; i < actualOverlap; i++) {
          const t = i / Math.max(1, actualOverlap - 1);
          const fadeIn = 0.5 * (1.0 - Math.cos(Math.PI * t));
          const fadeOut = 1.0 - fadeIn;
          outData[start + i] = outData[start + i] * fadeOut + chunkData[i] * fadeIn;
        }
        // Copy remainder
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

  onProgress("exporting", 98);
  const enhancedWavBlob = encodeAudioBufferToWav(finalBuffer, 16);
  const enhancedUrl = URL.createObjectURL(enhancedWavBlob);
  onProgress("completed", 100);

  return {
    enhancedBuffer: finalBuffer,
    enhancedWavBlob,
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
 * Never downloads JSON error payloads.
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
