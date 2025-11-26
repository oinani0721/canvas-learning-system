---
<!-- TEMP_COMPACT_SNAPSHOT_START -->
# Context Snapshot [2025-11-25 18:05:58]

**Snapshot File**: .claude/compact-snapshot-20251125180558.md
**Snapshot Time**: 2025-11-25 18:05:58
**Valid For**: 2 hours (auto-cleanup after expiration)

**Note**:
- This is a context snapshot before conversation compression
- Snapshot was automatically filled by PreCompact hook (PowerShell transcript parsing)
- If continuing conversation after compression (within 2 hours), use Read tool to load snapshot file
- If starting new conversation, SessionStart hook will automatically clean up this reference

<!-- TEMP_COMPACT_SNAPSHOT_END -->
---
---
---
---
---
---
---
---
---
---
---
---

---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---

---
---
---
---

---
---

---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---
---

## 📖 Documentation Structure

**This file (CLAUDE.md)**: Core project overview and BMad integration guide (<5KB)
**helpers.md**: Detailed procedural documentation (agents, workflows, architecture)

**Quick Links**:
- Detailed Agent Descriptions: @helpers.md#Section-1-14-agents详细说明
- Color System & Workflow: @helpers.md#Section-2-canvas颜色系统和工作流规则
- 8-Step Learning Loop: @helpers.md#Section-3-8步学习循环详解
- Technical Verification: @helpers.md#Section-4-技术验证检查清单
- Architecture Details: @helpers.md#Section-5-技术架构详解
- Project Structure: @helpers.md#Section-6-项目结构和资源

---

## 🎯 Project Overview

Canvas Learning System - Obsidian Canvas-based AI-assisted learning system using **Feynman Learning Method** with **14 specialized Agents**.

**Core Principle**: "Learning by teaching - if you can't explain it simply, you don't understand it"

**Key Features**:
- **14 Specialized Agents** (12 learning + 2 system-level)
- **Color-coded Progress** (🔴 Red → 🟣 Purple → 🟢 Green)
- **4-Dimension Scoring** (Accuracy, Imagery, Completeness, Originality)
- **Paperless Review System** (Verification canvas for knowledge reproduction)
- **Async Parallel Execution** (8x performance boost, 12 concurrent agents)

---

## 🔄 BMad 4.0 Complete Workflow Guide ⭐ CRITICAL

**Updated**: 2025-11-19 | **Status**: Complete Workflow Documented

### BMad 4-Phase Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Phase 1         │     │ Phase 2         │     │ Phase 3         │     │ Phase 4         │
│ ANALYSIS        │ ──► │ PLANNING        │ ──► │ SOLUTIONING     │ ──► │ IMPLEMENTATION  │
│ (Optional)      │     │ (Required)      │     │ (Architecture)  │     │ (Development)   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ • Brainstorming │     │ • PRD Creation  │     │ • Architecture  │     │ • Story Dev     │
│ • Market Research│    │ • Epic/Story    │     │ • ADRs          │     │ • Code Review   │
│ • Project Brief │     │ • UX Spec       │     │ • Tech Decisions│     │ • QA Testing    │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
      Analyst                  PM                   Architect              SM/Dev/QA
```

**Core Philosophy**: **Conversation-driven, NOT script-driven** - Use natural language + *commands

---

### 1. Complete Agent Command Reference ⭐⭐⭐

#### PM Agent (John 📋) - 13 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*create-prd` | Generate PRD from project brief | **Phase 2** |
| `*create-brownfield-prd` | PRD for existing projects | Phase 2 |
| `*create-brownfield-epic` | Epic for brownfield projects | Phase 2 |
| `*create-brownfield-story` | Story for brownfield projects | Phase 2 |
| `*create-behavior-spec {feature}` | **Create Gherkin BDD specification** | **Phase 2** |
| `*create-epic` | Create new epic | Phase 2 |
| `*create-story` | Create user story | Phase 2 |
| `*shard-prd` | Split large PRD into parts | Phase 2 |
| `*doc-out` | Output document to file | Phase 2 |
| `*yolo` | Toggle YOLO mode (skip confirmations) | Any |
| `*correct-course` | **Handle change triggers** | **Phase 2/4** |
| `*exit` | Exit PM agent | Any |

#### Architect Agent (Winston 🏗️) - 14 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*create-adr {title}` | Create Architecture Decision Record | **Phase 3** |
| `*create-openapi` | Create OpenAPI specification from PRD/Architecture | **Phase 3** |
| `*create-schemas` | Create JSON Schemas for data models | **Phase 3** |
| `*create-backend-architecture` | Backend system design | Phase 3 |
| `*create-front-end-architecture` | Frontend architecture | Phase 3 |
| `*create-full-stack-architecture` | Full-stack design | Phase 3 |
| `*create-brownfield-architecture` | Architecture for existing projects | Phase 3 |
| `*document-project` | Document existing codebase | Phase 3 |
| `*execute-checklist {checklist}` | Run architecture checklist | Phase 3 |
| `*research {topic}` | Deep research on topic | Phase 3 |
| `*shard-prd` | Split architecture.md | Phase 3 |
| `*doc-out` | Output document to file | Phase 3 |
| `*yolo` | Toggle YOLO mode | Any |
| `*exit` | Exit Architect agent | Any |

#### Scrum Master Agent (Bob 🏃) - 5 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*draft` | Create next story from epic | **Phase 4** |
| `*story-checklist` | Validate story draft | Phase 4 |
| `*correct-course` | **Handle scope shifts** | **Phase 2/4** |
| `*exit` | Exit SM agent | Any |

#### Developer Agent (James 💻) - 6 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*develop-story` | Implement story with tests | **Phase 4** |
| `*explain` | Explain implementation decisions | Phase 4 |
| `*review-qa` | Apply QA fixes | Phase 4 |
| `*run-tests` | Execute linting and tests | Phase 4 |
| `*exit` | Exit Dev agent | Any |

