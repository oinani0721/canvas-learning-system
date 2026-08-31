# Codex 独立复核存档 — CARD-M11M7 round-1

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-31
> **卡**: BATCH-2026-08-31-第七批 / CARD-M11M7（M11 批注跨板去重 + M7 板名字符拒绝集）
> **审阅对象**: 未提交的工作树 diff（4 文件：2 脚本 + 2 测试）
>
> ## ⚠ 审查期间的代码漂移（如实记录）
>
> 本轮**不是**对静止快照的审查。Codex 读的是实时文件，我在它审查期间改了三处：
> ① 顶层 `refusal_reason` 带上码位（自查发现诊断只落在 boards 明细里）；
> ② 竞态冲突不再静默（**因为看到它的注入实验输出** `per_board_tips=[1,2]` /
>    `receipt_tips=1` 而主动加固）；③ `ruff format`（它自己标注了
>    "Planning rerun after formatting changes"）。
> 报告后段的核对已覆盖上述改动，前段针对早期状态的判断可能已过期。
>
> ## 裁决与处置
>
> **PARTIAL · BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**
>
> 按停轮规则（第六批手册：BLOCKER/HIGH → 再一轮；MEDIUM/LOW → 登记结案）本可结案，
> 但那条 MEDIUM 是**带实证的真缺陷**（竞态下 create 仍 `created:true` 写出顺序相关的
> 数字），且修复成本低 ⇒ **修，不登记**。LOW-1 同样顺手修（三个入口的拒绝原因不一致
> 属名实不符）。LOW-2（SKILL.md 文档）复核者认可「合理守界」，维持移交。
> 整改后跑 round-2 定向复核。

---

## 裁决

**PARTIAL，需要再一轮。**  
分级：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**。

M11、M7 在稳定输入下均修对；剩余问题是 M11 遇到同节点扫描期计数冲突时，仍会发布顺序相关的数字。

### MEDIUM — M11 冲突被声明，但仍未 fail-closed

[`_cross_board_totals()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:179) 已检测不同 `tips_count`，产物也会在[阶段数字后追加警告](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:300)，所以“静默掩盖”已修复。

但总数仍取首现值并依赖板顺序：

```text
[A(1), B(2)] -> tips_total=1, conflicts=["N"]
[B(2), A(1)] -> tips_total=2, conflicts=["N"]
```

真实 `cmd_preview/cmd_create` 竞态注入中，两次都复现 `[1,2]` 时，create 仍 `created:true`，写出“总批注 1”；成功回执也没有冲突字段，见 [`cmd_create`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:837) 与[成功回执](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:944)。SKILL 又没有要求把 `tips_conflict_nodes` 在确认前转告用户。

`max/min/sum` 都不是正确替代；应在冲突非空时拒绝 preview/create，或改为汇总唯一节点后每个节点只读一次。

### LOW — M7 诊断没有贯穿所有入口

preview 会正确给出 `U+XXXX`，但 direct create 只返回“板不存在/非法”；`recap_scan collect` 仍误述为路径越界，见：

- [`recap_exam_build.py:104–120`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:104)
- [`recap_exam_build.py:844–855`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:844)
- [`recap_scan.py:1514–1531`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1514)

拒绝和零产物仍成立，故仅 LOW。

### 其余复核结果

1. **M11 稳定态 PASS**

   - 板内重复在 [`:135–137`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:135) 先去重。
   - ghost 不进入 `member_ids/member_tips`；跨板同 ghost 的 `ghosts` 数的是两条待修链接，语义合理。
   - 单板、空板、共享节点、独占节点、部分重叠均正确。实测分别得到 `1/3`、`0/0`、共享节点只计一次、部分重叠 `1+2+3=6`。

2. **消费点 PASS**

   正文和 preview 分别在 [`:227`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:227) 与 [`:816`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:816) 调同一 helper。全仓 active-code 搜索未发现第三份跨板同型计算；逐板展示不是遗漏。

3. **M7 边界与写前拒绝 PASS**

   [`unsafe_name_chars()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:120) 精确覆盖：

   - U+0000–001F 拒绝，U+0020 放行；
   - U+007E 放行，U+007F–009F 拒绝，U+00A0 放行；
   - U+2028/U+2029 拒绝。

   中文、空格、连字符、全角括号、带圈数字、重音字母、emoji、NBSP 均放行；补测 preview→create 成功。所有板先在 [`_prepare`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:734) 扫描，非法板在 create 首次 `mkdir` 前返回，没有写坏检验白板的绕过路径。

4. **测试承重性 PARTIAL/PASS**

   当前：**41 个 M11/M7 目标实例全过；两文件完整 243 passed**。用当前测试回放 HEAD 旧脚本：**31 failed / 10 passed**。

   - 承重门：M11 receipt、正文阶段行、部分重叠；M7 五种写前拒绝、三种消费症状、helper/containment/collect。
   - 旧版同绿且已诚实标注：M11 per-board、disjoint；合法板名六例；正常 collect；控制字符节点 ghost。
   - `no_conflict` 明示为反向锁；边界参数中的旧 C0/合法字符也是双向锁。
   - 未发现未标注的整条假绿用例。
   - [`test_m11_product_stage_numbers_line_deduped:2249`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2249) 的“未答上界等于 receipt”旧版同错为 2 时也通过，但相邻正确数字断言承重。
   - [`test_m11_tips_conflict_is_declared_not_silent`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2387) 真正先红后绿，但只证明“有警告”，并主动锁定首现值，不能证明数字正确或零写拒绝。

5. **范围 PASS**

   tracked diff 恰为授权的四文件；`git diff --check` 通过。没有新增 NFC/NFD、`normalize` 或 `casefold` 行为，[`recap_scan.py:137`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:137) 反而明确声明不归一化。

6. **文档 PARTIAL / LOW**

   [`SKILL.md:374`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/SKILL.md:374) 的括注和 [`:422`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/SKILL.md:422) 的矩阵确实漏了 DEL/C1/LS/PS；但 [`:107`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/SKILL.md:107) 已有泛化控制字符拒绝，非空 `refusal_reason` 的停机契约也仍有效。受“只许 scripts/tests”边界约束，不改文档而登记移交是合理守界，不构成 DD-13 式名实不符；但状态应标为“已移交、尚未文档闭环”，不能算完全一致。

结论：**再开一轮，但只需收口 M11 冲突态的 fail-closed 与相应零写测试；M7 安全修复本身可通过。**

审计锚点：HEAD `9cf0fb85…`；最终四文件哈希前缀 `eed4aa0f / 1c2a9457 / 962442e5 / 65fc001c`。未运行全仓 CI；审计期间出现的未跟踪验收单不属于用户指定的 `git diff`，未读取、未纳入结论。


