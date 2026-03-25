/**
 * Association Form Modal - Canvas Learning System Cross-Canvas Associations
 *
 * Modal form for creating and editing Canvas associations.
 * Implements Story 16.1: Canvas关联UI (Task 3: 创建关联编辑模态框)
 *
 * @module modals/AssociationFormModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API, Setting API)
 * ✅ Verified from Story 16.1 Dev Notes (Modal design, form fields)
 */

import { App, Modal, Notice, Setting, TFile, FuzzySuggestModal } from 'obsidian';
import type {
    CanvasAssociation,
    AssociationType,
    NodeAssociation
} from '../types/AssociationTypes';
import { DEFAULT_ASSOCIATION, ASSOCIATION_TYPE_CONFIG } from '../types/AssociationTypes';

/**
 * Form data for creating/editing an association
 */
interface AssociationFormData {
    targetCanvas: string;
    associationType: AssociationType;
    bidirectional: boolean;
    description: string;
    sharedConcepts: string[];
    relevanceScore: number;
}

/**
 * Canvas Suggester Modal
 * Provides fuzzy search for Canvas files in vault
 *
 * ✅ Verified from @obsidian-canvas Skill (FuzzySuggestModal pattern)
 */
class CanvasSuggesterModal extends FuzzySuggestModal<TFile> {
    private canvasFiles: TFile[];
    private onChoose: (file: TFile) => void;

    constructor(app: App, canvasFiles: TFile[], onChoose: (file: TFile) => void) {
        super(app);
        this.canvasFiles = canvasFiles;
        this.onChoose = onChoose;
        this.setPlaceholder('搜索Canvas文件...');
    }

    getItems(): TFile[] {
        return this.canvasFiles;
    }

    getItemText(item: TFile): string {
        return item.path;
    }

    onChooseItem(item: TFile, evt: MouseEvent | KeyboardEvent): void {
        this.onChoose(item);
    }
}

/**
 * Association Form Modal
 *
 * Provides a form for creating or editing Canvas associations.
 * Supports Canvas file selection via fuzzy search.
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class, Setting API)
 */
export class AssociationFormModal extends Modal {
    private sourceCanvasPath: string;
    private existingAssociation: CanvasAssociation | null;
    private formData: AssociationFormData;
    private onSubmit: (association: CanvasAssociation) => Promise<void>;
    private conceptInput: HTMLInputElement | null = null;

    /**
     * Creates a new AssociationFormModal
     *
     * @param app - Obsidian App instance
     * @param sourceCanvasPath - Path of the source Canvas file
     * @param existingAssociation - Existing association for editing (null for new)
     * @param onSubmit - Callback when form is submitted
     */
    constructor(
        app: App,
        sourceCanvasPath: string,
        existingAssociation: CanvasAssociation | null,
        onSubmit: (association: CanvasAssociation) => Promise<void>
    ) {
        super(app);
        this.sourceCanvasPath = sourceCanvasPath;
        this.existingAssociation = existingAssociation;
        this.onSubmit = onSubmit;

        // Initialize form data from existing or defaults
        this.formData = existingAssociation
            ? {
                targetCanvas: existingAssociation.target_canvas,
                associationType: existingAssociation.association_type,
                bidirectional: existingAssociation.bidirectional ?? false,
                description: existingAssociation.description ?? '',
                sharedConcepts: existingAssociation.shared_concepts ?? [],
                relevanceScore: existingAssociation.relevance_score ?? 0.5
            }
            : {
                targetCanvas: '',
                associationType: 'related',
                bidirectional: false,
                description: '',
                sharedConcepts: [],
                relevanceScore: 0.5
            };
    }