#### QA Agent (Quinn 🧪) - 8 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*risk-profile {story}` | Assess story risk | **Phase 4** |
| `*test-design {story}` | Design test scenarios | Phase 4 |
| `*trace {story}` | Trace requirements (Given-When-Then) | Phase 4 |
| `*nfr-assess {story}` | Non-functional requirements check | Phase 4 |
| `*review {story}` | Comprehensive QA review | Phase 4 |
| `*gate {story}` | Quality gate decision | Phase 4 |
| `*exit` | Exit QA agent | Any |

#### Product Owner Agent (Sarah 📝) - 9 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*execute-checklist-po` | Run PO master checklist | **Phase 2/3** |
| `*validate-story-draft {story}` | Validate story | Phase 3 |
| `*shard-doc {doc} {dest}` | Shard any document | Phase 2/3 |
| `*create-epic` | Create epic | Phase 2 |
| `*create-story` | Create user story | Phase 2 |
| `*doc-out` | Output document | Phase 2 |
| `*correct-course` | Handle requirement changes | **Phase 2/4** |
| `*yolo` | Toggle YOLO mode | Any |
| `*exit` | Exit PO agent | Any |

#### Business Analyst Agent (Mary 📊) - 8 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*create-project-brief` | Create project brief | **Phase 1** |
| `*perform-market-research` | Market research report | Phase 1 |
| `*create-competitor-analysis` | Competitor analysis | Phase 1 |
| `*brainstorm {topic}` | Facilitate brainstorming | Phase 1 |
| `*elicit` | Advanced requirements elicitation | Phase 1 |
| `*research-prompt {topic}` | Deep research prompt | Phase 1 |
| `*doc-out` | Output document | Phase 1 |
| `*yolo` | Toggle YOLO mode | Any |
| `*exit` | Exit BA agent | Any |

#### Planning Orchestrator (Marcus 🎯) - 7 Commands ⚡ Canvas Extension

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*init` | Initialize new iteration with snapshot | **Phase 2** |
| `*validate` | Run validation including SDD checks | Phase 2 |
| `*finalize` | Complete iteration with Git tag | Phase 2 |
| `*rollback` | Restore previous iteration state | Phase 2 |
| `*compare` | Diff between iterations | Phase 2 |
| `*status` | Show current iteration state | Phase 2 |
| `*exit` | Exit Planning Orchestrator | Any |

#### Parallel Dev Coordinator (Alex ⚡) - 6 Commands ⚡ Canvas Extension

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*analyze` | Analyze Story dependencies and conflicts | **Phase 4** |
| `*init` | Create worktrees for parallel Stories | Phase 4 |
| `*status` | Show all worktree progress | Phase 4 |
| `*merge` | Merge completed worktrees | Phase 4 |
| `*cleanup` | Remove completed worktrees | Phase 4 |
| `*exit` | Exit Parallel Dev Coordinator | Any |

---

### 2. `*correct-course` - 变更触发处理 ⚠️ CRITICAL

**Available To**: PM, SM, PO (3个Agent)

**Purpose**: 处理**任何阶段的变更触发**，输出 `sprint-change-proposal-{date}.md`

#### 两种使用场景

| 场景 | 阶段 | 工作流 |
|------|------|--------|
| **Planning迭代变更** | Phase 2 | `@pm *correct-course` → `@iteration-validator` 验证 |
| **Sprint中变更** | Phase 4 | `@sm *correct-course` → 生成变更提案 |

#### Phase 2 使用 (Planning迭代)
```bash
# 需要修改PRD/Architecture时
User: "/planning"
User: "*init"

# 使用 *correct-course 进行变更分析
User: "@pm *correct-course 添加Epic 13 - Ebbinghaus Review"

PM Agent:
⏳ 分析变更影响...
✅ Generated: sprint-change-proposal-20251119.md
   - 影响的Epics: Epic 8, Epic 10
   - 影响的API: 3个端点

# 使用 @iteration-validator 验证变更
User: "@iteration-validator Validate current changes"

Validator:
⏳ 检测breaking changes...
✅ No breaking changes detected
⚠️ 建议更新 CHANGELOG.md
```

#### Phase 4 使用 (Sprint中变更)
```bash
# 开发过程中发现技术转向
User: "@sm *correct-course 发现认证需要OAuth而非JWT"

SM Agent:
⏳ Analyzing impact...
✅ Generated: sprint-change-proposal-20251119.md
   - Stories affected: 3
   - Estimated impact: +2 story points
   - Recommendation: Proceed with changes
```

#### 命令选择指南

| 任务 | 正确命令 | 阶段 |
|------|----------|------|
| 首次创建PRD | `*create-prd` | Phase 2 |
| 添加新Epic | `*create-epic` | Phase 2 |
| **修改已有PRD/Epic** | `*correct-course` + `@iteration-validator` | Phase 2 |
| Sprint范围变更 | `*correct-course` | Phase 4 |
| 技术转向 | `*correct-course` | Phase 4 |

---

### 3. Phase Transition Signals & Commands

| Transition | Signal | Command/Action |
|------------|--------|----------------|
| **Start → Phase 1** | User wants to explore idea | `@analyst *create-project-brief` |
| **Phase 1 → Phase 2** | Project Brief complete | `@pm *create-prd` |
| **Phase 2 iterations** | Need to refine PRD | `/planning` → `*init` (Canvas extension) |
| **Phase 2 → Phase 3** | PRD validated by PO | `@architect *create-*-architecture` |
| **Phase 3 → Phase 4** | Architecture complete | `@po *execute-checklist-po` then `@sm *draft` |
| **Phase 4 iterations** | Develop stories | `@dev *develop-story` → `@qa *review` |
| **Phase 4 parallel** | Multiple Stories ready | `/parallel` → `*analyze` → `*init` (Canvas extension) |
| **Phase 4 changes** | Mid-sprint changes | `*correct-course` |
| **Phase 4 → Phase 2** | Major requirement changes | `/planning` → `*init` |

