/**
 * ReviewModeSelectionService - Canvas Learning System
 *
 * Story 14.15: 复习模式选择UI组件
 *
 * Provides UI components for review mode selection:
 * - Settings panel options (default review mode)
 * - Modal dialog (temporary override)
 * - Badge display (show mode in history)
 *
 * @module ReviewModeSelectionService
 * @version 1.0.0
 */

import { App, Modal, Setting, Notice } from 'obsidian';

/**
 * Review mode types
 */
export type ReviewMode = 'fresh' | 'targeted';

/**
 * Review mode metadata for display
 */
export interface ReviewModeInfo {
    mode: ReviewMode;
    label: string;
    description: string;
    icon: string;
    badgeColor: string;
}

/**
 * Review mode configuration
 */
export const REVIEW_MODES: Record<ReviewMode, ReviewModeInfo> = {
    fresh: {
        mode: 'fresh',
        label: '全新检验',
        description: '不使用历史数据，盲测式检验，测试真实记忆水平',
        icon: '🔄',
        badgeColor: '#4CAF50',
    },
    targeted: {
        mode: 'targeted',
        label: '针对性复习',
        description: '基于历史数据，聚焦薄弱概念（70%薄弱 + 30%已掌握）',
        icon: '🎯',
        badgeColor: '#2196F3',
    },
};

/**
 * Settings for review mode selection
 */
export interface ReviewModeSettings {
    defaultMode: ReviewMode;
    showModeSelectionOnStart: boolean;
    rememberLastMode: boolean;
    lastUsedMode: ReviewMode | null;
}

/**
 * Default settings
 */
export const DEFAULT_REVIEW_MODE_SETTINGS: ReviewModeSettings = {
    defaultMode: 'fresh',
    showModeSelectionOnStart: true,
    rememberLastMode: true,
    lastUsedMode: null,
};

/**
 * Modal selection result
 */
export interface ReviewModeSelectionResult {
    mode: ReviewMode;
    confirmed: boolean;
    rememberChoice: boolean;
}

/**
 * ReviewModeSelectionService
 *
 * Manages review mode selection UI components including:
 * - Settings panel integration
 * - Modal dialog for mode selection
 * - Badge rendering for history display
 */
export class ReviewModeSelectionService {
    private app: App;
    private settings: ReviewModeSettings;
    private modalCallback: ((result: ReviewModeSelectionResult) => void) | null = null;

    constructor(app: App, settings: Partial<ReviewModeSettings> = {}) {
        this.app = app;
        this.settings = {
            ...DEFAULT_REVIEW_MODE_SETTINGS,
            ...settings,
        };
    }

    /**
     * Get current settings
     */
    getSettings(): ReviewModeSettings {
        return { ...this.settings };
    }

    /**
     * Update settings
     */
    updateSettings(settings: Partial<ReviewModeSettings>): void {
        this.settings = {
            ...this.settings,
            ...settings,
        };
    }

    /**
     * Get the effective mode (considering lastUsedMode if rememberLastMode is enabled)
     */
    getEffectiveMode(): ReviewMode {
        if (this.settings.rememberLastMode && this.settings.lastUsedMode) {
            return this.settings.lastUsedMode;
        }
        return this.settings.defaultMode;
    }

    /**
     * Set the last used mode
     */
    setLastUsedMode(mode: ReviewMode): void {
        this.settings.lastUsedMode = mode;
    }

    /**
     * Get review mode info
     */
    getModeInfo(mode: ReviewMode): ReviewModeInfo {
        return REVIEW_MODES[mode];
    }

    /**
     * Get all available modes
     */
    getAllModes(): ReviewModeInfo[] {
        return Object.values(REVIEW_MODES);
    }

    /**
     * Show mode selection modal
     *
     * Returns a Promise that resolves when user makes a selection
     */
    showModeSelectionModal(): Promise<ReviewModeSelectionResult> {
        return new Promise((resolve) => {
            const modal = new ReviewModeModal(
                this.app,
                this.getEffectiveMode(),
                (result) => {
                    if (result.confirmed && result.rememberChoice) {
                        this.setLastUsedMode(result.mode);
                    }
                    resolve(result);
                }
            );
            modal.open();
        });
    }

    /**
     * Show quick mode selection notice with buttons
     */
    showQuickModeSelection(onSelect: (mode: ReviewMode) => void): void {
        const notice = new Notice('', 0);
        const noticeEl = notice.noticeEl;
        noticeEl.empty();
        noticeEl.addClass('review-mode-quick-select');

        const container = noticeEl.createDiv('review-mode-quick-container');
        container.createEl('div', {
            text: '选择复习模式',
            cls: 'review-mode-quick-title',
        });

        const buttonsContainer = container.createDiv('review-mode-quick-buttons');

        for (const modeInfo of this.getAllModes()) {
            const button = buttonsContainer.createEl('button', {
                text: `${modeInfo.icon} ${modeInfo.label}`,
                cls: 'review-mode-quick-button',
            });
            button.addEventListener('click', () => {
                this.setLastUsedMode(modeInfo.mode);
                notice.hide();
                onSelect(modeInfo.mode);
            });
        }
    }

