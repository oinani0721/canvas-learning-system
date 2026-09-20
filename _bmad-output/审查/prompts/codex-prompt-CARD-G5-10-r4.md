# CARD-G5-10 独立复核 round-4（绑 `f42ff845`）—— board-split 执行侧 split_apply（r3 整改后的复审）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`f42ff845`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关）。
r1（`db9fc54f`）：B1/H4/M3/L1 → 全部处置；r2（`f3260ed0`）：B0/H2/M2/L1 → 全部处置；
r3（`d5a06d33`）：**B0 / H2 / M1 / L2，已全部处置**。本轮重点：**独立验伪 r3 五条整改**并检查新回退。

**r3 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color d5a06d33 f42ff845 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color a357194b f42ff845 -- . ':(exclude)_bmad-output'`。
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，25 条用例）
- r1/r2/r3 存档：`_bmad-output/审查/codex-review-CARD-G5-10{,-r2,-r3}.md`

既有读取面（本卡零改动）：`split_preview.py` `:38-52,124-130,433-449,521-560,608-660,815-870,1090-1140,1734-1832,1846-1882`；
`board_manifest_service.py` `:132-145,457-500,525-560,645-677`；`undo_journal.py` 全文；`skill_trigger_matrix.yaml` `:41-44`；本卡文 §一(c)-(e)。

**jev 分诊（绑 `f42ff845`）**：`split_apply.py` URG 3.22（logic, P=.90）· 测试 1.77（test_or_docs, P=.73）；③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：25/25 绿；负控 3 段各自点名红 + 逐字还原（含
「门① 恒通过」变异本轮已补回有效位点并实测变红）；AST 删除门 1/0；真解析门 + 验伪锚；ruff rc=0；地盘恰两份新文件。

## ② 作者自述请独立核对（**r3 五条**整改声明——当成待验证命题）

1. **r3-HIGH-1**：门① 的 fresh 行号（当前坐标系）现已**传导到后续动作**——`_check_fresh` 返回 positions，`run_create` 用它切片（并剔除自家 callout 行）、`run_callout_insert` 用它作插入点（不再用 preview 旧行号）。
2. **r3-HIGH-2**：undo 的删/还原动作前对 **dst/src** 加 `assert_symlink_free` + realpath 物理包含判定（`节点/` 或 `原白板/` 被换成 symlink 时拒绝、列出）。
3. **r3-MEDIUM-1**：`resolved_name` 校验改为**按批前池重放**：批前池 = 当前池减去「frontmatter `split_stable_id` 命中同 id 候选」的节点（跨批次成立）；重放逐条必须与 preview 逐字相同（同基错误后缀不再放行）。
4. **r3-LOW-1**：㉒ 扩为三变体（batch / workroot / journal 各换成 symlink）各自点名拒绝且外部账本零追加。
5. **r3-LOW-2**：㉓ 补 U+2028 拒绝臂与混合行尾局部 terminator 断言（CRLF 区插 `\r\n`、LF 区插 `\n`）；新增 ㉕（先给甲插 callout 再建乙：乙正文完整、callout 位置正确——钉住 HIGH-1）。
6. 其余命题同前轮：真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 / 过期零产物 / undo 全树逐字节还原 / 0 物理删除 / callout 默认关 / 零改动 / 不加 SKILL.md。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r3 整改，再看新面）

0. **逐条验伪 ② 五条**，重点：
   - positions 传导后：`run_create` 的「剔除自家 callout」过滤与其他候选 callout（嵌套）叠加是否正确？`run_callout_insert` 的降序插入 + positions 组合下，同文件多候选（含嵌套）的插入点是否仍逐条正确？
   - 重放对账：批前池的减法判据（`split_stable_id` 命中）有没有被「同名节点 id 恰好相同」或「候选改名后残留节点」骗过的路径？`claimed` 顺序与引擎一致吗？
   - undo 目标链判定：`assert_symlink_free` + realpath 包含对 **dst/src 末段是 hardlink / 普通文件在 symlink 目录** 等组合的行为；`节点/` 被换成 symlink 时 create 与 modify 两分支是否都拒。
   - ㉒ 三变体在「只检查 journal 链不检查批目录」的缩窄突变下是否分别点名红？㉓/㉕ 是否钉住各自修复？
1. **r3 修复自身是否引入新回退**（对照 `git diff d5a06d33 f42ff845` 逐段读；特别看 positions 在 dry-run / 幂等 / 中断重跑路径上的取值）。
2. **25 条门**里有没有新的「绿在更早判据」；㉑㉕ 是否能互换地钉住映射/切片两半。
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
