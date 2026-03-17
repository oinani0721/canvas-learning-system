/**
 * Canvas Learning System - Dialog Engine Interface
 * Story 3.1: Claude Code CLI Integration (AC-5)
 *
 * Defines the pluggable DialogEngine interface that decouples the conversation
 * layer from any specific AI provider. The MVP implementation is ClaudeCodeEngine
 * (spawn CLI), with future slots for ApiKeyEngine and AcpEngine.
 *
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 1]
 * [Source: _decisions/ADR-001-dialogue-engine.md — FR-AGENT-03 engine replaceable]
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Stream Event Types (Task 1.2)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Events emitted during a streaming dialogue response.
 *
 * Aligned with Claude Code's `--output-format stream-json` NDJSON output.
 */
export type StreamEventType =
  | 'text'
  | 'tool_use'
  | 'tool_result'
  | 'error'
  | 'done';

export interface StreamEvent {
  /** Event type discriminator. */
  type: StreamEventType;

  /** Text content (for 'text' events). */
  text?: string;

  /** Tool name (for 'tool_use' events). */
  toolName?: string;

  /** Tool input parameters (for 'tool_use' events). */
  toolInput?: Record<string, unknown>;

  /** Tool result content (for 'tool_result' events). */
  toolResult?: string;

  /** Error message (for 'error' events). */
  error?: string;

  /** Session ID returned by Claude Code (for 'done' events). */
  sessionId?: string;

  /** Cost in USD (for 'done' events). */
  costUsd?: number;

  /** Raw NDJSON line for debugging. */
  raw?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Engine Error Types (Task 1.3)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Error types that can be emitted by a DialogEngine.
 *
 * - auth_failed: Claude Code authentication failed (exit code 2 / ENOENT)
 * - spawn_failed: Failed to start the CLI process
 * - rate_limited: Hit rate limits
 * - crash: Unexpected process crash
 */
export type EngineErrorType =
  | 'auth_failed'
  | 'spawn_failed'
  | 'rate_limited'
  | 'crash';

export interface EngineError {
  type: EngineErrorType;
  message: string;
  exitCode?: number;
  /** Original error for debugging. */
  cause?: Error;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Engine Event Callback
// ═══════════════════════════════════════════════════════════════════════════════

export type EngineErrorCallback = (error: EngineError) => void;

// ═══════════════════════════════════════════════════════════════════════════════
// DialogEngine Interface (Task 1.1)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Pluggable interface for AI dialogue engines.
 *
 * Story 3.1 AC-5: Defines a common contract so the conversation layer
 * can work with any engine implementation without modification.
 *
 * Current implementations:
 *   - ClaudeCodeEngine: Spawns the official `claude` CLI binary (MVP)
 *
 * Future implementations:
 *   - ApiKeyEngine: Direct API Key calls (Story 3.9 Fallback)
 *   - AcpEngine: Agent Communication Protocol (long-term)
 */
export interface DialogEngine {
  /**
   * Send a message to the AI and receive a stream of events.
   *
   * For a new node (no existing session), creates a new session.
   * For an existing node, resumes the session via --resume.
   *
   * @param nodeId - The canvas node identifier.
   * @param message - The user's message text.
   * @returns An async iterable of StreamEvents.
   */
  sendMessage(nodeId: string, message: string): AsyncIterable<StreamEvent>;

  /**
   * Resume a session without sending a new message.
   * Used to restore conversation state when switching nodes.
   *
   * @param sessionId - The Claude Code session identifier.
   */
  resume(sessionId: string): Promise<void>;

  /**
   * Get the session ID associated with a node.
   *
   * @param nodeId - The canvas node identifier.
   * @returns The session ID, or null if no session exists.
   */
  getSessionId(nodeId: string): Promise<string | null>;

  /**
   * Destroy the session for a node.
   * Stops any active process and cleans up resources.
   *
   * @param nodeId - The canvas node identifier.
   */
  destroy(nodeId: string): Promise<void>;

  /**
   * Register an error callback.
   * Called when the engine encounters an error (auth, spawn, crash, etc.).
   *
   * @param callback - Error handler function.
   */
  onError(callback: EngineErrorCallback): void;

  /**
   * Clean up all resources (all sessions, processes, listeners).
   * Called during plugin unload.
   */
  destroyAll(): Promise<void>;
}
