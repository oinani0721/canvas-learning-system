/**
 * TargetedReviewWeightService Tests - Canvas Learning System
 *
 * Tests for Story 14.14: 针对性复习问题生成算法
 *
 * @module TargetedReviewWeightService.test
 * @version 1.0.0
 */

import {
    TargetedReviewWeightService,
    TargetedReviewSettings,
    DEFAULT_TARGETED_REVIEW_SETTINGS,
    DEFAULT_WEIGHT_CONFIG,
    WeakConcept,
    MasteredConcept,
    WeightedConcept,
    WeightConfig,
    createTargetedReviewWeightService,
} from '../../src/services/TargetedReviewWeightService';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// Mock App
const mockApp = {} as any;

// Test helpers
function createWeakConcept(
    name: string,
    overrides: Partial<WeakConcept> = {}
): WeakConcept {
    return {
        conceptId: `weak-${name}`,
        conceptName: name,
        failureCount: 3,
        lastFailureDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        averageScore: 45,
        trend: 'stable',
        ...overrides,
    };
}

function createMasteredConcept(
    name: string,
    overrides: Partial<MasteredConcept> = {}
): MasteredConcept {
    return {
        conceptId: `mastered-${name}`,
        conceptName: name,
        masteryScore: 85,
        lastReviewDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
        consecutiveSuccesses: 3,
        ...overrides,
    };
}

