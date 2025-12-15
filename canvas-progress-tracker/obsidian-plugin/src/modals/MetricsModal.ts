/**
 * Metrics Modal - System Performance Monitoring Display
 *
 * Modal dialog for displaying system metrics and performance monitoring data.
 * Shows API metrics, agent execution stats, memory system status, and resource usage.
 *
 * @module modals/MetricsModal
 * @version 1.0.0
 * @story Story 20.3 - Monitoring System UI Integration
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from types.ts (MetricsSummaryResponse)
 */

import { App, Modal } from 'obsidian';
import type {
    MetricsSummaryResponse,
    APIMetricsSummary,
    AgentMetricsSummary,
    AgentTypeSummary,
    MemorySystemSummary,
    ResourcesSummary,
    AlertsSummary,
} from '../api/types';

/**
 * Alert severity display configuration
 */
const ALERT_SEVERITY_CONFIG: Record<string, { emoji: string; color: string }> = {
    critical: { emoji: '🔴', color: 'var(--text-error)' },
    warning: { emoji: '🟡', color: 'var(--text-warning)' },
    info: { emoji: '🔵', color: 'var(--text-accent)' },
};

/**
 * Metrics Modal
 *
 * Displays comprehensive system metrics:
 * - API performance (requests, latency, error rate)
 * - Agent execution statistics
 * - Memory system status (Graphiti, Temporal, Semantic)
 * - Resource usage (CPU, memory)
 * - Active alerts
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class MetricsModal extends Modal {
    private metrics: MetricsSummaryResponse;

    /**
     * Creates a new MetricsModal
     *
     * @param app - Obsidian App instance
     * @param metrics - Metrics summary response from backend
     */
    constructor(app: App, metrics: MetricsSummaryResponse) {
        super(app);
        this.metrics = metrics;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('metrics-modal');

        this.renderContent();
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Render main content
     */
    private renderContent(): void {
        const { contentEl } = this;

        // Header
        const header = contentEl.createEl('div', { cls: 'metrics-header' });
        header.createEl('h2', { text: '📊 系统性能监控' });
        header.createEl('p', {
            text: `数据时间: ${this.formatTimestamp(this.metrics.timestamp)}`,
            cls: 'metrics-timestamp',
        });

        // Alerts section (if any)
        if (this.metrics.alerts && this.metrics.alerts.active_count > 0) {
            this.renderAlertsSection();
        }

        // Stats overview grid
        this.renderOverviewGrid();

        // Detailed sections
        this.renderAPIMetrics();
        this.renderAgentMetrics();
        this.renderMemoryMetrics();
        this.renderResourceMetrics();

        // Footer
        this.renderFooter();
    }

    /**
     * Render alerts section
     */
    private renderAlertsSection(): void {
        const { contentEl } = this;
        const alertsSection = contentEl.createEl('div', { cls: 'metrics-alerts-section' });

        alertsSection.createEl('h3', { text: '⚠️ 活动告警', cls: 'section-title' });

        const alertsList = alertsSection.createEl('div', { cls: 'alerts-list' });

        // Display alert counts (AlertsSummary only has counts, not individual alerts)
        const alertItem = alertsList.createEl('div', { cls: 'alert-item' });
        if (this.metrics.alerts.critical_count > 0) {
            alertItem.createEl('span', { text: ALERT_SEVERITY_CONFIG.critical.emoji, cls: 'alert-icon' });
            alertItem.createEl('span', { text: `严重告警: ${this.metrics.alerts.critical_count}`, cls: 'alert-message' });
        }
        if (this.metrics.alerts.warning_count > 0) {
            const warningItem = alertsList.createEl('div', { cls: 'alert-item' });
            warningItem.createEl('span', { text: ALERT_SEVERITY_CONFIG.warning.emoji, cls: 'alert-icon' });
            warningItem.createEl('span', { text: `警告: ${this.metrics.alerts.warning_count}`, cls: 'alert-message' });
        }
        if (this.metrics.alerts.info_count > 0) {
            const infoItem = alertsList.createEl('div', { cls: 'alert-item' });
            infoItem.createEl('span', { text: ALERT_SEVERITY_CONFIG.info.emoji, cls: 'alert-icon' });
            infoItem.createEl('span', { text: `信息: ${this.metrics.alerts.info_count}`, cls: 'alert-message' });
        }
    }

    /**
     * Render overview statistics grid
     */
    private renderOverviewGrid(): void {
        const { contentEl } = this;
        const grid = contentEl.createEl('div', { cls: 'metrics-overview-grid' });

        // Total requests
        this.renderStatCard(grid, {
            value: this.formatNumber(this.metrics.api.requests_total),
            label: '总请求数',
            icon: '📨',
        });

        // RPS
        this.renderStatCard(grid, {
            value: this.metrics.api.requests_per_second.toFixed(1),
            label: '请求/秒',
            icon: '⚡',
        });

        // Avg latency
        this.renderStatCard(grid, {
            value: `${this.metrics.api.avg_latency_ms.toFixed(0)}ms`,
            label: '平均延迟',
            icon: '⏱️',
        });

        // Error rate
        this.renderStatCard(grid, {
            value: `${(this.metrics.api.error_rate * 100).toFixed(2)}%`,
            label: '错误率',
            icon: this.metrics.api.error_rate > 0.05 ? '🔴' : '🟢',
        });
    }

    /**
     * Render a single stat card
     */
    private renderStatCard(
        container: HTMLElement,
        config: { value: string; label: string; icon: string }
    ): void {
        const card = container.createEl('div', { cls: 'metrics-stat-card' });
        card.createEl('div', { text: config.icon, cls: 'stat-icon' });
        card.createEl('div', { text: config.value, cls: 'stat-value' });
        card.createEl('div', { text: config.label, cls: 'stat-label' });
    }

    /**
     * Render API metrics section
     */
    private renderAPIMetrics(): void {
        const { contentEl } = this;
        const section = contentEl.createEl('div', { cls: 'metrics-section' });

        section.createEl('h3', { text: '🌐 API性能', cls: 'section-title' });

        const table = section.createEl('table', { cls: 'metrics-table' });
        const tbody = table.createEl('tbody');

        this.addTableRow(tbody, 'P95延迟', `${this.metrics.api.p95_latency_ms.toFixed(0)}ms`);
        this.addTableRow(tbody, '平均延迟', `${this.metrics.api.avg_latency_ms.toFixed(0)}ms`);
        this.addTableRow(tbody, '错误率', `${(this.metrics.api.error_rate * 100).toFixed(2)}%`);
        this.addTableRow(tbody, '总请求数', this.formatNumber(this.metrics.api.requests_total));
    }

    /**
     * Render agent metrics section
     */
    private renderAgentMetrics(): void {
        const { contentEl } = this;
        const section = contentEl.createEl('div', { cls: 'metrics-section' });

        section.createEl('h3', { text: '🤖 Agent执行统计', cls: 'section-title' });

        // Summary stats
        const summaryDiv = section.createEl('div', { cls: 'agent-summary' });
        summaryDiv.createEl('p', {
            text: `总调用次数: ${this.formatNumber(this.metrics.agents.invocations_total)}`,
        });
        summaryDiv.createEl('p', {
            text: `平均执行时间: ${this.metrics.agents.avg_execution_time_s.toFixed(2)}s`,
        });

        // By type breakdown
        if (this.metrics.agents.by_type && this.metrics.agents.by_type.length > 0) {
            const typeSection = section.createEl('div', { cls: 'agent-by-type' });
            typeSection.createEl('h4', { text: '按类型统计' });

            const table = typeSection.createEl('table', { cls: 'metrics-table' });
            const thead = table.createEl('thead');
            const headerRow = thead.createEl('tr');
            headerRow.createEl('th', { text: 'Agent类型' });
            headerRow.createEl('th', { text: '调用次数' });
            headerRow.createEl('th', { text: '平均时间' });
            headerRow.createEl('th', { text: '成功率' });

            const tbody = table.createEl('tbody');
            for (const agent of this.metrics.agents.by_type) {
                const row = tbody.createEl('tr');
                row.createEl('td', { text: this.formatAgentType(agent.agent_type) });
                row.createEl('td', { text: String(agent.invocations) });
                row.createEl('td', { text: `${agent.avg_execution_time_s.toFixed(2)}s` });
                row.createEl('td', { text: '-' }); // success_rate not available in AgentTypeSummary
            }
        }
    }

    /**
     * Render memory system metrics
     */
    private renderMemoryMetrics(): void {
        const { contentEl } = this;
        const section = contentEl.createEl('div', { cls: 'metrics-section' });

        section.createEl('h3', { text: '🧠 记忆系统', cls: 'section-title' });

        const memoryGrid = section.createEl('div', { cls: 'memory-metrics-grid' });

        // Graphiti
        if (this.metrics.memory_system.graphiti) {
            this.renderMemoryCard(memoryGrid, 'Graphiti', this.metrics.memory_system.graphiti);
        }

        // Temporal
        if (this.metrics.memory_system.temporal) {
            this.renderMemoryCard(memoryGrid, 'Temporal', this.metrics.memory_system.temporal);
        }

        // Semantic
        if (this.metrics.memory_system.semantic) {
            this.renderMemoryCard(memoryGrid, 'Semantic', this.metrics.memory_system.semantic);
        }
    }

    /**
     * Render a memory layer card
     */
    private renderMemoryCard(
        container: HTMLElement,
        name: string,
        data: { queries_total: number; avg_latency_ms: number }
    ): void {
        const card = container.createEl('div', { cls: 'memory-card' });
        card.createEl('h4', { text: name });
        card.createEl('p', { text: `查询次数: ${this.formatNumber(data.queries_total)}` });
        card.createEl('p', { text: `平均延迟: ${data.avg_latency_ms.toFixed(0)}ms` });
    }

    /**
     * Render resource usage metrics
     */
    private renderResourceMetrics(): void {
        const { contentEl } = this;
        const section = contentEl.createEl('div', { cls: 'metrics-section' });

        section.createEl('h3', { text: '💻 资源使用', cls: 'section-title' });

        const resourceGrid = section.createEl('div', { cls: 'resource-metrics-grid' });

        // CPU
        const cpuCard = resourceGrid.createEl('div', { cls: 'resource-card' });
        cpuCard.createEl('div', { text: 'CPU', cls: 'resource-name' });
        const cpuPercent = this.metrics.resources.cpu_usage_percent || 0;
        this.renderProgressBar(cpuCard, cpuPercent, 100);
        cpuCard.createEl('div', { text: `${cpuPercent.toFixed(1)}%`, cls: 'resource-value' });

        // Memory
        const memCard = resourceGrid.createEl('div', { cls: 'resource-card' });
        memCard.createEl('div', { text: '内存', cls: 'resource-name' });
        const memPercent = this.metrics.resources.memory_usage_percent || 0;
        this.renderProgressBar(memCard, memPercent, 100);
        memCard.createEl('div', {
            text: `${memPercent.toFixed(1)}%`,
            cls: 'resource-value',
        });
    }

    /**
     * Render a progress bar
     */
    private renderProgressBar(container: HTMLElement, value: number, max: number): void {
        const bar = container.createEl('div', { cls: 'progress-bar' });
        const fill = bar.createEl('div', { cls: 'progress-fill' });
        const percent = Math.min((value / max) * 100, 100);
        fill.style.width = `${percent}%`;

        // Color based on usage
        if (percent > 80) {
            fill.addClass('progress-high');
        } else if (percent > 50) {
            fill.addClass('progress-medium');
        } else {
            fill.addClass('progress-low');
        }
    }

    /**
     * Add a row to metrics table
     */
    private addTableRow(tbody: HTMLElement, label: string, value: string): void {
        const row = tbody.createEl('tr');
        row.createEl('td', { text: label });
        row.createEl('td', { text: value });
    }

    /**
     * Render modal footer
     */
    private renderFooter(): void {
        const { contentEl } = this;
        const footer = contentEl.createEl('div', { cls: 'metrics-modal-footer' });

        const closeBtn = footer.createEl('button', {
            text: '关闭',
            cls: 'mod-cta',
        });
        closeBtn.addEventListener('click', () => this.close());
    }

    /**
     * Format agent type for display
     */
    private formatAgentType(agentType: string): string {
        const typeMap: Record<string, string> = {
            'comparison-table': '对比表',
            'basic-decomposition': '基础拆解',
            'deep-decomposition': '深度拆解',
            'clarification-path': '澄清路径',
            'oral-explanation': '口语化解释',
            'four-level-explanation': '四层次解释',
            'example-teaching': '例题教学',
            'verification-question': '检验问题',
            'memory-anchor': '记忆锚点',
            'scoring-agent': '评分',
            'question-decomposition': '问题拆解',
            'canvas-orchestrator': '画布编排',
        };
        return typeMap[agentType] || agentType;
    }

    /**
     * Format timestamp
     */
    private formatTimestamp(timestamp: string): string {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN');
        } catch {
            return timestamp;
        }
    }

    /**
     * Format number with thousand separators
     */
    private formatNumber(num: number): string {
        return num.toLocaleString('zh-CN');
    }

    /**
     * Format bytes to human-readable size
     */
    private formatBytes(bytes: number): string {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    }
}
