<!-- Powered by BMAD™ Core -->

# Create Next Story Task

## Purpose

To identify the next logical story based on project progress and epic definitions, and then to prepare a comprehensive, self-contained, and actionable story file using the `Story Template`. This task ensures the story is enriched with all necessary technical context, requirements, and acceptance criteria, making it ready for efficient implementation by a Developer Agent with minimal need for additional research or finding its own context.

## SEQUENTIAL Task Execution (Do not proceed until current Task is complete)

### 0. Load Core Configuration and Check Workflow

- Load `.bmad-core/core-config.yaml` from the project root
- If the file does not exist, HALT and inform the user: "core-config.yaml not found. This file is required for story creation. You can either: 1) Copy it from GITHUB bmad-core/core-config.yaml and configure it for your project OR 2) Run the BMad installer against your project to upgrade and add the file automatically. Please add and configure core-config.yaml before proceeding."
- Extract key configurations: `devStoryLocation`, `prd.*`, `architecture.*`, `workflow.*`

### 1. Identify Next Story for Preparation

#### 1.1 Locate Epic Files and Review Existing Stories

- Based on `prdSharded` from config, locate epic files (sharded location/pattern or monolithic PRD sections)
- If `devStoryLocation` has story files, load the highest `{epicNum}.{storyNum}.story.md` file
- **If highest story exists:**
  - Verify status is 'Done'. If not, alert user: "ALERT: Found incomplete story! File: {lastEpicNum}.{lastStoryNum}.story.md Status: [current status] You should fix this story first, but would you like to accept risk & override to create the next story in draft?"
  - If proceeding, select next sequential story in the current epic
  - If epic is complete, prompt user: "Epic {epicNum} Complete: All stories in Epic {epicNum} have been completed. Would you like to: 1) Begin Epic {epicNum + 1} with story 1 2) Select a specific story to work on 3) Cancel story creation"
  - **CRITICAL**: NEVER automatically skip to another epic. User MUST explicitly instruct which story to create.
- **If no story files exist:** The next story is ALWAYS 1.1 (first story of first epic)
- Announce the identified story to the user: "Identified next story for preparation: {epicNum}.{storyNum} - {Story Title}"

### 2. Gather Story Requirements and Previous Story Context

- Extract story requirements from the identified epic file
- If previous story exists, review Dev Agent Record sections for:
  - Completion Notes and Debug Log References
  - Implementation deviations and technical decisions
  - Challenges encountered and lessons learned
- Extract relevant insights that inform the current story's preparation

### 3. Gather Architecture Context

#### 3.1 Determine Architecture Reading Strategy

- **If `architectureVersion: >= v4` and `architectureSharded: true`**: Read `{architectureShardedLocation}/index.md` then follow structured reading order below
- **Else**: Use monolithic `architectureFile` for similar sections

#### 3.2 Read Architecture Documents Based on Story Type

**For ALL Stories:** tech-stack.md, unified-project-structure.md, coding-standards.md, testing-strategy.md

**For Backend/API Stories, additionally:** data-models.md, database-schema.md, backend-architecture.md, rest-api-spec.md, external-apis.md

**For Frontend/UI Stories, additionally:** frontend-architecture.md, components.md, core-workflows.md, data-models.md

**For Full-Stack Stories:** Read both Backend and Frontend sections above

#### 3.3 读取SDD规范文档 (Specification-Driven Design)

**目标**: 读取specs/目录下的SDD规范，确保Story基于API契约和数据Schema编写。

**操作步骤**:

1. **读取OpenAPI规范**:
   - 主API规范: `specs/api/canvas-api.openapi.yml`
   - Agent API规范: `specs/api/agent-api.openapi.yml`
   - 提取与当前Story相关的端点定义、请求/响应Schema

2. **读取JSON Schema**:
   - `specs/data/canvas-node.schema.json` - Canvas节点结构
   - `specs/data/canvas-edge.schema.json` - Canvas边结构
   - `specs/data/agent-response.schema.json` - Agent响应格式
   - `specs/data/scoring-response.schema.json` - 评分响应格式
   - 提取与当前Story相关的数据模型定义

3. **读取行为规范**（如适用）:
   - `specs/behavior/*.feature` - Gherkin行为定义
   - 提取相关的Given-When-Then场景

