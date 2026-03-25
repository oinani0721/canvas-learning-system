/**
 * BehaviorMonitorService Tests - Canvas Learning System
 *
 * Tests for Story 14.10: 行为监控触发机制（触发点4）
 *
 * @module BehaviorMonitorService.test
 * @version 1.0.0
 */

import {
    BehaviorMonitorService,
    BehaviorMonitorSettings,
    DEFAULT_BEHAVIOR_MONITOR_SETTINGS,
    createBehaviorMonitorService,
    WeaknessCluster,
    StaleReviewConcept,
    ReviewRecommendation,
} from '../../src/services/BehaviorMonitorService';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// Mock App
const mockApp = {} as any;

describe('BehaviorMonitorService', () => {
    let service: BehaviorMonitorService;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        service = new BehaviorMonitorService(mockApp);
    });

    afterEach(() => {
        service.stop();
        jest.useRealTimers();
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.enabled).toBe(true);
            expect(settings.intervalHours).toBe(6);
            expect(settings.weaknessClusterThreshold).toBe(3);
            expect(settings.daysWithoutReviewThreshold).toBe(3);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new BehaviorMonitorService(mockApp, {
                intervalHours: 12,
                weaknessClusterThreshold: 5,
            });

            const settings = customService.getSettings();
            expect(settings.intervalHours).toBe(12);
            expect(settings.weaknessClusterThreshold).toBe(5);
            expect(settings.enabled).toBe(true); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ intervalHours: 4 });
            const settings = service.getSettings();
            expect(settings.intervalHours).toBe(4);
            expect(settings.enabled).toBe(true); // Unchanged
        });

        it('should stop monitoring when disabled via settings', () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });
            service.start();
            expect(service.getStatus().isRunning).toBe(true);

            service.updateSettings({ enabled: false });
            expect(service.getStatus().isRunning).toBe(false);
        });

        it('should restart monitoring when interval changes', () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });
            service.start();
            const originalNextCheck = service.getStatus().nextCheck;

            service.updateSettings({ intervalHours: 12 });

            expect(service.getStatus().isRunning).toBe(true);
            expect(service.getStatus().intervalHours).toBe(12);
        });
    });

    describe('Scheduler Control', () => {
        it('should start monitoring', () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            service.start();

            expect(service.getStatus().isRunning).toBe(true);
            expect(service.getStatus().nextCheck).not.toBeNull();
        });

        it('should not start when disabled', () => {
            service.updateSettings({ enabled: false });
            service.start();

            expect(service.getStatus().isRunning).toBe(false);
        });

        it('should not start twice', () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            service.start();
            service.start(); // Should be ignored

            expect(service.getStatus().isRunning).toBe(true);
        });

        it('should stop monitoring', () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            service.start();
            expect(service.getStatus().isRunning).toBe(true);

            service.stop();
            expect(service.getStatus().isRunning).toBe(false);
            expect(service.getStatus().nextCheck).toBeNull();
        });

        it('should run initial check on start', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            service.start();

            // Advance time to trigger initial check (setTimeout with 0 delay)
            // Don't use runAllTimersAsync with setInterval - causes infinite loop
            jest.advanceTimersByTime(100);
            await Promise.resolve(); // Flush promises

            expect(mockRequestUrl).toHaveBeenCalled();
        });

        it('should run periodic checks', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            service.updateSettings({ intervalHours: 1 }); // 1 hour for testing
            service.start();

            // Advance time to trigger initial check
            jest.advanceTimersByTime(100);
            await Promise.resolve();
            const initialCalls = mockRequestUrl.mock.calls.length;

            // Advance by 1 hour to trigger periodic check
            jest.advanceTimersByTime(60 * 60 * 1000);
            await Promise.resolve();

            expect(mockRequestUrl.mock.calls.length).toBeGreaterThan(initialCalls);
        });
    });

    describe('Weakness Cluster Detection', () => {
        const mockClusters: any[] = [
            {
                cluster_id: 'cluster1',
                community_name: '线性代数基础',
                canvas_name: 'math.canvas',
                red_nodes: [
                    { node_id: 'n1', concept_name: '矩阵乘法', days_since_review: 5, memory_strength: 0.3, related_concepts: [] },
                    { node_id: 'n2', concept_name: '行列式', days_since_review: 7, memory_strength: 0.2, related_concepts: [] },
                    { node_id: 'n3', concept_name: '特征值', days_since_review: 10, memory_strength: 0.1, related_concepts: [] },
                ],
                total_nodes: 10,
                weakness_ratio: 0.3,
                recommendation: '建议系统复习线性代数',
            },
        ];

        it('should detect weakness clusters', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({ status: 200, json: { clusters: mockClusters } });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            const result = await service.triggerManualCheck();

            expect(result.success).toBe(true);
            expect(result.weaknessClusters).toHaveLength(1);
            expect(result.weaknessClusters[0].communityName).toBe('线性代数基础');
            expect(result.weaknessClusters[0].redNodes).toHaveLength(3);
        });

        it('should filter clusters below threshold', async () => {
            const smallCluster = {
                ...mockClusters[0],
                red_nodes: mockClusters[0].red_nodes.slice(0, 2), // Only 2 red nodes
            };

            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({ status: 200, json: { clusters: [smallCluster] } });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            const result = await service.triggerManualCheck();

            // Default threshold is 3, so cluster with 2 red nodes should be filtered
            expect(result.weaknessClusters).toHaveLength(0);
        });

        it('should handle API errors gracefully', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.reject(new Error('API unavailable'));
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            const result = await service.triggerManualCheck();

            // Should not throw, return empty clusters
            expect(result.success).toBe(true);
            expect(result.weaknessClusters).toHaveLength(0);
        });
    });

    describe('Stale Review Detection', () => {
        const mockStaleConcepts: any[] = [
            {
                concept_name: '逆否命题',
                node_id: 'n1',
                canvas_name: 'logic.canvas',
                days_since_review: 5,
                last_review_date: '2025-01-10T00:00:00Z',
                estimated_retention: 0.4,
                review_priority: 75,
            },
            {
                concept_name: '充分条件',
                node_id: 'n2',
                canvas_name: 'logic.canvas',
                days_since_review: 4,
                last_review_date: '2025-01-11T00:00:00Z',
                estimated_retention: 0.5,
                review_priority: 60,
            },
        ];

        it('should detect stale review concepts', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/stale-reviews')) {
                    return Promise.resolve({ status: 200, json: { stale_concepts: mockStaleConcepts } });
                }
                return Promise.resolve({ status: 200, json: { clusters: [] } });
            });

            const result = await service.triggerManualCheck();

            expect(result.success).toBe(true);
            expect(result.staleReviewConcepts).toHaveLength(2);
            expect(result.staleReviewConcepts[0].conceptName).toBe('逆否命题');
        });

        it('should include days threshold in API call', async () => {
            service.updateSettings({ daysWithoutReviewThreshold: 7 });

            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            await service.triggerManualCheck();

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('days=7'),
                })
            );
        });

        it('should handle API errors gracefully', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/stale-reviews')) {
                    return Promise.reject(new Error('API unavailable'));
                }
                return Promise.resolve({ status: 200, json: { clusters: [] } });
            });

            const result = await service.triggerManualCheck();

            expect(result.success).toBe(true);
            expect(result.staleReviewConcepts).toHaveLength(0);
        });
    });

    describe('Recommendation Generation', () => {
        const mockClusterData = {
            cluster_id: 'c1',
            community_name: '微积分',
            canvas_name: 'calc.canvas',
            red_nodes: [
                { node_id: 'n1', concept_name: '极限', days_since_review: 5, memory_strength: 0.3, related_concepts: [] },
                { node_id: 'n2', concept_name: '导数', days_since_review: 7, memory_strength: 0.2, related_concepts: [] },
                { node_id: 'n3', concept_name: '积分', days_since_review: 10, memory_strength: 0.1, related_concepts: [] },
            ],
            total_nodes: 10,
            weakness_ratio: 0.3,
        };

        it('should generate recommendations from weakness clusters', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({ status: 200, json: { clusters: [mockClusterData] } });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            await service.triggerManualCheck();

            const recommendations = service.getRecommendations();
            expect(recommendations.length).toBeGreaterThan(0);

            const clusterRec = recommendations.find(r => r.type === 'weakness_cluster');
            expect(clusterRec).toBeDefined();
            expect(clusterRec?.title).toContain('微积分');
            expect(clusterRec?.concepts).toContain('极限');
        });

        it('should generate urgent recommendations for very stale concepts', async () => {
            const veryStale = [
                { concept_name: 'A', node_id: 'n1', canvas_name: 'test.canvas', days_since_review: 10, estimated_retention: 0.1, review_priority: 90 },
                { concept_name: 'B', node_id: 'n2', canvas_name: 'test.canvas', days_since_review: 12, estimated_retention: 0.05, review_priority: 95 },
            ];

            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/stale-reviews')) {
                    return Promise.resolve({ status: 200, json: { stale_concepts: veryStale } });
                }
                return Promise.resolve({ status: 200, json: { clusters: [] } });
            });

            // Default threshold is 3 days, so 10+ days is very stale (>= 2x threshold)
            await service.triggerManualCheck();

            const recommendations = service.getRecommendations();
            const urgentRec = recommendations.find(r => r.type === 'stale_review' && r.priority >= 8);
            expect(urgentRec).toBeDefined();
            expect(urgentRec?.title).toContain('紧急');
        });

        it('should group stale concepts by canvas', async () => {
            const staleConcepts = [
                { concept_name: 'A', node_id: 'n1', canvas_name: 'canvas1.canvas', days_since_review: 4 },
                { concept_name: 'B', node_id: 'n2', canvas_name: 'canvas1.canvas', days_since_review: 4 },
                { concept_name: 'C', node_id: 'n3', canvas_name: 'canvas2.canvas', days_since_review: 4 },
                { concept_name: 'D', node_id: 'n4', canvas_name: 'canvas2.canvas', days_since_review: 4 },
            ];

            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/stale-reviews')) {
                    return Promise.resolve({ status: 200, json: { stale_concepts: staleConcepts } });
                }
                return Promise.resolve({ status: 200, json: { clusters: [] } });
            });

            await service.triggerManualCheck();

            const recommendations = service.getRecommendations();
            const canvasRecs = recommendations.filter(r => r.type === 'stale_review');

            // Should have grouped recommendations by canvas
            expect(canvasRecs.some(r => r.canvasName === 'canvas1.canvas')).toBe(true);
            expect(canvasRecs.some(r => r.canvasName === 'canvas2.canvas')).toBe(true);
        });

        it('should sort recommendations by priority', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            clusters: [
                                { ...mockClusterData, cluster_id: 'c1' },
                                { ...mockClusterData, cluster_id: 'c2', red_nodes: [...mockClusterData.red_nodes, { node_id: 'n4', concept_name: 'X' }] },
                            ],
                        },
                    });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            await service.triggerManualCheck();

            const recommendations = service.getRecommendations();
            expect(recommendations.length).toBeGreaterThan(1);

            // Should be sorted by priority descending
            for (let i = 1; i < recommendations.length; i++) {
                expect(recommendations[i - 1].priority).toBeGreaterThanOrEqual(recommendations[i].priority);
            }
        });

        it('should call recommendation callback', async () => {
            const callback = jest.fn();
            service.setRecommendationCallback(callback);

            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({ status: 200, json: { clusters: [mockClusterData] } });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            await service.triggerManualCheck();

            expect(callback).toHaveBeenCalled();
            expect(callback).toHaveBeenCalledWith(expect.any(Array));
        });
    });

    describe('Recommendations Access', () => {
        beforeEach(async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/weakness-clusters')) {
                    return Promise.resolve({
                        status: 200,
                        json: {
                            clusters: [{
                                cluster_id: 'c1',
                                community_name: 'Test',
                                canvas_name: 'test.canvas',
                                red_nodes: [
                                    { node_id: 'n1', concept_name: 'A' },
                                    { node_id: 'n2', concept_name: 'B' },
                                    { node_id: 'n3', concept_name: 'C' },
                                ],
                                total_nodes: 5,
                                weakness_ratio: 0.6,
                            }],
                        },
                    });
                }
                return Promise.resolve({ status: 200, json: { stale_concepts: [] } });
            });

            await service.triggerManualCheck();
        });

        it('should get all recommendations', () => {
            const all = service.getRecommendations();
            expect(all.length).toBeGreaterThan(0);
        });

        it('should get recommendations by type', () => {
            const clusterRecs = service.getRecommendationsByType('weakness_cluster');
            expect(clusterRecs.every(r => r.type === 'weakness_cluster')).toBe(true);
        });

        it('should get high priority recommendations', () => {
            const highPriority = service.getHighPriorityRecommendations();
            expect(highPriority.every(r => r.priority >= 7)).toBe(true);
        });

        it('should clear specific recommendation', () => {
            const all = service.getRecommendations();
            const firstId = all[0].id;

            service.clearRecommendation(firstId);

            expect(service.getRecommendations().find(r => r.id === firstId)).toBeUndefined();
        });

        it('should clear all recommendations', () => {
            expect(service.getRecommendations().length).toBeGreaterThan(0);

            service.clearAllRecommendations();

            expect(service.getRecommendations()).toHaveLength(0);
        });
    });

    describe('Status and Statistics', () => {
        it('should track check counts', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            await service.triggerManualCheck();
            await service.triggerManualCheck();

            expect(service.getStatus().totalChecks).toBe(2);
            expect(service.getStatus().successfulChecks).toBe(2);
        });

        it('should track failed checks', async () => {
            mockRequestUrl.mockRejectedValue(new Error('API Error'));

            await service.triggerManualCheck();

            expect(service.getStatus().totalChecks).toBe(1);
            expect(service.getStatus().failedChecks).toBe(1);
            expect(service.getStatus().successfulChecks).toBe(0);
        });

        it('should record last check time', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            const beforeCheck = new Date();
            await service.triggerManualCheck();
            const afterCheck = new Date();

            const lastCheck = service.getStatus().lastCheck;
            expect(lastCheck).not.toBeNull();
            expect(lastCheck!.getTime()).toBeGreaterThanOrEqual(beforeCheck.getTime());
            expect(lastCheck!.getTime()).toBeLessThanOrEqual(afterCheck.getTime());
        });

        it('should get statistics', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            await service.triggerManualCheck();

            const stats = service.getStatistics();
            expect(stats.totalChecks).toBe(1);
            expect(stats.successRate).toBe(100);
            expect(stats.lastCheckTime).not.toBeNull();
        });

        it('should get last result', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: { clusters: [], stale_concepts: [] } });

            await service.triggerManualCheck();

            const result = service.getLastResult();
            expect(result).not.toBeNull();
            expect(result?.success).toBe(true);
            expect(result?.durationMs).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Error Handling (Non-Blocking)', () => {
        it('should not throw on API errors', async () => {
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            // Should not throw
            const result = await service.triggerManualCheck();

            expect(result.success).toBe(false);
            expect(result.error).toBe('Network error');
        });

        it('should handle non-200 status codes', async () => {
            mockRequestUrl.mockResolvedValue({ status: 500, json: {} });

            const result = await service.triggerManualCheck();

            // Should succeed but with empty results
            expect(result.success).toBe(true);
            expect(result.weaknessClusters).toHaveLength(0);
            expect(result.staleReviewConcepts).toHaveLength(0);
        });

        it('should handle malformed responses', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200, json: null });

            const result = await service.triggerManualCheck();

            // Should succeed with empty results
            expect(result.success).toBe(true);
        });

        it('should continue monitoring after errors', async () => {
            // First check: BOTH API calls fail (2 rejections)
            // Second check: BOTH API calls succeed (2 resolves)
            mockRequestUrl
                .mockRejectedValueOnce(new Error('First error'))
                .mockRejectedValueOnce(new Error('First error'))
                .mockResolvedValueOnce({ status: 200, json: { clusters: [], stale_concepts: [] } })
                .mockResolvedValueOnce({ status: 200, json: { clusters: [], stale_concepts: [] } });

            const result1 = await service.triggerManualCheck();
            expect(result1.success).toBe(false);

            const result2 = await service.triggerManualCheck();
            expect(result2.success).toBe(true);

            expect(service.getStatus().totalChecks).toBe(2);
        });
    });
});

describe('DEFAULT_BEHAVIOR_MONITOR_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_BEHAVIOR_MONITOR_SETTINGS.enabled).toBe(true);
        expect(DEFAULT_BEHAVIOR_MONITOR_SETTINGS.intervalHours).toBe(6);
        expect(DEFAULT_BEHAVIOR_MONITOR_SETTINGS.weaknessClusterThreshold).toBe(3);
        expect(DEFAULT_BEHAVIOR_MONITOR_SETTINGS.daysWithoutReviewThreshold).toBe(3);
        expect(DEFAULT_BEHAVIOR_MONITOR_SETTINGS.timeout).toBe(30000);
    });
});

describe('createBehaviorMonitorService', () => {
    it('should create service instance', () => {
        const service = createBehaviorMonitorService(mockApp);
        expect(service).toBeInstanceOf(BehaviorMonitorService);
    });

    it('should create service with custom settings', () => {
        const service = createBehaviorMonitorService(mockApp, {
            intervalHours: 12,
        });

        expect(service.getSettings().intervalHours).toBe(12);
    });
});
