# 独立审查请求 — CARD-EXPECT-LOC-NARROW（BATCH-2026-09-11-第十四批 / 车道 card-t8-tools）

## ① 背景与最小读取面

用户裁定 **D-28** 把「给变异 harness 逐条补 `expect_loc`（断言源位置身份）」的范围收窄：
上一张卡只做 `g32b_mutation_gates.py` 的 138 条，**本卡**补剩下三套 ——
`g32cb_mutation_gates.py`(9 条) / `g32ccr1_negative_controls.py`(11 条) / `g33_mutation_gates.py`(18 条)。

要闭合的缺口（登记名 **Y1-B HIGH-1**）：共用裁决函数 `kill_identity()` 的第 3 条判据
`require_gate_file=True` 只要求「有**某条**失败落在**门文件**里」。而门函数里通常既有
**前提断言**（例如 `assert _race_fired(vault), f"竞态注入没有触发…{out}{err}"` —— 消息里
**原样内嵌**被测子进程的 STDOUT/STDERR），又有**目标断言**（这条变异本该打红的那一条）。
子进程运行期拼出的文本里只要含目标断言的 `expect_msg` 片段，消息维与弱位置维**同时**被满足，
而目标断言根本没执行 ⇒ 判成 `KILLED`。两条断言同在一个文件里，文件级位置分不开它们。
`kill_identity()` 已经支持 `expect_loc`（`stmt:<12 位十六进制>` 指纹，绑到**那一条语句**），
三套此前**一处都没传**（按 D-28 延期）。本卡补齐。

**最小读取面（请只读这些，不要展开到全仓）**：

1. 本卡 diff：`git diff 796f6490ba951a1826e2c28e97037ab47d71f4b8 0e6d82c00fad046a434461fa1a102617bd2d03c7 -- . ':(exclude)_bmad-output'`
   （恰三个文件：`backend/scripts/g32cb_mutation_gates.py` / `g32ccr1_negative_controls.py` / `g33_mutation_gates.py`）
2. `backend/scripts/mutation_kill_identity.py` 的三个函数（**只读，本卡不改它**，用来核口径）：
   `kill_identity` / `_loc_identity` / `check_expect_loc_unique`
3. `backend/scripts/g32b_mutation_gates.py` 的范式段（**只读，本卡不改它**）：
   `EXPECT_LOC` / `EXPECT_LOC_HELPER` / `EXPECT_LOC_EXEMPT` / `_check_expect_loc` / `--list` 块
4. 两个门文件的相关断言段（**只读，本卡不改它们**，也不评断言本身写得对不对）：
   `backend/tests/regression/test_g3_2_review_ledger.py`、`backend/tests/regression/test_g3_3_cas.py`
5. 本卡存档目录 `_bmad-output/审查/evidence-expect-loc-narrow/`：
   - 对照输入驱动 `negctl_expect_loc_driver.py` 与它的成对输出 `negctl-before-*.txt` / `negctl-after-*.txt`
   - 三套覆盖自检前后对照 `list-before-*.txt` / `list-after-*.txt`（g33 走本卡新增的 `--selfcheck-loc`）
   - 指纹探针 `probe-*.txt`、抽样/全量裁决 `only-*.txt`、目录级 `unit-close-*.txt`

## ② 作者自述（请独立核对，不要采信）

- 三套各新增：`EXPECT_LOC` 表 + `EXPECT_LOC_HELPER` 登记表 + `EXPECT_LOC_EXEMPT` 豁免表 +
  `_check_expect_loc()` 自检 + 覆盖自检入口（g32cb/g32ccr1 并进既有 `--list`；g33 没有 `--list`，
  新增同层早退的 `--selfcheck-loc`）+ `--probe` 观察入口（不判定、rc 恒 4）；
  g33 另加 `--skip <完整 mid>`（**精确**匹配）以排除触及零写者文件的那一条。
- **每个 `stmt:` 指纹都由 `--probe` 实测取得**，不是推算行号、不是手抄。
  逐套计数：g32cb 绑 **9** / 位置豁免 **0** / 共享 helper **0**；g32ccr1 绑 **11** / 豁免 **0** / helper **0**；
  g33 绑 **17** / 豁免 **1**（`M5-cas-revision-only`，零写者禁真跑）/ helper **0**。
  三套全部 `stmt:` 指纹所在**作用域**都等于各自变异点名的那道门函数（0 条落共享 helper）。
- `check_expect_loc_unique()` 自检干净（`--list` / `--selfcheck-loc` 的 rc=0 为证）。
- 落在门文件之外、或本批禁真跑取不到指纹的条目 ⇒ `EXPECT_LOC` 留空 + 进 `EXPECT_LOC_EXEMPT` 写理由。
- 对照输入成对：同一份合成 `out`，`expect_loc=None` ⇒ `KILLED`（改前口径的误判）；
  `expect_loc=<表里那个值>` ⇒ 非 `KILLED`（位置身份挡住了）。三套各一对，实测都是
  `KILLED` → `SURVIVED`「位置不符」。`after` 那一跑的 `expect_loc` 是 `import` harness 后
  **读它的 `EXPECT_LOC[<mid>]`**，不是驱动现算的。
