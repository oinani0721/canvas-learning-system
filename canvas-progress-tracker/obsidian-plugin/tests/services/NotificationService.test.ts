/**
 * NotificationService Tests - Canvas Learning System
 *
 * Tests for Story 14.7: 复习提醒通知
 *
 * @module NotificationService.test
 * @version 1.0.0
 */

import {
    NotificationService,
    NotificationSettings,
    DEFAULT_NOTIFICATION_SETTINGS,
    createNotificationService,
} from '../../src/services/NotificationService';

// Mock Obsidian Notice
jest.mock('obsidian', () => ({
    Notice: jest.fn().mockImplementation(() => ({
        noticeEl: {
            empty: jest.fn(),
            appendChild: jest.fn(),
            addClass: jest.fn(),
        },
        hide: jest.fn(),
    })),
}));

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: jest.fn((key: string) => store[key] || null),
        setItem: jest.fn((key: string, value: string) => {
            store[key] = value;
        }),
        removeItem: jest.fn((key: string) => {
            delete store[key];
        }),
        clear: jest.fn(() => {
            store = {};
        }),
    };
})();

Object.defineProperty(global, 'localStorage', {
    value: localStorageMock,
});

// Mock document.createDocumentFragment and createElement
Object.defineProperty(global, 'document', {
    value: {
        createDocumentFragment: jest.fn().mockReturnValue({
            appendChild: jest.fn(),
        }),
        createElement: jest.fn().mockImplementation((tag: string) => ({
            className: '',
            textContent: '',
            appendChild: jest.fn(),
            addEventListener: jest.fn(),
        })),
    },
});

// Mock App
const mockApp = {
    workspace: {
        getLeavesOfType: jest.fn().mockReturnValue([]),
        setActiveLeaf: jest.fn(),
        getRightLeaf: jest.fn().mockReturnValue({
            setViewState: jest.fn(),
        }),
    },
} as any;

// Mock DataManager
const createMockDataManager = (pendingCount: number = 0) => ({
    getReviewRecordDAO: jest.fn().mockReturnValue({
        getPendingReviewsForDate: jest.fn().mockResolvedValue(
            Array(pendingCount).fill({
                id: 1,
                canvasId: 'test.canvas',
                conceptName: 'Test Concept',
                status: 'pending',
            })
        ),
    }),
});

