# 独立复核：CARD-W4-4b（W4 测试隔离门 — 部分安装态的结算 + 账本发布顺序 + 契约收紧）

## 一 背景与最小读取面

被审对象是一个 **pytest 测试进程内的隔离门**：它监听 CPython 的 `socket.connect` 审计
事件，阻止测试进程连上开发机上的 Neo4j（端口 7691 / 7687），并在进程退出前做一次
「最终结算」——发现有拦截记录无人认领，就把进程退出码强制成 3。

上一轮独立复核对这道门提了十条意见。本卡处理其中四条（HIGH-2 / MEDIUM-4 / MEDIUM-7 /
MEDIUM-8），外加撤回一处**说得比证明的宽**的文档表述。此外作者在送审前跑了一轮
**5 维度对抗性自查复核**（独立 reviewer agents），又发现并修掉了自己初版的三处缺陷
（见 §二 (g)），自查负控存档在 `_bmad-output/审查/evidence-w44b/review-negctl-r{1,2}-*.txt`。

**请只读下面这几处，不要扩散到仓库其它部分**（工作目录 = 本仓库根）：

1. 本卡完整改动面：
   `git diff 10c80be7 <审SHA> -- backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py backend/scripts/lifespan_isolation_guard_probes.py`
   （`10c80be7` 是本卡开工前那一 commit；本卡未改 `backend/tests/conftest.py` 与
   `backend/tests/support/guard_plugin.py`，它们仍是那一版）；
2. `backend/tests/support/live_port_guard.py` 的四段：
   - `:255-480`（模块级发布序 `_SNAPSHOT_SEQ`/`_next_snapshot_seq` :261-272、`_GuardState`
     :275 起、`record` :308、`finalize_and_snapshot` / `late_snapshot` / `ledger` /
     `_ledger_locked`），
   - `:600-660`（`_safe_repr` :602、`_block_message` :628），
   - `:708-900`（`_audit_hook` :708 含受拦分支与迟到分支、`_install_audit_hook`、
     `install` :829 及其体内新顺序 :875-879），
   - `:1318-1470`（`write_ledger` :1318、`_PUBLISHED_SEQ` :1336、`_publish_ledger`
     :1344、`_rewrite_ledger_after_late_record` :1395、`_final_accounting` :1423、
     退出判据 :1455）；
3. `backend/tests/unit/test_live_port_guard_contract.py` 的四个类**全文**：
   `TestSettlementAtomicity` :726、`TestSingleLedgerSnapshot` :986、`TestInstallOrder`
   :1139、`TestFinalizeRaceSeam` :1329，以及文件头部的 AST helper（`_fn_ast` 起至
   `_live_called_names`）；
4. 两个新探针的函数体：`backend/scripts/lifespan_isolation_guard_probes.py`
   `probe_late_ledger_survives_stale_final_write` :1714、
   `probe_partial_install_settles_late_connection` :1865；
5. 负控输出（用于核对作者自述是否与实测一致）：
   `_bmad-output/审查/evidence-w44b/m7-negctl-{1,2,3,4,5a,5b}-after2-*.txt`、
   `review-negctl-r{1,2}-final-*.txt`、`m4-before-red-*.txt`、
   `high2-contract-red-*.txt`、`high2-probe-red-*.txt`、`m7-5-head-green-*.txt`，
   以及负控跑器 `m7-negctl.sh` / `review-negctl.sh` 与 `negctl_patch.py`。

## 二 作者自述（请独立核对，不要采信）

- **(a) HIGH-2 / 部分安装态**：`install()` 的顺序由「`_install_audit_hook()` → 目标预检 →
  `register_final_accounting()`」改为「`_install_audit_hook()` → `register_final_accounting()`
  → 目标预检」。理由：audit hook 装上就摘不掉（CPython 无 `sys.removeaudithook`），预检
  抛出时它已经在位并照常记账，而旧顺序下结算器尚未注册 ⇒ 这些记录无人交账、进程 exit 0。
  作者同时把契约 `test_final_accounting_is_registered_after_the_precheck` **翻转**成
  `..._before_the_precheck`，并在 docstring 里写明「旧断言把缺陷钉成了规格」。
  作者声称此时 `STATE.installed` 仍为 False，账本 `installed` 字段如实为 False，而
  `_final_accounting` 的退出判据与 `installed` 无关，故装门失败该以什么 rc 收场就还是什么。
