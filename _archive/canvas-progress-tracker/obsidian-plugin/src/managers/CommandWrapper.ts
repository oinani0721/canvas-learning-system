/**
 * CommandWrapper - Main class for wrapping slash commands
 *
 * Implements AC-1, AC-2: Command wrapper for Claude Code communication.
 * Provides a unified interface for executing and caching review commands.
 *
 * @module CommandWrapper
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - CommandWrapper Main Class
 */

import { CommandCache } from '../cache/CommandCache';
import type { HttpExecutorConfig } from '../executors/HttpCommandExecutor';
import { HttpCommandExecutor, MockCommandExecutor } from '../executors/HttpCommandExecutor';
import { ReviewOutputParser } from '../parsers/ReviewOutputParser';
import { GenerateReviewOutputParser } from '../parsers/GenerateReviewOutputParser';
import { CompleteReviewOutputParser } from '../parsers/CompleteReviewOutputParser';
import type {
  ICommandExecutor,
  OutputParser,
  ReviewTask,
  ReviewPlan,
  ReviewResult,
  ReviewOptions,
  ReviewPlanOptions,
  CompleteReviewOptions,
  CommandResult,
  ExecuteOptions,
  BatchCommand,
  BatchCommandResult,
  CommandExecutionError,
} from '../types/ReviewTypes';

// ============================================================================
// Constants
// ============================================================================

/** Default cache TTL: 5 minutes */
const DEFAULT_CACHE_TTL = 5 * 60 * 1000;

/** Commands supported by the wrapper */
const COMMANDS = {
  REVIEW_SHOW: '/review show',
  REVIEW_COMPLETE: '/review complete',
  GENERATE_REVIEW: '/generate-review',
} as const;

// ============================================================================
// Types
// ============================================================================

/**
 * Configuration for CommandWrapper
 */
export interface CommandWrapperConfig {
  /** HTTP executor configuration */
  executorConfig: HttpExecutorConfig;
  /** Default cache TTL in milliseconds */
  cacheTtl?: number;
  /** Enable persistent cache (IndexedDB) */
  enablePersistentCache?: boolean;
  /** Use mock executor for testing */
  useMockExecutor?: boolean;
}

/**
 * Command queue for concurrent control
 */
class CommandQueue {
  private queue: Array<() => Promise<unknown>> = [];
  private running = 0;
  private readonly maxConcurrent: number;

  constructor(maxConcurrent: number = 3) {
    this.maxConcurrent = maxConcurrent;
  }

  async add<T>(task: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await task();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      this.process();
    });
  }

  private async process(): Promise<void> {
    if (this.running >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    const task = this.queue.shift();
    if (!task) return;

    this.running++;
    try {
      await task();
    } finally {
      this.running--;
      this.process();
    }
  }

  get pendingCount(): number {
    return this.queue.length;
  }

  get activeCount(): number {
    return this.running;
  }
}

// ============================================================================
// CommandWrapper Class
// ============================================================================

/**
 * Main class for wrapping slash commands
 *
 * Integrates command execution, caching, and output parsing.
 * Source: Story 13.4 Dev Notes - CommandWrapper Main Class
 */
export class CommandWrapper {
  private readonly executor: ICommandExecutor;
  private readonly cache: CommandCache;
  private readonly cacheTtl: number;
  private readonly queue: CommandQueue;
  private readonly parsers: Map<string, OutputParser<unknown>>;

  /**
   * Create a new CommandWrapper instance
   *
   * @param config - Wrapper configuration
   */
  constructor(config: CommandWrapperConfig) {
    // Initialize executor
    if (config.useMockExecutor) {
      this.executor = new MockCommandExecutor();
    } else {
      this.executor = new HttpCommandExecutor(config.executorConfig);
    }

    // Initialize cache
    this.cache = new CommandCache({
      defaultTtl: config.cacheTtl ?? DEFAULT_CACHE_TTL,
      enablePersistentCache: config.enablePersistentCache ?? false,
    });

    this.cacheTtl = config.cacheTtl ?? DEFAULT_CACHE_TTL;

    // Initialize command queue
    this.queue = new CommandQueue(3);

    // Initialize parsers
    this.parsers = new Map();
    this.parsers.set(COMMANDS.REVIEW_SHOW, new ReviewOutputParser());
    this.parsers.set(COMMANDS.GENERATE_REVIEW, new GenerateReviewOutputParser());
    this.parsers.set(COMMANDS.REVIEW_COMPLETE, new CompleteReviewOutputParser());
  }

  // ==========================================================================
  // Public Methods - Review Commands
  // ==========================================================================

