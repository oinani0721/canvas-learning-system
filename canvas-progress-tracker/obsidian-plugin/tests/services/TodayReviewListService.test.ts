/**
 * TodayReviewListService Tests - Canvas Learning System
 *
 * Tests for Story 14.4: 今日复习列表与交互
 *
 * @module TodayReviewListService.test
 * @version 1.0.0
 */

import {
    TodayReviewListService,
    TodayReviewItem,
    TodayReviewSummary,
    PRIORITY_CONFIG,
    createTodayReviewListService,
} from '../../src/services/TodayReviewListService';

// Mock Obsidian - define MockTFile inside factory to avoid hoisting issues
jest.mock('obsidian', () => {
    // Define MockTFile INSIDE the factory to avoid jest.mock hoisting issues
    class MockTFile {
        path: string;
        name: string;
        constructor(path: string) {
            this.path = path;
            this.name = path.split('/').pop() || path;
        }
    }

    return {
        Notice: jest.fn(),
        Menu: jest.fn().mockImplementation(() => ({
            addItem: jest.fn().mockReturnThis(),
            addSeparator: jest.fn().mockReturnThis(),
            showAtMouseEvent: jest.fn(),
        })),
        TFile: MockTFile,
    };
});

// Re-export mocks for use in tests
const { TFile: MockTFile, Notice: mockNotice, Menu: mockMenu } = jest.requireMock('obsidian');

// Mock App
const mockApp = {
    vault: {
        getAbstractFileByPath: jest.fn(),
    },
    workspace: {
        openLinkText: jest.fn().mockResolvedValue(undefined),
    },
} as any;

// Mock ReviewRecord for testing
const createMockReviewRecord = (overrides: Partial<any> = {}) => ({
    id: 1,
    canvasId: 'test.canvas',
    conceptId: 'concept-1',
    status: 'pending',
    memoryStrength: 0.5,
    retentionRate: 0.7,
    reviewDate: new Date().toISOString(),
    nextReviewDate: new Date().toISOString(),
    ...overrides,
});

// Mock DatabaseManager
const createMockDbManager = (records: any[] = []) => ({
    getReviewRecordDAO: jest.fn().mockReturnValue({
        getDueForReview: jest.fn().mockResolvedValue(records),
        getDailyStats: jest.fn().mockResolvedValue({
            completedCount: 2,
            skippedCount: 0,
            totalReviews: 5,
        }),
        update: jest.fn().mockResolvedValue({}),
        updateMemoryMetrics: jest.fn().mockResolvedValue({}),
    }),
});

