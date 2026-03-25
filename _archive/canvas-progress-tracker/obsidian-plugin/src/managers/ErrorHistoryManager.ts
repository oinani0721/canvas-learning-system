/**
 * Canvas Learning System - Error History Manager
 *
 * Manages persistent storage of error records for the plugin.
 * Implements AC 4 and AC 5 of Story 21.5.5:
 * - Error history viewable in settings panel
 * - Auto-cleanup of records older than 7 days
 *
 * @source Story 21.5.5 - 任务3: 实现错误历史存储
 * @source ADR-009 - Error Handling & Retry Strategy
 */

import type { Plugin } from 'obsidian';
import { ApiError, ErrorType } from '../api/types';

// ═══════════════════════════════════════════════════════════════════════════════
// Types and Interfaces
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Error record stored in plugin data
 * @source Story 21.5.5 - 任务3.1: ErrorRecord接口
 */
export interface ErrorRecord {
  /** Unique identifier for the error record */
  id: string;
  /** Unix timestamp when error occurred */
  timestamp: number;
  /** Error type (our classification) */
  errorType: ErrorType;
  /** Backend error type name (if available) */
  backendErrorType?: string;
  /** Bug tracking ID from backend (format: BUG-XXXXXXXX) */
  bugId?: string;
  /** Error message */
  message: string;
  /** Operation that caused the error (e.g., 'decompose_basic') */
  operation: string;
  /** HTTP status code (if applicable) */
  statusCode?: number;
  /** Additional error details */
  details?: Record<string, unknown>;
}

/**
 * Plugin data structure for error history
 */
interface PluginErrorData {
  errorHistory?: ErrorRecord[];
  lastCleanup?: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Maximum number of error records to keep */
const MAX_RECORDS = 100;

/** Number of days before records expire */
const EXPIRY_DAYS = 7;

/** Milliseconds per day */
const MS_PER_DAY = 24 * 60 * 60 * 1000;

// ═══════════════════════════════════════════════════════════════════════════════
// ErrorHistoryManager Class
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manager for persistent error history storage
 *
 * Features:
 * - Persists error records using Obsidian plugin data API
 * - Auto-cleanup of records older than 7 days
 * - Maximum 100 records limit
 * - Thread-safe record operations
 *
 * @source Story 21.5.5 - AC 4, 5
 *
 * @example
 * ```typescript
 * // Initialize in plugin onload
 * this.errorHistoryManager = new ErrorHistoryManager(this);
 * await this.errorHistoryManager.load();
 *
 * // Add error after API call failure
 * this.errorHistoryManager.addError(apiError, 'decompose_basic');
 *
 * // Get recent errors for display
 * const recentErrors = this.errorHistoryManager.getRecent(20);
 * ```
 */
export class ErrorHistoryManager {
  /** In-memory cache of error records */
  private records: ErrorRecord[] = [];

  /** Flag to prevent concurrent saves */
  private isSaving = false;

  /** Pending save operation */
  private pendingSave: Promise<void> | null = null;

  /**
   * Create a new ErrorHistoryManager
   *
   * @param plugin - The Obsidian plugin instance (for loadData/saveData)
   */
  constructor(private plugin: Plugin) {}

  // ═══════════════════════════════════════════════════════════════════════════
  // Public Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Load error history from plugin data storage
   *
   * Should be called in plugin's onload() method.
   * Automatically runs cleanup after loading.
   *
   * @source Story 21.5.5 - 任务3.1
   */
  async load(): Promise<void> {
    try {
      const data = (await this.plugin.loadData()) as PluginErrorData | null;
      this.records = data?.errorHistory || [];

      // Run cleanup on load
      // @source Story 21.5.5 - AC 5: 插件启动时自动清理过期错误
      await this.cleanup();
    } catch (error) {
      console.error('[ErrorHistoryManager] Failed to load error history:', error);
      this.records = [];
    }
  }

  /**
   * Save error history to plugin data storage
   *
   * Uses debouncing to prevent excessive writes.
   *
   * @source Story 21.5.5 - 任务3.1
   */
  async save(): Promise<void> {
    // If already saving, queue this save
    if (this.isSaving) {
      if (!this.pendingSave) {
        this.pendingSave = new Promise((resolve) => {
          setTimeout(async () => {
            this.pendingSave = null;
            await this.save();
            resolve();
          }, 100);
        });
      }
      return this.pendingSave;
    }

    this.isSaving = true;

    try {
      const data = ((await this.plugin.loadData()) as PluginErrorData) || {};
      data.errorHistory = this.records;
      data.lastCleanup = Date.now();
      await this.plugin.saveData(data);
    } catch (error) {
      console.error('[ErrorHistoryManager] Failed to save error history:', error);
    } finally {
      this.isSaving = false;
    }
  }

