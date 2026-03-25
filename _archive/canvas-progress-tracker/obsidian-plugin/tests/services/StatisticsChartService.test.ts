/**
 * StatisticsChartService Tests - Canvas Learning System
 *
 * Tests for Story 14.8: 复习统计图表
 *
 * @module StatisticsChartService.test
 * @version 1.0.0
 */

import {
    StatisticsChartService,
    ChartTheme,
    DailyStatPoint,
    MasteryDistribution,
    ReviewTrend,
    LIGHT_THEME,
    DARK_THEME,
    aggregateDailyStats,
    calculateMasteryDistribution,
    buildReviewTrend,
    createStatisticsChartService,
} from '../../src/services/StatisticsChartService';

// Mock Chart.js
jest.mock('chart.js', () => {
    const mockChart = jest.fn().mockImplementation(() => ({
        destroy: jest.fn(),
        update: jest.fn(),
        data: {
            labels: [],
            datasets: [],
        },
        options: {
            scales: {},
            plugins: { legend: { labels: {} } },
        },
    }));

    // Add static register method
    mockChart.register = jest.fn();

    return {
        Chart: mockChart,
        CategoryScale: jest.fn(),
        LinearScale: jest.fn(),
        BarController: jest.fn(),
        BarElement: jest.fn(),
        LineController: jest.fn(),
        LineElement: jest.fn(),
        PointElement: jest.fn(),
        ArcElement: jest.fn(),
        PieController: jest.fn(),
        DoughnutController: jest.fn(),
        Title: jest.fn(),
        Tooltip: jest.fn(),
        Legend: jest.fn(),
        Filler: jest.fn(),
        registerables: [],
    };
});

// Mock Obsidian-style HTMLElement with createDiv, createEl, empty methods
const createMockObsidianContainer = () => {
    const mockCanvas = {
        getContext: jest.fn().mockReturnValue({
            fillRect: jest.fn(),
            clearRect: jest.fn(),
        }),
        width: 400,
        height: 300,
    };

    const mockWrapper = {
        style: { position: '', width: '', height: '' },
        createEl: jest.fn().mockReturnValue(mockCanvas),
    };

    return {
        empty: jest.fn(),
        createDiv: jest.fn().mockReturnValue(mockWrapper),
        createEl: jest.fn(),
        innerHTML: '',
        style: {},
    } as any;
};

