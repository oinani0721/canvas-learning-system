---
story_id: "5.7"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["5.5"]
blocks: ["7.3"]
trace:
  - "FR-MEM-04"
---

# Story 5.7: 3 层记忆检索

Status: ready-for-dev

## Story
As a 系统,
I want 通过 3 层优先级检索找到学习者的历史记忆（知识图谱 → 图数据库 → 缓存）,
So that AI 对话和出题有个人化的上下文，且搜索延迟 < 3 秒。

## Acceptance Criteria

1. **Given** 需要检索学习者历史记忆 **When** 调用 `search_memories` MCP 工具 **Then** 按 3 层优先级顺序检索：Layer 1 Graphiti 知识图谱（语义搜索，最丰富）→ Layer 2 Neo4j 图数据库（结构化查询，次丰富）→ Layer 3 TTLCache 内存缓存（最快，有限数据）

2. **Given** Layer 1 Graphiti 返回结果 **When** 结果数量 >= 请求数量 **Then** 直接返回 Graphiti 结果（不查 Layer 2/3）**And** 结果包含 `source: "graphiti"` 标记

3. **Given** Layer 1 Graphiti 返回结果不足或超时 **When** 降级到 Layer 2 **Then** 用 Neo4j Cypher 查询补充结果 **And** 结果包含 `source: "neo4j"` 标记 **And** 如果 Layer 2 也不足，继续降级到 Layer 3 缓存

4. **Given** Graphiti 服务完全不可用（连接失败/超时 > 3s）**When** 系统检索记忆 **Then** 降级到 Neo4j + 缓存（跳过 Graphiti）**And** 返回 `degraded: true` 标记 **And** 日志记录降级原因 **And** 如果 Neo4j 也不可用，返回默认先验值（NFR-DEG）

5. **Given** 任何层级的检索 **When** 总延迟超过 3 秒 **Then** 立即返回已获得的结果（不等待慢层完成）**And** 结果中标注 `truncated: true` 和 `latency_ms` **And** 慢层结果异步缓存到 Layer 3 供后续使用（NFR-PERF）

6. **Given** 检索成功返回结果 **When** 结果包含学习历史 **Then** 返回结构化数据：`{memories: [{concept, event_type, timestamp, content, source}], total_count, query_latency_ms, degraded, layers_queried}`

7. **Given** 全部 3 层都无数据（新用户或新概念）**When** 系统检索 **Then** 返回空列表 `memories: []` **And** `degraded: false`（非降级，是正常的无数据状态）**And** 下游系统使用默认先验值（BKT P_L0=0.30）

## Tasks / Subtasks

