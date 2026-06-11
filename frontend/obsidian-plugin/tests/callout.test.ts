import { test } from "node:test";
import assert from "node:assert/strict";
import {
  TAG_OPTIONS,
  UNDERSTANDING_OPTIONS,
  parseCalloutsFromContent,
  wrapSelection,
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
      "> hello",
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
      "> bad logic",
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
      "> line2",
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
      "> b",
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
      assert.ok(out.endsWith(">\n> x"), `body incorrect for ${tag.value}/${und.value}`);

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
  assert.ok(out.endsWith(">\n>   "));
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
