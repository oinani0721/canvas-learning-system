import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildNodeChatPrompt,
  byteLength,
  extractBodyWithoutFrontmatter,
  extractFrontmatterType,
  formatFrontmatterLines,
  isNodePath,
  type NodeChatContext,
  unicodeFirstN,
} from "../src/node-chat-context";

// ════════════════════════════════════════════════════════════════════
// extractBodyWithoutFrontmatter
// ════════════════════════════════════════════════════════════════════

test("extractBodyWithoutFrontmatter: 标准 frontmatter 剥离", () => {
  const md = "---\ntype: concept\nmastery_score: 0.5\n---\n\n本体内容\n第二段";
  assert.equal(
    extractBodyWithoutFrontmatter(md),
    "本体内容\n第二段",
  );
});

test("extractBodyWithoutFrontmatter: 无 frontmatter 原样返回", () => {
  const md = "# 标题\n纯正文";
  assert.equal(extractBodyWithoutFrontmatter(md), md);
});

test("extractBodyWithoutFrontmatter: 不闭合 frontmatter 返回原文（防 corruption）", () => {
  const md = "---\ntype: concept\n# 缺闭合";
  assert.equal(extractBodyWithoutFrontmatter(md), md);
});

// ════════════════════════════════════════════════════════════════════
// formatFrontmatterLines
// ════════════════════════════════════════════════════════════════════

test("formatFrontmatterLines: 全字段输出", () => {
  const out = formatFrontmatterLines({
    type: "concept",
    source_board: "[[原白板/线性代数]]",
    mastery_score: 0.3,
    relationships: [
      { type: "refines", target: "[[原白板/线性代数]]" },
    ],
  });
  assert.match(out, /类型: concept/);
  assert.match(out, /所属白板: \[\[原白板\/线性代数\]\]/);
  assert.match(out, /Mastery: 0\.30 🔴/);
  assert.match(out, /关系类型: refines/);
});

test("formatFrontmatterLines: mastery 颜色边界", () => {
  assert.match(formatFrontmatterLines({ mastery_score: 0.1 }), /🔴/);
  assert.match(formatFrontmatterLines({ mastery_score: 0.5 }), /🟡/);
  assert.match(formatFrontmatterLines({ mastery_score: 0.9 }), /🟢/);
});

test("formatFrontmatterLines: 缺字段不输出 undefined", () => {
  const out = formatFrontmatterLines({ type: "concept" });
  assert.equal(out, "类型: concept");
  assert.ok(!out.includes("undefined"));
});

test("formatFrontmatterLines: source_board 是对象 wikilink", () => {
  const out = formatFrontmatterLines({
    source_board: { link: "原白板/CS 61B", path: "原白板/CS 61B.md" },
  });
  assert.match(out, /所属白板: 原白板\/CS 61B/);
});

// ════════════════════════════════════════════════════════════════════
// buildNodeChatPrompt — 主要逻辑
// ════════════════════════════════════════════════════════════════════

const baseContext: NodeChatContext = {
  nodePath: "节点/Eigenvalues.md",
  nodeBasename: "Eigenvalues",
  frontmatter: {
    type: "concept",
    source_board: "[[原白板/线性代数]]",
    mastery_score: 0.3,
  },
  body: "特征值是线性代数中的核心概念。给定方阵 A，若存在非零向量 v 使 Av = λv，则 λ 是 A 的特征值。",
  neighbors: [
    {
      path: "节点/Linear-Independence",
      type: "concept",
      excerpt: "线性独立性是判断向量组能否互相线性表示的性质",
    },
  ],
};

