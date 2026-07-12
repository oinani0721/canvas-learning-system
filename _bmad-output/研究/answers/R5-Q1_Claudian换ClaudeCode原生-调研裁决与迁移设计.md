---
title: "R5-Q1 · 把 Claudian 换成 Claude Code 会不会更好——会，而且比想象中容易得多"
date: 2026-07-13
round: R5
question: Q1
source_file: _bmad-output/研究/answers/R4-Q2_对话记忆写入实现设计-不挂MCP用归档钩子.md
source_line: 33
category: research
parent: "[[批注总索引表-2026-07-12]]"
---

# R5-Q1 · Claudian → Claude Code 原生：调研裁决与迁移设计

> 产出方式: 3 路并行 agent deep explore（Claudian 依赖面审计 / 原生工作流设计 / 对比裁决与迁移），含对已安装 Claudian 的源码级取证、你的真实用量统计、官方文档核对。

## 批注原文

> **User：我们把 claudian 改为 claude code 来使用会不会更好，更成熟，我们改为 Canvas learning systeam 用于 obsidian 加 claude code**

## 一句话核心结论

**会更好，你的判断是对的**——而且有一个让这个决定变得非常轻松的事实：你的全部资产（8 个 skill、检索钩子、配置）**本来就是标准 Claude Code 格式**，Claudian 只是把 Claude Code 嵌进 Obsidian 侧栏的第三方壳。切换的必做工作只有**一个配置文件搬家（5 分钟）**，Claudian 不必卸载（降级为可选侧栏），产品定位改为「**Canvas Learning System for Obsidian + Claude Code**」成立。

## 一 · 为什么"更成熟"是实锤而不只是感觉

| 维度 | Claudian（第三方壳） | Claude Code 原生 |
|---|---|---|
| 身份 | 单作者第三方插件（虽然很活跃：13.9k stars、昨天刚发新版），内部行为**无文档**——我们已付过一次"逆向工程税"（一个配置字段位置写错导致检索工具静默失效，被迫读它源码定位） | Anthropic 官方产品，hooks/MCP/skills 全部官方文档保证 |
| **会话归档钩子**（Phase 2 刚需） | ⛔ **判负**：对已装版本源码取证，SessionEnd 引用 = 0 次；且它关会话时只给子进程 3 秒就强杀——任何超 3 秒的归档动作会死在半路 | ✅ 官方保证 SessionEnd **每会话恰好触发一次** |
| 版本现状 | 你装的版本已**落后 30 个发布** | 官方更新节奏 |
| 单点风险 | 全景报告 D6：插件停更/跟不上 CLI 变更 = 检验白板域整体熄火 | 官方产品，且切换后 Claudian 死不死都不影响关键链路 |

**你的用量实证也支持现在切**：Claudian 的 30 个会话集中在 4 月 20 日—5 月 13 日（当时真实高频使用），**近两个月零新会话**——切换的习惯成本正处于低点。

## 二 · 切换成本盘点——比想象中小一个数量级

审计结果：Claudian 对整个系统的**可执行依赖只有一处**（插件"节点对话"命令调它打开侧栏，且自带降级提示），其余 20+ 处提及全是文案。三项真实损失（全部非致命）：侧栏不切窗口、当前笔记自动注入（skill 已有回退）、Obsidian 内会话历史面板。

**社区早已收敛出你要的范式**：「vault 即代码库，Claude Code 工作目录 = vault」——Obsidian 只做渲染和手写层，它的文件监听会自动热刷新 Claude 改过的文件，两个应用零桥接天然协作（Mac 分屏后稳态零切换）。

**意外红利**：原生形态下两个老流程反而能简化——节点对话现在要把 10KB 上下文塞剪贴板（补偿侧栏年代的产物），原生只需复制一行命令，Claude Code 自己去读文件；派生节点的 AI 填正文未来可以完全免剪贴板（批量找待填标记）。

## 三 · 落地四步（总计约 1 小时 + 两周试用）

1. **第 0 步 · 唯一必做（5 分钟）**：在 vault 根新建 `.mcp.json`（把现有 MCP 配置从 Claudian 的私有位置搬到 Claude Code 标准位置）——不做这步，原生会话里 skill 看不到后端检索工具。原文件保留，对两边都无害
2. **第 1 步 · 开始用（零改动）**：终端 `cd` 到 vault 跑 `claude` 即可——8 个 skill、检索钩子、CLAUDE.md 全部零改动生效。⚠️ 官方桌面 App 体验更好但有一个**必须先实测的陷阱**：它对 git 仓库会自动做隔离副本，可能导致 Obsidian 看不到改动——CLI 无此坑，先用 CLI
3. **第 2 步 · 兑现净新增能力**：加上会话归档钩子（SessionEnd）——这是本次切换**唯一的新增能力**，恰好就是 Phase 2 对话记忆管道的触发器，一石二鸟
4. **第 3 步 · 两周试用后定稿**：重流程（出题/评分/归档）走 Claude Code，轻交互想留侧栏就留 Claudian（若留，建议先把它从落后 30 版升到最新）。试用期后把产品定位与文档改为「for Obsidian + Claude Code」（约 30 分钟文案量）

## 四 · 对 Phase 2 路线图的影响

这个决定**解锁而非推迟** Phase 2：对话记忆管道的触发器（会话收尾钩子）在 Claudian 里是结构性不可靠的（3 秒强杀），在原生里是官方保证——所以「改用 Claude Code」实质上是 Phase 2 的**前置条件**，两个决定互相成全。

- **User：**
**那么请你改为 claude code 然后重新进行规划开发路径**

> **[A6 2026-07-13 → round6]** ✅ 已执行：① 切换第 0 步完成——标准 `.mcp.json` 已落位双 vault 副本，**你现在终端 `cd canvas-vault && claude` 即可用原生形态（skill/钩子/检索全部就绪）**；② ChatGPT DR 报告交叉验证完成——它带来两个关键新证据（LM Studio #1773 Qwen reasoning 空 content / llama.cpp #21228 嵌套 schema 静默失守），修正了内部"单运行时"方案为"多服务分工 + canary 门控 + fail-closed"；③ 开发路径已重新规划为路线图 v2（M0✅→M1 canary→M4 速赢→M2→M3→M5），详见 [[2026-07-13-开发路线图v2-ClaudeCode原生+本地模型激活|📚 路线图 v2]]。M1 canary 工具开发中。
## 关联

- [[R4-Q2_对话记忆写入实现设计-不挂MCP用归档钩子|📚 R4-Q2]]（被批注的上文，归档钩子设计）
- [[R4-Q1_Mac部署方式内部调研-llama-server胜出|📚 R4-Q1]]
- [[批注总索引表-2026-07-12]]
