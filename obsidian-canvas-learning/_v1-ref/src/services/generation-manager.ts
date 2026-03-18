/**
 * Canvas Learning System - Generation Manager
 * Story 3.8: Async Background Generation Management (AC-3, AC-5)
 *
 * Manages concurrent AI generation processes across multiple nodes.
 * When a user switches away from a node mid-generation, the generation
 * continues in the background. Enforces a concurrency limit of 3.
 *
 * Status tracking:
 *   - generating: AI is actively generating a response
 *   - unread: Generation completed but user hasn't viewed it
 *   - idle: No active generation (default)
 *
 * [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 4]
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export type GenerationStatus = 'generating' | 'unread' | 'idle';

export interface PendingGeneration {
  nodeId: string;
  message: string;
  enqueuedAt: number;
}

export interface GenerationInfo {
  nodeId: string;
  startedAt: number;
  abortController: AbortController;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Maximum concurrent AI generation processes. */
const MAX_CONCURRENT = 3;

// ═══════════════════════════════════════════════════════════════════════════════
// Generation Manager
// ═══════════════════════════════════════════════════════════════════════════════

export class GenerationManager {
  /** Active generation processes. */
  private active: Map<string, GenerationInfo> = new Map();

  /** Queued generation requests waiting for a slot. */
  private queue: PendingGeneration[] = [];

  /** Per-node generation status. */
  private statusMap: Map<string, GenerationStatus> = new Map();

  /** Listeners for status changes. */
  private listeners: Set<(nodeId: string, status: GenerationStatus) => void> = new Set();

  // ═══════════════════════════════════════════════════════════════════════════
  // Public API
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Start a generation for a node.
   *
   * Story 3.8 AC-3: If under MAX_CONCURRENT, starts immediately.
   * Story 3.8 AC-5: If at limit, queues the request.
   *
   * @param nodeId - The node requesting generation.
   * @param message - The user message to send.
   * @param executor - Async function that performs the actual generation.
   * @returns Position in queue (0 = started immediately, 1+ = queued position).
   */
  async startGeneration(
    nodeId: string,
    message: string,
    executor: (nodeId: string, message: string, signal: AbortSignal) => Promise<void>,
  ): Promise<number> {
    // If already generating for this node, skip
    if (this.active.has(nodeId)) {
      return 0;
    }

    if (this.active.size < MAX_CONCURRENT) {
      // Slot available: start immediately
      await this._executeGeneration(nodeId, message, executor);
      return 0;
    } else {
      // Queue the request
      this.queue.push({
        nodeId,
        message,
        enqueuedAt: Date.now(),
      });
      this._setStatus(nodeId, 'generating');
      return this.queue.length;
    }
  }

  /**
   * Mark a node as "read" (user viewed the completed generation).
   *
   * Story 3.8 AC-4: unread -> idle when user switches to the node.
   *
   * @param nodeId - The node to mark as read.
   */
  markAsRead(nodeId: string): void {
    if (this.getStatus(nodeId) === 'unread') {
      this._setStatus(nodeId, 'idle');
    }
  }

  /**
   * Get the current generation status for a node.
   *
   * @param nodeId - The node to query.
   * @returns GenerationStatus.
   */
  getStatus(nodeId: string): GenerationStatus {
    return this.statusMap.get(nodeId) ?? 'idle';
  }

  /**
   * Get all node statuses (for UI rendering).
   *
   * @returns Map of nodeId -> GenerationStatus.
   */
  getAllStatuses(): Map<string, GenerationStatus> {
    return new Map(this.statusMap);
  }

  /**
   * Get the number of active generations.
   */
  get activeCount(): number {
    return this.active.size;
  }

  /**
   * Get the number of queued generations.
   */
  get queuedCount(): number {
    return this.queue.length;
  }

  /**
   * Subscribe to status changes.
   *
   * @param listener - Callback for status changes.
   * @returns Unsubscribe function.
   */
  onStatusChange(
    listener: (nodeId: string, status: GenerationStatus) => void,
  ): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Get queue position for a node (0 = not queued).
   *
   * @param nodeId - The node to check.
   * @returns Queue position (1-based) or 0 if not queued.
   */
  getQueuePosition(nodeId: string): number {
    const idx = this.queue.findIndex((p) => p.nodeId === nodeId);
    return idx >= 0 ? idx + 1 : 0;
  }

  /**
   * Clean up all active generations and queued requests.
   * Called during plugin unload.
   */
  async cleanup(): Promise<void> {
    // Abort all active generations
    for (const [nodeId, info] of this.active.entries()) {
      info.abortController.abort();
    }
    this.active.clear();
    this.queue.length = 0;
    this.statusMap.clear();
    this.listeners.clear();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal
  // ═══════════════════════════════════════════════════════════════════════════

  private async _executeGeneration(
    nodeId: string,
    message: string,
    executor: (nodeId: string, message: string, signal: AbortSignal) => Promise<void>,
  ): Promise<void> {
    const abortController = new AbortController();

    const info: GenerationInfo = {
      nodeId,
      startedAt: Date.now(),
      abortController,
    };

    this.active.set(nodeId, info);
    this._setStatus(nodeId, 'generating');

    // Run generation in background (non-blocking)
    this._runInBackground(nodeId, message, executor, abortController.signal);
  }

  private async _runInBackground(
    nodeId: string,
    message: string,
    executor: (nodeId: string, message: string, signal: AbortSignal) => Promise<void>,
    signal: AbortSignal,
  ): Promise<void> {
    try {
      await executor(nodeId, message, signal);
      // Generation completed successfully
      this._setStatus(nodeId, 'unread');
    } catch (err) {
      if (signal.aborted) {
        // Intentionally aborted - set to idle
        this._setStatus(nodeId, 'idle');
      } else {
        console.warn(`[Canvas Learning] Generation failed for node ${nodeId}:`, err);
        this._setStatus(nodeId, 'idle');
      }
    } finally {
      this.active.delete(nodeId);
      this._processQueue(executor);
    }
  }

  private async _processQueue(
    executor: (nodeId: string, message: string, signal: AbortSignal) => Promise<void>,
  ): Promise<void> {
    // Process queued requests if slots are available
    while (this.queue.length > 0 && this.active.size < MAX_CONCURRENT) {
      const next = this.queue.shift();
      if (next) {
        await this._executeGeneration(next.nodeId, next.message, executor);
      }
    }
  }

  private _setStatus(nodeId: string, status: GenerationStatus): void {
    const prev = this.statusMap.get(nodeId);
    if (prev === status) return;

    if (status === 'idle') {
      this.statusMap.delete(nodeId);
    } else {
      this.statusMap.set(nodeId, status);
    }

    // Notify listeners
    for (const listener of this.listeners) {
      try {
        listener(nodeId, status);
      } catch (err) {
        console.warn('[Canvas Learning] Status listener error:', err);
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Singleton
// ═══════════════════════════════════════════════════════════════════════════════

let _instance: GenerationManager | null = null;

export function getGenerationManager(): GenerationManager {
  if (!_instance) {
    _instance = new GenerationManager();
  }
  return _instance;
}
