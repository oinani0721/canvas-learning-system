# BMad 4.0 开发工作流指南

Canvas Learning System 使用 **BMad 4.0 方法论** 进行开发管理，并添加了 **Canvas 自定义扩展** 以增强迭代管理和并行开发能力。

---

## 目录

1. [工作流概述](#工作流概述)
2. [Phase 1: Analysis (分析)](#phase-1-analysis-分析)
3. [Phase 2: Planning (规划)](#phase-2-planning-规划)
4. [Phase 3: Solutioning (架构)](#phase-3-solutioning-架构)
5. [Phase 4: Implementation (实现)](#phase-4-implementation-实现)
6. [完整工作流示例](#完整工作流示例)
7. [快速参考表](#快速参考表)
8. [常见场景指南](#常见场景指南)

---

## 工作流概述

### BMad 4阶段流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Phase 1         │     │ Phase 2         │     │ Phase 3         │     │ Phase 4         │
│ ANALYSIS        │ ──► │ PLANNING        │ ──► │ SOLUTIONING     │ ──► │ IMPLEMENTATION  │
│ (可选)          │     │ (必需)          │     │ (架构)          │     │ (开发)          │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ /analyst        │     │ /pm             │     │ /architect      │     │ /sm             │
│                 │     │ /planning ⚡     │     │ /po             │     │ /dev            │
│                 │     │                 │     │                 │     │ /qa             │
│                 │     │                 │     │                 │     │ /parallel ⚡     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**⚡ = Canvas 自定义扩展**

### 核心原则

- **对话驱动**: 使用自然语言 + `/命令` + `*命令`
- **Agent协作**: 每个Agent有特定职责和命令集
- **迭代管理**: Phase 2使用Planning Orchestrator跟踪变更
- **质量门禁**: QA Agent在Phase 4把关质量

---

## Phase 1: Analysis (分析)

**目的**: 探索想法、市场调研、创建项目简报

**何时使用**: 新项目启动时（可选，已有明确需求可跳过）

### Agent: Business Analyst (Mary 📊)

**激活**: `/analyst`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*create-project-brief` | 创建项目简报 | `*create-project-brief` |
| `*perform-market-research` | 市场调研报告 | `*perform-market-research` |
| `*brainstorm {topic}` | 头脑风暴 | `*brainstorm "学习系统功能"` |
| `*elicit` | 需求获取 | `*elicit` |
| `*exit` | 退出Agent | `*exit` |

### 示例流程

```bash
# 激活Business Analyst
/analyst

Mary (Business Analyst):
📊 你好！我是Mary，你的业务分析师。
可用命令: *create-project-brief, *perform-market-research, *brainstorm...

# 创建项目简报
*create-project-brief

Mary:
📋 请回答以下问题来创建项目简报:
1. 项目目标是什么？
2. 目标用户是谁？
...

# 完成后输出
*doc-out

Mary:
✅ 已保存: docs/project-brief.md
```

### 阶段产出

- `docs/project-brief.md` - 项目简报

### 进入下一阶段信号

- 项目简报完成
- 需求基本明确

---

## Phase 2: Planning (规划)

**目的**: 创建PRD、定义Epic和Story、管理规划迭代

**何时使用**: 必需阶段，所有项目都要经过

### Agent 1: PM Agent (John 📋)

**激活**: `/pm`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*create-prd` | 从项目简报生成PRD | `*create-prd` |
| `*create-epic` | 创建新Epic | `*create-epic` |
| `*create-story` | 创建用户故事 | `*create-story` |
| `*correct-course` | 变更分析 | `*correct-course "添加新功能"` |
| `*shard-prd` | 拆分大型PRD | `*shard-prd` |
| `*doc-out` | 输出文档 | `*doc-out` |
| `*exit` | 退出Agent | `*exit` |

### Agent 2: Planning Orchestrator (Marcus 🎯) ⚡ Canvas扩展

**激活**: `/planning`

**目的**: 管理Phase 2迭代，跟踪PRD/Architecture变更，检测Breaking Changes

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*init` | 初始化新迭代 | `*init "Epic 13 - Ebbinghaus"` |
| `*validate` | 验证变更（含SDD检查） | `*validate` |
| `*finalize` | 完成迭代，创建Git tag | `*finalize` |
| `*status` | 显示当前迭代状态 | `*status` |
| `*rollback` | 回滚到之前迭代 | `*rollback 3` |
| `*compare` | 对比迭代差异 | `*compare 3 4` |
| `*exit` | 退出Agent | `*exit` |

### 标准PRD创建流程

```bash
# Step 1: 激活PM
/pm

John (PM):
📋 你好！我是John，你的产品经理。

# Step 2: 创建PRD
*create-prd

John:
📝 正在分析项目简报...
✅ PRD草稿已生成

# 回答PM的澄清问题...

# Step 3: 输出PRD
*doc-out

John:
✅ 已保存: docs/prd.md
```

### 迭代管理流程 (修改已有PRD)

```bash
# Step 1: 激活Planning Orchestrator
/planning

Marcus (Planning Orchestrator):
🎯 你好！我是Marcus，你的规划协调员。

# Step 2: 初始化迭代
*init "添加Epic 13 - Ebbinghaus复习系统"

Marcus:
✅ Pre-flight checks passed
⏳ Initializing Iteration 4...
   └─ Snapshot: iterations/iteration-004.json
   └─ Branch: planning-iteration-4

# Step 3: 使用PM进行变更
/pm
*correct-course "添加Epic 13 - Ebbinghaus Review"

PM:
✅ Generated: sprint-change-proposal-20251120.md

# Step 4: 验证变更
/planning
*validate

Marcus:
⏳ Running validation...
   └─ PRD: Validated
   └─ OpenAPI: No breaking changes
   └─ Schemas: Compatible
✅ Validation Passed!

# Step 5: 完成迭代
*finalize

Marcus:
✅ Git tag: planning-v4
🎉 Iteration 4 Complete!
```

### 阶段产出

- `docs/prd.md` 或 `docs/prd/*.md` (分片PRD)
- `iterations/iteration-{N}.json` (迭代快照)

### 进入下一阶段信号

- PRD经PO验证
- 所有Epic和Story定义完成

---

## Phase 3: Solutioning (架构)

**目的**: 创建技术架构、记录架构决策

**何时使用**: PRD完成后

### Agent 1: Architect Agent (Winston 🏗️)

**激活**: `/architect`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*create-adr {title}` | 创建架构决策记录(ADR) | `*create-adr "Vector Database Selection"` |
| `*create-backend-architecture` | 后端架构设计 | `*create-backend-architecture` |
| `*create-front-end-architecture` | 前端架构 | `*create-front-end-architecture` |
| `*create-full-stack-architecture` | 全栈架构 | `*create-full-stack-architecture` |
| `*research {topic}` | 深度研究 | `*research "LangGraph vs LangChain"` |
| `*doc-out` | 输出文档 | `*doc-out` |
| `*exit` | 退出Agent | `*exit` |

### Agent 2: Product Owner Agent (Sarah 📝)

**激活**: `/po`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*execute-checklist-po` | 运行PO检查清单 | `*execute-checklist-po` |
| `*validate-story-draft {story}` | 验证Story | `*validate-story-draft story-13.1` |
| `*correct-course` | 需求变更处理 | `*correct-course` |
| `*exit` | 退出Agent | `*exit` |

### ADR创建时机与工作流 ⭐ 行动指南

**ADR (Architecture Decision Record)** 用于记录重要的技术选型决策，遵循Michael Nygard格式。

#### 何时创建ADR？

| 触发条件 | 示例 | 优先级 |
|----------|------|--------|
| **技术选型决策** | 选择LanceDB而非Chroma | P0 必需 |
| **架构模式选择** | 选择微服务而非单体 | P0 必需 |
| **框架/库选择** | 选择LangGraph而非LangChain | P0 必需 |
| **数据存储决策** | 选择Neo4j存储知识图谱 | P0 必需 |
| **重大技术转向** | 从REST改为GraphQL | P0 必需 |
| **团队问"为什么选A不选B?"** | 任何需要解释的技术选择 | P1 推荐 |

#### ADR在Phase 3的位置

```
Phase 3 工作流
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. /planning ⚡ (初始化迭代)                            │
│     └─ *init "Architecture Design"                      │
│     └─ 创建快照，跟踪Specs/ADR变更                       │
│                                                         │
│  2. /architect                                          │
│     └─ *create-backend-architecture (或其他架构命令)     │
│     └─ 创建OpenAPI specs和JSON Schemas                  │
│                                                         │
│  3. 创建ADR (针对每个重要技术决策)  ⭐ 关键步骤          │
│     └─ *create-adr "技术选型标题"                       │
│     └─ 重复直到所有决策都已记录                         │
│                                                         │
│  4. *doc-out (输出架构文档)                              │
│                                                         │
│  5. /planning ⚡ (验证并完成迭代)                        │
│     └─ *validate (检测Breaking Changes)                 │
│     └─ *finalize (Git tag: arch-v1)                     │
│                                                         │
│  6. /po                                                 │
│     └─ *execute-checklist-po (验证架构和ADR)            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**⚠️ 重要**: Phase 3也需要使用Planning Iteration Management (`/planning`)来跟踪OpenAPI specs和JSON Schemas的变更。这确保：
- Specs版本被记录
- Breaking Changes被检测
- 可以回滚到之前的架构版本

#### 工作流要点

1. **先架构，后ADR**: 在`*create-backend-architecture`过程中识别需要ADR的决策点
2. **每个决策一个ADR**: 不要合并多个决策到一个ADR
3. **ADR编号自动递增**: 系统自动检测最高编号并递增
4. **引用PRD/Epic**: 在ADR的References中关联对应的PRD章节和Epic

### 示例流程 (含ADR)

```bash
# Step 0: 初始化迭代 ⚡ 新增步骤
/planning

Marcus (Planning Orchestrator):
🎯 你好！我是Marcus，你的规划协调员。

*init "Phase 3 - Architecture Design"

Marcus:
✅ Initializing Iteration...
   └─ Snapshot: iterations/iteration-arch-001.json
📋 Ready for Architecture changes

# Step 1: 创建架构
/architect

Winston (Architect):
🏗️ 你好！我是Winston，你的架构师。

*create-backend-architecture

Winston:
🔍 分析PRD需求...
📐 设计系统架构...
⚠️ 检测到3个需要ADR的决策点:
   1. Vector Database选型
   2. Agent框架选型
   3. 知识图谱存储方案
✅ 架构文档已生成

# Step 2: 为每个决策创建ADR ⭐ 关键步骤
*create-adr "Vector Database Selection"

Winston:
📝 创建ADR-0006...
[交互式收集决策信息]
✅ 已保存: docs/architecture/decisions/0006-vector-database-selection.md

*create-adr "Agent Framework Selection"

Winston:
📝 创建ADR-0007...
✅ 已保存: docs/architecture/decisions/0007-agent-framework-selection.md

# Step 3: 输出架构文档
*doc-out

Winston:
✅ 已保存: docs/architecture.md

# Step 4: 验证并完成迭代 ⚡ 新增步骤
/planning

Marcus:
🎯 规划协调员已激活

*validate

Marcus:
⏳ Running validation...
   └─ OpenAPI: No breaking changes ✅
   └─ Schemas: Compatible ✅
   └─ ADRs: 3 new ADRs detected ✅
✅ Validation Passed!

*finalize

Marcus:
✅ Git tag: arch-v1
🎉 Architecture Iteration Complete!

# Step 5: PO验证 (含ADR检查)
/po

Sarah (Product Owner):
📝 你好！我是Sarah，你的产品负责人。

*execute-checklist-po

Sarah:
✅ PRD完整性: Pass
✅ Story验收标准: Pass
✅ 架构对齐: Pass
✅ ADR完整性: 检测到3个ADR，覆盖所有主要决策
🎉 Ready for Implementation!
```

### 阶段产出

- `docs/architecture.md` 或 `docs/architecture/*.md`
- `docs/architecture/decisions/*.md` (ADRs) ⭐ **每个技术决策对应一个ADR**
- `specs/api/*.yml` (OpenAPI规范)
- `specs/data/*.json` (JSON Schema)

### 进入下一阶段信号

- 架构文档完成
- PO检查清单通过

---

## Phase 4: Implementation (实现)

**目的**: 开发Story、代码审查、质量测试

**何时使用**: 架构完成后

### Agent 1: Scrum Master Agent (Bob 🏃)

**激活**: `/sm`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*draft` | 从Epic创建下一个Story | `*draft` |
| `*story-checklist` | 验证Story草稿 | `*story-checklist` |
| `*correct-course` | 范围变更处理 | `*correct-course "技术转向"` |
| `*exit` | 退出Agent | `*exit` |

### Agent 2: Developer Agent (James 💻)

**激活**: `/dev`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*develop-story` | 实现Story含测试 | `*develop-story story-13.1` |
| `*run-tests` | 运行测试 | `*run-tests` |
| `*review-qa` | 应用QA修复 | `*review-qa` |
| `*exit` | 退出Agent | `*exit` |

### Agent 3: QA Agent (Quinn 🧪)

**激活**: `/qa`

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*risk-profile {story}` | 评估风险 | `*risk-profile story-13.1` |
| `*test-design {story}` | 设计测试场景 | `*test-design story-13.1` |
| `*review {story}` | 综合QA审查 | `*review story-13.1` |
| `*gate {story}` | 质量门禁决策 | `*gate story-13.1` |
| `*exit` | 退出Agent | `*exit` |

### Agent 4: Parallel Dev Coordinator (Alex ⚡) ⚡ Canvas扩展

**激活**: `/parallel`

**目的**: 协调多Story并行开发，管理Git worktree

| 命令 | 描述 | 示例 |
|------|------|------|
| `*help` | 显示所有命令 | `*help` |
| `*analyze` | 分析Story依赖和冲突 | `*analyze "13.1, 13.2, 13.3"` |
| `*init` | 创建并行worktree | `*init "13.1, 13.2"` |
| `*status` | 显示所有worktree进度 | `*status` |
| `*merge` | 合并完成的worktree | `*merge 13.1` 或 `*merge --all` |
| `*cleanup` | 清理已合并worktree | `*cleanup` |
| `*exit` | 退出Agent | `*exit` |

### 标准Story开发流程

```bash
# Step 1: SM创建Story
/sm

Bob (Scrum Master):
🏃 你好！我是Bob，你的Scrum Master。

*draft

Bob:
📝 从Epic 13创建Story...
✅ Story草稿: story-13.1.md
   包含完整Dev Notes和验收标准

# Step 2: Dev实现Story
/dev

James (Developer):
💻 你好！我是James，你的开发者。

*develop-story story-13.1

James:
⏳ 读取Story需求...
⏳ 实现功能...
⏳ 编写测试...
✅ 实现完成

*run-tests

James:
⏳ Running pytest...
✅ 12/12 tests passed

# Step 3: QA审查
/qa

Quinn (QA):
🧪 你好！我是Quinn，你的QA工程师。

*review story-13.1

Quinn:
🔍 代码审查...
🔍 测试覆盖...
🔍 安全检查...
✅ Review完成

*gate story-13.1

Quinn:
✅ PASS - Story 13.1通过质量门禁
   - 测试: 12/12
   - 覆盖率: 95%
   - 安全: No issues
```

### 并行开发流程

```bash
# Step 1: 分析依赖
/parallel

Alex (Parallel Dev Coordinator):
⚡ 你好！我是Alex，你的并行开发协调员。

*analyze "13.1, 13.2, 13.3, 13.4"

Alex:
✅ Safe to parallelize: 13.1, 13.2, 13.4
⚠️ Conflict: 13.1 ↔ 13.3 on src/review_engine.py

Recommended:
- Group 1: 13.1, 13.2, 13.4 (parallel)
- Group 2: 13.3 (after 13.1)

# Step 2: 创建worktree
*init "13.1, 13.2, 13.4"

Alex:
✅ Created 3 worktrees:
   └─ Canvas-develop-13.1
   └─ Canvas-develop-13.2
   └─ Canvas-develop-13.4

## Launch Parallel Sessions

### Option 1: Full Automation (推荐)
.\scripts\parallel-develop-auto.ps1 -Stories 13.1,13.2,13.4

### Option 2: Manual Interactive
# ...手动打开终端...

# Step 3: 在各worktree中开发 (Dev + QA)
# Window 1: cd Canvas-develop-13.1 && claude
# Window 2: cd Canvas-develop-13.2 && claude
# Window 3: cd Canvas-develop-13.4 && claude

# 每个窗口中执行完整的Dev+QA流程:
# Phase 1: Development
/dev
*develop-story story-13.X
*run-tests

# Phase 2: Quality Review
/qa
*review story-13.X
*gate story-13.X

# Step 4: 监控进度 (回到main repo)
*status

Alex:
| Worktree | Story | Status | Tests | QA Gate | Ready |
|----------|-------|--------|-------|---------|-------|
| Canvas-develop-13.1 | 13.1 | ✅ ready-to-merge | Passed | PASS | ✅ |
| Canvas-develop-13.2 | 13.2 | 🔄 dev-complete | Passed | - | ❌ |
| Canvas-develop-13.4 | 13.4 | 🔄 qa-reviewing | Passed | CONCERNS | ❌ |

Ready to merge: 1/3

# Step 5: 合并完成的工作 (只合并QA Gate=PASS)
*merge --all

Alex:
✅ Merged: 13.1 (QA Gate = PASS)
🔄 Skipped: 13.2 (needs QA review)
⚠️ Skipped: 13.4 (QA Gate = CONCERNS)

# Step 6: 清理
*cleanup
```

### 阶段产出

- `docs/stories/story-{epic}.{story}.md`
- `src/**/*.py` (实现代码)
- `src/tests/**/*.py` (测试代码)

---

## 完整工作流示例

### 新项目从零开始

```bash
# ═══════════════════════════════════════════════════════════
# Phase 1: Analysis
# ═══════════════════════════════════════════════════════════
/analyst
*create-project-brief
# 回答问题...
*doc-out
*exit

# ═══════════════════════════════════════════════════════════
# Phase 2: Planning
# ═══════════════════════════════════════════════════════════
# 初始化迭代
/planning
*init "Initial PRD - v1.0"

# 创建PRD
/pm
*create-prd
*doc-out

# 验证并完成迭代
/planning
*validate
*finalize

# ═══════════════════════════════════════════════════════════
# Phase 3: Solutioning
# ═══════════════════════════════════════════════════════════
/architect
*create-backend-architecture

# ⭐ 为每个重要技术决策创建ADR
*create-adr "Vector Database Selection"
*create-adr "Agent Framework Selection"

*doc-out
*exit

/po
*execute-checklist-po
*exit

# ═══════════════════════════════════════════════════════════
# Phase 4: Implementation
# ═══════════════════════════════════════════════════════════
# 循环: SM → Dev → QA
/sm
*draft

/dev
*develop-story story-1.1
*run-tests

/qa
*review story-1.1
*gate story-1.1

# 重复直到所有Story完成...
```

---

## 快速参考表

### 所有Agent命令一览

| Phase | Agent | 激活命令 | 核心命令 |
|-------|-------|----------|----------|
| 1 | Business Analyst | `/analyst` | `*create-project-brief`, `*brainstorm` |
| 2 | PM | `/pm` | `*create-prd`, `*create-epic`, `*correct-course` |
| 2 | Planning Orchestrator ⚡ | `/planning` | `*init`, `*validate`, `*finalize` |
| 3 | Architect | `/architect` | `*create-adr`, `*create-backend-architecture`, `*research` |
| 3 | Product Owner | `/po` | `*execute-checklist-po`, `*validate-story-draft` |
| 4 | Scrum Master | `/sm` | `*draft`, `*story-checklist`, `*correct-course` |
| 4 | Developer | `/dev` | `*develop-story`, `*run-tests` |
| 4 | QA | `/qa` | `*review`, `*gate`, `*risk-profile` |
| 4 | Parallel Coordinator ⚡ | `/parallel` | `*analyze`, `*init`, `*merge` |

### 阶段转换信号

| 转换 | 触发条件 | 命令 |
|------|----------|------|
| Start → Phase 1 | 新项目需要探索 | `/analyst` |
| Phase 1 → 2 | 项目简报完成 | `/pm` → `*create-prd` |
| Phase 2 → 3 | PRD验证通过 | `/architect` |
| Phase 3 → 4 | 架构完成 | `/sm` → `*draft` |
| Phase 4 迭代 | Story开发循环 | `/dev` → `/qa` → `/sm` |
| Phase 4 并行 | 多Story就绪 | `/parallel` → `*analyze` |
| Phase 4 → 2 | 重大需求变更 | `/planning` → `*init` |

### ADR创建时机快速参考 ⭐

| 阶段 | 何时创建ADR | 命令 |
|------|-------------|------|
| **Phase 3** (主要阶段) | 技术选型、框架选择、架构模式、数据存储决策 | `/architect` → `*create-adr "标题"` |
| **Phase 4** (补充) | 开发中重大技术转向、发现更好方案需要替换 | `/architect` → `*create-adr "标题"` |
| **Phase 2** (罕见) | 需求约束导致的技术预选 | `/architect` → `*create-adr "标题"` |

**ADR验证**: 在`/planning` → `*validate`时自动检查ADR完整性

---

## 常见场景指南

### 场景1: PRD需要修改

```bash
/planning
*init "PRD v2.0 - 添加新功能"

/pm
*correct-course "添加Epic 13"

/planning
*validate
*finalize
```

### 场景2: Sprint中技术转向

```bash
# Step 1: 分析变更影响
/sm
*correct-course "发现需要OAuth而非JWT"
# 生成变更提案，评估影响

# Step 2: 如果是重大技术决策变更，创建ADR ⭐
/architect
*create-adr "Authentication Method Change - OAuth vs JWT"
# 记录为什么需要从JWT改为OAuth

*exit
```

**⚠️ 注意**: Phase 4中的技术转向如果影响架构决策，也应该创建ADR来记录原因和影响。

### 场景3: 高风险Story开发

```bash
# 开发前评估风险
/qa
*risk-profile story-13.1
*test-design story-13.1

# 开发
/dev
*develop-story story-13.1

# 严格审查
/qa
*review story-13.1
*gate story-13.1
```

### 场景4: Breaking Changes处理

```bash
/planning
*validate

Marcus:
❌ Breaking Changes Detected!
   - DELETE /api/cache/{id} removed
   - Required field added

# 选项:
# A. 修复后重新验证
# B. 接受breaking changes
*finalize --accept-breaking
```

### 场景5: 创建架构决策记录(ADR)

```bash
# 当需要记录重要技术选型决策时
/architect

Winston (Architect):
🏗️ 你好！我是Winston，你的架构师。

*create-adr "Vector Database Selection"

Winston:
📝 开始创建ADR-0006...

Step 1: 已检测到现有最高编号为0005
Step 2: 请提供问题背景...
Step 3: 请列出候选方案（LanceDB, Chroma, Pinecone）...
Step 4: 选择最终方案...
Step 5: 描述决策影响...
Step 6: 添加引用...
Step 7: ✅ 已保存: docs/architecture/decisions/0006-vector-database-selection.md

# 验证ADR（可选）
python scripts/validate-adr.py
```

---

## 附录: Canvas自定义扩展说明

### Planning Orchestrator (Marcus 🎯)

**为什么需要**: BMad官方没有Phase 2迭代跟踪，多次PRD编辑会覆盖历史。

**功能**:
- 创建迭代快照
- 检测Breaking Changes (OpenAPI, JSON Schema)
- Git tag版本管理
- 迭代对比和回滚

### Parallel Dev Coordinator (Alex ⚡)

**为什么需要**: 提高开发效率，支持多Story并行开发。

**功能**:
- 分析Story文件依赖
- 检测潜在冲突
- 管理Git worktree
- 监控并行进度（含QA Gate状态）
- 协调合并（只合并QA Gate=PASS）

**关键设计**: 每个worktree必须完成完整的Dev+QA流程才能合并

**状态流转**: `initialized → in-progress → dev-complete → qa-reviewing → ready-to-merge`

**全自动化模式**: 使用`parallel-develop-auto.ps1`脚本，通过Claude Code的`-p`非交互模式自动执行完整Dev+QA流程：
```powershell
.\scripts\parallel-develop-auto.ps1 -Stories 13.1,13.2,13.4
```

每个会话使用:
- `--dangerously-skip-permissions` - 跳过所有确认
- `--allowedTools "..."` - 预授权工具
- `--max-turns 200` - 迭代次数限制

---

## SDD驱动开发流程 (Specification-Driven Development)

### 概述

Canvas Learning System采用**SDD（规范驱动开发）**方法，确保开发过程中：
- 所有API端点有OpenAPI规范定义
- 所有数据结构有JSON Schema定义
- 所有技术决策有ADR记录
- Story和代码都能追溯到规范来源

### SDD工件位置

| 工件类型 | 位置 | 创建时机 | 消费者 |
|----------|------|----------|--------|
| OpenAPI Specs | `specs/api/*.openapi.yml` | Phase 3 (Architect) | SM, Dev, QA |
| JSON Schemas | `specs/data/*.schema.json` | Phase 3 (Architect) | SM, Dev, QA |
| Gherkin Specs | `specs/behavior/*.feature` | Phase 3 (Architect) | SM, Dev, QA |
| ADRs | `docs/architecture/decisions/*.md` | Phase 3 (Architect) | SM, Dev |

### SDD在各Phase的角色

```
Phase 2: Planning Iteration Management
┌─────────────────────────────────────┐
│ *validate 验证OpenAPI/Schema变更    │
│ - 检测Breaking Changes              │
│ - 检查版本号递增                    │
└────────────────┬────────────────────┘
                 │
                 ▼
Phase 3: Solutioning
┌─────────────────────────────────────┐
│ /architect 创建SDD工件              │
│ - *create-backend-architecture      │
│ - *create-adr                       │
│ - 创建OpenAPI specs                 │
│ - 创建JSON Schemas                  │
└────────────────┬────────────────────┘
                 │
                 ▼
Phase 4: Implementation
┌─────────────────────────────────────┐
│ /sm *draft 读取并引用SDD            │
│ - Step 3.3: 读取specs/目录          │
│ - Step 3.4: 关联相关ADR             │
│ - Story包含SDD规范参考Section       │
├─────────────────────────────────────┤
│ validate-story-sdd.py 契约验证      │
│ - 验证API端点在OpenAPI中定义        │
│ - 验证数据模型在Schema中定义        │
│ - 验证ADR引用存在                   │
├─────────────────────────────────────┤
│ /dev *develop-story                 │
│ - 基于Story中的SDD引用开发          │
│ - devLoadAlwaysFiles加载specs       │
├─────────────────────────────────────┤
│ /qa *review                         │
│ - 可选运行SDD契约验证               │
└─────────────────────────────────────┘
```

### SM编写Story时的SDD集成

SM使用`*draft`命令时，自动执行以下步骤：

1. **Step 3.3 读取SDD规范**:
   - 读取`specs/api/*.openapi.yml`
   - 读取`specs/data/*.schema.json`
   - 提取与Story相关的端点和Schema

2. **Step 3.4 关联ADR**:
   - 扫描`docs/architecture/decisions/`
   - 根据Story技术栈关联相关ADR
   - 提取ADR中的约束和影响

3. **Step 5 填写Story模板**:
   - **SDD规范参考 (必填)**：API端点和Schema引用
   - **ADR决策关联 (必填)**：技术决策及其影响

### Story模板中的SDD Section示例

```markdown
## Dev Notes

### SDD规范参考 (必填)

**API端点**:
- `POST /api/canvas/analyze`
  - 来源: [Source: specs/api/canvas-api.openapi.yml#L156-L180]
  - 请求Schema: CanvasAnalyzeRequest
  - 响应Schema: AnalysisResult

**数据Schema**:
- CanvasNode: [Source: specs/data/canvas-node.schema.json]
  - 必填字段: id, type, x, y, width, height
- AgentResponse: [Source: specs/data/agent-response.schema.json]

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-002 | Vector Database选型(LanceDB) | 向量存储使用LanceDB API |
| ADR-003 | Agentic RAG架构 | 采用Router-Fusion-Reranking模式 |

**关键约束**:
- LanceDB要求embedding维度为1536
- RAG查询必须经过Router判断
```

### Phase 4 SDD契约验证

在Story编写完成后或QA Review时，运行契约验证：

```bash
# 验证单个Story
python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md

# Strict模式（warnings视为errors）
python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md --strict

# 指定输出路径
python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md --output validation-report.md
```

**验证内容**:
- ✅ SDD规范参考Section存在且非空
- ✅ ADR决策关联Section存在且非空
- ✅ API端点在OpenAPI spec中定义
- ✅ Schema引用在specs/data/中存在
- ✅ ADR引用在decisions/目录中存在

**验证结果**:
- **PASSED**: Story可以进入开发
- **PASSED WITH WARNINGS**: 建议修复但可以进入开发
- **FAILED**: 必须修复后才能进入开发

### 完整SDD工作流示例

```bash
# ══════════════════════════════════════════════════════════════
# Phase 2: 验证OpenAPI/Schema变更
# ══════════════════════════════════════════════════════════════
/planning
*init "Epic 12 - Three-Layer Memory"

# 修改specs后验证
*validate

Marcus:
⏳ Running validation...
   └─ PRD: Validated
   └─ OpenAPI: No breaking changes ✅
   └─ Schemas: Compatible ✅
✅ Validation Passed!

*finalize

# ══════════════════════════════════════════════════════════════
# Phase 3: 创建SDD工件
# ══════════════════════════════════════════════════════════════
/architect

*create-adr "Vector Database Selection"
# → docs/architecture/decisions/0002-vector-database-selection.md

*create-adr "Agentic RAG Architecture"
# → docs/architecture/decisions/0003-agentic-rag-architecture.md

# 手动创建或更新OpenAPI specs
# → specs/api/canvas-api.openapi.yml
# → specs/data/canvas-node.schema.json

*exit

# ══════════════════════════════════════════════════════════════
# Phase 4: SM编写Story（包含SDD引用）
# ══════════════════════════════════════════════════════════════
/sm

*draft

Bob (SM):
⏳ Reading specs/api/*.openapi.yml...
⏳ Reading specs/data/*.schema.json...
⏳ Scanning ADRs for LanceDB, LangGraph...
✅ Found 2 related ADRs: ADR-002, ADR-003

📝 Story 12.1 created with:
   - SDD规范参考: 3 API endpoints, 2 Schemas
   - ADR决策关联: ADR-002, ADR-003

*exit

# ══════════════════════════════════════════════════════════════
# Phase 4: SDD契约验证
# ══════════════════════════════════════════════════════════════
python scripts/validate-story-sdd.py --story docs/stories/12.1.story.md

✅ VALIDATION PASSED: Story ready for development

# ══════════════════════════════════════════════════════════════
# Phase 4: Dev开发（基于SDD）
# ══════════════════════════════════════════════════════════════
/dev

*develop-story story-12.1

James (Dev):
⏳ Loading devLoadAlwaysFiles (includes specs)...
⏳ Reading Story SDD规范参考...
⏳ Implementing based on specs/api/canvas-api.openapi.yml...
✅ Implementation follows SDD contract
```

### 常见问题

#### Q: 如果Story涉及的API端点未在OpenAPI中定义怎么办？

**A**: SM会在Step 3.3质量门禁处HALT，并提示：
```
⚠️ API端点 POST /api/memory/store 未在OpenAPI spec中定义
→ 请通知Architect补充规范后再继续
```

需要先在Phase 3补充OpenAPI spec，然后SM继续编写Story。

#### Q: 如果没有相关ADR怎么办？

**A**: SM会在ADR决策关联section中说明：
```
**注意**: 本Story涉及的OAuth认证技术栈尚无对应ADR。
建议Architect创建ADR记录此技术选型决策。
```

Story可以继续，但建议补充ADR以保持架构决策可追溯性。

#### Q: Dev Agent如何使用SDD规范？

**A**: Dev Agent通过以下方式获取SDD上下文：
1. `devLoadAlwaysFiles`自动加载`specs/api/*.yml`和`specs/data/*.json`
2. Story的Dev Notes中包含完整的SDD引用
3. 代码中添加来源标注：`# [Source: specs/api/canvas-api.openapi.yml#L156]`

---

**文档版本**: 1.1
**更新日期**: 2025-11-21
**适用于**: Canvas Learning System + BMad 4.0
**新增**: SDD驱动开发流程、validate-story-sdd.py工具
