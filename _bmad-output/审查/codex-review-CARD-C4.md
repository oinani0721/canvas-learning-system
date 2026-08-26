结论：**FAIL，不建议通过 CARD-C4**。无 BLOCKER；发现 **1 HIGH、3 MEDIUM、3 LOW**。安全下线方向正确，也未误伤真实调用链，但“失败不再谎报”尚未闭环。

## 分级问题

### BLOCKER

无。

### HIGH

1. `save_card_state()` 在唯一 JSON 持久化失败时仍返回 `True`

[review_service.py:325-343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:325) 吞掉 `OSError/TypeError`；[review_service.py:1992-2015](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1992) 却承诺“cache + JSON file”“True if saved successfully”，最后无条件返回 `True`。

真实入口复现：

```text
_CARD_STATES_FILE=/dev/null/card-states.json
→ Failed to save FSRS card states: Errno 17
→ return_value=True
→ 仅内存缓存有值，磁盘无值
```

这会把“本进程暂存、重启即丢”报告成持久化成功。相同 helper 也用于实际评分和自动建卡路径 [review_service.py:1009](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1009)、[review_service.py:2080](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:2080)。

修复建议：让 `_save_card_states() -> bool` 或向上传播异常，`save_card_state()` 仅在原子替换成功后返回 `True`，并让另外两处调用消费失败结果。因这会触及本卡禁止修改的其他 `except` 模式，应明确扩权或拆独立修复卡。

### MEDIUM

1. “该存储自诞生起 0 条记录”被历史直接反证

[review_service.py:1964-1968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1964) 的绝对陈述不成立：Git 历史中的 `learning_memories.json` 记录数曾依次达到 `5/60/152/171/179`；仓库主工作树当前也是 `25 条 / 9025B`，只有本 C4 工作树为 `0 条 / 110B`。[agent_service.py:5019](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/agent_service.py:5019) 仍有真实 `add_learning_episode()` 写入口。

真正成立的依据是 [neo4j_edge_client.py:725-746](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/clients/neo4j_edge_client.py:725) 的 canonical schema 无 `card_data`，历史记录同样无该字段，因此无法恢复 FSRS 卡。

建议改为：“历史存在普通 LearningMemory 记录，但受支持 schema 从不承载 `card_data`，因此从未持久化 FSRS 卡镜像记录。”

2. 文档把“不可达成功日志”误写成“运行时每次报成功”

问题见 [known-gotchas.md:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/docs/known-gotchas.md:18)、[review_service.py:1995-1998](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1995) 和 [验收单:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/_bmad-output/验收单/Story-CARD-C4-假Graphiti镜像下线.md:22)。

HEAD 旧代码先调用不存在的方法，之后才是 success log；`AttributeError` 时 success log 不可达，实际打印 warning。验收单“每次都在日志里报存储成功”明确不实。

建议表述为：“镜像调用每次失败并记 warning，但返回值不区分镜像失败；源码另含永远不可达的成功日志。”

3. 整体防复活覆盖不完整

[TestAutoPersistCounterRemoved:587-599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/unit/test_review_service_fsrs.py:587) 能锁住原计数器，[test_get_fsrs_state_spawns_no_background_tasks:219-229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/unit/test_fsrs_state_query.py:219) 和新增的直接 `create_task.assert_not_called()` 能锁住原后台任务；这两项本身有效。

但没有生产入口测试锁住 `save_card_state`、`load_card_state` 不得重新访问 LearningMemoryClient，也没有文件失败返回值测试。因此两处直接幻影路径可复活而现有核心锁仍全绿。

修复建议：补 load/save 真实入口的“零外部访问”测试及不可写目标下返回失败测试。

### LOW

1. [test_story_38_3_fsrs_init_guarantee.py:333-351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py:333) patch 了整个 `review_service.asyncio`，连 `asyncio.to_thread` 也被替换，导致唯一文件通道实际触发 TypeError 后被吞。它能锁 `create_task`，但不能证明“只走文件通道”。建议只 patch `asyncio.create_task`。

2. [test_story_38_3_edge_cases.py:79-96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/unit/test_story_38_3_edge_cases.py:79) 的两个 `load_card_state = AsyncMock(...)` 没有 `assert_awaited_once_with`；内部调用若被删，用例仍会绿。建议补 await 断言。

3. 验收追踪已过时：[验收单:61、119-126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/_bmad-output/验收单/Story-CARD-C4-假Graphiti镜像下线.md:61) 仍写“三个测试文件”且命令漏掉新修改的第四个测试文件；[验收单:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/_bmad-output/验收单/Story-CARD-C4-假Graphiti镜像下线.md:15) 引用的 goal-card 文件在本工作树及主工作树均不存在。

## 六个审查维度

