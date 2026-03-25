/**
 * Scoring Checkpoint Modal
 * Story 2.8: 嵌入式评分检查点 - 用户交互Modal
 *
 * 显示内容：
 * 1. 评分结果（总分 + 4维度分析）
 * 2. 智能建议（根据最弱维度推荐Agent）
 * 3. 用户选择按钮
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 2.8/2.9 PRD
 */

import { App, Modal, ButtonComponent, setIcon } from 'obsidian';
import {
    ScoringResult,
    SuggestionText,
    SuggestionChoice,
} from '../services/ScoringCheckpointService';

// ============================================================================
// Constants
// ============================================================================

/**
 * Operation display names
 */
const OPERATION_NAMES: Record<string, string> = {
    'decomposition': '基础拆解',
    'basic-decomp': '基础拆解',
    'deep-decomp': '深度拆解',
    'deep-decomposition': '深度拆解',
    'oral': '口语化解释',
    'oral-explanation': '口语化解释',
    'four-level': '四层次解释',
    'four-level-explanation': '四层次解释',
    'clarification': '澄清路径',
    'clarification-path': '澄清路径',
    'example-teaching': '例题教学',
    'memory-anchor': '记忆锚点',
    'verification-questions': '检验问题',
    'verification-canvas': '检验白板',
};

/**
 * Status icons
 */
const STATUS_ICONS = {
    good: '✅',
    warning: '⚠️',
    weak: '❌',
} as const;

/**
 * Score color classes
 */
const SCORE_COLORS = {
    high: 'score-high',    // >= 80
    medium: 'score-medium', // 60-79
    low: 'score-low',       // < 60
} as const;

// ============================================================================
// ScoringCheckpointModal
// ============================================================================

/**
 * Scoring Checkpoint Modal
 *
 * Displays scoring results and intelligent suggestions,
 * allowing user to choose next action.
 */
export class ScoringCheckpointModal extends Modal {
    private scoringResult: ScoringResult;
    private suggestion: SuggestionText;
    private operationType: string;
    private onChoiceCallback: (choice: SuggestionChoice) => Promise<void>;

    constructor(
        app: App,
        scoringResult: ScoringResult,
        suggestion: SuggestionText,
        operationType: string,
        onChoice: (choice: SuggestionChoice) => Promise<void>
    ) {
        super(app);
        this.scoringResult = scoringResult;
        this.suggestion = suggestion;
        this.operationType = operationType;
        this.onChoiceCallback = onChoice;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('scoring-checkpoint-modal');

        this.renderContent();
    }

    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Render modal content
     */
    private renderContent(): void {
        const { contentEl } = this;

        // Header
        this.renderHeader();

        // Score display
        this.renderScoreDisplay();

        // Dimension analysis
        this.renderDimensionAnalysis();

        // Suggestion box
        this.renderSuggestionBox();

        // Choice buttons
        this.renderChoiceButtons();

        // Footer note
        this.renderFooterNote();
    }

    /**
     * Render header section
     */
    private renderHeader(): void {
        const { contentEl } = this;

        const header = contentEl.createDiv({ cls: 'checkpoint-header' });

        // Icon
        const iconEl = header.createDiv({ cls: 'checkpoint-icon' });
        iconEl.setText('📊');

        // Title
        header.createEl('h2', {
            text: '评分检查点',
            cls: 'checkpoint-title',
        });

        // Subtitle
        const operationName = OPERATION_NAMES[this.operationType] || this.operationType;
        header.createEl('p', {
            text: `在执行「${operationName}」前，系统已自动评估您的理解`,
            cls: 'checkpoint-subtitle',
        });
    }

    /**
     * Render score display
     */
    private renderScoreDisplay(): void {
        const { contentEl } = this;
        const { totalScore, pass } = this.scoringResult;

        const scoreSection = contentEl.createDiv({ cls: 'score-display-section' });

        // Score circle
        const scoreCircle = scoreSection.createDiv({ cls: 'score-circle' });
        const colorClass = this.getScoreColorClass(totalScore);
        scoreCircle.addClass(colorClass);

        // Score value
        scoreCircle.createEl('span', {
            text: String(totalScore),
            cls: 'score-value',
        });

        // Score label
        scoreCircle.createEl('span', {
            text: '分',
            cls: 'score-unit',
        });

        // Pass/fail indicator
        const statusEl = scoreSection.createDiv({ cls: 'score-status' });
        if (pass) {
            statusEl.createEl('span', {
                text: '✅ 理解充分',
                cls: 'status-pass',
            });
        } else if (totalScore >= 60) {
            statusEl.createEl('span', {
                text: '⚠️ 似懂非懂',
                cls: 'status-partial',
            });
        } else {
            statusEl.createEl('span', {
                text: '❌ 需要深化',
                cls: 'status-fail',
            });
        }

        // Feedback text
        if (this.scoringResult.feedback) {
            scoreSection.createEl('p', {
                text: this.scoringResult.feedback,
                cls: 'score-feedback',
            });
        }
    }

