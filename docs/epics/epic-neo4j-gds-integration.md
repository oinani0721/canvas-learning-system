# EPIC: Neo4j GDS集成 - 轻量化社区检测方案

---
**Epic ID**: EPIC-Neo4j-GDS
**Epic类型**: 新功能 + 架构简化 (Enhancement)
**状态**: 📋 Ready for Development
**优先级**: 🔥 High (P0) - Epic 14依赖
**创建日期**: 2025-11-14
**预计开始**: 立即
**预计完成**: 4个工作日
**负责团队**: Backend Team
**预计成本**: $1,200 (首年)
**替代Epic**: EPIC-GraphRAG (已暂停)
---

## Epic概述

**目标**: 使用Neo4j GDS (Graph Data Science) 的Leiden算法实现概念社区检测，支持艾宾浩斯复习系统的触发点4（薄弱点聚类），作为Microsoft GraphRAG的轻量化替代方案。

**背景**:
原计划引入Microsoft GraphRAG (EPIC-GraphRAG) 经技术评估发现存在过度设计问题（功能重叠60%，成本10倍），采用Neo4j GDS可以实现相同功能，同时显著降低成本和复杂度。

---

## 为什么需要这个Epic？

### 业务价值
1. **满足Epic 14核心需求**: 艾宾浩斯触发点4需要薄弱点聚类能力
2. **智能复习推荐**: 自动识别相关联的薄弱概念群，生成针对性检验白板
3. **学习路径优化**: 基于概念社区结构推荐最优学习顺序

### 技术优势
| 维度 | GraphRAG方案 | Neo4j GDS方案 | 优势 |
|------|------------|--------------|-----|
| **算法** | Leiden社区检测 | Leiden社区检测 | ✅ 算法相同 |
| **存储** | Parquet文件 | Neo4j原生 | ✅ 架构统一 |
| **开发成本** | $2,400 (15-20天) | $640 (4天) | ✅ 节省73% |
| **运营成本** | $7,384/年 | $560/年 | ✅ 节省92% |
| **响应时间** | 2-8秒 | <200ms | ✅ 快40倍 |
| **维护复杂度** | 高（双存储） | 低（单存储） | ✅ 简化架构 |

**ROI**: 首年节省$8,584，投资回报率2,966%

---

## Epic范围

### In-Scope ✅
- ✅ Neo4j GDS库安装和配置
- ✅ 图投影创建（Concept节点 + RELATED_TO关系）
- ✅ Leiden社区检测算法实现
- ✅ 薄弱点过滤逻辑（评分<70或复习次数>3）
- ✅ 与艾宾浩斯系统的API集成
- ✅ 社区聚类结果可视化（在Obsidian Canvas中）
- ✅ 基础性能监控（算法执行时间、社区数量）

### Out-of-Scope ❌
- ❌ Global Search功能（Graphiti已提供）
- ❌ Parquet存储层（不需要）
- ❌ 本地LLM集成（现有OpenAI API足够）
- ❌ 多跳推理路径可视化（Phase 2功能）

---

## Stories

### Story GDS.1: Ebbinghaus Trigger Point 4 - Community-Based Weak Point Clustering
**优先级**: 🔥 Critical
**工作量**: 3天
**依赖**: Epic 12 (3层记忆系统), Epic 14 (艾宾浩斯基础)
**Story文件**: `gds-1-ebbinghaus-trigger-point-4.story.md`

**功能描述**:
实现艾宾浩斯触发点4的社区检测功能，自动识别薄弱概念聚类，生成针对性检验白板。

**AC (Acceptance Criteria)**:
1. ✅ Neo4j GDS Leiden算法成功聚类薄弱概念
2. ✅ 输出格式与艾宾浩斯系统兼容（社区ID + 概念列表）
3. ✅ 算法响应时间<500ms（1000个概念规模）
4. ✅ 生成的检验白板包含同一社区的相关薄弱点

**技术要点**:
```cypher
// 1. 创建图投影（包含薄弱点权重）
CALL gds.graph.project(
    'weak-concepts-graph',
    'Concept',
    'RELATED_TO',
    {
        nodeProperties: {
            avg_score: {defaultValue: 100},
            review_count: {defaultValue: 0},
            last_review_days_ago: {defaultValue: 999}
        },
        relationshipProperties: ['strength']
    }
)

// 2. Leiden聚类（仅处理薄弱概念）
CALL gds.leiden.stream('weak-concepts-graph', {
    nodeLabels: ['Concept'],
    relationshipWeightProperty: 'strength',
    includeIntermediateCommunities: true,
    tolerance: 0.0001,
    gamma: 1.0
})
YIELD nodeId, communityId, intermediateCommunityIds
WITH gds.util.asNode(nodeId) AS concept, communityId
WHERE concept.avg_score < 70 OR concept.review_count > 3
RETURN
    communityId AS cluster_id,
    collect({
        id: id(concept),
        name: concept.name,
        score: concept.avg_score,
        reviews: concept.review_count
    }) AS concepts
ORDER BY size(concepts) DESC
```

