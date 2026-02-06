/**
 * Review Dashboard View - Canvas Learning System
 *
 * Main dashboard view component for Obsidian.
 * Implements Story 14.2: 复习仪表板UI
 *
 * @module ReviewDashboardView
 * @version 1.0.0
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView Class)
 */

import { ItemView, WorkspaceLeaf, Notice, setIcon, Menu, TFile, requestUrl } from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import {
    ReviewTask,
    DashboardStatistics,
    DashboardViewState,
    DEFAULT_DASHBOARD_STATE,
    TaskSortOption,
    TaskFilterOption,
    TaskPriority,
    DashboardTab,
    HistoryTimeRange,
    HistoryEntry,
    DailyStatItem,
    CanvasReviewTrend,
    DEFAULT_HISTORY_STATE,
    DEFAULT_VERIFICATION_STATE,
    DEFAULT_CROSS_CANVAS_STATE,
    VerificationCanvasRelation,
    CrossCanvasAssociation,
    CrossCanvasSearchResult,
    KnowledgePath,
} from '../types/UITypes';
import { HistoryService } from '../services/HistoryService';
import { VerificationHistoryService, createVerificationHistoryService } from '../services/VerificationHistoryService';
import { CrossCanvasService, createCrossCanvasService } from '../services/CrossCanvasService';
import { TextbookMountService, createTextbookMountService } from '../services/TextbookMountService';
import type { MountedTextbook, TextbookType } from '../types/UITypes';
// Story 30.7 AC-30.7.3: Import PriorityCalculatorService for real memory-based priority
import {
    PriorityCalculatorService,
    createPriorityCalculatorService,
    PriorityResult,
} from '../services/PriorityCalculatorService';

export const VIEW_TYPE_REVIEW_DASHBOARD = 'canvas-review-dashboard';

/**
 * Review Dashboard View - Main dashboard ItemView
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (ItemView - Custom Views)
 */
