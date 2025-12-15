/**
 * MemoryQueryService - 3-Layer Memory System Query Integration
 *
 * Story 14.9: 3层记忆系统查询工具集成
 *
 * Integrates Graphiti (knowledge graph), Temporal (time-based events),
 * and Semantic (vector-based) memory layers for comprehensive review scheduling.
 *
 * @module MemoryQueryService
 * @version 1.0.0
 */

import { App, requestUrl } from 'obsidian';

// =============================================================================
// Types and Interfaces
// =============================================================================

/**
 * Memory layer types
 */
export type MemoryLayerType = 'graphiti' | 'temporal' | 'semantic';

/**
 * Memory layer status
 */
export interface MemoryLayerStatus {
    name: MemoryLayerType;
    status: 'up' | 'down' | 'unknown';
    lastChecked?: Date;
    errorMessage?: string;
}

/**
 * Concept relationship from Graphiti knowledge graph
 */
export interface ConceptRelationship {
    /** Source concept ID */
    sourceId: string;
    /** Source concept name */
    sourceName: string;
    /** Target concept ID */
    targetId: string;
    /** Target concept name */
    targetName: string;
    /** Relationship type */
    relationType: 'prerequisite' | 'related' | 'extends' | 'contradicts' | 'applies_to';
    /** Relationship strength (0-1) */
    strength: number;
    /** Canvas file where relationship was established */
    canvasSource?: string;
}

/**
 * Temporal event from time-based memory
 */
export interface TemporalEvent {
    /** Event ID */
    id: string;
    /** Session ID */
    sessionId: string;
    /** Event type */
    eventType: 'learning' | 'review' | 'scoring' | 'decomposition' | 'explanation';
    /** When the event occurred */
    timestamp: Date;
    /** Canvas file name */
    canvasName: string;
    /** Concept involved */
    conceptName: string;
    /** Event metadata */
    metadata?: Record<string, unknown>;
}

/**
 * Semantic memory result from vector search
 */
export interface SemanticResult {
    /** Document ID */
    documentId: string;
    /** Document path */
    documentPath: string;
    /** Content snippet */
    contentSnippet: string;
    /** Relevance score (0-1) */
    relevanceScore: number;
    /** Related concept */
    conceptName?: string;
    /** Document type */
    documentType: 'explanation' | 'example' | 'note' | 'canvas';
}

/**
 * Combined memory query result
 */
export interface MemoryQueryResult {
    /** Query timestamp */
    timestamp: Date;
    /** Query concept */
    concept: string;
    /** Results from Graphiti */
    graphitiResults: ConceptRelationship[];
    /** Results from Temporal memory */
    temporalResults: TemporalEvent[];
    /** Results from Semantic memory */
    semanticResults: SemanticResult[];
    /** Aggregated priority score (0-100) */
    priorityScore: number;
    /** Whether all layers responded */
    allLayersResponded: boolean;
    /** Layer-specific errors */
    layerErrors: Record<MemoryLayerType, string | null>;
}

/**
 * Review priority calculation result
 */
export interface ReviewPriority {
    /** Concept name */
    conceptName: string;
    /** Canvas containing the concept */
    canvasName: string;
    /** Node ID in canvas */
    nodeId?: string;
    /** Priority score (0-100) */
    priorityScore: number;
    /** Score breakdown */
    scoreBreakdown: {
        /** FSRS-based priority (40%) */
        fsrsScore: number;
        /** Behavior-based priority (30%) */
        behaviorScore: number;
        /** Relationship-based priority (20%) */
        relationshipScore: number;
        /** Interaction-based priority (10%) */
        interactionScore: number;
    };
    /** Days since last review */
    daysSinceLastReview: number;
    /** Related concepts that need review */
    relatedConceptsNeedingReview: string[];
    /** Recommended review date */
    recommendedReviewDate: Date;
}

/**
 * Memory query service settings
 */