describe('StatisticsChartService', () => {
    let service: StatisticsChartService;

    beforeEach(() => {
        service = new StatisticsChartService();
        jest.clearAllMocks();
    });

    afterEach(() => {
        service.destroyAllCharts();
    });

    describe('Constructor and Initialization', () => {
        it('should create service with default light theme', () => {
            expect(service).toBeDefined();
            expect(service.getTheme()).toEqual(LIGHT_THEME);
        });

        it('should create service with dark theme', () => {
            const darkService = new StatisticsChartService(true);
            expect(darkService).toBeDefined();
            expect(darkService.getTheme()).toEqual(DARK_THEME);
        });
    });

    describe('Theme Management', () => {
        it('should switch to dark mode', () => {
            service.setDarkMode(true);
            expect(service.getTheme()).toEqual(DARK_THEME);
        });

        it('should switch to light mode', () => {
            const darkService = new StatisticsChartService(true);
            darkService.setDarkMode(false);
            expect(darkService.getTheme()).toEqual(LIGHT_THEME);
        });

        it('should toggle theme multiple times', () => {
            service.setDarkMode(true);
            expect(service.getTheme()).toEqual(DARK_THEME);
            service.setDarkMode(false);
            expect(service.getTheme()).toEqual(LIGHT_THEME);
            service.setDarkMode(true);
            expect(service.getTheme()).toEqual(DARK_THEME);
        });
    });

    describe('Chart Creation', () => {
        it('should create daily review chart with valid data', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
                { date: '01/02', reviewCount: 3, averageScore: 85, duration: 20 },
            ];

            const chart = service.createDailyReviewChart(container, data, 'daily-chart');
            expect(chart).toBeDefined();
            expect(container.empty).toHaveBeenCalled();
            expect(container.createDiv).toHaveBeenCalledWith({ cls: 'chart-wrapper' });
        });

        it('should create score trend chart', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
            ];

            const chart = service.createScoreTrendChart(container, data, 'score-chart');
            expect(chart).toBeDefined();
        });

        it('should create mastery chart', () => {
            const container = createMockObsidianContainer();
            const data: MasteryDistribution = {
                mastered: 10,
                learning: 5,
                struggling: 2,
            };

            const chart = service.createMasteryChart(container, data, 'mastery-chart');
            expect(chart).toBeDefined();
        });

        it('should return null for empty mastery data', () => {
            const container = createMockObsidianContainer();
            const data: MasteryDistribution = {
                mastered: 0,
                learning: 0,
                struggling: 0,
            };

            const chart = service.createMasteryChart(container, data, 'empty-mastery');
            expect(chart).toBeNull();
        });

        it('should create combined trend chart', () => {
            const container = createMockObsidianContainer();
            const data: ReviewTrend = {
                labels: ['01/01', '01/02'],
                reviewCounts: [5, 3],
                averageScores: [80, 85],
                retentionRates: [0.8, 0.85],
            };

            const chart = service.createCombinedTrendChart(container, data, 'combined-chart');
            expect(chart).toBeDefined();
        });

        it('should create weekly summary chart', () => {
            const container = createMockObsidianContainer();
            const data = [
                { week: 'Week 1', count: 5, score: 80 },
                { week: 'Week 2', count: 3, score: 85 },
            ];

            const chart = service.createWeeklySummaryChart(container, data, 'weekly-chart');
            expect(chart).toBeDefined();
        });
    });

    describe('Chart Lifecycle', () => {
        it('should destroy existing chart before creating new one with same ID', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
            ];

            service.createDailyReviewChart(container, data, 'same-id');
            service.createDailyReviewChart(container, data, 'same-id');
            // Should not throw
            expect(service).toBeDefined();
        });

        it('should destroy specific chart', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
            ];

            service.createDailyReviewChart(container, data, 'to-destroy');
            service.destroyChart('to-destroy');
            // Should not throw
            expect(service).toBeDefined();
        });

        it('should handle destroying non-existent chart gracefully', () => {
            service.destroyChart('non-existent');
            // Should not throw
            expect(service).toBeDefined();
        });

        it('should destroy all charts', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
            ];

            service.createDailyReviewChart(container, data, 'chart1');
            service.createDailyReviewChart(container, data, 'chart2');
            service.destroyAllCharts();
            // Should not throw
            expect(service).toBeDefined();
        });
    });

    describe('Chart Data Update', () => {
        it('should update chart data', () => {
            const container = createMockObsidianContainer();
            const data: DailyStatPoint[] = [
                { date: '01/01', reviewCount: 5, averageScore: 80, duration: 30 },
            ];

            service.createDailyReviewChart(container, data, 'update-chart');
            service.updateChartData('update-chart', { labels: ['new'], datasets: [] });
            // Should not throw
            expect(service).toBeDefined();
        });

        it('should handle updating non-existent chart gracefully', () => {
            service.updateChartData('non-existent', { labels: [], datasets: [] });
            // Should not throw
            expect(service).toBeDefined();
        });
    });
});

