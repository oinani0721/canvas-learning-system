/**
 * ToolCallCard — Collapsible tool call display with 4-state machine.
 * GDR-P0-2: Claudian-style tool call card in chat conversation flow.
 *
 * States: pending → running → completed | error | blocked
 * References: Claudian ToolCallRenderer, Companion collapsible blocks,
 *             assistant-ui ToolGroup, Vercel AI SDK 3-state model.
 *
 * Callers:
 * - MessageBubble routes tool_use role messages here
 *
 * Wiring:
 * - ChatMessage from dexie-db (toolName, toolCallState, toolInput, content, learningAnnotation)
 */

import { useState } from 'react';
import type { ChatMessage } from '../../services/dexie-db';

// ═══════════════════════════════════════════════════════════════════════════════
// Tool icon mapping — maps tool names to display icons
// ═══════════════════════════════════════════════════════════════════════════════

const TOOL_ICONS: Record<string, string> = {
  search_vault_notes: '🔍',
  read_note: '📄',
  write_note: '✏️',
  record_learning_memory: '🧠',
  record_error: '⚠️',
  generate_question: '❓',
  get_mastery: '📊',
  search_memory: '💾',
  rag_query: '🔍',
};

function getToolIcon(toolName: string): string {
  return TOOL_ICONS[toolName] ?? '🔧';
}

// ═══════════════════════════════════════════════════════════════════════════════
// State display config
// ═══════════════════════════════════════════════════════════════════════════════

const STATE_CONFIG = {
  pending: { label: '等待中...', color: 'text-yellow-400', bgBorder: '' },
  running: { label: '执行中...', color: 'text-blue-400', bgBorder: '' },
  completed: { label: '完成', color: 'text-green-400', bgBorder: '' },
  error: { label: '出错', color: 'text-red-400', bgBorder: '' },
  blocked: { label: '需要确认', color: 'text-yellow-400', bgBorder: 'border border-yellow-400/40' },
} as const;

// ═══════════════════════════════════════════════════════════════════════════════
// Per-tool result rendering — maps tool names to specialized display
// ═══════════════════════════════════════════════════════════════════════════════

