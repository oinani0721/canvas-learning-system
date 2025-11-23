# Story GraphRAG.4: 艾宾浩斯触发点4集成

## Status
In Progress

## Story

**As a** 艾宾浩斯复习系统,
**I want** 基于3层记忆系统的行为监控和GraphRAG社区检测，自动识别薄弱点聚集并触发复习推荐,
**so that** 用户能够获得智能化、系统化的复习推荐，而不仅仅是碎片化的单个概念推荐，从而提升复习效率和学习效果。

## Acceptance Criteria

1. `MemoryBehaviorMonitor`后台任务成功实现，每6小时自动运行一次
2. 检测薄弱点聚集：同一GraphRAG社区内≥3个红色/紫色节点时触发告警
3. 触发GraphRAG Global Search进行社区分析，识别相关概念和学习路径
4. 生成定向复习推荐，包含：社区名称、薄弱概念列表、推荐学习顺序
5. 自动添加到艾宾浩斯复习系统（调用`add_concept_for_review`）
6. 触发准确率≥90%（100次检测中，≥90次成功识别并触发）
7. 触发失败不阻塞主流程（记录日志，下次重试，不影响其他触发点）
8. 触发延迟<10秒（从检测到完成复习推荐添加）

## Tasks / Subtasks

### Task 1: 实现MemoryBehaviorMonitor核心类 (AC: 1)

- [ ] **Subtask 1.1**: 创建`MemoryBehaviorMonitor`类
  - [ ] 定义类结构和核心方法
  - [ ] 集成APScheduler实现定时任务（每6小时运行）
  - [ ] 实现3层记忆系统查询接口（Temporal, Graphiti, Semantic）
  - [ ] 添加任务状态跟踪（running, success, failed）

- [ ] **Subtask 1.2**: 配置定时任务
  - [ ] 使用APScheduler的BackgroundScheduler
  - [ ] 配置CronTrigger：每6小时运行（00:00, 06:00, 12:00, 18:00）
  - [ ] 添加任务持久化（避免重启后任务丢失）
  - [ ] 实现手动触发接口（供测试和调试使用）

- [ ] **Subtask 1.3**: 实现日志记录
  - [ ] 记录每次运行的开始时间、结束时间、结果
  - [ ] 记录检测到的薄弱点聚集数量
  - [ ] 记录触发的复习推荐数量
  - [ ] 日志输出到`logs/memory_behavior_monitor.log`

- [ ] **Subtask 1.4**: 单元测试
  - [ ] 测试定时任务触发
  - [ ] 测试手动触发
  - [ ] 测试任务失败不阻塞后续运行
  - [ ] 测试日志记录完整性

### Task 2: 实现3层记忆系统行为查询 (AC: 2, 6)

- [ ] **Subtask 2.1**: 实现Temporal Memory查询（条件1）
  - [ ] 查询长期未访问的已掌握概念（>7天未访问，掌握度≥60分）
  - [ ] 实现Cypher查询：
    ```cypher
    MATCH (c:Concept)-[:HAS_LEARNING_RECORD]->(lr:LearningRecord)
    WHERE lr.last_accessed < datetime() - duration({days: 7})
      AND lr.mastery_score >= 0.6
    RETURN c.name, c.canvas_file, c.node_id, lr.mastery_score, lr.last_accessed
    ORDER BY lr.last_accessed ASC
    LIMIT 50
    ```
  - [ ] 返回概念列表，包含：concept, canvas_file, node_id, mastery, last_accessed
  - [ ] 标记检测原因：`detection_reason="inactive_mastered"`

- [ ] **Subtask 2.2**: 实现Graphiti知识断层查询（条件2）
  - [ ] 查询前置概念已掌握但后续概念长期未学习的情况
  - [ ] 实现Cypher查询：
    ```cypher
    MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(target:Concept)
    WHERE prereq.mastery_score >= 0.8
      AND target.mastery_score < 0.3
      AND target.last_accessed < datetime() - duration({days: 14})
    RETURN target.name, target.canvas_file, target.node_id,
           prereq.name AS prerequisite_name,
           prereq.mastery_score AS prerequisite_mastery
    ORDER BY target.last_accessed ASC
    LIMIT 50
    ```
  - [ ] 返回概念列表，包含前置依赖信息
  - [ ] 标记检测原因：`detection_reason="knowledge_gap"`

