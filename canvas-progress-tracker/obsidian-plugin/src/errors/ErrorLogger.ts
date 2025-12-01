/**
 * Error Logger - Canvas Review System
 *
 * Provides structured error logging with persistence,
 * log rotation, and export capabilities.
 *
 * @module errors/ErrorLogger
 * @version 1.0.0
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorLogger design)
 */

import type { Plugin } from 'obsidian';
import { ErrorSeverity } from './PluginError';

/**
 * Structure for error log entries
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorLogEntry interface)
 */
export interface ErrorLogEntry {
    /** ISO 8601 timestamp */
    timestamp: string;
    /** Error class name */
    errorType: string;
    /** Error severity level */
    severity: ErrorSeverity;
    /** Human-readable error message */
    message: string;
    /** Error stack trace */
    stack?: string;
    /** Additional context data */
    context?: Record<string, unknown>;
    /** What the user was doing when error occurred */
    userAction?: string;
    /** Plugin version */
    pluginVersion: string;
    /** Obsidian version */
    obsidianVersion: string;
}

/**
 * Error logger configuration
 */
export interface ErrorLoggerConfig {
    /** Maximum log entries to keep in memory */
    maxMemoryEntries: number;
    /** Maximum log file size in bytes */
    maxFileSize: number;
    /** Number of days to retain logs */
    retentionDays: number;
    /** Whether to persist logs to file */
    persistLogs: boolean;
    /** Log file name */
    logFileName: string;
}

/**
 * Default logger configuration
 */
const DEFAULT_CONFIG: ErrorLoggerConfig = {
    maxMemoryEntries: 100,
    maxFileSize: 1024 * 1024, // 1MB
    retentionDays: 7,
    persistLogs: true,
    logFileName: 'error-log.jsonl'
};

/**
 * Error Logger class
 *
 * Manages error logging with in-memory and persistent storage.
 *
 * ✅ Verified from Story 13.7 Dev Notes (ErrorLogger class)
 */
export class ErrorLogger {
    private plugin: Plugin;
    private config: ErrorLoggerConfig;
    private memoryLog: ErrorLogEntry[] = [];
    private initialized: boolean = false;
    private writeQueue: Promise<void> = Promise.resolve();

