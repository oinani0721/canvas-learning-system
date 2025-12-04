/**
 * @jest-environment jsdom
 */

// Mock canvas for Chart.js testing
import 'jest-canvas-mock';

/**
 * Visualization Components Unit Tests
 *
 * Story 19.5: Progress Visualization Components
 *
 * Tests for CircularProgress, ProgressTrendChart, ConceptMasteryChart,
 * LearningHeatmap, and export utilities.
 */

import {
    createCircularProgress,
    updateCircularProgress,
    getProgressColor,
    CircularProgressProps
} from '../../src/components/CircularProgress';

import {
    createProgressTrendChart,
    calculateTrend,
    getTrendIcon,
    formatDateLabel,
    ProgressDataPoint
} from '../../src/components/ProgressTrendChart';

import {
    createConceptMasteryChart,
    groupByStatus,
    calculateMasteryStats,
    ConceptMasteryData
} from '../../src/components/ConceptMasteryChart';

import {
    createLearningHeatmap,
    calculateActivityStats,
    HeatmapCell
} from '../../src/components/LearningHeatmap';

import {
    exportChartAsImage,
    downloadExportedChart,
    ExportOptions
} from '../../src/components/exportUtils';

// ============================================================
// CircularProgress Tests
// ============================================================

describe('CircularProgress', () => {
    describe('createCircularProgress', () => {
        it('should create a container element', () => {
            const progress = createCircularProgress({ percentage: 50 });
            expect(progress).toBeDefined();
            expect(progress.className).toBe('circular-progress-container');
        });

        it('should create SVG element with correct attributes', () => {
            const progress = createCircularProgress({ percentage: 75, size: 120 });
            const svg = progress.querySelector('svg');

            expect(svg).toBeDefined();
            expect(svg?.getAttribute('width')).toBe('120');
            expect(svg?.getAttribute('height')).toBe('120');
            expect(svg?.getAttribute('role')).toBe('progressbar');
        });

        it('should set aria-valuenow to percentage', () => {
            const progress = createCircularProgress({ percentage: 65 });
            const svg = progress.querySelector('svg');

            expect(svg?.getAttribute('aria-valuenow')).toBe('65');
        });

        it('should clamp percentage to 0-100 range', () => {
            const progressOver = createCircularProgress({ percentage: 150 });
            const progressUnder = createCircularProgress({ percentage: -20 });

            expect(progressOver.querySelector('svg')?.getAttribute('aria-valuenow')).toBe('100');
            expect(progressUnder.querySelector('svg')?.getAttribute('aria-valuenow')).toBe('0');
        });

        it('should show percentage text by default', () => {
            const progress = createCircularProgress({ percentage: 42 });
            const text = progress.querySelector('.progress-text');

            expect(text).toBeDefined();
            expect(text?.textContent).toBe('42%');
        });

        it('should hide percentage text when showText is false', () => {
            const progress = createCircularProgress({ percentage: 50, showText: false });
            const text = progress.querySelector('.progress-text');

            expect(text).toBeNull();
        });

        it('should add label when provided', () => {
            const progress = createCircularProgress({ percentage: 80, label: '通过率' });
            const label = progress.querySelector('.progress-label');

            expect(label).toBeDefined();
            expect(label?.textContent).toBe('通过率');
        });

        it('should use custom colors', () => {
            const progress = createCircularProgress({
                percentage: 50,
                color: '#FF0000',
                bgColor: '#CCCCCC'
            });

            const progressBar = progress.querySelector('.progress-bar');
            const bgCircle = progress.querySelector('.progress-bg');

            expect(progressBar?.getAttribute('stroke')).toBe('#FF0000');
            expect(bgCircle?.getAttribute('stroke')).toBe('#CCCCCC');
        });

        it('should apply animation when animated is true', () => {
            const progress = createCircularProgress({ percentage: 70, animated: true });
            const progressBar = progress.querySelector('.progress-bar') as HTMLElement;

            expect(progressBar?.style.transition).toContain('stroke-dashoffset');
        });
    });

    describe('updateCircularProgress', () => {
        it('should update percentage text', () => {
            const progress = createCircularProgress({ percentage: 30 });
            updateCircularProgress(progress, 80);

            const text = progress.querySelector('.progress-text');
            expect(text?.textContent).toBe('80%');
        });

        it('should update aria-valuenow', () => {
            const progress = createCircularProgress({ percentage: 30 });
            updateCircularProgress(progress, 90);

            const svg = progress.querySelector('svg');
            expect(svg?.getAttribute('aria-valuenow')).toBe('90');
        });
    });

    describe('getProgressColor', () => {
        it('should return green for 80+%', () => {
            expect(getProgressColor(80)).toBe('#4CAF50');
            expect(getProgressColor(100)).toBe('#4CAF50');
        });

        it('should return light green for 60-79%', () => {
            expect(getProgressColor(60)).toBe('#8BC34A');
            expect(getProgressColor(79)).toBe('#8BC34A');
        });

        it('should return yellow for 40-59%', () => {
            expect(getProgressColor(40)).toBe('#FFC107');
            expect(getProgressColor(59)).toBe('#FFC107');
        });

        it('should return orange for 20-39%', () => {
            expect(getProgressColor(20)).toBe('#FF9800');
            expect(getProgressColor(39)).toBe('#FF9800');
        });

        it('should return red for <20%', () => {
            expect(getProgressColor(0)).toBe('#F44336');
            expect(getProgressColor(19)).toBe('#F44336');
        });
    });
});

