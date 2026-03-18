/**
 * Canvas Learning System - Engine Fallback Manager
 * Story 3-9: Engine Fallback (CLI -> API Key degradation)
 *
 * Monitors ClaudeEngine errors and transparently switches to ApiKeyEngine
 * when the CLI is unavailable (auth failure, binary missing).
 *
 * Decision tree:
 *   spawn Claude Code CLI
 *     |- success -> ClaudeEngine (normal)
 *     |- auth_failed / not_installed -> check fallback API Key
 *     |   |- has key -> switch to ApiKeyEngine + notify
 *     |   |- no key  -> notify + prompt Settings
 *     |- rate_limited -> Story 3-10 quota management
 *     |- crash -> Story 3-11 crash recovery
 *
 * Reference: Claudian (YishenTu/claudian) - engine fallback pattern
 */

import { ClaudeEngine, type EngineError, type EngineErrorCallback, type StreamEvent, type SendMessageOptions } from './claude-engine';
import { ApiKeyEngine } from './api-key-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/** Which engine is currently active. */
export type ActiveEngine = 'claude-code' | 'api-key';

/** Callback when the engine is switched. */
export type EngineSwitchCallback = (engine: ActiveEngine, reason: string) => void;

/** localStorage key for persisted engine preference. */
const ENGINE_STATE_KEY = 'canvas-learning-active-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// EngineFallbackManager
// ═══════════════════════════════════════════════════════════════════════════════

export class EngineFallbackManager {
  private claudeEngine: ClaudeEngine;
  private apiKeyEngine: ApiKeyEngine;
  private _activeEngine: ActiveEngine;
  private switchCallbacks: EngineSwitchCallback[] = [];
  private engineErrorCallback: EngineErrorCallback;

  constructor() {
    this.claudeEngine = new ClaudeEngine();
    this.apiKeyEngine = new ApiKeyEngine();

    // Restore persisted engine preference
    const stored = localStorage.getItem(ENGINE_STATE_KEY);
    this._activeEngine = stored === 'api-key' ? 'api-key' : 'claude-code';

    // Listen to ClaudeEngine errors for automatic fallback
    this.engineErrorCallback = (error: EngineError) => {
      this.handleEngineError(error);
    };
    this.claudeEngine.onError(this.engineErrorCallback);
  }

  /** Get the currently active engine type. */
  get activeEngine(): ActiveEngine {
    return this._activeEngine;
  }

  /**
   * Send a message through whichever engine is currently active.
   * Transparent to the caller — same interface regardless of engine.
   */
  async sendMessage(
    options: SendMessageOptions,
    onEvent: (event: StreamEvent) => void,
  ): Promise<void> {
    if (this._activeEngine === 'api-key') {
      return this.apiKeyEngine.sendMessage(options, onEvent);
    }
    return this.claudeEngine.sendMessage(options, onEvent);
  }

  /** Check if a node has an active conversation. */
  isActive(nodeId: string): boolean {
    if (this._activeEngine === 'api-key') {
      return this.apiKeyEngine.isActive(nodeId);
    }
    return this.claudeEngine.isActive(nodeId);
  }

  /** Abort active conversation for a node. */
  async abort(nodeId: string): Promise<void> {
    if (this._activeEngine === 'api-key') {
      return this.apiKeyEngine.abort(nodeId);
    }
    return this.claudeEngine.abort(nodeId);
  }

  /** Get session ID (only meaningful for ClaudeEngine). */
  getSessionId(nodeId: string): string | null {
    if (this._activeEngine === 'claude-code') {
      return this.claudeEngine.getSessionId(nodeId);
    }
    return null;
  }

  /**
   * Manually switch to a specific engine.
   * Used when user wants to switch back to Claude Code after fixing subscription.
   */
  async switchEngine(engine: ActiveEngine, reason: string): Promise<void> {
    if (engine === this._activeEngine) return;

    this._activeEngine = engine;
    localStorage.setItem(ENGINE_STATE_KEY, engine);

    for (const cb of this.switchCallbacks) {
      try {
        cb(engine, reason);
      } catch (e) {
        console.error('[EngineFallbackManager] Error in switch callback:', e);
      }
    }
  }

  /**
   * Attempt to switch to API Key fallback.
   * Returns true if switch was successful (key exists), false otherwise.
   */
  switchToApiKeyFallback(reason: string): boolean {
    if (!ApiKeyEngine.hasApiKey()) {
      return false;
    }
    this.switchEngine('api-key', reason);
    return true;
  }

  /** Register a callback for engine switch events. */
  onEngineSwitch(callback: EngineSwitchCallback): void {
    this.switchCallbacks.push(callback);
  }

  /** Remove an engine switch callback. */
  offEngineSwitch(callback: EngineSwitchCallback): void {
    this.switchCallbacks = this.switchCallbacks.filter((cb) => cb !== callback);
  }

  /** Register an error callback (forwarded from both engines). */
  onError(callback: EngineErrorCallback): void {
    this.claudeEngine.onError(callback);
    this.apiKeyEngine.onError(callback);
  }

  /** Remove an error callback. */
  offError(callback: EngineErrorCallback): void {
    this.claudeEngine.offError(callback);
    this.apiKeyEngine.offError(callback);
  }

  /** Get direct access to the ClaudeEngine (for session management). */
  getClaudeEngine(): ClaudeEngine {
    return this.claudeEngine;
  }

  /** Clean up all resources. */
  async destroy(): Promise<void> {
    this.claudeEngine.offError(this.engineErrorCallback);
    await this.claudeEngine.destroyAll();
    await this.apiKeyEngine.destroyAll();
    this.switchCallbacks = [];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal: Error-driven fallback
  // ═══════════════════════════════════════════════════════════════════════════

  private handleEngineError(error: EngineError): void {
    // Only handle auth/installation failures for automatic fallback
    if (error.type !== 'auth_failed' && error.type !== 'not_installed' && error.type !== 'spawn_failed') {
      return;
    }

    console.warn(
      `[EngineFallbackManager] Claude Code unavailable (${error.type}): ${error.message}. Attempting API Key fallback.`,
    );

    const switched = this.switchToApiKeyFallback(
      error.type === 'auth_failed'
        ? '订阅认证不可用，已切换到 API Key 模式'
        : 'Claude Code CLI 不可用，已切换到 API Key 模式',
    );

    if (!switched) {
      console.warn(
        '[EngineFallbackManager] No fallback API Key configured. User needs to configure one in Settings.',
      );
    }
  }
}
