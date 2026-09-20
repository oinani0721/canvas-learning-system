# CARD-G5-12 独立复核 round-2（绑 `5e608026`）—— r1 整改后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`5e608026`**（= 送审时 HEAD；tracked 工作树干净）。

背景：本卡 = 计划书 `:66` STILL-OPEN「连坐删除」的**收口卡**（脚本本体零改动）：写入方枚举清单证据包 +
`test_sync_board_concepts.py` 的 h1/h1b 加**用户文字区 sha256 逐字节断言** + helper 敏感自测。
**round-1（绑 `371c21ae`）裁定 BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3**：M1（排除面宽于脚本真实管理域）、
L1（h1b「第二遍」是 no-op）、L3（`_EMPTY_HINT` 分支无自测）**已整改**；L2（尾巴前导空白 lstrip 归一）
按卡文**登记不改**。本轮：独立验伪这三条整改 + 是否有新的 BLOCKER/HIGH。

**r1 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color 371c21ae 5e608026 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color 1191dc1f 5e608026 -- . ':(exclude)_bmad-output'`
（= `backend/tests/regression/test_sync_board_concepts.py`，纯新增 163 行，`grep -c '^-[^-]'` = 0）。
- 测试文件终态全文：`cat backend/tests/regression/test_sync_board_concepts.py`
- r1 存档：`_bmad-output/审查/codex-review-CARD-G5-12.md`

既有读取面（本卡零改动）：`canvas-vault/.claude/scripts/sync_board_concepts.py` `:40-60` / `:313-348`（`:342`/`:345`）/
`:351-456`（`:456`）/ `:463-479` / `:499-570`（`:526`/`:533-539`）；`_bmad-output/审查/evidence-g512/writers-census.md`
（全文，r1 模板表述已按复核意见修正）；负控存档 `negctl1a-spec-456-*.txt` / `negctl1b-protect-layer-*.txt` / `negctl2-split-342-*.txt`（**已在 `5e608026` 上重跑**）。

**jev 分诊（协议 §2.4.3，绑 `5e608026`）**：`test_sync_board_concepts.py` URG **2.23**，REVIEW 0.74，risk test_or_docs；③ 按 urgency 降序。

已跑裁判（作者声明，存档 `evidence-g512/`）：**41 passed / collected 41**（`regress-close3-*.txt` 等）；负控三段在本 HEAD 重跑：
1a【观察】仍两绿（两层冗余结论不变）；1b `[begin_note_line]` FAILED 于 `hexdigest` / `[end_sentinel]` passed；2 两 param FAILED 于 `hexdigest` + h1 对照 passed；脚本 sha `282b7a96…` 每次还原逐字同。
目录级（在 `5e608026` 上重跑）：`regression-dir` **1914 passed / 0 failed**（open/close 红集 diff gt=0/lt=0）· `skills-dir` **4F/715P**（与开工同）· `unit` **32F/5731P**，vs BASE diff gt=0/lt=1（已知 flaky）· `spl` **4F/173P**。

## ② 作者自述请独立核对（**r1 三条整改**声明——当成待验证命题）

1. **r1-M1 整改**：`_user_region` 的 `_CONCEPT_LINE` 排除已收窄为「**`## Concepts` 段内、围栏外**」（段结束 = 下一个 `## ` 或 `---`；围栏为 ``` / ~~~ 行翻转）——段外与围栏内的清单形用户文字**留在区域内**。
2. **r1-L1 整改**：h1b 的「第二遍」改为**真写盘**——第一遍后把块内成员行换成 plugin 旧形态（`— seed note (mastery: 0.30)`）再同步：收编重建 ⇒ 确实写盘（断言 `stale not in final`），此后再比第三串 hash。
3. **r1-L3 整改**：自测新增 `(e1) _EMPTY_HINT 占位行必须真的在排除面内（排除非空转）` 与 `(e2) 只有逐字等于 _EMPTY_HINT 的行才被排除` 两臂。
4. **r1-L2 登记不改**：尾巴 `-->` 后的 `lstrip()` 归一（脚本 `:345` 同口径）保留——「逐字节」承诺对**前导空白**子集实为「非空文字逐字节」，已在清单 ⑥ 与 UAT 登记。
5. 其余命题同 r1：脚本本体零改动（`282b7a96…`）；新断言当前绿、红只来自负控；既有 25 个测试名与全部既有断言逐字保留；写入方清单四层分类与 `git grep` 原样输出一致。

## ③ 按重要性排序的问题

0. **逐条验伪 ② 第 1–3 条**：
   - 收窄后的排除面是否**真的**与脚本 `:351-456` 的管理域对齐—— `## Concepts` 段边界判定（`_NEXT_HEADING` / `---` / 段首尾）与脚本 `locate_section` 的口径是否一致？围栏翻转（``` / ~~~ 混用、未闭合围栏）在边界输入下的行为？
   - `(e1)/(e2)` 两臂是否真钉住 `_EMPTY_HINT` 分支（分别中和「排除 `_EMPTY_HINT`」与「改成前缀匹配」会红在哪）？
   - h1b 的真写盘第二遍：写盘证据（`stale not in final`）是否充分？该第二次写盘会不会改变**被断言区域**（成员行在排除面内、stamp 在机器头内）而污染第三串 hash 的归因？
1. **新面**：收窄后，段外/围栏内的清单形用户文字进入区域——`h1` 的夹具（stray 在段内）与 `a1/b1` 的夹具会不会与新区域口径产生**误报**相互干扰（跑绿是否只是没人变）？
2. **r1 整改自身是否引入新回退**（对照 `git diff 371c21ae 5e608026` 逐段读）？
3. 其余遗留：r1 LOW-2 的登记口径是否可接受；清单 ⑥「未证明什么」是否还缺条目；负控 1a 的「两层冗余」判定在新代码上是否仍成立（脚本未变，应然——请复核断言链）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 §三(b) 合同点；不评 G5-7 / G5-10 执行侧脚本；不评 SKILL.md 调用点（P6 地盘，只读参照）。
