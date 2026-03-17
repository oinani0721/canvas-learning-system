/**
 * Canvas Learning System - Sync Engine
 * Story 1.5: Canvas Data Sync to Backend KG (AC-1, AC-2, AC-3, AC-5, AC-6)
 *
 * Consumes the sync_outbox table written by canvas-state and batch-syncs
 * changes to the backend Neo4j knowledge graph.
 *
 * Architecture:
 *   User operation → canvasState → Dexie (IndexedDB + sync_outbox)
 *   → SyncEngine polls sync_outbox → 2s debounce → POST /api/v1/sync/batch
 *   → Neo4j MERGE (idempotent) → mark outbox entries as synced
 *
 * State machine:
 *   IDLE ──(outbox has entries)──→ SYNCING
 *   SYNCING ──(success)──→ IDLE
 *   SYNCING ──(5 consecutive failures)──→ OFFLINE
 *   OFFLINE ──(health check OK)──→ IDLE
 *
 * [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 1]
 * [Source: Architecture — Outbox pattern, delta sync, last-write-wins]
 */

import { db } from './dexie-db';
import { now } from '../utils/canvas-math';
import { systemState, type SyncState } from '../stores/system-state.svelte';
import type { ApiClient } from './api-client';
import type { SyncBatchRequest, SyncOperation } from '../types/api';
import type { SyncOutboxEntry } from '../types/canvas';
import { Notice } from 'obsidian';

/** Maximum operations per batch request. */
const BATCH_SIZE = 50;

/** Debounce delay (ms) — wait for rapid operations to accumulate. */
const DEBOUNCE_MS = 2000;

/** Base retry delay (ms) for exponential backoff. */
const RETRY_BASE_MS = 2000;

/** Maximum consecutive failures before switching to OFFLINE. */
const MAX_RETRIES = 5;

/** Interval (ms) for health checks while OFFLINE. */
const HEALTH_CHECK_INTERVAL_MS = 30_000;

/** Interval (ms) for cleaning up old synced Outbox entries. */
const CLEANUP_INTERVAL_MS = 3_600_000; // 1 hour

/** Max age (ms) for synced Outbox entries before cleanup. */
const SYNCED_MAX_AGE_MS = 86_400_000; // 24 hours

/** Interval (ms) for polling the Outbox for new entries. */
const POLL_INTERVAL_MS = 1000;

/**
 * SyncEngine: consumes the Outbox and syncs to the backend.
 *
 * Lifecycle: call start() on plugin load, stop() on plugin unload.
 */
export class SyncEngine {
  private apiClient: ApiClient;
  private state: SyncState = 'IDLE';
  private consecutiveFailures = 0;

  // Timers
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private healthCheckTimer: ReturnType<typeof setInterval> | null = null;
  private cleanupTimer: ReturnType<typeof setInterval> | null = null;

  // Prevents concurrent sync attempts
  private syncing = false;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Lifecycle
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Start the sync engine.
   * Begins polling the Outbox and sets up cleanup timer.
   *
   * [Source: Story 1.5 Task 1.8 — Plugin onload]
   */
  start(): void {
    console.log('[Canvas Learning] SyncEngine started');
    this.setState('IDLE');

    // Poll Outbox for pending entries
    this.pollTimer = setInterval(() => {
      this.checkOutbox();
    }, POLL_INTERVAL_MS);

    // Periodic cleanup of old synced entries (AC-5)
    this.cleanupTimer = setInterval(() => {
      this.cleanupSyncedEntries();
    }, CLEANUP_INTERVAL_MS);

    // Trigger an initial check
    this.checkOutbox();
  }

