# CARD-G8-7 送审 prompt（r5 · 整改轮 · 绑新 HEAD · SHA 内联自包含）

> 本件为 r4（`codex-review-CARD-G8-7-r4.md`：BLOCKER 1 / HIGH 1 / MEDIUM 6 / LOW 2）的**闭合核验轮**。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r5.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r5.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r5.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `d9d64ea1`**（r4 绑定的内容 commit 的父）；**FINAL = `67796927`**（整改轮 commit；`git rev-parse --short=8 HEAD` 应等于它）。
- 审查对象 = `[BATCH-2026-09-18-第十五批 / CARD-G8-7]` 证据包整改轮（改动面应全在 `_bmad-output/`）。**零代码卡**：
  `git --no-pager diff --stat --no-color d9d64ea1 67796927 -- . ':(exclude)_bmad-output'` 应为空。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color d9d64ea1 67796927`（全清单）
  2. `_bmad-output/审查/codex-review-CARD-G8-7-r4.md`（**本轮的闭合核验对象 = 其 11 项发现**）
  3. `_bmad-output/审查/evidence-g87-journey/`：`manifest.json`、`03-breakpoints.md`、`04-journey-log.md`、`manifest-red-remediate-*.txt`、`negctl1-remediate-*.txt`、`negctl2-remediate-*.txt`、`silent-rewrite-gate-remediate-*.txt`、`skill-versions-remediate-*.txt`、`structural-remediate-*.txt`、`ruff-remediate-*.txt`、`unit-remediate-*.txt`（含 `-nosandbox-` 版）全文/首尾
  4. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md`（§1 ③ / §2 / §4-C 三处）
  5. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r4.md`（首部回填块）+ 本件 `-r5.md`
  6. `docs/release-evidence/manifest.schema.json:47,139,666-690,713`

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **B-1 处置**：`codex-prompt-CARD-G8-7-r4.md` 首部已回填实跑绑定（PREV=`d9d64ea1` / FINAL=`484ccba0`，仅加注不改正文）；本轮 `-r5.md` 的 SHA 内联 = 自包含，命令可直接照跑。
2. **H-1 处置**：UAT §2 门口径已由"`outside=0`"更正为 **`changed=11 / outside=2`**，并写明 2 件 = `outputs/思维导图-*.excalidraw.md`、写者机制 = 自研 Excalidraw v3 一次性导出器、**触发者待用户确认**（开放项）；`03-breakpoints.md` §B 新增同级行。
3. **M/L 处置**：M-1 = UAT 4-A 表与 `04-journey-log.md` T1..T6 表均回填为终版（并注"权威面 = manifest/4-C"）；M-2 = UAT §1 ③ 期望路径改 `节点/csm-tutoring-unit-credit.md`；M-3 = 31→**35** artifacts；M-4 = `03-breakpoints.md` §C 加"历史层（未授权段）已被 09-20 授权段取代"横幅；M-5 = ⑤ 断言 note 显式降级为"更新发生证明，非完整状态迁移审计"并列出未登记的前值字段；M-6 = §B 增 `outside=2` 行；M-7 = manifest `notes` 补时间口径（18:06:19 仅六环节；裁判/整改归档在后）；L-1 = `artifacts-sha-authorized-*.txt` 追加"18:07 时点，03/04 后续更新以 manifest 终版为准"注记并重算哈希；L-2 = 快照描述改 `wc -l` 实测 50/52（头注 1 行）。
4. **承重裁判在整改树重跑**（全部落档）：manifest 先红 rc=1 红在 S3；后绿 rc=0；负控② rc=1 红在 signoff 必填；负控① `mutated_lines=1 / hits=1 / changed_total=12 / orig_same=1`；零静默改写门重算 `changed=11 / outside=2`（与授权窗口存档逐条一致）；skill dev↔live 复算 **DIFF=8**；ruff `files=0` + F821 锚 rc=1；`tests/unit` 免沙箱全量 = 33 红（与 33 基线**逐 nodeid 相同或更少**：仅 `<` 1 条 = 已知 flaky 转绿）。
> ⚠️ **作者自述笔误更正（自查，2026-09-20）**：② 第 4 条写「免沙箱全量 = 33 红」，权威档实为 **32 failed / 5845 passed**（33 = 沙箱首跑数，含 1 条沙箱假红）；r5 报告「作者自述逐条裁决 #4」已独立指出，两档存档均在案。

5. **沙箱假红如实登记**（不删）：首次 `tests/unit` 在 Codex 沙箱内跑出 1 条新红 `test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`，失败原因 = `PermissionError: [Errno 1] Operation not permitted`（该测试要 `sock.bind`）；免沙箱单跑 1 passed + 免沙箱全量重跑绿清单；两跑 archive 并存。
6. **未变项**：本卡零代码零部署；live vault 零写（旅程写入全部由用户在 pi 的 vault 内会话执行）；③/⑥ 判据未改判（仍 fail，用户侧截图/marker 复跑未发生）；`signoff` 仍 `pending`（用户未勾选）；`evidence_level=E2`。
7. **门口径补正**：快照门 known_limitations 已按 r4 建议统一为 "scoped gate：不覆盖 vault 根 `learning_events.jsonl`、`.obsidian/`、`.trash/`"。

## ③ 按重要性排序的核验点

⓪ **r4 11 项逐条闭合判定**（B-1 / H-1 / M-1..M-7 / L-1 / L-2）：每项给"闭合 / 部分 / 未闭合"，未闭合须给 `file:line` + 一句复现思路。
① **双真相源检查**：UAT §2 终版表、4-C、`manifest.json` assertions、`04-journey-log.md` T1..T6 四面对同一环节的判据是否一致（不得一处 pass 一处 fail；fail/partial 不得被文字洗成 pass）。
② **零代码零写面**：`d9d64ea1..FINAL` 排除 `_bmad-output` 是否为空；整改是否触碰 live vault / `canvas-vault/.claude/skills/**` / `backend/app/**`（应为零）。
③ **artifacts 完整性**：整改后 manifest `artifacts` 是否每件 `sha256+bytes` 与磁盘一致（含追加注记后的 `artifacts-sha-authorized-*.txt`、被改写的 `03-breakpoints.md`/`04-journey-log.md`）；J06 结构内副本 validator 是否 rc=0。
④ **门未被放宽**：零静默改写门白名单是否与授权窗口版本逐条相同（整改轮不得放宽/追加）；`outside=2` 是否仍作为**开放项**保留（触发者未确认前不得写成"已闭合"）。
⑤ **沙箱假红登记**：in-sandbox 红与免沙箱绿两跑是否都在案、结论是否可被独立复现（`sock.bind` 权限）；不得用"重跑就绿"掩盖未登记。
⑥ **r5 自包含性**：本 prompt 是否确实内联了 PREV/FINAL、命令照跑是否不再出现占位符。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若 11 项全部闭合且无新 B/H，请明确写 "r4 闭合，本卡可交主 session"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选（用户侧开放项：③ 带锚点复跑 / ⑥ 截图 / 思维导图触发者确认 / 签字）。
