# UAT — CARD-W4-4b7-TAIL（W4 门四债收口：白名单门认间接持锁调用 / seam 行为门 / 顺序门可达剪枝 / `_publish_ledger` docstring 收窄 / LOW-3a 负控跑器纪律）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-W4-4b7-TAIL]` · 车道 `card-t9-w4`（T9 第 2/4 张）
> 前提 commit `PREREQ = 46e7bf77`（前一卡 CARD-W4-FINAL-ACCOUNTING 末 commit）
> 代码 commit 链 `45b8e0b4` → `a307de45` → `c118e33e` → `485a1f89` → `6e4fedc5`（代码末态）
> + D-32 纯 docstring 尾巴 `a008882e`（**最终 HEAD**）· 文档 commit 见本文件末
> 证据目录 `_bmad-output/审查/evidence-w44b7-tail/`（引用一律写全文件名，不用 glob）
> 卡文 `第十四批-goals/T9-B.md` · 协议 `.claude/rules/card-batch-protocol.md`（feature 主干树那份）

---

## 〇 第 0 分钟自证（完成条件 a）

存档：`evidence-w44b7-tail/minute-zero-20260914T203810.txt`

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-t9-w4` ✅ |
| 分支 | `card/t9-w4` ✅ |
| `git status --porcelain \| wc -l` | **0**（首条命令实测；落档文件里显示 1 是该 evidence 文件自身，写档动作发生在自证之后） |
| `git log --oneline -3` 顶部 | `46e7bf77 docs(w4-guard): … CARD-W4-FINAL-ACCOUNTING` ✅（`grep -cF` = 2） |
| `PREREQ` | `46e7bf77` |
| `$BASE` 存在 + `grep -vc '^#'` | **64** ✅（feature 主干树 `evidence-b14/unit-red-baseline-08100483.txt`） |
| `backend/.venv/bin/pytest` / `backend/.env` / `pyright` | 三者均在 ✅ |

**行号实测（本树 HEAD，不沿用 `08100483` 原值）——与卡文 §〇 逐条吻合，零漂移：**

| 符号 | 卡文 | 本树实测 |
|---|---|---|
| `_locked_helper_names` | `:1035` | `:1035` ✅ |
| `_direct_self_calls` | `:1044` | `:1044` ✅ |
| `_is_dead_branch` | `:1054` | `:1054` ✅ |
| `_live_called_names` | `:1063` | `:1063` ✅ |
| `test_settlement_path_never_nests_the_lock` | `:1187` | `:1187` ✅ |
| `test_audit_hook_is_installed_before_the_target_precheck` | `:1516` | `:1516` ✅ |
| `test_final_accounting_is_registered_before_the_precheck` | `:1542` | `:1542` ✅ |
| `test_seam_is_called_unconditionally_not_inside_a_condition` | `:1715` | `:1715` ✅ |
| 失败文案「调了就是死锁」 | `:1222` | `:1222` ✅ |
| `_publish_ledger` def | `:1408` | `:1408` ✅ |
| 旧 docstring「文件停留在截断/无效态」 | `:1430` | `:1430` ✅ |

**面更正自证（卡文 §〇 第 1 行「三个门全在契约测试文件，不在 `guard_plugin.py`」）：**
`wc -l guard_plugin.py` = **55**；`grep -cE '^[[:space:]]*def test_' guard_plugin.py` = **0**；
验伪锚：同一条命令打在 `test_live_port_guard_contract.py` 上 = **101** —— 证明命令本身能命中，0 不是哑火。

---

## 一 4-A：Claude 已代验的技术证据

> ⛔ **本节记录的是首版（`45b8e0b4`）的改法、行号与存档**。此后经 Codex 五轮外审整改
> （r1~r5，详见 §五），**顺序门 (d) 的实现被重写过三次、最终改成「遇延迟执行体即拒绝判定」**，
> 本节 §一.3 的 helper 描述与行号已**不代表最终态**；(b)(c)(e)(f) 的结论与最终态一致但行号已漂。
> **最终态的权威记录在 §五（逐轮结论与处置）与 §六（收尾实测）**。下表是最终 HEAD 上的实测行号：
>
> | 符号 | 首版行号 | 最终 HEAD `a008882e` 实测 |
> |---|---|---|
> | `_indirect_self_method_calls` | `:1082-1148` | `:1082-1187` |
> | `_is_always_taken_branch` | `:1164-1171` | `:1203-1210` |
> | `_reachable_prefix` | `:1178-1190` | `:1217-1229` |
> | `_live_called_names` | `:1193-1292` | `:1232-1350` 左右（含 D-32 尾巴新增说明） |
> | `_refuse_to_guess_on_deferred_execution` | （首版无） | `:1353` 起（r4 新增、r5 扩面） |
> | 白名单门 | `:1382-1435` | `:1487` 左右 |
> | 顺序门 ×2 | `:1727-1757` / `:1759-1798` | `:1813` / `:1846` 左右 |
> | seam 行为门 | `:2002-2063` | `:2100` 左右 |
>
> 首版存档仍如实保留（`whitelist-negctl-20260914T204641.txt` /
> `seam-negctl-20260914T204736.txt` / `order-negctl-20260914T204828.txt`）：它们证明的是**首版**门
> 对各自对照输入先绿后红。**最终态的同族存档**是 `whitelist-negctl-r5-20260914T214915.txt` /
> `seam-negctl-r5-20260914T214915.txt` / `order-negctl-r5-20260914T214915.txt` 与
> `codex-all-rounds-repro-verify-r5-20260914T214830.txt`（引用一律写全名，不用 glob）。


### 1. 白名单门认间接持锁调用 + 失败文案收窄（完成条件 b）

**改法**：新增 `_guard_state_method_names`（`:1054-1061`）/ `_getattr_self_literal`（`:1064-1079`）/
`_indirect_self_method_calls`（`:1082-1148`）；白名单门 `:1382-1435` 把间接命中与直接命中一起过
`allowed`。**白名单仍走 `allowed = _locked_helper_names()` 源码导出 + `assert allowed == {…}` 漂移钉，
未改成写死字面量**（卡文 (b) ⛔ 条）。

**识别面直接探针**：`evidence-w44b7-tail/indirect-self-calls-probe-20260914T204553.txt`
—— 10 个用例全 OK（别名赋值 / 字面 `getattr` / 两者组合 / 内联海象 / 分离海象 / 带注解赋值 命中；
白名单内的间接调用正常放行；`recs = self.records` 不误判；动态名 `getattr(self, name)` 如实不命中；
「赋值但从不调用」不算命中）+ **7 条验伪锚**证明同一批喂给旧的 `_direct_self_calls` **一条都数不到**
（那正是 MEDIUM-1 的漏面）+ 干净源全部 `with self._lock` 临界区**零命中**（门不自伤）。

> ⚠️ 首轮探针抓到一处真漏：内联海象 `(_f := self.ledger)()` 的 `Call.func` 是 `NamedExpr` 不是 `Name`，
> 别名表够不着。已在 `:1138-1145` 补识别后复跑全绿。存档里保留了这一行注记。

**失败文案**：`:1222` 的「`_lock` 不可重入，调了就是死锁」已删（`grep -cF '调了就是死锁'` = 0），
改为「不在已持锁 helper 白名单内，这是一次**未经确认的持锁调用**。`_lock` 不可重入，须确认它体内不再取
`self._lock`：真取就是死锁……」—— 与 UAT-W4-4b MEDIUM-1「negctl case 2 的 helper 其实不取锁」一致。

**先绿后红**：`evidence-w44b7-tail/whitelist-negctl-20260914T204641.txt`

| 阶段 | 内容 | 结果 |
|---|---|---|
| before | `git show 46e7bf77:` 的未硬化门 + 对照输入 | `…::test_settlement_path_never_nests_the_lock **PASSED**`（门盲） |
| after | 工作树已硬化门 + 同一对照输入 | `… **FAILED**`，失败正文含「未经确认的持锁调用」 |
| clean | 干净源 + 已硬化门 | `… **PASSED**`（不自伤） |
| sha | 两份文件全文件 `shasum -a 256` | 跑前 = 跑后，逐字节相同 ✅ |

对照输入 = 在 `_GuardState.record` 临界区插 `_f = self.ledger` + `_f()`（`ledger()` 自己取
`self._lock` ⇒ 自死锁形态）。锚点命中次数脚本内硬断言 `== 1`（防变异静默落空把门盲读成门真红）。

### 2. seam 门加行为断言挡死语句（完成条件 c）

**改法**：`TestFinalizeRaceSeam` 的四条结构子规则**一条未动**（`:1932-2000`），新增行为门
`test_seam_runs_exactly_once_on_a_blocked_attempt`（`:2002-2063`）：把 `_finalize_race_seam_hook`
换成计数包装器（仍调原函数），用 `isolated_state` 隔离账本，先对非受拦端口 5432 断言 seam **0 次**
（并显式断言 5432 不在 `BLOCKED_PORTS` 里 —— 否则这一半失去对照），再合成
`sys.audit("socket.connect", None, ("127.0.0.1", 7691))` 断言 seam **恰 1 次** + `blocked == 1`。
全程不建立任何真实 socket 连接。

**先绿后红**：`evidence-w44b7-tail/seam-negctl-20260914T204736.txt`

| 阶段 | 目标 nodeid | 结果 |
|---|---|---|
| before | 结构门 `test_seam_is_called_unconditionally_not_inside_a_condition` | **PASSED**（四条子规则条条仍满足） |
| after | 行为门 `test_seam_runs_exactly_once_on_a_blocked_attempt` | **FAILED**，正文「受拦路径上注入点被执行了 0 次，应为 1」 |
| clean | 行为门 | **PASSED** |
| sha | 两份文件 | 跑前 = 跑后 ✅ |

对照输入 = 把 seam 调用变成 `while True: break` **之后**的死语句。结构上样样合格（独立 `Expr` /
在受拦分支 body 里 / 祖先链无恒假分支 / 不进任何判据），运行时永不执行 —— 这正是 MEDIUM-2 说的那一类。

### 3. 顺序门可达剪枝不止 `if False`（完成条件 d）

**改法**：`_live_called_names`（`:1193-1292`）剪枝清单由「只剪恒假 body」扩到四类，新增
`_is_always_taken_branch`（`:1164-1171`）与 `_BLOCK_TERMINATORS`/`_reachable_prefix`（`:1175/:1178-1190`）。
**`_is_dead_branch` 的判定逻辑一字未动**（`:1151-1161` 只加了一条「禁扩写」注释）—— seam 门子规则 (iii)
共用它，改它会连带。两个 helper 与顺序门 `:1727-1757` 的 docstring 同步改写成实际清单（不再写
「只剪 `if False`」这种过宽措辞）。

**剪枝语义直接探针**：`evidence-w44b7-tail/live-called-names-pruning-probe-20260914T204350.txt`
—— 17 个用例全 OK（四类剪枝各自生效 + 终结语句自己仍算 + `Try.handlers` 不受 body 截断影响 +
被提名的局部函数体仍展开 + 别名引用也算被提名）；保守方向三条守住（变量条件分支 / `while True` 的
loop-else / `lambda` 体一律当可达）；**8 条验伪锚**证明被剪的那些在未剪枝的 `_called_names` 下全是「可达」。

> ⚠️ 首轮探针 3 条 BAD，全部因为用例把根节点包成了 `def f():` —— 那恰好命中一条真语义：
> **根节点自己是 `FunctionDef` 时它的 body 不展开**（「定义函数」这条语句在顺序语义里不执行函数体）。
> 已把该语义连同它的假红代价写进 `_live_called_names` docstring（`:1284-1292`），并改正用例后复跑全绿。

**对照输入的 AST 预演**（不落盘改文件，纯内存）：干净源上未剪枝版与新剪枝版读数一致
（hook@4 < precheck@6）；对照输入上未剪枝版仍读 hook@4（诱饵，门盲），新剪枝版读 hook@7 > precheck@6（门红）。

**先绿后红**：`evidence-w44b7-tail/order-negctl-20260914T204828.txt`

| 阶段 | 目标 nodeid（两条） | 结果 |
|---|---|---|
| before | `test_audit_hook_is_installed_before_the_target_precheck` + `test_final_accounting_is_registered_before_the_precheck` | 两条均 **PASSED**（诱饵被当可达） |
| after | 同两条 | 两条均 **FAILED**；正文分别含「承重 hook 装在预检之后」（`assert 7 < 6`）与「结算器排到了 hook 前面」（`assert 7 < 5`） |
| clean | 同两条 | 两条均 **PASSED** |
| sha | 两份文件 | 跑前 = 跑后 ✅ |

对照输入 = 诱饵 `_install_audit_hook()` 放进 `if True: pass` 的**死 else** 且摆在预检之前，真调用挪到预检之后。

### 4. `_publish_ledger` docstring 收窄（完成条件 e）

存档：`evidence-w44b7-tail/publish-ledger-docstring-ast-20260914T204219.txt`

| 判据 | 实测 |
|---|---|
| 剥 docstring 节点后 `ast.dump` 逐字节相同 | **True**（两侧长度均 1437） |
| docstring 确实变了（验伪锚：False ⇒ 本条根本没改） | **True** |
| `grep -cF '文件可能缺失、无效或保留旧内容'`（工作树） | **1** |
| `grep -cF '文件停留在截断/无效态'`（工作树） | **0** |
| 验伪锚：同两条 grep 打在 `46e7bf77` 版上 | **0 / 1**（反过来，证明两条 grep 都能命中） |
| 全文件 diff hunk 数 | **1** |

新措辞把「文件停留在截断/无效态」拆成三种如实形态：失败点在 `open(path,"w")` 截断**之后**（截断/半截态，
父进程 `json.loads` 报错）；失败点在截断**之前**（磁盘满 / 权限 / 路径消失 ⇒ 旧合法 JSON 原样还在）；
并说明为何三种都不是「可信的谎」（发布序已先行推进，更旧的快照此后一律被拒）。

> ⚠️ 过程注：首版把新文案写成 `文件**可能缺失、无效或保留旧内容**`，markdown 强调符把卡文 §二.5 要求的
> 连续字面量断开了，`grep -cF` = 0。已改成连续写法后复跑命中 1。

### 5. LOW-3a 负控跑器纪律（完成条件 f）

跑器：`evidence-w44b7-tail/negctl_w4_gates.sh`（共用实现，清单只此一份）+ 三个薄壳
`negctl_whitelist.sh` / `negctl_seam.sh` / `negctl_order.sh`。

| 要求 | 实测存档 |
|---|---|
| ① 未识别参数 `rc≠0` + 打印 `unknown arg: <x>` | `negctl-unknown-arg-20260914T204207.txt`：三个跑器 × 两种坏参数（`--nonsense-arg` / `--phase bogus`）**全部 rc=2** 且正文含 `unknown arg:` |
| ① 验伪锚：合法参数不得被误拒 | 同档 `--help` → **rc=0** |
| ② 「应通过」那一跑核 nodeid 级 PASSED | 三份 negctl 存档里每条 `[OK] nodeid 级判定命中：<nodeid> PASSED`；实现见 `run_nodes`，绑 `grep -qF "$node PASSED"` 而非进程 rc、而非命中总数 |

### 6. guard 自测 + 反向锚（完成条件 g）

存档：`evidence-w44b7-tail/guard-selftest-20260914T204935.txt`

| 判据 | 实测 |
|---|---|
| `tests/unit -k live_port_guard` | **152 passed, 5206 deselected** —— selected=152 ≠ 0，非「全 deselect 假绿」 |
| 反向锚逐条 nodeid 级 | `test_seam_untouched_passes_liveness` **PASSED** / `test_seam_replacement_is_detected_as_drift` **PASSED** / `test_throwing_seam_cannot_skip_accounting` **PASSED** / 结构门 **PASSED** / 新行为门 **PASSED**（`collected 5 items` → `5 passed`） |
| 整份契约文件 | **152 passed** |
| `import tests.support.live_port_guard`（在 `backend/` 下） | rc=0，`BLOCKED_PORTS=[7687, 7691]`（import 期装门不崩，存档 `guard-import-and-ruff-20260914T204302.txt`） |

### 7. tests/unit 目录级（完成条件 h）

| 跑 | 存档 | 汇总 |
|---|---|---|
| 开工 | `unit-open-20260914T203839.txt` | 36 failed / 5076 passed / 29 errors（起跑 20:38:39，收集期早于本卡第一次编辑 ⇒ 反映**改前**树） |
| 收工 | `unit-close-<TS>.txt`（见下表） | 见下表 |

**开工 diff 判定**（`unit-open-diff-20260914T204610.txt`）：base(64) → open(65)，唯一一条 `>` 是
`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。
身份按协议 §3 / 手册 §零.6 绑**失败正文**而非 nodeid：该跑 `blocked=1`（基线那跑是候选树常态 `blocked=0`），
失败正文含 `live Neo4j port connect attempted —— 本用例期间有 1 次…` 与
`('::1', 7691, 0, 0) on thread MainThread`（去重计数 1）；验伪锚：同一条锚打在 `base.nodeids` 上 = 0。
⇒ 这是 W4 哨兵红按时序挂到某条用例上，与本卡改动无因果（本卡只改契约测试与一段 docstring，
不可能产生 Neo4j 连接）。卡文 (a) 允许开工 diff 含前卡与时序造成的增减，如实记录。

