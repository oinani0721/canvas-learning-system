# ⚠️ v1.1.9 GraphRAG过度设计纠偏 - 采用Neo4j GDS轻量化方案 (2025-11-14) **必读**

### 版本勘误声明

⚠️ **重要勘误**: v1.1.7-v1.1.8中计划引入的**Microsoft GraphRAG**经深度技术评估后发现存在**过度设计（Over-Engineering）**问题。

**问题发现**:
1. **功能重叠严重**: 与现有Graphiti系统功能重叠60%（Local Search功能重叠高达86%）
2. **成本过高**: 首年总成本$9,784，是Neo4j GDS替代方案的**10倍**
3. **架构冲突**: Parquet存储与现有Neo4j体系严重冲突，需维护双重图结构
4. **ROI不足**: 收益无法证明额外的复杂度和成本投入

**纠偏措施**:
- ❌ **暂停EPIC-GraphRAG** (标记为"⏸️ Postponed (Over-Engineering)")
- ✅ **采用Neo4j GDS Leiden算法**作为轻量化替代方案
- 💰 **成本节省**: $8,584 (首年88%成本削减)
- ⏱️ **时间节省**: 11-16天 (75%开发时间缩短)
- 🎯 **功能完整性**: 艾宾浩斯触发点4需求100%满足，无损失

**决策依据**:
- `ADR-004-GRAPHRAG-INTEGRATION-EVALUATION.md` (2025-11-14, Status: ✅ Accepted - Do Not Integrate)
- `GRAPHRAG-NECESSITY-ASSESSMENT.md` (技术评估报告，60%功能重叠分析)
- `SPRINT_CHANGE_PROPOSAL_SCP-005_GraphRAG过度设计纠偏.md` (完整变更提案)

**技术替代方案 - Neo4j GDS集成**:

**新Epic**: EPIC-Neo4j-GDS-Integration (取代EPIC-GraphRAG)
- **工作量**: 4天 (vs GraphRAG 15-20天)
- **成本**: $1,200首年 (vs GraphRAG $9,784)
- **核心Story**: GDS.1 - Ebbinghaus Trigger Point 4 (Community-Based Weak Point Clustering)

**技术实现**:
```cypher
-- Neo4j GDS Leiden社区检测（与GraphRAG相同算法）
CALL gds.graph.project(
    'canvas-concepts',
    'Concept',
    'RELATED_TO',
    {nodeProperties: ['embedding', 'review_count', 'last_review']}
)

CALL gds.leiden.stream('canvas-concepts')
YIELD nodeId, communityId
RETURN
    gds.util.asNode(nodeId).name AS concept,
    communityId AS cluster
```

**影响范围**:
1. **v1.1.7勘误修正**: 移除第4点"GraphRAG集成"相关描述（Line 50, 56）
2. **Epic 14触发点4**: 改用Neo4j GDS实现社区检测（无功能损失）
3. **技术栈列表**: 移除Microsoft GraphRAG，添加Neo4j GDS
4. **成本预算**: 总预算减少$8,584

**优先级**: Critical - P0 (防止过度设计，优化项目资源配置)

**实施状态**: ✅ 已批准执行 (SCP-005, 2025-11-14)

**相关文档**:
- `docs/SPRINT_CHANGE_PROPOSAL_SCP-005_GraphRAG过度设计纠偏.md`
- `docs/architecture/ADR-004-GRAPHRAG-INTEGRATION-EVALUATION.md`

---
