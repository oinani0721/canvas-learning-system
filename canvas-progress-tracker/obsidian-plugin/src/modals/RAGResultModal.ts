/**
 * RAG Result Modal - Intelligent RAG Query Results Display
 *
 * Modal dialog for displaying RAG (Retrieval-Augmented Generation) query results.
 * Shows search results, quality grade, latency info, and metadata.
 *
 * @module modals/RAGResultModal
 * @version 1.0.0
 * @story Story 20.1 - RAG UI Integration
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from types.ts (RAGQueryResponse, RAGSearchResultItem)
 */

import { App, Modal, Notice } from 'obsidian';
import type {
    RAGQueryResponse,
    RAGSearchResultItem,
    RAGQualityGrade,
    WeakConceptsResponse,
    WeakConceptItem,
} from '../api/types';

/**
 * Quality grade display configuration
 */
const QUALITY_GRADE_CONFIG: Record<RAGQualityGrade, { emoji: string; label: string; color: string }> = {
    high: { emoji: '🟢', label: '高质量', color: 'var(--text-success)' },
    medium: { emoji: '🟡', label: '中等质量', color: 'var(--text-warning)' },
    low: { emoji: '🔴', label: '低质量', color: 'var(--text-error)' },
};

/**
 * RAG Result Modal
 *
 * Displays RAG query results with:
 * - Quality grade indicator
 * - Search results list with scores
 * - Latency breakdown
 * - Query metadata (rewriting info)
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class RAGResultModal extends Modal {
    private result: RAGQueryResponse;
    private query: string;

    /**
     * Creates a new RAGResultModal
     *
     * @param app - Obsidian App instance
     * @param result - RAG query response from backend
     * @param query - Original query string
     */
    constructor(app: App, result: RAGQueryResponse, query: string) {
        super(app);
        this.result = result;
        this.query = query;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('rag-result-modal');

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
        const header = contentEl.createEl('div', { cls: 'rag-result-header' });
        header.createEl('h2', { text: '🔍 RAG智能检索结果' });

        // Query display
        const querySection = contentEl.createEl('div', { cls: 'rag-query-section' });
        querySection.createEl('span', { text: '查询: ', cls: 'rag-query-label' });
        querySection.createEl('span', { text: this.query, cls: 'rag-query-text' });

        // Quality grade and stats
        this.renderStatsGrid();

        // Results list
        this.renderResults();

        // Metadata section
        this.renderMetadata();

        // Footer with close button
        this.renderFooter();
    }

    /**
     * Render statistics grid
     */
    private renderStatsGrid(): void {
        const { contentEl } = this;
        const statsGrid = contentEl.createEl('div', { cls: 'rag-stats-grid' });

        // Quality grade
        const gradeConfig = QUALITY_GRADE_CONFIG[this.result.quality_grade];
        const gradeCard = statsGrid.createEl('div', { cls: 'rag-stat-card' });
        gradeCard.createEl('div', {
            text: gradeConfig.emoji,
            cls: 'rag-stat-icon',
        });
        gradeCard.createEl('div', {
            text: gradeConfig.label,
            cls: 'rag-stat-label',
        });

        // Result count
        const countCard = statsGrid.createEl('div', { cls: 'rag-stat-card' });
        countCard.createEl('div', {
            text: String(this.result.result_count),
            cls: 'rag-stat-value',
        });
        countCard.createEl('div', {
            text: '相关结果',
            cls: 'rag-stat-label',
        });

        // Total latency
        const latencyCard = statsGrid.createEl('div', { cls: 'rag-stat-card' });
        latencyCard.createEl('div', {
            text: `${this.result.total_latency_ms}ms`,
            cls: 'rag-stat-value',
        });
        latencyCard.createEl('div', {
            text: '响应时间',
            cls: 'rag-stat-label',
        });
    }

    /**
     * Render search results list
     */
    private renderResults(): void {
        const { contentEl } = this;

        if (this.result.results.length === 0) {
            const emptyState = contentEl.createEl('div', { cls: 'rag-empty-state' });
            emptyState.createEl('p', { text: '未找到相关知识点' });
            return;
        }

        const resultsSection = contentEl.createEl('div', { cls: 'rag-results-section' });
        resultsSection.createEl('h3', { text: '检索结果', cls: 'rag-section-title' });

        const resultsList = resultsSection.createEl('div', { cls: 'rag-results-list' });

        for (const item of this.result.results) {
            this.renderResultItem(resultsList, item);
        }
    }

    /**
     * Render a single result item
     */
    private renderResultItem(container: HTMLElement, item: RAGSearchResultItem): void {
        const resultItem = container.createEl('div', { cls: 'rag-result-item' });

        // Score badge
        const scoreBadge = resultItem.createEl('div', { cls: 'rag-score-badge' });
        const scorePercent = Math.round(item.score * 100);
        scoreBadge.createEl('span', {
            text: `${scorePercent}%`,
            cls: this.getScoreClass(item.score),
        });

        // Content
        const contentDiv = resultItem.createEl('div', { cls: 'rag-result-content' });

        // Source info from metadata or doc_id
        const sourceInfo = contentDiv.createEl('div', { cls: 'rag-source-info' });
        sourceInfo.createEl('span', {
            text: `📄 ${item.doc_id}`,
            cls: 'rag-source-file',
        });

        // Content text
        contentDiv.createEl('p', {
            text: this.truncateContent(item.content, 300),
            cls: 'rag-result-text',
        });

        // Copy button
        const copyBtn = resultItem.createEl('button', {
            text: '📋 复制',
            cls: 'rag-copy-btn',
        });
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(item.content);
            new Notice('已复制到剪贴板');
        });
    }

    /**
     * Get CSS class based on score
     */
    private getScoreClass(score: number): string {
        if (score >= 0.8) return 'rag-score-high';
        if (score >= 0.5) return 'rag-score-medium';
        return 'rag-score-low';
    }

    /**
     * Render metadata section
     */
    private renderMetadata(): void {
        const { contentEl } = this;
        const metaSection = contentEl.createEl('div', { cls: 'rag-metadata-section' });

        metaSection.createEl('h4', { text: '查询信息', cls: 'rag-meta-title' });

        const metaList = metaSection.createEl('ul', { cls: 'rag-meta-list' });

        // Query rewriting
        if (this.result.metadata.query_rewritten) {
            metaList.createEl('li', {
                text: `✅ 查询已优化 (重写${this.result.metadata.rewrite_count}次)`,
            });
        } else {
            metaList.createEl('li', {
                text: '原始查询 (未重写)',
            });
        }

        // Fusion strategy
        if (this.result.metadata.fusion_strategy) {
            metaList.createEl('li', {
                text: `融合策略: ${this.result.metadata.fusion_strategy}`,
            });
        }

        // Reranking strategy
        if (this.result.metadata.reranking_strategy) {
            metaList.createEl('li', {
                text: `重排策略: ${this.result.metadata.reranking_strategy}`,
            });
        }

        // Latency breakdown
        if (this.result.latency_ms) {
            const latencyInfo = this.result.latency_ms;
            const latencyParts: string[] = [];
            if (latencyInfo.graphiti) latencyParts.push(`Graphiti: ${latencyInfo.graphiti}ms`);
            if (latencyInfo.lancedb) latencyParts.push(`LanceDB: ${latencyInfo.lancedb}ms`);
            if (latencyInfo.fusion) latencyParts.push(`融合: ${latencyInfo.fusion}ms`);
            if (latencyParts.length > 0) {
                metaList.createEl('li', {
                    text: `延迟明细: ${latencyParts.join(', ')}`,
                });
            }
        }
    }

    /**
     * Render modal footer
     */
    private renderFooter(): void {
        const { contentEl } = this;
        const footer = contentEl.createEl('div', { cls: 'rag-modal-footer' });

        const closeBtn = footer.createEl('button', {
            text: '关闭',
            cls: 'mod-cta',
        });
        closeBtn.addEventListener('click', () => this.close());
    }

    /**
     * Truncate content to specified length
     */
    private truncateContent(text: string, maxLength: number): string {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength - 3) + '...';
    }
}