- [ ] **Subtask 2.3**: 实现Semantic Memory隐性需求查询（条件3）
  - [ ] 查询相关文档频繁访问但概念本身未复习的情况
  - [ ] 实现LanceDB查询：
    - 查询最近30天访问次数>5的文档
    - 提取文档关联的概念
    - 过滤出>7天未访问的概念
  - [ ] 返回概念列表
  - [ ] 标记检测原因：`detection_reason="implicit_need"`

- [ ] **Subtask 2.4**: 合并和去重3个查询结果
  - [ ] 合并Temporal、Graphiti、Semantic三个来源的概念
  - [ ] 按canvas_file + node_id去重（同一概念只保留一次）
  - [ ] 保留所有检测原因（一个概念可能满足多个条件）
  - [ ] 返回统一格式的概念列表

- [ ] **Subtask 2.5**: 单元测试
  - [ ] 测试Temporal查询返回正确的长期未访问概念
  - [ ] 测试Graphiti查询返回正确的知识断层
  - [ ] 测试Semantic查询返回正确的隐性需求
  - [ ] 测试合并去重逻辑

### Task 3: 实现GraphRAG社区聚类检测 (AC: 2, 3)

- [ ] **Subtask 3.1**: 查询概念所属的GraphRAG社区
  - [ ] 对于每个检测到的薄弱概念，查询其GraphRAG社区
  - [ ] 实现Cypher查询：
    ```cypher
    MATCH (c:ExtractedEntity {name: $concept_name})
          -[:BELONGS_TO_COMMUNITY]->(comm:Community)
    RETURN comm.id, comm.title, comm.level, comm.summary
    ```
  - [ ] 如概念不在任何社区，标记为`community_id=null`
  - [ ] 缓存社区查询结果（避免重复查询）

- [ ] **Subtask 3.2**: 统计每个社区的薄弱概念数量
  - [ ] 按community_id分组统计薄弱概念数量
  - [ ] 识别聚集阈值：同一社区内≥3个薄弱概念
  - [ ] 计算社区薄弱度分数：`weak_score = weak_count / total_concepts_in_community`
  - [ ] 返回薄弱社区列表，按薄弱度分数降序排列

- [ ] **Subtask 3.3**: 触发GraphRAG Global Search进行社区分析
  - [ ] 对于每个薄弱社区，调用GraphRAG Global Search
  - [ ] 查询问题：`f"在{community_title}主题中，哪些概念容易混淆或相互依赖？推荐的学习顺序是什么？"`
  - [ ] 使用本地模型（Qwen2.5-14B）进行社区分析
  - [ ] 解析返回结果，提取：易混淆概念、学习路径、关键依赖关系
  - [ ] 超时处理：如分析>10秒，降级到简单推荐（仅列出薄弱概念）

- [ ] **Subtask 3.4**: 生成定向复习推荐
  - [ ] 基于GraphRAG分析结果生成复习推荐
  - [ ] 推荐格式：
    ```python
    {
      "community_id": "comm_123",
      "community_title": "线性代数基础",
      "weak_concepts": ["特征向量", "特征值", "对角化"],
      "recommended_order": ["特征向量", "特征值", "对角化"],
      "learning_path": "建议先复习特征向量的定义，再理解特征值的计算方法，最后学习对角化应用",
      "confusing_pairs": [("特征向量", "特征值")],
      "detection_reasons": ["inactive_mastered", "knowledge_gap"]
    }
    ```
  - [ ] 如GraphRAG分析超时，使用简化推荐（仅列出概念，按掌握度排序）

- [ ] **Subtask 3.5**: 单元测试
  - [ ] 测试社区查询准确性
  - [ ] 测试薄弱度计算
  - [ ] 测试GraphRAG Global Search调用
  - [ ] 测试推荐格式生成

### Task 4: 集成艾宾浩斯复习系统 (AC: 5, 7)

- [ ] **Subtask 4.1**: 调用`add_concept_for_review`方法
  - [ ] 对于每个薄弱概念，调用艾宾浩斯系统的添加方法
  - [ ] 传递参数：
    ```python
    review_system.add_concept_for_review(
        canvas_file=concept['canvas_file'],
        node_id=concept['node_id'],
        concept=concept['concept'],
        initial_mastery=concept.get('mastery', 0.6),
        trigger_source="behavior_monitoring",  # 标记触发来源
        community_context={
            "community_id": community_id,
            "community_title": community_title,
            "recommended_order": recommended_order
        }
    )
    ```
  - [ ] 记录添加结果（成功/失败）

