> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-4
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat /tmp/codex-prompt-CARD-G8-7-r4-resolved.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r4.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r4.stderr </dev/null`
> 　（prompt = `codex-prompt-CARD-G8-7-r4.md`；`$PREV`/`$FINAL_SHA` 已解析为 `d9d64ea1` / `484ccba0`，解析副本 `/tmp/codex-prompt-CARD-G8-7-r4-resolved.md`）
> 审查绑定: `d9d64ea1..484ccba0`（FINAL = 审工作区 HEAD；本文件在整改轮 commit 前落盘，整改 commit 见 r5 绑定）
> 会话头自证（抄 .stderr 三行，行号括注；stderr 不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

# CARD-G8-7 r4 复核（绑最终 HEAD）

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-G8-7]`  
> **模型 / reasoning**：`glm-5.3` / `max`  
> **codex 实测**：`codex-cli 0.153.3`  
> **绑定**：PREV = `d9d64ea1e2fc7d0d8b64ee276e9374ba1bcd2cc0`；FINAL = `484ccba07b39cf8427b87992176898d1f66eae3b`；当前 HEAD 实测 = FINAL。  
> **会话头自证**：`codex-review-CARD-G8-7-r4.stderr:1-2` = stdin / `OpenAI Codex v0.153.3`；`:4-5` = worktree `card-p3-deploy` / model `glm-5.3`；`:9` = `reasoning effort: max`。  
> **边界遵守**：只读；未连 7691/7687；不评 G1-8 终审、G6-13 跨日、8 处 skill 差异本身对错、Excalidraw 导出器设计。

## 总裁决

**PARTIAL / 不建议按 r4 直接闭档。**

证据包本身有独立价值，不是空壳：六环节真实尝试、失败与待补状态大多如实登记，manifest 35 件 artifact 哈希全匹配，live 产物仍与 18:07 台账一致，J06 结构内副本校验 PASS。但 **r4 送审模板本身仍含 `$PREV` / `$FINAL_SHA` 未替换**，且 UAT 仍残留 `outside=0` 旧口径；这两点分别影响复审可复现性和核心门结果呈现。

计数：**BLOCKER 1 / HIGH 1 / MEDIUM 6 / LOW 2**。

---

## 独立验证结果

- 零代码：`d9d64ea1..484ccba0` 排除 `_bmad-output` 后 diff 为空；FINAL 的 parent 正是 PREV。
- manifest artifact 完整性：当前 `manifest.json` 35/35 件 `sha256 + bytes` 全部复算匹配。
- validator：
  - J06 结构内副本：`validate_release_manifest.py .../b15-g8-7/journeys/J06/manifest.json` → **PASS / rc=0**。
  - 根件 `journey_id="G8-7"` → expected FAIL：不匹配 `^J(0[1-9]|10)$`。
- 快照差集独立重算：before/after **changed=11**，与 `silent-rewrite-gate-authorized-20260920T180031.txt:1-16` 一致；两个 mindmap 为仅有的白名单外输出。
- live 产物复核：`artifacts-sha-authorized-20260920T180728.txt` 中 12 件 live vault / state 产物当前仍 12/12 哈希匹配。
- skill 面：当前 dev 13 文件、live 10 文件逐文件哈希复算，**DIFF=8**，与 `01-skill-versions.md` 一致。
- signoff：`manifest.json:439-442` 为 pending；UAT 用户体验与签字位未勾选，符合“仅用户勾选后填”的声明。

---

## 作者自述逐条裁决

