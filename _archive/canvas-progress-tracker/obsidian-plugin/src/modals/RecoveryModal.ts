/**
 * Recovery Modal - Canvas Review System
 *
 * Modal dialog for presenting error recovery options to users.
 *
 * @module modals/RecoveryModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 13.7 Dev Notes (RecoveryModal design)
 */

import { App, Modal } from 'obsidian';
import { PluginError } from '../errors/PluginError';

/**
 * Recovery action callbacks
 */
export interface RecoveryOptions {
    /** Callback when user clicks retry */
    retry?: () => void;
    /** Callback when user clicks clear cache */
    clearCache?: () => void;
    /** Callback when user clicks report issue */
    reportIssue?: () => void;
    /** Callback when user ignores the error */
    ignore?: () => void;
}

/**
 * Recovery Modal
 *
 * Presents recovery options to users when an error occurs.
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class RecoveryModal extends Modal {
    private error: PluginError;
    private operation: string;
    private options: RecoveryOptions;
    private resolved: boolean = false;

    /**
     * Creates a new RecoveryModal
     *
     * @param app - Obsidian App instance
     * @param error - The error that occurred
     * @param operation - Description of the failed operation
     * @param options - Recovery action callbacks
     */
    constructor(
        app: App,
        error: PluginError,
        operation: string,
        options: RecoveryOptions
    ) {
        super(app);
        this.error = error;
        this.operation = operation;
        this.options = options;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();

        // Add modal class for styling
        contentEl.addClass('canvas-review-recovery-modal');

        // Header
        const header = contentEl.createEl('div', {
            cls: 'recovery-modal-header'
        });

        header.createEl('h2', {
            text: '❌ 操作失败',
            cls: 'recovery-modal-title'
        });

        // Operation info
        const operationEl = contentEl.createEl('div', {
            cls: 'recovery-modal-operation'
        });
        operationEl.createEl('strong', { text: '操作: ' });
        operationEl.createSpan({ text: this.operation });

        // Error message
        const errorSection = contentEl.createEl('div', {
            cls: 'recovery-modal-error'
        });

        errorSection.createEl('div', {
            text: this.error.getUserMessage(),
            cls: 'recovery-modal-message'
        });

        // Error type badge
        const badge = errorSection.createEl('span', {
            text: this.error.name,
            cls: `recovery-modal-badge severity-${this.error.severity}`
        });

        // Context details (collapsible)
        if (this.error.context && Object.keys(this.error.context).length > 0) {
            const details = contentEl.createEl('details', {
                cls: 'recovery-modal-details'
            });
            details.createEl('summary', { text: '详细信息' });

            const contextPre = details.createEl('pre', {
                cls: 'recovery-modal-context'
            });
            contextPre.createEl('code', {
                text: JSON.stringify(this.error.context, null, 2)
            });
        }

        // Recovery options section
        const optionsSection = contentEl.createEl('div', {
            cls: 'recovery-modal-options'
        });

        optionsSection.createEl('h3', { text: '恢复选项' });

        const buttonContainer = optionsSection.createEl('div', {
            cls: 'recovery-modal-buttons'
        });

        // Retry button (if error is recoverable)
        if (this.error.recoverable && this.options.retry) {
            this.createButton(
                buttonContainer,
                '🔄 重试',
                'mod-cta',
                () => {
                    this.resolved = true;
                    this.close();
                    this.options.retry?.();
                }
            );
        }

        // Clear cache button
        if (this.options.clearCache) {
            this.createButton(
                buttonContainer,
                '🗑️ 清除缓存',
                '',
                () => {
                    this.resolved = true;
                    this.close();
                    this.options.clearCache?.();
                }
            );
        }

        // Report issue button
        if (this.options.reportIssue) {
            this.createButton(
                buttonContainer,
                '📝 报告问题',
                '',
                () => {
                    this.resolved = true;
                    this.close();
                    this.options.reportIssue?.();
                }
            );
        }

        // Ignore button (always show)
        this.createButton(
            buttonContainer,
            '关闭',
            '',
            () => {
                this.resolved = true;
                this.close();
                this.options.ignore?.();
            }
        );

        // Help text
        const helpText = contentEl.createEl('div', {
            cls: 'recovery-modal-help'
        });

        if (this.error.recoverable) {
            helpText.createEl('p', {
                text: '💡 此错误可能是暂时的，重试可能解决问题。'
            });
        } else {
            helpText.createEl('p', {
                text: '⚠️ 此错误需要手动修复。请检查设置或联系支持。'
            });
        }
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();

        // If closed without selecting an option, treat as ignore
        if (!this.resolved && this.options.ignore) {
            this.options.ignore();
        }
    }

    /**
     * Creates a styled button
     */
    private createButton(
        container: HTMLElement,
        text: string,
        cls: string,
        onClick: () => void
    ): HTMLButtonElement {
        const button = container.createEl('button', {
            text,
            cls: `recovery-modal-button ${cls}`.trim()
        });
        button.addEventListener('click', onClick);
        return button;
    }
}
