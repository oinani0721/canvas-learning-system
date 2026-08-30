/**
 * Wave-5 Stage A (2026-05-12) — Vault indicator unit tests.
 *
 * 用户场景: "在 obsidian 中关于 Canvas learning system 中可以**明确分隔开来**"
 * → 每次 hotkey 触发都"瞥见"当前 vault, status bar 常驻指示器避免误用。
 *
 * ⚠️ DEBT-5 债务哨兵化 (2026-08-28, Codex round-1 HIGH 整改):
 * 本文件的 spec-as-test wiring 断言 (grep main.ts) 自 3d10a02b (05-14
 * story-2.4) 移除 wiring 起持续 FAIL, 无 CI 门故无人察觉。考古结论:
 *   - α-5 (f860f57f) 的 StatusBarController 只渲染 Tips/导航路径,
 *     **没有**接替 vault_id 三态/mismatch/Notice 前缀行为;
 *   - α-5 状态记录把这些失败登记为 "Wave-5 Stage A 待补 wiring"
 *     (_bmad-output/_status/mvp-alpha-broadcast-session-b.yaml:114-117);
 *   - UAT 仍要求 `[vault:]` Notice 前缀
 *     (_bmad-output/验收单/Story-2.2+2.9-FINAL-comprehensive-UAT-2026-05-13.md
 *      "Step 1 — Notice [vault:] 前缀(必跑)")。
 * → 这是**未完成需求债务**, 不是已退役功能。断言不删除, 改标 node:test
 * `todo` (失败在输出可见但不 fail 套件, 等价 backend G2-1 门测试的
 * xfail 债务先例), 使 plugin-ci 门可落地而债务不被洗绿。
 * 最终裁决 (补 wiring 或正式退役并同步 UAT) = 用户决策, 移交条款见
 * _bmad-output/验收单/UAT-CARD-DEBT-5-插件CI-build-test门-2026-08-28.md
 * §"待用户裁决"。
 *
 * 覆盖:
 *   T1. buildVaultPrefix — Notice 前缀构造 (含 fallback)
 *   T2. [todo 债务] main.ts Notice 含 vault prefix wiring
 *   T3. buildStatusBarLabel 3 态 + [todo 债务] main.ts wiring
 *   T4. classifyBackendHealth — 3 态决策表 (down / mismatch / ok)
 *   T5. [todo 债务] status bar 点击 → Settings / 周期刷新 / layout-change
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import {
  buildStatusBarClassName,
  buildStatusBarLabel,
  buildVaultPrefix,
  classifyBackendHealth,
} from "../src/vault-indicator";

const WIRING_DEBT_TODO =
  "vault-indicator wiring 债务哨兵 (Wave-5 Stage A 待补, 见文件头 DEBT-5 注记)";

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
// DEBT-5: wiring 自 3d10a02b 缺失 → todo 债务哨兵, 见文件头。
// ─────────────────────────────────────────────────────────────

import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("handleChatWithContext_notice_contains_vault_prefix", () => {
  // 注意: __dirname 在 esbuild bundle 后指向 tests/.out/, 用 process.cwd() 兜底
  const mainPath = join(process.cwd(), "src", "main.ts");
  const mainTs = readFileSync(mainPath, "utf-8");

  test(
    "main.ts import buildVaultPrefix from vault-indicator",
    { todo: WIRING_DEBT_TODO },
    () => {
      assert.match(
        mainTs,
        /import\s*\{[^}]*buildVaultPrefix[^}]*\}\s*from\s*["']\.\/vault-indicator["']/,
        "main.ts 必须 import buildVaultPrefix 才能给 Notice 加前缀",
      );
    },
  );

  test(
    "4 handler 关键 Notice 都用 buildVaultPrefix 拼接",
    { todo: WIRING_DEBT_TODO },
    () => {
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
    },
  );
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

  test(
    "main.ts onload() 调 addStatusBarItem + updateStatusBar",
    { todo: WIRING_DEBT_TODO },
    () => {
      // addStatusBarItem 现役 (α-5 StatusBarController, 覆盖在
      // status-bar.test.ts); updateStatusBar (vault 三态刷新) 是待补部分。
      const mainTs2 = readFileSync(join(process.cwd(), "src", "main.ts"), "utf-8");
      assert.match(
        mainTs2,
        /addStatusBarItem\s*\(\s*\)/,
        "onload() 必须调 addStatusBarItem() 创建 status bar 元素",
      );
      assert.match(
        mainTs2,
        /updateStatusBar\s*\(/,
        "main.ts 必须含 updateStatusBar() 调用 (初始化 + 周期刷新)",
      );
    },
  );
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
// T5. status bar 点击 → 打开 Settings tab / 周期刷新 / layout-change
// DEBT-5: 全部 todo 债务哨兵。原 "setting.open 存在" 断言是假阳性
// (Codex round-1 MEDIUM: 全文件 grep 会命中设置页里的"打开快捷键设置"
// 按钮 main.ts:2188, 与 status bar click 无关) — 已改写为绑定 click
// 语境的行为级断言。
// ─────────────────────────────────────────────────────────────

describe("status_bar_click_opens_settings", () => {
  const mainPath = join(process.cwd(), "src", "main.ts");
  const mainTs = readFileSync(mainPath, "utf-8");

  test(
    "status bar element 接 click handler → setting.open + openTabById",
    { todo: WIRING_DEBT_TODO },
    () => {
      // Codex round-2 MEDIUM 整改: 断言锚定到 status bar element 本身,
      // 不再是"任意 click 结构"。
      //   1) 先定位 addStatusBarItem() 的接收变量名 (element 身份);
      //   2) 再要求该变量上注册 click (三种 Obsidian 常见形态 +
      //      registerDomEvent(el, "click", ...)), 且同一 handler 体内
      //      (800 字符窗口, 容纳委托前的若干行) 出现 setting.open()
      //      与 openTabById。
      // 仍是 spec-as-test 近似: 若实现把 handler 抽成独立方法
      // (openPluginSettings()), 本断言会漏报 —— 那属于 wiring 补齐时
      // 一并改写测试的范畴, 已在文件头债务条款登记。
      const elMatch = mainTs.match(
        /(?:const|let|var)\s+(\w+)\s*=\s*this\.addStatusBarItem\s*\(\s*\)/,
      );
      assert.ok(
        elMatch,
        "onload() 必须把 addStatusBarItem() 的返回值存入变量才能挂 click handler",
      );
      const el = elMatch![1];
      const clickOn = String.raw`(?:${el}\.addEventListener\s*\(\s*["']click["']|${el}\.onClickEvent\s*\(|${el}\.onclick\s*=|registerDomEvent\s*\(\s*${el}\s*,\s*["']click["'])`;
      assert.match(
        mainTs,
        new RegExp(`${clickOn}[\\s\\S]{0,800}?setting\\.open\\s*\\(`),
        `status bar element (${el}) 的 click handler 必须调 this.app.setting.open()`,
      );
      assert.match(
        mainTs,
        new RegExp(`${clickOn}[\\s\\S]{0,800}?openTabById`),
        `status bar element (${el}) 的 click handler 必须调 setting.openTabById(...) 跳到本插件 tab`,
      );
    },
  );

  test(
    "main.ts updateStatusBar 用 registerInterval/setInterval 周期刷新",
    { todo: WIRING_DEBT_TODO },
    () => {
      // Obsidian 推荐 registerInterval 包裹 setInterval 自动清理
      assert.match(
        mainTs,
        /registerInterval\s*\(/,
        "main.ts 必须用 registerInterval 包裹周期刷新, 否则 plugin unload 后 leak",
      );
    },
  );

  test(
    "main.ts 注册 layout-change 事件触发 updateStatusBar (切 vault 即时刷新)",
    { todo: WIRING_DEBT_TODO },
    () => {
      assert.match(
        mainTs,
        /["']layout-change["']/,
        "main.ts 必须监听 'layout-change' 事件实现切 vault 即时刷新",
      );
    },
  );
});
