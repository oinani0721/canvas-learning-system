/**
 * Group Preview Modal - Intelligent Parallel Processing
 *
 * Modal dialog for previewing intelligent grouping results before batch processing.
 * Displays node groups with recommended agents and estimated processing time.
 *
 * @module modals/GroupPreviewModal
 * @version 1.0.0
 * @story Story 13.8 Task 2
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 13.8 Dev Notes (GroupPreviewModal design)
 */

import { App, Modal, Notice, TFile } from 'obsidian';
import { RetryPolicy, NetworkError, TimeoutError, ErrorNotifier } from '../errors';

/**
 * Node data extracted from Canvas
 */
export interface CanvasNode {
    id: string;
    type: string;
    text?: string;
    color?: string;
    x: number;
    y: number;
    width: number;
    height: number;
}

/**
 * Group data from API response
 */
export interface NodeGroup {
    group_id: number;
    group_name: string;
    category: string;
    recommended_agent: string;
    priority: 'high' | 'medium' | 'low';
    nodes: CanvasNode[];
    estimated_time_seconds: number;
}

/**
 * API response for intelligent parallel grouping
 */
export interface GroupingResponse {
    success: boolean;
    session_id: string;
    canvas_path: string;
    groups: NodeGroup[];
    total_nodes: number;
    total_groups: number;
    total_estimated_time_seconds: number;
    message?: string;
}

/**
 * Callback for when user confirms processing
 */
export interface GroupPreviewCallbacks {
    onConfirm: (sessionId: string, groups: NodeGroup[]) => void;
    onCancel: () => void;
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
 * Priority badge colors
 */
const PRIORITY_COLORS: Record<string, string> = {
    'high': '#ef4444',
    'medium': '#f59e0b',
    'low': '#22c55e',
};

/**
 * Group Preview Modal
 *
 * Displays intelligent grouping preview with:
 * - Summary of detected nodes
 * - Group cards with agent recommendations
 * - Estimated processing time
 * - Confirm/Cancel actions
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class GroupPreviewModal extends Modal {
    private canvasFile: TFile;
    private nodes: CanvasNode[];
    private apiBaseUrl: string;
    private callbacks: GroupPreviewCallbacks;
    private isLoading: boolean = true;
    private groupingResponse: GroupingResponse | null = null;
    private error: string | null = null;

    /**
     * Creates a new GroupPreviewModal
     *
     * @param app - Obsidian App instance
     * @param canvasFile - The Canvas file being processed
     * @param nodes - Array of eligible nodes (red/purple)
     * @param apiBaseUrl - Base URL for API calls
     * @param callbacks - Callbacks for confirm/cancel actions
     */
    constructor(
        app: App,
        canvasFile: TFile,
        nodes: CanvasNode[],
        apiBaseUrl: string,
        callbacks: GroupPreviewCallbacks
    ) {
        super(app);
        this.canvasFile = canvasFile;
        this.nodes = nodes;
        this.apiBaseUrl = apiBaseUrl;
        this.callbacks = callbacks;
    }

