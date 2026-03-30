# Deep Explore: 从 BMAD 迁移到其他工作流的真实案例与经验

> **Date**: 2026-03-25 | **Status**: RESEARCH | **Sources**: 20+ WebSearch 结果 + GitHub Issues + 社区文章
> **核心问题**: 已有大量 BMAD 生成的文档(PRD/架构/Epic/Story 452+168个文件)，如何高效利用这些资产切换到更轻量的工作流？

---

## 一、当前项目的 BMAD 资产规模

| 资产类型 | 数量 | 路径 |
|---------|------|------|
| Slash Commands | 77 个 | `.claude/commands/bmad-*.md` |
| PRD 文档 | 20+ | `docs/prd/` |
| 架构文档 | 20+ | `docs/architecture/` |
| Epic 文档 | 20+ | `docs/epics/` |
| Story 文档 | 452 | `docs/stories/` |
| BMAD 输出物 | 168 | `_bmad-output/` |
| BMAD 核心框架 | 100+ | `_bmad/` |
| CLAUDE.md + Rules | ~616 行→140 行(已精简过一次) | 多层级 |

**关键事实**：你是 solo developer，项目是 Tauri+React+Python 的学习系统，不是企业团队。

---

## 二、社区中"从 BMAD 切换出去"的真实声音

### 2.1 BMAD 已知的结构性问题（GitHub Issues）

**Issue #2003 — Structural Gaps and Contradictions of BMAD V.6 Stable**
- BMAD 有一个根本性悖论：它声称适合技术用户和非技术用户，但实际上两者都会卡住
- 技术用户无法对"不是自己写的大量 AI 代码"做决策
- 非技术用户缺乏技术技能来执行
- v6 Stable 版缺少必要的质量保障机制

**Issue #1235 — Excessive Token Usage in Workflows**
- `create-story` 工作流每步消耗 80k-100k tokens
- 工作流执行无限制的深度分析，不做 targeted reading
- BMAD agents (TEA/SM/DEV) 激活后占用 67%+ 的 context window，只留 30% 给实际工作
- TEA agent 的知识库单独就能消耗 86% context (571KB / 143K tokens)

**Issue #446 — Real Usage on Brownfield Project Feedback**
- Solo developer 在 brownfield 项目上使用 BMAD 的反馈
- Elicitation 技术很好，但框架假设产生了摩擦，需要大量手动 workaround
- 框架为团队设计的假设在 solo 场景下成为负担

**Issue #1343 — Reduce BMAD Agent Context Window Usage**
- BMAD v6 虽然用 helper pattern 优化了 70-85% token，但仍然太重

### 2.2 关于 CLAUDE.md 膨胀的共识

**Rick Hightower (Medium, 2026-03)**:
> "400 行 CLAUDE.md 每个 session 都会全量加载。Claude 在编辑 React 组件时看到你的迁移安全规则，在写数据库查询时看到 React patterns。"

**Anthropic 官方 + 社区共识**:
- 前沿模型可靠跟随约 150-200 条独立指令
- Claude Code 系统 prompt 已用掉 ~50 个 slot
- 留给你的只有 100-150 个 slot
- **超过 200 行 CLAUDE.md → Claude 不是在反抗，是被过载了**

**DEV.to 文章**:
> "I Wrote 200 Lines of Rules for Claude Code. It Ignored Them All."

---

## 三、有没有人真的同时用 BMAD + Superpowers / GSD？

### 3.1 是的，有人在做 — 但方式不是你想的那样

**unified-workflow (github.com/mattjaikaran)**:
- 一个 Claude Code skill，在 GSD 项目管理和 Superpowers 工程纪律之间路由
- GSD 负责规划和任务分解，Superpowers 负责 TDD 执行质量
- 不是"两个框架全装"，而是各取一个核心能力

**Shipyard 模式**:
- 结合 GSD 的生命周期管理和 Superpowers 的 skill 框架
- "When GSD executes, it executes with Superpowers pushing the quality floor up"

**Issue #1785 — CC Skills override bmad agent/workflow**:
- Superpowers 的 "using-superpowers" skill 会和 BMAD commands 产生混淆
- 两者的 skill 注册机制不冲突，但认知上让 Claude 困惑

### 3.2 Framework Showdown 的结论（Rick Hightower, 2026-03）

| 框架 | 定位 | 适合 | 不适合 |
|------|------|------|-------|
| **BMAD** | 企业团队模拟 | 有真实用户的大项目、需要完整 SDLC | Solo dev、小项目、brownfield 迭代 |
| **GSD** | 轻量 spec-driven | Solo dev、快速迭代、brownfield 增量 | 需要完整规划体系的大团队 |
| **Superpowers** | TDD 工程纪律 | 代码质量要求高、需要系统调试 | 纯规划阶段 |
| **OpenSpec** | Brownfield-first delta specs | 维护已有项目、增量修改 | 全新项目 |
| **SpecKit** | 门控规范流程 | 中等规模项目 | 极小或极大项目 |

