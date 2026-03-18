/**
 * Canvas Learning System - Crash Recovery Manager
 * Story 3-11: Crash Recovery (process crash -> auto-restart + message replay)
 *
 * Caches the last sent message before each send, so if the CLI process
 * crashes, we can auto-restart and re-send. Includes a circuit breaker
 * that opens after 3 crashes within a 5-minute sliding window.
 *
 * Recovery flow:
 *   Process crash (exit != 0, not auth/rate-limit)
 *     |- circuit breaker open -> show error, no retry
 *     |- has lastSentMessage & not retried -> restart + resume + re-send
 *     |- already retried -> show manual retry button
 *     |- no lastSentMessage -> show error + manual retry
 *
 * Reference: Claudian (YishenTu/claudian) - lastSentMessage caching + auto-restart
 */

import { db } from './dexie-db';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/** Cached message for crash recovery. */
export interface CachedMessage {
  nodeId: string;
  message: string;
  sessionId: string | null;
  timestamp: string;
}

/** Recovery state for UI rendering. */
export type RecoveryStatus =
  | 'idle'           // No crash, normal operation
  | 'recovering'     // Auto-restart in progress
  | 'failed'         // Single retry exhausted, manual retry available
  | 'circuit_open';  // Circuit breaker tripped, no more retries

/** Callback for recovery status changes. */
export type RecoveryStatusCallback = (status: RecoveryStatus, detail?: string) => void;

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Circuit breaker: max crashes within the sliding window before tripping. */
const CIRCUIT_BREAKER_THRESHOLD = 3;

/** Circuit breaker: sliding window duration (ms). */
const CIRCUIT_BREAKER_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

/** Circuit breaker: auto-reset timeout (ms) after tripping. */
const CIRCUIT_BREAKER_RESET_MS = 5 * 60 * 1000; // 5 minutes

// ═══════════════════════════════════════════════════════════════════════════════
// CrashRecoveryManager
// ═══════════════════════════════════════════════════════════════════════════════

export class CrashRecoveryManager {
  /** In-memory cached last sent message (also persisted to Dexie). */
  private lastSentMessage: CachedMessage | null = null;

  /** Whether the current lastSentMessage has already been retried. */
  private retried = false;

  /** Timestamps of recent crashes for circuit breaker. */
  private crashTimestamps: number[] = [];

  /** Whether the circuit breaker is open (tripped). */
  private _circuitOpen = false;

  /** Timer for auto-resetting the circuit breaker. */
  private circuitResetTimer: ReturnType<typeof setTimeout> | null = null;

  /** Current recovery status. */
  private _status: RecoveryStatus = 'idle';

  /** Callbacks for status changes. */
  private statusCallbacks: RecoveryStatusCallback[] = [];

  constructor() {
    // Load any persisted lastSentMessage from a previous session/crash
    this.loadFromDexie();
  }

  /** Get the current recovery status. */
  get status(): RecoveryStatus {
    return this._status;
  }

