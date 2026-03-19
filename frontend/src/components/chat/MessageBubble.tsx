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

import { useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import type { ChatMessage } from '../../services/dexie-db';
import { openInObsidian, parseWikiLink } from '../../services/obsidian-link';

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
// Wiki-link preprocessing
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Regex to match [[wiki-links]] including optional #heading.
 * Matches: [[file]], [[file#heading]], [[path/to/file#heading]]
 * Does NOT match already-escaped links inside code blocks (handled by markdown).
 */
const WIKI_LINK_RE = /\[\[([^\]]+)\]\]/g;

/**
 * Pre-process message content to convert [[wiki-links]] into markdown links.
 * Converts [[file#section]] -> [file#section](wiki-link://file#section)
 *
 * Uses a custom `wiki-link://` protocol as a marker so we can intercept clicks
 * in the ReactMarkdown link renderer without conflicting with real URLs.
 */
function preprocessWikiLinks(content: string): string {
  return content.replace(WIKI_LINK_RE, (_match, linkText: string) => {
    // Encode the link text for URL safety
    const encoded = encodeURIComponent(linkText);
    return `[${linkText}](wiki-link://${encoded})`;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// Wiki-link click handler component
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Custom link renderer for ReactMarkdown.
 * Intercepts wiki-link:// protocol links and opens them in Obsidian.
 * Regular links render as normal anchor tags.
 */
function WikiLinkAnchor({
  href,
  children,
}: {
  href?: string;
  children?: React.ReactNode;
}) {
  const handleWikiLinkClick = useCallback(
    async (event: React.MouseEvent) => {
      if (!href?.startsWith('wiki-link://')) return;

      event.preventDefault();
      event.stopPropagation();

      // Decode the link text from the URL
      const encoded = href.replace('wiki-link://', '');
      const linkText = decodeURIComponent(encoded);
      const { filePath, heading } = parseWikiLink(linkText);

      const result = await openInObsidian(filePath, heading);

      if (!result.success && result.copyPath) {
        // Attempt to copy path to clipboard as fallback
        try {
          await navigator.clipboard.writeText(result.copyPath);
        } catch {
          // Clipboard API may not be available
          console.warn('[wiki-link] Could not copy path to clipboard:', result.copyPath);
        }
        if (result.error) {
          console.warn('[wiki-link]', result.error);
        }
      }
    },
    [href],
  );

  // Wiki-link: render as styled clickable span
  if (href?.startsWith('wiki-link://')) {
    return (
      <button
        type="button"
        onClick={handleWikiLinkClick}
        className="inline-flex items-center gap-0.5 px-1 py-0 rounded text-blue-500 hover:text-blue-600 hover:bg-blue-50 cursor-pointer transition-colors text-sm font-medium no-underline"
        title="Open in Obsidian"
      >
        <span className="text-xs opacity-70">[[</span>
        {children}
        <span className="text-xs opacity-70">]]</span>
      </button>
    );
  }

  // Regular link: render normally
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ReactMarkdown custom components
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Custom component map for ReactMarkdown.
 * Overrides the `a` tag renderer to handle wiki-links.
 */
const markdownComponents = {
  a: WikiLinkAnchor,
} as const;

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
                rehypePlugins={[rehypeSanitize]}
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
