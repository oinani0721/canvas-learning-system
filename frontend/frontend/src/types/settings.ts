/**
 * Canvas Learning System - Settings Types
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * Type definitions for application settings stored locally via Tauri Store.
 * API keys are stored in the local app config only (never plaintext in logs).
 *
 * [Source: Story 1.3 Task 10.1 / 10.2]
 */

/** Supported LLM providers. */
export type LLMProvider = "gemini" | "anthropic" | "openai" | "ollama";

/** Full application settings interface. */
export interface CanvasLearningSettings {
  /** Chat model provider */
  chatProvider: LLMProvider;
  /** Chat model name (e.g. "gemini-2.0-flash") */
  chatModel: string;
  /** Chat model API key */
  chatApiKey: string;

  /** Scoring model provider */
  scoringProvider: LLMProvider;
  /** Scoring model name */
  scoringModel: string;
  /** Scoring model API key */
  scoringApiKey: string;

  /** Backend API base URL */
  backendUrl: string;
  /** Neo4j Bolt connection URI */
  neo4jUrl: string;

  /** Whether the API key security notice has been shown */
  apiKeyNoticeShown: boolean;
}

/** Default settings values. */
export const DEFAULT_SETTINGS: CanvasLearningSettings = {
  chatProvider: "gemini",
  chatModel: "",
  chatApiKey: "",
  scoringProvider: "gemini",
  scoringModel: "",
  scoringApiKey: "",
  backendUrl: "http://localhost:8001",
  neo4jUrl: "bolt://localhost:7689",
  apiKeyNoticeShown: false,
};
