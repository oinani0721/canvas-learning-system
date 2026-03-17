/**
 * Canvas Learning System - Claude Code Engine
 * Story 3.1: Claude Code CLI Integration (AC-1, AC-2, AC-3, AC-4)
 *
 * Spawns the official `claude` CLI binary as a child process to provide
 * AI dialogue capabilities. Inherits authentication from the user's
 * Claude Code subscription (~/.claude/.credentials.json).
 *
 * Key features:
 * - Per-node sessions via --resume (AC-3)
 * - Authentication auto-inheritance (AC-2)
 * - Stream-json NDJSON parsing (AC-1)
 * - DialogEngine interface compliance (AC-5)
 *
 * Reference: Claudian (YishenTu/claudian) — spawn mode, session management
 *
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 2]
 * [Source: _decisions/ADR-001-dialogue-engine.md]
 */

import { spawn, type ChildProcess } from 'child_process';

import type {
  DialogEngine,
  EngineError,
  EngineErrorCallback,
  StreamEvent,
} from './dialog-engine';
import { SessionStore } from './session-store';

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

/** Default Claude Code binary name (expected to be on PATH). */
const CLAUDE_BINARY = 'claude';

/** Exit code indicating authentication failure. */
const AUTH_FAILED_EXIT_CODE = 2;

// ═══════════════════════════════════════════════════════════════════════════════
// ClaudeCodeEngine
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * DialogEngine implementation that spawns the official Claude Code CLI.
 *
 * Architecture (from ADR-001):
 * ```
 * Obsidian Plugin (Svelte UI)
 *   -> DialogEngine interface
 *     -> ClaudeCodeEngine (this class)
 *       -> child_process.spawn('claude', [...args])
 *         -> --resume $nodeSessionId
 *         -> --mcp-config ./canvas-mcp.json
 *         -> --output-format stream-json
 *   -> StreamEvent -> Svelte Store -> UI
 * ```
 */
export class ClaudeCodeEngine implements DialogEngine {
  private sessionStore: SessionStore;
  private mcpConfigPath: string | null;
  private errorCallbacks: EngineErrorCallback[] = [];
  private activeProcesses: Map<string, ChildProcess> = new Map();

  /**
   * Create a ClaudeCodeEngine.
   *
   * @param pluginDataDir - Plugin data directory for session persistence.
   * @param mcpConfigPath - Path to the MCP config file (from Story 3.2).
   *   If null, --mcp-config flag is omitted.
   */
  constructor(pluginDataDir: string, mcpConfigPath: string | null = null) {
    this.sessionStore = new SessionStore(pluginDataDir);
    this.mcpConfigPath = mcpConfigPath;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DialogEngine Interface Implementation
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Send a message to Claude Code for a specific node.
   *
   * Story 3.1 AC-1: Spawns `claude -p "message" --output-format stream-json`
   * Story 3.1 AC-3: Uses `--resume sessionId` if the node has an existing session
   *
   * @param nodeId - The canvas node identifier.
   * @param message - The user's message text.
   * @returns An async iterable of StreamEvents parsed from NDJSON.
   */
  async *sendMessage(
    nodeId: string,
    message: string,
  ): AsyncIterable<StreamEvent> {
    // Prevent concurrent processes for the same node (constraint #4)
    if (this.activeProcesses.has(nodeId)) {
      yield {
        type: 'error',
        error: `A conversation is already active for node ${nodeId}. Please wait for it to complete.`,
      };
      return;
    }

    // Build CLI arguments
    const args = this.buildArgs(message);

    // Add --resume if this node has an existing session
    const existingSessionId = await this.sessionStore.getSessionId(nodeId);
    if (existingSessionId) {
      args.push('--resume', existingSessionId);
    }

    // Spawn the CLI process
    let proc: ChildProcess;
    try {
      proc = spawn(CLAUDE_BINARY, args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        // Inherit environment (includes ~/.claude/.credentials.json path)
        env: { ...process.env },
      });
      this.activeProcesses.set(nodeId, proc);
    } catch (err) {
      const error = err as NodeJS.ErrnoException;
      const engineError: EngineError = {
        type: error.code === 'ENOENT' ? 'auth_failed' : 'spawn_failed',
        message:
          error.code === 'ENOENT'
            ? 'Claude Code CLI not found. Please install Claude Code first.'
            : `Failed to spawn Claude Code: ${error.message}`,
        cause: error,
      };
      this.emitError(engineError);
      yield { type: 'error', error: engineError.message };
      return;
    }

    // Parse NDJSON stream from stdout
    let buffer = '';
    let lastSessionId: string | null = null;

    try {
      // Create a promise that resolves when the process exits
      const exitPromise = new Promise<number | null>((resolve) => {
        proc.on('close', (code) => resolve(code));
        proc.on('error', (err) => {
          this.emitError({
            type: 'crash',
            message: `Claude Code process error: ${err.message}`,
            cause: err,
          });
          resolve(null);
        });
      });

      // Read stdout as async iterable
      if (proc.stdout) {
        for await (const chunk of proc.stdout) {
          buffer += chunk.toString('utf-8');

          // Process complete lines (NDJSON = one JSON object per line)
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? ''; // Keep incomplete last line in buffer

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            const event = this.parseNdjsonLine(trimmed);
            if (event) {
              // Extract session ID from result events
              if (event.sessionId) {
                lastSessionId = event.sessionId;
              }
              yield event;
            }
          }
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        const event = this.parseNdjsonLine(buffer.trim());
        if (event) {
          if (event.sessionId) {
            lastSessionId = event.sessionId;
          }
          yield event;
        }
      }

      // Collect stderr for error reporting
      let stderrOutput = '';
      if (proc.stderr) {
        for await (const chunk of proc.stderr) {
          stderrOutput += chunk.toString('utf-8');
        }
      }

      // Wait for process to exit
      const exitCode = await exitPromise;

      // Handle exit codes
      if (exitCode === AUTH_FAILED_EXIT_CODE) {
        const engineError: EngineError = {
          type: 'auth_failed',
          message:
            'Claude Code authentication failed. Please log in to Claude Code.',
          exitCode: AUTH_FAILED_EXIT_CODE,
        };
        this.emitError(engineError);
        yield { type: 'error', error: engineError.message };
      } else if (exitCode !== null && exitCode !== 0) {
        const msg = stderrOutput.trim() || `Process exited with code ${exitCode}`;
        yield { type: 'error', error: msg };
      }

      // Save session ID for future --resume (AC-3)
      if (lastSessionId) {
        const currentSessionId =
          await this.sessionStore.getSessionId(nodeId);
        if (currentSessionId !== lastSessionId) {
          await this.sessionStore.createSession(nodeId, lastSessionId);
        } else {
          await this.sessionStore.updateLastActive(nodeId);
        }
      }

      // Emit done event
      yield { type: 'done', sessionId: lastSessionId ?? undefined };
    } finally {
      this.activeProcesses.delete(nodeId);
    }
  }

