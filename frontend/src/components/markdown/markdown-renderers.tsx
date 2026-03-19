/**
 * Shared Markdown rendering utilities for KnowledgeNode and MessageBubble.
 *
 * Extracts wiki-link preprocessing and custom ReactMarkdown components so both
 * node content (view mode) and chat messages render identically.
 *
 * Callers:
 * - KnowledgeNode.tsx (node content view mode)
 * - MessageBubble.tsx (assistant chat messages)
 */

import { useCallback } from 'react';
import { openInObsidian, parseWikiLink } from '../../services/obsidian-link';

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
export function preprocessWikiLinks(content: string): string {
  return content.replace(WIKI_LINK_RE, (_match, linkText: string) => {
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
 * Regular links render as normal anchor tags with stopPropagation to prevent
 * parent onClick (e.g. KnowledgeNode entering edit mode on link click).
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

      const encoded = href.replace('wiki-link://', '');
      const linkText = decodeURIComponent(encoded);
      const { filePath, heading } = parseWikiLink(linkText);

      const result = await openInObsidian(filePath, heading);

      if (!result.success && result.copyPath) {
        try {
          await navigator.clipboard.writeText(result.copyPath);
        } catch {
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
        <span className="text-xs opacity-70">{'[['}</span>
        {children}
        <span className="text-xs opacity-70">{']]'}</span>
      </button>
    );
  }

  // Regular link: render normally, stopPropagation to avoid triggering node edit mode
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
    >
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
export const markdownComponents = {
  a: WikiLinkAnchor,
} as const;
