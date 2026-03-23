# ADR-001: 对话引擎选型 — Spawn 官方 Claude Code CLI

**状态**：⚠️ 实现方案已演进至 Agent SDK sidecar（2026-03-19）。核心决策（订阅额度、Spawn CLI 路线）仍有效，但具体实现路径已从直接 spawn CLI 演进为 Node.js sidecar 运行 Agent SDK。原确认日期：2026-03-16
**决策者**：ROG
**来源 Session**：Epics-Stories 创建 session（Party Mode 深度调研）

---

## 决策背景

Canvas Learning System 的每个知识节点需要独立的 AI 对话 session（FR-AGENT-02）。用户已有 Claude Code Max/Pro 订阅，不想为对话额外付 API 费用。需要选择对话引擎的实现方案。

## 考虑过的方案

| 方案 | 描述 | 成本 |
|------|------|------|
| **A. Claude Agent SDK + API Key** | SDK 直接调 Anthropic API | API 按量付费（额外） |
| **B. Spawn 官方 Claude Code CLI** | spawn 官方 claude binary，CLI 自己处理认证 | 用户已有订阅（免费） |
| **C. ACP 标准协议** | Agent Client Protocol，多引擎支持 | 取决于引擎 |
| **D. 直接使用 OAuth Token** | 提取 token 直调 API | ❌ 被 Anthropic 禁止 |

## 各方案权衡

| 维度 | A (SDK+API Key) | **B (Spawn CLI)** ✅ | C (ACP) | D (OAuth) |
|------|-----------------|---------------------|---------|-----------|
| **成本** | 额外付费 | **免费（订阅）** | 同 B | 违规风险 |
| **合规** | ✅ 完全合规 | ✅ 社区验证+Anthropic 默认允许 | ✅ 合规 | ❌ 违反 ToS |
| **per-node session** | Options.resume | **--resume session_id** | session/load | — |
| **MCP 注入** | Options.mcpServers | **--mcp-config** | session/new mcpServers | — |
| **上下文注入** | system prompt | **--append-system-prompt** | session/prompt context | — |
| **streaming UI** | StreamEvent 原生 | **stream-json NDJSON** | session/update 通知 | — |
| **社区验证** | Claudian v1.3.68 | **Pencil+Claudian+Zed+OpenCode proxy** | Zed+Agent Client | ❌ |
| **引擎可替换** | Claude only | Claude only | **多引擎** | — |
| **复杂度** | 低 | 中 | 中 | — |
| **政策风险** | 无 | 低（Anthropic 可能收紧） | 无 | 高 |

## 决定：方案 B（Spawn 官方 Claude Code CLI）

**理由**：
1. **成本为零** — 用户已有 Claude Code Max/Pro 订阅，spawn 官方 binary 继承认证
2. **社区验证充分** — Pencil "Connected via subscription"、Claudian spawn 模式、Zed ACP、opencode-claude-max-proxy 均在生产运行
3. **Anthropic 默认允许** — 2026-02-19 官方澄清"现有用法模式保持不变"，禁令只针对直接使用 OAuth token（方案 D）
4. **技术完全可行** — CLI 支持 `-p`/`--resume`/`--mcp-config`/`--append-system-prompt`/`--output-format stream-json`，满足全部 FR

**否决理由**：
- **方案 A（API Key）**：额外成本，用户明确诉求不想另付费
- **方案 C（ACP）**：长期可选（多引擎），但 MVP 阶段增加不必要复杂度
- **方案 D（直接 OAuth）**：违反 Anthropic ToS，已被服务端封杀（2026-01-09）

## 具体实现方案

> **⚠️ 2026-03-19 更新**：实现路径已从下方原始方案演进为 **Agent SDK sidecar 模式**：
> Tauri 2 桌面壳 + React 前端 + Node.js sidecar（运行 Agent SDK）。
> 演化链：Mode D → SDK直接嵌入（Tauri WebView不支持Node.js）→ Tier B增强CLI（CLI hanging + Tauri spawn bug）→ **Agent SDK sidecar**（当前活跃）。
> 核心决策（订阅额度、CLI spawn）不变，但宿主环境从 Obsidian Plugin 改为 Tauri + Node.js sidecar。

```
# 原始方案（2026-03-16，已被 sidecar 模式取代）
Obsidian Plugin (Svelte UI)
  → @anthropic-ai/claude-agent-sdk query()
    → spawnClaudeCodeProcess (自定义 spawn 回调)
      → 官方 claude binary（自动继承 ~/.claude/.credentials.json）
        → --resume $nodeSessionId
        → --mcp-config ./canvas-mcp.json (FastAPI 后端工具)
        → --append-system-prompt $nodeContext (Tips/错误/Edge理由)
        → --output-format stream-json
  → StreamEvent 驱动 Svelte Store → UI 响应式更新
```

**参考实现**：
- Claudian 源码 `YishenTu/claudian` — spawn 模式、session 管理、crash recovery
- Zed ACP `zed-industries/claude-agent-acp` — 标准化协议
- opencode-claude-max-proxy `rynfar/opencode-claude-max-proxy` — CLI proxy 模式

## Fallback 策略

如果 Anthropic 未来封禁 spawn 模式：
1. FR-AGENT-03（引擎可替换）保证切换成本可控
2. 回退方案 A（Claude Agent SDK + API Key）
3. 或切换到 ACP 支持的其他引擎（Codex/Gemini CLI）

## 风险与缓解

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| Anthropic 收紧 spawn 政策 | 中 | FR-AGENT-03 引擎可替换 + API Key fallback |
| CLI 每次 spawn ~12s 开销 | 中 | 使用 SDK Client Mode 长连接复用进程 |
| stream-json 工具事件不如 SDK StreamEvent 细粒度 | 低 | SDK 内部已封装，StreamEvent 可用 |
| session 文件 crash 导致 Claude Code 崩溃 | 低 | 参考 Claudian crash recovery（缓存 lastSentMessage + 进程重启重试） |

## 调研证据

- 15 个并行 Deep Explore Agent 调研（2026-03-16）
- Pencil 截图确认 "Connected via subscription"
- Anthropic 2026-02-19 官方澄清 "Nothing changes around how customers have been using their account"
- Claudian 源码分析（customSpawn.ts / MessageChannel.ts / SessionManager.ts）
- Claude Code CLI 完整参数验证（-p / --resume / --mcp-config / --output-format stream-json）
- ACP 协议规范分析（JSON-RPC 2.0 / session 管理 / 权限控制）

## 相关 FR

- FR-AGENT-01: 前端通过 Claude Agent SDK 驱动，Tool-UI Bridge 模式
- FR-AGENT-02: Agent 对话支持 per-node 独立 Session
- FR-AGENT-03: Agent 引擎可替换（不锁定厂商）
- FR-MCP-01: 后端通过 MCP 协议暴露核心算法能力
