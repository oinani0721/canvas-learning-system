/**
 * Error Notifier - Canvas Review System
 *
 * Provides user-friendly error notifications using Obsidian's Notice API.
 * Supports different notification styles based on error severity.
 *
 * @module errors/ErrorNotifier
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Notice API)
 * ✅ Verified from Story 13.7 Dev Notes (ErrorNotifier class)
 */

import { Notice } from 'obsidian';
import { PluginError, ErrorSeverity } from './PluginError';

/**
 * Notice duration settings (in milliseconds)
 */
const NOTICE_DURATIONS: Record<ErrorSeverity, number> = {
    critical: 10000, // 10 seconds
    warning: 5000,   // 5 seconds
    info: 3000       // 3 seconds
};

/**
 * Notice emoji prefixes by severity
 */
const NOTICE_PREFIXES: Record<ErrorSeverity, string> = {
    critical: '❌ 错误',
    warning: '⚠️ 警告',
    info: 'ℹ️'
};

/**
 * Error Notifier class
 *
 * Encapsulates Obsidian's Notice API to provide consistent
 * error notifications throughout the plugin.
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorNotifier design)
 */
export class ErrorNotifier {
    private activeNotices: Set<Notice> = new Set();

    /**
     * Shows an error notification to the user
     *
     * @param error - The PluginError to display
     *
     * ✅ Verified from @obsidian-canvas Skill (Notice API)
     */
    showError(error: PluginError): Notice {
        const prefix = NOTICE_PREFIXES[error.severity];
        const duration = NOTICE_DURATIONS[error.severity];
        const message = error.getUserMessage();

        const notice = new Notice(
            `${prefix}: ${message}`,
            duration
        );

        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows an error notification with recovery options
     *
     * @param error - The PluginError to display
     * @param onRetry - Callback function when user clicks retry
     *
     * ✅ Verified from Story 13.7 Dev Notes (showRecoveryOptions)
     */
    showRecoveryOptions(
        error: PluginError,
        onRetry: () => void
    ): Notice {
        // Create notice with interactive elements
        const frag = document.createDocumentFragment();

        // Error message
        const messageSpan = frag.createEl('span', {
            text: `❌ ${error.getUserMessage()} `
        });
        messageSpan.style.marginRight = '8px';

        // Retry button (only if error is recoverable)
        if (error.recoverable) {
            const retryBtn = frag.createEl('button', {
                text: '重试',
                cls: 'mod-cta'
            });
            retryBtn.style.marginRight = '4px';
            retryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                onRetry();
            });
        }

