/**
 * SyncEngine — Outbox consumer with state machine
 * Story 1-5: Delta sync from IndexedDB outbox to backend Neo4j
 *
 * State machine: IDLE → SYNCING → IDLE (success) / OFFLINE (5 failures)
 * OFFLINE → IDLE (health check recovery every 30s)
 *
 * Retry: exponential backoff 2s → 4s → 8s → 16s → 32s, max 5 attempts
 * Debounce: 2s after last outbox write before triggering sync
 */
import { db, type SyncOutboxEntry } from './dexie-db';
import {
  ApiClient,
  SyncNetworkError,
  SyncServerError,
  type SyncOperation,
  type SyncBatchRequest,
} from './api-client';

export type SyncState = 'idle' | 'syncing' | 'offline';

type SyncListener = (state: SyncState, pendingCount: number) => void;

const DEBOUNCE_MS = 2000;
const BASE_RETRY_MS = 2000;
const MAX_RETRIES = 5;
const HEALTH_CHECK_INTERVAL_MS = 30000;
const BATCH_SIZE = 50;
const OUTBOX_RETENTION_MS = 24 * 60 * 60 * 1000; // 24h

export class SyncEngine {
  private apiClient: ApiClient;
  private state: SyncState = 'idle';
  private consecutiveFailures = 0;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private healthCheckTimer: ReturnType<typeof setInterval> | null = null;
  private listeners: Set<SyncListener> = new Set();
  private running = false;
  private pendingCount = 0;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /** Subscribe to state changes. Returns unsubscribe function. */
  subscribe(listener: SyncListener): () => void {
    this.listeners.add(listener);
    // Immediately notify current state
    listener(this.state, this.pendingCount);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    for (const listener of this.listeners) {
      listener(this.state, this.pendingCount);
    }
  }

  private setState(newState: SyncState) {
    if (this.state === newState) return;
    this.state = newState;
    this.notify();
  }

  /** Start the sync engine. Call once on app mount. */
  start() {
    if (this.running) return;
    this.running = true;
    // Watch outbox for changes via polling (Dexie hooks don't support cross-tab)
    this.schedulePoll();
  }

  /** Stop the sync engine. Call on app unmount. */
  stop() {
    this.running = false;
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }

