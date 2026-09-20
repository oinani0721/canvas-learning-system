# CARD-G5-10 独立复核 round-2（绑 `f3260ed0`）—— board-split 执行侧 split_apply（r1 整改后的复审）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`f3260ed0`**（= 送审时 HEAD；tracked 工作树干净）。

背景：本卡补 board-split 的**执行侧** `split_apply.py`（消费 preview JSON + `--confirm <stable_id>`，
准入五门全过后原子创建 `节点/` 派生 md；复用 P7-A `undo_journal.py` 落账；默认路径 0 物理删除；
callout 默认关）。**round-1（绑 `db9fc54f`）裁定 BLOCKER 1 / HIGH 4 / MEDIUM 3 / LOW 1，已全部处置**，
本轮重点是**独立验伪这些整改**（② 列出整改声明；请逐条独立核对，不要采信作者结论）。

本卡 diff（含 r1 后的全部改动）：
```
git --no-pager diff --no-color a357194b f3260ed0 -- . ':(exclude)_bmad-output'
```
**r1 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color db9fc54f f3260ed0 -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，20 条用例）
- r1 存档（含 r1 全文与逐条裁定）：`_bmad-output/审查/codex-review-CARD-G5-10.md`

为读懂契约的既有文件（本卡只读/零改动）：`split_preview.py` `:38-52,124-130,433-449,521-560,608-660,815-870,1090-1140,1734-1832,1846-1882`；
`board_manifest_service.py` `:132-145,457-500,525-560,645-677`；`canvas-vault/.claude/scripts/undo_journal.py` 全文；
`ai-linked-doc/SKILL.md` `:140-158`；`skill_trigger_matrix.yaml` `:41-44`；本卡文 `第十五批-goals/P7-B.md` §一(c)-(e)。

**jev 分诊（协议 §2.4.3，绑 `f3260ed0`；③ 按 urgency 降序）**：

| FILE | CHURN | URG | REVIEW | TEST | RISK | VERDICT |
|---|---|---|---|---|---|---|
| `canvas-vault/.claude/skills/board-split/scripts/split_apply.py` | +845/-0 | 3.26 | 0.91 | 0.53 | logic | REVIEW |
| `backend/tests/skills/test_g5_10_split_apply.py` | +678/-0 | 1.76 | 0.67 | 0.91 | test_or_docs | REVIEW |

已跑裁判（作者声明，存档在 `_bmad-output/审查/evidence-g510/`）：20/20 绿；负控 3 段各自点名红 + 逐字还原；
AST 删除门 `undo_calls=1 non_undo_calls=0`；真解析门 + 验伪锚；ruff rc=0；地盘恰两份新文件。

## ② 作者自述请独立核对（含 **r1 八条**的整改声明——当成待验证命题）

1. **BLOCKER-1 整改**：一切「认领」（中断重跑补记 done / EEXIST 竞态认领）都要求「同 `split_stable_id` **且** 当前字节 sha == 账上 `sha256_planned`」；undo 对 planned（无 done）行**一律不删**（文件仍在则拒绝并列出）。是否还有旁路？
2. **HIGH-1 整改**：门① 对**全部候选**的 `identity_ambiguous / ambiguous_group_size / conflict_unresolvable / basis` 与重算结果对账后才动盘。
3. **HIGH-2 整改**：undo 对 split_modify 的「我们写的版本」证据 = `sha256_after or sha256_planned`（写后/记 done 前中断可还原）。
4. **HIGH-3 整改**：文件读取全部改按字节 `decode`（不过 universal newline）；插入行沿用文件自己的换行风格（`detect_newline`）。
5. **HIGH-4 整改**：门① 容忍 = 剔除**全文件**派生 callout 形态行（生成段/注释除外）后按账上行号比对（嵌套候选不再误判过期）。
6. **MEDIUM-1 整改**：「已存在同形 callout」判定按 `derived_names_in` 同口径屏蔽生成段/fence/注释。
7. **MEDIUM-2 整改**：`--undo` 只收 `bs-<16 位十六进制>` 形状，其余拒绝。
8. **MEDIUM-3 整改**：callout 循环每次插入前重验来源锚点（symlink/普通文件）；create 循环 open 前重验落点父目录无 symlink 组件。
9. **LOW-1 整改**：真解析门测试补 `source_board` 原文（`[[原白板/板A]]`）逐字断言。
10. 其余命题同 r1：真 `scan_vault` 判 derived 非孤儿 / 歧义候选零持久化 / 过期零产物 / undo 全树逐字节还原 / 默认路径 0 物理删除（AST 门）/ callout 默认关且非 TTY 未确认全跳过 / `split_preview.py`·`board_manifest_service.py` 零改动 / 不加 SKILL.md。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r1 整改，再看新面）

0. **逐条验伪 ② 的 9 条整改**：哪一条的实现盖不住它声称的输入？重点：
   - 认领条件「同 id 且 sha==planned」在 **done 已存在但字节被换** / **EEXIST 分支** / **planned 行缺 `sha256_planned`**（理论形态）下是否仍安全？
   - 门① 的「剔除全文件 callout 形态行后按账上行号比对」：文件里**原本就有** callout 行（changlog/别的派生物）时保守拒绝会误伤哪些正当输入？该保守侧是否可接受？
1. **HIGH-3 新面**：`split("\n")` + join 重写对「裸 `\r` 行尾 / 混用行尾」是否仍会改字节？`detect_newline`（看第一个 `\n` 的前一字节）在混合行尾下给插入行选的 terminator 对不对？
2. **HIGH-4 新面**：嵌套 + 多候选时 callout 插入的**行号**是否仍正确（降序插入 + 父/子 span 重叠）？「剔除后按原行号」在插入量大于原 span 时 `min()` clamp 会不会把不等价的说成等价？
3. **门① flags 对账的新面**：`conflict_unresolvable` 在 apply 后因**池变化**（新建节点入池）翻转为 true 的重跑会被判「过期」——这是安全侧还是误伤侧？`basis` 对账还有意义吗？
4. **undo 的 `state != done → 拒绝`**：正常 apply 后 done 在；用户手动删了 done 行再 undo → 拒绝。收口是否如预期？有没有把「确实该撤的使用路径」一刀切掉？
5. **⑭–⑳ 新测试**是否真钉住对应修复（把它们各自中和一层，是否各自点名红）？有没有断言其实绿在更早判据上的臂（特别是 ⑯⑰⑱）？
6. 其余面（同 r1 未覆盖完的）：`resolved_name` 路径安全 / batch_id 派生与落点 / `--confirm-insert` 子集校验 / dry-run 与 apply 输出契约。
7. 有没有 **r1 修复自身引入**的新回退（对照 `git diff db9fc54f f3260ed0` 逐段看）？

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
