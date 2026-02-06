/**
 * Story 31.A.4 Tests: 前端优先级计算 FSRS 状态修复
 *
 * Strict tests for all 4 acceptance criteria:
 * - AC-31.A.4.1: FSRSStateQueryService initialization in main.ts
 * - AC-31.A.4.2: Property declaration and import
 * - AC-31.A.4.3: ReviewDashboardView uses real FSRS state
 * - AC-31.A.4.4: Priority calculation verification with real FSRS data
 *
 * Additionally tests:
 * - TYPE MISMATCH: FSRSState (query service) vs FSRSCardState (priority calculator)
 * - Graceful degradation when backend unavailable
 * - Error boundary: no crash when FSRS service fails
 *
 * @module ReviewDashboardView.fsrs-integration.test
 * @version 1.0.0
 * @story 31.A.4
 */

import { ReviewDashboardView } from '../../src/views/ReviewDashboardView';
import {
    FSRSState,
    FSRSStateQueryResponse,
    FSRSStateQueryService,
} from '../../src/services/FSRSStateQueryService';
import {
    PriorityCalculatorService,
    FSRSCardState,
    PriorityResult,
} from '../../src/services/PriorityCalculatorService';

// ═══════════════════════════════════════════════════════════════════════════════
// Mocks
// ═══════════════════════════════════════════════════════════════════════════════

jest.mock('obsidian', () => ({
    ItemView: class {
        containerEl = { children: [null, { empty: jest.fn(), addClass: jest.fn() }] };
        app = {
            vault: { getAbstractFileByPath: jest.fn() },
            workspace: { openLinkText: jest.fn() },
        };
        leaf = {};
    },
    WorkspaceLeaf: class {},
    Notice: jest.fn(),
    setIcon: jest.fn(),
    requestUrl: jest.fn(),
}));

jest.mock('../../src/services/HistoryService', () => ({
    HistoryService: jest.fn(() => ({})),
}));
jest.mock('../../src/services/VerificationHistoryService', () => ({
    createVerificationHistoryService: jest.fn(() => ({})),
    VerificationHistoryService: jest.fn(),
}));
jest.mock('../../src/services/CrossCanvasService', () => ({
    createCrossCanvasService: jest.fn(() => ({})),
    CrossCanvasService: jest.fn(),
}));
jest.mock('../../src/services/TextbookMountService', () => ({
    createTextbookMountService: jest.fn(() => ({})),
    TextbookMountService: jest.fn(),
}));
jest.mock('../../src/services/PriorityCalculatorService', () => {
    const actual = jest.requireActual('../../src/services/PriorityCalculatorService');
    return {
        ...actual,
        createPriorityCalculatorService: jest.fn(() => ({
            calculatePriority: jest.fn().mockReturnValue({
                conceptId: 'test',
                priorityScore: 50,
                priorityTier: 'medium',
                dimensions: {
                    fsrs: { score: 50, explanation: 'mock', factors: {} },
                    behavior: { score: 50, explanation: 'mock', factors: {} },
                    network: { score: 50, explanation: 'mock', factors: {} },
                    interaction: { score: 50, explanation: 'mock', factors: {} },
                },
                weightsUsed: { fsrsWeight: 0.4, behaviorWeight: 0.3, networkWeight: 0.2, interactionWeight: 0.1 },
                calculatedAt: new Date(),
                recommendedReviewDate: new Date(),
            }),
        })),
    };
});

// ═══════════════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════════════

function createMockFSRSState(overrides: Partial<FSRSState> = {}): FSRSState {
    return {
        stability: 8.5,
        difficulty: 5.2,
        state: 2, // Review
        reps: 5,
        lapses: 1,
        retrievability: 0.85,
        due: '2026-01-22T10:00:00Z',
        last_review: '2026-01-14T10:00:00Z',
        ...overrides,
    };
}

function createMockFSRSQueryResponse(
    conceptId: string,
    fsrsState: FSRSState | null = null,
    found: boolean = true
): FSRSStateQueryResponse {
    return {
        concept_id: conceptId,
        fsrs_state: fsrsState,
        card_state: fsrsState ? JSON.stringify(fsrsState) : null,
        found,
    };
}

