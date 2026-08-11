import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildSeedActivityLine,
  buildSeedConceptsLine,
  deduplicateExistingBoards,
  determineScenario,
  extractBoardFromBacklinkSource,
  findBacklinkingNotes,
  parseVaultConfigYaml,
  renderWhiteboardTemplate,
  resolveUniqueSeedName,
  sanitizeBoardName,
  summarizeBacklinks,
  validateBoardName,
  WHITEBOARD_TEMPLATE,
  recountBoardConcepts,
} from "../src/configure-whiteboard";

// ════════════════════════════════════════════════════════════════════
// sanitizeBoardName / validateBoardName
// ════════════════════════════════════════════════════════════════════

test("sanitizeBoardName: 去前后空白", () => {
  assert.equal(sanitizeBoardName("  线性代数  "), "线性代数");
});

test("sanitizeBoardName: 移除非法字符", () => {
  assert.equal(sanitizeBoardName("a/b\\c:d*e?f<>g"), "abcdefg");
});

test("sanitizeBoardName: 中英混合 + 空格保留", () => {
  assert.equal(
    sanitizeBoardName("CS 61B 数据结构"),
    "CS 61B 数据结构",
  );
});

test("validateBoardName: 空名 → invalid", () => {
  assert.equal(validateBoardName("").valid, false);
});

test("validateBoardName: 80+ 字符 → invalid", () => {
  const long = "a".repeat(81);
  assert.equal(validateBoardName(long).valid, false);
});

test("validateBoardName: 含非法字符 → invalid", () => {
  assert.equal(validateBoardName("foo/bar").valid, false);
});

test("validateBoardName: 中英混合 + 空格 → valid", () => {
  assert.equal(validateBoardName("CS 61B 数据结构").valid, true);
});

// ════════════════════════════════════════════════════════════════════
// parseVaultConfigYaml
// ════════════════════════════════════════════════════════════════════

test("parseVaultConfigYaml: 真实 .canvas-config.yaml 格式", () => {
  const yaml = `
# Comment
subject: cs-61b
subject_display: "CS 61B 数据结构"
active_board: null
schema_version: "1.0-flat-architecture-2026-04-20"
`;
  const cfg = parseVaultConfigYaml(yaml);
  assert.ok(cfg);
  assert.equal(cfg!.subject, "cs-61b");
  assert.equal(cfg!.subject_display, "CS 61B 数据结构");
  assert.equal(cfg!.active_board, null);
});

test("parseVaultConfigYaml: 缺 subject → null", () => {
  const yaml = `subject_display: "X"\nactive_board: null\n`;
  assert.equal(parseVaultConfigYaml(yaml), null);
});

test("parseVaultConfigYaml: 行内注释 (#) 被剥离", () => {
  const yaml = `subject: math240   # 数学专题`;
  const cfg = parseVaultConfigYaml(yaml);
  assert.equal(cfg!.subject, "math240");
});

test("parseVaultConfigYaml: 引号包裹的值剥离引号", () => {
  const yaml = `subject: "cs-61b"\nactive_board: 'foo'\n`;
  const cfg = parseVaultConfigYaml(yaml);
  assert.equal(cfg!.subject, "cs-61b");
  assert.equal(cfg!.active_board, "foo");
});

test("parseVaultConfigYaml: deprecated_paths 数组段被忽略", () => {
  const yaml = `subject: x\ndeprecated_paths:\n  - wiki/canvases/\n  - wiki/concepts/\n`;
  const cfg = parseVaultConfigYaml(yaml);
  assert.equal(cfg!.subject, "x");
});

// ════════════════════════════════════════════════════════════════════
// findBacklinkingNotes / summarizeBacklinks / deduplicateExistingBoards
// ════════════════════════════════════════════════════════════════════

test("findBacklinkingNotes: 反向查询 200 笔记 < 10ms", () => {
  const links: Record<string, Record<string, number>> = {};
  for (let i = 0; i < 200; i++) {
    links[`节点/n${i}.md`] = {
      "节点/Fundamentals.md": i % 3 === 0 ? 1 : 0,
    };
  }
  const t0 = Date.now();
  const hits = findBacklinkingNotes(links, "节点/Fundamentals.md");
  const elapsed = Date.now() - t0;
  assert.ok(hits.length > 0, "应有命中");
  assert.ok(
    elapsed < 100,
    `200 笔记反向查询应 < 100ms（实测 ${elapsed}ms）`,
  );
});

