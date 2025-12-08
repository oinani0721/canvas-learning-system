/**
 * Data Manager - Canvas Learning System
 *
 * Main orchestrator for all database operations.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module DataManager
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - DataManager类
 */

import { App } from 'obsidian';
import { DatabaseManager } from './DatabaseManager';
import { MigrationManager } from './MigrationManager';
import { BackupManager } from './BackupManager';
import { ReviewRecordDAO } from './ReviewRecordDAO';
import { LearningSessionDAO } from './LearningSessionDAO';
import {
    DataConfig,
    DatabaseConfig,
    BackupConfig,
    MigrationConfig,
    DEFAULT_DATABASE_CONFIG,
    DEFAULT_BACKUP_CONFIG,
    DEFAULT_MIGRATION_CONFIG,
    ReviewRecord,
    LearningSession,
    LearningStatistics,
    DateRange,
    DatabaseError,
    DatabaseEvent,
    DatabaseEventHandler,
} from '../types/DataTypes';

/**
 * Default data manager configuration
 */
export const DEFAULT_DATA_CONFIG: DataConfig = {
    database: DEFAULT_DATABASE_CONFIG,
    backup: DEFAULT_BACKUP_CONFIG,
    migration: DEFAULT_MIGRATION_CONFIG,
};

/**
 * Data Manager - Main orchestrator for database operations
 *
 * Provides:
 * - Unified access to all data operations
 * - Lifecycle management
 * - Event handling
 * - Statistics aggregation
 *
 * ✅ Verified from Story 14.1 Dev Notes: DataManager类实现
 */
export class DataManager {
    private app: App;
    private config: DataConfig;

    // Core managers
    private dbManager: DatabaseManager;
    private migrationManager: MigrationManager;
    private backupManager: BackupManager;

    // DAOs
    private reviewRecordDAO: ReviewRecordDAO;
    private learningSessionDAO: LearningSessionDAO;

    // State
    private initialized: boolean = false;
    private eventHandlers: Map<DatabaseEvent, DatabaseEventHandler[]> = new Map();

    constructor(app: App, config: Partial<DataConfig> = {}) {
        this.app = app;
        this.config = this.mergeConfig(config);

        // Initialize managers
        this.dbManager = new DatabaseManager(app, this.config.database);
        this.migrationManager = new MigrationManager(app, this.dbManager, this.config.migration);
        this.backupManager = new BackupManager(app, this.config.backup);

        // Initialize DAOs
        this.reviewRecordDAO = new ReviewRecordDAO(this.dbManager);
        this.learningSessionDAO = new LearningSessionDAO(this.dbManager);
    }

    // =========================================================================
    // Lifecycle Management
    // =========================================================================

    /**
     * Initialize all database components
     */
    async initialize(): Promise<void> {
        if (this.initialized) {
            console.log('DataManager: Already initialized');
            return;
        }

        try {
            console.log('DataManager: Initializing...');

            // Initialize database
            await this.dbManager.initialize();
            this.emit('connected');

            // Run migrations
            this.emit('migration-started');
            const migrationsRun = await this.migrationManager.runMigrations();
            console.log(`DataManager: Ran ${migrationsRun} migrations`);
            this.emit('migration-completed');

            // Initialize backup manager
            await this.backupManager.initialize();

            this.initialized = true;
            console.log('DataManager: Initialization complete');
        } catch (error) {
            this.emit('error', error);
            throw new DatabaseError(
                `DataManager initialization failed: ${(error as Error).message}`,
                'CONNECTION_ERROR',
                error as Error
            );
        }
    }

    /**
     * Shutdown all database components
     */
    async shutdown(): Promise<void> {
        if (!this.initialized) {
            return;
        }

        try {
            console.log('DataManager: Shutting down...');

            // Flush any pending changes
            await this.dbManager.flush();

            // Shutdown backup manager
            await this.backupManager.shutdown();

            // Close database
            await this.dbManager.close();

            this.initialized = false;
            this.emit('disconnected');

            console.log('DataManager: Shutdown complete');
        } catch (error) {
            console.error(`DataManager: Shutdown error - ${(error as Error).message}`);
        }
    }

    /**
     * Check if data manager is initialized
     */
    isInitialized(): boolean {
        return this.initialized;
    }

    /**
     * Get the underlying DatabaseManager instance
     * Used by services that need direct database access
     */
    getDatabaseManager(): DatabaseManager {
        return this.dbManager;
    }

    // =========================================================================
    // Review Records API
    // =========================================================================

    /**
     * Get review record DAO for direct access
     */
    getReviewRecordDAO(): ReviewRecordDAO {
        return this.reviewRecordDAO;
    }

