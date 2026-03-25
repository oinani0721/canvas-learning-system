/**
 * Canvas Info View - Canvas Metadata Display Sidebar
 *
 * Story 38.1: Canvas Metadata Management System
 *
 * This view displays:
 * - Current Canvas file path
 * - Subject identifier (e.g., "math54")
 * - Category identifier (e.g., "math")
 * - Group ID for Graphiti (e.g., "math54:离散数学")
 * - Metadata source (manual/config/inferred/default)
 * - LanceDB index status (indexed, node count, last updated)
 * - Re-index button
 *
 * @module CanvasInfoView
 * @version 1.0.0
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView Class)
 */

import { ItemView, WorkspaceLeaf, Notice, setIcon, TFile } from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import type {
    CanvasMetadataResponse,
    CanvasIndexStatusResponse,
    VaultIndexStatusResponse,
} from '../api/types';

export const VIEW_TYPE_CANVAS_INFO = 'canvas-info-view';

// =========================================================================
// Type Definitions
// =========================================================================

/**
 * Metadata source types
 * Matches CanvasMetadataResponse.source plus 'manual' for future support
 */
type MetadataSource = 'config' | 'inferred' | 'default' | 'manual';

/**
 * Canvas Info view state
 */
interface CanvasInfoState {
    loading: boolean;
    error: string | null;
    canvasPath: string | null;
    metadata: CanvasMetadataResponse | null;
    indexStatus: CanvasIndexStatusResponse | null;
    lastUpdated: Date | null;
    isIndexing: boolean;
    vaultIndexStatus: VaultIndexStatusResponse | null;
    isVaultIndexing: boolean;
}

const DEFAULT_STATE: CanvasInfoState = {
    loading: false,
    error: null,
    canvasPath: null,
    metadata: null,
    indexStatus: null,
    lastUpdated: null,
    isIndexing: false,
    vaultIndexStatus: null,
    isVaultIndexing: false,
};

// =========================================================================
// Canvas Info View
// =========================================================================

/**
 * Canvas Info View - Canvas Metadata Display
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView)
 */
