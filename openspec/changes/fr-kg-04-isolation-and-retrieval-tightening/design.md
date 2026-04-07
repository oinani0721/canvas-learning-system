## Context

FR-KG-04 sync 写入端的 group_id 隔离已经在 `27bbd73` 落地（`MemoryService` 内存 fallback 路径补 group_id 过滤），但**读取端**和**检索退化路径**仍然破口三个：

1. **LearningContextService** 的 Cypher 查询 baseline（已读源码确认）：
   - `_fetch_edge_reasons` (line 202)：`MATCH (n:EntityNode)-[r]-(m:EntityNode) WHERE n.mastery_concept_id = $cid OR n.name = $cid` —— 完全没 group_id
   - `assemble_tier2` (line 262)：相同 Cypher —— 完全没 group_id
   - `_fetch_neighbor_records` (line 412)：`get_node_context` 的主调用路径，签名 `(node_id: str)` —— 完全没 group_id 参数
   - `get_node_context` (line 303) 已经接收 group_id 参数，但只把它传给 `_fetch_mastery`，邻居查询走的是 `_fetch_neighbor_records(node_id)` 完全 bypass 隔离

2. **Context API cache** baseline（已读源码确认）：
   - `_context_cache: dict[str, tuple[float, dict]] = {}` (line 95)
   - `_get_cached(node_id)` / `_set_cache(node_id, response)` —— key 仅 node_id
   - `get_node_context_endpoint` 在 line 207 调 `_get_cached(node_id)`，而 endpoint 自己接收了 `group_id` query param（line 181-184）
   - **结果**：先以 `group_id="physics"` 调一次 → cache 写入；再以 `group_id="math"` 调相同 node_id → cache 命中，返回 physics 的数据。这是**确定性的 read-time data leak**，不是 race condition

3. **cross_canvas_retriever** baseline（已读源码确认）：
   - `find_related_canvases` (line 157-192)：注释里写"占位实现"，函数体只构造空 list 然后返回 `related_canvases[:max_related_canvases]` —— 永远返回空列表
   - `_get_related_canvases_excluding_current` (line 324-337) 直接 return `find_related_canvases` 的结果
   - `search_related_nodes` (line 194-236) 关键路径：`if not related_canvases: results = await self.lancedb.search(query=query, table_name=self.config.canvas_table, num_results=num_results)` —— **不传 `canvas_file` 参数，全库 search**
   - 暴露面：当用户在 Subject A canvas 触发 cross_canvas 检索，由于"关联函数未实现"，会拿到全 vault 的 canvas_nodes 命中（包括 Subject B 的）

4. **vault_notes_retriever** baseline（已读源码确认）：
   - `search(query, num_results)` (line 126) —— 完全没 group_id / subject 参数
   - LanceDB metadata 里有 `metadata_json.subject_id` 但从未用作过滤条件
   - 当前架构假设单 vault 单用户，所以 R7 在当前部署不致命，但任何未来多用户配置都会立即破

5. **LICENSE 缺失**：`ls /Users/Heishing/Desktop/canvas/canvas-learning-system/LICENSE` 文件不存在；README.md 已 import "See LICENSE for terms"

## Goals / Non-Goals

**Goals:**
- 任何 `LearningContextService` 的邻居查询都按 group_id 过滤
- `/context/{node_id}` cache 跨 group_id 严格隔离
- `cross_canvas_retriever` 在 `find_related_canvases` 占位状态下返回空结果而非全库
- `vault_notes_retriever` 拥有 group_id 隔离接口（即使节点函数暂不传，为多 vault 留路径）
- LICENSE 文件落地，README 链接可达

**Non-Goals:**
- 不实现 `find_related_canvases` 真正逻辑（功能蔓延，留给独立 change `fr-kg-04-cross-canvas-relations`）
- 不重构 vault notes 的多 vault 切换 UI（占位接口而非完整功能）
- 不动 `_context_cache` 的 LRU 算法（现有 200 条 + 30s TTL 在 cache key 修复后仍然有效）
- 不引入新的 capability 用于 group_id 隔离的元规则（直接挂 algo-rag 下）

