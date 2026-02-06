/**
 * NodeColorChangeWatcher - Canvas Learning System
 *
 * Implements Story 30.6: Node Color Change Memory Trigger
 *
 * Watches Canvas files for node color changes and triggers memory events
 * to record learning progress transitions (red→yellow→green) to Neo4j.
 *
 * Features:
 * - Monitor `.canvas` file modifications via Obsidian Vault API
 * - Detect node color changes by comparing with previous state
 * - 500ms debounce mechanism to avoid event storms (AC-30.6.4)
 * - Batch multiple changes into single API call (AC-30.6.5)
 * - Fire-and-forget pattern with silent degradation (ADR-0004)
 *
 * @module NodeColorChangeWatcher
 * @version 1.0.0
 * @source Story 30.6: docs/stories/30.6.story.md
 */

import { App, TFile, requestUrl } from 'obsidian';

// ============================================================================
// Types and Interfaces
// ============================================================================

/**
 * Color mastery level enum
 * [Source: specs/data/canvas-node.schema.json#/properties/color]
 * [Source: tech-stack.md#颜色系统]
 */
export enum ColorMasteryLevel {
    /** Color "1" (red) - Concept not understood */
    NOT_UNDERSTOOD = 'not_understood',
    /** Color "6" (yellow) - Currently learning */
    LEARNING = 'learning',
    /** Color "2" (green) - Concept mastered */
    MASTERED = 'mastered',
    /** Color "3" (purple) - Pending verification */
    PENDING_VERIFICATION = 'pending_verification',
}

/**
 * Event type for color change events
 * [Source: Story 30.9 - AC-30.9.2, AC-30.9.4]
 */
export type ColorChangeEventType = 'color_changed' | 'color_removed' | 'node_removed';

/**
 * Color change event interface
 * [Source: specs/data/temporal-event.schema.json]
 */
export interface ColorChangeEvent {
    /** Event type: color_changed, color_removed, or node_removed */
    eventType: ColorChangeEventType;
    /** Node ID from canvas */
    nodeId: string;
    /** Canvas file path */
    canvasPath: string;
    /** Previous color code (null if new node) */
    oldColor: string | null;
    /** New color code (null if color removed or node deleted) */
    newColor: string | null;
    /** Previous mastery level */
    oldLevel: ColorMasteryLevel | null;
    /** New mastery level (null if color removed or node deleted) */
    newLevel: ColorMasteryLevel | null;
    /** Event timestamp */
    timestamp: Date;
    /** Node text content (for context) */
    nodeText?: string;
}

/**
 * Batch of color change events for API call
 * [Source: AC-30.6.5 - 批量合并单次API调用]
 */
export interface ColorChangeEventBatch {
    /** Array of color change events */
    events: Array<{
        event_type: ColorChangeEventType;
        timestamp: string;
        canvas_path: string;
        node_id: string;
        metadata: {
            old_color: string | null;
            new_color: string | null;
            old_level: ColorMasteryLevel | null;
            new_level: ColorMasteryLevel | null;
            concept: string;
            node_text?: string;
        };
    }>;
}

/**
 * Service settings
 * [Source: AC-30.6.4 - 500ms防抖机制]
 */
export interface NodeColorChangeWatcherSettings {
    /** Enable the watcher */
    enabled: boolean;
    /** Debounce delay in milliseconds (default: 500ms per AC-30.6.4) */
    debounceMs: number;
    /** API base URL for backend services */
    apiBaseUrl: string;
    /** Request timeout in milliseconds (default: 500ms per ADR-0004) */
    timeout: number;
    /** Enable console logging for debugging */
    enableLogging: boolean;
}

/**
 * Default settings
 * [Source: ADR-0004 - Fire-and-forget pattern with 500ms timeout]
 */
export const DEFAULT_NODE_COLOR_WATCHER_SETTINGS: NodeColorChangeWatcherSettings = {
    enabled: true,
    debounceMs: 500,
    apiBaseUrl: 'http://localhost:8000/api/v1',
    timeout: 500,
    enableLogging: false,
};

/**
 * Valid canvas color codes
 * [Source: specs/data/canvas-node.schema.json#/properties/color]
 */
const VALID_COLOR_CODES = ['1', '2', '3', '4', '5', '6'];

/**
 * Canvas node structure (minimal for color detection)
 */
interface CanvasNode {
    id: string;
    type?: string;
    text?: string;
    color?: string;
}

/**
 * Canvas data structure
 */
interface CanvasData {
    nodes?: CanvasNode[];
    edges?: unknown[];
}

// ============================================================================
// NodeColorChangeWatcher Class
// ============================================================================