    /**
     * Called when the modal is opened
     */
    async onOpen(): Promise<void> {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('intelligent-parallel-modal');
        contentEl.addClass('group-preview-modal');

        // Render loading state initially
        this.renderLoading();

        // Call API to get grouping
        await this.fetchGrouping();

        // Re-render with results
        contentEl.empty();
        if (this.error) {
            this.renderError();
        } else if (this.groupingResponse) {
            this.renderContent();
        }
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Fetch grouping from API with retry logic
     *
     * ✅ Verified from Story 13.7 (RetryPolicy integration)
     * - 3 retries with exponential backoff
     * - 30 second timeout per request
     * - Proper error categorization
     */
    private async fetchGrouping(): Promise<void> {
        const API_TIMEOUT = 30000; // 30 seconds as per Task 5 requirements
        const retryPolicy = RetryPolicy.forNetworkRequests();

        const fetchWithTimeout = async (): Promise<GroupingResponse> => {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

            try {
                const response = await fetch(`${this.apiBaseUrl}/canvas/intelligent-parallel`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                    },
                    body: JSON.stringify({
                        canvas_path: this.canvasFile.path,
                        nodes: this.nodes,
                        options: {
                            grouping_mode: 'intelligent',
                            max_groups: 6,
                            auto_execute: false,
                        },
                    }),
                    signal: controller.signal,
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new NetworkError(
                        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
                        response.status,
                        { endpoint: 'GROUPING_API' }
                    );
                }

                const data = await response.json();

                // Edge case: 分组结果为空 → 使用默认分组
                if (!data.groups || data.groups.length === 0) {
                    data.groups = this.createDefaultGroups();
                    data.total_groups = data.groups.length;
                    new Notice('⚠️ 智能分组返回空结果，已使用默认分组');
                }

                return data;
            } catch (err) {
                clearTimeout(timeoutId);

                if (err instanceof Error && err.name === 'AbortError') {
                    throw new TimeoutError('API请求超时（30秒）', 'GROUPING_API', API_TIMEOUT);
                }
                throw err;
            }
        };

        try {
            this.groupingResponse = await retryPolicy.executeWithRetry(fetchWithTimeout);
            this.isLoading = false;
        } catch (err) {
            if (err instanceof TimeoutError) {
                this.error = '请求超时，请检查网络连接后重试';
            } else if (err instanceof NetworkError) {
                this.error = err.message || '网络请求失败，请稍后重试';
            } else {
                this.error = err instanceof Error ? err.message : '未知错误';
            }
            this.isLoading = false;
        }
    }

    /**
     * Create default groups when API returns empty result
     * Edge case handling per Task 5 requirements
     */
    private createDefaultGroups(): NodeGroup[] {
        // Group all nodes into a single default group
        return [{
            group_id: 1,
            group_name: '默认分组',
            category: 'mixed',
            recommended_agent: 'basic-decomposition',
            priority: 'medium' as const,
            nodes: this.nodes,
            estimated_time_seconds: this.nodes.length * 30, // 30s per node estimate
        }];
    }

    /**
     * Render loading state
     */
    private renderLoading(): void {
        const { contentEl } = this;

        // Header
        const header = contentEl.createEl('div', { cls: 'modal-header' });
        header.createEl('h2', {
            text: '⚡ 智能并行处理 - 分组预览',
            cls: 'modal-title',
        });

        // Loading spinner
        const loadingContainer = contentEl.createEl('div', { cls: 'loading-container' });
        loadingContainer.createEl('div', { cls: 'loading-spinner' });
        loadingContainer.createEl('p', {
            text: '正在分析节点并生成智能分组...',
            cls: 'loading-text',
        });
    }

    /**
     * Render error state
     */
    private renderError(): void {
        const { contentEl } = this;

        // Header
        const header = contentEl.createEl('div', { cls: 'modal-header' });
        header.createEl('h2', {
            text: '⚡ 智能并行处理 - 分组预览',
            cls: 'modal-title',
        });

        // Error message
        const errorContainer = contentEl.createEl('div', { cls: 'error-container' });
        errorContainer.createEl('div', {
            text: '❌ 分组分析失败',
            cls: 'error-title',
        });
        errorContainer.createEl('p', {
            text: this.error || 'Unknown error',
            cls: 'error-message',
        });

        // Retry button
        const retryBtn = errorContainer.createEl('button', {
            text: '🔄 重试',
            cls: 'retry-button',
        });
        retryBtn.addEventListener('click', async () => {
            this.error = null;
            this.isLoading = true;
            contentEl.empty();
            this.renderLoading();
            await this.fetchGrouping();
            contentEl.empty();
            if (this.error) {
                this.renderError();
            } else if (this.groupingResponse) {
                this.renderContent();
            }
        });

        // Close button
        const closeBtn = errorContainer.createEl('button', {
            text: '关闭',
            cls: 'close-button',
        });
        closeBtn.addEventListener('click', () => {
            this.close();
            this.callbacks.onCancel();
        });
    }

