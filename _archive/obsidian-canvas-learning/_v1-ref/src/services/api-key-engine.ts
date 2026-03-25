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

import { requestUrl } from 'obsidian';
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
      // Use Obsidian's requestUrl() to bypass Electron CSP restrictions.
      // requestUrl() does not support streaming, so we use non-streaming mode.
      // This is acceptable since API Key mode is a degraded fallback.
      // Reference: Obsidian official API — requestUrl() runs at Node level.
      const response = await requestUrl({
        url: ANTHROPIC_API_URL,
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
          // Non-streaming: requestUrl doesn't support SSE ReadableStream
        }),
        throw: false, // Don't throw on non-200, we handle errors manually
      });

      if (response.status === 429) {
        const retryAfter = response.headers?.['retry-after'];
        const engineError: EngineError = {
          type: 'rate_limited',
          message: 'API 额度已用完',
          retryAfterSec: retryAfter ? parseInt(retryAfter, 10) : undefined,
        };
        this.emitError(engineError);
        history.pop();
        yield { type: 'error', error: engineError.message };
        return;
      }

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

      if (response.status < 200 || response.status >= 300) {
        history.pop();
        yield {
          type: 'error',
          error: `API request failed (${response.status}): ${response.text}`,
        };
        return;
      }

      // Parse non-streaming response (Anthropic Messages API response format)
      const result = response.json;
      let assistantContent = '';

      if (result?.content && Array.isArray(result.content)) {
        for (const block of result.content) {
          if (block.type === 'text' && block.text) {
            assistantContent += block.text;
            yield { type: 'text', text: block.text };
          }
        }
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
