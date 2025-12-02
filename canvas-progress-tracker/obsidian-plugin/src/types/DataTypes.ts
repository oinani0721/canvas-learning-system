/**
 * Data Types - Canvas Learning System Database
 *
 * Type definitions for SQLite database entities.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module DataTypes
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - 数据模型定义
 */

// ============================================================================
// Database Configuration Types
// ============================================================================

/**
 * Database configuration options
 * Source: Story 14.1 Dev Notes - DatabaseManager类
 */
export interface DatabaseConfig {
    /** Database file path */
    path: string;
    /** Maximum connections (for future connection pool) */
    maxConnections: number;
    /** Connection timeout in milliseconds */
    connectionTimeout: number;
    /** Busy timeout in milliseconds */
    busyTimeout: number;
    /** Enable foreign key constraints */
    enableForeignKeys: boolean;
    /** Enable WAL mode for better concurrency */
    enableWAL: boolean;
}

/**
 * Default database configuration
 */
export const DEFAULT_DATABASE_CONFIG: DatabaseConfig = {
    path: 'canvas-review.db',
    maxConnections: 5,
    connectionTimeout: 30000,
    busyTimeout: 5000,
    enableForeignKeys: true,
    enableWAL: true,
};

/**
 * Backup configuration options
 * Source: Story 14.1 Dev Notes - BackupManager类
 */
export interface BackupConfig {
    /** Database path */
    databasePath: string;
    /** Backup directory */
    backupDirectory: string;
    /** Enable automatic backups */
    autoBackup: boolean;
    /** Backup interval in hours */
    backupIntervalHours: number;
    /** Retention period in days */
    retentionDays: number;
    /** Compress backup files */
    compressBackups: boolean;
}

/**
 * Default backup configuration
 */
export const DEFAULT_BACKUP_CONFIG: BackupConfig = {
    databasePath: 'canvas-review.db',
    backupDirectory: 'backups',
    autoBackup: true,
    backupIntervalHours: 24,
    retentionDays: 7,
    compressBackups: false,
};

/**
 * Combined data manager configuration
 */
export interface DataConfig {
    database: DatabaseConfig;
    backup: BackupConfig;
    migration: MigrationConfig;
}

/**
 * Migration configuration
 */
export interface MigrationConfig {
    /** Directory for migration scripts */
    migrationsDirectory: string;
    /** Target version (null = latest) */
    targetVersion: number | null;
}

// ============================================================================
// Review Record Types
// ============================================================================

/**
 * Review record difficulty levels
 */
export type DifficultyLevel = 'easy' | 'medium' | 'hard';

/**
 * Review record status
 */
export type ReviewStatus = 'completed' | 'skipped' | 'postponed';

/**
 * Review record entity
 * Source: Story 14.1 Dev Notes - ReviewRecord接口
 */
export interface ReviewRecord {
    /** Auto-increment ID */
    id?: number;
    /** Canvas file identifier */
    canvasId: string;
    /** Canvas file title */
    canvasTitle: string;
    /** Name of the concept reviewed */
    conceptName: string;

    // Review information
    /** When the review occurred */
    reviewDate: Date;
    /** Duration in minutes */
    reviewDuration: number;
    /** Score (0-100) */
    reviewScore?: number;
    /** Notes from the review */
    reviewNotes?: string;

    // Memory metrics
    /** Memory strength (0-1) */
    memoryStrength: number;
    /** Retention rate (0-1) */
    retentionRate: number;
    /** Difficulty level */
    difficultyLevel: DifficultyLevel;

    // Status information
    /** Review status */
    status: ReviewStatus;
    /** Next scheduled review date */
    nextReviewDate?: Date;

    // Metadata
    /** Record creation time */
    createdAt?: Date;
    /** Last update time */
    updatedAt?: Date;
}

/**
 * Options for querying review records
 */
export interface ReviewRecordQueryOptions {
    /** Filter by canvas ID */
    canvasId?: string;
    /** Filter by date range */
    dateRange?: DateRange;
    /** Filter by status */
    status?: ReviewStatus;
    /** Filter by difficulty */
    difficultyLevel?: DifficultyLevel;
    /** Maximum records to return */
    limit?: number;
    /** Records to skip (pagination) */
    offset?: number;
    /** Sort field */
    orderBy?: 'reviewDate' | 'reviewScore' | 'memoryStrength' | 'createdAt';
    /** Sort direction */
    orderDirection?: 'ASC' | 'DESC';
}

// ============================================================================
// Learning Session Types
// ============================================================================

/**
 * Learning session type
 */
export type SessionType = 'review' | 'learning' | 'mixed';

/**
 * Learning session entity
 * Source: Story 14.1 Dev Notes - LearningSession接口
 */
export interface LearningSession {
    /** Auto-increment ID */
    id?: number;
    /** Unique session identifier */
    sessionId: string;

    // Session information
    /** Session start time */
    startTime: Date;
    /** Session end time */
    endTime?: Date;
    /** Total duration in minutes */
    totalDuration: number;

    // Session content
    /** Number of canvases accessed */
    canvasCount: number;
    /** Number of concepts covered */
    conceptCount: number;
    /** Number of reviews completed */
    completedReviews: number;

    // Session statistics
    /** Average score achieved */
    averageScore?: number;
    /** Combined notes */
    totalNotes?: string;
    /** Session type */
    sessionType: SessionType;

    // Metadata
    /** Record creation time */
    createdAt?: Date;
    /** Last update time */
    updatedAt?: Date;
}

/**
 * Options for querying learning sessions
 */
