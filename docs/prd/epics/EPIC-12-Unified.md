# Epic 12: 三层记忆系统 + LangGraph Agent编排 + Agentic RAG

**版本**: 1.0 (Unified)
**创建日期**: 2025-11-21
**来源**: PRD Epic 12 + EPIC-12-3LAYER-MEMORY-AGENTIC-RAG.md 合并

---

## 1. Epic概述

### 1.1 目标

统一实现Canvas Learning System的记忆基础设施、Agent执行编排和智能检索系统：
- **记忆层**: 三层记忆系统（Graphiti + LanceDB + Temporal Memory）
- **执行层**: LangGraph多Agent编排系统（工具配备模式）
- **检索层**: Agentic RAG智能检索编排

### 1.2 性能目标

| 指标 | 当前值 | 目标值 | 提升幅度 |
|------|--------|--------|----------|
| 检验白板生成准确率 | 60% | 85% | +25% |
| 检索质量 (MRR@10) | 0.280 | 0.380 | +36% |
| 薄弱点聚类F1 | 0.55 | 0.77 | +40% |
| P95检索延迟 | - | <400ms | - |

### 1.3 成本目标

- 年度运营成本 ≤ $60 (目标$49)
- Cohere API ≤ $20/年 (仅检验白板使用)
- LLM成本 (Query rewrite) ≤ $5/年

### 1.4 行为规范 (Gherkin BDD)

**文件**: `specs/behavior/three-layer-memory-agentic-rag.feature`

| Story | 关联场景 | 场景编号 |
|-------|----------|----------|
| 12.2 | 单Canvas检索使用group_ids隔离 | #13 |
| 12.3 | 大规模图谱性能保护机制 | #15 |
| 12.5 | 评分/解释/拆解触发记忆写入 | #7, #8, #9 |
| 12.8 | 记忆写入工具实现 | #7, #8, #9 |
| 12.13 | Agentic RAG路由决策 | #2, #3 |
| 12.14 | 三层记忆并行检索 | #1, #3, #4 |
| 12.15 | 融合算法 (RRF/Weighted/Cascade) | #1, #2, #3 |
| 12.16 | 混合Reranking策略 | #1, #6 |
| 12.17 | 质量控制循环 | #4 |
| 12.18 | Canvas集成和检验白板增强 | #1, #10, #11 |
| 12.19 | 检验历史记录存储 | #11, #12 |
| 12.20 | 针对性复习算法 | #10, #11 |
| 12.22 | 跨Canvas题目关联 | #12, #14, #18 |

**运行测试**: `pytest specs/behavior/three-layer-memory-agentic-rag.feature`

---

## 2. 技术架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Agentic RAG编排层                         │
│            (LangGraph StateGraph + Send模式)                 │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
    ┌───────────▼───────────┐ ┌───────────▼───────────┐
    │   并行检索 (Send)      │ │   融合 + Reranking     │
    │ • Graphiti           │ │ • RRF/Weighted/Cascade │
    │ • LanceDB            │ │ • Local/Cohere Rerank  │
    │ • Temporal Memory    │ │ • Quality Control Loop │
    └───────────┬───────────┘ └───────────┬───────────┘
                │                         │
┌───────────────▼─────────────────────────▼───────────────────┐
│                    三层记忆系统                               │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Layer 1:        │ Layer 2:        │ Layer 3:                │
│ Graphiti        │ LanceDB         │ Temporal Memory         │
│ (知识图谱)       │ (多模态向量)     │ (FSRS + 学习行为)        │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

## 3. Story Map (23个Story)

### Phase 1: 记忆层 (Story 12.1-12.6)

#### Story 12.1: LanceDB向量数据库集成
**优先级**: P0 | **工期**: 1天

**目标**: 替换ChromaDB，建立多模态向量存储基础

**验收标准**:
- ✅ LanceDB成功安装和配置
- ✅ 创建canvas_explanations表 (doc_id, content, type, concept, canvas_file, vector)
- ✅ 支持10K+文档检索，延迟<50ms
- ✅ 支持text-embedding-3-small嵌入

