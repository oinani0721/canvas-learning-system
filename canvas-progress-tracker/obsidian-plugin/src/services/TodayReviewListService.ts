/**
 * TodayReviewListService - Canvas Learning System
 *
 * Story 14.4: 今日复习列表与交互
 *
 * Provides functionality for:
 * - Getting today's due review items (AC 1, 6)
 * - Starting review sessions (AC 2)
 * - Postponing reviews by days (AC 3)
 * - Context menu actions (Mark as Mastered, Reset Progress) (AC 4)
 * - Opening original canvas (AC 5)
 * - Displaying review statistics (AC 7)
 *
 * @module TodayReviewListService
 * @version 1.0.0
 */

import { App, Notice, Menu, TFile } from 'obsidian';
import type {
    ReviewTask,
    TaskPriority,
    TaskFilterOption,
    TaskSortOption,
} from '../types/UITypes';
import type { DataManager } from '../database/DataManager';
import type { ReviewRecord } from '../types/DataTypes';

/**
 * Priority urgency levels mapped to display colors
 */
export const PRIORITY_CONFIG: Record<TaskPriority, { label: string; color: string; weight: number }> = {
    critical: { label: '紧急', color: '#dc2626', weight: 4 },
    high: { label: '高', color: '#f59e0b', weight: 3 },
    medium: { label: '中', color: '#3b82f6', weight: 2 },
    low: { label: '低', color: '#6b7280', weight: 1 },
};

/**
 * Review item for today's list
 */
export interface TodayReviewItem extends ReviewTask {
    /** Canvas file path */
    canvasPath: string;
    /** Node ID in canvas */
    nodeId?: string;
    /** Days since last review */
    daysSinceLastReview: number;
    /** Scheduled review date from FSRS */
    scheduledDate: Date;
    /** Urgency label */
    urgencyLabel: string;
    /** Urgency color */
    urgencyColor: string;
}

/**
 * Today's review summary statistics
 */
export interface TodayReviewSummary {
    /** Total items due today */
    totalDueToday: number;
    /** Overdue items count */
    overdueCount: number;
    /** Completed today count */
    completedToday: number;
    /** Postponed today count */
    postponedToday: number;
    /** Critical priority count */
    criticalCount: number;
    /** High priority count */
    highCount: number;
    /** Medium priority count */
    mediumCount: number;
    /** Low priority count */
    lowCount: number;
}

/**
 * Context menu action types
 */
export type ContextMenuAction = 'start_review' | 'postpone_1d' | 'postpone_3d' | 'postpone_7d' | 'mark_mastered' | 'reset_progress' | 'open_canvas';

/**
 * TodayReviewListService
 *
 * Manages today's review list with full interaction support.
 *
 * ✅ Verified from Story 14.4 Dev Notes: TodayReviewListService类实现
 */
export class TodayReviewListService {
    private app: App;
    private dbManager: DataManager | null = null;
    private cache: Map<string, TodayReviewItem[]> = new Map();
    private cacheTimestamp: number = 0;
    private readonly CACHE_TTL_MS = 60000; // 1 minute cache

    constructor(app: App) {
        this.app = app;
    }

    /**
     * Set data manager reference
     */
    setDataManager(dataManager: DataManager): void {
        this.dbManager = dataManager;
        this.clearCache();
    }

    /**
     * Get today's review items sorted by priority
     * AC: 1, 6 - Display today's due concepts with priority sorting
     */
    async getTodayReviewItems(forceRefresh = false): Promise<TodayReviewItem[]> {
        // Check cache
        if (!forceRefresh && this.isCacheValid()) {
            return this.cache.get('today') || [];
        }

        if (!this.dbManager) {
            console.warn('[TodayReviewListService] Database manager not initialized');
            return [];
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const dueRecords = await reviewRecordDAO.getDueForReview(new Date());

            const items: TodayReviewItem[] = dueRecords.map((record: ReviewRecord) =>
                this.convertToTodayReviewItem(record)
            );

            // Sort by priority (default)
            const sortedItems = this.sortItems(items, 'priority');

            // Update cache
            this.cache.set('today', sortedItems);
            this.cacheTimestamp = Date.now();

            return sortedItems;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to get today review items:', error);
            return [];
        }
    }

