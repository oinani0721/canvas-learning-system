> 批次: BATCH-2026-09-18-第十五批 · 车道 P7-A · 卡 CARD-G5-7 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-7-r3.md)"`
> 审查绑定: `421afe85ada5228cddeed952cacb85840a54a422`（该轮送审时的 HEAD；其后本卡按审查意见改过代码，故**不绑最终 HEAD**，如实写明）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---

结论：**FAIL，9 HIGH、3 MEDIUM、2 LOW；未发现 BLOCKER。** 绑定提交 `421afe85ada5228cddeed952cacb85840a54a422`。

未修改文件、未连接外部服务，也未重跑会写盘的 64 个用例；结论来自固定提交源码、契约核对及纯内存路径验证。工作树短暂出现的变异内容未计入。

1. **HIGH — 撤销 copy/link 会先修改未经核验的原路径。**  
   [undo_journal.py:994](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:994)：`_finish_restore` 先 chmod/utime，随后才检查源是否仍为普通文件、内容是否相符，因此拒绝时可能已经改动别的文件。  
   复现：copy 成功后，把收件箱原路径换成指向 vault 外普通文件的 symlink，再 undo；外部文件的权限、时间先被修改，随后才报错，现有门没有覆盖这个源末段。

2. **HIGH — 内容等式仍会认领未由本批产生的文件。**  
   [undo_journal.py:768](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:768)：`sha256_before` 相等直接证明归属，无法区分尚未执行的 planned 与用户后来放入的同字节独立文件。  
   复现：planned 落账后、主动作前中断，在目标放入与源同字节的独立文件；apply 会接受并写入溯源，undo 会把它移进 undone，现有归属门只用了不同内容的对照。

3. **HIGH — H7 只保护了其他硬链接，独立占位文件仍被替换。**  
   [undo_journal.py:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:735)：备份路径未检查归属，原子替换仍会丢失该路径上不属于本批的普通文件。  
   复现：备份完成、planned 尚未落账时中断，将备份路径换成用户独立文件后续跑；该文件被 `os.replace` 替换，现有门只检查另一条硬链接的内容保留。

4. **HIGH — `stale/` 的失败路径遗漏 symlink 检查。**  
   [undo_journal.py:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:212)：`_park_stale` 直接创建目录并搬入残片，没有检查祖先链或落点。  
   复现：令批次 `stale/` 指向 vault 外目录，再将回执目标设成目录触发 replace 失败；残片会被移到 vault 外，H5 的 undone 守卫覆盖不到这里。

5. **HIGH — M2 整改引入“恢复一次后账本再也读不回”的回归。**  
   [undo_journal.py:586](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:586)：坏行及封口哨兵仅在文件尾被接受，后续业务记录会使已封口坏行重新成为“中间损坏”。  
   复现：`planned → 半行 → tail_sealed → done` 后再次 apply/undo 即拒绝；现有门没有让恢复后的账本再次经过生产读账函数。

6. **HIGH — 续跑实际写入的溯源与账上固定期望不一致。**  
   [inbox_apply.py:513](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:513)：`perform` 使用本次 `applied_at` 重建 meta，没有使用 planned 已保存的 `prov_meta`。  
   复现：T1 排期后中断，T2 续跑写完溯源、未 commit 又中断；第三次 apply/undo 只认 T1 的期望字节，拒绝自己的 T2 产物，测试统一固定 `NOW_ISO` 遮住了这个差异。

7. **HIGH — planned move 的撤销仍有不可续跑窗口。**  
   [undo_journal.py:963](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:963)：目标消失后只用 `sha256_after` 识别带溯源的已搬回产物，而 planned 行没有该字段。  
   复现：apply 已写溯源但未 commit，undo 把目标搬回源路径后、还原备份前中断，再 undo 即拒绝；半还原门保留了 done，另一道 planned 门没有再次中断撤销。

8. **HIGH — 两处非原子复制会留下无法自动恢复的正式文件。**  
   [inbox_apply.py:492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:492)、[undo_journal.py:921](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:921)：两处 `copyfile` 都可能先截断，再因写入失败留下部分字节，而恢复分支只认可完整的 before/after。  
   复现：复制过程中磁盘写入失败；apply 的部分目标过不了归属检查，undo 的部分源也不等于 before/after，重试均拒绝；现有权限失败门主要覆盖尚未开始写入的情况。