4. **创建SDD引用清单**:

   ```markdown
   **Story {epicNum}.{storyNum} SDD规范引用**:

   API端点:
   - POST /api/canvas/analyze → specs/api/canvas-api.openapi.yml#L156-L180
   - GET /api/agents/status → specs/api/agent-api.openapi.yml#L89-L102

   数据Schema:
   - CanvasNode → specs/data/canvas-node.schema.json
   - AgentResponse → specs/data/agent-response.schema.json
   ```

**质量门禁**:
- ⚠️ 如果Story涉及的API端点未在OpenAPI中定义 → **HALT**，通知Architect补充规范
- ⚠️ 如果Story涉及的数据结构未在Schema中定义 → **HALT**，通知Architect补充规范

#### 3.4 关联相关ADR (架构决策记录)

**目标**: 识别并关联影响当前Story实现的架构决策，确保Dev Agent了解"为什么这样做"。

**操作步骤**:

1. **识别Story涉及的技术栈组件**:
   - 从Epic要求和architecture文档中提取技术栈
   - 示例: LanceDB, LangGraph, Neo4j, FastAPI

2. **扫描ADR目录**:
   - 读取`docs/architecture/decisions/`目录
   - 查找与技术栈组件相关的ADR

3. **读取相关ADR并提取关键信息**:

   对于每个相关ADR，提取:
   - **决策标题**: 例如"Vector Database Selection"
   - **选择的方案**: 例如"LanceDB"
   - **关键理由**: 为什么选择这个方案
   - **对Story的影响**: 实现时需要遵循的约束

4. **创建ADR关联清单**:

   ```markdown
   **Story {epicNum}.{storyNum} ADR关联**:

   | ADR | 决策 | 对Story影响 |
   |-----|------|------------|
   | ADR-001 | 使用Obsidian Canvas | Canvas操作使用JSON格式 |
   | ADR-002 | 选择LanceDB | 向量存储使用LanceDB API |
   | ADR-003 | Agentic RAG架构 | 采用Router-Fusion-Reranking模式 |
   ```

**关键提醒**:
- 🔴 如果Story涉及的技术选型没有对应ADR → 警告用户，建议在Phase 3补充ADR
- 🔴 ADR中的"Consequences"部分对Dev Agent至关重要，必须在Dev Notes中体现

#### 3.5 Extract Story-Specific Technical Details

Extract ONLY information directly relevant to implementing the current story. Do NOT invent new libraries, patterns, or standards not in the source documents.

Extract:

- Specific data models, schemas, or structures the story will use
- API endpoints the story must implement or consume
- Component specifications for UI elements in the story
- File paths and naming conventions for new code
- Testing requirements specific to the story's features
- Security or performance considerations affecting the story

ALWAYS cite source documents: `[Source: architecture/{filename}.md#{section}]` or `[Source: specs/{path}]` or `[Source: ADR-{number}]`


### 3.6 技术文档验证（新增 v1.3 - 强制验证步骤）

⚠️ **CRITICAL QUALITY GATE**: 此步骤是强制性的，必须在填写Story Dev Notes之前完成。本步骤实施CLAUDE.md中的"零幻觉开发原则"，确保所有技术细节可追溯到官方文档。

#### 3.6.1 识别涉及的技术栈

**目标**: 从Epic要求和Architecture文档中识别Story涉及的所有技术栈组件。

**操作步骤**:
1. **分析Story需求**: 从Epic文件中提取Story的技术要求
   - 需要调用哪些外部库？(例如: LangGraph, Graphiti, FastAPI)
   - 需要操作哪些数据库？(例如: Neo4j Cypher查询)
   - 需要集成哪些API？(例如: Claude API, Obsidian Canvas API)

2. **交叉验证Architecture文档**: 对照以下Architecture文档确认技术栈
   - tech-stack.md: 核心技术栈清单
   - backend-architecture.md: 后端技术组件
   - frontend-architecture.md: 前端技术组件
   - external-apis.md: 外部API集成

3. **创建技术栈清单**: 为当前Story创建技术栈清单，格式如下：

   **Story {epicNum}.{storyNum} 技术栈清单**:
   - [ ] LangGraph (工作流编排)
   - [ ] Graphiti (知识图谱)
   - [ ] Neo4j Cypher (图数据库查询)
   - [ ] FastAPI (REST API)
   - [ ] Obsidian Canvas API (Canvas操作)

