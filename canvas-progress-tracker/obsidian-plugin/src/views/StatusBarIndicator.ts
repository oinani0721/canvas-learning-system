/**
 * Status Bar Indicator - Canvas Learning System Cross-Canvas Associations
 *
 * Displays association count and sync status in Obsidian's status bar.
 * Implements Story 16.7: 关联状态指示器
 *
 * @module views/StatusBarIndicator
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin.addStatusBarItem, Menu API)
 * ✅ Verified from Story 16.7 Dev Notes (Sync status, right-click menu)
 */

import { App, Plugin, Menu, TFile, Notice } from 'obsidian';
import type { SyncStatus } from '../types/AssociationTypes';

/**
 * Association status for status bar display
 * ✅ Verified from Story 16.7 Dev Notes (AssociationStatus interface)
 */
export interface AssociationStatusData {
    canvas_path: string;
    association_count: number;
    sync_status: SyncStatus;
    last_sync: string;
    error_message?: string;
    related_canvas_names?: string[];
}

/**
 * Sync status with optional error message
 */
interface SyncStatusInfo {
    status: SyncStatus;
    errorMessage?: string;
}

/**
 * Status bar refresh callback type
 */
export type RefreshCallback = () => Promise<void>;
export type CleanOrphansCallback = () => Promise<number>;
export type OpenModalCallback = () => void;
export type GetAssociationCountCallback = (canvasPath: string) => Promise<AssociationStatusData>;

/**
 * Status bar indicator configuration
 */
export interface StatusIndicatorConfig {
    showWhenZero: boolean;
    maxTooltipItems: number;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: StatusIndicatorConfig = {
    showWhenZero: true,
    maxTooltipItems: 5
};

/**
 * Association Status Indicator
 *
 * Shows association count and sync status in Obsidian's status bar.
 * Supports click to open modal, right-click for context menu.
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin.addStatusBarItem)
 */
export class AssociationStatusIndicator {
    private app: App;
    private plugin: Plugin;
    private statusBarItem: HTMLElement;
    private currentData: AssociationStatusData | null = null;
    private syncStatus: SyncStatusInfo = { status: 'pending' };
    private config: StatusIndicatorConfig;

    // Callbacks
    private onRefresh?: RefreshCallback;
    private onCleanOrphans?: CleanOrphansCallback;
    private onOpenModal?: OpenModalCallback;
    private onGetAssociations?: GetAssociationCountCallback;

    /**
     * Creates a new AssociationStatusIndicator
     *
     * ✅ Verified from @obsidian-canvas Skill (Plugin.addStatusBarItem)
     *
     * @param app - Obsidian App instance
     * @param plugin - Plugin instance
     * @param config - Optional configuration
     */
    constructor(
        app: App,
        plugin: Plugin,
        config?: Partial<StatusIndicatorConfig>
    ) {
        this.app = app;
        this.plugin = plugin;
        this.config = { ...DEFAULT_CONFIG, ...config };

        // Create status bar item
        this.statusBarItem = plugin.addStatusBarItem();
        this.statusBarItem.addClass('association-status-indicator');

        this.setupEventListeners();
        this.render();
        this.injectStyles();
    }

    /**
     * Set callback handlers
     */
    setCallbacks(callbacks: {
        onRefresh?: RefreshCallback;
        onCleanOrphans?: CleanOrphansCallback;
        onOpenModal?: OpenModalCallback;
        onGetAssociations?: GetAssociationCountCallback;
    }): void {
        this.onRefresh = callbacks.onRefresh;
        this.onCleanOrphans = callbacks.onCleanOrphans;
        this.onOpenModal = callbacks.onOpenModal;
        this.onGetAssociations = callbacks.onGetAssociations;
    }

    /**
     * Setup event listeners
     *
     * ✅ Verified from @obsidian-canvas Skill (workspace.on, Menu API)
     */
    private setupEventListeners(): void {
        // Click to open association modal
        this.statusBarItem.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleClick();
        });

