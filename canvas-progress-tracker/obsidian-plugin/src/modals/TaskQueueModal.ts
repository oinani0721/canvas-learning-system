/**
 * Task Queue Modal - Agent Request Management
 *
 * Modal dialog for displaying and managing pending Agent requests.
 * Shows real-time status of all queued/running requests with cancel functionality.
 *
 * @module modals/TaskQueueModal
 * @version 1.0.0
 * @story Story 12.H.3 - 任务管理可视化面板
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal API)
 * ✅ Verified from Story 12.H.3 Dev Notes (TaskQueueModal design)
 */

import { App, Modal, Notice } from 'obsidian';

/**
 * Pending request information
 *
 * Tracks full details of an Agent request for UI display.
 * Extends beyond the simple boolean used in deduplication.
 *
 * @source Story 12.H.3 - PendingRequest interface definition
 */
export interface PendingRequest {
    /** Lock key (format: `${agentType}-${nodeId}`) */
    lockKey: string;
    /** Node ID being processed */
    nodeId: string;
    /** Node display name (for UI) */
    nodeName: string;
    /** Agent type identifier */
    agentType: string;
    /** Agent display name in Chinese */
    agentDisplayName: string;
    /** Request status */
    status: 'queued' | 'running';
    /** Request start time (Unix timestamp) */
    startTime: number;
    /** Estimated processing time in seconds */
    estimatedTime: number;
    /** AbortController for cancellation (optional - may not be available for all requests) */
    abortController?: AbortController;
}

/**
 * Agent estimated times (in seconds)
 *
 * Maps agent types to their estimated processing times.
 *
 * @source Story 12.F.6 - Timeout optimization
 */
export const AGENT_ESTIMATED_TIMES: Record<string, number> = {
    'basic-decomp': 20,
    'deep-decomp': 40,
    'oral': 25,
    'four-level': 45,
    'clarification': 30,
    'example': 35,
    'memory': 20,
    'comparison': 30,
    'question': 25,
    'verify': 30,
    'scoring': 15,
};

/**
 * Callback type for cancel action
 */
export type CancelTaskCallback = (lockKey: string) => void;

/**
 * Task Queue Modal
 *
 * Displays a list of all pending Agent requests with:
 * - Request status indicator (queued/running)
 * - Agent type and node information
 * - Progress indicator with elapsed/estimated time
 * - Cancel button for each request
 * - Auto-refresh every 500ms
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal class)
 */
export class TaskQueueModal extends Modal {
    /** Reference to tasks map (from main plugin) */
    private tasks: Map<string, PendingRequest>;
    /** Callback function when user cancels a task */
    private onCancelTask: CancelTaskCallback;
    /** Auto-refresh interval ID */
    private refreshInterval: number | null = null;
    /** Refresh interval in milliseconds */
    private readonly REFRESH_INTERVAL_MS = 500;

    /**
     * Creates a new TaskQueueModal
     *
     * @param app - Obsidian App instance
     * @param tasks - Reference to the pending tasks map
     * @param onCancelTask - Callback when user clicks cancel on a task
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal constructor)
     */
    constructor(
        app: App,
        tasks: Map<string, PendingRequest>,
        onCancelTask: CancelTaskCallback
    ) {
        super(app);
        this.tasks = tasks;
        this.onCancelTask = onCancelTask;
    }

