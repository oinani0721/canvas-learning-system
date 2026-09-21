> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-5
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r5.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r5.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r5.stderr </dev/null`
> 　（prompt = `codex-prompt-CARD-G8-7-r5.md`，SHA 内联自包含：PREV=`d9d64ea1` / FINAL=`67796927`）
> 审查绑定: `d9d64ea1..67796927`（FINAL = 审工作区 HEAD）
> 会话头自证（抄 .stderr 三行，行号括注；stderr 不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

所有核验完成。以下为 r5 闭合核验审查结论（本回复即由送审命令重定向落盘为 `codex-review-CARD-G8-7-r5.md`）。

---

# CARD-G8-7 r5 复核（闭合核验轮 · 绑新 HEAD `67796927`）

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-G8-7]`
> **绑定**：PREV = `d9d64ea1`；FINAL = `67796927`；当前 HEAD 实测 = FINAL（`git rev-parse --short=8 HEAD` = `67796927`）。
> **边界遵守**：只读；未连 7691/7687；不评 G1-8 终审、G6-13 跨日、8 处 skill 差异对错、Excalidraw 导出器设计；不要求用户签字位已勾选。

## 总裁决

**PARTIAL（接近闭合）**。r4 的 11 项发现中 **10 项完全闭合**，无新 BLOCKER/HIGH；但 **M-3 的同类缺陷在终版复现**：整改轮把 13 件承重裁判存档追加进 manifest（终版 `artifacts` = **48** 件，root 件与 J06 结构内副本均 48，且 48/48 `sha256+bytes` 复算全匹配），而 UAT §2 注记、UAT 4-C、`04-journey-log.md` 三处仍写 **“35 件 / 35/35 全匹配”**——计数在修复 `31→35` 之后又被自己的归档动作再次过期。另有一处 LOW 级排版残留。

计数：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 1**。

---

## 独立验证结果（全部本会话实跑）

- **零代码零写面**：`git --no-pager diff --stat d9d64ea1 67796927 -- . ':(exclude)_bmad-output'` 为空（exit=0）；提交链 `67796927 → cb4187c1 → 484ccba0 → d9d64ea1` 全为 docs。
- **manifest 完整性**：root `manifest.json` `artifacts` = **48** 件，逐件 `shasum -a 256` + `wc -c` 与登记值比对，**48/48 匹配，零 MISMATCH**（含被改写的 `03-breakpoints.md`/`04-journey-log.md`、追加注记后的 `artifacts-sha-authorized-*.txt`、全部 `-remediate-*` 裁判存档、J06 结构内副本自身）。
- **validator 独立重跑**：`python3 -B backend/scripts/validate_release_manifest.py .../evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json` → **PASS / rc=0**（J06 副本 journey_id=J06、result=partial、signoff=pending、48 artifacts）。root 件 → expected FAIL（`journey_id "G8-7"` 不匹配 `^J(0[1-9]|10)$`，即已登记的卡文缺陷）。
- **门未被放宽**：`silent-rewrite-gate-authorized-20260920T180031.txt` 与 `silent-rewrite-gate-remediate-20260920T183858.txt` **逐字节一致**（`diff` rc=0）：同 11 条 changed、同 2 条 outside（两个思维导图）、白名单零追加。
- **live 产物现值复核**：18:07 台账 13 条带哈希条目（vault 12 件 + pi session jsonl）当前 **13/13 哈希匹配** ⇒ 整改轮未触碰 live vault / state / session 存档。
- **单测两档独立复算**：沙箱档 33 failed（含 `test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`，`sock.bind("node")` → `PermissionError: [Errno 1] Operation not permitted`，在案未删）；免沙箱档 **32 failed / 5845 passed**；`diff remediate-nosandbox.nodeids base.nodeids` 仅少 1 条 = 已知 flaky `test_accept_candidate_already_accepted_returns_422`；`diff remediate.nodeids remediate-nosandbox.nodeids` 仅少沙箱假红那 1 条。
- **快照行数**：`wc -l` before=50 / after=52，与 manifest 终版描述（头注 1 + 条目 49/51）一致。
- **r5 自包含**：`grep '\$PREV\|\$FINAL' codex-prompt-CARD-G8-7-r5.md` 无占位符命中；PREV/FINAL 已内联（`:8`），命令可照跑。

