# CARD-G5-12 独立复核 round-4（绑 `654e76f0`）—— r3 整改后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`654e76f0`**（= 送审时 HEAD；**tracked 工作树干净**——除未跟踪的审查/evidence 材料外）。

背景：计划书 `:66` STILL-OPEN「连坐删除」的**收口卡**（脚本本体零改动）。
r1（`371c21ae`）B0/H0/M1/L3；r2（`5e608026`）B0/H1/M1/L1；r3（`87ba9d66`）**B0/H1/M1/L1**：
HIGH-1（负控存档未绑定到送审 SHA——存档自标 `5e608026`、生成早于 `87ba9d66` commit）、M1（白名单缺「本板成员」条件）、
L1（census §5 描述未随整改同步）——**均已在 `654e76f0` 处置**（负控在本次绑定 SHA 上重跑并自标；helper 加成员条件；
census 同步）。本轮：独立验伪这三条 + 是否有新 BLOCKER/HIGH。

**r3 的整改面（本轮重点读取面）**：
```
git --no-pager diff --no-color 87ba9d66 654e76f0 -- . ':(exclude)_bmad-output'
```
本卡全量 diff：`git --no-pager diff --no-color 1191dc1f 654e76f0 -- . ':(exclude)_bmad-output'`
（= `backend/tests/regression/test_sync_board_concepts.py`，纯新增 184 行，`grep -c '^-[^-]'` = 0）。
- 测试文件终态全文：`cat backend/tests/regression/test_sync_board_concepts.py`
- r1/r2/r3 存档：`_bmad-output/审查/codex-review-CARD-G5-12{,-r2,-r3}.md`

既有读取面（本卡零改动）：`canvas-vault/.claude/scripts/sync_board_concepts.py` `:40-60` / `:256-304` / `:313-348` /
`:351-456`（`:434-445` 白名单+成员条件）/ `:463-479` / `:499-570`；`_bmad-output/审查/evidence-g512/writers-census.md`
（§5/§6 已随最终 helper 语义同步，绑定在本 SHA）；负控存档 `negctl1a-spec-456-*.txt` / `negctl1b-protect-layer-*.txt` /
`negctl2-split-342-*.txt`——**最新三份均自标 `HEAD=654e76f0`**（生成晚于本 commit）。

**jev 分诊（协议 §2.4.3，绑 `654e76f0`）**：见 `evidence-g512/jev-triage-654e76f0.json`（同前：单测试文件、REVIEW）。

已跑裁判（作者声明，存档 `evidence-g512/`）：`41 passed / collected 41`；负控三段与本 HEAD 一致（1a 观察两绿 / 1b begin 红@end:end 绿 / 2 双红 + h1 passed；脚本 `282b7a96…` 每次还原逐字同）；ruff files=1 rc=0 + fmt_rc=0；地盘恰 1 文件 +184/-0；目录级在 `654e76f0` 上重跑（数字见 `*-close3-*.txt`）。

## ② 作者自述请独立核对（**r3 三条整改**——当成待验证命题）

1. **r3-HIGH-1 整改**：三段负控**已在 `654e76f0` 上重跑**且存档自标 `HEAD=654e76f0`（见各档第 1 行与文件 mtime > commit time）；脚本还原 sha 逐字同。
2. **r3-M1 整改**：`_user_region` 的排除条件 = 段内 ∧ 围栏外 ∧（`_SCRIPT_LINE`∨`_PLUGIN_LINE`）∧ **`group(1) 去路径后 ∈ member_ids`**；非成员机器形行留在区域；`member_ids=None` ⇒ 概念行一律保留（保守侧）。自测新增 (g1)/(g2)：`- [[节点/不是成员]] — 种子 · 待剖析占位` 默认（成员 {甲}）**不等于** base；(g2) 把「不是成员」纳入成员集后**相等**。
3. **r3-LOW-1 整改**：census §5「新承重判据」与 §6 已改为最终 helper 语义（段内·围栏外·白名单∧成员 / `_EMPTY_HINT` 限 BEGIN..END 块内 / `member_ids=None` 保守），并绑定在本 SHA。
4. 其余命题同前：脚本本体零改动；新断言当前绿、红只来自负控；既有 25 个测试名与全部既有断言逐字保留。

## ③ 按重要性排序的问题

0. **逐条验伪 ② 第 1–3 条**：
   - 负控存档的 SHA 绑定：第 1 行自标 + mtime + `git show -s --format=%cI` 三者对齐是否成立；还原 shasum 四行是否逐字同。
   - 成员条件：`group(1).rsplit("/", 1)[-1]` 与脚本 `basename()` 的口径是否等价（含 `|`/`#`/`^` 已在正则排除；`节点/子/甲` 这类多级路径）？`member_ids=None` 的保守方向是否会**误绿**（应只可能误红）？
   - (g1)/(g2) 是否真钉住成员条件（分别中和「去掉成员判断」与「成员判断恒真」会红在哪）？
1. **新面**：白名单 ∧ 成员双条件后，h1/h1b 的真实夹具是否仍走「排除」分支（否则 h1/h1b 的相等可能退化为「都没排除」）？sens `(c)` 臂的参数化成员集是否与断言自洽？
2. **r3 整改自身是否引入新回退**（对照 `git diff 87ba9d66 654e76f0` 逐段读）。
3. 其余遗留：r1-L2 登记口径；迁移态/围栏残差登记是否充分；负控 1a 两层冗余结论不变。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 §三(b) 合同点；不评 G5-7 / G5-10 执行侧脚本；不评 SKILL.md 调用点（P6 地盘，只读参照）。
