/**
 * FSRSStateQueryService - Canvas Learning System
 *
 * Story 32.3: FSRS State Query for Plugin Priority Calculation
 *
 * Provides functionality for:
 * - Querying backend for FSRS state (AC-32.3.1)
 * - Caching FSRS card data locally (AC-32.3.3)
 * - Graceful degradation when backend unavailable (AC-32.3.5)
 *
 * @module FSRSStateQueryService
 * @version 1.0.0
 * @source docs/stories/32.3.story.md
 */

import { App, requestUrl, RequestUrlParam } from 'obsidian';

/**
 * FSRS card state from backend
 *
 * Story 32.3 AC-32.3.2: Contains stability, difficulty, state, reps, lapses,
 * retrievability, and due date.
 *
 * [Source: specs/data/fsrs-state-query.schema.json#FSRSState]
 */
export interface FSRSState {
    /** Memory stability in days */
    stability: number;
    /** Difficulty coefficient (1-10) */
    difficulty: number;
    /** Card state: 0=New, 1=Learning, 2=Review, 3=Relearning */
    state: number;
    /** Successful review count */
    reps: number;
    /** Lapse count (rating=1) */
    lapses: number;
    /** Current retrievability probability (0-1) */
    retrievability: number | null;
    /** Next due date/time */
    due: string | null;
}

/**
 * Response from GET /api/v1/review/fsrs-state/{concept_id}
 *
 * [Source: specs/api/review-api.openapi.yml#FSRSStateQueryResponse]
 */
export interface FSRSStateQueryResponse {
    /** Concept identifier */
    concept_id: string;
    /** FSRS algorithm state (null if no card exists) */
    fsrs_state: FSRSState | null;
    /** Serialized FSRS card JSON for caching */
    card_state: string | null;
    /** Whether a card was found */
    found: boolean;
}

/**
 * Cached FSRS state with timestamp
 */
interface CachedFSRSState {
    state: FSRSStateQueryResponse;
    cachedAt: number;
}

/**
 * FSRSStateQueryService
 *
 * Story 32.3: Queries backend for FSRS state to enable plugin-side priority calculation.
 *
 * Features:
 * - Backend endpoint query with timeout handling
 * - Local caching of FSRS card states
 * - Graceful degradation when backend unavailable
 * - Batch query support for multiple concepts
 */
export class FSRSStateQueryService {
    private app: App;
    private baseUrl: string;
    private cache: Map<string, CachedFSRSState> = new Map();
    private readonly CACHE_TTL_MS = 5 * 60 * 1000; // 5 minute cache
    private readonly REQUEST_TIMEOUT_MS = 5000; // 5 second timeout
    private backendAvailable: boolean = true;
    private lastHealthCheck: number = 0;
    private readonly HEALTH_CHECK_INTERVAL_MS = 60 * 1000; // 1 minute health check interval

    /**
     * Create FSRSStateQueryService
     *
     * @param app - Obsidian App instance
     * @param backendUrl - Backend base URL (default: http://localhost:8000)
     */
    constructor(app: App, backendUrl: string = 'http://localhost:8000') {
        this.app = app;
        this.baseUrl = backendUrl;
    }

