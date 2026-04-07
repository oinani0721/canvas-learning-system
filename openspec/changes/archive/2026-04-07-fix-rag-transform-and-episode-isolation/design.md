# Design — RAG Transform Completeness + Episode Cache Per-Group Isolation

## D1. Episode 缓存的数据结构选择

### 问题

`memory_service.py:167` 的 `self._episodes: List[Dict[str, Any]] = []` 是单个共享 list，5 个 enforce 点都用 `self._episodes[-MAX_EPISODE_CACHE:]` 实现 FIFO 切片。这造成两个具体问题：
1. **跨 group 互相挤掉**：白板 A 的 1500 episode + 白板 B 的 600 episode → 总 2100 → 白板 A 最早的 100 条被永久丢失
2. **搜索时遍历全部**：line 1622 已经在搜索时按 `group_id` 过滤，但仍要遍历所有 episode（O(n_total)）

### 候选方案

| 方案 | 数据结构 | 内存上界 | 复杂度 | 选择 |
|------|---------|---------|--------|------|
| A | `List[Dict]` (现状) | 2000 | O(n) 搜索 | ❌ 现状 |
| B | `Dict[str, List[Dict]]` | 2000 × n_groups | O(k) 搜索（k = group 内大小） | ⚠️ 需要手动 enforce |
| C | `Dict[str, Deque[Dict, maxlen=2000]]` | 2000 × n_groups | O(k) 搜索 | ✅ 选择 |
| D | `OrderedDict[str, Dict]` 全局 LRU | 2000 | O(1) 但仍是全局 | ❌ 不解决跨 group 挤出 |

### 选 C 的理由

**`collections.deque(maxlen=N)` 自带 FIFO**：append 时自动丢最旧的，无需手动切片，所有 5 个 enforce 点的 `self._episodes = self._episodes[-MAX:]` 直接删除。

**搜索性能**：原全局 list 遍历 N=2000，新 dict 遍历 k = 单个 group 大小（典型值 ≈ 200-500），快 4-10 倍。

**内存上界守卫**：需要新增 `MAX_GROUPS = 100` 限制，防止用户创建 1000 个白板时总内存爆炸。超出 max_groups 时按 LRU 淘汰整个 group（淘汰条件：最近 24h 无活动）。

### 数据结构

```python
from collections import defaultdict, deque
from typing import Deque, Dict, Any

class MemoryService:
    MAX_EPISODE_CACHE = 2000     # per group
    MAX_GROUPS = 100              # 整个 service 的 group 数上限

    def __init__(self, ...):
        self._episodes_by_group: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.MAX_EPISODE_CACHE)
        )
        self._group_last_access: Dict[str, datetime] = {}
        self._episodes_lock = asyncio.Lock()
```

### 接口适配

所有 5 个 enforce 点改为：

```python
async with self._episodes_lock:
    self._episodes_by_group[group_id].append(episode)  # deque 自动 FIFO
    self._group_last_access[group_id] = datetime.now(timezone.utc)
    self._evict_idle_groups_if_needed()
```

`_evict_idle_groups_if_needed` 在 `len(self._episodes_by_group) > MAX_GROUPS` 时按 last_access 升序淘汰 idle group，但保留有最近 24h 活动的所有 group。

## D2. common_mistakes 的数据源选择

### 问题

commit f215830 自己承认 `common_mistakes` 是 placeholder："keep common_mistakes as placeholder (not separable from generic reranked content without additional LLM step)"。

但用户期望验证服务能告诉 LLM "学生在这个概念上经常错在 X"，这是评分的重要上下文。

### 候选数据源

| 数据源 | 真实性 | 实现成本 | 选择 |
|--------|-------|---------|------|
| A. 硬编码占位符 (现状) | ❌ | 0 | 现状 |
| B. RAG 二次 LLM 抽取 | ✅ | 高（每次评分 +1 LLM call） | ⚠️ 延后 |
| C. BKT lapse history (mastery_engine) | ✅ | 低（已有数据） | ✅ 选择 |
| D. verification 历史错答记录 | ✅ | 中（需新 Cypher 查询） | ✅ 选择（与 C 互补） |

