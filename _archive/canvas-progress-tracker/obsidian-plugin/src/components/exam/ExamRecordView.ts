/**
 * Canvas Learning System - Exam Record View Component
 *
 * Story 6.8 AC-3, AC-4: Full exam record detail display.
 * - Overview section: 4 key metric cards
 * - Node score list: table with 4-dim scores + grade + mastery change
 * - Conversation replay: collapsible per-node
 * - Discovered nodes: tree/chain layout showing recursion
 * - CSS prefix: cl-exam-record-*
 * - Light/Dark adaptive
 *
 * [Source: _bmad-output/implementation-artifacts/6-8-exam-record-persistence.md]
 *
 * @module ExamRecordView
 */

import { requestUrl } from 'obsidian';

export interface ExamRecordData {
    exam_id: string;
    source_canvas_name: string;
    exam_mode: string;
    start_time: string;
    end_time: string;
    active_duration_seconds: number;
    status: string;
    nodes_examined: number;
    score_history: any[];
    discovered_nodes: any[];
    skipped_nodes: any[];
    conversation_log: any[];
    mastery_changes: any[];
}

export class ExamRecordView {
    private containerEl: HTMLElement;

    constructor(parentEl: HTMLElement, data: ExamRecordData) {
        this.containerEl = parentEl.createDiv({ cls: 'cl-exam-record-container' });
        this.render(data);
        this.injectStyles();
    }

    private render(data: ExamRecordData): void {
        // Overview cards
        const overviewEl = this.containerEl.createDiv({ cls: 'cl-exam-record-overview' });
        this.renderMetricCard(overviewEl, '\u8003\u5bdf\u6a21\u5f0f', this.formatMode(data.exam_mode));
        this.renderMetricCard(overviewEl, '\u8003\u5bdf\u65f6\u957f', this.formatDuration(data.active_duration_seconds));
        this.renderMetricCard(overviewEl, '\u8003\u5bdf\u8282\u70b9', String(data.nodes_examined));
        this.renderMetricCard(overviewEl, '\u65b0\u53d1\u73b0', String(data.discovered_nodes.length));

        // Node score table
        if (data.score_history.length > 0) {
            const scoreSection = this.containerEl.createDiv({ cls: 'cl-exam-record-section' });
            scoreSection.createEl('h4', { text: '\u8282\u70b9\u8bc4\u5206', cls: 'cl-exam-record-section-title' });
            this.renderScoreTable(scoreSection, data.score_history);
        }

        // Discovered nodes chain
        if (data.discovered_nodes.length > 0) {
            const discoverSection = this.containerEl.createDiv({ cls: 'cl-exam-record-section' });
            discoverSection.createEl('h4', { text: '\u65b0\u53d1\u73b0\u8282\u70b9', cls: 'cl-exam-record-section-title' });
            this.renderDiscoveryChain(discoverSection, data.discovered_nodes);
        }

        // Conversation replay (collapsible)
        if (data.conversation_log.length > 0) {
            const convSection = this.containerEl.createDiv({ cls: 'cl-exam-record-section' });
            convSection.createEl('h4', { text: '\u5bf9\u8bdd\u56de\u653e', cls: 'cl-exam-record-section-title' });
            this.renderConversationReplay(convSection, data.conversation_log);
        }
    }

    private renderMetricCard(parentEl: HTMLElement, label: string, value: string): void {
        const card = parentEl.createDiv({ cls: 'cl-exam-record-card' });
        card.createDiv({ cls: 'cl-exam-record-card-value', text: value });
        card.createDiv({ cls: 'cl-exam-record-card-label', text: label });
    }

    private renderScoreTable(parentEl: HTMLElement, scores: any[]): void {
        const table = parentEl.createEl('table', { cls: 'cl-exam-record-table' });
        const thead = table.createEl('thead');
        const headerRow = thead.createEl('tr');
        const headers = ['\u8282\u70b9', '\u6982\u5ff5', '\u63a8\u7406', '\u8986\u76d6', '\u6574\u5408', '\u603b\u5206', '\u7b49\u7ea7', '\u7cbe\u901a\u5ea6\u53d8\u5316'];
        headers.forEach(h => headerRow.createEl('th', { text: h }));

        const tbody = table.createEl('tbody');
        for (const score of scores) {
            const row = tbody.createEl('tr');
            row.createEl('td', { text: score.node_text || score.node_id || '-' });
            row.createEl('td', { text: String(score.concept_accuracy ?? '-') });
            row.createEl('td', { text: String(score.reasoning_quality ?? '-') });
            row.createEl('td', { text: String(score.knowledge_coverage ?? '-') });
            row.createEl('td', { text: String(score.knowledge_integration ?? '-') });
            row.createEl('td', { text: String(score.overall_score ?? '-') });
            row.createEl('td', { text: this.gradeLabel(score.grade) });

            const delta = (score.proficiency_after ?? 0) - (score.proficiency_before ?? 0);
            const trend = delta > 0.01 ? '\u2191' : delta < -0.01 ? '\u2193' : '-';
            row.createEl('td', { text: trend });
        }
    }

