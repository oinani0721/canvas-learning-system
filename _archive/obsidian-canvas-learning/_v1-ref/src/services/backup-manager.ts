/**
 * Canvas Learning System - Backup Manager
 * Story 1.8: Data backup and restore (AC-4, AC-5)
 *
 * Backs up Neo4j data and plugin config to timestamped directories.
 * LanceDB backup path will be added when Story 2.x establishes its data directory.
 * Restore includes pre-restore snapshot for rollback safety.
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync, cpSync } from 'fs';
import { join, basename } from 'path';
import type { DockerManager } from './docker-manager';

export interface BackupProgress {
  step: number;
  totalSteps: number;
  description: string;
}

export interface BackupInfo {
  path: string;
  timestamp: string;
  version: string;
  components: string[];
}

export class BackupManager {
  private backupBaseDir: string;
  private dockerManager: DockerManager;
  private neo4jDataDir: string;
  private pluginDataPath: string;

  constructor(
    projectPath: string,
    dockerManager: DockerManager,
    pluginDataPath: string,
  ) {
    this.backupBaseDir = join(projectPath, 'backups');
    this.dockerManager = dockerManager;
    this.neo4jDataDir = join(projectPath, 'docker', 'neo4j', 'data');
    this.pluginDataPath = pluginDataPath;
  }

  /**
   * Create a full backup (AC-4).
   * Steps: (1) Neo4j data, (2) plugin config.
   */
  async createBackup(
    onProgress: (p: BackupProgress) => void,
  ): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const backupDir = join(this.backupBaseDir, timestamp);

    try {
      mkdirSync(backupDir, { recursive: true });

      // Step 1/2: Backup Neo4j data
      onProgress({ step: 1, totalSteps: 2, description: 'Neo4j' });
      const neo4jBackup = join(backupDir, 'neo4j-data');
      if (existsSync(this.neo4jDataDir)) {
        cpSync(this.neo4jDataDir, neo4jBackup, {
          recursive: true,
          filter: (src: string) => {
            const name = basename(src);
            return !name.endsWith('.lock') && !name.endsWith('.tmp') && name !== '__pycache__';
          },
        });
      } else {
        mkdirSync(neo4jBackup, { recursive: true });
      }

      // Step 2/2: Plugin config
      onProgress({ step: 2, totalSteps: 2, description: '配置' });
      const configBackup = join(backupDir, 'config');
      mkdirSync(configBackup, { recursive: true });
      if (existsSync(this.pluginDataPath)) {
        const configContent = readFileSync(this.pluginDataPath, 'utf-8');
        writeFileSync(join(configBackup, 'data.json'), configContent, 'utf-8');
      }

      // Write backup metadata
      const meta = {
        version: '1.0',
        timestamp: new Date().toISOString(),
        components: ['neo4j', 'config'],
        pluginVersion: '0.1.0',
      };
      writeFileSync(join(backupDir, 'backup-meta.json'), JSON.stringify(meta, null, 2), 'utf-8');

      return backupDir;
    } catch (error) {
      // Clean up incomplete backup
      if (existsSync(backupDir)) {
        rmSync(backupDir, { recursive: true, force: true });
      }
      throw error;
    }
  }

  /**
   * List available backups, sorted by time descending (AC-5).
   * Scans the backups/ directory for subdirectories containing backup-meta.json.
   */
  listBackups(): BackupInfo[] {
    const backups: BackupInfo[] = new Array<BackupInfo>();

    if (!existsSync(this.backupBaseDir)) {
      return backups;
    }

    const entries = readdirSync(this.backupBaseDir, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name.startsWith('_pre-restore')) continue;

      const metaPath = join(this.backupBaseDir, entry.name, 'backup-meta.json');
      if (!existsSync(metaPath)) continue;

      try {
        const meta = JSON.parse(readFileSync(metaPath, 'utf-8'));
        backups.push({
          path: join(this.backupBaseDir, entry.name),
          timestamp: meta.timestamp,
          version: meta.version,
          components: meta.components,
        });
      } catch {
        // Skip entries with corrupted metadata files
        continue;
      }
    }

    // Sort newest first
    backups.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    return backups;
  }

  /**
   * Restore from a backup (AC-5).
   * Steps: (1) stop services, (2) pre-restore snapshot, (3) restore Neo4j,
   *        (4) restore config + restart.
   */
  async restoreBackup(
    backupPath: string,
    onProgress: (p: BackupProgress) => void,
  ): Promise<void> {
    // Step 1/4: Stop backend services
    onProgress({ step: 1, totalSteps: 4, description: '停止服务' });
    try {
      await this.dockerManager.stopServices();
    } catch {
      // Services might not be running — continue
    }

    // Step 2/4: Create pre-restore snapshot for rollback
    const preRestoreDir = join(
      this.backupBaseDir,
      `_pre-restore-${Date.now()}`,
    );
    onProgress({ step: 2, totalSteps: 4, description: '创建恢复前快照' });
    mkdirSync(preRestoreDir, { recursive: true });
    if (existsSync(this.neo4jDataDir)) {
      cpSync(this.neo4jDataDir, join(preRestoreDir, 'neo4j-data'), { recursive: true });
    }

    try {
      // Step 3/4: Restore Neo4j data
      onProgress({ step: 3, totalSteps: 4, description: '恢复 Neo4j' });
      const neo4jSource = join(backupPath, 'neo4j-data');
      if (existsSync(neo4jSource)) {
        if (existsSync(this.neo4jDataDir)) {
          rmSync(this.neo4jDataDir, { recursive: true, force: true });
        }
        cpSync(neo4jSource, this.neo4jDataDir, { recursive: true });
      }

      // Step 4/4: Restore config + restart
      onProgress({ step: 4, totalSteps: 4, description: '恢复配置并重启服务' });
      const configSource = join(backupPath, 'config', 'data.json');
      if (existsSync(configSource)) {
        const configContent = readFileSync(configSource, 'utf-8');
        writeFileSync(this.pluginDataPath, configContent, 'utf-8');
      }

      await this.dockerManager.startServices();

      // Clean up pre-restore snapshot on success
      rmSync(preRestoreDir, { recursive: true, force: true });
    } catch (error) {
      // Rollback: restore from pre-restore snapshot
      const preRestoreNeo4j = join(preRestoreDir, 'neo4j-data');
      if (existsSync(preRestoreNeo4j)) {
        if (existsSync(this.neo4jDataDir)) {
          rmSync(this.neo4jDataDir, { recursive: true, force: true });
        }
        cpSync(preRestoreNeo4j, this.neo4jDataDir, { recursive: true });
      }
      try {
        await this.dockerManager.startServices();
      } catch {
        // Best effort restart after rollback
      }
      throw error;
    }
  }
}
