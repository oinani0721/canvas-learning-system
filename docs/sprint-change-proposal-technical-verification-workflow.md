# Sprint Change Proposal: Technical Verification Workflow

**Proposal ID**: SCP-2025-11-11-001
**Date**: 2025-11-11
**Status**: Pending Approval
**Priority**: High
**Affected Epics**: Epic 11-18 (Canvas Learning System - Obsidian Native Migration)

---

## Executive Summary

### Problem Statement
当前PRD和Story开发过程中存在技术"幻觉"问题，即开发者在编写技术文档时可能假设某些API、参数或架构模式存在，但实际上并未验证官方文档。这导致：
- ❌ Story开发时发现PRD中的API不存在
- ❌ 集成时发现架构模式不可行
- ❌ 返工和延期风险增加

### Proposed Solution
建立**Technical Verification Workflow**，要求所有技术细节在PRD和Story中必须有权威文档支撑。采用**Context7 + Claude Code Skills混合方案**：
- ✅ 已有Skills的技术栈（LangGraph, Graphiti, Obsidian Canvas）通过Skills查询
- ✅ 未有Skills的技术栈（FastAPI, Neo4j）通过Context7查询
- ✅ 所有技术决策必须在文档中标注来源

### Expected Outcomes
- ✅ **消除技术幻觉**: 100%技术细节可追溯到官方文档
- ✅ **加速Story开发**: 开发前已有完整技术参考
- ✅ **降低返工风险**: PRD阶段就确保技术可行性
- ✅ **提升文档质量**: 文档引用规范化

---

## Section 1: 变更概述

### 1.1 需要修改的文档

| 文档 | 修改类型 | 优先级 | 工作量 |
|------|---------|--------|--------|
| PRD v1.1.1 | 新增章节 | P0 | 2小时 |
| `.bmad-core/checklists/technical-verification-checklist.md` | 新建 | P0 | ✅ 已完成 |
| `CLAUDE.md` (Project Context) | 补充说明 | P1 | 1小时 |
| `.bmad-core/tasks/develop-story.md` | 修改流程 | P1 | 1小时 |
| `.bmad-core/tasks/write-prd.md` | 修改流程 | P1 | 1小时 |

### 1.2 影响范围

**直接影响**:
- Epic 11-18的所有未开发Story
- 当前PRD v1.1.1需要补充技术栈章节

**间接影响**:
- 未来所有PRD和Story的编写流程
- BMad工作流的标准化升级

---

## Section 2: 具体修改建议

### 2.1 PRD v1.1.1 修改

**文件位置**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`

**插入位置**: 在"## Section 2: Technical Architecture"之后

**新增内容**:

```markdown
## Section 2.5: Required Skills & Documentation Sources

### Purpose
本章节列出项目所有技术栈的官方文档查询方式，确保Story开发时有准确的技术参考，避免技术"幻觉"。

### Technology Stack Documentation Matrix

| Epic | 技术栈 | 版本 | 查询方式 | Library ID / Skill Path | Snippets/Pages |
|------|--------|------|---------|------------------------|----------------|
| **Epic 11: FastAPI Backend** |
| 11 | FastAPI | Latest | Context7 | `/websites/fastapi_tiangolo` | 22,734 snippets |
| 11 | Python | 3.11+ | Context7 | `/python/cpython` | (TBD) |
| 11 | Pydantic | 2.x | Context7 | `/pydantic/pydantic` | (TBD) |
| **Epic 12: LangGraph Agent System** |
| 12 | LangGraph | Latest | **Skill** | `.claude/skills/langgraph/` | 952 pages |
| 12 | Graphiti | Latest | **Skill** | `.claude/skills/graphiti/` | Complete docs |
| 12 | LangChain | Latest | Context7 | `/langchain-ai/langchain` | (TBD) |
| **Epic 13: Obsidian Plugin** |
| 13 | Obsidian Canvas API | Latest | **Skill** | `.claude/skills/obsidian-canvas/` | Complete docs |
| 13 | TypeScript | 5.x | Context7 | `/microsoft/typescript` | (TBD) |
| 13 | Obsidian Plugin API | Latest | **Skill** | `.claude/skills/obsidian-canvas/` | Included |
| **Epic 14: Neo4j Data Layer** |
| 14 | Neo4j Cypher | 2.5 | Context7 | `/websites/neo4j_cypher-manual_25` | 2,032 snippets |
| 14 | Neo4j Operations | Current | Context7 | `/websites/neo4j_operations-manual-current` | 4,940 snippets |
| 14 | Neo4j Python Driver | Latest | Context7 | `/neo4j/neo4j-python-driver` | 148 snippets |

