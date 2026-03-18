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
import type { ActiveEngineType } from '../services/engine-fallback';
import type { RecoveryStatus } from '../services/crash-recovery';

// ═══════════════════════════════════════════════════════════════════════════════
// State Types
// ═══════════════════════════════════════════════════════════════════════════════

export type ChatStatus = 'idle' | 'connecting' | 'streaming' | 'error';

/** Story 3.10: Quota status for subscription-based usage. */
export type QuotaStatus = 'available' | 'exhausted' | 'checking';

/**
 * Story 4.1: Chat panel mode — determines header UI and context injection.
 * - 'chat': Normal node dialog (header shows node name)
 * - 'exam': Exam mode (header shows exam status)
 * - 'edge': Edge Q&A (header shows "A ↔ B")
 */
export type ChatMode = 'chat' | 'exam' | 'edge';

/**
 * Story 4.1 AC-3: Edge context for ChatPanel edge mode.
 * Tracks which edge is being discussed and the names of connected nodes.
 */
export interface CurrentEdge {
  edgeId: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceNodeName: string;
  targetNodeName: string;
}

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

  /** Story 3.9: Current engine type indicator. */
  activeEngineType: ActiveEngineType = $state('claude-code');

  /** Story 3.10: Subscription quota status. */
  quotaStatus: QuotaStatus = $state('available');

  /** Story 3.10: Estimated time when quota resets (null if unknown). */
  quotaResetTime: Date | null = $state(null);

  /** Story 3.11: Current crash recovery status. */
  recoveryStatus: RecoveryStatus = $state('idle');

  /**
   * Story 4.1 AC-3: Current chat mode.
   * Determines ChatPanel header UI and context injection strategy.
   */
  chatMode: ChatMode = $state('chat');

  /**
   * Story 4.1 AC-3: Current edge being discussed (null when not in edge mode).
   */
  currentEdge: CurrentEdge | null = $state(null);

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
  // Story 3.9: Engine Switching
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Switch the active engine (called by EngineFallbackManager).
   *
   * Story 3.9 AC-3: Transparent engine switching — the UI layer
   * doesn't need to know about the switch, conversation history
   * is preserved in the message cache.
   *
   * @param engine - The new DialogEngine to use.
   * @param type - The engine type identifier.
   */
  switchEngine(engine: DialogEngine, type: ActiveEngineType): void {
    this.engine = engine;
    this.activeEngineType = type;
    this.engineAvailable = true;
    this.lastError = null;

    // Re-register error handler for the new engine
    engine.onError((error: EngineError) => {
      this.lastError = error;
      this.status = 'error';

      if (error.type === 'auth_failed') {
        this.engineAvailable = false;
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3.10: Quota Management
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Set the quota status to exhausted.
   *
   * Story 3.10 AC-1, AC-2: Called when a 429 rate_limited error is detected.
   *
   * @param retryAfterSec - Optional retry-after hint in seconds.
   */
  setQuotaExhausted(retryAfterSec?: number): void {
    this.quotaStatus = 'exhausted';

    if (retryAfterSec) {
      this.quotaResetTime = new Date(Date.now() + retryAfterSec * 1000);
    } else {
      // Default: estimate next Monday reset
      const now = new Date();
      const daysUntilMonday = (8 - now.getDay()) % 7 || 7;
      const nextMonday = new Date(now);
      nextMonday.setDate(now.getDate() + daysUntilMonday);
      nextMonday.setHours(0, 0, 0, 0);
      this.quotaResetTime = nextMonday;
    }
  }

  /**
   * Set the quota status back to available.
   *
   * Story 3.10 AC-5: Called when a re-spawn succeeds after quota exhaustion.
   */
  setQuotaAvailable(): void {
    this.quotaStatus = 'available';
    this.quotaResetTime = null;
  }

  /**
   * Set the quota status to checking (during re-spawn attempt).
   */
  setQuotaChecking(): void {
    this.quotaStatus = 'checking';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3.11: Recovery Status
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Update the crash recovery status for UI display.
   *
   * @param status - The new recovery status.
   */
  setRecoveryStatus(status: RecoveryStatus): void {
    this.recoveryStatus = status;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 4.1: Edge Chat Operations
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Open an Edge dialog session.
   *
   * Story 4.1 AC-3: Switches ChatPanel to edge mode, showing "A ↔ B" header.
   * Story 4.1 AC-4: Edge sessions use `edge_{edgeId}` as sessionId.
   *
   * @param edge - The edge context (edgeId, node names).
   */
  async openEdgeChat(edge: CurrentEdge): Promise<void> {
    if (!this.engine) {
      this.lastError = {
        type: 'spawn_failed',
        message: 'No dialogue engine configured',
      };
      this.status = 'error';
      return;
    }

    // Save current node's messages to cache before switching
    if (this.activeNodeId) {
      this.messageCache.set(this.activeNodeId, [...this.messages]);
    }

    // Set edge mode
    this.chatMode = 'edge';
    this.currentEdge = edge;

    // Use edge-scoped session ID
    const edgeSessionKey = `edge_${edge.edgeId}`;
    this.activeNodeId = edgeSessionKey;
    this.status = 'idle';
    this.lastError = null;

    // Restore cached messages or start fresh
    const cached = this.messageCache.get(edgeSessionKey);
    if (cached) {
      this.messages = cached;
    } else {
      this.messages = [];
    }

    // Check if this edge has an existing session
    const sessionId = await this.engine.getSessionId(edgeSessionKey);
    if (sessionId) {
      await this.engine.resume(sessionId);
    }
  }

  /**
   * Exit edge mode and return to normal chat mode.
   * Called when user clicks away from edge dialog or closes the panel.
   */
  exitEdgeChat(): void {
    if (this.chatMode !== 'edge') return;

    // Save edge messages to cache
    if (this.activeNodeId) {
      this.messageCache.set(this.activeNodeId, [...this.messages]);
    }

    this.chatMode = 'chat';
    this.currentEdge = null;
    this.activeNodeId = null;
    this.messages = [];
    this.status = 'idle';
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
    if (this.activeNodeId === nodeId && this.chatMode === 'chat') {
      return;
    }

    // Save current node's messages to cache before switching
    if (this.activeNodeId) {
      this.messageCache.set(this.activeNodeId, [...this.messages]);
    }

    // Story 4.1: Reset edge mode when switching to node chat
    this.chatMode = 'chat';
    this.currentEdge = null;

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
   * Story 4.1 AC-4: When in Edge mode, sets Edge context on the engine
   * before sending the message so --append-system-prompt includes
   * Edge dialog instructions.
   *
   * @param message - The user's message text.
   */
  async sendMessage(message: string): Promise<void> {
    if (!this.engine || !this.activeNodeId) {
      return;
    }

    // Story 4.1: Set Edge context on the engine if in Edge mode
    if (
      this.chatMode === 'edge' &&
      this.currentEdge &&
      'setEdgeContext' in this.engine
    ) {
      (
        this.engine as unknown as {
          setEdgeContext: (params: CurrentEdge | null) => void;
        }
      ).setEdgeContext(this.currentEdge);
    } else if ('setEdgeContext' in this.engine) {
      (
        this.engine as unknown as {
          setEdgeContext: (params: null) => void;
        }
      ).setEdgeContext(null);
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

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3.3: Streaming Chunk + History Management
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Append a streaming text chunk to the current assistant message.
   *
   * Story 3.3 AC-2: Real-time incremental rendering.
   * If no assistant message exists yet, creates one.
   *
   * @param text - Text chunk to append.
   */
  appendStreamChunk(text: string): void {
    const lastMsg = this.messages[this.messages.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') {
      const updated = { ...lastMsg, content: lastMsg.content + text };
      this.messages = [...this.messages.slice(0, -1), updated];
    } else {
      const newMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: text,
        timestamp: Date.now(),
      };
      this.messages = [...this.messages, newMsg];
    }
  }

  /**
   * Load persisted history messages into state.
   *
   * Story 3.3 AC-4: Called on ChatPanel mount to restore history.
   * Only loads if current messages array is empty (no in-memory cache).
   *
   * @param history - Messages from MessageStore, ordered oldest-first.
   */
  loadHistory(history: ChatMessage[]): void {
    if (this.messages.length === 0) {
      this.messages = history;
    }
  }

  /**
   * Prepend older history messages (for lazy-load pagination).
   *
   * Story 3.3 AC-4: IntersectionObserver triggers loading more.
   *
   * @param olderMessages - Older messages to prepend, ordered oldest-first.
   */
  prependHistory(olderMessages: ChatMessage[]): void {
    this.messages = [...olderMessages, ...this.messages];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3.5: Skill Command Execution
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Execute a skill command.
   *
   * Story 3.5 AC-2: Skill commands are sent as regular messages with
   * `/command-name args` format. Claude Code's native /command system
   * handles loading the corresponding .claude/commands/skill.md prompt.
   *
   * @param skillName - The skill command name (without /).
   * @param args - Optional arguments for the skill.
   */
  async executeSkill(skillName: string, args = ''): Promise<void> {
    const message = args ? `/${skillName} ${args}` : `/${skillName}`;
    await this.sendMessage(message);
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
    // Story 3.9 / 3.10 / 3.11 cleanup
    this.activeEngineType = 'claude-code';
    this.quotaStatus = 'available';
    this.quotaResetTime = null;
    this.recoveryStatus = 'idle';
    // Story 4.1 cleanup
    this.chatMode = 'chat';
    this.currentEdge = null;
  }
}

/** Singleton chat state instance. */
export const chatState = new ChatStateManager();
