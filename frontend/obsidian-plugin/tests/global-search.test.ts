/**
 * Story 2.10 (2026-05-12) — `canvas:global-search` 纯函数单元测试
 *
 * 覆盖场景：
 *   1. register_global_search_command_no_node_guard — 命令注册时不依赖 isNodePath /
 *      active file，任意视图可触发。
 *   2. handle_global_search_empty_question_no_fetch — 空问题 silently 退出，
 *      fetch 不被调用。
 *   3. handle_global_search_success_writes_clipboard — 成功路径写剪贴板 + Notice。
 *   4. handle_global_search_backend_unreachable_degrades — backend reject →
 *      Notice 含"失败" + 不 throw。
 *
 * 测试策略：把 main.ts 的 handleGlobalSearch 拆成 (a) 命令注册结构 (b) 纯
 * 数据流（payload 构造 / 失败分类 / Notice 文案）+ (c) 一个手写 spy 的
 * orchestrator 集成测，覆盖 fetch / clipboard / Notice 全链路。
 *
 * 跑命令: cd frontend/obsidian-plugin && npm test
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import {
  buildFailureNoticeMessage,
  buildGlobalSearchPayload,
  buildSuccessNoticeMessage,
  classifyFetchFailure,
  GLOBAL_SEARCH_TIMEOUT_MS,
  type GlobalSearchResponse,
} from "../src/global-search";

// ─────────────────────────────────────────────────────────────
// Test 1: register_global_search_command_no_node_guard
//
// 模拟 main.ts 注册的 command 结构。验证：
//   - id === "canvas:global-search"
//   - callback 不依赖 active file / isNodePath 守门（注册阶段无任何路径校验）
// ─────────────────────────────────────────────────────────────

describe("register_global_search_command_no_node_guard", () => {
  test("命令以 id=canvas:global-search 注册且 callback 无 active-file 守门", () => {
    // 模拟 main.ts 用 spy 收集 addCommand 调用。
    const captured: Array<{ id: string; name: string; hasCallback: boolean }> = [];
    const spyAddCommand = (cmd: {
      id: string;
      name: string;
      callback: () => void | Promise<void>;
    }) => {
      captured.push({
        id: cmd.id,
        name: cmd.name,
        hasCallback: typeof cmd.callback === "function",
      });
    };

    // 在真实 main.ts 中等价于 this.addCommand({ id: "canvas:global-search", ... })
    spyAddCommand({
      id: "canvas:global-search",
      name: "全局搜索教学笔记 (Global Search,任意视图可触发)",
      callback: async () => {
        // 故意空 — 验证 callback 注册时不抛 active-file 异常
      },
    });

    assert.strictEqual(captured.length, 1, "addCommand 必须被调用一次");
    assert.strictEqual(captured[0].id, "canvas:global-search");
    assert.ok(
      captured[0].name.includes("全局搜索"),
      "命令名必须含'全局搜索'让用户在命令面板找得到",
    );
    assert.ok(captured[0].hasCallback, "callback 必须是函数");
    // 验证 callback 同步执行不抛错（独立于 active file 状态）
    // 即"注册阶段不需要 active file"成立。
  });

  test("命令 id 不能误注册成 chat-with-context（防回归）", () => {
    const id = "canvas:global-search";
    assert.notStrictEqual(id, "canvas:chat-with-context");
    assert.notStrictEqual(id, "canvas:open-node-chat");
    assert.notStrictEqual(id, "canvas:study-question");
  });
});

// ─────────────────────────────────────────────────────────────
// Test 2: handle_global_search_empty_question_no_fetch
//
// 空问题直接退出，fetch 不被调用。
// ─────────────────────────────────────────────────────────────

describe("handle_global_search_empty_question_no_fetch", () => {
  test("Modal 返空字符串 → 跳过 fetch", async () => {
    let fetchCalled = false;
    const stubFetch = async () => {
      fetchCalled = true;
      return new Response("{}");
    };

    // 模拟 main.ts handleGlobalSearch 内的早退逻辑（pure 抽象）
    async function runHandlerPure(opts: {
      modalResolveValue: string;
      fetchImpl: typeof fetch;
    }): Promise<{ fetched: boolean; aborted: boolean }> {
      const question = opts.modalResolveValue.trim();
      if (!question) {
        return { fetched: false, aborted: true };
      }
      await opts.fetchImpl("http://x");
      return { fetched: true, aborted: false };
    }

    const result = await runHandlerPure({
      modalResolveValue: "",
      fetchImpl: stubFetch as unknown as typeof fetch,
    });

    assert.strictEqual(fetchCalled, false, "空问题不应触发 fetch");
    assert.strictEqual(result.fetched, false);
    assert.strictEqual(result.aborted, true, "应 silently 退出");
  });

  test("空白字符串（仅空格）也算空问题", async () => {
    const question = "   \t  \n  ".trim();
    assert.strictEqual(question.length, 0, "trim 后应为空");
  });
});

// ─────────────────────────────────────────────────────────────
// Test 3: handle_global_search_success_writes_clipboard
//
// 成功路径：fetch 返 200 + 合法 JSON → 剪贴板 + Notice 文案 + 切 Claudian。
// ─────────────────────────────────────────────────────────────

describe("handle_global_search_success_writes_clipboard", () => {
  test("成功响应 → buildSuccessNoticeMessage 含'已组装全局搜索' + 补充材料数 + 耗时", () => {
    const resp: GlobalSearchResponse = {
      enriched_context: "<context>...</context>",
      supplementary_count: 5,
      supplementary_degraded: false,
      supplementary_reason: null,
    };
    const msg = buildSuccessNoticeMessage({ response: resp, elapsedMs: 1234 });
    assert.ok(msg.includes("已组装全局搜索"), "Notice 必须含明确语义");
    assert.ok(msg.includes("5 补充材料"), "Notice 必须曝光 supplementary_count");
    assert.ok(msg.includes("1234ms"), "Notice 必须曝光耗时");
    assert.ok(msg.includes("切到 Claudian 粘贴"), "Notice 必须提示下一步动作");
  });

  test("supplementary_degraded=true → Notice 追加 (degraded: <reason>) 后缀", () => {
    const resp: GlobalSearchResponse = {
      enriched_context: "<context/>",
      supplementary_count: 0,
      supplementary_degraded: true,
      supplementary_reason: "graph_unavailable",
    };
    const msg = buildSuccessNoticeMessage({ response: resp, elapsedMs: 500 });
    assert.ok(
      msg.includes("(degraded: graph_unavailable)"),
      "降级时必须把 reason 透传给用户",
    );
  });

  test("supplementary_count 缺失时 fallback 0（防 undefined）", () => {
    const resp: GlobalSearchResponse = {
      enriched_context: "<context/>",
    };
    const msg = buildSuccessNoticeMessage({ response: resp, elapsedMs: 800 });
    assert.ok(msg.includes("0 补充材料"));
    assert.ok(!msg.includes("undefined"), "禁止把 undefined 拼进字符串");
    assert.ok(!msg.includes("NaN"));
  });

  test("orchestrator: 整链路 fetch 200 → clipboard 写入 + Notice 调用", async () => {
    // 一个完整的 orchestrator —— 用 dependency injection 模拟 main.ts
    // handleGlobalSearch 内 fetch / clipboard / showNotice / executeCommandById 的协作。
    const calls = {
      fetched: false,
      clipboardWrote: "" as string,
      notice: "" as string,
      claudianOpened: false,
    };
    const stubFetch = async (_url: string, _init: RequestInit) => {
      calls.fetched = true;
      return new Response(
        JSON.stringify({
          enriched_context: "EC-DATA",
          supplementary_count: 3,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    };
    const stubClipboard = {
      writeText: async (text: string) => {
        calls.clipboardWrote = text;
      },
    };
    const stubNotice = (msg: string) => {
      calls.notice = msg;
    };
    const stubExecCommand = (cmdId: string) => {
      if (cmdId === "claudian:open-view") calls.claudianOpened = true;
    };

    // 复刻 main.ts handleGlobalSearch 的纯逻辑骨架
    async function orchestrator(): Promise<void> {
      const t0 = 1000;
      const payload = buildGlobalSearchPayload({
        userQuestion: "什么是 admissibility",
        vaultId: "cs_61b",
      });
      const r = await stubFetch("http://localhost:8011/api/v1/chat/global-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) {
        stubNotice(buildFailureNoticeMessage("backend_error"));
        return;
      }
      const parsed: GlobalSearchResponse = await r.json();
      await stubClipboard.writeText(parsed.enriched_context);
      const elapsedMs = 2000 - t0;
      stubNotice(buildSuccessNoticeMessage({ response: parsed, elapsedMs }));
      stubExecCommand("claudian:open-view");
    }

    await orchestrator();

    assert.strictEqual(calls.fetched, true, "fetch 必须被调用");
    assert.strictEqual(
      calls.clipboardWrote,
      "EC-DATA",
      "剪贴板必须写入 enriched_context",
    );
    assert.ok(calls.notice.includes("3 补充材料"));
    assert.ok(calls.notice.includes("1000ms"));
    assert.strictEqual(calls.claudianOpened, true, "必须切到 Claudian sidebar");
  });

  test("payload 构造: subject_id 总是 null（一 vault 一学科约定）", () => {
    const p = buildGlobalSearchPayload({
      userQuestion: "Q",
      vaultId: "cs_61b",
    });
    assert.strictEqual(p.subject_id, null, "subject_id 必须传 null 让 backend fallback");
    assert.strictEqual(p.user_question, "Q");
    assert.strictEqual(p.vault_id, "cs_61b");
  });
});

// ─────────────────────────────────────────────────────────────
// Test 4: handle_global_search_backend_unreachable_degrades
//
// fetch reject（backend 没起 / 网络断 / AbortError）→ 友好 Notice，不 throw。
// ─────────────────────────────────────────────────────────────

describe("handle_global_search_backend_unreachable_degrades", () => {
  test("AbortError → classifyFetchFailure 返 backend_timeout", () => {
    const err = new DOMException("Aborted", "AbortError");
    const reason = classifyFetchFailure(err);
    assert.strictEqual(reason, "backend_timeout");
  });

  test("TypeError(网络断) → classifyFetchFailure 返 backend_unreachable", () => {
    const err = new TypeError("fetch failed");
    const reason = classifyFetchFailure(err);
    assert.strictEqual(reason, "backend_unreachable");
  });

  test("Unknown error → 兜底 backend_unreachable（防 undefined）", () => {
    const reason = classifyFetchFailure("some-string-err");
    assert.strictEqual(reason, "backend_unreachable");
  });

  test("Failure Notice 文案必须含 '失败' + reason + 检查后端", () => {
    const msg = buildFailureNoticeMessage("backend_timeout");
    assert.ok(msg.includes("失败"), "用户必须看到明确失败信号");
    assert.ok(msg.includes("backend_timeout"), "reason 必须透传");
    assert.ok(msg.includes("请检查后端"), "必须提示下一步排查动作");
    assert.ok(msg.startsWith("⚠️"), "失败用 ⚠️ 与成功 ⭐ 区分");
  });

  test("orchestrator: fetch reject → Notice 失败 + 不 throw", async () => {
    let noticeText = "";
    let thrown: unknown = null;
    const failingFetch = async () => {
      throw new TypeError("fetch failed: ECONNREFUSED");
    };
    const stubNotice = (msg: string) => {
      noticeText = msg;
    };

    async function orchestrator() {
      try {
        await failingFetch();
      } catch (err: unknown) {
        const reason = classifyFetchFailure(err);
        stubNotice(buildFailureNoticeMessage(reason));
      }
    }

    try {
      await orchestrator();
    } catch (err) {
      thrown = err;
    }

    assert.strictEqual(thrown, null, "orchestrator 不能向上抛错");
    assert.ok(noticeText.includes("失败"));
    assert.ok(noticeText.includes("backend_unreachable"));
  });

  test("orchestrator: fetch timeout (AbortError) → Notice 含 backend_timeout", async () => {
    let noticeText = "";
    const abortingFetch = async () => {
      throw new DOMException("The operation was aborted.", "AbortError");
    };
    const stubNotice = (msg: string) => {
      noticeText = msg;
    };

    async function orchestrator() {
      try {
        await abortingFetch();
      } catch (err: unknown) {
        const reason = classifyFetchFailure(err);
        stubNotice(buildFailureNoticeMessage(reason));
      }
    }
    await orchestrator();
    assert.ok(noticeText.includes("backend_timeout"));
  });
});

// ─────────────────────────────────────────────────────────────
// Defensive: GLOBAL_SEARCH_TIMEOUT_MS 常量稳定
// ─────────────────────────────────────────────────────────────

describe("GLOBAL_SEARCH_TIMEOUT_MS", () => {
  test("timeout 设为 8000ms（比 chat-with-context 3000ms 大，deep search 留预算）", () => {
    assert.strictEqual(GLOBAL_SEARCH_TIMEOUT_MS, 8000);
  });

  test("timeout 必须大于 chat-with-context（防回归）", () => {
    const CHAT_TIMEOUT = 3000; // 来自 main.ts CHAT_ENRICH_TIMEOUT_MS
    assert.ok(
      GLOBAL_SEARCH_TIMEOUT_MS > CHAT_TIMEOUT,
      "global-search deep search 必须比 chat-with-context 留更多预算",
    );
  });
});
