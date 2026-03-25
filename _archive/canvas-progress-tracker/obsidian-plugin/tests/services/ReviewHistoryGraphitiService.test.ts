/**
 * ReviewHistoryGraphitiService Tests - Canvas Learning System
 *
 * Tests for Story 14.13: 检验历史记录存储到Graphiti
 *
 * @module ReviewHistoryGraphitiService.test
 * @version 1.0.0
 */

import {
    ReviewHistoryGraphitiService,
    DEFAULT_GRAPHITI_SETTINGS,
    createReviewHistoryGraphitiService,
    ReviewMode,
    ReviewResults,
    ConceptResult,
    WeakConcept,
} from '../../src/services/ReviewHistoryGraphitiService';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// Mock App
const mockApp = {} as any;

// Test helpers
function createMockReviewResults(overrides: Partial<ReviewResults> = {}): ReviewResults {
    return {
        totalConcepts: 10,
        correctCount: 7,
        averageScore: 75,
        conceptResults: [
            createMockConceptResult({ conceptName: 'Concept A' }),
            createMockConceptResult({ conceptName: 'Concept B', wasCorrect: false, score: 40 }),
        ],
        reviewDate: new Date('2025-01-15'),
        durationMs: 300000, // 5 minutes
        ...overrides,
    };
}

function createMockConceptResult(overrides: Partial<ConceptResult> = {}): ConceptResult {
    return {
        conceptId: 'concept-1',
        conceptName: 'Test Concept',
        score: 85,
        wasCorrect: true,
        attemptCount: 1,
        timeSpent: 30000, // 30 seconds
        previouslyWeak: false,
        ...overrides,
    };
}