#### 3.6.2 确定文档查询方式

**目标**: 为每个技术栈组件确定最佳文档查询方式（Skill或Context7）。

**操作步骤**:
1. **检查.claude/skills目录**: 确认哪些技术栈已有本地Skill
   - langgraph: `.claude/skills/langgraph/SKILL.md` (952页)
   - graphiti: `.claude/skills/graphiti/SKILL.md`
   - obsidian-canvas: `.claude/skills/obsidian-canvas/SKILL.md`

2. **查阅CLAUDE.md的Context7映射表**: 对于没有Skill的技术栈，从CLAUDE.md中查找Context7 Library ID
   - FastAPI: `/websites/fastapi_tiangolo` (22,734 snippets)
   - Neo4j Cypher: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
   - Neo4j Operations: `/websites/neo4j_operations-manual-current` (4,940 snippets)

3. **更新技术栈清单**: 标注每个组件的查询方式

   **Story {epicNum}.{storyNum} 技术栈清单**:
   - [Skill] LangGraph → @langgraph
   - [Skill] Graphiti → @graphiti
   - [Context7] Neo4j Cypher → /websites/neo4j_cypher-manual_25
   - [Context7] FastAPI → /websites/fastapi_tiangolo
   - [Skill] Obsidian Canvas API → @obsidian-canvas

#### 3.6.3 激活Skills或查询Context7

**目标**: 为Story中涉及的每个技术栈组件实际执行文档查询，验证API存在性。

**操作步骤（Skills）**:
1. **激活Skill**: 在对话中使用 `@skill-name`
   - 示例: `@langgraph` 激活LangGraph Skill
   - 系统会加载对应的SKILL.md文档到上下文

2. **搜索关键API**: 使用Grep工具在Skill文档中搜索API

   示例: 搜索LangGraph的create_react_agent API
   Grep(pattern="create_react_agent", path=".claude/skills/langgraph/SKILL.md", output_mode="content")

3. **记录API位置**: 记录API在Skill文档中的准确位置

   ✅ LangGraph.create_react_agent → SKILL.md:226-230, Section: "Creating Agents"
   ✅ LangGraph.StateGraph → SKILL.md:445-450, Section: "State Management"

**操作步骤（Context7）**:
1. **查询Context7**: 使用Context7 MCP工具查询文档

   mcp__context7-mcp__get-library-docs(
       context7CompatibleLibraryID="/websites/fastapi_tiangolo",
       topic="dependency injection",
       tokens=5000
   )

2. **提取API信息**: 从返回的文档中提取API签名、参数、示例

3. **记录查询结果**: 记录API的文档来源

   ✅ FastAPI.Depends → Context7:/websites/fastapi_tiangolo, topic: "dependency injection"
   ✅ Neo4j MERGE语法 → Context7:/websites/neo4j_cypher-manual_25, topic: "MERGE clause"

#### 3.6.4 执行技术验证检查清单

**目标**: 使用`.bmad-core/checklists/technical-verification-checklist.md`进行系统化验证。

**操作步骤**:
1. **加载检查清单**: 读取`.bmad-core/checklists/technical-verification-checklist.md`

2. **逐项验证**: 对Story涉及的每个技术栈完成以下检查
   - [ ] Section 1: Skills系统验证
     - [ ] 1.1 识别Story涉及的技术栈
     - [ ] 1.2 检查本地Skills可用性
     - [ ] 1.3 激活相关Skills
   - [ ] Section 2: Context7 MCP验证
     - [ ] 2.1 识别需要Context7查询的技术栈
     - [ ] 2.2 确认Library ID映射
     - [ ] 2.3 执行Context7查询
   - [ ] Section 3: API验证
     - [ ] 3.1 验证所有API存在性
     - [ ] 3.2 确认参数名和类型
     - [ ] 3.3 检查版本兼容性
   - [ ] Section 4: 代码示例收集
     - [ ] 4.1 从Skills收集官方代码示例
     - [ ] 4.2 从Context7提取代码片段
     - [ ] 4.3 验证示例可运行性
   - [ ] Section 5: 文档来源标注
     - [ ] 5.1 为每个API准备来源标注
     - [ ] 5.2 确认标注格式正确
   - [ ] Section 6: 质量门禁
     - [ ] 6.1 所有核心API已验证
     - [ ] 6.2 文档来源标注完整
     - [ ] 6.3 无未验证的技术假设

