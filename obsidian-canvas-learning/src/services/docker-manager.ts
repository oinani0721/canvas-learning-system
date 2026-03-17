/**
 * Canvas Learning System - Docker Manager
 * Story 1.8: Backend service management via command palette (AC-1 ~ AC-3, AC-6)
 *
 * Wraps docker-compose commands for start/restart/stop.
 * Handles cross-platform docker compose vs docker-compose detection.
 */

import { exec } from 'child_process';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

/** Max time to wait for docker-compose commands (ms). */
const DOCKER_COMPOSE_TIMEOUT = 120000;

export class DockerManager {
  private projectPath: string;
  private composeCmd: string | null = null;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
  }

  /**
   * Detect whether Docker is available and which compose command to use.
   * Returns { available, error? }.
   */
  async checkDockerAvailable(): Promise<{ available: boolean; error?: string }> {
    // Check Docker daemon
    try {
      await execAsync('docker info', { timeout: 15000 });
    } catch {
      return { available: false, error: '请先启动 Docker Desktop' };
    }

    // Check docker-compose.yml exists
    const composePath = this.findComposePath();
    if (!composePath) {
      return { available: false, error: 'docker-compose.yml 未找到' };
    }

    // Detect compose command: `docker compose` (v2 plugin) or `docker-compose` (standalone)
    try {
      await execAsync('docker compose version', { timeout: 10000 });
      this.composeCmd = 'docker compose';
    } catch {
      try {
        await execAsync('docker-compose version', { timeout: 10000 });
        this.composeCmd = 'docker-compose';
      } catch {
        return { available: false, error: 'docker-compose 命令不可用' };
      }
    }

    return { available: true };
  }

  /**
   * Start all backend services (docker-compose up -d).
   */
  async startServices(): Promise<void> {
    await this.execDockerCompose(['up', '-d']);
  }

  /**
   * Restart all backend services (docker-compose restart).
   */
  async restartServices(): Promise<void> {
    await this.execDockerCompose(['restart']);
  }

  /**
   * Stop all backend services (docker-compose stop). Preserves data volumes.
   */
  async stopServices(): Promise<void> {
    await this.execDockerCompose(['stop']);
  }

  /**
   * Execute a docker-compose command in the project directory.
   */
  private async execDockerCompose(
    args: string[],
  ): Promise<{ stdout: string; stderr: string }> {
    const cmd = this.composeCmd ?? 'docker compose';
    const composePath = this.findComposePath();
    if (!composePath) {
      throw new Error('docker-compose.yml 未找到');
    }

    const cwd = dirname(composePath);
    const fullCmd = `${cmd} -f "${composePath}" ${args.join(' ')}`;

    const result = await execAsync(fullCmd, {
      cwd,
      timeout: DOCKER_COMPOSE_TIMEOUT,
    });

    return { stdout: result.stdout, stderr: result.stderr };
  }

  /**
   * Find docker-compose.yml in common locations relative to projectPath.
   */
  private findComposePath(): string | null {
    const candidates = [
      join(this.projectPath, 'docker-compose.yml'),
      join(this.projectPath, 'docker', 'docker-compose.yml'),
      join(dirname(this.projectPath), 'docker-compose.yml'),
    ];

    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate;
      }
    }
    return null;
  }
}