**代码示例**:
```python
import lancedb

db = lancedb.connect("~/.canvas_learning/lancedb")
table = db.create_table(
    "canvas_explanations",
    schema={
        "doc_id": "string",
        "content": "string",
        "type": "string",  # "oral-explanation", "clarification-path", etc.
        "concept": "string",
        "canvas_file": "string",
        "created_at": "timestamp",
        "vector": "vector[1536]"
    },
    mode="overwrite"
)
```

---

#### Story 12.2: Graphiti知识图谱增强
**优先级**: P0 | **工期**: 2天

**目标**: 增强现有Graphiti集成，支持hybrid search

**验收标准**:
- ✅ Neo4j 5.0+正确部署（Docker Compose）
- ✅ `add_episode()` 正确提取概念和关系
- ✅ `hybrid_search()` 返回Graph + Semantic + BM25融合结果
- ✅ 支持group_ids过滤

**代码示例**:
```python
results = await graphiti_client.hybrid_search(
    query="逆否命题的应用场景",
    num_results=10,
    group_ids=["canvas-discrete-math"]
)
```

---

#### Story 12.3: Neo4j索引优化
**优先级**: P1 | **工期**: 0.5天

**目标**: 优化Neo4j查询性能

**验收标准**:
- ✅ 创建Concept.name索引
- ✅ 创建Episode.created_at索引
- ✅ 10K概念 + 50K关系场景下延迟<100ms

---

#### Story 12.4: LanceDB数据迁移工具
**优先级**: P0 | **工期**: 1.5天

**目标**: 从ChromaDB迁移现有向量数据

**验收标准**:
- ✅ 导出ChromaDB所有documents和embeddings
- ✅ 转换格式并导入LanceDB
- ✅ 数据一致性校验（100%记录对齐）
- ✅ 双写模式支持（迁移期间同时写入两个DB）
- ✅ Rollback计划（保留ChromaDB 1周）

---

#### Story 12.5: 记忆系统触发时机定义
**优先级**: P0 | **工期**: 1天

**目标**: 定义各Canvas操作的记忆存储调度规则

**记忆系统调度时机矩阵**:

| Canvas操作 | Graphiti | Temporal | Semantic | LangGraph Checkpointer |
|-----------|----------|----------|----------|----------------------|
| 问题拆解 | ✅ | ✅ | ❌ | ✅ (自动) |
| 评分 | ✅ | ✅ | ❌ | ✅ (自动) |
| 生成解释文档 | ✅ | ✅ | ✅ | ✅ (自动) |
| 生成检验白板 | ✅ (查询+存储) | ✅ | ❌ | ✅ (自动) |
| 检验历史记录存储 | ✅ (查询+存储) | ❌ | ❌ | ✅ (自动) |
| 艾宾浩斯复习触发 | ✅ (查询) | ✅ (查询) | ✅ (查询) | ❌ |

**验收标准**:
- ✅ 所有操作类型的记忆调度规则文档化
- ✅ 精确时序定义（先Canvas后记忆）
- ✅ 错误处理策略定义（非关键路径不阻塞）

**行为规范**: `three-layer-memory-agentic-rag.feature` 场景 #7, #8, #9

---

#### Story 12.6: 跨Canvas多模态文件关联
**优先级**: P1 | **工期**: 1天

**目标**: 支持关联PDF、含图片的md文件到Canvas节点

**验收标准**:
- ✅ Canvas节点可关联外部PDF文件
- ✅ Canvas节点可关联含图片的md文件
- ✅ Graphiti存储跨Canvas关联关系
- ✅ LanceDB存储多模态向量（Phase 5 ImageBind预留接口）

**注**: 此Story来源于SCP-006提案

---

### Phase 2: 执行层 (Story 12.7-12.12)

#### Story 12.7: LangGraph StateGraph定义
**优先级**: P0 | **工期**: 2天

**目标**: 定义Canvas Learning System的LangGraph状态图

