/**
 * FSRSOptimizerService Tests - Canvas Learning System
 *
 * Tests for Story 14.12: FSRS参数优化功能（FR3.6）
 *
 * @module FSRSOptimizerService.test
 * @version 1.0.0
 */

import {
    FSRSOptimizerService,
    FSRSOptimizerSettings,
    ABTestConfig,
    DEFAULT_OPTIMIZER_SETTINGS,
    DEFAULT_AB_TEST_CONFIG,
    DEFAULT_FSRS_PARAMETERS,
    createFSRSOptimizerService,
    ReviewRecord,
    TrainingDataPoint,
    OptimizationResult,
} from '../../src/services/FSRSOptimizerService';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// Mock App
const mockApp = {} as any;

// ============================================================================
// Test Helpers
// ============================================================================

function createReviewRecord(overrides: Partial<ReviewRecord> = {}): ReviewRecord {
    const now = new Date();
    return {
        conceptId: 'test-concept-1',
        conceptName: 'Test Concept',
        reviewTime: now,
        rating: 3 as const,
        interval: 1,
        stability: 5,
        difficulty: 5,
        retention: 0.9,
        success: true,
        ...overrides,
    };
}

function generateReviewHistory(count: number): ReviewRecord[] {
    const records: ReviewRecord[] = [];
    const conceptNames = ['Concept A', 'Concept B', 'Concept C', 'Concept D', 'Concept E'];
    const ratings: (1 | 2 | 3 | 4)[] = [1, 2, 3, 4];

    for (let i = 0; i < count; i++) {
        const daysAgo = Math.floor(Math.random() * 60);
        const reviewTime = new Date();
        reviewTime.setDate(reviewTime.getDate() - daysAgo);

        records.push({
            conceptId: `concept-${i % 5}`,
            conceptName: conceptNames[i % 5],
            reviewTime,
            rating: ratings[Math.floor(Math.random() * 4)],
            interval: Math.floor(Math.random() * 30) + 1,
            stability: Math.random() * 10 + 1,
            difficulty: Math.random() * 9 + 1,
            retention: Math.random() * 0.4 + 0.5, // 0.5-0.9
            success: Math.random() > 0.2, // 80% success rate
        });
    }

    return records;
}

function createMockDataManager(reviewCount: number) {
    return {
        getReviewRecordDAO: jest.fn().mockReturnValue({
            getAllReviewRecords: jest.fn().mockResolvedValue(generateReviewHistory(reviewCount)),
        }),
    };
}

// ============================================================================
// Tests
// ============================================================================

