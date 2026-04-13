---
doc_type: story
story_id: "5.7"
aliases: ["5.7"]
epic_id: "EPIC-5"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 5.7: 历史记忆 3 层检索

## Story

As a 系统,
I want 通过 3 层检索搜索学习者的历史记忆,
so that 系统可以准确找到相关的历史学习数据。

## Acceptance Criteria

1. **Given** 系统需要查询学习者关于某概念的历史记忆
   **When** 执行 3 层检索
   **Then** 第 1 层：frontmatter 本地数据（最快，< 100ms）
   **And** 第 2 层：LanceDB 向量检索（语义相关，< 500ms）
   **And** 第 3 层：Graphiti 知识图谱检索（关系推理，< 3s，NFR-PERF-7）
   **And** 三层结果融合去重后返回

2. **Given** Graphiti 不可用
   **When** 系统执行 3 层检索
   **Then** 退回到前 2 层（frontmatter + LanceDB），不报错（NFR-DEG-3）
   **And** 响应体中包含 `degraded: true` 标记
   **And** 整体延迟保持在 < 600ms

3. **Given** 历史记忆有时间维度
   **When** 记忆超过 6 个月
   **Then** 自动归档到 Cold 层（AR2 Hot-Warm-Cold 三层时间归档）
   **And** Cold 层记忆仍可检索但排序权重降低
   **And** Hot 层（< 1 个月）和 Warm 层（1-6 个月）保持完整权重

4. **Given** 三层返回不同粒度的结果（frontmatter=结构化数据, LanceDB=向量块, Graphiti=图节点）
   **When** 执行结果融合
   **Then** 按统一的 `MemoryItem` 结构返回（含 source, relevance_score, content, timestamp）
   **And** 同一概念在多层出现时合并为单条（按 note_id 去重）

## Tasks / Subtasks

