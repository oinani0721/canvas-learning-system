/**
 * Canvas Learning System - API Type Definitions
 * Story 1.1: Plugin scaffold (AC-5)
 *
 * Types mirroring the FastAPI backend response schemas.
 * All response types follow the envelope: { data: T, meta: { timestamp: string } }
 */

/** Status of a single infrastructure component. */
export interface ComponentStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  message?: string;
}

/** System-level health check response payload. */
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: ComponentStatus[];
  timestamp: string;
}

/** Standard API response envelope. */
export interface ApiResponse<T> {
  data: T;
  meta: {
    timestamp: string;
  };
}

/** Standard API error response. */
export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 1.6: Image index API types
// ═══════════════════════════════════════════════════════════════════════════

/** Request body for POST /api/v1/index/image */
export interface ImageIndexRequest {
  nodeId: string;
  imageData: string;  // base64 DataURL
}

/** Response from POST /api/v1/index/image */
export interface ImageIndexResult {
  nodeId: string;
  ocrText: string;
  summary: string;
  concepts: string[];
  processingTimeMs: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 1.5: Sync API types (AC-7)
// [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 7]
// ═══════════════════════════════════════════════════════════════════════════

/** A single sync operation from the frontend Outbox. */
export interface SyncOperation {
  operationId: string;
  entityType: 'node' | 'edge' | 'board';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  timestamp: string;
}

/** Batch request sent to POST /api/v1/sync/batch. */
export interface SyncBatchRequest {
  canvasId: string;
  subjectId?: string | null;
  operations: SyncOperation[];
}

/** Result of a single sync operation. */
export interface SyncOperationResult {
  operationId: string;
  success: boolean;
  error?: string | null;
}

/** Response from POST /api/v1/sync/batch. */
export interface SyncBatchResponse {
  results: SyncOperationResult[];
  syncedCount: number;
  failedCount: number;
}
