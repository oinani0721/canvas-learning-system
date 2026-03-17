/**
 * Canvas Learning System - Settings Type Definitions
 * Story 1.3: Model Configuration & System Settings Panel (AC-1 ~ AC-8)
 *
 * Defines the plugin settings interface and default values.
 * Settings are persisted in Obsidian's local data.json file.
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 10]
 */

/** Supported LLM provider identifiers. */
export type LLMProvider = 'gemini' | 'anthropic' | 'openai' | 'ollama';

/**
 * Plugin settings stored in Obsidian's data.json.
 *
 * Dual-layer key architecture:
 * - Chat model: used by Agent SDK for user conversations (outer layer)
 * - Scoring model: synced to backend for evaluation/extraction tasks (inner layer)
 *
 * [Source: architecture.md#Technical Constraints & Dependencies - dual-layer key separation]
 */
export interface CanvasLearningSettings {
  // ---- Chat model (outer layer) ----
  chatProvider: LLMProvider;
  chatModel: string;
  chatApiKey: string;

  // ---- Scoring model (inner layer) ----
  scoringProvider: LLMProvider;
  scoringModel: string;
  scoringApiKey: string;

  // ---- Backend connection ----
  backendUrl: string;
  neo4jUrl: string;

  // ---- Story 3.9: Engine Fallback ----
  /** Backup Anthropic API Key for fallback when CLI spawn fails. */
  fallbackApiKey: string;
  /** Current active engine type. */
  currentEngine: 'claude-code' | 'api-key';

  // ---- Internal flags ----
  /** Whether the user has been shown the API key security notice. */
  apiKeyNoticeShown: boolean;

  // ---- Story 1.9: Multi-subject settings ----
  subjects: Array<{ id: string; name: string; createdAt: string; isDefault: boolean }>;
  activeSubjectId: string | null;
  crossSubjectEnabled: boolean;
  crossSubjectThreshold: number;
}

/** Default settings applied on first install. */
export const DEFAULT_SETTINGS: CanvasLearningSettings = {
  chatProvider: 'gemini',
  chatModel: '',
  chatApiKey: '',
  scoringProvider: 'gemini',
  scoringModel: '',
  scoringApiKey: '',
  backendUrl: 'http://localhost:8001',
  neo4jUrl: 'bolt://localhost:7689',
  fallbackApiKey: '',
  currentEngine: 'claude-code',
  apiKeyNoticeShown: false,
  // Story 1.9 defaults
  subjects: [{ id: 'default-general', name: '通用', createdAt: new Date().toISOString(), isDefault: true }],
  activeSubjectId: null,
  crossSubjectEnabled: false,
  crossSubjectThreshold: 0.3,
};