describe('NotificationService', () => {
    let service: NotificationService;
    let originalDate: typeof Date;

    beforeAll(() => {
        originalDate = global.Date;
    });

    afterAll(() => {
        global.Date = originalDate;
    });

    beforeEach(() => {
        jest.useFakeTimers();
        localStorageMock.clear();
        service = new NotificationService(mockApp);
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.clearAllMocks();
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
        });

        it('should merge custom settings with defaults', () => {
            const customSettings: Partial<NotificationSettings> = {
                enableNotifications: false,
                quietHoursStart: 22,
            };
            const customService = new NotificationService(mockApp, customSettings);
            expect(customService).toBeDefined();
        });

        it('should update settings', () => {
            service.updateSettings({ enableNotifications: false });
            expect(service.shouldShowNotification()).toBe(false);
        });
    });

    describe('Quiet Hours', () => {
        it('should detect quiet hours (overnight range 23:00-07:00)', () => {
            // At midnight (0:00) - should be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 0, 0, 0));
            expect(service.isInQuietHours()).toBe(true);

            // At 6:00 AM - should be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 6, 0, 0));
            expect(service.isInQuietHours()).toBe(true);

            // At 8:00 AM - should NOT be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 8, 0, 0));
            expect(service.isInQuietHours()).toBe(false);

            // At 10:00 PM - should NOT be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 22, 0, 0));
            expect(service.isInQuietHours()).toBe(false);

            // At 11:00 PM - should be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 23, 0, 0));
            expect(service.isInQuietHours()).toBe(true);
        });

        it('should handle same-day quiet hours (e.g., 02:00-06:00)', () => {
            service.updateSettings({
                quietHoursStart: 2,
                quietHoursEnd: 6,
            });

            // At 3:00 AM - should be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 3, 0, 0));
            expect(service.isInQuietHours()).toBe(true);

            // At 8:00 AM - should NOT be in quiet hours
            jest.setSystemTime(new Date(2025, 0, 1, 8, 0, 0));
            expect(service.isInQuietHours()).toBe(false);
        });
    });

    describe('Notification Interval', () => {
        it('should allow notification when no previous notification', () => {
            expect(service.hasMinIntervalPassed()).toBe(true);
        });

        it('should block notification within minimum interval', () => {
            // Record a notification
            service.recordNotificationTime();

            // Immediately check - should not allow
            expect(service.hasMinIntervalPassed()).toBe(false);
        });

        it('should allow notification after minimum interval', () => {
            // Record a notification
            service.recordNotificationTime();

            // Advance time by 12 hours (default interval)
            jest.advanceTimersByTime(12 * 60 * 60 * 1000);

            expect(service.hasMinIntervalPassed()).toBe(true);
        });

        it('should respect custom interval setting', () => {
            service.updateSettings({ minIntervalHours: 6 });

            service.recordNotificationTime();

            // Advance by 5 hours - should not allow
            jest.advanceTimersByTime(5 * 60 * 60 * 1000);
            expect(service.hasMinIntervalPassed()).toBe(false);

            // Advance by 1 more hour (total 6) - should allow
            jest.advanceTimersByTime(1 * 60 * 60 * 1000);
            expect(service.hasMinIntervalPassed()).toBe(true);
        });
    });

    describe('shouldShowNotification', () => {
        it('should return false when notifications disabled', () => {
            service.updateSettings({ enableNotifications: false });
            expect(service.shouldShowNotification()).toBe(false);
        });

        it('should return false during quiet hours', () => {
            jest.setSystemTime(new Date(2025, 0, 1, 0, 0, 0)); // Midnight
            expect(service.shouldShowNotification()).toBe(false);
        });

        it('should return false within minimum interval', () => {
            jest.setSystemTime(new Date(2025, 0, 1, 10, 0, 0)); // 10 AM
            service.recordNotificationTime();
            expect(service.shouldShowNotification()).toBe(false);
        });

        it('should return true when all conditions met', () => {
            jest.setSystemTime(new Date(2025, 0, 1, 10, 0, 0)); // 10 AM
            expect(service.shouldShowNotification()).toBe(true);
        });
    });

    describe('Pending Count', () => {
        it('should return 0 when data manager not set', async () => {
            const count = await service.getTodayPendingCount();
            expect(count).toBe(0);
        });

        it('should return pending count from data manager', async () => {
            const mockDataManager = createMockDataManager(5);
            service.setDataManager(mockDataManager as any);

            const count = await service.getTodayPendingCount();
            expect(count).toBe(5);
        });

        it('should handle errors gracefully', async () => {
            const mockDataManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getPendingReviewsForDate: jest.fn().mockRejectedValue(new Error('DB Error')),
                }),
            };
            service.setDataManager(mockDataManager as any);

            const count = await service.getTodayPendingCount();
            expect(count).toBe(0);
        });
    });

    describe('Notification Message', () => {
        it('should format singular message', () => {
            const message = service.formatNotificationMessage(1);
            expect(message).toBe('今日有 1 个概念需要复习');
        });

        it('should format plural message', () => {
            const message = service.formatNotificationMessage(5);
            expect(message).toBe('今日有 5 个概念需要复习');
        });
    });

    describe('Dashboard Callback', () => {
        it('should use custom callback when set', () => {
            const callback = jest.fn();
            service.setDashboardOpenCallback(callback);
            service.openDashboard();
            expect(callback).toHaveBeenCalled();
        });

        it('should fall back to workspace navigation', () => {
            service.openDashboard();
            expect(mockApp.workspace.getLeavesOfType).toHaveBeenCalledWith('review-dashboard');
        });
    });

    describe('checkAndShowNotification', () => {
        it('should not show notification when conditions not met', async () => {
            jest.setSystemTime(new Date(2025, 0, 1, 0, 0, 0)); // Quiet hours
            await service.checkAndShowNotification();
            // Should not throw, should silently return
        });

        it('should not show notification when pending count is 0', async () => {
            jest.setSystemTime(new Date(2025, 0, 1, 10, 0, 0)); // 10 AM
            const mockDataManager = createMockDataManager(0);
            service.setDataManager(mockDataManager as any);

            await service.checkAndShowNotification();
            // Should not record notification time
            expect(service.hasMinIntervalPassed()).toBe(true);
        });

        it('should show notification and record time when pending', async () => {
            jest.setSystemTime(new Date(2025, 0, 1, 10, 0, 0)); // 10 AM
            const mockDataManager = createMockDataManager(3);
            service.setDataManager(mockDataManager as any);

            await service.checkAndShowNotification();
            // Should have recorded notification time
            expect(service.hasMinIntervalPassed()).toBe(false);
        });
    });

    describe('Reset State', () => {
        it('should reset notification state', () => {
            service.recordNotificationTime();
            expect(service.hasMinIntervalPassed()).toBe(false);

            service.resetNotificationState();
            expect(service.hasMinIntervalPassed()).toBe(true);
        });
    });
});

describe('DEFAULT_NOTIFICATION_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_NOTIFICATION_SETTINGS.enableNotifications).toBe(true);
        expect(DEFAULT_NOTIFICATION_SETTINGS.quietHoursStart).toBe(23);
        expect(DEFAULT_NOTIFICATION_SETTINGS.quietHoursEnd).toBe(7);
        expect(DEFAULT_NOTIFICATION_SETTINGS.minIntervalHours).toBe(12);
    });
});

describe('createNotificationService', () => {
    it('should create service instance', () => {
        const service = createNotificationService(mockApp);
        expect(service).toBeInstanceOf(NotificationService);
    });

    it('should create service with custom settings', () => {
        const service = createNotificationService(mockApp, {
            enableNotifications: false,
        });
        expect(service).toBeInstanceOf(NotificationService);
    });
});
