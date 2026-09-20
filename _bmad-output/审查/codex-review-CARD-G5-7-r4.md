> 批次: BATCH-2026-09-18-第十五批 · 车道 P7-A · 卡 CARD-G5-7 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-7-r4.md)"`
> 审查绑定: `14fe770300df57c27e684d8b88ad5085b2052b78`（该轮送审时的 HEAD；其后本卡按审查意见改过代码，故**不绑最终 HEAD**，如实写明）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

**结论：本轮不通过。发现 6 HIGH、7 MEDIUM、1 LOW；未发现 BLOCKER。**

绑定 `14fe770300df57c27e684d8b88ad5085b2052b78`，结束时 HEAD 未变，三份文件与该提交一致。仅做静态审查及原始纯函数的内存核对；未修改文件、未联网、未运行会写盘的测试，因此不背书“77 全绿”的运行结果。

以下编号均为本轮编号。

1. **HIGH H1 — 续跑可以搬走新版，再由撤销静默覆盖成旧版。**  
   位置：[inbox_apply.py:669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:669)、[undo_journal.py:1103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:1103)。复用旧 entry 时，没有用已有的 `sha256_before` 核对当前源，尺寸与秒级 mtime 相等就放行。  
   复现：源为 `# AAAA\n`，令目标目录不可写，使 move 在备份和 acting 落账后失败；将源等长改为 `# BBBB\n` 并保持 preview 的 mtime，恢复权限后续跑、再 undo，最终成功恢复为 AAAA，BBBB 没有留痕。

2. **HIGH H2 — 同字节备份沿用共享 inode，既改用户文件时间，也失去独立快照。**  
   位置：[undo_journal.py:780](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:780)。同 SHA 分支直接沿用现存备份并 `utime`，没有排除指向另一份用户文件的硬链接。  
   对照：把测试 `test_backup_write_never_clobbers_a_hardlinked_neighbour` 中的用户文件改为与源同字节、不同 mtime；用户文件时间会改变，备份仍共享 inode，随后编辑用户文件便同步破坏唯一备份。这发生在 backup 阶段，不属于已登记的 acting 边界。

3. **HIGH H3 — 既有封口哨兵会容忍后来损坏的完整业务行。**  
   位置：[undo_journal.py:619](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:619)。`_tolerated` 跨过任意连续坏行寻找哨兵，无法确认哪些字节原本属于被封口的尾部。  
   复现：形成 `planned → 完整 acting → 半条 done → tail_sealed`，再让原本完整的 acting 行损坏；两条坏行都会被忽略，最新状态退回 planned，undo 报“未执行，无需还原”，实际产物仍在。保留 acting 完整的对照输入会真正撤销。

4. **HIGH H4 — 已产生文件的 acting 无法正常续跑。**  
   位置：[inbox_apply.py:410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:410)。`check_destinations_free` 仍只收集 planned/done，遗漏 acting，下一步因此拿不到归属记录。  
   复现：copy/link/move/recycle 主动作完成、done 尚未落账时中断，再用同输入 apply，会把本批产物判为外来文件而拒绝；现有续跑门及 H6 新门都在 **dst 尚未产生** 时失败，未覆盖此路径。

5. **HIGH H5 — 同 vault 的另一批账可以让不同决策被误报完成。**  
   位置：[undo_journal.py:851](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:851)、[inbox_apply.py:537](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:537)。绑定检查只核 vault，没有核行内 `batch_id`；完成复核又使用旧账的目标路径。  
   复现：同 preview，A 批 copy→节点、B 批 copy→归档；A 成功后将其原样 journal 放进 B 批目录，保持归档落点不存在，B 会验证节点中的旧产物并报完成，归档文件仍不存在。

6. **HIGH H6 — 回执发布仍会无留痕覆盖独立用户文件。**  
   位置：[undo_journal.py:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:471)、[undo_journal.py:486](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:486)。回执仅检查 symlink，随后无条件替换普通文件，没有归属检查或 stale 停放。  
   复现：首次 apply 前，在计算出的批目录放一份独立内容的 `receipt.md`，执行有效 skip/copy 后，该文件会被直接替换；“生成的回执可以重建”不能覆盖这个输入。

7. **MEDIUM M1 — 未知状态被静默忽略，可把已执行动作降回 planned。**  
   位置：[undo_journal.py:608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:608)、[undo_journal.py:507](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:507)。解析只要求对象含 `state`，后续却直接忽略不认识的值。  
   复现：在已有产物的 `planned → acting` 中，仅将 `acting` 改为 `actinh`；undo 不报账本状态损坏，而按 planned 成功跳过。原始 `latest_by_seq` 的内存核对确认了这一结果。

