# Story GraphRAG.1: GraphRAG数据采集Pipeline

---
**Status**: ❌ **Deprecated (已废弃)**
**Deprecated Date**: 2025-11-14
**Deprecated Reason**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停
**Replacement**: EPIC-Neo4j-GDS-Integration
**Decision Record**: ADR-004, SCP-005
---

## ⚠️ Story状态：已废弃

**废弃日期**: 2025-11-14
**废弃原因**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停

**替代方案**:
- Epic层面：EPIC-Neo4j-GDS-Integration (Neo4j GDS提供等效能力)
- 功能实现：Neo4j GDS Leiden算法提供社区检测功能

**详情参见**:
- Sprint Change Proposal: SCP-005 (GraphRAG过度设计纠偏)
- Architecture Decision Record: ADR-004 (Do Not Integrate GraphRAG)

**历史价值**: 保留此Story作为技术规划参考

---

## 原始Story定义（以下内容为历史记录）

---

## Status
~~In Progress~~ ❌ Deprecated

## Story

**As a** Canvas学习系统,
**I want** 从Canvas内容自动提取实体和关系并构建GraphRAG索引,
**so that** 系统能够支持数据集级全局查询和概念社区检测，识别学习模式和薄弱环节聚类。

## Acceptance Criteria

1. Canvas内容更新后自动触发实体提取（LLM powered）
2. 实体和关系存储到Neo4j（使用`:GraphRAGNode`标签命名空间隔离）
3. 支持增量索引（仅处理新增内容，每日凌晨2-3点自动运行）
4. 支持全量索引（每周完全重建，每周日凌晨2-4点自动运行）
5. 索引过程不阻塞Graphiti实时写入（独立事务，READ COMMITTED隔离级别）
6. 提取准确率≥80%（通过人工抽样验证100个样本）
7. 增量索引延迟<5分钟（从Canvas更新到索引完成）
8. 全量索引完成时间<2小时（1000个Canvas节点）

## Tasks / Subtasks

### Task 1: 实现Canvas内容监控与变更检测 (AC: 1, 3, 7)

- [ ] **Subtask 1.1**: 创建`CanvasChangeMonitor`类
  - [ ] 实现Canvas文件变更监听（基于文件修改时间戳）
  - [ ] 维护Canvas最后处理时间的元数据存储（SQLite `canvas_metadata.db`）
  - [ ] 检测新增/修改的节点和边
  - [ ] 实现增量变更队列（`collections.deque`）

- [ ] **Subtask 1.2**: 实现变更事件触发机制
  - [ ] 定时扫描Canvas文件夹（每5分钟扫描一次）
  - [ ] 生成变更事件对象（`CanvasChangeEvent`）
  - [ ] 事件包含：canvas_path, changed_nodes, changed_edges, timestamp
  - [ ] 添加事件日志记录（logging到`logs/canvas_changes.log`）

- [ ] **Subtask 1.3**: 单元测试
  - [ ] 测试新Canvas文件创建触发全量索引
  - [ ] 测试Canvas节点修改触发增量索引
  - [ ] 测试变更检测准确性（100个节点场景）
  - [ ] 测试多Canvas并发变更处理

### Task 2: 实现LLM-powered实体和关系提取 (AC: 1, 6)

- [ ] **Subtask 2.1**: 创建`GraphRAGEntityExtractor`类
  - [ ] 设计Prompt模板（参考Microsoft GraphRAG Entity Extraction模式）
  - [ ] 实现与Qwen2.5-14B的集成（通过Ollama API）
  - [ ] 处理Canvas节点文本内容提取
  - [ ] 处理Canvas边关系提取

- [ ] **Subtask 2.2**: 实现实体提取逻辑
  - [ ] 使用Qwen2.5提取实体（名称、类型、描述）
  - [ ] 实体类型分类：Concept（概念）, Topic（主题）, Skill（技能）
  - [ ] 实现实体去重和规范化（相似实体合并）
  - [ ] 添加提取置信度评分（0-1）

- [ ] **Subtask 2.3**: 实现关系提取逻辑
  - [ ] 使用Qwen2.5提取关系（源实体、目标实体、关系类型）
  - [ ] 关系类型分类：RELATED_TO, PREREQUISITE_OF, SIMILAR_TO
  - [ ] 从Canvas边标签推断关系类型
  - [ ] 添加关系强度评分（0-1）