### Story Development Protocol

#### Before Starting Any Story

**Step 1: Identify Required Documentation**
根据Story涉及的Epic，从上表找到对应的技术栈。

**Step 2: Activate Skills or Query Context7**

**For Epic 11 (FastAPI Backend)**:
```bash
# 使用Context7 MCP查询FastAPI文档
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="dependency injection"  # 根据Story内容调整
)
```

**For Epic 12 (LangGraph Agent System)**:
```bash
# 激活相关Skills
@langgraph
@graphiti

# Skills会自动加载，可直接查询SKILL.md和references/
```

**For Epic 13 (Obsidian Plugin)**:
```bash
# 激活Obsidian Canvas Skill
@obsidian-canvas
```

**For Epic 14 (Neo4j Data Layer)**:
```bash
# 查询Neo4j文档
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/neo4j_cypher-manual_25",
    topic="pattern matching"
)
```

**Step 3: Verify API and Parameters**
参考 `.bmad-core/checklists/technical-verification-checklist.md` 进行完整验证。

### Documentation Quality Standards

每个Story必须包含：
- ✅ **Required Skills**: 列出需要激活的Skills
- ✅ **Context7 Queries**: 列出已查询的Library IDs
- ✅ **API Verification**: 关键API都有文档来源标注
- ✅ **Code Examples**: 复制官方示例并标注来源

**示例标注格式**:
```python
# Verified from LangGraph Skill (SKILL.md:226-230)
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model,
    tools=[search_tool, calculator_tool],
    state_modifier="You are a helpful assistant."  # ✅ Parameter verified
)
```

### Known Technical Limitations

#### LangGraph Agent System (Epic 12)
- ⚠️ **Memory System Complexity**: 三层记忆系统集成需要额外验证
- ⚠️ **Streaming Support**: 确认LangGraph Streaming API与Obsidian集成可行性
- 📖 **Reference**: See LangGraph Skill references/llms-full.md

#### Neo4j Integration (Epic 14)
- ⚠️ **Performance**: 大规模知识图谱查询性能需要基准测试
- ⚠️ **Cypher Version**: 确认使用Cypher 2.5语法
- 📖 **Reference**: Context7 `/websites/neo4j_cypher-manual_25`

### Updates and Maintenance

本章节应随项目进展更新：
- 🔄 **新增技术栈**: 添加到上表并确定查询方式
- 🔄 **版本升级**: 更新版本号和Library ID
- 🔄 **Skills补充**: 新生成的Skills及时补充到表中
```

---

### 2.2 CLAUDE.md (Project Context) 修改

**文件位置**: `C:/Users/ROG/托福/CLAUDE.md`

**插入位置**: 在"## 📐 技术架构"章节之后

**新增内容**:

```markdown
## 🔍 技术验证流程 (Technical Verification Workflow)

### 核心原则
**"所有技术细节必须可追溯到官方文档"**

### Skills 系统

项目使用**Claude Code Skills**提供离线技术文档访问：

| Skill | 位置 | 内容 |
|-------|------|------|
| langgraph | `.claude/skills/langgraph/` | 952页LangGraph完整文档 |
| graphiti | `.claude/skills/graphiti/` | Graphiti知识图谱框架文档 |
| obsidian-canvas | `.claude/skills/obsidian-canvas/` | Obsidian Canvas插件开发文档 |

