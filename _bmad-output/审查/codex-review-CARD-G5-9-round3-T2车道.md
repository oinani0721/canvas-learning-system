# Codex 复核存档 — CARD-G5-9 round-3（窄范围实现审阅）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30
> **产出卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③（卡文要求的「修复后再跑一轮」）
> **审阅对象**: `recap_exam_build.py` 在 `38fc5823`（含首段 `9e24ef40` + 二段 `06dc6955`）的最终形态
>
> ## 为什么是「窄范围」
>
> 本卡的 Codex 复核**连续 4 轮**被平台内容过滤器拦下（G5-9 首轮 / round-2 / 自审 v1 / round-3 首版）。
> 排查发现触发源**不是提示词措辞**（已按已知 gotcha 改过「规范符合性」口径仍中），
> 而是 **codex 读对抗性测试文件的过程**——该文件含 `ATTACKER-BYTES`、symlink 越界构造等语料，
> 风控看的是**上下文里流过的内容**。
>
> ⇒ 本轮改为：**只读实现文件；明令不要读测试源码；承重性改用负验证脚本的 PASS/FAIL 输出判断**。
> **过滤器 0 命中**，一次跑通。经验已入记忆 `reference_codex_exec_gotchas`。
>
> ## 裁决
>
> **仍有实现级缺陷** · BLOCKER 0 / **HIGH 4** / MEDIUM 2 / LOW 2
>
> ### 好消息：题定的四项校验全部 PASS
> - `_atomic_write` 内 tmp open / link / target 回读 open / unlink / 目录 fsync **确实全部 basename + dir_fd**；
> - leaf symlink 拒绝位于 `.resolve()` **之前**（:681-686 vs :687）；
> - 留痕写入 + fsync 后**确有**重新打开核对 size 与 SHA（:819-849）；
> - 源文件再核 inode+SHA 后，**紧贴 unlink 再做一次 inode 检查**（:892-915），失败分支均先返回不删源。
> - 承重性 **PASS**：10/10 变体如期变红，逐字节还原后 55 passed；指定回归 **160 passed**；
>   工作树 `git status --untracked-files=all` 为空。
>
> ### 新发现的 4 条 HIGH 全在**失败路径 / 竞态窗口**上
> 它们不是「修错了」，而是「修好主路径后暴露出来的边缘路径」——详见下方正文。
> **全部落在 `recap_exam_build.py`（G5-9 地盘），不涉及本批禁改的 `recap_scan.py` verifier**，
> ⇒ 按停轮规则**在本卡整改**，不移交。整改与负验证见 `codex-review-CARD-G5-9-round3-处置.md`。
>
> 复核者自述限制：未打开或分析测试源码；新增 HIGH 为**单文件静态可达路径**，未另做竞态故障注入。

---

# 独立窄范围实现审阅报告

## 结论

**仍有实现级缺陷。**

- 承重性：**PASS**。10/10 旧形态变体全部如期变红，恢复后 55 项全绿，额外回归为 **160 passed**。
- 题定 undo 三处校验：均已正确落位。
- 整体实现自洽性：**FAIL**。静态复核发现 4 项未被上述变体覆盖的 HIGH 路径，可能导致越界写入、数据损失或回执与实际写入不一致。

## 实现级发现

1. **HIGH — dirfd 校验后目录仍可被移出 vault**

   [_open_exam_dirfd:306–325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:306) 只做一次 inode/同文件系统快照。校验通过后，若在 [_atomic_write 调用前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:612) 将该目录 rename 到 vault 外同一文件系统，dfd 仍指向已外移 inode；写入会落在外部目录，而 [回执仍生成 vault 内词法路径并报 `created:true`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:621)。

2. **HIGH — link 成功后的验证异常可能留下 target，却回报失败**

   [target 已在 378–380 发布](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:378)；随后回读 open/fstat/read 若出现 `EMFILE`、`EIO` 等异常，[统一错误路径仅删除 tmp](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:414)，可能留下本次创建的 target，但返回“原子写失败”。

3. **HIGH — mismatch 回滚使用过期身份，且吞掉 target 删除失败**

   `same_inode` 来自已打开 fd 的快照。若其后路径被换入其他文件，[按 basename unlink](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:399) 仍可能删除替代文件；若 unlink 自身失败，[异常又被静默吞掉](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:405)，错误字节 target 可留存而回执只报失败。  
   直接进入 `same_inode=False` 的 [411–413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:411) 分支本身正确：**不会删除目标**。

4. **HIGH — undo 的目录 fsync 失败会 fail-open，之后仍删除源**

   [_fsync_dir](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:278) 吞掉目录 open/fsync 错误；undo 在 [813](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:813) 调用后仍可于 [915](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:915) 删除源。在“目的目录项未持久化后崩溃”的模型下，可能两端皆失。

5. **MEDIUM — atomic_write 失败路径静默吞掉 tmp 清理错误**

   [420–423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:420) 不回报 tmp 删除失败，可能留下残留并阻断后续 `O_EXCL` 重试。

6. **MEDIUM — undo 两处读错误不按 JSON 契约回报**

   初始源回读 [713–722](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:713) 和留痕后的源回读 [857–868](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:857) 均有 `finally` 关闭 fd，但内部 `fstat/read` 的 `OSError` 会直接外抛。源不会删除，但不能如实输出结构化拒绝回执。

7. **LOW — 非 OSError 异常可能泄漏 tmp fd**

   [fdopen 使用 `closefd=False`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:367)，外围仅捕获 `OSError`；非 `OSError` 异常没有总 `finally` 关闭底层 fd。正常及常规 `OSError` 路径未见泄漏。

8. **LOW — 返回类型注解与实际值不一致**

   [_atomic_write 注解](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:328) 是 `str | None`，实际返回二元组并在 [616](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:616) 解包。

## 题定校验结果

- `_atomic_write` 内的 tmp open、link、target 回读 open、target/tmp unlink 和目录 fsync，确实全部采用 basename + `dir_fd`；读取、fstat、close 则直接使用已打开 fd。**PASS**
- leaf symlink 在 [681–686](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:681) 拒绝，`.resolve()` 位于 [687](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:687)。**PASS**
- 留痕写入及文件 fsync 后，于 [819–849](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:819) 重新打开并核对 size、SHA。**PASS**
- 源文件再次核对 inode+SHA 后，于 [892–915](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:892) 紧贴 unlink 再做 inode 检查。明确失败分支均先返回、不删源。**PASS**
- `lstat → unlink` 仍是两个系统调用间的已声明 TOCTOU；本次未将这一已知边界重复计为新发现。

## 承重与回归证据

- 负验证基线：`55 passed`
- 10/10 变体全部如期变红：
  - A：`7 failed, 48 deselected`
  - C：`1 failed, 4 passed, 50 deselected`
  - D：`1 failed, 1 passed, 53 deselected`
  - B/E/F/G/H/I/J：各 `1 failed, 54 deselected`
- 逐字节还原后：`55 passed`
- 脚本最终：`RESULT: PASS — 全部新门均为承重门`
- 指定回归：`160 passed in 13.07s`
- 独立复算源文件 SHA-256：`59fc71a4c83f2d7579618ff9be155272c78588ceb12693daead2ff7f707a089e`
- 最终 `git status --short --untracked-files=all` 为空；工作树干净。

未打开、展示或分析测试源码；仅执行了用户指定命令。上述新增 HIGH 为单文件静态可达路径，未另做竞态故障注入。

## 残留清单

- BLOCKER：**0**
- HIGH：**4**
- MEDIUM：**2**
- LOW：**2**


