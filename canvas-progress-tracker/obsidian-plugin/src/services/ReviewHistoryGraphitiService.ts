/**
 * ReviewHistoryGraphitiService - Canvas Learning System
 *
 * Story 14.13: 检验历史记录存储到Graphiti
 * Stores review canvas relationships to Graphiti knowledge graph for
 * tracking verification history across multiple review sessions.
 *
 * @module ReviewHistoryGraphitiService
 * @version 1.0.0
 */

import { App, requestUrl } from 'obsidian';

/**
 * Review mode types
 */
export type ReviewMode = 'fresh' | 'targeted';

/**
 * Concept result from review
 */
export interface ConceptResult {
    conceptId: string;
    conceptName: string;
    score: number;           // 0-100
    wasCorrect: boolean;
    attemptCount: number;
    timeSpent: number;       // milliseconds
    previouslyWeak: boolean; // Was this a targeted weak concept?
}

/**
 * Review session results
 */
export interface ReviewResults {
    totalConcepts: number;
    correctCount: number;
    averageScore: number;
    conceptResults: ConceptResult[];
    reviewDate: Date;
    durationMs: number;
}

/**
 * Review canvas relationship data
 */
export interface ReviewCanvasRelationship {
    reviewCanvasPath: string;
    originalCanvasPath: string;
    mode: ReviewMode;
    results: ReviewResults;
    createdAt: Date;
}

/**
 * Graphiti node representing a Canvas
 */
export interface CanvasNode {
    id: string;
    path: string;
    name: string;
    type: 'original' | 'review';
    createdAt: Date;
    lastModified?: Date;
}

/**
 * Graphiti relationship between canvases
 */
export interface CanvasRelationship {
    id: string;
    sourceId: string;     // Review canvas
    targetId: string;     // Original canvas
    relationshipType: 'GENERATED_FROM';
    mode: ReviewMode;
    results: ReviewResults;
    createdAt: Date;
}

/**
 * Weak concept from history analysis
 */
export interface WeakConcept {
    conceptId: string;
    conceptName: string;
    failureCount: number;
    lastFailureDate: Date;
    averageScore: number;
    trend: 'improving' | 'stable' | 'declining';
}

/**
 * Service settings
 */
export interface ReviewHistoryGraphitiSettings {
    apiBaseUrl: string;
    timeout: number;
    enableCaching: boolean;
    cacheExpiry: number;  // milliseconds
    autoSync: boolean;
    syncIntervalMinutes: number;
}

/**
 * Default settings
 */
export const DEFAULT_GRAPHITI_SETTINGS: ReviewHistoryGraphitiSettings = {
    apiBaseUrl: 'http://localhost:8000/api/v1',
    timeout: 10000,
    enableCaching: true,
    cacheExpiry: 5 * 60 * 1000, // 5 minutes
    autoSync: true,
    syncIntervalMinutes: 15,
};

/**
 * ReviewHistoryGraphitiService - Manages review history storage in Graphiti
 */
export class ReviewHistoryGraphitiService {
    private app: App;
    private settings: ReviewHistoryGraphitiSettings;
    private cache: Map<string, { data: any; timestamp: number }>;
    private syncInterval: NodeJS.Timer | null = null;
    private pendingWrites: ReviewCanvasRelationship[] = [];

    constructor(app: App, settings: Partial<ReviewHistoryGraphitiSettings> = {}) {
        this.app = app;
        this.settings = { ...DEFAULT_GRAPHITI_SETTINGS, ...settings };
        this.cache = new Map();
    }

    /**
     * Update settings
     */
    updateSettings(settings: Partial<ReviewHistoryGraphitiSettings>): void {
        this.settings = { ...this.settings, ...settings };
    }

    /**
     * Get current settings
     */
    getSettings(): ReviewHistoryGraphitiSettings {
        return { ...this.settings };
    }

