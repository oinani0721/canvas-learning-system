/**
 * Zustand Mastery Store (Story 5-2 + 5-4)
 *
 * Manages per-node mastery data cached from the backend.
 * Provides reactive state for:
 *   - Node color indicators (Story 5-2)
 *   - Learning profile panel (Story 5-3)
 *   - Dashboard review tab (Story 5-4)
 *
 * Data flow:
 *   Backend /mastery/board/{id} -> loadBoardMastery() -> nodeMasteryMap
 *   Backend WebSocket mastery_update -> updateNodeMastery() -> nodeMasteryMap
 *   Backend /mastery/batch -> loadMasteryBatch() -> batchData (Dashboard)
 */

import { create } from 'zustand';
import type { MasteryConceptResponse, MasteryBatchResponse, ReviewNode } from '../types';
import type { NodeMasteryData } from '../services/mastery-utils';

interface MasteryStore {
  /** Per-node mastery data (keyed by node ID). */
  nodeMasteryMap: Map<string, NodeMasteryData>;

  /** Full batch data from /mastery/batch (for Dashboard). */
  batchConcepts: MasteryConceptResponse[];
  topicSummary: Record<string, { avgProficiency: number; conceptCount: number; examWeight: number }>;

  /** Computed review nodes (sorted by urgency). */
  reviewNodes: ReviewNode[];

  /** Loading state. */
  isLoading: boolean;

  /** Update a single node's mastery data (from WebSocket or API). */
  updateNodeMastery: (nodeId: string, data: Partial<NodeMasteryData>) => void;

  /** Bulk load mastery data for a board. */
  loadBoardMastery: (items: Array<{ nodeId: string } & NodeMasteryData>) => void;

  /** Load batch data and compute review nodes (for Dashboard). */
  loadBatchData: (batch: MasteryBatchResponse) => void;

  /** Mark a node as having interaction (chat opened). */
  markInteraction: (nodeId: string) => void;

  /** Clear all mastery data (e.g. when switching boards). */
  clear: () => void;

  /** Set loading state. */
  setLoading: (loading: boolean) => void;
}

/**
 * Compute sorted review nodes from batch concepts.
 * Sort order: overdue -> due -> weak (proficiency < 0.70)
 */
function computeReviewNodes(concepts: MasteryConceptResponse[]): ReviewNode[] {
  const now = new Date();
  const reviewCandidates: ReviewNode[] = [];

  for (const c of concepts) {
    const isOverdue = c.freshness === 'overdue';
    const isDue = c.freshness === 'due';
    const isWeak = c.effectiveProficiency < 0.70 && c.interactionCount > 0;

    if (!isOverdue && !isDue && !isWeak) continue;

    let overdueDays: number | undefined;
    if (c.fsrsDueDate) {
      const dueDate = new Date(c.fsrsDueDate);
      const diffMs = now.getTime() - dueDate.getTime();
      if (diffMs > 0) {
        overdueDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      }
    }

    reviewCandidates.push({
      conceptId: c.conceptId,
      name: c.name,
      boardId: '', // TODO: fill from board context when available
      boardName: c.topic || '',
      masteryLevel: c.masteryLevel,
      masteryColor: c.masteryColor,
      effectiveProficiency: c.effectiveProficiency,
      freshness: c.freshness as 'fresh' | 'recent' | 'due' | 'overdue',
      lastReviewedAt: c.lastInteractionTs ?? undefined,
      dueDate: c.fsrsDueDate ?? undefined,
      overdueDays,
    });
  }

  // Sort: overdue (by overdue days desc) -> due (by due date asc) -> weak (by proficiency asc)
  return reviewCandidates.sort((a, b) => {
    const aIsOverdue = a.freshness === 'overdue' ? 1 : 0;
    const bIsOverdue = b.freshness === 'overdue' ? 1 : 0;
    if (aIsOverdue !== bIsOverdue) return bIsOverdue - aIsOverdue;

    if (a.freshness === 'overdue' && b.freshness === 'overdue') {
      return (b.overdueDays ?? 0) - (a.overdueDays ?? 0);
    }

    const aIsDue = a.freshness === 'due' ? 1 : 0;
    const bIsDue = b.freshness === 'due' ? 1 : 0;
    if (aIsDue !== bIsDue) return bIsDue - aIsDue;

    if (a.freshness === 'due' && b.freshness === 'due') {
      const aDate = a.dueDate ? new Date(a.dueDate).getTime() : Infinity;
      const bDate = b.dueDate ? new Date(b.dueDate).getTime() : Infinity;
      return aDate - bDate;
    }

    return a.effectiveProficiency - b.effectiveProficiency;
  });
}

export const useMasteryStore = create<MasteryStore>((set, get) => ({
  nodeMasteryMap: new Map(),
  batchConcepts: [],
  topicSummary: {},
  reviewNodes: [],
  isLoading: false,

  updateNodeMastery: (nodeId, data) => {
    const map = new Map(get().nodeMasteryMap);
    const existing = map.get(nodeId) ?? {
      effectiveProficiency: null,
      hasInteraction: false,
      hasExamRecord: false,
      fsrsNextReview: null,
    };
    map.set(nodeId, { ...existing, ...data });
    set({ nodeMasteryMap: map });
  },

  loadBoardMastery: (items) => {
    const map = new Map(get().nodeMasteryMap);
    for (const item of items) {
      map.set(item.nodeId, {
        effectiveProficiency: item.effectiveProficiency,
        hasInteraction: item.hasInteraction,
        hasExamRecord: item.hasExamRecord,
        fsrsNextReview: item.fsrsNextReview,
      });
    }
    set({ nodeMasteryMap: map });
  },

  loadBatchData: (batch) => {
    const reviewNodes = computeReviewNodes(batch.concepts);
    set({
      batchConcepts: batch.concepts,
      topicSummary: batch.topicSummary,
      reviewNodes,
    });
  },

  markInteraction: (nodeId) => {
    const map = new Map(get().nodeMasteryMap);
    const existing = map.get(nodeId) ?? {
      effectiveProficiency: null,
      hasInteraction: false,
      hasExamRecord: false,
      fsrsNextReview: null,
    };
    map.set(nodeId, { ...existing, hasInteraction: true });
    set({ nodeMasteryMap: map });
  },

  clear: () => {
    set({
      nodeMasteryMap: new Map(),
      batchConcepts: [],
      topicSummary: {},
      reviewNodes: [],
    });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },
}));