### 选 C+D 的理由

**C (BKT lapses)**：`mastery_engine.ConceptState` 已经持有 `fsrs_lapses` (遗忘次数) 和 `interaction_count` (总交互次数)。lapse_rate = `fsrs_lapses / max(interaction_count, 1)`，> 0.3 视为"易错概念"。

**D (verification 错答记录)**：在 Neo4j 查 `(:Episode)-[:SCORED {score < 60}]->(:CanvasNode {title: $concept})` 取最近 5 条对话片段，作为"具体错答"。

### 实现

```python
async def _extract_common_mistakes_from_bkt(self, concept_id: str, canvas_name: str) -> str:
    """从 BKT lapses + 历史低分记录提取错误模式描述。"""
    # 1. BKT lapse 信号
    state = await self._mastery_store.get_state(concept_id)
    lapse_signal = ""
    if state and state.interaction_count > 0:
        lapse_rate = state.fsrs_lapses / state.interaction_count
        if lapse_rate > 0.3:
            lapse_signal = f"该概念历史遗忘率 {lapse_rate:.0%}（{state.fsrs_lapses}/{state.interaction_count}）；"

    # 2. Neo4j 低分历史片段
    low_score_query = """
    MATCH (b:CanvasBoard {name: $canvas_name})
    MATCH (n:CanvasNode {canvasId: b.id})
    WHERE toLower(n.title) CONTAINS toLower($concept)
    MATCH (e:Episode)-[r:SCORED]->(n)
    WHERE r.score < 60
    RETURN e.user_answer AS answer, r.score AS score
    ORDER BY r.created_at DESC LIMIT 3
    """
    rows = await self._neo4j.execute_read(low_score_query, ...)
    fragments = [f"得分 {r['score']}: {r['answer'][:80]}" for r in rows] if rows else []

    if not lapse_signal and not fragments:
        return "无已知错误模式"
    return lapse_signal + "; ".join(fragments) if fragments else lapse_signal
```

### 失败兜底

若 mastery_engine 或 Neo4j 任一不可用，返回 `"无已知错误模式"`（保持现状兼容）+ 结构化日志告警。

## D3. related_concepts 路径退化的守护

### 问题

verification_service.py:1844 的退化逻辑：

```python
name = meta.get("concept") or meta.get("source", "")
```

`metadata.concept` 只有 Graphiti temporal client 写入时才有，其他 RAG 路径（LanceDB、cross-canvas、vault notes）的 metadata.source 通常是文件路径。

### 守护规则

定义"路径模式"（任一匹配即视为路径）：
1. 包含 `/` 或 `\`（路径分隔符）
2. 以 `.md` / `.pdf` / `.txt` / `.html` / `.docx` 结尾
3. 以 `file://` / `http://` / `https://` 开头

### 实现

```python
import re
from pathlib import PurePosixPath, PureWindowsPath

_PATH_LIKE_PATTERNS = re.compile(
    r"(^https?://|^file://|[/\\]|\.(md|pdf|txt|html|docx)$)",
    re.IGNORECASE,
)

def _looks_like_path(value: str) -> bool:
    if not value or not isinstance(value, str):
        return True
    return bool(_PATH_LIKE_PATTERNS.search(value))

def _extract_concept_name(meta: Dict[str, Any]) -> str:
    """优先级：metadata.concept > metadata.title > 过滤后的 metadata.source"""
    concept = meta.get("concept", "")
    if concept and not _looks_like_path(concept):
        return concept

    title = meta.get("title", "")
    if title and not _looks_like_path(title):
        return title

    source = meta.get("source", "")
    if source and not _looks_like_path(source):
        return source

    # 路径退化：从文件名提取（如 /vault/notes/导数.md → 导数）
    if source:
        try:
            stem = PurePosixPath(source).stem or PureWindowsPath(source).stem
            if stem and not _looks_like_path(stem):
                return stem
        except Exception:
            pass

    return ""  # 拒绝退化为路径
```