    /**
     * Create a new review record
     */
    async createReviewRecord(record: Omit<ReviewRecord, 'id' | 'createdAt' | 'updatedAt'>): Promise<ReviewRecord> {
        return await this.reviewRecordDAO.create(record);
    }

    /**
     * Get review records for a canvas
     */
    async getReviewsByCanvas(canvasId: string): Promise<ReviewRecord[]> {
        return await this.reviewRecordDAO.findByCanvasId(canvasId);
    }

    /**
     * Get reviews due today
     */
    async getDueReviews(): Promise<ReviewRecord[]> {
        return await this.reviewRecordDAO.getDueForReview();
    }

    /**
     * Update review memory metrics
     */
    async updateReviewMetrics(
        id: number,
        memoryStrength: number,
        retentionRate: number,
        nextReviewDate?: Date
    ): Promise<ReviewRecord | null> {
        return await this.reviewRecordDAO.updateMemoryMetrics(
            id,
            memoryStrength,
            retentionRate,
            nextReviewDate
        );
    }

    // =========================================================================
    // Learning Sessions API
    // =========================================================================

    /**
     * Get learning session DAO for direct access
     */
    getLearningSessionDAO(): LearningSessionDAO {
        return this.learningSessionDAO;
    }

    /**
     * Start a new learning session
     */
    async startSession(sessionType: 'review' | 'learning' | 'mixed' = 'learning'): Promise<LearningSession> {
        return await this.learningSessionDAO.startSession(sessionType);
    }

    /**
     * End the current learning session
     */
    async endSession(sessionId: string): Promise<LearningSession | null> {
        return await this.learningSessionDAO.endSession(sessionId);
    }

    /**
     * Get active sessions
     */
    async getActiveSessions(): Promise<LearningSession[]> {
        return await this.learningSessionDAO.getActiveSessions();
    }

    /**
     * Get recent sessions
     */
    async getRecentSessions(limit: number = 10): Promise<LearningSession[]> {
        return await this.learningSessionDAO.getRecentSessions(limit);
    }

    // =========================================================================
    // Statistics API
    // =========================================================================

    /**
     * Get daily statistics
     */
    async getDailyStatistics(date: Date = new Date()): Promise<LearningStatistics> {
        const reviewStats = await this.reviewRecordDAO.getDailyStats(date);
        const sessionStats = await this.learningSessionDAO.getDailyStats(date);

        // Get all reviews for cumulative stats
        const allReviews = await this.reviewRecordDAO.getAll();
        const allSessions = await this.learningSessionDAO.getAll();

        // Calculate mastery metrics
        const canvasMetrics = this.calculateCanvasMetrics(allReviews);

        return {
            statDate: date,
            dailyReviews: reviewStats.totalReviews,
            dailyDuration: reviewStats.totalDuration,
            dailyAverageScore: reviewStats.averageScore ?? undefined,
            totalReviews: allReviews.length,
            totalDuration: allSessions.reduce((acc, s) => acc + s.totalDuration, 0),
            totalSessions: allSessions.length,
            masteredConcepts: canvasMetrics.mastered,
            learningConcepts: canvasMetrics.learning,
            strugglingConcepts: canvasMetrics.struggling,
            averageRetentionRate: this.calculateAverageRetention(allReviews),
            averageMemoryStrength: this.calculateAverageMemoryStrength(allReviews),
        };
    }

    /**
     * Get statistics for a date range
     */
    async getStatisticsRange(dateRange: DateRange): Promise<{
        reviews: number;
        duration: number;
        sessions: number;
        averageScore: number | null;
    }> {
        const reviews = await this.reviewRecordDAO.findByDateRange(dateRange);
        const sessions = await this.learningSessionDAO.findByDateRange(dateRange);

        const totalReviews = reviews.length;
        const totalDuration = reviews.reduce((acc, r) => acc + r.reviewDuration, 0);
        const totalSessions = sessions.length;

        const reviewsWithScore = reviews.filter((r) => r.reviewScore !== undefined);
        const averageScore =
            reviewsWithScore.length > 0
                ? reviewsWithScore.reduce((acc, r) => acc + (r.reviewScore || 0), 0) /
                  reviewsWithScore.length
                : null;

        return {
            reviews: totalReviews,
            duration: totalDuration,
            sessions: totalSessions,
            averageScore,
        };
    }

    // =========================================================================
    // Backup API
    // =========================================================================

    /**
     * Get backup manager for direct access
     */
    getBackupManager(): BackupManager {
        return this.backupManager;
    }

    /**
     * Create a backup
     */
    async createBackup(description?: string): Promise<{ success: boolean; path?: string; error?: string }> {
        this.emit('backup-started');
        const result = await this.backupManager.createBackup(description);
        this.emit('backup-completed', result);
        return result;
    }

