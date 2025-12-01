/**
 * Backup Protection Manager
 * Story 13.5: 右键菜单和快捷键 - Task 3
 *
 * Manages backup file protection to prevent accidental deletion.
 * Implements SCP-003 backup protection feature.
 *
 * ✅ Verified from @obsidian-canvas Skill (Vault API - File Operations)
 * ✅ Verified from Story 13.5 Dev Notes - BackupProtectionManager
 */

import { TFile, Vault, Notice } from 'obsidian';
import type {
  BackupMetadata,
  BackupProtectionData,
} from '../types/menu';
import {
  BACKUP_METADATA_PATH,
  DEFAULT_BACKUP_PROTECTION_DATA,
} from '../types/menu';
import { BACKUP_FOLDER } from '../utils/canvas-helpers';

// ============================================================================
// Backup Protection Manager
// ============================================================================

/**
 * Manages backup file protection
 *
 * Story 13.5: AC 3 - SCP-003 backup protection
 *
 * Features:
 * - Toggle protection status for backup files
 * - Persist protection metadata to JSON file
 * - Prevent deletion of protected backups
 * - Display protection status in UI
 */
export class BackupProtectionManager {
  private vault: Vault;
  private protectionData: BackupProtectionData;
  private initialized: boolean = false;

  constructor(vault: Vault) {
    this.vault = vault;
    this.protectionData = { ...DEFAULT_BACKUP_PROTECTION_DATA };
  }

  // ============================================================================
  // Initialization
  // ============================================================================

  /**
   * Initialize the protection manager
   * Loads existing protection data from metadata file
   *
   * ✅ Verified from @obsidian-canvas Skill (Vault API - vault.read)
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      await this.loadMetadata();
      this.initialized = true;
      console.log('BackupProtectionManager: Initialized successfully');
    } catch (error) {
      console.error('BackupProtectionManager: Initialization failed', error);
      // Continue with default data
      this.initialized = true;
    }
  }

  /**
   * Load protection metadata from file
   */
  private async loadMetadata(): Promise<void> {
    try {
      const file = this.vault.getAbstractFileByPath(BACKUP_METADATA_PATH);

      if (file instanceof TFile) {
        const content = await this.vault.read(file);
        const data = JSON.parse(content) as BackupProtectionData;

        // Validate and migrate if needed
        if (this.isValidProtectionData(data)) {
          this.protectionData = data;
        } else {
          console.warn('BackupProtectionManager: Invalid metadata format, using defaults');
          this.protectionData = { ...DEFAULT_BACKUP_PROTECTION_DATA };
        }
      } else {
        // File doesn't exist, use defaults
        this.protectionData = { ...DEFAULT_BACKUP_PROTECTION_DATA };
      }
    } catch (error) {
      console.log('BackupProtectionManager: No existing metadata, creating new');
      this.protectionData = { ...DEFAULT_BACKUP_PROTECTION_DATA };
    }
  }

  /**
   * Validate protection data structure
   */
  private isValidProtectionData(data: unknown): data is BackupProtectionData {
    if (!data || typeof data !== 'object') return false;

    const d = data as Record<string, unknown>;
    return (
      typeof d.version === 'number' &&
      typeof d.lastModified === 'number' &&
      typeof d.backups === 'object' &&
      d.backups !== null
    );
  }

  // ============================================================================
  // Protection Operations
  // ============================================================================

  /**
   * Check if a backup file is protected
   *
   * @param filePath - Path to the backup file
   * @returns True if protected, false otherwise
   */
  async isProtected(filePath: string): Promise<boolean> {
    await this.ensureInitialized();

    const metadata = this.protectionData.backups[filePath];
    return metadata?.protected === true;
  }

