/**
 * Canvas Learning System - API Client
 * Adapted from v1-ref/src/services/api-client.ts
 *
 * Provides REST communication with the FastAPI backend.
 * Handles snake_case <-> camelCase conversion and the API envelope format.
 *
 * CHANGES FROM V1:
 * 1. [CHANGED] Replaced Obsidian requestUrl() with standard fetch() API
 * 2. [CHANGED] Removed all Obsidian/Svelte imports - types defined inline
 * 3. [CHANGED] WebSocket mastery updates use callback instead of Svelte store
 * 4. [CHANGED] Added AbortSignal support on indexImage()
 * 5. [CHANGED] backendUrl configurable via constructor (default 8001)
 * 6. [CHANGED] postModelConfig accepts ModelConfigPayload instead of full settings
 */

import { createLogger } from './logger';
import type {
  StartSessionResponse,
  SubmitAnswerResponse,
  VerificationProgress,
} from '../types';

// [CHANGED] All types defined inline - no external imports needed
// See v1-ref/src/types/api.d.ts and v1-ref/src/types/canvas.d.ts for originals
// EXCEPTION: EPIC-31 verification types live in ../types because they are
// shared with VerificationModal.tsx.

export interface ApiResponse<T> { data: T; meta: { timestamp: string } }
export interface ComponentStatus { name: string; status: 'healthy' | 'unhealthy' | 'unknown'; message?: string }
export interface HealthResponse { status: 'healthy' | 'degraded' | 'unhealthy'; components: ComponentStatus[]; timestamp: string }
export interface ImageIndexResult { nodeId: string; ocrText: string; summary: string; concepts: string[]; processingTimeMs: number }
export interface SyncOperation { operationId: string; entityType: 'node' | 'edge' | 'board'; entityId: string; operation: 'create' | 'update' | 'delete'; payload: Record<string, unknown>; timestamp: string }
export interface SyncBatchRequest { canvasId: string; subjectId?: string | null; operations: SyncOperation[] }
/**
 * FR-KG-04 Phase 12: three-value error classification for sync operations.
 * The backend attaches one of these to every failed op so the sync-engine
 * can pick a retry strategy without parsing the human-readable error string.
 */
export type SyncErrorClass =
  | 'VALIDATION_ERROR'
  | 'DEPENDENCY_MISSING'
  | 'TRANSIENT_ERROR';

export interface SyncOperationResult {
  operationId: string;
  success: boolean;
  error?: string | null;
  /**
   * FR-KG-04 Phase 12: failure classification. Optional so older backends
   * that do not yet emit this field still work (the sync-engine falls back
   * to TRANSIENT behavior when undefined).
   */
  errorClass?: SyncErrorClass | null;
  /**
   * fix-rag-transform-and-episode-isolation Phase 6: entity metadata
   * echoed back for memory-event dispatch. Optional.
   */
  entityType?: 'node' | 'edge' | 'board' | null;
  entityId?: string | null;
}
export interface SyncBatchResponse {
  results: SyncOperationResult[];
  syncedCount: number;
  failedCount: number;
}
export interface Recommendation { id: string; sourceNodeId: string; sourceNodeTitle: string; targetNodeId: string; targetNodeTitle: string; confidence: number; reason: string; suggestedLabel: string }
export interface RecommendationResponse { recommendations: Recommendation[]; canvasId: string; analyzedAt: string }
export interface ProfileSummary { conceptId: string; name: string; masteryLevel: number; masteryLabel: string; masteryColor: string; effectiveProficiency: number; prescriptiveMessage: string; interactionCount: number; examCount: number; lastExamDate: string | null; fsrsDueDate: string | null; freshness: string }
export interface TipItem { tipId: string; content: string; category: string; annotatedAt: string; contextMessages: string[]; sourceCanvasId?: string; sourceNodeId?: string }
export interface WeaknessItem { direction: string; frequency: number; lastSeen: string | null; relatedExamSummaries: string[]; sourceCanvasId?: string; sourceNodeId?: string }
export interface QAHighlight { question: string; answer: string; extractedAt: string }
export interface QAHighlightCluster { topic: string; qaPairs: QAHighlight[] }
export interface ExamSession { id: string; sourceBoardId: string; sourceBoardName: string; mode: 'point-to-point' | 'comprehensive' | 'mixed'; status: 'in-progress' | 'completed'; nodesExamined: number; masteryChangeSummary: string; createdAt: string; completedAt?: string }
export interface MasteryBatchResponse { concepts: MasteryConceptResponse[]; topicSummary: Record<string, { avgProficiency: number; conceptCount: number; examWeight: number }> }
export interface MasteryConceptResponse { conceptId: string; name: string; topic: string; effectiveProficiency: number; masteryLevel: number; masteryLabel: string; masteryColor: string; retrievability: number; freshness: string; fsrsDueDate: string | null; overrideActive: boolean; overrideValue: number | null; selfAssessValue: number | null; falseMasteryRisk: number; interactionCount: number; fluentCount: number; pMastery: number; lastInteractionTs: string | null }
export interface NodeMasteryData { effectiveProficiency: number | null; hasInteraction: boolean; hasExamRecord: boolean; fsrsNextReview: string | null }
/** A skill available for selection from the backend. */
export interface SkillItem { id: string; name: string; description: string; command: string; category?: string }

