/**
 * Canvas Learning System - Exam Card Component
 *
 * Story 6.8 AC-5: Dashboard exam record card.
 * - Shows: canvas name, mode icon, date, duration, node count, trend arrow
 * - Click expands to full ExamRecordView
 * - CSS prefix: cl-dash-exam-*
 *
 * [Source: _bmad-output/implementation-artifacts/6-8-exam-record-persistence.md]
 *
 * @module ExamCard
 */

export interface ExamCardData {
    exam_id: string;
    source_canvas_name: string;
    exam_mode: string;
    created_at: string;
    active_duration_seconds: number;
    nodes_examined: number;
    discovered_nodes_count: number;
    mastery_trend: string; // "up" | "down" | "stable"
}

export interface ExamCardCallbacks {
    onSelect: (examId: string) => void;
}

export class ExamCard {
    private containerEl: HTMLElement;

    constructor(
        parentEl: HTMLElement,
        data: ExamCardData,
        callbacks: ExamCardCallbacks,
    ) {
        this.containerEl = parentEl.createDiv({ cls: 'cl-dash-exam-card' });
        this.render(data);
        this.containerEl.addEventListener('click', () => callbacks.onSelect(data.exam_id));
        this.injectStyles();
    }

    private render(data: ExamCardData): void {
        // Header row: canvas name + mode icon
        const headerEl = this.containerEl.createDiv({ cls: 'cl-dash-exam-header' });
        headerEl.createSpan({
            cls: 'cl-dash-exam-mode-icon',
            text: this.modeIcon(data.exam_mode),
        });
        headerEl.createSpan({
            cls: 'cl-dash-exam-canvas-name',
            text: data.source_canvas_name || 'Unnamed Canvas',
        });

        // Metrics row
        const metricsEl = this.containerEl.createDiv({ cls: 'cl-dash-exam-metrics' });

        // Date
        metricsEl.createSpan({
            cls: 'cl-dash-exam-date',
            text: this.formatDate(data.created_at),
        });

        // Duration
        metricsEl.createSpan({
            cls: 'cl-dash-exam-duration',
            text: this.formatDuration(data.active_duration_seconds),
        });

        // Node count
        metricsEl.createSpan({
            cls: 'cl-dash-exam-nodes',
            text: `${data.nodes_examined} nodes`,
        });

        // Trend arrow
        const trendEl = metricsEl.createSpan({ cls: 'cl-dash-exam-trend' });
        if (data.mastery_trend === 'up') {
            trendEl.textContent = '\u2191';
            trendEl.classList.add('cl-dash-exam-trend-up');
        } else if (data.mastery_trend === 'down') {
            trendEl.textContent = '\u2193';
            trendEl.classList.add('cl-dash-exam-trend-down');
        } else {
            trendEl.textContent = '-';
            trendEl.classList.add('cl-dash-exam-trend-stable');
        }
    }

    private modeIcon(mode: string): string {
        const map: Record<string, string> = {
            point_to_point: '\u{1f3af}',
            comprehensive: '\u{1f4dd}',
            mixed: '\u{1f500}',
        };
        return map[mode] || '\u{1f4cb}';
    }

    private formatDate(isoString: string): string {
        if (!isoString) return '-';
        try {
            const d = new Date(isoString);
            return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
        } catch {
            return isoString.substring(0, 10);
        }
    }

    private formatDuration(seconds: number): string {
        const m = Math.floor(seconds / 60);
        if (m < 1) return '<1 min';
        return `${m} min`;
    }

    private injectStyles(): void {
        const styleId = 'cl-dash-exam-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-dash-exam-card {
                padding: 12px 16px;
                border-radius: 8px;
                background: var(--background-modifier-form-field);
                cursor: pointer;
                transition: background 0.2s ease;
                margin-bottom: 8px;
            }
            .cl-dash-exam-card:hover {
                background: var(--background-modifier-hover);
            }
            .cl-dash-exam-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            .cl-dash-exam-mode-icon {
                font-size: 16px;
            }
            .cl-dash-exam-canvas-name {
                font-weight: 600;
                font-size: 14px;
                color: var(--text-normal);
            }
            .cl-dash-exam-metrics {
                display: flex;
                gap: 16px;
                font-size: 12px;
                color: var(--text-muted);
            }
            .cl-dash-exam-trend {
                font-weight: 700;
            }
            .cl-dash-exam-trend-up {
                color: var(--text-success, #198754);
            }
            .cl-dash-exam-trend-down {
                color: var(--text-error, #dc3545);
            }
            .cl-dash-exam-trend-stable {
                color: var(--text-muted);
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        this.containerEl.remove();
    }
}
