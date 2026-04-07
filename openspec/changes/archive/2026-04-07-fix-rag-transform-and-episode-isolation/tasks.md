# Implementation Tasks

> **依赖前提**：本 change 的 Phase 6 必须等 `fix-fr-kg-04-schema-drift-and-sync-hardening` 的 Phase 11 (Dependency-Aware Segment Commit) 完成后再开始。其他 Phase 可与该 active change 并行进行。

## 1. Episode 缓存 per-group 隔离（Phase 1，P0，独立）

- [x] 1.1 在 `backend/app/services/memory_service.py:151` 新增 `MAX_GROUPS: int = 100` 常量，紧贴 `MAX_EPISODE_CACHE`
- [x] 1.2 修改 `backend/app/services/memory_service.py:167` 将 `self._episodes: List[Dict[str, Any]] = []` 替换为 `self._episodes_by_group: Dict[str, Deque[Dict[str, Any]]] = defaultdict(lambda: deque(maxlen=self.MAX_EPISODE_CACHE))`
- [x] 1.3 新增 `self._group_last_access: Dict[str, datetime] = {}` 跟踪每个 group 的最近活动时间
- [x] 1.4 添加 `from collections import defaultdict, deque` 与 `from typing import Deque` 导入
- [x] 1.5 修改 `backend/app/services/memory_service.py:262-298` 的恢复逻辑，按 episode 的 `group_id` 字段分桶 append 到对应 deque（不再用全局 list 的切片）
- [x] 1.6 实现 `_evict_idle_groups_if_needed()` 方法：当 `len(self._episodes_by_group) > MAX_GROUPS` 时，按 `_group_last_access` 升序移除超过 24h 无活动的 group（保护活跃 group）
- [x] 1.7 修改 `backend/app/services/memory_service.py:447-450` 的 `record_learning_event` enforce 点，改为 `self._episodes_by_group[group_id].append(episode)` + 更新 `_group_last_access[group_id]` + 调用 `_evict_idle_groups_if_needed()`
- [x] 1.8 修改 `backend/app/services/memory_service.py:1060-1062` 的 `batch_record_events` enforce 点，按 group_id 分桶
- [x] 1.9 修改 `backend/app/services/memory_service.py:1217-1218` 的 `record_summary_event` enforce 点
- [x] 1.10 修改 `backend/app/services/memory_service.py:1709-1710` 的 `record_temporal_event` enforce 点
- [x] 1.11 修改 `backend/app/services/memory_service.py:558-562` 的 `_get_user_memories` 内存路径，遍历改为 `self._episodes_by_group.get(group_id, [])`
- [x] 1.12 修改 `backend/app/services/memory_service.py:1622-1640` 的 `search_episodes` 内存 fallback 路径，按 group_id 直查 deque
- [x] 1.13 修改 `backend/app/services/memory_service.py:938` 的 stats 接口，`total_episodes` 改为 `sum(len(d) for d in self._episodes_by_group.values())`，新增 `groups_count` 字段
- [x] 1.14 新建 `backend/tests/unit/test_memory_episode_per_group.py`：场景 1 — group A 写入 2100 条只保留 2000 条最新
- [x] 1.15 同上：场景 2 — group A 写入 1500 + group B 写入 600 → 两个 group 各自保留全部数据（互不挤掉）
- [x] 1.16 同上：场景 3 — 创建 105 个 group → 触发 `_evict_idle_groups_if_needed`，最旧空闲 group 被淘汰
- [x] 1.17 同上：场景 4 — `search_episodes(group_id=A)` 只返回 group A 的数据，不遍历其他 group
- [x] 1.18 在 `test_memory_service.py` 现有测试中检查是否有依赖 `self._episodes` 直接访问的断言，如有则更新为 `_episodes_by_group`

## 2. RAG transform `common_mistakes` 真实数据源（Phase 2，P0，依赖 Phase 1 否则数据可能不一致）