1. **真实读写路径：PASS，无问题。** 五处 ReviewService 历史读取仍在 `1137/1362/1616/1717/1882`；memory endpoint → `MemoryService` → Neo4j 链与 HEAD 字节一致；真实边写 `add_edge_relationship`、`add_episode_for_edge` 仍在 [review_service.py:1437-1448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1437)。

2. **删除完整性：FAIL。** 可执行的 `add_learning_memory`、计数器、`contextvars`、旧成功/失败日志已清零；`_persist_auto_created_card` 仅剩历史说明注释。但 HIGH 的文件失败谎报仍存在。

3. **`load_card_state` 语义：PASS，无问题。** 缓存命中返回状态、缺失返回 `None`；`canvas_name` 在 [review_service.py:1972](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1972) 已诚实标注 unused；内部调用仍在 `2064`。

4. **测试适配：PARTIAL。** 四处直接 `await` 无异步残留；两个指定防复活锁对原实现有效，但存在上述整体覆盖缺口和 LOW 测试问题。

5. **文档与契约：PARTIAL。** “真接 Graphiti 等 C-1/C-2”与 [_bmad-output/.claude/CLAUDE.md:279-290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/_bmad-output/.claude/CLAUDE.md:279) 的唯一写 schema、唯一读 facade、禁止双主干契约一致，**无问题**；历史数量及日志描述不准确。

6. **硬边界：PASS，无问题。** 未触碰 `scripts/daily_review_*`、任何 `skills/`，也未修改授权目标之外的 `except` 模式。

验证：最终快照为 HEAD `58183ba9`；目标 5 文件 `92 passed`，额外文件持久化/并发测试 `16 passed`；Ruff 与 `git diff --check` 通过。未运行全套 CI。审查期间并发新增了 `test_story_38_3_fsrs_init_guarantee.py` 修改，本报告已按最终工作区重审；我未修改任何文件。



---

## 处置记录（Claude Code, 2026-08-25）

> 审查结论 FAIL（0 BLOCKER / 1 HIGH）后按 BLOCKER/HIGH 清零纪律全部处置。审查同时确认：真实读写路径 PASS（未误删）、load_card_state 语义 PASS、硬边界 PASS。

| 级别 | 发现 | 处置 |
|---|---|---|
| HIGH-1 | save_card_state 在唯一 JSON 持久化失败时仍 return True（"仅内存暂存、重启即丢"谎报成持久化成功） | ✅ FIXED（最小闭环，不改 except 捕获模式）— `_save_card_states()` 改为返回 bool（try 尾 return True / 既有 except 尾 return False，捕获类型与日志级别零变化），`save_card_state` 消费该值如实返回；新增 /dev/null 不可写目标回归测试锁定 return False。评分（:1009）与 auto-create（:2080）两处调用点的失败信号消费需改其控制流 = 越界（档案明令不动其他区段），docstring 显式注明移交后续卡 |
| MEDIUM-1 | "该存储自诞生起 0 条记录"被 git 历史反证（历史曾有 5→179 条普通记录；真实写入口 add_learning_episode 在 agent_service:5019） | ✅ FIXED — docstring 与 known-gotchas 表述改为审查建议版："canonical schema 从不承载 card_data——历史普通 LearningMemory 记录存在，但 FSRS 卡镜像从未被持久化，读侧按 card_data 过滤故永远 None" |
| MEDIUM-2 | "每次报成功"不实（AttributeError 时成功日志不可达，实际每次打 warning；不实处在 return True 不区分失败 + 永远不可达的成功日志） | ✅ FIXED — save_card_state docstring、known-gotchas、验收单三处表述全部修正为审查建议版 |
| MEDIUM-3 | 防复活覆盖缺口：无 load/save 真实入口"零外部访问"锁与文件失败返回值锁 | ✅ FIXED — 新增 test_save_and_load_card_state_touch_no_memory_client（get_learning_memory_client 被 monkeypatch 为 raise，load/save 正常完成即证零外部访问）+ test_save_card_state_returns_false_when_file_write_fails |
| LOW-1 | patch 整个 review_service.asyncio 连 to_thread 一起 mock，不能证明"只走文件通道" | ✅ FIXED — 两用例改为只 patch asyncio.create_task，文件通道真实执行 |
| LOW-2 | test_story_38_3_edge_cases 两个 load_card_state mock 无 await 断言 | ✅ FIXED — 补 assert_awaited_once_with |
| LOW-3 | 验收单"三个测试文件"过时 + goal-card 引用路径在本 worktree 不存在 | ✅ FIXED — 验收单更新为五个测试文件全景 + 档案路径改为 feature-obsidian-hybrid-dev worktree 绝对路径 |

附注：test_story_38_3_fsrs_init_guarantee.py 的两个"锁已删后台任务"用例在审查启动后由 Claude 自查发现并翻转为防复活锁（审查报告注明已按最终工作区重审）——与审查维度 4 的结论互相印证。
