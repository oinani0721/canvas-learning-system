/**
 * Canvas Learning System - Error Notification Service
 *
 * Service for displaying enhanced error notifications in Obsidian.
 * Implements ADR-009 NotificationManager pattern with:
 * - Error type-specific styling
 * - Bug ID display and copy functionality
 * - Retry button for retryable errors
 *
 * @source Story 21.5.5 - 插件错误显示增强
 * @source ADR-009 - Error Handling & Retry Strategy
 */

import { Notice } from 'obsidian';
import { ApiError, ErrorType } from '../api/types';

// ═══════════════════════════════════════════════════════════════════════════════
// Types and Interfaces
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Options for retry functionality
 * @source Story 21.5.5 - AC 3: 可重试错误提供重试按钮
 */
export interface RetryOptions {
  /** Operation name for logging/display */
  operation: string;
  /** Callback function to execute on retry */
  onRetry?: () => void | Promise<void>;
}

/**
 * Notification level enum matching ADR-009
 * @source ADR-009 - NotificationManager模式
 */
export enum NotificationLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  FATAL = 'fatal',
}

/**
 * Error type to notification level mapping
 * @source ADR-009 - 错误通知映射
 */
const ERROR_LEVEL_MAP: Record<ErrorType, NotificationLevel> = {
  NetworkError: NotificationLevel.WARNING,
  TimeoutError: NotificationLevel.WARNING,
  HttpError5xx: NotificationLevel.ERROR,
  HttpError4xx: NotificationLevel.ERROR,
  ValidationError: NotificationLevel.ERROR,
  UnknownError: NotificationLevel.ERROR,
};

/**
 * User-friendly messages for error types (Chinese)
 * @source Story 21.5.5 - AC 2: 不同错误类型显示不同样式
 */
const ERROR_TYPE_MESSAGES: Record<ErrorType, string> = {
  NetworkError: '网络连接问题',
  TimeoutError: '请求超时',
  HttpError5xx: '服务器错误',
  HttpError4xx: '请求错误',
  ValidationError: '数据验证错误',
  UnknownError: '未知错误',
};

// ═══════════════════════════════════════════════════════════════════════════════
// ErrorNotificationService Class
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Service for displaying enhanced error notifications
 *
 * Features:
 * - Error type-specific styling (warning/error)
 * - Bug ID display with click-to-copy
 * - Retry button for retryable errors
 * - User-friendly Chinese messages
 *
 * @source Story 21.5.5 - 任务2: 实现增强Notice显示
 * @source ADR-009 - NotificationManager设计模式
 *
 * @example
 * ```typescript
 * const notificationService = new ErrorNotificationService();
 *
 * // Show error with retry option
 * notificationService.showAgentError(apiError, {
 *   operation: 'decompose_basic',
 *   onRetry: () => this.executeBasicDecompose(context)
 * });
 *
 * // Show simple error
 * notificationService.showAgentError(apiError);
 * ```
 */
export class ErrorNotificationService {
  /** Default notice duration in milliseconds */
  private readonly DEFAULT_DURATION = 10000; // 10 seconds

  /** Duration for persistent notices (manual close) */
  private readonly PERSISTENT_DURATION = 0;

  /**
   * Display an enhanced error notification for Agent errors
   *
   * @param error - The ApiError instance to display
   * @param options - Optional retry configuration
   *
   * @source Story 21.5.5 - AC 1, 2, 3
   */
  showAgentError(error: ApiError, options?: RetryOptions): void {
    const duration = options?.onRetry
      ? this.PERSISTENT_DURATION // Keep open if retry available
      : this.DEFAULT_DURATION;

    const notice = new Notice('', duration);

    // Apply error-type specific styling
    // @source Story 21.5.5 - AC 2: 不同错误类型显示不同样式
    this.applyNoticeStyle(notice, error.type);

    // Build and set the message content
    const fragment = this.buildErrorFragment(error, options, notice);
    notice.setMessage(fragment);
  }

  /**
   * Display a simple error message without full ApiError details
   *
   * @param message - Error message to display
   * @param level - Notification level (default: ERROR)
   * @param duration - Display duration in ms (default: 5000)
   */
  showSimpleError(
    message: string,
    level: NotificationLevel = NotificationLevel.ERROR,
    duration: number = 5000
  ): void {
    const notice = new Notice(message, duration);

    if (level === NotificationLevel.WARNING) {
      notice.noticeEl.addClass('notice-warning');
    } else if (level === NotificationLevel.ERROR || level === NotificationLevel.FATAL) {
      notice.noticeEl.addClass('notice-error');
    }
  }

