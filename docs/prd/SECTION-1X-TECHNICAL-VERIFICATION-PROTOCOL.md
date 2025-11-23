---
document_type: "PRD"
version: "1.2.0"
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

# Section 1.X: 技术验证协议 (Mandatory Technical Verification Protocol)

**版本**: v1.2
**生效日期**: 2025-11-13
**强制执行**: Epic 0开始，适用于所有技术Epic (11, 12, 13, 15, 16)
**状态**: ✅ 已批准
**整合状态**: 待整合到主PRD (CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md)

---

## 📋 整合说明

**本文档应整合到主PRD的位置**:
- **插入位置**: Section 1（项目分析）之后，Section 2（需求定义）之前
- **对应行号**: 约Line 283-284之间
- **章节编号**: 1.X (待确定具体编号)

**整合方法**:
1. 复制本文档全部内容（从"1.X.1 核心原则"开始）
2. 在PRD的Line 283 `---` 之后插入
3. 保持Section 2的标题不变

---

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
