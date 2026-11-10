import {
  AudioUploadResponse,
  AudioAnalysisReport,
  ProcessingJobResponse,
  AudioOutputMetadata,
  MonitoringOverview,
  StudioSettings,
  ReciterProfile,
  AudioEditPayload,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function uploadAudio(file: File): Promise<AudioUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/audio/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function loadSampleAudio(): Promise<AudioUploadResponse> {
  const res = await fetch(`${API_BASE}/audio/load-sample`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to load demo sample vocal recording.");
  }
  return res.json();
}

export async function listSampleRecordings(): Promise<Array<{ id: string; title: string; description: string }>> {
  const res = await fetch(`${API_BASE}/audio/samples/list`);
  if (!res.ok) {
    return [
      { id: "hijaz", title: "Faslon Ko Takalluf (Maqam Hijaz)", description: "Urdu spiritual Naat vocal." },
      { id: "burda", title: "Qasida Burda Sharif (Arabic Recitation)", description: "Classical Arabic spiritual ode." },
      { id: "salam", title: "Mustafa Jane Rehmat (Warm Salam)", description: "Traditional soulful salam cadence." },
    ];
  }
  return res.json();
}

export async function loadSpecificSample(key: string): Promise<AudioUploadResponse> {
  const res = await fetch(`${API_BASE}/audio/load-sample/${key}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to load sample: ${key}`);
  }
  return res.json();
}

export async function getAudioAnalysis(audioId: string): Promise<AudioAnalysisReport> {
  const res = await fetch(`${API_BASE}/audio/${audioId}/analysis`);
  if (!res.ok) {
    throw new Error(`Failed to load audio analysis: ${res.status}`);
  }
  return res.json();
}

export async function editAudio(
  audioId: string,
  payload: AudioEditPayload
): Promise<AudioUploadResponse> {
  const res = await fetch(`${API_BASE}/audio/${audioId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to edit audio.`);
  }
  return res.json();
}

export async function listReciterProfiles(): Promise<{ total: number; profiles: ReciterProfile[] }> {
  const res = await fetch(`${API_BASE}/profiles`);
  if (!res.ok) {
    throw new Error("Failed to load reciter profiles.");
  }
  return res.json();
}

export async function createReciterProfile(payload: {
  name: string;
  description?: string;
  vocal_type?: string;
  settings: Record<string, any>;
}): Promise<ReciterProfile> {
  const res = await fetch(`${API_BASE}/profiles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to save profile.");
  }
  return res.json();
}

export async function deleteReciterProfile(profileId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/profiles/${profileId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to delete profile.");
  }
  return res.json();
}

export async function startProcessing(
  audioId: string,
  params: {
    preset: string;
    automatic_mode: boolean;
    custom_profile_id?: string;
    overrides?: {
      noise_reduction_enabled?: boolean;
      noise_reduction_strength?: number;
      noise_reduction_mode?: string;
      eq_intensity?: number;
      compression_intensity?: number;
      reverb_amount?: number;
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
      trim_start_seconds?: number;
      trim_end_seconds?: number;
      strip_silence?: boolean;
      target_lufs?: number;
      true_peak_ceiling?: number;
      output_format?: string;
    };
  }
): Promise<ProcessingJobResponse> {
  const res = await fetch(`${API_BASE}/processing/${audioId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to start processing job`);
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<ProcessingJobResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Failed to retrieve job status`);
  }
  return res.json();
}

export async function listJobs(): Promise<{ total: number; jobs: ProcessingJobResponse[] }> {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) {
    throw new Error(`Failed to load processing history`);
  }
  return res.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/jobs/${jobId}/cancel`, { method: "POST" });
}

export async function getOutputMetadata(outputId: string): Promise<AudioOutputMetadata> {
  const res = await fetch(`${API_BASE}/outputs/${outputId}/metadata`);
  if (!res.ok) {
    throw new Error(`Failed to load output metadata`);
  }
  return res.json();
}

export async function getMonitoringOverview(): Promise<MonitoringOverview> {
  const res = await fetch(`${API_BASE}/monitoring/overview`);
  if (!res.ok) {
    throw new Error(`Failed to load system monitoring overview`);
  }
  return res.json();
}

export async function getStudioSettings(): Promise<StudioSettings> {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) {
    throw new Error(`Failed to load settings`);
  }
  return res.json();
}

export async function updateStudioSettings(payload: Partial<StudioSettings>): Promise<any> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function clearAllStudioData(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/settings/clear-all-data`, {
    method: "POST",
  });
  return res.json();
}

export function getAudioStreamUrl(audioId: string): string {
  return `${API_BASE}/audio/${audioId}/stream`;
}

export function getOutputStreamUrl(outputId: string): string {
  return `${API_BASE}/outputs/${outputId}/stream`;
}

export function getOutputDownloadUrl(
  outputId: string,
  format?: "wav_24" | "wav_16" | "mp3_320" | string
): string {
  if (format) {
    return `${API_BASE}/outputs/${outputId}/download?format=${format}`;
  }
  return `${API_BASE}/outputs/${outputId}/download`;
}
