# UAT · CARD-W4-4-settle-atomic

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-W4-4-settle-atomic]`
> 车道 `card-y7-w4-settle`（分支 `card/y7-w4-settle`，起点主干 `03ac8bf8`）
> 证据目录 `_bmad-output/审查/evidence-w4-4/`（本单只引用路径与末行，不自述数字）

---

## 〇 一句话

测试隔离门的**最终结算**原来自己就是一处假绿：置结算标志与取账本快照是两条独立语句、
审计回调对那个标志是锁外读、记账又在另一把锁里，于是一条「连了现网端口」的记录可以
既不进快照又不触发迟到路径，进程照常绿着退出。本卡把这三者收进同一把锁，并顺带修了
装门顺序与预检时机两处同源问题。

---

## 一 DoD-3 双段

### 1-A 用户能看见什么（产品体验口径）

**无变化。** 这道门只在**跑测试**时起作用，它不改任何页面、不改任何数据。

如果一定要说变化：以前有一种漏网情形——测试跑完的最后一刻才去连开发机上的数据库，
那次连接会被门拦下、却没人把它算进最后的总账，于是整轮测试仍然报「全绿」。现在这种
情形一定会被记下来，并且让那轮测试**失败**。也就是说：以前可能骗过你的一种「假绿」，
现在骗不过了。

### 1-B 技术上改了什么

| # | 改动 | 位置 |
|---|---|---|
| a | `_GuardState.finalize_and_snapshot()`：**同一次持锁**内置结算标志 + 取快照 | `backend/tests/support/live_port_guard.py` |
| a | `record()` 返回三态（`RECORD_ADVISORY` / `RECORD_BLOCK` / `RECORD_LATE`），结算判定挪进**同一把锁** | 同上 |
| a | 模块级 `_FINALIZING` **删除**（不是「留着没人读」）；审计回调改读 `record()` 的返回值 | 同上 |
| b | `write_ledger(path, ledger=None)` 接收快照；`_final_accounting` 传下去 —— 裁定与落盘是**同一个 dict 对象** | 同上 |
| c | 迟到记录照常进账且**不看豁免**；`os._exit(3)` 前用 `late_snapshot()` 重写账本 | 同上 |
| d | `install()` 把 `_install_audit_hook()` 提到目标预检之前（`register_final_accounting()` 相对顺序不变） | 同上 |
| e | `assert_test_uri_not_blocked()` 从 session fixture 上移到 `pytest_configure`（两处接线） | `tests/conftest.py` / `tests/support/guard_plugin.py` |
| e | `_GuardState.precheck_done` + `begin_item()` 在预检未完成时不发豁免票（闩） | `live_port_guard.py` |
| f | `_finalize_race_seam` / `_finalize_race_seam_hook`：默认 no-op 的注入点 + `assert_guard_live` 身份复核 | 同上 |
| f | seam 调用包 `try/except BaseException`（Codex r1 HIGH-1 整改）——注入点对控制流的影响面为 0 | 同上 |
| c | 迟到分支与最终总账的**报告整块**包进 try，`os._exit` 永远在 try 之外（Codex r1 HIGH-3 整改） | 同上 |
| — | 契约用例 5 个新测试类；探针 **5 条**新增 | `tests/unit/test_live_port_guard_contract.py` / `scripts/lifespan_isolation_guard_probes.py` |

代码面 `git diff --stat -- backend/`：5 文件 / +865 / −51（`live_port_guard.py` 与
`guard_probes.py` 的增量里相当一部分是解释「为什么这样改」的注释与 docstring —— 这道门
被独立终审打回过多轮，写清楚拒因比省几行更值）。

---

## 二 改前的缺陷是**实测复现**的，不是推理

复现脚本 `_bmad-output/审查/evidence-w4-4/before-repro.py`（不动生产文件，全部注入都在
子进程里、且只做延迟与观测）。存档 `before-repro-*.txt` / `before-3-install-order-*.txt`。

| 编号 | 复现的是什么 | 结果 |
|---|---|---|
| before-1 | 结算竞态**丢记录**（放行点是比 guard 更早注册的 atexit 回调 = 生产真实路径） | 见存档：rc 与账本 `unaccounted` 一行 |
| before-2 | **账本与裁定打脸**（放行点落在快照 A 与快照 B 之间） | 见存档：rc 与账本 `unaccounted` 一行 |
| before-3 | `install()` 预检整段在**门外** | 见存档：`RESULT: 预检内连接 = …` 一行 |
| before-4 | 预检落在 `begin_item(exempt=True)` 作用域内 | 见存档：`PROBE session-fixture: exempt=… owner=…` 一行 |

改后同一时机的对照证据：`after-e-precheck-timing-*.txt`（在**真** conftest 接线上观测预检
的调用时机、当时的归属票、以及总调用次数）。

---

## 三 每条修复都做了拆门实测（「跑了没红」不算门成立）

`_bmad-output/审查/evidence-w4-4/mutation_teardown.py`，**最终存档 `mutation-teardown-r2c-*.txt`**。
**9 条**变异各自**点名**它必须杀掉的探针 / nodeid，判据是**三态**（只有「那条 nodeid 真的
跑起来并翻红」才算击杀，见 §九.1）；跑前记 3 个可能被变异文件的 sha，跑完逐个复核逐字节还原。

| 变异 | 拆掉的是 | 点名必须转红的门 |
|---|---|---|
| M1 | 结算判定搬回锁外读（= 主干形状） | 探针 `guard-finalize-race-loses-record` / `guard-ledger-matches-verdict` + 2 条 nodeid |
| M2 | `_final_accounting` 不再把快照传给 `write_ledger` | `test_final_accounting_hands_its_own_snapshot_to_write_ledger` |
| M3 | `install()` 顺序改回去 | 探针 `guard-install-order-precheck-is-guarded` + `test_audit_hook_is_installed_before_the_target_precheck` |
| M4 | `assert_guard_live` 不再复核注入点身份 | 探针 `guard-finalize-seam-inert-when-unset` + `test_seam_replacement_is_detected_as_drift` |
| M5 | 预检挪回 session fixture | `test_precheck_lives_in_pytest_configure_not_in_a_session_fixture[root-conftest]` |
| M6 | `begin_item` 的预检闩被拆 | `test_begin_item_refuses_exemption_before_the_precheck` |
| M7 | 迟到路径不再重写账本 | 探针 `guard-ledger-matches-verdict` |
| M8 | 拆掉注入点的 `try/except`（Codex r1 HIGH-1 的形态） | `test_throwing_seam_cannot_skip_accounting` |
| M9 | 迟到报告块移出 try（Codex r1 HIGH-3 的形态） | 探针 `guard-late-exit-survives-broken-stderr`（实测 rc=120 而非 3） |

**M1 的击杀理由与 before-1 逐字对上**（`rc=0 期望 3`），说明变异体确实复现了主干形状，
而不是随便弄坏了别的东西。**M7 的击杀理由是 `rc=3 而账本 blocked=0 unaccounted=0`** ——
正好是「账本与裁定打脸」的另一个方向。

---

## 四 裁判（只引用路径与末行）

| 裁判 | 命令 | 存档 |
|---|---|---|
| J1 探针 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/lifespan_isolation_guard_probes.py` | `evidence-w4-4/j1-guard-probes-*.txt` |
| J2 负控 | `… scripts/lifespan_isolation_negative_control.py` | `evidence-w4-4/j2-negative-control-*.txt` |
| J2 AST 负控 | `… scripts/lifespan_isolation_negative_control.py --ast-negative-control` | `evidence-w4-4/j2-ast-negative-control-*.txt` |
| J3 契约 | `… -m pytest -q -p no:cacheprovider tests/unit/test_live_port_guard_contract.py` | `evidence-w4-4/j3-contract-*.txt` |
| J4 目录级 | `… -m pytest -q -p no:cacheprovider --tb=line tests/api tests/regression`（开工 / 收工各一次） | `evidence-w4-4/api-regression-before-*.txt` / `-after-*.txt` |
| J4b tests/unit | 同上目录级，与本批基线 `evidence-b12/unit-red-baseline-03ac8bf8.txt` 逐 nodeid diff | `evidence-w4-4/unit-*.txt` |
| J5 运行时文件门 | `bash scripts/lifespan_isolation_runtime_sha.sh -- .venv/bin/python -m pytest tests/api -q -p no:cacheprovider` | `evidence-w4-4/j5-runtime-sha-*.txt` |
| J6 单快照/不变量 | grep + AST 双口径 | `evidence-w4-4/j6-grep-invariants-*.txt` |
| J7 before 证据 | 见 §二 | `evidence-w4-4/before-*.txt` |
| 拆门 | 见 §三 | `evidence-w4-4/mutation-teardown-*.txt` |
| ruff | `ruff format --check` / `ruff check` + 逐文件 HEAD 基线对比 | `evidence-w4-4/ruff-*.txt` |

