/**
 * Canvas Learning System - Hint Button Component
 *
 * Story 6.6 AC-2: 4-level progressive hint button.
 * - Text changes with level: "Hint (1/4)" -> "More (2/4)" -> ... -> "Last (4/4)"
 * - Grayed out and disabled after Level 4
 * - Resets to Level 1 on new question
 * - CSS prefix: cl-exam-hint-*
 *
 * [Source: _bmad-output/implementation-artifacts/6-6-progressive-hints-skip.md]
 *
 * @module HintButton
 */

import { requestUrl } from 'obsidian';

export interface HintButtonConfig {
    baseUrl: string;
    examId: string;
    nodeId: string;
    onHintReceived: (hintText: string, level: number) => void;
}

export class HintButton {
    private buttonEl: HTMLButtonElement;
    private currentLevel: number = 0; // 0 = no hints used yet
    private config: HintButtonConfig;
    private questionContext: string = '';

    constructor(parentEl: HTMLElement, config: HintButtonConfig) {
        this.config = config;

        this.buttonEl = parentEl.createEl('button', {
            cls: 'cl-exam-hint-btn',
        });
        this.updateButtonText();

        this.buttonEl.addEventListener('click', () => this.requestHint());
        this.injectStyles();
    }

    setQuestionContext(context: string): void {
        this.questionContext = context;
    }

    setNodeId(nodeId: string): void {
        this.config.nodeId = nodeId;
    }

    resetForNewQuestion(): void {
        this.currentLevel = 0;
        this.buttonEl.disabled = false;
        this.buttonEl.classList.remove('cl-exam-hint-exhausted');
        this.updateButtonText();
    }

    private updateButtonText(): void {
        const nextLevel = this.currentLevel + 1;
        if (this.currentLevel === 0) {
            this.buttonEl.textContent = '\u7ed9\u6211\u63d0\u793a (1/4)';
        } else if (this.currentLevel < 4) {
            this.buttonEl.textContent = `\u7ee7\u7eed\u63d0\u793a (${nextLevel}/4)`;
        } else {
            this.buttonEl.textContent = '\u63d0\u793a\u5df2\u7528\u5b8c (4/4)';
            this.buttonEl.disabled = true;
            this.buttonEl.classList.add('cl-exam-hint-exhausted');
        }
    }

    private async requestHint(): Promise<void> {
        if (this.currentLevel >= 4) return;

        const nextLevel = this.currentLevel + 1;
        this.buttonEl.disabled = true;
        this.buttonEl.textContent = '\u751f\u6210\u4e2d...';

        try {
            const response = await requestUrl({
                url: `${this.config.baseUrl}/api/v1/exam/${this.config.examId}/hint`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exam_id: this.config.examId,
                    node_id: this.config.nodeId,
                    hint_level: nextLevel,
                    question_context: this.questionContext,
                }),
            });

            const data = JSON.parse(response.text);
            if (data.status === 'ok' && data.hint_text) {
                this.currentLevel = data.current_level;
                this.config.onHintReceived(data.hint_text, data.current_level);
            }
        } catch (e) {
            console.error('[Story 6.6] Hint request failed:', e);
        } finally {
            this.buttonEl.disabled = this.currentLevel >= 4;
            this.updateButtonText();
        }
    }

    private injectStyles(): void {
        const styleId = 'cl-exam-hint-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-exam-hint-btn {
                padding: 4px 12px;
                border: 1px solid var(--interactive-accent, #7c3aed);
                border-radius: 6px;
                background: transparent;
                color: var(--interactive-accent, #7c3aed);
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s ease;
            }
            .cl-exam-hint-btn:hover:not(:disabled) {
                background: var(--interactive-accent, #7c3aed);
                color: var(--text-on-accent, #fff);
            }
            .cl-exam-hint-btn:disabled {
                cursor: not-allowed;
                opacity: 0.5;
            }
            .cl-exam-hint-exhausted {
                border-color: var(--text-muted) !important;
                color: var(--text-muted) !important;
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        this.buttonEl.remove();
    }
}
