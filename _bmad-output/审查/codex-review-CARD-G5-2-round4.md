## (1) 三轮 STILL-OPEN/PARTIAL 逐项裁定

| 项目 | 四轮裁定 | 依据 |
|---|---|---|
| H1 写边界 | **RESOLVED** | mkdir 前先验 parent；物理目标零残留测试；单 FD `open→fstat→ftruncate→write`。[引擎](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:727) [测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:485) |
| H2 读越界 | **RESOLVED** | `原白板/节点` 目录 symlink 整体拒绝，板与 seed 增加 realpath containment；检查—读取竞态已声明。[引擎](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:442) |
| H3 `clean_heading` 偏差 | **RESOLVED** | 引擎头及 README 首表已显式登记偏差 #5。README 后续“完整清单”仍只列四项，属非阻断文档瑕疵。[README](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/README.md:48) |
| H4 exact-byte 证据绑定 | **RESOLVED** | 当前引擎 `bd815e…` 与运行前、运行后、manifest 一致；四产物 digest 全匹配；before/after TSV exact bytes 相同。[转录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/live-run-log.txt:3) |
| H6 反事实锁 | **RESOLVED** | 见下。 |
| 来源多次读取、SHA/正文可能错版 | **RESOLVED** | 每来源一次 `read_bytes`，正文与 SHA 同字节。[引擎](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:467) |
| live 命令回放不完整 | **RESOLVED** | `set -x` 转录包含采集、两次运行、diff、摘要及退出码。 |
| collector 目录 symlink 不记 target | **RESOLVED** | 现按 `L + target` 记录。[collector](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/collect_live_baseline.py:28) |
| 零写单测元数据覆盖 | **仍开 / PARTIAL·MEDIUM** | 已补 root、目录 mtime/mode、文件 bytes；仍不直接锁目录 ctime/nlink、symlink target、xattr。 |
| 标记严格配对 | **仍开 / MEDIUM** | 缺闭合吞 EOF 是已声明立场；但 AUTO 仍可被任意含 `/AUTO-GENERATED` 的行关闭，fence 仍按任意 `startswith("```")` 翻转，弱配对未变。[引擎](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:195) |

## (2) H6 重查结论

**三轮静态推断错误，现予撤回。**

AUTO 开、闭标记分别是自闭合单行 HTML 注释；`comment_mask` 只掩这两个标记行，不会掩住中间的富假小节。把 `strip_generated` 置为全 False 后，AUTO、fence、Recent Activity 三类 fixture 都会产生假候选，因此常驻反事实测试确实能红，H6 **RESOLVED**。[反事实测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:674)

## (3) 新 BLOCKER/HIGH 与整体裁决

**新 BLOCKER：无。新 HIGH：无。**

整体裁决：**可验收——带声明边界**。边界包括祖先替换 TOCTOU、bind/overlay mount、上述标记弱配对/吞 EOF、TS oracle 未运行；本轮纯静态，确认存在 34 个测试函数，但不独立确认“34/34 全绿”。