> ⚠️ **本 session 的 zsh 5.9 不支持 `${PIPESTATUS[0]}`**（zsh 用 `$pipestatus[1]`，下标从 1 起），
> 早期一条存档的 `rc=` 因此为空，已在该文件尾补记说明并改用 `{ cmd; echo "rc=$?"; } 2>&1 | tee`。
> 另：`ruff` 那条第一次用裸 `$FILES` 展开，zsh 不做词分割 ⇒ 把 5 个路径当成 1 个文件名，
> 该次输出已作废并在新存档首行注明。

> ⚠️ **认存档后缀，别认文件名先后**。本卡的裁判跑了三轮，每轮都在**当时那份代码**上：
>
> | 后缀 | 跑的是哪份代码 |
> |---|---|
> | 无后缀 | 首版实现（未 `ruff format`） |
> | `-final-` | `ruff format` 落盘之后 |
> | **`-r2*`** | **Codex round-1 整改之后 = 要提交的那份，以这批为准** |
>
> 每轮都整套重跑（含拆门），而不是声称「这次改动不影响行为」——那正是「依据被自己
> 后一步消灭」那类问题的形状：判据必须跑在要提交的那份代码上。早两轮的存档保留，
> 用来看结论有没有随整改变化（`mutation-teardown-r2-*` 那次的 M1 `HARNESS-ERROR`
> 就是这么被看见的，见 §九.1）。

