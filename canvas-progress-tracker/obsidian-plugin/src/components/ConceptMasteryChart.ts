/**
 * Concept Mastery Bar Chart Component
 *
 * Story 19.5 AC 3: 概念掌握度条形图，显示各概念的掌握状态
 *
 * ✅ Verified from Chart.js v4 Documentation (Context7)
 * [Source: docs/stories/19.5.story.md:307-369 - 条形图组件]
 */

import { Chart, ChartConfiguration, BarController, BarElement, LinearScale, CategoryScale, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
// ✅ Verified from Context7: Chart.js v4 requires explicit registration
Chart.register(BarController, BarElement, LinearScale, CategoryScale, Title, Tooltip, Legend);

/**
 * Concept mastery data for bar chart.
 */
export interface ConceptMasteryData {
    /** Concept name/label */
    concept: string;
    /** Node ID for reference */
    nodeId: string;
    /** Mastery status: red (not started), purple (in progress), green (mastered) */
    status: 'red' | 'purple' | 'green';
    /** Optional mastery score (0-100) */
    score?: number;
    /** Number of review attempts */
    attempts?: number;
}

/**
 * Props for ConceptMasteryChart component.
 */
export interface ConceptMasteryChartProps {
    /** Array of concept mastery data */
    data: ConceptMasteryData[];
    /** Chart width in pixels (default: 600) */
    width?: number;
    /** Chart height in pixels (default: 400) */
    height?: number;
    /** Chart orientation (default: horizontal) */
    orientation?: 'horizontal' | 'vertical';
    /** Show legend (default: true) */
    showLegend?: boolean;
    /** Title text (optional) */
    title?: string;
    /** Callback when a bar is clicked */
    onBarClick?: (concept: ConceptMasteryData, index: number) => void;
}

/**
 * Status color mapping following Canvas color system.
 * [Source: CLAUDE.md - Color-coded Progress]
 */
const STATUS_COLORS: Record<string, string> = {
    red: '#F44336',      // Not started / struggling
    purple: '#9C27B0',   // In progress
    green: '#4CAF50'     // Mastered
};

const STATUS_LABELS: Record<string, string> = {
    red: '未掌握',
    purple: '学习中',
    green: '已掌握'
};

/**
 * Creates a concept mastery bar chart using Chart.js.
 *
 * Features:
 * - Color-coded bars by mastery status
 * - Horizontal or vertical orientation
 * - Interactive tooltips with concept details
 * - Clickable bars for navigation
 *
 * ✅ Verified from Context7: Chart.js Bar Chart configuration
 *
 * Example:
 * ```typescript
 * const chart = createConceptMasteryChart({
 *     data: [
 *         { concept: '逆否命题', nodeId: 'n1', status: 'green', score: 95 },
 *         { concept: '充分条件', nodeId: 'n2', status: 'purple', score: 60 },
 *     ],
 *     title: '概念掌握情况'
 * });
 * container.appendChild(chart.container);
 * ```
 */
export function createConceptMasteryChart(props: ConceptMasteryChartProps): {
    container: HTMLElement;
    chart: Chart;
    update: (newData: ConceptMasteryData[]) => void;
    destroy: () => void;
    toBase64Image: () => string;
} {
    const {
        data,
        width = 600,
        height = 400,
        orientation = 'horizontal',
        showLegend = true,
        title,
        onBarClick
    } = props;

    // Create container
    const container = document.createElement('div');
    container.className = 'concept-mastery-chart-container';
    container.style.width = `${width}px`;
    container.style.height = `${height}px`;

    // Create canvas element
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', title || 'Concept mastery chart');
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        throw new Error('Failed to get canvas 2D context');
    }

    // Prepare chart data
    const labels = data.map(d => truncateLabel(d.concept, 15));
    const scores = data.map(d => d.score ?? getDefaultScore(d.status));
    const colors = data.map(d => STATUS_COLORS[d.status]);

    // Determine chart type based on orientation
    const isHorizontal = orientation === 'horizontal';

    // ✅ Verified from Context7: Chart.js bar chart with indexAxis for horizontal
    const config: ChartConfiguration<'bar'> = {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: '掌握度',
                data: scores,
                backgroundColor: colors,
                borderColor: colors.map(c => darkenColor(c, 20)),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: isHorizontal ? 'y' : 'x',
            plugins: {
                legend: {
                    display: showLegend,
                    position: 'top',
                    labels: {
                        generateLabels: () => {
                            return Object.entries(STATUS_LABELS).map(([status, label]) => ({
                                text: label,
                                fillStyle: STATUS_COLORS[status],
                                strokeStyle: STATUS_COLORS[status],
                                hidden: false,
                                index: 0
                            }));
                        }
                    }
                },
                title: {
                    display: !!title,
                    text: title || ''
                },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            const index = items[0].dataIndex;
                            return data[index].concept;
                        },
                        label: (context) => {
                            const index = context.dataIndex;
                            const item = data[index];
                            const lines = [
                                `状态: ${STATUS_LABELS[item.status]}`,
                                `分数: ${scores[index]}%`
                            ];
                            if (item.attempts !== undefined) {
                                lines.push(`尝试次数: ${item.attempts}`);
                            }
                            return lines;
                        }
                    }
                }
            },
            scales: {
                [isHorizontal ? 'x' : 'y']: {
                    display: true,
                    title: {
                        display: true,
                        text: '掌握度 (%)'
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: (value) => `${value}%`
                    }
                },
                [isHorizontal ? 'y' : 'x']: {
                    display: true,
                    title: {
                        display: true,
                        text: '概念'
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0 && onBarClick) {
                    const index = elements[0].index;
                    onBarClick(data[index], index);
                }
            }
        }
    };

    // Create chart instance
    const chart = new Chart(ctx, config);

    // Update function
    const update = (newData: ConceptMasteryData[]): void => {
        chart.data.labels = newData.map(d => truncateLabel(d.concept, 15));
        chart.data.datasets[0].data = newData.map(d => d.score ?? getDefaultScore(d.status));
        (chart.data.datasets[0].backgroundColor as string[]) = newData.map(d => STATUS_COLORS[d.status]);
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
 * Get default score based on status.
 */
function getDefaultScore(status: 'red' | 'purple' | 'green'): number {
    switch (status) {
        case 'red': return 20;
        case 'purple': return 60;
        case 'green': return 95;
    }
}

/**
 * Truncate label to max length with ellipsis.
 */
function truncateLabel(label: string, maxLength: number): string {
    if (label.length <= maxLength) return label;
    return label.slice(0, maxLength - 1) + '…';
}

/**
 * Darken a hex color by percentage.
 */
function darkenColor(hex: string, percent: number): string {
    const num = parseInt(hex.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.max(0, (num >> 16) - amt);
    const G = Math.max(0, ((num >> 8) & 0x00FF) - amt);
    const B = Math.max(0, (num & 0x0000FF) - amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
}

/**
 * Group concepts by status for summary.
 */
export function groupByStatus(data: ConceptMasteryData[]): Record<string, ConceptMasteryData[]> {
    return data.reduce((acc, item) => {
        if (!acc[item.status]) {
            acc[item.status] = [];
        }
        acc[item.status].push(item);
        return acc;
    }, {} as Record<string, ConceptMasteryData[]>);
}

/**
 * Calculate mastery statistics.
 */
export function calculateMasteryStats(data: ConceptMasteryData[]): {
    total: number;
    mastered: number;
    inProgress: number;
    notStarted: number;
    masteryRate: number;
} {
    const grouped = groupByStatus(data);
    const total = data.length;
    const mastered = grouped['green']?.length || 0;
    const inProgress = grouped['purple']?.length || 0;
    const notStarted = grouped['red']?.length || 0;

    return {
        total,
        mastered,
        inProgress,
        notStarted,
        masteryRate: total > 0 ? (mastered / total) * 100 : 0
    };
}
