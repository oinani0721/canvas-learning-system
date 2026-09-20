# CARD-G5-10 独立复核 round-5（绑 `80e4a319`）—— board-split 执行侧 split_apply（r4 整改后的终轮复审）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`80e4a319`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关）。
r1 `db9fc54f`：B1/H4/M3/L1 → 处置；r2 `f3260ed0`：B0/H2/M2/L1 → 处置；r3 `d5a06d33`：B0/H2/M1/L2 → 处置；
r4 `f42ff845`：**B0 / H2 / M1 / L2，已全部处置**。本轮是**终轮**：独立验伪 r4 五条整改 + 是否存在新的 BLOCKER/HIGH。

**r4 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color f42ff845 80e4a319 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color a357194b 80e4a319 -- . ':(exclude)_bmad-output'`。
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，26 条用例）
- r1/r2/r3/r4 存档：`_bmad-output/审查/codex-review-CARD-G5-10{,-r2,-r3,-r4}.md`

既有读取面（本卡零改动）：`split_preview.py` `:38-52,124-130,433-449,521-560,608-660,815-870,1090-1140,1734-1832,1846-1882`；
`board_manifest_service.py` `:132-145,457-500,525-560,645-677`；`undo_journal.py` 全文；`skill_trigger_matrix.yaml` `:41-44`。

**jev 分诊（绑 `80e4a319`）**：`split_apply.py` URG 3.21（logic, P=.90）· 测试 1.79（test_or_docs, P=.72）；③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：26/26 绿；负控 3 段各自点名红 + 逐字还原；
AST 删除门 1/0；真解析门 + 验伪锚；ruff rc=0；地盘恰两份新文件。

## ② 作者自述请独立核对（**r4 五条**整改声明——当成待验证命题）

1. **r4-HIGH-1**：命名重放新增「改名残留」扫描——全池扫 frontmatter `split_stable_id`，命中本 preview 候选 id 但文件名 ≠ 候选账上名 ⇒ 拒绝（不再可能用旧 preview 再建一份同 id 的重复 provenance）。
2. **r4-HIGH-2**：创建正文改为剔除**全部**掩码派生 callout 形态行（不只自家那把）——父候选不会再收进子候选的 callout。
3. **r4-MEDIUM-1**：`run_create` 返回「已落地/可认领 id 集」；callout 分支只对其中候选动作（创建失败/拒认领的候选不再被插「已派生」）。
4. **r4-LOW-1**：㉒ 增第 4 变体（`outputs/` 本身换成 symlink）各自点名拒绝且外部账本零追加。
5. **r4-LOW-2**：新增 ㉖——池含 `甲小节`/`甲小节_2` 时期望名 `甲小节_3`，手改 preview 为同基空闲 `甲小节_9` 必须被重放拦下。
6. 其余命题同前轮：真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 / 过期零产物 / undo 全树逐字节还原 / 0 物理删除 / callout 默认关 / 零改动 / 不加 SKILL.md。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r4 整改，再看新面）

0. **逐条验伪 ② 五条**，重点：
   - 改名残留扫描：扫全池读每个节点 frontmatter 的代价与误伤面？「同 id 出现在两个不同名字」时的报告指向？正常重命名场景（用户主动改名后重跑 preview 应可行）会不会被卡死？
   - 正文「剔除全部 callout 行」：会不会把 preview 时就存在（属于内容指纹）的 callout 也从正文剃掉——与「行区间原文」的偏差是否需要更明确的口径？`stripped`/`comments` 掩码与 fingerprint 的 `machine` 掩码不一致处的交互？
   - `ok_ids` 传导：`--undo` 之后的再 apply、部分失败后重跑、dry-run 路径上的取值；callout 分支在「认领失败但在早前批次已 done」的候选上是否过度跳过？
   - ㉒×4 / ㉖ 的钉住程度（各自中和一层是否点名红）？
1. **终轮重点**：把 r1–r4 全部裁定过的五类面（归属/删除、freshness/绑定、CRLF/切行、symlink/链、测试钉住）再沿 `git diff a357194b 80e4a319` 通读一遍，**报出仍未关闭的 BLOCKER/HIGH**；没有就明说「无」。
2. r4 修复自身是否引入新回退（对照 `git diff f42ff845 80e4a319` 逐段读）。
3. 其余遗留面（含前几轮移交观察是否仍成立）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 P7-C 的 Concepts 托管块 sentinel 面、不评 G5-11 UAT / R-J03 / R-J08 旅程。
- 不评 P7-A `inbox_apply.py` 本体（只评它对 `undo_journal.py` 的复用面）。
- `split_preview.py` / `board_manifest_service.py` 是别的面的既有实现（本卡零改动）：对它们内部实现的意见请标注「移交」，不计本卡 BLOCKER/HIGH。