    /**
     * Get review summary statistics for today
     * AC: 7 - Show review counts and statistics
     */
    async getTodayReviewSummary(): Promise<TodayReviewSummary> {
        const items = await this.getTodayReviewItems();
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        let completedToday = 0;
        let postponedToday = 0;

        if (this.dbManager) {
            try {
                const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
                const todayStats = await reviewRecordDAO.getDailyStats(new Date());
                completedToday = todayStats.completedCount;
                // Postponed count would need additional tracking
            } catch (error) {
                console.error('[TodayReviewListService] Failed to get today stats:', error);
            }
        }

        return {
            totalDueToday: items.length,
            overdueCount: items.filter(i => i.overdueDays > 0).length,
            completedToday,
            postponedToday,
            criticalCount: items.filter(i => i.priority === 'critical').length,
            highCount: items.filter(i => i.priority === 'high').length,
            mediumCount: items.filter(i => i.priority === 'medium').length,
            lowCount: items.filter(i => i.priority === 'low').length,
        };
    }

    /**
     * Start review for a specific item
     * AC: 2 - "Start Review" button calls generate_review_canvas_file()
     */
    async startReview(item: TodayReviewItem): Promise<boolean> {
        try {
            // Update status to in_progress
            if (this.dbManager && item.id) {
                const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
                const recordId = parseInt(item.id, 10);
                if (!isNaN(recordId)) {
                    await reviewRecordDAO.update(recordId, { status: 'scheduled' });
                }
            }

            // Open the canvas file
            await this.openCanvas(item);

            new Notice(`开始复习: ${item.conceptName}`);
            this.clearCache();
            return true;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to start review:', error);
            new Notice(`启动复习失败: ${(error as Error).message}`);
            return false;
        }
    }

    /**
     * Postpone review by specified days
     * AC: 3 - "Postpone 1 Day" button adjusts Card.due time
     */
    async postponeReview(item: TodayReviewItem, days: number): Promise<boolean> {
        if (!this.dbManager || !item.id) {
            new Notice('无法推迟: 数据库未初始化');
            return false;
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const recordId = parseInt(item.id, 10);

            if (isNaN(recordId)) {
                throw new Error('Invalid record ID');
            }

            const newDueDate = new Date(item.dueDate);
            newDueDate.setDate(newDueDate.getDate() + days);

            await reviewRecordDAO.update(recordId, {
                nextReviewDate: newDueDate,
                status: 'scheduled',
            });

            new Notice(`已推迟 ${days} 天: ${item.conceptName}`);
            this.clearCache();
            return true;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to postpone review:', error);
            new Notice(`推迟失败: ${(error as Error).message}`);
            return false;
        }
    }

    /**
     * Mark item as mastered
     * AC: 4 - Context menu "Mark as Mastered"
     */
    async markAsMastered(item: TodayReviewItem): Promise<boolean> {
        if (!this.dbManager || !item.id) {
            new Notice('无法标记: 数据库未初始化');
            return false;
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const recordId = parseInt(item.id, 10);

            if (isNaN(recordId)) {
                throw new Error('Invalid record ID');
            }

            // Set high memory strength and long interval for mastered items
            const masteredDate = new Date();
            masteredDate.setDate(masteredDate.getDate() + 90); // 90 days interval for mastered

            await reviewRecordDAO.updateMemoryMetrics(
                recordId,
                0.95, // High memory strength
                0.95, // High retention rate
                masteredDate
            );

            await reviewRecordDAO.update(recordId, {
                status: 'completed',
                difficultyLevel: 'easy',
            });

            new Notice(`已标记为掌握: ${item.conceptName}`);
            this.clearCache();
            return true;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to mark as mastered:', error);
            new Notice(`标记失败: ${(error as Error).message}`);
            return false;
        }
    }

