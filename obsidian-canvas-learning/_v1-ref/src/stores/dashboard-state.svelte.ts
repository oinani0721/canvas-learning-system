/**
 * Canvas Learning System - Dashboard State Store
 * Story 5.4: FSRS Review Dashboard (AC-1 through AC-7)
 *
 * Svelte 5 reactive store managing Dashboard tab state, exam sessions,
 * and FSRS review node sorting.
 *
 * Data flow:
 *   Dashboard mounts -> refreshAll()
 *     -> parallel: loadExamSessions() + loadReviewNodes()
 *     -> FSRS sorting (front-end pure computation)
 *     -> $state updates -> Dashboard tabs re-render
 *
 * FSRS sorting algorithm (AC-3):
 *   1. overdue nodes: FSRS due date past, sorted by overdue days DESC
 *   2. due nodes: FSRS due today/soon, sorted by due date ASC
 *   3. weak nodes: proficiency < 0.70, not yet due, sorted by proficiency ASC
 */

import type {
  ExamSession,
  MasteryConceptResponse,
  ReviewNode,
} from '../types/canvas';
import type { ApiClient } from '../services/api-client';

/** Active dashboard tab. */
export type DashboardTab = 'boards' | 'exams' | 'review';

/**
 * Reactive dashboard state manager.
 * Uses Svelte 5 $state rune for fine-grained reactivity.
 */
class DashboardState {
  /** Currently active tab. */
  activeTab = $state<DashboardTab>('boards');

  /** Exam sessions list. */
  examSessions = $state<ExamSession[]>(new Array<ExamSession>());

  /** FSRS-sorted review nodes. */
  reviewNodes = $state<ReviewNode[]>(new Array<ReviewNode>());

  /** Loading state. */
  isLoading = $state<boolean>(false);

  /** Backend offline flag (for degradation). */
  backendOffline = $state<boolean>(false);

  /** Review statistics. */
  overdueCount = $state<number>(0);
  dueCount = $state<number>(0);
  weakCount = $state<number>(0);

  /** API client reference. */
  private apiClient: ApiClient | null = null;

  /**
   * Initialize with an API client reference.
   */
  init(apiClient: ApiClient): void {
    this.apiClient = apiClient;
  }

  /**
   * Switch the active tab.
   */
  setTab(tab: DashboardTab): void {
    this.activeTab = tab;
  }

  /**
   * Load exam sessions from the backend.
   * Sets backendOffline=true on failure.
   */
  async loadExamSessions(): Promise<void> {
    if (!this.apiClient) return;

    try {
      this.examSessions = await this.apiClient.getExamSessions();
      this.backendOffline = false;
    } catch {
      this.backendOffline = true;
      console.warn('[Canvas Learning] Failed to load exam sessions');
    }
  }

  /**
   * Load review nodes from /mastery/batch and apply FSRS sorting.
   * Sets backendOffline=true on failure.
   *
   * FSRS sorting (AC-3):
   *   1. overdue: due date past, by overdue days DESC
   *   2. due: due today, by due date ASC
   *   3. weak: proficiency < 0.70 but not due, by proficiency ASC
   */
  async loadReviewNodes(): Promise<void> {
    if (!this.apiClient) return;

    try {
      const batch = await this.apiClient.getMasteryBatch();
      if (!batch) {
        this.backendOffline = true;
        return;
      }

      this.backendOffline = false;
      const now = Date.now();

      // Categorize concepts into overdue/due/weak
      const overdue: ReviewNode[] = [];
      const due: ReviewNode[] = [];
      const weak: ReviewNode[] = [];

      for (const concept of batch.concepts) {
        const node = this.conceptToReviewNode(concept, now);
        if (!node) continue;

        if (node.freshness === 'overdue') {
          overdue.push(node);
        } else if (node.freshness === 'due') {
          due.push(node);
        } else if (concept.effectiveProficiency < 0.70) {
          node.freshness = 'stale'; // Weak but not FSRS-due
          weak.push(node);
        }
      }

      // Sort each category per AC-3
      overdue.sort((a, b) => (b.overdueDays ?? 0) - (a.overdueDays ?? 0));
      due.sort((a, b) => {
        const aTime = a.dueDate ? new Date(a.dueDate).getTime() : Infinity;
        const bTime = b.dueDate ? new Date(b.dueDate).getTime() : Infinity;
        return aTime - bTime;
      });
      weak.sort((a, b) => a.effectiveProficiency - b.effectiveProficiency);

      // Update stats
      this.overdueCount = overdue.length;
      this.dueCount = due.length;
      this.weakCount = weak.length;

      // Merge: overdue first, then due, then weak
      this.reviewNodes = [...overdue, ...due, ...weak];
    } catch {
      this.backendOffline = true;
      console.warn('[Canvas Learning] Failed to load review nodes');
    }
  }

  /**
   * Convert a mastery concept response to a ReviewNode.
   * Returns null if the concept doesn't qualify for review.
   */
  private conceptToReviewNode(
    concept: MasteryConceptResponse,
    nowMs: number,
  ): ReviewNode | null {
    // Skip concepts with no interactions
    if (concept.interactionCount === 0) return null;

    let freshness: ReviewNode['freshness'] = 'fresh';
    let overdueDays: number | undefined;

    if (concept.fsrsDueDate) {
      const dueTime = new Date(concept.fsrsDueDate).getTime();
      const diffMs = nowMs - dueTime;
      const diffDays = diffMs / (1000 * 60 * 60 * 24);

      if (diffDays > 1) {
        freshness = 'overdue';
        overdueDays = Math.floor(diffDays);
      } else if (diffDays >= 0) {
        freshness = 'due';
      } else {
        freshness = 'fresh';
      }
    } else if (concept.freshness === 'overdue') {
      freshness = 'overdue';
      overdueDays = 1;
    } else if (concept.freshness === 'due') {
      freshness = 'due';
    }

    // Only include if overdue, due, or weak
    if (
      freshness === 'fresh' &&
      concept.effectiveProficiency >= 0.70
    ) {
      return null;
    }

    return {
      conceptId: concept.conceptId,
      name: concept.name,
      boardId: '', // Not available from batch endpoint
      boardName: concept.topic,
      masteryLevel: concept.masteryLevel,
      masteryColor: concept.masteryColor,
      effectiveProficiency: concept.effectiveProficiency,
      freshness,
      lastReviewedAt: concept.lastInteractionTs ?? undefined,
      dueDate: concept.fsrsDueDate ?? undefined,
      overdueDays,
    };
  }

  /**
   * Refresh all Dashboard data in parallel.
   */
  async refreshAll(): Promise<void> {
    this.isLoading = true;
    await Promise.all([this.loadExamSessions(), this.loadReviewNodes()]);
    this.isLoading = false;
  }

  /**
   * Clear all dashboard data.
   */
  clear(): void {
    this.activeTab = 'boards';
    this.examSessions = new Array<ExamSession>();
    this.reviewNodes = new Array<ReviewNode>();
    this.isLoading = false;
    this.backendOffline = false;
    this.overdueCount = 0;
    this.dueCount = 0;
    this.weakCount = 0;
  }
}

/** Singleton dashboard state store. */
export const dashboardState = new DashboardState();
