/**
 * Learning Heatmap Component
 *
 * Story 19.5 AC 4: 学习热力图，显示学习活动分布
 *
 * ✅ Verified from SVG specification (MDN Standard)
 * [Source: docs/stories/19.5.story.md:370-432 - 热力图组件]
 */

/**
 * Heatmap cell data.
 */
export interface HeatmapCell {
    /** Date string (YYYY-MM-DD) */
    date: string;
    /** Activity count or intensity (0+) */
    value: number;
    /** Optional tooltip text */
    tooltip?: string;
}

/**
 * Props for LearningHeatmap component.
 */
export interface LearningHeatmapProps {
    /** Array of heatmap cells */
    data: HeatmapCell[];
    /** Start date (default: 6 months ago) */
    startDate?: Date;
    /** End date (default: today) */
    endDate?: Date;
    /** Cell size in pixels (default: 12) */
    cellSize?: number;
    /** Gap between cells in pixels (default: 3) */
    cellGap?: number;
    /** Color scheme (default: green) */
    colorScheme?: 'green' | 'blue' | 'purple';
    /** Show month labels (default: true) */
    showMonthLabels?: boolean;
    /** Show day labels (default: true) */
    showDayLabels?: boolean;
    /** Title text (optional) */
    title?: string;
    /** Callback when a cell is clicked */
    onCellClick?: (cell: HeatmapCell) => void;
}

/**
 * Color intensity levels for different schemes.
 */
const COLOR_SCHEMES: Record<string, string[]> = {
    green: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
    blue: ['#ebedf0', '#9ecae1', '#4292c6', '#2171b5', '#084594'],
    purple: ['#ebedf0', '#c9b3d9', '#9c6bbb', '#7b3fa0', '#4a0e6f']
};

const DAY_LABELS = ['日', '一', '二', '三', '四', '五', '六'];
const MONTH_LABELS = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

/**
 * Creates a GitHub-style learning activity heatmap using SVG.
 *
 * Features:
 * - Calendar grid showing activity over time
 * - Color intensity based on activity level
 * - Interactive tooltips
 * - Clickable cells for drill-down
 *
 * ✅ Verified from SVG specification (MDN Standard)
 *
 * Example:
 * ```typescript
 * const heatmap = createLearningHeatmap({
 *     data: [
 *         { date: '2025-01-10', value: 5 },
 *         { date: '2025-01-11', value: 2 },
 *     ],
 *     colorScheme: 'green',
 *     title: '学习活动'
 * });
 * container.appendChild(heatmap.container);
 * ```
 */