    /**
     * Store review canvas relationship to Graphiti
     * Creates relationship: (review)-[:GENERATED_FROM {mode, results}]->(original)
     */
    async storeReviewCanvasRelationship(
        reviewCanvasPath: string,
        originalCanvasPath: string,
        mode: ReviewMode,
        results: ReviewResults
    ): Promise<boolean> {
        const relationship: ReviewCanvasRelationship = {
            reviewCanvasPath,
            originalCanvasPath,
            mode,
            results,
            createdAt: new Date(),
        };

        try {
            // Prepare Cypher query data
            const cypherData = this.buildCypherData(relationship);

            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/store`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'create_review_relationship',
                    data: cypherData,
                }),
            });

            if (response.status === 200 || response.status === 201) {
                // Clear relevant cache entries
                this.invalidateCache(originalCanvasPath);
                return true;
            }

            console.error('Failed to store review relationship:', response.status);
            // Add to pending writes for retry
            this.pendingWrites.push(relationship);
            return false;
        } catch (error) {
            console.error('Error storing review relationship to Graphiti:', error);
            // Add to pending writes for retry
            this.pendingWrites.push(relationship);
            return false;
        }
    }

    /**
     * Build Cypher query data for relationship creation
     */
    private buildCypherData(relationship: ReviewCanvasRelationship): object {
        return {
            cypher: `
                MERGE (original:Canvas {path: $original_path})
                ON CREATE SET original.name = $original_name,
                              original.type = 'original',
                              original.createdAt = datetime()
                MERGE (review:ReviewCanvas {path: $review_path})
                ON CREATE SET review.name = $review_name,
                              review.type = 'review',
                              review.createdAt = datetime($created_at)
                CREATE (review)-[r:GENERATED_FROM {
                    mode: $mode,
                    totalConcepts: $total_concepts,
                    correctCount: $correct_count,
                    averageScore: $average_score,
                    durationMs: $duration_ms,
                    reviewDate: datetime($review_date),
                    createdAt: datetime($created_at)
                }]->(original)
                RETURN review, r, original
            `,
            params: {
                original_path: relationship.originalCanvasPath,
                original_name: this.extractCanvasName(relationship.originalCanvasPath),
                review_path: relationship.reviewCanvasPath,
                review_name: this.extractCanvasName(relationship.reviewCanvasPath),
                mode: relationship.mode,
                total_concepts: relationship.results.totalConcepts,
                correct_count: relationship.results.correctCount,
                average_score: relationship.results.averageScore,
                duration_ms: relationship.results.durationMs,
                review_date: relationship.results.reviewDate.toISOString(),
                created_at: relationship.createdAt.toISOString(),
            },
            conceptResults: relationship.results.conceptResults,
        };
    }

    /**
     * Extract canvas name from path
     */
    private extractCanvasName(path: string): string {
        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.canvas', '');
    }

    /**
     * Query review history for a canvas
     */
    async queryReviewHistory(
        originalCanvasPath: string,
        limit: number = 10
    ): Promise<CanvasRelationship[]> {
        // Check cache first
        const cacheKey = `history:${originalCanvasPath}:${limit}`;
        const cached = this.getCachedData<CanvasRelationship[]>(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'query_review_history',
                    canvasPath: originalCanvasPath,
                    limit,
                }),
            });

            if (response.status === 200) {
                const relationships = this.parseRelationships(response.json);
                this.setCachedData(cacheKey, relationships);
                return relationships;
            }

            return [];
        } catch (error) {
            console.error('Error querying review history:', error);
            return [];
        }
    }

    /**
     * Parse relationships from API response
     */
    private parseRelationships(data: any): CanvasRelationship[] {
        if (!data?.relationships) {
            return [];
        }

        return data.relationships.map((rel: any) => ({
            id: rel.id,
            sourceId: rel.sourceId,
            targetId: rel.targetId,
            relationshipType: 'GENERATED_FROM' as const,
            mode: rel.mode as ReviewMode,
            results: {
                totalConcepts: rel.totalConcepts,
                correctCount: rel.correctCount,
                averageScore: rel.averageScore,
                conceptResults: rel.conceptResults || [],
                reviewDate: new Date(rel.reviewDate),
                durationMs: rel.durationMs,
            },
            createdAt: new Date(rel.createdAt),
        }));
    }

    /**
     * Query weak concepts from review history
     */
    async queryWeakConcepts(
        originalCanvasPath: string,
        lookbackDays: number = 30
    ): Promise<WeakConcept[]> {
        const cacheKey = `weak:${originalCanvasPath}:${lookbackDays}`;
        const cached = this.getCachedData<WeakConcept[]>(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'query_weak_concepts',
                    canvasPath: originalCanvasPath,
                    lookbackDays,
                }),
            });

            if (response.status === 200) {
                const weakConcepts = this.parseWeakConcepts(response.json);
                this.setCachedData(cacheKey, weakConcepts);
                return weakConcepts;
            }

            return [];
        } catch (error) {
            console.error('Error querying weak concepts:', error);
            return [];
        }
    }

    /**
     * Parse weak concepts from API response
     */
    private parseWeakConcepts(data: any): WeakConcept[] {
        if (!data?.weakConcepts) {
            return [];
        }

        return data.weakConcepts.map((concept: any) => ({
            conceptId: concept.conceptId,
            conceptName: concept.conceptName,
            failureCount: concept.failureCount,
            lastFailureDate: new Date(concept.lastFailureDate),
            averageScore: concept.averageScore,
            trend: concept.trend as WeakConcept['trend'],
        }));
    }

    /**
     * Query mastered concepts from review history
     */
    async queryMasteredConcepts(
        originalCanvasPath: string,
        minScore: number = 80,
        minAttempts: number = 3
    ): Promise<string[]> {
        const cacheKey = `mastered:${originalCanvasPath}:${minScore}:${minAttempts}`;
        const cached = this.getCachedData<string[]>(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'query_mastered_concepts',
                    canvasPath: originalCanvasPath,
                    minScore,
                    minAttempts,
                }),
            });

            if (response.status === 200 && response.json?.masteredConcepts) {
                this.setCachedData(cacheKey, response.json.masteredConcepts);
                return response.json.masteredConcepts;
            }

            return [];
        } catch (error) {
            console.error('Error querying mastered concepts:', error);
            return [];
        }
    }

    /**
     * Store concept result for individual tracking
     */
    async storeConceptResult(
        canvasPath: string,
        result: ConceptResult
    ): Promise<boolean> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/store`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'store_concept_result',
                    canvasPath,
                    result: {
                        ...result,
                        timestamp: new Date().toISOString(),
                    },
                }),
            });

            return response.status === 200 || response.status === 201;
        } catch (error) {
            console.error('Error storing concept result:', error);
            return false;
        }
    }

    /**
     * Get aggregated statistics for a canvas
     */
    async getCanvasStatistics(originalCanvasPath: string): Promise<{
        totalReviews: number;
        averageScore: number;
        lastReviewDate: Date | null;
        improvementTrend: number;
        weakConceptCount: number;
        masteredConceptCount: number;
    }> {
        const cacheKey = `stats:${originalCanvasPath}`;
        const cached = this.getCachedData<any>(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'get_canvas_statistics',
                    canvasPath: originalCanvasPath,
                }),
            });

            if (response.status === 200 && response.json) {
                const stats = {
                    totalReviews: response.json.totalReviews || 0,
                    averageScore: response.json.averageScore || 0,
                    lastReviewDate: response.json.lastReviewDate
                        ? new Date(response.json.lastReviewDate)
                        : null,
                    improvementTrend: response.json.improvementTrend || 0,
                    weakConceptCount: response.json.weakConceptCount || 0,
                    masteredConceptCount: response.json.masteredConceptCount || 0,
                };
                this.setCachedData(cacheKey, stats);
                return stats;
            }
        } catch (error) {
            console.error('Error getting canvas statistics:', error);
        }

        return {
            totalReviews: 0,
            averageScore: 0,
            lastReviewDate: null,
            improvementTrend: 0,
            weakConceptCount: 0,
            masteredConceptCount: 0,
        };
    }

    /**
     * Delete review canvas relationship
     */
    async deleteReviewRelationship(reviewCanvasPath: string): Promise<boolean> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/delete`,
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'delete_review_relationship',
                    reviewPath: reviewCanvasPath,
                }),
            });

            if (response.status === 200) {
                // Clear all cache
                this.clearCache();
                return true;
            }

            return false;
        } catch (error) {
            console.error('Error deleting review relationship:', error);
            return false;
        }
    }

    /**
     * Start auto-sync for pending writes
     */
    startAutoSync(): void {
        if (this.syncInterval) {
            return; // Already running
        }

        if (!this.settings.autoSync) {
            return;
        }

        this.syncInterval = setInterval(
            () => this.syncPendingWrites(),
            this.settings.syncIntervalMinutes * 60 * 1000
        );
    }

    /**
     * Stop auto-sync
     */
    stopAutoSync(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    /**
     * Sync pending writes to Graphiti
     */
    async syncPendingWrites(): Promise<number> {
        if (this.pendingWrites.length === 0) {
            return 0;
        }

        let successCount = 0;
        const failedWrites: ReviewCanvasRelationship[] = [];

        for (const relationship of this.pendingWrites) {
            try {
                const cypherData = this.buildCypherData(relationship);
                const response = await requestUrl({
                    url: `${this.settings.apiBaseUrl}/memory/graphiti/store`,
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        operation: 'create_review_relationship',
                        data: cypherData,
                    }),
                });

                if (response.status === 200 || response.status === 201) {
                    successCount++;
                } else {
                    failedWrites.push(relationship);
                }
            } catch (error) {
                failedWrites.push(relationship);
            }
        }

        this.pendingWrites = failedWrites;
        return successCount;
    }

    /**
     * Get pending write count
     */
    getPendingWriteCount(): number {
        return this.pendingWrites.length;
    }

    /**
     * Clear pending writes
     */
    clearPendingWrites(): void {
        this.pendingWrites = [];
    }

    /**
     * Cache management methods
     */
    private getCachedData<T>(key: string): T | null {
        if (!this.settings.enableCaching) {
            return null;
        }

        const cached = this.cache.get(key);
        if (!cached) {
            return null;
        }

        const now = Date.now();
        if (now - cached.timestamp > this.settings.cacheExpiry) {
            this.cache.delete(key);
            return null;
        }

        return cached.data as T;
    }

    private setCachedData(key: string, data: any): void {
        if (!this.settings.enableCaching) {
            return;
        }

        this.cache.set(key, {
            data,
            timestamp: Date.now(),
        });
    }

    private invalidateCache(canvasPath: string): void {
        const keysToDelete: string[] = [];
        this.cache.forEach((_, key) => {
            if (key.includes(canvasPath)) {
                keysToDelete.push(key);
            }
        });
        keysToDelete.forEach(key => this.cache.delete(key));
    }

    /**
     * Clear all cache
     */
    clearCache(): void {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     */
    getCacheStats(): { size: number; oldestEntry: number | null } {
        if (this.cache.size === 0) {
            return { size: 0, oldestEntry: null };
        }

        let oldestTimestamp = Date.now();
        this.cache.forEach(entry => {
            if (entry.timestamp < oldestTimestamp) {
                oldestTimestamp = entry.timestamp;
            }
        });

        return {
            size: this.cache.size,
            oldestEntry: oldestTimestamp,
        };
    }

    /**
     * Check Graphiti connection health
     */
    async checkHealth(): Promise<boolean> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/health`,
                method: 'GET',
            });
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    /**
     * Export state for persistence
     */
    exportState(): object {
        return {
            pendingWrites: this.pendingWrites,
            cacheStats: this.getCacheStats(),
        };
    }

    /**
     * Import state from persistence
     */
    importState(state: any): void {
        if (state?.pendingWrites && Array.isArray(state.pendingWrites)) {
            this.pendingWrites = state.pendingWrites.map((pw: any) => ({
                ...pw,
                results: {
                    ...pw.results,
                    reviewDate: new Date(pw.results.reviewDate),
                },
                createdAt: new Date(pw.createdAt),
            }));
        }
    }
}

/**
 * Factory function to create ReviewHistoryGraphitiService
 */
export function createReviewHistoryGraphitiService(
    app: App,
    settings?: Partial<ReviewHistoryGraphitiSettings>
): ReviewHistoryGraphitiService {
    return new ReviewHistoryGraphitiService(app, settings);
}