    private renderDiscoveryChain(parentEl: HTMLElement, nodes: any[]): void {
        const listEl = parentEl.createDiv({ cls: 'cl-exam-record-discovery-chain' });
        for (const node of nodes) {
            const item = listEl.createDiv({ cls: 'cl-exam-record-discovery-item' });
            const indent = '\u00a0'.repeat((node.depth || 1) * 4);
            const arrow = node.depth > 1 ? '\u2514\u2500 ' : '\u25cf ';
            item.textContent = `${indent}${arrow}${node.node_id} (depth: ${node.depth || 1})`;
        }
    }

    private renderConversationReplay(parentEl: HTMLElement, messages: any[]): void {
        // Group messages by node_id
        const groups = new Map<string, any[]>();
        for (const msg of messages) {
            const key = msg.node_id || 'general';
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key)!.push(msg);
        }

        for (const [nodeId, msgs] of groups) {
            const details = parentEl.createEl('details', { cls: 'cl-exam-record-conv-group' });
            details.createEl('summary', { text: `\u8282\u70b9: ${nodeId} (${msgs.length} \u6761\u6d88\u606f)` });
            const content = details.createDiv({ cls: 'cl-exam-record-conv-messages' });
            for (const msg of msgs) {
                const msgEl = content.createDiv({
                    cls: `cl-exam-record-conv-msg cl-exam-record-conv-${msg.role || 'user'}`,
                });
                msgEl.createSpan({ cls: 'cl-exam-record-conv-role', text: `[${msg.role}]` });
                msgEl.createSpan({ cls: 'cl-exam-record-conv-text', text: ` ${msg.content}` });
            }
        }
    }

    private formatMode(mode: string): string {
        const map: Record<string, string> = {
            point_to_point: '\u70b9\u5bf9\u70b9',
            comprehensive: '\u7efc\u5408\u9898',
            mixed: '\u6df7\u5408',
        };
        return map[mode] || mode;
    }

    private formatDuration(seconds: number): string {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}\u5206${s}\u79d2`;
    }

    private gradeLabel(grade: number): string {
        const map: Record<number, string> = {
            1: 'Forgot',
            2: 'Struggled',
            3: 'Correct',
            4: 'Fluent',
        };
        return map[grade] || String(grade);
    }

    private injectStyles(): void {
        const styleId = 'cl-exam-record-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .cl-exam-record-container {
                padding: 16px;
            }
            .cl-exam-record-overview {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin-bottom: 20px;
            }
            .cl-exam-record-card {
                padding: 12px;
                border-radius: 8px;
                background: var(--background-modifier-form-field);
                text-align: center;
            }
            .cl-exam-record-card-value {
                font-size: 20px;
                font-weight: 700;
                color: var(--text-normal);
            }
            .cl-exam-record-card-label {
                font-size: 12px;
                color: var(--text-muted);
                margin-top: 4px;
            }
            .cl-exam-record-section {
                margin-bottom: 16px;
            }
            .cl-exam-record-section-title {
                margin: 0 0 8px 0;
                font-size: 14px;
                color: var(--text-normal);
            }
            .cl-exam-record-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }
            .cl-exam-record-table th,
            .cl-exam-record-table td {
                padding: 6px 8px;
                border-bottom: 1px solid var(--background-modifier-border);
                text-align: center;
            }
            .cl-exam-record-table th {
                background: var(--background-modifier-form-field);
                font-weight: 600;
                color: var(--text-muted);
            }
            .cl-exam-record-discovery-chain {
                font-family: var(--font-monospace);
                font-size: 13px;
                line-height: 1.8;
            }
            .cl-exam-record-conv-group {
                margin-bottom: 8px;
            }
            .cl-exam-record-conv-group summary {
                cursor: pointer;
                font-weight: 500;
                padding: 4px 0;
            }
            .cl-exam-record-conv-messages {
                padding-left: 16px;
                border-left: 2px solid var(--background-modifier-border);
            }
            .cl-exam-record-conv-msg {
                padding: 4px 0;
                font-size: 13px;
            }
            .cl-exam-record-conv-role {
                font-weight: 600;
                color: var(--text-muted);
            }
            .cl-exam-record-conv-user { }
            .cl-exam-record-conv-assistant {
                color: var(--interactive-accent);
            }
            .cl-exam-record-conv-hint {
                color: var(--text-warning, #e2b340);
            }
            .cl-exam-record-conv-rest_reminder {
                color: var(--text-accent);
            }
        `;
        document.head.appendChild(style);
    }

    destroy(): void {
        this.containerEl.remove();
    }
}
