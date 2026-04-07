/**
 * FR-KG-04 Phase 12 Tasks 12.13-12.15: SyncErrorClass routing in sync-engine.
 *
 * When the backend returns a failed SyncOperationResult, the sync-engine
 * routes the outbox entry into one of three buckets based on errorClass:
 *
 *   VALIDATION_ERROR   → permanentlyFailed=true (never retry)
 *   DEPENDENCY_MISSING → retryPriority=1 (jumps queue next poll)
 *   TRANSIENT_ERROR    → nextRetryAt = now + exponential backoff
 *   undefined (legacy) → falls through to TRANSIENT behavior
 *
 * These tests drive sendBatch() directly with a mocked ApiClient.syncBatch
 * so we can assert the exact db.sync_outbox.update() calls without running
 * the full poll loop.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiClient, type SyncBatchResponse } from '../api-client';
import { SyncEngine } from '../sync-engine';
import type { SyncOutboxEntry } from '../dexie-db';

// Capture every db.sync_outbox.update call so tests can assert the patches.
const updateCalls: Array<{ id: number; patch: Record<string, unknown> }> = [];

vi.mock('../dexie-db', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../dexie-db')>();
  return {
    ...actual,
    db: {
      sync_outbox: {
        update: vi.fn(async (id: number, patch: Record<string, unknown>) => {
          updateCalls.push({ id, patch });
        }),
      },
    },
  };
});

describe('SyncEngine error_class routing (FR-KG-04 Phase 12)', () => {
  let engine: SyncEngine;
  let syncBatchSpy: ReturnType<typeof vi.spyOn>;

  const makeEntry = (
    id: number,
    canvasId = 'board_1',
  ): SyncOutboxEntry => ({
    id,
    entityType: 'node',
    entityId: `entity-${id}`,
    operation: 'create',
    payload: { canvasId, title: 'x' },
    createdAt: '2026-04-07T00:00:00Z',
  });

  const setResponse = (response: SyncBatchResponse) => {
    syncBatchSpy.mockResolvedValueOnce(response);
  };

  beforeEach(() => {
    updateCalls.length = 0;
    const apiClient = new ApiClient('http://localhost:8001', 'k');
    syncBatchSpy = vi.spyOn(apiClient, 'syncBatch');
    engine = new SyncEngine(apiClient);
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('VALIDATION_ERROR marks entry permanentlyFailed=true', async () => {
    const entry = makeEntry(1);
    setResponse({
      results: [
        {
          operationId: '1',
          success: false,
          error: 'bad payload',
          errorClass: 'VALIDATION_ERROR',
        },
      ],
      syncedCount: 0,
      failedCount: 1,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);

    expect(updateCalls).toHaveLength(1);
    const patch = updateCalls[0].patch;
    expect(patch.permanentlyFailed).toBe(true);
    expect(patch.failureClass).toBe('VALIDATION_ERROR');
    expect(patch.lastError).toBe('bad payload');
    expect(patch.nextRetryAt).toBeUndefined();
  });

  it('DEPENDENCY_MISSING sets retryPriority=1 and does NOT set permanentlyFailed', async () => {
    const entry = makeEntry(2);
    setResponse({
      results: [
        {
          operationId: '2',
          success: false,
          error: 'upstream missing',
          errorClass: 'DEPENDENCY_MISSING',
        },
      ],
      syncedCount: 0,
      failedCount: 1,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);

    expect(updateCalls).toHaveLength(1);
    const patch = updateCalls[0].patch;
    expect(patch.retryPriority).toBe(1);
    expect(patch.failureClass).toBe('DEPENDENCY_MISSING');
    expect(patch.permanentlyFailed).toBeUndefined();
    expect(patch.lastError).toBe('upstream missing');
  });

  it('TRANSIENT_ERROR schedules full-jitter backoff via nextRetryAt + retryCount', async () => {
    // audit-2026-04-07/p1-2: TRANSIENT_ERROR now uses real exponential
    // backoff with full jitter — delay is uniform in [0, capMs] where
    // capMs = min(BASE_RETRY_MS * 2^retryCount, 60_000). On the first
    // failure (retryCount=0) capMs is 2000ms, so delay is in [0, 2000].
    // The previous test asserted >= 2000 which was the old broken
    // "always exactly 2s" behavior; the new contract is that delay
    // never exceeds the cap and retryCount is incremented.
    const entry = makeEntry(3);
    setResponse({
      results: [
        {
          operationId: '3',
          success: false,
          error: 'Neo4j transient error',
          errorClass: 'TRANSIENT_ERROR',
        },
      ],
      syncedCount: 0,
      failedCount: 1,
    });

    const before = Date.now();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);
    const after = Date.now();

    expect(updateCalls).toHaveLength(1);
    const patch = updateCalls[0].patch as {
      failureClass?: string;
      nextRetryAt?: string;
      lastError?: string;
      permanentlyFailed?: boolean;
      retryCount?: number;
    };
    expect(patch.failureClass).toBe('TRANSIENT_ERROR');
    expect(patch.permanentlyFailed).toBeUndefined();
    expect(patch.nextRetryAt).toBeDefined();
    // retryCount must be incremented (0 → 1) on the first failure
    expect(patch.retryCount).toBe(1);

    // nextRetryAt should be in [now, now + capMs] where capMs = 2000 for
    // first retry (retryCount was 0). Allow small clock skew on the upper
    // bound (test machine variance).
    const nextMs = new Date(patch.nextRetryAt as string).getTime();
    expect(nextMs - before).toBeGreaterThanOrEqual(0);
    expect(nextMs - after).toBeLessThanOrEqual(2000 + 100);
  });

  it('undefined errorClass (old backend) falls back to TRANSIENT behavior', async () => {
    const entry = makeEntry(4);
    setResponse({
      results: [
        {
          operationId: '4',
          success: false,
          error: 'unknown',
          // errorClass intentionally omitted
        },
      ],
      syncedCount: 0,
      failedCount: 1,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);

    expect(updateCalls).toHaveLength(1);
    const patch = updateCalls[0].patch;
    expect(patch.failureClass).toBe('TRANSIENT_ERROR');
    expect(patch.nextRetryAt).toBeDefined();
    expect(patch.permanentlyFailed).toBeUndefined();
  });

  it('successful op still marks entry as synced (baseline)', async () => {
    const entry = makeEntry(5);
    setResponse({
      results: [{ operationId: '5', success: true }],
      syncedCount: 1,
      failedCount: 0,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);

    expect(updateCalls).toHaveLength(1);
    const patch = updateCalls[0].patch;
    expect(patch.syncedAt).toBeDefined();
    expect(patch.permanentlyFailed).toBeUndefined();
    expect(patch.failureClass).toBeUndefined();
  });

  it('mixed batch: each entry gets its own classification', async () => {
    const entries = [makeEntry(10), makeEntry(11), makeEntry(12), makeEntry(13)];
    setResponse({
      results: [
        { operationId: '10', success: true },
        {
          operationId: '11',
          success: false,
          error: 'bad',
          errorClass: 'VALIDATION_ERROR',
        },
        {
          operationId: '12',
          success: false,
          error: 'up',
          errorClass: 'DEPENDENCY_MISSING',
        },
        {
          operationId: '13',
          success: false,
          error: 'tx',
          errorClass: 'TRANSIENT_ERROR',
        },
      ],
      syncedCount: 1,
      failedCount: 3,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch(entries);

    expect(updateCalls).toHaveLength(4);
    // op 10 succeeded
    expect(updateCalls[0].patch.syncedAt).toBeDefined();
    // op 11 permanent
    expect(updateCalls[1].patch.permanentlyFailed).toBe(true);
    // op 12 priority retry
    expect(updateCalls[2].patch.retryPriority).toBe(1);
    // op 13 backoff
    expect(updateCalls[3].patch.nextRetryAt).toBeDefined();
  });
});
