import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildBoardActivityLine,
  buildBoardConceptsLine,
  buildNodeBody,
  buildNodeFrontmatter,
  buildSourceReplacement,
  deriveConceptStub,
  getRelationCnLabel,
  resolveUniqueNodeName,
} from "../src/node-derivation";

// ════════════════════════════════════════════════════════════════════
// deriveConceptStub — 启发式从选中文本提取概念名
// ════════════════════════════════════════════════════════════════════

test("deriveConceptStub: 中文短句取整句作 stub", () => {
  const stub = deriveConceptStub("特征值是矩阵特殊向量");
  assert.equal(stub, "特征值是矩阵特殊向量");
});

test("deriveConceptStub: 中文长句按句号截断", () => {
  const stub = deriveConceptStub("特征值是矩阵特殊向量。还有更多内容。");
  assert.equal(stub, "特征值是矩阵特殊向量");
});

test("deriveConceptStub: 英文按空格 → kebab", () => {
  const stub = deriveConceptStub("Eigenvalues are special vectors");
  assert.equal(stub, "Eigenvalues-are-special-vectors");
});

test("deriveConceptStub: 英文按句号截断 + kebab", () => {
  const stub = deriveConceptStub(
    "Eigenvalues are special. Definition next.",
  );
  assert.equal(stub, "Eigenvalues-are-special");
});

test("deriveConceptStub: 非法字符被移除（注意 ? 同时是句号边界）", () => {
  const stub = deriveConceptStub("a/b\\c:d*ef");
  assert.ok(!/[\\/:*?"<>|]/.test(stub), "非法字符应被清除");
  assert.equal(stub, "abcdef");
});

test("deriveConceptStub: 选中文本超过 40 字符 → unicode-aware 截断", () => {
  const long = "特征值".repeat(20);
  const stub = deriveConceptStub(long);
  assert.equal(Array.from(stub).length, 40, "应按 unicode 字符 40 截断");
});

test("deriveConceptStub: 空字符串 → fallback derived-<timestamp>", () => {
  const stub = deriveConceptStub("");
  assert.match(stub, /^derived-\d{6}$/);
});

test("deriveConceptStub: 全非法字符 → fallback", () => {
  const stub = deriveConceptStub("///\\\\???");
  assert.match(stub, /^derived-\d{6}$/);
});

test("deriveConceptStub: 中英混合保留", () => {
  const stub = deriveConceptStub("Eigenvalue 特征值 definition");
  assert.equal(stub, "Eigenvalue-特征值-definition");
});

test("deriveConceptStub: 多个换行视为句号边界", () => {
  const stub = deriveConceptStub("第一行\n第二行\n第三行");
  assert.equal(stub, "第一行");
});

// ════════════════════════════════════════════════════════════════════
// resolveUniqueNodeName — 节点池重名处理
// ════════════════════════════════════════════════════════════════════

test("resolveUniqueNodeName: 不冲突 → 原 stub", () => {
  const result = resolveUniqueNodeName("foo", () => false);
  assert.equal(result, "foo");
});

test("resolveUniqueNodeName: 冲突 1 次 → _2", () => {
  const existing = new Set(["节点/foo.md"]);
  const result = resolveUniqueNodeName("foo", (p) => existing.has(p));
  assert.equal(result, "foo_2");
});

test("resolveUniqueNodeName: 冲突 1+2 → _3", () => {
  const existing = new Set(["节点/foo.md", "节点/foo_2.md"]);
  const result = resolveUniqueNodeName("foo", (p) => existing.has(p));
  assert.equal(result, "foo_3");
});

test("resolveUniqueNodeName: 占满 1-9 → 抛错", () => {
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
    resolveUniqueNodeName("foo", (p) => existing.has(p));
  }, /9\+ 重名/);
});

// ════════════════════════════════════════════════════════════════════
// getRelationCnLabel — 7 类中文映射
// ════════════════════════════════════════════════════════════════════

test("getRelationCnLabel: 7 类合法 key 都返中文", () => {
  assert.equal(getRelationCnLabel("prerequisite"), "先修");
  assert.equal(getRelationCnLabel("depends_on"), "依赖");
  assert.equal(getRelationCnLabel("refines"), "细化");
  assert.equal(getRelationCnLabel("extends"), "扩展");
  assert.equal(getRelationCnLabel("example_of"), "例子");
  assert.equal(getRelationCnLabel("contradicts"), "反驳");
  assert.equal(getRelationCnLabel("related_to"), "相关");
});

