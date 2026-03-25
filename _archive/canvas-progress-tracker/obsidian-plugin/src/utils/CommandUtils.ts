/**
 * CommandUtils - Utility functions for command operations
 *
 * Provides helper functions for command validation, formatting,
 * and common operations.
 *
 * @module CommandUtils
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Command Utility Functions
 */

import type { ReviewPriority, ReviewDifficulty, ReviewPlanType } from '../types/ReviewTypes';

// ============================================================================
// Command Validation
// ============================================================================

/**
 * Validate a command string
 *
 * @param command - Command to validate
 * @returns True if valid, false otherwise
 */
export function isValidCommand(command: string): boolean {
  if (!command || typeof command !== 'string') {
    return false;
  }

  const trimmed = command.trim();
  if (trimmed.length === 0) {
    return false;
  }

  // Check for dangerous patterns
  const dangerousPatterns = [/[;&|`$]/, /\n/, /\r/];
  for (const pattern of dangerousPatterns) {
    if (pattern.test(trimmed)) {
      return false;
    }
  }

  return true;
}

/**
 * Sanitize a command string
 *
 * @param command - Command to sanitize
 * @returns Sanitized command
 */
export function sanitizeCommand(command: string): string {
  if (!command) return '';

  return command
    .trim()
    .replace(/[;&|`$]/g, '')
    .replace(/[\n\r]/g, ' ')
    .replace(/\s+/g, ' ');
}

// ============================================================================
// Priority Utilities
// ============================================================================

/**
 * Priority weight mapping for sorting
 */
const PRIORITY_WEIGHTS: Record<ReviewPriority, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

/**
 * Get numeric weight for a priority
 *
 * @param priority - Priority value
 * @returns Numeric weight
 */
export function getPriorityWeight(priority: ReviewPriority): number {
  return PRIORITY_WEIGHTS[priority] ?? 2;
}

/**
 * Compare two priorities
 *
 * @param a - First priority
 * @param b - Second priority
 * @returns Comparison result (-1, 0, 1)
 */
export function comparePriorities(a: ReviewPriority, b: ReviewPriority): number {
  return getPriorityWeight(b) - getPriorityWeight(a);
}

/**
 * Get display label for priority
 *
 * @param priority - Priority value
 * @returns Display label
 */
export function getPriorityLabel(priority: ReviewPriority): string {
  const labels: Record<ReviewPriority, string> = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };
  return labels[priority] ?? 'Unknown';
}

/**
 * Get CSS class for priority styling
 *
 * @param priority - Priority value
 * @returns CSS class name
 */
export function getPriorityClass(priority: ReviewPriority): string {
  return `priority-${priority}`;
}

// ============================================================================
// Difficulty Utilities
// ============================================================================

/**
 * Get display label for difficulty
 *
 * @param difficulty - Difficulty value
 * @returns Display label
 */
export function getDifficultyLabel(difficulty: ReviewDifficulty): string {
  const labels: Record<ReviewDifficulty, string> = {
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard',
    adaptive: 'Adaptive',
  };
  return labels[difficulty] ?? 'Unknown';
}

// ============================================================================
// Plan Type Utilities
// ============================================================================

/**
 * Get display label for plan type
 *
 * @param planType - Plan type value
 * @returns Display label
 */
export function getPlanTypeLabel(planType: ReviewPlanType): string {
  const labels: Record<ReviewPlanType, string> = {
    'weakness-focused': 'Weakness Focused',
    comprehensive: 'Comprehensive',
    targeted: 'Targeted',
  };
  return labels[planType] ?? 'Unknown';
}

/**
 * Get description for plan type
 *
 * @param planType - Plan type value
 * @returns Description
 */
export function getPlanTypeDescription(planType: ReviewPlanType): string {
  const descriptions: Record<ReviewPlanType, string> = {
    'weakness-focused': 'Focus on areas that need improvement',
    comprehensive: 'Cover all topics systematically',
    targeted: 'Focus on specific selected areas',
  };
  return descriptions[planType] ?? '';
}

// ============================================================================
// Date Utilities
// ============================================================================

/**
 * Format a date for display
 *
 * @param date - Date to format
 * @param format - Format type ('short', 'long', 'relative')
 * @returns Formatted date string
 */
