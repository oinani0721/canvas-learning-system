/**
 * Zustand Chat Store — Per-node conversation state with Dexie persistence
 * Story 3-3: Chat Panel UI + Streaming
 *
 * Responsibilities:
 * - Per-node message list management (load, append, clear)
 * - Streaming state (isStreaming, current assistant message accumulation)
 * - Dexie persistence for cross-session history (AC-4)
 * - Lazy loading: initial 50 messages, load-more on scroll (AC-4)
 * - 2s first-token timeout tracking (AC-6)
 *
 * Callers:
 * - ChatPanel (main consumer — reads messages, dispatches sends)
 * - MessageBubble (reads individual message)
 * - InputBar (reads isStreaming to disable input)
 * - StreamingIndicator (reads streaming state)
 *
 * Wiring needs:
 * - ClaudeEngine.sendMessage() is called from sendMessage() action
 * - Dexie db.chat_messages is read/written for persistence
 */

import { create } from 'zustand';
import { db, type ChatMessage, type ChatMessageRole } from '../services/dexie-db';
import { ClaudeEngine, type StreamEvent } from '../services/claude-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Number of messages to load initially and per lazy-load batch. */
const PAGE_SIZE = 50;

/** Timeout (ms) before showing "thinking..." indicator if no first token. */
const FIRST_TOKEN_TIMEOUT_MS = 2000;

// ═══════════════════════════════════════════════════════════════════════════════
// Singleton engine
// ═══════════════════════════════════════════════════════════════════════════════

let engineInstance: ClaudeEngine | null = null;

