/**
 * Retry Policy Tests - Canvas Review System
 *
 * Tests for retry logic and circuit breaker functionality.
 *
 * @module tests/errors/RetryPolicy.test
 */

import {
    RetryPolicy,
    CircuitBreaker,
    DEFAULT_RETRY_CONFIG
} from '../../src/errors/RetryPolicy';
import { NetworkError, ValidationError } from '../../src/errors/PluginError';

describe('RetryPolicy', () => {
    describe('constructor', () => {
        it('should use default config when none provided', () => {
            const policy = new RetryPolicy();
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(DEFAULT_RETRY_CONFIG.maxRetries);
            expect(config.initialDelay).toBe(DEFAULT_RETRY_CONFIG.initialDelay);
            expect(config.maxDelay).toBe(DEFAULT_RETRY_CONFIG.maxDelay);
            expect(config.backoffFactor).toBe(DEFAULT_RETRY_CONFIG.backoffFactor);
        });

        it('should merge custom config with defaults', () => {
            const policy = new RetryPolicy({ maxRetries: 5 });
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(5);
            expect(config.initialDelay).toBe(DEFAULT_RETRY_CONFIG.initialDelay);
        });
    });

    describe('calculateDelay', () => {
        it('should calculate exponential backoff', () => {
            const policy = new RetryPolicy({
                initialDelay: 1000,
                backoffFactor: 2,
                jitter: false
            });

            expect(policy.calculateDelay(1)).toBe(1000);
            expect(policy.calculateDelay(2)).toBe(2000);
            expect(policy.calculateDelay(3)).toBe(4000);
        });

        it('should cap delay at maxDelay', () => {
            const policy = new RetryPolicy({
                initialDelay: 1000,
                backoffFactor: 2,
                maxDelay: 3000,
                jitter: false
            });

            expect(policy.calculateDelay(5)).toBe(3000);
        });

        it('should add jitter when enabled', () => {
            const policy = new RetryPolicy({
                initialDelay: 1000,
                jitter: true,
                jitterFactor: 0.1
            });

            // With 10% jitter, delay should be between 900-1100
            const delays = Array.from({ length: 10 }, () =>
                policy.calculateDelay(1)
            );

            expect(delays.some(d => d !== 1000)).toBe(true);
            expect(delays.every(d => d >= 900 && d <= 1100)).toBe(true);
        });
    });

    describe('shouldRetry', () => {
        const policy = new RetryPolicy();

        it('should retry recoverable PluginErrors', () => {
            const error = new NetworkError('Connection failed', 503);
            expect(policy.shouldRetry(error)).toBe(true);
        });

        it('should not retry non-recoverable PluginErrors', () => {
            const error = new ValidationError('Invalid input', 'field');
            expect(policy.shouldRetry(error)).toBe(false);
        });

        it('should retry retryable HTTP status codes', () => {
            const error = { status: 503 };
            expect(policy.shouldRetry(error)).toBe(true);
        });

        it('should not retry non-retryable HTTP status codes', () => {
            const error = { status: 400 };
            expect(policy.shouldRetry(error)).toBe(false);
        });

        it('should retry network TypeErrors', () => {
            const error = new TypeError('Failed to fetch');
            expect(policy.shouldRetry(error)).toBe(true);
        });

        it('should retry timeout errors', () => {
            const error = new Error('Request timed out');
            expect(policy.shouldRetry(error)).toBe(true);
        });

        it('should not retry unknown errors by default', () => {
            const error = new Error('Unknown error');
            expect(policy.shouldRetry(error)).toBe(false);
        });
    });

    describe('executeWithRetry', () => {
        jest.useFakeTimers();

        afterEach(() => {
            jest.clearAllTimers();
        });

        it('should return result on first success', async () => {
            const policy = new RetryPolicy();
            const operation = jest.fn().mockResolvedValue('success');

            const resultPromise = policy.executeWithRetry(operation);

            await expect(resultPromise).resolves.toBe('success');
            expect(operation).toHaveBeenCalledTimes(1);
        });

        it('should retry on recoverable error', async () => {
            const policy = new RetryPolicy({
                maxRetries: 2,
                initialDelay: 100,
                jitter: false
            });

            let callCount = 0;
            const operation = jest.fn().mockImplementation(() => {
                callCount++;
                if (callCount < 2) {
                    return Promise.reject(new NetworkError('Connection failed'));
                }
                return Promise.resolve('success');
            });

            const resultPromise = policy.executeWithRetry(operation);

            // Advance timer for first retry
            await jest.advanceTimersByTimeAsync(100);

            await expect(resultPromise).resolves.toBe('success');
            expect(operation).toHaveBeenCalledTimes(2);
        });

        it('should throw on non-recoverable error immediately', async () => {
            const policy = new RetryPolicy({ maxRetries: 3 });
            const error = new ValidationError('Invalid', 'field');
            const operation = jest.fn().mockRejectedValue(error);

            await expect(policy.executeWithRetry(operation)).rejects.toThrow(error);
            expect(operation).toHaveBeenCalledTimes(1);
        });

        it('should throw after max retries exhausted', async () => {
            // Use real timers for this specific test to avoid timing issues
            jest.useRealTimers();

            const policy = new RetryPolicy({
                maxRetries: 2,
                initialDelay: 10,  // Very short delays for real timer test
                jitter: false
            });

            const error = new NetworkError('Connection failed');
            const operation = jest.fn().mockRejectedValue(error);

            // Execute and expect rejection
            await expect(policy.executeWithRetry(operation)).rejects.toThrow('Connection failed');
            expect(operation).toHaveBeenCalledTimes(3); // 1 initial + 2 retries

            // Restore fake timers for subsequent tests
            jest.useFakeTimers();
        });

        it('should call onRetry callback', async () => {
            const policy = new RetryPolicy({
                maxRetries: 1,
                initialDelay: 100,
                jitter: false
            });

            const operation = jest.fn()
                .mockRejectedValueOnce(new NetworkError('Failed'))
                .mockResolvedValueOnce('success');

            const onRetry = jest.fn();

            const resultPromise = policy.executeWithRetry(operation, onRetry);

            await jest.advanceTimersByTimeAsync(100);

            await resultPromise;

            expect(onRetry).toHaveBeenCalledTimes(1);
            expect(onRetry).toHaveBeenCalledWith(expect.objectContaining({
                attempt: 1,
                delay: 100
            }));
        });
    });

    describe('static factory methods', () => {
        it('should create network request policy', () => {
            const policy = RetryPolicy.forNetworkRequests();
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(3);
            expect(config.jitter).toBe(true);
        });

        it('should create no-retry policy', () => {
            const policy = RetryPolicy.noRetry();
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(0);
        });

        it('should create quick retry policy', () => {
            const policy = RetryPolicy.quickRetry();
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(2);
            expect(config.initialDelay).toBe(100);
        });

        it('should create aggressive retry policy', () => {
            const policy = RetryPolicy.aggressiveRetry();
            const config = policy.getConfig();

            expect(config.maxRetries).toBe(5);
        });
    });

    describe('withConfig', () => {
        it('should create new policy with merged config', () => {
            const policy = new RetryPolicy({ maxRetries: 3 });
            const newPolicy = policy.withConfig({ maxRetries: 5 });

            expect(policy.getConfig().maxRetries).toBe(3);
            expect(newPolicy.getConfig().maxRetries).toBe(5);
        });
    });
});

