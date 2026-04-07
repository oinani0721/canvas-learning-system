#!/usr/bin/env node

/**
 * Canvas Learning System — Agent SDK Sidecar
 *
 * Long-running Node.js process that wraps @anthropic-ai/claude-agent-sdk.
 * Communicates with the Tauri frontend via stdin/stdout NDJSON.
 *
 * Protocol:
 *   stdin  (commands): {"cmd":"query|abort|ping|shutdown", "id":"...", ...}
 *   stdout (events):   {"id":"...", "type":"text|tool_use|tool_result|done|error|pong|ack|ready", ...}
 *   stderr:            logging only (never pollute NDJSON on stdout)
 *
 * SDK API (v0.2.79):
 *   query({ prompt, options }) → AsyncGenerator<SDKMessage>
 *   Options: { systemPrompt, abortController, cwd, resume, mcpServers, allowedTools,
 *              includePartialMessages, permissionMode, maxTurns }
 *   SDKMessage: SDKAssistantMessage | SDKPartialAssistantMessage (stream_event) |
 *               SDKResultMessage | SDKSystemMessage | SDKUserMessage | ...
 *
 * Reference: Solo IDE (Tauri + Agent SDK sidecar), Opcode (public source)
 */

import { query } from '@anthropic-ai/claude-agent-sdk';
import { createInterface } from 'node:readline';

// ─── Active Query Tracking ──────────────────────────────────────────────────

/**
 * @type {Map<string, { controller: AbortController, queryObj: object|null }>}
 * nodeId → { AbortController, Query object reference }
 */
const activeQueries = new Map();

// ─── Tool Permission Whitelists (audit-2026-04-07/p0-1: real permission gating) ─

/** MCP backend tools — always auto-allow (our own backend at localhost:8001/mcp). */
const MCP_TOOLS = new Set([
  'query_mastery', 'update_fsrs', 'update_bkt',
  'generate_question', 'score_answer', 'assemble_acp',
  'search_memories', 'record_calibration', 'record_learning_memory',
  'archive_conversation', 'create_exam_node', 'record_error',
  'request_hint', 'skip_question', 'search_notes',
]);

/**
 * Safe read-only SDK built-in tools — auto-allow without prompt.
 * audit-2026-04-07/p0-1: tightened — Read/Glob/Grep/LS/TodoRead are pure reads.
 * WebFetch/WebSearch/Task/TodoWrite moved to HIGH_RISK_SDK_TOOLS because they
 * either touch network, spawn agents, or mutate state.
 */
const SAFE_READONLY_SDK_TOOLS = new Set([
  'Read', 'Glob', 'Grep', 'LS', 'TodoRead',
]);

/**
 * High-risk SDK built-in tools — require user approval via permission_request.
 * Anything that hits the network, executes shell, writes files, or spawns
 * agents must be confirmed by the user. Defense in depth against prompt
 * injection (OWASP LLM01) and unintended actions (NIST AC-6 least privilege).
 */
const HIGH_RISK_SDK_TOOLS = new Set([
  // Networking — exfiltration / SSRF risk
  'WebFetch', 'WebSearch',
  // Shell / execution
  'Bash', 'Shell', 'Exec',
  // File writes / destructive
  'Write', 'Edit', 'MultiEdit', 'NotebookEdit',
  'Mkdir', 'Rm', 'Delete', 'Rename', 'Move', 'Copy',
  // Agent spawning / orchestration (can recursively run more tools)
  'Task', 'TodoWrite',
]);

/** Tools whose results contain student learning signals — trigger BEA extraction.
 *  Only tools where the STUDENT demonstrates understanding/misconception qualify.
 *  generate_question excluded: it's tutor output, not student signal. */
const BEA_EXTRACTION_TOOLS = new Set([
  'score_answer',
  'record_error',
]);

/** Permission approval timeout — fail-secure deny if user doesn't respond. */
const PERMISSION_TIMEOUT_MS = 30_000;

