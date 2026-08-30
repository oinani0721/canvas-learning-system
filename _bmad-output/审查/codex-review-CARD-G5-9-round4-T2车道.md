# Codex 复核存档 — CARD-G5-9 round-4（窄范围实现审阅 · 确认轮）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **产出卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③
> **审阅对象**: `recap_exam_build.py` @ `d5b1d3c5`（round-3 四条 HIGH 整改后的形态）
>
> ## 裁决
>
> **仍有实现级缺陷** · BLOCKER 0 / **HIGH 5** / MEDIUM 2 / LOW 1
>
> 承重性与回归**全部确认**：14 个变体全红、基线与还原后各 62 passed、
> 源码 SHA 前后一致、指定回归 167 passed、工作树干净。
>
> ⚠️ 但 round-3 的四条整改被逐条判为 **FAIL / FAIL / PARTIAL / FAIL** ——
> **不是新功能出错，是我上一轮的修复自身有洞**。最刺眼两条：
> `os.stat()` 跟随 symlink 让「写入后复核」可被别名绕过；
> 回滚 helper 用 `None` 同时表示四种结果，导致**回执声称「已撤销」而实际没删**。
>
> 全部 5 条已整改，逐条处置与承重变体见 `codex-review-CARD-G5-9-round4-处置.md`。
>
> 复核者自述限制：严格未读测试源码；新发现为**单文件静态可达路径**，未另做注入用例；
> 明言「167 项绿灯与 14 个承重门不能覆盖上述组合失败、symlink 别名与 fsync 语义缺口」。

---

# 第 4 轮窄范围实现审阅报告

## 结论

**仍有实现级缺陷，不能判定为“自洽且承重”。**

14 个旧形态变体全部如期变红，167 项回归全绿，说明现有测试门确实承重；但静态复核仍发现 **5 条 HIGH**：包括可绕过目录事后复核而向 vault 外发布、撤销失败状态被吞、撤销回执失实，以及 undo 持久化失败被误判/忽略。

当前检出版本：`d5b1d3c54dcaaea559c497a891370831dc2b90c0`。

## 四项整改判定

| 整改 | 判定 | 摘要 |
|---|---|---|
| `_dirfd_still_in_vault()` | **FAIL** | 调用位置正确并覆盖所有成功发布路径，但 `os.stat()` 跟随 symlink，可被别名绕过。 |
| `published` 状态 | **FAIL** | `os.link` 后置 `True` 正确；内容不符分支在确认撤销结果前清零，导致漏报残留。 |
| `_rollback_published()` | **PARTIAL** | identity/SHA 基本判定正确；返回值无法区分“已删”和“拒删”，且双空参数会无条件删除。 |
| `_fsync_dir()` 与 undo | **FAIL** | 删除源文件前的 fail-closed 位置正确，但豁免语义和后续调用仍然 fail-open。 |

## 发现

### HIGH 1 — 目录事后复核可被 symlink 别名绕过

位置：[recap_exam_build.py:342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:342)、[recap_exam_build.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:357)、[recap_exam_build.py:741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:741)

静态反例：

1. 将已打开的 `检验白板/` rename 到 vault 外同一文件系统。
2. 在原路径创建指回该目录的 symlink。
3. `os.stat(vault / EXAM_DIR)` 跟随 symlink，所得 inode 仍等于 `dir_fd` inode。
4. 检查通过，随后仍可回报 `created:true`，实际文件位于 vault 外。

检查位于 `_atomic_write()` 成功后、成功回执前，**位置本身正确**；问题是判定没有拒绝 symlink。

“这是事后检测而非事前阻止”基本诚实，但“保证不会谎报成功”的表述不成立：除上述绕过外，检查与回执之间仍有移动窗口。

### HIGH 2 — 撤销失败后过早清除 `published`，失败详情被吞

位置：[recap_exam_build.py:504](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:504)、[recap_exam_build.py:513](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:513)、[recap_exam_build.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:521)

同 inode、内容 SHA 不符时：

- `_rollback_published()` 即使返回撤销失败，代码仍先执行 `published = False`。
- 随后抛出的详细异常被外层捕获。
- 外层重新设置 `rb_err = None`，最终只返回 `原子写失败: OSError`。

错误 target 可以继续存在，但回执不披露“已发布目标未撤销”。因此 round-3 的 published 状态整改没有完全成立。

