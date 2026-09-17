# 独立复核请求 — CARD-W4-4b7-TAIL（W4 门四债收口：白名单门认间接持锁调用 / seam 行为门 / 顺序门可达剪枝 / `_publish_ledger` docstring 收窄 / 负控跑器拒未知参数）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`，前提 commit `46e7bf77`（前一卡 CARD-W4-FINAL-ACCOUNTING 末 commit），审查 SHA `45b8e0b4`。

**请只读这几处**：

1. `git --no-pager diff --no-color 46e7bf77 45b8e0b4 -- . ':(exclude)_bmad-output'`（代码面全部改动，恰两个文件）
2. `backend/tests/unit/test_live_port_guard_contract.py` 的 **:1054-1292**（本卡改写/新增的全部 helper，改后实测范围）：
   - `_guard_state_method_names` `:1054-1061`（新增）
   - `_getattr_self_literal` `:1064-1079`（新增）
   - `_indirect_self_method_calls` `:1082-1148`（新增）
   - `_is_dead_branch` `:1151-1161`（**只加注释，判定逻辑未动**）
   - `_is_always_taken_branch` `:1164-1171`（新增）
   - `_BLOCK_TERMINATORS` `:1175` + `_reachable_prefix` `:1178-1190`（新增）
   - `_live_called_names` `:1193-1292`（重写）
3. 三个被硬化 / 新增的门（改后实测范围）：
   - 白名单门 `TestSettlementAtomicity::test_settlement_path_never_nests_the_lock` `:1382-1435`
   - 顺序门 `TestInstallOrder::test_audit_hook_is_installed_before_the_target_precheck` `:1727-1757` 与
     `TestInstallOrder::test_final_accounting_is_registered_before_the_precheck` `:1759-1798`
   - seam 结构门 `TestFinalizeRaceSeam::test_seam_is_called_unconditionally_not_inside_a_condition` `:1932-2000`（本卡未改，作对照）
     与**新增行为门** `TestFinalizeRaceSeam::test_seam_runs_exactly_once_on_a_blocked_attempt` `:2002-2063`
4. `backend/tests/support/live_port_guard.py` 的 **`_publish_ledger` `:1408-1461`**（本卡只改其 docstring）
5. 三个负控跑器全文：`_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh`（共用实现）+
   `negctl_whitelist.sh` / `negctl_seam.sh` / `negctl_order.sh`（薄壳）
6. 判据存档（纯文本，均在 `_bmad-output/审查/evidence-w44b7-tail/`）：
   `whitelist-negctl-20260914T204641.txt`、`seam-negctl-20260914T204736.txt`、`order-negctl-20260914T204828.txt`、
   `indirect-self-calls-probe-20260914T204553.txt`、`live-called-names-pruning-probe-20260914T204350.txt`、
   `publish-ledger-docstring-ast-20260914T204219.txt`、`negctl-unknown-arg-20260914T204207.txt`、
   `guard-selftest-20260914T204935.txt`、`ruff-zsh-array-20260914T205153.txt`、`unit-open-diff-20260914T204610.txt`

**背景（供理解，不必再核）**：`live_port_guard.py` 是 pytest 测试进程内的一道「看门」——用 CPython
`sys.addaudithook` 拦下任何到现网 Neo4j 端口（7691/7687）的 `socket.connect`，并在进程退出时结账。
上面那几个「门」是**盯着这道看门自己的源码结构**的契约测试（AST 断言），本卡做的是把它们四笔已登记
的债收口（来源：`UAT-CARD-W4-4b` 的 MEDIUM-1/2/3 与 LOW-4，`UAT-CARD-W4-7` 的 LOW-3a）。

## 二 作者自述（请独立核对，不要采信）

