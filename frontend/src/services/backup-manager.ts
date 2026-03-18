/**
 * Canvas Learning System - Backup Manager (Tauri 2.0)
 *
 * Manages data backup and restore operations for the project's
 * Docker-managed data directories (neo4j-data, lancedb-data, config).
 *
 * Security: Uses @tauri-apps/plugin-fs for all file metadata operations
 * (mkdir, readDir, readFile, writeFile). Shell commands are ONLY used for
 * recursive directory copy (xcopy/cp -r with array arguments — no shell
 * interpretation, immune to injection).
 *
 * Story 1-8: Backend Service One-Click Start & Data Management
 */

import { Command } from '@tauri-apps/plugin-shell';
import {
  mkdir,
  readDir,
  readTextFile,
  writeTextFile,
  exists,
} from '@tauri-apps/plugin-fs';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface BackupInfo {
  /** Directory name of the backup (e.g., backup-2026-03-18T10-30-00). */
  name: string;
  /** ISO timestamp when the backup was created. */
  createdAt: string;
  /** Absolute path to the backup directory. */
  path: string;
}

export interface BackupResult {
  success: boolean;
  message: string;
  backupPath?: string;
}

export interface RestoreResult {
  success: boolean;
  message: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Directories to back up, relative to the project root. */
const BACKUP_TARGETS = [
  'docker/neo4j/data',
  'data',
] as const;

/** Backup directory name relative to the project root. */
const BACKUPS_DIR = 'backups';

/** Info file stored alongside each backup. */
const BACKUP_INFO_FILE = 'backup-info.json';

// ═══════════════════════════════════════════════════════════════════════════════
// Platform Detection
// ═══════════════════════════════════════════════════════════════════════════════

function isWindows(): boolean {
  return navigator.userAgent.includes('Windows') ||
    navigator.platform?.startsWith('Win') ||
    navigator.platform === 'Win32';
}

// ═══════════════════════════════════════════════════════════════════════════════
// BackupManager
// ═══════════════════════════════════════════════════════════════════════════════

export class BackupManager {
  /**
   * Create a timestamped backup of all data directories.
   *
   * @param projectPath - Absolute path to the project root.
   */
  async createBackup(projectPath: string): Promise<BackupResult> {
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, '-')
      .replace('Z', '');
    const backupName = `backup-${timestamp}`;
    const backupDir = joinPath(projectPath, BACKUPS_DIR, backupName);

    try {
      // Create the backup directory (Tauri fs — no shell)
      await mkdir(backupDir, { recursive: true });
    } catch (err) {
      return {
        success: false,
        message: `无法创建备份目录: ${err instanceof Error ? err.message : String(err)}`,
      };
    }

    // Copy each target directory
    let copiedCount = 0;
    for (const target of BACKUP_TARGETS) {
      const sourcePath = joinPath(projectPath, target);
      const destSubdir = target.replace(/\//g, '_');
      const destPath = joinPath(backupDir, destSubdir);

      // Check if source exists before copying
      try {
        const sourceExists = await exists(sourcePath);
        if (!sourceExists) {
          console.warn(`[BackupManager] 跳过 ${target}: 目录不存在`);
          continue;
        }
      } catch {
        console.warn(`[BackupManager] 跳过 ${target}: 无法检查`);
        continue;
      }

      try {
        await mkdir(destPath, { recursive: true });
      } catch {
        // Directory might already exist
      }

      // Recursive copy via shell (safe: array arguments, no shell interpretation)
      const copyResult = await this.copyDirectory(sourcePath, destPath);
      if (copyResult.success) {
        copiedCount++;
      } else {
        console.warn(`[BackupManager] 复制 ${target} 失败: ${copyResult.stderr}`);
      }
    }

    // Write backup info metadata (Tauri fs — no shell)
    const infoContent = JSON.stringify(
      {
        name: backupName,
        createdAt: new Date().toISOString(),
        targets: [...BACKUP_TARGETS],
        copiedCount,
      },
      null,
      2,
    );

    try {
      await writeTextFile(joinPath(backupDir, BACKUP_INFO_FILE), infoContent);
    } catch (err) {
      console.warn(`[BackupManager] 备份信息写入失败: ${err instanceof Error ? err.message : String(err)}`);
    }

    if (copiedCount === 0) {
      return {
        success: false,
        message: '备份失败: 没有成功复制任何数据目录',
      };
    }

    return {
      success: true,
      message: `备份创建成功: ${backupName} (${copiedCount}/${BACKUP_TARGETS.length} 目录)`,
      backupPath: backupDir,
    };
  }

