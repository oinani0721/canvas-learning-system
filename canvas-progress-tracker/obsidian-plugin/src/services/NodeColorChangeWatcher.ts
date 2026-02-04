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
 * Color change event interface
 * [Source: specs/data/temporal-event.schema.json]
 */
export interface ColorChangeEvent {
    /** Node ID from canvas */
    nodeId: string;
    /** Canvas file path */
    canvasPath: string;
    /** Previous color code (null if new node) */
    oldColor: string | null;
    /** New color code */
    newColor: string;
    /** Previous mastery level */
    oldLevel: ColorMasteryLevel | null;
    /** New mastery level */
    newLevel: ColorMasteryLevel;
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
        event_type: 'color_changed';
        timestamp: string;
        canvas_path: string;
        node_id: string;
        metadata: {
            old_color: string | null;
            new_color: string;
            old_level: ColorMasteryLevel | null;
            new_level: ColorMasteryLevel;
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
     */
    start(): void {
        if (!this.settings.enabled) {
            this.log('Watcher disabled in settings, not starting');
            return;
        }

        if (this.isRunning) {
            this.log('Watcher already running');
            return;
        }

        this.eventRef = this.app.vault.on('modify', async (file) => {
            if (file instanceof TFile && file.extension === 'canvas') {
                await this.handleCanvasModify(file);
            }
        });

        this.isRunning = true;
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
     */
    private detectColorChanges(canvasPath: string, canvasData: CanvasData): ColorChangeEvent[] {
        const changes: ColorChangeEvent[] = [];
        const now = new Date();

        // Get previous state for this canvas
        const prevState = this.previousCanvasState.get(canvasPath) || new Map<string, string>();
        const newState = new Map<string, string>();

        // Process each node in the canvas
        for (const node of canvasData.nodes || []) {
            const nodeId = node.id;
            const newColor = node.color || null;

            if (newColor && this.isValidColor(newColor)) {
                newState.set(nodeId, newColor);
                const oldColor = prevState.get(nodeId) || null;

                // Detect color change (including new nodes with color)
                if (oldColor !== newColor) {
                    changes.push({
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

        try {
            // Fire-and-forget with timeout
            // [Source: ADR-0004 - 超时保护: 500ms]
            await Promise.race([
                this.postColorChangeEvents(changesToSend),
                new Promise<void>((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout')), this.settings.timeout)
                ),
            ]);
            this.log(`Flushed ${changesToSend.length} color changes to memory API`);
        } catch (error) {
            // Silent degradation - log but don't throw
            // [Source: ADR-0004 - 失败时静默降级，记录错误日志]
            this.log('Failed to post color changes (silent degradation):', error);
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
                event_type: 'color_changed' as const,
                timestamp: e.timestamp.toISOString(),
                canvas_path: e.canvasPath,
                node_id: e.nodeId,
                metadata: {
                    old_color: e.oldColor,
                    new_color: e.newColor,
                    old_level: e.oldLevel,
                    new_level: e.newLevel,
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