  /** Whether the circuit breaker is currently open. */
  get circuitOpen(): boolean {
    return this._circuitOpen;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Message Caching (AC-2)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Cache a message before sending it to the engine.
   * Called by the chat store before each engine.sendMessage().
   */
  async cacheMessage(nodeId: string, message: string, sessionId: string | null): Promise<void> {
    this.lastSentMessage = {
      nodeId,
      message,
      sessionId,
      timestamp: new Date().toISOString(),
    };
    this.retried = false;

    // Persist to Dexie for cross-crash recovery
    await this.saveToDexie(this.lastSentMessage);
  }

  /**
   * Clear the cached message on successful completion.
   * Called when the engine emits a 'done' event.
   */
  async clearMessage(): Promise<void> {
    this.lastSentMessage = null;
    this.retried = false;
    await this.clearDexie();
    this.setStatus('idle');
  }

  /**
   * Get the cached last sent message (for retry after crash).
   */
  getLastMessage(): CachedMessage | null {
    return this.lastSentMessage;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Crash Handling (AC-1, AC-3, AC-4)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Record a crash event and determine recovery action.
   *
   * @param exitCode - The process exit code.
   * @param stderr - Captured stderr output.
   * @returns Recovery action to take.
   */
  recordCrash(exitCode: number | null, stderr: string): {
    action: 'auto_retry' | 'manual_retry' | 'circuit_open';
    lastMessage: CachedMessage | null;
  } {
    // Record crash timestamp for circuit breaker
    const now = Date.now();
    this.crashTimestamps.push(now);

    // Prune old timestamps outside the sliding window
    this.crashTimestamps = this.crashTimestamps.filter(
      (ts) => now - ts < CIRCUIT_BREAKER_WINDOW_MS,
    );

    console.warn(
      `[CrashRecovery] Crash recorded (exit code: ${exitCode}, crashes in window: ${this.crashTimestamps.length}/${CIRCUIT_BREAKER_THRESHOLD})`,
      stderr.slice(0, 200),
    );

    // Check circuit breaker (AC-5)
    if (this.crashTimestamps.length >= CIRCUIT_BREAKER_THRESHOLD) {
      this.tripCircuitBreaker();
      return { action: 'circuit_open', lastMessage: null };
    }

    // Check if we have a message to retry (AC-3)
    if (this.lastSentMessage && !this.retried) {
      this.retried = true;
      this.setStatus('recovering');
      return { action: 'auto_retry', lastMessage: this.lastSentMessage };
    }

    // Already retried or no message to retry (AC-4)
    this.setStatus('failed');
    return { action: 'manual_retry', lastMessage: this.lastSentMessage };
  }

  /**
   * Manual retry requested by user.
   * Returns the cached message if available, or null.
   */
  manualRetry(): CachedMessage | null {
    if (this._circuitOpen) {
      return null; // Circuit breaker still open
    }

    if (this.lastSentMessage) {
      this.retried = false; // Allow one more auto-retry on next crash
      this.setStatus('recovering');
      return this.lastSentMessage;
    }

    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Circuit Breaker (AC-5)
  // ═══════════════════════════════════════════════════════════════════════════

  private tripCircuitBreaker(): void {
    this._circuitOpen = true;
    this.setStatus('circuit_open');

    console.warn(
      `[CrashRecovery] Circuit breaker OPEN — ${CIRCUIT_BREAKER_THRESHOLD} crashes within ${CIRCUIT_BREAKER_WINDOW_MS / 1000}s. Auto-reset in ${CIRCUIT_BREAKER_RESET_MS / 1000}s.`,
    );

    // Schedule auto-reset
    if (this.circuitResetTimer) {
      clearTimeout(this.circuitResetTimer);
    }
    this.circuitResetTimer = setTimeout(() => {
      this.resetCircuitBreaker();
    }, CIRCUIT_BREAKER_RESET_MS);
  }

  private resetCircuitBreaker(): void {
    this._circuitOpen = false;
    this.crashTimestamps = [];
    this.circuitResetTimer = null;
    this.setStatus('idle');
    console.info('[CrashRecovery] Circuit breaker RESET — retries allowed again.');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Status Callbacks
  // ═══════════════════════════════════════════════════════════════════════════

  onStatusChange(callback: RecoveryStatusCallback): void {
    this.statusCallbacks.push(callback);
  }

  offStatusChange(callback: RecoveryStatusCallback): void {
    this.statusCallbacks = this.statusCallbacks.filter((cb) => cb !== callback);
  }

  private setStatus(status: RecoveryStatus, detail?: string): void {
    this._status = status;
    for (const cb of this.statusCallbacks) {
      try {
        cb(status, detail);
      } catch (e) {
        console.error('[CrashRecovery] Error in status callback:', e);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Dexie Persistence
  // ═══════════════════════════════════════════════════════════════════════════

  private async saveToDexie(msg: CachedMessage): Promise<void> {
    try {
      await db.crash_recovery.put({
        id: 'last_sent',
        nodeId: msg.nodeId,
        message: msg.message,
        sessionId: msg.sessionId,
        timestamp: msg.timestamp,
      });
    } catch {
      // Dexie table might not exist yet (schema migration) — use localStorage fallback
      try {
        localStorage.setItem(
          'canvas-learning:crash-recovery',
          JSON.stringify(msg),
        );
      } catch {
        // Silent fail
      }
    }
  }

  private async clearDexie(): Promise<void> {
    try {
      await db.crash_recovery.delete('last_sent');
    } catch {
      // Fallback
    }
    try {
      localStorage.removeItem('canvas-learning:crash-recovery');
    } catch {
      // Silent fail
    }
  }

  private async loadFromDexie(): Promise<void> {
    try {
      const entry = await db.crash_recovery.get('last_sent');
      if (entry) {
        this.lastSentMessage = {
          nodeId: entry.nodeId,
          message: entry.message,
          sessionId: entry.sessionId,
          timestamp: entry.timestamp,
        };
        return;
      }
    } catch {
      // Fallback to localStorage
    }

    try {
      const stored = localStorage.getItem('canvas-learning:crash-recovery');
      if (stored) {
        this.lastSentMessage = JSON.parse(stored) as CachedMessage;
      }
    } catch {
      // Silent fail
    }
  }

  /** Clean up timers on destroy. */
  destroy(): void {
    if (this.circuitResetTimer) {
      clearTimeout(this.circuitResetTimer);
      this.circuitResetTimer = null;
    }
    this.statusCallbacks = [];
  }
}
