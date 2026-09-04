需整改

[MEDIUM] [backend/scripts/validate_learning_events.py:1506](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1506) — 节点预算检查晚于整批子节点入栈，不能约束检查器自身的内存。实测 10,000 路自引用列表在仅访问约 65 层后才因深度拒绝，但 `tracemalloc` 峰值已达 `46,866,757 bytes`；扇出接近 20 万时可先构造约 1 GB 待处理栈。普通自引用实际报“深度超过 64”，也不符合 [docs/learning-events-schema-v1.md:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:114) 所写的“节点预算保证终止并报真因”。建议改成逐个取 child 的 lazy DFS，并用 active-path identity set 直接判环。

[MEDIUM] [backend/tests/regression/test_g3_2_review_ledger.py:5407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5407) — 精确的 64 层/20 万节点边界没有独立 oracle。`_max_legal_nesting()` 反问被测函数自身；我在 `/tmp` 把深度有效阈值放宽两层，相关三门仍 `3 passed`，而最大深度 65 的完整 record 已被放行；把节点阈值放宽 1，新增七门仍 `7 passed`。当前实现对普通链确实是 depth 64 PASS/65 FAIL、200000 nodes PASS/200001 FAIL，但测试守不住这些数值。另一个未定义边界是：root 从 0 起算，因此 64 条边、共 65 个容器且末端为空时仍 PASS。建议在契约明确 root、dict key、空容器的计数口径，并直接锁定 64/65 与 200000/200001。

[MEDIUM] [backend/tests/regression/test_g3_2_review_ledger.py:5511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5511) — 自引用门未到达新形状防线。实际第二跑 `rc=1`，但 stderr 是 `receipt 不可解析 ... 节点/测试节点.md`：`board_form: json` 使 [SKILL.md:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:451) 先对 YAML list 调 `json.loads()`，异常被吞；`:5536` 又被路径中的“节点”喂饱。隔离禁用整个 shape 调用后该门仍 `1 passed`。建议直接把循环对象交给 `value_shape_problems()`，精确断言环/预算拒因并排除 `receipt 不可解析`。

[MEDIUM] [backend/tests/regression/test_g3_2_review_ledger.py:5539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5539) — 六格门只打印、不校验三元组。我把 `_triplet()` 改成恒返 `(99, "WRONG-W", 999)`，六行全部错误仍 `1 passed`；现有断言只有 `len(rows)==6` 和最终 validator `rc=0`。建议逐格断言固定的 `(rc,W,ledger)`，最好隔离 fixture。

[LOW] [backend/tests/regression/test_g3_2_review_ledger.py:5279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:5279) — 512/900 降至最大合法约 62 后，原先“递归恢复会炸”的性质确实失去守护。把 `_canon_tree` 换回等价递归实现，当前门仍 PASS；因此 `:5289-5291` 所称“仍只有显式栈守着”不成立。由于新契约已把 >64 删除出合法输入域，这不是当前评分计数回归；建议把本门诚实改名为上限内恢复 smoke，或另加明确的 legacy/纵深测试。

[LOW] [docs/learning-events-schema-v1.md:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/docs/learning-events-schema-v1.md:112) — “首次 append 前/账本零行”只对空账本成立。[SKILL.md:2739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2739) 的 LF 守卫早于 `:2755` 自检；预置 `b"{"` 后提交超深记录，实测 `rc=1`、节点不变、无事件行，但账本变为 `b"{\n"`。建议改写为“不得追加该事件记录”，或把自检移至 LF 守卫前。

关键复核：

- 当前 SKILL 相对 `5a967446` 实际无 diff；直接 import 和首写自检已存在于基线。普通路径在 [SKILL.md:2755](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2755) 校验，`:2771` 才打开 `O_APPEND`，超限事件行不会由该路径写入。
- 删除临时 fixture 中的 validator 链接后，写点实测 `rc=1`、stderr 为 `No module named 'validate_learning_events'`、账本不存在、节点/账本写面不变。该 import 失败是安全的 fail-closed，没有降级放行。
- 超限记录仍可由绕过此 SKILL 的其他程序、手工或外部并发追加进入文件；校验器不是文件系统写入钩子，只会事后报违规。
- 真实生产 PYEOF 在临时 vault 产出的正常记录：`626 bytes`、最大深度 `2`、节点 `37`，余量为 62 层和 199,963 节点，没有现实误拒迹象。
- 七门承重结论：深度超限、节点超限、validator 独立深度、锚方向回落四项能杀对应防线删除；上限内门不锁精确边界；自引用门和六格门不承重。
- 独立 CLI：depth 2/nodes 37 为 `rc=0`；depth 65 为 `rc=1`；nodes 200001 为 `rc=1`。四个回归文件当前稳定快照实测为 `322 passed, 1 skipped`，不是整仓 CI。


