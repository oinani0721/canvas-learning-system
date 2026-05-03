/**
 * Story 1.19 v4.0 — configure-whiteboard 全 plugin 化
 *
 * 把 Skill v3.1 的 7 步流程全部迁回 plugin script，零 LLM 调用：
 *   Step 1: 读 vault 级 .canvas-config.yaml subject（plugin: vault.adapter.read）
 *   Step 2: 场景判定 A/B（plugin: 路径检查）
 *   Step 3: 用户输入 board_name（plugin: input modal）
 *   Step 4.1: 文件级冲突（plugin: vault.getAbstractFileByPath）
 *   Step 4.2: 反向引用检测（plugin: metadataCache.resolvedLinks，10ms vs Skill 500ms）
 *   Step 5: 建白板 md（plugin: vault.create + processFrontMatter）
 *   Step 6: 种子笔记归类 move/copy（plugin: vault.rename / vault.copy）
 *   Step 7: 回执 Notice（plugin: new Notice）
 *
 * 收益：15-30s LLM 推理 → <300ms 全脚本完成。
 * Skill `configure-whiteboard` v3.1 保留作 fallback（用户手动调 /configure-whiteboard 仍能跑）。
 */

const ILLEGAL_BOARD_NAME_CHARS = /[\\/:*?"<>|#^[\]]/g;

/**
 * 清洗用户输入的白板名（去非法字符 + trim）。
 */
export function sanitizeBoardName(input: string): string {
  return input.replace(ILLEGAL_BOARD_NAME_CHARS, "").trim();
}

export function validateBoardName(name: string): {
  valid: boolean;
  reason?: string;
} {
  if (!name) return { valid: false, reason: "白板名不能为空" };
  if (name.length > 80)
    return { valid: false, reason: "白板名超过 80 字符" };
  if (ILLEGAL_BOARD_NAME_CHARS.test(name))
    return {
      valid: false,
      reason: `白板名含非法字符（${ILLEGAL_BOARD_NAME_CHARS.source}）`,
    };
  return { valid: true };
}

/**
 * Vault config schema（.canvas-config.yaml）。
 */
export interface VaultConfig {
  subject: string;
  subject_display?: string;
  active_board?: string | null;
  schema_version?: string;
}

/**
 * 极简 YAML 行解析（仅 key: value，不支持嵌套 / 数组）— 已知 .canvas-config.yaml 是平铺格式。
 *
 * 注意：实际 YAML 可能含注释（#）、引号包围的值。简化处理：取第一个 : 后内容，
 *   trim + 去外围引号。如果结构变复杂应换 yaml lib。
 */
export function parseVaultConfigYaml(text: string): VaultConfig | null {
  const lines = text.split(/\r?\n/);
  const out: Record<string, string | null> = {};
  for (const raw of lines) {
    const line = raw.replace(/^\s+|\s+$/g, "");
    if (!line || line.startsWith("#") || line.startsWith("---")) continue;
    if (line.startsWith("deprecated_paths:")) break;
    const colonIdx = line.indexOf(":");
    if (colonIdx <= 0) continue;
    const key = line.substring(0, colonIdx).trim();
    let value = line.substring(colonIdx + 1).trim();
    const hashIdx = value.indexOf("#");
    if (hashIdx >= 0) value = value.substring(0, hashIdx).trim();
    value = value.replace(/^["']|["']$/g, "");
    if (!value || value === "null") {
      out[key] = null;
    } else {
      out[key] = value;
    }
  }
  if (!out.subject) return null;
  return {
    subject: out.subject,
    subject_display: out.subject_display ?? undefined,
    active_board: out.active_board ?? null,
    schema_version: out.schema_version ?? undefined,
  };
}

/**
 * 反向引用检测：从 metadataCache.resolvedLinks 反查所有 wikilink 指向 sourceFile 的源 md。
 *
 * resolvedLinks 数据结构（Obsidian 1.5+）：
 *   { "源文件路径": { "目标文件路径": 出现次数, ... }, ... }
 *
 * 我们要找：所有 sourceMd（源 md），其 resolvedLinks[sourceMd][sourceFile.path] > 0。
 * 性能：200 笔记 < 10ms（一次性遍历 + 哈希查询）。
 */
export interface BacklinkHit {
  sourceMdPath: string;
  occurrences: number;
}

export function findBacklinkingNotes(
  resolvedLinks: Record<string, Record<string, number>>,
  targetPath: string,
): BacklinkHit[] {
  const hits: BacklinkHit[] = [];
  for (const [sourceMd, targets] of Object.entries(resolvedLinks)) {
    if (sourceMd === targetPath) continue;
    const count = targets[targetPath];
    if (typeof count === "number" && count > 0) {
      hits.push({ sourceMdPath: sourceMd, occurrences: count });
    }
  }
  return hits;
}

/**
 * 从节点 md 的 frontmatter 提取 source_board name（已在 ai-linked-doc.ts 实现，此处复用语义）。
 *
 * 期望格式 `"[[原白板/<board>]]"` → 返回 board name。
 * 不在 `原白板/` 下 → null（拒绝错位归属）。
 */
export function extractBoardFromBacklinkSource(
  frontmatter: Record<string, unknown> | undefined,
): string | null {
  if (!frontmatter) return null;
  const raw = frontmatter.source_board;
  if (!raw) return null;
  let str = "";
  if (typeof raw === "string") {
    str = raw;
  } else if (typeof raw === "object" && raw !== null) {
    const linkLike = raw as { link?: unknown; path?: unknown };
    str =
      (typeof linkLike.link === "string" && linkLike.link) ||
      (typeof linkLike.path === "string" && linkLike.path) ||
      "";
  }
  if (!str) return null;
  const match = str.match(
    /(?:\[\[)?原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/,
  );
  if (!match) return null;
  const board = match[1].trim();
  return board || null;
}

/**
 * 白板 md 模板（内嵌，避免运行时读取外部 templates/whiteboard.md.template 文件）。
 *
 * 模板与 .claude/skills/configure-whiteboard/templates/whiteboard.md.template v2.7 保持一致：
 *   - frontmatter (5 字段)
 *   - # 标题
 *   - 说明 callout
 *   - ## Concepts
 *   - ## 🔗 节点关系图（含 dataviewjs mermaid 自动生成块）
 *   - ## Recent Activity
 *
 * 占位符：{{board_name}} / {{created_at}}
 */
export const WHITEBOARD_TEMPLATE = `---
type: whiteboard
board_name: "{{board_name}}"
created_at: "{{created_at}}"
doc_count: 0
doc_mastery_avg: 0.00
---

# {{board_name}}

> [!info]+ 原白板说明（扁平架构 · round-11）
> 这是学习主题"**{{board_name}}**"的原白板。本文档即白板本身（不是白板目录的索引）。
>
> - **节点 md** 都在 vault 根的 \`节点/\` 文件夹（扁平池，一 vault 一学科零重名）
> - **subject** 字段读 vault 级 \`.canvas-config.yaml\`（不在每个 md frontmatter 重复）
> - 左栏文件树默认**折叠节点文件夹**，你主要从这份白板 md 入口管理
> - Cmd+Click \`[[wikilink]]\` 仍可跳转到节点 md（节点级 AI 对话继续工作）
>
> ## 你在这白板里能做什么
> - 选中任意文本 → \`Cmd+Shift+D\` 让 AI 派生新节点（Story 1.17），**自动建双向 wikilink**
> - 选中文本 → \`Cmd+Shift+A\` 加 Tips/错误/提问/关键点 callout + 3 态理解度 checkbox
> - 按 \`Cmd+G\` 打开 Graph View 看本白板所有 wikilink 拓扑
> - 按 \`Cmd+E\` 切 Reading View 看渲染后 callout

## Concepts

<!--
本 section 由三处维护：
  1. canvas:configure-whiteboard 命令（Story 1.19 v4 plugin）— 种子笔记 append 时写 "seed note (mastery: 0.30)"
  2. canvas:ai-linked-doc 命令（Story 1.17 v3 plugin hybrid）— AI 派生新节点时 append "extracted, weak (0.30)"
  3. 你手动 — 直接写 \`- [[xxx]]\` 都会被 Graph View 识别
wikilink 目标都指向 vault 根的 节点/ 文件夹下 md。
-->

## 🔗 节点关系图（v2.7 · 白板核心 · 自动从真实双链生成）

\`\`\`dataviewjs
const here = dv.current().file.link;
const nodes = dv.pages('"节点"')
  .where(p => p.source_board?.path === here.path);

if (nodes.length === 0) {
  dv.paragraph("> 🌱 当前白板暂无派生节点，用 Cmd+Shift+D 派生第一个");
} else {
  let chart = "graph TD\\n";
  const declared = new Set();
  nodes.forEach(n => {
    const id = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
    if (!declared.has(id)) {
      const mastery = n.mastery_score ?? '—';
      chart += \`  \${id}["\${n.file.name}<br/>精通度 \${mastery}"]\\n\`;
      chart += \`  style \${id} fill:#fff3e0,stroke:#f57c00\\n\`;
      declared.add(id);
    }
    if (n["derived-from"]) {
      const srcName = n["derived-from"].fileName ? n["derived-from"].fileName() : n["derived-from"].path.split('/').pop().replace('.md','');
      const srcId = srcName.replace(/[^a-zA-Z0-9_]/g, "_");
      if (!declared.has(srcId)) {
        chart += \`  \${srcId}["\${srcName}<br/>(源笔记)"]\\n\`;
        chart += \`  style \${srcId} fill:#e1f5ff,stroke:#0288d1\\n\`;
        declared.add(srcId);
      }
    }
  });
  nodes.forEach(n => {
    if (n["derived-from"]) {
      const srcName = n["derived-from"].fileName ? n["derived-from"].fileName() : n["derived-from"].path.split('/').pop().replace('.md','');
      const src = srcName.replace(/[^a-zA-Z0-9_]/g, "_");
      const dst = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
      chart += \`  \${src} -->|派生| \${dst}\\n\`;
    }
    (n.file.outlinks || []).forEach(link => {
      const target = nodes.find(p => p.file.path === link.path);
      if (target && target.file.name !== n.file.name) {
        const src = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
        const dst = target.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
        chart += \`  \${src} -.->|wikilink| \${dst}\\n\`;
      }
    });
  });
  dv.paragraph("\\\`\\\`\\\`mermaid\\n" + chart + "\\\`\\\`\\\`");
}
\`\`\`

> **白板 = 节点关系**（社区共识：Karpathy / Andy Matuschak / Nick Milo / Wikipedia / Maggie Appleton + 5 真实成熟项目均零分类容器段）。Cmd+G 看 Graph View 全 vault 拓扑。

## Recent Activity

- {{created_at}}: Whiteboard created
`;

export function renderWhiteboardTemplate(
  boardName: string,
  createdAt: string,
): string {
  return WHITEBOARD_TEMPLATE.replace(/\{\{board_name\}\}/g, boardName).replace(
    /\{\{created_at\}\}/g,
    createdAt,
  );
}

/**
 * 种子笔记 append 到白板 ## Concepts 的行格式（区别于 ai-linked-doc 的派生节点行）。
 */
export function buildSeedConceptsLine(seedStem: string): string {
  return `- [[节点/${seedStem}]] — seed note (mastery: 0.30)`;
}

export function buildSeedActivityLine(
  seedBasename: string,
  isoTimestamp: string,
): string {
  return `- ${isoTimestamp}: Seed note ${seedBasename} imported`;
}

/**
 * Story 1.19 v4.2 — 实时数白板 ## Concepts 段含 wikilink 的行数。
 *
 * 修复 doc_count 漂移 bug：v4.0/v4.1 plugin 每次派生 doc_count++，但用户手动删
 *   ## Concepts 行 / cleanup 时不会 --，导致 doc_count = 5 但实际只 3 行。
 * 修复方案：plugin 每次更新白板时**实时数**（不依赖累加），保证 frontmatter 准确。
 *
 * 数法：## Concepts section（直到下一个 ## 标题或 --- 分隔线）内行首是 `- [[` 的行。
 */
export function recountBoardConcepts(boardContent: string): number {
  const lines = boardContent.split(/\r?\n/);
  let inSection = false;
  let count = 0;
  for (const line of lines) {
    if (line.startsWith("## Concepts")) {
      inSection = true;
      continue;
    }
    if (!inSection) continue;
    if (line.startsWith("## ") || line.startsWith("---")) {
      break;
    }
    if (/^\s*- \[\[/.test(line)) {
      count++;
    }
  }
  return count;
}

/**
 * 节点池重名解析（同 ai-linked-doc / node-derivation 的语义，但接受任意 stem）。
 */
export function resolveUniqueSeedName(
  desiredStem: string,
  existsCheck: (path: string) => boolean,
): string {
  if (!existsCheck(`节点/${desiredStem}.md`)) return desiredStem;
  for (let n = 2; n <= 9; n++) {
    if (!existsCheck(`节点/${desiredStem}_${n}.md`)) {
      return `${desiredStem}_${n}`;
    }
  }
  throw new Error(
    `节点池 9+ 重名（${desiredStem}），可能概念拆分有问题，请手动改名`,
  );
}

/**
 * 场景判定：A 从零建（无 source 或 source 已在 原白板/ 下）/ B 从已有 md 派生。
 */
export type ConfigureScenario = "scenario_a" | "scenario_b";

export function determineScenario(
  sourcePath: string | null,
): ConfigureScenario {
  if (!sourcePath) return "scenario_a";
  if (sourcePath.startsWith("原白板/")) return "scenario_a";
  return "scenario_b";
}

/**
 * 反向引用结果聚合：把 BacklinkHit[] 升级为含 source_board 信息的结果。
 *
 * 给出每个反向引用节点的 source_board，用于 modal 列出"已属于哪个白板"。
 */
export interface BacklinkSummary {
  sourceMdPath: string;
  sourceBoardName: string | null;
}

export function summarizeBacklinks(
  hits: BacklinkHit[],
  getFrontmatter: (
    path: string,
  ) => Record<string, unknown> | undefined,
): BacklinkSummary[] {
  return hits.map((hit) => ({
    sourceMdPath: hit.sourceMdPath,
    sourceBoardName: extractBoardFromBacklinkSource(
      getFrontmatter(hit.sourceMdPath),
    ),
  }));
}

/**
 * 从 BacklinkSummary[] 提取去重的已存在白板列表（按出现频次排序）。
 */
export function deduplicateExistingBoards(
  summaries: BacklinkSummary[],
): string[] {
  const counter = new Map<string, number>();
  for (const s of summaries) {
    if (s.sourceBoardName) {
      counter.set(s.sourceBoardName, (counter.get(s.sourceBoardName) ?? 0) + 1);
    }
  }
  return Array.from(counter.entries())
    .sort((a, b) => b[1] - a[1])
    .map((e) => e[0]);
}