        // Create persistent notice (0 = doesn't auto-dismiss)
        const notice = new Notice(frag, 0);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows a fatal error notification that requires user action
     *
     * @param error - The fatal PluginError
     */
    showFatalError(error: PluginError): Notice {
        const frag = document.createDocumentFragment();

        // Fatal error title
        const title = frag.createEl('div', {
            text: '🔴 Canvas复习系统 - 致命错误'
        });
        title.style.fontWeight = 'bold';
        title.style.marginBottom = '8px';

        // Error message
        const message = frag.createEl('div', {
            text: error.getUserMessage()
        });
        message.style.marginBottom = '8px';

        // Suggestion
        const suggestion = frag.createEl('div', {
            text: '请尝试重新加载Obsidian或禁用后重新启用插件'
        });
        suggestion.style.fontSize = '0.9em';
        suggestion.style.color = 'var(--text-muted)';

        // Persistent notice
        const notice = new Notice(frag, 0);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows a simple info notification
     *
     * @param message - The message to display
     */
    showInfo(message: string): Notice {
        const notice = new Notice(`ℹ️ ${message}`, NOTICE_DURATIONS.info);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows a success notification
     *
     * @param message - The success message
     */
    showSuccess(message: string): Notice {
        const notice = new Notice(`✅ ${message}`, NOTICE_DURATIONS.info);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows a warning notification
     *
     * @param message - The warning message
     */
    showWarning(message: string): Notice {
        const notice = new Notice(`⚠️ ${message}`, NOTICE_DURATIONS.warning);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows retry progress notification
     *
     * @param attempt - Current retry attempt number
     * @param maxRetries - Maximum number of retries
     * @param delay - Delay before next retry in ms
     */
    showRetryProgress(
        attempt: number,
        maxRetries: number,
        delay: number
    ): Notice {
        const delaySeconds = Math.round(delay / 1000);
        const message = `正在重试连接... (尝试 ${attempt}/${maxRetries}, ${delaySeconds}秒后)`;

        const notice = new Notice(message, delay + 1000);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows degraded mode notification
     *
     * @param feature - The feature that is degraded
     * @param reason - Reason for degradation
     */
    showDegradedMode(feature: string, reason: string): Notice {
        const frag = document.createDocumentFragment();

        const icon = frag.createEl('span', { text: '⚠️ ' });

        const message = frag.createEl('span', {
            text: `${feature}功能暂时使用降级模式: ${reason}`
        });

        const notice = new Notice(frag, NOTICE_DURATIONS.warning);
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Shows cache fallback notification
     */
    showCacheFallback(): Notice {
        const notice = new Notice(
            '⚠️ API服务暂时不可用，已使用缓存数据',
            NOTICE_DURATIONS.warning
        );
        this.trackNotice(notice);
        return notice;
    }

    /**
     * Hides all active notifications
     */
    hideAll(): void {
        for (const notice of this.activeNotices) {
            notice.hide();
        }
        this.activeNotices.clear();
    }

    /**
     * Gets the count of active notifications
     */
    getActiveCount(): number {
        return this.activeNotices.size;
    }

    // ========== Private Methods ==========

    /**
     * Tracks a notice for management
     */
    private trackNotice(notice: Notice): void {
        this.activeNotices.add(notice);

        // Remove from tracking when hidden
        // Note: Obsidian Notice doesn't have an onHide callback,
        // so we set a timeout based on duration + buffer
        const maxDuration = Math.max(...Object.values(NOTICE_DURATIONS)) + 1000;
        setTimeout(() => {
            this.activeNotices.delete(notice);
        }, maxDuration);
    }
}

/**
 * Internationalization support for error messages
 *
 * Maps error codes to localized messages in Chinese and English
 */
export const ErrorMessages = {
    zh: {
        network_timeout: '请求超时，请检查网络连接后重试',
        network_unavailable: '无法连接到API服务器',
        server_error: 'API服务器暂时不可用，请稍后重试',
        validation_failed: '输入验证失败',
        canvas_parse_error: 'Canvas文件解析失败',
        unauthorized: '未授权访问，请检查认证设置',
        not_found: '请求的资源未找到',
        rate_limited: 'API请求过于频繁，请稍后重试',
        agent_error: 'Agent执行失败',
        unknown_error: '发生未知错误'
    },
    en: {
        network_timeout: 'Request timed out. Please check your network connection.',
        network_unavailable: 'Unable to connect to API server',
        server_error: 'API server temporarily unavailable. Please try again later.',
        validation_failed: 'Input validation failed',
        canvas_parse_error: 'Failed to parse Canvas file',
        unauthorized: 'Unauthorized access. Please check authentication settings.',
        not_found: 'Requested resource not found',
        rate_limited: 'Too many API requests. Please wait before retrying.',
        agent_error: 'Agent execution failed',
        unknown_error: 'An unknown error occurred'
    }
} as const;

export type ErrorMessageKey = keyof typeof ErrorMessages.zh;

/**
 * Gets a localized error message
 *
 * @param key - Error message key
 * @param locale - Locale ('zh' or 'en'), defaults to 'zh'
 */
export function getErrorMessage(
    key: ErrorMessageKey,
    locale: 'zh' | 'en' = 'zh'
): string {
    return ErrorMessages[locale][key] || ErrorMessages[locale].unknown_error;
}
