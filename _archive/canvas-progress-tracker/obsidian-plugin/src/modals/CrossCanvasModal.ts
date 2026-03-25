/**
 * Cross-Canvas Modal - Canvas Learning System
 *
 * Modal for creating and managing cross-Canvas associations.
 * Implements Story 25.1: Cross-Canvas UI Entry Points (AC: 1, 3)
 *
 * @module modals/CrossCanvasModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 25.1 Dev Notes (Modal design)
 */

import { App, Modal, Notice, TFile, Setting, FuzzySuggestModal } from 'obsidian';
import type {
    CanvasRelationshipType,
    CrossCanvasAssociation,
} from '../types/UITypes';
import type { CrossCanvasService, CanvasAssociationSuggestion } from '../services/CrossCanvasService';

/**
 * Extended relationship types (now unified with base type per Story 25.3)
 * Kept for backward compatibility with existing code
 * [Source: Story 25.3 - Exercise-Lecture Canvas Association]
 */
export type ExtendedRelationshipType = CanvasRelationshipType;

/**
 * Association type configuration for display
 * ✅ Verified from Story 25.1 Dev Notes (ASSOCIATION_TYPE_CONFIG)
 */
const RELATIONSHIP_TYPE_CONFIG: Record<ExtendedRelationshipType, {
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
    application: {
        label: '应用场景',
        icon: '🎯',
        description: '知识的实际应用场景',
        color: '#2ecc71'
    },
    exercise_lecture: {
        label: '题目-讲座',
        icon: '📝',
        description: '练习题目关联到讲座Canvas',
        color: '#9b59b6'
    },
    exercise_solution: {
        label: '题目-解答',
        icon: '✅',
        description: '练习题目关联到解答Canvas',
        color: '#f39c12'
    }
};

/**
 * Form data for creating association
 */
interface AssociationFormData {
    targetCanvasPath: string;
    targetCanvasTitle: string;
    relationshipType: ExtendedRelationshipType;
    bidirectional: boolean;
    confidence: number;
    description: string;
}

/**
 * Canvas file suggestion for fuzzy search
 */
interface CanvasFileSuggestion {
    file: TFile;
    displayName: string;
}

/**
 * Fuzzy search modal for Canvas files
 * ✅ Verified from @obsidian-canvas Skill (FuzzySuggestModal API)
 */
class CanvasFileSuggestModal extends FuzzySuggestModal<CanvasFileSuggestion> {
    private canvasFiles: CanvasFileSuggestion[];
    private onSelect: (file: TFile) => void;

    constructor(app: App, canvasFiles: TFile[], onSelect: (file: TFile) => void) {
        super(app);
        this.canvasFiles = canvasFiles.map(file => ({
            file,
            displayName: file.basename
        }));
        this.onSelect = onSelect;
        this.setPlaceholder('搜索Canvas文件...');
    }

    getItems(): CanvasFileSuggestion[] {
        return this.canvasFiles;
    }

    getItemText(item: CanvasFileSuggestion): string {
        return item.displayName;
    }

    onChooseItem(item: CanvasFileSuggestion): void {
        this.onSelect(item.file);
    }
}