---

### 4. Planning Iteration Management (⚡ Canvas Custom Extension)

**⚠️ IMPORTANT**: This is a **Canvas project custom extension** to fill BMad's gap in Planning Phase version control. It is NOT official BMad.

**Problem Solved**: BMad has **NO built-in iteration tracking** for Phase 2. Multiple PRD edits overwrite without history.

**Components** (All Canvas-specific):
- **`@planning-orchestrator`**: Coordinates Planning workflow
- **`@iteration-validator`**: Validates changes, detects breaking changes
- **Python Scripts**: `snapshot-planning.py`, `validate-iteration.py`, etc.
- **Git Pre-Commit Hook**: Auto-validates Planning file commits

#### When to Use

| Scenario | Use Planning Iteration Mgmt? | Tool |
|----------|------------------------------|------|
| First PRD creation | ✅ Yes (Iteration 1) | `/planning` → `*init` then `/pm *create-prd` |
| Refine PRD/Architecture | ✅ Yes (Iteration 2+) | `/planning` → `*init` then edit/`*create-prd` |
| Add/modify Epic | ✅ Yes | Same as above |
| Update API spec | ✅ Yes | Same as above |
| Simple typo fix | ❌ Optional | Direct commit |
| Mid-sprint changes | ❌ No (use BMad official) | `*correct-course` |

#### Complete Workflow

```bash
# ══════════════════════════════════════════════════════════════════
# PHASE 2: Planning with Iteration Management (Canvas Extension)
# ══════════════════════════════════════════════════════════════════

# Step 1: Activate Planning Orchestrator
/planning

Marcus (Planning Orchestrator):
🎯 Hello! I'm Marcus, your Planning Orchestrator.
Available commands: *init, *validate, *finalize, *rollback, *compare, *status

# Step 2: Initialize Iteration
*init

Marcus:
✅ Pre-flight checks passed
⏳ Initializing Iteration 4...
   └─ Snapshot: iterations/iteration-004.json
   └─ Branch: planning-iteration-4

✅ Iteration 4 initialized
📋 Ready for Planning changes

# Step 3: Make Changes (使用 BMad PM Agent)
/pm
*correct-course "添加Epic 13 - Ebbinghaus Review"

PM Agent:
✅ Generated: sprint-change-proposal-20251119.md

# Step 4: Validate Changes ⭐ KEY
/planning
*validate

Marcus:
⏳ Running validation...
   └─ PRD: Validated
   └─ OpenAPI: No breaking changes
   └─ Schemas: Compatible
✅ Validation Passed!

# Step 5: Finalize Iteration
*finalize

Marcus:
✅ Git tag: planning-v4
🎉 Iteration 4 Complete!

# ══════════════════════════════════════════════════════════════════
# PHASE 4: Parallel Development (Canvas Extension)
# ══════════════════════════════════════════════════════════════════

# Step 1: Activate Parallel Coordinator
/parallel

Alex (Parallel Dev Coordinator):
⚡ Hello! I'm Alex, your Parallel Dev Coordinator.
Available commands: *analyze, *init, *status, *merge, *cleanup

# Step 2: Analyze Story dependencies
*analyze "13.1, 13.2, 13.3, 13.4"

Alex:
✅ Safe to parallelize: 13.1, 13.2, 13.4
⚠️ Conflict: 13.1 ↔ 13.3 on src/review_engine.py

# Step 3: Create worktrees
*init "13.1, 13.2, 13.4"

Alex:
✅ Created 3 worktrees
   └─ Canvas-develop-13.1
   └─ Canvas-develop-13.2
   └─ Canvas-develop-13.4

# Step 4: Develop in each worktree (separate Claude Code windows)
# In each window: /dev → *develop-story {story_id}

# Step 5: Monitor progress
*status

# Step 6: Merge completed work
*merge --all
```

---

### 5. Helper System - Canvas操作参考文档

**核心价值**: 将详细操作指南组织在单独文件中，需要时请Claude读取特定Section。

**⚠️ 重要说明**:
- `@helpers.md#Section-Name`语法**不会被Claude自动解析**
- 需要**手动请求Claude读取**或**复制粘贴**相关内容到对话中
- 这是**参考文档**，不是自动加载机制

**helpers.md内容** (716行):
- Section 1: 14 Agents完整规格 (250行)
- Section 2-3: 颜色系统/8步循环 (115行)
- Section 4-5: 技术验证/架构详解 (160行)
- Section 6: 项目结构资源 (120行)

**使用方式**:
```bash
# 方式1: 请Claude读取特定Section
"请读取helpers.md的Section-5技术架构详解"

# 方式2: 直接引用（Claude会理解并读取）
"根据@helpers.md#Section-4-技术验证检查清单，检查这段代码"
```

**何时使用**:
- 需要14个Agents的详细规格时
- 需要Canvas颜色系统完整规则时
- 需要8步学习循环详细流程时

---

### 6. Edge Cases & Special Scenarios

#### Breaking Changes Handling

```bash
# Git pre-commit hook detects breaking change
$ git commit -m "Update API"

❌ Breaking Changes Detected!
   - Endpoint deleted: DELETE /api/cache/{id}
   - Required field added: User.email_verified

Options:
  A. Fix issues and retry
  B. Accept: @planning-orchestrator "Finalize iteration, accept breaking changes"
  C. Rollback: @planning-orchestrator "Rollback to iteration 3"

# If accepting breaking changes
User: "@planning-orchestrator Finalize iteration, accept breaking changes"

Orchestrator:
⚠️ Breaking changes accepted
   - API version: v1.5.0 → v2.0.0 (MAJOR)
   - Git tag: planning-v4-BREAKING

⚠️ REQUIRED ACTIONS:
   1. Document migration path in CHANGELOG.md
   2. Notify all stakeholders
   3. Update consumer applications
```

