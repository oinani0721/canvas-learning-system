/**
 * Canvas Learning System - Engine Fallback Manager
 * Story 3.9: Engine Fallback (AC-1, AC-2, AC-3, AC-4)
 *
 * Monitors ClaudeCodeEngine errors and orchestrates automatic fallback
 * to ApiKeyEngine when spawn fails (auth error / binary not found).
 *
 * Fallback decision tree:
 * ```
 * spawn Claude Code CLI
 *   ├── Success → use ClaudeCodeEngine (normal mode)
 *   └── Failure
 *       ├── exit code 2 (auth) → check fallback API Key
 *       │   ├── Has Key → switch to ApiKeyEngine + Notice
 *       │   └── No Key → Notice: configure API Key + link to Settings
 *       ├── ENOENT (binary missing) → same as above
 *       └── Other errors → Story 3.11 Crash Recovery
 * ```
 *
 * [Source: _bmad-output/implementation-artifacts/3-9-engine-fallback.md#Task 2]
 */

import { Notice } from 'obsidian';

import type { DialogEngine, EngineError } from './dialog-engine';
import { ApiKeyEngine } from './api-key-engine';
import { ClaudeCodeEngine } from './claude-code-engine';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export type ActiveEngineType = 'claude-code' | 'api-key';

export interface EngineFallbackCallbacks {
  /** Called when the active engine changes. */
  onEngineSwitch: (
    newEngine: DialogEngine,
    engineType: ActiveEngineType,
  ) => void;
  /** Called to get the current fallback API Key from settings. */
  getFallbackApiKey: () => string;
  /** Called to persist the current engine type to settings. */
  saveEngineType: (type: ActiveEngineType) => Promise<void>;
  /** Called to open the Settings Tab for API Key configuration. */
  openSettings: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EngineFallbackManager
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manages automatic engine fallback from ClaudeCodeEngine to ApiKeyEngine.
 *
 * Story 3.9 AC-1: Detects spawn failures (exit code 2 / ENOENT)
 * Story 3.9 AC-2: Shows user-friendly Notice with guidance
 * Story 3.9 AC-3: Transparent engine switching
 * Story 3.9 AC-4: Conversation history preserved (SQLite/Dexie independent of engine)
 */
export class EngineFallbackManager {
  private primaryEngine: ClaudeCodeEngine;
  private fallbackEngine: ApiKeyEngine | null = null;
  private callbacks: EngineFallbackCallbacks;
  private currentType: ActiveEngineType = 'claude-code';

  /**
   * Whether a fallback has already been attempted in this session.
   * Prevents repeated fallback attempts when the primary engine
   * continues to fail after switching back.
   */
  private fallbackAttempted = false;

  constructor(
    primaryEngine: ClaudeCodeEngine,
    callbacks: EngineFallbackCallbacks,
  ) {
    this.primaryEngine = primaryEngine;
    this.callbacks = callbacks;

    // Listen for errors from the primary engine
    this.primaryEngine.onError((error: EngineError) => {
      this.handleEngineError(error);
    });
  }

  /**
   * Get the currently active engine type.
   */
  getActiveType(): ActiveEngineType {
    return this.currentType;
  }

  /**
   * Get the currently active engine instance.
   */
  getActiveEngine(): DialogEngine {
    if (this.currentType === 'api-key' && this.fallbackEngine) {
      return this.fallbackEngine;
    }
    return this.primaryEngine;
  }

  /**
   * Manually switch back to ClaudeCodeEngine.
   * Called when user fixes their subscription and wants to switch back.
   *
   * Story 3.9 AC-4 (manual switch-back): User can restore primary engine.
   */
  async switchToPrimary(): Promise<void> {
    if (this.currentType === 'claude-code') return;

    this.currentType = 'claude-code';
    this.fallbackAttempted = false;
    this.callbacks.onEngineSwitch(this.primaryEngine, 'claude-code');
    await this.callbacks.saveEngineType('claude-code');

    new Notice('已切换回 Claude Code 订阅模式', 3000);
  }

  /**
   * Manually switch to ApiKeyEngine.
   * Called from quota management (Story 3.10) when user chooses to switch.
   */
  async switchToApiKey(): Promise<void> {
    const apiKey = this.callbacks.getFallbackApiKey();
    if (!apiKey) {
      new Notice(
        '请先在设置中配置备用 API Key',
        5000,
      );
      this.callbacks.openSettings();
      return;
    }

    this.activateFallbackEngine(apiKey);
  }

  /**
   * Clean up resources.
   */
  async destroy(): Promise<void> {
    if (this.fallbackEngine) {
      await this.fallbackEngine.destroyAll();
      this.fallbackEngine = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Handle engine errors and decide whether to trigger fallback.
   *
   * Only auth_failed and spawn_failed errors trigger fallback.
   * rate_limited → Story 3.10, crash → Story 3.11.
   */
  private handleEngineError(error: EngineError): void {
    // Only handle auth/spawn failures for fallback
    if (error.type !== 'auth_failed' && error.type !== 'spawn_failed') {
      return;
    }

    // Prevent repeated fallback loops
    if (this.fallbackAttempted) {
      return;
    }

    this.fallbackAttempted = true;

    const apiKey = this.callbacks.getFallbackApiKey();

    if (apiKey) {
      // Has backup API Key → auto-switch
      this.activateFallbackEngine(apiKey);

      new Notice(
        '订阅认证不可用，已自动切换到 API Key 模式',
        10000,
      );
    } else {
      // No backup API Key → prompt user to configure
      const notice = new Notice(
        '订阅认证不可用。请在设置中配置备用 API Key 以继续使用 AI 对话功能。',
        10000,
      );

      // The notice element can be clicked to open settings
      notice.noticeEl.style.cursor = 'pointer';
      notice.noticeEl.addEventListener('click', () => {
        this.callbacks.openSettings();
        notice.hide();
      });
    }
  }

  /**
   * Create and activate the fallback ApiKeyEngine.
   */
  private activateFallbackEngine(apiKey: string): void {
    // Create or update the fallback engine
    if (this.fallbackEngine) {
      this.fallbackEngine.setApiKey(apiKey);
    } else {
      this.fallbackEngine = new ApiKeyEngine(apiKey);

      // Forward fallback engine errors
      this.fallbackEngine.onError((error: EngineError) => {
        console.error('[Canvas Learning] ApiKeyEngine error:', error);
      });
    }

    this.currentType = 'api-key';
    this.callbacks.onEngineSwitch(this.fallbackEngine, 'api-key');
    this.callbacks.saveEngineType('api-key');
  }
}