  /**
   * Display a success notification
   *
   * @param message - Success message
   * @param duration - Display duration in ms (default: 3000)
   */
  showSuccess(message: string, duration: number = 3000): void {
    const notice = new Notice(message, duration);
    notice.noticeEl.addClass('notice-success');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Private Helper Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Apply CSS class based on error type
   *
   * @source Story 21.5.5 - AC 2
   * - NetworkError: notice-warning
   * - TimeoutError: notice-warning
   * - HttpError5xx: notice-error
   * - HttpError4xx: notice-error
   */
  private applyNoticeStyle(notice: Notice, errorType: ErrorType): void {
    const level = ERROR_LEVEL_MAP[errorType] || NotificationLevel.ERROR;

    if (level === NotificationLevel.WARNING) {
      notice.noticeEl.addClass('notice-warning');
    } else {
      notice.noticeEl.addClass('notice-error');
    }
  }

  /**
   * Build the error message DocumentFragment
   *
   * Structure:
   * - Error type header (bold)
   * - Error message
   * - Bug ID (if present, clickable to copy)
   * - Retry button (if retryable and onRetry provided)
   *
   * @source Story 21.5.5 - 任务2.3: 实现带按钮的自定义Notice
   * @source Context7:/obsidianmd/obsidian-api - Notice with createDocumentFragment
   */
  private buildErrorFragment(
    error: ApiError,
    options?: RetryOptions,
    notice?: Notice
  ): DocumentFragment {
    const fragment = document.createDocumentFragment();

    // ── Error Type Header ──
    // Show backend error type if available, otherwise use our error type
    const typeText = error.backendErrorType || ERROR_TYPE_MESSAGES[error.type] || error.type;
    const typeEl = fragment.createEl('strong', {
      text: typeText,
      cls: 'error-notification-type',
    });
    fragment.appendChild(typeEl);

    // ── Error Message ──
    fragment.createEl('br');
    const messageEl = fragment.createEl('span', {
      text: error.message,
      cls: 'error-notification-message',
    });
    fragment.appendChild(messageEl);

    // ── Bug ID (if present) ──
    // @source Story 21.5.5 - AC 1: 显示bug_id用于问题追踪
    if (error.bugId) {
      fragment.createEl('br');
      const bugContainer = fragment.createEl('span', {
        cls: 'error-notification-bug-container',
      });

      const bugLabel = bugContainer.createEl('span', {
        text: 'Bug ID: ',
        cls: 'error-notification-bug-label',
      });

      const bugIdEl = bugContainer.createEl('code', {
        text: error.bugId,
        cls: 'error-notification-bug-id',
      });
      bugIdEl.setAttribute('title', '点击复制');

      // Click to copy bug ID
      bugIdEl.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(error.bugId!).then(() => {
          new Notice('Bug ID 已复制到剪贴板', 2000);
        });
      });

      fragment.appendChild(bugContainer);
    }

    // ── Retry Button (for retryable errors) ──
    // @source Story 21.5.5 - AC 3: 可重试错误提供重试按钮
    // @source ADR-009: RETRYABLE_ERROR_TYPES
    if (error.isRetryable && options?.onRetry) {
      fragment.createEl('br');

      const buttonContainer = fragment.createEl('div', {
        cls: 'error-notification-actions',
      });

      const retryBtn = buttonContainer.createEl('button', {
        text: '重试',
        cls: 'error-notification-retry-btn mod-cta',
      });

      retryBtn.addEventListener('click', async (e) => {
        e.stopPropagation();

        // Hide the notice
        if (notice) {
          notice.hide();
        }

        // Show retrying notice
        const retryingNotice = new Notice('正在重试...', 0);

        try {
          await options.onRetry!();
          retryingNotice.hide();
        } catch (retryError) {
          retryingNotice.hide();
          // Show the new error
          if (retryError instanceof ApiError) {
            this.showAgentError(retryError, options);
          } else {
            const msg = retryError instanceof Error ? retryError.message : '未知错误';
            this.showSimpleError(`重试失败: ${msg}`);
          }
        }
      });

      // Close button (for persistent notices)
      const closeBtn = buttonContainer.createEl('button', {
        text: '关闭',
        cls: 'error-notification-close-btn',
      });

      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (notice) {
          notice.hide();
        }
      });

      fragment.appendChild(buttonContainer);
    }

    return fragment;
  }

  /**
   * Get notification level for an error type
   */
  getNotificationLevel(errorType: ErrorType): NotificationLevel {
    return ERROR_LEVEL_MAP[errorType] || NotificationLevel.ERROR;
  }

  /**
   * Get user-friendly message for error type
   */
  getErrorTypeMessage(errorType: ErrorType): string {
    return ERROR_TYPE_MESSAGES[errorType] || '未知错误';
  }
}
