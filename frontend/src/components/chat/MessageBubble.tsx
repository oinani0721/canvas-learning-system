/**
 * MessageBubble — Single chat message display with Markdown rendering.
 * Story 3-3 AC-1 / AC-3
 * Scene 2.9: [[wiki-link]] clickable rendering
 *
 * Layout:
 * - User messages: right-aligned, accent-colored bubble
 * - Assistant messages: left-aligned, light bubble with Markdown rendering
 * - Error messages: left-aligned, red-tinted bubble
 * - Relative timestamp shown below each message
 * - [[wiki-links]] rendered as clickable links that open in Obsidian
 *
 * Callers:
 * - ChatPanel maps over messages and renders one MessageBubble per message
 *
 * Wiring:
 * - react-markdown for Markdown/code rendering (already in dependencies)
 * - ChatMessage type from dexie-db
 * - obsidian-link service for [[wiki-link]] click handling
 */

import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import type { ChatMessage } from '../../services/dexie-db';
import { preprocessWikiLinks, markdownComponents, remarkPlugins, rehypeExtraPlugins } from '../markdown/markdown-renderers';

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Format an ISO timestamp to a human-friendly relative time string.
 * "just now" / "3m ago" / "2h ago" / locale date for older.
 */
function formatRelativeTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;

  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// MessageBubble Component
// ═══════════════════════════════════════════════════════════════════════════════

export function MessageBubble({ message }: MessageBubbleProps) {
  const timestamp = formatRelativeTime(message.createdAt);

  // User message: right-aligned, accent bubble
  if (message.role === 'user') {
    return (
      <div className="flex justify-end" data-chat-message="user">
        <div className="max-w-[85%]">
          <div className="px-3 py-2 bg-blue-500 text-white text-sm rounded-2xl rounded-br-md">
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
          <div className="text-[10px] text-gray-400 text-right mt-0.5 pr-1">
            {timestamp}
          </div>
        </div>
      </div>
    );
  }

  // Error message: left-aligned, red bubble
  if (message.role === 'error') {
    return (
      <div className="flex justify-start" data-chat-message="error">
        <div className="max-w-[85%]">
          <div className="px-3 py-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded-2xl rounded-bl-md">
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
          <div className="text-[10px] text-gray-400 mt-0.5 pl-1">
            {timestamp}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message: left-aligned, light bubble with Markdown + wiki-link rendering
  const processedContent = message.content ? preprocessWikiLinks(message.content) : '';

  return (
    <div className="flex justify-start" data-chat-message="assistant">
      <div className="max-w-[85%]">
        <div className="px-3 py-2 bg-gray-100 text-gray-900 text-sm rounded-2xl rounded-bl-md">
          {processedContent ? (
            <div className="prose prose-sm prose-gray max-w-none break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown
                remarkPlugins={remarkPlugins}
                rehypePlugins={[...rehypeExtraPlugins, rehypeSanitize]}
                components={markdownComponents}
              >
                {processedContent}
              </ReactMarkdown>
            </div>
          ) : (
            <span className="text-gray-400 italic">...</span>
          )}
        </div>
        <div className="text-[10px] text-gray-400 mt-0.5 pl-1">
          {timestamp}
        </div>
      </div>
    </div>
  );
}
