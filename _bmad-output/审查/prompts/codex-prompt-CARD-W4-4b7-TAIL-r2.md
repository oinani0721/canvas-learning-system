# 独立复核请求 — CARD-W4-4b7-TAIL **round-2**（按 round-1 的 MEDIUM-1/2 与 LOW-④/⑤ 整改后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`。round-1 审查 SHA `45b8e0b4`，**本轮审查 SHA `a307de45`**（= 整改后的 HEAD）。
前提 commit `46e7bf77`。

**请只读这几处**：

1. `git --no-pager diff --no-color 45b8e0b4 a307de45 -- . ':(exclude)_bmad-output'`（**本轮整改的全部代码改动**）
2. 需要看整体时：`git --no-pager diff --no-color 46e7bf77 a307de45 -- . ':(exclude)_bmad-output'`（本卡代码面全量）
3. `backend/tests/unit/test_live_port_guard_contract.py` 改后实测范围：
   - `_guard_state_method_names` `:1054-1061`、`_getattr_self_literal` `:1064-1079`
   - **`_indirect_self_method_calls` `:1082-1180`**（MEDIUM-1 整改面）
   - `_is_dead_branch` `:1183-1193`、`_is_always_taken_branch` `:1196-1203`、`_reachable_prefix` `:1210-1222`
   - **`_live_called_names` `:1225-1298`**（签名新增 `expandable`）、**`_walk_live` `:1301-1371`**（遍历本体）、
     **`_reachable_local_func_names` `:1374-1390`**（MEDIUM-2 整改面）
   - 白名单门 `:1480-1533`
   - 顺序门 `:1825-1856` 与 `:1858-1898`（调用点改为 `_reachable_prefix(node.body)` + 传 `expandable`）
   - seam 结构门 `:2032-2100`（未改，作对照）、seam 行为门 `:2102-2163`（未改）
4. `backend/tests/support/live_port_guard.py` 的 **`_publish_ledger` `:1408-1467`**（LOW-⑤ 整改；仍只动 docstring）
5. 跑器 `_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh` 全文（LOW-④ 整改面：参数解析、
   `run_pytest` 看门、`node_result_line`、`phase_after` 的 summary 行绑定）
6. 本轮判据存档（`_bmad-output/审查/evidence-w44b7-tail/`）：
   `codex-r1-medium-fix-verify-20260914T210219.txt`（拿 round-1 原文的复现输入逐条验修复）、
   `probes-r2-20260914T210642.txt`（剪枝 17 例 + 识别面 11 例 + 验伪锚 + 干净源零命中）、
   `negctl-unknown-arg-r2-20260914T210313.txt`、
   `whitelist-negctl-r2-20260914T210321.txt`、`seam-negctl-r2-20260914T210321.txt`、
   `order-negctl-r2-20260914T210321.txt`、`r2-precheck-20260914T210549.txt`
7. round-1 存档（供对照）：`_bmad-output/审查/codex-review-CARD-W4-4b7-TAIL-r1.md`

## 二 本轮整改自述（请独立核对，不要采信）

**MEDIUM-1（别名覆盖 ⇒ 假绿）已改**：`aliases: dict[str, str]`（覆盖式）改成
`alias_methods: dict[str, set[str]]`（保留每个别名曾绑过的**全部**方法），并新增 `alias_links`
做别名→别名的不动点传播（`f = self.ledger; g = f; h = g; h()` 也算）。调用点改为
`names.extend(sorted(alias_methods.get(name, set())))`。round-1 给的两个复现输入现在都会报出
`ledger`（非白名单）⇒ 门红。docstring 里「过近似只会假红」那句**已删并改写成如实说明**（`:1094-1113`）。

**MEDIUM-2（第四类剪枝 ⇒ 顺序门假绿）已改，且面比 round-1 指出的更宽**：
- 带**装饰器**的局部函数体一律当可达（`_walk_live` `:1338-1345`）；
- 更根本的问题是**逐语句分析丢失跨语句关联**（round-1 LOW-③ 也点到）：新增
  `_reachable_local_func_names(scope)`（`:1374-1390`）先在**整个 `install()` 作用域**上算出
  「哪些局部函数名被**可达地**提名过」，两个顺序门把它当 `expandable` 传给每一条语句；
  名字在表里 ⇒ body 照常展开，不在表里 ⇒ 才算「谁都没提过」而剪掉。
  引用集合只从**已剪枝**的遍历里收（藏在恒假分支里的 `helper()` 不算提名，否则剪枝白做）。
- 顺序门调用点同时改成 `enumerate(_reachable_prefix(node.body))`（round-1 LOW-③ 指出的
  「顶层 `return` 之后仍被计数」）。
- 原 docstring 里「根节点是 `FunctionDef` ⇒ body 不展开」那段推论与「方向是吵不是漏」的说法**已删**。

**LOW-④（跑器绑定）已改**：
- nodeid 判定由 `grep -qF "$node $want"` 改为 `awk '$1 == n && $2 == w'`（字段精确相等，
  既有左边界，也免去 nodeid 里 `/` `.` `::` `[]` 的正则转义问题）；
