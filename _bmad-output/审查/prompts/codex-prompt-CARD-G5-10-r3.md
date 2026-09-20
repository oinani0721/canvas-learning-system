# CARD-G5-10 独立复核 round-3（绑 `d5a06d33`）—— board-split 执行侧 split_apply（r2 整改后的复审）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`d5a06d33`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm <stable_id>`，准入五门后原子创建
`节点/` 派生 md；复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关）。
round-1（`db9fc54f`）：BLOCKER 1 / HIGH 4 / MEDIUM 3 / LOW 1，已全部处置；
round-2（`f3260ed0`）：**BLOCKER 0 / HIGH 2 / MEDIUM 2 / LOW 1，也已全部处置**。
本轮重点：**独立验伪 r2 五条整改**（见 ②），并检查 r2 修复自身是否引入新回退。

**r2 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color f3260ed0 d5a06d33 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color a357194b d5a06d33 -- . ':(exclude)_bmad-output'`。
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，24 条用例）
- r1 存档：`_bmad-output/审查/codex-review-CARD-G5-10.md`；r2 存档：`_bmad-output/审查/codex-review-CARD-G5-10-r2.md`

为读懂契约的既有文件（本卡只读/零改动）：`split_preview.py` `:38-52,124-130,433-449,521-560,608-660,815-870,1090-1140,1734-1832,1846-1882`；
`board_manifest_service.py` `:132-145,457-500,525-560,645-677`；`undo_journal.py` 全文；
`ai-linked-doc/SKILL.md` `:140-158`；`skill_trigger_matrix.yaml` `:41-44`；本卡文 `第十五批-goals/P7-B.md` §一(c)-(e)。

**jev 分诊（协议 §2.4.3，绑 `d5a06d33`；③ 按 urgency 降序）**：

| FILE | CHURN | URG | REVIEW | TEST | RISK | VERDICT |
|---|---|---|---|---|---|---|
| `canvas-vault/.claude/skills/board-split/scripts/split_apply.py` | +928/-0 | 3.24 | 0.91 | 0.53 | logic | REVIEW |
| `backend/tests/skills/test_g5_10_split_apply.py` | +817/-0 | 1.78 | 0.74 | 0.91 | test_or_docs | REVIEW |

已跑裁判（作者声明，存档在 `_bmad-output/审查/evidence-g510/`）：24/24 绿；负控 3 段各自点名红 + 逐字还原；
AST 删除门 `undo_calls=1 non_undo_calls=0`；真解析门 + 验伪锚；ruff rc=0；地盘恰两份新文件。

## ② 作者自述请独立核对（**r2 五条**整改声明——当成待验证命题）

1. **r2-HIGH-1**：门① 对每个**确认候选**新增绑定对账：(a) `source_anchor.file` 与 `heading_path` 相等；(b) `suggested_name` 相等；(c) `resolved_name` 兼容（原名，或原名的 `_2.._9` 追加，或同基后缀重排）；(d) **行号映射对账**——把 fresh 候选行号在「剔除全文件派生 callout 行（生成段/注释除外）」的坐标系下映射后，必须等于账上行号（杜绝「正文相同的两节互换」这类指纹不变的位置漂移）。
2. **r2-HIGH-2**：undo 在**任何读账/封口/追加之前**先验批次目录链（`vault → outputs → outputs/board-split → batch → journal`）无 symlink 组件。
3. **r2-MEDIUM-1**：新增「切行契约」检查——来源文件含裸 CR 或 splitlines-only 分隔符（`\v \f \x1c-\x1e \x85 \u2028 \u2029`）时给出**精确**拒绝理由（而非含糊的「过期」）；callout 插入行的换行符改为「插入点上一行的局部风格」。
4. **r2-MEDIUM-2**：`--confirm-insert` 的解析/去重/子集校验移到 `run_create()` **之前**（确定性 CLI 输入错误零产物）。
5. **r2-LOW-1**：⑮ 补 conflict/basis 两臂（并注明各臂承重层）；⑲ 补 HTML comment 臂；⑳ 断言「形状不对」；新增 ㉑（互换/改名）/㉒（symlink 批次目录）/㉓（裸 CR）/㉔（未知 insert id）。
6. 其余命题同前两轮：真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 / 过期零产物 / undo 全树逐字节还原 / 0 物理删除（AST 门）/ callout 默认关 / 零改动 / 不加 SKILL.md。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r2 整改，再看新面）

0. **逐条验伪 ② 五条**，重点：
   - 行号映射对账在「callout 插在 span 起点之前 / 多个 callout（含嵌套）/ 插入后总行数小于原 span」时的行为（clamp、负值、等价类漏放/误拒）？
   - `resolved_name` 兼容规则的宽松面：同基后缀重排被接受——把名字改成同基的**错误后缀**（如 `甲_9`）能走多远（锚点/内容/stable_id 仍被绑住吗）？
   - 目录链校验的完备性：journal 的**任意祖先**被换成 symlink / 末段 symlink / 普通文件替换目录，各是什么结局？「纯读判绑定，通过后才可写」的顺序是否真的成立（封口追加发生在哪一步）？
   - 切行契约检查是否过宽（正文里合法的 `\f`/`\u2028` 被一刀切）或过窄（混合行尾、CRLF+裸 CR 混排仍留缝）？
   - `--confirm-insert` 重排后，dry-run / 正常 apply / 幂等重跑路径有没有受影响？
1. **新面**：映射对账与 `compute_content_fingerprint` 的归一化（丢空行）叠加时，「行数变化但剔除 callout 后等价」的输入分类是否自洽？有没有「指纹相同而映射不同」或「映射相同而指纹不同」被错误放过的组合？
2. **24 条门**：有没有新的「绿在更早判据」；㉑㉒㉓㉔ 是否各自钉住对应修复（各自中和一层，是否指名红）？
3. **r2 修复自身是否引入回退**（对照 `git diff f3260ed0 d5a06d33` 逐段读）？
4. 其余遗留面（含 r1/r2 的移交观察是否仍成立）。

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
