结论：正常串行且 state 完整持久化时，上界成立；但按“任何路径、accepted 次数严格 ≤2”的字面契约，存在两条第 3 次 accepted 路径，不能清零。审阅基线为 `card/m3-push`、HEAD `1a63522b…`；未运行被审脚本或测试，未修改文件。

## BLOCKER

无。

## HIGH

1. [scripts/daily_review_run.py:242-249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:242) — Bark 已 accepted 后才保存状态。路径：rest accepted（第 1 次）→ due 返回 `rc=0`（第 2 次）→ 进程在 `save_state()` 前崩溃或保存失败 → 磁盘仍为 `kind=rest` → 下小时 due 再次 accepted（第 3 次）。同 ID 只保证覆盖，不能证明 accepted 调用次数上界。建议：若 accepted≤2 是硬契约，需 durable pending/receipt 与模糊结果 fail-closed；否则把契约限定为“状态成功持久化时最多两个语义版本”。

2. [scripts/daily_review_run.py:68-84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:68)、[scripts/daily_review_run.py:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:229) — 损坏 state 被直接重建为空账，丢失当日 accepted 事实。rest、due 已各 accepted 后，只要 state 损坏，下一轮即可再次 accepted；反复损坏可无界重复。建议：从独立 durable receipt 恢复，或当日损坏时保守闭门；否则必须明确上界依赖“state 未丢失”。

## MEDIUM

1. [scripts/daily_review_run.py:73-76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:73)、[scripts/daily_review_run.py:173](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:173) — 损坏重建只覆盖语法错误/OSError。合法 JSON `[]` 会在 `setdefault` 崩溃；`board_last_recommended: []` 会在 `.values()` 或 picker 中崩溃。现有测试 [test_daily_review_run.py:620-630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:620) 已明确承认前者。建议在 `load_state()` 做顶层及嵌套类型校验，统一进入隔离恢复。

2. [scripts/daily_review_run.py:229-247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:229) — cached legacy payload 缺 `top_boards` 时不会报错，但 accepted 分支把未知语义记成 `rest`。若旧 payload 实际是 due，后续新版 due 会被误判为 rest→due，形成 due→due 二推。建议缺键记为 `unknown/legacy` 并保守关闭反转；只有明确存在且为空的 `top_boards` 才记 `rest`。

3. [test_daily_review_run.py:716-809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:716) — 四个新测试未覆盖 `due→rest`。将门改成“未知 kind 保守拦截，但任意已知语义变化均放行”可让全部新测试及旧 state 守卫通过，却使 `rest→due→rest` 出现第 3 次 accepted。建议增加完整 `rest→due→rest→due` 振荡用例，第二次成功后用队列越界哨兵禁止所有后续发送。

## LOW

1. [scripts/daily_review_run.py:251-266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:251) — `rc=2` 不更新 `last_result/last_error`。早晨 rest 成功、下午 due 缺 key 时，当轮输出虽是 `skip-nokey`，持久状态仍显示旧的 `pushed`/空错误。建议写入明确的 no-key 状态，或明确字段只代表最后一次实际网络结果。

2. [test_daily_review_run.py:693-706](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:693)、[test_daily_review_run.py:784-809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:784) — 失败测试仅覆盖 `[0,1,0]`，且 fallback 恒返回 `True`、不计调用数，未锁定连续失败只弹一次，也未断言 `last_error`、`last_local_notify_date` 和成功后清错。建议改为 `[0,1,1,0]` 并记录 fallback 次数。当前正常持久化路径确实只弹一次；显示后、状态保存前崩溃仍可能重复。

## 七项逐项结论

| # | 结论 | 静态结果 |
|---|---|---|
| 1 | FAIL（绝对口径） | 完整串行状态下：rest→due→rest→due 最多 2；due→rest→due 最多 1；失败、skip-empty、skip-window、窗口边界均不增加 accepted。两条 HIGH 故障路径会突破。上界是 per-vault，不是多 vault 全局。 |
| 2 | PARTIAL | 旧 state 缺 kind 时恒保守 `skip-done`；既有 [测试:109-145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:109) 已锁定。损坏恢复则存在上述丢账/结构崩溃。 |
| 3 | PARTIAL | 二推 `rc=1` 保持 `rest`，次小时可重试；成功后写 `due` 并清错。正常 fallback 不重复，但持久化崩溃窗及 `rc=2` 状态语义仍有缺口。 |
| 4 | PASS | D2a 落账位于 [runner:173-186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:173)，不修改 push 字段；与推送门正交。旧无-kind 场景保持一致。 |
| 5 | PARTIAL | 改回旧门、删除 kind 写入、due/rest 对调及常见条件反写都会被抓；`rcs` 越界作为 Bark 额外调用哨兵可靠。但双向翻转 mutant 和 fallback 次数 mutation 可逃逸。 |
| 6 | PASS | tracked diff 仅两目标文件；`daily_review_pick.py`、`send_bark.py`、launchd plist 均零 diff。两个未跟踪审查/UAT 文档按范围排除且未读取。 |
| 7 | PARTIAL | 缺 `top_boards` 时 `.get()` 安全返回 `None`；门本身保守，但首次 accepted 会把未知旧格式误记为 `rest`。 |

BLOCKER/HIGH 清零: 否