**验收标准**:
- ✅ 定义CanvasLearningState（含write_history字段）
- ✅ 实现WriteHistory类
- ✅ checkpointer配置（PostgresSaver生产/InMemorySaver开发）
- ✅ thread_id生成策略：`canvas_{canvas_name}_{session_id}`
- ✅ State可正确传递
- ✅ 可通过thread_id恢复对话上下文

**代码示例**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://user:pass@localhost:5432/canvas_learning"
checkpointer = PostgresSaver.from_conn_string(DB_URI)
graph = builder.compile(checkpointer=checkpointer)
```

**Canvas备份规范** (SCP-003):
- ✅ 备份文件夹`.canvas_backups/`在Vault根目录
- ✅ 命名：`{canvas_name}_{checkpoint_id}.canvas`
- ✅ 清理：超过50个自动删除最旧的
- ✅ 性能：备份创建+清理 <100ms

---

#### Story 12.8: 共享Tools实现
**优先级**: P0 | **工期**: 2天

**目标**: 实现所有Agent共享的Canvas操作工具

**Tools列表**:
- ✅ write_to_canvas (带FileLock和快照)
- ✅ create_md_file_for_canvas (支持Vault相对路径)
- ✅ add_edge_to_canvas
- ✅ update_ebbinghaus
- ✅ query_graphiti_context
- ✅ store_to_graphiti_memory
- ✅ store_to_temporal_memory
- ✅ store_to_semantic_memory
- ✅ query_graphiti_for_verification

**验收标准**:
- ✅ 所有工具可并发调用
- ✅ 数据一致性100%
- ✅ 跨平台FileLock测试通过

---

#### Story 12.9: 12个工具配备Agent节点创建
**优先级**: P0 | **工期**: 1.5天

**目标**: 使用create_react_agent创建12个学习Agent

**验收标准**:
- ✅ 每个Agent配备shared_tools
- ✅ 配置state_modifier
- ✅ 每个Agent能独立调用工具
- ✅ 首个节点<1秒出现

---

#### Story 12.10: LangGraph Supervisor路由逻辑
**优先级**: P0 | **工期**: 1.5天

**目标**: 实现Supervisor模式的Agent路由

**验收标准**:
- ✅ supervisor_router函数实现
- ✅ 支持单Agent和并行Agent调度
- ✅ 条件路由（根据operation类型）
- ✅ 路由准确率100%
- ✅ 多轮对话上下文正确恢复

**代码示例**:
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

---

#### Story 12.11: 回滚机制和错误恢复
**优先级**: P1 | **工期**: 1天

**目标**: 实现基于Checkpointer的回滚能力

**验收标准**:
- ✅ rollback_to_timestamp实现
- ✅ rollback_n_steps实现
- ✅ FastAPI /api/canvas/rollback端点
- ✅ Obsidian Plugin回滚UI
- ✅ 回滚准确率100%，<2秒完成

---

#### Story 12.12: LangSmith可观测性集成
**优先级**: P1 | **工期**: 1天

**目标**: 实现完整的执行追踪和监控

**验收标准**:
- ✅ LangSmith trace覆盖100%检索请求
- ✅ 每次API调用记录cost
- ✅ P50/P95/P99延迟实时展示
- ✅ 错误监控：检索失败率<1%

---

### Phase 3: 检索层 (Story 12.13-12.18)

#### Story 12.13: Agentic RAG StateGraph定义
**优先级**: P0 | **工期**: 1.5天

**目标**: 定义Agentic RAG的LangGraph状态图

**代码示例**:
```python
class CanvasRAGState(MessagesState):
    # Retrieval results from 3 layers
    graphiti_results: List[Dict[str, Any]] = field(default_factory=list)
    lancedb_results: List[Dict[str, Any]] = field(default_factory=list)
    temporal_weak_concepts: List[str] = field(default_factory=list)

    # Fusion and reranking
    fused_results: List[Dict[str, Any]] = field(default_factory=list)
    reranked_results: List[Dict[str, Any]] = field(default_factory=list)

    # Quality control
    quality_grade: Optional[Literal["high", "medium", "low"]] = None
    rewrite_count: int = 0
