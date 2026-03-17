/**
 * Canvas Learning System - Mastery Color Tests
 * Story 5.2: Unit tests for getMasteryStatus (AC-1, Task 2.3)
 *
 * Covers all branches of the mastery status decision tree:
 *   - unlearned (no interaction)
 *   - learning (interaction, no exam)
 *   - weak (low proficiency or null proficiency with exam)
 *   - mastered (high proficiency)
 *   - review (FSRS due, overrides mastered/learning)
 *   - transition zone (0.4 <= p < 0.7 -> learning)
 */

import {
  getMasteryStatus,
  getMasteryColorClass,
  getMasteryBorderClass,
  type NodeMasteryData,
} from '../utils/mastery-color';

// Fixed "now" for deterministic tests: 2026-03-16T12:00:00Z
const NOW = new Date('2026-03-16T12:00:00Z').getTime();

/** Helper to create NodeMasteryData with defaults. */
function makeData(overrides: Partial<NodeMasteryData> = {}): NodeMasteryData {
  return {
    effectiveProficiency: null,
    hasInteraction: false,
    hasExamRecord: false,
    fsrsNextReview: null,
    ...overrides,
  };
}

describe('getMasteryStatus', () => {
  it('returns "unlearned" for a node with no interaction and no exam', () => {
    const data = makeData();
    expect(getMasteryStatus(data, NOW)).toBe('unlearned');
  });

  it('returns "learning" for a node with interaction but no exam', () => {
    const data = makeData({
      hasInteraction: true,
    });
    expect(getMasteryStatus(data, NOW)).toBe('learning');
  });

  it('returns "weak" for proficiency = 0.2 (below 0.4 threshold)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.2,
    });
    expect(getMasteryStatus(data, NOW)).toBe('weak');
  });

  it('returns "learning" for proficiency = 0.5 (transition zone 0.4-0.7)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.5,
    });
    expect(getMasteryStatus(data, NOW)).toBe('learning');
  });

  it('returns "mastered" for proficiency = 0.8 (above 0.7 threshold)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.8,
    });
    expect(getMasteryStatus(data, NOW)).toBe('mastered');
  });

  it('returns "mastered" for proficiency exactly 0.7 (boundary)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.7,
    });
    expect(getMasteryStatus(data, NOW)).toBe('mastered');
  });

  it('returns "learning" for proficiency exactly 0.4 (boundary, transition zone)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.4,
    });
    expect(getMasteryStatus(data, NOW)).toBe('learning');
  });

  it('returns "review" when FSRS is due and proficiency >= 0.4 (overrides mastered)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.85,
      fsrsNextReview: '2026-03-16T08:00:00Z', // 4 hours before NOW
    });
    expect(getMasteryStatus(data, NOW)).toBe('review');
  });

  it('returns "review" when FSRS is due and proficiency is in transition zone', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.5,
      fsrsNextReview: '2026-03-15T00:00:00Z', // yesterday
    });
    expect(getMasteryStatus(data, NOW)).toBe('review');
  });

  it('returns "mastered" when FSRS is NOT due (future review date)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.9,
      fsrsNextReview: '2026-03-20T00:00:00Z', // 4 days from NOW
    });
    expect(getMasteryStatus(data, NOW)).toBe('mastered');
  });

  it('returns "weak" when proficiency is null but has exam record', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: null,
    });
    expect(getMasteryStatus(data, NOW)).toBe('weak');
  });

  it('returns "weak" when FSRS is due but proficiency < 0.4 (review requires p >= 0.4)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.2,
      fsrsNextReview: '2026-03-15T00:00:00Z',
    });
    expect(getMasteryStatus(data, NOW)).toBe('weak');
  });

  it('returns "weak" for proficiency = 0 (edge case)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0,
    });
    expect(getMasteryStatus(data, NOW)).toBe('weak');
  });

  it('returns "mastered" for proficiency = 1.0 (max)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 1.0,
    });
    expect(getMasteryStatus(data, NOW)).toBe('mastered');
  });

  it('returns "review" when FSRS review time equals now exactly', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: true,
      effectiveProficiency: 0.6,
      fsrsNextReview: '2026-03-16T12:00:00Z', // exactly NOW
    });
    expect(getMasteryStatus(data, NOW)).toBe('review');
  });

  it('returns "learning" when FSRS due but proficiency is null (no review for unexamined)', () => {
    const data = makeData({
      hasInteraction: true,
      hasExamRecord: false,
      effectiveProficiency: null,
      fsrsNextReview: '2026-03-15T00:00:00Z',
    });
    // hasExamRecord is false, so FSRS check passes (proficiency is null, not >= 0.4)
    // falls through to !hasExamRecord -> learning
    expect(getMasteryStatus(data, NOW)).toBe('learning');
  });
});

describe('getMasteryColorClass', () => {
  it('returns "cl-mastery-unlearned" for unlearned', () => {
    expect(getMasteryColorClass('unlearned')).toBe('cl-mastery-unlearned');
  });

  it('returns "cl-mastery-learning" for learning', () => {
    expect(getMasteryColorClass('learning')).toBe('cl-mastery-learning');
  });

  it('returns "cl-mastery-weak" for weak', () => {
    expect(getMasteryColorClass('weak')).toBe('cl-mastery-weak');
  });

  it('returns "cl-mastery-mastered" for mastered', () => {
    expect(getMasteryColorClass('mastered')).toBe('cl-mastery-mastered');
  });

  it('returns "cl-mastery-review" for review', () => {
    expect(getMasteryColorClass('review')).toBe('cl-mastery-review');
  });
});

describe('getMasteryBorderClass', () => {
  it('returns "cl-mastery-learning-border" for learning', () => {
    expect(getMasteryBorderClass('learning')).toBe('cl-mastery-learning-border');
  });

  it('returns "cl-mastery-mastered-border" for mastered', () => {
    expect(getMasteryBorderClass('mastered')).toBe('cl-mastery-mastered-border');
  });
});