// ============================================================
// ProgressTrendChart Tests
// ============================================================

describe('ProgressTrendChart', () => {
    const sampleData: ProgressDataPoint[] = [
        { date: '2025-01-10', coverageRate: 45, totalConcepts: 20, passedCount: 9 },
        { date: '2025-01-11', coverageRate: 50, totalConcepts: 20, passedCount: 10 },
        { date: '2025-01-12', coverageRate: 60, totalConcepts: 20, passedCount: 12 },
        { date: '2025-01-13', coverageRate: 75, totalConcepts: 20, passedCount: 15 },
    ];

    describe('createProgressTrendChart', () => {
        it('should create a container element', () => {
            const { container } = createProgressTrendChart({ data: sampleData });
            expect(container).toBeDefined();
            expect(container.className).toBe('progress-trend-chart-container');
        });

        it('should create a canvas element', () => {
            const { container } = createProgressTrendChart({ data: sampleData });
            const canvas = container.querySelector('canvas');
            expect(canvas).toBeDefined();
        });

        it('should set custom dimensions', () => {
            const { container } = createProgressTrendChart({
                data: sampleData,
                width: 800,
                height: 400
            });

            expect(container.style.width).toBe('800px');
            expect(container.style.height).toBe('400px');
        });

        it('should provide update function', () => {
            const chart = createProgressTrendChart({ data: sampleData });
            expect(typeof chart.update).toBe('function');
        });

        it('should provide destroy function', () => {
            const chart = createProgressTrendChart({ data: sampleData });
            expect(typeof chart.destroy).toBe('function');
        });

        it('should provide toBase64Image function', () => {
            const chart = createProgressTrendChart({ data: sampleData });
            expect(typeof chart.toBase64Image).toBe('function');
        });
    });

    describe('calculateTrend', () => {
        it('should return "up" for increasing trend', () => {
            const data = [
                { date: '2025-01-01', coverageRate: 30, totalConcepts: 10, passedCount: 3 },
                { date: '2025-01-02', coverageRate: 50, totalConcepts: 10, passedCount: 5 },
            ];
            expect(calculateTrend(data)).toBe('up');
        });

        it('should return "down" for decreasing trend', () => {
            const data = [
                { date: '2025-01-01', coverageRate: 70, totalConcepts: 10, passedCount: 7 },
                { date: '2025-01-02', coverageRate: 50, totalConcepts: 10, passedCount: 5 },
            ];
            expect(calculateTrend(data)).toBe('down');
        });

        it('should return "stable" for minimal change', () => {
            const data = [
                { date: '2025-01-01', coverageRate: 50, totalConcepts: 10, passedCount: 5 },
                { date: '2025-01-02', coverageRate: 52, totalConcepts: 10, passedCount: 5 },
            ];
            expect(calculateTrend(data)).toBe('stable');
        });

        it('should return "stable" for single data point', () => {
            const data = [
                { date: '2025-01-01', coverageRate: 50, totalConcepts: 10, passedCount: 5 },
            ];
            expect(calculateTrend(data)).toBe('stable');
        });
    });

    describe('getTrendIcon', () => {
        it('should return correct icons', () => {
            expect(getTrendIcon('up')).toBe('📈');
            expect(getTrendIcon('down')).toBe('📉');
            expect(getTrendIcon('stable')).toBe('➡️');
        });
    });

    describe('formatDateLabel', () => {
        it('should format date correctly', () => {
            const formatted = formatDateLabel('2025-01-15');
            // Format depends on locale, just check it's not the original
            expect(formatted).toBeDefined();
            expect(formatted.length).toBeGreaterThan(0);
        });

        it('should return original string for invalid date', () => {
            expect(formatDateLabel('invalid')).toBe('invalid');
        });
    });
});

// ============================================================
// ConceptMasteryChart Tests
// ============================================================