    /**
     * Reset progress for an item
     * AC: 4 - Context menu "Reset Progress"
     */
    async resetProgress(item: TodayReviewItem): Promise<boolean> {
        if (!this.dbManager || !item.id) {
            new Notice('无法重置: 数据库未初始化');
            return false;
        }

        try {
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            const recordId = parseInt(item.id, 10);

            if (isNaN(recordId)) {
                throw new Error('Invalid record ID');
            }

            // Reset to initial learning state
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);

            await reviewRecordDAO.updateMemoryMetrics(
                recordId,
                0.3, // Low memory strength (new)
                0.5, // Medium retention rate
                tomorrow
            );

            await reviewRecordDAO.update(recordId, {
                status: 'pending',
                difficultyLevel: 'medium',
                reviewScore: undefined,
            });

            new Notice(`已重置进度: ${item.conceptName}`);
            this.clearCache();
            return true;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to reset progress:', error);
            new Notice(`重置失败: ${(error as Error).message}`);
            return false;
        }
    }

    /**
     * Open the original canvas file
     * AC: 5 - Click on canvas card opens original whiteboard
     */
    async openCanvas(item: TodayReviewItem): Promise<boolean> {
        try {
            const canvasPath = item.canvasPath || item.canvasId;

            if (!canvasPath) {
                new Notice('Canvas路径不存在');
                return false;
            }

            // Try to find the file
            const file = this.app.vault.getAbstractFileByPath(canvasPath);

            if (file instanceof TFile) {
                await this.app.workspace.openLinkText(canvasPath, '', false);
                return true;
            } else {
                // Try with .canvas extension if not found
                const canvasWithExt = canvasPath.endsWith('.canvas')
                    ? canvasPath
                    : `${canvasPath}.canvas`;

                const canvasFile = this.app.vault.getAbstractFileByPath(canvasWithExt);

                if (canvasFile instanceof TFile) {
                    await this.app.workspace.openLinkText(canvasWithExt, '', false);
                    return true;
                }
            }

            new Notice(`找不到Canvas文件: ${canvasPath}`);
            return false;
        } catch (error) {
            console.error('[TodayReviewListService] Failed to open canvas:', error);
            new Notice(`打开Canvas失败: ${(error as Error).message}`);
            return false;
        }
    }

    /**
     * Show context menu for a review item
     * AC: 4 - Right-click menu functionality
     */
    showContextMenu(event: MouseEvent, item: TodayReviewItem, onAction: (action: ContextMenuAction) => void): void {
        const menu = new Menu();

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('🎯 开始复习')
                .setIcon('play')
                .onClick(() => onAction('start_review'));
        });

        menu.addSeparator();

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('⏰ 推迟1天')
                .setIcon('clock')
                .onClick(() => onAction('postpone_1d'));
        });

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('📅 推迟3天')
                .setIcon('calendar')
                .onClick(() => onAction('postpone_3d'));
        });

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('🗓️ 推迟7天')
                .setIcon('calendar-days')
                .onClick(() => onAction('postpone_7d'));
        });

        menu.addSeparator();

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('✅ 标记为已掌握')
                .setIcon('check-circle')
                .onClick(() => onAction('mark_mastered'));
        });

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('🔄 重置进度')
                .setIcon('refresh-cw')
                .onClick(() => onAction('reset_progress'));
        });

        menu.addSeparator();

        menu.addItem((menuItem) => {
            menuItem
                .setTitle('📂 打开Canvas')
                .setIcon('file')
                .onClick(() => onAction('open_canvas'));
        });

        menu.showAtMouseEvent(event);
    }

    /**
     * Handle context menu action
     */
    async handleContextMenuAction(action: ContextMenuAction, item: TodayReviewItem): Promise<boolean> {
        switch (action) {
            case 'start_review':
                return await this.startReview(item);
            case 'postpone_1d':
                return await this.postponeReview(item, 1);
            case 'postpone_3d':
                return await this.postponeReview(item, 3);
            case 'postpone_7d':
                return await this.postponeReview(item, 7);
            case 'mark_mastered':
                return await this.markAsMastered(item);
            case 'reset_progress':
                return await this.resetProgress(item);
            case 'open_canvas':
                return await this.openCanvas(item);
            default:
                return false;
        }
    }

    /**
     * Sort review items by specified criteria
     * AC: 6 - Sort by urgency (urgent/high/medium/low)
     */
    sortItems(items: TodayReviewItem[], sortBy: TaskSortOption): TodayReviewItem[] {
        const sorted = [...items];

        switch (sortBy) {
            case 'priority':
                sorted.sort((a, b) => {
                    const weightA = PRIORITY_CONFIG[a.priority]?.weight || 0;
                    const weightB = PRIORITY_CONFIG[b.priority]?.weight || 0;
                    if (weightA !== weightB) {
                        return weightB - weightA; // Higher weight first
                    }
                    // Secondary sort by overdue days
                    return b.overdueDays - a.overdueDays;
                });
                break;

            case 'dueDate':
                sorted.sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime());
                break;

            case 'memoryStrength':
                sorted.sort((a, b) => a.memoryStrength - b.memoryStrength);
                break;

            case 'canvas':
                sorted.sort((a, b) => a.canvasTitle.localeCompare(b.canvasTitle));
                break;
        }

        return sorted;
    }

    /**
     * Filter review items
     */
    filterItems(items: TodayReviewItem[], filterBy: TaskFilterOption): TodayReviewItem[] {
        switch (filterBy) {
            case 'all':
                return items;

            case 'overdue':
                return items.filter(item => item.overdueDays > 0);

            case 'today':
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);

                return items.filter(item => {
                    const dueDate = new Date(item.dueDate);
                    dueDate.setHours(0, 0, 0, 0);
                    return dueDate.getTime() === today.getTime();
                });

            case 'high-priority':
                return items.filter(item =>
                    item.priority === 'critical' || item.priority === 'high'
                );

            default:
                return items;
        }
    }

    /**
     * Get filtered and sorted items
     */
    async getFilteredSortedItems(
        filterBy: TaskFilterOption,
        sortBy: TaskSortOption,
        forceRefresh = false
    ): Promise<TodayReviewItem[]> {
        const items = await this.getTodayReviewItems(forceRefresh);
        const filtered = this.filterItems(items, filterBy);
        return this.sortItems(filtered, sortBy);
    }

    /**
     * Convert a ReviewRecord to TodayReviewItem
     */
    private convertToTodayReviewItem(record: ReviewRecord): TodayReviewItem {
        const now = new Date();
        const dueDate = record.nextReviewDate
            ? new Date(record.nextReviewDate)
            : new Date();

        const overdueDays = Math.floor(
            (now.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24)
        );

        const lastReviewDate = record.reviewDate
            ? new Date(record.reviewDate)
            : undefined;

        const daysSinceLastReview = lastReviewDate
            ? Math.floor((now.getTime() - lastReviewDate.getTime()) / (1000 * 60 * 60 * 24))
            : 0;

        const priority = this.calculatePriority(overdueDays, record.memoryStrength);
        const priorityInfo = PRIORITY_CONFIG[priority];

        return {
            id: record.id?.toString() || `item-${Date.now()}-${Math.random()}`,
            canvasId: record.canvasId || '',
            canvasPath: record.canvasId || '',
            canvasTitle: this.extractCanvasTitle(record.canvasId || ''),
            conceptName: record.conceptId || 'Unknown Concept',
            nodeId: record.conceptId,
            priority,
            dueDate,
            overdueDays,
            memoryStrength: record.memoryStrength || 0,
            retentionRate: record.retentionRate || 0,
            reviewCount: 1, // Would need tracking in schema
            lastReviewDate,
            daysSinceLastReview,
            scheduledDate: dueDate,
            urgencyLabel: priorityInfo.label,
            urgencyColor: priorityInfo.color,
            status: this.mapStatus(record.status),
        };
    }

    /**
     * Calculate priority based on overdue days and memory strength
     */
    private calculatePriority(overdueDays: number, memoryStrength: number): TaskPriority {
        // Critical: overdue by 3+ days OR very low memory strength
        if (overdueDays >= 3 || memoryStrength < 0.2) {
            return 'critical';
        }

        // High: overdue by 1-2 days OR low memory strength
        if (overdueDays >= 1 || memoryStrength < 0.4) {
            return 'high';
        }

        // Medium: due today OR medium memory strength
        if (overdueDays >= 0 || memoryStrength < 0.6) {
            return 'medium';
        }

        // Low: not yet due and good memory strength
        return 'low';
    }

    /**
     * Map database status to UI status
     */
    private mapStatus(status: string | undefined): 'pending' | 'in_progress' | 'completed' | 'postponed' {
        switch (status) {
            case 'completed':
                return 'completed';
            case 'in_progress':
                return 'in_progress';
            case 'scheduled':
            case 'postponed':
                return 'postponed';
            default:
                return 'pending';
        }
    }

    /**
     * Extract canvas title from path
     */
    private extractCanvasTitle(canvasPath: string): string {
        if (!canvasPath) return 'Unknown Canvas';
        const parts = canvasPath.split('/');
        const fileName = parts[parts.length - 1];
        return fileName.replace('.canvas', '');
    }

    /**
     * Check if cache is still valid
     */
    private isCacheValid(): boolean {
        if (!this.cache.has('today')) {
            return false;
        }
        return Date.now() - this.cacheTimestamp < this.CACHE_TTL_MS;
    }

    /**
     * Clear the cache
     */
    clearCache(): void {
        this.cache.clear();
        this.cacheTimestamp = 0;
    }

    /**
     * Get priority configuration
     */
    getPriorityConfig(priority: TaskPriority): { label: string; color: string; weight: number } {
        return PRIORITY_CONFIG[priority];
    }
}

/**
 * Create TodayReviewListService instance
 */
export function createTodayReviewListService(app: App): TodayReviewListService {
    return new TodayReviewListService(app);
}