  /**
   * Add a new error record
   *
   * @param error - The ApiError to record
   * @param operation - Name of the operation that failed
   *
   * @source Story 21.5.5 - 任务3.1
   */
  addError(error: ApiError, operation: string): ErrorRecord {
    const record: ErrorRecord = {
      id: this.generateId(),
      timestamp: Date.now(),
      errorType: error.type,
      backendErrorType: error.backendErrorType,
      bugId: error.bugId,
      message: error.message,
      operation,
      statusCode: error.statusCode,
      details: error.details,
    };

    // Add to beginning of array (most recent first)
    this.records.unshift(record);

    // Enforce max records limit
    if (this.records.length > MAX_RECORDS) {
      this.records = this.records.slice(0, MAX_RECORDS);
    }

    // Save asynchronously (don't block caller)
    this.save();

    return record;
  }

  /**
   * Get recent error records
   *
   * @param limit - Maximum number of records to return (default: 20)
   * @returns Array of error records, most recent first
   *
   * @source Story 21.5.5 - AC 4: 显示最近20条错误记录
   */
  getRecent(limit: number = 20): ErrorRecord[] {
    return this.records.slice(0, Math.min(limit, this.records.length));
  }

  /**
   * Get all error records
   *
   * @returns All stored error records
   */
  getAll(): ErrorRecord[] {
    return [...this.records];
  }

  /**
   * Get error record by ID
   *
   * @param id - Error record ID
   * @returns The error record or undefined
   */
  getById(id: string): ErrorRecord | undefined {
    return this.records.find((r) => r.id === id);
  }

  /**
   * Get error record by bug ID
   *
   * @param bugId - Bug tracking ID (format: BUG-XXXXXXXX)
   * @returns The error record or undefined
   */
  getByBugId(bugId: string): ErrorRecord | undefined {
    return this.records.find((r) => r.bugId === bugId);
  }

  /**
   * Get total count of stored records
   */
  getCount(): number {
    return this.records.length;
  }

  /**
   * Clean up expired error records
   *
   * Removes records older than EXPIRY_DAYS (7 days).
   * Called automatically on load and can be called manually.
   *
   * @source Story 21.5.5 - AC 5: 自动清理超过7天的错误历史
   */
  async cleanup(): Promise<number> {
    const expiryTime = Date.now() - EXPIRY_DAYS * MS_PER_DAY;
    const originalCount = this.records.length;

    // Filter out expired records
    this.records = this.records.filter((r) => r.timestamp > expiryTime);

    const removedCount = originalCount - this.records.length;

    if (removedCount > 0) {
      console.log(`[ErrorHistoryManager] Cleaned up ${removedCount} expired error records`);
      await this.save();
    }

    return removedCount;
  }

  /**
   * Clear all error history
   *
   * @returns Number of records cleared
   */
  async clearAll(): Promise<number> {
    const count = this.records.length;
    this.records = [];
    await this.save();
    return count;
  }

  /**
   * Delete a specific error record
   *
   * @param id - Error record ID to delete
   * @returns true if record was found and deleted
   */
  async deleteRecord(id: string): Promise<boolean> {
    const index = this.records.findIndex((r) => r.id === id);
    if (index === -1) {
      return false;
    }

    this.records.splice(index, 1);
    await this.save();
    return true;
  }

  /**
   * Get statistics about stored errors
   */
  getStats(): {
    total: number;
    byType: Record<string, number>;
    byOperation: Record<string, number>;
    oldestTimestamp: number | null;
    newestTimestamp: number | null;
  } {
    const byType: Record<string, number> = {};
    const byOperation: Record<string, number> = {};
    let oldestTimestamp: number | null = null;
    let newestTimestamp: number | null = null;

    for (const record of this.records) {
      // Count by error type
      const typeKey = record.backendErrorType || record.errorType;
      byType[typeKey] = (byType[typeKey] || 0) + 1;

      // Count by operation
      byOperation[record.operation] = (byOperation[record.operation] || 0) + 1;

      // Track timestamps
      if (oldestTimestamp === null || record.timestamp < oldestTimestamp) {
        oldestTimestamp = record.timestamp;
      }
      if (newestTimestamp === null || record.timestamp > newestTimestamp) {
        newestTimestamp = record.timestamp;
      }
    }

    return {
      total: this.records.length,
      byType,
      byOperation,
      oldestTimestamp,
      newestTimestamp,
    };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Private Helper Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Generate a unique ID for error records
   *
   * Format: ERR-{timestamp}-{random}
   */
  private generateId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `ERR-${timestamp}-${random}`;
  }
}