- [ ] **Subtask 2.4**: 实现质量验证机制
  - [ ] 提取结果结构化验证（JSON Schema）
  - [ ] 实体名称长度限制（2-100字符）
  - [ ] 关系三元组完整性检查（源、目标、类型都存在）
  - [ ] 过滤低置信度结果（threshold=0.3）

- [ ] **Subtask 2.5**: 集成LangGraph Skills提取参考
  - [ ] ✅ 查询LangGraph Skills获取实体提取最佳实践
  - [ ] 实现基于LangGraph推荐的提示词工程模式
  - [ ] 添加few-shot示例到提示词（3-5个示例）
  - [ ] 验证提取结果格式符合GraphRAG要求

- [ ] **Subtask 2.6**: 单元测试和准确率验证
  - [ ] 创建测试Canvas样本（20个节点，涵盖各类型内容）
  - [ ] 人工标注Ground Truth（实体和关系）
  - [ ] 实现准确率计算（Precision, Recall, F1）
  - [ ] 验证提取准确率≥80%（如不满足，调整Prompt）
  - [ ] 测试边缘情况：空节点、超长文本、特殊字符

### Task 3: 实现Neo4j存储层与命名空间隔离 (AC: 2, 5)

- [ ] **Subtask 3.1**: 设计Neo4j Schema
  - [ ] 定义`:GraphRAGNode`基础标签（所有GraphRAG实体共用）
  - [ ] 定义子标签：`:ExtractedEntity`, `:Community`, `:GlobalSummary`
  - [ ] 定义关系类型：`:RELATED_TO`, `:PREREQUISITE_OF`, `:SIMILAR_TO`
  - [ ] 添加属性：name, description, entity_type, confidence, created_at, canvas_source

- [ ] **Subtask 3.2**: 创建`GraphRAGNeo4jStorage`类
  - [ ] 实现Neo4j连接池管理（neo4j-driver-python）
  - [ ] 实现事务隔离（READ COMMITTED级别）
  - [ ] 实现批量写入优化（UNWIND + CREATE）
  - [ ] 添加写入重试机制（指数退避，最多3次）

- [ ] **Subtask 3.3**: 实现实体和关系存储方法
  - [ ] `store_entity(entity: Dict) -> str`: 存储单个实体，返回Neo4j node ID
  - [ ] `store_entities_batch(entities: List[Dict]) -> List[str]`: 批量存储（批大小=100）
  - [ ] `store_relationship(rel: Dict) -> str`: 存储单个关系
  - [ ] `store_relationships_batch(rels: List[Dict]) -> List[str]`: 批量存储
  - [ ] 所有节点自动添加`:GraphRAGNode`标签

- [ ] **Subtask 3.4**: 实现命名空间隔离验证
  - [ ] 查询验证：Graphiti节点使用`:GraphitiNode`标签
  - [ ] 查询验证：GraphRAG节点使用`:GraphRAGNode`标签
  - [ ] 创建Cypher查询测试两个命名空间不冲突
  - [ ] 性能测试：并发写入Graphiti和GraphRAG不互相阻塞

- [ ] **Subtask 3.5**: 集成Context7 MCP查询Neo4j最佳实践
  - [ ] ✅ 查询Context7 Neo4j Cypher Manual获取批量写入优化方法
  - [ ] ✅ 查询Neo4j Operations Manual获取事务隔离最佳实践
  - [ ] 实现APOC存储过程集成（如果可用，用于批量操作）
  - [ ] 实现索引创建：`CREATE INDEX ON :GraphRAGNode(name)`
  - [ ] 实现唯一性约束：`CREATE CONSTRAINT ON (e:ExtractedEntity) ASSERT e.name IS UNIQUE`

- [ ] **Subtask 3.6**: 单元测试和性能验证
  - [ ] 测试单个实体存储和检索
  - [ ] 测试批量存储（1000个实体，性能<10秒）
  - [ ] 测试命名空间隔离（Graphiti和GraphRAG节点不混淆）
  - [ ] 测试并发写入（Graphiti实时写入不受GraphRAG索引影响）
  - [ ] 测试事务回滚（写入失败不影响已有数据）

