/**
 * Canvas Learning System - Crash Recovery Manager
 * Story 3.11: Crash Recovery (AC-1 through AC-5)
 *
 * Handles automatic recovery when the Claude Code CLI process crashes
 * unexpectedly. Implements:
 * - lastSentMessage caching (memory + JSON file persistence)
 * - Auto-restart with --resume + message resend (limit 1 retry)
 * - Circuit breaker (3 crashes in 5-min window → stop auto-retry)
 *
 * Reference: Claudian (YishenTu/claudian) crash recovery pattern
 *
 * [Source: _bmad-output/implementation-artifacts/3-11-crash-recovery.md]
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Cached message that was sent to the engine before a crash occurred.
 */
export interface CachedMessage {
  nodeId: string;
  message: string;
  sessionId: string | null;
  timestamp: string;
}

/**
 * Recovery status communicated to the UI (Story 3.11 AC-3, AC-4, AC-5).
 */
export type RecoveryStatus =
  | 'idle'
  | 'recovering'
  | 'failed'
  | 'circuit_open';

/**
 * Callback interface for CrashRecoveryManager to interact with the engine layer.
 */
export interface CrashRecoveryCallbacks {
  /**
   * Restart the engine process and resend the cached message.
   * Returns true if the restart + resend succeeded.
   */
  restartAndResend: (
    nodeId: string,
    message: string,
    sessionId: string | null,
  ) => Promise<boolean>;

  /**
   * Called when recovery status changes (for UI updates).
   */
  onStatusChange: (status: RecoveryStatus) => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Persistence Types
// ═══════════════════════════════════════════════════════════════════════════════

interface CrashRecoveryData {
  version: 1;
  lastSentMessage: CachedMessage | null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Number of crashes within the window that triggers the circuit breaker. */
const CIRCUIT_BREAKER_THRESHOLD = 3;

/** Sliding window duration for crash counting (5 minutes). */
const CIRCUIT_BREAKER_WINDOW_MS = 5 * 60 * 1000;

/** Duration to keep the circuit breaker open (5 minutes). */
const CIRCUIT_BREAKER_COOLDOWN_MS = 5 * 60 * 1000;

// ═══════════════════════════════════════════════════════════════════════════════
// CrashRecoveryManager
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manages crash recovery for the Claude Code CLI engine.
 *
 * Story 3.11 AC-2: Caches the last sent message before each send.
 * Story 3.11 AC-3: On crash, auto-restarts and resends (limit 1 retry).
 * Story 3.11 AC-4: After retry failure, shows manual retry button.
 * Story 3.11 AC-5: Circuit breaker stops auto-retry after 3 crashes in 5 min.
 */
export class CrashRecoveryManager {
  private lastSentMessage: CachedMessage | null = null;
  private hasRetried = false;
  private crashTimestamps: number[] = [];
  private circuitOpen = false;
  private circuitResetTimer: ReturnType<typeof setTimeout> | null = null;
  private filePath: string;
  private callbacks: CrashRecoveryCallbacks;
  private status: RecoveryStatus = 'idle';