**激活方式**: 在对话中使用 `@skill-name` (例如: `@langgraph`)

### Context7 MCP 集成

未生成Skills的技术栈通过**Context7 MCP**查询：

| 技术栈 | Library ID | Snippets |
|--------|-----------|----------|
| FastAPI | `/websites/fastapi_tiangolo` | 22,734 |
| Neo4j Cypher | `/websites/neo4j_cypher-manual_25` | 2,032 |
| Neo4j Operations | `/websites/neo4j_operations-manual-current` | 4,940 |

**查询方式**:
```bash
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="your-topic",
    tokens=5000
)
```

### Story开发前检查清单

在开发任何Story前，必须完成：
1. ✅ 识别涉及的技术栈
2. ✅ 激活相关Skills或查询Context7
3. ✅ 验证所有API和参数
4. ✅ 标注文档来源

**详细清单**: 参见 `.bmad-core/checklists/technical-verification-checklist.md`
```

---

### 2.3 BMad Tasks 修改

#### 2.3.1 `write-prd.md` 修改

**文件位置**: `.bmad-core/tasks/write-prd.md`

**在"Research and Analysis"步骤后添加**:

```markdown
### Step 3.5: Technical Verification

**Goal**: 确保PRD中所有技术细节都有官方文档支撑

**Checklist**:
1. [ ] 列出所有涉及的技术栈和版本
2. [ ] 为每个技术栈确定查询方式（Skill或Context7）
3. [ ] 验证所有API、参数、架构模式
4. [ ] 在PRD中新增"Required Skills & Documentation Sources"章节
5. [ ] 标注关键API的文档来源

**Tools**:
- `.bmad-core/checklists/technical-verification-checklist.md`
- Claude Code Skills: `@skill-name`
- Context7 MCP: `mcp__context7-mcp__*`

**Deliverable**:
- ✅ PRD包含完整的技术栈文档索引
- ✅ 关键代码示例都有来源标注
```

#### 2.3.2 `develop-story.md` 修改

**文件位置**: `.bmad-core/tasks/develop-story.md`

**在"Story Analysis"步骤后添加**:

```markdown
### Step 2.5: Documentation Preparation

**Goal**: 在编写代码前准备好所有技术文档

**Checklist**:
1. [ ] 从PRD"Required Skills & Documentation Sources"章节找到对应技术栈
2. [ ] 激活所有需要的Skills
3. [ ] 查询所有需要的Context7 Library IDs
4. [ ] 验证Story中使用的API是否存在
5. [ ] 找到至少1个官方示例

**Quick Reference**:
```bash
# Epic 11: FastAPI
mcp__context7-mcp__get-library-docs("/websites/fastapi_tiangolo", topic="...")

# Epic 12: LangGraph/Graphiti
@langgraph @graphiti

# Epic 13: Obsidian
@obsidian-canvas

# Epic 14: Neo4j
mcp__context7-mcp__get-library-docs("/websites/neo4j_cypher-manual_25", topic="...")
```

