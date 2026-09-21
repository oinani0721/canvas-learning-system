# CARD-G8-7 送审 prompt（r4 · 绑最终 HEAD）

> ✅ **实跑解析回填（2026-09-20 整改轮补）**：本次 r4 实跑绑定 **PREV=`d9d64ea1`、FINAL_SHA=`484ccba0`**（正文 `$PREV`/`$FINAL_SHA` 在送审时由运行方替换为该两值；存档 = `codex-review-CARD-G8-7-r4.md`）。⚠️ r4 评审指出：本文件正文留占位符 ⇒ 归档 prompt 不自包含；整改轮已另出 **`codex-prompt-CARD-G8-7-r5.md`（SHA 内联，自包含）**，后续轮以 r5 为范式。
>
> ⚠️ 使用条件：**最终修订 commit 之后**才跑本 prompt，且把 `$PREV` / `$FINAL_SHA` 两处占位替换为实际值；存档首部按协议 §2.4 写（批次 / 模型 `glm-5.3` / reasoning_effort `max` / codex 实测版本 / 命令 / 审查绑定 SHA / 会话头自证三行含 `.stderr` 行号）。
> 命令：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r4.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r4.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r4.stderr </dev/null`

## ① 背景与最小读取面（写死）
本件审查对象 = `[BATCH-2026-09-18-第十五批 / CARD-G8-7]` 的**授权走查证据包最终版**（`_bmad-output/审查/evidence-g87-journey/**`）。零代码卡：`git --no-pager diff --stat --no-color $PREV $FINAL_SHA -- . ':(exclude)_bmad-output'` 应为空。
读取面（其余不读）：
- `git --no-pager diff --stat --no-color $PREV $FINAL_SHA` 全清单（应全在 `_bmad-output/`）
- `evidence-g87-journey/`：`00-README.md`、`01-skill-versions.md`、`03-breakpoints.md`、`manifest.json`、`04-journey-log.md`（全文）
- `02-live-snapshot-before-authorized.txt` / `04-live-snapshot-after-authorized.txt`（首部 5 行 + 行数）、`silent-rewrite-gate-authorized-*.txt`（全文）、`artifacts-sha-authorized-*.txt`（全文）、`overview-curl-*.txt`
- 5 份独立检查报告：`glm53-check-annotation-*.md`、`glm53-render-check-*.md`、`glm53-pi-review-*.md`、`glm53-503-review-*.md`、`pi-round-session-digest-20260920.md`
- `docs/release-evidence/manifest.schema.json:47,139,666-690,713`；`canvas-vault/.claude/skills/{quiz-answer/SKILL.md:74, start-exam-board/SKILL.md:78, board-recap/SKILL.md:54-56}`；总账 v2 `:386-391,977,1007`；卡文 §一(d)(e)

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）
1. 走查在 **pi**（vault 内会话，cwd=canvas-vault）完成六环节：① 用户批注（`%%cb-muad37hsmsm6%%` + 16:07 补 marker）；② board-recap 三件 + Step5.5 `VERIFY PASS`；③ **待重跑**（marker 已补；此前 0 命中归因=marker 缺失，索引活性有对照探针）；④ `检验白板/CS 61B-2026-09-20-2235.md`（**Context 档 FAIL 已如实登记**：同会话先读过节点正文）；⑤ mastery 0.01→0.02 + `fsrs_*` 六件 + calibration + ledger `answer_scored`；⑥ 车道侧只读 GET http=200。
2. 零静默改写门（授权窗口）：`changed=11 / outside=2`；2 件 = `outputs/思维导图-*.excalidraw.md`（14:05:52 同秒），写者 = **自研 Excalidraw v3「一次性导出」器**（设计记录 `研究/2026-08-15-思维导图-Excalidraw-需求与迭代记录.md:31,94`），触发者待用户确认。其余 9 件 ⊆ 声明写入面。
3. 已知第二写者：Obsidian 插件 `canvas-learning-system` 的 `FrontmatterTipsSync` 会重序列化节点 frontmatter（字节差异、语义等价）。
4. 快照面假阴性：`learning_events.jsonl`（vault 根）不在四目录+state 快照面内，窗口内 +3 事件（声明写入面内）。
5. 独立发现（另有登记，不要求本卡修）：`decay_beta.update_after_idle` 在低证据+久闲置下**答错 μ 反升**（GLM 上轮已独立复算：0.013333→0.015293）；pi 宿主 MCP 工具名与 canonical `mcp__canvas-learning-mcp__*` 不兼容。
6. skill dev↔live 差异 8 处双列、`evidence_level ≤ E3`、`signoff` 仅用户勾选后填。

## ③ 按重要性排序的核验点
⓪ 门与负控：`outside=2` 的定性与处置是否自洽（已知写者 vs 阻断级登记）；白名单是否过宽/是否实例化；
① ③ 的"待重跑"状态在 manifest/UAT 中是否如实（不得写作 pass）；
② ④ 的 Artifact/Context 两档拆分是否成立；⑤ 的证据字段是否足够（a/b/attempt/fsrs/calibration）；
③ 第二写者与 ledger 假阴性是否被正确归类（不得当作"门绿"的豁免）；
④ 断点归属是否把部署冻结误记缺陷；
⑤ 本卡产出是否有独立价值（非空壳）；
⑥ 零代码：`$PREV..$FINAL_SHA` 排除 `_bmad-output` 后是否为空。

## ④ 输出格式
BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。

## ⑤ 边界
只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器的设计。