  /**
   * List all existing backups, sorted by creation time (newest first).
   *
   * @param projectPath - Absolute path to the project root.
   */
  async listBackups(projectPath: string): Promise<BackupInfo[]> {
    const backupsPath = joinPath(projectPath, BACKUPS_DIR);
    const backups: BackupInfo[] = [];

    try {
      const dirExists = await exists(backupsPath);
      if (!dirExists) return backups;
    } catch {
      return backups;
    }

    // List contents via Tauri fs readDir (no shell)
    let entries: Array<{ name: string | undefined; isDirectory: boolean }>;
    try {
      entries = await readDir(backupsPath);
    } catch {
      return backups;
    }

    for (const entry of entries) {
      const name = entry.name;
      if (!name || !name.startsWith('backup-') || !entry.isDirectory) continue;

      const entryPath = joinPath(backupsPath, name);
      const infoPath = joinPath(entryPath, BACKUP_INFO_FILE);

      // Try to read backup-info.json (Tauri fs — no shell)
      try {
        const infoExists = await exists(infoPath);
        if (infoExists) {
          const raw = await readTextFile(infoPath);
          const info = JSON.parse(raw) as { name: string; createdAt: string };
          backups.push({ name: info.name, createdAt: info.createdAt, path: entryPath });
          continue;
        }
      } catch {
        // Fallback to directory name parsing
      }

      // Fallback: extract timestamp from directory name
      const tsMatch = name.match(/^backup-(\d{4}-\d{2}-\d{2}T[\d-]+)/);
      const createdAt = tsMatch
        ? tsMatch[1].replace(/-(\d{2})-(\d{2})-(\d{3})$/, ':$1:$2.$3Z')
        : new Date(0).toISOString();

      backups.push({ name, createdAt, path: entryPath });
    }

    // Sort newest first
    backups.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );

    return backups;
  }

  /**
   * Restore data from a backup.
   *
   * Stops services → copies backup data → restarts services.
   *
   * @param projectPath - Absolute path to the project root.
   * @param backupPath - Absolute path to the backup directory.
   * @param stopServices - Callback to stop Docker services before restoring.
   * @param startServices - Callback to start Docker services after restoring.
   */
  async restoreBackup(
    projectPath: string,
    backupPath: string,
    stopServices: () => Promise<void>,
    startServices: () => Promise<void>,
  ): Promise<RestoreResult> {
    // Step 1: Stop services
    try {
      await stopServices();
    } catch (err) {
      return {
        success: false,
        message: `停止服务失败: ${err instanceof Error ? err.message : String(err)}`,
      };
    }

    // Step 2: Restore each target
    for (const target of BACKUP_TARGETS) {
      const destSubdir = target.replace(/\//g, '_');
      const sourcePath = joinPath(backupPath, destSubdir);
      const destPath = joinPath(projectPath, target);

      // Check if this target exists in the backup (Tauri fs)
      try {
        const sourceExists = await exists(sourcePath);
        if (!sourceExists) continue;
      } catch {
        continue;
      }

      // Ensure dest directory exists
      try {
        await mkdir(destPath, { recursive: true });
      } catch {
        // May already exist
      }

      // Copy backup data back (safe shell: array args)
      const copyResult = await this.copyDirectory(sourcePath, destPath);
      if (!copyResult.success) {
        // Best-effort restart on failure
        try { await startServices(); } catch { /* best effort */ }
        return {
          success: false,
          message: `恢复 ${target} 失败: ${copyResult.stderr}`,
        };
      }
    }

    // Step 3: Restart services
    try {
      await startServices();
    } catch (err) {
      return {
        success: false,
        message: `数据已恢复但重启服务失败: ${err instanceof Error ? err.message : String(err)}`,
      };
    }

    return { success: true, message: '数据恢复成功，服务已重启' };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal: Recursive Directory Copy (shell with array args — safe)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Copy a directory recursively.
   *
   * Uses `xcopy` (Windows) or `cp -r` (Unix) with array-based arguments
   * passed to Tauri's Command.create(). Arguments are NOT interpreted by
   * a shell — each is passed as a separate argv entry, preventing injection.
   */
  private async copyDirectory(
    source: string,
    dest: string,
  ): Promise<{ success: boolean; stderr: string }> {
    try {
      if (isWindows()) {
        const winSource = source.replace(/\//g, '\\');
        const winDest = dest.replace(/\//g, '\\');
        const output = await Command.create('xcopy', [
          winSource,
          winDest,
          '/E', '/I', '/H', '/Y',
        ]).execute();
        return { success: output.code === 0, stderr: output.stderr };
      }

      const output = await Command.create('cp', [
        '-r', `${source}/.`, `${dest}/`,
      ]).execute();
      return { success: output.code === 0, stderr: output.stderr };
    } catch (err) {
      return {
        success: false,
        stderr: err instanceof Error ? err.message : String(err),
      };
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Utility
// ═══════════════════════════════════════════════════════════════════════════════

function joinPath(...segments: string[]): string {
  return segments
    .map((seg, i) => {
      let s = seg;
      if (i < segments.length - 1) s = s.replace(/[\\/]+$/, '');
      if (i > 0) s = s.replace(/^[\\/]+/, '');
      return s;
    })
    .join('/');
}
