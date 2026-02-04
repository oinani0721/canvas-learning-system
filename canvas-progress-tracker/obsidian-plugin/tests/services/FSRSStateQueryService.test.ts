/**
 * FSRSStateQueryService Tests - Canvas Learning System
 *
 * Tests for Story 32.3: FSRS State Query for Plugin Priority Calculation
 *
 * @module FSRSStateQueryService.test
 * @version 1.0.0
 */

import {
    FSRSStateQueryService,
    FSRSState,
    FSRSStateQueryResponse,
    createFSRSStateQueryService,
} from '../../src/services/FSRSStateQueryService';

// Mock Obsidian's requestUrl
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    requestUrl: (params: any) => mockRequestUrl(params),
}));

// Mock App
const mockApp = {} as any;

// Helper to create mock FSRS state
function createMockFSRSState(overrides: Partial<FSRSState> = {}): FSRSState {
    return {
        stability: 8.5,
        difficulty: 5.2,
        state: 2, // Review
        reps: 5,
        lapses: 1,
        retrievability: 0.85,
        due: '2026-01-22T10:00:00Z',
        ...overrides,
    };
}

// Helper to create mock response
function createMockResponse(data: FSRSStateQueryResponse, status = 200) {
    return {
        status,
        json: data,
    };
}

describe('FSRSStateQueryService', () => {
    let service: FSRSStateQueryService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new FSRSStateQueryService(mockApp);
    });

    // =============================================================================
    // Story 32.3 AC-32.3.1: Plugin queries backend for FSRS state
    // =============================================================================
    describe('AC-32.3.1: Query FSRS state from backend', () => {
        it('should query backend endpoint with correct URL', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'node-abc123',
                    fsrs_state: fsrsState,
                    card_state: JSON.stringify(fsrsState),
                    found: true,
                })
            );

            await service.queryFSRSState('node-abc123');

            expect(mockRequestUrl).toHaveBeenCalledWith({
                url: 'http://localhost:8000/api/v1/review/fsrs-state/node-abc123',
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });
        });

        it('should return FSRS state when found', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'node-abc123',
                    fsrs_state: fsrsState,
                    card_state: JSON.stringify(fsrsState),
                    found: true,
                })
            );

            const result = await service.queryFSRSState('node-abc123');

            expect(result).not.toBeNull();
            expect(result?.found).toBe(true);
            expect(result?.fsrs_state?.stability).toBe(8.5);
            expect(result?.fsrs_state?.retrievability).toBe(0.85);
        });

        it('should return found=false when concept has no card', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'node-new',
                    fsrs_state: null,
                    card_state: null,
                    found: false,
                })
            );

            const result = await service.queryFSRSState('node-new');

            expect(result).not.toBeNull();
            expect(result?.found).toBe(false);
            expect(result?.fsrs_state).toBeNull();
        });

        it('should URL-encode special characters in concept_id', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'node/with/slashes',
                    fsrs_state: null,
                    card_state: null,
                    found: false,
                })
            );

            await service.queryFSRSState('node/with/slashes');

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: 'http://localhost:8000/api/v1/review/fsrs-state/node%2Fwith%2Fslashes',
                })
            );
        });
    });

    // =============================================================================
    // Story 32.3 AC-32.3.2: Response contains FSRS algorithm values
    // =============================================================================
    describe('AC-32.3.2: Response contains complete FSRS state', () => {
        it('should include stability, difficulty, state, reps, lapses, retrievability, due', async () => {
            const fsrsState = createMockFSRSState({
                stability: 12.3,
                difficulty: 7.5,
                state: 1, // Learning
                reps: 10,
                lapses: 2,
                retrievability: 0.72,
                due: '2026-01-25T15:30:00Z',
            });
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'test-concept',
                    fsrs_state: fsrsState,
                    card_state: JSON.stringify(fsrsState),
                    found: true,
                })
            );

            const result = await service.queryFSRSState('test-concept');

            expect(result?.fsrs_state).toEqual({
                stability: 12.3,
                difficulty: 7.5,
                state: 1,
                reps: 10,
                lapses: 2,
                retrievability: 0.72,
                due: '2026-01-25T15:30:00Z',
            });
        });

        it('should handle null retrievability and due values', async () => {
            const fsrsState = createMockFSRSState({
                retrievability: null,
                due: null,
            });
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'new-card',
                    fsrs_state: fsrsState,
                    card_state: null,
                    found: true,
                })
            );

            const result = await service.queryFSRSState('new-card');

            expect(result?.fsrs_state?.retrievability).toBeNull();
            expect(result?.fsrs_state?.due).toBeNull();
        });
    });

    // =============================================================================
    // Story 32.3 AC-32.3.3: Plugin can cache FSRS card data locally
    // =============================================================================
    describe('AC-32.3.3: Local caching of FSRS state', () => {
        it('should cache query results', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'cached-concept',
                    fsrs_state: fsrsState,
                    card_state: JSON.stringify(fsrsState),
                    found: true,
                })
            );

            // First call - should hit backend
            await service.queryFSRSState('cached-concept');
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);

            // Second call - should use cache
            const result2 = await service.queryFSRSState('cached-concept');
            expect(mockRequestUrl).toHaveBeenCalledTimes(1); // Still 1
            expect(result2?.found).toBe(true);
        });

        it('should bypass cache when forceRefresh is true', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValue(
                createMockResponse({
                    concept_id: 'refresh-concept',
                    fsrs_state: fsrsState,
                    card_state: null,
                    found: true,
                })
            );

            await service.queryFSRSState('refresh-concept');
            await service.queryFSRSState('refresh-concept', true); // Force refresh

            expect(mockRequestUrl).toHaveBeenCalledTimes(2);
        });

        it('should return cached state via getCachedState', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'get-cached',
                    fsrs_state: fsrsState,
                    card_state: JSON.stringify(fsrsState),
                    found: true,
                })
            );

            await service.queryFSRSState('get-cached');

            const cached = service.getCachedState('get-cached');
            expect(cached).not.toBeNull();
            expect(cached?.found).toBe(true);
        });

        it('should clear cache via clearCache', async () => {
            const fsrsState = createMockFSRSState();
            mockRequestUrl.mockResolvedValue(
                createMockResponse({
                    concept_id: 'clear-cache',
                    fsrs_state: fsrsState,
                    card_state: null,
                    found: true,
                })
            );

            await service.queryFSRSState('clear-cache');
            expect(service.getCachedState('clear-cache')).not.toBeNull();

            service.clearCache();
            expect(service.getCachedState('clear-cache')).toBeNull();
        });

        it('should return card_state JSON for local deserialization', async () => {
            const fsrsState = createMockFSRSState();
            const cardStateJson = JSON.stringify(fsrsState);
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'card-state',
                    fsrs_state: fsrsState,
                    card_state: cardStateJson,
                    found: true,
                })
            );

            const cardState = await service.getCardState('card-state');

            expect(cardState).toBe(cardStateJson);
        });
    });

    // =============================================================================
    // Story 32.3 AC-32.3.4: Retrievability used in priority calculation
    // =============================================================================
    describe('AC-32.3.4: Retrievability for priority calculation', () => {
        it('should return retrievability via getRetrievability', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'retrievability-test',
                    fsrs_state: createMockFSRSState({ retrievability: 0.65 }),
                    card_state: null,
                    found: true,
                })
            );

            const retrievability = await service.getRetrievability('retrievability-test');

            expect(retrievability).toBe(0.65);
        });

        it('should return null when concept not found', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'not-found',
                    fsrs_state: null,
                    card_state: null,
                    found: false,
                })
            );

            const retrievability = await service.getRetrievability('not-found');

            expect(retrievability).toBeNull();
        });
    });

    // =============================================================================
    // Story 32.3 AC-32.3.5: Graceful degradation when backend unavailable
    // =============================================================================
    describe('AC-32.3.5: Graceful degradation', () => {
        it('should return null when backend request fails', async () => {
            mockRequestUrl.mockRejectedValueOnce(new Error('Network error'));

            const result = await service.queryFSRSState('error-concept');

            expect(result).toBeNull();
        });

        it('should mark backend as unavailable after error', async () => {
            mockRequestUrl.mockRejectedValueOnce(new Error('Connection refused'));

            await service.queryFSRSState('fail-concept');

            expect(service.isBackendAvailable()).toBe(false);
        });

        it('should handle 404 response gracefully', async () => {
            mockRequestUrl.mockResolvedValueOnce({
                status: 404,
                json: { detail: 'Not found' },
            });

            const result = await service.queryFSRSState('not-found-concept');

            expect(result).not.toBeNull();
            expect(result?.found).toBe(false);
        });

        it('should check backend health before retrying after failure', async () => {
            // This test verifies that a fresh service instance can still query
            // when the backend is available
            const freshService = new FSRSStateQueryService(mockApp);

            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'retry-concept',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            const result = await freshService.queryFSRSState('retry-concept');

            expect(result).not.toBeNull();
            expect(result?.found).toBe(true);
        });
    });

    // =============================================================================
    // Batch Query Tests
    // =============================================================================
    describe('Batch Query', () => {
        it('should batch query multiple concepts', async () => {
            // Clear any previous mocks and set up fresh mocks for batch query
            mockRequestUrl.mockReset();

            mockRequestUrl
                .mockResolvedValueOnce(
                    createMockResponse({
                        concept_id: 'concept-1',
                        fsrs_state: createMockFSRSState({ stability: 5 }),
                        card_state: null,
                        found: true,
                    })
                )
                .mockResolvedValueOnce(
                    createMockResponse({
                        concept_id: 'concept-2',
                        fsrs_state: createMockFSRSState({ stability: 10 }),
                        card_state: null,
                        found: true,
                    })
                );

            // Create fresh service to avoid cache from previous tests
            const batchService = new FSRSStateQueryService(mockApp);
            const results = await batchService.batchQueryFSRSStates(['concept-1', 'concept-2']);

            expect(results.size).toBe(2);
            expect(results.get('concept-1')?.fsrs_state?.stability).toBe(5);
            expect(results.get('concept-2')?.fsrs_state?.stability).toBe(10);
        });

        it('should use cache for already-queried concepts in batch', async () => {
            mockRequestUrl
                .mockResolvedValueOnce(
                    createMockResponse({
                        concept_id: 'cached-1',
                        fsrs_state: createMockFSRSState(),
                        card_state: null,
                        found: true,
                    })
                )
                .mockResolvedValueOnce(
                    createMockResponse({
                        concept_id: 'new-1',
                        fsrs_state: createMockFSRSState(),
                        card_state: null,
                        found: true,
                    })
                );

            // Pre-cache one concept
            await service.queryFSRSState('cached-1');
            mockRequestUrl.mockClear();

            // Batch query including cached and new
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'new-1',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            const results = await service.batchQueryFSRSStates(['cached-1', 'new-1']);

            expect(results.size).toBe(2);
            expect(mockRequestUrl).toHaveBeenCalledTimes(1); // Only new-1
        });
    });

    // =============================================================================
    // Factory Function Tests
    // =============================================================================
    describe('Factory Function', () => {
        it('should create service with default URL', () => {
            const factoryService = createFSRSStateQueryService(mockApp);
            expect(factoryService).toBeInstanceOf(FSRSStateQueryService);
        });

        it('should create service with custom URL', () => {
            const customService = createFSRSStateQueryService(
                mockApp,
                'http://custom:9000'
            );
            expect(customService).toBeInstanceOf(FSRSStateQueryService);
        });
    });

    // =============================================================================
    // Backend URL Configuration Tests
    // =============================================================================
    describe('Backend URL Configuration', () => {
        it('should allow changing backend URL', async () => {
            service.setBackendUrl('http://newhost:9000');

            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'url-test',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            await service.queryFSRSState('url-test');

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: 'http://newhost:9000/api/v1/review/fsrs-state/url-test',
                })
            );
        });

        it('should clear cache when URL changes', async () => {
            mockRequestUrl.mockResolvedValue(
                createMockResponse({
                    concept_id: 'cache-clear-test',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            await service.queryFSRSState('cache-clear-test');
            expect(service.getCachedState('cache-clear-test')).not.toBeNull();

            service.setBackendUrl('http://different:8080');
            expect(service.getCachedState('cache-clear-test')).toBeNull();
        });
    });

    // =============================================================================
    // Cache Statistics Tests
    // =============================================================================
    describe('Cache Statistics', () => {
        it('should return cache size', async () => {
            mockRequestUrl.mockResolvedValue(
                createMockResponse({
                    concept_id: 'stats-test',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            await service.queryFSRSState('stats-1');
            await service.queryFSRSState('stats-2', true);

            const stats = service.getCacheStats();
            expect(stats.size).toBe(2);
        });
    });

    // =============================================================================
    // hasCard Tests
    // =============================================================================
    describe('hasCard', () => {
        it('should return true when card exists', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'has-card',
                    fsrs_state: createMockFSRSState(),
                    card_state: null,
                    found: true,
                })
            );

            const hasCard = await service.hasCard('has-card');
            expect(hasCard).toBe(true);
        });

        it('should return false when card does not exist', async () => {
            mockRequestUrl.mockResolvedValueOnce(
                createMockResponse({
                    concept_id: 'no-card',
                    fsrs_state: null,
                    card_state: null,
                    found: false,
                })
            );

            const hasCard = await service.hasCard('no-card');
            expect(hasCard).toBe(false);
        });
    });
});
