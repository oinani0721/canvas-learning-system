/**
 * Canvas Learning System - Claude Code Engine (Tauri 2.0)
 *
 * Spawns the official `claude` CLI binary as a child process via
 * @tauri-apps/plugin-shell to provide AI dialogue capabilities.
 * Inherits authentication from the user's Claude Code subscription
 * (~/.claude/.credentials.json).
 *
 * Key features:
 * - Per-node sessions via --resume (conversation continuity)
 * - Authentication auto-inheritance from Claude Code subscription
 * - NDJSON stream-json parsing for real-time token streaming
 * - Error classification (auth_failed, rate_limited, crash)
 * - Auto-reconnect on crash (restart process with --resume)
 * - System prompt injection via --append-system-prompt
 *
 * Architecture:
 *   Tauri App (React UI)
 *     -> ClaudeEngine
 *       -> @tauri-apps/plugin-shell Command.create('claude-cli', [...args])
 *         -> --resume $nodeSessionId
 *         -> --output-format stream-json
 *         -> --append-system-prompt "learning context"
 *     -> StreamEvent -> React State -> UI
 *
 * Reference: v1-ref/src/services/claude-code-engine.ts (Obsidian version)
 * Reference: Claudian (YishenTu/claudian) - spawn mode, session management
 */

import { Command, type Child } from '@tauri-apps/plugin-shell';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/** Classification of engine errors for UI-level handling. */
export type EngineErrorType =
  | 'not_installed'   // claude CLI not found on system
  | 'auth_failed'     // subscription/auth invalid (exit code 2)
  | 'rate_limited'    // 429 / quota exhausted
  | 'crash'           // unexpected process crash
  | 'spawn_failed';   // failed to start process

/** Structured engine error for consumer handling. */
export interface EngineError {
  type: EngineErrorType;
  message: string;
  exitCode?: number | null;
  retryAfterSec?: number;
  cause?: unknown;
}

/** Callback for engine-level errors (auth, rate limit, crash). */
export type EngineErrorCallback = (error: EngineError) => void;

/**
 * Stream events emitted during a Claude CLI conversation.
 * Consumers iterate over these to update the UI in real time.
 */
export type StreamEvent =
  | { type: 'text'; text: string; raw?: string }
  | { type: 'tool_use'; toolName: string; toolInput: Record<string, unknown>; raw?: string }
  | { type: 'tool_result'; toolResult: string; raw?: string }
  | { type: 'error'; error: string; raw?: string }
  | { type: 'done'; sessionId?: string; costUsd?: number; raw?: string };

/** Options for sending a message to a node. */
export interface SendMessageOptions {
  /** User's message text. */
  message: string;
  /** Node ID for session tracking. */
  nodeId: string;
  /** Optional system prompt to append (learning context). */
  systemPrompt?: string;
  /** Optional MCP config file path. */
  mcpConfigPath?: string;
  /** Optional allowed-tools list. */
  allowedTools?: string[];
}

/** Result of a CLI availability check. */
export interface CliCheckResult {
  available: boolean;
  version?: string;
  error?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Scoped command name configured in src-tauri/capabilities/default.json.
 * Maps to the `claude` binary on the system PATH.
 */
const CLAUDE_COMMAND_NAME = 'claude-cli';

/** Exit code indicating authentication failure from Claude CLI. */
const AUTH_FAILED_EXIT_CODE = 2;

/** Maximum auto-restart attempts on crash before giving up. */
const MAX_CRASH_RESTARTS = 2;

/** Delay (ms) before auto-restart after a crash. */
const CRASH_RESTART_DELAY_MS = 1500;

/**
 * Patterns that indicate a 429 rate limit error in stderr or stream-json output.
 */
const RATE_LIMIT_PATTERNS = [
  /rate.?limit/i,
  /429/,
  /too many requests/i,
  /quota.*exceeded/i,
  /rate_limit_error/i,
];

// ═══════════════════════════════════════════════════════════════════════════════
// Helper functions
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Extract retry-after seconds from error text, if available.
 * Tries "retry-after: N" header-style and "try again in N seconds/minutes" natural language.
 */
function extractRetryAfter(text: string): number | null {
  const headerMatch = text.match(/retry[- ]after[:\s]+(\d+)/i);
  if (headerMatch) {
    return parseInt(headerMatch[1], 10);
  }
  const naturalMatch = text.match(
    /try again in (\d+)\s*(second|minute|hour)/i,
  );
  if (naturalMatch) {
    const value = parseInt(naturalMatch[1], 10);
    const unit = naturalMatch[2].toLowerCase();
    if (unit.startsWith('minute')) return value * 60;
    if (unit.startsWith('hour')) return value * 3600;
    return value;
  }
  return null;
}

/** Check whether an error string matches known rate limit patterns. */
function isRateLimitError(text: string): boolean {
  return RATE_LIMIT_PATTERNS.some((p) => p.test(text));
}

// ═══════════════════════════════════════════════════════════════════════════════
// Session Store (in-memory with localStorage persistence)
// ═══════════════════════════════════════════════════════════════════════════════

/** Persistent node-to-session-ID mapping. */
interface SessionEntry {
  sessionId: string;
  lastActiveAt: string;
}

const SESSION_STORAGE_KEY = 'canvas-learning:claude-sessions';

class SessionStore {
  private sessions: Map<string, SessionEntry>;