---

## 五 本卡未证明什么（如实）

1. **不证明 W4-⑤（AST 6 条口径）** —— Y8-B 的面；**不证明 W4-⑥（BASH_ENV）** —— Y7-B 的面。
2. **不证明 r2 存档 HIGH-1（自证地址伪装）在合并态的闭合** —— `_is_selftest_address` /
   `extract_port` / `port_is_trustworthy` 本卡一字未改，那是 Y8-A 的复审面。
3. **探针 ① 复现的是注入点制造的确定性交错，不是自然发生的时序**。真实竞态窗口有多宽、
   在真实负载下多久会撞上一次，本卡没有测量，也不打算测量——门要挡的是「有没有这个
   窗口」，不是「多久撞一次」。
4. **(b) 单快照在 (a) 落地之后没有独立的行为证据**。M2 变异**实跑**（不是推理，见 §九.2）：
   契约用例杀掉它，探针 `guard-ledger-matches-verdict` 存活——因为 (a) 之后任何落在两次
   快照之间的记录都会被判迟到并强制 rc=3，双快照的可观测分叉被 (a) 吸收了。(b) 因此是
   **结构性简化 + 纵深**，不是独立承重层；它的门是身份断言（`is`，不是 `==`）而不是行为门。
   **不得声称探针也在管这一条。**
5. **(e) 的 advisory 收紧面没有在 `tests/integration` 真跑验证**（本批禁跑 integration/e2e）。
   已验证的是：预检现在在 `pytest_configure` 期跑、当时归属为 `<unknown>` 且不豁免、
   全会话只调一次；以及 `begin_item` 的闩在契约用例里正反两向都成立。