/**
 * Cross-Canvas Modal
 *
 * Provides a UI for creating cross-Canvas associations.
 * Supports Canvas file selection with fuzzy search, relationship type selection,
 * bidirectional toggle, and confidence scoring.
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class CrossCanvasModal extends Modal {
    private sourceCanvasPath: string;
    private sourceCanvasTitle: string;
    private crossCanvasService: CrossCanvasService | null;
    private onAssociationCreated: ((association: CrossCanvasAssociation) => void) | null;

    // Form state
    private formData: AssociationFormData = {
        targetCanvasPath: '',
        targetCanvasTitle: '',
        relationshipType: 'related',
        bidirectional: false,
        confidence: 0.5,
        description: ''
    };

    // UI elements for dynamic updates
    private targetDisplayEl: HTMLElement | null = null;
    private createButtonEl: HTMLButtonElement | null = null;
    private suggestionsContainerEl: HTMLElement | null = null;

    // Suggestions state (Story 25.3 AC5)
    private suggestions: CanvasAssociationSuggestion[] = [];
    private loadingSuggestions: boolean = false;

    /**
     * Creates a new CrossCanvasModal
     *
     * @param app - Obsidian App instance
     * @param sourceCanvasPath - Path of the source Canvas file
     * @param crossCanvasService - Service for managing cross-canvas associations
     * @param onAssociationCreated - Callback when association is created
     */
    constructor(
        app: App,
        sourceCanvasPath: string,
        crossCanvasService?: CrossCanvasService | null,
        onAssociationCreated?: (association: CrossCanvasAssociation) => void
    ) {
        super(app);
        this.sourceCanvasPath = sourceCanvasPath;
        this.sourceCanvasTitle = this.extractCanvasName(sourceCanvasPath);
        this.crossCanvasService = crossCanvasService || null;
        this.onAssociationCreated = onAssociationCreated || null;
    }

    /**
     * Called when the modal is opened
     * ✅ Verified from @obsidian-canvas Skill (Modal lifecycle)
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('cross-canvas-modal');

        // Header
        this.renderHeader(contentEl);

        // Source Canvas info
        this.renderSourceInfo(contentEl);

        // Target Canvas selector
        this.renderTargetSelector(contentEl);

        // Story 25.3 AC5: Intelligent suggestions section
        this.renderSuggestionsSection(contentEl);

        // Relationship type selector
        this.renderRelationshipTypeSelector(contentEl);

        // Options (bidirectional, confidence)
        this.renderOptions(contentEl);

        // Description
        this.renderDescription(contentEl);

        // Action buttons
        this.renderActions(contentEl);
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
            cls: 'cross-canvas-modal-header'
        });

        header.createEl('h2', {
            text: '🔗 创建Canvas关联',
            cls: 'cross-canvas-modal-title'
        });

        header.createEl('p', {
            text: '创建与其他Canvas的语义关联，用于知识迁移和上下文增强',
            cls: 'cross-canvas-modal-subtitle'
        });
    }

    /**
     * Render source canvas info
     */
    private renderSourceInfo(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section'
        });

        section.createEl('h4', { text: '源Canvas' });

        const sourceInfo = section.createEl('div', {
            cls: 'cross-canvas-source-info'
        });

        sourceInfo.createEl('span', {
            text: '📄',
            cls: 'cross-canvas-icon'
        });

        sourceInfo.createEl('span', {
            text: this.sourceCanvasTitle,
            cls: 'cross-canvas-source-name'
        });

        sourceInfo.createEl('span', {
            text: `(${this.sourceCanvasPath})`,
            cls: 'cross-canvas-source-path'
        });
    }

    /**
     * Render target canvas selector with fuzzy search
     * ✅ Verified from Story 25.1 Dev Notes (Task 2.2)
     */
    private renderTargetSelector(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section'
        });

        section.createEl('h4', { text: '目标Canvas' });

        const selectorContainer = section.createEl('div', {
            cls: 'cross-canvas-target-selector'
        });

        // Display selected target
        this.targetDisplayEl = selectorContainer.createEl('div', {
            cls: 'cross-canvas-target-display'
        });
        this.updateTargetDisplay();

        // Select button
        const selectBtn = selectorContainer.createEl('button', {
            text: '选择Canvas',
            cls: 'cross-canvas-select-btn'
        });

        selectBtn.addEventListener('click', async () => {
            await this.openCanvasSelector();
        });
    }

    /**
     * Update target display element
     */
    private updateTargetDisplay(): void {
        if (!this.targetDisplayEl) return;

        this.targetDisplayEl.empty();

        if (this.formData.targetCanvasPath) {
            this.targetDisplayEl.createEl('span', {
                text: '📄',
                cls: 'cross-canvas-icon'
            });
            this.targetDisplayEl.createEl('span', {
                text: this.formData.targetCanvasTitle,
                cls: 'cross-canvas-target-name'
            });
            this.targetDisplayEl.removeClass('empty');
        } else {
            this.targetDisplayEl.createEl('span', {
                text: '请选择目标Canvas...',
                cls: 'cross-canvas-target-placeholder'
            });
            this.targetDisplayEl.addClass('empty');
        }

        this.updateCreateButtonState();
    }

    /**
     * Open Canvas file selector with fuzzy search
     */
    private async openCanvasSelector(): Promise<void> {
        // Get all canvas files
        const files = this.app.vault.getFiles();
        const canvasFiles = files.filter(
            file => file.extension === 'canvas' && file.path !== this.sourceCanvasPath
        );

        if (canvasFiles.length === 0) {
            new Notice('未找到其他Canvas文件');
            return;
        }

        // Open fuzzy search modal
        const modal = new CanvasFileSuggestModal(
            this.app,
            canvasFiles,
            (selectedFile: TFile) => {
                this.formData.targetCanvasPath = selectedFile.path;
                this.formData.targetCanvasTitle = selectedFile.basename;
                this.updateTargetDisplay();
            }
        );

        modal.open();
    }

    /**
     * Render intelligent suggestions section
     * [Source: Story 25.3 AC5 - Batch association suggestions]
     */
    private renderSuggestionsSection(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section cross-canvas-suggestions-section'
        });

        const headerRow = section.createEl('div', {
            cls: 'cross-canvas-suggestions-header'
        });

        headerRow.createEl('h4', { text: '💡 智能关联建议' });

        // Suggestion button
        const suggestBtn = headerRow.createEl('button', {
            text: '获取建议',
            cls: 'cross-canvas-suggest-btn'
        });

        suggestBtn.addEventListener('click', async () => {
            await this.loadSuggestions();
        });

        // Container for suggestions list
        this.suggestionsContainerEl = section.createEl('div', {
            cls: 'cross-canvas-suggestions-list'
        });

        // Initial message
        this.suggestionsContainerEl.createEl('p', {
            text: '点击"获取建议"按钮，系统将根据Canvas内容智能推荐关联',
            cls: 'cross-canvas-suggestions-placeholder'
        });
    }

    /**
     * Load suggestions from CrossCanvasService
     * [Source: Story 25.3 AC5 - Batch association suggestions]
     */
    private async loadSuggestions(): Promise<void> {
        if (!this.crossCanvasService) {
            new Notice('CrossCanvasService 未初始化');
            return;
        }

        if (this.loadingSuggestions) return;

        this.loadingSuggestions = true;
        this.updateSuggestionsDisplay('loading');

        try {
            this.suggestions = await this.crossCanvasService.getSuggestions(
                this.sourceCanvasPath
            );

            if (this.suggestions.length === 0) {
                this.updateSuggestionsDisplay('empty');
            } else {
                this.updateSuggestionsDisplay('loaded');
            }
        } catch (error) {
            console.error('[CrossCanvasModal] Failed to load suggestions:', error);
            new Notice('获取建议失败');
            this.updateSuggestionsDisplay('error');
        } finally {
            this.loadingSuggestions = false;
        }
    }

    /**
     * Update suggestions display based on state
     */
    private updateSuggestionsDisplay(state: 'loading' | 'empty' | 'loaded' | 'error'): void {
        if (!this.suggestionsContainerEl) return;

        this.suggestionsContainerEl.empty();

        switch (state) {
            case 'loading':
                this.suggestionsContainerEl.createEl('p', {
                    text: '⏳ 正在分析Canvas内容，请稍候...',
                    cls: 'cross-canvas-suggestions-loading'
                });
                break;

            case 'empty':
                this.suggestionsContainerEl.createEl('p', {
                    text: '未找到合适的关联建议。您可以手动选择目标Canvas。',
                    cls: 'cross-canvas-suggestions-empty'
                });
                break;

            case 'error':
                this.suggestionsContainerEl.createEl('p', {
                    text: '❌ 获取建议时出错，请重试或手动选择。',
                    cls: 'cross-canvas-suggestions-error'
                });
                break;

            case 'loaded':
                this.renderSuggestionsList();
                break;
        }
    }

    /**
     * Render the list of suggestions with accept/reject buttons
     * [Source: Story 25.3 AC5 - Display suggested associations with accept/reject buttons]
     */
    private renderSuggestionsList(): void {
        if (!this.suggestionsContainerEl) return;

        this.suggestionsContainerEl.empty();

        for (const suggestion of this.suggestions) {
            const item = this.suggestionsContainerEl.createEl('div', {
                cls: 'cross-canvas-suggestion-item'
            });

            // Left: suggestion info
            const infoDiv = item.createEl('div', {
                cls: 'cross-canvas-suggestion-info'
            });

            // Title row
            const titleRow = infoDiv.createEl('div', {
                cls: 'cross-canvas-suggestion-title-row'
            });

            const config = RELATIONSHIP_TYPE_CONFIG[suggestion.relation_type];
            titleRow.createEl('span', {
                text: config?.icon || '📄',
                cls: 'cross-canvas-suggestion-icon'
            });

            titleRow.createEl('span', {
                text: suggestion.target_canvas_title,
                cls: 'cross-canvas-suggestion-title'
            });

            // Confidence badge
            const confidencePercent = Math.round(suggestion.confidence * 100);
            const confidenceBadge = titleRow.createEl('span', {
                text: `${confidencePercent}%`,
                cls: `cross-canvas-suggestion-confidence ${this.getConfidenceClass(suggestion.confidence)}`
            });
            confidenceBadge.title = '置信度';

            // Reason
            infoDiv.createEl('div', {
                text: suggestion.reason,
                cls: 'cross-canvas-suggestion-reason'
            });

            // Common concepts
            if (suggestion.common_concepts && suggestion.common_concepts.length > 0) {
                const conceptsDiv = infoDiv.createEl('div', {
                    cls: 'cross-canvas-suggestion-concepts'
                });
                conceptsDiv.createEl('span', { text: '共同概念: ' });
                conceptsDiv.createEl('span', {
                    text: suggestion.common_concepts.slice(0, 3).join(', '),
                    cls: 'cross-canvas-concept-list'
                });
            }

            // Right: action buttons
            const actionsDiv = item.createEl('div', {
                cls: 'cross-canvas-suggestion-actions'
            });

            // Accept button
            const acceptBtn = actionsDiv.createEl('button', {
                text: '✓ 采用',
                cls: 'cross-canvas-accept-btn mod-cta'
            });

            acceptBtn.addEventListener('click', () => {
                this.acceptSuggestion(suggestion);
            });

            // Reject button
            const rejectBtn = actionsDiv.createEl('button', {
                text: '✗',
                cls: 'cross-canvas-reject-btn'
            });
            rejectBtn.title = '忽略此建议';

            rejectBtn.addEventListener('click', () => {
                this.rejectSuggestion(suggestion, item);
            });
        }
    }

    /**
     * Get CSS class for confidence level
     */
    private getConfidenceClass(confidence: number): string {
        if (confidence >= 0.7) return 'confidence-high';
        if (confidence >= 0.4) return 'confidence-medium';
        return 'confidence-low';
    }

    /**
     * Accept a suggestion and fill the form
     * [Source: Story 25.3 AC5 - Accept suggested association]
     */
    private acceptSuggestion(suggestion: CanvasAssociationSuggestion): void {
        this.formData.targetCanvasPath = suggestion.target_canvas_path;
        this.formData.targetCanvasTitle = suggestion.target_canvas_title;
        this.formData.relationshipType = suggestion.relation_type;
        this.formData.confidence = suggestion.confidence;

        // Update UI
        this.updateTargetDisplay();

        // Refresh relationship type buttons to show selected type
        const typesContainer = this.contentEl.querySelector('.cross-canvas-types-container');
        if (typesContainer) {
            this.refreshRelationshipTypeButtons(typesContainer as HTMLElement);
        }

        // Update confidence slider
        const slider = this.contentEl.querySelector('.cross-canvas-confidence-slider') as HTMLInputElement;
        const valueDisplay = this.contentEl.querySelector('.cross-canvas-confidence-value');
        if (slider && valueDisplay) {
            slider.value = String(Math.round(suggestion.confidence * 100));
            valueDisplay.textContent = `${Math.round(suggestion.confidence * 100)}%`;
        }

        new Notice(`✓ 已选择 "${suggestion.target_canvas_title}"`);
    }

    /**
     * Reject a suggestion and remove from list
     */
    private rejectSuggestion(suggestion: CanvasAssociationSuggestion, itemEl: HTMLElement): void {
        // Remove from suggestions array
        this.suggestions = this.suggestions.filter(s => s !== suggestion);

        // Animate removal
        itemEl.addClass('removing');
        setTimeout(() => {
            itemEl.remove();

            // Check if list is now empty
            if (this.suggestions.length === 0) {
                this.updateSuggestionsDisplay('empty');
            }
        }, 200);
    }

    /**
     * Render relationship type selector
     * ✅ Verified from Story 25.1 Dev Notes (Task 2.3)
     */
    private renderRelationshipTypeSelector(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section'
        });

        section.createEl('h4', { text: '关联类型' });

        const typesContainer = section.createEl('div', {
            cls: 'cross-canvas-types-container'
        });

        for (const [type, config] of Object.entries(RELATIONSHIP_TYPE_CONFIG)) {
            const typeBtn = typesContainer.createEl('button', {
                cls: `cross-canvas-type-btn ${this.formData.relationshipType === type ? 'active' : ''}`
            });

            typeBtn.createEl('span', {
                text: config.icon,
                cls: 'cross-canvas-type-icon'
            });

            typeBtn.createEl('span', {
                text: config.label,
                cls: 'cross-canvas-type-label'
            });

            typeBtn.style.borderColor = config.color;

            if (this.formData.relationshipType === type) {
                typeBtn.style.backgroundColor = `${config.color}20`;
            }

            typeBtn.addEventListener('click', () => {
                this.formData.relationshipType = type as ExtendedRelationshipType;
                this.refreshRelationshipTypeButtons(typesContainer);
            });

            // Tooltip with description
            typeBtn.title = config.description;
        }
    }

    /**
     * Refresh relationship type button states
     */
    private refreshRelationshipTypeButtons(container: HTMLElement): void {
        const buttons = container.querySelectorAll('.cross-canvas-type-btn');
        const types = Object.keys(RELATIONSHIP_TYPE_CONFIG) as ExtendedRelationshipType[];

        buttons.forEach((btn, index) => {
            const type = types[index];
            const config = RELATIONSHIP_TYPE_CONFIG[type];

            if (this.formData.relationshipType === type) {
                btn.addClass('active');
                (btn as HTMLElement).style.backgroundColor = `${config.color}20`;
            } else {
                btn.removeClass('active');
                (btn as HTMLElement).style.backgroundColor = '';
            }
        });
    }

    /**
     * Render options (bidirectional toggle, confidence slider)
     * ✅ Verified from Story 25.1 Dev Notes (Task 2.4)
     */
    private renderOptions(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section'
        });

        section.createEl('h4', { text: '选项' });

        const optionsContainer = section.createEl('div', {
            cls: 'cross-canvas-options'
        });

        // Bidirectional toggle
        new Setting(optionsContainer)
            .setName('双向关联')
            .setDesc('创建双向关联（A↔B而非A→B）')
            .addToggle(toggle => {
                toggle
                    .setValue(this.formData.bidirectional)
                    .onChange(value => {
                        this.formData.bidirectional = value;
                    });
            });

        // Confidence slider
        const confidenceContainer = optionsContainer.createEl('div', {
            cls: 'cross-canvas-confidence-container'
        });

        const confidenceLabel = confidenceContainer.createEl('div', {
            cls: 'cross-canvas-confidence-label'
        });

        confidenceLabel.createEl('span', { text: '置信度' });
        const confidenceValue = confidenceLabel.createEl('span', {
            text: `${Math.round(this.formData.confidence * 100)}%`,
            cls: 'cross-canvas-confidence-value'
        });

        const confidenceSlider = confidenceContainer.createEl('input', {
            type: 'range',
            cls: 'cross-canvas-confidence-slider'
        });
        confidenceSlider.min = '0';
        confidenceSlider.max = '100';
        confidenceSlider.value = String(Math.round(this.formData.confidence * 100));

        confidenceSlider.addEventListener('input', (e) => {
            const value = parseInt((e.target as HTMLInputElement).value);
            this.formData.confidence = value / 100;
            confidenceValue.textContent = `${value}%`;
        });
    }

    /**
     * Render description textarea
     */
    private renderDescription(container: HTMLElement): void {
        const section = container.createEl('div', {
            cls: 'cross-canvas-section'
        });

        section.createEl('h4', { text: '备注（可选）' });

        const textarea = section.createEl('textarea', {
            cls: 'cross-canvas-description-input',
            placeholder: '描述这个关联的用途或原因...'
        });

        textarea.addEventListener('input', (e) => {
            this.formData.description = (e.target as HTMLTextAreaElement).value;
        });
    }

    /**
     * Render action buttons
     * ✅ Verified from Story 25.1 Dev Notes (Task 2.5)
     */
    private renderActions(container: HTMLElement): void {
        const actionsContainer = container.createEl('div', {
            cls: 'cross-canvas-actions'
        });

        // Cancel button
        const cancelBtn = actionsContainer.createEl('button', {
            text: '取消',
            cls: 'cross-canvas-cancel-btn'
        });

        cancelBtn.addEventListener('click', () => {
            this.close();
        });

        // Create button
        this.createButtonEl = actionsContainer.createEl('button', {
            text: '创建关联',
            cls: 'cross-canvas-create-btn mod-cta'
        });

        this.createButtonEl.addEventListener('click', async () => {
            await this.createAssociation();
        });

        this.updateCreateButtonState();
    }

    /**
     * Update create button enabled state
     */
    private updateCreateButtonState(): void {
        if (!this.createButtonEl) return;

        const isValid = this.formData.targetCanvasPath !== '';
        this.createButtonEl.disabled = !isValid;

        if (isValid) {
            this.createButtonEl.removeClass('disabled');
        } else {
            this.createButtonEl.addClass('disabled');
        }
    }

    /**
     * Create the association
     */
    private async createAssociation(): Promise<void> {
        if (!this.formData.targetCanvasPath) {
            new Notice('请选择目标Canvas');
            return;
        }

        if (!this.crossCanvasService) {
            new Notice('CrossCanvasService 未初始化');
            return;
        }

        try {
            // Map extended type to base type for service
            const baseType = this.mapToBaseRelationshipType(this.formData.relationshipType);

            // Create association via service
            const association = await this.crossCanvasService.createCanvasAssociation(
                this.sourceCanvasPath,
                this.formData.targetCanvasPath,
                baseType
            );

            // Notify success
            new Notice(`✅ 已创建与 "${this.formData.targetCanvasTitle}" 的关联`);

            // Call callback if provided
            if (this.onAssociationCreated) {
                this.onAssociationCreated(association);
            }

            this.close();

        } catch (error) {
            console.error('[CrossCanvasModal] Failed to create association:', error);
            new Notice(`❌ 创建关联失败: ${error instanceof Error ? error.message : '未知错误'}`);
        }
    }

    /**
     * Map extended relationship type to base type
     * [Source: Story 25.3 - Exercise-Lecture Canvas Association]
     * Now all extended types are part of base CanvasRelationshipType
     */
    private mapToBaseRelationshipType(extendedType: ExtendedRelationshipType): CanvasRelationshipType {
        // Story 25.3: All extended types are now supported in base type
        return extendedType as CanvasRelationshipType;
    }

    /**
     * Extract canvas name from path
     */
    private extractCanvasName(path: string): string {
        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.canvas', '');
    }
}

/**
 * Factory function to create CrossCanvasModal
 */
export function createCrossCanvasModal(
    app: App,
    sourceCanvasPath: string,
    crossCanvasService?: CrossCanvasService | null,
    onAssociationCreated?: (association: CrossCanvasAssociation) => void
): CrossCanvasModal {
    return new CrossCanvasModal(app, sourceCanvasPath, crossCanvasService, onAssociationCreated);
}