export function formatDate(
  date: Date,
  format: 'short' | 'long' | 'relative' = 'short'
): string {
  if (!date || isNaN(date.getTime())) {
    return 'Invalid date';
  }

  switch (format) {
    case 'short':
      return date.toLocaleDateString();
    case 'long':
      return date.toLocaleDateString(undefined, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    case 'relative':
      return formatRelativeDate(date);
    default:
      return date.toLocaleDateString();
  }
}

/**
 * Format a date relative to now
 *
 * @param date - Date to format
 * @returns Relative date string
 */
export function formatRelativeDate(date: Date): string {
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Tomorrow';
  } else if (diffDays === -1) {
    return 'Yesterday';
  } else if (diffDays > 0 && diffDays <= 7) {
    return `In ${diffDays} days`;
  } else if (diffDays < 0 && diffDays >= -7) {
    return `${Math.abs(diffDays)} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

/**
 * Calculate days until a date
 *
 * @param date - Target date
 * @returns Days until date (negative if past)
 */
export function daysUntil(date: Date): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

// ============================================================================
// Duration Utilities
// ============================================================================

/**
 * Format duration in minutes
 *
 * @param minutes - Duration in minutes
 * @returns Formatted duration string
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (remainingMinutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${remainingMinutes} min`;
}

// ============================================================================
// Score Utilities
// ============================================================================

/**
 * Get color class for a score
 *
 * @param score - Score value (0-100)
 * @returns CSS class name
 */
export function getScoreClass(score: number): string {
  if (score >= 80) return 'score-excellent';
  if (score >= 60) return 'score-good';
  if (score >= 40) return 'score-fair';
  return 'score-poor';
}

/**
 * Get label for a score
 *
 * @param score - Score value (0-100)
 * @returns Score label
 */
export function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Fair';
  return 'Needs Improvement';
}

/**
 * Format a score for display
 *
 * @param score - Score value
 * @param maxScore - Maximum score (default 100)
 * @returns Formatted score string
 */
export function formatScore(score: number, maxScore: number = 100): string {
  return `${Math.round(score)}/${maxScore}`;
}

// ============================================================================
// Memory Strength Utilities
// ============================================================================

/**
 * Get description for memory strength
 *
 * @param strength - Memory strength (0-100)
 * @returns Description string
 */
export function getMemoryStrengthDescription(strength: number): string {
  if (strength >= 80) return 'Strong';
  if (strength >= 60) return 'Moderate';
  if (strength >= 40) return 'Weak';
  return 'Very Weak';
}

/**
 * Get color class for memory strength
 *
 * @param strength - Memory strength (0-100)
 * @returns CSS class name
 */
export function getMemoryStrengthClass(strength: number): string {
  if (strength >= 80) return 'memory-strong';
  if (strength >= 60) return 'memory-moderate';
  if (strength >= 40) return 'memory-weak';
  return 'memory-critical';
}

// ============================================================================
// Cache Key Utilities
// ============================================================================

/**
 * Generate a deterministic hash for cache keys
 *
 * @param str - String to hash
 * @returns Hash string
 */
export function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36);
}

/**
 * Create a cache key from command and options
 *
 * @param command - Command string
 * @param options - Command options
 * @returns Cache key
 */
export function createCacheKey(command: string, options?: Record<string, unknown>): string {
  const optionsStr = options ? JSON.stringify(options) : '';
  return `cmd:${simpleHash(command)}:${simpleHash(optionsStr)}`;
}

// ============================================================================
// Retry Utilities
// ============================================================================

/**
 * Calculate exponential backoff delay
 *
 * @param attempt - Attempt number (0-based)
 * @param baseDelay - Base delay in ms (default 1000)
 * @param maxDelay - Maximum delay in ms (default 30000)
 * @returns Delay in milliseconds
 */
export function calculateBackoff(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 30000
): number {
  const delay = Math.pow(2, attempt) * baseDelay;
  return Math.min(delay, maxDelay);
}

/**
 * Sleep for a specified duration
 *
 * @param ms - Duration in milliseconds
 * @returns Promise that resolves after delay
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
