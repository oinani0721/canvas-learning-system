/**
 * Canvas Learning System - Docker Manager (Tauri 2.0)
 *
 * Manages Docker Compose services (Neo4j, Ollama, Backend) via
 * @tauri-apps/plugin-shell Command API. Runs docker commands from
 * the Tauri native layer since the backend itself runs inside Docker.
 *
 * Story 1-8: Backend Service One-Click Start & Data Management
 *
 * Key features:
 * - Docker availability detection
 * - Docker Compose v2/v1 fallback
 * - Start/stop/restart all services
 * - Health check polling after start/restart
 * - Cross-platform (Windows + Unix)
 */

import { Command } from '@tauri-apps/plugin-shell';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export type DockerStatus =
  | 'unknown'
  | 'not_installed'
  | 'not_running'
  | 'available';

export type ServiceAction = 'start' | 'stop' | 'restart';

export interface DockerCheckResult {
  status: DockerStatus;
  message: string;
  composeVersion?: 'v2' | 'v1';
}

export interface CommandResult {
  success: boolean;
  stdout: string;
  stderr: string;
  code: number | null;
}

export interface HealthPollResult {
  ready: boolean;
  message: string;
  elapsedMs: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Health poll interval in milliseconds. */
const HEALTH_POLL_INTERVAL_MS = 3000;

/** Maximum wait time for health check polling (60 seconds). */
const HEALTH_POLL_TIMEOUT_MS = 60000;

// ═══════════════════════════════════════════════════════════════════════════════
// DockerManager
// ═══════════════════════════════════════════════════════════════════════════════

export class DockerManager {
  /**
   * Cached compose command style: 'v2' for `docker compose` (Docker Desktop v2+),
   * 'v1' for standalone `docker-compose`. Determined on first use.
   */
  private composeStyle: 'v2' | 'v1' | null = null;

  /**
   * Check whether Docker is installed and the Docker daemon is running.
   * Also detects available Docker Compose version (v2 plugin vs v1 standalone).
   */
  async checkDocker(): Promise<DockerCheckResult> {
    // Step 1: Check if docker binary is available via `docker info`
    const dockerInfo = await this.execCommand('docker', ['info']);
    if (!dockerInfo.success) {
      // Distinguish "not installed" from "daemon not running"
      const combined = (dockerInfo.stdout + dockerInfo.stderr).toLowerCase();
      const isNotInstalled =
        combined.includes('not found') ||
        combined.includes('enoent') ||
        combined.includes('program not found') ||
        combined.includes('not recognized');

      if (isNotInstalled) {
        return {
          status: 'not_installed',
          message: 'Docker 未安装。请先安装 Docker Desktop。',
        };
      }

      return {
        status: 'not_running',
        message: 'Docker 守护进程未运行。请启动 Docker Desktop。',
      };
    }

    // Step 2: Detect Docker Compose version
    const composeVersion = await this.detectComposeVersion();
    if (!composeVersion) {
      return {
        status: 'not_running',
        message: 'Docker 已安装，但未找到 Docker Compose。请确认 Docker Desktop 已更新。',
      };
    }

    this.composeStyle = composeVersion;

    return {
      status: 'available',
      message: `Docker 就绪 (Compose ${composeVersion})`,
      composeVersion,
    };
  }

  /**
   * Start all Docker Compose services in detached mode.
   *
   * @param projectPath - Absolute path to the project root containing docker-compose.yml.
   */
  async startServices(projectPath: string): Promise<CommandResult> {
    return this.runCompose(projectPath, ['up', '-d']);
  }

  /**
   * Restart all Docker Compose services.
   *
   * @param projectPath - Absolute path to the project root containing docker-compose.yml.
   */
  async restartServices(projectPath: string): Promise<CommandResult> {
    return this.runCompose(projectPath, ['restart']);
  }

  /**
   * Stop all Docker Compose services (without removing containers).
   *
   * @param projectPath - Absolute path to the project root containing docker-compose.yml.
   */
  async stopServices(projectPath: string): Promise<CommandResult> {
    return this.runCompose(projectPath, ['stop']);
  }

