/**
 * Story 1.17 v4.0 — 100% plugin 脚本派生（零 LLM 调用）
 *
 * 用户决策（2026-05-01）："派生 = 单独拉出来放在一个全新的文档来进行讨论"。
 * 不再 AI 生成正文，节点正文 = 选中文本 quote + 三段空白模板让用户自己写。
 *
 * 全部 7 步 deterministic（<200ms 完成）：
 *   1. 启发式提取概念名（无 LLM）
 *   2. 重名处理（_2 / _3 / ...）
 *   3. 构造 frontmatter（用 processFrontMatter API 保 YAML 安全）
 *   4. 生成节点正文（选中文本 quote + 三段空白模板）— **终态**，不等 AI
 *   5. wikilink + 关系 callout 模板（替换源笔记选中文本）
 *   6. 白板 ## Concepts append 行（无 ai_pending status）
 *   7. Notice 提示 — 不切 Claudian / 不写剪贴板
 *
 * 旧 v3 hybrid 阶段 2（buildPhase2SkillPrompt / AI_BODY_PLACEHOLDER）已删除 —
 *   Skill ai-linked-doc-fill v5.0 也一起删除。
 */

const ILLEGAL_FILENAME_CHARS = /[\\/:*?"<>|#^[\]]/g;
const WHITESPACE_RUN = /\s+/g;

/**
 * 启发式从选中文本提取概念名作为文件名。
 *
 * 中文：取前 2-10 个汉字（按句号 / 标点 / 换行截断）
 * 英文：取前 3-6 个 kebab-case 单词
 * 混合：保留字母数字汉字，连接符 -
 *
 * 全失败时 fallback 到 `derived-<6 位 timestamp>`。
 */
export function deriveConceptStub(selected: string): string {
  if (!selected) return fallbackStub();
  let head = selected.split(/[\n。.！!？?；;]/u)[0] ?? selected;
  head = head.trim();
  if (!head) return fallbackStub();

  const cleaned = head
    .replace(ILLEGAL_FILENAME_CHARS, "")
    .replace(WHITESPACE_RUN, "-")
    .replace(/^-+|-+$/g, "");

  if (!cleaned) return fallbackStub();

  const truncated = truncateUnicodeAware(cleaned, 40);
  if (!truncated) return fallbackStub();

  return truncated;
}

function fallbackStub(): string {
  const ts = new Date()
    .toISOString()
    .replace(/[-:T.Z]/g, "")
    .slice(8, 14);
  return `derived-${ts}`;
}

function truncateUnicodeAware(s: string, maxLen: number): string {
  const chars = Array.from(s);
  if (chars.length <= maxLen) return s;
  return chars.slice(0, maxLen).join("");
}

/**
 * 重名处理：节点池里同名 → 加 _2 / _3 / ... / _9。9+ 重名抛错。
 */
export function resolveUniqueNodeName(
  desiredStub: string,
  existsCheck: (path: string) => boolean,
): string {
  const baseName = `节点/${desiredStub}.md`;
  if (!existsCheck(baseName)) return desiredStub;
  for (let n = 2; n <= 9; n++) {
    const candidate = `节点/${desiredStub}_${n}.md`;
    if (!existsCheck(candidate)) return `${desiredStub}_${n}`;
  }
  throw new Error(
    `节点池 9+ 重名（${desiredStub}），请考虑概念拆分或手动改名`,
  );
}

const RELATION_CN_LABEL: Record<string, string> = {
  prerequisite: "先修",
  depends_on: "依赖",
  refines: "细化",
  extends: "扩展",
  example_of: "例子",
  contradicts: "反驳",
  related_to: "相关",
};

export function getRelationCnLabel(key: string): string {
  return RELATION_CN_LABEL[key] ?? key;
}

/**
 * 构造源笔记替换块（v4.1 保留原文）。
 *
 * 用户决策（2026-05-01）："虽然从原文拉出来作为新节点单独讨论，但是不要把原文删除了"。
 * 改成：原文逐字保留 + 下方紧跟 callout 标记派生关系 + wikilink。
 *
 * 输出格式（4 行 / 5 行）：
 *   <原选中文本，逐字不动>
 *   <空行>
 *   > [!relation/<key>]+ 已派生为 [[节点/<concept>]] · <中文标签>
 *   > 这段文本已被派生为独立讨论节点（保留原文供你后续阅读 + 派生节点供你深度展开）。
 *   > 你的派生意图: <description>     ← 仅当 description 非空
 *
 * PKM 共识对齐（Roam block-ref / Andy Matuschak transclude / Zettelkasten 非破坏性原则）：
 *   派生 ≠ 删除原文。原文作为"原始上下文"保留，派生节点作为"独立讨论容器"新建。
 */
export function buildSourceReplacement(
  conceptName: string,
  relationKey: string,
  description: string,
  selected: string,
): string {
  const cnLabel = getRelationCnLabel(relationKey);
  const trimmedSelected = selected.trim();
  const lines = [
    trimmedSelected,
    "",
    `> [!relation/${relationKey}]+ 已派生为 [[节点/${conceptName}]] · ${cnLabel}`,
    `> 这段文本已被派生为独立讨论节点（保留原文供你后续阅读 + 派生节点供你深度展开）。`,
  ];
  const trimmedDesc = description.trim();
  if (trimmedDesc) {
    lines.push(`> 你的派生意图: ${trimmedDesc}`);
  }
  return lines.join("\n");
}

/**
 * 构造新节点 frontmatter 数据对象（供 processFrontMatter 回调注入）。
 *
 * ⛔ 不要返回字符串拼接的 YAML — agent 1 验证：含 wikilink "[[原白板/X]]" 的字符串
 *   纯拼接会被 YAML 引擎误解析。必须用 processFrontMatter callback 让 Obsidian 处理转义。
 */
export interface NodeFrontmatter {
  type: "concept";
  mastery_score: number;
  created_at: string;
  source_note: string;
  source_board: string;
  created_from: "ai_linked_doc";
  up: string;
  "derived-from": string;
  relationships: Array<{
    type: string;
    target: string;
    description?: string;
  }>;
}

export function buildNodeFrontmatter(args: {
  sourceNoteStem: string;
  activeBoard: string;
  relationKey: string;
  description: string;
  createdAt: string;
}): NodeFrontmatter {
  const sourceWikilink = `[[${args.sourceNoteStem}]]`;
  const rel: NodeFrontmatter["relationships"][0] = {
    type: args.relationKey,
    target: sourceWikilink,
  };
  const trimmedDesc = args.description.trim();
  if (trimmedDesc) rel.description = trimmedDesc;
  return {
    type: "concept",
    mastery_score: 0.3,
    created_at: args.createdAt,
    source_note: sourceWikilink,
    source_board: `[[原白板/${args.activeBoard}]]`,
    created_from: "ai_linked_doc",
    up: sourceWikilink,
    "derived-from": sourceWikilink,
    relationships: [rel],
  };
}

/**
 * 节点正文模板（v4.0 终态，无 AI 生成）。
 *
 * 用户决策："派生 = 拉出来放新文档讨论"。正文 = 选中文本 quote + 三段空白让用户自己写。
 * 用户后续可在节点 md 内打开 Claudian sidebar 围绕这个概念展开讨论。
 *
 * Quote 块用 [!quote]+ callout 友好显示原文；三段（核心概念 / 关键点 / 关联概念）
 * 提供"思考起点"模板（PKM Evergreen Notes 共识：用户必须自己写以触发深度思考）。
 */
export function buildNodeBody(
  conceptName: string,
  selected: string,
  sourceNoteStem: string,
): string {
  const trimmedSelected = selected.trim();
  return [
    `# ${conceptName}`,
    "",
    `> [!quote]+ 派生起点（来自 [[${sourceNoteStem}]] 选中文本）`,
    `> ${trimmedSelected.replace(/\n/g, "\n> ")}`,
    "",
    "## 核心概念",
    "",
    "（你的 1-2 句精准定义。这个概念 *是什么* / *为什么重要*？）",
    "",
    "## 关键点",
    "",
    "- ",
    "",
    "## 关联概念",
    "",
    `- [[${sourceNoteStem}]] — extracted from this note`,
    "",
    "---",
    "",
    "> [!tip] 💬 围绕这个概念讨论",
    "> 这个节点是**讨论容器**，不是 AI 写好的内容。你可以：",
    "> - 在上面三段空白处写下你的理解（最有学习价值）",
    "> - 打开 Claudian sidebar 围绕本节点和 Claude 自由对话（节点级 AI 对话）",
    "> - `Cmd+Shift+D` 选中本节点正文继续派生子节点",
    "> - `Cmd+Shift+A` 选中文字加 Tips/疑问/错误标注",
    "",
  ].join("\n");
}

/**
 * 白板 ## Concepts append 行（v4.0：无 ai_pending status，因为不再有 AI 阶段）。
 */
export function buildBoardConceptsLine(
  conceptName: string,
  relationKey: string,
): string {
  return `- [[节点/${conceptName}]] — ${relationKey}, weak (0.30)`;
}

export function buildBoardActivityLine(
  conceptName: string,
  sourceNoteStem: string,
  relationKey: string,
  isoTimestamp: string,
): string {
  return `- ${isoTimestamp}: Extracted [[节点/${conceptName}]] via canvas:ai-linked-doc from [[${sourceNoteStem}]]（关系: ${relationKey}）`;
}
