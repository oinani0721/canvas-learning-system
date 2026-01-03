/**
 * UI Types - Canvas Learning System
 *
 * Type definitions for UI components.
 * Implements Story 14.2: 复习仪表板UI
 *
 * @module UITypes
 * @version 1.0.0
 */

// ============================================================================
// Review Task Types
// ============================================================================

/**
 * Task priority levels
 */
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';

/**
 * Task filter options
 */
export type TaskFilterOption = 'all' | 'overdue' | 'today' | 'high-priority';

/**
 * Task sort options
 */
export type TaskSortOption = 'priority' | 'dueDate' | 'memoryStrength' | 'canvas';

/**
 * Dashboard tab options (Story 14.6 + Story 14.13 + Epic 16)
 * Extended to include verification canvas and cross-canvas learning tabs
 */
export type DashboardTab = 'tasks' | 'history' | 'verification' | 'cross-canvas';

/**
 * History time range options (Story 14.6)
 */
export type HistoryTimeRange = '7d' | '30d';

/**
 * Review mode for history display (Story 14.6)
 */
export type ReviewMode = 'fresh' | 'targeted';

// ============================================================================
// History Types (Story 14.6)
// ============================================================================

/**
 * History entry for review record display
 */
export interface HistoryEntry {
    /** Unique entry ID */
    id: string;
    /** Canvas file path */
    canvasPath: string;
    /** Canvas title */
    canvasTitle: string;
    /** Concept name */
    conceptName: string;
    /** Review date */
    reviewDate: Date;
    /** Score (1-5) */
    score: number;
    /** Review mode */
    mode: ReviewMode;
    /** Memory strength after review */
    memoryStrength: number;
    /** Review duration in seconds */
    duration?: number;
}

/**
 * Daily statistics item for charts
 */
export interface DailyStatItem {
    /** Date string (YYYY-MM-DD) */
    date: string;
    /** Number of concepts reviewed */
    conceptCount: number;
    /** Average score (1-5) */
    averageScore: number;
    /** Total review time in minutes */
    totalMinutes: number;
}

/**
 * Canvas review trend for multi-review analysis
 */
export interface CanvasReviewTrend {
    /** Canvas file path */
    canvasPath: string;
    /** Canvas title */
    canvasTitle: string;
    /** Review sessions */
    sessions: ReviewSession[];
    /** Overall progress rate (percentage) */
    progressRate: number;
    /** Progress trend direction */
    trend: 'up' | 'down' | 'stable';
}

/**
 * Single review session data
 */
export interface ReviewSession {
    /** Session date */
    date: Date;
    /** Pass rate (0-1) */
    passRate: number;
    /** Review mode */
    mode: ReviewMode;
    /** Concepts reviewed count */
    conceptsReviewed: number;
    /** Weak concepts count */
    weakConceptsCount: number;
}

/**
 * History view state (Story 14.6)
 */
export interface HistoryViewState {
    /** History entries */
    entries: HistoryEntry[];
    /** Daily statistics */
    dailyStats: DailyStatItem[];
    /** Canvas review trends */
    canvasTrends: CanvasReviewTrend[];
    /** Selected time range */
    timeRange: HistoryTimeRange;
    /** Loading state */
    loading: boolean;
}

/**
 * Review task interface
 */
export interface ReviewTask {
    /** Unique task ID */
    id: string;
    /** Associated canvas ID */
    canvasId: string;
    /** Canvas title */
    canvasTitle: string;
    /** Concept being reviewed */
    conceptName: string;
    /** Task priority */
    priority: TaskPriority;
    /** Due date */
    dueDate: Date;
    /** Days overdue (negative if not due yet) */
    overdueDays: number;
    /** Memory strength (0-1) */
    memoryStrength: number;
    /** Retention rate (0-1) */
    retentionRate: number;
    /** Review count */
    reviewCount: number;
    /** Last review date */
    lastReviewDate?: Date;
    /** Task status */
    status: 'pending' | 'in_progress' | 'completed' | 'postponed';
}

// ============================================================================
// Statistics Types
// ============================================================================

/**
 * Mastery distribution item
 */
export interface MasteryDistributionItem {
    label: string;
    count: number;
    percentage: number;
    color: string;
}

/**
 * Activity type
 */
export type ActivityType = 'review' | 'session' | 'achievement' | 'milestone';

/**
 * Recent activity
 */
export interface RecentActivity {
    type: ActivityType;
    title: string;
    description?: string;
    timestamp: Date;
}

/**
 * Dashboard statistics
 */
export interface DashboardStatistics {
    /** Today's pending reviews */
    todayPending: number;
    /** Today's completed reviews */
    todayCompleted: number;
    /** Today's postponed reviews */
    todayPostponed: number;
    /** Today's progress (0-1) */
    todayProgress: number;
    /** Average score */
    averageScore: number;
    /** Average memory strength */
    averageMemoryStrength: number;
    /** Average retention rate */
    averageRetentionRate: number;
    /** Streak days */
    streakDays: number;
    /** Total concepts */
    totalConcepts: number;
    /** Mastered concepts */
    masteredConcepts: number;
    /** Learning concepts */
    learningConcepts: number;
    /** Struggling concepts */
    strugglingConcepts: number;
    /** Mastery distribution */
    masteryDistribution: MasteryDistributionItem[];
    /** Recent activities */
    recentActivities: RecentActivity[];
}