  /**
   * Poll the backend health endpoint until it reports healthy or timeout.
   *
   * After starting or restarting services, use this to wait for the backend
   * API to become available (AC-7).
   *
   * @param backendUrl - The backend base URL (e.g., http://localhost:8001).
   * @param onProgress - Optional callback invoked on each poll attempt.
   * @returns Result indicating whether the backend became ready within the timeout.
   */
  async pollHealthUntilReady(
    backendUrl: string,
    onProgress?: (attempt: number, elapsedMs: number) => void,
  ): Promise<HealthPollResult> {
    const startTime = Date.now();
    let attempt = 0;

    while (Date.now() - startTime < HEALTH_POLL_TIMEOUT_MS) {
      attempt++;
      const elapsed = Date.now() - startTime;

      if (onProgress) {
        onProgress(attempt, elapsed);
      }

      try {
        const response = await fetch(
          `${backendUrl.replace(/\/+$/, '')}/api/v1/system/health`,
          {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(5000),
          },
        );

        if (response.ok) {
          return {
            ready: true,
            message: '后端服务已就绪',
            elapsedMs: Date.now() - startTime,
          };
        }
      } catch {
        // Backend not ready yet — continue polling
      }

      // Wait before next poll
      await new Promise<void>((resolve) =>
        setTimeout(resolve, HEALTH_POLL_INTERVAL_MS),
      );
    }

    return {
      ready: false,
      message: '后端启动但 API 未就绪，请检查日志',
      elapsedMs: Date.now() - startTime,
    };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Detect whether Docker Compose v2 (plugin) or v1 (standalone) is available.
   * Tries `docker compose version` first, then falls back to `docker-compose version`.
   */
  private async detectComposeVersion(): Promise<'v2' | 'v1' | null> {
    // Try Docker Compose v2 (plugin mode: `docker compose`)
    const v2Check = await this.execCommand('docker', ['compose', 'version']);
    if (v2Check.success) {
      return 'v2';
    }

    // Try Docker Compose v1 (standalone: `docker-compose`)
    const v1Check = await this.execCommand('docker-compose-v1', ['version']);
    if (v1Check.success) {
      return 'v1';
    }

    return null;
  }

  /**
   * Run a Docker Compose command with the correct compose style.
   * Ensures compose style is detected before running.
   *
   * @param projectPath - Absolute path to the project root.
   * @param composeArgs - Arguments to pass after `compose` (e.g., ['up', '-d']).
   */
  private async runCompose(
    projectPath: string,
    composeArgs: string[],
  ): Promise<CommandResult> {
    // Auto-detect compose style if not cached
    if (!this.composeStyle) {
      const detected = await this.detectComposeVersion();
      if (!detected) {
        return {
          success: false,
          stdout: '',
          stderr: 'Docker Compose 未找到。请安装 Docker Desktop 或 docker-compose。',
          code: -1,
        };
      }
      this.composeStyle = detected;
    }

    // Normalize path: forward slashes for docker-compose.yml reference
    const composeFile = projectPath.replace(/\\/g, '/') + '/docker-compose.yml';

    if (this.composeStyle === 'v2') {
      // docker compose -f /path/docker-compose.yml up -d
      return this.execCommand('docker', [
        'compose',
        '-f',
        composeFile,
        ...composeArgs,
      ]);
    }

    // docker-compose -f /path/docker-compose.yml up -d
    return this.execCommand('docker-compose-v1', [
      '-f',
      composeFile,
      ...composeArgs,
    ]);
  }

  /**
   * Execute a shell command via Tauri Shell plugin and return structured result.
   *
   * @param commandName - Scoped command name registered in capabilities/default.json.
   * @param args - Arguments to pass to the command.
   */
  private async execCommand(
    commandName: string,
    args: string[],
  ): Promise<CommandResult> {
    try {
      const output = await Command.create(commandName, args).execute();
      return {
        success: output.code === 0,
        stdout: output.stdout,
        stderr: output.stderr,
        code: output.code,
      };
    } catch (err) {
      return {
        success: false,
        stdout: '',
        stderr: err instanceof Error ? err.message : String(err),
        code: null,
      };
    }
  }
}
