# Codex 复核任务 — CARD-RED-MOCKFIX（第十四批 T10-A）

## 一 背景 + 最小读取面（写死，勿越界）

仓库：Canvas Learning System。车道树：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`。
基线 `08100483`（B14_BASE），审查 SHA = `f6e4f8a1`（当前 HEAD）。

本卡做的事：`backend/tests/unit` 下 27 条测试长期以 **setup ERROR** 失败，失败身份统一为
`TypeError: 'MagicMock' object can't be awaited`，崩点在生产
`backend/app/services/memory_service.py:384`（`_recover_episodes_from_neo4j` 内
`records = await self.neo4j.get_all_recent_episodes(...)`，由 `initialize():285` 触发）。
根因判定为**测试侧 mock 漏桩**（生产恢复链路是 Story 38.2 的真实行为，不是缺陷）。
修法：在 7 处 `mock_neo4j` fixture 各补一行
`neo4j.get_all_recent_episodes = AsyncMock(return_value=[])`。**生产代码一行未动。**

最小读取面（只读这些，不要扩散到其它目录）：

1. `git -C <车道树> --no-pager diff --no-color 08100483 f6e4f8a1 -- . ':(exclude)_bmad-output'`
2. 三个测试文件全文：
   - `backend/tests/unit/test_memory_service_batch.py`
   - `backend/tests/unit/test_story_30_11_batch_parallel.py`
   - `backend/tests/unit/test_story_30_13_batch_idempotency.py`
3. `backend/app/services/memory_service.py` 的 `:276-288`（`initialize`）与 `:320-443`
   （`_recover_episodes_from_neo4j`）—— **只读，本卡不改它，也不要评价它的设计**；
   另可读 `:1285-1469`（`record_batch_learning_events`）判断降级语义，同样只读。
4. 证据目录（可选，用于核对我下面的自述）：`_bmad-output/审查/evidence-red-mockfix/`

## 二 作者自述（请逐条独立核对，不要采信）

1. `get_all_recent_episodes` 是 `initialize()` → episode 恢复链路上**唯一**被 await 的漏桩子属性。
2. `mock_neo4j` fixture 全仓这三文件里共 **7 处**（`test_story_30_11_batch_parallel.py` 五个类各一处、
   `test_story_30_13_batch_idempotency.py` 模块级一处、`test_memory_service_batch.py` 一处），
   已逐处补桩，无遗漏。
3. 桩值取 `[]` 而非非空：生产 `:388` 是 `if records:`，返回 `[]` 时 `self._episodes` 保持为空，
   与补桩前逐字节等价；若返回非空会往 `_episodes` 预置 `episode_type="recovered"` 条目。
4. 三条「Neo4j 不可用仍落内存」用例（`test_neo4j_disconnected_still_stores_in_memory` /
   `test_neo4j_unavailable_still_processes_to_memory` / `test_neo4j_unavailable_fallback`）的
   「不可用」设定点在**写侧**：`record_batch_learning_events:1384` 读 `self.neo4j.stats["initialized"]`；
   而恢复路径 `:320-443` 全文不读 `stats`。故恢复桩与被断言的降级行为正交。
5. 第 11 条 `test_config_batch_neo4j_concurrency_exists` 改前后皆绿（它不请求这些 fixture）。
6. 三文件：改前 27 error + 1 passed → 改后 28 passed / 0 error / 0 failed。
7. `tests/unit` 目录级 nodeid 口径与 64 条红基线 diff 只有 27 条 `<`、零条 `>`。
8. 未改任何 conftest，未引入 `autouse` fixture，未碰 `backend/app/**`。

## 三 请按重要性排序回答的问题

0. 补 `AsyncMock(return_value=[])` 是否在任何一条相关用例里**改变了被断言的行为**？
   对照输入：把返回值换成非空列表，是否会让某条断言翻转或变成恒真——若会，说明该用例其实
   依赖恢复结果，桩值选择有隐患。请指出具体 nodeid 与断言行。
1. 是否有用例进入函数体后仍依赖**别的、未被本卡补桩**的异步 neo4j 子属性，只是恰好没被当前
   断言触达？即门未覆盖的路径。
2. 第二节第 4 条的定性是否成立？恢复桩返回 `[]` 会不会顺带满足了某条本应失败的前置条件？
3. 是否存在过度修法痕迹（例如把 `MagicMock()` 整体换成 `AsyncMock()`、放宽断言、改动 skip 标记）？
4. 「目录级 diff 只 `<`」这个判据本身是否可能被路径前缀 / 通配符 / 颜色码等问题静默失效？
   证据文件在 `evidence-red-mockfix/`（`base.nodeids` / `close2.nodeids` / `diff-base-close2.txt`）。
5. 是否误改了 conftest 或引入了 autouse fixture？
6. 已知红 `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 在收工
   第 1 轮出现、第 2 轮（同一份代码）消失。作者判定其为与本卡无关的 W4 哨兵抖动，依据是
   该文件收集序 670、早于本卡三文件（2899 / 4341 / 4370）。该归因是否站得住？

## 四 输出格式

逐条给出：`BLOCKER` / `HIGH` / `MEDIUM` / `LOW` + `file:line` + 一句说明如何自行验证该问题。
无问题则明确写「该级别 0 条」。末尾给出四个级别的计数汇总。

## 五 边界

- 只读，不要修改任何文件，不要连接任何数据库或网络服务。
- 不评价生产 episode 恢复链路的设计取舍（那是 Story 38.2 / CARD-G4-1b 的既有决策）。
- 不评价第十四批 T10-B / T10-C / T10-D / T10-E 的面（`test_agent_service_extraction.py`、
  `requirements.txt`、`test_graphiti_json_dual_write.py` 等均不在本卡范围）。
- 不评价 `ruff format` 的既有格式漂移（整仓重排是第十五批单独一条 commit 的事）。