test("getRelationCnLabel: 未知 key → 兜底返原值", () => {
  assert.equal(getRelationCnLabel("unknown_xyz"), "unknown_xyz");
});

// ════════════════════════════════════════════════════════════════════
// buildSourceReplacement — v4.1 保留原文 + 关系 callout
// ════════════════════════════════════════════════════════════════════

test("buildSourceReplacement v4.1: 原文 100% 保留（不再删除）", () => {
  const selected = "Eigenvalues are special vectors that satisfy Av = λv";
  const out = buildSourceReplacement("foo", "refines", "", selected);
  assert.ok(out.includes(selected), "原文必须完整保留");
  assert.ok(out.startsWith(selected), "原文应在第一行（不被 callout 包住）");
});

test("buildSourceReplacement v4.1: 描述空 → 4 行（原文 + 空行 + callout 2 行）", () => {
  const out = buildSourceReplacement("foo", "refines", "", "原文 X");
  const lines = out.split("\n");
  assert.equal(lines.length, 4, "空描述应 4 行");
  assert.equal(lines[0], "原文 X", "首行 = 原文");
  assert.equal(lines[1], "", "第 2 行空行");
  assert.equal(
    lines[2],
    "> [!relation/refines]+ 已派生为 [[节点/foo]] · 细化",
    "第 3 行 callout 标题含 wikilink + 关系标签",
  );
  assert.match(lines[3], /^> 这段文本已被派生为独立讨论节点/);
});

test("buildSourceReplacement v4.1: 描述非空 → 5 行（多 1 行用户意图）", () => {
  const out = buildSourceReplacement(
    "foo",
    "extends",
    "为了梳理求解步骤",
    "原文",
  );
  const lines = out.split("\n");
  assert.equal(lines.length, 5, "非空描述应 5 行");
  assert.equal(lines[4], "> 你的派生意图: 为了梳理求解步骤");
});

test("buildSourceReplacement v4.1: 描述 + 选中文本前后空白都 trim", () => {
  const out = buildSourceReplacement(
    "foo",
    "refines",
    "   多余空白   ",
    "  原文带空白  ",
  );
  assert.ok(out.startsWith("原文带空白\n"), "原文 trim");
  assert.ok(
    out.includes("> 你的派生意图: 多余空白"),
    "描述 trim",
  );
});

test("buildSourceReplacement v4.1: callout 标题用'已派生为'（不是'上方 wikilink'）", () => {
  const out = buildSourceReplacement("foo", "refines", "", "x");
  assert.ok(out.includes("已派生为 [[节点/foo]]"));
  assert.ok(!out.includes("上方 wikilink"), "v4.0 旧文案被替换");
});

// ════════════════════════════════════════════════════════════════════
// buildNodeFrontmatter — 节点 frontmatter 数据对象
// ════════════════════════════════════════════════════════════════════

test("buildNodeFrontmatter: 空描述 → relationships[0] 不含 description", () => {
  const fm = buildNodeFrontmatter({
    sourceNoteStem: "Fundamentals",
    activeBoard: "线性代数",
    relationKey: "refines",
    description: "",
    createdAt: "2026-04-30T10:00:00Z",
  });
  assert.equal(fm.type, "concept");
  assert.equal(fm.mastery_score, 0.3);
  assert.equal(fm.source_note, "[[Fundamentals]]");
  assert.equal(fm.source_board, "[[原白板/线性代数]]");
  assert.equal(
    (fm as Record<string, unknown>).status,
    undefined,
    "v4.0 起去掉 status 字段（无 AI 阶段）",
  );
  assert.equal(fm.relationships.length, 1);
  assert.equal(fm.relationships[0].type, "refines");
  assert.equal(fm.relationships[0].target, "[[Fundamentals]]");
  assert.equal(
    fm.relationships[0].description,
    undefined,
    "空描述应不写 description 字段",
  );
});

test("buildNodeFrontmatter: 非空描述 → relationships[0].description 含原文", () => {
  const fm = buildNodeFrontmatter({
    sourceNoteStem: "Fundamentals",
    activeBoard: "线性代数",
    relationKey: "extends",
    description: "为了单独梳理特征方程",
    createdAt: "2026-04-30T10:00:00Z",
  });
  assert.equal(fm.relationships[0].description, "为了单独梳理特征方程");
});