#### Multi-Epic Coordination

```bash
# When changes affect multiple Epics
User: "/planning"
User: "*init"

Orchestrator:
✅ Iteration N initialized
⏳ Scanning affected Epics...
📊 Impact Analysis:
   - Epic 8: 3 stories affected
   - Epic 10: 2 stories affected
   - Epic 12: API contract changes

Recommendation: Use @po *execute-checklist-po to validate alignment
```

#### Quality Gate Decisions (QA)

| Decision | Meaning | Action |
|----------|---------|--------|
| **PASS** | All critical requirements met | Proceed to next story |
| **CONCERNS** | Non-critical issues | Team reviews, may proceed |
| **FAIL** | Critical issues (security, P0 tests missing) | Must fix before proceeding |
| **WAIVED** | Issues acknowledged but accepted | Document reason, approver, expiry |

#### High-Risk Story Workflow

```bash
# Before development
User: "@qa *risk-profile Story-13.1"  # Identify pitfalls early
User: "@qa *test-design Story-13.1"   # Guide test strategy

# During development
User: "@dev *develop-story Story-13.1"
User: "@qa *trace Story-13.1"         # Verify coverage
User: "@qa *nfr-assess Story-13.1"    # Check quality issues

# Quality gate
User: "@qa *gate Story-13.1"          # Final decision
```

---

### 7. Anti-Hallucination Measures by Phase

**How to maintain global view and avoid API hallucinations across multiple Epics?**

| Phase | Tool | Purpose | How to Invoke |
|-------|------|---------|---------------|
| **Phase 2** | Planning Iteration Management | Track changes, detect breaking changes | `@planning-orchestrator`, `@iteration-validator` |
| **Phase 2/3** | OpenAPI Specs | Define API contracts | `@architect "请创建OpenAPI规范"` |
| **Phase 2/3** | JSON Schemas | Define data structures | `@pm "请定义Canvas节点Schema"` |
| **Phase 3** | ADRs | Record architecture decisions | `@architect "请为此决策创建ADR"` |
| **Phase 4** | devLoadAlwaysFiles | Load architecture context | 自动加载 (core-config.yaml) |
| **Phase 4** | Contract Testing | Validate code against specs | ✅ 已实现 (tests/contract/) |
| **Phase 4** | project-file-index.md | Prevent file path hallucination | 自动生成 (scripts/generate-file-index.py) |

**Chain-of-Verification Protocol** (防止文件幻觉):
```
Before referencing any file, API endpoint, or data model:
1. Check project-file-index.md first
2. If not found, use Glob/Grep to verify
3. If still not found, explicitly state uncertainty
4. NEVER invent file paths not in the index
```

**SDD调用示例**:
```bash
# Phase 2/3: 创建OpenAPI规范
User: "@architect 请为Canvas Learning System创建OpenAPI规范"
→ 产出: specs/api/canvas-api.openapi.yml

# Phase 2/3: 定义JSON Schema
User: "@pm 请定义Canvas节点的JSON Schema"
→ 产出: specs/data/canvas-node.schema.json

# Phase 3: 记录架构决策
User: "@architect 请为'使用LangGraph'决策创建ADR"
→ 产出: docs/architecture/decisions/0002-langgraph-agents.md
```

**Key Insight**: Planning Iteration Management is the **first line of defense** - catches issues in Phase 2 before they reach Phase 4.

**⚠️ 注意**:
- SDD artifacts通过**自然语言与Agent对话**创建
- 没有专门的`*create-openapi`或`*create-schema`命令
- Contract Testing已实现 (tests/contract/)

---

### 7a. Source of Truth (SoT) Hierarchy ⭐ NEW

**Purpose**: Define authoritative source when documents conflict.

**Hierarchy** (highest to lowest authority):
```
1. PRD (Level 1)           ← WHAT: Functional requirements
2. Architecture (Level 2)  ← HOW: System design
3. JSON Schema (Level 3)   ← Data structure contracts
4. OpenAPI Spec (Level 4)  ← API behavior contracts
5. Stories (Level 5)       ← Implementation details
6. Code (Level 6)          ← Must comply with all above
```

**Conflict Resolution Protocol**:
1. **HALT** - Stop validation/development
2. **Detect** - Identify conflicting documents
3. **Apply Hierarchy** - Higher level wins
4. **Confirm** - User approves resolution
5. **Update** - Fix lower-level document
6. **Re-validate** - Run validation again

**Validation Integration**:
- **PO `*validate-story-draft`**: Steps 8a-8d check SoT consistency
- **Contract Testing**: Schemathesis validates Code vs OpenAPI
- **Pre-commit Hook**: Blocks commits violating specifications

**Reference**: `docs/architecture/sot-hierarchy.md` for complete protocol

---

### 8. Phase 4正确工作流 - SM/Dev/QA循环 ⭐ CRITICAL

**⚠️ 关键理解**: PRD/Architecture**不需要手动传递给SM**，SM通过`core-config.yaml`配置自动读取。

#### 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Implementation - 正确的BMad工作流                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │ /sm         │ ← 激活Scrum Master Agent                   │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │ *draft                                      │           │
│  │ SM自动执行:                                  │           │
│  │   1. 读取core-config.yaml获取路径:           │           │
│  │      - prdShardedLocation: docs/prd         │           │
│  │      - architectureShardedLocation: docs/arch│           │
│  │   2. 自动加载当前Epic文件                     │           │
│  │   3. 自动加载相关Architecture文档             │           │
│  │   4. 生成Story with完整Dev Notes             │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │ 用户审核    │ ← 检查Story draft，确认内容正确            │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │ /dev                                        │           │
│  │ Dev Agent自动执行:                           │           │
│  │   - 读取core-config.yaml                    │           │
│  │   - 加载devLoadAlwaysFiles (SDD规范等)       │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │ *develop-story {story-id}                   │           │
│  │ ⚠️ 关键: Dev只读Story文件，不加载PRD/Arch    │           │
│  │ Story的Dev Notes已包含所有需要的技术上下文    │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │ /qa         │ ← 激活QA Agent                             │
│  │ *review     │ ← 综合审查 + 质量门禁                       │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │ 循环继续    │ ← 返回 /sm *draft 处理下一个Story          │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 关键原则

