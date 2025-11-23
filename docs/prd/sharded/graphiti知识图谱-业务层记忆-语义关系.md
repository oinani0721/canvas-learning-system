# Graphiti知识图谱 (业务层记忆 - 语义关系)

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