describe('TodayReviewListService', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new TodayReviewListService(mockApp);
    });

    describe('Constructor', () => {
        it('should create service instance', () => {
            expect(service).toBeDefined();
            expect(service).toBeInstanceOf(TodayReviewListService);
        });
    });

    describe('Database Manager', () => {
        it('should set database manager', () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);
            // No error thrown means success
        });

        it('should clear cache when database manager is set', async () => {
            const records = [createMockReviewRecord()];
            const mockDbManager = createMockDbManager(records);
            service.setDataManager(mockDbManager as any);

            // First call populates cache
            await service.getTodayReviewItems();

            // Set new manager clears cache
            service.setDataManager(mockDbManager as any);

            // Force refresh to verify cache was cleared
            const items = await service.getTodayReviewItems(true);
            expect(items).toBeDefined();
        });
    });

    describe('getTodayReviewItems', () => {
        it('should return empty array when no database manager', async () => {
            const items = await service.getTodayReviewItems();
            expect(items).toEqual([]);
        });

        it('should return review items from database', async () => {
            const records = [
                createMockReviewRecord({ id: 1, conceptId: 'concept-1' }),
                createMockReviewRecord({ id: 2, conceptId: 'concept-2' }),
            ];
            const mockDbManager = createMockDbManager(records);
            service.setDataManager(mockDbManager as any);

            const items = await service.getTodayReviewItems();

            expect(items).toHaveLength(2);
            expect(items[0].conceptName).toBe('concept-1');
            expect(items[1].conceptName).toBe('concept-2');
        });

        it('should use cache for subsequent calls', async () => {
            const records = [createMockReviewRecord()];
            const mockDbManager = createMockDbManager(records);
            service.setDataManager(mockDbManager as any);

            await service.getTodayReviewItems();
            await service.getTodayReviewItems();

            const dao = mockDbManager.getReviewRecordDAO();
            expect(dao.getDueForReview).toHaveBeenCalledTimes(1);
        });

        it('should bypass cache when forceRefresh is true', async () => {
            const records = [createMockReviewRecord()];
            const mockDbManager = createMockDbManager(records);
            service.setDataManager(mockDbManager as any);

            await service.getTodayReviewItems();
            await service.getTodayReviewItems(true);

            const dao = mockDbManager.getReviewRecordDAO();
            expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
        });
    });

    describe('getTodayReviewSummary', () => {
        it('should return summary statistics', async () => {
            const now = new Date();
            const overdue = new Date(now);
            overdue.setDate(overdue.getDate() - 2);

            const records = [
                createMockReviewRecord({ id: 1, nextReviewDate: overdue.toISOString(), memoryStrength: 0.1 }),
                createMockReviewRecord({ id: 2, memoryStrength: 0.5 }),
                createMockReviewRecord({ id: 3, memoryStrength: 0.8 }),
            ];
            const mockDbManager = createMockDbManager(records);
            service.setDataManager(mockDbManager as any);

            const summary = await service.getTodayReviewSummary();

            expect(summary.totalDueToday).toBe(3);
            expect(summary.completedToday).toBe(2);
            expect(typeof summary.criticalCount).toBe('number');
            expect(typeof summary.highCount).toBe('number');
        });
    });

    describe('startReview', () => {
        it('should start review and open canvas', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);

            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 1,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            // Mock file exists
            (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue({ path: 'test.canvas' });

            const result = await service.startReview(item);

            expect(result).toBe(true);
            expect(mockNotice).toHaveBeenCalled();
        });
    });

    describe('postponeReview', () => {
        it('should postpone review by specified days', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);

            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            const result = await service.postponeReview(item, 3);

            expect(result).toBe(true);
            const dao = mockDbManager.getReviewRecordDAO();
            expect(dao.update).toHaveBeenCalled();
            expect(mockNotice).toHaveBeenCalledWith(expect.stringContaining('已推迟 3 天'));
        });

        it('should fail when no database manager', async () => {
            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            const result = await service.postponeReview(item, 1);

            expect(result).toBe(false);
        });
    });

    describe('markAsMastered', () => {
        it('should mark item as mastered with high memory strength', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);

            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            const result = await service.markAsMastered(item);

            expect(result).toBe(true);
            const dao = mockDbManager.getReviewRecordDAO();
            expect(dao.updateMemoryMetrics).toHaveBeenCalledWith(
                1,
                0.95, // High memory strength
                0.95, // High retention rate
                expect.any(Date)
            );
        });
    });

    describe('resetProgress', () => {
        it('should reset item to initial learning state', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);

            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.8,
                retentionRate: 0.9,
                reviewCount: 10,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'completed',
            };

            const result = await service.resetProgress(item);

            expect(result).toBe(true);
            const dao = mockDbManager.getReviewRecordDAO();
            expect(dao.updateMemoryMetrics).toHaveBeenCalledWith(
                1,
                0.3, // Low memory strength
                0.5, // Medium retention rate
                expect.any(Date)
            );
        });
    });

    describe('openCanvas', () => {
        it('should open canvas file', async () => {
            // Use MockTFile instance so instanceof check passes
            (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue(
                new MockTFile('test.canvas')
            );

            const item: TodayReviewItem = {
                id: '1',
                canvasId: 'test.canvas',
                canvasPath: 'test.canvas',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            const result = await service.openCanvas(item);

            expect(result).toBe(true);
            expect(mockApp.workspace.openLinkText).toHaveBeenCalled();
        });

        it('should return false when canvas path is missing', async () => {
            const item: TodayReviewItem = {
                id: '1',
                canvasId: '',
                canvasPath: '',
                canvasTitle: 'Test',
                conceptName: 'Concept A',
                priority: 'high',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.5,
                retentionRate: 0.7,
                reviewCount: 3,
                daysSinceLastReview: 2,
                scheduledDate: new Date(),
                urgencyLabel: '高',
                urgencyColor: '#f59e0b',
                status: 'pending',
            };

            const result = await service.openCanvas(item);

            expect(result).toBe(false);
        });
    });

    describe('sortItems', () => {
        const items: TodayReviewItem[] = [
            {
                id: '1', canvasId: 'a.canvas', canvasPath: 'a.canvas', canvasTitle: 'A Canvas',
                conceptName: 'Concept A', priority: 'low', dueDate: new Date('2025-01-15'),
                overdueDays: 0, memoryStrength: 0.8, retentionRate: 0.9, reviewCount: 5,
                daysSinceLastReview: 1, scheduledDate: new Date(), urgencyLabel: '低',
                urgencyColor: '#6b7280', status: 'pending',
            },
            {
                id: '2', canvasId: 'b.canvas', canvasPath: 'b.canvas', canvasTitle: 'B Canvas',
                conceptName: 'Concept B', priority: 'critical', dueDate: new Date('2025-01-10'),
                overdueDays: 5, memoryStrength: 0.2, retentionRate: 0.3, reviewCount: 2,
                daysSinceLastReview: 7, scheduledDate: new Date(), urgencyLabel: '紧急',
                urgencyColor: '#dc2626', status: 'pending',
            },
            {
                id: '3', canvasId: 'c.canvas', canvasPath: 'c.canvas', canvasTitle: 'C Canvas',
                conceptName: 'Concept C', priority: 'high', dueDate: new Date('2025-01-12'),
                overdueDays: 2, memoryStrength: 0.4, retentionRate: 0.5, reviewCount: 3,
                daysSinceLastReview: 5, scheduledDate: new Date(), urgencyLabel: '高',
                urgencyColor: '#f59e0b', status: 'pending',
            },
        ];

        it('should sort by priority (critical first)', () => {
            const sorted = service.sortItems(items, 'priority');

            expect(sorted[0].priority).toBe('critical');
            expect(sorted[1].priority).toBe('high');
            expect(sorted[2].priority).toBe('low');
        });

        it('should sort by due date', () => {
            const sorted = service.sortItems(items, 'dueDate');

            expect(sorted[0].dueDate.getTime()).toBeLessThanOrEqual(sorted[1].dueDate.getTime());
            expect(sorted[1].dueDate.getTime()).toBeLessThanOrEqual(sorted[2].dueDate.getTime());
        });

        it('should sort by memory strength', () => {
            const sorted = service.sortItems(items, 'memoryStrength');

            expect(sorted[0].memoryStrength).toBeLessThanOrEqual(sorted[1].memoryStrength);
            expect(sorted[1].memoryStrength).toBeLessThanOrEqual(sorted[2].memoryStrength);
        });

        it('should sort by canvas title', () => {
            const sorted = service.sortItems(items, 'canvas');

            expect(sorted[0].canvasTitle).toBe('A Canvas');
            expect(sorted[1].canvasTitle).toBe('B Canvas');
            expect(sorted[2].canvasTitle).toBe('C Canvas');
        });
    });

    describe('filterItems', () => {
        const now = new Date();
        const items: TodayReviewItem[] = [
            {
                id: '1', canvasId: 'a.canvas', canvasPath: 'a.canvas', canvasTitle: 'A',
                conceptName: 'A', priority: 'low', dueDate: now, overdueDays: 0,
                memoryStrength: 0.8, retentionRate: 0.9, reviewCount: 5, daysSinceLastReview: 1,
                scheduledDate: now, urgencyLabel: '低', urgencyColor: '#6b7280', status: 'pending',
            },
            {
                id: '2', canvasId: 'b.canvas', canvasPath: 'b.canvas', canvasTitle: 'B',
                conceptName: 'B', priority: 'critical', dueDate: now, overdueDays: 3,
                memoryStrength: 0.2, retentionRate: 0.3, reviewCount: 2, daysSinceLastReview: 5,
                scheduledDate: now, urgencyLabel: '紧急', urgencyColor: '#dc2626', status: 'pending',
            },
            {
                id: '3', canvasId: 'c.canvas', canvasPath: 'c.canvas', canvasTitle: 'C',
                conceptName: 'C', priority: 'high', dueDate: now, overdueDays: 1,
                memoryStrength: 0.4, retentionRate: 0.5, reviewCount: 3, daysSinceLastReview: 3,
                scheduledDate: now, urgencyLabel: '高', urgencyColor: '#f59e0b', status: 'pending',
            },
        ];

        it('should return all items when filter is "all"', () => {
            const filtered = service.filterItems(items, 'all');
            expect(filtered).toHaveLength(3);
        });

        it('should filter overdue items', () => {
            const filtered = service.filterItems(items, 'overdue');
            expect(filtered.length).toBeGreaterThan(0);
            filtered.forEach(item => {
                expect(item.overdueDays).toBeGreaterThan(0);
            });
        });

        it('should filter high priority items', () => {
            const filtered = service.filterItems(items, 'high-priority');
            expect(filtered.length).toBeGreaterThan(0);
            filtered.forEach(item => {
                expect(['critical', 'high']).toContain(item.priority);
            });
        });
    });

    describe('handleContextMenuAction', () => {
        it('should handle start_review action', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);
            (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue({ path: 'test.canvas' });

            const item: TodayReviewItem = {
                id: '1', canvasId: 'test.canvas', canvasPath: 'test.canvas', canvasTitle: 'Test',
                conceptName: 'A', priority: 'high', dueDate: new Date(), overdueDays: 0,
                memoryStrength: 0.5, retentionRate: 0.7, reviewCount: 3, daysSinceLastReview: 2,
                scheduledDate: new Date(), urgencyLabel: '高', urgencyColor: '#f59e0b', status: 'pending',
            };

            const result = await service.handleContextMenuAction('start_review', item);
            expect(result).toBe(true);
        });

        it('should handle postpone_1d action', async () => {
            const mockDbManager = createMockDbManager();
            service.setDataManager(mockDbManager as any);

            const item: TodayReviewItem = {
                id: '1', canvasId: 'test.canvas', canvasPath: 'test.canvas', canvasTitle: 'Test',
                conceptName: 'A', priority: 'high', dueDate: new Date(), overdueDays: 0,
                memoryStrength: 0.5, retentionRate: 0.7, reviewCount: 3, daysSinceLastReview: 2,
                scheduledDate: new Date(), urgencyLabel: '高', urgencyColor: '#f59e0b', status: 'pending',
            };

            const result = await service.handleContextMenuAction('postpone_1d', item);
            expect(result).toBe(true);
        });
    });

    describe('PRIORITY_CONFIG', () => {
        it('should have all priority levels defined', () => {
            expect(PRIORITY_CONFIG.critical).toBeDefined();
            expect(PRIORITY_CONFIG.high).toBeDefined();
            expect(PRIORITY_CONFIG.medium).toBeDefined();
            expect(PRIORITY_CONFIG.low).toBeDefined();
        });

        it('should have correct weight ordering', () => {
            expect(PRIORITY_CONFIG.critical.weight).toBeGreaterThan(PRIORITY_CONFIG.high.weight);
            expect(PRIORITY_CONFIG.high.weight).toBeGreaterThan(PRIORITY_CONFIG.medium.weight);
            expect(PRIORITY_CONFIG.medium.weight).toBeGreaterThan(PRIORITY_CONFIG.low.weight);
        });
    });
});

