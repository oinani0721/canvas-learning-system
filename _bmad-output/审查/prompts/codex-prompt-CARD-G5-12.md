# CARD-G5-12 独立复核 round-1（绑 `371c21ae`）—— sync_board_concepts sentinel 用户文字区 sha256 门 + 写入方清单

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`371c21ae`**（= 送审时 HEAD；tracked 工作树干净）。

背景：计划书 `:66` §2.3 **STILL-OPEN**「同步脚本可能**连坐删除** sentinel 区间内用户文字」。
缺陷本体已由 `867112af` / `334f316a` 修复（2026-08-12），但回归门只到**子串级**。本卡（缩为收口卡）：
① 写入方枚举清单证据包（四层分类）；② `test_sync_board_concepts.py` 的 h1/h1b 加**用户文字区
sha256 前后逐字节断言**（既有子串断言降为诊断、保留不删）+ helper 敏感性自测；③ 回归测试以显式路径
写进裁判口径。**脚本本体零改动**。红**只来自负控输入**（连坐删除在 `9c4e7e82` 上已不可复现）。

本卡 diff（应恰 1 文件）：
```
git --no-pager diff --no-color 1191dc1f 371c21ae -- . ':(exclude)_bmad-output'
```
= `backend/tests/regression/test_sync_board_concepts.py`（全文：`cat` 它；纯新增 132 行，`diff | grep -c '^-[^-]'` = 0）。

既有读取面（本卡零改动）：
- `canvas-vault/.claude/scripts/sync_board_concepts.py`：`:40-60`（常量/正则）/ `:313-348`（`split_sentinel_tails`；`:342/:345`）/ `:351-456`（`managed_lines`；`:456` 保护减法）/ `:463-479`（`render_block` + `_strip_stamp`）/ `:499-570`（`sync_board`；`:526` protected 投影、`:533-539` `head_idx` 重排回插）
- `_bmad-output/审查/evidence-g512/writers-census.md`（全文，6 节）
- 负控存档：`_bmad-output/审查/evidence-g512/negctl1a-spec-456-*.txt`（**观察项**）/ `negctl1b-protect-layer-*.txt` / `negctl2-split-342-*.txt`
- 总账 v2 `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:315-320`；计划书 `:66` / `:435`

**jev 分诊（协议 §2.4.3，绑 `371c21ae`）**：`backend/tests/regression/test_sync_board_concepts.py` +132/-0，URG **1.90**，REVIEW 0.67，risk test_or_docs，VERDICT REVIEW；③ 按 urgency 降序（本卡唯一文件）。

已跑裁判（作者声明，存档在 `evidence-g512/`）：`40 passed`（开工）→ **`41 passed` / collected 41**（收工，+1 = 自测）；负控三段（1a 观察 / 1b / 2）见 ②；脚本 sha256 负控前后 = `282b7a96…` 逐字同；ruff files=1 rc=0 + F821 锚 rc=1。

## ② 作者自述请独立核对（当成**待验证的命题**，不是事实）

1. **脚本本体零改动**：本卡 diff 恰 1 个测试文件；`sync_board_concepts.py` 与 `skill_portability_lint.py:3217` 的 digest 条目逐字同（`282b7a96…`）。
2. **新 sha256 断言在当前脚本上直接绿**；行为面的「红」**只来自负控输入**——不得理解成「本卡修复了连坐删除」。
3. **`_user_region` 排除面恰四类机器行**：sentinel 三行（BEGIN / 收尾 NOTE / END）只丢 `-->` 及其之前的机器头、尾巴 `lstrip` 后保留为一行（与脚本 `:345` 同口径）；匹配 `_CONCEPT_LINE` 的行；等于 `_EMPTY_HINT` 的行。其余一行不动（自测四分支：删用户行必变 / 改时间戳与 n= 不变 / 成员行形态变化不变 / 尾巴粘行尾与独立成行不变）。
4. **负控**：①【观察】卡文原样 `:456` 去 `- (protected or set())` → 实测**两 param 都绿**——根因是脚本第二层保护 `head_idx`（`:533-539`）独立保留拆出的尾巴，`:456` 的减法在常规路径上与它**冗余**；② 替代单层变异 `:526 protected = set()`（保护层源头）→ `[begin_note_line]` **FAILED 于 `hexdigest` 断言**、`[end_sentinel]` **passed**；③ `:342 if tail.strip():`→`if False:` → 两 param **均 FAILED 于 `hexdigest`**，同变异态下 `test_h1…` **passed**。三段跑前跑后 shasum 逐字同。
5. **清单四层分类与 `git grep` 原样输出一致**：托管块改写者 1 / sentinel 字面量发射者 2 / 段内非托管行写者 1（`appendBoardLines` + 4 调用点）/ 只读消费者 4；测试夹具命中 5 文件另表（不计写入方）。
6. 既有 25 个测试名与全部既有断言逐字保留；`41 passed / collected 41`；目录级红集与开工侧相同（存档名在 `evidence-g512/`）。

## ③ 按重要性排序的问题

0. **`_user_region` 排除面是否过宽**：尤其「**成员行尾的用户批注**」（如 `- [[节点/甲]] — 我卡在第 3 步`）落在 `_CONCEPT_LINE` 排除面内——字节门**不覆盖它**（既有 a2 子串门覆盖）。请对照脚本 `:48` `_CONCEPT_LINE` 与 `:460` `_EMPTY_HINT` 逐条核：有没有更宽的其他用户文字形态被静默排除？排除面与脚本「收编重建」的真实集合是否对齐？
1. **负控 1b / 2 的红是否真落在新增 `hexdigest` 断言**（而非既有子串断言）；**1a 的「两层冗余」判定是否成立**——`:456` 的减法有没有边缘路径（提示：`marks` 因围栏跳过、`insert_at` 后移时）仍是唯一保命线？如是，本卡应把它登记为「纵深」还是「缺陷」？
2. **清单是否漏写入方**：`main.ts appendBoardLines` 四调用点是否都写在 `## Concepts` 段边界前？`whiteboard.md.template:27-30` 与 `configure-whiteboard.ts:185-188` 两份模板是否逐字同？`白板 _md` 的 11 文件分层有没有错位？
3. **尾巴 `-->` 取法与 `:345 lstrip()` 归一**是否让「前导空白丢失」逃过 hash 门（本卡**登记不改**；请评是否应升级为缺陷）。
4. **h1b 第三串 hash 是否真跑了写盘那一次**（`--check` 不写盘，测试内插入了第二次 `_sync` 写盘运行）？断言次序与既有 `--check` 行的关系是否合理？
5. `41 passed / collected 41` 是否核过；`40→41` 是否只多 `test_g512_user_region_hash_is_sensitive`；新增断言会不会把**设计内的收编/重建**误报成漂移（对照 a1/a2 语义）。
6. 有没有把「**门未覆盖的路径**」漏掉：如 h1 未覆盖「块内夹在 BEGIN 与用户 callout 之间」的第二类位置、`--all`/`--backup` 路径上的字节不变性。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 §三(b) 合同点（`exam_service.py` `DEFAULT_GROUP_ID` / `verification_service.py:2036`，已登记移交）。
- 不评 G5-7 / G5-10 执行侧脚本（P7-A/P7-B 地盘）。
- 不评三份 SKILL.md 调用点是否该加 `--backup` / `--check`（P6 地盘，只读参照）。