export interface MemoryQuerySettings {
    /** API base URL */
    apiBaseUrl: string;
    /** Request timeout in ms */
    timeout: number;
    /** Enable Graphiti queries */
    enableGraphiti: boolean;
    /** Enable Temporal queries */
    enableTemporal: boolean;
    /** Enable Semantic queries */
    enableSemantic: boolean;
    /** Cache duration in ms */
    cacheDuration: number;
}

/**
 * Default settings
 */
export const DEFAULT_MEMORY_QUERY_SETTINGS: MemoryQuerySettings = {
    apiBaseUrl: 'http://localhost:8000/api/v1',
    timeout: 10000,
    enableGraphiti: true,
    enableTemporal: true,
    enableSemantic: true,
    cacheDuration: 5 * 60 * 1000, // 5 minutes
};

// =============================================================================
// MemoryQueryService Class
// =============================================================================

/**
 * Service for querying the 3-layer memory system
 *
 * Architecture:
 * - Graphiti: Knowledge graph for concept relationships
 * - Temporal: Time-based events (Neo4j-backed)
 * - Semantic: Vector-based document search (ChromaDB-backed)
 */
export class MemoryQueryService {
    private app: App;
    private settings: MemoryQuerySettings;
    private cache: Map<string, { result: MemoryQueryResult; timestamp: number }>;
    private layerStatus: Map<MemoryLayerType, MemoryLayerStatus>;

    constructor(app: App, settings?: Partial<MemoryQuerySettings>) {
        this.app = app;
        this.settings = { ...DEFAULT_MEMORY_QUERY_SETTINGS, ...settings };
        this.cache = new Map();
        this.layerStatus = new Map([
            ['graphiti', { name: 'graphiti', status: 'unknown' }],
            ['temporal', { name: 'temporal', status: 'unknown' }],
            ['semantic', { name: 'semantic', status: 'unknown' }],
        ]);
    }

    /**
     * Update service settings
     */
    updateSettings(settings: Partial<MemoryQuerySettings>): void {
        this.settings = { ...this.settings, ...settings };
    }

    /**
     * Get current settings
     */
    getSettings(): MemoryQuerySettings {
        return { ...this.settings };
    }

    /**
     * Check health of all memory layers
     */
    async checkLayerHealth(): Promise<MemoryLayerStatus[]> {
        const results: MemoryLayerStatus[] = [];

        // Check Graphiti
        if (this.settings.enableGraphiti) {
            const graphitiStatus = await this.checkSingleLayerHealth('graphiti');
            results.push(graphitiStatus);
        }

        // Check Temporal
        if (this.settings.enableTemporal) {
            const temporalStatus = await this.checkSingleLayerHealth('temporal');
            results.push(temporalStatus);
        }

        // Check Semantic
        if (this.settings.enableSemantic) {
            const semanticStatus = await this.checkSingleLayerHealth('semantic');
            results.push(semanticStatus);
        }

        return results;
    }

