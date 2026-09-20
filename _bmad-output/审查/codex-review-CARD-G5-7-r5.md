> 批次: BATCH-2026-09-18-第十五批 · 车道 P7-A · 卡 CARD-G5-7 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-7-r5.md)"`
> 审查绑定: `293f8d6a8f4a04a9debb120db63dc0d1752dc334`（该轮送审时的 HEAD；其后本卡按审查意见改过代码，故**不绑最终 HEAD**，如实写明）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`
> ⚠️ 本轮第一次跑产出 0 字节存档（stderr 末行 `stream disconnected before completion`，网络断流非配额，已耗 121,950 tokens）；按协议原样重发一次，本文件是第二次的产出（89,444 tokens）。0 字节那一份未入库。

---

结论：**不建议当前合入。BLOCKER 0、HIGH 3、MEDIUM 4、LOW 1。三条 HIGH 均须合入前修，不能仅登记移交。**

绑定提交：`293f8d6a8f4a04a9debb120db63dc0d1752dc334`。本轮只读审查，未运行测试或写盘复现，因此不独立背书“88 条全绿”。期间工作树曾出现临时改动，已改读固定提交；结束时三份文件与 HEAD 无差异。

**HIGH，按严重性排序**

1. **HIGH-1：旧文件留存失败后，仍继续覆盖。**  
   位置：[undo_journal.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:255)。`_park_stale` 失败时返回原路径，`_replace_or_park` 忽略结果，随后仍执行替换；round-4 H6 未堵完整。  
   **复现思路：**已有用户内容的 `receipt.md`，将 `stale/` 设为普通文件或不可写目录，而批次目录保持可写；重跑仍能替换回执，旧内容没有留存。现 H6 门只覆盖停放成功路径。

2. **HIGH-2：新增的两次 rename 缺口，让 move 中断后无法自动续跑或撤销。**  
   位置：[undo_journal.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:255)，调用点 `:474`、`:1065`。留存逻辑也作用于业务文件：先移走旧文件、再就位新文件，中间存在正式路径缺失的窗口，这是 H6 整改引入的回归。  
   **复现思路：**move 已将源搬至目标，写溯源时在“目标移入 stale”之后、“临时文件就位”之前中断；源、目标均不存在，apply 的 `:369–379` 和 undo 的 `:1105–1109` 都拒绝恢复，即使备份完好。撤销 move 时重写原件也有相同缺口。

3. **HIGH-3：完整的未知状态位于账尾时，仍被静默忽略，撤销可误报成功。**  
   位置：[undo_journal.py:634](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:634)、`:658–671`。未知状态被转成与半行相同的 `None`，随后获得尾部容忍；round-4 M1 仍会让最新状态退回上一步。  
   **复现思路：**保留完整 `planned`，实际动作已经发生，但最后一条完整 JSON 的状态为 `actinh`，且没有 done；undo 会封口忽略它，再按 planned 记“未执行”，材料没有还原。现门把未知状态放在中间，未覆盖账尾。

**MEDIUM，可登记移交；其中旧账兼容项须在实际升级前处理**

4. **MEDIUM-1：旧版正常封口的多坏行账本，升级后无法读取。**  
   位置：[undo_journal.py:650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:650)。缺少 `sealed_bad_count` 时固定按一行处理，不能表达旧版曾合法封住的多行。  
   **复现思路：**用 `14fe7703` 形成“业务行中断 → 封口再中断 → 完整封口 → 后续正常行”；旧哨兵无计数，HEAD 只覆盖最后一条坏行，前一条被报为中间损坏，续跑与撤销均拒绝。

5. **MEDIUM-2：失败回执再次失败，会掩盖原始失败摘要。**  
   位置：[inbox_apply.py:803](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:803)，undo 同类位置 `:857`。回执写入发生在失败摘要输出之前且没有保护，第二次异常使原失败件、原因、完成数和账本位置无法输出。  
   **复现思路：**沿用备份失败用例，再把 `receipt.md` 设为目录；回执发布异常先抛出，`:805–811` 的原始失败摘要走不到。M3 门只测回执仍可写的情况。

6. **MEDIUM-3：“只有 planned”的门仍不能证明专用分支有效。**  
   位置：[test_g5_7_inbox_apply.py:1686](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:1686)。夹具确已删除 acting，但随后两件产物都被搬走，两份源保持原样，planned 专用分支仍未承重。  
   **对照思路：**删除 `undo_journal.py:1092–1096` 的 planned 分支，两个条目仍可经过“目标不存在、源符合 before”的通用恢复路径，现断言仍绿；缺少“planned 源已变化，同时先前完成项的产物仍在”的对照。

7. **MEDIUM-4：源 symlink 用例实际绿在更早的路径检查上。**  
   位置：[test_g5_7_inbox_apply.py:789](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:789)。用例声称只有 `lstat` 能区分，但链接指向 vault 外，先被 `source_path` 的 realpath 父目录检查拒绝。  
   **对照思路：**把 `check_source_fresh` 的 `os.lstat` 改成 `os.stat`，该门仍绿；应对照链接指向收件箱内另一份同字节、同 mtime 文件的情况。

**LOW，可登记移交**

8. **LOW-1：残片成功停放后，提示仍可能指向不存在的旧路径。**  
   位置：[undo_journal.py:509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:509)。当前失败 tmp 已在 `:259` 移入 stale，附注却仍使用原 tmp 路径；准备临时文件阶段的失败也未补位置附注。  
   **复现思路：**使用正常可写 stale，并把第二份回执落点设为目录，核对异常附注中的路径是否存在；现 L1 门强制停放失败，且只检查提示字符串，恰好看不出这个问题。

round-4 十四项的逐条核对如下；PASS 仅指静态复核通过：

| round-4 项 | 结果 | 本轮判断 |
|---|---|---|
| H1 | PASS | 复用 open entry 且源仍在时检查账上 SHA |
| H2 | PASS | 复用备份增加独立 inode 条件 |
| H3 | PARTIAL | 新格式计数有效；旧账兼容见 MEDIUM-1 |
| H4 | PASS | 目标归属检查已纳入 acting |
| H5 | PASS | 生产入口同时核 vault 与 batch |
| H6 | FAIL | 留存失败仍覆盖，并引入恢复缺口 |
| M1 | FAIL | 中间未知状态拒绝，尾部仍忽略 |
| M2 | PASS | `--undo` 文件名检查有效 |
| M3 | PARTIAL | `_do_one` 已覆盖；回执二次失败仍缺处理 |
| M4 | PARTIAL | 状态夹具修正，专用分支仍未承重 |
| M5 | PASS | inode 断言能检出 helper 本体退化为截断写 |
| M6 | PASS | 跨环比较可独立触发 |
| M7 | PASS | 已检查拒绝前产物未被搬走 |
| L1 | PARTIAL | 停放成功后的最终位置仍可能报错 |

补答你特别关心的边界：

- **正常重跑会累积**：每次完整重写回执都会向 stale 增加两份旧回执。一次发布的 JSON、Markdown 不会互相挪走；但共用 helper 会挪走刚复制或移动的 Markdown 原字节版本，HIGH-2 正发生在这里。
- **新格式连续中断、封口的计数**：未发现正常生成序列出现覆盖扩张；确认的问题是旧版无计数哨兵的兼容性。
- **`st_nlink != 1`**：当前代码选择隔离重建，并非直接拒绝。未确认普通本地文件系统上的误伤；异种文件系统未实测，不能据此宣称兼容性已验证。