// ─── IPC Helpers ────────────────────────────────────────────────────────────

/** Write a single JSON line to stdout (NDJSON protocol). */
function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

/** Write a log line to stderr (never stdout). */
function log(...args) {
  process.stderr.write(`[sidecar] ${args.join(' ')}\n`);
}

// ─── Permission Request Pipeline (audit-2026-04-07/p0-1) ────────────────────

/**
 * Pending permission requests, keyed by toolUseId.
 * Each entry has { resolve, timer, nodeId } so the stdin handler can resolve
 * it when a permission_response arrives, the timer prevents indefinite hang,
 * and abort can sweep all entries belonging to a cancelled node.
 *
 * @type {Map<string, { resolve: (decision: 'allow' | 'deny') => void, timer: NodeJS.Timeout, nodeId: string }>}
 */
const pendingPermissions = new Map();

/** Patterns that look like secrets. We redact these before showing to the UI. */
const SECRET_PATTERNS = [
  // OpenAI / Anthropic style sk-... (40+ chars)
  /\bsk-[A-Za-z0-9_-]{20,}\b/g,
  // Google API key
  /\bAIza[0-9A-Za-z_-]{20,}\b/g,
  // GitHub token
  /\bghp_[A-Za-z0-9]{20,}\b/g,
  // Bearer tokens in headers
  /\bBearer\s+[A-Za-z0-9._-]{20,}\b/gi,
  // Generic JWT
  /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b/g,
];

/**
 * Redact secret-looking strings from arbitrary text.
 * Defensive layer in case prompt-injected content tries to leak credentials
 * via the permission card the user sees.
 */
function redactSecrets(text) {
  if (typeof text !== 'string') return text;
  let redacted = text;
  for (const pat of SECRET_PATTERNS) {
    redacted = redacted.replace(pat, '***REDACTED***');
  }
  return redacted;
}

/**
 * Build a safe JSON preview of toolInput for the permission card.
 * - Truncates each string field to 500 chars
 * - Redacts secrets
 * - Limits total size to 4KB so a malicious payload can't blow up the UI
 */
function safeJsonPreview(input) {
  if (input === null || input === undefined) return {};
  const seen = new WeakSet();
  const sanitize = (val) => {
    if (typeof val === 'string') {
      const truncated = val.length > 500 ? `${val.slice(0, 500)}…` : val;
      return redactSecrets(truncated);
    }
    if (Array.isArray(val)) return val.slice(0, 20).map(sanitize);
    if (val && typeof val === 'object') {
      if (seen.has(val)) return '[Circular]';
      seen.add(val);
      const out = {};
      let count = 0;
      for (const [k, v] of Object.entries(val)) {
        if (count >= 30) {
          out['…'] = `(${Object.keys(val).length - count} more)`;
          break;
        }
        out[k] = sanitize(v);
        count += 1;
      }
      return out;
    }
    return val;
  };
  const sanitized = sanitize(input);
  const json = JSON.stringify(sanitized);
  if (json.length > 4096) {
    return { __truncated__: true, preview: `${json.slice(0, 4096)}…` };
  }
  return sanitized;
}

/**
 * Request user approval for a high-risk tool call.
 *
 * Returns a Promise that resolves to 'allow' or 'deny'. If the user does not
 * respond within PERMISSION_TIMEOUT_MS, the request is auto-denied (fail-secure).
 *
 * @param {string} toolName
 * @param {object} toolInput
 * @param {string} nodeId
 * @param {string} requestId  parent query id (so frontend can route the event back)
 * @returns {Promise<'allow' | 'deny'>}
 */
