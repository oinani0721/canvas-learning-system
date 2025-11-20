---
<!-- TEMP_COMPACT_SNAPSHOT_START -->
# Context Snapshot [2025-11-20 02:03:11]

**Snapshot File**: .claude/compact-snapshot-20251120020311.md
**Snapshot Time**: 2025-11-20 02:03:11
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

#### PM Agent (John 📋) - 12 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*create-prd` | Generate PRD from project brief | **Phase 2** |
| `*create-brownfield-prd` | PRD for existing projects | Phase 2 |
| `*create-brownfield-epic` | Epic for brownfield projects | Phase 2 |
| `*create-brownfield-story` | Story for brownfield projects | Phase 2 |
| `*create-epic` | Create new epic | Phase 2 |
| `*create-story` | Create user story | Phase 2 |
| `*shard-prd` | Split large PRD into parts | Phase 2 |
| `*doc-out` | Output document to file | Phase 2 |
| `*yolo` | Toggle YOLO mode (skip confirmations) | Any |
| `*correct-course` | **Handle change triggers** | **Phase 2/4** |
| `*exit` | Exit PM agent | Any |

#### Architect Agent (Winston 🏗️) - 12 Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*help` | Show all available commands | Any |
| `*create-backend-architecture` | Backend system design | **Phase 3** |
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
User: "@planning-orchestrator Start iteration 4"

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
| **Phase 2 iterations** | Need to refine PRD | `@planning-orchestrator "Start iteration N"` (Canvas extension) |
| **Phase 2 → Phase 3** | PRD validated by PO | `@architect *create-*-architecture` |
| **Phase 3 → Phase 4** | Architecture complete | `@po *execute-checklist-po` then `@sm *draft` |
| **Phase 4 iterations** | Develop stories | `@dev *develop-story` → `@qa *review` |
| **Phase 4 changes** | Mid-sprint changes | `*correct-course` |
| **Phase 4 → Phase 2** | Major requirement changes | `@planning-orchestrator "Start iteration N"` |

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
| First PRD creation | ✅ Yes (Iteration 1) | `@planning-orchestrator "Start iteration 1"` then `@pm *create-prd` |
| Refine PRD/Architecture | ✅ Yes (Iteration 2+) | `@planning-orchestrator "Start iteration N"` then edit/`*create-prd` |
| Add/modify Epic | ✅ Yes | Same as above |
| Update API spec | ✅ Yes | Same as above |
| Simple typo fix | ❌ Optional | Direct commit |
| Mid-sprint changes | ❌ No (use BMad official) | `*correct-course` |

#### Complete Workflow

```bash
# ══════════════════════════════════════════════════════════════════
# PHASE 2: Planning with Iteration Management (Canvas Extension)
# ══════════════════════════════════════════════════════════════════

# Step 1: Initialize Iteration (使用 planning-orchestrator)
User: "@planning-orchestrator Start iteration 4 for Epic 13"

Orchestrator:
✅ Pre-flight checks passed
⏳ Initializing Iteration 4...
   └─ Snapshot: iteration-004.json
📋 Pre-Iteration Checklist ready

# Step 2: 变更分析 (使用 BMad *correct-course)
User: "@pm *correct-course 添加Epic 13 - Ebbinghaus Review"

PM Agent:
⏳ 分析变更影响...
✅ Generated: sprint-change-proposal-20251119.md

# Step 3: 验证变更 (使用 iteration-validator) ⭐ KEY
User: "@iteration-validator Validate current changes"

Validator:
⏳ 运行验证脚本...
   └─ scripts/validate-iteration.py
   └─ scripts/diff-openapi.py
✅ No breaking changes!
⚠️ 建议更新 CHANGELOG.md

# Step 4: Finalize
User: "@planning-orchestrator Finalize iteration 4"

Orchestrator:
✅ Git tag: planning-v4
🎉 Iteration 4 Complete!

# ══════════════════════════════════════════════════════════════════
# PHASE 4: Sprint中变更 (BMad Official *correct-course)
# ══════════════════════════════════════════════════════════════════

# 开发过程中发现需要技术转向
User: "@sm *correct-course 发现认证需要OAuth而非JWT"

SM Agent:
⏳ Analyzing impact...
✅ Generated: sprint-change-proposal-20251119.md
```

#### Natural Language Commands

**Planning Orchestrator** (Phase 2):
- `"Start iteration N for [goal]"` - Initialize
- `"Validate current iteration"` - Run validation
- `"Finalize iteration N"` - Complete, create Git tag
- `"Status report"` - Current state
- `"Rollback to iteration N"` - Emergency rollback
- `"Compare iterations M and N"` - Review changes

**Iteration Validator** (Phase 2):
- `"Initialize Iteration N"` - Create snapshot
- `"Validate current changes"` - Check breaking changes
- `"Compare [spec] v1.0.0 vs current"` - OpenAPI diff

---

### 5. Helper System - 按需加载的详细文档架构

**核心价值**: 将15k+ tokens的详细操作指南从会话启动延迟到实际需要时加载，实现**50-70%上下文窗口节省**。

**设计原则**:

| 机制 | 内容类型 | 加载时机 | 目的 |
|------|---------|---------|------|
| devLoadAlwaysFiles | 架构约束 | 每会话自动 | 保证正确性 |
| Helper System | 操作指南 | 按需引用 | 保证效率 |

**helpers.md内容** (716行, ~15k tokens):
- Section 1: 14 Agents完整规格 (250行)
- Section 2-3: 颜色系统/8步循环 (115行)
- Section 4-5: 技术验证/架构详解 (160行)
- Section 6: 项目结构资源 (120行)

**使用方式**:
```bash
# Story开发时引用架构
开发者: "@helpers.md#Section-5-技术架构详解 我需要了解4层Python架构"

# Code Review时引用检查清单
QA: "@helpers.md#Section-4-技术验证检查清单 这段代码是否符合零幻觉开发规则？"
```

**为什么不是可有可无**:
1. BMad官方core-config.yaml定义节省70-85% tokens
2. 包含14个Agents完整规格等**必须存在**的信息
3. 大多数会话只需10-30%内容，全量加载浪费token
4. 200k窗口中15k = 7.5%，多轮会话累积显著

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
User: "@planning-orchestrator Start iteration for cross-Epic refactoring"

Orchestrator:
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
| **Phase 4** | Contract Testing | Validate code against specs | ⏳ 计划中 (tests/contract/ 未创建) |

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
- Contract Testing尚未实现

---

### 8. Supporting Infrastructure

#### YAML Status Tracking

**Purpose**: Maintain Epic/Story completion status across sessions

**File**: `.bmad-core/data/canvas-project-status.yaml`

**Loaded**: Session start (via `.claude/hooks/session-start-load-status.ps1`)

#### devLoadAlwaysFiles

**Purpose**: Dev Agent auto-loads architecture docs as read-only context

**Config**: `.bmad-core/core-config.yaml`

```yaml
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md
  - docs/architecture/project-structure.md
  - CANVAS_ERROR_LOG.md
```

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
- [ ] Contract Testing (⏳ 计划中 - tests/contract/ 未创建)
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
