/**
 * Rollback Modal - Canvas Snapshot and Rollback Management
 *
 * Modal dialog for viewing Canvas snapshots and executing rollback operations.
 * Supports operation-level, snapshot-level, and timepoint-based rollbacks.
 *
 * @module modals/RollbackModal
 * @version 1.0.0
 * @story Story 20.4 - Rollback System UI Integration
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from types.ts (Snapshot, SnapshotListResponse, RollbackRequest)
 */

import { App, Modal, Notice, Setting } from 'obsidian';
import type {
    Snapshot,
    SnapshotListResponse,
    SnapshotType,
    RollbackRequest,
    RollbackResult,
    RollbackType,
} from '../api/types';
import type { ApiClient } from '../api/ApiClient';

/**
 * Snapshot type display configuration
 */
const SNAPSHOT_TYPE_CONFIG: Record<SnapshotType, { emoji: string; label: string }> = {
    auto: { emoji: '🤖', label: '自动' },
    manual: { emoji: '📸', label: '手动' },
    checkpoint: { emoji: '🏁', label: '检查点' },
};

/**
 * Rollback Modal
 *
 * Displays Canvas snapshots with:
 * - Snapshot list with type indicators
 * - Snapshot details (metadata, timestamp)
 * - Rollback execution with confirmation
 * - Backup creation option
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class RollbackModal extends Modal {
    private apiClient: ApiClient;
    private canvasPath: string;
    private snapshots: Snapshot[];
    private selectedSnapshot: Snapshot | null = null;

    /**
     * Creates a new RollbackModal
     *
     * @param app - Obsidian App instance
     * @param apiClient - API client for backend calls
     * @param canvasPath - Path to the Canvas file
     * @param snapshotResponse - Initial snapshot list response
     */
    constructor(
        app: App,
        apiClient: ApiClient,
        canvasPath: string,
        snapshotResponse: SnapshotListResponse
    ) {
        super(app);
        this.apiClient = apiClient;
        this.canvasPath = canvasPath;
        this.snapshots = snapshotResponse.snapshots;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('rollback-modal');

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
        const header = contentEl.createEl('div', { cls: 'rollback-header' });
        header.createEl('h2', { text: '📜 Canvas快照历史' });

        // Canvas info
        const infoSection = contentEl.createEl('div', { cls: 'rollback-info' });
        infoSection.createEl('p', {
            text: `Canvas: ${this.getCanvasName()}`,
            cls: 'rollback-canvas-path',
        });
        infoSection.createEl('p', {
            text: `共 ${this.snapshots.length} 个快照`,
            cls: 'rollback-count',
        });

        // Action buttons
        this.renderActionBar();

        // Snapshots list
        this.renderSnapshotsList();

        // Footer
        this.renderFooter();
    }

    /**
     * Render action bar
     */
    private renderActionBar(): void {
        const { contentEl } = this;
        const actionBar = contentEl.createEl('div', { cls: 'rollback-action-bar' });

        // Create snapshot button
        const createBtn = actionBar.createEl('button', {
            text: '📸 创建快照',
            cls: 'rollback-create-btn',
        });
        createBtn.addEventListener('click', () => this.handleCreateSnapshot());

        // Refresh button
        const refreshBtn = actionBar.createEl('button', {
            text: '🔄 刷新',
            cls: 'rollback-refresh-btn',
        });
        refreshBtn.addEventListener('click', () => this.handleRefresh());
    }

    /**
     * Render snapshots list
     */
    private renderSnapshotsList(): void {
        const { contentEl } = this;

        if (this.snapshots.length === 0) {
            const emptyState = contentEl.createEl('div', { cls: 'rollback-empty-state' });
            emptyState.createEl('p', { text: '暂无快照记录' });
            emptyState.createEl('p', {
                text: '点击"创建快照"保存当前Canvas状态',
                cls: 'rollback-empty-hint',
            });
            return;
        }

        const listSection = contentEl.createEl('div', { cls: 'rollback-list-section' });
        listSection.createEl('h3', { text: '快照列表', cls: 'section-title' });

        const snapshotsList = listSection.createEl('div', { cls: 'snapshots-list' });

        for (const snapshot of this.snapshots) {
            this.renderSnapshotItem(snapshotsList, snapshot);
        }
    }

    /**
     * Render a single snapshot item
     */
    private renderSnapshotItem(container: HTMLElement, snapshot: Snapshot): void {
        const snapshotItem = container.createEl('div', {
            cls: `snapshot-item ${this.selectedSnapshot?.id === snapshot.id ? 'selected' : ''}`,
        });

        // Type indicator
        const typeConfig = SNAPSHOT_TYPE_CONFIG[snapshot.type];
        const typeIndicator = snapshotItem.createEl('div', { cls: 'snapshot-type' });
        typeIndicator.createEl('span', { text: typeConfig.emoji, cls: 'snapshot-type-emoji' });
        typeIndicator.createEl('span', { text: typeConfig.label, cls: 'snapshot-type-label' });

        // Snapshot info
        const infoDiv = snapshotItem.createEl('div', { cls: 'snapshot-info' });

        // Timestamp
        infoDiv.createEl('div', {
            text: this.formatTimestamp(snapshot.timestamp),
            cls: 'snapshot-timestamp',
        });

        // Description
        if (snapshot.metadata.description) {
            infoDiv.createEl('div', {
                text: snapshot.metadata.description,
                cls: 'snapshot-description',
            });
        }

        // Metadata row
        const metaRow = infoDiv.createEl('div', { cls: 'snapshot-meta-row' });
        metaRow.createEl('span', {
            text: `${this.formatBytes(snapshot.metadata.size_bytes)}`,
            cls: 'snapshot-size',
        });
        if (snapshot.metadata.tags && snapshot.metadata.tags.length > 0) {
            metaRow.createEl('span', {
                text: snapshot.metadata.tags.join(', '),
                cls: 'snapshot-tags',
            });
        }

        // Action buttons
        const actionsDiv = snapshotItem.createEl('div', { cls: 'snapshot-actions' });

        // Restore button
        const restoreBtn = actionsDiv.createEl('button', {
            text: '↩️ 回滚',
            cls: 'snapshot-restore-btn',
        });
        restoreBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleRollback(snapshot);
        });

        // Select on click
        snapshotItem.addEventListener('click', () => {
            this.selectedSnapshot = snapshot;
            this.contentEl.empty();
            this.renderContent();
        });
    }

    /**
     * Handle create snapshot action
     */
    private async handleCreateSnapshot(): Promise<void> {
        const description = await this.promptForDescription();
        if (description === null) return; // User cancelled

        try {
            new Notice('正在创建快照...');
            const result = await this.apiClient.createSnapshot({
                canvas_path: this.canvasPath,
                description: description || `手动快照 - ${new Date().toLocaleString('zh-CN')}`,
            });
            new Notice(`✅ 快照创建成功: ${result.id}`);
            await this.handleRefresh();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            new Notice(`❌ 创建快照失败: ${message}`);
        }
    }

    /**
     * Handle refresh action
     */
    private async handleRefresh(): Promise<void> {
        try {
            new Notice('正在刷新...');
            const response = await this.apiClient.listSnapshots(this.canvasPath);
            this.snapshots = response.snapshots;
            this.selectedSnapshot = null;
            this.contentEl.empty();
            this.renderContent();
            new Notice('✅ 刷新完成');
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            new Notice(`❌ 刷新失败: ${message}`);
        }
    }

    /**
     * Handle rollback action
     */
    private async handleRollback(snapshot: Snapshot): Promise<void> {
        // Confirmation dialog
        const confirmed = await this.confirmRollback(snapshot);
        if (!confirmed) return;

        try {
            new Notice('正在执行回滚...');
            const request: RollbackRequest = {
                canvas_path: this.canvasPath,
                rollback_type: 'snapshot',
                target_id: snapshot.id,
                create_backup: true,
                preserve_graph: true,
            };

            const result = await this.apiClient.executeRollback(request);

            if (result.success) {
                new Notice(`✅ 回滚成功！${result.backup_snapshot_id ? '已创建备份快照' : ''}`);
                this.close();
            } else {
                new Notice(`❌ 回滚失败: ${result.error || result.message}`);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            new Notice(`❌ 回滚失败: ${message}`);
        }
    }

    /**
     * Confirm rollback with user
     */
    private confirmRollback(snapshot: Snapshot): Promise<boolean> {
        return new Promise((resolve) => {
            const confirmModal = new ConfirmRollbackModal(
                this.app,
                snapshot,
                (confirmed) => resolve(confirmed)
            );
            confirmModal.open();
        });
    }

    /**
     * Prompt for snapshot description
     */
    private promptForDescription(): Promise<string | null> {
        return new Promise((resolve) => {
            const inputModal = new SnapshotDescriptionModal(
                this.app,
                (description) => resolve(description)
            );
            inputModal.open();
        });
    }

    /**
     * Render modal footer
     */
    private renderFooter(): void {
        const { contentEl } = this;
        const footer = contentEl.createEl('div', { cls: 'rollback-modal-footer' });

        const closeBtn = footer.createEl('button', {
            text: '关闭',
            cls: 'mod-cta',
        });
        closeBtn.addEventListener('click', () => this.close());
    }

    /**
     * Get canvas name from path
     */
    private getCanvasName(): string {
        const parts = this.canvasPath.split('/');
        return parts[parts.length - 1].replace('.canvas', '');
    }

    /**
     * Format timestamp to readable string
     */
    private formatTimestamp(timestamp: string): string {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return timestamp;
        }
    }

    /**
     * Format bytes to human-readable size
     */
    private formatBytes(bytes: number): string {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }
}