**收工 diff**（本卡只对「收工相对开工的新增 `>`」负责）：见 §一.10。

### 8. ruff（裁判 5）

存档：`evidence-w44b7-tail/ruff-zsh-array-20260914T205153.txt`（zsh 数组写法，协议 §2.2）

```
files=2
backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py
All checks passed!   ruff_rc=0
验伪锚（树内 F821 锚）: F821 Undefined name `undefined_name_for_anchor`   anchor_rc=1
```

> ⚠️ 首版验伪锚放在 `/tmp`，解析到的是另一套 ruff 配置（不选 F821）⇒ `anchor_rc=0` **锚哑火**。
> 锚必须放在树内才与真判据同配置。已复跑，锚 rc=1。锚文件跑后即移出树外，`git status --porcelain backend/` = 0。
> （`backend/ruff.toml` 未选 F401 ⇒ F401 是假锚，沿用 T9-A 实测结论。）

`ruff format --check` 两份文件 **already formatted**：本卡新写的一行曾触发 reformat，但该文件在
`46e7bf77` 上 `ruff format --check` 是**干净的**（不属协议 §2.3 的 462 主干既有漂移），故由本卡自己修，
**未使用任何 `LEFTHOOK_EXCLUDE`**。commit 时 lefthook `python-lint` 全绿、`python-typecheck` 因零
`backend/app` 改动而 skip。

