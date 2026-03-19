/**
 * Zustand Chat Store — Per-node conversation state with Dexie persistence
 * Story 3-3: Chat Panel UI + Streaming
 * Story 3-9: Engine Fallback (CLI -> API Key degradation)
 * Story 3-10: Quota Management + Degradation (429 detection + countdown)
 * Story 3-11: Crash Recovery (lastSentMessage + circuit breaker)
 *
 * Responsibilities:
 * - Per-node message list management (load, append, clear)
 * - Streaming state (isStreaming, current assistant message accumulation)
 * - Dexie persistence for cross-session history (AC-4)
 * - Lazy loading: initial 50 messages, load-more on scroll (AC-4)
 * - 2s first-token timeout tracking (AC-6)
 * - Engine switching: ClaudeEngine <-> ApiKeyEngine (Story 3-9)
 * - Quota status tracking and degradation UI (Story 3-10)
 * - Crash recovery: lastSentMessage caching + circuit breaker (Story 3-11)
 *
 * Callers:
 * - ChatPanel (main consumer — reads messages, dispatches sends)
 * - MessageBubble (reads individual message)
 * - InputBar (reads isStreaming to disable input)
 * - StreamingIndicator (reads streaming state)
 * - QuotaExhaustedBanner (reads quotaStatus)
 * - RecoveryBanner (reads recoveryStatus)
 *
 * Wiring needs:
 * - EngineFallbackManager.sendMessage() is called from sendMessage() action
 * - Dexie db.chat_messages is read/written for persistence
 * - CrashRecoveryManager handles crash caching/replay
 */

import { create } from 'zustand';
import { db, type ChatMessage, type ChatMessageRole } from '../services/dexie-db';
import { type StreamEvent } from '../services/claude-engine';
import { EngineFallbackManager, type ActiveEngine } from '../services/engine-fallback';
import { CrashRecoveryManager, type RecoveryStatus } from '../services/crash-recovery';
import { ApiClient } from '../services/api-client';

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Number of messages to load initially and per lazy-load batch. */
const PAGE_SIZE = 50;

/** Timeout (ms) before showing "thinking..." indicator if no first token. */
const FIRST_TOKEN_TIMEOUT_MS = 2000;

// ═══════════════════════════════════════════════════════════════════════════════
// Singletons
// ═══════════════════════════════════════════════════════════════════════════════

let fallbackManager: EngineFallbackManager | null = null;
let crashRecovery: CrashRecoveryManager | null = null;
let chatApiClient: ApiClient | null = null;

function getChatApiClient(): ApiClient {
  if (!chatApiClient) {
    chatApiClient = new ApiClient();
  }
  return chatApiClient;
}

function getFallbackManager(): EngineFallbackManager {
  if (!fallbackManager) {
    fallbackManager = new EngineFallbackManager();
  }
  return fallbackManager;
}