export function createLearningHeatmap(props: LearningHeatmapProps): {
    container: HTMLElement;
    update: (newData: HeatmapCell[]) => void;
    destroy: () => void;
    toDataUrl: () => string;
} {
    const {
        data,
        startDate = getDefaultStartDate(),
        endDate = new Date(),
        cellSize = 12,
        cellGap = 3,
        colorScheme = 'green',
        showMonthLabels = true,
        showDayLabels = true,
        title,
        onCellClick
    } = props;

    // Create data map for quick lookup
    const dataMap = new Map(data.map(d => [d.date, d]));

    // Calculate grid dimensions
    const weeks = getWeeksBetween(startDate, endDate);
    const numWeeks = weeks.length;
    const labelOffset = showDayLabels ? 30 : 0;
    const headerOffset = showMonthLabels ? 20 : 0;
    const titleOffset = title ? 30 : 0;

    const svgWidth = labelOffset + numWeeks * (cellSize + cellGap);
    const svgHeight = titleOffset + headerOffset + 7 * (cellSize + cellGap);

    // Create container
    const container = document.createElement('div');
    container.className = 'learning-heatmap-container';
    container.style.display = 'inline-block';

    // Create SVG element
    // ✅ Verified from SVG specification (MDN): createElementNS for SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', String(svgWidth));
    svg.setAttribute('height', String(svgHeight));
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', title || 'Learning activity heatmap');
    svg.style.fontFamily = 'var(--font-ui), -apple-system, BlinkMacSystemFont, sans-serif';

    // Add title
    if (title) {
        const titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        titleEl.setAttribute('x', '0');
        titleEl.setAttribute('y', '16');
        titleEl.setAttribute('font-size', '14');
        titleEl.setAttribute('font-weight', 'bold');
        titleEl.setAttribute('fill', 'currentColor');
        titleEl.textContent = title;
        svg.appendChild(titleEl);
    }

    // Add month labels
    if (showMonthLabels) {
        let lastMonth = -1;
        weeks.forEach((week, weekIndex) => {
            const firstDay = week[0];
            if (firstDay && firstDay.getMonth() !== lastMonth) {
                lastMonth = firstDay.getMonth();
                const monthLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                monthLabel.setAttribute('x', String(labelOffset + weekIndex * (cellSize + cellGap)));
                monthLabel.setAttribute('y', String(titleOffset + 12));
                monthLabel.setAttribute('font-size', '10');
                monthLabel.setAttribute('fill', 'var(--text-muted)');
                monthLabel.textContent = MONTH_LABELS[lastMonth];
                svg.appendChild(monthLabel);
            }
        });
    }

    // Add day labels
    if (showDayLabels) {
        [1, 3, 5].forEach(dayIndex => {
            const dayLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            dayLabel.setAttribute('x', '0');
            dayLabel.setAttribute('y', String(titleOffset + headerOffset + dayIndex * (cellSize + cellGap) + cellSize - 2));
            dayLabel.setAttribute('font-size', '10');
            dayLabel.setAttribute('fill', 'var(--text-muted)');
            dayLabel.textContent = DAY_LABELS[dayIndex];
            svg.appendChild(dayLabel);
        });
    }

    // Create cells group
    const cellsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    cellsGroup.setAttribute('class', 'heatmap-cells');
    svg.appendChild(cellsGroup);

    // Calculate max value for color scaling
    const maxValue = Math.max(1, ...data.map(d => d.value));

    // Render cells
    const renderCells = (cellData: Map<string, HeatmapCell>): void => {
        // Clear existing cells
        while (cellsGroup.firstChild) {
            cellsGroup.removeChild(cellsGroup.firstChild);
        }

        weeks.forEach((week, weekIndex) => {
            week.forEach((date, dayIndex) => {
                if (!date) return;

                const dateStr = formatDate(date);
                const cell = cellData.get(dateStr);
                const value = cell?.value || 0;
                const color = getColorForValue(value, maxValue, COLOR_SCHEMES[colorScheme]);

                const x = labelOffset + weekIndex * (cellSize + cellGap);
                const y = titleOffset + headerOffset + dayIndex * (cellSize + cellGap);

                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('class', 'heatmap-cell');
                rect.setAttribute('x', String(x));
                rect.setAttribute('y', String(y));
                rect.setAttribute('width', String(cellSize));
                rect.setAttribute('height', String(cellSize));
                rect.setAttribute('rx', '2');
                rect.setAttribute('fill', color);
                rect.setAttribute('data-date', dateStr);
                rect.setAttribute('data-value', String(value));
                rect.style.cursor = 'pointer';

                // Tooltip title
                const tooltipText = cell?.tooltip || `${dateStr}: ${value} 次学习活动`;
                const titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                titleEl.textContent = tooltipText;
                rect.appendChild(titleEl);

                // Click handler
                if (onCellClick) {
                    rect.addEventListener('click', () => {
                        onCellClick(cell || { date: dateStr, value: 0 });
                    });
                }

                // Hover effect
                rect.addEventListener('mouseenter', () => {
                    rect.setAttribute('stroke', '#333');
                    rect.setAttribute('stroke-width', '1');
                });
                rect.addEventListener('mouseleave', () => {
                    rect.removeAttribute('stroke');
                    rect.removeAttribute('stroke-width');
                });

                cellsGroup.appendChild(rect);
            });
        });
    };

    // Initial render
    renderCells(dataMap);

    container.appendChild(svg);

    // Add legend
    const legend = createLegend(COLOR_SCHEMES[colorScheme]);
    container.appendChild(legend);

    // Update function
    const update = (newData: HeatmapCell[]): void => {
        const newDataMap = new Map(newData.map(d => [d.date, d]));
        renderCells(newDataMap);
    };

    // Destroy function
    const destroy = (): void => {
        container.remove();
    };

    // Export to data URL
    const toDataUrl = (): string => {
        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svg);
        const base64 = btoa(unescape(encodeURIComponent(svgStr)));
        return `data:image/svg+xml;base64,${base64}`;
    };

    return {
        container,
        update,
        destroy,
        toDataUrl
    };
}

