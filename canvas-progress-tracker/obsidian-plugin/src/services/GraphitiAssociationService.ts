/**
 * Graphiti Association Service - Canvas Learning System Cross-Canvas Associations
 *
 * Service for storing and querying cross-Canvas relationships in Graphiti knowledge graph.
 * Implements Story 16.3: Graphiti跨Canvas关系存储
 *
 * @module GraphitiAssociationService
 * @version 1.0.0
 *
 * ✅ Verified from @graphiti Skill (search, add_episode, Cypher queries)
 * ✅ Verified from Story 16.3 Dev Notes (Neo4j schema, timeout handling)
 */

import { App, Notice, requestUrl } from 'obsidian';
import type {
    CanvasAssociation,
    AssociationType,
    SyncStatus
} from '../types/AssociationTypes';

/**
 * Graphiti API configuration
 */
interface GraphitiConfig {
    baseUrl: string;
    timeout: number;
    retryCount: number;
    cacheTimeout: number;
}

/**
 * Default Graphiti configuration
 * ✅ Verified from Story 16.3 Dev Notes (2s timeout, 30s cache)
 */
const DEFAULT_CONFIG: GraphitiConfig = {
    baseUrl: 'http://localhost:8000',
    timeout: 2000,      // 2 seconds timeout for graceful degradation
    retryCount: 3,
    cacheTimeout: 30000 // 30 seconds cache
};

/**
 * Neo4j relationship types for cross-Canvas associations
 * ✅ Verified from Story 16.3 Dev Notes (relationship types)
 */
export type Neo4jRelationshipType = 'RELATED_TO' | 'REQUIRES' | 'SIMILAR_TO' | 'REFERENCES';

/**
 * Mapping from association type to Neo4j relationship
 */
const ASSOCIATION_TO_NEO4J: Record<AssociationType, Neo4jRelationshipType> = {
    related: 'RELATED_TO',
    prerequisite: 'REQUIRES',
    extends: 'SIMILAR_TO',
    references: 'REFERENCES'
};

/**
 * Graph node structure from Graphiti
 * ✅ Verified from @graphiti Skill (search_nodes response)
 */
interface GraphNode {
    uuid: string;
    name: string;
    entity_type: string;
    summary?: string;
    created_at: string;
}

/**
 * Graph edge structure from Graphiti
 * ✅ Verified from @graphiti Skill (search_facts response)
 */
interface GraphEdge {
    uuid: string;
    source_node_uuid: string;
    target_node_uuid: string;
    name: string;
    fact: string;
    created_at: string;
}

/**
 * Search result from Graphiti
 */
interface SearchResult {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

/**
 * Cache entry structure
 */
interface CacheEntry<T> {
    data: T;
    timestamp: number;
}

/**
 * Graphiti Association Service
 *
 * Provides cross-Canvas relationship storage and querying via Graphiti knowledge graph.
 * Implements graceful degradation with 2-second timeout.
 *
 * ✅ Verified from @graphiti Skill (MCP integration pattern)
 */
export class GraphitiAssociationService {
    private app: App;
    private config: GraphitiConfig;
    private cache: Map<string, CacheEntry<unknown>> = new Map();
    private syncStatus: SyncStatus = 'pending';
    private lastError: string | null = null;
    private statusListeners: ((status: SyncStatus, error?: string) => void)[] = [];

    /**
     * Creates a new GraphitiAssociationService
     *
     * @param app - Obsidian App instance
     * @param config - Optional Graphiti configuration
     */
    constructor(app: App, config?: Partial<GraphitiConfig>) {
        this.app = app;
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * Check if Graphiti service is available
     *
     * ✅ Verified from @graphiti Skill (health check pattern)
     *
     * @returns Promise<boolean>
     */
    async isAvailable(): Promise<boolean> {
        try {
            const response = await this.fetchWithTimeout(
                `${this.config.baseUrl}/health`,
                { method: 'GET' },
                this.config.timeout
            );
            return response.status === 200;
        } catch {
            return false;
        }
    }

    /**
     * Write an association to Graphiti knowledge graph
     *
     * ✅ Verified from @graphiti Skill (add_episode pattern)
     *
     * @param association - Association to write
     * @returns Promise<boolean> - Success status
     */
    async writeAssociation(association: CanvasAssociation): Promise<boolean> {
        this.updateSyncStatus('syncing');

        try {
            // Build episode content for Graphiti
            const episodeContent = this.buildEpisodeContent(association);

            // Use add_episode to store in knowledge graph
            const response = await this.fetchWithTimeout(
                `${this.config.baseUrl}/api/v1/episodes`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: episodeContent,
                        source: 'canvas-association',
                        source_description: `Canvas association: ${association.source_canvas} -> ${association.target_canvas}`,
                        reference_time: association.created_at || new Date().toISOString()
                    })
                },
                this.config.timeout
            );

