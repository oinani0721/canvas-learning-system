/**
 * Review Record DAO - Canvas Learning System
 *
 * Data Access Object for review records.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module ReviewRecordDAO
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - ReviewRecordDAO类
 */

import { DatabaseManager } from './DatabaseManager';
import {
    ReviewRecord,
    ReviewRecordQueryOptions,
    DateRange,
    PaginatedResult,
    DifficultyLevel,
    ReviewStatus,
    DatabaseError,
} from '../types/DataTypes';

/**
 * Review Record DAO - Specialized access for review records
 *
 * Provides:
 * - CRUD operations for review records
 * - Query by canvas, date range, status
 * - Statistics aggregation
 * - Batch operations
 *
 * ✅ Verified from Story 14.1 Dev Notes: ReviewRecordDAO类实现
 */
export class ReviewRecordDAO {
    private dbManager: DatabaseManager;
    private static readonly TABLE_NAME = 'review_records';

    // Story 32.4 QA Improvement: Streak cache for performance optimization
    private streakCache: { value: number; timestamp: number } | null = null;
    private static readonly STREAK_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

    constructor(dbManager: DatabaseManager) {
        this.dbManager = dbManager;
    }

    /**
     * Invalidate streak cache when data changes
     * Story 32.4 QA Improvement: Cache invalidation on data mutation
     */
    private invalidateStreakCache(): void {
        this.streakCache = null;
    }

    // =========================================================================
    // CRUD Operations
    // =========================================================================

