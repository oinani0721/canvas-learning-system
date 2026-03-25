/**
 * ReviewOutputParser - Parser for /review show command output
 *
 * Implements AC-3: Command output parsing with JSON and text fallback.
 * Parses output from /review show command into ReviewTask[] array.
 *
 * @module ReviewOutputParser
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Output Parser Implementation
 */

import type {
  OutputParser,
  ReviewTask,
  ReviewPriority,
  CommandExecutionError,
} from '../types/ReviewTypes';

// ============================================================================
// Types
// ============================================================================

/**
 * Raw task data from API response
 */
interface RawTaskData {
  id?: string;
  canvas_id?: string;
  canvasId?: string;
  canvas_title?: string;
  canvasTitle?: string;
  concept_name?: string;
  conceptName?: string;
  priority?: string | number;
  urgency?: number;
  memory_strength?: number;
  memoryStrength?: number;
  retention_rate?: number;
  retentionRate?: number;
  forgetting_curve_position?: number;
  forgettingCurvePosition?: number;
  due_date?: string;
  dueDate?: string;
  overdue_days?: number;
  overdueDays?: number;
  estimated_duration?: number;
  estimatedDuration?: number;
  last_review_date?: string;
  lastReviewDate?: string;
  streak?: number;
  skip_count?: number;
  skipCount?: number;
}

/**
 * Raw API response structure
 */
interface RawApiResponse {
  tasks?: RawTaskData[];
  items?: RawTaskData[];
  data?: RawTaskData[];
  reviews?: RawTaskData[];
}

// ============================================================================
// ReviewOutputParser Class
// ============================================================================

/**
 * Parser for /review show command output
 *
 * Supports both JSON and text output formats with graceful fallback.
 * Source: Story 13.4 Dev Notes - ReviewOutputParser
 */
export class ReviewOutputParser implements OutputParser<ReviewTask[]> {
  // ==========================================================================
  // Public Methods
  // ==========================================================================

  /**
   * Parse command output into ReviewTask array
   *
   * @param output - Raw command output
   * @returns Array of ReviewTask objects
   * @throws Error if parsing completely fails
   */
  parse(output: string): ReviewTask[] {
    if (!output || typeof output !== 'string') {
      return [];
    }

    const trimmedOutput = output.trim();
    if (!trimmedOutput) {
      return [];
    }

    // Try JSON parsing first
    try {
      const data = JSON.parse(trimmedOutput);
      return this.transformToReviewTasks(data);
    } catch {
      // Fallback to text parsing
      return this.parseTextOutput(trimmedOutput);
    }
  }

  // ==========================================================================
  // Private Methods - JSON Parsing
  // ==========================================================================

  /**
   * Transform JSON data to ReviewTask array
   *
   * @param data - Parsed JSON data
   * @returns Array of ReviewTask objects
   */
  private transformToReviewTasks(data: RawApiResponse | RawTaskData[]): ReviewTask[] {
    // Handle different response formats
    let tasks: RawTaskData[] = [];

    if (Array.isArray(data)) {
      tasks = data;
    } else if (data.tasks) {
      tasks = data.tasks;
    } else if (data.items) {
      tasks = data.items;
    } else if (data.data) {
      tasks = data.data;
    } else if (data.reviews) {
      tasks = data.reviews;
    }

    return tasks
      .filter((task): task is RawTaskData => task !== null && task !== undefined)
      .map(task => this.transformSingleTask(task));
  }

  /**
   * Transform a single raw task to ReviewTask
   *
   * @param task - Raw task data
   * @returns ReviewTask object
   */
  private transformSingleTask(task: RawTaskData): ReviewTask {
    return {
      id: task.id ?? this.generateId(),
      canvasId: task.canvas_id ?? task.canvasId ?? '',
      canvasTitle: task.canvas_title ?? task.canvasTitle ?? '',
      conceptName: task.concept_name ?? task.conceptName ?? '',
      priority: this.mapPriority(task.priority),
      urgency: this.normalizeNumber(task.urgency, 0, 100, 0),
      memoryStrength: this.normalizeNumber(
        task.memory_strength ?? task.memoryStrength,
        0,
        100,
        50
      ),
      retentionRate: this.normalizeNumber(
        task.retention_rate ?? task.retentionRate,
        0,
        100,
        100
      ),
      forgettingCurvePosition: this.normalizeNumber(
        task.forgetting_curve_position ?? task.forgettingCurvePosition,
        0,
        100,
        0
      ),
      dueDate: this.parseDate(task.due_date ?? task.dueDate) ?? new Date(),
      overdueDays: task.overdue_days ?? task.overdueDays ?? 0,
      estimatedDuration: task.estimated_duration ?? task.estimatedDuration ?? 15,
      lastReviewDate: this.parseDate(task.last_review_date ?? task.lastReviewDate),
      streak: task.streak ?? 0,
      skipCount: task.skip_count ?? task.skipCount ?? 0,
    };
  }

  // ==========================================================================
  // Private Methods - Text Parsing (Fallback)
  // ==========================================================================

