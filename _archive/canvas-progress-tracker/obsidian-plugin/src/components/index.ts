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

// ============================================================
// Story 6.9: Multimodal UI Components
// ============================================================

// Image Preview Component (AC 6.9.1)
export {
    createImagePreview,
    createImageGallery,
    openLightbox,
    closeLightbox,
    resetLightbox,
    createThumbnail,
    type ImagePreviewProps,
    type ImageGalleryProps
} from './ImagePreview';

// PDF Preview Component (AC 6.9.2)
export {
    createPDFPreview,
    createPDFThumbnail,
    openPDFModal,
    updatePDFPage,
    type PDFPreviewProps,
    type PDFThumbnailProps
} from './PDFPreview';

// Media Player Component (AC 6.9.3)
export {
    createAudioPlayer,
    createVideoPlayer,
    formatTime,
    seekTo,
    addTimeMarker,
    getCurrentTime,
    setPlaybackRate,
    type AudioPlayerProps,
    type VideoPlayerProps,
    type TimeMarker
} from './MediaPlayer';

// Media Panel Component (AC 6.9.4 + 6.9.5)
export {
    createMediaPanel,
    createMediaList,
    updateMediaPanel,
    getMediaPanelFilter,
    setMediaPanelFilter,
    type MediaType,
    type MediaItem,
    type MediaPanelProps,
    type MediaListProps
} from './MediaPanel';