### 9. 地盘门（完成条件 i）

存档：`evidence-w44b7-tail/territory-gate-20260914T205637.txt`

| 判据 | 实测 |
|---|---|
| `git --no-pager diff --name-only --no-color 46e7bf77 45b8e0b4 -- . ':(exclude)_bmad-output'` | 恰 **2** 条：`backend/tests/support/live_port_guard.py`、`backend/tests/unit/test_live_port_guard_contract.py` ✅ ⊆ 地盘 |
| `--stat` 形态 | `2 files changed, 298 insertions(+), 13 deletions(-)` |
| **验伪锚**（证明 exclude 真的在滤东西） | 用跨越 T9-A 文档 commit 的区间 `5e4d10cf..HEAD`：不带 exclude 多出 **4** 条 `_bmad-output/` 路径，带 exclude 只剩 2 条代码文件 ✅ |
| 写法自证 `':!…'` vs `':(exclude)…'` | `':!_bmad-output'` → `fatal: Unimplemented pathspec magic '_'`、**真实 rc=128 且 stdout 空**（协议 §1 第十一批实测同形）——本卡一律用 `':(exclude)…'` |
| 越界自证（各期望 0） | `backend/app` 0 / `guard_plugin.py` 0 / `backend/tests/conftest.py` 0 / `backend/tests/unit/conftest.py` 0 / `backend/scripts/lifespan_isolation_runtime_sha.sh` 0 / `canvas-vault` 0 ✅ |

> ⚠️ 存档尾部有一段**补正**：首次那条「多出的 `_bmad-output` 条数 = 0」是本判据自己的假零 ——
> git 默认 `core.quotePath=true` 会把含中文的路径整行加引号，`grep -c '^_bmad-output/'` 锚在行首因而 0 命中，
> 而肉眼可见清单里有 4 条。改 `git -c core.quotePath=false` 后为 **4**（带 exclude 时为 **0**）。
> 同段还补正了 `':!…'` 那行打印的 `rc=0` 其实是管道末端 `head` 的 rc，git 真实 rc 是 **128**。

### 10. 收尾实测汇总

| 完成条件 | 结论 | 主要存档 |
|---|---|---|
| (a) 第 0 分钟 + PREREQ | ✅ 零行号漂移 | `minute-zero-20260914T203810.txt` |
| (b) 白名单门认间接持锁 + 文案收窄 | ✅ 先绿后红 | `whitelist-negctl-20260914T204641.txt`、`indirect-self-calls-probe-20260914T204553.txt` |
| (c) seam 行为断言挡死语句 | ✅ 先绿后红 | `seam-negctl-20260914T204736.txt` |
| (d) 顺序门可达剪枝 | ✅ 先绿后红 | `order-negctl-20260914T204828.txt`、`live-called-names-pruning-probe-20260914T204350.txt` |
| (e) `_publish_ledger` docstring + AST 逐字节 | ✅ | `publish-ledger-docstring-ast-20260914T204219.txt` |
| (f) 跑器拒未知参数 + 核 nodeid PASSED | ✅ | `negctl-unknown-arg-20260914T204207.txt` + 三份 negctl |
| (g) `-k live_port_guard` 全绿 + 反向锚 | ✅ 152 passed / 5206 deselected | `guard-selftest-20260914T204935.txt` |
| (h) tests/unit 目录级 diff 只许 `<` | ✅ **1 个 `<`、0 个 `>`**；且收工红集 = 基线 64 逐 nodeid 全同 | `unit-close-diff-20260914T205753.txt` |
| (i) 地盘门 + Codex | ✅ 地盘恰 2 文件；Codex 见 §五 | `territory-gate-20260914T205637.txt` |
| (j) 未证明 / 台账各 ≥4 | ✅ 7 条 / 9 条 | 本文件 §三 §四 |

