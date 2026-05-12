# ⚠️ Tauri 前端已 DEPRECATED (architecture 2026-04 决策)

> **Status**: DEPRECATED
> **决策日期**: 2026-04 (Obsidian Hybrid 降级路径,见 `_bmad-output/.claude/CLAUDE.md` "Obsidian Hybrid 已从 Tauri v0 降级")
> **保留原因**: git history + 参考价值 (设计文档 / RAG 集成 / SSE streaming 模式可借鉴)
> **当前生效前端**: `frontend/obsidian-plugin/` (Obsidian Hybrid 路径)

---

## 受 DEPRECATED 范围的目录与文件

| 路径 | 内容 | 状态 |
|---|---|---|
| `frontend/src/` | Tauri React app source (含 chat / canvas / settings UI) | DEPRECATED |
| `frontend/src-tauri/` | Tauri Rust shell (window / IPC / native bridge) | DEPRECATED |
| `frontend/sidecar/` | Tauri sidecar (Claude Agent SDK Node 进程) | DEPRECATED |
| `frontend/index.html` | Tauri Vite entry | DEPRECATED |
| `frontend/vite.config.ts` / `vitest.config.ts` | Tauri build / test config | DEPRECATED |
| `frontend/tsconfig.json` / `tsconfig.node.json` | Tauri TypeScript config | DEPRECATED |
| `frontend/stryker.config.json` | Tauri mutation testing config | DEPRECATED |
| `frontend/package.json` / `package-lock.json` | Tauri build deps | DEPRECATED (npm install 仍可,但不建议) |

**唯一例外**: `frontend/obsidian-plugin/` — 这是 Obsidian Hybrid 部署的现役代码,**不 deprecated**。

---

## 已知安全风险 (deprecation 前历史负债)

### P0: `frontend/src/services/api-key-engine.ts` 浏览器直连 LLM

ChatGPT 对抗审查 (2026-05-12) 揭示:
- 浏览器直接 `fetch('https://api.anthropic.com/v1/messages', ...)`
- API key 通过 `x-api-key` header 暴露在 fetch
- 设置 `anthropic-dangerous-direct-browser-access: true` (Anthropic 文档明文警告 prod 勿用)
- API key 存 `sessionStorage` (同源 JS 可读 → XSS 风险)
- 对话历史存 `localStorage` (永久 + 同源可读)

**当前缓解**: Tauri 前端不在 Hybrid 部署路径,用户使用的 Obsidian 插件 (`frontend/obsidian-plugin/`) **不**含此模式。

**永久修法 (如复活 Tauri)**: 改走后端代理 (`POST /api/v1/llm/proxy`),前端不持 API key。

---

## CI / build 行为

- ✅ 根 `package.json` 的脚本 (lint:plugin / build:plugin / deploy:plugin / verify:plugin) 全部只指向 `frontend/obsidian-plugin/`,**不构建 Tauri**
- ✅ `lefthook.yml` pre-commit / pre-push hook glob 已 scope 到 `frontend/obsidian-plugin/{src,tests}/**/*.{ts,tsx}`,**不触发 Tauri 文件**
- ✅ `.github/workflows/*.yml` 不引用 Tauri 路径
- ⚠️ `frontend/package.json` 自带 `dev` / `build` / `test` 脚本仍可手工 `cd frontend && npm test` 跑,但 CI 默认不调

---

## 如未来复活 Tauri 路径

必须先解决:
1. **P0 安全**: api-key-engine 改后端代理,前端不持 key
2. **架构对齐**: 与 Obsidian Hybrid 决策协调,避免双前端并存歧义
3. **deps 重新审计**: Tauri 2 / Vite 6 / React 19 已更新,本目录可能有未跟进的 CVE
4. **集成测试**: post-turn-extract / global-search / multi-vault 隔离需在 Tauri 路径重新验证

在 done 前,**不要把这部分代码 build/ship 给用户**。

---

*Marked DEPRECATED on 2026-05-12 by wave-3 hotfix (ChatGPT 项目审查 P0 finding A). See commit history for context.*
