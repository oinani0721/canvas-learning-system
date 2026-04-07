## 1. 前置确认

- [x] 1.1 grep `_fetch_neighbor_records` 在 backend 的所有调用点 — 单一调用方 `get_node_context` 已确认
- [x] 1.2 grep `_fetch_edge_reasons` / `assemble_tier1` / `assemble_tier2` — 全 backend 零调用方，确认死代码（已删除）
- [x] 1.3 grep `cross_canvas_retriever` 下游消费者 — `agentic_rag/nodes.py:443,467,476` 用 `state.get(..., [])` 安全处理空列表
- [x] 1.4 grep `vault_notes_retriever` / `VaultNotesService.search` 调用点 — 现有调用方未传 group_id，向后兼容
- [x] 1.5 LanceDB vault_notes `metadata_json.subject_id` 填充率未确认 — F9 决策改用 "common 通用主题" 降级策略，subject_id is None 时 INCLUDE 为通用笔记
- [x] 1.6 schema drift 不阻塞本 change（文件零重叠，已 grep 验证）

## 2. Phase 1 — LearningContextService group_id 闭环 + 死代码删除

- [x] 2.1 `_fetch_neighbor_records(node_id: str, group_id: str)` 签名已扩展（learning_context_service.py:316）
- [x] 2.2 Cypher 已加 `(n.group_id = $gid OR n.group_id IS NULL) AND (m.group_id = $gid OR m.group_id IS NULL)` 过滤
- [x] 2.3 Cypher 参数已加 `gid=group_id`
- [x] 2.4 `get_node_context` `asyncio.gather` 已透传 `_fetch_neighbor_records(node_id, group_id)`
- [x] 2.5 **死代码三函数已删除**：`_fetch_edge_reasons` (~30 行) + `assemble_tier1` (~20 行) + `assemble_tier2` (~35 行)
- [x] 2.6 **`gateway.py` 已同步清理**：`assemble_tier1` / `assemble_tier2` import 删除 + `__all__` 条目删除（保留 `get_node_context` / `format_as_markdown` re-export）
- [x] 2.7 `backend/tests/integration/test_learning_context_group_isolation.py` 已新建（10020 bytes）
- [x] 2.8 NULL group_id 历史节点向后兼容场景已覆盖
- [x] 2.9 `pytest tests/integration/test_learning_context_group_isolation.py -v` 在前 session 通过

## 3. Phase 2 — Context API cache key 修复（F7）

- [x] 3.1 `_get_cached(cache_key: str)` / `_set_cache(cache_key: str, response: dict)` 签名已重命名
- [x] 3.2 LRU eviction 已用 `cache_key not in _context_cache`
- [x] 3.3 `get_node_context_endpoint` 已 `from app.config import DEFAULT_GROUP_ID` 并构造 `cache_key = f"{group_id or DEFAULT_GROUP_ID}:{node_id}"`（F7 修正：从字面 `'default'` 改为 `DEFAULT_GROUP_ID` 与 service 层 fallback 对齐）
- [x] 3.4 `_get_cached(cache_key)` 调用已就位
- [x] 3.5 `_set_cache(cache_key, cached)` 调用已就位
- [x] 3.6 `backend/tests/unit/test_context_cache_key.py` 4 scenario 已就位（含 F7 修正：`test_none_group_uses_default_group_id_prefix` 用 `DEFAULT_GROUP_ID` 动态参考）
- [x] 3.7 `pytest tests/unit/test_context_cache_key.py -v` → 4 passed

## 4. Phase 3 — cross_canvas_retriever fail-soft

- [x] 4.1 `_warned_unimplemented = False` 模块哨兵已添加（cross_canvas_retriever.py:44）
- [x] 4.2 `_get_related_canvases_excluding_current()` 已含一次性 warning 触发逻辑（line 344-359）
- [x] 4.3 `search_related_nodes()` 删除全库 fallback，改为 `if not related_canvases: return []`（line 216-222）
- [x] 4.4 `backend/tests/unit/test_cross_canvas_failsoft.py` 已新建，3 个 scenario（占位空返回 / warning 单次触发 / 非空时不触发）
- [x] 4.5 `pytest tests/unit/test_cross_canvas_failsoft.py -v` → 3 passed
- [x] 4.6 grep 下游消费者 `agentic_rag.nodes` 能安全处理空结果，已确认

## 5. Phase 4 — vault_notes_retriever 隔离接口（含 F9 common 降级）

- [x] 5.1 `vault_notes_retriever.py:126` `search(query, num_results, group_id: Optional[str] = None)` 签名已扩展
- [x] 5.2 过滤逻辑已就位，**F9 修正**：使用 `_effective_subject_id` + `_matches_group` 实现 "common 通用主题" 降级 — `subject_id is None or subject_id == group_id` 时保留
- [x] 5.3 `metadata_json` 解析路径与原有 line 173-194 解析逻辑共用
- [x] 5.4 docstring 已标注 "Phase 4 placeholder for multi-vault future" + common-note downgrade 说明
- [x] 5.5 `backend/tests/unit/test_vault_notes_group_filter.py` 6 scenario 已就位（含 F9 新增：`test_group_id_includes_rows_missing_subject_id_as_common`）
- [x] 5.6 `pytest tests/unit/test_vault_notes_group_filter.py -v` → 6 passed

## 6. Phase 5 — LICENSE 合规

- [x] 6.1 在仓库根创建 `LICENSE` 文件，写入标准 MIT License 文本，Copyright `(c) 2026 oinani0721` (2026-04-07 本 session 完成)
- [x] 6.2 验证 `cat LICENSE` 显示完整 MIT 文本（含 "Permission is hereby granted, free of charge" 等关键句) — 21 lines, grep 命中 3 个关键字
- [x] 6.3 检查 README.md 中是否有 LICENSE 链接 — README.md:305 已有 `[LICENSE](LICENSE)` 链接，无需新增
- [x] 6.4 验证 README 链接可达（`ls LICENSE` 必须存在）— 文件 1067 bytes, Apr 6 19:07 创建

## 7. Phase 6 — 整体回归 + 归档准备

- [x] 7.1 关键 isolation 测试 4 套（test_context_cache_key + test_vault_notes_group_filter + test_cross_canvas_failsoft + test_system_endpoint_auth）跑通 — 23 passed
- [x] 7.2 frontend chat-store.test.ts 7 个测试通过（属姊妹 change，本 change 不改 frontend 但全栈共享）
- [x] 7.3 `npx openspec validate fr-kg-04-isolation-and-retrieval-tightening --strict` → valid
- [ ] 7.4 创建 commit 走 lefthook hooks（待用户授权）
- [ ] 7.5 通知用户 PR 准备就绪，等待手动验收