  /** Trigger a sync attempt after debounce period. */
  triggerSync() {
    if (!this.running) return;
    if (this.state === 'offline') return; // wait for health check
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.processOutbox();
    }, DEBOUNCE_MS);
  }

  /** Main sync loop: consume outbox entries in batches. */
  private async processOutbox() {
    if (this.state === 'syncing') return;
    if (this.state === 'offline') return;

    // Get pending entries (not yet synced)
    const pending = await db.sync_outbox
      .where('syncedAt')
      .equals('')
      .or('syncedAt')
      .equals(undefined as unknown as string)
      .toArray()
      .catch(() =>
        // Fallback: get all entries without syncedAt
        db.sync_outbox.filter((e) => !e.syncedAt).toArray(),
      );

    // Also try getting entries that were never synced (syncedAt is undefined)
    let allPending: SyncOutboxEntry[];
    try {
      allPending = await db.sync_outbox.filter((e) => !e.syncedAt).toArray();
    } catch {
      allPending = pending;
    }

    this.pendingCount = allPending.length;
    this.notify();

    if (allPending.length === 0) {
      this.cleanupOldEntries();
      return;
    }

    this.setState('syncing');

    // Process in batches
    for (let i = 0; i < allPending.length; i += BATCH_SIZE) {
      if (!this.running) break;

      const batch = allPending.slice(i, i + BATCH_SIZE);
      const success = await this.sendBatch(batch);

      if (!success) {
        this.consecutiveFailures++;
        if (this.consecutiveFailures >= MAX_RETRIES) {
          this.setState('offline');
          this.startHealthCheck();
          return;
        }
        // Exponential backoff retry
        const delay = BASE_RETRY_MS * Math.pow(2, this.consecutiveFailures - 1);
        await this.sleep(delay);
        // Retry this batch
        i -= BATCH_SIZE;
        continue;
      }

      this.consecutiveFailures = 0;
    }

    this.pendingCount = 0;
    this.setState('idle');

    // Schedule next poll
    this.schedulePoll();
  }

  /** Send a batch of outbox entries to the backend.
   *
   * FR-KG-04 Phase 14 (Tasks 14.1-14.3): canvasId is strictly required.
   *
   * The previous implementation fell back to the literal string 'default'
   * when an outbox entry was missing both payload.canvasId and
   * payload.canvas_id. That silently routed orphaned entries into a
   * virtual "default" canvas bucket — which then either masked a Wave 1
   * canvas-store bug (the original motivation for the fallback) or
   * polluted a real canvas named "default". Wave 1 fixed the upstream
   * omission, so this fallback now has zero legitimate triggers and only
   * hides bugs. We enforce the invariant instead: an entry with no
   * resolvable canvasId is skipped for this poll cycle, a structured
   * warning is logged identifying the entry id, and the entry remains
   * in sync_outbox so a follow-up fix can re-submit it without data
   * loss.
   */
  private async sendBatch(entries: SyncOutboxEntry[]): Promise<boolean> {
    // Group by canvasId (from payload). Skip entries whose canvasId cannot
    // be resolved — they stay in the outbox for the next poll, which
    // surfaces the bug instead of quietly sending to a 'default' bucket.
    const grouped = new Map<string, SyncOutboxEntry[]>();
    for (const entry of entries) {
      const canvasId =
        (entry.payload.canvasId as string) ??
        (entry.payload.canvas_id as string);
      if (!canvasId) {
        console.warn(
          '[SyncEngine] Outbox entry missing canvasId, skipping',
          entry.id,
          {
            entityType: entry.entityType,
            entityId: entry.entityId,
          },
        );
        continue;
      }
      const existing = grouped.get(canvasId);
      if (existing) {
        existing.push(entry);
      } else {
        grouped.set(canvasId, [entry]);
      }
    }

    let allSuccess = true;
    for (const [canvasId, groupEntries] of grouped) {
      const operations: SyncOperation[] = groupEntries.map((e) => ({
        operationId: e.id?.toString() ?? crypto.randomUUID(),
        entityType: e.entityType,
        entityId: e.entityId,
        operation: e.operation,
        payload: e.payload,
        timestamp: e.createdAt,
      }));

      const request: SyncBatchRequest = {
        canvasId,
        subjectId: (groupEntries[0]?.payload.subjectId as string) ?? null,
        operations,
      };

      try {
        const response = await this.apiClient.syncBatch(request);
        // Mark successful entries as synced
        const syncedAt = new Date().toISOString();
        const successIds = response.results
          .filter((r) => r.success)
          .map((r) => r.operationId);

        for (const entry of groupEntries) {
          const opId = entry.id?.toString() ?? '';
          if (successIds.includes(opId)) {
            await db.sync_outbox.update(entry.id!, { syncedAt });
          }
        }

        // If any failed, mark as partial failure
        if (response.failedCount > 0) {
          console.warn(
            `[SyncEngine] Partial sync failure: ${response.failedCount}/${response.results.length} operations failed`,
          );
        }

        // If all failed, treat as batch failure
        if (response.syncedCount === 0 && response.failedCount > 0) {
          allSuccess = false;
        }
        // FR-KG-04 fix: Removed else-branch that overwrote per-operation
        // success tracking (lines 200-210) by marking ALL entries as synced.
        // Failed operations now stay in outbox for retry on next poll cycle.
      } catch (err) {
        if (err instanceof SyncNetworkError) {
          console.warn('[SyncEngine] Network error:', err.message);
          allSuccess = false;
        } else if (err instanceof SyncServerError) {
          console.warn('[SyncEngine] Server error:', err.message);
          allSuccess = false;
        } else {
          console.error('[SyncEngine] Unexpected error:', err);
          allSuccess = false;
        }
      }
    }

    return allSuccess;
  }

  /** Periodically poll for new outbox entries. */
  private schedulePoll() {
    if (!this.running) return;
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.processOutbox();
    }, 5000); // Poll every 5s as fallback
  }

  /** Health check to recover from OFFLINE state. */
  private startHealthCheck() {
    if (this.healthCheckTimer) return;
    this.healthCheckTimer = setInterval(async () => {
      try {
        await this.apiClient.checkHealth();
        // Backend is back
        this.consecutiveFailures = 0;
        this.setState('idle');
        if (this.healthCheckTimer) {
          clearInterval(this.healthCheckTimer);
          this.healthCheckTimer = null;
        }
        // Resume processing
        this.processOutbox();
      } catch {
        // Still offline, continue checking
      }
    }, HEALTH_CHECK_INTERVAL_MS);
  }

  /** Clean up synced entries older than 24h (AC-5). */
  private async cleanupOldEntries() {
    const cutoff = new Date(Date.now() - OUTBOX_RETENTION_MS).toISOString();
    try {
      const old = await db.sync_outbox
        .filter((e) => !!e.syncedAt && e.syncedAt < cutoff)
        .toArray();
      if (old.length > 0) {
        const ids = old.map((e) => e.id!).filter(Boolean);
        await db.sync_outbox.bulkDelete(ids);
      }
    } catch {
      // Non-critical cleanup failure
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /** Get current state. */
  getState(): SyncState {
    return this.state;
  }

  /** Get pending operation count. */
  getPendingCount(): number {
    return this.pendingCount;
  }
}