### Task 4: 实现增量索引调度器 (AC: 3, 7)

- [ ] **Subtask 4.1**: 创建`IncrementalIndexScheduler`类
  - [ ] 使用APScheduler实现定时任务（每日凌晨2点触发）
  - [ ] 集成`CanvasChangeMonitor`获取变更列表
  - [ ] 实现索引任务队列（防止任务堆积）
  - [ ] 添加任务状态跟踪（pending, running, completed, failed）

- [ ] **Subtask 4.2**: 实现增量索引Pipeline
  - [ ] Step 1: 获取自上次索引以来的Canvas变更
  - [ ] Step 2: 调用`GraphRAGEntityExtractor`提取新增实体和关系
  - [ ] Step 3: 调用`GraphRAGNeo4jStorage`批量存储
  - [ ] Step 4: 更新Canvas元数据（最后处理时间）
  - [ ] Step 5: 记录索引统计（新增实体数、关系数、耗时）

- [ ] **Subtask 4.3**: 实现延迟监控
  - [ ] 记录Canvas变更时间戳（change_detected_at）
  - [ ] 记录索引完成时间戳（index_completed_at）
  - [ ] 计算索引延迟（index_completed_at - change_detected_at）
  - [ ] 验证延迟<5分钟（如超时，告警）

- [ ] **Subtask 4.4**: 单元测试
  - [ ] 测试增量索引只处理变更内容（不重复处理）
  - [ ] 测试定时触发机制（模拟时间推进）
  - [ ] 测试多Canvas并发增量索引
  - [ ] 测试索引延迟计算准确性

### Task 5: 实现全量索引调度器 (AC: 4, 8)

- [ ] **Subtask 5.1**: 创建`FullIndexScheduler`类
  - [ ] 使用APScheduler实现周调度（每周日凌晨2点触发）
  - [ ] 实现索引前备份机制（备份当前Neo4j GraphRAG节点到JSON）
  - [ ] 实现失败回滚机制（如索引失败，从备份恢复）
  - [ ] 添加索引进度跟踪（处理了多少Canvas）

- [ ] **Subtask 5.2**: 实现全量索引Pipeline
  - [ ] Step 1: 清空Neo4j中所有`:GraphRAGNode`节点
  - [ ] Step 2: 扫描所有Canvas文件（递归遍历Canvas文件夹）
  - [ ] Step 3: 对每个Canvas调用`GraphRAGEntityExtractor`提取实体和关系
  - [ ] Step 4: 批量存储到Neo4j（批大小=500）
  - [ ] Step 5: 触发Leiden社区检测（为后续Global Search准备）
  - [ ] Step 6: 记录全量索引统计（总实体数、关系数、耗时）

- [ ] **Subtask 5.3**: 实现性能优化
  - [ ] 使用多线程并行处理Canvas文件（ThreadPoolExecutor, max_workers=4）
  - [ ] 实现批量提交（每100个实体提交一次事务）
  - [ ] 添加进度条显示（tqdm库）
  - [ ] 实现断点续传（如索引中断，从上次位置继续）

- [ ] **Subtask 5.4**: 实现完成时间验证
  - [ ] 测试1000个Canvas节点的全量索引时间
  - [ ] 验证完成时间<2小时
  - [ ] 如超时，调整批大小和并行度

- [ ] **Subtask 5.5**: 单元测试
  - [ ] 测试全量索引清空旧数据
  - [ ] 测试全量索引处理所有Canvas
  - [ ] 测试失败回滚机制
  - [ ] 测试性能（1000节点<2小时）

### Task 6: 集成测试和文档 (ALL AC)

- [ ] **Subtask 6.1**: 端到端集成测试
  - [ ] 测试完整流程：Canvas创建 → 变更检测 → 实体提取 → Neo4j存储 → 索引完成
  - [ ] 测试增量索引流程（修改Canvas → 自动触发 → 仅处理变更）
  - [ ] 测试全量索引流程（定时触发 → 清空旧数据 → 重建索引）
  - [ ] 测试与Graphiti共存（GraphRAG索引不影响Graphiti实时写入）