    /**
     * Called when modal is opened
     * ✅ Verified from @obsidian-canvas Skill (Modal.onOpen)
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('canvas-association-form-modal');

        // Header
        this.renderHeader(contentEl);

        // Form container
        const formContainer = contentEl.createDiv({ cls: 'association-form-container' });

        // Form fields
        this.renderTargetCanvasField(formContainer);
        this.renderTypeField(formContainer);
        this.renderBidirectionalField(formContainer);
        this.renderDescriptionField(formContainer);
        this.renderSharedConceptsField(formContainer);
        this.renderRelevanceScoreField(formContainer);

        // Actions
        this.renderActions(contentEl);
    }

    /**
     * Called when modal is closed
     * ✅ Verified from @obsidian-canvas Skill (Modal.onClose)
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Render modal header
     */
    private renderHeader(container: HTMLElement): void {
        const header = container.createDiv({ cls: 'association-form-header' });
        header.createEl('h2', {
            text: this.existingAssociation ? '编辑Canvas关联' : '创建Canvas关联'
        });

        const sourceInfo = header.createDiv({ cls: 'source-canvas-info' });
        sourceInfo.createSpan({ text: '来源: ' });
        sourceInfo.createSpan({
            text: this.getCanvasDisplayName(this.sourceCanvasPath),
            cls: 'source-canvas-name'
        });
    }

    /**
     * Render target Canvas selection field
     * ✅ Verified from @obsidian-canvas Skill (Setting API, FuzzySuggestModal)
     */
    private renderTargetCanvasField(container: HTMLElement): void {
        new Setting(container)
            .setName('目标Canvas')
            .setDesc('选择要关联的Canvas文件')
            .addButton(button => button
                .setButtonText(this.formData.targetCanvas
                    ? this.getCanvasDisplayName(this.formData.targetCanvas)
                    : '选择Canvas...'
                )
                .onClick(() => {
                    this.openCanvasSuggester((file) => {
                        this.formData.targetCanvas = file.path;
                        button.setButtonText(this.getCanvasDisplayName(file.path));
                    });
                })
            );
    }

    /**
     * Render association type dropdown
     * ✅ Verified from @obsidian-canvas Skill (Setting.addDropdown)
     */
    private renderTypeField(container: HTMLElement): void {
        new Setting(container)
            .setName('关联类型')
            .setDesc('选择关联的类型')
            .addDropdown(dropdown => {
                // Add options from ASSOCIATION_TYPE_CONFIG
                const types: AssociationType[] = ['prerequisite', 'related', 'extends', 'references'];
                types.forEach(type => {
                    const config = ASSOCIATION_TYPE_CONFIG[type];
                    dropdown.addOption(type, `${config.icon} ${config.label}`);
                });

                dropdown.setValue(this.formData.associationType);
                dropdown.onChange((value) => {
                    this.formData.associationType = value as AssociationType;
                });
            });
    }

    /**
     * Render bidirectional toggle
     * ✅ Verified from @obsidian-canvas Skill (Setting.addToggle)
     */
    private renderBidirectionalField(container: HTMLElement): void {
        new Setting(container)
            .setName('双向关联')
            .setDesc('是否创建双向关联（A→B 和 B→A）')
            .addToggle(toggle => toggle
                .setValue(this.formData.bidirectional)
                .onChange((value) => {
                    this.formData.bidirectional = value;
                })
            );
    }

    /**
     * Render description text area
     * ✅ Verified from @obsidian-canvas Skill (Setting.addTextArea)
     */
    private renderDescriptionField(container: HTMLElement): void {
        new Setting(container)
            .setName('描述')
            .setDesc('可选的关联描述')
            .addTextArea(textArea => {
                textArea
                    .setPlaceholder('输入关联描述...')
                    .setValue(this.formData.description)
                    .onChange((value) => {
                        this.formData.description = value;
                    });
                textArea.inputEl.rows = 3;
            });
    }

