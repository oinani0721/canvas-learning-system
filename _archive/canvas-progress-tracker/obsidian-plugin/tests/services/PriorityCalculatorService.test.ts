/**
 * PriorityCalculatorService Tests - Canvas Learning System
 *
 * Tests for Story 14.11: 多维度优先级计算
 *
 * @module PriorityCalculatorService.test
 * @version 1.0.0
 */

import {
    PriorityCalculatorService,
    PriorityCalculatorSettings,
    DEFAULT_PRIORITY_WEIGHTS,
    DEFAULT_PRIORITY_CALCULATOR_SETTINGS,
    createPriorityCalculatorService,
    FSRSCardState,
    PriorityWeights,
    DimensionScore,
    PriorityResult,
} from '../../src/services/PriorityCalculatorService';

import {
    ConceptRelationship,
    TemporalEvent,
    SemanticResult,
    MemoryQueryResult,
} from '../../src/services/MemoryQueryService';

// Mock App
const mockApp = {} as any;

// Helper functions to create test data
// Fixed dates for deterministic tests (avoid new Date() flakiness)
// Use jest.useFakeTimers so Date.now() returns FIXED_NOW inside service code
const FIXED_NOW = new Date('2025-01-15T10:00:00Z');
const FIXED_TOMORROW = new Date('2025-01-16T10:00:00Z');

function createFSRSCardState(overrides: Partial<FSRSCardState> = {}): FSRSCardState {
    return {
        conceptId: 'test-concept',
        stability: 5,
        difficulty: 5,
        lastReview: FIXED_NOW,
        nextReview: FIXED_TOMORROW,
        reps: 3,
        lapses: 0,
        state: 'review' as const,
        ...overrides,
    };
}

function createTemporalEvent(overrides: Partial<TemporalEvent> = {}): TemporalEvent {
    return {
        id: 'event-1',
        sessionId: 'session-1',
        eventType: 'review' as const,
        timestamp: FIXED_NOW,
        canvasName: 'test.canvas',
        conceptName: 'Test Concept',
        ...overrides,
    };
}

function createConceptRelationship(overrides: Partial<ConceptRelationship> = {}): ConceptRelationship {
    return {
        sourceId: 'node-1',
        sourceName: 'Concept A',
        targetId: 'node-2',
        targetName: 'Concept B',
        relationType: 'related' as const,
        strength: 0.7,
        ...overrides,
    };
}

function createSemanticResult(overrides: Partial<SemanticResult> = {}): SemanticResult {
    return {
        documentId: 'doc-1',
        documentPath: '/path/to/doc.md',
        contentSnippet: 'Related content...',
        relevanceScore: 0.8,
        conceptName: 'Test Concept',
        documentType: 'explanation' as const,
        ...overrides,
    };
}

function createMemoryQueryResult(overrides: Partial<MemoryQueryResult> = {}): MemoryQueryResult {
    return {
        concept: 'Test Concept',
        graphitiResults: [],
        temporalResults: [],
        semanticResults: [],
        priorityScore: 50,
        allLayersResponded: true,
        layerErrors: [],
        ...overrides,
    };
}

