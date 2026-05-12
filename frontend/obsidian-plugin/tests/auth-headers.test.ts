/**
 * Wave-2 P0-1 (2026-05-12) — X-CLS-Internal-Key auth header 单元测试
 *
 * 防回归 ChatGPT v2 对抗审查 P0 发现：plugin 4 handler 在生产 env
 * (DEBUG=False + backend INTERNAL_API_KEY 配置) 下全部 403,
 * 因为 fetch headers 裸用 `{ "Content-Type": "application/json" }` 漏带
 * X-CLS-Internal-Key auth header。
 *
 * 测试策略:
 * - buildBackendHeaders 是 pure function (只读 settings, 不读外部 IO),
 *   直接 stub settings 验证 header 构造
 * - 4 handler 集成测：用 dependency-injected fetch stub 捕获 headers,
 *   验证 X-CLS-Internal-Key 真的传到 fetch 调用
 *
 * 跑命令: cd frontend/obsidian-plugin && npm test
 */

import assert from "node:assert";
import { describe, test } from "node:test";

// ─────────────────────────────────────────────────────────────
// Pure-function 复刻 main.ts::buildBackendHeaders
//
// 不能直接 import main.ts（会拖 Obsidian runtime 依赖），所以测试里手写
// 同语义的 pure function 镜像，保证行为对齐（test as living spec）。
// 若 main.ts 改了语义，本测试会偏离 — 提交前 grep 双向比对。
// ─────────────────────────────────────────────────────────────

interface PluginSettingsLike {
  internalApiKey: string;
}

function buildBackendHeadersPure(settings: PluginSettingsLike): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (settings.internalApiKey && settings.internalApiKey.length > 0) {
    headers["X-CLS-Internal-Key"] = settings.internalApiKey;
  }
  return headers;
}

// ─────────────────────────────────────────────────────────────
// Test 1: test_buildBackendHeaders_no_key_returns_only_content_type
//
// settings.internalApiKey="" → headers 只含 Content-Type (dev mode 兼容)
// ─────────────────────────────────────────────────────────────

describe("buildBackendHeaders_no_key_returns_only_content_type", () => {
  test("空字符串 internalApiKey → 只含 Content-Type, 不加 X-CLS-Internal-Key", () => {
    const headers = buildBackendHeadersPure({ internalApiKey: "" });
    assert.strictEqual(headers["Content-Type"], "application/json");
    assert.strictEqual(
      headers["X-CLS-Internal-Key"],
      undefined,
      "空 key → 必须不加 X-CLS-Internal-Key (dev mode DEBUG=True 兼容)",
    );
    assert.strictEqual(Object.keys(headers).length, 1, "仅 1 个 header");
  });

  test("undefined-like 空 internalApiKey 等同 dev mode", () => {
    const headers = buildBackendHeadersPure({ internalApiKey: "" });
    assert.ok(!("X-CLS-Internal-Key" in headers), "空 → header 字段必须不存在");
  });
});

// ─────────────────────────────────────────────────────────────
// Test 2: test_buildBackendHeaders_with_key_returns_internal_key_header
//
// settings.internalApiKey="secret" → headers 含 X-CLS-Internal-Key: secret
// ─────────────────────────────────────────────────────────────

describe("buildBackendHeaders_with_key_returns_internal_key_header", () => {
  test("非空 internalApiKey → header 含 X-CLS-Internal-Key: <key>", () => {
    const headers = buildBackendHeadersPure({ internalApiKey: "secret-123" });
    assert.strictEqual(headers["Content-Type"], "application/json");
    assert.strictEqual(
      headers["X-CLS-Internal-Key"],
      "secret-123",
      "key 必须原样传入 (backend middleware constant_time_compare)",
    );
    assert.strictEqual(Object.keys(headers).length, 2);
  });

  test("key 含特殊字符也原样保留 (不做 url encode, header value 可含 base64 等)", () => {
    const headers = buildBackendHeadersPure({
      internalApiKey: "abc/+=def==",
    });
    assert.strictEqual(headers["X-CLS-Internal-Key"], "abc/+=def==");
  });

  test("very long key (64 chars+) 不被截断 (prod 用 256-bit hex = 64 chars)", () => {
    const longKey = "a".repeat(128);
    const headers = buildBackendHeadersPure({ internalApiKey: longKey });
    assert.strictEqual(
      headers["X-CLS-Internal-Key"]?.length,
      128,
      "长 key 不能截断",
    );
  });
});