- **(b) 撤回双向声明**：原文三处写「`rc=3` 与账本 `unaccounted>0` 两个方向都成立」。作者
  声称这是过宽表述，改为单向（`unaccounted>0` 蕴含 `rc=3`），理由是 `_final_accounting`
  的退出判据 :1455 还有第二个分支（`blocked>0` 且 `effective_status==0`），那时
  `unaccounted` 可以是 0。探针 `guard-ledger-matches-verdict` 的 docstring 同步改成
  「钉的是两个特例」，作者声称**判据一字未改**。
- **(c) MEDIUM-4 / 账本发布顺序**：新增 `_publish_ledger(path, ledger)` :1344 与账本快照的
  全进程单调发布序 `seq`；序号不比已发布的大就不回写。`seq` 只盖在
  `finalize_and_snapshot` / `late_snapshot`（要发布的快照）上，`ledger()` 这种纯读取不盖 ——
  作者声称初版盖在无条件路径上时，探针 `guard-finalize-seam-inert-when-unset` 的
  「前后账本逐字节相同」当场恒假转红，于是把序号收窄（有裁判门
  `test_plain_ledger_read_does_not_consume_a_publish_seq` 钉住）。
- **(d) MEDIUM-7 / 五处 AST 契约收紧**：① 结算临界区改按结构判（`items[0]` 必须是
  `self._lock`），不再对 `ast.dump` 做子串；② 持锁方法体内对 `self` 的直接调用改**白名单**
  （必须落在以 `_locked` 结尾的方法集里，该集合从源码 AST 导出并与手写清单做相等断言）；
  ③ `_audit_hook` 内 `finalizing` 属性访问次数必须为 0（不只查旧拼写 `_FINALIZING`）；
  ④ 顺序门只数**可达**语句（恒假分支的 body 不算）；⑤ 注入点必须是受拦分支 body 内的一条
  独立 `Expr`、祖先链无恒假分支、不进任何判据（`Try` 显式允许，因为现状就在 `try` 内）。
  每处配了一份负控：把上一轮点名的宽松写法临时写进生产代码，旧门放行 / 新门以**指定理由**
  拦下（负控跑器带 EXIT trap 无条件还原 + `shasum -a 256` 前后比对 + 变异后 `ast.parse`
  自检）。作者自查发现 `_live_called_names` 初版只在子节点上判恒假分支（根节点自身是
  `if False:` 时剪枝失效），M7④ 负控 case 4 首跑 SURVIVED，已修并复跑全绿。
- **(e) MEDIUM-8 / `repr` 出锁**：`record()` 把地址格式化挪到 `self._lock` **之前**，
  锁内只记字符串；提取模块级 `_safe_repr(address)`（捕 `BaseException`，作者声称卡文原写
  `Exception` 是**更弱**的：从 `__repr__` 逃出的任何东西都会从计数之前穿过去）。
- **(f) 作者自己声明的局限**：探针制造的是**注入点决定的确定性交错**，不是自然时序；
  `_publish_ledger` 只证明「成功写入时后写者不是旧快照」，不证明落盘 I/O 成功；
  M7 白名单只锁当前方法集，新增 `_locked` 方法会被相等断言顶红而不是自动放行。
- **(g) 自查复核（5 维度 reviewer + 证伪）又修了三处**，请重点独立核对这些修法：
  1. **死锁门的失败形态**（自查 HIGH）：初版死锁单测在它要抓的回退发生时会**挂住整条
     session**（conftest 哨兵 `pytest_runtest_makereport` 无超时 `STATE.take()`，取的正是
     被 worker 永久持有的那把锁）。修法：`__repr__` 闭包引用 fixture 实例、并在用例内把
     `guard.STATE` 指到另一份全新 state。
  2. **`_publish_ledger` 的 I/O 失败窗口**（自查 MEDIUM）：初版把 `_PUBLISHED_SEQ = seq`
     放在写盘成功之后 ⇒ 较新的那份写失败后，陈旧发布反而成功。修法：序号**先行推进**
     （失败方向变成「更旧的也别写」，文件停留在截断/无效态）；裁判门
     `test_publish_ledger_refuses_stale_even_after_a_failed_write`（负控 r2）。
  3. **`_block_message` 的第二处裸 repr**（自查 MEDIUM）：拒因文本 `{address!r}` 可被恶意
     `__repr__` 劫持，`BLOCK_REASON` 拒因绑定断裂。修法：复用 `_safe_repr`；裁判门
     `test_block_message_binds_the_reason_despite_a_hostile_repr`（负控 r1，判据在
     `sys.audit` 最远下游）。另有 3 条 LOW：两处「拒绝装门」doc 补写新语义、
     `hook_at < register_at` 断言 message 撤回不成立的危害声明。

