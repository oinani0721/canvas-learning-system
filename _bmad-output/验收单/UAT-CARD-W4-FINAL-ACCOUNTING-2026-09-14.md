# UAT — CARD-W4-FINAL-ACCOUNTING（W4 守卫最终结账：落盘失败 print 移入退出保护块）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-W4-FINAL-ACCOUNTING]` · 车道 `card-t9-w4`（分支 `card/t9-w4`，本车道第 1/4 张）
> 基线 `08100483`（B14_BASE）→ 本卡 commit **`5e4d10cf`**（未 push）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T9-A.md`（feature 主干树）
> 裁定依据 **R-11**（U7-A 外审 HIGH-1「`_final_accounting` 落盘失败 print 在退出保护块外、rc=0 假绿」→ 登记 TAIL 高优先 = 第十四批、人判合入）
> 判据存档一律在 `_bmad-output/审查/evidence-w4final/`；本单只**引用路径与实测行**，不自述数字。

---

## 〇 第 0 分钟自证（完成条件 a）

| 项 | 实测 |
|---|---|
| `pwd` | `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4` ✅ |
| `git branch --show-current` | `card/t9-w4` ✅ |
| `git rev-parse --short=8 HEAD` | `08100483` ✅（= B14_BASE） |
| `git status --porcelain \| wc -l` | `0` ✅ |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 均在 ✅ |
| 基线 `grep -vc '^#' "$BASE"` | **64** ✅（`$BASE` = feature 主干树 `_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`） |
| `grep -c live_port_guard "$BASE"` | `0` ✅（基线不含本文件任何 nodeid） |

**手册地盘对齐核**（只读 feature 主干树那份 `2026-09-11-第十四批开跑手册-10车道43卡.md`）：**已对齐**。抄命中行——
- `:67` §一「只 T9」：`backend/tests/support/live_port_guard.py`、`guard_plugin.py`、`backend/tests/conftest.py`、`backend/tests/unit/conftest.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`（⚠️ 排批稿误写 `scripts/runtime_sha.sh`，实测不存在；裁定 **R-B14-5**）、`backend/tests/unit/test_live_port_guard_contract.py`（R-B14-4 扩充）
- `:44` / `:125` 车道表：T9 `card-t9-w4`，A CARD-W4-FINAL-ACCOUNTING → B → C → D

**§〇 事实逐条核**（无一漂移，全部与卡文逐字同）：

| 卡文事实 | 本树实测 |
|---|---|
| 文件 1575 行 | `wc -l` = **1575** ✅ |
| blob `d0f12093…` @ `08100483` | `git rev-parse HEAD:…` = `d0f12093105f1356214e0ca6faf5142c06b3a773` ✅ |
| 与 U7 车道树 sha 相同 | `shasum` = `e1988410c382a827cc412f28cc7f839e689b4a06` ✅（与卡文所记 U7 树 sha 逐字同） |
| `_final_accounting` = 1487–1535 | AST = `[('_final_accounting', 1487, 1535)]` ✅ |
| 缺陷锚 `grep -nF '账本落盘失败'` → `1512` 恰 1 行 | 实测 `1512:` 恰 1 行 ✅ |
| `:1504-1535` 原文 | `sed -n '1504,1535p'` 与卡文 §〇 逐字同 ✅ |
| guard API 锚 | `BLOCK_REASON :205` / `ENV_REQUIRE_BLOCKED_TARGET :219` / `ENV_LEDGER :222` / `FINAL_EXIT_CODE :225` / `record :308` / `finalize_and_snapshot :365` / `late_snapshot :379` / `_audit_hook :772` / `addaudithook :857` / `install :893` / `register_final_accounting :1361` / `_publish_ledger :1408` —— 全部与卡文逐字同 ✅ |
| `fsrs_bridge` / `decay_beta` 零关联 | `grep -c` = **0** ✅ |

---

## 一 4-A：Claude 已代验的技术证据

### 1. 先红（完成条件 b）— 在 HEAD 未改代码时先跑

**① AST 判据**（脚本 `evidence-w4final/ast-protected.py`，从车道树根跑）
存档：`evidence-w4final/ast-before-20260914T195111.txt`，`rc=0`

```
1512 UNPROTECTED
1523 protected
1530 protected
```

`grep -c UNPROTECTED` → **1**（恰 1 行未护，与卡文期望逐字同）。

**② 三跑 harness**（脚本 `evidence-w4final/three-run-abc.py`，从 `backend/` 跑）
存档：`evidence-w4final/three-run-before-20260914T195119.txt`，`rc=0`

```
A ledger=目录 + stderr 坏: rc=0 acct={'blocked': 1, 'unaccounted': 1}
B 只落盘失败（ledger=目录 + stderr 正常）: rc=3 acct={'blocked': 1, 'unaccounted': 1}
C 只 stderr 坏（ledger 正常 + stderr 坏）: rc=3 acct={'blocked': 1, 'unaccounted': 1}
sha-unchanged: True
PRECOND blocked/unaccounted all 1: True
A!=B,C: True
```

⇒ **缺陷复现于 A 格**（rc=0 假绿），且 B/C 恒 3 ⇒ 缺陷恰在「落盘失败 + stderr 坏」两条件**同时**成立那一格，不是随便坏一个就退不出去。三跑账本前提 `blocked=1 / unaccounted=1` 成立。

### 2. 修法（完成条件 c）— 只动 `:1511-1512` 的 `except Exception` 体

代码面 diff 全文（`git diff --no-color 08100483 5e4d10cf -- backend/tests/support/live_port_guard.py`，单 hunk，4 insertions / 1 deletion）：

```diff
@@ -1509,7 +1509,10 @@ def _final_accounting() -> None:
             # 更新的一份，这里不回写（MEDIUM-4 的陈旧覆盖）。
             _publish_ledger(path, ledger)
         except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账
