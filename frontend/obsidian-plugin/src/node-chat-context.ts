/**
 * Story 3.1 v1.0 — 节点对话上下文收集 + prompt 组装（纯函数模块）
 *
 * 用户决策（2026-05-02 路线 A）：4 MVP 闭环达成后先用 Claudian 现成对话能力跑节点 AI 对话原型。
 * 复用 1.17 v3.0 已验证的 Hybrid 范式（plugin clipboard write + Claudian invoke）。
 *
 * 本文件只放纯函数（无 obsidian API 依赖），让单元测试好写。
 * obsidian API 调用（metadataCache / vault.read）放在 main.ts 的 handleOpenNodeChat 内。
 */

export interface NeighborSummary {
  path: string;
  type?: string;
  excerpt?: string;
}

export interface NodeChatContext {
  nodePath: string;
  nodeBasename: string;
  frontmatter: Record<string, unknown>;
  body: string;
  selection?: string;
  neighbors: NeighborSummary[];
}

export interface PromptBuildResult {
  prompt: string;
  sizeBytes: number;
  truncated: boolean;
  truncationReason?: string;
}

const DEFAULT_MAX_BYTES = 10 * 1024;
const TRUNCATED_BODY_RATIO = 0.6;
const TRUNCATED_NEIGHBOR_EXCERPT = 50;

/**
 * 剥离 frontmatter（YAML 块），返回正文。
 *
 * 兼容场景：
 *   - 标准 `---\n...\n---\n<body>` → 返回 body
 *   - 无 frontmatter（直接正文）→ 返回原文
 *   - 仅有起始 `---` 但缺结束 → 返回原文（防 corruption）
 */
export function extractBodyWithoutFrontmatter(content: string): string {
  if (!content.startsWith("---")) return content;
  const lines = content.split("\n");
  if (lines.length < 2 || lines[0].trim() !== "---") return content;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") {
      return lines.slice(i + 1).join("\n").replace(/^\n+/, "");
    }
  }
  return content;
}

/**
 * 截取首 N 个 unicode 字符（处理中英混合）。
 * 不破坏 emoji / surrogate pair。
 */
export function unicodeFirstN(s: string, n: number): string {
  const arr = Array.from(s);
  return arr.slice(0, n).join("");
}

/**
 * 节点 frontmatter 提炼为 prompt 头部行。
 * 缺字段不输出，避免"undefined"污染。
 */
export function formatFrontmatterLines(fm: Record<string, unknown>): string {
  const lines: string[] = [];
  if (typeof fm.type === "string") lines.push(`类型: ${fm.type}`);
  if (typeof fm.source_board === "string") {
    lines.push(`所属白板: ${fm.source_board}`);
  } else if (fm.source_board && typeof fm.source_board === "object") {
    const sb = fm.source_board as Record<string, unknown>;
    const linkOrPath = sb.link || sb.path;
    if (typeof linkOrPath === "string") {
      lines.push(`所属白板: ${linkOrPath}`);
    }
  }
  if (typeof fm.mastery_score === "number") {
    const score = fm.mastery_score;
    // Dashboard v1.x 对齐：<= 0.3 起步🔴，<= 0.7 进行中🟡，> 0.7 掌握🟢
    const emoji = score <= 0.3 ? "🔴" : score <= 0.7 ? "🟡" : "🟢";
    lines.push(`Mastery: ${score.toFixed(2)} ${emoji}`);
  }
  if (Array.isArray(fm.relationships) && fm.relationships.length > 0) {
    const types = fm.relationships
      .map((r: unknown) => {
        if (r && typeof r === "object" && "type" in (r as object)) {
          return String((r as Record<string, unknown>).type);
        }
        return null;
      })
      .filter((t): t is string => t !== null);
    if (types.length > 0) {
      lines.push(`关系类型: ${types.join(" / ")}`);
    }
  }
  return lines.join("\n");
}

/**
 * 邻居列表渲染为 prompt 行。
 */
