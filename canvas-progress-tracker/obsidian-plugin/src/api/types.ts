/**
 * Canvas Learning System - API Type Definitions
 *
 * Type definitions for the HTTP API client that communicates with
 * the FastAPI backend.
 *
 * @source Story 13.3 Dev Notes - types.ts完整接口
 * @verified specs/api/canvas-api.openapi.yml (components/schemas)
 */

// =============================================================================
// Error Types
// =============================================================================

/**
 * Error type enumeration for API errors
 * @source Story 13.3 Dev Notes - ErrorType定义
 */
export type ErrorType =
  | 'NetworkError'
  | 'TimeoutError'
  | 'HttpError4xx'
  | 'HttpError5xx'
  | 'ValidationError'
  | 'UnknownError';

/**
 * Custom API Error class
 * @source Story 13.3 Dev Notes - ApiError类设计
 * @source Story 21.5.5 - 增强错误属性 (bugId, backendErrorType)
 */
export class ApiError extends Error {
  /**
   * Bug tracking ID from backend (format: BUG-XXXXXXXX)
   * @source Story 21.5.3 - Bug追踪日志系统
   */
  public bugId?: string;

  /**
   * Backend error type name (e.g., AIProviderError, ConfigurationError)
   * @source Story 21.5.5 - 后端错误类型映射
   */
  public backendErrorType?: string;

