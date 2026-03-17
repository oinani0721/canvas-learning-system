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
