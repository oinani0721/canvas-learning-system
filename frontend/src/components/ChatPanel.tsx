/**
 * ChatPanel — AI conversation panel with streaming and persistent history.
 * Story 3-3: Chat Panel UI + Streaming
 * Story 3-9: Engine Fallback (engine status indicator)
 * Story 3-10: Quota Management (QuotaExhaustedBanner)
 * Story 3-11: Crash Recovery (RecoveryBanner)
 * Story 4-1: Edge Dialog Trigger — edge mode rendering
 * Story 4-2: Edge Dialog Agent Reasoning — edge-specific system prompt
 *
 * Features:
 * - Per-node conversation history persisted in Dexie (AC-4)
 * - Real-time streaming with typewriter effect via ClaudeEngine (AC-2)
 * - Markdown rendering for AI responses via react-markdown (AC-3)
 * - Auto-scroll to latest message
 * - Lazy loading: initial 50 messages, IntersectionObserver for older (AC-4)
 * - 2s first-token timeout with "Thinking..." indicator (AC-6)
 * - Input bar with Enter/Shift+Enter/Escape shortcuts (AC-5)
 * - Text selection toolbar for Add Tip / Pull to Node
 * - Engine status indicator (Claude Code vs API Key) (Story 3-9)
 * - Quota exhaustion banner with countdown + degradation options (Story 3-10)
 * - Crash recovery banner with auto/manual retry status (Story 3-11)
 * - Edge dialog mode: header shows "A <-> B", edge-specific system prompt (Story 4-1/4-2)
 *
 * Callers:
 * - App.tsx renders this in the right sidebar when a node or edge is selected
 *
 * Wiring:
 * - useChatStore (Zustand) — all message state + streaming actions
 * - MessageBubble — individual message rendering
 * - InputBar — text input with keyboard shortcuts
 * - StreamingIndicator — animated streaming feedback
 * - SelectionToolbar — text selection actions
 * - TipsList — displays saved tips for the node
 * - EngineStatusIndicator — shows active engine (Story 3-9)
 * - QuotaExhaustedBanner — quota degradation UI (Story 3-10)
 * - RecoveryBanner — crash recovery UI (Story 3-11)
 */