- [ ] **Subtask 4.2**: 实现批量添加优化
  - [ ] 使用批量接口（如有）而非逐个添加
  - [ ] 实现事务管理（全部成功或全部回滚）
  - [ ] 添加重复检测（避免重复添加已在复习系统中的概念）
  - [ ] 记录批量添加统计（总数、成功数、失败数）

- [ ] **Subtask 4.3**: 实现失败重试机制
  - [ ] 如添加失败，记录失败原因到队列
  - [ ] 下次运行时优先处理失败队列
  - [ ] 最多重试3次，3次后放弃并告警
  - [ ] 失败不阻塞其他概念的添加

- [ ] **Subtask 4.4**: 实现触发日志和通知
  - [ ] 记录每次触发的详细日志：
    - 检测到的社区数量
    - 薄弱概念总数
    - 成功添加到复习系统的概念数
    - 失败概念数和失败原因
  - [ ] 生成触发摘要通知（可选，供用户查看）：
    ```
    🔔 智能复习推荐
    检测到「线性代数基础」社区有3个薄弱概念需要复习：
    - 特征向量（7天未复习）
    - 特征值（知识断层）
    - 对角化（相关文档频繁访问）

    推荐学习顺序：特征向量 → 特征值 → 对角化
    已自动添加到复习计划。
    ```

- [ ] **Subtask 4.5**: 单元测试
  - [ ] 测试单个概念添加
  - [ ] 测试批量添加
  - [ ] 测试失败重试
  - [ ] 测试重复检测
  - [ ] 测试日志记录

### Task 5: 性能优化和监控 (AC: 6, 8)

- [ ] **Subtask 5.1**: 实现触发准确率监控
  - [ ] 定义准确率计算方法：
    - 真正例（TP）：检测到薄弱聚集且用户确实复习
    - 假正例（FP）：检测到但用户未复习（推荐不相关）
    - 准确率 = TP / (TP + FP)
  - [ ] 记录每次触发的准确性标记（需用户反馈或后续复习行为验证）
  - [ ] 实现准确率统计查询：`get_trigger_accuracy() -> float`
  - [ ] 目标：准确率≥90%

- [ ] **Subtask 5.2**: 实现触发延迟优化
  - [ ] 记录每次触发的延迟（从检测开始到添加完成）
  - [ ] 优化慢查询：
    - 对Temporal/Graphiti/Semantic查询添加索引
    - 限制查询结果数量（最多50个概念/来源）
    - 使用并行查询（asyncio.gather）
  - [ ] 优化GraphRAG Global Search调用：
    - 设置超时（10秒）
    - 使用本地模型（避免API延迟）
    - 批量分析（一次分析多个社区）
  - [ ] 验证触发延迟<10秒

- [ ] **Subtask 5.3**: 实现失败不阻塞主流程
  - [ ] 所有异常捕获并记录，不抛出到主流程
  - [ ] 部分失败允许（如10个社区中8个成功，2个失败）
  - [ ] 失败后下次运行时重试
  - [ ] 连续3次失败后发送告警（邮件或日志）

- [ ] **Subtask 5.4**: 实现监控指标
  - [ ] 触发频率：每6小时触发次数统计
  - [ ] 检测命中率：检测到薄弱聚集的次数 / 总运行次数
  - [ ] 触发成功率：成功添加到复习系统的次数 / 检测次数
  - [ ] 平均延迟：触发延迟的平均值和P95
  - [ ] 提供监控查询接口：`get_monitor_stats() -> Dict`

- [ ] **Subtask 5.5**: 单元测试
  - [ ] 测试准确率计算
  - [ ] 测试延迟监控
  - [ ] 测试失败处理
  - [ ] 测试监控指标查询

### Task 6: 集成测试和文档 (ALL AC)

- [ ] **Subtask 6.1**: 端到端集成测试
  - [ ] 模拟3层记忆系统数据（Temporal, Graphiti, Semantic）
  - [ ] 创建测试场景：同一社区有3个红色节点
  - [ ] 触发MemoryBehaviorMonitor
  - [ ] 验证检测到薄弱聚集
  - [ ] 验证调用GraphRAG Global Search
  - [ ] 验证生成复习推荐
  - [ ] 验证添加到艾宾浩斯复习系统

