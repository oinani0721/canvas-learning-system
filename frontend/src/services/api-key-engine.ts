/**
 * Canvas Learning System - API Key Engine (Fallback Mode)
 * Story 3-9: Engine Fallback mechanism
 *
 * Direct Anthropic API calls when Claude Code CLI is unavailable.
 * Uses the same StreamEvent interface as ClaudeEngine for transparent
 * substitution. Maintains conversation history via messages array
 * (no --resume, since there's no CLI session).
 *
 * Reference: Anthropic SDK messages.stream() API
 * Reference: v1-ref/src/services/api-key-engine.ts (Obsidian version)
 */

import type { StreamEvent, SendMessageOptions, EngineError, EngineErrorCallback } from './claude-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/** A single message in the conversation history array. */
interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

/** sessionStorage key for the fallback API key (not persisted across sessions for security). */
const FALLBACK_API_KEY_STORAGE = 'canvas-learning-fallback-api-key';

/** Per-node conversation history for session continuity. */
const CONVERSATION_STORAGE_PREFIX = 'canvas-learning:apikey-conversations:';

/** Maximum messages retained in conversation context. */
const MAX_CONTEXT_MESSAGES = 40;

// ═══════════════════════════════════════════════════════════════════════════════
// ApiKeyEngine
// ═══════════════════════════════════════════════════════════════════════════════

export class ApiKeyEngine {
  private conversations: Map<string, ConversationMessage[]> = new Map();
  private errorCallbacks: EngineErrorCallback[] = [];
  private activeAbortControllers: Map<string, AbortController> = new Map();