  /**
   * Toggle protection status for a backup file
   *
   * @param filePath - Path to the backup file
   * @param note - Optional note about why protection was added/removed
   * @returns New protection status
   */
  async toggleProtection(filePath: string, note?: string): Promise<boolean> {
    await this.ensureInitialized();

    // Validate this is actually a backup file
    if (!this.isBackupFile(filePath)) {
      throw new Error(`Not a backup file: ${filePath}`);
    }

    const currentMetadata = this.protectionData.backups[filePath];
    const wasProtected = currentMetadata?.protected === true;

    if (wasProtected) {
      // Remove protection
      delete this.protectionData.backups[filePath];
      new Notice(`备份已取消保护: ${this.getDisplayName(filePath)} 🔓`);
    } else {
      // Add protection
      this.protectionData.backups[filePath] = {
        filePath,
        protected: true,
        protectedAt: Date.now(),
        protectedBy: 'user',
        note: note || undefined,
        originalName: this.extractOriginalName(filePath),
        backupTimestamp: this.extractBackupTimestamp(filePath),
      };
      new Notice(`备份已保护: ${this.getDisplayName(filePath)} 🔒`);
    }

    // Update last modified
    this.protectionData.lastModified = Date.now();

    // Save changes
    await this.saveMetadata();

    return !wasProtected;
  }

  /**
   * Protect a backup file
   *
   * @param filePath - Path to the backup file
   * @param note - Optional protection note
   */
  async protect(filePath: string, note?: string): Promise<void> {
    await this.ensureInitialized();

    if (!this.isBackupFile(filePath)) {
      throw new Error(`Not a backup file: ${filePath}`);
    }

    if (await this.isProtected(filePath)) {
      return; // Already protected
    }

    this.protectionData.backups[filePath] = {
      filePath,
      protected: true,
      protectedAt: Date.now(),
      protectedBy: 'user',
      note: note || undefined,
      originalName: this.extractOriginalName(filePath),
      backupTimestamp: this.extractBackupTimestamp(filePath),
    };

    this.protectionData.lastModified = Date.now();
    await this.saveMetadata();

    new Notice(`备份已保护: ${this.getDisplayName(filePath)} 🔒`);
  }

  /**
   * Remove protection from a backup file
   *
   * @param filePath - Path to the backup file
   */
  async unprotect(filePath: string): Promise<void> {
    await this.ensureInitialized();

    if (!(await this.isProtected(filePath))) {
      return; // Not protected
    }

    delete this.protectionData.backups[filePath];
    this.protectionData.lastModified = Date.now();
    await this.saveMetadata();

    new Notice(`备份已取消保护: ${this.getDisplayName(filePath)} 🔓`);
  }

  /**
   * Check if a file can be deleted (not protected)
   *
   * @param filePath - Path to check
   * @returns True if can be deleted, false if protected
   */
  async canDelete(filePath: string): Promise<boolean> {
    if (!this.isBackupFile(filePath)) {
      return true; // Not a backup file, allow deletion
    }

    if (await this.isProtected(filePath)) {
      new Notice('⚠️ 此备份已受保护，无法删除。请先取消保护。', 5000);
      return false;
    }

    return true;
  }

  // ============================================================================
  // Metadata Queries
  // ============================================================================

  /**
   * Get metadata for a specific backup
   *
   * @param filePath - Path to the backup file
   * @returns Backup metadata or undefined
   */
  async getMetadata(filePath: string): Promise<BackupMetadata | undefined> {
    await this.ensureInitialized();
    return this.protectionData.backups[filePath];
  }

  /**
   * Get all protected backups
   *
   * @returns Array of protected backup metadata
   */
  async getProtectedBackups(): Promise<BackupMetadata[]> {
    await this.ensureInitialized();

    return Object.values(this.protectionData.backups)
      .filter(b => b.protected)
      .sort((a, b) => (b.protectedAt || 0) - (a.protectedAt || 0));
  }

  /**
   * Get protection statistics
   *
   * @returns Statistics about protected backups
   */
  async getStats(): Promise<{
    totalProtected: number;
    byOriginalFile: Record<string, number>;
  }> {
    await this.ensureInitialized();

    const protectedBackups = Object.values(this.protectionData.backups)
      .filter(b => b.protected);

    const byOriginalFile: Record<string, number> = {};
    for (const backup of protectedBackups) {
      const name = backup.originalName || 'unknown';
      byOriginalFile[name] = (byOriginalFile[name] || 0) + 1;
    }

    return {
      totalProtected: protectedBackups.length,
      byOriginalFile,
    };
  }