- [ ] **Subtask 6.2**: 性能验证测试
  - [ ] 测试触发延迟<10秒（100次运行，P95<10秒）
  - [ ] 测试触发准确率≥90%（人工验证50次触发）
  - [ ] 测试失败不阻塞（mock失败场景，验证其他流程正常）

- [ ] **Subtask 6.3**: 兼容性测试
  - [ ] 验证不影响现有艾宾浩斯触发点1-3
  - [ ] 验证不影响3层记忆系统性能
  - [ ] 验证与GraphRAG.1, GraphRAG.2集成正常

- [ ] **Subtask 6.4**: 创建用户文档
  - [ ] 编写`docs/user-guides/ebbinghaus-trigger-point-4-guide.md`
  - [ ] 包含：触发点4原理、触发条件、如何查看触发日志
  - [ ] 添加常见问题解答（触发频率、准确率、关闭方法）
  - [ ] 添加监控指标查看指南

- [ ] **Subtask 6.5**: 创建开发者文档
  - [ ] 编写`docs/architecture/ebbinghaus-trigger-point-4-architecture.md`
  - [ ] 包含：MemoryBehaviorMonitor架构、3层记忆系统查询流程、GraphRAG集成
  - [ ] 添加扩展指南（如何添加新的检测条件）
  - [ ] 添加监控指标设计文档

## Dev Notes

### 架构上下文

**艾宾浩斯触发点4在PRD中的定义** [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md#Line 1572-1624]

本Story实现PRD v1.1.6定义的第4个触发点，基于3层记忆系统的行为监控主动识别需要复习的概念。

```
┌──────────────────────────────────────────────────────────┐
│  艾宾浩斯触发点4: 3层记忆系统行为监控触发                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │ Temporal       │  │ Graphiti       │  │ Semantic    │ │
│  │ Memory         │  │ Knowledge      │  │ Memory      │ │
│  │ (行为时序)     │  │ Graph          │  │ (文档向量)  │ │
│  └────────┬───────┘  └────────┬───────┘  └──────┬──────┘ │
│           │                   │                  │        │
│           ▼                   ▼                  ▼        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ MemoryBehaviorMonitor (每6小时运行)                  │ │
│  │ - 条件1: 长期未访问的已掌握概念 (Temporal)           │ │
│  │ - 条件2: 知识断层检测 (Graphiti)                    │ │
│  │ - 条件3: 隐性需求检测 (Semantic)                    │ │
│  └────────────────────────┬─────────────────────────────┘ │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ GraphRAG社区聚类检测                                 │ │
│  │ - 查询薄弱概念所属社区                               │ │
│  │ - 统计社区薄弱度（≥3个红色/紫色节点 → 告警）        │ │
│  │ - 触发GraphRAG Global Search进行社区分析             │ │
│  └────────────────────────┬─────────────────────────────┘ │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 生成定向复习推荐                                     │ │
│  │ - 社区名称: "线性代数基础"                          │ │
│  │ - 薄弱概念: [特征向量, 特征值, 对角化]              │ │
│  │ - 推荐顺序: 特征向量 → 特征值 → 对角化              │ │
│  └────────────────────────┬─────────────────────────────┘ │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 艾宾浩斯复习系统 (add_concept_for_review)            │ │
│  │ - 批量添加薄弱概念到复习计划                         │ │
│  │ - 标记触发来源: "behavior_monitoring"               │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**Epic目标** [Source: docs/epics/epic-graphrag-integration.md#目标4]

- MemoryBehaviorMonitor后台任务（每6小时运行）
- 检测薄弱点聚集（同一社区≥3个红色节点）
- 触发GraphRAG社区分析并生成复习推荐
- 触发失败不阻塞主流程（非关键路径）

### 技术栈

**APScheduler定时任务** [Source: Story GraphRAG.1 Dev Notes]

```python
# ✅ Verified from Story GraphRAG.1 - APScheduler使用模式
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class MemoryBehaviorMonitor:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self.run_monitoring_task,
            trigger=CronTrigger(hour='*/6'),  # 每6小时运行
            id='memory_behavior_monitor',
            name='3层记忆系统行为监控'
        )

    def start(self):
        """启动监控任务"""
        self.scheduler.start()
        logger.info("✅ MemoryBehaviorMonitor已启动")

    def run_monitoring_task(self):
        """监控任务主流程"""
        try:
            logger.info("🔍 开始3层记忆系统行为监控...")

            # Step 1: 查询3层记忆系统
            weak_concepts = self.query_all_memory_layers()

            # Step 2: GraphRAG社区聚类检测
            weak_communities = self.detect_weak_communities(weak_concepts)

            # Step 3: 触发GraphRAG Global Search
            recommendations = self.analyze_communities(weak_communities)

            # Step 4: 添加到艾宾浩斯复习系统
            self.add_to_review_system(recommendations)

            logger.info(f"✅ 监控任务完成: 检测到{len(weak_communities)}个薄弱社区")

        except Exception as e:
            # 失败不阻塞主流程
            logger.error(f"❌ 监控任务失败: {e}")