6. **不做真连 7691 的活性验证**（本卡对 live vault 与 7691/7687 全程只读）。
7. **迟到路径重写账本是 fail-open 的**（写盘失败被吞，绝不阻断 `os._exit(3)`）。也就是说
   「账本文件与退出码一致」这句在**磁盘写失败**时不成立——承重的始终是那个非零退出码，
   账本只是给父进程的可观测性。这一点写进了函数 docstring。
8. **审计回调的迟到分支（含 `os._exit`）无法在 pytest 进程内测**，它只有子进程探针覆盖；
   契约用例锁的是 `record()` 的判定本身。
10. ⛔ **「`rc=3` ⇔ 账本 `unaccounted>0` 双向成立」这句我写宽了，现更正**（Codex r1
   MEDIUM-4）：最终结算与迟到路径是**两条独立的写盘路径，没有共同的发布顺序控制**。
   可达的交错是：结算取得零账快照 → 迟到线程记账并把文件重写成 `unaccounted=1` →
   结算线程用**旧快照**再 `open(path,"w")` 写回零账 → 迟到线程 `_exit(3)`。结果是
   **rc=3 而文件零账**。这是静态控制流证明，本卡**未做落盘竞争实测**，也**未修**。
   正确的措辞是：**承重的始终是那个非零退出码；账本文件是尽力而为的可观测性**。
   另外 `_final_accounting` 的 `blocked>0 and effective_status==0` 这一支也允许
   `unaccounted=0` 时退出 3 —— 「双向等价」本来就不该那么说。
9. **(d) 留下的一处残留边界（作者自查，如实登记）**：卡文要求
   `register_final_accounting()` 相对顺序**不变**（仍在预检之后），本卡照办。于是在
   「预检抛出 ⇒ 拒绝装门」这条路径上，audit hook 已装（能记账）而最终结算**没注册**——
   假如预检那一小段里真的发生了一次到受拦端口的连接，它会被拦下并记进 `STATE.blocked`，
   但没有 atexit 层把退出码兜成 3。实际后果有限：预检抛出的 `RuntimeError` 本身就会让
   `pytest_configure` 报错、会话非零退出；而且这比改动前**严格更好**（改动前那段连接
   既不被拦也不进账，见 before-3）。但它确实是「记了账却没有兜底层」的一个窄窗口，
   本卡**没有**闭合它，也没有为它写门。要闭合就得把 `register_final_accounting()` 一起
   提到预检之前——那超出卡文 (d) 的授权范围，登记为移交项。

---

## 六 台账待登记条目（车道不改台账，由主 session 登记）

1. 本卡合入后 `backend/tests/support/live_port_guard.py` 与
   `backend/tests/unit/test_live_port_guard_contract.py` 与 `e06009bc` **分叉**（预期；
   Y8-A 用 `git show e06009bc:` 只读钉那个 sha，不受影响）。
2. **`backend/tests/support/guard_plugin.py` 是本卡新增的写面**（原卡文只在 (e) 方案 A 下
   允许改）——本卡选了方案 A，该文件的 `pytest_configure` 与 session fixture 各改一处。
3. `T-1 / T-13 / T-15` 扫描面按 D-9c 登记**不做**。
4. `pyright` 例外提交按 D-14 附存档（`evidence-w4-4/pyright-r2-*.txt`，求交 = 0），见 §八。
5. ⛔ **Codex round-1 与最终代码失绑**（协议 §1「同一卡内审后再改 = 真失绑」）：按其
   HIGH-1 / HIGH-3 / MEDIUM-5 / MEDIUM-6 / LOW-9 / LOW-10 整改过，登记
   **「整改未复审」**。未整改的 HIGH-2 / MEDIUM-4 / MEDIUM-7 / MEDIUM-8 逐条理由见 §九。
7. **移交项（Codex 提出、本卡未闭合）**：HIGH-2 部分安装态无结算；MEDIUM-4 两条写盘
   路径无发布顺序；MEDIUM-7 AST 契约比宣称宽；MEDIUM-8 `record()` 持锁时 `repr(address)`。
