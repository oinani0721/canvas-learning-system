/**
 * Canvas Learning System - API Client
 * Story 1.1: Plugin scaffold (AC-4)
 * Story 1.3: Model config sync + LLM test (AC-8, AC-3/AC-4)
 * Story 1.5: Sync batch API (AC-7)
 * Story 5.2: Mastery WebSocket + getBoardMastery (AC-2, Task 6/7)
 *
 * Provides REST communication with the FastAPI backend.
 * Handles snake_case <-> camelCase conversion and the API envelope format.
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 10.3]
 */

import { requestUrl, type RequestUrlResponse } from 'obsidian';
import type {
  ApiResponse,
  HealthResponse,
  ImageIndexResult,
  SyncBatchRequest,
  SyncBatchResponse,
} from '../types/api';
import type { RecommendationResponse } from '../types/canvas';
import type { CanvasLearningSettings } from '../types/settings';
import type { NodeMasteryData } from '../stores/mastery-state.svelte';
import type {
  ExamSession,
  MasteryBatchResponse,
  ProfileSummary,
  QAHighlightCluster,
  TipItem,
  WeaknessItem,
} from '../types/canvas';
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
   * Uses Obsidian's requestUrl to bypass Electron CSP restrictions.
   * Response keys are converted from snake_case to camelCase.
   */
  async get<T>(path: string): Promise<T> {
    const response: RequestUrlResponse = await requestUrl({
      url: `${this.baseUrl}${path}`,
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (response.status < 200 || response.status >= 300) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw = response.json;
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Perform a POST request to the backend.
   * Uses Obsidian's requestUrl to bypass Electron CSP restrictions.
   * Request keys are converted from camelCase to snake_case.
   * Response keys are converted from snake_case to camelCase.
   */
  async post<T>(path: string, body: unknown): Promise<T> {
    const response: RequestUrlResponse = await requestUrl({
      url: `${this.baseUrl}${path}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (response.status < 200 || response.status >= 300) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw = response.json;
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Perform a PATCH request to the backend.
   * Uses Obsidian's requestUrl to bypass Electron CSP restrictions.
   * Story 6.1: Exam session status updates.
   * Request keys are converted from camelCase to snake_case.
   * Response keys are converted from snake_case to camelCase.
   */
  async patch<T>(path: string, body: unknown): Promise<T> {
    const response: RequestUrlResponse = await requestUrl({
      url: `${this.baseUrl}${path}`,
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (response.status < 200 || response.status >= 300) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw = response.json;
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

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 1.5: Sync Batch API (AC-7)
  // [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 7]
  // ═══════════════════════════════════════════════════════════════════════════

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 5.3: Profile API (Learning Profile Panel)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Get mastery summary for a node's learning profile.
   * Returns prescriptive (supportive) language, not raw numbers.
   */
  async getProfileSummary(nodeId: string): Promise<ProfileSummary | null> {
    try {
      return await this.get<ProfileSummary>(
        `/api/v1/profile/${encodeURIComponent(nodeId)}/summary`,
      );
    } catch {
      console.warn(`[Canvas Learning] Failed to fetch profile summary for "${nodeId}"`);
      return null;
    }
  }

  /**
   * Get tips annotations for a node from Graphiti.
   * NFR-REL-02: Returns empty result on backend failure (degradation).
   */
  async getProfileTips(nodeId: string): Promise<{ tips: TipItem[]; total: number }> {
    try {
      return await this.get<{ tips: TipItem[]; total: number }>(
        `/api/v1/profile/${encodeURIComponent(nodeId)}/tips`,
      );
    } catch {
      console.warn(`[Canvas Learning] Failed to fetch tips for "${nodeId}"`);
      return { tips: new Array<TipItem>(), total: 0 };
    }
  }

  /**
   * Get weakness patterns for a node (positive framing).
   * NFR-REL-02: Returns empty result on backend failure (degradation).
   */
  async getProfileWeaknesses(nodeId: string): Promise<{ weaknesses: WeaknessItem[]; total: number }> {
    try {
      return await this.get<{ weaknesses: WeaknessItem[]; total: number }>(
        `/api/v1/profile/${encodeURIComponent(nodeId)}/weaknesses`,
      );
    } catch {
      console.warn(`[Canvas Learning] Failed to fetch weaknesses for "${nodeId}"`);
      return { weaknesses: new Array<WeaknessItem>(), total: 0 };
    }
  }

  /**
   * Get key Q&A highlights for a node, clustered by topic.
   * NFR-REL-02: Returns empty result on backend failure (degradation).
   */
  async getProfileQAHighlights(nodeId: string): Promise<{ clusters: QAHighlightCluster[]; total: number }> {
    try {
      return await this.get<{ clusters: QAHighlightCluster[]; total: number }>(
        `/api/v1/profile/${encodeURIComponent(nodeId)}/qa-highlights`,
      );
    } catch {
      console.warn(`[Canvas Learning] Failed to fetch QA highlights for "${nodeId}"`);
      return { clusters: new Array<QAHighlightCluster>(), total: 0 };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 5.4: Dashboard API (FSRS Review Dashboard)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Get all exam sessions, optionally filtered by board ID.
   * NFR-REL-02: Returns empty list when backend is unreachable (offline degradation).
   */
  async getExamSessions(boardId?: string): Promise<ExamSession[]> {
    try {
      const query = boardId ? `?board_id=${encodeURIComponent(boardId)}` : '';
      const result = await this.get<{ sessions: ExamSession[]; total: number }>(
        `/api/v1/exam_sessions${query}`,
      );
      return result.sessions;
    } catch {
      console.warn('[Canvas Learning] Failed to fetch exam sessions — backend may be offline');
      return new Array<ExamSession>();
    }
  }

  /**
   * Get batch mastery data for all concepts (used by Dashboard review tab).
   * Returns null when backend is unreachable.
   */
  async getMasteryBatch(): Promise<MasteryBatchResponse | null> {
    try {
      return await this.get<MasteryBatchResponse>('/api/v1/mastery/batch');
    } catch {
      console.warn('[Canvas Learning] Failed to fetch mastery batch — backend may be offline');
      return null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 1.6: Image Index API (AC-4)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Submit an image for OCR indexing.
   *
   * POST /api/v1/index/image
   *
   * @param nodeId - The image node ID.
   * @param imageData - Base64 DataURL of the image.
   * @param signal - Optional AbortSignal for cancellation.
   */
  async indexImage(
    nodeId: string,
    imageData: string,
    _signal?: AbortSignal,
  ): Promise<ImageIndexResult> {
    const response: RequestUrlResponse = await requestUrl({
      url: `${this.baseUrl}/api/v1/index/image`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, image_data: imageData }),
    });

    if (response.status < 200 || response.status >= 300) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw = response.json;
    return convertKeys(raw, snakeToCamel) as ImageIndexResult;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 1.7: Recommendation API (AC-1)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Fetch concept-relation recommendations for a canvas board.
   *
   * POST /api/v1/canvas/{canvasId}/recommendations
   *
   * Silent degradation: returns empty recommendations on any error.
   */
  async fetchRecommendations(
    canvasId: string,
    dismissedPairs: Array<{ nodeIdA: string; nodeIdB: string }>,
  ): Promise<RecommendationResponse> {
    try {
      return await this.post<RecommendationResponse>(
        `/api/v1/canvas/${encodeURIComponent(canvasId)}/recommendations`,
        { dismissedPairs },
      );
    } catch {
      console.warn('[Canvas Learning] Recommendation fetch failed — silent degradation');
      return {
        recommendations: new Array<import('../types/canvas').Recommendation>(),
        canvasId,
        analyzedAt: new Date().toISOString(),
      };
    }
  }

  /**
   * Send a batch of sync operations to the backend for Neo4j persistence.
   *
   * POST /api/v1/sync/batch
   *
   * Throws SyncNetworkError on network failures and SyncServerError on
   * server-side errors (5xx). The caller (SyncEngine) uses these to
   * decide retry vs. offline behavior.
   *
   * @param request - The batch sync request.
   * @returns SyncBatchResponse with per-operation results.
   */
  async syncBatch(request: SyncBatchRequest): Promise<SyncBatchResponse> {
    try {
      return await this.post<SyncBatchResponse>(
        '/api/v1/sync/batch',
        request,
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (
        message.includes('Failed to fetch') ||
        message.includes('NetworkError') ||
        message.includes('ERR_CONNECTION_REFUSED') ||
        message.includes('net::') ||
        message.includes('ECONNREFUSED') ||
        message.includes('request to') // Obsidian requestUrl network error
      ) {
        throw new SyncNetworkError(message);
      }
      throw new SyncServerError(message);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Story 1.5: Sync Error Types
// ═══════════════════════════════════════════════════════════════════════════════

/** Network-level error (backend unreachable). */
export class SyncNetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SyncNetworkError';
  }
}

/** Server-side error (5xx response). */
export class SyncServerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SyncServerError';
  }
}
