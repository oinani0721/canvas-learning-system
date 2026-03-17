/**
 * Canvas Learning System - API Key Engine
 * Story 3.9: Engine Fallback (AC-3)
 *
 * Fallback DialogEngine implementation that uses a direct Anthropic API Key
 * instead of spawning the Claude Code CLI. Activated when CLI spawn fails
 * (auth error / binary not found) and the user has configured a backup API Key.
 *
 * Key differences from ClaudeCodeEngine:
 * - Authentication: user-provided API Key (not CLI credentials)
 * - Session: maintained via conversation history array (not --resume)
 * - Streaming: fetch-based SSE from Anthropic Messages API
 * - MCP: not supported in API Key mode (backend tools only)
 *
 * Reference: Anthropic Messages API
 *   POST https://api.anthropic.com/v1/messages
 *   Header: x-api-key, anthropic-version
 *
 * [Source: _bmad-output/implementation-artifacts/3-9-engine-fallback.md#Task 1]
 */

import type {
  DialogEngine,
  EngineError,
  EngineErrorCallback,
  StreamEvent,
} from './dialog-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_VERSION = '2023-06-01';
const DEFAULT_MODEL = 'claude-sonnet-4-20250514';
const MAX_TOKENS = 8192;

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// ApiKeyEngine
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * DialogEngine that calls the Anthropic Messages API directly using an API Key.
 *
 * Story 3.9 AC-3: Implements the same DialogEngine interface as ClaudeCodeEngine,
 * allowing transparent engine switching without UI changes.
 */
export class ApiKeyEngine implements DialogEngine {
  private apiKey: string;
  private model: string;
  private errorCallbacks: EngineErrorCallback[] = [];

  /**
   * Per-node conversation history.
   * Since we cannot use --resume (CLI feature), we maintain the full
   * conversation history in memory and send it with each request.
   */
  private conversationHistories: Map<string, ConversationMessage[]> =
    new Map();

  /** Track active requests so they can be aborted on destroy. */
  private activeControllers: Map<string, AbortController> = new Map();

  /**
   * Create an ApiKeyEngine.
   *
   * @param apiKey - Anthropic API Key (from plugin settings).
   * @param model - Model identifier (default: claude-sonnet-4-20250514).
   */
  constructor(apiKey: string, model: string = DEFAULT_MODEL) {
    this.apiKey = apiKey;
    this.model = model;
  }

  /**
   * Update the API key (e.g., after user changes it in settings).
   */
  setApiKey(apiKey: string): void {
    this.apiKey = apiKey;
  }

