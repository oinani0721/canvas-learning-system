import { test } from "node:test";
import assert from "node:assert/strict";
import { buildAIDocPrompt, isCanvasesPath } from "../src/ai-linked-doc";

test("buildAIDocPrompt: 首行 slash + 显式 Skill 调用指令 (v2.1 强化)", () => {
  const out = buildAIDocPrompt(
    "Eigenvalues are special vectors",
    "wiki/canvases/math240/Fundamentals.md",
    "math240",
  );
  assert.ok(out.startsWith("/ai-linked-doc\n"), "首行必须是 slash 命令");
  assert.ok(
    out.includes('Please invoke the Skill tool with skill_name="ai-linked-doc"'),
    "必须含显式 Skill 工具调用指令（对抗 Claude 自由对话）",
  );
  assert.ok(
    out.includes("Do NOT answer freely"),
    "必须含 Do NOT answer freely 硬约束",
  );
  assert.ok(
    out.includes("选中文本:\nEigenvalues are special vectors\n\n"),
    "选中文本段落",
  );
  assert.ok(
    out.includes("源笔记路径: wiki/canvases/math240/Fundamentals.md\n"),
    "源笔记路径",
  );
  assert.ok(out.includes("学科: math240\n\n"), "学科字段");
  assert.ok(
    out.endsWith("三段式：## 核心概念 / ## 关键点 / ## 关联概念）。"),
    "指令结尾",
  );
});

test("buildAIDocPrompt: frontmatter 缺 subject → 填 'unknown'", () => {
  const out = buildAIDocPrompt("任意文本", "unknown", "unknown");
  assert.ok(
    out.includes("学科: unknown\n"),
    "unknown subject 用于 Skill 侧 AskUserQuestion 降级",
  );
  assert.ok(
    out.includes("源笔记路径: unknown\n"),
    "sourcePath 缺失时也用 unknown",
  );
});

test("buildAIDocPrompt: 选中文本含 markdown 语法 (粗体 / 斜体 / 行内代码) 保留原样", () => {
  const selected = "**Eigenvalues** are _special_ vectors: `Av = λv`";
  const out = buildAIDocPrompt(
    selected,
    "wiki/canvases/math240/Linear.md",
    "math240",
  );
  assert.ok(
    out.includes(
      "选中文本:\n**Eigenvalues** are _special_ vectors: `Av = λv`\n\n",
    ),
    "markdown 语法字符不被转义",
  );
});

test("buildAIDocPrompt: 多行选中文本保留换行", () => {
  const selected = "第一行\n第二行\n第三行";
  const out = buildAIDocPrompt(selected, "p.md", "s");
  assert.ok(
    out.includes("选中文本:\n第一行\n第二行\n第三行\n\n"),
    "多行原样保留",
  );
});

test("isCanvasesPath: 判断源笔记是否在 wiki/canvases/ 路径下", () => {
  assert.equal(
    isCanvasesPath("wiki/canvases/math240/Fundamentals.md"),
    true,
    "canvases 子路径应返回 true",
  );
  assert.equal(
    isCanvasesPath("wiki/canvases/default/Concept.md"),
    true,
    "canvases default 子路径应返回 true",
  );
  assert.equal(isCanvasesPath("unknown"), false, "unknown 应返回 false");
  assert.equal(
    isCanvasesPath("未命名.md"),
    false,
    "vault 根的文件应返回 false",
  );
  assert.equal(
    isCanvasesPath("wiki/concepts/xxx.md"),
    false,
    "concepts 路径（非 canvases）应返回 false",
  );
  assert.equal(
    isCanvasesPath("raw/xxx.md"),
    false,
    "raw 路径应返回 false",
  );
});