    /**
     * Restore from backup
     */
    async restoreFromBackup(backupPath: string): Promise<{ success: boolean; error?: string }> {
        const result = await this.backupManager.restoreFromBackup(backupPath);

        if (result.success) {
            // Reinitialize database after restore
            await this.dbManager.initialize();
        }

        return result;
    }

    /**
     * List available backups
     */
    async listBackups(): Promise<Array<{ path: string; name: string; createdAt: Date }>> {
        return await this.backupManager.listBackups();
    }

    // =========================================================================
    // Migration API
    // =========================================================================

    /**
     * Get current database version
     */
    async getDatabaseVersion(): Promise<number> {
        return await this.migrationManager.getCurrentVersion();
    }

    /**
     * Check for pending migrations
     */
    async hasPendingMigrations(): Promise<boolean> {
        return await this.migrationManager.hasPendingMigrations();
    }

    // =========================================================================
    // Event Handling
    // =========================================================================

    /**
     * Subscribe to database events
     */
    on(event: DatabaseEvent, handler: DatabaseEventHandler): void {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event)!.push(handler);
    }

    /**
     * Unsubscribe from database events
     */
    off(event: DatabaseEvent, handler: DatabaseEventHandler): void {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Emit a database event
     */
    private emit(event: DatabaseEvent, data?: any): void {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            for (const handler of handlers) {
                try {
                    handler(event, data);
                } catch (error) {
                    console.error(`DataManager: Event handler error - ${(error as Error).message}`);
                }
            }
        }
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    /**
     * Force flush all pending changes
     */
    async flush(): Promise<void> {
        await this.dbManager.flush();
    }

    /**
     * Get database health status
     */
    async getHealthStatus(): Promise<{
        initialized: boolean;
        databaseVersion: number;
        hasPendingMigrations: boolean;
        lastBackup: Date | null;
        autoBackupEnabled: boolean;
        reviewCount: number;
        sessionCount: number;
    }> {
        const reviews = await this.reviewRecordDAO.getAll();
        const sessions = await this.learningSessionDAO.getAll();

        return {
            initialized: this.initialized,
            databaseVersion: await this.migrationManager.getCurrentVersion(),
            hasPendingMigrations: await this.migrationManager.hasPendingMigrations(),
            lastBackup: this.backupManager.getLastBackupTime(),
            autoBackupEnabled: this.backupManager.isAutoBackupRunning(),
            reviewCount: reviews.length,
            sessionCount: sessions.length,
        };
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    /**
     * Merge user config with defaults
     */
    private mergeConfig(config: Partial<DataConfig>): DataConfig {
        return {
            database: { ...DEFAULT_DATABASE_CONFIG, ...config.database },
            backup: { ...DEFAULT_BACKUP_CONFIG, ...config.backup },
            migration: { ...DEFAULT_MIGRATION_CONFIG, ...config.migration },
        };
    }

    /**
     * Calculate canvas mastery metrics
     */
    private calculateCanvasMetrics(reviews: ReviewRecord[]): {
        mastered: number;
        learning: number;
        struggling: number;
    } {
        // Group by canvas
        const canvasMap = new Map<string, ReviewRecord[]>();

        for (const review of reviews) {
            const key = review.canvasId;
            if (!canvasMap.has(key)) {
                canvasMap.set(key, []);
            }
            canvasMap.get(key)!.push(review);
        }

        let mastered = 0;
        let learning = 0;
        let struggling = 0;

        for (const [, canvasReviews] of canvasMap) {
            // Get latest review for this canvas
            const sortedReviews = canvasReviews.sort(
                (a, b) => new Date(b.reviewDate).getTime() - new Date(a.reviewDate).getTime()
            );
            const latestReview = sortedReviews[0];

            if (latestReview.memoryStrength >= 0.8) {
                mastered++;
            } else if (latestReview.memoryStrength >= 0.5) {
                learning++;
            } else {
                struggling++;
            }
        }

        return { mastered, learning, struggling };
    }

    /**
     * Calculate average retention rate
     */
    private calculateAverageRetention(reviews: ReviewRecord[]): number {
        if (reviews.length === 0) {
            return 0;
        }

        const sum = reviews.reduce((acc, r) => acc + r.retentionRate, 0);
        return sum / reviews.length;
    }

    /**
     * Calculate average memory strength
     */
    private calculateAverageMemoryStrength(reviews: ReviewRecord[]): number {
        if (reviews.length === 0) {
            return 0;
        }

        const sum = reviews.reduce((acc, r) => acc + r.memoryStrength, 0);
        return sum / reviews.length;
    }
}

/**
 * Export default configuration
 */
export { DEFAULT_MIGRATION_CONFIG } from './MigrationManager';