3. **记录检查清单结果**: 在Story文件的Dev Notes中记录验证结果摘要

#### 3.6.5 收集官方代码示例

**目标**: 从Skills/Context7中收集官方代码示例，为Dev Agent提供参考实现。

**操作步骤**:
1. **从Skills收集示例**: 搜索Skill文档中的代码示例

   示例: 从LangGraph Skill提取create_react_agent示例
   Grep(pattern="```python.*create_react_agent", path=".claude/skills/langgraph/SKILL.md", multiline=True)

2. **从Context7收集示例**: 在Context7查询中指定topic="code examples"

   mcp__context7-mcp__get-library-docs(
       context7CompatibleLibraryID="/websites/fastapi_tiangolo",
       topic="dependency injection examples",
       tokens=3000
   )

3. **整理代码示例库**: 为Story创建代码示例库，包含：
   - ✅ 文档来源标注
   - ✅ 完整的import语句
   - ✅ 必要的参数说明
   - ✅ 版本兼容性说明（如有）

4. **验证示例完整性**: 确保每个示例都可以被Dev Agent直接引用

#### 3.6.6 Quality Gate 检查

**目标**: 在继续填写Story之前，确认技术验证达到质量标准。

**通过标准**:
1. ✅ **技术栈清单完整性**: 所有技术栈组件已识别并分类（Skill/Context7）
2. ✅ **文档查询完成度**: 所有技术栈已执行Skills激活或Context7查询
3. ✅ **API验证覆盖率**: 核心API 100%验证，辅助API ≥80%验证
4. ✅ **代码示例充足性**: 每个核心技术栈至少1个官方代码示例
5. ✅ **来源标注准备度**: 所有API的文档来源标注已准备就绪

**不通过处理**:
- ⚠️ 如果任何核心API未验证 → **HALT**，返回Step 3.6.3重新查询
- ⚠️ 如果代码示例不足 → **HALT**，返回Step 3.6.5收集更多示例
- ⚠️ 如果来源标注缺失 → **HALT**，补充标注后再继续

**通过后行动**:
- ✅ 记录Quality Gate通过时间戳
- ✅ 生成技术验证摘要报告（见下一步）
- ✅ 继续Step 5：Populate Story Template

#### 3.6.7 在Story中记录验证结果

**目标**: 将技术验证结果系统化地记录到Story文件的Dev Notes中，为Dev Agent提供完整上下文。

**记录内容结构**:

在Story文件的`Dev Notes`section中，添加以下子章节：

## Dev Notes

### 📋 技术验证报告 (Step 3.6)

**验证完成时间**: {timestamp}
**验证执行人**: SM Agent
**Quality Gate状态**: ✅ PASSED

#### 技术栈清单

| 技术栈 | 查询方式 | 验证状态 | 文档位置 |
|--------|---------|---------|----------|
| LangGraph | Skill | ✅ 已验证 | SKILL.md:226-450 |
| Graphiti | Skill | ✅ 已验证 | SKILL.md:156-320 |
| Neo4j Cypher | Context7 | ✅ 已验证 | /websites/neo4j_cypher-manual_25 |
| FastAPI | Context7 | ✅ 已验证 | /websites/fastapi_tiangolo |

#### 核心API验证结果

**LangGraph APIs**:
- ✅ `create_react_agent` → Verified from LangGraph Skill (SKILL.md:226-230)
  - 参数: `model`, `tools`, `state_schema`
  - 返回: `CompiledGraph`
- ✅ `StateGraph` → Verified from LangGraph Skill (SKILL.md:445-450)
  - 参数: `state_schema`
  - 方法: `add_node()`, `add_edge()`, `compile()`

**Graphiti APIs**:
- ✅ `Graphiti` → Verified from Graphiti Skill (SKILL.md:156-162)
- ✅ `EntityEdge` → Verified from Graphiti Skill (SKILL.md:234-240)

**Neo4j Cypher**:
- ✅ `MERGE` 语法 → Verified from Context7:/websites/neo4j_cypher-manual_25
  - 语法: `MERGE (n:Label {property: value})`
  - 语义: 不存在则创建，存在则匹配

**FastAPI**:
- ✅ `Depends` → Verified from Context7:/websites/fastapi_tiangolo
  - 用途: 依赖注入

