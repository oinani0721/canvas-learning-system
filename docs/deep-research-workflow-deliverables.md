# 工作流优化交付物 — 综合 6 份报告 + 本地代码分析

> **日期**: 2026-03-29 | **Session**: S35 Deep Research
> **数据源**: Gemini Code mode (500文件) + Gemini Web mode (34 sources) + 4份已有报告 + 本地 Grep/Read 分析
> **核心发现**: 返工率高的 3 个机械性根因 + Graphiti 噪音的 2 个配置性根因

---

## 交付物 A: ⭐ 日常工作流序列

```
SESSION 开始:
  ┌─ /daily-start (新建)
  │  → 搜索 Graphiti 最近决策 + 读取 known-gotchas.md + CURRENT_TASK.md
  │  → 输出: 今日上下文摘要
  └─

新功能开发:
  ┌─ /plan-feature <描述>
  │  → Phase 1: 需求澄清 + Graphiti 搜索 + Context7 查文档
  │  → Phase 2: 方案设计 + known-gotchas 注入 + architecture.md 对照
  │  → Phase 3: 用户确认 → 计划文件
  │
  ├─ /tech-audit <技术> (可选, 引入新技术时)
  │  → Context7 查能力 → 用户确认启用哪些 → Graphiti 记录
  │
  ├─ /tdd-cycle <任务> (>30min 任务)
  │  → RED: 子 Agent 写失败测试 (注入 known-gotchas)
  │  → GREEN: 子 Agent 最小实现
  │  → REFACTOR: 清理
  │  → hooks 自动守护 DD-03
  │
  │  或: 直接编码 (<30min 小修复, hooks 自动守护)
  │
  ├─ /code-review [files]
  │  → 独立 Agent 对抗性审查 → 修复问题
  │
  └─ commit → lefthook auto-push

Bug 修复:
  /parallel-fix → 分类 → 5 专家 Agent 并行修复

质量检查 (每周/sprint 结束):
  /coverage-check all → 死代码 + 利用率审计

SESSION 结束:
  ┌─ /session-close (新建)
  │  → 更新 CURRENT_TASK.md
  │  → 记录本 session 决策到 Graphiti
  │  → 输出: 下 session 接手摘要
  └─
```

---

## 交付物 B: 命令处置表

### 工作流命令 (9个)

| 命令 | 处置 | 理由 |
|------|------|------|
| /plan-feature | **MODIFY** | 补充 known-gotchas.md 读取 (当前缺失) |
| /code-review | **KEEP** | 设计良好,独立 Agent + Graphiti 记录 |
| /tdd-cycle | **MODIFY** | 补充 known-gotchas.md 注入到子 Agent prompt |
| /tech-audit | **KEEP** | Context7 能力审计,独特价值 |
| /coverage-check | **KEEP** | 已读取 gotchas + architecture |
| /parallel-fix | **KEEP** | 5-agent 并行,设计精良 |
| /error-revisit | **KEEP** | 教育产品功能 |
| /summary-review | **KEEP** | 教育产品功能 |
| /variation-practice | **KEEP** | 教育产品功能 |

### 新建命令 (2个)

| 命令 | 功能 |
|------|------|
| **/daily-start** | Session 开始: Graphiti 上下文 + gotchas + 当前任务 |
| **/session-close** | Session 结束: 决策记录 + 上下文转储 + 任务状态更新 |

### 教育命令 (13个) — 全部 KEEP (产品功能)

/basic-decompose, /deep-decompose, /deep-explain, /example-teach, /four-level, /memory-anchor, /oral-explain, /question-decompose, /compare, /relation-probe, /score, /study-plan, /verify-question

---

## 交付物 C: Agent 处置表

### ARCHIVE (6个, 共 ~5300+ 行, 0 个 command 引用)

| Agent | 行数 | 归档理由 |
|-------|------|---------|
| canvas-orchestrator.md | 3232 | 无 command 引用; 3232 行超 LLM 注意力窗口 ("lost in middle") |
| planning-orchestrator.md | 614 | BMAD Phase 2 专用,无外部调用 |
| parallel-dev-orchestrator.md | 522 | BMAD Phase 4 专用,无外部调用 |
| iteration-validator.md | 436 | 仅被 planning-orchestrator 引用 |
| review-board-agent-selector.md | ~100 | 无调用方 |
| graphiti-memory-agent.md | ~200 | 0 个 command 引用 |

### KEEP (16个)