  /**
   * Get review tasks
   *
   * Wraps the /review show command.
   * Source: Story 13.4 Dev Notes - getReviewTasks Method
   *
   * @param options - Review options
   * @returns Array of review tasks
   */
  async getReviewTasks(options?: ReviewOptions): Promise<ReviewTask[]> {
    const command = COMMANDS.REVIEW_SHOW;
    const cacheKey = CommandCache.generateKey(command, options as Record<string, unknown>);

    // Check cache
    const cached = await this.cache.get<ReviewTask[]>(cacheKey);
    if (cached) {
      return cached;
    }

    // Execute command
    const result = await this.queue.add(() =>
      this.executor.execute(command, {
        timeout: 10000,
        parseOutput: true,
        context: options as Record<string, unknown>,
      })
    );

    if (!result.success || !result.output) {
      throw this.createExecutionError(result, 'Failed to get review tasks');
    }

    // Parse output
    const parser = this.parsers.get(command) as OutputParser<ReviewTask[]>;
    const tasks = parser.parse(result.output);

    // Apply filters if provided
    const filteredTasks = this.applyTaskFilters(tasks, options);

    // Cache result
    await this.cache.set(cacheKey, filteredTasks, this.cacheTtl);

    return filteredTasks;
  }

  /**
   * Generate a review plan
   *
   * Wraps the /generate-review command.
   * Source: Story 13.4 Dev Notes - generateReviewPlan Method
   *
   * @param canvas - Canvas identifier
   * @param options - Plan generation options
   * @returns Generated review plan
   */
  async generateReviewPlan(
    canvas: string,
    options: ReviewPlanOptions = {}
  ): Promise<ReviewPlan> {
    // Build command with parameters
    const params = this.buildReviewPlanParams(options);
    const command = params
      ? `${COMMANDS.GENERATE_REVIEW} ${canvas} ${params}`
      : `${COMMANDS.GENERATE_REVIEW} ${canvas}`;

    // Note: Don't cache plan generation - always fresh
    const result = await this.queue.add(() =>
      this.executor.execute(command, {
        timeout: 30000,
        parseOutput: true,
        context: {
          canvas,
          ...options,
        },
      })
    );

    if (!result.success || !result.output) {
      throw this.createExecutionError(result, 'Failed to generate review plan');
    }

    // Parse output
    const parser = this.parsers.get(COMMANDS.GENERATE_REVIEW) as OutputParser<ReviewPlan>;
    return parser.parse(result.output);
  }

  /**
   * Complete a review
   *
   * Wraps the /review complete command.
   *
   * @param taskId - Task identifier
   * @param options - Completion options
   * @returns Review result
   */
  async completeReview(
    taskId: string,
    options: CompleteReviewOptions
  ): Promise<ReviewResult> {
    // Validate input
    if (!taskId) {
      throw new Error('Task ID is required');
    }
    if (!options.userUnderstanding) {
      throw new Error('User understanding is required');
    }

    // Build command
    const command = `${COMMANDS.REVIEW_COMPLETE} ${taskId}`;

    const result = await this.queue.add(() =>
      this.executor.execute(command, {
        timeout: 20000,
        parseOutput: true,
        input: options.userUnderstanding,
        context: {
          taskId,
          timeSpent: options.timeSpent,
          notes: options.notes,
          skipScoring: options.skipScoring,
        },
      })
    );

    if (!result.success || !result.output) {
      throw this.createExecutionError(result, 'Failed to complete review');
    }

    // Parse output
    const parser = this.parsers.get(COMMANDS.REVIEW_COMPLETE) as OutputParser<ReviewResult>;
    const reviewResult = parser.parse(result.output);

    // Invalidate related caches
    await this.invalidateTaskCache();

    return reviewResult;
  }

  // ==========================================================================
  // Public Methods - Batch Operations
  // ==========================================================================

  /**
   * Execute multiple commands in batch
   *
   * Source: Story 13.4 Dev Notes - Performance Optimization
   *
   * @param commands - Array of commands to execute
   * @returns Array of results
   */
  async executeBatch(commands: BatchCommand[]): Promise<BatchCommandResult[]> {
    const promises = commands.map(async (cmd, index) => {
      try {
        const result = await this.queue.add(() =>
          this.executor.execute(cmd.command, cmd.options)
        );
        return {
          id: cmd.id ?? String(index),
          result,
          status: 'fulfilled' as const,
        };
      } catch (error) {
        return {
          id: cmd.id ?? String(index),
          result: {
            success: false,
            error: (error as Error).message,
          },
          status: 'rejected' as const,
        };
      }
    });

    return Promise.all(promises);
  }

  // ==========================================================================
  // Public Methods - Cache Management
  // ==========================================================================

  /**
   * Clear all cached data
   */
  async clearCache(): Promise<void> {
    await this.cache.clear();
  }

