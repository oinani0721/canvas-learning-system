/**
 * Canvas Learning System - API Types
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * Type definitions for backend API responses.
 *
 * [Source: backend/app/api/v1/system.py — health/config/test-llm endpoints]
 */

/** Standard API response envelope. */
export interface ApiResponse<T> {
  data: T;
  meta: {
    timestamp: string;
  };
}

/** Individual component health status. */
export interface ComponentStatus {
  name: string;
  status: "healthy" | "unhealthy" | "unknown";
  message?: string;
}

/** Aggregated system health response. */
export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  components: ComponentStatus[];
  timestamp: string;
}

/** LLM connection test result. */
export interface TestLlmResult {
  status: "success" | "failed";
  model?: string;
  error?: string;
}

/** Model config sync response. */
export interface ConfigSyncResult {
  status: string;
  message: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 3.12: LLM Usage Statistics Types
// [Source: backend/app/api/v1/system.py — LLMStatsResponse models]
// ═══════════════════════════════════════════════════════════════════════════

/** Summary statistics for LLM usage. */
export interface LlmStatsSummary {
  totalCalls: number;
  totalTokens: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCostUsd: number;
  avgLatencyMs: number;
  successRate: number;
}

/** Per-task-type statistics. */
export interface TaskTypeStats {
  taskType: string;
  calls: number;
  tokens: number;
  costUsd: number;
}

/** Per-day statistics. */
export interface DayStats {
  date: string;
  calls: number;
  tokens: number;
  costUsd: number;
}

/** Error statistics. */
export interface ErrorStats {
  total: number;
  byType: Record<string, number>;
}

/** LLM statistics data payload. */
export interface LlmStatsData {
  summary: LlmStatsSummary;
  byTask: TaskTypeStats[];
  byDay: DayStats[];
  errors: ErrorStats;
}

/** LLM statistics query metadata. */
export interface LlmStatsMeta {
  period: string;
  startDate: string;
  endDate: string;
  timestamp: string;
}

/** Full LLM statistics response. */
export interface LlmStatsResponse {
  data: LlmStatsData;
  meta: LlmStatsMeta;
}
