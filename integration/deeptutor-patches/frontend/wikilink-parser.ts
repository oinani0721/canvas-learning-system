/**
 * Wikilink parser (Day 1 staging).
 *
 * Usage in DeepTutor fork:
 *   Copy to: deeptutor-fork/web/src/lib/wikilink/parser.ts
 *
 * Parses Obsidian-style [[wikilinks]] into structured refs:
 *   [[recursion]]                    → { target: "recursion", display: "recursion" }
 *   [[recursion|递归]]                → { target: "recursion", display: "递归" }
 *   [[原白板/递归]]                   → { target: "原白板/递归", display: "原白板/递归" }
 *   [[原白板/递归#基线条件]]          → { target: "原白板/递归", anchor: "基线条件", display: "..." }
 */

export interface WikilinkRef {
  /** Raw target path/slug, e.g. "recursion" or "原白板/递归" */
  target: string;
  /** Optional anchor (header) inside target, e.g. "基线条件" */
  anchor?: string;
  /** Display text shown to user (defaults to target if no pipe) */
  display: string;
  /** Original raw match including [[]] */
  raw: string;
  /** Position in source string */
  start: number;
  end: number;
}

// Match [[xxx]], [[xxx|display]], [[xxx#anchor]], [[xxx#anchor|display]]
// Excludes nested ]] within target (basic heuristic)
const WIKILINK_RE = /\[\[([^\[\]\|\#]+)(?:#([^\[\]\|]+))?(?:\|([^\[\]]+))?\]\]/g;


export function parseWikilinks(markdown: string): WikilinkRef[] {
  const refs: WikilinkRef[] = [];
  let match: RegExpExecArray | null;

  // Reset lastIndex (regex with /g flag is stateful)
  WIKILINK_RE.lastIndex = 0;

  while ((match = WIKILINK_RE.exec(markdown)) !== null) {
    const [raw, target, anchor, alias] = match;
    refs.push({
      target: target.trim(),
      anchor: anchor?.trim(),
      display: (alias ?? target).trim(),
      raw,
      start: match.index,
      end: match.index + raw.length,
    });
  }
  return refs;
}


/**
 * Extract all unique wikilink targets from markdown.
 * Used for backlink index building (Day 2).
 */
export function extractTargets(markdown: string): string[] {
  const seen = new Set<string>();
  for (const ref of parseWikilinks(markdown)) {
    seen.add(ref.target);
  }
  return Array.from(seen);
}


/**
 * Convert a wikilink to a URL for DeepTutor routing.
 * Default mapping: [[xxx]] → /notes/xxx
 *
 * Override via routePrefix for book-scoped wikilinks:
 *   wikilinkToUrl({ target: "recursion" }, { routePrefix: "/book/123/page" })
 *   → /book/123/page/recursion
 */
export function wikilinkToUrl(ref: WikilinkRef, opts: { routePrefix?: string } = {}): string {
  const prefix = opts.routePrefix ?? "/notes";
  const slug = encodeURIComponent(ref.target);
  const anchor = ref.anchor ? `#${encodeURIComponent(ref.anchor)}` : "";
  return `${prefix}/${slug}${anchor}`;
}
