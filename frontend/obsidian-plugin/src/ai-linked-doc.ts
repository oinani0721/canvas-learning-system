export interface RelationTypeOption {
  key: string;
  label: string;
  description: string;
}

/**
 * Story 1.17 v2.4 — D1-1 决策 C 混合 7 类（项目 Story 6-3 5 类 + 社区 prerequisite + example_of）
 * 用户在 Cmd+Shift+D 派生新节点时通过 Modal 选择本组中的一类作为新节点和源笔记的关系。
 * 7 类同时落到：
 *   1. 源笔记 callout `[!relation/<key>]+`（视觉提示）
 *   2. 新节点 frontmatter `relationships: [{type: <key>, target: [[源笔记]]}]`（机器可读）
 */
export const RELATION_TYPES: readonly RelationTypeOption[] = [
  {
    key: "prerequisite",
    label: "先修 (prerequisite)",
    description: "新节点是源笔记的先修知识（学源笔记必须先懂新节点）",
  },
  {
    key: "depends_on",
    label: "依赖 (depends_on)",
    description: "新节点在概念上依赖源笔记（理解新节点需要源笔记的概念）",
  },
  {
    key: "refines",
    label: "细化 (refines)",
    description: "新节点是源笔记某段的更细化版本",
  },
  {
    key: "extends",
    label: "扩展 (extends)",
    description: "新节点在源笔记基础上延伸或补全",
  },
  {
    key: "example_of",
    label: "例子 (example_of)",
    description: "新节点是源笔记某概念的具体例子或实例",
  },
  {
    key: "contradicts",
    label: "反驳 (contradicts)",
    description: "新节点与源笔记观点矛盾或反驳",
  },
  {
    key: "related_to",
    label: "相关 (related_to)",
    description: "一般性关联（兜底，不确定哪类时选这个）",
  },
] as const;

export function getRelationLabel(key: string): string {
  return RELATION_TYPES.find((r) => r.key === key)?.label ?? key;
}

export function isValidRelationKey(key: string): boolean {
  return RELATION_TYPES.some((r) => r.key === key);
}

/**
 * Story 1.17 v2.5 — D1-4 决策 B 可选 + D1-5 决策 C 三处都写
 * 用户在选完关系类型后弹第二个 modal，自由文本描述"为什么要派生这个节点"。
 * 留空 / Esc → description = "" (下游处理时跳过 callout body 行 + 跳过 frontmatter 字段 + 不注入 prompt)
 * 非空 → 写入 (1) 源笔记 callout body / (2) 新节点 frontmatter relationships[].description / (3) AI prompt
 */
export function buildAIDocPrompt(
  selected: string,
  sourcePath: string,
  activeBoard?: string,
  relationType?: string,
  description?: string,
): string {
  const activeBoardLine = activeBoard
    ? `活动白板: ${activeBoard}\n`
    : `活动白板: (Skill 会从 .canvas-config.yaml 或 AskUserQuestion 确定)\n`;

  const relationKey =
    relationType && isValidRelationKey(relationType)
      ? relationType
      : "related_to";
  const relationLabel = getRelationLabel(relationKey);
  const relationLine = `关系类型: ${relationKey} (${relationLabel})\n`;

  const trimmedDesc = (description ?? "").trim();
  const descLine = trimmedDesc
    ? `派生描述: ${trimmedDesc}\n`
    : `派生描述: (用户留空)\n`;

  return (
    `/ai-linked-doc\n` +
    `Please invoke the Skill tool with skill_name="ai-linked-doc" to handle this request.\n` +
    `Do NOT answer freely — follow the 8-step Skill flow strictly.\n` +
    `\n` +
    `选中文本:\n${selected}\n\n` +
    `源笔记路径: ${sourcePath}\n` +
    activeBoardLine +
    relationLine +
    descLine +
    `\n` +
    `请为这段内容派生一个新概念节点（扁平架构：节点/<concept>.md + 更新 原白板/<active_board>.md 的 ## Concepts）。`
  );
}

export function isBoardsPath(sourcePath: string): boolean {
  return sourcePath !== "unknown" && sourcePath.startsWith("原白板/");
}

export function isNodesPath(sourcePath: string): boolean {
  return sourcePath !== "unknown" && sourcePath.startsWith("节点/");
}

export function isFlatArchPath(sourcePath: string): boolean {
  return isBoardsPath(sourcePath) || isNodesPath(sourcePath);
}

export function extractBoardNameFromPath(sourcePath: string): string | null {
  if (!isBoardsPath(sourcePath)) return null;
  const filename = sourcePath.substring("原白板/".length);
  return filename.endsWith(".md")
    ? filename.substring(0, filename.length - 3)
    : filename;
}

/**
 * Story 1.17 v2.6 — 节点派生节点继承源节点的 source_board 白板归属。
 *
 * source_board frontmatter 实际格式（v4 Skill 写入）："[[原白板/<board_name>]]"。
 * Obsidian metadataCache 把 frontmatter 中的 wikilink 解析为：
 *   - 较新版本: Link-like 对象 `{ link: "原白板/<board>", path?: ... }`
 *   - 较老版本: 原始字符串 "[[原白板/<board>]]"
 *
 * 本函数对两种形态都 robust：先取出底层字符串，用 regex 提取 board name。
 * 失败 / 不在 `原白板/` 下 → null（让上层 fallback 到 .canvas-config.yaml 或 AskUserQuestion）。
 */
export function extractSourceBoardFromFrontmatter(
  frontmatter: Record<string, unknown> | undefined,
): string | null {
  if (!frontmatter) return null;
  const raw = frontmatter.source_board;
  if (!raw) return null;
  let str = "";
  if (typeof raw === "string") {
    str = raw;
  } else if (typeof raw === "object" && raw !== null) {
    const linkLike = raw as { link?: unknown; path?: unknown; display?: unknown };
    str =
      (typeof linkLike.link === "string" && linkLike.link) ||
      (typeof linkLike.path === "string" && linkLike.path) ||
      (typeof linkLike.display === "string" && linkLike.display) ||
      "";
  }
  if (!str) return null;
  const match = str.match(/(?:\[\[)?原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
  if (!match) return null;
  const board = match[1].trim();
  return board || null;
}