test("buildNodeChatPrompt: 标准节点（含选中文 + 邻居）prompt 完整", () => {
  const ctx = { ...baseContext, selection: "Av = λv" };
  const result = buildNodeChatPrompt(ctx);
  assert.match(result.prompt, /^\/node-chat/);
  assert.match(result.prompt, /## 当前节点/);
  assert.match(result.prompt, /路径: 节点\/Eigenvalues\.md/);
  assert.match(result.prompt, /节点名: Eigenvalues/);
  assert.match(result.prompt, /## 节点正文/);
  assert.match(result.prompt, /Av = λv/);
  assert.match(result.prompt, /## 选中文/);
  assert.match(result.prompt, /## 1-hop 邻居（1 个/);
  assert.match(result.prompt, /\[\[节点\/Linear-Independence\]\] \(concept\)/);
  assert.match(result.prompt, /## 任务/);
  assert.equal(result.truncated, false);
  assert.ok(result.sizeBytes > 0);
});

test("buildNodeChatPrompt: 无选中文 → 跳过 ## 选中文 section", () => {
  const result = buildNodeChatPrompt(baseContext);
  assert.ok(!result.prompt.includes("## 选中文"));
});

test("buildNodeChatPrompt: 节点孤立（无邻居）→ 注明孤立概念", () => {
  const ctx: NodeChatContext = { ...baseContext, neighbors: [] };
  const result = buildNodeChatPrompt(ctx);
  assert.match(result.prompt, /## 1-hop 邻居（0 个/);
  assert.match(result.prompt, /（无关联节点 — 这是孤立概念）/);
  assert.equal(result.truncated, false);
});

test("buildNodeChatPrompt: 节点正文超大 → 截断 60% + 标记剩余字数", () => {
  // body = 6000 中文 = 18KB UTF-8。maxBytes 12KB 让第一阶段（body 60%）截断生效。
  // 60% body = 3600 中文 = 10.8KB + 模板 ~500B = ~11.3KB < 12KB，第一阶段标记保留。
  const longBody = "特征值".repeat(2000);
  const ctx: NodeChatContext = { ...baseContext, body: longBody };
  const result = buildNodeChatPrompt(ctx, { maxBytes: 12288 });
  assert.equal(result.truncated, true);
  assert.match(result.prompt, /\[\.\.\. 原文还有约 \d+ 字\]/);
  assert.ok(result.sizeBytes <= 12288);
  assert.ok(
    result.truncationReason !== undefined,
    "应记录 truncationReason",
  );
});

test("buildNodeChatPrompt: maxBytes 极小 → 第二阶段强制截断（80% maxBytes）", () => {
  // maxBytes 4096 太小，body 60% 截断后仍超 → 触发第二阶段强制 80% 截断
  const longBody = "特征值".repeat(2000);
  const ctx: NodeChatContext = { ...baseContext, body: longBody };
  const result = buildNodeChatPrompt(ctx, { maxBytes: 4096 });
  assert.equal(result.truncated, true);
  assert.match(result.prompt, /prompt 截断到 80% maxBytes/);
  assert.ok(result.sizeBytes <= 4096);
});

test("buildNodeChatPrompt: 5+ 邻居正常显示（无截断邻居数量限制 — 由 collectNeighbors 上游控制）", () => {
  const ctx: NodeChatContext = {
    ...baseContext,
    neighbors: Array.from({ length: 5 }).map((_, i) => ({
      path: `节点/Concept-${i}`,
      type: "concept",
      excerpt: `第 ${i} 个邻居的摘要内容`,
    })),
  };
  const result = buildNodeChatPrompt(ctx);
  assert.match(result.prompt, /## 1-hop 邻居（5 个/);
  for (let i = 0; i < 5; i++) {
    assert.ok(
      result.prompt.includes(`节点/Concept-${i}`),
      `邻居 ${i} 应在 prompt 中`,
    );
  }
});

test("buildNodeChatPrompt: 邻居 excerpt 含换行/连续空格 → 规范化为单空格", () => {
  const ctx: NodeChatContext = {
    ...baseContext,
    neighbors: [
      {
        path: "节点/Test",
        type: "concept",
        excerpt: "多 行\n\n摘要  内 容",
      },
    ],
  };
  const result = buildNodeChatPrompt(ctx);
  assert.ok(
    !result.prompt.includes("多 行\n\n摘要"),
    "换行应被规范化",
  );
  assert.match(result.prompt, /多 行 摘要 内 容/);
});

// ════════════════════════════════════════════════════════════════════
// 工具函数
// ════════════════════════════════════════════════════════════════════

test("byteLength: 中文 = 3 bytes / char", () => {
  assert.equal(byteLength("中文"), 6);
  assert.equal(byteLength("abc"), 3);
});

test("unicodeFirstN: 不破坏 surrogate pair", () => {
  const s = "🎯特征值🚀";
  const taken = unicodeFirstN(s, 2);
  assert.equal(taken, "🎯特");
});

test("isNodePath: 节点/ 起头 + .md 结尾", () => {
  assert.equal(isNodePath("节点/Eigenvalues.md"), true);
  assert.equal(isNodePath("节点/sub/Eigenvalues.md"), true);
  assert.equal(isNodePath("原白板/线性代数.md"), false);
  assert.equal(isNodePath("节点/Eigenvalues"), false);
  assert.equal(isNodePath(""), false);
});

// ════════════════════════════════════════════════════════════════════
// Story 2.1 P1.6 — isNodePath 配置化前缀 + path normalization
// ════════════════════════════════════════════════════════════════════

test("isNodePath: 自定义前缀（英文 vault 用 'Nodes/'）", () => {
  assert.equal(isNodePath("Nodes/Eigenvalues.md", ["Nodes/"]), true);
  assert.equal(isNodePath("节点/Eigenvalues.md", ["Nodes/"]), false);
  // 默认前缀不变
  assert.equal(isNodePath("节点/X.md"), true);
});

test("isNodePath: 多前缀同时支持", () => {
  const prefixes = ["节点/", "Nodes/"];
  assert.equal(isNodePath("节点/X.md", prefixes), true);
  assert.equal(isNodePath("Nodes/Y.md", prefixes), true);
  assert.equal(isNodePath("Other/Z.md", prefixes), false);
});

test("isNodePath: 前缀缺失尾部斜杠时自动补", () => {
  // "节点" 自动补成 "节点/"
  assert.equal(isNodePath("节点/X.md", ["节点"]), true);
  // 不会误匹配 "节点其他/"
  assert.equal(isNodePath("节点其他/X.md", ["节点"]), false);
});

test("isNodePath: path traversal escape (..) 被拒绝", () => {
  // 节点/../escape.md 经 normalizePath 后 = escape.md，不在 节点/ 下
  assert.equal(isNodePath("节点/../escape.md"), false);
  assert.equal(isNodePath("节点/sub/../../escape.md"), false);
  // 合法的 .. 段（不离开根）仍能被识别
  assert.equal(isNodePath("节点/sub/../X.md"), true);
});

test("isNodePath: Windows 反斜杠路径自动归一", () => {
  assert.equal(isNodePath("节点\\Eigenvalues.md"), true);
  assert.equal(isNodePath("节点\\sub\\X.md"), true);
});

test("isNodePath: 前导 ./ 或 / 自动剥离", () => {
  assert.equal(isNodePath("./节点/X.md"), true);
  assert.equal(isNodePath("/节点/X.md"), true);
  assert.equal(isNodePath("节点//X.md"), true);  // 重复斜杠
});

test("extractFrontmatterType: 取 type 字段或 undefined", () => {
  assert.equal(
    extractFrontmatterType({ type: "concept", source_board: "X" }),
    "concept",
  );
  assert.equal(extractFrontmatterType({ source_board: "X" }), undefined);
  assert.equal(extractFrontmatterType(undefined), undefined);
  assert.equal(extractFrontmatterType({ type: 42 }), undefined);
});