  // ============================================================================
  // Persistence
  // ============================================================================

  /**
   * Save protection metadata to file
   *
   * ✅ Verified from @obsidian-canvas Skill (Vault API - vault.modify, vault.create)
   */
  private async saveMetadata(): Promise<void> {
    try {
      // Ensure backup folder exists
      await this.ensureBackupFolder();

      const content = JSON.stringify(this.protectionData, null, 2);
      const file = this.vault.getAbstractFileByPath(BACKUP_METADATA_PATH);

      if (file instanceof TFile) {
        await this.vault.modify(file, content);
      } else {
        await this.vault.create(BACKUP_METADATA_PATH, content);
      }
    } catch (error) {
      console.error('BackupProtectionManager: Failed to save metadata', error);
      throw new Error('保存保护元数据失败');
    }
  }

  /**
   * Ensure backup folder exists
   */
  private async ensureBackupFolder(): Promise<void> {
    const folder = this.vault.getAbstractFileByPath(BACKUP_FOLDER);
    if (!folder) {
      await this.vault.createFolder(BACKUP_FOLDER);
    }
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Check if a path is in the backup folder
   */
  isBackupFile(filePath: string): boolean {
    return filePath.startsWith(BACKUP_FOLDER + '/') ||
           filePath.startsWith(BACKUP_FOLDER + '\\');
  }

  /**
   * Extract original canvas name from backup file path
   */
  private extractOriginalName(filePath: string): string {
    const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || '';
    // Format: originalName_YYYYMMDD_HHmmss.canvas
    const match = fileName.match(/^(.+?)_\d{8}_\d{6}\.canvas$/);
    return match ? match[1] : fileName.replace('.canvas', '');
  }

  /**
   * Extract backup timestamp from file name
   */
  private extractBackupTimestamp(filePath: string): number | undefined {
    const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || '';
    // Format: originalName_YYYYMMDD_HHmmss.canvas
    const match = fileName.match(/_(\d{8})_(\d{6})\.canvas$/);

    if (match) {
      const dateStr = match[1];
      const timeStr = match[2];

      const year = parseInt(dateStr.substring(0, 4));
      const month = parseInt(dateStr.substring(4, 6)) - 1;
      const day = parseInt(dateStr.substring(6, 8));
      const hour = parseInt(timeStr.substring(0, 2));
      const minute = parseInt(timeStr.substring(2, 4));
      const second = parseInt(timeStr.substring(4, 6));

      return new Date(year, month, day, hour, minute, second).getTime();
    }

    return undefined;
  }

  /**
   * Get display name for a backup file
   */
  private getDisplayName(filePath: string): string {
    const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || '';
    // Truncate if too long
    if (fileName.length > 40) {
      return fileName.substring(0, 37) + '...';
    }
    return fileName;
  }

  /**
   * Ensure manager is initialized
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }
  }

  // ============================================================================
  // Cleanup
  // ============================================================================

  /**
   * Clean up orphaned protection entries (backup files that no longer exist)
   *
   * @returns Number of entries cleaned up
   */
  async cleanupOrphanedEntries(): Promise<number> {
    await this.ensureInitialized();

    let cleanedCount = 0;
    const pathsToRemove: string[] = [];

    for (const filePath of Object.keys(this.protectionData.backups)) {
      const file = this.vault.getAbstractFileByPath(filePath);
      if (!file) {
        pathsToRemove.push(filePath);
      }
    }

    for (const path of pathsToRemove) {
      delete this.protectionData.backups[path];
      cleanedCount++;
    }

    if (cleanedCount > 0) {
      this.protectionData.lastModified = Date.now();
      await this.saveMetadata();
      console.log(`BackupProtectionManager: Cleaned ${cleanedCount} orphaned entries`);
    }

    return cleanedCount;
  }

  /**
   * Reset all protection data
   * Use with caution!
   */
  async resetAll(): Promise<void> {
    this.protectionData = { ...DEFAULT_BACKUP_PROTECTION_DATA };
    await this.saveMetadata();
    new Notice('所有备份保护已重置');
  }
}
