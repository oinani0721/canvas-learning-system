/**
 * Wave-5 Stage A (2026-05-12) — Vault indicator helpers.
 *
 * 用户原话:
 *   "我们使用涉及到 Neo4j 和 Graphiti 等后端数据存储,所以我们本身就是要在
 *    obsidian 中关于 Canvas learning system 中可以**明确分隔开来**"
 *
 * 目标:
 *   1. 4 个 hotkey handler Notice 加 `[vault: <vault_id>]` 前缀让用户每次触发都
 *      能"瞥见"当前 vault, 避免在错 vault 上操作。
 *   2. Obsidian status bar 常驻 vault 指示器（3 态: ✓ / ⚠ / ❌）。
 *
 * 本模块为 pure-function 层:
 *   - 不依赖 Obsidian runtime (可在 node:test 下直接 import)
 *   - main.ts 调用本模块的 build* / classify* 函数生成最终文本
 *   - 测试直接 unit-test 本模块, main.ts 是薄 wiring
 */

/**
 * 构造 Notice 前缀 `[vault: <vault_id>] ` (含尾空格, 直接拼接到 Notice 文本前).
 *
 * 用例:
 *   buildVaultPrefix("cs_61b") → "[vault: cs_61b] "
 *   new Notice(`${buildVaultPrefix(vaultId)}原 Notice 文案`)
 *
 * 空字符串 / undefined → fallback "default" (与 inferVaultId 一致):
 *   buildVaultPrefix("") → "[vault: default] "
 *   buildVaultPrefix(undefined) → "[vault: default] "
 */
export function buildVaultPrefix(vaultId: string | undefined): string {
  const id = vaultId && vaultId.trim() ? vaultId.trim() : "default";
  return `[vault: ${id}] `;
}

/**
 * Backend health classification — 3 态决策表。
 *
 * 输入:
 *   - ok: HTTP 200 response (健康)
 *   - vaultIdLocal: plugin 当前 vault_id (inferVaultId from app.vault.getName())
 *   - vaultIdRemote: backend /api/v1/vault/current 返回的 vault_id (可选)
 *
 * 输出: "ok" | "mismatch" | "down"
 *   - "ok": backend 200 + local == remote (或 remote 未知 = 不强制比对)
 *   - "mismatch": backend 200 但 local != remote (backend 挂在另一 vault)
 *   - "down": backend 非 200 / 不可达 / 超时 / 403
 *
 * 设计:
 *   - vaultIdRemote 为 undefined 时不触发 mismatch（兼容 backend 不返此字段时的版本）
 *   - case-insensitive 比对（sanitize_vault_id 已 NFKC + casefold）
 */
export type BackendHealthState = "ok" | "mismatch" | "down";

export function classifyBackendHealth(input: {
  ok: boolean;
  vaultIdLocal: string;
  vaultIdRemote?: string;
}): BackendHealthState {
  if (!input.ok) {
    return "down";
  }
  // backend 200 但若 remote vault_id 已知且与 local 不一致 → mismatch
  if (input.vaultIdRemote && input.vaultIdRemote.trim()) {
    const a = input.vaultIdLocal.trim().toLowerCase();
    const b = input.vaultIdRemote.trim().toLowerCase();
    if (a !== b) {
      return "mismatch";
    }
  }
  return "ok";
}

/**
 * 构造 status bar 显示文本 (3 态).
 *
 * - ok:       "🎓 cs_61b · ✓"
 * - mismatch: "🎓 cs_61b · ⚠ backend on another vault"
 * - down:     "🎓 cs_61b · ❌ backend down"
 *
 * 颜色用 status bar element 的 className 控制（main.ts 注入 css class）,
 * 本函数只负责文本生成 (易测).
 */
export function buildStatusBarLabel(input: {
  state: BackendHealthState;
  vaultId: string;
}): string {
  const id = input.vaultId && input.vaultId.trim() ? input.vaultId.trim() : "default";
  switch (input.state) {
    case "ok":
      return `🎓 ${id} · ✓`;
    case "mismatch":
      return `🎓 ${id} · ⚠ backend on another vault`;
    case "down":
      return `🎓 ${id} · ❌ backend down`;
  }
}

/**
 * 构造 status bar 元素的 css class (主题色控制).
 *
 * Obsidian status bar element 接受 className —— main.ts 拿这个 class 名注入
 * statusBarItem.className 切换颜色态.
 *
 * 设计:
 *   - 用 `canvas-vault-indicator` 作 base class (便于用户 css snippet override)
 *   - state-specific suffix: -ok / -mismatch / -down
 */
export function buildStatusBarClassName(state: BackendHealthState): string {
  return `canvas-vault-indicator canvas-vault-indicator-${state}`;
}
