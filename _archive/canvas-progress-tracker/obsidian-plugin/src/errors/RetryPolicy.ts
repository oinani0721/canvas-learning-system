/**
 * Retry Policy - Canvas Review System
 *
 * Implements intelligent retry logic with exponential backoff
 * for network requests and other recoverable operations.
 *
 * @module errors/RetryPolicy
 * @version 1.0.0
 *
 * ✅ Verified from Story 13.7 Dev Notes (RetryPolicy design)
 */

import { PluginError, isPluginError } from './PluginError';
import { ErrorNotifier } from './ErrorNotifier';

/**
 * Retry policy configuration options
 */
export interface RetryPolicyConfig {
    /** Maximum number of retry attempts */
    maxRetries: number;
    /** Initial delay in milliseconds */
    initialDelay: number;
    /** Maximum delay between retries in milliseconds */
    maxDelay: number;
    /** Backoff multiplier for each retry */
    backoffFactor: number;
    /** Whether to add jitter to delays */
    jitter: boolean;
    /** Jitter factor (0-1, percentage of delay to randomize) */
    jitterFactor: number;
}

/**
 * Retry attempt callback information
 */
export interface RetryAttemptInfo {
    /** Current attempt number (1-based) */
    attempt: number;
    /** Delay before this retry in ms */
    delay: number;
    /** The error that triggered the retry */
    error: Error;
    /** Total elapsed time in ms */
    elapsedTime: number;
}

/**
 * Callback type for retry events
 */
export type OnRetryCallback = (info: RetryAttemptInfo) => void;

/**
 * Default retry policy configuration
 *
 * ✅ Verified from Story 13.7 Dev Notes (retry parameters)
 */
export const DEFAULT_RETRY_CONFIG: RetryPolicyConfig = {
    maxRetries: 3,
    initialDelay: 1000,    // 1 second
    maxDelay: 30000,       // 30 seconds
    backoffFactor: 2,
    jitter: true,
    jitterFactor: 0.1      // 10% jitter
};

/**
 * HTTP status codes that should trigger a retry
 */
const RETRYABLE_STATUS_CODES = new Set([
    408, // Request Timeout
    429, // Too Many Requests
    500, // Internal Server Error
    502, // Bad Gateway
    503, // Service Unavailable
    504  // Gateway Timeout
]);

/**
 * Retry Policy class
 *
 * Provides exponential backoff retry logic for operations
 * that may fail transiently.
 *
 * ✅ Verified from Story 13.7 Dev Notes (RetryPolicy class)
 */
export class RetryPolicy {
    private config: RetryPolicyConfig;
    private notifier: ErrorNotifier | null = null;

    /**
     * Creates a new RetryPolicy
     *
     * @param config - Partial configuration (merged with defaults)
     * @param notifier - Optional ErrorNotifier for showing retry progress
     */
    constructor(
        config: Partial<RetryPolicyConfig> = {},
        notifier?: ErrorNotifier
    ) {
        this.config = { ...DEFAULT_RETRY_CONFIG, ...config };
        this.notifier = notifier || null;
    }

    /**
     * Executes an operation with retry logic
     *
     * @param operation - The async operation to execute
     * @param onRetry - Optional callback for each retry attempt
     * @returns The result of the operation
     * @throws The last error if all retries fail
     *
     * ✅ Verified from Story 13.7 Dev Notes (executeWithRetry method)
     */
    async executeWithRetry<T>(
        operation: () => Promise<T>,
        onRetry?: OnRetryCallback
    ): Promise<T> {
        let lastError: Error | null = null;
        const startTime = Date.now();

        for (let attempt = 1; attempt <= this.config.maxRetries + 1; attempt++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error as Error;

                // Check if error is recoverable
                if (!this.shouldRetry(error)) {
                    throw error;
                }

                // Check if we've exhausted retries
                if (attempt > this.config.maxRetries) {
                    throw error;
                }

                // Calculate delay with exponential backoff
                const delay = this.calculateDelay(attempt);
                const elapsedTime = Date.now() - startTime;

                // Notify about retry
                const retryInfo: RetryAttemptInfo = {
                    attempt,
                    delay,
                    error: lastError,
                    elapsedTime
                };

                // Call user callback
                onRetry?.(retryInfo);

                // Show notification if notifier is available
                if (this.notifier) {
                    this.notifier.showRetryProgress(
                        attempt,
                        this.config.maxRetries,
                        delay
                    );
                }

                // Wait before retry
                await this.sleep(delay);
            }
        }