  /**
   * Create a CrashRecoveryManager.
   *
   * @param pluginDataDir - Plugin data directory for persistent storage.
   * @param callbacks - Callbacks for engine interaction and UI updates.
   */
  constructor(pluginDataDir: string, callbacks: CrashRecoveryCallbacks) {
    this.filePath = join(pluginDataDir, 'crash-recovery.json');
    this.callbacks = callbacks;

    // Load any persisted lastSentMessage (from a previous plugin crash)
    this.loadPersistedMessage();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Public API
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Cache a message before sending it to the engine.
   *
   * Story 3.11 AC-2: Called before each sendMessage to ensure
   * the message is recoverable if the process crashes.
   *
   * @param nodeId - The canvas node identifier.
   * @param message - The user's message text.
   * @param sessionId - The current session ID (for --resume on restart).
   */
  cacheMessage(nodeId: string, message: string, sessionId: string | null): void {
    this.lastSentMessage = {
      nodeId,
      message,
      sessionId,
      timestamp: new Date().toISOString(),
    };
    this.hasRetried = false;
    this.persist();
  }

  /**
   * Clear the cached message after successful completion.
   *
   * Story 3.11 AC-2: Called when the engine process completes normally
   * (exit code 0 / done event received).
   */
  clearMessage(): void {
    this.lastSentMessage = null;
    this.hasRetried = false;
    this.persist();
    this.setStatus('idle');
  }

  /**
   * Get the currently cached message.
   */
  getLastMessage(): CachedMessage | null {
    return this.lastSentMessage;
  }

  /**
   * Get the current recovery status.
   */
  getStatus(): RecoveryStatus {
    return this.status;
  }

  /**
   * Whether the circuit breaker is currently open.
   */
  isCircuitOpen(): boolean {
    return this.circuitOpen;
  }

  /**
   * Handle a process crash.
   *
   * Story 3.11 AC-1: Called when ClaudeCodeEngine detects an abnormal exit.
   * Orchestrates the recovery flow: retry / manual retry / circuit breaker.
   *
   * @param exitCode - The process exit code (for logging).
   * @param stderr - The stderr output (for logging).
   */
  async handleCrash(exitCode: number | null, stderr: string): Promise<void> {
    console.error(
      `[Canvas Learning] Crash detected: exit=${exitCode}, stderr="${stderr.slice(0, 200)}"`,
    );

    // Record crash timestamp for circuit breaker
    this.recordCrash();

    // Check circuit breaker
    if (this.circuitOpen) {
      this.setStatus('circuit_open');
      return;
    }

    // Check if we have a message to retry
    if (!this.lastSentMessage) {
      // No message to retry — just show error
      this.setStatus('failed');
      return;
    }

    // Check retry limit (1 automatic retry only)
    if (this.hasRetried) {
      this.setStatus('failed');
      return;
    }

    // Attempt automatic recovery
    this.hasRetried = true;
    this.setStatus('recovering');

    const { nodeId, message, sessionId } = this.lastSentMessage;

    const success = await this.callbacks.restartAndResend(
      nodeId,
      message,
      sessionId,
    );

    if (success) {
      // Recovery succeeded — clear cached message
      this.clearMessage();
    } else {
      // Recovery failed — show manual retry
      this.setStatus('failed');
    }
  }

  /**
   * Manually trigger a retry (from the UI "retry" button).
   *
   * Story 3.11 AC-4: User-initiated retry after automatic retry failed.
   */
  async manualRetry(): Promise<boolean> {
    if (!this.lastSentMessage) {
      return false;
    }

    if (this.circuitOpen) {
      this.setStatus('circuit_open');
      return false;
    }

    this.setStatus('recovering');

    const { nodeId, message, sessionId } = this.lastSentMessage;

    const success = await this.callbacks.restartAndResend(
      nodeId,
      message,
      sessionId,
    );

    if (success) {
      this.clearMessage();
      return true;
    } else {
      this.recordCrash();
      this.setStatus(this.circuitOpen ? 'circuit_open' : 'failed');
      return false;
    }
  }

  /**
   * Clean up resources.
   */
  destroy(): void {
    if (this.circuitResetTimer) {
      clearTimeout(this.circuitResetTimer);
      this.circuitResetTimer = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Circuit Breaker
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Record a crash timestamp and check if the circuit breaker should open.
   *
   * Story 3.11 AC-5: 3 crashes within a 5-minute sliding window
   * triggers the circuit breaker.
   */
  private recordCrash(): void {
    const now = Date.now();

    // Add new crash timestamp
    this.crashTimestamps.push(now);

    // Remove timestamps outside the sliding window
    const windowStart = now - CIRCUIT_BREAKER_WINDOW_MS;
    this.crashTimestamps = this.crashTimestamps.filter((t) => t >= windowStart);

    // Check threshold
    if (this.crashTimestamps.length >= CIRCUIT_BREAKER_THRESHOLD) {
      this.openCircuit();
    }
  }

  /**
   * Open the circuit breaker — stop all automatic retries.
   *
   * Story 3.11 AC-5: Circuit breaker auto-resets after 5 minutes.
   */
  private openCircuit(): void {
    this.circuitOpen = true;
    this.setStatus('circuit_open');

    console.warn(
      `[Canvas Learning] Circuit breaker opened: ${this.crashTimestamps.length} crashes in ${CIRCUIT_BREAKER_WINDOW_MS / 1000}s window`,
    );

    // Auto-reset after cooldown period
    if (this.circuitResetTimer) {
      clearTimeout(this.circuitResetTimer);
    }

    this.circuitResetTimer = setTimeout(() => {
      this.circuitOpen = false;
      this.crashTimestamps = [];
      this.circuitResetTimer = null;
      this.setStatus('idle');

      console.log('[Canvas Learning] Circuit breaker reset');
    }, CIRCUIT_BREAKER_COOLDOWN_MS);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Status Management
  // ═══════════════════════════════════════════════════════════════════════════

  private setStatus(newStatus: RecoveryStatus): void {
    this.status = newStatus;
    this.callbacks.onStatusChange(newStatus);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Persistence (JSON file, same pattern as SessionStore)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Load persisted lastSentMessage from disk.
   * If a message exists from a previous plugin crash, it can be used
   * for recovery on next startup.
   */
  private loadPersistedMessage(): void {
    if (!existsSync(this.filePath)) {
      return;
    }

    try {
      const raw = readFileSync(this.filePath, 'utf-8');
      const data = JSON.parse(raw) as CrashRecoveryData;

      if (data.version === 1 && data.lastSentMessage) {
        this.lastSentMessage = data.lastSentMessage;
      }
    } catch (err) {
      console.warn(
        '[Canvas Learning] CrashRecovery: failed to load persisted data:',
        err,
      );
    }
  }

  /**
   * Persist the current lastSentMessage to disk.
   */
  private persist(): void {
    try {
      const dir = dirname(this.filePath);
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }

      const data: CrashRecoveryData = {
        version: 1,
        lastSentMessage: this.lastSentMessage,
      };

      writeFileSync(this.filePath, JSON.stringify(data, null, 2), 'utf-8');
    } catch (err) {
      console.error(
        '[Canvas Learning] CrashRecovery: failed to persist:',
        err,
      );
    }
  }
}
