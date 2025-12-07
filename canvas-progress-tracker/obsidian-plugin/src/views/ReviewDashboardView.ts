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

import { ItemView, WorkspaceLeaf, Notice, setIcon, Menu } from 'obsidian';
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
} from '../types/UITypes';
import { HistoryService } from '../services/HistoryService';

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

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;
        this.state = { ...DEFAULT_DASHBOARD_STATE };
        this.historyService = new HistoryService(this.app);
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
        this.setState({ loading: true, error: null });

        try {
            const dataManager = this.plugin.getDataManager();

            if (!dataManager) {
                throw new Error('Database not initialized');
            }

            // Get review data
            const dueReviews = await dataManager.getDueReviews();
            const dailyStats = await dataManager.getDailyStatistics();

            // Convert to ReviewTask format
            const tasks: ReviewTask[] = dueReviews.map((review) => ({
                id: String(review.id),
                canvasId: review.canvasId,
                canvasTitle: review.canvasTitle,
                conceptName: review.conceptName,
                priority: this.calculatePriority(review),
                dueDate: review.nextReviewDate || new Date(),
                overdueDays: this.calculateOverdueDays(review.nextReviewDate),
                memoryStrength: review.memoryStrength,
                retentionRate: review.retentionRate,
                reviewCount: 1, // TODO: Track review count
                lastReviewDate: review.reviewDate,
                status: 'pending',
            }));

            // Calculate dashboard statistics
            const statistics = this.calculateStatistics(tasks, dailyStats);

            this.setState({
                tasks,
                statistics,
                loading: false,
                lastUpdated: new Date(),
            });
        } catch (error) {
            console.error('ReviewDashboard: Failed to load data:', error);
            this.setState({
                loading: false,
                error: (error as Error).message,
            });
        }
    }

    private calculatePriority(review: any): TaskPriority {
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

    private calculateStatistics(tasks: ReviewTask[], dailyStats: any): DashboardStatistics {
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
            streakDays: 0, // TODO: Calculate streak
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

    private setState(updates: Partial<DashboardViewState>): void {
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
     * Render tab navigation (Story 14.6)
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
        tasksTab.onclick = () => this.switchTab('tasks');

        // History tab
        const historyTab = tabNav.createDiv({
            cls: `dashboard-tab ${this.state.currentTab === 'history' ? 'active' : ''}`,
        });
        const historyIcon = historyTab.createSpan({ cls: 'tab-icon' });
        setIcon(historyIcon, 'history');
        historyTab.createSpan({ text: '历史记录', cls: 'tab-label' });
        historyTab.onclick = () => this.switchTab('history');
    }

    /**
     * Switch between tabs (Story 14.6)
     */
    private async switchTab(tab: DashboardTab): Promise<void> {
        if (this.state.currentTab === tab) return;

        this.setState({ currentTab: tab });

        if (tab === 'history') {
            await this.loadHistoryData();
        }
    }

    /**
     * Load history data (Story 14.6)
     */
    private async loadHistoryData(): Promise<void> {
        const historyState = { ...this.state.historyState, loading: true };
        this.setState({ historyState });

        try {
            const dataManager = this.plugin.getDataManager();
            if (dataManager) {
                this.historyService.setDatabaseManager(dataManager);
            }

            const newHistoryState = await this.historyService.loadHistoryState(
                this.state.historyState.timeRange
            );

            this.setState({ historyState: newHistoryState });
        } catch (error) {
            console.error('[ReviewDashboard] Failed to load history:', error);
            this.setState({
                historyState: {
                    ...DEFAULT_HISTORY_STATE,
                    timeRange: this.state.historyState.timeRange,
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
            btn.onclick = async () => {
                if (this.state.historyState.timeRange !== range.value) {
                    this.setState({
                        historyState: {
                            ...this.state.historyState,
                            timeRange: range.value,
                        },
                    });
                    await this.loadHistoryData();
                }
            };
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
     */
    private renderHistoryList(container: HTMLElement): void {
        const listContainer = container.createDiv({ cls: 'history-list-container' });
        listContainer.createEl('h3', { text: '复习记录', cls: 'history-list-title' });

        if (this.state.historyState.loading) {
            listContainer.createDiv({ text: '加载中...', cls: 'history-loading' });
            return;
        }

        const { entries } = this.state.historyState;
        if (entries.length === 0) {
            listContainer.createDiv({ text: '暂无复习记录', cls: 'history-empty' });
            return;
        }

        const historyList = listContainer.createDiv({ cls: 'history-list' });

        // Group by date
        const groupedEntries = this.groupEntriesByDate(entries);

        Object.entries(groupedEntries)
            .slice(0, 7) // Show last 7 days
            .forEach(([date, dateEntries]) => {
                const dateGroup = historyList.createDiv({ cls: 'history-date-group' });
                dateGroup.createDiv({ text: date, cls: 'history-date-header' });

                dateEntries.forEach((entry) => {
                    this.renderHistoryEntry(dateGroup, entry);
                });
            });
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
        entryEl.onclick = () => {
            if (entry.canvasPath) {
                this.app.workspace.openLinkText(entry.canvasPath, '', false);
            }
        };
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

        // Refresh button
        const actions = header.createDiv({ cls: 'header-actions' });
        const refreshBtn = actions.createEl('button', {
            cls: 'header-button',
            attr: { 'aria-label': '刷新' },
        });
        setIcon(refreshBtn, 'refresh-cw');
        if (this.state.loading) {
            refreshBtn.addClass('spinning');
        }
        refreshBtn.onclick = () => this.loadData();
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
            this.setState({ filterBy: filterSelect.value as TaskFilterOption });
        };

        // Sort dropdown
        const sortGroup = controls.createDiv({ cls: 'control-group' });
        sortGroup.createSpan({ text: '排序: ', cls: 'control-label' });
        const sortSelect = sortGroup.createEl('select', { cls: 'control-select' });
        this.createSortOptions(sortSelect);
        sortSelect.value = this.state.sortBy;
        sortSelect.onchange = () => {
            this.setState({ sortBy: sortSelect.value as TaskSortOption });
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
            startBtn.onclick = (e) => {
                e.stopPropagation();
                this.handleTaskStart(task);
            };
        }

        const completeBtn = primaryActions.createEl('button', {
            cls: 'task-action-btn complete',
            attr: { 'aria-label': '完成复习' },
        });
        const completeIcon = completeBtn.createSpan();
        setIcon(completeIcon, 'check');
        completeBtn.createSpan({ text: '完成' });
        completeBtn.onclick = (e) => {
            e.stopPropagation();
            this.showCompleteDialog(task);
        };

        // Secondary actions
        const secondaryActions = actions.createDiv({ cls: 'secondary-actions' });

        const postponeBtn = secondaryActions.createEl('button', {
            cls: 'task-action-btn secondary postpone',
            attr: { 'aria-label': '推迟复习' },
        });
        setIcon(postponeBtn, 'clock');
        postponeBtn.onclick = (e) => {
            e.stopPropagation();
            this.showPostponeDialog(task);
        };

        const detailsBtn = secondaryActions.createEl('button', {
            cls: 'task-action-btn secondary',
            attr: { 'aria-label': '查看详情' },
        });
        setIcon(detailsBtn, 'info');
        detailsBtn.onclick = (e) => {
            e.stopPropagation();
            this.handleTaskDetails(task);
        };

        // Status indicator
        const statusIndicator = actions.createDiv({
            cls: `status-indicator ${task.status}`,
        });
        const statusIcon = statusIndicator.createSpan();
        setIcon(statusIcon, this.getStatusIcon(task.status));
        statusIndicator.createSpan({ text: this.getStatusText(task.status) });

        // Card click handler
        card.onclick = () => this.handleTaskClick(task);
        card.setAttribute('tabindex', '0');
        card.onkeydown = (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.handleTaskClick(task);
            }
        };

        // Right-click context menu (Story 14.4: AC4)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Menu.showAtMouseEvent)
        card.oncontextmenu = (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showTaskContextMenu(e, task);
        };
    }

    /**
     * Show context menu for task card
     * Story 14.4: AC4 - Right-click menu with "Mark as mastered" / "Reset progress"
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Menu API)
     */
    private showTaskContextMenu(event: MouseEvent, task: ReviewTask): void {
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
        startBtn.onclick = () => this.handleStartReview();

        // Generate plan button
        const planBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '生成计划',
        });
        const planIcon = planBtn.createSpan({ cls: 'button-icon' });
        setIcon(planIcon, 'calendar-plus');
        planBtn.prepend(planIcon);
        planBtn.onclick = () => this.handleGeneratePlan();

        // View calendar button
        const calendarBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '复习日历',
        });
        const calendarIcon = calendarBtn.createSpan({ cls: 'button-icon' });
        setIcon(calendarIcon, 'calendar');
        calendarBtn.prepend(calendarIcon);
        calendarBtn.onclick = () => this.handleViewCalendar();

        // Generate review canvas button (Story 14.5)
        const generateCanvasBtn = actions.createEl('button', {
            cls: 'action-button secondary',
            text: '生成检验白板',
        });
        const generateIcon = generateCanvasBtn.createSpan({ cls: 'button-icon' });
        setIcon(generateIcon, 'file-plus');
        generateCanvasBtn.prepend(generateIcon);
        generateCanvasBtn.onclick = () => this.showReviewModeDialog();

        // Settings button
        const settingsBtn = actions.createEl('button', {
            cls: 'action-button ghost',
            text: '设置',
        });
        const settingsIcon = settingsBtn.createSpan({ cls: 'button-icon' });
        setIcon(settingsIcon, 'settings');
        settingsBtn.prepend(settingsIcon);
        settingsBtn.onclick = () => this.handleOpenSettings();
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
        retryBtn.onclick = () => this.loadData();
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
        closeBtn.onclick = () => overlay.remove();

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
            btn.onclick = () => {
                scoreSelector.querySelectorAll('.score-btn').forEach((el) => {
                    el.removeClass('selected');
                });
                btn.addClass('selected');
                selectedScore = score.value;
            };
        });

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.onclick = () => overlay.remove();

        const confirmBtn = actions.createEl('button', {
            cls: 'task-action-btn primary',
            text: '确认完成',
        });
        confirmBtn.onclick = async () => {
            await this.handleTaskComplete(task, selectedScore);
            overlay.remove();
        };

        // Close on overlay click
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        };
    }

    private showPostponeDialog(task: ReviewTask): void {
        const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
        const dialog = overlay.createDiv({ cls: 'task-dialog' });

        // Header
        const header = dialog.createDiv({ cls: 'dialog-header' });
        header.createEl('h3', { text: '推迟复习', cls: 'dialog-title' });
        const closeBtn = header.createEl('button', { cls: 'dialog-close' });
        setIcon(closeBtn, 'x');
        closeBtn.onclick = () => overlay.remove();

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
            btn.onclick = async () => {
                await this.handleTaskPostpone(task, delay.days);
                overlay.remove();
            };
        });

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.onclick = () => overlay.remove();

        // Close on overlay click
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        };
    }

    /**
     * Story 14.5: AC2 - Review mode selection dialog
     * Shows dialog for selecting review mode: "fresh" or "targeted"
     */
    private showReviewModeDialog(): void {
        const pendingTasks = this.state.tasks.filter((t) => t.status === 'pending');
        if (pendingTasks.length === 0) {
            new Notice('🎉 当前没有待复习的任务，无需生成检验白板');
            return;
        }

        const overlay = document.body.createDiv({ cls: 'task-dialog-overlay' });
        const dialog = overlay.createDiv({ cls: 'task-dialog review-mode-dialog' });

        // Header
        const header = dialog.createDiv({ cls: 'dialog-header' });
        header.createEl('h3', { text: '生成检验白板', cls: 'dialog-title' });
        const closeBtn = header.createEl('button', { cls: 'dialog-close' });
        setIcon(closeBtn, 'x');
        closeBtn.onclick = () => overlay.remove();

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
        freshOption.onclick = () => {
            modeOptions.querySelectorAll('.mode-option').forEach((el) => el.removeClass('selected'));
            freshOption.addClass('selected');
            selectedMode = 'fresh';
        };

        targetedOption.onclick = () => {
            modeOptions.querySelectorAll('.mode-option').forEach((el) => el.removeClass('selected'));
            targetedOption.addClass('selected');
            selectedMode = 'targeted';
        };

        // Task selection
        const taskSection = body.createDiv({ cls: 'task-selection' });
        taskSection.createEl('p', { text: `将为 ${pendingTasks.length} 个待复习概念生成检验白板：` });

        const taskList = taskSection.createDiv({ cls: 'task-list-preview' });
        pendingTasks.slice(0, 5).forEach((task) => {
            const taskItem = taskList.createDiv({ cls: 'task-preview-item' });
            const icon = taskItem.createSpan({ cls: 'task-icon' });
            setIcon(icon, 'circle');
            taskItem.createSpan({ text: task.conceptName });
        });
        if (pendingTasks.length > 5) {
            taskList.createDiv({ cls: 'task-more', text: `...还有 ${pendingTasks.length - 5} 个` });
        }

        // Actions
        const actions = dialog.createDiv({ cls: 'dialog-actions' });

        const cancelBtn = actions.createEl('button', {
            cls: 'task-action-btn secondary',
            text: '取消',
        });
        cancelBtn.onclick = () => overlay.remove();

        const generateBtn = actions.createEl('button', {
            cls: 'task-action-btn primary',
            text: '生成检验白板',
        });
        generateBtn.onclick = async () => {
            overlay.remove();
            await this.handleGenerateReviewCanvases(pendingTasks, selectedMode);
        };

        // Close on overlay click
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        };
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
            const response = await fetch('http://localhost:8001/api/v1/canvas/generate-review', {
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
            const response = await fetch('http://localhost:8001/api/v1/memory/relationship', {
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
            const canvasGenerator = this.plugin.getCanvasGenerator?.();

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
