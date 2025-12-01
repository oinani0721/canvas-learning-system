/**
 * Output Parsers Unit Tests
 *
 * Tests for ReviewOutputParser, GenerateReviewOutputParser, CompleteReviewOutputParser.
 *
 * @module tests/parsers
 */

import { describe, it, expect } from 'vitest';
import { ReviewOutputParser } from '../src/parsers/ReviewOutputParser';
import { GenerateReviewOutputParser } from '../src/parsers/GenerateReviewOutputParser';
import { CompleteReviewOutputParser } from '../src/parsers/CompleteReviewOutputParser';

describe('ReviewOutputParser', () => {
  const parser = new ReviewOutputParser();

  describe('JSON Parsing', () => {
    it('should parse valid JSON with tasks array', () => {
      const input = JSON.stringify({
        tasks: [
          {
            id: 'task-1',
            canvas_id: 'canvas-1',
            canvas_title: 'Math Canvas',
            concept_name: 'Algebra',
            priority: 'high',
            urgency: 75,
            memory_strength: 60,
            due_date: '2025-01-20',
          },
        ],
      });

      const result = parser.parse(input);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('task-1');
      expect(result[0].canvasId).toBe('canvas-1');
      expect(result[0].priority).toBe('high');
      expect(result[0].urgency).toBe(75);
    });

    it('should handle items array format', () => {
      const input = JSON.stringify({
        items: [{ id: 'item-1', concept_name: 'Test' }],
      });

      const result = parser.parse(input);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('item-1');
    });

    it('should handle direct array format', () => {
      const input = JSON.stringify([
        { id: 'direct-1', concept_name: 'Direct Test' },
      ]);

      const result = parser.parse(input);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('direct-1');
    });

    it('should map priority values correctly', () => {
      const testCases = [
        { input: 'critical', expected: 'critical' },
        { input: 'high', expected: 'high' },
        { input: 'medium', expected: 'medium' },
        { input: 'low', expected: 'low' },
        { input: '4', expected: 'critical' },
        { input: '3', expected: 'high' },
        { input: '2', expected: 'medium' },
        { input: '1', expected: 'low' },
        { input: 'unknown', expected: 'medium' },
      ];

      for (const tc of testCases) {
        const input = JSON.stringify({
          tasks: [{ id: 'test', priority: tc.input }],
        });
        const result = parser.parse(input);
        expect(result[0].priority).toBe(tc.expected);
      }
    });

    it('should normalize numeric values', () => {
      const input = JSON.stringify({
        tasks: [
          {
            id: 'test',
            urgency: 150, // Over 100
            memory_strength: -10, // Under 0
          },
        ],
      });

      const result = parser.parse(input);
      expect(result[0].urgency).toBe(100);
      expect(result[0].memoryStrength).toBe(0);
    });

    it('should parse dates correctly', () => {
      const input = JSON.stringify({
        tasks: [
          {
            id: 'test',
            due_date: '2025-01-20T10:30:00Z',
            last_review_date: '2025-01-15',
          },
        ],
      });

      const result = parser.parse(input);
      expect(result[0].dueDate).toBeInstanceOf(Date);
      expect(result[0].lastReviewDate).toBeInstanceOf(Date);
    });
  });

  describe('Text Parsing (Fallback)', () => {
    it('should parse text format with key-value pairs', () => {
      const input = `
Task #1:
  - Canvas: math.canvas
  - Concept: Algebra Basics
  - Priority: high
  - Due: 2025-01-20
`;

      const result = parser.parse(input);
      expect(result).toHaveLength(1);
      expect(result[0].canvasId).toBe('math.canvas');
      expect(result[0].conceptName).toBe('Algebra Basics');
      expect(result[0].priority).toBe('high');
    });

    it('should parse standalone line format', () => {
      const input = `- Algebra (canvas: math, priority: high, due: 2025-01-20)`;

      const result = parser.parse(input);
      expect(result).toHaveLength(1);
      expect(result[0].conceptName).toBe('Algebra');
    });
  });

  describe('Edge Cases', () => {
    it('should return empty array for null input', () => {
      expect(parser.parse(null as unknown as string)).toEqual([]);
    });

    it('should return empty array for empty string', () => {
      expect(parser.parse('')).toEqual([]);
    });

    it('should return empty array for whitespace only', () => {
      expect(parser.parse('   \n  \t  ')).toEqual([]);
    });

    it('should handle malformed JSON gracefully', () => {
      const result = parser.parse('{ invalid json');
      // Should fallback to text parsing and return something
      expect(Array.isArray(result)).toBe(true);
    });
  });
});