function formatNeighborLines(
  neighbors: NeighborSummary[],
  excerptMax = 100,
): string {
  if (neighbors.length === 0) {
    return "（无关联节点 — 这是孤立概念）";
  }
  return neighbors
    .map((n) => {
      const typePart = n.type ? ` (${n.type})` : "";
      const excerptPart = n.excerpt
        ? ` — ${unicodeFirstN(n.excerpt.replace(/\s+/g, " ").trim(), excerptMax)}`
        : "";
      return `- [[${n.path}]]${typePart}${excerptPart}`;
    })
    .join("\n");
}

/**
 * 组装 prompt 写到剪贴板。
 *
 * 大小控制：
 *   - 总长 <= maxBytes（默认 10KB）
 *   - 超长 → 节点 body 截到 60% + 邻居 excerpt 截到 50 字
 *   - 仍超长 → body 强行截到 maxBytes 80% + 注 "[...原文还有 X 字]"
 */
export function buildNodeChatPrompt(
  context: NodeChatContext,
  options: { maxBytes?: number } = {},
): PromptBuildResult {
  const maxBytes = options.maxBytes ?? DEFAULT_MAX_BYTES;
  const fmLines = formatFrontmatterLines(context.frontmatter);
  const neighborSection = formatNeighborLines(context.neighbors);

  const buildPrompt = (
    body: string,
    neighbors: string,
    selection: string | undefined,
  ): string => {
    const sections: string[] = [];
    sections.push("/node-chat");
    sections.push("");
    sections.push("## 当前节点");
    sections.push(`路径: ${context.nodePath}`);
    sections.push(`节点名: ${context.nodeBasename}`);
    if (fmLines) sections.push(fmLines);
    sections.push("");
    sections.push("## 节点正文");
    sections.push(body);
    if (selection) {
      sections.push("");
      sections.push("## 选中文（重点关注）");
      sections.push(selection);
    }
    sections.push("");
    sections.push(
      `## 1-hop 邻居（${context.neighbors.length} 个 wikilink 关联节点）`,
    );
    sections.push(neighbors);
    sections.push("");
    sections.push("## 任务");
    sections.push("围绕本节点进行学习对话。可问的方向：");
    sections.push("- 概念定义 / 直觉解释");
    sections.push("- 与邻居节点的关系");
    sections.push("- 具体例子 / 反例");
    sections.push("- 自测题");
    return sections.join("\n");
  };

  let prompt = buildPrompt(context.body, neighborSection, context.selection);
  let truncated = false;
  let truncationReason: string | undefined;

  if (byteLength(prompt) > maxBytes) {
    truncated = true;
    const trimmedNeighbors = formatNeighborLines(
      context.neighbors,
      TRUNCATED_NEIGHBOR_EXCERPT,
    );
    const targetBodyChars = Math.max(
      200,
      Math.floor(Array.from(context.body).length * TRUNCATED_BODY_RATIO),
    );
    let trimmedBody = unicodeFirstN(context.body, targetBodyChars);
    const remaining = Array.from(context.body).length - targetBodyChars;
    if (remaining > 0) {
      trimmedBody += `\n\n[... 原文还有约 ${remaining} 字]`;
    }
    prompt = buildPrompt(trimmedBody, trimmedNeighbors, context.selection);
    truncationReason = "body+neighbor 截断（节点正文 60% / 邻居摘要 50 字）";
  }

  if (byteLength(prompt) > maxBytes) {
    const safeBytes = Math.floor(maxBytes * 0.8);
    const truncatedPrompt = takeBytes(prompt, safeBytes) +
      "\n\n[... prompt 截断到 80% maxBytes 防溢出 ...]";
    return {
      prompt: truncatedPrompt,
      sizeBytes: byteLength(truncatedPrompt),
      truncated: true,
      truncationReason: "prompt 整体强制截断（80% maxBytes）",
    };
  }

  return {
    prompt,
    sizeBytes: byteLength(prompt),
    truncated,
    truncationReason,
  };
}

/**
 * 用 TextEncoder 算 UTF-8 byte 长度（中文 1 字符 = 3 bytes）。
 */
export function byteLength(s: string): number {
  if (typeof TextEncoder !== "undefined") {
    return new TextEncoder().encode(s).length;
  }
  return Buffer.byteLength(s, "utf8");
}

/**
 * 按 byte 长度截取（防 unicode 半字符 corruption）。
 */
