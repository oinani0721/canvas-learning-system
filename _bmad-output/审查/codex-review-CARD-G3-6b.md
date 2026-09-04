总裁决：**FAIL**。发现 1 个 HIGH；无 BLOCKER。虽然 121 项指定测试全部通过，但核心系数指纹声明可被实际排序变更绕过。

## 发现

- [HIGH] [scripts/daily_review_pick.py:275-282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:275)、[608-630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:608)、[754-759](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:754) — 排序因子序不是真正的运行时 SHA 真相源。摘要读取独立的 `RANKING_FACTOR_ORDER`，实际排序则硬编码在 `_tie`。纯内存交换 `_tie` 的 `board_last_recommended` 和 `min_last_examined` 后，板序从 `['B板','A板']` 变成 `['A板','B板']`，但 SHA 均为 `e3a6c062...88dea`。漂移告警也无法发现。建议用同一可执行因子描述符同时构造 `_tie` 和 canonical config，并加入“排序改变且 SHA 必变”的变异测试。

- [MEDIUM] [test_daily_review_pick.py:1581-1608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/tests/regression/test_daily_review_pick.py:1581) — 排序金样没有覆盖全部四级因子，却声称“任何排序变化都会翻车”。fixture 中所有 `pick` 相同、所有 `last_examined` 为空，仅一板有推荐记录；删除首因子、删除第三因子或交换第二/第三因子，top 3 都仍是 `['丁板','丙板','甲板']`。建议为每级因子增加互相冲突的两板 fixture，分别验证删除、换序、反向。

- [MEDIUM] [scripts/daily_review_pick.py:649-665](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:649)、[696-699](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:696) — 未来的 `board_last_recommended` 被 `max(0, ...)` 压成零天。实测 `now=2026-07-30`、记录为 `2026-08-01`，落盘解释为“今天已推荐过”，违反 S4 不虚构。建议将未来日期作为异常状态并生成诚实文案。

- [MEDIUM] [review_overview.py:678-684](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/app/api/v1/endpoints/review_overview.py:678)、[1032-1040](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/app/api/v1/endpoints/review_overview.py:1032) — `why_this_board` 与 `estimated_minutes` 被独立放行。只有 why、缺分钟时仍会渲染解释行，违反“任一字段缺省整块不出现”。现有测试 [test_review_overview.py:2142-2158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/tests/unit/test_review_overview.py:2142) 只覆盖双缺省和榜外板。建议把两字段作为原子对处理，并补两个单边缺失测试。

- [MEDIUM] [scripts/daily_review_pick.py:541-577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:541) — authoritative 缺键时静默回退。仅提供 `per_due_node` 会保留 `version=1`、默认补入 `per_new_node=5`，但 `stderr` 为空，与“逐项回落并点名”不符。建议对缺 section、缺对象及缺单键分别告警；实际回退值继续进入 SHA。

## 逐项裁定

| 项 | 结论 | 判断 |
|---|---|---|
| A | PARTIAL | why 是纯函数，落盘 factors 可逐字复算；due 三分、rollup、idle 同源。未来推荐日文案及 UI 单缺字段存在上述问题。UI 未重新估算分钟。 |
| B | FAIL | 有效 SHA `e3a6c062...` 与 manifest 文件字节 SHA `33dcfaf0...` 不同，确认不是文件哈希；六个 decay、两个分钟、两个上限逐项变异均改 SHA，recorded 不改行为。但真实排序因子序可变化而 SHA 不变。 |
| C | PARTIAL | `schema_version` 仍为 3；两个累积金样是硬编码历史快照并锁嵌套键序；当前 `_tie` 与基线一致，runner/禁改文件 diff 为空。排序门覆盖不足。 |
| D | PASS | 无归属、多板、同名板、上限、去重均有独立生产路径测试。实测 YAML 数组得到 `(None, None)`；逗号串得到完整原串并归为 `B板`，与 S6 书面声明一致。 |

验证结果：

- 指定测试：`121 passed, 10 warnings`。
- `git diff --check 9af18b27`：通过。
- 禁改文件及 `daily_review_run.py` 相对基线：零差异。
- tracked diff 恰为四个指定文件；另有新 manifest。`git status` 还显示 W6 明示要求生成的 Codex prompt/report/stderr 和 UAT，若“应无其他”按全部 untracked 字面解释，则范围并非严格只有五项。
- 未运行可能触发 Bark 的 runner 场景，也未读取 live vault 原始 frontmatter；“现网 14 节点均单值”未独立复核。上述 121 项不是全量 CI。