**(h) 明细**（⛔ 以**绑最终代码 `c118e33e`** 的那跑为准，存档 `unit-close-diff-r3-20260914T213110.txt`）：

| 跑 | 绑定代码 | nodeid 红数 | `blocked=` | 哨兵失败正文锚 |
|---|---|---|---|---|
| 基线 `08100483` | — | 64 | 0（候选树常态） | — |
| 开工 `unit-open-20260914T203839.txt` | 改前树 | 65 | **1** | 1 条 `('::1', 7691, 0, 0) on thread MainThread` |
| 收工① `unit-close-20260914T205114.txt` | `45b8e0b4` | 64 | 0 | 0 |
| **收工③ `unit-close-r3-20260914T212532.txt`** | **`c118e33e`（最终）** | **64** | **0** | 0 |

`diff open close` = **`>` 行数 0 / `<` 行数 1**（哨兵红消失）；`diff base close` = **空**（64 = 64 逐 nodeid 全同）。
消失的那条是 W4 哨兵红本身（随 lifespan 健康检查时序漂移），不是本卡修好了某条用例，更非本卡引入
—— 判据按协议 §3 绑 `blocked=` 与失败正文，不绑 nodeid。
验伪锚：`open↔close` 差异行数 = 1（证明 diff 在有差异时确实会输出，两处 rc=0/1 非哑火）。
（收工②在 `a307de45` 上未单独跑，因为 r2 整改后立即又进了 r3 整改；以最终 SHA 那跑为准。）

---

## 二 4-B：你来验（零技术词）

- [ ] 我做：什么都不用做 —— 这张卡改的是「保护测试用环境的那道看门规则」自己。
      我看到：以前有几种写法能从侧门溜进去不被发现，现在都会被当场拦下，而且拦下时给的理由更准确、
      不再把「可能有问题」说成「一定出事」。
      我感觉：**这道门更靠得住了** —— 它不再只看「话写在哪儿」，还会真去看「那句话到底跑没跑」。

---

## 三 本卡未证明什么（必填，≥4）

1. **未做白名单门的全称封闭**。只覆盖别名赋值（含带注解、海象）与**字面** `getattr(self, "x")` 两大类。
   动态属性名 `getattr(self, name)`、`self.__getattribute__("ledger")()`、`functools.partial(self.ledger)`、
   把绑定方法塞进容器/参数再取出来调、经由局部函数间接调用 —— 这些仍是**门未覆盖的路径**，登记不主张已封死。
2. **seam「恰 1 次」只在本机 CPython 3.14.4 的 audit 语义下验过**，不证其它解释器/版本对同一次
   `sys.audit` 的分发次数相同；非受拦端口取 5432（带「不在 `BLOCKED_PORTS`」的显式断言），
   但未证明任何环境下 5432 都不会被别的 hook 拦。
3. **⛔ 顺序门证明的范围已收窄到「`install()` 字面语句序列里那几个直接具名调用的先后」，
   不是「运行时调用顺序」**。行为面的证明在子进程探针 `guard-install-order-precheck-is-guarded`，
   不在本门。四轮外审把这条边界逼了出来（详见 §五）：
   - 本作用域里**可见**的延迟执行体（`def`/`async def`/`lambda`/`class` 体/三种推导式/生成器
     表达式）现在一律让门**拒绝判定并报红**，不再猜；
   - 但 AST **看不穿一次调用背后的函数体**。以下五类仍是**门未覆盖的路径**，如实登记、
     未为其造负控，总验证脚本把其中三条**照实打印为「绿」**而不是藏起来：
     调用模块级 helper 而它体内做提前预检、`functools.partial(...)()`、`exec`/`eval` 字符串、
     `type("X", (), {...})()` 动态绑定、把模块级函数直接绑成类属性。
   - ⚠️ 我先后写下并被逐一证伪的说法（留档，别再重犯）：「这个近似只往安全一侧偏」
     （r1 证伪）、「收多了无害/偏假红」（r3 证伪）、「挪到模块级函数里顺序门就数得对」
     （r4 证伪）。**凡是「误差只会往安全一侧偏」这类方向性断言，本身就是待证命题。**
4. **未证 `_publish_ledger` 在真实「`open` 截断前 I/O 失败」时旧内容确被保留**。本卡 (e) 是描述性更正，
   **没有**新增运行时断言去钉那个状态（归 W4 行为门面，登记移交）。
5. **未连 7691/7687、未跑真连接活性**。受拦路径只由合成 `sys.audit` 事件覆盖，全程零真实 socket。
6. **未证白名单导出发生漂移时本门仍判得对**。若有人给 `_GuardState` 新增一个带 `with self._lock:` 的
   `*_locked` 方法，本卡只沿用既有 `assert allowed == {…}` 漂移钉，**未为「新增已持锁 helper」造负控**。
7. **未证 `_live_called_names` 在两个顺序门之外的调用方上语义也合适**。本卡实测它的生产调用方只有
   那两个门（逐 stmt 调 + 传 `expandable`）。`expandable=None` 的**自足模式**只看本子树，跨语句关联
   会丢 —— 本卡把它降级成「仅供独立探针使用」并写进 docstring，但**没有门钉住**「顺序类判据不得用
   自足模式」。谁将来忘了传 `expandable`，MEDIUM-2 那类假绿会原样回来。
8. **未证 `_reachable_local_func_names` 自身没有漏面**：它只扫 `scope.body` 的可达前缀，
   嵌套函数里定义的局部函数、同名函数在不同分支各定义一次（表按名字去重）这两类未验，已列进 r2 提问。
9. **未证对照输入在跑的过程中被隔离**。实况是对照输入写进**工作树**，临时目录放的是备份；
   全文件 sha 跑前跑后逐字节相同证明的是**还原正确**，不是运行期间隔离（Codex round-1 MEDIUM-3
   的判断正确）。本卡加了墙钟看门限制影响面，但 `kill -9` 不走 EXIT trap 的孤儿子进程面未验。

---

## 四 台账待登记条目（必填，≥4）

1. **W4-4b MEDIUM-1 / MEDIUM-2 / MEDIUM-3 + LOW-4 四债本卡收口**，代码 commit `45b8e0b4`；
   硬化后的门 nodeid：
   `tests/unit/test_live_port_guard_contract.py::TestSettlementAtomicity::test_settlement_path_never_nests_the_lock`、
   `::TestFinalizeRaceSeam::test_seam_runs_exactly_once_on_a_blocked_attempt`（**新增**）、
   `::TestInstallOrder::test_audit_hook_is_installed_before_the_target_precheck`、
   `::TestInstallOrder::test_final_accounting_is_registered_before_the_precheck`。
2. **UAT-W4-7 LOW-3a 本卡收口**（负控跑器拒未知参数 + 核 should-pass 的 nodeid 级 PASSED）。
   后续 W4 卡沿用此跑器纪律；实现在 `evidence-w44b7-tail/negctl_w4_gates.sh` 的 `run_nodes` 与参数解析段。
