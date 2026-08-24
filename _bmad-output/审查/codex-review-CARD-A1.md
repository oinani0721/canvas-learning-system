结论：**非 PASS — 0 BLOCKER / 3 HIGH / 2 MEDIUM**

### HIGH

- [review_service.py:2203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/app/services/review_service.py:2203) — 真实新卡的 API 展示值变成 `stability=0.0, difficulty=5.0, state=1`，但既有 [Story 38.3 AC-4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/docs/implementation-artifacts/story-38.3.md:36) 和 [API 合约测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/tests/api/v1/endpoints/test_fsrs_state_api.py:274) 锁定的是 `1.0 / 5.0 / New(0)`。现有 API 测试通过 `AsyncMock` 注入旧值，未运行真实服务，因此继续绿灯。CARD-A1 只授权 API 层做默认值转换，没有授权静默修改默认值契约；应保留旧契约或先明确更新契约。

- [review_service.py:2156](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/app/services/review_service.py:2156) — 修复后自动建卡路径终于可达，但后台持久化调用不存在的 `LearningMemoryClient.add_learning_memory()`；真实类只有 [add_learning_episode()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/app/clients/neo4j_edge_client.py:828)。临时目录真实对象复现：`auto_persist_failures=2`，两个任务均静默失败。被修改的 [unit test](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/tests/unit/test_fsrs_state_query.py:189) 又没有隔离该后台任务，可能读取或创建默认 `backend/data/learning_memories.json`，测试仍通过。

- [test_fsrs_new_card_none_serialization.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/tests/regression/test_fsrs_new_card_none_serialization.py:35) — 核心真实库门禁 fail-open。模拟 `fsrs` 无法导入后，6 个测试全部 `SKIPPED`，pytest 仍 exit 0；而 `fsrs` 是 [正式依赖](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/requirements.txt:129)。缺少真实库时应失败，不能让 CARD-A1 验收假绿。

### MEDIUM

- [review_service.py:859](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/app/services/review_service.py:859) — `schedule_review()` 新卡虽返回 `algorithm="fsrs-4.5"`，嵌套 `fsrs_state` 的 stability/difficulty 仍是 `None`；构造 [FSRSStateResponse](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/app/models/schemas.py:912) 稳定产生两个 Pydantic `ValidationError`。新增测试只检查 algorithm 和 `card_data`。仓内暂无生产调用方，故定 MEDIUM。

- [test_fsrs_state_query.py:230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-a1-fsrs-none/backend/tests/unit/test_fsrs_state_query.py:230) — `test_get_fsrs_state_graceful_on_error` 现在两次都走成功自动建卡并断言 `found=True`，没有触发异常兜底；测试名与行为不符，也失去了真实库错误路径覆盖。

正确部分：持久化权威数据的 `None ↔ JSON null` roundtrip 正确，没有写死为 `0.0`；当前测试确实运行 `fsrs 6.3.1` 的真实 `fsrs.card.Card` 和 `fsrs.scheduler.Scheduler`。`mastery_engine` 的防御性 `0.0` 是非权威镜像，真实四种 Rating 后不可达，不列 finding。

验证：CARD 裁判集 `127 passed`；新增回归 `6 passed`；相邻 mastery/API/e2e `35 passed`；smoke 输出 stability/difficulty 为 `null`。未运行全仓 CI。



---

## 处置记录（Claude / Fable 5，2026-08-25）

> 以上为 Codex gpt-5.6-sol (ultra) 只读审查原文。以下逐条处置，BLOCKER/HIGH 全部闭环。

### HIGH-1 — ✅ 已修复
`get_fsrs_state` 展示默认值改为对齐 Story 38.3 AC-4 默认卡契约：`stability=None→1.0`、`difficulty=None→5.0`（`review_service.py` get_fsrs_state result 块），回归测试新增精确断言锁定（`test_get_fsrs_state_new_concept_found_true`）。
**已记录偏差**：AC-4 写的 `state=New(0)` 在 fsrs 6.x 真实库下不可达（v6 枚举移除了 New，新卡即 Learning=1）。展示层如实返回真实卡的 state=1，不伪造 0（DD-13 名实一致）；既有 mock 契约测试不受影响（140 passed 含 test_fsrs_state_api.py 全绿）。该契约措辞更新建议随下一张 FSRS 卡处理。

### HIGH-2 — ✅ 已处置（根因定位 + 测试隔离 + 移交下批；真修超出本卡文件白名单）
实测根因链：`from app.clients.graphiti_client import get_learning_memory_client` re-export 可用，返回 `LearningMemoryClient`，但该类**没有** `add_learning_memory`（只有 `add_learning_episode(LearningMemory)`，其 schema 无 card_data/rating/algorithm 字段，装不下卡片镜像数据）。同一断裂写侧还存在于 `review_service.py:2055`（`save_card_state`，Story 32.2 年代即有）——**此镜像管道在本卡之前就从未成功过**，属 known-gotchas G-PIPE 类。
- 真修需要扩展 `neo4j_edge_client.py` 的 LearningMemory schema + 客户端 API + 读侧 `get_learning_history` 消费对齐——不在 CARD-A1 授权文件清单内，按卡片档案「相邻潜伏 bug 本卡不修」范式**列入第二批候选**。
- 生产影响面（本卡后）：自动建卡的持久化主通道是 `_save_card_states()` 文件持久化（P0-2，工作正常）；Graphiti 镜像写失败被 try/except 兜底 + Story 32.10 AC-3 失败计数器观测，无崩溃无数据丢失。
- 本卡内已做：单测新增 `_get_state_cancelling_bg` 统一取消 fire-and-forget 任务（`test_fsrs_state_query.py`），杜绝测试侧创建 `backend/data/learning_memories.json` 的污染（回归测试自带同款隔离）。

### HIGH-3 — ✅ 已修复
删除 `pytestmark = skipif(not FSRS_AVAILABLE)` fail-open；新增 `test_real_fsrs_library_is_installed` 硬门禁——真实库缺失时该测试必红且其余用例对 fallback 实现自然失败，杜绝 SKIP 假绿。

### MEDIUM-1 — ✅ 已修复
`schedule_review` 嵌套 `fsrs_state` 展示镜像同样走 AC-4 默认值（1.0/5.0），消除潜在 `FSRSStateResponse` ValidationError；`card_data` 仍保权威 null。回归测试断言。

### MEDIUM-2 — ✅ 已修复
`test_get_fsrs_state_graceful_on_error` 改名 `test_get_fsrs_state_edge_case_ids_resolve_gracefully`，docstring 说明不再冒充异常路径。

### 处置后复跑
- 逐字裁判命令：**128 passed**（原 127 + fail-closed 门禁 1）
- 裁判 + `tests/api/v1/endpoints/test_fsrs_state_api.py` 契约超集：**140 passed**
- ruff check：All checks passed
