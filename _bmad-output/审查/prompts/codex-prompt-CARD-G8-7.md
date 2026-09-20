# Codex 复核 prompt — CARD-G8-7（两白板全旅程走查证据包）

> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7
> 本 prompt 为**最小读取面**；请只读下列文件，不要扩面。

## ① 背景 + 读取面

**背景**：CARD-G8-7 是零代码证据包卡（kind=ledger）。用「当前已上线能力」真实走「原白板 → 检验白板」全旅程（vault 准备 → `/board-recap` → `search_notes` → `/start-exam-board` → `/quiz-answer` 本地 `mastery_*`+`fsrs_bridge` → 次日总览页 `/api/v1/review/overview/page`），逐环节留命令 / 产物 sha256 / 截图 / skill 版本 hash。**真实旅程需用户当次授权并在 vault 内会话执行**；本次用户裁定**不授权** ⇒ 六环节全 `not_run` + SKIP 登记，仅车道侧（证据包 / 快照 / 门 / 负控）落地。改动面全在 `_bmad-output/`。不做 ChatGPT 终审（G1-8）。

**读取面（写死，只读这些）**：
1. `git --no-pager status --porcelain --no-color` 与 `git --no-pager diff --stat --no-color 9d4f7bf0 HEAD -- . ':(exclude)_bmad-output'`（应空）
2. `_bmad-output/审查/evidence-g87-journey/00-README.md`
3. `_bmad-output/审查/evidence-g87-journey/01-skill-versions.md`
4. `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md`
5. `_bmad-output/审查/evidence-g87-journey/manifest.json`
6. `_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json`
7. `_bmad-output/审查/evidence-g87-journey/02-live-snapshot-before.txt` 首 5 行
8. `_bmad-output/审查/evidence-g87-journey/04-live-snapshot-after.txt` 首 5 行
9. `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-*.txt` 全文
10. `_bmad-output/审查/evidence-g87-journey/negctl1-*.txt` / `negctl2-signoff-*.txt` / `negctl1-cardtext-sed-noop-*.txt` 全文
11. `_bmad-output/审查/evidence-g87-journey/manifest-red-*.txt` / `manifest-green-*.txt` / `manifest-validator-conflict-*.txt` 全文
12. `docs/release-evidence/manifest.schema.json` :47 / :139 / :666-690 / :713
13. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` :74
14. `canvas-vault/.claude/skills/start-exam-board/SKILL.md` :78
15. `canvas-vault/.claude/skills/board-recap/SKILL.md` :54-56
16. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` :386-391 / :977 / :1007
17. 卡文 `P3-C.md` §一(d)(e)（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md`）

## ② 作者自述（请独立核对，不要采信）

1. 旅程跑的是 **live skill 副本**，与 HEAD 有 **8 处**不同，已双列登记（`01-skill-versions.md`）；本卡**零部署**。
2. **零静默改写门**：白名单与声明写入面一致；未授权 ⇒ before/after 相同、`outside=0`。
3. 未授权环节**全为 `not_run`**，无一装绿（`manifest.json` assertions + `03-breakpoints.md` §C）。
4. **manifest 过校验**：根件 `manifest.json`（卡文字面 `journey_id="G8-7"`）**恒红**（借用的 release schema 要求 `journey_id` 为 `J01-J10` 且 S6 要求 `<rc>/journeys/<Jxx>/` 路径）；**一致性副本** `b15-g8-7/journeys/J06/manifest.json` 绿跑 `rc=0`，并在其上做「先红(S3)/后绿」成对——此偏离经用户 2026-09-19 裁定（混合方案）。
5. `evidence_level` 自评 **E0 ≤ E3**；`signoff` 未经用户勾选保持 `pending`。
6. 本卡**零代码零部署**（`backend/`、`canvas-vault/.claude/skills/**`、`scripts/` 无改动）。
7. 另登记两处**卡文缺陷**：卡文 §二.7 零静默改写门 `awk '{print $3}'` 对含空格路径截断；卡文 §二.8 负控① 的 `sed '…\1f'` 在 `原白板/CS.md` 的 sha 第 64 位恰为 `f` 时是 no-op（实测 diff=0）。两处均已给出对照输入 / 修正判据（见 `negctl1-cardtext-sed-noop-*.txt`、`silent-rewrite-gate-literal-*.txt`）。

## ③ 请按重要性核对（⓪ 最重）

- ⓪ **零静默改写门是否真能抓到集外变化**：负控① 是否红在**指定文件**而非「diff 非空」？卡文字面判据与修正判据的差异是否被如实登记？
- ① **白名单是否过宽**：`节点/` 整目录放行会否掩盖 skill 误写别的节点？是否应收窄到被答节点 + 新材料两文件？
- ② `search_notes` 环节「检回含新材料」判据是否可被旧材料同名命中而假绿？
- ③ 环节⑤「`mastery_*` 出现或变化」是否足以证明 FSRS 更新（`fsrs_bridge` 字段是否也该核）？
- ④ **断点归属切片**是否把「部署冻结造成的差异」误记为缺陷？
- ⑤ 未授权路径下本卡产出是否仍有独立价值（不是空壳）？
- ⑥ manifest 校验的**混合解析**是否诚实、可复核（根件红、副本绿、裁定留痕）？

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给 `file:line` + 一句复现思路。描述现象时请使用中性表述：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。

## ⑤ 边界

只读复核；不连库；不评 G1-8 终审结论；不评 G6-13 跨日旅程；不评 8 处 skill 差异本身的对错（那是部署卡的面）。若读取面不足以判断，请指出缺口而不是外推。
