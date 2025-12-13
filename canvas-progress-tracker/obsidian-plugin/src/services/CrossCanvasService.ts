/**
 * Cross-Canvas Learning Service - Canvas Learning System
 *
 * Service for managing cross-Canvas associations and knowledge paths.
 * Implements Epic 16: 跨Canvas关联学习系统
 * Extended by Story 25.3: Exercise-Lecture Canvas Association
 *
 * @module CrossCanvasService
 * @version 1.1.0
 */

import type { App, TFile } from 'obsidian';
import type {
    CrossCanvasAssociation,
    CrossCanvasSearchResult,
    KnowledgePath,
    KnowledgePathNode,
    CrossCanvasViewState,
    CanvasRelationshipType,
} from '../types/UITypes';
import { DEFAULT_CROSS_CANVAS_STATE } from '../types/UITypes';
import type { DataManager } from '../database/DataManager';

/**
 * Storage keys for cross-canvas data
 */
const ASSOCIATIONS_STORAGE_KEY = 'canvas-cross-canvas-associations';
const PATHS_STORAGE_KEY = 'canvas-knowledge-paths';

/**
 * Backend API base URL
 * [Source: Story 25.3 - Exercise-Lecture Canvas Association]
 */
const BACKEND_API_BASE = 'http://localhost:8000';

/**
 * Suggestion from backend for canvas association
 * [Source: Story 25.3 AC5 - Batch association suggestions]
 */
export interface CanvasAssociationSuggestion {
    target_canvas_path: string;
    target_canvas_title: string;
    relation_type: CanvasRelationshipType;
    confidence: number;
    reason: string;
    common_concepts: string[];
}

/**
 * Canvas node interface for internal use
 */
interface CanvasNode {
    id: string;
    type: string;
    text?: string;
    color?: string;
    x: number;
    y: number;
    width: number;
    height: number;
}

/**
 * Canvas data interface
 */
interface CanvasData {
    nodes: CanvasNode[];
    edges: Array<{
        id: string;
        fromNode: string;
        toNode: string;
    }>;
}

/**
 * Service for managing cross-Canvas learning relationships
 * [Source: PRD Epic 16 - 跨Canvas关联学习系统]
 */
export class CrossCanvasService {
    private app: App;
    private dbManager: DataManager | null = null;
    private associations: CrossCanvasAssociation[] = [];
    private knowledgePaths: KnowledgePath[] = [];

    constructor(app: App) {
        this.app = app;
        this.loadData();
    }

    /**
     * Set data manager reference
     */
    setDataManager(dataManager: DataManager): void {
        this.dbManager = dataManager;
    }

    /**
     * Load associations and paths from storage
     */
    private async loadData(): Promise<void> {
        try {
            // Load associations
            const storedAssociations = localStorage.getItem(ASSOCIATIONS_STORAGE_KEY);
            if (storedAssociations) {
                const parsed = JSON.parse(storedAssociations);
                this.associations = parsed.map((a: any) => ({
                    ...a,
                    createdDate: new Date(a.createdDate),
                    updatedDate: new Date(a.updatedDate),
                }));
            }

            // Load knowledge paths
            const storedPaths = localStorage.getItem(PATHS_STORAGE_KEY);
            if (storedPaths) {
                this.knowledgePaths = JSON.parse(storedPaths);
            }
        } catch (error) {
            console.error('[CrossCanvasService] Failed to load data:', error);
            this.associations = [];
            this.knowledgePaths = [];
        }
    }

    /**
     * Save associations to storage
     */
    private saveAssociations(): void {
        try {
            localStorage.setItem(ASSOCIATIONS_STORAGE_KEY, JSON.stringify(this.associations));
        } catch (error) {
            console.error('[CrossCanvasService] Failed to save associations:', error);
        }
    }

    /**
     * Save knowledge paths to storage
     */
    private savePaths(): void {
        try {
            localStorage.setItem(PATHS_STORAGE_KEY, JSON.stringify(this.knowledgePaths));
        } catch (error) {
            console.error('[CrossCanvasService] Failed to save paths:', error);
        }
    }

