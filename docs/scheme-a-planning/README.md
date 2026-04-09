---
title: Scheme A Planning Archive
subtitle: Claudian + Obsidian 降级架构设计文档归档
status: design-archive
scope: not-implementation
primary-prd: 14-scheme-a-implementation-prd.md
primary-prd-version: v5 (Plan v23)
imported-at: 2026-04-09
imported-from: /Users/Heishing/Desktop/spring course 2026/CS 61B/
imported-by: Plan v24 Part A
ci-coverage: false
purpose: Enable ChatGPT Deep Research ongoing reference during Phase 1
---

# Scheme A Planning Archive

> **This is a design document archive, NOT implementation code.**
>
> 实施代码位于 `backend/` 和 `frontend/sidecar/` · 本目录仅用于：
> 1. ChatGPT Deep Research 在 Phase 1 期间的 ongoing 参考（GitHub link-based access）
> 2. Plan v15 → v23 的版本演化历史归档
> 3. 三方审查报告与 4-layer nested errata pattern 的证据保留
>
> **不在 Canvas 主 repo 的 CI / test coverage 范围内。**

## 背景

Canvas Learning System 在 Plan v12 提出"降级方案"：用 Claudian plugin + Obsidian vault 替代部分 Canvas 前端功能 · 保留 Canvas backend 的 13 核心服务与 15 MCP 工具作为运行时底座。

Scheme A 指代这个降级架构的完整 PRD 设计。Plan v15 → v16（三方审查） → v19（prompt v2） → v21（fix-7 + prompt v3） → v23（fix-5 + 真实运行证据）是 5 次迭代 · 每一次都响应前一次发现的 layer-N errata。

**核心发现（Plan v23 §7.6.5）**：运行级证据比审查共识更重要 · 之前的 4 轮审查都错过了 UserPromptSubmit hook 的架构层归属（真实位置：Claude Code Desktop `~/.claude/settings.json` · 不是 Canvas backend）· 这类"只有 real-run 才能暴露"的盲点是 Phase 1 Day 1 Spike 1/2/3 的存在理由。

## 文件清单与阅读顺序

| # | 文件 | 大小 | 行数 | 角色 | 读者应该先看 |
|---|---|---|---|---|---|
| 1 | [`14-scheme-a-implementation-prd.md`](./14-scheme-a-implementation-prd.md) | 371 KB | 7594 | **主 PRD v5**（Plan v23 产物） | ⭐ ChatGPT Deep Research 从这里开始 |
| 2 | [`16-triangulated-review-report.md`](./16-triangulated-review-report.md) | 131 KB | 2531 | 三方审查报告 + §1.5.8/§1.5.9 四层 nested errata | ⭐ 理解"为什么需要 real-run" |
| 3 | [`21-prd-v5-changelog.md`](./21-prd-v5-changelog.md) | 42 KB | 736 | Plan v23 changelog（5 项 Fix-11~15 + 真实运行输出） | 第三优先 |
| 4 | [`19-prd-v4-changelog.md`](./19-prd-v4-changelog.md) | 43 KB | 765 | Plan v21 changelog（7 项 Fix-4~10） | 历史参考 |
| 5 | [`20-adversarial-review-prompt-v3.md`](./20-adversarial-review-prompt-v3.md) | 44 KB | 773 | Plan v21 第三轮 ChatGPT review prompt | 历史参考 |
| 6 | [`17-prd-v3-changelog.md`](./17-prd-v3-changelog.md) | 29 KB | 673 | Plan v19 changelog | 最老的历史 |

**推荐阅读顺序**：14 → 16（§1.5.8 + §1.5.9）→ 21 → 其他。

## 版本演化链

```
Plan v15 (Scheme A 首版)
  ↓ 三方审查（ChatGPT / Gemini / Claude）
Plan v16 → 16-triangulated-review-report.md §1.5（layer-1/2 errata）
  ↓ Fix-1~3
Plan v19 → 17-prd-v3-changelog.md
  ↓ 第二轮 adversarial review（prompt v2 = 18-*.md · 已归档在 CS 61B）
Plan v21 → 19-prd-v4-changelog.md（Fix-4~10） + 20-adversarial-review-prompt-v3.md
  ↓ 第三轮 adversarial review（layer-3 errata 暴露）
Plan v22 → （版本错配事件 · 中途发现 ChatGPT 读的是陈旧本地副本）
  ↓ Plan v23（触发"入库到 GitHub 让 ChatGPT link-based 访问"的需求）
Plan v23 → 14-scheme-a-implementation-prd.md v5 + 16-report §1.5.9（layer-4 erratum）+ 21-changelog
  ↓ 真实运行证据（§7.6.5）
Phase 1（当前）
```