export class ReviewDashboardView extends ItemView {
    private plugin: CanvasReviewPlugin;
    private state: DashboardViewState;
    private refreshInterval: number | null = null;
    private historyService: HistoryService;
    private verificationService: VerificationHistoryService;
    private crossCanvasService: CrossCanvasService;
    private textbookMountService: TextbookMountService;
    /** Story 30.7 AC-30.7.3: PriorityCalculatorService for 4-dimensional priority */
    private priorityCalculatorService: PriorityCalculatorService;

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;
        this.state = { ...DEFAULT_DASHBOARD_STATE };
        this.historyService = new HistoryService(this.app);
        this.verificationService = createVerificationHistoryService(this.app);
        this.crossCanvasService = plugin.crossCanvasService || createCrossCanvasService(this.app);
        this.textbookMountService = createTextbookMountService(this.app);
        // Story 30.7 AC-30.7.3: Initialize PriorityCalculatorService
        this.priorityCalculatorService = createPriorityCalculatorService(this.app);
    }

    getViewType(): string {
        return VIEW_TYPE_REVIEW_DASHBOARD;
    }

    getDisplayText(): string {
        return 'Canvas Review Dashboard';
    }

    getIcon(): string {
        return 'calendar-check';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        container.addClass('review-dashboard-container');

        // Load CSS
        this.loadStyles();

        // Render initial loading state
        this.renderDashboard(container as HTMLElement);

        // Load data
        await this.loadData();

        // Setup auto-refresh (every 5 minutes)
        this.refreshInterval = window.setInterval(() => {
            this.loadData();
        }, 5 * 60 * 1000);
    }

    async onClose(): Promise<void> {
        if (this.refreshInterval !== null) {
            window.clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // =========================================================================
    // Data Loading
    // =========================================================================

    private async loadData(): Promise<void> {
        this.updateViewState({ loading: true, error: null });

        try {
            const dataManager = this.plugin.getDataManager();

            if (!dataManager) {
                throw new Error('Database not initialized');
            }

            // ✅ 保留：Dashboard 统计数据（TodayReviewListService 不提供这些）
            const dailyStats = await dataManager.getDailyStatistics();

            // Story 32.4 AC-32.4.2: Query streak days from ReviewRecordDAO
            let streakDays = 0;
            try {
                const reviewRecordDAO = dataManager.getReviewRecordDAO();
                streakDays = await reviewRecordDAO.calculateStreakDays();
            } catch (error) {
                console.warn('[ReviewDashboard] Streak calculation failed, using default:', error);
            }

            // Story 31.A.6: Get review tasks from TodayReviewListService (with 60s cache + real FSRS)
            // Falls back to legacy loading if service not available
            const todayService = this.plugin.todayReviewListService;
            let tasks: ReviewTask[];

            if (todayService) {
                const todayItems = await todayService.getTodayReviewItems();
                // TodayReviewItem extends ReviewTask, so this is type-safe
                tasks = todayItems as ReviewTask[];
            } else {
                // Fallback: legacy loading path (pre-31.A.6)
                const dueReviews = await dataManager.getDueReviews();
                const conceptIds = dueReviews
                    .map((r) => r.conceptId || r.conceptName || '')
                    .filter(Boolean);
                let reviewCountMap = new Map<string, number>();
                try {
                    const reviewRecordDAO = dataManager.getReviewRecordDAO();
                    reviewCountMap = await reviewRecordDAO.getReviewCountBatch(conceptIds);
                } catch (error) {
                    console.warn('[ReviewDashboard] Batch review count query failed:', error);
                }

                // Batch query all FSRS states upfront (concurrency-controlled)
                const fsrsStateMap = await this.batchQueryFSRSStates(conceptIds);

                tasks = await Promise.all(
                    dueReviews.map(async (review) => {
                        const conceptId = review.conceptId || review.conceptName || '';
                        const memoryResult = await this.queryConceptMemory(review.conceptName || conceptId);
                        // Story 31.A.4 AC-31.A.4.3: Use batch-queried FSRS state
                        const fsrsResponse = fsrsStateMap.get(conceptId);
                        const fsrsState = fsrsResponse?.fsrs_state || null;
                        const adaptedFsrs = fsrsState ? this.adaptFSRSStateToCardState(conceptId, fsrsState) : null;
                        const priorityResult = this.priorityCalculatorService.calculatePriority(
                            conceptId,
                            adaptedFsrs,
                            memoryResult,
                            review.canvasId
                        );
                        const reviewCount = reviewCountMap.get(conceptId) || 1;

                        return {
                            id: String(review.id),
                            canvasId: review.canvasId,
                            canvasTitle: review.canvasTitle,
                            conceptName: review.conceptName,
                            priority: priorityResult.priorityTier,
                            dueDate: review.nextReviewDate || new Date(),
                            overdueDays: this.calculateOverdueDays(review.nextReviewDate),
                            memoryStrength: review.memoryStrength,
                            retentionRate: review.retentionRate,
                            reviewCount,
                            lastReviewDate: review.reviewDate,
                            status: 'pending',
                        };
                    })
                );
            }

            // Batch query subject/category from backend for each unique canvas
            try {
                const uniqueCanvasIds = [...new Set(tasks.map(t => t.canvasId))];
                const subjectMap = new Map<string, { subject: string; category: string }>();
                const apiBase = this.plugin.settings.aiBaseUrl || 'http://localhost:8000';

                await Promise.all(uniqueCanvasIds.map(async (canvasId) => {
                    try {
                        const resp = await requestUrl({
                            url: `${apiBase}/api/v1/canvas-meta/metadata?canvas_path=${encodeURIComponent(canvasId)}`,
                            method: 'GET',
                        });
                        if (resp.status === 200 && resp.json) {
                            subjectMap.set(canvasId, {
                                subject: resp.json.subject || 'general',
                                category: resp.json.category || 'general',
                            });
                        }
                    } catch { /* silent fail per canvas */ }
                }));

                for (const task of tasks) {
                    const info = subjectMap.get(task.canvasId);
                    if (info) {
                        task.subject = info.subject;
                        task.category = info.category;
                    }
                }
            } catch { /* silent fail for entire subject query */ }

            // Calculate dashboard statistics
            // Story 32.4 AC-32.4.2: Pass real streakDays to statistics calculation
            const statistics = this.calculateStatistics(tasks, dailyStats, streakDays);

            this.updateViewState({
                tasks,
                statistics,
                loading: false,
                lastUpdated: new Date(),
            });
        } catch (error) {
            console.error('ReviewDashboard: Failed to load data:', error);
            this.updateViewState({
                loading: false,
                error: (error as Error).message,
            });
        }
    }

    /**
     * Story 30.7 AC-30.7.3: Query concept memory from MemoryQueryService
     *
     * Returns real memory result if MemoryQueryService is available,
     * otherwise returns null for graceful degradation.
     *
     * @param conceptName - Concept name to query
     * @returns MemoryQueryResult or null
     */
    private async queryConceptMemory(conceptName: string): Promise<import('../services/MemoryQueryService').MemoryQueryResult | null> {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const memoryService = (this.plugin as any).memoryQueryService;
            if (!memoryService || !conceptName) {
                return null;
            }
            return await memoryService.queryConceptMemory(conceptName);
        } catch (error) {
            // Silent degradation - memory query failure shouldn't block dashboard
            if (this.plugin.settings?.debugMode) {
                console.warn('[ReviewDashboard] Memory query failed for:', conceptName, error);
            }
            return null;
        }
    }

    /**
     * Story 31.A.4 AC-31.A.4.3: Query FSRS state from FSRSStateQueryService
     *
     * Returns real FSRS state if FSRSStateQueryService is available,
     * otherwise returns null for graceful degradation.
     *
     * @param conceptId - Concept ID to query
     * @returns FSRSState or null
     */
    private async queryFSRSState(conceptId: string): Promise<import('../services/FSRSStateQueryService').FSRSState | null> {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const fsrsService = (this.plugin as any).fsrsStateQueryService;
            if (!fsrsService) {
                return null;
            }
            const response = await fsrsService.queryFSRSState(conceptId);
            return response?.fsrs_state || null;
        } catch (error) {
            // Silent degradation - FSRS query failure shouldn't block dashboard
            if (this.plugin.settings?.debugMode) {
                console.warn('[ReviewDashboard] FSRS state query failed for:', conceptId, error);
            }
            return null;
        }
    }

    /**
     * Batch query FSRS states for multiple concepts.
     * Delegates to FSRSStateQueryService.batchQueryFSRSStates() with built-in
     * concurrency control (max 5 parallel requests) and caching.
     *
     * @param conceptIds - Array of concept IDs to query
     * @returns Map of conceptId to FSRSStateQueryResponse
     */
    private async batchQueryFSRSStates(
        conceptIds: string[]
    ): Promise<Map<string, import('../services/FSRSStateQueryService').FSRSStateQueryResponse>> {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const fsrsService = (this.plugin as any).fsrsStateQueryService;
            if (!fsrsService) {
                return new Map();
            }
            return await fsrsService.batchQueryFSRSStates(conceptIds);
        } catch (error) {
            if (this.plugin.settings?.debugMode) {
                console.warn('[ReviewDashboard] Batch FSRS query failed:', error);
            }
            return new Map();
        }
    }

    /**
     * Story 31.A.4: Adapt FSRSState (from query service) to FSRSCardState (for priority calculator)
     *
     * FSRSState: { stability, difficulty, state: number(0-3), reps, lapses, retrievability, due }
     * FSRSCardState: { conceptId, stability, difficulty, lastReview: Date, nextReview: Date, ... }
     *
     * @param conceptId - Concept identifier
     * @param fsrs - Raw FSRS state from backend
     * @returns Adapted FSRSCardState for PriorityCalculatorService
     */
    private adaptFSRSStateToCardState(
        conceptId: string,
        fsrs: import('../services/FSRSStateQueryService').FSRSState
    ): import('../services/PriorityCalculatorService').FSRSCardState {
        const stateMap: Record<number, 'new' | 'learning' | 'review' | 'relearning'> = {
            0: 'new',
            1: 'learning',
            2: 'review',
            3: 'relearning',
        };

        const now = new Date();
        // Use real last_review from backend if available, otherwise estimate from stability
        const lastReview = fsrs.last_review
            ? new Date(fsrs.last_review)
            : (() => {
                const est = new Date(now);
                est.setDate(est.getDate() - Math.max(1, Math.floor(fsrs.stability)));
                return est;
            })();

        return {
            conceptId,
            stability: fsrs.stability,
            difficulty: fsrs.difficulty,
            lastReview,
            nextReview: fsrs.due ? new Date(fsrs.due) : now,
            reps: fsrs.reps,
            lapses: fsrs.lapses,
            state: stateMap[fsrs.state] || 'new',
        };
    }

    /**
     * @deprecated Use PriorityCalculatorService.calculatePriority() instead (Story 30.7)
     * Kept for backwards compatibility fallback only.
     */
    private calculatePriorityLegacy(review: any): TaskPriority {
        if (review.memoryStrength < 0.3) return 'critical';
        if (review.memoryStrength < 0.5) return 'high';
        if (review.memoryStrength < 0.7) return 'medium';
        return 'low';
    }

    private calculateOverdueDays(dueDate?: Date): number {
        if (!dueDate) return 0;
        const now = new Date();
        const due = new Date(dueDate);
        const diff = now.getTime() - due.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24));
    }

    /**
     * Calculate dashboard statistics from tasks and daily stats
     * Story 32.4 AC-32.4.2: Added streakDays parameter for real streak calculation
     *
     * @param tasks - Array of review tasks
     * @param dailyStats - Daily statistics from database
     * @param streakDays - Consecutive review days (Story 32.4)
     */
    private calculateStatistics(tasks: ReviewTask[], dailyStats: any, streakDays: number = 0): DashboardStatistics {
        const pendingTasks = tasks.filter((t) => t.status === 'pending');
        const overdueTasks = tasks.filter((t) => t.overdueDays > 0);

        return {
            todayPending: pendingTasks.length,
            todayCompleted: dailyStats.dailyReviews || 0,
            todayPostponed: 0,
            todayProgress:
                pendingTasks.length > 0
                    ? dailyStats.dailyReviews / (pendingTasks.length + dailyStats.dailyReviews)
                    : 1,
            averageScore: dailyStats.dailyAverageScore || 0,
            averageMemoryStrength: dailyStats.averageMemoryStrength || 0,
            averageRetentionRate: dailyStats.averageRetentionRate || 0,
            streakDays, // Story 32.4: Real streak from database
            totalConcepts:
                dailyStats.masteredConcepts + dailyStats.learningConcepts + dailyStats.strugglingConcepts,
            masteredConcepts: dailyStats.masteredConcepts || 0,
            learningConcepts: dailyStats.learningConcepts || 0,
            strugglingConcepts: dailyStats.strugglingConcepts || 0,
            masteryDistribution: [
                {
                    label: '已掌握',
                    count: dailyStats.masteredConcepts || 0,
                    percentage: 0,
                    color: '#4ade80',
                },
                {
                    label: '学习中',
                    count: dailyStats.learningConcepts || 0,
                    percentage: 0,
                    color: '#fbbf24',
                },
                {
                    label: '需加强',
                    count: dailyStats.strugglingConcepts || 0,
                    percentage: 0,
                    color: '#f87171',
                },
            ],
            recentActivities: [],
        };
    }

    // =========================================================================
    // State Management
    // =========================================================================

    private updateViewState(updates: Partial<DashboardViewState>): void {
        this.state = { ...this.state, ...updates };
        this.render();
    }

    private render(): void {
        const container = this.containerEl.children[1] as HTMLElement;
        if (container) {
            container.empty();
            this.renderDashboard(container);
        }
    }

    // =========================================================================
    // Rendering
    // =========================================================================

    private renderDashboard(container: HTMLElement): void {
        const dashboard = container.createDiv({ cls: 'review-dashboard' });

        // Header
        this.renderHeader(dashboard);

        // Tab navigation (Story 14.6)
        this.renderTabNavigation(dashboard);

        // Main content
        const content = dashboard.createDiv({ cls: 'dashboard-content' });

        // Render content based on active tab
        if (this.state.currentTab === 'history') {
            // History view (Story 14.6)
            this.renderHistoryContent(content);
        } else if (this.state.currentTab === 'verification') {
            // Verification canvas view (Story 14.13)
            this.renderVerificationContent(content);
        } else if (this.state.currentTab === 'cross-canvas') {
            // Cross-Canvas learning view (Epic 16)
            this.renderCrossCanvasContent(content);
        } else {
            // Task list (left side)
            const taskListContainer = content.createDiv({ cls: 'task-list-container' });
            this.renderTaskList(taskListContainer);

            // Sidebar (right side)
            const sidebar = content.createDiv({ cls: 'dashboard-sidebar' });
            this.renderStatistics(sidebar);
            this.renderQuickActions(sidebar);
        }
    }

    /**
     * Render tab navigation (Story 14.6 + Story 14.13 + Epic 16)
     * Extended to include verification canvas and cross-canvas learning tabs
     */
    private renderTabNavigation(container: HTMLElement): void {
        const tabNav = container.createDiv({ cls: 'dashboard-tabs' });

        // Tasks tab
        const tasksTab = tabNav.createDiv({
            cls: `dashboard-tab ${this.state.currentTab === 'tasks' ? 'active' : ''}`,
        });
        const tasksIcon = tasksTab.createSpan({ cls: 'tab-icon' });
        setIcon(tasksIcon, 'list-checks');
        tasksTab.createSpan({ text: '今日任务', cls: 'tab-label' });
        tasksTab.addEventListener('click', () => {
            console.log('[ReviewDashboard] Tasks tab clicked');
            this.switchTab('tasks');
        });

        // History tab
        const historyTab = tabNav.createDiv({
            cls: `dashboard-tab ${this.state.currentTab === 'history' ? 'active' : ''}`,
        });
        const historyIcon = historyTab.createSpan({ cls: 'tab-icon' });
        setIcon(historyIcon, 'history');
        historyTab.createSpan({ text: '历史记录', cls: 'tab-label' });
        historyTab.addEventListener('click', () => {
            console.log('[ReviewDashboard] History tab clicked');
            this.switchTab('history');
        });

        // Verification tab (Story 14.13)
        const verificationTab = tabNav.createDiv({
            cls: `dashboard-tab ${this.state.currentTab === 'verification' ? 'active' : ''}`,
        });
        const verificationIcon = verificationTab.createSpan({ cls: 'tab-icon' });
        setIcon(verificationIcon, 'clipboard-check');
        verificationTab.createSpan({ text: '检验白板', cls: 'tab-label' });
        verificationTab.addEventListener('click', () => {
            console.log('[ReviewDashboard] Verification tab clicked');
            this.switchTab('verification');
        });

        // Cross-Canvas tab (Epic 16)
        const crossCanvasTab = tabNav.createDiv({
            cls: `dashboard-tab ${this.state.currentTab === 'cross-canvas' ? 'active' : ''}`,
        });
        const crossCanvasIcon = crossCanvasTab.createSpan({ cls: 'tab-icon' });
        setIcon(crossCanvasIcon, 'git-branch');
        crossCanvasTab.createSpan({ text: '跨Canvas学习', cls: 'tab-label' });
        crossCanvasTab.addEventListener('click', () => {
            console.log('[ReviewDashboard] Cross-Canvas tab clicked');
            this.switchTab('cross-canvas');
        });
    }

    /**
     * Switch between tabs (Story 14.6 + Story 14.13 + Epic 16)
     */
    private async switchTab(tab: DashboardTab): Promise<void> {
        console.log('[ReviewDashboard] switchTab called with:', tab);
        if (this.state.currentTab === tab) return;

        this.updateViewState({ currentTab: tab });

        if (tab === 'history') {
            await this.loadHistoryData();
        } else if (tab === 'verification') {
            await this.loadVerificationData();
        } else if (tab === 'cross-canvas') {
            await this.loadCrossCanvasData();
        }
    }

    /**
     * Load history data (Story 14.6)
     * Story 34.4: Added showAll parameter for pagination
     * @param showAll - If true, load all records; if false, limit to 5 (default)
     */
    private async loadHistoryData(showAll: boolean = false): Promise<void> {
        const historyState = { ...this.state.historyState, loading: true };
        this.updateViewState({ historyState });

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                this.historyService.setDataManager(dataManager);
            }

            // Story 34.4: Pass showAll parameter to loadHistoryState
            const newHistoryState = await this.historyService.loadHistoryState(
                this.state.historyState.timeRange,
                showAll
            );

            this.updateViewState({ historyState: newHistoryState });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load history:', error);
            this.updateViewState({
                historyState: {
                    ...DEFAULT_HISTORY_STATE,
                    timeRange: this.state.historyState.timeRange,
                    loading: false,
                    hasMore: false,
                    totalCount: 0,
                    showAll: false,
                },
            });
        }
    }

    /**
     * Story 34.4: Toggle between showing limited (5) and all history entries
     */
    private async toggleShowAllHistory(): Promise<void> {
        const currentShowAll = this.state.historyState.showAll || false;
        await this.loadHistoryData(!currentShowAll);
    }

    /**
     * Load verification data (Story 14.13)
     */
    private async loadVerificationData(): Promise<void> {
        const verificationState = { ...this.state.verificationState, loading: true };
        this.updateViewState({ verificationState });

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                this.verificationService.setDataManager(dataManager);
            }

            const viewState = await this.verificationService.getViewState();
            this.updateViewState({ verificationState: viewState });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load verification data:', error);
            this.updateViewState({
                verificationState: {
                    ...DEFAULT_VERIFICATION_STATE,
                    loading: false,
                },
            });
        }
    }

    /**
     * Load cross-canvas data (Epic 16)
     */
    private async loadCrossCanvasData(): Promise<void> {
        const crossCanvasState = { ...this.state.crossCanvasState, loading: true };
        this.updateViewState({ crossCanvasState });

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                this.crossCanvasService.setDataManager(dataManager);
            }

            const viewState = await this.crossCanvasService.getViewState();
            this.updateViewState({ crossCanvasState: viewState });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load cross-canvas data:', error);
            this.updateViewState({
                crossCanvasState: {
                    ...DEFAULT_CROSS_CANVAS_STATE,
                    loading: false,
                },
            });
        }
    }

    /**
     * Render history content (Story 14.6)
     */
    private renderHistoryContent(container: HTMLElement): void {
        const historyContainer = container.createDiv({ cls: 'history-container' });

        // Time range selector
        this.renderTimeRangeSelector(historyContainer);

        // Daily stats chart
        this.renderDailyStatsChart(historyContainer);

        // Canvas trends
        this.renderCanvasTrends(historyContainer);

        // History list
        this.renderHistoryList(historyContainer);
    }

    /**
     * Render time range selector (Story 14.6)
     */
    private renderTimeRangeSelector(container: HTMLElement): void {
        const selector = container.createDiv({ cls: 'time-range-selector' });

        const ranges: { value: HistoryTimeRange; label: string }[] = [
            { value: '7d', label: '最近7天' },
            { value: '30d', label: '最近30天' },
        ];

        ranges.forEach((range) => {
            const btn = selector.createEl('button', {
                text: range.label,
                cls: `time-range-btn ${this.state.historyState.timeRange === range.value ? 'active' : ''}`,
            });
            btn.addEventListener('click', async () => {
                if (this.state.historyState.timeRange !== range.value) {
                    this.updateViewState({
                        historyState: {
                            ...this.state.historyState,
                            timeRange: range.value,
                        },
                    });
                    await this.loadHistoryData();
                }
            });
        });
    }

    /**
     * Render daily statistics chart (Story 14.6)
     */
    private renderDailyStatsChart(container: HTMLElement): void {
        const chartContainer = container.createDiv({ cls: 'daily-stats-chart' });
        chartContainer.createEl('h3', { text: '每日复习统计', cls: 'chart-title' });

        if (this.state.historyState.loading) {
            chartContainer.createDiv({ text: '加载中...', cls: 'chart-loading' });
            return;
        }

        const { dailyStats } = this.state.historyState;
        if (dailyStats.length === 0) {
            chartContainer.createDiv({ text: '暂无数据', cls: 'chart-empty' });
            return;
        }

        // Create CSS bar chart
        const chart = chartContainer.createDiv({ cls: 'bar-chart' });
        const maxCount = Math.max(...dailyStats.map((d) => d.conceptCount), 1);

        dailyStats.forEach((stat) => {
            const bar = chart.createDiv({ cls: 'bar-item' });
            const barHeight = (stat.conceptCount / maxCount) * 100;
            const barFill = bar.createDiv({ cls: 'bar-fill' });
            barFill.style.height = `${barHeight}%`;

            // Color based on average score
            if (stat.averageScore >= 4) {
                barFill.addClass('bar-excellent');
            } else if (stat.averageScore >= 3) {
                barFill.addClass('bar-good');
            } else {
                barFill.addClass('bar-needs-work');
            }

            bar.createDiv({
                text: stat.conceptCount.toString(),
                cls: 'bar-value',
            });
            bar.createDiv({
                text: stat.date.slice(5), // MM-DD
                cls: 'bar-label',
            });
        });

        // Summary stats
        const summary = chartContainer.createDiv({ cls: 'chart-summary' });
        const totalConcepts = dailyStats.reduce((sum, d) => sum + d.conceptCount, 0);
        const avgScore =
            dailyStats.filter((d) => d.conceptCount > 0).reduce((sum, d) => sum + d.averageScore, 0) /
            dailyStats.filter((d) => d.conceptCount > 0).length || 0;

        summary.createSpan({ text: `总计复习: ${totalConcepts} 个概念`, cls: 'summary-item' });
        summary.createSpan({
            text: `平均评分: ${avgScore.toFixed(1)} 分`,
            cls: 'summary-item',
        });
    }

    /**
     * Render canvas review trends (Story 14.6)
     */
    private renderCanvasTrends(container: HTMLElement): void {
        const trendsContainer = container.createDiv({ cls: 'canvas-trends' });
        trendsContainer.createEl('h3', { text: '白板复习趋势', cls: 'trends-title' });

        if (this.state.historyState.loading) {
            trendsContainer.createDiv({ text: '加载中...', cls: 'trends-loading' });
            return;
        }

        const { canvasTrends } = this.state.historyState;
        if (canvasTrends.length === 0) {
            trendsContainer.createDiv({ text: '暂无白板复习数据', cls: 'trends-empty' });
            return;
        }

        const trendsList = trendsContainer.createDiv({ cls: 'trends-list' });

        canvasTrends.slice(0, 5).forEach((trend) => {
            const trendItem = trendsList.createDiv({ cls: 'trend-item' });

            // Canvas name
            trendItem.createDiv({ text: trend.canvasTitle, cls: 'trend-title' });

            // Progress bar
            const progressBar = trendItem.createDiv({ cls: 'trend-progress-bar' });
            const progressFill = progressBar.createDiv({ cls: 'trend-progress-fill' });
            progressFill.style.width = `${trend.progressRate}%`;

            // Progress rate with trend arrow
            const progressText = trendItem.createDiv({ cls: 'trend-progress-text' });
            const trendIcon = progressText.createSpan({ cls: 'trend-icon' });
            if (trend.trend === 'up') {
                setIcon(trendIcon, 'trending-up');
                trendIcon.addClass('trend-up');
            } else if (trend.trend === 'down') {
                setIcon(trendIcon, 'trending-down');
                trendIcon.addClass('trend-down');
            } else {
                setIcon(trendIcon, 'minus');
                trendIcon.addClass('trend-stable');
            }
            progressText.createSpan({ text: `${trend.progressRate}%`, cls: 'progress-value' });

            // Session count
            trendItem.createDiv({
                text: `${trend.sessions.length} 次检验`,
                cls: 'trend-sessions',
            });
        });
    }

    /**
     * Render history list (Story 14.6)
     * Story 34.4: Added "Show All" button for pagination
     */
    private renderHistoryList(container: HTMLElement): void {
        const listContainer = container.createDiv({ cls: 'history-list-container' });

        // Story 34.4: Show count info in title
        const { entries, hasMore, totalCount, showAll } = this.state.historyState;
        const countText = totalCount && totalCount > 0
            ? ` (${showAll ? '全部' : `最近${entries.length}条`}/${totalCount})`
            : '';
        listContainer.createEl('h3', { text: `复习记录${countText}`, cls: 'history-list-title' });

        if (this.state.historyState.loading) {
            listContainer.createDiv({ text: '加载中...', cls: 'history-loading' });
            return;
        }

        if (entries.length === 0) {
            listContainer.createDiv({ text: '暂无复习记录', cls: 'history-empty' });
            return;
        }

        const historyList = listContainer.createDiv({ cls: 'history-list' });

        // Group by date
        const groupedEntries = this.groupEntriesByDate(entries);

        Object.entries(groupedEntries)
            .slice(0, showAll ? undefined : 7) // Story 34.4: Show all days when showAll=true
            .forEach(([date, dateEntries]) => {
                const dateGroup = historyList.createDiv({ cls: 'history-date-group' });
                dateGroup.createDiv({ text: date, cls: 'history-date-header' });

                dateEntries.forEach((entry) => {
                    this.renderHistoryEntry(dateGroup, entry);
                });
            });

        // Story 34.4 AC2: "Show All" button when hasMore=true
        if (hasMore && !showAll) {
            const showAllBtn = listContainer.createEl('button', {
                text: `显示全部 (${totalCount || 0}条)`,
                cls: 'history-show-all-btn',
            });
            showAllBtn.addEventListener('click', () => {
                this.toggleShowAllHistory();
            });
        } else if (showAll && totalCount && totalCount > 5) {
            // Show "Collapse" button when showing all
            const collapseBtn = listContainer.createEl('button', {
                text: '收起',
                cls: 'history-collapse-btn',
            });
            collapseBtn.addEventListener('click', () => {
                this.toggleShowAllHistory();
            });
        }
    }

    /**
     * Render single history entry (Story 14.6)
     */
    private renderHistoryEntry(container: HTMLElement, entry: HistoryEntry): void {
        const entryEl = container.createDiv({ cls: 'history-entry' });

        // Mode badge
        const modeBadge = entryEl.createSpan({
            text: entry.mode === 'fresh' ? '全新检验' : '针对性复习',
            cls: `mode-badge mode-${entry.mode}`,
        });

        // Concept name
        entryEl.createSpan({ text: entry.conceptName, cls: 'entry-concept' });

        // Canvas name
        entryEl.createSpan({
            text: `@ ${entry.canvasTitle}`,
            cls: 'entry-canvas',
        });

        // Score
        const scoreEl = entryEl.createSpan({ cls: 'entry-score' });
        for (let i = 0; i < 5; i++) {
            const star = scoreEl.createSpan({ cls: 'score-star' });
            setIcon(star, i < entry.score ? 'star' : 'star');
            if (i < entry.score) {
                star.addClass('filled');
            }
        }

        // Memory strength
        const strengthEl = entryEl.createDiv({ cls: 'entry-strength' });
        const strengthBar = strengthEl.createDiv({ cls: 'strength-bar' });
        strengthBar.style.width = `${entry.memoryStrength * 100}%`;

        // Click to open canvas
        entryEl.addEventListener('click', () => {
            if (entry.canvasPath) {
                this.app.workspace.openLinkText(entry.canvasPath, '', false);
            }
        });
    }

    /**
     * Group history entries by date
     */
    private groupEntriesByDate(entries: HistoryEntry[]): Record<string, HistoryEntry[]> {
        const grouped: Record<string, HistoryEntry[]> = {};

        entries.forEach((entry) => {
            const dateStr = entry.reviewDate.toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric',
                weekday: 'short',
            });
            if (!grouped[dateStr]) {
                grouped[dateStr] = [];
            }
            grouped[dateStr].push(entry);
        });

        return grouped;
    }

    // =========================================================================
    // Verification Canvas Tab (Story 14.13)
    // =========================================================================

    /**
     * Render verification canvas content (Story 14.13)
     */
    private renderVerificationContent(container: HTMLElement): void {
        const verificationContainer = container.createDiv({ cls: 'verification-container' });

        // Loading state
        if (this.state.verificationState.loading) {
            verificationContainer.createDiv({ text: '加载中...', cls: 'verification-loading' });
            return;
        }

        // Header section
        this.renderVerificationHeader(verificationContainer);

        // Recent verification canvases list
        this.renderVerificationList(verificationContainer);

        // Multi-review comparison chart
        this.renderVerificationChart(verificationContainer);

        // Generate new verification canvas button
        this.renderVerificationActions(verificationContainer);
    }

    /**
     * Render verification header (Story 14.13)
     */
    private renderVerificationHeader(container: HTMLElement): void {
        const header = container.createDiv({ cls: 'verification-header' });
        header.createEl('h3', { text: '📋 检验白板', cls: 'verification-title' });

        const stats = this.state.verificationState.relations;
        const statsContainer = header.createDiv({ cls: 'verification-stats' });
        statsContainer.createSpan({
            text: `共 ${stats.length} 个检验白板`,
            cls: 'verification-stat',
        });
    }

    /**
     * Render verification canvas list (Story 14.13)
     */
    private renderVerificationList(container: HTMLElement): void {
        const listContainer = container.createDiv({ cls: 'verification-list-section' });
        listContainer.createEl('h4', { text: '🔄 最近检验白板', cls: 'section-title' });

        const { relations } = this.state.verificationState;

        if (relations.length === 0) {
            listContainer.createDiv({
                text: '暂无检验白板，点击下方按钮生成',
                cls: 'verification-empty',
            });
            return;
        }

        const list = listContainer.createDiv({ cls: 'verification-list' });

        relations.slice(0, 5).forEach((relation) => {
            this.renderVerificationItem(list, relation);
        });
    }

    /**
     * Render single verification canvas item (Story 14.13)
     */
    private renderVerificationItem(container: HTMLElement, relation: VerificationCanvasRelation): void {
        const item = container.createDiv({ cls: 'verification-item' });

        // Canvas info
        const info = item.createDiv({ cls: 'verification-item-info' });
        info.createSpan({
            text: relation.verificationCanvasTitle,
            cls: 'verification-item-title',
        });

        // Mode badge
        const modeBadge = info.createSpan({
            text: relation.reviewMode === 'fresh' ? '全新检验' : '针对性复习',
            cls: `mode-badge mode-${relation.reviewMode}`,
        });

        // Original canvas reference
        info.createDiv({
            text: `原始Canvas: ${relation.originalCanvasTitle}`,
            cls: 'verification-item-source',
        });

        // Stats
        const stats = item.createDiv({ cls: 'verification-item-stats' });

        // Completion rate
        const completion = Math.round((relation.completionRate || 0) * 100);
        stats.createSpan({
            text: `完成度: ${completion}%`,
            cls: 'verification-stat-item',
        });

        // Session count
        stats.createSpan({
            text: `${relation.sessionCount}次复习`,
            cls: 'verification-stat-item',
        });

        // Highest score from sessions (Story 31.7 AC-31.7.3)
        if (relation.sessions && relation.sessions.length > 0) {
            const highestPassRate = Math.max(...relation.sessions.map((s) => s.passRate));
            const highestScore = (highestPassRate * 5).toFixed(1);
            stats.createSpan({
                text: `最高分: ${highestScore}/5`,
                cls: 'verification-stat-item verification-stat-highest',
            });
        }

        // Most recent verification time (Story 31.7 AC-31.7.3)
        if (relation.sessions && relation.sessions.length > 0) {
            const lastSession = relation.sessions[relation.sessions.length - 1];
            const lastDateStr = lastSession.date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric',
            });
            stats.createSpan({
                text: `最近: ${lastDateStr}`,
                cls: 'verification-stat-item verification-stat-recent',
            });
        }

        // Score
        if (relation.currentScore !== undefined) {
            stats.createSpan({
                text: `平均分: ${relation.currentScore.toFixed(1)}/5`,
                cls: 'verification-stat-item',
            });
        }

        // Date
        const dateStr = relation.generatedDate.toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
        });
        stats.createSpan({
            text: dateStr,
            cls: 'verification-stat-date',
        });

        // Delete button (Story 31.7 AC-31.7.5)
        const deleteBtn = item.createDiv({ cls: 'verification-item-delete' });
        setIcon(deleteBtn, 'trash-2');
        deleteBtn.setAttribute('title', '删除检验白板记录');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering item click
            this.confirmDeleteVerification(relation);
        });

        // Click to open
        item.addEventListener('click', () => {
            if (relation.verificationCanvasPath) {
                this.app.workspace.openLinkText(relation.verificationCanvasPath, '', false);
            }
        });
    }

    /**
     * Confirm and delete verification canvas relation (Story 31.7 AC-31.7.5)
     */
    private async confirmDeleteVerification(relation: VerificationCanvasRelation): Promise<void> {
        const confirmed = await this.showConfirmDialog(
            '删除检验白板记录',
            `确定要删除"${relation.verificationCanvasTitle}"的检验记录吗？此操作不可撤销。`
        );

        if (confirmed) {
            try {
                await this.verificationService.deleteRelation(relation.id);
                new Notice('检验白板记录已删除');
                await this.loadVerificationData();
            } catch (error) {
                console.error('[ReviewDashboard] Failed to delete verification:', error);
                new Notice('删除失败，请重试');
            }
        }
    }

    /**
     * Render verification comparison chart (Story 14.13)
     */
    private renderVerificationChart(container: HTMLElement): void {
        const chartContainer = container.createDiv({ cls: 'verification-chart-section' });
        chartContainer.createEl('h4', { text: '📊 多次检验对比', cls: 'section-title' });

        const { relations } = this.state.verificationState;

        if (relations.length === 0 || relations.every((r) => r.sessions.length === 0)) {
            chartContainer.createDiv({
                text: '完成至少一次检验后显示趋势图',
                cls: 'verification-chart-empty',
            });
            return;
        }

        // Simple bar chart for recent sessions
        const chartArea = chartContainer.createDiv({ cls: 'verification-chart' });

        relations.slice(0, 3).forEach((relation) => {
            if (relation.sessions.length > 0) {
                const relChart = chartArea.createDiv({ cls: 'relation-chart' });
                relChart.createDiv({
                    text: relation.verificationCanvasTitle,
                    cls: 'relation-chart-label',
                });

                const bars = relChart.createDiv({ cls: 'relation-chart-bars' });
                relation.sessions.slice(-5).forEach((session) => {
                    const bar = bars.createDiv({ cls: 'session-bar' });
                    bar.style.height = `${session.passRate * 100}%`;
                    bar.setAttribute('title', `通过率: ${Math.round(session.passRate * 100)}%`);
                });
            }
        });
    }

    /**
     * Render verification actions (Story 14.13)
     */
    private renderVerificationActions(container: HTMLElement): void {
        const actionsContainer = container.createDiv({ cls: 'verification-actions' });

        const generateBtn = actionsContainer.createEl('button', {
            text: '➕ 生成新检验白板',
            cls: 'mod-cta verification-generate-btn',
        });

        generateBtn.addEventListener('click', () => {
            this.showReviewModeDialog();
        });
    }

    // =========================================================================
    // Cross-Canvas Learning Tab (Epic 16)
    // =========================================================================

    /**
     * Render cross-canvas learning content (Epic 16)
     */
    private renderCrossCanvasContent(container: HTMLElement): void {
        const crossCanvasContainer = container.createDiv({ cls: 'cross-canvas-container' });

        // Loading state
        if (this.state.crossCanvasState.loading) {
            crossCanvasContainer.createDiv({ text: '加载中...', cls: 'cross-canvas-loading' });
            return;
        }

        // Canvas association configuration
        this.renderCanvasAssociationConfig(crossCanvasContainer);

        // Knowledge graph search
        this.renderKnowledgeGraphSearch(crossCanvasContainer);

        // Knowledge transfer paths
        this.renderKnowledgePaths(crossCanvasContainer);

        // Existing associations list
        this.renderAssociationsList(crossCanvasContainer);

        // Textbook mount section (Epic 21: 多格式教材挂载系统)
        this.renderTextbookMountSection(crossCanvasContainer);
    }

    /**
     * Render canvas association configuration (Epic 16)
     */
    private renderCanvasAssociationConfig(container: HTMLElement): void {
        const configSection = container.createDiv({ cls: 'cross-canvas-config' });
        configSection.createEl('h3', { text: '📚 Canvas关联配置', cls: 'section-title' });

        // Canvas selector row
        const selectorRow = configSection.createDiv({ cls: 'canvas-selector-row' });

        // Source canvas selector
        const sourceGroup = selectorRow.createDiv({ cls: 'canvas-selector-group' });
        sourceGroup.createSpan({ text: '选择教材Canvas:', cls: 'selector-label' });
        const sourceSelect = sourceGroup.createEl('select', { cls: 'canvas-select source-canvas' });
        sourceSelect.createEl('option', { text: '-- 选择Canvas --', value: '' });

        // Target canvas selector
        const targetGroup = selectorRow.createDiv({ cls: 'canvas-selector-group' });
        targetGroup.createSpan({ text: '选择习题Canvas:', cls: 'selector-label' });
        const targetSelect = targetGroup.createEl('select', { cls: 'canvas-select target-canvas' });
        targetSelect.createEl('option', { text: '-- 选择Canvas --', value: '' });

        // Load canvas files
        this.loadCanvasFilesIntoSelectors(sourceSelect, targetSelect);

        // Relationship type
        const relationRow = configSection.createDiv({ cls: 'relation-type-row' });
        relationRow.createSpan({ text: '关联类型:', cls: 'relation-label' });

        const relationTypes = [
            { value: 'prerequisite', label: '前置概念' },
            { value: 'related', label: '相关主题' },
            { value: 'application', label: '应用练习' },
        ];

        relationTypes.forEach((type, index) => {
            const radioWrapper = relationRow.createDiv({ cls: 'radio-wrapper' });
            const radio = radioWrapper.createEl('input', {
                type: 'radio',
                attr: { name: 'relationshipType', value: type.value, id: `rel-${type.value}` },
            });
            if (index === 0) radio.checked = true;
            radioWrapper.createEl('label', {
                text: type.label,
                attr: { for: `rel-${type.value}` },
            });
        });

        // Create association button
        const createBtn = configSection.createEl('button', {
            text: '创建关联',
            cls: 'mod-cta create-association-btn',
        });

        createBtn.addEventListener('click', async () => {
            const sourceValue = (sourceSelect as HTMLSelectElement).value;
            const targetValue = (targetSelect as HTMLSelectElement).value;
            const relationTypeEl = configSection.querySelector(
                'input[name="relationshipType"]:checked'
            ) as HTMLInputElement;
            const relationType = relationTypeEl?.value || 'related';

            if (!sourceValue || !targetValue) {
                new Notice('请选择两个Canvas文件');
                return;
            }

            if (sourceValue === targetValue) {
                new Notice('请选择不同的Canvas文件');
                return;
            }

            try {
                await this.crossCanvasService.createCanvasAssociation(
                    sourceValue,
                    targetValue,
                    relationType as 'prerequisite' | 'related' | 'application'
                );
                new Notice('✅ Canvas关联创建成功');
                await this.loadCrossCanvasData();
            } catch (error) {
                new Notice('❌ 创建关联失败');
                console.error('[ReviewDashboard] Failed to create association:', error);
            }
        });
    }

    /**
     * Load canvas files into selectors
     */
    private async loadCanvasFilesIntoSelectors(
        sourceSelect: HTMLSelectElement,
        targetSelect: HTMLSelectElement
    ): Promise<void> {
        try {
            const canvasFiles = await this.crossCanvasService.getAllCanvasFiles();

            canvasFiles.forEach((file) => {
                const title = file.basename;
                sourceSelect.createEl('option', { text: title, value: file.path });
                targetSelect.createEl('option', { text: title, value: file.path });
            });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load canvas files:', error);
        }
    }

    /**
     * Render knowledge graph search (Epic 16)
     */
    private renderKnowledgeGraphSearch(container: HTMLElement): void {
        const searchSection = container.createDiv({ cls: 'cross-canvas-search' });
        searchSection.createEl('h3', { text: '🔍 知识图谱查询', cls: 'section-title' });

        // Search input
        const searchRow = searchSection.createDiv({ cls: 'search-row' });
        const searchInput = searchRow.createEl('input', {
            type: 'text',
            placeholder: '输入概念名称...',
            cls: 'concept-search-input',
        });

        const searchBtn = searchRow.createEl('button', {
            text: '搜索',
            cls: 'search-btn',
        });

        // Results container
        const resultsContainer = searchSection.createDiv({ cls: 'search-results' });

        // Show existing search results
        const { searchResults, searchQuery } = this.state.crossCanvasState;
        if (searchQuery && searchResults.length > 0) {
            this.renderSearchResults(resultsContainer, searchResults);
        } else if (searchQuery && searchResults.length === 0) {
            resultsContainer.createDiv({
                text: `未找到与"${searchQuery}"相关的概念`,
                cls: 'search-empty',
            });
        }

        // Search handler
        searchBtn.addEventListener('click', async () => {
            const query = (searchInput as HTMLInputElement).value.trim();
            if (!query) {
                new Notice('请输入搜索内容');
                return;
            }

            try {
                const results = await this.crossCanvasService.searchConceptAcrossCanvas(query);
                this.updateViewState({
                    crossCanvasState: {
                        ...this.state.crossCanvasState,
                        searchQuery: query,
                        searchResults: results,
                    },
                });
            } catch (error) {
                console.error('[ReviewDashboard] Search failed:', error);
                new Notice('搜索失败');
            }
        });

        // Enter key handler
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }

    /**
     * Render search results (Epic 16)
     */
    private renderSearchResults(container: HTMLElement, results: CrossCanvasSearchResult[]): void {
        container.empty();

        results.forEach((result) => {
            const resultItem = container.createDiv({ cls: 'search-result-item' });

            // Concept header
            const header = resultItem.createDiv({ cls: 'result-header' });
            header.createSpan({ text: result.concept, cls: 'result-concept' });
            header.createSpan({
                text: `在 ${result.totalCount} 个Canvas中找到`,
                cls: 'result-count',
            });

            // Occurrences
            const occurrences = resultItem.createDiv({ cls: 'result-occurrences' });
            result.canvasOccurrences.slice(0, 3).forEach((occ) => {
                const occItem = occurrences.createDiv({ cls: 'occurrence-item' });
                occItem.createSpan({ text: occ.canvasTitle, cls: 'occ-canvas' });
                occItem.createDiv({
                    text: occ.nodeText.substring(0, 100) + '...',
                    cls: 'occ-preview',
                });

                occItem.addEventListener('click', () => {
                    this.app.workspace.openLinkText(occ.canvasPath, '', false);
                });
            });

            if (result.canvasOccurrences.length > 3) {
                occurrences.createDiv({
                    text: `还有 ${result.canvasOccurrences.length - 3} 个结果...`,
                    cls: 'more-results',
                });
            }
        });
    }

    /**
     * Render knowledge paths (Epic 16)
     */
    private renderKnowledgePaths(container: HTMLElement): void {
        const pathsSection = container.createDiv({ cls: 'knowledge-paths-section' });
        pathsSection.createEl('h3', { text: '🗺️ 知识迁移路径', cls: 'section-title' });

        const { knowledgePaths } = this.state.crossCanvasState;

        if (knowledgePaths.length === 0) {
            const emptyMsg = pathsSection.createDiv({ cls: 'paths-empty' });
            emptyMsg.createSpan({ text: '暂无知识路径，' });

            const createLink = emptyMsg.createEl('a', { text: '点击创建' });
            createLink.addEventListener('click', () => {
                this.showCreatePathDialog();
            });

            return;
        }

        const pathsList = pathsSection.createDiv({ cls: 'paths-list' });

        knowledgePaths.forEach((path) => {
            this.renderKnowledgePath(pathsList, path);
        });
    }

    /**
     * Render single knowledge path (Epic 16)
     */
    private renderKnowledgePath(container: HTMLElement, path: KnowledgePath): void {
        const pathItem = container.createDiv({ cls: 'path-item' });

        // Path header
        const header = pathItem.createDiv({ cls: 'path-header' });
        header.createSpan({ text: path.name, cls: 'path-name' });

        // Progress bar
        const progress = Math.round(path.completionProgress * 100);
        const progressBar = header.createDiv({ cls: 'path-progress' });
        const progressFill = progressBar.createDiv({ cls: 'progress-fill' });
        progressFill.style.width = `${progress}%`;
        header.createSpan({ text: `${progress}%`, cls: 'progress-text' });

        // Path nodes (sequence)
        const nodesContainer = pathItem.createDiv({ cls: 'path-nodes' });

        path.nodes.forEach((node, index) => {
            const nodeEl = nodesContainer.createDiv({
                cls: `path-node ${node.isCompleted ? 'completed' : ''}`,
            });

            nodeEl.createSpan({ text: node.canvasTitle, cls: 'node-title' });

            if (index < path.nodes.length - 1) {
                nodesContainer.createSpan({ text: '→', cls: 'path-arrow' });
            }

            nodeEl.addEventListener('click', () => {
                this.app.workspace.openLinkText(node.canvasPath, '', false);
            });
        });

        // Recommended next
        if (path.recommendedNext && !path.recommendedNext.isCompleted) {
            const recommendedEl = pathItem.createDiv({ cls: 'recommended-next' });
            recommendedEl.createSpan({ text: '建议下一步: ' });
            const nextLink = recommendedEl.createEl('a', {
                text: path.recommendedNext.canvasTitle,
            });
            nextLink.addEventListener('click', () => {
                this.app.workspace.openLinkText(path.recommendedNext!.canvasPath, '', false);
            });
        }
    }

    /**
     * Render associations list (Epic 16)
     */
    private renderAssociationsList(container: HTMLElement): void {
        const listSection = container.createDiv({ cls: 'associations-list-section' });
        listSection.createEl('h3', { text: '🔗 已建立的关联', cls: 'section-title' });

        const { associations } = this.state.crossCanvasState;

        if (associations.length === 0) {
            listSection.createDiv({
                text: '暂无Canvas关联',
                cls: 'associations-empty',
            });
            return;
        }

        const list = listSection.createDiv({ cls: 'associations-list' });

        associations.forEach((assoc) => {
            this.renderAssociationItem(list, assoc);
        });
    }

    /**
     * Render single association item (Epic 16)
     */
    private renderAssociationItem(container: HTMLElement, assoc: CrossCanvasAssociation): void {
        const item = container.createDiv({ cls: 'association-item' });

        // Canvas pair
        const pair = item.createDiv({ cls: 'association-pair' });
        pair.createSpan({ text: assoc.sourceCanvasTitle, cls: 'source-canvas' });

        const relationLabel =
            assoc.relationshipType === 'prerequisite'
                ? '→ 前置 →'
                : assoc.relationshipType === 'related'
                  ? '↔ 相关 ↔'
                  : '→ 应用 →';
        pair.createSpan({ text: relationLabel, cls: 'relation-arrow' });
        pair.createSpan({ text: assoc.targetCanvasTitle, cls: 'target-canvas' });

        // Common concepts
        if (assoc.commonConcepts.length > 0) {
            const concepts = item.createDiv({ cls: 'common-concepts' });
            concepts.createSpan({ text: '共同概念: ' });
            concepts.createSpan({
                text: assoc.commonConcepts.slice(0, 3).join(', '),
                cls: 'concept-tags',
            });
            if (assoc.commonConcepts.length > 3) {
                concepts.createSpan({
                    text: ` +${assoc.commonConcepts.length - 3}`,
                    cls: 'more-concepts',
                });
            }
        }

        // Confidence
        const confidence = item.createDiv({ cls: 'association-confidence' });
        confidence.createSpan({
            text: `置信度: ${Math.round(assoc.confidence * 100)}%`,
        });

        // Delete button
        const deleteBtn = item.createEl('button', { cls: 'delete-association-btn' });
        setIcon(deleteBtn, 'trash-2');
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                await this.crossCanvasService.deleteAssociation(assoc.id);
                new Notice('关联已删除');
                await this.loadCrossCanvasData();
            } catch (error) {
                console.error('[ReviewDashboard] Failed to delete association:', error);
                new Notice('删除失败');
            }
        });
    }

    /**
     * Show dialog to create knowledge path
     */
    private showCreatePathDialog(): void {
        new Notice('知识路径创建功能开发中...');
        // TODO: Implement path creation dialog
    }

    // =========================================================================
    // Textbook Mount Section (Epic 21: 多格式教材挂载系统)
    // =========================================================================

    /**
     * Render textbook mount section
     * Allows users to mount PDF/Markdown/Canvas files as textbook references
     */
    private renderTextbookMountSection(container: HTMLElement): void {
        const mountSection = container.createDiv({ cls: 'textbook-mount-section' });
        mountSection.createEl('h3', { text: '📖 挂载教材', cls: 'section-title' });

        // Mount form
        this.renderTextbookMountForm(mountSection);

        // Mounted textbooks list
        this.renderMountedTextbooksList(mountSection);
    }

    /**
     * Render textbook mount form
     */
    private renderTextbookMountForm(container: HTMLElement): void {
        const formDiv = container.createDiv({ cls: 'textbook-mount-form' });

        // File type selector
        const typeGroup = formDiv.createDiv({ cls: 'mount-type-group' });
        typeGroup.createSpan({ text: '文件类型:', cls: 'mount-label' });

        const typeSelect = typeGroup.createEl('select', { cls: 'mount-type-select' });
        typeSelect.createEl('option', { text: '全部', value: 'all' });
        typeSelect.createEl('option', { text: 'PDF 文件', value: 'pdf' });
        typeSelect.createEl('option', { text: 'Markdown', value: 'markdown' });
        typeSelect.createEl('option', { text: 'Canvas', value: 'canvas' });

        // File selector
        const fileGroup = formDiv.createDiv({ cls: 'mount-file-group' });
        fileGroup.createSpan({ text: '选择文件:', cls: 'mount-label' });

        const fileSelect = fileGroup.createEl('select', { cls: 'mount-file-select' });
        fileSelect.createEl('option', { text: '-- 选择教材文件 --', value: '' });

        // Load available files
        this.loadTextbookFilesIntoSelector(fileSelect, 'all');

        // Update file list when type changes
        typeSelect.addEventListener('change', () => {
            const selectedType = typeSelect.value as TextbookType | 'all';
            this.loadTextbookFilesIntoSelector(fileSelect, selectedType);
        });

        // Mount button
        const mountBtn = formDiv.createEl('button', {
            text: '挂载教材',
            cls: 'mod-cta mount-textbook-btn',
        });

        mountBtn.addEventListener('click', async () => {
            const filePath = fileSelect.value;
            if (!filePath) {
                new Notice('请选择要挂载的教材文件');
                return;
            }

            // Story 34.3 AC1: Get current canvas path for backend sync
            const canvasPath = this.getCurrentCanvasPath();
            if (!canvasPath) {
                new Notice('⚠️ 请先打开一个Canvas文件，以便关联教材');
                return;
            }

            try {
                mountBtn.disabled = true;
                mountBtn.textContent = '挂载中...';

                // Story 34.3 AC2: Use mountTextbookForCanvas to trigger backend sync
                await this.textbookMountService.mountTextbookForCanvas(filePath, canvasPath);
                new Notice(`✅ 教材挂载成功 (已关联到 ${canvasPath.split('/').pop()})`);

                // Refresh the list
                this.refreshTextbookMountSection(container.parentElement!);

                // Reset selection
                fileSelect.value = '';
            } catch (error) {
                console.error('[ReviewDashboard] Failed to mount textbook:', error);
                new Notice('❌ 挂载失败: ' + (error as Error).message);
            } finally {
                mountBtn.disabled = false;
                mountBtn.textContent = '挂载教材';
            }
        });
    }

    /**
     * Load available textbook files into selector
     */
    private async loadTextbookFilesIntoSelector(
        select: HTMLSelectElement,
        filterType: TextbookType | 'all'
    ): Promise<void> {
        // Clear existing options except first
        while (select.options.length > 1) {
            select.remove(1);
        }

        try {
            const files = await this.textbookMountService.getAvailableTextbookFiles();
            const mountedPaths = this.textbookMountService.getMountedTextbooks().map(tb => tb.path);

            files
                .filter(file => filterType === 'all' || file.type === filterType)
                .filter(file => !mountedPaths.includes(file.path)) // Exclude already mounted
                .forEach(file => {
                    const typeIcon = file.type === 'pdf' ? '📕' : file.type === 'markdown' ? '📝' : '🎨';
                    select.createEl('option', {
                        text: `${typeIcon} ${file.basename}`,
                        value: file.path,
                    });
                });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load textbook files:', error);
        }
    }

    /**
     * Render mounted textbooks list
     */
    private renderMountedTextbooksList(container: HTMLElement): void {
        const listDiv = container.createDiv({ cls: 'mounted-textbooks-list' });
        listDiv.createEl('h4', { text: '已挂载的教材', cls: 'mounted-list-title' });

        const textbooks = this.textbookMountService.getMountedTextbooks();

        if (textbooks.length === 0) {
            listDiv.createDiv({
                text: '暂无挂载的教材，请选择文件进行挂载',
                cls: 'mounted-empty',
            });
            return;
        }

        const list = listDiv.createDiv({ cls: 'textbook-items' });

        textbooks.forEach((textbook) => {
            this.renderMountedTextbookItem(list, textbook);
        });
    }

    /**
     * Render single mounted textbook item
     */
    private renderMountedTextbookItem(container: HTMLElement, textbook: MountedTextbook): void {
        const item = container.createDiv({ cls: 'textbook-item' });

        // Icon based on type
        const typeIcon = textbook.type === 'pdf' ? '📕' : textbook.type === 'markdown' ? '📝' : '🎨';

        // Header row
        const headerRow = item.createDiv({ cls: 'textbook-header' });
        headerRow.createSpan({ text: typeIcon, cls: 'textbook-icon' });
        headerRow.createSpan({ text: textbook.name, cls: 'textbook-name' });

        // Type badge
        const typeBadge = headerRow.createSpan({ cls: `textbook-type-badge type-${textbook.type}` });
        typeBadge.textContent = textbook.type.toUpperCase();

        // Info row
        const infoRow = item.createDiv({ cls: 'textbook-info' });

        // Sections count
        const sectionsCount = textbook.sections?.length || 0;
        infoRow.createSpan({
            text: `${sectionsCount} 个章节`,
            cls: 'textbook-sections',
        });

        // Reference count
        infoRow.createSpan({
            text: `引用: ${textbook.referenceCount} 次`,
            cls: 'textbook-refs',
        });

        // Mounted date
        const mountedDate = new Date(textbook.mountedDate);
        infoRow.createSpan({
            text: `挂载于 ${mountedDate.toLocaleDateString()}`,
            cls: 'textbook-date',
        });

        // Actions row
        const actionsRow = item.createDiv({ cls: 'textbook-actions' });

        // Open file button
        const openBtn = actionsRow.createEl('button', { cls: 'textbook-action-btn open-btn' });
        setIcon(openBtn, 'external-link');
        openBtn.setAttribute('aria-label', '打开文件');
        openBtn.addEventListener('click', () => {
            this.app.workspace.openLinkText(textbook.path, '', false);
        });

        // View sections button (if has sections)
        if (sectionsCount > 0) {
            const sectionsBtn = actionsRow.createEl('button', { cls: 'textbook-action-btn sections-btn' });
            setIcon(sectionsBtn, 'list');
            sectionsBtn.setAttribute('aria-label', '查看章节');
            sectionsBtn.addEventListener('click', () => {
                this.showTextbookSections(textbook);
            });
        }

        // Unmount button
        const unmountBtn = actionsRow.createEl('button', { cls: 'textbook-action-btn unmount-btn' });
        setIcon(unmountBtn, 'trash-2');
        unmountBtn.setAttribute('aria-label', '卸载教材');
        unmountBtn.addEventListener('click', async () => {
            this.textbookMountService.unmountTextbook(textbook.id);
            new Notice('教材已卸载');
            this.refreshTextbookMountSection(container.parentElement!.parentElement!);
        });
    }

    /**
     * Show textbook sections in a menu/popup
     */
    private showTextbookSections(textbook: MountedTextbook): void {
        if (!textbook.sections || textbook.sections.length === 0) {
            new Notice('此教材暂无章节信息');
            return;
        }

        const menu = new Menu();

        textbook.sections.forEach((section) => {
            const levelIndent = '  '.repeat(section.level - 1);
            menu.addItem((item) => {
                item.setTitle(`${levelIndent}${section.title}`)
                    .setIcon('bookmark')
                    .onClick(async () => {
                        // For PDF, open with page number
                        if (textbook.type === 'pdf' && section.pageNumber) {
                            // Try to open PDF at specific page
                            await this.app.workspace.openLinkText(
                                `${textbook.path}#page=${section.pageNumber}`,
                                '',
                                false
                            );
                        } else {
                            // For markdown/canvas, just open the file
                            await this.app.workspace.openLinkText(textbook.path, '', false);
                        }
                        this.textbookMountService.incrementReferenceCount(textbook.id);
                    });
            });
        });

        // Show at cursor position
        const activeLeaf = this.app.workspace.activeLeaf;
        if (activeLeaf) {
            menu.showAtMouseEvent(new MouseEvent('click'));
        }
    }

    /**
     * Refresh textbook mount section
     */
    private refreshTextbookMountSection(container: HTMLElement): void {
        // Find and remove existing section
        const existingSection = container.querySelector('.textbook-mount-section');
        if (existingSection) {
            existingSection.remove();
        }

        // Re-render
        this.renderTextbookMountSection(container);
    }

    /**
     * Story 34.3 Task 1: Get current active canvas file path
     *
     * Detects the currently active canvas file from Obsidian workspace.
     * Used to associate mounted textbooks with the active canvas for backend sync.
     *
     * @returns Canvas file path if a canvas is active, null otherwise
     * @source Story 34.3 AC1 - ReviewDashboardView自动检测当前Canvas
     */
    private getCurrentCanvasPath(): string | null {
        const activeFile = this.app.workspace.getActiveFile();

        // Check if there's an active file and it's a canvas
        if (!activeFile) {
            console.log('[ReviewDashboard] No active file');
            return null;
        }

        if (!activeFile.path.endsWith('.canvas')) {
            console.log('[ReviewDashboard] Active file is not a canvas:', activeFile.path);
            return null;
        }

        console.log('[ReviewDashboard] Current canvas detected:', activeFile.path);
        return activeFile.path;
    }

    private renderHeader(container: HTMLElement): void {
        const header = container.createDiv({ cls: 'dashboard-header' });

        // Title
        const titleArea = header.createDiv({ cls: 'dashboard-title-area' });
        titleArea.createEl('h2', { text: '复习仪表板', cls: 'dashboard-title' });

        if (this.state.lastUpdated) {
            titleArea.createEl('span', {
                text: `更新于 ${this.state.lastUpdated.toLocaleTimeString()}`,
                cls: 'dashboard-subtitle',
            });
        }

        // Summary stats
        const summaryStats = header.createDiv({ cls: 'header-stats' });

        this.createStatItem(summaryStats, this.state.statistics.todayPending, '待复习', 'alert-circle');
        this.createStatItem(summaryStats, this.state.statistics.todayCompleted, '已完成', 'check-circle');
        this.createStatItem(
            summaryStats,
            Math.round(this.state.statistics.todayProgress * 100) + '%',
            '进度',
            'trending-up'
        );

        // Actions area
        const actions = header.createDiv({ cls: 'header-actions' });

        // Auto-scoring toggle
        this.renderAutoScoringToggle(actions);

        // Refresh button
        const refreshBtn = actions.createEl('button', {
            cls: 'header-button',
            attr: { 'aria-label': '刷新' },
        });
        setIcon(refreshBtn, 'refresh-cw');
        if (this.state.loading) {
            refreshBtn.addClass('spinning');
        }
        refreshBtn.addEventListener('click', () => this.loadData());
    }

    /**
     * Render auto-scoring toggle button
     *
     * Controls whether scoring checkpoint runs before agent operations.
     * Default: enabled (true)
     *
     * @param container - Parent container element
     */
    private renderAutoScoringToggle(container: HTMLElement): void {
        const isEnabled = this.plugin.settings.enableAutoScoring;

        // Create toggle container
        const toggleContainer = container.createDiv({ cls: 'auto-scoring-toggle' });

        // Label
        toggleContainer.createSpan({
            text: '自动评分',
            cls: 'toggle-label'
        });

        // Toggle button
        const toggleBtn = toggleContainer.createEl('button', {
            cls: `toggle-button ${isEnabled ? 'active' : ''}`,
            attr: {
                'aria-label': isEnabled ? '禁用自动评分' : '启用自动评分',
                'aria-pressed': String(isEnabled)
            },
        });

        // Icon based on state
        setIcon(toggleBtn, isEnabled ? 'check-circle' : 'circle');

        // Status text
        toggleBtn.createSpan({
            text: isEnabled ? '开' : '关',
            cls: 'toggle-status'
        });

        // Click handler
        toggleBtn.addEventListener('click', async () => {
            // Toggle the setting
            this.plugin.settings.enableAutoScoring = !this.plugin.settings.enableAutoScoring;
            await this.plugin.saveSettings();

            // Refresh entire dashboard to update toggle state
            this.render();

            // Show feedback
            new Notice(this.plugin.settings.enableAutoScoring
                ? '自动评分已启用'
                : '自动评分已禁用');
        });
    }

    private createStatItem(
        container: HTMLElement,
        value: string | number,
        label: string,
        icon: string
    ): void {
        const item = container.createDiv({ cls: 'stat-item' });
        const iconEl = item.createSpan({ cls: 'stat-icon' });
        setIcon(iconEl, icon);
        item.createSpan({ text: String(value), cls: 'stat-value' });
        item.createSpan({ text: label, cls: 'stat-label' });
    }

    private renderTaskList(container: HTMLElement): void {
        // Controls
        const controls = container.createDiv({ cls: 'task-list-controls' });

        // Filter dropdown
        const filterGroup = controls.createDiv({ cls: 'control-group' });
        filterGroup.createSpan({ text: '筛选: ', cls: 'control-label' });
        const filterSelect = filterGroup.createEl('select', { cls: 'control-select' });
        this.createFilterOptions(filterSelect);
        filterSelect.value = this.state.filterBy;
        filterSelect.onchange = () => {
            this.updateViewState({ filterBy: filterSelect.value as TaskFilterOption });
        };

        // Sort dropdown
        const sortGroup = controls.createDiv({ cls: 'control-group' });
        sortGroup.createSpan({ text: '排序: ', cls: 'control-label' });
        const sortSelect = sortGroup.createEl('select', { cls: 'control-select' });
        this.createSortOptions(sortSelect);
        sortSelect.value = this.state.sortBy;
        sortSelect.onchange = () => {
            this.updateViewState({ sortBy: sortSelect.value as TaskSortOption });
        };

        // Task list
        const taskList = container.createDiv({ cls: 'task-list' });

        if (this.state.loading) {
            this.renderLoadingState(taskList);
            return;
        }

        if (this.state.error) {
            this.renderErrorState(taskList);
            return;
        }

        const filteredTasks = this.filterAndSortTasks();

        if (filteredTasks.length === 0) {
            this.renderEmptyState(taskList);
            return;
        }

        // Render task cards
        filteredTasks.forEach((task) => {
            this.renderTaskCard(taskList, task);
        });
    }

    private createFilterOptions(select: HTMLSelectElement): void {
        const options = [
            { value: 'all', label: '全部任务' },
            { value: 'overdue', label: '已逾期' },
            { value: 'today', label: '今日到期' },
            { value: 'high-priority', label: '高优先级' },
        ];
        options.forEach((opt) => {
            select.createEl('option', { value: opt.value, text: opt.label });
        });
    }

    private createSortOptions(select: HTMLSelectElement): void {
        const options = [
            { value: 'priority', label: '按优先级' },
            { value: 'dueDate', label: '按到期时间' },
            { value: 'memoryStrength', label: '按记忆强度' },
            { value: 'canvas', label: '按Canvas' },
        ];
        options.forEach((opt) => {
            select.createEl('option', { value: opt.value, text: opt.label });
        });
    }

    private filterAndSortTasks(): ReviewTask[] {
        let tasks = [...this.state.tasks];

        // Filter
        switch (this.state.filterBy) {
            case 'overdue':
                tasks = tasks.filter((t) => t.overdueDays > 0);
                break;
            case 'today':
                tasks = tasks.filter((t) => {
                    const today = new Date().toDateString();
                    return t.dueDate.toDateString() === today;
                });
                break;
            case 'high-priority':
                tasks = tasks.filter((t) => t.priority === 'critical' || t.priority === 'high');
                break;
        }

        // Sort
        tasks.sort((a, b) => {
            switch (this.state.sortBy) {
                case 'priority':
                    return this.getPriorityWeight(b.priority) - this.getPriorityWeight(a.priority);
                case 'dueDate':
                    return a.dueDate.getTime() - b.dueDate.getTime();
                case 'memoryStrength':
                    return a.memoryStrength - b.memoryStrength;
                case 'canvas':
                    return a.canvasTitle.localeCompare(b.canvasTitle);
                default:
                    return 0;
            }
        });

        return tasks;
    }

    private getPriorityWeight(priority: TaskPriority): number {
        const weights: Record<TaskPriority, number> = {
            critical: 4,
            high: 3,
            medium: 2,
            low: 1,
        };
        return weights[priority];
    }

    private renderTaskCard(container: HTMLElement, task: ReviewTask): void {
        const isOverdue = task.overdueDays > 0;
        const isToday = task.dueDate.toDateString() === new Date().toDateString();

        // Build class list
        const cardClasses = [
            'task-card',
            `priority-${task.priority}`,
            `status-${task.status}`,
            isOverdue ? 'overdue' : '',
            isToday && !isOverdue ? 'due-today' : '',
        ]
            .filter(Boolean)
            .join(' ');

        const card = container.createDiv({ cls: cardClasses });

        // Card header
        const header = card.createDiv({ cls: 'task-card-header' });
        const headerContent = header.createDiv({ cls: 'header-content' });
        headerContent.createEl('h3', { text: task.conceptName, cls: 'task-title' });

        // Canvas info
        const canvasInfo = headerContent.createDiv({ cls: 'canvas-info' });
        const canvasIcon = canvasInfo.createSpan();
        setIcon(canvasIcon, 'file-text');
        canvasInfo.createSpan({ text: task.canvasTitle, cls: 'canvas-title' });

        // Subject badge
        if (task.subject && task.subject !== 'general') {
            const subjectBadge = canvasInfo.createSpan({
                cls: 'subject-badge',
                text: task.subject,
            });
            subjectBadge.style.cssText =
                'margin-left:6px;padding:1px 6px;border-radius:3px;font-size:11px;background:var(--interactive-accent);color:var(--text-on-accent);opacity:0.85;';
        }

        // Badges
        const badges = header.createDiv({ cls: 'header-badges' });

        // Priority badge
        const priorityBadge = badges.createSpan({ cls: `priority-badge ${task.priority}` });
        priorityBadge.setText(this.getPriorityLabel(task.priority));

        // Time badge (if overdue or due today)
        if (isOverdue) {
            const timeBadge = badges.createSpan({ cls: 'time-badge overdue' });
            const alertIcon = timeBadge.createSpan();
            setIcon(alertIcon, 'alert-circle');
            timeBadge.createSpan({ text: `逾期${task.overdueDays}天` });
        } else if (isToday) {
            const timeBadge = badges.createSpan({ cls: 'time-badge due-today' });
            const clockIcon = timeBadge.createSpan();
            setIcon(clockIcon, 'clock');
            timeBadge.createSpan({ text: '今日到期' });
        }

        // Memory metrics section
        const metrics = card.createDiv({ cls: 'task-metrics' });

        // Memory strength
        this.renderMemoryStrength(metrics, task);

        // Forgetting curve indicator
        this.renderForgettingCurve(metrics, task);

        // Task details
        const details = card.createDiv({ cls: 'task-details' });

        // Review count
        const reviewCountItem = details.createDiv({ cls: 'detail-item' });
        reviewCountItem.createSpan({ text: '复习次数', cls: 'detail-label' });
        reviewCountItem.createSpan({ text: String(task.reviewCount), cls: 'detail-value' });

        // Retention rate
        const retentionItem = details.createDiv({ cls: 'detail-item' });
        retentionItem.createSpan({ text: '保持率', cls: 'detail-label' });
        retentionItem.createSpan({
            text: `${Math.round(task.retentionRate * 100)}%`,
            cls: 'detail-value',
        });

        // Last review
        const lastReviewItem = details.createDiv({ cls: 'detail-item' });
        lastReviewItem.createSpan({ text: '上次复习', cls: 'detail-label' });
        lastReviewItem.createSpan({
            text: task.lastReviewDate ? this.formatRelativeDate(task.lastReviewDate) : '从未',
            cls: 'detail-value',
        });

        // Due date
        const dueDateItem = details.createDiv({ cls: 'detail-item' });
        dueDateItem.createSpan({ text: '到期时间', cls: 'detail-label' });
        dueDateItem.createSpan({
            text: this.formatRelativeDate(task.dueDate),
            cls: `detail-value ${isOverdue ? 'overdue' : ''}`,
        });

        // Card actions
        const actions = card.createDiv({ cls: 'task-card-actions' });

        // Primary actions
        const primaryActions = actions.createDiv({ cls: 'primary-actions' });

        if (task.status === 'pending' || task.status === 'in_progress') {
            const startBtn = primaryActions.createEl('button', {
                cls: 'task-action-btn primary start',
                attr: { 'aria-label': '开始复习' },
            });
            const startIcon = startBtn.createSpan();
            setIcon(startIcon, task.status === 'in_progress' ? 'play-circle' : 'play');
            startBtn.createSpan({ text: task.status === 'in_progress' ? '继续' : '开始' });
            startBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleTaskStart(task);
            });
        }

        const completeBtn = primaryActions.createEl('button', {
            cls: 'task-action-btn complete',
            attr: { 'aria-label': '完成复习' },
        });
        const completeIcon = completeBtn.createSpan();
        setIcon(completeIcon, 'check');
        completeBtn.createSpan({ text: '完成' });
        completeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showCompleteDialog(task);
        });

        // Secondary actions
        const secondaryActions = actions.createDiv({ cls: 'secondary-actions' });

        const postponeBtn = secondaryActions.createEl('button', {
            cls: 'task-action-btn secondary postpone',
            attr: { 'aria-label': '推迟复习' },
        });
        setIcon(postponeBtn, 'clock');
        postponeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showPostponeDialog(task);
        });

        const detailsBtn = secondaryActions.createEl('button', {
            cls: 'task-action-btn secondary',
            attr: { 'aria-label': '查看详情' },
        });
        setIcon(detailsBtn, 'info');
        detailsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleTaskDetails(task);
        });

        // Status indicator
        const statusIndicator = actions.createDiv({
            cls: `status-indicator ${task.status}`,
        });
        const statusIcon = statusIndicator.createSpan();
        setIcon(statusIcon, this.getStatusIcon(task.status));
        statusIndicator.createSpan({ text: this.getStatusText(task.status) });

        // Card click handler
        card.addEventListener('click', () => this.handleTaskClick(task));
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.handleTaskClick(task);
            }
        });

        // Right-click context menu (Story 14.4: AC4)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Menu.showAtMouseEvent)
        card.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showTaskContextMenu(e, task);
        });
    }

    /**
     * Show context menu for task card
     * Story 14.4: AC4 - Right-click menu with "Mark as mastered" / "Reset progress"
     * Story 31.A.6: Enhanced with TodayReviewListService context menu actions
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Menu API)
     */
    private showTaskContextMenu(event: MouseEvent, task: ReviewTask): void {
        const todayService = this.plugin.todayReviewListService;
        const isTodayReviewItem = todayService && 'canvasPath' in task;

        // Story 31.A.6: If TodayReviewListService is available and task is a TodayReviewItem,
        // delegate to the service's context menu for unified action handling
        if (isTodayReviewItem) {
            const todayItem = task as import('../services/TodayReviewListService').TodayReviewItem;
            todayService.showContextMenu(event, todayItem, async (action) => {
                const success = await todayService.handleContextMenuAction(action, todayItem);
                if (success) {
                    await this.loadData();
                }
            });
            return;
        }

        // Fallback: legacy context menu (pre-31.A.6)
        const menu = new Menu();

        // Mark as mastered
        menu.addItem((item) => {
            item.setTitle('标记为已掌握')
                .setIcon('check-circle-2')
                .onClick(async () => {
                    await this.handleMarkAsMastered(task);
                });
        });

        // Reset progress
        menu.addItem((item) => {
            item.setTitle('重置进度')
                .setIcon('rotate-ccw')
                .onClick(async () => {
                    await this.handleResetProgress(task);
                });
        });

        menu.addSeparator();

        // Generate review canvas
        menu.addItem((item) => {
            item.setTitle('生成检验白板')
                .setIcon('file-plus')
                .onClick(async () => {
                    await this.handleGenerateReviewCanvas(task);
                });
        });

        // Open original canvas
        menu.addItem((item) => {
            item.setTitle('打开原白板')
                .setIcon('file-text')
                .onClick(() => {
                    this.handleTaskClick(task);
                });
        });

        menu.addSeparator();

        // Postpone options
        menu.addItem((item) => {
            item.setTitle('推迟1天')
                .setIcon('clock')
                .onClick(async () => {
                    await this.handleTaskPostpone(task, 1);
                });
        });

        menu.addItem((item) => {
            item.setTitle('推迟3天')
                .setIcon('clock')
                .onClick(async () => {
                    await this.handleTaskPostpone(task, 3);
                });
        });

        menu.addItem((item) => {
            item.setTitle('推迟1周')
                .setIcon('calendar')
                .onClick(async () => {
                    await this.handleTaskPostpone(task, 7);
                });
        });

        menu.showAtMouseEvent(event);
    }

    private renderMemoryStrength(container: HTMLElement, task: ReviewTask): void {
        const memoryStrength = container.createDiv({ cls: 'memory-strength' });

        // Header
        const header = memoryStrength.createDiv({ cls: 'strength-header' });
        header.createSpan({ text: '记忆强度', cls: 'strength-label' });

        const strengthPercentage = Math.round(task.memoryStrength * 100);
        const strengthLevel = this.getStrengthLevel(task.memoryStrength);
        header.createSpan({
            text: `${strengthPercentage}%`,
            cls: `strength-value ${strengthLevel}`,
        });

        // Progress bar
        const barContainer = memoryStrength.createDiv({ cls: 'strength-bar-container' });
        const bar = barContainer.createDiv({ cls: 'strength-bar' });
        const fill = bar.createDiv({ cls: `strength-fill ${strengthLevel}` });
        fill.style.width = `${strengthPercentage}%`;

        // Strength icon
        const iconEl = barContainer.createSpan({ cls: 'strength-icon' });
        iconEl.setText(this.getStrengthEmoji(task.memoryStrength));
    }

    private renderForgettingCurve(container: HTMLElement, task: ReviewTask): void {
        const curve = container.createDiv({ cls: 'forgetting-curve' });

        // Header
        const header = curve.createDiv({ cls: 'curve-header' });
        header.createSpan({ text: '遗忘曲线', cls: 'curve-label' });

        const urgency = this.getUrgencyLevel(task.overdueDays);
        const urgencyIndicator = header.createSpan({ cls: `urgency-indicator ${urgency.level}` });
        urgencyIndicator.createSpan({ text: urgency.label });

        // Urgency bar
        const urgencyBar = curve.createDiv({ cls: 'urgency-bar' });
        const urgencyFill = urgencyBar.createDiv({ cls: 'urgency-fill' });
        urgencyFill.style.width = `${Math.min(100, Math.max(0, (1 - task.memoryStrength) * 100))}%`;
        urgencyFill.style.backgroundColor = urgency.color;

        // Info
        const info = curve.createDiv({ cls: 'curve-info' });
        info.createSpan({ text: '下次复习: ', cls: 'label' });
        info.createSpan({
            text: this.formatRelativeDate(task.dueDate),
            cls: 'next-review',
        });
    }

    private getStrengthLevel(strength: number): string {
        if (strength >= 0.7) return 'high';
        if (strength >= 0.4) return 'medium';
        return 'low';
    }

    private getStrengthEmoji(strength: number): string {
        if (strength >= 0.9) return '🏆';
        if (strength >= 0.7) return '✅';
        if (strength >= 0.4) return '⚠️';
        return '❌';
    }

    private getUrgencyLevel(overdueDays: number): { level: string; label: string; color: string } {
        if (overdueDays > 0) {
            return { level: 'urgent', label: '急需复习', color: '#ef4444' };
        }
        if (overdueDays === 0) {
            return { level: 'due', label: '今日到期', color: '#eab308' };
        }
        if (overdueDays >= -3) {
            return { level: 'soon', label: '即将到期', color: 'var(--text-normal)' };
        }
        return { level: 'future', label: '计划中', color: '#22c55e' };
    }

    private getStatusIcon(status: string): string {
        const icons: Record<string, string> = {
            pending: 'circle',
            in_progress: 'loader',
            completed: 'check-circle',
            postponed: 'clock',
        };
        return icons[status] || 'circle';
    }

    private getStatusText(status: string): string {
        const texts: Record<string, string> = {
            pending: '待复习',
            in_progress: '学习中',
            completed: '已完成',
            postponed: '已推迟',
        };
        return texts[status] || '待复习';
    }

    private formatRelativeDate(date: Date): string {
        const now = new Date();
        const diff = date.getTime() - now.getTime();
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

        if (days < -1) return `${Math.abs(days)}天前`;
        if (days === -1) return '昨天';
        if (days === 0) return '今天';
        if (days === 1) return '明天';
        if (days < 7) return `${days}天后`;
        return date.toLocaleDateString();
    }

    private getPriorityLabel(priority: TaskPriority): string {
        const labels: Record<TaskPriority, string> = {
            critical: '紧急',
            high: '高',
            medium: '中',
            low: '低',
        };
        return labels[priority];
    }

    private renderStatistics(container: HTMLElement): void {
        const stats = this.state.statistics;

        // Today Overview Card
        const overviewCard = container.createDiv({ cls: 'stat-card' });
        overviewCard.createEl('h3', { text: '今日概览' });

        const metrics = overviewCard.createDiv({ cls: 'stat-metrics' });

        this.createMetric(metrics, stats.todayPending, '待复习');
        this.createMetric(metrics, stats.todayCompleted, '已完成');
        this.createMetric(metrics, Math.round(stats.todayProgress * 100) + '%', '进度');

        // Progress bar
        const progressBar = overviewCard.createDiv({ cls: 'progress-bar' });
        const progressFill = progressBar.createDiv({ cls: 'progress-fill' });
        progressFill.style.width = `${stats.todayProgress * 100}%`;

        // Learning Stats Card
        const learningCard = container.createDiv({ cls: 'stat-card' });
        learningCard.createEl('h3', { text: '学习统计' });

        const statList = learningCard.createDiv({ cls: 'stat-list' });
        this.createStatListItem(statList, '平均分数', Math.round(stats.averageScore).toString());
        this.createStatListItem(
            statList,
            '记忆强度',
            Math.round(stats.averageMemoryStrength * 100) + '%'
        );
        this.createStatListItem(
            statList,
            '保持率',
            Math.round(stats.averageRetentionRate * 100) + '%'
        );
        this.createStatListItem(statList, '连续学习', stats.streakDays + '天');

        // Mastery Distribution Card
        const masteryCard = container.createDiv({ cls: 'stat-card' });
        masteryCard.createEl('h3', { text: '掌握度分布' });

        const masteryChart = masteryCard.createDiv({ cls: 'mastery-chart' });
        stats.masteryDistribution.forEach((item) => {
            const masteryItem = masteryChart.createDiv({ cls: 'mastery-item' });
            const bar = masteryItem.createDiv({ cls: 'mastery-bar' });
            bar.style.backgroundColor = item.color;

            // Calculate percentage
            const total = stats.masteredConcepts + stats.learningConcepts + stats.strugglingConcepts;
            const percentage = total > 0 ? (item.count / total) * 100 : 0;
            bar.style.width = `${percentage}%`;

            masteryItem.createSpan({ text: item.label, cls: 'mastery-label' });
            masteryItem.createSpan({ text: String(item.count), cls: 'mastery-count' });
        });
    }

    private createMetric(container: HTMLElement, value: string | number, label: string): void {
        const metric = container.createDiv({ cls: 'metric' });
        metric.createSpan({ text: String(value), cls: 'value' });
        metric.createSpan({ text: label, cls: 'label' });
    }

    private createStatListItem(container: HTMLElement, label: string, value: string): void {
        const item = container.createDiv({ cls: 'stat-list-item' });
        item.createSpan({ text: label, cls: 'label' });
        item.createSpan({ text: value, cls: 'value' });
    }

    private renderQuickActions(container: HTMLElement): void {
        const actionsCard = container.createDiv({ cls: 'stat-card quick-actions-card' });
        actionsCard.createEl('h3', { text: '快速操作' });

        const actions = actionsCard.createDiv({ cls: 'quick-actions' });

        // Start review button
        const startBtn = actions.createEl('button', {
            cls: 'action-button primary',
            text: '开始复习',
        });
        const startIcon = startBtn.createSpan({ cls: 'button-icon' });
        setIcon(startIcon, 'play');
        startBtn.prepend(startIcon);
        startBtn.addEventListener('click', () => this.handleStartReview());

        // Generate plan button
        const planBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '生成计划',
        });
        const planIcon = planBtn.createSpan({ cls: 'button-icon' });
        setIcon(planIcon, 'calendar-plus');
        planBtn.prepend(planIcon);
        planBtn.addEventListener('click', () => this.handleGeneratePlan());

        // View calendar button
        const calendarBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '复习日历',
        });
        const calendarIcon = calendarBtn.createSpan({ cls: 'button-icon' });
        setIcon(calendarIcon, 'calendar');
        calendarBtn.prepend(calendarIcon);
        calendarBtn.addEventListener('click', () => this.handleViewCalendar());

        // Generate review canvas button (Story 14.5)
        const generateCanvasBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '生成检验白板',
        });
        const generateIcon = generateCanvasBtn.createSpan({ cls: 'button-icon' });
        setIcon(generateIcon, 'file-plus');
        generateCanvasBtn.prepend(generateIcon);
        generateCanvasBtn.addEventListener('click', async () => await this.showReviewModeDialog());

        // Settings button
        const settingsBtn = actions.createEl('button', {
            cls: 'action-button ghost',
            text: '设置',
        });
        const settingsIcon = settingsBtn.createSpan({ cls: 'button-icon' });
        setIcon(settingsIcon, 'settings');
        settingsBtn.prepend(settingsIcon);
        settingsBtn.addEventListener('click', () => this.handleOpenSettings());
    }

    private renderLoadingState(container: HTMLElement): void {
        const loading = container.createDiv({ cls: 'loading-state' });
        const spinner = loading.createDiv({ cls: 'spinner' });
        loading.createSpan({ text: '加载中...' });
    }

    private renderErrorState(container: HTMLElement): void {
        const error = container.createDiv({ cls: 'error-state' });
        const icon = error.createSpan({ cls: 'error-icon' });
        setIcon(icon, 'alert-circle');
        error.createSpan({ text: this.state.error || '加载失败', cls: 'error-message' });

        const retryBtn = error.createEl('button', {
            cls: 'retry-button',
            text: '重试',
        });
        retryBtn.addEventListener('click', () => this.loadData());
    }

    private renderEmptyState(container: HTMLElement): void {
        const empty = container.createDiv({ cls: 'empty-state' });
        const icon = empty.createSpan({ cls: 'empty-icon' });
        setIcon(icon, 'check-circle-2');
        empty.createEl('h4', { text: '太棒了!' });
        empty.createEl('p', { text: '当前没有待复习的任务' });
    }

    // =========================================================================
    // Dialogs
    // =========================================================================

    private showCompleteDialog(task: ReviewTask): void {
        const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
        const dialog = overlay.createDiv({ cls: 'task-dialog' });

        // Header
        const header = dialog.createDiv({ cls: 'dialog-header' });
        header.createEl('h3', { text: '完成复习', cls: 'dialog-title' });
        const closeBtn = header.createEl('button', { cls: 'dialog-close' });
        setIcon(closeBtn, 'x');
        closeBtn.addEventListener('click', () => overlay.remove());

        // Body
        const body = dialog.createDiv({ cls: 'dialog-body' });
        body.createEl('p', { text: `请评价您对 "${task.conceptName}" 的掌握程度：` });

        // Score selector
        const scoreSelector = body.createDiv({ cls: 'score-selector' });
        const scores = [
            { value: 1, label: '完全忘记' },
            { value: 2, label: '似曾相识' },
            { value: 3, label: '费力回忆' },
            { value: 4, label: '清晰记得' },
            { value: 5, label: '牢固掌握' },
        ];

        let selectedScore = 3;

        scores.forEach((score) => {
            const btn = scoreSelector.createDiv({
                cls: `score-btn ${score.value === selectedScore ? 'selected' : ''}`,
            });
            btn.createSpan({ text: String(score.value), cls: 'score-value' });
            btn.createSpan({ text: score.label, cls: 'score-label' });
            btn.addEventListener('click', () => {
                scoreSelector.querySelectorAll('.score-btn').forEach((el) => {
                    el.removeClass('selected');
                });
                btn.addClass('selected');
                selectedScore = score.value;
            });
        });

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.addEventListener('click', () => overlay.remove());

        const confirmBtn = actions.createEl('button', {
            cls: 'task-action-btn primary',
            text: '确认完成',
        });
        confirmBtn.addEventListener('click', async () => {
            await this.handleTaskComplete(task, selectedScore);
            overlay.remove();
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    private showPostponeDialog(task: ReviewTask): void {
        const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
        const dialog = overlay.createDiv({ cls: 'task-dialog' });

        // Header
        const header = dialog.createDiv({ cls: 'dialog-header' });
        header.createEl('h3', { text: '推迟复习', cls: 'dialog-title' });
        const closeBtn = header.createEl('button', { cls: 'dialog-close' });
        setIcon(closeBtn, 'x');
        closeBtn.addEventListener('click', () => overlay.remove());

        // Body
        const body = dialog.createDiv({ cls: 'dialog-body' });
        body.createEl('p', { text: `将 "${task.conceptName}" 推迟多久？` });

        // Postpone options
        const options = body.createDiv({ cls: 'postpone-options' });
        const delays = [
            { days: 1, label: '明天' },
            { days: 3, label: '3天后' },
            { days: 7, label: '一周后' },
        ];

        delays.forEach((delay) => {
            const btn = options.createDiv({ cls: 'postpone-btn' });
            btn.createSpan({ text: String(delay.days), cls: 'days' });
            btn.createSpan({ text: delay.label, cls: 'label' });
            btn.addEventListener('click', async () => {
                await this.handleTaskPostpone(task, delay.days);
                overlay.remove();
            });
        });

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.addEventListener('click', () => overlay.remove());

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Check if a canvas file has red or purple nodes that need review
     * PRD F8: 红色(color="1") + 紫色(color="3")节点需要复习
     */
    private async canvasHasReviewNodes(canvasPath: string): Promise<{ hasNodes: boolean; count: number; canvasName: string }> {
        try {
            const file = this.app.vault.getAbstractFileByPath(canvasPath);
            if (!(file instanceof TFile)) {
                return { hasNodes: false, count: 0, canvasName: '' };
            }

            const content = await this.app.vault.read(file);
            const canvasData = JSON.parse(content);
            const nodes = canvasData.nodes || [];

            // PRD F8: 红色(color="1") + 紫色(color="3")
            const reviewColors = new Set(['1', '3']);
            const reviewNodes = nodes.filter((n: { type: string; color: string }) =>
                n.type === 'text' && reviewColors.has(n.color)
            );

            const canvasName = file.basename;
            return { hasNodes: reviewNodes.length > 0, count: reviewNodes.length, canvasName };
        } catch (e) {
            console.error('Error reading canvas:', e);
            return { hasNodes: false, count: 0, canvasName: '' };
        }
    }

    /**
     * Story 14.5: AC2 - Review mode selection dialog
     * Shows dialog for selecting review mode: "fresh" or "targeted"
     * ✅ FIXED: Now checks canvas nodes instead of pending tasks
     */
    private async showReviewModeDialog(): Promise<void> {
        // ✅ FIXED: Check current canvas for red/purple nodes instead of pending tasks
        // PRD F8: Extract red (color="1") + purple (color="3") nodes

        // Step 1: Check if a canvas is currently open
        const canvasPath = this.getCurrentCanvasPath();
        if (!canvasPath) {
            new Notice('⚠️ 请先打开一个Canvas文件');
            return;
        }

        // Step 2: Check if canvas has red/purple nodes
        const { hasNodes, count, canvasName } = await this.canvasHasReviewNodes(canvasPath);
        if (!hasNodes) {
            new Notice('📋 当前Canvas中没有需要复习的节点（红色或紫色）');
            return;
        }

        const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
        const dialog = overlay.createDiv({ cls: 'task-dialog review-mode-dialog' });

        // Header
        const header = dialog.createDiv({ cls: 'dialog-header' });
        header.createEl('h3', { text: '生成检验白板', cls: 'dialog-title' });
        const closeBtn = header.createEl('button', { cls: 'dialog-close' });
        setIcon(closeBtn, 'x');
        closeBtn.addEventListener('click', () => overlay.remove());

        // Body
        const body = dialog.createDiv({ cls: 'dialog-body' });
        body.createEl('p', { text: '请选择复习模式：' });

        // Mode options
        const modeOptions = body.createDiv({ cls: 'mode-options' });

        // Fresh mode option
        const freshOption = modeOptions.createDiv({ cls: 'mode-option selected' });
        freshOption.dataset.mode = 'fresh';
        const freshIcon = freshOption.createSpan({ cls: 'mode-icon' });
        setIcon(freshIcon, 'file-question');
        const freshContent = freshOption.createDiv({ cls: 'mode-content' });
        freshContent.createEl('strong', { text: '全新检验 (Fresh)' });
        freshContent.createEl('p', { text: '盲测式复习，不使用历史数据，测试真实记忆水平' });

        // Targeted mode option
        const targetedOption = modeOptions.createDiv({ cls: 'mode-option' });
        targetedOption.dataset.mode = 'targeted';
        const targetedIcon = targetedOption.createSpan({ cls: 'mode-icon' });
        setIcon(targetedIcon, 'target');
        const targetedContent = targetedOption.createDiv({ cls: 'mode-content' });
        targetedContent.createEl('strong', { text: '针对性复习 (Targeted)' });
        targetedContent.createEl('p', { text: '基于薄弱概念，专注于需要加强的知识点' });

        let selectedMode: 'fresh' | 'targeted' = 'fresh';

        // Mode selection handlers
        freshOption.addEventListener('click', () => {
            modeOptions.querySelectorAll('.mode-option').forEach((el) => el.removeClass('selected'));
            freshOption.addClass('selected');
            selectedMode = 'fresh';
        });

        targetedOption.addEventListener('click', () => {
            modeOptions.querySelectorAll('.mode-option').forEach((el) => el.removeClass('selected'));
            targetedOption.addClass('selected');
            selectedMode = 'targeted';
        });

        // Canvas info section (replaced task selection)
        const canvasSection = body.createDiv({ cls: 'task-selection' });
        canvasSection.createEl('p', { text: `将为Canvas "${canvasName}" 中的 ${count} 个节点生成检验白板` });

        const infoList = canvasSection.createDiv({ cls: 'task-list-preview' });
        const canvasItem = infoList.createDiv({ cls: 'task-preview-item' });
        const canvasIcon = canvasItem.createSpan({ cls: 'task-icon' });
        setIcon(canvasIcon, 'file-text');
        canvasItem.createSpan({ text: `${canvasName}.canvas (${count} 个红色/紫色节点)` });

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.addEventListener('click', () => overlay.remove());

        const generateBtn = actions.createEl('button', {
            cls: 'task-action-btn primary',
            text: '生成检验白板',
        });
        generateBtn.addEventListener('click', async () => {
            overlay.remove();
            // ✅ FIXED: Use canvas-based generation instead of task-based
            await this.handleGenerateCanvasReview(canvasPath, canvasName, selectedMode);
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Handle canvas-based verification canvas generation
     * ✅ NEW: Calls backend API with canvas path instead of task list
     * PRD F8: Generate verification canvas from red/purple nodes
     */
    private async handleGenerateCanvasReview(
        canvasPath: string,
        canvasName: string,
        mode: 'fresh' | 'targeted'
    ): Promise<void> {
        const modeLabel = mode === 'fresh' ? '全新检验' : '针对性复习';
        new Notice(`🔄 正在为 "${canvasName}" 生成检验白板 (${modeLabel})...`);

        try {
            // Call backend API to generate verification canvas
            // Fix: Use canvasPath (without .canvas extension) instead of canvasName (basename only)
            // Backend expects full relative path, e.g., "Canvas/Math53/Lecture5"
            const canvasPathWithoutExt = canvasPath.replace(/\.canvas$/i, '');
            const response = await fetch('http://localhost:8000/api/v1/review/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_canvas: canvasPathWithoutExt,
                    review_mode: mode,
                }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const result = await response.json();

            if (result.node_count > 0) {
                new Notice(`✅ 已生成检验白板: ${result.verification_canvas_name} (${result.node_count} 个节点)`);

                // Open the generated canvas
                const generatedPath = `${result.verification_canvas_name}.canvas`;
                const file = this.app.vault.getAbstractFileByPath(generatedPath);
                if (file instanceof TFile) {
                    await this.app.workspace.getLeaf().openFile(file);
                }
            } else {
                new Notice('⚠️ 没有找到可生成的节点');
            }
        } catch (error) {
            console.error('Failed to generate verification canvas:', error);
            new Notice(`❌ 生成失败: ${error instanceof Error ? error.message : '未知错误'}`);
        }
    }

    /**
     * Story 14.5: AC3, AC4, AC5, AC6 - Generate review canvases
     * Generates review canvases for selected tasks with specified mode
     * @param tasks Tasks to generate review canvases for
     * @param mode Review mode: "fresh" or "targeted"
     */
    private async handleGenerateReviewCanvases(
        tasks: ReviewTask[],
        mode: 'fresh' | 'targeted'
    ): Promise<void> {
        if (tasks.length === 0) {
            new Notice('⚠️ 没有选择任何任务');
            return;
        }

        const modeLabel = mode === 'fresh' ? '全新检验' : '针对性复习';
        new Notice(`🔄 正在生成检验白板 (${modeLabel})...`);

        let successCount = 0;
        let failCount = 0;
        let lastGeneratedPath: string | null = null;

        for (const task of tasks) {
            try {
                // Generate review canvas for each task
                const result = await this.generateReviewCanvas(task, mode);
                if (result.success) {
                    successCount++;
                    lastGeneratedPath = result.canvasPath || null;

                    // Story 14.5: AC4 - Store relationship to Graphiti
                    await this.storeGraphitiRelationship(
                        task.canvasId,
                        result.canvasPath || '',
                        mode
                    );
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error(`Failed to generate review canvas for ${task.conceptName}:`, error);
                failCount++;
            }
        }

        // Show result notification (AC7)
        if (successCount > 0 && failCount === 0) {
            new Notice(`✅ 成功生成 ${successCount} 个检验白板`);
        } else if (successCount > 0 && failCount > 0) {
            new Notice(`⚠️ 成功: ${successCount}, 失败: ${failCount}`);
        } else {
            new Notice(`❌ 生成检验白板失败`);
        }

        // Story 14.5: AC5 - Auto open the last generated canvas
        if (lastGeneratedPath) {
            const file = this.app.vault.getAbstractFileByPath(lastGeneratedPath);
            if (file) {
                await this.app.workspace.openLinkText(lastGeneratedPath, '', true);
            }
        }

        // Refresh the dashboard
        await this.loadData();
    }

    /**
     * Story 14.5: AC3 - Generate single review canvas
     * Calls the existing generate_review_canvas_file() function from Epic 4
     */
    private async generateReviewCanvas(
        task: ReviewTask,
        mode: 'fresh' | 'targeted'
    ): Promise<{ success: boolean; canvasPath?: string }> {
        try {
            // Get concepts for this task
            const concepts = mode === 'targeted' ? [task.conceptName] : [];

            // Call API to generate review canvas
            // This integrates with Epic 4's generate_review_canvas_file()
            const response = await fetch('http://localhost:8000/api/v1/canvas/generate-review', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    canvas_path: task.canvasId,
                    concepts: concepts,
                    mode: mode,
                }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const result = await response.json();
            return {
                success: true,
                canvasPath: result.review_canvas_path,
            };
        } catch (error) {
            console.error('Error generating review canvas:', error);

            // Fallback: Try local generation if API fails
            try {
                const timestamp = new Date().toISOString().slice(0, 10);
                const baseName = task.canvasId.replace('.canvas', '');
                const reviewCanvasPath = `${baseName}-检验白板-${timestamp}.canvas`;

                // Create a basic review canvas structure
                const reviewCanvas = {
                    nodes: [],
                    edges: [],
                };

                await this.app.vault.create(reviewCanvasPath, JSON.stringify(reviewCanvas, null, 2));

                return {
                    success: true,
                    canvasPath: reviewCanvasPath,
                };
            } catch (fallbackError) {
                console.error('Fallback generation also failed:', fallbackError);
                return { success: false };
            }
        }
    }

    /**
     * Story 14.5: AC4 - Store relationship to Graphiti
     * Creates (review)-[:GENERATED_FROM]->(original) relationship
     */
    private async storeGraphitiRelationship(
        originalCanvasPath: string,
        reviewCanvasPath: string,
        mode: 'fresh' | 'targeted'
    ): Promise<void> {
        try {
            // Call Graphiti MCP to store relationship
            const response = await fetch('http://localhost:8000/api/v1/memory/relationship', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    entity1: reviewCanvasPath,
                    entity2: originalCanvasPath,
                    relationship_type: 'GENERATED_FROM',
                    metadata: {
                        mode: mode,
                        timestamp: new Date().toISOString(),
                        type: 'review_canvas',
                    },
                }),
            });

            if (!response.ok) {
                console.warn('Failed to store Graphiti relationship:', response.status);
            }
        } catch (error) {
            // Log but don't fail - Graphiti storage is optional
            console.warn('Error storing Graphiti relationship:', error);
        }
    }

    // =========================================================================
    // Event Handlers
    // =========================================================================

    private handleTaskClick(task: ReviewTask): void {
        // Open the canvas file
        const file = this.app.vault.getAbstractFileByPath(task.canvasId);
        if (file) {
            this.app.workspace.openLinkText(task.canvasId, '', true);
        } else {
            new Notice(`⚠️ 找不到Canvas文件: ${task.canvasId}`);
        }
    }

    private handleTaskStart(task: ReviewTask): void {
        new Notice(`📖 开始复习: ${task.conceptName}`);

        // Open the canvas file
        const file = this.app.vault.getAbstractFileByPath(task.canvasId);
        if (file) {
            this.app.workspace.openLinkText(task.canvasId, '', true);
        }
    }

    private handleTaskDetails(task: ReviewTask): void {
        new Notice(`📋 ${task.conceptName}\n记忆强度: ${Math.round(task.memoryStrength * 100)}%\n保持率: ${Math.round(task.retentionRate * 100)}%`);
    }

    /**
     * Mark task as fully mastered
     * Story 14.4: AC4 - "标记为已掌握" context menu action
     *
     * Sets memory strength to 100% and schedules next review far in the future
     */
    private async handleMarkAsMastered(task: ReviewTask): Promise<void> {
        // Show confirmation dialog
        const confirmed = await this.showConfirmDialog(
            '确认标记为已掌握',
            `确定要将 "${task.conceptName}" 标记为已掌握吗？\n\n这将把记忆强度设为100%，并推迟下次复习时间。`
        );

        if (!confirmed) return;

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                // Set memory strength to 100%, retention to 100%
                // Schedule next review 30 days later
                await dataManager.updateReviewMetrics(
                    parseInt(task.id),
                    1.0, // Maximum memory strength
                    1.0, // Maximum retention rate
                    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days later
                );

                new Notice(`✅ 已标记为掌握: ${task.conceptName}`);
                await this.loadData();
            }
        } catch (error) {
            new Notice(`❌ 标记失败: ${(error as Error).message}`);
        }
    }

    /**
     * Reset task progress to initial state
     * Story 14.4: AC4 - "重置进度" context menu action
     *
     * Resets memory strength and schedules immediate review
     */
    private async handleResetProgress(task: ReviewTask): Promise<void> {
        // Show confirmation dialog
        const confirmed = await this.showConfirmDialog(
            '确认重置进度',
            `确定要重置 "${task.conceptName}" 的学习进度吗？\n\n这将清除所有学习记录，需要从头开始复习。`
        );

        if (!confirmed) return;

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                // Reset to initial values
                await dataManager.updateReviewMetrics(
                    parseInt(task.id),
                    0.3, // Low memory strength
                    0.5, // Base retention rate
                    new Date() // Due immediately
                );

                new Notice(`🔄 已重置进度: ${task.conceptName}`);
                await this.loadData();
            }
        } catch (error) {
            new Notice(`❌ 重置失败: ${(error as Error).message}`);
        }
    }

    /**
     * Generate review canvas file for the task
     * Story 14.4: AC2 - Calls generate_review_canvas_file()
     *
     * Creates a verification canvas for knowledge reproduction
     */
    private async handleGenerateReviewCanvas(task: ReviewTask): Promise<void> {
        try {
            new Notice(`📝 正在生成检验白板: ${task.conceptName}...`);

            // Call the plugin's canvas generation method
            // This integrates with the existing canvas learning system
            const canvasGenerator = (this.plugin as any).getCanvasGenerator?.();

            if (canvasGenerator && typeof canvasGenerator.generateReviewCanvas === 'function') {
                const reviewCanvasPath = await canvasGenerator.generateReviewCanvas(
                    task.canvasId,
                    task.conceptName
                );

                if (reviewCanvasPath) {
                    new Notice(`✅ 检验白板已生成: ${reviewCanvasPath}`);
                    // Open the generated canvas
                    await this.app.workspace.openLinkText(reviewCanvasPath, '', true);
                }
            } else {
                // Fallback: just open the original canvas with a notice
                new Notice(`⚠️ 检验白板生成功能需要Canvas Generator服务\n正在打开原白板...`);
                await this.app.workspace.openLinkText(task.canvasId, '', true);
            }
        } catch (error) {
            new Notice(`❌ 生成检验白板失败: ${(error as Error).message}`);
        }
    }

    /**
     * Show a confirmation dialog
     * Returns true if user confirms, false otherwise
     */
    private showConfirmDialog(title: string, message: string): Promise<boolean> {
        return new Promise((resolve) => {
            const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
            const dialog = overlay.createDiv({ cls: 'task-dialog confirm-dialog' });

            // Header
            const header = dialog.createDiv({ cls: 'dialog-header' });
            header.createEl('h3', { text: title, cls: 'dialog-title' });
            const closeBtn = header.createEl('button', { cls: 'dialog-close' });
            setIcon(closeBtn, 'x');
            closeBtn.onclick = () => {
                overlay.remove();
                resolve(false);
            };

            // Body
            const body = dialog.createDiv({ cls: 'dialog-body' });
            body.createEl('p', { text: message });

            // Actions
            const actions = dialog.createDiv({ cls: 'dialog-actions' });

            const cancelBtn = actions.createEl('button', {
                cls: 'task-action-btn secondary',
                text: '取消',
            });
            cancelBtn.onclick = () => {
                overlay.remove();
                resolve(false);
            };

            const confirmBtn = actions.createEl('button', {
                cls: 'task-action-btn primary',
                text: '确认',
            });
            confirmBtn.onclick = () => {
                overlay.remove();
                resolve(true);
            };

            // Close on overlay click
            overlay.onclick = (e) => {
                if (e.target === overlay) {
                    overlay.remove();
                    resolve(false);
                }
            };
        });
    }

    private async handleTaskComplete(task: ReviewTask, score: number = 3): Promise<void> {
        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                // Update memory metrics (simulated completion)
                await dataManager.updateReviewMetrics(
                    parseInt(task.id),
                    Math.min(task.memoryStrength + 0.1, 1),
                    Math.min(task.retentionRate + 0.05, 1),
                    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // Next review in 7 days
                );

                new Notice(`✅ 已完成复习: ${task.conceptName}`);
                await this.loadData();
            }
        } catch (error) {
            new Notice(`❌ 完成复习失败: ${(error as Error).message}`);
        }
    }

    private async handleTaskPostpone(task: ReviewTask, days: number = 1): Promise<void> {
        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                // Postpone by specified days
                await dataManager.updateReviewMetrics(
                    parseInt(task.id),
                    task.memoryStrength,
                    task.retentionRate,
                    new Date(Date.now() + days * 24 * 60 * 60 * 1000)
                );

                new Notice(`⏰ 已推迟复习: ${task.conceptName} (${days}天)`);
                await this.loadData();
            }
        } catch (error) {
            new Notice(`❌ 推迟复习失败: ${(error as Error).message}`);
        }
    }

    private handleStartReview(): void {
        const pendingTasks = this.state.tasks.filter((t) => t.status === 'pending');
        if (pendingTasks.length === 0) {
            new Notice('🎉 今日所有复习任务已完成！');
            return;
        }

        // Open first task's canvas
        const firstTask = pendingTasks[0];
        new Notice(`📖 开始复习: ${firstTask.conceptName}`);

        // TODO: Navigate to canvas file
    }

    private handleGeneratePlan(): void {
        new Notice('📋 生成复习计划功能即将上线');
    }

    private handleViewCalendar(): void {
        new Notice('📅 复习日历功能即将上线');
    }

    private handleOpenSettings(): void {
        // Open settings tab
        (this.app as any).setting.open();
        (this.app as any).setting.openTabById('canvas-review-system');
    }

    // =========================================================================
    // Styles
    // =========================================================================

    private loadStyles(): void {
        // Styles are loaded via styles.css in the plugin
    }
}