  constructor() {
    this.sessions = new Map();
    this.load();
  }

  /** Load sessions from localStorage. */
  private load(): void {
    try {
      const raw = localStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Record<string, SessionEntry>;
        for (const [nodeId, entry] of Object.entries(parsed)) {
          this.sessions.set(nodeId, entry);
        }
      }
    } catch {
      // Corrupt data - start fresh
      this.sessions.clear();
    }
  }

  /** Persist sessions to localStorage. */
  private save(): void {
    try {
      const obj: Record<string, SessionEntry> = {};
      for (const [nodeId, entry] of this.sessions) {
        obj[nodeId] = entry;
      }
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(obj));
    } catch {
      // localStorage full or unavailable - silent fail
    }
  }

  getSessionId(nodeId: string): string | null {
    return this.sessions.get(nodeId)?.sessionId ?? null;
  }

  setSession(nodeId: string, sessionId: string): void {
    this.sessions.set(nodeId, {
      sessionId,
      lastActiveAt: new Date().toISOString(),
    });
    this.save();
  }

  updateLastActive(nodeId: string): void {
    const entry = this.sessions.get(nodeId);
    if (entry) {
      entry.lastActiveAt = new Date().toISOString();
      this.save();
    }
  }

  deleteSession(nodeId: string): void {
    this.sessions.delete(nodeId);
    this.save();
  }

  clear(): void {
    this.sessions.clear();
    this.save();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ClaudeEngine
// ═══════════════════════════════════════════════════════════════════════════════

export class ClaudeEngine {
  private sessionStore: SessionStore;
  private errorCallbacks: EngineErrorCallback[] = [];
  private activeProcesses: Map<string, Child> = new Map();
  /** Track crash restart counts per node to prevent infinite restart loops. */
  private crashCounts: Map<string, number> = new Map();

  constructor() {
    this.sessionStore = new SessionStore();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CLI Availability Check
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Check if the `claude` CLI is installed and accessible.
   * Runs `claude --version` and parses the output.
   */
  async checkCliAvailable(): Promise<CliCheckResult> {
    try {
      const output = await Command.create(CLAUDE_COMMAND_NAME, [
        '--version',
      ]).execute();

      if (output.code === 0) {
        const version = output.stdout.trim();
        return { available: true, version };
      }

      return {
        available: false,
        error: `claude --version exited with code ${output.code}: ${output.stderr}`,
      };
    } catch (err) {
      return {
        available: false,
        error: err instanceof Error
          ? err.message
          : 'Failed to execute claude CLI',
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Message Sending (Streaming)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Send a message to Claude Code for a specific node.
   *
   * Spawns `claude -p "message" --output-format stream-json` and streams
   * NDJSON events back to the caller via callback. Uses --resume if the
   * node has an existing session.
   *
   * @param options - Message options (nodeId, message, systemPrompt, etc.)
   * @param onEvent - Callback invoked for each StreamEvent.
   * @returns Promise that resolves when the conversation turn completes.
   */
  async sendMessage(
    options: SendMessageOptions,
    onEvent: (event: StreamEvent) => void,
  ): Promise<void> {
    const { nodeId } = options;

    // Prevent concurrent processes for the same node
    if (this.activeProcesses.has(nodeId)) {
      onEvent({
        type: 'error',
        error: `A conversation is already active for node ${nodeId}. Please wait for it to complete.`,
      });
      return;
    }

    // Reset crash count for fresh message attempts
    this.crashCounts.delete(nodeId);

    await this.spawnAndStream(options, onEvent, 0);
  }

  /**
   * Internal: spawn the CLI process and handle streaming.
   * Supports auto-restart on crash via the `attemptNumber` parameter.
   */
  private async spawnAndStream(
    options: SendMessageOptions,
    onEvent: (event: StreamEvent) => void,
    attemptNumber: number,
  ): Promise<void> {
    const { nodeId, message, systemPrompt, mcpConfigPath, allowedTools } = options;

    // Build CLI arguments
    const args = this.buildArgs(message, {
      systemPrompt,
      mcpConfigPath,
      allowedTools,
    });

    // Add --resume if this node has an existing session
    const existingSessionId = this.sessionStore.getSessionId(nodeId);
    if (existingSessionId) {
      args.push('--resume', existingSessionId);
    }

    // Create the Command via Tauri shell plugin
    const command = Command.create(CLAUDE_COMMAND_NAME, args);

    // State for NDJSON parsing
    let stdoutBuffer = '';
    let stderrOutput = '';
    let lastSessionId: string | null = null;

    // Handle stdout: accumulate NDJSON lines and parse them
    command.stdout.on('data', (line: string) => {
      stdoutBuffer += line;

      // Process complete lines (NDJSON = one JSON object per line)
      const lines = stdoutBuffer.split('\n');
      stdoutBuffer = lines.pop() ?? ''; // Keep incomplete last line in buffer

      for (const rawLine of lines) {
        const trimmed = rawLine.trim();
        if (!trimmed) continue;

        const event = this.parseNdjsonLine(trimmed);
        if (event) {
          // Extract session ID from result events
          if (event.type === 'done' && event.sessionId) {
            lastSessionId = event.sessionId;
          }
          onEvent(event);
        }
      }
    });

    // Handle stderr: accumulate for error classification
    command.stderr.on('data', (line: string) => {
      stderrOutput += line;
    });

    // Spawn the process
    let child: Child;
    try {
      child = await command.spawn();
      this.activeProcesses.set(nodeId, child);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      const isNotFound =
        errorMessage.includes('not found') ||
        errorMessage.includes('ENOENT') ||
        errorMessage.includes('program not found');

      const engineError: EngineError = {
        type: isNotFound ? 'not_installed' : 'spawn_failed',
        message: isNotFound
          ? 'Claude Code CLI not found. Please install Claude Code (https://docs.anthropic.com/en/docs/claude-code) first.'
          : `Failed to spawn Claude Code: ${errorMessage}`,
        cause: err,
      };
      this.emitError(engineError);
      onEvent({ type: 'error', error: engineError.message });
      return;
    }

    // Wait for the process to close
    return new Promise<void>((resolve) => {
      command.on('close', async (payload) => {
        const { code, signal } = payload;

        // Process any remaining stdout buffer
        if (stdoutBuffer.trim()) {
          const event = this.parseNdjsonLine(stdoutBuffer.trim());
          if (event) {
            if (event.type === 'done' && event.sessionId) {
              lastSessionId = event.sessionId;
            }
            onEvent(event);
          }
          stdoutBuffer = '';
        }

        // Clean up active process tracking
        this.activeProcesses.delete(nodeId);

        // Classify the exit
        if (signal !== null) {
          // External termination (e.g., user killed)
          onEvent({
            type: 'error',
            error: `Process terminated by signal ${signal}`,
          });
        } else if (code === AUTH_FAILED_EXIT_CODE) {
          // Auth failure
          const engineError: EngineError = {
            type: 'auth_failed',
            message:
              'Claude Code authentication failed. Please log in to Claude Code.',
            exitCode: AUTH_FAILED_EXIT_CODE,
          };
          this.emitError(engineError);
          onEvent({ type: 'error', error: engineError.message });
        } else if (code !== null && code !== 0 && isRateLimitError(stderrOutput)) {
          // 429 Rate Limit
          const retryAfterSec = extractRetryAfter(stderrOutput);
          const engineError: EngineError = {
            type: 'rate_limited',
            message: 'Subscription quota exhausted. Please try again later.',
            exitCode: code,
            retryAfterSec: retryAfterSec ?? undefined,
          };
          this.emitError(engineError);
          onEvent({ type: 'error', error: engineError.message });
        } else if (code !== null && code !== 0) {
          // Other non-zero exit: crash
          const crashCount = (this.crashCounts.get(nodeId) ?? 0) + 1;
          this.crashCounts.set(nodeId, crashCount);

          if (crashCount <= MAX_CRASH_RESTARTS && lastSessionId) {
            // Auto-restart with --resume
            console.warn(
              `[ClaudeEngine] Crash detected for node "${nodeId}" (attempt ${crashCount}/${MAX_CRASH_RESTARTS}). Auto-restarting in ${CRASH_RESTART_DELAY_MS}ms...`,
            );
            onEvent({
              type: 'error',
              error: `Process crashed (exit code ${code}). Restarting automatically...`,
            });

            // Save session before restart
            if (lastSessionId) {
              this.sessionStore.setSession(nodeId, lastSessionId);
            }

            await new Promise<void>((r) =>
              setTimeout(r, CRASH_RESTART_DELAY_MS),
            );

            // Restart with same options (--resume will pick up the saved session)
            await this.spawnAndStream(options, onEvent, attemptNumber + 1);
            resolve();
            return;
          }

          // Max restarts exceeded or no session to resume
          const msg =
            stderrOutput.trim() || `Process exited with code ${code}`;
          const engineError: EngineError = {
            type: 'crash',
            message: msg,
            exitCode: code,
          };
          this.emitError(engineError);
          onEvent({ type: 'error', error: msg });
        }

        // Save session ID for future --resume
        if (lastSessionId) {
          const currentSessionId = this.sessionStore.getSessionId(nodeId);
          if (currentSessionId !== lastSessionId) {
            this.sessionStore.setSession(nodeId, lastSessionId);
          } else {
            this.sessionStore.updateLastActive(nodeId);
          }
        }

        // Emit done event
        onEvent({
          type: 'done',
          sessionId: lastSessionId ?? undefined,
        });

        resolve();
      });

      // Handle spawn-level errors (distinct from process exit)
      command.on('error', (errorMsg: string) => {
        this.activeProcesses.delete(nodeId);
        const engineError: EngineError = {
          type: 'crash',
          message: `Claude Code process error: ${errorMsg}`,
        };
        this.emitError(engineError);
        onEvent({ type: 'error', error: engineError.message });
        resolve();
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Session Management
  // ═══════════════════════════════════════════════════════════════════════════

  /** Get the session ID for a node. */
  getSessionId(nodeId: string): string | null {
    return this.sessionStore.getSessionId(nodeId);
  }

  /** Check if a node has an active conversation process. */
  isActive(nodeId: string): boolean {
    return this.activeProcesses.has(nodeId);
  }

  /**
   * Abort the active conversation for a node by killing the child process.
   */
  async abort(nodeId: string): Promise<void> {
    const child = this.activeProcesses.get(nodeId);
    if (child) {
      await child.kill();
      this.activeProcesses.delete(nodeId);
    }
  }

  /**
   * Destroy the session for a node: kill active process and remove session mapping.
   */
  async destroySession(nodeId: string): Promise<void> {
    await this.abort(nodeId);
    this.sessionStore.deleteSession(nodeId);
  }

  /**
   * Clean up all resources: kill all active processes and clear error callbacks.
   */
  async destroyAll(): Promise<void> {
    const killPromises: Promise<void>[] = [];
    for (const [nodeId, child] of this.activeProcesses) {
      killPromises.push(
        child.kill().catch((err) => {
          console.warn(
            `[ClaudeEngine] Failed to kill process for node "${nodeId}":`,
            err,
          );
        }),
      );
    }
    await Promise.all(killPromises);
    this.activeProcesses.clear();
    this.errorCallbacks = [];
    this.crashCounts.clear();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Error Handling
  // ═══════════════════════════════════════════════════════════════════════════

  /** Register an error callback for engine-level errors. */
  onError(callback: EngineErrorCallback): void {
    this.errorCallbacks.push(callback);
  }

  /** Remove an error callback. */
  offError(callback: EngineErrorCallback): void {
    this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Build CLI arguments for the `claude` command.
   *
   * Base args: `-p "message" --output-format stream-json`
   * Optional: `--append-system-prompt`, `--mcp-config`, `--allowedTools`
   */
  private buildArgs(
    message: string,
    opts: {
      systemPrompt?: string;
      mcpConfigPath?: string;
      allowedTools?: string[];
    } = {},
  ): string[] {
    const args: string[] = [
      '-p',
      message,
      '--output-format',
      'stream-json',
      '--verbose',
    ];

    // Inject learning context as appended system prompt
    if (opts.systemPrompt) {
      args.push('--append-system-prompt', opts.systemPrompt);
    }

    // Add MCP config if available
    if (opts.mcpConfigPath) {
      args.push('--mcp-config', opts.mcpConfigPath);
    }

    // Restrict allowed tools if specified
    if (opts.allowedTools && opts.allowedTools.length > 0) {
      for (const tool of opts.allowedTools) {
        args.push('--allowedTools', tool);
      }
    }

    return args;
  }

  /**
   * Parse a single NDJSON line from Claude Code's stream-json output.
   *
   * Expected formats from the CLI:
   * - `{"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}`
   * - `{"type":"result","subtype":"success","session_id":"abc123","cost_usd":0.001}`
   * - `{"type":"system","message":"..."}`
   * - `{"type":"error","error":{"type":"rate_limit_error","message":"..."}}`
   */
  private parseNdjsonLine(line: string): StreamEvent | null {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(line) as Record<string, unknown>;
    } catch {
      // Not valid JSON - skip (could be progress dots or other non-JSON output)
      return null;
    }

    const eventType = parsed.type as string;

    // Handle assistant message events
    if (eventType === 'assistant') {
      const message = parsed.message as
        | Record<string, unknown>
        | undefined;
      if (message?.content && Array.isArray(message.content)) {
        const contentBlocks = message.content as Array<
          Record<string, unknown>
        >;
        for (const block of contentBlocks) {
          if (block.type === 'text') {
            return {
              type: 'text',
              text: block.text as string,
              raw: line,
            };
          }
          if (block.type === 'tool_use') {
            return {
              type: 'tool_use',
              toolName: block.name as string,
              toolInput: block.input as Record<string, unknown>,
              raw: line,
            };
          }
          if (block.type === 'tool_result') {
            return {
              type: 'tool_result',
              toolResult: block.content as string,
              raw: line,
            };
          }
        }
      }
      return null;
    }

    // Handle result events (end of response)
    if (eventType === 'result') {
      return {
        type: 'done',
        sessionId: parsed.session_id as string | undefined,
        costUsd: parsed.cost_usd as number | undefined,
        raw: line,
      };
    }

    // Handle system/error events
    if (eventType === 'system' || eventType === 'error') {
      const errorObj = parsed.error as
        | Record<string, unknown>
        | string
        | undefined;
      const errorType =
        typeof errorObj === 'object'
          ? (errorObj?.type as string)
          : undefined;
      const errorMsg =
        (typeof errorObj === 'object'
          ? (errorObj?.message as string)
          : (errorObj as string)) ??
        (parsed.message as string) ??
        'Unknown error';

      // Detect rate_limit_error from stream-json
      if (errorType === 'rate_limit_error' || isRateLimitError(errorMsg)) {
        const retryAfterSec = extractRetryAfter(errorMsg);
        this.emitError({
          type: 'rate_limited',
          message: 'Subscription quota exhausted. Please try again later.',
          retryAfterSec: retryAfterSec ?? undefined,
        });
      }

      return {
        type: 'error',
        error: errorMsg,
        raw: line,
      };
    }

    // Unknown event type - return as raw text for debugging
    return {
      type: 'text',
      text: '',
      raw: line,
    };
  }

  /** Emit an error to all registered callbacks. */
  private emitError(error: EngineError): void {
    for (const cb of this.errorCallbacks) {
      try {
        cb(error);
      } catch (e) {
        console.error('[ClaudeEngine] Error in engine error callback:', e);
      }
    }
  }
}
