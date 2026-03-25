/**
 * Canvas Learning System - Skip Button Component
 *
 * Story 6.6 AC-5: Skip current question button.
 * - Gray text style (tertiary action)
 * - No confirmation dialog (reduce friction)
 * - CSS prefix: cl-exam-skip-*
 *
 * [Source: _bmad-output/implementation-artifacts/6-6-progressive-hints-skip.md]
 *
 * @module SkipButton
 */

import { requestUrl } from 'obsidian';

export interface SkipButtonConfig {
    baseUrl: string;
    examId: string;
    nodeId: string;
    onSkipped: () => void;
}

export class SkipButton {
    private buttonEl: HTMLButtonElement;
    private config: SkipButtonConfig;
    private questionId: string = '';

    constructor(parentEl: HTMLElement, config: SkipButtonConfig) {
        this.config = config;

        this.buttonEl = parentEl.createEl('button', {
            cls: 'cl-exam-skip-btn',
            text: '\u8df3\u8fc7\u8fd9\u9898',
        });

        this.buttonEl.addEventListener('click', () => this.skipQuestion());
        this.injectStyles();
    }

    setNodeId(nodeId: string): void {
        this.config.nodeId = nodeId;
    }

    setQuestionId(questionId: string): void {
        this.questionId = questionId;
    }

    private async skipQuestion(): Promise<void> {
        this.buttonEl.disabled = true;

        try {
            await requestUrl({
                url: `${this.config.baseUrl}/api/v1/exam/${this.config.examId}/skip`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exam_id: this.config.examId,
                    node_id: this.config.nodeId,
                    question_id: this.questionId,
                }),
            });

            this.config.onSkipped();
        } catch (e) {
            console.error('[Story 6.6] Skip request failed:', e);
        } finally {
            this.buttonEl.disabled = false;
        }
    }

    private injectStyles(): void {
        const styleId = 'cl-exam-skip-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-exam-skip-btn {
                padding: 4px 12px;
                border: none;
                border-radius: 6px;
                background: transparent;
                color: var(--text-muted);
                cursor: pointer;
                font-size: 12px;
                transition: color 0.2s ease;
            }
            .cl-exam-skip-btn:hover {
                color: var(--text-normal);
                text-decoration: underline;
            }
            .cl-exam-skip-btn:disabled {
                cursor: not-allowed;
                opacity: 0.4;
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        this.buttonEl.remove();
    }
}
