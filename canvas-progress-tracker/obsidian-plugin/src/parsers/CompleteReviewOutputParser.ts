/**
 * CompleteReviewOutputParser - Parser for /review complete command output
 *
 * Implements AC-3: Command output parsing for review completion.
 * Parses output from /review complete command into ReviewResult object.
 *
 * @module CompleteReviewOutputParser
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Output Parser Implementation
 */

import type {
  OutputParser,
  ReviewResult,
  ScoreBreakdown,
  ReviewStatistics,
} from '../types/ReviewTypes';

// ============================================================================
// Types
// ============================================================================

/**
 * Raw score breakdown from API response
 */
interface RawScoreBreakdown {
  accuracy?: number;
  imagery?: number;
  completeness?: number;
  originality?: number;
}

/**
 * Raw statistics from API response
 */
interface RawStatistics {
  concepts_reviewed?: number;
  conceptsReviewed?: number;
  concepts_passed?: number;
  conceptsPassed?: number;
  concepts_failed?: number;
  conceptsFailed?: number;
  average_score?: number;
  averageScore?: number;
  time_spent?: number;
  timeSpent?: number;
}

/**
 * Raw result data from API response
 */
interface RawResultData {
  success?: boolean;
  task_id?: string;
  taskId?: string;
  canvas_id?: string;
  canvasId?: string;
  scores?: RawScoreBreakdown;
  total_score?: number;
  totalScore?: number;
  score?: number;
  passed?: boolean;
  pass_threshold?: number;
  passThreshold?: number;
  statistics?: RawStatistics;
  stats?: RawStatistics;
  feedback?: string;
  message?: string;
  completed_at?: string;
  completedAt?: string;
  timestamp?: string;
}

/**
 * Raw API response structure
 */
interface RawApiResponse {
  result?: RawResultData;
  data?: RawResultData;
  review?: RawResultData;
}

// ============================================================================
// CompleteReviewOutputParser Class
// ============================================================================

/**
 * Parser for /review complete command output
 *
 * Supports both JSON and text output formats with graceful fallback.
 * Source: Story 13.4 Dev Notes - CompleteReviewOutputParser
 */
export class CompleteReviewOutputParser implements OutputParser<ReviewResult> {
  // ==========================================================================
  // Public Methods
  // ==========================================================================

  /**
   * Parse command output into ReviewResult
   *
   * @param output - Raw command output
   * @returns ReviewResult object
   * @throws Error if parsing completely fails
   */
  parse(output: string): ReviewResult {
    if (!output || typeof output !== 'string') {
      return this.createEmptyResult();
    }

    const trimmedOutput = output.trim();
    if (!trimmedOutput) {
      return this.createEmptyResult();
    }

    // Try JSON parsing first
    try {
      const data = JSON.parse(trimmedOutput);
      return this.transformToReviewResult(data);
    } catch {
      // Fallback to text parsing
      return this.parseTextOutput(trimmedOutput);
    }
  }

  // ==========================================================================
  // Private Methods - JSON Parsing
  // ==========================================================================

  /**
   * Transform JSON data to ReviewResult
   *
   * @param data - Parsed JSON data
   * @returns ReviewResult object
   */
  private transformToReviewResult(data: RawApiResponse | RawResultData): ReviewResult {
    // Handle different response formats
    let resultData: RawResultData;

    if ('result' in data && data.result) {
      resultData = data.result;
    } else if ('data' in data && data.data) {
      resultData = data.data;
    } else if ('review' in data && data.review) {
      resultData = data.review;
    } else {
      resultData = data as RawResultData;
    }

    const totalScore = resultData.total_score ?? resultData.totalScore ?? resultData.score ?? 0;
    const passThreshold = resultData.pass_threshold ?? resultData.passThreshold ?? 60;

    return {
      success: resultData.success ?? true,
      taskId: resultData.task_id ?? resultData.taskId ?? '',
      canvasId: resultData.canvas_id ?? resultData.canvasId ?? '',
      scores: this.transformScores(resultData.scores),
      totalScore: this.normalizeNumber(totalScore, 0, 100, 0),
      passed: resultData.passed ?? totalScore >= passThreshold,
      passThreshold,
      statistics: this.transformStatistics(resultData.statistics ?? resultData.stats),
      feedback: resultData.feedback ?? resultData.message,
      completedAt: this.parseDate(
        resultData.completed_at ?? resultData.completedAt ?? resultData.timestamp
      ) ?? new Date(),
    };
  }

  /**
   * Transform raw scores to ScoreBreakdown
   *
   * @param scores - Raw score data
   * @returns ScoreBreakdown object
   */
  private transformScores(scores?: RawScoreBreakdown): ScoreBreakdown {
    if (!scores) {
      return {
        accuracy: 0,
        imagery: 0,
        completeness: 0,
        originality: 0,
      };
    }

    return {
      accuracy: this.normalizeNumber(scores.accuracy, 0, 25, 0),
      imagery: this.normalizeNumber(scores.imagery, 0, 25, 0),
      completeness: this.normalizeNumber(scores.completeness, 0, 25, 0),
      originality: this.normalizeNumber(scores.originality, 0, 25, 0),
    };
  }