    /**
     * Create a new review record
     */
    async create(record: Omit<ReviewRecord, 'id' | 'createdAt' | 'updatedAt'>): Promise<ReviewRecord> {
        const fullRecord = {
            ...record,
            createdAt: new Date(),
            updatedAt: new Date(),
        };

        const result = await this.dbManager.insert<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            fullRecord
        );
        this.invalidateStreakCache(); // Story 32.4 QA: Invalidate cache on create
        return result;
    }

    /**
     * Get review record by ID
     */
    async getById(id: number): Promise<ReviewRecord | null> {
        return await this.dbManager.findById<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            id
        );
    }

    /**
     * Update a review record
     */
    async update(id: number, updates: Partial<ReviewRecord>): Promise<ReviewRecord | null> {
        const updatesWithTimestamp = {
            ...updates,
            updatedAt: new Date(),
        };

        const result = await this.dbManager.update<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            id,
            updatesWithTimestamp
        );
        this.invalidateStreakCache(); // Story 32.4 QA: Invalidate cache on update
        return result;
    }

    /**
     * Delete a review record
     */
    async delete(id: number): Promise<boolean> {
        const result = await this.dbManager.delete(ReviewRecordDAO.TABLE_NAME, id);
        this.invalidateStreakCache(); // Story 32.4 QA: Invalidate cache on delete
        return result;
    }

    // =========================================================================
    // Query Operations
    // =========================================================================

    /**
     * Find review records by canvas ID
     */
    async findByCanvasId(canvasId: string): Promise<ReviewRecord[]> {
        return await this.dbManager.findAll<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            {
                where: { canvasId },
                orderBy: 'reviewDate' as keyof ReviewRecord,
                orderDirection: 'DESC',
            }
        );
    }

    /**
     * Find review records by date range
     */
    async findByDateRange(dateRange: DateRange): Promise<ReviewRecord[]> {
        const allRecords = await this.dbManager.findAll<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME
        );

        return allRecords.filter((record) => {
            const reviewDate = new Date(record.reviewDate);
            return reviewDate >= dateRange.startDate && reviewDate <= dateRange.endDate;
        });
    }

    /**
     * Find review records by status
     */
    async findByStatus(status: ReviewStatus): Promise<ReviewRecord[]> {
        return await this.dbManager.findAll<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            {
                where: { status },
            }
        );
    }

    /**
     * Find review records by difficulty level
     */
    async findByDifficulty(difficultyLevel: DifficultyLevel): Promise<ReviewRecord[]> {
        return await this.dbManager.findAll<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME,
            {
                where: { difficultyLevel },
            }
        );
    }

    /**
     * Advanced query with multiple filters
     */
    async query(options: ReviewRecordQueryOptions): Promise<PaginatedResult<ReviewRecord>> {
        let records = await this.dbManager.findAll<ReviewRecord>(
            ReviewRecordDAO.TABLE_NAME
        );

        // Apply filters
        if (options.canvasId) {
            records = records.filter((r) => r.canvasId === options.canvasId);
        }

        if (options.status) {
            records = records.filter((r) => r.status === options.status);
        }

        if (options.difficultyLevel) {
            records = records.filter((r) => r.difficultyLevel === options.difficultyLevel);
        }

        if (options.dateRange) {
            records = records.filter((r) => {
                const reviewDate = new Date(r.reviewDate);
                return (
                    reviewDate >= options.dateRange!.startDate &&
                    reviewDate <= options.dateRange!.endDate
                );
            });
        }

        // Sort
        if (options.orderBy) {
            const direction = options.orderDirection === 'ASC' ? 1 : -1;
            records.sort((a, b) => {
                const aVal = a[options.orderBy!];
                const bVal = b[options.orderBy!];
                if (aVal === undefined || bVal === undefined) return 0;
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
        }

        const total = records.length;
        const offset = options.offset || 0;
        const limit = options.limit || 50;

        // Apply pagination
        records = records.slice(offset, offset + limit);

        return {
            data: records,
            total,
            limit,
            offset,
            hasMore: offset + records.length < total,
        };
    }

    /**
     * Get all review records
     */
    async getAll(): Promise<ReviewRecord[]> {
        return await this.dbManager.findAll<ReviewRecord>(ReviewRecordDAO.TABLE_NAME);
    }

    // =========================================================================
    // Statistics Operations
    // =========================================================================

    /**
     * Get review count by canvas
     */
    async getCountByCanvas(canvasId: string): Promise<number> {
        const records = await this.findByCanvasId(canvasId);
        return records.length;
    }

    /**
     * Get average score for a canvas
     */
    async getAverageScore(canvasId: string): Promise<number | null> {
        const records = await this.findByCanvasId(canvasId);
        const recordsWithScore = records.filter((r) => r.reviewScore !== undefined);

        if (recordsWithScore.length === 0) {
            return null;
        }

        const sum = recordsWithScore.reduce((acc, r) => acc + (r.reviewScore || 0), 0);
        return sum / recordsWithScore.length;
    }

    /**
     * Get average memory strength for a canvas
     */
    async getAverageMemoryStrength(canvasId: string): Promise<number> {
        const records = await this.findByCanvasId(canvasId);

        if (records.length === 0) {
            return 0;
        }

        const sum = records.reduce((acc, r) => acc + r.memoryStrength, 0);
        return sum / records.length;
    }

    /**
     * Get daily review statistics
     */
    async getDailyStats(date: Date): Promise<{
        totalReviews: number;
        totalDuration: number;
        averageScore: number | null;
        completedCount: number;
        skippedCount: number;
    }> {
        const startOfDay = new Date(date);
        startOfDay.setHours(0, 0, 0, 0);

        const endOfDay = new Date(date);
        endOfDay.setHours(23, 59, 59, 999);

        const records = await this.findByDateRange({
            startDate: startOfDay,
            endDate: endOfDay,
        });

        const totalReviews = records.length;
        const totalDuration = records.reduce((acc, r) => acc + r.reviewDuration, 0);
        const recordsWithScore = records.filter((r) => r.reviewScore !== undefined);
        const averageScore =
            recordsWithScore.length > 0
                ? recordsWithScore.reduce((acc, r) => acc + (r.reviewScore || 0), 0) /
                  recordsWithScore.length
                : null;
        const completedCount = records.filter((r) => r.status === 'completed').length;
        const skippedCount = records.filter((r) => r.status === 'skipped').length;

        return {
            totalReviews,
            totalDuration,
            averageScore,
            completedCount,
            skippedCount,
        };
    }

    /**
     * Get records due for review
     */
    async getDueForReview(beforeDate?: Date): Promise<ReviewRecord[]> {
        const cutoffDate = beforeDate || new Date();
        const allRecords = await this.getAll();

        return allRecords.filter((record) => {
            if (!record.nextReviewDate) {
                return false;
            }
            return new Date(record.nextReviewDate) <= cutoffDate;
        });
    }

    // =========================================================================
    // Batch Operations
    // =========================================================================

    /**
     * Create multiple review records
     */
    async createBatch(records: Omit<ReviewRecord, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<ReviewRecord[]> {
        const results: ReviewRecord[] = [];

        this.dbManager.beginTransaction();

        try {
            for (const record of records) {
                const created = await this.create(record);
                results.push(created);
            }
            await this.dbManager.commitTransaction();
        } catch (error) {
            await this.dbManager.rollbackTransaction();
            throw new DatabaseError(
                `Batch create failed: ${(error as Error).message}`,
                'TRANSACTION_ERROR',
                error as Error
            );
        }

        return results;
    }

    /**
     * Delete all records for a canvas
     */
    async deleteByCanvasId(canvasId: string): Promise<number> {
        const records = await this.findByCanvasId(canvasId);
        let deletedCount = 0;

        this.dbManager.beginTransaction();

        try {
            for (const record of records) {
                if (record.id !== undefined) {
                    await this.delete(record.id);
                    deletedCount++;
                }
            }
            await this.dbManager.commitTransaction();
        } catch (error) {
            await this.dbManager.rollbackTransaction();
            throw new DatabaseError(
                `Batch delete failed: ${(error as Error).message}`,
                'TRANSACTION_ERROR',
                error as Error
            );
        }

        return deletedCount;
    }

    /**
     * Update memory metrics for a record
     */
    async updateMemoryMetrics(
        id: number,
        memoryStrength: number,
        retentionRate: number,
        nextReviewDate?: Date
    ): Promise<ReviewRecord | null> {
        return await this.update(id, {
            memoryStrength,
            retentionRate,
            nextReviewDate,
        });
    }

    // =========================================================================
    // Story 14.6/14.7 Methods - History & Notifications
    // =========================================================================

    /**
     * Get pending reviews for a specific date (for notifications)
     * Story 14.7: 复习提醒通知
     */
    async getPendingReviewsForDate(date: Date): Promise<ReviewRecord[]> {
        const endOfDay = new Date(date);
        endOfDay.setHours(23, 59, 59, 999);

        const dueRecords = await this.getDueForReview(endOfDay);
        // Filter to only pending/scheduled status
        return dueRecords.filter((r) => r.status === 'pending' || r.status === 'scheduled');
    }

    /**
     * Get reviews since a start date (for history view)
     * Story 14.6: 复习历史查看
     */
    async getReviewsSince(startDate: Date): Promise<ReviewRecord[]> {
        return await this.findByDateRange({
            startDate,
            endDate: new Date(),
        });
    }

    /**
     * Get reviews within a date range (for daily statistics)
     * Story 14.6: 复习历史查看
     */
    async getReviewsInRange(startDate: Date, endDate: Date): Promise<ReviewRecord[]> {
        return await this.findByDateRange({
            startDate,
            endDate,
        });
    }

    /**
     * Get review history for a specific concept
     * Story 14.6: 复习历史查看
     */
    async getConceptReviews(conceptId: string): Promise<ReviewRecord[]> {
        const allRecords = await this.getAll();
        return allRecords
            .filter((r) => r.conceptId === conceptId)
            .sort((a, b) => new Date(b.reviewDate).getTime() - new Date(a.reviewDate).getTime());
    }

    /**
     * Get review count for a specific concept
     * Story 32.4 AC-32.4.1: reviewCount field filled with actual review history count
     *
     * @param conceptId - Unique concept identifier
     * @returns Number of times this concept has been reviewed
     */
    async getReviewCountByConceptId(conceptId: string): Promise<number> {
        const records = await this.getConceptReviews(conceptId);
        return records.length;
    }

    /**
     * Calculate consecutive review days (streak) ending today
     * Story 32.4 AC-32.4.2: streakDays field calculates consecutive review days
     * Story 32.4 QA Improvement: Added cache mechanism for performance optimization
     *
     * Algorithm:
     * 1. Check cache validity (TTL: 5 minutes)
     * 2. Get all review records if cache miss
     * 3. Extract unique review dates (normalized to YYYY-MM-DD)
     * 4. Starting from today, count consecutive days with reviews
     *
     * @returns Number of consecutive days with at least one review
     */
    async calculateStreakDays(): Promise<number> {
        // Story 32.4 QA: Check cache first
        const now = Date.now();
        if (this.streakCache && (now - this.streakCache.timestamp) < ReviewRecordDAO.STREAK_CACHE_TTL_MS) {
            return this.streakCache.value;
        }

        const allRecords = await this.getAll();
        if (allRecords.length === 0) {
            this.streakCache = { value: 0, timestamp: now };
            return 0;
        }

        // Extract unique review dates
        const reviewDates = new Set<string>();
        for (const record of allRecords) {
            if (record.reviewDate) {
                const dateKey = new Date(record.reviewDate).toISOString().split('T')[0];
                reviewDates.add(dateKey);
            }
        }

        if (reviewDates.size === 0) {
            this.streakCache = { value: 0, timestamp: now };
            return 0;
        }

        // Count consecutive days starting from today
        let streak = 0;
        const checkDate = new Date();

        while (reviewDates.has(checkDate.toISOString().split('T')[0])) {
            streak++;
            checkDate.setDate(checkDate.getDate() - 1);
        }

        // Story 32.4 QA: Update cache
        this.streakCache = { value: streak, timestamp: now };
        return streak;
    }

    /**
     * Batch query for review counts (performance optimization)
     * Story 32.4 Task 4.3: Batch query optimization
     *
     * @param conceptIds - Array of concept identifiers
     * @returns Map of conceptId to review count
     */
    async getReviewCountBatch(conceptIds: string[]): Promise<Map<string, number>> {
        const records = await this.getAll();
        const countMap = new Map<string, number>();

        // Initialize all requested concepts with 0
        for (const conceptId of conceptIds) {
            countMap.set(conceptId, 0);
        }

        // Count reviews for each concept
        for (const record of records) {
            if (record.conceptId && countMap.has(record.conceptId)) {
                countMap.set(record.conceptId, (countMap.get(record.conceptId) || 0) + 1);
            }
        }

        return countMap;
    }

    /**
     * Get review sessions for a canvas (grouped by session)
     * Story 14.6: 复习历史查看 + 趋势分析
     */
    async getCanvasReviewSessions(canvasPath: string): Promise<{
        date: Date;
        passRate: number;
        mode: string;
        conceptsReviewed: number;
        weakConceptsCount: number;
    }[]> {
        const records = await this.findByCanvasId(canvasPath);

        // Group records by day to form "sessions"
        const sessionMap = new Map<string, ReviewRecord[]>();

        for (const record of records) {
            const dateKey = new Date(record.reviewDate).toISOString().split('T')[0];
            if (!sessionMap.has(dateKey)) {
                sessionMap.set(dateKey, []);
            }
            sessionMap.get(dateKey)!.push(record);
        }

        const sessions: {
            date: Date;
            passRate: number;
            mode: string;
            conceptsReviewed: number;
            weakConceptsCount: number;
        }[] = [];

        for (const [dateKey, dayRecords] of sessionMap) {
            const conceptsReviewed = dayRecords.length;
            const passedCount = dayRecords.filter((r) =>
                r.status === 'completed' && (r.reviewScore || 0) >= 60
            ).length;
            const passRate = conceptsReviewed > 0 ? passedCount / conceptsReviewed : 0;
            const weakConceptsCount = dayRecords.filter((r) =>
                (r.reviewScore || 0) < 60
            ).length;

            // Determine mode based on if there's targeted review indicator
            const hasTargetedReview = dayRecords.some((r) =>
                r.difficultyLevel === 'hard' || r.memoryStrength < 0.5
            );
            const mode = hasTargetedReview ? 'targeted' : 'fresh';

            sessions.push({
                date: new Date(dateKey),
                passRate,
                mode,
                conceptsReviewed,
                weakConceptsCount,
            });
        }

        // Sort by date descending
        return sessions.sort((a, b) => b.date.getTime() - a.date.getTime());
    }

    /**
     * Get list of canvases that have been reviewed since a date
     * Story 14.6: 复习历史查看
     */
    async getReviewedCanvasesSince(startDate: Date): Promise<string[]> {
        const records = await this.getReviewsSince(startDate);
        const canvasSet = new Set<string>();

        for (const record of records) {
            if (record.canvasId) {
                canvasSet.add(record.canvasId);
            }
        }

        return Array.from(canvasSet);
    }
}
