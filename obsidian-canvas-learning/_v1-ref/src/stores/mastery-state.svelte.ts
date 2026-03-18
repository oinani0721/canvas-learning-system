/**
 * Canvas Learning System - Mastery State Store
 * Story 5.2: Node Color Mastery Visualization (AC-2, AC-6)
 *
 * Svelte 5 reactive store managing front-end mastery data cache.
 * Authoritative data lives in the backend Neo4j (Layer 0 principle).
 *
 * Data flow:
 *   Backend EventBus BKT_UPDATED
 *     -> WebSocket mastery_update
 *     -> masteryState.updateNodeMastery()
 *     -> Svelte $state reactivity
 *     -> NodeColorIndicator re-renders
 */

import {
  getMasteryStatus,
  type MasteryStatus,
  type NodeMasteryData,
} from '../utils/mastery-color';

/**
 * Reactive mastery state manager.
 * Uses Svelte 5 `$state` rune for fine-grained reactivity.
 */
class MasteryState {
  /** Map of nodeId -> mastery data. Reassigned (not mutated) to trigger reactivity. */
  nodeMasteryMap = $state<Map<string, NodeMasteryData>>(new Map());

  /**
   * Update a single node's mastery data.
   * Called when a WebSocket `mastery_update` message arrives.
   * Creates a new Map to trigger Svelte reactivity.
   *
   * @param nodeId - The canvas node identifier.
   * @param data   - Partial mastery data to merge with existing state.
   */
  updateNodeMastery(nodeId: string, data: Partial<NodeMasteryData>): void {
    const current = this.nodeMasteryMap.get(nodeId);
    const merged: NodeMasteryData = {
      effectiveProficiency: null,
      hasInteraction: false,
      hasExamRecord: false,
      fsrsNextReview: null,
      ...current,
      ...data,
    };
    const next = new Map(this.nodeMasteryMap);
    next.set(nodeId, merged);
    this.nodeMasteryMap = next;
  }

  /**
   * Batch-load mastery data for an entire board.
   * Called when a canvas board is opened / switched to.
   * Replaces the entire map to avoid stale data from a previous board.
   *
   * @param entries - Array of [nodeId, data] tuples from the backend.
   */
  loadBoardMastery(
    entries: Array<{ nodeId: string } & NodeMasteryData>,
  ): void {
    const next = new Map<string, NodeMasteryData>();
    for (const entry of entries) {
      const { nodeId, ...data } = entry;
      next.set(nodeId, data);
    }
    this.nodeMasteryMap = next;
  }

  /**
   * Get the computed mastery status for a node.
   * Returns 'unlearned' when the node has no mastery data.
   *
   * @param nodeId - The canvas node identifier.
   * @returns The mastery status used for color mapping.
   */
  getNodeStatus(nodeId: string): MasteryStatus {
    const data = this.nodeMasteryMap.get(nodeId);
    if (!data) {
      return 'unlearned';
    }
    return getMasteryStatus(data);
  }

  /**
   * Mark a node as having user interaction (e.g. conversation started).
   * If the node has no existing mastery data, creates a default entry.
   *
   * @param nodeId - The canvas node identifier.
   */
  markInteraction(nodeId: string): void {
    const current = this.nodeMasteryMap.get(nodeId);
    const merged: NodeMasteryData = {
      effectiveProficiency: null,
      hasInteraction: true,
      hasExamRecord: current?.hasExamRecord ?? false,
      fsrsNextReview: current?.fsrsNextReview ?? null,
      ...(current?.effectiveProficiency !== undefined
        ? { effectiveProficiency: current.effectiveProficiency }
        : {}),
    };
    const next = new Map(this.nodeMasteryMap);
    next.set(nodeId, merged);
    this.nodeMasteryMap = next;
  }

  /**
   * Clear all mastery data.
   * Called when navigating away from a board or during cleanup.
   */
  clear(): void {
    this.nodeMasteryMap = new Map();
  }
}

/** Singleton mastery state store. */
export const masteryState = new MasteryState();

// Re-export types for consumer convenience
export type { NodeMasteryData, MasteryStatus };