- 三套 `require_gate_file` **全部条目一律保持 `True`**，⛔ 没有照抄 g32b 的
  `require_gate_file=tag not in EXPECT_LOC_EXEMPT`。
- 改后文案与证据等宽：豁免条目仍写作「**仅消息维**、位置只绑到门文件一级」，
  没有写「全部绑到具体断言」，也没有写「⇒ KILLED-UNBOUND」。

## ③ 请按重要性排序回答的问题

0. **对照输入是否真反映 Y1-B HIGH-1**：合成的 `out` 里，位置行是否确实落在**门文件内的前提断言**上、
   而 reason 里含的是**目标断言**的 `expect_msg`？有没有哪条**未被拦下的输入**形态是这份对照没覆盖的？
1. 某条 `expect_loc` 指纹是否可能在门文件里命中**两条同形语句**（身份不可唯一归属）？
   自检里那道「恰好命中 1 条」是否真的会在这种情况下红？
2. 三套是否**都**保持了 `require_gate_file=True`？有没有哪一处照抄了 g32b 的
   `tag not in EXPECT_LOC_EXEMPT`？（本三套 `expect_msg` 覆盖率 100%，那样写会把该条从
   「弱位置 AND 消息」整块降成「只消息」。）
3. 进 `EXPECT_LOC_EXEMPT` 的条目是否**本可绑**却被放进豁免表？
4. 改后文案（汇总打印、表头注释、覆盖行）是否仍**比证据宽**？
5. g33 没有模块级 `EXPECT_MSG`（`expect_msg` 内联在 `MUTATIONS` 第 7 字段），
   新增的 `EXPECT_LOC` 键是否与 `MUTATIONS` 第 1 字段一一对齐、没有错位？
6. 三套源码与本卡验收单里是否还有残留的「⇒ KILLED-UNBOUND」措辞？（本三套取不到那一档。）
7. g33 的 `M5-cas-revision-only` 进位置豁免的理由写得是否与证据等宽？
   其余 17 条是否**都**真跑取了指纹，而不是搭车进豁免表？
8. g33 新增的 `--skip`：四处同步（循环过滤 / `_selected` 分母 / `--json` 的 `partial` / 「rc 恒 4」分支）
   有没有漏？精确匹配是否真的不会退化成前缀匹配？
9. `--probe` 三套都跳过了跑前的 `_check_expect_loc()`（理由：probe 就是为了把表填出来才跑的）。
   这个跳过有没有**别的**后果 —— 例如让某条已经漂掉的锚在 probe 这一路上静默通过？
10. `_check_expect_loc()` 里那道「指纹所在作用域 = 该条变异点名的门函数」的核，
    在 g33 上用的是 `BACKEND / TESTS` 这个**固定**门文件，而 `check_expect_loc_unique()` 收的是
    **逐条**从 `nodeid` 推出来的门文件路径。今天 18 条 nodeid 全在 `TESTS` 里所以两者相同 ——
    这个隐含前提值不值得显式核出来？（作者已把它登记为移交项，请判断严重度。）

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句**对照思路**
（在什么输入下这条判据会给出与事实不符的结论）。没有问题的维度请明确写「未发现」。

## ⑤ 边界

- **只读**：不要运行任何门、不要跑 pytest、不要连数据库。
- 跑完裁判**之后**作者只做过**纯注释**编辑（给两处表头补事实说明）；等价性由
  `evidence-expect-loc-narrow/ast_equal_after_comment_edit.py` 的 `ast.dump` 逐字符比对证明
  （存档 `ast-equal-*.txt`）。请核那份证明，而不是按「存档比代码旧」直接判失效。
- 不评门文件里那些断言**本身**写得对不对（门文件不在本卡地盘，本卡只读取它们算指纹）。
- 主 session 裁定（**不是本卡的疏漏，请不要当成问题报**）：
  - `g33` 的 `M5-cas-revision-only` 按裁定 **R-B14-9 (1)** 排除不跑
    （它是 18 条里唯一变异 `canvas-vault/.claude/scripts/fsrs_bridge.py` 的条目，该文件是本批点名的零写者）；
    其余 17 条按 **R-B14-9 (2)** 放行真跑。
  - `g33` 的 `restore_all()` 对 `_TARGET_FILES` **全量** `write_bytes`，所以任何一次 g33 真跑都会对车道树那份
    `fsrs_bridge.py` 做一次**等字节重写**；裁定明确「等字节 restore 不算碰零写者」，
    承重判据是**跑前跑后 `shasum -a 256` 逐字相同**，存档在 `probe-g33-*.txt` / `only-g33-*.txt` 首尾。
    请不要把「M5 无指纹」或「fsrs_bridge.py 被 restore_all 重写」当成卡的疏漏。
  - 排除 M5 走的是「在本卡地盘内给 g33 加精确匹配的 `--skip`」这一形态（裁定 R-B14-9 (1)「`--only` 排除或跳过」
    二选一），请核它的判据，而不是评「为何不 import 复用 g33 的内部函数」
    （实测 g33 的施加/跑门/还原循环内联在 `main()` 里，没有可复用的模块级函数）。
  - 给三套补 `--json` / `verdict_counts` 属**第十五批另立卡**，请不要评本卡缺它。
- 措辞：请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法描述问题。
