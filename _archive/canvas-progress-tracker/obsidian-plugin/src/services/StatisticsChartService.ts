/**
 * Statistics Chart Service - Canvas Learning System
 *
 * Service for rendering review statistics charts using Chart.js.
 * Implements Story 14.8: 复习统计图表
 *
 * @module StatisticsChartService
 * @version 1.0.0
 */

import {
    Chart,
    CategoryScale,
    LinearScale,
    BarController,
    BarElement,
    LineController,
    LineElement,
    PointElement,
    ArcElement,
    PieController,
    DoughnutController,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import type { ChartConfiguration, ChartType } from 'chart.js';
import type { ReviewRecord, LearningStatistics } from '../types/DataTypes';

// Register Chart.js components
Chart.register(
    CategoryScale,
    LinearScale,
    BarController,
    BarElement,
    LineController,
    LineElement,
    PointElement,
    ArcElement,
    PieController,
    DoughnutController,
    Title,
    Tooltip,
    Legend,
    Filler
);

/**
 * Chart theme configuration
 */
export interface ChartTheme {
    /** Primary color for main data */
    primary: string;
    /** Secondary color for comparison data */
    secondary: string;
    /** Success color (green) */
    success: string;
    /** Warning color (yellow/orange) */
    warning: string;
    /** Danger color (red) */
    danger: string;
    /** Text color */
    text: string;
    /** Grid color */
    grid: string;
    /** Background color */
    background: string;
}

/**
 * Default light theme
 */
export const LIGHT_THEME: ChartTheme = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#22c55e',
    warning: '#f59e0b',
    danger: '#ef4444',
    text: '#374151',
    grid: '#e5e7eb',
    background: '#ffffff',
};

/**
 * Default dark theme
 */
export const DARK_THEME: ChartTheme = {
    primary: '#818cf8',
    secondary: '#a78bfa',
    success: '#4ade80',
    warning: '#fbbf24',
    danger: '#f87171',
    text: '#e5e7eb',
    grid: '#374151',
    background: '#1f2937',
};

/**
 * Daily statistics data point
 */
export interface DailyStatPoint {
    date: string;
    reviewCount: number;
    averageScore: number;
    duration: number;
}

/**
 * Mastery distribution data
 */
export interface MasteryDistribution {
    mastered: number;
    learning: number;
    struggling: number;
}

/**
 * Review trend data
 */
export interface ReviewTrend {
    labels: string[];
    reviewCounts: number[];
    averageScores: number[];
    retentionRates: number[];
}

/**
 * Service for creating and managing Chart.js charts
 */
export class StatisticsChartService {
    private charts: Map<string, Chart> = new Map();
    private theme: ChartTheme;
    private isDarkMode: boolean;

    constructor(isDarkMode: boolean = false) {
        this.isDarkMode = isDarkMode;
        this.theme = isDarkMode ? DARK_THEME : LIGHT_THEME;
    }

    /**
     * Update theme based on dark mode setting
     */
    setDarkMode(isDarkMode: boolean): void {
        this.isDarkMode = isDarkMode;
        this.theme = isDarkMode ? DARK_THEME : LIGHT_THEME;

        // Update all existing charts
        this.charts.forEach((chart, id) => {
            this.updateChartTheme(chart);
        });
    }

    /**
     * Update chart theme colors
     */
    private updateChartTheme(chart: Chart): void {
        if (chart.options.scales) {
            const scales = chart.options.scales as any;
            if (scales.x) {
                scales.x.ticks = { ...scales.x.ticks, color: this.theme.text };
                scales.x.grid = { ...scales.x.grid, color: this.theme.grid };
            }
            if (scales.y) {
                scales.y.ticks = { ...scales.y.ticks, color: this.theme.text };
                scales.y.grid = { ...scales.y.grid, color: this.theme.grid };
            }
        }
        if (chart.options.plugins?.legend?.labels) {
            (chart.options.plugins.legend.labels as any).color = this.theme.text;
        }
        chart.update();
    }

