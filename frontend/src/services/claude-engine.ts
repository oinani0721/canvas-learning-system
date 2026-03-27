/**
 * Canvas Learning System - Claude Code Engine (Tauri 2.0 + Agent SDK Sidecar)
 *
 * Communicates with a long-running Node.js sidecar process that wraps
 * @anthropic-ai/claude-agent-sdk. The sidecar runs Agent SDK's query()
 * function and streams results back via stdin/stdout NDJSON.
 *
 * Key features:
 * - Per-node sessions via SDK resume (conversation continuity)
 * - Authentication auto-inheritance from Claude Code subscription
 * - NDJSON IPC for real-time token streaming
 * - Error classification (auth_failed, rate_limited, crash)
 * - Singleton sidecar process with multiplexed conversations
 * - System prompt injection via SDK native systemPrompt option
 * - MCP tool integration via SDK native mcpServers option
 *
 * Architecture:
 *   Tauri App (React UI)
 *     -> ClaudeEngine (singleton sidecar management)
 *       -> @tauri-apps/plugin-shell Command.create('canvas-sidecar', [sidecarPath])
 *         -> stdin: {"cmd":"query","id":"req-1","prompt":"...","resume":"session-id",...}
 *         -> stdout: {"id":"req-1","type":"text","text":"Hello"}
 *     -> StreamEvent -> React State -> UI
 *
 * Reference: Solo IDE (Tauri+SDK+sidecar), Opcode (public source)
 * Supersedes: CLI spawn mode (Mode D → Spawn CLI → SDK migration → Tier B → Agent SDK sidecar)
 */

import { Command, type Child } from '@tauri-apps/plugin-shell';

// ═══════════════════════════════════════════════════════════════════════════════
// Types (UNCHANGED — preserved for backward compatibility)
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
 * Stream events emitted during a Claude conversation.
 * Consumers iterate over these to update the UI in real time.
 */
export type StreamEvent =
  | { type: 'text'; text: string; raw?: string }
  | { type: 'tool_use'; toolName: string; toolInput: Record<string, unknown>; raw?: string }
  | { type: 'tool_result'; toolResult: string; raw?: string }
  | { type: 'error'; error: string; raw?: string }
  | { type: 'done'; sessionId?: string; costUsd?: number; raw?: string }
  // GDR: Permission request from sidecar PreToolUse hook
  | { type: 'permission_request'; toolUseId: string; toolName: string; toolInput: Record<string, unknown>; nodeId: string; raw?: string };

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
 * Maps to `node` binary on the system PATH (sidecar: false).
 */
const SIDECAR_COMMAND_NAME = 'canvas-sidecar';

/**
 * Absolute path to the sidecar script, injected by Vite at build time.
 * Tauri binary CWD is src-tauri/target/debug/, not the project root,
 * so relative paths don't work. Vite's `define` resolves this at compile time.
 */
declare const __SIDECAR_SCRIPT_PATH__: string;
const SIDECAR_SCRIPT_PATH = __SIDECAR_SCRIPT_PATH__;

/** Default MCP server URL for the backend. */
const DEFAULT_MCP_URL = 'http://localhost:8001/mcp';

/** Timeout (ms) to wait for sidecar ready signal. */
const SIDECAR_READY_TIMEOUT_MS = 15000;

/** Timeout (ms) for shutdown before force kill. */
const SHUTDOWN_TIMEOUT_MS = 5000;

