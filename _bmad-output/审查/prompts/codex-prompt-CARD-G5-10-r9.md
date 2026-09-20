# CARD-G5-10 独立复核 round-9（绑 `9943b59d`）—— r8-HIGH-1「不可列举目录」整改后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`9943b59d`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关；`节点/` 契约是**扁平池**）。
轮次史：r1 `db9fc54f` B1/H4/M3/L1 → r2 `f3260ed0` B0/H2/M2/L1 → r3 `d5a06d33` B0/H2/M1/L2 →
r4 `f42ff845` B0/H2/M1/L2 → r5 `80e4a319` B0/H3/M0/L2（整改于 `b8b8357a`）→ r6 `b8b8357a` B0/H1/M1/L2
（整改于 `8ce16fbb`）→ r7 `8ce16fbb` B0/H1/M0/L1（整改于 `e2abb8ef`）→ r8 `e2abb8ef` **B0/H1/M0/L0**
（不可列举目录让 `rglob` 静默漏段）→ 本卡 r9 整改。

**本轮整改面（重点读取面）**：
```
git --no-pager diff --no-color 9943b59d^ 9943b59d -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，37 条用例）
- r8 存档（本 HIGH 原文与修复方向）：`_bmad-output/审查/codex-review-CARD-G5-10-r8.md`

既有读取面（本卡零改动）：`split_preview.py` `:38-52,433-449,608-780,850-890,1090-1180`；`undo_journal.py` 全文。

**jev 分诊（绑 `9943b59d`）**：`split_apply.py` URG 3.01（error_handling, P=.81）· 测试 1.60（pass）；③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：点名套件 **37/37 绿**；负控 **8 段**各自点名红 +
逐字还原；AST 删除门 1/0；zero-writers 两脚本 sha 未动；`tests/skills` 目录级 4 红 = 历轮**逐字同**的既有基线
（`test_skill_portability_lint.py`）；`tests/unit` nodeid diff gt=0 / lt=1（只减成立）。

## ② 作者自述请独立核对（当成待验证命题）

1. **r8-HIGH-1（不可列举目录静默漏段）**：新增 `_enumerate_node_pool(node_dir)` —— 显式
   `os.scandir` 递归枚举（⛔ 不用 `Path.rglob`：其递归 `scandir` 遇 `OSError` 静默跳过整段），
   返回 `(entries, 拒绝原因)`；**任何一层目录枚举失败 ⇒ 返回原因, 调用方 fail-closed 拒绝整批**
   （文案「池内目录无法枚举（…）—— 无法排除里面藏着同 stable_id 的残留, 拒绝（fail-closed…）」）。
   覆盖面与旧 `rglob("*.md")` + `rglob("*")` 兜底等价并新增：递归 .md、symlink 目录、symlink 的 .md、
   目录名以 `.md` 结尾（拒绝）、非普通文件（拒绝）、r8 的 canonical 顶层路径判据保持不变。
   负控 ㊲（子目录 `chmod 000` + **保持原名**）在 `e2abb8ef` 上 `created=1`、整改后拒绝（`finally` 恢复权限；
   root 环境 skip）。
   请核：显式走法是否**真的完全闭合** —— 还有没有能藏同 id 残留且不被枚举/不被拒的条目类别（例如：
   枚举中途权限变化、mount point / bind mount、极深嵌套、`os.scandir` 对 `node_dir` 本身失败、
   非 `OSError` 异常、`dir-md` 分支与旧语义是否等价）；以及 fail-closed 是否过宽（合法 vault 里存在
   一个不可读目录就整批拒绝，作者认为是既有保守取向，请判断是否可接受/是否有更精准做法）。
2. **只收紧不放宽**：相对 `e2abb8ef`，旧判据 `p != node_dir / f"{by_id[sid]}.md"` 与旧的 symlink/非普通文件/
   读不回门全部保留；新增的只是「枚举失败 ⇒ 拒绝」。请给真值表或反例搜索结论证明无「旧拒新放」。
3. **其余命题不被本轮回退**：三条 r5-HIGH 整改（改名残留 fail-closed / 剔行分层 / 字节锚）、r6 的
   MEDIUM-1（容忍面机器段口径）、r6-LOW-1 文案、r7 的 canonical 路径规则；真 `scan_vault` 判 derived 非孤儿 /
   歧义零持久化 / 过期零产物 / undo 全树逐字节还原 / 0 物理删除 / callout 默认关 / 零改动
   （`split_preview.py` + `undo_journal.py`）/ 不加 SKILL.md / 只改两份文件。
4. 残余风险（沿承，请复核仍成立）：完整协同重写 preview JSON（指纹 + `board_sha256` + `sources[]`）在带内
   不可判，需带外生成时间锚，超出本卡边界。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪 r8-HIGH-1 是否闭合，再看新面）

1. 独立验伪「显式 `scandir` + 枚举失败 fail-closed」是否**完全**闭合 r8-HIGH-1（列出你检验过的条目/目录
   类别与结论）；特别核 `_enumerate_node_pool` 的异常面（只捕 `OSError`？够不够）、`dir-md` /
   `symlink-md` / `symlink-dir` 分类与旧覆盖面逐项等价性、以及 `sorted(it)` 的迭代器资源语义。
2. 核「只收紧不放宽」：真值表或反例搜索结论。
3. 是否引入新的 BLOCKER/HIGH（含误伤面：合法 vault 有不可读目录、合法重跑/分段确认、插入后重跑、
   大树 vault 的枚举代价）。
4. LOW 只报可复现的；零改动面与「只改两份文件」核对。

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分节（无则写「无」）；每条给 `file:line` + 复现思路
（「未被拦下的输入」或「负控输入」）；末尾给结论计数 `BLOCKER n / HIGH n / MEDIUM n / LOW n`。
只读，不要改任何文件；不要运行 apply/undo/pytest（按作者提供的 evidence 静态验伪即可）。