**输出示例**:
```json
{
  "trigger_point": 4,
  "trigger_name": "薄弱点聚类",
  "clusters": [
    {
      "cluster_id": 42,
      "concepts": [
        {"id": 123, "name": "逆否命题", "score": 65, "reviews": 4},
        {"id": 124, "name": "充分必要条件", "score": 68, "reviews": 3},
        {"id": 125, "name": "逻辑等价", "score": 62, "reviews": 5}
      ],
      "cluster_score": 65.0,
      "recommended_review_urgency": "high"
    }
  ],
  "total_weak_concepts": 23,
  "total_clusters": 5
}
```

### Story GDS.2: Performance Tuning (可选)
**优先级**: 🟡 Low
**工作量**: 1天
**依赖**: GDS.1

**功能描述**: 优化Leiden算法参数和图投影配置，支持更大规模数据（10,000+概念）

**AC**:
1. ✅ 支持10,000个概念的聚类（<2秒）
2. ✅ 内存使用优化（图投影<500MB）
3. ✅ 参数调优文档（gamma, tolerance, iterations）

**Note**: 此Story为可选扩展，MVP阶段可推迟

---

## Epic成功标准

1. ✅ **功能完整性**: 艾宾浩斯触发点4正常工作，生成的检验白板包含聚类薄弱点
2. ✅ **性能达标**: 1000概念规模下，聚类时间<500ms
3. ✅ **成本控制**: 首年总成本≤$1,200
4. ✅ **架构简洁**: 无新增存储层，复用Neo4j
5. ✅ **Epic 14解除阻塞**: 艾宾浩斯系统可正常启动开发

---

## 依赖关系

**前置依赖** (必须完成才能开始):
- ✅ Epic 12: 3层记忆系统（Neo4j Graphiti已部署）
- ✅ Epic 10: 智能并行处理系统（Canvas操作基础）

**阻塞Epic** (本Epic完成后可启动):
- 🔓 Epic 14: 艾宾浩斯复习系统（等待触发点4实现）

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Neo4j GDS库版本不兼容 | 🟡 低 | 🟡 中 | 提前在dev环境测试，锁定版本号 |
| Leiden算法结果不稳定 | 🟢 极低 | 🟡 中 | 固定随机种子，添加结果验证测试 |
| 大规模数据性能下降 | 🟡 低 | 🟢 低 | 实施Story GDS.2性能调优 |

---

## 交付物

1. ✅ Neo4j GDS集成代码 (`canvas_memory/neo4j_gds_clustering.py`)
2. ✅ 艾宾浩斯触发点4 API实现 (`ebbinghaus/trigger_point_4.py`)
3. ✅ 单元测试和集成测试（覆盖率>90%）
4. ✅ 性能基准测试报告
5. ✅ 用户文档：如何解读社区聚类结果
6. ✅ 开发者文档：Leiden参数调优指南

---

## 时间线

| 里程碑 | 预计日期 | 交付物 |
|-------|---------|-------|
| **Kickoff** | Day 0 | Epic启动，环境准备 |
| **GDS.1 完成** | Day 3 | 触发点4功能可用 |
| **集成测试** | Day 4 | 与艾宾浩斯系统联调 |
| **Epic完成** | Day 4 | 所有AC验证通过 |

**总工期**: 4个工作日
**缓冲**: 已包含1天缓冲时间

---

## 成本明细

| 成本项 | 金额 | 说明 |
|-------|------|------|
| **开发成本** | $640 | 4天 × $160/天 |
| **Neo4j内存增量** | $60/年 | GDS库运行时内存（估算） |
| **运营成本** | $500/年 | 监控和维护 |
| **首年总计** | **$1,200** | |

**对比GraphRAG**: 节省$8,584 (88%)

---

## 后续扩展 (Phase 2)

本Epic聚焦MVP核心功能（触发点4），以下功能规划在后续版本：

1. **多层级社区检测**: 利用Leiden的中间社区层级（`intermediateCommunityIds`）
2. **社区演化追踪**: 跟踪概念社区随时间的变化
3. **个性化聚类**: 基于用户学习历史调整聚类参数
4. **可视化仪表盘**: 在Obsidian中展示概念社区网络图

---

## 决策记录

**相关ADR**:
- ADR-004: GraphRAG Integration Evaluation (✅ Accepted - Do Not Integrate)

**相关SCP**:
- SCP-005: GraphRAG过度设计纠偏提案 (✅ Approved)

---

**Epic Owner**: Architect Agent (Morgan)
**Created**: 2025-11-14
**Last Updated**: 2025-11-14
**Status**: ✅ Ready for Development