/**
 * Weak Concepts Modal
 *
 * Displays weak concepts that need review, based on temporal memory analysis.
 *
 * ✅ Verified from types.ts (WeakConceptsResponse, WeakConceptItem)
 */
export class WeakConceptsModal extends Modal {
    private response: WeakConceptsResponse;

    /**
     * Creates a new WeakConceptsModal
     *
     * @param app - Obsidian App instance
     * @param response - Weak concepts response from backend
     */
    constructor(app: App, response: WeakConceptsResponse) {
        super(app);
        this.response = response;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('weak-concepts-modal');

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
        const header = contentEl.createEl('div', { cls: 'weak-concepts-header' });
        header.createEl('h2', { text: '🧠 薄弱概念分析' });

        // Canvas file info
        const infoSection = contentEl.createEl('div', { cls: 'weak-concepts-info' });
        infoSection.createEl('p', {
            text: `Canvas: ${this.response.canvas_file || '全局分析'}`,
        });
        infoSection.createEl('p', {
            text: `共发现 ${this.response.total_count} 个需要复习的概念`,
        });

        // Concepts list
        this.renderConceptsList();

        // Footer
        this.renderFooter();
    }

    /**
     * Render concepts list
     */
    private renderConceptsList(): void {
        const { contentEl } = this;

        if (this.response.concepts.length === 0) {
            const emptyState = contentEl.createEl('div', { cls: 'weak-concepts-empty' });
            emptyState.createEl('p', { text: '🎉 没有发现薄弱概念，继续保持！' });
            return;
        }

        const listSection = contentEl.createEl('div', { cls: 'weak-concepts-list-section' });
        listSection.createEl('h3', { text: '需要复习的概念', cls: 'section-title' });

        const conceptsList = listSection.createEl('div', { cls: 'weak-concepts-list' });

        for (const concept of this.response.concepts) {
            this.renderConceptItem(conceptsList, concept);
        }
    }

