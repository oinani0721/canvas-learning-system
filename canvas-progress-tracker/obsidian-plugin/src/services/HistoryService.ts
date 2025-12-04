/**
 * History Service - Canvas Learning System
 *
 * Service for managing review history data and trend analysis.
 * Implements Story 14.6: 复习历史查看 + 趋势分析
 *
 * @module HistoryService
 * @version 1.0.0
 */

import type { App } from 'obsidian';
import type {
    HistoryEntry,
    DailyStatItem,
    CanvasReviewTrend,
    ReviewSession,
    HistoryTimeRange,
    HistoryViewState,
    ReviewMode,
} from '../types/UITypes';
import { DEFAULT_HISTORY_STATE } from '../types/UITypes';
import type { DatabaseManager } from '../database/DatabaseManager';

/**
 * Service for managing review history and trend analysis
 */
export class HistoryService {
    private app: App;
    private dbManager: DatabaseManager | null = null;

    constructor(app: App) {
        this.app = app;
    }

    /**
     * Set database manager reference
     */
    setDatabaseManager(dbManager: DatabaseManager): void {
        this.dbManager = dbManager;
    }

    /**
     * Get review history entries for a time range
     * @param timeRange - Time range ('7d' or '30d')
     * @returns Promise<HistoryEntry[]>
     */
    async getReviewHistory(timeRange: HistoryTimeRange): Promise<HistoryEntry[]> {
        if (!this.dbManager) {
            console.warn('[HistoryService] Database manager not initialized');
            return [];
        }

        const days = timeRange === '7d' ? 7 : 30;
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const records = await reviewRecordDAO.getReviewsSince(startDate);

            return records.map((record: any) => ({
                id: record.id || `history-${Date.now()}-${Math.random()}`,
                canvasPath: record.canvas_path || record.canvasPath || '',
                canvasTitle: this.extractCanvasTitle(record.canvas_path || record.canvasPath || ''),
                conceptName: record.concept_name || record.conceptName || 'Unknown Concept',
                reviewDate: new Date(record.review_date || record.reviewDate || Date.now()),
                score: record.score || 0,
                mode: (record.mode || 'fresh') as ReviewMode,
                memoryStrength: record.memory_strength || record.memoryStrength || 0,
                duration: record.duration,
            }));
        } catch (error) {
            console.error('[HistoryService] Failed to get review history:', error);
            return [];
        }
    }

    /**
     * Get daily statistics for charts
     * @param timeRange - Time range ('7d' or '30d')
     * @returns Promise<DailyStatItem[]>
     */
    async getDailyStatistics(timeRange: HistoryTimeRange): Promise<DailyStatItem[]> {
        if (!this.dbManager) {
            console.warn('[HistoryService] Database manager not initialized');
            return this.generateEmptyDailyStats(timeRange);
        }

        const days = timeRange === '7d' ? 7 : 30;
        const dailyStats: DailyStatItem[] = [];

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();

            for (let i = days - 1; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                const dateStr = date.toISOString().split('T')[0];

                const dayStart = new Date(date);
                dayStart.setHours(0, 0, 0, 0);
                const dayEnd = new Date(date);
                dayEnd.setHours(23, 59, 59, 999);

                const dayRecords = await reviewRecordDAO.getReviewsInRange(dayStart, dayEnd);

                const conceptCount = dayRecords.length;
                const totalScore = dayRecords.reduce((sum: number, r: any) => sum + (r.score || 0), 0);
                const averageScore = conceptCount > 0 ? totalScore / conceptCount : 0;
                const totalMinutes = dayRecords.reduce((sum: number, r: any) => sum + ((r.duration || 0) / 60), 0);

                dailyStats.push({
                    date: dateStr,
                    conceptCount,
                    averageScore: Math.round(averageScore * 10) / 10,
                    totalMinutes: Math.round(totalMinutes),
                });
            }

            return dailyStats;
        } catch (error) {
            console.error('[HistoryService] Failed to get daily statistics:', error);
            return this.generateEmptyDailyStats(timeRange);
        }
    }

    /**
     * Get concept review history
     * @param conceptId - Concept identifier
     * @returns Promise<HistoryEntry[]>
     */
    async getConceptHistory(conceptId: string): Promise<HistoryEntry[]> {
        if (!this.dbManager) {
            return [];
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const records = await reviewRecordDAO.getConceptReviews(conceptId);

            return records.map((record: any) => ({
                id: record.id || `concept-${Date.now()}-${Math.random()}`,
                canvasPath: record.canvas_path || record.canvasPath || '',
                canvasTitle: this.extractCanvasTitle(record.canvas_path || record.canvasPath || ''),
                conceptName: record.concept_name || record.conceptName || conceptId,
                reviewDate: new Date(record.review_date || record.reviewDate || Date.now()),
                score: record.score || 0,
                mode: (record.mode || 'fresh') as ReviewMode,
                memoryStrength: record.memory_strength || record.memoryStrength || 0,
                duration: record.duration,
            }));
        } catch (error) {
            console.error('[HistoryService] Failed to get concept history:', error);
            return [];
        }
    }

    /**
     * Get canvas review trend for multi-review analysis
     * @param canvasPath - Canvas file path
     * @returns Promise<CanvasReviewTrend | null>
     */
    async getCanvasReviewTrend(canvasPath: string): Promise<CanvasReviewTrend | null> {
        if (!this.dbManager) {
            return null;
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const sessions = await reviewRecordDAO.getCanvasReviewSessions(canvasPath);

            if (sessions.length === 0) {
                return null;
            }

            const reviewSessions: ReviewSession[] = sessions.map((session: any) => ({
                date: new Date(session.date || session.review_date || Date.now()),
                passRate: session.pass_rate || session.passRate || 0,
                mode: (session.mode || 'fresh') as ReviewMode,
                conceptsReviewed: session.concepts_reviewed || session.conceptsReviewed || 0,
                weakConceptsCount: session.weak_concepts_count || session.weakConceptsCount || 0,
            }));

            // Calculate progress rate and trend
            const { progressRate, trend } = this.calculateProgressTrend(reviewSessions);

            return {
                canvasPath,
                canvasTitle: this.extractCanvasTitle(canvasPath),
                sessions: reviewSessions,
                progressRate,
                trend,
            };
        } catch (error) {
            console.error('[HistoryService] Failed to get canvas review trend:', error);
            return null;
        }
    }

    /**
     * Get all canvas review trends
     * @param timeRange - Time range
     * @returns Promise<CanvasReviewTrend[]>
     */
    async getAllCanvasTrends(timeRange: HistoryTimeRange): Promise<CanvasReviewTrend[]> {
        if (!this.dbManager) {
            return [];
        }

        try {
            const days = timeRange === '7d' ? 7 : 30;
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - days);

            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const canvasPaths = await reviewRecordDAO.getReviewedCanvasesSince(startDate);

            const trends: CanvasReviewTrend[] = [];
            for (const path of canvasPaths) {
                const trend = await this.getCanvasReviewTrend(path);
                if (trend) {
                    trends.push(trend);
                }
            }

            // Sort by progress rate descending
            return trends.sort((a, b) => b.progressRate - a.progressRate);
        } catch (error) {
            console.error('[HistoryService] Failed to get all canvas trends:', error);
            return [];
        }
    }

    /**
     * Load complete history view state
     * @param timeRange - Time range
     * @returns Promise<HistoryViewState>
     */
    async loadHistoryState(timeRange: HistoryTimeRange): Promise<HistoryViewState> {
        try {
            const [entries, dailyStats, canvasTrends] = await Promise.all([
                this.getReviewHistory(timeRange),
                this.getDailyStatistics(timeRange),
                this.getAllCanvasTrends(timeRange),
            ]);

            return {
                entries,
                dailyStats,
                canvasTrends,
                timeRange,
                loading: false,
            };
        } catch (error) {
            console.error('[HistoryService] Failed to load history state:', error);
            return {
                ...DEFAULT_HISTORY_STATE,
                timeRange,
                loading: false,
            };
        }
    }

    /**
     * Calculate progress trend from review sessions
     */
    private calculateProgressTrend(sessions: ReviewSession[]): { progressRate: number; trend: 'up' | 'down' | 'stable' } {
        if (sessions.length === 0) {
            return { progressRate: 0, trend: 'stable' };
        }

        if (sessions.length === 1) {
            return { progressRate: sessions[0].passRate * 100, trend: 'stable' };
        }

        // Sort by date
        const sorted = [...sessions].sort((a, b) => a.date.getTime() - b.date.getTime());

        // Calculate average pass rate
        const avgPassRate = sorted.reduce((sum, s) => sum + s.passRate, 0) / sorted.length;
        const progressRate = Math.round(avgPassRate * 100);

        // Determine trend (compare first half to second half)
        const midpoint = Math.floor(sorted.length / 2);
        const firstHalf = sorted.slice(0, midpoint);
        const secondHalf = sorted.slice(midpoint);

        const firstAvg = firstHalf.reduce((sum, s) => sum + s.passRate, 0) / firstHalf.length;
        const secondAvg = secondHalf.reduce((sum, s) => sum + s.passRate, 0) / secondHalf.length;

        const diff = secondAvg - firstAvg;
        let trend: 'up' | 'down' | 'stable';
        if (diff > 0.05) {
            trend = 'up';
        } else if (diff < -0.05) {
            trend = 'down';
        } else {
            trend = 'stable';
        }

        return { progressRate, trend };
    }

    /**
     * Extract canvas title from path
     */
    private extractCanvasTitle(canvasPath: string): string {
        if (!canvasPath) return 'Unknown Canvas';
        const parts = canvasPath.split('/');
        const fileName = parts[parts.length - 1];
        return fileName.replace('.canvas', '');
    }

    /**
     * Generate empty daily stats for a time range
     */
    private generateEmptyDailyStats(timeRange: HistoryTimeRange): DailyStatItem[] {
        const days = timeRange === '7d' ? 7 : 30;
        const stats: DailyStatItem[] = [];

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            stats.push({
                date: date.toISOString().split('T')[0],
                conceptCount: 0,
                averageScore: 0,
                totalMinutes: 0,
            });
        }

        return stats;
    }
}

/**
 * Create history service instance
 */
export function createHistoryService(app: App): HistoryService {
    return new HistoryService(app);
}
