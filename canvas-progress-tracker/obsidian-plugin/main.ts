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
import { CanvasInfoView, VIEW_TYPE_CANVAS_INFO } from './src/views/CanvasInfoView';
import { CrossCanvasModal, createCrossCanvasModal } from './src/modals/CrossCanvasModal';
import type { CrossCanvasAssociation } from './src/types/UITypes';
import { NotificationService, createNotificationService } from './src/services/NotificationService';
import { GroupPreviewModal, CanvasNode, NodeGroup } from './src/modals/GroupPreviewModal';
import { ProgressMonitorModal, ProgressMonitorCallbacks, SessionStatus } from './src/modals/ProgressMonitorModal';
import { ResultSummaryModal, ResultSummaryCallbacks } from './src/modals/ResultSummaryModal';
import { TaskQueueModal, PendingRequest, AGENT_ESTIMATED_TIMES } from './src/modals/TaskQueueModal';
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
import { CanvasFileManager } from './src/managers/CanvasFileManager';
import type { CanvasData, CanvasTextNode } from './src/types/canvas';
import { ScoringCheckpointService, SuggestionChoice } from './src/services/ScoringCheckpointService';
// Story 16.1: Canvas Association UI - Textbook Mounting
import { TextbookMountService } from './src/services/TextbookMountService';
import { CanvasAssociationModal } from './src/modals/CanvasAssociationModal';
import { AssociationFormModal } from './src/modals/AssociationFormModal';
import type { CanvasAssociation, CanvasLinksConfig } from './src/types/AssociationTypes';
import { DEFAULT_CANVAS_LINKS_CONFIG } from './src/types/AssociationTypes';
// Story 30.6: Node Color Change Watcher - monitors canvas color changes for memory triggers
import { NodeColorChangeWatcher, createNodeColorChangeWatcher } from './src/services/NodeColorChangeWatcher';
// Story 16.7: Association Status Bar Indicator
import { AssociationStatusIndicator, createStatusBarIndicator } from './src/views/StatusBarIndicator';
// Story 30.7: Memory Query Service (3-layer memory integration)
import { MemoryQueryService } from './src/services/MemoryQueryService';
// Story 30.7: Graphiti Association Service
import { GraphitiAssociationService } from './src/services/GraphitiAssociationService';
// Story 31.2: Verification History Service - tracks verification canvas relations
import { VerificationHistoryService } from './src/services/VerificationHistoryService';
import type { ReviewMode } from './src/types/UITypes';

/**
 * Story 12.H.2: Node-level Request Queue
 *
 * Ensures only one Agent request executes per node at a time.
 * Subsequent requests for the same node are queued and executed sequentially.
 * Different nodes can process requests concurrently.
 *
 * @source Story 12.H.2 - 同一节点并发 Agent 限制
 */
class NodeRequestQueue {
    /** Map of nodeId -> current Promise chain */
    private nodeQueues: Map<string, Promise<unknown>> = new Map();

    /** Map of nodeId -> currently running Agent type (for user feedback) */
    private nodeAgentTypes: Map<string, string> = new Map();

    /**
     * Enqueue a request for a specific node
     *
     * @param nodeId - The node ID to queue for
     * @param agentType - Agent type name (for user feedback, e.g., '口语化解释')
     * @param fn - The async function to execute
     * @returns The result of fn()
     */
    async enqueue<T>(
        nodeId: string,
        agentType: string,
        fn: () => Promise<T>
    ): Promise<T> {
        // Check if there's a request in progress for this node
        const currentAgent = this.nodeAgentTypes.get(nodeId);
        if (currentAgent) {
            // Notify user that node is busy
            new Notice(`节点正在处理 "${currentAgent}"，请稍候...`);
            console.log(`[Story 12.H.2] Node "${nodeId}" busy with "${currentAgent}", queueing "${agentType}"`);
        }

        // Get current queue for this node (or resolved Promise if none)
        const prev = this.nodeQueues.get(nodeId) || Promise.resolve();

        // Create new Promise that chains after previous
        const current = prev.then(async () => {
            // Set current agent type for this node
            this.nodeAgentTypes.set(nodeId, agentType);
            console.log(`[Story 12.H.2] Starting "${agentType}" for node "${nodeId}"`);

            try {
                return await fn();
            } finally {
                // Cleanup: only remove if this is still the current queue item
                // This ensures we don't remove a newer queue item
                if (this.nodeQueues.get(nodeId) === current) {
                    this.nodeQueues.delete(nodeId);
                    this.nodeAgentTypes.delete(nodeId);
                    console.log(`[Story 12.H.2] Completed "${agentType}" for node "${nodeId}", queue cleared`);
                }
            }
        });

        // Store as current queue item for this node
        this.nodeQueues.set(nodeId, current);
        return current as Promise<T>;
    }

    /**
     * Check if a node has a request in progress
     *
     * @param nodeId - The node ID to check
     * @returns true if node is processing a request
     */
    isProcessing(nodeId: string): boolean {
        return this.nodeQueues.has(nodeId);
    }