export interface SessionQueryOptions {
    /** Filter by session type */
    sessionType?: SessionType;
    /** Filter by date range */
    dateRange?: DateRange;
    /** Only include completed sessions */
    completedOnly?: boolean;
    /** Maximum sessions to return */
    limit?: number;
    /** Sessions to skip (pagination) */
    offset?: number;
    /** Sort field */
    orderBy?: 'startTime' | 'totalDuration' | 'completedReviews';
    /** Sort direction */
    orderDirection?: 'ASC' | 'DESC';
}

// ============================================================================
// Statistics Types
// ============================================================================

/**
 * Learning statistics entity
 */
export interface LearningStatistics {
    /** Auto-increment ID */
    id?: number;
    /** Statistics date */
    statDate: Date;

    // Daily statistics
    /** Reviews completed today */
    dailyReviews: number;
    /** Total duration in minutes */
    dailyDuration: number;
    /** Average score for the day */
    dailyAverageScore?: number;

    // Cumulative statistics
    /** Total reviews all time */
    totalReviews: number;
    /** Total duration all time */
    totalDuration: number;
    /** Total sessions all time */
    totalSessions: number;

    // Mastery statistics
    /** Concepts fully mastered */
    masteredConcepts: number;
    /** Concepts in progress */
    learningConcepts: number;
    /** Concepts needing attention */
    strugglingConcepts: number;

    // Memory metrics
    /** Average retention rate */
    averageRetentionRate: number;
    /** Average memory strength */
    averageMemoryStrength: number;

    // Metadata
    /** Record creation time */
    createdAt?: Date;
    /** Last update time */
    updatedAt?: Date;
}

/**
 * Statistics query options
 */
export interface StatisticsQueryOptions {
    /** Date range for statistics */
    dateRange?: DateRange;
    /** Group by period */
    groupBy?: 'day' | 'week' | 'month';
}

// ============================================================================
// User Settings Types
// ============================================================================

/**
 * User setting value types
 */
export type SettingType = 'string' | 'number' | 'boolean' | 'json';

/**
 * User setting entity
 */
export interface UserSetting {
    /** Auto-increment ID */
    id?: number;
    /** Setting key */
    settingKey: string;
    /** Setting value (stored as string) */
    settingValue: string;
    /** Value type for parsing */
    settingType: SettingType;
    /** Setting description */
    description?: string;

    // Metadata
    /** Record creation time */
    createdAt?: Date;
    /** Last update time */
    updatedAt?: Date;
}

// ============================================================================
// Common Types
// ============================================================================

/**
 * Date range for filtering
 */
export interface DateRange {
    startDate: Date;
    endDate: Date;
}

/**
 * Pagination options
 */
export interface PaginationOptions {
    limit: number;
    offset: number;
}

/**
 * Paginated result
 */
export interface PaginatedResult<T> {
    data: T[];
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
}

// ============================================================================
// Migration Types
// ============================================================================

/**
 * Database migration definition
 */
export interface Migration {
    /** Migration version number */
    version: number;
    /** Migration description */
    description: string;
    /** Apply migration */
    up: (db: any) => Promise<void>;
    /** Rollback migration */
    down: (db: any) => Promise<void>;
}

/**
 * Migration history record
 */
export interface MigrationRecord {
    version: number;
    appliedAt: Date;
    description: string;
}

// ============================================================================
// Backup Types
// ============================================================================

/**
 * Backup file information
 */
export interface BackupFile {
    /** File path */
    path: string;
    /** File name */
    name: string;
    /** File size in bytes */
    size: number;
    /** Creation timestamp */
    createdAt: Date;
    /** Whether compressed */
    compressed: boolean;
}

/**
 * Backup result
 */
export interface BackupResult {
    success: boolean;
    path?: string;
    error?: string;
    timestamp: Date;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Database error codes
 */
export type DatabaseErrorCode =
    | 'CONNECTION_ERROR'
    | 'QUERY_ERROR'
    | 'TRANSACTION_ERROR'
    | 'MIGRATION_ERROR'
    | 'BACKUP_ERROR'
    | 'RESTORE_ERROR'
    | 'VALIDATION_ERROR'
    | 'NOT_FOUND'
    | 'DUPLICATE_KEY'
    | 'UNKNOWN';

/**
 * Custom database error
 */
export class DatabaseError extends Error {
    public readonly code: DatabaseErrorCode;
    public readonly originalError?: Error;

    constructor(
        message: string,
        code: DatabaseErrorCode = 'UNKNOWN',
        originalError?: Error
    ) {
        super(message);
        this.name = 'DatabaseError';
        this.code = code;
        this.originalError = originalError;
        Object.setPrototypeOf(this, DatabaseError.prototype);
    }
}

/**
 * Custom backup error
 */
export class BackupError extends Error {
    public readonly code: DatabaseErrorCode;
    public readonly originalError?: Error;

    constructor(
        message: string,
        code: DatabaseErrorCode = 'BACKUP_ERROR',
        originalError?: Error
    ) {
        super(message);
        this.name = 'BackupError';
        this.code = code;
        this.originalError = originalError;
        Object.setPrototypeOf(this, BackupError.prototype);
    }
}

// ============================================================================
// Event Types
// ============================================================================

/**
 * Database events
 */
export type DatabaseEvent =
    | 'connected'
    | 'disconnected'
    | 'error'
    | 'migration-started'
    | 'migration-completed'
    | 'backup-started'
    | 'backup-completed';

/**
 * Event handler type
 */
export type DatabaseEventHandler = (event: DatabaseEvent, data?: any) => void;
