// @ts-nocheck - Mock types don't match Obsidian types exactly
/**
 * Tests for Canvas Backup Manager
 * Story 13.2: Canvas API集成 - Task 4
 */

import { CanvasBackupManager } from '../../src/managers/CanvasBackupManager';
import { Vault, TFile, TFolder } from '../__mocks__/obsidian';
import { BACKUP_FOLDER } from '../../src/utils/canvas-helpers';

// Extended mock vault for backup testing
class MockVaultWithFolderChildren extends Vault {
  private folderChildren: Map<string, (TFile | TFolder)[]> = new Map();

  setFolderChildren(folderPath: string, children: (TFile | TFolder)[]): void {
    this.folderChildren.set(folderPath, children);
    this._setFolder(folderPath);
  }

  getAbstractFileByPath(path: string): TFile | TFolder | null {
    const result = super.getAbstractFileByPath(path);
    if (result instanceof TFolder) {
      const folder = new TFolder(path);
      folder.children = this.folderChildren.get(path) || [];
      return folder;
    }
    return result;
  }
}

describe('CanvasBackupManager', () => {
  let backupManager: CanvasBackupManager;
  let vault: MockVaultWithFolderChildren;

  beforeEach(() => {
    vault = new MockVaultWithFolderChildren();
    backupManager = new CanvasBackupManager(vault as Vault);
  });

  afterEach(() => {
    vault._clear();
  });

  describe('createBackup', () => {
    it('should create backup with correct naming format', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{"nodes":[],"edges":[]}');

      const backupPath = await backupManager.createBackup(file);

      expect(backupPath).toMatch(/^\.canvas_backups\/test-\d{8}-\d{6}\.canvas$/);
    });

    it('should throw for non-canvas files', async () => {
      const file = new TFile('test.md');

      await expect(backupManager.createBackup(file)).rejects.toThrow(
        'Not a valid canvas file'
      );
    });
  });

  describe('createAutoBackup', () => {
    it('should create backup when autoBackup is enabled', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{"nodes":[],"edges":[]}');

      const backupPath = await backupManager.createAutoBackup(file);

      expect(backupPath).not.toBeNull();
    });

    it('should return null when autoBackup is disabled', async () => {
      backupManager.updateConfig({ autoBackup: false });
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}');

      const result = await backupManager.createAutoBackup(file);

      expect(result).toBeNull();
    });
  });

  describe('listBackups', () => {
    it('should return empty array when no backups exist', async () => {
      const file = new TFile('test.canvas');
      const backups = await backupManager.listBackups(file);
      expect(backups).toHaveLength(0);
    });

    it('should list backups sorted by timestamp (newest first)', async () => {
      const file = new TFile('test.canvas');

      // Create mock backup files
      const backup1 = new TFile(`${BACKUP_FOLDER}/test-20250101-100000.canvas`);
      backup1.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };

      const backup2 = new TFile(`${BACKUP_FOLDER}/test-20250115-120000.canvas`);
      backup2.stat = { mtime: Date.now(), ctime: Date.now(), size: 2048 };

      vault.setFolderChildren(BACKUP_FOLDER, [backup1, backup2]);

      const backups = await backupManager.listBackups(file);

      expect(backups).toHaveLength(2);
      expect(backups[0].timestamp.getTime()).toBeGreaterThan(backups[1].timestamp.getTime());
    });

    it('should only list backups for the specified canvas file', async () => {
      const file = new TFile('test.canvas');

      const backup1 = new TFile(`${BACKUP_FOLDER}/test-20250101-100000.canvas`);
      backup1.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };

      const backup2 = new TFile(`${BACKUP_FOLDER}/other-20250101-100000.canvas`);
      backup2.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };

      vault.setFolderChildren(BACKUP_FOLDER, [backup1, backup2]);

      const backups = await backupManager.listBackups(file);

      expect(backups).toHaveLength(1);
      expect(backups[0].originalName).toBe('test');
    });
  });

  describe('getLatestBackup', () => {
    it('should return null when no backups exist', async () => {
      const file = new TFile('test.canvas');
      const latest = await backupManager.getLatestBackup(file);
      expect(latest).toBeNull();
    });

    it('should return most recent backup', async () => {
      const file = new TFile('test.canvas');

      const backup1 = new TFile(`${BACKUP_FOLDER}/test-20250101-100000.canvas`);
      backup1.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };

      const backup2 = new TFile(`${BACKUP_FOLDER}/test-20250115-120000.canvas`);
      backup2.stat = { mtime: Date.now(), ctime: Date.now(), size: 2048 };

      vault.setFolderChildren(BACKUP_FOLDER, [backup1, backup2]);

      const latest = await backupManager.getLatestBackup(file);

      expect(latest).not.toBeNull();
      expect(latest?.timestamp.getMonth()).toBe(0); // January (0-indexed)
      expect(latest?.timestamp.getDate()).toBe(15);
    });
  });

  describe('restoreBackup', () => {
    it('should restore canvas from backup', async () => {
      const file = new TFile('test.canvas');
      const backupPath = `${BACKUP_FOLDER}/test-20250101-100000.canvas`;

      vault._setFile('test.canvas', '{"nodes":[],"edges":[]}');
      vault._setFile(backupPath, '{"nodes":[{"id":"restored"}],"edges":[]}');

      await backupManager.restoreBackup(backupPath, file);

      const content = await vault.read(file);
      const data = JSON.parse(content);
      expect(data.nodes).toHaveLength(1);
      expect(data.nodes[0].id).toBe('restored');
    });

    it('should throw for non-existent backup', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}');

      await expect(
        backupManager.restoreBackup('nonexistent.canvas', file)
      ).rejects.toThrow('Backup not found');
    });

    it('should throw for corrupted backup', async () => {
      const file = new TFile('test.canvas');
      const backupPath = `${BACKUP_FOLDER}/test-20250101-100000.canvas`;

      vault._setFile('test.canvas', '{}');
      vault._setFile(backupPath, 'invalid json');

      await expect(backupManager.restoreBackup(backupPath, file)).rejects.toThrow(
        'Backup file is corrupted'
      );
    });
  });

  describe('deleteBackup', () => {
    it('should delete existing backup', async () => {
      const backupPath = `${BACKUP_FOLDER}/test-20250101-100000.canvas`;
      vault._setFile(backupPath, '{}');

      await backupManager.deleteBackup(backupPath);

      expect(vault.getAbstractFileByPath(backupPath)).toBeNull();
    });

    it('should not throw for non-existent backup', async () => {
      await expect(
        backupManager.deleteBackup('nonexistent.canvas')
      ).resolves.not.toThrow();
    });
  });

  describe('cleanupOldBackups', () => {
    it('should keep only specified number of backups', async () => {
      const file = new TFile('test.canvas');

      // Create mock backup files (will be cleaned up in real implementation)
      const backups: TFile[] = [];
      for (let i = 1; i <= 15; i++) {
        const day = String(i).padStart(2, '0');
        const backup = new TFile(`${BACKUP_FOLDER}/test-202501${day}-100000.canvas`);
        backup.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };
        backups.push(backup);
        vault._setFile(backup.path, '{}');
      }

      vault.setFolderChildren(BACKUP_FOLDER, backups);

      const deleted = await backupManager.cleanupOldBackups(file, 10);

      // Should delete 5 oldest backups (15 - 10 = 5)
      expect(deleted).toBe(5);
    });

    it('should not delete if backup count is within limit', async () => {
      const file = new TFile('test.canvas');

      const backups: TFile[] = [];
      for (let i = 1; i <= 5; i++) {
        const backup = new TFile(`${BACKUP_FOLDER}/test-2025010${i}-100000.canvas`);
        backup.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };
        backups.push(backup);
      }

      vault.setFolderChildren(BACKUP_FOLDER, backups);

      const deleted = await backupManager.cleanupOldBackups(file, 10);

      expect(deleted).toBe(0);
    });
  });

  describe('backupFolderExists', () => {
    it('should return false when folder does not exist', () => {
      expect(backupManager.backupFolderExists()).toBe(false);
    });

    it('should return true when folder exists', () => {
      vault._setFolder(BACKUP_FOLDER);
      expect(backupManager.backupFolderExists()).toBe(true);
    });
  });

  describe('getTotalBackupSize', () => {
    it('should return 0 when no backups exist', async () => {
      const size = await backupManager.getTotalBackupSize();
      expect(size).toBe(0);
    });

    it('should calculate total size of all backups', async () => {
      const backup1 = new TFile(`${BACKUP_FOLDER}/test-20250101-100000.canvas`);
      backup1.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };

      const backup2 = new TFile(`${BACKUP_FOLDER}/test-20250102-100000.canvas`);
      backup2.stat = { mtime: Date.now(), ctime: Date.now(), size: 2048 };

      vault.setFolderChildren(BACKUP_FOLDER, [backup1, backup2]);

      const size = await backupManager.getTotalBackupSize();

      expect(size).toBe(3072); // 1024 + 2048
    });
  });

  describe('Configuration', () => {
    describe('updateConfig', () => {
      it('should update configuration', () => {
        backupManager.updateConfig({ maxBackups: 20, autoBackup: false });

        const config = backupManager.getConfig();
        expect(config.maxBackups).toBe(20);
        expect(config.autoBackup).toBe(false);
      });

      it('should merge with existing config', () => {
        backupManager.updateConfig({ maxBackups: 5 });

        const config = backupManager.getConfig();
        expect(config.maxBackups).toBe(5);
        expect(config.autoBackup).toBe(true); // Default value preserved
      });
    });

    describe('getConfig', () => {
      it('should return copy of config', () => {
        const config1 = backupManager.getConfig();
        const config2 = backupManager.getConfig();

        expect(config1).not.toBe(config2);
        expect(config1).toEqual(config2);
      });
    });
  });
});