| # | 作者自述 | 裁决 |
|---|---|---|
| 1 | pi、vault 内会话完成六环节；③待重跑、④ Context FAIL、⑥车道侧 GET 200 | **部分证实**。六环节确实真实尝试并有产物/事件支撑；但不能概括为全通过。`manifest.json:141-180` 如实登记 ①pass / ②pass / ③fail / ④fail(Artifact pass, Context fail) / ⑤pass / ⑥fail(车道侧 pass)。 |
| 2 | gate `changed=11 / outside=2`；2件 mindmap 为自研 Excalidraw v3 一次性导出，触发者待确认；其余9件在声明面 | **证实，但触发者仍开放**。差集独立重算一致；设计记录 `2026-08-15-思维导图-Excalidraw-需求与迭代记录.md:31,94` 支持“一次性导出、不回读”语义。白名单不是宽泛放行整个 `outputs/`，否则这两个 mindmap 不会被标为 outside。 |
| 3 | `FrontmatterTipsSync` 为已知第二写者，重序列化 frontmatter | **部分证实**。字节差异与代码路径强证实；但 GLM 报告自己也声明未捕获 OS 级 write trace，不能升格为已观测进程身份。 |
| 4 | vault 根 `learning_events.jsonl` 不在快照面，窗口 +3 事件 | **证实**。ledger 当前第 23-25 行正是 `callout_ingested / exam_created / answer_scored`；这是门未覆盖路径，不是 outside 计数。 |
| 5 | `decay_beta` 答错 μ 反升、pi MCP 工具名不兼容均为另案登记 | **证实**。`glm53-pi-review-20260920T154846.md:31` 有完整复算；`:54` 登记 pi MCP 工具名差异。 |
| 6 | skill DIFF=8、E2、signoff pending | **证实**。当前 dev/live 哈希复算仍为 8 处差异；`manifest.json:443` 为 `E2`，`:439-442` pending。 |

---

# BLOCKER

## B-1. r4 送审模板未绑定最终 SHA， prescribed command 会把占位符原样发给审查者

- **位置**：`_bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r4.md:3-9,30`
- **事实**：最终 commit 中的 r4 prompt 仍写 `$PREV` / `$FINAL_SHA`；而命令 `:4` 是直接 `cat` 该文件，不会替换文件正文中的 shell 占位符。
- **影响**：这不是“绑最终 HEAD”的自包含送审输入。即使本次会话由外部消息补上了 d9d64ea1/484ccba0，归档 prompt 本身仍无法确定性复现同一审查范围。
- **复现思路**：`rg '\$PREV|\$FINAL_SHA' _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r4.md`；再按 `:4` 原命令运行，审查者收到的是字面 `$PREV..$FINAL_SHA`。
- **处置**：不能用事后编辑未归档 r4 输出来“补绑”。应做新的 docs-only commit 替换为实际 SHA；因 FINAL SHA 改变，需按新 HEAD 另跑 r5/下一轮绑定复审。

---

# HIGH

## H-1. UAT 证据区仍写 `outside=0`，与授权窗口核心门结果 `outside=2` 直接冲突

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:84`；对照 `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-authorized-20260920T180031.txt:13-16` 和 `UAT...:148`
- **事实**：UAT `:84` 仍说“差集 ⊆ 声明写入面，`outside=0`”；权威 gate 与 UAT 4-C 均为 `changed=11 / outside=2`。
- **影响**：这是核心审计门的假绿残留；读者若只看 §2 会得到错误结论。
- **复现思路**：并排读取 UAT `:84` 与 gate `:13-16` / UAT `:148`。
- **处置**：把 `:84` 改成授权窗口实际 `outside=2`，并指向“2件 mindmap、写者机制已知、触发者待确认”的开放项。

---

# MEDIUM

## M-1. 收口文档仍保留“进行中 / 待填”的模板面，未同步终版结果

- **位置**：`_bmad-output/审查/evidence-g87-journey/04-journey-log.md:26-37`；`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:73-82`
- **事实**：journey log 的 T1..T6 主表仍写“状态：进行中 / 待登”；UAT 4-A 证据表仍全为“待填”。后续 T-3.4/T-3.5、manifest 与 UAT 4-C 已有终版信息，但这些模板面没有回填。
- **复现思路**：读取 `04-journey-log.md:26-37` 和 UAT `:73-82`，再对照 `manifest.json:139-182`。
- **处置**：至少加“已由 manifest / UAT 4-C 终版取代”的显式注记，避免双真相源。

## M-2. UAT ③ 的期望路径仍是旧口径 `原白板/CS 61B.md`

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:47-50`；正确口径在同文件 `:155`
- **事实**：前文仍要求结果指向原白板；后文已更正为 `节点/csm-tutoring-unit-credit.md`。这也是此前检索判据假阴性的组成部分。
- **复现思路**：并排读取 UAT `:49` 与 `:155`。
- **处置**：把 §1 ③ 的期望路径同步为节点路径，或标注为历史模板已被 4-C 取代。