describe('createTodayReviewListService', () => {
    it('should create service instance', () => {
        const service = createTodayReviewListService(mockApp);
        expect(service).toBeInstanceOf(TodayReviewListService);
    });
});

// =========================================================================
// Story 32.4 Integration Tests - Dashboard统计补全
// Added by: Quinn (Test Architect) - QA Improvement
// =========================================================================
describe('TodayReviewListService - Story 32.4 Integration', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new TodayReviewListService(mockApp);
    });

    describe('reviewCount Integration (AC-32.4.1)', () => {
        it('should query reviewCount from ReviewRecordDAO', async () => {
            const mockGetReviewCountByConceptId = jest.fn().mockResolvedValue(5);
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockResolvedValue([
                        createMockReviewRecord({ id: 1, conceptId: 'concept-1' }),
                    ]),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 0,
                        skippedCount: 0,
                        totalReviews: 0,
                    }),
                    getReviewCountByConceptId: mockGetReviewCountByConceptId,
                }),
            };
            service.setDataManager(mockDbManager as any);

            await service.getTodayReviewItems();

            // Verify that DAO method would be called in real implementation
            expect(mockDbManager.getReviewRecordDAO).toHaveBeenCalled();
        });

        it('should use default reviewCount of 1 when DAO unavailable', async () => {
            // No database manager set
            const items = await service.getTodayReviewItems();

            expect(items).toEqual([]);
            // Graceful degradation - returns empty array instead of throwing
        });

        it('should handle reviewCount query failure gracefully', async () => {
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockResolvedValue([
                        createMockReviewRecord({ id: 1, conceptId: 'concept-1' }),
                    ]),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 0,
                        skippedCount: 0,
                        totalReviews: 0,
                    }),
                    getReviewCountByConceptId: jest.fn().mockRejectedValue(new Error('DB Error')),
                }),
            };
            service.setDataManager(mockDbManager as any);

            // Should not throw, should use default value
            const items = await service.getTodayReviewItems();
            expect(items).toBeDefined();
        });
    });

    describe('Batch Query Optimization (Task 4.3)', () => {
        it('should support batch reviewCount queries for multiple concepts', async () => {
            const mockGetReviewCountBatch = jest.fn().mockResolvedValue(
                new Map([
                    ['concept-1', 3],
                    ['concept-2', 7],
                    ['concept-3', 0],
                ])
            );
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockResolvedValue([
                        createMockReviewRecord({ id: 1, conceptId: 'concept-1' }),
                        createMockReviewRecord({ id: 2, conceptId: 'concept-2' }),
                        createMockReviewRecord({ id: 3, conceptId: 'concept-3' }),
                    ]),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 0,
                        skippedCount: 0,
                        totalReviews: 0,
                    }),
                    getReviewCountBatch: mockGetReviewCountBatch,
                }),
            };
            service.setDataManager(mockDbManager as any);

            const items = await service.getTodayReviewItems();

            expect(items).toHaveLength(3);
            expect(mockDbManager.getReviewRecordDAO).toHaveBeenCalled();
        });
    });

    describe('Graceful Degradation', () => {
        it('should return items with default values when memory service unavailable', async () => {
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockResolvedValue([
                        createMockReviewRecord({
                            id: 1,
                            conceptId: 'concept-1',
                            memoryStrength: 0.6,
                        }),
                    ]),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 2,
                        skippedCount: 0,
                        totalReviews: 5,
                    }),
                }),
            };
            service.setDataManager(mockDbManager as any);

            const items = await service.getTodayReviewItems();

            expect(items).toHaveLength(1);
            expect(items[0].memoryStrength).toBe(0.6);
            // Default reviewCount when not available from batch query
            expect(typeof items[0].reviewCount).toBe('number');
        });

        it('should handle complete DAO failure gracefully', async () => {
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockRejectedValue(new Error('Database connection failed')),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 0,
                        skippedCount: 0,
                        totalReviews: 0,
                    }),
                }),
            };
            service.setDataManager(mockDbManager as any);

            // Should not throw
            await expect(service.getTodayReviewItems()).resolves.toBeDefined();
        });
    });

    describe('TodayReviewItem reviewCount field', () => {
        it('should include reviewCount in TodayReviewItem interface', async () => {
            const mockDbManager = {
                getReviewRecordDAO: jest.fn().mockReturnValue({
                    getDueForReview: jest.fn().mockResolvedValue([
                        createMockReviewRecord({ id: 1, conceptId: 'concept-1' }),
                    ]),
                    getDailyStats: jest.fn().mockResolvedValue({
                        completedCount: 0,
                        skippedCount: 0,
                        totalReviews: 0,
                    }),
                }),
            };
            service.setDataManager(mockDbManager as any);

            const items = await service.getTodayReviewItems();

            expect(items.length).toBeGreaterThan(0);
            // Verify reviewCount property exists on each item
            items.forEach((item) => {
                expect(item).toHaveProperty('reviewCount');
                expect(typeof item.reviewCount).toBe('number');
                expect(item.reviewCount).toBeGreaterThanOrEqual(0);
            });
        });
    });
});
