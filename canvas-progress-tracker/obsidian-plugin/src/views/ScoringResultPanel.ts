/**
 * Scoring Result Panel - Agent Decision UI
 *
 * Shows scoring results with Agent decision buttons.
 * After scoring, suggests next actions based on score:
 * - Low score (<60): Decompose or Explain options
 * - Medium score (60-80): Clarification option
 * - High score (>=80): Continue to next
 *
 * @module views/ScoringResultPanel
 * @version 1.0.0
 * @story Story 14.16 Phase 5.1
 *
 * [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-5-Memory-Integration]
 */

import { App, Modal, Notice } from 'obsidian';
import { ApiClient } from '../api/ApiClient';
import { NodeScore } from '../api/types';

/**
 * Scoring result with node context
 */
export interface ScoringResultItem {
    nodeId: string;
    nodeText: string;
    score: NodeScore;
    canvasName: string;
}

/**
 * Agent action suggestion
 */
export interface AgentSuggestion {
    action: 'decompose' | 'explain' | 'clarify' | 'memory-anchor' | 'next';
    label: string;
    emoji: string;
    description: string;
}

/**
 * Callbacks for ScoringResultPanel
 */
export interface ScoringResultCallbacks {
    onClose: () => void;
    onAgentAction?: (nodeId: string, action: string) => Promise<void>;
    onNextNode?: () => void;
}

/**
 * Score thresholds for decision logic
 * [Source: PRD F2 - 4-dimension scoring system]
 */
const SCORE_THRESHOLDS = {
    LOW: 24,      // Total score < 24 = Red (need decomposition)
    MEDIUM: 32,   // Total score 24-31 = Yellow (need clarification)
    HIGH: 32,     // Total score >= 32 = Green (mastered)
};

/**
 * Agent suggestions based on score
 */
function getSuggestionsForScore(totalScore: number): AgentSuggestion[] {
    if (totalScore < SCORE_THRESHOLDS.LOW) {
        // Low score: needs fundamental help
        return [
            {
                action: 'decompose',
                label: '进一步拆解',
                emoji: '🔍',
                description: '将概念拆解为更基础的问题，帮助理解核心要点',
            },
            {
                action: 'explain',
                label: '补充解释',
                emoji: '💡',
                description: '生成更详细的解释，加深理解',
            },
            {
                action: 'memory-anchor',
                label: '记忆锚点',
                emoji: '⚓',
                description: '创建生动的类比和故事，帮助长期记忆',
            },
        ];
    } else if (totalScore < SCORE_THRESHOLDS.HIGH) {
        // Medium score: needs refinement
        return [
            {
                action: 'clarify',
                label: '深入理解',
                emoji: '🧠',
                description: '澄清模糊点，完善理解',
            },
            {
                action: 'explain',
                label: '四层次解释',
                emoji: '📚',
                description: '从入门到专家的渐进式解释',
            },
            {
                action: 'next',
                label: '跳过，继续下一个',
                emoji: '➡️',
                description: '已基本掌握，继续下一个概念',
            },
        ];
    } else {
        // High score: mastered
        return [
            {
                action: 'next',
                label: '继续下一个',
                emoji: '✅',
                description: '已掌握，继续下一个概念',
            },
        ];
    }
}

/**
 * Get color class for score
 */
function getScoreColorClass(totalScore: number): string {
    if (totalScore < SCORE_THRESHOLDS.LOW) {
        return 'score-low';    // Red
    } else if (totalScore < SCORE_THRESHOLDS.HIGH) {
        return 'score-medium'; // Yellow
    } else {
        return 'score-high';   // Green
    }
}

/**
 * Get score feedback text
 */
function getScoreFeedback(totalScore: number): string {
    if (totalScore < SCORE_THRESHOLDS.LOW) {
        return '需要进一步学习';
    } else if (totalScore < SCORE_THRESHOLDS.HIGH) {
        return '基本理解，可以深入';
    } else {
        return '掌握良好！';
    }
}