## 为 ChatGPT Deep Research 的访问指引

**入口 URL**：
```
https://github.com/oinani0721/canvas-learning-system/tree/main/docs/scheme-a-planning/
```

**主 PRD 直链**：
```
https://github.com/oinani0721/canvas-learning-system/blob/main/docs/scheme-a-planning/14-scheme-a-implementation-prd.md
```

**使用场景**：
- Phase 1 实施期间遇到架构疑问 → 让 ChatGPT 读 14-PRD 对应 section（尤其是 §7.6.x 运行级证据 + §10.1 Phase 1 任务清单）
- 遇到新盲点 → 让 ChatGPT 对照 16-report §1.5 的 errata 分类决定是否构成 layer-5

**⛔ 不用于**：
- ❌ **第四轮正式 review**（Plan v23 决策锁定：不做）
- ❌ 作为"权威事实源"引用 · 14-PRD 本身是 v5 设计文档 · 不是代码实现
- ❌ 质疑 main repo 最新 commit 的代码 · 应改用 `/blob/main/backend/app/...` 直接读实际代码

## 四层 nested errata pattern（关键概念）

PRD 迭代过程中发现：每次审查都修了前一轮的 errata · 但新的 errata 又在更深层暴露。Plan v23 确认这个 pattern 是 **不可避免** 的 · 理性策略是：

| Layer | 示例 | 发现方式 |
|---|---|---|
| L1 | 句法 / 拼写 / 链接错误 | 审查者快速扫描 |
| L2 | 事实错误 · 过期 API · 版本号 | Context7 查文档对比 |
| L3 | 架构层误判（如 UserPromptSubmit hook 归属）| 需要对架构有深度理解的审查者 |
| L4 | Meta-errata：审查共识本身是错的 | 需要跨审查者 triangulation + real-run |
| **L5** | Real-run-only：代码能跑但行为不符预期 / 启动失败 / runtime 警告 | ⭐ **只有真实运行** 能暴露 |

详见 `16-triangulated-review-report.md` §1.5.8（L4 defense）+ §1.5.9（L5 inevitability）。

## Phase 1 Day 1 Spike 与本归档的关系

Phase 1 Day 1 Spike 1/2/3 的目的是**暴露 L5 盲点**：
- **Spike 1**：Canvas 后端 13 服务 + 15 MCP 工具启动验证
- **Spike 2**：`canvas_agentic_rag` import 重跑（Plan v23 Stage 1 已完成一次）
- **Spike 3**：UserPromptSubmit hook 在 `~/.claude/settings.json` 的实际配置 + 测试

Spike 的真实运行输出会记录到 `phase-1-day-1-spike-results.md`（与本 README 同目录）· 为 Plan v23 v5 提供 L5 证据补充。

## 路径引用说明

14-PRD 内部的文件路径（如 `backend/lib/agentic_rag/__init__.py`）**以 repo 根目录为基准** · 不以本目录为基准。这是因为 PRD 原本起草于 CS 61B sibling 目录 · 现在 commit 到主 repo 后 · 所有相对路径语境自动对齐到 repo 根。

如果 PRD 中某处路径看起来 broken · 优先检查是否 repo 根下的真实路径：
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system
ls <path-from-prd>
```

## 与 Canvas 原生 `docs/prd/` 的区别

Canvas 主 repo 已有：
- `docs/prd/` · `docs/prd-phase3-phase4.md` · `docs/PRD-v2-chinese.md` · `docs/PRD-v3-execution-checklist.md`

这些是 **Canvas 原生功能** 的 PRD（不涉及 Scheme A 降级方案）。本目录 `scheme-a-planning/` 是 **降级架构** 的独立设计 · 两者**概念上并列** · 实施顺序：先验证 Scheme A 降级层（Phase 1 Day 1 Spike）· 再决定是否启动 Phase 1 §10.1 任务 1-7（vault / Claudian / skill 集）。

## 下一步

- [ ] Phase 1 Day 1 Spike 1/2/3 执行（Plan v24 Part B）
- [ ] 写 `phase-1-day-1-spike-results.md` 记录真实运行输出
- [ ] 根据 Spike 结果决定是否进入 Phase 1 §10.1 任务 1-7（独立 plan）

---

**免责声明**：本归档仅为 Phase 1 期间的 ongoing 参考 · 不构成正式规范（formal spec 在 `openspec/specs/` 下）· 任何实施决策以 main 分支代码 + openspec spec 为准。