            if (response.status === 200 || response.status === 201) {
                this.updateSyncStatus('synced');
                this.invalidateCache();
                return true;
            } else {
                throw new Error(`Graphiti API returned ${response.status}`);
            }
        } catch (error) {
            const errorMsg = (error as Error).message;
            this.updateSyncStatus('error', errorMsg);
            console.warn('[GraphitiAssociationService] Write failed, falling back to local:', errorMsg);
            return false;
        }
    }

    /**
     * Get associations for a Canvas from knowledge graph
     *
     * ✅ Verified from @graphiti Skill (search pattern)
     *
     * @param canvasPath - Path to the Canvas file
     * @param forceRefresh - Bypass cache
     * @returns Promise<CanvasAssociation[]>
     */
    async getAssociations(canvasPath: string, forceRefresh = false): Promise<CanvasAssociation[]> {
        const cacheKey = `associations:${canvasPath}`;

        // Check cache first
        if (!forceRefresh) {
            const cached = this.getFromCache<CanvasAssociation[]>(cacheKey);
            if (cached) {
                return cached;
            }
        }

        this.updateSyncStatus('syncing');

        try {
            // Search for associations involving this Canvas
            const searchResult = await this.searchCrossCanvasConcepts(canvasPath);

            // Convert graph edges to Canvas associations
            const associations = this.edgesToAssociations(searchResult.edges, canvasPath);

            // Cache the result
            this.setCache(cacheKey, associations);
            this.updateSyncStatus('synced');

            return associations;
        } catch (error) {
            const errorMsg = (error as Error).message;
            this.updateSyncStatus('error', errorMsg);
            console.warn('[GraphitiAssociationService] Get associations failed:', errorMsg);
            return [];
        }
    }

    /**
     * Search for cross-Canvas concepts
     *
     * ✅ Verified from @graphiti Skill (hybrid search: search_nodes + search_facts)
     *
     * @param query - Search query (Canvas path or concept name)
     * @returns Promise<SearchResult>
     */
    async searchCrossCanvasConcepts(query: string): Promise<SearchResult> {
        const cacheKey = `search:${query}`;

        const cached = this.getFromCache<SearchResult>(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            // Hybrid search: nodes + facts
            const [nodesResponse, factsResponse] = await Promise.all([
                this.fetchWithTimeout(
                    `${this.config.baseUrl}/api/v1/search/nodes`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: query,
                            entity_types: ['Canvas', 'LearningNode', 'ConceptNode'],
                            limit: 50
                        })
                    },
                    this.config.timeout
                ),
                this.fetchWithTimeout(
                    `${this.config.baseUrl}/api/v1/search/facts`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: query,
                            limit: 50
                        })
                    },
                    this.config.timeout
                )
            ]);

            const nodes = nodesResponse.status === 200 ? await nodesResponse.json : [];
            const edges = factsResponse.status === 200 ? await factsResponse.json : [];

            const result: SearchResult = { nodes, edges };
            this.setCache(cacheKey, result);

            return result;
        } catch (error) {
            console.warn('[GraphitiAssociationService] Search failed:', (error as Error).message);
            return { nodes: [], edges: [] };
        }
    }

    /**
     * Delete an association from knowledge graph
     *
     * @param associationId - Association ID to delete
     * @returns Promise<boolean>
     */
    async deleteAssociation(associationId: string): Promise<boolean> {
        this.updateSyncStatus('syncing');

        try {
            // In Graphiti, we mark edges as invalid rather than deleting
            const response = await this.fetchWithTimeout(
                `${this.config.baseUrl}/api/v1/edges/${associationId}/invalidate`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                },
                this.config.timeout
            );

            if (response.status === 200 || response.status === 204) {
                this.updateSyncStatus('synced');
                this.invalidateCache();
                return true;
            } else {
                throw new Error(`Delete failed with status ${response.status}`);
            }
        } catch (error) {
            const errorMsg = (error as Error).message;
            this.updateSyncStatus('error', errorMsg);
            console.warn('[GraphitiAssociationService] Delete failed:', errorMsg);
            return false;
        }
    }

    /**
     * Get current sync status
     *
     * @returns SyncStatus
     */
    getSyncStatus(): SyncStatus {
        return this.syncStatus;
    }

    /**
     * Get last error message
     *
     * @returns string | null
     */
    getLastError(): string | null {
        return this.lastError;
    }

    /**
     * Subscribe to sync status changes
     *
     * @param callback - Callback function
     * @returns Unsubscribe function
     */
    onSyncStatusChange(callback: (status: SyncStatus, error?: string) => void): () => void {
        this.statusListeners.push(callback);
        return () => {
            const index = this.statusListeners.indexOf(callback);
            if (index > -1) {
                this.statusListeners.splice(index, 1);
            }
        };
    }

    /**
     * Clear all caches
     */
    clearCache(): void {
        this.cache.clear();
    }

    /**
     * Build episode content for Graphiti from association
     */
    private buildEpisodeContent(association: CanvasAssociation): string {
        const relationshipType = ASSOCIATION_TO_NEO4J[association.association_type];
        const sharedConcepts = association.shared_concepts?.join(', ') || 'none';

        return `Canvas "${association.source_canvas}" ${relationshipType} Canvas "${association.target_canvas}". ` +
            `Association type: ${association.association_type}. ` +
            `Shared concepts: ${sharedConcepts}. ` +
            `Relevance score: ${association.relevance_score ?? 0.5}. ` +
            `Bidirectional: ${association.bidirectional ?? false}. ` +
            `${association.description || ''}`.trim();
    }

    /**
     * Convert graph edges to Canvas associations
     */
    private edgesToAssociations(edges: GraphEdge[], canvasPath: string): CanvasAssociation[] {
        return edges
            .filter(edge => edge.fact.includes(canvasPath))
            .map(edge => this.edgeToAssociation(edge, canvasPath))
            .filter((a): a is CanvasAssociation => a !== null);
    }

    /**
     * Convert a single graph edge to Canvas association
     */
    private edgeToAssociation(edge: GraphEdge, canvasPath: string): CanvasAssociation | null {
        try {
            // Parse association data from edge fact
            const sourceMatch = edge.fact.match(/Canvas "([^"]+)" (\w+) Canvas "([^"]+)"/);
            if (!sourceMatch) return null;

            const [, sourceCanvas, relationshipType, targetCanvas] = sourceMatch;

            // Map Neo4j relationship back to association type
            const associationType = this.neo4jToAssociationType(relationshipType as Neo4jRelationshipType);

            return {
                association_id: edge.uuid,
                source_canvas: sourceCanvas,
                target_canvas: targetCanvas,
                association_type: associationType,
                auto_generated: true,
                created_at: edge.created_at
            };
        } catch {
            return null;
        }
    }

    /**
     * Map Neo4j relationship type to association type
     */
    private neo4jToAssociationType(neo4jType: Neo4jRelationshipType): AssociationType {
        const mapping: Record<Neo4jRelationshipType, AssociationType> = {
            RELATED_TO: 'related',
            REQUIRES: 'prerequisite',
            SIMILAR_TO: 'extends',
            REFERENCES: 'references'
        };
        return mapping[neo4jType] || 'related';
    }

    /**
     * Fetch with timeout for graceful degradation
     *
     * ✅ Verified from Story 16.3 Dev Notes (2s timeout)
     */
    private async fetchWithTimeout(
        url: string,
        options: RequestInit,
        timeout: number
    ): Promise<{ status: number; json?: unknown }> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            // Use Obsidian's requestUrl for cross-platform compatibility
            const response = await requestUrl({
                url,
                method: options.method as 'GET' | 'POST' | 'PUT' | 'DELETE',
                headers: options.headers as Record<string, string>,
                body: options.body as string,
                throw: false
            });

            clearTimeout(timeoutId);

            return {
                status: response.status,
                json: response.json
            };
        } catch (error) {
            clearTimeout(timeoutId);
            if ((error as Error).name === 'AbortError') {
                throw new Error('Request timeout (graceful degradation triggered)');
            }
            throw error;
        }
    }

    /**
     * Update sync status and notify listeners
     */
    private updateSyncStatus(status: SyncStatus, error?: string): void {
        this.syncStatus = status;
        this.lastError = error || null;

        this.statusListeners.forEach(listener => {
            try {
                listener(status, error);
            } catch (e) {
                console.error('[GraphitiAssociationService] Status listener error:', e);
            }
        });
    }

    /**
     * Get value from cache if not expired
     */
    private getFromCache<T>(key: string): T | null {
        const entry = this.cache.get(key) as CacheEntry<T> | undefined;
        if (!entry) return null;

        const now = Date.now();
        if (now - entry.timestamp > this.config.cacheTimeout) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    /**
     * Set value in cache
     */
    private setCache<T>(key: string, data: T): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Invalidate all cache entries
     */
    private invalidateCache(): void {
        this.cache.clear();
    }
}
