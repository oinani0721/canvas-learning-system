/**
 * MVP-α-3 (2026-05-14) — exam-quick.ts unit tests.
 *
 * 用户场景:
 *   1. active file = 节点/递归.md → Quick Exam 命令 → 生成 节点/考察-递归-{date}.md
 *   2. 用户手写答案 → vault.on('modify') → backend grade → 文件底部追加反馈
 *
 * 覆盖 (pure helpers + main.ts wiring spec-as-test):
 *   T1. buildExamFilePath — concept/date/suffix 组合 + 空白处理
 *   T2. todayDateStr — YYYY-MM-DD 提取
 *   T3. buildExamFileBody — 完整 markdown 协议 (frontmatter + 题目 + 回答 + 提交)
 *   T4. extractAnswer — 从 ## 你的回答 段抽取, 占位符 → null
 *   T5. hasFeedbackSection — 防重复 grade 守门
 *   T6. buildFeedbackAppend — 反馈区文案 + score clamp [0,5]
 *   T7. main.ts 已 wire QuickExamController + 命令 + vault.on('modify')
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  buildExamFileBody,
  buildExamFilePath,
  buildFeedbackAppend,
  extractAnswer,
  hasFeedbackSection,
  todayDateStr,
} from "../src/exam-quick";

// ─────────────────────────────────────────────────────────────
// T1. buildExamFilePath
// ─────────────────────────────────────────────────────────────

describe("buildExamFilePath", () => {
  test("基础: 节点/考察-{concept}-{date}.md", () => {
    assert.strictEqual(
      buildExamFilePath("递归", "2026-05-14"),
      "节点/考察-递归-2026-05-14.md",
    );
  });

  test("suffix=0 不附加 (undefined 等价)", () => {
    assert.strictEqual(
      buildExamFilePath("递归", "2026-05-14", 0),
      "节点/考察-递归-2026-05-14.md",
    );
  });

  test("suffix=1 附加 -1 (重名递增)", () => {
    assert.strictEqual(
      buildExamFilePath("递归", "2026-05-14", 1),
      "节点/考察-递归-2026-05-14-1.md",
    );
  });

  test("concept 含空白 → 替换 -", () => {
    assert.strictEqual(
      buildExamFilePath("base case", "2026-05-14"),
      "节点/考察-base-case-2026-05-14.md",
    );
  });

  test("英文 concept", () => {
    assert.strictEqual(
      buildExamFilePath("factorial", "2026-05-14"),
      "节点/考察-factorial-2026-05-14.md",
    );
  });

  test("concept 空字符串 → 'unknown' fallback", () => {
    const path = buildExamFilePath("", "2026-05-14");
    assert.ok(path.includes("unknown"));
  });
});

// ─────────────────────────────────────────────────────────────
// T2. todayDateStr
// ─────────────────────────────────────────────────────────────

describe("todayDateStr", () => {
  test("固定日期 ISO 前 10 字符", () => {
    const fixed = new Date("2026-05-14T10:30:00Z");
    assert.strictEqual(todayDateStr(fixed), "2026-05-14");
  });

  test("跨年边界", () => {
    const fixed = new Date("2027-01-01T00:00:00Z");
    assert.strictEqual(todayDateStr(fixed), "2027-01-01");
  });

  test("无参数 → 现在 (YYYY-MM-DD 格式校验)", () => {
    const today = todayDateStr();
    assert.match(today, /^\d{4}-\d{2}-\d{2}$/);
  });
});

// ─────────────────────────────────────────────────────────────
// T3. buildExamFileBody
// ─────────────────────────────────────────────────────────────

describe("buildExamFileBody", () => {
  test("含 frontmatter 5 字段 (exam_question_id / source_concept / generated_at / exam_status)", () => {
    const body = buildExamFileBody({
      concept: "递归",
      questionId: "q-uuid-123",
      questionText: "请说说 base case 的作用",
      generatedAt: "2026-05-14T10:00:00Z",
    });
    assert.match(body, /^---\n/);
    assert.ok(body.includes("exam_question_id: q-uuid-123"));
    assert.ok(body.includes("source_concept: 递归"));
    assert.ok(body.includes("generated_at: 2026-05-14T10:00:00Z"));
    assert.ok(body.includes("exam_status: pending"));
  });

  test("含协议 4 段 (# 考察 / ## 题目 / ## 你的回答 / ## 提交)", () => {
    const body = buildExamFileBody({
      concept: "递归",
      questionId: "q1",
      questionText: "题目内容",
    });
    assert.ok(body.includes("# 考察: 递归"));
    assert.ok(body.includes("## 题目"));
    assert.ok(body.includes("## 你的回答"));
    assert.ok(body.includes("## 提交"));
    assert.ok(body.includes("[在此填写]"));
  });

  test("question_text 被 trim", () => {
    const body = buildExamFileBody({
      concept: "X",
      questionId: "q1",
      questionText: "  \n带空白的题目  \n  ",
    });
    assert.ok(body.includes("带空白的题目"));
    assert.ok(!body.includes("  \n带空白"), "前导空白应被 trim");
  });

  test("generatedAt 缺省时填当前时间 ISO", () => {
    const body = buildExamFileBody({
      concept: "X",
      questionId: "q1",
      questionText: "Q",
    });
    assert.match(body, /generated_at: \d{4}-\d{2}-\d{2}T/);
  });
});

// ─────────────────────────────────────────────────────────────
// T4. extractAnswer
// ─────────────────────────────────────────────────────────────

describe("extractAnswer", () => {
  test("提取 ## 你的回答 到 ## 提交 之间的内容", () => {
    const content = `# 考察
## 题目
题
## 你的回答

我认为 base case 是递归终止条件

## 提交
xxx`;
    assert.strictEqual(
      extractAnswer(content),
      "我认为 base case 是递归终止条件",
    );
  });

  test("用户未替换占位符 → null", () => {
    const content = `## 你的回答

[在此填写]

## 提交`;
    assert.strictEqual(extractAnswer(content), null);
  });

  test("回答区完全空 → null", () => {
    const content = `## 你的回答


## 提交`;
    assert.strictEqual(extractAnswer(content), null);
  });

  test("用户保留占位符 + 加内容 → 剔除占位符行", () => {
    const content = `## 你的回答

[在此填写]
其实我懂了 base case = 终止条件

## 提交`;
    assert.strictEqual(
      extractAnswer(content),
      "其实我懂了 base case = 终止条件",
    );
  });

  test("文件不含 ## 你的回答 → null", () => {
    assert.strictEqual(extractAnswer("# 标题\n内容"), null);
  });

  test("多行回答 (含换行) 保留段内换行", () => {
    const content = `## 你的回答

第一行
第二行
第三行

## 提交`;
    assert.strictEqual(extractAnswer(content), "第一行\n第二行\n第三行");
  });

  test("回答后没有 ## 提交 标题 (用户删了) → 抽到文件末", () => {
    const content = `## 你的回答

我的答案`;
    assert.strictEqual(extractAnswer(content), "我的答案");
  });
});

// ─────────────────────────────────────────────────────────────
// T5. hasFeedbackSection
// ─────────────────────────────────────────────────────────────

describe("hasFeedbackSection", () => {
  test("含 ## 反馈 (4/5) → true", () => {
    assert.strictEqual(
      hasFeedbackSection("## 题目\n...\n## 反馈 (4/5)\n好评"),
      true,
    );
  });

  test("不含 → false", () => {
    assert.strictEqual(hasFeedbackSection("## 题目\n## 你的回答"), false);
  });

  test("含 '反馈' 但不是 ## 段标题 → false (避免误判)", () => {
    assert.strictEqual(
      hasFeedbackSection("用户在反馈中提到..."),
      false,
    );
  });

  test("含 ## 反馈 (无评分括号) → true (容错)", () => {
    assert.strictEqual(hasFeedbackSection("## 反馈\n内容"), true);
  });
});

// ─────────────────────────────────────────────────────────────
// T6. buildFeedbackAppend
// ─────────────────────────────────────────────────────────────

describe("buildFeedbackAppend", () => {
  test("标准 4/5 + 反馈文本", () => {
    const text = buildFeedbackAppend({ score: 4, feedback: "答得不错" });
    assert.ok(text.includes("## 反馈 (4/5)"));
    assert.ok(text.includes("答得不错"));
    assert.ok(text.startsWith("\n\n"), "前置双换行避免粘连前文");
  });

  test("score > 5 被 clamp 到 5", () => {
    const text = buildFeedbackAppend({ score: 9, feedback: "x" });
    assert.ok(text.includes("(5/5)"));
  });

  test("score < 0 被 clamp 到 0", () => {
    const text = buildFeedbackAppend({ score: -2, feedback: "x" });
    assert.ok(text.includes("(0/5)"));
  });

  test("score 小数被 round", () => {
    const text = buildFeedbackAppend({ score: 3.7, feedback: "x" });
    assert.ok(text.includes("(4/5)"));
  });

  test("feedback 空 → fallback 文案", () => {
    const text = buildFeedbackAppend({ score: 3, feedback: "" });
    assert.ok(text.includes("后端未返回文字反馈"));
  });
});

// ─────────────────────────────────────────────────────────────
// T7. main.ts 已 wire QuickExam (spec-as-test)
// ─────────────────────────────────────────────────────────────

describe("main_ts_wires_quick_exam", () => {
  const mainPath = join(process.cwd(), "src", "main.ts");
  const mainTs = readFileSync(mainPath, "utf-8");

  test("import QuickExamController from ./exam-quick", () => {
    assert.match(
      mainTs,
      /import\s*\{\s*QuickExamController\s*\}\s*from\s*["']\.\/exam-quick["']/,
      "main.ts 必须 import QuickExamController",
    );
  });

  test("import inferVaultId from ./error-candidate-helpers (Story 2.5.Y vault_id 推断)", () => {
    assert.match(
      mainTs,
      /import\s*\{\s*inferVaultId\s*\}\s*from\s*["']\.\/error-candidate-helpers["']/,
    );
  });

  test("onload new QuickExamController + 接 callBackend 闭包", () => {
    assert.match(
      mainTs,
      /new\s+QuickExamController\s*\(\s*\{[\s\S]{0,400}?callBackendJson[\s\S]{0,200}?this\.callBackend/,
      "main.ts 必须 new QuickExamController 并把 callBackendJson 绑到 this.callBackend",
    );
  });

  test("addCommand 注册 canvas:start-quick-exam", () => {
    assert.match(
      mainTs,
      /id:\s*["']canvas:start-quick-exam["']/,
      "命令 ID canvas:start-quick-exam 未注册 — 命令面板看不到 Quick Exam",
    );
  });

  test("命令 callback 调 quickExam.startExam(Notice)", () => {
    assert.match(
      mainTs,
      /quickExam\.startExam\s*\(\s*Notice\s*\)/,
      "命令必须把 Notice constructor 注入 controller (避免顶部 import 渗透到 pure module)",
    );
  });

  test("vault.on('modify') 分发到 quickExam.onFileModified", () => {
    assert.match(
      mainTs,
      /vault\.on\s*\(\s*["']modify["'][\s\S]{0,400}?quickExam\.onFileModified/,
      "vault 'modify' 事件必须接到 quickExam.onFileModified (评分触发口)",
    );
  });
});