/**
 * Confirm Rollback Modal
 *
 * Confirmation dialog before executing rollback
 */
class ConfirmRollbackModal extends Modal {
    private snapshot: Snapshot;
    private onConfirm: (confirmed: boolean) => void;

    constructor(app: App, snapshot: Snapshot, onConfirm: (confirmed: boolean) => void) {
        super(app);
        this.snapshot = snapshot;
        this.onConfirm = onConfirm;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('confirm-rollback-modal');

        contentEl.createEl('h3', { text: '⚠️ 确认回滚' });

        contentEl.createEl('p', {
            text: `即将回滚到以下快照:`,
        });

        const detailsDiv = contentEl.createEl('div', { cls: 'rollback-confirm-details' });
        detailsDiv.createEl('p', {
            text: `时间: ${this.formatTimestamp(this.snapshot.timestamp)}`,
        });
        if (this.snapshot.metadata.description) {
            detailsDiv.createEl('p', {
                text: `描述: ${this.snapshot.metadata.description}`,
            });
        }

        contentEl.createEl('p', {
            text: '此操作会覆盖当前Canvas内容，但会自动创建备份快照。',
            cls: 'rollback-warning',
        });

        const buttonContainer = contentEl.createEl('div', { cls: 'rollback-confirm-buttons' });

        const cancelBtn = buttonContainer.createEl('button', { text: '取消' });
        cancelBtn.addEventListener('click', () => {
            this.onConfirm(false);
            this.close();
        });

        const confirmBtn = buttonContainer.createEl('button', {
            text: '确认回滚',
            cls: 'mod-warning',
        });
        confirmBtn.addEventListener('click', () => {
            this.onConfirm(true);
            this.close();
        });
    }

    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    private formatTimestamp(timestamp: string): string {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN');
        } catch {
            return timestamp;
        }
    }
}