export class CanvasInfoView extends ItemView {
    private plugin: CanvasReviewPlugin;
    private state: CanvasInfoState;
    private fileOpenHandler: (() => void) | null = null;

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;
        this.state = { ...DEFAULT_STATE };
    }

    getViewType(): string {
        return VIEW_TYPE_CANVAS_INFO;
    }

    getDisplayText(): string {
        return 'Canvas 信息';
    }

    getIcon(): string {
        return 'info';
    }

    async onOpen(): Promise<void> {
        // ItemView base class provides contentEl
        this.contentEl.empty();
        this.contentEl.addClass('canvas-info-view');

        // Add custom styles
        this.addStyles();

        // Register file open event
        this.fileOpenHandler = () => {
            const activeFile = this.app.workspace.getActiveFile();
            if (activeFile && activeFile.extension === 'canvas') {
                this.loadCanvasInfo(activeFile.path);
            }
        };
        this.app.workspace.on('file-open', this.fileOpenHandler);

        // Initial render
        this.render();

        // Check if a canvas file is already open
        const activeFile = this.app.workspace.getActiveFile();
        if (activeFile && activeFile.extension === 'canvas') {
            await this.loadCanvasInfo(activeFile.path);
        }
    }

    async onClose(): Promise<void> {
        // Remove event handler
        if (this.fileOpenHandler) {
            this.app.workspace.off('file-open', this.fileOpenHandler);
            this.fileOpenHandler = null;
        }
    }

    /**
     * Load Canvas info from backend
     */
    async loadCanvasInfo(canvasPath: string): Promise<void> {
        this.state = {
            ...this.state,
            loading: true,
            error: null,
            canvasPath,
        };
        this.render();

        try {
            const apiClient = this.plugin.getApiClient();
            if (!apiClient) {
                throw new Error('API 客户端未初始化');
            }

            // Fetch metadata, canvas index status, and vault index status in parallel
            const [metadata, indexStatus, vaultIndexStatus] = await Promise.all([
                apiClient.getCanvasMetadata(canvasPath),
                apiClient.getCanvasIndexStatus(canvasPath),
                apiClient.getVaultIndexStatus().catch(() => null),
            ]);

            this.state = {
                ...this.state,
                loading: false,
                metadata,
                indexStatus,
                vaultIndexStatus,
                lastUpdated: new Date(),
            };
        } catch (error) {
            console.error('[CanvasInfoView] Failed to load canvas info:', error);
            this.state = {
                ...this.state,
                loading: false,
                error: error instanceof Error ? error.message : '加载失败',
            };
        }

        this.render();
    }

    /**
     * Trigger re-indexing of current Canvas
     */
    async reindexCanvas(): Promise<void> {
        const canvasPath = this.state.canvasPath;
        if (!canvasPath || this.state.isIndexing) {
            return;
        }

        this.state = { ...this.state, isIndexing: true };
        this.render();

        try {
            const apiClient = this.plugin.getApiClient();
            if (!apiClient) {
                throw new Error('API 客户端未初始化');
            }

            const result = await apiClient.indexCanvas({
                canvas_path: canvasPath,
                force: true,
            });

            if (result.success) {
                new Notice(`索引成功: ${result.node_count} 个节点`);
                // Refresh index status
                await this.loadCanvasInfo(canvasPath);
            } else {
                new Notice(`索引失败: ${result.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('[CanvasInfoView] Failed to index canvas:', error);
            new Notice(`索引失败: ${error instanceof Error ? error.message : '未知错误'}`);
        } finally {
            this.state = { ...this.state, isIndexing: false };
            this.render();
        }
    }

    /**
     * Trigger full vault notes re-indexing
     */
    async reindexVault(): Promise<void> {
        if (this.state.isVaultIndexing) return;

        this.state = { ...this.state, isVaultIndexing: true };
        this.render();

        try {
            const apiClient = this.plugin.getApiClient();
            if (!apiClient) {
                throw new Error('API 客户端未初始化');
            }

            const result = await apiClient.indexVaultFull();

            if (result.success) {
                const count = result.chunk_count ?? 0;
                new Notice(`Vault 索引成功: ${count} 个文本块`);
                // Refresh vault index status
                const vaultIndexStatus = await apiClient.getVaultIndexStatus().catch(() => null);
                this.state = { ...this.state, vaultIndexStatus };
            } else {
                new Notice(`Vault 索引失败: ${result.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('[CanvasInfoView] Failed to index vault:', error);
            new Notice(`Vault 索引失败: ${error instanceof Error ? error.message : '未知错误'}`);
        } finally {
            this.state = { ...this.state, isVaultIndexing: false };
            this.render();
        }
    }

    /**
     * Render the view
     */
    private render(): void {
        this.contentEl.empty();

        // Header
        const header = this.contentEl.createDiv({ cls: 'canvas-info-header' });
        const headerTitle = header.createDiv({ cls: 'canvas-info-header-title' });
        setIcon(headerTitle.createSpan({ cls: 'canvas-info-icon' }), 'info');
        headerTitle.createSpan({ text: 'Canvas 信息' });

        // Refresh button
        const refreshBtn = header.createEl('button', {
            cls: 'canvas-info-refresh-btn clickable-icon',
            attr: { 'aria-label': '刷新' },
        });
        setIcon(refreshBtn, 'refresh-cw');
        refreshBtn.addEventListener('click', () => {
            if (this.state.canvasPath) {
                this.loadCanvasInfo(this.state.canvasPath);
            }
        });

        // Loading state
        if (this.state.loading) {
            const loadingDiv = this.contentEl.createDiv({ cls: 'canvas-info-loading' });
            loadingDiv.createSpan({ text: '加载中...' });
            return;
        }

        // Error state
        if (this.state.error) {
            const errorDiv = this.contentEl.createDiv({ cls: 'canvas-info-error' });
            setIcon(errorDiv.createSpan({ cls: 'canvas-info-error-icon' }), 'alert-circle');
            errorDiv.createSpan({ text: this.state.error });
            return;
        }

        // No canvas selected
        if (!this.state.canvasPath) {
            const emptyDiv = this.contentEl.createDiv({ cls: 'canvas-info-empty' });
            emptyDiv.createSpan({ text: '请打开一个 Canvas 文件' });
            return;
        }

        // Content sections
        this.renderMetadataSection();
        this.renderIndexSection();
        this.renderVaultIndexSection();
    }

    /**
     * Render metadata section
     */
    private renderMetadataSection(): void {
        const section = this.contentEl.createDiv({ cls: 'canvas-info-section' });
        section.createEl('h4', { text: '📊 元数据', cls: 'canvas-info-section-title' });

        const metadata = this.state.metadata;
        if (!metadata) {
            section.createDiv({ text: '无元数据', cls: 'canvas-info-empty-text' });
            return;
        }

        const grid = section.createDiv({ cls: 'canvas-info-grid' });

        // File path
        this.createInfoRow(grid, '文件', this.getFileName(metadata.canvas_path));

        // Subject
        this.createInfoRow(grid, '学科', metadata.subject, 'tag');

        // Category
        this.createInfoRow(grid, '大类', metadata.category, 'folder');

        // Group ID
        this.createInfoRow(grid, 'Group ID', metadata.group_id, 'database');

        // Source
        const sourceText = this.getSourceText(metadata.source);
        const sourceClass = this.getSourceClass(metadata.source);
        const sourceRow = this.createInfoRow(grid, '来源', sourceText, 'info');
        sourceRow.addClass(sourceClass);
    }

    /**
     * Render index status section
     */
    private renderIndexSection(): void {
        const section = this.contentEl.createDiv({ cls: 'canvas-info-section' });

        const titleRow = section.createDiv({ cls: 'canvas-info-section-title-row' });
        titleRow.createEl('h4', { text: '📦 LanceDB 索引', cls: 'canvas-info-section-title' });

        // Re-index button
        const reindexBtn = titleRow.createEl('button', {
            cls: 'canvas-info-reindex-btn',
            text: this.state.isIndexing ? '索引中...' : '🔄 重新索引',
        });
        reindexBtn.disabled = this.state.isIndexing;
        reindexBtn.addEventListener('click', () => this.reindexCanvas());

        const indexStatus = this.state.indexStatus;
        if (!indexStatus) {
            section.createDiv({ text: '无索引状态', cls: 'canvas-info-empty-text' });
            return;
        }

        const grid = section.createDiv({ cls: 'canvas-info-grid' });

        // Indexed status
        const statusText = indexStatus.indexed ? '✅ 已索引' : '❌ 未索引';
        const statusClass = indexStatus.indexed ? 'canvas-info-status-indexed' : 'canvas-info-status-not-indexed';
        const statusRow = this.createInfoRow(grid, '状态', statusText);
        statusRow.addClass(statusClass);

        // Node count
        if (indexStatus.indexed) {
            this.createInfoRow(grid, '节点数', indexStatus.node_count.toString(), 'hash');
        }

        // Subject used
        if (indexStatus.subject) {
            this.createInfoRow(grid, '索引学科', indexStatus.subject, 'tag');
        }

        // Last indexed
        if (indexStatus.last_indexed) {
            const date = new Date(indexStatus.last_indexed);
            this.createInfoRow(grid, '更新时间', date.toLocaleString('zh-CN'), 'clock');
        }
    }

    /**
     * Render vault notes index section
     */
    private renderVaultIndexSection(): void {
        const section = this.contentEl.createDiv({ cls: 'canvas-info-section' });

        const titleRow = section.createDiv({ cls: 'canvas-info-section-title-row' });
        titleRow.createEl('h4', { text: '📚 Vault 笔记索引', cls: 'canvas-info-section-title' });

        // Full re-index button
        const reindexBtn = titleRow.createEl('button', {
            cls: 'canvas-info-reindex-btn',
            text: this.state.isVaultIndexing ? '索引中...' : '🔄 全量索引',
        });
        reindexBtn.disabled = this.state.isVaultIndexing;
        reindexBtn.addEventListener('click', () => this.reindexVault());

        const vaultStatus = this.state.vaultIndexStatus;
        if (!vaultStatus) {
            section.createDiv({ text: '无法获取 Vault 索引状态', cls: 'canvas-info-empty-text' });
            return;
        }

        const grid = section.createDiv({ cls: 'canvas-info-grid' });

        // Indexed status
        const statusText = vaultStatus.indexed ? '✅ 已索引' : '❌ 未索引';
        const statusClass = vaultStatus.indexed ? 'canvas-info-status-indexed' : 'canvas-info-status-not-indexed';
        const statusRow = this.createInfoRow(grid, '状态', statusText);
        statusRow.addClass(statusClass);

        // Chunk count
        if (vaultStatus.indexed) {
            this.createInfoRow(grid, '文本块数', vaultStatus.chunk_count.toString(), 'hash');
        }

        // Hint text
        if (!vaultStatus.indexed) {
            section.createDiv({
                text: '点击"全量索引"初始化笔记搜索。之后 .md 文件变更将自动增量索引。',
                cls: 'canvas-info-hint-text',
            });
        }
    }

    /**
     * Create an info row
     */
    private createInfoRow(
        container: HTMLElement,
        label: string,
        value: string,
        icon?: string
    ): HTMLElement {
        const row = container.createDiv({ cls: 'canvas-info-row' });
        row.createSpan({ text: label, cls: 'canvas-info-label' });

        const valueEl = row.createSpan({ cls: 'canvas-info-value' });
        if (icon) {
            setIcon(valueEl.createSpan({ cls: 'canvas-info-value-icon' }), icon);
        }
        valueEl.createSpan({ text: value });

        return row;
    }

    /**
     * Get file name from path
     */
    private getFileName(path: string): string {
        const parts = path.split('/');
        return parts[parts.length - 1];
    }

    /**
     * Get display text for metadata source
     */
    private getSourceText(source: MetadataSource): string {
        switch (source) {
            case 'manual':
                return '手动指定 ✓';
            case 'config':
                return '配置文件 ✓';
            case 'inferred':
                return '路径推断';
            case 'default':
                return '默认值';
            default:
                return '未知';
        }
    }

    /**
     * Get CSS class for metadata source
     */
    private getSourceClass(source: MetadataSource): string {
        switch (source) {
            case 'manual':
            case 'config':
                return 'canvas-info-source-verified';
            case 'inferred':
                return 'canvas-info-source-inferred';
            case 'default':
                return 'canvas-info-source-default';
            default:
                return '';
        }
    }

    /**
     * Add custom styles
     */
    private addStyles(): void {
        const styleId = 'canvas-info-view-styles';
        if (document.getElementById(styleId)) {
            return;
        }

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .canvas-info-view {
                padding: 12px;
                font-size: 13px;
            }

            .canvas-info-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 8px;
                border-bottom: 1px solid var(--background-modifier-border);
            }

            .canvas-info-header-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                font-size: 14px;
            }

            .canvas-info-icon {
                color: var(--text-accent);
            }

            .canvas-info-refresh-btn {
                padding: 4px;
                border-radius: 4px;
            }

            .canvas-info-loading,
            .canvas-info-error,
            .canvas-info-empty {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 16px;
                color: var(--text-muted);
                justify-content: center;
            }

            .canvas-info-error {
                color: var(--text-error);
            }

            .canvas-info-error-icon {
                color: var(--text-error);
            }

            .canvas-info-section {
                margin-bottom: 16px;
            }

            .canvas-info-section-title {
                margin: 0 0 8px 0;
                font-size: 13px;
                font-weight: 600;
                color: var(--text-normal);
            }

            .canvas-info-section-title-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }

            .canvas-info-section-title-row .canvas-info-section-title {
                margin: 0;
            }

            .canvas-info-reindex-btn {
                padding: 4px 8px;
                font-size: 11px;
                border-radius: 4px;
                cursor: pointer;
                background: var(--interactive-accent);
                color: var(--text-on-accent);
                border: none;
            }

            .canvas-info-reindex-btn:hover:not(:disabled) {
                background: var(--interactive-accent-hover);
            }

            .canvas-info-reindex-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .canvas-info-grid {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .canvas-info-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 4px 8px;
                background: var(--background-secondary);
                border-radius: 4px;
            }

            .canvas-info-label {
                color: var(--text-muted);
                font-size: 12px;
            }

            .canvas-info-value {
                display: flex;
                align-items: center;
                gap: 4px;
                font-family: var(--font-monospace);
                font-size: 12px;
                color: var(--text-normal);
            }

            .canvas-info-value-icon {
                color: var(--text-muted);
                width: 12px;
                height: 12px;
            }

            .canvas-info-empty-text {
                color: var(--text-muted);
                font-style: italic;
                padding: 8px;
            }

            .canvas-info-status-indexed .canvas-info-value {
                color: var(--text-success);
            }

            .canvas-info-status-not-indexed .canvas-info-value {
                color: var(--text-error);
            }

            .canvas-info-source-verified .canvas-info-value {
                color: var(--text-success);
            }

            .canvas-info-source-inferred .canvas-info-value {
                color: var(--text-warning);
            }

            .canvas-info-source-default .canvas-info-value {
                color: var(--text-muted);
            }
        `;
        document.head.appendChild(style);
    }
}
