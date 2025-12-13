/**
 * Cross-Canvas Sidebar - Canvas Learning System
 *
 * Sidebar component for displaying cross-Canvas associations.
 * Implements Story 25.1: Cross-Canvas UI Entry Points (AC: 4, 5)
 *
 * Features:
 * - Display list of associated Canvas files
 * - Show association type icons and labels
 * - Click-to-jump navigation
 * - Real-time association updates
 *
 * @module CrossCanvasSidebar
 * @version 1.0.0
 *
 * ✅ Verified from Story 25.1 (AC4, AC5)
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView Class)
 */

import { ItemView, WorkspaceLeaf, Notice, setIcon, TFile } from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import type { CrossCanvasService } from '../services/CrossCanvasService';
import type { CanvasRelationshipType, CrossCanvasAssociation } from '../types/UITypes';

export const VIEW_TYPE_CROSS_CANVAS_SIDEBAR = 'cross-canvas-sidebar-view';

// =========================================================================
// Type Definitions
// =========================================================================

/**
 * Extended relationship types (now unified with base type per Story 25.3)
 * Kept for backward compatibility with existing code
 * [Source: Story 25.3 - Exercise-Lecture Canvas Association]
 */
type ExtendedRelationshipType = CanvasRelationshipType;

/**
 * Association type configuration for display
 * [Source: Story 25.1 Dev Notes - CrossCanvasModal pattern]
 */
const RELATIONSHIP_TYPE_CONFIG: Record<ExtendedRelationshipType, {
    label: string;
    icon: string;
    description: string;
    color: string;
}> = {
    prerequisite: {
        label: '前置知识',
        icon: 'book-open',
        description: '需要先学习的基础知识',
        color: '#e74c3c',
    },
    related: {
        label: '相关内容',
        icon: 'link',
        description: '相关联的知识点',
        color: '#3498db',
    },
    application: {
        label: '应用场景',
        icon: 'target',
        description: '知识的实际应用场景',
        color: '#2ecc71',
    },
    exercise_lecture: {
        label: '题目-讲座',
        icon: 'book',
        description: '练习题目关联到讲座Canvas',
        color: '#9b59b6',
    },
    exercise_solution: {
        label: '题目-解答',
        icon: 'check-square',
        description: '练习题目关联到解答Canvas',
        color: '#f39c12',
    },
};

/**
 * Sidebar view state
 */
interface CrossCanvasSidebarState {
    loading: boolean;
    error: string | null;
    currentCanvasPath: string | null;
    associations: CrossCanvasAssociation[];
    lastUpdated: Date | null;
    filterType: ExtendedRelationshipType | 'all';
}

const DEFAULT_STATE: CrossCanvasSidebarState = {
    loading: false,
    error: null,
    currentCanvasPath: null,
    associations: [],
    lastUpdated: null,
    filterType: 'all',
};

// =========================================================================
// Cross-Canvas Sidebar View
// =========================================================================

/**
 * Cross-Canvas Sidebar View - Association List Display
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView)
 * ✅ Verified from Story 25.1 (AC4, AC5)
 */