## Decisions

### D1: group_id 透传 vs 全局 ContextVar

**决策**：用显式参数透传，不引入 ContextVar 全局状态。

**Why X over Y**：
- 候选 A: 显式参数 ✅ 选用
- 候选 B: `contextvars.ContextVar('group_id')` 在请求边界设置，learning_context_service 内部隐式读取 ❌ 隐式依赖难以测试，async 边界传递容易丢

**Rationale**：项目里其他写入端（SyncService）都是显式传参。保持一致。

### D2: Cypher 向后兼容策略 — `OR n.group_id IS NULL`

**决策**：所有新加 group_id 过滤的 Cypher 都用 `WHERE (n.group_id = $group_id OR n.group_id IS NULL) AND (m.group_id = $group_id OR m.group_id IS NULL)`。

**Why X over Y**：
- 候选 A: 严格 `n.group_id = $group_id` ❌ 历史无 group_id 数据立即不可见，破坏现有 demo 数据
- 候选 B: `OR IS NULL` 兼容 ✅ 选用 — 历史数据可读，新数据强制 group_id 不为空（在 SyncService 写入端已强制）

**Rationale**：
- SyncService 已强制新写入必有 group_id（commit `1ea43b2`）
- 历史 demo / dev 数据可能仍有 NULL group_id，全部 NULL 隐藏会破坏开发体验
- `IS NULL` 不会泄露 Subject A 数据给 Subject B，因为它只允许"无主"节点被任意 group 看到

### D3: cache key 格式 — `f"{group_id or 'default'}:{node_id}"`

**决策**：cache key = `f"{group_id or 'default'}:{node_id}"`。

**Why X over Y**：
- 候选 A: `f"{group_id}:{node_id}"`（None 也作为字面 'None'）❌ 字符串 'None' 与默认 group 'default' 不一致，下游解析复杂
- 候选 B: `f"{group_id or 'default'}:{node_id}"` ✅ 选用 — None 时回退到 app config 的 DEFAULT_GROUP_ID 等价值
- 候选 C: tuple key `(group_id, node_id)` ❌ dict 支持 tuple 但日志中难以打印

**Rationale**：与 `_fetch_mastery` 中 `if group_id is None: group_id = DEFAULT_GROUP_ID` 的回退语义保持一致。

### D4: cross_canvas_retriever 占位检测策略

**决策**：在 `_get_related_canvases_excluding_current()` 内做检测：
```python
async def _get_related_canvases_excluding_current(self, canvas_file: str) -> List[str]:
    related = await self.find_related_canvases(canvas_file)
    if not related:
        global _warned_unimplemented
        if not _warned_unimplemented:
            logger.warning("cross_canvas disabled: find_related_canvases returns empty (placeholder implementation)")
            _warned_unimplemented = True
    return [c for c in related if c != canvas_file]
```

并在 `search_related_nodes` 删除 `if not related_canvases: 全库 fallback` 分支：
```python
async def search_related_nodes(self, query, related_canvases, num_results=10):
    if not related_canvases:
        return []  # ← 新逻辑：空就空，不全库
    # ... 原有 for canvas in related_canvases 逻辑
```

**Why X over Y**：
- 候选 A: feature flag `CROSS_CANVAS_ENABLED=false` 默认关闭 ❌ 占位状态本身是事实，flag 是代码层加封装的多余抽象
- 候选 B: 空返回 + warning ✅ 选用 — 行为对齐"占位状态"
- 候选 C: 抛 NotImplementedError ❌ 上游调用方可能没有 try/except，破坏正常 RAG 流

**Rationale**：DD-10 防功能蔓延 —— 不在本 change 实现 `find_related_canvases`，但要确保占位状态的 fail-soft。

### D5: vault_notes_retriever 占位接口