## ⓪ r4 十一项逐条闭合判定

| # | 判定 | 证据 |
|---|---|---|
| B-1 | **闭合** | r4 prompt `:3` 首部回填实跑绑定（PREV=`d9d64ea1`/FINAL_SHA=`484ccba0`，仅加注）；r5 prompt `:8` SHA 内联、零占位符，命令自包含 |
| H-1 | **闭合** | UAT `:89-90`：`changed=11 / outside=2` + 两件 mindmap + 触发者待用户确认；旧 `outside=0` 显式标注为未授权段口径，勿再引用 |
| M-1 | **闭合** | UAT §2 终版表 `:80-87`、journey-log T1..T6 `:28-37` 均回填终版，并注“权威面 = manifest/4-C” |
| M-2 | **闭合** | UAT `:49-50` 期望路径改 `节点/csm-tutoring-unit-credit.md` + 口径更正注记 |
| M-3 | **部分闭合** | 31→35 的修复当时成立（UAT `:155`）；但终版 manifest 已 48 件，三处仍写 35 → 见新 M-1 |
| M-4 | **闭合** | `03-breakpoints.md:31` 历史层横幅（未授权段已被 09-20 授权段取代） |
| M-5 | **闭合** | `manifest.json:173` 显式降级“更新发生证明，非完整状态迁移审计”并列出未登记前值字段 |
| M-6 | **闭合** | `03-breakpoints.md:30` §B 新增 outside=2 同级行（触发者待确认、不放宽白名单） |
| M-7 | **闭合** | `manifest.json:546` notes 时间口径补正（18:06:19 仅六环节旅程；裁判/整改归档在后） |
| L-1 | **闭合** | 台账尾部追加“18:07 时点，03/04 后续以 manifest 终版为准”注记（不改写既有行）；manifest 内该台账条目哈希/字节与磁盘一致 |
| L-2 | **闭合** | `manifest.json:327,334` 改 `wc -l 50/52（头注 1 行）`，实测一致 |

## ① 双真相源检查

六环节判据四面（UAT §2 / UAT 4-C / manifest assertions / journey T1..T6）对齐：①pass ②pass ③fail ④fail（Artifact pass / Context fail）⑤pass ⑥fail（车道侧 pass、用户侧待补）；无一处把 fail/partial 洗成 pass；`result=partial`、`signoff=pending`、`E2`、③/⑥ 未改判。**唯一四面不一致点 = artifacts 计数（文档 35 vs manifest 48）**，见 M-1。

## 作者自述逐条裁决

| # | 自述 | 裁决 |
|---|---|---|
| 1 | B-1 处置 | **证实** |
| 2 | H-1 处置 | **证实** |
| 3 | M/L 处置 | **部分证实**：M-1/2/4/5/6/7、L-1/2 全证实；M-3 修复成立后终版计数再漂移（新 M-1） |
| 4 | 承重裁判重跑 | **证实（一处笔误）**：manifest 先红 rc=1 红在 S3（G8-7-3/4/6）；后绿 rc=0；负控① 四值一致；负控② rc=1 红在 signoff 必填；门重算与授权档逐字节一致；skill DIFF=8；ruff `from_d9d64ea1_files=0`+F821 锚 rc=1。笔误 = 自述“免沙箱全量 = **33** 红”，权威档实为 **32 failed / 5845 passed**（33 是沙箱首跑数；“仅 < 1 条 = flaky 转绿”部分正确） |
| 5 | 沙箱假红登记 | **证实**（两档并存、原因 `sock.bind` 权限、基线⊆关系均可独立复现，见上） |
| 6 | 未变项 | **证实**（零代码；live 13/13 哈希未漂移；③/⑥ 仍 fail；signoff pending；E2） |
| 7 | 门口径补正 | **证实**（`manifest.json:544` known_limitations 统一为 scoped gate：不覆盖 vault 根、`.obsidian/`、`.trash/`） |