test("findBacklinkingNotes: 排除自引用", () => {
  const links = {
    "节点/A.md": { "节点/A.md": 1, "节点/B.md": 1 },
  };
  const hits = findBacklinkingNotes(links, "节点/A.md");
  assert.equal(hits.length, 0, "自身不算反向引用");
});

test("findBacklinkingNotes: 0 引用 → 空数组", () => {
  const links = {};
  const hits = findBacklinkingNotes(links, "节点/Fundamentals.md");
  assert.deepEqual(hits, []);
});

test("findBacklinkingNotes: 多源 md 引用同目标 → 全部捕获", () => {
  const links = {
    "节点/A.md": { "节点/Fundamentals.md": 1 },
    "节点/B.md": { "节点/Fundamentals.md": 2 },
    "节点/C.md": { "节点/Other.md": 1 },
  };
  const hits = findBacklinkingNotes(links, "节点/Fundamentals.md");
  assert.equal(hits.length, 2);
  assert.equal(hits[0].sourceMdPath, "节点/A.md");
  assert.equal(hits[1].sourceMdPath, "节点/B.md");
  assert.equal(hits[1].occurrences, 2);
});

test("summarizeBacklinks + deduplicateExistingBoards: 按白板归类", () => {
  const hits = [
    { sourceMdPath: "节点/A.md", occurrences: 1 },
    { sourceMdPath: "节点/B.md", occurrences: 1 },
    { sourceMdPath: "节点/C.md", occurrences: 1 },
  ];
  const fmMap: Record<string, Record<string, unknown>> = {
    "节点/A.md": { source_board: "[[原白板/线性代数]]" },
    "节点/B.md": { source_board: "[[原白板/线性代数]]" },
    "节点/C.md": { source_board: "[[原白板/CS 61B]]" },
  };
  const summaries = summarizeBacklinks(hits, (p) => fmMap[p]);
  assert.equal(summaries.length, 3);
  const boards = deduplicateExistingBoards(summaries);
  assert.deepEqual(boards, ["线性代数", "CS 61B"], "频次降序");
});

// ════════════════════════════════════════════════════════════════════
// extractBoardFromBacklinkSource
// ════════════════════════════════════════════════════════════════════

test("extractBoardFromBacklinkSource: 复用 ai-linked-doc 的 robust 解析", () => {
  assert.equal(
    extractBoardFromBacklinkSource({
      source_board: "[[原白板/特征值与特征向量]]",
    }),
    "特征值与特征向量",
  );
  assert.equal(
    extractBoardFromBacklinkSource({
      source_board: "[[原白板/CS 61B.md]]",
    }),
    "CS 61B",
  );
  assert.equal(extractBoardFromBacklinkSource(undefined), null);
  assert.equal(
    extractBoardFromBacklinkSource({ source_board: "" }),
    null,
  );
});

// ════════════════════════════════════════════════════════════════════
// determineScenario
// ════════════════════════════════════════════════════════════════════

test("determineScenario: null source → A", () => {
  assert.equal(determineScenario(null), "scenario_a");
});

test("determineScenario: 已在 原白板/ 下 → A", () => {
  assert.equal(determineScenario("原白板/CS 61B.md"), "scenario_a");
});

test("determineScenario: 在 节点/ 或其他路径 → B", () => {
  assert.equal(determineScenario("节点/foo.md"), "scenario_b");
  assert.equal(
    determineScenario("wiki/canvases/math140/Fundamentals.md"),
    "scenario_b",
  );
  assert.equal(determineScenario("raw/notes.md"), "scenario_b");
});

// ════════════════════════════════════════════════════════════════════
// resolveUniqueSeedName
// ════════════════════════════════════════════════════════════════════

test("resolveUniqueSeedName: 不冲突 → 原 stem", () => {
  assert.equal(
    resolveUniqueSeedName("foo", () => false),
    "foo",
  );
});