/** [CHANGED] Callback replaces direct masteryState Svelte store mutation */
export type MasteryUpdateCallback = (nodeId: string, data: Partial<NodeMasteryData>) => void;
/** [CHANGED] Slimmed from CanvasLearningSettings - only backend-relevant fields */
export interface ModelConfigPayload { chatProvider: string; chatModel: string; chatApiKey: string; scoringProvider: string; scoringModel: string; scoringApiKey: string }

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

/** Story 4-2: Callback for edge label updates via WebSocket. */
export type EdgeLabelUpdateCallback = (edgeId: string, relationType: string) => void;

export class ApiClient {
  private baseUrl: string;
  private readonly logger = createLogger('ApiClient');
  /** [CHANGED] Callback replaces v1 direct masteryState Svelte store import */
  private onMasteryUpdate: MasteryUpdateCallback | null = null;
  /** Story 4-2: Callback for edge label updates from WebSocket. */
  private onEdgeLabelUpdate: EdgeLabelUpdateCallback | null = null;
  /**
   * FR-KG-04 Phase 2: Device-scoped internal API key for sensitive backend
   * endpoints (currently /api/v1/sync/batch). Sent via the X-CLS-Internal-Key
   * header. Initialized via constructor or setInternalApiKey(); when null,
   * the header is omitted (the backend will reject with 403 in production).
   */
  private internalApiKey: string | null = null;

  /** [CHANGED] Parameter renamed to backendUrl for clarity */
  constructor(backendUrl = 'http://localhost:8001', internalApiKey?: string) {
    this.baseUrl = backendUrl.replace(/\/+$/, '');
    // FR-KG-04 Phase 2: Resolve internal API key from (1) explicit arg or
    // (2) Vite build-time env var VITE_INTERNAL_API_KEY. Falling back to env
    // lets every `new ApiClient()` call across the codebase pick up the key
    // automatically without threading it through every call site.
    // When neither is provided, the key stays null and requests to sensitive
    // endpoints will receive 403 in production (see backend/app/security.py).
    if (internalApiKey) {
      this.internalApiKey = internalApiKey;
    } else {
      const envKey =
        typeof import.meta !== 'undefined' &&
        import.meta.env?.VITE_INTERNAL_API_KEY;
      if (envKey) {
        this.internalApiKey = envKey;
      } else {
        this.logger.warn(
          'VITE_INTERNAL_API_KEY is not set — requests to /api/v1/sync/batch ' +
            'will be rejected with 403 in production. Configure this env var ' +
            'via your Tauri build or dev environment.',
        );
      }
    }
  }

  /**
   * FR-KG-04 Phase 2: Update the internal API key at runtime.
   *
   * Used by the Tauri startup flow when VITE_INTERNAL_API_KEY is provisioned
   * after the ApiClient was constructed (e.g. read from a secure store).
   */
  setInternalApiKey(key: string): void {
    this.internalApiKey = key || null;
  }