describe('ConceptMasteryChart', () => {
    const sampleData: ConceptMasteryData[] = [
        { concept: '逆否命题', nodeId: 'n1', status: 'green', score: 95 },
        { concept: '充分条件', nodeId: 'n2', status: 'purple', score: 60 },
        { concept: '必要条件', nodeId: 'n3', status: 'red', score: 20 },
    ];

    describe('createConceptMasteryChart', () => {
        it('should create a container element', () => {
            const { container } = createConceptMasteryChart({ data: sampleData });
            expect(container).toBeDefined();
            expect(container.className).toBe('concept-mastery-chart-container');
        });

        it('should create a canvas element', () => {
            const { container } = createConceptMasteryChart({ data: sampleData });
            const canvas = container.querySelector('canvas');
            expect(canvas).toBeDefined();
        });

        it('should support horizontal orientation', () => {
            const { container } = createConceptMasteryChart({
                data: sampleData,
                orientation: 'horizontal'
            });
            expect(container).toBeDefined();
        });

        it('should support vertical orientation', () => {
            const { container } = createConceptMasteryChart({
                data: sampleData,
                orientation: 'vertical'
            });
            expect(container).toBeDefined();
        });
    });

    describe('groupByStatus', () => {
        it('should group concepts by status', () => {
            const grouped = groupByStatus(sampleData);

            expect(grouped['green']?.length).toBe(1);
            expect(grouped['purple']?.length).toBe(1);
            expect(grouped['red']?.length).toBe(1);
        });

        it('should handle empty array', () => {
            const grouped = groupByStatus([]);
            expect(Object.keys(grouped).length).toBe(0);
        });
    });

    describe('calculateMasteryStats', () => {
        it('should calculate correct statistics', () => {
            const stats = calculateMasteryStats(sampleData);

            expect(stats.total).toBe(3);
            expect(stats.mastered).toBe(1);
            expect(stats.inProgress).toBe(1);
            expect(stats.notStarted).toBe(1);
            expect(stats.masteryRate).toBeCloseTo(33.33, 1);
        });

        it('should handle empty array', () => {
            const stats = calculateMasteryStats([]);

            expect(stats.total).toBe(0);
            expect(stats.mastered).toBe(0);
            expect(stats.masteryRate).toBe(0);
        });

        it('should handle all green concepts', () => {
            const allGreen: ConceptMasteryData[] = [
                { concept: 'A', nodeId: '1', status: 'green' },
                { concept: 'B', nodeId: '2', status: 'green' },
            ];
            const stats = calculateMasteryStats(allGreen);

            expect(stats.masteryRate).toBe(100);
        });
    });
});

// ============================================================
// LearningHeatmap Tests
// ============================================================

describe('LearningHeatmap', () => {
    const sampleData: HeatmapCell[] = [
        { date: '2025-01-10', value: 5 },
        { date: '2025-01-11', value: 2 },
        { date: '2025-01-12', value: 0 },
        { date: '2025-01-13', value: 8 },
        { date: '2025-01-14', value: 3 },
    ];

    describe('createLearningHeatmap', () => {
        it('should create a container element', () => {
            const { container } = createLearningHeatmap({ data: sampleData });
            expect(container).toBeDefined();
            expect(container.className).toBe('learning-heatmap-container');
        });

        it('should create an SVG element', () => {
            const { container } = createLearningHeatmap({ data: sampleData });
            const svg = container.querySelector('svg');
            expect(svg).toBeDefined();
        });

        it('should create a legend', () => {
            const { container } = createLearningHeatmap({ data: sampleData });
            const legend = container.querySelector('.heatmap-legend');
            expect(legend).toBeDefined();
        });

        it('should support different color schemes', () => {
            const greenHeatmap = createLearningHeatmap({ data: sampleData, colorScheme: 'green' });
            const blueHeatmap = createLearningHeatmap({ data: sampleData, colorScheme: 'blue' });
            const purpleHeatmap = createLearningHeatmap({ data: sampleData, colorScheme: 'purple' });

            expect(greenHeatmap.container).toBeDefined();
            expect(blueHeatmap.container).toBeDefined();
            expect(purpleHeatmap.container).toBeDefined();
        });

        it('should provide update function', () => {
            const heatmap = createLearningHeatmap({ data: sampleData });
            expect(typeof heatmap.update).toBe('function');
        });

        it('should provide toDataUrl function', () => {
            const heatmap = createLearningHeatmap({ data: sampleData });
            expect(typeof heatmap.toDataUrl).toBe('function');
        });
    });

    describe('calculateActivityStats', () => {
        it('should calculate total days and active days', () => {
            const stats = calculateActivityStats(sampleData);

            expect(stats.totalDays).toBe(5);
            expect(stats.activeDays).toBe(4); // One day has value 0
        });

        it('should calculate total activities', () => {
            const stats = calculateActivityStats(sampleData);
            expect(stats.totalActivities).toBe(18); // 5+2+0+8+3
        });

        it('should calculate average per day', () => {
            const stats = calculateActivityStats(sampleData);
            expect(stats.averagePerDay).toBeCloseTo(4.5, 1); // 18/4
        });

        it('should handle empty array', () => {
            const stats = calculateActivityStats([]);

            expect(stats.totalDays).toBe(0);
            expect(stats.activeDays).toBe(0);
            expect(stats.totalActivities).toBe(0);
            expect(stats.averagePerDay).toBe(0);
        });

        it('should calculate streak correctly', () => {
            const consecutiveData: HeatmapCell[] = [
                { date: '2025-01-10', value: 1 },
                { date: '2025-01-11', value: 2 },
                { date: '2025-01-12', value: 1 },
                { date: '2025-01-14', value: 3 }, // Gap
            ];
            const stats = calculateActivityStats(consecutiveData);

            expect(stats.maxStreak).toBe(3); // First 3 days
        });
    });
});