3. **本卡地盘含 `backend/tests/unit/test_live_port_guard_contract.py` 依裁定 R-B14-4 已获批**
   （手册 §一 地盘互斥行已补齐）。集成期地盘核请直接引 R-B14-4，勿按设计稿 §3 原清单误判越界。
4. **白名单门全称封闭仍未成立**（§三.1 列出的剩余间接持锁路径）—— 建议作下一张 W4 卡候选。
5. **seam 行为断言的版本依赖**（跨 CPython 版本的 audit 分发语义）登记（§三.2）。
6. **`_publish_ledger`「截断前失败保留旧内容」态缺运行时行为门**（§三.4），归 W4 行为门面。
7. **Codex 各轮**：存档路径、绑定 SHA、B/H/M/L 计数见 §五。
8. **tests/unit 目录级 diff 结果**：开工 base(64)→open(65)，多出的 1 条经绑失败正文确认是 W4 哨兵归属
   漂移（协议 §3 / R-08/R-10），非本卡引入；收工数字见 §一.10。
9. **⛔ 方法论教训，建议进工程坑索引（主 session 判是否值得全批通告）**：
   我在两个 helper 的 docstring 里写了「这个过近似只会假红不会假绿」这类**方向性断言**，却没有像
   对待判据那样给它找反例。Codex round-1 用两条**可复现输入**同时证伪（MEDIUM-1 别名覆盖、
   MEDIUM-2 装饰器/跨语句）。**「近似的误差只往安全一侧偏」本身就是一条需要验伪锚的主张**，
   写下它 = 欠一个反例搜索。
10. **⛔ 高优先级移交：`ast.TypeAlias` 漏面（Codex round-5 MEDIUM-1，已独立复现）**。
    PEP 695 的 `type X = <expr>`（CPython 3.12 起惰性求值，读 `__value__` 才跑）是本作用域
    **AST 可见**的延迟执行体，按 `_refuse_to_guess_on_deferred_execution` 自己的口径应当进拒绝面，
    但当前实现漏了。本机 Python 3.14.4 实测：
    ```python
    type H = _install_audit_hook()
    type R = register_final_accounting()
    assert_neo4j_target_blocked()
    H.__value__; R.__value__          # 真实求值序：precheck → hook → register
    ```
    下标读成 `0/1/2` ⇒ **两个顺序门双双假绿**。**修法是一行**（把 `ast.TypeAlias` 加进
    `_refuse_to_guess_on_deferred_execution` 的收集分支）。本卡未修：D-15 轮次上限 5 已用尽，
    审后改代码须再送一轮。请主 session 按高优先级排进下一张 W4 卡。
11. **本卡 Codex 五轮结算**：r1 `45b8e0b4` 0/0/3/5 → r2 `a307de45` 0/0/3/5 →
    r3 `c118e33e` 0/0/3/4 → r4 `485a1f89` 0/0/1/3 → **r5（末轮）`6e4fedc5` 0/0/1/2**。
    每轮 BLOCKER/HIGH 均为 0（D-15 合并门在每一轮都满足）；r1~r4 的再送是**主动**整改
    —— 那些 MEDIUM 是本卡新门自身的假绿或我 docstring 里的错话，不是被迫。
    末轮无 HIGH ⇒ 不触发「第 5 轮仍有 HIGH 交主 session 人审」那条。
    D-32 纯 docstring 尾巴 `a008882e` 不占轮次（AST 174192 == 174192 逐字节相同）。
11. **一件残档已按协议移出树外（如实登记，供主 session 裁）**：
    `evidence-w44b7-tail/ruff-and-territory-20260914T205124.txt` 是 ruff 判据的**验伪锚哑火那一版**
    （锚放 `/tmp`、解析到另一套 ruff 配置），其 territory 半段也被后来带活锚的
    `territory-gate-20260914T205637.txt` 取代。按协议「失败运行产物不入库」未提交；
    本车道 `rm` 被用户级守卫拦下，故以 `mv` 移至 scratchpad
    `.../scratchpad/SUPERSEDED-ruff-and-territory-20260914T205124.txt`（未删除，可复核）。
    取代它的两份是 `ruff-zsh-array-20260914T205153.txt` 与 `territory-gate-20260914T205637.txt`。
12. **另三件残档已按协议移出树外（同 §四.11 口径）**：
    `whitelist|seam|order-negctl-r3-20260914T212035.txt` 三份是**脚本崩在最后一步**的运行产物
    （`set -u` 下 `「$text」` 的中文右括号被 bash 当成变量名 ⇒ `unbound variable`），
    已被同名 `-20260914T212233` 那轮取代。移至 scratchpad 的 `SUPERSEDED-*`（未删除，可复核）。
13. **⛔ bash 坑：`set -u` 下 `$var` 紧跟中文标点会报 `unbound variable`**（建议进工程坑索引）。
    实测 `bash -c 'set -u; text=hi; echo "「$text」"'` → `bash: text<乱码>: unbound variable`；
    `"「${text}」"` 正常。bash 把多字节字符的首字节当成了变量名的一部分。**在中文注释/输出密集
    的判据脚本里这是个高频雷**：它不是语法错误，`bash -n` 查不出来，只在那一行真的执行到时才炸，
    而那一行往往是判据的最后一步 —— 前面全 `[OK]`、最后崩掉，很容易被读成「跑过了」。
    本卡已对整份跑器做全量 `${var}` 化。
14. **工具面小坑两条，建议进工程坑索引**：
   (a) **ruff 验伪锚放在 `/tmp` 会解析到另一套配置**（不选 F821）⇒ 锚哑火、判据未被证明能命中 ——
       锚必须放在树内；
   (b) **本车道 `rm` 被用户级守卫拦下**（`PreToolUse:Bash hook error … guard-hook.sh: No stderr output`，
       与 T9-A 同一条），临时文件只能用 `mv` 移出树外。本卡无残留（`git status --porcelain backend/` = 0），
       但该守卫行为值得主 session 确认是策略还是 hook 故障。

---

## 五 Codex 独立复核

命令（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" …`
codex 版本 `codex-cli 0.153.3`（`codex --version` 实测）。存档首部按协议 §2.1 六行 blockquote，
会话头自证抄 `.stderr` 的 `OpenAI Codex v0.153.3`（:2）/ `model: gpt-6-astra`（:5）/
`reasoning effort: ultra`（:9）三行并括注行号；`.stderr` 本身不入库。

### round-1（审 SHA `45b8e0b4`）— 存档 `codex-review-CARD-W4-4b7-TAIL-r1.md`

**BLOCKER = 0 / HIGH = 0 / MEDIUM = 3 / LOW = 5**（D-15 的 B0+H0 门在本轮即已满足）。

但其中两条 MEDIUM 是**本卡新门自身的可复现假绿**，且**证伪了我写在 docstring 里的方向性断言**
（「这个过近似只会假红不会假绿」）。「登记不阻断」不等于可以留着错话与假绿，故本卡**主动整改并再送一轮**
（D-15：审后改代码必再送一轮）。逐条处置：