/**
 * Get default start date (6 months ago).
 */
function getDefaultStartDate(): Date {
    const date = new Date();
    date.setMonth(date.getMonth() - 6);
    // Align to start of week (Sunday)
    date.setDate(date.getDate() - date.getDay());
    return date;
}

/**
 * Get weeks between two dates.
 * Each week is an array of 7 dates (Sun-Sat), with null for out-of-range dates.
 */
function getWeeksBetween(start: Date, end: Date): (Date | null)[][] {
    const weeks: (Date | null)[][] = [];
    const current = new Date(start);

    // Align to Sunday
    current.setDate(current.getDate() - current.getDay());

    while (current <= end) {
        const week: (Date | null)[] = [];
        for (let i = 0; i < 7; i++) {
            if (current >= start && current <= end) {
                week.push(new Date(current));
            } else {
                week.push(null);
            }
            current.setDate(current.getDate() + 1);
        }
        weeks.push(week);
    }

    return weeks;
}

/**
 * Format date as YYYY-MM-DD.
 */
function formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Get color for value based on intensity levels.
 */
function getColorForValue(value: number, maxValue: number, colors: string[]): string {
    if (value === 0) return colors[0];

    const ratio = value / maxValue;
    const index = Math.min(
        colors.length - 1,
        Math.ceil(ratio * (colors.length - 1))
    );
    return colors[index];
}

/**
 * Create legend element for the heatmap.
 */
function createLegend(colors: string[]): HTMLElement {
    const legend = document.createElement('div');
    legend.className = 'heatmap-legend';
    legend.style.display = 'flex';
    legend.style.alignItems = 'center';
    legend.style.gap = '4px';
    legend.style.marginTop = '8px';
    legend.style.fontSize = '10px';
    legend.style.color = 'var(--text-muted)';

    const lessLabel = document.createElement('span');
    lessLabel.textContent = '少';
    legend.appendChild(lessLabel);

    colors.forEach(color => {
        const box = document.createElement('span');
        box.style.width = '10px';
        box.style.height = '10px';
        box.style.backgroundColor = color;
        box.style.borderRadius = '2px';
        legend.appendChild(box);
    });

    const moreLabel = document.createElement('span');
    moreLabel.textContent = '多';
    legend.appendChild(moreLabel);

    return legend;
}

/**
 * Calculate activity statistics from heatmap data.
 */
export function calculateActivityStats(data: HeatmapCell[]): {
    totalDays: number;
    activeDays: number;
    totalActivities: number;
    maxStreak: number;
    currentStreak: number;
    averagePerDay: number;
} {
    const sortedData = [...data].sort((a, b) => a.date.localeCompare(b.date));
    const activeDays = data.filter(d => d.value > 0).length;
    const totalActivities = data.reduce((sum, d) => sum + d.value, 0);

    // Calculate streaks
    let maxStreak = 0;
    let currentStreak = 0;
    let streak = 0;
    let lastDate: Date | null = null;

    sortedData.forEach(d => {
        if (d.value > 0) {
            const currentDate = new Date(d.date);
            if (lastDate) {
                const diff = (currentDate.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24);
                if (diff === 1) {
                    streak++;
                } else {
                    maxStreak = Math.max(maxStreak, streak);
                    streak = 1;
                }
            } else {
                streak = 1;
            }
            lastDate = currentDate;
        } else {
            maxStreak = Math.max(maxStreak, streak);
            streak = 0;
        }
    });
    maxStreak = Math.max(maxStreak, streak);

    // Check if current streak extends to today
    const today = formatDate(new Date());
    const yesterday = formatDate(new Date(Date.now() - 86400000));
    const lastActive = sortedData.filter(d => d.value > 0).pop();
    if (lastActive && (lastActive.date === today || lastActive.date === yesterday)) {
        currentStreak = streak;
    }

    return {
        totalDays: data.length,
        activeDays,
        totalActivities,
        maxStreak,
        currentStreak,
        averagePerDay: activeDays > 0 ? totalActivities / activeDays : 0
    };
}
