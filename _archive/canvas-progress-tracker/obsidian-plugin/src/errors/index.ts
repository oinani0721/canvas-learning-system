/**
 * Error Handling Module - Canvas Review System
 *
 * Exports all error handling components for the Obsidian plugin.
 *
 * @module errors
 * @version 1.0.0
 */

// Error classes
export {
    PluginError,
    NetworkError,
    CanvasParseError,
    APIError,
    ValidationError,
    ConfigurationError,
    TimeoutError,
    AgentExecutionError,
    isPluginError,
    toPluginError,
    type ErrorSeverity
} from './PluginError';

// Global error handler
export {
    GlobalErrorHandler,
    withErrorHandling,
    type ErrorHandlerConfig
} from './GlobalErrorHandler';

// Error notifier
export {
    ErrorNotifier,
    ErrorMessages,
    getErrorMessage,
    type ErrorMessageKey
} from './ErrorNotifier';

// Retry policy
export {
    RetryPolicy,
    CircuitBreaker,
    DEFAULT_RETRY_CONFIG,
    type RetryPolicyConfig,
    type RetryAttemptInfo,
    type OnRetryCallback
} from './RetryPolicy';

// Error logger
export {
    ErrorLogger,
    type ErrorLogEntry,
    type ErrorLoggerConfig,
    type ErrorLogStatistics
} from './ErrorLogger';

// Error recovery
export {
    ErrorRecoveryManager,
    type RecoveryAction,
    type RecoveryResult
} from './ErrorRecoveryManager';

// Agent error handler (Story 12.G.5)
export {
    AgentErrorHandler,
    type AgentErrorHandlerConfig
} from './AgentErrorHandler';

// Error notification map (Story 12.G.5)
export {
    NotificationLevel,
    ERROR_NOTIFICATION_MAP,
    getNotificationConfig,
    isRetryableErrorCode,
    type ErrorNotificationConfig
} from './error-notification-map';
