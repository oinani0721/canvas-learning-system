/**
 * Review Types - Canvas Learning System
 *
 * Data type definitions for the CommandWrapper system.
 * Implements AC-6: ReviewTask, ReviewPlan, ReviewResult, CommandResult interfaces.
 *
 * @module ReviewTypes
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Data Type Definitions
 */

// ============================================================================
// Priority and Status Enums
// ============================================================================

/**
 * Review task priority levels
 */
export type ReviewPriority = 'critical' | 'high' | 'medium' | 'low';

/**
 * Review plan types
 */
export type ReviewPlanType = 'weakness-focused' | 'comprehensive' | 'targeted';

/**
 * Review difficulty levels
 */
export type ReviewDifficulty = 'easy' | 'medium' | 'hard' | 'adaptive';

// ============================================================================
// Command Execution Types
// ============================================================================

/**
 * Options for command execution
 * Source: Story 13.4 Dev Notes - HTTP Communication Protocol
 */
export interface ExecuteOptions {
  /** Timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Whether to parse the command output */
  parseOutput?: boolean;
  /** Input data for the command */
  input?: string;
  /** Additional context for the command */
  context?: Record<string, unknown>;
}

/**
 * Metadata about command execution
 */
export interface CommandMetadata {
  /** Execution time in milliseconds */
  executionTime: number;
  /** Whether the result was from cache */
  cacheHit: boolean;
  /** Number of retry attempts */
  retryCount: number;
}

/**
 * Result of command execution
 * Source: Story 13.4 Dev Notes - HTTP Communication Protocol
 */
export interface CommandResult<T = string> {
  /** Whether the command succeeded */
  success: boolean;
  /** Command output (string or parsed data) */
  output?: T;
  /** Error message if failed */
  error?: string;
  /** Execution metadata */
  metadata?: CommandMetadata;
}

// ============================================================================
// Review Task Types
// ============================================================================

/**
 * Review task representing a concept that needs review
 * Source: Story 13.4 Dev Notes - ReviewTask Interface
 */
export interface ReviewTask {
  /** Unique task identifier */
  id: string;
  /** Canvas file identifier */
  canvasId: string;
  /** Canvas file title */
  canvasTitle: string;
  /** Name of the concept to review */
  conceptName: string;

  // Priority and urgency
  /** Task priority level */
  priority: ReviewPriority;
  /** Urgency score (0-100) */
  urgency: number;

  // Memory metrics
  /** Current memory strength (0-100) */
  memoryStrength: number;
  /** Memory retention rate (0-100) */
  retentionRate: number;
  /** Position on forgetting curve (0-100) */
  forgettingCurvePosition: number;

  // Time information
  /** When the review is due */
  dueDate: Date;
  /** Days overdue (negative if not yet due) */
  overdueDays: number;
  /** Estimated review duration in minutes */
  estimatedDuration: number;

  // Learning state
  /** Last review date (if any) */
  lastReviewDate?: Date;
  /** Consecutive review streak */
  streak: number;
  /** Number of times skipped */
  skipCount: number;
}

// ============================================================================
// Review Plan Types
// ============================================================================

/**
 * A section within a review plan
 */
export interface ReviewSection {
  /** Section identifier */
  id: string;
  /** Section title */
  title: string;
  /** Section type (e.g., 'concept', 'practice', 'quiz') */
  type: string;
  /** Concepts covered in this section */
  concepts: string[];
  /** Estimated duration in minutes */
  duration: number;
  /** Section order in the plan */
  order: number;
}

/**
 * A resource referenced in a review plan
 */
export interface Resource {
  /** Resource identifier */
  id: string;
  /** Resource title */
  title: string;
  /** Resource type (e.g., 'note', 'canvas', 'external') */
  type: string;
  /** Resource path or URL */
  path: string;
  /** Whether the resource is required */
  required: boolean;
}

/**
 * Review plan for structured learning sessions
 * Source: Story 13.4 Dev Notes - ReviewPlan Interface
 */
export interface ReviewPlan {
  /** Unique plan identifier */
  id: string;
  /** Associated canvas identifier */
  canvasId: string;
  /** Canvas title */
  canvasTitle: string;

  // Plan information
  /** Type of review plan */
  planType: ReviewPlanType;
  /** Difficulty level */
  difficulty: ReviewDifficulty;
  /** Estimated total duration in minutes */
  estimatedDuration: number;

  // Goals
  /** Target mastery level (0-100) */
  targetMastery: number;
  /** Areas to focus on */
  focusAreas: string[];
  /** Maximum concepts to cover */
  maxConcepts: number;

  // Content structure
  /** Plan sections */
  sections: ReviewSection[];
  /** Associated resources */
  resources: Resource[];

  // Generation info
  /** When the plan was generated */
  generatedAt: Date;
  /** Data sources used for generation */
  basedOnData: string[];
}

// ============================================================================
// Review Result Types
// ============================================================================

/**
 * Score breakdown for a review
 */
export interface ScoreBreakdown {
  /** Accuracy score (0-25) */
  accuracy: number;
  /** Imagery/visualization score (0-25) */
  imagery: number;
  /** Completeness score (0-25) */
  completeness: number;
  /** Originality score (0-25) */
  originality: number;
}

