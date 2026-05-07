/**
 * Remark plugin: parse [[wikilinks]] in markdown AST (Day 1 staging).
 *
 * Usage in DeepTutor fork:
 *   1. Copy to: deeptutor-fork/web/src/lib/wikilink/remark-wikilink-plugin.ts
 *   2. Register in RichMarkdownRenderer.tsx:
 *      import { remarkWikilink } from "@/lib/wikilink/remark-wikilink-plugin";
 *      <ReactMarkdown remarkPlugins={[remarkGfm, remarkWikilink]}>
 *
 * Transforms [[xxx]] text nodes into <a href="/notes/xxx" data-wikilink="true">xxx</a>.
 * Preserves position info so RichMarkdownRenderer can render custom WikilinkLink component.
 */

import type { Plugin } from "unified";
import type { Root, Text, Link } from "mdast";
import { visit } from "unist-util-visit";

import { parseWikilinks, wikilinkToUrl } from "./parser";


export interface RemarkWikilinkOptions {
  /** Route prefix for wikilink URLs. Default: "/notes" */
  routePrefix?: string;
  /** Custom URL builder (overrides routePrefix) */
  urlBuilder?: (target: string, anchor?: string) => string;
}


export const remarkWikilink: Plugin<[RemarkWikilinkOptions?], Root> = (options = {}) => {
  return (tree) => {
    visit(tree, "text", (node: Text, index, parent) => {
      if (!parent || index === undefined) return;

      const refs = parseWikilinks(node.value);
      if (refs.length === 0) return;

      // Replace single text node with [text, link, text, link, text, ...] sequence
      const newChildren: (Text | Link)[] = [];
      let cursor = 0;

      for (const ref of refs) {
        // Text before the wikilink
        if (ref.start > cursor) {
          newChildren.push({
            type: "text",
            value: node.value.slice(cursor, ref.start),
          });
        }

        // The wikilink itself as a Link node with hProperties for renderer detection
        const url = options.urlBuilder
          ? options.urlBuilder(ref.target, ref.anchor)
          : wikilinkToUrl(ref, { routePrefix: options.routePrefix });

        newChildren.push({
          type: "link",
          url,
          title: ref.target,
          children: [{ type: "text", value: ref.display }],
          data: {
            hProperties: {
              dataWikilink: "true",
              dataTarget: ref.target,
              dataAnchor: ref.anchor ?? "",
              className: "wikilink",
            },
          },
        } as Link);

        cursor = ref.end;
      }

      // Trailing text after last wikilink
      if (cursor < node.value.length) {
        newChildren.push({
          type: "text",
          value: node.value.slice(cursor),
        });
      }

      // Splice into parent
      parent.children.splice(index, 1, ...newChildren);
      return [visit.SKIP, index + newChildren.length];
    });
  };
};
