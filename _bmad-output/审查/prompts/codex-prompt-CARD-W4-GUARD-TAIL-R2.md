# CARD-W4-GUARD-TAIL-R2 独立复核请求（BATCH-2026-09-18-第十五批 · 车道 card-p9-testinfra）

## ① 背景与最小读取面（只读这些，不要扩散到别处）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra`
基线 `9c4e7e82`，本卡是当前 `HEAD` 上的**单个** commit（`git log -1` 可见卡号）。
**审查绑定 = 当前 HEAD**；本卡的代码面 diff 请一律用下面第 1 条命令取（不要硬记某个短 SHA）。
本卡零 `backend/app` 改动、零数据库连接。

W4 门（`backend/tests/support/live_port_guard.py`）是「离线测试禁连现网 Neo4j 7691」的唯一防线：
它装一个 CPython `socket.connect` 审计 hook，拦下的每一次尝试都要记账，收尾时任何未结账的
拦截都必须把进程退出码强制成 3。本卡收的是前一批（T9 三卡）如实登记、但没关的四类尾债。

**最小读取面（请逐个打开）**：

1. 本卡代码面全量 diff：`git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'`
2. `backend/tests/support/live_port_guard.py`
   - `:772-830` `_audit_hook`（迟到分支：`_rewrite_ledger_after_late_record()` → stderr 打印 → `os._exit(3)`）
   - `:1382-1502` `write_ledger` / `_publish_ledger` / `_rewrite_ledger_after_late_record`（本卡只改了后者的 `:1494` 一句 docstring 与 `:1501` 一行）
   - `:1505-1556` `_final_accounting`
   - `:893-952` `install()`
3. `backend/tests/unit/test_live_port_guard_contract.py`
   - `:1335-1410` `_refuse_to_guess_on_deferred_execution`（拒绝表全貌；本卡加了 `ast.TypeAlias` 一支）
   - `:1692-1897` `TestSingleLedgerSnapshot`（发布序族；本卡新增 `:1817` 截断门）
   - `:1897-1990` `TestInstallOrder`（本卡新增 `:1900` / `:1930` 两条）
   - `:2351-2440` `TestForcedExitPathsAreFailOpen`（本卡新增整类）
4. `backend/tests/support/w4_sentinel_identity.py`
   - `:77-124`（`_SUMMARY_RE` / `_FINAL_RE` / `_BODY_RE` 三个锚 + 两个分隔符常量）
   - `:164-183` `_lines` / `normalise_thread`
   - `:186-266` `summary_quad` / `_final_blocked` / `blocked_count`
   - `:269-303` `_refuse_ambiguous_record`（本卡新增）
   - `:306-437` `_declared_record_blocks` / `failure_body_identities`
   - `:458-550` `_describe` / `main`（CLI 的 0/1/2 语义）
5. `backend/tests/unit/test_w4_sentinel_rebind.py`
   - `:278-378` `TestFailureBodyIdentities`（本卡改了其中 `test_owner_containing_on_thread_does_not_leak_into_identity` 的输入）
   - `:476-572` `TestRound4Closures`（本卡改了 `test_orphan_record_outside_any_block_is_refused` 的输入）
   - `:572-706` `TestJudgeIsBoundToTheRealProducers`（四条字面量门，必须仍绿）
   - `:818-end` `TestGuardTailR2Closures`（本卡新增整类）
6. `backend/tests/unit/test_w4_a_regression_lock.py` **全文**（本卡新文件）
7. 冻结参照（本卡**不改**，只作对照）：`_bmad-output/审查/evidence-w4final/three-run-abc.py`、
   `ast-protected.py`、`nc-remove-protection.py`
8. `backend/tests/support/hygiene_snapshot_tristate.py:27-55`（只为核对本卡「不改、只登记」的说法是否属实）
9. 台账来源行：`_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:105`
10. 本卡证据目录：`_bmad-output/审查/evidence-w4-guard-tail-r2/`（先红、结构判据两侧、AST 门、负控五段、目录级存档）

## ② 作者自述 —— 请独立核对，不要采信

1. `ast.TypeAlias` 分支加在 `_refuse_to_guess_on_deferred_execution` 的收集分支里，写法是
   `getattr(ast, "TypeAlias", ())`（3.11 及更早退化成空元组）；真实 `install()` 仍照常通过。