    /**
     * Create badge element for mode display
     */
    createModeBadge(mode: ReviewMode): HTMLElement {
        const modeInfo = this.getModeInfo(mode);
        const badge = document.createElement('span');
        badge.className = 'review-mode-badge';
        badge.textContent = `${modeInfo.icon} ${modeInfo.label}`;
        badge.style.backgroundColor = modeInfo.badgeColor;
        badge.style.color = '#fff';
        badge.style.padding = '2px 8px';
        badge.style.borderRadius = '12px';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = '500';
        badge.setAttribute('title', modeInfo.description);
        return badge;
    }

    /**
     * Create badge HTML string for embedding
     */
    createModeBadgeHTML(mode: ReviewMode): string {
        const modeInfo = this.getModeInfo(mode);
        return `<span class="review-mode-badge" style="background-color: ${modeInfo.badgeColor}; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500;" title="${modeInfo.description}">${modeInfo.icon} ${modeInfo.label}</span>`;
    }

    /**
     * Add settings to a settings container (for plugin settings tab)
     */
    addSettingsUI(containerEl: HTMLElement, onSave: () => void): void {
        containerEl.createEl('h3', { text: '复习模式设置' });

        new Setting(containerEl)
            .setName('默认复习模式')
            .setDesc('启动复习时的默认模式')
            .addDropdown((dropdown) => {
                for (const modeInfo of this.getAllModes()) {
                    dropdown.addOption(modeInfo.mode, `${modeInfo.icon} ${modeInfo.label}`);
                }
                dropdown.setValue(this.settings.defaultMode);
                dropdown.onChange((value: ReviewMode) => {
                    this.settings.defaultMode = value;
                    onSave();
                });
            });

        new Setting(containerEl)
            .setName('启动时显示模式选择')
            .setDesc('每次启动复习时弹出模式选择对话框')
            .addToggle((toggle) => {
                toggle.setValue(this.settings.showModeSelectionOnStart);
                toggle.onChange((value) => {
                    this.settings.showModeSelectionOnStart = value;
                    onSave();
                });
            });

        new Setting(containerEl)
            .setName('记住上次选择')
            .setDesc('自动使用上次选择的复习模式')
            .addToggle((toggle) => {
                toggle.setValue(this.settings.rememberLastMode);
                toggle.onChange((value) => {
                    this.settings.rememberLastMode = value;
                    onSave();
                });
            });

        // Mode descriptions
        const descContainer = containerEl.createDiv('review-mode-descriptions');
        descContainer.createEl('h4', { text: '模式说明' });

        for (const modeInfo of this.getAllModes()) {
            const modeRow = descContainer.createDiv('review-mode-desc-row');
            modeRow.createEl('span', {
                text: `${modeInfo.icon} ${modeInfo.label}`,
                cls: 'review-mode-desc-label',
            });
            modeRow.createEl('span', {
                text: modeInfo.description,
                cls: 'review-mode-desc-text',
            });
        }
    }

    /**
     * Validate mode string
     */
    isValidMode(mode: string): mode is ReviewMode {
        return mode === 'fresh' || mode === 'targeted';
    }

    /**
     * Parse mode from string with fallback
     */
    parseMode(mode: string, fallback: ReviewMode = 'fresh'): ReviewMode {
        return this.isValidMode(mode) ? mode : fallback;
    }

    /**
     * Get CSS styles for the components
     */
    getStyles(): string {
        return `
            .review-mode-badge {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                margin: 0 4px;
            }

            .review-mode-quick-select {
                padding: 16px !important;
            }

            .review-mode-quick-container {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .review-mode-quick-title {
                font-weight: 600;
                font-size: 14px;
            }

            .review-mode-quick-buttons {
                display: flex;
                gap: 8px;
            }

            .review-mode-quick-button {
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                border: 1px solid var(--background-modifier-border);
            }

            .review-mode-quick-button:hover {
                background-color: var(--background-modifier-hover);
            }

            .review-mode-descriptions {
                margin-top: 16px;
                padding: 12px;
                background-color: var(--background-secondary);
                border-radius: 8px;
            }

            .review-mode-desc-row {
                display: flex;
                gap: 8px;
                margin: 8px 0;
            }

            .review-mode-desc-label {
                font-weight: 500;
                min-width: 100px;
            }

            .review-mode-desc-text {
                color: var(--text-muted);
            }
        `;
    }
}