  constructor() {
    // Load persisted conversations from localStorage
    this.loadConversations();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // API Key Management
  // ═══════════════════════════════════════════════════════════════════════════

  /** Get the stored fallback API key (sessionStorage — not persisted across browser sessions). */
  static getApiKey(): string {
    return sessionStorage.getItem(FALLBACK_API_KEY_STORAGE) ?? '';
  }

  /** Store the fallback API key in sessionStorage (cleared when browser tab closes). */
  static setApiKey(key: string): void {
    if (key.trim()) {
      sessionStorage.setItem(FALLBACK_API_KEY_STORAGE, key);
    } else {
      sessionStorage.removeItem(FALLBACK_API_KEY_STORAGE);
    }
  }

  /** Check if a fallback API key is configured. */
  static hasApiKey(): boolean {
    const key = ApiKeyEngine.getApiKey();
    return key.length > 0 && key.startsWith('sk-');
  }

  /**
   * Test API key validity by making a minimal API call.
   * Returns { valid: true } or { valid: false, error: string }.
   */
  static async testApiKey(apiKey: string): Promise<{ valid: boolean; error?: string }> {
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 10,
          messages: [{ role: 'user', content: 'test' }],
        }),
      });

      if (response.ok) {
        return { valid: true };
      }

      if (response.status === 401) {
        return { valid: false, error: 'API Key 无效或已过期' };
      }
      if (response.status === 403) {
        return { valid: false, error: 'API Key 权限不足' };
      }
      if (response.status === 429) {
        // Rate limited but key is valid
        return { valid: true };
      }

      const body = await response.text();
      return { valid: false, error: `API 错误 (${response.status}): ${body.slice(0, 200)}` };
    } catch (err) {
      return {
        valid: false,
        error: err instanceof Error ? err.message : '网络错误',
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Message Sending (Streaming via Fetch + ReadableStream)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Send a message to the Anthropic API for a specific node.
   * Uses streaming via fetch + ReadableStream (SSE).
   * Maintains per-node conversation history for context.
   */
  async sendMessage(
    options: SendMessageOptions,
    onEvent: (event: StreamEvent) => void,
  ): Promise<void> {
    const { nodeId, message, systemPrompt } = options;

    // Prevent concurrent requests for the same node
    if (this.activeAbortControllers.has(nodeId)) {
      onEvent({
        type: 'error',
        error: `A conversation is already active for node ${nodeId}. Please wait for it to complete.`,
      });
      return;
    }

    const apiKey = ApiKeyEngine.getApiKey();
    if (!apiKey) {
      const err: EngineError = {
        type: 'auth_failed',
        message: '未配置备用 API Key。请在设置中配置 Anthropic API Key。',
      };
      this.emitError(err);
      onEvent({ type: 'error', error: err.message });
      return;
    }

    // Build messages array with conversation history
    const history = this.getConversation(nodeId);
    const messages = [
      ...history,
      { role: 'user' as const, content: message },
    ];

    // Trim to max context size (keep most recent messages)
    const trimmedMessages = messages.length > MAX_CONTEXT_MESSAGES
      ? messages.slice(-MAX_CONTEXT_MESSAGES)
      : messages;

    const abortController = new AbortController();
    this.activeAbortControllers.set(nodeId, abortController);

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 4096,
          stream: true,
          system: systemPrompt ?? undefined,
          messages: trimmedMessages,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text();

        if (response.status === 401 || response.status === 403) {
          const err: EngineError = {
            type: 'auth_failed',
            message: 'API Key 认证失败，请检查 Key 是否有效。',
            exitCode: response.status,
          };
          this.emitError(err);
          onEvent({ type: 'error', error: err.message });
          return;
        }

        if (response.status === 429) {
          const retryAfterSec = this.extractRetryAfter(response, errorBody);
          const err: EngineError = {
            type: 'rate_limited',
            message: 'API 额度已用完，请稍后重试。',
            exitCode: 429,
            retryAfterSec: retryAfterSec ?? undefined,
          };
          this.emitError(err);
          onEvent({ type: 'error', error: err.message });
          return;
        }

        onEvent({ type: 'error', error: `API error (${response.status}): ${errorBody.slice(0, 200)}` });
        return;
      }

      // Stream the response
      const reader = response.body?.getReader();
      if (!reader) {
        onEvent({ type: 'error', error: 'No response body stream available' });
        return;
      }

      const decoder = new TextDecoder();
      let fullText = '';
      let sseBuffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });

        // Parse SSE events
        const lines = sseBuffer.split('\n');
        sseBuffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') continue;

            try {
              const event = JSON.parse(data) as Record<string, unknown>;
              const eventType = event.type as string;

              if (eventType === 'content_block_delta') {
                const delta = event.delta as Record<string, unknown> | undefined;
                if (delta?.type === 'text_delta') {
                  const text = delta.text as string;
                  fullText += text;
                  onEvent({ type: 'text', text });
                }
              } else if (eventType === 'message_stop') {
                // Done
              } else if (eventType === 'error') {
                const errorObj = event.error as Record<string, unknown> | undefined;
                const errorMsg = (errorObj?.message as string) ?? 'Stream error';
                onEvent({ type: 'error', error: errorMsg });
              }
            } catch {
              // Skip unparseable SSE data
            }
          }
        }
      }

      // Save conversation history
      history.push({ role: 'user', content: message });
      if (fullText) {
        history.push({ role: 'assistant', content: fullText });
      }
      this.setConversation(nodeId, history);

      onEvent({ type: 'done' });
    } catch (err) {
      if (abortController.signal.aborted) {
        // User-initiated abort
        onEvent({ type: 'error', error: 'Request aborted' });
      } else {
        const errorMsg = err instanceof Error ? err.message : String(err);
        onEvent({ type: 'error', error: `API Key engine error: ${errorMsg}` });
      }
    } finally {
      this.activeAbortControllers.delete(nodeId);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Session / Conversation Management
  // ═══════════════════════════════════════════════════════════════════════════

  /** Check if a node has an active request. */
  isActive(nodeId: string): boolean {
    return this.activeAbortControllers.has(nodeId);
  }

  /** Abort the active request for a node. */
  async abort(nodeId: string): Promise<void> {
    const controller = this.activeAbortControllers.get(nodeId);
    if (controller) {
      controller.abort();
      this.activeAbortControllers.delete(nodeId);
    }
  }

  /** Destroy session for a node: abort + clear conversation history. */
  async destroySession(nodeId: string): Promise<void> {
    await this.abort(nodeId);
    this.conversations.delete(nodeId);
    localStorage.removeItem(CONVERSATION_STORAGE_PREFIX + nodeId);
  }

  /** Clean up all resources. */
  async destroyAll(): Promise<void> {
    for (const controller of this.activeAbortControllers.values()) {
      controller.abort();
    }
    this.activeAbortControllers.clear();
    this.errorCallbacks = [];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Error Handling
  // ═══════════════════════════════════════════════════════════════════════════

  onError(callback: EngineErrorCallback): void {
    this.errorCallbacks.push(callback);
  }

  offError(callback: EngineErrorCallback): void {
    this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal
  // ═══════════════════════════════════════════════════════════════════════════

  private getConversation(nodeId: string): ConversationMessage[] {
    if (!this.conversations.has(nodeId)) {
      try {
        const stored = localStorage.getItem(CONVERSATION_STORAGE_PREFIX + nodeId);
        if (stored) {
          const parsed = JSON.parse(stored) as ConversationMessage[];
          this.conversations.set(nodeId, parsed);
        } else {
          this.conversations.set(nodeId, []);
        }
      } catch {
        this.conversations.set(nodeId, []);
      }
    }
    return this.conversations.get(nodeId)!;
  }

  private setConversation(nodeId: string, messages: ConversationMessage[]): void {
    // Keep only recent messages to prevent localStorage bloat
    const trimmed = messages.length > MAX_CONTEXT_MESSAGES
      ? messages.slice(-MAX_CONTEXT_MESSAGES)
      : messages;
    this.conversations.set(nodeId, trimmed);
    try {
      localStorage.setItem(
        CONVERSATION_STORAGE_PREFIX + nodeId,
        JSON.stringify(trimmed),
      );
    } catch {
      // localStorage full — silently fail
    }
  }

  private loadConversations(): void {
    // Conversations are loaded lazily in getConversation()
  }

  private extractRetryAfter(response: Response, _body: string): number | null {
    const header = response.headers.get('retry-after');
    if (header) {
      const seconds = parseInt(header, 10);
      if (!isNaN(seconds)) return seconds;
    }
    return null;
  }

  private emitError(error: EngineError): void {
    for (const cb of this.errorCallbacks) {
      try {
        cb(error);
      } catch (e) {
        console.error('[ApiKeyEngine] Error in error callback:', e);
      }
    }
  }
}