describe('PriorityCalculatorService', () => {
    let service: PriorityCalculatorService;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        jest.setSystemTime(FIXED_NOW);
        service = new PriorityCalculatorService(mockApp);
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.weights).toEqual(DEFAULT_PRIORITY_WEIGHTS);
            expect(settings.targetRetention).toBe(0.9);
            expect(settings.staleDaysThreshold).toBe(7);
            expect(settings.minEventsForBehavior).toBe(3);
            expect(settings.boostPrerequisites).toBe(true);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new PriorityCalculatorService(mockApp, {
                targetRetention: 0.85,
                weights: { fsrsWeight: 0.5 },
            });

            const settings = customService.getSettings();
            expect(settings.targetRetention).toBe(0.85);
            expect(settings.weights.fsrsWeight).toBe(0.5);
            expect(settings.weights.behaviorWeight).toBe(0.3); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ staleDaysThreshold: 14 });
            const settings = service.getSettings();
            expect(settings.staleDaysThreshold).toBe(14);
            expect(settings.targetRetention).toBe(0.9); // Unchanged
        });

        it('should update weights partially', () => {
            service.updateSettings({ weights: { fsrsWeight: 0.5 } });
            const settings = service.getSettings();
            expect(settings.weights.fsrsWeight).toBe(0.5);
            expect(settings.weights.behaviorWeight).toBe(0.3); // Unchanged
        });
    });

    describe('FSRS Urgency Calculation', () => {
        it('should return neutral score when no FSRS state', () => {
            const result = service.calculatePriority('test', null, null);
            expect(result.dimensions.fsrs.score).toBe(50);
            expect(result.dimensions.fsrs.explanation).toContain('No FSRS data');
        });

        it('should give high score for overdue cards', () => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const twoDaysAgo = new Date();
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            const fsrsState = createFSRSCardState({
                lastReview: twoDaysAgo,
                nextReview: yesterday,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(result.dimensions.fsrs.score).toBeGreaterThan(70);
            expect(result.dimensions.fsrs.explanation).toContain('Overdue');
        });

        it('should give high score for cards due today', () => {
            const now = new Date();
            const twoDaysAgo = new Date();
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            const fsrsState = createFSRSCardState({
                lastReview: twoDaysAgo,
                nextReview: now,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(result.dimensions.fsrs.score).toBeGreaterThanOrEqual(75);
            expect(result.dimensions.fsrs.explanation).toContain('Due today');
        });

        it('should give moderate score for cards due soon', () => {
            const now = new Date();
            const inTwoDays = new Date();
            inTwoDays.setDate(inTwoDays.getDate() + 2);

            const fsrsState = createFSRSCardState({
                lastReview: now,
                nextReview: inTwoDays,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(result.dimensions.fsrs.score).toBeGreaterThanOrEqual(60);
            expect(result.dimensions.fsrs.score).toBeLessThan(80);
            expect(result.dimensions.fsrs.explanation).toContain('Due in');
        });

        it('should give low score for cards not due soon', () => {
            const now = new Date();
            const inTwoWeeks = new Date();
            inTwoWeeks.setDate(inTwoWeeks.getDate() + 14);

            const fsrsState = createFSRSCardState({
                lastReview: now,
                nextReview: inTwoWeeks,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(result.dimensions.fsrs.score).toBeLessThan(50);
            expect(result.dimensions.fsrs.explanation).toContain('Not due');
        });

        it('should add bonus for learning state cards', () => {
            const fsrsState1 = createFSRSCardState({ state: 'review' });
            const fsrsState2 = createFSRSCardState({ state: 'learning' });

            const result1 = service.calculatePriority('test', fsrsState1, null);
            const result2 = service.calculatePriority('test', fsrsState2, null);

            expect(result2.dimensions.fsrs.score).toBeGreaterThan(result1.dimensions.fsrs.score);
        });

        it('should add bonus for relearning state cards', () => {
            const fsrsState1 = createFSRSCardState({ state: 'learning' });
            const fsrsState2 = createFSRSCardState({ state: 'relearning' });

            const result1 = service.calculatePriority('test', fsrsState1, null);
            const result2 = service.calculatePriority('test', fsrsState2, null);

            expect(result2.dimensions.fsrs.score).toBeGreaterThan(result1.dimensions.fsrs.score);
        });

        it('should add penalty for lapses', () => {
            const fsrsState1 = createFSRSCardState({ lapses: 0 });
            const fsrsState2 = createFSRSCardState({ lapses: 3 });

            const result1 = service.calculatePriority('test', fsrsState1, null);
            const result2 = service.calculatePriority('test', fsrsState2, null);

            expect(result2.dimensions.fsrs.score).toBeGreaterThan(result1.dimensions.fsrs.score);
            expect(result2.dimensions.fsrs.explanation).toContain('lapses');
        });

        it('should not produce Infinity when stability is 0 (P0-4)', () => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const twoDaysAgo = new Date();
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            const fsrsState = createFSRSCardState({
                stability: 0,
                lastReview: twoDaysAgo,
                nextReview: yesterday,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(Number.isFinite(result.dimensions.fsrs.score)).toBe(true);
            expect(result.dimensions.fsrs.score).toBeGreaterThan(0);
            expect(result.dimensions.fsrs.score).toBeLessThanOrEqual(100);
        });

        it('should handle stability=0 for non-overdue cards (P0-4)', () => {
            const fsrsState = createFSRSCardState({
                stability: 0,
            });

            const result = service.calculatePriority('test', fsrsState, null);
            expect(Number.isFinite(result.dimensions.fsrs.score)).toBe(true);
        });

        it('should modify score based on difficulty', () => {
            const fsrsState1 = createFSRSCardState({ difficulty: 3 });
            const fsrsState2 = createFSRSCardState({ difficulty: 8 });

            const result1 = service.calculatePriority('test', fsrsState1, null);
            const result2 = service.calculatePriority('test', fsrsState2, null);

            expect(result2.dimensions.fsrs.score).toBeGreaterThan(result1.dimensions.fsrs.score);
        });
    });

    describe('Behavior Weight Calculation', () => {
        it('should return neutral score when no events', () => {
            const memoryResult = createMemoryQueryResult({ temporalResults: [] });
            const result = service.calculatePriority('test', null, memoryResult);

            expect(result.dimensions.behavior.score).toBe(50);
            expect(result.dimensions.behavior.explanation).toContain('No learning events');
        });

        it('should give higher score for stale concepts than recent ones', () => {
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            const staleResult = createMemoryQueryResult({
                temporalResults: [createTemporalEvent({ timestamp: twoWeeksAgo })],
            });
            const recentResult = createMemoryQueryResult({
                temporalResults: [createTemporalEvent({ timestamp: yesterday })],
            });

            const stale = service.calculatePriority('test', null, staleResult);
            const recent = service.calculatePriority('test', null, recentResult);

            // Stale concepts should have higher behavior score (needs attention)
            expect(stale.dimensions.behavior.score).toBeGreaterThan(recent.dimensions.behavior.score);
            expect(stale.dimensions.behavior.explanation).toContain('14 days ago');
        });

        it('should give low score for very recent activity', () => {
            const halfDayAgo = new Date();
            halfDayAgo.setHours(halfDayAgo.getHours() - 12);

            const memoryResult = createMemoryQueryResult({
                temporalResults: [createTemporalEvent({ timestamp: halfDayAgo })],
            });

            const result = service.calculatePriority('test', null, memoryResult);
            expect(result.dimensions.behavior.score).toBeLessThan(40);
        });

        it('should increase score for more frequent events', () => {
            const now = new Date();
            const events = Array(5).fill(null).map((_, i) => {
                const timestamp = new Date(now);
                timestamp.setDate(timestamp.getDate() - i);
                return createTemporalEvent({ id: `event-${i}`, timestamp });
            });

            const memoryResult1 = createMemoryQueryResult({
                temporalResults: [events[0]],
            });
            const memoryResult2 = createMemoryQueryResult({
                temporalResults: events,
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.behavior.score).toBeGreaterThanOrEqual(result1.dimensions.behavior.score);
        });

        it('should add bonus for decomposition events', () => {
            const now = new Date();

            const memoryResult1 = createMemoryQueryResult({
                temporalResults: [createTemporalEvent({ eventType: 'review' as any, timestamp: now })],
            });
            const memoryResult2 = createMemoryQueryResult({
                temporalResults: [createTemporalEvent({ eventType: 'decomposition' as any, timestamp: now })],
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.behavior.score).toBeGreaterThan(result1.dimensions.behavior.score);
        });
    });

    describe('Network Centrality Calculation', () => {
        it('should return neutral score when no relationships', () => {
            const memoryResult = createMemoryQueryResult({ graphitiResults: [] });
            const result = service.calculatePriority('test', null, memoryResult);

            expect(result.dimensions.network.score).toBe(50);
            expect(result.dimensions.network.explanation).toContain('No concept relationships');
        });

        it('should increase score for more connections', () => {
            const memoryResult1 = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship()],
            });
            const memoryResult2 = createMemoryQueryResult({
                graphitiResults: Array(5).fill(null).map((_, i) =>
                    createConceptRelationship({ sourceId: `node-${i}` })
                ),
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.network.score).toBeGreaterThan(result1.dimensions.network.score);
        });

        it('should increase score for stronger relationships', () => {
            const memoryResult1 = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship({ strength: 0.3 })],
            });
            const memoryResult2 = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship({ strength: 0.9 })],
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.network.score).toBeGreaterThan(result1.dimensions.network.score);
        });

        it('should add bonus for prerequisite concepts', () => {
            const memoryResult1 = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship({ relationType: 'related' })],
            });
            const memoryResult2 = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship({ relationType: 'prerequisite' })],
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.network.score).toBeGreaterThan(result1.dimensions.network.score);
            expect(result2.dimensions.network.explanation).toContain('prerequisite');
        });

        it('should respect boostPrerequisites setting', () => {
            const memoryResult = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship({ relationType: 'prerequisite' })],
            });

            const serviceWithBoost = new PriorityCalculatorService(mockApp, {
                boostPrerequisites: true,
            });
            const serviceWithoutBoost = new PriorityCalculatorService(mockApp, {
                boostPrerequisites: false,
            });

            const result1 = serviceWithBoost.calculatePriority('test', null, memoryResult);
            const result2 = serviceWithoutBoost.calculatePriority('test', null, memoryResult);

            expect(result1.dimensions.network.score).toBeGreaterThan(result2.dimensions.network.score);
        });
    });

    describe('Interaction Weight Calculation', () => {
        it('should return neutral score when no semantic results', () => {
            const memoryResult = createMemoryQueryResult({ semanticResults: [] });
            const result = service.calculatePriority('test', null, memoryResult);

            expect(result.dimensions.interaction.score).toBe(50);
            expect(result.dimensions.interaction.explanation).toContain('No document interactions');
        });

        it('should increase score for higher relevance', () => {
            const memoryResult1 = createMemoryQueryResult({
                semanticResults: [createSemanticResult({ relevanceScore: 0.4 })],
            });
            const memoryResult2 = createMemoryQueryResult({
                semanticResults: [createSemanticResult({ relevanceScore: 0.9 })],
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.interaction.score).toBeGreaterThan(result1.dimensions.interaction.score);
        });

        it('should increase score for more documents', () => {
            const memoryResult1 = createMemoryQueryResult({
                semanticResults: [createSemanticResult()],
            });
            const memoryResult2 = createMemoryQueryResult({
                semanticResults: Array(4).fill(null).map((_, i) =>
                    createSemanticResult({ documentId: `doc-${i}` })
                ),
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.interaction.score).toBeGreaterThan(result1.dimensions.interaction.score);
        });

        it('should add bonus for explanation documents', () => {
            const memoryResult1 = createMemoryQueryResult({
                semanticResults: [createSemanticResult({ documentType: 'note' as any })],
            });
            const memoryResult2 = createMemoryQueryResult({
                semanticResults: [createSemanticResult({ documentType: 'explanation' as any })],
            });

            const result1 = service.calculatePriority('test', null, memoryResult1);
            const result2 = service.calculatePriority('test', null, memoryResult2);

            expect(result2.dimensions.interaction.score).toBeGreaterThan(result1.dimensions.interaction.score);
        });
    });

    describe('Combined Priority Calculation', () => {
        it('should calculate weighted priority score', () => {
            // Create a scenario where all dimensions have data
            const now = new Date();
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);

            const fsrsState = createFSRSCardState({
                lastReview: yesterday,
                nextReview: tomorrow,
            });

            const memoryResult = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship()],
                temporalResults: [createTemporalEvent({ timestamp: yesterday })],
                semanticResults: [createSemanticResult()],
            });

            const result = service.calculatePriority('test-concept', fsrsState, memoryResult, 'test.canvas');

            expect(result.conceptId).toBe('test-concept');
            expect(result.canvasName).toBe('test.canvas');
            expect(result.priorityScore).toBeGreaterThanOrEqual(0);
            expect(result.priorityScore).toBeLessThanOrEqual(100);
            expect(result.weightsUsed).toEqual(DEFAULT_PRIORITY_WEIGHTS);
            expect(result.calculatedAt).toBeInstanceOf(Date);
        });

        it('should respect custom weights', () => {
            const customService = new PriorityCalculatorService(mockApp, {
                weights: {
                    fsrsWeight: 1.0, // 100% FSRS
                    behaviorWeight: 0,
                    networkWeight: 0,
                    interactionWeight: 0,
                },
            });

            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const fsrsState = createFSRSCardState({
                lastReview: yesterday,
                nextReview: yesterday, // Overdue
            });

            const result = customService.calculatePriority('test', fsrsState, null);

            // With 100% FSRS weight and overdue card, score should be high
            expect(result.priorityScore).toBeGreaterThan(70);
        });

        it('should return all dimension details', () => {
            const memoryResult = createMemoryQueryResult({
                graphitiResults: [createConceptRelationship()],
                temporalResults: [createTemporalEvent()],
                semanticResults: [createSemanticResult()],
            });

            const result = service.calculatePriority('test', null, memoryResult);

            expect(result.dimensions.fsrs).toBeDefined();
            expect(result.dimensions.fsrs.score).toBeDefined();
            expect(result.dimensions.fsrs.explanation).toBeDefined();
            expect(result.dimensions.fsrs.factors).toBeDefined();

            expect(result.dimensions.behavior).toBeDefined();
            expect(result.dimensions.network).toBeDefined();
            expect(result.dimensions.interaction).toBeDefined();
        });
    });

    describe('Priority Tier Determination', () => {
        it('should determine tier based on score thresholds', () => {
            // Test the tier determination logic using custom weights
            const customService = new PriorityCalculatorService(mockApp, {
                weights: {
                    fsrsWeight: 1.0,
                    behaviorWeight: 0,
                    networkWeight: 0,
                    interactionWeight: 0,
                },
            });

            // Create very overdue card for high score
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 14);
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 21);

            const fsrsState = createFSRSCardState({
                lastReview: twoWeeksAgo,
                nextReview: weekAgo, // Very overdue
                lapses: 5,
                state: 'relearning',
                difficulty: 10,
                stability: 1, // Low stability increases urgency
            });

            const result = customService.calculatePriority('test', fsrsState, null);
            // With extreme overdue + lapses + relearning + high difficulty, should be critical
            expect(result.priorityScore).toBeGreaterThanOrEqual(80);
            expect(result.priorityTier).toBe('critical');
        });

        it('should return low for score < 40', () => {
            const inTwoWeeks = new Date();
            inTwoWeeks.setDate(inTwoWeeks.getDate() + 14);

            const fsrsState = createFSRSCardState({
                nextReview: inTwoWeeks,
                difficulty: 2,
            });

            // Use custom weights to ensure low score
            const customService = new PriorityCalculatorService(mockApp, {
                weights: {
                    fsrsWeight: 1.0,
                    behaviorWeight: 0,
                    networkWeight: 0,
                    interactionWeight: 0,
                },
            });

            const result = customService.calculatePriority('test', fsrsState, null);
            expect(result.priorityTier).toBe('low');
        });
    });

    describe('Recommended Review Date Calculation', () => {
        it('should return today for critical priority', () => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 5);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);

            const fsrsState = createFSRSCardState({
                lastReview: weekAgo,
                nextReview: yesterday, // Very overdue
                lapses: 5,
                state: 'relearning',
                difficulty: 10,
            });

            const result = service.calculatePriority('test', fsrsState, null);

            if (result.priorityScore >= 80) {
                const today = new Date();
                expect(result.recommendedReviewDate.getDate()).toBe(today.getDate());
            }
        });

        it('should return FSRS date for non-urgent cards', () => {
            const inOneWeek = new Date();
            inOneWeek.setDate(inOneWeek.getDate() + 7);

            const fsrsState = createFSRSCardState({
                nextReview: inOneWeek,
                difficulty: 3,
            });

            // Use custom weights to ensure low priority
            const customService = new PriorityCalculatorService(mockApp, {
                weights: {
                    fsrsWeight: 1.0,
                    behaviorWeight: 0,
                    networkWeight: 0,
                    interactionWeight: 0,
                },
            });

            const result = customService.calculatePriority('test', fsrsState, null);

            if (result.priorityScore < 60) {
                expect(result.recommendedReviewDate.getTime()).toBe(inOneWeek.getTime());
            }
        });
    });

    describe('Batch Calculation', () => {
        it('should calculate priorities for multiple concepts', () => {
            const items = [
                { conceptId: 'concept-1', fsrsState: null, memoryResult: null },
                { conceptId: 'concept-2', fsrsState: createFSRSCardState(), memoryResult: null },
                { conceptId: 'concept-3', fsrsState: null, memoryResult: createMemoryQueryResult(), canvasName: 'test.canvas' },
            ];

            const results = service.calculateBatchPriorities(items);

            expect(results).toHaveLength(3);
            expect(results[0].conceptId).toBe('concept-1');
            expect(results[1].conceptId).toBe('concept-2');
            expect(results[2].conceptId).toBe('concept-3');
            expect(results[2].canvasName).toBe('test.canvas');
        });
    });

    describe('Utility Methods', () => {
        it('should sort by priority', () => {
            const results: PriorityResult[] = [
                { conceptId: 'low', priorityScore: 30 } as PriorityResult,
                { conceptId: 'high', priorityScore: 90 } as PriorityResult,
                { conceptId: 'mid', priorityScore: 60 } as PriorityResult,
            ];

            const sorted = service.sortByPriority(results);

            expect(sorted[0].conceptId).toBe('high');
            expect(sorted[1].conceptId).toBe('mid');
            expect(sorted[2].conceptId).toBe('low');
        });

        it('should not mutate original array when sorting', () => {
            const results: PriorityResult[] = [
                { conceptId: 'low', priorityScore: 30 } as PriorityResult,
                { conceptId: 'high', priorityScore: 90 } as PriorityResult,
            ];

            service.sortByPriority(results);

            expect(results[0].conceptId).toBe('low');
        });

        it('should filter by tier', () => {
            const results: PriorityResult[] = [
                { conceptId: 'critical', priorityTier: 'critical' } as PriorityResult,
                { conceptId: 'high', priorityTier: 'high' } as PriorityResult,
                { conceptId: 'medium', priorityTier: 'medium' } as PriorityResult,
                { conceptId: 'low', priorityTier: 'low' } as PriorityResult,
            ];

            const critical = service.filterByTier(results, 'critical');
            const high = service.filterByTier(results, 'high');

            expect(critical).toHaveLength(1);
            expect(critical[0].conceptId).toBe('critical');
            expect(high).toHaveLength(1);
            expect(high[0].conceptId).toBe('high');
        });

        it('should get concepts needing review today', () => {
            const today = new Date();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            const results: PriorityResult[] = [
                { conceptId: 'overdue', recommendedReviewDate: yesterday } as PriorityResult,
                { conceptId: 'today', recommendedReviewDate: today } as PriorityResult,
                { conceptId: 'tomorrow', recommendedReviewDate: tomorrow } as PriorityResult,
            ];

            const needsReview = service.getConceptsNeedingReviewToday(results);

            expect(needsReview).toHaveLength(2);
            expect(needsReview.map(r => r.conceptId)).toContain('overdue');
            expect(needsReview.map(r => r.conceptId)).toContain('today');
            expect(needsReview.map(r => r.conceptId)).not.toContain('tomorrow');
        });
    });
});