/**
 * Scoring Result Panel Modal
 *
 * Displays scoring results and provides Agent decision buttons
 * for next learning actions.
 *
 * [Source: Story 14.16 - Agent Decision UI]
 */
export class ScoringResultPanel extends Modal {
    private results: ScoringResultItem[];
    private currentIndex: number;
    private apiClient: ApiClient;
    private callbacks: ScoringResultCallbacks;
    private isProcessing: boolean = false;

    /**
     * Creates a new ScoringResultPanel
     *
     * @param app - Obsidian App instance
     * @param results - Scoring results to display
     * @param apiClient - API client for Agent calls
     * @param callbacks - Callbacks for actions
     */
    constructor(
        app: App,
        results: ScoringResultItem[],
        apiClient: ApiClient,
        callbacks: ScoringResultCallbacks
    ) {
        super(app);
        this.results = results;
        this.currentIndex = 0;
        this.apiClient = apiClient;
        this.callbacks = callbacks;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('scoring-result-panel');

        this.renderCurrentResult();
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
        this.callbacks.onClose();
    }

    /**
     * Render current result
     */
    private renderCurrentResult(): void {
        const { contentEl } = this;
        contentEl.empty();

        if (this.results.length === 0) {
            this.renderNoResults();
            return;
        }

        const result = this.results[this.currentIndex];
        const suggestions = getSuggestionsForScore(result.score.total);

        // Header
        this.renderHeader(result);

        // Score details
        this.renderScoreDetails(result.score);

        // Feedback
        this.renderFeedback(result.score.total);

        // Agent decision buttons
        this.renderAgentButtons(result, suggestions);

        // Navigation (if multiple results)
        if (this.results.length > 1) {
            this.renderNavigation();
        }
    }

    /**
     * Render no results message
     */
    private renderNoResults(): void {
        const { contentEl } = this;
        contentEl.createEl('div', {
            cls: 'no-results',
            text: '没有评分结果',
        });
    }

    /**
     * Render header with node info
     */
    private renderHeader(result: ScoringResultItem): void {
        const { contentEl } = this;
        const header = contentEl.createEl('div', { cls: 'scoring-header' });

        // Title
        header.createEl('h2', {
            text: '📝 评分结果',
            cls: 'scoring-title',
        });

        // Progress indicator
        if (this.results.length > 1) {
            header.createEl('div', {
                text: `${this.currentIndex + 1} / ${this.results.length}`,
                cls: 'progress-indicator',
            });
        }

        // Node text
        header.createEl('div', {
            text: this.truncateText(result.nodeText, 60),
            cls: 'node-text',
        });
    }

    /**
     * Render 4-dimension score details
     */
    private renderScoreDetails(score: NodeScore): void {
        const { contentEl } = this;
        const colorClass = getScoreColorClass(score.total);

        // Total score (prominent)
        const totalSection = contentEl.createEl('div', { cls: 'total-score-section' });
        totalSection.createEl('div', {
            text: String(score.total),
            cls: `total-score ${colorClass}`,
        });
        totalSection.createEl('div', {
            text: '/ 40',
            cls: 'max-score',
        });

        // Dimension breakdown
        const dimensionsSection = contentEl.createEl('div', { cls: 'dimensions-section' });

        const dimensions = [
            { name: '准确性', value: score.accuracy, emoji: '🎯' },
            { name: '形象化', value: score.imagery, emoji: '🖼️' },
            { name: '完整性', value: score.completeness, emoji: '📋' },
            { name: '创造性', value: score.originality, emoji: '💡' },
        ];

        for (const dim of dimensions) {
            const dimItem = dimensionsSection.createEl('div', { cls: 'dimension-item' });
            dimItem.createEl('span', { text: dim.emoji, cls: 'dimension-emoji' });
            dimItem.createEl('span', { text: dim.name, cls: 'dimension-name' });
            dimItem.createEl('span', { text: `${dim.value}/10`, cls: 'dimension-value' });

            // Progress bar
            const progressBar = dimItem.createEl('div', { cls: 'dimension-progress' });
            const progressFill = progressBar.createEl('div', { cls: 'dimension-progress-fill' });
            progressFill.style.width = `${dim.value * 10}%`;
        }
    }