function requestUserApproval(toolName, toolInput, nodeId, requestId) {
  // Use crypto.randomUUID (Node 18+, no import needed)
  const toolUseId =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `pcr-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      pendingPermissions.delete(toolUseId);
      log(`[Permission] Timeout waiting for user response on ${toolName}, denying.`);
      resolve('deny');
    }, PERMISSION_TIMEOUT_MS);

    pendingPermissions.set(toolUseId, { resolve, timer, nodeId });

    // Notify the frontend via the parent query's request id so the message
    // is routed to the right pendingRequest in claude-engine.ts.
    emit({
      id: requestId,
      type: 'permission_request',
      toolUseId,
      toolName,
      toolInput: safeJsonPreview(toolInput),
      nodeId,
    });

    log(`[Permission] Awaiting user approval for ${toolName} (toolUseId=${toolUseId})`);
  });
}

// ─── Query Handler ──────────────────────────────────────────────────────────

/**
 * Execute an Agent SDK query and stream results back as NDJSON events.
 *
 * SDK → StreamEvent mapping:
 *   SDKPartialAssistantMessage (stream_event)
 *     → content_block_delta + text_delta     → { type: 'text', text: delta }
 *     → content_block_start + tool_use       → { type: 'tool_use', toolName, toolInput }
 *   SDKAssistantMessage (assistant)
 *     → tool_result content blocks           → { type: 'tool_result', toolResult }
 *   SDKResultMessage (result)                → { type: 'done', sessionId, costUsd }
 *   Error                                    → { type: 'error', error, errorType }
 */
async function handleQuery(cmd) {
  const { id, prompt, nodeId, systemPrompt, mcpServers, allowedTools, resume, cwd, canvasPath } = cmd;

  // If this node already has an active query, abort it first
  const existing = activeQueries.get(nodeId);
  if (existing) {
    existing.controller.abort();
    if (existing.queryObj?.close) existing.queryObj.close();
    activeQueries.delete(nodeId);
  }

  const controller = new AbortController();
  const entry = { controller, queryObj: null };
  activeQueries.set(nodeId, entry);

  try {
    // Build SDK query options using native SDK parameters
    const queryOpts = {
      prompt,
      options: {
        abortController: controller,
        includePartialMessages: true,
        permissionMode: 'default',
        // H-3 fix: Safety limit to prevent unbounded agent loops (cost + security)
        maxTurns: 25,
        // GDR-P0-4 fix: SDK v0.2.68+ silently injects effort:medium,
        // breaking agentic tool-use workflows (Issue #214).
        // Must explicitly set effort:high to restore proper tool-use behavior.
        effort: 'high',
        // Enable adaptive extended thinking (Opus 4.6+ / Sonnet 4.6+).
        // SDK dynamically allocates thinking tokens based on task complexity.
        thinking: { type: 'adaptive' },
        // canUseTool — SDK dedicated permission handler (sdk.d.ts:126-168).
        // audit-2026-04-07/p0-1: real permission gating, replacing the prior
        // "auto-allow everything" stub. Behavior:
        //   - MCP backend tools (our own backend): allow
        //   - Read-only SDK tools (Read/Glob/Grep/LS/TodoRead): allow
        //   - High-risk SDK tools (Bash/Write/WebFetch/...): prompt user
        //   - Anything else (unknown): deny by default (fail-secure)
        // SDK v0.2.79 Zod validation requires `updatedInput` even in allow.
        canUseTool: async (toolName, input, _options) => {
          // 1) MCP backend tools — trusted, our own backend at localhost:8001
          if (MCP_TOOLS.has(toolName) || toolName.startsWith('mcp__')) {
            return { behavior: 'allow', updatedInput: input };
          }

          // 2) Read-only SDK tools — safe to auto-allow
          if (SAFE_READONLY_SDK_TOOLS.has(toolName)) {
            return { behavior: 'allow', updatedInput: input };
          }

          // 3) High-risk SDK tools — require user approval via the permission
          // pipeline. Frontend permission card is already wired (chat-store.ts
          // approveToolCall/denyToolCall + claude-engine.ts sendPermissionResponse).
          if (HIGH_RISK_SDK_TOOLS.has(toolName)) {
            const decision = await requestUserApproval(toolName, input, nodeId, id);
            if (decision === 'allow') {
              log(`[Permission] User approved ${toolName}`);
              return { behavior: 'allow', updatedInput: input };
            }
            log(`[Permission] User denied ${toolName}`);
            return {
              behavior: 'deny',
              message: `User denied ${toolName} via Canvas permission card.`,
            };
          }

          // 4) Unknown tool — fail-secure deny.
          // Surface to the frontend so the user sees what was blocked instead
          // of the agent silently failing on an opaque tool name.
          log(`[Permission] Unknown tool blocked: ${toolName}`);
          return {
            behavior: 'deny',
            message: `Unknown tool '${toolName}' blocked by Canvas sidecar (fail-secure default).`,
          };
        },
        // S29 Phase 3B: PostToolUse hook for BEA 4-dimension extraction.
        // Fires after learning-relevant MCP tool calls (score_answer, record_error).
        // Fire-and-forget POST to backend /api/v1/memory/extract-conversation.
        // Academic basis: Anderson & Krathwohl Bloom Taxonomy + Dialogue-KT (LAK 2025).
        hooks: {
          PostToolUse: [{
            hooks: [async (input) => {
              const toolName = input.tool_name || '';
              if (!BEA_EXTRACTION_TOOLS.has(toolName)) {
                return { continue: true };
              }
              // Fire-and-forget: extract learning signals from tool interaction
              const backendUrl = process.env.CANVAS_BACKEND_URL || 'http://localhost:8001';
              const observerToken = process.env.CANVAS_OBSERVER_TOKEN || '';
              const inputSummary = JSON.stringify(input.tool_input || {}).slice(0, 500);
              const responseSummary = JSON.stringify(input.tool_response || {}).slice(0, 1000);
              fetch(`${backendUrl}/api/v1/memory/extract-conversation`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  // audit-2026-04-07/p0-2: opt-in shared-secret auth.
                  // Empty token = open mode (T1 single-user). Backend
                  // _require_observer_token enforces only when its env is set.
                  'X-Canvas-Observer-Token': observerToken,
                },
                body: JSON.stringify({
                  node_id: nodeId,
                  session_id: input.session_id || '',
                  messages: [
                    { role: 'user', content: `[Tool: ${toolName}] ${inputSummary}` },
                    { role: 'assistant', content: `[Result] ${responseSummary}` },
                  ],
                  // audit-2026-04-07/p0-2: canvasPath is the relative path
                  // (e.g. "数学/微积分.canvas"), passed by frontend chat-store
                  // from canvas-store. Backend derives the real subject +
                  // canvas group_id from this instead of hard-coded cs188.
                  canvas_path: canvasPath || null,
                }),
                signal: AbortSignal.timeout(30000),
              }).then(r => {
                if (r.ok) log(`[PostToolUse] BEA extraction for ${toolName}: OK`);
                else log(`[PostToolUse] BEA extraction failed: HTTP ${r.status}`);
              }).catch(err => {
                log(`[PostToolUse] BEA extraction error (non-fatal): ${err.message || err}`);
              });
              return { continue: true };
            }],
          }],
        },
      },
    };

    // systemPrompt: SDK native option (string or preset object)
    if (systemPrompt) {
      queryOpts.options.systemPrompt = {
        type: 'preset',
        preset: 'claude_code',
        append: systemPrompt,
      };
    }

    // Session resume
    if (resume) {
      queryOpts.options.resume = resume;
    }

    // Working directory (F4: cwd = vaultPath)
    if (cwd) {
      queryOpts.options.cwd = cwd;
    }

    // MCP servers (backend at http://localhost:8001/mcp)
    if (mcpServers && Object.keys(mcpServers).length > 0) {
      queryOpts.options.mcpServers = mcpServers;
    }

    // Tool allow list
    if (allowedTools && allowedTools.length > 0) {
      queryOpts.options.allowedTools = allowedTools;
    }

    log(`Query ${id} started for node ${nodeId}${resume ? ` (resume: ${resume})` : ''}`);

    // Execute query — returns a Query object (AsyncGenerator + methods)
    const queryResult = query(queryOpts);
    entry.queryObj = queryResult;

    // Track emitted tool_use block IDs to deduplicate across partial messages
    const emittedToolIds = new Set();

    // Learning Observer: track if record_learning_memory was called this turn
    let learningRecorded = false;
    const collectedTexts = [];  // collect assistant text for fallback extraction

    for await (const msg of queryResult) {
      // ── stream_event: Real-time text streaming via BetaRawMessageStreamEvent ──
      if (msg.type === 'stream_event') {
        const event = msg.event;
        if (!event) continue;

        // Text delta: emit incremental text for real-time UI rendering
        if (event.type === 'content_block_delta' && event.delta?.type === 'text_delta') {
          emit({ id, type: 'text', text: event.delta.text });
          collectedTexts.push(event.delta.text);
        }

        // Tool use start: emit when a tool call begins
        if (event.type === 'content_block_start' && event.content_block?.type === 'tool_use') {
          const block = event.content_block;
          const toolId = block.id || `tool_${emittedToolIds.size}`;
          if (!emittedToolIds.has(toolId)) {
            emittedToolIds.add(toolId);
            emit({
              id,
              type: 'tool_use',
              toolName: block.name,
              toolInput: block.input || {},
            });
            // Learning Observer: track if memory recording tool was called
            if (block.name === 'record_learning_memory' || block.name === 'record_error') {
              learningRecorded = true;
            }
          }
        }
        continue;
      }

      // ── assistant: Complete assistant message (contains tool results) ──
      if (msg.type === 'assistant') {
        const content = msg.message?.content;
        if (!Array.isArray(content)) continue;

        // Extract tool results from complete messages
        for (const block of content) {
          if (block.type === 'tool_result') {
            const resultText = typeof block.content === 'string'
              ? block.content
              : JSON.stringify(block.content);
            emit({ id, type: 'tool_result', toolResult: resultText });
          }
          // Emit tool_use from complete messages (for non-streaming fallback)
          if (block.type === 'tool_use') {
            const toolId = block.id || `tool_${emittedToolIds.size}`;
            if (!emittedToolIds.has(toolId)) {
              emittedToolIds.add(toolId);
              emit({
                id,
                type: 'tool_use',
                toolName: block.name,
                toolInput: block.input || {},
              });
            }
          }
        }
        continue;
      }

      // ── user: Tool execution results fed back to Claude (internal to SDK) ──
      if (msg.type === 'user') {
        // Extract tool results from user messages (SDK feeds tool results back)
        if (msg.tool_use_result) {
          const resultText = typeof msg.tool_use_result === 'string'
            ? msg.tool_use_result
            : JSON.stringify(msg.tool_use_result);
          emit({ id, type: 'tool_result', toolResult: resultText });
        }
        continue;
      }

      // ── result: Final result with session_id and cost ──
      if (msg.type === 'result') {
        const errorType = msg.subtype === 'success' ? undefined : msg.subtype;

        // Learning Observer fallback: if no memory tool was called this turn,
        // send conversation to backend for Ollama-based extraction (fire-and-forget)
        if (!learningRecorded && msg.subtype === 'success' && collectedTexts.length > 0) {
          const backendUrl = process.env.CANVAS_BACKEND_URL || 'http://localhost:8001';
          const observerToken = process.env.CANVAS_OBSERVER_TOKEN || '';
          fetch(`${backendUrl}/api/v1/memory/extract-conversation`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              // audit-2026-04-07/p0-2: opt-in shared-secret auth (see top of file).
              'X-Canvas-Observer-Token': observerToken,
            },
            body: JSON.stringify({
              node_id: nodeId,
              session_id: msg.session_id || '',
              messages: [
                { role: 'user', content: prompt },
                { role: 'assistant', content: collectedTexts.join('') },
              ],
              // audit-2026-04-07/p0-2: forward canvas_path so backend can
              // resolve the real Graphiti group_id (subject:canvasName) instead
              // of falling back to the hard-coded cs188 default.
              canvas_path: canvasPath || null,
            }),
            signal: AbortSignal.timeout(30000),
          }).then(r => {
            if (r.ok) log(`[Observer] Fallback extraction for ${nodeId}: OK`);
            else log(`[Observer] Fallback extraction failed: HTTP ${r.status}`);
          }).catch(err => {
            log(`[Observer] Fallback extraction error (non-fatal): ${err.message || err}`);
          });
        }

        emit({
          id,
          type: 'done',
          sessionId: msg.session_id,
          costUsd: msg.total_cost_usd,
          isError: msg.is_error,
          errorType,
        });
        continue;
      }

      // ── system: Init (slash_commands list), compact_boundary, etc. ──
      if (msg.type === 'system') {
        emit({
          id,
          type: 'system',
          subtype: msg.subtype || '',
          sessionId: msg.session_id,
          slashCommands: msg.slash_commands,
          compactMetadata: msg.compact_metadata,
        });
        continue;
      }

      // ── rate_limit: SDK emits this for rate limit events ──
      if (msg.type === 'rate_limit') {
        emit({
          id,
          type: 'error',
          error: 'Rate limit reached. Please try again later.',
          errorType: 'rate_limited',
          retryAfterSec: msg.retryAfterMs ? Math.ceil(msg.retryAfterMs / 1000) : undefined,
        });
        continue;
      }

      // Unknown type — log for debugging
      log(`Unknown SDK message type: ${msg.type}`);
    }

    log(`Query ${id} completed`);
  } catch (err) {
    // Don't emit error for AbortError (intentional cancellation)
    if (err.name === 'AbortError' || controller.signal.aborted) {
      log(`Query ${id} cancelled`);
      return;
    }

    const errorMsg = err.message || String(err);
    let errorType = 'crash';
    let retryAfterSec;

    // Classify error to match EngineErrorType
    // SDK may set error field on SDKAssistantMessage: 'authentication_failed' | 'billing_error' | 'rate_limit' etc.
    if (/auth|401|credentials|login|not.?logged|authentication_failed/i.test(errorMsg)) {
      errorType = 'auth_failed';
    } else if (/rate.?limit|429|too many requests|quota.*exceeded|rate_limit_error|billing_error/i.test(errorMsg)) {
      errorType = 'rate_limited';
      const headerMatch = errorMsg.match(/retry[- ]?after[:\s]+(\d+)/i);
      const naturalMatch = errorMsg.match(/try again in (\d+)\s*(second|minute|hour)/i);
      if (headerMatch) {
        retryAfterSec = parseInt(headerMatch[1], 10);
      } else if (naturalMatch) {
        retryAfterSec = parseInt(naturalMatch[1], 10);
        if (naturalMatch[2].startsWith('minute')) retryAfterSec *= 60;
        if (naturalMatch[2].startsWith('hour')) retryAfterSec *= 3600;
      }
    } else if (/not.?found|ENOENT|not.?installed|cannot find/i.test(errorMsg)) {
      errorType = 'not_installed';
    } else if (/spawn|failed to start/i.test(errorMsg)) {
      errorType = 'spawn_failed';
    }

    emit({ id, type: 'error', error: errorMsg, errorType, retryAfterSec });
    log(`Query ${id} error: [${errorType}] ${errorMsg}`);
  } finally {
    activeQueries.delete(nodeId);
  }
}

// ─── Stdin Command Router ───────────────────────────────────────────────────

const rl = createInterface({
  input: process.stdin,
  crlfDelay: Infinity,  // Handle both \n and \r\n (Windows compatibility)
});

rl.on('line', (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let cmd;
  try {
    cmd = JSON.parse(trimmed);
  } catch {
    emit({ id: null, type: 'error', error: 'Invalid JSON on stdin', errorType: 'crash' });
    return;
  }

  const { id } = cmd;

  switch (cmd.cmd) {
    case 'ping':
      emit({ id, type: 'pong' });
      break;

    case 'shutdown':
      log('Shutdown requested');
      for (const [, entry] of activeQueries) {
        entry.controller.abort();
        if (entry.queryObj?.close) entry.queryObj.close();
      }
      activeQueries.clear();
      // audit-2026-04-07/p0-1: drain pending permission prompts so the
      // canUseTool promises resolve and the SDK loop can unwind cleanly.
      for (const [toolUseId, pending] of pendingPermissions) {
        clearTimeout(pending.timer);
        pending.resolve('deny');
        pendingPermissions.delete(toolUseId);
      }
      emit({ id, type: 'ack' });
      setTimeout(() => process.exit(0), 100);
      break;

    case 'abort': {
      const entry = activeQueries.get(cmd.nodeId);
      if (entry) {
        entry.controller.abort();
        if (entry.queryObj?.close) entry.queryObj.close();
        activeQueries.delete(cmd.nodeId);
        log(`Aborted query for node ${cmd.nodeId}`);
      }
      // audit-2026-04-07/p0-1: deny any in-flight permission prompts for this
      // node so the SDK loop unwinds instead of hanging on a stale promise.
      for (const [toolUseId, pending] of pendingPermissions) {
        if (pending.nodeId === cmd.nodeId) {
          clearTimeout(pending.timer);
          pendingPermissions.delete(toolUseId);
          pending.resolve('deny');
        }
      }
      emit({ id, type: 'ack' });
      break;
    }

    case 'query':
      handleQuery(cmd).catch((err) => {
        emit({ id, type: 'error', error: err.message || String(err), errorType: 'crash' });
        log(`Unhandled query error: ${err.message}`);
      });
      break;

    case 'permission_response': {
      // audit-2026-04-07/p0-1: user approve/deny decision routed back from frontend.
      // Look up the pending request by toolUseId and resolve its promise.
      const { toolUseId, decision } = cmd;
      const pending = pendingPermissions.get(toolUseId);
      if (!pending) {
        log(`[Permission] No pending request for toolUseId=${toolUseId} (already timed out?)`);
        emit({ id, type: 'ack' });
        break;
      }
      clearTimeout(pending.timer);
      pendingPermissions.delete(toolUseId);
      const normalized = decision === 'allow' ? 'allow' : 'deny';
      pending.resolve(normalized);
      emit({ id, type: 'ack' });
      break;
    }

    default:
      emit({ id, type: 'error', error: `Unknown command: ${cmd.cmd}`, errorType: 'crash' });
      break;
  }
});

// When stdin closes, parent process is gone — exit immediately
rl.on('close', () => {
  log('stdin closed — parent gone. Exiting.');
  for (const [, entry] of activeQueries) {
    entry.controller.abort();
    if (entry.queryObj?.close) entry.queryObj.close();
  }
  // audit-2026-04-07/p0-1: clear permission timers so the process can exit.
  for (const [, pending] of pendingPermissions) {
    clearTimeout(pending.timer);
    pending.resolve('deny');
  }
  pendingPermissions.clear();
  process.exit(0);
});

// ─── Global Error Handlers ──────────────────────────────────────────────────

process.on('uncaughtException', (err) => {
  log(`FATAL uncaught exception: ${err.stack || err.message}`);
  emit({ id: null, type: 'error', error: `Sidecar crash: ${err.message}`, errorType: 'crash' });
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  log(`Unhandled rejection: ${reason}`);
});

// ─── Startup ────────────────────────────────────────────────────────────────

log('Canvas Learning Sidecar v1.0.0 started');
emit({ id: null, type: 'ready' });
