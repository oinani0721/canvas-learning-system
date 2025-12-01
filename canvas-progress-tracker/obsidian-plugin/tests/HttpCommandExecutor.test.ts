/**
 * HttpCommandExecutor Unit Tests
 *
 * Tests for the HTTP command executor and mock executor.
 *
 * @module tests/HttpCommandExecutor
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  HttpCommandExecutor,
  MockCommandExecutor,
} from '../src/executors/HttpCommandExecutor';
import { CommandExecutionError } from '../src/types/ReviewTypes';

describe('HttpCommandExecutor', () => {
  let executor: HttpCommandExecutor;

  beforeEach(() => {
    executor = new HttpCommandExecutor({
      baseUrl: 'http://localhost:3000',
      apiKey: 'test-api-key',
      defaultTimeout: 5000,
      maxRetries: 2,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Command Validation', () => {
    it('should reject empty commands', async () => {
      await expect(executor.execute('')).rejects.toThrow(CommandExecutionError);
    });

    it('should reject commands with dangerous characters', async () => {
      const dangerousCommands = [
        '/test; rm -rf /',
        '/test && malicious',
        '/test | pipe',
        '/test `injection`',
        '/test $variable',
        '/test\ninjection',
      ];

      for (const cmd of dangerousCommands) {
        await expect(executor.execute(cmd)).rejects.toThrow('dangerous');
      }
    });
  });

  describe('API Communication', () => {
    it('should make POST request with correct headers', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, output: 'test' }),
      });
      global.fetch = mockFetch;

      await executor.execute('/review show');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/execute',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key',
          }),
        })
      );
    });

    it('should include command in request body', async () => {
      let requestBody: unknown;
      const mockFetch = vi.fn().mockImplementation((_url, options) => {
        requestBody = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, output: 'test' }),
        });
      });
      global.fetch = mockFetch;

      await executor.execute('/review show');

      expect(requestBody).toMatchObject({
        command: '/review show',
        format: 'json',
      });
    });
  });

  describe('Error Handling', () => {
    it('should throw on HTTP 401/403 without retry', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
      });
      global.fetch = mockFetch;

      await expect(executor.execute('/test')).rejects.toThrow('Authentication');
      expect(mockFetch).toHaveBeenCalledTimes(1); // No retry
    });

    it('should throw on HTTP 404 without retry', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
      });
      global.fetch = mockFetch;

      await expect(executor.execute('/test')).rejects.toThrow('not found');
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should retry on HTTP 500', async () => {
      let callCount = 0;
      const mockFetch = vi.fn().mockImplementation(() => {
        callCount++;
        if (callCount < 3) {
          return Promise.resolve({ ok: false, status: 500 });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });
      });
      global.fetch = mockFetch;

      await executor.execute('/test');
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it('should throw after max retries exhausted', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      });
      global.fetch = mockFetch;

      await expect(executor.execute('/test')).rejects.toThrow('retries');
      expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });
  });

  describe('Timeout Handling', () => {
    it('should handle aborted requests', async () => {
      // Create a mock that simulates an abort
      const mockFetch = vi.fn().mockImplementation(() => {
        const error = new Error('The operation was aborted');
        error.name = 'AbortError';
        return Promise.reject(error);
      });
      global.fetch = mockFetch;

      await expect(executor.execute('/test', { timeout: 100 })).rejects.toThrow('timed out');
    });
  });

  describe('Response Handling', () => {
    it('should return success result', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            output: 'test output',
            executionTime: 150,
          }),
      });
      global.fetch = mockFetch;

      const result = await executor.execute('/test');

      expect(result.success).toBe(true);
      expect(result.output).toBe('test output');
      expect(result.metadata?.retryCount).toBe(0);
    });

    it('should include metadata in result', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, output: 'test' }),
      });
      global.fetch = mockFetch;

      const result = await executor.execute('/test');

      expect(result.metadata).toBeDefined();
      expect(result.metadata?.cacheHit).toBe(false);
      expect(result.metadata?.executionTime).toBeGreaterThanOrEqual(0);
    });
  });
});

describe('MockCommandExecutor', () => {
  let executor: MockCommandExecutor;

  beforeEach(() => {
    executor = new MockCommandExecutor();
  });

  describe('Mock Responses', () => {
    it('should return mocked response', async () => {
      const mockResponse = {
        success: true,
        output: 'mocked output',
      };
      executor.setResponse('/test', mockResponse);

      const result = await executor.execute('/test');

      expect(result).toEqual(mockResponse);
    });

    it('should throw for unmocked commands', async () => {
      await expect(executor.execute('/unknown')).rejects.toThrow(
        'No mock response'
      );
    });

    it('should track execution history', async () => {
      executor.setResponse('/test', { success: true });

      await executor.execute('/test', { timeout: 1000 });
      await executor.execute('/test', { timeout: 2000 });

      const history = executor.getExecutionHistory();
      expect(history).toHaveLength(2);
      expect(history[0].command).toBe('/test');
      expect(history[0].options?.timeout).toBe(1000);
    });

    it('should clear responses and history', async () => {
      executor.setResponse('/test', { success: true });
      await executor.execute('/test');

      executor.clear();

      expect(executor.getExecutionHistory()).toHaveLength(0);
      await expect(executor.execute('/test')).rejects.toThrow();
    });
  });

  describe('Multiple Commands', () => {
    it('should handle different responses for different commands', async () => {
      executor.setResponse('/cmd1', { success: true, output: 'output1' });
      executor.setResponse('/cmd2', { success: true, output: 'output2' });

      const result1 = await executor.execute('/cmd1');
      const result2 = await executor.execute('/cmd2');

      expect(result1.output).toBe('output1');
      expect(result2.output).toBe('output2');
    });

    it('should return same response for repeated commands', async () => {
      executor.setResponse('/test', { success: true, output: 'same' });

      const result1 = await executor.execute('/test');
      const result2 = await executor.execute('/test');

      expect(result1.output).toBe(result2.output);
    });
  });
});