    /**
     * Create daily review count bar chart
     */
    createDailyReviewChart(
        container: HTMLElement,
        data: DailyStatPoint[],
        chartId: string = 'daily-review-chart'
    ): Chart | null {
        // Clean up existing chart
        this.destroyChart(chartId);

        const canvas = this.createCanvas(container, chartId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        const config: ChartConfiguration<'bar'> = {
            type: 'bar',
            data: {
                labels: data.map(d => d.date),
                datasets: [
                    {
                        label: '复习概念数',
                        data: data.map(d => d.reviewCount),
                        backgroundColor: this.theme.primary,
                        borderColor: this.theme.primary,
                        borderWidth: 1,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: this.theme.text,
                            font: { size: 12 },
                        },
                    },
                    title: {
                        display: true,
                        text: '每日复习统计',
                        color: this.theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    tooltip: {
                        backgroundColor: this.theme.background,
                        titleColor: this.theme.text,
                        bodyColor: this.theme.text,
                        borderColor: this.theme.grid,
                        borderWidth: 1,
                    },
                },
                scales: {
                    x: {
                        ticks: { color: this.theme.text },
                        grid: { color: this.theme.grid },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: this.theme.text,
                            stepSize: 1,
                        },
                        grid: { color: this.theme.grid },
                    },
                },
            },
        };

        const chart = new Chart(ctx, config);
        this.charts.set(chartId, chart);
        return chart;
    }

