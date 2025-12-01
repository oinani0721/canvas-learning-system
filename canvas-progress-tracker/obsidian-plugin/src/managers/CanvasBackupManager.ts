/**
 * Canvas Backup Manager
 * Story 13.2: Canvas API集成 - Task 4
 *
 * Manages Canvas file backups in a hidden `.canvas_backups/` folder.
 *
 * Story 13.2: AC 4, 5 (SCP-003 compliance)
 */

import { TFile, TFolder, Vault, Notice } from 'obsidian';
import { BackupInfo } from '../types/canvas';
import {
  BACKUP_FOLDER,
  formatBackupName,
  parseBackupTimestamp,
  extractOriginalName,
  isValidCanvasFile,
} from '../utils/canvas-helpers';

/**
 * Backup configuration options
 */
export interface BackupConfig {
  /** Maximum backups to keep per canvas file */
  maxBackups: number;
  /** Auto-backup before modifications */
  autoBackup: boolean;
}

/**
 * Default backup configuration
 */
const DEFAULT_BACKUP_CONFIG: BackupConfig = {
  maxBackups: 10,
  autoBackup: true,
};

/**
 * Canvas Backup Manager
 * Manages backup creation, restoration, and cleanup for Canvas files.
 *
 * Story 13.2: AC 4 - Backup management
 * Story 13.2: AC 5 - Hidden folder (SCP-003)
 */
export class CanvasBackupManager {
  private vault: Vault;
  private config: BackupConfig;

  constructor(vault: Vault, config?: Partial<BackupConfig>) {
    this.vault = vault;
    this.config = { ...DEFAULT_BACKUP_CONFIG, ...config };
  }

  // ============================================================================
  // Backup Creation
  // ============================================================================