    /**
     * Render a single concept item
     */
    private renderConceptItem(container: HTMLElement, item: WeakConceptItem): void {
        const conceptItem = container.createEl('div', { cls: 'weak-concept-item' });

        // Stability indicator
        const stabilityBar = conceptItem.createEl('div', { cls: 'stability-bar' });
        const stabilityPercent = Math.round(item.stability * 100);
        const stabilityFill = stabilityBar.createEl('div', {
            cls: `stability-fill ${this.getStabilityClass(item.stability)}`,
        });
        stabilityFill.style.width = `${stabilityPercent}%`;

        // Concept info
        const infoDiv = conceptItem.createEl('div', { cls: 'concept-info' });
        infoDiv.createEl('span', { text: item.concept, cls: 'concept-name' });

        // Stats
        const statsDiv = conceptItem.createEl('div', { cls: 'concept-stats' });
        statsDiv.createEl('span', {
            text: `稳定性: ${stabilityPercent}%`,
            cls: 'stability-text',
        });
        statsDiv.createEl('span', {
            text: `复习次数: ${item.review_count}`,
            cls: 'review-count',
        });
        if (item.last_review) {
            statsDiv.createEl('span', {
                text: `上次复习: ${this.formatDate(item.last_review)}`,
                cls: 'last-review',
            });
        }
    }

    /**
     * Get CSS class based on stability
     */
    private getStabilityClass(stability: number): string {
        if (stability >= 0.7) return 'stability-high';
        if (stability >= 0.4) return 'stability-medium';
        return 'stability-low';
    }

    /**
     * Format date string
     */
    private formatDate(dateStr: string): string {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric',
            });
        } catch {
            return dateStr;
        }
    }

    /**
     * Render modal footer
     */
    private renderFooter(): void {
        const { contentEl } = this;
        const footer = contentEl.createEl('div', { cls: 'weak-concepts-footer' });

        const closeBtn = footer.createEl('button', {
            text: '关闭',
            cls: 'mod-cta',
        });
        closeBtn.addEventListener('click', () => this.close());
    }
}