```

**3层记忆系统查询** [Source: PRD Line 1576-1608 + LANGGRAPH架构]

```python
def query_all_memory_layers(self) -> List[Dict]:
    """查询3层记忆系统获取薄弱概念"""

    # ✅ Verified from PRD Line 1589-1594 - Temporal Memory查询
    # 条件1: Temporal Memory - 长期未访问的已掌握概念
    inactive_concepts = self.query_temporal_memory(
        days_threshold=7,
        min_mastery=0.6
    )

    # ✅ Verified from PRD Line 1596-1601 - Graphiti查询
    # 条件2: Graphiti - 知识断层检测
    knowledge_gaps = self.query_graphiti_knowledge_graph(
        min_prerequisite_mastery=0.8,
        gap_days_threshold=14
    )

    # ✅ Verified from PRD Line 1603-1608 - Semantic Memory查询
    # 条件3: Semantic Memory - 隐性需求检测
    implicit_needs = self.query_semantic_memory(
        related_access_threshold=5,
        concept_inactive_days=7
    )

    # 合并并去重
    all_concepts = self._merge_and_deduplicate(
        inactive_concepts,
        knowledge_gaps,
        implicit_needs
    )

    return all_concepts
```

**Temporal Memory查询实现** [Source: PRD + Neo4j Cypher]

```python
# ✅ Verified from Context7 Neo4j Cypher Manual - 时间查询模式
def query_temporal_memory(
    self,
    days_threshold: int = 7,
    min_mastery: float = 0.6
) -> List[Dict]:
    """查询长期未访问的已掌握概念

    Args:
        days_threshold: 未访问天数阈值
        min_mastery: 最低掌握度分数

    Returns:
        概念列表，包含：concept, canvas_file, node_id, mastery, last_accessed
    """
    query = """
    MATCH (c:Concept)-[:HAS_LEARNING_RECORD]->(lr:LearningRecord)
    WHERE lr.last_accessed < datetime() - duration({days: $days_threshold})
      AND lr.mastery_score >= $min_mastery
    RETURN
      c.name AS concept,
      c.canvas_file AS canvas_file,
      c.node_id AS node_id,
      lr.mastery_score AS mastery,
      lr.last_accessed AS last_accessed,
      'inactive_mastered' AS detection_reason
    ORDER BY lr.last_accessed ASC
    LIMIT 50
    """

    with self.neo4j_driver.session() as session:
        result = session.run(query, days_threshold=days_threshold, min_mastery=min_mastery)
        return [dict(record) for record in result]
```

**Graphiti知识断层查询** [Source: PRD + Graphiti Schema]

```python
# ✅ Verified from Graphiti Skills - 前置依赖查询模式
def query_graphiti_knowledge_graph(
    self,
    min_prerequisite_mastery: float = 0.8,
    gap_days_threshold: int = 14
) -> List[Dict]:
    """查询知识断层（前置已掌握但后续未学习）

    Args:
        min_prerequisite_mastery: 前置概念最低掌握度
        gap_days_threshold: 后续概念未访问天数阈值

    Returns:
        概念列表，包含前置依赖信息
    """
    query = """
    MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(target:Concept)
    WHERE prereq.mastery_score >= $min_prereq_mastery
      AND target.mastery_score < 0.3
      AND target.last_accessed < datetime() - duration({days: $gap_days})
    RETURN
      target.name AS concept,
      target.canvas_file AS canvas_file,
      target.node_id AS node_id,
      target.mastery_score AS mastery,
      prereq.name AS prerequisite_name,
      prereq.mastery_score AS prerequisite_mastery,
      'knowledge_gap' AS detection_reason
    ORDER BY target.last_accessed ASC
    LIMIT 50
    """

    with self.neo4j_driver.session() as session:
        result = session.run(
            query,
            min_prereq_mastery=min_prerequisite_mastery,
            gap_days=gap_days_threshold
        )
        return [dict(record) for record in result]
