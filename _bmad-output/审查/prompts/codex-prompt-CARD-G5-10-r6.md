# CARD-G5-10 独立复核 round-6（绑 `b8b8357a`）—— H 整改（r5 三条 HIGH）后的复审

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`b8b8357a`**（= 送审时 HEAD；tracked 工作树干净）。

背景：board-split 执行侧 `split_apply.py`（消费 preview + `--confirm`，准入五门后原子创建 `节点/` 派生 md；
复用 P7-A `undo_journal.py`；默认路径 0 物理删除；callout 默认关）。
轮次史：r1 `db9fc54f` B1/H4/M3/L1 → r2 `f3260ed0` B0/H2/M2/L1 → r3 `d5a06d33` B0/H2/M1/L2 →
r4 `f42ff845` B0/H2/M1/L2 → r5 `80e4a319` **B0/H3/M0/L2**（三条 HIGH：①改名残留 fail-open ②创建正文过度剔除
preview 时真实 callout 行 ③指纹绑定缺陷）→ 主 session 已批补轮 r6/r7，本卡做 H 整改。

**本轮整改面（重点读取面）**：
```
git --no-pager diff --no-color b8b8357a^ b8b8357a -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（终态全文：`cat` 它）
- `backend/tests/skills/test_g5_10_split_apply.py`（终态全文，33 条用例）
- r5 存档（三条 HIGH 原文与复现思路）：`_bmad-output/审查/codex-review-CARD-G5-10-r5.md`
- 本卡 P7-C 之外的改动不属本轮：`654e76f0`/`3581f0d1` 是别的卡（G5-12）的文件，请忽略。

既有读取面（本卡零改动）：`split_preview.py` `:38-52,433-449,608-780,850-890,1090-1180`；`undo_journal.py` 全文。

**jev 分诊（绑 `b8b8357a`）**：`split_apply.py` URG 3.29（logic, P=.90）· 测试 1.86（test_or_docs, P=.72）；
③ 按 urgency 降序。

已跑裁判（作者声明，见 `_bmad-output/审查/evidence-g510/`）：点名套件 33/33 绿；负控 5 段（3 既有 + 2 新增）
各自点名红 + 逐字还原；AST 删除门 1/0；zero-writers 两脚本 sha 未动；`tests/skills` 目录级 4 红 = 与上轮**逐字同**
的既有基线（`test_skill_portability_lint.py`）；`tests/unit` nodeid diff gt=0 / lt=1（只减成立）。

## ② 作者自述请独立核对（当成待验证命题）

1. **r5-HIGH-2（改名残留 fail-open）**：`existing_split_stable_id` 去掉 200 行 frontmatter 上限；
   池扫描对 `symlink` / 非普通文件 / 读不回一律 **fail-closed 拒绝**（不再 `continue` 跳过）。
   负控 ㉗ 覆盖 r5 的两条路径（symlink 残留 / id 位于 200 行后），旧代码上各自复现「同 id 双产物
   created=1」，整改后拒绝且零产物。
2. **r5-HIGH-3（callout 过度剔除）**：`_span_drift_reason` 返回 `(原因, 是否走 callout 容差)`；
   `run_create` 只在容差路径剔行 —— 原字节指纹**精确相符**时区间内 callout 形态行原样保留。
   ⚠️ 作者实测并请复核：r5 给的「preview 时已在正文的真实 callout 行」输入在本 revision 会**先撞**
   既有 `_callout_mapped_span` 行号对账（`(7,11)≠(7,12)`）而被拒绝 —— 旧代码也到不了 `run_create` 的过剔；
   故该层语义用 ㉙ 在函数面钉住（旧代码返回 `None` 而非 `(None, False)` 即为红）。
   请独立验伪「过剔在本 revision 是否真的不可达」，以及 ② 的分层是否与门① 第一层自洽。
3. **r5-HIGH-1（指纹绑定缺陷）**：新增 `_anchor_sha_reconciliation` —— 对 `confirmed` 的锚文件
   （板或种子笔记）从 `sources[]` 取 sha256 对账**当前字节**；容忍面**只**剔「本 preview 候选名的
   **精确形态** callout 行」（逐字等于 `callout_line(resolved_name)`，含 CRLF 尾 `\r`）；另加
   `sources[]` 板记录与 `board_sha256` 的**双写自洽**门。
   作者判定 r5 原处方（旧 `content_fingerprint` vs fresh 候选指纹对账）对其自身复现**无效**（两侧
   都绑到改后值），故改用字节锚。负控 ㉚（改板 + 抄指纹）/ ㉛（改**种子笔记** + 抄指纹）/ ㉝（双写不自洽）
   在旧代码 created=1、整改后拒绝零产物；㉜ 钉容忍面不误剔 preview 时既存的非本轮 callout（strip-all 会 livelock）。
4. **残余风险（作者自认，请核）**：**完整重写 JSON**（`content_fingerprint` + `board_sha256` + `sources[]`
   一起改）在带内不可判 —— 它与「对改动后的板重新生成一份合法 preview」字节上不可区分（preview JSON 无生成
   时间戳）；需带外锚（生成时的 append-only 日志）才能闭合，超出本卡「只改 split_apply.py + 其测试」的边界。
   另：本轮起「同锚文件里、被确认候选 span 之外」的无关漂移会拒绝（旧版放行），作者认为与门①「板或种子笔记
   已改, 请重跑 preview」的既有立场一致、且补救廉价。
5. 其余命题同前轮：真 `scan_vault` 判 derived 非孤儿 / 歧义零持久化 / 过期零产物 / undo 全树逐字节还原 /
   0 物理删除 / callout 默认关 / 零改动（`split_preview.py`+`undo_journal.py` 未改）/ 不加 SKILL.md /
   只改上述两份文件。

## ③ 按重要性排序的问题（按分诊 urgency 降序；先验伪三条 H 的整改，再看新面）

1. 逐条独立验伪 ①②③ 是否真闭合 r5 三条 HIGH；重点核作者的两个判定是否成立：
   (a) ② 的过剔在本 revision 不可达（`_callout_mapped_span` 先拦）；(b) r5 的 HIGH-1 处方无效。
2. 新字节锚门自身：容忍面（精确形态 + 候选名限定 + CRLF 尾）是否有绕过或**误剔**；fail-closed 面
   （`sources[]` 缺记录 / sha 为 None / 非 UTF-8）是否过宽或过窄；与既有 `_callout_mapped_span`、
   `_span_drift_reason` 容差路径的交互是否有反例（含种子笔记锚、同 preview 分段确认、undo 后重跑）。
3. 是否存在新的 BLOCKER/HIGH（含：去掉 200 行上限后池扫描的最坏复杂度是否有 DoS 面；fail-closed 是否
   会把既有合法 vault 卡死）。
4. LOW 只报可复现的；零改动面与「只改两份文件」请核对。

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分节（无则写「无」）；每条给 `file:line` + 复现思路
（「未被拦下的输入」或「负控输入」）；末尾给结论计数 `BLOCKER n / HIGH n / MEDIUM n / LOW n`。
只读，不要改任何文件；不要运行 apply/undo/pytest（按作者提供的 evidence 静态验伪即可）。