  /**
   * Transform raw statistics to ReviewStatistics
   *
   * @param stats - Raw statistics data
   * @returns ReviewStatistics object
   */
  private transformStatistics(stats?: RawStatistics): ReviewStatistics {
    if (!stats) {
      return {
        conceptsReviewed: 0,
        conceptsPassed: 0,
        conceptsFailed: 0,
        averageScore: 0,
        timeSpent: 0,
      };
    }

    return {
      conceptsReviewed: stats.concepts_reviewed ?? stats.conceptsReviewed ?? 0,
      conceptsPassed: stats.concepts_passed ?? stats.conceptsPassed ?? 0,
      conceptsFailed: stats.concepts_failed ?? stats.conceptsFailed ?? 0,
      averageScore: stats.average_score ?? stats.averageScore ?? 0,
      timeSpent: stats.time_spent ?? stats.timeSpent ?? 0,
    };
  }

  // ==========================================================================
  // Private Methods - Text Parsing (Fallback)
  // ==========================================================================

  /**
   * Parse text output format (fallback)
   *
   * @param output - Text output to parse
   * @returns ReviewResult object
   */
  private parseTextOutput(output: string): ReviewResult {
    const result = this.createEmptyResult();
    const lines = output.split('\n').filter(line => line.trim());

    for (const line of lines) {
      this.parseResultLine(line, result);
    }

    // Calculate derived values if not set
    if (result.totalScore === 0) {
      const { accuracy, imagery, completeness, originality } = result.scores;
      result.totalScore = accuracy + imagery + completeness + originality;
    }

    if (result.passed === false && result.totalScore >= result.passThreshold) {
      result.passed = true;
    }

    return result;
  }

  /**
   * Parse a result property line
   *
   * @param line - Line to parse
   * @param result - Result object to update
   */
  private parseResultLine(line: string, result: ReviewResult): void {
    const keyValueMatch = line.match(/^\s*[-*]?\s*([\w\s]+):\s*(.+)$/);
    if (!keyValueMatch) {
      // Try to parse success/failure indicators
      this.parseStatusLine(line, result);
      return;
    }

    const [, key, value] = keyValueMatch;
    const normalizedKey = key.toLowerCase().trim().replace(/\s+/g, '_');

    switch (normalizedKey) {
      case 'task':
      case 'task_id':
        result.taskId = value.trim();
        break;
      case 'canvas':
      case 'canvas_id':
        result.canvasId = value.trim();
        break;
      case 'total':
      case 'total_score':
      case 'score':
        result.totalScore = this.parseScore(value);
        break;
      case 'accuracy':
        result.scores.accuracy = this.parseScore(value, 25);
        break;
      case 'imagery':
      case 'visualization':
        result.scores.imagery = this.parseScore(value, 25);
        break;
      case 'completeness':
        result.scores.completeness = this.parseScore(value, 25);
        break;
      case 'originality':
        result.scores.originality = this.parseScore(value, 25);
        break;
      case 'passed':
      case 'pass':
        result.passed = this.parseBoolean(value);
        break;
      case 'threshold':
      case 'pass_threshold':
        result.passThreshold = parseInt(value.trim(), 10) || 60;
        break;
      case 'feedback':
      case 'message':
      case 'notes':
        result.feedback = value.trim();
        break;
      case 'time':
      case 'time_spent':
        result.statistics.timeSpent = parseInt(value.trim(), 10) || 0;
        break;
      case 'concepts_reviewed':
      case 'reviewed':
        result.statistics.conceptsReviewed = parseInt(value.trim(), 10) || 0;
        break;
    }
  }

  /**
   * Parse status indicator lines
   *
   * @param line - Line to parse
   * @param result - Result object to update
   */
  private parseStatusLine(line: string, result: ReviewResult): void {
    const lowerLine = line.toLowerCase();

    // Check for success indicators
    if (
      lowerLine.includes('success') ||
      lowerLine.includes('passed') ||
      lowerLine.includes('completed successfully')
    ) {
      result.success = true;
      result.passed = true;
    }

    // Check for failure indicators
    if (
      lowerLine.includes('failed') ||
      lowerLine.includes('not passed') ||
      lowerLine.includes('error')
    ) {
      result.passed = false;
    }

    // Try to extract score from line like "Score: 85/100" or "85 points"
    const scoreMatch = line.match(/(\d+)\s*(?:\/\s*100|points?|%)/i);
    if (scoreMatch && result.totalScore === 0) {
      result.totalScore = parseInt(scoreMatch[1], 10);
    }
  }

  // ==========================================================================
  // Private Methods - Utilities
  // ==========================================================================

  /**
   * Create an empty result with defaults
   *
   * @returns Empty ReviewResult
   */
  private createEmptyResult(): ReviewResult {
    return {
      success: false,
      taskId: '',
      canvasId: '',
      scores: {
        accuracy: 0,
        imagery: 0,
        completeness: 0,
        originality: 0,
      },
      totalScore: 0,
      passed: false,
      passThreshold: 60,
      statistics: {
        conceptsReviewed: 0,
        conceptsPassed: 0,
        conceptsFailed: 0,
        averageScore: 0,
        timeSpent: 0,
      },
      completedAt: new Date(),
    };
  }

  /**
   * Parse a score value from string
   *
   * @param value - String value to parse
   * @param max - Maximum allowed value (default 100)
   * @returns Parsed score number
   */
  private parseScore(value: string, max: number = 100): number {
    // Handle formats like "85", "85/100", "85%", "85 points"
    const match = value.match(/(\d+(?:\.\d+)?)/);
    if (!match) return 0;

    const score = parseFloat(match[1]);
    return this.normalizeNumber(score, 0, max, 0);
  }

  /**
   * Parse a boolean value from string
   *
   * @param value - String value to parse
   * @returns Boolean value
   */
  private parseBoolean(value: string): boolean {
    const normalized = value.toLowerCase().trim();
    return (
      normalized === 'true' ||
      normalized === 'yes' ||
      normalized === 'passed' ||
      normalized === '1'
    );
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
}