function takeBytes(s: string, maxBytes: number): string {
  if (typeof TextEncoder !== "undefined" && typeof TextDecoder !== "undefined") {
    const buf = new TextEncoder().encode(s);
    if (buf.length <= maxBytes) return s;
    return new TextDecoder("utf-8", { fatal: false }).decode(
      buf.slice(0, maxBytes),
    );
  }
  let bytes = 0;
  let cut = 0;
  for (let i = 0; i < s.length; i++) {
    const cp = s.charCodeAt(i);
    bytes += cp < 0x80 ? 1 : cp < 0x800 ? 2 : 3;
    if (bytes > maxBytes) break;
    cut = i + 1;
  }
  return s.slice(0, cut);
}

/**
 * 路径规范化（不依赖 obsidian module，让单元测试好跑）。
 *
 * - 反斜杠 → 正斜杠（Windows 兼容）
 * - 折叠重复 `/`
 * - 去掉前导 `/` 或 `./`
 * - 解析 `..` 段（防 path traversal escape）
 *
 * `节点/../escape.md` → `escape.md`（前缀检查会失败 → escape 拒绝）
 */
function _normalizePath(path: string): string {
  const normalized = path.replace(/[\\/]+/g, "/").replace(/^\.?\//, "");
  const segments = normalized.split("/");
  const resolved: string[] = [];
  for (const seg of segments) {
    if (seg === ".." && resolved.length > 0) {
      resolved.pop();
    } else if (seg === ".." || seg === "." || seg === "") {
      continue;
    } else {
      resolved.push(seg);
    }
  }
  return resolved.join("/");
}

/**
 * Story 2.1 P1.6 — 检查 path 是否在 nodePathPrefixes 任一前缀下，且为 .md 笔记。
 *
 * 升级（v1.1）：
 * - 接受 prefixes 参数（DD-10 配置化，默认 `["节点/"]` 兼容现有 vault）
 * - 内置 path normalization（防反斜杠 / `..` 路径逃逸）
 *
 * @param path - 要检查的路径（任意大小写 / 任意斜杠形式）
 * @param prefixes - 允许的前缀列表（默认 `["节点/"]`），不带 `/` 的会自动补
 */
export function isNodePath(
  path: string,
  prefixes: string[] = ["节点/"],
): boolean {
  if (!path) return false;
  const normalized = _normalizePath(path);
  if (!normalized.endsWith(".md")) return false;
  return prefixes.some((p) => {
    const prefix = p.endsWith("/") ? p : `${p}/`;
    return normalized.startsWith(prefix);
  });
}

/**
 * 从 frontmatter 抽 type 字段（兜底返回 undefined）。
 */
export function extractFrontmatterType(
  fm: Record<string, unknown> | undefined,
): string | undefined {
  if (!fm) return undefined;
  const t = fm.type;
  return typeof t === "string" ? t : undefined;
}

/**
 * Story 2.2+2.9 T1 (2026-05-11) — chat-with-context 降级路径输入。
 *
 * 触发场景:
 *   - backend_timeout: AbortController abort (>3000ms)
 *   - backend_unreachable: fetch TypeError (docker 没启 / 网络断 / DNS fail)
 */
export type ChatFallbackReason = "backend_timeout" | "backend_unreachable";

export interface ChatWithContextFallbackInput {
  reason: ChatFallbackReason;
  localPrompt: string;
}

/**
 * Story 2.2+2.9 T1 (2026-05-11) — 组装 backend 降级路径的 chat-with-context prompt。
 *
 * 保留 /chat-with-context skill 前缀（用户视角连续，不混淆为 /node-chat）,
 * 在 prompt 顶部加 HTML 注释 marker 让 Claude/Skill 端识别降级路径
 * （邻居数从 N-hop 降到 1-hop, supplementary=0, 应跳过 ANCHOR_INSTRUCTION 的 Read 步骤）。
 *
 * HTML 注释格式 `<!-- ... -->` 是 Obsidian-safe 的（渲染时不可见，不暴露给用户）。
 */
export function buildChatWithContextFallbackPrompt(
  input: ChatWithContextFallbackInput,
): string {
  const { reason, localPrompt } = input;
  const header = `<!-- Degradations: ${reason} / fallback=local_metadata / hop=1 -->`;
  return `/chat-with-context\n\n${header}\n\n${localPrompt}`;
}