#### 代码示例库

[在此粘贴Step 3.5.5收集的代码示例]

#### 技术约束和注意事项

**版本约束**:
- LangGraph: ≥0.2.0 (SKILL.md基于v0.2.14)
- Neo4j: ≥5.0 (Cypher查询语法)
- FastAPI: ≥0.100.0 (异步支持)

**已知限制**:
- [从Architecture文档或Skill中提取的技术限制]

**安全考虑**:
- [从Architecture文档中提取的安全要求]

### [继续原有的Dev Notes其他章节...]

**记录后验证**:
1. ✅ 所有API都有文档来源标注
2. ✅ 代码示例已添加到Story
3. ✅ 技术约束已明确说明
4. ✅ Dev Agent可以直接引用这些信息进行开发

**关键提醒**:
- 🔴 Dev Agent开发时必须严格遵循此技术验证报告中的API和参数
- 🔴 任何偏离都必须先重新执行Step 3.5验证流程
- 🔴 代码标注必须使用此报告中的文档来源

---

⚠️ **IMPORTANT**: Step 3.6完成后，继续Step 4: Verify Project Structure Alignment


### 4. Verify Project Structure Alignment

- Cross-reference story requirements with Project Structure Guide from `docs/architecture/unified-project-structure.md`
- Ensure file paths, component locations, or module names align with defined structures
- Document any structural conflicts in "Project Structure Notes" section within the story draft

### 5. Populate Story Template with Full Context

- Create new story file: `{devStoryLocation}/{epicNum}.{storyNum}.story.md` using Story Template
- Fill in basic story information: Title, Status (Draft), Story statement, Acceptance Criteria from Epic
- **`Dev Notes` section (CRITICAL):**
  - CRITICAL: This section MUST contain ONLY information extracted from architecture documents, SDD specs, and ADRs. NEVER invent or assume technical details.
  - Include ALL relevant technical details from Steps 2-3, organized by category:
    - **Previous Story Insights**: Key learnings from previous story
    - **SDD规范参考 (必填)**: OpenAPI端点、JSON Schema引用、行为规范 [Source: specs/{path}]
    - **ADR决策关联 (必填)**: 影响Story实现的架构决策及其约束 [Source: ADR-{number}]
    - **Data Models**: Specific schemas, validation rules, relationships [with source references]
    - **API Specifications**: Endpoint details, request/response formats, auth requirements [with source references]
    - **Component Specifications**: UI component details, props, state management [with source references]
    - **File Locations**: Exact paths where new code should be created based on project structure
    - **Testing Requirements**: Specific test cases or strategies from testing-strategy.md
    - **Technical Constraints**: Version requirements, performance considerations, security rules
  - Every technical detail MUST include its source reference: `[Source: architecture/{filename}.md#{section}]` or `[Source: specs/{path}]` or `[Source: ADR-{number}]`
  - If information for a category is not found in the architecture docs, explicitly state: "No specific guidance found in architecture docs"
  - ⚠️ **质量门禁**: 如果SDD规范参考或ADR决策关联为空，Story不能标记为Draft
- **`Tasks / Subtasks` section:**
  - Generate detailed, sequential list of technical tasks based ONLY on: Epic Requirements, Story AC, Reviewed Architecture Information
  - Each task must reference relevant architecture documentation
  - Include unit testing as explicit subtasks based on the Testing Strategy
  - Link tasks to ACs where applicable (e.g., `Task 1 (AC: 1, 3)`)
- Add notes on project structure alignment or discrepancies found in Step 4

### 6. Story Draft Completion and Review

- Review all sections for completeness and accuracy
- Verify all source references are included for technical details
- Ensure tasks align with both epic requirements and architecture constraints
- Update status to "Draft" and save the story file
- Execute `.bmad-core/tasks/execute-checklist` `.bmad-core/checklists/story-draft-checklist`
- Provide summary to user including:
  - Story created: `{devStoryLocation}/{epicNum}.{storyNum}.story.md`
  - Status: Draft
  - Key technical components included from architecture docs
  - Any deviations or conflicts noted between epic and architecture
  - Checklist Results
  - Next steps: For Complex stories, suggest the user carefully review the story draft and also optionally have the PO run the task `.bmad-core/tasks/validate-next-story`