1. **白名单门（MEDIUM-1）**：原判据 `_direct_self_calls` 只认字面 `self.<name>(...)`，于是临界区里
   `f = self.ledger` 后 `f()`、`getattr(self, "ledger")()` 这两类间接形态不被检查。新增
   `_indirect_self_method_calls` 识别四种：别名赋值（`Assign`）、带注解赋值（`AnnAssign`）、海象
   （`NamedExpr`，含内联 `(f := self.ledger)()`）、字面 `getattr(self, "<字面串>")`。识别面限定在
   `_GuardState` 的方法名集（源码导出）内，避免把 `recs = self.records` 误判成方法调用。白名单仍是
   `_locked_helper_names()` 源码导出 + `assert allowed == {"_unaccounted_locked","_ledger_locked"}`
   漂移钉，**没有改成写死字面量**。失败文案由「`_lock` 不可重入，调了就是死锁」改为「不在已持锁 helper
   白名单内，这是一次未经确认的持锁调用……须确认它体内不再取 `self._lock`」。
2. **seam 行为门（MEDIUM-2）**：原四条子规则全是结构性的，挡不住「结构合法但运行时不执行」的摘除。
   新增行为门把 `guard._finalize_race_seam_hook` 换成计数包装器（仍调原函数），用 `isolated_state`
   fixture 隔离账本后合成 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))`，断言注入点恰被
   执行 1 次；并先对非受拦端口 5432 断言 0 次（且该端口不在 `BLOCKED_PORTS` 里有显式断言）。
   全程不建立任何真实 socket 连接。
3. **顺序门剪枝（MEDIUM-3）**：`_live_called_names` 的剪枝清单由「只剪字面恒假分支的 body」扩到四类：
   ①恒假 body；②恒真 `if` 的 `orelse`（死 else）；③同一语句块里 `return`/`raise`/`break`/`continue`
   **之后**的语句（终结语句自己仍算）；④整个子树里名字再没出现过的局部 `FunctionDef` 的 body。
   第④类的判据是「名字有没有作为任何 `Name` 被提过」而不是「有没有被调用」，以免把 `g = helper; g()`
   这种别名调用的真可达函数体误剪。`_is_dead_branch` 的**判定逻辑一字未动**（seam 门子规则 (iii) 共用它），
   新形态另写 `_is_always_taken_branch`。两个 helper 与顺序门的 docstring 同步改写成实际清单。
4. **`_publish_ledger` docstring（LOW-4）**：「文件停留在截断/无效态」改为「文件可能缺失、无效或保留
   旧内容」，并分开说明「失败点在 `open(path,"w")` 截断之后 / 之前」两种形态。判定逻辑未动：剥掉
   docstring 节点后 `ast.dump` 与改前**逐字节相同**（存档 `publish-ledger-docstring-ast-*.txt`，
   实测 1437 字符两侧相同）。
5. **LOW-3a（跑器纪律）**：三个负控跑器对未识别参数一律 `exit 2` 并打印 `unknown arg: <x>`；每个「应
   通过」的跑都断言 `<nodeid> PASSED` 这个身份（不只看进程 rc、不只数正文命中总数）。
6. **先绿后红（三个门各一次，存档见 §一.6）**：`before` 用 `git show 46e7bf77:<测试文件>` 换回未硬化的
   门 + 对照输入 → 目标门 `PASSED`（门盲）；`after` 用工作树已硬化的门 + 同一对照输入 → 目标门
   `FAILED` 且失败正文含指定断言消息；`clean` 两份文件都不动 → `PASSED`（不自伤）。对照输入只写进
   临时副本，EXIT trap 无条件还原，两份文件全文件 `shasum -a 256` 跑前跑后逐字节相同。对照输入的
   锚点字符串命中次数若 `!= 1` 脚本立刻退出（防「变异静默落空」把门盲读成门真红）。
7. **未改动面**：`guard_plugin.py`、任何 `conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`、
   `backend/app/**` 一律零改动（地盘门实测 diff 恰两个文件）。反向锚
   `test_seam_untouched_passes_liveness` / `test_seam_replacement_is_detected_as_drift` /
   `test_throwing_seam_cannot_skip_accounting` 逐条 `PASSED`；契约文件 152 passed；
   `tests/unit -k live_port_guard` = 152 passed / 5206 deselected（非零收集）。

## 三 请回答的问题（按重要性排序）

① **白名单门硬化后，是否仍有更隐蔽的间接持锁路径没被识别？** 请如实列举（这是「门未覆盖的路径」，
本卡不主张全称封闭）。特别是：动态属性名 `getattr(self, name)`、`self.__getattribute__("ledger")()`、
把绑定方法塞进容器/参数再取出来调、`functools.partial(self.ledger)`、以及经由局部函数间接调用的形态。
另外请判断：识别面被限制在 `_GuardState` 方法名集内，会不会反而漏掉某个**不在类里**但同样会取
`self._lock` 的可调用对象？

② **seam 行为门的「恰 1 次」是否会被合法重构误红？** 例如：受拦路径将来若在同一次事件里多走一次记账、
或 `_audit_hook` 被拆成两层函数、或 CPython 的 audit 语义在别的版本上对同一次 `sys.audit` 调用多次分发。
本门是否依赖本机 CPython 3.14.x 的具体 audit 语义？非受拦端口选 5432 是否可能在别的环境里恰好被拦？

③ **顺序门剪枝扩面是否引入了「把合法的可达代码误判为死码」的假红面？** 请逐条检查四类剪枝在 Python
语义下是否**真的**不可达，尤其：③类对 `Try.body` / `match` case / `with` body 的按字段截断是否都成立；
④类「按名字被提过」的判据在 `globals()` / `locals()` 反射调用、装饰器注册、以及闭包被返回后在别处调用
这三种情形下会不会误剪。另外请评估作者在 docstring 里承认的那条推论（根节点自己是 `FunctionDef` 时
body 不展开 ⇒ 跨语句的「先定义后调用」会以『找不到可达的 X』翻红）——这个方向是否可接受。

④ **负控跑器对「应通过」节点的核法是否真绑 nodeid 而非总数？** 请核 `run_nodes` 的实现：它用
`grep -qF "$node $want"` 在 pytest `-v` 正文里找 `<nodeid> PASSED`。这种绑法有没有可能被「另一条
nodeid 恰好是本 nodeid 的前缀」之类情形骗过？`after` 阶段只核 `FAILED` 与失败正文关键词，是否足够
排除「红在别的断言上」？

⑤ **`_publish_ledger` 的 docstring 收窄是否反而漏了某种失败态？** 新措辞列了三种（缺失 / 无效 /
保留旧内容）。`write_ledger` 的实现路径上是否还存在第四种可观测结果（例如写了一半但恰好是合法 JSON、
或目标是符号链接/命名管道时的形态）？以及：新措辞声称「发布序已先行推进 ⇒ 更旧的快照此后一律被拒」，
这句在 `_PUBLISHED_SEQ` 为进程级全局、而账本文件可能被**另一个进程**写的前提下是否仍成立？

⑥ 本卡对照输入之一（白名单门那条）在 `record()` 的临界区里插入了 `_f = self.ledger` + `_f()`，那是
一个**真的自死锁**形态。作者的论证是：负控只跑 AST 结构门那一个 nodeid，`record()` 在该跑里不会被
执行（`audit_hook_alive()` 的自证地址在 `record()` 之前就以 `_SelfTestBlocked` 抛出），因此不会挂住
进程。请独立核对这条论证，并指出如果有人把该跑器改成目录级会发生什么。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：`file:line` + 一句话复现思路。
若某一项经核对成立，请明说「核对通过」并给出你据以判断的具体位置，不要只回「看起来没问题」。

## 五 边界

- **只读**：不要修改仓库里的任何文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692，本卡代码不发起任何真实连接。
- **不评被守逻辑本身**：`live_port_guard.py` 的结账 / 发布 / 退出语义是前一卡与更早卡的面，本卡只改了
  `_publish_ledger` 的 docstring；请不要把那些逻辑的设计问题当成本卡缺陷（可作为 LOW 登记移交）。
- **不做全称封闭证明**：作者已明说识别面有限；请把剩余漏面**列举**出来而不是要求本卡穷尽。