2. 回归锁三格全部在**真子进程**里跑，受拦事件由 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))`
   合成，不建立任何真实连接；父进程内不触发任何受拦事件（否则会记到本用例名下）。
3. 截断门用**真实文件权限** `chmod 0o400` 而不是 monkeypatch `open` / `write_ledger`；
   非 root 且文件系统强制写权限时才判，否则 `pytest.skip` 并登记。
4. `_rewrite_ledger_after_late_record` 的 `except Exception` 收成 `except BaseException` 之后，
   `BaseException` 从落盘逸出时不再跳过 `_audit_hook` 中 `os._exit` 前的 stderr 打印与两次 flush。
5. `w4_sentinel_identity` 四条改法**全部是收紧**（`fullmatch` / 右锚 / 拒判），没有任何输入因此从红变绿。
6. 「与已认领记录逐字节相同的块外行豁免」对**集合**语义可证安全：逐字重复不可能改变身份集。
7. 产出方（`live_port_guard` 的三处抬头与记录行、根 `conftest.py`）**零改动**；
   `backend/tests/conftest.py` / `backend/tests/unit/conftest.py` / `guard_plugin.py` **零改动**。
8. 本卡对卡文有两处如实记录的口径更正，请一并核对是否成立：
   - 卡文说「地址含 ` on thread `」这一类由「`owner` 组含 ` on thread `」判得出；实测不成立
     （非贪婪 `thread` 会吃到最后一个 ` (owner=` 之前，`owner` 组干净），改用
     「` (owner=` 之前那一段里 ` on thread ` 出现两次」判（见 `_refuse_ambiguous_record`）。
   - 卡文预期 `grep -c 'W4LedgerConflict('` 改后 = N+3 = 14；实测 15，因为分隔符拒判有两个
     `raise` 点（两个分隔符各报各的事实）。

## ③ 请按重要性排序回答的问题

0. 回归锁 A 格的红是否**真由** T9-A 那 4 行修复决定？负控存档 `negctl-2-*.txt` 显示
   删掉那层嵌套 try 后 A 红（`assert 0 == 3`）、B/C 绿。三格 `rc == 3` 是否可能来自
   `live_port_guard` 里**别的** `os._exit(3)` 路径，使这条锁其实没绑在它声称的那一行上？
1. 截断门：macOS 默认 APFS + 非 root 下对**文件自身** `chmod 0o400` 是否真使 `open(path, "w")`
   抛 `PermissionError` 且旧字节原样保留？`pytest.skip` 那条分支会不会让整条门在 CI（root 容器）里恒 skip
   而没人发现？断言顺序（先判发布序、后判陈旧发布返回 False）是否掩盖了某一侧？
2. `getattr(ast, "TypeAlias", ())` 在 3.14 下是否真命中？`node.name` 在 `ast.TypeAlias` 上是否
   总是 `ast.Name`（`f"type {node.name.id}"` 会不会在某种写法下抛 `AttributeError` 而不是判红）？
3. `_BODY_RE` 全匹配 + `\)$` 是否会误拒产出方 `live_port_guard.py:1551` 的真实记录行？
   分隔符二次出现拒判的**保守假红面**有多大——真实 nodeid / 线程名 / 地址 repr 里
   出现 ` (owner=` 或两个 ` on thread ` 的可能性？
4. 「逐字节相同的块外行豁免」是否会掩盖「同一条记录被两个块各印一次、其中一块抬头已漂」？
   集合语义下是否真的没有信息损失？本卡为此改了 `test_orphan_record_outside_any_block_is_refused`
   的输入（改成携带**不同**记录的漂移块），这个改法是否削弱了 r4 MEDIUM-2 的门？
5. `_FINAL_RE` 的右锚是否与产出方 `:1544-1549` 逐字一致（`***` 结尾、退出码取自 `FINAL_EXIT_CODE`）？
   「抬头命中但不全匹配即拒判」会不会在**正常**存档上误触发？
6. `_rewrite_ledger_after_late_record` 改 `BaseException` 后会不会吞掉 `SystemExit` /
   `KeyboardInterrupt` 而改变解释器收尾期行为（调用点 `:821` 已经是同样写法）？
7. 四个目录级套件与 contract 三文件是否真跑完（存档末行 rc、`collected` 数）？
   红集 diff 是否只有减少？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` + 一句复现思路。
措辞请用：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**。

## ⑤ 边界

只读，不要修改任何文件；不要连接任何数据库或网络端口；
不要评论 P9-B 的 timeout / marker 面、不要评论 `classify_sha_change` 的修法本身（本卡地盘外，只登记）、
不要评论产出方的文案与记录行格式（本卡零改动，改动会连带三处抬头与四条字面量门）。
