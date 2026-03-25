/**
 * Learning Session DAO - Canvas Learning System
 *
 * Data Access Object for learning sessions.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module LearningSessionDAO
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - LearningSessionDAO类
 */

import { DatabaseManager } from './DatabaseManager';
import {
    LearningSession,
    SessionQueryOptions,
    DateRange,
    PaginatedResult,
    SessionType,
    DatabaseError,
} from '../types/DataTypes';

/**
 * Learning Session DAO - Specialized access for learning sessions
 *
 * Provides:
 * - CRUD operations for learning sessions
 * - Active session management
 * - Session statistics
 * - Query by type and date
 *
 * ✅ Verified from Story 14.1 Dev Notes: LearningSessionDAO类实现
 */
export class LearningSessionDAO {
    private dbManager: DatabaseManager;
    private static readonly TABLE_NAME = 'learning_sessions';

    constructor(dbManager: DatabaseManager) {
        this.dbManager = dbManager;
    }

    // =========================================================================
    // CRUD Operations
    // =========================================================================

    /**
     * Create a new learning session
     */
    async create(session: Omit<LearningSession, 'id' | 'createdAt' | 'updatedAt'>): Promise<LearningSession> {
        const fullSession = {
            ...session,
            createdAt: new Date(),
            updatedAt: new Date(),
        };

        return await this.dbManager.insert<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            fullSession
        );
    }

    /**
     * Get learning session by ID
     */
    async getById(id: number): Promise<LearningSession | null> {
        return await this.dbManager.findById<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            id
        );
    }

    /**
     * Get learning session by session ID (UUID)
     */
    async getBySessionId(sessionId: string): Promise<LearningSession | null> {
        const sessions = await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            {
                where: { sessionId },
                limit: 1,
            }
        );

        return sessions.length > 0 ? sessions[0] : null;
    }

    /**
     * Update a learning session
     */
    async update(id: number, updates: Partial<LearningSession>): Promise<LearningSession | null> {
        const updatesWithTimestamp = {
            ...updates,
            updatedAt: new Date(),
        };

        return await this.dbManager.update<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            id,
            updatesWithTimestamp
        );
    }

    /**
     * Delete a learning session
     */
    async delete(id: number): Promise<boolean> {
        return await this.dbManager.delete(LearningSessionDAO.TABLE_NAME, id);
    }

    // =========================================================================
    // Session Management
    // =========================================================================

    /**
     * Start a new learning session
     */
    async startSession(sessionType: SessionType = 'learning'): Promise<LearningSession> {
        const sessionId = this.generateSessionId();

        return await this.create({
            sessionId,
            startTime: new Date(),
            totalDuration: 0,
            canvasCount: 0,
            conceptCount: 0,
            completedReviews: 0,
            sessionType,
        });
    }

    /**
     * End an active learning session
     */
    async endSession(sessionId: string): Promise<LearningSession | null> {
        const session = await this.getBySessionId(sessionId);

        if (!session || !session.id) {
            return null;
        }

        const endTime = new Date();
        const startTime = new Date(session.startTime);
        const totalDuration = Math.round((endTime.getTime() - startTime.getTime()) / 60000); // minutes

        return await this.update(session.id, {
            endTime,
            totalDuration,
        });
    }

    /**
     * Update session statistics
     */
    async updateSessionStats(
        sessionId: string,
        stats: {
            canvasCount?: number;
            conceptCount?: number;
            completedReviews?: number;
            averageScore?: number;
        }
    ): Promise<LearningSession | null> {
        const session = await this.getBySessionId(sessionId);

        if (!session || !session.id) {
            return null;
        }

        return await this.update(session.id, stats);
    }

    /**
     * Increment canvas count for a session
     */
    async incrementCanvasCount(sessionId: string): Promise<LearningSession | null> {
        const session = await this.getBySessionId(sessionId);

        if (!session || !session.id) {
            return null;
        }

        return await this.update(session.id, {
            canvasCount: session.canvasCount + 1,
        });
    }

    /**
     * Increment completed reviews for a session
     */
    async incrementCompletedReviews(sessionId: string): Promise<LearningSession | null> {
        const session = await this.getBySessionId(sessionId);

        if (!session || !session.id) {
            return null;
        }

        return await this.update(session.id, {
            completedReviews: session.completedReviews + 1,
        });
    }

    /**
     * Get active (not ended) sessions
     */
    async getActiveSessions(): Promise<LearningSession[]> {
        const allSessions = await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME
        );

        return allSessions.filter((session) => !session.endTime);
    }

    /**
     * Check if there's an active session
     */
    async hasActiveSession(): Promise<boolean> {
        const activeSessions = await this.getActiveSessions();
        return activeSessions.length > 0;
    }

    // =========================================================================
    // Query Operations
    // =========================================================================

    /**
     * Find sessions by type
     */
    async findByType(sessionType: SessionType): Promise<LearningSession[]> {
        return await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            {
                where: { sessionType },
                orderBy: 'startTime' as keyof LearningSession,
                orderDirection: 'DESC',
            }
        );
    }

    /**
     * Find sessions by date range
     */
    async findByDateRange(dateRange: DateRange): Promise<LearningSession[]> {
        const allSessions = await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME
        );

        return allSessions.filter((session) => {
            const startTime = new Date(session.startTime);
            return startTime >= dateRange.startDate && startTime <= dateRange.endDate;
        });
    }

    /**
     * Advanced query with multiple filters
     */
    async query(options: SessionQueryOptions): Promise<PaginatedResult<LearningSession>> {
        let sessions = await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME
        );

        // Apply filters
        if (options.sessionType) {
            sessions = sessions.filter((s) => s.sessionType === options.sessionType);
        }

        if (options.completedOnly) {
            sessions = sessions.filter((s) => s.endTime !== undefined);
        }

        if (options.dateRange) {
            sessions = sessions.filter((s) => {
                const startTime = new Date(s.startTime);
                return (
                    startTime >= options.dateRange!.startDate &&
                    startTime <= options.dateRange!.endDate
                );
            });
        }

        // Sort
        if (options.orderBy) {
            const direction = options.orderDirection === 'ASC' ? 1 : -1;
            sessions.sort((a, b) => {
                const aVal = a[options.orderBy!];
                const bVal = b[options.orderBy!];
                if (aVal === undefined) return 1;
                if (bVal === undefined) return -1;
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
        }

        const total = sessions.length;
        const offset = options.offset || 0;
        const limit = options.limit || 50;

        // Apply pagination
        sessions = sessions.slice(offset, offset + limit);

        return {
            data: sessions,
            total,
            limit,
            offset,
            hasMore: offset + sessions.length < total,
        };
    }

    /**
     * Get all learning sessions
     */
    async getAll(): Promise<LearningSession[]> {
        return await this.dbManager.findAll<LearningSession>(LearningSessionDAO.TABLE_NAME);
    }

    // =========================================================================
    // Statistics Operations
    // =========================================================================

    /**
     * Get total session count
     */
    async getTotalCount(): Promise<number> {
        const sessions = await this.getAll();
        return sessions.length;
    }

    /**
     * Get total learning time in minutes
     */
    async getTotalLearningTime(): Promise<number> {
        const sessions = await this.getAll();
        return sessions.reduce((acc, s) => acc + s.totalDuration, 0);
    }

    /**
     * Get average session duration in minutes
     */
    async getAverageSessionDuration(): Promise<number> {
        const sessions = await this.getAll();
        const completedSessions = sessions.filter((s) => s.endTime);

        if (completedSessions.length === 0) {
            return 0;
        }

        const totalDuration = completedSessions.reduce((acc, s) => acc + s.totalDuration, 0);
        return totalDuration / completedSessions.length;
    }

    /**
     * Get daily session statistics
     */
    async getDailyStats(date: Date): Promise<{
        sessionCount: number;
        totalDuration: number;
        totalReviews: number;
        averageScore: number | null;
    }> {
        const startOfDay = new Date(date);
        startOfDay.setHours(0, 0, 0, 0);

        const endOfDay = new Date(date);
        endOfDay.setHours(23, 59, 59, 999);

        const sessions = await this.findByDateRange({
            startDate: startOfDay,
            endDate: endOfDay,
        });

        const sessionCount = sessions.length;
        const totalDuration = sessions.reduce((acc, s) => acc + s.totalDuration, 0);
        const totalReviews = sessions.reduce((acc, s) => acc + s.completedReviews, 0);

        const sessionsWithScore = sessions.filter((s) => s.averageScore !== undefined);
        const averageScore =
            sessionsWithScore.length > 0
                ? sessionsWithScore.reduce((acc, s) => acc + (s.averageScore || 0), 0) /
                  sessionsWithScore.length
                : null;

        return {
            sessionCount,
            totalDuration,
            totalReviews,
            averageScore,
        };
    }

    /**
     * Get recent sessions
     */
    async getRecentSessions(limit: number = 10): Promise<LearningSession[]> {
        return await this.dbManager.findAll<LearningSession>(
            LearningSessionDAO.TABLE_NAME,
            {
                orderBy: 'startTime' as keyof LearningSession,
                orderDirection: 'DESC',
                limit,
            }
        );
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    /**
     * Generate a unique session ID
     */
    private generateSessionId(): string {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 10);
        return `session-${timestamp}-${random}`;
    }

    /**
     * Clean up orphaned sessions (no end time after 24 hours)
     */
    async cleanupOrphanedSessions(): Promise<number> {
        const activeSessions = await this.getActiveSessions();
        const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24 hours ago
        let cleanedCount = 0;

        for (const session of activeSessions) {
            if (new Date(session.startTime) < cutoff && session.id) {
                // Auto-end the orphaned session
                await this.update(session.id, {
                    endTime: new Date(session.startTime),
                    totalDuration: 0,
                    totalNotes: 'Session auto-closed due to timeout',
                });
                cleanedCount++;
            }
        }

        return cleanedCount;
    }
}
