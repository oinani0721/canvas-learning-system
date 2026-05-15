/**
 * MVP-α-5 (2026-05-14) — status-bar.ts unit tests.
 *
 * 用户场景:
 *   "用户写 callout → frontmatter.tips[] 增长 → status bar 数字跃迁 → 短 Notice 反馈"
 *   "Cmd+Click wikilink 跳转 → status bar 显示 '递归 → factorial' 路径"
 *
 * 覆盖:
 *   T1. countTipsFromFrontmatter — 各种 frontmatter 形状的鲁棒性
 *   T2. buildNavPath — prev/current 组合 (含 trim / 重复 / 空)
 *   T3. buildStatusBarText — 文本拼装 (有/无 navPath)
 *   T4. classifyTipsTransition — 4 种过渡状态判定
 *   T5. shouldTrackInNavPath — 路径白名单 (节点/ 原白板/ vs 其他)
 *   T6. buildTipsIncreaseNotice — Notice 文案
 *   T7. main.ts 已 wire (spec-as-test grep)
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  buildNavPath,
  buildStatusBarText,
  buildTipsIncreaseNotice,
  classifyTipsTransition,
  countTipsFromFrontmatter,
  shouldTrackInNavPath,
} from "../src/status-bar";

// ─────────────────────────────────────────────────────────────
// T1. countTipsFromFrontmatter
// ─────────────────────────────────────────────────────────────

describe("countTipsFromFrontmatter", () => {
  test("null fm → 0", () => {
    assert.strictEqual(countTipsFromFrontmatter(null), 0);
  });

  test("undefined fm → 0", () => {
    assert.strictEqual(countTipsFromFrontmatter(undefined), 0);
  });

  test("无 tips 字段 → 0", () => {
    assert.strictEqual(countTipsFromFrontmatter({ board_name: "X" }), 0);
  });

  test("tips 字段非数组 (字符串误填) → 0 (防御)", () => {
    assert.strictEqual(
      countTipsFromFrontmatter({ tips: "我对 base case 还不理解" }),
      0,
    );
  });

  test("空 tips 数组 → 0", () => {
    assert.strictEqual(countTipsFromFrontmatter({ tips: [] }), 0);
  });

  test("3 条 tips → 3", () => {
    assert.strictEqual(
      countTipsFromFrontmatter({
        tips: [
          { text: "a", tag: "tips", understanding: "fuzzy" },
          { text: "b", tag: "error", understanding: "not-understood" },
          { text: "c", tag: "question", understanding: "" },
        ],
      }),
      3,
    );
  });
});

// ─────────────────────────────────────────────────────────────
// T2. buildNavPath
// ─────────────────────────────────────────────────────────────

describe("buildNavPath", () => {
  test("仅 current, prev 缺省 → 单文件名", () => {
    assert.strictEqual(buildNavPath("递归"), "递归");
  });

  test("prev + current → '递归 → factorial'", () => {
    assert.strictEqual(buildNavPath("factorial", "递归"), "递归 → factorial");
  });

  test("prev null → 只显示 current", () => {
    assert.strictEqual(buildNavPath("factorial", null), "factorial");
  });

  test("prev === current (重复打开同文件) → 只显示一次", () => {
    assert.strictEqual(buildNavPath("递归", "递归"), "递归");
  });

  test("两端空白被 trim", () => {
    assert.strictEqual(buildNavPath("  factorial  ", "  递归  "), "递归 → factorial");
  });

  test("current 空字符串 → 返回空 (调用方兜底)", () => {
    assert.strictEqual(buildNavPath(""), "");
  });

  test("prev 空白字符串 → 视作无 prev", () => {
    assert.strictEqual(buildNavPath("factorial", "   "), "factorial");
  });
});

// ─────────────────────────────────────────────────────────────
// T3. buildStatusBarText
// ─────────────────────────────────────────────────────────────

describe("buildStatusBarText", () => {
  test("有 navPath → 完整双段", () => {
    const text = buildStatusBarText({
      tipsCount: 2,
      navPath: "递归 → factorial",
    });
    assert.ok(text.includes("📝 Tips: 2"));
    assert.ok(text.includes("📍 递归 → factorial"));
    assert.ok(text.includes(" · "));
  });

  test("无 navPath → 只 tips 段", () => {
    const text = buildStatusBarText({ tipsCount: 0, navPath: "" });
    assert.strictEqual(text, "📝 Tips: 0");
  });

  test("tipsCount = 0 仍保留, 让用户看到从 0 → 1 跃迁", () => {
    const text = buildStatusBarText({ tipsCount: 0, navPath: "递归" });
    assert.ok(text.includes("📝 Tips: 0"));
    assert.ok(text.includes("📍 递归"));
  });
});

// ─────────────────────────────────────────────────────────────
// T4. classifyTipsTransition
// ─────────────────────────────────────────────────────────────

describe("classifyTipsTransition", () => {
  test("prev undefined → 'init' (避免初始化 Notice 噪音)", () => {
    assert.strictEqual(classifyTipsTransition(undefined, 5), "init");
  });

  test("0 → 1 (用户写第一条 callout) → 'increase'", () => {
    assert.strictEqual(classifyTipsTransition(0, 1), "increase");
  });

  test("2 → 3 → 'increase'", () => {
    assert.strictEqual(classifyTipsTransition(2, 3), "increase");
  });

  test("3 → 2 (用户删了 callout) → 'decrease' (静默, 不打扰)", () => {
    assert.strictEqual(classifyTipsTransition(3, 2), "decrease");
  });

  test("3 → 3 → 'same' (frontmatter 写入触发的 no-op changed)", () => {
    assert.strictEqual(classifyTipsTransition(3, 3), "same");
  });

  test("init 优先级高于 same (即使 prev 与 next 巧合一致)", () => {
    // prev=undefined + next=0 → init, 不是 same
    assert.strictEqual(classifyTipsTransition(undefined, 0), "init");
  });
});

// ─────────────────────────────────────────────────────────────
// T5. shouldTrackInNavPath
// ─────────────────────────────────────────────────────────────

describe("shouldTrackInNavPath", () => {
  test("节点/recursion.md → true", () => {
    assert.strictEqual(shouldTrackInNavPath("节点/recursion.md"), true);
  });

  test("原白板/CS 61B.md → true", () => {
    assert.strictEqual(shouldTrackInNavPath("原白板/CS 61B.md"), true);
  });

  test("Dashboard.md → false (功能页不入 path)", () => {
    assert.strictEqual(shouldTrackInNavPath("Dashboard.md"), false);
  });

  test("templates/Note.md → false", () => {
    assert.strictEqual(shouldTrackInNavPath("templates/Note.md"), false);
  });

  test("raw/transcript.md → false", () => {
    assert.strictEqual(shouldTrackInNavPath("raw/transcript.md"), false);
  });

  test("验收单/Story-1.18.md → false (开发文档不入 path)", () => {
    assert.strictEqual(shouldTrackInNavPath("验收单/Story-1.18.md"), false);
  });
});

// ─────────────────────────────────────────────────────────────
// T6. buildTipsIncreaseNotice
// ─────────────────────────────────────────────────────────────

describe("buildTipsIncreaseNotice", () => {
  test("含 emoji + 计数 + '已记住' 关键字", () => {
    const text = buildTipsIncreaseNotice(2);
    assert.ok(text.includes("🎓"));
    assert.ok(text.includes("2"));
    assert.ok(text.includes("已记住"));
  });

  test("count = 1 时也通顺 (单数无 fallback)", () => {
    const text = buildTipsIncreaseNotice(1);
    assert.ok(text.includes("1"));
  });
});

// ─────────────────────────────────────────────────────────────
// T7. main.ts 已 wire status-bar (spec-as-test)
//
// 复用 vault-indicator.test.ts T2 的 pattern: 读 main.ts 源码 grep
// 关键 wiring 指标. 测试本身不 import main.ts (避开 Obsidian runtime).
// ─────────────────────────────────────────────────────────────

describe("main_ts_wires_status_bar", () => {
  const mainPath = join(process.cwd(), "src", "main.ts");
  const mainTs = readFileSync(mainPath, "utf-8");

  test("import StatusBarController + buildTipsIncreaseNotice from ./status-bar", () => {
    assert.match(
      mainTs,
      /import\s*\{[\s\S]*?StatusBarController[\s\S]*?\}\s*from\s*["']\.\/status-bar["']/,
      "main.ts 必须 import StatusBarController 才能挂状态栏",
    );
    assert.match(
      mainTs,
      /import\s*\{[\s\S]*?buildTipsIncreaseNotice[\s\S]*?\}\s*from\s*["']\.\/status-bar["']/,
      "main.ts 必须 import buildTipsIncreaseNotice 用作 Notice 文案",
    );
  });

  test("onload 调 addStatusBarItem() 创建常驻 element", () => {
    assert.match(
      mainTs,
      /addStatusBarItem\s*\(\s*\)/,
      "onload 必须调 addStatusBarItem() 拿到 HTMLElement",
    );
  });

  test("new StatusBarController(this, ...) 实例化挂在 plugin 字段", () => {
    assert.match(
      mainTs,
      /new\s+StatusBarController\s*\(\s*this\s*,/,
      "main.ts 必须 new StatusBarController(this, ...) 让 controller 拿到 plugin.app",
    );
  });

  test("metadataCache.on('changed') callback 内调 statusBar.handleMetadataChanged", () => {
    // 复用 Story 2.4 Plan A 已注册的 metadataCache 监听, 同回调里追加 status bar 刷新
    assert.match(
      mainTs,
      /statusBar\.handleMetadataChanged\s*\(/,
      "metadataCache 'changed' 回调必须 fan-out 到 statusBar.handleMetadataChanged",
    );
  });

  test("workspace.on('file-open') callback 调 statusBar.handleFileOpen", () => {
    assert.match(
      mainTs,
      /workspace\.on\s*\(\s*["']file-open["'][\s\S]{0,200}?statusBar\.handleFileOpen/,
      "workspace 'file-open' 必须接到 statusBar.handleFileOpen (导航路径反馈瞬间 #3)",
    );
  });

  test("onLayoutReady 初始化 — 打开 Obsidian 即可见当前节点", () => {
    // 用户打开 Obsidian 时不必先切文件, status bar 直接显示当前 active file
    assert.match(
      mainTs,
      /onLayoutReady[\s\S]{0,400}?getActiveFile\(\)[\s\S]{0,200}?statusBar\.handleFileOpen/,
      "onLayoutReady 中必须用 getActiveFile() 触发一次初始化 handleFileOpen",
    );
  });

  test("onTipsIncreased 回调用 buildTipsIncreaseNotice 文案", () => {
    assert.match(
      mainTs,
      /onTipsIncreased\s*:\s*\([^)]*\)\s*=>[\s\S]{0,200}?buildTipsIncreaseNotice\s*\(/,
      "onTipsIncreased 回调必须用 buildTipsIncreaseNotice 文案 (避免硬编码漂移)",
    );
  });
});
