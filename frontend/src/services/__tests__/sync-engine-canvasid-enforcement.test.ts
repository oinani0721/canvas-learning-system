/**
 * FR-KG-04 Phase 14 Tasks 14.4, 14.5: canvasId enforcement in sync-engine.
 *
 * The previous sync-engine fell back to the literal string 'default' when
 * an outbox entry was missing both payload.canvasId and payload.canvas_id.
 * Wave 1 fixed the upstream canvas-store bug that sometimes produced
 * orphaned entries, so this fallback no longer has legitimate triggers.
 * It now actively hides bugs.
 *
 * These tests verify that:
 *   1. An entry with no canvasId is skipped (not sent to the backend)
 *   2. A warning is logged identifying the entry id
 *   3. Entries with a valid canvasId are processed normally (regression)
 *   4. snake_case canvas_id is still accepted for backwards compatibility
 *   5. The literal string 'default' is never sent as canvasId
 *
 * The test invokes the private sendBatch method directly via `as any` so
 * we do not need to wire up the full polling loop.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiClient } from '../api-client';
import { SyncEngine } from '../sync-engine';
import type { SyncOutboxEntry } from '../dexie-db';

// Mock the dexie-db module: sync_outbox.update is a no-op spy so the
// orphan-skip branch does not try to persist anything.
vi.mock('../dexie-db', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../dexie-db')>();
  return {
    ...actual,
    db: {
      sync_outbox: {
        update: vi.fn(async () => {}),
      },
    },
  };
});

describe('SyncEngine canvasId enforcement (FR-KG-04 Phase 14)', () => {
  let engine: SyncEngine;
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let syncBatchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    const apiClient = new ApiClient('http://localhost:8001', 'test-key');
    syncBatchSpy = vi.spyOn(apiClient, 'syncBatch').mockResolvedValue({
      results: [],
      syncedCount: 0,
      failedCount: 0,
    });
    engine = new SyncEngine(apiClient);
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const makeEntry = (
    id: number,
    payload: Record<string, unknown>,
    entityType: 'node' | 'edge' | 'board' = 'node',
  ): SyncOutboxEntry => ({
    id,
    entityType,
    entityId: `entity-${id}`,
    operation: 'create',
    payload,
    createdAt: '2026-04-07T00:00:00Z',
  });

  it('skips orphan entries with no canvasId and never calls syncBatch', async () => {
    const orphan = makeEntry(1, {
      title: 'orphaned node',
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result = await (engine as any).sendBatch([orphan]);

    // Backend never called because every entry was skipped
    expect(syncBatchSpy).not.toHaveBeenCalled();
    // sendBatch treats an empty grouped map as a no-op success
    expect(result).toBe(true);

    // Warning was logged with the entry id
    expect(warnSpy).toHaveBeenCalled();
    const warnCall = warnSpy.mock.calls[0];
    expect(warnCall[0]).toContain('Outbox entry missing canvasId');
    expect(warnCall[1]).toBe(1);
  });

  it('skips orphans but still sends entries that have a canvasId', async () => {
    const orphan = makeEntry(1, { title: 'no canvasId' });
    const validEntry = makeEntry(2, {
      canvasId: 'board_42',
      title: 'valid',
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([orphan, validEntry]);

    expect(syncBatchSpy).toHaveBeenCalledTimes(1);
    const sentRequest = syncBatchSpy.mock.calls[0][0];
    expect(sentRequest.canvasId).toBe('board_42');
    expect(sentRequest.operations).toHaveLength(1);
    expect(sentRequest.operations[0].entityId).toBe('entity-2');

    expect(warnSpy).toHaveBeenCalled();
  });

  it('accepts snake_case canvas_id payload key for backwards compatibility', async () => {
    const entry = makeEntry(3, {
      canvas_id: 'legacy_board',
      title: 'legacy',
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([entry]);

    expect(syncBatchSpy).toHaveBeenCalledTimes(1);
    const sentRequest = syncBatchSpy.mock.calls[0][0];
    expect(sentRequest.canvasId).toBe('legacy_board');
    expect(warnSpy).not.toHaveBeenCalled();
  });

  it('NEVER sends the literal "default" canvasId (regression guard)', async () => {
    const orphan = makeEntry(4, {});

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (engine as any).sendBatch([orphan]);

    expect(syncBatchSpy).not.toHaveBeenCalled();
    for (const call of syncBatchSpy.mock.calls) {
      expect(call[0].canvasId).not.toBe('default');
    }
  });
});
