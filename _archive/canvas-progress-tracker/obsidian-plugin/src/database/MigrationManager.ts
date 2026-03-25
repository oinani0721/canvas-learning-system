/**
 * Migration Manager - Canvas Learning System
 *
 * Manages database schema migrations and version control.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module MigrationManager
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - MigrationManager类
 */

import { App } from 'obsidian';
import { DatabaseManager } from './DatabaseManager';
import {
    Migration,
    MigrationRecord,
    MigrationConfig,
    DatabaseError,
} from '../types/DataTypes';

/**
 * Default migration configuration
 */
export const DEFAULT_MIGRATION_CONFIG: MigrationConfig = {
    migrationsDirectory: 'migrations',
    targetVersion: null,
};

/**
 * Migration Manager - Handles database version control
 *
 * Provides:
 * - Version tracking
 * - Forward migrations (up)
 * - Rollback migrations (down)
 * - Migration history
 *
 * ✅ Verified from Story 14.1 Dev Notes: MigrationManager类实现
 */
export class MigrationManager {
    private app: App;
    private dbManager: DatabaseManager;
    private config: MigrationConfig;
    private migrations: Migration[] = [];

    private static readonly MIGRATIONS_TABLE = '__migrations';

    constructor(
        app: App,
        dbManager: DatabaseManager,
        config: Partial<MigrationConfig> = {}
    ) {
        this.app = app;
        this.dbManager = dbManager;
        this.config = { ...DEFAULT_MIGRATION_CONFIG, ...config };
        this.registerBuiltInMigrations();
    }

    /**
     * Register built-in migrations
     */
    private registerBuiltInMigrations(): void {
        // Migration 1: Create core tables
        this.migrations.push({
            version: 1,
            description: 'Create core tables (review_records, learning_sessions)',
            up: async (db: DatabaseManager) => {
                // Create review_records table
                await db.createTable('review_records', [
                    'canvasId',
                    'reviewDate',
                    'status',
                ]);

                // Create learning_sessions table
                await db.createTable('learning_sessions', [
                    'sessionId',
                    'sessionType',
                    'startTime',
                ]);

                console.log('Migration 1: Created core tables');
            },
            down: async (db: DatabaseManager) => {
                await db.dropTable('review_records');
                await db.dropTable('learning_sessions');
                console.log('Migration 1: Dropped core tables');
            },
        });

        // Migration 2: Create statistics table
        this.migrations.push({
            version: 2,
            description: 'Create learning_statistics table',
            up: async (db: DatabaseManager) => {
                await db.createTable('learning_statistics', ['statDate']);
                console.log('Migration 2: Created learning_statistics table');
            },
            down: async (db: DatabaseManager) => {
                await db.dropTable('learning_statistics');
                console.log('Migration 2: Dropped learning_statistics table');
            },
        });

        // Migration 3: Create user_settings table
        this.migrations.push({
            version: 3,
            description: 'Create user_settings table',
            up: async (db: DatabaseManager) => {
                await db.createTable('user_settings', ['settingKey']);
                console.log('Migration 3: Created user_settings table');
            },
            down: async (db: DatabaseManager) => {
                await db.dropTable('user_settings');
                console.log('Migration 3: Dropped user_settings table');
            },
        });
    }

    /**
     * Register a custom migration
     */
    registerMigration(migration: Migration): void {
        // Ensure version is unique
        if (this.migrations.some((m) => m.version === migration.version)) {
            throw new DatabaseError(
                `Migration version ${migration.version} already exists`,
                'MIGRATION_ERROR'
            );
        }

        this.migrations.push(migration);
        // Sort by version
        this.migrations.sort((a, b) => a.version - b.version);
    }

    /**
     * Initialize migration tracking table
     */
    async initialize(): Promise<void> {
        try {
            await this.dbManager.createTable(MigrationManager.MIGRATIONS_TABLE, [
                'version',
            ]);
        } catch (error) {
            // Table may already exist, which is fine
            console.log('MigrationManager: Migrations table ready');
        }
    }

    /**
     * Run all pending migrations
     */
    async runMigrations(): Promise<number> {
        await this.initialize();

        const currentVersion = await this.getCurrentVersion();
        const targetVersion = this.config.targetVersion ?? this.getLatestVersion();

        console.log(
            `MigrationManager: Current version ${currentVersion}, target version ${targetVersion}`
        );

        if (currentVersion >= targetVersion) {
            console.log('MigrationManager: Already at target version');
            return 0;
        }

        let migrationsRun = 0;

        for (const migration of this.migrations) {
            if (
                migration.version > currentVersion &&
                migration.version <= targetVersion
            ) {
                console.log(
                    `MigrationManager: Running migration v${migration.version}: ${migration.description}`
                );

                try {
                    this.dbManager.beginTransaction();
                    await migration.up(this.dbManager);
                    await this.recordMigration(migration);
                    await this.dbManager.commitTransaction();
                    migrationsRun++;

                    console.log(
                        `MigrationManager: Completed migration v${migration.version}`
                    );
                } catch (error) {
                    await this.dbManager.rollbackTransaction();
                    throw new DatabaseError(
                        `Migration v${migration.version} failed: ${(error as Error).message}`,
                        'MIGRATION_ERROR',
                        error as Error
                    );
                }
            }
        }

        console.log(`MigrationManager: Completed ${migrationsRun} migrations`);
        return migrationsRun;
    }