    /**
     * Render feedback based on score
     */
    private renderFeedback(totalScore: number): void {
        const { contentEl } = this;
        const colorClass = getScoreColorClass(totalScore);
        const feedback = getScoreFeedback(totalScore);

        const feedbackSection = contentEl.createEl('div', { cls: `feedback-section ${colorClass}` });
        feedbackSection.createEl('div', {
            text: feedback,
            cls: 'feedback-text',
        });
    }

    /**
     * Render Agent decision buttons
     */
    private renderAgentButtons(result: ScoringResultItem, suggestions: AgentSuggestion[]): void {
        const { contentEl } = this;
        const buttonsSection = contentEl.createEl('div', { cls: 'agent-buttons-section' });

        buttonsSection.createEl('h3', {
            text: '下一步行动',
            cls: 'section-title',
        });

        for (const suggestion of suggestions) {
            const btn = buttonsSection.createEl('button', {
                cls: `agent-button action-${suggestion.action}`,
            });

            btn.createEl('span', { text: suggestion.emoji, cls: 'button-emoji' });
            btn.createEl('span', { text: suggestion.label, cls: 'button-label' });
            btn.createEl('div', { text: suggestion.description, cls: 'button-description' });

            btn.addEventListener('click', () => this.handleAgentAction(result, suggestion));
        }
    }

    /**
     * Render navigation buttons
     */
    private renderNavigation(): void {
        const { contentEl } = this;
        const nav = contentEl.createEl('div', { cls: 'navigation-section' });

        // Previous button
        if (this.currentIndex > 0) {
            const prevBtn = nav.createEl('button', {
                text: '← 上一个',
                cls: 'nav-button prev-button',
            });
            prevBtn.addEventListener('click', () => {
                this.currentIndex--;
                this.renderCurrentResult();
            });
        }

        // Next button
        if (this.currentIndex < this.results.length - 1) {
            const nextBtn = nav.createEl('button', {
                text: '下一个 →',
                cls: 'nav-button next-button',
            });
            nextBtn.addEventListener('click', () => {
                this.currentIndex++;
                this.renderCurrentResult();
            });
        }
    }

    /**
     * Handle Agent action button click
     */
    private async handleAgentAction(
        result: ScoringResultItem,
        suggestion: AgentSuggestion
    ): Promise<void> {
        if (this.isProcessing) {
            return;
        }

        this.isProcessing = true;

        try {
            if (suggestion.action === 'next') {
                // Move to next node or close
                if (this.currentIndex < this.results.length - 1) {
                    this.currentIndex++;
                    this.renderCurrentResult();
                } else {
                    new Notice('所有节点已完成评分！');
                    this.close();
                    this.callbacks.onNextNode?.();
                }
                return;
            }

            // Show processing state
            new Notice(`${suggestion.emoji} 正在${suggestion.label}...`);

            // Call Agent API based on action
            switch (suggestion.action) {
                case 'decompose':
                    await this.apiClient.decomposeBasic({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                    });
                    new Notice('✅ 基础拆解完成，已添加到Canvas');
                    break;

                case 'explain':
                    await this.apiClient.explainOral({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                    });
                    new Notice('✅ 口语化解释完成，已添加到Canvas');
                    break;

                case 'clarify':
                    await this.apiClient.explainClarification({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                    });
                    new Notice('✅ 澄清路径完成，已添加到Canvas');
                    break;

                case 'memory-anchor':
                    await this.apiClient.explainMemory({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                    });
                    new Notice('✅ 记忆锚点完成，已添加到Canvas');
                    break;
            }

            // Call callback if provided
            await this.callbacks.onAgentAction?.(result.nodeId, suggestion.action);

            // Move to next or close
            if (this.currentIndex < this.results.length - 1) {
                this.currentIndex++;
                this.renderCurrentResult();
            } else {
                this.close();
            }

        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            new Notice(`❌ 操作失败: ${message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Truncate text to specified length
     */
    private truncateText(text: string, maxLength: number): string {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength - 3) + '...';
    }
}
