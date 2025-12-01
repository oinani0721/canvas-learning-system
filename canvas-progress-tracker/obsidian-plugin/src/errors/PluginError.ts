/**
 * Plugin Error Classes - Canvas Review System
 *
 * Defines the error type hierarchy for the Obsidian plugin.
 * Aligns with backend error types from canvas_exceptions.py
 *
 * @module errors/PluginError
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin API documentation)
 * ✅ Verified from Story 13.7 Dev Notes (Error Classification Design)
 */

/**
 * Error severity levels for user notifications
 * - critical: Red notice, 10s duration, indicates system-level failures
 * - warning: Orange notice, 5s duration, indicates recoverable issues
 * - info: Default notice, 3s duration, informational messages
 */
export type ErrorSeverity = 'critical' | 'warning' | 'info';

/**
 * Base class for all plugin errors
 *
 * Provides structured error information including severity,
 * context data, and recoverability status.
 *
 * ✅ Verified from Story 13.7 Dev Notes (PluginError base class design)
 */
export abstract class PluginError extends Error {
    /**
     * Creates a new PluginError
     *
     * @param message - Human-readable error message
     * @param severity - Error severity level for UI display
     * @param context - Additional context data for debugging
     * @param recoverable - Whether the error can be recovered from (enables retry)
     */
    constructor(
        message: string,
        public severity: ErrorSeverity,
        public context?: Record<string, unknown>,
        public recoverable: boolean = true
    ) {
        super(message);
        this.name = this.constructor.name;

        // Maintains proper stack trace for where our error was thrown (only V8)
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
    }

    /**
     * Serializes error for logging
     */
    toJSON(): Record<string, unknown> {
        return {
            name: this.name,
            message: this.message,
            severity: this.severity,
            context: this.context,
            recoverable: this.recoverable,
            stack: this.stack
        };
    }

    /**
     * Creates a user-friendly error message
     */
    getUserMessage(): string {
        return this.message;
    }
}

/**
 * Network-related errors (retryable)
 *
 * Used for connection failures, timeouts, and HTTP errors.
 * Aligns with backend connection errors.
 *
 * ✅ Verified from Story 13.7 Dev Notes (NetworkError design)
 */
export class NetworkError extends PluginError {
    /**
     * Creates a new NetworkError
     *
     * @param message - Error description
     * @param statusCode - HTTP status code if available
     * @param context - Additional context (e.g., URL, timeout value)
     */
    constructor(
        message: string,
        public statusCode?: number,
        context?: Record<string, unknown>
    ) {
        // Network errors are always critical and typically recoverable
        super(message, 'critical', { ...context, statusCode }, true);
    }

    getUserMessage(): string {
        if (this.statusCode) {
            switch (this.statusCode) {
                case 408:
                    return '请求超时，请检查网络连接后重试';
                case 500:
                case 502:
                case 503:
                case 504:
                    return 'API服务器暂时不可用，请稍后重试';
                default:
                    return `网络错误 (${this.statusCode}): ${this.message}`;
            }
        }
        return '无法连接到API服务器，请检查网络设置';
    }
}

/**
 * Canvas file parsing errors (not retryable)
 *
 * Used when Canvas JSON is malformed or missing required fields.
 *
 * ✅ Verified from Story 13.7 Dev Notes (CanvasParseError design)
 */
export class CanvasParseError extends PluginError {
    /**
     * Creates a new CanvasParseError
     *
     * @param message - Error description
     * @param filePath - Path to the problematic Canvas file
     * @param context - Additional context (e.g., line number, expected format)
     */
    constructor(
        message: string,
        public filePath: string,
        context?: Record<string, unknown>
    ) {
        // Parse errors are critical and NOT recoverable (need manual fix)
        super(message, 'critical', { ...context, filePath }, false);
    }

    getUserMessage(): string {
        return `Canvas文件解析失败: ${this.message}\n文件: ${this.filePath}`;
    }
}

/**
 * API business logic errors (partially retryable)
 *
 * Used for API response errors. 5xx errors are retryable, 4xx are not.
 * Aligns with backend exceptions (CanvasNotFoundError, ValidationError, etc.)
 *
 * ✅ Verified from Story 13.7 Dev Notes (APIError design)
 * ✅ Verified from backend/app/exceptions/canvas_exceptions.py
 */
export class APIError extends PluginError {
    /**
     * Creates a new APIError
     *
     * @param message - Error description from API
     * @param code - HTTP status code
     * @param apiEndpoint - The API endpoint that failed
     * @param context - Additional context (e.g., request body, response)
     */
    constructor(
        message: string,
        public code: number,
        public apiEndpoint: string,
        context?: Record<string, unknown>
    ) {
        // 5xx errors are critical and retryable, 4xx are warnings and not retryable
        const isServerError = code >= 500;
        super(
            message,
            isServerError ? 'critical' : 'warning',
            { ...context, apiEndpoint, code },
            isServerError
        );
    }