- [ ] **Subtask 6.2**: 准确率人工验证
  - [ ] 随机抽样100个Canvas节点
  - [ ] 人工标注实体和关系（Ground Truth）
  - [ ] 对比系统提取结果
  - [ ] 计算准确率（Precision, Recall, F1）
  - [ ] 验证准确率≥80%

- [ ] **Subtask 6.3**: 性能基准测试
  - [ ] 测试增量索引延迟（10个Canvas变更 → 验证<5分钟）
  - [ ] 测试全量索引完成时间（1000个节点 → 验证<2小时）
  - [ ] 测试Neo4j存储性能（10000个实体批量写入 → 验证<30秒）

- [ ] **Subtask 6.4**: 创建用户文档
  - [ ] 编写`docs/user-guides/graphrag-data-pipeline-setup.md`
  - [ ] 包含：安装依赖、配置Qwen2.5、启动调度器
  - [ ] 添加故障排查章节（常见问题和解决方法）
  - [ ] 添加监控指南（查看索引日志、统计数据）

- [ ] **Subtask 6.5**: 创建开发者文档
  - [ ] 编写`docs/architecture/graphrag-data-pipeline-architecture.md`
  - [ ] 包含：架构图、类设计、数据流、Neo4j Schema
  - [ ] 添加扩展指南（如何添加新的实体类型、关系类型）

## Dev Notes

### 架构上下文

**GraphRAG集成架构** [Source: docs/architecture/GRAPHRAG-INTEGRATION-DESIGN.md]

本Story实现GraphRAG数据采集Pipeline，是GraphRAG集成的第一步，也是后续Global Search和社区检测的数据基础。

```
┌─────────────────────────────────────────────────────────┐
│  GraphRAG数据采集Pipeline                               │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ Canvas变更    │→ │ LLM实体提取     │→ │ Neo4j存储  │  │
│  │ 监控          │  │ (Qwen2.5-14B)  │  │ :GraphRAG  │  │
│  └───────────────┘  └────────────────┘  └────────────┘  │
│         ↓                    ↓                   ↓       │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ 增量索引      │  │ 全量索引        │  │ Leiden社区 │  │
│  │ (每日2-3点)   │  │ (每周日2-4点)   │  │ 检测       │  │
│  └───────────────┘  └────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**四层记忆架构中的位置** [Source: docs/architecture/LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md]

GraphRAG是第4层（战略记忆层），提供数据集级全局分析能力：

```
Layer 1: LanceDB (Semantic Memory - 语义向量)
Layer 2: Graphiti (Episodic Memory - 实时知识图谱)
Layer 3: Temporal (Behavioral Memory - 学习行为时序)
Layer 4: GraphRAG (Strategic Memory - 社区检测) ← 本Story实现
```

### 技术栈

**本地LLM集成** [Source: docs/epics/epic-graphrag-integration.md#本地模型优先架构]

核心决策：使用Qwen2.5-14B替代GPT-4o，成本从$570/月降至$57/月（90%节省）

```python
# ✅ Verified from Context7 - 本地模型集成模式
from langchain_community.llms import Ollama

llm = Ollama(
    model="qwen2.5:14b-instruct",
    base_url="http://localhost:11434",
    temperature=0.2
)
```

**Microsoft GraphRAG Entity Extraction模式** [Source: Epic文档 + GraphRAG官方文档]

使用Few-shot Prompting进行实体和关系提取：

```python
# Entity Extraction Prompt Template
ENTITY_EXTRACTION_PROMPT = """
你是一个专业的知识图谱实体提取专家。请从以下Canvas学习内容中提取关键实体和关系。

**输入内容**: {canvas_content}

**提取要求**:
1. 实体类型：Concept（概念）, Topic（主题）, Skill（技能）
2. 关系类型：RELATED_TO（相关）, PREREQUISITE_OF（前置依赖）, SIMILAR_TO（相似）
3. 每个实体包含：名称、类型、简短描述、置信度（0-1）
4. 每个关系包含：源实体、目标实体、关系类型、强度（0-1）

**输出格式** (JSON):
{{
  "entities": [
    {{"name": "实体名称", "type": "Concept", "description": "描述", "confidence": 0.9}}
  ],
  "relationships": [
    {{"source": "实体A", "target": "实体B", "type": "PREREQUISITE_OF", "strength": 0.8}}
  ]
}}

**Few-shot示例**:
输入: "线性代数中，特征向量是矩阵的重要属性，用于主成分分析（PCA）"
输出:
{{
  "entities": [
    {{"name": "特征向量", "type": "Concept", "description": "矩阵的特殊向量", "confidence": 0.95}},
    {{"name": "主成分分析", "type": "Skill", "description": "降维技术", "confidence": 0.9}},
    {{"name": "线性代数", "type": "Topic", "description": "数学分支", "confidence": 1.0}}
  ],
  "relationships": [
    {{"source": "特征向量", "target": "主成分分析", "type": "PREREQUISITE_OF", "strength": 0.9}},
    {{"source": "特征向量", "target": "线性代数", "type": "RELATED_TO", "strength": 1.0}}
  ]
}}

请提取上述Canvas内容的实体和关系：
"""
```

**Neo4j Python Driver** [Source: Context7 Neo4j Operations Manual]

```python
# ✅ Verified from Context7 Neo4j Operations Manual - 批量写入最佳实践
from neo4j import GraphDatabase