### 测试场景

| 输入 metadata | 期望输出 |
|---------------|---------|
| `{"concept": "导数"}` | `"导数"` |
| `{"source": "/vault/notes/导数.md"}` | `"导数"`（从 stem 提取） |
| `{"source": "/vault/notes/math.pdf"}` | `"math"`（从 stem 提取） |
| `{"source": "https://example.com/x"}` | `""`（拒绝） |
| `{"title": "链式法则"}` | `"链式法则"` |
| `{}` | `""`（拒绝） |

## D4. 测试 Mock 改造

### 问题

`test_verification_service_activation.py:100-108`：

```python
service.query = AsyncMock(return_value={
    "learning_history": "用户之前学习过相关概念",   # 旧字段，RAG 实际不返回
    "related_excerpts": "...",
    "related_concepts": ["相关概念1"],            # 旧字段
    "common_mistakes": "常见错误模式",            # 旧字段
})
```

这个 mock 直接绕过了 `_get_rag_context_for_concept` 的 transform 逻辑，导致 transform 改坏永远不会被发现。

### 改造方案

新建一个 `mock_rag_service_modern` fixture，使用真实 RAG 返回结构：

```python
@pytest.fixture
def mock_rag_service_modern() -> MagicMock:
    service = MagicMock()
    service.query = AsyncMock(return_value={
        "messages": [],
        "reranked_results": [
            {
                "doc_id": "g1",
                "content": "导数描述了函数在某点的瞬时变化率，是微积分的核心概念之一。",
                "score": 0.92,
                "metadata": {"concept": "导数", "source": "graphiti:temporal"}
            },
            {
                "doc_id": "g2",
                "content": "链式法则用于复合函数求导...",
                "score": 0.85,
                "metadata": {"title": "链式法则", "source": "/vault/notes/calculus.md"}
            },
            {
                "doc_id": "v1",
                "content": "牛顿和莱布尼茨独立发明了微积分。",
                "score": 0.71,
                "metadata": {"source": "/vault/notes/history.md"}
            },
        ],
        "fused_results": [],
        "quality_grade": "high",
        "metadata": {},
    })
    return service
```

### 断言强化

新建 `test_rag_transform_field_completeness.py`：

```python
async def test_learning_history_extracts_real_content(verification_service, mock_rag_service_modern):
    verification_service._rag_service = mock_rag_service_modern
    ctx = await verification_service._get_rag_context_for_concept("导数", "微积分")
    assert ctx["learning_history"] != "无历史记录"
    assert "瞬时变化率" in ctx["learning_history"]

async def test_related_concepts_rejects_path_strings(verification_service, mock_rag_service_modern):
    verification_service._rag_service = mock_rag_service_modern
    ctx = await verification_service._get_rag_context_for_concept("导数", "微积分")
    for c in ctx["related_concepts"]:
        assert "/" not in c, f"路径退化未守护: {c}"
        assert not c.endswith(".md"), f"路径退化未守护: {c}"

async def test_common_mistakes_uses_bkt_lapses(verification_service_with_lapses):
    ctx = await verification_service_with_lapses._get_rag_context_for_concept("导数", "微积分")
    assert ctx["common_mistakes"] != "无已知错误模式"
    assert "%" in ctx["common_mistakes"] or "得分" in ctx["common_mistakes"]
```

## D5. sync/batch memory event 触发的非阻塞策略

### 问题

active change Phase 11 引入 Segment Commit 后，Edge Segment 提交成功的 edge 不触发 `memory_service.record_learning_event(EDGE_CREATED)`，导致 Graphiti 不知道用户建立了新的概念关联。

### 候选方案