/**
 * Service for watching Canvas node color changes and triggering memory events
 * Implements Story 30.6: Node Color Change Memory Trigger
 */
export class NodeColorChangeWatcher {
    private app: App;
    private settings: NodeColorChangeWatcherSettings;

    /** Previous canvas state: canvasPath -> (nodeId -> color) */
    private previousCanvasState: Map<string, Map<string, string>> = new Map();

    /** Pending color change events waiting to be flushed */
    private pendingChanges: ColorChangeEvent[] = [];

    /** Debounce timeout handle */
    private debounceTimeout: ReturnType<typeof setTimeout> | null = null;

    /** Obsidian event reference for cleanup */
    private eventRef: ReturnType<typeof App.prototype.vault.on> | null = null;

    /** Whether the watcher is currently running */
    private isRunning: boolean = false;

    /**
     * Create a new NodeColorChangeWatcher instance
     * @param app Obsidian App instance
     * @param settings Optional settings override
     */
    constructor(app: App, settings?: Partial<NodeColorChangeWatcherSettings>) {
        this.app = app;
        this.settings = { ...DEFAULT_NODE_COLOR_WATCHER_SETTINGS, ...settings };
    }

    // ========================================================================
    // Public API
    // ========================================================================

    /**
     * Start watching canvas files for color changes
     * [Source: Context7:/obsidianmd/obsidian-api - Vault.on('modify')]
     * [Source: Story 30.9 AC-30.9.1 - async start with state preloading]
     */
    async start(): Promise<void> {
        if (!this.settings.enabled) {
            this.log('Watcher disabled in settings, not starting');
            return;
        }

        if (this.isRunning) {
            this.log('Watcher already running');
            return;
        }

        // Set immediately to prevent double-start from sync callers (e.g. updateSettings)
        this.isRunning = true;

        // Pre-populate previousCanvasState before registering event listener
        // [Source: Story 30.9 Task 1 - Fixes DATA-001]
        await this.initializeState();

        this.eventRef = this.app.vault.on('modify', async (file) => {
            if (file instanceof TFile && file.extension === 'canvas') {
                await this.handleCanvasModify(file);
            }
        });

        this.log('Started watching canvas color changes');
    }

    /**
     * Stop watching canvas files
     * [Source: Context7:/obsidianmd/obsidian-api - Vault.offref]
     */
    stop(): void {
        // Remove event listener
        if (this.eventRef) {
            this.app.vault.offref(this.eventRef);
            this.eventRef = null;
        }

        // Clear debounce timeout and flush pending changes
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
            this.debounceTimeout = null;
            // Flush any pending changes before stopping
            this.flushChanges();
        }

