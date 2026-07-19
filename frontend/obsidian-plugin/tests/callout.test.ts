import { test } from "node:test";
import assert from "node:assert/strict";
import {
  TAG_OPTIONS,
  UNDERSTANDING_OPTIONS,
  parseCalloutsFromContent,
  wrapSelection,
  generateAnnotationId,
  buildNewQuestionCallout,
  NEW_QUESTION_PROMPT,
  NEW_QUESTION_PLACEHOLDER,
  computeInsertionSpacing,
} from "../src/callout";

test("TAG_OPTIONS exposes 4 semantic tags (tips/error/question/keypoint)", () => {
  assert.deepEqual(
    TAG_OPTIONS.map((t) => t.value),
    ["tips", "error", "question", "keypoint"],
  );
});

test("TAG_OPTIONS each has emoji label and matching callout id", () => {
  for (const t of TAG_OPTIONS) {
    assert.equal(t.value, t.callout);
    assert.ok(t.label.includes(t.value === "tips" ? "Tips" : t.value === "error" ? "错误" : t.value === "question" ? "提问" : "关键点"));
  }
});

test("UNDERSTANDING_OPTIONS exposes 3 levels (understood/fuzzy/not-understood)", () => {
  assert.deepEqual(
    UNDERSTANDING_OPTIONS.map((u) => u.value),
    ["understood", "fuzzy", "not-understood"],
  );
});

test("wrapSelection: tips + fuzzy produces callout with 3 checkboxes (fuzzy checked)", () => {
  const tips = TAG_OPTIONS[0];
  const out = wrapSelection("hello", tips, "fuzzy");
  assert.equal(
    out,
    "> [!tips]+ 💡 Tips\n" +
      "> - [ ] ✅ 已懂\n" +
      "> - [x] 🤔 模糊\n" +
      "> - [ ] ❌ 不懂\n" +
      ">\n" +
      "> hello\n" +
      ">\n" +
      "> ✍️ 我的理解：",
  );
});

test("wrapSelection: error + understood (understood checked)", () => {
  const error = TAG_OPTIONS[1];
  const out = wrapSelection("bad logic", error, "understood");
  assert.equal(
    out,
    "> [!error]+ ❌ 错误\n" +
      "> - [x] ✅ 已懂\n" +
      "> - [ ] 🤔 模糊\n" +
      "> - [ ] ❌ 不懂\n" +
      ">\n" +
      "> bad logic\n" +
      ">\n" +
      "> ✍️ 我的理解：",
  );
});

test("wrapSelection: question + not-understood (not-understood checked) + multi-line body", () => {
  const question = TAG_OPTIONS[2];
  const out = wrapSelection("line1\nline2", question, "not-understood");
  assert.equal(
    out,
    "> [!question]+ ❓ 提问\n" +
      "> - [ ] ✅ 已懂\n" +
      "> - [ ] 🤔 模糊\n" +
      "> - [x] ❌ 不懂\n" +
      ">\n" +
      "> line1\n" +
      "> line2\n" +
      ">\n" +
      "> ✍️ 我的理解：",
  );
});

test("wrapSelection: keypoint + fuzzy + blank line in body (blank line kept as `> `)", () => {
  const keypoint = TAG_OPTIONS[3];
  const out = wrapSelection("a\n\nb", keypoint, "fuzzy");
  assert.equal(
    out,
    "> [!keypoint]+ 📌 关键点\n" +
      "> - [ ] ✅ 已懂\n" +
      "> - [x] 🤔 模糊\n" +
      "> - [ ] ❌ 不懂\n" +
      ">\n" +
      "> a\n" +
      "> \n" +
      "> b\n" +
      ">\n" +
      "> ✍️ 我的理解：",
  );
});

