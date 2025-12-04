/**
 * Progress Monitor Modal - Intelligent Parallel Processing
 *
 * Modal dialog for monitoring real-time progress of batch processing.
 * Uses WebSocket for live updates with polling fallback.
 *
 * @module modals/ProgressMonitorModal
 * @version 1.0.0
 * @story Story 13.8 Task 3
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 13.8 Dev Notes (ProgressMonitorModal design)
 */

import { App, Modal, Notice, TFile } from 'obsidian';
import { NodeGroup } from './GroupPreviewModal';

/**
 * Group processing status
 */
export type GroupStatus = 'pending' | 'running' | 'completed' | 'failed';

/**
 * Individual node result
 */
export interface NodeResult {
    node_id: string;
    node_text: string;
    status: 'success' | 'failed';
    output?: string;
    error?: string;
    processing_time_seconds?: number;
}

/**
 * Group processing state
 */
export interface GroupState {
    group_id: number;
    group_name: string;
    status: GroupStatus;
    progress: number; // 0-100
    nodes_completed: number;
    nodes_total: number;
    current_node?: string;
    results: NodeResult[];
}

/**
 * WebSocket message types
 */
export interface WSMessage {
    type: 'progress_update' | 'task_completed' | 'task_failed' | 'session_completed' | 'error';
    data: any;
}

/**
 * Session status from polling API
 */
export interface SessionStatus {
    session_id: string;
    status: 'running' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    groups: GroupState[];
    start_time: string;
    elapsed_seconds: number;
    message?: string;
}

/**
 * Callbacks for progress monitor events
 */
export interface ProgressMonitorCallbacks {
    onComplete: (results: SessionStatus) => void;
    onCancel: () => void;
}