/**
 * Snapshot Description Modal
 *
 * Input dialog for snapshot description
 */
class SnapshotDescriptionModal extends Modal {
    private onSubmit: (description: string | null) => void;
    private inputEl: HTMLInputElement | null = null;

    constructor(app: App, onSubmit: (description: string | null) => void) {
        super(app);
        this.onSubmit = onSubmit;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('snapshot-description-modal');

        contentEl.createEl('h3', { text: '📸 创建快照' });

        new Setting(contentEl)
            .setName('快照描述')
            .setDesc('为快照添加描述（可选）')
            .addText((text) => {
                this.inputEl = text.inputEl;
                text.setPlaceholder('例如: 完成第3章学习');
                text.inputEl.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.onSubmit(text.getValue());
                        this.close();
                    }
                });
            });

        const buttonContainer = contentEl.createEl('div', { cls: 'snapshot-description-buttons' });

        const cancelBtn = buttonContainer.createEl('button', { text: '取消' });
        cancelBtn.addEventListener('click', () => {
            this.onSubmit(null);
            this.close();
        });

        const submitBtn = buttonContainer.createEl('button', {
            text: '创建',
            cls: 'mod-cta',
        });
        submitBtn.addEventListener('click', () => {
            this.onSubmit(this.inputEl?.value || '');
            this.close();
        });

        // Focus input
        setTimeout(() => this.inputEl?.focus(), 50);
    }

    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }
}
