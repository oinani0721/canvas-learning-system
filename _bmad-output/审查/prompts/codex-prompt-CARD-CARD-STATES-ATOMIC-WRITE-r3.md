# 独立复核 round-3：CARD-CARD-STATES-ATOMIC-WRITE（BATCH-2026-09-18-第十五批 / 车道 P4）

## ① 背景与最小读取面

round-1: BLOCKER=0 HIGH=1 MEDIUM=3 LOW=1。round-2: BLOCKER=0 HIGH=1 MEDIUM=5 LOW=0。
本轮已按 round-2 整改，**并撤回了 round-2 那层 inode 认领**（见 §②）。请独立复核并重新判级。

只读下面这些：

1. 本卡全量 diff：`git --no-pager diff --no-color 9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680 b173eb4480d8ca00b98474d576c3c4c723fe32b3 -- . ':(exclude)_bmad-output'`（恰 3 个文件）
2. 相对 round-2 的增量：`git --no-pager diff --no-color d7ab47c811230989765cb65568ff6b6b15ea7b7e b173eb4480d8ca00b98474d576c3c4c723fe32b3 -- . ':(exclude)_bmad-output'`
3. `backend/app/services/review_service.py`：`:60-72`（import 段）、`:660-725`
   （`_card_states_file_lock`:668 + `_persist_card_states_bytes`:671）、`:930-1060`
   （`_load_card_states`:937 / `_save_card_states`:981 全貌，含 `:1041` 与 `:1053` 两个异常分支）
4. `openspec/specs/concept-identity/spec.md` 改后全文（6 个 Scenario）
5. `backend/tests/regression/test_g3_7_truth_source.py`：`:74-135`（既有 fixtures）与
   `:685` 到文件末尾（本卡新增段，12 个 `concept_identity` test + 1 个 `_WriteRefusingFile` 代理）