- [ ] Task 1: MemoryItem 统一数据模型 (AC: #4)
  - [ ] 1.1 在 `backend/app/schemas/memory.py` 定义 `MemorySource` enum：`FRONTMATTER`, `LANCEDB`, `GRAPHITI`
  - [ ] 1.2 定义 `MemoryLayer` enum：`HOT`, `WARM`, `COLD`（按时间）
  - [ ] 1.3 定义 `MemoryItem` Pydantic 模型：`note_id: str, source: MemorySource, layer: MemoryLayer, relevance_score: float, content: str, mastery_score: Optional[float], error_summary: Optional[str], timestamp: datetime`
  - [ ] 1.4 时间到层映射：`< 30 天 = HOT`，`30-180 天 = WARM`，`> 180 天 = COLD`

- [ ] Task 2: 第 1 层 frontmatter 检索 (AC: #1, #4)
  - [ ] 2.1 在 `backend/app/services/memory_retrieval_service.py` 实现 `search_frontmatter_layer(query_note_id: str) -> list[MemoryItem]`
  - [ ] 2.2 直接读取笔记 frontmatter，提取：mastery_score, bkt_params, error_history(最近 3 条), calibration_bias, last_reviewed
  - [ ] 2.3 如果 frontmatter 中有 `error_history`，提取最新错误分类的摘要文本
  - [ ] 2.4 性能要求：< 100ms（本地文件读取，无网络调用）

- [ ] Task 3: 第 2 层 LanceDB 向量检索 (AC: #1, #4)
  - [ ] 3.1 在 `backend/app/services/memory_retrieval_service.py` 实现 `search_lancedb_layer(query: str, top_k: int = 5) -> list[MemoryItem]`
  - [ ] 3.2 使用已有 `backend/app/services/rag_service.py` 中的 LanceDB 客户端（不新建连接）
  - [ ] 3.3 查询向量从 query 字符串生成（调用已有的 embedding 服务）
  - [ ] 3.4 返回结果包含 cosine similarity 作为 relevance_score
  - [ ] 3.5 性能要求：< 500ms

- [ ] Task 4: 第 3 层 Graphiti 知识图谱检索 (AC: #1, #2, #4)
  - [ ] 4.1 在 `backend/app/services/memory_retrieval_service.py` 实现 `search_graphiti_layer(query: str, group_id: str) -> list[MemoryItem]`
  - [ ] 4.2 调用 `graphiti_service.search_memory_facts(query, group_id)` 获取相关 episodes 和 facts
  - [ ] 4.3 Graphiti 不可用时捕获异常，返回空列表 + 设置降级标志（不向上抛出）
  - [ ] 4.4 性能要求：< 3s（NFR-PERF-7），超时后自动截断并返回已有结果

- [ ] Task 5: 三层融合去重 (AC: #1, #3, #4)
  - [ ] 5.1 实现 `merge_memory_layers(layer1: list[MemoryItem], layer2: list[MemoryItem], layer3: list[MemoryItem]) -> list[MemoryItem]`
  - [ ] 5.2 按 note_id 去重：同一 note_id 的多层结果合并，relevance_score 取最高值
  - [ ] 5.3 时间归档权重：`HOT * 1.0, WARM * 0.8, COLD * 0.5`（乘到 relevance_score）
  - [ ] 5.4 最终结果按 relevance_score 降序排列，返回 top_k（默认 10）

- [ ] Task 6: 3 层检索统一接口 (AC: #1, #2)
  - [ ] 6.1 实现 `three_layer_search(query: str, note_id: Optional[str], group_id: str) -> ThreeLayerSearchResult`
  - [ ] 6.2 `ThreeLayerSearchResult` 包含：`items: list[MemoryItem], degraded: bool, layer_latencies: dict[str, float]`
  - [ ] 6.3 三层并发执行（`asyncio.gather`），Graphiti 层设置 3s 超时
  - [ ] 6.4 创建 `GET /api/v1/mastery/memory-search` 端点，query params：`q: str, note_id: Optional[str]`

- [ ] Task 7: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 7.1 `tests/unit/test_memory_layer_search.py`：单独验证每层的检索逻辑
  - [ ] 7.2 `tests/unit/test_memory_fusion.py`：验证去重合并和时间归档权重
  - [ ] 7.3 `tests/unit/test_graphiti_degradation.py`：验证 Graphiti 不可用时降级到 2 层
  - [ ] 7.4 `tests/integration/test_three_layer_search_endpoint.py`：端到端验证搜索 API（含降级场景）

## Dev Notes

- **3 层架构依据**：参考 Retrieval-Augmented Generation (RAG) 多源融合论文（Lewis et al., 2020）+ Graphiti 知识图谱检索（AR2 Hot-Warm-Cold）
- **并发执行**：使用 `asyncio.gather(l1_task, l2_task, l3_task, return_exceptions=True)` 三层同时发起，避免串行等待
- **Graphiti 超时**：3s 是 NFR-PERF-7 定义的上限，超时不报错（降级处理）
- **LanceDB 客户端复用**：`rag_service.py` 中已有 LanceDB 连接池，直接注入依赖，不新建实例
- **Cold 层权重 0.5**：降低但不忽略 Cold 层，6 个月前的深度错误仍有参考价值
- **去重策略**：同 note_id 合并时保留来自多层的 content 摘要（用 `|` 分隔），便于下游使用

### Project Structure Notes

- 检索服务：`backend/app/services/memory_retrieval_service.py`（新建）
- 复用：`backend/app/services/rag_service.py`（LanceDB 客户端）
- 复用：`backend/app/services/graphiti_service.py`（Graphiti 检索）
- Pydantic 模型：`backend/app/schemas/memory.py`（新建）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（新增 /memory-search）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.7] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR26] — 历史记忆检索需求
- [Source: _bmad-output/planning-artifacts/prd.md#AR2] — Hot-Warm-Cold 三层时间归档
- [Source: backend/app/services/rag_service.py] — LanceDB 连接参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证检索到历史学习记录** (AC: #1)
   - 对某个已经考察过多次的概念，开始新的对话
   - 查看 AI 是否在对话中提到了你之前的学习历史（例如"你上次在这个概念上遇到过..."）
   - 如果 AI 完全不了解你的历史，记录 Story 5.7

2. **验证 Graphiti 不可用时系统不崩溃** (AC: #2)
   - 临时关闭 Neo4j（停止 Docker neo4j 服务）
   - 进行一次学习会话和概念检索
   - 系统应该继续工作（可能速度稍慢），不出现红色错误界面
   - 如果出现系统崩溃或无法继续，记录 Story 5.7

3. **验证旧记忆（6 个月以上）仍可检索但权重较低** (AC: #3)
   - 这项测试需要有超过 6 个月的历史数据（或开发者手动调整时间戳测试）
   - 系统应该能检索到旧记忆，但相同查询时新记忆排在旧记忆前面

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.7.1 | pytest | `.venv/bin/pytest tests/unit/test_memory_layer_search.py -x -q` | 0 failed |
| CP-5.7.2 | pytest | `.venv/bin/pytest tests/unit/test_memory_fusion.py -x -q` | 0 failed |
| CP-5.7.3 | pytest | `.venv/bin/pytest tests/unit/test_graphiti_degradation.py -x -q` | 0 failed |
| CP-5.7.4 | pytest | `.venv/bin/pytest tests/integration/test_three_layer_search_endpoint.py -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-5]]
- PRD: [[PRD14]]