9. **HIGH — H8 的逐行绑定检查没有接入 apply。**  
   [inbox_apply.py:624](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py:624)：apply 读取、采信历史业务记录时没有调用 `_assert_bound_to`，只有 undo 调用了它。  
   复现：从成功账本各行移除指纹后重跑相同 apply，仍可报完成，随后 undo 却拒绝；新增无指纹门只调用 undo。

10. **MEDIUM — 后一步的 post 可以覆盖前一步的目录时间环。**  
    [undo_journal.py:857](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:857)：写入 `at_act/post` 时使用 `chain[rel][-1]`，没有确认该环属于当前 seq。  
    复现：同一次运行中，seq1 完成后、seq2 备份期间把目标目录改名；seq2 的 pre 不含该目录，执行重建后却有 post，于是新目录时间覆盖 seq1 的 post，撤销误把新目录时间回填成旧目录的批前值。

11. **MEDIUM — 目录链测试没有覆盖它声称的跨步骤断链。**  
    [test_g5_7_inbox_apply.py:1736](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/backend/tests/skills/test_g5_7_inbox_apply.py:1736)：两件都写入预先 chmod 0500 的“节点”，实际第一件就失败，注释中的“seq1 成功、seq2 失败”没有发生。  
    对照：删除 `post[k-1] != pre[k]` 检查，该输入仍会被第一件的 `pre != at_act` 判据拦住；此门也没有目录 mtime 的实盘断言。

12. **MEDIUM — 非 Markdown 文件新增整文件入内存的回归。**  
    [undo_journal.py:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:424)：现在先 `read_bytes()` 再判断后缀，PDF、视频等本可流式处理的文件也会完整读入内存。  
    对照：给 copy/move 输入大体积非 `.md` 文件，内存需求随文件大小增长；此前后缀分支直接返回，现有小文件用例无法体现差异。

13. **LOW — 第一份回执就位失败会遗留第二份 tmp。**  
    [undo_journal.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:461)：发布循环失败后只停放当前 tmp，尚未发布的其他 tmp 留在原目录。  
    对照：把 L1 门中用于阻止发布的目录从 `receipt.md` 换成 `receipt.json`；第二份 tmp 不会进入 stale。

14. **LOW — 第二次 undo 会清空仍然存在的新建目录说明。**  
    [undo_journal.py:814](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x/canvas-vault/.claude/scripts/undo_journal.py:814)：`created_dirs` 只从最新业务行汇总，而 undone 行没有保存该字段。  
    复现：copy 到新目录、成功 undo，再执行一次 undo；空目录仍在，新写的撤销回执却变成 `created_dirs: []`，L2 门只覆盖成功 apply 重跑。

18 条整改逐项结论如下；“成立”仅指原意见描述的直接路径。

| round-2 项 | round-3 判定 |
|---|---|
| H1 | 原子串判据已移除；仍有第 2、6 条归属问题 |
| H2 | 部分成立；仍有第 7、8 条中断窗口 |
| H3 | 状态选择成立；最新行丢失目录说明见第 14 条 |
| H4 | 0444 正常撤销路径成立 |
| H5 | undone 路径成立；stale 同族遗漏见第 4 条 |
| H6 | 搬动前验证备份成立 |
| H7 | 部分成立，见第 3 条 |
| H8 | undo 成立；apply 遗漏，见第 9 条 |
| H9 | 所述源路径越界路径已堵住 |
| M1 | 未执行 planned、源完好的直接路径成立 |
| M2 | 出现回归，见第 5 条 |
| M3 | 部分成立；实现与测试缺口见第 10、11 条 |
| M4 | 顶格注释实例已堵住 |
| M5 | 已如实声明限制；新门证明了 undo 的全缺失情况 |
| M6 | 加入实盘断言的整改成立 |
| M7 | 同文件系统内断开硬链接的对照成立 |
| L1 | 部分成立，见第 13 条 |
| L2 | 成功 apply 重跑成立；重复 undo 遗漏见第 14 条 |

另外，`expected_after_provenance` 与 `write_provenance` 的四类分支共用判断，未发现输出分歧；第 6 条问题来自调用者换了 meta。`planned` 缺 `at_act` 本身不会错误回填，因为同时缺 post，会保守跳过。`done → undone → planned` 在两侧解读一致。按 preview 原样输出的 `name/rel_path`，未见 NFC/NFD 误伤；`.` 与重复斜杠规范化后仍受父目录边界检查。
