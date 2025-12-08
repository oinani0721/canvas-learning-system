/**
 * Result Summary Modal - Intelligent Parallel Processing
 *
 * Modal dialog for displaying batch processing results.
 * Shows execution summary, document statistics, and failed node retry options.
 *
 * @module modals/ResultSummaryModal
 * @version 1.0.0
 * @story Story 13.8 Task 4
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 13.8 Dev Notes (ResultSummaryModal design)
 */

import { App, Modal, Notice, TFile } from 'obsidian';
import { NodeGroup } from './GroupPreviewModal';
import { NodeResult, SessionStatus } from './ProgressMonitorModal';
import { RetryPolicy, NetworkError } from '../errors';

/**
 * Document statistics by agent type
 */
export interface DocumentStat {
    agentType: string;
    count: number;
    emoji: string;
}

/**
 * Failed node with retry capability
 */
export interface FailedNode {
    nodeId: string;
    nodeText: string;
    errorMessage: string;
    recommendedAgent: string;
}

/**
 * Callbacks for ResultSummaryModal
 */
export interface ResultSummaryCallbacks {
    onClose: () => void;
    onRetryNode?: (nodeId: string, agent: string) => Promise<boolean>;
}

/**
 * Agent emoji mapping
 */
const AGENT_EMOJI: Record<string, string> = {
    'comparison-table': '📊',
    'basic-decomposition': '🔍',
    'deep-decomposition': '🧠',
    'clarification-path': '💡',
    'oral-explanation': '🗣️',
    'four-level-explanation': '📚',
    'example-teaching': '✏️',
    'verification-question': '❓',
    'memory-anchor': '⚓',
    'scoring-agent': '⭐',
    'question-decomposition': '🎯',
    'canvas-orchestrator': '🎭',
    'default': '🤖',
};

/**
 * Agent display names
 */
const AGENT_NAMES: Record<string, string> = {
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
    'default': 'Agent',
};

