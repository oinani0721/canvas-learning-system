/**
 * MasteryService - Canvas Learning System
 *
 * API client for the BKT + FSRS hybrid mastery proficiency system.
 * Handles all communication with the /mastery/* backend endpoints.
 *
 * Also provides integration hooks for:
 * - NodeColorChangeWatcher → self-assess signals
 * - score_node response → mastery data extraction
 */

import { requestUrl } from 'obsidian';

// ============================================================================
// Types
// ============================================================================

export interface MasteryConceptResponse {
    concept_id: string;
    name: string;
    topic: string;
    effective_proficiency: number;
    mastery_level: number; // 0-4
    mastery_label: string;
    mastery_color: string; // hex
    retrievability: number;
    freshness: string; // fresh/recent/due/overdue
    override_active: boolean;
    override_value: number | null;
    self_assess_value: number | null;
    false_mastery_risk: number;
    interaction_count: number;
    fluent_count: number;
    p_mastery: number;
}

export interface TopicSummary {
    avg_proficiency: number;
    concept_count: number;
    exam_weight: number;
}

export interface MasteryBatchResponse {
    concepts: MasteryConceptResponse[];
    topic_summary: Record<string, TopicSummary>;
}

export interface MasteryServiceConfig {
    apiBaseUrl: string;
    timeout: number;
    enableLogging: boolean;
}

export const DEFAULT_MASTERY_SERVICE_CONFIG: MasteryServiceConfig = {
    apiBaseUrl: 'http://localhost:8000/api/v1',
    timeout: 10000,
    enableLogging: false,
};

// Mastery level metadata
export const MASTERY_LEVELS = [
    { level: 0, label: 'Not Assessed', color: '#6c757d', key: 'not_assessed' },
    { level: 1, label: 'Shaky', color: '#dc3545', key: 'shaky' },
    { level: 2, label: 'Developing', color: '#fd7e14', key: 'developing' },
    { level: 3, label: 'Proficient', color: '#0d6efd', key: 'proficient' },
    { level: 4, label: 'Mastered', color: '#198754', key: 'mastered' },
] as const;

// ============================================================================
// MasteryService Class
// ============================================================================

export class MasteryService {
    private config: MasteryServiceConfig;

    constructor(config?: Partial<MasteryServiceConfig>) {
        this.config = { ...DEFAULT_MASTERY_SERVICE_CONFIG, ...config };
    }

    // ========================================================================
    // API Methods
    // ========================================================================

    /**
     * Fetch all concepts' mastery state (batch).
     * Called on Sidebar open and manual refresh.
     */
    async getBatchMastery(groupId = 'cs188'): Promise<MasteryBatchResponse> {
        const url = `${this.config.apiBaseUrl}/mastery/batch?group_id=${encodeURIComponent(groupId)}`;
        try {
            const resp = await requestUrl({ url, method: 'GET' });
            return resp.json as MasteryBatchResponse;
        } catch (error) {
            this.log('getBatchMastery failed:', error);
            return { concepts: [], topic_summary: {} };
        }
    }

    /**
     * Record an interaction grade (1-4).
     */
    async recordGrade(
        conceptId: string,
        grade: number,
        topic = '',
        name = '',
        groupId = 'cs188',
    ): Promise<MasteryConceptResponse | null> {
        const url = `${this.config.apiBaseUrl}/mastery/${encodeURIComponent(conceptId)}/grade?group_id=${encodeURIComponent(groupId)}`;
        try {
            const resp = await requestUrl({
                url,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grade, topic, name }),
            });
            return resp.json as MasteryConceptResponse;
        } catch (error) {
            this.log('recordGrade failed:', error);
            return null;
        }
    }

    /**
     * Set explicit override from Sidebar (weight=0.8).
     */
    async setOverride(
        conceptId: string,
        level: string,
        reason = '',
        groupId = 'cs188',
    ): Promise<MasteryConceptResponse | null> {
        const url = `${this.config.apiBaseUrl}/mastery/${encodeURIComponent(conceptId)}/override?group_id=${encodeURIComponent(groupId)}`;
        try {
            const resp = await requestUrl({
                url,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level, reason }),
            });
            return resp.json as MasteryConceptResponse;
        } catch (error) {
            this.log('setOverride failed:', error);
            return null;
        }
    }

    /**
     * Record implicit self-assessment from Canvas color change (weight=0.5).
     */
    async selfAssess(
        conceptId: string,
        color: string,
        groupId = 'cs188',
    ): Promise<MasteryConceptResponse | null> {
        const url = `${this.config.apiBaseUrl}/mastery/${encodeURIComponent(conceptId)}/self-assess?group_id=${encodeURIComponent(groupId)}`;
        try {
            const resp = await requestUrl({
                url,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ color }),
            });
            return resp.json as MasteryConceptResponse;
        } catch (error) {
            this.log('selfAssess failed:', error);
            return null;
        }
    }

    /**
     * Reset override to model-computed value.
     */
    async resetOverride(
        conceptId: string,
        groupId = 'cs188',
    ): Promise<MasteryConceptResponse | null> {
        const url = `${this.config.apiBaseUrl}/mastery/${encodeURIComponent(conceptId)}/override?group_id=${encodeURIComponent(groupId)}`;
        try {
            const resp = await requestUrl({ url, method: 'DELETE' });
            return resp.json as MasteryConceptResponse;
        } catch (error) {
            this.log('resetOverride failed:', error);
            return null;
        }
    }

    // ========================================================================
    // Utilities
    // ========================================================================

    updateConfig(config: Partial<MasteryServiceConfig>): void {
        this.config = { ...this.config, ...config };
    }

    private log(...args: unknown[]): void {
        if (this.config.enableLogging) {
            console.log('[MasteryService]', ...args);
        }
    }
}

// ============================================================================
// Factory
// ============================================================================

export function createMasteryService(
    config?: Partial<MasteryServiceConfig>,
): MasteryService {
    return new MasteryService(config);
}