test("resolveUniqueSeedName: 9+ 重名 → 抛错", () => {
  const existing = new Set([
    "节点/foo.md",
    "节点/foo_2.md",
    "节点/foo_3.md",
    "节点/foo_4.md",
    "节点/foo_5.md",
    "节点/foo_6.md",
    "节点/foo_7.md",
    "节点/foo_8.md",
    "节点/foo_9.md",
  ]);
  assert.throws(() => {
    resolveUniqueSeedName("foo", (p) => existing.has(p));
  }, /9\+ 重名/);
});

// ════════════════════════════════════════════════════════════════════
// renderWhiteboardTemplate
// ════════════════════════════════════════════════════════════════════

test("renderWhiteboardTemplate: 占位符全部替换", () => {
  const out = renderWhiteboardTemplate("线性代数", "2026-04-30T10:00:00Z");
  assert.ok(!out.includes("{{board_name}}"), "board_name 占位应被替换");
  assert.ok(!out.includes("{{created_at}}"), "created_at 占位应被替换");
  assert.ok(out.includes("线性代数"));
  assert.ok(out.includes("2026-04-30T10:00:00Z"));
});

test("renderWhiteboardTemplate: 含 frontmatter 5 字段", () => {
  const out = renderWhiteboardTemplate("X", "Y");
  assert.ok(out.includes("type: whiteboard"));
  assert.ok(out.includes('board_name: "X"'));
  assert.ok(out.includes('created_at: "Y"'));
  assert.ok(out.includes("doc_count: 0"));
  assert.ok(!out.includes("doc_mastery_avg")); // 2026-07-25 死字段已删 (双真相源反模式, 板均值由节点实时派生)
});

test("renderWhiteboardTemplate: 含 ## Concepts + ## Recent Activity sections", () => {
  const out = renderWhiteboardTemplate("X", "Y");
  assert.ok(out.includes("## Concepts"));
  assert.ok(out.includes("## Recent Activity"));
  assert.ok(out.includes("## 🔗 节点关系图"));
});

test("renderWhiteboardTemplate: dataviewjs 块完整保留 (mermaid 自动生成)", () => {
  const out = renderWhiteboardTemplate("X", "Y");
  assert.ok(out.includes("```dataviewjs"));
  assert.ok(out.includes('dv.pages(\'"节点"\')'));
  assert.ok(out.includes("source_board"));
});

test("WHITEBOARD_TEMPLATE: 模板与 vault 侧 .template 同源标识（v2.7 关系图段）", () => {
  // 原断言是 `includes("v4 plugin")`，那句字面量只存在于旧的「本 section 由三处
  // 维护」注释里 —— RAG-S2.6 把 ## Concepts 降级成只读派生物后，「三处维护」
  // 这个前提本身作废，注释已被 sentinel 块取代。⇒ 改锁一个仍然成立的同源标识。
  assert.ok(WHITEBOARD_TEMPLATE.includes("v2.7 · 白板核心"));
});

// ════════════════════════════════════════════════════════════════════
// buildSeedConceptsLine / buildSeedActivityLine
// ════════════════════════════════════════════════════════════════════

test("buildSeedConceptsLine: 标 seed note (mastery: 0.30)", () => {
  const line = buildSeedConceptsLine("foo");
  assert.equal(line, "- [[节点/foo]] — seed note (mastery: 0.30)");
});

test("buildSeedActivityLine: ISO 时间 + Seed note imported", () => {
  const line = buildSeedActivityLine(
    "Fundamentals.md",
    "2026-05-01T00:00:00Z",
  );
  assert.equal(
    line,
    "- 2026-05-01T00:00:00Z: Seed note Fundamentals.md imported",
  );
});

// ════════════════════════════════════════════════════════════════════
// recountBoardConcepts — RAG-S2.6 FIX-8「三把锁口径统一」
// ════════════════════════════════════════════════════════════════════

