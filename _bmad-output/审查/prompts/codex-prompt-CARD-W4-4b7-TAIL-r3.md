# 独立复核请求 — CARD-W4-4b7-TAIL **round-3**（按 round-2 的 MEDIUM-1/2/3 与 LOW-1~5 整改后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。round-1 审 `45b8e0b4`，round-2 审 `a307de45`，**本轮审查 SHA `c118e33e`**（整改后 HEAD）。
前提 commit `46e7bf77`。

**请只读这几处**：

1. `git --no-pager diff --no-color a307de45 c118e33e -- . ':(exclude)_bmad-output'`（**本轮整改的全部代码改动**）
2. 需要整体时：`git --no-pager diff --no-color 46e7bf77 c118e33e -- . ':(exclude)_bmad-output'`
3. `backend/tests/unit/test_live_port_guard_contract.py` 改后实测范围：
   - **`_indirect_self_method_calls` `:1082-1187`**（round-2 LOW-1 的取舍已写进 docstring）
   - `_is_always_taken_branch` `:1203-1210`、`_reachable_prefix` `:1217-1229`
   - **`_live_called_names` `:1232-1372`**（**语义重写**：定义点不贡献调用，调用点就地展开）
   - **`_local_func_defs` `:1375-1393`**（取代 round-2 的 `_reachable_local_func_names`）
   - 白名单门 `:1483-1536`、顺序门 `:1828-1859` 与 `:1861-1901`
4. `backend/tests/support/live_port_guard.py` 的 **`_publish_ledger` `:1408-1472`**（仍只动 docstring）
5. 跑器 `_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh` 全文
6. 本轮判据存档（`_bmad-output/审查/evidence-w44b7-tail/`）：
   `codex-r2-medium-fix-verify-20260914T212009.txt`（拿 round-2 原文复现输入逐条验，9 例含 2 条「不得误红」反向用例）、
   `negctl-arg-and-nodeid-r3-20260914T212029.txt`（参数纪律 6 例 + `node_result_line` 恒真回归的直接自证）、
   `whitelist-negctl-r3-20260914T212233.txt`、`seam-negctl-r3-20260914T212233.txt`、`order-negctl-r3-20260914T212233.txt`、
   `r3-precheck-20260914T212429.txt`、`probes-r3-20260914T212511.txt`（剪枝 15 例 + 识别面 14 例 + 验伪锚）
7. 前两轮存档（对照）：`codex-review-CARD-W4-4b7-TAIL-r1.md`、`codex-review-CARD-W4-4b7-TAIL-r2.md`

## 二 本轮整改自述（请独立核对，不要采信）

**MEDIUM-1（跑器 nodeid 检查恒真）已改**：`awk '$1==n && $2==w'` 未匹配时退出码仍是 0，上一版
直接拿它当条件 ⇒ 身份检查恒真。已独立复现（`printf 'a b\n' | awk '$1=="zzz"'; echo $?` → 0）。
现改成显式判输出非空 + `awk ... END { exit(found ? 0 : 1) }` 双保险（`node_result_line`）。
存档里有三条自证：真命中 rc=0 / 不命中 rc=1 / `other/<完整nodeid>` 前缀冒充 rc=1。

**MEDIUM-2、MEDIUM-3（顺序门假绿）已改，且是语义重写不是打补丁**：你的诊断准确 ——
round-2 把函数体的调用记在 **`def` 的下标**上，而顺序语义要的是**调用发生的下标**。现在：
- **无装饰器的 `def` 不贡献任何调用**（body 归到调用点）；
- **带装饰器的 `def` 在定义点就展开**（装饰器在 `def` 执行时确实会跑它）；
- **调用点 `helper()` 就地展开 `helper` 的 body**，沿调用链递归（在途集合防自递归）；
- `_reachable_local_func_names` 删除，换成 `_local_func_defs`：裸 `ast.walk` 收**全部**定义
  （含嵌套），**同名多份全收一起展开**（不再 `setdefault` 只留第一份 —— 你指出只留第一份会
  掩盖真调用）。
你给的两个复现输入与附例（`first()` 调 `second()`）现在都翻红；两条「不得误红」的反向用例
（helper 在 hook 之后才调用 / 谁都没调过的局部函数）仍绿；自递归不卷死；干净源下标仍 `4/5/6`。

**MEDIUM-3 你指出的「同一条复合语句内完成定义+调用可以展开，不能笼统说传集合后一概不展开」**：
接受，那句自述作废。新语义下自足模式与作用域模式的区别只剩「有没有局部函数表可查」。