function getEngine(): ClaudeEngine {
  if (!engineInstance) {
    engineInstance = new ClaudeEngine();
  }
  return engineInstance;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Store types
// ═══════════════════════════════════════════════════════════════════════════════

interface ChatStoreState {
  /** Current node ID the chat panel is bound to. */
  currentNodeId: string | null;

  /** Messages loaded for the current node (oldest first). */
  messages: ChatMessage[];

  /** Whether a streaming response is in progress. */
  isStreaming: boolean;

  /** Whether the engine is unavailable (Tauri not present, CLI missing). */
  engineUnavailable: boolean;

  /** Whether we are still waiting for the first token (> 2s = show thinking). */
  waitingForFirstToken: boolean;

  /** Whether there are older messages to load (lazy loading). */
  hasMore: boolean;

  /** Total message count for current node (for lazy loading offset). */
  totalCount: number;
}

interface ChatStoreActions {
  /**
   * Switch the chat to a different node. Loads the most recent PAGE_SIZE messages.
   * Called by: ChatPanel when selectedNode changes.
   */
  switchNode: (nodeId: string) => Promise<void>;

  /**
   * Load older messages (lazy loading on scroll up).
   * Called by: ChatPanel's IntersectionObserver sentinel.
   */
  loadMore: () => Promise<void>;

  /**
   * Send a user message and begin streaming the assistant response.
   * Called by: InputBar on submit.
   * Wiring: Calls ClaudeEngine.sendMessage() internally.
   */
  sendMessage: (text: string, nodeTitle: string) => Promise<void>;

  /**
   * Clear all messages for the current node.
   * Called by: ChatPanel "Clear" button.
   */
  clearHistory: () => Promise<void>;

  /**
   * Append a stream chunk to the current assistant message (internal).
   * Called by: sendMessage's StreamEvent callback.
   */
  appendStreamChunk: (text: string) => void;

  /**
   * Finalize the current streaming message (mark complete).
   * Called by: sendMessage's 'done' event.
   */
  finalizeStream: () => void;

  /**
   * Handle a stream error by updating the assistant message to error state.
   * Called by: sendMessage's 'error' event.
   */
  handleStreamError: (errorText: string) => void;
}

type ChatStore = ChatStoreState & ChatStoreActions;

// ═══════════════════════════════════════════════════════════════════════════════
// Persistence helpers
// ═══════════════════════════════════════════════════════════════════════════════

async function saveMessage(msg: ChatMessage): Promise<void> {
  await db.chat_messages.put(msg);
}

async function loadMessages(
  nodeId: string,
  limit: number,
  offset: number,
): Promise<ChatMessage[]> {
  // Get all messages for this node, sorted by createdAt descending,
  // skip `offset`, take `limit`, then reverse to oldest-first for display.
  const all = await db.chat_messages
    .where('nodeId')
    .equals(nodeId)
    .sortBy('createdAt');

  // Apply offset from the end (most recent) and take limit
  const total = all.length;
  const start = Math.max(0, total - offset - limit);
  const end = Math.max(0, total - offset);
  return all.slice(start, end);
}

async function countMessages(nodeId: string): Promise<number> {
  return db.chat_messages.where('nodeId').equals(nodeId).count();
}

async function deleteNodeMessages(nodeId: string): Promise<void> {
  await db.chat_messages.where('nodeId').equals(nodeId).delete();
}

// ═══════════════════════════════════════════════════════════════════════════════
// Store
// ═══════════════════════════════════════════════════════════════════════════════

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial state
  currentNodeId: null,
  messages: [],
  isStreaming: false,
  engineUnavailable: false,
  waitingForFirstToken: false,
  hasMore: false,
  totalCount: 0,

  switchNode: async (nodeId: string) => {
    // Abort any in-progress stream for the previous node
    const prevNodeId = get().currentNodeId;
    if (prevNodeId && get().isStreaming) {
      const engine = getEngine();
      await engine.abort(prevNodeId);
    }

    const total = await countMessages(nodeId);
    const messages = await loadMessages(nodeId, PAGE_SIZE, 0);

    set({
      currentNodeId: nodeId,
      messages,
      isStreaming: false,
      waitingForFirstToken: false,
      hasMore: total > PAGE_SIZE,
      totalCount: total,
    });
  },

  loadMore: async () => {
    const { currentNodeId, messages, hasMore, totalCount } = get();
    if (!currentNodeId || !hasMore) return;

    const offset = messages.length;
    const older = await loadMessages(currentNodeId, PAGE_SIZE, offset);
    if (older.length === 0) {
      set({ hasMore: false });
      return;
    }

    // Prepend older messages
    set({
      messages: [...older, ...messages],
      hasMore: offset + older.length < totalCount,
    });
  },

  sendMessage: async (text: string, nodeTitle: string) => {
    const { currentNodeId, isStreaming } = get();
    if (!currentNodeId || isStreaming) return;

    const nodeId = currentNodeId;

    // Create and persist user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      nodeId,
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    };
    await saveMessage(userMsg);

    // Create assistant placeholder (not yet persisted — persisted on finalize)
    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      nodeId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      isStreaming: true,
      waitingForFirstToken: true,
      totalCount: state.totalCount + 1, // user msg counted; assistant counted on finalize
    }));

    // 2s first-token timeout (AC-6)
    const firstTokenTimer = setTimeout(() => {
      // If still waiting and still streaming the same node, keep waitingForFirstToken true
      // (StreamingIndicator reads this to show "Thinking..." vs bouncing dots)
    }, FIRST_TOKEN_TIMEOUT_MS);

    const engine = getEngine();
    const systemPrompt = `You are helping the user learn about "${nodeTitle}". This is a knowledge node in their Canvas Learning System. Provide clear, educational responses. If the node has specific content, reference it in your explanations.`;

    // Accumulator for streaming content (avoids repeated store reads)
    let accumulated = '';

    try {
      await engine.sendMessage(
        {
          message: text,
          nodeId,
          systemPrompt,
        },
        (event: StreamEvent) => {
          // Ignore events if user switched away
          if (get().currentNodeId !== nodeId) return;

          switch (event.type) {
            case 'text':
              clearTimeout(firstTokenTimer);
              accumulated += event.text;
              set((state) => ({
                waitingForFirstToken: false,
                messages: state.messages.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: accumulated }
                    : m,
                ),
              }));
              break;

            case 'tool_use':
              accumulated += `\n\n*Using tool: ${event.toolName}...*\n`;
              set((state) => ({
                messages: state.messages.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: accumulated }
                    : m,
                ),
              }));
              break;

            case 'tool_result':
              // Internal context - not displayed
              break;

            case 'error': {
              clearTimeout(firstTokenTimer);

              // Check for engine unavailability
              const errText = event.error;
              const isUnavailable =
                errText.includes('not found') ||
                errText.includes('not available') ||
                errText.includes('spawn') ||
                errText.includes('Failed to spawn') ||
                errText.includes('program not found');

              set((state) => ({
                engineUnavailable: isUnavailable || state.engineUnavailable,
                waitingForFirstToken: false,
                messages: state.messages.map((m) =>
                  m.id === assistantId
                    ? { ...m, role: 'error' as ChatMessageRole, content: errText }
                    : m,
                ),
              }));
              break;
            }

            case 'done': {
              clearTimeout(firstTokenTimer);

              // Persist the assistant message if it has content
              const finalContent = accumulated;
              if (finalContent) {
                const finalMsg: ChatMessage = {
                  id: assistantId,
                  nodeId,
                  role: 'assistant',
                  content: finalContent,
                  createdAt: assistantMsg.createdAt,
                  metadata: event.sessionId
                    ? JSON.stringify({ sessionId: event.sessionId, costUsd: event.costUsd })
                    : undefined,
                };
                saveMessage(finalMsg);
                set((state) => ({
                  isStreaming: false,
                  waitingForFirstToken: false,
                  totalCount: state.totalCount + 1, // count the assistant msg
                }));
              } else {
                // No content produced — remove the empty placeholder
                set((state) => ({
                  isStreaming: false,
                  waitingForFirstToken: false,
                  messages: state.messages.filter(
                    (m) => m.id !== assistantId || m.role === 'error',
                  ),
                }));
              }
              break;
            }
          }
        },
      );
    } catch (err) {
      clearTimeout(firstTokenTimer);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';

      const isUnavailable =
        errorMsg.includes('__TAURI__') ||
        errorMsg.includes('is not defined') ||
        errorMsg.includes('not found') ||
        errorMsg.includes('spawn');

      // Persist error as the assistant message
      const errorChatMsg: ChatMessage = {
        id: assistantId,
        nodeId,
        role: 'error',
        content: errorMsg,
        createdAt: assistantMsg.createdAt,
      };
      await saveMessage(errorChatMsg);

      set((state) => ({
        isStreaming: false,
        waitingForFirstToken: false,
        engineUnavailable: isUnavailable || state.engineUnavailable,
        messages: state.messages.map((m) =>
          m.id === assistantId
            ? { ...m, role: 'error' as ChatMessageRole, content: errorMsg }
            : m,
        ),
      }));
    }
  },

  clearHistory: async () => {
    const { currentNodeId } = get();
    if (!currentNodeId) return;
    await deleteNodeMessages(currentNodeId);
    set({ messages: [], totalCount: 0, hasMore: false });
  },

  // These are kept for potential external callers but the main flow uses
  // the inline callbacks in sendMessage above.
  appendStreamChunk: (text: string) => {
    const { messages } = get();
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') {
      set({
        waitingForFirstToken: false,
        messages: messages.map((m) =>
          m.id === lastMsg.id
            ? { ...m, content: m.content + text }
            : m,
        ),
      });
    }
  },

  finalizeStream: () => {
    set({ isStreaming: false, waitingForFirstToken: false });
  },

  handleStreamError: (errorText: string) => {
    const { messages } = get();
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') {
      set({
        isStreaming: false,
        waitingForFirstToken: false,
        messages: messages.map((m) =>
          m.id === lastMsg.id
            ? { ...m, role: 'error' as ChatMessageRole, content: errorText }
            : m,
        ),
      });
    }
  },
}));