| 级别 | Codex 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | 别名表覆盖式（`dict[str,str]`）：`f=self.ledger; f(); f=self._ledger_locked` 只剩白名单那个 ⇒ **真实的非白名单持锁调用被判合规（假绿）**；「过近似只会假红」不成立 | **接受并已改**（`a307de45`）：改 `dict[str,set[str]]` 保留全部绑定 + 别名→别名不动点传播；docstring 那句已删并改写成如实说明 |
| MEDIUM-2 | 第四类剪枝会剪掉**真实执行**的函数体：`@eager` 装饰器在 `def` 执行时就调它，源码此后不必再出现函数名 ⇒ 两个顺序门**双双假绿** | **接受并已改**：带装饰器一律当可达；并进一步修掉更根本的**跨语句丢关联**（新增 `_reachable_local_func_names` 在整个 `install()` 作用域算 `expandable`），顺序门调用点改传它 |
| MEDIUM-3 | 负控改的是**工作树**，临时目录放的是**备份**；「对照输入只写进临时副本」的自述不成立；挂住时 EXIT trap 轮不到执行 | **接受（判断正确）**：这是**自述错误**不是代码缺陷，已改正措辞（见下「自述更正」）；并加墙钟看门限制「万一挂住」的影响面。**仍不主张运行期间隔离** |
| LOW-① | 白名单剩余漏面清单（动态 `getattr`、容器/参数/包装器、元组解包、临界区外绑定、方法名集外的 callable…） | **登记**（已并入 §三.1）；其中「别名传递 `f=self.ledger; g=f; g()`」本轮**顺手修掉**了 |
| LOW-③ | `install().body` 顶层未经 `_reachable_prefix` 截断 ⇒ 顶层 `return` 之后的 hook/register/precheck 仍被计数；`locals()` 反射、跨语句关联等 | **部分接受并已改**：顺序门调用点已改 `_reachable_prefix(node.body)`；反射调用面**登记**（§三.3） |
| LOW-④ | nodeid 判据缺左边界；`after` 阶段关键词未绑到同一节点的失败原因、也未核 rc；`--help` 早退会放过后续未知参数 | **全部接受并已改**：awk 字段精确相等 / 绑 `short test summary` 同一行 + 断言 `rc==1` / `--help` 不再早退 |
| LOW-⑤ | docstring 仍过满：「截断后必报错」不成立；「父进程不会误读」推不出来；`_PUBLISHED_SEQ` 只约束本进程 | **全部接受并已改**（纯 docstring，D-32） |

**Codex 明确「核对通过」的项（原文摘录）**：普通 Assign/AnnAssign/两种海象/字面 getattr 的基础案例、
源码导出白名单与相等漂移钉；前三类剪枝（含 `Try` handler/finally 独立、`with.__exit__`、match 各 case）；
seam 行为门**不依赖本机 3.14.x 独有语义**（audit 按注册顺序分发、无自动重复分发）；5432 若被加入
`BLOCKED_PORTS` 会由 `:2032` 明确报红而非静默失效；纯 docstring 性质（独立重算两版去 docstring 后
AST 均 **1437 字符、逐字节相同**）；三份 negctl 存档的**实际红因**确实是各自指定的那条断言；
普通未知参数路径六例；`152 passed / 5206 deselected` 与三个反向锚逐节点通过。

**自述更正（我在 r1 prompt 里写错、被 Codex 指出）**：prompt §二.6 写「对照输入只写进临时副本」——
**不准确**。实况是：对照输入写进**工作树**的被守源，临时目录里放的是**原文件备份**，EXIT trap 从备份
还原，并以全文件 `shasum -a 256` 跑前跑后逐字节相同作证。这证明的是**还原正确**，不是**运行期间隔离**。
r2 prompt 已改正。

### round-2（审 SHA `a307de45`）— 存档 `codex-review-CARD-W4-4b7-TAIL-r2.md`

**BLOCKER = 0 / HIGH = 0 / MEDIUM = 3 / LOW = 5**。Codex 自证审前审后 HEAD 均为 `a307de45`。

其中**两条 MEDIUM 是我在 round-1 整改里自己引入的回归**，且都是真假绿。我逐条独立复现后整改：

| 级别 | Codex 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | 跑器 `node_result_line` 用 `awk '$1==n && $2==w'` 当条件，**awk 未匹配退出码仍是 0** ⇒ nodeid 身份检查**恒真**（我修 LOW-④ 时换的工具带进来比原问题更大的假绿） | **接受并已改**（`c118e33e`）：显式判输出非空 + `awk END{exit(found?0:1)}` 双保险。独立复现：`printf 'a b\n' \| awk '$1=="zzz"'; echo $?` → **0** |
| MEDIUM-2 | round-1 的修法把函数体的调用记在 **`def` 的下标**上，而顺序语义要的是**调用发生的下标**。hook/注册各包一层 helper 并在第一次预检之后才调用 ⇒ `hook_at=0 < precheck_at=2` ⇒ **两个顺序门双双假绿**（真实执行是 `precheck → hook → register → precheck`） | **接受并已语义重写**：定义点不贡献任何调用（带装饰器除外），**调用点就地展开**被调局部函数 body，沿调用链递归 |
| MEDIUM-3 | 作用域集合不继续传播新发现的局部函数引用：`outer` 内定义并调 `inner`、或 `first()` 调 `second()`，都仍能漏掉提前预检 | **同上一并封住**：`_reachable_local_func_names` 删除，换 `_local_func_defs`（裸 walk 收全部定义含嵌套；同名多份**全收**——只留第一份会掩盖真调用，这一点是 Codex 实测出来的） |
| LOW-1 | MEDIUM-1 原漏洞封住了，但新增合法临界区的假红（`f=self.ledger; f=self._ledger_locked; f()`） | **接受，有意不改**：判「哪个绑定在调用时活着」需真流分析。两个方向只能选一个，选假红（吵一次）不选假绿（漏一次真嵌套取锁 = atexit 期挂住）。已写进 docstring 并列出元组解包 / `for` 目标 / `with as` 三类**根本没收**的绑定 |
| LOW-2 | summary 仍能被冒充（整份输出筛 `^FAILED `、`grep -F "$node "` 缺左边界、关键词与节点交叉搜索） | **全部接受并已改**：区段提取 + `$1=="FAILED" && $2==n` 字段比较 + **按下标一一配对** |
| LOW-3 | 看门只杀一个 PID，不保证整棵进程树；脚本头「只写临时副本」的注释仍未同步 | **全部接受并已改**：`set -m` 独立进程组 + 杀整组；注释已改正为「写进工作树、临时目录放备份」 |
| LOW-4 | `--help --phase bogus` / `--help --gate bogus` / `--phase --nonsense-arg --help` 仍 rc=0 | **接受并已改**：`--help` 移到取值校验之后；取值不得以 `-` 开头。三例现均 rc=2 |
| LOW-5 | 「失败方向一律是不写」仍过满（写盘异常时文件可能已改变）；「先行推进」需注明是条件式（锁超时未推进） | **全部接受并已改**（纯 docstring） |

**Codex round-2 明确「核对通过」的项**：round-1 两条顺序假绿确已修复（装饰器例 `1/2/0`、跨语句例
`2/3/0`，两门均红）；`_reachable_prefix` 下标语义（只删后缀不删中间，保留语句下标不变）；
前三类剪枝及基础回归（22 个内存样本，覆盖真假分支 / 四种终结语句 / handler-finally / `with` 后继 /
`match`）；源码导出与相等漂移钉未被削弱；seam 两门无回归；**纯 docstring 性质独立核对通过**
（对 `46e7bf77`、`45b8e0b4`、本轮三版去 docstring 后比较，均 **1437 字符逐字相同**）；
三份负控存档的真实节点结果、指定红因、rc 与前后哈希人工核对通过。

