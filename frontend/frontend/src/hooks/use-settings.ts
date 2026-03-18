/**
 * Canvas Learning System - Settings Hook
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * React hook for loading, saving, and updating application settings.
 * Uses Tauri Store plugin for local persistence when running in Tauri,
 * falls back to localStorage for web development.
 *
 * API keys are stored locally only (never sent to logs or external services).
 *
 * [Source: Story 1.3 AC-6 — API Key secure storage]
 * [Source: Story 1.3 Task 1.3 / 1.4 — settings load/save]
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  type CanvasLearningSettings,
  DEFAULT_SETTINGS,
} from "@/types/settings";
import { getApiClient } from "@/lib/api-client";

const STORAGE_KEY = "canvas-learning-settings";

/**
 * Load settings from Tauri Store or localStorage fallback.
 * Never logs API keys.
 */
async function loadFromStorage(): Promise<CanvasLearningSettings> {
  try {
    // Try Tauri Store first (v2 API uses load() factory)
    const { load } = await import("@tauri-apps/plugin-store");
    const store = await load("settings.json");
    const stored = await store.get<CanvasLearningSettings>(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...stored };
    }
  } catch {
    // Tauri not available — use localStorage
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<CanvasLearningSettings>;
        return { ...DEFAULT_SETTINGS, ...parsed };
      }
    } catch {
      // Parsing failed, use defaults
    }
  }
  return { ...DEFAULT_SETTINGS };
}

/**
 * Save settings to Tauri Store or localStorage fallback.
 * Never logs API keys.
 */
async function saveToStorage(
  settings: CanvasLearningSettings
): Promise<void> {
  try {
    // Tauri Store v2 API uses load() factory
    const { load } = await import("@tauri-apps/plugin-store");
    const store = await load("settings.json");
    await store.set(STORAGE_KEY, settings);
    await store.save();
  } catch {
    // Tauri not available — use localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }
}

export interface UseSettingsReturn {
  /** Current settings state. */
  settings: CanvasLearningSettings;
  /** Whether settings are still loading. */
  loading: boolean;
  /** Update one or more settings fields and persist. */
  updateSettings: (
    partial: Partial<CanvasLearningSettings>
  ) => Promise<void>;
  /** Sync current model config to the backend. Returns true on success. */
  syncToBackend: () => Promise<boolean>;
}

/**
 * Hook for managing application settings with local persistence.
 *
 * Automatically syncs model config to the backend when chat/scoring
 * provider, model, or API key changes.
 */
export function useSettings(): UseSettingsReturn {
  const [settings, setSettings] =
    useState<CanvasLearningSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  // Load settings on mount
  useEffect(() => {
    loadFromStorage().then((loaded) => {
      setSettings(loaded);
      setLoading(false);

      // Update API client base URL
      getApiClient(loaded.backendUrl);
    });
  }, []);

  const updateSettings = useCallback(
    async (partial: Partial<CanvasLearningSettings>) => {
      const updated = { ...settingsRef.current, ...partial };
      setSettings(updated);
      settingsRef.current = updated;

      // Persist locally
      await saveToStorage(updated);

      // Update API client if backend URL changed
      if (partial.backendUrl !== undefined) {
        getApiClient(partial.backendUrl);
      }

      // Auto-sync model config to backend if model-related fields changed
      const modelFields: (keyof CanvasLearningSettings)[] = [
        "chatProvider",
        "chatModel",
        "chatApiKey",
        "scoringProvider",
        "scoringModel",
        "scoringApiKey",
      ];
      const hasModelChange = modelFields.some(
        (key) => key in partial
      );
      if (hasModelChange) {
        // Fire and forget — sync failure doesn't block local save (AC-8)
        const client = getApiClient();
        client.postModelConfig(updated).catch(() => {
          // Sync failed — this is acceptable per AC-8
        });
      }
    },
    []
  );

  const syncToBackend = useCallback(async (): Promise<boolean> => {
    const client = getApiClient();
    return client.postModelConfig(settingsRef.current);
  }, []);

  return { settings, loading, updateSettings, syncToBackend };
}