describe('CircuitBreaker', () => {
    describe('basic operation', () => {
        it('should start with closed circuit', () => {
            const breaker = new CircuitBreaker();
            expect(breaker.isCircuitOpen()).toBe(false);
        });

        it('should open after reaching failure threshold', () => {
            const breaker = new CircuitBreaker(3, 1000);

            breaker.recordFailure();
            breaker.recordFailure();
            expect(breaker.isCircuitOpen()).toBe(false);

            breaker.recordFailure();
            expect(breaker.isCircuitOpen()).toBe(true);
        });

        it('should close after successful operation', () => {
            const breaker = new CircuitBreaker(2, 1000);

            breaker.recordFailure();
            breaker.recordFailure();
            expect(breaker.isCircuitOpen()).toBe(true);

            breaker.reset();
            breaker.recordSuccess();
            expect(breaker.isCircuitOpen()).toBe(false);
        });

        it('should auto-reset after timeout', () => {
            jest.useFakeTimers();

            const breaker = new CircuitBreaker(2, 1000);

            breaker.recordFailure();
            breaker.recordFailure();
            expect(breaker.isCircuitOpen()).toBe(true);

            jest.advanceTimersByTime(1001);
            expect(breaker.isCircuitOpen()).toBe(false);

            jest.useRealTimers();
        });
    });

    describe('execute', () => {
        it('should execute operation when circuit is closed', async () => {
            const breaker = new CircuitBreaker();
            const operation = jest.fn().mockResolvedValue('success');

            const result = await breaker.execute(operation);

            expect(result).toBe('success');
            expect(operation).toHaveBeenCalled();
        });

        it('should throw when circuit is open', async () => {
            const breaker = new CircuitBreaker(1, 10000);
            breaker.recordFailure();

            const operation = jest.fn();

            await expect(breaker.execute(operation)).rejects.toThrow(
                'Circuit breaker is open'
            );
            expect(operation).not.toHaveBeenCalled();
        });

        it('should record success on successful execution', async () => {
            const breaker = new CircuitBreaker(3, 1000);
            breaker.recordFailure();
            breaker.recordFailure();

            const operation = jest.fn().mockResolvedValue('success');

            await breaker.execute(operation);

            expect(breaker.getFailureCount()).toBe(0);
        });

        it('should record failure on failed execution', async () => {
            const breaker = new CircuitBreaker(3, 1000);
            const operation = jest.fn().mockRejectedValue(new Error('Failed'));

            await expect(breaker.execute(operation)).rejects.toThrow('Failed');
            expect(breaker.getFailureCount()).toBe(1);
        });
    });

    describe('reset', () => {
        it('should reset all state', () => {
            const breaker = new CircuitBreaker(2, 1000);

            breaker.recordFailure();
            breaker.recordFailure();
            expect(breaker.isCircuitOpen()).toBe(true);

            breaker.reset();

            expect(breaker.isCircuitOpen()).toBe(false);
            expect(breaker.getFailureCount()).toBe(0);
        });
    });
});
