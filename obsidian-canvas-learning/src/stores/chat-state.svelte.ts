/**
 * Canvas Learning System - Chat State Store
 * Story 3.1: Claude Code CLI Integration (AC-1, AC-3, AC-4)
 *
 * Manages the active dialogue engine and per-node conversation state.
 * Provides reactive state for the ChatPanel UI (Story 3.3) to consume.
 *
 * Key responsibilities:
 * - Track the active node ID and its dialogue engine
 * - Handle node switching (preserve old session, resume new)
 * - Expose reactive state for UI binding
 *
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 4]
 */

import type {
  DialogEngine,
  EngineError,
  StreamEvent,
} from '../services/dialog-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// State Types
// ═══════════════════════════════════════════════════════════════════════════════

export type ChatStatus = 'idle' | 'connecting' | 'streaming' | 'error';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  /** Tool use events associated with this message. */
  toolEvents?: StreamEvent[];
}

interface ChatStateData {
  /** Currently active node ID (null if no node selected). */
  activeNodeId: string | null;

  /** Current chat status. */
  status: ChatStatus;

  /** Messages for the currently active node. */
  messages: ChatMessage[];

  /** Last error encountered. */
  lastError: EngineError | null;

  /** Whether the engine is available (CLI found, auth OK). */
  engineAvailable: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Chat State Manager
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Singleton chat state manager.
 *
 * Uses Svelte 5 $state runes for reactivity.
 */
class ChatStateManager {
  /** Reactive state using Svelte 5 $state. */
  activeNodeId: string | null = $state(null);
  status: ChatStatus = $state('idle');
  messages: ChatMessage[] = $state([]);
  lastError: EngineError | null = $state(null);
  engineAvailable: boolean = $state(true);

  /** The active DialogEngine instance. */
  private engine: DialogEngine | null = null;

  /** Per-node message history cache (kept in memory during session). */
  private messageCache: Map<string, ChatMessage[]> = new Map();

  // ═══════════════════════════════════════════════════════════════════════════
  // Engine Management
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Set the active DialogEngine instance.
   * Called during plugin initialization after creating ClaudeCodeEngine.
   *
   * @param engine - The DialogEngine to use for conversations.
   */
  setEngine(engine: DialogEngine): void {
    this.engine = engine;

    // Register error handler
    engine.onError((error: EngineError) => {
      this.lastError = error;
      this.status = 'error';

      if (error.type === 'auth_failed') {
        this.engineAvailable = false;
      }
    });
  }

  /**
   * Get the current engine instance.
   */
  getEngine(): DialogEngine | null {
    return this.engine;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Node Chat Operations (Task 4.2, 4.3)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Open a chat session for a specific node.
   *
   * Story 3.1 AC-3: If the node has an existing session, resumes it.
   * Story 3.1 AC-4: If switching from another node, preserves the old session.
   *
   * @param nodeId - The canvas node identifier.
   */
  async openNodeChat(nodeId: string): Promise<void> {
    if (!this.engine) {
      this.lastError = {
        type: 'spawn_failed',
        message: 'No dialogue engine configured',
      };
      this.status = 'error';
      return;
    }

    // If same node is already active, no-op
    if (this.activeNodeId === nodeId) {
      return;
    }

    // Save current node's messages to cache before switching
    if (this.activeNodeId) {
      this.messageCache.set(this.activeNodeId, [...this.messages]);
    }

    // Switch to new node
    this.activeNodeId = nodeId;
    this.status = 'idle';
    this.lastError = null;

    // Restore cached messages or start fresh
    const cached = this.messageCache.get(nodeId);
    if (cached) {
      this.messages = cached;
    } else {
      this.messages = [];
    }

    // Check if this node has an existing session
    const sessionId = await this.engine.getSessionId(nodeId);
    if (sessionId) {
      await this.engine.resume(sessionId);
    }
  }

  /**
   * Switch from the current node to a new node.
   *
   * Story 3.1 AC-4: Preserves the old session (does not destroy).
   *
   * @param newNodeId - The new node to switch to.
   */
  async switchNode(newNodeId: string): Promise<void> {
    await this.openNodeChat(newNodeId);
  }

  /**
   * Send a message in the currently active node's chat.
   *
   * @param message - The user's message text.
   */
  async sendMessage(message: string): Promise<void> {
    if (!this.engine || !this.activeNodeId) {
      return;
    }

    const nodeId = this.activeNodeId;

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: Date.now(),
    };
    this.messages = [...this.messages, userMsg];
    this.status = 'streaming';

    // Collect assistant response
    let assistantContent = '';
    const toolEvents: StreamEvent[] = [];

    try {
      for await (const event of this.engine.sendMessage(nodeId, message)) {
        // Check if user switched away during streaming
        if (this.activeNodeId !== nodeId) {
          break;
        }

        switch (event.type) {
          case 'text':
            if (event.text) {
              assistantContent += event.text;
            }
            break;
          case 'tool_use':
          case 'tool_result':
            toolEvents.push(event);
            break;
          case 'error':
            this.lastError = {
              type: 'crash',
              message: event.error ?? 'Unknown error',
            };
            break;
          case 'done':
            // Session completed
            break;
        }
      }

      // Add assistant message
      if (assistantContent || toolEvents.length > 0) {
        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: assistantContent,
          timestamp: Date.now(),
          toolEvents: toolEvents.length > 0 ? toolEvents : undefined,
        };
        this.messages = [...this.messages, assistantMsg];
      }

      this.status = this.lastError ? 'error' : 'idle';
    } catch (err) {
      this.lastError = {
        type: 'crash',
        message:
          err instanceof Error ? err.message : 'Unexpected error during chat',
        cause: err instanceof Error ? err : undefined,
      };
      this.status = 'error';
    }

    // Update cache
    this.messageCache.set(nodeId, [...this.messages]);
  }

  /**
   * Clear the chat history for the active node.
   */
  async clearChat(): Promise<void> {
    if (this.activeNodeId) {
      this.messages = [];
      this.messageCache.delete(this.activeNodeId);

      if (this.engine) {
        await this.engine.destroy(this.activeNodeId);
      }
    }
  }

  /**
   * Clean up all state and resources.
   * Called during plugin unload.
   */
  async cleanup(): Promise<void> {
    if (this.engine) {
      await this.engine.destroyAll();
    }
    this.activeNodeId = null;
    this.status = 'idle';
    this.messages = [];
    this.lastError = null;
    this.messageCache.clear();
  }
}

/** Singleton chat state instance. */
export const chatState = new ChatStateManager();
