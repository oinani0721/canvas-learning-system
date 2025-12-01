/**
 * Error Logger Tests - Canvas Review System
 *
 * Tests for error logging functionality.
 *
 * @module tests/errors/ErrorLogger.test
 */

import { ErrorLogger, ErrorLogEntry } from '../../src/errors/ErrorLogger';

// Mock Obsidian Plugin
const createMockPlugin = () => ({
    manifest: { version: '1.0.0' },
    loadData: jest.fn().mockResolvedValue({}),
    saveData: jest.fn().mockResolvedValue(undefined)
});

describe('ErrorLogger', () => {
    let logger: ErrorLogger;
    let mockPlugin: ReturnType<typeof createMockPlugin>;

    beforeEach(() => {
        mockPlugin = createMockPlugin();
        logger = new ErrorLogger(mockPlugin as any);
    });

    describe('log', () => {
        it('should add log entry to memory', async () => {
            const entry: ErrorLogEntry = {
                timestamp: new Date().toISOString(),
                errorType: 'NetworkError',
                severity: 'critical',
                message: 'Connection failed',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            };

            await logger.log(entry);

            const logs = logger.getMemoryLogs();
            expect(logs).toHaveLength(1);
            expect(logs[0]).toEqual(entry);
        });

        it('should trim memory log when exceeding max entries', async () => {
            const smallLogger = new ErrorLogger(mockPlugin as any, {
                maxMemoryEntries: 3,
                persistLogs: false
            });

            for (let i = 0; i < 5; i++) {
                await smallLogger.log({
                    timestamp: new Date().toISOString(),
                    errorType: 'TestError',
                    severity: 'info',
                    message: `Error ${i}`,
                    pluginVersion: '1.0.0',
                    obsidianVersion: '1.5.0'
                });
            }

            const logs = smallLogger.getMemoryLogs();
            expect(logs).toHaveLength(3);
            expect(logs[0].message).toBe('Error 2');
            expect(logs[2].message).toBe('Error 4');
        });

        it('should persist logs to file when enabled', async () => {
            const persistLogger = new ErrorLogger(mockPlugin as any, {
                persistLogs: true
            });

            await persistLogger.log({
                timestamp: new Date().toISOString(),
                errorType: 'TestError',
                severity: 'warning',
                message: 'Test message',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            // Wait for async write
            await new Promise(resolve => setTimeout(resolve, 10));

            expect(mockPlugin.saveData).toHaveBeenCalled();
        });
    });

    describe('getRecentLogs', () => {
        beforeEach(async () => {
            for (let i = 0; i < 10; i++) {
                await logger.log({
                    timestamp: new Date().toISOString(),
                    errorType: 'TestError',
                    severity: 'info',
                    message: `Error ${i}`,
                    pluginVersion: '1.0.0',
                    obsidianVersion: '1.5.0'
                });
            }
        });

        it('should return specified number of recent logs', () => {
            const recent = logger.getRecentLogs(3);
            expect(recent).toHaveLength(3);
            expect(recent[0].message).toBe('Error 7');
            expect(recent[2].message).toBe('Error 9');
        });

        it('should return all logs if count exceeds total', () => {
            const recent = logger.getRecentLogs(20);
            expect(recent).toHaveLength(10);
        });
    });

    describe('getLogsBySeverity', () => {
        beforeEach(async () => {
            const severities: Array<'critical' | 'warning' | 'info'> = [
                'critical', 'warning', 'info', 'critical', 'warning'
            ];

            for (const severity of severities) {
                await logger.log({
                    timestamp: new Date().toISOString(),
                    errorType: 'TestError',
                    severity,
                    message: `${severity} error`,
                    pluginVersion: '1.0.0',
                    obsidianVersion: '1.5.0'
                });
            }
        });

        it('should filter by severity', () => {
            const criticalLogs = logger.getLogsBySeverity('critical');
            expect(criticalLogs).toHaveLength(2);
            criticalLogs.forEach(log => {
                expect(log.severity).toBe('critical');
            });
        });
    });

    describe('getLogsInRange', () => {
        it('should filter logs by time range', async () => {
            const now = Date.now();

            // Log with old timestamp
            await logger.log({
                timestamp: new Date(now - 86400000).toISOString(), // 24h ago
                errorType: 'OldError',
                severity: 'info',
                message: 'Old error',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            // Log with recent timestamp
            await logger.log({
                timestamp: new Date(now - 3600000).toISOString(), // 1h ago
                errorType: 'RecentError',
                severity: 'info',
                message: 'Recent error',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            const logsInRange = logger.getLogsInRange(
                new Date(now - 7200000), // 2h ago
                new Date(now)
            );

            expect(logsInRange).toHaveLength(1);
            expect(logsInRange[0].errorType).toBe('RecentError');
        });
    });

    describe('clearMemoryLogs', () => {
        it('should clear all memory logs', async () => {
            await logger.log({
                timestamp: new Date().toISOString(),
                errorType: 'TestError',
                severity: 'info',
                message: 'Test',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            expect(logger.getMemoryLogs()).toHaveLength(1);

            logger.clearMemoryLogs();

            expect(logger.getMemoryLogs()).toHaveLength(0);
        });
    });

    describe('exportToMarkdown', () => {
        it('should export logs in markdown format', async () => {
            await logger.log({
                timestamp: '2024-01-15T10:30:00.000Z',
                errorType: 'NetworkError',
                severity: 'critical',
                message: 'Connection failed',
                context: { url: '/api/test' },
                userAction: 'Decomposing node',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            const markdown = logger.exportToMarkdown();

            expect(markdown).toContain('# Canvas复习系统 - 错误日志报告');
            expect(markdown).toContain('NetworkError');
            expect(markdown).toContain('Connection failed');
            expect(markdown).toContain('/api/test');
            expect(markdown).toContain('Decomposing node');
        });

        it('should group logs by severity', async () => {
            await logger.log({
                timestamp: new Date().toISOString(),
                errorType: 'CriticalError',
                severity: 'critical',
                message: 'Critical',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            await logger.log({
                timestamp: new Date().toISOString(),
                errorType: 'WarningError',
                severity: 'warning',
                message: 'Warning',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            const markdown = logger.exportToMarkdown();

            expect(markdown).toContain('🔴 严重错误');
            expect(markdown).toContain('🟠 警告');
        });
    });

    describe('exportToJSON', () => {
        it('should export logs in JSON format', async () => {
            await logger.log({
                timestamp: '2024-01-15T10:30:00.000Z',
                errorType: 'TestError',
                severity: 'info',
                message: 'Test',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            const json = logger.exportToJSON();
            const parsed = JSON.parse(json);

            expect(Array.isArray(parsed)).toBe(true);
            expect(parsed[0].errorType).toBe('TestError');
        });
    });

    describe('getStatistics', () => {
        beforeEach(async () => {
            const now = Date.now();

            // Recent logs
            await logger.log({
                timestamp: new Date(now - 3600000).toISOString(), // 1h ago
                errorType: 'NetworkError',
                severity: 'critical',
                message: 'Critical 1',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            await logger.log({
                timestamp: new Date(now - 3600000).toISOString(), // 1h ago
                errorType: 'ValidationError',
                severity: 'warning',
                message: 'Warning 1',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });

            // Old log
            await logger.log({
                timestamp: new Date(now - 172800000).toISOString(), // 2 days ago
                errorType: 'NetworkError',
                severity: 'critical',
                message: 'Critical 2',
                pluginVersion: '1.0.0',
                obsidianVersion: '1.5.0'
            });
        });

        it('should calculate correct statistics', () => {
            const stats = logger.getStatistics();

            expect(stats.totalCount).toBe(3);
            expect(stats.bySeverity.critical).toBe(2);
            expect(stats.bySeverity.warning).toBe(1);
            expect(stats.bySeverity.info).toBe(0);
            expect(stats.byType['NetworkError']).toBe(2);
            expect(stats.byType['ValidationError']).toBe(1);
            expect(stats.last24Hours).toBe(2);
            expect(stats.last7Days).toBe(3);
        });
    });

    describe('initialize', () => {
        it('should load existing logs from file', async () => {
            const existingLogs = [
                {
                    timestamp: new Date().toISOString(),
                    errorType: 'ExistingError',
                    severity: 'info',
                    message: 'From file',
                    pluginVersion: '1.0.0',
                    obsidianVersion: '1.5.0'
                }
            ];

            mockPlugin.loadData.mockResolvedValue({ errorLogs: existingLogs });

            await logger.initialize();

            const logs = logger.getMemoryLogs();
            expect(logs).toHaveLength(1);
            expect(logs[0].errorType).toBe('ExistingError');
        });

        it('should handle empty data gracefully', async () => {
            mockPlugin.loadData.mockResolvedValue(null);

            await expect(logger.initialize()).resolves.not.toThrow();
        });
    });
});