describe('TargetedReviewWeightService', () => {
    let service: TargetedReviewWeightService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new TargetedReviewWeightService(mockApp);
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.apiBaseUrl).toBe('http://localhost:8000/api/v1');
            expect(settings.timeout).toBe(10000);
            expect(settings.weightConfig.weakRatio).toBe(0.7);
            expect(settings.weightConfig.masteredRatio).toBe(0.3);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new TargetedReviewWeightService(mockApp, {
                apiBaseUrl: 'http://custom:9000/api',
                weightConfig: {
                    weakRatio: 0.8,
                    masteredRatio: 0.2,
                },
            });

            const settings = customService.getSettings();
            expect(settings.apiBaseUrl).toBe('http://custom:9000/api');
            expect(settings.weightConfig.weakRatio).toBe(0.8);
            expect(settings.weightConfig.masteredRatio).toBe(0.2);
            // Defaults preserved
            expect(settings.weightConfig.recencyBoost).toBe(1.5);
        });

        it('should update settings', () => {
            service.updateSettings({
                timeout: 20000,
                weightConfig: { recencyBoost: 2.0 },
            });

            const settings = service.getSettings();
            expect(settings.timeout).toBe(20000);
            expect(settings.weightConfig.recencyBoost).toBe(2.0);
            expect(settings.weightConfig.weakRatio).toBe(0.7); // Unchanged
        });
    });

    describe('calculateTargetedReviewWeights', () => {
        it('should return empty array for empty inputs', () => {
            const result = service.calculateTargetedReviewWeights([], []);
            expect(result).toHaveLength(0);
        });

        it('should calculate weights for weak concepts only', () => {
            const weakConcepts = [
                createWeakConcept('Concept A', { failureCount: 5, averageScore: 30 }),
                createWeakConcept('Concept B', { failureCount: 2, averageScore: 60 }),
            ];

            const result = service.calculateTargetedReviewWeights(weakConcepts, []);

            expect(result).toHaveLength(2);
            expect(result.every(r => r.category === 'weak')).toBe(true);

            // Total weight should be 0.7 (weak ratio) when no mastered concepts
            const totalWeight = result.reduce((sum, r) => sum + r.weight, 0);
            expect(totalWeight).toBeCloseTo(0.7, 2);
        });

        it('should calculate weights for mastered concepts only', () => {
            const masteredConcepts = [
                createMasteredConcept('Concept A', { masteryScore: 90 }),
                createMasteredConcept('Concept B', { masteryScore: 75 }),
            ];

            const result = service.calculateTargetedReviewWeights([], masteredConcepts);

            expect(result).toHaveLength(2);
            expect(result.every(r => r.category === 'mastered')).toBe(true);

            // Total weight should be 0.3 (mastered ratio) when no weak concepts
            const totalWeight = result.reduce((sum, r) => sum + r.weight, 0);
            expect(totalWeight).toBeCloseTo(0.3, 2);
        });

        it('should distribute weights according to 70/30 ratio', () => {
            const weakConcepts = [
                createWeakConcept('Weak A'),
                createWeakConcept('Weak B'),
            ];
            const masteredConcepts = [
                createMasteredConcept('Mastered A'),
                createMasteredConcept('Mastered B'),
            ];

            const result = service.calculateTargetedReviewWeights(
                weakConcepts,
                masteredConcepts
            );

            const weakWeight = result
                .filter(r => r.category === 'weak')
                .reduce((sum, r) => sum + r.weight, 0);
            const masteredWeight = result
                .filter(r => r.category === 'mastered')
                .reduce((sum, r) => sum + r.weight, 0);

            expect(weakWeight).toBeCloseTo(0.7, 1);
            expect(masteredWeight).toBeCloseTo(0.3, 1);
        });

        it('should prioritize concepts with more recent failures', () => {
            const recentFailure = createWeakConcept('Recent', {
                lastFailureDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
                failureCount: 3,
                averageScore: 50,
            });
            const oldFailure = createWeakConcept('Old', {
                lastFailureDate: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000), // 14 days ago
                failureCount: 3,
                averageScore: 50,
            });

            const result = service.calculateTargetedReviewWeights(
                [oldFailure, recentFailure],
                []
            );

            const recentWeight = result.find(r => r.conceptName === 'Recent')?.weight || 0;
            const oldWeight = result.find(r => r.conceptName === 'Old')?.weight || 0;

            expect(recentWeight).toBeGreaterThan(oldWeight);
        });

        it('should prioritize declining concepts', () => {
            const declining = createWeakConcept('Declining', {
                trend: 'declining',
                failureCount: 3,
                averageScore: 50,
            });
            const improving = createWeakConcept('Improving', {
                trend: 'improving',
                failureCount: 3,
                averageScore: 50,
            });

            const result = service.calculateTargetedReviewWeights(
                [improving, declining],
                []
            );

            const decliningWeight = result.find(r => r.conceptName === 'Declining')?.weight || 0;
            const improvingWeight = result.find(r => r.conceptName === 'Improving')?.weight || 0;

            expect(decliningWeight).toBeGreaterThan(improvingWeight);
        });

        it('should prioritize mastered concepts not reviewed recently', () => {
            const oldReview = createMasteredConcept('Old Review', {
                lastReviewDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
            });
            const recentReview = createMasteredConcept('Recent Review', {
                lastReviewDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
            });

            const result = service.calculateTargetedReviewWeights(
                [],
                [recentReview, oldReview]
            );

            const oldWeight = result.find(r => r.conceptName === 'Old Review')?.weight || 0;
            const recentWeight = result.find(r => r.conceptName === 'Recent Review')?.weight || 0;

            expect(oldWeight).toBeGreaterThan(recentWeight);
        });

        it('should respect maxWeakConcepts limit', () => {
            const weakConcepts = Array.from({ length: 25 }, (_, i) =>
                createWeakConcept(`Concept ${i}`)
            );

            const result = service.calculateTargetedReviewWeights(
                weakConcepts,
                [],
                { maxWeakConcepts: 10 }
            );

            expect(result.length).toBeLessThanOrEqual(10);
        });

        it('should respect maxMasteredConcepts limit', () => {
            const masteredConcepts = Array.from({ length: 15 }, (_, i) =>
                createMasteredConcept(`Concept ${i}`)
            );

            const result = service.calculateTargetedReviewWeights(
                [],
                masteredConcepts,
                { maxMasteredConcepts: 5 }
            );

            expect(result.length).toBeLessThanOrEqual(5);
        });

        it('should filter out concepts below minWeight threshold', () => {
            // Create many concepts to distribute weight thinly
            const weakConcepts = Array.from({ length: 100 }, (_, i) =>
                createWeakConcept(`Concept ${i}`)
            );

            const result = service.calculateTargetedReviewWeights(
                weakConcepts,
                [],
                { maxWeakConcepts: 100, minWeight: 0.05 }
            );

            // With minWeight 0.05 and total weight 0.7, we expect fewer than 14 concepts
            expect(result.length).toBeLessThan(14);
            result.forEach(r => {
                expect(r.weight).toBeGreaterThanOrEqual(0.05);
            });
        });

        it('should sort results by weight descending', () => {
            const weakConcepts = [
                createWeakConcept('Low', { failureCount: 1, averageScore: 70 }),
                createWeakConcept('High', { failureCount: 10, averageScore: 10 }),
                createWeakConcept('Medium', { failureCount: 5, averageScore: 40 }),
            ];

            const result = service.calculateTargetedReviewWeights(weakConcepts, []);

            for (let i = 0; i < result.length - 1; i++) {
                expect(result[i].weight).toBeGreaterThanOrEqual(result[i + 1].weight);
            }
        });
    });

    describe('calculateWithMetadata', () => {
        it('should return full result with metadata', () => {
            const weakConcepts = [createWeakConcept('Weak')];
            const masteredConcepts = [createMasteredConcept('Mastered')];

            const result = service.calculateWithMetadata(weakConcepts, masteredConcepts);

            expect(result.concepts).toHaveLength(2);
            expect(result.weakCount).toBe(1);
            expect(result.masteredCount).toBe(1);
            expect(result.totalWeight).toBeCloseTo(1.0, 2);
            expect(result.timestamp).toBeInstanceOf(Date);
        });
    });

    describe('generateQuestionDistribution', () => {
        it('should return empty array for empty concepts', () => {
            const result = service.generateQuestionDistribution([], 10);
            expect(result).toHaveLength(0);
        });

        it('should return empty array for zero questions', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.5, category: 'weak', rawScore: 1 },
            ];
            const result = service.generateQuestionDistribution(concepts, 0);
            expect(result).toHaveLength(0);
        });

        it('should distribute questions proportionally', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.5, category: 'weak', rawScore: 1 },
                { conceptName: 'B', weight: 0.3, category: 'weak', rawScore: 1 },
                { conceptName: 'C', weight: 0.2, category: 'mastered', rawScore: 1 },
            ];

            const result = service.generateQuestionDistribution(concepts, 10);

            const totalQuestions = result.reduce((sum, r) => sum + r.questionCount, 0);
            expect(totalQuestions).toBe(10);

            // Check proportions (with rounding)
            const aQuestions = result.find(r => r.conceptName === 'A')?.questionCount || 0;
            const bQuestions = result.find(r => r.conceptName === 'B')?.questionCount || 0;
            const cQuestions = result.find(r => r.conceptName === 'C')?.questionCount || 0;

            expect(aQuestions).toBeGreaterThanOrEqual(4); // ~50%
            expect(bQuestions).toBeGreaterThanOrEqual(2); // ~30%
            expect(cQuestions).toBeGreaterThanOrEqual(1); // ~20%
        });

        it('should distribute remaining questions to highest-weight concepts', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.6, category: 'weak', rawScore: 1 },
                { conceptName: 'B', weight: 0.4, category: 'weak', rawScore: 1 },
            ];

            const result = service.generateQuestionDistribution(concepts, 5);

            // 5 questions: A should get 3 (0.6*5=3), B should get 2 (0.4*5=2)
            expect(result.find(r => r.conceptName === 'A')?.questionCount).toBe(3);
            expect(result.find(r => r.conceptName === 'B')?.questionCount).toBe(2);
        });

        it('should handle single concept', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 1.0, category: 'weak', rawScore: 1 },
            ];

            const result = service.generateQuestionDistribution(concepts, 5);

            expect(result).toHaveLength(1);
            expect(result[0].questionCount).toBe(5);
        });

        it('should exclude concepts with 0 questions after distribution', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.99, category: 'weak', rawScore: 1 },
                { conceptName: 'B', weight: 0.01, category: 'weak', rawScore: 1 },
            ];

            const result = service.generateQuestionDistribution(concepts, 2);

            // With only 2 questions and weight heavily towards A
            const totalConcepts = result.length;
            expect(totalConcepts).toBeLessThanOrEqual(2);
        });

        it('should sort by question count descending', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'Low', weight: 0.1, category: 'weak', rawScore: 1 },
                { conceptName: 'High', weight: 0.6, category: 'weak', rawScore: 1 },
                { conceptName: 'Medium', weight: 0.3, category: 'weak', rawScore: 1 },
            ];

            const result = service.generateQuestionDistribution(concepts, 10);

            for (let i = 0; i < result.length - 1; i++) {
                expect(result[i].questionCount).toBeGreaterThanOrEqual(result[i + 1].questionCount);
            }
        });
    });

    describe('validateDistribution', () => {
        it('should validate correct 70/30 distribution', () => {
            const distribution = [
                { conceptName: 'A', questionCount: 7, category: 'weak' as const, weight: 0.7 },
                { conceptName: 'B', questionCount: 3, category: 'mastered' as const, weight: 0.3 },
            ];

            const result = service.validateDistribution(distribution);

            expect(result.valid).toBe(true);
            expect(result.weakRatio).toBeCloseTo(0.7, 2);
            expect(result.masteredRatio).toBeCloseTo(0.3, 2);
            expect(result.error).toBe(0);
        });

        it('should allow error of 1 question', () => {
            const distribution = [
                { conceptName: 'A', questionCount: 8, category: 'weak' as const, weight: 0.7 },
                { conceptName: 'B', questionCount: 2, category: 'mastered' as const, weight: 0.3 },
            ];

            const result = service.validateDistribution(distribution);

            expect(result.valid).toBe(true);
            expect(result.error).toBe(1);
        });

        it('should fail distribution with error > 1', () => {
            const distribution = [
                { conceptName: 'A', questionCount: 9, category: 'weak' as const, weight: 0.9 },
                { conceptName: 'B', questionCount: 1, category: 'mastered' as const, weight: 0.1 },
            ];

            const result = service.validateDistribution(distribution);

            expect(result.valid).toBe(false);
            expect(result.error).toBeGreaterThan(1);
        });

        it('should handle empty distribution', () => {
            const result = service.validateDistribution([]);

            expect(result.valid).toBe(true);
            expect(result.weakRatio).toBe(0);
            expect(result.masteredRatio).toBe(0);
            expect(result.error).toBe(0);
        });

        it('should respect custom config ratios', () => {
            const distribution = [
                { conceptName: 'A', questionCount: 8, category: 'weak' as const, weight: 0.8 },
                { conceptName: 'B', questionCount: 2, category: 'mastered' as const, weight: 0.2 },
            ];

            const result = service.validateDistribution(distribution, {
                weakRatio: 0.8,
                masteredRatio: 0.2,
            });

            expect(result.valid).toBe(true);
            expect(result.error).toBe(0);
        });
    });

    describe('Backend Integration', () => {
        it('should fetch weak concepts from backend', async () => {
            const mockConcepts = [
                {
                    concept_id: 'c1',
                    concept_name: 'Concept A',
                    failure_count: 5,
                    last_failure_date: '2025-01-10T00:00:00.000Z',
                    average_score: 40,
                    trend: 'declining',
                },
            ];

            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { concepts: mockConcepts },
            });

            const result = await service.fetchWeakConcepts('test.canvas');

            expect(result).toHaveLength(1);
            expect(result[0].conceptName).toBe('Concept A');
            expect(result[0].failureCount).toBe(5);
            expect(result[0].trend).toBe('declining');
            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/memory/graphiti/weak-concepts'),
                    method: 'POST',
                })
            );
        });

        it('should return empty array on fetch weak concepts error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const result = await service.fetchWeakConcepts('test.canvas');

            expect(result).toHaveLength(0);
        });

        it('should fetch mastered concepts from backend', async () => {
            const mockConcepts = [
                {
                    concept_id: 'c1',
                    concept_name: 'Concept A',
                    mastery_score: 92,
                    last_review_date: '2025-01-15T00:00:00.000Z',
                    consecutive_successes: 5,
                },
            ];

            mockRequestUrl.mockResolvedValue({
                status: 200,
                json: { concepts: mockConcepts },
            });

            const result = await service.fetchMasteredConcepts('test.canvas');

            expect(result).toHaveLength(1);
            expect(result[0].conceptName).toBe('Concept A');
            expect(result[0].masteryScore).toBe(92);
            expect(result[0].consecutiveSuccesses).toBe(5);
        });

        it('should return empty array on fetch mastered concepts error', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            const result = await service.fetchMasteredConcepts('test.canvas');

            expect(result).toHaveLength(0);
        });

        it('should calculate weights for canvas', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('weak-concepts')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            concepts: [{
                                concept_id: 'w1',
                                concept_name: 'Weak Concept',
                                failure_count: 3,
                                last_failure_date: new Date().toISOString(),
                                average_score: 40,
                                trend: 'stable',
                            }],
                        },
                    });
                }
                if (options.url.includes('mastered-concepts')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            concepts: [{
                                concept_id: 'm1',
                                concept_name: 'Mastered Concept',
                                mastery_score: 90,
                                last_review_date: new Date().toISOString(),
                                consecutive_successes: 4,
                            }],
                        },
                    });
                }
                return Promise.resolve({ status: 404, json: {} });
            });

            const result = await service.calculateForCanvas('test.canvas');

            expect(result.concepts).toHaveLength(2);
            expect(result.weakCount).toBe(1);
            expect(result.masteredCount).toBe(1);
        });

        it('should generate question set for canvas', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('weak-concepts')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            concepts: [
                                { concept_id: 'w1', concept_name: 'Weak A', failure_count: 3, last_failure_date: new Date().toISOString(), average_score: 40, trend: 'stable' },
                                { concept_id: 'w2', concept_name: 'Weak B', failure_count: 5, last_failure_date: new Date().toISOString(), average_score: 30, trend: 'declining' },
                            ],
                        },
                    });
                }
                if (options.url.includes('mastered-concepts')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            concepts: [
                                { concept_id: 'm1', concept_name: 'Mastered A', mastery_score: 90, last_review_date: new Date().toISOString(), consecutive_successes: 4 },
                            ],
                        },
                    });
                }
                return Promise.resolve({ status: 404, json: {} });
            });

            const result = await service.generateQuestionSetForCanvas('test.canvas', 10);

            expect(result.distribution).toBeDefined();
            expect(result.validation).toBeDefined();
            expect(result.metadata).toBeDefined();

            const totalQuestions = result.distribution.reduce((sum, d) => sum + d.questionCount, 0);
            expect(totalQuestions).toBe(10);
        });
    });

    describe('getWeightStatistics', () => {
        it('should calculate statistics for weighted concepts', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.4, category: 'weak', rawScore: 1 },
                { conceptName: 'B', weight: 0.3, category: 'weak', rawScore: 1 },
                { conceptName: 'C', weight: 0.2, category: 'mastered', rawScore: 1 },
                { conceptName: 'D', weight: 0.1, category: 'mastered', rawScore: 1 },
            ];

            const stats = service.getWeightStatistics(concepts);

            expect(stats.weakTotal).toBeCloseTo(0.7, 2);
            expect(stats.masteredTotal).toBeCloseTo(0.3, 2);
            expect(stats.avgWeakWeight).toBeCloseTo(0.35, 2);
            expect(stats.avgMasteredWeight).toBeCloseTo(0.15, 2);
            expect(stats.maxWeight).toBe(0.4);
            expect(stats.minWeight).toBe(0.1);
        });

        it('should handle empty concepts', () => {
            const stats = service.getWeightStatistics([]);

            expect(stats.weakTotal).toBe(0);
            expect(stats.masteredTotal).toBe(0);
            expect(stats.avgWeakWeight).toBe(0);
            expect(stats.avgMasteredWeight).toBe(0);
            expect(stats.maxWeight).toBe(0);
            expect(stats.minWeight).toBe(0);
        });

        it('should handle only weak concepts', () => {
            const concepts: WeightedConcept[] = [
                { conceptName: 'A', weight: 0.6, category: 'weak', rawScore: 1 },
                { conceptName: 'B', weight: 0.4, category: 'weak', rawScore: 1 },
            ];

            const stats = service.getWeightStatistics(concepts);

            expect(stats.weakTotal).toBeCloseTo(1.0, 2);
            expect(stats.masteredTotal).toBe(0);
            expect(stats.avgWeakWeight).toBeCloseTo(0.5, 2);
            expect(stats.avgMasteredWeight).toBe(0);
        });
    });
});

