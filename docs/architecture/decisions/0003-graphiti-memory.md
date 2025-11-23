# 3. 使用Graphiti实现时序知识图谱记忆系统

Date: 2025-10-20

## Status

Accepted

Enables: [ADR-0014: 艾宾浩斯复习系统](#0014-ebbinghaus-review-system.md)

## Context

Canvas Learning System需要一个长期记忆系统来跨会话、跨Canvas、跨时间管理学习历史，需要满足以下需求：

1. **时序记忆需求**:
   - 记录学习会话的时间序列（什么时候学习了什么概念）
   - 支持时间范围查询（最近7天学习了哪些概念）
   - 追踪概念理解度随时间的变化（红→紫→绿的流转历史）
   - 支持艾宾浩斯复习调度（根据遗忘曲线计算复习时间）

2. **概念关系网络需求**:
   - 自动提取Canvas中的概念和关系（从节点文本和边连接）
   - 构建概念知识图谱（概念-概念关系、概念-文档关系）
   - 识别薄弱环节（频繁出错的概念聚类）
   - 推荐学习路径（基于概念依赖关系）

3. **语义搜索需求**:
   - 基于语义而非关键词搜索相关概念
   - 检验白板生成时查询历史薄弱点（"我上次在哪个概念上卡住了？"）
   - 推荐相关学习材料（"与'逆否命题'相关的其他概念有哪些？"）

4. **性能和成本需求**:
   - API调用成本优化（避免重复调用GPT-4处理相同内容）
   - 多级缓存（内存缓存 + 磁盘缓存 + 图数据库缓存）
   - 批量处理（合并相似的embedding请求）
   - 实时响应（<2秒查询历史薄弱点）

### 候选方案对比

| 方案 | 优点 | 缺点 | 评分 |
|------|------|------|------|
| **Graphiti + Neo4j** | • 专为时序知识图谱设计<br>• 原生支持时间索引<br>• 与LangGraph无缝集成<br>• 支持Hybrid Search (向量+图)<br>• 活跃社区和文档 | • 需要部署Neo4j服务器<br>• 学习曲线中等<br>• 依赖Neo4j GDS插件 | ⭐⭐⭐⭐⭐ |
| MemGPT | • 为Agent长期记忆优化<br>• 自动内存分页<br>• 易于集成 | • 主要面向对话记忆<br>• 不支持复杂图查询<br>• 概念关系建模有限 | ⭐⭐⭐ |
| LangMem (LangChain) | • LangChain官方记忆模块<br>• 简单易用 | • 功能较基础<br>• 不支持时序图<br>• 扩展性有限 | ⭐⭐⭐ |
| 自定义Neo4j方案 | • 完全控制<br>• 可定制化 | • 开发周期长<br>• 需要自己实现时序索引<br>• 维护成本高 | ⭐⭐ |
| 纯向量数据库(LanceDB) | • 快速语义搜索<br>• 低成本 | • 不支持图关系<br>• 无时间索引<br>• 无法识别薄弱点聚类 | ⭐⭐ |

## Decision

我们决定使用**Graphiti + Neo4j**作为Canvas Learning System的时序知识图谱记忆系统。

**选择理由**:

1. **时序知识图谱专用设计** 🕒:
   - Graphiti原生支持时间索引（每个Episode和Entity都有timestamp）
   - 支持时间范围查询（`search(start_time, end_time)`）
   - 自动维护概念理解度时间线（红→紫→绿流转历史）
   - 完美匹配艾宾浩斯复习系统需求（查询"7天前学习的概念"）

2. **LangGraph生态无缝集成** 🔗:
   - Graphiti是LangGraph官方推荐的知识图谱层
   - 可以作为LangGraph的State层（ADR-0002中提到的扩展）
   - 支持与LangGraph Agent协作（Agent调用Graphiti查询历史）
   - 与我们的Agent架构完美契合

3. **Hybrid Search支持** 🔍:
   - 同时支持向量搜索（语义）+ 图搜索（关系）
   - 检验白板生成时可以查询"语义相似 + 历史频繁出错"的概念
   - 权重可调（70%薄弱点 + 30%已掌握概念，PRD v1.1.8要求）
   - 比纯向量数据库更智能

4. **Neo4j图算法支持** 📊:
   - Neo4j GDS (Graph Data Science) 提供Leiden聚类算法
   - 支持艾宾浩斯触发点4: 薄弱点聚类（Epic 14需求）
   - 概念社区检测（发现相关概念群）
   - 学习路径推荐（基于概念依赖关系）

5. **API成本优化机制** 💰:
   - Graphiti内置结果缓存（避免重复embedding相同文本）
   - 支持批量处理（合并多个概念的embedding请求）
   - 三级缓存策略：内存 → 磁盘 → Neo4j
   - 预计API调用成本降低60-80%

**技术实现**:

我们将创建`.claude/agents/graphiti-memory-agent.md`作为系统级Agent，提供以下API：

```python
# 学习会话记录
await graphiti_memory_agent.add_episode(
    canvas_path="离散数学.canvas",
    concepts=["逆否命题", "布尔代数"],
    activities=["basic-decomposition", "scoring"],
    timestamp=datetime.now()
)

# 查询历史薄弱点（检验白板生成）
weak_concepts = await graphiti_memory_agent.query_weak_concepts(
    time_range=(7_days_ago, now),
    min_error_count=2,
    include_related=True
)

# 艾宾浩斯复习推荐（Epic 14）
review_concepts = await graphiti_memory_agent.get_review_candidates(
    algorithm="py-fsrs",
    current_time=now
)
```

**3层记忆系统架构** (Epic 12):

```
Layer 1: Temporal Memory (时序记忆)
  ↓ Neo4j DirectNeo4jStorage
  ↓ 存储: Episode (学习会话) + timestamp

Layer 2: Graphiti (概念关系网络)
  ↓ Neo4j Graphiti Layer
  ↓ 存储: Entity (概念) + Relationship (关系)

Layer 3: Semantic Memory (语义向量)
  ↓ LanceDB + CUDA加速
  ↓ 存储: Embedding vectors for hybrid search
```

**与其他系统集成**:

- **检验白板生成**: 查询历史薄弱点和相关概念（Epic 4扩展，PRD v1.1.8）
- **艾宾浩斯复习系统**: 提供遗忘曲线计算所需的时序数据（Epic 14）
- **智能Agent调度器**: 推荐基于历史薄弱点的Agent组合（Epic 10扩展）

## Consequences

### 正面影响

1. **长期学习记忆能力** 🧠:
   - 跨会话追踪学习进度
   - 识别频繁出错的概念（薄弱环节）
   - 支持复习调度和遗忘曲线计算
   - 可视化学习路径和概念网络

2. **智能检验白板生成** 🎯:
   - 基于历史数据生成个性化检验题
   - 优先检验历史薄弱点（70%权重）
   - 包含已掌握概念巩固题（30%权重）
   - 推荐相关概念扩展学习

3. **API成本大幅降低** 💰:
   - 三级缓存减少60-80% API调用
   - 批量处理降低embedding成本
   - Graphiti内置去重机制
   - 预计每月成本从$50降至$10-15

4. **LangGraph生态协同** 🔗:
   - 作为State层扩展LangGraph能力
   - 与14个Agent无缝协作
   - 支持Agent间共享知识图谱
   - 未来可以实现跨用户知识共享

### 负面影响

1. **基础设施复杂度增加** ⚠️:
   - 需要部署Neo4j服务器（Docker推荐）
   - 需要安装Neo4j GDS插件（Leiden算法依赖）
   - 需要配置3层存储（Neo4j + LanceDB + 内存缓存）
   - **缓解措施**: 提供Docker Compose一键部署脚本，自动化配置流程

2. **学习曲线** ⚠️:
   - 团队需要学习Graphiti API和Cypher查询语言
   - 需要理解时序图数据模型（Episode, Entity, Relationship）
   - 需要掌握Neo4j GDS图算法
   - **缓解措施**: 创建`graphiti` Skill (~200页离线文档)，提供快速参考

3. **性能优化挑战** ⚠️:
   - Neo4j查询性能依赖索引设计
   - 大规模概念网络（>10000节点）可能需要优化
   - 并发写入需要事务管理
   - **缓解措施**:
     - 预建索引（timestamp, concept_name, user_id）
     - 使用Neo4j查询性能分析工具（EXPLAIN, PROFILE）
     - 实现异步写入队列（避免阻塞学习流程）

4. **数据一致性** ⚠️:
   - 3层存储需要保证一致性（Neo4j vs LanceDB vs 内存缓存）
   - 缓存失效策略需要精心设计
   - 并发更新可能导致冲突
   - **缓解措施**:
     - Neo4j作为Single Source of Truth
     - LanceDB和内存缓存作为只读副本
     - 定期同步（每30分钟全量同步）
     - 写入时立即失效相关缓存

### 技术债务

- **TODO**: 监控Neo4j性能，优化慢查询（PROFILE工具）
- **TODO**: 实现自动备份策略（Neo4j dump + LanceDB snapshot）
- **TODO**: 开发监控Dashboard（Grafana + Prometheus）
- **TODO**: 评估多用户场景下的数据隔离策略（tenant_id分区）
- **TODO**: 考虑Graphiti版本升级策略（当前0.3.x → 未来1.0）

### 度量指标

- **查询性能**: 历史薄弱点查询 <2秒 (目标)
- **API成本**: 降低60-80% (vs 无缓存方案)
- **缓存命中率**: >70% (内存缓存 + 磁盘缓存)
- **概念提取准确率**: >90% (vs 人工标注)
- **检验白板生成时间**: <10秒 (包含Graphiti查询)

## References

- Graphiti官方文档: https://github.com/getzep/graphiti
- Graphiti官方示例: https://github.com/getzep/graphiti-examples
- Neo4j图数据库: https://neo4j.com/
- Neo4j GDS插件: https://neo4j.com/docs/graph-data-science/current/
- LanceDB向量数据库: https://lancedb.com/
- Canvas Learning System PRD: `docs/prd/FULL-PRD-REFERENCE.md` (Epic 12, Epic 14)
- Canvas Learning System Skill: `.claude/skills/graphiti/` (~200页离线文档)

## Notes

此决策是Canvas Learning System **长期记忆系统的基石**。Graphiti的时序知识图谱能力使得系统可以跨会话、跨时间追踪学习历史，为艾宾浩斯复习系统（Epic 14）和智能检验白板生成（Epic 4扩展）提供数据支撑。

**历史背景**: 在Epic 12规划阶段（2025-10-20），我们评估了5种记忆系统方案，Graphiti以其时序图能力、LangGraph集成和Hybrid Search支持脱颖而出。

**实施状态**:
- ✅ Epic 12.1-12.3: Graphiti基础设施部署（Docker Compose）
- ✅ Epic 12.4-12.6: 3层记忆系统集成（Temporal + Graphiti + Semantic）
- ✅ Epic 12.7-12.9: API成本优化（三级缓存 + 批量处理）
- ⏳ Epic 14: 艾宾浩斯复习系统集成（依赖Graphiti时序查询）

**重要约束**:
- Graphiti查询必须**异步执行**（使用`await`），避免阻塞学习流程
- 所有写入操作必须使用**事务**（Neo4j transaction），保证数据一致性
- 缓存失效必须**及时**（write-through策略），避免脏读

**API成本优化策略** (关键！):
1. **智能缓存**:
   - 内存缓存（LRU, 1000个最近查询）
   - 磁盘缓存（Redis, 10000个热点查询）
   - Graphiti内置缓存（Neo4j查询结果）

2. **批量处理**:
   - 合并相似的embedding请求（使用`batch_add_episodes`）
   - 延迟非紧急写入（使用异步队列）
   - 复用已有embedding（concept去重）

3. **模型降级**:
   - 使用gpt-3.5-turbo处理基础任务（概念提取）
   - 使用gpt-4仅处理复杂分析（薄弱点聚类）
   - 使用text-embedding-3-small降低embedding成本

4. **重试策略**:
   - 指数退避（exponential backoff）处理API限流
   - 最多重试3次
   - 失败后降级到缓存结果（如果可用）

## Related ADRs

- [ADR-0002: 使用LangGraph实现多Agent协作系统](#0002-langgraph-agents.md) - Graphiti可以作为LangGraph的State层扩展
- [ADR-0014: 艾宾浩斯复习系统](#0014-ebbinghaus-review-system.md) - 依赖Graphiti的时序查询能力（未来ADR）
- [ADR-0004: 异步并行执行引擎](#0004-async-execution-engine.md) - Graphiti查询使用异步API