describe('GenerateReviewOutputParser', () => {
  const parser = new GenerateReviewOutputParser();

  describe('JSON Parsing', () => {
    it('should parse valid review plan', () => {
      const input = JSON.stringify({
        plan: {
          id: 'plan-1',
          canvas_id: 'canvas-1',
          canvas_title: 'Study Plan',
          plan_type: 'weakness-focused',
          difficulty: 'adaptive',
          estimated_duration: 45,
          target_mastery: 85,
          focus_areas: ['algebra', 'geometry'],
          max_concepts: 8,
          sections: [
            {
              id: 'sec-1',
              title: 'Introduction',
              type: 'concept',
              concepts: ['basics'],
              duration: 10,
              order: 1,
            },
          ],
          resources: [
            {
              id: 'res-1',
              title: 'Study Guide',
              type: 'note',
              path: 'guides/study.md',
              required: true,
            },
          ],
          generated_at: '2025-01-15T10:00:00Z',
        },
      });

      const result = parser.parse(input);
      expect(result.id).toBe('plan-1');
      expect(result.planType).toBe('weakness-focused');
      expect(result.difficulty).toBe('adaptive');
      expect(result.estimatedDuration).toBe(45);
      expect(result.sections).toHaveLength(1);
      expect(result.resources).toHaveLength(1);
      expect(result.focusAreas).toContain('algebra');
    });

    it('should map plan types correctly', () => {
      const testCases = [
        { input: 'weakness-focused', expected: 'weakness-focused' },
        { input: 'weakness', expected: 'weakness-focused' },
        { input: 'comprehensive', expected: 'comprehensive' },
        { input: 'full', expected: 'comprehensive' },
        { input: 'targeted', expected: 'targeted' },
        { input: 'unknown', expected: 'comprehensive' },
      ];

      for (const tc of testCases) {
        const input = JSON.stringify({ plan_type: tc.input });
        const result = parser.parse(input);
        expect(result.planType).toBe(tc.expected);
      }
    });

    it('should map difficulty correctly', () => {
      const testCases = [
        { input: 'easy', expected: 'easy' },
        { input: 'simple', expected: 'easy' },
        { input: 'medium', expected: 'medium' },
        { input: 'hard', expected: 'hard' },
        { input: 'adaptive', expected: 'adaptive' },
        { input: 'auto', expected: 'adaptive' },
        { input: 'unknown', expected: 'adaptive' },
      ];

      for (const tc of testCases) {
        const input = JSON.stringify({ difficulty: tc.input });
        const result = parser.parse(input);
        expect(result.difficulty).toBe(tc.expected);
      }
    });
  });

  describe('Text Parsing (Fallback)', () => {
    it('should parse text format', () => {
      const input = `
Canvas: math.canvas
Type: comprehensive
Difficulty: medium
Duration: 30

Sections:
1. Introduction (concepts: basics; duration: 10)
2. Advanced Topics (concepts: algebra, geometry; duration: 20)
`;

      const result = parser.parse(input);
      expect(result.canvasId).toBe('math.canvas');
      expect(result.planType).toBe('comprehensive');
      expect(result.difficulty).toBe('medium');
      expect(result.estimatedDuration).toBe(30);
    });
  });

  describe('Edge Cases', () => {
    it('should return empty plan for empty input', () => {
      const result = parser.parse('');
      expect(result.id).toBeDefined();
      expect(result.sections).toEqual([]);
      expect(result.resources).toEqual([]);
    });

    it('should use defaults for missing values', () => {
      const result = parser.parse('{}');
      expect(result.planType).toBe('comprehensive');
      expect(result.difficulty).toBe('adaptive');
      expect(result.estimatedDuration).toBe(30);
      expect(result.targetMastery).toBe(80);
      expect(result.maxConcepts).toBe(10);
    });
  });
});