// ============================================================================
// Component Props Types
// ============================================================================

/**
 * Base component props
 */
export interface BaseComponentProps {
    className?: string;
}

/**
 * Dashboard header props
 */
export interface DashboardHeaderProps extends BaseComponentProps {
    statistics: DashboardStatistics;
    onRefresh: () => void;
    loading: boolean;
}

/**
 * Task list props
 */
export interface TaskListProps extends BaseComponentProps {
    tasks: ReviewTask[];
    loading: boolean;
    sortBy: TaskSortOption;
    filterBy: TaskFilterOption;
    onTaskClick?: (task: ReviewTask) => void;
    onTaskComplete: (task: ReviewTask) => void;
    onTaskPostpone: (task: ReviewTask, days: number) => void;
    onSortChange: (sort: TaskSortOption) => void;
    onFilterChange: (filter: TaskFilterOption) => void;
}

/**
 * Task card props
 */
export interface TaskCardProps extends BaseComponentProps {
    task: ReviewTask;
    onClick?: () => void;
    onComplete: () => void;
    onPostpone: (days: number) => void;
}

/**
 * Statistics panel props
 */
export interface StatisticsPanelProps extends BaseComponentProps {
    statistics: DashboardStatistics;
    loading: boolean;
}

/**
 * Quick actions props
 */
export interface QuickActionsProps extends BaseComponentProps {
    onStartReview: () => void;
    onGeneratePlan: () => void;
    onViewCalendar: () => void;
    onRefresh: () => void;
    loading: boolean;
}

// ============================================================================
// View Types
// ============================================================================

/**
 * Dashboard view state
 */
export interface DashboardViewState {
    /** Current active tab (Story 14.6 + Story 14.13 + Epic 16) */
    currentTab: DashboardTab;
    tasks: ReviewTask[];
    statistics: DashboardStatistics;
    /** History view state (Story 14.6) */
    historyState: HistoryViewState;
    /** Verification view state (Story 14.13) */
    verificationState: VerificationViewState;
    /** Cross-canvas view state (Epic 16) */
    crossCanvasState: CrossCanvasViewState;
    loading: boolean;
    error: string | null;
    sortBy: TaskSortOption;
    filterBy: TaskFilterOption;
    lastUpdated: Date | null;
}

/**
 * Default history view state (Story 14.6)
 */
export const DEFAULT_HISTORY_STATE: HistoryViewState = {
    entries: [],
    dailyStats: [],
    canvasTrends: [],
    timeRange: '7d',
    loading: false,
};

/**
 * Default verification view state (Story 14.13)
 */
export const DEFAULT_VERIFICATION_STATE: VerificationViewState = {
    relations: [],
    loading: false,
    selectedRelationId: undefined,
};

/**
 * Default cross-canvas view state (Epic 16)
 */
export const DEFAULT_CROSS_CANVAS_STATE: CrossCanvasViewState = {
    associations: [],
    searchResults: [],
    knowledgePaths: [],
    searchQuery: '',
    loading: false,
    selectedAssociationId: undefined,
};

/**
 * Default dashboard state
 */
export const DEFAULT_DASHBOARD_STATE: DashboardViewState = {
    currentTab: 'tasks',
    tasks: [],
    statistics: {
        todayPending: 0,
        todayCompleted: 0,
        todayPostponed: 0,
        todayProgress: 0,
        averageScore: 0,
        averageMemoryStrength: 0,
        averageRetentionRate: 0,
        streakDays: 0,
        totalConcepts: 0,
        masteredConcepts: 0,
        learningConcepts: 0,
        strugglingConcepts: 0,
        masteryDistribution: [],
        recentActivities: [],
    },
    historyState: DEFAULT_HISTORY_STATE,
    verificationState: DEFAULT_VERIFICATION_STATE,
    crossCanvasState: DEFAULT_CROSS_CANVAS_STATE,
    loading: true,
    error: null,
    sortBy: 'priority',
    filterBy: 'all',
    lastUpdated: null,
};

// ============================================================================
// Verification Canvas Types (Story 14.13 - 检验历史存储)
// ============================================================================

/**
 * Verification canvas relationship with original canvas
 * [Source: PRD Story 14.13 - 检验历史存储]
 */
export interface VerificationCanvasRelation {
    /** Unique relationship ID */
    id: string;
    /** Original canvas file path */
    originalCanvasPath: string;
    /** Original canvas title */
    originalCanvasTitle: string;
    /** Generated verification canvas file path */
    verificationCanvasPath: string;
    /** Generated verification canvas title */
    verificationCanvasTitle: string;
    /** Generation date */
    generatedDate: Date;
    /** Review mode used for generation */
    reviewMode: ReviewMode;
    /** Current average score (1-5) */
    currentScore?: number;
    /** Completion rate (0-1) */
    completionRate?: number;
    /** Total number of review sessions */
    sessionCount: number;
    /** All review sessions for this verification canvas */
    sessions: ReviewSession[];
}