class GraphRAGNeo4jStorage:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def store_entities_batch(self, entities: List[Dict]) -> List[str]:
        """批量存储实体到Neo4j（使用UNWIND优化）"""
        with self.driver.session() as session:
            result = session.execute_write(self._create_entities_tx, entities)
            return result

    @staticmethod
    def _create_entities_tx(tx, entities):
        # ✅ Verified from Context7 - UNWIND批量插入模式
        query = """
        UNWIND $entities AS entity
        CREATE (e:GraphRAGNode:ExtractedEntity {
            name: entity.name,
            entity_type: entity.type,
            description: entity.description,
            confidence: entity.confidence,
            created_at: datetime(),
            canvas_source: entity.canvas_source
        })
        RETURN id(e) AS node_id
        """
        result = tx.run(query, entities=entities)
        return [record["node_id"] for record in result]
```

**APScheduler定时任务** [Source: Python APScheduler官方文档]

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# 增量索引：每日凌晨2点
scheduler.add_job(
    func=incremental_index_task,
    trigger=CronTrigger(hour=2, minute=0),
    id='incremental_index',
    name='GraphRAG增量索引'
)

# 全量索引：每周日凌晨2点
scheduler.add_job(
    func=full_index_task,
    trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
    id='full_index',
    name='GraphRAG全量索引'
)

scheduler.start()
```

### 文件位置

**新创建的文件：**
```
C:/Users/ROG/托福/
├── src/
│   ├── graphrag/
│   │   ├── __init__.py
│   │   ├── canvas_monitor.py           # CanvasChangeMonitor类
│   │   ├── entity_extractor.py         # GraphRAGEntityExtractor类
│   │   ├── neo4j_storage.py            # GraphRAGNeo4jStorage类
│   │   ├── incremental_scheduler.py    # IncrementalIndexScheduler类
│   │   ├── full_scheduler.py           # FullIndexScheduler类
│   │   └── config.py                   # GraphRAG配置类
│   └── ...
├── tests/
│   ├── test_graphrag_entity_extraction.py
│   ├── test_graphrag_neo4j_storage.py
│   ├── test_graphrag_schedulers.py
│   └── fixtures/
│       └── test-canvas-samples/        # 测试Canvas样本
├── logs/
│   ├── canvas_changes.log              # Canvas变更日志
│   └── graphrag_indexing.log           # 索引日志
├── data/
│   ├── canvas_metadata.db              # Canvas元数据（SQLite）
│   └── graphrag_backups/               # 全量索引备份
└── docs/
    ├── user-guides/
    │   └── graphrag-data-pipeline-setup.md
    └── architecture/
        └── graphrag-data-pipeline-architecture.md
```

### 编码规范

