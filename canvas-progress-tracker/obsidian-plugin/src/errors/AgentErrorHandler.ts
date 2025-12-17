/**
 * Agent Error Handler - Canvas Learning System
 *
 * Unified error handling for all Agent API calls.
 * Provides user-friendly notifications, retry buttons, and status bar updates.
 *
 * @source Story 12.G.5: Frontend Error Display Optimization
 * @source ADR-009: Error Handling & Retry Strategy
 * @module errors/AgentErrorHandler
 */

import { Notice } from 'obsidian';
import { ApiError } from '../api/types';
import {
  ERROR_NOTIFICATION_MAP,
  NotificationLevel,
  getNotificationConfig,
  type ErrorNotificationConfig,
} from './error-notification-map';

/**
 * Configuration for AgentErrorHandler
 */
export interface AgentErrorHandlerConfig {
  /** Status bar element for persistent error display */
  statusBarEl?: HTMLElement;
  /** Default notice duration in milliseconds */
  defaultNoticeDuration?: number;
  /** Enable debug logging */
  debug?: boolean;
}

/**
 * Unified Agent Error Handler
 *
 * Handles all Agent API call errors with:
 * - User-friendly error messages (Chinese)
 * - Retry buttons for retryable errors
 * - Bug ID display and copy functionality
 * - Status bar error state indication
 *
 * @example
 * ```typescript
 * const handler = new AgentErrorHandler({ statusBarEl: this.statusBarEl });
 *
 * try {
 *   await apiClient.callAgent(params);
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     await handler.handleError(error, async () => {
 *       await apiClient.callAgent(params); // retry
 *     });
 *   }
 * }
 * ```
 */
export class AgentErrorHandler {
  private statusBarEl: HTMLElement | null = null;
  private lastError: ApiError | null = null;
  private defaultNoticeDuration: number;
  private debug: boolean;

  constructor(config: AgentErrorHandlerConfig = {}) {
    this.statusBarEl = config.statusBarEl ?? null;
    this.defaultNoticeDuration = config.defaultNoticeDuration ?? 5000;
    this.debug = config.debug ?? false;
  }

  /**
   * Handle an Agent API error
   *
   * @param error - The ApiError instance
   * @param retryCallback - Optional callback to retry the failed operation
   * @returns Promise that resolves when error handling is complete
   */
  async handleError(
    error: ApiError,
    retryCallback?: () => Promise<void>
  ): Promise<void> {
    this.lastError = error;

    if (this.debug) {
      console.log('[AgentErrorHandler] Handling error:', {
        type: error.type,
        message: error.message,
        bugId: error.bugId,
        isRetryable: error.isRetryable,
        details: error.details,
      });
    }

    // 1. Get mapped error configuration
    const errorCode = this.extractErrorCode(error);
    const mappedError = this.getMappedError(error, errorCode);

    // 2. Create notification content
    const frag = document.createDocumentFragment();
    const container = frag.createDiv({ cls: 'agent-error-notice' });

    // Error icon and message
    const iconClass = this.getIconForLevel(mappedError.level);
    container.createSpan({ text: `${iconClass} ${mappedError.message}` });

    // Bug ID (if available)
    if (error.bugId) {
      this.addBugIdElement(container, error.bugId);
    }

    // Retry button (if retryable and callback provided)
    if (error.isRetryable && retryCallback) {
      this.addRetryButton(container, retryCallback);
    }

    // 3. Show notification
    const duration = this.getNoticeDuration(mappedError.level);
    new Notice(frag, duration);

    // 4. Update status bar
    this.updateStatusBar(mappedError.level);

    // 5. Log for debugging
    if (this.debug) {
      console.log('[AgentErrorHandler] Error displayed:', {
        level: mappedError.level,
        message: mappedError.message,
        duration,
      });
    }
  }

  /**
   * Extract error code from ApiError
   */
  private extractErrorCode(error: ApiError): number | undefined {
    // Try to get error code from details
    const code = error.details?.code;
    if (typeof code === 'number') {
      return code;
    }

    // Try to parse from error_code field
    const errorCode = error.details?.error_code;
    if (typeof errorCode === 'number') {
      return errorCode;
    }

    return undefined;
  }

