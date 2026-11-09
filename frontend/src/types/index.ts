export interface FrequencyBandAnalysis {
  sub_bass_energy_db: number;
  bass_energy_db: number;
  low_mid_energy_db: number;
  mid_energy_db: number;
  high_mid_energy_db: number;
  presence_high_energy_db: number;
  air_energy_db: number;
  spectral_centroid_hz: number;
  spectral_rolloff_hz: number;
}

export interface AudioQualityProblems {
  has_clipping: boolean;
  clipped_sample_count: number;
  clipped_sample_percentage: number;
  has_sub_rumble: boolean;
  has_boxiness_mud: boolean;
  has_excessive_sibilance: boolean;
  has_high_noise_floor: boolean;
  is_too_quiet: boolean;
  has_excessive_dynamic_range: boolean;
  is_mono: boolean;
}

export interface ReciterVocalProfile {
  estimated_f0_hz: number;
  vocal_register: string;
  vocal_timbre: string;
  recommended_preset: string;
  personalized_reason: string;
}

export interface AudioAnalysisReport {
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  peak_amplitude_dbfs: number;
  rms_dbfs: number;
  crest_factor_db: number;
  integrated_lufs: number | null;
  true_peak_dbtp: number | null;
  silence_regions: Array<{ start_seconds: number; end_seconds: number; duration_seconds: number }>;
  silence_percentage: number;
  estimated_snr_db: number | null;
  noise_estimation_confidence: string;
  frequency_bands: FrequencyBandAnalysis;
  quality_problems: AudioQualityProblems;
  vocal_profile?: ReciterVocalProfile;
  recommendations: string[];
}

export interface ReciterProfile {
  id: string;
  name: string;
  description: string;
  is_builtin: boolean;
  vocal_type: string;
  settings: Record<string, any>;
  created_at?: string;
}

export interface AudioEditPayload {
  start_seconds?: number;
  end_seconds?: number;
  strip_silence?: boolean;
  gain_db?: number;
}

export interface AudioUploadResponse {
  audio_id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  file_size_bytes: number;
  analysis: AudioAnalysisReport;
  message: string;
}

export interface ProcessingDecisionLog {
  preset_selected: string;
  noise_reduction_decision: string;
  high_pass_decision: string;
  eq_decision: string;
  compression_decision: string;
  deess_decision: string;
  reverb_decision: string;
  loudness_decision: string;
  limiting_decision: string;
  notes: string[];
}

export interface ProcessingJobResponse {
  job_id: string;
  audio_id: string;
  status: string;
  current_stage: string;
  progress_percent: number;
  preset_name: string;
  config_parameters?: Record<string, any>;
  decision_log?: ProcessingDecisionLog;
  output_id?: string | null;
  error_message?: string | null;
  execution_time_ms?: number | null;
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface QualityComparisonMetrics {
  duration_passed: boolean;
  duration_delta_seconds: number;
  clipping_resolved: boolean;
  original_clipped_samples: number;
  processed_clipped_samples: number;
  original_integrated_lufs: number | null;
  processed_integrated_lufs: number | null;
  original_true_peak_dbtp: number | null;
  processed_true_peak_dbtp: number | null;
  original_rms_dbfs: number;
  processed_rms_dbfs: number;
  original_crest_factor_db: number;
  processed_crest_factor_db: number;
  estimated_snr_change_db: number | null;
  nan_inf_check_passed: boolean;
  silence_dropout_detected: boolean;
  overall_quality_passed: boolean;
  quality_summary: string;
}

export interface AudioOutputMetadata {
  id: string;
  job_id: string;
  audio_file_id: string;
  filename: string;
  file_format: string;
  file_size_bytes: number;
  metrics: Record<string, any>;
  quality_report: QualityComparisonMetrics;
  created_at: string;
}

export interface MonitoringOverview {
  backend_status: string;
  app_version: string;
  uptime_seconds: number;
  active_jobs_count: number;
  completed_jobs_count: number;
  failed_jobs_count: number;
  total_audio_files: number;
  average_processing_duration_ms: number;
  system_resources: {
    cpu_percent: number;
    memory_used_mb: number;
    memory_total_mb: number;
    memory_percent: number;
  };
  engine_status: {
    engine_name: string;
    active_noise_reducer: string;
    deepfilternet_available: boolean;
    deepfilternet_details: string;
    spectral_gating_available: boolean;
    ffmpeg_available: boolean;
    ffmpeg_version: string | null;
    sample_rate_support: number[];
    device_mode: string;
  };
  storage_usage: {
    originals_bytes: number;
    processed_bytes: number;
    temporary_bytes: number;
    database_bytes: number;
    total_app_storage_bytes: number;
    disk_free_bytes: number;
    disk_total_bytes: number;
  };
  recent_errors: Array<Record<string, any>>;
}

export interface StudioSettings {
  max_upload_size_mb: number;
  allowed_extensions: string[];
  default_target_lufs: number;
  default_true_peak_ceiling_dbtp: number;
  default_sample_rate: number;
  active_noise_reducer: string;
  force_cpu: boolean;
  temp_retention_hours: number;
}