**PEP 8规范** [Source: CLAUDE.md#代码规范]
- 使用4个空格缩进
- 每行最多79字符（文档字符串最多72字符）
- 使用UTF-8编码
- 类名：PascalCase（如 `GraphRAGEntityExtractor`）
- 函数名：snake_case（如 `extract_entities`）
- 常量：UPPER_SNAKE_CASE（如 `ENTITY_EXTRACTION_PROMPT`）

**类型注解（强制）** [Source: CLAUDE.md#零幻觉开发原则]

每个函数必须有完整的类型注解：
```python
from typing import Dict, List, Optional, Tuple

def extract_entities(
    canvas_content: str,
    llm: Ollama
) -> Tuple[List[Dict], List[Dict]]:
    """提取实体和关系

    Args:
        canvas_content: Canvas节点文本内容
        llm: Qwen2.5 LLM实例

    Returns:
        Tuple[entities, relationships]
    """
    pass
```

**文档来源标注（强制）** [Source: CLAUDE.md#零幻觉开发原则]

所有技术API必须标注来源：
```python
# ✅ Verified from Context7 Neo4j Cypher Manual - UNWIND批量插入
query = "UNWIND $entities AS entity CREATE (e:GraphRAGNode) ..."

# ✅ Verified from LangGraph Skill - Ollama集成模式
llm = Ollama(model="qwen2.5:14b-instruct")
```

### Neo4j Schema设计

**命名空间隔离** [Source: docs/architecture/GRAPHRAG-INTEGRATION-DESIGN.md#Neo4j Label Hierarchy]

```cypher
-- Graphiti节点（实时知识图谱）
:GraphitiNode
  ├─ :Concept
  ├─ :Episode
  └─ :Entity

-- GraphRAG节点（批量索引，社区检测）
:GraphRAGNode
  ├─ :ExtractedEntity   -- Canvas提取的实体
  ├─ :Community         -- Leiden算法检测的社区
  └─ :GlobalSummary     -- 社区摘要（用于Global Search）
```

**索引和约束**
```cypher
-- ✅ Verified from Context7 Neo4j Cypher Manual - 索引创建
CREATE INDEX graphrag_entity_name IF NOT EXISTS
FOR (e:ExtractedEntity) ON (e.name);

CREATE INDEX graphrag_entity_type IF NOT EXISTS
FOR (e:ExtractedEntity) ON (e.entity_type);

-- 唯一性约束
CREATE CONSTRAINT graphrag_entity_unique IF NOT EXISTS
FOR (e:ExtractedEntity) REQUIRE (e.name, e.canvas_source) IS UNIQUE;
```

**实体属性Schema**
```cypher
(:ExtractedEntity:GraphRAGNode {
  name: String,              -- 实体名称（必需）
  entity_type: String,       -- Concept | Topic | Skill
  description: String,       -- 简短描述
  confidence: Float,         -- 提取置信度 0-1
  canvas_source: String,     -- 来源Canvas文件路径
  created_at: DateTime,      -- 创建时间
  updated_at: DateTime       -- 更新时间
})
```

**关系Schema**
```cypher
(:ExtractedEntity)-[:RELATED_TO {
  strength: Float,           -- 关系强度 0-1
  created_at: DateTime
}]->(:ExtractedEntity)

(:ExtractedEntity)-[:PREREQUISITE_OF {
  strength: Float,
  created_at: DateTime
}]->(:ExtractedEntity)

(:ExtractedEntity)-[:SIMILAR_TO {
  strength: Float,
  similarity_score: Float,   -- 相似度分数
  created_at: DateTime
}]->(:ExtractedEntity)
```

### 性能要求

**索引延迟目标** [Source: Epic AC]

| 操作类型 | 数据规模 | 目标延迟 |
|---------|---------|---------|
| 增量索引 | 10个Canvas节点变更 | < 5分钟 |
| 全量索引 | 1000个Canvas节点 | < 2小时 |
| Neo4j批量写入 | 1000个实体 | < 10秒 |

**准确率目标** [Source: Epic AC]
- 实体提取准确率: ≥80% (F1 Score)
- 关系提取准确率: ≥75% (F1 Score)
- 人工抽样验证: 100个样本

### 依赖项

**Python依赖** [Source: requirements.txt]
```
# LLM集成
langchain-community>=0.0.20
ollama>=0.1.0

# Neo4j
neo4j>=5.14.0

# 调度器
apscheduler>=3.10.0

# 工具库
tqdm>=4.66.0          # 进度条
pydantic>=2.0.0       # 数据验证
```

**系统依赖**
- **Ollama**: 本地LLM运行环境
  - 安装: `curl -fsSL https://ollama.com/install.sh | sh`
  - 拉取模型: `ollama pull qwen2.5:14b-instruct`
  - 启动: `ollama serve`

- **Neo4j**: 图数据库
  - 版本: ≥5.14.0
  - 配置: `dbms.memory.heap.max_size=4G`（推荐）
  - APOC插件: 如需高级批量操作

### 测试要求

**测试覆盖率目标** [Source: CLAUDE.md#测试规范]
- 单元测试覆盖率: ≥90%
- 集成测试覆盖关键流程: 100%

**测试框架**
```bash
pip install pytest pytest-cov pytest-asyncio
```

**测试运行命令**
```bash
# 运行所有GraphRAG测试
pytest tests/test_graphrag_*.py -v

# 生成覆盖率报告
pytest tests/test_graphrag_*.py --cov=src/graphrag --cov-report=html
```

**关键测试用例**
1. **实体提取测试**
   - 正常Canvas内容提取
   - 空内容处理
   - 超长文本处理（>10000字符）
   - 特殊字符处理（emoji, 数学符号）
   - 提取准确率验证（≥80%）

2. **Neo4j存储测试**
   - 单个实体存储和检索
   - 批量存储性能（1000个实体<10秒）
   - 命名空间隔离验证
   - 并发写入测试
   - 事务回滚测试

3. **调度器测试**
   - 增量索引定时触发
   - 全量索引定时触发
   - 任务失败重试
   - 延迟计算准确性

### 故障排查

**常见问题和解决方法**

**问题1: Qwen2.5提取准确率<80%**
- **原因**: Prompt模板不适合或Few-shot示例不足
- **解决**:
  1. 增加Few-shot示例数量（从3个增加到10个）
  2. 调整temperature参数（降低到0.1）
  3. 使用更大的模型（qwen2.5:32b）
  4. 添加思维链（Chain-of-Thought）提示词

**问题2: Neo4j写入性能慢**
- **原因**: 单条插入而非批量，或未使用UNWIND
- **解决**:
  1. 使用UNWIND批量插入（批大小=100-500）
  2. 使用APOC存储过程（apoc.periodic.iterate）
  3. 增加Neo4j堆内存（dbms.memory.heap.max_size=8G）
  4. 创建必要的索引

**问题3: 增量索引延迟>5分钟**
- **原因**: Canvas变更检测不及时或提取速度慢
- **解决**:
  1. 降低Canvas扫描间隔（从5分钟降到1分钟）
  2. 使用文件系统监听器（watchdog库）替代定时扫描
  3. 并行处理多个Canvas变更（ThreadPoolExecutor）

**问题4: Graphiti和GraphRAG节点混淆**
- **原因**: 标签命名不规范或查询未过滤标签
- **解决**:
  1. 确保所有GraphRAG节点都有`:GraphRAGNode`标签
  2. 查询时明确指定标签：`MATCH (e:GraphRAGNode:ExtractedEntity)`
  3. 创建约束验证标签一致性

### 监控指标

**关键监控指标** [Source: Epic成功指标]

1. **索引健康度**
   - 增量索引成功率: 目标≥95%
   - 全量索引成功率: 目标≥99%
   - 索引延迟: 目标<5分钟

2. **数据质量**
   - 实体提取准确率: 目标≥80%
   - 关系提取准确率: 目标≥75%
   - 重复实体率: 目标<5%

3. **性能指标**
   - Neo4j写入QPS: 目标≥100 entities/s
   - Qwen2.5推理延迟: 目标<3秒/节点
   - 内存使用: 目标<8GB

4. **成本指标**
   - LLM成本: 目标$0（使用本地模型）
   - Neo4j资源使用: 目标<4GB堆内存

### 安全考虑

**Neo4j注入防护**
- 使用参数化查询（$parameters），禁止字符串拼接
- 验证实体名称长度（2-100字符）
- 过滤特殊字符（Cypher保留字）

**LLM输出验证**
- 使用Pydantic Schema验证JSON输出格式
- 限制实体数量（单次提取最多50个实体）
- 过滤低置信度结果（threshold=0.3）

**文件系统安全**
- Canvas路径白名单验证（限制在Canvas文件夹内）
- 防止路径遍历攻击（../绝对路径）

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-14 | 1.0 | 初始Story创建，基于Epic GraphRAG集成和PM审查反馈 | SM Agent (Bob) |

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
