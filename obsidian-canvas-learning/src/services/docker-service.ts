/**
 * Canvas Learning System - Docker Service
 * Story 1.2: Setup Wizard (AC-2, AC-4)
 *
 * Provides Docker Desktop detection and one-click backend start
 * via Node.js child_process (available in Obsidian's Electron environment).
 */

import { exec } from 'child_process';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

/** Timeout for Docker commands (ms). */
const DOCKER_CMD_TIMEOUT = 15000;

/** Delay after starting backend before re-check (ms). */
export const BACKEND_START_WAIT = 8000;

export class DockerService {
  /**
   * Check if Docker Desktop is running by executing `docker info`.
   * Returns true if exit code is 0, false otherwise.
   */
  async isDockerRunning(): Promise<boolean> {
    try {
      await execAsync('docker info', { timeout: DOCKER_CMD_TIMEOUT });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Start the backend services via docker-compose.
   * Searches for docker-compose.yml in common locations relative to the vault.
   *
   * @param composePath - Absolute path to the docker-compose.yml file
   * @throws Error if docker-compose command fails
   */
  async startBackend(composePath: string): Promise<void> {
    await execAsync(
      `docker-compose -f "${composePath}" up -d`,
      { timeout: 60000 },
    );
  }

  /**
   * Try to find the docker-compose.yml file in common locations.
   * Returns the first valid path found, or null if none exists.
   *
   * @param vaultPath - The Obsidian vault's base path
   */
  findComposePath(vaultPath: string): string | null {
    // Common locations to search for docker-compose.yml
    const candidates = [
      // Same level as vault (project root pattern)
      join(dirname(vaultPath), 'docker-compose.yml'),
      // Inside vault
      join(vaultPath, 'docker-compose.yml'),
      // Parent of vault parent (monorepo pattern)
      join(dirname(dirname(vaultPath)), 'docker-compose.yml'),
      // canvas-learning-system directory
      join(dirname(vaultPath), 'canvas-learning-system', 'docker-compose.yml'),
    ];

    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate;
      }
    }

    return null;
  }
}