describe('Theme Constants', () => {
    describe('LIGHT_THEME', () => {
        it('should have all required properties', () => {
            expect(LIGHT_THEME.primary).toBeDefined();
            expect(LIGHT_THEME.secondary).toBeDefined();
            expect(LIGHT_THEME.success).toBeDefined();
            expect(LIGHT_THEME.warning).toBeDefined();
            expect(LIGHT_THEME.danger).toBeDefined();
            expect(LIGHT_THEME.text).toBeDefined();
            expect(LIGHT_THEME.grid).toBeDefined();
            expect(LIGHT_THEME.background).toBeDefined();
        });

        it('should have valid hex color values', () => {
            expect(LIGHT_THEME.primary).toMatch(/^#[0-9A-Fa-f]{6}$/);
            expect(LIGHT_THEME.success).toMatch(/^#[0-9A-Fa-f]{6}$/);
            expect(LIGHT_THEME.warning).toMatch(/^#[0-9A-Fa-f]{6}$/);
        });
    });

    describe('DARK_THEME', () => {
        it('should have all required properties', () => {
            expect(DARK_THEME.primary).toBeDefined();
            expect(DARK_THEME.secondary).toBeDefined();
            expect(DARK_THEME.success).toBeDefined();
            expect(DARK_THEME.warning).toBeDefined();
            expect(DARK_THEME.danger).toBeDefined();
            expect(DARK_THEME.text).toBeDefined();
            expect(DARK_THEME.grid).toBeDefined();
            expect(DARK_THEME.background).toBeDefined();
        });

        it('should have different values from light theme', () => {
            expect(DARK_THEME.text).not.toBe(LIGHT_THEME.text);
            expect(DARK_THEME.background).not.toBe(LIGHT_THEME.background);
        });
    });
});

describe('Helper Functions', () => {
    describe('aggregateDailyStats', () => {
        it('should return array with correct length for empty records', () => {
            const result = aggregateDailyStats([], 7);
            expect(result).toHaveLength(7);
            result.forEach((stat) => {
                expect(stat.reviewCount).toBe(0);
                expect(stat.averageScore).toBe(0);
                expect(stat.duration).toBe(0);
            });
        });

        it('should aggregate records by date', () => {
            const today = new Date();
            today.setHours(12, 0, 0, 0); // Middle of day

            const records = [
                {
                    reviewDate: today,
                    reviewScore: 80,
                    reviewDuration: 30,
                    memoryStrength: 0.8,
                    conceptName: 'Test1',
                },
                {
                    reviewDate: today,
                    reviewScore: 90,
                    reviewDuration: 20,
                    memoryStrength: 0.9,
                    conceptName: 'Test2',
                },
            ];

            const result = aggregateDailyStats(records as any, 7);
            expect(result).toHaveLength(7);

            // Last entry should be today with aggregated data
            const lastEntry = result[result.length - 1];
            expect(lastEntry.reviewCount).toBe(2);
            expect(lastEntry.averageScore).toBe(85);
            expect(lastEntry.duration).toBe(50);
        });

        it('should handle records with missing scores', () => {
            const today = new Date();
            const records = [
                {
                    reviewDate: today,
                    reviewScore: undefined,
                    reviewDuration: 30,
                    memoryStrength: 0.8,
                    conceptName: 'Test',
                },
            ];

            const result = aggregateDailyStats(records as any, 7);
            const lastEntry = result[result.length - 1];
            expect(lastEntry.averageScore).toBe(0);
        });

        it('should respect days parameter', () => {
            const result = aggregateDailyStats([], 14);
            expect(result).toHaveLength(14);
        });

        it('should format dates as MM/DD', () => {
            const result = aggregateDailyStats([], 7);
            result.forEach((stat) => {
                expect(stat.date).toMatch(/^\d{2}\/\d{2}$/);
            });
        });
    });

    describe('calculateMasteryDistribution', () => {
        it('should return zeros for empty records', () => {
            const result = calculateMasteryDistribution([]);
            expect(result.mastered).toBe(0);
            expect(result.learning).toBe(0);
            expect(result.struggling).toBe(0);
        });

        it('should classify mastered concepts correctly (memoryStrength >= 0.8)', () => {
            const records = [
                { memoryStrength: 0.9, conceptName: 'A', reviewDate: new Date() },
                { memoryStrength: 0.85, conceptName: 'B', reviewDate: new Date() },
                { memoryStrength: 0.8, conceptName: 'C', reviewDate: new Date() },
            ];

            const result = calculateMasteryDistribution(records as any);
            expect(result.mastered).toBe(3);
            expect(result.learning).toBe(0);
            expect(result.struggling).toBe(0);
        });

        it('should classify learning concepts correctly (0.5 <= memoryStrength < 0.8)', () => {
            const records = [
                { memoryStrength: 0.6, conceptName: 'A', reviewDate: new Date() },
                { memoryStrength: 0.5, conceptName: 'B', reviewDate: new Date() },
                { memoryStrength: 0.7, conceptName: 'C', reviewDate: new Date() },
            ];

            const result = calculateMasteryDistribution(records as any);
            expect(result.mastered).toBe(0);
            expect(result.learning).toBe(3);
            expect(result.struggling).toBe(0);
        });

        it('should classify struggling concepts correctly (memoryStrength < 0.5)', () => {
            const records = [
                { memoryStrength: 0.3, conceptName: 'A', reviewDate: new Date() },
                { memoryStrength: 0.2, conceptName: 'B', reviewDate: new Date() },
                { memoryStrength: 0.4, conceptName: 'C', reviewDate: new Date() },
            ];

            const result = calculateMasteryDistribution(records as any);
            expect(result.mastered).toBe(0);
            expect(result.learning).toBe(0);
            expect(result.struggling).toBe(3);
        });

        it('should handle mixed distribution', () => {
            const records = [
                { memoryStrength: 0.9, conceptName: 'A', reviewDate: new Date() }, // mastered
                { memoryStrength: 0.6, conceptName: 'B', reviewDate: new Date() }, // learning
                { memoryStrength: 0.3, conceptName: 'C', reviewDate: new Date() }, // struggling
            ];

            const result = calculateMasteryDistribution(records as any);
            expect(result.mastered).toBe(1);
            expect(result.learning).toBe(1);
            expect(result.struggling).toBe(1);
        });

        it('should deduplicate by concept using latest record', () => {
            const earlier = new Date('2025-01-01');
            const later = new Date('2025-01-02');

            const records = [
                { memoryStrength: 0.3, conceptName: 'A', reviewDate: earlier }, // struggling (earlier)
                { memoryStrength: 0.9, conceptName: 'A', reviewDate: later }, // mastered (later - should win)
            ];

            const result = calculateMasteryDistribution(records as any);
            expect(result.mastered).toBe(1);
            expect(result.learning).toBe(0);
            expect(result.struggling).toBe(0);
        });
    });

    describe('buildReviewTrend', () => {
        it('should return empty arrays for empty stats', () => {
            const result = buildReviewTrend([]);
            expect(result.labels).toHaveLength(0);
            expect(result.reviewCounts).toHaveLength(0);
            expect(result.averageScores).toHaveLength(0);
            expect(result.retentionRates).toHaveLength(0);
        });

        it('should build trend from learning statistics', () => {
            const stats = [
                {
                    statDate: new Date('2025-01-01'),
                    dailyReviews: 5,
                    dailyAverageScore: 80,
                    averageRetentionRate: 0.8,
                },
                {
                    statDate: new Date('2025-01-02'),
                    dailyReviews: 3,
                    dailyAverageScore: 85,
                    averageRetentionRate: 0.85,
                },
            ];

            const result = buildReviewTrend(stats as any, 7);
            expect(result.labels).toHaveLength(2);
            expect(result.reviewCounts).toEqual([5, 3]);
            expect(result.averageScores).toEqual([80, 85]);
            expect(result.retentionRates).toEqual([0.8, 0.85]);
        });

        it('should sort stats by date', () => {
            const stats = [
                {
                    statDate: new Date('2025-01-02'),
                    dailyReviews: 3,
                    dailyAverageScore: 85,
                    averageRetentionRate: 0.85,
                },
                {
                    statDate: new Date('2025-01-01'),
                    dailyReviews: 5,
                    dailyAverageScore: 80,
                    averageRetentionRate: 0.8,
                },
            ];

            const result = buildReviewTrend(stats as any, 7);
            expect(result.reviewCounts).toEqual([5, 3]); // Should be sorted
        });

        it('should limit to specified days', () => {
            const stats = Array.from({ length: 10 }, (_, i) => ({
                statDate: new Date(`2025-01-${(i + 1).toString().padStart(2, '0')}`),
                dailyReviews: i + 1,
                dailyAverageScore: 70 + i,
                averageRetentionRate: 0.7 + i * 0.02,
            }));

            const result = buildReviewTrend(stats as any, 5);
            expect(result.labels).toHaveLength(5);
            expect(result.reviewCounts).toEqual([6, 7, 8, 9, 10]); // Last 5
        });

        it('should format dates as MM/DD', () => {
            // Use explicit local time to avoid UTC timezone conversion issues
            const testDate = new Date(2025, 0, 15, 12, 0, 0); // Jan 15, 2025, noon local time
            const stats = [
                {
                    statDate: testDate,
                    dailyReviews: 5,
                    dailyAverageScore: 80,
                    averageRetentionRate: 0.8,
                },
            ];

            const result = buildReviewTrend(stats as any, 7);
            // Verify format is MM/DD (matches the date we created)
            expect(result.labels[0]).toMatch(/^\d{2}\/\d{2}$/);
            expect(result.labels[0]).toBe('01/15');
        });

        it('should handle missing dailyAverageScore', () => {
            const stats = [
                {
                    statDate: new Date('2025-01-01'),
                    dailyReviews: 5,
                    dailyAverageScore: undefined,
                    averageRetentionRate: 0.8,
                },
            ];

            const result = buildReviewTrend(stats as any, 7);
            expect(result.averageScores[0]).toBe(0);
        });
    });
});

describe('createStatisticsChartService', () => {
    it('should create service with light mode', () => {
        const service = createStatisticsChartService(false);
        expect(service).toBeInstanceOf(StatisticsChartService);
        expect(service.getTheme()).toEqual(LIGHT_THEME);
    });

    it('should create service with dark mode', () => {
        const service = createStatisticsChartService(true);
        expect(service).toBeInstanceOf(StatisticsChartService);
        expect(service.getTheme()).toEqual(DARK_THEME);
    });
});
