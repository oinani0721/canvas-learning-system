# 独立复核：CARD-W4-4-settle-atomic（测试隔离门的结算原子性）

## 一 背景与最小读取面

被审对象是一个 **pytest 测试进程内的隔离门**：它监听 CPython 的 `socket.connect`
审计事件，阻止测试进程连上开发机上的 Neo4j（端口 7691 / 7687），并在进程退出前做
一次「最终结算」——发现有拦截记录无人认领，就把进程退出码强制成 3。

本次改动修的是**这道门自己的一处假绿**：最终结算把「置结算标志」与「取账本快照」
写成两条独立语句，而审计回调对那个标志是锁外读、记账又在另一把锁里。三者不在同一
临界区，于是一条拦截记录可以既不进结算快照、又不触发迟到路径，进程照常以 0 退出。

**请只读这几处，不要扩散到仓库其它部分**（工作目录 = 本仓库根）：

1. `git diff` 的全部内容（本次改动面：`backend/tests/support/live_port_guard.py`、
   `backend/tests/conftest.py`、`backend/tests/support/guard_plugin.py`、
   `backend/tests/unit/test_live_port_guard_contract.py`、
   `backend/scripts/lifespan_isolation_guard_probes.py`，以及 `_bmad-output/` 下的证据）；
2. `backend/tests/support/live_port_guard.py` **全文**（1300 余行，含模块 docstring）；
3. 需要时再看 `backend/tests/conftest.py` 的 pytest 接线段（约 :83-215）与
   `backend/tests/support/guard_plugin.py`（全文 55 行）。

证据文件（可读，用于核对作者自述是否与实测一致）：
`_bmad-output/审查/evidence-w4-4/`（`before-repro.py` + 各裁判的 `*.txt` 存档 +
`mutation_teardown.py` 与它的输出）。

## 二 作者自述（请独立核对，不要采信）

作者声称做了六件事：

- **(a) 结算原子化**：新增 `_GuardState.finalize_and_snapshot()`，在**同一次持锁**内
  置 `self.finalizing` 并取账本快照；`record()` 改为在**同一把锁**内先看该标志，已结算
  就返回 `RECORD_LATE`。审计回调不再对结算标志做锁外读，模块级 `_FINALIZING` 已删除。
  作者声称：一条记录只有两种归宿——在快照里，或被判迟到——没有第三种。
- **(b) 单快照**：`write_ledger(path, ledger=None)` 接收快照；`_final_accounting` 把
  `finalize_and_snapshot()` 的返回值传下去，裁定与落盘用同一个 dict 对象。
- **(c) 迟到路径重写账本**：迟到记录照常进账（`total`/`blocked`/`pending` 都加，且**不看
  豁免**），并在 `os._exit(3)` 之前用 `late_snapshot()` 把账本文件重写一次，使
  「退出码 3 ⇔ 账本 `unaccounted>0`」两个方向都成立。
- **(d) install 顺序**：`_install_audit_hook()` 提到目标预检 `assert_neo4j_target_blocked()`
  之前；`register_final_accounting()` 相对位置不变（仍在预检之后）。
- **(e) 预检时机**：`assert_test_uri_not_blocked()` 从 session autouse fixture 上移到
  `pytest_configure`（根 conftest 与 guard_plugin 两处），并在 `_GuardState` 上加
  `precheck_done`，`begin_item()` 在预检未完成时**不发豁免票**。
- **(f) 注入点**：新增 `_finalize_race_seam` / `_finalize_race_seam_hook` —— 一个默认
  no-op、被审计回调无条件调用、返回值被丢弃的函数；`assert_guard_live()` 复核它未被替换。

作者同时**自己声明**了两处局限，请一并判断这两句是否如实：

- (b) 在 (a) 落地之后**不再有独立可观测的行为差异**（作者的变异实测里，只有契约用例
  能杀掉「双快照」这个变异，探针杀不掉）；
- 探针 `guard-finalize-race-loses-record` 复现的是**注入点制造的确定性交错**，不是自然
  发生的时序。

## 三 请按重要性排序回答（每条给出结论 + 依据行号）

1. **注入点未被替换时是否完全惰性**：`_finalize_race_seam_hook` 是否出现在任何判据、
   分支条件、等待或环境变量读取里？它的返回值是否可能影响「拦 / 不拦」的结论？
   `assert_guard_live` 对它的身份复核是否留下了门未覆盖的路径（例如某些调用序列下
   这道复核根本不会跑）？
2. **`finalize_and_snapshot()` 与 `record()` 是否真的在同一个临界区**：置标志与取快照
   之间是否还存在任何间隙？是否还有其它地方在锁外读写 `finalizing`？作者「只有两种
   归宿」的说法在多线程下是否成立，还是存在第三种落点？
3. **单快照是否闭合**：结算路径上是否只取一次快照？`write_ledger` 的 `ledger=None`
   默认值是否给结算路径留了一条可以再取一次的入口？
4. **install 顺序变更是否引入了新的门前窗口或新的失败模式**：把审计回调装到预检之前，
   是否让某些原本会被拒绝装门的对照输入变成「门已装、随后才拒绝」？预检抛出时
   `register_final_accounting()` 不执行，这个组合是否会留下未结算的账？
5. **(e) 的 advisory 语义变化**：预检上移之后，`tests/integration` / `tests/e2e` 的豁免
   语义有没有被改宽？`begin_item` 的 `precheck_done` 闩是否可能在某条路径上永久为
   False，从而让本该豁免的用例一直不豁免（或反过来）？预检在 `pytest_configure` 期
   抛出时，会话的失败形态与上移前是否等价？
6. **`_lock` 是否被嵌套获取**：`_lock` 是不可重入的 `threading.Lock`。`finalize_and_snapshot`
   / `late_snapshot` / `record` / `_mark_precheck_done` / `begin_item` 里是否存在
   「持锁时再调一个会取锁的方法」？`_rewrite_ledger_after_late_record()` 在审计回调里
   被调用，它会取锁——这条路径上是否可能已经持有该锁？
7. **迟到路径重写账本的副作用**：它跑在解释器收尾期、任意线程里，写文件失败被吞掉。
   这个 fail-open 选择是否可能让账本文件与退出码在某些对照输入下重新对不上？
8. 新增的契约用例与探针里，有没有**判据比它声称的宽**、或者「没有发生」被当成
   「验证通过」的地方？特别是那些用 AST 断言结构顺序的用例——它们锁住的是否就是
   它们声称锁住的那件事？
9. 其余你认为重要的问题（含文档/注释与实现不一致）。

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条写：

- 标题（一句话）
- 位置（文件:行号）
- 为什么成立（推理链，或你实际读到的代码依据）
- 建议的处置方向（一句话即可）

最后给一段「作者自述里哪几句与代码不符 / 比代码宽」的清单。若某条你无法判定，
请明确写「未判定」并说明缺什么信息，不要给推测性的结论。

## 五 边界（不在本次复核范围）

- `backend/scripts/lifespan_isolation_runtime_sha.sh` 与探针里的
  `probe_shell_injections()`（另一张卡 Y7-B 的面）；
- `backend/scripts/lifespan_isolation_negative_control.py` 的 AST 门本体（Y8-B 的面）；
- `_is_selftest_address` / `extract_port` / `port_is_trustworthy` 的地址判定（Y8-A 的
  复审面，本次未改动）；
- 仓库其它目录（`backend/app/**` 等）与本次改动无关，请不要展开阅读。

只读复核，不要修改任何文件。