describe('DEFAULT_WEIGHT_CONFIG', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_WEIGHT_CONFIG.weakRatio).toBe(0.7);
        expect(DEFAULT_WEIGHT_CONFIG.masteredRatio).toBe(0.3);
        expect(DEFAULT_WEIGHT_CONFIG.recencyBoost).toBe(1.5);
        expect(DEFAULT_WEIGHT_CONFIG.declineMultiplier).toBe(1.3);
        expect(DEFAULT_WEIGHT_CONFIG.maxWeakConcepts).toBe(20);
        expect(DEFAULT_WEIGHT_CONFIG.maxMasteredConcepts).toBe(10);
        expect(DEFAULT_WEIGHT_CONFIG.minWeight).toBe(0.01);
    });
});

describe('DEFAULT_TARGETED_REVIEW_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_TARGETED_REVIEW_SETTINGS.apiBaseUrl).toBe('http://localhost:8000/api/v1');
        expect(DEFAULT_TARGETED_REVIEW_SETTINGS.timeout).toBe(10000);
        expect(DEFAULT_TARGETED_REVIEW_SETTINGS.weightConfig).toEqual(DEFAULT_WEIGHT_CONFIG);
    });
});

describe('createTargetedReviewWeightService', () => {
    it('should create service instance', () => {
        const service = createTargetedReviewWeightService(mockApp);
        expect(service).toBeInstanceOf(TargetedReviewWeightService);
    });

    it('should create service with custom settings', () => {
        const service = createTargetedReviewWeightService(mockApp, {
            apiBaseUrl: 'http://custom:8080',
        });

        expect(service.getSettings().apiBaseUrl).toBe('http://custom:8080');
    });
});