// ════════════════════════════════════════════════════════════════════
// buildNodeBody — v4.0 节点正文（无 AI 生成，三段空白模板）
// ════════════════════════════════════════════════════════════════════

test("buildNodeBody: 含 # 概念名 标题", () => {
  const body = buildNodeBody("特征方程", "x", "Fundamentals");
  assert.ok(body.startsWith("# 特征方程\n"));
});

test("buildNodeBody: 选中文本作 [!quote]+ callout（友好显示原文）", () => {
  const body = buildNodeBody("foo", "Eigenvalue definition", "Fundamentals");
  assert.ok(
    body.includes("[!quote]+ 派生起点"),
    "用 quote callout 显示原文（不是 SELECTED_TEXT 注释）",
  );
  assert.ok(body.includes("[[Fundamentals]]"), "callout 标题含源笔记 wikilink");
  assert.ok(body.includes("Eigenvalue definition"), "选中文本嵌入");
});

test("buildNodeBody: 选中文本含换行 → 多行 quote", () => {
  const body = buildNodeBody("foo", "第一行\n第二行", "Src");
  assert.ok(body.includes("> 第一行\n> 第二行"), "换行被 > 前缀");
});

test("buildNodeBody: 三段空白模板（核心概念 / 关键点 / 关联概念）", () => {
  const body = buildNodeBody("foo", "x", "Src");
  assert.ok(body.includes("## 核心概念"));
  assert.ok(body.includes("## 关键点"));
  assert.ok(body.includes("## 关联概念"));
});

test("buildNodeBody: 关联概念预填源笔记 wikilink", () => {
  const body = buildNodeBody("foo", "x", "Fundamentals");
  assert.ok(body.includes("- [[Fundamentals]] — extracted from this note"));
});

test("buildNodeBody: 含讨论容器 tip callout（解释节点定位）", () => {
  const body = buildNodeBody("foo", "x", "Src");
  assert.ok(
    body.includes("讨论容器"),
    "明确告诉用户节点是讨论容器（不是 AI 生成内容）",
  );
  assert.ok(body.includes("Cmd+Shift+D"), "提示派生子节点快捷键");
  assert.ok(body.includes("Cmd+Shift+A"), "提示批注快捷键");
});

test("buildNodeBody: 不含 AI_BODY_PLACEHOLDER / SELECTED_TEXT 注释（v4.0 砍掉）", () => {
  const body = buildNodeBody("foo", "x", "Src");
  assert.ok(!body.includes("AI_BODY_PLACEHOLDER"), "v4.0 无 AI 占位符");
  assert.ok(!body.includes("SELECTED_TEXT_START"), "v4.0 无 SELECTED_TEXT 注释");
  assert.ok(!body.includes("AI 正在生成"), "v4.0 无 AI 生成承诺");
  assert.ok(!body.includes("ai_pending"), "v4.0 无状态机字段");
});

// ════════════════════════════════════════════════════════════════════
// buildBoardConceptsLine + buildBoardActivityLine — 白板更新行
// ════════════════════════════════════════════════════════════════════

test("buildBoardConceptsLine: v4.0 无 ai_pending 后缀（因为不再有 AI 阶段）", () => {
  const line = buildBoardConceptsLine("foo", "refines");
  assert.equal(line, "- [[节点/foo]] — refines, weak (0.30)");
  assert.ok(!line.includes("ai_pending"), "v4.0 砍掉 ai_pending 状态");
  assert.ok(!line.includes("⏳"), "v4.0 砍掉 ⏳ 进行中符号");
});

test("buildBoardActivityLine: v4.0 含 ISO 时间 + 关系 (无 status)", () => {
  const line = buildBoardActivityLine(
    "foo",
    "源笔记",
    "extends",
    "2026-04-30T10:00:00Z",
  );
  assert.match(line, /^- 2026-04-30T10:00:00Z: Extracted/);
  assert.ok(line.includes("[[节点/foo]]"));
  assert.ok(line.includes("[[源笔记]]"));
  assert.ok(line.includes("关系: extends"));
  assert.ok(!line.includes("status: ai_pending"), "v4.0 砍掉 status 字段");
  assert.ok(line.includes("canvas:ai-linked-doc"), "v4.0 用 plugin 命令名");
});
