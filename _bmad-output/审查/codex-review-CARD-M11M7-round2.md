# Codex 独立复核存档 — CARD-M11M7 round-2

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-31
> **卡**: BATCH-2026-08-31-第七批 / CARD-M11M7
> **审阅范围**: 只审 round-1 三条整改（MEDIUM fail-closed / LOW-1 诊断贯穿 / LOW-2 文档移交）
>
> ## 裁决与处置
>
> **PARTIAL · BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3 ·「需再一轮，只需短定向复核」**
>
> 这一轮最有价值的一条是**冲我自己写的注释来的**：测试里写着「不确定的数字一个都不许
> 发布」，实际断言只检查了顶层 `totals`，而 `boards` 明细里的板级计数同样顺序相关、
> 照样发布（反转 `--boards` 顺序，同一块板的公开值从 1 变 2）。⇒ 修，不登记。
>
> | 条 | 处置 |
> |---|---|
> | MEDIUM 板级数字仍顺序相关 + 两个组合态吞掉冲突声明 | ✅ 修（`_redact_untrusted_counts()` + 组合态补句 + 4 条新测试含**顺序无关锁**） |
> | LOW-1 冲突门遮蔽非法 SHA 的 exit 2 契约 | ✅ 修（冲突门移到形状校验之后 + 专门的退出码锁） |
> | LOW-2 create 零写测试假承重 | ✅ 修（改用正确 SHA + 先跑对照组证明该 SHA 无竞态时确能创建） |
> | LOW-3 docstring 描述旧语义 | ✅ 修 |
>
> ⚠ 整改过程中我把组合态补句写成了 if/elif 链中间的一个 `if`，直接把渲染 `else`
> 挂错到它身上（「有缺板但无冲突」也会去渲染）——**被既有测试当场抓红**，已改为链后
> 独立成句。这个失误如实记在代码注释与验收单里。

---

## 裁决

**PARTIAL — BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3。需要再一轮：是，但只需短定向复核。**

锚点：`card/v2-recapfix`，HEAD `9cf0fb85ed839bb7035d023534fca222a24d6968`。全程只读，工作树状态未变化。

### MEDIUM — preview 拒绝仍发布顺序相关数字

[recap_exam_build.py:801](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:801) 在冲突检查前已把完整 `boards` 放入输出；[recap_exam_build.py:825](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:825) 只增加 `refusal_reason`，没有裁掉板级 `tips_total`、`tips_unanswered_upper_bound`、`member_tips`。

用现有 `_rs._read` 竞态手法反转板序：

```text
--boards 板一 板二 → 板一=1，板二=2
--boards 板二 板一 → 板二=1，板一=2
```

顶层 `totals/content/content_sha256` 确实不存在，create 也不会发生；但同一板的公开数字会随扫描顺序从 1 变 2，直接命中本轮“不得发布顺序相关数字”的检查项。

更严重的组合态：

- `target_exists + conflict`：因 [819](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:819) 的优先分支，拒绝理由只说目标存在。
- `missing + conflict`：因 [810](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:810) 的优先分支，拒绝理由只说缺板。

两种情况下仍返回上述板级数字，却完全不声明冲突。

测试也锁住了这个遗漏：[test_g5_9_recap_exam.py:2433](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2433) 要求公开 `[1,2]`，随后注释称“不确定的数字一个都不许发布”，实际仅检查顶层 `totals`。

### LOW

1. **冲突遮蔽非法 SHA 的退出码契约。**  
   冲突门在 [recap_exam_build.py:887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:887)，早于 SHA 形状校验 [905](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:905)。`conflict + 空串/大写 SHA` 实测为 `exit 0 + created:false`，而既有测试契约 [test_g5_9_recap_exam.py:761](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:761) 声称非法形状一律 `exit 2`。安全上仍零写。

2. **create 零写测试未独立承重。**  
   [test_g5_9_recap_exam.py:2451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2451) 固定传全零 SHA；撤销冲突门后，旧 SHA mismatch 本来也会零写。整条测试会因冲突文案断言变红，不是整条假绿，但“零写由冲突门保证”这个子结论是假承重。且 [vault_snapshot:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:91) 只记录文件 SHA，漏空目录、目录项和 symlink 身份。

3. **实现注释仍描述旧语义。**  
   [recap_exam_build.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:189) 仍说冲突会在“产物与回执里显式声明”，与当前拒绝、不渲染的行为相反。

## 已确认通过的部分

- **create 无落盘绕过。** 冲突门位于 render、SHA 比较、`mkdir`、tmp/write 之前。稳定 SHA、全零 SHA、冲突态“若继续渲染就会精确匹配”的 SHA、参数换序/重复均 `created:false`；省略 SHA 为 argparse `exit 2`。
- **真零写。** 使用 `lstat` 全树快照，记录目录项、目录元数据、文件 exact bytes、symlink target；前后摘要全等。预置无关 tmp/symlink 原样保留，无目标或 `.g59-tmp`。`检验白板/` 原本不存在时，拒绝后仍不存在。
- **正常态不误伤。** 一致共享、单板、空板、幽灵链接、板内重复均实测 `_tips_conflict_refusal(...) is None`，preview 正常、create 成功。
- **M7 就原问题 PASS。** preview/create 经 [recap_exam_build.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:104)、collect 经 [recap_scan.py:1514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1514) 均点名 `U+XXXX`；真正 `../外部板` 仍在 [1531](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1531) 报路径原因。未发现第四个生产入口。
- **正常产物 bytes 未变。** 与仅撤销本轮三项行为的 functional round-1 mutant 比较，standard/shared/disjoint/single/empty/ghost/板内重复/partial 共 8 个构造，preview content 与 create 文件均逐字节相同。
- **测试结果：** 两个目标测试文件 `245 passed`；`-k 'm11 or m7'` 为 `43 passed`。

整改前 byte-exact 中间态未进入 Git 对象库，因此回放采用明确标注的 functional mutant：本轮 9 个新增/改写实例为 `8 FAIL / 1 PASS`；唯一同绿是明确标注的“真正路径仍报路径”反向锁。

LOW-2 状态也保持诚实：`SKILL.md` 仍未同步拒绝矩阵，四个目标文件没有宣称“已完全一致”。


