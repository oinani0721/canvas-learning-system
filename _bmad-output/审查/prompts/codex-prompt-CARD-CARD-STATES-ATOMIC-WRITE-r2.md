# 独立复核 round-2：CARD-CARD-STATES-ATOMIC-WRITE（BATCH-2026-09-18-第十五批 / 车道 P4）

## ① 背景与最小读取面（只读这些，不要扩大搜索面）

round-1 你给出 BLOCKER=0 / HIGH=1 / MEDIUM=3 / LOW=1。本轮已按其中可在本卡地盘内
处理的部分整改，请独立复核整改本身，并重新判定全部等级。

只读下面这些：

1. 本卡 diff：`git --no-pager diff --no-color 9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680 d7ab47c811230989765cb65568ff6b6b15ea7b7e -- . ':(exclude)_bmad-output'`（恰 3 个文件）
2. round-1 到本轮的增量：`git --no-pager diff --no-color 7a5081f197b364c6eb7d1db99e0382e0d4aa7a4f d7ab47c811230989765cb65568ff6b6b15ea7b7e -- . ':(exclude)_bmad-output'`
3. `backend/app/services/review_service.py`：`:60-70`（import 段）、`:655-735`
   （`_tmp_is_ours` 与 `_persist_card_states_bytes`）、`:950-1080`
   （`_load_card_states` / `_save_card_states` 全貌与两个异常分支）
4. `openspec/specs/concept-identity/spec.md` 改后全文（150 行，7 个 Scenario）
5. `backend/tests/regression/test_g3_7_truth_source.py`：`:74-135`（既有 fixtures）与
   `:685` 到文件末尾（本卡新增的整段，11 个 `concept_identity_s<N>` test）
6. 范式对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:582-611`
7. 不复用理由对照 `backend/app/utils/atomic_io.py:47-91`（本卡不改，已登记另立卡）
8. 本轮裁判存档（**round-1 的问题 7 需要它**，都在 `_bmad-output/审查/evidence-card-states-atomic/`）：
   - `probe-cancel-thread-*.txt` —— 对你 round-1 HIGH 的三个前提的实测
   - `negctl-r2-{1,2,3}-*.txt` 与同名 `-sha-before/-sha-after`、`-mutant-diff-` —— 三段负控输入
   - `redbind-ctrl-*.txt` —— 把实现整体换回 `9c4e7e82` 形态的对照输入
   - `dir-regression-r2-*.txt` / `suites-r2-*.txt` / `unit-r2-*.txt` —— 绑本 HEAD 的目录级
   - `ast-after-head-*.txt` / `ast-falsification-anchor-*.txt` / `pyright-r2-*.txt` / `ruff-*.txt`

> ⚠️ round-1 我给的 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:149`
> 在**本车道树**的副本里不存在（该副本只有 111 行，行号是另一棵树的）。本轮已删除该引用。

## ② 本轮整改自述（请独立核对，不要采信）

1. **HIGH（交叉删除）已修**：`_persist_card_states_bytes` 在 `open` 后用
   `os.fstat(fh.fileno()).st_ino` 记下 inode，`finally` 改为
   `if _tmp_is_ours(tmp, tmp_ino): tmp.unlink(missing_ok=True)`。
   你 round-1 的三个前提我实测了（存档 `probe-cancel-thread-*.txt`）：协程取消后
   `lock.locked()` 为 False、锁可被重获、线程跑完、A 的 `finally` 确实删掉了 B 的 tmp、
   两者 inode 不同。新增门 `…s6_cleanup_spares_a_foreign_tmp`；负控输入
   `negctl-r2-3`（把认领换成 `if True:`）让它且只让它变红。
2. **MEDIUM「finally 覆盖范围没被绑住」已补**：新增 `…s6_write_phase_failure_leaves_no_residue`
   让**文件 fsync** 失败；负控输入 `negctl-r2-1`（拆掉清理动作）现在让**两条**残留门同时变红。
3. **MEDIUM「`:844` 分不清从没建过与建了又清掉」已补**：S3 现在用 open 探针断言
   `.json.tmp` **从未以写模式被打开过**。
4. **MEDIUM「目录 fsync 未被拦下」已补**：新增
   `…s6_directory_fsync_failure_is_reported_not_swallowed`，钉住「目标其实已落位、
   仍返回 False、脏标记保留」这个如实面，并断言第二次 fsync 真的被走到。
5. **MEDIUM「spec 零残留承诺过宽」已改**：Requirement 现在写「每条失败路径 MUST attempt to
   remove」，并写明 `missing_ok=True` 只吞 `FileNotFoundError`、清理自身失败按 OSError 归一；
   同时写明清理只认领本次 inode 及其理由。
6. **LOW「Scenario 1 仍写 `Path.replace`」已改**为 `os.replace`；新增 Scenario 7 描述认领规则。
7. **未改、如实登记的一条**：spec 里「On a successful replace the method MUST clear …」那一段
   落在卡文规定的**一字不动**区间（原 `:34-57`，T4-C 收窄结论），本卡无权改动。目录 fsync
   失败确实使该句不再逐字成立，已在验收单登记待裁，并由第 4 条新门把该失真做成可观测的。
8. **仍未做（卡文硬边界）**：不给 tmp 换随机名、不加跨进程锁，故跨进程 / 多 worker 在同一
   路径上互相截断仍不在保护范围内。

## ③ 请按重要性回答

0. inode 认领是否**真的**切断了你 round-1 描述的那条路径？有没有**未被拦下的输入**
   仍能让一次落盘删掉或截断另一次的 tmp（单进程内）？`os.stat` 与 `unlink` 之间的
   TOCTOU 窗口在本仓的调用频率下是否值得进一步处理？
1. `_tmp_is_ours` 在 `OSError` 时返回 `False`（不删）。这是否引入了**新的残留面**——
   某条失败路径上 `os.stat` 失败而 tmp 确实存在且确实是本次的？
2. 三段负控输入是否各自只拆了一层？有没有**门未覆盖的路径**：某个变异体能让 11 条全绿？
3. spec 改后的 Requirement 有没有仍然超出实现的承诺？请逐句对照。
4. 新增三条门里有没有哪一条在**对照输入**（把实现换回 `9c4e7e82` 形态）下也是绿的——
   若有，它没有绑住本卡引入的任何行为。
5. `…s6_directory_fsync_failure_is_reported_not_swallowed` 里 `len(seen) == 2` 这个
   探针存活锚够不够？它会不会在实现改变 fsync 次数时误红而不是真正失效时误绿？
6. round-1 的问题 7（目录级是否真的在最终 HEAD 上跑）现在有存档了，请核对存档里的
   SHA / 退出码 / passed 与 skipped 的区分，并说明还缺什么。
7. pyright 0 errors 是否靠 ignore 掩盖（本卡新增 ignore 自述为 0）。

## ④ 输出格式

逐条列 `BLOCKER / HIGH / MEDIUM / LOW`，每条给 `file:line` + 一句复现思路。
措辞统一用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
最后给一行：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## ⑤ 边界

只读，不写任何文件；不连数据库；不评 `next_review` 迁移（P4-B）；不评
`backend/app/utils/atomic_io.py` 该怎么修；不评 `tests/unit` 的隔离问题；不评
`backend/app/models/**`；不评那段被卡文锁死的 spec 文字**该不该**改（只可指出其失真）。