  /**
   * Update the model (e.g., after user changes it in settings).
   */
  setModel(model: string): void {
    this.model = model;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DialogEngine Interface
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Send a message via the Anthropic Messages API with streaming.
   *
   * Story 3.9 AC-3: Uses fetch-based SSE streaming, converting Anthropic
   * stream events to the common StreamEvent format.
   */
  async *sendMessage(
    nodeId: string,
    message: string,
  ): AsyncIterable<StreamEvent> {
    if (!this.apiKey) {
      const engineError: EngineError = {
        type: 'auth_failed',
        message: '未配置备用 API Key，请在设置中配置。',
      };
      this.emitError(engineError);
      yield { type: 'error', error: engineError.message };
      return;
    }

    // Prevent concurrent requests for the same node
    if (this.activeControllers.has(nodeId)) {
      yield {
        type: 'error',
        error: `A conversation is already active for node ${nodeId}. Please wait for it to complete.`,
      };
      return;
    }

    // Get or create conversation history for this node
    const history = this.conversationHistories.get(nodeId) ?? [];

    // Append user message to history
    history.push({ role: 'user', content: message });

    // Create abort controller for cancellation
    const controller = new AbortController();
    this.activeControllers.set(nodeId, controller);

    try {
      const response = await fetch(ANTHROPIC_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': ANTHROPIC_VERSION,
        },
        body: JSON.stringify({
          model: this.model,
          max_tokens: MAX_TOKENS,
          messages: history,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();

        // Detect rate limiting
        if (response.status === 429) {
          const retryAfter = response.headers.get('retry-after');
          const engineError: EngineError = {
            type: 'rate_limited',
            message: 'API 额度已用完',
            retryAfterSec: retryAfter ? parseInt(retryAfter, 10) : undefined,
          };
          this.emitError(engineError);
          // Remove the failed user message from history
          history.pop();
          yield { type: 'error', error: engineError.message };
          return;
        }

        // Detect auth errors
        if (response.status === 401 || response.status === 403) {
          const engineError: EngineError = {
            type: 'auth_failed',
            message: 'API Key 无效或已过期，请在设置中更新。',
          };
          this.emitError(engineError);
          history.pop();
          yield { type: 'error', error: engineError.message };
          return;
        }

        // Other HTTP errors
        history.pop();
        yield {
          type: 'error',
          error: `API request failed (${response.status}): ${errorText}`,
        };
        return;
      }

      // Parse SSE stream
      const reader = response.body?.getReader();
      if (!reader) {
        history.pop();
        yield { type: 'error', error: 'No response body from API' };
        return;
      }

      const decoder = new TextDecoder();
      let sseBuffer = '';
      let assistantContent = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          sseBuffer += decoder.decode(value, { stream: true });

          // Process complete SSE events (separated by double newline)
          const eventBlocks = sseBuffer.split('\n\n');
          sseBuffer = eventBlocks.pop() ?? '';

          for (const block of eventBlocks) {
            const lines = block.split('\n');
            let eventType = '';
            let data = '';

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                data = line.slice(6);
              }
            }

            if (!data || data === '[DONE]') continue;

            let parsed: Record<string, unknown>;
            try {
              parsed = JSON.parse(data) as Record<string, unknown>;
            } catch {
              continue;
            }

            // Handle different SSE event types from Anthropic API
            if (eventType === 'content_block_delta') {
              const delta = parsed.delta as Record<string, unknown> | undefined;
              if (delta?.type === 'text_delta') {
                const text = delta.text as string;
                assistantContent += text;
                yield { type: 'text', text, raw: data };
              }
            } else if (eventType === 'message_stop') {
              // Message complete
              break;
            } else if (eventType === 'error') {
              const errorData = parsed.error as Record<string, unknown> | undefined;
              const errorMsg = (errorData?.message as string) ?? 'Unknown API error';
              yield { type: 'error', error: errorMsg, raw: data };
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Save assistant response to conversation history
      if (assistantContent) {
        history.push({ role: 'assistant', content: assistantContent });
      }
      this.conversationHistories.set(nodeId, history);

      // Emit done event (API Key mode has no session ID)
      yield { type: 'done' };
    } catch (err) {
      // Remove the failed user message from history
      history.pop();

      if ((err as Error).name === 'AbortError') {
        yield { type: 'error', error: 'Request cancelled' };
        return;
      }

      const engineError: EngineError = {
        type: 'crash',
        message: `API request failed: ${(err as Error).message}`,
        cause: err as Error,
      };
      this.emitError(engineError);
      yield { type: 'error', error: engineError.message };
    } finally {
      this.activeControllers.delete(nodeId);
    }
  }

  /**
   * Resume is a no-op for API Key mode.
   * Conversation context is maintained via the history array.
   */
  async resume(_sessionId: string): Promise<void> {
    // No-op: API Key engine maintains context via conversation history array.
  }

  /**
   * Get session ID — returns null since API Key mode doesn't use CLI sessions.
   */
  async getSessionId(_nodeId: string): Promise<string | null> {
    return null;
  }

  /**
   * Destroy the conversation for a node.
   */
  async destroy(nodeId: string): Promise<void> {
    // Abort any active request
    const controller = this.activeControllers.get(nodeId);
    if (controller) {
      controller.abort();
      this.activeControllers.delete(nodeId);
    }

    // Clear conversation history
    this.conversationHistories.delete(nodeId);
  }

  /**
   * Register an error callback.
   */
  onError(callback: EngineErrorCallback): void {
    this.errorCallbacks.push(callback);
  }

  /**
   * Clean up all resources.
   */
  async destroyAll(): Promise<void> {
    // Abort all active requests
    for (const [, controller] of this.activeControllers) {
      controller.abort();
    }
    this.activeControllers.clear();
    this.conversationHistories.clear();
    this.errorCallbacks = [];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal
  // ═══════════════════════════════════════════════════════════════════════════

  private emitError(error: EngineError): void {
    for (const cb of this.errorCallbacks) {
      try {
        cb(error);
      } catch (e) {
        console.error(
          '[Canvas Learning] Error in ApiKeyEngine error callback:',
          e,
        );
      }
    }
  }
}
