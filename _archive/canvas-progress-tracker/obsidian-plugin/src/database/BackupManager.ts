/**
 * Backup Manager - Canvas Learning System
 *
 * Manages database backup and restore operations.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module BackupManager
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - BackupManager类
 */

import { App, TFile, TFolder, normalizePath } from 'obsidian';
import {
    BackupConfig,
    BackupFile,
    BackupResult,
    DEFAULT_BACKUP_CONFIG,
    BackupError,
} from '../types/DataTypes';

/**
 * Backup Manager - Handles database backup and restore
 *
 * Provides:
 * - Manual backups
 * - Automatic scheduled backups
 * - Backup retention management
 * - Restore from backup
 *
 * ✅ Verified from Story 14.1 Dev Notes: BackupManager类实现
 */
export class BackupManager {
    private app: App;
    private config: BackupConfig;
    private autoBackupInterval: ReturnType<typeof setInterval> | null = null;
    private lastBackupTime: Date | null = null;

    constructor(app: App, config: Partial<BackupConfig> = {}) {
        this.app = app;
        this.config = { ...DEFAULT_BACKUP_CONFIG, ...config };
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    /**
     * Initialize backup manager
     */
    async initialize(): Promise<void> {
        // Ensure backup directory exists
        await this.ensureBackupDirectory();

        // Start auto-backup if enabled
        if (this.config.autoBackup) {
            this.startAutoBackup();
        }

        console.log('BackupManager: Initialized');
    }

    /**
     * Shutdown backup manager
     */
    async shutdown(): Promise<void> {
        this.stopAutoBackup();
        console.log('BackupManager: Shutdown');
    }

    // =========================================================================
    // Backup Operations
    // =========================================================================

    /**
     * Create a backup of the database
     */
    async createBackup(description?: string): Promise<BackupResult> {
        try {
            const timestamp = this.formatTimestamp(new Date());
            const backupName = `backup-${timestamp}.json`;
            const backupPath = normalizePath(`${this.config.backupDirectory}/${backupName}`);

            // Read current database file
            const dbPath = normalizePath(this.config.databasePath);
            let dbContent: string;

            try {
                dbContent = await this.app.vault.adapter.read(dbPath);
            } catch (error) {
                // Database file doesn't exist yet - nothing to backup
                return {
                    success: false,
                    error: 'Database file not found',
                    timestamp: new Date(),
                };
            }

            // Create backup metadata
            const backupData = {
                version: '1.0.0',
                timestamp: new Date().toISOString(),
                description: description || 'Manual backup',
                source: this.config.databasePath,
                data: JSON.parse(dbContent),
            };

            // Write backup file
            await this.app.vault.adapter.write(
                backupPath,
                JSON.stringify(backupData, null, 2)
            );

            this.lastBackupTime = new Date();

            console.log(`BackupManager: Created backup ${backupName}`);

            // Clean up old backups
            await this.cleanupOldBackups();

            return {
                success: true,
                path: backupPath,
                timestamp: new Date(),
            };
        } catch (error) {
            const errorMessage = (error as Error).message;
            console.error(`BackupManager: Backup failed - ${errorMessage}`);

            return {
                success: false,
                error: errorMessage,
                timestamp: new Date(),
            };
        }
    }

    /**
     * Restore from a backup file
     */
    async restoreFromBackup(backupPath: string): Promise<BackupResult> {
        try {
            // Read backup file
            const backupContent = await this.app.vault.adapter.read(backupPath);
            const backupData = JSON.parse(backupContent);

            // Validate backup format
            if (!backupData.version || !backupData.data) {
                throw new BackupError('Invalid backup format', 'RESTORE_ERROR');
            }

            // Create pre-restore backup
            await this.createBackup('Pre-restore backup');

            // Restore database
            const dbPath = normalizePath(this.config.databasePath);
            await this.app.vault.adapter.write(
                dbPath,
                JSON.stringify(backupData.data, null, 2)
            );

            console.log(`BackupManager: Restored from ${backupPath}`);

            return {
                success: true,
                path: dbPath,
                timestamp: new Date(),
            };
        } catch (error) {
            const errorMessage = (error as Error).message;
            console.error(`BackupManager: Restore failed - ${errorMessage}`);

            return {
                success: false,
                error: errorMessage,
                timestamp: new Date(),
            };
        }
    }

    /**
     * Restore from the latest backup
     */
    async restoreLatest(): Promise<BackupResult> {
        const backups = await this.listBackups();

        if (backups.length === 0) {
            return {
                success: false,
                error: 'No backups found',
                timestamp: new Date(),
            };
        }

        // Sort by creation date descending
        backups.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

        return await this.restoreFromBackup(backups[0].path);
    }

    // =========================================================================
    // Backup Management
    // =========================================================================

    /**
     * List all available backups
     */
    async listBackups(): Promise<BackupFile[]> {
        const backups: BackupFile[] = [];
        const backupDir = normalizePath(this.config.backupDirectory);

        try {
            const files = await this.app.vault.adapter.list(backupDir);

            for (const filePath of files.files) {
                if (filePath.endsWith('.json')) {
                    try {
                        const stat = await this.app.vault.adapter.stat(filePath);

                        if (stat) {
                            backups.push({
                                path: filePath,
                                name: filePath.split('/').pop() || filePath,
                                size: stat.size,
                                createdAt: new Date(stat.ctime),
                                compressed: false,
                            });
                        }
                    } catch (error) {
                        // Skip files that can't be read
                        console.warn(`BackupManager: Could not read ${filePath}`);
                    }
                }
            }
        } catch (error) {
            // Backup directory might not exist yet
            console.log('BackupManager: No backups directory found');
        }

        return backups;
    }

    /**
     * Delete a specific backup
     */
    async deleteBackup(backupPath: string): Promise<boolean> {
        try {
            await this.app.vault.adapter.remove(backupPath);
            console.log(`BackupManager: Deleted backup ${backupPath}`);
            return true;
        } catch (error) {
            console.error(`BackupManager: Failed to delete ${backupPath}`);
            return false;
        }
    }

    /**
     * Get backup information
     */
    async getBackupInfo(backupPath: string): Promise<{
        version: string;
        timestamp: string;
        description: string;
        recordCount: number;
    } | null> {
        try {
            const content = await this.app.vault.adapter.read(backupPath);
            const data = JSON.parse(content);

            return {
                version: data.version || 'unknown',
                timestamp: data.timestamp || 'unknown',
                description: data.description || 'No description',
                recordCount: this.countRecords(data.data),
            };
        } catch (error) {
            return null;
        }
    }

    /**
     * Get the last backup time
     */
    getLastBackupTime(): Date | null {
        return this.lastBackupTime;
    }

    // =========================================================================
    // Auto-Backup
    // =========================================================================

    /**
     * Start automatic backups
     */
    startAutoBackup(): void {
        if (this.autoBackupInterval) {
            return; // Already running
        }

        const intervalMs = this.config.backupIntervalHours * 60 * 60 * 1000;

        this.autoBackupInterval = setInterval(async () => {
            console.log('BackupManager: Running automatic backup');
            await this.createBackup('Automatic backup');
        }, intervalMs);

        console.log(
            `BackupManager: Auto-backup started (every ${this.config.backupIntervalHours} hours)`
        );
    }

    /**
     * Stop automatic backups
     */
    stopAutoBackup(): void {
        if (this.autoBackupInterval) {
            clearInterval(this.autoBackupInterval);
            this.autoBackupInterval = null;
            console.log('BackupManager: Auto-backup stopped');
        }
    }

    /**
     * Check if auto-backup is running
     */
    isAutoBackupRunning(): boolean {
        return this.autoBackupInterval !== null;
    }

    // =========================================================================
    // Retention Management
    // =========================================================================

    /**
     * Clean up old backups based on retention policy
     */
    async cleanupOldBackups(): Promise<number> {
        const backups = await this.listBackups();
        const retentionMs = this.config.retentionDays * 24 * 60 * 60 * 1000;
        const cutoffDate = new Date(Date.now() - retentionMs);

        let deletedCount = 0;

        for (const backup of backups) {
            if (backup.createdAt < cutoffDate) {
                const deleted = await this.deleteBackup(backup.path);
                if (deleted) {
                    deletedCount++;
                }
            }
        }

        if (deletedCount > 0) {
            console.log(`BackupManager: Cleaned up ${deletedCount} old backups`);
        }

        return deletedCount;
    }

    // =========================================================================
    // Configuration
    // =========================================================================

    /**
     * Update backup configuration
     */
    updateConfig(config: Partial<BackupConfig>): void {
        this.config = { ...this.config, ...config };

        // Restart auto-backup if running and interval changed
        if (this.autoBackupInterval && config.backupIntervalHours) {
            this.stopAutoBackup();
            this.startAutoBackup();
        }

        // Start/stop auto-backup based on config
        if (config.autoBackup !== undefined) {
            if (config.autoBackup && !this.autoBackupInterval) {
                this.startAutoBackup();
            } else if (!config.autoBackup && this.autoBackupInterval) {
                this.stopAutoBackup();
            }
        }
    }

    /**
     * Get current configuration
     */
    getConfig(): BackupConfig {
        return { ...this.config };
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    /**
     * Ensure backup directory exists
     */
    private async ensureBackupDirectory(): Promise<void> {
        const backupDir = normalizePath(this.config.backupDirectory);

        try {
            const exists = await this.app.vault.adapter.exists(backupDir);

            if (!exists) {
                await this.app.vault.adapter.mkdir(backupDir);
                console.log(`BackupManager: Created backup directory ${backupDir}`);
            }
        } catch (error) {
            console.error(`BackupManager: Failed to create backup directory`);
        }
    }

    /**
     * Format timestamp for backup filename
     */
    private formatTimestamp(date: Date): string {
        return date.toISOString().replace(/[:.]/g, '-').slice(0, 19);
    }

    /**
     * Count records in backup data
     */
    private countRecords(data: any): number {
        if (!data || typeof data !== 'object') {
            return 0;
        }

        let count = 0;

        for (const tableName of Object.keys(data)) {
            if (Array.isArray(data[tableName])) {
                count += data[tableName].length;
            }
        }

        return count;
    }
}