    /**
     * Render dimension analysis
     */
    private renderDimensionAnalysis(): void {
        const { contentEl } = this;

        const analysisSection = contentEl.createDiv({ cls: 'dimension-analysis-section' });

        analysisSection.createEl('h3', {
            text: '4维度分析',
            cls: 'section-title',
        });

        const dimensionList = analysisSection.createDiv({ cls: 'dimension-list' });

        for (const dim of this.suggestion.dimensionAnalysis) {
            const dimItem = dimensionList.createDiv({ cls: 'dimension-item' });

            // Dimension name and status icon
            const dimHeader = dimItem.createDiv({ cls: 'dimension-header' });
            dimHeader.createEl('span', {
                text: `${STATUS_ICONS[dim.status]} ${dim.dimension}`,
                cls: `dimension-name ${dim.status}`,
            });

            // Score bar
            const barContainer = dimItem.createDiv({ cls: 'dimension-bar-container' });
            const bar = barContainer.createDiv({ cls: 'dimension-bar' });
            bar.style.width = `${(dim.score / 25) * 100}%`;
            bar.addClass(this.getDimensionBarClass(dim.score));

            // Score value
            dimItem.createEl('span', {
                text: `${dim.score}/25`,
                cls: 'dimension-score',
            });
        }

        // Highlight weakest dimension
        const weakestNote = analysisSection.createDiv({ cls: 'weakest-note' });
        weakestNote.createEl('span', {
            text: `最弱维度：${this.suggestion.weakestDimension}`,
            cls: 'weakest-dimension',
        });
    }

    /**
     * Render suggestion box
     */
    private renderSuggestionBox(): void {
        const { contentEl } = this;

        const suggestionSection = contentEl.createDiv({ cls: 'suggestion-section' });

        suggestionSection.createEl('h3', {
            text: '智能建议',
            cls: 'section-title',
        });

        // Summary
        const summaryBox = suggestionSection.createDiv({ cls: 'suggestion-summary' });
        summaryBox.createEl('p', {
            text: this.suggestion.summary,
        });

        // Recommended agent
        const recBox = suggestionSection.createDiv({ cls: 'recommended-agent-box' });
        const { recommendedAgent } = this.suggestion;

        recBox.createEl('div', {
            text: '💡 推荐使用',
            cls: 'recommendation-label',
        });

        const agentInfo = recBox.createDiv({ cls: 'agent-info' });
        agentInfo.createEl('span', {
            text: recommendedAgent.agentName,
            cls: 'agent-name',
        });
        agentInfo.createEl('span', {
            text: recommendedAgent.rationale,
            cls: 'agent-rationale',
        });
    }

    /**
     * Render choice buttons
     */
    private renderChoiceButtons(): void {
        const { contentEl } = this;

        const buttonSection = contentEl.createDiv({ cls: 'choice-buttons-section' });

        // Option A: Accept suggestion
        const acceptBtn = new ButtonComponent(buttonSection);
        acceptBtn
            .setButtonText(`A. 使用${this.suggestion.recommendedAgent.agentName} (推荐)`)
            .setCta()
            .onClick(async () => {
                this.close();
                await this.onChoiceCallback({
                    choice: 'accept_suggestion',
                    suggestedAgent: this.suggestion.recommendedAgent.agentType,
                });
            });
        acceptBtn.buttonEl.addClass('choice-btn', 'choice-accept');

        // Option B: Continue original
        const operationName = OPERATION_NAMES[this.operationType] || this.operationType;
        const continueBtn = new ButtonComponent(buttonSection);
        continueBtn
            .setButtonText(`B. 继续${operationName}`)
            .onClick(async () => {
                this.close();
                await this.onChoiceCallback({
                    choice: 'continue_original',
                });
            });
        continueBtn.buttonEl.addClass('choice-btn', 'choice-continue');

        // Option C: Cancel
        const cancelBtn = new ButtonComponent(buttonSection);
        cancelBtn
            .setButtonText('C. 取消操作')
            .onClick(async () => {
                this.close();
                await this.onChoiceCallback({
                    choice: 'cancel',
                });
            });
        cancelBtn.buttonEl.addClass('choice-btn', 'choice-cancel');
    }

    /**
     * Render footer note
     */
    private renderFooterNote(): void {
        const { contentEl } = this;

        const footer = contentEl.createDiv({ cls: 'checkpoint-footer' });
        footer.createEl('p', {
            text: '💡 系统仅提供建议，最终决定权在您手中',
            cls: 'footer-note',
        });
    }

    // ========================================================================
    // Helper Methods
    // ========================================================================

    /**
     * Get score color class
     */
    private getScoreColorClass(score: number): string {
        if (score >= 80) return SCORE_COLORS.high;
        if (score >= 60) return SCORE_COLORS.medium;
        return SCORE_COLORS.low;
    }

    /**
     * Get dimension bar class
     */
    private getDimensionBarClass(score: number): string {
        if (score >= 20) return 'bar-good';
        if (score >= 15) return 'bar-warning';
        return 'bar-weak';
    }
}
