你是本次改动的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line 与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c`

本轮**只审**这一段 diff：

```
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c \
    diff 5a967446 -- \
    canvas-vault/.claude/skills/quiz-answer/SKILL.md \
    backend/tests/regression/test_g3_2_review_ledger.py \
    backend/scripts/validate_learning_events.py \
    docs/learning-events-schema-v1.md
```

范围外的文件、范围外的历史轮次结论，都不在本轮。

## 这次改了什么（一句话）

给学习事件账本加了一条**输入形状的硬上限**：任何一条记录的值，嵌套深度不得超过 64、
节点总数不得超过 20 万，超出即判违规。上限定义在校验器
`backend/scripts/validate_learning_events.py`（`MAX_VALUE_DEPTH` / `MAX_VALUE_NODES`
与 `value_shape_problems()`），由 `validate_record_full()` 在最前面执行。

设计要点：写入端在追加第一行**之前**就调用同一个 `validate_record_full()` 自检
（`SKILL.md` 直接 import 校验器本体），所以上限只定义了一份、两端天然一致。
契约文字写在 `docs/learning-events-schema-v1.md` §6.1「输入硬上限」。

配套：`backend/tests/regression/test_g3_2_review_ledger.py` 新增 7 道回归门
（超深拒 / 上限内仍放行 / 超节点数拒 / 校验器侧独立拒 / 自引用报真因 /
六格状态机三元组实测 / 写序锚方向证据缺失时回落），并把一道既有门
（`test_round17_deep_json_recovers_after_crash_window`）的用例深度从 512、900
改为上限内的值 —— 因为「深层值是合法值」这个前提被本次契约变更取消了。

## 已裁决、不在本轮讨论的事项

- A1–A6 主序条款：此前轮次已 VERIFIED，本轮不重开。
- A4.1 的并发锁：已归属 G3-3，本卡明确不实现任何锁。
- 字符轴（U+0085 / 孤立代理 / 超大整数字面量等编码问题）：归属 C 卡。
- 「开放集合边界」类意见：不计入本轮。

## 请重点回答的问题

1. **上限是否真的在首次追加之前生效**：读代码确认写入端自检的位置，并说明
   在什么情况下一条超限记录仍可能进入账本文件。
2. **两端一致性是否真的由 import 保证**：`SKILL.md` 里那次 import 的失败路径是什么？
   如果校验器不可达，写入端的行为是什么？这个降级是否安全。
3. **`value_shape_problems()` 的正确性**：它是迭代实现（不是递归）。请检查深度计
   数是否正确（尤其 dict 的键与值、空容器、元组）、节点计数是否会重复或漏计、
   以及自引用输入下是否一定终止。
4. **是否引入误拒**：真实写入路径产生的记录，其形状离 64 层 / 20 万节点有多远？
   请给出你实测的真实记录深度。
5. **新增的 7 道门是否承重**：哪几道门在你看来即使把对应实现删掉也依然会绿？
   如果有，请指出并说明它被什么别的东西喂饱了。
6. **既有门的用例改动是否掩盖了回归**：那道深层恢复门从 512/900 改成上限内的值，
   是否让原先由它覆盖的某个性质失去了守护？

## 我已经跑过的（请独立复核，不要采信）

- 四个回归文件合计：`320 passed, 1 skipped`（rc=0）。
- 校验器命令行：合法记录 rc=0；65 层记录 rc=1 报「值的嵌套深度超过上限 64」；
  200008 元素记录 rc=1 报「值的节点数超过上限 200000」。
- 变异负控 `backend/scripts/g32cb_mutation_gates.py`：逐条拆掉一道防线看指定的门
  是否变红。

## 输出格式

先给一行结论（`通过` / `需整改`），然后按 `[级别] file:line — 一句话` 列出问题，
每条附你的观测值与可执行的建议。级别用 BLOCKER / HIGH / MEDIUM / LOW。
判断标准以「会不会造成用户的一次评分被少记或多记」为最高优先级。