/**
 * Progress Monitor Modal
 *
 * Displays real-time processing progress with:
 * - Overall progress bar
 * - Group status cards
 * - WebSocket updates with polling fallback
 * - Pause/Cancel/Minimize controls
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class ProgressMonitorModal extends Modal {
    private canvasFile: TFile;
    private sessionId: string;
    private groups: NodeGroup[];
    private apiBaseUrl: string;
    private wsBaseUrl: string;
    private callbacks: ProgressMonitorCallbacks;

    // State
    private groupStates: Map<number, GroupState> = new Map();
    private overallProgress: number = 0;
    private startTime: Date;
    private isCompleted: boolean = false;
    private isCancelled: boolean = false;

    // WebSocket
    private ws: WebSocket | null = null;
    private wsReconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 3;

    // Polling fallback
    private pollingInterval: number | null = null;
    private pollingIntervalMs: number = 5000;
    private usePolling: boolean = false;

    // UI elements
    private progressBarFill: HTMLElement | null = null;
    private progressText: HTMLElement | null = null;
    private groupListContainer: HTMLElement | null = null;
    private elapsedTimeEl: HTMLElement | null = null;

    // Timer
    private elapsedTimer: number | null = null;

    /**
     * Creates a new ProgressMonitorModal
     *
     * @param app - Obsidian App instance
     * @param canvasFile - The Canvas file being processed
     * @param sessionId - Processing session ID
     * @param groups - Array of groups to process
     * @param apiBaseUrl - Base URL for REST API
     * @param wsBaseUrl - Base URL for WebSocket
     * @param callbacks - Callbacks for complete/cancel events
     */
    constructor(
        app: App,
        canvasFile: TFile,
        sessionId: string,
        groups: NodeGroup[],
        apiBaseUrl: string,
        wsBaseUrl: string,
        callbacks: ProgressMonitorCallbacks
    ) {
        super(app);
        this.canvasFile = canvasFile;
        this.sessionId = sessionId;
        this.groups = groups;
        this.apiBaseUrl = apiBaseUrl;
        this.wsBaseUrl = wsBaseUrl;
        this.callbacks = callbacks;
        this.startTime = new Date();

        // Initialize group states
        for (const group of groups) {
            this.groupStates.set(group.group_id, {
                group_id: group.group_id,
                group_name: group.group_name,
                status: 'pending',
                progress: 0,
                nodes_completed: 0,
                nodes_total: group.nodes.length,
                results: [],
            });
        }
    }

    /**
     * Called when the modal is opened
     */
    async onOpen(): Promise<void> {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('intelligent-parallel-modal');
        contentEl.addClass('progress-monitor-modal');

        this.renderContent();
        this.startElapsedTimer();
        this.connectWebSocket();
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        this.cleanup();
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Cleanup resources
     */
    private cleanup(): void {
        // Stop elapsed timer
        if (this.elapsedTimer) {
            window.clearInterval(this.elapsedTimer);
            this.elapsedTimer = null;
        }

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // Stop polling
        if (this.pollingInterval) {
            window.clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Render main content
     */
    private renderContent(): void {
        const { contentEl } = this;

        // Header
        const header = contentEl.createEl('div', { cls: 'progress-header' });
        header.createEl('h2', {
            text: '⚡ 智能并行处理 - 执行中',
            cls: 'modal-title',
        });

        // Elapsed time
        this.elapsedTimeEl = header.createEl('span', {
            text: '⏱️ 00:00',
            cls: 'elapsed-time',
        });

        // Overall progress section
        const progressSection = contentEl.createEl('div', { cls: 'overall-progress' });
        progressSection.createEl('p', {
            text: `处理 ${this.groups.length} 个分组中...`,
            cls: 'progress-label',
        });

        const progressBarContainer = progressSection.createEl('div', { cls: 'progress-bar-container' });
        this.progressBarFill = progressBarContainer.createEl('div', { cls: 'progress-bar-fill' });
        this.progressBarFill.style.width = '0%';

        this.progressText = progressSection.createEl('p', {
            text: '0% 完成',
            cls: 'progress-text',
        });

        // Group status list
        this.groupListContainer = contentEl.createEl('div', { cls: 'group-status-list' });
        this.renderGroupStatusCards();

        // Control buttons
        const controlSection = contentEl.createEl('div', { cls: 'control-buttons' });

        // Cancel button
        const cancelBtn = controlSection.createEl('button', {
            text: '❌ 取消',
            cls: 'control-button danger',
        });
        cancelBtn.addEventListener('click', () => this.handleCancel());

        // Minimize button (placeholder - minimizes to Notice)
        const minimizeBtn = controlSection.createEl('button', {
            text: '📤 最小化',
            cls: 'control-button',
        });
        minimizeBtn.addEventListener('click', () => this.handleMinimize());
    }

    /**
     * Render group status cards
     */
    private renderGroupStatusCards(): void {
        if (!this.groupListContainer) return;
        this.groupListContainer.empty();

        for (const [groupId, state] of this.groupStates) {
            const card = this.groupListContainer.createEl('div', { cls: 'group-status-card' });

            // Group name
            const nameEl = card.createEl('span', {
                text: `Group ${groupId}: ${state.group_name}`,
                cls: 'group-status-name',
            });

            // Status badge
            const badge = card.createEl('span', {
                cls: `group-status-badge status-${state.status}`,
            });
            badge.textContent = this.getStatusText(state.status);

            // Store reference for updates
            card.dataset.groupId = String(groupId);
        }
    }

    /**
     * Get human-readable status text
     */
    private getStatusText(status: GroupStatus): string {
        switch (status) {
            case 'pending':
                return '⏳ 等待中';
            case 'running':
                return '🔄 处理中';
            case 'completed':
                return '✅ 完成';
            case 'failed':
                return '❌ 失败';
            default:
                return status;
        }
    }

    /**
     * Start elapsed time timer
     */
    private startElapsedTimer(): void {
        this.elapsedTimer = window.setInterval(() => {
            this.updateElapsedTime();
        }, 1000);
    }

    /**
     * Update elapsed time display
     */
    private updateElapsedTime(): void {
        if (!this.elapsedTimeEl) return;

        const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        this.elapsedTimeEl.textContent = `⏱️ ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    /**
     * Connect to WebSocket
     */
    private connectWebSocket(): void {
        try {
            const wsUrl = `${this.wsBaseUrl}/ws/intelligent-parallel/${this.sessionId}`;
            console.log(`Canvas Review System: Connecting to WebSocket: ${wsUrl}`);

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('Canvas Review System: WebSocket connected');
                this.wsReconnectAttempts = 0;
                this.usePolling = false;

                // Stop polling if it was running
                if (this.pollingInterval) {
                    window.clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const message: WSMessage = JSON.parse(event.data);
                    this.handleWSMessage(message);
                } catch (err) {
                    console.error('Canvas Review System: Failed to parse WebSocket message:', err);
                }
            };

            this.ws.onerror = (error) => {
                console.error('Canvas Review System: WebSocket error:', error);
                this.handleWSError();
            };

            this.ws.onclose = () => {
                console.log('Canvas Review System: WebSocket closed');
                if (!this.isCompleted && !this.isCancelled) {
                    this.handleWSClose();
                }
            };
        } catch (err) {
            console.error('Canvas Review System: Failed to create WebSocket:', err);
            this.startPolling();
        }
    }

    /**
     * Handle WebSocket message
     */
    private handleWSMessage(message: WSMessage): void {
        switch (message.type) {
            case 'progress_update':
                this.handleProgressUpdate(message.data);
                break;
            case 'task_completed':
                this.handleTaskCompleted(message.data);
                break;
            case 'task_failed':
                this.handleTaskFailed(message.data);
                break;
            case 'session_completed':
                this.handleSessionCompleted(message.data);
                break;
            case 'error':
                this.handleSessionError(message.data);
                break;
        }
    }

    /**
     * Handle progress update message
     */
    private handleProgressUpdate(data: any): void {
        const groupId = data.group_id;
        const state = this.groupStates.get(groupId);

        if (state) {
            state.status = 'running';
            state.progress = data.progress || 0;
            state.nodes_completed = data.nodes_completed || 0;
            state.current_node = data.current_node;

            this.groupStates.set(groupId, state);
            this.updateUI();
        }
    }

    /**
     * Handle task completed message
     */
    private handleTaskCompleted(data: any): void {
        const groupId = data.group_id;
        const state = this.groupStates.get(groupId);

        if (state) {
            state.nodes_completed = (state.nodes_completed || 0) + 1;
            state.results.push({
                node_id: data.node_id,
                node_text: data.node_text || '',
                status: 'success',
                output: data.output,
                processing_time_seconds: data.processing_time_seconds,
            });

            // Check if group is complete
            if (state.nodes_completed >= state.nodes_total) {
                state.status = 'completed';
                state.progress = 100;
            }

            this.groupStates.set(groupId, state);
            this.updateUI();
        }
    }

    /**
     * Handle task failed message
     */
    private handleTaskFailed(data: any): void {
        const groupId = data.group_id;
        const state = this.groupStates.get(groupId);

        if (state) {
            state.results.push({
                node_id: data.node_id,
                node_text: data.node_text || '',
                status: 'failed',
                error: data.error,
            });

            // Mark as failed if all nodes processed
            state.nodes_completed = (state.nodes_completed || 0) + 1;
            if (state.nodes_completed >= state.nodes_total) {
                // Check if any succeeded
                const hasSuccess = state.results.some((r) => r.status === 'success');
                state.status = hasSuccess ? 'completed' : 'failed';
                state.progress = 100;
            }

            this.groupStates.set(groupId, state);
            this.updateUI();
        }
    }

    /**
     * Handle session completed message
     */
    private handleSessionCompleted(data: any): void {
        this.isCompleted = true;
        this.overallProgress = 100;

        // Update all remaining groups to completed
        for (const [groupId, state] of this.groupStates) {
            if (state.status === 'pending' || state.status === 'running') {
                state.status = 'completed';
                state.progress = 100;
                this.groupStates.set(groupId, state);
            }
        }

        this.updateUI();
        this.showCompletionNotice();

        // Close modal and trigger callback
        setTimeout(() => {
            this.close();
            this.callbacks.onComplete(data);
        }, 1000);
    }

    /**
     * Handle session error
     */
    private handleSessionError(data: any): void {
        console.error('Canvas Review System: Session error:', data);
        new Notice(`处理错误: ${data.message || '未知错误'}`, 5000);
    }

    /**
     * Handle WebSocket error
     */
    private handleWSError(): void {
        if (!this.isCompleted && !this.isCancelled) {
            this.attemptReconnect();
        }
    }

    /**
     * Handle WebSocket close
     */
    private handleWSClose(): void {
        if (!this.isCompleted && !this.isCancelled) {
            this.attemptReconnect();
        }
    }

    /**
     * Attempt WebSocket reconnection
     */
    private attemptReconnect(): void {
        this.wsReconnectAttempts++;

        if (this.wsReconnectAttempts <= this.maxReconnectAttempts) {
            console.log(`Canvas Review System: Reconnecting WebSocket (attempt ${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
                this.connectWebSocket();
            }, 1000 * this.wsReconnectAttempts); // Exponential backoff
        } else {
            console.log('Canvas Review System: Max reconnection attempts reached, switching to polling');
            this.startPolling();
        }
    }

    /**
     * Start polling fallback
     *
     * ✅ Verified from Story 13.8 Task 5 (Edge case: WebSocket断开 → 切换到轮询)
     */
    private startPolling(): void {
        if (this.pollingInterval) return;

        this.usePolling = true;
        console.log('Canvas Review System: Starting polling mode');

        // Notify user about mode degradation
        new Notice('⚠️ WebSocket连接失败，已切换到轮询模式', 5000);

        this.pollingInterval = window.setInterval(async () => {
            await this.pollStatus();
        }, this.pollingIntervalMs);

        // Immediately poll once
        this.pollStatus();
    }

    /**
     * Poll status from API
     */
    private async pollStatus(): Promise<void> {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/canvas/intelligent-parallel/status/${this.sessionId}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                    },
                }
            );

            if (!response.ok) {
                console.error('Canvas Review System: Polling failed:', response.status);
                return;
            }

            const data: SessionStatus = await response.json();
            this.updateFromPollingData(data);

            if (data.status === 'completed' || data.status === 'failed') {
                if (this.pollingInterval) {
                    window.clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                }

                this.isCompleted = true;
                this.showCompletionNotice();

                setTimeout(() => {
                    this.close();
                    this.callbacks.onComplete(data);
                }, 1000);
            }
        } catch (err) {
            console.error('Canvas Review System: Polling error:', err);
        }
    }

    /**
     * Update state from polling data
     */
    private updateFromPollingData(data: SessionStatus): void {
        this.overallProgress = data.progress;

        for (const groupData of data.groups) {
            const state = this.groupStates.get(groupData.group_id);
            if (state) {
                state.status = groupData.status;
                state.progress = groupData.progress;
                state.nodes_completed = groupData.nodes_completed;
                state.nodes_total = groupData.nodes_total;
                state.results = groupData.results || [];
                this.groupStates.set(groupData.group_id, state);
            }
        }

        this.updateUI();
    }

    /**
     * Update UI elements
     */
    private updateUI(): void {
        // Calculate overall progress
        let totalNodes = 0;
        let completedNodes = 0;

        for (const state of this.groupStates.values()) {
            totalNodes += state.nodes_total;
            completedNodes += state.nodes_completed;
        }

        this.overallProgress = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

        // Update progress bar
        if (this.progressBarFill) {
            this.progressBarFill.style.width = `${this.overallProgress}%`;
        }

        // Update progress text
        if (this.progressText) {
            this.progressText.textContent = `${this.overallProgress}% 完成 (${completedNodes}/${totalNodes} 节点)`;
        }

        // Update group status cards
        if (this.groupListContainer) {
            const cards = this.groupListContainer.querySelectorAll('.group-status-card');
            cards.forEach((card) => {
                const groupId = Number((card as HTMLElement).dataset.groupId);
                const state = this.groupStates.get(groupId);

                if (state) {
                    const badge = card.querySelector('.group-status-badge');
                    if (badge) {
                        badge.className = `group-status-badge status-${state.status}`;
                        badge.textContent = this.getStatusText(state.status);
                    }
                }
            });
        }
    }

    /**
     * Show completion notice
     */
    private showCompletionNotice(): void {
        let successCount = 0;
        let failedCount = 0;

        for (const state of this.groupStates.values()) {
            for (const result of state.results) {
                if (result.status === 'success') {
                    successCount++;
                } else {
                    failedCount++;
                }
            }
        }

        const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timeStr = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;

        if (failedCount > 0) {
            new Notice(`✅ 处理完成: ${successCount}个成功, ${failedCount}个失败 (耗时${timeStr})`, 5000);
        } else {
            new Notice(`✅ 全部处理完成: ${successCount}个节点 (耗时${timeStr})`, 5000);
        }
    }

    /**
     * Handle cancel button click
     */
    private async handleCancel(): Promise<void> {
        this.isCancelled = true;

        try {
            // Call cancel API
            await fetch(`${this.apiBaseUrl}/canvas/intelligent-parallel/cancel/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                },
            });
        } catch (err) {
            console.error('Canvas Review System: Failed to cancel session:', err);
        }

        new Notice('处理已取消', 3000);
        this.close();
        this.callbacks.onCancel();
    }

    /**
     * Handle minimize button click
     */
    private handleMinimize(): void {
        // Show a persistent notice indicating background processing
        new Notice(`⚡ 智能并行处理在后台运行中 (${this.overallProgress}% 完成)`, 0);

        // Store reference for reopening
        // Note: In a real implementation, we'd store this in plugin state

        this.close();

        // Continue polling in background if using polling mode
        if (this.usePolling && !this.pollingInterval) {
            this.startPolling();
        }
    }

    /**
     * Get current results
     */
    public getResults(): Map<number, GroupState> {
        return new Map(this.groupStates);
    }
}