    /**
     * Render shared concepts input with tags
     */
    private renderSharedConceptsField(container: HTMLElement): void {
        const setting = new Setting(container)
            .setName('共享概念')
            .setDesc('添加两个Canvas共同涉及的概念（按Enter添加）');

        // Tags container
        const tagsContainer = setting.settingEl.createDiv({ cls: 'shared-concepts-tags' });
        this.renderConceptTags(tagsContainer);

        // Input field
        setting.addText(text => {
            this.conceptInput = text.inputEl;
            text.setPlaceholder('输入概念名称...');
            text.inputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const value = text.getValue().trim();
                    if (value && !this.formData.sharedConcepts.includes(value)) {
                        this.formData.sharedConcepts.push(value);
                        this.renderConceptTags(tagsContainer);
                        text.setValue('');
                    }
                }
            });
        });
    }

    /**
     * Render concept tags
     */
    private renderConceptTags(container: HTMLElement): void {
        container.empty();
        this.formData.sharedConcepts.forEach((concept, index) => {
            const tag = container.createDiv({ cls: 'concept-tag' });
            tag.createSpan({ text: concept });
            const removeBtn = tag.createSpan({ text: '×', cls: 'concept-tag-remove' });
            removeBtn.addEventListener('click', () => {
                this.formData.sharedConcepts.splice(index, 1);
                this.renderConceptTags(container);
            });
        });
    }

    /**
     * Render relevance score slider
     * ✅ Verified from @obsidian-canvas Skill (Setting.addSlider)
     */
    private renderRelevanceScoreField(container: HTMLElement): void {
        new Setting(container)
            .setName('相关度评分')
            .setDesc(`当前: ${Math.round(this.formData.relevanceScore * 100)}%`)
            .addSlider(slider => slider
                .setLimits(0, 1, 0.1)
                .setValue(this.formData.relevanceScore)
                .setDynamicTooltip()
                .onChange((value) => {
                    this.formData.relevanceScore = value;
                    // Update description text
                    const descEl = slider.sliderEl.parentElement?.previousElementSibling;
                    if (descEl) {
                        descEl.textContent = `当前: ${Math.round(value * 100)}%`;
                    }
                })
            );
    }

    /**
     * Render form actions (Cancel / Submit)
     */
    private renderActions(container: HTMLElement): void {
        const actions = container.createDiv({ cls: 'association-form-actions' });

        // Cancel button
        const cancelBtn = actions.createEl('button', {
            text: '取消',
            cls: 'association-form-cancel'
        });
        cancelBtn.addEventListener('click', () => {
            this.close();
        });

        // Submit button
        const submitBtn = actions.createEl('button', {
            text: this.existingAssociation ? '保存' : '创建',
            cls: 'association-form-submit mod-cta'
        });
        submitBtn.addEventListener('click', async () => {
            await this.handleSubmit();
        });
    }

    /**
     * Handle form submission
     */
    private async handleSubmit(): Promise<void> {
        // Validate
        if (!this.formData.targetCanvas) {
            new Notice('请选择目标Canvas');
            return;
        }

        if (this.formData.targetCanvas === this.sourceCanvasPath) {
            new Notice('不能关联到自身');
            return;
        }

        // Build association object
        const association: CanvasAssociation = {
            association_id: this.existingAssociation?.association_id ?? this.generateUUID(),
            source_canvas: this.sourceCanvasPath,
            target_canvas: this.formData.targetCanvas,
            association_type: this.formData.associationType,
            bidirectional: this.formData.bidirectional,
            description: this.formData.description || undefined,
            shared_concepts: this.formData.sharedConcepts.length > 0
                ? this.formData.sharedConcepts
                : undefined,
            relevance_score: this.formData.relevanceScore,
            auto_generated: false,
            created_at: this.existingAssociation?.created_at ?? new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        try {
            await this.onSubmit(association);
            new Notice(this.existingAssociation ? '关联已更新' : '关联已创建');
            this.close();
        } catch (error) {
            console.error('[AssociationFormModal] Submit error:', error);
            new Notice('保存失败: ' + (error as Error).message);
        }
    }

    /**
     * Open Canvas file suggester
     * ✅ Verified from @obsidian-canvas Skill (Vault.getFiles)
     */
    private openCanvasSuggester(onChoose: (file: TFile) => void): void {
        // Get all .canvas files from vault
        const canvasFiles = this.app.vault.getFiles()
            .filter(f => f.extension === 'canvas')
            .filter(f => f.path !== this.sourceCanvasPath); // Exclude current

        new CanvasSuggesterModal(this.app, canvasFiles, onChoose).open();
    }

    /**
     * Get display name from Canvas path
     */
    private getCanvasDisplayName(path: string): string {
        const name = path.split('/').pop() || path;
        return name.replace('.canvas', '');
    }

    /**
     * Generate UUID v4
     */
    private generateUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}