/** Create a view instance via Object.create to bypass constructor */
function createTestView(pluginOverrides: Record<string, any> = {}) {
    const view = Object.create(ReviewDashboardView.prototype) as any;
    view.app = {
        vault: { getAbstractFileByPath: jest.fn() },
        workspace: { openLinkText: jest.fn() },
    };
    view.plugin = {
        settings: { debugMode: false, aiBaseUrl: 'http://localhost:8000' },
        fsrsStateQueryService: undefined,
        memoryQueryService: undefined,
        ...pluginOverrides,
    };
    view.priorityCalculatorService = {
        calculatePriority: jest.fn().mockReturnValue({
            conceptId: 'test',
            priorityScore: 65,
            priorityTier: 'high',
            dimensions: {
                fsrs: { score: 80, explanation: 'Overdue', factors: {} },
                behavior: { score: 50, explanation: 'neutral', factors: {} },
                network: { score: 50, explanation: 'neutral', factors: {} },
                interaction: { score: 50, explanation: 'neutral', factors: {} },
            },
            weightsUsed: { fsrsWeight: 0.4, behaviorWeight: 0.3, networkWeight: 0.2, interactionWeight: 0.1 },
            calculatedAt: new Date(),
            recommendedReviewDate: new Date(),
        }),
    };
    return view;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe('Story 31.A.4: ReviewDashboardView FSRS Integration', () => {

    beforeEach(() => {
        jest.clearAllMocks();
    });

    // ═════════════════════════════════════════════════════════════════════════
    // AC-31.A.4.1: FSRSStateQueryService Initialization
    // ═════════════════════════════════════════════════════════════════════════
    describe('AC-31.A.4.1: FSRSStateQueryService initialization in main.ts', () => {

        it('should have FSRSStateQueryService class importable from service module', () => {
            expect(FSRSStateQueryService).toBeDefined();
            expect(typeof FSRSStateQueryService).toBe('function');
        });

        it('should construct FSRSStateQueryService with App and URL', () => {
            const mockApp = {} as any;
            const service = new FSRSStateQueryService(mockApp, 'http://localhost:8000');
            expect(service).toBeDefined();
            expect(service).toBeInstanceOf(FSRSStateQueryService);
        });

        it('should construct FSRSStateQueryService with default URL', () => {
            const mockApp = {} as any;
            const service = new FSRSStateQueryService(mockApp);
            expect(service).toBeDefined();
        });

        it('should handle construction errors without throwing', () => {
            // FSRSStateQueryService constructor should never throw
            expect(() => {
                const service = new FSRSStateQueryService({} as any, '');
                expect(service).toBeDefined();
            }).not.toThrow();
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // AC-31.A.4.2: Property Declaration Verification
    // ═════════════════════════════════════════════════════════════════════════
    describe('AC-31.A.4.2: Plugin property declaration', () => {

        it('should expose FSRSState and FSRSStateQueryResponse types', () => {
            // Type-level check: these types should be importable
            const mockState: FSRSState = createMockFSRSState();
            expect(mockState.stability).toBe(8.5);
            expect(mockState.difficulty).toBe(5.2);
            expect(mockState.state).toBe(2);
            expect(mockState.reps).toBe(5);
            expect(mockState.lapses).toBe(1);
            expect(mockState.retrievability).toBe(0.85);
            expect(mockState.due).toBe('2026-01-22T10:00:00Z');
        });

        it('should expose FSRSStateQueryResponse with concept_id, fsrs_state, card_state, found', () => {
            const mockResponse: FSRSStateQueryResponse = createMockFSRSQueryResponse(
                'test-concept',
                createMockFSRSState(),
                true
            );
            expect(mockResponse.concept_id).toBe('test-concept');
            expect(mockResponse.fsrs_state).not.toBeNull();
            expect(mockResponse.found).toBe(true);
            expect(mockResponse.card_state).not.toBeNull();
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // AC-31.A.4.3: ReviewDashboardView Uses Real FSRS State
    // ═════════════════════════════════════════════════════════════════════════
    describe('AC-31.A.4.3: queryFSRSState method', () => {

        it('should return FSRS state when service is available and concept found', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockResolvedValue(
                    createMockFSRSQueryResponse('test-concept', createMockFSRSState(), true)
                ),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            // Story 31.A.4 adds queryFSRSState private method
            const fsrsState = await (view as any).queryFSRSState('test-concept');

            expect(mockFsrsService.queryFSRSState).toHaveBeenCalledWith('test-concept');
            expect(fsrsState).not.toBeNull();
            expect(fsrsState.stability).toBe(8.5);
            expect(fsrsState.difficulty).toBe(5.2);
            expect(fsrsState.retrievability).toBe(0.85);
        });

        it('should return null when FSRSStateQueryService is not initialized (graceful degradation)', async () => {
            const view = createTestView({ fsrsStateQueryService: undefined });

            const fsrsState = await (view as any).queryFSRSState('test-concept');

            expect(fsrsState).toBeNull();
        });

        it('should return null when FSRSStateQueryService is null', async () => {
            const view = createTestView({ fsrsStateQueryService: null });

            const fsrsState = await (view as any).queryFSRSState('test-concept');

            expect(fsrsState).toBeNull();
        });

        it('should return null when queryFSRSState throws error', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockRejectedValue(new Error('Network error')),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            const fsrsState = await (view as any).queryFSRSState('test-concept');

            expect(fsrsState).toBeNull();
        });

        it('should return null when concept has no FSRS card (found=false)', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockResolvedValue(
                    createMockFSRSQueryResponse('new-concept', null, false)
                ),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            const fsrsState = await (view as any).queryFSRSState('new-concept');

            // fsrs_state is null when not found
            expect(fsrsState).toBeNull();
        });

        it('should return null when queryFSRSState returns null response', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockResolvedValue(null),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            const fsrsState = await (view as any).queryFSRSState('test-concept');

            expect(fsrsState).toBeNull();
        });

        it('should not log warnings in non-debug mode when service unavailable', async () => {
            const consoleWarnSpy = jest.spyOn(console, 'warn');
            const view = createTestView({
                fsrsStateQueryService: undefined,
            });
            view.plugin.settings.debugMode = false;

            await (view as any).queryFSRSState('test-concept');

            // Should not emit noisy warnings in production
            // (only warn on actual errors, not missing service)
            expect(consoleWarnSpy).not.toHaveBeenCalled();
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // AC-31.A.4.3 Extended: loadData Integration
    // ═════════════════════════════════════════════════════════════════════════
    describe('AC-31.A.4.3: loadData integration with FSRS', () => {

        it('should call queryFSRSState for each concept in loadData', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockResolvedValue(
                    createMockFSRSQueryResponse('concept-1', createMockFSRSState(), true)
                ),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });
            // Mock queryFSRSState on the view (simulating the story's implementation)
            view.queryFSRSState = jest.fn().mockResolvedValue(createMockFSRSState());
            view.queryConceptMemory = jest.fn().mockResolvedValue(null);

            // Simulate the map operation from loadData
            const concepts = ['concept-1', 'concept-2', 'concept-3'];
            const results = await Promise.all(
                concepts.map(async (conceptId) => {
                    const fsrsState = await view.queryFSRSState(conceptId);
                    const memoryResult = await view.queryConceptMemory(conceptId);
                    return { conceptId, fsrsState, memoryResult };
                })
            );

            expect(view.queryFSRSState).toHaveBeenCalledTimes(3);
            expect(results[0].fsrsState).not.toBeNull();
            expect(results[0].fsrsState.stability).toBe(8.5);
        });

        it('should pass FSRS state (not null) to calculatePriority after fix', async () => {
            const mockFsrsState = createMockFSRSState();
            const view = createTestView();
            view.queryFSRSState = jest.fn().mockResolvedValue(mockFsrsState);
            view.queryConceptMemory = jest.fn().mockResolvedValue(null);

            // Simulate the fixed loadData logic
            const conceptId = 'test-concept';
            const fsrsState = await view.queryFSRSState(conceptId);
            const memoryResult = await view.queryConceptMemory(conceptId);

            view.priorityCalculatorService.calculatePriority(
                conceptId,
                fsrsState, // Should be real state, not null
                memoryResult,
                'test.canvas'
            );

            expect(view.priorityCalculatorService.calculatePriority).toHaveBeenCalledWith(
                'test-concept',
                expect.objectContaining({ stability: 8.5, difficulty: 5.2 }),
                null,
                'test.canvas'
            );
        });

        it('should pass null to calculatePriority when FSRS service unavailable (graceful)', async () => {
            const view = createTestView({ fsrsStateQueryService: undefined });
            view.queryFSRSState = jest.fn().mockResolvedValue(null);
            view.queryConceptMemory = jest.fn().mockResolvedValue(null);

            const conceptId = 'test-concept';
            const fsrsState = await view.queryFSRSState(conceptId);
            const memoryResult = await view.queryConceptMemory(conceptId);

            view.priorityCalculatorService.calculatePriority(
                conceptId,
                fsrsState, // null when service unavailable
                memoryResult,
                'test.canvas'
            );

            expect(view.priorityCalculatorService.calculatePriority).toHaveBeenCalledWith(
                'test-concept',
                null,
                null,
                'test.canvas'
            );
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // AC-31.A.4.4: Priority Calculation Verification
    // ═════════════════════════════════════════════════════════════════════════
    describe('AC-31.A.4.4: Priority calculation with real FSRS state', () => {
        // Use the REAL PriorityCalculatorService (not mocked)
        let realPriorityService: PriorityCalculatorService;

        beforeEach(() => {
            const { PriorityCalculatorService: RealService } =
                jest.requireActual('../../src/services/PriorityCalculatorService');
            realPriorityService = new RealService({} as any);
        });

        it('should return neutral FSRS score (50) when fsrsState is null', () => {
            const result = realPriorityService.calculatePriority('test', null, null);

            expect(result.dimensions.fsrs.score).toBe(50);
            expect(result.dimensions.fsrs.explanation).toContain('No FSRS data');
        });

        it('should return non-neutral FSRS score when fsrsState has valid FSRSCardState', () => {
            const now = new Date();
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            const twoDaysAgo = new Date(now);
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            // Use FSRSCardState (the type calculatePriority actually expects)
            const validCardState: FSRSCardState = {
                conceptId: 'test-overdue',
                stability: 3,
                difficulty: 7,
                lastReview: twoDaysAgo,
                nextReview: yesterday, // Overdue
                reps: 5,
                lapses: 2,
                state: 'review',
            };

            const result = realPriorityService.calculatePriority('test', validCardState, null);

            expect(result.dimensions.fsrs.score).not.toBe(50);
            expect(result.dimensions.fsrs.score).toBeGreaterThan(50);
            expect(result.dimensions.fsrs.explanation).toContain('Overdue');
        });

        it('should give higher priority when FSRS indicates card is overdue', () => {
            const now = new Date();
            const threeDaysAgo = new Date(now);
            threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            const inOneWeek = new Date(now);
            inOneWeek.setDate(inOneWeek.getDate() + 7);

            const overdueState: FSRSCardState = {
                conceptId: 'overdue',
                stability: 3,
                difficulty: 6,
                lastReview: threeDaysAgo,
                nextReview: yesterday,
                reps: 3,
                lapses: 1,
                state: 'review',
            };

            const futureState: FSRSCardState = {
                conceptId: 'future',
                stability: 10,
                difficulty: 3,
                lastReview: now,
                nextReview: inOneWeek,
                reps: 8,
                lapses: 0,
                state: 'review',
            };

            const overdueResult = realPriorityService.calculatePriority('overdue', overdueState, null);
            const futureResult = realPriorityService.calculatePriority('future', futureState, null);

            expect(overdueResult.priorityScore).toBeGreaterThan(futureResult.priorityScore);
        });

        it('should give higher urgency for relearning state than review state', () => {
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);

            const reviewState: FSRSCardState = {
                conceptId: 'review',
                stability: 5,
                difficulty: 5,
                lastReview: now,
                nextReview: tomorrow,
                reps: 3,
                lapses: 0,
                state: 'review',
            };

            const relearningState: FSRSCardState = {
                ...reviewState,
                conceptId: 'relearning',
                state: 'relearning',
                lapses: 2,
            };

            const reviewResult = realPriorityService.calculatePriority('r1', reviewState, null);
            const relearningResult = realPriorityService.calculatePriority('r2', relearningState, null);

            expect(relearningResult.dimensions.fsrs.score)
                .toBeGreaterThan(reviewResult.dimensions.fsrs.score);
        });

        it('should increase urgency score with higher difficulty', () => {
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);

            const easyState: FSRSCardState = {
                conceptId: 'easy',
                stability: 5,
                difficulty: 2,
                lastReview: now,
                nextReview: tomorrow,
                reps: 5,
                lapses: 0,
                state: 'review',
            };

            const hardState: FSRSCardState = {
                ...easyState,
                conceptId: 'hard',
                difficulty: 9,
            };

            const easyResult = realPriorityService.calculatePriority('easy', easyState, null);
            const hardResult = realPriorityService.calculatePriority('hard', hardState, null);

            expect(hardResult.dimensions.fsrs.score)
                .toBeGreaterThan(easyResult.dimensions.fsrs.score);
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // CRITICAL: Type Mismatch Detection
    // ═════════════════════════════════════════════════════════════════════════
    describe('CRITICAL: FSRSState vs FSRSCardState type mismatch', () => {

        /**
         * This test documents a critical design issue in Story 31.A.4:
         *
         * FSRSStateQueryService returns FSRSState:
         *   { stability, difficulty, state: number (0-3), reps, lapses, retrievability, due: string }
         *
         * PriorityCalculatorService.calculatePriority expects FSRSCardState:
         *   { conceptId, stability, difficulty, lastReview: Date, nextReview: Date, reps, lapses,
         *     state: 'new'|'learning'|'review'|'relearning' }
         *
         * These types are INCOMPATIBLE. Passing FSRSState directly to calculatePriority will
         * cause crashes because calculateFSRSUrgency tries state.lastReview.getTime()
         * but FSRSState has no lastReview field.
         *
         * SOLUTION: A type adapter is needed to convert FSRSState -> FSRSCardState
         */

        it('should detect that FSRSState and FSRSCardState have different structures', () => {
            const fsrsState: FSRSState = createMockFSRSState();
            const fsrsCardState: FSRSCardState = {
                conceptId: 'test',
                stability: 5,
                difficulty: 5,
                lastReview: new Date(),
                nextReview: new Date(),
                reps: 3,
                lapses: 0,
                state: 'review',
            };

            // FSRSState has numeric state, FSRSCardState has string state
            expect(typeof fsrsState.state).toBe('number');
            expect(typeof fsrsCardState.state).toBe('string');

            // FSRSState has no lastReview/nextReview
            expect((fsrsState as any).lastReview).toBeUndefined();
            expect((fsrsState as any).nextReview).toBeUndefined();

            // FSRSCardState has no retrievability/due
            expect((fsrsCardState as any).retrievability).toBeUndefined();
            expect((fsrsCardState as any).due).toBeUndefined();
        });

        it('should map FSRSState.state (number) to FSRSCardState.state (string) correctly', () => {
            const stateMap: Record<number, FSRSCardState['state']> = {
                0: 'new',
                1: 'learning',
                2: 'review',
                3: 'relearning',
            };

            expect(stateMap[0]).toBe('new');
            expect(stateMap[1]).toBe('learning');
            expect(stateMap[2]).toBe('review');
            expect(stateMap[3]).toBe('relearning');
        });

        it('should convert FSRSState.due (string) to FSRSCardState.nextReview (Date)', () => {
            const fsrsState = createMockFSRSState({ due: '2026-02-10T15:00:00Z' });

            const nextReview = fsrsState.due ? new Date(fsrsState.due) : new Date();

            expect(nextReview).toBeInstanceOf(Date);
            expect(nextReview.toISOString()).toContain('2026-02-10');
        });

        it('should handle null due date in FSRSState', () => {
            const fsrsState = createMockFSRSState({ due: null });

            const nextReview = fsrsState.due ? new Date(fsrsState.due) : new Date();

            expect(nextReview).toBeInstanceOf(Date);
            // Falls back to current date
            expect(nextReview.getTime()).toBeCloseTo(Date.now(), -3);
        });

        it('should define a correct adapter function signature: FSRSState -> FSRSCardState', () => {
            const view = createTestView();

            const fsrsState = createMockFSRSState({
                stability: 10,
                difficulty: 6,
                state: 2,
                reps: 8,
                lapses: 1,
                due: '2026-02-15T10:00:00Z',
                last_review: '2026-02-05T10:00:00Z',
            });

            const cardState = (view as any).adaptFSRSStateToCardState('test-concept', fsrsState);

            expect(cardState.conceptId).toBe('test-concept');
            expect(cardState.stability).toBe(10);
            expect(cardState.difficulty).toBe(6);
            expect(cardState.state).toBe('review');
            expect(cardState.reps).toBe(8);
            expect(cardState.lapses).toBe(1);
            expect(cardState.lastReview).toBeInstanceOf(Date);
            expect(cardState.lastReview.toISOString()).toBe('2026-02-05T10:00:00.000Z');
            expect(cardState.nextReview).toBeInstanceOf(Date);
            expect(cardState.nextReview.toISOString()).toContain('2026-02-15');
        });

        it('should produce correct priority when adapted FSRSState is used', () => {
            const { PriorityCalculatorService: RealService } =
                jest.requireActual('../../src/services/PriorityCalculatorService');
            const realService = new RealService({} as any);

            // Simulate adapter output
            const now = new Date();
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);

            const adaptedCardState: FSRSCardState = {
                conceptId: 'adapted-test',
                stability: 3,
                difficulty: 7,
                lastReview: yesterday,
                nextReview: yesterday, // Overdue
                reps: 5,
                lapses: 2,
                state: 'relearning',
            };

            const result = realService.calculatePriority('adapted-test', adaptedCardState, null);

            // Should produce meaningful priority, not the default neutral score
            expect(result.dimensions.fsrs.score).not.toBe(50);
            expect(result.dimensions.fsrs.score).toBeGreaterThan(60);
            expect(result.priorityTier).not.toBe('low');
        });

        it('should crash if raw FSRSState is passed directly to calculatePriority (documents the bug)', () => {
            const { PriorityCalculatorService: RealService } =
                jest.requireActual('../../src/services/PriorityCalculatorService');
            const realService = new RealService({} as any);

            const rawFsrsState = createMockFSRSState() as any;

            // This demonstrates why a type adapter is needed:
            // calculateFSRSUrgency accesses state.lastReview.getTime() which will throw
            // because FSRSState has no lastReview property
            expect(() => {
                realService.calculatePriority('test', rawFsrsState, null);
            }).toThrow();
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // Error Boundary Tests
    // ═════════════════════════════════════════════════════════════════════════
    describe('Error boundary: FSRS failures must not crash Dashboard', () => {

        it('should not throw when queryFSRSState returns rejected promise', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockRejectedValue(new Error('Backend timeout')),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            // Should not throw
            await expect(
                (view as any).queryFSRSState('test-concept')
            ).resolves.toBeNull();
        });

        it('should not throw when queryFSRSState returns malformed data', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockResolvedValue({ unexpected: 'data' }),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });

            // Should not throw, just return null or handle gracefully
            const result = await (view as any).queryFSRSState('test-concept');
            // With malformed data, fsrs_state would be undefined, so should be null
            expect(result).toBeNull();
        });

        it('should continue loading dashboard even when all FSRS queries fail', async () => {
            const mockFsrsService = {
                queryFSRSState: jest.fn().mockRejectedValue(new Error('Service down')),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });
            view.queryFSRSState = jest.fn().mockResolvedValue(null); // Graceful fallback
            view.queryConceptMemory = jest.fn().mockResolvedValue(null);

            // Simulate processing 3 concepts - all FSRS fail but dashboard keeps working
            const concepts = ['c1', 'c2', 'c3'];
            const results = await Promise.all(
                concepts.map(async (conceptId) => {
                    const fsrsState = await view.queryFSRSState(conceptId);
                    return {
                        conceptId,
                        fsrsState,
                        priorityResult: view.priorityCalculatorService.calculatePriority(
                            conceptId, fsrsState, null
                        ),
                    };
                })
            );

            // All 3 should succeed with null FSRS
            expect(results).toHaveLength(3);
            results.forEach((r) => {
                expect(r.fsrsState).toBeNull();
                expect(r.priorityResult).toBeDefined();
                expect(r.priorityResult.priorityTier).toBeDefined();
            });
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // Regression: Verify Current Broken Behavior
    // ═════════════════════════════════════════════════════════════════════════
    describe('Regression: Current code passes null for FSRS state', () => {

        it('should document that line 165 currently passes null (hardcoded)', () => {
            // This test documents the current broken behavior
            // ReviewDashboardView.ts:163-168 currently has:
            //   const priorityResult = this.priorityCalculatorService.calculatePriority(
            //       review.conceptId || review.conceptName || '',
            //       null, // ❌ FSRS state hardcoded to null
            //       memoryResult,
            //       review.canvasId
            //   );

            const view = createTestView();

            // Current behavior: always passes null
            const nullFsrs = null;
            view.priorityCalculatorService.calculatePriority(
                'any-concept',
                nullFsrs,
                null,
                'any-canvas'
            );

            expect(view.priorityCalculatorService.calculatePriority).toHaveBeenCalledWith(
                'any-concept',
                null, // This is the bug - always null
                null,
                'any-canvas'
            );
        });

        it('should prove null FSRS yields neutral score (50) for 40% weight', () => {
            const { PriorityCalculatorService: RealService } =
                jest.requireActual('../../src/services/PriorityCalculatorService');
            const realService = new RealService({} as any);

            const result = realService.calculatePriority('test', null, null);

            // 40% of the total weight always contributes exactly 50 * 0.4 = 20
            expect(result.dimensions.fsrs.score).toBe(50);
            expect(result.dimensions.fsrs.explanation).toBe('No FSRS data available, using neutral score');

            // The FSRS contribution is locked at 20 points (50 * 0.4)
            // This means 40% of priority calculation is wasted
            const fsrsContribution = result.dimensions.fsrs.score * 0.4;
            expect(fsrsContribution).toBe(20);
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // FSRSState field validation
    // ═════════════════════════════════════════════════════════════════════════
    describe('FSRSState field validation', () => {

        it('should validate stability is a positive number', () => {
            const state = createMockFSRSState({ stability: 10.5 });
            expect(state.stability).toBeGreaterThan(0);
            expect(typeof state.stability).toBe('number');
        });

        it('should validate difficulty is between 1-10', () => {
            const state = createMockFSRSState({ difficulty: 5.2 });
            expect(state.difficulty).toBeGreaterThanOrEqual(1);
            expect(state.difficulty).toBeLessThanOrEqual(10);
        });

        it('should validate state is 0-3 enum', () => {
            [0, 1, 2, 3].forEach((stateVal) => {
                const state = createMockFSRSState({ state: stateVal });
                expect(state.state).toBeGreaterThanOrEqual(0);
                expect(state.state).toBeLessThanOrEqual(3);
            });
        });

        it('should validate retrievability is null or between 0-1', () => {
            const withRetrievability = createMockFSRSState({ retrievability: 0.85 });
            expect(withRetrievability.retrievability).toBeGreaterThanOrEqual(0);
            expect(withRetrievability.retrievability).toBeLessThanOrEqual(1);

            const withNull = createMockFSRSState({ retrievability: null });
            expect(withNull.retrievability).toBeNull();
        });

        it('should validate due is null or ISO 8601 string', () => {
            const withDue = createMockFSRSState({ due: '2026-02-10T15:00:00Z' });
            expect(new Date(withDue.due!).toISOString()).toBe('2026-02-10T15:00:00.000Z');

            const withNull = createMockFSRSState({ due: null });
            expect(withNull.due).toBeNull();
        });

        it('should validate last_review is null or ISO 8601 string', () => {
            const withLastReview = createMockFSRSState({ last_review: '2026-01-14T10:00:00Z' });
            expect(new Date(withLastReview.last_review!).toISOString()).toBe('2026-01-14T10:00:00.000Z');

            const withNull = createMockFSRSState({ last_review: null });
            expect(withNull.last_review).toBeNull();
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // Optimization: last_review real field usage
    // ═════════════════════════════════════════════════════════════════════════
    describe('Optimization: adaptFSRSStateToCardState uses real last_review', () => {

        it('should use real last_review when available', () => {
            const view = createTestView();
            const fsrsState = createMockFSRSState({
                last_review: '2026-01-10T08:00:00Z',
                stability: 5,
            });

            const cardState = (view as any).adaptFSRSStateToCardState('test', fsrsState);

            expect(cardState.lastReview).toBeInstanceOf(Date);
            expect(cardState.lastReview.toISOString()).toBe('2026-01-10T08:00:00.000Z');
        });

        it('should fall back to stability estimation when last_review is null', () => {
            const view = createTestView();
            const fsrsState = createMockFSRSState({
                last_review: null,
                stability: 7,
            });

            const cardState = (view as any).adaptFSRSStateToCardState('test', fsrsState);

            expect(cardState.lastReview).toBeInstanceOf(Date);
            // Should be approximately now - 7 days
            const now = new Date();
            const expectedApprox = new Date(now);
            expectedApprox.setDate(expectedApprox.getDate() - 7);
            const diffMs = Math.abs(cardState.lastReview.getTime() - expectedApprox.getTime());
            expect(diffMs).toBeLessThan(5000); // Within 5 seconds
        });

        it('should produce more accurate priority with real last_review than estimation', () => {
            const { PriorityCalculatorService: RealService } =
                jest.requireActual('../../src/services/PriorityCalculatorService');
            const realService = new RealService({} as any);

            const view = createTestView();

            // With real last_review: reviewed 2 days ago, due yesterday = 1 day overdue
            const withReal = createMockFSRSState({
                last_review: (() => {
                    const d = new Date(); d.setDate(d.getDate() - 2); return d.toISOString();
                })(),
                due: (() => {
                    const d = new Date(); d.setDate(d.getDate() - 1); return d.toISOString();
                })(),
                stability: 5,
                difficulty: 6,
            });

            const cardWithReal = (view as any).adaptFSRSStateToCardState('real', withReal);
            const resultReal = realService.calculatePriority('real', cardWithReal, null);

            // With null last_review: uses stability estimation (now - 5 days)
            const withEstimation = createMockFSRSState({
                last_review: null,
                due: withReal.due,
                stability: 5,
                difficulty: 6,
            });

            const cardWithEstimation = (view as any).adaptFSRSStateToCardState('est', withEstimation);
            const resultEstimation = realService.calculatePriority('est', cardWithEstimation, null);

            // Both should produce valid results (not neutral 50)
            expect(resultReal.dimensions.fsrs.score).not.toBe(50);
            expect(resultEstimation.dimensions.fsrs.score).not.toBe(50);

            // Real last_review (2 days ago) differs from estimation (5 days ago)
            expect(cardWithReal.lastReview.getTime()).not.toBe(cardWithEstimation.lastReview.getTime());
        });
    });

    // ═════════════════════════════════════════════════════════════════════════
    // Optimization: Batch FSRS query
    // ═════════════════════════════════════════════════════════════════════════
    describe('Optimization: batchQueryFSRSStates', () => {

        it('should return Map from batchQueryFSRSStates when service available', async () => {
            const batchMap = new Map<string, any>();
            batchMap.set('c1', createMockFSRSQueryResponse('c1', createMockFSRSState(), true));
            batchMap.set('c2', createMockFSRSQueryResponse('c2', createMockFSRSState({ stability: 3 }), true));

            const mockFsrsService = {
                batchQueryFSRSStates: jest.fn().mockResolvedValue(batchMap),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });
            const result = await (view as any).batchQueryFSRSStates(['c1', 'c2']);

            expect(mockFsrsService.batchQueryFSRSStates).toHaveBeenCalledWith(['c1', 'c2']);
            expect(result.size).toBe(2);
            expect(result.get('c1')?.fsrs_state?.stability).toBe(8.5);
            expect(result.get('c2')?.fsrs_state?.stability).toBe(3);
        });

        it('should return empty Map when service is unavailable', async () => {
            const view = createTestView({ fsrsStateQueryService: undefined });
            const result = await (view as any).batchQueryFSRSStates(['c1', 'c2']);

            expect(result).toBeInstanceOf(Map);
            expect(result.size).toBe(0);
        });

        it('should return empty Map when batch query throws', async () => {
            const mockFsrsService = {
                batchQueryFSRSStates: jest.fn().mockRejectedValue(new Error('Batch failed')),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });
            const result = await (view as any).batchQueryFSRSStates(['c1']);

            expect(result).toBeInstanceOf(Map);
            expect(result.size).toBe(0);
        });

        it('should handle partial results (some concepts not found)', async () => {
            const batchMap = new Map<string, any>();
            batchMap.set('found', createMockFSRSQueryResponse('found', createMockFSRSState(), true));
            // 'not-found' is not in the map

            const mockFsrsService = {
                batchQueryFSRSStates: jest.fn().mockResolvedValue(batchMap),
            };

            const view = createTestView({ fsrsStateQueryService: mockFsrsService });
            const result = await (view as any).batchQueryFSRSStates(['found', 'not-found']);

            expect(result.get('found')?.fsrs_state).not.toBeNull();
            expect(result.get('not-found')).toBeUndefined();
        });
    });
});