| 类别 | Agent | 引用方 |
|------|-------|--------|
| QA修复 | integrity-auditor.md | /parallel-fix |
| QA修复 | logic-bug-fixer.md | /parallel-fix |
| QA修复 | type-async-fixer.md | /parallel-fix |
| QA修复 | security-api-reviewer.md | /parallel-fix |
| QA修复 | performance-reviewer.md | /parallel-fix |
| 教育 | basic-decomposition.md | /basic-decompose |
| 教育 | deep-decomposition.md | /deep-decompose |
| 教育 | clarification-path.md | /deep-explain |
| 教育 | example-teaching.md | /example-teach |
| 教育 | four-level-explanation.md | /four-level |
| 教育 | memory-anchor.md | /memory-anchor |
| 教育 | oral-explanation.md | /oral-explain |
| 教育 | question-decomposition.md | /question-decompose |
| 教育 | comparison-table.md | /compare |
| 教育 | scoring-agent.md | /score |
| 教育 | verification-question-agent.md | /verify-question |

---

## 交付物 D: Hook 防护网规划

### 当前 (2 hooks, 仅 DD-03)

| Hook | 类型 | 执行 | 延迟 |
|------|------|------|------|
| pretool-guard.js | PreToolUse(Edit\|Write) | DD-03 stub 检测 | <100ms |
| mock-import-guard.js | PreToolUse(Edit\|Write) | DD-03 mock import 守卫 | <100ms |

### 建议新增 (3 hooks)

| Hook | 类型 | 执行什么 | DD 规则 | 预估延迟 | 社区验证 |
|------|------|---------|---------|---------|---------|
| **context-inject.js** | SessionStart | 注入 known-gotchas + 当前任务上下文到 stdout | DD-08 | <200ms | Web报告: SessionStart 注入是社区共识 |
| **architecture-guard.js** | PreToolUse(Edit\|Write) on backend/app/\|frontend/src/ | 检查 tool_input 是否涉及核心模块,若是则要求 architecture.md 已被读取 | DD-02 | <150ms | Web报告: architecture obedience hybrid enforcement |
| **stop-test-runner.js** | Stop | Claude 完成整轮回复后运行 pytest + tsc --noEmit | DD-07 | 5-15s (不阻塞交互) | Web报告: Stop hook > PostToolUse,避免 token 膨胀 |

### 不需要 Hook 的 DD 规则 (保持 CLAUDE.md 文字)

| DD 规则 | 理由 |
|---------|------|
| DD-01 学术实证 | 需要 Context7/WebSearch,hook 无法判断 |
| DD-04 参考案例 | 同上 |
| DD-05 先 Pencil | UI 设计决策,非代码检查 |
| DD-06 前端规范 | .claude/rules/ 路径规则已覆盖 |
| DD-09 增量提问 | 对话行为,非工具操作 |
| DD-10 防蔓延 | 需要理解 MVP 清单,hook 无法判断 |
| DD-11 管道打通 | /code-review + /parallel-fix 覆盖 |
| DD-12 范围约束 | S32 已移除(regex 太脆弱),改用 .claude/rules/ 路径规则 |
| DD-13 名实一致 | S32 已移除(regex 太脆弱),改用 /code-review |

---

## 交付物 E: Graphiti 改造方案

### 问题 1: group_id 理解纠正 (⚠️ Gemini 报告有误)

```
实际状况 (非 Gemini 报告所述的 "分裂"):
  - "canvas-dev" = 开发工作流数据 (Claude Code /commands → 直连 Graphiti MCP)
  - "cs188" = 学习产品数据 (后端 sidecar → memory_tools.py)
  → 这是两个不同的数据域, 应该分开! 不是 bug!

真正的问题:
  - "cs188" 是硬编码的默认科目名 (UC Berkeley CS 188)
  - S27-GDA-3 决策要求 group_id 按白板名动态配置
  - 当前所有白板/科目的学习数据都写到 "cs188" 同一空间
  → 不同科目的学习记忆互相污染

修复方案:
  - 保持开发工作流用 "canvas-dev" (已正确)
  - DEFAULT_GROUP_ID 改为由前端传入的白板名 (S27-GDA-3 落地)
  - 后端 memory_tools.py 的 group_id 参数必须由调用方显式传入
```

### 问题 2: group_id 重组 (中期)

```
当前: 单一 "canvas-dev" 装所有内容

目标 (GuardKit 模式, Web 报告推荐):
  "canvas-dev-decisions"    — 架构决策, 技术选型
  "canvas-dev-gotchas"      — Bug 模式, 失败教训
  "canvas-dev-reviews"      — 代码审查记录
  "canvas-dev-capabilities" — 技术能力审计结果

学习数据 (S27-GDA-3 决策):
  "{canvas-name}"           — 每个白板的学习数据独立命名空间
```

### 问题 3: 检索质量 (中期)

