/**
 * Visualization Components Index
 *
 * Story 19.5: Progress Visualization Components
 *
 * Exports all visualization components for the Canvas Progress Tracker.
 */

// Circular Progress Component
export {
    createCircularProgress,
    updateCircularProgress,
    getProgressColor,
    type CircularProgressProps
} from './CircularProgress';

// Progress Trend Line Chart
export {
    createProgressTrendChart,
    calculateTrend,
    getTrendIcon,
    formatDateLabel,
    type ProgressDataPoint,
    type ProgressTrendChartProps
} from './ProgressTrendChart';

// Concept Mastery Bar Chart
export {
    createConceptMasteryChart,
    groupByStatus,
    calculateMasteryStats,
    type ConceptMasteryData,
    type ConceptMasteryChartProps
} from './ConceptMasteryChart';

// Learning Activity Heatmap
export {
    createLearningHeatmap,
    calculateActivityStats,
    type HeatmapCell,
    type LearningHeatmapProps
} from './LearningHeatmap';

// Export Utilities
export { exportChartAsImage, exportAllCharts } from './exportUtils';