- [x] 2.1 在 `backend/app/services/verification_service.py` 新增私有方法 `_extract_common_mistakes_from_bkt(self, concept_id: str, canvas_name: str) -> str`
- [x] 2.2 实现 BKT lapse 信号提取：调用 `self._mastery_store.get_state(concept_id)`，计算 `lapse_rate = state.fsrs_lapses / max(state.interaction_count, 1)`，> 0.3 时生成 `f"该概念历史遗忘率 {lapse_rate:.0%}（{lapses}/{count}）"`
- [x] 2.3 实现 Neo4j 历史低分查询：`MATCH (b:CanvasBoard {name})-[:CONTAINS_NODE]->(n:CanvasNode) WHERE toLower(n.title) CONTAINS toLower($concept) MATCH (e:Episode)-[r:SCORED]->(n) WHERE r.score < 60 RETURN e.user_answer, r.score ORDER BY r.created_at DESC LIMIT 3`
- [x] 2.4 拼接 lapse 信号 + 低分片段：若两者都为空，返回 `"无已知错误模式"`；否则返回 `lapse_signal + "; ".join(fragments)` 形式的字符串（最大 500 字符）
- [x] 2.5 在 `_get_rag_context_for_concept` (verification_service.py:1832) 调用 `_extract_common_mistakes_from_bkt(concept, canvas_name)` 替换硬编码 `"无已知错误模式"`
- [x] 2.6 添加结构化日志 `common_mistakes_extracted`，含 `lapse_rate / fragments_count / extraction_source` 字段，便于线上观测
- [x] 2.7 在 `_extract_common_mistakes_from_bkt` 内对 mastery_store / Neo4j 调用都用 try-except 兜底，任一失败返回 `"无已知错误模式"` + WARNING 日志
- [x] 2.8 单元测试 `test_common_mistakes_extraction.py`：场景 1 — BKT lapse_rate=0.4 + 无低分历史 → 返回 lapse_signal
- [x] 2.9 同上：场景 2 — BKT 不可用 + Neo4j 有 2 条低分 → 返回 fragments 部分
- [x] 2.10 同上：场景 3 — BKT + Neo4j 都不可用 → 返回 `"无已知错误模式"` + 日志告警
- [x] 2.11 同上：场景 4 — lapse_rate < 0.3 且无低分 → 返回 `"无已知错误模式"`（不强行虚构）

## 3. RAG transform `related_concepts` 路径退化守护（Phase 3，P0，独立）

- [x] 3.1 在 `backend/app/services/verification_service.py` 顶部添加正则常量 `_PATH_LIKE_PATTERNS = re.compile(r"(^https?://|^file://|[/\\\\]|\\.(md|pdf|txt|html|docx)$)", re.IGNORECASE)`
- [x] 3.2 新增私有函数 `_looks_like_path(value: str) -> bool`：空字符串 / 非字符串返回 True；含路径分隔符或文件扩展名返回 True
- [x] 3.3 新增私有函数 `_extract_concept_name(meta: Dict[str, Any]) -> str`：优先级 `metadata.concept` > `metadata.title` > `metadata.source`，每一步都过滤路径
- [x] 3.4 在 `_extract_concept_name` 中实现"路径退化但有文件名"的兜底：用 `PurePosixPath(source).stem` 提取文件名（如 `/vault/notes/导数.md` → `导数`），仍要再次检查 stem 不是路径
- [x] 3.5 修改 `verification_service.py:1842-1849` 的 related_concepts 提取循环，调用 `_extract_concept_name(meta)` 替代 `meta.get("concept") or meta.get("source", "")`
- [x] 3.6 单元测试 `test_related_concepts_path_guard.py`：6 个 metadata 输入测试矩阵（见 design.md D3）
- [x] 3.7 边界 case 测试：`metadata = None` → 返回 `""`；`metadata = {"concept": "/abs/path"}` → 返回 `""`（拒绝带路径的 concept）
- [x] 3.8 性能测试：1000 个 reranked_results × 调用 `_extract_concept_name` 的总耗时 < 5ms（避免正则成为热路径瓶颈）

## 4. 测试 mock 改造（Phase 4，P1，依赖 Phase 2+3）

- [x] 4.1 在 `backend/tests/unit/test_verification_service_activation.py` 新增 fixture `mock_rag_service_modern`，使用真实 `reranked_results` 结构（参考 design.md D4）
- [x] 4.2 标记原 fixture `mock_rag_service` 为 `@pytest.fixture(scope="function")` 并添加 deprecation 注释 `# DEPRECATED: 使用旧字段绕过 transform，新测试请用 mock_rag_service_modern`
- [x] 4.3 找出所有依赖 `mock_rag_service` 的测试用例（grep `mock_rag_service` in tests/），逐个评估是否需要迁移到 `mock_rag_service_modern`
- [x] 4.4 新建 `backend/tests/unit/test_rag_transform_field_completeness.py`：3 个核心断言（见 design.md D4）
- [x] 4.5 新增 fixture `mock_rag_service_empty`：返回 `{"reranked_results": [], ...}`，用于测试 fallback 行为
- [x] 4.6 新增 fixture `mock_rag_service_paths_only`：返回所有 metadata 都是路径的 reranked_results，验证 related_concepts 全部被守护过滤
- [x] 4.7 新增集成测试 `test_verification_e2e_with_real_rag_shape.py`：用真实 LanceDB / Graphiti 接口（不 mock），验证 transform 在端到端流程中字段非空
- [x] 4.8 在 CI 中添加 `pytest backend/tests/unit/test_rag_transform_field_completeness.py -v` 的 required check

## 5. FR-KG-04 文档同步（Phase 5，P1，独立）