```
措施 1: ContextBudget 模式 (Web 报告 GuardKit 推荐)
  总 token 预算: 4000
  - architecture_context: 20% (800 tokens)
  - warnings/gotchas: 30% (1200 tokens)
  - feature_context: 30% (1200 tokens)
  - domain_knowledge: 20% (800 tokens)

措施 2: 检索时 exclude_invalidated: true (已在 commands 中使用)

措施 3: PENDING 决策清理
  - 13 条 "Review PENDING" 决策 (2026-03-16~24) 需要批量审查
  - 过期的标记 invalidated, 仍有效的标记 ACCEPTED
```

### Graphiti vs Agentic RAG 决策

```
Web 报告结论: 保留 Graphiti + 添加 CRAG 评估层

理由:
  1. Graphiti 的三层搜索 (语义+BM25+BFS) 已在后端实现且稳定
  2. CRAG 可作为 /plan-feature 和 /tdd-cycle 的前置过滤器
     — 检索后评估相关性 (Correct/Incorrect/Ambiguous)
     — 过滤 Incorrect 节点后再注入 Agent 上下文
  3. 不建议替换为 mcp-neuralmemory (迁移成本高, 收益不明确)

实施路径: 先修复 group_id 分裂 → 再重组 group_id → 最后添加 CRAG 层
```

---

## 交付物 F: BMAD + SuperPower 处置

### BMAD

```
处置: ARCHIVE (不删除, 保留历史参考)

_bmad/ (605 文件, 5.3MB) → git mv _bmad/ _archive/bmad-frozen/
_bmad-output/ (3.4MB) → 保留 planning-artifacts/, 其余归档
docs/stories/ (454 文件) → git mv docs/stories/ _archive/bmad-stories/
docs/epics/ (24 文件) → KEEP (架构参考价值)

理由:
  - Code mode 报告: "BMAD is fundamentally an LLM scaffolding overlay, not a runtime dependency"
  - Report 3: "544 个冻结文件是死重"
  - 归档不影响运行时, 但释放 git 搜索噪音

需迁移的 BMAD 工作流:
  - 代码审查 → 已有 /code-review (替代完成)
  - Sprint 规划 → Claude Code Plan Mode (原生替代)
  - Quick Flow → /plan-feature + 直接编码 (替代完成)
```

### SuperPower

```
处置: ARCHIVE

docs/superpowers/ (5 文件) → git mv docs/superpowers/ _archive/superpowers/

理由:
  - Report 3: "78 session 0 次激活"
  - Web 报告: "1% 规则需要正确的插件安装、同步 Hook、足够的提示预算——仍是概率性的"
  - 已有 /plan-feature 替代 brainstorming 技能
  - 已有 /code-review 替代 requesting-code-review 技能
  - 确定性执行由 hooks 提供, 不需要 HARD-GATE
```

### 清理 Graphiti MCP 冗余

```
处置: 统一为 graphiti-canvas, 移除 graphiti (legacy)

settings.local.json:
  - 移除所有 mcp__graphiti__* 权限条目
  - 保留所有 mcp__graphiti-canvas__* 权限条目

理由:
  - Code mode 报告: "Legacy server allows agents to accidentally route queries to deprecated endpoints"
  - commands 全部引用 graphiti-canvas, 不引用 graphiti
```

---

## 实施优先级

| 批次 | 改动 | 预计时间 | 影响 |
|------|------|---------|------|
| **P0** | ~~修复 DEFAULT_GROUP_ID 分裂~~ → **纠正**: cs188 是产品数据域,canvas-dev 是开发数据域,两者分开是正确的。真正的 P0 是 P1。 | 0 分钟 | Gemini 误判,无需改动 |
| **P1** | 修改 /plan-feature 和 /tdd-cycle 注入 known-gotchas | 30 分钟 | 阻止已知 Bug 重复 |
| **P2** | 创建 /daily-start 和 /session-close | 45 分钟 | Session 生命周期管理 |
| **P3** | 新增 3 个 hooks (context-inject, architecture-guard, stop-test-runner) | 1-2 小时 | 确定性执行 DD 规则 |
| **P4** | 归档 6 个死 Agent | 15 分钟 | 减少混淆 |
| **P5** | 归档 BMAD + SuperPower | 15 分钟 | 减少噪音 |
| **P6** | Graphiti group_id 重组 | 1-2 小时 | 检索质量提升 |
| **P7** | 清理 13 条 PENDING 决策 | 1 小时 | 消除矛盾记忆 |
| **P8** | 移除 legacy graphiti MCP | 10 分钟 | 统一检索路径 |

---

## Gemini 报告纠正

⚠️ **Gemini Code mode 错误**: 报告声称 `.claude/commands/plan-feature.md` 是 `// placeholder`。
**实际**: 该文件是完善的 76 行命令（Phase 1 需求澄清 + Phase 2 方案设计 + Phase 3 计划文件 + Phase 4 记录），包含 Graphiti + Context7 + Sequential Thinking 集成。Gemini 的 File Search Store 混淆了文件。