        // Should never reach here, but TypeScript needs it
        throw lastError || new Error('Retry failed');
    }

    /**
     * Determines if an error should trigger a retry
     *
     * @param error - The error to check
     * @returns true if the operation should be retried
     */
    shouldRetry(error: unknown): boolean {
        // PluginError has explicit recoverable flag
        if (isPluginError(error)) {
            return error.recoverable;
        }

        // Check for HTTP status code in error
        const statusCode = this.extractStatusCode(error);
        if (statusCode !== null) {
            return RETRYABLE_STATUS_CODES.has(statusCode);
        }

        // Check for network-related errors
        if (error instanceof TypeError) {
            const message = error.message.toLowerCase();
            return (
                message.includes('fetch') ||
                message.includes('network') ||
                message.includes('connection')
            );
        }

        // Check for timeout errors
        if (error instanceof Error) {
            const name = error.name.toLowerCase();
            const message = error.message.toLowerCase();
            return (
                name.includes('timeout') ||
                message.includes('timeout') ||
                message.includes('timed out')
            );
        }

        // Default: don't retry unknown errors
        return false;
    }

    /**
     * Calculates delay for a given retry attempt
     *
     * @param attempt - The retry attempt number (1-based)
     * @returns Delay in milliseconds
     */
    calculateDelay(attempt: number): number {
        // Exponential backoff
        let delay = this.config.initialDelay *
            Math.pow(this.config.backoffFactor, attempt - 1);

        // Cap at max delay
        delay = Math.min(delay, this.config.maxDelay);

        // Add jitter if enabled
        if (this.config.jitter) {
            const jitterAmount = delay * this.config.jitterFactor;
            delay += (Math.random() * 2 - 1) * jitterAmount;
        }

        return Math.round(delay);
    }

    /**
     * Gets the current configuration
     */
    getConfig(): Readonly<RetryPolicyConfig> {
        return { ...this.config };
    }

    /**
     * Creates a new RetryPolicy with modified config
     *
     * @param overrides - Configuration overrides
     */
    withConfig(overrides: Partial<RetryPolicyConfig>): RetryPolicy {
        return new RetryPolicy(
            { ...this.config, ...overrides },
            this.notifier || undefined
        );
    }

    // ========== Static Factory Methods ==========

    /**
     * Creates a policy optimized for network requests
     */
    static forNetworkRequests(notifier?: ErrorNotifier): RetryPolicy {
        return new RetryPolicy({
            maxRetries: 3,
            initialDelay: 1000,
            maxDelay: 30000,
            backoffFactor: 2,
            jitter: true
        }, notifier);
    }

    /**
     * Creates a policy with no retries
     */
    static noRetry(): RetryPolicy {
        return new RetryPolicy({
            maxRetries: 0,
            initialDelay: 0,
            maxDelay: 0,
            backoffFactor: 1,
            jitter: false
        });
    }

    /**
     * Creates a policy for quick retries (e.g., local operations)
     */
    static quickRetry(notifier?: ErrorNotifier): RetryPolicy {
        return new RetryPolicy({
            maxRetries: 2,
            initialDelay: 100,
            maxDelay: 1000,
            backoffFactor: 2,
            jitter: true
        }, notifier);
    }

    /**
     * Creates a policy for aggressive retries (many attempts)
     */
    static aggressiveRetry(notifier?: ErrorNotifier): RetryPolicy {
        return new RetryPolicy({
            maxRetries: 5,
            initialDelay: 500,
            maxDelay: 60000,
            backoffFactor: 2,
            jitter: true
        }, notifier);
    }

    // ========== Private Methods ==========

    /**
     * Extracts HTTP status code from error if present
     */
    private extractStatusCode(error: unknown): number | null {
        if (error && typeof error === 'object') {
            const obj = error as Record<string, unknown>;

            // Check common status code properties
            if (typeof obj.status === 'number') return obj.status;
            if (typeof obj.statusCode === 'number') return obj.statusCode;
            if (typeof obj.code === 'number' && obj.code >= 100 && obj.code < 600) {
                return obj.code;
            }

            // Check for response object
            if (obj.response && typeof obj.response === 'object') {
                const response = obj.response as Record<string, unknown>;
                if (typeof response.status === 'number') return response.status;
            }
        }

        return null;
    }

    /**
     * Sleep for a given duration
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Circuit Breaker for preventing cascade failures
 *
 * Tracks failures and temporarily disables operations
 * when failure rate is too high.
 */
export class CircuitBreaker {
    private failures: number = 0;
    private lastFailure: number = 0;
    private isOpen: boolean = false;

    /**
     * Creates a new CircuitBreaker
     *
     * @param failureThreshold - Number of failures before opening
     * @param resetTimeout - Time in ms before attempting to close
     */
    constructor(
        private failureThreshold: number = 5,
        private resetTimeout: number = 30000
    ) {}

    /**
     * Checks if the circuit is open (operations should be blocked)
     */
    isCircuitOpen(): boolean {
        if (!this.isOpen) return false;

        // Check if reset timeout has passed
        if (Date.now() - this.lastFailure > this.resetTimeout) {
            this.reset();
            return false;
        }

        return true;
    }

    /**
     * Records a successful operation
     */
    recordSuccess(): void {
        this.failures = 0;
        this.isOpen = false;
    }

    /**
     * Records a failed operation
     */
    recordFailure(): void {
        this.failures++;
        this.lastFailure = Date.now();

        if (this.failures >= this.failureThreshold) {
            this.isOpen = true;
        }
    }

    /**
     * Resets the circuit breaker
     */
    reset(): void {
        this.failures = 0;
        this.isOpen = false;
        this.lastFailure = 0;
    }

    /**
     * Gets current failure count
     */
    getFailureCount(): number {
        return this.failures;
    }

    /**
     * Executes an operation through the circuit breaker
     *
     * @param operation - The operation to execute
     * @param retryPolicy - Optional retry policy
     */
    async execute<T>(
        operation: () => Promise<T>,
        retryPolicy?: RetryPolicy
    ): Promise<T> {
        if (this.isCircuitOpen()) {
            throw new Error('Circuit breaker is open - operation blocked');
        }

        try {
            const result = retryPolicy
                ? await retryPolicy.executeWithRetry(operation)
                : await operation();

            this.recordSuccess();
            return result;
        } catch (error) {
            this.recordFailure();
            throw error;
        }
    }
}
