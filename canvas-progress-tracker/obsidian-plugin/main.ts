/**
 * Canvas Review System - Main Plugin Entry Point
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Class, PluginSettingTab, Setting)
 * ✅ Verified from Story 13.1 Dev Notes: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#插件核心类
 * ✅ Verified from Story 13.6: Settings Panel implementation
 *
 * This plugin provides Ebbinghaus-based intelligent Canvas review management
 * integrated with the Canvas Learning System.
 *
 * @module main
 * @version 2.0.0
 */

import {
    App,
    Plugin,
    Notice,
    MarkdownView,
    TFile
} from 'obsidian';
import {
    PluginSettings,
    DEFAULT_SETTINGS,
    validateSettings,
    migrateSettings
} from './src/types/settings';
import { CanvasReviewSettingsTab } from './src/settings/PluginSettingsTab';
import { DataManager } from './src/database/DataManager';
import { ReviewDashboardView, VIEW_TYPE_REVIEW_DASHBOARD } from './src/views/ReviewDashboardView';
import { ProgressTrackerView, VIEW_TYPE_PROGRESS_TRACKER } from './src/views/ProgressTrackerView';
import { CrossCanvasSidebarView, VIEW_TYPE_CROSS_CANVAS_SIDEBAR } from './src/views/CrossCanvasSidebar';
import { CrossCanvasModal, createCrossCanvasModal } from './src/modals/CrossCanvasModal';
import type { CrossCanvasAssociation } from './src/types/UITypes';
import { NotificationService, createNotificationService } from './src/services/NotificationService';
import { GroupPreviewModal, CanvasNode, NodeGroup } from './src/modals/GroupPreviewModal';
import { ProgressMonitorModal, ProgressMonitorCallbacks, SessionStatus } from './src/modals/ProgressMonitorModal';
import { ResultSummaryModal, ResultSummaryCallbacks } from './src/modals/ResultSummaryModal';
import { ContextMenuManager } from './src/managers/ContextMenuManager';
import type { MenuContext } from './src/types/menu';
import { BackupProtectionManager } from './src/managers/BackupProtectionManager';
import { ApiClient } from './src/api/ApiClient';
import { CanvasDataImporterService } from './src/services/CanvasDataImporterService';
import { CrossCanvasService } from './src/services/CrossCanvasService';
import { ErrorHistoryManager } from './src/managers/ErrorHistoryManager';
import { ErrorNotificationService } from './src/services/ErrorNotificationService';
import { ApiError } from './src/api/types';
import { BackendProcessManager, createBackendProcessManager, BackendStatus } from './src/services/BackendProcessManager';

/**
 * Canvas Review Plugin - Main Plugin Class
 *
 * Implements the core plugin functionality including:
 * - Plugin lifecycle management (onload/onunload)
 * - Settings management with migration support
 * - Command registration
 * - Manager initialization placeholders
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Class - Core Plugin Lifecycle)
 */
export default class CanvasReviewPlugin extends Plugin {
    /** Plugin settings - initialized in onload via loadSettings() */
    settings!: PluginSettings;

    /** Auto-sync interval ID for cleanup */
    private autoSyncIntervalId: number | null = null;

    /** Data Manager - Handles all database operations (Story 14.1) */
    private dataManager: DataManager | null = null;

    /** Notification Service - Handles review reminder notifications (Story 14.7) */
    private notificationService: NotificationService | null = null;

    /** Backup Protection Manager - Required by ContextMenuManager (Story 13.5) */
    private backupProtectionManager: BackupProtectionManager | null = null;

    /** Context Menu Manager - Provides right-click menu for Canvas nodes (Story 13.5) */
    private contextMenuManager: ContextMenuManager | null = null;

    /** API Client - HTTP communication with backend (Story 13.3) */
    private apiClient: ApiClient | null = null;

    /** Canvas Data Importer - Scans vault for Canvas files and imports nodes (P0 Task #3) */
    private canvasDataImporter: CanvasDataImporterService | null = null;

    /** Cross-Canvas Service - Manages canvas associations (Story 25.1) */
    private crossCanvasService: CrossCanvasService | null = null;

    /** Error History Manager - Tracks API errors for debugging (Story 21.5.5) */
    public errorHistoryManager: ErrorHistoryManager | null = null;

    /** Error Notification Service - Shows enhanced error notices (Story 21.5.5) */
    private errorNotificationService: ErrorNotificationService | null = null;

    /** Backend Process Manager - Manages FastAPI backend lifecycle */
    public backendManager: BackendProcessManager | null = null;

    /** Current backend status for UI updates */
    private backendStatus: BackendStatus = 'stopped';

