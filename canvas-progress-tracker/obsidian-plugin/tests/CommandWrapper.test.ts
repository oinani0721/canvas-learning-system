/**
 * CommandWrapper Unit Tests
 *
 * Tests for the main CommandWrapper class.
 *
 * @module tests/CommandWrapper
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  CommandWrapper,
  createMockCommandWrapper,
} from '../src/managers/CommandWrapper';
import { MockCommandExecutor } from '../src/executors/HttpCommandExecutor';

describe('CommandWrapper', () => {
  let wrapper: CommandWrapper;
  let mockExecutor: MockCommandExecutor;

  beforeEach(() => {
    wrapper = createMockCommandWrapper();
    mockExecutor = wrapper.getMockExecutor()!;
  });

  afterEach(async () => {
    await wrapper.dispose();
  });

  describe('getReviewTasks', () => {
    it('should return review tasks from API', async () => {
      const mockTasks = {
        success: true,
        output: JSON.stringify({
          tasks: [
            {
              id: 'task-1',
              canvas_id: 'canvas-1',
              canvas_title: 'Math',
              concept_name: 'Algebra',
              priority: 'high',
              urgency: 80,
              memory_strength: 60,
              due_date: '2025-01-20',
            },
            {
              id: 'task-2',
              canvas_id: 'canvas-1',
              concept_name: 'Geometry',
              priority: 'medium',
              urgency: 50,
              memory_strength: 70,
              due_date: '2025-01-22',
            },
          ],
        }),
      };
      mockExecutor.setResponse('/review show', mockTasks);

      const tasks = await wrapper.getReviewTasks();

      expect(tasks).toHaveLength(2);
      expect(tasks[0].id).toBe('task-1');
      expect(tasks[0].conceptName).toBe('Algebra');
      expect(tasks[0].priority).toBe('high');
    });

    it('should cache results', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({ tasks: [{ id: 'task-1' }] }),
      });

      // First call
      await wrapper.getReviewTasks();
      // Second call (should use cache)
      await wrapper.getReviewTasks();

      const history = mockExecutor.getExecutionHistory();
      expect(history).toHaveLength(1); // Only one API call
    });

    it('should filter by canvas ID', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({
          tasks: [
            { id: 'task-1', canvas_id: 'canvas-1' },
            { id: 'task-2', canvas_id: 'canvas-2' },
          ],
        }),
      });

      const tasks = await wrapper.getReviewTasks({ canvasId: 'canvas-1' });

      expect(tasks).toHaveLength(1);
      expect(tasks[0].canvasId).toBe('canvas-1');
    });

    it('should filter by priority', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({
          tasks: [
            { id: 'task-1', priority: 'high' },
            { id: 'task-2', priority: 'low' },
          ],
        }),
      });

      const tasks = await wrapper.getReviewTasks({ priority: 'high' });

      expect(tasks).toHaveLength(1);
      expect(tasks[0].priority).toBe('high');
    });

    it('should sort tasks', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({
          tasks: [
            { id: 'task-1', urgency: 50 },
            { id: 'task-2', urgency: 80 },
            { id: 'task-3', urgency: 30 },
          ],
        }),
      });

      const tasks = await wrapper.getReviewTasks({
        sortBy: 'urgency',
        sortOrder: 'desc',
      });

      expect(tasks[0].urgency).toBe(80);
      expect(tasks[1].urgency).toBe(50);
      expect(tasks[2].urgency).toBe(30);
    });

    it('should limit results', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({
          tasks: [
            { id: 'task-1' },
            { id: 'task-2' },
            { id: 'task-3' },
          ],
        }),
      });

      const tasks = await wrapper.getReviewTasks({ limit: 2 });

      expect(tasks).toHaveLength(2);
    });

    it('should throw on API error', async () => {
      mockExecutor.setResponse('/review show', {
        success: false,
        error: 'API Error',
      });

      await expect(wrapper.getReviewTasks()).rejects.toThrow('API Error');
    });
  });

  describe('generateReviewPlan', () => {
    it('should generate review plan', async () => {
      const mockPlan = {
        success: true,
        output: JSON.stringify({
          plan: {
            id: 'plan-1',
            canvas_id: 'canvas-1',
            plan_type: 'weakness-focused',
            difficulty: 'adaptive',
            estimated_duration: 30,
            sections: [
              { id: 'sec-1', title: 'Intro', duration: 10 },
            ],
          },
        }),
      };
      mockExecutor.setResponse('/generate-review canvas-1', mockPlan);

      const plan = await wrapper.generateReviewPlan('canvas-1');

      expect(plan.id).toBe('plan-1');
      expect(plan.planType).toBe('weakness-focused');
      expect(plan.sections).toHaveLength(1);
    });

    it('should include options in command', async () => {
      mockExecutor.setResponse(
        '/generate-review canvas-1 --plan-type=targeted --difficulty=hard --duration=60',
        {
          success: true,
          output: JSON.stringify({ plan: { id: 'plan-1' } }),
        }
      );

      await wrapper.generateReviewPlan('canvas-1', {
        planType: 'targeted',
        difficulty: 'hard',
        duration: 60,
      });

      const history = mockExecutor.getExecutionHistory();
      expect(history[0].command).toContain('--plan-type=targeted');
      expect(history[0].command).toContain('--difficulty=hard');
      expect(history[0].command).toContain('--duration=60');
    });

    it('should not cache plan generation', async () => {
      mockExecutor.setResponse('/generate-review canvas-1', {
        success: true,
        output: JSON.stringify({ plan: { id: 'plan-1' } }),
      });

      await wrapper.generateReviewPlan('canvas-1');
      await wrapper.generateReviewPlan('canvas-1');

      const history = mockExecutor.getExecutionHistory();
      expect(history).toHaveLength(2); // Both calls made
    });
  });

  describe('completeReview', () => {
    it('should complete review and return result', async () => {
      mockExecutor.setResponse('/review complete task-1', {
        success: true,
        output: JSON.stringify({
          result: {
            success: true,
            task_id: 'task-1',
            total_score: 85,
            passed: true,
            scores: {
              accuracy: 22,
              imagery: 20,
              completeness: 23,
              originality: 20,
            },
          },
        }),
      });

      const result = await wrapper.completeReview('task-1', {
        userUnderstanding: 'My understanding of the concept...',
      });

      expect(result.success).toBe(true);
      expect(result.totalScore).toBe(85);
      expect(result.passed).toBe(true);
    });

    it('should require task ID', async () => {
      await expect(
        wrapper.completeReview('', { userUnderstanding: 'test' })
      ).rejects.toThrow('Task ID is required');
    });

    it('should require user understanding', async () => {
      await expect(
        wrapper.completeReview('task-1', { userUnderstanding: '' })
      ).rejects.toThrow('User understanding is required');
    });

    it('should invalidate cache after completion', async () => {
      // Setup review tasks
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({ tasks: [{ id: 'task-1' }] }),
      });
      mockExecutor.setResponse('/review complete task-1', {
        success: true,
        output: JSON.stringify({ result: { success: true } }),
      });

      // Get tasks (cached)
      await wrapper.getReviewTasks();
      // Complete review (should invalidate)
      await wrapper.completeReview('task-1', {
        userUnderstanding: 'test',
      });
      // Get tasks again (should refetch)
      await wrapper.getReviewTasks();

      const history = mockExecutor.getExecutionHistory();
      const showCalls = history.filter((h) => h.command === '/review show');
      expect(showCalls).toHaveLength(2); // Cache was invalidated
    });
  });

  describe('executeBatch', () => {
    it('should execute multiple commands', async () => {
      mockExecutor.setResponse('/cmd1', { success: true, output: 'out1' });
      mockExecutor.setResponse('/cmd2', { success: true, output: 'out2' });

      const results = await wrapper.executeBatch([
        { command: '/cmd1', id: 'first' },
        { command: '/cmd2', id: 'second' },
      ]);

      expect(results).toHaveLength(2);
      expect(results[0].id).toBe('first');
      expect(results[0].result.output).toBe('out1');
      expect(results[1].id).toBe('second');
      expect(results[1].result.output).toBe('out2');
    });

    it('should handle partial failures', async () => {
      mockExecutor.setResponse('/cmd1', { success: true });
      // /cmd2 not set, will throw

      const results = await wrapper.executeBatch([
        { command: '/cmd1' },
        { command: '/cmd2' },
      ]);

      expect(results[0].status).toBe('fulfilled');
      expect(results[1].status).toBe('rejected');
    });
  });

  describe('Cache Management', () => {
    it('should clear cache', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({ tasks: [] }),
      });

      await wrapper.getReviewTasks();
      await wrapper.clearCache();
      await wrapper.getReviewTasks();

      const history = mockExecutor.getExecutionHistory();
      expect(history).toHaveLength(2);
    });

    it('should return cache statistics', async () => {
      mockExecutor.setResponse('/review show', {
        success: true,
        output: JSON.stringify({ tasks: [] }),
      });

      await wrapper.getReviewTasks();
      await wrapper.getReviewTasks(); // From cache

      const stats = wrapper.getCacheStats();
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
    });
  });
});
