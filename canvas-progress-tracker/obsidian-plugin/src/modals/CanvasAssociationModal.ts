/**
 * Canvas Association Modal - Canvas Learning System Cross-Canvas Associations
 *
 * Main modal for viewing and managing Canvas associations.
 * Implements Story 16.1: Canvas关联UI
 *
 * @module modals/CanvasAssociationModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 16.1 Dev Notes (Modal design)
 */

import { App, Modal, Notice, TFile, Menu } from 'obsidian';
import type {
    CanvasAssociation,
    AssociationType,
    CanvasLinksConfig,
    ASSOCIATION_TYPE_CONFIG
} from '../types/AssociationTypes';
import { DEFAULT_ASSOCIATION, DEFAULT_CANVAS_LINKS_CONFIG } from '../types/AssociationTypes';

/**
 * Sort options for association list
 */
type SortOption = 'date' | 'type' | 'relevance';

/**
 * Filter options for association list
 */
interface FilterState {
    types: AssociationType[];
    searchQuery: string;
}

/**
 * Canvas Association Modal
 *
 * Provides a UI for viewing and managing cross-Canvas associations.
 * Shows current Canvas's associations with filtering, sorting, and CRUD operations.
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class CanvasAssociationModal extends Modal {
    private currentCanvasPath: string;
    private associations: CanvasAssociation[];
    private config: CanvasLinksConfig;
    private sortBy: SortOption = 'date';
    private filter: FilterState = { types: [], searchQuery: '' };
    private onSave: ((associations: CanvasAssociation[]) => Promise<void>) | null;
    private onCreateAssociation: (() => void) | null;
    private onNavigate: ((canvasPath: string) => Promise<void>) | null;

    /**
     * Association type configuration for display
     * ✅ Verified from Story 16.1 Dev Notes (ASSOCIATION_TYPE_CONFIG)
     */
    private static readonly TYPE_CONFIG: Record<AssociationType, {
        label: string;
        icon: string;
        description: string;
        color: string;
    }> = {
        prerequisite: {
            label: '前置知识',
            icon: '📚',
            description: '需要先学习的基础知识',
            color: '#e74c3c'
        },
        related: {
            label: '相关内容',
            icon: '🔗',
            description: '相关联的知识点',
            color: '#3498db'
        },
        extends: {
            label: '扩展内容',
            icon: '📈',
            description: '深入或扩展的知识',
            color: '#2ecc71'
        },
        references: {
            label: '教材引用',
            icon: '📖',
            description: '引用的教材或参考资料',
            color: '#9b59b6'
        }
    };

    /**
     * Creates a new CanvasAssociationModal
     *
     * @param app - Obsidian App instance
     * @param currentCanvasPath - Path of the current Canvas file
     * @param associations - Array of associations for this Canvas
     * @param config - Canvas links configuration
     * @param onSave - Callback for saving associations
     * @param onCreateAssociation - Callback for opening create modal
     * @param onNavigate - Callback for navigating to another Canvas
     */
    constructor(
        app: App,
        currentCanvasPath: string,
        associations: CanvasAssociation[],
        config?: CanvasLinksConfig,
        onSave?: (associations: CanvasAssociation[]) => Promise<void>,
        onCreateAssociation?: () => void,
        onNavigate?: (canvasPath: string) => Promise<void>
    ) {
        super(app);
        this.currentCanvasPath = currentCanvasPath;
        this.associations = associations;
        this.config = config || DEFAULT_CANVAS_LINKS_CONFIG;
        this.onSave = onSave || null;
        this.onCreateAssociation = onCreateAssociation || null;
        this.onNavigate = onNavigate || null;
    }

    /**
     * Called when the modal is opened
     * ✅ Verified from @obsidian-canvas Skill (Modal lifecycle)
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();

        // Add modal class for styling
        contentEl.addClass('canvas-association-modal');

        // Header with title and add button
        this.renderHeader(contentEl);

        // Toolbar with sort and filter
        this.renderToolbar(contentEl);

        // Association list
        this.renderAssociationList(contentEl);

        // Footer with actions
        this.renderFooter(contentEl);
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    // ========== Render Methods ==========

    /**
     * Render modal header
     */
    private renderHeader(container: HTMLElement): void {
        const header = container.createEl('div', {
            cls: 'association-modal-header'
        });

        // Title section
        const titleSection = header.createEl('div', {
            cls: 'association-modal-title-section'
        });

        titleSection.createEl('h2', {
            text: '🔗 Canvas关联管理',
            cls: 'association-modal-title'
        });

        // Current canvas name
        const canvasName = this.extractCanvasName(this.currentCanvasPath);
        titleSection.createEl('span', {
            text: `当前: ${canvasName}`,
            cls: 'association-modal-subtitle'
        });

        // Add button
        const addBtn = header.createEl('button', {
            text: '+ 添加关联',
            cls: 'association-add-btn mod-cta'
        });
        addBtn.addEventListener('click', () => {
            if (this.onCreateAssociation) {
                this.onCreateAssociation();
            }
        });
    }

    /**
     * Render toolbar with sort and filter options
     */
    private renderToolbar(container: HTMLElement): void {
        const toolbar = container.createEl('div', {
            cls: 'association-modal-toolbar'
        });

        // Search input
        const searchContainer = toolbar.createEl('div', {
            cls: 'association-search-container'
        });

        const searchInput = searchContainer.createEl('input', {
            type: 'text',
            placeholder: '搜索关联...',
            cls: 'association-search-input'
        });
        searchInput.value = this.filter.searchQuery;
        searchInput.addEventListener('input', (e) => {
            this.filter.searchQuery = (e.target as HTMLInputElement).value;
            this.refreshList(container);
        });

        // Sort dropdown
        const sortContainer = toolbar.createEl('div', {
            cls: 'association-sort-container'
        });

        sortContainer.createEl('label', { text: '排序:' });

        const sortSelect = sortContainer.createEl('select', {
            cls: 'association-sort-select'
        });

        const sortOptions: { value: SortOption; label: string }[] = [
            { value: 'date', label: '按日期' },
            { value: 'type', label: '按类型' },
            { value: 'relevance', label: '按相关度' }
        ];

        for (const opt of sortOptions) {
            const option = sortSelect.createEl('option', {
                value: opt.value,
                text: opt.label
            });
            if (opt.value === this.sortBy) {
                option.selected = true;
            }
        }

        sortSelect.addEventListener('change', (e) => {
            this.sortBy = (e.target as HTMLSelectElement).value as SortOption;
            this.refreshList(container);
        });

        // Filter chips
        const filterContainer = toolbar.createEl('div', {
            cls: 'association-filter-container'
        });

        for (const [type, config] of Object.entries(CanvasAssociationModal.TYPE_CONFIG)) {
            const chip = filterContainer.createEl('button', {
                cls: `association-filter-chip ${this.filter.types.includes(type as AssociationType) ? 'active' : ''}`
            });
            chip.createSpan({ text: `${config.icon} ${config.label}` });
            chip.style.borderColor = config.color;

            chip.addEventListener('click', () => {
                const typeKey = type as AssociationType;
                if (this.filter.types.includes(typeKey)) {
                    this.filter.types = this.filter.types.filter(t => t !== typeKey);
                } else {
                    this.filter.types.push(typeKey);
                }
                this.refreshList(container);
            });
        }
    }

    /**
     * Render association list
     */
    private renderAssociationList(container: HTMLElement): void {
        // Remove existing list
        const existingList = container.querySelector('.association-modal-list');
        if (existingList) {
            existingList.remove();
        }

        const listContainer = container.createEl('div', {
            cls: 'association-modal-list'
        });

        // Get filtered and sorted associations
        const filteredAssociations = this.getFilteredAssociations();

        // Show empty state if no associations
        if (filteredAssociations.length === 0) {
            const emptyState = listContainer.createEl('div', {
                cls: 'association-empty-state'
            });

            if (this.associations.length === 0) {
                emptyState.createEl('div', {
                    text: '🔗',
                    cls: 'association-empty-icon'
                });
                emptyState.createEl('div', {
                    text: '暂无关联',
                    cls: 'association-empty-title'
                });
                emptyState.createEl('div', {
                    text: '点击"添加关联"按钮创建第一个Canvas关联',
                    cls: 'association-empty-description'
                });
            } else {
                emptyState.createEl('div', {
                    text: '没有找到匹配的关联',
                    cls: 'association-empty-title'
                });
            }
            return;
        }

        // Render association cards
        for (const association of filteredAssociations) {
            this.renderAssociationCard(listContainer, association);
        }
    }

    /**
     * Render single association card
     */
    private renderAssociationCard(container: HTMLElement, association: CanvasAssociation): void {
        const card = container.createEl('div', {
            cls: 'association-card'
        });

        // Determine if current canvas is source or target
        const isSource = association.source_canvas === this.currentCanvasPath;
        const linkedCanvas = isSource ? association.target_canvas : association.source_canvas;
        const linkedCanvasName = this.extractCanvasName(linkedCanvas);

        // Type badge
        const typeConfig = CanvasAssociationModal.TYPE_CONFIG[association.association_type];
        const typeBadge = card.createEl('div', {
            cls: 'association-type-badge'
        });
        typeBadge.style.backgroundColor = typeConfig.color;
        typeBadge.createSpan({ text: `${typeConfig.icon} ${typeConfig.label}` });

        // Direction indicator
        if (association.bidirectional) {
            card.createEl('span', {
                text: '↔️',
                cls: 'association-direction',
                attr: { 'aria-label': '双向关联' }
            });
        } else {
            card.createEl('span', {
                text: isSource ? '→' : '←',
                cls: 'association-direction',
                attr: { 'aria-label': isSource ? '指向目标' : '来自源' }
            });
        }

        // Canvas info
        const canvasInfo = card.createEl('div', {
            cls: 'association-canvas-info'
        });

        const canvasLink = canvasInfo.createEl('a', {
            text: linkedCanvasName,
            cls: 'association-canvas-link'
        });
        canvasLink.addEventListener('click', async (e) => {
            e.preventDefault();
            if (this.onNavigate) {
                await this.onNavigate(linkedCanvas);
                this.close();
            }
        });

        // Relevance score (if available)
        if (association.relevance_score !== undefined) {
            const scorePercent = Math.round(association.relevance_score * 100);
            canvasInfo.createEl('span', {
                text: `${scorePercent}% 相关`,
                cls: 'association-relevance'
            });
        }

        // Shared concepts
        if (association.shared_concepts && association.shared_concepts.length > 0) {
            const conceptsContainer = card.createEl('div', {
                cls: 'association-concepts'
            });

            for (const concept of association.shared_concepts.slice(0, 3)) {
                conceptsContainer.createEl('span', {
                    text: concept,
                    cls: 'association-concept-tag'
                });
            }

            if (association.shared_concepts.length > 3) {
                conceptsContainer.createEl('span', {
                    text: `+${association.shared_concepts.length - 3} 更多`,
                    cls: 'association-concept-more'
                });
            }
        }

        // Description (if available)
        if (association.description) {
            card.createEl('div', {
                text: association.description,
                cls: 'association-description'
            });
        }

        // Actions
        const actionsContainer = card.createEl('div', {
            cls: 'association-actions'
        });

        // Navigate button
        const navBtn = actionsContainer.createEl('button', {
            text: '打开',
            cls: 'association-action-btn'
        });
        navBtn.addEventListener('click', async () => {
            if (this.onNavigate) {
                await this.onNavigate(linkedCanvas);
                this.close();
            }
        });

        // Menu button (edit/delete)
        const menuBtn = actionsContainer.createEl('button', {
            text: '⋮',
            cls: 'association-action-btn association-menu-btn'
        });
        menuBtn.addEventListener('click', (e) => {
            this.showCardMenu(e, association);
        });

        // Auto-generated indicator
        if (association.auto_generated) {
            card.createEl('span', {
                text: '🤖 自动生成',
                cls: 'association-auto-badge'
            });
        }

        // Timestamps
        if (association.created_at) {
            const date = new Date(association.created_at);
            card.createEl('span', {
                text: date.toLocaleDateString('zh-CN'),
                cls: 'association-date'
            });
        }
    }

    /**
     * Show context menu for association card
     * ✅ Verified from @obsidian-canvas Skill (Menu API)
     */
    private showCardMenu(event: MouseEvent, association: CanvasAssociation): void {
        const menu = new Menu();

        menu.addItem((item) => {
            item.setTitle('编辑关联')
                .setIcon('pencil')
                .onClick(() => {
                    // TODO: Open edit modal
                    new Notice('编辑功能开发中');
                });
        });

        menu.addItem((item) => {
            item.setTitle('复制Canvas路径')
                .setIcon('copy')
                .onClick(() => {
                    const isSource = association.source_canvas === this.currentCanvasPath;
                    const linkedCanvas = isSource ? association.target_canvas : association.source_canvas;
                    navigator.clipboard.writeText(linkedCanvas);
                    new Notice('已复制路径');
                });
        });

        menu.addSeparator();

        menu.addItem((item) => {
            item.setTitle('删除关联')
                .setIcon('trash')
                .onClick(async () => {
                    await this.deleteAssociation(association);
                });
        });

        menu.showAtMouseEvent(event);
    }

    /**
     * Render modal footer
     */
    private renderFooter(container: HTMLElement): void {
        const footer = container.createEl('div', {
            cls: 'association-modal-footer'
        });

        // Statistics
        const stats = footer.createEl('div', {
            cls: 'association-stats'
        });

        stats.createEl('span', {
            text: `共 ${this.associations.length} 个关联`
        });

        // Type breakdown
        const typeBreakdown = this.getTypeBreakdown();
        for (const [type, count] of Object.entries(typeBreakdown)) {
            if (count > 0) {
                const config = CanvasAssociationModal.TYPE_CONFIG[type as AssociationType];
                stats.createEl('span', {
                    text: `${config.icon} ${count}`,
                    cls: 'association-stat-item'
                });
            }
        }

        // Action buttons
        const actionsContainer = footer.createEl('div', {
            cls: 'association-footer-actions'
        });

        const closeBtn = actionsContainer.createEl('button', {
            text: '关闭',
            cls: 'association-close-btn'
        });
        closeBtn.addEventListener('click', () => {
            this.close();
        });
    }

    // ========== Helper Methods ==========

    /**
     * Get filtered and sorted associations
     */
    private getFilteredAssociations(): CanvasAssociation[] {
        let filtered = [...this.associations];

        // Filter by types
        if (this.filter.types.length > 0) {
            filtered = filtered.filter(a => this.filter.types.includes(a.association_type));
        }

        // Filter by search query
        if (this.filter.searchQuery) {
            const query = this.filter.searchQuery.toLowerCase();
            filtered = filtered.filter(a => {
                const targetName = this.extractCanvasName(a.target_canvas).toLowerCase();
                const sourceName = this.extractCanvasName(a.source_canvas).toLowerCase();
                const concepts = (a.shared_concepts || []).join(' ').toLowerCase();
                const description = (a.description || '').toLowerCase();

                return targetName.includes(query) ||
                       sourceName.includes(query) ||
                       concepts.includes(query) ||
                       description.includes(query);
            });
        }

        // Sort
        switch (this.sortBy) {
            case 'date':
                filtered.sort((a, b) => {
                    const dateA = new Date(a.created_at || 0).getTime();
                    const dateB = new Date(b.created_at || 0).getTime();
                    return dateB - dateA;
                });
                break;
            case 'type':
                filtered.sort((a, b) => a.association_type.localeCompare(b.association_type));
                break;
            case 'relevance':
                filtered.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
                break;
        }

        return filtered;
    }

    /**
     * Get type breakdown statistics
     */
    private getTypeBreakdown(): Record<AssociationType, number> {
        const breakdown: Record<AssociationType, number> = {
            prerequisite: 0,
            related: 0,
            extends: 0,
            references: 0
        };

        for (const association of this.associations) {
            breakdown[association.association_type]++;
        }

        return breakdown;
    }

    /**
     * Extract canvas name from path
     */
    private extractCanvasName(path: string): string {
        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.canvas', '');
    }

    /**
     * Delete an association
     */
    private async deleteAssociation(association: CanvasAssociation): Promise<void> {
        // Confirm deletion
        const confirmed = confirm(`确定要删除与"${this.extractCanvasName(
            association.source_canvas === this.currentCanvasPath
                ? association.target_canvas
                : association.source_canvas
        )}"的关联吗？`);

        if (!confirmed) return;

        // Remove from list
        this.associations = this.associations.filter(
            a => a.association_id !== association.association_id
        );

        // Save changes
        if (this.onSave) {
            await this.onSave(this.associations);
        }

        new Notice('关联已删除');
        this.refresh();
    }

    /**
     * Refresh the list portion of the modal
     */
    private refreshList(container: HTMLElement): void {
        const parentEl = container.closest('.canvas-association-modal') || this.contentEl;
        this.renderAssociationList(parentEl as HTMLElement);

        // Update filter chip states
        const chips = parentEl.querySelectorAll('.association-filter-chip');
        chips.forEach((chip, index) => {
            const types = Object.keys(CanvasAssociationModal.TYPE_CONFIG);
            const type = types[index] as AssociationType;
            if (this.filter.types.includes(type)) {
                chip.addClass('active');
            } else {
                chip.removeClass('active');
            }
        });
    }

    /**
     * Refresh the entire modal
     */
    private refresh(): void {
        this.onClose();
        this.onOpen();
    }
}