describe('CompleteReviewOutputParser', () => {
  const parser = new CompleteReviewOutputParser();

  describe('JSON Parsing', () => {
    it('should parse complete review result', () => {
      const input = JSON.stringify({
        result: {
          success: true,
          task_id: 'task-1',
          canvas_id: 'canvas-1',
          scores: {
            accuracy: 22,
            imagery: 20,
            completeness: 23,
            originality: 18,
          },
          total_score: 83,
          passed: true,
          pass_threshold: 60,
          statistics: {
            concepts_reviewed: 5,
            concepts_passed: 4,
            concepts_failed: 1,
            average_score: 80,
            time_spent: 25,
          },
          feedback: 'Great understanding!',
          completed_at: '2025-01-15T11:30:00Z',
        },
      });

      const result = parser.parse(input);
      expect(result.success).toBe(true);
      expect(result.taskId).toBe('task-1');
      expect(result.totalScore).toBe(83);
      expect(result.passed).toBe(true);
      expect(result.scores.accuracy).toBe(22);
      expect(result.statistics.conceptsReviewed).toBe(5);
      expect(result.feedback).toBe('Great understanding!');
    });

    it('should calculate passed from score and threshold', () => {
      const input = JSON.stringify({
        total_score: 65,
        pass_threshold: 60,
      });

      const result = parser.parse(input);
      expect(result.passed).toBe(true);
    });

    it('should normalize scores to valid ranges', () => {
      const input = JSON.stringify({
        scores: {
          accuracy: 30, // Over 25
          imagery: -5, // Under 0
          completeness: 20,
          originality: 15,
        },
      });

      const result = parser.parse(input);
      expect(result.scores.accuracy).toBe(25);
      expect(result.scores.imagery).toBe(0);
    });
  });

  describe('Text Parsing (Fallback)', () => {
    it('should parse success indicator', () => {
      const input = 'Review completed successfully!\nScore: 85/100';

      const result = parser.parse(input);
      expect(result.success).toBe(true);
      expect(result.totalScore).toBe(85);
    });

    it('should parse failure indicator', () => {
      const input = 'Review failed.\nScore: 45 points';

      const result = parser.parse(input);
      expect(result.passed).toBe(false);
      expect(result.totalScore).toBe(45);
    });

    it('should parse key-value format', () => {
      const input = `
Task: task-123
Canvas: math-canvas
Total: 78/100
Accuracy: 20
Imagery: 18
Completeness: 22
Originality: 18
Passed: yes
`;

      const result = parser.parse(input);
      expect(result.taskId).toBe('task-123');
      expect(result.canvasId).toBe('math-canvas');
      expect(result.totalScore).toBe(78);
      expect(result.scores.accuracy).toBe(20);
      expect(result.passed).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should return empty result for empty input', () => {
      const result = parser.parse('');
      expect(result.success).toBe(false);
      expect(result.totalScore).toBe(0);
      expect(result.completedAt).toBeInstanceOf(Date);
    });

    it('should calculate total from individual scores if not provided', () => {
      const input = `
Accuracy: 20
Imagery: 18
Completeness: 22
Originality: 15
`;

      const result = parser.parse(input);
      expect(result.totalScore).toBe(75);
    });
  });
});