```

**GraphRAG社区聚类检测** [Source: GraphRAG文档 + Epic设计]

```python
def detect_weak_communities(self, weak_concepts: List[Dict]) -> List[Dict]:
    """检测薄弱概念聚集的社区

    Args:
        weak_concepts: 薄弱概念列表

    Returns:
        薄弱社区列表，按薄弱度排序
    """
    # Step 1: 查询每个概念所属的GraphRAG社区
    concept_communities = {}
    for concept in weak_concepts:
        community = self._query_concept_community(concept['concept'])
        if community:
            concept_communities[concept['concept']] = community

    # Step 2: 按社区分组统计薄弱概念数量
    community_stats = defaultdict(list)
    for concept, community in concept_communities.items():
        community_id = community['id']
        community_stats[community_id].append(concept)

    # Step 3: 过滤出薄弱社区（≥3个薄弱概念）
    weak_communities = []
    for community_id, concepts in community_stats.items():
        if len(concepts) >= 3:
            community = concept_communities[concepts[0]]  # 获取社区信息
            total_concepts = self._query_community_size(community_id)
            weak_score = len(concepts) / total_concepts

            weak_communities.append({
                'community_id': community_id,
                'community_title': community['title'],
                'community_level': community['level'],
                'weak_concepts': concepts,
                'weak_count': len(concepts),
                'total_count': total_concepts,
                'weak_score': weak_score
            })

    # Step 4: 按薄弱度降序排序
    weak_communities.sort(key=lambda x: x['weak_score'], reverse=True)

    return weak_communities
```

**GraphRAG Global Search集成** [Source: LANGGRAPH Section 10.4.4]

```python
# ✅ Verified from LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md Section 10.4.4
from graphrag.query.structured_search.global_search import GlobalSearch

def analyze_communities(self, weak_communities: List[Dict]) -> List[Dict]:
    """使用GraphRAG Global Search分析薄弱社区

    Args:
        weak_communities: 薄弱社区列表

    Returns:
        复习推荐列表
    """
    recommendations = []

    for community in weak_communities:
        try:
            # 构造查询问题
            query = f"""
            在「{community['community_title']}」主题中，
            以下概念需要复习：{', '.join(community['weak_concepts'])}。

            请分析：
            1. 哪些概念容易混淆或相互依赖？
            2. 推荐的学习顺序是什么？
            3. 有哪些关键知识点需要优先掌握？
            """

            # ✅ Verified from LANGGRAPH Section 10.4.4 - GraphRAG Global Search调用
            searcher = GlobalSearch(
                llm=self.local_llm,  # 使用Qwen2.5-14B本地模型
                context_builder=self.context_builder,
                max_data_tokens=12000
            )

            # 执行Global Search
            result = await searcher.asearch(
                query=query,
                community_level=community['community_level'],
                response_type="multiple paragraphs"
            )

            # 解析结果，提取学习路径
            recommendation = self._parse_graphrag_response(
                community=community,
                graphrag_result=result
            )

            recommendations.append(recommendation)

        except Exception as e:
            # 降级处理：使用简单推荐
            logger.warning(f"GraphRAG分析失败，使用简单推荐: {e}")
            recommendation = self._generate_simple_recommendation(community)
            recommendations.append(recommendation)

    return recommendations
