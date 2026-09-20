# CARD-G5-10 独立复核 round-7（绑 `8ce16fbb`）—— r6 的 1×HIGH + 1×MEDIUM 整改后的复审（本卡补轮上限）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`8ce16fbb`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关；`节点/` 契约是**扁平池**）。
轮次史：r1 `db9fc54f` B1/H4/M3/L1 → r2 `f3260ed0` B0/H2/M2/L1 → r3 `d5a06d33` B0/H2/M1/L2 →
r4 `f42ff845` B0/H2/M1/L2 → r5 `80e4a319` B0/H3/M0/L2（3 HIGH，已整改于 `b8b8357a`）→
r6 `b8b8357a` **B0/H1/M1/L2** → 本卡 r7（补轮上限）整改 r6 的 1 HIGH + 1 MEDIUM。

**本轮整改面（重点读取面）**：
```
git --no-pager diff --no-color 8ce16fbb^ 8ce16fbb -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，35 条用例）
- r5/r6 存档：`_bmad-output/审查/codex-review-CARD-G5-10-r5.md`、`...-r6.md`
- `654e76f0`/`3581f0d1` 是别的卡（G5-12）的文件，请忽略。

既有读取面（本卡零改动）：`split_preview.py` `:38-52,433-449,608-780,850-890,1090-1180`；`undo_journal.py` 全文。

**jev 分诊（绑 `8ce16fbb`）**：`split_apply.py` URG 2.93（logic, P=.78）· 测试 1.46（pass）；③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：点名套件 35/35 绿；负控 **6 段**（3 既有 +
3 新增）各自点名红 + 逐字还原；AST 删除门 1/0；zero-writers 两脚本 sha 未动；`tests/skills` 目录级 4 红 =
历轮**逐字同**的既有基线（`test_skill_portability_lint.py`）；`tests/unit` nodeid diff gt=0 / lt=1（只减成立）。

## ② 作者自述请独立核对（当成待验证命题）

1. **r6-HIGH-1（子目录残留绕过）**：`_resolution_replay_reason()` 的池扫描由 `glob("*.md")` 改
   `rglob("*.md")`（递归，含子目录）；消息改用 vault 相对路径（`p.relative_to(node_dir)`）；
   另对 `节点/` 下**symlink 目录**单独 fail-closed（`rglob` 默认不跟随，里面的 `*.md` 不可见 ⇒
   归属不可判定，故拒绝）。负控 ㉞（把产物移进 `节点/archive/` 后重跑）在 `b8b8357a` 上 `created=1`、
   整改后拒绝零产物；脚本负控第 6 段（`rglob`→`glob`）点名该用例变红。
   请核：递归面是否还有漏（更深层、symlink 文件、非 UTF-8、目录名以 `.md` 结尾等）；
   symlink 目录 fail-closed 是否过宽（会不会把合法 vault 卡死）；`rglob` 的跟随语义在本环境是否如声明。
2. **r6-MEDIUM-1（容忍面不看机器段）**：字节锚容忍面只剔「**非**机器段/非 HTML 注释 且逐字等于
   本 preview 候选名精确形态 callout」的行（与 `derived_names_in`/`run_callout_insert` 的机器段口径一致）；
   机器 fence 里的同形行保持原样。负控 ㉟（fence 里预置**本轮候选名**的同形行 → 插入 + 重跑）
   在 `b8b8357a` 上误拒、整改后放行；㉜（非本轮候选名的 fence 行）保持绿。
   请核：机器段口径与 `split_preview.py` 完全同源？是否引入新的绕过（例如攻击者新增 fence 行）？
3. **r6-LOW-1（提示误导）**：改名残留消息由「请恢复文件名或重跑 preview」改为
   「只能恢复原文件名（重跑 preview 不解除本门）」。
4. **r6-LOW-2（㉒ 未逐层钉 `outputs`）**：**本轮未修**——这是测试钉法弱点（无行为缺陷），
   作者判为 LOW 并留观。请核该判定是否成立（若认为必须修，请给出可复现理由与钉法）。
5. 其余命题同前轮：三条 r5-HIGH 的整改（改名残留 fail-closed / 剔行分层 / 字节锚）不被本轮回退；
   真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 / 过期零产物 / undo 全树逐字节还原 / 0 物理删除 /
   callout 默认关 / 零改动（`split_preview.py`+`undo_journal.py`）/ 不加 SKILL.md / 只改两份文件。
6. 残余风险（沿承，请复核是否仍成立）：完整协同重写 JSON（指纹+`board_sha256`+`sources[]`）在带内不可判，
   需带外生成时间锚，超出本卡边界。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r6 两条整改，再看新面）

1. 独立验伪 r6-HIGH-1 与 r6-MEDIUM-1 是否真闭合（含递归扫描的新面与容忍面机器段口径）。
2. 新 face 专项：递归 `rglob` + symlink 目录 fail-closed 的**代价与过宽风险**；池扫描最坏复杂度；
   `ours`/`pool` 仍只按顶层名是否自洽（子目录文件不占名是否符合 `节点/` 扁平契约）。
3. 是否存在新的 BLOCKER/HIGH；LOW 只报可复现的。
4. 零改动面与「只改两份文件」核对。

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分节（无则写「无」）；每条给 `file:line` + 复现思路
（「未被拦下的输入」或「负控输入」）；末尾给结论计数 `BLOCKER n / HIGH n / MEDIUM n / LOW n`。
只读，不要改任何文件；不要运行 apply/undo/pytest（按作者提供的 evidence 静态验伪即可）。
