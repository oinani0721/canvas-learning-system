# CARD-G5-10 独立复核 round-8（绑 `e2abb8ef`）—— r7-HIGH-1「canonical 顶层路径」整改后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`e2abb8ef`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关；`节点/` 契约是**扁平池**）。
轮次史：r1 `db9fc54f` B1/H4/M3/L1 → r2 `f3260ed0` B0/H2/M2/L1 → r3 `d5a06d33` B0/H2/M1/L2 →
r4 `f42ff845` B0/H2/M1/L2 → r5 `80e4a319` B0/H3/M0/L2（3 HIGH，整改于 `b8b8357a`）→
r6 `b8b8357a` B0/H1/M1/L2（整改于 `8ce16fbb`）→ r7 `8ce16fbb` **B0/H1/M0/L1** → 主 session 批 r8，本卡整改。

**本轮整改面（重点读取面）**：
```
git --no-pager diff --no-color e2abb8ef^ e2abb8ef -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，36 条用例）
- r7 存档（本 HIGH 原文与复现思路）：`_bmad-output/审查/codex-review-CARD-G5-10-r7.md`
- `7374e220`（父提交的父）是 G5-7 补审归档文档 commit，与代码无关。

既有读取面（本卡零改动）：`split_preview.py` `:38-52,433-449,608-780,850-890,1090-1180`；`undo_journal.py` 全文。

**jev 分诊（绑 `e2abb8ef`）**：`split_apply.py` URG 2.76（logic, P=.74）· 测试 1.58（pass）；③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：点名套件 **36/36 绿**；负控 **7 段**各自点名红 +
逐字还原；AST 删除门 1/0；zero-writers 两脚本 sha 未动；`tests/skills` 目录级 4 红 = 历轮**逐字同**的既有基线
（`test_skill_portability_lint.py`）；`tests/unit` nodeid diff gt=0 / lt=1（只减成立）。

## ② 作者自述请独立核对（当成待验证命题）

1. **r7-HIGH-1（子目录保持原名漏网）**：`_resolution_replay_reason()` 的残留判据由
   `if sid in by_id and p.stem != by_id[sid]:`（只比 stem）改为
   `if sid in by_id and p != node_dir / f"{by_id[sid]}.md":` —— 对任何携带本 preview 候选
   `stable_id` 的**递归命中**，**只有**路径精确等于 canonical 顶层 `节点/<账上名>.md` 才算自家产物（放行），
   其余位置（改名 / 移入子目录 / 子目录内保持原名）一律拒绝；错误文案改为
   「发现同 stable_id 的残留节点: …（候选账上路径 节点/<账上名>.md）—— 请把该文件移回原路径并恢复原文件名
   （重跑 preview 不解除本门）」；循环上方注释语义同步更新；三处 fail-closed 文案里的「改名残留」改为「残留」。
   负控 ㊱（移动 + **保持原名**）在 `7374e220` 上 `created=1`、整改后拒绝零产物；㉞（移动 + 改名）与 ㉗ 的
   断言同步改为新文案；全仓 `grep 改名残留` 仅剩历史存档/prompt/UAT 叙事，无失效断言。
   请核：**是否真的完全闭合** —— 还有没有「携带候选 id 但 `p == node_dir / f"{by_id[sid]}.md"` 之外」能漏网的
   位置类别（例如：hardlink、canonical 路径本身是 symlink、`.`/`..` 段、大小写差异文件系统、NFD/NFC 文件名
   差异、深层 more 层）；以及 canonical 比较用**原始路径串相等**（不做 resolve/NFC 归一）是否会误伤合法
   工具自建文件（apply 写入的路径是否逐字等于 `node_dir / f"{resolved_name}.md"`）。
2. **不得放宽既有拒绝条件**：新条件为严格更严（`p != canonical` 涵盖 `stem != 账上名` 的全部情形并新增
   同名异路径）；r5 的 fail-closed 面（symlink / 非普通文件 / 读不回 / symlink 目录）与其余四门零放宽。
   请核：有无任何输入在旧态被拒、新态被放行（方向必须单向收紧）。
3. **其余命题不被本轮回退**：三条 r5-HIGH 整改（改名残留 fail-closed / 剔行分层 / 字节锚）、r6 的
   MEDIUM-1（容忍面机器段口径）、LOW-1 文案；真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 /
   过期零产物 / undo 全树逐字节还原 / 0 物理删除 / callout 默认关 / 零改动（`split_preview.py` +
   `undo_journal.py`）/ 不加 SKILL.md / 只改两份文件。
4. 残余风险（沿承，请复核仍成立）：完整协同重写 preview JSON（指纹 + `board_sha256` + `sources[]`）在带内
   不可判，需带外生成时间锚，超出本卡边界；`节点/` 下 symlink 目录 ⇒ fail-closed（保守）。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r7-HIGH-1 是否闭合，再看新面）

1. 独立验伪「canonical 顶层路径」判据是否**完全**闭合 r7-HIGH-1（列出你检验过的位置类别与结论）；
   特别核 `p != node_dir / f"{by_id[sid]}.md"` 的路径语义（是否需 `resolve()` / NFC / `os.path.samefile`）。
2. 核「只收紧不放宽」：给旧/新判据的真值表或反例搜索结论。
3. 是否引入新的 BLOCKER/HIGH（含误伤面：合法工具自建文件、合法重跑/分段确认、插入后重跑）。
4. LOW 只报可复现的；零改动面与「只改两份文件」核对。

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分节（无则写「无」）；每条给 `file:line` + 复现思路
（「未被拦下的输入」或「负控输入」）；末尾给结论计数 `BLOCKER n / HIGH n / MEDIUM n / LOW n`。
只读，不要改任何文件；不要运行 apply/undo/pytest（按作者提供的 evidence 静态验伪即可）。
