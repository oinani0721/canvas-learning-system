/**
 * Canvas Learning System - API Client
 *
 * HTTP client for communicating with the FastAPI backend.
 * Implements all 22 API endpoints with retry mechanism and error handling.
 * (19 original + 3 RAG endpoints from Story 12.5)
 *
 * @source Story 13.3 - API客户端实现
 * @verified specs/api/canvas-api.openapi.yml
 *
 * Architecture context:
 * ├── PluginCore (CanvasReviewPlugin)
 * ├── CommandWrapper (命令包装层) ← depends on ApiClient
 * ├── DataManager (数据管理层)
 * ├── UIManager (UI组件层) ← depends on ApiClient
 * └── ApiClient (this file) ⭐ HTTP通信层
 */

import {
  ApiClientConfig,
  ApiError,
  ErrorType,
  RetryPolicy,
  RequestOptions,
  ErrorResponse,
  HealthCheckResponse,
  CanvasResponse,
  NodeCreate,
  NodeRead,
  NodeUpdate,
  EdgeCreate,
  EdgeRead,
  DecomposeRequest,
  DecomposeResponse,
  ScoreRequest,
  ScoreResponse,
  ExplainRequest,
  ExplainResponse,
  ReviewScheduleResponse,
  GenerateReviewRequest,
  GenerateReviewResponse,
  RecordReviewRequest,
  RecordReviewResponse,
  // RAG Types (Story 12.5 - Plugin RAG API Client)
  RAGQueryRequest,
  RAGQueryResponse,
  WeakConceptsResponse,
  RAGStatusResponse,
  // Story 12.A.6: Verification Question and Question Decomposition
  VerificationQuestionRequest,
  VerificationQuestionResponse,
  QuestionDecomposeRequest,
  QuestionDecomposeResponse,
  // Story 12.G.2: Agent Error Types
  AgentErrorType,
  AgentErrorResponse,
  isAgentErrorRetryable,
  getAgentErrorMessage,
  // Epic 28: Textbook Sync Types
  MountedTextbookApi,
  SyncMountResponse,
  UnmountTextbookResponse,
  ListMountedTextbooksResponse,
} from './types';

/**
 * Default configuration values
 * @source Story 13.3 Dev Notes - ApiClientConfig默认值
 * @modified Story 12.F.6 - Timeout increased from 30s to 60s for Agent calls
 */
const DEFAULT_TIMEOUT = 150000; // 150 seconds (Story 12.K: Match backend AI_TIMEOUT=120s + buffer)
const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_RETRY_BACKOFF_MS = 1000;
const RETRYABLE_ERROR_TYPES: ErrorType[] = [
  'NetworkError',
  'TimeoutError',
  'HttpError5xx',
];

/**
 * Story 12.F.6: Estimated processing time for each Agent type (in seconds)
 * Used to display progress hints to users ("正在分析... 预计30秒")
 */
const ESTIMATED_TIME: Record<string, number> = {
  'clarification-path': 30,
  'four-level-explanation': 45,
  'basic-decomposition': 20,
  'deep-decomposition': 40,
  'oral-explanation': 25,
  'example-teaching': 35,
  'memory-anchor': 20,
  'comparison-table': 30,
  'question-decomposition': 25,
  'verification-question': 30,
  'scoring': 15,
};

/**
 * Canvas Learning System API Client
 *
 * Provides type-safe methods for all backend API endpoints with:
 * - Automatic retry with exponential backoff
 * - Timeout control via AbortController
 * - Comprehensive error handling
 *
 * @source Story 13.3 Dev Notes - ApiClient类设计
 */