  /**
   * Parse text output format (fallback)
   *
   * Handles various text formats from CLI output.
   *
   * @param output - Text output to parse
   * @returns Array of ReviewTask objects
   */
  private parseTextOutput(output: string): ReviewTask[] {
    const tasks: ReviewTask[] = [];
    const lines = output.split('\n').filter(line => line.trim());

    let currentTask: Partial<ReviewTask> | null = null;

    for (const line of lines) {
      // Check for task header patterns
      const taskMatch = line.match(/^(?:Task|Review|Item)\s*[#:]?\s*(\d+|[\w-]+)/i);
      if (taskMatch) {
        if (currentTask && currentTask.id) {
          tasks.push(this.completePartialTask(currentTask));
        }
        currentTask = { id: taskMatch[1] };
        continue;
      }

      // Parse key-value pairs within task
      if (currentTask) {
        this.parseTextLine(line, currentTask);
      } else {
        // Try to parse standalone lines
        const standaloneTask = this.parseStandaloneLine(line);
        if (standaloneTask) {
          tasks.push(standaloneTask);
        }
      }
    }

    // Don't forget the last task
    if (currentTask && currentTask.id) {
      tasks.push(this.completePartialTask(currentTask));
    }

    return tasks;
  }

  /**
   * Parse a single line for key-value data
   *
   * @param line - Line to parse
   * @param task - Task object to populate
   */
  private parseTextLine(line: string, task: Partial<ReviewTask>): void {
    const keyValueMatch = line.match(/^\s*[-*]?\s*([\w\s]+):\s*(.+)$/);
    if (!keyValueMatch) return;

    const [, key, value] = keyValueMatch;
    const normalizedKey = key.toLowerCase().trim().replace(/\s+/g, '_');

    switch (normalizedKey) {
      case 'canvas':
      case 'canvas_id':
        task.canvasId = value.trim();
        break;
      case 'canvas_title':
      case 'title':
        task.canvasTitle = value.trim();
        break;
      case 'concept':
      case 'concept_name':
        task.conceptName = value.trim();
        break;
      case 'priority':
        task.priority = this.mapPriority(value.trim());
        break;
      case 'urgency':
        task.urgency = parseInt(value.trim(), 10) || 0;
        break;
      case 'due':
      case 'due_date':
        task.dueDate = this.parseDate(value.trim());
        break;
      case 'strength':
      case 'memory_strength':
        task.memoryStrength = parseInt(value.trim(), 10) || 50;
        break;
      case 'duration':
      case 'estimated_duration':
        task.estimatedDuration = parseInt(value.trim(), 10) || 15;
        break;
    }
  }

  /**
   * Try to parse a standalone line as a task
   *
   * @param line - Line to parse
   * @returns ReviewTask or null
   */
  private parseStandaloneLine(line: string): ReviewTask | null {
    // Pattern: "- ConceptName (canvas: CanvasName, priority: high, due: 2025-01-20)"
    const match = line.match(
      /[-*]\s*([^(]+)\s*\((?:.*canvas:\s*([^,)]+))?(?:.*priority:\s*(\w+))?(?:.*due:\s*([^,)]+))?\)/i
    );

    if (match) {
      const [, conceptName, canvasId, priority, dueDate] = match;
      return {
        id: this.generateId(),
        canvasId: canvasId?.trim() ?? '',
        canvasTitle: canvasId?.trim() ?? '',
        conceptName: conceptName.trim(),
        priority: this.mapPriority(priority),
        urgency: 0,
        memoryStrength: 50,
        retentionRate: 100,
        forgettingCurvePosition: 0,
        dueDate: this.parseDate(dueDate) ?? new Date(),
        overdueDays: 0,
        estimatedDuration: 15,
        streak: 0,
        skipCount: 0,
      };
    }

    return null;
  }

  /**
   * Complete a partial task with defaults
   *
   * @param partial - Partial task data
   * @returns Complete ReviewTask
   */
  private completePartialTask(partial: Partial<ReviewTask>): ReviewTask {
    return {
      id: partial.id ?? this.generateId(),
      canvasId: partial.canvasId ?? '',
      canvasTitle: partial.canvasTitle ?? '',
      conceptName: partial.conceptName ?? '',
      priority: partial.priority ?? 'medium',
      urgency: partial.urgency ?? 0,
      memoryStrength: partial.memoryStrength ?? 50,
      retentionRate: partial.retentionRate ?? 100,
      forgettingCurvePosition: partial.forgettingCurvePosition ?? 0,
      dueDate: partial.dueDate ?? new Date(),
      overdueDays: partial.overdueDays ?? 0,
      estimatedDuration: partial.estimatedDuration ?? 15,
      lastReviewDate: partial.lastReviewDate,
      streak: partial.streak ?? 0,
      skipCount: partial.skipCount ?? 0,
    };
  }

  // ==========================================================================
  // Private Methods - Utilities
  // ==========================================================================

  /**
   * Map priority value to ReviewPriority enum
   *
   * @param priority - Priority value (string or number)
   * @returns ReviewPriority value
   */
  private mapPriority(priority?: string | number): ReviewPriority {
    if (priority === undefined || priority === null) {
      return 'medium';
    }

    const priorityStr = String(priority).toLowerCase().trim();

    switch (priorityStr) {
      case 'critical':
      case '4':
      case 'urgent':
        return 'critical';
      case 'high':
      case '3':
        return 'high';
      case 'medium':
      case 'normal':
      case '2':
        return 'medium';
      case 'low':
      case '1':
      case '0':
        return 'low';
      default:
        return 'medium';
    }
  }

  /**
   * Normalize a number to a range
   *
   * @param value - Value to normalize
   * @param min - Minimum allowed value
   * @param max - Maximum allowed value
   * @param defaultValue - Default if value is invalid
   * @returns Normalized number
   */
  private normalizeNumber(
    value: number | undefined,
    min: number,
    max: number,
    defaultValue: number
  ): number {
    if (value === undefined || value === null || isNaN(value)) {
      return defaultValue;
    }
    return Math.max(min, Math.min(max, value));
  }

  /**
   * Parse date string to Date object
   *
   * @param dateStr - Date string to parse
   * @returns Date object or undefined
   */
  private parseDate(dateStr?: string): Date | undefined {
    if (!dateStr) return undefined;

    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? undefined : date;
  }

  /**
   * Generate a unique ID
   *
   * @returns Unique identifier string
   */
  private generateId(): string {
    return `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