  /**
   * Invalidate task-related cache entries
   */
  async invalidateTaskCache(): Promise<void> {
    // Since we use dynamic cache keys, we need to clear all
    // In a more sophisticated implementation, we could track keys
    await this.cache.clear();
  }

  /**
   * Get cache statistics
   *
   * @returns Cache statistics
   */
  getCacheStats() {
    return this.cache.getStats();
  }

  // ==========================================================================
  // Public Methods - Lifecycle
  // ==========================================================================

  /**
   * Clean up resources
   */
  async dispose(): Promise<void> {
    await this.cache.close();
  }

  // ==========================================================================
  // Public Methods - Testing Support
  // ==========================================================================

  /**
   * Get the underlying executor (for testing)
   *
   * @returns The command executor instance
   */
  getExecutor(): ICommandExecutor {
    return this.executor;
  }

  /**
   * Get the mock executor if using mock mode
   *
   * @returns MockCommandExecutor or null
   */
  getMockExecutor(): MockCommandExecutor | null {
    if (this.executor instanceof MockCommandExecutor) {
      return this.executor;
    }
    return null;
  }

  // ==========================================================================
  // Private Methods - Parameter Building
  // ==========================================================================

  /**
   * Build URL parameters for review plan generation
   *
   * @param options - Plan options
   * @returns Parameter string
   */
  private buildReviewPlanParams(options: ReviewPlanOptions): string {
    const params: string[] = [];

    if (options.planType) {
      params.push(`--plan-type=${options.planType}`);
    }
    if (options.difficulty) {
      params.push(`--difficulty=${options.difficulty}`);
    }
    if (options.duration !== undefined) {
      params.push(`--duration=${options.duration}`);
    }
    if (options.maxConcepts !== undefined) {
      params.push(`--max-concepts=${options.maxConcepts}`);
    }
    if (options.focusAreas && options.focusAreas.length > 0) {
      params.push(`--focus-areas=${options.focusAreas.join(',')}`);
    }

    return params.join(' ');
  }

  // ==========================================================================
  // Private Methods - Filtering
  // ==========================================================================

  /**
   * Apply filters to task array
   *
   * @param tasks - Tasks to filter
   * @param options - Filter options
   * @returns Filtered tasks
   */
  private applyTaskFilters(tasks: ReviewTask[], options?: ReviewOptions): ReviewTask[] {
    if (!options) return tasks;

    let filtered = [...tasks];

    // Filter by canvas ID
    if (options.canvasId) {
      filtered = filtered.filter(t => t.canvasId === options.canvasId);
    }

    // Filter by priority
    if (options.priority) {
      filtered = filtered.filter(t => t.priority === options.priority);
    }

    // Filter by due date
    if (options.dueBefore) {
      filtered = filtered.filter(t => t.dueDate <= options.dueBefore!);
    }

    // Sort
    if (options.sortBy) {
      const order = options.sortOrder === 'desc' ? -1 : 1;
      filtered.sort((a, b) => {
        const aVal = a[options.sortBy!];
        const bVal = b[options.sortBy!];

        if (aVal instanceof Date && bVal instanceof Date) {
          return (aVal.getTime() - bVal.getTime()) * order;
        }
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return (aVal - bVal) * order;
        }
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return aVal.localeCompare(bVal) * order;
        }
        return 0;
      });
    }

    // Limit
    if (options.limit && options.limit > 0) {
      filtered = filtered.slice(0, options.limit);
    }

    return filtered;
  }

  // ==========================================================================
  // Private Methods - Error Handling
  // ==========================================================================

  /**
   * Create an execution error from result
   *
   * @param result - Command result
   * @param defaultMessage - Default error message
   * @returns Error to throw
   */
  private createExecutionError(result: CommandResult, defaultMessage: string): Error {
    const message = result.error ?? defaultMessage;
    return new Error(message);
  }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a CommandWrapper instance with default configuration
 *
 * @param baseUrl - API base URL
 * @param apiKey - Optional API key
 * @returns Configured CommandWrapper instance
 */
export function createCommandWrapper(
  baseUrl: string,
  apiKey?: string
): CommandWrapper {
  return new CommandWrapper({
    executorConfig: {
      baseUrl,
      apiKey,
    },
    cacheTtl: DEFAULT_CACHE_TTL,
    enablePersistentCache: false,
  });
}

/**
 * Create a CommandWrapper instance for testing
 *
 * @returns CommandWrapper with mock executor
 */
export function createMockCommandWrapper(): CommandWrapper {
  return new CommandWrapper({
    executorConfig: {
      baseUrl: 'http://localhost:3000',
    },
    useMockExecutor: true,
  });
}