    /**
     * Rollback to a specific version
     */
    async rollbackTo(targetVersion: number): Promise<number> {
        const currentVersion = await this.getCurrentVersion();

        if (currentVersion <= targetVersion) {
            console.log('MigrationManager: Already at or below target version');
            return 0;
        }

        let rollbacksRun = 0;

        // Run migrations in reverse order
        const migrationsToRollback = this.migrations
            .filter(
                (m) => m.version > targetVersion && m.version <= currentVersion
            )
            .reverse();

        for (const migration of migrationsToRollback) {
            console.log(
                `MigrationManager: Rolling back migration v${migration.version}: ${migration.description}`
            );

            try {
                this.dbManager.beginTransaction();
                await migration.down(this.dbManager);
                await this.removeMigration(migration.version);
                await this.dbManager.commitTransaction();
                rollbacksRun++;

                console.log(
                    `MigrationManager: Rolled back migration v${migration.version}`
                );
            } catch (error) {
                await this.dbManager.rollbackTransaction();
                throw new DatabaseError(
                    `Rollback v${migration.version} failed: ${(error as Error).message}`,
                    'MIGRATION_ERROR',
                    error as Error
                );
            }
        }

        console.log(`MigrationManager: Rolled back ${rollbacksRun} migrations`);
        return rollbacksRun;
    }

    /**
     * Get current database version
     */
    async getCurrentVersion(): Promise<number> {
        try {
            const records = await this.dbManager.findAll<MigrationRecord>(
                MigrationManager.MIGRATIONS_TABLE,
                {
                    orderBy: 'version' as keyof MigrationRecord,
                    orderDirection: 'DESC',
                    limit: 1,
                }
            );

            return records.length > 0 ? records[0].version : 0;
        } catch (error) {
            // Table may not exist yet
            return 0;
        }
    }

    /**
     * Get latest available migration version
     */
    getLatestVersion(): number {
        if (this.migrations.length === 0) {
            return 0;
        }
        return Math.max(...this.migrations.map((m) => m.version));
    }

    /**
     * Get migration history
     */
    async getHistory(): Promise<MigrationRecord[]> {
        try {
            return await this.dbManager.findAll<MigrationRecord>(
                MigrationManager.MIGRATIONS_TABLE,
                {
                    orderBy: 'version' as keyof MigrationRecord,
                    orderDirection: 'ASC',
                }
            );
        } catch (error) {
            return [];
        }
    }

    /**
     * Get pending migrations
     */
    async getPendingMigrations(): Promise<Migration[]> {
        const currentVersion = await this.getCurrentVersion();
        return this.migrations.filter((m) => m.version > currentVersion);
    }

    /**
     * Check if there are pending migrations
     */
    async hasPendingMigrations(): Promise<boolean> {
        const pending = await this.getPendingMigrations();
        return pending.length > 0;
    }

    /**
     * Validate migration sequence
     */
    validateMigrations(): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Check for version gaps
        const versions = this.migrations.map((m) => m.version).sort((a, b) => a - b);

        for (let i = 1; i < versions.length; i++) {
            if (versions[i] !== versions[i - 1] + 1) {
                errors.push(
                    `Gap in migration versions: ${versions[i - 1]} -> ${versions[i]}`
                );
            }
        }

        // Check that all migrations have up and down
        for (const migration of this.migrations) {
            if (typeof migration.up !== 'function') {
                errors.push(`Migration v${migration.version} missing 'up' function`);
            }
            if (typeof migration.down !== 'function') {
                errors.push(`Migration v${migration.version} missing 'down' function`);
            }
        }

        return {
            valid: errors.length === 0,
            errors,
        };
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    private async recordMigration(migration: Migration): Promise<void> {
        await this.dbManager.insert(
            MigrationManager.MIGRATIONS_TABLE,
            {
                version: migration.version,
                description: migration.description,
                appliedAt: new Date(),
            } as any
        );
    }

    private async removeMigration(version: number): Promise<void> {
        await this.dbManager.deleteWhere(MigrationManager.MIGRATIONS_TABLE, {
            version,
        });
    }
}
