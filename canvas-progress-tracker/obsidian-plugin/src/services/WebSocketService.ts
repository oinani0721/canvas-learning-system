/**
 * WebSocket Service for Real-time Progress Updates
 *
 * Story 19.4 AC 3-5: WebSocket客户端 + 断线重连
 *
 * ✅ Verified from WebSocket API (MDN Standard)
 * [Source: docs/stories/19.4.story.md:241-297 - WebSocket客户端]
 */

import { Notice } from 'obsidian';

/**
 * WebSocket message structure from server.
 * [Source: docs/stories/19.4.story.md:78-102 - SDD规范参考]
 */
export interface WSMessage {
    type: 'progress_update' | 'connection_ack' | 'error';
    data: ProgressUpdateData | ConnectionAckData | ErrorData;
    timestamp: string;
}

export interface ProgressUpdateData {
    canvas_id: string;
    total_concepts: number;
    passed_count: number;
    coverage_rate: number;
    changed_node: ChangedNodeInfo | null;
}

export interface ChangedNodeInfo {
    node_id: string;
    source_node_id: string;
    old_color: string;
    new_color: string;
}

export interface ConnectionAckData {
    status: 'connected';
    canvas_id: string;
}

export interface ErrorData {
    code: string;
    message: string;
}

/**
 * Connection state enum
 */
export enum ConnectionState {
    DISCONNECTED = 'disconnected',
    CONNECTING = 'connecting',
    CONNECTED = 'connected',
    RECONNECTING = 'reconnecting'
}

/**
 * WebSocket service configuration
 */
export interface WebSocketServiceConfig {
    /** Base URL for WebSocket server (default: ws://localhost:8000) */
    baseUrl: string;
    /** Maximum reconnection attempts (default: 5) */
    maxReconnectAttempts: number;
    /** Maximum reconnect delay in ms (default: 30000) */
    maxReconnectDelay: number;
    /** Show notifications on connection events (default: true) */
    showNotifications: boolean;
}

const DEFAULT_CONFIG: WebSocketServiceConfig = {
    baseUrl: 'ws://localhost:8001',
    maxReconnectAttempts: 5,
    maxReconnectDelay: 30000,
    showNotifications: true
};

/**
 * WebSocket service for real-time progress updates.
 *
 * Manages WebSocket connection to the backend server, handles
 * automatic reconnection with exponential backoff, and dispatches
 * progress update events to subscribers.
 *
 * [Source: docs/stories/19.4.story.md:114-117 - 关键约束]
 *
 * Example:
 * ```typescript
 * const ws = new WebSocketService('离散数学.canvas', (data) => {
 *     console.log('Progress:', data.coverage_rate);
 * });
 * ws.connect();
 * // ... later
 * ws.disconnect();
 * ```
 *
 * ✅ Verified from WebSocket API (MDN Standard)
 */
export class WebSocketService {
    private ws: WebSocket | null = null;
    private canvasId: string;
    private config: WebSocketServiceConfig;
    private reconnectAttempts = 0;
    private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    private state: ConnectionState = ConnectionState.DISCONNECTED;

    // Event callbacks
    private onProgressUpdate: (data: ProgressUpdateData) => void;
    private onConnectionChange?: (state: ConnectionState) => void;
    private onError?: (error: ErrorData) => void;

