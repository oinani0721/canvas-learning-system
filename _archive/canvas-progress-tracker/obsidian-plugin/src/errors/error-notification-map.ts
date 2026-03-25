/**
 * Error Notification Map - Canvas Learning System
 *
 * Maps error codes to user-friendly notifications with appropriate levels.
 * Based on ADR-009: Error Handling & Retry Strategy
 *
 * @source ADR-009: ERROR_NOTIFICATION_MAP design (lines 617-665)
 * @source Story 12.G.5: Frontend Error Display Optimization
 * @module errors/error-notification-map
 */

/**
 * Notification levels for error display
 * @source ADR-009: NotificationLevel enum (lines 508-513)
 */
export enum NotificationLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  FATAL = 'fatal',
}

/**
 * Error notification configuration
 */
export interface ErrorNotificationConfig {
  level: NotificationLevel;
  message: string;
  action?: {
    label: string;
    callback?: () => void;
    settingsTab?: string;
  };
}

/**
 * Error code to notification mapping
 * Based on ADR-009 error code system:
 * - 1xxx: LLM related errors
 * - 2xxx: Database related errors
 * - 3xxx: File related errors
 * - 4xxx: Network related errors
 * - 5xxx: Agent related errors
 *
 * @source ADR-009: ErrorCode enum (lines 57-87)
 */
export const ERROR_NOTIFICATION_MAP: Record<number, ErrorNotificationConfig> = {
  // =========================================================================
  // LLM Related (1xxx)
  // =========================================================================
  1001: {
    level: NotificationLevel.WARNING,
    message: 'LLM服务繁忙，正在重试...',
  },
  1002: {
    level: NotificationLevel.WARNING,
    message: '请求超时，正在重试...',
  },
  1003: {
    level: NotificationLevel.FATAL,
    message: 'API Key无效或账户余额不足',
    action: { label: '打开设置', settingsTab: 'api' },
  },
  1004: {
    level: NotificationLevel.ERROR,
    message: 'LLM返回无效响应',
  },
  1100: {
    level: NotificationLevel.ERROR,
    message: 'LLM服务暂时不可用，稍后自动重试',
  },

  // =========================================================================
  // Database Related (2xxx)
  // =========================================================================
  2001: {
    level: NotificationLevel.ERROR,
    message: '数据库连接失败，请重启插件',
  },
  2002: {
    level: NotificationLevel.WARNING,
    message: '数据库锁定，正在重试...',
  },
  2003: {
    level: NotificationLevel.ERROR,
    message: '数据库查询失败',
  },

  // =========================================================================
  // File Related (3xxx)
  // =========================================================================
  3001: {
    level: NotificationLevel.ERROR,
    message: 'Canvas文件不存在',
  },
  3002: {
    level: NotificationLevel.ERROR,
    message: '文件权限错误',
  },
  3003: {
    level: NotificationLevel.FATAL,
    message: 'Canvas文件格式错误',
    action: { label: '查看帮助' },
  },

  // =========================================================================
  // Network Related (4xxx)
  // =========================================================================
  4001: {
    level: NotificationLevel.WARNING,
    message: '网络请求超时，正在重试...',
  },
  4002: {
    level: NotificationLevel.ERROR,
    message: '网络连接失败，请检查网络',
  },
  4003: {
    level: NotificationLevel.WARNING,
    message: 'SSE连接断开，正在重连...',
  },

  // =========================================================================
  // Agent Related (5xxx)
  // =========================================================================
  5001: {
    level: NotificationLevel.ERROR,
    message: 'Agent状态错误',
  },
  5002: {
    level: NotificationLevel.WARNING,
    message: 'Agent处理超时，正在重试...',
  },
  5003: {
    level: NotificationLevel.ERROR,
    message: '输入参数无效',
  },
};

/**
 * Get notification config for an error code
 * Returns default config if code not found
 */
export function getNotificationConfig(
  errorCode: number | undefined,
  fallbackMessage: string = '发生未知错误'
): ErrorNotificationConfig {
  if (errorCode && ERROR_NOTIFICATION_MAP[errorCode]) {
    return ERROR_NOTIFICATION_MAP[errorCode];
  }

  return {
    level: NotificationLevel.ERROR,
    message: fallbackMessage,
  };
}

/**
 * Check if an error code represents a retryable error
 * @source ADR-009: RETRYABLE_ERROR_TYPES
 */
export function isRetryableErrorCode(errorCode: number | undefined): boolean {
  if (!errorCode) return false;

  const config = ERROR_NOTIFICATION_MAP[errorCode];
  if (!config) return false;

  // WARNING level errors are typically retryable
  return config.level === NotificationLevel.WARNING;
}