```

**添加到艾宾浩斯复习系统** [Source: PRD Line 1614-1623]

```python
# ✅ Verified from PRD Line 1614-1623 - 批量添加到复习系统
def add_to_review_system(self, recommendations: List[Dict]) -> Dict:
    """批量添加到艾宾浩斯复习系统

    Args:
        recommendations: 复习推荐列表

    Returns:
        添加统计信息
    """
    from ebbinghaus_review_system import EbbinghausReviewSystem

    review_system = EbbinghausReviewSystem()
    success_count = 0
    fail_count = 0

    for rec in recommendations:
        for concept in rec['weak_concepts']:
            try:
                # ✅ Verified from PRD Line 1615-1622
                review_system.add_concept_for_review(
                    canvas_file=concept['canvas_file'],
                    node_id=concept['node_id'],
                    concept=concept['concept'],
                    initial_mastery=concept.get('mastery', 0.6),
                    trigger_source="behavior_monitoring",  # 标记触发来源
                    community_context={
                        'community_id': rec['community_id'],
                        'community_title': rec['community_title'],
                        'recommended_order': rec['recommended_order']
                    }
                )

                success_count += 1
                logger.info(f"✅ 行为监控触发复习: {concept['concept']} (社区: {rec['community_title']})")

            except Exception as e:
                fail_count += 1
                logger.error(f"❌ 添加失败: {concept['concept']}, 原因: {e}")

    return {
        'total': len([c for r in recommendations for c in r['weak_concepts']]),
        'success': success_count,
        'fail': fail_count,
        'recommendations': recommendations
    }
```

### 配置文件设计

**配置文件位置**: `config/memory_behavior_monitor.json`

```json
{
  "monitor": {
    "enabled": true,
    "schedule": {
      "interval_hours": 6,
      "cron_expression": "0 */6 * * *"
    },
    "timeout": 300
  },
  "detection": {
    "temporal": {
      "enabled": true,
      "days_threshold": 7,
      "min_mastery": 0.6
    },
    "graphiti": {
      "enabled": true,
      "min_prerequisite_mastery": 0.8,
      "gap_days_threshold": 14
    },
    "semantic": {
      "enabled": true,
      "related_access_threshold": 5,
      "concept_inactive_days": 7
    }
  },
  "clustering": {
    "weak_concept_threshold": 3,
    "community_levels": [0, 1, 2],
    "max_communities_per_run": 10
  },
  "graphrag": {
    "enabled": true,
    "timeout": 10,
    "use_local_model": true,
    "fallback_to_simple": true
  },
  "review_system": {
    "batch_size": 50,
    "duplicate_detection": true,
    "max_retries": 3
  },
  "monitoring": {
    "log_level": "INFO",
    "accuracy_tracking": true,
    "performance_tracking": true,
    "alert_on_failure": true
  }
}
```

### 文件位置

**新创建的文件：**
```
C:/Users/ROG/托福/
├── src/
│   ├── ebbinghaus/
│   │   ├── memory_behavior_monitor.py      # MemoryBehaviorMonitor类
│   │   ├── memory_layer_queries.py         # 3层记忆系统查询
│   │   ├── community_clustering.py         # GraphRAG社区聚类检测
│   │   ├── review_recommendation.py        # 复习推荐生成
│   │   └── trigger_point_4_integration.py  # 触发点4集成类
│   └── ...
├── tests/
│   ├── test_memory_behavior_monitor.py
│   ├── test_memory_layer_queries.py
│   ├── test_community_clustering.py
│   └── test_trigger_point_4_e2e.py
├── config/
│   └── memory_behavior_monitor.json        # 监控配置文件
├── logs/
│   └── memory_behavior_monitor.log         # 监控日志
└── docs/
    ├── user-guides/
    │   └── ebbinghaus-trigger-point-4-guide.md
    └── architecture/
        └── ebbinghaus-trigger-point-4-architecture.md
```

### 性能要求

**延迟目标** [Source: Epic AC]

| 操作 | 目标延迟 |
|------|---------|
| 3层记忆系统查询（总计） | <3秒 |
| GraphRAG社区聚类检测 | <2秒 |
| GraphRAG Global Search分析 | <8秒 |
| 添加到复习系统 | <2秒 |
| **总触发延迟** | **<10秒** |

**准确率目标** [Source: Epic AC]
- 触发准确率: ≥90%（100次检测中≥90次成功识别并触发）
- 降级率: <10%（GraphRAG分析失败，使用简单推荐）
- 复习接受率: ≥70%（用户接受复习推荐并生成检验白板）

### 依赖项

**Python依赖** [Source: requirements.txt]
```
# 定时任务
apscheduler>=3.10.0

# GraphRAG
graphrag>=0.1.0

