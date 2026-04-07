## Why

`fix-fr-kg-04-schema-drift-and-sync-hardening` change 修了 sync **写入端**的 group_id 隔离（MemoryService 内存路径、SyncService 写入路径已 commit `27bbd73`），但 FR-KG-04 闭环还需要：

1. **读取端隔离**：`LearningContextService._fetch_neighbor_records` 与 `_fetch_edge_reasons` 的 Cypher 查询完全没有 `group_id` 过滤，可以从 Subject A 漏读出 Subject B 的邻居节点；`/api/v1/context/{node_id}` 的 30s TTL `_context_cache` 只用 `node_id` 作 key，跨 group_id 调用同一节点会拿到上一个 group 的缓存（read-time data leak）。
2. **检索退化路径**：`cross_canvas_retriever.find_related_canvases` 当前是占位实现永久返回空 list，触发 `search_related_nodes:208-214` 的 fallback 路径——后者**不传 `canvas_file` 参数**直接全库 `lancedb.search`，扩大了暴露面（R6 风险确认）。
3. **隔离接口准备**：`vault_notes_retriever.search` 的签名完全没有 `group_id` 参数，`metadata_json` 的 `subject_id` 字段从未被过滤过。当前架构假设单 vault 单用户，但缺少未来多 vault 的接口占位。
4. **合规债**：仓库根缺 LICENSE 文件（R8）。README 已经写了 "See LICENSE" 但目标不存在。

合并后 ChatGPT 报告 #6 的 6 个核心风险全部归零。

## What Changes

- **LearningContextService group_id 闭环 + 死代码删除**：
  - `_fetch_neighbor_records(node_id, group_id)` 签名增加 `group_id` 参数，Cypher 增加 `(n.group_id = $gid OR n.group_id IS NULL) AND (m.group_id = $gid OR m.group_id IS NULL)` 过滤
  - `get_node_context()` 把 `group_id` 透传给 `_fetch_neighbor_records`
  - **删除 3 个死代码函数**（grep 全 backend 零调用方，且 `backend/app/domains/memory/gateway.py` 已不再 re-export）：
    - `_fetch_edge_reasons(node_id)` ≈ 30 行
    - `assemble_tier1(node_id, group_id)` ≈ 20 行
    - `assemble_tier2(node_id)` ≈ 35 行
  - **同步删除 `backend/app/domains/memory/gateway.py` 的 4 行 re-export**（line 28/29 import + line 41/42 `__all__`）
  - 向后兼容：Cypher 保留 `OR IS NULL` 分支（历史无 group_id 数据仍可被读出，但新数据强制非空）

- **Context API cache key 修复**：
  - `_context_cache` 类型 `dict[str, ...]` 不变，但 key 从 `node_id` 改为 `f"{group_id or DEFAULT_GROUP_ID}:{node_id}"`（与 `get_node_context` 的 fallback 对齐，避免字面 `'default'` 与实际 `cs188` 不一致导致同一条目出现两个 cache key）
  - `_get_cached(cache_key)` / `_set_cache(cache_key, response)` 签名重命名以反映新语义
  - `get_node_context_endpoint` 先 `from app.config import DEFAULT_GROUP_ID` 再构造 cache_key，再调用辅助函数

- **cross_canvas_retriever fail-soft**：
  - `_get_related_canvases_excluding_current()` 新增检测：如果 `find_related_canvases` 返回空 list（视作"占位未实现"）→ retriever 节点函数返回空结果 + 一次性 warning 日志
  - `search_related_nodes` 不再退化为不带 `canvas_file` 的全库查询。原 `if not related_canvases: 全库 fallback` 分支删除
  - 在 retriever 模块顶部添加 `_warned_unimplemented` 哨兵避免重复打 warning

- **vault_notes_retriever 隔离接口准备（含 common-note 降级）**：
  - `search()` 增加 `group_id: Optional[str] = None` 参数（默认 None 保持当前行为）
  - 当 `group_id` 非 None 时，保留 `subject_id == group_id` 的条目 **以及 `subject_id is None` 的通用 (common) 条目**——即 `subject_id in (group_id, None)`。这避免当前 ingestion 路径尚未全量回填 `subject_id` 时过滤把结果集收敛为空
  - 节点函数 `vault_notes_retrieval_node` 暂不传 `group_id`（保持单 vault 假设）
  - 文档注释标注 "Phase 4 placeholder for multi-vault future"