        // Right-click for context menu
        this.statusBarItem.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showContextMenu(e);
        });

        // Hover for tooltip
        this.statusBarItem.addEventListener('mouseenter', () => {
            this.showTooltip();
        });

        // Canvas switch listener
        // ✅ Verified from @obsidian-canvas Skill (workspace:active-leaf-change)
        this.plugin.registerEvent(
            this.app.workspace.on('active-leaf-change', (leaf) => {
                this.updateForActiveCanvas();
            })
        );
    }

    /**
     * Update association count
     */
    updateCount(count: number, relatedNames?: string[]): void {
        const previousCount = this.currentData?.association_count ?? 0;
        const changed = count !== previousCount;

        this.currentData = {
            ...this.currentData,
            canvas_path: this.currentData?.canvas_path || '',
            association_count: count,
            sync_status: this.syncStatus.status,
            last_sync: new Date().toISOString(),
            related_canvas_names: relatedNames
        };

        this.render();

        if (changed && previousCount !== 0) {
            this.animatePulse();
        }
    }

    /**
     * Update sync status
     */
    updateSyncStatus(status: SyncStatus, errorMessage?: string): void {
        this.syncStatus = { status, errorMessage };

        if (this.currentData) {
            this.currentData.sync_status = status;
            this.currentData.error_message = errorMessage;
        }

        this.render();
    }

    /**
     * Update with full status data
     */
    updateData(data: AssociationStatusData): void {
        const previousCount = this.currentData?.association_count ?? 0;
        const changed = data.association_count !== previousCount;

        this.currentData = data;
        this.syncStatus = {
            status: data.sync_status,
            errorMessage: data.error_message
        };

        this.render();

        if (changed && previousCount !== 0) {
            this.animatePulse();
        }
    }

    /**
     * Render status bar content
     */
    private render(): void {
        const count = this.currentData?.association_count ?? 0;

        // Hide if zero and configured to do so
        if (count === 0 && !this.config.showWhenZero) {
            this.statusBarItem.style.display = 'none';
            return;
        }

        this.statusBarItem.style.display = '';
        const syncIndicator = this.getSyncIndicator();

        this.statusBarItem.textContent = `🔗 ${count} 关联 ${syncIndicator}`;
        this.statusBarItem.setAttribute('data-sync', this.syncStatus.status);
        this.statusBarItem.setAttribute('aria-label', this.getAriaLabel());
    }

    /**
     * Get sync status indicator text
     */
    private getSyncIndicator(): string {
        switch (this.syncStatus.status) {
            case 'syncing':
                return '(同步中...)';
            case 'synced':
                return '✓';
            case 'error':
                return '⚠️';
            case 'pending':
            default:
                return '';
        }
    }

    /**
     * Get aria-label for accessibility
     */
    private getAriaLabel(): string {
        const count = this.currentData?.association_count ?? 0;

        if (this.syncStatus.status === 'error' && this.syncStatus.errorMessage) {
            return `${count} 个关联，同步失败: ${this.syncStatus.errorMessage}`;
        }

        if (this.syncStatus.status === 'syncing') {
            return `${count} 个关联，正在同步...`;
        }

        return `${count} 个关联，点击管理`;
    }

    /**
     * Show tooltip with related Canvas names
     */
    private showTooltip(): void {
        const names = this.currentData?.related_canvas_names || [];
        const count = this.currentData?.association_count ?? 0;

        if (names.length === 0) {
            this.statusBarItem.setAttribute('aria-label', this.getAriaLabel());
            return;
        }

        const maxItems = this.config.maxTooltipItems;
        const displayNames = names.slice(0, maxItems);
        const remaining = names.length - maxItems;

        let tooltip = '关联的Canvas:\n';
        tooltip += displayNames.map(name => `• ${name}`).join('\n');

        if (remaining > 0) {
            tooltip += `\n... 还有 ${remaining} 个`;
        }

        if (this.syncStatus.status === 'error' && this.syncStatus.errorMessage) {
            tooltip += `\n\n⚠️ ${this.syncStatus.errorMessage}`;
        }

        this.statusBarItem.setAttribute('aria-label', tooltip);
    }

    /**
     * Handle click event
     */
    private handleClick(): void {
        if (this.onOpenModal) {
            this.onOpenModal();
        } else {
            new Notice('关联管理功能未配置');
        }
    }

    /**
     * Show context menu
     *
     * ✅ Verified from @obsidian-canvas Skill (Menu API)
     */
    private showContextMenu(e: MouseEvent): void {
        const menu = new Menu();

        // Refresh sync
        menu.addItem((item) => {
            item.setTitle('刷新同步')
                .setIcon('refresh-cw')
                .onClick(async () => {
                    await this.handleRefreshSync();
                });
        });

        // Clean orphan associations
        menu.addItem((item) => {
            item.setTitle('清理孤儿关联')
                .setIcon('trash-2')
                .onClick(async () => {
                    await this.handleCleanOrphans();
                });
        });

        menu.addSeparator();

        // Open association management
        menu.addItem((item) => {
            item.setTitle('打开关联管理')
                .setIcon('settings')
                .onClick(() => {
                    this.handleClick();
                });
        });

        menu.showAtMouseEvent(e);
    }

    /**
     * Handle refresh sync action
     */
    private async handleRefreshSync(): Promise<void> {
        if (!this.onRefresh) {
            new Notice('刷新功能未配置');
            return;
        }

        this.updateSyncStatus('syncing');

        try {
            await this.onRefresh();
            this.updateSyncStatus('synced');
            new Notice('同步完成');
        } catch (error) {
            const errorMsg = (error as Error).message;
            this.updateSyncStatus('error', errorMsg);
            new Notice(`同步失败: ${errorMsg}`);
        }
    }

    /**
     * Handle clean orphans action
     */
    private async handleCleanOrphans(): Promise<void> {
        if (!this.onCleanOrphans) {
            new Notice('清理功能未配置');
            return;
        }

        try {
            const count = await this.onCleanOrphans();

            if (count > 0) {
                new Notice(`已清理 ${count} 个孤儿关联`);
                // Refresh display
                await this.updateForActiveCanvas();
            } else {
                new Notice('没有发现孤儿关联');
            }
        } catch (error) {
            new Notice(`清理失败: ${(error as Error).message}`);
        }
    }

    /**
     * Update display for active Canvas
     *
     * ✅ Verified from @obsidian-canvas Skill (workspace.getActiveFile)
     */
    private async updateForActiveCanvas(): Promise<void> {
        const activeFile = this.app.workspace.getActiveFile();

        if (!activeFile || activeFile.extension !== 'canvas') {
            // Not a Canvas file, hide or show zero
            this.updateCount(0, []);
            return;
        }

        if (!this.onGetAssociations) {
            return;
        }

        try {
            const data = await this.onGetAssociations(activeFile.path);
            this.updateData(data);
        } catch (error) {
            console.warn('[StatusBarIndicator] Failed to get associations:', error);
            this.updateSyncStatus('error', (error as Error).message);
        }
    }

    /**
     * Animate pulse effect on count change
     */
    private animatePulse(): void {
        this.statusBarItem.addClass('pulse');

        setTimeout(() => {
            this.statusBarItem.removeClass('pulse');
        }, 1000);
    }

    /**
     * Show indicator (if hidden)
     */
    show(): void {
        this.statusBarItem.style.display = '';
    }

    /**
     * Hide indicator
     */
    hide(): void {
        this.statusBarItem.style.display = 'none';
    }

    /**
     * Update configuration
     */
    setConfig(config: Partial<StatusIndicatorConfig>): void {
        this.config = { ...this.config, ...config };
        this.render();
    }

    /**
     * Force refresh display
     */
    async refresh(): Promise<void> {
        await this.updateForActiveCanvas();
    }

    /**
     * Inject CSS styles
     */
    private injectStyles(): void {
        const styleId = 'association-status-indicator-styles';

        if (document.getElementById(styleId)) {
            return;
        }

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* Association Status Indicator Styles */
            /* ✅ Verified from Story 16.7 Dev Notes (CSS样式) */

            .association-status-indicator {
                cursor: pointer;
                padding: 0 8px;
                border-radius: 4px;
                transition: background-color 0.2s ease;
                font-size: var(--font-ui-smaller);
            }

            .association-status-indicator:hover {
                background-color: var(--background-modifier-hover);
            }

            /* Pulse animation for count changes */
            .association-status-indicator.pulse {
                animation: association-status-pulse 1s ease-in-out;
            }

            @keyframes association-status-pulse {
                0%, 100% {
                    background-color: transparent;
                }
                50% {
                    background-color: var(--interactive-accent);
                    color: var(--text-on-accent);
                }
            }

            /* Sync status colors */
            .association-status-indicator[data-sync="syncing"] {
                color: var(--text-muted);
            }

            .association-status-indicator[data-sync="synced"] {
                color: var(--text-success, var(--color-green));
            }

            .association-status-indicator[data-sync="error"] {
                color: var(--text-warning, var(--color-yellow));
            }

            .association-status-indicator[data-sync="pending"] {
                color: var(--text-normal);
            }

            /* Syncing animation */
            .association-status-indicator[data-sync="syncing"]::after {
                content: '';
                display: inline-block;
                width: 8px;
                height: 8px;
                margin-left: 4px;
                border: 2px solid var(--text-muted);
                border-radius: 50%;
                border-top-color: transparent;
                animation: association-sync-spin 1s linear infinite;
            }

            @keyframes association-sync-spin {
                to {
                    transform: rotate(360deg);
                }
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Cleanup resources
     */
    destroy(): void {
        this.statusBarItem.remove();
    }
}

/**
 * Create and configure status bar indicator
 *
 * Factory function for easy instantiation with all callbacks configured.
 *
 * @param app - Obsidian App instance
 * @param plugin - Plugin instance
 * @param callbacks - Callback handlers
 * @param config - Optional configuration
 * @returns Configured AssociationStatusIndicator
 */
export function createStatusBarIndicator(
    app: App,
    plugin: Plugin,
    callbacks: {
        onRefresh: RefreshCallback;
        onCleanOrphans: CleanOrphansCallback;
        onOpenModal: OpenModalCallback;
        onGetAssociations: GetAssociationCountCallback;
    },
    config?: Partial<StatusIndicatorConfig>
): AssociationStatusIndicator {
    const indicator = new AssociationStatusIndicator(app, plugin, config);
    indicator.setCallbacks(callbacks);
    return indicator;
}