// ============================================================
// Export Utilities Tests
// ============================================================

describe('exportUtils', () => {
    describe('exportChartAsImage', () => {
        it('should export chart with toBase64Image method', async () => {
            const mockChart = {
                toBase64Image: jest.fn().mockReturnValue('data:image/png;base64,mockdata')
            };

            const result = await exportChartAsImage(mockChart, {
                format: 'png',
                fileName: 'test-chart'
            });

            expect(result.dataUrl).toBe('data:image/png;base64,mockdata');
            expect(result.format).toBe('png');
            expect(result.fileName).toBe('test-chart.png');
        });

        it('should handle JPEG format', async () => {
            const mockChart = {
                toBase64Image: jest.fn().mockReturnValue('data:image/jpeg;base64,mockdata')
            };

            const result = await exportChartAsImage(mockChart, { format: 'jpeg' });

            expect(result.format).toBe('jpeg');
            expect(mockChart.toBase64Image).toHaveBeenCalledWith('image/jpeg', 1.0);
        });
    });

    describe('downloadExportedChart', () => {
        it('should create and click a download link', () => {
            const mockResult = {
                dataUrl: 'data:image/png;base64,test',
                format: 'png',
                fileName: 'test.png'
            };

            // Mock DOM methods
            const mockLink = {
                href: '',
                download: '',
                click: jest.fn()
            };
            const createElementSpy = jest.spyOn(document, 'createElement')
                .mockReturnValue(mockLink as unknown as HTMLElement);
            const appendChildSpy = jest.spyOn(document.body, 'appendChild')
                .mockImplementation(() => mockLink as unknown as HTMLElement);
            const removeChildSpy = jest.spyOn(document.body, 'removeChild')
                .mockImplementation(() => mockLink as unknown as HTMLElement);

            downloadExportedChart(mockResult);

            expect(mockLink.href).toBe(mockResult.dataUrl);
            expect(mockLink.download).toBe(mockResult.fileName);
            expect(mockLink.click).toHaveBeenCalled();

            createElementSpy.mockRestore();
            appendChildSpy.mockRestore();
            removeChildSpy.mockRestore();
        });
    });
});

// ============================================================
// Integration Tests
// ============================================================

describe('Visualization Integration', () => {
    it('should allow chaining circular progress with trend chart', () => {
        const circularProgress = createCircularProgress({ percentage: 75, label: '当前' });
        const trendChart = createProgressTrendChart({
            data: [
                { date: '2025-01-10', coverageRate: 50, totalConcepts: 10, passedCount: 5 },
                { date: '2025-01-11', coverageRate: 75, totalConcepts: 10, passedCount: 8 },
            ]
        });

        const dashboard = document.createElement('div');
        dashboard.appendChild(circularProgress);
        dashboard.appendChild(trendChart.container);

        expect(dashboard.children.length).toBe(2);
    });

    it('should update all visualizations with new data', () => {
        const circularProgress = createCircularProgress({ percentage: 50 });
        const masteryChart = createConceptMasteryChart({
            data: [{ concept: 'Test', nodeId: '1', status: 'purple' }]
        });

        // Update circular progress
        updateCircularProgress(circularProgress, 80);

        // Update mastery chart
        masteryChart.update([
            { concept: 'Test', nodeId: '1', status: 'green', score: 90 }
        ]);

        const progressText = circularProgress.querySelector('.progress-text');
        expect(progressText?.textContent).toBe('80%');
    });
});