### HIGH 3 — “因 SHA 不符而未删”被回报为“已撤销”

位置：[recap_exam_build.py:388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:388)、[recap_exam_build.py:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:409)、[recap_exam_build.py:745](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:745)

`_rollback_published()` 的 `None` 同时表示：

- 已成功删除；
- 文件已不存在；
- identity 不符而未删；
- SHA 不符而未删。

目录移动后的调用只传 `expect_sha=sha`。若内容已改变，helper 正确拒删并返回 `None`，但调用方仍拼接“已撤销该文件”。这是回执与实际副作用直接不一致。

### HIGH 4 — fsync 豁免把“未确认持久化”当作成功

位置：[recap_exam_build.py:279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:279)、[recap_exam_build.py:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:299)、[recap_exam_build.py:947](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:947)

- `EINVAL/ENOTSUP` 可以表示目录 fsync 不受支持，但这只表示**无法证明目录项已持久化**，不等于成功。
- `EPERM` 更不能可靠证明“不支持”，也可能是真实的权限或策略拒绝。
- 三者均返回 `None` 后，undo 会继续删除 vault 内源文件。

因此在崩溃模型下仍可能出现源已删、留痕目录项未落盘，即“两端皆失”。这与 fail-closed 承诺冲突。

### HIGH 5 — 删除源文件后的 fsync 结果被忽略

位置：[recap_exam_build.py:1066](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1066)、[recap_exam_build.py:1072](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1072)

`os.unlink(target)` 后调用 `_fsync_dir(target.parent)`，但完全忽略其返回值，随后无条件回报 `undone:true`。若发生目录打开失败、EIO 等真实持久化错误，崩溃后源文件可能重新出现，回执与持久状态分叉。

删除源文件**之前**的 fail-closed 分支位置正确；删除之后的持久化结果处理仍不闭合。

### MEDIUM 1 — rollback 核验与 unlink 间仍有按名称竞态

位置：[recap_exam_build.py:390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:390)、[recap_exam_build.py:398](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:398)、[recap_exam_build.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:411)

`lstat`/回读完成后仍按 basename `unlink`，期间可换入另一文件；SHA-only 调用甚至没有把回读 fd 的 identity 绑定到最终删除。属于已声明的残留窗口，按要求定为 MEDIUM。

### MEDIUM 2 — `_fsync_dir()` 的 close 异常逸出返回契约

位置：[recap_exam_build.py:292](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:292)、[recap_exam_build.py:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:302)

`os.close(fd)` 位于未捕获的 `finally` 中；若 close 抛错，不会按函数契约返回失败字符串，而会直接逸出并破坏 JSON 回执。未发现正常路径 fd 泄漏，所有 fd 均至少进入关闭路径。

### LOW 1 — 双空判据会无条件删除

位置：[recap_exam_build.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:370)、[recap_exam_build.py:396](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:396)、[recap_exam_build.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:411)

`identity=None` 且 `expect_sha=None` 时会跳过两个判据并直接 `unlink`。

当前三个调用点均至少传入一个：

- `510–512`：identity；
- `531–533`：identity；
- `747`：SHA。

因此当前不可达，属于潜在接口陷阱。

## 承重性与回归

- 14 个变体：**全部如期变红**。
  - A：7 failed；
  - K、M、N：各 2 failed；
  - 其余变体均至少 1 failed。
- 负验证基线：`62 passed`。
- 还原后：`62 passed`。
- 脚本结果：`RESULT: PASS — 全部新门均为承重门`。
- 初始与最终源码 SHA-256 均为：  
  `7a8d1dc9aa300becfd81f7805e63da5d3e699b7a4a4d30368974becaea30ff36`
- 指定回归：`167 passed in 13.31s`。
- 最终 `git status --short`：无输出，工作树干净。

## 验证限制

- 严格未打开或读取 `backend/tests/skills/test_g5_9_recap_exam.py`。
- 未读取其他实现源码或 round-3 处置文档。
- 测试源码仅由指定命令执行；新发现基于当前实现调用链的静态反例，未额外编写或运行注入用例。
- 167 项绿灯及 14 个承重门不能覆盖上述组合失败、symlink 别名和 fsync 语义缺口。

## 残留清单

- BLOCKER：0
- HIGH：5
- MEDIUM：2
- LOW：1