## 三 请按重要性排序回答（每条给出结论 + 依据行号）

1. **新顺序是否引入「结算器已注册但 hook 未装」的反向窗口**？`install()` :829-890 的
   语句序列里，`register_final_accounting()` 之前是否存在任何可抛出的步骤？
2. **`installed=False` 时 `_final_accounting` 的退出码语义**是否与 :1455 的判据一致？
   装门失败且零连接的进程，退出码是否被这个新注册的处理器改变？既有探针
   `require-blocked-target`（期望 rc=0）在新顺序下是否仍然成立？
3. **(g).2 的修法是否完整**：序号先行推进后，两条写盘路径是否仍可交错？写盘失败时
   `_PUBLISH_LOCK` 释放、调用点各自的 try 包裹、迟到路径 `os._exit` 不被挡 —— 这几条
   是否都保持？`_SEQ_LOCK` 在 `self._lock` 内取，锁序是否可能成环？
4. **`_PUBLISHED_SEQ` 是模块级且只增**：同一个 pytest 进程里跨用例累积，是否存在某条路径
   使一次**合法**发布被判成陈旧（例如契约 `TestSingleLedgerSnapshot` 里换个执行顺序）？
5. **(g).3 的 `_safe_repr` 复用是否还有漏网的格式化点**：受拦路径上（`_audit_hook` 全文 +
   `record` + `_block_message` + 迟到分支的打印）还有没有对不可信地址对象的裸
   `{address!r}` / `repr(address)`？迟到分支 :751 的 `f"...{address!r}..."` 在
   try 保护内 —— 作者认为它已被 HIGH-3 的保护覆盖，你同意吗？
6. **白名单 ② 是否误拒正例**：有没有合法的、不会取锁的写法会被这条门拦下？该门受检方法
   集与白名单都从源码 AST 导出，是否存在门未覆盖的路径（例如临界区里通过局部变量或
   `getattr` 间接调到会取锁的方法）？
7. **⑤ 的四条子规则在未改动的 `_audit_hook` 上是否仍绿**（注入点 :734 本就在 `try:` +
   受拦分支 + 事件分支三层里）？(ii) 用 AST 定位受拦分支（`test` 含 `BLOCKED_PORTS` 或
   `port_is_trustworthy`）的写法，会不会在受拦判据措辞改动后**静默失配**成「找不到就
   通过」？还有哪些等价写法能让注入点实际失效而这条门看不见（例如恒真循环、赋值语句、
   别名调用）？
8. **(g).1 的死锁门修法**：`__repr__` 闭包引用 fixture 实例 + `guard.STATE` 指到全新
   state —— 回退发生时这条门是否真的以「一条红」收场而不是挂 session？卡死 worker 是
   daemon 线程，随进程退出 —— 有没有别的地方会在 teardown 期再碰那份被卡死的 state？
9. **「⇔」撤回之后 :1655 探针是否仍承重**：`guard-ledger-matches-verdict` 的判据是否真的
   一字未改？改后的 docstring 是否仍然说得比它证明的宽？
10. **本卡新增的门里有没有恒真判据**（无论生产代码怎么改都不会红）？逐条给出「什么输入下
    它会红」。特别看 `test_partial_install_still_registers_final_accounting` 用替身替换
    `guard.atexit` 之后，判据是否变成自证。

## 四 输出格式

每条给：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据**（读到的代码/输出，
不要复述作者自述）+ **建议**。只读判定不了的写「未验证」，不要推测。
请在开头给一行总结：BLOCKER 数 / HIGH 数。

## 五 边界

- **只读**。不要修改任何文件，不要跑测试、探针或负控脚本。
- **不要连任何端口**（7691 / 7687 是开发机上的真库）。
- 上一轮十条意见里的 H-1a / H-2 / M-1 / M-3 / M-5 / L-2 不在本卡范围（另有卡处理）；
  `backend/scripts/lifespan_isolation_negative_control.py` 不在本卡地盘（另有卡处理），
  本卡对它只出建议不改（作者已登记它 :44-45 的 doc 措辞待 U8 顺手更新）。
- 不需要评价 `_bmad-output/` 下的文档写法，只核对证据与代码是否一致。