/**
 * Statistics about a review session
 */
export interface ReviewStatistics {
  /** Total concepts reviewed */
  conceptsReviewed: number;
  /** Concepts that passed */
  conceptsPassed: number;
  /** Concepts that failed */
  conceptsFailed: number;
  /** Average score achieved */
  averageScore: number;
  /** Total time spent in minutes */
  timeSpent: number;
}

/**
 * Result of completing a review
 */
export interface ReviewResult {
  /** Whether the review was successful */
  success: boolean;
  /** Task that was reviewed */
  taskId: string;
  /** Canvas identifier */
  canvasId: string;
  /** Score breakdown */
  scores: ScoreBreakdown;
  /** Total score (0-100) */
  totalScore: number;
  /** Whether the review passed */
  passed: boolean;
  /** Threshold for passing */
  passThreshold: number;
  /** Review statistics */
  statistics: ReviewStatistics;
  /** Feedback or notes */
  feedback?: string;
  /** When the review was completed */
  completedAt: Date;
}

// ============================================================================
// Command Wrapper Options
// ============================================================================

/**
 * Options for retrieving review tasks
 */
export interface ReviewOptions {
  /** Filter by canvas ID */
  canvasId?: string;
  /** Filter by priority */
  priority?: ReviewPriority;
  /** Filter by due date (before) */
  dueBefore?: Date;
  /** Maximum tasks to return */
  limit?: number;
  /** Sort by field */
  sortBy?: 'dueDate' | 'priority' | 'urgency' | 'memoryStrength';
  /** Sort order */
  sortOrder?: 'asc' | 'desc';
}

/**
 * Options for generating a review plan
 */
export interface ReviewPlanOptions {
  /** Type of plan to generate */
  planType?: ReviewPlanType;
  /** Difficulty level */
  difficulty?: ReviewDifficulty;
  /** Target duration in minutes */
  duration?: number;
  /** Maximum concepts to include */
  maxConcepts?: number;
  /** Specific focus areas */
  focusAreas?: string[];
}

/**
 * Options for completing a review
 */
export interface CompleteReviewOptions {
  /** User's understanding text */
  userUnderstanding: string;
  /** Time spent on review in minutes */
  timeSpent?: number;
  /** Additional notes */
  notes?: string;
  /** Whether to skip scoring */
  skipScoring?: boolean;
}

// ============================================================================
// Cache Types
// ============================================================================

/**
 * Cache item structure
 */
export interface CacheItem<T = unknown> {
  /** Cached data */
  data: T;
  /** Timestamp when cached */
  timestamp: number;
  /** Time to live in milliseconds */
  ttl: number;
}

/**
 * Cache statistics
 */
export interface CacheStats {
  /** Total cache hits */
  hits: number;
  /** Total cache misses */
  misses: number;
  /** Current item count */
  itemCount: number;
  /** Hit rate percentage */
  hitRate: number;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Error codes for command execution
 */
export type CommandErrorCode =
  | 'TIMEOUT'
  | 'NETWORK_ERROR'
  | 'PARSE_ERROR'
  | 'VALIDATION_ERROR'
  | 'RETRY_EXHAUSTED'
  | 'NOT_FOUND'
  | 'UNAUTHORIZED'
  | 'UNKNOWN';

/**
 * Custom error for command execution failures
 */
export class CommandExecutionError extends Error {
  public readonly code: CommandErrorCode;
  public readonly originalError?: Error;

  constructor(
    message: string,
    code: CommandErrorCode = 'UNKNOWN',
    originalError?: Error
  ) {
    super(message);
    this.name = 'CommandExecutionError';
    this.code = code;
    this.originalError = originalError;

    // Ensure proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, CommandExecutionError.prototype);
  }
}

// ============================================================================
// Command Executor Interface
// ============================================================================

/**
 * Interface for command executors
 * Source: Story 13.4 Dev Notes - HTTP Command Executor
 */
export interface ICommandExecutor {
  /**
   * Execute a command
   * @param command - The command to execute
   * @param options - Execution options
   * @returns Command result
   */
  execute(command: string, options?: ExecuteOptions): Promise<CommandResult>;
}

// ============================================================================
// Output Parser Interface
// ============================================================================

/**
 * Interface for output parsers
 * Source: Story 13.4 Dev Notes - Output Parsers
 */
export interface OutputParser<T> {
  /**
   * Parse command output into structured data
   * @param output - Raw command output
   * @returns Parsed data
   */
  parse(output: string): T;
}

// ============================================================================
// Batch Command Types
// ============================================================================

/**
 * Batch command structure
 */
export interface BatchCommand {
  /** Command to execute */
  command: string;
  /** Command options */
  options?: ExecuteOptions;
  /** Command identifier for result matching */
  id?: string;
}

/**
 * Batch command result
 */
export interface BatchCommandResult {
  /** Command identifier */
  id?: string;
  /** Command result */
  result: CommandResult;
  /** Execution status */
  status: 'fulfilled' | 'rejected';
}