test("wrapSelection: all 4 tags × all 3 levels = 12 combinations produce valid callout", () => {
  for (const tag of TAG_OPTIONS) {
    for (const und of UNDERSTANDING_OPTIONS) {
      const out = wrapSelection("x", tag, und.value);
      assert.ok(
        out.startsWith(`> [!${tag.callout}]+ ${tag.label}\n`),
        `header not matched for ${tag.value}/${und.value}`,
      );
      assert.ok(
        out.includes(`> - [x] ${und.label}`),
        `checked box missing for ${und.value}`,
      );
      assert.ok(
        out.endsWith("> x\n>\n> ✍️ 我的理解："),
        `body incorrect for ${tag.value}/${und.value}`,
      );

      const uncheckedCount = (out.match(/> - \[ \]/g) || []).length;
      const checkedCount = (out.match(/> - \[x\]/g) || []).length;
      assert.equal(uncheckedCount, 2, `expected 2 unchecked for ${und.value}`);
      assert.equal(checkedCount, 1, `expected 1 checked for ${und.value}`);
    }
  }
});

test("wrapSelection: pure whitespace line preserved", () => {
  const tips = TAG_OPTIONS[0];
  const out = wrapSelection("  ", tips, "understood");
  assert.ok(out.endsWith(">\n>   \n>\n> ✍️ 我的理解："));
});

// ═══════════════════════════════════════════════════════════════════════════════
// 实测修复 (2026-06-11): 列表嵌套批注 `* > [!tips]+` — 用户真实格式 (lecture 2.md:89)
// 旧正则锚定 ^> 漏识别 → Plan A frontmatter 同步 + batch 同步 双双静默丢失
// ═══════════════════════════════════════════════════════════════════════════════

test("parseCalloutsFromContent: list-nested `* > [!tips]+` is recognized", async () => {
  const md = [
    "* > [!tips]+ 💡 Tips",
    "> - [ ] ✅ 已懂",
    "> - [x] 🤔 模糊",
    "> - [ ] ❌ 不懂",
    ">",
    "> **最大化 (Maximize)**：意味着代理面临选择",
    ">",
    "> ✍️ 我的理解：我对于最大化还是有点不理解。",
  ].join("\n");
  const result = await parseCalloutsFromContent(md, "lecture 2");
  assert.equal(result.length, 1);
  assert.equal(result[0].tag, "tips");
  assert.match(result[0].content, /我对于最大化还是有点不理解/);
});

test("parseCalloutsFromContent: plain `> [!tips]+` still works (regression)", async () => {
  const md = "> [!tips]+ 💡 Tips\n> ✍️ 我的理解：普通格式";
  const result = await parseCalloutsFromContent(md, "n");
  assert.equal(result.length, 1);
});

// ═══════════════════════════════════════════════════════════════════════════════
// P0 (A+-prime 2026-06-26): 稳定 annotation_id round-trip
// ═══════════════════════════════════════════════════════════════════════════════

test("generateAnnotationId: produces cb-prefixed unique ids", () => {
  const a = generateAnnotationId();
  const b = generateAnnotationId();
  assert.match(a, /^cb-[a-z0-9]+$/);
  assert.notEqual(a, b);
});

test("wrapSelection: embeds %%cb-xxx%% in header title line", () => {
  const tips = TAG_OPTIONS[0];
  const out = wrapSelection("hello", tips, "fuzzy", "cb-abc123");
  assert.ok(out.startsWith("> [!tips]+ 💡 Tips %%cb-abc123%%\n"));
});

test("wrapSelection without id: header unchanged (backward compat)", () => {
  const tips = TAG_OPTIONS[0];
  assert.ok(wrapSelection("hi", tips, "fuzzy").startsWith("> [!tips]+ 💡 Tips\n"));
});

test("round-trip: wrapSelection id → parseCalloutsFromContent annotationId, not in content/label", async () => {
  const id = generateAnnotationId();
  const tips = TAG_OPTIONS[0];
  const md = wrapSelection("一个代理是实体", tips, "fuzzy", id);
  const result = await parseCalloutsFromContent(md, "lecture 2");
  assert.equal(result.length, 1);
  assert.equal(result[0].annotationId, id);
  assert.equal(result[0].tagLabel, "💡 Tips"); // id 已从 label 剥离
  assert.ok(!result[0].content.includes("%%")); // id 不污染正文
});

