/**
 * ErrorHistoryManager Tests - Canvas Review System
 *
 * Tests for error history persistence and management.
 *
 * @source Story 21.5.5 - AC 4, 5: 设置面板历史 + 7天自动清理
 * @module tests/managers/ErrorHistoryManager.test
 */

import { Plugin } from 'obsidian';
import { ErrorHistoryManager, ErrorRecord } from '../../src/managers/ErrorHistoryManager';
import { ApiError, ErrorType } from '../../src/api/types';

// Constants (must match implementation)
const MAX_RECORDS = 100;
const EXPIRY_DAYS = 7;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

describe('ErrorHistoryManager', () => {
  let plugin: Plugin;
  let manager: ErrorHistoryManager;

  beforeEach(() => {
    plugin = new Plugin();
    (plugin as any)._clearData();
    manager = new ErrorHistoryManager(plugin);
  });

  describe('addError', () => {
    it('should create valid record with all fields', () => {
      const error = new ApiError(
        'Test error message',
        'HttpError5xx',
        500,
        { detail: 'server crash' },
        'BUG-12345678',
        'AIProviderError'
      );

      const record = manager.addError(error, 'decompose_basic');

      expect(record.id).toMatch(/^ERR-[a-z0-9]+-[a-z0-9]+$/);
      expect(record.timestamp).toBeLessThanOrEqual(Date.now());
      expect(record.errorType).toBe('HttpError5xx');
      expect(record.backendErrorType).toBe('AIProviderError');
      expect(record.bugId).toBe('BUG-12345678');
      expect(record.message).toBe('Test error message');
      expect(record.operation).toBe('decompose_basic');
      expect(record.statusCode).toBe(500);
      expect(record.details).toEqual({ detail: 'server crash' });
    });

    it('should add records to the beginning (most recent first)', () => {
      const error1 = new ApiError('Error 1', 'NetworkError');
      const error2 = new ApiError('Error 2', 'TimeoutError');

      manager.addError(error1, 'op1');
      manager.addError(error2, 'op2');

      const recent = manager.getRecent(10);
      expect(recent[0].message).toBe('Error 2');
      expect(recent[1].message).toBe('Error 1');
    });

    it('should handle error without optional fields', () => {
      const error = new ApiError('Simple error', 'UnknownError');

      const record = manager.addError(error, 'test_op');

      expect(record.bugId).toBeUndefined();
      expect(record.backendErrorType).toBeUndefined();
      expect(record.statusCode).toBeUndefined();
      expect(record.details).toBeUndefined();
    });
  });

  describe('getRecent', () => {
    it('should return max 20 records by default', () => {
      // Add 30 errors
      for (let i = 0; i < 30; i++) {
        manager.addError(new ApiError(`Error ${i}`, 'NetworkError'), 'test');
      }

      const recent = manager.getRecent();
      expect(recent.length).toBe(20);
    });

    it('should return specified limit', () => {
      for (let i = 0; i < 10; i++) {
        manager.addError(new ApiError(`Error ${i}`, 'NetworkError'), 'test');
      }

      expect(manager.getRecent(5).length).toBe(5);
      expect(manager.getRecent(3).length).toBe(3);
    });

    it('should return all records if less than limit', () => {
      manager.addError(new ApiError('Error 1', 'NetworkError'), 'test');
      manager.addError(new ApiError('Error 2', 'NetworkError'), 'test');

      const recent = manager.getRecent(20);
      expect(recent.length).toBe(2);
    });

    it('should return empty array when no records', () => {
      expect(manager.getRecent()).toEqual([]);
    });
  });

  describe('cleanup - AC5: 7天自动清理', () => {
    beforeEach(async () => {
      await manager.load();
    });

    it('should remove records older than 7 days', async () => {
      // Add an old record manually
      const oldTimestamp = Date.now() - (EXPIRY_DAYS + 1) * MS_PER_DAY;
      const oldRecord: ErrorRecord = {
        id: 'ERR-old-record',
        timestamp: oldTimestamp,
        errorType: 'NetworkError',
        message: 'Old error',
        operation: 'test',
      };

      // Add through internal array
      (manager as any).records = [oldRecord];
      await manager.save();

      // Add a new record
      manager.addError(new ApiError('New error', 'NetworkError'), 'test');

      // Run cleanup
      const removed = await manager.cleanup();

      expect(removed).toBe(1);
      expect(manager.getAll().length).toBe(1);
      expect(manager.getAll()[0].message).toBe('New error');
    });

    it('should keep records within 7 days', async () => {
      // Add record from 6 days ago
      const recentTimestamp = Date.now() - 6 * MS_PER_DAY;
      const recentRecord: ErrorRecord = {
        id: 'ERR-recent-record',
        timestamp: recentTimestamp,
        errorType: 'TimeoutError',
        message: 'Recent error',
        operation: 'test',
      };

      (manager as any).records = [recentRecord];

      const removed = await manager.cleanup();

      expect(removed).toBe(0);
      expect(manager.getAll().length).toBe(1);
    });

    it('should return count of removed records', async () => {
      const now = Date.now();
      const records: ErrorRecord[] = [
        { id: 'ERR-1', timestamp: now - 8 * MS_PER_DAY, errorType: 'NetworkError', message: 'Old 1', operation: 'test' },
        { id: 'ERR-2', timestamp: now - 10 * MS_PER_DAY, errorType: 'NetworkError', message: 'Old 2', operation: 'test' },
        { id: 'ERR-3', timestamp: now - 1 * MS_PER_DAY, errorType: 'NetworkError', message: 'New', operation: 'test' },
      ];

      (manager as any).records = records;

      const removed = await manager.cleanup();

      expect(removed).toBe(2);
      expect(manager.getAll().length).toBe(1);
    });
  });

  describe('MAX_RECORDS limit', () => {
    it('should enforce 100 records limit', () => {
      // Add 110 errors
      for (let i = 0; i < 110; i++) {
        manager.addError(new ApiError(`Error ${i}`, 'NetworkError'), 'test');
      }

      expect(manager.getCount()).toBe(MAX_RECORDS);
      // Most recent should be Error 109
      expect(manager.getRecent(1)[0].message).toBe('Error 109');
    });

    it('should remove oldest records when limit exceeded', () => {
      for (let i = 0; i < 105; i++) {
        manager.addError(new ApiError(`Error ${i}`, 'NetworkError'), 'test');
      }

      const all = manager.getAll();
      // Should not contain Error 0-4 (first 5 were dropped)
      const messages = all.map((r) => r.message);
      expect(messages).not.toContain('Error 0');
      expect(messages).not.toContain('Error 4');
      expect(messages).toContain('Error 104');
    });
  });

  describe('save/load persistence', () => {
    it('should persist records across load cycles', async () => {
      manager.addError(new ApiError('Persistent error', 'HttpError5xx', 500), 'persist_test');

      // Force save
      await manager.save();

      // Create new manager with same plugin
      const manager2 = new ErrorHistoryManager(plugin);
      await manager2.load();

      expect(manager2.getCount()).toBe(1);
      expect(manager2.getRecent(1)[0].message).toBe('Persistent error');
    });

    it('should handle load with no existing data', async () => {
      (plugin as any)._clearData();

      await manager.load();

      expect(manager.getCount()).toBe(0);
      expect(manager.getAll()).toEqual([]);
    });

    it('should run cleanup on load', async () => {
      // Set up old data
      const oldTimestamp = Date.now() - 10 * MS_PER_DAY;
      (plugin as any)._setData({
        errorHistory: [
          { id: 'ERR-old', timestamp: oldTimestamp, errorType: 'NetworkError', message: 'Old', operation: 'test' },
        ],
      });

      await manager.load();

      // Old record should be cleaned up
      expect(manager.getCount()).toBe(0);
    });
  });

  describe('debouncing concurrent saves', () => {
    it('should not corrupt data with concurrent saves', async () => {
      // Add multiple errors rapidly
      for (let i = 0; i < 10; i++) {
        manager.addError(new ApiError(`Error ${i}`, 'NetworkError'), 'rapid');
      }

      // Wait for debounced saves to complete
      await new Promise((resolve) => setTimeout(resolve, 200));

      // All records should be present
      expect(manager.getCount()).toBe(10);
    });
  });

  describe('getById and getByBugId', () => {
    it('should find record by ID', () => {
      const error = new ApiError('Test', 'NetworkError');
      const record = manager.addError(error, 'test');

      const found = manager.getById(record.id);
      expect(found).toBeDefined();
      expect(found?.message).toBe('Test');
    });

    it('should find record by bug ID', () => {
      const error = new ApiError('Test', 'HttpError5xx', 500, undefined, 'BUG-ABCD1234');
      manager.addError(error, 'test');

      const found = manager.getByBugId('BUG-ABCD1234');
      expect(found).toBeDefined();
      expect(found?.bugId).toBe('BUG-ABCD1234');
    });

    it('should return undefined for non-existent ID', () => {
      expect(manager.getById('non-existent')).toBeUndefined();
      expect(manager.getByBugId('BUG-NOTFOUND')).toBeUndefined();
    });
  });

  describe('clearAll and deleteRecord', () => {
    it('should clear all records', async () => {
      manager.addError(new ApiError('Error 1', 'NetworkError'), 'test');
      manager.addError(new ApiError('Error 2', 'NetworkError'), 'test');

      const cleared = await manager.clearAll();

      expect(cleared).toBe(2);
      expect(manager.getCount()).toBe(0);
    });

    it('should delete specific record', async () => {
      const record1 = manager.addError(new ApiError('Error 1', 'NetworkError'), 'test');
      manager.addError(new ApiError('Error 2', 'NetworkError'), 'test');

      const deleted = await manager.deleteRecord(record1.id);

      expect(deleted).toBe(true);
      expect(manager.getCount()).toBe(1);
      expect(manager.getById(record1.id)).toBeUndefined();
    });

    it('should return false when deleting non-existent record', async () => {
      const deleted = await manager.deleteRecord('non-existent');
      expect(deleted).toBe(false);
    });
  });

  describe('getStats', () => {
    it('should return statistics about stored errors', () => {
      manager.addError(new ApiError('Network fail', 'NetworkError'), 'decompose');
      manager.addError(new ApiError('Timeout', 'TimeoutError'), 'decompose');
      manager.addError(new ApiError('Server error', 'HttpError5xx'), 'scoring');

      const stats = manager.getStats();

      expect(stats.total).toBe(3);
      expect(stats.byType['NetworkError']).toBe(1);
      expect(stats.byType['TimeoutError']).toBe(1);
      expect(stats.byType['HttpError5xx']).toBe(1);
      expect(stats.byOperation['decompose']).toBe(2);
      expect(stats.byOperation['scoring']).toBe(1);
      expect(stats.newestTimestamp).toBeDefined();
      expect(stats.oldestTimestamp).toBeDefined();
    });

    it('should return null timestamps when no records', () => {
      const stats = manager.getStats();

      expect(stats.total).toBe(0);
      expect(stats.oldestTimestamp).toBeNull();
      expect(stats.newestTimestamp).toBeNull();
    });
  });
});
