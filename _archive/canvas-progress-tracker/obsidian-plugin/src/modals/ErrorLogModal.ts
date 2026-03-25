/**
 * Error Log Modal - Canvas Review System
 *
 * Modal dialog for viewing and exporting error logs.
 *
 * @module modals/ErrorLogModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 13.7 Dev Notes (ErrorLogModal design)
 */

import { App, Modal, Notice } from 'obsidian';
import { ErrorLogEntry, ErrorLogStatistics } from '../errors/ErrorLogger';
import { ErrorSeverity } from '../errors/PluginError';

/**
 * Tab types for the log modal
 */
type LogTab = 'all' | 'critical' | 'warning' | 'info';

/**
 * Error Log Modal
 *
 * Provides a UI for viewing error logs with filtering,
 * search, and export capabilities.
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal class)
 */
export class ErrorLogModal extends Modal {
    private logs: ErrorLogEntry[];
    private statistics: ErrorLogStatistics | null;
    private activeTab: LogTab = 'all';
    private searchQuery: string = '';
    private onExport: ((format: 'markdown' | 'json') => void) | null;

    /**
     * Creates a new ErrorLogModal
     *
     * @param app - Obsidian App instance
     * @param logs - Array of error log entries
     * @param statistics - Optional statistics object
     * @param onExport - Optional callback for exporting logs
     */
    constructor(
        app: App,
        logs: ErrorLogEntry[],
        statistics?: ErrorLogStatistics,
        onExport?: (format: 'markdown' | 'json') => void
    ) {
        super(app);
        this.logs = logs;
        this.statistics = statistics || null;
        this.onExport = onExport || null;
    }

    /**
     * Called when the modal is opened
     */
    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();

        // Add modal class for styling
        contentEl.addClass('canvas-review-error-log-modal');

        // Header
        this.renderHeader(contentEl);

        // Statistics (if available)
        if (this.statistics) {
            this.renderStatistics(contentEl);
        }

        // Tabs
        this.renderTabs(contentEl);

        // Search bar
        this.renderSearchBar(contentEl);

        // Log list
        this.renderLogList(contentEl);