# 3层记忆系统（已有）
neo4j>=5.14.0
lancedb>=0.3.0
```

**系统依赖**
- **Neo4j**: 存储Temporal Memory和Graphiti Knowledge Graph
- **LanceDB**: 存储Semantic Memory（文档向量）
- **GraphRAG索引**: Story GraphRAG.1生成的实体和社区数据
- **艾宾浩斯复习系统**: 提供`add_concept_for_review`接口

### 测试要求

**测试覆盖率目标** [Source: CLAUDE.md#测试规范]
- 单元测试覆盖率: ≥90%
- 集成测试覆盖关键流程: 100%

**关键测试用例**

1. **3层记忆系统查询测试**
   - Temporal Memory查询准确性
   - Graphiti知识断层检测
   - Semantic Memory隐性需求检测
   - 合并去重逻辑

2. **GraphRAG社区聚类测试**
   - 社区查询准确性
   - 薄弱度计算
   - 聚类阈值触发（≥3个薄弱概念）
   - GraphRAG Global Search调用

3. **复习系统集成测试**
   - 单个概念添加
   - 批量添加
   - 重复检测
   - 失败重试

4. **端到端测试**
   - 完整触发流程（检测→聚类→分析→推荐→添加）
   - 触发延迟<10秒
   - 触发准确率≥90%
   - 失败不阻塞

### 故障排查

**问题1: 触发准确率<90%**
- **原因**: 检测条件设置不合理或GraphRAG分析质量差
- **解决**:
  1. 调整检测阈值（days_threshold, min_mastery等）
  2. 优化GraphRAG Prompt模板
  3. 增加人工标注样本，微调检测条件
  4. 收集用户反馈，改进推荐算法

**问题2: 触发延迟>10秒**
- **原因**: 3层记忆系统查询慢或GraphRAG分析超时
- **解决**:
  1. 添加Neo4j索引（last_accessed, mastery_score）
  2. 限制查询结果数量（50个/来源）
  3. 使用并行查询（asyncio.gather）
  4. 降低GraphRAG分析超时（10秒→5秒）

**问题3: GraphRAG分析频繁失败**
- **原因**: 本地模型推理失败或超时
- **解决**:
  1. 检查Ollama服务状态
  2. 增加超时时间（10秒→15秒）
  3. 使用简单推荐作为降级方案
  4. 记录失败原因，分析Prompt问题

**问题4: 复习系统添加失败**
- **原因**: 艾宾浩斯系统接口错误或重复添加
- **解决**:
  1. 实现重复检测（避免重复添加）
  2. 添加失败重试机制（最多3次）
  3. 记录失败原因到日志
  4. 下次运行时优先处理失败队列

### 监控指标

**关键监控指标** [Source: Epic成功指标]

1. **触发健康度**
   - 触发频率: 每6小时1次（正常）
   - 检测命中率: 检测到薄弱聚集的次数 / 总运行次数（目标≥50%）
   - 触发成功率: 成功添加到复习系统的次数 / 检测次数（目标≥95%）
   - 触发准确率: ≥90%

2. **性能指标**
   - 触发延迟P50/P95/P99: 目标P95<10秒
   - 3层记忆系统查询延迟: 目标<3秒
   - GraphRAG分析延迟: 目标<8秒
   - 复习系统添加延迟: 目标<2秒

3. **质量指标**
   - 复习接受率: 用户接受推荐并生成检验白板的比例（目标≥70%）
   - 降级率: GraphRAG分析失败，使用简单推荐的比例（目标<10%）
   - 用户满意度: 用户对复习推荐的评分（1-5星，目标≥4星）

4. **系统影响**
   - 对3层记忆系统性能影响: 查询延迟增加<5%
   - 对艾宾浩斯系统影响: 复习推荐数量增加≥30%
   - 对用户学习效率影响: 复习效率提升≥20%（基于用户反馈）

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-14 | 1.0 | 初始Story创建，基于PRD触发点4设计和Epic GraphRAG集成 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
claude-sonnet-4.5 (claude-sonnet-4-5-20250929)

### Debug Log References
待开发

### Completion Notes
待开发

### File List
待开发

## QA Results

### Review Date
待QA审查

### Reviewed By
Quinn (Senior Developer QA)

### Code Quality Assessment
待QA审查

### Compliance Check
待QA审查

### Final Status
In Progress - 等待开发开始