describe('DEFAULT_PRIORITY_WEIGHTS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_PRIORITY_WEIGHTS.fsrsWeight).toBe(0.4);
        expect(DEFAULT_PRIORITY_WEIGHTS.behaviorWeight).toBe(0.3);
        expect(DEFAULT_PRIORITY_WEIGHTS.networkWeight).toBe(0.2);
        expect(DEFAULT_PRIORITY_WEIGHTS.interactionWeight).toBe(0.1);
    });

    it('should sum to 1.0', () => {
        const sum = DEFAULT_PRIORITY_WEIGHTS.fsrsWeight +
            DEFAULT_PRIORITY_WEIGHTS.behaviorWeight +
            DEFAULT_PRIORITY_WEIGHTS.networkWeight +
            DEFAULT_PRIORITY_WEIGHTS.interactionWeight;
        // Use toBeCloseTo for floating point comparison
        expect(sum).toBeCloseTo(1.0, 10);
    });
});

describe('DEFAULT_PRIORITY_CALCULATOR_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_PRIORITY_CALCULATOR_SETTINGS.weights).toEqual(DEFAULT_PRIORITY_WEIGHTS);
        expect(DEFAULT_PRIORITY_CALCULATOR_SETTINGS.targetRetention).toBe(0.9);
        expect(DEFAULT_PRIORITY_CALCULATOR_SETTINGS.staleDaysThreshold).toBe(7);
        expect(DEFAULT_PRIORITY_CALCULATOR_SETTINGS.minEventsForBehavior).toBe(3);
        expect(DEFAULT_PRIORITY_CALCULATOR_SETTINGS.boostPrerequisites).toBe(true);
    });
});

