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
 * SDK API (v0.2.74):
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

// ─── IPC Helpers ────────────────────────────────────────────────────────────

/** Write a single JSON line to stdout (NDJSON protocol). */
function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

/** Write a log line to stderr (never stdout). */
function log(...args) {
  process.stderr.write(`[sidecar] ${args.join(' ')}\n`);
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
  const { id, prompt, nodeId, systemPrompt, mcpServers, allowedTools, resume, cwd } = cmd;

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
        permissionMode: 'bypassPermissions',
        allowDangerouslySkipPermissions: true,
        // H-3 fix: Safety limit to prevent unbounded agent loops (cost + security)
        maxTurns: 25,
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
          fetch(`${backendUrl}/api/v1/memory/extract-conversation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              node_id: nodeId,
              session_id: msg.session_id || '',
              messages: [
                { role: 'user', content: prompt },
                { role: 'assistant', content: collectedTexts.join('') },
              ],
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

      // ── system: Init and compact boundary — no UI action ──
      if (msg.type === 'system') {
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
      emit({ id, type: 'ack' });
      break;
    }

    case 'query':
      handleQuery(cmd).catch((err) => {
        emit({ id, type: 'error', error: err.message || String(err), errorType: 'crash' });
        log(`Unhandled query error: ${err.message}`);
      });
      break;

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
