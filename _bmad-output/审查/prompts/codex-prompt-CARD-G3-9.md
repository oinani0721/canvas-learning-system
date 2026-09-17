# CARD-G3-9 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-A / round-1）

## 一 背景 与 最小读取面（只读这些，不要全仓扫）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
审查绑定 SHA：`30b23c4d`（基线 `08100483`）

本卡新增一个**三面机器对账脚本**：把同一份 `<vault>/outputs/今日复习.json` 派生出的
三个消费面放在一起逐项比对，验「卡片数 / 板集 / 板级到期数 / 排序」逐项相同。三面是：

1. **picker** = `scripts/daily_review_pick.py` 产出的 `今日复习.json`（schema v3）
2. **Dashboard** = `canvas-vault/Dashboard.md` 的 DataviewJS 归约块（在脚本里用 Python 重算）
3. **overview** = `GET /api/v1/review/overview`（`backend/app/api/v1/endpoints/review_overview.py`）

请只读下列内容：

- `git diff 08100483 30b23c4d -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
- `backend/scripts/g39_three_view_reconcile.py`（新增，全文）
- `backend/tests/regression/test_g39_three_view_reconcile.py`（新增，全文）
- `scripts/daily_review_pick.py` 的 `:1037-1145`（due_rows 与 payload 构建）与 `:1311-1320`（state 读侧）
- `canvas-vault/Dashboard.md` 的 `:52-90`（被镜像的归约块）
- `backend/app/api/v1/endpoints/review_overview.py` 的 `:159-330`（`_due_ts` / `_gate_due_groups` /
  `_gate_boards_rollup`）与 `:894-1000`（`board_rows` / `_summarize` 返回 / `_node_rows`）与
  `:1029-1170`（`_vault_entry` 尾段 / `_collect` / `/overview` 路由）—— **只读参照，本卡禁改这两个端点文件**

## 二 作者自述（请独立核对，不要采信）

1. **三面对账项定义**：到期卡片数（picker `stats.due_nodes` / picker `len(due_nodes)` /
   Dashboard 重算值 / overview `due_count`）；板集与板级到期数（picker `boards` rollup 的 due /
   picker `due_nodes` 按 board 分组 / overview `boards[].due`）；排序（picker `top_boards` 板序 ≡
   overview 板序前缀；板内节点身份集合；overview 板内行序 ≡ 独立复算的紧迫度序）。
2. **Dashboard 重算逐字镜像 md**：镜像范围 `Dashboard.md:57-83`，含 `:65` 的四条结构校验、
   `:68` 的 `dueCnt` 三元、`:73` 的 placeholder 取法、**以及 `:74` 的 `|| (proj.stats?.ineligible ?? 0)`
   回退**。结构校验不过时脚本记 `not-comparable` 且**计入** `semantic_diff`，不记 0。
   另声明：`_is_js_number` 用 `type(v) is int or type(v) is float` 而非 `isinstance`，
   因为 Python 的 `bool` 是 `int` 子类、JS 的 `typeof true` 是 `"boolean"`，两者方向相反。
3. **负控红在指定差异行**：测试里三段负控各只改一面一项，断言点名 `(pair, field)` 二元组，
   不接受「有任意失败」。另有一份变异对照脚本 `_bmad-output/审查/evidence-g39/g39_mutation_negctl.py`，
   逐条抽掉脚本里的判据并要求**被点名的那条测试**变红，实测 6/6 变红、脚本还原后 shasum 逐字节相同。
4. **`known_scope_note` 与 `semantic_diff` 的分类边界**：`SCOPE_NOTE_CODES` 是**闭集白名单**
   （N1 Dashboard 全板 vs picker 有成员板 / N2 扫描序 vs 紧迫度序 / N3 连不上 / N4 旧投影无 boards 键），
   `_note()` 对白名单外的 code 直接 assert 失败；其余一切默认进 `semantic_diff`。
   **`not-fetched` 只给「连不上」**：连上但 entry 是 corrupt / 非 2xx / 响应非 JSON / 响应里没有本
   vault 的 entry，一律计入 `semantic_diff`。
5. **脚本零库连接**：只用标准库（argparse/json/sys/urllib/pathlib/typing），不导入后端应用包，
   不连任何数据库，不启动后端进程；唯一写口是 `--out`。测试里有 AST 级允许清单用例把这条钉死。
6. **按甲支读数（本批裁定 R-B14-12）**：对 `/overview` 的取数先按 `vault_id` 定位 entry 再取字段，
   不做跨 vault 合并。

## 三 请按重要性排序回答的问题

1. 脚本是否存在把**真缺陷**误分类进 `known_scope_note` 的**未被拦下的输入**？特别是
   N1/N2/N4 三类口径差的边界——有没有哪种真实的投影形态会落进这三个 note 而本应算差异？
2. 板级到期数对账是否**真的三源独立**？`_gate_boards_rollup` 在网关内部已断言
   「rollup ≡ group-by 派生」，那么 overview 成功返回时这一子项在它那侧是否恒真？
   脚本用 `independence` 字段标注了 `cross-source` / `structurally-guaranteed`，
   这个标注有没有标错的地方（把恒真的标成了跨源，或反过来）？
3. 排序对账是否覆盖了**稳定性**（同键 tie-break）？`urgency_sorted_nodes` 的三元组键
   `(fsrs_due == "", fsrs_due, node)` 与 `_node_rows` 的实际实现是否逐位同语义？
   同 `fsrs_due` 同 `node` 的情形、以及 `fsrs_due` 非字符串的情形，两侧会不会给出不同结果？
4. live GET 连不上时降级为两面对账，有没有悄悄把「后端缺陷」变成「对账通过」？
   `compared_views` / 终端与报告里的提示是否足以让读者不把 `rc=0` 读成「总览页已验」？
5. 甲支（vault 维度）取数是否在脚本里真正落实？`select_vault_entry` 会不会在某些响应形态下
   退化成「取第一条」或「合并各 vault」（即乙支扁平读法）？

补充：若发现本卡镜像 `Dashboard.md` 或复算紧迫度序时与真实实现有**语义分叉**，请点名具体行号与
分叉后的可观察后果（哪个界面会显示什么不同的数字或顺序）。

## 四 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句话说明**如何观察到它**
（给出具体输入形态与预期的错误结论即可）。没有问题的维度请明确写「未发现」。

## 五 边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库、不要启动后端进程。
- **不评** `review_overview.py` / `review_app.py` **本体**的设计（那是另一张卡的地盘，本卡只读其输出）。
- 不评 mini-UAT 的用户主观项（那是用户 hands-on 环节）。
- `canvas-vault/**` 是线上 vault，只读。
