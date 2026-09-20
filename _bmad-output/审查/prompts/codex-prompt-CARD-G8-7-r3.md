# Codex 复核 prompt — CARD-G8-7（r3：回应 r2 的 H-1 / M-1 / M-2）

> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 · round-3
> 最小读取面；请只读下列文件。

## ① 背景 + 读取面

**背景**：零代码证据包卡；用户裁定**不授权**真实旅程 ⇒ 六环节全 `not_run` + SKIP；改动面全在 `_bmad-output/`。r1：B=0/H=5/M=2/L=2；r2：B=0/**H=1**/M=2/L=0。r3 回应 r2。

**读取面**：
1. `git --no-pager status --porcelain --no-color` 与 `git --no-pager diff --stat --no-color 9d4f7bf0 HEAD -- . ':(exclude)_bmad-output'`（应空）
2. `_bmad-output/审查/evidence-g87-journey/manifest.json`
3. `_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json`
4. `_bmad-output/审查/evidence-g87-journey/manifest-bindings.md`（新增：非循环绑定层）
5. `_bmad-output/审查/evidence-g87-journey/manifest-isolation-v2-20260919T212305.txt`（新增：绑定冻结对象）
6. `_bmad-output/审查/evidence-g87-journey/negctl-strengthen-v2-20260919T212246.txt`（新增：可复跑）
7. `_bmad-output/审查/evidence-g87-journey/scripts/negctl_strengthen.sh`（新增：脚本本体）
8. `_bmad-output/审查/evidence-g87-journey/00-README.md`
9. `_bmad-output/审查/evidence-g87-journey/01-skill-versions.md`
10. `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md`
11. `_bmad-output/审查/evidence-g87-journey/02-live-snapshot-before.txt` 首 5 行
12. `_bmad-output/审查/evidence-g87-journey/04-live-snapshot-after.txt` 首 5 行
13. `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-20260919T173124.txt` 与 `silent-rewrite-gate-literal-20260919T173124.txt`
14. `_bmad-output/审查/evidence-g87-journey/negctl2-signoff-20260919T173154.txt`
15. `_bmad-output/审查/evidence-g87-journey/manifest-validator-conflict-20260919T170857.txt`
16. `docs/release-evidence/manifest.schema.json` :47 / :139 / :666-690 / :713
17. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` :74 / `start-exam-board/SKILL.md` :78 / `board-recap/SKILL.md` :54-56
18. 卡文 `P3-C.md`（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md`）

## ② r2 三项的回应（请独立核对是否闭合）

- **H-1（isolation 未绑最终 J06 对象）** → 先冻结副本（`journeys/J06/manifest.json`，SHA `866983aadbf9b0e0e8a91d1f917358b0058e72d4b1524b351e20344d7be092cf`，commands=9 / artifacts=19），再在其上重跑 isolation（`manifest-isolation-v2-*.txt`：首行记冻结 SHA、各段 `restore_sha`、末行 `final_sha` 均为该 SHA）；自引用排除规则与绑定见 sidecar `manifest-bindings.md`（第 2/3/5 节）；manifest 的 `notes` 按**文件名**引用该 sidecar（不带 SHA，避免循环）。
- **M-1（强化负控缺精确命令/rc/白名单实现）** → 新增可复跑脚本 `scripts/negctl_strengthen.sh`（`bash` 直接跑）与输出 `negctl-strengthen-v2-*.txt`：打印白名单 matcher 全文、输入面 before/after SHA、每段精确命令、`changed/outside` 明细、逐段 `rc`；D 段含 `原白板/CS.md` **完整原文行** + 第 64 位字符 `f` + `before vs bm_d 差异=0`（no-op 身份链）。
- **M-2（isolation 不在 manifest 账本、缺非循环登记）** → 由 `notes` + sidecar `manifest-bindings.md` 承担非循环登记层；sidecar 第 4 节如实声明早期 isolation/red/green 记录属于较早副本对象（`e0d39556…`）、不绑定冻结对象，判据以 v2 为准。

## ③ 请核对

- ⓪ 自引用排除规则是否成立（把 isolation 输出登记进 artifacts 会不会形成 SHA 循环）？非循环绑定层是否足以让 reviewer 仅凭包内文件定位最终对象？
- ① 冻结 SHA 是否贯穿 isolation v2 的 before/各 restore/final？
- ② `negctl_strengthen.sh` 是否可从产物本身重建同一门实现（白名单 matcher + 提取规则 + 逐段 rc）？
- ③ `search_notes` 身份绑定 / 环节⑤ `fsrs_*` 区分 / 断点归属 / 未授权独立价值 是否维持 r2 的 PASS？
- ④ 新证据是否引入新的不一致（如样例文件 sha 漂移、路径越界）？

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条 `file:line` + 一句复现思路。中性表述：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。

## ⑤ 边界

只读；不连库；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错。读取面不足请指缺口，勿外推。
