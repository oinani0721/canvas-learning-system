# Technical Verification Checklist

## Purpose
防止PRD和Story开发中的技术"幻觉"，确保所有技术细节都有权威文档支撑。

## When to Use This Checklist
- ✅ 编写PRD时（初步验证）
- ✅ Epic实施前（深度验证）
- ✅ Story开发时（代码级验证）
- ✅ 技术决策评审时

## Section 1: 识别技术栈

### 1.1 列出所有涉及的技术栈
- [ ] 编程语言和版本
- [ ] 框架和库（含版本号）
- [ ] 数据库和查询语言
- [ ] API和集成服务
- [ ] 工具和平台

### 1.2 确定文档查询方式

对每个技术栈，按以下规则确定查询方式：

| 技术栈 | 查询方式 | 位置/Library ID |
|--------|---------|----------------|
| LangGraph | Skill | `.claude/skills/langgraph/` |
| Graphiti | Skill | `.claude/skills/graphiti/` |
| Obsidian Canvas | Skill | `.claude/skills/obsidian-canvas/` |
| FastAPI | Context7 | `/websites/fastapi_tiangolo` |
| Neo4j Cypher | Context7 | `/websites/neo4j_cypher-manual_25` |
| Neo4j Operations | Context7 | `/websites/neo4j_operations-manual-current` |

**决策规则**：
1. 首先检查 `.claude/skills/` 目录是否存在对应Skill
2. 如果存在Skill → 使用 `@skill-name` 激活
3. 如果不存在 → 查询Context7获取Library ID
4. 如果Context7也没有 → 考虑使用Skill Seeker生成

---

## Section 2: API和参数验证

### 2.1 函数/方法签名验证
- [ ] **函数名**: 准确无误（大小写敏感）
- [ ] **参数名**: 与官方文档一致
- [ ] **参数类型**: 明确类型和可选性
- [ ] **返回值**: 明确返回类型

### 2.2 使用示例验证
对每个关键API：
- [ ] 找到至少1个官方示例
- [ ] 复制示例代码到PRD/Story
- [ ] 标注示例来源（URL或Skill文件:行号）

### 2.3 版本兼容性验证
- [ ] 明确使用的版本号
- [ ] 检查版本特定的API差异
- [ ] 记录已知的breaking changes

**示例**：
```python
# ✅ 正确验证：from LangGraph Skill (SKILL.md:226-230)
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model,
    tools=[search_tool, calculator_tool],
    state_modifier="You are a helpful assistant."  # ✅ 参数存在
)
```

---

## Section 3: 架构模式验证

### 3.1 设计模式验证
- [ ] 使用的架构模式有官方推荐
- [ ] 找到类似use case的示例
- [ ] 了解模式的限制和trade-offs

### 3.2 集成模式验证
- [ ] 多个技术栈如何集成
- [ ] 数据流向和转换
- [ ] 错误处理和重试策略

---

## Section 4: 性能和限制验证

### 4.1 性能指标
- [ ] 查询官方性能基准
- [ ] 了解并发和扩展限制
- [ ] 记录典型性能数据

### 4.2 已知限制
- [ ] 列出技术栈的已知限制
- [ ] 标注不支持的功能
- [ ] 记录workaround方案

---

## Section 5: 文档引用规范

### 5.1 在PRD中添加技术栈章节

在PRD中添加以下章节：

