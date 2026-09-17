# CARD-G3-9 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-A / round-3）

## 一 背景 与 最小读取面（只读这些，不要全仓扫）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
审查绑定 SHA：`0596386b`（基线 `08100483`；r1 绑 `30b23c4d`，r2 绑 `b2f962d9`）

**round-2 的十一条已全部采纳并修复，零驳回**（r1 九条亦然）。本轮请复核修复是否正确、
有没有引入新缺口，并继续找未被拦下的输入。

请只读：

- `git diff 08100483 0596386b -- . ':(exclude)_bmad-output'`
- `backend/scripts/g39_three_view_reconcile.py`（全文）
- `backend/tests/regression/test_g39_three_view_reconcile.py`（全文）
- `scripts/daily_review_pick.py` 的 `:1037-1145`、`:1311-1320`
- `canvas-vault/Dashboard.md` 的 `:52-95`
- `backend/app/api/v1/endpoints/review_overview.py` 的 `:155-340`、`:780-1015`、`:1029-1175`
  （**只读参照，本卡禁改这两个端点文件**）

## 二 round-2 十一条的处置（请独立核对修复是否真的成立）

| r2 | 修法 | 回归钉 |
|---|---|---|
| HIGH-1 响应头阶段失败仍被豁免 | 新增 `_is_connection_failure()`：**只有能证明连接没建立**的三类（连接被拒 / 主机网络不可达 errno / DNS 解析失败）才走 N3；超时、连接重置、未知 scheme 一律 fail-closed 进 `__open_error__` → 差异 | `test_r2_high1_headerless_hang_is_not_exempted` + 反面 `..._connection_refused_still_exempted` |
| HIGH-2 前缀之后的板序漏查 | 新增 `expected_board_order()` 复算**整张板表**顺序（到期板按 `(prio, -due, board)`；零到期板按来源分两支：rollup 在场取 `due==0` 板、键 `(earliest is None, earliest or "", board)`；rollup 缺席取 `upcoming`、键 `(earliest, board)`），逐位比 | `test_r2_high2_order_after_prefix_is_checked` |
| HIGH-3 overview 重复板行被字典覆盖 | 入表前先查板行唯一性 | `test_r2_high3_duplicate_overview_board_row_is_a_diff` |
| MEDIUM-4 N4 接纳非历史形态 | `buckets` 在场而 `boards` 缺席 ⇒ 差异，不记 N4 | `test_r2_medium4_buckets_without_boards_is_not_legacy` |
| MEDIUM-5 合法旧投影零到期板误报 | 板集在 rollup 缺席时改用 `upcoming` | `test_r2_medium5_legacy_upcoming_zero_board_is_not_a_false_diff` |
| MEDIUM-6 rollup `due` 无类型门禁 | `_strict_count()` 只收真 `int`（bool/float 均拒） | `test_r2_medium6_rollup_due_type_is_strict` |
| MEDIUM-7 Dashboard 插值异常未镜像 | `_js_interp_throws()`：带 `toString` 键的对象 ⇒ 模板插值抛错 ⇒ 该面 `not-comparable`；作用于 `generated_at` 与 `stats.unassigned` | `test_r2_medium7_generated_at_throwing_value_degrades_dashboard` |
| MEDIUM-8 离线入口解析异常逃逸 | `--overview-json` 的读取/解析包进 try，归 `__json_error__` | `test_r2_medium8_offline_overview_parse_error_is_classified` |
| MEDIUM-9 不可哈希节点打断对账 | 板内先查 `node` 是否字符串，非字符串报输入损坏并跳过该板 | `test_r2_medium9_unhashable_node_does_not_abort_reconcile` |
| MEDIUM-10 节点排序独立性标错 | `node_identity` / `node_order` 均改标 `reimplementation` | `test_r2_medium10_node_order_labelled_reimplementation` |
| LOW-11 未尝试连接也进 N3 | 新增 N5 `overview_not_requested`，与 N3「试过但连不上」分开 | `test_r2_low11_not_requested_is_distinct_from_not_fetched` |

## 三 请按重要性排序回答的问题

1. **`_is_connection_failure()` 的分类是否正确且完备？** 有没有哪种**已连接**的失败仍会被判成
   连接失败（假豁免）？反过来，有没有哪种**真的没连上**的常见情形被 fail-closed 成差异
   （假红，会把「后端没起」报成缺陷）？errno 白名单在 macOS / Linux 上是否都对？
2. **`expected_board_order()` 与参照实现（`:911` + `:918-941`）是否逐位同语义？**
   特别是：零到期板两支来源的排序键、`earliest` 的取法（rollup 支 `next_due or None` vs
   upcoming 支原值）、以及「已在到期板里的板要排除」这条在两支里是否都落实了。
3. **`_js_interp_throws()` 的判定是否既不漏也不多？** JSON 解出来的哪些值会让
   `` `${v}` `` 抛、哪些不会？只覆盖 `generated_at` 与 `stats.unassigned` 两个字段够不够
   （`Dashboard.md:76-83` 还插值了哪些值）？
4. **`known_scope_note` 白名单（N1–N5）现在闭合了吗？** 有没有真缺陷仍能落进某个 note？
5. **新引入的路径有没有制造新的假绿？** 尤其 `_strict_count()` 返回 None 后的下游处理、
   `zero_source` 的缺省取值、以及 `node` 非字符串时 `continue` 掉整块板会不会吞掉该板的
   其他差异。

## 四 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句话说明**如何观察到它**。
没有问题的维度请明确写「未发现」。

## 五 边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库、不要启动后端进程。
- **不评** `review_overview.py` / `review_app.py` **本体**的设计。
- 不评 mini-UAT 的用户主观项。
- `canvas-vault/**` 是线上 vault，只读。
