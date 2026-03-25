/**
 * Error Recovery Manager - Canvas Review System
 *
 * Provides error recovery strategies including automatic degradation,
 * manual recovery options, and state rollback mechanisms.
 *
 * @module errors/ErrorRecoveryManager
 * @version 1.0.0
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorRecoveryManager design)
 */

import type { App } from 'obsidian';
import { PluginError, APIError, NetworkError, isPluginError } from './PluginError';
import { ErrorNotifier } from './ErrorNotifier';
import { RecoveryModal, RecoveryOptions } from '../modals/RecoveryModal';

/**
 * Recovery action types
 */
export type RecoveryAction =
    | 'retry'
    | 'use_cache'
    | 'clear_cache'
    | 'restart_plugin'
    | 'ignore'
    | 'report';

/**
 * Recovery result
 */
export interface RecoveryResult<T = unknown> {
    /** Whether recovery was successful */
    success: boolean;
    /** Recovered data (if any) */
    data?: T;
    /** The action that was taken */
    action: RecoveryAction;
    /** Message describing the result */
    message: string;
}

/**
 * State snapshot for rollback
 */
interface StateSnapshot<T> {
    id: string;
    timestamp: number;
    state: T;
    operation: string;
}

/**
 * Error Recovery Manager
 *
 * Implements various error recovery strategies:
 * - Automatic degradation (cache fallback)
 * - Manual recovery options (user-initiated)
 * - State rollback (undo failed operations)
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorRecoveryManager class)
 */
export class ErrorRecoveryManager {
    private app: App;
    private notifier: ErrorNotifier;

    // State management for rollback
    private stateSnapshots: Map<string, StateSnapshot<unknown>> = new Map();
    private maxSnapshots: number = 10;

    // Cache for degraded mode
    private cache: Map<string, { data: unknown; timestamp: number }> = new Map();
    private cacheMaxAge: number = 5 * 60 * 1000; // 5 minutes

    // Degraded features tracking
    private degradedFeatures: Set<string> = new Set();

    /**
     * Creates a new ErrorRecoveryManager
     *
     * @param app - Obsidian App instance
     * @param notifier - ErrorNotifier for user notifications
     */
    constructor(app: App, notifier: ErrorNotifier) {
        this.app = app;
        this.notifier = notifier;
    }

    /**
     * Recovers from an API error with automatic strategies
     *
     * @param error - The API error
     * @param operation - Description of the failed operation
     * @param fallbackData - Optional cached data to use
     * @returns Recovery result
     *
     * ✅ Verified from Story 13.7 Dev Notes (recoverFromAPIError method)
     */
    async recoverFromAPIError<T>(
        error: APIError,
        operation: string,
        fallbackData?: T
    ): Promise<RecoveryResult<T>> {
        // Strategy 1: Check internal cache first (most recent data)
        const cached = this.getCachedData<T>(operation);
        if (cached) {
            this.notifier.showCacheFallback();
            this.markFeatureDegraded(operation, 'Using internal cache');

            return {
                success: true,
                data: cached,
                action: 'use_cache',
                message: 'API服务暂时不可用，已使用内部缓存数据'
            };
        }

        // Strategy 2: Use provided fallback data
        if (fallbackData !== undefined) {
            this.notifier.showCacheFallback();
            this.markFeatureDegraded(operation, 'Using fallback data');

            return {
                success: true,
                data: fallbackData,
                action: 'use_cache',
                message: 'API服务暂时不可用，已使用备用数据'
            };
        }

        // Strategy 3: For recoverable errors, offer manual recovery
        if (error.recoverable) {
            return this.promptManualRecovery<T>(error, operation);
        }

        // Strategy 4: Graceful degradation (disable feature)
        this.markFeatureDegraded(operation, error.message);
        this.notifier.showDegradedMode(operation, error.getUserMessage());

        return {
            success: false,
            action: 'ignore',
            message: `${operation}功能暂时不可用，请稍后重试`
        };
    }

    /**
     * Recovers from a network error
     *
     * @param error - The network error
     * @param operation - Description of the failed operation
     */
    async recoverFromNetworkError<T>(
        error: NetworkError,
        operation: string
    ): Promise<RecoveryResult<T>> {
        // Check for cached data first
        const cached = this.getCachedData<T>(operation);
        if (cached) {
            this.notifier.showCacheFallback();
            return {
                success: true,
                data: cached,
                action: 'use_cache',
                message: '网络连接失败，已使用缓存数据'
            };
        }

        // Network errors are typically recoverable - offer retry
        return this.promptManualRecovery<T>(error, operation);
    }

    /**
     * Shows manual recovery options to the user
     *
     * @param error - The error that occurred
     * @param operation - Description of the failed operation
     *
     * ✅ Verified from Story 13.7 Dev Notes (promptManualRecovery method)
     */
    async promptManualRecovery<T>(
        error: PluginError,
        operation: string
    ): Promise<RecoveryResult<T>> {
        return new Promise((resolve) => {
            const options: RecoveryOptions = {
                retry: () => {
                    resolve({
                        success: false,
                        action: 'retry',
                        message: '用户选择重试'
                    });
                },
                clearCache: () => {
                    this.clearCache();
                    this.notifier.showInfo('缓存已清除');
                    resolve({
                        success: false,
                        action: 'clear_cache',
                        message: '用户选择清除缓存'
                    });
                },
                reportIssue: () => {
                    resolve({
                        success: false,
                        action: 'report',
                        message: '用户选择报告问题'
                    });
                },
                ignore: () => {
                    resolve({
                        success: false,
                        action: 'ignore',
                        message: '用户选择忽略错误'
                    });
                }
            };

            const modal = new RecoveryModal(
                this.app,
                error,
                operation,
                options
            );

            modal.open();
        });
    }