  /**
   * Create a backup of a Canvas file
   * Story 13.2: AC 4 - Backup creation
   *
   * @param canvasFile - Canvas file to backup
   * @returns Backup file path
   */
  async createBackup(canvasFile: TFile): Promise<string> {
    if (!isValidCanvasFile(canvasFile)) {
      throw new Error(`Not a valid canvas file: ${canvasFile.path}`);
    }

    try {
      // Ensure backup folder exists and is hidden
      await this.ensureBackupFolder();

      // Generate backup file name
      const timestamp = new Date();
      const backupName = formatBackupName(canvasFile.basename, timestamp);
      const backupPath = `${BACKUP_FOLDER}/${backupName}`;

      // Read original file content
      const content = await this.vault.read(canvasFile);

      // Create backup file
      await this.vault.create(backupPath, content);

      console.log(`Canvas备份已创建: ${backupPath}`);

      // Auto-cleanup old backups
      await this.cleanupOldBackups(canvasFile, this.config.maxBackups);

      return backupPath;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to create backup for ${canvasFile.path}:`, error);
      new Notice(`备份创建失败: ${message}`);
      throw error;
    }
  }

  /**
   * Create backup if auto-backup is enabled
   *
   * @param canvasFile - Canvas file to backup
   * @returns Backup path or null if skipped
   */
  async createAutoBackup(canvasFile: TFile): Promise<string | null> {
    if (!this.config.autoBackup) {
      return null;
    }
    return this.createBackup(canvasFile);
  }

  // ============================================================================
  // Backup Listing
  // ============================================================================

  /**
   * List all backups for a Canvas file
   * Story 13.2: AC 4 - List backups
   *
   * @param canvasFile - Original canvas file
   * @returns Array of backup info, sorted by timestamp (newest first)
   */
  async listBackups(canvasFile: TFile): Promise<BackupInfo[]> {
    const backupFolder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);
    if (!backupFolder || !(backupFolder instanceof TFolder)) {
      return [];
    }

    const baseName = canvasFile.basename;
    const backups: BackupInfo[] = [];

    for (const file of backupFolder.children) {
      if (!(file instanceof TFile)) {
        continue;
      }

      // Check if backup belongs to this canvas file
      const originalName = extractOriginalName(file.name);
      if (originalName !== baseName) {
        continue;
      }

      const timestamp = parseBackupTimestamp(file.name);
      if (!timestamp) {
        continue;
      }

      backups.push({
        path: file.path,
        originalName: baseName,
        timestamp,
        size: file.stat.size,
      });
    }

    // Sort by timestamp (newest first)
    return backups.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * List all backups in the backup folder
   *
   * @returns All backup infos grouped by original file
   */
  async listAllBackups(): Promise<Map<string, BackupInfo[]>> {
    const backupFolder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);
    if (!backupFolder || !(backupFolder instanceof TFolder)) {
      return new Map();
    }

    const backupsByFile = new Map<string, BackupInfo[]>();

    for (const file of backupFolder.children) {
      if (!(file instanceof TFile) || !file.path.endsWith('.canvas')) {
        continue;
      }

      const originalName = extractOriginalName(file.name);
      if (!originalName) {
        continue;
      }

      const timestamp = parseBackupTimestamp(file.name);
      if (!timestamp) {
        continue;
      }

      const backup: BackupInfo = {
        path: file.path,
        originalName,
        timestamp,
        size: file.stat.size,
      };

      if (!backupsByFile.has(originalName)) {
        backupsByFile.set(originalName, []);
      }
      backupsByFile.get(originalName)!.push(backup);
    }

    // Sort each file's backups by timestamp
    for (const [, backups] of backupsByFile) {
      backups.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    }

    return backupsByFile;
  }

  // ============================================================================
  // Backup Restoration
  // ============================================================================

  /**
   * Restore a Canvas file from backup
   * Story 13.2: AC 4 - Restore backup
   *
   * @param backupPath - Path to backup file
   * @param canvasFile - Target canvas file to restore to
   */
  async restoreBackup(backupPath: string, canvasFile: TFile): Promise<void> {
    const backupFile = this.vault.getAbstractFileByPath(backupPath);
    if (!backupFile || !(backupFile instanceof TFile)) {
      throw new Error(`Backup not found: ${backupPath}`);
    }

    try {
      // Create a backup of current state before restoring
      if (this.config.autoBackup) {
        await this.createBackup(canvasFile);
      }

      // Read backup content
      const content = await this.vault.read(backupFile);

      // Validate backup content
      try {
        const data = JSON.parse(content);
        if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
          throw new Error('Invalid canvas structure in backup');
        }
      } catch (parseError) {
        throw new Error('Backup file is corrupted');
      }

      // Write to original file
      await this.vault.modify(canvasFile, content);

      console.log(`Canvas已恢复自备份: ${backupPath}`);
      new Notice('Canvas已从备份恢复');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to restore backup ${backupPath}:`, error);
      new Notice(`备份恢复失败: ${message}`);
      throw error;
    }
  }

  /**
   * Get the most recent backup for a canvas file
   *
   * @param canvasFile - Canvas file
   * @returns Most recent backup info or null
   */
  async getLatestBackup(canvasFile: TFile): Promise<BackupInfo | null> {
    const backups = await this.listBackups(canvasFile);
    return backups.length > 0 ? backups[0] : null;
  }

  // ============================================================================
  // Backup Deletion
  // ============================================================================

  /**
   * Delete a specific backup
   * Story 13.2: AC 4 - Delete backup
   *
   * @param backupPath - Path to backup file
   */
  async deleteBackup(backupPath: string): Promise<void> {
    const backupFile = this.vault.getAbstractFileByPath(backupPath);
    if (!backupFile || !(backupFile instanceof TFile)) {
      console.warn(`Backup not found: ${backupPath}`);
      return;
    }

    try {
      await this.vault.delete(backupFile);
      console.log(`备份已删除: ${backupPath}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to delete backup ${backupPath}:`, error);
      throw new Error(`备份删除失败: ${message}`);
    }
  }

  /**
   * Delete all backups for a canvas file
   *
   * @param canvasFile - Canvas file
   * @returns Number of backups deleted
   */
  async deleteAllBackups(canvasFile: TFile): Promise<number> {
    const backups = await this.listBackups(canvasFile);
    let deletedCount = 0;

    for (const backup of backups) {
      try {
        await this.deleteBackup(backup.path);
        deletedCount++;
      } catch {
        // Continue deleting other backups
      }
    }

    return deletedCount;
  }

  // ============================================================================
  // Cleanup
  // ============================================================================

  /**
   * Clean up old backups, keeping only the most recent N backups
   * Story 13.2: AC 4 - Auto-cleanup mechanism
   *
   * @param canvasFile - Canvas file
   * @param keepCount - Number of backups to keep
   * @returns Number of backups deleted
   */
  async cleanupOldBackups(canvasFile: TFile, keepCount: number = 10): Promise<number> {
    const backups = await this.listBackups(canvasFile);

    if (backups.length <= keepCount) {
      return 0;
    }

    const toDelete = backups.slice(keepCount);
    let deletedCount = 0;

    for (const backup of toDelete) {
      try {
        await this.deleteBackup(backup.path);
        deletedCount++;
      } catch {
        // Continue cleaning up
      }
    }

    if (deletedCount > 0) {
      console.log(`已清理${deletedCount}个旧备份`);
    }

    return deletedCount;
  }

  /**
   * Clean up all old backups for all canvas files
   *
   * @param keepCount - Number of backups to keep per file
   * @returns Total number of backups deleted
   */
  async cleanupAllOldBackups(keepCount: number = 10): Promise<number> {
    const backupsByFile = await this.listAllBackups();
    let totalDeleted = 0;

    for (const [, backups] of backupsByFile) {
      if (backups.length <= keepCount) {
        continue;
      }

      const toDelete = backups.slice(keepCount);
      for (const backup of toDelete) {
        try {
          await this.deleteBackup(backup.path);
          totalDeleted++;
        } catch {
          // Continue cleaning up
        }
      }
    }

    return totalDeleted;
  }

  // ============================================================================
  // Backup Folder Management
  // ============================================================================

  /**
   * Ensure backup folder exists and is properly configured
   * Story 13.2: AC 5 - Hidden folder configuration
   *
   * Creates `.canvas_backups/` with `.obsidian-ignore` marker
   */
  private async ensureBackupFolder(): Promise<void> {
    let folder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);

    if (!folder) {
      // Create backup folder
      await this.vault.createFolder(BACKUP_FOLDER);

      // Create .obsidian-ignore marker file to hide folder in file tree
      // Story 13.2: AC 5 - SCP-003 compliance
      const ignorePath = `${BACKUP_FOLDER}/.obsidian-ignore`;
      try {
        await this.vault.create(ignorePath, '');
      } catch {
        // Ignore if already exists
      }

      console.log(`备份文件夹已创建并配置为隐藏: ${BACKUP_FOLDER}`);
    }
  }

  /**
   * Check if backup folder exists
   *
   * @returns True if backup folder exists
   */
  backupFolderExists(): boolean {
    const folder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);
    return folder instanceof TFolder;
  }

  /**
   * Get total size of all backups in bytes
   *
   * @returns Total backup size
   */
  async getTotalBackupSize(): Promise<number> {
    const backupFolder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);
    if (!backupFolder || !(backupFolder instanceof TFolder)) {
      return 0;
    }

    let totalSize = 0;
    for (const file of backupFolder.children) {
      if (file instanceof TFile) {
        totalSize += file.stat.size;
      }
    }

    return totalSize;
  }

  // ============================================================================
  // Configuration
  // ============================================================================

  /**
   * Update backup configuration
   *
   * @param config - Partial config to update
   */
  updateConfig(config: Partial<BackupConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current backup configuration
   *
   * @returns Current config
   */
  getConfig(): BackupConfig {
    return { ...this.config };
  }
}
