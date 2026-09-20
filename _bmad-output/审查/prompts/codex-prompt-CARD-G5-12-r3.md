# CARD-G5-12 独立复核 round-3（绑 `87ba9d66`）—— r2 整改后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`87ba9d66`**（= 送审时 HEAD；**tracked 工作树干净**——除未跟踪的审查/evidence 材料外）。

背景：本卡 = 计划书 `:66` STILL-OPEN「连坐删除」的**收口卡**（脚本本体零改动）。
r1（`371c21ae`）B0/H0/M1/L3 → M1/L1/L3 整改、L2 登记；r2（`5e608026`）**B0/H1/M1/L1**：
HIGH-1（census 修正未绑定进送审 SHA + tracked 有未提交修改）、M1（排除面仍宽于脚本真实收编白名单）、LOW-1（段/围栏状态机与 `locate_section`/`code_spans` 有边界分歧）——**均已在 `87ba9d66` 处置**。本轮：独立验伪这三条 + 是否有新 BLOCKER/HIGH。

**r2 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color 5e608026 87ba9d66 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color 1191dc1f 87ba9d66 -- . ':(exclude)_bmad-output'`
（= `backend/tests/regression/test_sync_board_concepts.py`，纯新增 176 行，`grep -c '^-[^-]'` = 0）。
- 测试文件终态全文：`cat backend/tests/regression/test_sync_board_concepts.py`
- r1/r2 存档：`_bmad-output/审查/codex-review-CARD-G5-12{,-r2}.md`

既有读取面（本卡零改动）：`canvas-vault/.claude/scripts/sync_board_concepts.py` `:40-60` / `:256-304`（`locate_section` / `code_spans`）/
`:313-348`（`:342`/`:345`）/ `:351-456`（`:434-445` 白名单 / `:456`）/ `:463-479` / `:499-570`（`:526`/`:533-539`）；
`_bmad-output/审查/evidence-g512/writers-census.md`（**已含 r1 表述修正并绑定在本 SHA**）；
负控存档 `negctl1a-spec-456-*.txt` / `negctl1b-protect-layer-*.txt` / `negctl2-split-342-*.txt`（均在 `87ba9d66` 上重跑）。

**jev 分诊（协议 §2.4.3，绑 `87ba9d66`）**：`test_sync_board_concepts.py` URG **2.21**，REVIEW 0.74，risk test_or_docs。

已跑裁判（作者声明，存档 `evidence-g512/`）：`41 passed / collected 41`；负控三段与本 HEAD 一致（1a 观察两绿 / 1b begin 红@end:end 绿 / 2 双红 + h1 passed；脚本 `282b7a96…` 每次还原逐字同）；目录级在 `87ba9d66` 上重跑（数字见 `*-close2-*.txt`）。

## ② 作者自述请独立核对（**r2 三条整改**——当成待验证命题）

1. **r2-HIGH-1 整改**：census 的表述修正（「发射块文本逐字同；TS 源码因转义非原始字节相同」）已**绑定进 `87ba9d66`**（amend）；`git status --porcelain` 中无已跟踪改动（未跟踪审查材料除外）。
2. **r2-M1 整改**：`_user_region` 的概念行排除收窄为**稳态白名单**——仅排除「`## Concepts` 段内、围栏外、匹配 `_SCRIPT_LINE` 或 `_PLUGIN_LINE`（脚本 `:434-445` 真正收编重建的形状）」的行；**非成员行与带自定义文字的成员行留在区域内**；`_EMPTY_HINT` 的排除限定在 **BEGIN..END 块内**。自测新增 (f) 臂：自定义批注两变体（`我卡在第 3 步` vs `第 4 步`）hash 必不同。
3. **r2-LOW-1 整改**：段/围栏状态机对齐脚本——标题判定用**原始行** `_CONCEPTS_HEADING`；段界 = 原始行 `_NEXT_HEADING`（**无 `---` 段界**）；围栏仅段内跟踪、`_FENCE_RE`、**同字符闭合**（``` 与 ~~~ 不互相闭合）。
4. 其余命题同前：脚本本体零改动；新断言当前绿、红只来自负控；既有 25 个测试名与全部既有断言逐字保留。

## ③ 按重要性排序的问题

0. **逐条验伪 ② 第 1–3 条**：
   - 白名单口径是否与脚本 `:383-412`＋`:434-445` **逐字同源**（`_SCRIPT_LINE` / `_PLUGIN_LINE` 直接引用模块常量，无手抄？迁移态文本若进区域会不会保守误红——h1/h1b/自测窗口是否都是稳态）？
   - `_EMPTY_HINT` 块内判定：BEGIN 行被围栏/被跳过时 `in_block` 会不会错置？END 带尾巴（拆行前）时 `in_block` 翻转时机？
   - 围栏状态机与 `code_spans` 剩余分歧（缩进围栏、4 空格缩进块、未闭合围栏）对**本卡断言链**的实际影响（不是与脚本的任意文本等价的追求，而是会不会误红/漏红）？
1. **新面**：`(f)` 臂是否真钉住「自定义批注行在区域内」（分别中和「白名单收窄」与「概念行全排除」两种回归，各红在哪）？白名单收窄后 `(c)` 臂（两种机器形态相等）是否仍承重？
2. **r2 整改自身是否引入新回退**（对照 `git diff 5e608026 87ba9d66` 逐段读）。
3. 其余遗留：r1-L2（lstrip 归一）登记口径；清单 ⑥；负控三段结果在新 SHA 上的一致性。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 §三(b) 合同点；不评 G5-7 / G5-10 执行侧脚本；不评 SKILL.md 调用点（P6 地盘，只读参照）。
