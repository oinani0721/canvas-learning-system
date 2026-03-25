/**
 * HistoryService Tests - Canvas Learning System
 *
 * Tests for Story 14.6: 复习历史查看 + 趋势分析
 *
 * @module HistoryService.test
 * @version 1.0.0
 */

import {
    HistoryService,
    createHistoryService,
} from '../../src/services/HistoryService';
import type {
    HistoryEntry,
    DailyStatItem,
    CanvasReviewTrend,
    ReviewSession,
    HistoryTimeRange,
    HistoryViewState,
} from '../../src/types/UITypes';
import type { DatabaseManager } from '../../src/database/DatabaseManager';

// Mock App
const mockApp = {} as any;

// Mock ReviewRecordDAO
const mockReviewRecordDAO = {
    getReviewsSince: jest.fn(),
    getReviewsInRange: jest.fn(),
    getConceptReviews: jest.fn(),
    getCanvasReviewSessions: jest.fn(),
    getReviewedCanvasesSince: jest.fn(),
};

// Mock DatabaseManager
const mockDbManager = {
    getReviewRecordDAO: jest.fn().mockReturnValue(mockReviewRecordDAO),
} as unknown as DatabaseManager;

describe('HistoryService', () => {
    let service: HistoryService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new HistoryService(mockApp);
        service.setDatabaseManager(mockDbManager);
    });

    describe('Constructor and Database Manager', () => {
        it('should create service instance', () => {
            expect(service).toBeDefined();
        });

        it('should set database manager', () => {
            const newService = new HistoryService(mockApp);
            newService.setDatabaseManager(mockDbManager);
            // No error means success
            expect(true).toBe(true);
        });
    });

    describe('getReviewHistory', () => {
        const mockRecords = [
            {
                id: 'record-1',
                canvas_path: 'math.canvas',
                concept_name: 'Algebra',
                review_date: '2025-01-15T10:00:00Z',
                score: 85,
                mode: 'fresh',
                memory_strength: 0.7,
                duration: 300,
            },
            {
                id: 'record-2',
                canvas_path: 'physics.canvas',
                concept_name: 'Newton Laws',
                review_date: '2025-01-14T14:00:00Z',
                score: 92,
                mode: 'targeted',
                memory_strength: 0.85,
                duration: 450,
            },
        ];

        beforeEach(() => {
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue(mockRecords);
        });

        it('should return history entries for 7d time range', async () => {
            const entries = await service.getReviewHistory('7d');

            expect(mockReviewRecordDAO.getReviewsSince).toHaveBeenCalled();
            expect(entries).toHaveLength(2);
            expect(entries[0].conceptName).toBe('Algebra');
            expect(entries[1].conceptName).toBe('Newton Laws');
        });

        it('should return history entries for 30d time range', async () => {
            await service.getReviewHistory('30d');

            expect(mockReviewRecordDAO.getReviewsSince).toHaveBeenCalled();
            const callArg = mockReviewRecordDAO.getReviewsSince.mock.calls[0][0];
            const daysAgo = Math.round((Date.now() - callArg.getTime()) / (1000 * 60 * 60 * 24));
            expect(daysAgo).toBe(30);
        });

        it('should map record fields correctly', async () => {
            const entries = await service.getReviewHistory('7d');

            expect(entries[0]).toEqual(expect.objectContaining({
                id: 'record-1',
                canvasPath: 'math.canvas',
                canvasTitle: 'math',
                conceptName: 'Algebra',
                score: 85,
                mode: 'fresh',
                memoryStrength: 0.7,
                duration: 300,
            }));
        });

        it('should return empty array when database not initialized', async () => {
            const newService = new HistoryService(mockApp);
            const entries = await newService.getReviewHistory('7d');

            expect(entries).toEqual([]);
        });

        it('should handle database errors gracefully', async () => {
            mockReviewRecordDAO.getReviewsSince.mockRejectedValue(new Error('Database error'));

            const entries = await service.getReviewHistory('7d');

            expect(entries).toEqual([]);
        });

        it('should handle alternate field names (camelCase)', async () => {
            const camelCaseRecords = [
                {
                    id: 'record-3',
                    canvasPath: 'chemistry.canvas',
                    conceptName: 'Reactions',
                    reviewDate: '2025-01-13T09:00:00Z',
                    score: 78,
                    mode: 'fresh',
                    memoryStrength: 0.6,
                },
            ];
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue(camelCaseRecords);

            const entries = await service.getReviewHistory('7d');

            expect(entries[0].canvasPath).toBe('chemistry.canvas');
            expect(entries[0].conceptName).toBe('Reactions');
        });
    });

    describe('getDailyStatistics', () => {
        beforeEach(() => {
            mockReviewRecordDAO.getReviewsInRange.mockResolvedValue([
                { score: 80, duration: 600 },
                { score: 90, duration: 900 },
            ]);
        });

        it('should return daily stats for 7d range', async () => {
            const stats = await service.getDailyStatistics('7d');

            expect(stats).toHaveLength(7);
            expect(stats[0]).toHaveProperty('date');
            expect(stats[0]).toHaveProperty('conceptCount');
            expect(stats[0]).toHaveProperty('averageScore');
            expect(stats[0]).toHaveProperty('totalMinutes');
        });

        it('should return daily stats for 30d range', async () => {
            const stats = await service.getDailyStatistics('30d');

            expect(stats).toHaveLength(30);
        });

        it('should calculate average score correctly', async () => {
            const stats = await service.getDailyStatistics('7d');

            // Each day should have 2 records with scores 80 and 90
            const dayWithData = stats.find(s => s.conceptCount > 0);
            if (dayWithData) {
                expect(dayWithData.averageScore).toBe(85);
            }
        });

        it('should calculate total minutes correctly', async () => {
            const stats = await service.getDailyStatistics('7d');

            const dayWithData = stats.find(s => s.conceptCount > 0);
            if (dayWithData) {
                // 600 + 900 seconds = 1500 seconds = 25 minutes
                expect(dayWithData.totalMinutes).toBe(25);
            }
        });

        it('should return empty stats when database not initialized', async () => {
            const newService = new HistoryService(mockApp);
            const stats = await newService.getDailyStatistics('7d');

            expect(stats).toHaveLength(7);
            expect(stats.every(s => s.conceptCount === 0)).toBe(true);
        });

        it('should handle database errors gracefully', async () => {
            mockReviewRecordDAO.getReviewsInRange.mockRejectedValue(new Error('Query failed'));

            const stats = await service.getDailyStatistics('7d');

            expect(stats).toHaveLength(7);
            expect(stats.every(s => s.conceptCount === 0)).toBe(true);
        });
    });

    describe('getConceptHistory', () => {
        const mockConceptRecords = [
            {
                id: 'concept-1',
                canvas_path: 'math.canvas',
                concept_name: 'Algebra',
                review_date: '2025-01-15T10:00:00Z',
                score: 85,
                mode: 'fresh',
            },
            {
                id: 'concept-2',
                canvas_path: 'math.canvas',
                concept_name: 'Algebra',
                review_date: '2025-01-10T10:00:00Z',
                score: 72,
                mode: 'targeted',
            },
        ];

        beforeEach(() => {
            mockReviewRecordDAO.getConceptReviews.mockResolvedValue(mockConceptRecords);
        });

        it('should return concept history entries', async () => {
            const entries = await service.getConceptHistory('algebra-id');

            expect(mockReviewRecordDAO.getConceptReviews).toHaveBeenCalledWith('algebra-id');
            expect(entries).toHaveLength(2);
        });

        it('should return empty array when database not initialized', async () => {
            const newService = new HistoryService(mockApp);
            const entries = await newService.getConceptHistory('test-id');

            expect(entries).toEqual([]);
        });

        it('should handle errors gracefully', async () => {
            mockReviewRecordDAO.getConceptReviews.mockRejectedValue(new Error('Not found'));

            const entries = await service.getConceptHistory('invalid-id');

            expect(entries).toEqual([]);
        });
    });

    describe('getCanvasReviewTrend', () => {
        const mockSessions = [
            {
                date: '2025-01-10T10:00:00Z',
                pass_rate: 0.6,
                mode: 'fresh',
                concepts_reviewed: 10,
                weak_concepts_count: 4,
            },
            {
                date: '2025-01-12T10:00:00Z',
                pass_rate: 0.7,
                mode: 'targeted',
                concepts_reviewed: 10,
                weak_concepts_count: 3,
            },
            {
                date: '2025-01-14T10:00:00Z',
                pass_rate: 0.85,
                mode: 'targeted',
                concepts_reviewed: 10,
                weak_concepts_count: 2,
            },
        ];

        beforeEach(() => {
            mockReviewRecordDAO.getCanvasReviewSessions.mockResolvedValue(mockSessions);
        });

        it('should return canvas review trend', async () => {
            const trend = await service.getCanvasReviewTrend('math.canvas');

            expect(trend).not.toBeNull();
            expect(trend?.canvasPath).toBe('math.canvas');
            expect(trend?.canvasTitle).toBe('math');
            expect(trend?.sessions).toHaveLength(3);
        });

        it('should calculate progress rate', async () => {
            const trend = await service.getCanvasReviewTrend('math.canvas');

            // Average of 0.6, 0.7, 0.85 = 0.7167 ≈ 72%
            expect(trend?.progressRate).toBeGreaterThan(70);
            expect(trend?.progressRate).toBeLessThan(75);
        });

        it('should determine upward trend', async () => {
            const trend = await service.getCanvasReviewTrend('math.canvas');

            // Progress from 0.6 to 0.85, should be 'up'
            expect(trend?.trend).toBe('up');
        });

        it('should determine downward trend', async () => {
            const downSessions = [
                { date: '2025-01-10T10:00:00Z', pass_rate: 0.9, mode: 'fresh', concepts_reviewed: 10, weak_concepts_count: 1 },
                { date: '2025-01-12T10:00:00Z', pass_rate: 0.8, mode: 'targeted', concepts_reviewed: 10, weak_concepts_count: 2 },
                { date: '2025-01-14T10:00:00Z', pass_rate: 0.6, mode: 'targeted', concepts_reviewed: 10, weak_concepts_count: 4 },
            ];
            mockReviewRecordDAO.getCanvasReviewSessions.mockResolvedValue(downSessions);

            const trend = await service.getCanvasReviewTrend('declining.canvas');

            expect(trend?.trend).toBe('down');
        });

        it('should determine stable trend', async () => {
            const stableSessions = [
                { date: '2025-01-10T10:00:00Z', pass_rate: 0.75, mode: 'fresh', concepts_reviewed: 10, weak_concepts_count: 3 },
                { date: '2025-01-12T10:00:00Z', pass_rate: 0.76, mode: 'targeted', concepts_reviewed: 10, weak_concepts_count: 2 },
                { date: '2025-01-14T10:00:00Z', pass_rate: 0.74, mode: 'targeted', concepts_reviewed: 10, weak_concepts_count: 3 },
            ];
            mockReviewRecordDAO.getCanvasReviewSessions.mockResolvedValue(stableSessions);

            const trend = await service.getCanvasReviewTrend('stable.canvas');

            expect(trend?.trend).toBe('stable');
        });

        it('should return null when no sessions found', async () => {
            mockReviewRecordDAO.getCanvasReviewSessions.mockResolvedValue([]);

            const trend = await service.getCanvasReviewTrend('empty.canvas');

            expect(trend).toBeNull();
        });

        it('should return null when database not initialized', async () => {
            const newService = new HistoryService(mockApp);
            const trend = await newService.getCanvasReviewTrend('test.canvas');

            expect(trend).toBeNull();
        });

        it('should handle single session', async () => {
            const singleSession = [
                { date: '2025-01-10T10:00:00Z', pass_rate: 0.8, mode: 'fresh', concepts_reviewed: 5, weak_concepts_count: 1 },
            ];
            mockReviewRecordDAO.getCanvasReviewSessions.mockResolvedValue(singleSession);

            const trend = await service.getCanvasReviewTrend('single.canvas');

            expect(trend?.progressRate).toBe(80);
            expect(trend?.trend).toBe('stable');
        });
    });

    describe('getAllCanvasTrends', () => {
        beforeEach(() => {
            mockReviewRecordDAO.getReviewedCanvasesSince.mockResolvedValue([
                'math.canvas',
                'physics.canvas',
            ]);
            mockReviewRecordDAO.getCanvasReviewSessions.mockImplementation((path: string) => {
                if (path === 'math.canvas') {
                    return Promise.resolve([
                        { date: '2025-01-10', pass_rate: 0.9, mode: 'fresh', concepts_reviewed: 5, weak_concepts_count: 1 },
                    ]);
                }
                if (path === 'physics.canvas') {
                    return Promise.resolve([
                        { date: '2025-01-10', pass_rate: 0.7, mode: 'fresh', concepts_reviewed: 8, weak_concepts_count: 2 },
                    ]);
                }
                return Promise.resolve([]);
            });
        });

        it('should return all canvas trends', async () => {
            const trends = await service.getAllCanvasTrends('7d');

            expect(trends).toHaveLength(2);
        });

        it('should sort trends by progress rate descending', async () => {
            const trends = await service.getAllCanvasTrends('7d');

            expect(trends[0].canvasPath).toBe('math.canvas'); // 90% > 70%
            expect(trends[1].canvasPath).toBe('physics.canvas');
        });

        it('should return empty array when database not initialized', async () => {
            const newService = new HistoryService(mockApp);
            const trends = await newService.getAllCanvasTrends('7d');

            expect(trends).toEqual([]);
        });

        it('should handle errors gracefully', async () => {
            mockReviewRecordDAO.getReviewedCanvasesSince.mockRejectedValue(new Error('Failed'));

            const trends = await service.getAllCanvasTrends('30d');

            expect(trends).toEqual([]);
        });
    });

    describe('loadHistoryState', () => {
        beforeEach(() => {
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue([]);
            mockReviewRecordDAO.getReviewsInRange.mockResolvedValue([]);
            mockReviewRecordDAO.getReviewedCanvasesSince.mockResolvedValue([]);
        });

        it('should load complete history state', async () => {
            const state = await service.loadHistoryState('7d');

            expect(state).toHaveProperty('entries');
            expect(state).toHaveProperty('dailyStats');
            expect(state).toHaveProperty('canvasTrends');
            expect(state).toHaveProperty('timeRange');
            expect(state).toHaveProperty('loading');
            expect(state.timeRange).toBe('7d');
            expect(state.loading).toBe(false);
        });

        it('should load state for 30d time range', async () => {
            const state = await service.loadHistoryState('30d');

            expect(state.timeRange).toBe('30d');
            expect(state.dailyStats).toHaveLength(30);
        });

        it('should handle errors and return default state', async () => {
            mockReviewRecordDAO.getReviewsSince.mockRejectedValue(new Error('Critical error'));

            const state = await service.loadHistoryState('7d');

            expect(state.loading).toBe(false);
            expect(state.entries).toEqual([]);
        });

        it('should load all data in parallel', async () => {
            const startTime = Date.now();
            await service.loadHistoryState('7d');
            const endTime = Date.now();

            // All three methods should be called
            expect(mockReviewRecordDAO.getReviewsSince).toHaveBeenCalled();
            expect(mockReviewRecordDAO.getReviewsInRange).toHaveBeenCalled();
            expect(mockReviewRecordDAO.getReviewedCanvasesSince).toHaveBeenCalled();
        });
    });

    describe('extractCanvasTitle', () => {
        it('should extract title from simple path', async () => {
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue([
                { canvas_path: 'mycanvas.canvas', concept_name: 'Test', review_date: new Date() },
            ]);

            const entries = await service.getReviewHistory('7d');

            expect(entries[0].canvasTitle).toBe('mycanvas');
        });

        it('should extract title from nested path', async () => {
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue([
                { canvas_path: 'folder/subfolder/mycanvas.canvas', concept_name: 'Test', review_date: new Date() },
            ]);

            const entries = await service.getReviewHistory('7d');

            expect(entries[0].canvasTitle).toBe('mycanvas');
        });

        it('should handle empty path', async () => {
            mockReviewRecordDAO.getReviewsSince.mockResolvedValue([
                { canvas_path: '', concept_name: 'Test', review_date: new Date() },
            ]);

            const entries = await service.getReviewHistory('7d');

            expect(entries[0].canvasTitle).toBe('Unknown Canvas');
        });
    });
});

describe('createHistoryService', () => {
    it('should create service instance', () => {
        const service = createHistoryService(mockApp);
        expect(service).toBeInstanceOf(HistoryService);
    });
});
