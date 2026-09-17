# 独立复核请求 — CARD-W4-4b7-TAIL **round-4**（顺序门改为「遇局部函数即拒绝判定」后的复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。round-1 审 `45b8e0b4`、round-2 审 `a307de45`、round-3 审 `c118e33e`，
**本轮审查 SHA `485a1f89`**。前提 commit `46e7bf77`。

**请只读这几处**：

1. `git --no-pager diff --no-color c118e33e 485a1f89 -- . ':(exclude)_bmad-output'`（**本轮全部代码改动**）
2. `backend/tests/unit/test_live_port_guard_contract.py` 改后实测范围：
   - `_indirect_self_method_calls` `:1082-1187`（本轮未改）
   - `_is_always_taken_branch` `:1203-1210`、`_reachable_prefix` `:1217-1229`
   - **`_live_called_names` `:1232-1344`**（去掉 `local_funcs` 参数与调用点展开）
   - **`_refuse_to_guess_on_local_functions` `:1347-1376`**（新增：顺序类判据的前置条件断言）
   - `_local_func_defs` `:1379-1397`
   - 顺序门 `:1832-1863` 与 `:1865-1905`（先跑前置断言，再算下标）
3. `backend/tests/support/live_port_guard.py` 的 **`_publish_ledger` `:1408-1474`**（仍只动 docstring）
4. 跑器 `_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh` 全文
5. 本轮判据存档（`_bmad-output/审查/evidence-w44b7-tail/`）：
   **`codex-all-rounds-repro-verify-20260914T213639.txt`**（把你三轮给出的 **12 个**复现输入
   + 两条「不得误红」的干净形态一起跑，含真实 `install()` 回归）、
   `r4-precheck-20260914T213650.txt`（参数纪律 7 例 / 契约套件 / docstring AST / ruff）、
   `whitelist-negctl-r4-20260914T213721.txt`、`seam-negctl-r4-20260914T213721.txt`、
   `order-negctl-r4-20260914T213721.txt`
6. 前三轮存档（对照）：`codex-review-CARD-W4-4b7-TAIL-r1.md` / `-r2.md` / `-r3.md`

## 二 本轮整改自述（请独立核对，不要采信）

**方向变了，不是第四次精化。** 你三轮分别打出：r1「跨语句丢关联」、r2「记到定义点」、
r3「同名定义全展开 / `g=helper;g()` 漏 / 局部装饰器自身漏」。共同根因是：**「谁在什么时候真的
执行了某个局部函数体」在 AST 层面判不了**，需要解析调用绑定。所以本轮让判据**拒绝判定**：

- 新增 `_refuse_to_guess_on_local_functions(scope)`：`scope` 体内只要有**任何**局部函数定义
  （`_local_func_defs` 裸 `ast.walk` 收，含嵌套、含同名多份），就 `assert` 失败并说明理由；
- 两个顺序门在算下标**之前**先调它；
- `_live_called_names` 去掉 `local_funcs` 参数与调用点展开，回到可陈述的语义：
  「只数可达语句里的调用；局部函数体不在定义点计入」，并写明该语义**只在没有跨语句调用时成立** ——
  而那个前提现在由上面的断言强制，不再靠注释。

**实测**：真实 `install()` 的 `_local_func_defs` 为 `{}` ⇒ 前置断言不触发、下标仍 `4/5/6`，
对现状零影响。你三轮的 12 个复现输入（含你保留的两条历史边界：三件事全在同一 helper、
生成器 helper 只创建不迭代）现在**一律翻红**；两条干净形态（顺序正确 ⇒ 绿 / 预检在前 ⇒ 红）都对。
方向上这是**收紧**：更多输入判红，没有任何输入因此变绿。

**跑器**：LOW-2 summary 只取**最后一个**区段（伪造标题可出现在捕获输出里，旧写法会合并多段）；
LOW-3 缺值检查移到**调用方**数实参（`need_value "$1" "${2-}"` 时被调方永远看得到第二个实参，
缺值诊断走不到，最后死在 `$2: unbound variable`）。现在裸 `--phase` 结尾 → `missing value for --phase` rc=2。

**docstring（LOW-4）**：「抛异常 ⇒ 写盘调了」已限定为 **`write_ledger` 抛出**；并补上「本函数在到达
写盘之前也可能抛（`seq` 非数时比较即 `TypeError`），那一类既没写盘也没推进序号」。

**未改动面**：`guard_plugin.py`、任何 `conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`、
`backend/app/**` 零改动；`_indirect_self_method_calls` 与 seam 两门本轮一字未改。

## 三 请回答的问题（按重要性排序）

① **「拒绝判定」这条前置断言是否真的把顺序门的假绿面清空了？** 请特别核：
(a) `_local_func_defs` 用裸 `ast.walk` 收定义，是否存在**它收不到**的「会在 `install()` 体内引入
可调用体」的构造（`lambda`、`class` 体内的方法、`exec`/`eval`、comprehension 的隐式作用域、
`functools.partial` 包住的模块级函数、`type()` 动态造类）—— 这些是否能绕开断言并让顺序门读错；
(b) 断言只加在两个顺序门上，本文件里**还有没有别的判据**在用 `_live_called_names` 或同类下标逻辑
而没加这条前置条件；
(c) 断言本身会不会在某些合法重构下变成难以接受的假红（请给出你认为合理的边界）。

② **`_live_called_names` 现在的语义陈述是否与实现一致？** 「局部函数体不在定义点计入」——
带装饰器的呢？请核实现（`:1232-1344`）与 docstring 的说法是否**逐条对得上**，有没有残留的
上一轮说法。另外：去掉 `local_funcs` 后，前三类剪枝是否仍与你前几轮「核对通过」的结论一致。

③ **跑器的两处修法是否彻底？** (a) summary「只取最后一段」的 awk 实现在「输出里根本没有 summary
标题」「有标题但区段为空」两种情形下分别得到什么，方向是假红还是假绿；
(b) 缺值检查移位后，`--gate`/`--phase`/`--prereq` 三个分支是否**都**改到了，有没有漏掉的分支。

④ **`_publish_ledger` docstring 现在是否还有说过头的地方？** 三类结果（返回 False / `write_ledger`
抛出 / 到达写盘前抛出）的划分是否与 `:1462-1474` 的实际控制流逐条对应。

⑤ **是否有回归**：`_indirect_self_method_calls`、seam 两门、前三类剪枝、`_reachable_prefix` 下标语义、
源码导出白名单与相等漂移钉、纯 docstring 性质 —— 本轮是否仍成立。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评被守逻辑本身**：`live_port_guard.py` 的结账 / 发布 / 退出语义不是本卡的面。
- **不做全称封闭证明**：请把剩余漏面**列举**出来而不是要求本卡穷尽。
