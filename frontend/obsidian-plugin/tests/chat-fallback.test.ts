/**
 * Story 2.2+2.9 T1 (2026-05-11) — chat-with-context 降级路径单元测试
 *
 * 覆盖场景:
 *   - AC #2 "Given backend 响应慢于 plugin timeout / When 等待超时 / Then 降级到本地"
 *   - prompt 头部含 Degradations marker (Skill 端识别)
 *   - 保留 /chat-with-context skill 前缀（不混淆为 /node-chat）
 *   - HTML 注释格式（Obsidian-safe）
 *   - 两种 reason: backend_timeout / backend_unreachable
 */

import { test } from "node:test";
import { strict as assert } from "node:assert";
import { buildChatWithContextFallbackPrompt } from "../src/node-chat-context";

test("buildChatWithContextFallbackPrompt: backend_timeout reason 写入 marker", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt: "/node-chat\n\nnode body",
  });
  assert.ok(
    result.includes("Degradations: backend_timeout"),
    "marker must include backend_timeout reason",
  );
  assert.ok(result.includes("fallback=local_metadata"));
  assert.ok(result.includes("hop=1"));
});

test("buildChatWithContextFallbackPrompt: backend_unreachable reason 写入 marker", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_unreachable",
    localPrompt: "/node-chat\n\nnode body",
  });
  assert.ok(
    result.includes("Degradations: backend_unreachable"),
    "marker must include backend_unreachable reason",
  );
});

test("buildChatWithContextFallbackPrompt: 保留 /chat-with-context skill 前缀（不混淆为 /node-chat）", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt: "/node-chat\n\nnode body",
  });
  assert.ok(
    result.startsWith("/chat-with-context"),
    "降级 prompt 必须以 /chat-with-context 开头，保持用户视角连续",
  );
  assert.ok(
    !result.startsWith("/node-chat"),
    "降级 prompt 不能直接以 /node-chat 开头（避免用户混淆两个 skill）",
  );
});

test("buildChatWithContextFallbackPrompt: marker 是 HTML 注释格式（Obsidian 渲染时不暴露给用户）", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt: "body",
  });
  // marker 必须包裹在 <!-- ... --> 中
  assert.match(
    result,
    /<!--\s*Degradations:\s*backend_timeout[^>]+-->/,
    "marker must be HTML comment so Obsidian doesn't render it visibly",
  );
});

test("buildChatWithContextFallbackPrompt: localPrompt 正文被保留", () => {
  const localPrompt = "/node-chat\n\nspecific body content with neighbors";
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt,
  });
  assert.ok(
    result.includes("specific body content with neighbors"),
    "localPrompt body 必须保留在最终 prompt 里",
  );
});

test("buildChatWithContextFallbackPrompt: prompt 结构顺序 (skill 前缀 → marker → body)", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_unreachable",
    localPrompt: "BODY",
  });
  const skillIdx = result.indexOf("/chat-with-context");
  const markerIdx = result.indexOf("<!-- Degradations:");
  const bodyIdx = result.indexOf("BODY");
  assert.ok(skillIdx === 0, "skill 前缀必须在 prompt 最开头");
  assert.ok(
    markerIdx > skillIdx && markerIdx < bodyIdx,
    "marker 必须在 skill 前缀和 body 之间（顺序: skill → marker → body）",
  );
});

test("buildChatWithContextFallbackPrompt: hop=1 marker（用户视角无功能损失，仅邻居数从 N-hop 降到 1-hop）", () => {
  const result = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt: "body",
  });
  assert.ok(
    result.includes("hop=1"),
    "marker 必须明示 hop=1, 让 Skill 知道邻居只有 1-hop（vs backend N-hop）",
  );
});

test("buildChatWithContextFallbackPrompt: 两种 reason 输出不同 prompt（防 reason 字段被吞）", () => {
  const a = buildChatWithContextFallbackPrompt({
    reason: "backend_timeout",
    localPrompt: "body",
  });
  const b = buildChatWithContextFallbackPrompt({
    reason: "backend_unreachable",
    localPrompt: "body",
  });
  assert.notStrictEqual(
    a,
    b,
    "不同 reason 必须产生不同 prompt（防 reason 被硬编码吞）",
  );
});