import { useEffect, useRef, useCallback } from 'react';
import type { Node } from '@xyflow/react';
import { useChatStore, type EdgeContext } from '../stores/chat-store';
import { MessageBubble } from './chat/MessageBubble';
import { InputBar } from './chat/InputBar';
import { StreamingIndicator } from './chat/StreamingIndicator';
import { SelectionToolbar } from './chat/SelectionToolbar';
import { TipsList } from './chat/TipsList';
import { EngineStatusIndicator } from './chat/EngineStatusIndicator';
import { QuotaExhaustedBanner } from './chat/QuotaExhaustedBanner';
import { RecoveryBanner } from './chat/RecoveryBanner';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface ChatPanelProps {
  /** Selected node (for normal mode). Null when in edge mode. */
  selectedNode?: Node | null;
  /** Edge context (for edge mode). Null when in normal mode. */
  edgeContext?: EdgeContext | null;
  onOpenSettings?: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

export function ChatPanel({ selectedNode, edgeContext, onOpenSettings }: ChatPanelProps) {
  // Story 4-1/4-2: Determine mode from props
  const chatMode = useChatStore((s) => s.chatMode);
  const currentEdge = useChatStore((s) => s.currentEdge);
  const isEdgeMode = chatMode === 'edge' && currentEdge !== null;

  // Derive display values based on mode
  const nodeId = isEdgeMode
    ? `edge_${currentEdge!.edgeId}`
    : selectedNode?.id ?? '';
  const displayTitle = isEdgeMode
    ? `${currentEdge!.sourceNodeName} \u2194 ${currentEdge!.targetNodeName}`
    : ((selectedNode?.data as Record<string, unknown>)?.title as string) || 'Untitled';

  // ── Store bindings ────────────────────────────────────────────────────

  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const engineUnavailable = useChatStore((s) => s.engineUnavailable);
  const waitingForFirstToken = useChatStore((s) => s.waitingForFirstToken);
  const hasMore = useChatStore((s) => s.hasMore);
  const switchNode = useChatStore((s) => s.switchNode);
  const switchToEdge = useChatStore((s) => s.switchToEdge);
  const loadMore = useChatStore((s) => s.loadMore);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const clearHistory = useChatStore((s) => s.clearHistory);
  const quotaStatus = useChatStore((s) => s.quotaStatus);

  // ── Refs ──────────────────────────────────────────────────────────────

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // ── Switch node/edge on selection change ──────────────────────────────

  useEffect(() => {
    if (edgeContext) {
      switchToEdge(edgeContext);
    } else if (selectedNode) {
      switchNode(selectedNode.id);
    }
  }, [edgeContext, selectedNode, switchNode, switchToEdge]);

  // ── Auto-scroll to bottom on new messages ─────────────────────────────

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Lazy loading: IntersectionObserver on top sentinel ────────────────

  useEffect(() => {
    const sentinel = sentinelRef.current;
    const container = scrollContainerRef.current;
    if (!sentinel || !container || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry && entry.isIntersecting) {
          // Save scroll position before loading
          const prevScrollHeight = container.scrollHeight;
          loadMore().then(() => {
            // Restore scroll position after prepending older messages
            const newScrollHeight = container.scrollHeight;
            container.scrollTop = newScrollHeight - prevScrollHeight;
          });
        }
      },
      { root: container, threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadMore]);

  // ── Send handler ──────────────────────────────────────────────────────

  const handleSend = useCallback(
    (text: string) => {
      sendMessage(text, displayTitle);
    },
    [sendMessage, displayTitle],
  );

  // ── Clear handler ─────────────────────────────────────────────────────

  const handleClear = useCallback(() => {
    clearHistory();
  }, [clearHistory]);

  // ── Open settings handler (for quota degradation) ─────────────────────

  const handleOpenSettings = useCallback(() => {
    if (onOpenSettings) {
      onOpenSettings();
    }
  }, [onOpenSettings]);

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full">
      {/* Header — Story 3-9: Engine status indicator, Story 4-1: Edge mode header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-sm font-medium text-gray-700 truncate">
            {isEdgeMode ? (
              <span title="Edge Dialog">
                <span className="text-blue-500">Edge:</span> {displayTitle}
              </span>
            ) : (
              <>Chat: {displayTitle}</>
            )}
          </h3>
          <EngineStatusIndicator />
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors shrink-0 ml-2"
            title="Clear chat history"
          >
            Clear
          </button>
        )}
      </div>

      {/* Engine unavailable banner */}
      {engineUnavailable && (
        <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 shrink-0">
          <p className="text-xs text-amber-700">
            Claude Code not available. Run via Tauri desktop app to enable AI chat.
          </p>
        </div>
      )}

      {/* Story 3-11: Crash recovery banner */}
      <RecoveryBanner nodeTitle={displayTitle} />

      {/* Story 3-10: Quota exhaustion banner */}
      {quotaStatus === 'exhausted' && (
        <QuotaExhaustedBanner onOpenSettings={handleOpenSettings} />
      )}

      {/* Messages list */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-3 py-3 space-y-3"
      >
        {/* Lazy loading sentinel — triggers loadMore when visible */}
        {hasMore && (
          <div ref={sentinelRef} className="flex justify-center py-2">
            <span className="text-xs text-gray-300">Loading older messages...</span>
          </div>
        )}

        {/* Empty state — Story 4-1: different prompt for edge mode */}
        {messages.length === 0 && !hasMore && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-400 text-center">
              {isEdgeMode
                ? `Discuss the relationship between "${currentEdge!.sourceNodeName}" and "${currentEdge!.targetNodeName}"`
                : <>Ask anything about &quot;{displayTitle}&quot;</>
              }
            </p>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming indicator */}
        {isStreaming && (
          <StreamingIndicator waitingForFirstToken={waitingForFirstToken} />
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Tips section (collapsible, below messages) — only in node mode */}
      {!isEdgeMode && (
        <div className="shrink-0 border-t border-gray-100 px-3 py-2 max-h-40 overflow-y-auto">
          <TipsList nodeId={nodeId} />
        </div>
      )}

      {/* Input bar — disabled when quota exhausted (Story 3-10 AC-4) */}
      <InputBar
        isStreaming={isStreaming}
        engineUnavailable={engineUnavailable}
        nodeTitle={displayTitle}
        onSend={handleSend}
        quotaExhausted={quotaStatus === 'exhausted'}
      />

      {/* Text selection toolbar (floating, appears on text select) — only in node mode */}
      {!isEdgeMode && <SelectionToolbar nodeId={nodeId} />}
    </div>
  );
}
