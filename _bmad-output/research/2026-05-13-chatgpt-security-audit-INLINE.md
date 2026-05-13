---
title: "ChatGPT Deep Research 安全审查 (2026-05-13)"
date: "2026-05-13"
source: "ChatGPT-5 Pro Deep Research mode"
prompt_used: "_bmad-output/research/2026-05-13-chatgpt-对抗审查-核心闭环可行性.md"
pivot_status: "PIVOTED — 偏题做了安全审查而非闭环可行性审查"
value_assessment: "意外高价值 — 8 个 Claude 完全漏看的安全维度"
user_decision: "立即修 4 个 Critical 安全 bug (Path α)"
---

# ChatGPT Deep Research 安全审查归档

## Claude Pivot 诊断

ChatGPT 没回答原 prompt 的核心问题（10 个 Gap 打分 / 7 个对抗问题 / 闭环 Verdict），跑了独立的安全审查。Pivot 原因：Deep Research 模式 + GitHub connector 让它扫真实仓库时发现一堆安全维度，焦点偏离。

**净效果**：本案 net positive — ChatGPT 在 Claude 5 Agent 没覆盖的 auth/network/security 维度找到 8 个高价值发现。

## Cross-check 表（核心交付）

| # | ChatGPT 发现 | 严重度 | Claude 提过吗 |
|---|---|---|---|
| 1 | Memory API 未统一鉴权 — 任何匿名主体可读写他人学习历史 | Critical | ❌ 完全漏看 |
| 2 | `/memory/extract-conversation` 默认 fail-open — `SIDECAR_OBSERVER_TOKEN` 未配置时任意人可往 Graphiti 写 misconception | Critical | ❌ 完全漏看 |
| 3 | MCP `/mcp/tools/*` 网络可达 — 18 个工具路由可被外部 JSON-RPC 直接调 | Critical | ❌ 完全漏看 |
| 4 | DEBUG=True + key fail-open 危险默认值 | Critical | ⚠️ Round-23 ChatGPT v2 verdict 提过但未实施 |
| 5 | WebSocket `/ws` 无鉴权 + 全局 mastery 广播 | Medium | ❌ 漏 |
| 6 | `/system/health` 泄露文件路径 + 异常摘要 | Medium | ❌ 漏 |
| 7 | Tauri `CSP: null` 桌面 XSS 放大 | Medium | ⚠️ 提过 frontend @deprecated 但没扎实评估 |
| 8 | 供应链 + secret scan 不足 | Medium | ❌ 漏 |

## 反直觉关键 finding

**正交视角**：Claude 评估"批注**功能闭环**是否打通"，ChatGPT 评估"批注**作为数据资产**是否安全"。两者完全正交但同等重要。

**武器化风险**：如果 Memory API 任何人可以匿名调（#1），那即便 Claude 评估的 10 个功能 Gap 全修了，攻击者也可以匿名往用户 Graphiti 注入伪批注，让 AI 按"假误解"给用户出针对性考题 — 这是把用户的核心闭环武器化。

## ChatGPT 给的 P0 修复路径（已被 user 采纳）

| Task | 工时估算 | 状态 |
|---|---|---|
| P0-1 observer fail-closed | 1-2h | in_progress |
| P0-2 DEBUG=False + dev bypass 开关 | 1-2 天 | pending |
| P0-3 Memory API 统一鉴权 | 2-3 天 | pending |
| P0-4 MCP 工具面认证 + loopback only | 2-4 天 | pending |

**总工时**：6-10 天（与 Round-23 ChatGPT DR 估算"硬化版 134-192h"前半段吻合）

## ChatGPT 完整 response

由于 ChatGPT response 长达 5000+ 字（含 60+ `fileciteturn` GitHub 引用），完整内容在 Claude conversation log 里保留。归档此文件主要为后续 ChatGPT vN 对照用。

如需查询 ChatGPT 原文细节：参考本 session 用户消息中粘贴的"# Canvas Learning System 对抗性安全审查报告"段全文。

## 历史对照

ChatGPT 已经**第 3 次**提到"生产默认值收紧"P0：
- `_bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md` — Round-23 提到 1-2d
- `_bmad-output/research/chatgpt-adversarial-review-wave2-v4-INLINE-2026-05-12.md` — wave-2 v4 验证
- `_bmad-output/chatgpt-review-response-2026-05-11.md` — 全链路对抗审查 P0-B

本次决策"立即修"是该 P0 的最终落地。

## 下一步追踪

每个 P0 修复 commit 一次（按 Boris 最小验收单位原则），让 user 能 incremental review。每个 commit 都引用本文件作为 ChatGPT 审查证据。
