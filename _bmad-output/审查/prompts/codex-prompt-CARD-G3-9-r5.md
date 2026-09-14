# CARD-G3-9 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-A / round-5 · 末轮）

## 一 背景 与 最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
审查绑定 SHA：`a2b93980`（基线 `08100483`）
前四轮：r1 `30b23c4d`（9 条）/ r2 `b2f962d9`（11 条）/ r3 `0596386b`（11 条）/ r4 `72b1cabd`（8 条）——
**共 39 条全部采纳，零驳回。**

⚠️ round-4 已 BLOCKER=0 / HIGH=0 且绑当时最终 HEAD，门槛已达成；本轮是**自愿加严的末轮**
（轮次上限 5）。请重点确认 r4 那批修复没有引入新的 HIGH 级问题。

请只读：

- `git diff 72b1cabd a2b93980 -- . ':(exclude)_bmad-output'`（本轮改动）
- `backend/scripts/g39_three_view_reconcile.py`（全文）
- `backend/tests/regression/test_g39_three_view_reconcile.py`（全文）
- `canvas-vault/Dashboard.md` 的 `:52-95`
- `backend/app/api/v1/endpoints/review_overview.py` 的 `:155-340`、`:780-1015`（只读参照，本卡禁改）

## 二 round-4 八条的处置

| r4 | 修法 |
|---|---|
| #1 `Request()` 在 try 外，畸形 URL 的 ValueError 逃逸 | 移进 try |
| #2（本卡回归·崩溃）深嵌套数组触发 RecursionError | `_js_interp_throws` 改**显式栈**遍历，并带 10 万节点上限 |
| #3 rollup 行损坏的 `next_due` 归一后未报出 | `picker_rollup_due()` 补 `next_due` 类型自检 |
| #4 三处计数仍用宽松相等 | 统一走 `_same_count` |
| #5 `upcoming` 非数组被静默当空 | 键在但不是数组 ⇒ 报损坏 |
| #6 `fsrs_due` 非字符串被归一成空串 | 补 `fsrs_due` 类型自检 |
| #7 node 自检只验类型 | 补**非空**与**同板唯一性** |
| #8（本卡回归·假红）`0.0 ↔ 0` 被报成差异 | 计数比较改按 **JS 显示字符串**（`_js_str`）：`String(0.0)==="0"` 故与 `0` 一致；`String(false)==="false"` 故与 `0` 仍是差异 |

变异对照 33/33 KILLED（脚本还原后 shasum 逐字节相同）；测试 66 例全绿。

## 三 请按重要性排序回答的问题

1. **`_js_str()` 与真实 JS `String(v)` 是否逐值一致？** 特别是：大整数、负零、极大/极小浮点
   （`1e21`、`1e-7`）、`NaN`/`Infinity`（解析层已拒）、字符串本身。有没有哪对值会因此被误判
   成一致（假绿）或不一致（假红）？
2. **显式栈版 `_js_interp_throws` 与递归版是否等价？** 10 万节点上限在什么输入下会触发，
   触发时返回 True（判为抛）是否是**安全**方向？有没有合法投影会命中它？
3. **新增的四条 picker 自检（#3/#5/#6/#7）有没有误报？** 合法投影里 `next_due` / `upcoming` /
   `fsrs_due` / `node` 的全部合法形态是否都不会被这些自检打红？
4. **`known_scope_note` 白名单（N1–N5）现在闭合了吗？**
5. **本轮改动有没有引入新的 BLOCKER / HIGH？**

## 四 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句话说明**如何观察到它**。
没有问题的维度请明确写「未发现」。

## 五 边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库、不要启动后端进程。
- **不评** `review_overview.py` / `review_app.py` **本体**的设计。
- 不评 mini-UAT 的用户主观项。
- `canvas-vault/**` 是线上 vault，只读。
