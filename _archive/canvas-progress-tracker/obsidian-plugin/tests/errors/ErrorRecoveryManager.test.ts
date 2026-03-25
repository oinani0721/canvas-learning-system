/**
 * Error Recovery Manager Tests - Canvas Review System
 *
 * Tests for error recovery strategies and state management.
 *
 * @module tests/errors/ErrorRecoveryManager.test
 */

import { ErrorRecoveryManager } from '../../src/errors/ErrorRecoveryManager';
import { ErrorNotifier } from '../../src/errors/ErrorNotifier';
import { APIError, NetworkError } from '../../src/errors/PluginError';

// Mock ErrorNotifier
jest.mock('../../src/errors/ErrorNotifier');

// Mock Obsidian
jest.mock('obsidian', () => ({
    Modal: class MockModal {
        open() {}
        close() {}
    },
    Notice: jest.fn()
}));

describe('ErrorRecoveryManager', () => {
    let manager: ErrorRecoveryManager;
    let mockNotifier: jest.Mocked<ErrorNotifier>;
    let mockApp: any;

    beforeEach(() => {
        mockApp = {
            workspace: {},
            vault: {}
        };

        mockNotifier = new ErrorNotifier() as jest.Mocked<ErrorNotifier>;
        mockNotifier.showCacheFallback = jest.fn();
        mockNotifier.showDegradedMode = jest.fn();
        mockNotifier.showInfo = jest.fn();
        mockNotifier.showSuccess = jest.fn();

        manager = new ErrorRecoveryManager(mockApp, mockNotifier);
    });

    describe('cache management', () => {
        it('should cache data', () => {
            manager.cacheData('operation1', { key: 'value' });

            const cached = manager.getCachedData<{ key: string }>('operation1');
            expect(cached).toEqual({ key: 'value' });
        });

        it('should return null for expired cache', async () => {
            manager.setCacheMaxAge(100); // 100ms
            manager.cacheData('operation1', { key: 'value' });

            // Wait for cache to expire
            await new Promise(resolve => setTimeout(resolve, 150));

            const cached = manager.getCachedData('operation1');
            expect(cached).toBeNull();
        });

        it('should return null for non-existent cache', () => {
            const cached = manager.getCachedData('nonexistent');
            expect(cached).toBeNull();
        });

        it('should clear all cache', () => {
            manager.cacheData('op1', 'data1');
            manager.cacheData('op2', 'data2');

            manager.clearCache();

            expect(manager.getCachedData('op1')).toBeNull();
            expect(manager.getCachedData('op2')).toBeNull();
        });
    });

    describe('state snapshots', () => {
        it('should save and retrieve state snapshot', () => {
            const state = { nodes: [], edges: [] };
            manager.saveStateSnapshot('canvas1', state, 'addNode');

            const retrieved = manager.getSnapshot<typeof state>('canvas1');
            expect(retrieved).toEqual(state);
        });

        it('should rollback to saved state', () => {
            const state = { nodes: [{ id: '1' }] };
            manager.saveStateSnapshot('canvas1', state, 'deleteNode');

            const rolledBack = manager.rollbackState<typeof state>('canvas1');

            expect(rolledBack).toEqual(state);
            expect(manager.getSnapshot('canvas1')).toBeNull(); // Removed after rollback
            expect(mockNotifier.showInfo).toHaveBeenCalled();
        });

        it('should return null for non-existent snapshot', () => {
            const result = manager.rollbackState('nonexistent');
            expect(result).toBeNull();
        });

        it('should remove oldest snapshot when limit reached', () => {
            // Save 11 snapshots (limit is 10)
            for (let i = 0; i < 11; i++) {
                manager.saveStateSnapshot(`snap${i}`, { id: i }, `op${i}`);
            }

            // First snapshot should be gone
            expect(manager.getSnapshot('snap0')).toBeNull();
            // Last snapshot should exist
            expect(manager.getSnapshot('snap10')).not.toBeNull();
        });

        it('should deep clone state to prevent mutations', () => {
            const state = { nested: { value: 1 } };
            manager.saveStateSnapshot('test', state, 'op');

            // Mutate original
            state.nested.value = 999;

            // Snapshot should have original value
            const retrieved = manager.getSnapshot<typeof state>('test');
            expect(retrieved?.nested.value).toBe(1);
        });
    });

    describe('degraded features', () => {
        it('should mark feature as degraded', () => {
            manager.markFeatureDegraded('decompose', 'API unavailable');

            expect(manager.isFeatureDegraded('decompose')).toBe(true);
        });

        it('should not mark non-degraded feature', () => {
            expect(manager.isFeatureDegraded('score')).toBe(false);
        });

        it('should restore degraded feature', () => {
            manager.markFeatureDegraded('decompose', 'reason');
            manager.restoreFeature('decompose');

            expect(manager.isFeatureDegraded('decompose')).toBe(false);
            expect(mockNotifier.showSuccess).toHaveBeenCalled();
        });

        it('should list degraded features', () => {
            manager.markFeatureDegraded('feature1', 'reason1');
            manager.markFeatureDegraded('feature2', 'reason2');

            const degraded = manager.getDegradedFeatures();
            expect(degraded).toContain('feature1');
            expect(degraded).toContain('feature2');
        });

        it('should clear all degraded features', () => {
            manager.markFeatureDegraded('f1', 'r1');
            manager.markFeatureDegraded('f2', 'r2');

            manager.clearDegradedFeatures();

            expect(manager.getDegradedFeatures()).toHaveLength(0);
        });
    });

    describe('recoverFromAPIError', () => {
        it('should use provided fallback data', async () => {
            const error = new APIError('Server error', 500, '/api/test');
            const fallbackData = { cached: true };

            const result = await manager.recoverFromAPIError(
                error,
                'test operation',
                fallbackData
            );

            expect(result.success).toBe(true);
            expect(result.data).toEqual(fallbackData);
            expect(result.action).toBe('use_cache');
            expect(mockNotifier.showCacheFallback).toHaveBeenCalled();
        });

        it('should use internal cache when available', async () => {
            manager.cacheData('test operation', { internal: true });

            const error = new APIError('Server error', 500, '/api/test');

            const result = await manager.recoverFromAPIError(
                error,
                'test operation'
            );

            expect(result.success).toBe(true);
            expect(result.data).toEqual({ internal: true });
        });

        it('should mark feature as degraded when no recovery possible', async () => {
            const error = new APIError('Not found', 404, '/api/test');

            const result = await manager.recoverFromAPIError(
                error,
                'test operation'
            );

            expect(result.success).toBe(false);
            expect(manager.isFeatureDegraded('test operation')).toBe(true);
        });
    });

    describe('recoverFromNetworkError', () => {
        it('should use cached data on network error', async () => {
            manager.cacheData('network op', { cached: 'data' });

            const error = new NetworkError('Connection failed');

            const result = await manager.recoverFromNetworkError(
                error,
                'network op'
            );

            expect(result.success).toBe(true);
            expect(result.data).toEqual({ cached: 'data' });
        });
    });

    describe('withRecovery', () => {
        it('should cache successful result', async () => {
            const result = await manager.withRecovery(
                'op',
                () => Promise.resolve({ success: true })
            );

            expect(result).toEqual({ success: true });
            expect(manager.getCachedData('op')).toEqual({ success: true });
        });

        it('should restore degraded feature on success', async () => {
            manager.markFeatureDegraded('op', 'was broken');

            await manager.withRecovery(
                'op',
                () => Promise.resolve('success')
            );

            expect(manager.isFeatureDegraded('op')).toBe(false);
        });

        it('should use fallback on API error with cache', async () => {
            manager.cacheData('op', 'cached value');

            const result = await manager.withRecovery(
                'op',
                () => Promise.reject(new APIError('Error', 500, '/')),
                'fallback value'
            );

            expect(result).toBe('cached value');
        });
    });

    describe('cleanup', () => {
        it('should clear all state on cleanup', () => {
            manager.cacheData('op', 'data');
            manager.saveStateSnapshot('snap', {}, 'op');
            manager.markFeatureDegraded('feature', 'reason');

            manager.cleanup();

            expect(manager.getCachedData('op')).toBeNull();
            expect(manager.getSnapshot('snap')).toBeNull();
            expect(manager.getDegradedFeatures()).toHaveLength(0);
        });
    });
});