8. **MEDIUM M2 — `--undo` 指定的文件名没有被执行侧采用。**  
   位置：[inbox_apply.py:786](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:786)。CLI 验证参数是文件后，仅取父目录，再固定读取该目录的 `journal.jsonl`。  
   复现：传入 `--undo <batch>/receipt.json`，或同目录另一份存在的账文件，实际撤销的仍是 `journal.jsonl`，没有拒绝选错文件。

9. **MEDIUM M3 — 备份及记账失败不会进入承诺的失败回执流程。**  
   位置：[inbox_apply.py:679](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:679)、[inbox_apply.py:713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:713)。`try` 只包住 perform，backup、plan、mark_acting 和 commit 均在外面。  
   复现：两件 copy，第一件成功，第二件备份落点预置为 symlink；第二件抛错后直接退出，已完成第一件，却没有生成包含失败件号和完成数量的失败回执。

10. **MEDIUM M4 — “只有 planned”的撤销测试实际保留了 acting。**  
    位置：[test_g5_7_inbox_apply.py:1685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:1685)。夹具仅删除 seq2 的 done，已不再触达它声称验证的 planned 分支。  
    对照：删除实现中的 planned 特判，该门仍能经 acting 的“dst 缺席”分支通过；同时移除夹具中的 acting，并改变源内容或 metadata，才会独立验证“未执行项不碰源且不阻塞前项撤销”。

11. **MEDIUM M5 — H8 新门验证的是拼写，不能证明复制原子性。**  
    位置：[test_g5_7_inbox_apply.py:2002](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:2002)。该门只检查 `shutil.copyfile(` 消失以及 helper 存在。  
    对照：将 helper 改成直接 `open(dst, "wb")` 配合 `copyfileobj`，本门仍绿；缺少“复制已经开始后失败，正式文件不变、再次撤销成功”的行为断言。

12. **MEDIUM M6 — 目录链的两个关键拒绝条件仍未被独立承重。**  
    位置：[test_g5_7_inbox_apply.py:1756](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:1756)、[test_g5_7_inbox_apply.py:2054](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:2054)。前者被 `pre != at_act` 拒绝，后者被缺 pre 拒绝，不能独立证明跨环连续性；后者去掉缺 pre 守卫，又会被跨环比较挡住。  
    对照：令 seq1 为 `pre=at_act=100, post=200`，seq2 为 `pre=at_act=300, post=400`，实盘为 400，才能单独验证跨环断裂；缺 pre 则应另用只有一环的输入验证。

13. **MEDIUM M7 — H1 新门没有验证“搬产物之前拒绝”。**  
    位置：[test_g5_7_inbox_apply.py:1850](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:1850)。断言仅检查返回失败及 symlink 指向文件的权限、时间，没有检查 copy 产物仍在原落点。  
    对照：删除 `_undo_one` 搬产物前的源检查，后面的 `_finish_restore` 仍会拒绝，当前门仍绿，但产物已经被搬进 `recycle/undone/`。

14. **LOW L1 — 停放失败留下的 tmp 没有可供调用方追踪的结果。**  
    位置：[undo_journal.py:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:222)。守卫或停放失败直接返回，残片位置没有进入账本、回执或异常补充信息，后续重跑也不处理。  
    复现：stale 为 symlink，同时令回执发布失败；tmp 留在正式目录，修好 stale 并重跑后仍留存。就地保留是安全选择，缺陷是调用方无法获知需要处理哪份残片。

round-3 的十四项逐条结论如下；“成立”仅指原触发路径已经堵住，不代表整卡通过。

| round-3 项 | 本轮结论 |
|---|---|
| H1 | 实现成立；新门漏了搬前拒绝断言，见 M7 |
| H2 | planned 不认领成立；acting 接入遗漏引入 H4 |
| H3 | 部分成立；不同字节会停放，同字节硬链接仍有 H2 |
| H4 | symlink 守卫成立；停放失败不可观测，见 L1 |
| H5 | 封口后继续追加可读；真正中间损坏仍可能被容忍，见 H3 |
| H6 | 使用账上 meta 成立；已有产物的续跑被 H4 阻断 |
| H7 | acting move 搬回源后继续撤销的路径成立 |
| H8 | 原子替换实现成立；新门不足以证明失败恢复，见 M5 |
| H9 | apply 的 vault 绑定检查成立；批次绑定仍有 H5 |
| M10 | 按 seq 建环及缺 pre 拒绝成立；独立覆盖不足，见 M6 |
| M11 | 不同落点、第一件成功前提已修；跨环判据仍缺独立门 |
| M12 | 后缀先判、再读取成立 |
| L13 | stale 可用时，其余未发布 tmp 会一并停放 |
| L14 | 从全部行汇总 created_dirs 成立 |

另一个口径纠正：当前回执使用的是 `write_pair_atomically`，并非 `copy_file_atomically`。