1. **Story是自包含的** - Dev Agent只需Story文件，不再加载PRD/Architecture
2. **SM自动加载文档** - 通过`*draft`任务从config路径读取
3. **Dev只加载devLoadAlwaysFiles** - 编码标准和SDD规范
4. **不需要手动传递文件** - 配置路径自动解析

#### 示例

```bash
# Step 1: 激活SM，创建Story
/sm
*draft
# SM自动:
#   - 读取 docs/prd/epic-13-ebbinghaus.md
#   - 读取 docs/architecture/coding-standards.md
#   - 生成 docs/stories/story-13.1.md (含完整Dev Notes)

# Step 2: 激活Dev，开发Story
/dev
*develop-story story-13.1
# Dev只读取story-13.1.md，不加载PRD/Architecture
# Story的Dev Notes包含所有需要的API规范、数据模型等

# Step 3: 激活QA，审查
/qa
*review story-13.1
```

---

### 9. Supporting Infrastructure

#### YAML Status Tracking

**Purpose**: Maintain Epic/Story completion status across sessions

**File**: `.bmad-core/data/canvas-project-status.yaml`

**Loaded**: Session start (via `.claude/hooks/session-start-load-status.ps1`)

#### devLoadAlwaysFiles

**Purpose**: Dev Agent加载架构文档作为开发参考

**⚠️ 重要：加载时机**
- **不是**"会话启动时自动加载"
- **只有**当执行`/dev`命令激活Dev Agent时才加载
- 其他Agent（SM, PM, QA等）不会自动加载这些文件

**Config**: `.bmad-core/core-config.yaml`

```yaml
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md
  - docs/architecture/project-structure.md
  - docs/architecture/canvas-layer-architecture.md
  - CANVAS_ERROR_LOG.md
  - specs/api/canvas-api.openapi.yml      # SDD规范
  - specs/data/canvas-node.schema.json    # SDD规范
```

**作用**: 让Dev Agent在开发时有架构约束和SDD规范作为参考，减少幻觉

#### Document Sharding

**Purpose**: Split >20k tokens documents to avoid context collapse

**Triggers**: >20k consider, >40k recommended, >60k must shard

**Method**: Split by `## heading` into separate files

---

### 9. BMad Integration Checklist

Before continuing Canvas feature development, ensure:

**✅ Infrastructure**:
- [x] `.bmad-core/core-config.yaml` exists and configured
- [x] devLoadAlwaysFiles contains all architecture docs
- [x] `.bmad-core/data/canvas-project-status.yaml` exists
- [x] `.claude/hooks/session-start-load-status.ps1` exists

**✅ Planning Iteration Management** (Phase 2):
- [x] `.claude/agents/planning-orchestrator.md` exists
- [x] `.claude/agents/iteration-validator.md` exists
- [x] `scripts/snapshot-planning.py` exists
- [x] `scripts/validate-iteration.py` exists
- [x] `scripts/init-iteration.py` exists
- [x] `scripts/finalize-iteration.py` exists
- [x] Git pre-commit hook configured
- [x] `.bmad-core/validators/iteration-rules.yaml` exists

**✅ SDD Integration** (Partial):
- [x] `specs/api/canvas-api.openapi.yml` defines APIs (Phase 3 Architect)
- [x] `specs/data/*.schema.json` define data structures (Phase 2/3)
- [x] Contract Testing (✅ 已实现 - tests/contract/)
- [x] ADRs record architecture decisions (Phase 3 Architect)

**✅ Documentation Optimization**:
- [x] CLAUDE.md contains Planning Iteration Workflow section
- [x] helpers.md contains procedural sections (Phase 4)
- [x] All `@helpers.md#Section` references correct

**✅ Cognitive Alignment**:
- [x] Understand BMad is conversation-driven, NOT script-driven
- [x] Understand Helper System is 按需加载架构 (saves 50-70% tokens vs full embedding)
- [x] Understand Planning Iteration Management is Phase 2 quality gate
- [x] Understand YAML Status is progress tracking, NOT workflow orchestrator
- [x] Understand devLoadAlwaysFiles is read-only context, NOT executable scripts

---

## 🚀 Quick Start

### Prerequisites
1. **Obsidian** (View Canvas whiteboards)
2. **Python 3.9+** (Run canvas_utils.py)
3. **Claude Code** (Sub-agent system)

### Basic Usage

**Original Canvas Learning**:
```bash
"@离散数学.canvas 拆解'逆否命题'这个红色节点"  # basic-decomposition
"@离散数学.canvas 评分所有黄色节点"            # scoring-agent
"@离散数学.canvas 生成口语化解释'逆否命题'"    # oral-explanation
```

**Verification Canvas** (Epic 4):
```bash
"@离散数学.canvas 生成检验白板"  # Step 1: Generate verification canvas
# Step 2: Fill yellow nodes in Obsidian (without looking at original canvas)
"@离散数学-检验白板-20250115.canvas 评分所有黄色节点"  # Step 3: Score
# Step 4: Iterate until 80% green
```

---

## ⚠️ IMPORTANT: Read Before Any Canvas Operation

**MUST READ**: `CANVAS_ERROR_LOG.md`

**Core Points**:
1. 🟡 **Every question/explanation node MUST have a blank yellow node** (personal understanding area)
2. 💾 **All operations MUST actually modify Canvas file** (not just display)
3. 🎨 **Strictly follow color judgment standards**

---