const AUTOGEN_BLOCK = [
  "## Concepts",
  "",
  "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py · 真相源 = 节点 frontmatter source_board",
  "     ⛔ 请勿手改：手改会在下次同步时被覆盖。增删成员请改节点的 source_board（或 Cmd+Shift+D 派生） -->",
  "- [[节点/甲]] — 种子 · 掌握度 0.30 · 未考",
  "- [[节点/乙]] — 派生自 甲 · 掌握度 0.10 · 已考 2 次",
  "<!-- /AUTO-GENERATED n=2 · synced 2026-08-11T00:00:00Z -->",
  "",
  "## 其他段",
].join("\n");

test("recountBoardConcepts: 有托管块时只数块内（游离行不计）", () => {
  // ⛔ 同步脚本改成白名单收编后会**保留**段内非成员游离行；本函数若仍全段
  // 扫描就会把它们数进 doc_count，与脚本写的成员数形成 flip-flop：
  // 脚本写 2 → 本函数回写 4 → --check 红 → 脚本写回 2 → 无限拉锯。
  const withStray = AUTOGEN_BLOCK.replace(
    "\n## 其他段",
    "\n- [[教材第三章]] 这本书要重看\n- [[原白板/线性代数]]\n\n## 其他段",
  );
  assert.equal(recountBoardConcepts(withStray), 2);
});

test("recountBoardConcepts: 无托管块时回落全段扫描（迁移前 / 手工板兼容）", () => {
  const legacy = [
    "## Concepts",
    "",
    "- [[节点/甲]] — seed note (mastery: 0.30)",
    "- [[节点/乙]] — extends, weak (0.30)",
    "",
    "## 其他段",
  ].join("\n");
  assert.equal(recountBoardConcepts(legacy), 2);
});

test("recountBoardConcepts: 块内空清单（占位提示行）计 0", () => {
  const empty = AUTOGEN_BLOCK.replace(
    /- \[\[节点\/甲\]\][^\n]*\n- \[\[节点\/乙\]\][^\n]*\n/,
    "_（暂无节点 — 在源笔记选中文本按 `Cmd+Shift+D` 派生第一个）_\n",
  );
  assert.equal(recountBoardConcepts(empty), 0);
});

test("WHITEBOARD_TEMPLATE: dataviewjs 过滤剥 .md 后缀（FIX-10 防模板回退）", () => {
  // Dataview 的 p.source_board.path 是裸 linkpath，here.path 永远带 .md；
  // 恒等比较全靠索引期归一化补救，索引未归一时静默退化成「暂无派生节点」。
  // ⛔ 断言里要的是产出文本 `\.md$`（正则转义点），不是 `.md$`（任意字符+md）——
  //    模板是 JS 模板字面量，源码里必须写 `\\.` 才能产出 `\.`，写 `\.` 会被吃掉。
  assert.ok(
    WHITEBOARD_TEMPLATE.includes('.replace(/\\.md$/, "")'),
    "模板必须产出转义好的 /\\.md$/，不能是 /.md$/",
  );
  assert.ok(!WHITEBOARD_TEMPLATE.includes("source_board?.path === here.path"));
});

test("WHITEBOARD_TEMPLATE: Concepts 段是 sync 脚本的 sentinel 块（两个模板源必须同形）", () => {
  // ⛔ 本条锁的是「两个模板源不同步」这个根因：新建白板走 plugin 命令时用的是
  //    这里的 TS 模板，而 RAG-S2.6 T2 只改了 vault 里的 .template 文件 ——
  //    结果 plugin 建出来的新白板仍是旧「三处维护」格式、没有 sentinel，
  //    同步脚本要走一次迁移态才认得它。
  assert.ok(
    WHITEBOARD_TEMPLATE.includes(
      "<!-- AUTO-GENERATED by .claude/scripts/sync_board_concepts.py",
    ),
    "模板的 ## Concepts 段必须自带 AUTO-GENERATED sentinel",
  );
  assert.ok(WHITEBOARD_TEMPLATE.includes("<!-- /AUTO-GENERATED n=0"));
  assert.ok(
    !WHITEBOARD_TEMPLATE.includes("本 section 由三处维护"),
    "旧「三处维护」注释必须已被替换（Concepts 现在是只读派生物）",
  );
});