    // ========== State Rollback ==========

    /**
     * Saves a state snapshot for potential rollback
     *
     * @param id - Unique identifier for this snapshot
     * @param state - The state to save
     * @param operation - Description of the operation
     */
    saveStateSnapshot<T>(id: string, state: T, operation: string): void {
        // Remove oldest snapshot if at limit
        if (this.stateSnapshots.size >= this.maxSnapshots) {
            const oldestKey = this.stateSnapshots.keys().next().value;
            if (oldestKey) {
                this.stateSnapshots.delete(oldestKey);
            }
        }

        this.stateSnapshots.set(id, {
            id,
            timestamp: Date.now(),
            state: structuredClone(state),
            operation
        });
    }

    /**
     * Rolls back to a saved state
     *
     * @param id - ID of the snapshot to restore
     * @returns The restored state, or null if not found
     */
    rollbackState<T>(id: string): T | null {
        const snapshot = this.stateSnapshots.get(id);
        if (!snapshot) {
            return null;
        }

        this.stateSnapshots.delete(id);
        this.notifier.showInfo(`已回滚到操作前状态: ${snapshot.operation}`);

        return snapshot.state as T;
    }

    /**
     * Gets a saved snapshot without removing it
     */
    getSnapshot<T>(id: string): T | null {
        const snapshot = this.stateSnapshots.get(id);
        return snapshot ? (snapshot.state as T) : null;
    }

    /**
     * Clears all state snapshots
     */
    clearSnapshots(): void {
        this.stateSnapshots.clear();
    }

    // ========== Cache Management ==========

    /**
     * Caches data for potential fallback
     *
     * @param key - Cache key (typically operation name)
     * @param data - Data to cache
     */
    cacheData<T>(key: string, data: T): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Gets cached data if still valid
     *
     * @param key - Cache key
     */
    getCachedData<T>(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        // Check if cache is still valid
        if (Date.now() - entry.timestamp > this.cacheMaxAge) {
            this.cache.delete(key);
            return null;
        }

        return entry.data as T;
    }

    /**
     * Clears all cached data
     */
    clearCache(): void {
        this.cache.clear();
    }

    /**
     * Sets cache max age
     */
    setCacheMaxAge(ageMs: number): void {
        this.cacheMaxAge = ageMs;
    }

    // ========== Degraded Mode ==========

    /**
     * Marks a feature as degraded
     */
    markFeatureDegraded(feature: string, reason: string): void {
        this.degradedFeatures.add(feature);
        console.warn(`Canvas复习系统: ${feature} 已降级 - ${reason}`);
    }

    /**
     * Checks if a feature is degraded
     */
    isFeatureDegraded(feature: string): boolean {
        return this.degradedFeatures.has(feature);
    }

    /**
     * Restores a degraded feature
     */
    restoreFeature(feature: string): void {
        if (this.degradedFeatures.delete(feature)) {
            this.notifier.showSuccess(`${feature} 功能已恢复`);
        }
    }

    /**
     * Gets list of degraded features
     */
    getDegradedFeatures(): string[] {
        return Array.from(this.degradedFeatures);
    }

    /**
     * Clears all degraded feature flags
     */
    clearDegradedFeatures(): void {
        this.degradedFeatures.clear();
    }

    // ========== Utility ==========

    /**
     * Wraps an async operation with automatic recovery
     *
     * @param operation - The operation name
     * @param fn - The async function to execute
     * @param fallbackData - Optional fallback data
     */
    async withRecovery<T>(
        operation: string,
        fn: () => Promise<T>,
        fallbackData?: T
    ): Promise<T> {
        try {
            const result = await fn();

            // Cache successful result
            this.cacheData(operation, result);

            // Restore feature if it was degraded
            this.restoreFeature(operation);

            return result;
        } catch (error) {
            let recoveryResult: RecoveryResult<T>;

            if (error instanceof APIError) {
                recoveryResult = await this.recoverFromAPIError(
                    error,
                    operation,
                    fallbackData
                );
            } else if (error instanceof NetworkError) {
                recoveryResult = await this.recoverFromNetworkError(
                    error,
                    operation
                );
            } else if (isPluginError(error)) {
                recoveryResult = await this.promptManualRecovery(error, operation);
            } else {
                throw error;
            }

            if (recoveryResult.success && recoveryResult.data !== undefined) {
                return recoveryResult.data;
            }

            // If retry was selected, throw to let caller handle
            if (recoveryResult.action === 'retry') {
                throw error;
            }

            // If we have fallback data, use it
            if (fallbackData !== undefined) {
                return fallbackData;
            }

            throw error;
        }
    }

    /**
     * Cleans up resources
     */
    cleanup(): void {
        this.cache.clear();
        this.stateSnapshots.clear();
        this.degradedFeatures.clear();
    }
}
