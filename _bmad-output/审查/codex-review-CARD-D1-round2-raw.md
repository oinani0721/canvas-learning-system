复核对象：当前 HEAD `b923ff67`；仅做静态阅读与内存反例推演，未运行会写临时文件的 pytest，目标四文件 AST 正常且工作树无新增改动。

- H1 — RESOLVED — `9999-12-31T23:59:59Z` 虽通过日期门禁，但 `_humanize_due` 在 [review_overview.py:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:229) 捕获 `OverflowError` 并安全显示“—”，不再 500。
- H2 — RESOLVED — [review_overview.py:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:430) 的严格 UTF-8 编码会让 `\ud800` 抛 `UnicodeEncodeError`，随后统一降级 `corrupt`，JSON/HTML 两端均无逃逸。
- H3 — RESOLVED — [review_overview.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:139) 仅对非空 scheduled 时间取最小值，内存推演“new+逾期”得到逾期时间而非空串，测试也在 [test_review_overview.py:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/tests/unit/test_review_overview.py:418) 锁定。
- H4 — STILL-OPEN — 点名的 due 漂移、缺失到期板及 placeholder=999 均被拒，但 [review_overview.py:198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:198) 仍放行全零幽灵板、`future=999/next_due=""`、`due_new=due_scheduled=999` 和 `stats.due_nodes=999`，故一轮要求的完整构造律及跨源一致性未闭合。
- H5 — STILL-OPEN — `boards:null`、重复 due/top/upcoming、空 due node 和垃圾 placeholder 元素均已拒收，但 [review_overview.py:330](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:330) 仍接受空 top board、[review_overview.py:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:165) 接受空 upcoming node、[review_overview.py:390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:390) 接受非法 date 并发 `ok`。
- H6 — RESOLVED — NO-CHANGE 主张属实且自洽：`stale` 降级逻辑及对应测试均源自 CARD-C2 提交 `434141b6`，早于 CARD-D1，D1 仅把本地日换为上海时区，未引入该语义。

- 新增 500/误杀 — RESOLVED — 未发现新 500 路径或过严门禁；生产器由唯一文件 stem、按板字典及集合构造 due/top/upcoming/rollup，[daily_review_pick.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/scripts/daily_review_pick.py:252) 至 315 的真实成功产物满足全部新增门禁。
- M1 — STILL-OPEN — 合法生产场景“只有无 source_board placeholder”会生成 `boards=[]`，而 [review_overview.py:576](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/app/api/v1/endpoints/review_overview.py:576) 在 `ph_known=[]` 时把未归板差额错误置零，仍不显示注记。
- M2 — RESOLVED — [test_daily_review_pick.py:380](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/tests/regression/test_daily_review_pick.py:380) 已用完整字面 golden、深度全等及顶层键序冻结旧 payload。
- M3 — RESOLVED — [test_review_overview.py:689](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/tests/unit/test_review_overview.py:689) 固定上海 `00:30` 的三条跨 UTC 日边界，能有效击穿错误 UTC 日期算法。
- L1 — RESOLVED — [test_review_overview.py:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/tests/unit/test_review_overview.py:18) 已与生产代码一致地回退固定 UTC+8。
- L2 — RESOLVED — [test_review_overview.py:375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/backend/tests/unit/test_review_overview.py:375) 对小写全文拒绝任意 `<script`，内联脚本不再漏检。
- L3 — RESOLVED — [daily_review_pick.py:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m1-anki/scripts/daily_review_pick.py:85) 的 docstring 已准确声明四元组及 `placeholder_boards` 语义。

BLOCKER/HIGH 清零: 否（H4 完整构造律仍有旁路，H5 空值及非法 date 门禁仍未闭合）