```markdown
## Section N: Required Skills & Documentation Sources

本项目涉及的技术栈及其文档查询方式：

| Epic | 技术栈 | 查询方式 | Library ID / Skill Path |
|------|--------|---------|------------------------|
| Epic 11 | FastAPI | Context7 | `/websites/fastapi_tiangolo` |
| Epic 11 | Python 3.11 | Context7 | `/python/cpython` |
| Epic 12 | LangGraph | Skill | `.claude/skills/langgraph/` |
| Epic 12 | Graphiti | Skill | `.claude/skills/graphiti/` |
| Epic 13 | Obsidian Canvas | Skill | `.claude/skills/obsidian-canvas/` |
| Epic 13 | TypeScript | Context7 | `/microsoft/typescript` |
| Epic 14 | Neo4j Cypher | Context7 | `/websites/neo4j_cypher-manual_25` |
| Epic 14 | Neo4j Operations | Context7 | `/websites/neo4j_operations-manual-current` |

### Story开发前必读

每个Story开发前，**必须**激活或查询相应的文档：

**Epic 11 (FastAPI后端)**:
```bash
# 使用Context7查询FastAPI
mcp__context7-mcp__get-library-docs("/websites/fastapi_tiangolo", topic="your-topic")
```

**Epic 12 (LangGraph Agent系统)**:
```bash
# 激活Skills
@langgraph
@graphiti
```

**Epic 13 (Obsidian插件)**:
```bash
# 激活Skill
@obsidian-canvas
```

**Epic 14 (Neo4j数据层)**:
```bash
# 使用Context7查询Neo4j
mcp__context7-mcp__get-library-docs("/websites/neo4j_cypher-manual_25", topic="your-topic")
```
```

### 5.2 在Story中引用文档

每个Story应包含：
- [ ] **Required Skills**: 列出需要激活的Skills
- [ ] **Context7 Queries**: 列出需要查询的Library IDs
- [ ] **Verification Notes**: 已验证的API和参数

---

## Section 6: 验证质量标准

### 6.1 完成标准
- [ ] ✅ **100%覆盖**: 所有技术细节都有文档支撑
- [ ] ✅ **可追溯**: 每个API都能找到来源
- [ ] ✅ **可复现**: 示例代码可直接运行
- [ ] ✅ **版本明确**: 所有依赖版本已锁定

### 6.2 质量检查清单
- [ ] 无假设的API名称
- [ ] 无猜测的参数类型
- [ ] 无未验证的架构模式
- [ ] 无缺失的错误处理

### 6.3 审批流程
- [ ] **Self-Review**: 开发者自查（使用本清单）
- [ ] **Peer Review**: PM/Architect审查文档引用
- [ ] **Documentation Test**: 尝试用引用的文档实际开发

---

## Section 7: 常见错误和预防

### 7.1 常见"幻觉"类型
1. **参数幻觉**: 假设某个参数存在但实际不存在
   - 预防: 总是从文档复制参数名
2. **版本幻觉**: 假设新版本API与旧版本相同
   - 预防: 明确版本号并查看changelog
3. **架构幻觉**: 假设某个集成模式可行但未验证
   - 预防: 找到官方示例或社区案例

### 7.2 快速验证技巧
```bash
# 1. 激活所有相关Skills
@langgraph @graphiti @obsidian-canvas

# 2. 批量查询Context7
for lib_id in ["/websites/fastapi_tiangolo", "/websites/neo4j_cypher-manual_25"]; do
  mcp__context7-mcp__get-library-docs($lib_id, topic="quick-start")
done

# 3. 搜索关键API
# 在Skill文件中: Ctrl+F 搜索函数名
# 在Context7中: 使用topic参数精确查询
```

---

## Appendix: Context7 Library ID Reference

### 常用Library IDs
- **Python生态**:
  - FastAPI: `/websites/fastapi_tiangolo`
  - Pydantic: `/pydantic/pydantic`
  - SQLAlchemy: `/sqlalchemy/sqlalchemy`

- **LLM框架**:
  - LangChain: `/langchain-ai/langchain`
  - LangGraph: （使用Skill）

- **数据库**:
  - Neo4j Cypher: `/websites/neo4j_cypher-manual_25`
  - Neo4j Operations: `/websites/neo4j_operations-manual-current`
  - Neo4j Python Driver: `/neo4j/neo4j-python-driver`

- **前端**:
  - TypeScript: `/microsoft/typescript`
  - React: `/facebook/react`
  - Obsidian API: （使用Skill）

### 查询新Library ID的流程
1. 使用 `mcp__context7-mcp__resolve-library-id(libraryName="your-lib")`
2. 选择Trust Score最高、Code Snippets最多的结果
3. 记录到PRD的技术栈章节

---

## Version History
- **v1.0** (2025-11-11): Initial version - Canvas Learning System PRD v1.1.1
