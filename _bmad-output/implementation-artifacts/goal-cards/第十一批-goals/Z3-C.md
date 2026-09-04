> ⚠️ 本文件是 CARD-W4-3c 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z3-C 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-W4-3c]`。车道：`card-z3-w4`，**前提 Z3-B 已独立 commit**。微卡 1h。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-W4-3c — `test_search_error_memories.py` 转真 mock（门抓到的第二个主干既有偷连）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 第十批集成树门下目录级 `tests/regression` 抓到：`test_search_error_memories.py` 3 条用例经 `neo4j_client` health_check 连 7691（`blocked=1`），与 `test_story_38_3` 同型 | 复核裁定 §四.4 / 台账 §一.b X4 行 |
| 根因一行：测试 patch 的是 `svc.search_memories`（test:22），被测路径直接调 `self.search_memories_with_status`（`memory_service.py:2496`）；`search_memories`（`:2450`）反过来是委托 `_with_status` 的兼容壳 → patch 对被测路径零作用 → 走 `:2319 await self.initialize()` → `:278 self.neo4j.initialize()` → health_check → bolt 7691 | memory_service.py |
| 四条用例共用同一个 `_call()` helper、同一条 `:2496` 路径；台账记「×3」是因为 Neo4jClient 单例首次 initialize 失败后转 JSON fallback、后续不再重连——**不要把「3 变 0」当验收判据**，以「blocked=0 且 mock 被 assert_awaited」为准 | 计数口径 |
| `MemoryService(neo4j_client=…)` 构造签名本就支持注入（`memory_service.py:231-243`） | 现成 |
| 返回值形状 `StatusedResult.from_items(hits)`（`from app.models.service_status import StatusedResult`，与 `memory_service.py:2530` 同源） | 现成 |
| X4 在 `test_story_38_3_fsrs_init_guarantee.py` 里已有同型 mock 范式（docstring 写链路与依据） | 参照 |

## 一 完成条件（AND）
- (a) `_call()` 里 patch 目标由 `search_memories` 改为 `search_memories_with_status`，返回 `StatusedResult.from_items(hits)`；四条用例一处改全。
- (b) `MemoryService` 构造不再取进程单例：`MemoryService(neo4j_client=MagicMock())`，断绝 `get_neo4j_client` 单例被本文件污染。
- (c) helper docstring 按 test_story_38_3 范式写清链路：`memory_service.py:2496 → :2319 initialize() → :278 self.neo4j.initialize() → health_check → bolt 7691`，并注明「旧 patch 目标是兼容壳，对被测路径无效」。
- (d) **防回归断言**：mock 的 `search_memories_with_status` 必须 `assert_awaited`（或 `assert_called_once`）——证明 patch 真的落在被测路径上。
- (e) 四条用例原有断言语义（过滤 2 条 / schema 七字段 / limit=3 / 空列表）一字不改。
- (f) 门下实跑：session 末尾 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 摘要 `blocked=0`。
- (g) 人工反证写进验收单：临时删 (d) 的 assert 并把 patch 目标改回 `search_memories` → 必须重新出现 `blocked>0` → 还原。
- (h) 默认**不送 Codex**（微卡，Z3-B round-2 的读取面已覆盖 `tests/regression/conftest.py`）；若 (g) 反证失败则升 1 轮。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_search_error_memories.py` → 4 passed，摘要行 `blocked=0`。
2. `… $PYTEST -q -p no:cacheprovider tests/regression` → 1371+ 绿基线不回退（主干既有红 2 条 `test_write_side_group_guard` 登记，Z4 合入后为 0），`blocked=0`。
3. `… bash scripts/lifespan_isolation_runtime_sha.sh -- <venv>/python -m pytest tests/regression/test_search_error_memories.py -q -p no:cacheprovider` → `unchanged`。
4. (g) 反证输出贴验收单。

## 三 禁改与隔离
禁用 `pytest.mark.integration` / `real_neo4j` marker 或把文件挪进 `tests/integration/` 来「消掉」告警（那是走 advisory 豁免）；禁改 `app/services/memory_service.py`（若 `:2496` 委托关系需改，登记移交）；不连 7691/7687，不起真 Neo4j 或测试容器；禁重写四条用例断言语义；不改台账；不 push。

## 四 验收单
`…/验收单/UAT-CARD-W4-3c-<日期>.md`：DoD-3 双段；4-B「无变化（一组测试以前偷偷去碰真数据库，现在不碰了）」；「本卡未证明什么」必填；「台账待登记条目」必填（X4 行 ×3 → 已转 mock）。commit header ≤100 含批次标记，body 行 ≤100；不 push；跑完说「复核第十一批 Z3」。
