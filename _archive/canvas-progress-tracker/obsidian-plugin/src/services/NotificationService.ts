/**
 * Notification Service - Canvas Learning System
 *
 * Service for managing review reminder notifications.
 * Implements Story 14.7: 复习提醒通知
 *
 * @module NotificationService
 * @version 1.0.0
 */

import { Notice, Workspace } from 'obsidian';
import type { App } from 'obsidian';
import type { DataManager } from '../database/DataManager';

/**
 * Notification settings interface
 */
export interface NotificationSettings {
    /** Enable/disable notifications */
    enableNotifications: boolean;
    /** Quiet hours start (0-23) */
    quietHoursStart: number;
    /** Quiet hours end (0-23) */
    quietHoursEnd: number;
    /** Minimum interval between notifications (hours) */
    minIntervalHours: number;
}

/**
 * Default notification settings
 */
export const DEFAULT_NOTIFICATION_SETTINGS: NotificationSettings = {
    enableNotifications: true,
    quietHoursStart: 23,  // 11 PM
    quietHoursEnd: 7,     // 7 AM
    minIntervalHours: 12,
};

/**
 * Storage key for last notification timestamp
 */
const LAST_NOTIFICATION_KEY = 'canvas-learning-last-notification';

/**
 * Service for managing review reminder notifications
 */
export class NotificationService {
    private app: App;
    private dataManager: DataManager | null = null;
    private settings: NotificationSettings;
    private onDashboardOpen: (() => void) | null = null;

    constructor(app: App, settings?: Partial<NotificationSettings>) {
        this.app = app;
        this.settings = { ...DEFAULT_NOTIFICATION_SETTINGS, ...settings };
    }

    /**
     * Set data manager reference
     */
    setDataManager(dataManager: DataManager): void {
        this.dataManager = dataManager;
    }

    /**
     * Update notification settings
     */
    updateSettings(settings: Partial<NotificationSettings>): void {
        this.settings = { ...this.settings, ...settings };
    }

    /**
     * Set callback for opening dashboard
     */
    setDashboardOpenCallback(callback: () => void): void {
        this.onDashboardOpen = callback;
    }

    /**
     * Check and show notification if needed
     * Called on app layout ready
     */
    async checkAndShowNotification(): Promise<void> {
        if (!this.shouldShowNotification()) {
            return;
        }

        const pendingCount = await this.getTodayPendingCount();

        if (pendingCount > 0) {
            this.showReviewNotification(pendingCount);
            this.recordNotificationTime();
        }
    }

    /**
     * Get count of today's pending reviews
     */
    async getTodayPendingCount(): Promise<number> {
        if (!this.dataManager) {
            console.warn('[NotificationService] Data manager not initialized');
            return 0;
        }

        try {
            const reviewRecordDAO = this.dataManager.getReviewRecordDAO();
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // Get reviews due today that haven't been completed
            const pendingReviews = await reviewRecordDAO.getPendingReviewsForDate(today);
            return pendingReviews.length;
        } catch (error) {
            console.error('[NotificationService] Failed to get pending count:', error);
            return 0;
        }
    }

    /**
     * Check if notification should be shown
     */
    shouldShowNotification(): boolean {
        // Check if notifications are enabled
        if (!this.settings.enableNotifications) {
            return false;
        }

        // Check quiet hours
        if (this.isInQuietHours()) {
            return false;
        }

        // Check minimum interval
        if (!this.hasMinIntervalPassed()) {
            return false;
        }

        return true;
    }

    /**
     * Check if current time is within quiet hours
     */
    isInQuietHours(): boolean {
        const now = new Date();
        const currentHour = now.getHours();
        const { quietHoursStart, quietHoursEnd } = this.settings;

        // Handle overnight quiet hours (e.g., 23:00 - 07:00)
        if (quietHoursStart > quietHoursEnd) {
            return currentHour >= quietHoursStart || currentHour < quietHoursEnd;
        }

        // Handle same-day quiet hours (e.g., 02:00 - 06:00)
        return currentHour >= quietHoursStart && currentHour < quietHoursEnd;
    }

    /**
     * Check if minimum interval has passed since last notification
     */
    hasMinIntervalPassed(): boolean {
        const lastNotification = this.getLastNotificationTime();

        if (!lastNotification) {
            return true;
        }

        const now = Date.now();
        const intervalMs = this.settings.minIntervalHours * 60 * 60 * 1000;

        return (now - lastNotification) >= intervalMs;
    }

    /**
     * Get last notification timestamp from storage
     */
    getLastNotificationTime(): number | null {
        try {
            const stored = localStorage.getItem(LAST_NOTIFICATION_KEY);
            if (stored) {
                return parseInt(stored, 10);
            }
        } catch (error) {
            console.warn('[NotificationService] Failed to read last notification time:', error);
        }
        return null;
    }

    /**
     * Record current time as last notification time
     */
    recordNotificationTime(): void {
        try {
            localStorage.setItem(LAST_NOTIFICATION_KEY, Date.now().toString());
        } catch (error) {
            console.warn('[NotificationService] Failed to record notification time:', error);
        }
    }

    /**
     * Show review notification
     */
    showReviewNotification(pendingCount: number): void {
        const message = this.formatNotificationMessage(pendingCount);

        // Create notice with longer timeout (10 seconds)
        const notice = new Notice('', 10000);

        // Create clickable content
        const fragment = document.createDocumentFragment();

        const container = document.createElement('div');
        container.className = 'review-notification';

        const icon = document.createElement('span');
        icon.className = 'notification-icon';
        icon.textContent = '📚';
        container.appendChild(icon);

        const text = document.createElement('span');
        text.className = 'notification-text';
        text.textContent = message;
        container.appendChild(text);

        const action = document.createElement('span');
        action.className = 'notification-action';
        action.textContent = ' (点击查看)';
        container.appendChild(action);

        // Make entire notice clickable
        container.addEventListener('click', () => {
            notice.hide();
            this.openDashboard();
        });

        fragment.appendChild(container);

        // Replace notice content
        const noticeEl = (notice as any).noticeEl;
        if (noticeEl) {
            noticeEl.empty();
            noticeEl.appendChild(fragment);
            noticeEl.addClass('review-reminder-notice');
        }
    }

    /**
     * Format notification message
     */
    formatNotificationMessage(pendingCount: number): string {
        if (pendingCount === 1) {
            return '今日有 1 个概念需要复习';
        }
        return `今日有 ${pendingCount} 个概念需要复习`;
    }

    /**
     * Open review dashboard
     */
    openDashboard(): void {
        if (this.onDashboardOpen) {
            this.onDashboardOpen();
        } else {
            // Fallback: activate review dashboard leaf
            const workspace = this.app.workspace;
            const leaves = workspace.getLeavesOfType('review-dashboard');

            if (leaves.length > 0) {
                workspace.setActiveLeaf(leaves[0], { focus: true });
            } else {
                // Open new dashboard
                workspace.getRightLeaf(false)?.setViewState({
                    type: 'review-dashboard',
                    active: true,
                });
            }
        }
    }

    /**
     * Reset notification state (for testing)
     */
    resetNotificationState(): void {
        try {
            localStorage.removeItem(LAST_NOTIFICATION_KEY);
        } catch (error) {
            console.warn('[NotificationService] Failed to reset notification state:', error);
        }
    }
}

/**
 * Create notification service instance
 */
export function createNotificationService(
    app: App,
    settings?: Partial<NotificationSettings>
): NotificationService {
    return new NotificationService(app, settings);
}