**决策**：`search()` 加 `group_id: Optional[str] = None`，None 时跳过过滤：
```python
async def search(self, query: str, num_results: int = 10, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
    # ... 现有 lancedb.search 调用 ...
    if group_id is not None:
        results = [r for r in results if (r.get("metadata", {}).get("metadata_json", {}).get("subject_id") == group_id)]
    return results
```

**Why X over Y**：
- 候选 A: 占位参数但不实现过滤 ❌ 接口骗局
- 候选 B: 实现过滤但默认 None 不破坏现有调用 ✅ 选用 — 真过滤代码 + 向后兼容
- 候选 C: 强制 group_id 必传 ❌ 破坏所有现有调用方

**Rationale**：单 vault 假设下节点函数继续传 None，但单测覆盖 group_id 非 None 路径，确保未来切多 vault 无需再加测试。

### D6: LICENSE 选择 — MIT

**决策**：MIT License，作者 oinani0721，year 2026。

**Why X over Y**：
- MIT vs Apache 2.0 vs GPL：项目 README 已写"See LICENSE"暗示开源；Tauri / FastAPI / Neo4j 都是 MIT/BSD/Apache 兼容栈；最宽松对个人项目友好
- 候选 A: MIT ✅ 选用 — 兼容性最好
- 候选 B: Apache 2.0 ❌ 专利条款对个人项目过度
- 候选 C: GPL-3.0 ❌ 强 copyleft 不适合"未来可能商业化"的桌面应用

## Risks / Trade-offs

| Risk | Likelihood | Mitigation |
|---|---|---|
| `OR group_id IS NULL` 让恶意脚本写入 NULL group_id 节点反复被任意 group 读到 | Low | 写入端已强制 group_id 非空（commit `1ea43b2`），新数据无 NULL；旧 NULL 数据是 demo seed 没有用户敏感信息 |
| cache key 改动后旧 cache 全部 miss，第一次访问 latency 升 | Low | TTL 30s，5 分钟内全量 reseed 完成；用户感知不到 |
| cross_canvas 直接返回空可能影响 agentic_rag.graph 节点函数 | Medium | 已读源码确认 graph 节点函数已经处理空结果 (`if not results: continue`)；本 change tasks Phase 3.5 强制 grep 验证 |
| vault_notes 加 group_id 参数后 retriever 节点函数代码意外传 None 但 retriever 期望非 None | Low | 默认值 `Optional[str] = None`，None 时跳过过滤 |
| LICENSE 文件加完后 README link 仍然失效（路径不对） | Low | tasks Phase 5.3 强制验证链接 |
| 修改 `_fetch_neighbor_records` 签名破坏其他调用方 | Medium | grep 全 backend 确认只有 `get_node_context` 一个调用点；如发现其他调用点，添加默认值参数兼容 |

## Migration Plan

### 部署顺序
1. Phase 1: LearningContextService group_id 闭环
2. Phase 2: Context API cache key 修复
3. Phase 3: cross_canvas_retriever fail-soft
4. Phase 4: vault_notes_retriever 隔离接口
5. Phase 5: LICENSE 落地
6. Phase 6: 验证

### 回滚策略
- Phase 1-4 都是单文件 change，`git revert` 单 commit
- Phase 5 是新建文件，`git rm LICENSE && commit`
- 总回滚时间 < 5 分钟，无数据迁移

### 数据迁移
- 无。`OR IS NULL` 兼容历史数据，cache 自然 reseed。

## Open Questions

1. **`_fetch_edge_reasons` 是否还在被调用？** — Phase 1 实施前 grep 确认。如果是死代码，直接删除而非修改。
2. **`metadata_json.subject_id` 字段在 LanceDB 中是否始终被填充？** — 如果某些历史 vault notes 入库时没填，加过滤后会被全部过滤掉，导致 vault_notes 检索结果归零。Phase 4 实施前必须 sample 一批 vault notes 确认。
3. **`cross_canvas_retriever` 的下游消费者列表完整吗？** — Phase 3 实施前 grep `cross_canvas_retriever` 在整个 backend 的 import 引用，确认所有消费者都能处理空结果。