    /**
     * Get the currently running Agent type for a node
     *
     * @param nodeId - The node ID to check
     * @returns Agent type string, or undefined if not processing
     */
    getCurrentAgentType(nodeId: string): string | undefined {
        return this.nodeAgentTypes.get(nodeId);
    }
}

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
    public crossCanvasService: CrossCanvasService | null = null;

    /** Canvas File Manager - Reads/writes Canvas files (Story 12.M: Node Creation Fix) */
    private canvasFileManager: CanvasFileManager | null = null;

    /** Error History Manager - Tracks API errors for debugging (Story 21.5.5) */
    public errorHistoryManager: ErrorHistoryManager | null = null;

    /** Error Notification Service - Shows enhanced error notices (Story 21.5.5) */
    private errorNotificationService: ErrorNotificationService | null = null;

    /** Backend Process Manager - Manages FastAPI backend lifecycle */
    public backendManager: BackendProcessManager | null = null;

    /** Current backend status for UI updates */
    private backendStatus: BackendStatus = 'stopped';

    /** Story 12.F.4: Pending requests map for deduplication - prevents duplicate Agent calls */
    private pendingRequests: Map<string, boolean> = new Map();

    /** Story 12.H.3: Task registry for UI display - tracks full task information */
    private taskRegistry: Map<string, PendingRequest> = new Map();

    /** Story 12.H.2: Node-level request queue - ensures one Agent per node at a time */
    private nodeRequestQueue: NodeRequestQueue = new NodeRequestQueue();

    /** Story 2.8: Scoring Checkpoint Service - auto-scores before agent operations */
    private scoringCheckpointService: ScoringCheckpointService | null = null;

    /** Story 16.1: Textbook Mount Service - manages textbook mounting */
    private textbookMountService: TextbookMountService | null = null;

    /** Story 30.6: Node Color Change Watcher - monitors canvas color changes */
    private nodeColorChangeWatcher: NodeColorChangeWatcher | null = null;

    /** Story 16.7: Association Status Bar Indicator */
    private associationStatusIndicator: AssociationStatusIndicator | null = null;

    /** Story 30.7: Memory Query Service (3-layer memory integration) */
    memoryQueryService?: MemoryQueryService;

    /** Story 30.7: Graphiti Association Service */
    graphitiAssociationService?: GraphitiAssociationService;

    /** Story 31.2: Verification History Service - tracks verification canvas relations */
    private verificationHistoryService: VerificationHistoryService | null = null;

    /** Story 30.6: Canvas auto-index debounce timers */
    private indexDebounceTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();

    /**
     * Get API Client instance (Story 38.1)
     *
     * Provides access to the API client for View classes that need
     * to communicate with the backend.
     *
     * @returns ApiClient instance or null if not initialized
     */
    public getApiClient(): ApiClient | null {
        return this.apiClient;
    }

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

            // Story 12.H.3: Add ribbon icon for task queue
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (addRibbonIcon)
            this.addRibbonIcon('list-todo', 'Agent 任务队列 (Task Queue)', () => {
                this.openTaskQueueModal();
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

            // CRITICAL FIX: Kill backend process SYNCHRONOUSLY before Obsidian exits.
            // onunload() is void (not async), so we cannot await backendManager.stop().
            // Previously cleanupManagers() was called without await, causing the backend
            // process to become orphaned. Using execSync ensures the process is killed
            // before Obsidian finishes unloading.
            if (this.backendManager && this.backendManager.getStatus() === 'running') {
                try {
                    const { execSync } = require('child_process');
                    const port = 8000;
                    const netstatResult = execSync(
                        `netstat -ano | findstr :${port} | findstr LISTENING`,
                        { encoding: 'utf8', timeout: 3000 }
                    );
                    const pids = new Set<string>();
                    netstatResult.split('\n').forEach((line: string) => {
                        const parts = line.trim().split(/\s+/);
                        if (parts.length >= 5 && parts[4] !== '0') {
                            pids.add(parts[4]);
                        }
                    });
                    for (const pid of pids) {
                        try {
                            execSync(`taskkill /pid ${pid} /T /F`, { timeout: 3000 });
                            console.log(`Canvas Review System: Killed backend PID ${pid}`);
                        } catch {
                            // Process may already be dead
                        }
                    }
                } catch {
                    // Port not in use or netstat failed - backend already stopped
                }
            }

            // Story 30.6: Clear canvas auto-index debounce timers
            for (const timer of this.indexDebounceTimers.values()) {
                clearTimeout(timer);
            }
            this.indexDebounceTimers.clear();

            // Cleanup managers (non-backend cleanup is fast/sync-safe)
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

            // Story 12.M: Initialize CanvasFileManager for reading/writing Canvas files
            this.canvasFileManager = new CanvasFileManager(this.app.vault);

            this.contextMenuManager = new ContextMenuManager(this.app, this.backupProtectionManager);
            this.contextMenuManager.initialize(this);

            // Initialize API Client (Story 13.3)
            // Story 12.K: Timeout = 150s to match backend AI_TIMEOUT=120s + buffer
            const apiBaseUrl = this.settings.claudeCodeUrl || 'http://localhost:8000';
            this.apiClient = new ApiClient({
                baseUrl: `${apiBaseUrl}/api/v1`,
                timeout: 150000, // 150 seconds (backend AI timeout = 120s + 30s buffer)
            });

            // Initialize Scoring Checkpoint Service (Story 2.8: 嵌入式评分检查点)
            this.scoringCheckpointService = new ScoringCheckpointService(this.app, this.apiClient);
            if (this.settings.debugMode) {
                console.log('Canvas Review System: ScoringCheckpointService initialized');
            }

            // Initialize Textbook Mount Service (Story 16.1: Canvas关联UI - 教材挂载)
            this.textbookMountService = new TextbookMountService(this.app, apiBaseUrl);
            if (this.settings.debugMode) {
                console.log('Canvas Review System: TextbookMountService initialized');
            }

            // Initialize NodeColorChangeWatcher (Story 30.6: Node Color Change Memory Trigger)
            try {
                this.nodeColorChangeWatcher = createNodeColorChangeWatcher(this.app, {
                    apiBaseUrl: `${apiBaseUrl}/api/v1`,
                    enableLogging: this.settings.debugMode,
                });
                await this.nodeColorChangeWatcher.start();
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: NodeColorChangeWatcher initialized and started');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize NodeColorChangeWatcher:', error);
            }

            // Story 30.6: Auto-index canvas on save (debounced 5s)
            this.registerEvent(
                this.app.vault.on('modify', (file) => {
                    if (file instanceof TFile && file.extension === 'canvas') {
                        this.debouncedIndexCanvas(file);
                    }
                })
            );

            // Initialize CrossCanvasService (Story 25.1: Cross-Canvas Association System)
            try {
                this.crossCanvasService = new CrossCanvasService(this.app, apiBaseUrl);
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: CrossCanvasService initialized');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize CrossCanvasService:', error);
            }

            // Story 30.7: Initialize Memory Query Service (3-layer memory integration)
            try {
                this.memoryQueryService = new MemoryQueryService(this.app, {
                    apiBaseUrl: `${apiBaseUrl}/api/v1`,
                });
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: MemoryQueryService initialized');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize MemoryQueryService:', error);
            }

            // Story 30.7: Initialize Graphiti Association Service
            try {
                this.graphitiAssociationService = new GraphitiAssociationService(this.app, {
                    baseUrl: apiBaseUrl,
                });
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: GraphitiAssociationService initialized');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize GraphitiAssociationService:', error);
            }

            // Story 31.2: Initialize Verification History Service
            try {
                this.verificationHistoryService = new VerificationHistoryService(this.app);
                if (this.dataManager) {
                    this.verificationHistoryService.setDataManager(this.dataManager);
                }
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: VerificationHistoryService initialized');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize VerificationHistoryService:', error);
            }

            // Initialize Association Status Bar Indicator (Story 16.7)
            try {
                this.associationStatusIndicator = new AssociationStatusIndicator(this.app, this);

                // Wire up callbacks connecting to CrossCanvasService
                const crossService = this.crossCanvasService;
                if (crossService) {
                    this.associationStatusIndicator.setCallbacks({
                        onRefresh: async () => {
                            // Refresh association data for current canvas
                            await this.associationStatusIndicator?.refresh();
                        },
                        onCleanOrphans: async () => {
                            // Clean orphan associations that reference deleted Canvas files
                            const all = await crossService.getAllAssociations();
                            let cleaned = 0;
                            for (const assoc of all) {
                                const sourceExists = this.app.vault.getAbstractFileByPath(assoc.sourceCanvasPath);
                                const targetExists = this.app.vault.getAbstractFileByPath(assoc.targetCanvasPath);
                                if (!sourceExists || !targetExists) {
                                    await crossService.deleteAssociation(assoc.id);
                                    cleaned++;
                                }
                            }
                            return cleaned;
                        },
                        onOpenModal: () => {
                            const activeFile = this.app.workspace.getActiveFile();
                            if (activeFile?.extension === 'canvas') {
                                this.openCrossCanvasModal(activeFile);
                            } else {
                                this.showCrossCanvasSidebar();
                            }
                        },
                        onGetAssociations: async (canvasPath: string) => {
                            const associations = await crossService.getAssociationsForCanvas(canvasPath);
                            return {
                                canvas_path: canvasPath,
                                association_count: associations.length,
                                sync_status: 'synced' as const,
                                last_sync: new Date().toISOString(),
                                related_canvas_names: associations.map(a => a.targetCanvasTitle || a.targetCanvasPath),
                            };
                        },
                    });
                }

                if (this.settings.debugMode) {
                    console.log('Canvas Review System: AssociationStatusIndicator initialized');
                }
            } catch (error) {
                console.error('Canvas Review System: Failed to initialize AssociationStatusIndicator:', error);
            }

            // Register action callbacks for context menu (Fix for missing Agent options)
            this.contextMenuManager.setActionRegistry({
                executeDecomposition: async (context: MenuContext) => {
                    console.log('[Story 12.K] executeDecomposition callback entered:', { nodeId: context.nodeId, filePath: context.filePath });
                    if (!this.apiClient) {
                        console.error('[Story 12.K] apiClient is null!');
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters
                    const validationError = this.validateAgentParams(context);
                    if (validationError) {
                        console.warn('[Story 12.K] Validation failed:', validationError);
                        new Notice(validationError);
                        return;
                    }
                    console.log('[Story 12.K] Validation passed, calling queue');

                    // Story 2.8: Scoring checkpoint - auto-evaluate before decomposition
                    // Check if auto-scoring is enabled in settings
                    if (this.scoringCheckpointService && this.settings.enableAutoScoring) {
                        const checkpointResult = await this.scoringCheckpointService.runCheckpoint(
                            context,
                            'decomposition',
                            async (choice) => {
                                if (choice.choice === 'accept_suggestion' && choice.suggestedAgent) {
                                    // Execute suggested agent instead
                                    await this.executeSuggestedAgent(choice.suggestedAgent, context);
                                }
                                // continue_original or cancel: handled by runCheckpoint return value
                            }
                        );
                        if (checkpointResult.handled) {
                            console.log('[Story 2.8] Checkpoint handled flow, skipping original operation');
                            return;
                        }
                    }

                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'basic-decomp',
                        '基础拆解',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `basic-decomp-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在拆解节点... (预计20秒)');
                                // Story 12.M: Update result type to include created_nodes and created_edges
                                const result = await this.callAgentWithAbort<{
                                    questions?: string[];
                                    created_nodes?: Array<{
                                        id: string;
                                        type: string;
                                        text?: string;
                                        x: number;
                                        y: number;
                                        width: number;
                                        height: number;
                                        color?: string;
                                    }>;
                                    created_edges?: Array<{
                                        id: string;
                                        fromNode: string;
                                        toNode: string;
                                        fromSide?: string;
                                        toSide?: string;
                                        label?: string;
                                    }>;
                                }>(
                                    lockKey,
                                    '/agents/decompose/basic',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                // Story 12.M: Write created nodes and edges to Canvas
                                const nodesWritten = await this.writeNodesToCanvas(
                                    context.filePath,
                                    result.created_nodes || [],
                                    result.created_edges || []
                                );
                                console.log(`[Story 12.M] Basic decomp: wrote ${nodesWritten} nodes and ${result.created_edges?.length || 0} edges to canvas`);
                                new Notice(`拆解完成: 生成了 ${result.questions?.length || 0} 个问题，已添加到Canvas`);
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'decompose_basic', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeDecomposition?.(context)
                                );
                            }
                        }
                    );
                },

                executeOralExplanation: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }

                    // Story 2.8: Scoring checkpoint - auto-evaluate before oral explanation
                    // Check if auto-scoring is enabled in settings
                    if (this.scoringCheckpointService && this.settings.enableAutoScoring) {
                        const checkpointResult = await this.scoringCheckpointService.runCheckpoint(
                            context,
                            'oral-explanation',
                            async (choice) => {
                                if (choice.choice === 'accept_suggestion' && choice.suggestedAgent) {
                                    await this.executeSuggestedAgent(choice.suggestedAgent, context);
                                }
                            }
                        );
                        if (checkpointResult.handled) {
                            console.log('[Story 2.8] Checkpoint handled flow for oral-explanation');
                            return;
                        }
                    }

                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'oral',
                        '口语化解释',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `oral-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成口语化解释... (预计25秒)');
                                // Story 12.B.2: Pass real-time node content to backend
                                const result = await this.callAgentWithAbort<{ explanation?: string }>(
                                    lockKey,
                                    '/agents/explain/oral',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice('口语化解释生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_oral', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeOralExplanation?.(context)
                                );
                            }
                        }
                    );
                },

                executeFourLevelExplanation: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }

                    // Story 2.8: Scoring checkpoint - auto-evaluate before four-level explanation
                    // Check if auto-scoring is enabled in settings
                    if (this.scoringCheckpointService && this.settings.enableAutoScoring) {
                        const checkpointResult = await this.scoringCheckpointService.runCheckpoint(
                            context,
                            'four-level-explanation',
                            async (choice) => {
                                if (choice.choice === 'accept_suggestion' && choice.suggestedAgent) {
                                    await this.executeSuggestedAgent(choice.suggestedAgent, context);
                                }
                            }
                        );
                        if (checkpointResult.handled) {
                            console.log('[Story 2.8] Checkpoint handled flow for four-level-explanation');
                            return;
                        }
                    }

                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'four-level',
                        '四层次解释',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `four-level-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成四层次解释... (预计45秒)');
                                // Story 12.B.2: Pass real-time node content to backend
                                const result = await this.callAgentWithAbort<{ explanation?: string }>(
                                    lockKey,
                                    '/agents/explain/four-level',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice('四层次解释生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_four_level', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeFourLevelExplanation?.(context)
                                );
                            }
                        }
                    );
                },

                executeScoring: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters
                    const validationError = this.validateAgentParams(context);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'scoring',
                        '评分',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `scoring-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在评分节点... (预计15秒)');
                                const result = await this.callAgentWithAbort<{ scores?: unknown[] }>(
                                    lockKey,
                                    '/agents/score',
                                    {
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_ids: context.nodeId ? [context.nodeId] : [],
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice(`评分完成: ${result.scores?.length || 0} 个节点已评分`);
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'score_understanding', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeScoring?.(context)
                                );
                            }
                        }
                    );
                },

                // Story 12.F.2: Comparison Table - call ActionRegistry implementation
                generateComparisonTable: async (context: MenuContext) => {
                    await this.contextMenuManager?.getActionRegistry()?.executeComparisonTable?.(context);
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

                /**
                 * Story 31.2: Generate Verification Canvas
                 *
                 * Creates a verification canvas from the current canvas's concepts.
                 * - AC-31.2.1: Calls POST /review/generate API
                 * - AC-31.2.2: Backend creates canvas file with naming convention
                 * - AC-31.2.3: Records relation in VerificationHistoryService
                 * - AC-31.2.4: Auto-opens the new verification canvas
                 * - AC-31.2.5: Shows progress and completion notices
                 *
                 * @source Story 31.2 - 检验白板生成端到端对接
                 */
                generateVerificationCanvas: async (context: MenuContext) => {
                    // AC-31.2.1: Check API client initialization
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }

                    // Validate filePath
                    const filePath = context.filePath;
                    if (!filePath) {
                        new Notice('无法获取Canvas文件路径');
                        return;
                    }

                    // AC-31.2.5: Show progress notice (estimated 30s for AI generation)
                    new Notice('正在生成检验白板... 预计30秒');

                    try {
                        // Extract canvas name from file path (without extension)
                        const canvasName = this.extractCanvasFileName(filePath);

                        // AC-31.2.1: Call POST /review/generate API
                        // ✅ Verified from ApiClient.ts:593-601 - generateReview method
                        const response = await this.apiClient.generateReview({
                            source_canvas: canvasName,
                        });

                        // AC-31.2.2: Backend creates canvas file with naming: {原名}_验证_{timestamp}.canvas
                        const verificationCanvasName = response.verification_canvas_name;

                        // AC-31.2.3: Record relation in VerificationHistoryService
                        // ✅ Verified from VerificationHistoryService.ts:123-151 - addRelation method
                        if (this.verificationHistoryService) {
                            // Construct full path for verification canvas
                            // Backend returns just the name, we add .canvas extension
                            const verificationCanvasPath = verificationCanvasName.endsWith('.canvas')
                                ? verificationCanvasName
                                : `${verificationCanvasName}.canvas`;
                            await this.verificationHistoryService.addRelation(
                                filePath,
                                verificationCanvasPath,
                                'fresh' as ReviewMode
                            );
                            if (this.settings.debugMode) {
                                console.log('[Story 31.2] Recorded verification canvas relation:', {
                                    original: filePath,
                                    verification: verificationCanvasPath,
                                });
                            }
                        }

                        // AC-31.2.4: Auto-open the new verification Canvas
                        // ✅ Verified from Context7: /obsidianmd/obsidian-api - workspace.openLinkText
                        await this.app.workspace.openLinkText(
                            verificationCanvasName,
                            filePath,
                            false // don't create if doesn't exist (backend already created it)
                        );

                        // AC-31.2.5: Success notice with node count
                        new Notice(`检验白板生成完成: ${verificationCanvasName} (${response.node_count}个验证节点)`);

                    } catch (error) {
                        // AC-31.2.5: Error handling with user-friendly messages
                        console.error('[Story 31.2] generateVerificationCanvas error:', error);
                        if (error instanceof ApiError) {
                            new Notice(`生成检验白板失败: ${error.message}`);
                        } else if (error instanceof Error) {
                            new Notice(`生成检验白板失败: ${error.message}`);
                        } else {
                            new Notice('生成检验白板失败，请检查后端服务状态');
                        }
                    }
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
                    // Story 12.F.5: Validate parameters
                    const validationError = this.validateAgentParams(context);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }

                    // Story 2.8: Scoring checkpoint - auto-evaluate before deep decomposition
                    // Check if auto-scoring is enabled in settings
                    if (this.scoringCheckpointService && this.settings.enableAutoScoring) {
                        const checkpointResult = await this.scoringCheckpointService.runCheckpoint(
                            context,
                            'deep-decomposition',
                            async (choice) => {
                                if (choice.choice === 'accept_suggestion' && choice.suggestedAgent) {
                                    await this.executeSuggestedAgent(choice.suggestedAgent, context);
                                }
                            }
                        );
                        if (checkpointResult.handled) {
                            console.log('[Story 2.8] Checkpoint handled flow for deep-decomposition');
                            return;
                        }
                    }

                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'deep-decomp',
                        '深度拆解',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `deep-decomp-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在进行深度拆解... (预计40秒)');
                                // Story 12.M: Update result type to include created_nodes and created_edges
                                const result = await this.callAgentWithAbort<{
                                    questions?: string[];
                                    created_nodes?: Array<{
                                        id: string;
                                        type: string;
                                        text?: string;
                                        x: number;
                                        y: number;
                                        width: number;
                                        height: number;
                                        color?: string;
                                    }>;
                                    created_edges?: Array<{
                                        id: string;
                                        fromNode: string;
                                        toNode: string;
                                        fromSide?: string;
                                        toSide?: string;
                                        label?: string;
                                    }>;
                                }>(
                                    lockKey,
                                    '/agents/decompose/deep',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                // Story 12.M: Write created nodes and edges to Canvas
                                const nodesWritten = await this.writeNodesToCanvas(
                                    context.filePath,
                                    result.created_nodes || [],
                                    result.created_edges || []
                                );
                                console.log(`[Story 12.M] Deep decomp: wrote ${nodesWritten} nodes and ${result.created_edges?.length || 0} edges to canvas`);
                                new Notice(`深度拆解完成: 生成了 ${result.questions?.length || 0} 个深度问题，已添加到Canvas`);
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'decompose_deep', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeDeepDecomposition?.(context)
                                );
                            }
                        }
                    );
                },

                executeClarificationPath: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }

                    // Story 2.8: Scoring checkpoint - auto-evaluate before clarification path
                    // Check if auto-scoring is enabled in settings
                    if (this.scoringCheckpointService && this.settings.enableAutoScoring) {
                        const checkpointResult = await this.scoringCheckpointService.runCheckpoint(
                            context,
                            'clarification-path',
                            async (choice) => {
                                if (choice.choice === 'accept_suggestion' && choice.suggestedAgent) {
                                    await this.executeSuggestedAgent(choice.suggestedAgent, context);
                                }
                            }
                        );
                        if (checkpointResult.handled) {
                            console.log('[Story 2.8] Checkpoint handled flow for clarification-path');
                            return;
                        }
                    }

                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'clarification',
                        '澄清路径',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `clarification-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成澄清路径... (预计30秒)');
                                // Story 12.B.2: Pass real-time node content to backend
                                const result = await this.callAgentWithAbort<{ explanation?: string }>(
                                    lockKey,
                                    '/agents/explain/clarification',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice('澄清路径生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_clarification', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeClarificationPath?.(context)
                                );
                            }
                        }
                    );
                },

                executeExampleTeaching: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'example',
                        '例题教学',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `example-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成例题教学... (预计35秒)');
                                // Story 12.B.2: Pass real-time node content to backend
                                const result = await this.callAgentWithAbort<{ explanation?: string }>(
                                    lockKey,
                                    '/agents/explain/example',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice('例题教学生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_example', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeExampleTeaching?.(context)
                                );
                            }
                        }
                    );
                },

                executeMemoryAnchor: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'memory',
                        '记忆锚点',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `memory-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成记忆锚点... (预计20秒)');
                                // Story 12.B.2: Pass real-time node content to backend
                                const result = await this.callAgentWithAbort<{ explanation?: string }>(
                                    lockKey,
                                    '/agents/explain/memory',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice('记忆锚点生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_memory', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeMemoryAnchor?.(context)
                                );
                            }
                        }
                    );
                },

                generateVerificationQuestions: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters
                    const validationError = this.validateAgentParams(context);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'verify',
                        '检验问题',
                        async () => {
                            // Story 12.H.4: Use cancellable request
                            const lockKey = `verify-${context.nodeId || ''}`;
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在生成检验问题... (预计30秒)');
                                // Story 12.A.6: Use new verification question API
                                const result = await this.callAgentWithAbort<{ questions?: unknown[] }>(
                                    lockKey,
                                    '/agents/verification/question',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                    }
                                );
                                // Story 12.H.4 AC5: Check for cancellation before success notice
                                if (result === null) {
                                    return; // Cancelled, skip success notice
                                }
                                new Notice(`检验问题生成完成: 生成了 ${result.questions?.length || 0} 个问题`);
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'generate_verification_questions', () =>
                                    this.contextMenuManager?.getActionRegistry()?.generateVerificationQuestions?.(context)
                                );
                            }
                        }
                    );
                },

                // Story 12.A.6: Question Decomposition Agent
                decomposeQuestion: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters
                    const validationError = this.validateAgentParams(context);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.4: Create lockKey for cancellation
                    const lockKey = `question-${context.nodeId || ''}`;
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'question',
                        '问题拆解',
                        async () => {
                            try {
                                // Story 12.F.6: Show estimated time
                                new Notice('正在拆解问题... (预计25秒)');
                                // Story 12.H.4: Use cancellable request
                                const result = await this.callAgentWithAbort<{ questions?: string[] }>(
                                    lockKey,
                                    '/agents/decompose/question',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                    }
                                );
                                // Story 12.H.4 AC5: Cancelled request returns null, skip success notice
                                if (result === null) {
                                    return;
                                }
                                new Notice(`问题拆解完成: 生成了 ${result.questions?.length || 0} 个子问题`);
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'decompose_question', () =>
                                    this.contextMenuManager?.getActionRegistry()?.decomposeQuestion?.(context)
                                );
                            }
                        }
                    );
                },

                // Story 12.F.2: Comparison Table Agent
                executeComparisonTable: async (context: MenuContext) => {
                    if (!this.apiClient) {
                        new Notice('API客户端未初始化');
                        return;
                    }
                    // Story 12.F.5: Validate parameters (requires content)
                    const validationError = this.validateAgentParams(context, true);
                    if (validationError) {
                        new Notice(validationError);
                        return;
                    }
                    // Story 12.H.4: Create lockKey for cancellation
                    const lockKey = `comparison-${context.nodeId || ''}`;
                    // Story 12.H.2: Node-level queue with deduplication
                    await this.callAgentWithNodeQueue(
                        context.nodeId || '',
                        'comparison',
                        '对比表',
                        async () => {
                            try {
                                new Notice('正在生成对比表... (预计30秒)');
                                // Story 12.H.4: Use cancellable request with real-time node content
                                const result = await this.callAgentWithAbort<{ comparison_table?: string }>(
                                    lockKey,
                                    '/agents/explain/comparison',
                                    {
                                        node_id: context.nodeId || '',
                                        canvas_name: this.extractCanvasFileName(context.filePath),
                                        node_content: context.nodeContent,  // Real-time content
                                    }
                                );
                                // Story 12.H.4 AC5: Cancelled request returns null, skip success notice
                                if (result === null) {
                                    return;
                                }
                                new Notice('对比表生成完成');
                            } catch (error) {
                                // @source Story 21.5.5 - 增强错误处理
                                this.handleAgentError(error, 'explain_comparison', () =>
                                    this.contextMenuManager?.getActionRegistry()?.executeComparisonTable?.(context)
                                );
                            }
                        }
                    );
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
    /**
     * Story 30.6: Debounced canvas auto-index on save
     * Waits 5 seconds after last modification before triggering LanceDB index.
     */
    private debouncedIndexCanvas(file: TFile): void {
        const existing = this.indexDebounceTimers.get(file.path);
        if (existing) clearTimeout(existing);

        const timer = setTimeout(async () => {
            this.indexDebounceTimers.delete(file.path);
            if (!this.apiClient) return;
            try {
                await this.apiClient.indexCanvas({ canvas_path: file.path });
                if (this.settings.debugMode) {
                    console.log(`Canvas Review System: Auto-indexed ${file.path}`);
                }
            } catch (e) {
                console.warn(`Canvas Review System: Auto-index failed for ${file.path}:`, e);
            }
        }, 5000);

        this.indexDebounceTimers.set(file.path, timer);
    }

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

        // Cleanup NodeColorChangeWatcher (Story 30.6)
        if (this.nodeColorChangeWatcher) {
            this.nodeColorChangeWatcher.stop();
            this.nodeColorChangeWatcher = null;
        }

        // Cleanup AssociationStatusIndicator (Story 16.7)
        if (this.associationStatusIndicator) {
            this.associationStatusIndicator.destroy();
            this.associationStatusIndicator = null;
        }

        // Cleanup CrossCanvasService (Story 25.1)
        this.crossCanvasService = null;

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
            (leaf) => {
                const view = new CrossCanvasSidebarView(leaf, this);
                if (this.crossCanvasService) {
                    view.setCrossCanvasService(this.crossCanvasService);
                }
                return view;
            }
        );

        // Register Canvas Info View (Story 38.1)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (registerView)
        this.registerView(
            VIEW_TYPE_CANVAS_INFO,
            (leaf) => new CanvasInfoView(leaf, this)
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

        // Register "Show Canvas Info" command (Story 38.1)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with checkCallback)
        this.addCommand({
            id: 'show-canvas-info',
            name: 'Canvas: 显示 Canvas Info (Show Canvas Info)',
            checkCallback: (checking: boolean) => {
                const activeFile = this.app.workspace.getActiveFile();
                if (activeFile?.extension === 'canvas') {
                    if (!checking) {
                        this.showCanvasInfo();
                    }
                    return true;
                }
                return false;
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
        // Story 16.1: Textbook Mount Commands (教材挂载)
        // ══════════════════════════════════════════════════════════════════

        // Register "Mount Textbook" command (Story 16.1)
        // Opens the Canvas Association Modal for managing textbook references
        this.addCommand({
            id: 'mount-textbook',
            name: 'Canvas: 挂载教材 (Mount Textbook)',
            icon: 'book-open',
            checkCallback: (checking: boolean) => {
                const activeFile = this.app.workspace.getActiveFile();
                const isCanvasView = activeFile?.extension === 'canvas';

                if (isCanvasView) {
                    if (!checking) {
                        this.openTextbookMountModal(activeFile);
                    }
                    return true;
                }
                return false;
            }
        });

        // Register "View Mounted Textbooks" command (Story 16.1)
        // Shows all textbooks mounted to the current Canvas
        this.addCommand({
            id: 'view-mounted-textbooks',
            name: 'Canvas: 查看挂载的教材 (View Mounted Textbooks)',
            icon: 'book',
            checkCallback: (checking: boolean) => {
                const activeFile = this.app.workspace.getActiveFile();
                const isCanvasView = activeFile?.extension === 'canvas';

                if (isCanvasView) {
                    if (!checking) {
                        this.showMountedTextbooksModal(activeFile);
                    }
                    return true;
                }
                return false;
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

        // ══════════════════════════════════════════════════════════════════
        // Story 12.H.3: Task Queue Commands
        // ══════════════════════════════════════════════════════════════════

        // Register "Open Task Queue" command
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'open-task-queue',
            name: 'Agent: 打开任务队列 (Open Task Queue)',
            icon: 'list-todo',
            callback: () => {
                this.openTaskQueueModal();
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
     * Open Textbook Mount Modal (Story 16.1)
     *
     * Opens the AssociationFormModal for creating a new textbook reference.
     * User can select a PDF or Canvas file as a textbook reference.
     *
     * @param canvasFile - The current Canvas file
     */
    private openTextbookMountModal(canvasFile: TFile): void {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Opening TextbookMountModal for:', canvasFile.path);
        }

        // Open AssociationFormModal for creating new textbook reference
        const modal = new AssociationFormModal(
            this.app,
            canvasFile.path,
            null, // No existing association - creating new
            async (association: CanvasAssociation) => {
                // Save the association to .canvas-links.json
                if (this.textbookMountService) {
                    try {
                        await this.saveTextbookAssociation(canvasFile, association);
                        new Notice(`教材挂载成功: ${association.target_canvas}`);
                    } catch (error) {
                        console.error('Failed to save textbook association:', error);
                        new Notice('教材挂载失败，请查看控制台');
                    }
                } else {
                    new Notice('教材挂载服务未初始化');
                }
            }
        );
        modal.open();
    }

    /**
     * Show Mounted Textbooks Modal (Story 16.1)
     *
     * Opens the CanvasAssociationModal showing all textbooks mounted to the current Canvas.
     * User can view, edit, and delete existing textbook references.
     *
     * @param canvasFile - The current Canvas file
     */
    private async showMountedTextbooksModal(canvasFile: TFile): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Showing mounted textbooks for:', canvasFile.path);
        }

        // Load existing associations from .canvas-links.json
        const config = await this.loadCanvasLinksConfig(canvasFile);
        const associations = config.associations || [];

        // Filter for textbook references only (references type)
        const textbookAssociations = associations.filter(
            a => a.association_type === 'references'
        );

        // Open CanvasAssociationModal
        const modal = new CanvasAssociationModal(
            this.app,
            canvasFile.path,
            textbookAssociations,
            config,
            async (updatedAssociations: CanvasAssociation[]) => {
                // Save updated associations
                await this.saveCanvasLinksConfig(canvasFile, {
                    ...config,
                    associations: updatedAssociations
                });
                new Notice('教材关联已更新');
            },
            () => {
                // Open create modal when user clicks "New Association"
                this.openTextbookMountModal(canvasFile);
            },
            async (targetCanvasPath: string) => {
                // Navigate to target Canvas
                const targetFile = this.app.vault.getAbstractFileByPath(targetCanvasPath);
                if (targetFile && targetFile instanceof TFile) {
                    await this.app.workspace.openLinkText(targetFile.path, '', false);
                } else {
                    new Notice(`找不到文件: ${targetCanvasPath}`);
                }
            }
        );
        modal.open();
    }

    /**
     * Load Canvas Links Configuration (Story 16.2)
     *
     * Loads the .canvas-links.json configuration file for a Canvas.
     *
     * @param canvasFile - The Canvas file
     * @returns The canvas links configuration
     */
    private async loadCanvasLinksConfig(canvasFile: TFile): Promise<CanvasLinksConfig> {
        const configPath = canvasFile.path.replace('.canvas', '.canvas-links.json');
        const configDir = canvasFile.parent?.path;
        const configFilePath = configDir ? `${configDir}/.canvas-links.json` : '.canvas-links.json';

        try {
            const configFile = this.app.vault.getAbstractFileByPath(configFilePath);
            if (configFile && configFile instanceof TFile) {
                const content = await this.app.vault.read(configFile);
                return JSON.parse(content) as CanvasLinksConfig;
            }
        } catch (error) {
            if (this.settings.debugMode) {
                console.log('Canvas links config not found, using defaults:', configFilePath);
            }
        }

        return { ...DEFAULT_CANVAS_LINKS_CONFIG };
    }

    /**
     * Save Canvas Links Configuration (Story 16.2)
     *
     * Saves the .canvas-links.json configuration file for a Canvas.
     *
     * @param canvasFile - The Canvas file
     * @param config - The configuration to save
     */
    private async saveCanvasLinksConfig(canvasFile: TFile, config: CanvasLinksConfig): Promise<void> {
        const configDir = canvasFile.parent?.path;
        const configFilePath = configDir ? `${configDir}/.canvas-links.json` : '.canvas-links.json';

        const content = JSON.stringify(config, null, 2);

        const existingFile = this.app.vault.getAbstractFileByPath(configFilePath);
        if (existingFile && existingFile instanceof TFile) {
            await this.app.vault.modify(existingFile, content);
        } else {
            await this.app.vault.create(configFilePath, content);
        }

        if (this.settings.debugMode) {
            console.log('Saved canvas links config:', configFilePath);
        }
    }

    /**
     * Save Textbook Association (Story 16.1)
     *
     * Saves a new textbook association to the Canvas links config.
     *
     * @param canvasFile - The Canvas file
     * @param association - The association to save
     */
    private async saveTextbookAssociation(canvasFile: TFile, association: CanvasAssociation): Promise<void> {
        const config = await this.loadCanvasLinksConfig(canvasFile);

        // Add source canvas path
        association.source_canvas = canvasFile.path;

        // Add to associations array
        config.associations.push(association);

        // Save updated config
        await this.saveCanvasLinksConfig(canvasFile, config);
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
     * Show Canvas Info sidebar view (Story 38.1)
     *
     * Opens the Canvas Info sidebar in the right panel, showing metadata
     * and index status for the currently active Canvas.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (workspace.getRightLeaf, setViewState)
     */
    private async showCanvasInfo(): Promise<void> {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: showCanvasInfo called');
        }

        const { workspace } = this.app;

        // Check if Canvas Info view is already open
        const existingLeaves = workspace.getLeavesOfType(VIEW_TYPE_CANVAS_INFO);
        if (existingLeaves.length > 0) {
            // Reveal existing view
            workspace.revealLeaf(existingLeaves[0]);
            return;
        }

        // Open new sidebar in right split
        const leaf = workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({
                type: VIEW_TYPE_CANVAS_INFO,
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
     * Story 12.F.5: Validate Agent call parameters
     *
     * Returns error message if validation fails, or null if valid.
     * Provides user-friendly Chinese error messages.
     *
     * @param context - Menu context with node information
     * @param requireContent - Whether node_content is required (default: false)
     * @returns Error message string, or null if valid
     *
     * @source Story 12.F.5 - 前端参数校验
     */
    private validateAgentParams(context: MenuContext, requireContent = false): string | null {
        // Validate canvas_name (via filePath)
        const canvasName = this.extractCanvasFileName(context.filePath);
        if (!canvasName || canvasName.trim() === '') {
            return '请先打开 Canvas 文件';
        }

        // Validate node_id
        if (!context.nodeId || context.nodeId.trim() === '') {
            return '请选择一个节点';
        }

        // Validate node_content if required
        if (requireContent && (context.nodeContent === undefined || context.nodeContent === null)) {
            return '节点内容为空，无法生成解释';
        }

        return null; // Valid
    }

    /**
     * Story 2.8: Execute suggested agent from scoring checkpoint
     *
     * Maps agent type to action registry method and executes it.
     *
     * @param agentType - Agent type identifier (e.g., 'clarification-path')
     * @param context - Menu context to pass to the agent
     */
    private async executeSuggestedAgent(agentType: string, context: MenuContext): Promise<void> {
        const registry = this.contextMenuManager?.getActionRegistry();
        if (!registry) {
            console.warn('[Story 2.8] Action registry not available');
            return;
        }

        console.log(`[Story 2.8] Executing suggested agent: ${agentType}`);

        // Execute the appropriate agent based on type
        switch (agentType) {
            case 'clarification-path':
                await registry.executeClarificationPath?.(context);
                break;
            case 'oral-explanation':
                await registry.executeOralExplanation?.(context);
                break;
            case 'memory-anchor':
                await registry.executeMemoryAnchor?.(context);
                break;
            case 'four-level-explanation':
                await registry.executeFourLevelExplanation?.(context);
                break;
            case 'comparison-table':
                await registry.executeComparisonTable?.(context);
                break;
            case 'deep-decomposition':
                await registry.executeDeepDecomposition?.(context);
                break;
            case 'example-teaching':
                await registry.executeExampleTeaching?.(context);
                break;
            default:
                console.warn(`[Story 2.8] Unknown agent type: ${agentType}`);
        }
    }

    /**
     * Story 12.M: Write created nodes to Canvas file
     *
     * After Agent API returns created_nodes, this method:
     * 1. Gets the current Canvas file
     * 2. Reads existing Canvas data
     * 3. Adds new nodes to the Canvas
     * 4. Writes updated data back to file
     *
     * @param filePath - Canvas file path from context
     * @param createdNodes - Array of nodes returned by backend API
     * @param createdEdges - Array of edges returned by backend API (optional)
     * @returns Number of nodes successfully written
     *
     * @source Story 12.M - Canvas Node Creation Fix
     */
    private async writeNodesToCanvas(
        filePath: string | undefined,
        createdNodes: Array<{
            id: string;
            type: string;
            text?: string;
            x: number;
            y: number;
            width: number;
            height: number;
            color?: string;
        }>,
        createdEdges?: Array<{
            id: string;
            fromNode: string;
            toNode: string;
            fromSide?: string;
            toSide?: string;
            label?: string;
        }>
    ): Promise<number> {
        if (!filePath || !createdNodes || createdNodes.length === 0) {
            console.log('[Story 12.M] No nodes to write or no file path');
            return 0;
        }

        if (!this.canvasFileManager) {
            console.error('[Story 12.M] CanvasFileManager not initialized');
            new Notice('Canvas管理器未初始化');
            return 0;
        }

        try {
            // Get Canvas file
            const canvasFile = this.app.vault.getAbstractFileByPath(filePath);
            if (!canvasFile || !(canvasFile instanceof TFile)) {
                console.error(`[Story 12.M] Canvas file not found: ${filePath}`);
                new Notice('Canvas文件未找到');
                return 0;
            }

            // Read existing Canvas data
            const canvasData = await this.canvasFileManager.readCanvas(canvasFile);
            console.log(`[Story 12.M] Read canvas with ${canvasData.nodes.length} existing nodes`);

            // Add new nodes to Canvas data
            for (const node of createdNodes) {
                const canvasNode: CanvasTextNode = {
                    id: node.id,
                    type: 'text',
                    text: node.text || '',
                    x: node.x,
                    y: node.y,
                    width: node.width,
                    height: node.height,
                    color: node.color as CanvasTextNode['color'],
                };
                canvasData.nodes.push(canvasNode);
                console.log(`[Story 12.M] Added node: ${node.id} at (${node.x}, ${node.y})`);
            }

            // Story 12.M.2: Add edges to Canvas data
            if (createdEdges && createdEdges.length > 0) {
                for (const edge of createdEdges) {
                    const canvasEdge = {
                        id: edge.id,
                        fromNode: edge.fromNode,
                        toNode: edge.toNode,
                        fromSide: edge.fromSide as 'top' | 'bottom' | 'left' | 'right' | undefined,
                        toSide: edge.toSide as 'top' | 'bottom' | 'left' | 'right' | undefined,
                        label: edge.label,
                    };
                    canvasData.edges.push(canvasEdge);
                    console.log(`[Story 12.M] Added edge: ${edge.id} (${edge.fromNode} → ${edge.toNode})`);
                }
            }

            // Write updated Canvas data
            await this.canvasFileManager.writeCanvas(canvasFile, canvasData);
            console.log(`[Story 12.M] Successfully wrote ${createdNodes.length} nodes and ${createdEdges?.length || 0} edges to canvas`);

            // Story 12.M.3: Refresh Canvas view after file write
            // Obsidian Canvas has internal memory cache, writing to file doesn't auto-refresh view
            try {
                const activeLeaf = this.app.workspace.activeLeaf;
                if (activeLeaf?.view?.getViewType() === 'canvas') {
                    const canvas = (activeLeaf.view as any)?.canvas;
                    if (canvas && canvas.file?.path === filePath) {
                        console.log('[Story 12.M.3] Refreshing Canvas view...');

                        // Method 1: Use setData if available (directly updates memory)
                        if (typeof canvas.setData === 'function') {
                            canvas.setData(canvasData);
                            console.log('[Story 12.M.3] Canvas view refreshed via setData()');
                        }
                        // Method 2: Trigger requestFrame to re-render
                        else if (typeof canvas.requestFrame === 'function') {
                            canvas.requestFrame();
                            console.log('[Story 12.M.3] Canvas view refreshed via requestFrame()');
                        }
                        // Method 3: Force reload from file
                        else {
                            // Read file content again and parse
                            const content = await this.app.vault.read(canvasFile);
                            const freshData = JSON.parse(content);
                            if (canvas.data) {
                                canvas.data.nodes = freshData.nodes;
                                canvas.data.edges = freshData.edges;
                            }
                            console.log('[Story 12.M.3] Canvas view refreshed via data override');
                        }
                    } else {
                        console.log('[Story 12.M.3] Active canvas does not match target file, skipping refresh');
                    }
                }
            } catch (refreshError) {
                console.warn('[Story 12.M.3] Failed to refresh Canvas view:', refreshError);
                // Non-fatal: file was already written, user can manually refresh
            }

            return createdNodes.length;
        } catch (error) {
            console.error('[Story 12.M] Failed to write nodes to canvas:', error);
            new Notice(`保存Canvas节点失败: ${error instanceof Error ? error.message : '未知错误'}`);
            return 0;
        }
    }

    /**
     * Story 12.F.4: Execute Agent call with deduplication lock
     *
     * Prevents duplicate API calls when:
     * - User double-clicks menu item
     * - Event bubbling triggers multiple handlers
     * - User clicks again while request is in progress
     *
     * @param lockKey - Unique key for this request (format: `${agentType}-${nodeId}`)
     * @param fn - The async function to execute (API call)
     * @returns Result from fn, or null if request was deduplicated
     *
     * @source Story 12.F.4 - 请求去重机制
     */
    private async callAgentWithLock<T>(
        lockKey: string,
        fn: () => Promise<T>
    ): Promise<T | null> {
        // Check if same request is already in progress
        if (this.pendingRequests.get(lockKey)) {
            console.log(`[Story 12.F.4] Request "${lockKey}" already in progress, skipping`);
            new Notice('请求处理中，请稍候...');
            return null;
        }

        try {
            // Set lock
            this.pendingRequests.set(lockKey, true);
            console.log(`[Story 12.F.4] Request "${lockKey}" started`);

            // Execute the actual API call
            const result = await fn();

            return result;
        } finally {
            // Release lock (always, even on error)
            this.pendingRequests.delete(lockKey);
            console.log(`[Story 12.F.4] Request "${lockKey}" completed`);
        }
    }

    /**
     * Story 12.H.2: Execute Agent call with node-level queue
     * Story 12.H.3: Extended to track tasks in taskRegistry for UI display
     *
     * Combines node-level queueing (one Agent per node) with request deduplication
     * (same Agent+node cannot be called twice).
     *
     * - Same node, different Agents: Queued (sequential execution)
     * - Same node, same Agent: Blocked (deduplication)
     * - Different nodes: Concurrent execution
     *
     * @param nodeId - The node ID to queue for
     * @param agentType - Agent type (for lockKey and user feedback)
     * @param agentDisplayName - User-visible Agent name in Chinese (e.g., '口语化解释')
     * @param fn - The async function to execute (API call)
     * @returns Result from fn, or null if request was blocked
     *
     * @source Story 12.H.2 - 同一节点并发 Agent 限制
     * @source Story 12.H.3 - Task registry integration
     */
    private async callAgentWithNodeQueue<T>(
        nodeId: string,
        agentType: string,
        agentDisplayName: string,
        fn: () => Promise<T>
    ): Promise<T | null> {
        const lockKey = `${agentType}-${nodeId}`;

        // First check if exact same request is in progress (Story 12.F.4)
        if (this.pendingRequests.get(lockKey)) {
            console.log(`[Story 12.H.2] Same request "${lockKey}" in progress, blocking`);
            new Notice('相同请求处理中，请稍候...');
            return null;
        }

        // Story 12.H.3: Register task in registry (status: queued)
        this.registerTask(lockKey, nodeId, agentType, agentDisplayName);

        // Queue through NodeRequestQueue (Story 12.H.2)
        return this.nodeRequestQueue.enqueue(nodeId, agentDisplayName, async () => {
            // Set dedup lock inside the queue
            this.pendingRequests.set(lockKey, true);
            console.log(`[Story 12.H.2] Request "${lockKey}" starting via queue`);

            // Story 12.H.3: Mark task as running
            this.markTaskRunning(lockKey);

            try {
                return await fn();
            } finally {
                this.pendingRequests.delete(lockKey);
                // Story 12.H.3: Unregister completed task
                this.unregisterTask(lockKey);
                console.log(`[Story 12.H.2] Request "${lockKey}" finished`);
            }
        });
    }

    /**
     * Story 12.H.4: Execute cancellable Agent API request
     *
     * Wrapper around ApiClient.callAgentWithCancel that:
     * - Creates and registers AbortController with task registry
     * - Calls the cancellable API method
     * - Returns null if cancelled (AC5: don't write to Canvas)
     *
     * @param lockKey - Unique request identifier (format: `${agentType}-${nodeId}`)
     * @param endpoint - API endpoint path (e.g., '/agents/explain/oral')
     * @param data - Request body data
     * @param timeout - Optional timeout in milliseconds
     * @returns Response data or null if cancelled
     *
     * @source Story 12.H.4 - AC1, AC2, AC5
     */
    private async callAgentWithAbort<T>(
        lockKey: string,
        endpoint: string,
        data: unknown,
        timeout?: number
    ): Promise<T | null> {
        if (!this.apiClient) {
            console.error('[Story 12.H.4] ApiClient not initialized');
            return null;
        }

        // Update task registry with AbortController tracking
        // Note: The actual AbortController is managed inside ApiClient.callAgentWithCancel
        const task = this.taskRegistry.get(lockKey);
        if (task) {
            // Mark that this task is using the cancellable API
            console.log(`[Story 12.H.4] Task "${lockKey}" using cancellable request`);
        }

        // Call the cancellable API method
        const result = await this.apiClient.callAgentWithCancel<T>(
            lockKey,
            endpoint,
            data,
            timeout
        );

        // AC5: null means cancelled, caller should not write to Canvas
        if (result === null) {
            console.log(`[Story 12.H.4] Request "${lockKey}" was cancelled, skipping Canvas write`);
        }

        return result;
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

    // ══════════════════════════════════════════════════════════════════
    // Story 12.H.3: Task Queue Management
    // ══════════════════════════════════════════════════════════════════

    /**
     * Open Task Queue Modal
     *
     * Opens the task queue modal displaying all pending Agent requests.
     *
     * @source Story 12.H.3 - AC: Support Ribbon Icon and Command Palette
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Modal.open)
     */
    private openTaskQueueModal(): void {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Opening Task Queue Modal');
            console.log(`Canvas Review System: ${this.taskRegistry.size} tasks in registry`);
        }

        const modal = new TaskQueueModal(
            this.app,
            this.taskRegistry,
            (lockKey: string) => this.cancelTask(lockKey)
        );
        modal.open();
    }

    /**
     * Cancel a pending task
     *
     * Cancels a task by its lock key and removes it from the registry.
     * Shows cancellation notice to user (AC4).
     *
     * @param lockKey - The unique task identifier (format: `${agentType}-${nodeId}`)
     *
     * @source Story 12.H.3 - AC: Cancel button functionality
     * @source Story 12.H.4 - AC3, AC4, AC6: Cancel request support
     */
    private cancelTask(lockKey: string): void {
        const task = this.taskRegistry.get(lockKey);

        if (task) {
            // Story 12.H.4 AC3: Cancel via ApiClient if available (preferred method)
            // This triggers AbortController.abort() internally
            if (this.apiClient) {
                const cancelled = this.apiClient.cancelRequest(lockKey);
                if (cancelled) {
                    console.log(`[Story 12.H.4] Task "${lockKey}" cancelled via ApiClient`);
                }
            }

            // Story 12.H.4: Also abort local AbortController if ApiClient didn't handle it
            if (task.abortController) {
                task.abortController.abort();
                console.log(`[Story 12.H.4] Task "${lockKey}" aborted via local AbortController`);
            }

            // Story 12.H.4 AC4: Show cancellation notice
            new Notice(`已取消: ${task.agentDisplayName}`);

            // Remove from task registry
            this.taskRegistry.delete(lockKey);

            // Also remove from pending requests (deduplication map)
            this.pendingRequests.delete(lockKey);

            if (this.settings.debugMode) {
                console.log(`[Story 12.H.4] Task "${lockKey}" cancelled and cleaned up`);
            }
        } else {
            console.warn(`[Story 12.H.4] Task "${lockKey}" not found in registry`);
        }
    }

    /**
     * Register a task in the task registry
     *
     * Called when a new Agent request starts to track it for UI display.
     *
     * @param lockKey - Unique task identifier
     * @param nodeId - Node ID being processed
     * @param agentType - Agent type identifier
     * @param agentDisplayName - Human-readable agent name
     * @param abortController - Optional AbortController for cancellation
     *
     * @source Story 12.H.3 - Task tracking for UI
     */
    private registerTask(
        lockKey: string,
        nodeId: string,
        agentType: string,
        agentDisplayName: string,
        abortController?: AbortController
    ): void {
        const task: PendingRequest = {
            lockKey,
            nodeId,
            nodeName: this.getNodeName(nodeId) || nodeId.substring(0, 8),
            agentType,
            agentDisplayName,
            status: 'queued',
            startTime: Date.now(),
            estimatedTime: AGENT_ESTIMATED_TIMES[agentType] || 30,
            abortController,
        };

        this.taskRegistry.set(lockKey, task);

        if (this.settings.debugMode) {
            console.log(`[Story 12.H.3] Task "${lockKey}" registered`);
        }
    }

    /**
     * Update task status to running
     *
     * @param lockKey - Task identifier
     *
     * @source Story 12.H.3 - Task status tracking
     */
    private markTaskRunning(lockKey: string): void {
        const task = this.taskRegistry.get(lockKey);
        if (task) {
            task.status = 'running';
            task.startTime = Date.now(); // Reset start time when actually running
            this.taskRegistry.set(lockKey, task);
        }
    }

    /**
     * Unregister a completed task
     *
     * @param lockKey - Task identifier
     *
     * @source Story 12.H.3 - Task cleanup
     */
    private unregisterTask(lockKey: string): void {
        this.taskRegistry.delete(lockKey);

        if (this.settings.debugMode) {
            console.log(`[Story 12.H.3] Task "${lockKey}" unregistered`);
        }
    }

    /**
     * Get node name from Canvas
     *
     * Attempts to retrieve the node's display name from the active Canvas.
     *
     * @param nodeId - Node ID to look up
     * @returns Node name or undefined
     */
    private getNodeName(nodeId: string): string | undefined {
        // Try to get node name from active Canvas
        const activeFile = this.app.workspace.getActiveFile();
        if (!activeFile || activeFile.extension !== 'canvas') {
            return undefined;
        }

        // Return truncated nodeId as fallback
        // Full implementation would require reading Canvas file
        return undefined;
    }
}