/**
 * Patterns that indicate a 429 rate limit error.
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

/** Generate a unique request ID for IPC multiplexing. */
let reqCounter = 0;
function generateRequestId(): string {
  return `req-${Date.now()}-${++reqCounter}`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Session Store (in-memory with localStorage persistence) — UNCHANGED
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
// Pending Request Tracker
// ═══════════════════════════════════════════════════════════════════════════════

interface PendingRequest {
  nodeId: string;
  onEvent: (event: StreamEvent) => void;
  resolve: () => void;
  reject: (err: Error) => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// ClaudeEngine — Singleton Sidecar Mode
// ═══════════════════════════════════════════════════════════════════════════════

export class ClaudeEngine {
  private sessionStore: SessionStore;
  private errorCallbacks: EngineErrorCallback[] = [];

  /** Singleton sidecar process. */
  private sidecarChild: Child | null = null;
  /** Promise that resolves when sidecar is ready. */
  private sidecarReady: Promise<void> | null = null;

  /** Pending requests waiting for sidecar responses, keyed by request ID. */
  private pendingRequests: Map<string, PendingRequest> = new Map();
  /** Map nodeId → requestId for abort lookups. */
  private nodeToRequestId: Map<string, string> = new Map();

  /** Buffer for incomplete NDJSON lines from stdout. */
  private stdoutBuffer = '';

  constructor() {
    this.sessionStore = new SessionStore();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Sidecar Process Management
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Ensure the singleton sidecar process is running.
   * Lazy-starts on first use and reuses for subsequent calls.
   */
  private async ensureSidecar(): Promise<Child> {
    // Already running
    if (this.sidecarChild) {
      return this.sidecarChild;
    }

    // Already starting — wait for it
    if (this.sidecarReady) {
      await this.sidecarReady;
      if (this.sidecarChild) return this.sidecarChild;
      throw new Error('Sidecar failed to start');
    }

    // Start the sidecar
    this.sidecarReady = new Promise<void>((resolve, reject) => {
      this.startSidecar(resolve, reject);
    });

    await this.sidecarReady;

    if (!this.sidecarChild) {
      throw new Error('Sidecar failed to start');
    }
    return this.sidecarChild;
  }

  /**
   * Start the Node.js sidecar process via Tauri shell plugin.
   */
  private startSidecar(
    onReady: () => void,
    onFailure: (err: Error) => void,
  ): void {
    const command = Command.create(SIDECAR_COMMAND_NAME, [SIDECAR_SCRIPT_PATH]);

    // Ready timeout
    const readyTimeout = setTimeout(() => {
      onFailure(new Error('Sidecar startup timed out'));
    }, SIDECAR_READY_TIMEOUT_MS);

    let readyResolved = false;

    // Handle stdout: parse NDJSON lines and route to pending requests
    command.stdout.on('data', (line: string) => {
      this.stdoutBuffer += line;
      const lines = this.stdoutBuffer.split('\n');
      this.stdoutBuffer = lines.pop() ?? '';

      for (const rawLine of lines) {
        const trimmed = rawLine.trim();
        if (!trimmed) continue;

        let parsed: Record<string, unknown>;
        try {
          parsed = JSON.parse(trimmed) as Record<string, unknown>;
        } catch {
          continue; // Skip non-JSON output
        }

        // Handle sidecar ready signal (L-3 fix: defer until sidecarChild is set)
        if (parsed.type === 'ready' && !readyResolved) {
          readyResolved = true;
          clearTimeout(readyTimeout);
          // Wait for spawn().then() to set sidecarChild before resolving
          const waitForChild = () => {
            if (this.sidecarChild) {
              onReady();
            } else {
              setTimeout(waitForChild, 10);
            }
          };
          waitForChild();
          continue;
        }

        // Route to pending request by ID
        this.handleSidecarMessage(parsed);
      }
    });

    // Handle stderr: log sidecar debug output
    command.stderr.on('data', (line: string) => {
      console.debug('[sidecar]', line.trim());
    });

    // Handle process exit
    command.on('close', (payload) => {
      const { code } = payload;
      console.warn(`[ClaudeEngine] Sidecar exited with code ${code}`);

      this.sidecarChild = null;
      this.sidecarReady = null;
      this.stdoutBuffer = '';

      // Reject all pending requests
      for (const [reqId, pending] of this.pendingRequests) {
        pending.onEvent({
          type: 'error',
          error: 'Sidecar process exited unexpectedly',
        });
        pending.resolve();
        this.pendingRequests.delete(reqId);
      }
      this.nodeToRequestId.clear();

      // Emit crash error so CrashRecoveryManager can handle it
      if (code !== 0) {
        this.emitError({
          type: 'crash',
          message: `Sidecar process exited with code ${code}`,
          exitCode: code,
        });
      }

      if (!readyResolved) {
        readyResolved = true;
        clearTimeout(readyTimeout);
        onFailure(new Error(`Sidecar exited during startup (code ${code})`));
      }
    });

    command.on('error', (errorMsg: string) => {
      console.error(`[ClaudeEngine] Sidecar error: ${errorMsg}`);
      if (!readyResolved) {
        readyResolved = true;
        clearTimeout(readyTimeout);
        onFailure(new Error(`Sidecar error: ${errorMsg}`));
      }
    });

    // Spawn the process
    command.spawn().then(
      (child) => {
        this.sidecarChild = child;
      },
      (err) => {
        clearTimeout(readyTimeout);
        const errorMessage = err instanceof Error ? err.message : String(err);
        const isNotFound =
          errorMessage.includes('not found') ||
          errorMessage.includes('ENOENT') ||
          errorMessage.includes('program not found');

        if (!readyResolved) {
          readyResolved = true;
          onFailure(
            new Error(
              isNotFound
                ? 'Node.js not found. Please install Node.js first.'
                : `Failed to start sidecar: ${errorMessage}`,
            ),
          );
        }
      },
    );
  }

  /**
   * Route a parsed NDJSON message from the sidecar to the correct pending request.
   */
  private handleSidecarMessage(msg: Record<string, unknown>): void {
    const reqId = msg.id as string | null;
    if (!reqId) return; // Skip messages without an ID (like ready)

    const pending = this.pendingRequests.get(reqId);
    if (!pending) return; // No matching request — likely already resolved

    const msgType = msg.type as string;

    switch (msgType) {
      case 'text':
        pending.onEvent({
          type: 'text',
          text: msg.text as string,
        });
        break;

      case 'tool_use':
        pending.onEvent({
          type: 'tool_use',
          toolName: msg.toolName as string,
          toolInput: (msg.toolInput as Record<string, unknown>) || {},
        });
        break;

      case 'tool_result':
        pending.onEvent({
          type: 'tool_result',
          toolResult: msg.toolResult as string,
        });
        break;

      case 'permission_request':
        // GDR: Sidecar PreToolUse hook requests user confirmation for sensitive tools
        pending.onEvent({
          type: 'permission_request',
          toolUseId: msg.toolUseId as string,
          toolName: msg.toolName as string,
          toolInput: (msg.toolInput as Record<string, unknown>) || {},
          nodeId: msg.nodeId as string,
        });
        break;

      case 'done': {
        const sessionId = msg.sessionId as string | undefined;
        const costUsd = msg.costUsd as number | undefined;

        // Save session ID for future resume
        if (sessionId) {
          const currentSessionId = this.sessionStore.getSessionId(pending.nodeId);
          if (currentSessionId !== sessionId) {
            this.sessionStore.setSession(pending.nodeId, sessionId);
          } else {
            this.sessionStore.updateLastActive(pending.nodeId);
          }
        }

        pending.onEvent({
          type: 'done',
          sessionId,
          costUsd,
        });

        // Clean up and resolve
        this.pendingRequests.delete(reqId);
        this.nodeToRequestId.delete(pending.nodeId);
        pending.resolve();
        break;
      }

      case 'error': {
        const errorText = msg.error as string;
        const errorType = msg.errorType as EngineErrorType | undefined;
        const retryAfterSec = msg.retryAfterSec as number | undefined;

        pending.onEvent({
          type: 'error',
          error: errorText,
        });

        // Emit engine-level error for fallback handling (including crash)
        if (errorType) {
          this.emitError({
            type: errorType,
            message: errorText,
            retryAfterSec,
            exitCode: msg.exitCode as number | undefined,
          });
        } else if (isRateLimitError(errorText)) {
          this.emitError({
            type: 'rate_limited',
            message: errorText,
            retryAfterSec: retryAfterSec ?? extractRetryAfter(errorText) ?? undefined,
          });
        }

        // Clean up and resolve
        this.pendingRequests.delete(reqId);
        this.nodeToRequestId.delete(pending.nodeId);
        pending.resolve();
        break;
      }

      case 'ack':
        // Acknowledgment for abort/shutdown — no action needed
        break;

      default:
        // Unknown message type — ignore
        break;
    }
  }

  /**
   * Write a JSON command to the sidecar's stdin.
   */
  private async writeSidecarCommand(cmd: Record<string, unknown>): Promise<void> {
    if (!this.sidecarChild) {
      throw new Error('Sidecar not running');
    }
    await this.sidecarChild.write(JSON.stringify(cmd) + '\n');
  }

  /**
   * GDR: Send permission response to sidecar for a PreToolUse hook request.
   * Called by chat-store when user approves or denies a sensitive tool call.
   */
  async sendPermissionResponse(toolUseId: string, decision: 'allow' | 'deny'): Promise<void> {
    await this.writeSidecarCommand({
      cmd: 'permission_response',
      id: `perm-${toolUseId}`,
      toolUseId,
      decision,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CLI Availability Check
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Check if the sidecar can be started (Node.js available + sidecar script exists).
   */
  async checkCliAvailable(): Promise<CliCheckResult> {
    try {
      // Check if node is available
      const output = await Command.create(SIDECAR_COMMAND_NAME, [
        '--version',
      ]).execute();

      if (output.code === 0) {
        const version = `sidecar (node ${output.stdout.trim()})`;
        return { available: true, version };
      }

      return {
        available: false,
        error: `Node.js check failed (code ${output.code}): ${output.stderr}`,
      };
    } catch (err) {
      return {
        available: false,
        error: err instanceof Error
          ? err.message
          : 'Failed to check Node.js availability',
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Message Sending (Streaming via Sidecar IPC)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Send a message to Claude for a specific node.
   *
   * Sends a query command to the sidecar via stdin. The sidecar runs
   * Agent SDK's query() and streams NDJSON events back to us via stdout.
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

    // Prevent concurrent conversations for the same node
    const existingReqId = this.nodeToRequestId.get(nodeId);
    if (existingReqId && this.pendingRequests.has(existingReqId)) {
      onEvent({
        type: 'error',
        error: `A conversation is already active for node ${nodeId}. Please wait for it to complete.`,
      });
      return;
    }

    // Ensure sidecar is running
    try {
      await this.ensureSidecar();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      const isNotFound =
        errorMessage.includes('not found') ||
        errorMessage.includes('ENOENT') ||
        errorMessage.includes('Node.js not found');

      const engineError: EngineError = {
        type: isNotFound ? 'not_installed' : 'spawn_failed',
        message: isNotFound
          ? 'Node.js not found. Claude Code requires Node.js to be installed.'
          : `Failed to start sidecar: ${errorMessage}`,
        cause: err,
      };
      this.emitError(engineError);
      onEvent({ type: 'error', error: engineError.message });
      return;
    }

    // Generate request ID and register pending request
    const reqId = generateRequestId();

    return new Promise<void>((resolve, reject) => {
      this.pendingRequests.set(reqId, {
        nodeId,
        onEvent,
        resolve,
        reject,
      });
      this.nodeToRequestId.set(nodeId, reqId);

      // Build and send query command
      const existingSessionId = this.sessionStore.getSessionId(nodeId);

      const queryCmd: Record<string, unknown> = {
        cmd: 'query',
        id: reqId,
        prompt: options.message,
        nodeId,
      };

      // System prompt (SDK native option)
      if (options.systemPrompt) {
        queryCmd.systemPrompt = options.systemPrompt;
      }

      // Session resume
      if (existingSessionId) {
        queryCmd.resume = existingSessionId;
      }

      // F4: Set cwd to vault path so SDK can discover vault files
      try {
        const settingsJson = localStorage.getItem('canvas-learning-settings');
        if (settingsJson) {
          const settings = JSON.parse(settingsJson) as { vaultPath?: string };
          if (settings.vaultPath) {
            queryCmd.cwd = settings.vaultPath;
          }
        }
      } catch {
        // Settings unavailable — SDK uses process.cwd() as fallback
      }

      // MCP servers (default: backend at localhost:8001/mcp)
      // S29 fix: Backend uses fastapi-mcp SSE transport (GET /mcp + POST /mcp/messages/).
      // 'http' (Streamable HTTP) sends POST /mcp which returns 405.
      queryCmd.mcpServers = {
        canvas: { type: 'sse', url: DEFAULT_MCP_URL },
      };

      // Allowed tools
      if (options.allowedTools && options.allowedTools.length > 0) {
        queryCmd.allowedTools = options.allowedTools;
      }

      // Send command to sidecar stdin
      this.writeSidecarCommand(queryCmd).catch((err) => {
        const errorMessage = err instanceof Error ? err.message : String(err);
        onEvent({ type: 'error', error: `Failed to send command: ${errorMessage}` });
        this.pendingRequests.delete(reqId);
        this.nodeToRequestId.delete(nodeId);
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

  /** Check if a node has an active conversation. */
  isActive(nodeId: string): boolean {
    const reqId = this.nodeToRequestId.get(nodeId);
    return reqId ? this.pendingRequests.has(reqId) : false;
  }

  /**
   * Abort the active conversation for a node by sending an abort command.
   */
  async abort(nodeId: string): Promise<void> {
    const reqId = this.nodeToRequestId.get(nodeId);
    if (!reqId) return;

    const pending = this.pendingRequests.get(reqId);

    try {
      await this.writeSidecarCommand({
        cmd: 'abort',
        id: generateRequestId(),
        nodeId,
      });
    } catch {
      // Sidecar may be down — clean up locally
    }

    // Clean up pending request
    if (pending) {
      pending.onEvent({ type: 'error', error: 'Conversation aborted' });
      pending.resolve();
    }
    this.pendingRequests.delete(reqId);
    this.nodeToRequestId.delete(nodeId);
  }

  /**
   * Destroy the session for a node: abort active conversation and remove session mapping.
   */
  async destroySession(nodeId: string): Promise<void> {
    await this.abort(nodeId);
    this.sessionStore.deleteSession(nodeId);
  }

  /**
   * Clean up all resources: shutdown sidecar and clear state.
   */
  async destroyAll(): Promise<void> {
    // Send shutdown command to sidecar
    if (this.sidecarChild) {
      try {
        await this.writeSidecarCommand({
          cmd: 'shutdown',
          id: generateRequestId(),
        });

        // M-1 fix: Wait for graceful exit with timeout, no polling interval
        await Promise.race([
          new Promise<void>((resolve) => {
            const check = () => {
              if (!this.sidecarChild) { resolve(); return; }
              setTimeout(check, 100);
            };
            check();
          }),
          new Promise<void>((resolve) => {
            setTimeout(async () => {
              if (this.sidecarChild) {
                await this.sidecarChild.kill().catch(() => {});
              }
              resolve();
            }, SHUTDOWN_TIMEOUT_MS);
          }),
        ]);
      } catch {
        // Force kill on any error
        if (this.sidecarChild) {
          await this.sidecarChild.kill().catch(() => {});
        }
      }
    }

    // Clean up all state
    this.sidecarChild = null;
    this.sidecarReady = null;
    this.stdoutBuffer = '';

    for (const [, pending] of this.pendingRequests) {
      pending.resolve();
    }
    this.pendingRequests.clear();
    this.nodeToRequestId.clear();
    this.errorCallbacks = [];
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
