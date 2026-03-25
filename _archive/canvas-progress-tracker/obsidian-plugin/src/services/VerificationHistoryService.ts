/**
 * Verification History Service - Canvas Learning System
 *
 * Service for managing verification canvas history and relationships.
 * Implements Story 14.13: 检验历史存储
 *
 * @module VerificationHistoryService
 * @version 1.0.0
 */

import type { App, TFile } from 'obsidian';
import type {
    VerificationCanvasRelation,
    VerificationViewState,
    ReviewMode,
    ReviewSession,
} from '../types/UITypes';
import { DEFAULT_VERIFICATION_STATE } from '../types/UITypes';
import type { DataManager } from '../database/DataManager';

/**
 * Storage key for verification canvas relations
 */
const STORAGE_KEY = 'canvas-review-verification-relations';

/**
 * Service for managing verification canvas history
 * [Source: PRD Story 14.13 - 检验历史存储]
 */
export class VerificationHistoryService {
    private app: App;
    private dbManager: DataManager | null = null;
    private relations: VerificationCanvasRelation[] = [];

    constructor(app: App) {
        this.app = app;
        this.loadRelations();
    }

    /**
     * Set data manager reference
     */
    setDataManager(dataManager: DataManager): void {
        this.dbManager = dataManager;
    }