6. 范式对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:582-611`
7. 本轮裁判存档，全在 `_bmad-output/审查/evidence-card-states-atomic/`：
   - `probe-cancel-thread-*.txt` —— 对「取消后锁释放、线程续跑、同路径互删」三个前提的实测
   - `negctl-r3-{1,2,4,5,6}-*.txt` + 同名 `-sha-before-` / `-sha-after-` / `-mutant-diff-` —— 五段负控输入
   - `suites-final-*.txt` / `dir-regression-final-*.txt` / `unit-final-*.txt` —— 绑最终 HEAD 的目录级，
     **文件首部写了 HEAD、开跑时刻、实际命令、以及两个源码文件的 sha256**；`unit-final-*.txt` 末尾
     另有收工后 sha256，可与首部逐字比对
   - `territory-ruff-r3-*.txt`（地盘 + ruff，带 HEAD）、`pyright-r3-*.txt`、`ast-after-r3-*.txt`、
     `ast-falsification-anchor-*.txt`、`byte-equivalence-write-*.txt`
   - `unit-r2-*.txt` 首部已标注**作废**（跑到 22% 时源码被改，已 TaskStop 中止），请勿采信

## ② 本轮整改自述（请独立核对，不要采信）

1. **round-2 HIGH 已按你指的根因修，但方向是撤回而不是再加一层**：你指出 B 若在 A replace
   **之前** `open(tmp,"wb")` 会 truncate 同一个 inode，认领认不出来。因此 `_tmp_is_ours`
   **整个删除**，改为整段落盘持有模块级 `threading.Lock`（`_card_states_file_lock`），
   `finally` 恢复无条件 `tmp.unlink(missing_ok=True)`。随之 round-2 的 Scenario 7 与
   `…cleanup_spares_a_foreign_tmp` 门也一并删除（它们绑的是已撤回的那层）。
2. **round-2 MEDIUM-2（认领引入的未清理路径）随撤回一并消失**。
3. **round-2 MEDIUM-3 已补两条**：`…s6_write_failure_leaves_no_residue` 让 **`write` 自己**
   失败（经 `_WriteRefusingFile` 薄代理，只拦 `write`、其余转发真文件对象）；
   `…s6_fsync_precedes_replace` 加了 `os.fstat(fd).st_size == len(expected)` 判据，钉住
   「flush 先于 fsync」。
4. **round-2 MEDIUM-4 已改**：目录门不再按「第几次调用」判定，改按 `stat.S_ISDIR(os.fstat(fd).st_mode)`
   识别对象，并断言父目录 inode 确实被 fsync 过、文件 fsync 先于目录 fsync。
5. **round-2 MEDIUM-5 已改**：Requirement 去掉 inode 措辞、写明线程锁及其只覆盖进程内；
   锁那一段补了一句「asyncio.Lock 不覆盖被取消后仍在跑的线程」。
6. **round-2 MEDIUM-6 已补**：三份目录级存档首部自带 HEAD + 命令 + 源码 sha256，
   `unit-final-*.txt` 末尾有收工后 sha256；负控存档补齐了 `-sha-after-`。
7. **新增第 12 条门** `…s6_persist_is_serialized_across_threads`：四条线程直接跑
   `_persist_card_states_bytes`（真生产函数），以「tmp 被写模式 open ↔ `os.replace` 返回」
   为临界区边界测重叠；负控输入 `negctl-r3-4`（把锁换成 `nullcontext()`）让它且只让它变红。
8. **仍未做（卡文硬边界）**：不换随机 tmp 名、不加跨进程锁 ⇒ 跨进程/多 worker 仍不在保护范围。
9. **仍未改、如实登记**：spec 里「On a successful replace … MUST clear …」落在卡文规定的
   一字不动区间，目录 fsync 失败确实使该句不再逐字成立，已由第 4 条门做成可观测并登记待裁。

## ③ 请按重要性回答

0. 线程锁是否**真的**让整段串行？还有没有**未被拦下的输入**能让两条线程同时落在同一个
   `.json.tmp` 上（单进程内）？`_persist_card_states_bytes` 是模块级函数，是否存在
   绕开该锁的调用路径？
1. 把锁放在**线程**层而不是协程层，有没有引入新的问题：线程池耗尽、长时间阻塞、
   与事件循环的交互、或某条路径上的死锁？
2. 五段负控输入是否各只拆一层？有没有**门未覆盖的路径**：某个变异体能让 12 条全绿？
3. spec 改后的 Requirement 有没有仍然超出实现的承诺？请逐句对照。
4. 12 条门里有没有哪一条在**对照输入**（把实现整体换回 `9c4e7e82` 形态）下也是绿的？
   哪几条绑的是本卡引入的行为、哪几条只是既有行为的回归门？
5. `_WriteRefusingFile` 这个薄代理是否偏离了「不 mock 内部实现」的口径？它转发 `__getattr__`
   与 `__enter__/__exit__`，是否可能让被测路径与生产路径产生语义差？
6. 目录 fsync 门的新判据（`S_ISDIR` + 父目录 inode + 文件先于目录）是否还会误红或误绿？
7. 存档现在能否闭合「目录级确实在最终 HEAD 上跑完」：请核首部 HEAD / 命令 / 源码 sha256、
   末尾摘要与 `pytest_rc`、以及 passed 与 skipped 的分列，并说明还缺什么。

## ④ 输出格式

逐条列 `BLOCKER / HIGH / MEDIUM / LOW`，每条给 `file:line` + 一句复现思路。
措辞统一用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
最后给一行：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## ⑤ 边界

只读，不写任何文件；不连数据库；不评 `next_review` 迁移（P4-B）；不评
`backend/app/utils/atomic_io.py` 该怎么修；不评 `tests/unit` 的隔离问题；不评
`backend/app/models/**`；不评那段被卡文锁死的 spec 文字**该不该**改（只可指出其失真）。