    /**
     * Create a new WebSocket service instance.
     *
     * @param canvasId - Canvas identifier to subscribe to
     * @param onProgressUpdate - Callback for progress update events
     * @param config - Optional configuration overrides
     */
    constructor(
        canvasId: string,
        onProgressUpdate: (data: ProgressUpdateData) => void,
        config?: Partial<WebSocketServiceConfig>
    ) {
        this.canvasId = canvasId;
        this.onProgressUpdate = onProgressUpdate;
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * Set callback for connection state changes.
     */
    setOnConnectionChange(callback: (state: ConnectionState) => void): void {
        this.onConnectionChange = callback;
    }

    /**
     * Set callback for error events.
     */
    setOnError(callback: (error: ErrorData) => void): void {
        this.onError = callback;
    }

    /**
     * Get current connection state.
     */
    getState(): ConnectionState {
        return this.state;
    }

    /**
     * Get the canvas ID this service is subscribed to.
     */
    getCanvasId(): string {
        return this.canvasId;
    }

    /**
     * Connect to the WebSocket server.
     *
     * Establishes connection to `/ws/progress/{canvas_id}` endpoint.
     * Automatically handles reconnection on disconnect.
     *
     * ✅ Verified from WebSocket API (MDN): new WebSocket(url)
     */
    connect(): void {
        if (this.state === ConnectionState.CONNECTED ||
            this.state === ConnectionState.CONNECTING) {
            return;
        }

        this.updateState(ConnectionState.CONNECTING);

        const wsUrl = `${this.config.baseUrl}/ws/progress/${encodeURIComponent(this.canvasId)}`;

        try {
            // ✅ Verified from MDN: WebSocket constructor
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
            this.ws.onerror = this.handleError.bind(this);
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleReconnect();
        }
    }

    /**
     * Disconnect from the WebSocket server.
     *
     * Cleanly closes the connection and stops reconnection attempts.
     *
     * ✅ Verified from MDN: WebSocket.close()
     */
    disconnect(): void {
        // Clear reconnect timer
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        // Close connection
        if (this.ws) {
            // Prevent reconnect on intentional close
            this.reconnectAttempts = this.config.maxReconnectAttempts;
            this.ws.close();
            this.ws = null;
        }

        this.updateState(ConnectionState.DISCONNECTED);
    }

    /**
     * Send a ping message to keep connection alive.
     */
    ping(): void {
        if (this.ws && this.state === ConnectionState.CONNECTED) {
            this.ws.send('ping');
        }
    }

    /**
     * Handle WebSocket open event.
     */
    private handleOpen(): void {
        console.log(`WebSocket connected for canvas: ${this.canvasId}`);
        this.reconnectAttempts = 0;
        this.updateState(ConnectionState.CONNECTED);

        if (this.config.showNotifications) {
            new Notice(`Progress tracker connected: ${this.canvasId}`);
        }
    }

    /**
     * Handle incoming WebSocket message.
     *
     * Parses JSON message and dispatches to appropriate handler.
     *
     * ✅ Verified from MDN: WebSocket.onmessage, JSON.parse
     */
    private handleMessage(event: MessageEvent): void {
        try {
            const message: WSMessage = JSON.parse(event.data);

            switch (message.type) {
                case 'progress_update':
                    this.onProgressUpdate(message.data as ProgressUpdateData);
                    break;

                case 'connection_ack':
                    console.log('Connection acknowledged:', message.data);
                    break;

                case 'error':
                    const errorData = message.data as ErrorData;
                    console.error('WebSocket error:', errorData);
                    if (this.onError) {
                        this.onError(errorData);
                    }
                    if (this.config.showNotifications) {
                        new Notice(`Progress tracker error: ${errorData.message}`);
                    }
                    break;

                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket close event.
     *
     * Triggers reconnection if not intentionally closed.
     */
    private handleClose(event: CloseEvent): void {
        console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
        this.ws = null;

        if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.handleReconnect();
        } else {
            this.updateState(ConnectionState.DISCONNECTED);
            if (this.config.showNotifications) {
                new Notice('Progress tracker disconnected. Click to reconnect.');
            }
        }
    }

    /**
     * Handle WebSocket error event.
     */
    private handleError(event: Event): void {
        console.error('WebSocket error:', event);
        // onclose will be called after onerror, which handles reconnect
    }

    /**
     * Handle reconnection with exponential backoff.
     *
     * [Source: docs/stories/19.4.story.md:116 - 重连间隔: 指数退避]
     * Delay pattern: 1s, 2s, 4s, 8s, max 30s
     *
     * ✅ Verified from docs/stories/19.4.story.md:283-288
     */
    private handleReconnect(): void {
        if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            this.updateState(ConnectionState.DISCONNECTED);
            return;
        }

        this.updateState(ConnectionState.RECONNECTING);

        // Exponential backoff: 1s, 2s, 4s, 8s... max 30s
        const delay = Math.min(
            1000 * Math.pow(2, this.reconnectAttempts),
            this.config.maxReconnectDelay
        );

        console.log(
            `Reconnecting in ${delay}ms ` +
            `(attempt ${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`
        );

        this.reconnectAttempts++;

        this.reconnectTimeout = setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Update connection state and notify listeners.
     */
    private updateState(newState: ConnectionState): void {
        if (this.state !== newState) {
            this.state = newState;
            if (this.onConnectionChange) {
                this.onConnectionChange(newState);
            }
        }
    }
}

/**
 * Factory function to create WebSocket service with common configuration.
 *
 * @param canvasId - Canvas identifier
 * @param onProgressUpdate - Progress update callback
 * @param serverUrl - Optional server URL override
 */
export function createWebSocketService(
    canvasId: string,
    onProgressUpdate: (data: ProgressUpdateData) => void,
    serverUrl?: string
): WebSocketService {
    return new WebSocketService(canvasId, onProgressUpdate, {
        baseUrl: serverUrl || 'ws://localhost:8000'
    });
}