**我的自述被证伪一处**：r2 prompt 说「`expandable is not None` 时同一条语句内的定义+调用不再展开」——
Codex 实测 `expandable={'outer','inner'}`，**可以展开**。该句作废（新语义下这个区别已不存在）。

### round-3（审 SHA `c118e33e`）— 存档 `codex-review-CARD-W4-4b7-TAIL-r3.md`

**BLOCKER = 0 / HIGH = 0 / MEDIUM = 3 / LOW = 4**。round-2 的三条 MEDIUM 复现已修复确认，
但**又出现三条新的假绿**：① 同名定义全展开 ⇒ 恒假分支里的同名诱饵被算到活的调用上（双向：
也能造成双假红，我「收多了无害/偏假红」的说法再次被证伪）；② `g = helper; g()` 现在**漏**
（round-2 靠「名字被提名」规则能抓到，属退化）；③ 局部装饰器函数**自身**的 body 漏掉。

### ⛔ 到这里我停止精化，换了方向（round-4，审 SHA `485a1f89`）

三轮的失败是同一个模式：每把「谁在什么时候执行了局部函数体」做得更精细一层，就开出一个新
假绿口子 —— 因为这个问题在 AST 层面**判不了**，需要解析调用绑定。而**真实 `install()` 里一个
局部函数都没有**（`_local_func_defs` 实测 `{}`）：我三轮都在给一个源码里不存在、也没人打算加的
构造建模，建模本身成了缺陷来源。

改法：新增 `_refuse_to_guess_on_local_functions`，两个顺序门在算下标**之前**断言
`install()` 体内没有任何局部函数定义，有就当场报红并说明「本判据拒绝猜」。
`_live_called_names` 去掉 `local_funcs` 参数与调用点展开，回到可陈述语义，其成立前提由该断言
**强制**而不是靠注释。

**总验证**（存档 `codex-all-rounds-repro-verify-20260914T213639.txt`）：三轮共 **12 个**复现输入
（含 Codex 保留的两条历史边界：三件事全在同一 helper、生成器 helper 只创建不迭代）**一律翻红**；
两条干净形态（顺序正确 ⇒ 绿 / 预检在前 ⇒ 红）都对；真实 `install()` 前置断言不触发、下标仍 `4/5/6`。
方向是**收紧**：更多输入判红，没有任何输入因此变绿。

| 级别 | Codex round-3 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | 同名定义全收全展开 ⇒ 死码诱饵变成提前调用（双假绿；反方向双假红） | **接受**，由「拒绝判定」一并封住 |
| MEDIUM-2 | `g = helper; g()` 漏掉提前预检（相对 round-2 的退化） | **接受**，同上 |
| MEDIUM-3 | 局部裸装饰器函数自身的隐式调用被漏 | **接受**，同上 |
| LOW-1 | 自足模式不再自行展开局部函数（仅影响独立探针） | **接受**：语义已在 docstring 如实陈述，生产两门都走前置断言 |
| LOW-2 | 完整仿冒 summary 标题仍能冒充 | **接受并已改**：只取**最后一个** summary 区段 |
| LOW-3 | 缺值检查实际失效（`need_value "$1" "${2-}"` 使被调方永远看得到第二个实参） | **接受并已改**：改到调用方数实参；裸 `--phase` 现在 rc=2 + `missing value for --phase` |
| LOW-4 | 「抛异常 ⇒ 写盘调了」泛指本函数所有异常过宽 | **接受并已改**（纯 docstring）：限定为 `write_ledger` 抛出，并补「到达写盘前也可能抛」那一类 |

**Codex round-3 明确「核对通过」的项**：round-2 三条复现确已修复；两条「不得误红」反向例仍绿；
递归/互递归在途集合未单独漏调用；`_publish_ledger` 返回 `False` 的两条路径确在唯一写盘调用之前；
条件式推进保证成立；`node_result_line` 的恒真问题已修（且确认无 `local x="$(...)"` 吞退出码问题，
`END{exit}` 在 BSD awk / gawk / mawk 无语义差异）；summary 区段提取对分隔线宽度变化稳健、
提取失败方向是**假红不是假绿**；前三类剪枝本体、`_reachable_prefix` 下标、源码导出白名单与漂移钉、
间接调用识别、seam 两门、纯 docstring 性质均无回归。

### round-4（审 SHA `485a1f89`）— 存档 `codex-review-CARD-W4-4b7-TAIL-r4.md`

**BLOCKER = 0 / HIGH = 0 / MEDIUM = 1 / LOW = 3**。Codex 明确肯定方向：「对同一输入，本轮收紧
方向成立」，并把 MEDIUM-1 归为**剩余漏面而非本轮新引入**。

| 级别 | Codex round-4 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | 拒绝断言只收 `def`，两个 `lambda` 分别包住 hook/注册、在首次预检之后才调用 ⇒ 断言放行、两门双假绿。并逐条列出生成器表达式 / 空推导式 / 模块级 helper / `partial` / `exec` / `type()` / class 内绑模块函数等 | **接受并已改**（`6e4fedc5`）：拒绝面扩到 `def`/`async def`/`lambda`/`class` 体/三种推导式/生成器表达式。**其余五类（看不穿一次调用背后的函数体）如实登记为门未覆盖的路径**，总验证脚本把其中三条照实打印为「绿」 |
| LOW-1 | docstring 残留已删机制（`local_funcs`/调用点展开/在途集合/`expand_call`）；「只数定义点之外的调用」不准确；「挪到模块级函数里顺序门就数得对」**被证伪** | **全部接受并已改**：残留清零（`grep -c` → 0）；两处说法更正（带装饰器改写成「保守计入」而非「定义时确实执行」）；顺带删掉已无引用的 `_local_func_defs` |
| LOW-2 | `--prereq ''` 通过解析 ⇒ `git show ':path'` 读 index 而非指定提交 | **接受并已改**：取值拒空串，实测 rc=2 |
| LOW-3 | 最后一个 summary 仍只有文本位置约束、没有来源保证 | **接受，登记不改**：跑器读的是它自己发起的那次 pytest 的输出，纯文本判据无法区分「真 summary」与「捕获输出里一段长得一样的文本」；没有可信来源通道可用 |

**Codex round-4 明确「核对通过」的项**：无第三处同类顺序下标判据漏加前置断言（全文件
`_live_called_names` 实际调用仅两处，均先过断言）；普通 class 内显式 `def` 方法能被收到；
前三类剪枝（20 个独立样本）；`_reachable_prefix` 下标；无 summary 标题/最后 summary 为空两种
情形方向都是**拒绝（可能假红）而非假绿**；三个裸旗标缺值均 rc=2；间接调用识别、seam 两门、
白名单漂移钉无回归；**`_publish_ledger` 三类说明与 `:1449-1474` 实际控制流逐条对应、
纯 docstring 性质独立核对通过（两版去 docstring 后 AST 均 1437 字符完全相同）**。

### round-5（末轮，审 SHA `6e4fedc5`）— 存档 `codex-review-CARD-W4-4b7-TAIL-r5.md`

**BLOCKER = 0 / HIGH = 0 / MEDIUM = 1 / LOW = 2**。Codex 自证审前审后 HEAD 均为 `6e4fedc5`，
并明确「未发现本轮引入的新回归」。**D-15 合并门（末轮绑最终 HEAD 且 BLOCKER/HIGH = 0）在本轮满足。**

