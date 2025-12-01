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
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public type: ErrorType,
    public statusCode?: number,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
    // Maintain prototype chain for instanceof checks
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * Get user-friendly error message based on error type
   * @source Story 13.3 Dev Notes - 错误处理策略表
   */
  getUserFriendlyMessage(): string {
    switch (this.type) {
      case 'NetworkError':
        return '无法连接到服务器，请检查网络连接';
      case 'TimeoutError':
        return '请求超时，请重试';
      case 'HttpError4xx':
        return `请求参数错误: ${this.message}`;
      case 'HttpError5xx':
        return '服务器错误，正在重试...';
      case 'ValidationError':
        return `数据验证失败: ${JSON.stringify(this.details)}`;
      default:
        return `未知错误: ${this.message}`;
    }
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
 * @verified specs/api/canvas-api.openapi.yml - 颜色代码: 1=红, 2=橙, 3=黄, 5=绿, 6=紫
 */
export type NodeColor = '1' | '2' | '3' | '5' | '6';

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
 */
export interface ScoreRequest {
  canvas_name: string;
  node_ids: string[];
}

/**
 * Individual node score with 4-dimension scoring
 * @source Story 13.3 Dev Notes - NodeScore
 */
export interface NodeScore {
  node_id: string;
  accuracy: number; // 0-10
  imagery: number; // 0-10
  completeness: number; // 0-10
  originality: number; // 0-10
  total: number; // 0-40
  new_color: NodeColor; // 5=green(>=32), 3=yellow(24-31), 1=red(<24)
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
 */
export interface ExplainRequest {
  canvas_name: string;
  node_id: string;
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