## M-3. UAT 记录 manifest artifacts=31，当前 manifest 实为 35

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:149`；当前 artifacts 范围为 `_bmad-output/审查/evidence-g87-journey/manifest.json:188-434`
- **事实**：我逐条计数并复算哈希，当前 manifest artifacts 为 35 件且全部匹配。UAT 的 31 是 T-3.4 时点数，未包含后续四件承重裁判输出。
- **复现思路**：`jq '.artifacts | length' manifest.json`，再对 UAT `:149`。
- **处置**：UAT 4-C 更新为 35，或标明 31 是中间时点。

## M-4. `03-breakpoints.md` 保留前一日“不授权 → 六环节 SKIP”终局段，缺少历史隔离标记

- **位置**：`_bmad-output/审查/evidence-g87-journey/03-breakpoints.md:30-44`
- **事实**：该段仍写“用户 2026-09-19 当次裁定：不授权真实走查”和六环节 `not_run`；这是前一日状态。当前 2026-09-20 授权段由 UAT/manifest/journey log 承载，但本文件标题未写“历史未授权段，已被 09-20 授权段 superseded”。
- **复现思路**：直接读取 `03-breakpoints.md:30-44`，再对照 UAT `:4-7` 与 manifest `provenance/assertions`。
- **处置**：给 §C 加显著历史层标记；否则同一证据包内存在授权/不授权双叙述。

## M-5. ⑤ 的终版登记字段仍低于 GLM 建议的最小前后值集合

- **位置**：`_bmad-output/审查/evidence-g87-journey/manifest.json:169-174`；建议标准在 `glm53-pi-review-20260920T154846.md:107-114`
- **事实**：manifest 登记了 `mastery_score 0.01→0.02`、final `a/b`、attempt、`fsrs_*`、calibration 追加和 ledger 事件，足以证明发生了本地更新；但没有完整登记 `mastery_a / mastery_b` 的 before→after、`last_examined` 前值、`calibration_log[-1].event_id`。这些散落在 GLM/pi 摘录中，不是 assertion 主字段。
- **复现思路**：对齐 `manifest.json:173` 与 GLM `:109-114` 的字段清单。
- **处置**：若 ⑤ 要作为可复验判据，补一张 before/after 字段表；若只作旅程证据，则显式降级为“更新发生证明，非完整状态迁移审计”。

## M-6. `outside=2` 的开放触发者没有进入 `03-breakpoints.md` 断点归属表

- **位置**：`_bmad-output/审查/evidence-g87-journey/03-breakpoints.md:15-29`；归因叙述在 `04-journey-log.md:134-138`
- **事实**：mindmap 写者机制和“触发者待用户确认”只存在于 journey log / manifest / UAT，`03-breakpoints.md` B 表没有对应行。相比 ledger 假阴性已有 `:26`，这个开放项缺少同级别追踪。
- **复现思路**：在 `03-breakpoints.md` 中搜索 `思维导图 / outside=2 / 触发者`，应为 0 命中。
- **处置**：加一行“授权窗口 outside=2，写者机制已知、触发者待确认，不放宽白名单”。

## M-7. manifest `execution.finished_at` 早于终版承重裁判 artifacts

- **位置**：`_bmad-output/审查/evidence-g87-journey/manifest.json:31-32`；终版裁判叙述 `04-journey-log.md:164-171`，对应 artifacts 在 `manifest.json:407-433`
- **事实**：execution 结束时间写 18:06:19，但 manifest 归档了 18:15-18:16 的 manifest-red / negctl / skill 第三跑输出。可以解释为“旅程结束时间”而非“证据包最终归档时间”，但字段名未区分。
- **复现思路**：比较 `execution.finished_at`、T-3.5 时间与 artifacts 文件名时间戳。
- **处置**：拆成 `journey_finished_at` 与 `evidence_pack_finalized_at`，或在 note 中明示 18:06 只覆盖六环境旅程。

---

# LOW

## L-1. 18:07 `artifacts-sha` 台账中的 03/04 文档哈希已被后续编辑 superseded

- **位置**：`_bmad-output/审查/evidence-g87-journey/artifacts-sha-authorized-20260920T180728.txt:22-23`
- **事实**：该台账记录的是 18:07 时点 `04-journey-log.md` / `03-breakpoints.md` 哈希；两文件 18:16 又更新，最终哈希在 `manifest.json:211-215` 与 `:400-404`。manifest 最终 35/35 匹配，所以不是产物漂移，但内部台账有时序差。
- **复现思路**：对 `:22-23` 所列哈希重新 `shasum -a 256` 两文件，再比较 manifest。
- **处置**：给台账加“18:07 时点，03/04 后续以 manifest final hash 为准”，或终版重跑。

## L-2. manifest 对授权快照行数的描述不准

- **位置**：`_bmad-output/审查/evidence-g87-journey/manifest.json:323-334`
- **事实**：实际 `wc -l`：before authorized = 50 行，after authorized = 52 行；manifest 分别写 51 / 51。哈希与字节数正确，仅描述性行数错。
- **复现思路**：`wc -l 02-live-snapshot-before-authorized.txt 04-live-snapshot-after-authorized.txt`。
- **处置**：改为“before 49 条目+1 header / after 51 条目+1 header”或直接写总行数 50/52。

---

# 门与负控专项结论

- **负控输入 / 对照输入**：manifest J06 副本 validator PASS；根件因 `journey_id="G8-7"` expected FAIL。signoff 负控语义与 `manifest.schema.json:666-690` 一致，approved 必须 user/at。
- **未被拦下的输入**：vault 根 `learning_events.jsonl` 的 +3 事件不会进入四目录+state diff；这是已登记的 false-negative 覆盖缺口，不能当门绿豁免。
- **门未覆盖的路径**：除 ledger 外，`.obsidian/` 也不在扫描面。`04-journey-log.md:92-100` 记录了授权主题修复写入 `.obsidian/themes/**`，UAT `:122` 已声明该局限；但 manifest known limitation 仅点名 ledger。建议统一写成“scoped gate 不覆盖 vault 根、`.obsidian/`、`.trash/`”。
- **白名单宽度**：未见“整目录 outputs 全放行”的问题；两个 mindmap 虽在 `outputs/` 仍被判 outside，说明存在即时实例化/精确匹配。
- **部署冻结归属**：`03-breakpoints.md:10-12` 将 8 处 skill 差异和 live 缺文件归为部署冻结/别的 owner，未误记为本卡代码缺陷，符合总账 v2 `:1007` 的冻结裁定。

# 结论

证据链的实质内容是有效且诚实的：真实 live 产物、失败状态、开放签字位、skill 版本、hash 和独立报告均有独立价值。当前不能闭档的主要原因不是旅程“装绿”，而是 **r4 归档 prompt 未实际绑 SHA** 与 **UAT/gate 文档残留旧结果**。修复这两类登记面后，需要产生新最终 commit 并重新送审绑定。