    /**
     * Creates a new ErrorLogger
     *
     * @param plugin - Obsidian plugin instance
     * @param config - Optional configuration overrides
     */
    constructor(
        plugin: Plugin,
        config: Partial<ErrorLoggerConfig> = {}
    ) {
        this.plugin = plugin;
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * Initializes the error logger
     */
    async initialize(): Promise<void> {
        if (this.initialized) return;

        // Load existing logs from file
        if (this.config.persistLogs) {
            await this.loadLogsFromFile();
            await this.rotateOldLogs();
        }

        this.initialized = true;
    }

    /**
     * Logs an error entry
     *
     * @param entry - The error log entry
     */
    async log(entry: ErrorLogEntry): Promise<void> {
        // Add to memory log
        this.memoryLog.push(entry);

        // Trim memory log if needed
        while (this.memoryLog.length > this.config.maxMemoryEntries) {
            this.memoryLog.shift();
        }

        // Persist to file (queued to avoid race conditions)
        if (this.config.persistLogs) {
            this.writeQueue = this.writeQueue.then(() =>
                this.appendToFile(entry)
            );
        }
    }

    /**
     * Gets all logs from memory
     */
    getMemoryLogs(): readonly ErrorLogEntry[] {
        return [...this.memoryLog];
    }

    /**
     * Gets recent logs (from memory)
     *
     * @param count - Number of recent logs to return
     */
    getRecentLogs(count: number = 20): ErrorLogEntry[] {
        return this.memoryLog.slice(-count);
    }

    /**
     * Gets logs by severity
     *
     * @param severity - Filter by severity level
     */
    getLogsBySeverity(severity: ErrorSeverity): ErrorLogEntry[] {
        return this.memoryLog.filter(log => log.severity === severity);
    }

    /**
     * Gets logs within a time range
     *
     * @param startTime - Start of time range (ISO string or Date)
     * @param endTime - End of time range (ISO string or Date)
     */
    getLogsInRange(
        startTime: string | Date,
        endTime: string | Date
    ): ErrorLogEntry[] {
        const start = new Date(startTime).getTime();
        const end = new Date(endTime).getTime();

        return this.memoryLog.filter(log => {
            const logTime = new Date(log.timestamp).getTime();
            return logTime >= start && logTime <= end;
        });
    }

    /**
     * Clears all in-memory logs
     */
    clearMemoryLogs(): void {
        this.memoryLog = [];
    }

    /**
     * Exports logs to markdown format
     *
     * @param logs - Logs to export (defaults to memory logs)
     */
    exportToMarkdown(logs?: ErrorLogEntry[]): string {
        const logsToExport = logs || this.memoryLog;

        const lines: string[] = [
            '# Canvas复习系统 - 错误日志报告',
            '',
            `**导出时间**: ${new Date().toISOString()}`,
            `**日志条目数**: ${logsToExport.length}`,
            '',
            '---',
            ''
        ];

        // Group by severity
        const grouped: Record<ErrorSeverity, ErrorLogEntry[]> = {
            critical: [],
            warning: [],
            info: []
        };

        for (const log of logsToExport) {
            grouped[log.severity].push(log);
        }

        // Output by severity
        const severityOrder: ErrorSeverity[] = ['critical', 'warning', 'info'];
        const severityNames: Record<ErrorSeverity, string> = {
            critical: '🔴 严重错误',
            warning: '🟠 警告',
            info: 'ℹ️ 信息'
        };

        for (const severity of severityOrder) {
            const entries = grouped[severity];
            if (entries.length === 0) continue;

            lines.push(`## ${severityNames[severity]} (${entries.length})`);
            lines.push('');

            for (const entry of entries) {
                lines.push(`### ${entry.errorType}`);
                lines.push('');
                lines.push(`- **时间**: ${entry.timestamp}`);
                lines.push(`- **消息**: ${entry.message}`);
                lines.push(`- **插件版本**: ${entry.pluginVersion}`);
                lines.push(`- **Obsidian版本**: ${entry.obsidianVersion}`);

                if (entry.userAction) {
                    lines.push(`- **用户操作**: ${entry.userAction}`);
                }

                if (entry.context) {
                    lines.push('');
                    lines.push('**上下文**:');
                    lines.push('```json');
                    lines.push(JSON.stringify(entry.context, null, 2));
                    lines.push('```');
                }

                if (entry.stack) {
                    lines.push('');
                    lines.push('**堆栈跟踪**:');
                    lines.push('```');
                    lines.push(entry.stack);
                    lines.push('```');
                }

                lines.push('');
                lines.push('---');
                lines.push('');
            }
        }

        return lines.join('\n');
    }

    /**
     * Exports logs to JSON format
     */
    exportToJSON(): string {
        return JSON.stringify(this.memoryLog, null, 2);
    }

    /**
     * Gets log statistics
     */
    getStatistics(): ErrorLogStatistics {
        const now = Date.now();
        const dayMs = 24 * 60 * 60 * 1000;

        const stats: ErrorLogStatistics = {
            totalCount: this.memoryLog.length,
            bySeverity: {
                critical: 0,
                warning: 0,
                info: 0
            },
            byType: {},
            last24Hours: 0,
            last7Days: 0
        };

        for (const log of this.memoryLog) {
            // Count by severity
            stats.bySeverity[log.severity]++;

            // Count by type
            stats.byType[log.errorType] = (stats.byType[log.errorType] || 0) + 1;

            // Time-based counts
            const logTime = new Date(log.timestamp).getTime();
            if (now - logTime <= dayMs) {
                stats.last24Hours++;
            }
            if (now - logTime <= 7 * dayMs) {
                stats.last7Days++;
            }
        }

        return stats;
    }

    /**
     * Cleans up resources
     */
    cleanup(): void {
        // Wait for any pending writes
        this.writeQueue.then(() => {
            this.memoryLog = [];
            this.initialized = false;
        });
    }

    // ========== Private Methods ==========

    /**
     * Loads logs from the persistent file
     */
    private async loadLogsFromFile(): Promise<void> {
        try {
            const data = await this.plugin.loadData();
            const logs = data?.errorLogs;

            if (Array.isArray(logs)) {
                this.memoryLog = logs.slice(-this.config.maxMemoryEntries);
            }
        } catch (error) {
            console.warn('Canvas复习系统: 无法加载错误日志', error);
        }
    }

    /**
     * Appends a log entry to the persistent file
     */
    private async appendToFile(entry: ErrorLogEntry): Promise<void> {
        try {
            const data = (await this.plugin.loadData()) || {};
            const logs = data.errorLogs || [];

            logs.push(entry);

            // Check file size limit (approximate)
            const size = JSON.stringify(logs).length;
            if (size > this.config.maxFileSize) {
                // Remove oldest entries to stay under limit
                const removeCount = Math.ceil(logs.length * 0.2); // Remove 20%
                logs.splice(0, removeCount);
            }

            data.errorLogs = logs;
            await this.plugin.saveData(data);
        } catch (error) {
            console.error('Canvas复习系统: 无法保存错误日志', error);
        }
    }

    /**
     * Rotates out old logs
     */
    private async rotateOldLogs(): Promise<void> {
        const cutoff = Date.now() - (this.config.retentionDays * 24 * 60 * 60 * 1000);

        const originalCount = this.memoryLog.length;
        this.memoryLog = this.memoryLog.filter(log => {
            const logTime = new Date(log.timestamp).getTime();
            return logTime >= cutoff;
        });

        const removedCount = originalCount - this.memoryLog.length;
        if (removedCount > 0) {
            console.log(`Canvas复习系统: 清理了 ${removedCount} 条过期日志`);

            // Update persisted logs
            if (this.config.persistLogs) {
                try {
                    const data = (await this.plugin.loadData()) || {};
                    data.errorLogs = this.memoryLog;
                    await this.plugin.saveData(data);
                } catch (error) {
                    console.warn('Canvas复习系统: 无法更新持久化日志', error);
                }
            }
        }
    }
}

/**
 * Error log statistics
 */
export interface ErrorLogStatistics {
    totalCount: number;
    bySeverity: Record<ErrorSeverity, number>;
    byType: Record<string, number>;
    last24Hours: number;
    last7Days: number;
}