```

**验收标准**:
- ✅ CanvasRAGState定义完整
- ✅ CanvasRAGConfig支持fusion_strategy和reranking_strategy
- ✅ 与执行层StateGraph正确集成

---

#### Story 12.14: 并行检索节点 (Send模式)
**优先级**: P0 | **工期**: 1.5天

**目标**: 使用LangGraph Send模式实现3层并行检索

**代码示例**:
```python
from langgraph.graph import Send

async def fan_out_retrieval(state: CanvasRAGState, runtime: Runtime) -> list[Send]:
    return [
        Send("retrieve_graphiti", {"query": query, "limit": batch_size}),
        Send("retrieve_lancedb", {"query": query, "limit": batch_size}),
        Send("retrieve_temporal_weak_concepts", {"canvas_file": canvas_file})
    ]
```

**验收标准**:
- ✅ 3层检索并行执行
- ✅ 总延迟<150ms（不含网络）
- ✅ Retry policy配置（3次重试）

**行为规范**: `three-layer-memory-agentic-rag.feature` 场景 #1, #3, #4, #5, #6

---

#### Story 12.15: 融合算法实现
**优先级**: P0 | **工期**: 2天

**目标**: 实现3种融合算法

**融合策略**:
1. **RRF** (Reciprocal Rank Fusion): 默认，k=60
2. **Weighted**: 检验白板生成（薄弱点权重70%）
3. **Cascade**: 成本优化模式（Tier 1不足才调用Tier 2）

**验收标准**:
- ✅ RRF正确融合Graphiti + LanceDB结果
- ✅ Weighted: alpha=0.7检验白板场景
- ✅ Cascade: 成本节省≥50%
- ✅ 可通过config动态选择策略

---

#### Story 12.16: 混合Reranking策略
**优先级**: P0 | **工期**: 2天

**目标**: 实现Local + API的混合Reranking

**策略**:
- **local**: BAAI/bge-reranker-base（中文优化）
- **cohere**: Cohere rerank-multilingual-v3.0
- **hybrid_auto**: 自动选择（检验白板用Cohere，其他用Local）

**验收标准**:
- ✅ Local Reranker正确rerank中文文档
- ✅ Cohere API调用成功率≥99%
- ✅ hybrid_auto正确选择策略
- ✅ 检验白板自动启用Cohere

---

#### Story 12.17: 质量控制循环
**优先级**: P1 | **工期**: 1.5天

**目标**: 实现检索质量评估和Query重写

**质量分级**:
- **high**: Top-3平均分 ≥ 0.7
- **medium**: 0.5-0.7
- **low**: < 0.5

**验收标准**:
- ✅ Quality checker正确分级
- ✅ Query rewriter在low质量时触发
- ✅ 最多2次迭代
- ✅ Rewrite后质量提升avg +0.15

---

#### Story 12.18: Canvas集成和检验白板增强
**优先级**: P0 | **工期**: 1天

**目标**: 将Agentic RAG集成到检验白板生成流程

**验收标准**:
- ✅ 检验白板生成调用新Agentic RAG
- ✅ graphiti-memory-agent正确记录到Graphiti
- ✅ Temporal Memory正确更新FSRS卡片
- ✅ 向后兼容：Epic 1-10功能不受影响

**行为规范**: `three-layer-memory-agentic-rag.feature` 场景 #1, #10, #11

---

### Phase 4: 复习关联层 (Story 12.19-12.23)

#### Story 12.19: 检验历史记录存储
**优先级**: P1 | **工期**: 1天

**目标**: 存储检验白板生成历史和结果

**验收标准**:
- ✅ store_review_canvas_relationship实现
- ✅ 创建(review)-[:GENERATED_FROM]->(original)关系
- ✅ 存储mode和results元数据

---

#### Story 12.20: 针对性复习算法
**优先级**: P1 | **工期**: 1天

**目标**: 基于历史薄弱点计算针对性复习权重

**验收标准**:
- ✅ query_review_history_from_graphiti实现
- ✅ calculate_targeted_review_weights实现
- ✅ 70%薄弱点 + 30%已掌握概念权重

---

#### Story 12.21: 复习模式选择UI
**优先级**: P2 | **工期**: 0.5天

**目标**: Obsidian Plugin复习模式选择界面

**验收标准**:
- ✅ 支持选择"全面复习"或"针对性复习"
- ✅ 显示历史薄弱概念列表
- ✅ 用户可手动调整权重

---

#### Story 12.22: 题目关联查询
**优先级**: P2 | **工期**: 0.5天

**目标**: 支持跨Canvas题目关联查询

**验收标准**:
- ✅ 基于Graphiti查询相关题目
- ✅ 支持按概念、难度、时间过滤
- ✅ 返回结果包含Canvas路径和节点ID

**行为规范**: `three-layer-memory-agentic-rag.feature` 场景 #12, #14, #18

---

#### Story 12.23: 端到端集成测试
**优先级**: P0 | **工期**: 1.5天

**目标**: 完整系统集成测试

**测试场景**:
1. 检验白板生成E2E（含Agentic RAG）
2. 艾宾浩斯复习调度E2E（触发点4）
3. 多轮对话上下文恢复
4. 记忆系统一致性

**验收标准**:
- ✅ 所有E2E场景通过
- ✅ MRR@10 ≥ 0.380
- ✅ Recall@10 ≥ 0.68
- ✅ 薄弱点聚类F1 ≥ 0.77
- ✅ 检验白板生成准确率 ≥ 85%
- ✅ 单元测试覆盖率 ≥ 80%
- ✅ Epic 1-10回归测试通过

---

## 4. 依赖关系

### 4.1 外部依赖

| 依赖 | 版本 | 用途 | 风险缓解 |
|------|------|------|----------|
| Neo4j | 5.0+ | Graphiti backend | Docker Compose部署 |
| Cohere API | - | 检验白板Reranking | 超限降级到Local |
| OpenAI API | - | Embedding + Query rewrite | 使用最便宜模型 |
| LangGraph | 0.2.55 | Agent编排 | 锁定版本 |

### 4.2 Epic依赖

- **Epic 4**: 检验白板生成（本Epic提供新检索能力）
- **Epic 10**: graphiti-memory-agent定义
- **Epic 1-3**: canvas_utils.py基础操作

### 4.3 被依赖

- **Epic 14**: 艾宾浩斯复习系统依赖本Epic的Temporal Memory

---

## 5. 风险和缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| LanceDB迁移数据丢失 | 中 | 高 | 双写模式 + 完整备份 + Rollback计划 |
| Neo4j性能瓶颈 | 低 | 中 | 预先性能测试 + 索引优化 |
| Cohere API限流 | 低 | 低 | 自动降级到Local Reranker |
| Query重写死循环 | 极低 | 中 | 硬编码max=2 + 超时保护 |
| LangGraph版本兼容 | 低 | 中 | 锁定版本 + 预留buffer |

---

## 6. 时间规划

**总工期**: 约20人天

- **Phase 1 (记忆层)**: 7天
- **Phase 2 (执行层)**: 9天
- **Phase 3 (检索层)**: 9.5天
- **Phase 4 (复习关联层)**: 4.5天

**注**: Phase 1-2可部分并行，Phase 3依赖Phase 1，Phase 4依赖Phase 2-3

---

## 7. ADR引用

- **ADR-001**: 本地模型优先策略
- **ADR-002**: LanceDB向量数据库选型
- **ADR-003**: Agentic RAG架构
- **ADR-004**: GraphRAG评估（不引入）

---

## 8. 技术验证要求

⚠️ 本Epic所有Stories必须遵守Section 1.X技术验证协议

**强制文档来源**:
- Local Skill: `@langgraph` (952页完整文档)
- Local Skill: `@graphiti` (完整框架文档)

**验证检查点**:
- SM Agent必须激活Skills并记录查询结果
- Dev Agent必须在代码中添加Skill引用注释
- Code Review必须验证StateGraph和节点创建的正确性

---

**文档结束**

**下一步**: 基于此Epic创建详细Story文件 (docs/stories/12.x.story.md)