  /**
   * FR-KG-04 Phase 2: Build the headers dict for every outgoing request.
   *
   * Always includes Content-Type and X-Request-ID. Adds X-CLS-Internal-Key
   * when an internal key has been provisioned. Centralizing this logic here
   * means every fetch path picks up the auth header automatically.
   */
  private buildHeaders(requestId: string): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
    };
    if (this.internalApiKey) {
      headers['X-CLS-Internal-Key'] = this.internalApiKey;
    }
    return headers;
  }

  /**
   * Core HTTP request method. Injects X-Request-ID for frontend-backend correlation
   * and X-CLS-Internal-Key for sensitive endpoint auth (FR-KG-04 Phase 2).
   */
  private async request<T>(
    method: 'GET' | 'POST' | 'PATCH',
    path: string,
    body?: unknown,
    options?: { signal?: AbortSignal },
  ): Promise<T> {
    const requestId = crypto.randomUUID();
    const url = `${this.baseUrl}${path}`;

    this.logger.debug('request', { method, path, requestId });

    const init: RequestInit = {
      method,
      headers: this.buildHeaders(requestId),
      signal: options?.signal,
    };

    if (body !== undefined) {
      init.body = JSON.stringify(convertKeys(body, camelToSnake));
    }

    const response = await fetch(url, init);

    if (!response.ok) {
      this.logger.warn('response error', { method, path, status: response.status, requestId });
      throw new Error(`API error: ${response.status}`);
    }

    const raw: unknown = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /** [CHANGED] New method - decouples from Svelte masteryState store */
  setMasteryUpdateCallback(cb: MasteryUpdateCallback): void {
    this.onMasteryUpdate = cb;
  }

  /** Story 4-2: Set callback for edge label updates via WebSocket. */
  setEdgeLabelUpdateCallback(cb: EdgeLabelUpdateCallback): void {
    this.onEdgeLabelUpdate = cb;
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('POST', path, body);
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('PATCH', path, body);
  }

  /**
   * Check backend system health (AC-4).
   * Returns the health response or null if the backend is unreachable.
   */
  async checkHealth(): Promise<HealthResponse | null> {
    try {
      const envelope = await this.get<ApiResponse<HealthResponse>>(
        '/api/v1/health',
      );
      return envelope.data;
    } catch (err) {
      this.logger.debug('checkHealth failed — backend unreachable', err instanceof Error ? err.message : err);
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
  /** [CHANGED] Accepts ModelConfigPayload instead of CanvasLearningSettings */
  async postModelConfig(config: ModelConfigPayload): Promise<boolean> {
    try {
      await this.post('/api/v1/system/config', {
        chat: {
          provider: config.chatProvider,
          modelName: config.chatModel,
          apiKey: config.chatApiKey,
        },
        scoring: {
          provider: config.scoringProvider,
          modelName: config.scoringModel,
          apiKey: config.scoringApiKey,
        },
      });
      return true;
    } catch (err) {
      this.logger.warn('postModelConfig failed', err instanceof Error ? err.message : err);
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

    // Story 4-2: Edge label update from record_edge_rationale
    if (parsed.type === 'edge_label_update') {
      const converted = convertKeys(parsed, snakeToCamel) as Record<string, unknown>;
      const edgeId = converted.edgeId as string | undefined;
      const relationType = converted.relationType as string | undefined;
      if (edgeId && relationType && this.onEdgeLabelUpdate) {
        this.onEdgeLabelUpdate(edgeId, relationType);
      }
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

    // [CHANGED] Callback-based instead of direct Svelte store mutation
    if (this.onMasteryUpdate) {
      this.onMasteryUpdate(nodeId, data);
    }
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
  // Tips API — backend sync for tip annotations (MVP #5)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Save a tip annotation to the backend.
   * POST /api/v1/tips
   *
   * Graceful degradation: returns null on failure (localStorage still has it).
   */
  async saveTip(
    nodeId: string,
    content: string,
    tags: string[] = [],
  ): Promise<TipItem | null> {
    try {
      return await this.post<TipItem>('/api/v1/tips', {
        nodeId,
        content,
        tags,
      });
    } catch (err) {
      console.warn(
        '[Canvas Learning] Failed to save tip to backend:',
        err instanceof Error ? err.message : err,
      );
      return null;
    }
  }

  /**
   * Get tips for a node from the backend.
   * GET /api/v1/tips?node_id={nodeId}
   *
   * Graceful degradation: returns empty array on failure.
   */
  async getTips(nodeId: string): Promise<TipItem[]> {
    try {
      const result = await this.get<{ tips: TipItem[]; total: number }>(
        `/api/v1/tips?node_id=${encodeURIComponent(nodeId)}`,
      );
      return result.tips;
    } catch {
      console.warn(
        `[Canvas Learning] Failed to fetch tips for "${nodeId}" from backend`,
      );
      return new Array<TipItem>();
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Skills API — list available skills (MVP #13)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Get available skills from the backend.
   * GET /api/v1/skills
   *
   * Graceful degradation: returns empty array on failure.
   */
  async getSkills(): Promise<SkillItem[]> {
    try {
      const result = await this.get<{ skills: SkillItem[] }>('/api/v1/skills');
      return result.skills;
    } catch {
      console.warn('[Canvas Learning] Failed to fetch skills from backend');
      return new Array<SkillItem>();
    }
  }

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
  // Story 6.1-6.2: Exam Board APIs
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Story 6.1 AC-1: Create a new exam session from source canvas.
   */
  async startExam(sourceCanvasId: string, examMode: string, targetNodeId?: string): Promise<Record<string, unknown> | null> {
    try {
      return await this.post<Record<string, unknown>>('/api/v1/exam/start', {
        source_canvas_id: sourceCanvasId,
        exam_mode: examMode,
        target_node_id: targetNodeId || null,
      });
    } catch (err) {
      console.error('[Story 6.1] startExam failed:', err);
      return null;
    }
  }

  /**
   * Story 6.2 AC-2: Analyze canvas content for mode recommendation.
   */
  async analyzeCanvas(canvasId: string, targetNodeId?: string): Promise<{ contentType: string; recommendedMode: string; confidence: number } | null> {
    try {
      return await this.post<{ contentType: string; recommendedMode: string; confidence: number }>('/api/v1/exam/analyze-canvas', {
        canvas_id: canvasId,
        target_node_id: targetNodeId || null,
      });
    } catch (err) {
      this.logger.warn('analyzeCanvas failed', err instanceof Error ? err.message : err);
      return null;
    }
  }

  /**
   * Story 6.5 AC-2: Sync discovered node back to source canvas.
   */
  async syncExamNode(
    examId: string,
    payload: {
      examId: string;
      sourceCanvasId: string;
      nodeId: string;
      nodeText: string;
      sourceNodeId: string;
      suggestedRelation?: string;
    },
  ): Promise<Record<string, unknown> | null> {
    try {
      return await this.post<Record<string, unknown>>(`/api/v1/exam/${examId}/sync-node`, {
        exam_id: payload.examId,
        source_canvas_id: payload.sourceCanvasId,
        node_id: payload.nodeId,
        node_text: payload.nodeText,
        source_node_id: payload.sourceNodeId,
        suggested_relation: payload.suggestedRelation || 'related_to',
      });
    } catch (err) {
      console.error('[Story 6.5] syncExamNode failed:', err);
      return null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EPIC-31: Interactive Verification Session APIs (A4 Runbook)
  // Bridges VerificationModal.tsx ↔ backend review.py:1640-1807
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * EPIC-31 AC-1: Start an interactive verification session for a canvas.
   *
   * POST /api/v1/review/session/start (review.py:1640)
   * Returns sessionId + first AI-generated question, or null on failure.
   *
   * Phase 17.2 note: `canvasName` is sanitized server-side (rejects path
   * traversal like "../../etc/passwd" → resolves to sentinel ["默认概念"]),
   * so the frontend can pass user input through without pre-validation.
   */
  async startVerificationSession(
    canvasName: string,
    nodeIds?: string[] | null,
    includeMastered = true,
  ): Promise<StartSessionResponse | null> {
    try {
      return await this.post<StartSessionResponse>('/api/v1/review/session/start', {
        canvas_name: canvasName,
        node_ids: nodeIds ?? null,
        include_mastered: includeMastered,
      });
    } catch (err) {
      console.error('[EPIC-31] startVerificationSession failed:', err);
      return null;
    }
  }

  /**
   * EPIC-31 AC-2: Submit user answer and receive scoring result.
   *
   * POST /api/v1/review/session/{session_id}/answer (review.py:1719)
   * Returns score, quality, degraded flag, next question, or null on failure.
   *
   * Phase 17.1 fail-closed contract: When the scoring-agent is unreachable,
   * the response will contain `degraded=true`, `score=0`, `quality='unknown'`,
   * and a Chinese `degradedWarning` string. The UI must display the warning
   * prominently so users know the answer is not counted toward mastery.
   */
  async submitVerificationAnswer(
    sessionId: string,
    userAnswer: string,
  ): Promise<SubmitAnswerResponse | null> {
    try {
      return await this.post<SubmitAnswerResponse>(
        `/api/v1/review/session/${sessionId}/answer`,
        { user_answer: userAnswer },
      );
    } catch (err) {
      console.error('[EPIC-31] submitVerificationAnswer failed:', err);
      return null;
    }
  }

  /**
   * EPIC-31 AC-3: Poll current verification progress (used on modal reopen).
   *
   * GET /api/v1/review/session/{session_id}/progress
   * Returns a progress snapshot, or null on failure.
   */
  async getVerificationProgress(
    sessionId: string,
  ): Promise<VerificationProgress | null> {
    try {
      return await this.get<VerificationProgress>(
        `/api/v1/review/session/${sessionId}/progress`,
      );
    } catch (err) {
      console.error('[EPIC-31] getVerificationProgress failed:', err);
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
    signal?: AbortSignal,
  ): Promise<ImageIndexResult> {
    const requestId = crypto.randomUUID();
    this.logger.debug('request', { method: 'POST', path: '/api/v1/index/image', requestId });

    const response = await fetch(`${this.baseUrl}/api/v1/index/image`, {
      method: 'POST',
      // FR-KG-04 Phase 2: route through buildHeaders so X-CLS-Internal-Key
      // is injected on this side-path the same way as the main request().
      headers: this.buildHeaders(requestId),
      body: JSON.stringify({ node_id: nodeId, image_data: imageData }),
      signal,
    });

    if (!response.ok) {
      this.logger.warn('response error', { path: '/api/v1/index/image', status: response.status, requestId });
      throw new Error(`API error: ${response.status}`);
    }

    const raw: unknown = await response.json();
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
        recommendations: new Array<Recommendation>(),
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
        message.includes('Load failed') // [CHANGED] Safari fetch error pattern (replaced Obsidian-specific pattern)
      ) {
        throw new SyncNetworkError(message);
      }
      throw new SyncServerError(message);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 4-2: Edge Rationale Recording API
  // [Source: _bmad-output/implementation-artifacts/4-2-edge-dialog-agent-reasoning.md#Task 2]
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Record an edge rationale via dual-write (Graphiti + LanceDB).
   * POST /api/v1/edges/record-rationale
   *
   * Graceful degradation: returns a failure result on network error
   * instead of throwing (edge dialog continues working).
   */
  async recordEdgeRationale(params: {
    edgeId: string;
    sourceNodeId: string;
    targetNodeId: string;
    sourceConcept: string;
    targetConcept: string;
    relationType: string;
    rationaleText: string;
    confidence: number;
    strategiesApplied?: string[];
    questioningRounds?: number;
    explanationDepthScore?: number;
  }): Promise<EdgeRationaleResult> {
    try {
      return await this.post<EdgeRationaleResult>(
        '/api/v1/edges/record-rationale',
        params,
      );
    } catch (err) {
      console.warn(
        '[Canvas Learning] Edge rationale recording failed:',
        err instanceof Error ? err.message : err,
      );
      return {
        recordId: '',
        edgeId: params.edgeId,
        relationType: params.relationType,
        graphitiStatus: { success: false, error: 'Network error' },
        lancedbStatus: { success: false, error: 'Network error' },
        timestamp: new Date().toISOString(),
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // F9: Conversation Distillation Trigger
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * F9: Trigger conversation distillation for a node after dialogue ends.
   * Sends message history to backend for LLM-based extraction of summary,
   * tips, errors, and Q&A highlights. Results are persisted for Edge inheritance.
   * Fire-and-forget: returns null on any failure (non-blocking).
   */
  async triggerDistillation(
    nodeId: string,
    messages: { role: string; content: string }[],
  ): Promise<{ success: boolean; summary: string } | null> {
    try {
      return await this.post<{ success: boolean; summary: string }>(
        `/api/v1/chat/${encodeURIComponent(nodeId)}/distill`,
        { messages },
      );
    } catch (err) {
      console.warn('[F9] triggerDistillation failed (non-blocking):', err);
      return null;
    }
  }
}

/** Response from record_edge_rationale endpoint. */
export interface EdgeRationaleResult {
  recordId: string;
  edgeId: string;
  relationType: string;
  graphitiStatus: { success: boolean; error?: string | null };
  lancedbStatus: { success: boolean; error?: string | null };
  timestamp: string;
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