**LOW-1（别名覆盖造成假红）——承认，有意不改**：`f=self.ledger; f=self._ledger_locked; f()`
现在会报 `ledger`。判「哪个绑定在调用时活着」需要真流分析，本判据不做；两个方向只能选一个，
选**假红**（吵一次，人来确认）而不是**假绿**（漏一次真嵌套取锁，表现为 atexit 期挂住）。
已写进 docstring，并把元组解包 / `for` 目标 / `with ... as f` 三类**根本没收**如实列出。

**LOW-2（summary 可冒充）已改**：① 只在 `short test summary info` 区段内筛（awk 区段提取，
遇下一条 `===` 结束）；② nodeid 用 `$1=="FAILED" && $2==n` 字段比较（有左边界）；
③ 关键词与节点**按下标一一配对**，不再交叉搜索。

**LOW-3（看门只杀一个 PID）已改**：`set -m` 起独立进程组，超时 `kill -9 -- "-$pid"` 杀整组。
脚本头「对照输入只写进临时副本」的**失实注释已改正**为「写进工作树、临时目录放备份；
sha 一致证明的是还原正确，不是运行期间隔离」。

**LOW-4（`--help` 绕过取值校验）已改**：`--help` 移到取值校验**之后**；取值不得以 `-` 开头。
现在 `--help --phase bogus` / `--help --gate bogus` / `--phase --nonsense-arg --help` 全部 rc=2，
单独 `--help` 仍 rc=0。

**LOW-5（docstring）已改**：区分「返回 `False` ⇒ 本函数没调写盘」与「抛异常 ⇒ 写盘调了、文件
状态未定（可能已截断甚至写了一部分）」；并写明「先行推进」是**条件式**保证 —— 锁超时那条路径
并未推进，不能推广成「每次发布请求都获得该保证」。

**另修一处与判据无关的 bash 坑**：`set -u` 下 `「$text」` 里的中文右括号被 bash 当成变量名的一部分，
报 `unbound variable`；已全量改 `${text}` 形式。该缺陷曾让三个负控在最后一步崩溃（那三份产物按
协议未入库，已移出树外并在验收单登记）。

**未改动面**：`guard_plugin.py`、任何 `conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`、
`backend/app/**` 零改动。seam 结构门与行为门本轮**一字未改**。

## 三 请回答的问题（按重要性排序）

① **「调用点展开」这套新语义是否真的封住了 round-2 的两条假绿，且没有造出新的假绿/假红？**
请特别核：(a) 同名多份定义**全部展开**会不会把一个分支里的诱饵算到另一条调用上；
(b) 递归/互递归的在途集合会不会把**本该计入**的调用漏掉（第二次进入时直接 return）；
(c) 局部函数被**赋给别名再调用**（`g = helper; g()`）现在是漏还是算 —— 以及这个方向是否可接受；
(d) `_local_func_defs` 用裸 `ast.walk` 收定义（不剪枝），会不会把只存在于恒假分支里的同名定义
也纳入展开集合，从而在调用点引入死代码里的名字。

② **`node_result_line` 的修法是否彻底？** `awk ... END{exit}` 与「输出非空」两道判据是否都必要、
是否有一条在某些 awk 实现（BSD awk / gawk / mawk）下行为不同？`local line="$(...)" || return 1`
这种写法里 `local` 会不会吞掉右侧命令的退出码（bash 的已知陷阱）——若会，本处是否仍正确？

③ **`phase_after` 的 summary 区段提取是否稳健？** awk 的 `/^=+ short test summary info =+$/`
在 pytest 改变分隔线宽度、启用 `-q`/`--no-header`、或终端宽度不同时是否仍匹配？若区段提取失败
（`summary` 为空），判据会变成假红还是假绿？

④ **`_publish_ledger` 的 docstring 现在是否还有说过头的地方？** 尤其「返回 False 的两条路径都没碰
文件」这句 —— 请核 `:1457` 之后的实际控制流确认它成立。

⑤ **是否有回归**：前两轮已「核对通过」的项（前三类剪枝、源码导出白名单与相等漂移钉、seam 两门、
纯 docstring 性质、`_reachable_prefix` 下标语义）本轮是否仍成立？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评被守逻辑本身**：`live_port_guard.py` 的结账 / 发布 / 退出语义不是本卡的面。
- **不做全称封闭证明**：请把剩余漏面**列举**出来而不是要求本卡穷尽。