---

# MEDIUM

## M-1. artifacts 计数在终版再次漂移：文档三处 35 vs manifest 实际 48

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:78`、`:155`；`_bmad-output/审查/evidence-g87-journey/04-journey-log.md:28`；对照 `manifest.json`（root 与 `b15-g8-7/journeys/J06/manifest.json` 均 `artifacts | length = 48`）。
- **事实**：M-3 修复把 31 改 35 正确；随后整改轮把 13 件裁判存档（manifest red/green、负控①②、gate、skill、structural×2、ruff、unit×2、nodeids×2、territory）追加进 manifest，终版 = 48，但三处计数文本未同步刷新。
- **影响**：r5 ① 双真相源判据下的索引漂移；读者按“35/35 全匹配”会漏 13 件整改轮承重证据（幸而这 13 件本身已在 manifest 内且哈希全匹配，非产物缺失）。
- **复现思路**：`jq '.artifacts | length' _bmad-output/审查/evidence-g87-journey/manifest.json` → 48；再 `grep -n '35 artifacts\|35/35\|35 件'` 上列三文件。
- **处置**：三处 35 → 48（可注“35 = 授权窗口时点，48 = 整改轮终版”），docs-only 新 commit 后按新 HEAD 轻量复核。

# LOW

## L-1. UAT §2 残留孤儿表头（双 4-A 模板头并存）

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:76-77`（旧表头“命令原文…”两行悬空）→ `:78` 注记 → `:80-81` 真表头。
- **事实**：整改编辑后旧表头未删，渲染为一个空表 + 一个真表；人工可辨，机器解析“4-A 表”会得到两张表。
- **复现思路**：读取 UAT `:74-87`。
- **处置**：删除 `:76-77` 两行孤儿表头即可。

---

# 门与负控专项结论

- **负控输入 / 对照输入**：J06 结构内副本 validator 独立重跑 **rc=0**；root 件 `journey_id="G8-7"` schema 红 = 已登记卡文缺陷（`03-breakpoints.md:20`，阻断级、主 session 裁定），非本卡代码问题。负控①② 整改轮存档与授权窗口语义同值；`structural-remediate` 的 `主表行数=0` 工具错误有诚实注记 + `structural-remediate2` 更正为 13，原值未改写。
- **未被拦下的输入**：vault 根 `learning_events.jsonl`（+3 事件）仍在四目录+state 快照面外——已按 r4 建议统一写为 scoped gate 局限（`manifest.json:544`），不因口径补正而变成门绿豁免。
- **门未覆盖的路径**：`.obsidian/`、`.trash/` 同上已在 known_limitations 点名。outside=2 保持**开放项**（触发者未确认；`03-breakpoints.md:30` / manifest `:543` / UAT 收口待办均未标闭合）——合规。
- **白名单宽度**：授权档与整改档 gate 输出逐字节一致，零放宽、零追加。
- **沙箱假红**：`PermissionError [Errno 1] sock.bind` 红如实保留 + 免沙箱权威档 32 红并存，未用“重跑就绿”掩盖。
- **时点说明（非缺陷）**：整改轮裁判跑在 `484ccba0` 工作树（`skill-versions-remediate:1` 自证 HEAD）；其后 `cb4187c1`/`67796927` 仅增 `_bmad-output` 文档（territory 档 + 本轮零代码卡双重证实），裁判结论对 FINAL 仍有效。

# 结论

r4 的 11 项中 **10 项闭合**，M-3 **部分闭合**（终版 35→48 计数漂移，新 M-1）；无新 BLOCKER/HIGH。因存在新 MEDIUM，**不写“本卡可交主 session”**；最小收口 = 改三处计数（35→48，可加时点注）+ 删 UAT 孤儿表头，做 docs-only 新 commit 后按新 HEAD 走 r6 轻量闭合复核即可。用户侧四项开放（③带锚点复跑 / ⑥截图 / 思维导图触发者确认 / 签字）维持原状，不属本轮判罚范围。