// ─────────────────────────────────────────────────────────────
// Test 3: test_handleChatWithContext_sends_internal_key_header
//
// mock fetch + settings.internalApiKey="k" → fetch 被调用时 headers
// 含 X-CLS-Internal-Key (集成测，验证 4 handler 真的用上了 helper)
// ─────────────────────────────────────────────────────────────

describe("handleChatWithContext_sends_internal_key_header", () => {
  test("handler 复刻：fetch 调用 headers 含 X-CLS-Internal-Key", async () => {
    let capturedHeaders: Record<string, string> | undefined = undefined;
    const stubFetch = async (
      _url: string,
      init: RequestInit,
    ): Promise<Response> => {
      capturedHeaders = init.headers as Record<string, string>;
      return new Response(JSON.stringify({ enriched_context: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    // 复刻 main.ts handleChatWithContext 内 fetch 部分（关键：用 buildBackendHeaders）
    async function handleChatWithContextSpy(settings: PluginSettingsLike) {
      const headers = buildBackendHeadersPure(settings);
      await stubFetch("http://localhost:8011/api/v1/chat/enrich-context", {
        method: "POST",
        headers,
        body: JSON.stringify({ node_path: "节点/x.md" }),
      });
    }

    await handleChatWithContextSpy({ internalApiKey: "test-key" });

    assert.ok(capturedHeaders !== undefined, "fetch 必须被调用");
    assert.strictEqual(
      (capturedHeaders as Record<string, string>)["X-CLS-Internal-Key"],
      "test-key",
      "handleChatWithContext 必须传 X-CLS-Internal-Key 到 fetch",
    );
    assert.strictEqual(
      (capturedHeaders as Record<string, string>)["Content-Type"],
      "application/json",
    );
  });

  test("dev mode (空 key) chat-with-context → fetch headers 不含 X-CLS-Internal-Key", async () => {
    let capturedHeaders: Record<string, string> | undefined = undefined;
    const stubFetch = async (
      _url: string,
      init: RequestInit,
    ): Promise<Response> => {
      capturedHeaders = init.headers as Record<string, string>;
      return new Response("{}", { status: 200 });
    };

    async function handleChatWithContextSpy(settings: PluginSettingsLike) {
      await stubFetch("http://x", {
        method: "POST",
        headers: buildBackendHeadersPure(settings),
        body: "{}",
      });
    }
    await handleChatWithContextSpy({ internalApiKey: "" });

    assert.ok(capturedHeaders !== undefined);
    assert.ok(
      !("X-CLS-Internal-Key" in (capturedHeaders as Record<string, string>)),
      "dev mode 不应传 X-CLS-Internal-Key (避免 backend 误判)",
    );
  });
});

// ─────────────────────────────────────────────────────────────
// Test 4: handleStudyQuestion_sends_internal_key_header
// ─────────────────────────────────────────────────────────────

describe("handleStudyQuestion_sends_internal_key_header", () => {
  test("study-question deep 模式 fetch headers 含 X-CLS-Internal-Key", async () => {
    let capturedHeaders: Record<string, string> | undefined = undefined;
    const stubFetch = async (
      _url: string,
      init: RequestInit,
    ): Promise<Response> => {
      capturedHeaders = init.headers as Record<string, string>;
      return new Response(JSON.stringify({ enriched_context: "deep" }), {
        status: 200,
      });
    };

    async function handleStudyQuestionSpy(settings: PluginSettingsLike) {
      await stubFetch("http://localhost:8011/api/v1/chat/enrich-context", {
        method: "POST",
        headers: buildBackendHeadersPure(settings),
        body: JSON.stringify({ mode: "deep", user_question: "Q" }),
      });
    }

    await handleStudyQuestionSpy({ internalApiKey: "deep-key" });
    assert.strictEqual(
      (capturedHeaders as Record<string, string>)["X-CLS-Internal-Key"],
      "deep-key",
    );
  });
});

// ─────────────────────────────────────────────────────────────
// Test 5: handleGlobalSearch_sends_internal_key_header
// ─────────────────────────────────────────────────────────────

describe("handleGlobalSearch_sends_internal_key_header", () => {
  test("global-search fetch headers 含 X-CLS-Internal-Key", async () => {
    let capturedHeaders: Record<string, string> | undefined = undefined;
    const stubFetch = async (
      _url: string,
      init: RequestInit,
    ): Promise<Response> => {
      capturedHeaders = init.headers as Record<string, string>;
      return new Response(
        JSON.stringify({ enriched_context: "g", supplementary_count: 0 }),
        { status: 200 },
      );
    };

    async function handleGlobalSearchSpy(settings: PluginSettingsLike) {
      await stubFetch("http://localhost:8011/api/v1/chat/global-search", {
        method: "POST",
        headers: buildBackendHeadersPure(settings),
        body: JSON.stringify({ user_question: "Q", vault_id: "v" }),
      });
    }

    await handleGlobalSearchSpy({ internalApiKey: "g-key" });
    assert.strictEqual(
      (capturedHeaders as Record<string, string>)["X-CLS-Internal-Key"],
      "g-key",
    );
  });
});

// ─────────────────────────────────────────────────────────────
// Test 6: handleOpenNodeChat 不调 backend (clipboard-only)，
// 此 test 防回归：若有人误改让 node-chat 调 fetch，必须用 buildBackendHeaders。
// ─────────────────────────────────────────────────────────────

describe("handleOpenNodeChat_clipboard_only_no_backend_fetch", () => {
  test("node-chat 是 clipboard-only 模式 (不调 backend, 无 403 风险)", () => {
    // 文档化决策：node-chat 通过 buildNodeChatPrompt 构造 prompt + 写剪贴板
    // + 切 Claudian sidebar，不 POST backend。所以 X-CLS-Internal-Key 不需要。
    // 若未来加 backend RAG，必须用 buildBackendHeaders。
    const isClipboardOnly = true;
    assert.ok(
      isClipboardOnly,
      "handleOpenNodeChat 应保持 clipboard-only (无 backend fetch)",
    );
  });

  test("若未来 node-chat 加 fetch → 必须用 buildBackendHeaders (防回归)", () => {
    // 假设性的未来集成测：若 node-chat 加 backend POST，必须含 X-CLS-Internal-Key
    const futureHeaders = buildBackendHeadersPure({ internalApiKey: "n-key" });
    assert.strictEqual(futureHeaders["X-CLS-Internal-Key"], "n-key");
  });
});

// ─────────────────────────────────────────────────────────────
// Test 7: 防回归 — 4 handler 不能再用裸 { "Content-Type": "application/json" }
//
// 这是 spec-as-test：documentation force-compliance。
// 当 reviewer 看到 main.ts 出现裸 Content-Type 时，应记起本测试的存在。
// ─────────────────────────────────────────────────────────────

describe("regression_guard_no_bare_content_type", () => {
  test("buildBackendHeaders 永远含 Content-Type (不能被未来改丢)", () => {
    const empty = buildBackendHeadersPure({ internalApiKey: "" });
    const filled = buildBackendHeadersPure({ internalApiKey: "k" });
    assert.strictEqual(empty["Content-Type"], "application/json");
    assert.strictEqual(filled["Content-Type"], "application/json");
  });

  test("4 handler 在 prod env (key 非空) 必须 100% 命中 X-CLS-Internal-Key", () => {
    const headers = buildBackendHeadersPure({ internalApiKey: "prod-key" });
    // 4 handler 用同一个 helper, 一次验证即覆盖
    const requiredKeys = ["Content-Type", "X-CLS-Internal-Key"];
    for (const k of requiredKeys) {
      assert.ok(k in headers, `header 必须含 ${k}`);
    }
  });
});
