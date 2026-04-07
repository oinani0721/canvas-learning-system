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

  /** Main sync loop: consume outbox entries in batches.
   *
   * FR-KG-04 Phase 12 Tasks 12.11-12.12: pending queue is now sensitive to
   * the failure-tracking fields added in schema v6:
   *   - permanentlyFailed=true entries are skipped entirely (no poll will
   *     ever touch them again; the user must explicitly clear them)
   *   - entries with nextRetryAt in the future are skipped this cycle
   *   - remaining entries are sorted by retryPriority DESC so
   *     DEPENDENCY_MISSING retries jump the queue ahead of normal entries
   */
  private async processOutbox() {
    if (this.state === 'syncing') return;
    if (this.state === 'offline') return;

    // Collect all pending entries (not yet synced, not permanently failed).
    // Dexie's filter() runs in JavaScript, which is fine for outbox sizes
    // we expect (hundreds, not millions) and lets us use the full type-safe
    // predicate API.
    const nowIso = new Date().toISOString();
    const allPending: SyncOutboxEntry[] = await db.sync_outbox
      .filter((entry) => {
        if (entry.syncedAt) return false;
        if (entry.permanentlyFailed === true) return false;
        if (entry.nextRetryAt && entry.nextRetryAt > nowIso) return false;
        return true;
      })
      .toArray();

    // Sort by retryPriority DESC (1 → 0), then by createdAt ASC so older
    // entries go first. DEPENDENCY_MISSING entries get retryPriority=1 and
    // therefore jump ahead of normal (priority=0 or undefined) entries.
    allPending.sort((a, b) => {
      const priA = a.retryPriority ?? 0;
      const priB = b.retryPriority ?? 0;
      if (priA !== priB) return priB - priA;
      return a.createdAt.localeCompare(b.createdAt);
    });

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
        // FR-KG-04 Phase 12 Tasks 12.7-12.10: per-op error_class routing.
        //
        // Walk every result and update the matching outbox entry based on
        // the backend's SyncErrorClass verdict:
        //   success              → mark synced
        //   VALIDATION_ERROR     → permanentlyFailed=true, never retry
        //   DEPENDENCY_MISSING   → retryPriority=1, jumps the queue
        //   TRANSIENT_ERROR      → exponentialBackoff(retryCount)
        //   undefined (old API)  → fall through to TRANSIENT behavior
        const syncedAt = new Date().toISOString();
        // Index groupEntries by their outbox id for O(1) lookup
        const entryById = new Map<string, (typeof groupEntries)[0]>();
        for (const entry of groupEntries) {
          const opId = entry.id?.toString() ?? '';
          if (opId) entryById.set(opId, entry);
        }

        for (const result of response.results) {
          const entry = entryById.get(result.operationId);
          if (!entry || entry.id == null) continue;

          if (result.success) {
            await db.sync_outbox.update(entry.id, { syncedAt });
            continue;
          }

          const errorClass = result.errorClass ?? 'TRANSIENT_ERROR';
          const lastError = (result.error ?? '').slice(0, 200);

          switch (errorClass) {
            case 'VALIDATION_ERROR':
              // Payload itself is wrong — retrying is a dead-end waste of
              // round-trips and will never change outcome. Mark permanent.
              await db.sync_outbox.update(entry.id, {
                permanentlyFailed: true,
                failureClass: 'VALIDATION_ERROR',
                lastError,
              });
              break;

            case 'DEPENDENCY_MISSING':
              // Upstream entity (node/board) hasn't synced yet — bump the
              // priority so this entry gets retried first in the next poll.
              // Do NOT set permanentlyFailed: the retry might succeed once
              // the upstream catches up.
              await db.sync_outbox.update(entry.id, {
                failureClass: 'DEPENDENCY_MISSING',
                retryPriority: 1,
                lastError,
              });
              break;

            case 'TRANSIENT_ERROR':
            default: {
              // Neo4j driver hiccup or similar — exponential backoff.
              // We approximate retryCount from how many times this entry
              // has been seen with a nextRetryAt already set (stored on
              // the row itself). The backoff base is 2s, doubling.
              const currentRetries = entry.nextRetryAt ? 1 : 0;
              const delayMs =
                BASE_RETRY_MS * Math.pow(2, currentRetries);
              const nextRetryAt = new Date(
                Date.now() + delayMs,
              ).toISOString();
              await db.sync_outbox.update(entry.id, {
                failureClass: 'TRANSIENT_ERROR',
                nextRetryAt,
                lastError,
              });
              break;
            }
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
