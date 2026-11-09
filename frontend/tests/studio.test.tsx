import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AnalysisView } from "../src/features/AnalysisView";
import { EnhancementSettingsView } from "../src/features/EnhancementSettingsView";
import { AudioAnalysisReport } from "../src/types";

describe("AnalysisView", () => {
  it("renders empty state when no analysis is passed", () => {
    render(<AnalysisView analysis={null} />);
    expect(screen.getByText(/No Audio Recording Loaded/i)).toBeDefined();
  });

  it("renders objective acoustic metrics when report is provided", () => {
    const mockReport: AudioAnalysisReport = {
      duration_seconds: 3.5,
      sample_rate: 44100,
      channels: 1,
      peak_amplitude_dbfs: -3.2,
      rms_dbfs: -18.5,
      crest_factor_db: 15.3,
      integrated_lufs: -16.2,
      true_peak_dbtp: -1.5,
      silence_regions: [],
      silence_percentage: 12.0,
      estimated_snr_db: 28.5,
      noise_estimation_confidence: "measured",
      frequency_bands: {
        sub_bass_energy_db: -42.0,
        bass_energy_db: -28.0,
        low_mid_energy_db: -24.0,
        mid_energy_db: -20.0,
        high_mid_energy_db: -22.0,
        presence_high_energy_db: -30.0,
        air_energy_db: -38.0,
        spectral_centroid_hz: 1450.0,
        spectral_rolloff_hz: 3800.0,
      },
      quality_problems: {
        has_clipping: false,
        clipped_sample_count: 0,
        clipped_sample_percentage: 0.0,
        has_sub_rumble: false,
        has_boxiness_mud: false,
        has_excessive_sibilance: false,
        has_high_noise_floor: false,
        is_too_quiet: false,
        has_excessive_dynamic_range: false,
        is_mono: true,
      },
      recommendations: ["Gentle enhancement with transparent air and subtle warmth is recommended."],
    };

    render(<AnalysisView analysis={mockReport} />);
    expect(screen.getByText(/Objective Audio Quality Analysis/i)).toBeDefined();
    expect(screen.getByText(/-16.2 LUFS/i)).toBeDefined();
    expect(screen.getByText(/-1.5 dBTP/i)).toBeDefined();
    expect(screen.getByText(/Gentle enhancement with transparent air/i)).toBeDefined();
  });
});

describe("EnhancementSettingsView", () => {
  it("renders the 3 standard Naat presets", () => {
    const dummyOverrides = {
      noise_reduction_strength: 0.35,
      eq_intensity: 1.0,
      compression_intensity: 0.5,
      reverb_amount: 0.08,
      target_lufs: -16.0,
      output_format: "wav",
    };

    render(
      <EnhancementSettingsView
        preset="natural_naat"
        onPresetChange={vi.fn()}
        overrides={dummyOverrides}
        onOverridesChange={vi.fn()}
        isAutomatic={true}
        onAutomaticToggle={vi.fn()}
      />
    );

    expect(screen.getByText(/Natural Naat/i)).toBeDefined();
    expect(screen.getByText(/Studio Naat/i)).toBeDefined();
    expect(screen.getByText(/Spacious Naat/i)).toBeDefined();
  });
});
