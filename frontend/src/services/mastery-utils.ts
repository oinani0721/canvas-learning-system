/**
 * Mastery Utility Functions (Story 5-2)
 *
 * Pure functions for computing mastery status from backend data.
 * These drive node color mapping and profile display.
 */

import type { MasteryStatus } from '../types';

/**
 * Per-node mastery data from the backend /mastery/board/{id} endpoint.
 * Matches the NodeMasteryData interface in api-client.ts.
 */
export interface NodeMasteryData {
  effectiveProficiency: number | null;
  hasInteraction: boolean;
  hasExamRecord: boolean;
  fsrsNextReview: string | null;
}

/**
 * Determine the mastery visual status for a node.
 *
 * Priority order (highest first):
 * 1. No interaction at all -> 'unlearned'
 * 2. FSRS review is due/overdue -> 'review' (overrides other states)
 * 3. Has interaction but no exam record -> 'learning'
 * 4. Has exam record with proficiency < 0.4 -> 'weak'
 * 5. Has exam record with proficiency >= 0.7 -> 'mastered'
 * 6. Has exam record with 0.4 <= proficiency < 0.7 -> 'learning' (transition)
 * 7. Has exam record but null proficiency -> 'weak'
 */
export function getMasteryStatus(data: NodeMasteryData): MasteryStatus {
  const { effectiveProficiency, hasInteraction, hasExamRecord, fsrsNextReview } = data;

  // Rule 1: No interaction at all
  if (!hasInteraction && !hasExamRecord) {
    return 'unlearned';
  }

  // Rule 2: FSRS review is due (overrides other states)
  if (fsrsNextReview) {
    const dueDate = new Date(fsrsNextReview);
    if (dueDate <= new Date()) {
      return 'review';
    }
  }

  // Rule 3: Has interaction but no exam record
  if (!hasExamRecord) {
    return 'learning';
  }

  // Rule 4-7: Has exam record, check proficiency
  if (effectiveProficiency === null || effectiveProficiency === undefined) {
    return 'weak'; // Examined but no proficiency data
  }

  if (effectiveProficiency < 0.4) {
    return 'weak';
  }
  if (effectiveProficiency >= 0.7) {
    return 'mastered';
  }
  return 'learning'; // Transition zone: 0.4 <= p < 0.7
}

/**
 * CSS class for the mastery status (Tailwind border color).
 */
export function getMasteryBorderClass(status: MasteryStatus): string {
  switch (status) {
    case 'unlearned': return 'border-gray-300';
    case 'learning': return 'border-blue-400';
    case 'weak': return 'border-red-400';
    case 'mastered': return 'border-green-500';
    case 'review': return 'border-yellow-400';
  }
}

/**
 * Hex color for the mastery status (for inline styles / progress bars).
 */
export function getMasteryColor(status: MasteryStatus): string {
  switch (status) {
    case 'unlearned': return '#9ca3af'; // gray-400
    case 'learning': return '#60a5fa';  // blue-400
    case 'weak': return '#f87171';      // red-400
    case 'mastered': return '#22c55e';  // green-500
    case 'review': return '#facc15';    // yellow-400
  }
}

/**
 * Human-readable label for the mastery status (Chinese).
 */
export function getMasteryLabel(status: MasteryStatus): string {
  switch (status) {
    case 'unlearned': return '未学习';
    case 'learning': return '学习中';
    case 'weak': return '需加强';
    case 'mastered': return '已掌握';
    case 'review': return '待复习';
  }
}

/**
 * Map backend mastery level (0-4) to MasteryStatus.
 */
/**
 * Map backend mastery level (0-4) to MasteryStatus.
 *
 * Backend levels (from MASTERY_LABELS):
 *   0 = Not Assessed -> unlearned
 *   1 = Shaky        -> weak
 *   2 = Developing   -> learning
 *   3 = Proficient   -> learning  (proficient but NOT yet mastered)
 *   4 = Mastered     -> mastered
 */
export function masteryLevelToStatus(level: number | null): MasteryStatus {
  switch (level) {
    case 0: return 'unlearned';
    case 1: return 'weak';
    case 2: return 'learning';
    case 3: return 'learning';
    case 4: return 'mastered';
    default: return 'unlearned';
  }
}

/**
 * Format a relative date string (e.g. "3 days ago", "tomorrow").
 */
export function formatRelativeDate(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '明天';
  if (diffDays === -1) return '昨天';
  if (diffDays > 1) return `${diffDays} 天后`;
  return `${Math.abs(diffDays)} 天前`;
}