/**
 * Verification tab view state
 */
export interface VerificationViewState {
    /** Verification canvas relations */
    relations: VerificationCanvasRelation[];
    /** Loading state */
    loading: boolean;
    /** Selected relation for details */
    selectedRelationId?: string;
}

// ============================================================================
// Cross-Canvas Learning Types (Epic 16 - 跨Canvas关联学习系统)
// ============================================================================

/**
 * Canvas association relationship type
 * [Source: PRD Epic 16 - 跨Canvas关联学习系统]
 * [Source: Story 25.3 - Exercise-Lecture Canvas Association]
 */
export type CanvasRelationshipType =
    | 'prerequisite'
    | 'related'
    | 'application'
    | 'exercise_lecture'   // Story 25.3: 练习Canvas关联到讲座Canvas
    | 'exercise_solution'; // Story 25.3: 练习Canvas关联到解答Canvas

/**
 * Cross-Canvas association between two canvas files
 */
export interface CrossCanvasAssociation {
    /** Unique association ID */
    id: string;
    /** Source canvas file path (e.g., textbook canvas) */
    sourceCanvasPath: string;
    /** Source canvas title */
    sourceCanvasTitle: string;
    /** Target canvas file path (e.g., exercise canvas) */
    targetCanvasPath: string;
    /** Target canvas title */
    targetCanvasTitle: string;
    /** Common concepts found in both canvases */
    commonConcepts: string[];
    /** Type of relationship */
    relationshipType: CanvasRelationshipType;
    /** Confidence score (0-1) */
    confidence: number;
    /** Creation date */
    createdDate: Date;
    /** Last updated date */
    updatedDate: Date;
}

/**
 * Cross-Canvas concept search result
 */
export interface CrossCanvasSearchResult {
    /** Concept name */
    concept: string;
    /** Canvas files containing this concept */
    canvasOccurrences: {
        canvasPath: string;
        canvasTitle: string;
        nodeId: string;
        nodeText: string;
        nodeColor: string;
    }[];
    /** Total occurrence count */
    totalCount: number;
}

/**
 * Knowledge path node for learning transfer visualization
 */
export interface KnowledgePathNode {
    /** Canvas file path */
    canvasPath: string;
    /** Canvas title */
    canvasTitle: string;
    /** Order in learning sequence */
    order: number;
    /** Prerequisite concepts covered */
    prerequisiteConcepts: string[];
    /** Mastery level (0-1) */
    masteryLevel: number;
    /** Is completed */
    isCompleted: boolean;
}

/**
 * Knowledge transfer path
 * [Source: PRD Epic 16 - 知识迁移路径]
 */
export interface KnowledgePath {
    /** Path ID */
    id: string;
    /** Path name (e.g., "线性代数学习路径") */
    name: string;
    /** Path description */
    description?: string;
    /** Ordered nodes in the path */
    nodes: KnowledgePathNode[];
    /** Overall completion progress (0-1) */
    completionProgress: number;
    /** Recommended next canvas to study */
    recommendedNext?: KnowledgePathNode;
}

/**
 * Cross-Canvas tab view state
 */
export interface CrossCanvasViewState {
    /** Canvas associations */
    associations: CrossCanvasAssociation[];
    /** Search results */
    searchResults: CrossCanvasSearchResult[];
    /** Knowledge paths */
    knowledgePaths: KnowledgePath[];
    /** Current search query */
    searchQuery: string;
    /** Loading state */
    loading: boolean;
    /** Selected association for details */
    selectedAssociationId?: string;
}

// ============================================================================
// Textbook Mount Types (Epic 21 - 多格式教材挂载系统)
// ============================================================================

/**
 * Textbook file type
 * [Source: Epic 21 - 多格式教材挂载系统]
 */
export type TextbookType = 'markdown' | 'pdf' | 'canvas';

/**
 * Section extracted from a textbook
 * [Source: Epic 21 - 多格式教材挂载系统]
 */
export interface TextbookSection {
    /** Unique section ID */
    id: string;
    /** Section title (heading text) */
    title: string;
    /** Heading level (1-6 for markdown, page number for PDF) */
    level: number;
    /** Content preview (first ~200 chars) */
    preview: string;
    /** Start offset in file */
    startOffset: number;
    /** End offset in file */
    endOffset: number;
    /** Page number (for PDF) */
    pageNumber?: number;
}

/**
 * Mounted textbook information
 * [Source: Epic 21 - 多格式教材挂载系统]
 */
export interface MountedTextbook {
    /** Unique textbook ID */
    id: string;
    /** File path in vault */
    path: string;
    /** Display name (file basename) */
    name: string;
    /** Textbook type */
    type: TextbookType;
    /** Date when mounted */
    mountedDate: Date;
    /** Last accessed date */
    lastAccessedDate?: Date;
    /** Parsed sections (for navigation) */
    sections?: TextbookSection[];
    /** Number of times referenced by agents */
    referenceCount: number;
}