    /**
     * Plugin load lifecycle method
     *
     * Called when the plugin is loaded. Sets up all plugin components:
     * - Loads saved settings (with migration support)
     * - Initializes managers (placeholders for future stories)
     * - Registers commands
     * - Adds settings tab
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.onload)
     */
    async onload(): Promise<void> {
        console.log('Canvas Review System: Loading plugin...');

        try {
            // Load settings from data.json (with migration support)
            await this.loadSettings();

            // Initialize managers (Story 14.1 - DataManager)
            await this.initializeManagers();

            // Register views (Story 14.2 - Dashboard)
            this.registerViews();

            // Register commands
            this.registerCommands();

            // Add comprehensive settings tab (Story 13.6)
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (addSettingTab)
            this.addSettingTab(new CanvasReviewSettingsTab(this.app, this));

            // Setup auto-sync if enabled
            this.setupAutoSync();

            // Apply custom CSS if configured
            this.applyCustomCss();

            // Add ribbon icon for intelligent parallel processing (Story 13.8)
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (addRibbonIcon)
            this.addRibbonIcon('zap', 'Intelligent Batch Processing (智能批量处理)', async () => {
                // Check if current view is a Canvas
                const activeFile = this.app.workspace.getActiveFile();
                if (activeFile?.extension === 'canvas') {
                    await this.handleIntelligentParallelClick();
                } else {
                    new Notice('Please open a Canvas file first to use Intelligent Batch Processing');
                }
            });

            // Register layout-ready event for notifications (Story 14.7)
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (workspace.onLayoutReady)
            this.app.workspace.onLayoutReady(() => {
                this.checkAndShowNotification();
            });

            // Log successful load
            console.log('Canvas Review System: Plugin loaded successfully');

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Debug mode enabled');
                console.log('Canvas Review System: Settings:', this.settings);
            }

        } catch (error) {
            console.error('Canvas Review System: Failed to load plugin:', error);
            new Notice('Canvas Review System failed to load. Check console for details.');
        }
    }

    /**
     * Plugin unload lifecycle method
     *
     * Called when the plugin is disabled. Cleans up all resources:
     * - Stops auto-sync
     * - Cleans up managers
     * - Removes custom CSS
     * - Saves final state
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.onunload)
     */
    onunload(): void {
        console.log('Canvas Review System: Unloading plugin...');

        try {
            // Stop auto-sync interval
            if (this.autoSyncIntervalId !== null) {
                window.clearInterval(this.autoSyncIntervalId);
                this.autoSyncIntervalId = null;
            }

            // Remove custom CSS
            this.removeCustomCss();

            // Cleanup managers (placeholder for future stories)
            this.cleanupManagers();

            console.log('Canvas Review System: Plugin unloaded successfully');

        } catch (error) {
            console.error('Canvas Review System: Error during unload:', error);
        }
    }

    /**
     * Initialize manager instances
     *
     * Initializes all plugin managers:
     * - DataManager (Story 14.1)
     * - CommandWrapper (Story 13.3+)
     * - UIManager (Story 13.4+)
     * - SyncManager (Story 13.5+)
     */
    private async initializeManagers(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Initializing managers...');
        }

        // Initialize DataManager (Story 14.1)
        try {
            this.dataManager = new DataManager(this.app, {
                database: {
                    path: this.settings.dataPath || 'canvas-review.db',
                    maxConnections: 5,
                    connectionTimeout: 30000,
                    busyTimeout: 5000,
                    enableForeignKeys: true,
                    enableWAL: true,
                },
                backup: {
                    databasePath: this.settings.dataPath || 'canvas-review.db',
                    backupDirectory: 'canvas-review-backups',
                    autoBackup: this.settings.autoBackup,
                    backupIntervalHours: 24,
                    retentionDays: this.settings.backupRetentionDays,
                    compressBackups: false,
                },
            });

            await this.dataManager.initialize();

            // Initialize CanvasDataImporter and inject DataManager (P0 Task #3)
            // Source: Plan - P0 Task #3: 在main.ts初始化时导入Canvas数据
            this.canvasDataImporter = new CanvasDataImporterService(this.app);
            this.canvasDataImporter.setDataManager(this.dataManager);

            if (this.settings.debugMode) {
                console.log('Canvas Review System: DataManager initialized');
                console.log('Canvas Review System: CanvasDataImporter initialized');
            }
        } catch (error) {
            console.error('Canvas Review System: Failed to initialize DataManager:', error);
            new Notice('Canvas Review System: Database initialization failed. Check console.');
        }

        // Initialize NotificationService (Story 14.7)
        try {
            this.notificationService = createNotificationService(this.app, {
                enableNotifications: this.settings.enableNotifications,
                quietHoursStart: this.settings.quietHoursStart,
                quietHoursEnd: this.settings.quietHoursEnd,
                minIntervalHours: this.settings.minNotificationInterval,
            });

            // Connect notification service to data manager
            if (this.dataManager) {
                this.notificationService.setDataManager(this.dataManager);
            }

            // Set callback for opening dashboard
            this.notificationService.setDashboardOpenCallback(() => {
                this.showReviewDashboard();
            });

            if (this.settings.debugMode) {
                console.log('Canvas Review System: NotificationService initialized');
            }
        } catch (error) {
            console.error('Canvas Review System: Failed to initialize NotificationService:', error);
        }

        // Initialize BackupProtectionManager and ContextMenuManager (Story 13.5)
        try {
            this.backupProtectionManager = new BackupProtectionManager(this.app.vault);
            await this.backupProtectionManager.initialize();

            this.contextMenuManager = new ContextMenuManager(this.app, this.backupProtectionManager);
            this.contextMenuManager.initialize(this);

            // Initialize API Client (Story 13.3)
            const apiBaseUrl = this.settings.claudeCodeUrl || 'http://localhost:8000';
            this.apiClient = new ApiClient({
                baseUrl: `${apiBaseUrl}/api/v1`,
                timeout: 30000,
            });

            // Register action callbacks for context menu (Fix for missing Agent options)
            this.contextMenuManager.setActionRegistry({
                executeDecomposition: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在拆解节点...');
                        const result = await this.apiClient.decomposeBasic({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice(`拆解完成: 生成了 ${result.questions?.length || 0} 个问题`);
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'decompose_basic', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeDecomposition?.(context)
                        );
                    }
                },

                executeOralExplanation: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成口语化解释...');
                        const result = await this.apiClient.explainOral({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice('口语化解释生成完成');
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'explain_oral', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeOralExplanation?.(context)
                        );
                    }
                },

                executeFourLevelExplanation: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成四层次解释...');
                        const result = await this.apiClient.explainFourLevel({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice('四层次解释生成完成');
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'explain_four_level', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeFourLevelExplanation?.(context)
                        );
                    }
                },

                executeScoring: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在评分节点...');
                        const result = await this.apiClient.scoreUnderstanding({
                            canvas_name: this.extractCanvasFileName(context.filePath),
                            node_ids: context.nodeId ? [context.nodeId] : [],
                        });
                        new Notice(`评分完成: ${result.scores?.length || 0} 个节点已评分`);
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'score_understanding', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeScoring?.(context)
                        );
                    }
                },

                generateComparisonTable: async (context: MenuContext) => {
                    new Notice('对比表功能开发中...');
                },

                viewNodeHistory: async (context: MenuContext) => {
                    new Notice('节点历史功能开发中...');
                },

                addToReviewPlan: async (context: MenuContext) => {
                    new Notice('添加到复习计划功能开发中...');
                },

                openReviewDashboard: async (_context: MenuContext) => {
                    this.showReviewDashboard();
                },

                generateVerificationCanvas: async (context: MenuContext) => {
                    new Notice('生成检验白板功能开发中...');
                },

                // Story 25.1: Cross-Canvas UI Entry Points (AC1, AC2)
                openCrossCanvasModal: async (context: MenuContext) => {
                    const filePath = context.filePath;
                    if (!filePath) {
                        new Notice('无法获取Canvas文件路径');
                        return;
                    }
                    const file = this.app.vault.getAbstractFileByPath(filePath);
                    if (file instanceof TFile) {
                        this.openCrossCanvasModal(file);
                    } else {
                        new Notice('无法找到Canvas文件');
                    }
                },

                viewAssociatedCanvas: async (context: MenuContext) => {
                    const filePath = context.filePath;
                    if (!filePath) {
                        new Notice('无法获取Canvas文件路径');
                        return;
                    }
                    const file = this.app.vault.getAbstractFileByPath(filePath);
                    if (file instanceof TFile) {
                        this.showJumpToAssociatedCanvasModal(file);
                    } else {
                        new Notice('无法找到Canvas文件');
                    }
                },

                // 5 Additional Learning Agent Callbacks
                executeDeepDecomposition: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在进行深度拆解...');
                        const result = await this.apiClient.decomposeDeep({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice(`深度拆解完成: 生成了 ${result.questions?.length || 0} 个深度问题`);
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'decompose_deep', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeDeepDecomposition?.(context)
                        );
                    }
                },

                executeClarificationPath: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成澄清路径...');
                        const result = await this.apiClient.explainClarification({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice('澄清路径生成完成');
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'explain_clarification', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeClarificationPath?.(context)
                        );
                    }
                },

                executeExampleTeaching: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成例题教学...');
                        const result = await this.apiClient.explainExample({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice('例题教学生成完成');
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'explain_example', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeExampleTeaching?.(context)
                        );
                    }
                },

                executeMemoryAnchor: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成记忆锚点...');
                        const result = await this.apiClient.explainMemory({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice('记忆锚点生成完成');
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'explain_memory', () =>
                            this.contextMenuManager?.getActionRegistry()?.executeMemoryAnchor?.(context)
                        );
                    }
                },

                generateVerificationQuestions: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在生成检验问题...');
                        // Story 12.A.6: Use new verification question API
                        const result = await this.apiClient.generateVerificationQuestions({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice(`检验问题生成完成: 生成了 ${result.questions?.length || 0} 个问题`);
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'generate_verification_questions', () =>
                            this.contextMenuManager?.getActionRegistry()?.generateVerificationQuestions?.(context)
                        );
                    }
                },

                // Story 12.A.6: Question Decomposition Agent
                decomposeQuestion: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    try {
                        new Notice('正在拆解问题...');
                        const result = await this.apiClient.decomposeQuestion({
                            node_id: context.nodeId || '',
                            canvas_name: this.extractCanvasFileName(context.filePath),
                        });
                        new Notice(`问题拆解完成: 生成了 ${result.questions?.length || 0} 个子问题`);
                    } catch (error) {
                        // @source Story 21.5.5 - 增强错误处理
                        this.handleAgentError(error, 'decompose_question', () =>
                            this.contextMenuManager?.getActionRegistry()?.decomposeQuestion?.(context)
                        );
                    }
                },
            });

            if (this.settings.debugMode) {
                console.log('Canvas Review System: ContextMenuManager initialized');
                console.log('Canvas Review System: Action registry configured');
            }
        } catch (error) {
            console.error('Canvas Review System: Failed to initialize ContextMenuManager:', error);
        }

        // Story 13.3 - ApiClient initialized above
        // TODO: Story 13.4+ - Initialize UIManager
        // TODO: Story 13.5+ - Initialize SyncManager

        // Initialize ErrorHistoryManager and ErrorNotificationService (Story 21.5.5)
        // @source Story 21.5.5 - AC 4, 5: 错误历史管理
        try {
            this.errorHistoryManager = new ErrorHistoryManager(this);
            await this.errorHistoryManager.load();

            this.errorNotificationService = new ErrorNotificationService();

            if (this.settings.debugMode) {
                console.log('Canvas Review System: ErrorHistoryManager initialized');
                console.log('Canvas Review System: ErrorNotificationService initialized');
            }
        } catch (error) {
            console.error('Canvas Review System: Failed to initialize error tracking:', error);
        }

        // Initialize BackendProcessManager
        // @source Plan: 后端启动/停止UI实现计划
        try {
            // Extract port from settings URL
            const apiUrl = this.settings.claudeCodeUrl || 'http://localhost:8000';
            const urlMatch = apiUrl.match(/:(\d+)/);
            const port = urlMatch ? parseInt(urlMatch[1], 10) : 8000;

            // Get backend path relative to vault
            // FIX: Removed extra "Canvas/" - backend is at ../backend, not ../Canvas/backend
            const vaultPath = (this.app.vault.adapter as any).basePath || '';
            const backendPath = `${vaultPath}/../backend`;

            this.backendManager = createBackendProcessManager(backendPath, {
                onStatusChange: (status: BackendStatus, message?: string) => {
                    this.backendStatus = status;
                    if (this.settings.debugMode) {
                        console.log(`Canvas Review System: Backend status changed to ${status}`, message);
                    }
                    // Show notice for important status changes
                    if (status === 'running') {
                        new Notice('✅ 后端服务已启动');
                    } else if (status === 'stopped') {
                        new Notice('⏹️ 后端服务已停止');
                    } else if (status === 'error') {
                        new Notice(`❌ 后端服务错误: ${message || '未知错误'}`);
                    }
                },
                onOutput: (data: string) => {
                    if (this.settings.debugMode) {
                        console.log('Backend output:', data);
                    }
                },
                onError: (error: string) => {
                    console.error('Backend error:', error);
                }
            });

            // Override the port from settings
            (this.backendManager as any).config.port = port;

            if (this.settings.debugMode) {
                console.log('Canvas Review System: BackendProcessManager initialized');
                console.log(`Canvas Review System: Backend configured for port ${port}`);
            }
        } catch (error) {
            console.error('Canvas Review System: Failed to initialize BackendProcessManager:', error);
        }
    }

    /**
     * Cleanup manager instances
     *
     * Shuts down all managers properly:
     * - DataManager (Story 14.1)
     * - CommandWrapper (Story 13.3+)
     * - UIManager (Story 13.4+)
     * - SyncManager (Story 13.5+)
     */
    private async cleanupManagers(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Cleaning up managers...');
        }

        // Cleanup DataManager (Story 14.1)
        if (this.dataManager) {
            try {
                await this.dataManager.shutdown();
                this.dataManager = null;
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: DataManager shutdown complete');
                }
            } catch (error) {
                console.error('Canvas Review System: Error shutting down DataManager:', error);
            }
        }

        // Cleanup ContextMenuManager (Story 13.5)
        if (this.contextMenuManager) {
            try {
                this.contextMenuManager.cleanup();
                this.contextMenuManager = null;
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: ContextMenuManager cleanup complete');
                }
            } catch (error) {
                console.error('Canvas Review System: Error cleaning up ContextMenuManager:', error);
            }
        }

        // Cleanup BackupProtectionManager
        this.backupProtectionManager = null;

        // Cleanup BackendProcessManager
        if (this.backendManager) {
            try {
                // Stop backend if running when plugin unloads
                if (this.backendManager.getStatus() === 'running') {
                    await this.backendManager.stop();
                }
                this.backendManager = null;
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: BackendProcessManager cleanup complete');
                }
            } catch (error) {
                console.error('Canvas Review System: Error cleaning up BackendProcessManager:', error);
            }
        }

        // TODO: Story 13.3+ - Cleanup CommandWrapper
        // TODO: Story 13.4+ - Cleanup UIManager
        // TODO: Story 13.5+ - Cleanup SyncManager
    }

    /**
     * Get DataManager instance
     *
     * Returns the DataManager for external access (e.g., from UI components)
     */
    getDataManager(): DataManager | null {
        return this.dataManager;
    }

    /**
     * Register custom views (Story 14.2)
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (registerView)
     */
    private registerViews(): void {
        // Register Review Dashboard View
        this.registerView(
            VIEW_TYPE_REVIEW_DASHBOARD,
            (leaf) => new ReviewDashboardView(leaf, this)
        );

        // Register Progress Tracker View (Story 19.3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (registerView)
        this.registerView(
            VIEW_TYPE_PROGRESS_TRACKER,
            (leaf) => new ProgressTrackerView(leaf, this)
        );

        // Register Cross-Canvas Sidebar View (Story 25.1 AC4)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (registerView)
        this.registerView(
            VIEW_TYPE_CROSS_CANVAS_SIDEBAR,
            (leaf) => new CrossCanvasSidebarView(leaf, this)
        );

        if (this.settings.debugMode) {
            console.log('Canvas Review System: Views registered');
        }
    }

    /**
     * Register plugin commands
     *
     * Registers commands available in the command palette:
     * - Show Review Dashboard (main command for AC 6)
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.addCommand)
     */
    private registerCommands(): void {
        // Register "Show Review Dashboard" command (Story 14.2)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'show-review-dashboard',
            name: 'Show Review Dashboard',
            callback: async () => {
                await this.showReviewDashboard();
            }
        });

        // Register "Show Progress Tracker" command (Story 19.3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'show-progress-tracker',
            name: 'Show Verification Progress Tracker (检验进度追踪)',
            callback: async () => {
                await this.showProgressTracker();
            }
        });

        // Register "Sync Canvas Progress" command
        this.addCommand({
            id: 'sync-canvas-progress',
            name: 'Sync Canvas Progress',
            callback: async () => {
                await this.syncCanvasProgress();
            }
        });

        // Register "Open Settings" command
        this.addCommand({
            id: 'open-settings',
            name: 'Open Canvas Review Settings',
            callback: () => {
                // ✅ Verified from Context7: /obsidianmd/obsidian-api (app.setting.open)
                (this.app as any).setting.open();
                (this.app as any).setting.openTabById('canvas-review-system');
            }
        });

        // Register "Create Backup" command (Story 14.1)
        this.addCommand({
            id: 'create-backup',
            name: 'Create Canvas Data Backup',
            callback: async () => {
                if (!this.dataManager) {
                    new Notice('Canvas Review System: Database not initialized');
                    return;
                }

                new Notice('Canvas Review System: Creating backup...');

                try {
                    const result = await this.dataManager.createBackup('Manual backup via command');
                    if (result.success) {
                        new Notice(`Canvas Review System: Backup created at ${result.path}`);
                    } else {
                        new Notice(`Canvas Review System: Backup failed - ${result.error}`);
                    }
                } catch (error) {
                    console.error('Canvas Review System: Backup error:', error);
                    new Notice('Canvas Review System: Backup failed. Check console.');
                }
            }
        });

        // Register "Run Diagnostics" command
        this.addCommand({
            id: 'run-diagnostics',
            name: 'Run Canvas Review Diagnostics',
            callback: async () => {
                await this.runDiagnostics();
            }
        });

        // Register "Intelligent Parallel Processing" command (Story 13.8)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with checkCallback)
        // ✅ Verified from Story 13.8 Dev Notes: Canvas-specific command with view detection
        this.addCommand({
            id: 'canvas-intelligent-parallel',
            name: 'Intelligent Batch Processing (智能批量处理)',
            icon: 'zap',
            checkCallback: (checking: boolean) => {
                // Check if active view is a Canvas view
                const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
                const activeFile = this.app.workspace.getActiveFile();
                const isCanvasView = activeFile?.extension === 'canvas';

                if (isCanvasView) {
                    if (!checking) {
                        this.handleIntelligentParallelClick();
                    }
                    return true;
                }
                return false;
            }
        });

        // Register "Import Canvas Data" command (P0 Task #3)
        // Source: Plan - P0 Task #3: 在main.ts初始化时导入Canvas数据
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'import-canvas-data',
            name: 'Import Canvas Review Items (导入Canvas复习项)',
            callback: async () => {
                if (this.canvasDataImporter) {
                    await this.canvasDataImporter.quickImport();
                } else {
                    new Notice('❌ Canvas Data Importer not initialized');
                }
            }
        });

        // ══════════════════════════════════════════════════════════════════
        // Story 25.1: Cross-Canvas UI Entry Points (AC3 - Command Palette)
        // ══════════════════════════════════════════════════════════════════

        // Register "Create Canvas Association" command (Story 25.1 AC3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with checkCallback)
        this.addCommand({
            id: 'cross-canvas-create-association',
            name: 'Canvas: 创建Canvas关联 (Create Canvas Association)',
            icon: 'link',
            checkCallback: (checking: boolean) => {
                const activeFile = this.app.workspace.getActiveFile();
                const isCanvasView = activeFile?.extension === 'canvas';

                if (isCanvasView) {
                    if (!checking) {
                        this.openCrossCanvasModal(activeFile);
                    }
                    return true;
                }
                return false;
            }
        });

        // Register "View All Associations" command (Story 25.1 AC3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'cross-canvas-view-associations',
            name: 'Canvas: 查看所有关联 (View All Associations)',
            icon: 'list',
            callback: async () => {
                await this.showCrossCanvasSidebar();
            }
        });

        // Register "Jump to Associated Canvas" command (Story 25.1 AC3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with checkCallback)
        this.addCommand({
            id: 'cross-canvas-jump-to-associated',
            name: 'Canvas: 跳转到关联Canvas (Jump to Associated Canvas)',
            icon: 'external-link',
            checkCallback: (checking: boolean) => {
                const activeFile = this.app.workspace.getActiveFile();
                const isCanvasView = activeFile?.extension === 'canvas';

                if (isCanvasView) {
                    if (!checking) {
                        this.showJumpToAssociatedCanvasModal(activeFile);
                    }
                    return true;
                }
                return false;
            }
        });

        // Register "Manage Canvas Associations" command (Story 25.1 AC3)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'cross-canvas-manage-associations',
            name: 'Canvas: 管理Canvas关联 (Manage Canvas Associations)',
            icon: 'settings',
            callback: async () => {
                await this.showCrossCanvasSidebar();
                new Notice('Canvas关联管理面板已打开');
            }
        });

        // ══════════════════════════════════════════════════════════════════
        // Backend Service Control Commands
        // @source Plan: 后端启动/停止UI实现计划
        // ══════════════════════════════════════════════════════════════════

        // Register "Toggle Backend" command
        this.addCommand({
            id: 'backend-toggle',
            name: 'Backend: 切换后端状态 (Toggle Backend Server)',
            icon: 'play',
            callback: async () => {
                if (!this.backendManager) {
                    new Notice('后端管理器未初始化');
                    return;
                }
                const currentStatus = this.backendManager.getStatus();
                if (currentStatus === 'running') {
                    new Notice('⏳ 正在停止后端服务...');
                    await this.backendManager.stop();
                } else if (currentStatus === 'stopped' || currentStatus === 'error') {
                    new Notice('⏳ 正在启动后端服务...');
                    await this.backendManager.start();
                } else {
                    new Notice(`后端服务当前状态: ${currentStatus}`);
                }
            }
        });

        // Register "Start Backend" command
        this.addCommand({
            id: 'backend-start',
            name: 'Backend: 启动后端 (Start Backend Server)',
            icon: 'play',
            callback: async () => {
                if (!this.backendManager) {
                    new Notice('后端管理器未初始化');
                    return;
                }
                const status = this.backendManager.getStatus();
                if (status === 'running') {
                    new Notice('后端服务已在运行中');
                    return;
                }
                new Notice('⏳ 正在启动后端服务...');
                await this.backendManager.start();
            }
        });

        // Register "Stop Backend" command
        this.addCommand({
            id: 'backend-stop',
            name: 'Backend: 停止后端 (Stop Backend Server)',
            icon: 'square',
            callback: async () => {
                if (!this.backendManager) {
                    new Notice('后端管理器未初始化');
                    return;
                }
                const status = this.backendManager.getStatus();
                if (status === 'stopped') {
                    new Notice('后端服务已停止');
                    return;
                }
                new Notice('⏳ 正在停止后端服务...');
                await this.backendManager.stop();
            }
        });

        // Register "Backend Status" command
        this.addCommand({
            id: 'backend-status',
            name: 'Backend: 查看后端状态 (Show Backend Status)',
            icon: 'info',
            callback: () => {
                if (!this.backendManager) {
                    new Notice('后端管理器未初始化');
                    return;
                }
                const status = this.backendManager.getStatus();
                const statusEmoji: Record<BackendStatus, string> = {
                    'stopped': '⏹️',
                    'starting': '⏳',
                    'running': '✅',
                    'stopping': '⏳',
                    'error': '❌'
                };
                const apiUrl = this.settings.claudeCodeUrl || 'http://localhost:8000';
                new Notice(`${statusEmoji[status]} 后端状态: ${status}\n地址: ${apiUrl}`);
            }
        });

        if (this.settings.debugMode) {
            console.log('Canvas Review System: Commands registered');
        }
    }

    /**
     * Show the review dashboard (Story 14.2)
     *
     * Opens the Review Dashboard view in a new leaf.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (getLeaf, setViewState)
     */
    private async showReviewDashboard(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: showReviewDashboard called');
        }

        const { workspace } = this.app;

        // Check if dashboard is already open
        const existingLeaves = workspace.getLeavesOfType(VIEW_TYPE_REVIEW_DASHBOARD);
        if (existingLeaves.length > 0) {
            // Reveal existing dashboard
            workspace.revealLeaf(existingLeaves[0]);
            return;
        }

        // Open new dashboard in right split
        const leaf = workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({
                type: VIEW_TYPE_REVIEW_DASHBOARD,
                active: true,
            });
            workspace.revealLeaf(leaf);
        }
    }

    /**
     * Show Progress Tracker view (Story 19.3)
     *
     * Opens the verification canvas progress tracker in a right split panel.
     * If already open, reveals the existing view.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (workspace.getRightLeaf, setViewState)
     */
    private async showProgressTracker(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: showProgressTracker called');
        }

        const { workspace } = this.app;

        // Check if progress tracker is already open
        const existingLeaves = workspace.getLeavesOfType(VIEW_TYPE_PROGRESS_TRACKER);
        if (existingLeaves.length > 0) {
            // Reveal existing view
            workspace.revealLeaf(existingLeaves[0]);
            return;
        }

        // Open new progress tracker in right split
        const leaf = workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({
                type: VIEW_TYPE_PROGRESS_TRACKER,
                active: true,
            });
            workspace.revealLeaf(leaf);
        }
    }

    /**
     * Sync Canvas progress data
     *
     * Placeholder implementation.
     * Will be fully implemented in Story 13.2+
     */
    private async syncCanvasProgress(): Promise<void> {
        new Notice('Canvas Review System: Syncing progress...');

        if (this.settings.debugMode) {
            console.log('Canvas Review System: syncCanvasProgress called');
        }

        // TODO: Story 13.2+ - Implement data sync
        // - Connect to Claude Code API
        // - Fetch latest Canvas data
        // - Update local cache
        // - Refresh UI

        // Simulate sync delay for placeholder
        await new Promise(resolve => setTimeout(resolve, 1000));
        new Notice('Canvas Review System: Sync complete (placeholder)');
    }

    /**
     * Setup auto-sync interval
     *
     * Configures periodic syncing based on settings.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (registerInterval)
     */
    private setupAutoSync(): void {
        // Clear existing interval if any
        if (this.autoSyncIntervalId !== null) {
            window.clearInterval(this.autoSyncIntervalId);
            this.autoSyncIntervalId = null;
        }

        if (this.settings.autoSyncInterval > 0) {
            const intervalMs = this.settings.autoSyncInterval * 60 * 1000;

            // ✅ Verified from Context7: /obsidianmd/obsidian-api (registerInterval with setInterval)
            this.autoSyncIntervalId = window.setInterval(() => {
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Auto-sync triggered');
                }
                this.syncCanvasProgress();
            }, intervalMs);

            // Register for automatic cleanup
            this.registerInterval(this.autoSyncIntervalId);

            if (this.settings.debugMode) {
                console.log(`Canvas Review System: Auto-sync enabled every ${this.settings.autoSyncInterval} minutes`);
            }
        }
    }

    /**
     * Apply custom CSS from settings
     */
    private applyCustomCss(): void {
        if (this.settings.customCss) {
            const styleEl = document.createElement('style');
            styleEl.id = 'canvas-review-custom-css';
            styleEl.textContent = this.settings.customCss;
            document.head.appendChild(styleEl);

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Custom CSS applied');
            }
        }
    }

    /**
     * Remove custom CSS
     */
    private removeCustomCss(): void {
        const styleEl = document.getElementById('canvas-review-custom-css');
        if (styleEl) {
            styleEl.remove();
        }
    }

    /**
     * Check and show notification on app ready (Story 14.7)
     *
     * Called when the workspace layout is ready.
     * Checks if there are pending reviews and shows notification.
     */
    private async checkAndShowNotification(): Promise<void> {
        if (!this.notificationService) {
            return;
        }

        try {
            await this.notificationService.checkAndShowNotification();

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Notification check completed');
            }
        } catch (error) {
            console.error('Canvas Review System: Error checking notifications:', error);
        }
    }

    /**
     * Run diagnostics and show results
     */
    private async runDiagnostics(): Promise<void> {
        const validation = validateSettings(this.settings);
        let message = 'Canvas Review System Diagnostics:\n\n';

        // Settings validation
        if (validation.isValid) {
            message += '✅ Settings: Valid\n';
        } else {
            message += '❌ Settings: Invalid\n';
            validation.errors.forEach(err => {
                message += `   - ${err}\n`;
            });
        }

        // Warnings
        if (validation.warnings.length > 0) {
            message += '\n⚠️ Warnings:\n';
            validation.warnings.forEach(warn => {
                message += `   - ${warn}\n`;
            });
        }

        // Database health (Story 14.1)
        message += `\n🗄️ Database:\n`;
        if (this.dataManager) {
            try {
                const health = await this.dataManager.getHealthStatus();
                message += `   Status: ${health.initialized ? '✅ Connected' : '❌ Disconnected'}\n`;
                message += `   Version: ${health.databaseVersion}\n`;
                message += `   Pending Migrations: ${health.hasPendingMigrations ? 'Yes' : 'No'}\n`;
                message += `   Review Records: ${health.reviewCount}\n`;
                message += `   Sessions: ${health.sessionCount}\n`;
                message += `   Last Backup: ${health.lastBackup ? health.lastBackup.toLocaleString() : 'Never'}\n`;
                message += `   Auto-backup: ${health.autoBackupEnabled ? 'Enabled' : 'Disabled'}\n`;
            } catch (error) {
                message += `   Status: ❌ Error\n`;
                message += `   Error: ${(error as Error).message}\n`;
            }
        } else {
            message += `   Status: ❌ Not initialized\n`;
        }

        // Connection info
        message += `\n📡 Connection:\n`;
        message += `   URL: ${this.settings.claudeCodeUrl || 'Not configured'}\n`;
        message += `   Cache: ${this.settings.enableCache ? 'Enabled' : 'Disabled'}\n`;
        message += `   Timeout: ${this.settings.commandTimeout / 1000}s\n`;

        // Storage info
        message += `\n💾 Storage:\n`;
        message += `   Path: ${this.settings.dataPath || 'Not configured'}\n`;
        message += `   Auto-backup: ${this.settings.autoBackup ? 'Enabled' : 'Disabled'}\n`;
        message += `   Auto-sync: ${this.settings.autoSyncInterval > 0 ? `${this.settings.autoSyncInterval}min` : 'Disabled'}\n`;

        // Debug info
        message += `\n🔧 Debug:\n`;
        message += `   Debug mode: ${this.settings.debugMode ? 'On' : 'Off'}\n`;
        message += `   Performance monitoring: ${this.settings.enablePerformanceMonitoring ? 'On' : 'Off'}\n`;
        message += `   Experimental features: ${this.settings.enableExperimentalFeatures ? 'On' : 'Off'}\n`;

        console.log(message);
        new Notice('Diagnostics complete. Check console for details.');
    }

    /**
     * Handle intelligent parallel processing click (Story 13.8)
     *
     * Initiates the intelligent parallel processing workflow:
     * 1. Gets selected nodes from Canvas (or all red/purple nodes if none selected)
     * 2. Opens GroupPreviewModal to show intelligent grouping results
     * 3. User confirms processing
     * 4. Opens ProgressMonitorModal to track batch processing
     * 5. Shows ResultSummaryModal with results
     *
     * ✅ Verified from Story 13.8 Dev Notes: Intelligent Parallel Processing UI
     */
    private async handleIntelligentParallelClick(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: handleIntelligentParallelClick called');
        }

        try {
            // Get active Canvas file
            const activeFile = this.app.workspace.getActiveFile();
            if (!activeFile || activeFile.extension !== 'canvas') {
                new Notice('Please open a Canvas file first');
                return;
            }

            // Get Canvas content
            const canvasContent = await this.app.vault.read(activeFile);
            let canvasData: { nodes?: any[] };
            try {
                canvasData = JSON.parse(canvasContent);
            } catch (parseError) {
                new Notice('Failed to parse Canvas file');
                console.error('Canvas Review System: Canvas parse error:', parseError);
                return;
            }

            // Count eligible nodes (red/purple nodes)
            const nodes = canvasData.nodes || [];
            const eligibleNodes: CanvasNode[] = nodes
                .filter((node: any) => {
                    const color = node.color;
                    // Red nodes: color = "1" or "red", Purple nodes: color = "6" or "purple"
                    return color === '1' || color === 'red' ||
                           color === '6' || color === 'purple' ||
                           color === '#ff0000' || color === '#a855f7';
                })
                .map((node: any) => ({
                    id: node.id,
                    type: node.type,
                    text: node.text,
                    color: node.color,
                    x: node.x,
                    y: node.y,
                    width: node.width,
                    height: node.height,
                }));

            if (eligibleNodes.length === 0) {
                new Notice('No red or purple nodes found in Canvas. Intelligent processing requires nodes that need review.');
                return;
            }

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Eligible nodes:', eligibleNodes.length);
                console.log('Canvas Review System: Canvas path:', activeFile.path);
            }

            // Open GroupPreviewModal
            // ✅ Verified from @obsidian-canvas Skill (Modal API)
            const modal = new GroupPreviewModal(
                this.app,
                activeFile,
                eligibleNodes,
                this.settings.claudeCodeUrl || 'http://localhost:8000/api/v1',
                {
                    onConfirm: (sessionId: string, groups: NodeGroup[]) => {
                        this.handleGroupProcessingConfirm(activeFile, sessionId, groups);
                    },
                    onCancel: () => {
                        if (this.settings.debugMode) {
                            console.log('Canvas Review System: Intelligent parallel processing cancelled');
                        }
                    }
                }
            );
            modal.open();

        } catch (error) {
            console.error('Canvas Review System: Intelligent parallel processing error:', error);
            new Notice('Error starting intelligent batch processing. Check console for details.');
        }
    }

    /**
     * Handle group processing confirmation (Story 13.8 Task 3)
     *
     * Called when user confirms processing in GroupPreviewModal.
     * Opens ProgressMonitorModal to track batch processing.
     *
     * @param canvasFile - The Canvas file being processed
     * @param sessionId - Session ID from API
     * @param groups - Node groups to process
     */
    private async handleGroupProcessingConfirm(
        canvasFile: TFile,
        sessionId: string,
        groups: NodeGroup[]
    ): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Processing confirmed');
            console.log('Canvas Review System: Session ID:', sessionId);
            console.log('Canvas Review System: Groups:', groups.length);
        }

        new Notice(`Starting batch processing for ${groups.length} groups...`);

        // Derive WebSocket URL from API base URL
        // http://localhost:8000 → ws://localhost:8000
        // https://example.com → wss://example.com
        const apiBaseUrl = this.settings.claudeCodeUrl;
        const wsBaseUrl = apiBaseUrl
            .replace(/^https:\/\//, 'wss://')
            .replace(/^http:\/\//, 'ws://');

        // Confirm session with API before opening progress modal
        try {
            const confirmResponse = await fetch(`${apiBaseUrl}/canvas/intelligent-parallel/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                }),
            });

            if (!confirmResponse.ok) {
                const errorData = await confirmResponse.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${confirmResponse.status}`);
            }

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Session confirmed, opening progress monitor');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            new Notice(`Failed to confirm session: ${message}`);
            console.error('Canvas Review System: Failed to confirm session:', err);
            return;
        }

        // Open ProgressMonitorModal
        const progressCallbacks: ProgressMonitorCallbacks = {
            onComplete: (results: SessionStatus) => {
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Processing complete', results);
                }

                // Open ResultSummaryModal
                const resultCallbacks: ResultSummaryCallbacks = {
                    onClose: () => {
                        if (this.settings.debugMode) {
                            console.log('Canvas Review System: Result summary closed');
                        }
                    },
                    onRetryNode: async (nodeId: string, agent: string): Promise<boolean> => {
                        try {
                            const response = await fetch(`${apiBaseUrl}/canvas/single-agent`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
                                },
                                body: JSON.stringify({
                                    canvas_path: canvasFile.path,
                                    node_id: nodeId,
                                    agent: agent,
                                }),
                            });
                            return response.ok;
                        } catch (err) {
                            console.error('Canvas Review System: Retry failed:', err);
                            return false;
                        }
                    },
                };

                const resultModal = new ResultSummaryModal(
                    this.app,
                    canvasFile,
                    results,
                    groups,
                    apiBaseUrl,
                    resultCallbacks
                );
                resultModal.open();
            },
            onCancel: () => {
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Processing cancelled');
                }
                new Notice('Batch processing was cancelled.');
            },
        };

        const progressModal = new ProgressMonitorModal(
            this.app,
            canvasFile,
            sessionId,
            groups,
            apiBaseUrl,
            wsBaseUrl,
            progressCallbacks
        );
        progressModal.open();
    }

    /**
     * Load settings from storage with migration support
     *
     * Loads saved settings, merges with defaults, and migrates if needed.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (loadSettings pattern)
     */
    async loadSettings(): Promise<void> {
        const savedData = await this.loadData();

        // Migrate settings if needed (handles version upgrades)
        if (savedData) {
            this.settings = migrateSettings(savedData);

            // Save migrated settings if version changed
            if (savedData.settingsVersion !== this.settings.settingsVersion) {
                await this.saveSettings();
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Settings migrated to version', this.settings.settingsVersion);
                }
            }
        } else {
            this.settings = { ...DEFAULT_SETTINGS };
        }
    }

    /**
     * Save settings to storage
     *
     * Validates and persists current settings.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (saveSettings pattern)
     */
    async saveSettings(): Promise<void> {
        const validation = validateSettings(this.settings);
        if (!validation.isValid) {
            console.warn('Canvas Review System: Invalid settings:', validation.errors);
        }
        if (validation.warnings.length > 0) {
            console.warn('Canvas Review System: Settings warnings:', validation.warnings);
        }
        await this.saveData(this.settings);

        // Re-apply custom CSS when settings are saved
        this.removeCustomCss();
        this.applyCustomCss();

        // Restart auto-sync with new interval
        this.setupAutoSync();
    }

    // ══════════════════════════════════════════════════════════════════
    // Story 25.1: Cross-Canvas UI Entry Points - Helper Methods
    // ══════════════════════════════════════════════════════════════════

    /**
     * Open Cross-Canvas Modal for creating associations (Story 25.1 AC1, AC3)
     *
     * Opens the CrossCanvasModal to allow user to create an association
     * from the current Canvas to another Canvas file.
     *
     * @param canvasFile - The source Canvas file for the association
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal.open)
     */
    private openCrossCanvasModal(canvasFile: TFile): void {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Opening CrossCanvasModal for:', canvasFile.path);
        }

        // ✅ Verified from CrossCanvasModal.ts (createCrossCanvasModal signature)
        const modal = createCrossCanvasModal(
            this.app,
            canvasFile.path,
            this.crossCanvasService || null,
            (association: CrossCanvasAssociation) => {
                new Notice(`Canvas关联创建成功: ${canvasFile.basename} → ${association.targetCanvasTitle}`);
                // Refresh sidebar if open
                this.refreshCrossCanvasSidebar();
            }
        );
        modal.open();
    }

    /**
     * Show Cross-Canvas Sidebar (Story 25.1 AC4)
     *
     * Opens the Cross-Canvas sidebar view in a right split panel.
     * If already open, reveals the existing view.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (workspace.getRightLeaf, setViewState)
     */
    private async showCrossCanvasSidebar(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: showCrossCanvasSidebar called');
        }

        const { workspace } = this.app;

        // Check if sidebar is already open
        const existingLeaves = workspace.getLeavesOfType(VIEW_TYPE_CROSS_CANVAS_SIDEBAR);
        if (existingLeaves.length > 0) {
            // Reveal existing view
            workspace.revealLeaf(existingLeaves[0]);
            return;
        }

        // Open new sidebar in right split
        const leaf = workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({
                type: VIEW_TYPE_CROSS_CANVAS_SIDEBAR,
                active: true,
            });
            workspace.revealLeaf(leaf);
        }
    }

    /**
     * Refresh Cross-Canvas Sidebar if open (Story 25.1)
     *
     * Triggers a refresh of the Cross-Canvas sidebar view if it's currently open.
     */
    private refreshCrossCanvasSidebar(): void {
        const existingLeaves = this.app.workspace.getLeavesOfType(VIEW_TYPE_CROSS_CANVAS_SIDEBAR);
        if (existingLeaves.length > 0) {
            const view = existingLeaves[0].view as CrossCanvasSidebarView;
            if (view && typeof view.refresh === 'function') {
                view.refresh();
            }
        }
    }

    /**
     * Show Jump to Associated Canvas Modal (Story 25.1 AC5)
     *
     * Opens a modal showing all associations for the current Canvas,
     * allowing quick navigation to associated Canvas files.
     *
     * @param canvasFile - The current Canvas file
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (SuggestModal pattern)
     */
    private async showJumpToAssociatedCanvasModal(canvasFile: TFile): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: showJumpToAssociatedCanvasModal for:', canvasFile.path);
        }

        const apiBaseUrl = this.settings.claudeCodeUrl || 'http://localhost:8000';

        try {
            // Fetch associations for current Canvas
            const response = await fetch(`${apiBaseUrl}/api/v1/cross-canvas/associations?canvas_path=${encodeURIComponent(canvasFile.path)}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const associations = await response.json();

            if (!associations || associations.length === 0) {
                new Notice('当前Canvas没有关联。使用 "创建Canvas关联" 命令添加关联。');
                return;
            }

            // Create quick jump modal using Obsidian's SuggestModal pattern
            const { FuzzySuggestModal } = await import('obsidian');

            class JumpToCanvasModal extends FuzzySuggestModal<{ path: string; type: string; title: string }> {
                constructor(app: App, private associations: any[]) {
                    super(app);
                    this.setPlaceholder('选择要跳转的Canvas...');
                }

                getItems(): { path: string; type: string; title: string }[] {
                    return this.associations.map((a: any) => ({
                        path: a.target_canvas_path || a.targetPath,
                        type: a.association_type || a.type,
                        title: (a.target_canvas_path || a.targetPath).split('/').pop()?.replace('.canvas', '') || 'Unknown',
                    }));
                }

                getItemText(item: { path: string; type: string; title: string }): string {
                    return `${item.title} (${item.type})`;
                }

                async onChooseItem(item: { path: string; type: string; title: string }): Promise<void> {
                    await this.app.workspace.openLinkText(item.path, '', true);
                }
            }

            const modal = new JumpToCanvasModal(this.app, associations);
            modal.open();

        } catch (error) {
            const msg = error instanceof Error ? error.message : 'Unknown error';
            new Notice(`获取Canvas关联失败: ${msg}`);
            console.error('Canvas Review System: Failed to fetch associations:', error);
        }
    }

    // ══════════════════════════════════════════════════════════════════
    // Story 21.5.5: Enhanced Error Handling - Helper Methods
    // ══════════════════════════════════════════════════════════════════

    /**
     * 提取 Canvas 路径 (不含 .canvas 扩展名)
     *
     * 后端 canvas_service.py 期望格式: "子目录/文件名" (无扩展名)
     * 后端会自动添加 .canvas 扩展名
     *
     * @param filePath - Complete file path (e.g., "Canvas/Math53/Lecture5.canvas")
     * @returns Canvas path without extension (e.g., "Canvas/Math53/Lecture5")
     *
     * @source Fix for Canvas path truncation issue (Agent API 500 Error)
     *
     * @example
     * extractCanvasFileName("Canvas/Math53/Lecture5.canvas") // "Canvas/Math53/Lecture5"
     * extractCanvasFileName("笔记库/test.canvas") // "笔记库/test"
     * extractCanvasFileName("KP13-线性逼近与微分.md") // "KP13-线性逼近与微分"
     * extractCanvasFileName("test.canvas") // "test"
     * extractCanvasFileName(undefined) // ""
     *
     * @source Story 12.A.1 - AC 1, 2: Canvas名称标准化
     */
    private extractCanvasFileName(filePath: string | undefined): string {
        if (!filePath) return '';
        // ✅ FIX Story 12.A.1: 移除 .canvas 或 .md 扩展名，保留完整路径
        // 修复39次 "无法从AI响应中提取有效内容" 错误
        return filePath.replace(/\.(canvas|md)$/i, '');
    }

    /**
     * Handle Agent API error with enhanced notification and history tracking
     *
     * @param error - The caught error (may be ApiError or generic Error)
     * @param operation - Name of the operation that failed (e.g., 'decompose_basic')
     * @param onRetry - Optional retry callback for retryable errors
     *
     * @source Story 21.5.5 - AC 1, 2, 3: 增强错误显示
     */
    private handleAgentError(
        error: unknown,
        operation: string,
        onRetry?: () => void | Promise<void>
    ): void {
        // Convert to ApiError if it isn't already
        let apiError: ApiError;

        if (error instanceof ApiError) {
            apiError = error;
        } else {
            // Wrap generic error in ApiError
            const msg = error instanceof Error ? error.message : 'Unknown error';
            apiError = new ApiError(msg, 'UnknownError');
        }

        // Log the error
        console.error(`Canvas Review System: ${operation} failed:`, apiError);

        // Record in error history
        if (this.errorHistoryManager) {
            this.errorHistoryManager.addError(apiError, operation);
        }

        // Show enhanced notification
        if (this.errorNotificationService) {
            this.errorNotificationService.showAgentError(apiError, {
                operation,
                onRetry,
            });
        } else {
            // Fallback to basic Notice if service not initialized
            new Notice(`${operation} 失败: ${apiError.getFormattedMessage()}`);
        }
    }
}