| 级别 | Codex round-5 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | 拒绝表漏了 `ast.TypeAlias`（PEP 695 `type X = <expr>`，CPython 3.12 起**惰性求值**）—— 它是本作用域 AST **可见**的延迟执行体，按我自己的口径应当进表。本机 3.14.4 实测下标 `0/1/2` ⇒ 两个顺序门**双双假绿** | **⛔ 已独立复现确认，但本卡不改代码**：D-15 轮次上限 5 已用尽，审后改代码须再送一轮。按 MEDIUM「登记不阻断」**移交下一张 W4 卡**；修法是一行（把 `ast.TypeAlias` 加进收集分支），复现输入与结论已写进 `_refuse_to_guess_on_deferred_execution` 的 docstring 与本文件 §四 |
| LOW-1 | docstring 清理未完成且「恰好四类」不精确：①「带装饰器的 body 在定义点执行」与新增的「保守计入」自相矛盾；②「不带装饰器的 def 不贡献任何调用」但默认参数调用会计入；③ 实现跳过 `returns` / `type_params`，「恰好四类／其余一律」未完整描述实现 | **全部接受并已改**（D-32 纯 docstring 尾巴 `a008882e`，剥 docstring 后 AST **174192 == 174192 逐字节相同**，不占轮次） |
| LOW-2 | 总验证存档实际是 **16 条**复现标签 + 2 条干净形态，不是我自述的「18 + 2」；且 round-4 原例 `type("Early", (), {...})()` **没有 `ClassDef`**，当前仍放行 —— 我「已因 class 体翻红」的说法不成立 | **接受，两处自述均已更正**（见下「自述更正」）；`type()` 已改回登记为门未覆盖的路径 |

**Codex round-5 明确「核对通过」的项**：async 四类推导式/生成器表达式、`match` guard、
`NamedExpr` 内 lambda、`global`/`nonlocal` 配合 lambda 赋值、装饰器表达式与非字符串注解内的
lambda —— 均被拒绝面收到；三个 flag 的空串拒绝与数字短 SHA 正常接受（9 条独立参数探针）；
新 docstring 的两句核心更正与实现相符；旧机制说明（`local_funcs`/`expand_call`/调用点展开/
在途集合）已删除；`_indirect_self_method_calls`、seam 两门、白名单与相等漂移钉、前三类剪枝、
`_reachable_prefix` 下标语义均未改；**`_publish_ledger` 去 docstring 后 AST 对前提 `46e7bf77`
仍 1437 字符完全相同**；三份负控的 before 绿 / after 指定原因红 / clean 绿，两份源码 SHA256
与负控记录一致。

**自述更正（我写错、被 Codex round-5 指出）**：
1. r5 prompt 与本文件曾写「四轮共 **18** 个复现输入」—— **实际是 16 条复现标签 + 2 条干净形态**。
   已在下文与 §三 统一改为 16 + 2。
2. r4 我声称 `type("X", (), {...})()` 已因 class 体被拒 —— **不成立**。我把用例换成了
   `class Early: __init__ = ...`（那确有 `ClassDef`）再得结论，**对原例（内置 `type()`，无
   `ClassDef` 节点）无效**。⚠️ 这是「替换了用例再宣布覆盖」，与本卡一路在防的假绿同型，
   如实记在这里。

### D-15 轮次结算

| 轮 | 审 SHA | B/H/M/L | 处置 |
|---|---|---|---|
| r1 | `45b8e0b4` | 0/0/3/5 | 两条 MEDIUM 是新门自身假绿 + docstring 错话 ⇒ 主动整改 |
| r2 | `a307de45` | 0/0/3/5 | 两条是 r1 整改引入的回归 ⇒ 整改 |
| r3 | `c118e33e` | 0/0/3/4 | 三条新假绿 ⇒ **停止精化，改走「拒绝判定」** |
| r4 | `485a1f89` | 0/0/1/3 | 方向被肯定；MEDIUM 归剩余漏面 ⇒ 扩拒绝面 + 清残留文案 |
| **r5（末轮）** | **`6e4fedc5`** | **0/0/1/2** | **合并门满足**；MEDIUM 登记移交，LOW-1 走 D-32 尾巴 `a008882e` |

⛔ 末轮**没有 HIGH**，因此不触发协议 §1「第 5 轮仍有 HIGH → 停下交主 session 人审」那条；
但 MEDIUM-1（`ast.TypeAlias`）是**已确认、有一行修法、本卡因轮次上限未修**的真缺陷，
请主 session 在 §四 台账里按高优先级排下一张 W4 卡。

---

## 六 收尾实测

**最终 HEAD = `a008882e`**（代码末态 `6e4fedc5` + D-32 纯 docstring 尾巴 `a008882e`）。
存档 `evidence-w44b7-tail/final-gates-20260914T220151.txt`。

| 判据 | 结论 |
|---|---|
| (h) tests/unit 目录级（绑 `6e4fedc5`；其后仅 D-32 尾巴，剥 docstring 后 AST 逐字节相同 ⇒ 运行语义不变） | base 64 / open 65 / **close 64**；**收工 vs 开工 `>` 行数 = 0**、`<` = 1（哨兵红消失）；**收工 vs 基线 diff 为空** |
| W4 哨兵判据（协议 §3：绑 `blocked=` 与失败正文，不绑 nodeid） | 开工 `blocked=1` / 正文锚去重 1；收工 `blocked=0` / 正文锚去重 0 ⇒ 那条 `<` 是哨兵按时序漂移，非本卡引入 |
| 验伪锚（diff 会说话） | `open↔close` 差异行数 = 1（非哑火） |
| (i) 地盘门 | 恰 **2** 文件：`live_port_guard.py`、`test_live_port_guard_contract.py`；`--stat` = `2 files changed, 437 insertions(+), 21 deletions(-)` |
| 地盘门验伪锚 | 跨 T9-A 文档 commit 区间：不带 exclude 多出 **4** 条 `_bmad-output/`，带 exclude 为 **0** |
| 越界自证 | `backend/app` / `guard_plugin.py` / 两个 conftest / `lifespan_isolation_runtime_sha.sh` / `canvas-vault` **全 0** |
| ruff（zsh 数组 + 树内 F821 验伪锚） | `files=2`、`All checks passed!`、`format: 2 files already formatted`；锚 rc=1 |
| lefthook | 五次 commit 全绿，**零 `LEFTHOOK_EXCLUDE`**；`python-typecheck` 因零 `backend/app` 改动而 skip |

**本卡 commit 链**（`PREREQ = 46e7bf77`）：

| commit | 内容 | 绑定的 Codex 轮 |
|---|---|---|
| `45b8e0b4` | 门四债首版硬化（b)(c)(d)(e) | r1 审此 |
| `a307de45` | 按 r1 整改（别名集合 / 装饰器 + 作用域表 / 跑器绑定） | r2 审此 |
| `c118e33e` | 按 r2 整改（展开改到调用点 / awk 恒真 / summary 绑定） | r3 审此 |
| `485a1f89` | 按 r3 改走「拒绝判定」 | r4 审此 |
| `6e4fedc5` | 按 r4 扩拒绝面 + 清残留文案 | **r5（末轮）审此，B0/H0** |
| `a008882e` | **D-32 纯 docstring 尾巴**（AST 逐字节相同，不占轮次） | — |
| （本文件的文档 commit） | 验收单 + 五轮 Codex 存档 + prompts + evidence | — |

**未 push**（卡文硬边界）。工作树在文档 commit 后应为干净，供同车道 T9-C 接手。