test("parse: two annotations same first line but different id are distinct", async () => {
  const tips = TAG_OPTIONS[0];
  const md =
    wrapSelection("同一句原文", tips, "fuzzy", "cb-first0") +
    "\n\n" +
    wrapSelection("同一句原文", tips, "fuzzy", "cb-second");
  const result = await parseCalloutsFromContent(md, "n");
  assert.equal(result.length, 2);
  assert.notEqual(result[0].annotationId, result[1].annotationId);
});

// ═══════════ P7 (2026-07-16 UAT): buildNewQuestionCallout 直插新疑问 ═══════════

test("buildNewQuestionCallout: 2 lines — question header + visible prompt line", () => {
  const out = buildNewQuestionCallout();
  const lines = out.split("\n");
  assert.equal(lines.length, 2);
  assert.equal(lines[0], "> [!question]+ ❓ 提问");
  assert.equal(lines[1], NEW_QUESTION_PROMPT);
});

test("buildNewQuestionCallout: annotationId embedded as %%cb-xxx%% in header", () => {
  const id = generateAnnotationId();
  const out = buildNewQuestionCallout(id);
  assert.ok(out.split("\n")[0].endsWith(`%%${id}%%`));
});

test("buildNewQuestionCallout: header matches quiz-answer / exam-board extraction regexes", () => {
  const header = buildNewQuestionCallout(generateAnnotationId()).split("\n")[0];
  // /quiz-answer 疑问归纳 Grep
  assert.ok(/^>\s*\[!question\]\+/.test(header));
  // /start-exam-board 安全抽取器
  assert.ok(/>\s*\[!(question|error)\]\+/.test(header));
});

test("round-trip: user types question after prompt → parseCalloutsFromContent picks it up", async () => {
  const id = generateAnnotationId();
  const typed = buildNewQuestionCallout(id) + "特征向量到底是什么？";
  const result = await parseCalloutsFromContent(typed, "Fundamentals");
  assert.equal(result.length, 1);
  assert.equal(result[0].tag, "question");
  assert.equal(result[0].annotationId, id);
  assert.ok(result[0].content.includes("特征向量到底是什么？"));
});

test("MEDIUM-2: untouched placeholder-only question callout is SKIPPED by parse (弃置不入 sync/归纳链)", async () => {
  const result = await parseCalloutsFromContent(
    buildNewQuestionCallout(generateAnnotationId()),
    "n",
  );
  assert.equal(result.length, 0); // 内容只剩占位符 = 用户没写疑问 → 不收割
});

test("MEDIUM-2: placeholder constant stays in sync with prompt line (契约锁)", () => {
  assert.equal(NEW_QUESTION_PROMPT.replace(/^>\s?/, ""), NEW_QUESTION_PLACEHOLDER);
});

// ═══════════ MEDIUM-1/LOW-3 (Code-Review 2026-07-16): computeInsertionSpacing ═══════════

test("spacing: 非空锚点行 → lead 两个换行（行尾另起空行）", () => {
  assert.deepEqual(computeInsertionSpacing("正在答题的一行", "", ""), {
    lead: "\n\n",
    tail: "",
  });
});

test("spacing: 空行但上一行是 '>' 行 → lead 一个换行（保留空行隔离防并块）", () => {
  assert.deepEqual(computeInsertionSpacing("", "> [!tips]+ 💡 Tips", ""), {
    lead: "\n",
    tail: "",
  });
});

test("spacing: 双空行 → 原地起块，无 lead", () => {
  assert.deepEqual(computeInsertionSpacing("", "", ""), { lead: "", tail: "" });
});

test("spacing: 下一行有内容（含 '>' 行）→ tail 垫空行防向下并块", () => {
  assert.equal(computeInsertionSpacing("x", "", "> body").tail, "\n");
  assert.equal(computeInsertionSpacing("x", "", "普通文本").tail, "\n");
  assert.equal(computeInsertionSpacing("x", "", "   ").tail, "");
});

test("spacing: 纯空格行按空行处理（配合 handler 整行替换防 code block）", () => {
  assert.deepEqual(computeInsertionSpacing("   ", "上面有字", ""), {
    lead: "\n",
    tail: "",
  });
});
