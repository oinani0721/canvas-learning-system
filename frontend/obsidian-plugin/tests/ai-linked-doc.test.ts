import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildAIDocPrompt,
  isBoardsPath,
  isNodesPath,
  isFlatArchPath,
  extractBoardNameFromPath,
} from "../src/ai-linked-doc";

test("buildAIDocPrompt v4: 首行 slash + 显式 Skill 调用指令", () => {
  const out = buildAIDocPrompt(
    "Eigenvalues are special vectors",
    "原白板/CS 61B 数据结构.md",
    "CS 61B 数据结构",
  );
  assert.ok(out.startsWith("/ai-linked-doc\n"), "首行必须是 slash 命令");
  assert.ok(
    out.includes('Please invoke the Skill tool with skill_name="ai-linked-doc"'),
    "必须含显式 Skill 工具调用指令",
  );
  assert.ok(
    out.includes("Do NOT answer freely"),
    "必须含 Do NOT answer freely 硬约束",
  );
  assert.ok(
    out.includes("8-step Skill flow"),
    "v4 是 8 步 Skill 流程",
  );
});

test("buildAIDocPrompt v4: 活动白板字段注入", () => {
  const out = buildAIDocPrompt(
    "文本",
    "原白板/线性代数.md",
    "线性代数",
  );
  assert.ok(
    out.includes("活动白板: 线性代数\n"),
    "活动白板字段注入",
  );
});

test("buildAIDocPrompt v4: 活动白板未知时 Skill 会自行 AskUserQuestion", () => {
  const out = buildAIDocPrompt("文本", "raw/notes.md");
  assert.ok(
    out.includes("活动白板: (Skill 会从 .canvas-config.yaml 或 AskUserQuestion 确定)"),
    "未传 activeBoard → fallback 文案",
  );
});

test("buildAIDocPrompt v4: 扁平架构结尾指令（节点/ + 原白板/）", () => {
  const out = buildAIDocPrompt("x", "原白板/Test.md", "Test");
  assert.ok(
    out.endsWith("扁平架构：节点/<concept>.md + 更新 原白板/<active_board>.md 的 ## Concepts）。"),
    "结尾必须指明扁平架构路径",
  );
});

test("buildAIDocPrompt v4: 多行选中文本保留换行", () => {
  const selected = "第一行\n第二行\n第三行";
  const out = buildAIDocPrompt(selected, "原白板/X.md", "X");
  assert.ok(
    out.includes("选中文本:\n第一行\n第二行\n第三行\n\n"),
    "多行原样保留",
  );
});

test("isBoardsPath: 判断源笔记在 原白板/ 下", () => {
  assert.equal(isBoardsPath("原白板/CS 61B.md"), true);
  assert.equal(isBoardsPath("原白板/线性代数.md"), true);
  assert.equal(isBoardsPath("节点/recursion.md"), false);
  assert.equal(isBoardsPath("raw/notes.md"), false);
  assert.equal(isBoardsPath("unknown"), false);
  assert.equal(
    isBoardsPath("wiki/canvases/cs-61b/index.md"),
    false,
    "弃用路径应 false",
  );
});

test("isNodesPath: 判断源笔记在 节点/ 下", () => {
  assert.equal(isNodesPath("节点/recursion.md"), true);
  assert.equal(isNodesPath("节点/递归.md"), true, "中文节点名");
  assert.equal(isNodesPath("原白板/X.md"), false);
  assert.equal(isNodesPath("raw/notes.md"), false);
  assert.equal(
    isNodesPath("wiki/concepts/old.md"),
    false,
    "弃用路径应 false",
  );
});

test("isFlatArchPath: 判断是否在扁平架构路径下（原白板/ 或 节点/）", () => {
  assert.equal(isFlatArchPath("原白板/CS 61B.md"), true);
  assert.equal(isFlatArchPath("节点/base-case.md"), true);
  assert.equal(isFlatArchPath("raw/notes.md"), false);
  assert.equal(isFlatArchPath("未命名.md"), false);
  assert.equal(
    isFlatArchPath("wiki/canvases/cs-61b/index.md"),
    false,
    "弃用 v2 路径",
  );
});

test("extractBoardNameFromPath: 从 原白板/<name>.md 提取 board_name", () => {
  assert.equal(
    extractBoardNameFromPath("原白板/CS 61B 数据结构.md"),
    "CS 61B 数据结构",
  );
  assert.equal(
    extractBoardNameFromPath("原白板/线性代数.md"),
    "线性代数",
  );
  assert.equal(
    extractBoardNameFromPath("节点/recursion.md"),
    null,
    "节点路径返回 null",
  );
  assert.equal(
    extractBoardNameFromPath("raw/notes.md"),
    null,
    "raw 路径返回 null",
  );
});
