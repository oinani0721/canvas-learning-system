# Codex 复核 prompt — CARD-G8-7（r2：回应 r1 五项 HIGH）

> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 · round-2
> 本 prompt 为**最小读取面**；请只读下列文件，不要扩面。

## ① 背景 + 读取面

**背景**：CARD-G8-7 是零代码证据包卡。用户裁定**不授权**真实旅程 ⇒ 六环节全 `not_run` + SKIP 登记，仅车道侧（证据包 / 快照 / 门 / 负控 / manifest）落地。改动面全在 `_bmad-output/`。r1 复核给出 BLOCKER=0 / HIGH=5 / MEDIUM=2 / LOW=2；本 r2 为回应。

**读取面（写死，只读这些）**：
1. `git --no-pager status --porcelain --no-color` 与 `git --no-pager diff --stat --no-color 9d4f7bf0 HEAD -- . ':(exclude)_bmad-output'`（应空）
2. `_bmad-output/审查/evidence-g87-journey/00-README.md`
3. `_bmad-output/审查/evidence-g87-journey/01-skill-versions.md`
4. `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md`
5. `_bmad-output/审查/evidence-g87-journey/manifest.json`
6. `_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json`
7. `_bmad-output/审查/evidence-g87-journey/02-live-snapshot-before.txt` 首 5 行
8. `_bmad-output/审查/evidence-g87-journey/04-live-snapshot-after.txt` 首 5 行
9. `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-20260919T173124.txt` 与 `silent-rewrite-gate-literal-20260919T173124.txt` 全文
10. `_bmad-output/审查/evidence-g87-journey/negctl-strengthen-20260919T211354.txt` 全文（新增）
11. `_bmad-output/审查/evidence-g87-journey/negctl1-snapshot-20260919T173142.txt` 与 `negctl1-cardtext-sed-noop-20260919T173131.txt` 全文
12. `_bmad-output/审查/evidence-g87-journey/negctl2-signoff-20260919T173154.txt` 全文
13. `_bmad-output/审查/evidence-g87-journey/manifest-isolation-20260919T211402.txt` 全文（新增）
14. `_bmad-output/审查/evidence-g87-journey/manifest-validator-conflict-20260919T170857.txt` 全文
15. `docs/release-evidence/manifest.schema.json` :47 / :139 / :666-690 / :713
16. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` :74
17. `canvas-vault/.claude/skills/start-exam-board/SKILL.md` :78
18. `canvas-vault/.claude/skills/board-recap/SKILL.md` :54-56
19. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` :386-391 / :977 / :1007
20. 卡文 `P3-C.md`（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md`）

## ② r1 五项 HIGH 的回应（请独立核对是否真的闭合）

- **HIGH1**（卡文字面 sed 是 no-op、证据不自洽）→ 新增 `negctl-strengthen-*.txt` D 段：记录精确 `sed` 命令、`原白板/CS.md` 行原文 SHA 前 16 位、`before vs bm_d` 差异行数 = **0**（证 no-op）；另 `negctl1-snapshot-*.txt` 用**已确认 `diff=1` 的对照输入**（改 sha 末位 `f`→`0`）跑修正判据，红在指定文件、计数 = 1。
- **HIGH2**（含空格路径未覆盖）→ `negctl-strengthen-*.txt` C 段：对 `原白板/递归与分治 (Recursion & Divide-Conquer).md` 单行变异，并列卡文字面 `awk $3`（截断为 `原白板/递归与分治`）与修正版完整路径，`outside=1`。
- **HIGH3**（白名单过宽：`节点/` 整目录）→ 白名单已收窄为**声明写入面精确匹配**（占位 `节点/<被答节点>.md`、`节点/<新材料>.md` 等，未授权下匹配为空）；`negctl-strengthen-*.txt` A/B 段证明非白名单文件与**无关节点** `节点/lecture 2.md` 均被 outside 捕获（`outside=1`）。
- **HIGH4**（红/绿与 signoff 负控非孤立对照）→ 新增 `manifest-isolation-*.txt`：在一致性副本上顺序跑 [1] 绿 → [2] 仅 `result=pass` ⇒ **仅红 S3** → [3] 绿 → [4] 仅 `signoff=approved` 缺 user/at ⇒ **仅红 signoff** → [5] 绿，逐步 rc 与还原确认。
- **HIGH5**（`search_notes` 判据可被同名旧材料冒充）→ `00-README.md` 环节③ 判据已改为**须命中新材料完整 vault 相对路径 + 内容 sha256 前 16 位**（不接受仅同名/同标题字符串命中）。
- **MEDIUM1** → 环节⑤ 判据加 `-e fsrs_`，并要求「若仅 `mastery_*` 变化则登记为本地掌握度更新、**不证明** `fsrs_bridge`」。
- **MEDIUM2** → `manifest.json` / 副本的 `execution.commands` 扩为 9 条（含 validator 红/绿、零改写门、负控①②、tests/unit），`artifacts` 扩为 18 件（含各门与负控产物）；**自引用产物（validator 输出）不入 artifacts** 以免循环依赖。
- **LOW1** → `00-README.md` 索引已区分：`04-live-snapshot-after.txt`（未授权也做）vs `04-journey-log.md`（未授权不产出）。
- **LOW2** → `03-breakpoints.md` 该行已标「⚠️ 读取面外主张，未纳入包内复核」。

## ③ 请按重要性核对（⓪ 最重）

- ⓪ 零静默改写门负控是否**红在指定文件**而非「diff 非空」？修正判据 vs 卡文字面判据的差异是否被如实登记？白名单是否已无过宽前缀？
- ① `search_notes` 判据的身份绑定是否足以排除同名旧材料？
- ② 环节⑤ `fsrs_*` 与 `mastery_*` 的区分是否如实？
- ③ manifest 混合解析（根件恒红 / 副本绿 / 裁定留痕）是否诚实可复核？
- ④ 断点归属是否把部署冻结误记为缺陷？
- ⑤ 未授权路径下本卡产出是否仍有独立价值？

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给 `file:line` + 一句复现思路。描述现象时请使用中性表述：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。

## ⑤ 边界

只读复核；不连库；不评 G1-8 终审结论；不评 G6-13 跨日旅程；不评 8 处 skill 差异本身的对错。若读取面不足以判断，请指出缺口而不是外推。