- `phase_after` 的关键词改为**绑到 `short test summary info` 的同一行**（`FAILED <nodeid> - <原因>`），
  不再整份输出搜；并新增 `pytest rc == 1` 的断言（收集错误/超时不算门红）；
- `--help` 不再早退，先解析完全部参数（`--help --nonsense-arg` 现在 rc=2）；
- 新增墙钟看门 `run_pytest`（默认 180s，`NEGCTL_TIMEOUT_SECS` 可调），超时 kill 并记 rc=124。

**LOW-⑤（docstring 过满）已改**：删去「截断之后失败 ⇒ `json.loads` 必报错」的必然性表述
（改为「多半…但不是必然：内容可能已完整落盘而 `close`/延迟 I/O 才报错」）；删去「父进程据文件复核
不会把陈旧零账当真」这个推不出来的结论（改为明说发布序**只**保证「更旧的不再回写」，父进程要不要
另看退出码或 `seq` 属本函数管不到的范围）；明写 `_PUBLISHED_SEQ` 是**进程级**全局，另一个进程不受约束。

**MEDIUM-3（隔离方式与自述不符）——承认，未改代码形态**：对照输入确实写进**工作树**，临时目录里放的是
**备份**；round-1 的判断正确，本轮把自述改正（见验收单），并加了上面的墙钟看门以限制「万一挂住」的
影响面。仍不主张「运行期间隔离」。

**未改动面**：`guard_plugin.py`、任何 `conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`、
`backend/app/**` 零改动。反向锚三条 + 两个顺序门 + 白名单门逐条 `PASSED`；`tests/unit -k live_port_guard`
= 152 passed / 5206 deselected；三个负控 before/after/clean 三阶段全部成立且 sha 前后逐字节相同。

## 三 请回答的问题（按重要性排序）

① **MEDIUM-1 的整改是否真的封住了那条假绿，且没有引入新的假红？** 请特别核：
`alias_links` 的不动点传播在「别名被重新绑成非方法值」（`f = self.ledger; f = some_plain_value; f()`）
时会怎样；元组解包 / `for` 目标 / `with ... as f` 这些**没有**进 `alias_methods` 的绑定形态是否仍如实算漏面；
以及 `alias_methods` 现在只增不减，会不会让某个**合法**的临界区（当前源码里没有，将来可能有）被误红。

② **MEDIUM-2 的整改是否真的封住了那两条假绿？** 请用你 round-1 的两个复现输入独立重跑，并再找
`_reachable_local_func_names` 自身的漏面：它只扫 `scope.body` 的可达前缀，
(a) 定义在**嵌套**函数里的局部函数、(b) 通过 `locals()` / registry 反射调用、
(c) `expandable` 表按**名字**去重（同名函数在不同分支各定义一次）——这三类现在分别是漏还是误红？
另外：`_walk_live` 在 `expandable is not None` 时**不再**跑自足不动点，同一条语句内「定义 + 调用」
的嵌套函数是否还能展开？

③ **顺序门改用 `_reachable_prefix(node.body)` 后，下标语义是否仍然正确？** 截断会让下标空间变小，
`hook_at < precheck_at` 这类比较是否可能因此得出与「真实执行顺序」不一致的结论？
`install()` 当前源码上实测下标是 `4 / 5 / 6`（与整改前相同）——请独立复算。

④ **跑器的新绑定是否还有可冒充面？** `awk '$1 == n && $2 == w'` 对 pytest `-v` 输出的格式假设
（结果行第一个字段恰好是 nodeid）在什么情况下会不成立（例如 `-p xdist`、`--tb` 变体、
参数化 id 含空格）？`phase_after` 用 `grep -F "$node " | grep -qF "$text"` 绑 summary 行，
summary 行被 pytest 截断时会不会让关键词判据静默失效？墙钟看门用 `kill -9` 是否会留下孤儿子进程？

⑤ **LOW-⑤ 改后的 docstring 是否还有说过头的地方？** 以及：新写法说「发布序先行推进保证的只有一件事」，
这句本身是否准确（`_PUBLISH_LOCK` 超时返回 `False` 那条路径上序号并未推进，是否需要一并说明）？

⑥ 本轮是否有**回归**：整改引入的 `_walk_live` / `_reachable_local_func_names` 是否让此前
round-1 已「核对通过」的项（前三类剪枝、源码导出白名单与相等漂移钉、seam 行为门、纯 docstring 性质）
发生变化？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路。
若某项经核对成立，请明说「核对通过」并给出你据以判断的具体位置。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。

## 五 边界

- **只读**：不要修改仓库里的任何文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评被守逻辑本身**：`live_port_guard.py` 的结账 / 发布 / 退出语义不是本卡的面（本卡只改其 docstring）。
- **不做全称封闭证明**：作者已明说识别面有限；请把剩余漏面**列举**出来而不是要求本卡穷尽。