describe('FSRSOptimizerService', () => {
    let service: FSRSOptimizerService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new FSRSOptimizerService(mockApp);
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.apiBaseUrl).toBe('http://localhost:8000/api/v1');
            expect(settings.timeout).toBe(30000);
            expect(settings.minSamples).toBe(100);
            expect(settings.maxIterations).toBe(100);
            expect(settings.learningRate).toBe(0.01);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new FSRSOptimizerService(mockApp, {
                apiBaseUrl: 'http://custom:9000/api',
                minSamples: 50,
            });

            const settings = customService.getSettings();
            expect(settings.apiBaseUrl).toBe('http://custom:9000/api');
            expect(settings.minSamples).toBe(50);
            expect(settings.maxIterations).toBe(100); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ maxIterations: 200 });
            const settings = service.getSettings();
            expect(settings.maxIterations).toBe(200);
            expect(settings.minSamples).toBe(100); // Unchanged
        });
    });

    describe('Default FSRS Parameters', () => {
        it('should have 17 default parameters', () => {
            expect(DEFAULT_FSRS_PARAMETERS).toHaveLength(17);
        });

        it('should have reasonable initial stability values', () => {
            // w[0-3] are initial stability for Again, Hard, Good, Easy
            expect(DEFAULT_FSRS_PARAMETERS[0]).toBeLessThan(DEFAULT_FSRS_PARAMETERS[1]);
            expect(DEFAULT_FSRS_PARAMETERS[1]).toBeLessThan(DEFAULT_FSRS_PARAMETERS[2]);
            expect(DEFAULT_FSRS_PARAMETERS[2]).toBeLessThan(DEFAULT_FSRS_PARAMETERS[3]);
        });

        it('should have all positive values', () => {
            for (const param of DEFAULT_FSRS_PARAMETERS) {
                expect(param).toBeGreaterThan(0);
            }
        });
    });

    describe('Parameter Management', () => {
        it('should return current parameters', () => {
            const params = service.getCurrentParameters();
            expect(params).toEqual(DEFAULT_FSRS_PARAMETERS);
        });

        it('should return null for optimized parameters before optimization', () => {
            expect(service.getOptimizedParameters()).toBeNull();
        });

        it('should indicate not using optimized parameters initially', () => {
            expect(service.isUsingOptimizedParameters()).toBe(false);
        });

        it('should reset to default parameters', () => {
            // Manually set some parameters first
            (service as any).currentParameters = [1, 2, 3];
            (service as any).optimizedParameters = [4, 5, 6];

            service.resetToDefaultParameters();

            expect(service.getCurrentParameters()).toEqual(DEFAULT_FSRS_PARAMETERS);
            expect(service.getOptimizedParameters()).toBeNull();
        });
    });

    describe('A/B Test Configuration', () => {
        it('should have default A/B test config', () => {
            const config = service.getABTestConfig();
            expect(config.enabled).toBe(false);
            expect(config.testGroupRatio).toBe(0.5);
            expect(config.trackingPeriodDays).toBe(30);
            expect(config.minimumSamplesPerGroup).toBe(50);
        });

        it('should update A/B test config', () => {
            service.updateABTestConfig({ enabled: true, testGroupRatio: 0.3 });
            const config = service.getABTestConfig();
            expect(config.enabled).toBe(true);
            expect(config.testGroupRatio).toBe(0.3);
        });

        it('should create with custom A/B config', () => {
            const customService = new FSRSOptimizerService(mockApp, {}, {
                enabled: true,
                testGroupRatio: 0.7,
            });

            const config = customService.getABTestConfig();
            expect(config.enabled).toBe(true);
            expect(config.testGroupRatio).toBe(0.7);
        });
    });

    describe('Test Group Assignment', () => {
        it('should assign to control when A/B testing disabled', () => {
            service.updateABTestConfig({ enabled: false });
            expect(service.getTestGroupAssignment('concept-1')).toBe('control');
            expect(service.getTestGroupAssignment('concept-2')).toBe('control');
        });

        it('should assign deterministically based on concept ID', () => {
            service.updateABTestConfig({ enabled: true, testGroupRatio: 0.5 });

            const assignment1 = service.getTestGroupAssignment('concept-abc');
            const assignment2 = service.getTestGroupAssignment('concept-abc');
            const assignment3 = service.getTestGroupAssignment('concept-xyz');

            // Same concept should always get same assignment
            expect(assignment1).toBe(assignment2);
            // Different concepts may get different assignments
            expect(['control', 'test']).toContain(assignment3);
        });

        it('should respect test group ratio', () => {
            service.updateABTestConfig({ enabled: true, testGroupRatio: 0.5 });

            const assignments: string[] = [];
            for (let i = 0; i < 1000; i++) {
                assignments.push(service.getTestGroupAssignment(`concept-${i}`));
            }

            const testCount = assignments.filter(a => a === 'test').length;
            const ratio = testCount / 1000;

            // Should be roughly 50% with some tolerance
            expect(ratio).toBeGreaterThan(0.35);
            expect(ratio).toBeLessThan(0.65);
        });
    });

    describe('Optimization with Insufficient Data', () => {
        it('should return default params when samples insufficient', async () => {
            const mockDataManager = createMockDataManager(50); // Below minimum 100
            service.setDataManager(mockDataManager);

            const result = await service.optimizeParameters();

            expect(result.isOptimized).toBe(false);
            expect(result.parameters).toEqual(DEFAULT_FSRS_PARAMETERS);
            expect(result.metrics.sampleSize).toBe(50);
        });

        it('should return default params with no data manager and API failure', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const result = await service.optimizeParameters();

            expect(result.isOptimized).toBe(false);
            expect(result.parameters).toEqual(DEFAULT_FSRS_PARAMETERS);
        });
    });

    describe('Optimization with Sufficient Data', () => {
        beforeEach(() => {
            const mockDataManager = createMockDataManager(150);
            service.setDataManager(mockDataManager);

            // Mock API calls for concept network and document interactions
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/graphiti/query')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            distribution: {
                                'Concept A': { difficulty: 0.6, prerequisite_count: 2 },
                                'Concept B': { difficulty: 0.4, prerequisite_count: 1 },
                            },
                        },
                    });
                }
                if (options.url.includes('/semantic/query')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            correlations: {
                                'Concept A': { engagement: 0.8, document_count: 5 },
                                'Concept B': { engagement: 0.6, document_count: 3 },
                            },
                        },
                    });
                }
                return Promise.resolve({ status: 404, json: {} });
            });
        });

        it('should optimize parameters with sufficient data', async () => {
            const result = await service.optimizeParameters();

            expect(result.isOptimized).toBe(true);
            expect(result.parameters).toHaveLength(17);
            expect(result.metrics.sampleSize).toBe(150);
            expect(result.lastOptimizationTime).toBeInstanceOf(Date);
        });

        it('should calculate optimization metrics', async () => {
            const result = await service.optimizeParameters();

            expect(result.metrics.rmse).toBeGreaterThanOrEqual(0);
            expect(result.metrics.dataQualityScore).toBeGreaterThanOrEqual(0);
            expect(result.metrics.dataQualityScore).toBeLessThanOrEqual(1);
            expect(result.metrics.convergenceIterations).toBeGreaterThan(0);
        });

        it('should store optimized parameters', async () => {
            await service.optimizeParameters();

            const optimized = service.getOptimizedParameters();
            expect(optimized).not.toBeNull();
            expect(optimized).toHaveLength(17);
        });

        it('should store last optimization result', async () => {
            await service.optimizeParameters();

            const lastResult = service.getLastOptimizationResult();
            expect(lastResult).not.toBeNull();
            expect(lastResult?.isOptimized).toBe(true);
        });
    });

    describe('Apply Optimized Parameters', () => {
        beforeEach(async () => {
            const mockDataManager = createMockDataManager(150);
            service.setDataManager(mockDataManager);
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });
        });

        it('should return false when no optimized parameters', () => {
            expect(service.applyOptimizedParameters()).toBe(false);
        });

        it('should apply optimized parameters after optimization', async () => {
            await service.optimizeParameters();

            const applied = service.applyOptimizedParameters();

            expect(applied).toBe(true);
            expect(service.isUsingOptimizedParameters()).toBe(true);
        });
    });

    describe('Auto-Optimization Trigger', () => {
        beforeEach(() => {
            service.updateSettings({ autoOptimizeInterval: 5 }); // Low threshold for testing
            const mockDataManager = createMockDataManager(150);
            service.setDataManager(mockDataManager);
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });
        });

        it('should not trigger optimization below threshold', async () => {
            for (let i = 0; i < 4; i++) {
                const triggered = await service.recordReview(createReviewRecord());
                expect(triggered).toBe(false);
            }
        });

        it('should trigger optimization at threshold', async () => {
            for (let i = 0; i < 4; i++) {
                await service.recordReview(createReviewRecord());
            }

            const triggered = await service.recordReview(createReviewRecord());
            expect(triggered).toBe(true);
        });

        it('should reset counter after optimization', async () => {
            // Trigger first optimization
            for (let i = 0; i < 5; i++) {
                await service.recordReview(createReviewRecord());
            }

            // Next 4 reviews should not trigger
            for (let i = 0; i < 4; i++) {
                const triggered = await service.recordReview(createReviewRecord());
                expect(triggered).toBe(false);
            }
        });
    });

    describe('Scheduled Optimization', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
            service.stopScheduledOptimization();
        });

        it('should start scheduled optimization', () => {
            service.updateSettings({ monthlyOptimizationEnabled: true });
            service.startScheduledOptimization();

            // Should not throw
            expect(true).toBe(true);
        });

        it('should stop scheduled optimization', () => {
            service.updateSettings({ monthlyOptimizationEnabled: true });
            service.startScheduledOptimization();
            service.stopScheduledOptimization();

            // Should not throw
            expect(true).toBe(true);
        });

        it('should not start when disabled', () => {
            service.updateSettings({ monthlyOptimizationEnabled: false });
            service.startScheduledOptimization();

            // Check that no timer was set by verifying the internal state
            expect((service as any).scheduledOptimizationTimer).toBeNull();
        });
    });

    describe('A/B Test Results', () => {
        beforeEach(() => {
            service.updateABTestConfig({
                enabled: true,
                testGroupRatio: 0.5,
                minimumSamplesPerGroup: 10,
            });
        });

        it('should record A/B test reviews', () => {
            const review = createReviewRecord({ conceptId: 'concept-1' });
            service.recordABTestReview('concept-1', review);

            const results = service.analyzeABTestResults();
            expect(results.controlGroup.sampleSize + results.testGroup.sampleSize).toBe(1);
        });

        it('should analyze A/B test results', () => {
            // Add reviews to different concepts
            for (let i = 0; i < 100; i++) {
                const conceptId = `concept-${i}`;
                const review = createReviewRecord({
                    conceptId,
                    retention: Math.random() * 0.4 + 0.5,
                    success: Math.random() > 0.2,
                });
                service.recordABTestReview(conceptId, review);
            }

            const results = service.analyzeABTestResults();

            expect(results.controlGroup.sampleSize).toBeGreaterThan(0);
            expect(results.testGroup.sampleSize).toBeGreaterThan(0);
            expect(results.controlGroup.avgRetention).toBeGreaterThan(0);
            expect(results.testGroup.avgRetention).toBeGreaterThan(0);
            expect(['control', 'test', 'inconclusive']).toContain(results.winner);
        });

        it('should return inconclusive with insufficient samples', () => {
            service.updateABTestConfig({ minimumSamplesPerGroup: 1000 });

            for (let i = 0; i < 10; i++) {
                const review = createReviewRecord({ conceptId: `concept-${i}` });
                service.recordABTestReview(`concept-${i}`, review);
            }

            const results = service.analyzeABTestResults();
            expect(results.winner).toBe('inconclusive');
        });

        it('should clear A/B test data', () => {
            for (let i = 0; i < 10; i++) {
                service.recordABTestReview(`concept-${i}`, createReviewRecord());
            }

            service.clearABTestData();

            const results = service.analyzeABTestResults();
            expect(results.controlGroup.sampleSize).toBe(0);
            expect(results.testGroup.sampleSize).toBe(0);
        });
    });

    describe('Parameters for Concept', () => {
        beforeEach(async () => {
            const mockDataManager = createMockDataManager(150);
            service.setDataManager(mockDataManager);
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });
            await service.optimizeParameters();
        });

        it('should return default params when A/B testing disabled', () => {
            service.updateABTestConfig({ enabled: false });

            const params = service.getParametersForConcept('concept-1');
            expect(params).toEqual(service.getCurrentParameters());
        });

        it('should return appropriate params based on group when A/B enabled', () => {
            service.updateABTestConfig({ enabled: true });
            service.applyOptimizedParameters();

            const params = service.getParametersForConcept('concept-1');
            expect(params).toHaveLength(17);
        });
    });

    describe('State Export/Import', () => {
        beforeEach(async () => {
            const mockDataManager = createMockDataManager(150);
            service.setDataManager(mockDataManager);
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });
        });

        it('should export state', async () => {
            await service.optimizeParameters();

            const state = service.exportState();

            expect(state.currentParameters).toEqual(DEFAULT_FSRS_PARAMETERS);
            expect(state.optimizedParameters).not.toBeNull();
            expect(state.lastOptimization).not.toBeNull();
            expect(state.reviewsSinceOptimization).toBe(0);
        });

        it('should import state', () => {
            const customParams = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17];

            service.importState({
                currentParameters: customParams,
                reviewsSinceOptimization: 25,
            });

            expect(service.getCurrentParameters()).toEqual(customParams);
            expect((service as any).reviewsSinceOptimization).toBe(25);
        });

        it('should handle partial state import', () => {
            const originalParams = service.getCurrentParameters();

            service.importState({
                reviewsSinceOptimization: 42,
            });

            expect(service.getCurrentParameters()).toEqual(originalParams);
            expect((service as any).reviewsSinceOptimization).toBe(42);
        });
    });

    describe('Data Quality Calculation', () => {
        it('should return 0 for empty data', () => {
            const quality = (service as any).calculateDataQuality([]);
            expect(quality).toBe(0);
        });

        it('should calculate quality score for diverse data', () => {
            const trainingData: TrainingDataPoint[] = [];
            const ratings: (1 | 2 | 3 | 4)[] = [1, 2, 3, 4];

            for (let i = 0; i < 200; i++) {
                trainingData.push({
                    deltaT: (i % 30) + 1,
                    rating: ratings[i % 4],
                    retention: 0.5 + Math.random() * 0.4,
                    conceptDifficulty: Math.random(),
                    docEngagement: Math.random(),
                    prerequisiteReadiness: Math.random(),
                });
            }

            const quality = (service as any).calculateDataQuality(trainingData);

            expect(quality).toBeGreaterThan(0);
            expect(quality).toBeLessThanOrEqual(1);
        });

        it('should give higher score for larger sample sizes', () => {
            const smallData: TrainingDataPoint[] = Array(50).fill(null).map((_, i) => ({
                deltaT: 1,
                rating: 3 as const,
                retention: 0.8,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.5,
            }));

            const largeData: TrainingDataPoint[] = Array(500).fill(null).map((_, i) => ({
                deltaT: 1,
                rating: 3 as const,
                retention: 0.8,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.5,
            }));

            const smallQuality = (service as any).calculateDataQuality(smallData);
            const largeQuality = (service as any).calculateDataQuality(largeData);

            expect(largeQuality).toBeGreaterThan(smallQuality);
        });
    });

    describe('Gradient Descent Optimization', () => {
        it('should run gradient descent optimization', () => {
            const trainingData: TrainingDataPoint[] = Array(100).fill(null).map((_, i) => ({
                deltaT: (i % 10) + 1,
                rating: ((i % 4) + 1) as 1 | 2 | 3 | 4,
                retention: 0.5 + Math.random() * 0.4,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            }));

            const result = (service as any).runGradientDescentOptimization(trainingData);

            expect(result.parameters).toHaveLength(17);
            expect(result.iterations).toBeGreaterThan(0);
            expect(result.iterations).toBeLessThanOrEqual(100);
        });

        it('should clamp parameters to reasonable bounds', () => {
            const trainingData: TrainingDataPoint[] = Array(100).fill(null).map(() => ({
                deltaT: 1,
                rating: 4 as const,
                retention: 0.99, // Very high retention
                conceptDifficulty: 0.1,
                docEngagement: 0.9,
                prerequisiteReadiness: 0.9,
            }));

            const result = (service as any).runGradientDescentOptimization(trainingData);

            for (const param of result.parameters) {
                expect(param).toBeGreaterThanOrEqual(0.001);
                expect(param).toBeLessThanOrEqual(10);
            }
        });
    });

    describe('Retention Prediction', () => {
        it('should predict retention between 0 and 1', () => {
            const data: TrainingDataPoint = {
                deltaT: 5,
                rating: 3,
                retention: 0.8,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            };

            const prediction = (service as any).predictRetention(data, DEFAULT_FSRS_PARAMETERS);

            expect(prediction).toBeGreaterThanOrEqual(0);
            expect(prediction).toBeLessThanOrEqual(1);
        });

        it('should predict higher retention for shorter intervals', () => {
            const shortInterval: TrainingDataPoint = {
                deltaT: 1,
                rating: 3,
                retention: 0.9,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            };

            const longInterval: TrainingDataPoint = {
                deltaT: 30,
                rating: 3,
                retention: 0.5,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            };

            const shortPrediction = (service as any).predictRetention(shortInterval, DEFAULT_FSRS_PARAMETERS);
            const longPrediction = (service as any).predictRetention(longInterval, DEFAULT_FSRS_PARAMETERS);

            expect(shortPrediction).toBeGreaterThan(longPrediction);
        });

        it('should predict higher retention for easier ratings', () => {
            const againRating: TrainingDataPoint = {
                deltaT: 5,
                rating: 1,
                retention: 0.5,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            };

            const easyRating: TrainingDataPoint = {
                deltaT: 5,
                rating: 4,
                retention: 0.9,
                conceptDifficulty: 0.5,
                docEngagement: 0.5,
                prerequisiteReadiness: 0.8,
            };

            const againPrediction = (service as any).predictRetention(againRating, DEFAULT_FSRS_PARAMETERS);
            const easyPrediction = (service as any).predictRetention(easyRating, DEFAULT_FSRS_PARAMETERS);

            expect(easyPrediction).toBeGreaterThan(againPrediction);
        });
    });

    describe('Loss Calculation', () => {
        it('should calculate RMSE loss', () => {
            const trainingData: TrainingDataPoint[] = [
                { deltaT: 1, rating: 3, retention: 0.9, conceptDifficulty: 0.5, docEngagement: 0.5, prerequisiteReadiness: 0.8 },
                { deltaT: 5, rating: 3, retention: 0.7, conceptDifficulty: 0.5, docEngagement: 0.5, prerequisiteReadiness: 0.8 },
                { deltaT: 10, rating: 3, retention: 0.5, conceptDifficulty: 0.5, docEngagement: 0.5, prerequisiteReadiness: 0.8 },
            ];

            const loss = (service as any).calculateLoss(trainingData, DEFAULT_FSRS_PARAMETERS);

            expect(loss).toBeGreaterThanOrEqual(0);
            expect(loss).toBeLessThan(1); // RMSE should be reasonable
        });

        it('should return 0 for empty data', () => {
            const loss = (service as any).calculateLoss([], DEFAULT_FSRS_PARAMETERS);
            expect(loss).toBe(0);
        });
    });
});