| 方案 | 描述 | 风险 |
|------|------|------|
| A. 同步触发，阻塞响应 | 在 Segment 3 commit 后调用 record_learning_event | sync/batch 延迟可能 +100ms |
| B. asyncio.create_task fire-and-forget | 后台异步触发 | 失败无追踪 |
| C. 写入本地 event_outbox 表 | 持久化事件，由独立 worker 消费 | 引入新依赖 |
| D. 复用 SyncOperationResult，附加 should_trigger_memory_event 字段 | 让前端决定是否回调 | 把责任甩给前端 |

### 选 B 的理由

memory event 写入失败不应阻塞 sync 主流程；fire-and-forget 配合结构化日志足以满足"不丢但允许偶尔失败"的语义；archive_scheduler 已经有定期重放机制（即使丢了也可恢复）。

### 实现

```python
# backend/app/api/v1/endpoints/sync.py 修改 Segment 3 commit 后
for op_result in segment3_results:
    if op_result.success and op_result.entity_type == "edge":
        asyncio.create_task(
            _trigger_memory_event_safe(
                memory_service,
                event_type=CanvasEventType.EDGE_CREATED,
                payload={
                    "edge_id": op_result.entity_id,
                    "canvas_name": canvas_name,
                    "source_node_id": op_result.payload.get("source_node_id"),
                    "target_node_id": op_result.payload.get("target_node_id"),
                },
            )
        )

async def _trigger_memory_event_safe(memory_service, event_type, payload):
    try:
        await asyncio.wait_for(
            memory_service.record_learning_event(event_type=event_type, payload=payload),
            timeout=2.0,
        )
    except Exception as exc:
        logger.warning(
            "memory_event_trigger_failed",
            event_type=event_type.value,
            error=str(exc)[:200],
            payload_id=payload.get("edge_id"),
        )
```

### Feature flag

`SYNC_BATCH_TRIGGER_MEMORY_EVENT: bool = True`（默认开）— 出问题可一键关闭。

## D6. Phase 顺序与依赖

```
Phase 1 (Episode per-group)         独立，可立即开始
    │
    ├── Phase 2 (common_mistakes)   依赖 mastery_engine 数据已经稳定
    ├── Phase 3 (related_concepts)  独立
    │
    └── Phase 4 (Test mock 改造)    依赖 Phase 2+3 完成（否则新 mock 跑不过新断言）
        │
        └── Phase 5 (FR-KG-04 文档)  独立，可与 Phase 1 并行
            │
            └── Phase 6 (memory event 触发)  依赖 active change Phase 11 (Segment Commit) 完成
```

**关键依赖**：Phase 6 必须等 active change `fix-fr-kg-04-schema-drift-and-sync-hardening` 的 Phase 11 完成后再开始，否则 Segment 3 还不存在。其他 Phase 可与 active change 并行。

## D7. 回滚边界

每个 Phase 都有独立的 git commit，可以单独 revert。最坏情况下：

- **revert Phase 1**：内存数据结构回到 list，FIFO 行为不变（用户仍然丢数据，但不会引入新 bug）
- **revert Phase 2**：common_mistakes 退回 placeholder，验证服务 LLM 看不到错误模式
- **revert Phase 3**：related_concepts 可能再次退化为路径，LLM 看到 `/vault/notes/x.md`
- **revert Phase 4**：mock 退回旧字段，测试不再覆盖 transform
- **revert Phase 5**：文档退回错误版本（无运行时影响）
- **revert Phase 6**：memory event 不再被触发，Graphiti 不知道新边（但 Neo4j CANVAS_EDGE 仍正常）

## D8. 与 Story 38.2 (MAX_EPISODE_CACHE 引入) 的关系

Story 38.2 在 2026-02-08 提取了 `MAX_EPISODE_CACHE = 2000` 常量，但当时未拆分到 per-group。本 change 不否定 Story 38.2，而是把它的"全局上限"语义改为"per-group 上限"。Story 38.2 的 AC-1/AC-2（episode 持久化恢复）继续有效。
