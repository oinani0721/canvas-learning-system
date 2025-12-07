# 1.X.4 文档查询工作流 (Documentation Query Workflow)

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