6. 本卡在 `_bmad-output/审查/evidence-w4-4/` 下新增两个**可执行证据脚本**
   （`before-repro.py` / `mutation_teardown.py`）——它们会原地改生产文件后还原，
   **只能串行跑**，且跑的时候不要编辑它们的目标文件。

---

## 七 环境与例外

- 未往共享 venv 装任何东西（协议 §2.3）。
- Codex：`gpt-6-astra` + `ultra`，1 轮，存档 `_bmad-output/审查/codex-review-CARD-W4-4-settle-atomic.md`
  （首部按协议 §2.1 六行 blockquote）。
- pyright：见 §八。

## 八 pyright（D-14）

`lefthook.yml::python-typecheck` 现在**真阻断**（pyright 已在共享 venv 里）。本卡在
staged 面上跑 pyright 的原始输出落在 `evidence-w4-4/pyright-*.txt`，末行 `pyright-rc=`
（用 zsh 的 `$pipestatus[1]` 取，不是 `tail` 的 rc）。

**「报错不在本卡改动行」是算出来的，不是声称的**：同一份存档里附了一段求交——把
`git diff --unified=0` 的 `+` 侧行号逐文件收成集合，再与 pyright 报出的每一条
`file:line` 求交集。结果那一行写着「落在本卡新增行上的条目: 0」（pyright 条目总数与
各文件新增行数同时打印，便于复核这个判据本身没被写窄）。

因此本卡的 commit 走 `LEFTHOOK_EXCLUDE=python-typecheck`，属协议 §2.3 允许的例外
（本卡不改 `backend/app/**`）。存量 12 errors / 6 warnings 的清理不在本卡范围。

---

## 九 Codex round-1 逐条处置（⚠️ 含**失绑**声明）

存档 `_bmad-output/审查/codex-review-CARD-W4-4-settle-atomic.md`（首部按协议 §2.1，
会话头三行抄自 `.stderr`，stderr 本身不入库）。结论：**0 BLOCKER / 3 HIGH / 5 MEDIUM
/ 2 LOW**，每条都附了它自己的独立实测。

> ⛔ **失绑声明（协议 §1）**：Codex 审的是整改**之前**的工作区。我按它的 HIGH-1 /
> HIGH-3 / MEDIUM-5 / MEDIUM-6 / LOW-9 / LOW-10 改了代码与证据脚本，**该轮复核因此
> 不绑定最终代码**，按协议登记「整改未复审」。之所以选择改而不是「留着等下一轮」：
> HIGH-1 是**我自己引入**的一条跳过记账的旁路，HIGH-3 让我写下的「判迟到就必然退出 3」
> 成为假话——为了保住一个复核绑定而留着这两条，是拿门的真实强度换流程好看。

