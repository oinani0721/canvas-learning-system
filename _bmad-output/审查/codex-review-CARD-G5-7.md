> 批次: BATCH-2026-09-18-第十五批 · 车道 P7-A · 卡 CARD-G5-7 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-7.md)"`
> 审查绑定: `1d3e75b3f3785d799bf5e31bc1c4534e386c5e38`（该轮送审时的 HEAD；其后本卡按审查意见改过代码，故**不绑最终 HEAD**，如实写明）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

**结论：G5-7 不通过。** recycle 双确认本身成立，但存在覆盖既有内容、撤销路径验证和中断恢复缺陷。历史 ASCII 改动单独判定 **PASS**。

复核绑定 `HEAD 1d3e75b3`；三份文件与指定 diff 一致。以下基于源码、29 个用例的覆盖检查及纯内存验证，未修改文件、未运行写盘测试。

1. **HIGH — [inbox_apply.py:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:337)**  
   `planned` 行仅凭 `(seq, dst, dst_base)` 就被当成落点归属证明，随后 `copyfile` 可以覆盖用户后来放入的文件。  
   复现：copy 因目标目录不可写而在 planned 后失败；恢复权限并放入同名新文件，再用原输入重跑，新文件会被覆盖。

2. **HIGH — [inbox_apply.py:333](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:333)**  
   recycle 完全跳过落点占用检查，`:402` 的 `os.replace` 会覆盖回收路径已有内容。  
   复现：让回收父目录不可写，留下 planned 且源仍在；恢复权限、在回收落点放同名文件后重跑，该文件不会被占用守卫保护。

3. **HIGH — [undo_journal.py:158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:158)**  
   固定的 `<目标>.undo-journal.tmp` 用 `O_TRUNC` 打开，既不检查已有文件，也不检查硬链接。  
   复现：目标 `节点/a.md` 不存在，但 `节点/a.md.undo-journal.tmp` 是用户文件，copy 会截断它；若临时路径硬链接到收件箱原件，连 copy 的原件也会被改写。

4. **HIGH — [inbox_apply.py:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:212)、[undo_journal.py:548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:548)**  
   apply 只检查源路径末段；undo 对源祖先、目标末段及祖先均缺少对应验证，目标 SHA 检查还会跟随 symlink。  
   复现：preview 后把整个收件箱移到 vault 外并以 symlink 接回，move/recycle 仍通过；另将已 move 的 `.md` 落点替换为指向同 SHA 文件的 symlink，undo 搬回链接后，`:564` 的 `copyfile` 会改写链接指向的文件。

5. **HIGH — [inbox_apply.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:618)**  
   undo 没有验证 journal 与 `--vault` 的绑定，而是使用当前 vault 解释账上的相对路径。  
   复现：A 完成 copy，运行 `--vault B --undo A的账本`；B 的同名目标会先被搬入 A 的 `undone/`，之后才检查 B 的源文件。

6. **HIGH — [undo_journal.py:539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:539)**  
   copy/link 撤销不比较目标 SHA，直接搬走修改后的产物，源校验发生在搬动之后。  
   复现：copy 后修改目标，undo 仍可成功并搬走修改版；link 修改共同 inode 后，则会先搬走目标再报源校验失败。内容仍留在 `undone/`，但没有兑现“发现修改先拒绝”。

7. **HIGH — [inbox_apply.py:481](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:481)**  
   `build_plans()` 在读取 journal 前无条件检查源仍存在，使 move/recycle 的完成态和搬动后中断态都无法重跑。  
   复现：成功 move 后原样重跑，或第一件 move 成功、第二件失败后重跑，都会先报源不存在；现有幂等测试只覆盖 copy。

8. **HIGH — [undo_journal.py:520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:520)、[:562](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:562)**  
   撤销状态机忽略已动盘但未 done 的 planned，也不能恢复已搬回源但尚未写 undone 的状态。  
   复现：分别在 apply 主动作后、commit 前，以及 undo 的 `os.replace` 后、undone 前中断；前者撤销会漏掉该项，后者再次撤销会因旧落点不存在而停止。

9. **HIGH — [undo_journal.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:400)**  
   尾行 JSON 完整但缺最后一个 LF 时不会被封口，下一条追加会与它拼成坏行。  
   复现：让最后一条 planned 仅缺结尾换行，再重跑追加 done；纯内存验证显示两条记录合并后均无法解析。