**关键推荐**:
> "Solo developer 或小团队 → GSD 学习曲线最低"
> "企业团队 + 已有敏捷流程 → BMAD 最完整"
> "长期演进的混合方案：BMAD 的规划 → SpecKit 的执行 → OpenSpec 的维护"

### 3.3 ranthebuilder 的经验法则

> "对有真实用户、外部集成或安全表面的重要项目用 BMAD。对小功能用 plan mode，但你需要自己问那些难问题——因为 AI 不会主动问。"

---

## 四、如何利用已有的 BMAD 文档资产？

### 4.1 OpenSpec 的 Delta Spec 模式（最适合你的场景）

**核心概念**:
- 分离 Source of Truth (`openspec/specs/`) 和 Change Proposals (`openspec/changes/`)
- 用 ADDED/MODIFIED/REMOVED 标记追踪变更
- 不重述整个 spec，只描述"变了什么"

**对你的价值**:
- 你的 452 个 Story 和 20+ PRD 可以作为 Source of Truth 保留
- 新的开发只写 delta spec，描述相对现有功能的变更
- Token 效率最高，适合高频小范围变更

### 4.2 GSD 的 map-codebase 模式

**流程**:
1. `/gsd:map-codebase` — 启动并行 agents 分析现有代码库的 stack、架构、约定
2. `/gsd:new-project` — 自动加载代码库 patterns，只聚焦你要添加什么
3. 生成 `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`

**对你的价值**:
- 不需要从零重写需求文档
- GSD 的 map-codebase 会自动读取你现有的架构和约定
- PLAN.md 直接作为 subagent 的可执行指令

### 4.3 Superpowers 的 Plan-Execute 模式

**流程**:
1. Brainstorm → 捕获上下文
2. `/superpowers:write-plan` — 生成 plan doc
3. 手动修改 plan doc 确保细节正确
4. `/superpowers:execute-plan` — 在 subagent 中执行

**对你的价值**:
- 你可以把已有的 PRD/架构文档内容粘贴到 plan 中
- Superpowers 的 TDD 纪律可以替代你现有的 DD-07 验收规则
- 比 BMAD 轻量得多，但保留了计划-执行分离

### 4.4 avishek.net 的经验：借用而非全盘采纳

> "Rather than adopting the entire framework, I adopted five workflow patterns from GSD 2. These patterns are tool-agnostic."

**五个可借用的 pattern**:
1. Phase gates（阶段门控）
2. Complexity awareness（复杂度感知）
3. Verification（验证）
4. Persistent state（持久状态）
5. Context isolation（上下文隔离）

---

## 五、推荐迁移策略

### 5.1 不要迁移 — 做精简 + 混合

基于所有调研，最务实的方案不是"从 BMAD 迁移到 X"，而是：

**Phase 1: 精简 BMAD 到只保留有价值的部分**

| 保留 | 删除/归档 |
|------|---------|
| `bmad-bmm-code-review` | 全部 `bmad-agent-cis-*` (创新/故事/设计思维 — solo dev 不需要) |
| `bmad-bmm-dev-story` | 全部 `bmad-bmb-*` (构建 agent/module/workflow — 框架元工具) |
| `bmad-bmm-document-project` | 全部 `bmad-tea-*` (测试架构师 — 86% context 消耗) |
| `bmad-bmm-sprint-status` | 全部 `bmad-editorial-*` (编辑审查) |
| `bmad-bmm-correct-course` | `bmad-party-mode` (多角色模式) |
| `bmad-bmm-quick-dev` | 大部分 `bmad-bmm-create-*` (已经有了就不需要重新创建) |

**预计：77 个命令 → 8-12 个命令**

**Phase 2: 引入轻量补充**

| 需求 | 用什么 | 替代 BMAD 什么 |
|------|-------|--------------|
| 任务分解 + 计划执行 | GSD 的 PLAN.md 模式 | BMAD 的 Epic→Story→Sprint 全套仪式 |
| TDD + 代码质量 | Superpowers 的 TDD skill | BMAD 的 TEA agent (86% context) |
| 代码审查 | 保留 `bmad-bmm-code-review` | 不变 |
| 增量变更追踪 | OpenSpec 的 delta spec 概念 | BMAD 的完整 PRD 重写 |
| 上下文隔离 | GSD 的 fresh-context-per-plan | BMAD 的 session 混杂 |

**Phase 3: CLAUDE.md 精简到 < 100 行**

当前你的 CLAUDE.md 体系分散在 6+ 个文件中：
- `~/.claude/CLAUDE.md` (全局)
- `canvas/CLAUDE.md` (项目)
- `canvas-learning-system/CLAUDE.md` (子项目)
- `.claude/rules/*.md` (5+ 个规则文件)

建议：
- 把真正被 Claude 忽略的规则（根据实际观察）删除
- 能用 hook 强制的就不写成规则（你已经有 pretool-guard.js 等 hooks）
- 把 DD-01~DD-13 精简为 5 条最核心的
- 把长篇解释移入 `.claude/skills/`（按需加载，不膨胀 context）

### 5.2 已有文档的处理

