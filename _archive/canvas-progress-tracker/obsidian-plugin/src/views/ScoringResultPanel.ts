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
import { NodeScore, RecommendActionResponse } from '../api/types';

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
 * Score thresholds for decision logic (0-100 scale)
 * [Source: specs/data/scoring-response.schema.json]
 * [Source: Story 31.3 - AC-31.3.3, AC-31.3.5]
 *
 * Note: These thresholds are used as fallback when API recommendation fails.
 * Primary recommendation comes from POST /agents/recommend-action endpoint.
 */
const SCORE_THRESHOLDS = {
    LOW: 60,      // Total score < 60 = Red (need decomposition)
    MEDIUM: 80,   // Total score 60-79 = Yellow (need clarification)
    HIGH: 80,     // Total score >= 80 = Green (mastered)
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
    /** Story 31.3: Cached API recommendations keyed by nodeId */
    private apiRecommendations: Map<string, RecommendActionResponse> = new Map();
    /** Story 31.10: Debounce tracking for retry button */
    private lastRetryTime: number = 0;
    /** Story 31.10: Flag to detect retry-triggered re-render */
    private isRetrying: boolean = false;
    /** Story 31.10: Render version counter — detects stale renders from concurrent calls */
    private renderVersion: number = 0;

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
     * Story 31.3: Fetch intelligent action recommendation from API
     *
     * @param result - Current scoring result item
     * @returns API recommendation or undefined on failure
     */
    private async fetchRecommendation(result: ScoringResultItem): Promise<RecommendActionResponse | undefined> {
        // Check cache first
        if (this.apiRecommendations.has(result.nodeId)) {
            return this.apiRecommendations.get(result.nodeId);
        }

        try {
            const recommendation = await this.apiClient.recommendAction({
                score: result.score.total,
                node_id: result.nodeId,
                canvas_name: result.canvasName,
                include_history: true,
            });

            // Cache the result
            this.apiRecommendations.set(result.nodeId, recommendation);
            return recommendation;
        } catch (error) {
            console.warn('[Story 31.3] Failed to fetch recommendation, using fallback:', error);
            return undefined;
        }
    }

    /**
     * Story 31.3: Convert API recommendation to AgentSuggestion format
     *
     * @param recommendation - API recommendation response
     * @returns Array of agent suggestions
     */
    private convertRecommendationToSuggestions(recommendation: RecommendActionResponse): AgentSuggestion[] {
        const suggestions: AgentSuggestion[] = [];

        // Primary recommendation
        const actionMap: Record<string, { label: string; emoji: string; description: string }> = {
            'decompose': {
                label: '进一步拆解',
                emoji: '🔍',
                description: recommendation.reason,
            },
            'explain': {
                label: '补充解释',
                emoji: '💡',
                description: recommendation.reason,
            },
            'next': {
                label: '继续下一个',
                emoji: '✅',
                description: recommendation.reason,
            },
        };

        const primaryAction = actionMap[recommendation.action];
        if (primaryAction) {
            suggestions.push({
                action: recommendation.action as AgentSuggestion['action'],
                ...primaryAction,
            });
        }

        // Add alternatives from API
        if (recommendation.alternative_agents) {
            for (const alt of recommendation.alternative_agents) {
                // Map agent endpoint to action type
                const altAction = alt.agent.includes('memory') ? 'memory-anchor' :
                                 alt.agent.includes('clarify') ? 'clarify' :
                                 alt.agent.includes('explain') ? 'explain' : 'explain';
                suggestions.push({
                    action: altAction,
                    label: altAction === 'memory-anchor' ? '记忆锚点' : '补充解释',
                    emoji: altAction === 'memory-anchor' ? '⚓' : '💡',
                    description: alt.reason,
                });
            }
        }

        // Add review suggestion if needed
        if (recommendation.review_suggested && !suggestions.some(s => s.action === 'explain')) {
            suggestions.push({
                action: 'explain',
                label: '建议复习',
                emoji: '📖',
                description: '历史成绩显示需要加强复习',
            });
        }

        return suggestions;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('scoring-result-panel');

        // Story 31.3: renderCurrentResult is now async, handle promise
        this.renderCurrentResult().catch(error => {
            console.error('[ScoringResultPanel] Failed to render:', error);
        });
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
     * Story 31.3: Now fetches intelligent recommendations from API
     */
    private async renderCurrentResult(): Promise<void> {
        const thisRender = ++this.renderVersion;
        const { contentEl } = this;
        contentEl.empty();

        if (this.results.length === 0) {
            this.renderNoResults();
            return;
        }

        const result = this.results[this.currentIndex];

        // Story 31.3: Try to get API recommendations, fall back to score-based logic
        let suggestions: AgentSuggestion[];
        const recommendation = await this.fetchRecommendation(result);

        // Stale render check: bail out if another render started during await
        if (thisRender !== this.renderVersion) {
            this.isRetrying = false;
            return;
        }

        if (recommendation) {
            suggestions = this.convertRecommendationToSuggestions(recommendation);
            console.log('[Story 31.3] Using API recommendation:', recommendation.action);
        } else {
            suggestions = getSuggestionsForScore(result.score.total);
            console.warn('[Story 31.8] Using fallback recommendations — API unavailable');
            // Story 31.8: Show notice on retry failure (AC-31.8.2)
            if (this.isRetrying) {
                new Notice('后端仍不可用');
            }
        }
        this.isRetrying = false;

        // Header
        this.renderHeader(result);

        // Score details
        this.renderScoreDetails(result.score);

        // Feedback
        this.renderFeedback(result.score.total);

        // Story 31.10: Recommendation source status indicator
        this.renderRecommendationStatus(!!recommendation, recommendation, result);

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
            text: '/ 100',
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
            dimItem.createEl('span', { text: `${dim.value}/25`, cls: 'dimension-value' });

            // Progress bar
            const progressBar = dimItem.createEl('div', { cls: 'dimension-progress' });
            const progressFill = progressBar.createEl('div', { cls: 'dimension-progress-fill' });
            progressFill.style.width = `${dim.value * 4}%`;
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
     * Story 31.8/31.10: Render recommendation source status indicator
     *
     * Shows whether recommendations come from the API (online/intelligent)
     * or from local fallback logic (offline/score-based).
     * Story 31.8: Adds fallback indicator with retry button when API unavailable.
     *
     * @param isOnline - true if API recommendation was successful
     * @param recommendation - API recommendation response (if available)
     * @param result - Current scoring result item (for retry context)
     *
     * [Source: Story 31.8 - AC-31.8.1, AC-31.8.2, AC-31.8.3]
     * [Source: Story 31.10 - AC-31.10.1, AC-31.10.2, AC-31.10.3, AC-31.10.4]
     */
    private renderRecommendationStatus(
        isOnline: boolean,
        recommendation: RecommendActionResponse | undefined,
        result: ScoringResultItem
    ): void {
        const { contentEl } = this;

        if (isOnline) {
            // AC-31.10.2: Online/intelligent recommendation indicator
            const statusEl = contentEl.createEl('div', {
                cls: 'recommendation-status-container recommendation-status-online',
            });
            statusEl.createEl('span', {
                text: '✅ 智能推荐',
                cls: 'recommendation-status-label',
            });
            // Show history context info if available
            if (recommendation?.history_context?.recent_scores?.length) {
                statusEl.createEl('span', {
                    text: `基于 ${recommendation.history_context.recent_scores.length} 次历史记录`,
                    cls: 'recommendation-status-info',
                });
            }
        } else {
            // Story 31.8 AC-31.8.1: Offline/fallback recommendation indicator
            const statusEl = contentEl.createEl('div', {
                cls: 'fallback-indicator',
            });
            statusEl.createEl('span', {
                text: '⚠️ 离线推荐 — 后端不可用，使用本地规则',
                cls: 'fallback-text',
            });

            // Story 31.8 AC-31.8.2: Retry button
            const retryBtn = statusEl.createEl('button', {
                text: '🔄 重试',
                cls: 'fallback-retry-button',
            });
            retryBtn.addEventListener('click', () => this.handleRetry(retryBtn, result));
        }
    }

    /**
     * Story 31.10: Handle retry button click
     *
     * Clears cached recommendation and re-fetches from API.
     * Includes debounce (2s) and disable-on-fail (5s) protections.
     *
     * @param btn - The retry button element
     * @param result - Current scoring result item
     *
     * [Source: Story 31.10 - AC-31.10.3, ADR-009 (WARNING level notification)]
     */
    private async handleRetry(btn: HTMLButtonElement, result: ScoringResultItem): Promise<void> {
        // Debounce: 2 seconds between retries
        const now = Date.now();
        if (now - this.lastRetryTime < 2000) {
            return;
        }
        this.lastRetryTime = now;

        // Disable button during retry
        btn.disabled = true;
        btn.textContent = '重试中...';

        // Clear cached recommendation for this node
        this.apiRecommendations.delete(result.nodeId);

        // Set retry flag so renderCurrentResult can detect retry failure
        this.isRetrying = true;

        await this.renderCurrentResult();

        // After re-render, if still in fallback mode, apply 5s cooldown to new retry button
        const newRetryBtn = this.contentEl.querySelector('.fallback-retry-button') as HTMLButtonElement | null;
        if (newRetryBtn) {
            newRetryBtn.disabled = true;
            newRetryBtn.textContent = '冷却中...';
            setTimeout(() => {
                newRetryBtn.disabled = false;
                newRetryBtn.textContent = '🔄 重试';
            }, 5000);
        }
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
                // Story 31.3: Handle async render
                this.renderCurrentResult().catch(e => console.error('[ScoringResultPanel] Nav error:', e));
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
                // Story 31.3: Handle async render
                this.renderCurrentResult().catch(e => console.error('[ScoringResultPanel] Nav error:', e));
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
                    await this.renderCurrentResult();
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
                        node_content: result.nodeText,
                    });
                    new Notice('✅ 基础拆解完成，已添加到Canvas');
                    break;

                case 'explain':
                    await this.apiClient.explainOral({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                        node_content: result.nodeText,
                    });
                    new Notice('✅ 口语化解释完成，已添加到Canvas');
                    break;

                case 'clarify':
                    await this.apiClient.explainClarification({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                        node_content: result.nodeText,
                    });
                    new Notice('✅ 澄清路径完成，已添加到Canvas');
                    break;

                case 'memory-anchor':
                    await this.apiClient.explainMemory({
                        canvas_name: result.canvasName,
                        node_id: result.nodeId,
                        node_content: result.nodeText,
                    });
                    new Notice('✅ 记忆锚点完成，已添加到Canvas');
                    break;
            }

            // Fire-and-forget: record learning event to memory system (Story 30.7)
            this.apiClient.recordLearningEvent({
                canvasPath: result.canvasName,
                nodeId: result.nodeId,
                concept: result.nodeText.substring(0, 100),
                agentType: 'scoring',
                score: result.score.total,
            });

            // Call callback if provided
            await this.callbacks.onAgentAction?.(result.nodeId, suggestion.action);

            // Move to next or close
            if (this.currentIndex < this.results.length - 1) {
                this.currentIndex++;
                await this.renderCurrentResult();
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