    /**
     * Load relations from storage
     */
    private async loadRelations(): Promise<void> {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                this.relations = parsed.map((r: any) => ({
                    ...r,
                    generatedDate: new Date(r.generatedDate),
                    sessions: (r.sessions || []).map((s: any) => ({
                        ...s,
                        date: new Date(s.date),
                    })),
                }));
            }
        } catch (error) {
            console.error('[VerificationHistoryService] Failed to load relations:', error);
            this.relations = [];
        }
    }

    /**
     * Save relations to storage
     */
    private saveRelations(): void {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(this.relations));
        } catch (error) {
            console.error('[VerificationHistoryService] Failed to save relations:', error);
        }
    }

    /**
     * Get all verification canvas relations
     * @returns Promise<VerificationCanvasRelation[]>
     */
    async getAllRelations(): Promise<VerificationCanvasRelation[]> {
        // Validate that files still exist
        const validRelations: VerificationCanvasRelation[] = [];

        for (const relation of this.relations) {
            const verificationFile = this.app.vault.getAbstractFileByPath(
                relation.verificationCanvasPath
            );
            if (verificationFile) {
                validRelations.push(relation);
            }
            // else: file no longer exists in vault, skip it
        }

        // Sort by generation date (most recent first)
        return validRelations.sort(
            (a, b) => b.generatedDate.getTime() - a.generatedDate.getTime()
        );
    }

    /**
     * Get relations for a specific original canvas
     * @param originalCanvasPath - Path to the original canvas
     * @returns Promise<VerificationCanvasRelation[]>
     */
    async getRelationsForCanvas(
        originalCanvasPath: string
    ): Promise<VerificationCanvasRelation[]> {
        const allRelations = await this.getAllRelations();
        return allRelations.filter((r) => r.originalCanvasPath === originalCanvasPath);
    }

    /**
     * Add a new verification canvas relation
     * @param relation - The relation to add
     */
    async addRelation(
        originalCanvasPath: string,
        verificationCanvasPath: string,
        reviewMode: ReviewMode
    ): Promise<VerificationCanvasRelation> {
        const id = `vcr-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const originalTitle = this.extractCanvasTitle(originalCanvasPath);
        const verificationTitle = this.extractCanvasTitle(verificationCanvasPath);

        const newRelation: VerificationCanvasRelation = {
            id,
            originalCanvasPath,
            originalCanvasTitle: originalTitle,
            verificationCanvasPath,
            verificationCanvasTitle: verificationTitle,
            generatedDate: new Date(),
            reviewMode,
            currentScore: undefined,
            completionRate: 0,
            sessionCount: 0,
            sessions: [],
        };

        this.relations.push(newRelation);
        this.saveRelations();

        return newRelation;
    }

    /**
     * Update relation with review session data
     * @param relationId - Relation ID
     * @param session - Review session data
     */
    async addReviewSession(
        relationId: string,
        session: Omit<ReviewSession, 'date'>
    ): Promise<void> {
        const relation = this.relations.find((r) => r.id === relationId);
        if (!relation) {
            console.warn('[VerificationHistoryService] Relation not found:', relationId);
            return;
        }

        const newSession: ReviewSession = {
            ...session,
            date: new Date(),
        };

        relation.sessions.push(newSession);
        relation.sessionCount = relation.sessions.length;

        // Update current score (average of last 3 sessions)
        const recentSessions = relation.sessions.slice(-3);
        const avgPassRate =
            recentSessions.reduce((sum, s) => sum + s.passRate, 0) /
            recentSessions.length;
        relation.currentScore = avgPassRate * 5; // Convert to 1-5 scale

        // Update completion rate
        relation.completionRate = avgPassRate;

        this.saveRelations();
    }

    /**
     * Get verification view state
     */
    async getViewState(): Promise<VerificationViewState> {
        const relations = await this.getAllRelations();
        return {
            relations,
            loading: false,
            selectedRelationId: undefined,
        };
    }

    /**
     * Delete a verification relation
     * @param relationId - Relation ID to delete
     */
    async deleteRelation(relationId: string): Promise<void> {
        this.relations = this.relations.filter((r) => r.id !== relationId);
        this.saveRelations();
    }

    /**
     * Get recent verification canvases (for quick access)
     * @param limit - Maximum number of results
     */
    async getRecentVerificationCanvases(
        limit: number = 5
    ): Promise<VerificationCanvasRelation[]> {
        const allRelations = await this.getAllRelations();
        return allRelations.slice(0, limit);
    }

    /**
     * Get verification statistics
     */
    async getStatistics(): Promise<{
        totalVerificationCanvases: number;
        totalSessions: number;
        averageScore: number;
        averageCompletionRate: number;
    }> {
        const relations = await this.getAllRelations();

        const totalSessions = relations.reduce((sum, r) => sum + r.sessionCount, 0);

        const relationsWithScores = relations.filter(
            (r) => r.currentScore !== undefined
        );
        const averageScore =
            relationsWithScores.length > 0
                ? relationsWithScores.reduce((sum, r) => sum + (r.currentScore || 0), 0) /
                  relationsWithScores.length
                : 0;

        const averageCompletionRate =
            relations.length > 0
                ? relations.reduce((sum, r) => sum + (r.completionRate || 0), 0) /
                  relations.length
                : 0;

        return {
            totalVerificationCanvases: relations.length,
            totalSessions,
            averageScore,
            averageCompletionRate,
        };
    }

    /**
     * Find relation by verification canvas path
     */
    async findByVerificationCanvas(
        verificationCanvasPath: string
    ): Promise<VerificationCanvasRelation | undefined> {
        const allRelations = await this.getAllRelations();
        return allRelations.find(
            (r) => r.verificationCanvasPath === verificationCanvasPath
        );
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

    /**
     * Check if a canvas is a verification canvas
     */
    async isVerificationCanvas(canvasPath: string): Promise<boolean> {
        const relation = await this.findByVerificationCanvas(canvasPath);
        return relation !== undefined;
    }

    /**
     * Get the original canvas for a verification canvas
     */
    async getOriginalCanvas(
        verificationCanvasPath: string
    ): Promise<string | undefined> {
        const relation = await this.findByVerificationCanvas(verificationCanvasPath);
        return relation?.originalCanvasPath;
    }
}

/**
 * Factory function
 */
export function createVerificationHistoryService(app: App): VerificationHistoryService {
    return new VerificationHistoryService(app);
}