export class CrossCanvasSidebarView extends ItemView {
    private plugin: CanvasReviewPlugin;
    private crossCanvasService: CrossCanvasService | null = null;
    private state: CrossCanvasSidebarState;
    private refreshInterval: number | null = null;

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;
        this.state = { ...DEFAULT_STATE };
    }

    getViewType(): string {
        return VIEW_TYPE_CROSS_CANVAS_SIDEBAR;
    }

    getDisplayText(): string {
        return 'Canvas关联';
    }

    getIcon(): string {
        return 'link-2';
    }

    /**
     * Set the CrossCanvasService dependency
     */
    setCrossCanvasService(service: CrossCanvasService): void {
        this.crossCanvasService = service;
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        container.addClass('cross-canvas-sidebar-container');

        this.render();

        // Watch for active file changes
        this.registerEvent(
            this.app.workspace.on('active-leaf-change', () => {
                this.handleActiveFileChange();
            })
        );

        // Initial load
        this.handleActiveFileChange();

        // Setup auto-refresh (every 60 seconds)
        this.refreshInterval = window.setInterval(() => {
            if (this.state.currentCanvasPath) {
                this.loadAssociations();
            }
        }, 60 * 1000);
    }

    async onClose(): Promise<void> {
        if (this.refreshInterval !== null) {
            window.clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // =========================================================================
    // Event Handlers
    // =========================================================================

    /**
     * Handle active file change - update sidebar for current Canvas
     */
    private handleActiveFileChange(): void {
        const activeFile = this.app.workspace.getActiveFile();

        if (activeFile && activeFile.extension === 'canvas') {
            if (this.state.currentCanvasPath !== activeFile.path) {
                this.updateViewState({
                    currentCanvasPath: activeFile.path,
                });
                this.loadAssociations();
            }
        } else {
            // Not viewing a Canvas file
            this.updateViewState({
                currentCanvasPath: null,
                associations: [],
            });
        }
    }

    // =========================================================================
    // Data Loading
    // =========================================================================

    /**
     * Load associations for current Canvas
     */
    private async loadAssociations(): Promise<void> {
        if (!this.state.currentCanvasPath) {
            return;
        }

        if (!this.crossCanvasService) {
            this.updateViewState({
                error: 'CrossCanvasService 未初始化',
            });
            return;
        }

        this.updateViewState({ loading: true, error: null });

        try {
            const associations = await this.crossCanvasService.getAssociationsForCanvas(
                this.state.currentCanvasPath
            );

            this.updateViewState({
                associations: associations || [],
                loading: false,
                lastUpdated: new Date(),
            });
        } catch (error) {
            console.error('[CrossCanvasSidebar] Failed to load associations:', error);
            this.updateViewState({
                loading: false,
                error: (error as Error).message,
            });
        }
    }

    /**
     * Refresh associations from backend
     */
    async refresh(): Promise<void> {
        await this.loadAssociations();
    }

    // =========================================================================
    // State Management
    // =========================================================================

    private updateViewState(updates: Partial<CrossCanvasSidebarState>): void {
        this.state = { ...this.state, ...updates };
        this.render();
    }

    private render(): void {
        const container = this.containerEl.children[1] as HTMLElement;
        if (container) {
            container.empty();
            this.renderView(container);
        }
    }

    // =========================================================================
    // Rendering
    // =========================================================================

    /**
     * Main render method
     * [Source: Story 25.1 Dev Notes - Sidebar View Pattern]
     */
    private renderView(container: HTMLElement): void {
        const view = container.createDiv({ cls: 'cross-canvas-sidebar-view' });

        // Header
        this.renderHeader(view);

        // Content area
        const content = view.createDiv({ cls: 'sidebar-content' });

        if (!this.state.currentCanvasPath) {
            this.renderNoCanvasState(content);
            return;
        }

        if (this.state.loading) {
            this.renderLoadingState(content);
            return;
        }

        if (this.state.error) {
            this.renderErrorState(content);
            return;
        }

        // Filter controls
        this.renderFilterControls(content);

        // Association list
        this.renderAssociationList(content);
    }

    /**
     * Render header section
     */
    private renderHeader(container: HTMLElement): void {
        const header = container.createDiv({ cls: 'sidebar-header' });

        // Title
        const titleArea = header.createDiv({ cls: 'header-title-area' });
        const iconSpan = titleArea.createSpan({ cls: 'header-icon' });
        setIcon(iconSpan, 'link-2');
        titleArea.createSpan({ text: 'Canvas关联', cls: 'header-title' });

        // Actions
        const actions = header.createDiv({ cls: 'header-actions' });

        // Add association button
        const addBtn = actions.createEl('button', {
            cls: 'action-button add-button',
            attr: { 'aria-label': '创建关联' },
        });
        setIcon(addBtn, 'plus');
        addBtn.onclick = () => this.openCreateAssociationModal();

        // Refresh button
        const refreshBtn = actions.createEl('button', {
            cls: 'action-button refresh-button',
            attr: { 'aria-label': '刷新' },
        });
        setIcon(refreshBtn, 'refresh-cw');
        if (this.state.loading) {
            refreshBtn.addClass('spinning');
        }
        refreshBtn.onclick = () => this.loadAssociations();
    }

    /**
     * Render filter controls
     */
    private renderFilterControls(container: HTMLElement): void {
        const filterArea = container.createDiv({ cls: 'filter-controls' });

        const filterLabel = filterArea.createSpan({
            text: '筛选: ',
            cls: 'filter-label',
        });

        const filterSelect = filterArea.createEl('select', {
            cls: 'filter-select',
        });

        // All option
        const allOption = filterSelect.createEl('option', {
            text: '全部类型',
            attr: { value: 'all' },
        });
        if (this.state.filterType === 'all') {
            allOption.selected = true;
        }

        // Type options
        Object.entries(RELATIONSHIP_TYPE_CONFIG).forEach(([type, config]) => {
            const option = filterSelect.createEl('option', {
                text: `${config.icon} ${config.label}`,
                attr: { value: type },
            });
            if (this.state.filterType === type) {
                option.selected = true;
            }
        });

        filterSelect.onchange = () => {
            this.updateViewState({
                filterType: filterSelect.value as ExtendedRelationshipType | 'all',
            });
        };

        // Association count
        const filteredCount = this.getFilteredAssociations().length;
        const totalCount = this.state.associations.length;
        filterArea.createSpan({
            text: ` (${filteredCount}/${totalCount})`,
            cls: 'association-count',
        });
    }

    /**
     * Get filtered associations based on current filter
     */
    private getFilteredAssociations(): CrossCanvasAssociation[] {
        if (this.state.filterType === 'all') {
            return this.state.associations;
        }
        return this.state.associations.filter(
            (a) => a.relationshipType === this.state.filterType
        );
    }

    /**
     * Render association list (AC 4)
     * [Source: Story 25.1 AC4 - Sidebar Canvas association list]
     */
    private renderAssociationList(container: HTMLElement): void {
        const filtered = this.getFilteredAssociations();

        if (filtered.length === 0) {
            this.renderEmptyState(container);
            return;
        }

        const list = container.createDiv({ cls: 'association-list' });

        filtered.forEach((association) => {
            this.renderAssociationItem(list, association);
        });
    }

    /**
     * Render single association item (AC 4, AC 5)
     * [Source: Story 25.1 AC4, AC5 - Show association with click-to-jump]
     */
    private renderAssociationItem(
        container: HTMLElement,
        association: CrossCanvasAssociation
    ): void {
        const item = container.createDiv({ cls: 'association-item' });

        // Determine which canvas to display (the other one from current)
        const isSource = association.sourceCanvasPath === this.state.currentCanvasPath;
        const targetPath = isSource ? association.targetCanvasPath : association.sourceCanvasPath;
        const targetName = this.getCanvasDisplayName(targetPath);

        // Type icon and label
        const typeConfig = RELATIONSHIP_TYPE_CONFIG[association.relationshipType as ExtendedRelationshipType] ||
            RELATIONSHIP_TYPE_CONFIG['related'];

        const typeArea = item.createDiv({ cls: 'item-type' });
        const iconSpan = typeArea.createSpan({ cls: 'type-icon' });
        setIcon(iconSpan, typeConfig.icon);
        iconSpan.style.color = typeConfig.color;

        // Canvas name (clickable) - AC 5
        const nameArea = item.createDiv({ cls: 'item-name' });
        const nameLink = nameArea.createEl('a', {
            text: targetName,
            cls: 'canvas-link',
            attr: { href: '#' },
        });
        nameLink.onclick = (e) => {
            e.preventDefault();
            // Navigate to canvas (node ID not available in current schema)
            this.navigateToCanvas(targetPath);
        };

        // Type label
        const labelSpan = item.createSpan({
            text: typeConfig.label,
            cls: 'type-label',
        });
        labelSpan.style.backgroundColor = `${typeConfig.color}20`;
        labelSpan.style.color = typeConfig.color;

        // Direction indicator
        const directionSpan = item.createSpan({
            text: isSource ? '→' : '←',
            cls: 'direction-indicator',
        });

        // Bidirectional indicator (extend type to support optional bidirectional field)
        const extWithBi = association as CrossCanvasAssociation & { bidirectional?: boolean };
        if (extWithBi.bidirectional) {
            const biIcon = item.createSpan({ cls: 'bidirectional-icon' });
            setIcon(biIcon, 'arrow-left-right');
            biIcon.setAttribute('aria-label', '双向关联');
        }

        // Confidence score (if available)
        const extAssoc = association as CrossCanvasAssociation & { confidence?: number };
        if (extAssoc.confidence !== undefined && extAssoc.confidence > 0) {
            const confidenceSpan = item.createSpan({
                text: `${Math.round(extAssoc.confidence * 100)}%`,
                cls: 'confidence-score',
            });
        }

        // Actions
        const actionsArea = item.createDiv({ cls: 'item-actions' });

        // Jump button
        const jumpBtn = actionsArea.createEl('button', {
            cls: 'item-action jump-button',
            attr: { 'aria-label': '跳转' },
        });
        setIcon(jumpBtn, 'external-link');
        jumpBtn.onclick = (e) => {
            e.stopPropagation();
            // Navigate to canvas (node ID not available in current schema)
            this.navigateToCanvas(targetPath);
        };

        // Delete button
        const deleteBtn = actionsArea.createEl('button', {
            cls: 'item-action delete-button',
            attr: { 'aria-label': '删除关联' },
        });
        setIcon(deleteBtn, 'trash-2');
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            this.deleteAssociation(association);
        };
    }

    /**
     * Navigate to Canvas file (AC 5)
     * [Source: Story 25.1 AC5 - Click-to-jump navigation]
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Workspace.openLinkText)
     */
    private async navigateToCanvas(canvasPath: string, nodeId?: string): Promise<void> {
        try {
            // Open the Canvas file using Obsidian API
            // ✅ Verified from Context7: app.workspace.openLinkText()
            await this.app.workspace.openLinkText(canvasPath, '', true);

            // If a specific node is specified, try to focus on it
            if (nodeId) {
                // Note: Canvas node focus requires additional Canvas API interaction
                // This would be handled by Canvas event handlers
                new Notice(`已打开 Canvas，请找到节点: ${nodeId}`);
            }
        } catch (error) {
            console.error('[CrossCanvasSidebar] Failed to navigate:', error);
            new Notice(`无法打开 Canvas: ${(error as Error).message}`);
        }
    }

    /**
     * Get display name from Canvas path
     */
    private getCanvasDisplayName(path: string): string {
        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.canvas', '');
    }

    /**
     * Open create association modal
     */
    private openCreateAssociationModal(): void {
        if (!this.state.currentCanvasPath) {
            new Notice('请先打开一个 Canvas 文件');
            return;
        }

        // Trigger the menu action if available
        // This connects to the ContextMenuManager's action registry
        const event = new CustomEvent('cross-canvas:open-modal', {
            detail: { canvasPath: this.state.currentCanvasPath },
        });
        window.dispatchEvent(event);
    }

    /**
     * Delete association
     */
    private async deleteAssociation(association: CrossCanvasAssociation): Promise<void> {
        if (!this.crossCanvasService) {
            new Notice('CrossCanvasService 未初始化');
            return;
        }

        const confirmed = await this.confirmDelete(association);
        if (!confirmed) {
            return;
        }

        try {
            // ✅ Fixed: Use deleteAssociation method (not deleteCanvasAssociation)
            await this.crossCanvasService.deleteAssociation(association.id);
            new Notice('关联已删除');
            await this.loadAssociations();
        } catch (error) {
            console.error('[CrossCanvasSidebar] Failed to delete:', error);
            new Notice(`删除失败: ${(error as Error).message}`);
        }
    }

    /**
     * Confirm delete dialog
     */
    private async confirmDelete(association: CrossCanvasAssociation): Promise<boolean> {
        // Simple confirmation using Notice for now
        // Could be replaced with a proper modal in the future
        return new Promise((resolve) => {
            const targetName = this.getCanvasDisplayName(
                association.sourceCanvasPath === this.state.currentCanvasPath
                    ? association.targetCanvasPath
                    : association.sourceCanvasPath
            );

            // For now, always confirm (proper modal would be better UX)
            // TODO: Implement proper confirmation modal
            resolve(confirm(`确定要删除与 "${targetName}" 的关联吗？`));
        });
    }

    // =========================================================================
    // State Rendering Helpers
    // =========================================================================

    private renderNoCanvasState(container: HTMLElement): void {
        const emptyState = container.createDiv({ cls: 'empty-state' });
        const iconSpan = emptyState.createSpan({ cls: 'empty-icon' });
        setIcon(iconSpan, 'file-question');
        emptyState.createEl('p', {
            text: '请打开一个 Canvas 文件查看其关联',
            cls: 'empty-message',
        });
    }

    private renderEmptyState(container: HTMLElement): void {
        const emptyState = container.createDiv({ cls: 'empty-state' });
        const iconSpan = emptyState.createSpan({ cls: 'empty-icon' });
        setIcon(iconSpan, 'link');
        emptyState.createEl('p', {
            text: '此 Canvas 暂无关联',
            cls: 'empty-message',
        });

        const addBtn = emptyState.createEl('button', {
            text: '创建关联',
            cls: 'empty-action-button',
        });
        addBtn.onclick = () => this.openCreateAssociationModal();
    }

    private renderLoadingState(container: HTMLElement): void {
        const loading = container.createDiv({ cls: 'loading-state' });
        loading.createDiv({ cls: 'spinner' });
        loading.createSpan({ text: '加载中...' });
    }

    private renderErrorState(container: HTMLElement): void {
        const error = container.createDiv({ cls: 'error-state' });
        const iconSpan = error.createSpan({ cls: 'error-icon' });
        setIcon(iconSpan, 'alert-circle');
        error.createSpan({
            text: this.state.error || '加载失败',
            cls: 'error-message',
        });

        const retryBtn = error.createEl('button', {
            cls: 'retry-button',
            text: '重试',
        });
        retryBtn.onclick = () => this.loadAssociations();
    }
}

// =========================================================================
// Factory Function
// =========================================================================

/**
 * Create CrossCanvasSidebarView instance
 * [Source: Story 25.1 Task 3.1]
 */
export function createCrossCanvasSidebarView(
    leaf: WorkspaceLeaf,
    plugin: CanvasReviewPlugin
): CrossCanvasSidebarView {
    return new CrossCanvasSidebarView(leaf, plugin);
}