        // Footer with export options
        this.renderFooter(contentEl);
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }

    // ========== Render Methods ==========

    private renderHeader(container: HTMLElement): void {
        const header = container.createEl('div', {
            cls: 'error-log-modal-header'
        });

        header.createEl('h2', {
            text: '📋 错误日志',
            cls: 'error-log-modal-title'
        });

        header.createEl('span', {
            text: `共 ${this.logs.length} 条记录`,
            cls: 'error-log-modal-count'
        });
    }

    private renderStatistics(container: HTMLElement): void {
        if (!this.statistics) return;

        const statsSection = container.createEl('div', {
            cls: 'error-log-modal-stats'
        });

        // Severity breakdown
        const severityStats = statsSection.createEl('div', {
            cls: 'error-log-severity-stats'
        });

        const severities: { key: ErrorSeverity; label: string; emoji: string }[] = [
            { key: 'critical', label: '严重', emoji: '🔴' },
            { key: 'warning', label: '警告', emoji: '🟠' },
            { key: 'info', label: '信息', emoji: '🔵' }
        ];

        for (const { key, label, emoji } of severities) {
            const count = this.statistics.bySeverity[key];
            const stat = severityStats.createEl('span', {
                cls: `stat-badge severity-${key}`
            });
            stat.createSpan({ text: `${emoji} ${label}: ${count}` });
        }

        // Time breakdown
        const timeStats = statsSection.createEl('div', {
            cls: 'error-log-time-stats'
        });

        timeStats.createEl('span', {
            text: `📅 最近24小时: ${this.statistics.last24Hours}`
        });

        timeStats.createEl('span', {
            text: `📆 最近7天: ${this.statistics.last7Days}`
        });
    }

    private renderTabs(container: HTMLElement): void {
        const tabsContainer = container.createEl('div', {
            cls: 'error-log-modal-tabs'
        });

        const tabs: { id: LogTab; label: string }[] = [
            { id: 'all', label: '全部' },
            { id: 'critical', label: '🔴 严重' },
            { id: 'warning', label: '🟠 警告' },
            { id: 'info', label: '🔵 信息' }
        ];

        for (const tab of tabs) {
            const tabEl = tabsContainer.createEl('button', {
                text: tab.label,
                cls: `error-log-tab ${this.activeTab === tab.id ? 'active' : ''}`
            });

            tabEl.addEventListener('click', () => {
                this.activeTab = tab.id;
                this.refresh();
            });
        }
    }

    private renderSearchBar(container: HTMLElement): void {
        const searchContainer = container.createEl('div', {
            cls: 'error-log-modal-search'
        });

        const searchInput = searchContainer.createEl('input', {
            type: 'text',
            placeholder: '搜索错误日志...',
            cls: 'error-log-search-input'
        });

        searchInput.value = this.searchQuery;
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = (e.target as HTMLInputElement).value;
            this.renderLogList(container.parentElement!);
        });

        // Clear button
        if (this.searchQuery) {
            const clearBtn = searchContainer.createEl('button', {
                text: '✕',
                cls: 'error-log-search-clear'
            });
            clearBtn.addEventListener('click', () => {
                this.searchQuery = '';
                searchInput.value = '';
                this.refresh();
            });
        }
    }

    private renderLogList(container: HTMLElement): void {
        // Remove existing list
        const existingList = container.querySelector('.error-log-modal-list');
        if (existingList) {
            existingList.remove();
        }

        const listContainer = container.createEl('div', {
            cls: 'error-log-modal-list'
        });

        // Filter logs
        let filteredLogs = this.logs;

        // Filter by tab
        if (this.activeTab !== 'all') {
            filteredLogs = filteredLogs.filter(
                log => log.severity === this.activeTab
            );
        }

        // Filter by search query
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filteredLogs = filteredLogs.filter(log =>
                log.message.toLowerCase().includes(query) ||
                log.errorType.toLowerCase().includes(query) ||
                (log.userAction && log.userAction.toLowerCase().includes(query))
            );
        }

        // Show empty state if no logs
        if (filteredLogs.length === 0) {
            listContainer.createEl('div', {
                text: '没有找到匹配的日志记录',
                cls: 'error-log-empty'
            });
            return;
        }

        // Render log entries (most recent first)
        const sortedLogs = [...filteredLogs].reverse();

        for (const log of sortedLogs) {
            this.renderLogEntry(listContainer, log);
        }
    }

    private renderLogEntry(container: HTMLElement, log: ErrorLogEntry): void {
        const entry = container.createEl('div', {
            cls: `error-log-entry severity-${log.severity}`
        });

        // Header row
        const headerRow = entry.createEl('div', {
            cls: 'error-log-entry-header'
        });

        // Severity icon
        const severityIcons: Record<ErrorSeverity, string> = {
            critical: '🔴',
            warning: '🟠',
            info: '🔵'
        };
        headerRow.createEl('span', {
            text: severityIcons[log.severity],
            cls: 'error-log-entry-icon'
        });

        // Error type
        headerRow.createEl('span', {
            text: log.errorType,
            cls: 'error-log-entry-type'
        });

        // Timestamp
        const date = new Date(log.timestamp);
        headerRow.createEl('span', {
            text: date.toLocaleString('zh-CN'),
            cls: 'error-log-entry-time'
        });

        // Message
        entry.createEl('div', {
            text: log.message,
            cls: 'error-log-entry-message'
        });

        // User action (if present)
        if (log.userAction) {
            entry.createEl('div', {
                text: `操作: ${log.userAction}`,
                cls: 'error-log-entry-action'
            });
        }

        // Expandable details
        if (log.context || log.stack) {
            const details = entry.createEl('details', {
                cls: 'error-log-entry-details'
            });

            details.createEl('summary', { text: '详细信息' });

            // Context
            if (log.context) {
                const contextEl = details.createEl('div', {
                    cls: 'error-log-entry-context'
                });
                contextEl.createEl('strong', { text: '上下文:' });
                contextEl.createEl('pre').createEl('code', {
                    text: JSON.stringify(log.context, null, 2)
                });
            }

            // Stack trace
            if (log.stack) {
                const stackEl = details.createEl('div', {
                    cls: 'error-log-entry-stack'
                });
                stackEl.createEl('strong', { text: '堆栈跟踪:' });
                stackEl.createEl('pre').createEl('code', {
                    text: log.stack
                });
            }
        }

        // Version info
        const versionRow = entry.createEl('div', {
            cls: 'error-log-entry-version'
        });
        versionRow.createEl('span', {
            text: `插件: v${log.pluginVersion}`
        });
        versionRow.createEl('span', {
            text: `Obsidian: v${log.obsidianVersion}`
        });
    }

    private renderFooter(container: HTMLElement): void {
        const footer = container.createEl('div', {
            cls: 'error-log-modal-footer'
        });

        // Export buttons
        const exportSection = footer.createEl('div', {
            cls: 'error-log-export-buttons'
        });

        if (this.onExport) {
            const exportMdBtn = exportSection.createEl('button', {
                text: '📄 导出 Markdown',
                cls: 'error-log-export-btn'
            });
            exportMdBtn.addEventListener('click', () => {
                this.onExport?.('markdown');
                new Notice('错误日志已导出为 Markdown');
            });

            const exportJsonBtn = exportSection.createEl('button', {
                text: '📦 导出 JSON',
                cls: 'error-log-export-btn'
            });
            exportJsonBtn.addEventListener('click', () => {
                this.onExport?.('json');
                new Notice('错误日志已导出为 JSON');
            });
        }

        // Close button
        const closeBtn = footer.createEl('button', {
            text: '关闭',
            cls: 'error-log-close-btn'
        });
        closeBtn.addEventListener('click', () => {
            this.close();
        });
    }

    /**
     * Refreshes the modal content
     */
    private refresh(): void {
        this.onClose();
        this.onOpen();
    }
}