describe('ReviewHistoryGraphitiService', () => {
    let service: ReviewHistoryGraphitiService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new ReviewHistoryGraphitiService(mockApp);
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.apiBaseUrl).toBe('http://localhost:8000/api/v1');
            expect(settings.timeout).toBe(10000);
            expect(settings.enableCaching).toBe(true);
            expect(settings.autoSync).toBe(true);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new ReviewHistoryGraphitiService(mockApp, {
                apiBaseUrl: 'http://custom:9000/api',
                timeout: 5000,
            });

            const settings = customService.getSettings();
            expect(settings.apiBaseUrl).toBe('http://custom:9000/api');
            expect(settings.timeout).toBe(5000);
            expect(settings.enableCaching).toBe(true); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ timeout: 20000 });
            const settings = service.getSettings();
            expect(settings.timeout).toBe(20000);
            expect(settings.apiBaseUrl).toBe('http://localhost:8000/api/v1'); // Unchanged
        });
    });

    describe('Store Review Canvas Relationship', () => {
        const reviewPath = 'reviews/test-review.canvas';
        const originalPath = 'canvases/test-original.canvas';
        const mode: ReviewMode = 'fresh';

        it('should store relationship successfully', async () => {
            mockRequestUrl.mockResolvedValue({ status: 201, json: {} });

            const results = createMockReviewResults();
            const success = await service.storeReviewCanvasRelationship(
                reviewPath,
                originalPath,
                mode,
                results
            );

            expect(success).toBe(true);
            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/memory/graphiti/store'),
                    method: 'POST',
                })
            );
        });

        it('should include correct Cypher data in request', async () => {
            mockRequestUrl.mockResolvedValue({ status: 201, json: {} });

            const results = createMockReviewResults();
            await service.storeReviewCanvasRelationship(
                reviewPath,
                originalPath,
                'targeted',
                results
            );

            const call = mockRequestUrl.mock.calls[0][0];
            const body = JSON.parse(call.body);
            expect(body.operation).toBe('create_review_relationship');
            expect(body.data.params.mode).toBe('targeted');
            expect(body.data.params.original_path).toBe(originalPath);
            expect(body.data.params.review_path).toBe(reviewPath);
        });

        it('should add to pending writes on failure', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const results = createMockReviewResults();
            const success = await service.storeReviewCanvasRelationship(
                reviewPath,
                originalPath,
                mode,
                results
            );

            expect(success).toBe(false);
            expect(service.getPendingWriteCount()).toBe(1);
        });

        it('should add to pending writes on non-success status', async () => {
            mockRequestUrl.mockResolvedValue({ status: 500, json: {} });

            const results = createMockReviewResults();
            const success = await service.storeReviewCanvasRelationship(
                reviewPath,
                originalPath,
                mode,
                results
            );

            expect(success).toBe(false);
            expect(service.getPendingWriteCount()).toBe(1);
        });
    });

    describe('Query Review History', () => {
        const canvasPath = 'canvases/test.canvas';

        it('should query review history successfully', async () => {
            const mockRelationships = [
                {
                    id: 'rel-1',
                    sourceId: 'review-1',
                    targetId: 'original-1',
                    mode: 'fresh',
                    totalConcepts: 10,
                    correctCount: 8,
                    averageScore: 80,
                    durationMs: 300000,
                    reviewDate: '2025-01-15T00:00:00.000Z',
                    createdAt: '2025-01-15T00:00:00.000Z',
                },
            ];

            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { relationships: mockRelationships },
            });

            const history = await service.queryReviewHistory(canvasPath);

            expect(history).toHaveLength(1);
            expect(history[0].mode).toBe('fresh');
            expect(history[0].results.averageScore).toBe(80);
        });

        it('should return empty array on error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const history = await service.queryReviewHistory(canvasPath);

            expect(history).toHaveLength(0);
        });

        it('should use cache for repeated queries', async () => {
            const mockRelationships = [
                {
                    id: 'rel-1',
                    sourceId: 'review-1',
                    targetId: 'original-1',
                    mode: 'fresh',
                    totalConcepts: 10,
                    correctCount: 8,
                    averageScore: 80,
                    durationMs: 300000,
                    reviewDate: '2025-01-15T00:00:00.000Z',
                    createdAt: '2025-01-15T00:00:00.000Z',
                },
            ];

            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { relationships: mockRelationships },
            });

            await service.queryReviewHistory(canvasPath);
            await service.queryReviewHistory(canvasPath);

            // Should only call API once due to caching
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
        });

        it('should respect limit parameter', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { relationships: [] },
            });

            await service.queryReviewHistory(canvasPath, 5);

            const call = mockRequestUrl.mock.calls[0][0];
            const body = JSON.parse(call.body);
            expect(body.limit).toBe(5);
        });
    });

    describe('Query Weak Concepts', () => {
        const canvasPath = 'canvases/test.canvas';

        it('should query weak concepts successfully', async () => {
            const mockWeakConcepts: WeakConcept[] = [
                {
                    conceptId: 'concept-1',
                    conceptName: 'Hard Concept',
                    failureCount: 5,
                    lastFailureDate: new Date('2025-01-10'),
                    averageScore: 45,
                    trend: 'declining',
                },
            ];

            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { weakConcepts: mockWeakConcepts.map(c => ({
                    ...c,
                    lastFailureDate: c.lastFailureDate.toISOString(),
                })) },
            });

            const weakConcepts = await service.queryWeakConcepts(canvasPath);

            expect(weakConcepts).toHaveLength(1);
            expect(weakConcepts[0].conceptName).toBe('Hard Concept');
            expect(weakConcepts[0].trend).toBe('declining');
        });

        it('should return empty array on error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const weakConcepts = await service.queryWeakConcepts(canvasPath);

            expect(weakConcepts).toHaveLength(0);
        });

        it('should use lookback days parameter', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { weakConcepts: [] },
            });

            await service.queryWeakConcepts(canvasPath, 60);

            const call = mockRequestUrl.mock.calls[0][0];
            const body = JSON.parse(call.body);
            expect(body.lookbackDays).toBe(60);
        });
    });

    describe('Query Mastered Concepts', () => {
        const canvasPath = 'canvases/test.canvas';

        it('should query mastered concepts successfully', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { masteredConcepts: ['Concept A', 'Concept B'] },
            });

            const mastered = await service.queryMasteredConcepts(canvasPath);

            expect(mastered).toHaveLength(2);
            expect(mastered).toContain('Concept A');
        });

        it('should return empty array on error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const mastered = await service.queryMasteredConcepts(canvasPath);

            expect(mastered).toHaveLength(0);
        });
    });

    describe('Store Concept Result', () => {
        const canvasPath = 'canvases/test.canvas';

        it('should store concept result successfully', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });

            const result = createMockConceptResult();
            const success = await service.storeConceptResult(canvasPath, result);

            expect(success).toBe(true);
            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/memory/graphiti/store'),
                    method: 'POST',
                })
            );
        });

        it('should return false on failure', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const result = createMockConceptResult();
            const success = await service.storeConceptResult(canvasPath, result);

            expect(success).toBe(false);
        });
    });

    describe('Get Canvas Statistics', () => {
        const canvasPath = 'canvases/test.canvas';

        it('should get canvas statistics successfully', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: {
                    totalReviews: 10,
                    averageScore: 75,
                    lastReviewDate: '2025-01-15T00:00:00.000Z',
                    improvementTrend: 5,
                    weakConceptCount: 3,
                    masteredConceptCount: 7,
                },
            });

            const stats = await service.getCanvasStatistics(canvasPath);

            expect(stats.totalReviews).toBe(10);
            expect(stats.averageScore).toBe(75);
            expect(stats.lastReviewDate).toBeInstanceOf(Date);
            expect(stats.improvementTrend).toBe(5);
        });

        it('should return default stats on error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const stats = await service.getCanvasStatistics(canvasPath);

            expect(stats.totalReviews).toBe(0);
            expect(stats.averageScore).toBe(0);
            expect(stats.lastReviewDate).toBeNull();
        });
    });

    describe('Delete Review Relationship', () => {
        it('should delete relationship successfully', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });

            const success = await service.deleteReviewRelationship('reviews/test.canvas');

            expect(success).toBe(true);
            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'DELETE',
                })
            );
        });

        it('should return false on failure', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const success = await service.deleteReviewRelationship('reviews/test.canvas');

            expect(success).toBe(false);
        });
    });

    describe('Auto Sync', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
            service.stopAutoSync();
        });

        it('should start auto sync', () => {
            service.startAutoSync();
            // Should not throw
        });

        it('should not start when disabled', () => {
            service.updateSettings({ autoSync: false });
            service.startAutoSync();
            // Should not throw
        });

        it('should stop auto sync', () => {
            service.startAutoSync();
            service.stopAutoSync();
            // Should not throw
        });
    });

    describe('Sync Pending Writes', () => {
        it('should return 0 when no pending writes', async () => {
            const count = await service.syncPendingWrites();
            expect(count).toBe(0);
        });

        it('should sync pending writes successfully', async () => {
            // First, cause a failure to add to pending
            mockRequestUrl.mockRejectedValueOnce(new Error('Network error'));

            const results = createMockReviewResults();
            await service.storeReviewCanvasRelationship(
                'reviews/test.canvas',
                'canvases/test.canvas',
                'fresh',
                results
            );

            expect(service.getPendingWriteCount()).toBe(1);

            // Now sync successfully
            mockRequestUrl.mockResolvedValue({ status: 201, json: {} });
            const synced = await service.syncPendingWrites();

            expect(synced).toBe(1);
            expect(service.getPendingWriteCount()).toBe(0);
        });

        it('should keep failed writes in pending', async () => {
            // Add to pending
            mockRequestUrl.mockRejectedValueOnce(new Error('Network error'));

            const results = createMockReviewResults();
            await service.storeReviewCanvasRelationship(
                'reviews/test.canvas',
                'canvases/test.canvas',
                'fresh',
                results
            );

            // Sync fails again
            mockRequestUrl.mockRejectedValue(new Error('Network error'));
            const synced = await service.syncPendingWrites();

            expect(synced).toBe(0);
            expect(service.getPendingWriteCount()).toBe(1);
        });
    });

    describe('Cache Management', () => {
        it('should clear cache', () => {
            service.clearCache();
            const stats = service.getCacheStats();
            expect(stats.size).toBe(0);
        });

        it('should clear pending writes', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const results = createMockReviewResults();
            await service.storeReviewCanvasRelationship(
                'reviews/test.canvas',
                'canvases/test.canvas',
                'fresh',
                results
            );

            expect(service.getPendingWriteCount()).toBe(1);

            service.clearPendingWrites();
            expect(service.getPendingWriteCount()).toBe(0);
        });

        it('should report cache statistics', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { relationships: [] },
            });

            await service.queryReviewHistory('canvases/test.canvas');

            const stats = service.getCacheStats();
            expect(stats.size).toBe(1);
            expect(stats.oldestEntry).not.toBeNull();
        });
    });

    describe('Health Check', () => {
        it('should return true when healthy', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });

            const healthy = await service.checkHealth();

            expect(healthy).toBe(true);
        });

        it('should return false when unhealthy', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Connection refused'));

            const healthy = await service.checkHealth();

            expect(healthy).toBe(false);
        });
    });

    describe('State Export/Import', () => {
        it('should export state', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const results = createMockReviewResults();
            await service.storeReviewCanvasRelationship(
                'reviews/test.canvas',
                'canvases/test.canvas',
                'fresh',
                results
            );

            const state = service.exportState();

            expect(state).toHaveProperty('pendingWrites');
            expect(state).toHaveProperty('cacheStats');
        });

        it('should import state', () => {
            const state = {
                pendingWrites: [
                    {
                        reviewCanvasPath: 'reviews/test.canvas',
                        originalCanvasPath: 'canvases/test.canvas',
                        mode: 'fresh',
                        results: {
                            totalConcepts: 10,
                            correctCount: 7,
                            averageScore: 70,
                            conceptResults: [],
                            reviewDate: '2025-01-15T00:00:00.000Z',
                            durationMs: 300000,
                        },
                        createdAt: '2025-01-15T00:00:00.000Z',
                    },
                ],
            };

            service.importState(state);

            expect(service.getPendingWriteCount()).toBe(1);
        });
    });
});

describe('DEFAULT_GRAPHITI_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_GRAPHITI_SETTINGS.apiBaseUrl).toBe('http://localhost:8000/api/v1');
        expect(DEFAULT_GRAPHITI_SETTINGS.timeout).toBe(10000);
        expect(DEFAULT_GRAPHITI_SETTINGS.enableCaching).toBe(true);
        expect(DEFAULT_GRAPHITI_SETTINGS.cacheExpiry).toBe(5 * 60 * 1000);
        expect(DEFAULT_GRAPHITI_SETTINGS.autoSync).toBe(true);
        expect(DEFAULT_GRAPHITI_SETTINGS.syncIntervalMinutes).toBe(15);
    });
});

describe('createReviewHistoryGraphitiService', () => {
    it('should create service instance', () => {
        const service = createReviewHistoryGraphitiService(mockApp);
        expect(service).toBeInstanceOf(ReviewHistoryGraphitiService);
    });

    it('should create service with custom settings', () => {
        const service = createReviewHistoryGraphitiService(mockApp, {
            apiBaseUrl: 'http://custom:8080',
        });

        expect(service.getSettings().apiBaseUrl).toBe('http://custom:8080');
    });
});
