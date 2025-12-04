/**
 * Progress Trend Line Chart Component
 *
 * Story 19.5 AC 2: 进度趋势折线图，显示历史学习趋势
 *
 * ✅ Verified from Chart.js v4 Documentation (Context7)
 * [Source: docs/stories/19.5.story.md:244-306 - 折线图组件]
 */

import { Chart, ChartConfiguration, LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend, Filler } from 'chart.js';

// Register Chart.js components
// ✅ Verified from Context7: Chart.js v4 requires explicit registration
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend, Filler);

/**
 * Data point for progress trend.
 */
export interface ProgressDataPoint {
    /** Date label (e.g., "2025-01-15") */
    date: string;
    /** Coverage rate percentage (0-100) */
    coverageRate: number;
    /** Total concepts count */
    totalConcepts: number;
    /** Passed concepts count */
    passedCount: number;
}

/**
 * Props for ProgressTrendChart component.
 */
export interface ProgressTrendChartProps {
    /** Array of progress data points */
    data: ProgressDataPoint[];
    /** Chart width in pixels (default: 600) */
    width?: number;
    /** Chart height in pixels (default: 300) */
    height?: number;
    /** Show legend (default: true) */
    showLegend?: boolean;
    /** Show data points (default: true) */
    showPoints?: boolean;
    /** Enable fill under line (default: true) */
    showFill?: boolean;
    /** Line color (default: primary theme color) */
    lineColor?: string;
    /** Fill color (default: semi-transparent primary) */
    fillColor?: string;
    /** Title text (optional) */
    title?: string;
    /** Callback when a data point is clicked */
    onPointClick?: (dataPoint: ProgressDataPoint, index: number) => void;
}

/**
 * Creates a progress trend line chart using Chart.js.
 *
 * Features:
 * - Animated line chart showing coverage rate over time
 * - Interactive tooltips with detailed information
 * - Clickable data points for drill-down
 * - Export to image capability
 *
 * ✅ Verified from Context7: Chart.js Line Chart configuration
 *
 * Example:
 * ```typescript
 * const chart = createProgressTrendChart({
 *     data: [
 *         { date: '2025-01-10', coverageRate: 45, totalConcepts: 20, passedCount: 9 },
 *         { date: '2025-01-15', coverageRate: 60, totalConcepts: 20, passedCount: 12 },
 *     ],
 *     title: '学习进度趋势'
 * });
 * container.appendChild(chart.container);
 * ```
 */
export function createProgressTrendChart(props: ProgressTrendChartProps): {
    container: HTMLElement;
    chart: Chart;
    update: (newData: ProgressDataPoint[]) => void;
    destroy: () => void;
    toBase64Image: () => string;
} {
    const {
        data,
        width = 600,
        height = 300,
        showLegend = true,
        showPoints = true,
        showFill = true,
        lineColor = '#4CAF50',
        fillColor = 'rgba(76, 175, 80, 0.2)',
        title,
        onPointClick
    } = props;

    // Create container
    const container = document.createElement('div');
    container.className = 'progress-trend-chart-container';
    container.style.width = `${width}px`;
    container.style.height = `${height}px`;

    // Create canvas element
    // ✅ Verified from Context7: Chart.js requires canvas element
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', title || 'Progress trend chart');
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        throw new Error('Failed to get canvas 2D context');
    }

    // Prepare chart data
    const labels = data.map(d => d.date);
    const coverageData = data.map(d => d.coverageRate);

    // ✅ Verified from Context7: Chart.js configuration structure
    const config: ChartConfiguration<'line'> = {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: '通过率 (%)',
                data: coverageData,
                borderColor: lineColor,
                backgroundColor: showFill ? fillColor : 'transparent',
                fill: showFill,
                tension: 0.3, // Smooth curve
                pointRadius: showPoints ? 5 : 0,
                pointHoverRadius: showPoints ? 8 : 0,
                pointBackgroundColor: lineColor,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: showLegend,
                    position: 'top'
                },
                title: {
                    display: !!title,
                    text: title || ''
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const index = context.dataIndex;
                            const point = data[index];
                            return [
                                `通过率: ${point.coverageRate.toFixed(1)}%`,
                                `已通过: ${point.passedCount}/${point.totalConcepts}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '通过率 (%)'
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: (value) => `${value}%`
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0 && onPointClick) {
                    const index = elements[0].index;
                    onPointClick(data[index], index);
                }
            }
        }
    };

    // Create chart instance
    const chart = new Chart(ctx, config);

    // Update function
    const update = (newData: ProgressDataPoint[]): void => {
        chart.data.labels = newData.map(d => d.date);
        chart.data.datasets[0].data = newData.map(d => d.coverageRate);
        chart.update('active');
    };

    // Destroy function
    const destroy = (): void => {
        chart.destroy();
        container.remove();
    };

    // Export to base64 image
    // ✅ Verified from Context7: toBase64Image() method
    const toBase64Image = (): string => {
        return chart.toBase64Image('image/png', 1.0);
    };

    return {
        container,
        chart,
        update,
        destroy,
        toBase64Image
    };
}

/**
 * Calculate trend direction from data points.
 * Returns 'up', 'down', or 'stable'.
 */
export function calculateTrend(data: ProgressDataPoint[]): 'up' | 'down' | 'stable' {
    if (data.length < 2) return 'stable';

    const first = data[0].coverageRate;
    const last = data[data.length - 1].coverageRate;
    const diff = last - first;

    if (diff > 5) return 'up';
    if (diff < -5) return 'down';
    return 'stable';
}

/**
 * Get trend icon based on direction.
 */
export function getTrendIcon(trend: 'up' | 'down' | 'stable'): string {
    switch (trend) {
        case 'up': return '📈';
        case 'down': return '📉';
        case 'stable': return '➡️';
    }
}

/**
 * Format date for display in chart labels.
 */
export function formatDateLabel(dateStr: string): string {
    try {
        const date = new Date(dateStr);
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateStr;
        }
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } catch {
        return dateStr;
    }
}