-            print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
+            try:
+                print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
+            except BaseException:  # noqa: BLE001 —— 可观测性不得挡在强制退出前面
+                pass
     unaccounted = ledger["unaccounted"]
     blocked = ledger["blocked"]
     status = ledger["reported_status"]
```

- 与退出保护块（改前 `:1522-1534`）**同型**；文件 1575 → **1578** 行（净增 3）。
- **未动**：取快照 `:1504`、`_publish_ledger` 调用 `:1510`、`except Exception as exc:` 行本身 `:1511`、裁定分支 `:1519`、退出保护块 `:1522-1534`、`os._exit(FINAL_EXIT_CODE)` `:1535`、函数签名。结账 / 发布 / 退出语义一律未改。
- 严格照卡文 (c) 代码块落地，**未加额外注释行**（避免偏离「最小修法」并使卡文预测的 +1/+3/+3 位移失真）。

### 3. 后绿（完成条件 d）

**① AST** 存档：`evidence-w4final/ast-after-20260914T200544.txt`，`rc=0`

```
1513 protected
1526 protected
1533 protected
```

`grep -c UNPROTECTED` → **0**；`grep -c protected` → **3**。
`_final_accounting` 新范围 AST = `[('_final_accounting', 1487, 1538)]`。
⇒ 三个 print 各下移 **+1 / +3 / +3**、函数尾行 `1535 → 1538`，与卡文 (d) 的预测**逐字吻合**，无漂移需登记。

**② 三跑** 存档：`evidence-w4final/three-run-after-20260914T200549.txt`，`rc=0`

```
A ledger=目录 + stderr 坏: rc=3 acct={'blocked': 1, 'unaccounted': 1}
B 只落盘失败（ledger=目录 + stderr 正常）: rc=3 acct={'blocked': 1, 'unaccounted': 1}
C 只 stderr 坏（ledger 正常 + stderr 坏）: rc=3 acct={'blocked': 1, 'unaccounted': 1}
sha-unchanged: True
PRECOND blocked/unaccounted all 1: True
A!=B,C: False
```

⇒ **A 由 rc=0 翻到 rc=3**，B/C 恒 3，三跑账本前提仍 `blocked=1 / unaccounted=1`。
（`A!=B,C: False` 是修好后的**应然**——该行是先红阶段用来区分「缺陷恰在 A 格」的判别式，三格一致正说明假绿格已消失。）

### 4. 负控（完成条件 e，承重）

存档：`evidence-w4final/nc-negative-control-20260914T200618.txt`（单次 shell 调用内完成，`trap … EXIT` 无条件还原；⛔ 全程未用 `git stash`、未用 `git checkout`）
变异器：`evidence-w4final/nc-remove-protection.py`（严格是 (c) 的逆操作：`NEW → OLD`，恰 1 处命中，断言净变 −3 行，否则 `exit 2`）

| 步 | 实测 |
|---|---|
| [1] 变异前 sha（已修态） | `56c589ac66585f3566936bddd2a88708f24f3723db260cfa24ade1570a0fcbc5` |
| [2] 施加负控 | `NC mutated ok; 行数 1578 -> 1575` |
| [3] 变异体 vs 当时 `HEAD` blob（负控段执行于本卡 commit **之前**，当时 `HEAD` = **`08100483`** = B14_BASE） | **逐字节相同**（`diff -q` 通过）⇒ 证明负控恰是本次修法的精确逆操作，不多删也不少删。（Codex round-1 末段指出原存档只写「与 HEAD blob 相同」未绑当时 SHA，此处补齐；可由 `evidence-w4final/nc-negative-control-20260914T200618.txt` 的 `[2] 1578 -> 1575` 与本卡 diff 的 `4 insertions(+), 1 deletion(-)` 交叉复算） |
| [4] 判据① AST | 回到 **`1512 UNPROTECTED` / 1523 protected / 1530 protected**（恰 1 行未护）✅ 翻转 |
| [5] 判据② 三跑 | **A 回 rc=0**、B rc=3、C rc=3、`PRECOND … True`、`A!=B,C: True` ✅ 翻转 |
| [6][7] 显式还原后 sha | `56c589ac66585f3566936bddd2a88708f24f3723db260cfa24ade1570a0fcbc5` —— 与 [1] **逐字同** ✅ |
| [8] 还原后复核 AST | `1513 / 1526 / 1533` 全 protected，0 UNPROTECTED ✅ |

⇒ **两个判据都翻转**（只翻一个 = 判据没锁住缺陷）。判据非恒绿，承重成立。

### 5. guard 契约不回退（完成条件 f）

| 跑 | 存档 | 结果 |
|---|---|---|
| 开工 `test_live_port_guard_contract.py` | `evidence-w4final/contract-open-20260914T195128.txt` | **151 passed, 0 failed**，`rc=0` |
| 收工 同上 | `evidence-w4final/contract-close-20260914T200632.txt` | **151 passed, 0 failed**，`rc=0` |
| 收工 `tests/unit -k live_port_guard` | `evidence-w4final/unit-k-liveportguard-20260914T200632.txt` | **151 passed, 5206 deselected, 0 failed**，`rc=0` |

passed 数开工 = 收工 = **151**（本卡只把 print 护起来，未改结账 / 发布 / 退出语义，契约套件原样通过）。

### 6. tests/unit 目录级（完成条件 g）

承重文件名先固定成变量（⛔ 未用 glob），`$BASE` 取 feature 主干树基线 64 条。

| 跑 | 存档 | 汇总行 | nodeid 口径 diff |
|---|---|---|---|
| 开工 | `evidence-w4final/unit-open-20260914T195838.txt`（末行 `rc=1`） | `35 failed, 5077 passed, 48 skipped, 23 xfailed, 171 warnings, 29 errors in 362.70s` | `base.nodeids`(64) vs `open.nodeids`(64) → **diff 空**，`diff_rc=0` |
| 收工 | `evidence-w4final/unit-close-20260914T200714.txt`（末行 `rc=1`） | `35 failed, 5077 passed, 48 skipped, 23 xfailed, 171 warnings, 29 errors in 353.34s` | `base.nodeids`(64) vs `close.nodeids`(64) → **diff 空**，`diff_rc=0` |

⇒ **零 `>` 行**（无本卡引入的新红），也无 `<`（本卡不修红，预期如此）。
**验伪锚**（同次执行）：把 `base.nodeids` 首行改一字后 diff 立刻非空（`probe_diff_rc=1`）；把 `close.nodeids` 删一行后 diff 报出 `< ERROR tests/unit/test_agent_service_extraction.py::…` —— 证明该 diff 判据真能报差异、真能报 `<`，不是恒空。

> **存档卫生（如实记录）**：首次开工那跑命令误写成 `pytest … 2>&1 | tail -25 | tee $RUN.tail`，存档只落尾部 25 行，**无法做 nodeid 身份比对**（数量 35+29=64 虽与基线数量一致，但数量判据挡不住等长替换）。已按 §二.6 重跑完整存档（即上表 `unit-open-20260914T195838.txt`）。该截断产物按协议应剔除，但 `rm` 被用户级 `~/.claude/guard-hook.sh:20` 确定性阻断（删除文件需用户确认），故**未绕过**，改为就地改名为 `DISCARDED-unit-open-20260914T195156-truncated.txt` 并在文件头写明「⛔ 作废运行（不得作判据引用）」+ 原因 + 处置。**留给主 session 处置**（见「台账待登记」⑤）。

### 7. 地盘门（完成条件 h）

`git --no-pager diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'`：