    /**
     * Called when the modal is opened
     *
     * Renders initial content and starts auto-refresh polling.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal.onOpen)
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.addClass('task-queue-modal');

        this.renderHeader();
        this.renderTaskList();
        this.startPolling();
    }

    /**
     * Called when the modal is closed
     *
     * Stops polling and cleans up UI elements.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal.onClose)
     */
    onClose(): void {
        this.stopPolling();
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Render modal header with title and summary
     */
    private renderHeader(): void {
        const { contentEl } = this;

        // Clear existing header if any
        const oldHeader = contentEl.querySelector('.task-queue-header');
        if (oldHeader) oldHeader.remove();

        const header = contentEl.createEl('div', { cls: 'task-queue-header' });
        header.createEl('h2', { text: 'Agent 任务队列' });

        const taskCount = this.tasks.size;
        const runningCount = Array.from(this.tasks.values())
            .filter(t => t.status === 'running').length;
        const queuedCount = taskCount - runningCount;

        const summaryText = taskCount === 0
            ? '暂无任务'
            : `共 ${taskCount} 个任务 (${runningCount} 运行中, ${queuedCount} 排队中)`;

        header.createEl('p', {
            text: summaryText,
            cls: 'task-queue-summary'
        });
    }

    /**
     * Render task list container and items
     */
    private renderTaskList(): void {
        const { contentEl } = this;

        // Clear existing task list
        const oldList = contentEl.querySelector('.task-queue-list');
        if (oldList) oldList.remove();

        const listContainer = contentEl.createEl('div', { cls: 'task-queue-list' });

        if (this.tasks.size === 0) {
            listContainer.createEl('p', {
                text: '暂无进行中的任务',
                cls: 'task-queue-empty'
            });
            return;
        }

        // Sort tasks: running first, then by start time
        const sortedTasks = Array.from(this.tasks.entries()).sort((a, b) => {
            // Running tasks first
            if (a[1].status === 'running' && b[1].status !== 'running') return -1;
            if (a[1].status !== 'running' && b[1].status === 'running') return 1;
            // Then by start time (oldest first)
            return a[1].startTime - b[1].startTime;
        });

        for (const [lockKey, task] of sortedTasks) {
            this.renderTaskItem(listContainer, task, lockKey);
        }
    }

    /**
     * Render individual task item
     *
     * @param container - Parent container element
     * @param task - Task information
     * @param lockKey - Unique task identifier
     */
    private renderTaskItem(
        container: HTMLElement,
        task: PendingRequest,
        lockKey: string
    ): void {
        const item = container.createEl('div', { cls: 'task-queue-item' });

        // Status indicator dot
        const statusDot = item.createEl('span', {
            cls: `task-status-dot ${task.status}`
        });

        // Task info section
        const info = item.createEl('div', { cls: 'task-info' });
        info.createEl('div', {
            text: task.agentDisplayName,
            cls: 'task-agent-name'
        });
        info.createEl('div', {
            text: `节点: ${task.nodeName || task.nodeId.substring(0, 8) + '...'}`,
            cls: 'task-node-name'
        });

        // Progress/time section
        const progress = item.createEl('div', { cls: 'task-progress' });
        const elapsed = Math.floor((Date.now() - task.startTime) / 1000);

        if (task.status === 'running') {
            // Show elapsed time and progress bar
            progress.createEl('div', {
                text: `已用 ${elapsed}s / 预计 ${task.estimatedTime}s`,
                cls: 'task-time'
            });

            // Progress bar
            const progressBar = progress.createEl('div', { cls: 'task-progress-bar' });
            const progressFill = progressBar.createEl('div', { cls: 'task-progress-fill' });
            const percent = Math.min(100, (elapsed / task.estimatedTime) * 100);
            progressFill.style.width = `${percent}%`;

            // Add warning class if over estimated time
            if (elapsed > task.estimatedTime) {
                progressFill.addClass('overtime');
            }
        } else {
            // Show queued status
            progress.createEl('div', {
                text: '排队中...',
                cls: 'task-time queued'
            });
        }

        // Cancel button
        const cancelBtn = item.createEl('button', {
            text: '取消',
            cls: 'task-cancel-btn'
        });
        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleCancelClick(lockKey, task);
        });
    }

    /**
     * Handle cancel button click
     *
     * @param lockKey - Task identifier
     * @param task - Task information
     */
    private handleCancelClick(lockKey: string, task: PendingRequest): void {
        // Call cancel callback
        this.onCancelTask(lockKey);

        // Show notice
        new Notice(`已取消: ${task.agentDisplayName}`);

        // Refresh the list immediately
        this.renderHeader();
        this.renderTaskList();
    }

    /**
     * Start auto-refresh polling
     *
     * Refreshes the modal content every 500ms to show real-time updates.
     *
     * @source Story 12.H.3 - AC: 每 500ms 自动刷新状态
     */
    private startPolling(): void {
        this.refreshInterval = window.setInterval(() => {
            this.renderHeader();
            this.renderTaskList();
        }, this.REFRESH_INTERVAL_MS);
    }

    /**
     * Stop auto-refresh polling
     */
    private stopPolling(): void {
        if (this.refreshInterval !== null) {
            window.clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}
