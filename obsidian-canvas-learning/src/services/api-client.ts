/**
 * Canvas Learning System - API Client
 * Story 1.1: Plugin scaffold (AC-4)
 * Story 1.3: Model config sync + LLM test (AC-8, AC-3/AC-4)
 * Story 5.2: Mastery WebSocket + getBoardMastery (AC-2, Task 6/7)
 *
 * Provides REST communication with the FastAPI backend.
 * Handles snake_case <-> camelCase conversion and the API envelope format.
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 10.3]
 */

import type { ApiResponse, HealthResponse } from '../types/api';
import type { CanvasLearningSettings } from '../types/settings';
import type { NodeMasteryData } from '../stores/mastery-state.svelte';
import { masteryState } from '../stores/mastery-state.svelte';

/** Convert snake_case keys to camelCase. */
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
}

/** Convert camelCase keys to snake_case. */
function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

/** Recursively convert object keys. */
function convertKeys(
  obj: unknown,
  converter: (key: string) => string,
): unknown {
  if (Array.isArray(obj)) {
    return obj.map((item) => convertKeys(item, converter));
  }
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      result[converter(key)] = convertKeys(value, converter);
    }
    return result;
  }
  return obj;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl = 'http://localhost:8001') {
    this.baseUrl = baseUrl;
  }

  /**
   * Perform a GET request to the backend.
   * Response keys are converted from snake_case to camelCase.
   */
  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const raw = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Perform a POST request to the backend.
   * Request keys are converted from camelCase to snake_case.
   * Response keys are converted from snake_case to camelCase.
   */
  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const raw = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Check backend system health (AC-4).
   * Returns the health response or null if the backend is unreachable.
   */
  async checkHealth(): Promise<HealthResponse | null> {
    try {
      const envelope = await this.get<ApiResponse<HealthResponse>>(
        '/api/v1/system/health',
      );
      return envelope.data;
    } catch {
      return null;
    }
  }

  /**
   * Update the base URL used for all API requests.
   * Called when the user changes the backend address in Settings.
   *
   * [Source: Story 1.3 AC-7]
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  /**
   * Sync model configuration to the backend (Story 1.3 AC-8).
   *
   * Sends the current chat + scoring model settings so the backend
   * can update its in-memory LiteLLM runtime config.
   *
   * [Source: Story 1.3 Task 10.3 — postModelConfig()]
   *
   * @returns true if the sync succeeded, false otherwise.
   */
  async postModelConfig(settings: CanvasLearningSettings): Promise<boolean> {
    try {
      await this.post('/api/v1/system/config', {
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
   * Test an LLM connection via the backend (Story 1.3 AC-3 / AC-4).
   *
   * [Source: Story 1.3 Task 10.3 — testLlmConnection()]
   *
   * @returns An object with `status` ("success" | "failed") and
   *          an optional `error` message.
   */
  async testLlmConnection(
    provider: string,
    modelName: string,
    apiKey: string,
  ): Promise<{ status: string; error?: string; model?: string }> {
    try {
      const envelope = await this.post<
        ApiResponse<{ status: string; error?: string; model?: string }>
      >('/api/v1/system/test-llm', {
        provider,
        modelName,
        apiKey,
      });
      return envelope.data;
    } catch (err) {
      return {
        status: 'failed',
        error: err instanceof Error ? err.message : 'Unknown error',
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 5.2: Mastery Data (AC-2, Task 6 + Task 7)
  // ═══════════════════════════════════════════════════════════════════════════

  /** Active WebSocket connection (null when disconnected). */
  private ws: WebSocket | null = null;

  /** Whether a reconnect attempt is scheduled. */
  private wsReconnectTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Get the WebSocket URL derived from the REST base URL.
   * Converts http(s) -> ws(s) and appends the /ws path.
   */
  private getWsUrl(): string {
    return this.baseUrl
      .replace(/^http/, 'ws')
      .concat('/ws');
  }

  /**
   * Open a WebSocket connection to the backend.
   * Automatically handles `mastery_update` messages by updating the
   * masteryState store. On disconnect, cached mastery data is preserved
   * (not cleared) and a reconnect is scheduled.
   *
   * [Source: Story 5.2 Task 6 — WebSocket mastery_update]
   */
  connectWebSocket(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return; // already connected
    }

    try {
      this.ws = new WebSocket(this.getWsUrl());
    } catch (err) {
      console.warn('[Canvas Learning] WebSocket connection failed:', err);
      this.scheduleReconnect();
      return;
    }

    this.ws.onmessage = (event: MessageEvent) => {
      this.handleWebSocketMessage(event.data);
    };

    this.ws.onclose = () => {
      console.warn(
        '[Canvas Learning] WebSocket disconnected — mastery cache preserved, scheduling reconnect',
      );
      this.ws = null;
      this.scheduleReconnect();
    };

    this.ws.onerror = (err) => {
      console.warn('[Canvas Learning] WebSocket error:', err);
      // onclose will fire after onerror, so reconnect is handled there
    };
  }

  /**
   * Parse and dispatch incoming WebSocket messages.
   * Only processes `mastery_update` type; other message types are ignored
   * (future Stories will add more handlers).
   *
   * Expected payload format (snake_case from backend):
   * ```json
   * {
   *   "type": "mastery_update",
   *   "node_id": "abc-123",
   *   "effective_proficiency": 0.75,
   *   "has_interaction": true,
   *   "has_exam_record": true,
   *   "fsrs_next_review": "2026-03-20T00:00:00Z"
   * }
   * ```
   */
  private handleWebSocketMessage(raw: string): void {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(raw);
    } catch {
      console.warn('[Canvas Learning] WebSocket: failed to parse message');
      return;
    }

    if (parsed.type !== 'mastery_update') {
      return; // not our concern
    }

    // Convert snake_case payload to camelCase
    const converted = convertKeys(parsed, snakeToCamel) as Record<
      string,
      unknown
    >;

    const nodeId = converted.nodeId as string | undefined;
    if (!nodeId) {
      console.warn(
        '[Canvas Learning] WebSocket mastery_update missing nodeId',
      );
      return;
    }

    const data: Partial<NodeMasteryData> = {};
    if (typeof converted.effectiveProficiency === 'number') {
      data.effectiveProficiency = converted.effectiveProficiency;
    } else if (converted.effectiveProficiency === null) {
      data.effectiveProficiency = null;
    }
    if (typeof converted.hasInteraction === 'boolean') {
      data.hasInteraction = converted.hasInteraction;
    }
    if (typeof converted.hasExamRecord === 'boolean') {
      data.hasExamRecord = converted.hasExamRecord;
    }
    if (
      typeof converted.fsrsNextReview === 'string' ||
      converted.fsrsNextReview === null
    ) {
      data.fsrsNextReview = converted.fsrsNextReview as string | null;
    }

    masteryState.updateNodeMastery(nodeId, data);
  }

  /**
   * Schedule a WebSocket reconnect after a delay.
   * Uses a 5-second backoff. Only one timer is active at a time.
   */
  private scheduleReconnect(): void {
    if (this.wsReconnectTimer !== null) {
      return; // already scheduled
    }
    this.wsReconnectTimer = setTimeout(() => {
      this.wsReconnectTimer = null;
      this.connectWebSocket();
    }, 5000);
  }

  /**
   * Close the WebSocket connection and cancel any pending reconnect.
   * Called during plugin unload.
   */
  disconnectWebSocket(): void {
    if (this.wsReconnectTimer !== null) {
      clearTimeout(this.wsReconnectTimer);
      this.wsReconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null; // prevent reconnect on intentional close
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Fetch mastery data for all nodes on a board (Story 5.2 Task 7).
   *
   * GET /api/v1/mastery/board/{boardId}
   *
   * Graceful degradation (NFR-REL-02): when the backend is unreachable,
   * returns an empty result set so all nodes default to "unlearned" color.
   * This is intentional fallback behavior — the real API call is attempted
   * first and only falls back on network/server errors.
   *
   * @param boardId - The canvas board identifier.
   */
  async getBoardMastery(
    boardId: string,
  ): Promise<Array<{ nodeId: string } & NodeMasteryData>> {
    try {
      const envelope = await this.get<
        ApiResponse<Array<{ nodeId: string } & NodeMasteryData>>
      >(`/api/v1/mastery/board/${encodeURIComponent(boardId)}`);
      return envelope.data;
    } catch {
      // NFR-REL-02 degradation: backend unreachable -> nodes show default color
      console.warn(
        `[Canvas Learning] Failed to fetch mastery for board "${boardId}" — degrading to default node colors`,
      );
      return new Array<{ nodeId: string } & NodeMasteryData>();
    }
  }
}
