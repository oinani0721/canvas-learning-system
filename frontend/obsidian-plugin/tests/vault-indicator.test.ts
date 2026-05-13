/**
 * Wave-5 Stage A (2026-05-12) — Vault indicator unit tests.
 *
 * 用户场景: "在 obsidian 中关于 Canvas learning system 中可以**明确分隔开来**"
 * → 每次 hotkey 触发都"瞥见"当前 vault, status bar 常驻指示器避免误用。
 *
 * 覆盖:
 *   T1. buildVaultPrefix — Notice 前缀构造 (含 fallback)
 *   T2. handleChatWithContext Notice 含 vault prefix (集成: 验证 main.ts 已 wire)
 *   T3. status bar 用 vault 名初始化 (3 态)
 *   T4. status bar 在 backend ✓/❌ 切换时更新
 *   T5. status bar 点击 → 打开 Settings tab
 *   T6. classifyBackendHealth — 3 态决策表 (down / mismatch / ok)
 *   T7. buildStatusBarLabel — 3 态文本
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import {
  buildStatusBarClassName,
  buildStatusBarLabel,
  buildVaultPrefix,
  classifyBackendHealth,
} from "../src/vault-indicator";

// ─────────────────────────────────────────────────────────────
// T1. buildVaultPrefix — pure function
// ─────────────────────────────────────────────────────────────

describe("buildVaultPrefix_returns_bracketed_vault_id", () => {
  test("普通 vault_id → '[vault: cs_61b] '", () => {
    assert.strictEqual(buildVaultPrefix("cs_61b"), "[vault: cs_61b] ");
  });

  test("空字符串 → fallback '[vault: default] '", () => {
    assert.strictEqual(buildVaultPrefix(""), "[vault: default] ");
  });

  test("undefined → fallback '[vault: default] '", () => {
    assert.strictEqual(buildVaultPrefix(undefined), "[vault: default] ");
  });

  test("两端空白被 trim", () => {
    assert.strictEqual(buildVaultPrefix("  数学  "), "[vault: 数学] ");
  });

  test("尾部含单空格 (与 Notice 文案直接拼接)", () => {
    const p = buildVaultPrefix("x");
    assert.ok(p.endsWith("] "), "prefix 必须以 '] ' 结尾以分隔 Notice 主体");
  });
});

// ─────────────────────────────────────────────────────────────
// T2. handleChatWithContext Notice 含 vault prefix
//
// 集成测：通过文本断言验证 main.ts 源码确实把 buildVaultPrefix 拼到了
// 4 个 handler 的 Notice 字符串前。test 不 import main.ts (拖 Obsidian
// runtime)，而是读源文件 grep 关键字。这是 spec-as-test pattern。
// ─────────────────────────────────────────────────────────────

import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("handleChatWithContext_notice_contains_vault_prefix", () => {
  // 注意: __dirname 在 esbuild bundle 后指向 tests/.out/, 用 process.cwd() 兜底
  const mainPath = join(process.cwd(), "src", "main.ts");
  const mainTs = readFileSync(mainPath, "utf-8");

  test("main.ts import buildVaultPrefix from vault-indicator", () => {
    assert.match(
      mainTs,
      /import\s*\{[^}]*buildVaultPrefix[^}]*\}\s*from\s*["']\.\/vault-indicator["']/,
      "main.ts 必须 import buildVaultPrefix 才能给 Notice 加前缀",
    );
  });

  test("4 handler 关键 Notice 都用 buildVaultPrefix 拼接", () => {
    // 4 个 handler 的标志性 Notice 文案:
    //   handleChatWithContext: "已组装 backend RAG 上下文"
    //   handleStudyQuestion:   "🧠 解题深度模式已就绪"
    //   handleOpenNodeChat:    "已复制节点"
    //   fallbackToLocalNeighbors: "已降级到本地"
    //
    // 验证: 每条 Notice 上游必有 buildVaultPrefix(...) 调用拼接,
    //       不再裸用模板字符串。
    const keyPhrases = [
      "已组装 backend RAG 上下文",
      "解题深度模式已就绪",
      "已复制节点",
      "已降级到本地",
    ];
    const occurrences = (mainTs.match(/buildVaultPrefix\s*\(/g) ?? []).length;
    assert.ok(
      occurrences >= 4,
      `main.ts 至少含 4 处 buildVaultPrefix() 调用 (4 个 Notice handler), 实际: ${occurrences}`,
    );
    for (const phrase of keyPhrases) {
      assert.ok(
        mainTs.includes(phrase),
        `main.ts 必须保留 Notice 关键文案: ${phrase}`,
      );
    }
  });
});

// ─────────────────────────────────────────────────────────────
// T3. status bar 初始化
// ─────────────────────────────────────────────────────────────

describe("status_bar_initialized_with_current_vault", () => {
  test("buildStatusBarLabel ok 状态 → 含 vault 名 + ✓", () => {
    const label = buildStatusBarLabel({ state: "ok", vaultId: "cs_61b" });
    assert.ok(label.includes("cs_61b"));
    assert.ok(label.includes("✓"));
    assert.ok(label.includes("🎓"));
  });

  test("空 vault_id 时 fallback 'default'", () => {
    const label = buildStatusBarLabel({ state: "ok", vaultId: "" });
    assert.ok(label.includes("default"), `空 vault 应 fallback 到 default: ${label}`);
  });

  test("main.ts onload() 调 addStatusBarItem + updateStatusBar", () => {
    const mainPath = join(process.cwd(), "src", "main.ts");
    const mainTs = readFileSync(mainPath, "utf-8");
    assert.match(
      mainTs,
      /addStatusBarItem\s*\(\s*\)/,
      "onload() 必须调 addStatusBarItem() 创建 status bar 元素",
    );
    assert.match(
      mainTs,
      /updateStatusBar\s*\(/,
      "main.ts 必须含 updateStatusBar() 调用 (初始化 + 周期刷新)",
    );
  });
});

// ─────────────────────────────────────────────────────────────
// T4. status bar 在 backend health 切换时更新
// ─────────────────────────────────────────────────────────────

describe("status_bar_updates_on_backend_health_change", () => {
  test("classifyBackendHealth — backend 200 + vault 匹配 → ok", () => {
    const state = classifyBackendHealth({
      ok: true,
      vaultIdLocal: "cs_61b",
      vaultIdRemote: "cs_61b",
    });
    assert.strictEqual(state, "ok");
  });

  test("classifyBackendHealth — backend 503/无响应 → down", () => {
    const state = classifyBackendHealth({
      ok: false,
      vaultIdLocal: "cs_61b",
    });
    assert.strictEqual(state, "down");
  });

  test("classifyBackendHealth — backend 200 但 vault 不匹配 → mismatch", () => {
    const state = classifyBackendHealth({
      ok: true,
      vaultIdLocal: "cs_61b",
      vaultIdRemote: "数学",
    });
    assert.strictEqual(state, "mismatch");
  });

  test("classifyBackendHealth — remote vault_id 未知时不触发 mismatch (容错)", () => {
    const state = classifyBackendHealth({
      ok: true,
      vaultIdLocal: "cs_61b",
      vaultIdRemote: undefined,
    });
    assert.strictEqual(state, "ok");
  });

  test("buildStatusBarLabel — mismatch 状态文本", () => {
    const label = buildStatusBarLabel({ state: "mismatch", vaultId: "cs_61b" });
    assert.ok(label.includes("⚠"));
    assert.ok(label.includes("backend on another vault"));
  });

  test("buildStatusBarLabel — down 状态文本", () => {
    const label = buildStatusBarLabel({ state: "down", vaultId: "cs_61b" });
    assert.ok(label.includes("❌"));
    assert.ok(label.includes("backend down"));
  });

  test("buildStatusBarClassName — 3 态各自独立 className", () => {
    const ok = buildStatusBarClassName("ok");
    const mm = buildStatusBarClassName("mismatch");
    const dn = buildStatusBarClassName("down");
    assert.ok(ok.includes("canvas-vault-indicator-ok"));
    assert.ok(mm.includes("canvas-vault-indicator-mismatch"));
    assert.ok(dn.includes("canvas-vault-indicator-down"));
    assert.notStrictEqual(ok, mm);
    assert.notStrictEqual(mm, dn);
  });
});

// ─────────────────────────────────────────────────────────────
// T5. status bar 点击 → 打开 Settings tab
// ─────────────────────────────────────────────────────────────

describe("status_bar_click_opens_settings", () => {
  test("main.ts updateStatusBar 注册 click handler 调 setting.open / setting.openTabById", () => {
    const mainPath = join(process.cwd(), "src", "main.ts");
    const mainTs = readFileSync(mainPath, "utf-8");
    // 验证 main.ts wiring: status bar element 接 click → 触发 setting.open
    // (Obsidian 标准 API: this.app.setting.open() + openTabById(plugin-id))
    assert.match(
      mainTs,
      /setting\.open\s*\(\s*\)/,
      "click handler 必须调 this.app.setting.open() 打开设置面板",
    );
    assert.match(
      mainTs,
      /openTabById/,
      "click handler 必须调 setting.openTabById(...) 跳到本插件 tab",
    );
  });

  test("main.ts updateStatusBar 用 registerInterval/setInterval 周期刷新", () => {
    const mainPath = join(process.cwd(), "src", "main.ts");
    const mainTs = readFileSync(mainPath, "utf-8");
    // Obsidian 推荐 registerInterval 包裹 setInterval 自动清理
    assert.match(
      mainTs,
      /registerInterval\s*\(/,
      "main.ts 必须用 registerInterval 包裹周期刷新, 否则 plugin unload 后 leak",
    );
  });

  test("main.ts 注册 layout-change 事件触发 updateStatusBar (切 vault 即时刷新)", () => {
    const mainPath = join(process.cwd(), "src", "main.ts");
    const mainTs = readFileSync(mainPath, "utf-8");
    assert.match(
      mainTs,
      /["']layout-change["']/,
      "main.ts 必须监听 'layout-change' 事件实现切 vault 即时刷新",
    );
  });
});