        this.isRunning = false;
        this.log('Stopped watching canvas color changes');
    }

    /**
     * Check if watcher is currently running
     */
    isActive(): boolean {
        return this.isRunning;
    }

    /**
     * Update settings dynamically
     */
    updateSettings(settings: Partial<NodeColorChangeWatcherSettings>): void {
        const wasEnabled = this.settings.enabled;
        this.settings = { ...this.settings, ...settings };

        // Handle enable/disable toggle
        if (wasEnabled && !this.settings.enabled) {
            this.stop();
        } else if (!wasEnabled && this.settings.enabled && !this.isRunning) {
            this.start();
        }
    }

    /**
     * Get pending changes count (for debugging/testing)
     */
    getPendingChangesCount(): number {
        return this.pendingChanges.length;
    }

    /**
     * Clear previous state (useful for testing)
     */
    clearState(): void {
        this.previousCanvasState.clear();
        this.pendingChanges = [];
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
            this.debounceTimeout = null;
        }
    }

    // ========================================================================
    // Private Methods - Canvas File Processing
    // ========================================================================

    /**
     * Pre-populate previousCanvasState by scanning all .canvas files
     * Must be called before registering vault.on('modify')
     * [Source: Story 30.9 Task 1 - Fixes DATA-001]
     * [Source: AC-30.9.1 - 启动时预加载Canvas状态]
     */
    private async initializeState(): Promise<void> {
        const INIT_TIMEOUT_MS = 5000;
        try {
            await Promise.race([
                this.scanAllCanvasFiles(),
                new Promise<void>((_, reject) =>
                    setTimeout(() => reject(new Error('initializeState timeout')), INIT_TIMEOUT_MS)
                ),
            ]);
        } catch (error) {
            // Continue with partial state on timeout or error
            this.log('initializeState completed with partial state:', error);
        }
        this.log(`Initialized state for ${this.previousCanvasState.size} canvases`);
    }

    /**
     * Scan all .canvas files and populate previousCanvasState
     */
    private async scanAllCanvasFiles(): Promise<void> {
        const files = this.app.vault.getFiles().filter((f: TFile) => f.extension === 'canvas');

        for (const file of files) {
            try {
                const content = await this.app.vault.read(file);
                const canvasData: CanvasData = JSON.parse(content);
                const nodeColors = new Map<string, string>();

                for (const node of canvasData.nodes || []) {
                    if (node.color && this.isValidColor(node.color)) {
                        nodeColors.set(node.id, node.color);
                    }
                }

                if (nodeColors.size > 0) {
                    this.previousCanvasState.set(file.path, nodeColors);
                }
            } catch {
                // Skip files that can't be parsed
                this.log(`Skip initial scan for ${file.path}`);
            }
        }
    }

    /**
     * Handle canvas file modification event
     * [Source: AC-30.6.1 - 监听.canvas文件变化]
     */
    private async handleCanvasModify(file: TFile): Promise<void> {
        try {
            const content = await this.app.vault.read(file);
            const canvasData: CanvasData = JSON.parse(content);
            const changes = this.detectColorChanges(file.path, canvasData);

            if (changes.length > 0) {
                this.log(`Detected ${changes.length} color changes in ${file.path}`);
                this.accumulateChanges(changes);
            }
        } catch (error) {
            // Silent degradation - log but don't throw
            this.log('Error processing canvas file:', error);
        }
    }

    /**
     * Detect color changes by comparing with previous state
     * [Source: specs/data/canvas-node.schema.json#/properties/color]
     * [Source: AC-30.6.1 - 检测节点颜色属性变更]
     * [Source: Story 30.9 - AC-30.9.2 color removal, AC-30.9.4 node deletion]
     */
    private detectColorChanges(canvasPath: string, canvasData: CanvasData): ColorChangeEvent[] {
        const changes: ColorChangeEvent[] = [];
        const now = new Date();

        // Get previous state for this canvas
        const prevState = this.previousCanvasState.get(canvasPath) || new Map<string, string>();
        const newState = new Map<string, string>();

        // Track all node IDs and their text for removal/deletion detection
        const allNodeIds = new Set<string>();
        const nodeTextMap = new Map<string, string | undefined>();

        // Process each node in the canvas
        for (const node of canvasData.nodes || []) {
            const nodeId = node.id;
            allNodeIds.add(nodeId);
            nodeTextMap.set(nodeId, node.text || undefined);

            const newColor = node.color || null;

            if (newColor && this.isValidColor(newColor)) {
                newState.set(nodeId, newColor);
                const oldColor = prevState.get(nodeId) || null;

                // Detect color change (including new nodes with color)
                if (oldColor !== newColor) {
                    changes.push({
                        eventType: 'color_changed',
                        nodeId,
                        canvasPath,
                        oldColor,
                        newColor,
                        oldLevel: oldColor ? this.mapColorToLevel(oldColor) : null,
                        newLevel: this.mapColorToLevel(newColor),
                        timestamp: now,
                        nodeText: node.text || undefined,
                    });
                }
            }
        }

        // Detect color removal: node exists but color was removed
        // [Source: Story 30.9 Task 2 - Fixes DATA-002]
        for (const [nodeId, oldColor] of prevState) {
            if (allNodeIds.has(nodeId) && !newState.has(nodeId)) {
                changes.push({
                    eventType: 'color_removed',
                    nodeId,
                    canvasPath,
                    oldColor,
                    newColor: null,
                    oldLevel: this.mapColorToLevel(oldColor),
                    newLevel: null,
                    timestamp: now,
                    nodeText: nodeTextMap.get(nodeId),
                });
            }
        }

        // Detect node deletion: node no longer exists in canvas
        // [Source: Story 30.9 Task 4 - Fixes DATA-004]
        for (const [nodeId, oldColor] of prevState) {
            if (!allNodeIds.has(nodeId)) {
                changes.push({
                    eventType: 'node_removed',
                    nodeId,
                    canvasPath,
                    oldColor,
                    newColor: null,
                    oldLevel: this.mapColorToLevel(oldColor),
                    newLevel: null,
                    timestamp: now,
                });
            }
        }

        // Update stored state
        this.previousCanvasState.set(canvasPath, newState);

        return changes;
    }

    // ========================================================================
    // Private Methods - Color Mapping
    // ========================================================================

    /**
     * Map canvas color code to mastery level
     * [Source: tech-stack.md#颜色系统]
     * [Source: AC-30.6.2 - 颜色映射规则]
     */
    private mapColorToLevel(color: string): ColorMasteryLevel {
        switch (color) {
            case '1':
                // Red - 不理解/未通过
                return ColorMasteryLevel.NOT_UNDERSTOOD;
            case '2':
                // Green - 完全理解/已通过
                return ColorMasteryLevel.MASTERED;
            case '3':
                // Purple - 似懂非懂/待检验
                return ColorMasteryLevel.PENDING_VERIFICATION;
            case '6':
                // Yellow - 个人理解输出区
                return ColorMasteryLevel.LEARNING;
            default:
                // Colors 4 (cyan) and 5 (blue) not used in learning system
                // Default to LEARNING for unknown colors
                return ColorMasteryLevel.LEARNING;
        }
    }

    /**
     * Validate color code is in valid range
     * [Source: specs/data/canvas-node.schema.json#/properties/color]
     */
    private isValidColor(color: string): boolean {
        return VALID_COLOR_CODES.includes(color);
    }

    // ========================================================================
    // Private Methods - Debounce and Batching
    // ========================================================================

    /**
     * Accumulate changes with debounce
     * [Source: AC-30.6.4 - 500ms防抖机制避免事件风暴]
     */
    private accumulateChanges(changes: ColorChangeEvent[]): void {
        // Add new changes to pending list
        this.pendingChanges.push(...changes);

        // Reset debounce timer
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }

        // Set new debounce timer
        this.debounceTimeout = setTimeout(() => {
            this.flushChanges();
        }, this.settings.debounceMs);
    }

    /**
     * Flush accumulated changes to API
     * [Source: ADR-0004 - Fire-and-forget pattern with timeout]
     * [Source: AC-30.6.5 - 批量合并单次API调用]
     */
    private async flushChanges(): Promise<void> {
        if (this.pendingChanges.length === 0) {
            return;
        }

        // Move pending changes to local array and clear pending
        const changesToSend = [...this.pendingChanges];
        this.pendingChanges = [];
        this.debounceTimeout = null;

        // [Source: Story 30.9 Task 6 - Fixes BATCH-001: 50-per-batch chunking]
        const BATCH_SIZE = 50;
        for (let i = 0; i < changesToSend.length; i += BATCH_SIZE) {
            const chunk = changesToSend.slice(i, i + BATCH_SIZE);
            try {
                // Fire-and-forget with timeout per chunk
                // [Source: ADR-0004 - 超时保护: 500ms]
                await Promise.race([
                    this.postColorChangeEvents(chunk),
                    new Promise<void>((_, reject) =>
                        setTimeout(() => reject(new Error('Timeout')), this.settings.timeout)
                    ),
                ]);
                this.log(`Flushed chunk ${Math.floor(i / BATCH_SIZE) + 1} (${chunk.length} events) to memory API`);
            } catch (error) {
                // Silent degradation - log but don't throw
                // [Source: ADR-0004 - 失败时静默降级，记录错误日志]
                this.log('Failed to post color changes chunk (silent degradation):', error);
            }
        }
    }

    // ========================================================================
    // Private Methods - API Communication
    // ========================================================================

    /**
     * POST color change events to memory API
     * [Source: AC-30.6.3 - POST到/api/v1/memory/episodes]
     * [Source: specs/data/temporal-event.schema.json]
     */
    private async postColorChangeEvents(events: ColorChangeEvent[]): Promise<void> {
        const payload: ColorChangeEventBatch = {
            events: events.map((e) => ({
                event_type: e.eventType,
                timestamp: e.timestamp.toISOString(),
                canvas_path: e.canvasPath,
                node_id: e.nodeId,
                metadata: {
                    old_color: e.oldColor,
                    new_color: e.newColor,
                    old_level: e.oldLevel,
                    new_level: e.newLevel,
                    concept: e.nodeText || 'unknown',
                    node_text: e.nodeText,
                },
            })),
        };

        // [Source: Context7:/obsidianmd/obsidian-api - requestUrl]
        await requestUrl({
            url: `${this.settings.apiBaseUrl}/memory/episodes/batch`,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
    }

    // ========================================================================
    // Private Methods - Logging
    // ========================================================================

    /**
     * Log message if logging is enabled
     */
    private log(...args: unknown[]): void {
        if (this.settings.enableLogging) {
            console.log('[NodeColorWatcher]', ...args);
        }
    }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a new NodeColorChangeWatcher instance
 * @param app Obsidian App instance
 * @param settings Optional settings override
 * @returns NodeColorChangeWatcher instance
 */
export function createNodeColorChangeWatcher(
    app: App,
    settings?: Partial<NodeColorChangeWatcherSettings>
): NodeColorChangeWatcher {
    return new NodeColorChangeWatcher(app, settings);
}