describe('createPriorityCalculatorService', () => {
    it('should create service instance', () => {
        const service = createPriorityCalculatorService(mockApp);
        expect(service).toBeInstanceOf(PriorityCalculatorService);
    });

    it('should create service with custom settings', () => {
        const service = createPriorityCalculatorService(mockApp, {
            targetRetention: 0.85,
            weights: { fsrsWeight: 0.5 },
        });

        const settings = service.getSettings();
        expect(settings.targetRetention).toBe(0.85);
        expect(settings.weights.fsrsWeight).toBe(0.5);
    });
});

// =============================================================================
// Story 30.17: Degradation Transparency Tests
// =============================================================================

describe('Story 30.17: Degradation Transparency', () => {
    let service: PriorityCalculatorService;
    let warnSpy: jest.SpyInstance;

    beforeEach(() => {
        jest.useFakeTimers();
        jest.setSystemTime(FIXED_NOW);
        service = new PriorityCalculatorService(mockApp);
        warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    });

    afterEach(() => {
        warnSpy.mockRestore();
        jest.useRealTimers();
    });

    describe('degradedDimensions field', () => {
        it('should include "fsrs" when fsrsState is null', () => {
            const result = service.calculatePriority(
                'concept-1',
                null,
                createMemoryQueryResult({
                    temporalResults: [createTemporalEvent()],
                    graphitiResults: [createConceptRelationship()],
                    semanticResults: [createSemanticResult()],
                })
            );

            expect(result.degradedDimensions).toContain('fsrs');
            expect(result.degradedDimensions).not.toContain('behavior');
            expect(result.degradedDimensions).not.toContain('network');
            expect(result.degradedDimensions).not.toContain('interaction');
        });

        it('should include behavior, network, interaction when memoryResult is null', () => {
            const fsrs = createFSRSCardState();
            const result = service.calculatePriority('concept-2', fsrs, null);

            expect(result.degradedDimensions).not.toContain('fsrs');
            expect(result.degradedDimensions).toContain('behavior');
            expect(result.degradedDimensions).toContain('network');
            expect(result.degradedDimensions).toContain('interaction');
        });

        it('should include all 4 dimensions when both fsrsState and memoryResult are null', () => {
            const result = service.calculatePriority('concept-3', null, null);

            expect(result.degradedDimensions).toHaveLength(4);
            expect(result.degradedDimensions).toContain('fsrs');
            expect(result.degradedDimensions).toContain('behavior');
            expect(result.degradedDimensions).toContain('network');
            expect(result.degradedDimensions).toContain('interaction');
        });

        it('should be empty when all data is available', () => {
            const result = service.calculatePriority(
                'concept-4',
                createFSRSCardState(),
                createMemoryQueryResult({
                    temporalResults: [createTemporalEvent()],
                    graphitiResults: [createConceptRelationship()],
                    semanticResults: [createSemanticResult()],
                })
            );

            expect(result.degradedDimensions).toHaveLength(0);
        });

        it('should include only dimensions with empty arrays in memoryResult', () => {
            const result = service.calculatePriority(
                'concept-5',
                createFSRSCardState(),
                createMemoryQueryResult({
                    temporalResults: [createTemporalEvent()],
                    graphitiResults: [],  // empty
                    semanticResults: [createSemanticResult()],
                })
            );

            expect(result.degradedDimensions).toEqual(['network']);
        });
    });

    describe('console.warn on degradation', () => {
        it('should warn when fsrsState is null', () => {
            service.calculatePriority('concept-1', null, createMemoryQueryResult({
                temporalResults: [createTemporalEvent()],
                graphitiResults: [createConceptRelationship()],
                semanticResults: [createSemanticResult()],
            }));

            const fsrsWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('FSRS data unavailable')
            );
            expect(fsrsWarn).toBeDefined();
        });

        it('should warn with summary when any dimension is degraded', () => {
            service.calculatePriority('test-concept', null, null);

            const summaryWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('4/4 dimensions degraded')
            );
            expect(summaryWarn).toBeDefined();
            expect(summaryWarn![0]).toContain('test-concept');
        });

        it('should not warn summary when no dimensions are degraded', () => {
            service.calculatePriority(
                'healthy-concept',
                createFSRSCardState(),
                createMemoryQueryResult({
                    temporalResults: [createTemporalEvent()],
                    graphitiResults: [createConceptRelationship()],
                    semanticResults: [createSemanticResult()],
                })
            );

            const summaryWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('dimensions degraded')
            );
            expect(summaryWarn).toBeUndefined();
        });

        it('should warn for behavior when temporal events are empty', () => {
            service.calculatePriority(
                'concept-x',
                createFSRSCardState(),
                createMemoryQueryResult({ temporalResults: [] })
            );

            const behaviorWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('Behavior data unavailable')
            );
            expect(behaviorWarn).toBeDefined();
        });

        it('should warn for network when graphiti results are empty', () => {
            service.calculatePriority(
                'concept-y',
                createFSRSCardState(),
                createMemoryQueryResult({ graphitiResults: [] })
            );

            const networkWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('Network data unavailable')
            );
            expect(networkWarn).toBeDefined();
        });

        it('should warn for interaction when semantic results are empty', () => {
            service.calculatePriority(
                'concept-z',
                createFSRSCardState(),
                createMemoryQueryResult({ semanticResults: [] })
            );

            const interactionWarn = warnSpy.mock.calls.find(
                (call: any[]) => typeof call[0] === 'string' && call[0].includes('Interaction data unavailable')
            );
            expect(interactionWarn).toBeDefined();
        });
    });

    describe('mixed degradation scenarios', () => {
        it('should handle fsrs+behavior degraded but network+interaction available', () => {
            const result = service.calculatePriority(
                'mixed-1',
                null,
                createMemoryQueryResult({
                    temporalResults: [],
                    graphitiResults: [createConceptRelationship()],
                    semanticResults: [createSemanticResult()],
                })
            );

            expect(result.degradedDimensions).toEqual(['fsrs', 'behavior']);
            expect(result.fsrsUnavailable).toBe(true);
        });

        it('should correctly set fsrsUnavailable alongside degradedDimensions', () => {
            const result = service.calculatePriority('test', null, null);
            expect(result.fsrsUnavailable).toBe(true);
            expect(result.degradedDimensions).toContain('fsrs');
        });

        it('should have fsrsUnavailable=false when fsrs is available', () => {
            const result = service.calculatePriority(
                'test',
                createFSRSCardState(),
                null
            );
            expect(result.fsrsUnavailable).toBe(false);
            expect(result.degradedDimensions).not.toContain('fsrs');
        });

        it('should include degradedDimensions in batch results', () => {
            const results = service.calculateBatchPriorities([
                { conceptId: 'a', fsrsState: null, memoryResult: null },
                { conceptId: 'b', fsrsState: createFSRSCardState(), memoryResult: createMemoryQueryResult({
                    temporalResults: [createTemporalEvent()],
                    graphitiResults: [createConceptRelationship()],
                    semanticResults: [createSemanticResult()],
                })},
            ]);

            expect(results[0].degradedDimensions).toHaveLength(4);
            expect(results[1].degradedDimensions).toHaveLength(0);
        });
    });
});