    /**
     * Render main content
     */
    private renderContent(): void {
        const { contentEl } = this;
        const response = this.groupingResponse!;

        // Header
        const header = contentEl.createEl('div', { cls: 'modal-header' });
        header.createEl('h2', {
            text: '⚡ 智能并行处理 - 分组预览',
            cls: 'modal-title',
        });

        // Node summary
        const summary = contentEl.createEl('div', { cls: 'node-summary' });
        summary.createEl('p', {
            text: `检测到 ${response.total_nodes} 个待处理节点，智能分组为 ${response.total_groups} 组`,
            cls: 'summary-text',
        });

        // Group list container
        const groupList = contentEl.createEl('div', { cls: 'group-list' });

        // Render each group card
        for (const group of response.groups) {
            this.renderGroupCard(groupList, group);
        }

        // Footer
        const footer = contentEl.createEl('div', { cls: 'modal-footer' });

        // Estimated time
        const estimatedTime = this.formatTime(response.total_estimated_time_seconds);
        footer.createEl('span', {
            text: `⏱️ 预计处理时间: ${estimatedTime}`,
            cls: 'estimated-time',
        });

        // Button container
        const buttonContainer = footer.createEl('div', { cls: 'button-container' });

        // Cancel button
        const cancelBtn = buttonContainer.createEl('button', {
            text: '取消',
            cls: 'cancel-button',
        });
        cancelBtn.addEventListener('click', () => {
            this.close();
            this.callbacks.onCancel();
        });

        // Confirm button
        const confirmBtn = buttonContainer.createEl('button', {
            text: '🚀 开始处理',
            cls: 'confirm-button mod-cta',
        });
        confirmBtn.addEventListener('click', () => {
            this.close();
            this.callbacks.onConfirm(response.session_id, response.groups);
        });
    }

    /**
     * Render a single group card
     */
    private renderGroupCard(container: HTMLElement, group: NodeGroup): void {
        const card = container.createEl('div', { cls: 'group-card' });

        // Card header
        const cardHeader = card.createEl('div', { cls: 'group-card-header' });

        // Group name with agent emoji
        const agentEmoji = AGENT_EMOJI[group.recommended_agent] || AGENT_EMOJI['default'];
        cardHeader.createEl('span', {
            text: `${agentEmoji} Group ${group.group_id}: ${group.group_name}`,
            cls: 'group-name',
        });

        // Priority badge
        const priorityBadge = cardHeader.createEl('span', {
            text: group.priority.toUpperCase(),
            cls: `priority-badge priority-${group.priority}`,
        });
        priorityBadge.style.backgroundColor = PRIORITY_COLORS[group.priority] || PRIORITY_COLORS['medium'];

        // Agent info
        const agentInfo = card.createEl('div', { cls: 'agent-info' });
        agentInfo.createEl('span', {
            text: `推荐Agent: `,
            cls: 'agent-label',
        });
        agentInfo.createEl('code', {
            text: group.recommended_agent,
            cls: 'agent-name',
        });

        // Node list
        const nodeList = card.createEl('div', { cls: 'node-list' });
        const nodeCount = group.nodes.length;
        const displayNodes = group.nodes.slice(0, 3); // Show max 3 nodes

        for (const node of displayNodes) {
            const nodeText = this.truncateText(node.text || node.id, 40);
            nodeList.createEl('div', {
                text: `• ${nodeText}`,
                cls: 'node-item',
            });
        }

        if (nodeCount > 3) {
            nodeList.createEl('div', {
                text: `... 还有 ${nodeCount - 3} 个节点`,
                cls: 'node-more',
            });
        }

        // Estimated time for this group
        const timeInfo = card.createEl('div', { cls: 'group-time' });
        timeInfo.createEl('span', {
            text: `⏱️ 预计: ${this.formatTime(group.estimated_time_seconds)}`,
            cls: 'time-text',
        });
    }

    /**
     * Format seconds to human-readable time
     */
    private formatTime(seconds: number): string {
        if (seconds < 60) {
            return `${Math.round(seconds)}秒`;
        } else if (seconds < 3600) {
            const minutes = Math.round(seconds / 60);
            return `${minutes}分钟`;
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
