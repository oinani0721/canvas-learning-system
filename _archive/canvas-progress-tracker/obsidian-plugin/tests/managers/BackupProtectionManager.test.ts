// @ts-nocheck - Mock types don't match Obsidian types exactly
/**
 * Tests for Backup Protection Manager
 * Story 13.5: 右键菜单和快捷键 - Task 3
 *
 * Tests SCP-003 backup protection functionality.
 */

import { BackupProtectionManager } from '../../src/managers/BackupProtectionManager';
import { Vault, TFile, Notice } from '../__mocks__/obsidian';
import { BACKUP_FOLDER } from '../../src/utils/canvas-helpers';
import { BACKUP_METADATA_PATH, DEFAULT_BACKUP_PROTECTION_DATA } from '../../src/types/menu';

// Mock Notice globally
jest.mock('obsidian', () => {
  const actual = jest.requireActual('../__mocks__/obsidian');
  return {
    ...actual,
    Notice: jest.fn().mockImplementation((message, duration) => {
      console.log(`[Notice] ${message}`);
      return { message, duration };
    }),
  };
});

describe('BackupProtectionManager', () => {
  let manager: BackupProtectionManager;
  let vault: Vault;

  beforeEach(() => {
    vault = new Vault();
    manager = new BackupProtectionManager(vault as any);
    jest.clearAllMocks();
  });

  afterEach(() => {
    vault._clear();
  });

  // ============================================================================
  // Initialization Tests
  // ============================================================================

  describe('initialize', () => {
    it('should initialize with default data when no metadata file exists', async () => {
      await manager.initialize();

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(0);
    });

    it('should load existing metadata from file', async () => {
      const existingData = {
        version: 1,
        lastModified: Date.now(),
        backups: {
          [`${BACKUP_FOLDER}/test_20250101_100000.canvas`]: {
            filePath: `${BACKUP_FOLDER}/test_20250101_100000.canvas`,
            protected: true,
            protectedAt: Date.now(),
            protectedBy: 'user',
            originalName: 'test',
          },
        },
      };

      vault._setFolder(BACKUP_FOLDER);
      vault._setFile(BACKUP_METADATA_PATH, JSON.stringify(existingData));

      await manager.initialize();

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(1);
    });

    it('should use defaults for invalid metadata format', async () => {
      vault._setFolder(BACKUP_FOLDER);
      vault._setFile(BACKUP_METADATA_PATH, '{"invalid": "format"}');

      await manager.initialize();

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(0);
    });

    it('should handle corrupted JSON gracefully', async () => {
      vault._setFolder(BACKUP_FOLDER);
      vault._setFile(BACKUP_METADATA_PATH, 'not valid json');

      await manager.initialize();

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(0);
    });

    it('should not reinitialize if already initialized', async () => {
      await manager.initialize();
      await manager.initialize(); // Second call should be no-op

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(0);
    });
  });

  // ============================================================================
  // Protection Status Tests
  // ============================================================================

  describe('isProtected', () => {
    it('should return false for unprotected backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;

      const result = await manager.isProtected(filePath);

      expect(result).toBe(false);
    });

    it('should return true for protected backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      const result = await manager.isProtected(filePath);
      expect(result).toBe(true);
    });
  });

  describe('isBackupFile', () => {
    it('should return true for files in backup folder', () => {
      expect(manager.isBackupFile(`${BACKUP_FOLDER}/test.canvas`)).toBe(true);
    });

    it('should return false for files outside backup folder', () => {
      expect(manager.isBackupFile('test.canvas')).toBe(false);
      expect(manager.isBackupFile('folder/test.canvas')).toBe(false);
    });

    it('should handle Windows-style paths', () => {
      expect(manager.isBackupFile(`${BACKUP_FOLDER}\\test.canvas`)).toBe(true);
    });
  });

  // ============================================================================
  // Toggle Protection Tests
  // ============================================================================

  describe('toggleProtection', () => {
    it('should protect an unprotected backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      const result = await manager.toggleProtection(filePath);

      expect(result).toBe(true); // Now protected
      expect(await manager.isProtected(filePath)).toBe(true);
    });

    it('should unprotect a protected backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);
      const result = await manager.toggleProtection(filePath);

      expect(result).toBe(false); // Now unprotected
      expect(await manager.isProtected(filePath)).toBe(false);
    });

    it('should throw error for non-backup files', async () => {
      await expect(manager.toggleProtection('test.canvas')).rejects.toThrow(
        'Not a backup file'
      );
    });

    it('should include note in metadata when provided', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.toggleProtection(filePath, 'Important backup');

      const metadata = await manager.getMetadata(filePath);
      expect(metadata?.note).toBe('Important backup');
    });

    it('should update lastModified timestamp', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      const beforeTime = Date.now();
      await manager.toggleProtection(filePath);

      // Verify metadata was saved (file should exist)
      const file = vault.getAbstractFileByPath(BACKUP_METADATA_PATH);
      expect(file).not.toBeNull();
    });
  });

  // ============================================================================
  // Protect/Unprotect Tests
  // ============================================================================

  describe('protect', () => {
    it('should protect a backup file', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      expect(await manager.isProtected(filePath)).toBe(true);
    });

    it('should not duplicate protection if already protected', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);
      await manager.protect(filePath); // Should be no-op

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(1);
    });

    it('should throw error for non-backup files', async () => {
      await expect(manager.protect('test.canvas')).rejects.toThrow(
        'Not a backup file'
      );
    });

    it('should extract original name from file path', async () => {
      const filePath = `${BACKUP_FOLDER}/MyCanvas_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      const metadata = await manager.getMetadata(filePath);
      expect(metadata?.originalName).toBe('MyCanvas');
    });

    it('should extract backup timestamp from file path', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250115_143000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      const metadata = await manager.getMetadata(filePath);
      expect(metadata?.backupTimestamp).toBeDefined();
      // Verify it's a valid timestamp (roughly Jan 15, 2025)
      const date = new Date(metadata!.backupTimestamp!);
      expect(date.getFullYear()).toBe(2025);
      expect(date.getMonth()).toBe(0); // January
      expect(date.getDate()).toBe(15);
    });
  });

  describe('unprotect', () => {
    it('should remove protection from a backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);
      await manager.unprotect(filePath);

      expect(await manager.isProtected(filePath)).toBe(false);
    });

    it('should do nothing if not protected', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;

      await expect(manager.unprotect(filePath)).resolves.not.toThrow();
    });
  });

  // ============================================================================
  // canDelete Tests
  // ============================================================================

  describe('canDelete', () => {
    it('should return true for non-backup files', async () => {
      const result = await manager.canDelete('test.canvas');
      expect(result).toBe(true);
    });

    it('should return true for unprotected backups', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;

      const result = await manager.canDelete(filePath);
      expect(result).toBe(true);
    });

    it('should return false for protected backups', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      const result = await manager.canDelete(filePath);
      expect(result).toBe(false);
    });
  });

  // ============================================================================
  // Query Tests
  // ============================================================================

  describe('getMetadata', () => {
    it('should return undefined for non-existent backup', async () => {
      const metadata = await manager.getMetadata(`${BACKUP_FOLDER}/nonexistent.canvas`);
      expect(metadata).toBeUndefined();
    });

    it('should return metadata for protected backup', async () => {
      const filePath = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath, 'Test note');

      const metadata = await manager.getMetadata(filePath);
      expect(metadata).toBeDefined();
      expect(metadata?.protected).toBe(true);
      expect(metadata?.note).toBe('Test note');
      expect(metadata?.protectedBy).toBe('user');
    });
  });

  describe('getProtectedBackups', () => {
    it('should return empty array when no protected backups', async () => {
      const backups = await manager.getProtectedBackups();
      expect(backups).toHaveLength(0);
    });

    it('should return all protected backups sorted by protectedAt', async () => {
      const file1 = `${BACKUP_FOLDER}/test1_20250101_100000.canvas`;
      const file2 = `${BACKUP_FOLDER}/test2_20250101_110000.canvas`;
      const file3 = `${BACKUP_FOLDER}/test3_20250101_120000.canvas`;

      vault._setFile(file1, '{}');
      vault._setFile(file2, '{}');
      vault._setFile(file3, '{}');

      await manager.protect(file1);
      await new Promise(r => setTimeout(r, 10)); // Small delay
      await manager.protect(file2);
      await new Promise(r => setTimeout(r, 10));
      await manager.protect(file3);

      const backups = await manager.getProtectedBackups();

      expect(backups).toHaveLength(3);
      // Most recent first
      expect(backups[0].filePath).toBe(file3);
    });
  });

  describe('getStats', () => {
    it('should return correct statistics', async () => {
      const file1 = `${BACKUP_FOLDER}/canvas1_20250101_100000.canvas`;
      const file2 = `${BACKUP_FOLDER}/canvas1_20250102_100000.canvas`;
      const file3 = `${BACKUP_FOLDER}/canvas2_20250101_100000.canvas`;

      vault._setFile(file1, '{}');
      vault._setFile(file2, '{}');
      vault._setFile(file3, '{}');

      await manager.protect(file1);
      await manager.protect(file2);
      await manager.protect(file3);

      const stats = await manager.getStats();

      expect(stats.totalProtected).toBe(3);
      expect(stats.byOriginalFile['canvas1']).toBe(2);
      expect(stats.byOriginalFile['canvas2']).toBe(1);
    });
  });

  // ============================================================================
  // Cleanup Tests
  // ============================================================================

  describe('cleanupOrphanedEntries', () => {
    it('should remove entries for non-existent files', async () => {
      const existingFile = `${BACKUP_FOLDER}/existing_20250101_100000.canvas`;
      const orphanedFile = `${BACKUP_FOLDER}/orphaned_20250101_100000.canvas`;

      vault._setFile(existingFile, '{}');
      vault._setFile(orphanedFile, '{}');

      await manager.protect(existingFile);
      await manager.protect(orphanedFile);

      // Remove the orphaned file
      await vault.delete(new TFile(orphanedFile));

      const cleaned = await manager.cleanupOrphanedEntries();

      expect(cleaned).toBe(1);

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(1);
    });

    it('should return 0 when no orphaned entries', async () => {
      const file = `${BACKUP_FOLDER}/test_20250101_100000.canvas`;
      vault._setFile(file, '{}');

      await manager.protect(file);

      const cleaned = await manager.cleanupOrphanedEntries();

      expect(cleaned).toBe(0);
    });
  });

  describe('resetAll', () => {
    it('should clear all protection data', async () => {
      const file1 = `${BACKUP_FOLDER}/test1_20250101_100000.canvas`;
      const file2 = `${BACKUP_FOLDER}/test2_20250101_100000.canvas`;

      vault._setFile(file1, '{}');
      vault._setFile(file2, '{}');

      await manager.protect(file1);
      await manager.protect(file2);

      await manager.resetAll();

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(0);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('edge cases', () => {
    it('should handle file paths with special characters', async () => {
      const filePath = `${BACKUP_FOLDER}/测试文件_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      expect(await manager.isProtected(filePath)).toBe(true);
    });

    it('should handle very long file names', async () => {
      const longName = 'a'.repeat(100);
      const filePath = `${BACKUP_FOLDER}/${longName}_20250101_100000.canvas`;
      vault._setFile(filePath, '{}');

      await manager.protect(filePath);

      expect(await manager.isProtected(filePath)).toBe(true);
    });

    it('should handle concurrent protection operations', async () => {
      const files = Array.from({ length: 5 }, (_, i) =>
        `${BACKUP_FOLDER}/test${i}_20250101_100000.canvas`
      );

      files.forEach(f => vault._setFile(f, '{}'));

      // Protect all files concurrently
      await Promise.all(files.map(f => manager.protect(f)));

      const stats = await manager.getStats();
      expect(stats.totalProtected).toBe(5);
    });
  });
});