function renderToolResult(toolName: string, resultContent: string): React.ReactNode {
  // Try JSON parse for structured results
  let parsed: unknown = null;
  try {
    parsed = JSON.parse(resultContent);
  } catch {
    // Not JSON — render as plain text
  }

  switch (toolName) {
    case 'search_vault_notes':
    case 'rag_query':
    case 'search_memory': {
      // Search results: render as list of note paths
      if (Array.isArray(parsed)) {
        return (
          <div className="mt-1.5 space-y-1">
            {parsed.slice(0, 10).map((item, i) => {
              const path = typeof item === 'string' ? item : (item as Record<string, unknown>).path ?? String(item);
              return (
                <div key={i} className="text-xs text-[#89b4fa] px-2 py-0.5 hover:bg-[#45475a]/30 rounded cursor-pointer truncate">
                  📄 {String(path)}
                </div>
              );
            })}
            {parsed.length > 10 && (
              <div className="text-[10px] text-[#6c7086] px-2">...及其他 {parsed.length - 10} 条结果</div>
            )}
          </div>
        );
      }
      // Fallback: plain text
      return (
        <div className="mt-1.5 px-2.5 py-2 bg-[#181825] rounded-md text-xs text-[#a6adc8] whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
          {resultContent || '(无结果)'}
        </div>
      );
    }

    case 'record_learning_memory':
    case 'record_error': {
      // Memory write: success badge
      return (
        <div className="mt-1.5 flex items-center gap-1.5 px-2 py-1 bg-green-900/20 border border-green-500/20 rounded-md">
          <span className="text-green-400 text-xs">✓</span>
          <span className="text-[11px] text-green-300">已记录到知识图谱</span>
        </div>
      );
    }

    case 'generate_question': {
      // Question preview: render question text
      const questionText = typeof parsed === 'object' && parsed !== null
        ? (parsed as Record<string, unknown>).question ?? resultContent
        : resultContent;
      return (
        <div className="mt-1.5 px-2.5 py-2 bg-[#181825] border-l-2 border-[#cba6f7] rounded-md text-xs text-[#cdd6f4]">
          ❓ {String(questionText).slice(0, 200)}
        </div>
      );
    }

    case 'get_mastery': {
      // Mastery data: render as compact stats
      if (typeof parsed === 'object' && parsed !== null) {
        const p = parsed as Record<string, unknown>;
        return (
          <div className="mt-1.5 flex gap-3 px-2 py-1.5 bg-[#181825] rounded-md text-[11px]">
            {p.proficiency !== undefined && (
              <span className="text-[#a6e3a1]">掌握度: {String(p.proficiency)}</span>
            )}
            {p.retention !== undefined && (
              <span className="text-[#89b4fa]">保留率: {String(p.retention)}</span>
            )}
            {p.review_count !== undefined && (
              <span className="text-[#6c7086]">复习次数: {String(p.review_count)}</span>
            )}
          </div>
        );
      }
      return (
        <div className="mt-1.5 px-2.5 py-2 bg-[#181825] rounded-md text-xs text-[#a6adc8]">
          {resultContent}
        </div>
      );
    }

    default: {
      // Generic: collapsible text/JSON display
      return (
        <div className="mt-1.5 px-2.5 py-2 bg-[#181825] rounded-md text-xs text-[#a6adc8] whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
          {resultContent || '(无输出)'}
        </div>
      );
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ToolCallCard Component
// ═══════════════════════════════════════════════════════════════════════════════

interface ToolCallCardProps {
  message: ChatMessage;
  /** Optional: paired tool_result message for this tool call. */
  resultMessage?: ChatMessage;
  /** Callback when user approves a blocked tool call. */
  onApprove?: (messageId: string) => void;
  /** Callback when user denies a blocked tool call. */
  onDeny?: (messageId: string) => void;
}

export function ToolCallCard({ message, resultMessage, onApprove, onDeny }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toolName = message.toolName ?? 'unknown_tool';
  const state = message.toolCallState ?? 'running';
  const config = STATE_CONFIG[state];
  const icon = getToolIcon(toolName);
  const displayName = toolName.replace(/_/g, ' ');

  // Parse tool input for summary display
  let toolInputSummary: string | null = null;
  if (message.toolInput) {
    try {
      const parsed = JSON.parse(message.toolInput);
      const firstValue = Object.values(parsed)[0];
      if (typeof firstValue === 'string' && firstValue.length < 80) {
        toolInputSummary = firstValue;
      }
    } catch {
      toolInputSummary = null;
    }
  }

  return (
    <div
      className={`rounded-lg bg-[#313244] ${config.bgBorder} overflow-hidden transition-all duration-200`}
      data-tool-state={state}
      data-tool-name={toolName}
    >
      {/* ── Header: always visible (click to toggle expand) ── */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-[#45475a]/50 transition-colors"
        aria-expanded={isExpanded}
        aria-label={`${displayName} — ${config.label}`}
      >
        <span className="text-sm flex-shrink-0">{icon}</span>

        <span className="text-xs font-semibold text-[#cdd6f4] truncate">
          {displayName}
        </span>

        {toolInputSummary && state !== 'pending' && (
          <span className="text-[10px] text-[#6c7086] truncate max-w-[120px]">
            &quot;{toolInputSummary}&quot;
          </span>
        )}

        <span className={`text-[10px] ml-auto flex-shrink-0 ${config.color}`}>
          {state === 'pending' && '⏳ '}
          {state === 'running' && '⏳ '}
          {state === 'completed' && '✅ '}
          {state === 'error' && '❌ '}
          {state === 'blocked' && '⚠️ '}
          {config.label}
        </span>

        <span className={`text-[10px] text-[#6c7086] transition-transform duration-150 ${isExpanded ? 'rotate-180' : ''}`}>
          ▾
        </span>
      </button>

      {/* ── Expanded content ── */}
      {isExpanded && (
        <div className="px-3 pb-2.5 border-t border-[#45475a]/50">
          {message.toolInput && (
            <div className="mt-1.5 text-[10px] text-[#6c7086]">
              <span className="font-medium">参数: </span>
              <code className="text-[#89b4fa] break-all">{message.toolInput}</code>
            </div>
          )}

          {state === 'completed' && resultMessage?.content &&
            renderToolResult(toolName, resultMessage.content)
          }

          {state === 'error' && resultMessage?.content && (
            <div className="mt-1.5 px-2.5 py-2 bg-red-900/20 border border-red-500/30 rounded-md text-xs text-red-300">
              {resultMessage.content}
            </div>
          )}
        </div>
      )}

      {/* ── Blocked state: approval buttons ── */}
      {state === 'blocked' && (
        <div className="px-3 pb-2.5 border-t border-yellow-400/20">
          <p className="text-[11px] text-[#a6adc8] mt-1.5 mb-2">
            {message.content || `${displayName} 需要你的确认才能执行`}
          </p>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => onDeny?.(message.id)}
              className="px-3 py-1 text-[11px] bg-[#45475a] text-[#cdd6f4] rounded-md hover:bg-[#585b70] transition-colors"
            >
              拒绝
            </button>
            <button
              onClick={() => onApprove?.(message.id)}
              className="px-3 py-1 text-[11px] bg-[#a6e3a1] text-[#1e1e2e] font-semibold rounded-md hover:bg-[#94e2d5] transition-colors"
            >
              允许
            </button>
          </div>
        </div>
      )}

      {/* ── Learning annotation (GDR unique differentiator) ── */}
      {message.learningAnnotation && (
        <div className="px-3 pb-2 text-[10px] text-[#fab387]">
          📝 {message.learningAnnotation}
        </div>
      )}
    </div>
  );
}