describe('DEFAULT_OPTIMIZER_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_OPTIMIZER_SETTINGS.apiBaseUrl).toBe('http://localhost:8000/api/v1');
        expect(DEFAULT_OPTIMIZER_SETTINGS.timeout).toBe(30000);
        expect(DEFAULT_OPTIMIZER_SETTINGS.minSamples).toBe(100);
        expect(DEFAULT_OPTIMIZER_SETTINGS.maxIterations).toBe(100);
        expect(DEFAULT_OPTIMIZER_SETTINGS.learningRate).toBe(0.01);
        expect(DEFAULT_OPTIMIZER_SETTINGS.convergenceThreshold).toBe(0.0001);
        expect(DEFAULT_OPTIMIZER_SETTINGS.autoOptimizeInterval).toBe(50);
        expect(DEFAULT_OPTIMIZER_SETTINGS.monthlyOptimizationEnabled).toBe(true);
        expect(DEFAULT_OPTIMIZER_SETTINGS.monthlyOptimizationDay).toBe(1);
        expect(DEFAULT_OPTIMIZER_SETTINGS.monthlyOptimizationHour).toBe(3);
    });
});

describe('DEFAULT_AB_TEST_CONFIG', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_AB_TEST_CONFIG.enabled).toBe(false);
        expect(DEFAULT_AB_TEST_CONFIG.testGroupRatio).toBe(0.5);
        expect(DEFAULT_AB_TEST_CONFIG.trackingPeriodDays).toBe(30);
        expect(DEFAULT_AB_TEST_CONFIG.minimumSamplesPerGroup).toBe(50);
    });
});

describe('createFSRSOptimizerService', () => {
    it('should create service instance', () => {
        const service = createFSRSOptimizerService(mockApp);
        expect(service).toBeInstanceOf(FSRSOptimizerService);
    });

    it('should create service with custom settings', () => {
        const service = createFSRSOptimizerService(mockApp, {
            minSamples: 50,
        });

        expect(service.getSettings().minSamples).toBe(50);
    });

    it('should create service with custom A/B config', () => {
        const service = createFSRSOptimizerService(mockApp, {}, {
            enabled: true,
        });

        expect(service.getABTestConfig().enabled).toBe(true);
    });
});