  /**
   * Stop the sync engine.
   * Cancels all timers and resets state.
   *
   * [Source: Story 1.5 Task 1.8 — Plugin onunload]
   */
  stop(): void {
    console.log('[Canvas Learning] SyncEngine stopped');

    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    if (this.healthCheckTimer !== null) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
    if (this.cleanupTimer !== null) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    this.syncing = false;
    this.consecutiveFailures = 0;
    this.setState('IDLE');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // State Machine
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Transition to a new state and update the system state store.
   *
   * [Source: Story 1.5 Task 3.2 — SyncEngine → systemState]
   */
  private setState(newState: SyncState): void {
    if (this.state === newState) return;

    const prev = this.state;
    this.state = newState;
    systemState.setSyncState(newState);

    console.log(`[Canvas Learning] SyncEngine: ${prev} → ${newState}`);

    // Start/stop health checks based on state
    if (newState === 'OFFLINE') {
      this.startHealthCheck();
    } else {
      this.stopHealthCheck();
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Outbox Consumption (AC-1)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Check if there are pending Outbox entries and schedule a sync.
   * Uses a 2s debounce to accumulate rapid operations.
   *
   * [Source: Story 1.5 Task 1.3 — Outbox polling with 2s debounce]
   */
  private async checkOutbox(): Promise<void> {
    if (this.state === 'OFFLINE' || this.syncing) return;

    try {
      const pendingCount = await db.sync_outbox
        .where('syncedAt')
        .equals('')
        .count()
        .catch(() =>
          // Fallback: count entries without syncedAt
          db.sync_outbox.filter((e) => !e.syncedAt).count(),
        );

      systemState.setPendingSyncCount(pendingCount);

      if (pendingCount > 0) {
        // Debounce: wait for more operations before syncing
        if (this.debounceTimer !== null) {
          clearTimeout(this.debounceTimer);
        }
        this.debounceTimer = setTimeout(() => {
          this.debounceTimer = null;
          this.performSync();
        }, DEBOUNCE_MS);
      }
    } catch (err) {
      console.warn('[Canvas Learning] SyncEngine: outbox check error:', err);
    }
  }

  /**
   * Perform the actual sync: read pending entries, batch POST, mark synced.
   *
   * [Source: Story 1.5 Task 1.4 — batch sync request]
   * [Source: Story 1.5 AC-2 — optimistic update, async background sync]
   */
  private async performSync(): Promise<void> {
    if (this.syncing || this.state === 'OFFLINE') return;
    this.syncing = true;
    this.setState('SYNCING');

    try {
      // Read pending entries ordered by createdAt (AC-3: preserve order)
      const pendingEntries = await db.sync_outbox
        .filter((e) => !e.syncedAt)
        .sortBy('createdAt');

      if (pendingEntries.length === 0) {
        this.syncing = false;
        this.setState('IDLE');
        return;
      }

      // Process in batches of BATCH_SIZE
      const batch = pendingEntries.slice(0, BATCH_SIZE);

      // Group by canvasId for the request
      // All entries in a single batch should typically be for the same canvas,
      // but we handle multiple canvases by using the first entry's canvasId
      const canvasId = this.extractCanvasId(batch);

      const operations: SyncOperation[] = batch.map((entry) => ({
        operationId: String(entry.id),
        entityType: entry.entityType,
        entityId: entry.entityId,
        operation: entry.operation,
        payload: entry.payload,
        timestamp: entry.createdAt,
      }));

      const request: SyncBatchRequest = {
        canvasId,
        operations,
      };

      const response = await this.apiClient.syncBatch(request);

      // Mark successful operations as synced (AC-2, AC-5)
      const syncedAt = now();
      const successIds: number[] = [];
      for (const result of response.results) {
        if (result.success) {
          const entryId = parseInt(result.operationId, 10);
          if (!isNaN(entryId)) {
            successIds.push(entryId);
          }
        }
      }

      if (successIds.length > 0) {
        await db.sync_outbox.bulkUpdate(
          successIds.map((id) => ({
            key: id,
            changes: { syncedAt },
          })),
        );
      }

      // Update state
      this.consecutiveFailures = 0;
      systemState.setLastSuccessfulSync(new Date());
      systemState.setPendingSyncCount(
        Math.max(0, pendingEntries.length - successIds.length),
      );

      if (response.failedCount > 0) {
        console.warn(
          `[Canvas Learning] SyncEngine: ${response.failedCount} operations failed`,
        );
      }

      this.syncing = false;
      this.setState('IDLE');

      // If there are more pending entries, schedule another sync
      if (pendingEntries.length > BATCH_SIZE) {
        this.checkOutbox();
      }
    } catch (err) {
      this.syncing = false;
      this.handleSyncFailure(err);
    }
  }

  /**
   * Extract canvasId from a batch of outbox entries.
   * Uses the payload's canvasId field, falling back to 'unknown'.
   */
  private extractCanvasId(entries: SyncOutboxEntry[]): string {
    for (const entry of entries) {
      const cid = entry.payload?.canvasId;
      if (typeof cid === 'string' && cid) {
        return cid;
      }
    }
    return 'unknown';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Retry & Failure Handling (AC-3)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Handle a sync failure with exponential backoff.
   *
   * [Source: Story 1.5 Task 1.5 — exponential backoff 2s→4s→8s→16s→32s]
   */
  private handleSyncFailure(err: unknown): void {
    this.consecutiveFailures++;
    const errorMsg = err instanceof Error ? err.message : String(err);

    systemState.setSyncError(errorMsg);
    console.warn(
      `[Canvas Learning] SyncEngine: sync failure #${this.consecutiveFailures}: ${errorMsg}`,
    );

    if (this.consecutiveFailures >= MAX_RETRIES) {
      // Switch to OFFLINE after max retries (AC-3)
      this.setState('OFFLINE');
      new Notice('Canvas Learning: 后端不可达，同步已暂停', 5000);
      return;
    }

    // Exponential backoff: 2s, 4s, 8s, 16s, 32s
    const delay = RETRY_BASE_MS * Math.pow(2, this.consecutiveFailures - 1);
    console.log(
      `[Canvas Learning] SyncEngine: retrying in ${delay}ms`,
    );

    // Schedule retry
    setTimeout(() => {
      this.performSync();
    }, delay);

    // Stay in SYNCING state during retries
    this.setState('SYNCING');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // OFFLINE Recovery (AC-3)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Start periodic health checks to detect backend recovery.
   *
   * [Source: Story 1.5 Task 1.6 — OFFLINE health check every 30s]
   */
  private startHealthCheck(): void {
    this.stopHealthCheck();
    this.healthCheckTimer = setInterval(async () => {
      try {
        const health = await this.apiClient.checkHealth();
        if (health) {
          console.log('[Canvas Learning] SyncEngine: backend recovered');
          this.consecutiveFailures = 0;
          this.setState('IDLE');
          // Resume syncing
          this.checkOutbox();
        }
      } catch {
        // Still offline, keep checking
      }
    }, HEALTH_CHECK_INTERVAL_MS);
  }

  /**
   * Stop health check polling.
   */
  private stopHealthCheck(): void {
    if (this.healthCheckTimer !== null) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Outbox Cleanup (AC-5)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Remove Outbox entries that were synced more than 24 hours ago.
   *
   * [Source: Story 1.5 Task 2.1 — periodic cleanup]
   */
  private async cleanupSyncedEntries(): Promise<void> {
    try {
      const cutoff = new Date(Date.now() - SYNCED_MAX_AGE_MS).toISOString();
      const toDelete = await db.sync_outbox
        .filter((e) => !!e.syncedAt && e.syncedAt < cutoff)
        .primaryKeys();

      if (toDelete.length > 0) {
        await db.sync_outbox.bulkDelete(toDelete);
        console.log(
          `[Canvas Learning] SyncEngine: cleaned up ${toDelete.length} old outbox entries`,
        );
      }
    } catch (err) {
      console.warn('[Canvas Learning] SyncEngine: cleanup error:', err);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Public Query Methods (Task 2.2)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Get the count of pending (unsynced) Outbox entries.
   */
  async getPendingCount(): Promise<number> {
    return db.sync_outbox.filter((e) => !e.syncedAt).count();
  }

  /**
   * Get the timestamp of the oldest pending entry, or null if none.
   */
  async getOldestPending(): Promise<Date | null> {
    const oldest = await db.sync_outbox
      .filter((e) => !e.syncedAt)
      .sortBy('createdAt');

    if (oldest.length > 0) {
      return new Date(oldest[0].createdAt);
    }
    return null;
  }
}
