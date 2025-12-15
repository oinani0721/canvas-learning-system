/**
 * Canvas Learning System - Backend Health Service
 *
 * Provides health check functionality for the backend server.
 * Used by the plugin to verify backend availability on startup.
 *
 * @module BackendHealthService
 * @version 1.0.1
 */

import { requestUrl, RequestUrlResponse } from 'obsidian';

export interface HealthStatus {
    status: 'healthy' | 'unhealthy' | 'unreachable';
    app_name?: string;
    version?: string;
    timestamp?: string;
    error?: string;
    responseTime?: number;
}

export interface BackendHealthServiceConfig {
    baseUrl: string;
    timeout?: number;
    retryCount?: number;
    retryDelay?: number;
}

/**
 * BackendHealthService - Checks backend server health
 *
 * Features:
 * - Health endpoint polling
 * - Retry logic with exponential backoff
 * - Connection status tracking
 */
export class BackendHealthService {
    private baseUrl: string;
    private timeout: number;
    private retryCount: number;
    private retryDelay: number;
    private lastHealthStatus: HealthStatus | null = null;

    constructor(config: BackendHealthServiceConfig) {
        this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.timeout = config.timeout ?? 5000;
        this.retryCount = config.retryCount ?? 3;
        this.retryDelay = config.retryDelay ?? 1000;
    }

    /**
     * Check backend health with retry logic
     *
     * @returns Health status object
     */
    async checkHealth(): Promise<HealthStatus> {
        let lastError: string | undefined;

        for (let attempt = 1; attempt <= this.retryCount; attempt++) {
            try {
                const startTime = Date.now();

                // Use Obsidian's requestUrl instead of fetch for consistency
                // This bypasses CORS issues in Electron environment
                const timeoutPromise = new Promise<never>((_, reject) =>
                    setTimeout(() => reject(new Error('Connection timeout')), this.timeout)
                );

                const requestPromise = requestUrl({
                    url: `${this.baseUrl}/health`,
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                    },
                    throw: false,
                });

                const response: RequestUrlResponse = await Promise.race([
                    requestPromise,
                    timeoutPromise,
                ]);

                const responseTime = Date.now() - startTime;

                if (response.status >= 200 && response.status < 300) {
                    const data = response.json;
                    this.lastHealthStatus = {
                        status: 'healthy',
                        app_name: data.app_name,
                        version: data.version,
                        timestamp: data.timestamp,
                        responseTime,
                    };
                    return this.lastHealthStatus;
                } else {
                    lastError = `HTTP ${response.status}`;
                }
            } catch (error) {
                if (error instanceof Error) {
                    lastError = error.message;
                } else {
                    lastError = 'Unknown error';
                }
            }

            // Wait before retry (exponential backoff)
            if (attempt < this.retryCount) {
                await this.sleep(this.retryDelay * Math.pow(2, attempt - 1));
            }
        }

        // All retries failed
        this.lastHealthStatus = {
            status: 'unreachable',
            error: lastError,
        };
        return this.lastHealthStatus;
    }

    /**
     * Quick health check (single attempt, shorter timeout)
     *
     * @returns Health status object
     */
    async quickCheck(): Promise<HealthStatus> {
        try {
            const startTime = Date.now();

            // Use Obsidian's requestUrl instead of fetch for consistency
            const timeoutPromise = new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error('Connection timeout')), 2000)
            );

            const requestPromise = requestUrl({
                url: `${this.baseUrl}/health`,
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                throw: false,
            });

            const response: RequestUrlResponse = await Promise.race([
                requestPromise,
                timeoutPromise,
            ]);

            const responseTime = Date.now() - startTime;

            if (response.status >= 200 && response.status < 300) {
                const data = response.json;
                return {
                    status: 'healthy',
                    app_name: data.app_name,
                    version: data.version,
                    timestamp: data.timestamp,
                    responseTime,
                };
            } else {
                return {
                    status: 'unhealthy',
                    error: `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            return {
                status: 'unreachable',
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }

    /**
     * Get last known health status
     */
    getLastHealthStatus(): HealthStatus | null {
        return this.lastHealthStatus;
    }

    /**
     * Check if backend is available (based on last check)
     */
    isAvailable(): boolean {
        return this.lastHealthStatus?.status === 'healthy';
    }

    /**
     * Get backend URL
     */
    getBaseUrl(): string {
        return this.baseUrl;
    }

    /**
     * Update base URL (useful when settings change)
     */
    setBaseUrl(url: string): void {
        this.baseUrl = url.replace(/\/$/, '');
        this.lastHealthStatus = null; // Reset status when URL changes
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Create BackendHealthService instance
 *
 * @param baseUrl - API base URL (e.g., 'http://localhost:8001/api/v1')
 * @param options - Optional configuration
 */
export function createBackendHealthService(
    baseUrl: string,
    options?: Partial<BackendHealthServiceConfig>
): BackendHealthService {
    return new BackendHealthService({
        baseUrl,
        ...options,
    });
}