function getCrashRecovery(): CrashRecoveryManager {
  if (!crashRecovery) {
    crashRecovery = new CrashRecoveryManager();
  }
  return crashRecovery;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Quota status type (Story 3-10)
// ═══════════════════════════════════════════════════════════════════════════════

export type QuotaStatus = 'available' | 'exhausted' | 'checking';

// ═══════════════════════════════════════════════════════════════════════════════
// Story 4-1/4-2: Edge dialog types
// ═══════════════════════════════════════════════════════════════════════════════

/** Chat panel mode: normal node dialog or edge relationship dialog. */
export type ChatMode = 'normal' | 'edge';

/** Context for the current edge dialog (when chatMode === 'edge'). */
export interface EdgeContext {
  edgeId: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceNodeName: string;
  targetNodeName: string;
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

  // ── Story 3-9: Engine Fallback ──────────────────────────────────────
  /** Which engine is currently active. */
  activeEngine: ActiveEngine;

  // ── Story 3-10: Quota Management ────────────────────────────────────
  /** Current subscription quota status. */
  quotaStatus: QuotaStatus;
  /** ISO-8601 timestamp when quota is expected to reset. */
  quotaResetTime: string | null;
  /** Seconds until retry (from retry-after header). */
  quotaRetryAfterSec: number | null;

  // ── Story 3-11: Crash Recovery ──────────────────────────────────────
  /** Current crash recovery status. */
  recoveryStatus: RecoveryStatus;

  // ── Story 4-1/4-2: Edge Dialog ──────────────────────────────────────
  /** Current chat panel mode. */
  chatMode: ChatMode;
  /** Edge context when chatMode === 'edge'. */
  currentEdge: EdgeContext | null;
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
   * Wiring: Calls EngineFallbackManager.sendMessage() internally.
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

  // ── Story 3-9: Engine control ───────────────────────────────────────
  /**
   * Manually switch to a specific engine.
   * Called by: ChatPanel header engine status click.
   */
  switchEngine: (engine: ActiveEngine) => Promise<void>;

  // ── Story 3-10: Quota management ────────────────────────────────────
  /**
   * Dismiss quota exhaustion banner (user chose "wait for reset").
   * Quota status reverts to checking on next send attempt.
   */
  dismissQuotaExhausted: () => void;

  // ── Story 3-11: Crash recovery ──────────────────────────────────────
  /**
   * Manual retry after crash failure.
   * Called by: RecoveryBanner "Retry" button.
   */
  manualRetry: (nodeTitle: string) => Promise<void>;

  // ── Story 4-1/4-2: Edge dialog ────────────────────────────────────
  /**
   * Switch the chat panel to edge dialog mode.
   * Loads chat history for the edge session (keyed as edge_{edgeId}).
   * Called by: App.tsx when user clicks an edge.
   */
  switchToEdge: (edge: EdgeContext) => Promise<void>;

  /**
   * Exit edge mode and return to normal node chat (or no selection).
   * Called by: App.tsx when user clicks away from edge / selects a node.
   */
  exitEdgeMode: () => void;
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
  beforeCursor?: string,
): Promise<ChatMessage[]> {
  // Cursor-based pagination: load `limit` messages older than `beforeCursor`.
  // This avoids skip/duplicate issues that offset-based pagination causes when
  // new messages are appended between page loads.
  //
  // When beforeCursor is undefined, loads the most recent `limit` messages.
  const all = await db.chat_messages
    .where('nodeId')
    .equals(nodeId)
    .sortBy('createdAt');

  if (!beforeCursor) {
    // Initial load: take the most recent `limit` messages
    const start = Math.max(0, all.length - limit);
    return all.slice(start);
  }

  // Cursor-based: find all messages older than the cursor
  const olderMessages = all.filter((m) => m.createdAt < beforeCursor);
  // Take the most recent `limit` from the older set
  const start = Math.max(0, olderMessages.length - limit);
  return olderMessages.slice(start);
}

async function countMessages(nodeId: string): Promise<number> {
  return db.chat_messages.where('nodeId').equals(nodeId).count();
}

async function deleteNodeMessages(nodeId: string): Promise<void> {
  await db.chat_messages.where('nodeId').equals(nodeId).delete();
}

// ═══════════════════════════════════════════════════════════════════════════════
// Story 4-1/4-2: Edge dialog system prompt builder
// [Source: backend/prompts/edge-dialog.md — translated to frontend constant]
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Build system prompt for node conversations.
 * Defines the learning assistant role and guides MCP tool usage.
 */
function buildNodeSystemPrompt(nodeTitle: string): string {
  return [
    `你是 Canvas Learning System 的学习助手，正在帮助用户学习「${nodeTitle}」。`,
    ``,
    `## 你的角色`,
    `- 像一个耐心的私教，根据用户的水平调整讲解深度`,
    `- 用清晰易懂的语言解释概念，避免不必要的术语堆砌`,
    `- 主动引导用户思考，而不是直接给答案`,
    ``,
    `## 工具使用指南`,
    `你可以使用后端提供的 MCP 工具来辅助教学。以下是使用时机：`,
    ``,
    `### 应该使用工具的场景（调用 search_notes / search_memories）`,
    `- 用户提到"我的笔记里有..."、"之前学过..."、"上次..."等需要检索的内容`,
    `- 需要引用用户自己写的笔记来解释概念`,
    `- 用户问的问题涉及多个知识点的关联，需要搜索上下文`,
    `- 用户对概念理解有误，需要找到相关学习记录来定位误解根源`,
    ``,
    `### 不需要工具的场景（直接回答）`,
    `- 用户问的是通用知识（"什么是XX"、"XX的定义"）`,
    `- 简单的概念解释、举例说明`,
    `- 用户只是在闲聊或打招呼`,
    `- 对上一轮回答的追问（上下文已经在对话历史中）`,
    ``,
    `### 可用的 MCP 工具`,
    `- **search_notes**：搜索用户的 Vault 笔记库（语义搜索，支持中英文）`,
    `- **search_memories**：搜索学习记忆（历史对话、错误记录、学习事件）`,
    `- **query_mastery**：查询节点的精通度（BKT概率 + FSRS复习状态）`,
    `- **record_error**：记录用户的理解错误（4种类型自动分类）`,
    ``,
    `## 教学策略`,
    `1. **先理解用户意图**：区分"想学新知识"、"想复习旧知识"、"有疑惑想澄清"`,
    `2. **渐进式引导**：不要一次性把所有内容倒出来，分步骤讲解`,
    `3. **结合用户笔记**：如果搜索到相关笔记，引用并建立连接`,
    `4. **发现错误时记录**：当用户表现出误解，用 record_error 记录以便后续复习`,
    ``,
    `## 语言`,
    `- 默认使用中文回复`,
    `- 如果用户的笔记是英文的，可以中英混合解释`,
    `- 学术术语首次出现时给出中文解释`,
  ].join('\n');
}

function buildEdgeSystemPrompt(edge: EdgeContext): string {
  return [
    `你是一个学习助手，正在帮助用户理解两个概念之间的关系。`,
    ``,
    `## 当前连线`,
    `- **概念 A**：${edge.sourceNodeName}`,
    `- **概念 B**：${edge.targetNodeName}`,
    ``,
    `## 你的任务`,
    `用户在白板上把「${edge.sourceNodeName}」和「${edge.targetNodeName}」连在了一起。你需要：`,
    `1. **友好地询问**用户为什么把这两个概念连在一起`,
    `2. **深入理解**用户对这段关系的认知`,
    `3. **帮助用户**把模糊的直觉整理成清晰的表述`,
    ``,
    `## 对话风格`,
    `- 像一个好奇的学伴，而不是老师或考官`,
    `- 用自然的对话语气，不要用教学术语`,
    `- 保持轻松，用户应该感觉是在"聊天"而不是"做作业"`,
    ``,
    `## 追问策略`,
    `- 开场：用自然语气引用两端概念名称，询问用户为什么把它们连在一起`,
    `- 深层追问：当用户只给出表面回答时，追问更深层的因果关系`,
    `- 最多 3-4 轮追问，避免用户疲劳`,
    `- 用户给出完整因果关系 + 条件限制 + 自己的表述后可以结束`,
    ``,
    `## 理由提取`,
    `当你判断用户已经充分解释后，在对话中自然地总结关系类型。`,
    `例如："好的，我理解了——${edge.sourceNodeName} 是 ${edge.targetNodeName} 的前提条件。"`,
    ``,
    `## 重要`,
    `- 不要使用 Active Recall 策略——连线时两端概念都在白板上可见`,
    `- 不要使用教学术语（EI、SE、Active Recall等）`,
    `- 不要像做练习或考试那样追问`,
  ].join('\n');
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

  // Story 3-9: Engine Fallback
  activeEngine: getFallbackManager().activeEngine,

  // Story 3-10: Quota Management
  quotaStatus: 'available',
  quotaResetTime: null,
  quotaRetryAfterSec: null,

  // Story 3-11: Crash Recovery
  recoveryStatus: 'idle',

  // Story 4-1/4-2: Edge Dialog
  chatMode: 'normal',
  currentEdge: null,

  switchNode: async (nodeId: string) => {
    // Abort any in-progress stream for the previous node
    const prevNodeId = get().currentNodeId;
    if (prevNodeId && get().isStreaming) {
      const mgr = getFallbackManager();
      await mgr.abort(prevNodeId);
    }

    const total = await countMessages(nodeId);
    const messages = await loadMessages(nodeId, PAGE_SIZE);

    set({
      currentNodeId: nodeId,
      messages,
      isStreaming: false,
      waitingForFirstToken: false,
      hasMore: total > PAGE_SIZE,
      totalCount: total,
      // Reset edge mode when switching to a node
      chatMode: 'normal',
      currentEdge: null,
    });
  },

  loadMore: async () => {
    const { currentNodeId, messages, hasMore } = get();
    if (!currentNodeId || !hasMore) return;

    // Cursor-based: use the oldest currently loaded message's createdAt
    const oldestLoaded = messages.length > 0 ? messages[0] : null;
    const cursor = oldestLoaded?.createdAt;

    const older = await loadMessages(currentNodeId, PAGE_SIZE, cursor);
    if (older.length === 0) {
      set({ hasMore: false });
      return;
    }

    // Prepend older messages (cursor ensures no duplicates)
    set({
      messages: [...older, ...messages],
      hasMore: older.length >= PAGE_SIZE,
    });
  },

  sendMessage: async (text: string, nodeTitle: string) => {
    const { currentNodeId, isStreaming, quotaStatus } = get();
    if (!currentNodeId || isStreaming) return;

    const nodeId = currentNodeId;
    const mgr = getFallbackManager();
    const recovery = getCrashRecovery();

    // Story 3-10: If quota was exhausted, re-check by attempting to send
    // (the engine will detect if quota has been restored)
    if (quotaStatus === 'exhausted') {
      set({ quotaStatus: 'checking' });
    }

    // Story 3-11: Cache message before sending (AC-2)
    const sessionId = mgr.getSessionId(nodeId);
    await recovery.cacheMessage(nodeId, text, sessionId);

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

    // 2s first-token timeout (AC-6): if no token arrives within 2s,
    // explicitly confirm waitingForFirstToken stays true (the UI already
    // shows "Thinking..." based on this flag being true from the initial set).
    // Previously this was a no-op callback. Now it explicitly re-asserts the
    // state in case a race condition cleared it prematurely.
    const firstTokenTimer = setTimeout(() => {
      if (get().isStreaming && get().currentNodeId === nodeId && get().waitingForFirstToken) {
        // Re-assert: still waiting after 2s — no-op since flag is already true,
        // but this documents the intent and guards against future refactors.
        set({ waitingForFirstToken: true });
      }
    }, FIRST_TOKEN_TIMEOUT_MS);

    // Story 3-4: Fetch learning context before sending message (best-effort, non-blocking on failure)
    let learningContext = '';
    const { chatMode: currentMode, currentEdge } = get();
    if (currentMode !== 'edge') {
      try {
        // Use raw fetch because ?format=markdown returns text/plain, not JSON.
        // Read backend URL from settings (same pattern as useBackendStatus).
        const settingsRaw = localStorage.getItem('canvas-learning-settings');
        const backendUrl = settingsRaw
          ? (JSON.parse(settingsRaw) as { backendUrl?: string }).backendUrl || 'http://localhost:8001'
          : 'http://localhost:8001';
        const ctxUrl = `${backendUrl}/api/v1/context/${encodeURIComponent(nodeId)}?format=markdown`;
        const ctxResp = await fetch(ctxUrl, { method: 'GET' });
        if (ctxResp.ok) {
          const ctxText = await ctxResp.text();
          if (ctxText) {
            learningContext = ctxText;
          }
        }
      } catch {
        // Non-blocking: context unavailable doesn't prevent chat
      }
    }

    // Story 4-1/4-2: Edge mode uses edge-specific system prompt
    const baseSystemPrompt = currentMode === 'edge' && currentEdge
      ? buildEdgeSystemPrompt(currentEdge)
      : buildNodeSystemPrompt(nodeTitle);

    // Inject learning context into system prompt if available
    const systemPrompt = learningContext
      ? `${baseSystemPrompt}\n\n## Learning Context\n${learningContext}`
      : baseSystemPrompt;

    // Accumulator for streaming content (avoids repeated store reads)
    let accumulated = '';

    try {
      await mgr.sendMessage(
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

              // Story 3-11: Clear cached message on success
              recovery.clearMessage();

              // Story 3-10: Quota restored if we got a successful response
              if (get().quotaStatus !== 'available') {
                set({ quotaStatus: 'available', quotaResetTime: null, quotaRetryAfterSec: null });
              }

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
                saveMessage(finalMsg).catch((err) =>
                  console.error('[chat-store] Failed to persist assistant message:', err)
                );

                // Story 4-1/4-2: Record edge rationale when edge dialog completes
                const { chatMode: doneMode, currentEdge: doneEdge } = get();
                if (doneMode === 'edge' && doneEdge && finalContent) {
                  const client = getChatApiClient();
                  client.recordEdgeRationale({
                    edgeId: doneEdge.edgeId,
                    sourceNodeId: doneEdge.sourceNodeId,
                    targetNodeId: doneEdge.targetNodeId,
                    sourceConcept: doneEdge.sourceNodeName,
                    targetConcept: doneEdge.targetNodeName,
                    relationType: 'related_to',
                    rationaleText: finalContent,
                    confidence: 0.5,
                  }).catch((err) =>
                    console.warn('[Story 4-2] Edge rationale recording failed:', err)
                  );
                }

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

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3-9: Engine control
  // ═══════════════════════════════════════════════════════════════════════════

  switchEngine: async (engine: ActiveEngine) => {
    const mgr = getFallbackManager();
    const reason = engine === 'claude-code'
      ? '手动切换回 Claude Code 模式'
      : '手动切换到 API Key 模式';
    await mgr.switchEngine(engine, reason);
    set({ activeEngine: engine, engineUnavailable: false });
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3-10: Quota management
  // ═══════════════════════════════════════════════════════════════════════════

  dismissQuotaExhausted: () => {
    // User chose "wait for reset" — set quotaStatus to 'available' so the banner
    // is dismissed and the user can attempt to send again. If the quota is still
    // exhausted, the next send will re-detect it via a 429 response and re-set
    // quotaStatus to 'exhausted'.
    set({ quotaStatus: 'available', quotaResetTime: null, quotaRetryAfterSec: null });
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 3-11: Crash recovery
  // ═══════════════════════════════════════════════════════════════════════════

  manualRetry: async (nodeTitle: string) => {
    const recovery = getCrashRecovery();
    const cachedMsg = recovery.manualRetry();
    if (!cachedMsg) return;

    // Re-send the cached message
    set({ recoveryStatus: 'recovering' });
    await get().sendMessage(cachedMsg.message, nodeTitle);
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 4-1/4-2: Edge dialog
  // ═══════════════════════════════════════════════════════════════════════════

  switchToEdge: async (edge: EdgeContext) => {
    // Abort any in-progress stream
    const prevNodeId = get().currentNodeId;
    if (prevNodeId && get().isStreaming) {
      const mgr = getFallbackManager();
      await mgr.abort(prevNodeId);
    }

    // Use edge_{edgeId} as the session key for message persistence
    const edgeSessionKey = `edge_${edge.edgeId}`;

    const total = await countMessages(edgeSessionKey);
    const messages = await loadMessages(edgeSessionKey, PAGE_SIZE);

    set({
      currentNodeId: edgeSessionKey,
      messages,
      isStreaming: false,
      waitingForFirstToken: false,
      hasMore: total > PAGE_SIZE,
      totalCount: total,
      chatMode: 'edge',
      currentEdge: edge,
    });
  },

  exitEdgeMode: () => {
    set({
      chatMode: 'normal',
      currentEdge: null,
      currentNodeId: null,
      messages: [],
      hasMore: false,
      totalCount: 0,
    });
  },
}));

// ═══════════════════════════════════════════════════════════════════════════════
// Engine error listener setup (runs once on module load)
// Handles Story 3-9 fallback, Story 3-10 quota, Story 3-11 crash
// ═══════════════════════════════════════════════════════════════════════════════

function setupEngineListeners(): void {
  const mgr = getFallbackManager();

  // Listen for engine errors
  mgr.onError((error) => {
    if (error.type === 'rate_limited') {
      // Story 3-10: Set quota exhausted state
      let resetTime: string | null = null;
      if (error.retryAfterSec) {
        const resetDate = new Date(Date.now() + error.retryAfterSec * 1000);
        resetTime = resetDate.toISOString();
      }
      useChatStore.setState({
        quotaStatus: 'exhausted',
        quotaResetTime: resetTime,
        quotaRetryAfterSec: error.retryAfterSec ?? null,
      });
    } else if (error.type === 'auth_failed' || error.type === 'not_installed' || error.type === 'spawn_failed') {
      // Story 3-9: Engine fallback handled by EngineFallbackManager
      // Update store to reflect new active engine
      useChatStore.setState({
        activeEngine: mgr.activeEngine,
      });
    } else if (error.type === 'crash') {
      // Story 3-11: Handle crash via CrashRecoveryManager
      const recovery = getCrashRecovery();
      const result = recovery.recordCrash(error.exitCode ?? null, error.message);
      useChatStore.setState({
        recoveryStatus: result.action === 'auto_retry'
          ? 'recovering'
          : result.action === 'circuit_open'
            ? 'circuit_open'
            : 'failed',
      });
    }
  });

  // Listen for engine switch events (Story 3-9)
  mgr.onEngineSwitch((engine) => {
    useChatStore.setState({ activeEngine: engine });
  });

  // Listen for crash recovery status changes (Story 3-11)
  const recovery = getCrashRecovery();
  recovery.onStatusChange((status) => {
    useChatStore.setState({ recoveryStatus: status });
  });

  // Story 4-2: Set up edge label update callback on the API client
  const client = getChatApiClient();
  client.setEdgeLabelUpdateCallback((edgeId: string, relationType: string) => {
    console.info(`[Story 4-2] Edge label update: edge=${edgeId} type=${relationType}`);
    // The edge label update is dispatched via WebSocket from the backend
    // after recordEdgeRationale succeeds. Consumers (e.g. canvas store)
    // can listen to this callback via the ApiClient instance.
  });
}

// Lazy initialization: set up listeners on first store subscription
// instead of eagerly on module load (which triggers side effects during
// imports and can cause issues in test environments or SSR).
let _listenersInitialized = false;
useChatStore.subscribe(() => {
  if (!_listenersInitialized) {
    _listenersInitialized = true;
    setupEngineListeners();
  }
});