## 🔧 Current Development Status

**Phase**: ✅ **BMad Integration Correction + Core Features Complete**

**Progress**:
- ✅ Epic 1-6: Core Learning System (100%)
- 🔄 Epic 12: BMad Integration Correction (In Progress)
  - ✅ Phase 1.1-1.3: CLAUDE.md updated, YAML Status created, session-start hook created
  - 🔄 Phase 1.4: CLAUDE.md sharding (Current task)
  - ⏳ Phase 2-4: OpenAPI Specs, Contract Testing, ADRs, helpers.md structure
- ⏳ Epic 13+: Future features (after Epic 12 complete)

**Statistics**:
- Agents: 14/14 (100%)
- Test Pass Rate: 357/360 (99.2%)
- Documentation: 100%
- BMad Integration: Aligning to official standard

---

## 📚 Core Documentation

**For Detailed Information**, see:

- **14 Agents**: @helpers.md#Section-1-14-agents详细说明
- **Color System & Workflow**: @helpers.md#Section-2-canvas颜色系统和工作流规则
- **8-Step Learning Loop**: @helpers.md#Section-3-8步学习循环详解
- **Technical Verification**: @helpers.md#Section-4-技术验证检查清单
- **Architecture**: @helpers.md#Section-5-技术架构详解
- **Project Structure**: @helpers.md#Section-6-项目结构和资源

**Additional Resources**:
- Project Brief: `docs/project-brief.md`
- PRD: `docs/prd/FULL-PRD-REFERENCE.md`
- Architecture Docs: `docs/architecture/`
- BMad Integration Research: `docs/RESEARCH_REPORT_BMAD_INTEGRATION.md`

---

## 💡 Best Practices Quick Reference

| Symptom | Recommended Agent | Goal |
|---------|------------------|------|
| Completely lost | basic-decomposition | Break down difficulty |
| Partial understanding (purple) | clarification-path | Deep understanding |
| Confusing concepts | comparison-table | Structured comparison |
| Need memorization | memory-anchor | Vivid analogies |
| Need practice | example-teaching | Example consolidation |

**Full table**: @helpers.md#Section-3-8步学习循环详解

---

**Encoding**: UTF-8
**Claude Code Auto-load**: ✅ This file is in project root
**Helper System**: 按需加载架构 (节省50-70% tokens)
**BMad 4.0 Integration**: ✅ Corrected and aligned to official standard
- --
# 📦 Canvas Learning System 迁移到Langgraph 开发obsdian插件规划阶段交付清单（含未创建文件）（所有文件都是在用Bmad，PM的correct-course指令修正PRD而产生的）

## 📊 总览统计

| 类别 | 已创建 | 待创建 | 总计 |
|------|--------|--------|------|
| 核心文档 | 3 | 0 | 3 |
| SCP提案 | 5 | 0 | 5 |
| 技术验证文档 | 5 | 0 | 5 |
| Epic文档 | 4 | 0 | 4 |
| ADR决策 | 4 | 0 | 4 |
| 架构文档 | 11 | 2 | 13 |
| Story文档 | 60+ | 80+ | 140+ |
| 技术报告 | 8 | 0 | 8 |
| 配置文件 | 1 | 0 | 1 |
| 代码实现 | 60+ | 80+ | 140+ |

---

## 一、核心项目文档

### ✅ 已创建（3个）

| 文件 | 版本 | 行数 | 位置 |
|------|------|------|------|
| CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md | v1.1.8 | 5,272行 | docs/prd/ |
| CLAUDE.md | - | ~1,000行 | C:/Users/ROG/托福/ |
| README.md | - | ~500行 | C:/Users/ROG/托福/ |

---

## 二、Sprint变更提案（SCP）

### ✅ 已创建（5个）

| SCP | 文件名 | 行数 | 状态 |
|-----|--------|------|------|
| SCP-001 | SPRINT_CHANGE_PROPOSAL_SCP-001_智能并行处理UI需求补全.md | ~900行 | ✅ 已批准 |
| SCP-002 | SPRINT_CHANGE_PROPOSAL_SCP-002_艾宾浩斯系统数据源整合.md | ~800行 | ✅ 已批准 |
| SCP-003 | SPRINT_CHANGE_PROPOSAL_SCP-003_检验白板历史关联增强.md | ~800行 | ✅ 已批准 |
| SCP-004 | SPRINT_CHANGE_PROPOSAL_SCP-004_单节点智能分析UI.md | ~900行 | ✅ 已批准 |
| SCP-005 | SCP-005-REMOVE-API-CONCURRENCY-LIMITS-FINAL.md | ~600行 | ✅ 已批准 |

---

## 三、技术验证文档

### ✅ 已创建（5个）

| 文件 | 行数 | 位置 |
|------|------|------|
| technical-verification-checklist.md | ~200行 | .bmad-core/checklists/ |
| create-next-story.md | ~300行 | .bmad-core/tasks/ |
| context7-access-test.md | 299行 | docs/verification/ |
| local-skills-test.md | 600行 | docs/verification/ |
| story-12-1-verification-demo.md | 833行 | docs/examples/ |

---

## 四、Epic规划文档

### ✅ 已创建（4个）

| Epic | 文件名 | 行数 | 位置 |
|------|--------|------|------|
| Epic 0 | EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md | ~400行 | docs/prd/ |
| Epic 11 | EPIC-11-FASTAPI-BACKEND-DETAILED.md | ~800行 | docs/prd/ |
| Epic 12 | EPIC-12-3LAYER-MEMORY-AGENTIC-RAG.md | ~25,000字 | docs/epics/ |
| Epic 12 | EPIC-12-STORY-MAP.md | ~20,000字 | docs/epics/ |

---

## 五、架构决策记录（ADR）

### ✅ 已创建（4个）