  constructor(
    message: string,
    public type: ErrorType,
    public statusCode?: number,
    public details?: Record<string, unknown>,
    bugId?: string,
    backendErrorType?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.bugId = bugId;
    this.backendErrorType = backendErrorType;
    // Maintain prototype chain for instanceof checks
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * Check if this error is retryable
   * @source Story 21.5.5 - AC 3: 可重试错误提供重试按钮
   * @source ADR-009: RETRYABLE_ERROR_TYPES
   */
  get isRetryable(): boolean {
    return ['NetworkError', 'TimeoutError', 'HttpError5xx'].includes(this.type);
  }

  /**
   * Get user-friendly error message based on error type
   * @source Story 13.3 Dev Notes - 错误处理策略表
   * @source Story 21.5.5 - 增强错误消息显示
   */
  getUserFriendlyMessage(): string {
    // 如果有后端错误类型，优先使用
    const typePrefix = this.backendErrorType
      ? `[${this.backendErrorType}] `
      : '';

    switch (this.type) {
      case 'NetworkError':
        return '无法连接到服务器，请检查网络连接';
      case 'TimeoutError':
        return '请求超时，请重试';
      case 'HttpError4xx':
        return `${typePrefix}请求参数错误: ${this.message}`;
      case 'HttpError5xx':
        return `${typePrefix}服务器错误: ${this.message}`;
      case 'ValidationError':
        return `数据验证失败: ${JSON.stringify(this.details)}`;
      default:
        return `${typePrefix}未知错误: ${this.message}`;
    }
  }

  /**
   * Get formatted error string including bug_id if available
   * @source Story 21.5.5 - AC 1: Agent调用错误显示bug_id
   */
  getFormattedMessage(): string {
    let msg = this.getUserFriendlyMessage();
    if (this.bugId) {
      msg += `\n[Bug ID: ${this.bugId}]`;
    }
    return msg;
  }
}

/**
 * Backend error response format
 * @source Story 13.3 Dev Notes - ErrorResponse接口
 */
export interface ErrorResponse {
  code: number;
  message: string;
  details?: Record<string, unknown>;
}

// =============================================================================
// Story 12.G.2: Agent Error Types (对齐ADR-009 ErrorCode)
// =============================================================================

/**
 * Agent错误类型枚举 (对齐后端AgentErrorType和ADR-009)
 * @source specs/api/agent-api.openapi.yml:617-627
 * @source docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md
 */
export type AgentErrorType =
  | 'CONFIG_MISSING'       // 2001 - API Key未配置 (NON_RETRYABLE)
  | 'FILE_NOT_FOUND'       // 3001 - 模板缺失 (FATAL)
  | 'LLM_TIMEOUT'          // 1002 - API调用超时 (RETRYABLE)
  | 'LLM_RATE_LIMIT'       // 1001 - 速率限制 (RETRYABLE)
  | 'LLM_INVALID_RESPONSE' // 1004 - 响应格式错误 (NON_RETRYABLE)
  | 'NETWORK_TIMEOUT'      // 4001 - 网络错误 (RETRYABLE)
  | 'UNKNOWN';             // 9999 - 未知错误

/**
 * 错误类型到用户消息映射 (对齐后端)
 * @source Story 12.G.2 AC1
 */
export const AGENT_ERROR_MESSAGES: Record<AgentErrorType, string> = {
  CONFIG_MISSING: '请在插件设置中配置 API Key',
  FILE_NOT_FOUND: 'Agent 模板文件缺失',
  LLM_TIMEOUT: 'AI 响应超时，请重试',
  LLM_RATE_LIMIT: '请求过于频繁，请稍后重试',
  LLM_INVALID_RESPONSE: 'AI 响应格式异常',
  NETWORK_TIMEOUT: '网络连接失败，请检查网络',
  UNKNOWN: '发生未知错误',
};

/**
 * 可重试错误类型 (对齐ADR-009 ErrorCategory.RETRYABLE)
 * @source Story 12.G.2 AC3
 */
export const RETRYABLE_AGENT_ERRORS: AgentErrorType[] = [
  'LLM_TIMEOUT',
  'LLM_RATE_LIMIT',
  'NETWORK_TIMEOUT',
];

/**
 * Agent错误响应接口 (对齐OpenAPI AgentError schema)
 * @source specs/api/agent-api.openapi.yml:629-652
 */
export interface AgentErrorResponse {
  error_type: AgentErrorType;
  message: string;
  is_retryable: boolean;
  details?: Record<string, unknown>;
  bug_id?: string;  // Format: BUG-XXXXXXXX
}

/**
 * 判断错误类型是否可重试
 * @source Story 12.G.2 AC3
 */
export function isAgentErrorRetryable(errorType: AgentErrorType): boolean {
  return RETRYABLE_AGENT_ERRORS.includes(errorType);
}

/**
 * 获取Agent错误的用户友好消息
 * @source Story 12.G.2 AC1
 */
export function getAgentErrorMessage(errorType: AgentErrorType): string {
  return AGENT_ERROR_MESSAGES[errorType] || AGENT_ERROR_MESSAGES.UNKNOWN;
}

// =============================================================================
// Common Types
// =============================================================================

/**
 * Health check response from backend
 * @source Story 13.3 Dev Notes - HealthCheckResponse
 * @verified specs/api/canvas-api.openapi.yml#HealthCheckResponse
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string; // ISO 8601 datetime
  version?: string;
  components?: {
    api?: { status: 'up' | 'down'; response_time_ms?: number };
    canvas_filesystem?: { status: 'up' | 'down'; vault_path?: string };
    knowledge_graph?: { status: 'up' | 'down'; connection?: string };
    memory_system?: {
      graphiti?: 'up' | 'down';
      temporal?: 'up' | 'down';
      semantic?: 'up' | 'down';
    };
  };
}

// =============================================================================
// Canvas Types
// =============================================================================

/**
 * Canvas node types
 * @source Story 13.3 Dev Notes - NodeType
 * @verified specs/api/canvas-api.openapi.yml#CanvasNode/properties/type
 */
export type NodeType = 'text' | 'file' | 'group' | 'link';

/**
 * Canvas node color codes
 * @source Story 13.3 Dev Notes - NodeColor
 * @verified Story 12.B.4 - 正确颜色映射: 1=灰, 2=绿, 3=紫, 4=红, 5=蓝, 6=黄
 * @see canvas-progress-tracker/obsidian-plugin/src/types/menu.ts - CANVAS_COLOR_NAMES
 */
export type NodeColor = '1' | '2' | '3' | '4' | '5' | '6';

/**
 * Edge connection sides
 * @source Story 13.3 Dev Notes - EdgeSide
 * @verified specs/api/canvas-api.openapi.yml#CanvasEdge/properties/fromSide
 */
export type EdgeSide = 'top' | 'bottom' | 'left' | 'right';

/**
 * Node creation request
 * @source Story 13.3 Dev Notes - NodeCreate
 * @verified specs/api/canvas-api.openapi.yml#NodeInput
 */
export interface NodeCreate {
  type: NodeType;
  text?: string;
  file?: string;
  url?: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: NodeColor;
}

/**
 * Node update request (partial update)
 * @source Story 13.3 Dev Notes - NodeUpdate
 */
export interface NodeUpdate {
  text?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  color?: NodeColor;
}

/**
 * Node read response
 * @source Story 13.3 Dev Notes - NodeRead
 * @verified specs/api/canvas-api.openapi.yml#CanvasNode
 */
export interface NodeRead {
  id: string;
  type: NodeType;
  text?: string;
  file?: string;
  url?: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: NodeColor;
}

/**
 * Edge creation request
 * @source Story 13.3 Dev Notes - EdgeCreate
 * @verified specs/api/canvas-api.openapi.yml#EdgeInput
 */
export interface EdgeCreate {
  fromNode: string;
  toNode: string;
  fromSide?: EdgeSide;
  toSide?: EdgeSide;
  label?: string;
}

/**
 * Edge read response
 * @source Story 13.3 Dev Notes - EdgeRead
 * @verified specs/api/canvas-api.openapi.yml#CanvasEdge
 */
export interface EdgeRead {
  id: string;
  fromNode: string;
  toNode: string;
  fromSide?: EdgeSide;
  toSide?: EdgeSide;
  label?: string;
}

/**
 * Canvas response containing all nodes and edges
 * @source Story 13.3 Dev Notes - CanvasResponse
 * @verified specs/api/canvas-api.openapi.yml#CanvasData
 */
export interface CanvasResponse {
  name: string;
  nodes: NodeRead[];
  edges: EdgeRead[];
}

// =============================================================================
// Agent Types
// =============================================================================

/**
 * Decomposition request for basic/deep decomposition agents
 * @source Story 13.3 Dev Notes - DecomposeRequest
 */
export interface DecomposeRequest {
  canvas_name: string;
  node_id: string;
}

/**
 * Decomposition response with generated questions and nodes
 * @source Story 13.3 Dev Notes - DecomposeResponse
 */
export interface DecomposeResponse {
  questions: string[];
  created_nodes: NodeRead[];
}

/**
 * Scoring request for understanding evaluation
 * @source Story 13.3 Dev Notes - ScoreRequest
 * @source Story 2.8 - Added node_content for real-time content passing
 */
export interface ScoreRequest {
  canvas_name: string;
  node_ids: string[];
  /** Node content to score (passed from plugin) - Story 2.8 */
  node_content?: string;
}

/**
 * Individual node score with 4-dimension scoring
 * @source Story 13.3 Dev Notes - NodeScore
 * @source Story 2.8 - Added feedback and color_action fields
 * @source .claude/agents/scoring.md - Output Format
 */
export interface NodeScore {
  node_id: string;
  accuracy: number; // 0-25 (updated from 0-10)
  imagery: number; // 0-25 (updated from 0-10)
  completeness: number; // 0-25 (updated from 0-10)
  originality: number; // 0-25 (updated from 0-10)
  total: number; // 0-100 (updated from 0-40)
  new_color: NodeColor; // 2=green(>=80), 3=purple(60-79), 4=red(<60)
  /** Specific improvement suggestions from Agent (100-200 chars) */
  feedback?: string;
  /** Color action: change_to_green/change_to_purple/keep_red */
  color_action?: string;
}

/**
 * Scoring response with all node scores
 * @source Story 13.3 Dev Notes - ScoreResponse
 */
export interface ScoreResponse {
  scores: NodeScore[];
}

/**
 * Explanation request for various explanation agents
 * @source Story 13.3 Dev Notes - ExplainRequest
 * @source Story 12.B.2 - node_content for real-time content passing
 */
export interface ExplainRequest {
  canvas_name: string;
  node_id: string;
  /**
   * Real-time node content from plugin (Story 12.B.2)
   * If provided, backend uses this directly instead of reading from disk.
   * Solves the "content mismatch" bug where disk content differs from UI display.
   */
  node_content?: string;
}

/**
 * Explanation response with generated content
 * @source Story 13.3 Dev Notes - ExplainResponse
 */
export interface ExplainResponse {
  explanation: string;
  created_node_id: string;
}

// =============================================================================
// Story 12.A.6: Verification Question and Question Decomposition Types
// =============================================================================

/**
 * Verification question request
 * @source Story 12.A.6 - verification-question Agent
 */
export interface VerificationQuestionRequest {
  canvas_name: string;
  node_id: string;
}

/**
 * Single verification question
 * @source Story 12.A.6 - verification-question Agent
 */
export interface VerificationQuestion {
  source_node_id: string;
  question_text: string;
  question_type: string; // 突破型/检验型/应用型/综合型
  difficulty: string; // 基础/深度
  guidance?: string; // Optional hint starting with 💡
  rationale: string;
}

/**
 * Verification question response
 * @source Story 12.A.6 - verification-question Agent
 */
export interface VerificationQuestionResponse {
  questions: VerificationQuestion[];
  concept: string;
  generated_at: string; // ISO datetime
  created_nodes: NodeRead[];
}

/**
 * Question decomposition request
 * @source Story 12.A.6 - question-decomposition Agent
 */
export interface QuestionDecomposeRequest {
  canvas_name: string;
  node_id: string;
}

/**
 * Single sub-question from decomposition
 * @source Story 12.A.6 - question-decomposition Agent
 */
export interface SubQuestion {
  text: string;
  type: string; // 检验型/应用型/对比型/推理型
  guidance: string; // Starts with 💡 提示:
}

/**
 * Question decomposition response
 * @source Story 12.A.6 - question-decomposition Agent
 */
export interface QuestionDecomposeResponse {
  questions: SubQuestion[];
  created_nodes: NodeRead[];
}

// =============================================================================
// Review Types
// =============================================================================

/**
 * Single review item in schedule
 * @source Story 13.3 Dev Notes - ReviewItem
 */
export interface ReviewItem {
  canvas_name: string;
  node_id: string;
  concept: string;
  due_date: string; // YYYY-MM-DD
  interval_days: number; // 1/7/30
}

/**
 * Review schedule response
 * @source Story 13.3 Dev Notes - ReviewScheduleResponse
 */
export interface ReviewScheduleResponse {
  items: ReviewItem[];
  total_count: number;
}

/**
 * Request to generate verification canvas for review
 * @source Story 13.3 Dev Notes - GenerateReviewRequest
 */
export interface GenerateReviewRequest {
  source_canvas: string;
  node_ids?: string[];
}

/**
 * Response after generating verification canvas
 * @source Story 13.3 Dev Notes - GenerateReviewResponse
 */
export interface GenerateReviewResponse {
  verification_canvas_name: string;
  node_count: number;
}

/**
 * Request to record a review result
 * @source Story 13.3 Dev Notes - RecordReviewRequest
 */
export interface RecordReviewRequest {
  canvas_name: string;
  node_id: string;
  score: number; // 0-40
}

/**
 * Response after recording a review
 * @source Story 13.3 Dev Notes - RecordReviewResponse
 */
export interface RecordReviewResponse {
  next_review_date: string; // YYYY-MM-DD
  new_interval: number; // days
}

// =============================================================================
// RAG Types (Story 12.5 - Plugin RAG API Client)
// =============================================================================

/**
 * RAG fusion strategy for multi-source retrieval
 * @source Story 12.5 - Plugin RAG API Client
 * @source backend/app/api/v1/endpoints/rag.py
 */
export type RAGFusionStrategy = 'rrf' | 'weighted' | 'cascade';

/**
 * RAG reranking strategy for result optimization
 * @source Story 12.5 - Plugin RAG API Client
 */
export type RAGRerankingStrategy = 'local' | 'cohere' | 'hybrid_auto';

/**
 * RAG query request for intelligent retrieval
 * @source Story 12.5 - Plugin RAG API Client
 * @verified backend/app/api/v1/endpoints/rag.py#RAGQueryRequest
 */
export interface RAGQueryRequest {
  query: string;
  canvas_file?: string;
  is_review_canvas?: boolean;
  fusion_strategy?: RAGFusionStrategy;
  reranking_strategy?: RAGRerankingStrategy;
}

/**
 * Single search result item from RAG query
 * @source Story 12.5 - Plugin RAG API Client
 */
export interface RAGSearchResultItem {
  doc_id: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

/**
 * RAG query latency information
 * @source Story 12.5 - Plugin RAG API Client
 */
export interface RAGLatencyInfo {
  graphiti?: number;
  lancedb?: number;
  multimodal?: number;
  fusion?: number;
  reranking?: number;
}

/**
 * RAG query metadata
 * @source Story 12.5 - Plugin RAG API Client
 */
export interface RAGQueryMetadata {
  query_rewritten: boolean;
  rewrite_count: number;
  fusion_strategy?: string;
  reranking_strategy?: string;
}

/**
 * RAG query response with results and metrics
 * @source Story 12.5 - Plugin RAG API Client
 * @verified backend/app/api/v1/endpoints/rag.py#RAGQueryResponse
 */
export interface RAGQueryResponse {
  results: RAGSearchResultItem[];
  quality_grade: 'high' | 'medium' | 'low';
  result_count: number;
  latency_ms: RAGLatencyInfo;
  total_latency_ms: number;
  metadata: RAGQueryMetadata;
}

/**
 * Single weak concept item
 * @source Story 12.5 - Plugin RAG API Client
 */
export interface WeakConceptItem {
  concept: string;
  stability: number;
  last_review?: string;
  review_count: number;
}

/**
 * Weak concepts response for review canvas generation
 * @source Story 12.5 - Plugin RAG API Client
 * @verified backend/app/api/v1/endpoints/rag.py#WeakConceptsResponse
 */
export interface WeakConceptsResponse {
  concepts: WeakConceptItem[];
  total_count: number;
  canvas_file: string;
}

/**
 * RAG service status response
 * @source Story 12.5 - Plugin RAG API Client
 * @verified backend/app/api/v1/endpoints/rag.py#RAGStatusResponse
 */
export interface RAGStatusResponse {
  available: boolean;
  initialized: boolean;
  langgraph_available: boolean;
  import_error?: string;
  timestamp: string;
}

// =============================================================================
// Configuration Types
// =============================================================================

/**
 * API client configuration options
 * @source Story 13.3 Dev Notes - ApiClientConfig
 */
export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number; // Default: 30000ms
  maxRetries?: number; // Default: 3
  retryBackoffMs?: number; // Default: 1000ms
}

/**
 * Retry policy configuration
 * @source Story 13.3 Dev Notes - RetryPolicy
 */
export interface RetryPolicy {
  maxRetries: number;
  backoffMs: number;
  retryableErrors: ErrorType[];
}

/**
 * Additional request options
 * @source Story 13.3 Dev Notes - RequestOptions
 */
export interface RequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

// =============================================================================
// Textbook API Types (Epic 28 - Bidirectional Textbook Links)
// =============================================================================

/**
 * Textbook section from parsed document
 * @source Epic 28 - 方案A: 前端同步到后端
 */
export interface TextbookSectionApi {
  id: string;
  title: string;
  level: number;
  preview: string;
  start_offset: number;
  end_offset: number;
  page_number?: number;
}

/**
 * Mounted textbook information for sync
 * @source Epic 28 - 方案A: 前端同步到后端
 */
export interface MountedTextbookApi {
  id: string;
  path: string;
  name: string;
  type: 'markdown' | 'pdf' | 'canvas';
  sections: TextbookSectionApi[];
}

/**
 * Request to sync mounted textbook to backend
 * @source Epic 28 - 方案A: 前端同步到后端
 * @verified backend/app/api/v1/endpoints/textbook.py#SyncMountRequest
 */
export interface SyncMountRequest {
  canvas_path: string;
  textbook: MountedTextbookApi;
}

/**
 * Response after syncing mounted textbook
 * @source Epic 28 - 方案A: 前端同步到后端
 * @verified backend/app/api/v1/endpoints/textbook.py#SyncMountResponse
 */
export interface SyncMountResponse {
  success: boolean;
  config_path: string;
  message: string;
  association_id: string;
}

/**
 * Request to unmount a textbook
 * @source Epic 28 - 方案A: 前端同步到后端
 * @verified backend/app/api/v1/endpoints/textbook.py#UnmountRequest
 */
export interface UnmountTextbookRequest {
  canvas_path: string;
  textbook_id: string;
}

/**
 * Response after unmounting textbook
 * @source Epic 28 - 方案A: 前端同步到后端
 * @verified backend/app/api/v1/endpoints/textbook.py#UnmountResponse
 */
export interface UnmountTextbookResponse {
  success: boolean;
  message: string;
}

/**
 * Response listing mounted textbooks for a canvas
 * @source Epic 28 - 方案A: 前端同步到后端
 * @verified backend/app/api/v1/endpoints/textbook.py#ListMountedResponse
 */
export interface ListMountedTextbooksResponse {
  canvas_path: string;
  associations: Record<string, unknown>[];
  config_path: string;
}