- **LICENSE 合规**：
  - 在仓库根新建 `LICENSE` 文件（标准 MIT 文本，作者 oinani0721，year 2026）
  - README 现有的 "See LICENSE" 链接验证可达

## Capabilities

### New Capabilities
- `repo-compliance`: 仓库根级别的合规要求（LICENSE / SECURITY.md / 第三方授权清单）。当前 change 仅落地 LICENSE，后续 change 可在此 capability 下扩展 SECURITY.md 与 SBOM 生成。

### Modified Capabilities
- `algo-rag`: 新增 retriever 隔离与 fail-soft 退化策略要求（cross_canvas + vault_notes）。修改对象是已有的 RAG capability 主 spec（虽然主 specs 目录下 algo-rag/spec.md 文件还不存在，但本 change 用 ADDED Requirements 头部即可，归档时会作为该 capability 的首批 requirement 落地）。

⚠️ **OpenSpec 校验注意**：`openspec/specs/` 目录下当前只有 `canvas-recommendations/spec.md`，其他 capability 的主 spec 都尚未归档。本 change 的 `specs/algo-rag/spec.md` 与 `specs/repo-compliance/spec.md` 都用 `## ADDED Requirements` 头部，归档时由 CLI 自动创建主 spec 文件。

## Impact

### Affected code
- `backend/app/services/learning_context_service.py:412` `_fetch_neighbor_records` — 签名扩展 + Cypher 过滤
- `backend/app/services/learning_context_service.py:202` `_fetch_edge_reasons` — 同上（如未死代码）
- `backend/app/services/learning_context_service.py:333` `get_node_context` — 透传 group_id
- `backend/app/api/v1/endpoints/context.py:95-117` `_context_cache` + `_get_cached` + `_set_cache` — cache key 重构
- `backend/app/api/v1/endpoints/context.py:206-209` `get_node_context_endpoint` — 构造 cache_key
- `backend/lib/agentic_rag/retrievers/cross_canvas_retriever.py:208-214` — 删除全库 fallback
- `backend/lib/agentic_rag/retrievers/cross_canvas_retriever.py:324-337` `_get_related_canvases_excluding_current` — 添加占位检测
- `backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:126-202` `search` — 新增 group_id 参数与过滤逻辑
- `LICENSE`（仓库根，新建）

### Affected APIs
- `GET /api/v1/context/{node_id}?group_id=<X>`：相同 node_id 不同 group_id 不再共享缓存（行为变更，但向后兼容因为旧调用 group_id=None 仍走 'default' key）
- `cross_canvas_retriever.search()`：在 `find_related_canvases` 实现前永远返回空列表而非"全库结果伪装成 cross_canvas"（行为变更，下游消费者必须能处理空结果——已检查 `agentic_rag.graph` 节点函数已经处理空结果）
- `vault_notes_retriever.search(query, num_results, group_id?)`：新增 optional 参数，向后兼容

### Dependencies
- 无新依赖
- 与 `fix-fr-kg-04-schema-drift-and-sync-hardening` 文件无重叠：写入端在 `sync_service.py` / `memory_service.py`，本 change 在 `learning_context_service.py` / `context.py` / 两个 retrievers
- 与 `fr-kg-04-prompt-injection-and-auth-completion`（姊妹 change）文件无重叠

### Rollback
- 删除新增 `LICENSE` 文件（git rm + commit）
- `git revert` learning_context_service.py / context.py 单 commit
- retriever 改动通过 git revert 单 commit
- vault_notes_retriever 的 group_id 参数有 `Optional[str] = None` 默认值，向后兼容

### Verification
- `pytest backend/tests/integration/test_learning_context_group_isolation.py -v` — 多 group 同名概念串读测试
- `pytest backend/tests/unit/test_context_cache_key.py -v` — cache key 唯一性测试
- `pytest backend/tests/unit/test_cross_canvas_failsoft.py -v` — fail-soft 退化空结果测试
- `pytest backend/tests/unit/test_vault_notes_group_filter.py -v` — group_id 过滤测试
- `cat LICENSE` 显示 MIT 文本
- `pytest backend/tests/ -x -q` 整体回归
