/**
 * Canvas Learning System - Cognitive Load Timer Component
 *
 * Story 6.7 AC-4: Displays exam duration in the status bar.
 * - Format: "MM:SS"
 * - Yellow color when approaching threshold (2 min before)
 * - CSS prefix: cl-exam-timer-*
 *
 * [Source: _bmad-output/implementation-artifacts/6-7-cognitive-load-rest-reminder.md]
 *
 * @module CognitiveLoadTimer
 */

const THRESHOLDS = [15, 25, 35, 45]; // minutes
const WARNING_BEFORE_SECONDS = 120; // 2 minutes before threshold

export class CognitiveLoadTimer {
    private containerEl: HTMLElement;
    private timerEl: HTMLElement;
    private updateInterval: ReturnType<typeof setInterval> | null = null;
    private getActiveSeconds: () => number;

    constructor(
        parentEl: HTMLElement,
        getActiveSeconds: () => number,
    ) {
        this.getActiveSeconds = getActiveSeconds;

        this.containerEl = parentEl.createDiv({ cls: 'cl-exam-timer-container' });
        this.timerEl = this.containerEl.createSpan({ cls: 'cl-exam-timer-display' });

        this.injectStyles();
        this.startDisplay();
    }

    private startDisplay(): void {
        this.updateDisplay();
        this.updateInterval = setInterval(() => this.updateDisplay(), 1000);
    }

    private updateDisplay(): void {
        const totalSeconds = this.getActiveSeconds();
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        const mm = String(minutes).padStart(2, '0');
        const ss = String(seconds).padStart(2, '0');
        this.timerEl.textContent = `\u8003\u5bdf ${mm}:${ss}`;

        // Check if approaching a threshold (Story 6.7 AC-4: yellow warning)
        const isNearThreshold = THRESHOLDS.some(t => {
            const thresholdSeconds = t * 60;
            const diff = thresholdSeconds - totalSeconds;
            return diff > 0 && diff <= WARNING_BEFORE_SECONDS;
        });

        this.timerEl.classList.toggle('cl-exam-timer-warning', isNearThreshold);
    }

    private injectStyles(): void {
        const styleId = 'cl-exam-timer-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-exam-timer-container {
                display: inline-flex;
                align-items: center;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-variant-numeric: tabular-nums;
            }
            .cl-exam-timer-display {
                color: var(--text-muted);
                transition: color 0.3s ease;
            }
            .cl-exam-timer-warning {
                color: var(--text-warning, #e2b340) !important;
                font-weight: 600;
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        this.containerEl.remove();
    }
}