  /**
   * Get mapped error configuration
   */
  private getMappedError(
    error: ApiError,
    errorCode: number | undefined
  ): ErrorNotificationConfig {
    // Try to get config from error code
    if (errorCode && ERROR_NOTIFICATION_MAP[errorCode]) {
      return ERROR_NOTIFICATION_MAP[errorCode];
    }

    // Fall back to error type-based mapping
    return {
      level: error.isRetryable ? NotificationLevel.WARNING : NotificationLevel.ERROR,
      message: error.getUserFriendlyMessage(),
    };
  }

  /**
   * Get icon for notification level
   */
  private getIconForLevel(level: NotificationLevel): string {
    switch (level) {
      case NotificationLevel.INFO:
        return 'ℹ️';
      case NotificationLevel.WARNING:
        return '⏳';
      case NotificationLevel.ERROR:
        return '⚠️';
      case NotificationLevel.FATAL:
        return '❌';
      default:
        return '⚠️';
    }
  }

  /**
   * Get notice duration based on error level
   */
  private getNoticeDuration(level: NotificationLevel): number {
    switch (level) {
      case NotificationLevel.FATAL:
        return 0; // Persistent until dismissed
      case NotificationLevel.ERROR:
        return 8000;
      case NotificationLevel.WARNING:
        return 5000;
      case NotificationLevel.INFO:
        return 3000;
      default:
        return this.defaultNoticeDuration;
    }
  }

  /**
   * Add Bug ID element with copy button
   */
  private addBugIdElement(container: HTMLElement, bugId: string): void {
    const bugIdEl = container.createDiv({ cls: 'agent-error-bugid' });
    bugIdEl.createSpan({ text: `Bug ID: ${bugId}` });

    const copyBtn = bugIdEl.createEl('button', { text: '复制' });
    copyBtn.onclick = async (e) => {
      e.stopPropagation();
      try {
        await navigator.clipboard.writeText(bugId);
        new Notice('Bug ID 已复制', 2000);
      } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = bugId;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        new Notice('Bug ID 已复制', 2000);
      }
    };
  }

  /**
   * Add retry button
   */
  private addRetryButton(
    container: HTMLElement,
    retryCallback: () => Promise<void>
  ): void {
    const retryBtn = container.createEl('button', {
      text: '重试',
      cls: 'agent-error-retry-btn',
    });

    let isRetrying = false;

    retryBtn.onclick = async (e) => {
      e.stopPropagation();

      if (isRetrying) {
        return; // Prevent double-click
      }

      isRetrying = true;
      retryBtn.setText('重试中...');
      retryBtn.disabled = true;

      try {
        new Notice('正在重试...', 2000);
        await retryCallback();
        this.clearError();
      } catch (retryError) {
        // Retry failed - error will be handled by the caller
        if (this.debug) {
          console.log('[AgentErrorHandler] Retry failed:', retryError);
        }
      } finally {
        isRetrying = false;
        retryBtn.setText('重试');
        retryBtn.disabled = false;
      }
    };
  }

  /**
   * Update status bar with error state
   */
  private updateStatusBar(level: NotificationLevel): void {
    if (!this.statusBarEl) return;

    const icons: Record<NotificationLevel, string> = {
      [NotificationLevel.INFO]: '✅',
      [NotificationLevel.WARNING]: '⚠️',
      [NotificationLevel.ERROR]: '❌',
      [NotificationLevel.FATAL]: '🚫',
    };

    this.statusBarEl.setText(`${icons[level]} Canvas: 错误`);
    this.statusBarEl.addClass('canvas-status-error');

    // Non-fatal errors auto-clear after 5 seconds
    if (level !== NotificationLevel.FATAL) {
      setTimeout(() => {
        if (this.lastError) {
          // Only clear if no new error occurred
          this.clearError();
        }
      }, 5000);
    }
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this.lastError = null;
    if (this.statusBarEl) {
      this.statusBarEl.setText('✅ Canvas: Ready');
      this.statusBarEl.removeClass('canvas-status-error');
    }
  }

  /**
   * Get the last error
   */
  getLastError(): ApiError | null {
    return this.lastError;
  }

  /**
   * Check if there's an active error
   */
  hasError(): boolean {
    return this.lastError !== null;
  }

  /**
   * Set the status bar element
   */
  setStatusBarEl(el: HTMLElement): void {
    this.statusBarEl = el;
  }
}