| # | 级别 | 结论 | 处置 |
|---|---|---|---|
| 1 | HIGH | seam 抛异常可在记账前跳过账；身份复核并非必然执行 | **已改**：seam 调用包 `try/except BaseException`，它对控制流的影响面收敛到 0；docstring 如实写明「承重的是这个 try，不是那道身份复核」。新增契约 `test_throwing_seam_cannot_skip_accounting` + 变异 **M8** |
| 2 | HIGH | 预检失败留下「已装 hook 但没注册结算」的部分安装态 | **不改，登记**：卡文 (d) 明令 `register_final_accounting()` 相对顺序不变。我在 §五.9 已自查登记过同一条；Codex 的独立实测把它坐实了。闭合需把注册也提前 = 超出本卡授权，移交 |
| 3 | HIGH | stderr 写失败可越过迟到路径的 `os._exit(3)`（既有缺口） | **已改**：迟到分支与最终总账的**报告整块**都包进 try，强制退出永远在 try 之外。新增探针 `guard-late-exit-survives-broken-stderr` + 变异 **M9**（拆掉后实测 rc=120 而非 3） |
| 4 | MEDIUM | 两条写盘路径没有共同的发布顺序，迟到账本仍可被旧零账覆盖 | **不改，登记 + 收窄措辞**：这是静态控制流证明、本轮未做落盘实测。我原先写的「`rc=3` ⇔ 账本 `unaccounted>0` **双向成立**」**过宽**，已在 §五.10 更正为「承重的是 rc，账本是尽力而为的可观测性」 |
| 5 | MEDIUM | `precheck_done` 是「曾经成功」，后续失败不撤销 | **已改 docstring**：如实写成「曾经成功过一次」+ 前提（预检输入会话期内不变）+ **为什么不做「入口清零」**（契约测试里十余处期望抛出的调用会把真 STATE 的闩永久留在 False，反而让 integration 集体失去 advisory —— 拿假想风险换真实回归） |
| 6 | MEDIUM | 变异裁判把「没跑到指定断言」也算 KILLED | **已改**：`run_tests` / `run_probe` 改**三态**（`PASS` / `FAILED` / `NOTRUN`），只有 `FAILED`（`-rf` 短摘要点名该 nodeid **且** 确实收集到 1 条）算击杀；另加 `_syntax_ok()` 与 `ANCHOR-MISS`。**这条修完当场抓到两个真问题**，见下方「自证」 |
| 7 | MEDIUM | 多条 AST 契约比它们声称锁住的性质宽 | **不改，登记 + 收窄措辞**：Codex 用内存构造的反例证明「测试支持不了它的完整宣称」（如「同一把锁」用例会接受 `with self.unrelated_lock`）。这些用例锁的是**当前实现没走那些错误结构**，不是「不可能走」；行为面的证明在探针与变异里。收紧到「精确检查接收者/可达顺序」需要另写一套 AST 匹配器，移交 |
| 8 | MEDIUM | `record()` 持锁时调 `repr(address)`，留了重入/抛出入口 | **不改，登记**：既有记账诊断结构，本卡只是让迟到分支也经过它。移交 |
| 9 | LOW | before 证据把未确认的线程状态打印成「已落账」 | **已改**：`join` 之后实测 `is_alive()` 与 `STATE.total`，不满足就打印 `STAGE-INVALID: …本次复现无效` |
| 10 | LOW | 部分时机注释与实际接线冲突 | **已改**：`canonical_target_ports` 的「两个调用方都在 configure 期或更晚」是错的（`guard_plugin` 在 **import 期** `install()`，开负控开关时预检当场跑），已按实际改写；`# 最终总账（所有 cleanup / atexit 之后）` 也已改成不与紧随其后的 LIFO 说明打架 |

### 九.1 MEDIUM-6 修完当场抓到的两个真问题（这条修得值）

把「rc≠0 就算击杀」换成三态之后，**同一批变异立刻报出两条 harness 故障**，而旧判据
会把它们记成 KILLED：

1. **M1 的锚点缩进漂移**：r2 把 seam 调用从 12 空格挪进 `try`（16 空格），而 12 空格版本
   恰好是 16 空格版本的**子串** ⇒ `str.count` 仍返回 1、替换成功、产出 `IndentationError`。
   那一轮 M1 的探针确实翻红了，但**红的原因是模块导不进来**，不是「锁外读丢了记录」——
   这正是「假杀第二形态」。修法：锚点按**行首**匹配（`"\n" + old`）+ 变异后 `ast.parse` 自检。
2. **M7 的锚点同样漂移**（`_rewrite_ledger_after_late_record()` 也进了 try），新判据如实
   报 `ANCHOR-MISS: 按行首匹配到 0 次`，而不是悄悄不打补丁然后宣布击杀。

最终 `mutation-teardown-r2c-*.txt`：**9/9 KILLED**，三文件还原逐字节相同。

### 九.2 M2「探针杀不掉」这句现在是跑出来的

Codex 判它「未判定」是对的：初版 M2 的 `probes` 是空列表，我却在验收单里断言「探针杀不掉」。
现在 M2 显式挂上 `guard-ledger-matches-verdict` 并真跑，harness 用 `expect_probe_survives`
把「预期存活」显式声明出来，输出里写着「已声明的预期存活: probe guard-ledger-matches-verdict」
——**是实跑结果，不是我替它下的结论**。
