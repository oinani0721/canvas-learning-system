/**
 * Canvas Learning System - Health Poller
 * Story 1.8: Post-startup health check polling (AC-7)
 *
 * After docker-compose up/restart, polls the backend /health endpoint
 * until the API is ready or a timeout is reached (60s max, 3s intervals).
 */

import type { ApiClient } from './api-client';
import { systemState } from '../stores/system-state.svelte';

/** Max wait time for backend to become ready (ms). */
const MAX_WAIT_MS = 60000;
/** Interval between health check polls (ms). */
const POLL_INTERVAL_MS = 3000;

/**
 * Wait for the backend API to become ready after starting Docker services.
 * Updates systemState.backendRunning on success.
 *
 * @returns true if backend became ready within timeout, false otherwise.
 */
export async function waitForBackendReady(apiClient: ApiClient): Promise<boolean> {
  const start = Date.now();

  while (Date.now() - start < MAX_WAIT_MS) {
    const health = await apiClient.checkHealth();
    if (health) {
      systemState.setBackendRunning(true);
      return true;
    }

    // Wait before next poll
    await new Promise<void>(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  // Timeout: backend did not become ready
  return false;
}
