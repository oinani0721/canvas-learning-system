/**
 * Canvas Learning System - Rest Reminder Component
 *
 * Story 6.7 AC-2, AC-5: Displays rest reminders as special messages
 * in the chat panel (not modal popups).
 * - Soft background + icon style (distinct from regular messages)
 * - "Continue" and "Rest" action buttons
 * - CSS prefix: cl-exam-rest-*
 * - Light/Dark theme adaptive
 *
 * [Source: _bmad-output/implementation-artifacts/6-7-cognitive-load-rest-reminder.md]
 *
 * @module RestReminder
 */

export interface RestReminderCallbacks {
    onContinue: () => void;
    onRest: () => void;
}

export class RestReminder {
    private containerEl: HTMLElement;

    constructor(
        parentEl: HTMLElement,
        message: string,
        minutesElapsed: number,
        callbacks: RestReminderCallbacks,
    ) {
        this.containerEl = parentEl.createDiv({ cls: 'cl-exam-rest-container' });

        // Icon
        const iconEl = this.containerEl.createSpan({ cls: 'cl-exam-rest-icon' });
        iconEl.textContent = '\u23f0'; // Alarm clock

        // Message text
        const textEl = this.containerEl.createDiv({ cls: 'cl-exam-rest-text' });
        textEl.textContent = message;

        // Buttons row
        const buttonsEl = this.containerEl.createDiv({ cls: 'cl-exam-rest-buttons' });

        // "Continue" button (secondary style - border button)
        const continueBtn = buttonsEl.createEl('button', {
            cls: 'cl-exam-rest-btn-continue',
            text: '\u7ee7\u7eed\u8003\u5bdf',
        });
        continueBtn.addEventListener('click', () => {
            this.dismiss();
            callbacks.onContinue();
        });

        // "Rest" button (text style)
        const restBtn = buttonsEl.createEl('button', {
            cls: 'cl-exam-rest-btn-rest',
            text: '\u4f11\u606f',
        });
        restBtn.addEventListener('click', () => {
            this.dismiss();
            callbacks.onRest();
        });

        this.injectStyles();
    }

    private dismiss(): void {
        this.containerEl.classList.add('cl-exam-rest-dismissed');
        setTimeout(() => this.containerEl.remove(), 300);
    }

    private injectStyles(): void {
        const styleId = 'cl-exam-rest-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-exam-rest-container {
                display: flex;
                flex-direction: column;
                gap: 8px;
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 8px;
                background: var(--background-modifier-info, rgba(59, 130, 246, 0.08));
                border-left: 3px solid var(--interactive-accent, #7c3aed);
                transition: opacity 0.3s ease;
            }
            .cl-exam-rest-dismissed {
                opacity: 0;
            }
            .cl-exam-rest-icon {
                font-size: 18px;
                margin-right: 8px;
            }
            .cl-exam-rest-text {
                color: var(--text-normal);
                font-size: 14px;
                line-height: 1.5;
            }
            .cl-exam-rest-buttons {
                display: flex;
                gap: 8px;
                margin-top: 4px;
            }
            .cl-exam-rest-btn-continue {
                padding: 4px 16px;
                border: 1px solid var(--interactive-accent, #7c3aed);
                border-radius: 6px;
                background: transparent;
                color: var(--interactive-accent, #7c3aed);
                cursor: pointer;
                font-size: 13px;
            }
            .cl-exam-rest-btn-continue:hover {
                background: var(--interactive-accent, #7c3aed);
                color: var(--text-on-accent, #fff);
            }
            .cl-exam-rest-btn-rest {
                padding: 4px 16px;
                border: none;
                border-radius: 6px;
                background: transparent;
                color: var(--text-muted);
                cursor: pointer;
                font-size: 13px;
            }
            .cl-exam-rest-btn-rest:hover {
                color: var(--text-normal);
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        this.containerEl.remove();
    }
}
