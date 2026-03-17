/**
 * Canvas Learning System - API Client
 * Story 1.1: Plugin scaffold (AC-4)
 *
 * Provides REST communication with the FastAPI backend.
 * Handles snake_case <-> camelCase conversion and the API envelope format.
 */

import type { ApiResponse, HealthResponse } from '../types/api';

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
}
