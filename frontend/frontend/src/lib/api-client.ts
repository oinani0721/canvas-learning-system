/**
 * Canvas Learning System - API Client (React/Tauri frontend)
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * REST client for communicating with the FastAPI backend.
 * Handles snake_case <-> camelCase conversion and the API envelope format.
 *
 * [Source: Story 1.3 Task 10.3 — postModelConfig() + testLlmConnection()]
 * [Source: backend/app/api/v1/system.py — endpoint contracts]
 */

import type {
  ApiResponse,
  HealthResponse,
  TestLlmResult,
  LlmStatsResponse,
} from "@/types/api";
import type { CanvasLearningSettings } from "@/types/settings";

/** Convert snake_case keys to camelCase. */
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
}

/** Convert camelCase keys to snake_case. */
function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

/** Recursively convert object keys using the given converter function. */
function convertKeys(
  obj: unknown,
  converter: (key: string) => string
): unknown {
  if (Array.isArray(obj)) {
    return obj.map((item) => convertKeys(item, converter));
  }
  if (obj !== null && typeof obj === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(
      obj as Record<string, unknown>
    )) {
      result[converter(key)] = convertKeys(value, converter);
    }
    return result;
  }
  return obj;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl = "http://localhost:8001") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  /** Update the base URL for all subsequent API requests. */
  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, "");
  }

  /** GET request with snake_case -> camelCase response conversion. */
  private async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const raw = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /** POST request with camelCase -> snake_case body conversion. */
  private async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const raw = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Check backend system health.
   * Returns the health response or null if the backend is unreachable.
   *
   * [Source: Story 1.3 AC-2 — health check for 5 components]
   */
  async checkHealth(): Promise<HealthResponse | null> {
    try {
      const envelope = await this.get<ApiResponse<HealthResponse>>(
        "/api/v1/system/health"
      );
      return envelope.data;
    } catch {
      return null;
    }
  }

  /**
   * Sync model configuration to the backend.
   *
   * Sends the current chat + scoring model settings so the backend
   * can update its in-memory LiteLLM runtime config.
   *
   * [Source: Story 1.3 AC-8 — model config sync]
   * [Source: Story 1.3 Task 10.3 — postModelConfig()]
   *
   * @returns true if the sync succeeded, false otherwise.
   */
  async postModelConfig(settings: CanvasLearningSettings): Promise<boolean> {
    try {
      await this.post("/api/v1/system/config", {
        chat: {
          provider: settings.chatProvider,
          modelName: settings.chatModel,
          apiKey: settings.chatApiKey,
        },
        scoring: {
          provider: settings.scoringProvider,
          modelName: settings.scoringModel,
          apiKey: settings.scoringApiKey,
        },
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get LLM usage statistics from the backend.
   *
   * Supports period filtering: today, week, month, custom.
   * Graceful degradation: returns null when backend is unreachable.
   *
   * [Source: Story 3.12 Task 2.1 — getLlmStats()]
   * [Source: backend/app/api/v1/system.py — GET /api/v1/system/llm-stats]
   */
  async getLlmStats(
    period: "today" | "week" | "month" = "today",
    taskType?: string
  ): Promise<LlmStatsResponse | null> {
    try {
      const params = new URLSearchParams({ period });
      if (taskType) {
        params.set("task_type", taskType);
      }
      return await this.get<LlmStatsResponse>(
        `/api/v1/system/llm-stats?${params.toString()}`
      );
    } catch {
      return null;
    }
  }

  /**
   * Test an LLM connection via the backend.
   *
   * [Source: Story 1.3 AC-3 / AC-4 — test connection button]
   * [Source: Story 1.3 Task 10.3 — testLlmConnection()]
   */
  async testLlmConnection(
    provider: string,
    modelName: string,
    apiKey: string
  ): Promise<TestLlmResult> {
    try {
      const envelope = await this.post<ApiResponse<TestLlmResult>>(
        "/api/v1/system/test-llm",
        { provider, modelName, apiKey }
      );
      return envelope.data;
    } catch (err) {
      return {
        status: "failed",
        error: err instanceof Error ? err.message : "Unknown error",
      };
    }
  }
}

/** Singleton API client instance. */
let apiClientInstance: ApiClient | null = null;

/**
 * Get or create the API client singleton.
 * Optionally update the base URL.
 */
export function getApiClient(baseUrl?: string): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient(baseUrl);
  } else if (baseUrl) {
    apiClientInstance.setBaseUrl(baseUrl);
  }
  return apiClientInstance;
}