    // ============================================================================
    // Canvas File Operations
    // ============================================================================

    /**
     * Get all Canvas files in the vault
     * @returns Promise<TFile[]>
     */
    async getAllCanvasFiles(): Promise<TFile[]> {
        const files = this.app.vault.getFiles();
        return files.filter((file) => file.extension === 'canvas');
    }

    /**
     * Read Canvas data from a file
     * @param canvasPath - Path to the canvas file
     * @returns Promise<CanvasData | null>
     */
    private async readCanvasData(canvasPath: string): Promise<CanvasData | null> {
        try {
            const file = this.app.vault.getAbstractFileByPath(canvasPath);
            if (!(file instanceof this.app.vault.adapter.constructor) && file) {
                const content = await this.app.vault.read(file as TFile);
                return JSON.parse(content) as CanvasData;
            }
            return null;
        } catch (error) {
            console.error(`[CrossCanvasService] Failed to read canvas: ${canvasPath}`, error);
            return null;
        }
    }

    /**
     * Extract concepts from Canvas nodes
     * @param canvasData - Canvas data
     * @returns string[] - List of concepts
     */
    private extractConcepts(canvasData: CanvasData): string[] {
        const concepts: string[] = [];

        for (const node of canvasData.nodes) {
            if (node.type === 'text' && node.text) {
                // Extract first line as concept name
                const firstLine = node.text.split('\n')[0].trim();
                // Remove markdown headers
                const cleanConcept = firstLine.replace(/^#+\s*/, '').trim();
                if (cleanConcept && cleanConcept.length > 0 && cleanConcept.length < 100) {
                    concepts.push(cleanConcept);
                }
            }
        }

        return [...new Set(concepts)]; // Remove duplicates
    }

    /**
     * Extract canvas title from path
     */
    private extractCanvasTitle(canvasPath: string): string {
        if (!canvasPath) return 'Unknown Canvas';
        const parts = canvasPath.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.canvas', '');
    }

    // ============================================================================
    // Association Management
    // ============================================================================

    /**
     * Get all associations
     * @returns Promise<CrossCanvasAssociation[]>
     */
    async getAllAssociations(): Promise<CrossCanvasAssociation[]> {
        return this.associations.sort(
            (a, b) => b.updatedDate.getTime() - a.updatedDate.getTime()
        );
    }

    /**
     * Create a new Canvas association
     * [Source: PRD Epic 16 - 跨Canvas关联学习系统]
     *
     * @param sourceCanvasPath - Source canvas file path
     * @param targetCanvasPath - Target canvas file path
     * @param relationshipType - Type of relationship
     * @returns Promise<CrossCanvasAssociation>
     */
    async createCanvasAssociation(
        sourceCanvasPath: string,
        targetCanvasPath: string,
        relationshipType: CanvasRelationshipType
    ): Promise<CrossCanvasAssociation> {
        // Read both canvas files to find common concepts
        const sourceData = await this.readCanvasData(sourceCanvasPath);
        const targetData = await this.readCanvasData(targetCanvasPath);

        let commonConcepts: string[] = [];
        let confidence = 0.5;

        if (sourceData && targetData) {
            const sourceConcepts = this.extractConcepts(sourceData);
            const targetConcepts = this.extractConcepts(targetData);

            // Find common concepts (case-insensitive)
            const sourceSet = new Set(sourceConcepts.map((c) => c.toLowerCase()));
            commonConcepts = targetConcepts.filter((c) =>
                sourceSet.has(c.toLowerCase())
            );

            // Calculate confidence based on common concepts
            const totalUniqueConcepts =
                new Set([...sourceConcepts, ...targetConcepts]).size;
            if (totalUniqueConcepts > 0) {
                confidence = Math.min(1, commonConcepts.length / totalUniqueConcepts + 0.3);
            }
        }

        const id = `cca-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const now = new Date();

        const association: CrossCanvasAssociation = {
            id,
            sourceCanvasPath,
            sourceCanvasTitle: this.extractCanvasTitle(sourceCanvasPath),
            targetCanvasPath,
            targetCanvasTitle: this.extractCanvasTitle(targetCanvasPath),
            commonConcepts,
            relationshipType,
            confidence,
            createdDate: now,
            updatedDate: now,
        };

        this.associations.push(association);
        this.saveAssociations();

        return association;
    }

    /**
     * Update an existing association
     */
    async updateAssociation(
        associationId: string,
        updates: Partial<Omit<CrossCanvasAssociation, 'id' | 'createdDate'>>
    ): Promise<void> {
        const index = this.associations.findIndex((a) => a.id === associationId);
        if (index !== -1) {
            this.associations[index] = {
                ...this.associations[index],
                ...updates,
                updatedDate: new Date(),
            };
            this.saveAssociations();
        }
    }

    /**
     * Delete an association
     */
    async deleteAssociation(associationId: string): Promise<void> {
        this.associations = this.associations.filter((a) => a.id !== associationId);
        this.saveAssociations();
    }

    /**
     * Get associations for a specific canvas
     */
    async getAssociationsForCanvas(canvasPath: string): Promise<CrossCanvasAssociation[]> {
        return this.associations.filter(
            (a) => a.sourceCanvasPath === canvasPath || a.targetCanvasPath === canvasPath
        );
    }

    // ============================================================================
    // Intelligent Suggestions (Story 25.3)
    // ============================================================================

    /**
     * Get intelligent association suggestions from backend
     * [Source: Story 25.3 AC5 - Batch association suggestions]
     *
     * @param exerciseCanvasPath - Path to the exercise canvas
     * @param concept - Optional concept to search for
     * @returns Promise<CanvasAssociationSuggestion[]>
     */
    async getSuggestions(
        exerciseCanvasPath: string,
        concept?: string
    ): Promise<CanvasAssociationSuggestion[]> {
        try {
            const requestBody: {
                exercise_canvas_path: string;
                concept?: string;
            } = {
                exercise_canvas_path: exerciseCanvasPath,
            };

            if (concept) {
                requestBody.concept = concept;
            }

            const response = await fetch(`${BACKEND_API_BASE}/api/v1/cross-canvas/suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                console.error(
                    `[CrossCanvasService] Suggestions API error: ${response.status} ${response.statusText}`
                );
                // Fall back to local suggestions
                return this.getLocalSuggestions(exerciseCanvasPath);
            }

            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('[CrossCanvasService] Failed to get suggestions from backend:', error);
            // Fall back to local suggestions if backend is unavailable
            return this.getLocalSuggestions(exerciseCanvasPath);
        }
    }

    /**
     * Get local suggestions based on file naming and existing associations
     * Fallback when backend is unavailable
     * [Source: Story 25.3 - Local fallback logic]
     */
    private async getLocalSuggestions(
        exerciseCanvasPath: string
    ): Promise<CanvasAssociationSuggestion[]> {
        const suggestions: CanvasAssociationSuggestion[] = [];
        const canvasFiles = await this.getAllCanvasFiles();

        // Patterns that indicate lecture/textbook content
        const lecturePatterns = ['讲座', '讲义', '笔记', '知识点', '概念', '定义', '教材', 'lecture', 'notes'];
        const exercisePatterns = ['题目', '习题', '练习', '作业', '考试', '复习', '期末', 'exercise', 'problem'];

        // Check if source is an exercise canvas
        const sourceIsExercise = exercisePatterns.some(pattern =>
            exerciseCanvasPath.toLowerCase().includes(pattern)
        );

        if (!sourceIsExercise) {
            return []; // Only suggest for exercise canvases
        }

        // Find lecture canvases that might be related
        for (const file of canvasFiles) {
            if (file.path === exerciseCanvasPath) continue;

            const fileName = file.basename.toLowerCase();
            const isLecture = lecturePatterns.some(pattern => fileName.includes(pattern));

            if (isLecture) {
                // Check for name similarity
                const exerciseName = this.extractCanvasTitle(exerciseCanvasPath).toLowerCase();
                const lectureName = fileName;

                // Simple similarity: check for common words
                const exerciseWords = exerciseName.split(/[\s\-_]+/);
                const lectureWords = lectureName.split(/[\s\-_]+/);
                const commonWords = exerciseWords.filter(word =>
                    lectureWords.some(lw => lw.includes(word) || word.includes(lw))
                );

                let confidence = 0.3; // Base confidence
                if (commonWords.length > 0) {
                    confidence += 0.2 * Math.min(commonWords.length, 3);
                }

                suggestions.push({
                    target_canvas_path: file.path,
                    target_canvas_title: file.basename,
                    relation_type: 'exercise_lecture',
                    confidence,
                    reason: commonWords.length > 0
                        ? `文件名包含相似词: ${commonWords.join(', ')}`
                        : '检测到讲座/笔记Canvas',
                    common_concepts: commonWords,
                });
            }
        }

        // Sort by confidence
        return suggestions.sort((a, b) => b.confidence - a.confidence);
    }

    // ============================================================================
    // Concept Search
    // ============================================================================

    /**
     * Search for a concept across all Canvas files
     * [Source: PRD Epic 16 - 跨Canvas知识图谱查询]
     *
     * @param query - Search query
     * @returns Promise<CrossCanvasSearchResult[]>
     */
    async searchConceptAcrossCanvas(query: string): Promise<CrossCanvasSearchResult[]> {
        const results: Map<string, CrossCanvasSearchResult> = new Map();
        const canvasFiles = await this.getAllCanvasFiles();
        const queryLower = query.toLowerCase();

        for (const file of canvasFiles) {
            const canvasData = await this.readCanvasData(file.path);
            if (!canvasData) continue;

            for (const node of canvasData.nodes) {
                if (node.type === 'text' && node.text) {
                    const textLower = node.text.toLowerCase();

                    if (textLower.includes(queryLower)) {
                        // Extract concept name from node
                        const firstLine = node.text.split('\n')[0].trim();
                        const concept = firstLine.replace(/^#+\s*/, '').trim();

                        const occurrence = {
                            canvasPath: file.path,
                            canvasTitle: this.extractCanvasTitle(file.path),
                            nodeId: node.id,
                            nodeText: node.text.substring(0, 200), // Truncate for display
                            nodeColor: node.color || '',
                        };

                        if (results.has(concept)) {
                            const existing = results.get(concept)!;
                            existing.canvasOccurrences.push(occurrence);
                            existing.totalCount++;
                        } else {
                            results.set(concept, {
                                concept,
                                canvasOccurrences: [occurrence],
                                totalCount: 1,
                            });
                        }
                    }
                }
            }
        }

        // Sort by total count (most occurrences first)
        return Array.from(results.values()).sort((a, b) => b.totalCount - a.totalCount);
    }

    // ============================================================================
    // Knowledge Path Management
    // ============================================================================

    /**
     * Get all knowledge paths
     */
    async getAllKnowledgePaths(): Promise<KnowledgePath[]> {
        return this.knowledgePaths;
    }

    /**
     * Create a new knowledge path
     * [Source: PRD Epic 16 - 知识迁移路径]
     *
     * @param name - Path name
     * @param description - Path description
     * @param canvasPaths - Ordered list of canvas paths
     * @returns Promise<KnowledgePath>
     */
    async createKnowledgePath(
        name: string,
        description: string,
        canvasPaths: string[]
    ): Promise<KnowledgePath> {
        const nodes: KnowledgePathNode[] = [];

        for (let i = 0; i < canvasPaths.length; i++) {
            const canvasPath = canvasPaths[i];
            const canvasData = await this.readCanvasData(canvasPath);
            const concepts = canvasData ? this.extractConcepts(canvasData) : [];

            nodes.push({
                canvasPath,
                canvasTitle: this.extractCanvasTitle(canvasPath),
                order: i + 1,
                prerequisiteConcepts: concepts.slice(0, 5), // Top 5 concepts
                masteryLevel: 0,
                isCompleted: false,
            });
        }

        const id = `kp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const path: KnowledgePath = {
            id,
            name,
            description,
            nodes,
            completionProgress: 0,
            recommendedNext: nodes[0],
        };

        this.knowledgePaths.push(path);
        this.savePaths();

        return path;
    }

    /**
     * Update node mastery in a knowledge path
     */
    async updateNodeMastery(
        pathId: string,
        canvasPath: string,
        masteryLevel: number,
        isCompleted: boolean
    ): Promise<void> {
        const path = this.knowledgePaths.find((p) => p.id === pathId);
        if (!path) return;

        const node = path.nodes.find((n) => n.canvasPath === canvasPath);
        if (!node) return;

        node.masteryLevel = masteryLevel;
        node.isCompleted = isCompleted;

        // Recalculate completion progress
        const completedCount = path.nodes.filter((n) => n.isCompleted).length;
        path.completionProgress = completedCount / path.nodes.length;

        // Update recommended next
        const nextIncomplete = path.nodes.find((n) => !n.isCompleted);
        path.recommendedNext = nextIncomplete;

        this.savePaths();
    }

    /**
     * Delete a knowledge path
     */
    async deleteKnowledgePath(pathId: string): Promise<void> {
        this.knowledgePaths = this.knowledgePaths.filter((p) => p.id !== pathId);
        this.savePaths();
    }

    /**
     * Get knowledge path by ID
     */
    async getKnowledgePath(pathId: string): Promise<KnowledgePath | undefined> {
        return this.knowledgePaths.find((p) => p.id === pathId);
    }

    /**
     * Auto-generate knowledge path based on associations
     * [Source: PRD Epic 16 - 智能路径生成]
     */
    async autoGenerateKnowledgePath(
        startCanvasPath: string,
        name: string
    ): Promise<KnowledgePath | null> {
        const visited = new Set<string>();
        const pathOrder: string[] = [startCanvasPath];
        visited.add(startCanvasPath);

        // BFS to find connected canvases through associations
        const queue = [startCanvasPath];

        while (queue.length > 0) {
            const current = queue.shift()!;
            const associations = await this.getAssociationsForCanvas(current);

            for (const assoc of associations) {
                const nextCanvas =
                    assoc.sourceCanvasPath === current
                        ? assoc.targetCanvasPath
                        : assoc.sourceCanvasPath;

                if (!visited.has(nextCanvas)) {
                    visited.add(nextCanvas);
                    pathOrder.push(nextCanvas);
                    queue.push(nextCanvas);
                }
            }
        }

        if (pathOrder.length < 2) {
            return null; // Not enough connected canvases
        }

        return this.createKnowledgePath(
            name,
            `Auto-generated path starting from ${this.extractCanvasTitle(startCanvasPath)}`,
            pathOrder
        );
    }

    // ============================================================================
    // View State
    // ============================================================================

    /**
     * Get cross-canvas view state
     */
    async getViewState(): Promise<CrossCanvasViewState> {
        const associations = await this.getAllAssociations();
        const knowledgePaths = await this.getAllKnowledgePaths();

        return {
            associations,
            searchResults: [],
            knowledgePaths,
            searchQuery: '',
            loading: false,
            selectedAssociationId: undefined,
        };
    }

    // ============================================================================
    // Statistics
    // ============================================================================

    /**
     * Get cross-canvas statistics
     */
    async getStatistics(): Promise<{
        totalAssociations: number;
        totalPaths: number;
        totalCanvasesLinked: number;
        averagePathCompletion: number;
    }> {
        const associations = await this.getAllAssociations();
        const paths = await this.getAllKnowledgePaths();

        // Count unique canvases in associations
        const linkedCanvases = new Set<string>();
        for (const assoc of associations) {
            linkedCanvases.add(assoc.sourceCanvasPath);
            linkedCanvases.add(assoc.targetCanvasPath);
        }

        // Calculate average path completion
        const avgCompletion =
            paths.length > 0
                ? paths.reduce((sum, p) => sum + p.completionProgress, 0) / paths.length
                : 0;

        return {
            totalAssociations: associations.length,
            totalPaths: paths.length,
            totalCanvasesLinked: linkedCanvases.size,
            averagePathCompletion: avgCompletion,
        };
    }
}

/**
 * Factory function
 */
export function createCrossCanvasService(app: App): CrossCanvasService {
    return new CrossCanvasService(app);
}