10. **HIGH — [undo_journal.py:519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:519)**  
    undo 读到损坏尾行后没有调用 `seal_tail_if_needed()`，直接追加 undone 会破坏账目。  
    复现：已有 done 的账末尾留下半行，再直接 undo；第一条 undone 被接入坏行而丢失，后续追加会使其成为拒绝读取的中间损坏。

11. **HIGH — [undo_journal.py:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:160)、[:564](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:564)**  
    provenance 用新临时文件替换 inode，账本没有保存或恢复原 `st_mode`。  
    复现：在 `umask=022` 下，对权限 `0600` 的 UTF-8 `.md` 执行 move→undo，权限会留下 `0644`；现有全树测试使用默认权限，覆盖不到这个差别。

12. **HIGH，需并发条件 — [split_preview.py:1788](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1788)、[:1799](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1799)**  
    回执回滚仅依据早先的 `lexists` 结果按路径 unlink，没有核对当前目录项是否仍由本次创建。  
    复现：本次创建 `receipt.json` 后，另一进程将其替换为用户文件，再令 `receipt.md` 准入失败，回滚会删除替换后的目录项；无并发时，预先存在的文件不会进入该删除分支。

13. **MEDIUM — [undo_journal.py:575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:575)**  
    目录 mtime 无条件回写，会掩盖用户后来对目录条目集合的修改。  
    复现：apply 后在目标目录新增无关文件，再 undo，新增文件仍在，但目录时间被改回批前；此外，undone 全部落账后、此循环前中断，重跑也不会补回这些目录时间。

14. **MEDIUM — [inbox_apply.py:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:385)**  
    允许创建新目标目录，却不在 undo 中撤回这些目录，因此“排除工作目录后全树逐项相等”并不普遍成立。  
    复现：target 设为尚不存在的 `归档/新目录`，copy→undo 后空目录仍在；源码已声明这个边界，但作者总述及现有预建目录测试没有体现它。

15. **MEDIUM — [undo_journal.py:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:225)**  
    旧 provenance 仅按裸键和连续缩进行删除，空行会提前结束块识别，可能改变其他 metadata 的归属。  
    复现：旧 provenance 的两个缩进字段之间放空行，并在其前面放另一个 mapping，渲染后第二个字段会归入前一个 mapping；引号形式的同名键则会留下重复键，均已纯内存验证。

其余重点问题的结论：

| 问题 | 独立结论 |
|---|---|
| 双确认、拒绝零写 | **通过该检查。** `store_true` 配合 `confirm is True`；数字、字符串、容器不能替代布尔真，全部 decisions 检查先于建目录。 |
| 同路径同时 move/recycle | 正常 preview 下对应同一 stable_id，重复 decisions 会整批拒绝。普通文件的 move/recycle undo 也确实检查目标 SHA 和原路径占用。 |
| 完整哨兵再次读取 | **通过。** 坏半行后紧邻完整 `tail_sealed`，后续读取不会误判为中间损坏；缺口是第 9、10 项。 |
| 同内容 preview 与 `--now` | 同 vault、同 preview/decisions **原始字节**得到同 batch_id，文件路径不参与；换 `--now` 改变字节后成为新批次，但不能笼统说都由落点占用拦截，move/recycle 会先报源缺失。 |
| provenance 其余输入 | 无 frontmatter：前置新块；未闭合：同样前置新块并保留原文；非 UTF-8：跳过写入；纯 CRLF：保持；metadata 编码失败发生于打开临时文件之前。 |
| link 的 EXDEV | 被捕获并写入含 errno、路径的失败原因；首次失败留下 planned、没有 done、没有目标文件，属于明确的未完成态。 |
| target 白名单 | 列举的 `..`、绝对路径、收件箱、工作目录、精确拼写的配置首段及目标祖先 symlink 有静态检查；它不覆盖第 4 项的其他路径。 |

**历史 `ac949f6f..69fce02c`：PASS，限该 +14/-5。** 三处 `.strip(" \t")` 保留此前被 Unicode 空白规则丢弃的内容，未发现此次收窄引入缺陷。

**“零物理删除”的边界：** 两份新增脚本没有所列删除原语调用，字面声明成立；整条调用链包含依赖的 unlink，且无 unlink 也不能证明不会覆盖既有内容，第 1—3、12 项分别说明了这些边界。