  /**
   * Resume a session (no-op for CLI mode since sessions are file-based).
   * The actual resume happens via --resume flag in sendMessage.
   */
  async resume(_sessionId: string): Promise<void> {
    // In CLI mode, resume is handled by --resume flag in sendMessage.
    // This method exists for interface compatibility.
  }

  /**
   * Get the session ID for a node from the persistent store.
   */
  async getSessionId(nodeId: string): Promise<string | null> {
    return this.sessionStore.getSessionId(nodeId);
  }

  /**
   * Destroy the session for a node and kill any active process.
   */
  async destroy(nodeId: string): Promise<void> {
    // Kill active process if running
    const proc = this.activeProcesses.get(nodeId);
    if (proc) {
      proc.kill('SIGTERM');
      this.activeProcesses.delete(nodeId);
    }

    // Remove session mapping
    await this.sessionStore.deleteSession(nodeId);
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
    // Kill all active processes
    for (const [nodeId, proc] of this.activeProcesses) {
      proc.kill('SIGTERM');
      this.activeProcesses.delete(nodeId);
    }
    this.errorCallbacks = [];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Internal Methods
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Build CLI arguments for the `claude` command.
   *
   * @param message - User message to send via -p flag.
   * @returns Array of CLI arguments.
   */
  private buildArgs(message: string): string[] {
    const args: string[] = [
      '-p',
      message,
      '--output-format',
      'stream-json',
    ];

    // Add MCP config if available (Story 3.2 integration point)
    if (this.mcpConfigPath) {
      args.push('--mcp-config', this.mcpConfigPath);
    }

    return args;
  }

  /**
   * Parse a single NDJSON line from Claude Code's stream-json output.
   *
   * Expected formats:
   * ```
   * {"type":"assistant","message":{"content":[{"type":"text","text":"Hello"}]}}
   * {"type":"result","subtype":"success","session_id":"abc123","cost_usd":0.001}
   * ```
   *
   * @param line - A single line of NDJSON output.
   * @returns Parsed StreamEvent, or null if the line is not parseable.
   */
  private parseNdjsonLine(line: string): StreamEvent | null {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(line) as Record<string, unknown>;
    } catch {
      // Not valid JSON — skip
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
      return {
        type: 'error',
        error:
          (parsed.message as string) ??
          (parsed.error as string) ??
          'Unknown error',
        raw: line,
      };
    }

    // Unknown event type — return raw for debugging
    return {
      type: 'text',
      text: '',
      raw: line,
    };
  }

  /**
   * Emit an error to all registered callbacks.
   */
  private emitError(error: EngineError): void {
    for (const cb of this.errorCallbacks) {
      try {
        cb(error);
      } catch (e) {
        console.error(
          '[Canvas Learning] Error in engine error callback:',
          e,
        );
      }
    }
  }
}
