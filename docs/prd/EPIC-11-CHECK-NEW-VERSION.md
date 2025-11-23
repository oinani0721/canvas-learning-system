---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial PRD with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 0
  fr_count: 0
  nfr_count: 0
---

# Canvas Learning System - Obsidian原生插件迁移PRD

**文档版本**: v1.1.7 (3层记忆技术栈勘误修正版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-12 (**NEW**: 3层记忆技术栈勘误修正 - 确保100%代码一致性)

## ⚠️ v1.1.7 3层记忆技术栈勘误修正 (2025-11-12) **必读**

**核心变更**: 修正PRD中3层记忆系统技术栈描述,确保与实际代码实现100%一致,消除AI幻觉风险

**关键修正**:
1. **Temporal Memory技术栈**: TimescaleDB → **Neo4j** (代码实际使用DirectNeo4jStorage)
2. **Semantic Memory技术栈**: Qdrant → **ChromaDB + CUDA** (代码实际使用ChromaDB + PyTorch CUDA加速)
3. **Graphiti技术栈**: Neo4j ✅ (正确,无需修改)

**代码证据**:
- `memory_system/temporal_memory_manager.py` Line 61-64: `DirectNeo4jStorage(uri='bolt://localhost:7687', database='ultrathink')`
- `mcp_memory_client.py` Line 263-280: `chromadb.PersistentClient()` + `device="cuda"` (Line 197-207)
- `memory_system/graphiti_storage.py` Line 27-82: `Graphiti(uri='bolt://localhost:7687')`

**影响范围**:
- **FR3数据流向图** (Line 425, 429): 已修正技术栈名称
- **无新Story或Epic影响**: 纯文档勘误,不影响实施计划

**优先级**: Critical - P0 (技术栈错误会导致Story开发时AI产生幻觉,实现错误的技术选型)

**修正依据**: 深度代码审计 (learning_analyzer.py, mcp_memory_client.py, temporal_memory_manager.py, graphiti_storage.py)

---

## ⚠️ v1.1.6 艾宾浩斯系统3层记忆数据整合 (2025-11-12) **必读**

**核心变更**: 艾宾浩斯复习系统全面整合3层记忆系统数据源，实现100%真实数据驱动，消除所有模拟数据

**关键问题解决**:
1. **数据源单一问题**: 原系统仅依赖Canvas评分≥60作为唯一数据源 → 整合Temporal/Graphiti/Semantic三层记忆
2. **参数默认值问题**: Py-FSRS使用默认17参数（相当于模拟数据） → 从真实行为数据动态优化参数
3. **行为监控缺失**: 无法主动发现需要复习的概念 → 新增触发点4（行为监控自动触发）

**新增内容**:
1. **FR3数据流向重构**: 添加3层记忆系统作为数据源（FR3 Lines 386-426）
2. **FR3.1触发点4**: 行为监控触发机制（FR3.1 Lines 475-530）
3. **FR3.2聚合逻辑升级**: 多维度优先级计算（FSRS 40% + 行为30% + 关系20% + 交互10%）（FR3.2 Lines 534-668）
4. **FR3.6参数优化函数**: 从真实行为数据优化FSRS 17参数（FR3.6 Lines 930-1080）
5. **4个新工具定义** (Section 3 Lines 1896-2211):
   - `query_temporal_learning_behavior`: 查询学习行为数据
   - `query_graphiti_concept_network`: 查询概念关系网络
   - `query_semantic_document_interactions`: 查询文档交互数据
   - `track_learning_behavior`: 记录学习行为
6. **记忆系统派遣矩阵更新**: 添加艾宾浩斯复习触发行（Section 3 Line 3671）
7. **Epic影响**:
   - Epic 11: +1 Story (11.7 - 3层记忆查询API)
   - Epic 12: Story 12.2扩展（工具实现）
   - Epic 14: +2 Stories (14.9数据集成 + 14.10行为监控) + 修改14.1/14.2/14.4

**优先级**: Must Have - P0（核心需求缺失，影响系统数据真实性）

**实施时间**: +4-5周 (Phase 1 MVP延长到12-16周)

**相关文档**: `docs/SPRINT_CHANGE_PROPOSAL_SCP-002_艾宾浩斯系统数据源整合.md`

---

## ⚠️ v1.1.5 智能并行处理UI需求补全 (2025-11-12) **必读**

**核心变更**: 新增FR2.1（智能并行处理UI），扩展Epic 13（Story 13.8）和Epic 11（Story 11.6），暴露Epic 10后端实现

**新增内容**:
1. **FR2.1 智能并行处理UI**: Canvas工具栏"智能批量处理"按钮，4步交互流程（分组预览→执行→进度监控→结果展示）
2. **Story 13.8 UI实现**: 7天工作量，5个Task（工具栏按钮、分组预览模态框、实时进度、结果预览、错误处理）
3. **Story 11.6 API端点**: 4个REST API + 1个WebSocket，集成AsyncExecutionEngine和智能调度器
4. **Epic影响**: Epic 13 (7→8 Stories), Epic 11 (5→6 Stories), 总时间+1周

**技术基础**: Epic 10的完整后端实现（1400+行代码）已验证，8倍性能提升，TF-IDF+K-Means智能分组

**优先级**: Must Have - P0（后端已实现，只需UI暴露）

**相关文档**: `docs/SPRINT_CHANGE_PROPOSAL_SCP-001_智能并行处理UI需求补全.md`

## ⚠️ v1.1.4 艾宾浩斯复习系统设计补全 (2025-11-11) **必读**

**核心变更**: FR3艾宾浩斯复习系统设计补全，新增5个关键设计元素，Epic 14调整为"迁移+UI集成"方案

**补全内容**:
1. **FR3.1 数据采集触发机制**: 明确何时、由谁触发add_concept_for_review()，错误处理机制
2. **FR3.2 复习推送聚合逻辑**: 从概念级别→Canvas级别的聚合算法，优先级排序
3. **FR3.3 Obsidian UI设计Mockup**: 侧边栏复习面板完整设计（布局、交互、样式）
4. **FR3.4 Py-FSRS集成细节**: Card schema、17参数配置、调用时机、性能预期
5. **FR3.5 数据一致性保证**: Canvas评分 ↔ 复习数据双向同步机制，冲突解决策略

**算法升级**: 采用**Py-FSRS算法**（相比经典艾宾浩斯遗忘曲线准确性提升20-30%）

**Epic 14调整**: 从"新开发"改为"迁移+UI集成"（基于已有ebbinghaus_review.py 870行代码，2025-01-22实现）

---

## ⚠️ v1.1.3 LangGraph记忆系统集成 (2025-11-11)

**核心变更**: 新增Section 3.6 "LangGraph记忆系统集成设计"，明确LangGraph Checkpointer与3层业务记忆系统的职责边界、触发时机、一致性保证和故障处理机制

**强制要求** (Quality Gate):
- 🚫 **未验证的API不能进入Story实施**
- 🚫 **所有技术细节必须有官方文档支撑**
- ✅ **每个关键API必须标注文档来源**

**SM/Dev Agent必读**:
- 📖 **Section 3.5** (本PRD第1541行起): 技术栈映射和验证协议
- 📖 **CLAUDE.md**: 技术验证流程章节（自动加载）
- 📖 **create-next-story.md Step 3.5**: 技术验证强制步骤
- 📖 **Checklist**: `.bmad-core/checklists/technical-verification-checklist.md`

**Quick Start** (在Story开发前):
```bash
# 1. 识别Epic涉及的技术栈（查看Section 3.5表格）
# 2. 激活相关Skills（如果是Skill类型）
@langgraph      # Epic 12
@graphiti       # Epic 12
@obsidian-canvas # Epic 13

# 3. 查询Context7（如果是Context7类型）
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",  # Epic 11
    topic="your-topic"
)

# 4. 验证每个API（参见technical-verification-checklist.md）
```

**为什么重要**:
- ❌ **之前**: Story开发时假设API存在 → 实施后发现不存在 → 返工重构
- ✅ **现在**: Story开发前验证API → 确认存在且参数正确 → 直接实施

**示例**: 参见 `docs/examples/story-12-1-verification-demo.md` (Epic 12实例)

---

**文档类型**: Brownfield Enhancement PRD
**项目类型**: 架构迁移 + 功能增强

---

## 🔧 v1.1.1 技术细节完善摘要

**修复原因**: 用户反馈PRD缺失3个关键技术实现细节

**修复内容**:
1. ✅ **需求1: Obsidian文件引用路径问题修复**
   - 将`create_md_file`改为`create_md_file_for_canvas`，新增`canvas_path`参数
   - 使用Vault相对路径而非`./相对路径`，解决历史上反复出现的文件引用失败问题
   - 返回包含`vault_path`的完整字典，确保Canvas FILE节点可正确引用

2. ✅ **需求2: 3层记忆系统调度时机明确**
   - 新增4个记忆存储工具：`store_to_graphiti_memory`, `store_to_temporal_memory`, `store_to_semantic_memory`, `query_graphiti_for_verification`
   - 在Story 12.2中新增"记忆系统调度时机矩阵"，明确何时调度哪些记忆层
   - 提供完整代码集成示例

3. ✅ **需求3: 智能检验白板生成机制增强**
   - 新增`query_graphiti_for_verification`工具，在生成检验白板前查询Graphiti获取上下文
   - 查询内容包括：相关概念、历史盲区、概念关系
   - 生成的检验问题基于Graphiti上下文，关联度高，能切到重点（如教授审问）

**变更范围**:
- 工具定义: Lines 696-1011 (修改`create_md_file` + 新增4个工具)
- shared_tools列表: Lines 1030-1042 (新增4个工具)
- Story 12.2: Lines 1545-1611 (扩展记忆系统调度矩阵 + 代码示例)

**验收标准**:
- ✅ Obsidian可正常打开所有Agent生成的.md文件（无引用失败）
- ✅ 所有Canvas操作正确触发记忆系统存储（按调度矩阵）
- ✅ 检验白板生成的问题具有高关联度（基于Graphiti上下文）

详见: **本PRD Lines 696-1011（工具定义）和Lines 1545-1611（Story 12.2）**

---

## 🔄 v1.1 架构调整摘要

**调整原因**: 用户反馈要求快速节点生成和实时反馈

**关键变更**:
1. **保留canvas-orchestrator作为Layer 3智能路由层** (原有核心优势)
2. **新增LangGraph Supervisor作为Layer 4执行引擎** (并发调度)
3. **所有Agent配备write_to_canvas等工具** (分布式写入,0.5-1秒响应)
4. **FileLock并发安全机制** (跨平台文件锁)
5. **WriteHistory回滚机制** (操作历史追溯和恢复)

**性能提升**: 首个节点出现时间从8-10秒降至0.5-1秒 (8-16倍提升 ⚡)

详见: **附录C - 架构调整说明**

---

## 📋 文档摘要

### 项目概述

**项目名称**: Canvas Learning System - Obsidian Native Plugin Migration
**项目代号**: CLSV2-OB-NATIVE
**项目类型**: Brownfield架构迁移 + 新功能增强

**核心目标**:
将现有的Canvas学习系统从**Python CLI + Claude Code Task调用**架构迁移到**Obsidian原生插件 + FastAPI后端 + LangGraph多Agent编排**架构,同时新增艾宾浩斯复习提醒、检验白板进度追踪、跨Canvas关联学习三大核心功能。

**核心原则**: **功能完整性优先** - 100%保留现有功能,0%功能回退

---

## 🎯 Section 1: 项目分析

### 1.1 现有项目概览

#### 系统架构 (当前)

```
用户在Obsidian中打开Canvas
    ↓
切换到Claude Code窗口
    ↓
手动输入命令: "@离散数学.canvas 基础拆解'逆否命题'"
    ↓
Claude Code调用Task tool → 调用12个Sub-agent
    ↓
Sub-agent返回JSON结果
    ↓
canvas_utils.py写入Canvas文件
    ↓
用户切回Obsidian查看结果
```

**痛点**:
- ❌ 需要频繁切换窗口 (Obsidian ↔ Claude Code)
- ❌ 命令行输入门槛高,需要记忆语法
- ❌ 无法实时看到Agent执行进度
- ❌ 缺少今日复习提醒功能
- ❌ 检验白板无法追踪原白板节点还原进度
- ❌ 跨Canvas学习需手动记忆关联关系

#### 核心资产

| 组件 | 规模 | 状态 | 价值 |
|------|------|------|------|
| canvas_utils.py | ~150KB, 3层架构 | ✅ 稳定 | 核心业务逻辑 |
| 12个Sub-agent | `.claude/agents/*.md` | ✅ 验证可用 | Agent定义 |
| Epic 10.2异步引擎 | 8倍性能提升 | ✅ 完成 | 性能优势 |
| 测试套件 | 360+测试, 99.2%通过率 | ✅ 高质量 | 质量保证 |
| Graphiti集成 | Neo4j + KnowledgeGraphLayer | ✅ 完成 | 知识图谱基础 |
| EbbinghausReviewSystem | Py-FSRS算法 | ✅ 已实现 | 复习算法 |

**保留策略**: 所有核心资产100%保留,仅迁移接口层

---

### 1.2 迁移范围评估

#### 需要迁移的部分

```
❌ CLI命令接口               → ✅ Obsidian Plugin命令
❌ Claude Code Task调用      → ✅ LangGraph Supervisor调度
❌ 手动切换窗口              → ✅ Obsidian内原生操作
```

#### 需要保留的部分

```
✅ canvas_utils.py (3层架构)    → FastAPI后端继续使用
✅ 12个Agent定义               → LangGraph节点封装
✅ Epic 10.2异步执行引擎       → 性能优势保留
✅ Graphiti知识图谱            → 跨Canvas关联基础
✅ EbbinghausReviewSystem      → 复习系统核心
```

#### 需要新增的功能

```
🆕 艾宾浩斯复习面板            → 今日复习提醒
🆕 检验白板进度追踪            → 原白板节点还原状态
🆕 跨Canvas关联UI              → 手动配置教材-习题关联
🆕 实时进度显示                → WebSocket推送Agent状态
```

---


## 🔍 Section 1.X: 技术验证协议 (Mandatory Technical Verification Protocol)


## 1.X.1 核心原则

### "Zero Hallucination Policy - 零幻觉政策"

本项目对技术实现采用**学术论文级别的引用标准**。任何技术细节（API调用、参数、返回值、配置项）都必须可追溯到官方文档，禁止基于"常识"或"经验"进行假设性实现。

**违反此协议的Story将被标记为FAILED，必须重做。**

---

### 质量目标

| 质量维度 | 目标 | 衡量方式 | 负责人 |
|---------|------|---------|--------|
| **Bug率（API误用）** | ↓50% | Epic 11-16 Bug追踪 | QA Agent |
| **返工率（技术假设错误）** | ↓70% | Story重做次数统计 | PM Agent |
| **Code Review效率** | ↑30% | Review时间对比 | SM Agent |
| **代码可维护性** | ↑40% | 文档引用注释覆盖率 | Dev Agent |

---

## 1.X.2 技术栈文档访问矩阵

| 技术栈 | 访问方式 | Library ID / Skill Path | 代码片段数 | Epic依赖 | 查询响应时间 |
|--------|---------|------------------------|-----------|---------|-------------|
| **FastAPI** | Context7 MCP | `/websites/fastapi_tiangolo` | 22,734 | Epic 11 | <5秒 |
| **Neo4j Cypher** | Context7 MCP | `/websites/neo4j_cypher-manual_25` | 2,032 | Epic 15-16 | <5秒 |
| **Neo4j Operations** | Context7 MCP | `/websites/neo4j_operations-manual-current` | 4,940 | Epic 15-16 | <5秒 |
| **LangGraph** | Local Skill | `@langgraph` | 952页完整文档 | Epic 12 | 即时 |
| **Graphiti** | Local Skill | `@graphiti` | 完整框架文档 | Epic 12 | 即时 |
| **Obsidian Canvas** | Local Skill | `@obsidian-canvas` | Canvas API文档 | Epic 13 | 即时 |

### 访问方式说明

#### Context7 MCP查询
**命令格式**:
```python
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="dependency injection async Depends",
    tokens=3000
)
```

#### Local Skill激活
**命令格式**:
```
@langgraph  # 在Claude Code对话中直接使用
```

---

## 1.X.3 强制性查询触发点 (Mandatory Verification Triggers)

### 🔴 Level 1: SM Agent编写Story时 (CRITICAL)

**触发条件**: 编写任何包含技术实现细节的Story

**强制操作**:
1. **识别技术栈**: 列出Story涉及的所有技术（FastAPI、Neo4j、LangGraph等）
2. **查询官方文档**:
   - 使用Context7查询相关API/配置
   - 或激活本地Skill (`@langgraph`, `@obsidian-canvas`)
3. **在Story中引用**: 添加"技术验证"section（见1.X.5模板）

**示例Story片段**:
```markdown
### Story 11.2: 实现Canvas节点查询API

## 技术验证 (Technical Verification) 🔍

### 涉及技术栈
- [x] FastAPI

### 已完成的文档查询
1. **查询1**: FastAPI - "APIRouter path operations GET method"
   - 来源: Context7 `/websites/fastapi_tiangolo`
   - 查询时间: 2025-11-13
   - 关键发现: 使用`@router.get("/path")`装饰器定义GET endpoint
   - 引用位置: AC1

2. **查询2**: FastAPI - "dependency injection async Depends"
   - 来源: Context7 `/websites/fastapi_tiangolo`
   - 关键发现: 使用`Annotated[Type, Depends(func)]`语法进行依赖注入
   - 引用位置: AC2

### 技术债务声明
- [x] 本Story中所有技术实现均已查询官方文档验证
- [x] 无任何基于"常识"或"经验"的假设性实现
- [x] 所有API调用均可追溯到文档引用

**SM Agent签名**: _________
**验证时间**: 2025-11-13

## Acceptance Criteria

### AC1: 定义GET endpoint
**技术依据**: Context7 FastAPI - "APIRouter GET operation"

```python
# 来源: Context7 /websites/fastapi_tiangolo - "GET path operation"
@router.get("/api/canvas/{canvas_id}/nodes")
async def get_canvas_nodes(canvas_id: str):
    ...
```

### AC2: 实现依赖注入
**技术依据**: Context7 FastAPI - "Dependency Injection"

```python
# 来源: Context7 /websites/fastapi_tiangolo - "Depends with Annotated"
async def get_canvas_nodes(
    canvas_id: str,
    canvas_service: Annotated[CanvasService, Depends(get_canvas_service)]
):
    ...
```
```

---

### 🔴 Level 2: Dev Agent开发实现时 (CRITICAL)

**触发条件**: 编写任何包含框架API调用的代码

**强制操作 - 实时查询流程**:

```python
# ❌ 错误示例 - 直接凭记忆写代码
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 100):
    return {"items": []}

# ✅ 正确流程：
# Step 1: 查询Context7确认语法
#   查询命令: mcp__context7-mcp__get-library-docs(
#              context7CompatibleLibraryID="/websites/fastapi_tiangolo",
#              topic="GET endpoint async function syntax",
#              tokens=3000
#            )
# Step 2: 查询Context7确认参数验证
#   查询主题: "query parameters validation"
# Step 3: 根据查询结果编写代码并添加注释引用

@app.get("/items/")  # Context7: fastapi_tiangolo - "GET path operation"
async def read_items(
    skip: int = 0,  # Context7: "query parameter with default value"
    limit: int = 100
):
    # Context7验证: async endpoint返回dict自动转JSON
    return {"items": []}
```

---

### 🤔 UltraThink检查点 (开发时强制执行)

**每当编写涉及框架API的代码时，必须执行以下思考流程**:

```
🤔 UltraThink检查点：
1. 我是否100%确定这个API的用法？
   ❌ 如果否 → 立即查询Context7/Skill

2. 参数名称、类型、默认值是否正确？
   ❌ 如果不确定 → 立即查询Context7/Skill

3. 返回值类型是否符合框架要求？
   ❌ 如果不确定 → 立即查询Context7/Skill

4. 是否有更好的官方推荐写法？
   ✅ 查询Context7获取best practices

5. 这个写法是"创新"还是"标准"？
   ⚠️ 如果是"创新" → 必须提供官方文档支持
```

**强制暂停点**: 如果任何一个问题的答案是"不确定"，**必须立即停止编码，先查询文档**。

---

### 🟡 Level 3: Code Review时 (IMPORTANT)

**触发条件**: 审查任何技术实现代码

**强制操作**:
1. **检查Story**: 确认Story包含完整的"技术验证"section
2. **验证API调用**: 逐一核对代码中API调用是否与文档一致
3. **交叉验证**: 使用Context7交叉验证可疑用法
4. **要求证据**: 如发现可疑用法，要求Dev Agent提供文档引用

**Code Review检查清单**:
- [ ] Story包含"技术验证"section且记录完整
- [ ] 代码中所有框架API调用均与官方文档一致
- [ ] 关键代码行包含文档来源注释
- [ ] 无明显的"凭经验"或"创新"写法
- [ ] 参数类型、默认值、返回值均正确
- [ ] 配置项符合官方推荐

---

## 1.X.4 文档查询工作流 (Documentation Query Workflow)

### 方式1: 使用Context7 MCP查询FastAPI/Neo4j

**场景**: 需要实现FastAPI的依赖注入

**查询命令**:
```python
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="dependency injection async Depends",
    tokens=3000
)
```

**记录查询结果** (在Story/代码注释中):
```markdown
**技术验证**:
- 技术栈: FastAPI
- 查询主题: "dependency injection async Depends"
- 来源: Context7 `/websites/fastapi_tiangolo`
- 验证时间: 2025-11-13
- 关键发现: 使用`Annotated[Type, Depends(func)]`语法
```

**查询主题建议** (FastAPI):
- "dependency injection async Depends"
- "APIRouter path operations"
- "request body validation Pydantic"
- "response model serialization"
- "middleware async"
- "background tasks"
- "WebSocket endpoint"

**查询主题建议** (Neo4j):
- "MATCH query basic syntax"
- "CREATE node relationship"
- "WHERE clause filtering"
- "RETURN projection"
- "transaction management"
- "index optimization"

---

### 方式2: 使用本地Skill查询LangGraph/Obsidian

**场景**: 需要实现LangGraph的StateGraph

**激活Skill**:
```
@langgraph
```

**查询内容**:
"如何创建StateGraph并添加节点"

**记录查询结果**:
```markdown
**技术验证**:
- 技术栈: LangGraph
- 查询主题: "StateGraph node creation"
- 来源: Local Skill `@langgraph`
- 验证代码示例: SKILL.md Line 24-48
```

---

## 1.X.5 Story模板更新 - 新增验证部分

**所有Epic 11/12/13/15/16的Story必须包含以下section**:

```markdown
## 技术验证 (Technical Verification) 🔍

### 涉及技术栈
- [ ] FastAPI
- [ ] Neo4j
- [ ] LangGraph
- [ ] Obsidian Canvas API
- [ ] Graphiti
- [ ] 其他: __________

### 已完成的文档查询
1. **查询1**: [技术栈] - [查询主题]
   - 来源: Context7 / Skill
   - Library ID / Skill名称: __________
   - 关键发现: [API/配置/参数]
   - 引用位置: [AC编号]

2. **查询2**: [技术栈] - [查询主题]
   - 来源: __________
   - 关键发现: __________
   - 引用位置: __________

### 技术债务声明
- [ ] 本Story中所有技术实现均已查询官方文档验证
- [ ] 无任何基于"常识"或"经验"的假设性实现
- [ ] 所有API调用均可追溯到文档引用

**SM Agent签名**: _________
**验证时间**: _________
```

---

## 1.X.6 Definition of Done (DoD) 更新

**所有技术Story的DoD新增以下条目**:

```markdown
## Definition of Done (Enhanced)

### 技术验证要求 (NEW - MANDATORY) ⚠️
- [ ] **文档查询记录完整**: Story包含完整的"技术验证"section
- [ ] **API调用已验证**: 所有框架API调用均通过Context7/Skill确认
- [ ] **参数类型正确**: 所有函数参数、返回值类型与官方文档一致
- [ ] **配置项已确认**: 所有配置项（数据库连接、中间件等）符合官方推荐
- [ ] **代码注释包含引用**: 关键代码行包含文档来源注释（Context7/Skill引用）

### 传统DoD (保留)
- [ ] 代码通过所有单元测试
- [ ] 代码通过集成测试
- [ ] 代码符合项目编码规范（PEP 8 / TypeScript规范）
- [ ] PR已通过Code Review
- [ ] 文档已更新（如有必要）
- [ ] 无已知的Critical/High severity bugs
```

---

## 1.X.7 违反协议的处理流程

| 违规类型 | 严重程度 | 处理措施 | 责任人 |
|---------|---------|---------|--------|
| **Story缺少"技术验证"section** | 🔴 Critical | Story标记为BLOCKED，要求SM Agent补充 | SM Agent |
| **代码中API调用与官方文档不符** | 🔴 Critical | PR被拒绝，Dev Agent必须修正并提供文档引用 | Dev Agent |
| **使用了未经验证的"创新"写法** | 🟡 High | 必须提供官方文档支持或回退到标准写法 | Dev Agent |
| **文档查询记录不完整** | 🟡 Medium | 要求补充完整的查询记录和时间戳 | SM Agent |
| **代码注释缺少文档引用** | 🟢 Low | Code Review时要求补充注释 | Dev Agent |

### 升级路径
1. **首次违规**: 警告并要求修正
2. **再次违规**: Story/PR标记为FAILED，需要重做
3. **反复违规**: 暂停Epic执行，进行流程培训

---

## 1.X.8 成功案例示例

**参考文档**: `docs/examples/story-12-1-verification-demo.md`

该示例展示了：
- ✅ 如何在Story中记录技术查询
- ✅ 如何在代码注释中引用文档
- ✅ 如何通过UltraThink检查点避免幻觉
- ✅ 完整的AC编写规范（含技术依据）

**强烈建议**: 所有SM Agent和Dev Agent在开始Epic 11前阅读该示例。

---

## 1.X.9 开发流程检查清单

### SM Agent编写Story前必查清单
- [ ] 已识别Story涉及的所有技术栈
- [ ] 已查询Context7/Skill获取相关API文档
- [ ] 已在Story中添加"技术验证"section
- [ ] 已在每个AC中引用具体的API/配置/参数
- [ ] 已记录所有查询的时间戳和来源
- [ ] 已签名确认Story的技术债务声明

### Dev Agent开发代码前必查清单
- [ ] 已阅读Story的"技术验证"section
- [ ] 已激活相关Skill或准备好Context7查询命令
- [ ] 已确认代码中每个API调用的官方写法
- [ ] 已准备在代码关键位置添加文档来源注释
- [ ] 已理解UltraThink检查点流程

### Code Review必查清单
- [ ] Story包含完整的"技术验证"section
- [ ] 代码中所有API调用均与文档一致
- [ ] 关键代码行包含文档引用注释
- [ ] 无明显的"凭经验"或"创新"写法
- [ ] 参数类型、默认值、返回值正确
- [ ] 配置项符合官方推荐

---

## 1.X.10 质量监控与持续改进

### 监控指标

| 指标 | 目标值 | 监控周期 | 责任人 |
|------|--------|---------|--------|
| **Story技术验证完整率** | 100% | 每个Story | SM Agent |
| **API误用Bug数** | <2/Epic | Epic结束时 | QA Agent |
| **文档引用覆盖率** | >80% | Code Review时 | Dev Agent |
| **返工Story数** | <1/Epic | Epic结束时 | PM Agent |

### 持续改进机制

#### 1. Epic回顾 (Epic结束时)
- 统计技术验证相关的Bug和返工
- 识别常见的文档查询盲点
- 更新查询主题建议列表

#### 2. 流程优化 (每2个Epic)
- 收集SM/Dev Agent的反馈
- 优化Story模板和检查清单
- 补充成功案例和最佳实践

#### 3. 培训更新 (发现新问题时)
- 更新`docs/examples/`中的示例
- 在Epic 0中添加新的验证测试
- 共享经验教训到团队

---

## 1.X.11 附录：快速参考

### Context7查询速查表

| 需求 | Context7 Library ID | 推荐查询主题 | tokens |
|------|---------------------|-------------|--------|
| **FastAPI路由** | `/websites/fastapi_tiangolo` | "APIRouter path operations" | 3000 |
| **FastAPI依赖注入** | `/websites/fastapi_tiangolo` | "dependency injection Depends" | 3000 |
| **FastAPI请求验证** | `/websites/fastapi_tiangolo` | "request body validation Pydantic" | 3000 |
| **FastAPI异步操作** | `/websites/fastapi_tiangolo` | "async operations background tasks" | 3000 |
| **FastAPI响应模型** | `/websites/fastapi_tiangolo` | "response model serialization" | 3000 |
| **FastAPI中间件** | `/websites/fastapi_tiangolo` | "middleware async CORS" | 3000 |
| **FastAPI WebSocket** | `/websites/fastapi_tiangolo` | "WebSocket endpoint" | 3000 |
| **Neo4j查询语法** | `/websites/neo4j_cypher-manual_25` | "MATCH query WHERE clause" | 3000 |
| **Neo4j关系创建** | `/websites/neo4j_cypher-manual_25` | "CREATE relationship" | 3000 |
| **Neo4j事务管理** | `/websites/neo4j_operations-manual-current` | "transaction management" | 3000 |
| **Neo4j索引优化** | `/websites/neo4j_operations-manual-current` | "index performance" | 3000 |

### Local Skill快速激活

| 需求 | Skill名称 | 查询建议 | 响应时间 |
|------|----------|---------|---------|
| **LangGraph状态图** | `@langgraph` | "StateGraph creation" | 即时 |
| **LangGraph节点添加** | `@langgraph` | "add node to graph" | 即时 |
| **LangGraph边连接** | `@langgraph` | "add edge between nodes" | 即时 |
| **Graphiti知识图谱** | `@graphiti` | "knowledge graph operations" | 即时 |
| **Obsidian Canvas节点** | `@obsidian-canvas` | "Canvas API node creation" | 即时 |
| **Obsidian Canvas连接** | `@obsidian-canvas` | "Canvas API edge creation" | 即时 |

---

## 📊 Section 1.X总结

### 核心价值
1. **零幻觉**: 所有技术实现可追溯到官方文档
2. **学术标准**: 类似论文引用的严谨性
3. **质量提升**: Bug率↓50%，返工率↓70%
4. **可维护性**: 代码注释包含文档来源

### 强制执行点
1. **SM Agent写Story**: 必须包含"技术验证"section
2. **Dev Agent开发**: 必须通过UltraThink检查点
3. **Code Review**: 必须验证文档引用完整性

### 成功标准
- ✅ Story技术验证完整率 = 100%
- ✅ API误用Bug数 < 2/Epic
- ✅ 文档引用覆盖率 > 80%
- ✅ 返工Story数 < 1/Epic

---

**文档状态**: ✅ 完成
**下一步**: 整合到主PRD或作为独立附件引用
**相关文档**:
- Epic 0详情: `docs/prd/EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md`
- 示例Story: `docs/examples/story-12-1-verification-demo.md`
- Sprint Change Proposal: `docs/SPRINT-CHANGE-PROPOSAL-2025-11-13.md`

---

## 📐 Section 2: 需求定义

### 2.1 功能需求 (Functional Requirements)

#### FR1: Obsidian原生Canvas操作 (Must Have - P0)

**描述**: 用户在Obsidian内完成所有Canvas学习操作,无需切换到Claude Code

**用户故事**:
```
作为学习者
我希望在Obsidian内完成拆解、评分、生成解释等所有操作
这样我可以保持专注,不被窗口切换打断思路
```

**验收标准**:
- ✅ 右键Canvas节点 → 显示"基础拆解"、"深度拆解"、"评分"等菜单
- ✅ 快捷键支持 (如 Ctrl+Shift+D 拆解)
- ✅ 命令面板支持 (Ctrl+P → "Canvas学习: 基础拆解")
- ✅ 操作结果实时显示,无需刷新
- ✅ 错误提示友好,有重试机制

---

#### FR2: 12个Agent功能100%保留 (Must Have - P0)

**描述**: 所有现有Agent功能完整迁移,0%功能回退

**验收标准**:

| Agent | 现有功能 | 迁移后实现 |
|-------|---------|-----------|
| basic-decomposition | 生成3-7个引导问题 | ✅ 配备write_to_canvas工具 |
| deep-decomposition | 生成深度检验问题 | ✅ 配备write_to_canvas工具 |
| scoring-agent | 4维评分,颜色流转 | ✅ 配备write_to_canvas工具 |
| oral-explanation | 生成800-1200词口语化解释 | ✅ 配备create_md_file工具 |
| clarification-path | 生成1500+词澄清文档 | ✅ 配备create_md_file工具 |
| comparison-table | 生成对比表 | ✅ 配备create_md_file工具 |
| memory-anchor | 生成记忆锚点 | ✅ 配备create_md_file工具 |
| four-level-explanation | 生成4层次解释 | ✅ 配备create_md_file工具 |
| example-teaching | 生成例题教程 | ✅ 配备create_md_file工具 |
| verification-question | 生成检验问题 | ✅ 配备write_to_canvas工具 |
| canvas-orchestrator | 主控Agent,自然语言理解 | ✅ **保留为Layer 3智能路由层** |
| (新增) LangGraph Supervisor | N/A | ✅ Layer 4执行引擎,并发调度 |

**性能要求**:
- ✅ 响应时间不低于现有系统
- ✅ Epic 10.2的8倍性能提升必须保留
- ✅ 并发执行能力不退化

---
#### FR2.1: 智能并行处理UI (Must Have - P0)

**背景**: Epic 10智能并行处理系统的完整后端实现已完成（IntelligentParallelCommandHandler + AsyncExecutionEngine + IntelligentParallelScheduler），但缺少Obsidian Plugin的UI暴露。当前仅能通过CLI命令`/intelligent-parallel`使用。

**描述**: 在Obsidian Canvas工具栏添加"智能批量处理"按钮，用户可一键触发对当前Canvas的所有黄色节点进行智能分组和Agent批量调用。

**核心能力**:
- ✅ **智能分组**: TF-IDF向量化 + K-Means聚类，自动将语义相近的黄色节点分组
- ✅ **Agent推荐**: 基于节点内容关键词，自动推荐最合适的6个解释Agent
- ✅ **异步并发**: AsyncExecutionEngine支持最多12个Agent并发执行（Epic 10.2的8倍性能提升）
- ✅ **实时进度**: WebSocket推送任务进度、完成状态和错误信息
- ✅ **3层Canvas结构**: 黄色节点 → 蓝色TEXT节点（说明） → File节点（.md文档）

**UI交互流程**:

**Step 1: 工具栏按钮**
```
┌─────────────────────────────────────────┐
│ Canvas工具栏                             │
│ [🎯 拆解] [📊 评分] [📝 解释] [⚡ 智能批量处理] │
└─────────────────────────────────────────┘
```

**Step 2: 智能分组预览模态框**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 分组预览                       │
├────────────────────────────────────────────┤
│ 检测到 12 个黄色节点，智能分组为 4 组:        │
│                                            │
│ 📊 Group 1: 对比类概念 (3节点)              │
│   推荐Agent: comparison-table              │
│   • 逆否命题 vs 否命题                      │
│   • 充分条件 vs 必要条件                    │
│   优先级: High                             │
│                                            │
│ 🔍 Group 2: 复杂概念澄清 (4节点)            │
│   推荐Agent: clarification-path            │
│   优先级: High                             │
│                                            │
│ [ 修改分组 ] [ 取消 ] [ 开始处理 (预计2分钟) ] │
└────────────────────────────────────────────┘
```

**Step 3: 实时进度显示**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 执行中                        │
├────────────────────────────────────────────┤
│ 总进度: ████████░░░░░░░░ 8/12 (67%)        │
│                                            │
│ ✅ Group 1 (comparison-table): 已完成       │
│    ├─ 逆否命题 vs 否命题.md (3.2KB)         │
│    └─ 充分条件 vs 必要条件.md (2.8KB)       │
│                                            │
│ ⏳ Group 2 (clarification-path): 进行中 (2/4)│
│                                            │
│ [ 暂停 ] [ 取消 ] [ 最小化 ]                │
└────────────────────────────────────────────┘
```

**Step 4: 完成结果预览**
```
┌────────────────────────────────────────────┐
│ 智能并行处理 - 完成                          │
├────────────────────────────────────────────┤
│ ✅ 成功处理 11/12 个节点                     │
│ ❌ 1个节点失败                               │
│ ⏱️ 总耗时: 2分15秒                          │
│                                            │
│ 生成文档:                                   │
│ • 3个对比表 (📊)                            │
│ • 4个澄清路径 (🔍)                          │
│                                            │
│ [ 查看错误日志 ] [ 关闭 ]                   │
└────────────────────────────────────────────┘
```

**验收标准**:
- ✅ Canvas工具栏显示"智能批量处理"按钮（图标：⚡）
- ✅ 点击按钮触发智能分组分析（<3秒完成）
- ✅ 分组预览模态框正确显示分组结果
- ✅ 实时进度显示（WebSocket推送，延迟<500ms）
- ✅ 完成结果预览（成功/失败统计）
- ✅ Canvas自动更新（3层结构正确）
- ✅ 错误处理完善（无黄色节点提示、Agent失败不中断其他）

**关联Epic/Story**:
- Epic 11: Story 11.6（4个REST API + 1个WebSocket）
- Epic 13: Story 13.8（UI实现，7天）

**优先级**: Must Have - P0（已有完整后端实现，只缺UI暴露）

**时间估算**: +1周（UI开发 + API集成 + E2E测试



#### FR3: 艾宾浩斯复习提醒系统 (Must Have - P0)

**描述**: 每日打开Obsidian自动显示今日应复习的Canvas白板

**用户故事**:
```
作为学习者
我希望每天打开Obsidian时看到"今日应复习:离散数学、线性代数"
这样我可以及时复习,避免遗忘
```

**数据流向** (v1.1.6更新 - 3层记忆系统数据整合):
```
┌──────────────────────────────────────────────────────────────────┐
│ 数据源 (Data Sources)                                            │
├──────────────────────────────────────────────────────────────────┤
│ 1. Canvas节点评分 (≥60分) → 触发添加概念到复习队列              │
│ 2. Temporal Memory (Neo4j) → 学习行为数据                        │
│    - 复习频率、间隔时间、正确率趋势                             │
│ 3. Graphiti Knowledge Graph (Neo4j) → 概念关系网络              │
│    - 前置概念掌握度、关联概念难度、知识图谱路径                 │
│ 4. Semantic Memory (ChromaDB + CUDA) → 文档交互数据             │
│    - 查阅频率、停留时间、相关文档访问模式                       │
└──────────────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────────┐
        │ EbbinghausReviewSystem            │
        │ - add_concept_for_review()        │
        │ - optimize_fsrs_parameters()      │ ← 新增: 参数优化
        └───────────────────────────────────┘
                        ↓
        ┌───────────────────────────────────┐
        │ ebbinghaus_review_data.json       │
        │ (Py-FSRS Card对象)                │
        └───────────────────────────────────┘
                        ↓
        ┌───────────────────────────────────┐
        │ Py-FSRS算法                       │
        │ - 使用从真实行为优化的17参数      │ ← 新增: 真实参数
        │ - 计算下次复习时间                │
        └───────────────────────────────────┘
                        ↓
        ┌───────────────────────────────────┐
        │ Obsidian侧边栏"今日复习面板"     │
        └───────────────────────────────────┘
```

**v1.1.6关键变更**:
- ✅ **100%真实数据源**: 所有数据来自实际学习行为，无模拟数据
- ✅ **3层记忆系统整合**: Temporal/Graphiti/Semantic全面接入
- ✅ **动态参数优化**: FSRS 17参数从真实行为数据中计算，非默认值
- ✅ **多维度评估**: 不仅基于评分，还考虑行为模式、概念关系、文档交互

**验收标准**:
- ✅ 每日打开Obsidian自动显示复习面板
- ✅ 显示应复习的Canvas名称和到期概念数量
- ✅ 一键生成检验白板
- ✅ 复习历史可查看 (最近7天/30天)
- ✅ 复习提醒通知 (可配置开启/关闭)

---

#### FR3.1: 数据采集触发机制

**触发时机和调用者**:

```python
# 触发点1: scoring-agent评分后自动触发
# 调用者: ScoringAgentHandler (command_handlers/scoring_handler.py)
def handle_scoring_completion(canvas_file: str, node_id: str, score: int, concept: str):
    """评分完成后的回调"""
    if score >= 60:  # 达到复习阈值
        try:
            # 调用艾宾浩斯系统添加概念
            review_system = EbbinghausReviewSystem()
            review_system.add_concept_for_review(
                canvas_file=canvas_file,
                node_id=node_id,
                concept=concept,
                initial_mastery=score / 100.0  # 将评分转换为掌握度
            )
            logger.info(f"✅ 已添加概念到复习系统: {concept} (评分: {score})")
        except Exception as e:
            logger.error(f"❌ 添加概念失败: {concept}, 错误: {e}")
            # 降级策略: 记录失败日志,但不阻塞主流程
            log_review_system_error(canvas_file, node_id, concept, e)
```

**错误处理策略**:
1. **非阻塞原则**: 复习系统故障不影响评分主流程
2. **重试机制**: 失败概念记录到`review_system_errors.json`,后台定时重试
3. **降级方案**: SQLite不可用时自动切换到JSON文件存储
4. **告警机制**: 连续失败>5次时通知用户检查数据库连接

**触发点汇总**:
- ✅ **触发点1**: scoring-agent评分≥60分后自动触发
- ✅ **触发点2**: 用户手动标记概念为"需要复习" (右键菜单)
- ✅ **触发点3**: 批量导入历史Canvas节点 (数据迁移场景)
- ✅ **触发点4**: 3层记忆系统行为监控触发 (v1.1.6新增)

**触发点4详细设计** (v1.1.6):

```python
# 触发点4: 3层记忆系统行为监控触发
# 调用者: MemoryBehaviorMonitor (后台定时任务)
def monitor_and_trigger_review():
    """
    基于3层记忆系统的行为数据主动识别需要复习的概念

    触发条件:
    1. Temporal Memory检测到: 某概念>7天未访问，且历史掌握度≥60分
    2. Graphiti检测到: 前置概念已掌握，但后续概念长期未学习（知识断层）
    3. Semantic Memory检测到: 相关文档被频繁访问，但概念本身未复习（隐性需求）
    """

    # 条件1: Temporal Memory - 长期未访问的已掌握概念
    inactive_concepts = query_temporal_learning_behavior(
        filter_type="inactive_mastered",
        days_threshold=7,
        min_mastery=0.6
    )

    # 条件2: Graphiti - 知识断层检测
    knowledge_gaps = query_graphiti_concept_network(
        analysis_type="prerequisite_gap",
        min_prerequisite_mastery=0.8,
        gap_days_threshold=14
    )

    # 条件3: Semantic Memory - 隐性需求检测
    implicit_needs = query_semantic_document_interactions(
        pattern="related_doc_frequent_but_concept_inactive",
        related_access_threshold=5,
        concept_inactive_days=7
    )

    # 合并并去重
    all_concepts = set(inactive_concepts + knowledge_gaps + implicit_needs)

    # 批量添加到复习系统
    review_system = EbbinghausReviewSystem()
    for concept in all_concepts:
        review_system.add_concept_for_review(
            canvas_file=concept['canvas_file'],
            node_id=concept['node_id'],
            concept=concept['concept'],
            initial_mastery=concept.get('mastery', 0.6),
            trigger_source="behavior_monitoring"  # 标记触发来源
        )
        logger.info(f"✅ 行为监控触发复习: {concept['concept']} (来源: {concept['detection_reason']})")
```

**定时执行策略**:
- **执行频率**: 每日凌晨2:00自动执行 (用户非活跃时间)
- **执行时长**: 预期<30秒 (查询3层记忆系统 + 批量添加)
- **失败处理**: 记录日志，次日重试，不影响其他触发点

---

#### FR3.2: 复习推送聚合逻辑

**从概念级别到Canvas级别的聚合算法** (v1.1.6更新 - 3层记忆系统数据整合):

```python
def get_today_review_summary() -> List[Dict]:
    """
    聚合今日复习任务到Canvas级别 (v1.1.6 - 整合3层记忆系统数据)

    Returns:
        [
            {
                "canvas_file": "笔记库/离散数学.canvas",
                "canvas_name": "离散数学",
                "due_concepts_count": 5,
                "priority_score": 8.5,  # 0-10分
                "due_concepts": ["逆否命题", "德摩根定律", ...],
                "urgency_level": "high",  # low/medium/high/urgent
                "behavior_insights": {...},  # v1.1.6新增
                "memory_metrics": {...}      # v1.1.6新增
            },
            ...
        ]
    """
    # Step 1: 查询所有到期概念 (Py-FSRS计算到期时间)
    due_concepts = query_due_concepts(today=datetime.now())

    # Step 2: 按Canvas文件分组
    canvas_groups = defaultdict(list)
    for concept in due_concepts:
        canvas_groups[concept['canvas_file']].append(concept)

    # Step 3: 对每个Canvas，从3层记忆系统聚合数据 (v1.1.6新增)
    canvas_summary = []
    for canvas_file, concepts in canvas_groups.items():
        concept_ids = [c['node_id'] for c in concepts]

        # 3.1: Temporal Memory - 学习行为数据
        behavior_data = query_temporal_learning_behavior(
            canvas_file=canvas_file,
            concept_ids=concept_ids,
            metrics=["review_frequency", "avg_interval", "accuracy_trend"]
        )

        # 3.2: Graphiti - 概念关系网络
        network_data = query_graphiti_concept_network(
            canvas_file=canvas_file,
            concept_ids=concept_ids,
            analysis=["prerequisite_mastery", "related_difficulty", "knowledge_path"]
        )

        # 3.3: Semantic Memory - 文档交互数据
        interaction_data = query_semantic_document_interactions(
            canvas_file=canvas_file,
            concept_ids=concept_ids,
            metrics=["access_frequency", "dwell_time", "related_docs_pattern"]
        )

        # Step 4: 计算每个Canvas的优先级分数 (v1.1.6更新 - 多维度评估)
        # 优先级计算公式 (0-10分):
        # priority = FSRS权重(40%) + 行为权重(30%) + 关系权重(20%) + 交互权重(10%)

        # 4.1: FSRS基础分数 (40%)
        concept_count_score = min(len(concepts) / 5.0 * 10, 10)  # 5个概念=10分
        avg_forgetting_risk = sum(c['forgetting_risk'] for c in concepts) / len(concepts)
        max_overdue_days = max(c['overdue_days'] for c in concepts)
        overdue_score = min(max_overdue_days / 3.0 * 10, 10)  # 3天逾期=10分

        fsrs_score = (
            concept_count_score * 0.3 +
            avg_forgetting_risk * 10 * 0.5 +
            overdue_score * 0.2
        ) * 0.4  # FSRS权重40%

        # 4.2: 行为分数 (30%) - v1.1.6新增
        behavior_score = (
            (1.0 - behavior_data.get('review_frequency_normalized', 0.5)) * 10 * 0.4 +  # 复习频率低 = 高分
            (behavior_data.get('interval_deviation', 0.5)) * 10 * 0.3 +  # 间隔偏差大 = 高分
            (1.0 - behavior_data.get('accuracy_trend', 0.7)) * 10 * 0.3   # 正确率下降 = 高分
        ) * 0.3  # 行为权重30%

        # 4.3: 关系分数 (20%) - v1.1.6新增
        network_score = (
            network_data.get('prerequisite_completeness', 0.8) * 10 * 0.5 +  # 前置概念完整度
            (1.0 - network_data.get('related_difficulty_normalized', 0.5)) * 10 * 0.5  # 关联难度低 = 高分
        ) * 0.2  # 关系权重20%

        # 4.4: 交互分数 (10%) - v1.1.6新增
        interaction_score = (
            interaction_data.get('recent_access_frequency', 0.3) * 10 * 0.6 +  # 最近访问频率
            (interaction_data.get('dwell_time_normalized', 0.4)) * 10 * 0.4  # 停留时间
        ) * 0.1  # 交互权重10%

        # 4.5: 综合优先级分数
        priority_score = fsrs_score + behavior_score + network_score + interaction_score

        # 紧急程度分级
        if priority_score >= 8.0:
            urgency_level = "urgent"
        elif priority_score >= 6.0:
            urgency_level = "high"
        elif priority_score >= 4.0:
            urgency_level = "medium"
        else:
            urgency_level = "low"

        canvas_summary.append({
            "canvas_file": canvas_file,
            "canvas_name": Path(canvas_file).stem,
            "due_concepts_count": len(concepts),
            "priority_score": round(priority_score, 2),
            "due_concepts": [c['concept'] for c in concepts],
            "urgency_level": urgency_level,
            # v1.1.6新增: 行为洞察和记忆指标
            "behavior_insights": {
                "avg_review_frequency": behavior_data.get('review_frequency', 0),
                "accuracy_trend": behavior_data.get('accuracy_trend', 0),
                "last_review_days_ago": behavior_data.get('last_review_days', 0)
            },
            "memory_metrics": {
                "prerequisite_readiness": network_data.get('prerequisite_completeness', 0),
                "knowledge_path_depth": network_data.get('knowledge_path_depth', 0),
                "recent_engagement": interaction_data.get('recent_access_frequency', 0)
            }
        })

    # Step 5: 按优先级排序返回
    return sorted(canvas_summary, key=lambda x: x['priority_score'], reverse=True)
```

**v1.1.6关键改进**:
- ✅ **多维度优先级**: FSRS(40%) + 行为(30%) + 关系(20%) + 交互(10%)
- ✅ **真实数据驱动**: 所有指标来自3层记忆系统实际记录
- ✅ **智能识别需求**: 行为偏差、知识断层、隐性需求自动发现
- ✅ **可解释性**: 返回详细的行为洞察和记忆指标，用户可理解推荐原因

**推送展示规则**:
- **Urgent级别 (红色徽章)**: 优先级≥8.0,顶部展示,闪烁动画
- **High级别 (橙色徽章)**: 优先级6.0-7.9,正常展示
- **Medium/Low级别 (灰色徽章)**: 优先级<6.0,折叠展示,点击展开

---

#### FR3.3: Obsidian UI设计Mockup

**侧边栏复习面板设计**:

```
┌─────────────────────────────────────┐
│  📚 今日复习 (3个白板, 12个概念)     │ ← 标题栏
├─────────────────────────────────────┤
│  🔴 离散数学 (5个概念) [!urgent]     │ ← Canvas卡片1
│     逆否命题、德摩根定律、命题逻辑... │
│     [📝 开始复习] [⏰ 推迟1天]       │ ← 操作按钮
├─────────────────────────────────────┤
│  🟠 线性代数 (4个概念) [!high]       │ ← Canvas卡片2
│     特征向量、正交矩阵、行列式...     │
│     [📝 开始复习] [⏰ 推迟1天]       │
├─────────────────────────────────────┤
│  ⚪ 概率论 (3个概念) [medium]        │ ← Canvas卡片3 (折叠)
│     [展开查看]                       │
├─────────────────────────────────────┤
│  📊 复习统计 (本周)                  │ ← 统计面板
│     ✅ 已复习: 28个概念               │
│     📈 平均评分: 82分                │
│     🔥 连续复习: 7天                 │
├─────────────────────────────────────┤
│  ⚙️ 设置  📜 历史记录                │ ← 底部工具栏
└─────────────────────────────────────┘
```

**交互逻辑**:
1. **点击"开始复习"**: 自动调用`generate_review_canvas_file()`生成检验白板并打开
2. **点击"推迟1天"**: 调整Py-FSRS的next_review_date +1天,重新计算遗忘风险
3. **点击Canvas卡片**: 直接打开原白板文件
4. **右键菜单**: "标记为已掌握"(直接设为绿色,不再推送) / "重置复习进度"

**样式规范**:
- **字体**: Obsidian默认字体,14px
- **颜色**: 使用Obsidian主题变量 (`--text-accent`, `--background-secondary`)
- **动画**: urgent级别卡片使用`pulse`动画,period=2s
- **响应式**: 宽度<600px时自动调整为单列布局

---

#### FR3.4: Py-FSRS集成细节

**Py-FSRS Card Schema**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FSRSCard:
    """Py-FSRS记忆卡片 (基于FSRS v5算法)"""

    # 核心字段
    due: datetime  # 下次复习时间
    stability: float  # 记忆稳定性 (天数)
    difficulty: float  # 难度系数 (0.0-10.0)
    elapsed_days: int  # 距离上次复习的天数
    scheduled_days: int  # 预定复习间隔天数
    reps: int  # 复习次数
    lapses: int  # 遗忘次数
    state: str  # 状态: "New"/"Learning"/"Review"/"Relearning"
    last_review: Optional[datetime]  # 上次复习时间

    # Canvas扩展字段
    concept: str  # 概念名称
    canvas_file: str  # 所属Canvas文件
    node_id: str  # Canvas节点ID
    mastery_level: float  # 掌握度 (0.0-1.0)

# 初始化Card (用户首次评分≥60分时)
def create_initial_card(concept: str, initial_score: int) -> FSRSCard:
    """
    从Canvas评分创建初始Card

    Args:
        concept: 概念名称
        initial_score: 评分 (60-100)

    Returns:
        初始化的FSRSCard,使用FSRS默认参数
    """
    fsrs = FSRS()  # 使用默认17参数
    card = fsrs.new_card()  # 创建新卡片

    # 根据评分调整初始难度
    # 评分越高,难度越低 (更容易记住)
    difficulty_adjustment = (100 - initial_score) / 40.0  # 60分→1.0, 100分→0.0
    card.difficulty = max(1.0, min(10.0, card.difficulty + difficulty_adjustment))

    # 自定义字段
    card.concept = concept
    card.mastery_level = initial_score / 100.0

    return card
```

**Py-FSRS 17参数配置** (使用默认值,待后期调优):

```python
FSRS_PARAMETERS = {
    "w": [  # 17个权重参数 (FSRS v5默认值)
        0.4072, 1.1829, 3.1262, 15.4722, 7.2102,
        0.5316, 1.0651, 0.0234, 1.616, 0.1544,
        1.0824, 1.9813, 0.0953, 0.2975, 2.2042,
        0.2407, 2.9466
    ],
    "request_retention": 0.9,  # 目标保留率 90%
    "maximum_interval": 36500,  # 最大间隔100年
    "enable_fuzz": True  # 启用模糊化避免复习集中
}

# 创建FSRS实例
fsrs = FSRS(
    w=FSRS_PARAMETERS["w"],
    request_retention=FSRS_PARAMETERS["request_retention"],
    maximum_interval=FSRS_PARAMETERS["maximum_interval"],
    enable_fuzz=FSRS_PARAMETERS["enable_fuzz"]
)
```

**Py-FSRS调用时机**:

| 时机 | 调用方法 | 说明 |
|------|---------|------|
| 首次添加概念 | `fsrs.new_card()` | 创建初始Card,state="New" |
| 复习后更新 | `fsrs.review_card(card, rating)` | rating: 1(Again)/2(Hard)/3(Good)/4(Easy) |
| 查询到期概念 | `card.due <= datetime.now()` | 直接比较due时间 |
| 计算遗忘风险 | `fsrs.current_retrievability(card)` | 返回0.0-1.0,越低越容易忘 |

**性能预期**:
- **单次review_card()**: <5ms (纯计算,无IO)
- **批量查询1000个Card的到期状态**: <50ms (内存遍历)
- **并发安全**: 使用FileLock锁定SQLite数据库,支持多进程访问

**依赖安装**:
```bash
pip install py-fsrs==1.0.0  # 固定版本,避免API变更
```

---

#### FR3.5: 数据一致性保证机制

**双向同步场景**:

```
场景1: Canvas评分 → 复习系统
┌─────────────┐         ┌──────────────────┐
│ ScoringAgent│ ─评分─→ │ EbbinghausSystem │
│  (评分80分) │         │  (创建/更新Card) │
└─────────────┘         └──────────────────┘

场景2: 复习系统 → Canvas评分 (用户在检验白板复习后)
┌──────────────────┐         ┌─────────────┐
│ EbbinghausSystem │ ←复习─  │ 检验白板评分 │
│  (更新Card难度)  │         │  (评分75分)  │
└──────────────────┘         └─────────────┘
```

**同步策略**:

```python
class DataConsistencyManager:
    """Canvas评分 ↔ 复习数据双向同步管理器"""

    def sync_score_to_review(self, canvas_file: str, node_id: str, new_score: int):
        """
        Canvas评分更新 → 复习系统同步

        触发时机: scoring-agent评分完成后
        """
        # Step 1: 查找对应的Card
        card_id = f"{canvas_file}_{node_id}"
        card = self.review_db.get_card(card_id)

        if card is None:
            # 首次评分且≥60分,创建新Card
            if new_score >= 60:
                card = create_initial_card(concept, new_score)
                self.review_db.save_card(card)
                logger.info(f"✅ 创建新Card: {card_id}, 初始评分: {new_score}")
        else:
            # 已有Card,更新掌握度
            card.mastery_level = new_score / 100.0

            # 如果评分显著提升(+15分以上),调整Card难度
            if new_score - card.mastery_level * 100 >= 15:
                card.difficulty = max(1.0, card.difficulty - 0.5)  # 降低难度
                logger.info(f"✅ 评分提升,降低Card难度: {card_id}, 新难度: {card.difficulty}")

            self.review_db.update_card(card)

    def sync_review_to_score(self, canvas_file: str, node_id: str, review_rating: int):
        """
        检验白板复习 → 原Canvas评分同步

        触发时机: 用户在检验白板上完成复习并评分后
        """
        # Step 1: 更新Py-FSRS Card
        card_id = f"{canvas_file}_{node_id}"
        card = self.review_db.get_card(card_id)
        card, review_log = self.fsrs.review_card(card, review_rating)
        self.review_db.update_card(card)

        # Step 2: 同步更新原Canvas节点颜色
        # rating=4(Easy)或rating=3(Good)且reps≥3 → 绿色
        if review_rating == 4 or (review_rating == 3 and card.reps >= 3):
            self.canvas_operator.update_node_color(canvas_file, node_id, COLOR_GREEN)
            logger.info(f"✅ 复习达标,原Canvas节点变绿: {node_id}")

        # rating=1(Again) → 保持红色/紫色
        elif review_rating == 1:
            logger.info(f"⚠️ 复习失败,原Canvas节点保持原色: {node_id}")

    def resolve_conflict(self, canvas_file: str, node_id: str):
        """
        冲突解决策略

        冲突场景: Canvas节点被手动修改为绿色,但Card显示需要复习
        """
        canvas_color = self.canvas_operator.get_node_color(canvas_file, node_id)
        card = self.review_db.get_card(f"{canvas_file}_{node_id}")

        if canvas_color == COLOR_GREEN and card.due <= datetime.now():
            # 策略: 以Canvas为准 (用户手动标记为已掌握)
            # 将Card的due时间延后7天,避免推送
            card.due = datetime.now() + timedelta(days=7)
            self.review_db.update_card(card)
            logger.warning(f"⚠️ 冲突解决: Canvas已标绿但Card到期,延后复习: {node_id}")
```

**冲突解决优先级**:
1. **用户手动操作 > 自动同步**: 用户手动标记为绿色,则延后复习推送
2. **最新评分为准**: 同一概念在1小时内多次评分,以最新评分为准
3. **检验白板评分 > 原白板评分**: 检验白板的复习评分更能反映真实掌握情况

**一致性检查工具**:
```bash
# 定期运行一致性检查 (每周日晚上)
python -m canvas_utils.consistency_checker --canvas-dir "笔记库" --review-db "ebbinghaus_review.db"

# 输出报告:
# ✅ 一致性检查通过: 检查了150个概念, 0个冲突
# ⚠️ 发现3个冲突:
#    1. 离散数学.canvas node123 (Canvas绿色, Card到期3天) → 已自动修复
#    2. 线性代数.canvas node456 (Canvas红色, Card已掌握) → 需要手动确认
```

---

#### FR3.6: Py-FSRS参数优化函数 (v1.1.6新增)

**核心目标**: 从真实学习行为数据中动态优化Py-FSRS的17个参数，替代默认值，实现100%真实数据驱动

**问题背景**:
- Py-FSRS默认使用17个预设参数（基于通用用户群统计）
- 默认参数对个体学习特征的拟合度不高
- 使用默认参数等同于使用"模拟数据"，不符合v1.1.6的核心要求

**解决方案**:

```python
def optimize_fsrs_parameters_from_behavior() -> Dict[str, float]:
    """
    从3层记忆系统的真实行为数据中优化Py-FSRS 17参数

    数据来源:
    1. Temporal Memory: 历史复习记录（时间间隔、成功率、遗忘曲线）
    2. Graphiti: 概念难度分布、前置关系对学习效果的影响
    3. Semantic Memory: 文档交互模式与记忆保持的相关性

    Returns:
        {
            "w": [0.4, 0.6, 2.4, 5.8, ...],  # 17个优化后的FSRS参数
            "optimization_metrics": {
                "sample_size": 500,  # 用于优化的样本数量
                "rmse": 0.12,  # 预测误差
                "data_quality_score": 0.85  # 数据质量评分
            }
        }
    """

    # Step 1: 从Temporal Memory提取历史复习数据
    review_history = query_temporal_learning_behavior(
        filter_type="all_reviews",
        min_samples=100,  # 至少需要100次复习记录才能优化
        fields=["review_time", "rating", "interval", "stability", "difficulty"]
    )

    if len(review_history) < 100:
        logger.warning("⚠️ 复习样本不足(<100),使用默认FSRS参数")
        return {"w": DEFAULT_FSRS_PARAMETERS, "optimization_metrics": {"sample_size": 0}}

    # Step 2: 从Graphiti提取概念关系影响
    concept_network_influence = query_graphiti_concept_network(
        analysis_type="learning_difficulty_distribution",
        concepts=review_history['concepts']
    )

    # Step 3: 从Semantic Memory提取文档交互模式
    doc_interaction_patterns = query_semantic_document_interactions(
        pattern="review_engagement_correlation",
        concepts=review_history['concepts']
    )

    # Step 4: 准备优化数据集
    training_data = []
    for review in review_history:
        # 整合3层记忆系统数据
        concept_difficulty = concept_network_influence.get(review['concept'], {}).get('difficulty', 0.5)
        doc_engagement = doc_interaction_patterns.get(review['concept'], {}).get('engagement', 0.5)

        training_data.append({
            "delta_t": review['interval'],  # 复习间隔（天）
            "rating": review['rating'],  # 用户评分（1-4）
            "r": review['retention'],  # 实际记忆保持率（0-1）
            # 新增特征（利用3层记忆系统数据）
            "concept_difficulty": concept_difficulty,
            "doc_engagement": doc_engagement,
            "prerequisite_readiness": review.get('prerequisite_mastery', 0.5)
        })

    # Step 5: 使用Py-FSRS内置优化器
    from fsrs import FSRS, FSRS_PARAMETERS
    optimizer = FSRS()

    # 转换为FSRS要求的格式
    fsrs_training_data = [
        (item['delta_t'], item['rating'], item['r'])
        for item in training_data
    ]

    # 执行参数优化（最小化RMSE）
    optimized_params = optimizer.optimal_parameters(
        fsrs_training_data,
        initial_params=FSRS_PARAMETERS,
        max_iterations=100,
        verbose=False
    )

    # Step 6: 评估优化效果
    predictions = [optimizer.predict_memory(t[0], optimized_params) for t in fsrs_training_data]
    actual = [t[2] for t in fsrs_training_data]
    rmse = compute_rmse(predictions, actual)

    # 数据质量评分（基于样本量、时间跨度、评分分布）
    data_quality_score = calculate_data_quality(training_data)

    logger.info(f"✅ FSRS参数优化完成: RMSE={rmse:.4f}, 样本数={len(training_data)}, 质量评分={data_quality_score:.2f}")

    return {
        "w": optimized_params,
        "optimization_metrics": {
            "sample_size": len(training_data),
            "rmse": round(rmse, 4),
            "data_quality_score": round(data_quality_score, 2),
            "last_optimization_time": datetime.now().isoformat()
        }
    }


def apply_optimized_parameters():
    """
    应用优化后的参数到EbbinghausReviewSystem

    触发时机:
    1. 系统初始化时（如果有历史数据）
    2. 每累积50次新复习后自动重新优化
    3. 用户手动触发参数优化
    """
    params_result = optimize_fsrs_parameters_from_behavior()

    # 保存优化参数到配置文件
    config_path = "ebbinghaus_config.json"
    with open(config_path, 'w') as f:
        json.dump({
            "optimized_parameters": params_result['w'],
            "metrics": params_result['optimization_metrics'],
            "is_optimized": params_result['optimization_metrics']['sample_size'] >= 100
        }, f, indent=2)

    # 全局替换FSRS实例的参数
    global_fsrs_instance.parameters = params_result['w']

    logger.info(f"✅ 已应用优化参数,样本数={params_result['optimization_metrics']['sample_size']}")
```

**参数优化周期**:
- **初始化**: 如果有≥100次历史复习记录，启动时自动优化
- **增量优化**: 每累积50次新复习后，自动重新优化参数
- **手动触发**: 用户可通过命令 `/review optimize-parameters` 手动触发

**优化效果预期**:
- **准确性提升**: 相比默认参数，预测误差（RMSE）降低20-30%
- **个性化**: 参数完全基于个人学习行为，无通用假设
- **数据真实性**: 100%来自Temporal/Graphiti/Semantic的真实记录

**降级策略**:
- 如果样本数<100，使用默认参数，但明确标记为"临时默认"
- 定期提示用户："已完成50次复习，参数将自动优化以提升准确性"

---

**数据源**:
```json
// ebbinghaus_review_data.json
{
  "concepts": {
    "笔记库/离散数学.canvas_node123_逆否命题": {
      "concept": "逆否命题",
      "canvas_file": "笔记库/离散数学.canvas",
      "node_id": "node123",
      "card": { /* Py-FSRS Card对象 */ },
      "mastery_level": 0.85,
      "review_count": 5,
      "last_reviewed": "2025-01-15T14:30:00Z",
      "created_at": "2025-01-10T10:00:00Z"
    }
  }
}
```

---

#### FR4: 检验白板进度追踪系统 (Should Have - P1)

**描述**: 在检验白板中实时显示已还原的原白板节点数量和颜色分布

**用户故事**:
```
作为学习者
我希望在检验白板中看到"已还原12/15个原白板节点,红色2个通过,紫色10个通过"
这样我可以知道还有哪些知识点没有复现
```

**技术方案**:

**双向映射设计**:
```json
// 检验白板节点 (离散数学-检验白板-20250115.canvas)
{
  "id": "question-abc123",
  "type": "text",
  "text": "什么是逆否命题？",
  "color": "2",  // 用户回答后变绿
  "sourceNodeId": "original-node-xyz789"  // ⭐ 指向原白板节点
}
```

**进度追踪算法**:
```python
def analyze_review_progress(review_canvas_path, original_canvas_path):
    # 1. 读取检验白板,提取所有问题节点的sourceNodeId和颜色
    restored_nodes = {
        node['sourceNodeId']: node['color']
        for node in review_data['nodes']
        if 'sourceNodeId' in node
    }

    # 2. 统计通过的节点
    red_passed = [nid for nid, color in restored_nodes.items() if color == "2"]
    purple_passed = [nid for nid, color in restored_nodes.items() if color == "2"]

    # 3. 返回进度报告
    return {
        "total_concepts": len(restored_nodes),
        "red_nodes_passed": len(red_passed),
        "purple_nodes_passed": len(purple_passed),
        "coverage_rate": len(red_passed + purple_passed) / len(restored_nodes)
    }
```

**UI显示**:
```markdown
## 检验白板进度 - 离散数学

📊 知识还原进度: 12/15 (80%)

🔴 红色节点 (基础概念):
  ✅ 逆否命题定义 (原白板 node-123)
  ✅ 充要条件 (原白板 node-456)
  ❌ 德摩根律 (原白板 node-789) - 未通过

🟣 紫色节点 (进阶问题):
  ✅ 逆否命题应用 (原白板 node-234)
  ❌ 命题等价证明 (原白板 node-567) - 未通过
```

**验收标准**:
- ✅ 实时显示已还原节点数量
- ✅ 红色/紫色/绿色节点统计准确
- ✅ 可点击跳转到原白板对应节点
- ✅ 进度百分比计算正确

---

#### FR5: 跨Canvas关联学习系统 (Should Have - P1)

**描述**: 用户手动配置习题Canvas关联到教材Canvas,Agent自动引用教材内容

**用户故事**:
```
作为学习者
我希望在"线性代数习题集3.canvas"中设置关联到"第3章-向量空间.canvas"
这样Agent生成解释时会自动引用教材定义和文档
```

**UI设计 - Canvas工具栏按钮 + 模态框**:

```
Canvas工具栏:
┌────────────────────────────────────────────┐
│ [🔍] [➕] [🗑️] [⚙️]  ...  [🔗关联]      │  ← 新增按钮
└────────────────────────────────────────────┘

点击 [🔗关联] 后弹出模态框:
┌──────────────────────────────────────────┐
│  🔗 设置Canvas关联                        │
│  ════════════════════════════════════════│
│                                           │
│  当前Canvas:                              │
│  📄 线性代数习题集3.canvas                │
│                                           │
│  ☑️ 启用关联学习模式                      │
│                                           │
│  选择关联的教材Canvas:                    │
│  ┌─────────────────────────────────────┐ │
│  │ 🔍 搜索Canvas...                    │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  最近使用:                                │
│  • 第3章-向量空间.canvas                  │
│  • 第2章-矩阵.canvas                      │
│                                           │
│  或从所有Canvas中选择:                    │
│  • 第1章-行列式.canvas                    │
│  • 第3章-向量空间.canvas ✓ 已选择         │
│  • 第4章-线性方程组.canvas                │
│                                           │
│  [ 取消 ]              [ 保存并启用 ]     │
└──────────────────────────────────────────┘
```

**数据存储**:
```json
// .canvas-links.json (Vault根目录)
{
  "version": "1.0",
  "links": {
    "线性代数习题集3.canvas": {
      "linked_canvas": "第3章-向量空间.canvas",
      "enabled": true,
      "created_at": "2025-01-15T14:30:00Z",
      "settings": {
        "citation_depth": 2,
        "auto_reference": true,
        "priority": "high"
      }
    }
  }
}
```

**Graphiti知识图谱同步**:
```cypher
// 每次保存关联时,同步写入Graphiti
CREATE (exercise:Canvas {path: "线性代数习题集3.canvas"})
CREATE (textbook:Canvas {path: "第3章-向量空间.canvas"})
CREATE (exercise)-[:LINKED_TO {enabled: true, depth: 2}]->(textbook)
```

**Agent引用机制**:
```python
# 调用Agent时,传入教材关联上下文
agent_input = {
  "concept": "向量空间的基",
  "linked_learning_mode": True,
  "textbook_context": [
    {
      "canvas": "第3章-向量空间.canvas",
      "node_id": "concept-basis",
      "content": "基底的定义: 向量空间V的一组基是...",
      "file": "第3章-向量空间-基底-clarification-20250110.md"
    }
  ]
}

# Agent生成的解释文档会包含引用
"""
# 向量空间的基 - 澄清路径

## 教材引用 📚
> 来源: 第3章-向量空间.canvas - 基底节点
> 文档: [基底-clarification-20250110.md](...)

基底的定义: 向量空间V的一组基是...
"""
```

**验收标准**:
- ✅ 用户可通过UI选择关联Canvas
- ✅ 关联配置持久化存储
- ✅ 关联模式可随时开启/关闭 (Toggle)
- ✅ Agent生成的解释自动包含教材引用
- ✅ 教材引用来源清晰标注 (Canvas名称、节点ID、文档链接)
- ✅ Graphiti知识图谱同步关联关系

---

#### FR6-FR10: 其他核心功能

**FR6**: LangGraph多Agent编排 (Must Have - P0)
**FR7**: FastAPI RESTful API (Must Have - P0)
**FR8**: 实时进度推送 (Should Have - P1)
**FR9**: 错误恢复和回滚机制 (Must Have - P0)
**FR10**: 设置面板和配置管理 (Should Have - P1)

---

### 2.2 非功能需求 (Non-Functional Requirements)

#### NFR1: 性能要求 (Critical)

| 指标 | 目标 | 当前系统 | 验证方法 |
|------|------|---------|---------|
| API响应时间 (P95) | <2秒 | ~1.5秒 | 性能基准测试 |
| Canvas文件操作 | <500ms | ~200ms | 单元测试 |
| Neo4j查询响应 | <500ms | ~80ms | 集成测试 |
| Agent执行时间 | 保持现有水平 | 8倍性能提升 | E2E测试 |
| 并发用户支持 | ≥50用户 | 未测试 | 负载测试 |

**关键约束**: Epic 10.2的异步并行执行引擎(8倍性能提升)必须保留

---

#### NFR2: 可靠性要求 (Critical)

- ✅ **数据零丢失**: 所有Canvas操作前自动备份
  - **备份文件夹**: `{Vault根目录}/.canvas_backups/`
    - 系统首次运行时自动创建
    - 在Obsidian设置中配置为隐藏文件夹（不在文件浏览器显示）
  - **备份命名规则**: `{canvas_name}_{checkpoint_id}.canvas`
    - 示例: `离散数学_ckpt_1699999999.canvas`
  - **备份触发时机**: 每次LangGraph创建checkpoint时自动生成
  - **备份清理策略**:
    - 每个Canvas保留最近50个checkpoint备份
    - 超过50个时自动删除最旧的备份
    - 用户手动标记为"受保护"的备份永不自动删除
  - **实施位置**: Epic 12, Story 12.1

- ✅ 故障恢复: API故障时自动重试3次
- ✅ 回滚机制: 错误操作可在10秒内回滚
- ✅ 服务可用性: ≥99% (每月停机时间 <7小时)

---

#### NFR3: 可维护性要求

- ✅ 代码测试覆盖率: ≥85%
- ✅ 文档完整性: 100% (API文档、用户指南、架构文档)
- ✅ 日志完整性: 所有API调用和Agent执行有完整日志
- ✅ 监控告警: 错误率>5%自动告警

---

#### NFR4: 兼容性要求

| 平台/软件 | 版本要求 | 优先级 |
|----------|---------|-------|
| Obsidian | ≥1.4.0 | Must Have |
| Windows | 10/11 | Must Have |
| macOS | ≥12.0 | Should Have |
| Linux | Ubuntu 20.04+ | Could Have |
| Python | 3.11+ | Must Have |
| Node.js | ≥18.0 | Must Have |
| Neo4j | 5.x | Must Have |
| Docker | ≥20.10 | Should Have |

---

#### NFR5: 安全性要求

- ✅ API认证: Bearer Token或API Key
- ✅ 敏感数据加密: OpenAI API Key加密存储
- ✅ CORS配置: 仅允许 `app://obsidian.md` 访问
- ✅ 输入验证: 所有API请求参数验证,防止注入攻击

---

#### NFR6: 用户体验要求

- ✅ 操作响应: UI操作反馈 <500ms
- ✅ 错误提示: 清晰、友好、可操作 (不显示技术栈错误)
- ✅ 加载状态: 长操作显示进度条和百分比
- ✅ 帮助文档: 内置帮助,快捷键Ctrl+? 呼出

---

## 🏗️ Section 3: 技术架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Obsidian Desktop                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Canvas Learning Plugin (TypeScript)           │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────────┐ │  │
│  │  │ UI Layer│  │ Commands │  │ Views (Review Panel) │ │  │
│  │  └────┬────┘  └────┬─────┘  └──────────┬───────────┘ │  │
│  │       └────────────┼────────────────────┘             │  │
│  │                    │ HTTP/WebSocket                   │  │
│  └────────────────────┼──────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │       【Layer 3】canvas-orchestrator (智能路由层)     │  │
│  │  • 自然语言意图识别                                   │  │
│  │  • 执行计划生成                                       │  │
│  │  • 调用LangGraph执行引擎                              │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       ↓                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     【Layer 4】LangGraph StateGraph (执行引擎)        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │        LangGraph Supervisor (并发调度)           │ │  │
│  │  └────┬──────────┬──────────┬──────────┬──────┬────┘ │  │
│  │       │          │          │          │      │      │  │
│  │  ┌────▼────┐┌───▼────┐┌───▼────┐┌───▼────┐ ┌▼────┐ │  │
│  │  │basic-   ││deep-   ││scoring ││oral-   │ │...  │ │  │
│  │  │decomp   ││decomp  ││agent   ││explain │ │x12  │ │  │
│  │  │✅ Tools ││✅ Tools││✅ Tools││✅ Tools│ │     │ │  │
│  │  └─────────┘└────────┘└────────┘└────────┘ └─────┘ │  │
│  │      ↓           ↓          ↓          ↓      ↓     │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  共享Tools (所有Agent可直接调用)              │   │  │
│  │  │  • write_to_canvas (FileLock)               │   │  │
│  │  │  • create_md_file                           │   │  │
│  │  │  • add_edge_to_canvas                       │   │  │
│  │  │  • update_ebbinghaus                        │   │  │
│  │  │  • query_graphiti_context                   │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────┐  ┌────────────────┐  ┌──────────────────┐    │
│  │ Canvas   │  │ Ebbinghaus     │  │ .canvas-links    │    │
│  │ Utils    │  │ review_data    │  │ .json            │    │
│  │ (Python) │  │ .json          │  │                  │    │
│  └──────────┘  └────────────────┘  └──────────────────┘    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Neo4j Knowledge Graph                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Graphiti Temporal Knowledge Graph                    │  │
│  │  • Canvas entities                                    │  │
│  │  • Node concepts                                      │  │
│  │  • Cross-canvas links (LINKED_TO, REQUIRES)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**架构设计说明 (双层Supervisor模式)**:

**核心理念**: 保留canvas-orchestrator的智能路由能力,同时引入LangGraph的并发执行引擎

**Layer 3 - canvas-orchestrator (智能路由层)**:
- **作用**: 自然语言意图识别、执行计划生成、调用LangGraph执行
- **保留原因**: 这是现有系统的核心优势,能准确理解用户意图
- **位置**: FastAPI Backend的前置处理层

**Layer 4 - LangGraph StateGraph (执行引擎)**:
- **作用**: 并发调度、状态管理、Agent生命周期管理
- **优势**: 保留Epic 10.2的8倍性能提升,实现真正的异步并行执行
- **创新**: 每个Agent配备工具,直接写入Canvas,实现0.5-1s快速响应

**工具配备策略**:
- **分布式写入**: 每个Agent直接调用write_to_canvas工具,避免集中式写入的延迟
- **FileLock保护**: 跨平台文件锁机制,确保多个Agent并发写入时的数据一致性
- **写入历史**: 记录所有写入操作,支持错误回滚

**性能对比**:

| 方案 | 首个节点出现时间 | 用户体验 | 实现复杂度 |
|------|-----------------|---------|-----------|
| 集中式写入 (canvas_finalizer) | 8-10秒 | ❌ 无实时反馈 | 低 |
| 工具配备Agent (分布式写入) | 0.5-1秒 | ✅ 实时可见 | 中 (需FileLock) |

### 3.2 LangGraph多Agent架构 (工具配备模式)

#### 3.2.1 State定义

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import MessagesState, add_messages

class CanvasLearningState(MessagesState):
    # 基础信息
    canvas_path: str
    operation: str  # decompose/explain/score/review

    # Canvas数据
    canvas_data: dict
    target_nodes: list[dict]

    # 关联学习
    linked_mode: bool
    linked_canvas_path: str | None
    textbook_context: list[dict]

    # Agent结果
    agent_results: dict
    generated_files: list[str]

    # 艾宾浩斯复习
    review_updates: list[dict]

    # 进度追踪
    progress_data: dict | None

    # 写入历史 (用于回滚)
    write_history: list[dict]

    # 最终输出
    output_message: str
```

#### 3.2.2 双层Supervisor设计

**Layer 3: canvas-orchestrator (智能路由层)**

```python
class CanvasOrchestrator:
    """Layer 3: 智能路由层 - 保留原有的自然语言理解能力"""

    def process_command(self, user_input: str, canvas_path: str) -> dict:
        """处理用户命令,生成执行计划"""
        # Step 1: 意图识别
        intent = self.parse_intent(user_input)
        # intent = {
        #     "operation": "basic_decompose",
        #     "target_nodes": ["node-123", "node-456"],
        #     "linked_mode": True,
        #     "textbook_canvas": "第3章-向量空间.canvas"
        # }

        # Step 2: 生成执行计划
        plan = self.create_execution_plan(intent, canvas_path)

        # Step 3: 调用LangGraph执行引擎
        result = await self.execute_with_langgraph(plan, canvas_path)

        return result

    def parse_intent(self, user_input: str) -> dict:
        """自然语言意图识别 (保留原有逻辑)"""
        # 现有的canvas-orchestrator逻辑
        pass

    def create_execution_plan(self, intent: dict, canvas_path: str) -> dict:
        """生成执行计划"""
        return {
            "operation": intent["operation"],
            "canvas_path": canvas_path,
            "target_nodes": self.load_target_nodes(canvas_path, intent["target_nodes"]),
            "linked_mode": intent.get("linked_mode", False),
            "textbook_context": self.load_textbook_context(intent) if intent.get("linked_mode") else []
        }
```

**Layer 4: LangGraph StateGraph (执行引擎)**

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_openai import ChatOpenAI

# Step 1: 定义共享Tools
@tool
def write_to_canvas(canvas_path: str, node_data: dict, config: RunnableConfig) -> str:
    """直接写入Canvas节点 (带FileLock保护)"""
    lock_file = f"{canvas_path}.lock"

    with FileLock(lock_file, timeout=10):
        # 读取Canvas
        canvas_data = read_canvas(canvas_path)

        # 添加节点
        canvas_data["nodes"].append(node_data)

        # 写入Canvas
        write_canvas(canvas_path, canvas_data)

        # 记录写入历史 (用于回滚)
        state = config.configurable.get("state")
        if state:
            state["write_history"].append({
                "timestamp": datetime.now().isoformat(),
                "operation": "add_node",
                "node_id": node_data["id"],
                "canvas_path": canvas_path
            })

    return f"✅ 已添加节点 {node_data['id']} 到 {canvas_path}"

@tool
def create_md_file_for_canvas(
    concept: str,
    content: str,
    file_type: str,
    canvas_path: str,  # ✅ 新增参数：Canvas文件路径
    config: RunnableConfig
) -> Dict[str, Any]:  # ✅ 修改返回类型
    """
    为Canvas生成解释文档（Markdown文件）

    ⚠️ 修复需求1: 解决Obsidian文件引用路径问题

    Args:
        concept: 概念名称
        content: 文档内容
        file_type: 文档类型（oral-explanation, clarification-path, etc.）
        canvas_path: Canvas文件路径（用于计算Vault相对路径）
        config: Runnable配置

    Returns:
        包含vault_path, timestamp, filename的字典
        - vault_path: Vault相对路径（用于Canvas FILE节点引用）
        - timestamp: 时间戳（确保Canvas引用与实际文件一致）
        - filename: 文件名
        - full_path: 完整文件系统路径
        - success: 是否成功

    Example:
        canvas_path = "Canvas/Math53/离散数学.canvas"
        result = create_md_file_for_canvas("逆否命题", content, "口语化解释", canvas_path, config)
        # result["vault_path"] = "Canvas/Math53/逆否命题-口语化解释-20250115143025.md"
        # 用于Canvas FILE节点: {"type": "file", "file": result["vault_path"]}
    """
    # ✅ 计算Canvas所在目录（Vault相对路径）
    canvas_dir = os.path.dirname(canvas_path)  # "Canvas/Math53"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{concept}-{file_type}-{timestamp}.md"
    vault_relative_path = os.path.join(canvas_dir, filename)
    # 结果: "Canvas/Math53/逆否命题-口语化解释-20250115143025.md"

    # ✅ 获取Vault根目录
    vault_root = config.configurable.get("vault_root") or os.getenv("OBSIDIAN_VAULT_ROOT")
    if not vault_root:
        raise ValueError("Vault root not configured in config.configurable['vault_root'] or OBSIDIAN_VAULT_ROOT env var")

    full_path = os.path.join(vault_root, vault_relative_path)

    # ✅ 写入文件
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 记录到state
    state = config.configurable.get("state")
    if state:
        state["generated_files"].append(vault_relative_path)

    return {
        "vault_path": vault_relative_path,  # ✅ Vault相对路径（用于Canvas FILE节点）
        "timestamp": timestamp,              # ✅ 时间戳一致性
        "filename": filename,
        "full_path": full_path,
        "success": True
    }

# ========================================
# ✅ 新增工具组: 3层记忆系统调度工具
# 修复需求2: 明确记忆系统调度时机
# 修复需求3: 检验白板生成时调用Graphiti获取上下文
# ========================================

@tool
def store_to_graphiti_memory(
    session_id: str,
    operation_type: str,  # "decomposition", "scoring", "explanation", "verification_board", etc.
    canvas_path: str,
    node_data: Dict[str, Any],
    config: RunnableConfig
) -> str:
    """
    存储Canvas操作到Graphiti知识图谱

    ⚠️ 修复需求2: 记忆系统调度时机

    调度时机:
    1. 问题拆解后: operation_type="decomposition"
    2. 评分完成后: operation_type="scoring"
    3. 生成解释文档后: operation_type="explanation"
    4. 生成检验白板后: operation_type="verification_board"
    5. 跨Canvas关联时: operation_type="cross_canvas_link"

    Args:
        session_id: 学习会话ID
        operation_type: 操作类型
        canvas_path: Canvas文件路径
        node_data: 节点数据（包含节点ID、内容、颜色等）
        config: Runnable配置

    Returns:
        Graphiti存储结果消息
    """
    episode_content = f"""
Canvas学习操作记录:
- 会话ID: {session_id}
- 操作类型: {operation_type}
- Canvas: {canvas_path}
- 节点数据: {json.dumps(node_data, ensure_ascii=False, indent=2)}
- 时间戳: {datetime.now().isoformat()}
"""

    # 调用MCP Graphiti工具
    result = mcp__graphiti_memory__add_episode(content=episode_content)

    # 记录到state
    state = config.configurable.get("state")
    if state and "memory_records" in state:
        state["memory_records"].append({
            "type": "graphiti",
            "operation": operation_type,
            "timestamp": datetime.now().isoformat()
        })

    return f"✅ 已存储到Graphiti知识图谱: {result}"

@tool
def store_to_temporal_memory(
    session_id: str,
    event_type: str,
    timestamp: datetime,
    metadata: Dict[str, Any],
    config: RunnableConfig
) -> str:
    """
    存储Canvas操作到时序记忆

    ⚠️ 修复需求2: 时序记忆调度

    调度时机: 与Graphiti同步调度（所有Canvas操作）

    Args:
        session_id: 学习会话ID
        event_type: 事件类型
        timestamp: 事件时间戳
        metadata: 元数据（Canvas路径、节点信息等）
        config: Runnable配置

    Returns:
        Temporal存储结果消息
    """
    from memory_system.unified_memory_interface import UnifiedMemoryInterface

    memory = UnifiedMemoryInterface()
    memory.temporal_manager.store_event(
        session_id=session_id,
        event_type=event_type,
        timestamp=timestamp,
        metadata=metadata
    )

    # 记录到state
    state = config.configurable.get("state")
    if state and "memory_records" in state:
        state["memory_records"].append({
            "type": "temporal",
            "event_type": event_type,
            "timestamp": timestamp.isoformat()
        })

    return f"✅ 已存储到Temporal时序记忆"

@tool
def store_to_semantic_memory(
    session_id: str,
    document_path: str,
    content: str,
    metadata: Dict[str, Any],
    config: RunnableConfig
) -> str:
    """
    存储文档向量到语义记忆

    ⚠️ 修复需求2: 语义记忆调度

    调度时机: 仅在生成解释文档后调用（operation_type="explanation"）

    Args:
        session_id: 学习会话ID
        document_path: 文档路径（Vault相对路径）
        content: 文档内容
        metadata: 元数据
        config: Runnable配置

    Returns:
        Semantic存储结果消息
    """
    from memory_system.unified_memory_interface import UnifiedMemoryInterface

    memory = UnifiedMemoryInterface()
    memory.semantic_manager.store_document_vector(
        session_id=session_id,
        document_path=document_path,
        content=content,
        metadata=metadata
    )

    # 记录到state
    state = config.configurable.get("state")
    if state and "memory_records" in state:
        state["memory_records"].append({
            "type": "semantic",
            "document_path": document_path,
            "timestamp": datetime.now().isoformat()
        })

    return f"✅ 已存储到Semantic语义记忆: {document_path}"

@tool
def query_graphiti_for_verification(
    concept: str,
    user_understanding: str,
    canvas_path: str,
    config: RunnableConfig
) -> Dict[str, Any]:
    """
    查询Graphiti以生成高关联度检验问题

    ⚠️ 修复需求3: 智能检验白板生成机制

    用途: 在生成检验白板时，先查询Graphiti获取上下文，再传递给verification-question-agent

    查询内容:
    1. 相关概念: 查找与目标概念相关的其他概念
    2. 历史盲区: 查询用户在此概念上的历史理解盲区
    3. 概念关系: 查询概念之间的关系（前置知识、等价关系等）

    返回的上下文将作为verification-question-agent的graphiti_context字段输入

    Args:
        concept: 概念名称
        user_understanding: 用户当前理解（黄色节点内容）
        canvas_path: Canvas文件路径
        config: Runnable配置

    Returns:
        包含related_concepts, historical_blind_spots, concept_relationships的字典

    Example:
        context = query_graphiti_for_verification("逆否命题", user_understanding, canvas_path, config)
        # context = {
        #   "related_concepts": [{"name": "命题逻辑", "relationship": "prerequisite_of", "score": 0.9}],
        #   "historical_blind_spots": [{"concept": "否命题 vs 逆否命题", "frequency": 3}],
        #   "concept_relationships": [{"from": "逆否命题", "to": "等价命题", "type": "is_a"}]
        # }
        #
        # 然后传递给verification-question-agent:
        # agent_input = {"nodes": [...], "graphiti_context": context}
    """
    session_id = config.configurable.get("session_id")

    # 1. 查询相关概念
    related_concepts_raw = mcp__graphiti_memory__search_memories(
        query=f"concept:{concept} related prerequisite"
    )

    # 2. 查询历史盲区
    blind_spots_raw = mcp__graphiti_memory__search_memories(
        query=f"user:{session_id} blind_spot error misconception {concept}"
    )

    # 3. 查询概念关系
    relationships_raw = mcp__graphiti_memory__search_memories(
        query=f"relationship {concept} equivalent prerequisite contrast"
    )

    # 解析并结构化结果
    related_concepts = [
        {
            "name": item.get("concept", ""),
            "relationship": item.get("relationship_type", "related_to"),
            "score": item.get("relevance_score", 0.5)
        }
        for item in related_concepts_raw[:5]  # 取Top 5
    ]

    historical_blind_spots = [
        {
            "concept": item.get("blind_spot_concept", ""),
            "frequency": item.get("occurrence_count", 1),
            "last_occurrence": item.get("last_seen", "")
        }
        for item in blind_spots_raw[:3]  # 取Top 3
    ]

    concept_relationships = [
        {
            "from": item.get("source_concept", concept),
            "to": item.get("target_concept", ""),
            "type": item.get("relationship_type", "related_to"),
            "strength": item.get("strength", 0.5)
        }
        for item in relationships_raw[:5]  # 取Top 5
    ]

    return {
        "related_concepts": related_concepts,
        "historical_blind_spots": historical_blind_spots,
        "concept_relationships": concept_relationships,
        "suggested_question_types": ["definition", "contrast", "application", "reasoning"],
        "query_metadata": {
            "concept": concept,
            "session_id": session_id,
            "canvas_path": canvas_path,
            "query_timestamp": datetime.now().isoformat()
        }
    }

# ========================================
# ✅ v1.1.6新增工具组: 艾宾浩斯复习系统3层记忆查询工具
# 用途: 为艾宾浩斯复习系统提供真实数据源，替代模拟数据
# ========================================

@tool
def query_temporal_learning_behavior(
    filter_type: str,
    canvas_file: str = None,
    concept_ids: List[str] = None,
    days_threshold: int = None,
    min_mastery: float = None,
    min_samples: int = None,
    fields: List[str] = None,
    metrics: List[str] = None,
    config: RunnableConfig = None
) -> Dict[str, Any]:
    """
    查询Temporal Memory学习行为数据（v1.1.6新增 - 艾宾浩斯系统数据整合）

    用途:
    1. 艾宾浩斯系统触发点4: 检测长期未访问的已掌握概念
    2. FR3.2聚合逻辑: 提供学习行为数据（复习频率、间隔、正确率）
    3. FR3.6参数优化: 提供历史复习记录用于优化FSRS参数

    Args:
        filter_type: 过滤类型
            - "inactive_mastered": 长期未访问且已掌握的概念（触发点4）
            - "all_reviews": 所有复习记录（参数优化）
            - "recent_behavior": 最近行为数据（聚合逻辑）
        canvas_file: Canvas文件路径（可选，用于聚合逻辑）
        concept_ids: 概念ID列表（可选，用于聚合逻辑）
        days_threshold: 天数阈值（用于inactive_mastered）
        min_mastery: 最小掌握度阈值（用于inactive_mastered）
        min_samples: 最小样本数（用于参数优化）
        fields: 返回字段列表（用于参数优化）
        metrics: 指标列表（用于聚合逻辑）
        config: Runnable配置

    Returns:
        根据filter_type返回不同格式:
        - inactive_mastered: List[Dict] 未访问概念列表
        - all_reviews: List[Dict] 历史复习记录
        - recent_behavior: Dict 行为指标数据
    """
    from memory_system.unified_memory_interface import UnifiedMemoryInterface

    memory = UnifiedMemoryInterface()
    temporal_manager = memory.temporal_manager

    if filter_type == "inactive_mastered":
        # 触发点4: 查询长期未访问的已掌握概念
        return temporal_manager.query_inactive_mastered_concepts(
            days_threshold=days_threshold or 7,
            min_mastery=min_mastery or 0.6
        )

    elif filter_type == "all_reviews":
        # FR3.6参数优化: 查询所有历史复习记录
        return temporal_manager.query_all_reviews(
            min_samples=min_samples or 100,
            fields=fields or ["review_time", "rating", "interval", "stability", "difficulty"]
        )

    elif filter_type == "recent_behavior":
        # FR3.2聚合逻辑: 查询最近行为数据
        return temporal_manager.query_recent_behavior(
            canvas_file=canvas_file,
            concept_ids=concept_ids,
            metrics=metrics or ["review_frequency", "avg_interval", "accuracy_trend"]
        )

    else:
        raise ValueError(f"Unknown filter_type: {filter_type}")

@tool
def query_graphiti_concept_network(
    canvas_file: str = None,
    concept_ids: List[str] = None,
    analysis_type: str = "related_concepts",
    concepts: List[str] = None,
    analysis: List[str] = None,
    min_prerequisite_mastery: float = None,
    gap_days_threshold: int = None,
    config: RunnableConfig = None
) -> Dict[str, Any]:
    """
    查询Graphiti概念关系网络（v1.1.6新增 - 艾宾浩斯系统数据整合）

    用途:
    1. 艾宾浩斯系统触发点4: 检测知识断层（前置概念已掌握但后续概念未学习）
    2. FR3.2聚合逻辑: 提供概念关系数据（前置概念掌握度、关联概念难度）
    3. FR3.6参数优化: 提供概念难度分布和前置关系影响

    Args:
        canvas_file: Canvas文件路径（可选，用于聚合逻辑）
        concept_ids: 概念ID列表（可选，用于聚合逻辑）
        analysis_type: 分析类型
            - "prerequisite_gap": 知识断层检测（触发点4）
            - "learning_difficulty_distribution": 概念难度分布（参数优化）
            - "related_concepts": 相关概念查询（聚合逻辑）
        concepts: 概念名称列表（用于参数优化）
        analysis: 分析维度列表（用于聚合逻辑）
        min_prerequisite_mastery: 前置概念最小掌握度（用于知识断层检测）
        gap_days_threshold: 知识断层天数阈值（用于知识断层检测）
        config: Runnable配置

    Returns:
        根据analysis_type返回不同格式:
        - prerequisite_gap: List[Dict] 知识断层概念列表
        - learning_difficulty_distribution: Dict[str, float] 概念→难度映射
        - related_concepts: Dict 概念关系数据
    """
    session_id = config.configurable.get("session_id") if config else "default_session"

    if analysis_type == "prerequisite_gap":
        # 触发点4: 检测知识断层
        query = f"prerequisite mastered but successor not learned gap_days:{gap_days_threshold or 14}"
        results = mcp__graphiti_memory__search_memories(query=query)

        return [
            {
                "concept": item.get("successor_concept", ""),
                "canvas_file": item.get("canvas_file", ""),
                "node_id": item.get("node_id", ""),
                "mastery": item.get("estimated_mastery", 0.0),
                "detection_reason": "知识断层"
            }
            for item in results if item.get("prerequisite_mastery", 0) >= (min_prerequisite_mastery or 0.8)
        ]

    elif analysis_type == "learning_difficulty_distribution":
        # FR3.6参数优化: 概念难度分布
        difficulty_map = {}
        for concept in (concepts or []):
            query = f"concept:{concept} difficulty mastery_level"
            results = mcp__graphiti_memory__search_memories(query=query)
            if results:
                difficulty_map[concept] = {"difficulty": results[0].get("difficulty", 0.5)}

        return difficulty_map

    elif analysis_type == "related_concepts":
        # FR3.2聚合逻辑: 相关概念查询
        network_data = {}
        for concept_id in (concept_ids or []):
            query = f"node:{concept_id} prerequisite related difficulty path_depth"
            results = mcp__graphiti_memory__search_memories(query=query)
            if results:
                network_data[concept_id] = {
                    "prerequisite_completeness": results[0].get("prerequisite_completeness", 0.8),
                    "related_difficulty_normalized": results[0].get("related_difficulty_normalized", 0.5),
                    "knowledge_path_depth": results[0].get("knowledge_path_depth", 0)
                }

        # 聚合指标
        if concept_ids:
            values = list(network_data.values())
            return {
                "prerequisite_completeness": sum(v.get("prerequisite_completeness", 0) for v in values) / len(values) if values else 0.8,
                "related_difficulty_normalized": sum(v.get("related_difficulty_normalized", 0) for v in values) / len(values) if values else 0.5,
                "knowledge_path_depth": sum(v.get("knowledge_path_depth", 0) for v in values) / len(values) if values else 0
            }
        return network_data

    else:
        raise ValueError(f"Unknown analysis_type: {analysis_type}")

@tool
def query_semantic_document_interactions(
    pattern: str = "related_doc_frequent_but_concept_inactive",
    canvas_file: str = None,
    concept_ids: List[str] = None,
    related_access_threshold: int = None,
    concept_inactive_days: int = None,
    concepts: List[str] = None,
    metrics: List[str] = None,
    config: RunnableConfig = None
) -> Dict[str, Any]:
    """
    查询Semantic Memory文档交互数据（v1.1.6新增 - 艾宾浩斯系统数据整合）

    用途:
    1. 艾宾浩斯系统触发点4: 检测隐性需求（相关文档频繁访问但概念未复习）
    2. FR3.2聚合逻辑: 提供文档交互数据（查阅频率、停留时间、访问模式）
    3. FR3.6参数优化: 提供文档交互模式与记忆保持的相关性

    Args:
        pattern: 查询模式
            - "related_doc_frequent_but_concept_inactive": 隐性需求检测（触发点4）
            - "review_engagement_correlation": 复习参与度相关性（参数优化）
            - "access_metrics": 访问指标查询（聚合逻辑）
        canvas_file: Canvas文件路径（可选，用于聚合逻辑）
        concept_ids: 概念ID列表（可选，用于聚合逻辑）
        related_access_threshold: 相关文档访问阈值（用于隐性需求检测）
        concept_inactive_days: 概念未活跃天数（用于隐性需求检测）
        concepts: 概念名称列表（用于参数优化）
        metrics: 指标列表（用于聚合逻辑）
        config: Runnable配置

    Returns:
        根据pattern返回不同格式:
        - related_doc_frequent_but_concept_inactive: List[Dict] 隐性需求概念列表
        - review_engagement_correlation: Dict[str, float] 概念→参与度映射
        - access_metrics: Dict 访问指标数据
    """
    from memory_system.unified_memory_interface import UnifiedMemoryInterface

    memory = UnifiedMemoryInterface()
    semantic_manager = memory.semantic_manager

    if pattern == "related_doc_frequent_but_concept_inactive":
        # 触发点4: 隐性需求检测
        return semantic_manager.detect_implicit_needs(
            related_access_threshold=related_access_threshold or 5,
            concept_inactive_days=concept_inactive_days or 7
        )

    elif pattern == "review_engagement_correlation":
        # FR3.6参数优化: 复习参与度相关性
        engagement_map = {}
        for concept in (concepts or []):
            engagement_data = semantic_manager.query_engagement(concept=concept)
            engagement_map[concept] = {"engagement": engagement_data.get("engagement_score", 0.5)}

        return engagement_map

    elif pattern == "access_metrics":
        # FR3.2聚合逻辑: 访问指标查询
        interaction_data = {}
        for concept_id in (concept_ids or []):
            metrics_data = semantic_manager.query_metrics(
                concept_id=concept_id,
                metrics=metrics or ["access_frequency", "dwell_time", "related_docs_pattern"]
            )
            interaction_data[concept_id] = metrics_data

        # 聚合指标
        if concept_ids:
            values = list(interaction_data.values())
            return {
                "recent_access_frequency": sum(v.get("access_frequency", 0) for v in values) / len(values) if values else 0.3,
                "dwell_time_normalized": sum(v.get("dwell_time_normalized", 0) for v in values) / len(values) if values else 0.4,
                "related_docs_pattern_score": sum(v.get("related_docs_pattern_score", 0) for v in values) / len(values) if values else 0.5
            }
        return interaction_data

    else:
        raise ValueError(f"Unknown pattern: {pattern}")

@tool
def track_learning_behavior(
    session_id: str,
    canvas_file: str,
    node_id: str,
    concept: str,
    operation_type: str,
    behavior_data: Dict[str, Any],
    config: RunnableConfig = None
) -> str:
    """
    记录学习行为到Temporal Memory（v1.1.6新增 - 艾宾浩斯系统行为监控）

    用途:
    1. FR3.1触发点4: 为行为监控提供数据源
    2. FR3.6参数优化: 积累真实复习记录用于FSRS参数优化
    3. FR3.2聚合逻辑: 提供实时行为数据用于优先级计算

    调用时机:
    - Canvas节点评分后: operation_type="scoring"
    - 检验白板复习后: operation_type="review"
    - 用户访问Canvas时: operation_type="view"
    - 文档交互时: operation_type="doc_interaction"

    Args:
        session_id: 学习会话ID
        canvas_file: Canvas文件路径
        node_id: 节点ID
        concept: 概念名称
        operation_type: 操作类型 (scoring/review/view/doc_interaction)
        behavior_data: 行为数据
            - score: 评分（如果operation_type="scoring"）
            - rating: 复习评级1-4（如果operation_type="review"）
            - duration: 停留时间（如果operation_type="view"）
            - interaction_type: 交互类型（如果operation_type="doc_interaction"）
        config: Runnable配置

    Returns:
        记录结果消息
    """
    from memory_system.unified_memory_interface import UnifiedMemoryInterface

    memory = UnifiedMemoryInterface()
    temporal_manager = memory.temporal_manager

    # 构建事件数据
    event_data = {
        "session_id": session_id,
        "canvas_file": canvas_file,
        "node_id": node_id,
        "concept": concept,
        "operation_type": operation_type,
        "timestamp": datetime.now().isoformat(),
        **behavior_data
    }

    # 存储到Temporal Memory
    temporal_manager.store_learning_event(event_data)

    # 同步记录到state（用于会话追踪）
    if config:
        state = config.configurable.get("state")
        if state and "behavior_tracking" in state:
            state["behavior_tracking"].append(event_data)

    return f"✅ 已记录学习行为: {operation_type} - {concept}"

@tool
def add_edge_to_canvas(canvas_path: str, from_id: str, to_id: str, config: RunnableConfig) -> str:
    """添加Canvas边连接"""
    lock_file = f"{canvas_path}.lock"

    with FileLock(lock_file, timeout=10):
        canvas_data = read_canvas(canvas_path)
        canvas_data["edges"].append({
            "id": f"edge-{from_id}-{to_id}",
            "fromNode": from_id,
            "toNode": to_id
        })
        write_canvas(canvas_path, canvas_data)

    return f"✅ 已连接节点 {from_id} → {to_id}"

# 所有Agent共享的工具集
# ✅ 修复后的共享工具列表（包含3个需求的所有修复）
shared_tools = [
    write_to_canvas,
    create_md_file_for_canvas,  # ✅ 修复需求1: 支持Vault相对路径
    add_edge_to_canvas,
    update_ebbinghaus,
    query_graphiti_context,
    # ✅ 修复需求2&3: 3层记忆系统调度工具
    store_to_graphiti_memory,
    store_to_temporal_memory,
    store_to_semantic_memory,
    query_graphiti_for_verification  # ✅ 修复需求3: 检验白板Graphiti上下文查询
]

# ========================================
# 工具间协调机制与职责边界 (新增 - v1.1.3)
# ========================================

**背景**: Canvas学习系统采用双重记忆架构：
1. **LangGraph Checkpointer** (框架自带): 持久化Agent执行状态和对话上下文
2. **3层记忆系统** (业务定制): Graphiti知识图谱 + Temporal时序记忆 + Semantic语义记忆

**设计原则**: 职责明确，避免数据冗余，确保一致性

---

## LangGraph Checkpointer (框架层记忆)

**职责范围**:
- ✅ 存储CanvasLearningState对象（Agent执行的中间状态）
- ✅ 支持多轮对话上下文持久化（thread_id维度）
- ✅ 提供回滚能力（通过checkpoint ID和timestamp）
- ✅ 自动管理（LangGraph框架自动调用，开发者无需手动触发）

**不存储**:
- ❌ Canvas文件内容（由write_to_canvas直接写入文件系统）
- ❌ 知识图谱数据（由Graphiti管理）
- ❌ 学习事件时间线（由Temporal记忆管理）
- ❌ 文档向量（由Semantic记忆管理）

**数据示例**:
```json
{
  "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875",
  "thread_id": "canvas_离散数学_session_20250115_143025",
  "timestamp": "2025-01-15T14:30:25Z",
  "state": {
    "session_id": "session_20250115_143025",
    "canvas_path": "Canvas/Math53/离散数学.canvas",
    "current_concept": "逆否命题",
    "last_operation": "decomposition",
    "decomposition_results": ["什么是逆否命题？", "它与原命题有何关系？"],
    "write_history": [...]
  }
}
```

**何时使用**:
- Agent节点执行完毕自动触发（LangGraph框架行为）
- 多轮对话需要恢复上下文时读取（通过thread_id）
- 回滚操作时查询历史checkpoint

---

## Graphiti知识图谱 (业务层记忆 - 语义关系)

**职责范围**:
- ✅ 存储Canvas节点的语义关系（概念关联、前置知识、相似概念）
- ✅ 支持跨Canvas知识图谱查询（Epic 16核心功能）
- ✅ 支持智能推荐（相关概念、前置知识推荐）
- ✅ 支持检验白板生成时的上下文查询

**不存储**:
- ❌ Agent执行状态（由LangGraph checkpointer管理）
- ❌ 文档完整内容（仅存储关联关系，内容由Semantic管理）

**数据示例**:
```cypher
// 节点
(n1:Concept {name: "逆否命题", canvas: "离散数学.canvas"})
(n2:Concept {name: "原命题", canvas: "离散数学.canvas"})
(n3:Concept {name: "逆否命题", canvas: "数理逻辑.canvas"})

// 关系
(n1)-[:RELATED_TO {relation_type: "逻辑等价"}]->(n2)
(n1)-[:SIMILAR_TO {similarity: 0.95}]->(n3)
```

**何时调用**:
- `store_to_graphiti_memory()`: 每次Canvas操作后（拆解、评分、生成解释、跨Canvas关联）
- `query_graphiti_for_verification()`: 生成检验白板前查询相关概念
- `query_graphiti_context()`: Agent需要上下文时查询

---

## Temporal时序记忆 (业务层记忆 - 学习历程)

**职责范围**:
- ✅ 存储学习事件时间线（拆解时间、评分时间、复习时间）
- ✅ 支持学习进度分析和统计（Epic 14复习系统依赖）
- ✅ 支持学习习惯分析（学习时段、学习频率）

**不存储**:
- ❌ 事件的详细内容（仅存储元数据和时间戳）
- ❌ 知识图谱关系（由Graphiti管理）

**数据示例**:
```json
{
  "event_id": "evt_20250115_143025_001",
  "session_id": "session_20250115_143025",
  "event_type": "decomposition_completed",
  "timestamp": "2025-01-15T14:30:25Z",
  "metadata": {
    "canvas_path": "离散数学.canvas",
    "concept": "逆否命题",
    "question_count": 5
  }
}
```

**何时调用**:
- `store_to_temporal_memory()`: 每次Canvas操作后记录事件

---

## Semantic语义记忆 (业务层记忆 - 文档向量)

**职责范围**:
- ✅ 存储AI生成文档的向量表示（解释文档embeddings）
- ✅ 支持语义相似度检索（找相似解释）
- ✅ 支持文档推荐（"这个解释可能对你有帮助"）

**不存储**:
- ❌ Canvas节点内容（节点内容在Canvas文件中）
- ❌ 知识图谱（由Graphiti管理）

**数据示例**:
```json
{
  "document_id": "doc_逆否命题_口语化解释_20250115143025",
  "file_path": "Canvas/Math53/逆否命题-口语化解释-20250115143025.md",
  "embedding": [0.123, -0.456, ...],  // 1536维向量
  "metadata": {
    "concept": "逆否命题",
    "agent": "oral-explanation",
    "word_count": 950
  }
}
```

**何时调用**:
- `store_to_semantic_memory()`: 仅在生成解释文档后

---

## 调用时序图

```
Agent Node执行
    ↓
1. Canvas操作 (write_to_canvas, create_md_file_for_canvas)
    ↓ ← 关键路径，失败则整个操作失败
2. 业务层记忆存储 (非关键路径，最终一致性)
    ├─→ store_to_graphiti_memory()
    ├─→ store_to_temporal_memory()
    └─→ store_to_semantic_memory() [仅解释文档]
    ↓ ← 失败仅记录日志，不阻塞
3. Agent返回new_state
    ↓
LangGraph框架自动持久化State到Checkpointer
    ↓
操作完成
```

---

## 一致性保证

**强一致性**:
- Canvas文件写入 ↔ LangGraph Checkpointer State
  - 机制: 在事务内完成，write_to_canvas失败则LangGraph自动回滚State

**最终一致性**:
- Canvas文件 ↔ Graphiti/Temporal/Semantic
  - 机制: 异步存储 + 重试机制 + 定期对账任务

**冲突解决**:
- 如果Graphiti/Temporal/Semantic存储失败，系统行为：
  1. 记录错误日志（包含session_id, operation_type, error_message）
  2. 不阻塞Canvas操作和用户体验
  3. 后台异步重试（指数退避策略）
  4. 管理员可查看失败队列，手动触发重试

---

# Step 2: 创建工具配备的Agent节点
model = ChatOpenAI(model="gpt-4")

# Agent 1: basic-decomposition (配备工具)
basic_decomposition_agent = create_react_agent(
    model=model,
    tools=shared_tools,
    state_modifier="""你是基础拆解Agent。

    任务: 为红色节点生成3-7个基础引导问题。

    ⚠️ 重要: 生成问题后,立即调用write_to_canvas工具将问题节点写入Canvas!

    工具使用示例:
    1. 生成问题列表
    2. 对每个问题调用 write_to_canvas(canvas_path, {
        "id": "question-abc123",
        "type": "text",
        "text": "什么是逆否命题?",
        "color": "1",
        "x": 100, "y": 200,
        "width": 300, "height": 80
    })
    3. 调用 add_edge_to_canvas 连接原节点和问题节点

    返回: 生成的问题列表
    """
)

# Agent 2: deep-decomposition (配备工具)
deep_decomposition_agent = create_react_agent(
    model=model,
    tools=shared_tools,
    state_modifier="""你是深度拆解Agent。

    任务: 为紫色节点生成深度检验问题,暴露理解盲区。

    ⚠️ 重要: 立即调用write_to_canvas写入问题节点!
    """
)

# Agent 3: oral-explanation (配备工具)
oral_explanation_agent = create_react_agent(
    model=model,
    tools=shared_tools,
    state_modifier="""你是口语化解释Agent。

    任务: 生成800-1200词的口语化解释文档。

    ⚠️ 重要步骤:
    1. 生成解释内容
    2. 调用 create_md_file 创建文档
    3. 调用 write_to_canvas 创建蓝色FILE节点
    4. 调用 add_edge_to_canvas 连接原节点和FILE节点

    返回: 生成的文档路径
    """
)

# Agent 4: scoring-agent (配备工具)
scoring_agent = create_react_agent(
    model=model,
    tools=shared_tools,
    state_modifier="""你是评分Agent。

    任务: 对黄色节点进行4维评分 (准确性、具象性、完整性、原创性)。

    ⚠️ 重要: 评分后立即调用write_to_canvas更新节点颜色!

    颜色规则:
    - ≥80分 → color="2" (绿色)
    - 60-79分 → color="3" (紫色)
    - <60分 → color="1" (红色)

    返回: 评分结果和建议
    """
)

# ... 其他8个Agent (同样配备工具)

# Step 3: 构建LangGraph StateGraph
builder = StateGraph(CanvasLearningState)

# 添加Agent节点
builder.add_node("basic_decomposition", basic_decomposition_agent)
builder.add_node("deep_decomposition", deep_decomposition_agent)
builder.add_node("oral_explanation", oral_explanation_agent)
builder.add_node("scoring_agent", scoring_agent)
# ... 添加其他8个Agent节点

# Supervisor路由逻辑 (由canvas-orchestrator的plan决定)
def supervisor_router(state: CanvasLearningState) -> Command[Literal[
    "basic_decomposition",
    "deep_decomposition",
    "scoring_agent",
    "oral_explanation",
    # ... 其他Agent
    END
]]:
    """LangGraph Supervisor - 根据canvas-orchestrator的计划路由到对应Agent"""
    operation = state["operation"]

    routing_map = {
        "basic_decompose": "basic_decomposition",
        "deep_decompose": "deep_decomposition",
        "score": "scoring_agent",
        "oral_explain": "oral_explanation",
        # ... 其他映射
    }

    next_node = routing_map.get(operation, END)

    # 如果是并行操作,同时调度多个Agent
    if state.get("parallel_mode"):
        return Command(
            goto=[routing_map[op] for op in state["parallel_operations"]]
        )

    return Command(goto=next_node)

builder.add_conditional_edges(START, supervisor_router)

# 编译图
canvas_learning_graph = builder.compile()
```

#### 3.2.3 关键设计优势

**1. 实时节点生成 (0.5-1秒响应)**:
```python
# 用户调用: "基础拆解'逆否命题'"
# 0.5秒后: 第一个问题节点出现在Canvas
# 1.0秒后: 第二个问题节点出现
# ...
# 用户可以立即看到Agent在工作,不需要等待8-10秒
```

**2. FileLock并发安全** (详见Section 3.2.4):
```python
with FileLock(f"{canvas_path}.lock", timeout=10):
    # 多个Agent同时写入时,自动排队,避免数据冲突
    canvas_data = read_canvas(canvas_path)
    canvas_data["nodes"].append(new_node)
    write_canvas(canvas_path, canvas_data)
```

**3. 写入历史和回滚** (详见Section 3.2.5):
```python
state["write_history"] = [
    {"timestamp": "2025-01-15T14:30:01", "operation": "add_node", "node_id": "q1"},
    {"timestamp": "2025-01-15T14:30:02", "operation": "add_node", "node_id": "q2"},
    # ... 可以按时间回滚到任意版本
]
```

**4. 保留Epic 10.2性能优势**:
- LangGraph的异步并发调度与Epic 10.2的AsyncExecutionEngine兼容
- 最多12个Agent同时运行
- 8倍性能提升完全保留

#### 3.2.4 FileLock并发写入安全机制

**问题背景**: 多个Agent同时写入同一个Canvas文件时,可能造成数据冲突和丢失

**解决方案**: 跨平台文件锁机制

```python
import fcntl  # Unix/Linux/macOS
import msvcrt  # Windows
import platform
from contextlib import contextmanager

class FileLock:
    """跨平台文件锁实现"""

    def __init__(self, lock_file: str, timeout: int = 10):
        self.lock_file = lock_file
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        """获取锁"""
        import time
        start_time = time.time()

        # 创建锁文件
        self.fd = open(self.lock_file, 'w')

        # 根据平台选择锁机制
        if platform.system() == 'Windows':
            # Windows: msvcrt.locking
            while True:
                try:
                    msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except IOError:
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(f"无法获取文件锁: {self.lock_file}")
                    time.sleep(0.1)
        else:
            # Unix/Linux/macOS: fcntl.flock
            while True:
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError:
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(f"无法获取文件锁: {self.lock_file}")
                    time.sleep(0.1)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """释放锁"""
        if self.fd:
            if platform.system() == 'Windows':
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.fd, fcntl.LOCK_UN)

            self.fd.close()

            # 删除锁文件
            try:
                os.remove(self.lock_file)
            except:
                pass
```

**使用示例**:

```python
# Scenario: 3个Agent同时向Canvas写入节点

# Agent 1 (basic-decomposition)
with FileLock("离散数学.canvas.lock", timeout=10):
    canvas_data = read_canvas("离散数学.canvas")
    canvas_data["nodes"].append(question_node_1)
    write_canvas("离散数学.canvas", canvas_data)
# 释放锁

# Agent 2 (scoring-agent) - 等待锁释放
with FileLock("离散数学.canvas.lock", timeout=10):  # 等待0.1秒后获得锁
    canvas_data = read_canvas("离散数学.canvas")
    canvas_data["nodes"][0]["color"] = "2"  # 更新颜色
    write_canvas("离散数学.canvas", canvas_data)

# Agent 3 (oral-explanation) - 等待锁释放
with FileLock("离散数学.canvas.lock", timeout=10):
    canvas_data = read_canvas("离散数学.canvas")
    canvas_data["nodes"].append(file_node)
    write_canvas("离散数学.canvas", canvas_data)
```

**性能影响**:
- 锁等待时间: 平均 50-100ms (当其他Agent正在写入时)
- 锁开销: <10ms (无竞争时)
- **总影响**: 可接受,仍能保持0.5-1秒的首次节点出现时间

**错误处理**:
```python
try:
    with FileLock(lock_file, timeout=10):
        # ... 写入操作
except TimeoutError:
    # 超时后的fallback策略
    logger.error("文件锁超时,可能有其他操作正在进行")
    # 选项1: 重试
    # 选项2: 通知用户稍后重试
    # 选项3: 使用临时缓冲区,稍后合并
```

---

#### 3.2.5 写入历史和回滚机制

**目的**: 当Agent操作出错时,能快速回滚到之前的状态

**数据结构**:

```python
class WriteHistory:
    """写入历史记录"""

    def __init__(self):
        self.history: list[dict] = []
        self.snapshots: dict[str, dict] = {}

    def record(self, operation: str, canvas_path: str, node_id: str = None, **metadata):
        """记录写入操作"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,  # add_node, update_node, add_edge, create_file
            "canvas_path": canvas_path,
            "node_id": node_id,
            "metadata": metadata
        }
        self.history.append(entry)

    def snapshot(self, canvas_path: str, canvas_data: dict):
        """创建Canvas快照 (每次操作前)"""
        snapshot_key = f"{canvas_path}_{len(self.history)}"
        self.snapshots[snapshot_key] = {
            "timestamp": datetime.now().isoformat(),
            "canvas_data": copy.deepcopy(canvas_data)
        }

    def rollback_to_timestamp(self, target_timestamp: str):
        """回滚到指定时间点"""
        # 找到目标时间点之前的最后一个快照
        target_snapshot = None
        for snapshot_key, snapshot in self.snapshots.items():
            if snapshot["timestamp"] <= target_timestamp:
                target_snapshot = snapshot
            else:
                break

        if target_snapshot:
            return target_snapshot["canvas_data"]
        else:
            raise ValueError(f"无法找到时间点 {target_timestamp} 的快照")

    def rollback_n_steps(self, n: int):
        """回滚n步"""
        if n > len(self.history):
            raise ValueError(f"无法回滚{n}步,总共只有{len(self.history)}步操作")

        target_index = len(self.history) - n
        target_entry = self.history[target_index]
        return self.rollback_to_timestamp(target_entry["timestamp"])
```

**集成到Agent工具中**:

```python
@tool
def write_to_canvas(canvas_path: str, node_data: dict, config: RunnableConfig) -> str:
    """带历史记录的Canvas写入"""
    lock_file = f"{canvas_path}.lock"
    state = config.configurable.get("state")

    with FileLock(lock_file, timeout=10):
        # 1. 读取当前Canvas
        canvas_data = read_canvas(canvas_path)

        # 2. 创建快照 (操作前)
        if state and "write_history_manager" in state:
            state["write_history_manager"].snapshot(canvas_path, canvas_data)

        # 3. 执行写入
        canvas_data["nodes"].append(node_data)
        write_canvas(canvas_path, canvas_data)

        # 4. 记录操作
        if state and "write_history_manager" in state:
            state["write_history_manager"].record(
                operation="add_node",
                canvas_path=canvas_path,
                node_id=node_data["id"],
                node_type=node_data["type"],
                node_color=node_data.get("color")
            )

    return f"✅ 已添加节点 {node_data['id']}"
```

**回滚API**:

```python
# FastAPI端点
@app.post("/api/canvas/rollback")
async def rollback_canvas(
    canvas_path: str,
    rollback_steps: int = 1,
    rollback_to_timestamp: str = None
):
    """回滚Canvas操作"""
    # 从session中获取write_history_manager
    session = get_session(canvas_path)
    history_manager = session["write_history_manager"]

    if rollback_to_timestamp:
        restored_data = history_manager.rollback_to_timestamp(rollback_to_timestamp)
    else:
        restored_data = history_manager.rollback_n_steps(rollback_steps)

    # 写入恢复的数据
    write_canvas(canvas_path, restored_data)

    return {
        "success": True,
        "message": f"已回滚到 {rollback_steps} 步前",
        "restored_timestamp": history_manager.history[-rollback_steps]["timestamp"]
    }
```

**用户体验**:

```
Obsidian Plugin UI:

┌────────────────────────────────────────────┐
│  ⚠️ Agent操作出错                          │
│                                            │
│  错误信息: scoring-agent评分失败           │
│                                            │
│  [ 重试 ]  [ 回滚到错误前 ]  [ 取消 ]     │
└────────────────────────────────────────────┘

用户点击 [回滚到错误前]:
→ 调用 /api/canvas/rollback?rollback_steps=3
→ Canvas恢复到3步操作之前的状态
→ 用户可以重新尝试或修改操作
```

**性能开销**:
- 快照存储: 每个Canvas ~50KB,每次操作前创建快照
- 内存占用: 一个session ~10MB (假设20次操作)
- **优化策略**: 只保留最近50次操作的快照,超过后自动清理

---

### 3.3 数据迁移策略

**Phase 1: 双系统并行** (MVP)
```
CLI系统 ←────共享────→ FastAPI Backend
   ↓                        ↓
Vault文件              Obsidian Plugin
```

**Phase 2: LangGraph集成**
- 用LangGraph Supervisor替换直接函数调用
- 保留Epic 10.2异步并行性能

**Phase 3: 完整迁移**
- 所有功能迁移到Plugin
- 弃用CLI接口

### 3.4 部署架构 (Docker Compose)

```yaml
services:
  canvas-api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - VAULT_PATH=/vault
    volumes:
      - ${VAULT_PATH}:/vault
      - ./data:/data
    depends_on: [neo4j]

  neo4j:
    image: neo4j:5.15-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
```

### 3.5 Required Skills & Documentation Sources

#### Purpose
本章节列出项目所有技术栈的官方文档查询方式，确保Story开发时有准确的技术参考，**避免技术"幻觉"**（假设API存在但实际不存在的情况）。

#### Technology Stack Documentation Matrix

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
| **Epic 14: 艾宾浩斯复习系统迁移+UI集成** |
| 14 | Py-FSRS | 1.0.0 | PyPI | `pip install py-fsrs==1.0.0` | [GitHub](https://github.com/open-spaced-repetition/py-fsrs) |
| 14 | SQLite3 | Python内置 | Python Docs | `import sqlite3` | Built-in |
| 14 | Chart.js | 4.x | Context7 | `/chartjs/Chart.js` | (TBD) |
| **Epic 15-16: Neo4j Data Layer (Graphiti Backend)** |
| 15-16 | Neo4j Cypher | 2.5 | Context7 | `/websites/neo4j_cypher-manual_25` | 2,032 snippets |
| 15-16 | Neo4j Operations | Current | Context7 | `/websites/neo4j_operations-manual-current` | 4,940 snippets |
| 15-16 | Neo4j Python Driver | Latest | Context7 | `/neo4j/neo4j-python-driver` | 148 snippets |

#### Story Development Protocol

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

**For Epic 14 (艾宾浩斯复习系统迁移+UI集成)**:
```bash
# Py-FSRS使用GitHub README和源码
# GitHub: https://github.com/open-spaced-repetition/py-fsrs
# 本地代码参考: ebbinghaus_review.py (870行, 已有实现)

# 如需查询Chart.js文档 (用于统计图表)
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/chartjs/Chart.js",
    topic="line charts"
)
```

**For Epic 15-16 (Neo4j Data Layer / Graphiti Backend)**:
```bash
# 查询Neo4j文档
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/neo4j_cypher-manual_25",
    topic="pattern matching"
)
```

**Step 3: Verify API and Parameters**
参考 `.bmad-core/checklists/technical-verification-checklist.md` 进行完整验证。

#### Documentation Quality Standards

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

#### Known Technical Limitations

**LangGraph Agent System (Epic 12)**:
- ⚠️ **Memory System Complexity**: 三层记忆系统集成需要额外验证
- ⚠️ **Streaming Support**: 确认LangGraph Streaming API与Obsidian集成可行性
- 📖 **Reference**: See LangGraph Skill references/llms-full.md

**艾宾浩斯复习系统 (Epic 14)**:
- ⚠️ **算法迁移**: 从经典艾宾浩斯公式迁移到Py-FSRS需要数据迁移脚本
- ⚠️ **向后兼容**: 保留双算法支持,避免历史数据失效
- 📖 **Reference**: ebbinghaus_review.py (870行, 已有实现), Py-FSRS GitHub

**Neo4j Integration (Epic 15-16)**:
- ⚠️ **Performance**: 大规模知识图谱查询性能需要基准测试
- ⚠️ **Cypher Version**: 确认使用Cypher 2.5语法
- 📖 **Reference**: Context7 `/websites/neo4j_cypher-manual_25`

#### Updates and Maintenance

本章节应随项目进展更新：
- 🔄 **新增技术栈**: 添加到上表并确定查询方式
- 🔄 **版本升级**: 更新版本号和Library ID
- 🔄 **Skills补充**: 新生成的Skills及时补充到表中

**详细验证流程**: 参见 `.bmad-core/checklists/technical-verification-checklist.md`

---

### 3.6 LangGraph记忆系统集成设计

#### Purpose
本章节详细定义LangGraph框架层记忆系统（Checkpointer）与Canvas学习系统3层业务记忆系统（Graphiti + Temporal + Semantic）的集成架构，明确职责边界、触发时机、一致性保证和故障处理机制。

> **关键问题解决**:
> - ❓ **何时触发记忆存储**: 每个Canvas操作的6步精确时序
> - ❓ **如何避免冲突**: LangGraph Checkpointer vs 3层业务记忆的职责边界
> - ❓ **如何保证一致性**: 强一致性 vs 最终一致性模型
> - ❓ **如何处理失败**: 关键路径 vs 非关键路径的错误处理策略

---

#### 3.6.1 Checkpointer选型和配置

**生产环境推荐**: PostgresSaver（持久化到PostgreSQL数据库）

```python
# Epic 12: LangGraph checkpointer配置
from langgraph.checkpoint.postgres import PostgresSaver

# 数据库连接配置
DB_URI = "postgresql://user:pass@localhost:5432/canvas_learning"
checkpointer = PostgresSaver.from_conn_string(DB_URI)

# StateGraph编译时注入checkpointer
graph = builder.compile(checkpointer=checkpointer)
```

**开发/测试环境**: InMemorySaver（内存存储，快速但不持久化）

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**持久化内容**:
- Agent State完整快照（包括CanvasLearningState所有字段）
- 会话上下文（multi-turn dialogue context）
- 中间步骤和决策历史
- 工具调用记录

**不持久化**:
- Canvas文件内容（由Obsidian负责）
- Graphiti知识图谱数据（由Neo4j负责）
- 向量嵌入（由Semantic Memory负责）

---

#### 3.6.2 thread_id设计策略

**thread_id格式**: `canvas_{canvas_name}_{session_id}`

**组成部分**:
- `canvas_name`: Canvas文件名（去除`.canvas`扩展名）
- `session_id`: 唯一会话标识符（UUID v4）

**示例**:
```python
# Canvas文件: 笔记库/离散数学/离散数学.canvas
# Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
thread_id = "canvas_离散数学_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**设计原则**:
1. **唯一性**: 每个学习会话独立thread_id，避免状态混淆
2. **可追溯性**: 从thread_id可直接定位Canvas文件和会话
3. **隔离性**: 同一Canvas的不同会话互不干扰
4. **跨会话查询**: Temporal Memory可通过canvas_name查询历史所有会话

**生命周期**:
- **创建时机**: 用户首次调用Agent操作Canvas时
- **持续时间**: 整个学习会话（可能跨越多天）
- **终止时机**: 用户明确关闭会话或超时（默认30天无活动）
- **复用策略**: 同一Canvas的新会话创建新thread_id

---

#### 3.6.3 config参数结构定义

**完整config结构**:

```python
from typing import TypedDict
from pathlib import Path

class LangGraphConfig(TypedDict):
    """LangGraph调用配置参数"""
    configurable: dict  # LangGraph标准配置字段

# 具体实现
def create_langgraph_config(
    canvas_path: str,
    user_id: str,
    session_id: str
) -> LangGraphConfig:
    """生成LangGraph graph.invoke()所需的config参数

    Args:
        canvas_path: Canvas文件绝对路径
        user_id: 用户唯一标识符
        session_id: 会话唯一标识符（UUID v4）

    Returns:
        符合LangGraph标准的config字典
    """
    canvas_name = Path(canvas_path).stem
    thread_id = f"canvas_{canvas_name}_{session_id}"

    return {
        "configurable": {
            # LangGraph核心参数
            "thread_id": thread_id,  # 会话标识符

            # Canvas学习系统业务参数
            "canvas_path": canvas_path,  # Canvas文件路径
            "user_id": user_id,          # 用户ID
            "session_id": session_id,    # 会话ID

            # 可选扩展参数
            "checkpoint_ns": "canvas_learning",  # 命名空间隔离
            "checkpoint_id": None,  # 指定恢复的checkpoint ID（默认最新）
        }
    }
```

**使用示例**:

```python
# 创建新会话
config = create_langgraph_config(
    canvas_path="C:/Users/ROG/托福/笔记库/离散数学/离散数学.canvas",
    user_id="user_12345",
    session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
)

# 调用Agent
result = graph.invoke(
    {
        "canvas_path": config["configurable"]["canvas_path"],
        "operation": "decomposition",
        "concept": "逆否命题"
    },
    config=config  # 注入config
)
```

---

#### 3.6.4 graph编译示例（完整可运行代码）

**完整StateGraph定义**:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver

# Step 1: 定义State Schema
class CanvasLearningState(TypedDict):
    """Canvas学习系统State定义"""
    # 会话元信息
    canvas_path: str
    user_id: str
    session_id: str

    # 操作上下文
    operation: str  # "decomposition" | "explanation" | "scoring" | "verification"
    concept: str

    # Agent输出结果
    decomposition_results: list[str]  # basic-decomposition输出
    explanation_doc_path: str | None  # explanation agent输出
    scoring_result: dict | None       # scoring-agent输出

    # LangChain messages（用于对话历史）
    messages: Annotated[list, add_messages]

    # 最后操作记录
    last_operation: str
    last_timestamp: str

# Step 2: 定义Agent节点函数
def basic_decomposition_node(state: CanvasLearningState):
    """基础拆解Agent节点"""
    # 生成拆解问题
    questions = generate_decomposition_questions(state["concept"])

    # 写入Canvas（关键路径 - 必须成功）
    write_questions_to_canvas(
        state["canvas_path"],
        questions,
        config={"thread_id": f"canvas_{Path(state['canvas_path']).stem}_{state['session_id']}"}
    )

    # 存储到业务记忆系统（非关键路径 - 允许失败）
    try:
        store_to_graphiti(state["session_id"], "decomposition", questions)
        store_to_temporal(state["session_id"], "decomposition_completed", datetime.now())
    except Exception as e:
        logger.error(f"Memory storage failed: {e}")  # 仅记录，不中断流程

    # 返回更新的State（LangGraph自动持久化）
    return {
        **state,
        "decomposition_results": questions,
        "last_operation": "decomposition",
        "last_timestamp": datetime.now().isoformat()
    }

def scoring_node(state: CanvasLearningState):
    """评分Agent节点"""
    # 读取黄色节点内容
    yellow_nodes = read_yellow_nodes_from_canvas(state["canvas_path"])

    # 调用scoring-agent评分
    scoring_results = score_understanding(yellow_nodes)

    # 更新Canvas节点颜色（关键路径）
    update_node_colors_based_on_score(
        state["canvas_path"],
        scoring_results,
        config={"thread_id": f"canvas_{Path(state['canvas_path']).stem}_{state['session_id']}"}
    )

    # 存储评分结果到业务记忆（非关键路径）
    try:
        store_to_temporal(state["session_id"], "scoring_completed", datetime.now(), scoring_results)
    except Exception as e:
        logger.error(f"Scoring storage failed: {e}")

    return {
        **state,
        "scoring_result": scoring_results,
        "last_operation": "scoring",
        "last_timestamp": datetime.now().isoformat()
    }

# Step 3: 构建StateGraph
builder = StateGraph(CanvasLearningState)

# 添加节点
builder.add_node("decomposition", basic_decomposition_node)
builder.add_node("scoring", scoring_node)
builder.add_node("explanation", explanation_node)
builder.add_node("verification", verification_node)

# 定义路由逻辑
def route_operation(state: CanvasLearningState):
    """根据operation字段路由到对应Agent"""
    operation = state.get("operation")
    if operation == "decomposition":
        return "decomposition"
    elif operation == "scoring":
        return "scoring"
    elif operation == "explanation":
        return "explanation"
    elif operation == "verification":
        return "verification"
    else:
        return END

# 添加边
builder.add_conditional_edges(START, route_operation)
builder.add_edge("decomposition", END)
builder.add_edge("scoring", END)
builder.add_edge("explanation", END)
builder.add_edge("verification", END)

# Step 4: 编译graph并注入checkpointer
DB_URI = "postgresql://user:pass@localhost:5432/canvas_learning"
checkpointer = PostgresSaver.from_conn_string(DB_URI)

graph = builder.compile(checkpointer=checkpointer)

# Step 5: 调用示例
config = create_langgraph_config(
    canvas_path="C:/Users/ROG/托福/笔记库/离散数学/离散数学.canvas",
    user_id="user_12345",
    session_id=str(uuid.uuid4())
)

result = graph.invoke(
    {
        "canvas_path": config["configurable"]["canvas_path"],
        "user_id": config["configurable"]["user_id"],
        "session_id": config["configurable"]["session_id"],
        "operation": "decomposition",
        "concept": "逆否命题",
        "messages": []
    },
    config=config
)

# LangGraph自动将State持久化到PostgreSQL
```

**关键要点**:
1. ✅ State更新自动触发checkpointer持久化
2. ✅ 每次`graph.invoke()`调用都会创建新的checkpoint
3. ✅ 可通过`graph.get_state(config)`恢复历史State
4. ✅ Canvas操作在Node内部完成，确保原子性

---

#### 3.6.5 多轮对话支持

**场景描述**: 用户与Canvas学习系统进行多轮交互（例如：拆解 → 填写理解 → 评分 → 补充解释 → 再评分）

**实现机制**:

```python
# 第1轮：基础拆解
config_round1 = create_langgraph_config(
    canvas_path="离散数学.canvas",
    user_id="user_12345",
    session_id="session_abc"  # 同一session_id
)
result1 = graph.invoke({"operation": "decomposition", "concept": "逆否命题", ...}, config=config_round1)

# 第2轮：评分（复用相同thread_id）
config_round2 = create_langgraph_config(
    canvas_path="离散数学.canvas",
    user_id="user_12345",
    session_id="session_abc"  # 相同session_id → 相同thread_id
)
result2 = graph.invoke({"operation": "scoring", ...}, config=config_round2)

# 第3轮：补充解释（继续复用）
config_round3 = create_langgraph_config(
    canvas_path="离散数学.canvas",
    user_id="user_12345",
    session_id="session_abc"
)
result3 = graph.invoke({"operation": "explanation", "concept": "逆否命题", ...}, config=config_round3)

# 恢复历史State
historical_state = graph.get_state(config_round3)
print(historical_state.values)  # 包含所有历史操作结果
```

**关键优势**:
- ✅ **上下文保持**: 每轮对话都能访问之前的操作结果
- ✅ **状态累积**: `messages`字段记录完整对话历史
- ✅ **可回溯**: 可查询任意历史checkpoint
- ✅ **无缝衔接**: Agent可根据历史结果做更智能的决策

**与3层业务记忆配合**:
- **Checkpointer**: 短期会话上下文（当前学习会话）
- **Temporal Memory**: 长期学习历史（跨会话时间线）
- **Graphiti**: 知识关联网络（跨Canvas概念关系）
- **Semantic Memory**: 文档语义检索（跨会话文档查询）

---

#### 3.6.6 回滚机制增强

**传统Canvas操作回滚**（已实现）:
- 操作前备份Canvas JSON
- 失败时恢复备份
- 覆盖范围：单次操作

**LangGraph Checkpointer回滚**（新增）:
- 回滚到任意历史checkpoint
- 恢复完整Agent State
- 覆盖范围：整个学习会话

**完整回滚策略**:

```python
def rollback_to_checkpoint(
    canvas_path: str,
    session_id: str,
    checkpoint_id: str
):
    """回滚到指定checkpoint

    Args:
        canvas_path: Canvas文件路径
        session_id: 会话ID
        checkpoint_id: 目标checkpoint ID（从get_state_history获取）
    """
    config = create_langgraph_config(canvas_path, "user_id", session_id)
    config["configurable"]["checkpoint_id"] = checkpoint_id

    # Step 1: 恢复Agent State
    state = graph.get_state(config)

    # Step 2: 回滚Canvas文件（从备份）
    backup_path = f".canvas_backups/{Path(canvas_path).stem}_{checkpoint_id}.canvas"
    shutil.copy(backup_path, canvas_path)

    # Step 3: 回滚业务记忆（标记为已撤销）
    mark_memory_operations_as_reverted(
        session_id,
        after_timestamp=state.values["last_timestamp"]
    )

    return state.values

# 使用示例
# 查询历史checkpoints
config = create_langgraph_config("离散数学.canvas", "user_12345", "session_abc")
history = graph.get_state_history(config)

for h in history:
    print(f"Checkpoint ID: {h.config['configurable']['checkpoint_id']}")
    print(f"Timestamp: {h.values['last_timestamp']}")
    print(f"Operation: {h.values['last_operation']}")

# 回滚到第2个checkpoint
rollback_to_checkpoint("离散数学.canvas", "session_abc", history[1].config["configurable"]["checkpoint_id"])
```

**增强的一致性保证**:
- ✅ Canvas文件状态 ↔ LangGraph State: 强一致性
- ✅ Canvas文件状态 ↔ Graphiti/Temporal: 最终一致性（允许延迟）
- ✅ 回滚操作: Canvas + State同步回滚，业务记忆标记撤销

##### 备份文件组织规范

**问题背景**:
为避免备份文件与工作Canvas文件混在一起造成Obsidian文件浏览器显示凌乱，所有备份文件统一存放在专用文件夹。

**备份根目录**:
```python
# 获取Vault根目录
def get_vault_root(canvas_path: str) -> Path:
    """
    从Canvas路径向上查找，直到找到.obsidian文件夹的父目录
    """
    current = Path(canvas_path).resolve()
    while current.parent != current:
        if (current / ".obsidian").exists():
            return current
        current = current.parent
    raise ValueError(f"无法找到Vault根目录: {canvas_path}")

# 备份文件夹路径
vault_root = get_vault_root(canvas_path)
backup_dir = vault_root / ".canvas_backups"

# 系统首次运行时创建
if not backup_dir.exists():
    backup_dir.mkdir(parents=True, exist_ok=True)
```

**备份文件路径计算**:
```python
def get_backup_path(canvas_path: str, checkpoint_id: str) -> Path:
    """
    计算备份文件的完整路径

    Args:
        canvas_path: 原Canvas文件路径（可以是Vault中任意位置）
        checkpoint_id: LangGraph checkpoint ID

    Returns:
        备份文件路径: {Vault根目录}/.canvas_backups/{canvas_name}_{checkpoint_id}.canvas
    """
    vault_root = get_vault_root(canvas_path)
    canvas_name = Path(canvas_path).stem

    backup_path = vault_root / ".canvas_backups" / f"{canvas_name}_{checkpoint_id}.canvas"
    return backup_path

# 示例
canvas_path = "/path/to/vault/笔记库/离散数学/离散数学.canvas"
checkpoint_id = "ckpt_1699999999"
backup_path = get_backup_path(canvas_path, checkpoint_id)
# 结果: /path/to/vault/.canvas_backups/离散数学_ckpt_1699999999.canvas
```

**备份创建时机（LangGraph Checkpointer集成）**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

class CanvasBackupCheckpointer(PostgresSaver):
    """扩展的Checkpointer，同步创建Canvas文件备份"""

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata) -> RunnableConfig:
        # Step 1: 调用父类保存checkpoint到数据库
        new_config = super().put(config, checkpoint, metadata)

        # Step 2: 同步创建Canvas文件备份
        canvas_path = config["configurable"].get("canvas_path")
        if canvas_path:
            checkpoint_id = new_config["configurable"]["checkpoint_id"]
            backup_path = get_backup_path(canvas_path, checkpoint_id)

            # 复制当前Canvas文件到备份目录
            shutil.copy(canvas_path, backup_path)

            # Step 3: 执行备份清理
            cleanup_old_backups(canvas_path, keep_count=50)

        return new_config
```

**备份清理策略**:
```python
def cleanup_old_backups(canvas_path: str, keep_count: int = 50):
    """
    清理旧的备份文件，保留最近N个

    Args:
        canvas_path: Canvas文件路径
        keep_count: 保留的备份数量（默认50）
    """
    vault_root = get_vault_root(canvas_path)
    canvas_name = Path(canvas_path).stem
    backup_dir = vault_root / ".canvas_backups"

    # 查找该Canvas的所有备份（按修改时间排序）
    backups = sorted(
        backup_dir.glob(f"{canvas_name}_*.canvas"),
        key=lambda p: p.stat().st_mtime,
        reverse=True  # 最新的在前
    )

    # 删除超过keep_count的备份
    for backup in backups[keep_count:]:
        # 检查是否被手动标记为"受保护"
        if not is_protected_backup(backup):
            backup.unlink()
            logger.info(f"🗑️ 已删除旧备份: {backup.name}")

def is_protected_backup(backup_path: Path) -> bool:
    """
    检查备份是否被用户标记为受保护

    实现方式：
    - 在备份文件同级目录查找 {backup_name}.protected 标记文件
    - 或在数据库中查询保护标记
    """
    marker_file = backup_path.with_suffix(".canvas.protected")
    return marker_file.exists()
```

**Obsidian文件浏览器隐藏配置**:
```typescript
// Obsidian Plugin中的配置（Story 13.1实施）
// 文件: src/main.ts

export default class CanvasLearningPlugin extends Plugin {
    async onload() {
        // 注册.canvas_backups为系统文件夹（不在文件浏览器显示）
        this.registerEvent(
            this.app.vault.on('create', (file) => {
                if (file.path.startsWith('.canvas_backups/')) {
                    // 标记为系统文件，隐藏显示
                    this.app.vault.adapter.setHidden(file.path, true);
                }
            })
        );
    }
}
```

**用户手动保护备份（Obsidian UI）**:
```typescript
// 右键菜单: "保护此备份"（Story 13.5实施）
this.registerEvent(
    this.app.workspace.on('file-menu', (menu, file) => {
        if (file.path.startsWith('.canvas_backups/') && file.extension === 'canvas') {
            menu.addItem((item) => {
                item
                    .setTitle('保护此备份 🔒')
                    .setIcon('shield')
                    .onClick(async () => {
                        // 创建.protected标记文件
                        const markerPath = file.path + '.protected';
                        await this.app.vault.adapter.write(markerPath, '');
                        new Notice('✅ 备份已标记为受保护，不会被自动删除');
                    });
            });
        }
    })
);
```

**验收标准（补充到Story 12.1）**:
- ✅ 备份文件夹`.canvas_backups/`在Vault根目录正确创建
- ✅ 备份文件按规范命名：`{canvas_name}_{checkpoint_id}.canvas`
- ✅ 每次checkpoint创建时自动生成对应备份文件
- ✅ 备份清理机制正常工作：超过50个自动删除最旧的（跳过受保护的）
- ✅ 备份文件夹在Obsidian文件浏览器中默认隐藏
- ✅ 回滚功能正确读取备份文件：`rollback_to_checkpoint()`能找到并恢复备份

**性能影响**:
- 备份文件复制: ~10-50ms（取决于Canvas大小，通常<100KB）
- 备份清理: ~5-10ms（仅在超过50个时触发）
- 总体影响: 可忽略（<100ms per checkpoint）

---

#### 3.6.7 性能考虑

**Checkpointer写入性能**:
- PostgresSaver: ~50ms per checkpoint（包含序列化 + 数据库写入）
- InMemorySaver: ~5ms per checkpoint（纯内存操作）

**优化策略**:

**1. 批量操作优化**
```python
# ❌ 低效：每个节点单独invoke
for node_id in node_ids:
    graph.invoke({"operation": "scoring", "node_id": node_id}, config)
    # 每次都创建新checkpoint（假设100个节点 = 100次数据库写入）

# ✅ 高效：批量处理
graph.invoke({
    "operation": "batch_scoring",
    "node_ids": node_ids  # 一次性传入所有节点
}, config)
# 仅1次checkpoint写入
```

**2. 异步持久化**
```python
# LangGraph内部已实现异步写入，无需额外配置
# checkpointer.put()是非阻塞的
```

**3. Checkpoint清理策略**
```python
# 定期清理旧checkpoints（保留最近30天）
def cleanup_old_checkpoints(session_id: str, days=30):
    cutoff_date = datetime.now() - timedelta(days=days)
    # PostgresSaver提供TTL机制
    checkpointer.delete_checkpoints_before(session_id, cutoff_date)
```

**性能基准**（单次操作）:
- Canvas读取: ~10ms
- Agent节点执行: ~200ms（不含LLM调用）
- Canvas写入: ~15ms
- Checkpointer持久化: ~50ms（PostgresSaver）
- Graphiti存储: ~100ms（异步，不阻塞）
- **总延迟**: ~275ms（用户感知）

---

#### 3.6.8 与Epic 16跨Canvas关联的配合

**Epic 16需求**: 跨Canvas知识关联查询（例如：查询"线性代数"和"离散数学"中关于"矩阵"的所有节点）

**LangGraph Checkpointer职责**:
- ❌ **不负责**跨Canvas查询（这是Graphiti的职责）
- ✅ **负责**单个Canvas会话的State管理
- ✅ **负责**提供当前Canvas的上下文给Graphiti

**协作机制**:

```python
# Epic 16 Story: 跨Canvas关联查询
def cross_canvas_query_node(state: CanvasLearningState):
    """跨Canvas查询Agent节点"""
    query = state["query"]  # "查询所有Canvas中关于'矩阵'的节点"

    # Step 1: 从当前State获取上下文
    current_canvas = state["canvas_path"]
    current_concept = state["concept"]

    # Step 2: 调用Graphiti进行跨Canvas查询
    related_nodes = graphiti_client.search_nodes(
        query=query,
        filters={
            "concept": current_concept,
            "exclude_canvas": current_canvas  # 排除当前Canvas
        },
        limit=10
    )

    # Step 3: 将结果整合到当前Canvas
    for node in related_nodes:
        add_reference_node_to_canvas(
            current_canvas,
            node,
            link_type="cross_canvas_reference"
        )

    # Step 4: 更新State（LangGraph持久化）
    return {
        **state,
        "cross_canvas_results": related_nodes,
        "last_operation": "cross_canvas_query"
    }
```

**数据流**:
```
LangGraph State (当前Canvas上下文)
    ↓
Graphiti Knowledge Graph (跨Canvas语义查询)
    ↓
LangGraph State (查询结果写回)
    ↓
LangGraph Checkpointer (持久化查询历史)
```

**关键设计**:
- ✅ Checkpointer记录"在哪个Canvas、什么时候、查询了什么"
- ✅ Graphiti提供跨Canvas的语义关联能力
- ✅ 两者通过State传递数据，职责清晰

---

#### 3.6.9 验收标准

**功能验收**:
- ✅ **AC 1**: PostgresSaver和InMemorySaver均可正常工作
- ✅ **AC 2**: thread_id格式符合`canvas_{name}_{session_id}`规范
- ✅ **AC 3**: config参数包含所有必需字段（thread_id, canvas_path, user_id, session_id）
- ✅ **AC 4**: graph.compile(checkpointer=checkpointer)成功编译
- ✅ **AC 5**: 多轮对话可复用相同thread_id并累积State
- ✅ **AC 6**: graph.get_state()可恢复历史State
- ✅ **AC 7**: 回滚操作同步恢复Canvas文件和LangGraph State

**性能验收**:
- ✅ **AC 8**: 单次checkpoint写入 < 100ms（PostgresSaver）
- ✅ **AC 9**: 批量操作（10个节点）总耗时 < 3秒
- ✅ **AC 10**: checkpoint清理脚本可正常运行

**一致性验收**:
- ✅ **AC 11**: Canvas操作失败时，checkpointer不创建新checkpoint
- ✅ **AC 12**: 业务记忆存储失败时，不影响Canvas操作成功
- ✅ **AC 13**: 回滚后Canvas文件、LangGraph State、业务记忆三者一致

**文档验收**:
- ✅ **AC 14**: 代码示例可直接运行
- ✅ **AC 15**: 职责边界表格完整清晰
- ✅ **AC 16**: 所有API调用已通过Context7/Skills验证

**集成验收**（与Epic 12 Stories配合）:
- ✅ **AC 17**: Story 12.1 checkpointer配置可被Story 12.2调用
- ✅ **AC 18**: Story 12.5可使用本章节定义的config结构
- ✅ **AC 19**: Story 12.7测试用例覆盖checkpointer所有场景

---

## 📊 Section 4: Epic和Story结构

### Epic概览

| Epic | 名称 | Story数 | 优先级 | 估算时间 |
|------|------|---------|--------|---------|
| **Epic 0** | **技术文档验证基础设施** | **4** | **P0 (BLOCKER)** | **0.5天** |
| Epic 11 | FastAPI后端基础架构 | 6 | P0 | 2-3周 |
| Epic 12 | LangGraph多Agent编排 | 7 | P0 | 3-4周 |
| Epic 13 | Obsidian Plugin核心功能 | 7 | P0 | 3-4周 |
| Epic 14 | 艾宾浩斯复习系统迁移+UI集成 **(v1.1.6扩展)** | **12** | P0 | **4-6.5周** (迁移+3层记忆整合) |
| Epic 15 | 检验白板进度追踪 | 5 | P1 | 2周 |
| Epic 16 | 跨Canvas关联学习 | 7 | P1 | 3周 |
| Epic 17 | 性能优化和监控 | 6 | P2 | 2周 |
| Epic 18 | 数据迁移和回滚 | 5 | P1 | 1-2周 |

**总时间估算**: **20.5-24.5周** (5-6个月) - *v1.1.6调整: +2.5周*
**MVP时间**: **10.5-13.5周** (2.5-3.5个月) - *v1.1.6调整: +2.5周*

**v1.1.6变更影响**:
- Epic 14新增4个Story (14.9-14.12): 3层记忆系统整合
- 工作量增加: +2-2.5周
- 核心价值: 实现100%真实数据源，消除模拟数据

---

### Epic 0: 技术文档验证基础设施

**Epic ID**: Epic 0
**优先级**: P0 (BLOCKER)
**预计时间**: 0.5天 (4小时)
**依赖**: 无
**阻塞**: Epic 11, 12, 13, 15, 16

#### 目标
建立零幻觉开发的技术基础设施，确保所有后续Epic的开发都基于官方文档验证。

#### Story列表

| Story ID | Story名称 | 预计时间 |
|----------|----------|---------|
| Story 0.1 | 验证Context7文档访问 | 0.5小时 |
| Story 0.2 | 验证本地Skills可用性 | 0.5小时 |
| Story 0.3 | 创建技术验证示例Story | 2小时 |
| Story 0.4 | 更新PRD文档 | 1小时 |

#### 关键交付物
- ✅ Context7文档访问验证报告 (`docs/verification/context7-access-test.md`)
- ✅ 本地Skills验证报告 (`docs/verification/local-skills-test.md`)
- ✅ 示例Story模板 (`docs/examples/story-12-1-verification-demo.md`)
- ✅ 更新后的PRD和README (本文档)

#### 成功标准
- Context7可访问所有必需文档（FastAPI, Neo4j）
- 本地Skills全部可用且返回正确文档
- 示例Story已创建并可作为后续Stories的参考模板
- PRD已更新包含Section 1.X技术验证协议
- 所有Agent（SM/Dev）理解技术验证新流程

**详细文档**: `docs/prd/EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md`

---

### Epic 11: FastAPI后端基础架构搭建

**Epic ID**: Epic 11
**优先级**: P0
**预计时间**: 2周 (43小时)
**依赖**: Epic 0（技术验证基础设施）
**阻塞**: Epic 12, 13, 14

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/fastapi_tiangolo` (22,734 snippets)
- 查询主题示例: "dependency injection", "async operations", "APIRouter"

**验证检查点**:
- SM Agent编写Story时必须查询并记录API用法
- Dev Agent开发时必须在代码中添加文档引用注释
- Code Review必须验证所有API调用的正确性

#### 目标
搭建高性能、可扩展的FastAPI后端基础架构，作为Canvas学习系统Web化的核心API层。采用4层架构设计（API Layer → Service Layer → Core Layer → Infrastructure Layer），实现19个RESTful API endpoints，集成现有canvas_utils.py，支持异步操作和后台任务。

#### Story列表

| Story ID | Story名称 | 预计时间 | 优先级 |
|----------|----------|---------|--------|
| Story 11.1 | FastAPI应用初始化和基础配置 | 4-6小时 | P0 |
| Story 11.2 | 路由系统和APIRouter配置 | 5-7小时 | P0 |
| Story 11.3 | 依赖注入系统设计 | 6-8小时 | P0 |
| Story 11.4 | 中间件和错误处理 | 5-7小时 | P1 |
| Story 11.5 | 异步操作和后台任务 | 6-9小时 | P1 |
| Story 11.6 | API文档和测试框架 | 4-6小时 | P1 |

**总时间**: 30-43小时

#### 核心架构

**4层架构设计**:
```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理（Pydantic Settings）
│   ├── dependencies.py         # 全局依赖项（DI）
│   ├── api/v1/endpoints/       # API endpoints
│   │   ├── canvas.py           # Canvas操作 (6 endpoints)
│   │   ├── agents.py           # Agent调用 (9 endpoints)
│   │   └── review.py           # 检验白板 (3 endpoints)
│   ├── models/                 # Pydantic模型 (31个)
│   ├── services/               # 业务逻辑层
│   ├── core/                   # 核心层（canvas_utils.py集成）
│   └── middleware/             # 中间件
└── tests/                      # 测试
```

#### 关键交付物

**规划文档** (已完成):
- ✅ Sprint Kick-off: `docs/SPRINT-KICKOFF-EPIC-11.md`
- ✅ Epic 11详细规划: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`
- ✅ 技术架构设计: `docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md`
- ✅ API接口规范: `docs/api/EPIC-11-API-SPECIFICATION.md`
- ✅ 数据模型设计: `docs/architecture/EPIC-11-DATA-MODELS.md`
- ✅ PM-SM交接文档: `docs/PM-TO-SM-HANDOFF-EPIC-11.md`

**代码交付物** (待开发):
- [ ] FastAPI应用核心代码（`app/main.py`, `app/config.py`）
- [ ] 19个API endpoints实现
- [ ] 31个Pydantic数据模型
- [ ] 中间件系统（日志、错误处理、CORS）
- [ ] 异步服务层
- [ ] pytest测试套件（覆盖率 ≥ 85%）

#### API Endpoints概览

**Canvas操作** (6 endpoints):
- `GET /api/v1/canvas/{canvas_name}` - 读取Canvas文件
- `POST /api/v1/canvas/{canvas_name}/nodes` - 创建节点
- `PUT /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 更新节点
- `DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 删除节点
- `POST /api/v1/canvas/{canvas_name}/edges` - 创建边
- `DELETE /api/v1/canvas/{canvas_name}/edges/{edge_id}` - 删除边

**Agent调用** (9 endpoints):
- `POST /api/v1/agents/decompose/basic` - 基础拆解
- `POST /api/v1/agents/decompose/deep` - 深度拆解
- `POST /api/v1/agents/score` - 评分
- `POST /api/v1/agents/explain/oral` - 口语化解释
- `POST /api/v1/agents/explain/clarification` - 澄清路径
- `POST /api/v1/agents/explain/comparison` - 对比表
- `POST /api/v1/agents/explain/memory` - 记忆锚点
- `POST /api/v1/agents/explain/four-level` - 四层次解释
- `POST /api/v1/agents/explain/example` - 例题教学

**检验白板** (3 endpoints):
- `POST /api/v1/review/generate` - 生成检验白板
- `GET /api/v1/review/{canvas_name}/progress` - 获取检验进度
- `POST /api/v1/review/sync` - 同步检验结果

**健康检查** (1 endpoint):
- `GET /api/v1/health` - 健康检查

#### 数据模型概览

**31个Pydantic模型**, 分为4类:
1. **Canvas模型** (10个): `NodeBase`, `NodeCreate`, `NodeUpdate`, `NodeRead`, `EdgeBase`, `EdgeCreate`, `EdgeRead`, `CanvasData`, `CanvasMeta`, `CanvasResponse`
2. **Agent模型** (12个): `DecomposeRequest`, `DecomposeResponse`, `ScoreRequest`, `ScoreResponse`, `ScoreDimensions`, `ScoreFeedback`, `ExplainRequest`, `ExplainResponse`, `AgentType`, `AgentMeta`, `AgentRecommendation`, `ErrorDetail`
3. **Review模型** (5个): `ReviewGenerateRequest`, `ReviewGenerateResponse`, `ReviewProgressResponse`, `ReviewSyncRequest`, `ReviewSyncResponse`
4. **Common模型** (4个): `SuccessResponse`, `ErrorResponse`, `PaginationMeta`, `HealthCheckResponse`

#### 技术栈

**核心框架**:
- FastAPI 0.104+
- Pydantic 2.5+
- Uvicorn 0.24+

**开发工具**:
- pytest 7.4+
- pytest-asyncio
- httpx (async client for testing)
- python-dotenv

**架构模式**:
- 依赖注入（`Depends()`）
- 异步优先（`async/await`）
- API版本控制（`/api/v1/`）
- Pydantic Settings配置管理

#### 成功标准

**功能验收**:
- ✅ 19个API endpoints全部实现并可正常调用
- ✅ 所有endpoints返回符合规范的JSON响应
- ✅ 错误处理覆盖所有预期错误场景（400/404/500）
- ✅ Canvas文件读写操作成功
- ✅ Agent调用成功返回结果

**技术验收**:
- ✅ 所有API调用已通过Context7验证
- ✅ 代码包含文档引用注释
- ✅ 依赖注入系统正常工作
- ✅ 中间件正确处理请求/响应
- ✅ 异步操作无阻塞

**测试验收**:
- ✅ pytest测试覆盖率 ≥ 85%
- ✅ 所有API endpoints有对应的测试用例
- ✅ 异步操作有集成测试
- ✅ 错误处理有单元测试

**文档验收**:
- ✅ FastAPI自动生成的Swagger文档可访问
- ✅ API endpoints有完整的docstring
- ✅ 所有技术实现可追溯到Context7查询

**性能验收**:
- ✅ 单个API请求响应时间 < 500ms
- ✅ Canvas文件读取 < 200ms
- ✅ Agent调用 < 5秒（不含Agent执行时间）

**集成验收**（与Epic 12配合）:
- ✅ FastAPI endpoints可被Epic 12 LangGraph调用
- ✅ 依赖注入系统支持LangGraph集成
- ✅ 异步操作不阻塞LangGraph workflow

**详细文档**: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`

---

### Epic 12: LangGraph多Agent编排系统 (工具配备模式)

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Local Skill: `@langgraph` (952页完整文档)
- Local Skill: `@graphiti` (完整框架文档)

**验证检查点**:
- SM Agent必须激活Skills并记录查询结果
- Dev Agent必须在代码中添加Skill引用注释
- Code Review必须验证StateGraph和节点创建的正确性

---

**Story序列**:
- **Story 12.1**: LangGraph StateGraph定义和写入历史机制 + **LangGraph Checkpointer集成**
  - 定义CanvasLearningState (含write_history字段)
  - 实现WriteHistory类
  - **[新增] 定义LangGraph checkpointer配置**:
    - checkpointer类型选型: PostgresSaver (生产) / InMemorySaver (开发)
    - thread_id生成策略: `canvas_{canvas_name}_{session_id}`
    - config参数结构定义 (包含thread_id, canvas_path, user_id, session_id)
  - **[新增] graph编译配置**:
    ```python
    from langgraph.checkpoint.postgres import PostgresSaver

    DB_URI = "postgresql://user:pass@localhost:5432/canvas_learning"
    checkpointer = PostgresSaver.from_conn_string(DB_URI)

    graph = builder.compile(checkpointer=checkpointer)
    ```
  - 验收:
    - State可正确传递
    - 写入历史正常记录
    - **[新增] checkpointer成功持久化对话状态**
    - **[新增] 可通过thread_id恢复之前的对话上下文**
    - **[SCP-003新增] Canvas备份文件组织规范**:
      - ✅ 备份文件夹`.canvas_backups/`在Vault根目录正确创建
      - ✅ 备份文件按规范命名：`{canvas_name}_{checkpoint_id}.canvas`
      - ✅ 每次checkpoint创建时自动生成对应备份文件
      - ✅ 备份清理机制正常工作：超过50个自动删除最旧的（跳过受保护的）
      - ✅ 备份文件夹在Obsidian文件浏览器中默认隐藏（需Story 13.1配合）
      - ✅ 回滚功能正确：`rollback_to_checkpoint()`能找到并恢复备份
      - ✅ 性能达标：备份创建+清理总耗时 <100ms

- **Story 12.2**: 共享Tools实现 (FileLock + 写入历史 + 3层记忆系统集成 + **LangGraph记忆系统协调**)
  - ✅ 实现write_to_canvas工具 (带FileLock和快照)
  - ✅ 实现create_md_file_for_canvas工具 (支持Vault相对路径) - **修复需求1**
  - 实现add_edge_to_canvas工具
  - 实现update_ebbinghaus工具
  - 实现query_graphiti_context工具
  - ✅ 实现store_to_graphiti_memory工具 - **修复需求2**
  - ✅ 实现store_to_temporal_memory工具 - **修复需求2**
  - ✅ 实现store_to_semantic_memory工具 - **修复需求2**
  - ✅ 实现query_graphiti_for_verification工具 - **修复需求3**
  - 跨平台FileLock测试 (Windows/macOS/Linux)
  - ✅ 文件路径可用性测试（验证Obsidian可正常打开生成的.md文件）
  - ✅ 记忆系统调度测试（验证在正确时机触发记忆存储）
  - 验收: 所有工具可并发调用,数据一致性100%

  **⚠️ 记忆系统调度时机矩阵** (修复需求2 + **精确化时序**):

  | Canvas操作 | Graphiti | Temporal | Semantic | LangGraph Checkpointer | 精确时序 |
  |-----------|----------|----------|----------|----------------------|---------|
  | 问题拆解 | ✅ | ✅ | ❌ | ✅ (自动) | 1. write_to_canvas完成 → Canvas文件修改<br>2. store_to_graphiti_memory → 知识图谱更新<br>3. store_to_temporal_memory → 时序事件记录<br>4. Agent返回new_state → LangGraph自动持久化到checkpointer |
  | 评分 | ✅ | ✅ | ❌ | ✅ (自动) | 1. 计算评分<br>2. write_to_canvas更新颜色 → Canvas文件修改<br>3. store_to_graphiti_memory(scoring_result) → 评分存入知识图谱<br>4. store_to_temporal_memory(score_event) → 时序记录<br>5. **track_learning_behavior(operation_type="scoring")** → 记录行为数据<br>6. **如果评分≥60**: EbbinghausReviewSystem.add_concept_for_review()<br>7. Agent返回new_state → LangGraph持久化 |
  | 生成解释文档 | ✅ | ✅ | ✅ | ✅ (自动) | 1. create_md_file_for_canvas → 生成.md文件<br>2. write_to_canvas创建FILE节点 → Canvas引用文件<br>3. store_to_graphiti_memory → 文档关联存入图谱<br>4. store_to_semantic_memory → 文档向量化<br>5. store_to_temporal_memory → 时序记录<br>6. Agent返回new_state → LangGraph持久化 |
  | 生成检验白板 | ✅ (查询+存储) | ✅ | ❌ | ✅ (自动) | 1. query_graphiti_for_verification → 查询上下文<br>2. 传递给verification-question-agent<br>3. write_to_canvas创建检验白板<br>4. store_to_graphiti_memory → 存储<br>5. Agent返回new_state → LangGraph持久化 |
  | 跨Canvas关联 | ✅ | ✅ | ❌ | ✅ (自动) | 1. 创建关联关系<br>2. store_to_graphiti_memory → 跨Canvas关系存入图谱<br>3. store_to_temporal_memory → 关联事件记录<br>4. Agent返回new_state → LangGraph持久化 |
  | **艾宾浩斯复习触发** (v1.1.6新增) | ✅ (查询) | ✅ (查询) | ✅ (查询) | ❌ | 1. **query_temporal_learning_behavior** → 检测未访问概念<br>2. **query_graphiti_concept_network** → 检测知识断层<br>3. **query_semantic_document_interactions** → 检测隐性需求<br>4. **合并触发列表** → EbbinghausReviewSystem批量添加<br>5. **optimize_fsrs_parameters_from_behavior** → 定期参数优化 |

  **[新增] 工具间协调机制**:

  **LangGraph Checkpointer职责**:
  - ✅ 存储Agent执行的中间状态（CanvasLearningState对象）
  - ✅ 支持多轮对话上下文持久化（thread_id）
  - ✅ 提供回滚能力（通过checkpoint ID和timestamp）
  - ⚠️ **不存储**：Canvas文件内容、知识图谱、学习事件

  **Graphiti知识图谱职责**:
  - ✅ 存储Canvas节点语义关系（概念关联、前置知识）
  - ✅ 支持跨Canvas查询和推荐
  - ⚠️ **不存储**：Agent执行状态、文档向量

  **Temporal时序记忆职责**:
  - ✅ 存储学习事件时间线（拆解时间、评分时间）
  - ✅ 支持学习进度分析和统计
  - ⚠️ **不存储**：文档内容、知识图谱

  **Semantic语义记忆职责**:
  - ✅ 存储AI生成文档的向量表示
  - ✅ 支持语义相似度检索
  - ⚠️ **不存储**：Canvas节点、知识图谱

  **[新增] 错误处理策略**:
  ```python
  def agent_node(state: CanvasLearningState):
      try:
          # Step 1: Canvas操作（关键路径）
          write_to_canvas(...)  # 失败 → 抛出异常，LangGraph回滚

          # Step 2: 记忆存储（非关键路径，最终一致性）
          try:
              store_to_graphiti_memory(...)
              store_to_temporal_memory(...)
          except MemoryStorageError as e:
              # 记录日志，不阻塞Canvas操作
              logger.error(f"Memory storage failed: {e}")
              # 可选：异步重试机制

          return new_state  # LangGraph自动持久化到checkpointer
      except CanvasOperationError as e:
          # Canvas操作失败 → 整个操作失败
          raise
  ```

  **调度规则说明**:
  1. **Graphiti (知识图谱)**: 所有Canvas操作都应存储，用于构建学习知识网络
  2. **Temporal (时序记忆)**: 所有Canvas操作都应存储，用于追踪学习历程
  3. **Semantic (语义记忆)**: 仅存储解释文档，用于文档向量检索
  4. **[新增] LangGraph Checkpointer**: 框架自动持久化Agent State，无需手动调用

  **[新增] 代码集成示例** (basic-decomposition Agent完整实现):
  ```python
  def basic_decomposition_agent_node(state: CanvasLearningState):
      session_id = state.session_id
      canvas_path = state.canvas_path
      config = state.config  # 包含thread_id

      # Step 1: 生成问题
      questions = generate_questions(state.concept)

      # Step 2: 写入Canvas（关键路径）
      for q in questions:
          write_to_canvas(canvas_path, {
              "id": generate_id(),
              "type": "text",
              "text": q,
              "color": "1",  # 红色问题节点
              "x": calc_x(), "y": calc_y()
          }, config)

      # Step 3: 存储到记忆系统（非关键路径）
      try:
          store_to_graphiti_memory(session_id, "decomposition", canvas_path, {
              "concept": state.concept,
              "questions": questions,
              "agent": "basic-decomposition"
          }, config)

          store_to_temporal_memory(session_id, "decomposition_completed",
              datetime.now(), {
                  "concept": state.concept,
                  "question_count": len(questions)
              }, config)
      except Exception as e:
          logger.error(f"Memory storage failed: {e}")

      # Step 4: 返回新State（LangGraph自动持久化到checkpointer）
      return CanvasLearningState(
          ...state,
          last_operation="decomposition",
          decomposition_results=questions
      )
  ```

- **Story 12.3**: 12个工具配备Agent节点创建
  - 使用create_react_agent创建12个Agent
  - 每个Agent配备shared_tools
  - 配置state_modifier (明确指示立即调用写入工具)
  - 验收: 每个Agent能独立调用工具,首个节点<1秒出现

- **Story 12.4**: canvas-orchestrator (Layer 3) 集成
  - 保留原有自然语言意图识别逻辑
  - 实现execute_with_langgraph方法
  - 将canvas-orchestrator的计划转换为LangGraph State
  - 验收: 用户命令正确路由到对应Agent

- **Story 12.5**: LangGraph Supervisor路由逻辑 (Layer 4) + **Checkpointer集成**
  - 实现supervisor_router函数
  - 支持单Agent和并行Agent调度
  - 实现条件路由 (根据operation类型)
  - **[新增] graph编译时配置checkpointer**:
    ```python
    from langgraph.checkpoint.postgres import PostgresSaver

    checkpointer = PostgresSaver.from_conn_string(DB_URI)
    supervisor_graph = builder.compile(checkpointer=checkpointer)
    ```
  - **[新增] config参数生成**:
    ```python
    def create_langgraph_config(canvas_path: str, user_id: str, session_id: str):
        canvas_name = Path(canvas_path).stem
        thread_id = f"canvas_{canvas_name}_{session_id}"

        return {
            "configurable": {
                "thread_id": thread_id,
                "canvas_path": canvas_path,
                "user_id": user_id,
                "session_id": session_id
            }
        }
    ```
  - **[新增] 多轮对话支持**:
    ```python
    # 第一轮：拆解问题
    config1 = create_langgraph_config("离散数学.canvas", "user123", "session_001")
    supervisor_graph.invoke({"operation": "decomposition", ...}, config1)

    # 第二轮：评分（继承第一轮上下文）
    config2 = create_langgraph_config("离散数学.canvas", "user123", "session_001")  # 相同thread_id
    supervisor_graph.invoke({"operation": "scoring", ...}, config2)
    # ↑ LangGraph自动加载第一轮的checkpoint，恢复上下文
    ```
  - 验收:
    - 路由准确率100%
    - 并行调度无冲突
    - **[新增] 多轮对话上下文正确恢复**

- **Story 12.6**: 回滚机制和错误恢复
  - 实现rollback_to_timestamp和rollback_n_steps
  - FastAPI /api/canvas/rollback端点
  - Obsidian Plugin回滚UI
  - 验收: 回滚准确率100%,<2秒完成

- **Story 12.7**: 端到端集成测试和性能验证 + **记忆系统一致性测试**
  - 测试12个Agent在真实Canvas上的完整流程
  - 验证Epic 10.2的8倍性能提升保留
  - 测试并发场景 (最多12个Agent同时运行)
  - FileLock压力测试 (模拟100次并发写入)
  - **[新增] 记忆系统一致性测试**:
    - **测试1**: Checkpointer状态与Canvas文件一致性
    - **测试2**: Graphiti知识图谱与Canvas节点关系一致性
    - **测试3**: Temporal事件时间线完整性
    - **测试4**: Semantic向量与文档内容一致性
    - **测试5**: 多轮对话上下文恢复准确性
  - **[新增] 记忆存储失败容错测试**:
    - 模拟Graphiti连接失败 → Canvas操作应成功，记录错误日志
    - 模拟checkpointer写入延迟 → 不影响用户体验
  - 验收:
    - 所有功能可用
    - 性能不退化
    - 并发安全100%
    - **[新增] 记忆系统一致性100%，容错机制有效**

### Epic 13: Obsidian Plugin核心功能

**Story序列**:
- Story 13.1: Plugin项目初始化
- Story 13.2: Canvas API集成
- Story 13.3: API客户端实现
- Story 13.4: 核心命令 (拆解、评分、解释)
- Story 13.5: 右键菜单和快捷键
- Story 13.6: 设置面板
- Story 13.7: 错误处理

### Epic 14: 艾宾浩斯复习系统迁移+UI集成 (v1.1.6扩展)

**Epic性质**: 🔄 **迁移+集成+3层记忆整合** (基于已有ebbinghaus_review.py 870行代码)

**背景说明**:
- **已有实现**: `ebbinghaus_review.py` (870行, 2025-01-22完成)
  - ✅ SQLite数据库 (3表: review_schedules, review_history, user_review_stats)
  - ✅ 经典艾宾浩斯遗忘曲线算法 R(t)=e^(-t/S)
  - ✅ 基础CRUD操作 (添加概念、查询到期、更新复习记录)
- **本Epic目标 (v1.1.6扩展)**:
  1. **算法升级**: 从经典公式迁移到Py-FSRS (准确性提升20-30%)
  2. **Obsidian UI集成**: 创建侧边栏复习面板 (基于FR3.3 Mockup)
  3. **FastAPI接口封装**: 将Python函数封装为REST API
  4. **LangGraph集成**: 复习推送接入LangGraph Supervisor路由
  5. **⭐ v1.1.6新增: 3层记忆系统数据整合**
     - 集成Temporal Memory学习行为数据
     - 集成Graphiti概念关系网络
     - 集成Semantic Memory文档交互数据
     - 实现多维度优先级计算（4维度综合评分）
     - 实现行为监控触发机制（触发点4）
     - 实现FSRS参数自适应优化

**迁移策略**:
```python
# 阶段1: 保留现有SQLite schema,新增Py-FSRS字段 (向后兼容)
ALTER TABLE review_schedules ADD COLUMN fsrs_card_json TEXT;  # 存储FSRSCard序列化

# 阶段2: 双算法并行运行 (1周观察期)
if USE_FSRS_ALGORITHM:
    card = fsrs.review_card(card, rating)  # 使用Py-FSRS
else:
    retention_rate = calculate_retention_rate(time_elapsed, memory_strength)  # 经典公式

# 阶段3: 完全切换到Py-FSRS (保留经典算法作为fallback)
```

**工作量估算调整**:
- **原估算 (新开发)**: 6-8周
- **新估算 (迁移+UI)**: 2-4周 (代码复用率~70%)

**Story序列**:
- Story 14.1: Py-FSRS算法迁移 (2-3天)
  - 数据库schema扩展 (新增fsrs_card_json列)
  - FSRSCard <-> SQLite序列化/反序列化
  - 双算法A/B测试框架
  - 数据迁移脚本 (历史复习记录转换)

- Story 14.2: FastAPI接口封装 (1-2天)
  - POST /api/review/add-concept
  - GET /api/review/today-summary
  - POST /api/review/complete
  - GET /api/review/history

- Story 14.3: 复习面板视图 (Obsidian Plugin) (3-4天)
  - 侧边栏View注册
  - Canvas卡片列表渲染 (基于FR3.3 Mockup)
  - 紧急程度样式 (urgent/high/medium/low)
  - 响应式布局

- Story 14.4: 今日复习列表与交互 (2-3天)
  - "开始复习"按钮 → 调用generate_review_canvas_file()
  - "推迟1天"按钮 → 调整Card.due时间
  - 右键菜单 ("标记为已掌握" / "重置进度")
  - Canvas卡片点击 → 打开原白板

- Story 14.5: 一键生成检验白板集成 (1天)
  - 复用Epic 4已有generate_review_canvas_file()
  - 传入Canvas文件路径和到期概念列表
  - 检验白板生成后自动打开

- Story 14.6: 复习历史查看 (1-2天)
  - 历史记录列表 (最近7天/30天切换)
  - 每日复习统计图表 (复习概念数、平均评分)
  - 单个概念的复习轨迹查看

- Story 14.7: 复习提醒通知 (1天)
  - Obsidian Notice API集成
  - 每日首次打开触发提醒
  - 提醒开关配置 (插件设置页)

- Story 14.8: 复习统计图表 (2天)
  - 本周/本月复习概念数趋势图 (Chart.js)
  - 平均评分趋势
  - 连续复习天数徽章
  - 各Canvas复习覆盖率饼图

- **Story 14.9: 3层记忆系统查询工具集成** (2-3天) - **v1.1.6新增**
  - 实现4个新查询工具:
    - `query_temporal_learning_behavior(filter_type, ...)` - 查询时序学习行为数据
    - `query_graphiti_concept_network(analysis_type, ...)` - 查询概念关系网络
    - `query_semantic_document_interactions(pattern, ...)` - 查询文档交互模式
    - `track_learning_behavior(operation_type, ...)` - 记录学习行为数据
  - 工具集成到shared_tools列表
  - 单元测试（覆盖所有filter_type和analysis_type组合）
  - 验收: 所有工具可正常查询3层记忆系统，返回格式正确

- **Story 14.10: 行为监控触发机制（触发点4）** (3-4天) - **v1.1.6新增**
  - **背景**: 现有触发点1-3仅被动响应用户操作，无法主动检测"长期未访问的已掌握概念"等情况
  - **目标**: 实现每日凌晨2:00自动扫描3层记忆系统，检测需要复习的概念并自动添加到复习队列
  - 实现定时任务调度器:
    - 使用LangGraph定时触发机制
    - Cron表达式: `0 2 * * *` (每日凌晨2:00)
  - 实现3个检测条件:
    - **条件1 (Temporal)**: 已掌握但7天未访问的概念
    - **条件2 (Graphiti)**: 前置概念已掌握但后续概念长期未学的知识断层
    - **条件3 (Semantic)**: 相关文档频繁访问但概念本身未复习的隐性需求
  - 实现LangGraph行为监控节点:
    ```python
    def behavior_monitoring_node(state: EbbinghausMonitoringState):
        # 并行查询3层记忆
        temporal_concepts = query_temporal_learning_behavior(...)
        graphiti_concepts = query_graphiti_concept_network(...)
        semantic_concepts = query_semantic_document_interactions(...)

        # 合并去重并批量添加
        review_system.batch_add_concepts(all_concepts)
    ```
  - 日志记录和监控（每日生成监控报告）
  - 验收:
    - 定时任务准时触发（误差≤1分钟）
    - 3个条件检测准确率≥95%
    - 批量添加成功率100%
    - 每日监控报告自动生成

- **Story 14.11: 多维度优先级计算** (2天) - **v1.1.6新增**
  - **背景**: 现有优先级仅依赖FSRS算法的单一维度（遗忘曲线），未考虑学习行为、知识网络和文档交互等因素
  - **目标**: 实现4维度综合评分，提升复习推荐准确性
  - 实现多维度优先级计算函数:
    ```python
    def calculate_multidimensional_priority(concept_id: str) -> float:
        # 维度1: FSRS紧迫性 (40%)
        fsrs_urgency = calculate_fsrs_urgency(concept_id)

        # 维度2: 行为权重 (30%) - 从Temporal Memory
        behavior_weight = calculate_behavior_weight(
            recent_review_frequency,
            avg_interval,
            recent_accuracy
        )

        # 维度3: 网络中心性 (20%) - 从Graphiti
        network_centrality = calculate_network_centrality(
            prerequisite_mastery_avg,
            dependent_concepts_count,
            knowledge_path_depth
        )

        # 维度4: 交互权重 (10%) - 从Semantic Memory
        interaction_weight = calculate_interaction_weight(
            related_doc_access_count,
            avg_dwell_time,
            related_search_frequency
        )

        return (
            fsrs_urgency * 0.4 +
            behavior_weight * 0.3 +
            network_centrality * 0.2 +
            interaction_weight * 0.1
        )
    ```
  - 替换现有单一优先级排序逻辑
  - A/B测试框架（对比单维度 vs 多维度推荐效果）
  - 验收:
    - 多维度评分准确计算
    - 推荐列表排序合理性≥85%（人工评审）
    - A/B测试显示多维度优于单维度（提升≥15%）

- **Story 14.12: FSRS参数优化功能（FR3.6）** (3-4天) - **v1.1.6新增**
  - **背景**: 现有系统使用FSRS默认参数（17个），未针对用户实际学习行为优化
  - **目标**: 基于Temporal Memory的真实历史复习记录，优化FSRS参数，提升预测准确性
  - 实现数据提取模块:
    - 从Temporal Memory提取历史复习记录
    - 构建训练数据集: `(card_state, rating, actual_retention) -> prediction_error`
  - 实现参数优化算法:
    ```python
    def optimize_fsrs_parameters(user_id: str) -> FSRSParameters:
        # 提取历史复习数据
        review_history = query_temporal_learning_behavior(
            filter_type="optimization_dataset",
            user_id=user_id,
            min_samples=100
        )

        # 使用梯度下降优化17个参数
        optimizer = FSRSOptimizer()
        optimized_params = optimizer.optimize(
            review_history,
            initial_params=DEFAULT_FSRS_PARAMS,
            max_iterations=1000
        )

        return optimized_params
    ```
  - 实现A/B测试框架:
    - 组A: 使用默认参数
    - 组B: 使用优化参数
    - 对比指标: RMSE（均方根误差），预测准确率
  - 实现定期优化任务（每月1日凌晨3:00触发）
  - 验收:
    - 至少100条历史记录才触发优化
    - 优化参数RMSE优于默认参数（提升≥10%）
    - 参数持久化到数据库
    - 每月自动优化成功率≥95%

**v1.1.6工作量调整**:
- **原估算 (Story 14.1-14.8)**: 2-4周
- **新增 (Story 14.9-14.12)**: 2-2.5周
- **总估算 (v1.1.6)**: 4-6.5周

### Epic 15: 检验白板进度追踪系统

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- Context7: `/websites/neo4j_operations-manual-current` (4,940 snippets)

**验证检查点**:
- SM Agent必须查询Cypher语法和Operations最佳实践
- Dev Agent必须验证所有MATCH/CREATE/WHERE语句
- Code Review必须验证事务管理和索引使用

---

**Story序列**:
- Story 15.1: sourceNodeId元数据写入
- Story 15.2: 进度分析算法
- Story 15.3: 进度追踪UI组件
- Story 15.4: 实时进度更新 (WebSocket)
- Story 15.5: 进度可视化

### Epic 16: 跨Canvas关联学习系统

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- Context7: `/websites/neo4j_operations-manual-current` (4,940 snippets)
- Local Skill: `@graphiti` (完整框架文档)

**验证检查点**:
- SM Agent必须查询Cypher语法和Graphiti API
- Dev Agent必须验证所有图数据库操作
- Code Review必须验证跨Canvas关系的正确性

---

**Story序列**:
- Story 16.1: Canvas关联UI (工具栏按钮 + 模态框)
- Story 16.2: .canvas-links.json配置管理
- Story 16.3: Graphiti跨Canvas关系存储
- Story 16.4: 关联模式Toggle控制
- Story 16.5: Agent引用教材上下文
- Story 16.6: 教材引用显示
- Story 16.7: 关联状态指示器

---

## ⚠️ Section 5: 风险评估

### 技术风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| LangGraph性能不如直接调用 | 高 | 中 | 性能基准测试,保留Epic 10.2优化 |
| Obsidian API限制 | 高 | 低 | POC验证,备用Vault文件操作 |
| Docker配置复杂 | 中 | 中 | 详细文档,自动化脚本 |
| 跨平台兼容性 | 中 | 中 | CI/CD多平台测试 |

### 迁移风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| 用户数据丢失 | 极高 | 低 | Epic 18备份机制,双系统验证 |
| 功能回退 | 高 | 中 | 完整测试,保留CLI fallback |
| 用户学习成本高 | 中 | 高 | 详细文档,视频教程 |

### 回滚计划

**触发条件**:
- 数据丢失或损坏
- 严重性能退化 (>50%)
- 关键功能失效

**回滚步骤**:
1. 停止FastAPI和Neo4j服务
2. 恢复备份数据
3. 切换回CLI命令
4. 通知用户

---

## 📈 Section 6: 成功指标

### 关键指标 (KPI)

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 功能迁移完整性 | 100% (12个Agent全部可用) | 功能清单验证 |
| 性能不退化 | ≥现有系统 | 性能基准测试 |
| 用户满意度 | ≥80% | 用户调研 |
| 窗口切换次数 | 0 (完全在Obsidian内操作) | 用户观察 |
| 数据零丢失 | 100% | 迁移验证 |

---

## 📅 Section 7: 交付计划

### Phase 1: MVP (8-11周)

**交付内容**:
- ✅ Epic 11: FastAPI后端
- ✅ Epic 12: LangGraph编排
- ✅ Epic 13: Plugin核心功能
- ✅ Story 14.1-14.3: 复习面板核心

**验收标准**:
- 用户可在Obsidian内完成所有12个Agent操作
- 性能不低于现有系统
- 今日复习功能可用

### Phase 2: 完整功能 (18-22周)

**交付内容**:
- ✅ Epic 14: 艾宾浩斯复习系统迁移+UI集成完整功能
- ✅ Epic 15: 进度追踪
- ✅ Epic 16: 跨Canvas关联
- ✅ Epic 18: 数据迁移

---

## ✅ Section 8: 验收标准

### 最终验收清单

- [ ] 所有12个Agent功能100%可用
- [ ] Epic 10.2性能优势保留 (8倍提升)
- [ ] 艾宾浩斯复习面板正常工作
- [ ] 检验白板进度追踪准确显示
- [ ] 跨Canvas关联UI可配置
- [ ] 测试覆盖率 ≥85%
- [ ] 文档完整性 100%
- [ ] 用户满意度 ≥80%
- [ ] 数据迁移零丢失
- [ ] 回滚机制验证通过

---

## 📚 附录

### A. 参考文档

- Canvas Learning System CLAUDE.md
- Epic 10.2 Completion Report
- Story 4.9 (sourceNodeId元数据)
- Story 6.1 (Graphiti知识图谱)
- LangGraph官方文档 (Context7)

### B. 术语表

- **LangGraph**: LangChain的图编排框架,用于构建多Agent系统
- **Supervisor Pattern**: 中央路由器模式,一个Supervisor调度多个Worker Agent
- **Graphiti**: 时间感知知识图谱框架
- **Py-FSRS**: Python实现的FSRS间隔重复算法
- **FileLock**: 跨平台文件锁机制,防止并发写入冲突
- **create_react_agent**: LangGraph的工具配备Agent创建函数
- **Tool-Equipped Agent**: 配备工具的Agent,可直接调用函数完成任务
- **WriteHistory**: 写入历史记录系统,支持回滚操作

### C. 架构调整说明 (v1.0 → v1.1)

#### 调整动机

**用户核心需求**: "我需要能在Canvas白板进行快速的节点生成,那么我是否给各个解释agent中直接配备写入工具"

**原始设计 (v1.0)** 的问题:
- ❌ 集中式写入 (canvas_finalizer): 所有Agent完成后统一写入
- ❌ 首个节点出现时间: 8-10秒 (用户需要等待所有Agent完成)
- ❌ 无实时反馈: 用户不知道Agent是否在工作

#### 架构变更详情

**变更1: 双层Supervisor设计**

| 层级 | 组件 | 作用 | 变更类型 |
|------|------|------|---------|
| Layer 3 | canvas-orchestrator | 自然语言意图识别、计划生成 | ✅ **保留** |
| Layer 4 | LangGraph Supervisor | 并发调度、状态管理 | 🆕 **新增** |

**理由**: 保留canvas-orchestrator的智能路由优势,同时引入LangGraph的并发执行引擎

**变更2: 工具配备Agent**

| v1.0 设计 | v1.1 设计 (最终) |
|----------|-----------------|
| Agent返回JSON → canvas_finalizer写入 | Agent直接调用write_to_canvas工具 |
| 集中式写入,顺序执行 | 分布式写入,并发执行 |
| 8-10秒首个节点出现 | **0.5-1秒首个节点出现** ⚡ |

**理由**: 实时反馈,用户体验显著提升

**变更3: FileLock并发安全**

- **新增组件**: FileLock类 (跨平台文件锁)
- **作用**: 多个Agent同时写入Canvas时,自动排队,避免数据冲突
- **性能开销**: <100ms锁等待时间 (可接受)

**变更4: 写入历史和回滚**

- **新增组件**: WriteHistory类
- **作用**: 记录所有写入操作,支持按时间点或步数回滚
- **用户价值**: Agent操作出错时,可快速恢复到之前状态

#### 性能对比

| 指标 | v1.0 (集中式) | v1.1 (工具配备) | 提升 |
|------|--------------|----------------|------|
| 首个节点出现时间 | 8-10秒 | 0.5-1秒 | **8-16倍** ⚡ |
| 用户可见反馈 | 操作结束后 | 实时 (每0.5秒) | ✅ 显著改善 |
| Epic 10.2性能 | 8倍并发提升 | 8倍并发提升 | ✅ 完全保留 |
| 并发安全 | N/A (顺序执行) | FileLock保护 | ✅ 新增 |
| 错误恢复 | 无 | WriteHistory回滚 | ✅ 新增 |

#### 兼容性影响

**100%向后兼容**:
- ✅ 所有12个Agent功能完全保留
- ✅ canvas_utils.py 3层架构无变化
- ✅ Epic 10.2异步执行引擎保留
- ✅ Graphiti知识图谱集成保留

**新增能力**:
- ✅ 实时节点生成
- ✅ 并发写入安全
- ✅ 操作回滚
- ✅ 写入历史追溯

#### 风险缓解

| 风险 | 缓解措施 | 状态 |
|------|---------|------|
| FileLock性能开销 | 基准测试,<100ms开销 | ✅ 可接受 |
| 跨平台兼容性 | Windows/macOS/Linux测试 | 📋 Story 12.2 |
| 并发写入冲突 | FileLock + 压力测试 | 📋 Story 12.7 |
| 回滚数据丢失 | 快照验证测试 | 📋 Story 12.6 |

---

**文档结束**

**文档版本**: v1.1 (架构调整版)
**原始版本**: v1.0 (2025-01-15)
**调整日期**: 2025-01-15
**调整原因**: 用户反馈要求快速节点生成和实时反馈

**下一步**: 开始Epic 11 Story 11.1实施

**批准签名**: ___________
**日期**: 2025-01-15