    /**
     * Check health of a single memory layer
     */
    private async checkSingleLayerHealth(layer: MemoryLayerType): Promise<MemoryLayerStatus> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/${layer}/health`,
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });

            const status: MemoryLayerStatus = {
                name: layer,
                status: response.status === 200 ? 'up' : 'down',
                lastChecked: new Date(),
            };

            this.layerStatus.set(layer, status);
            return status;
        } catch (error) {
            const status: MemoryLayerStatus = {
                name: layer,
                status: 'down',
                lastChecked: new Date(),
                errorMessage: error instanceof Error ? error.message : 'Unknown error',
            };

            this.layerStatus.set(layer, status);
            return status;
        }
    }

    /**
     * Get layer status (cached)
     */
    getLayerStatus(): MemoryLayerStatus[] {
        return Array.from(this.layerStatus.values());
    }

    /**
     * Query all memory layers for a concept
     */
    async queryConceptMemory(concept: string, forceRefresh = false): Promise<MemoryQueryResult> {
        // Check cache
        const cacheKey = `concept:${concept}`;
        if (!forceRefresh) {
            const cached = this.cache.get(cacheKey);
            if (cached && Date.now() - cached.timestamp < this.settings.cacheDuration) {
                return cached.result;
            }
        }

        const result: MemoryQueryResult = {
            timestamp: new Date(),
            concept,
            graphitiResults: [],
            temporalResults: [],
            semanticResults: [],
            priorityScore: 0,
            allLayersResponded: true,
            layerErrors: {
                graphiti: null,
                temporal: null,
                semantic: null,
            },
        };

        // Query all layers in parallel
        const [graphitiResult, temporalResult, semanticResult] = await Promise.allSettled([
            this.settings.enableGraphiti ? this.queryGraphiti(concept) : Promise.resolve([]),
            this.settings.enableTemporal ? this.queryTemporal(concept) : Promise.resolve([]),
            this.settings.enableSemantic ? this.querySemantic(concept) : Promise.resolve([]),
        ]);

        // Process Graphiti results
        if (graphitiResult.status === 'fulfilled') {
            result.graphitiResults = graphitiResult.value;
        } else {
            result.allLayersResponded = false;
            result.layerErrors.graphiti = graphitiResult.reason?.message || 'Query failed';
        }

        // Process Temporal results
        if (temporalResult.status === 'fulfilled') {
            result.temporalResults = temporalResult.value;
        } else {
            result.allLayersResponded = false;
            result.layerErrors.temporal = temporalResult.reason?.message || 'Query failed';
        }

        // Process Semantic results
        if (semanticResult.status === 'fulfilled') {
            result.semanticResults = semanticResult.value;
        } else {
            result.allLayersResponded = false;
            result.layerErrors.semantic = semanticResult.reason?.message || 'Query failed';
        }

        // Calculate aggregated priority score
        result.priorityScore = this.calculatePriorityScore(result);

        // Update cache
        this.cache.set(cacheKey, { result, timestamp: Date.now() });

        return result;
    }

    /**
     * Query Graphiti knowledge graph for concept relationships
     */
    private async queryGraphiti(concept: string): Promise<ConceptRelationship[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ concept }),
                throw: false,
            });

            if (response.status === 200) {
                return response.json.relationships || [];
            }

            // Return empty array if endpoint not available
            return [];
        } catch (error) {
            console.error('Graphiti query failed:', error);
            return [];
        }
    }

    /**
     * Query Temporal memory for time-based events
     */
    private async queryTemporal(concept: string): Promise<TemporalEvent[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/temporal/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ concept }),
                throw: false,
            });

            if (response.status === 200) {
                const events = response.json.events || [];
                return events.map((e: any) => ({
                    ...e,
                    timestamp: new Date(e.timestamp),
                }));
            }

            return [];
        } catch (error) {
            console.error('Temporal query failed:', error);
            return [];
        }
    }

    /**
     * Query Semantic memory for related documents
     */
    private async querySemantic(concept: string): Promise<SemanticResult[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/semantic/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: concept, limit: 10 }),
                throw: false,
            });

            if (response.status === 200) {
                return response.json.results || [];
            }

            return [];
        } catch (error) {
            console.error('Semantic query failed:', error);
            return [];
        }
    }

    /**
     * Calculate aggregated priority score from all memory layers
     *
     * Weight distribution:
     * - FSRS-based: 40%
     * - Behavior-based: 30%
     * - Relationship-based: 20%
     * - Interaction-based: 10%
     */
    private calculatePriorityScore(result: MemoryQueryResult): number {
        let totalScore = 0;

        // 1. Calculate relationship score from Graphiti (20%)
        const relationshipScore = this.calculateRelationshipScore(result.graphitiResults);
        totalScore += relationshipScore * 0.2;

        // 2. Calculate behavior score from Temporal (30%)
        const behaviorScore = this.calculateBehaviorScore(result.temporalResults);
        totalScore += behaviorScore * 0.3;

        // 3. Calculate interaction score from Semantic (10%)
        const interactionScore = this.calculateInteractionScore(result.semanticResults);
        totalScore += interactionScore * 0.1;

        // 4. FSRS score would come from external source (40%) - placeholder
        // This will be calculated by the FSRS engine separately
        const fsrsPlaceholder = 50; // Neutral default
        totalScore += fsrsPlaceholder * 0.4;

        return Math.round(Math.min(100, Math.max(0, totalScore)));
    }

    /**
     * Calculate relationship-based priority score
     */
    private calculateRelationshipScore(relationships: ConceptRelationship[]): number {
        if (relationships.length === 0) return 50; // Neutral if no data

        // Higher score for concepts with more/stronger relationships
        const avgStrength = relationships.reduce((sum, r) => sum + r.strength, 0) / relationships.length;
        const countBonus = Math.min(relationships.length * 5, 30); // Max 30 bonus for count

        return Math.min(100, avgStrength * 70 + countBonus);
    }

    /**
     * Calculate behavior-based priority score
     */
    private calculateBehaviorScore(events: TemporalEvent[]): number {
        if (events.length === 0) return 50; // Neutral if no data

        // Score based on recency and frequency of events
        const now = new Date();
        const oneDay = 24 * 60 * 60 * 1000;
        const oneWeek = 7 * oneDay;

        let recencyScore = 0;
        let frequencyScore = Math.min(events.length * 10, 50);

        // More recent events = higher priority for review
        const mostRecent = events[0]?.timestamp;
        if (mostRecent) {
            const daysSince = (now.getTime() - mostRecent.getTime()) / oneDay;
            if (daysSince > 7) {
                recencyScore = 80; // Needs review
            } else if (daysSince > 3) {
                recencyScore = 60;
            } else {
                recencyScore = 30; // Recently reviewed
            }
        }

        return Math.min(100, (recencyScore + frequencyScore) / 2);
    }

    /**
     * Calculate interaction-based priority score
     */
    private calculateInteractionScore(results: SemanticResult[]): number {
        if (results.length === 0) return 50; // Neutral if no data

        // Higher relevance = more connected concept
        const avgRelevance = results.reduce((sum, r) => sum + r.relevanceScore, 0) / results.length;
        return Math.min(100, avgRelevance * 100);
    }

    /**
     * Get review priorities for concepts in a canvas
     */
    async getReviewPriorities(canvasName: string): Promise<ReviewPriority[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/review-priorities`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ canvas_name: canvasName }),
                throw: false,
            });

            if (response.status === 200) {
                return (response.json.priorities || []).map((p: any) => ({
                    ...p,
                    recommendedReviewDate: new Date(p.recommendedReviewDate),
                }));
            }

            return [];
        } catch (error) {
            console.error('Failed to get review priorities:', error);
            return [];
        }
    }

    /**
     * Store a learning event to temporal memory
     */
    async storeTemporalEvent(event: Omit<TemporalEvent, 'id'>): Promise<boolean> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/temporal/store`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...event,
                    timestamp: event.timestamp.toISOString(),
                }),
                throw: false,
            });

            return response.status === 200 || response.status === 201;
        } catch (error) {
            console.error('Failed to store temporal event:', error);
            return false;
        }
    }

    /**
     * Store a concept relationship to Graphiti
     */
    async storeConceptRelationship(relationship: Omit<ConceptRelationship, 'sourceId' | 'targetId'>): Promise<boolean> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/store`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(relationship),
                throw: false,
            });

            return response.status === 200 || response.status === 201;
        } catch (error) {
            console.error('Failed to store concept relationship:', error);
            return false;
        }
    }

    /**
     * Clear cache
     */
    clearCache(): void {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     */
    getCacheStats(): { size: number; oldestEntry: number | null } {
        let oldestTimestamp: number | null = null;

        for (const entry of this.cache.values()) {
            if (oldestTimestamp === null || entry.timestamp < oldestTimestamp) {
                oldestTimestamp = entry.timestamp;
            }
        }

        return {
            size: this.cache.size,
            oldestEntry: oldestTimestamp,
        };
    }
}

// =============================================================================
// Factory Function
// =============================================================================

/**
 * Create a new MemoryQueryService instance
 */
export function createMemoryQueryService(
    app: App,
    settings?: Partial<MemoryQuerySettings>
): MemoryQueryService {
    return new MemoryQueryService(app, settings);
}