    /**
     * Create average score line chart
     */
    createScoreTrendChart(
        container: HTMLElement,
        data: DailyStatPoint[],
        chartId: string = 'score-trend-chart'
    ): Chart | null {
        this.destroyChart(chartId);

        const canvas = this.createCanvas(container, chartId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        const config: ChartConfiguration<'line'> = {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [
                    {
                        label: '平均评分',
                        data: data.map(d => d.averageScore),
                        borderColor: this.theme.secondary,
                        backgroundColor: this.hexToRgba(this.theme.secondary, 0.1),
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: this.theme.text,
                            font: { size: 12 },
                        },
                    },
                    title: {
                        display: true,
                        text: '评分趋势',
                        color: this.theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    tooltip: {
                        backgroundColor: this.theme.background,
                        titleColor: this.theme.text,
                        bodyColor: this.theme.text,
                        borderColor: this.theme.grid,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => `评分: ${(context.parsed.y ?? 0).toFixed(1)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        ticks: { color: this.theme.text },
                        grid: { color: this.theme.grid },
                    },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            color: this.theme.text,
                            stepSize: 20,
                        },
                        grid: { color: this.theme.grid },
                    },
                },
            },
        };

        const chart = new Chart(ctx, config);
        this.charts.set(chartId, chart);
        return chart;
    }

    /**
     * Create mastery distribution doughnut chart
     */
    createMasteryChart(
        container: HTMLElement,
        data: MasteryDistribution,
        chartId: string = 'mastery-chart'
    ): Chart | null {
        this.destroyChart(chartId);

        const canvas = this.createCanvas(container, chartId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        const total = data.mastered + data.learning + data.struggling;
        if (total === 0) {
            this.renderEmptyState(container, '暂无掌握数据');
            return null;
        }

        const config: ChartConfiguration<'doughnut'> = {
            type: 'doughnut',
            data: {
                labels: ['已掌握', '学习中', '需加强'],
                datasets: [
                    {
                        data: [data.mastered, data.learning, data.struggling],
                        backgroundColor: [
                            this.theme.success,
                            this.theme.warning,
                            this.theme.danger,
                        ],
                        borderColor: this.theme.background,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: this.theme.text,
                            font: { size: 12 },
                            padding: 16,
                        },
                    },
                    title: {
                        display: true,
                        text: '概念掌握分布',
                        color: this.theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    tooltip: {
                        backgroundColor: this.theme.background,
                        titleColor: this.theme.text,
                        bodyColor: this.theme.text,
                        borderColor: this.theme.grid,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value} (${percentage}%)`;
                            },
                        },
                    },
                },
                cutout: '60%',
            },
        };

        const chart = new Chart(ctx, config);
        this.charts.set(chartId, chart);
        return chart;
    }

    /**
     * Create combined review trend chart (bar + line)
     */
    createCombinedTrendChart(
        container: HTMLElement,
        data: ReviewTrend,
        chartId: string = 'combined-trend-chart'
    ): Chart | null {
        this.destroyChart(chartId);

        const canvas = this.createCanvas(container, chartId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        const config: ChartConfiguration = {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        type: 'bar',
                        label: '复习次数',
                        data: data.reviewCounts,
                        backgroundColor: this.hexToRgba(this.theme.primary, 0.7),
                        borderColor: this.theme.primary,
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y',
                        order: 2,
                    },
                    {
                        type: 'line',
                        label: '平均评分',
                        data: data.averageScores,
                        borderColor: this.theme.secondary,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y1',
                        order: 1,
                    },
                    {
                        type: 'line',
                        label: '记忆保持率',
                        data: data.retentionRates.map(r => r * 100),
                        borderColor: this.theme.success,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y1',
                        order: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: this.theme.text,
                            font: { size: 11 },
                            usePointStyle: true,
                        },
                    },
                    title: {
                        display: true,
                        text: '复习趋势分析',
                        color: this.theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    tooltip: {
                        backgroundColor: this.theme.background,
                        titleColor: this.theme.text,
                        bodyColor: this.theme.text,
                        borderColor: this.theme.grid,
                        borderWidth: 1,
                    },
                },
                scales: {
                    x: {
                        ticks: { color: this.theme.text },
                        grid: { color: this.theme.grid },
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '复习次数',
                            color: this.theme.text,
                        },
                        ticks: {
                            color: this.theme.text,
                            stepSize: 1,
                        },
                        grid: { color: this.theme.grid },
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: '百分比 (%)',
                            color: this.theme.text,
                        },
                        ticks: { color: this.theme.text },
                        grid: { drawOnChartArea: false },
                    },
                },
            },
        };

        const chart = new Chart(ctx, config as any);
        this.charts.set(chartId, chart);
        return chart;
    }

    /**
     * Create weekly summary bar chart
     */
    createWeeklySummaryChart(
        container: HTMLElement,
        data: { week: string; count: number; score: number }[],
        chartId: string = 'weekly-summary-chart'
    ): Chart | null {
        this.destroyChart(chartId);

        const canvas = this.createCanvas(container, chartId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        const config: ChartConfiguration<'bar'> = {
            type: 'bar',
            data: {
                labels: data.map(d => d.week),
                datasets: [
                    {
                        label: '复习次数',
                        data: data.map(d => d.count),
                        backgroundColor: this.theme.primary,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false,
                    },
                    title: {
                        display: true,
                        text: '每周复习统计',
                        color: this.theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    tooltip: {
                        backgroundColor: this.theme.background,
                        titleColor: this.theme.text,
                        bodyColor: this.theme.text,
                        borderColor: this.theme.grid,
                        borderWidth: 1,
                        callbacks: {
                            afterLabel: (context) => {
                                const idx = context.dataIndex;
                                return `平均评分: ${data[idx].score.toFixed(1)}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { color: this.theme.text },
                        grid: { color: this.theme.grid },
                    },
                    y: {
                        ticks: { color: this.theme.text },
                        grid: { display: false },
                    },
                },
            },
        };

        const chart = new Chart(ctx, config);
        this.charts.set(chartId, chart);
        return chart;
    }

    /**
     * Update chart data
     */
    updateChartData(chartId: string, newData: any): void {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    /**
     * Destroy a specific chart
     */
    destroyChart(chartId: string): void {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
        }
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts(): void {
        this.charts.forEach((chart) => chart.destroy());
        this.charts.clear();
    }

    /**
     * Create canvas element for chart
     */
    private createCanvas(container: HTMLElement, id: string): HTMLCanvasElement | null {
        // Clear container
        container.empty();

        const wrapper = container.createDiv({ cls: 'chart-wrapper' });
        wrapper.style.position = 'relative';
        wrapper.style.width = '100%';
        wrapper.style.height = '100%';

        const canvas = wrapper.createEl('canvas', { attr: { id } });
        return canvas;
    }

    /**
     * Render empty state when no data
     */
    private renderEmptyState(container: HTMLElement, message: string): void {
        container.empty();
        const emptyDiv = container.createDiv({ cls: 'chart-empty-state' });
        emptyDiv.createEl('span', { cls: 'empty-icon', text: '📊' });
        emptyDiv.createEl('p', { text: message });
    }

    /**
     * Convert hex color to rgba
     */
    private hexToRgba(hex: string, alpha: number): string {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /**
     * Get theme colors
     */
    getTheme(): ChartTheme {
        return this.theme;
    }
}

/**
 * Aggregate review records into daily statistics
 */
export function aggregateDailyStats(
    records: ReviewRecord[],
    days: number = 7
): DailyStatPoint[] {
    const now = new Date();
    const result: DailyStatPoint[] = [];

    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        date.setHours(0, 0, 0, 0);

        const nextDate = new Date(date);
        nextDate.setDate(nextDate.getDate() + 1);

        const dayRecords = records.filter(r => {
            const reviewDate = new Date(r.reviewDate);
            return reviewDate >= date && reviewDate < nextDate;
        });

        const reviewCount = dayRecords.length;
        const totalScore = dayRecords.reduce((sum, r) => sum + (r.reviewScore || 0), 0);
        const averageScore = reviewCount > 0 ? totalScore / reviewCount : 0;
        const totalDuration = dayRecords.reduce((sum, r) => sum + r.reviewDuration, 0);

        result.push({
            date: formatDate(date),
            reviewCount,
            averageScore,
            duration: totalDuration,
        });
    }

    return result;
}

/**
 * Calculate mastery distribution from records
 */
export function calculateMasteryDistribution(
    records: ReviewRecord[]
): MasteryDistribution {
    // Get unique concepts by latest record
    const conceptMap = new Map<string, ReviewRecord>();

    records.forEach(record => {
        const key = record.conceptId || record.conceptName;
        const existing = conceptMap.get(key);
        if (!existing || new Date(record.reviewDate) > new Date(existing.reviewDate)) {
            conceptMap.set(key, record);
        }
    });

    let mastered = 0;
    let learning = 0;
    let struggling = 0;

    conceptMap.forEach(record => {
        if (record.memoryStrength >= 0.8) {
            mastered++;
        } else if (record.memoryStrength >= 0.5) {
            learning++;
        } else {
            struggling++;
        }
    });

    return { mastered, learning, struggling };
}

/**
 * Build review trend data from statistics
 */
export function buildReviewTrend(
    stats: LearningStatistics[],
    days: number = 7
): ReviewTrend {
    const sortedStats = [...stats]
        .sort((a, b) => new Date(a.statDate).getTime() - new Date(b.statDate).getTime())
        .slice(-days);

    return {
        labels: sortedStats.map(s => formatDate(new Date(s.statDate))),
        reviewCounts: sortedStats.map(s => s.dailyReviews),
        averageScores: sortedStats.map(s => s.dailyAverageScore || 0),
        retentionRates: sortedStats.map(s => s.averageRetentionRate),
    };
}

/**
 * Format date as MM/DD
 */
function formatDate(date: Date): string {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${month}/${day}`;
}

/**
 * Create statistics chart service instance
 */
export function createStatisticsChartService(isDarkMode: boolean = false): StatisticsChartService {
    return new StatisticsChartService(isDarkMode);
}
