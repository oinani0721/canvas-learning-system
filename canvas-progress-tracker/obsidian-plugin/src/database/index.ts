/**
 * Database Module - Canvas Learning System
 *
 * Main exports for the database module.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module Database
 * @version 1.0.0
 */

// Core Managers
export { DatabaseManager, DEFAULT_DATABASE_CONFIG } from './DatabaseManager';
export { MigrationManager, DEFAULT_MIGRATION_CONFIG } from './MigrationManager';
export { BackupManager } from './BackupManager';
export { DataManager, DEFAULT_DATA_CONFIG } from './DataManager';

// DAOs
export { ReviewRecordDAO } from './ReviewRecordDAO';
export { LearningSessionDAO } from './LearningSessionDAO';

// Re-export types
export type {
    DatabaseConfig,
    BackupConfig,
    MigrationConfig,
    DataConfig,
    ReviewRecord,
    ReviewRecordQueryOptions,
    LearningSession,
    SessionQueryOptions,
    LearningStatistics,
    StatisticsQueryOptions,
    UserSetting,
    Migration,
    MigrationRecord,
    BackupFile,
    BackupResult,
    DateRange,
    PaginatedResult,
    PaginationOptions,
    DifficultyLevel,
    ReviewStatus,
    SessionType,
    SettingType,
    DatabaseErrorCode,
    DatabaseEvent,
    DatabaseEventHandler,
} from '../types/DataTypes';

export { DatabaseError, BackupError } from '../types/DataTypes';