/**
 * Modal for review mode selection
 */
export class ReviewModeModal extends Modal {
    private selectedMode: ReviewMode;
    private rememberChoice: boolean = false;
    private onSubmit: (result: ReviewModeSelectionResult) => void;

    constructor(
        app: App,
        defaultMode: ReviewMode,
        onSubmit: (result: ReviewModeSelectionResult) => void
    ) {
        super(app);
        this.selectedMode = defaultMode;
        this.onSubmit = onSubmit;
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('review-mode-modal');

        contentEl.createEl('h2', { text: '选择复习模式' });
        contentEl.createEl('p', {
            text: '请选择本次复习的模式',
            cls: 'review-mode-modal-subtitle',
        });

        const modeContainer = contentEl.createDiv('review-mode-options');

        for (const modeInfo of Object.values(REVIEW_MODES)) {
            const option = modeContainer.createDiv('review-mode-option');
            option.addClass(this.selectedMode === modeInfo.mode ? 'selected' : '');

            const header = option.createDiv('review-mode-option-header');
            header.createEl('span', {
                text: modeInfo.icon,
                cls: 'review-mode-option-icon',
            });
            header.createEl('span', {
                text: modeInfo.label,
                cls: 'review-mode-option-label',
            });

            option.createEl('p', {
                text: modeInfo.description,
                cls: 'review-mode-option-desc',
            });

            option.addEventListener('click', () => {
                modeContainer.querySelectorAll('.review-mode-option').forEach((el) => {
                    el.removeClass('selected');
                });
                option.addClass('selected');
                this.selectedMode = modeInfo.mode;
            });
        }

        // Remember choice checkbox
        const checkboxContainer = contentEl.createDiv('review-mode-remember');
        const checkbox = checkboxContainer.createEl('input', {
            type: 'checkbox',
            attr: { id: 'remember-choice' },
        });
        checkbox.checked = this.rememberChoice;
        checkbox.addEventListener('change', () => {
            this.rememberChoice = checkbox.checked;
        });
        checkboxContainer.createEl('label', {
            text: '记住此选择',
            attr: { for: 'remember-choice' },
        });

        // Action buttons
        const buttonContainer = contentEl.createDiv('review-mode-buttons');

        const cancelButton = buttonContainer.createEl('button', {
            text: '取消',
            cls: 'review-mode-button-cancel',
        });
        cancelButton.addEventListener('click', () => {
            this.close();
            this.onSubmit({
                mode: this.selectedMode,
                confirmed: false,
                rememberChoice: false,
            });
        });

        const confirmButton = buttonContainer.createEl('button', {
            text: '开始复习',
            cls: 'review-mode-button-confirm mod-cta',
        });
        confirmButton.addEventListener('click', () => {
            this.close();
            this.onSubmit({
                mode: this.selectedMode,
                confirmed: true,
                rememberChoice: this.rememberChoice,
            });
        });
    }

    onClose() {
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Get CSS styles for the modal
     */
    static getStyles(): string {
        return `
            .review-mode-modal {
                padding: 20px;
            }

            .review-mode-modal h2 {
                margin-bottom: 8px;
            }

            .review-mode-modal-subtitle {
                color: var(--text-muted);
                margin-bottom: 20px;
            }

            .review-mode-options {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-bottom: 20px;
            }

            .review-mode-option {
                padding: 16px;
                border: 2px solid var(--background-modifier-border);
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .review-mode-option:hover {
                border-color: var(--interactive-accent);
                background-color: var(--background-modifier-hover);
            }

            .review-mode-option.selected {
                border-color: var(--interactive-accent);
                background-color: var(--background-modifier-active-hover);
            }

            .review-mode-option-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }

            .review-mode-option-icon {
                font-size: 20px;
            }

            .review-mode-option-label {
                font-weight: 600;
                font-size: 16px;
            }

            .review-mode-option-desc {
                color: var(--text-muted);
                font-size: 14px;
                margin: 0;
            }

            .review-mode-remember {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 20px;
            }

            .review-mode-buttons {
                display: flex;
                justify-content: flex-end;
                gap: 12px;
            }

            .review-mode-button-cancel,
            .review-mode-button-confirm {
                padding: 8px 20px;
                border-radius: 4px;
                cursor: pointer;
            }
        `;
    }
}

/**
 * Factory function
 */
export function createReviewModeSelectionService(
    app: App,
    settings?: Partial<ReviewModeSettings>
): ReviewModeSelectionService {
    return new ReviewModeSelectionService(app, settings);
}