export class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private retryPolicy: RetryPolicy;

  /**
   * Story 12.H.4: AbortController registry for cancellable requests
   *
   * Maps lockKey to AbortController, allowing external cancellation of
   * in-flight requests. Used by callAgentWithCancel() and cancelRequest().
   *
   * @source Story 12.H.4 - AC1, AC2
   */
  private abortControllers: Map<string, AbortController> = new Map();

  /**
   * Create a new API client instance
   * @param config - Client configuration options
   *
   * @example
   * ```typescript
   * const client = new ApiClient({
   *   baseUrl: 'http://localhost:8000/api/v1',
   *   timeout: 30000,
   *   maxRetries: 3
   * });
   * ```
   */
  constructor(config: ApiClientConfig) {
    // ✅ Verified from Story 13.3 Dev Notes - ApiClient constructor
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT;
    this.retryPolicy = {
      maxRetries: config.maxRetries ?? DEFAULT_MAX_RETRIES,
      backoffMs: config.retryBackoffMs ?? DEFAULT_RETRY_BACKOFF_MS,
      retryableErrors: RETRYABLE_ERROR_TYPES,
    };
  }

  // ===========================================================================
  // Core Request Method
  // ===========================================================================

  /**
   * Generic request method with retry logic and error handling
   *
   * @param method - HTTP method (GET, POST, PUT, DELETE)
   * @param path - API endpoint path
   * @param body - Optional request body
   * @param options - Additional request options
   * @returns Promise with typed response
   *
   * @source Story 13.3 Dev Notes - Core Request Method
   * @verified Web Fetch API documentation for AbortController usage
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    let lastError: ApiError | null = null;

    // ✅ Verified from Story 13.3 - 重试策略: 最大重试次数3次
    for (let attempt = 0; attempt <= this.retryPolicy.maxRetries; attempt++) {
      try {
        // Create AbortController for timeout control
        // ✅ Verified from MDN Web Docs - AbortController for fetch timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
          // ✅ Verified from Story 13.3 Dev Notes - 请求头设置
          // ✅ Story 12.J.2: 添加 charset=utf-8 确保中文正确传输
          const response = await fetch(`${this.baseUrl}${path}`, {
            method,
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
              'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
              ...options?.headers,
            },
            body: body ? JSON.stringify(body) : undefined,
            signal: options?.signal ?? controller.signal,
          });

          clearTimeout(timeoutId);

          // Handle HTTP errors
          // ✅ Verified from Story 13.3 Dev Notes - HTTP错误处理
          if (!response.ok) {
            let errorDetails: ErrorResponse | null = null;
            try {
              errorDetails = (await response.json()) as ErrorResponse;
            } catch {
              // Response body might not be JSON
            }

            const errorType: ErrorType =
              response.status >= 500 ? 'HttpError5xx' : 'HttpError4xx';
            const errorMessage =
              errorDetails?.message ?? response.statusText ?? 'HTTP Error';

            throw new ApiError(
              `HTTP ${response.status}: ${errorMessage}`,
              errorType,
              response.status,
              errorDetails?.details
            );
          }

          // Handle 204 No Content
          // ✅ Verified from Story 13.3 Dev Notes - 204响应处理
          if (response.status === 204) {
            return undefined as T;
          }

          // Parse JSON response
          return (await response.json()) as T;
        } finally {
          clearTimeout(timeoutId);
        }
      } catch (error) {
        // Convert to ApiError if not already
        const apiError = this.normalizeError(error);
        lastError = apiError;

        // Check if we should retry
        // ✅ Verified from Story 13.3 Dev Notes - 可重试错误判断
        if (
          attempt < this.retryPolicy.maxRetries &&
          this.isRetryable(apiError)
        ) {
          // ✅ Verified from Story 13.3 - 指数退避算法: delay = baseDelay * 2^attempt
          const delay = this.retryPolicy.backoffMs * Math.pow(2, attempt);
          console.log(
            `[ApiClient] Request failed, retrying in ${delay}ms ` +
              `(attempt ${attempt + 1}/${this.retryPolicy.maxRetries}): ${apiError.message}`
          );
          await this.sleep(delay);
          continue;
        }

        // Not retryable or max retries reached
        throw apiError;
      }
    }

    // Should not reach here, but TypeScript needs a return
    throw lastError ?? new ApiError('Unknown error', 'UnknownError');
  }

  // ===========================================================================
  // Health Check (1 endpoint)
  // ===========================================================================

  /**
   * Check backend service health
   * @returns Health check response with service status
   *
   * @source Story 13.3 Dev Notes - GET /health
   * @verified specs/api/canvas-api.openapi.yml#/health
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('GET', '/health');
  }

  /**
   * Test connection to backend
   * @returns true if connection successful, false otherwise
   *
   * @source Story 13.3 Dev Notes - testConnection辅助方法
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }

  // ===========================================================================
  // Canvas API Methods (6 endpoints)
  // ===========================================================================

  /**
   * Read a canvas file
   * @param canvasName - Canvas file name (without path)
   * @returns Canvas data with nodes and edges
   *
   * @source Story 13.3 Dev Notes - GET /canvas/{canvas_name}
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}
   */
  async readCanvas(canvasName: string): Promise<CanvasResponse> {
    return this.request<CanvasResponse>(
      'GET',
      `/canvas/${encodeURIComponent(canvasName)}`
    );
  }

  /**
   * Create a new node in canvas
   * @param canvasName - Target canvas name
   * @param node - Node creation data
   * @returns Created node with generated ID
   *
   * @source Story 13.3 Dev Notes - POST /canvas/{canvas_name}/nodes
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}/nodes (POST)
   */
  async createNode(canvasName: string, node: NodeCreate): Promise<NodeRead> {
    return this.request<NodeRead>(
      'POST',
      `/canvas/${encodeURIComponent(canvasName)}/nodes`,
      node
    );
  }

  /**
   * Update an existing node
   * @param canvasName - Target canvas name
   * @param nodeId - Node ID to update
   * @param update - Partial node update data
   * @returns Updated node
   *
   * @source Story 13.3 Dev Notes - PUT /canvas/{canvas_name}/nodes/{node_id}
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}/nodes/{node_id} (PUT)
   */
  async updateNode(
    canvasName: string,
    nodeId: string,
    update: NodeUpdate
  ): Promise<NodeRead> {
    return this.request<NodeRead>(
      'PUT',
      `/canvas/${encodeURIComponent(canvasName)}/nodes/${encodeURIComponent(nodeId)}`,
      update
    );
  }

  /**
   * Delete a node from canvas
   * @param canvasName - Target canvas name
   * @param nodeId - Node ID to delete
   *
   * @source Story 13.3 Dev Notes - DELETE /canvas/{canvas_name}/nodes/{node_id}
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}/nodes/{node_id} (DELETE)
   */
  async deleteNode(canvasName: string, nodeId: string): Promise<void> {
    return this.request<void>(
      'DELETE',
      `/canvas/${encodeURIComponent(canvasName)}/nodes/${encodeURIComponent(nodeId)}`
    );
  }

  /**
   * Create a new edge (connection) in canvas
   * @param canvasName - Target canvas name
   * @param edge - Edge creation data
   * @returns Created edge with generated ID
   *
   * @source Story 13.3 Dev Notes - POST /canvas/{canvas_name}/edges
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}/edges (POST)
   */
  async createEdge(canvasName: string, edge: EdgeCreate): Promise<EdgeRead> {
    return this.request<EdgeRead>(
      'POST',
      `/canvas/${encodeURIComponent(canvasName)}/edges`,
      edge
    );
  }

  /**
   * Delete an edge from canvas
   * @param canvasName - Target canvas name
   * @param edgeId - Edge ID to delete
   *
   * @source Story 13.3 Dev Notes - DELETE /canvas/{canvas_name}/edges/{edge_id}
   * @verified specs/api/canvas-api.openapi.yml#/canvas/{canvas_path}/edges/{edge_id} (DELETE)
   */
  async deleteEdge(canvasName: string, edgeId: string): Promise<void> {
    return this.request<void>(
      'DELETE',
      `/canvas/${encodeURIComponent(canvasName)}/edges/${encodeURIComponent(edgeId)}`
    );
  }

  // ===========================================================================
  // Agent API Methods (9 endpoints)
  // ===========================================================================

  /**
   * Decompose a concept into basic questions
   * @param request - Decomposition request
   * @returns Generated questions and created nodes
   *
   * @source Story 13.3 Dev Notes - POST /agents/decompose/basic
   */
  async decomposeBasic(request: DecomposeRequest): Promise<DecomposeResponse> {
    return this.request<DecomposeResponse>(
      'POST',
      '/agents/decompose/basic',
      request
    );
  }

  /**
   * Decompose a concept with deep analysis
   * @param request - Decomposition request
   * @returns Generated deep questions and created nodes
   *
   * @source Story 13.3 Dev Notes - POST /agents/decompose/deep
   */
  async decomposeDeep(request: DecomposeRequest): Promise<DecomposeResponse> {
    return this.request<DecomposeResponse>(
      'POST',
      '/agents/decompose/deep',
      request
    );
  }

  /**
   * Score understanding of nodes
   * @param request - Scoring request with node IDs
   * @returns Scores for each node with 4-dimension evaluation
   *
   * @source Story 13.3 Dev Notes - POST /agents/score
   */
  async scoreUnderstanding(request: ScoreRequest): Promise<ScoreResponse> {
    return this.request<ScoreResponse>('POST', '/agents/score', request);
  }

  /**
   * Generate oral-style explanation
   * @param request - Explanation request
   * @returns Generated oral explanation
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/oral
   */
  async explainOral(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/oral',
      request
    );
  }

  /**
   * Generate clarification path explanation
   * @param request - Explanation request
   * @returns Generated clarification path
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/clarification
   */
  async explainClarification(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/clarification',
      request
    );
  }

  /**
   * Generate comparison table explanation
   * @param request - Explanation request
   * @returns Generated comparison table
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/comparison
   */
  async explainComparison(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/comparison',
      request
    );
  }

  /**
   * Generate memory anchor explanation
   * @param request - Explanation request
   * @returns Generated memory anchors
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/memory
   */
  async explainMemory(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/memory',
      request
    );
  }

  /**
   * Generate four-level explanation
   * @param request - Explanation request
   * @returns Generated four-level explanation
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/four-level
   */
  async explainFourLevel(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/four-level',
      request
    );
  }

  /**
   * Generate example-based explanation
   * @param request - Explanation request
   * @returns Generated example explanation
   *
   * @source Story 13.3 Dev Notes - POST /agents/explain/example
   */
  async explainExample(request: ExplainRequest): Promise<ExplainResponse> {
    return this.request<ExplainResponse>(
      'POST',
      '/agents/explain/example',
      request
    );
  }

  // ===========================================================================
  // Review API Methods (3 endpoints)
  // ===========================================================================

  /**
   * Get current review schedule
   * @returns List of items due for review
   *
   * @source Story 13.3 Dev Notes - GET /review/schedule
   */
  async getReviewSchedule(): Promise<ReviewScheduleResponse> {
    return this.request<ReviewScheduleResponse>('GET', '/review/schedule');
  }

  /**
   * Generate a verification canvas for review
   * @param request - Generation request
   * @returns Information about created verification canvas
   *
   * @source Story 13.3 Dev Notes - POST /review/generate
   */
  async generateReview(
    request: GenerateReviewRequest
  ): Promise<GenerateReviewResponse> {
    return this.request<GenerateReviewResponse>(
      'POST',
      '/review/generate',
      request
    );
  }

  /**
   * Record a review result
   * @param request - Review record request
   * @returns Next review date and interval
   *
   * @source Story 13.3 Dev Notes - POST /review/record
   */
  async recordReview(
    request: RecordReviewRequest
  ): Promise<RecordReviewResponse> {
    return this.request<RecordReviewResponse>(
      'POST',
      '/review/record',
      request
    );
  }

  // ===========================================================================
  // Textbook API Methods (3 endpoints) - Epic 28: Bidirectional Textbook Links
  // ===========================================================================

  /**
   * Sync a mounted textbook from frontend to backend
   *
   * This bridges the gap between frontend localStorage and backend filesystem,
   * enabling Agent services to access textbook context when generating responses.
   *
   * @param canvasPath - Current Canvas path that the textbook is mounted to
   * @param textbook - Mounted textbook information
   * @returns Sync result with config file path
   *
   * @source Epic 28 - 方案A: 前端同步到后端
   * @verified backend/app/api/v1/endpoints/textbook.py#sync_mount_textbook
   */
  async syncMountedTextbook(
    canvasPath: string,
    textbook: MountedTextbookApi
  ): Promise<SyncMountResponse> {
    return this.request<SyncMountResponse>('POST', '/textbook/sync-mount', {
      canvas_path: canvasPath,
      textbook: textbook,
    });
  }

  /**
   * Unmount a textbook from a canvas
   *
   * Removes the textbook association from .canvas-links.json
   *
   * @param canvasPath - Canvas path
   * @param textbookId - Textbook ID to unmount
   * @returns Unmount result
   *
   * @source Epic 28 - 方案A: 前端同步到后端
   * @verified backend/app/api/v1/endpoints/textbook.py#unmount_textbook
   */
  async unmountTextbook(
    canvasPath: string,
    textbookId: string
  ): Promise<UnmountTextbookResponse> {
    return this.request<UnmountTextbookResponse>('POST', '/textbook/unmount', {
      canvas_path: canvasPath,
      textbook_id: textbookId,
    });
  }

  /**
   * List all mounted textbooks for a canvas
   *
   * Returns textbook associations from .canvas-links.json
   *
   * @param canvasPath - Canvas path
   * @returns List of mounted textbook associations
   *
   * @source Epic 28 - 方案A: 前端同步到后端
   * @verified backend/app/api/v1/endpoints/textbook.py#list_mounted_textbooks
   */
  async listMountedTextbooks(
    canvasPath: string
  ): Promise<ListMountedTextbooksResponse> {
    return this.request<ListMountedTextbooksResponse>(
      'GET',
      `/textbook/mounted/${encodeURIComponent(canvasPath)}`
    );
  }

  // ===========================================================================
  // RAG API Methods (3 endpoints) - Story 12.5: Plugin RAG API Client
  // ===========================================================================

  /**
   * Execute RAG intelligent retrieval query
   *
   * Features:
   * - Multi-source parallel retrieval (Graphiti + LanceDB + Multimodal)
   * - 3 fusion algorithms (RRF, Weighted, Cascade)
   * - Hybrid reranking (Local + Cohere)
   * - Quality control with query rewriting
   *
   * @param request - RAG query request
   * @returns RAG query response with results and metrics
   *
   * @source Story 12.5 - Plugin RAG API Client (P0)
   * @source UltraThink深度调研报告 v2.0 - Section 10.1
   * @verified backend/app/api/v1/endpoints/rag.py#rag_query
   */
  async ragQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    return this.request<RAGQueryResponse>('POST', '/rag/query', request);
  }

  /**
   * Get weak concepts for a canvas (low stability items)
   *
   * Used to generate verification canvas for review based on
   * concepts that need more practice.
   *
   * @param canvasFile - Canvas file path
   * @param limit - Maximum number of concepts to return (default: 10)
   * @returns Weak concepts list from Temporal Memory
   *
   * @source Story 12.5 - Plugin RAG API Client (P0)
   * @verified backend/app/api/v1/endpoints/rag.py#get_weak_concepts
   */
  async getWeakConcepts(
    canvasFile: string,
    limit = 10
  ): Promise<WeakConceptsResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    return this.request<WeakConceptsResponse>(
      'GET',
      `/rag/weak-concepts/${encodeURIComponent(canvasFile)}?${params}`
    );
  }

  /**
   * Get RAG service status
   *
   * Returns availability information including:
   * - Whether the RAG service is available
   * - Whether LangGraph is initialized
   * - Any import/initialization errors
   *
   * @returns RAG service status
   *
   * @source Story 12.5 - Plugin RAG API Client (P0)
   * @verified backend/app/api/v1/endpoints/rag.py#get_rag_status
   */
  async getRagStatus(): Promise<RAGStatusResponse> {
    return this.request<RAGStatusResponse>('GET', '/rag/status');
  }

  // ===========================================================================
  // Story 12.A.6: Verification Question and Question Decomposition
  // ===========================================================================

  /**
   * Generate verification questions for a concept node
   *
   * Creates 2-4 verification questions based on the node content,
   * suitable for testing understanding of red/purple nodes.
   *
   * @param request - Verification question request
   * @returns Generated questions and created nodes
   *
   * @source Story 12.A.6 - verification-question Agent (AC1, AC5)
   * @verified backend/app/api/v1/endpoints/agents.py#generate_verification_questions
   */
  async generateVerificationQuestions(
    request: VerificationQuestionRequest
  ): Promise<VerificationQuestionResponse> {
    return this.request<VerificationQuestionResponse>(
      'POST',
      '/agents/verification/question',
      request
    );
  }

  /**
   * Decompose a verification question into sub-questions
   *
   * Takes a purple node (verification question) and creates 2-5
   * smaller, more focused sub-questions to guide understanding.
   *
   * @param request - Question decomposition request
   * @returns Decomposed questions and created nodes
   *
   * @source Story 12.A.6 - question-decomposition Agent (AC2, AC5)
   * @verified backend/app/api/v1/endpoints/agents.py#decompose_question
   */
  async decomposeQuestion(
    request: QuestionDecomposeRequest
  ): Promise<QuestionDecomposeResponse> {
    return this.request<QuestionDecomposeResponse>(
      'POST',
      '/agents/decompose/question',
      request
    );
  }

  // ===========================================================================
  // Story 12.H.4: Cancellable Request Methods
  // ===========================================================================

  /**
   * Story 12.H.4: Make a cancellable Agent request
   *
   * Unlike the standard request() method, this:
   * - Registers AbortController by lockKey for external cancellation
   * - Returns null on cancellation instead of throwing
   * - Distinguishes user cancellation from timeout
   *
   * @param lockKey - Unique identifier for the request (e.g., "oral-{nodeId}")
   * @param endpoint - API endpoint path
   * @param data - Request body data
   * @param timeout - Optional timeout in milliseconds (defaults to this.timeout)
   * @returns Response data or null if cancelled
   *
   * @source Story 12.H.4 - AC1, AC2, AC5
   * @source ADR-009 - Error handling strategy (user cancel should not trigger retry)
   */
  async callAgentWithCancel<T>(
    lockKey: string,
    endpoint: string,
    data: unknown,
    timeout?: number
  ): Promise<T | null> {
    // Story 12.H.4 AC2: Create unique AbortController for this request
    const controller = new AbortController();
    this.abortControllers.set(lockKey, controller);

    // Track if this was a user-initiated cancel (not timeout)
    let userCancelled = false;

    const effectiveTimeout = timeout ?? this.timeout;
    const startTime = Date.now();

    // Story 12.K: Debug logging for request tracing
    const requestBody = JSON.stringify(data);
    console.log(`[ApiClient] Sending request:`, {
      lockKey,
      url: `${this.baseUrl}${endpoint}`,
      timeout: effectiveTimeout,
      bodySize: requestBody.length,
      startTime: new Date(startTime).toISOString(),
    });

    const timeoutId = setTimeout(() => {
      // Don't mark as user-cancelled for timeout
      console.log(`[ApiClient] Timeout triggered for "${lockKey}" after ${effectiveTimeout}ms`);
      controller.abort();
    }, effectiveTimeout);

    try {
      // ✅ Verified from MDN Web Docs - fetch with AbortController signal
      // ✅ Story 12.J.2: 添加 charset=utf-8 确保中文正确传输
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
        },
        body: JSON.stringify(data),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const elapsed = Date.now() - startTime;
      console.log(`[ApiClient] Response received for "${lockKey}":`, {
        status: response.status,
        elapsed: `${elapsed}ms`,
        ok: response.ok,
      });

      if (!response.ok) {
        let errorDetails: ErrorResponse | null = null;
        try {
          errorDetails = (await response.json()) as ErrorResponse;
        } catch {
          // Response body might not be JSON
        }

        const errorType: ErrorType =
          response.status >= 500 ? 'HttpError5xx' : 'HttpError4xx';
        const errorMessage =
          errorDetails?.message ?? response.statusText ?? 'HTTP Error';

        throw new ApiError(
          `HTTP ${response.status}: ${errorMessage}`,
          errorType,
          response.status,
          errorDetails?.details
        );
      }

      const result = (await response.json()) as T;
      console.log(`[ApiClient] Request "${lockKey}" completed successfully in ${elapsed}ms`);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);

      // Check if this was an abort (user cancel or timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        // Story 12.H.4 AC5: Return null on cancellation, don't write to Canvas
        // Check if it was user-cancelled (controller still in map means timeout)
        userCancelled = !this.abortControllers.has(lockKey);
        console.log(
          `[ApiClient] Request "${lockKey}" was ${userCancelled ? 'cancelled by user' : 'timed out'}`
        );
        return null;
      }

      // Re-throw other errors for normal handling
      throw this.normalizeError(error);
    } finally {
      // Story 12.H.4 AC6: Clean up AbortController, release lock
      this.abortControllers.delete(lockKey);
    }
  }

  /**
   * Story 12.H.4: Cancel a pending request by lockKey
   *
   * Immediately aborts the request if it exists. The request's promise
   * will resolve to null rather than throwing an error.
   *
   * @param lockKey - Request identifier to cancel
   * @returns true if request was found and cancelled, false if not found
   *
   * @source Story 12.H.4 - AC3, AC6
   * @source ADR-009 - User cancel should not trigger retry or error logging
   */
  cancelRequest(lockKey: string): boolean {
    const controller = this.abortControllers.get(lockKey);
    if (controller) {
      // Remove first so the abort handler knows it's user-initiated
      this.abortControllers.delete(lockKey);
      controller.abort();
      console.log(`[ApiClient] Cancelled request: ${lockKey}`);
      return true;
    }
    return false;
  }

  /**
   * Story 12.H.4: Cancel all pending requests
   *
   * Useful for cleanup on plugin unload or when user wants to stop
   * all Agent operations.
   *
   * @source Story 12.H.4 - Task 2.2
   */
  cancelAllRequests(): void {
    const count = this.abortControllers.size;
    this.abortControllers.forEach((controller, lockKey) => {
      console.log(`[ApiClient] Cancelling request: ${lockKey}`);
      controller.abort();
    });
    this.abortControllers.clear();
    if (count > 0) {
      console.log(`[ApiClient] Cancelled ${count} pending request(s)`);
    }
  }

  /**
   * Story 12.H.4: Check if a request is currently pending
   *
   * @param lockKey - Request identifier to check
   * @returns true if request is in progress
   *
   * @source Story 12.H.4 - Task 2.3
   */
  isRequestPending(lockKey: string): boolean {
    return this.abortControllers.has(lockKey);
  }

  /**
   * Story 12.H.4: Get all currently pending request keys
   *
   * @returns Array of lockKeys for pending requests
   *
   * @source Story 12.H.4 - Task 2.4
   */
  getPendingRequests(): string[] {
    return Array.from(this.abortControllers.keys());
  }

  // ===========================================================================
  // Helper Methods
  // ===========================================================================

  /**
   * Check if an error is retryable
   * @param error - Error to check
   * @returns true if the error should trigger a retry
   *
   * @source Story 13.3 Dev Notes - 可重试错误判断逻辑
   */
  private isRetryable(error: ApiError): boolean {
    return this.retryPolicy.retryableErrors.includes(error.type);
  }

  /**
   * Normalize any error to ApiError
   * @param error - Error to normalize
   * @returns Normalized ApiError instance
   *
   * @source Story 13.3 Dev Notes - 错误转换逻辑
   */
  private normalizeError(error: unknown): ApiError {
    if (error instanceof ApiError) {
      return error;
    }

    // AbortController timeout
    // ✅ Verified from MDN - AbortError name for abort signal
    // Story 12.F.6: User-friendly timeout message in Chinese
    if (error instanceof Error && error.name === 'AbortError') {
      return new ApiError('请求超时 (60秒)，请稍后重试', 'TimeoutError', 408);
    }

    // Network error (fetch failed)
    // ✅ Verified from MDN - TypeError for network failures
    if (error instanceof TypeError) {
      return new ApiError(
        'Network error: Unable to reach server',
        'NetworkError',
        0
      );
    }

    // Unknown error
    const message =
      error instanceof Error ? error.message : 'Unknown error occurred';
    return new ApiError(message, 'UnknownError', 0);
  }

  /**
   * Story 12.G.2: Normalize Agent error response to ApiError
   *
   * Converts backend AgentErrorResponse to frontend ApiError with:
   * - Proper error type classification
   * - User-friendly Chinese messages
   * - Bug ID for tracking
   * - Retryable flag for UI hints
   *
   * @param response - Agent error response from backend
   * @returns Normalized ApiError instance
   *
   * @source Story 12.G.2 - 增强错误处理与友好提示
   * @source specs/api/agent-api.openapi.yml:629-652
   */
  normalizeAgentError(response: AgentErrorResponse): ApiError {
    const errorType = response.error_type || 'UNKNOWN';
    const isRetryable = isAgentErrorRetryable(errorType as AgentErrorType);

    // Map Agent error types to ApiError types
    let apiErrorType: ErrorType;
    let statusCode: number;

    if (isRetryable) {
      apiErrorType = 'HttpError5xx';  // Retryable errors use 5xx category
      statusCode = 503;  // Service Unavailable
    } else {
      apiErrorType = 'HttpError4xx';  // Non-retryable errors use 4xx category
      statusCode = 400;  // Bad Request
    }

    // Create ApiError with Agent-specific information
    const apiError = new ApiError(
      response.message || getAgentErrorMessage(errorType as AgentErrorType),
      apiErrorType,
      statusCode,
      response.details,
      response.bug_id,
      errorType  // backendErrorType for display
    );

    return apiError;
  }

  /**
   * Story 12.G.2: Check if API response contains Agent error
   *
   * Agent errors have specific fields: error_type, is_retryable, bug_id
   *
   * @param data - Response data to check
   * @returns True if response is an Agent error
   */
  isAgentErrorResponse(data: unknown): data is AgentErrorResponse {
    if (typeof data !== 'object' || data === null) {
      return false;
    }

    const obj = data as Record<string, unknown>;
    return (
      'error' in obj &&
      obj.error === true &&
      'error_type' in obj &&
      typeof obj.error_type === 'string'
    );
  }

  /**
   * Story 12.G.2: Handle Agent response that may contain error
   *
   * Used by Agent-calling methods to detect and throw proper errors
   *
   * @param data - Response data from Agent endpoint
   * @throws ApiError if response contains error
   */
  handleAgentResponse<T>(data: T): T {
    if (this.isAgentErrorResponse(data)) {
      throw this.normalizeAgentError(data as AgentErrorResponse);
    }
    return data;
  }

  /**
   * Sleep for specified milliseconds
   * @param ms - Milliseconds to sleep
   * @returns Promise that resolves after delay
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ===========================================================================
  // Configuration Getters
  // ===========================================================================

  /**
   * Get current base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Get current timeout setting
   */
  getTimeout(): number {
    return this.timeout;
  }

  /**
   * Get current retry policy
   */
  getRetryPolicy(): RetryPolicy {
    return { ...this.retryPolicy };
  }

  /**
   * Story 12.F.6: Get estimated processing time for an Agent type
   * @param agentType - Agent type identifier
   * @returns Estimated time in seconds (default: 30)
   */
  getEstimatedTime(agentType: string): number {
    return ESTIMATED_TIME[agentType] ?? 30;
  }
}

/**
 * Create a default API client with standard configuration
 * @param baseUrl - Backend base URL (default: http://localhost:8000/api/v1)
 * @returns Configured ApiClient instance
 *
 * @source Story 13.3 Dev Notes - 插件设置集成示例
 */
export function createDefaultApiClient(
  baseUrl = 'http://localhost:8000/api/v1'
): ApiClient {
  return new ApiClient({
    baseUrl,
    timeout: DEFAULT_TIMEOUT,
    maxRetries: DEFAULT_MAX_RETRIES,
    retryBackoffMs: DEFAULT_RETRY_BACKOFF_MS,
  });
}