| 文档类型 | 建议 |
|---------|------|
| **PRD 20+** | 保留为参考。新开发不需要重新走 PRD 流程，直接写 PLAN.md 引用相关 PRD 即可 |
| **架构文档 20+** | 保留为 Source of Truth。告诉 Claude "看 docs/architecture/X.md 的模式来做 Y" |
| **Epic 20+** | 归档。新工作用 GSD 的 PLAN.md 替代 Epic 体系 |
| **Story 452** | 归档。已完成的 story 只作为历史记录，不再加载到 context |
| **BMAD 输出 168** | 归档到 `_archive/bmad-output/`。测试报告和 retro 保留参考价值 |
| **BMAD 核心框架 100+** | 删除不用的模块，只保留实际使用的 commands |

### 5.3 具体步骤

```
Step 1: 审计 — 记录过去 30 天实际用过哪些 BMAD 命令（大概率 < 10 个）
Step 2: 归档 — 把不用的命令移到 _archive/bmad-commands/
Step 3: 精简 CLAUDE.md — 合并到 < 100 行，把解释性内容移到 skills
Step 4: 安装 GSD — /gsd:map-codebase 让它理解现有代码
Step 5: 安装 Superpowers — 只用 TDD skill 和 execute-plan
Step 6: 试跑 — 用新工作流做一个小 feature，对比效率
Step 7: 调整 — 根据试跑结果微调保留/删除的命令
```

---

## 六、关键结论

1. **没有人记录过完整的"BMAD → X"迁移案例**。社区中更常见的是：(a) 部分借用其他框架的 pattern，(b) 精简 BMAD 到 Quick Flow，(c) 直接不用框架只用 CLAUDE.md + plan mode。

2. **BMAD 的真正价值是它的 elicitation（引导提问）和 code review**。其他部分（multi-agent role play, 70+ commands, sprint ceremony）对 solo dev 是净负担。

3. **你的 452 个 Story 和 168 个输出物是历史资产，不是活跃工具**。它们的价值在于记录了"做过什么"和"为什么这样做"，但不应该参与日常 context。

4. **GSD + Superpowers 混合是目前社区对 solo brownfield 的最佳实践**：GSD 管理任务和上下文隔离，Superpowers 保障代码质量。

5. **OpenSpec 的 delta spec 概念值得借用但不需要全装**：对于增量修改，写"相对现有功能变了什么"比重写完整 spec 高效得多。

6. **CLAUDE.md 精简是最高 ROI 的行动**：从研究看，你当前的多层 CLAUDE.md + rules 体系很可能已经超过了 Claude 能可靠跟随的指令上限。

---

## Sources

- [Framework Showdown: Superpowers vs BMAD vs SpecKit vs GSD](https://medium.com/@richardhightower/the-great-framework-showdown-superpowers-vs-bmad-vs-speckit-vs-gsd-360983101c10)
- [BMAD Issue #2003: Structural Gaps and Contradictions](https://github.com/bmad-code-org/BMAD-METHOD/issues/2003)
- [BMAD Issue #1235: Excessive Token Usage](https://github.com/bmad-code-org/BMAD-METHOD/issues/1235)
- [BMAD Issue #446: Brownfield Feedback](https://github.com/bmad-code-org/BMAD-METHOD/issues/446)
- [BMAD Issue #1343: Reduce Context Window Usage](https://github.com/bmad-code-org/BMAD-METHOD/issues/1343)
- [BMAD Issue #1785: CC Skills Override BMAD](https://github.com/bmad-code-org/BMAD-METHOD/issues/1785)
- [Claude Code Rules: Stop Stuffing Everything into CLAUDE.md](https://medium.com/@richardhightower/claude-code-rules-stop-stuffing-everything-into-one-claude-md-0b3732bca433)
- [200 Lines of Rules — Ignored](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639)
- [Superpowers GitHub (obra)](https://github.com/obra/superpowers)
- [GSD GitHub](https://github.com/gsd-build/get-shit-done)
- [OpenSpec Brownfield](https://intent-driven.dev/blog/2026/03/10/spec-driven-development-brownfield/)
- [Evolving Workflow: Borrowing from GSD 2](https://avishek.net/2026/03/23/adopting-gsd2-patterns.html)
- [unified-workflow: GSD + Superpowers](https://github.com/mattjaikaran/unified-workflow)
- [ranthebuilder: Claude Code Best Practices Lessons](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/)
- [Spec-Driven Development Brownfield](https://intent-driven.dev/blog/2026/03/10/spec-driven-development-brownfield/)
- [BMAD Quick Flow](https://dev.to/jacktt/bmad-quick-flow-15en)
- [Anthropic Best Practices](https://code.claude.com/docs/en/best-practices)
- [BMAD v6 Token Savings](https://medium.com/@hieutrantrung.it/from-token-hell-to-90-savings-how-bmad-v6-revolutionized-ai-assisted-development-09c175013085)
- [ChatPRD for Claude Code](https://www.chatprd.ai/learn/PRD-for-Claude-Code)
- [Boris Cherny Creator Workflow](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [Brownfield Research (同项目)](research-brownfield-ai-workflow.md)
