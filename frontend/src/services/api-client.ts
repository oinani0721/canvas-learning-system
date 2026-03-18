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

// [CHANGED] All types defined inline - no external imports needed
// See v1-ref/src/types/api.d.ts and v1-ref/src/types/canvas.d.ts for originals

export interface ApiResponse<T> { data: T; meta: { timestamp: string } }
export interface ComponentStatus { name: string; status: 'healthy' | 'unhealthy' | 'unknown'; message?: string }
export interface HealthResponse { status: 'healthy' | 'degraded' | 'unhealthy'; components: ComponentStatus[]; timestamp: string }
export interface ImageIndexResult { nodeId: string; ocrText: string; summary: string; concepts: string[]; processingTimeMs: number }
export interface SyncOperation { operationId: string; entityType: 'node' | 'edge' | 'board'; entityId: string; operation: 'create' | 'update' | 'delete'; payload: Record<string, unknown>; timestamp: string }
export interface SyncBatchRequest { canvasId: string; subjectId?: string | null; operations: SyncOperation[] }
export interface SyncOperationResult { operationId: string; success: boolean; error?: string | null }
export interface SyncBatchResponse { results: SyncOperationResult[]; syncedCount: number; failedCount: number }
export interface Recommendation { id: string; sourceNodeId: string; sourceNodeTitle: string; targetNodeId: string; targetNodeTitle: string; confidence: number; reason: string; suggestedLabel: string }
export interface RecommendationResponse { recommendations: Recommendation[]; canvasId: string; analyzedAt: string }
export interface ProfileSummary { conceptId: string; name: string; masteryLevel: number; masteryLabel: string; masteryColor: string; effectiveProficiency: number; prescriptiveMessage: string; interactionCount: number; examCount: number; lastExamDate: string | null; fsrsDueDate: string | null; freshness: string }
export interface TipItem { tipId: string; content: string; category: string; annotatedAt: string; contextMessages: string[] }
export interface WeaknessItem { direction: string; frequency: number; lastSeen: string | null; relatedExamSummaries: string[] }
export interface QAHighlight { question: string; answer: string; extractedAt: string }
export interface QAHighlightCluster { topic: string; qaPairs: QAHighlight[] }
export interface ExamSession { id: string; sourceBoardId: string; sourceBoardName: string; mode: 'point-to-point' | 'comprehensive' | 'mixed'; status: 'in-progress' | 'completed'; nodesExamined: number; masteryChangeSummary: string; createdAt: string; completedAt?: string }
export interface MasteryBatchResponse { concepts: MasteryConceptResponse[]; topicSummary: Record<string, { avgProficiency: number; conceptCount: number; examWeight: number }> }
export interface MasteryConceptResponse { conceptId: string; name: string; topic: string; effectiveProficiency: number; masteryLevel: number; masteryLabel: string; masteryColor: string; retrievability: number; freshness: string; fsrsDueDate: string | null; overrideActive: boolean; overrideValue: number | null; selfAssessValue: number | null; falseMasteryRisk: number; interactionCount: number; fluentCount: number; pMastery: number; lastInteractionTs: string | null }
export interface NodeMasteryData { effectiveProficiency: number | null; hasInteraction: boolean; hasExamRecord: boolean; fsrsNextReview: string | null }
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
  /** [CHANGED] Callback replaces v1 direct masteryState Svelte store import */
  private onMasteryUpdate: MasteryUpdateCallback | null = null;
  /** Story 4-2: Callback for edge label updates from WebSocket. */
  private onEdgeLabelUpdate: EdgeLabelUpdateCallback | null = null;

  /** [CHANGED] Parameter renamed to backendUrl for clarity */
  constructor(backendUrl = 'http://localhost:8001') {
    this.baseUrl = backendUrl.replace(/\/+$/, '');
  }

  /** [CHANGED] New method - decouples from Svelte masteryState store */
  setMasteryUpdateCallback(cb: MasteryUpdateCallback): void {
    this.onMasteryUpdate = cb;
  }

  /** Story 4-2: Set callback for edge label updates via WebSocket. */
  setEdgeLabelUpdateCallback(cb: EdgeLabelUpdateCallback): void {
    this.onEdgeLabelUpdate = cb;
  }

  /**
   * Perform a GET request to the backend.
   * [CHANGED] Uses standard fetch() instead of Obsidian's requestUrl().
   * Response keys are converted from snake_case to camelCase.
   */
  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw: unknown = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Perform a POST request to the backend.
   * [CHANGED] Uses standard fetch() instead of Obsidian's requestUrl().
   */
  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw: unknown = await response.json();
    return convertKeys(raw, snakeToCamel) as T;
  }

  /**
   * Perform a PATCH request to the backend.
   * [CHANGED] Uses standard fetch() instead of Obsidian's requestUrl().
   */
  async patch<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(convertKeys(body, camelToSnake)),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const raw: unknown = await response.json();
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
    } catch {
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
  /** [CHANGED] Uses standard fetch() with AbortSignal now wired up */
  async indexImage(
    nodeId: string,
    imageData: string,
    signal?: AbortSignal,
  ): Promise<ImageIndexResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/index/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, image_data: imageData }),
      signal, // [CHANGED] was unused (_signal) in v1
    });

    if (!response.ok) {
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