| ADR | 文件名 | 行数 | 决策内容 |
|-----|--------|------|----------|
| ADR-001 | ADR-001-local-model-vs-api.md | ~480行 | 本地模型优先策略 |
| ADR-002 | ADR-002-VECTOR-DATABASE-SELECTION.md | ~600行 | LanceDB选型 |
| ADR-003 | ADR-003-AGENTIC-RAG-ARCHITECTURE.md | ~700行 | Agentic RAG架构 |
| ADR-004 | ADR-004-GRAPHRAG-INTEGRATION-EVALUATION.md | ~500行 | GraphRAG评估（不引入） |

---

## 六、架构设计文档

### ✅ 已创建（11个）

| 文件名 | 行数 | 位置 |
|--------|------|------|
| LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md | 1,205行 | docs/architecture/ |
| GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md | ~1,200行 | docs/architecture/ |
| MULTI-AGENT-CONCURRENT-ANALYSIS-SYSTEM-ARCHITECTURE.md | ~800行 | docs/architecture/ |
| GRAPHRAG-INTEGRATION-DESIGN.md | ~3,500行 | docs/architecture/ |
| canvas-progress-tracking-brownfield-architecture.md | ~800行 | docs/architecture/ |
| COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md | ~80,000字 | docs/architecture/ |
| EPIC-11-BACKEND-ARCHITECTURE.md | ~1,200行 | docs/architecture/ |
| EPIC-11-DATA-MODELS.md | ~800行 | docs/architecture/ |
| epic10-concurrency-definition.md | ~1,000行 | docs/architecture/ |
| GRAPHITI-HYBRID-SEARCH-ANALYSIS.md | ~800行 | docs/architecture/ |
| FUSION-ALGORITHM-DESIGN.md | ~700行 | docs/architecture/ |

### ⏳ 待创建（2个）

| 文件名 | 预计行数 | 负责Agent |
|--------|----------|-----------|
| neo4j-review-history-schema-design.md | ~600行 | Architect |
| FastAPI-Backend-Detailed-Architecture.md | ~1,000行 | Architect |

---

## 七、API/接口规范文档

### ✅ 已创建（2个）

| 文件名 | 行数 | 内容 |
|--------|------|------|
| EPIC-11-API-SPECIFICATION.md | ~900行 | 19个API端点规范 |
| RERANKING-STRATEGY-SELECTION.md | ~600行 | 重排序策略设计 |

---

## 八、技术研究报告

### ✅ 已创建（4个）

| 文件名 | 行数 |
|--------|------|
| GRAPHITI-HYBRID-SEARCH-ANALYSIS.md | ~800行 |
| FUSION-ALGORITHM-DESIGN.md | ~700行 |
| RERANKING-STRATEGY-SELECTION.md | ~600行 |
| LANGGRAPH-INTEGRATION-DESIGN.md | ~750行 |

---

## 九、Story文档清单

### ✅ 已创建 Story（~60个）

#### Epic 0（4个）
- ✅ Story 0.1: Context7访问验证
- ✅ Story 0.2: 本地Skills验证
- ✅ Story 0.3: 技术验证示例
- ✅ Story 0.4: PRD和README更新

#### Epic 10（部分，~10个）
- ✅ Story 10.1-10.10（已完成）
- ✅ Story 10.15: 资源感知调度器

#### Epic 11（部分，6个）
- ✅ Story 11.6: API端点

#### Epic 12（16个Story已规划）
- Epic 12完整Story Map已创建

#### Epic 13（部分，8个）
- ✅ Story 13.8: UI实现

#### Epic 14（部分规划）
- 部分Story已规划

### ⏳ 待创建 Story（~80个）

#### Epic 6: 知识图谱查询推荐（5个）
- ⏳ Story 6.1-6.5（待创建）

#### Epic 7: 可视化（3个）
- ⏳ Story 7.1-7.3（待创建）

#### Epic 8: 智能检验白板调度（19个）
- ⏳ Story 8.1-8.19（待创建）

#### Epic 9: 文件监控引擎（10个）
- ⏳ Story 9.1-9.10（待创建）

#### Epic 11: FastAPI后端（6个）
- ⏳ Story 11.1: FastAPI应用初始化
- ⏳ Story 11.2: 路由系统
- ⏳ Story 11.3: 依赖注入
- ⏳ Story 11.4: 中间件
- ⏳ Story 11.5: 异步操作
- ✅ Story 11.6: API文档和测试（已创建）
- ⏳ Story 11.9: 单节点API（草稿存在）

#### Epic 12: 三层记忆+Agentic RAG（16个）
- ⏳ Story 12.1: LanceDB集成
- ⏳ Story 12.2: 数据迁移工具
- ⏳ Story 12.3: Graphiti增强
- ⏳ Story 12.4: Neo4j优化
- ⏳ Story 12.5: LangGraph StateGraph
- ⏳ Story 12.6: 并行检索节点
- ⏳ Story 12.7: RRF融合算法
- ⏳ Story 12.8: Weighted融合
- ⏳ Story 12.9: Cascade融合
- ⏳ Story 12.10: 混合Reranking
- ⏳ Story 12.11: Query重写循环
- ⏳ Story 12.12: Canvas集成
- ⏳ Story 12.13: 性能监控
- ⏳ Story 12.14: 成本追踪
- ⏳ Story 12.15: 集成测试
- ⏳ Story 12.16: 多模态扩展（P2）

#### Epic 13: UI集成（9个）
- ⏳ Story 13.1-13.7（待创建）
- ✅ Story 13.8: 智能并行处理UI（已创建）
- ⏳ Story 13.9: 单节点UI（草稿存在）

