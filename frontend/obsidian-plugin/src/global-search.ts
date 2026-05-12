/**
 * Story 2.10 (2026-05-12) — `canvas:global-search` 全局搜索教学笔记
 *
 * 区别于 `canvas:chat-with-context`（Cmd+Shift+E）：
 *   - chat-with-context 要求 active file 在 `节点/<concept>.md` 下（isNodePath 守门）
 *   - global-search 在任意视图（Dashboard / 教学笔记 / 设置 tab 等）都可触发，
 *     不依赖 active file，让用户从全局发起教学笔记搜索。
 *
 * 设计要点：
 *   - timeout 8000ms（vs chat-with-context 3000ms）— deep search 给 backend 多预算
 *   - subject_id = null → backend 按"一 vault 一学科"约定从 .canvas-config.yaml fallback
 *   - 失败不 crash：AbortError / TypeError(fetch reject) / 非 200 → 友好 Notice
 *
 * 纯函数模块，方便单元测试（不依赖 obsidian API）。
 * obsidian 端的 fetch / clipboard / Notice 由 main.ts handleGlobalSearch 编排。
 */

/** Backend 端 supplementary 降级时返回的 reason 集合（参考 chat/enrich-context 兼容） */
export type GlobalSearchDegradeReason =
  | "supplementary_disabled"
  | "supplementary_timeout"
  | "supplementary_error"
  | "graph_unavailable"
  | string;

export interface GlobalSearchRequest {
  user_question: string;
  vault_id: string;
  subject_id: string | null;
}

export interface GlobalSearchResponse {
  enriched_context: string;
  supplementary_count?: number;
  supplementary_degraded?: boolean;
  supplementary_reason?: GlobalSearchDegradeReason | null;
}

export type GlobalSearchFailureReason =
  | "backend_timeout"
  | "backend_unreachable"
  | "backend_error"
  | "non_json_response";

/** 全局搜索请求 timeout（ms）— 比 chat-with-context (3000ms) 大，给 deep search 留预算。 */
export const GLOBAL_SEARCH_TIMEOUT_MS = 8000;

/**
 * 构造发给 backend 的 POST payload。
 *
 * 一 vault 一学科约定：subject_id 总是传 null，让 backend 从
 * `.canvas-config.yaml` 推断当前学科。这避免 plugin 端硬编码 subject。
 */
export function buildGlobalSearchPayload(opts: {
  userQuestion: string;
  vaultId: string;
}): GlobalSearchRequest {
  return {
    user_question: opts.userQuestion,
    vault_id: opts.vaultId,
    subject_id: null,
  };
}

/**
 * 把 fetch 抛出的错误归类成稳定的失败原因。
 *
 * - AbortError → backend_timeout（AbortController 触发）
 * - TypeError / 其他 → backend_unreachable（fetch 端 reject，通常是 docker 没起 / 网络断）
 */
export function classifyFetchFailure(err: unknown): GlobalSearchFailureReason {
  if (err instanceof DOMException && err.name === "AbortError") {
    return "backend_timeout";
  }
  return "backend_unreachable";
}

/**
 * 把成功响应包装成给用户看的 Notice 文案。
 *
 * 规则：
 *   - 主行: `⭐ 已组装全局搜索: {N} 补充材料 / {elapsed_ms}ms — 切到 Claudian 粘贴`
 *   - 当 supplementary_degraded=true → 追加 ` (degraded: <reason>)` 后缀
 *   - supplementary_count 缺失时取 0（防 NaN 字符串）
 */
export function buildSuccessNoticeMessage(opts: {
  response: GlobalSearchResponse;
  elapsedMs: number;
}): string {
  const count = opts.response.supplementary_count ?? 0;
  const base = `⭐ 已组装全局搜索: ${count} 补充材料 / ${opts.elapsedMs}ms — 切到 Claudian 粘贴`;
  if (opts.response.supplementary_degraded) {
    const reason = opts.response.supplementary_reason ?? "?";
    return `${base} (degraded: ${reason})`;
  }
  return base;
}

/**
 * 失败 Notice 文案：永远以 `⚠️ 全局搜索失败` 开头 + 括号注明 reason + 检查后端提示。
 */
export function buildFailureNoticeMessage(reason: GlobalSearchFailureReason): string {
  return `⚠️ 全局搜索失败 (${reason}) — 请检查后端`;
}