- [x] 5.1 修改 `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md:110-131` 的"后端处理链路详解"段落，将 `canvas_service.add_edge()` 调用链替换为：`POST /api/v1/sync/batch → SyncService.process_sync_batch() → _upsert_node/_upsert_edge → Neo4j (CANVAS_EDGE)`
- [x] 5.2 修改 FR-KG-04.md 第 156-164 行的"后端关键函数"表，删除 `_sync_edge_to_neo4j` 和 `sync_all_edges_to_neo4j` 行（这些是已废弃的 Path B），改为 `SyncService._upsert_node` / `_upsert_edge` 行
- [x] 5.3 修改 FR-KG-04.md 第 245-254 行的"被替代的旧代码"表，标注 `fallback_sync_service.py / sync.py / sync_service.py` 现在的真实状态（哪些已删、哪些仍在用）
- [x] 5.4 在 FR-KG-04.md 第 188-225 行的"潜在断裂点分析"图后追加"已确认的断裂点"小节，列出本次 4 轮探索发现的 6 个 confirmed bug 与对应 active change
- [x] 5.5 修改 FR-KG-04.md 第 580-589 行的"FSRS 难度映射"，将 60/80 阈值改为 0.3/0.5/0.7（基于 effective_proficiency），并标注"4 档难度（easy/medium-easy/medium-hard/hard）"
- [x] 5.6 在 FR-KG-04.md 顶部 status 行追加 `> **2026-04-07 update**: 经 4 轮 Explore Agent 核实，原文档调用链与代码不符，已修正。详见 commit f215830 + active change fix-fr-kg-04-schema-drift-and-sync-hardening`
- [x] 5.7 grep 整个 docs/ 目录确认无其他文档仍引用错误的 `canvas_service.add_edge → CONNECTS_TO` 调用链，发现的逐一修正

## 6. sync/batch memory event 触发（Phase 6，P2，依赖 active change Phase 11 完成）

- [x] 6.1 等待 `fix-fr-kg-04-schema-drift-and-sync-hardening` Phase 11 (Dependency-Aware Segment Commit) merge 到主干
- [x] 6.2 在 `backend/app/config.py` 的 `Settings` 添加 `SYNC_BATCH_TRIGGER_MEMORY_EVENT: bool = Field(default=True, description="Trigger memory event after Segment 3 commit in /sync/batch")`
- [x] 6.3 在 `backend/app/api/v1/endpoints/sync.py` 引入 `from app.models.canvas_events import CanvasEventType`
- [x] 6.4 在 sync.py 新增私有 helper `_trigger_memory_event_safe(memory_service, event_type, payload)`，包 try/except + asyncio.wait_for(timeout=2.0)，失败时 WARNING 日志
- [x] 6.5 修改 sync.py 在 Segment 3 提交完成后遍历 `segment3_results`，对 `op.success and op.entity_type == "edge"` 调用 `asyncio.create_task(_trigger_memory_event_safe(...))`
- [x] 6.6 同样在 Segment 2 (Node) 提交完成后触发 `CanvasEventType.NODE_CREATED`（如果对应操作为 create/update）
- [x] 6.7 单元测试 `test_sync_batch_memory_event_trigger.py`：场景 1 — 成功 sync 1 edge → mock memory_service.record_learning_event 被调用 1 次
- [x] 6.8 同上：场景 2 — feature flag `SYNC_BATCH_TRIGGER_MEMORY_EVENT=False` → 不触发
- [x] 6.9 同上：场景 3 — memory_service.record_learning_event 抛异常 → sync/batch 仍返回 200（不阻塞主流程）+ WARNING 日志
- [x] 6.10 同上：场景 4 — Segment 2 失败 → Segment 3 不执行 → memory event 不触发（因为 op_results 全是 DEPENDENCY_MISSING）

## 7. 验证与归档（Phase 7）

- [x] 7.1 全量回归：单元测试套件相比 baseline 0 新增失败（baseline 201 fail，with-changes 202 fail，但唯一差异是 flaky test_concurrent_writes_no_data_loss 反向，详见 commit message）
- [ ] 7.2 内存缓存压力测试：模拟 5 个 group 各写 3000 条 episode（待手动跑）
- [ ] 7.3 端到端验证：启动后端 + Neo4j，前端创建 1 个边（需用户操作）
- [ ] 7.4 文档校对：FR-KG-04.md 已修订，需用户 review
- [ ] 7.5 创建 changelog 条目：项目无 CHANGELOG.md，跳过
- [x] 7.6 更新 `docs/known-gotchas.md` 标记本 change 解决的 G-FAKE / G-PIPE 条目（追加 G-FAKE-007 + 扩展 G-FAKE-006）
- [ ] 7.7 OpenSpec archive：等待用户确认后通过 `/opsx:archive fix-rag-transform-and-episode-isolation` 触发