#### Epic 14: 艾宾浩斯复习系统（15个）
- ⏳ Story 14.1: 触发点1 - 24小时复习
- ⏳ Story 14.2: 触发点2 - 7天复习
- ⏳ Story 14.3: 触发点3 - 30天复习
- ⏳ Story 14.4: 触发点4调度逻辑（GDS.1已完成）
- ⏳ Story 14.5: Py-FSRS算法集成
- ⏳ Story 14.6: 复习调度系统
- ⏳ Story 14.7-14.12: 其他Story
- ⏳ Story 14.13: 检验历史记录存储
- ⏳ Story 14.14: 针对性复习算法
- ⏳ Story 14.15: 复习模式选择UI

#### Epic 15-18（待规划）
- ⏳ 各Epic的Story待创建

---

## 十、辅助交付文档

### ✅ 已创建（15个）

| 文件名 | 大小/行数 |
|--------|-----------|
| PM-TO-SM-HANDOFF-EPIC-11.md | ~800行 |
| SPRINT-KICKOFF-EPIC-11.md | ~1,000行 |
| PM-DELIVERABLES-EPIC-11.md | ~600行 |
| PM-PHASE-DELIVERABLES-CHECKLIST.md | ~1,000行 |
| PROJECT_DELIVERY_INVENTORY.md | ~2,000行 |
| SCP-001_明确交付文档清单.md | ~500行 |
| 交付物查看清单_SCP-001.md | ~300行 |
| SCP-001_交付物完成报告.md | ~400行 |
| PRD_v1.1.5_UPDATE_PATCH.md | ~500行 |
| PRD_EDIT_GUIDE_SCP-004.md | ~400行 |
| CANVAS-PRD-CHANGELOG-v1.1.8.md | 600+行 |
| prd-gap-analysis-ebbinghaus-system.md | 800行 |
| prd-architecture-conflict-analysis.md | 500行 |
| SECTION-1X-TECHNICAL-VERIFICATION-PROTOCOL.md | ~600行 |
| epic-graphrag-integration.md | ~1,000行 |

---

## 十一、GraphRAG Story文档

### ✅ 已创建（5个）

| Story | 文件名 | 行数 |
|-------|--------|------|
| GraphRAG.1 | graphrag-1-data-pipeline.story.md | ~540行 |
| GraphRAG.2 | graphrag-2-local-model-integration.story.md | ~650行 |
| GraphRAG.3 | graphrag-3-routing-fusion.story.md | ~620行 |
| GraphRAG.4 | graphrag-4-ebbinghaus-trigger-point-4.story.md | ~680行 |
| GraphRAG.5 | graphrag-5-performance-cost.story.md | ~850行 |

---

## 十二、配置文件

### ✅ 已创建（1个）

| 文件名 | 行数 |
|--------|------|
| graphrag_cost_control.json | ~350行 |

---

## 十三、代码实现文件

### ✅ 已实现（约60个模块）

#### Epic 1-5 核心模块
- ✅ canvas_utils.py (~100KB)
- ✅ ebbinghaus_review.py (870行)
- ✅ 其他Epic 1-5核心模块

#### Epic 10 部分模块
- ✅ AsyncExecutionEngine
- ✅ 并行处理核心模块

### ⏳ 待实现（约80个模块）

#### Epic 11: FastAPI后端（约15个文件）
- ⏳ main.py (FastAPI应用)
- ⏳ routers/ (API路由)
- ⏳ dependencies/ (依赖注入)
- ⏳ middleware/ (中间件)
- ⏳ models/ (Pydantic模型，31个)
- ⏳ tests/ (测试文件)

#### Epic 12: 三层记忆（约25个文件）
- ⏳ lancedb_client.py
- ⏳ graphiti_enhanced.py
- ⏳ langgraph_stategraph.py
- ⏳ fusion_algorithms.py
- ⏳ reranking_strategies.py
- ⏳ 相关测试文件

#### Epic 13: UI组件（约20个文件）
- ⏳ 6个核心TS文件
- ⏳ 6个React组件
- ⏳ 3个CSS文件
- ⏳ 测试文件

#### Epic 14: 艾宾浩斯系统（约15个文件）
- ⏳ fsrs_algorithm.py
- ⏳ review_scheduler.py
- ⏳ trigger_point_handlers.py
- ⏳ 相关测试文件

#### GraphRAG集成（约10个文件）
- ⏳ entity_extraction.py
- ⏳ ollama_integration.py
- ⏳ cost_tracker.py
- ⏳ hybrid_llm_provider.py

---

## 十四、测试文件

### ✅ 已创建（360+ 测试）
- Epic 1-5测试
- Epic 10部分测试

### ⏳ 待创建（约200+测试）
- Epic 11: 39个测试用例
- Epic 12: 约50个测试用例
- Epic 13: 59个测试用例
- Epic 14: 约40个测试用例
- 其他Epic测试

---

## 十五、文档备份文件

### ✅ 已创建

| 文件 | 用途 |
|------|------|
| PRD备份文件 (多个版本) | 安全备份 |
| 各SCP备份文件 | 变更记录 |

---

## 📈 完成度统计

| 阶段 | 完成度 | 说明 |
|------|--------|------|
| PM阶段 | 100% ✅ | 所有规划文档完成 |
| Epic 0-5 | 100% ✅ | 核心功能已完成 |
| Epic 10 | ~70% | 部分功能已完成 |
| Epic 11 | ~20% | 规划完成，待开发 |
| Epic 12 | ~10% | 规划完成，待开发 |
| Epic 13 | ~30% | 部分Story完成 |
| Epic 14 | ~40% | 部分功能完成 |
| Epic 6-9, 15-18 | ~10% | 规划阶段 |
| **整体** | **~60%** | 核心功能完成 |

---

## 🎯 关键路径文件（优先级P0）

1. ✅ PRD v1.1.8
2. ✅ CLAUDE.md
3. ✅ 所有SCP（1-5）
4. ✅ Epic 12完整规划
5. ⏳ Story 14.1-14.6（待创建）
6. ⏳ Story 12.1-12.15（待创建）
7. ⏳ Epic 11所有Story（待创建）

---

**总计文件数**: 约400+个（已创建150+，待创建250+）