/**
 * Result Summary Modal
 *
 * Displays:
 * - Execution summary (success/failed counts, total time)
 * - Document statistics by agent type
 * - Failed node list with retry functionality
 * - Error log viewer
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class ResultSummaryModal extends Modal {
    private canvasFile: TFile;
    private sessionStatus: SessionStatus;
    private groups: NodeGroup[];
    private apiBaseUrl: string;
    private callbacks: ResultSummaryCallbacks;
    private failedNodes: FailedNode[];
    private documentStats: DocumentStat[];

    /**
     * Creates a new ResultSummaryModal
     *
     * @param app - Obsidian App instance
     * @param canvasFile - The Canvas file that was processed
     * @param sessionStatus - Final session status from processing
     * @param groups - Original node groups
     * @param apiBaseUrl - Base URL for API calls (for retry)
     * @param callbacks - Callbacks for close and retry actions
     */
    constructor(
        app: App,
        canvasFile: TFile,
        sessionStatus: SessionStatus,
        groups: NodeGroup[],
        apiBaseUrl: string,
        callbacks: ResultSummaryCallbacks
    ) {
        super(app);
        this.canvasFile = canvasFile;
        this.sessionStatus = sessionStatus;
        this.groups = groups;
        this.apiBaseUrl = apiBaseUrl;
        this.callbacks = callbacks;

        // Extract failed nodes from session status
        this.failedNodes = this.extractFailedNodes();

        // Calculate document statistics
        this.documentStats = this.calculateDocumentStats();
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('intelligent-parallel-modal');
        contentEl.addClass('result-summary-modal');

        this.renderContent();
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
        this.callbacks.onClose();
    }

    /**
     * Extract failed nodes from session status
     */
    private extractFailedNodes(): FailedNode[] {
        const failed: FailedNode[] = [];

        for (const result of this.sessionStatus.node_results || []) {
            if (result.status === 'failed') {
                // Find the group this node belongs to
                const group = this.groups.find(g =>
                    g.nodes.some(n => n.id === result.node_id)
                );
                const node = group?.nodes.find(n => n.id === result.node_id);

                failed.push({
                    nodeId: result.node_id,
                    nodeText: node?.text || result.node_id,
                    errorMessage: result.error || 'Unknown error',
                    recommendedAgent: group?.recommended_agent || 'basic-decomposition',
                });
            }
        }

        return failed;
    }

    /**
     * Calculate document statistics by agent type
     */
    private calculateDocumentStats(): DocumentStat[] {
        const stats: Map<string, number> = new Map();

        // Count successful results by agent type
        for (const result of this.sessionStatus.node_results || []) {
            if (result.status === 'success') {
                // Find the group this node belongs to
                const group = this.groups.find(g =>
                    g.nodes.some(n => n.id === result.node_id)
                );
                if (group) {
                    const agent = group.recommended_agent;
                    stats.set(agent, (stats.get(agent) || 0) + 1);
                }
            }
        }

        // Convert to array with emoji
        return Array.from(stats.entries()).map(([agentType, count]) => ({
            agentType,
            count,
            emoji: AGENT_EMOJI[agentType] || AGENT_EMOJI['default'],
        }));
    }

    /**
     * Render main content
     */
    private renderContent(): void {
        const { contentEl } = this;

        // Header with result icon
        const header = contentEl.createEl('div', { cls: 'result-header' });
        const isFullSuccess = this.failedNodes.length === 0;
        const resultIcon = isFullSuccess ? '✅' : '⚠️';
        const resultTitle = isFullSuccess ? '处理完成' : '处理完成（部分失败）';

        header.createEl('div', {
            text: resultIcon,
            cls: 'result-icon',
        });
        header.createEl('h2', {
            text: `⚡ 智能并行处理 - ${resultTitle}`,
            cls: 'result-title',
        });

        // Subtitle with canvas file
        header.createEl('p', {
            text: this.canvasFile.basename,
            cls: 'result-subtitle',
        });

        // Statistics grid
        this.renderStatsGrid();

        // Document statistics
        if (this.documentStats.length > 0) {
            this.renderDocumentStats();
        }

        // Failed nodes (if any)
        if (this.failedNodes.length > 0) {
            this.renderFailedNodes();
        }

        // Canvas update notice
        const successCount = (this.sessionStatus.node_results || []).filter(r => r.status === 'success').length;
        if (successCount > 0) {
            const notice = contentEl.createEl('div', { cls: 'canvas-update-notice' });
            notice.createEl('p', {
                text: `Canvas已自动更新，添加了${successCount}个蓝色说明节点和${successCount}个文档节点`,
            });
        }

        // Footer with buttons
        this.renderFooter();
    }

    /**
     * Render statistics grid
     */
    private renderStatsGrid(): void {
        const { contentEl } = this;
        const statsGrid = contentEl.createEl('div', { cls: 'stats-grid' });

        // Total nodes
        const nodeResults = this.sessionStatus.node_results || [];
        const totalNodes = nodeResults.length;
        const successNodes = nodeResults.filter(r => r.status === 'success').length;
        const failedNodes = this.failedNodes.length;

        // Success stat
        const successCard = statsGrid.createEl('div', { cls: 'stat-card' });
        successCard.createEl('div', {
            text: String(successNodes),
            cls: 'stat-value',
        });
        successCard.createEl('div', {
            text: '成功处理',
            cls: 'stat-label',
        });

        // Failed stat
        const failedCard = statsGrid.createEl('div', { cls: 'stat-card' });
        failedCard.createEl('div', {
            text: String(failedNodes),
            cls: 'stat-value',
        });
        failedCard.createEl('div', {
            text: '失败节点',
            cls: 'stat-label',
        });

        // Total time stat
        const timeCard = statsGrid.createEl('div', { cls: 'stat-card' });
        const totalTime = this.formatTime(this.sessionStatus.elapsed_seconds || 0);
        timeCard.createEl('div', {
            text: totalTime,
            cls: 'stat-value',
        });
        timeCard.createEl('div', {
            text: '总耗时',
            cls: 'stat-label',
        });
    }

    /**
     * Render document statistics
     */
    private renderDocumentStats(): void {
        const { contentEl } = this;
        const docSection = contentEl.createEl('div', { cls: 'document-stats-section' });

        docSection.createEl('h3', {
            text: '生成文档统计',
            cls: 'section-title',
        });

        const docList = docSection.createEl('div', { cls: 'document-stats-list' });

        for (const stat of this.documentStats) {
            const agentName = AGENT_NAMES[stat.agentType] || stat.agentType;
            docList.createEl('div', {
                text: `• ${stat.count}个${agentName} (${stat.emoji})`,
                cls: 'document-stat-item',
            });
        }
    }

    /**
     * Render failed nodes section
     */
    private renderFailedNodes(): void {
        const { contentEl } = this;
        const failedSection = contentEl.createEl('div', { cls: 'failed-nodes-section' });

        failedSection.createEl('h3', {
            text: '❌ 失败节点',
            cls: 'section-title',
        });

        const nodeResults = contentEl.createEl('div', { cls: 'node-results' });

        for (const node of this.failedNodes) {
            this.renderFailedNodeItem(nodeResults, node);
        }
    }

    /**
     * Render a single failed node item
     */
    private renderFailedNodeItem(container: HTMLElement, node: FailedNode): void {
        const item = container.createEl('div', { cls: 'node-result-item' });

        // Node info
        const info = item.createEl('div', { cls: 'node-info' });
        info.createEl('span', {
            text: this.truncateText(node.nodeText, 30),
            cls: 'node-result-name',
        });
        info.createEl('span', {
            text: node.errorMessage,
            cls: 'node-result-status failed',
        });

        // Retry button
        const retryBtn = item.createEl('button', {
            text: '🔄 重试',
            cls: 'retry-button',
        });
        retryBtn.addEventListener('click', () => this.handleRetryNode(node, retryBtn));
    }

    /**
     * Handle retry for a failed node
     *
     * ✅ Verified from Story 13.8 Task 5 (RetryPolicy integration)
     */
    private async handleRetryNode(node: FailedNode, button: HTMLButtonElement): Promise<void> {
        // Disable button during retry
        button.disabled = true;
        button.textContent = '⏳ 重试中...';

        const retryPolicy = RetryPolicy.forNetworkRequests();

        try {
            if (this.callbacks.onRetryNode) {
                const success = await this.callbacks.onRetryNode(node.nodeId, node.recommendedAgent);
                if (success) {
                    new Notice(`节点 "${this.truncateText(node.nodeText, 20)}" 重试成功！`);
                    // Remove from failed list and re-render
                    this.failedNodes = this.failedNodes.filter(n => n.nodeId !== node.nodeId);
                    this.documentStats = this.calculateDocumentStats();
                    this.contentEl.empty();
                    this.renderContent();
                    return;
                }
            } else {
                // Default retry implementation with RetryPolicy
                const retryFetch = async (): Promise<void> => {
                    const response = await fetch(`${this.apiBaseUrl}/canvas/single-agent`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                        },
                        body: JSON.stringify({
                            canvas_path: this.canvasFile.path,
                            node_id: node.nodeId,
                            agent: node.recommendedAgent,
                        }),
                    });

                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new NetworkError(
                            errorData.message || `HTTP ${response.status}`,
                            response.status,
                            { endpoint: 'SINGLE_AGENT_API' }
                        );
                    }
                };

                await retryPolicy.executeWithRetry(retryFetch);

                new Notice(`节点 "${this.truncateText(node.nodeText, 20)}" 重试成功！`);
                // Remove from failed list and re-render
                this.failedNodes = this.failedNodes.filter(n => n.nodeId !== node.nodeId);
                this.documentStats = this.calculateDocumentStats();
                this.contentEl.empty();
                this.renderContent();
                return;
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            new Notice(`重试失败: ${message}`);
        }

        // Re-enable button
        button.disabled = false;
        button.textContent = '🔄 重试';
    }

    /**
     * Render modal footer
     */
    private renderFooter(): void {
        const { contentEl } = this;
        const footer = contentEl.createEl('div', { cls: 'modal-footer result-footer' });

        // View error log button (if there are errors)
        if (this.failedNodes.length > 0) {
            const logBtn = footer.createEl('button', {
                text: '📋 查看错误日志',
                cls: 'view-log-button',
            });
            logBtn.addEventListener('click', () => this.showErrorLog());
        }

        // Done button
        const doneBtn = contentEl.createEl('button', {
            text: '完成',
            cls: 'done-button mod-cta',
        });
        doneBtn.addEventListener('click', () => this.close());
    }

    /**
     * Show error log modal
     */
    private showErrorLog(): void {
        // Create a simple error log view
        const logContent = this.failedNodes.map(node => {
            return `节点: ${node.nodeText}\nAgent: ${node.recommendedAgent}\n错误: ${node.errorMessage}\n---`;
        }).join('\n\n');

        // Use Notice for simple display (could be enhanced with a proper modal)
        new Notice(`错误日志:\n\n${logContent}`, 10000);
    }

    /**
     * Format seconds to human-readable time
     */
    private formatTime(seconds: number): string {
        if (seconds < 60) {
            return `${Math.round(seconds)}秒`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            return secs > 0 ? `${minutes}分${secs}秒` : `${minutes}分钟`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.round((seconds % 3600) / 60);
            return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`;
        }
    }

    /**
     * Truncate text to specified length
     */
    private truncateText(text: string, maxLength: number): string {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength - 3) + '...';
    }
}