**Quality Gate**:
- ⚠️ **不允许继续**: 如果Story中使用的API无法在文档中找到
- ✅ **可以继续**: 所有API都有文档支撑，并在Story中标注来源
```

---

## Section 3: 技术栈覆盖现状

### 3.1 已验证的技术栈

| 技术栈 | 验证方式 | 结果 | 备注 |
|--------|---------|------|------|
| LangGraph | Skill | ✅ 完整 | 952页文档，`create_react_agent`的`state_modifier`参数已验证 |
| Graphiti | Skill | ✅ 完整 | 知识图谱完整API文档 |
| Obsidian Canvas | Skill | ✅ 完整 | Canvas插件开发完整文档 |
| FastAPI | Context7 | ✅ 可用 | 22,734 snippets，覆盖全面 |
| Neo4j Cypher | Context7 | ✅ 可用 | 2,032 snippets，Cypher 2.5语法 |
| Neo4j Operations | Context7 | ✅ 可用 | 4,940 snippets，运维完整文档 |

### 3.2 Skill Seeker尝试记录

**尝试生成FastAPI和Neo4j Skills**:
- ❌ **FastAPI**: 抓取超时（17500秒 ≈ 5小时）
- ❌ **Neo4j**: 估算超时（300秒）

**原因分析**:
- 文档网站规模巨大
- 可能存在反爬虫机制
- Skill Seeker当前限制无法处理

**决策**: 采用Context7作为替代方案，满足技术验证需求

---

## Section 4: 实施计划

### 4.1 优先级和时间线

| 阶段 | 任务 | 负责人 | 预计时间 | 截止日期 |
|------|------|--------|---------|---------|
| **Phase 1: 核心文档更新** (P0) |
| 1.1 | PRD新增Section 2.5 | PM Agent | 2小时 | D+1 |
| 1.2 | 验证技术验证清单可用性 | Dev Agent | 1小时 | D+1 |
| **Phase 2: BMad流程集成** (P1) |
| 2.1 | 修改`write-prd.md` | SM Agent | 1小时 | D+2 |
| 2.2 | 修改`develop-story.md` | SM Agent | 1小时 | D+2 |
| 2.3 | 更新`CLAUDE.md` | PM Agent | 1小时 | D+2 |
| **Phase 3: 培训和推广** (P2) |
| 3.1 | 团队培训会议 | All | 2小时 | D+3 |
| 3.2 | 编写使用示例 | Dev Agent | 2小时 | D+3 |

**总计工作量**: 10小时
**完成时间**: 3个工作日

### 4.2 验收标准

**Phase 1完成标准**:
- ✅ PRD v1.1.1包含完整的技术栈文档索引
- ✅ 技术验证清单可被实际使用
- ✅ Epic 11-18的技术栈都已映射到查询方式

**Phase 2完成标准**:
- ✅ BMad tasks包含技术验证步骤
- ✅ `CLAUDE.md`更新Skills和Context7使用说明
- ✅ 新Story开发必须通过技术验证

**Phase 3完成标准**:
- ✅ 团队所有成员理解新流程
- ✅ 至少1个Story使用新流程开发并成功验证

---

## Section 5: 风险评估

### 5.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Context7 MCP不可用 | 低 | 高 | • 已验证Context7可用<br>• 核心技术栈有Skills备份 |
| Skills文档过时 | 中 | 中 | • 定期更新Skills<br>• 优先使用Context7最新文档 |
| 技术栈新增未覆盖 | 中 | 低 | • 流程中包含新技术栈识别<br>• 及时补充到文档索引 |

### 5.2 流程风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 开发者不遵守流程 | 中 | 高 | • 代码审查时检查文档来源<br>• BMad tasks强制技术验证步骤 |
| 验证时间过长 | 低 | 中 | • Skills提供快速离线查询<br>• Context7响应快速（<5秒） |
| 文档查询学习曲线 | 中 | 低 | • 提供培训和示例<br>• CLAUDE.md包含快速参考 |

### 5.3 项目风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Epic 11-18延期 | 低 | 中 | • PRD验证前置，减少返工<br>• 验证时间已计入估算 |
| Story返工增加 | 低 | 高 | • 这正是本提案要避免的<br>• 前期验证降低返工风险 |

---

## Section 6: 成功指标 (KPIs)

### 6.1 质量指标
- 🎯 **技术幻觉率**: 0% (目标: Story开发时无未验证API)
- 🎯 **文档覆盖率**: 100% (目标: 所有技术栈都有查询方式)
- 🎯 **来源标注率**: ≥80% (目标: 关键API都有文档来源)

### 6.2 效率指标
- 🎯 **PRD验证时间**: ≤2小时/Epic (技术验证)
- 🎯 **Story验证时间**: ≤30分钟/Story
- 🎯 **返工率**: <5% (因技术问题返工的Story比例)

### 6.3 流程指标
- 🎯 **流程遵守率**: 100% (所有新Story都执行技术验证)
- 🎯 **Skills激活率**: ≥90% (Story开发前激活了Skills)
- 🎯 **Context7查询率**: ≥80% (使用Context7查询FastAPI/Neo4j)

---

## Section 7: 批准和签署

### 7.1 批准流程
1. **用户审阅**: 审阅本提案并提供反馈
2. **修改**: 根据反馈调整提案
3. **最终批准**: 用户确认实施
4. **执行**: 按Phase 1-3顺序实施

### 7.2 待批准决策

**Decision 1**: 是否采用Context7 + Skills混合方案？
- ✅ **推荐**: 是 (已验证可行性)
- ❌ **备选**: 纯Context7方案
- ❌ **备选**: 等待Skill Seeker优化

**Decision 2**: 是否强制要求文档来源标注？
- ✅ **推荐**: 关键API必须标注
- ⚠️ **备选**: 仅建议标注，不强制

**Decision 3**: 技术验证清单是否作为Quality Gate？
- ✅ **推荐**: 是 (未通过不能继续Story开发)
- ⚠️ **备选**: 仅作为指南，不强制

### 7.3 签署栏

**准备者**:
- Name: Claude (PM Agent)
- Date: 2025-11-11
- Signature: _________________

**批准者**:
- Name: [用户名]
- Date: __________
- Signature: _________________
- Decision: ☐ 批准 ☐ 需修改 ☐ 拒绝

**备注**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

## Appendix A: Context7 Library IDs完整清单

### Python生态
- **FastAPI**: `/websites/fastapi_tiangolo` (22,734 snippets, Trust Score: 9)
- **Pydantic**: `/pydantic/pydantic` (Trust Score: 9.9)
- **SQLAlchemy**: `/sqlalchemy/sqlalchemy`
- **Python Core**: `/python/cpython`

### LLM框架
- **LangChain**: `/langchain-ai/langchain`
- **LangGraph**: （使用Skill: `.claude/skills/langgraph/`）
- **Graphiti**: （使用Skill: `.claude/skills/graphiti/`）

### 数据库
- **Neo4j Cypher Manual**: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- **Neo4j Operations Manual**: `/websites/neo4j_operations-manual-current` (4,940 snippets)
- **Neo4j Python Driver**: `/neo4j/neo4j-python-driver` (148 snippets, Trust Score: 8.8)

### 前端
- **TypeScript**: `/microsoft/typescript`
- **React**: `/facebook/react`
- **Obsidian API**: （使用Skill: `.claude/skills/obsidian-canvas/`）

### 如何查找新Library ID
```bash
# 1. 解析库名到Library ID
mcp__context7-mcp__resolve-library-id(libraryName="your-library")

# 2. 获取文档
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/org/project",
    topic="your-topic",
    tokens=5000
)
```

---

## Appendix B: 技术验证清单摘要

完整清单见：`.bmad-core/checklists/technical-verification-checklist.md`

**快速检查（5分钟）**:
- [ ] 列出技术栈
- [ ] 确定查询方式（Skill or Context7）
- [ ] 激活Skills或查询Context7

**完整验证（30分钟）**:
- [ ] API签名验证
- [ ] 参数类型验证
- [ ] 找到官方示例
- [ ] 标注文档来源
- [ ] 检查版本兼容性

---

## Document Metadata

**Created**: 2025-11-11
**Last Modified**: 2025-11-11
**Version**: 1.0
**Related Documents**:
- PRD v1.1.1: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
- Technical Verification Checklist: `.bmad-core/checklists/technical-verification-checklist.md`
- Project Context: `CLAUDE.md`

**Change Log**:
- 2025-11-11 v1.0: Initial proposal created based on Correct Course analysis