- [ ] Task 1: 实现 3 层检索调度器 (AC: #1, #2, #3)
  - [ ] 创建 `ThreeLayerRetriever` 类（或扩展现有 MemoryService）
  - [ ] Layer 1：调用 Graphiti `search_memory_facts` / `search_nodes`
  - [ ] Layer 2：调用 Neo4j Cypher 查询（learning episodes by node_id）
  - [ ] Layer 3：查询 `TTLCache`（cachetools，30s TTL，已在 memory_service.py 中使用）
  - [ ] 逐层降级逻辑：结果够则短路，不够则继续查下一层
  - [ ] 单元测试：每层独立测试 + 降级路径测试

- [ ] Task 2: 实现 Graphiti 不可用降级 (AC: #4)
  - [ ] Graphiti 连接失败时自动跳过 Layer 1
  - [ ] 超时保护：Graphiti 查询限制 2s（给 Neo4j + 缓存留 1s）
  - [ ] 降级到默认先验值的最终兜底
  - [ ] 单元测试：mock Graphiti ConnectionError → 降级到 Neo4j

- [ ] Task 3: 实现 3s 超时截断 (AC: #5)
  - [ ] 使用 `asyncio.wait_for` 对每层查询设置超时
  - [ ] Layer 1: 2000ms，Layer 2: 800ms，Layer 3: 200ms（总计 3000ms 预算）
  - [ ] 超时时返回已获得的部分结果
  - [ ] 慢层结果异步回填到 Layer 3 缓存
  - [ ] 单元测试：mock 慢查询 → 截断返回

- [ ] Task 4: 实现结果结构化 + source 标记 (AC: #2, #3, #6, #7)
  - [ ] 统一返回格式：`SearchMemoriesOutput` Pydantic model
  - [ ] 每条 memory 标注 source（graphiti/neo4j/cache）
  - [ ] 返回元数据：total_count, query_latency_ms, degraded, layers_queried
  - [ ] 空结果（新用户）返回 `memories: [], degraded: false`
  - [ ] 单元测试：各场景的返回格式验证

- [ ] Task 5: MCP 工具更新 + 集成测试 (AC: #1-#7)
  - [ ] 更新 `search_memories` MCP 工具调用 `ThreeLayerRetriever`
  - [ ] 验证 `backend/app/mcp/server.py` 路由已注册
  - [ ] 集成测试：全 3 层可用场景
  - [ ] 集成测试：Graphiti 不可用降级场景
  - [ ] 性能测试：100 次查询的 p95 延迟 < 3s

## Dev Notes

### Architecture
- 3 层检索架构是 FR-MEM-04 的核心实现，NFR-PERF 要求 < 3s，NFR-DEG 要求 Graphiti 不可用时降级
- Layer 1 Graphiti 是最丰富的（语义搜索 + 知识图谱关系），但延迟最高
- Layer 2 Neo4j 是结构化查询（精确但无语义），中等延迟
- Layer 3 TTLCache 是内存缓存（最快但数据最旧），30s TTL
- 现有 `MemoryService`（memory_service.py）已有 Neo4j 查询和 TTLCache，需要新增 Graphiti 层和调度逻辑
- 超时预算分配：2000ms Graphiti + 800ms Neo4j + 200ms Cache = 3000ms 总预算

### File Paths
- 记忆服务：`backend/app/services/memory_service.py` (MemoryService)
- MCP 工具：`backend/app/mcp/tools/memory_tools.py` (search_memories, line 157-241)
- SearchMemoriesInput/Output：`backend/app/mcp/tools/memory_tools.py` (line 26-58)
- Neo4j 客户端：`backend/app/clients/neo4j_client.py`
- TTLCache：`backend/app/services/memory_service.py` (SCORE_HISTORY_CACHE_TTL, line 64)
- Graphiti entity types：`backend/app/graphiti/entity_types.py`

### Testing
- 单元测试：各层独立检索、降级路径、超时截断、结果格式化
- 集成测试：3 层级联、Graphiti 不可用降级
- 性能测试：p95 延迟 < 3s
- 边界测试：空结果、单层可用、全部不可用

### References
- **From PRD**: FR-MEM-04 3 层检索
- **From PRD**: NFR-PERF 搜索 < 3s
- **From PRD**: NFR-DEG Graphiti 不可用降级
- `backend/app/services/memory_service.py`: 现有 Neo4j 查询 + TTLCache 实现

## UAT Script

> 1. 完成若干考察题产生学习历史数据
> 2. 调用 search_memories 查询某概念的历史记忆
> 3. 确认返回结果包含 memories 数组和 source 标记
> 4. 确认 query_latency_ms < 3000
> 5. 停止 Graphiti 服务
> 6. 再次查询，确认返回 degraded: true 但仍有 Neo4j 层的结果
> 7. 在新概念上查询，确认返回 memories: [] 空列表

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 3 层检索调度 | unit | `pytest tests/unit/test_three_layer_retrieval.py -x` | 0 failures |
| Graphiti 降级 | unit | `pytest tests/unit/test_memory_degradation.py -x` | 0 failures |
| 3s 超时截断 | unit | `pytest tests/unit/test_memory_timeout.py -x` | 0 failures |
| 结果格式化 | unit | `pytest tests/unit/test_memory_output_format.py -x` | 0 failures |
| 3 层集成 | integration | `pytest tests/integration/test_three_layer_memory.py -x` | 0 failures |
| 性能 p95<3s | performance | `pytest tests/performance/test_memory_latency.py -x` | p95 < 3000ms |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