```
 backend/tests/support/live_port_guard.py | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)
```

⇒ 代码文件 ⊆ {`backend/tests/support/live_port_guard.py`}，**仅此一个** ✅。零 `backend/app/**` 文件（未越界）。
**验伪锚**：同命令去掉 `':(exclude)_bmad-output'` → `20 files changed, 2938 insertions(+), 1 deletion(-)`，多出 `_bmad-output/…` 路径 ⇒ 证明 exclude 真在起作用。
存档：`evidence-w4final/gate-scope-ruff-20260914T201503.txt`

### 8. ruff（完成条件 k）

zsh 数组写法，从车道树根跑（同存档 `gate-scope-ruff-20260914T201503.txt`）：

```
files=1
list=backend/tests/support/live_port_guard.py
All checks passed!
rc_check=0
1 file already formatted
rc_fmt=0
```

**验伪锚（⛔ 用 F821，不用 F401）**，同次执行：

| 锚 | 实测 |
|---|---|
| `F821` 未定义名（stdin，不落盘） | `F821 Undefined name '_undefined_probe'` + `Found 1 error.`，**rc=1** ✅ 真在报 |
| `format --check` 劣构 `x = [1,2,\n 3]` | **rc=1** ✅ |
| `format --check` 良构 `x = [1, 2, 3]` | **rc=0** ✅（对照） |
| **假锚实证** `F401` 未用 import | `All checks passed!` **rc=0** ⇒ 证实卡文 §二.8 警告：`backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 不含 F401，拿它当锚会把「ruff 根本没在报」误读成「干净」 |
| 探针文件未落盘 | `test -e backend/tests/support/_probe.py` → **absent** ✅ |

本卡非 app 卡：`python-typecheck` glob = `backend/app/*.py`，本卡零 `backend/app` 改动 ⇒ 不触发，无「pyright 保持 0」义务；`python-lint`（ruff）glob = `{backend,src,scripts}/*.py`，本文件在命中集内，已保持绿（且本卡**未**使用 `LEFTHOOK_EXCLUDE`）。

### 9. 现网只读（完成条件 i）

哨兵 `evidence-w4final/sentinel` 建于开工（`Sep 14 19:50`）。存档：`evidence-w4final/readonly-live-20260914T201356.txt`

| 面 | `find … -type f -newer sentinel \| wc -l` |
|---|---|
| `canvas-learning-system/backend/data/lancedb`（现网，含 `vault_notes.lance` / `file_fingerprints.lance`） | **0** ✅ |
| `canvas-learning-system/data/lancedb`（现网，含 `canvas_vault_file_fingerprints.lance`） | **0** ✅ |
| `canvas-learning-system/canvas-vault/**`（live vault） | **0** ✅ |
| **验伪锚** `evidence-w4final/` 自身 | **18** ⇒ 证明 `find -newer` 真能报，不是恒 0 |

三跑 harness 的 ledger 路径全部由 `tempfile.TemporaryDirectory(prefix="w4final-")` 派生；harness **未设** `W4_GUARD_REQUIRE_BLOCKED_TARGET=1`、未设 `NEO4J_URI` / LanceDB 路径类环境变量；受拦事件由 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))` 合成，**不建立真实连接**；全程未连 7691 / 7687。`fsrs_bridge.py` / `decay_beta.py` 零关联（grep 0 命中）、零写。

---

## 二 4-B：用户侧一句话（零技术词）

以前这套自动检查在一种少见的巧合下会「假装通过」——明明有东西闯了禁区没记上账，它却照样报一切正常；更糟的是，连它想喊话的那个出口也同时坏掉了，于是它连喊都喊不出来，就那么悄无声息地放行了。现在就算喊话的出口坏了，它也一定会以「失败」收场，绝不蒙混过去。

**felt-sense**：像是发现家里最后那道防盗门在某个特定角度其实是虚掩的，而且报警器恰好也哑了——现在把它彻底焊实了。心里踏实，睡得着。

---

## 三 本卡未证明什么（必填，≥4）

① **未证明真实 Neo4j 拦截**：三跑用 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))` 合成受拦事件，全程不建立真实连接、不连 7691 / 7687。合成事件与真实 `socket.connect` 触发在记账路径上是否完全等价，本卡未独立验证。Codex round-1 **L3** 进一步精确化：现有证据覆盖的只是「合成审计事件 → 退出前 `late_snapshot()` 计数为 `1/1` → 组合故障下最终返回码」这条链，**退出前快照不等于最终快照的直接观测**；结论是「未证明等价」，**不是**「已证明不等价」。

② **未跑完整 7692 真库门**，也未证真实 atexit 迟到线程与 `_publish_ledger` 锁竞态下的行为。三跑是单线程、确定性的子进程对照。

③ **故障面只覆盖两类**：落盘失败只覆盖 `IsADirectoryError`（ledger 路径指向目录），stderr 坏态只覆盖「`io.StringIO` 已 `close()` 后替换 `sys.stderr`」这一种。**未覆盖**磁盘满 / 权限不足 / 路径中途消失等其它落盘失败，也未覆盖 stderr 半坏态（可写但 flush 失败、`BrokenPipeError` 管道对端已关等）。

④ **committed 测试套件未新增回归锁**：本卡的先红后绿只存在于 `evidence-w4final/` 的脚本里，**不在 CI 跑的 pytest 里**。契约套件 `test_live_port_guard_contract.py` 不覆盖 A 格（ledger=目录 + stderr 坏 ⇒ rc）。该 committed 锁按裁定 **R-B14-4** 属 **T9-B** 地盘，本卡只登记移交，⛔ 未自行扩面。

⑤ **未排查迟到路径的同型问题**：`_rewrite_ledger_after_late_record` 等迟到路径里的 print 是否也有同型未护，本卡只改 `_final_accounting`，未做全文件排查（已列为 Codex 问题⑤）。

⑥ **未评 W4 哨兵判据改绑**（T9-C 面）；未评 `guard_plugin.py` / 两个 conftest（T9-C 地盘）与 `lifespan_isolation_runtime_sha.sh`（T9-D 地盘）。

⑦ **未证明「可观测性降级可接受」是一项产品判断**：本卡把该 print 的异常就地吞掉（与改前 `:1534` 同语义）。在 stderr 正常时落盘失败仍照常打印（B 格实测 rc=3 且流程走完），但「stderr 坏 + 落盘失败」这一格从此彻底无声——这是刻意取舍，未做用户侧确认。

⑧ **未排他证明 rc=3 来自哪个退出调用点**（Codex round-1 **L2**）：三跑只记录返回码与退出前计数，未记录执行到哪个退出调用点。单 hunk + A 格负控翻转 + `:1522`（改后）裁定分支的控制流「**强支持**」最终执行的是改后 `:1538` 的 `os._exit(FINAL_EXIT_CODE)`，但这是推断而非运行时排他证明。（`CHILD-JSON` 已输出 ⇒ 至少排除了「合成事件发生当时就提前退出」。）

⑨ **本卡 AST 判据存在已知盲区，未加固**（Codex round-1 **L1**）：判据只看「print 行号落在某个 `try` 的 `lineno..end_lineno` 区间」+「该 try 带 `except BaseException`」，**未确认 print 位于受保护的 `try.body`**。把 print 移进同一 `try` 的 `finally` 会被误报 `protected`。当前三个 print 实测均在 `try.body`（Codex 复算确认），故不推翻本次修法；但该盲区本卡**未修**——判据脚本由卡文 §二.3 / §二.2 逐字指定，事后改判据 = 动裁判，且会使已归档的 before/after 两跑与新脚本不同版。登记交主 session 裁（见「台账待登记」⑨）。

⑩ **未证明 B 格的错误文字实际可见**（Codex round-1 ③ 末句）：三跑未保存子进程 stderr，只记 rc 与账本计数，因此「stderr 正常时落盘失败仍会说话」这一点存档里没有直接证据，只有「B 格 rc=3 且流程走完」的间接支持。

---

## 四 台账待登记条目（必填，≥4）

① **R-11 / U7-A 外审 HIGH-1「rc=0 假绿」→ 本卡修复收口**。修复 commit **`5e4d10cf`**（未 push）；判据证据路径 `_bmad-output/审查/evidence-w4final/`（`ast-before/after-*.txt`、`three-run-before/after-*.txt`、`nc-negative-control-*.txt`）。

② **口径更正落档（行号）**：U7 验收单写的 `:1291-1303` 保护块与其后 `os._exit`（整体较本主干 **−231 行**，取自更早审 SHA）**作废**；本主干实测缺陷在 `:1512`，退出保护块 `:1522-1534`，`os._exit` `:1535`（皆为改前 `B14_BASE` 锚）。修后各下移 +1/+3/+3，`_final_accounting` 由 1487–1535 变 1487–1538。

③ **口径更正落档（print 个数）**：`_final_accounting` 内 `print(...)` 实测 **3 个**（改前 `:1512` / `:1523` / `:1530`），设计稿 §4「修后两行 protected」为**笔误**；实义是「修后 3 个全 protected / 0 UNPROTECTED」。本卡按 3 个执行并实测通过。

④ **committed 回归锁缺口 → 移交 T9-B**：先红后绿只在 evidence 脚本，CI 的 pytest 无 A 格（ledger=目录 + stderr 坏 ⇒ rc=3）回归用例。建议由 `test_live_port_guard_contract.py` 的 **R-B14-4** 批准持有者（**T9-B**）补一条。本卡只登记、**未扩面**；是否排进 T9-B 由主 session 裁。

⑤ **存档卫生待处置**：`evidence-w4final/DISCARDED-unit-open-20260914T195156-truncated.txt` 是一份**作废**的截断运行产物（已随本卡 commit 入库）。按协议应剔除，但 `rm` 被用户级 `~/.claude/guard-hook.sh:20` 确定性阻断（删除文件需用户确认），车道**未绕过守卫**，改为就地改名 + 文件头写明作废原因。请主 session 在集成期决定是删除还是保留痕迹。

⑥ **迟到路径同型未护排查 → 仍未关闭**：Codex round-1 对问题⑤ 明确答「**未评估**」（`_rewrite_ledger_after_late_record` 等实现不在 prompt 指定的最小读取面内），既不能认定存在同型问题，也不能宣布已排除。建议单开一卡做 `live_port_guard.py` 全文件「stderr 坏态下可逸出的 print」排查，或并入 T9-B/T9-C。

⑦ **Codex 存档与计数**：round-1（唯一一轮）存档 `_bmad-output/审查/codex-review-CARD-W4-FINAL-ACCOUNTING.md`，prompt `_bmad-output/审查/prompts/codex-prompt-CARD-W4-FINAL-ACCOUNTING.md`；绑定 **`5e4d10cf`**（= 最终 HEAD 代码面，diff 空）；模型 `gpt-6-astra` · `ultra` · `codex-cli 0.153.3`；**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3**。按 D-15 一轮达标。

⑧ **tests/unit 目录级 diff 结果**：开工 / 收工均 64 vs 基线 64、**diff 空**（零 `>`、零 `<`），基线 64 条未被本卡改动。

⑨ **判据加固项（Codex L1）→ 交主 session 裁**：`evidence-w4final/ast-protected.py` 的 `protected` 判定应收窄为「print 位于该 `try` 的 `body` 之内」而非「落在 `lineno..end_lineno` 区间内」，否则 `finally` 里的 print 会被误报 protected。车道**未事后改判据**（卡文逐字指定 + 会与已归档两跑不同版）。若主 session 认为该加固应落地，建议与 T9-B 的契约用例一并做（同一面、同一次重跑）。

⑩ **自动阻断缺口（Codex M1）**：`evidence-w4final/three-run-abc.py` 只打印、无断言、脚本自身恒 `rc=0`，人读存档能判红绿，自动执行者收到的是成功状态。与 ④ 同一落点（T9-B 契约用例），若 ④ 落地则本条一并关闭。

---

## 五 Codex 独立复核

顺序遵守：代码与两判据全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`（本节回填、Codex 存档入库；代码面零改动）。

### round-1（唯一一轮）

| 项 | 实测 |
|---|---|
| prompt | `_bmad-output/审查/prompts/codex-prompt-CARD-W4-FINAL-ACCOUNTING.md`（五分节 + 最小读取面写死；协议 §2 四个禁用措辞 grep 均 **0**） |
| 存档 | `_bmad-output/审查/codex-review-CARD-W4-FINAL-ACCOUNTING.md`（非 0 字节；`.stderr` **未入库**） |
| 模型 / effort / codex | `gpt-6-astra` / `ultra` / `codex-cli 0.153.3`（存档首部三字段齐；旧模型名 `gpt-5.6` grep = 0） |
| 会话头自证 | `.stderr` `:4 OpenAI Codex v0.153.3` / `:7 model: gpt-6-astra` / `:11 reasoning effort: ultra` |
| **审查绑定** | **`5e4d10cf`** = 当时 HEAD；`git diff --stat --no-color 5e4d10cf HEAD -- . ':(exclude)_bmad-output'` → **空**（仍绑定最终 HEAD 的代码面） |
| **BLOCKER** | **0 条** |
| **HIGH** | **0 条** |
| MEDIUM | 1 条（M1） |
| LOW | 3 条（L1 / L2 / L3） |

Codex 首句结论：「本次三行修法成立：新增 `try` 包住完整的落盘失败 `print`，没有改动结账判定和强制退出。**未发现本次改动新增的 BLOCKER/HIGH。**」

**轮次判定（D-15）**：本卡有代码改动 ⇒ 需多轮直到「绑最终 HEAD 的一轮 BLOCKER = 0、HIGH = 0」。round-1 已同时满足「绑定最终 HEAD 代码面」与「B=0、H=0」⇒ **一轮达标，无需再送**。本节回填后的 commit 只动 `_bmad-output`，按 D-15 **不算审后改代码**、不触发再审。

### MEDIUM / LOW 逐条处置（⛔ 车道不自判通过，全部登记交主 session 裁）

| 编号 | Codex 原意 | 车道处置 |
|---|---|---|
| **M1** 缺少自动阻断回归 | `three-run-abc.py` 只打印结果、无断言、脚本自身恒 `rc=0`；人能从存档看见红，自动执行者仍收到成功状态 | **属实**。本卡的先红后绿是「人读存档判定」，脚本不是门。按协议 §1，MEDIUM 登记不阻断。⛔ 车道**不改**卡文 §二.3 逐字指定的判据脚本（改判据 = 事后动裁判，且会使已归档的 before/after 两跑与新脚本不同版）。Codex 自己给的落点与本卡「未证明」④ 一致：**移交 T9-B** 在契约套件补 A 格用例（断言 `blocked/unaccounted == 1/1` 且子进程 `rc=3`，并验证负控输入能让该用例转红）。见「台账待登记」④。 |
| **L1** AST 判据会放过 `finally` 里的 print | 判据只看「print 行号落在某个 `try` 的 `lineno..end_lineno` 区间」+「该 try 有 `except BaseException`」，未确认 print 位于受保护的 `try.body`；若把 print 移进同一 try 的 `finally`，判据仍报 `protected` 但异常不会被那个 `except` 接住 | **属实，是本卡判据的真实盲区**。Codex 同时指出：当前三个 print 实测**均在 `try.body`**，故不推翻本次修法。同 M1 理由，车道**不事后改判据**。登记为判据加固项交主 session 裁（见「台账待登记」⑨）。 |
| **L2** rc=3 缺退出调用点的直接证据 | 三跑只记返回码与退出前计数，没记录执行到哪个退出调用点；单 hunk + A 格负控翻转 + 控制流「**强支持**」最终执行改后 `:1538` 的 `os._exit`，但不是运行时排他证明 | **属实**。本卡未声称排他证明；已并入「本卡未证明」新增第 ⑧ 条。Codex 亦确认 `CHILD-JSON` 已输出 ⇒ 至少排除「合成事件当时就提前退出」。 |
| **L3** 合成事件与真实入口的记账等价未核实 | 三跑用 `sys.audit(...)` 合成且首参 `None`；prompt 的最小读取面未含 `_audit_hook` / `record` / `finalize_and_snapshot` 实现，故只能说「未证明等价」，**不是**「已证明不等价」 | **属实，且本卡开卡时即已如实登记**（「本卡未证明」①）。Codex 的补充精确化：现有证据覆盖的是「合成审计事件 → 退出前 `late_snapshot()` 计数 1/1 → 组合故障下最终返回码」，退出前快照不等于最终快照的直接观测。已据此加严「未证明」① 的措辞。 |

### Codex 对其余提问的直接回答（摘要，原文见存档）

- **⓪ 保护范围**：改后 `:1513`（本树实测 print 在 `:1514`，Codex 指的是 `try:` 起点行）整个表达式都在保护内，含字符串格式化、`exc!r`、stderr 输出；同步抛出的 `BrokenPipeError`、关闭文件的 `ValueError`、替换后 stderr 方法抛出的 `BaseException` 子类都会被接住。**但**三跑实际只覆盖了「已关闭的 `StringIO`」一种；且这不保证「阻塞 / 不返回 / 直接终止进程」的输出实现仍能走到末行。
- **③ 可观测性**：「落盘失败仍会尝试说话」成立；「保证运维看见」**不成立**——A 格可降级到「账本不可写、错误文字不可见，仅剩非零退出状态」。新增保护吞的是**报告**异常，发布异常本来就已由外层 `except Exception` 接住；它既没新增也没删除「落盘失败本身必须非零退出」的规则。对本卡「未结账不能以零退出」的目标，该取舍**可接受**，并与改后 `:1536` 既有注释一致。另：三跑未保存 stderr ⇒ 存档**没有**直接证明 B 格的错误文字实际可见。
- **⑤ 迟到路径**：**未评估**（`_rewrite_ledger_after_late_record` 等不在指定读取面内）；既不能认定存在同型问题，也不能宣布已全部排除。

### Codex 自述的复核边界（如实抄录）

「复核仅使用指定文本及内存 AST 对照，未修改文件、未运行三跑或 pytest、未连接端口。存档中的红→绿→负控回红及首尾哈希一致已核对；但负控档案写的是『与 HEAD blob 相同』，没有绑定当时 HEAD 的 SHA，因此未独立确认其『与 `08100483` 逐字节相同』的执行记录；`151 passed` 也不在允许读取的证据中，未予背书。」

> 车道回应（只补文档、不改代码 / 不改判据）：负控段执行于本卡 commit **之前**，当时 `HEAD` 即 `08100483`（B14_BASE），已在 §一.4 表格 [3] 行补绑该 SHA。`151 passed` 的存档路径见 §一.5（`contract-open-*.txt` / `contract-close-*.txt`），Codex 未获授权读取属 prompt 最小读取面的刻意收窄，非证据缺失。