    getUserMessage(): string {
        switch (this.code) {
            case 400:
                return `请求参数无效: ${this.message}`;
            case 401:
                return '未授权访问，请检查认证设置';
            case 403:
                return '访问被拒绝';
            case 404:
                return `资源未找到: ${this.message}`;
            case 429:
                return 'API请求过于频繁，请稍后重试';
            case 500:
                return 'API服务器内部错误，请稍后重试';
            default:
                return `API错误 (${this.code}): ${this.message}`;
        }
    }
}

/**
 * Validation errors (not retryable)
 *
 * Used for input validation failures. Users need to fix the input.
 * Aligns with backend ValidationError (400).
 *
 * ✅ Verified from Story 13.7 Dev Notes (ValidationError design)
 */
export class ValidationError extends PluginError {
    /**
     * Creates a new ValidationError
     *
     * @param message - Validation error description
     * @param field - The field that failed validation
     * @param context - Additional context (e.g., expected format, constraints)
     */
    constructor(
        message: string,
        public field: string,
        context?: Record<string, unknown>
    ) {
        // Validation errors are warnings and NOT recoverable (need user input fix)
        super(message, 'warning', { ...context, field }, false);
    }

    getUserMessage(): string {
        return `验证失败 (${this.field}): ${this.message}`;
    }
}

/**
 * Configuration errors (not retryable)
 *
 * Used when plugin settings are invalid or missing.
 */
export class ConfigurationError extends PluginError {
    /**
     * Creates a new ConfigurationError
     *
     * @param message - Configuration error description
     * @param settingKey - The setting that is misconfigured
     * @param context - Additional context
     */
    constructor(
        message: string,
        public settingKey: string,
        context?: Record<string, unknown>
    ) {
        super(message, 'warning', { ...context, settingKey }, false);
    }

    getUserMessage(): string {
        return `配置错误 (${this.settingKey}): ${this.message}\n请在插件设置中修正`;
    }
}

/**
 * Timeout errors (retryable)
 *
 * Used when operations exceed time limits.
 */
export class TimeoutError extends PluginError {
    /**
     * Creates a new TimeoutError
     *
     * @param message - Timeout description
     * @param operation - The operation that timed out
     * @param timeoutMs - The timeout value in milliseconds
     * @param context - Additional context
     */
    constructor(
        message: string,
        public operation: string,
        public timeoutMs: number,
        context?: Record<string, unknown>
    ) {
        super(message, 'warning', { ...context, operation, timeoutMs }, true);
    }

    getUserMessage(): string {
        return `操作超时: ${this.operation} (超过 ${this.timeoutMs / 1000}秒)`;
    }
}

/**
 * Agent execution errors (potentially retryable)
 *
 * Used when AI agent operations fail.
 * Aligns with backend AgentExecutionError (500).
 */
export class AgentExecutionError extends PluginError {
    /**
     * Creates a new AgentExecutionError
     *
     * @param message - Error description
     * @param agentName - Name of the agent that failed
     * @param context - Additional context (e.g., input, partial output)
     */
    constructor(
        message: string,
        public agentName: string,
        context?: Record<string, unknown>
    ) {
        super(message, 'critical', { ...context, agentName }, true);
    }

    getUserMessage(): string {
        return `Agent执行失败 (${this.agentName}): ${this.message}`;
    }
}

/**
 * Type guard to check if an error is a PluginError
 */
export function isPluginError(error: unknown): error is PluginError {
    return error instanceof PluginError;
}

/**
 * Converts unknown errors to PluginError
 *
 * @param error - Any error type
 * @param defaultMessage - Fallback message if error has no message
 * @returns A PluginError instance
 */
export function toPluginError(
    error: unknown,
    defaultMessage: string = '发生未知错误'
): PluginError {
    if (isPluginError(error)) {
        return error;
    }

    if (error instanceof Error) {
        // Check for network-related errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return new NetworkError(
                error.message,
                undefined,
                { originalError: error.message }
            );
        }

        // Generic error conversion
        return new class extends PluginError {
            constructor() {
                super(error.message || defaultMessage, 'warning', {
                    originalError: error.name,
                    originalStack: error.stack
                });
                this.name = 'WrappedError';
            }
        }();
    }

    // Unknown error type
    return new class extends PluginError {
        constructor() {
            super(
                typeof error === 'string' ? error : defaultMessage,
                'warning',
                { originalValue: String(error) }
            );
            this.name = 'UnknownError';
        }
    }();
}
