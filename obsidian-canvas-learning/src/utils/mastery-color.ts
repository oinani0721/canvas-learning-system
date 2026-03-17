/**
 * Canvas Learning System - Mastery Color Utility
 * Story 5.2: Node Color Mastery Visualization (AC-1, AC-6)
 *
 * Pure functions for computing mastery status from node data
 * and mapping status to CSS class names.
 *
 * Mastery status priority (highest first):
 *   1. No interaction at all         -> unlearned
 *   2. FSRS review due (p >= 0.4)    -> review  (overrides mastered/learning)
 *   3. Has interaction, no exam      -> learning
 *   4. Exam proficiency null         -> weak
 *   5. Exam proficiency < 0.4        -> weak
 *   6. Exam proficiency >= 0.7       -> mastered
 *   7. 0.4 <= proficiency < 0.7      -> learning (transition zone)
 */

/** The five mastery visual states. */
export type MasteryStatus =
  | 'unlearned'
  | 'learning'
  | 'weak'
  | 'mastered'
  | 'review';

/**
 * Data needed to determine a node's mastery status.
 * All fields come from the backend mastery engine (Story 5.1).
 */
export interface NodeMasteryData {
  /** Combined proficiency = min(p_mastery, R). null when never examined. */
  effectiveProficiency: number | null;
  /** Whether the user has interacted with this node (e.g. opened a conversation). */
  hasInteraction: boolean;
  /** Whether the node has been examined (AutoSCORE graded at least once). */
  hasExamRecord: boolean;
  /** ISO-8601 timestamp of next FSRS review. null if no FSRS card exists. */
  fsrsNextReview: string | null;
}

/**
 * Determine the mastery status for a node.
 * This is a pure function with deterministic output for any given input + current time.
 *
 * @param data - The node's mastery data from the backend.
 * @param now  - Current time (injectable for testing). Defaults to Date.now().
 * @returns The mastery status used to select visual styling.
 */
export function getMasteryStatus(
  data: NodeMasteryData,
  now: number = Date.now(),
): MasteryStatus {
  // 1. No interaction at all → unlearned
  if (!data.hasInteraction && !data.hasExamRecord) {
    return 'unlearned';
  }

  // 2. FSRS review due AND proficiency >= 0.4 → review (overrides mastered/learning)
  if (data.fsrsNextReview !== null) {
    const reviewTime = new Date(data.fsrsNextReview).getTime();
    if (
      reviewTime <= now &&
      data.effectiveProficiency !== null &&
      data.effectiveProficiency >= 0.4
    ) {
      return 'review';
    }
  }

  // 3. Has interaction but no exam → learning
  if (!data.hasExamRecord) {
    return 'learning';
  }

  // Has exam record from here on
  // 4. proficiency is null with exam record → weak
  if (data.effectiveProficiency === null) {
    return 'weak';
  }

  // 5. proficiency < 0.4 → weak
  if (data.effectiveProficiency < 0.4) {
    return 'weak';
  }

  // 6. proficiency >= 0.7 → mastered
  if (data.effectiveProficiency >= 0.7) {
    return 'mastered';
  }

  // 7. 0.4 <= proficiency < 0.7 → learning (transition zone)
  return 'learning';
}

/**
 * Map a mastery status to its CSS class name.
 *
 * @param status - The mastery status.
 * @returns CSS class name with `cl-mastery-` prefix.
 */
export function getMasteryColorClass(status: MasteryStatus): string {
  return `cl-mastery-${status}`;
}

/**
 * Map a mastery status to its border CSS class name.
 *
 * @param status - The mastery status.
 * @returns CSS class name for the node border color.
 */
export function getMasteryBorderClass(status: MasteryStatus): string {
  return `cl-mastery-${status}-border`;
}
