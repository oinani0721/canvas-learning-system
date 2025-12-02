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
    tasks: ReviewTask[];
    statistics: DashboardStatistics;
    loading: boolean;
    error: string | null;
    sortBy: TaskSortOption;
    filterBy: TaskFilterOption;
    lastUpdated: Date | null;
}

/**
 * Default dashboard state
 */
export const DEFAULT_DASHBOARD_STATE: DashboardViewState = {
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
    loading: true,
    error: null,
    sortBy: 'priority',
    filterBy: 'all',
    lastUpdated: null,
};
