# 独立复核请求 — CARD-W4-4b7-TAIL **round-5**（末轮：拒绝面扩到一切延迟执行体 + 清残留文案）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。前四轮审 `45b8e0b4` / `a307de45` / `c118e33e` / `485a1f89`，
**本轮审查 SHA `6e4fedc5`**。前提 commit `46e7bf77`。本卡按 D-15 最多 5 轮，**这是末轮**。

**请只读这几处**：

1. `git --no-pager diff --no-color 485a1f89 6e4fedc5 -- . ':(exclude)_bmad-output'`（**本轮全部代码改动**，单文件）
2. `backend/tests/unit/test_live_port_guard_contract.py` 改后实测范围：
   - `_indirect_self_method_calls` `:1082-1187`（本轮未改）
   - `_is_always_taken_branch` `:1203-1210`、`_reachable_prefix` `:1217-1229`
   - **`_live_called_names` `:1232-1320`**（docstring 清残留 + 语义陈述更正）
   - **`_refuse_to_guess_on_deferred_execution` `:1323-1378`**（原 `_refuse_to_guess_on_local_functions`，拒绝面扩大）
   - 顺序门 `:1813-1844` 与 `:1846-1886`
3. `backend/tests/support/live_port_guard.py` 的 `_publish_ledger`（**本轮未改**，round-4 已核对通过）
4. 跑器 `_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh` 全文（本轮只改 `need_value` 拒空串）
5. 本轮判据存档（`_bmad-output/审查/evidence-w44b7-tail/`）：
   **`codex-all-rounds-repro-verify-r5-20260914T214830.txt`**（四轮共 **18 个**复现输入
   + 2 条干净形态 + **3 条已登记漏面照实打印为「绿」**+ 真实 `install()` 回归）、
   `r5-precheck-20260914T214842.txt`、
   `whitelist-negctl-r5-20260914T214915.txt`、`seam-negctl-r5-20260914T214915.txt`、
   `order-negctl-r5-20260914T214915.txt`
6. 前四轮存档（对照）：`codex-review-CARD-W4-4b7-TAIL-r1.md` … `-r4.md`

## 二 本轮整改自述（请独立核对，不要采信）

**MEDIUM-1（lambda 等绕开 `def` 断言）已改**：`_local_func_defs` 只收 `def`，你的两个 `lambda`
反例因此放行。现在改名 `_refuse_to_guess_on_deferred_execution`，拒绝面 = 本作用域里一切
「写在这里、执行在别处」的体：`FunctionDef` / `AsyncFunctionDef` / `Lambda` / `ClassDef` /
`ListComp` / `SetComp` / `DictComp` / `GeneratorExp`。你 round-4 表格里前 6 行（两个 lambda、
生成器表达式、空列表推导式、`type()` 动态绑定里的 class 体、class 内绑模块函数、class 内显式
`def`）实测**全部翻红**。

**⛔ 能力边界写进 docstring 而不是靠默认**：这条前置条件封的是「本作用域内**可见**的延迟执行体」，
**不是**「顺序判断从此可靠」。AST 看不穿一次**调用**背后的函数体，所以这五类如实登记为
**门未覆盖的路径**：调用模块级 helper 而它体内做提前预检、`functools.partial(...)()`、
`exec`/`eval` 字符串、`type("X", (), {...})()`、把模块级函数直接绑成类属性。
总验证脚本把其中三条**照实打印为「绿」**（不藏），存档可见。

**LOW-1（残留文案）已改**：上一轮删了机制却漏删了描述它的整段 —— docstring 仍在要求传
`local_funcs`、讲调用点展开与递归在途集合，注释还引用已删的 `expand_call`。全部清除
（`grep -c 'local_funcs\|expand_call\|在途集合'` → **0**）。并更正你指出的两处不准确：
① 「只数定义点之外的调用」→ 改成「不带装饰器时函数体不计入；带装饰器时**保守计入**
（装饰器**可能**当场调用它，也可能像 `identity` 那样根本不调 —— 计入是偏红那一侧的选择，
不是『定义时确实执行』的断言）；装饰器表达式本身与默认参数里的调用一律计入」；
② 「挪到模块级函数里顺序门就数得对」—— **已删并明确写成被证伪**，模块级 helper 正是反例
（`grep -c '模块级的调用关系顺序门本来就数得对'` → **0**）。
顺带删掉已无引用的 `_local_func_defs`（留着是死代码）。

**LOW-2（`--prereq ''`）已改**：取值拒空串。实测 `--prereq ''` → rc=2 且打印
`unknown arg: <empty>` 并说明「空 PREREQ 会让 `git show ':path'` 读 index」。

**LOW-3（伪造 summary 的文本来源边界）登记不改**：跑器读的是**它自己发起的那次** pytest 的
输出，没有可信来源通道可用；纯文本判据无法区分「真 summary」与「捕获输出里一段长得一样的
文本」。如实登记为剩余边界，不声称已封。

**未改动面**：`live_port_guard.py` 本轮**零改动**；`_indirect_self_method_calls`、seam 两门、
`guard_plugin.py`、任何 `conftest.py`、`backend/app/**` 均未改。

## 三 请回答的问题（按重要性排序）

① **扩大后的拒绝面是否还有**本作用域内可见的**延迟执行体**没覆盖到？例如：`async` 推导式、
`match` 的 guard 表达式、`global`/`nonlocal` 配合的赋值、装饰器表达式里内联的 `lambda`、
`ast.NamedExpr` 里藏的 `lambda`、类型注解里的字符串前向引用 —— 哪些会被 `ast.walk` 收到、
哪些不会？（只要它**在 AST 里可见**就应当被收到；看不见的那些属于已登记的漏面。）

② **`_live_called_names` 的 docstring 现在是否与实现逐条对得上？** 请特别核「带装饰器时保守
计入」「装饰器表达式与默认参数一律计入」这两句与 `:1232-1320` 的实现是否一致，以及四类剪枝
的描述有没有残留上一轮的说法。

③ **两个顺序门的 claim 是否已经收窄到它真能证明的范围？** docstring 现在说它证明的是
`install()` **字面语句序列**里那几个**直接具名调用**的先后，行为面的证明在子进程探针。
这个 claim 与实现是否相符、还有没有说过头的地方？

④ **跑器 `need_value` 的空串拒绝是否对三个 flag 都生效**、有没有引入新的合法取值被误拒
（例如 `--prereq` 传一个合法但以数字开头的短 SHA）？

⑤ **是否有回归**：`_indirect_self_method_calls`、seam 两门、前三类剪枝、`_reachable_prefix`
下标语义、源码导出白名单与相等漂移钉、`_publish_ledger` 纯 docstring 性质 —— 本轮是否仍成立。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评被守逻辑本身**：`live_port_guard.py` 的结账 / 发布 / 退出语义不是本卡的面。
- **不做全称封闭证明**：作者已明说识别面有限并逐条列出漏面；请**列举**剩余漏面而不是要求穷尽。