    /**
     * Query FSRS state for a concept
     *
     * Story 32.3 AC-32.3.1: Plugin queries backend for FSRS state before calculating priority.
     *
     * @param conceptId - Concept identifier (node_id)
     * @param forceRefresh - Force refresh from backend, bypass cache
     * @returns FSRSStateQueryResponse or null if unavailable
     */
    async queryFSRSState(
        conceptId: string,
        forceRefresh: boolean = false
    ): Promise<FSRSStateQueryResponse | null> {
        // Check cache first
        if (!forceRefresh) {
            const cached = this.getCachedState(conceptId);
            if (cached) {
                console.debug(`[FSRSStateQueryService] Cache hit for ${conceptId}`);
                return cached;
            }
        }

        // Check backend availability
        if (!this.backendAvailable) {
            await this.checkBackendHealth();
            if (!this.backendAvailable) {
                console.warn('[FSRSStateQueryService] Backend unavailable, returning null');
                return null;
            }
        }

        try {
            const url = `${this.baseUrl}/api/v1/review/fsrs-state/${encodeURIComponent(conceptId)}`;

            const requestParams: RequestUrlParam = {
                url,
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            const response = await requestUrl(requestParams);

            if (response.status === 200) {
                const data = response.json as FSRSStateQueryResponse;

                // Cache the result
                this.cacheState(conceptId, data);

                console.debug(
                    `[FSRSStateQueryService] Got FSRS state for ${conceptId}: found=${data.found}`
                );

                return data;
            }

            // 404 means concept not found - cache as not found
            if (response.status === 404) {
                const notFoundResponse: FSRSStateQueryResponse = {
                    concept_id: conceptId,
                    fsrs_state: null,
                    card_state: null,
                    found: false,
                };
                this.cacheState(conceptId, notFoundResponse);
                return notFoundResponse;
            }

            console.warn(
                `[FSRSStateQueryService] Unexpected response status: ${response.status}`
            );
            return null;
        } catch (error) {
            console.error(`[FSRSStateQueryService] Failed to query FSRS state for ${conceptId}:`, error);
            this.backendAvailable = false;
            return null;
        }
    }

    /**
     * Batch query FSRS states for multiple concepts
     *
     * Efficiently queries multiple concepts in parallel with rate limiting.
     *
     * @param conceptIds - Array of concept identifiers
     * @param forceRefresh - Force refresh from backend
     * @returns Map of conceptId to FSRSStateQueryResponse
     */
    async batchQueryFSRSStates(
        conceptIds: string[],
        forceRefresh: boolean = false
    ): Promise<Map<string, FSRSStateQueryResponse>> {
        const results = new Map<string, FSRSStateQueryResponse>();
        const toQuery: string[] = [];

        // Check cache first
        for (const conceptId of conceptIds) {
            if (!forceRefresh) {
                const cached = this.getCachedState(conceptId);
                if (cached) {
                    results.set(conceptId, cached);
                    continue;
                }
            }
            toQuery.push(conceptId);
        }

        // Query remaining concepts in parallel with concurrency limit
        const CONCURRENCY_LIMIT = 5;
        for (let i = 0; i < toQuery.length; i += CONCURRENCY_LIMIT) {
            const batch = toQuery.slice(i, i + CONCURRENCY_LIMIT);
            const batchResults = await Promise.all(
                batch.map((conceptId) => this.queryFSRSState(conceptId, true))
            );

            batchResults.forEach((result, index) => {
                if (result) {
                    results.set(batch[index], result);
                }
            });
        }

        return results;
    }

    /**
     * Get retrievability for a concept
     *
     * Story 32.3 AC-32.3.4: Uses retrievability in priority calculation.
     *
     * @param conceptId - Concept identifier
     * @returns Retrievability (0-1) or null if unavailable
     */
    async getRetrievability(conceptId: string): Promise<number | null> {
        const state = await this.queryFSRSState(conceptId);
        if (!state || !state.found || !state.fsrs_state) {
            return null;
        }
        return state.fsrs_state.retrievability;
    }

    /**
     * Get FSRS card state JSON for local caching/deserialization
     *
     * Story 32.3 AC-32.3.3: Plugin can cache full card_state for future use.
     *
     * @param conceptId - Concept identifier
     * @returns Card state JSON string or null
     */
    async getCardState(conceptId: string): Promise<string | null> {
        const state = await this.queryFSRSState(conceptId);
        if (!state || !state.found) {
            return null;
        }
        return state.card_state;
    }

    /**
     * Check if FSRS state exists for a concept
     *
     * @param conceptId - Concept identifier
     * @returns True if FSRS card exists
     */
    async hasCard(conceptId: string): Promise<boolean> {
        const state = await this.queryFSRSState(conceptId);
        return state?.found ?? false;
    }

    /**
     * Get cached state without network request
     *
     * @param conceptId - Concept identifier
     * @returns Cached response or null
     */
    getCachedState(conceptId: string): FSRSStateQueryResponse | null {
        const cached = this.cache.get(conceptId);
        if (!cached) {
            return null;
        }

        // Check if cache is still valid
        if (Date.now() - cached.cachedAt > this.CACHE_TTL_MS) {
            this.cache.delete(conceptId);
            return null;
        }

        return cached.state;
    }

    /**
     * Cache FSRS state
     *
     * @param conceptId - Concept identifier
     * @param state - FSRS state response
     */
    private cacheState(conceptId: string, state: FSRSStateQueryResponse): void {
        this.cache.set(conceptId, {
            state,
            cachedAt: Date.now(),
        });
    }

    /**
     * Check backend health
     *
     * Story 32.3 AC-32.3.5: Graceful degradation when backend unavailable.
     */
    private async checkBackendHealth(): Promise<void> {
        // Rate limit health checks
        if (Date.now() - this.lastHealthCheck < this.HEALTH_CHECK_INTERVAL_MS) {
            return;
        }

        this.lastHealthCheck = Date.now();

        try {
            const response = await requestUrl({
                url: `${this.baseUrl}/api/v1/health`,
                method: 'GET',
            });

            this.backendAvailable = response.status === 200;
            console.debug(
                `[FSRSStateQueryService] Backend health check: ${this.backendAvailable ? 'available' : 'unavailable'}`
            );
        } catch (error) {
            this.backendAvailable = false;
            console.warn('[FSRSStateQueryService] Backend health check failed:', error);
        }
    }

    /**
     * Clear the cache
     */
    clearCache(): void {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     */
    getCacheStats(): { size: number; hitRate: number } {
        return {
            size: this.cache.size,
            hitRate: 0, // Would need hit/miss tracking for accurate rate
        };
    }

    /**
     * Check if backend is available
     */
    isBackendAvailable(): boolean {
        return this.backendAvailable;
    }

    /**
     * Set backend URL
     *
     * @param url - New backend URL
     */
    setBackendUrl(url: string): void {
        this.baseUrl = url;
        this.backendAvailable = true; // Reset availability on URL change
        this.clearCache();
    }
}

/**
 * Create FSRSStateQueryService instance
 *
 * @param app - Obsidian App instance
 * @param backendUrl - Optional backend URL
 * @returns FSRSStateQueryService instance
 */
export function createFSRSStateQueryService(
    app: App,
    backendUrl?: string
): FSRSStateQueryService {
    return new FSRSStateQueryService(app, backendUrl);
}
