# CARD-G3-9 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-A / round-2）

## 一 背景 与 最小读取面（只读这些，不要全仓扫）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
审查绑定 SHA：`b2f962d9`（基线 `08100483`；round-1 绑定 `30b23c4d`）

**round-1 的九条已全部采纳并修复**（无驳回）。本轮请复核修复本身是否正确、是否引入新问题，
并继续找未被拦下的输入。

请只读下列内容：

- `git diff 08100483 b2f962d9 -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
- `backend/scripts/g39_three_view_reconcile.py`（全文）
- `backend/tests/regression/test_g39_three_view_reconcile.py`（全文）
- `scripts/daily_review_pick.py` 的 `:1037-1145`、`:1311-1320`
- `canvas-vault/Dashboard.md` 的 `:52-95`
- `backend/app/api/v1/endpoints/review_overview.py` 的 `:159-340`、`:860-1015`（⚠️ **本轮请务必读到
  `:1015`** —— round-1 说授权片段在 `:1000` 截断、没看到 `_node_rows` 的完整排序键；该键在
  `:1007-1008`）、`:1029-1175`。**只读参照，本卡禁改这两个端点文件。**

## 二 round-1 九条的处置（请逐条独立核对修复是否真的成立）

| r1 | 结论 | 修法 | 回归钉 |
|---|---|---|---|
| HIGH-1 零到期板未进板集 | 采纳 | 新增 `picker_rollup_boards()` 取**完整板行**（含 `due=0`）；板集对账用 `set(group_due) \| set(rollup_rows)` | `test_r1_high1_zero_due_board_missing_from_overview_is_a_diff` |
| HIGH-2 板序比子序列 | 采纳 | 改为**前缀**比较 `ov_order[:len(top_names)] == top_names` | `test_r1_high2_board_order_is_prefix_not_subsequence` |
| HIGH-3 NaN 解析分叉 | 采纳 | picker 与 overview 的 `json.loads` 均加 `parse_constant=_reject_js_nonstandard`，与 JS `JSON.parse` 同严格度 | `test_r1_high3_nan_is_rejected_like_js_json_parse` |
| HIGH-4 连上后读取失败被豁免 | 采纳 | 连接阶段与读取阶段**分开捕获**；已连接后的任何失败返回 `__read_error__`，不进 not-fetched | `test_r1_high4_read_failure_after_connect_is_not_exempted` |
| MEDIUM-5 N4 混淆缺键与损坏 | 采纳 | `picker_rollup_due()` 改返回 `(值, 损坏原因)`；缺键 → N4，键在但类型损坏 → 差异 | `test_r1_medium5_*`（正反两例） |
| MEDIUM-6 独立性标错 | 采纳 | 新增第三档 `reimplementation`（同一契约的两个独立实现，能抓实现漂移但**不是**第三个独立源），overview 板级 due 对账改标此档 | `test_r1_medium6_overview_groupby_is_labelled_reimplementation` |
| MEDIUM-7 逐行异常未镜像 | 采纳 | `due_nodes` 含 `null` 行 ⇒ Dashboard 面记 `not-comparable`（镜像 `:70-72` 抛错 → `:87`） | `test_r1_medium7_null_row_makes_dashboard_not_comparable` |
| MEDIUM-8 非法 UTF-8 逃逸 | 采纳 | 读取阶段统一捕获，`UnicodeDecodeError` 归入 `__read_error__` | `test_r1_medium8_invalid_utf8_body_is_classified_not_crash` |
| LOW-9 重复 vault_id 取首条 | 采纳 | 收集全部命中；`len(hits) > 1` ⇒ 差异 | `test_r1_low9_duplicate_vault_entries_is_a_diff` |

**另有一条本卡自查出的缺陷（round-1 未覆盖，一并说明）**：`fetch_overview` 原先走
`urllib.request.urlopen`，会被**系统代理**接管。本机实测代理设在 `127.0.0.1` 上，后端没起时
代理自己回 503 ⇒ 脚本读成「连上了但后端答 503」而非「连不上」，唯一的豁免口永远走不到，
「后端没运行」被报成「总览页有缺陷」。现改为 `build_opener(ProxyHandler({}))` 直连。
回归钉 `test_fetch_overview_opener_bypasses_system_proxy`（含同函数内验伪锚：同样环境下默认
opener 必须带 ProxyHandler，证明该判据分得清两者）。

## 三 请按重要性排序回答的问题

1. **修复是否引入新的未被拦下的输入？** 特别是：
   - `picker_rollup_boards()` 与 `picker_rollup_due()` 现在是两条独立扫描，形状判定不一致处会怎样？
   - 板集对账里 `group_due.get(b, 0 if (rollup_rows and b in rollup_rows) else "(picker 明细无此板)")`
     这个缺省取法，在「rollup 说某板 due=2 但明细无此板」时给出的是哪一侧的值、会不会掩盖差异？
2. **前缀比较是否在所有形态下成立？** `board_rows` 只含有到期节点的板、零到期板由 `rollup_zero`
   追加在后 —— 当某个 `top_boards` 成员因故不在 `groups` 里时，前缀比较给出的结论是否仍正确？
3. **`urgency_sorted_nodes` 与 `_node_rows`（`:1007-1008`）的排序键是否逐位同语义？**
   请务必读到 `:1015`。同 `fsrs_due` 同 `node`、`fsrs_due` 非字符串、`node` 非字符串三种情形下，
   两侧会不会给出不同结果？
4. **`known_scope_note` 白名单（N1–N4）是否仍闭合？** 修复后有没有哪种真实投影形态落进 note
   而本应算差异？
5. **`not-fetched` 豁免口现在是否**恰好**只剩「连接阶段失败」一种？** 有没有别的路径能到达它？

## 四 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句话说明**如何观察到它**
（具体输入形态与预期的错误结论）。没有问题的维度请明确写「未发现」。

## 五 边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库、不要启动后端进程。
- **不评** `review_overview.py` / `review_app.py` **本体**的设计（另一张卡的地盘，本卡只读其输出）。
- 不评 mini-UAT 的用户主观项。
- `canvas-vault/**` 是线上 vault，只读。
