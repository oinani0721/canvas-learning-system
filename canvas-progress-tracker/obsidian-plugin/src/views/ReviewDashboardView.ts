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

import { ItemView, WorkspaceLeaf, Notice, setIcon } from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import {
    ReviewTask,
    DashboardStatistics,
    DashboardViewState,
    DEFAULT_DASHBOARD_STATE,
    TaskSortOption,
    TaskFilterOption,
    TaskPriority,
} from '../types/UITypes';

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

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;
        this.state = { ...DEFAULT_DASHBOARD_STATE };
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

        // Main content
        const content = dashboard.createDiv({ cls: 'dashboard-content' });

        // Task list (left side)
        const taskListContainer = content.createDiv({ cls: 'task-list-container' });
        this.renderTaskList(taskListContainer);

        // Sidebar (right side)
        const sidebar = content.createDiv({ cls: 'dashboard-sidebar' });
        this.renderStatistics(sidebar);
        this.renderQuickActions(sidebar);
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
