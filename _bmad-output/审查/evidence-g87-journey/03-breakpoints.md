# 03 — 断点归属表（CARD-G8-7）

> 列：环节 / 现象 / 证据文件 / 归属切片·卡 / 是否阻断旅程
> 「已知前置断点」= 走查开始前已存在的状态（非本卡引入），登记不修（走查窗口冻结部署 / 别卡 owner）。

## A. 已知前置断点（走查前存在，非本卡引入）

| 环节 | 现象 | 证据文件 | 归属切片·卡 | 是否阻断旅程 |
|---|---|---|---|---|
| ② / ④ | live 缺 `board-recap/scripts/recap_exam_build.py`（第十批 `5322043f` 修过的加载点在 live 不可达） | `01-skill-versions.md` 第 4 行（DIFF, live MISSING） | G5 / 部署链（非本卡修） | 否（第二刀「阶段回顾→派生检验白板」在 live 不可达；本卡走单板 `/board-recap` + `/start-exam-board`，不经该脚本） |
| ② ③ ④ ⑤ | dev↔live skill 版本差异 **8 处**（`ai-linked-doc` / `board-recap` SKILL+recap_scan / `quiz-answer` / `start-exam-board` 等） | `01-skill-versions.md` 主表 | 部署冻结（非缺陷；总账 v2 :1007） | 否（旅程跑 live 副本；差异只双列登记，不「顺手同步」） |
| ① ② | live 未部署 `board-split` / `clear-inbox` 两目录（只有 `scripts/`，无 SKILL.md） | `01-skill-versions.md` 结论段 | G5-7 / G5-10 面（本批其它车道） | 否（本卡六环节不经该两 skill） |
| ③ | `search_notes` 延伸路径 `RAG_EXTENDED_MODE=1`（退役 LangGraph 多源管道）0/5 通道存活 | ⚠️ **读取面外主张，未纳入包内复核**（源自 `backend/app/mcp/tools/note_search_tools.py` 只读阅读；本卡不改该文件） | G4（RAG） | 否（默认 fast path LanceDB + BGE-M3 可用；本卡走默认） |

## B. 本卡运行期发现（新增）

| 环节 | 现象 | 证据文件 | 归属切片·卡 | 是否阻断旅程 |
|---|---|---|---|---|
| ① | **渲染态 callout（问题块）内拖选 → 插件读空选区、报「请先选中文本」**（Live Preview 块级 widget；无分型诊断、文案误导） | 本卡实测：用户两轮截图（放大件 `/tmp/g87-crop-callout.png`）+ 源码 `main.js:2525-2533` + GLM 报告 §B.1 候选① | **G5（插件面）** | 否（改选普通正文即绕过；如实登记） |
| （证据包元级）manifest | 卡文 (c)④ / §二.5 要求 `validate_release_manifest.py _bmad-output/审查/evidence-g87-journey/manifest.json` → rc=0 且 `journey_id: "G8-7"`；**实测不可同时成立**：schema 的 `journey_id` 模式为 `^J(0[1-9]|10)$`（`"G8-7"` 被结构层直接拒），且语义规则 S6 要求 manifest 位于 `<rc>/journeys/<Jxx>/manifest.json`（证据目录根不满足） | `manifest-red-*.txt` / `manifest-green-*.txt` / `manifest-validator-conflict-*.txt` | **本卡（卡文缺陷）** —— 断点登记，主 session 裁定 | **是**（指定裁判红 = 阻断级，协议 §1） |
| ①/② | **板上批注不进 board manifest**：`原白板/*.md` 的属性邀请你批注（板内 info callout + 插件白名单含 `原白板/`），但 `board_manifest_service.py` 的 `list_node_files()` 只列 `节点/`、`tips` 只从节点 frontmatter 读（:642）⇒ 板上批注不会出现在 board-recap 的「批注共 N 条 / 未闭环 N 条」对账行（它另走 `POST /api/v1/tips` 出题数据面通道） | 本卡写卡实测（`board_manifest_service.py:236-260/:642`；live `原白板/CS 61B.md` 无 `tips`、两成员节点有）；走查 ① 因此改为节点批注 | **G5（Skills/报告口径）** 待主 session 裁定是否登记为 UX 口径差 | 否（口径调整即绕过；本卡如实登记） |
| （环境）test harness | `pytest tests/unit` 目录级开工基线 **32 红 ⊆ 33 基线**，唯一差 = 已知 flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`（本批手册 §零.2 明示按噪声处理） | `unit-open-*.txt` / `open.nodeids` / `base.nodeids` | 非本卡（既有红基线） | 否 |

| ①（环境） | **Obsidian 1.13.7 更新包已实际运行**（app-support asar 覆盖，plist 仍显示 1.12.7）× **Underwater 1.6.61（4/18）仍用 RGB 三元组** ⇒ callout 底色/边框/图标色静默失效（1.13 要求 `--callout-color` 为完整颜色；包内实测 0 处 `rgb(var())` 消费） | 日志 `Loaded updated app package …obsidian-1.13.7.asar`（8/22 起）；1.13.7 asar sha `a52a7daf…`；像素实测底色差=0；上游 7/31「Fixed callout colors」 | **主题维护面（非本卡、非 CLS 代码）**；用户环境修复另办 | 是（影响用户观感；与走查证据链无关） |
| ⑤ | **衰减 Beta 低证据+久闲置下答错 μ 反升**（`update()` 逐坐标 FLOOR 抬 a；`effective()` 无 FLOOR）→ 掌握度方向与作答质量相反 | GLM 独立复算（`glm53-pi-review-20260920T154846.md` §1-2）+ 落盘 3.2196/0.02；源 `decay_beta.py:36-40,98-114` | **G3（FSRS/掌握度）** 待开卡 | 否（旅程可走；判据不得用方向） |
| 全轮 | **零静默改写门漏扫 vault 根 `learning_events.jsonl`**（不在快照面 ⇒ false-negative 覆盖缺口，非 outside≠0） | GLM §1-4；快照命令 `04-journey-log.md`；ledger 新增 3 事件 | **本卡判据**（车道上报，主 session 裁定扩充扫描面） | 是（审计门覆盖不全） |
| ④ | **HARD-ISO 上下文前提被同会话 ③ 诊断污染**（同会话先读节点正文再出题；产物无泄漏） | pi 会话 L55/L57 vs L79；GLM §1-1 | **走查判据**（需拆 Artifact/Context 两档；严格复跑＝新会话） | 否（Artifact 可单独判） |
| ⑤ | **插件 `FrontmatterTipsSync` 为已知第二写者**（frontmatter 重序列化：ts 去引号 / grade_norm: 0 / self_confidence_norm 空） | GLM §1-3（第三条 callout_parse tips 为决定证据）；`frontend/obsidian-plugin/src/frontmatter-tips-sync.ts:47-85` | **G5（插件）× 本卡判据**（归因登记） | 否 |
| ③ | **fast 路径无关键词/稀有串召回通道**：dense 阈值先滤 → FTS 仅对已召回候选做确认；纯稀有中文短语/标记串（UUID 类）在 chunk 缺语义锚点时结构性 0 命中（`all_filtered_below_threshold`, top_score 0.0） | T-3.3：pi 会话 L110-127 五轮探针（`代理` 6/6 fts 正常；`scheduler…`→该节点 0.877；`走查批注+锚点`→该节点 0.839 fts=true；纯 marker 串 0） | **G4（RAG/检索）** 新缺陷 | 是（③ 判据未达成；不阻断④⑤） |
| 全轮 | **卡文 (m) 出现面判据此前未落档**（2026-09-20 19:37 补跑）：形态红/意图绿 —— 命中超范围者为缺陷登记+索引说明+第三方报告（非写入命令）；两文件 dev==live、本卡零 diff | `fsrs-decay-scope-20260920T193722.txt` | **本卡判据**（补跑闭合；形态过宽交主 session 裁定） | 否（意图判据绿） |
| （证据包元级） | **§二.1 第 0 分钟判据未单独落档**（2026-09-20 19:37 重建）：HEAD/分支/BASE=33 三条可重建且符预期；pyright 不适用；docker ps 有 T-1 等价证据；当时 status 与 §〇 sed 深核未落档 | `minute0-reconstruct-20260920T193730.txt` | **本卡判据**（覆盖缺口如实登记，交主 session 裁定是否补跑） | 否（关键值可重建） |
| 全轮 | **授权窗口零静默改写门 `outside=2`（开放项）**：`outputs/思维导图-CS 61B.excalidraw.md` 与 `outputs/思维导图-特征值与特征向量.excalidraw.md`（14:05:52 同秒）不在白名单内 | `silent-rewrite-gate-authorized-20260920T180031.txt`；写者机制 = T-3.2（自研 Excalidraw v3「一次性导出」器，`_bmad-output/研究/2026-08-15-思维导图-Excalidraw-需求与迭代记录.md`） | **本卡**（车道上报；**触发者待用户一句确认**）；⚠️ 不放宽白名单 | 否（已归因；未确认前按开放项跟踪） |
> ⚠️ **历史层（未授权段，2026-09-19）**：本节 = 用户当日裁定「不授权真实走查」时的 SKIP 登记，**已被 2026-09-20 授权走查段取代**（终态 = `manifest.json` assertions / `04-journey-log.md` T-1.x–T-3.5 / UAT 4-C）。保留仅为时间线完整，**不得引作当前状态**；两段并存不构成「授权/不授权双叙述」冲突（整改轮 M-4 标记）。

## C. 授权侧六环节（SKIP 登记 · 历史段）

> **用户 2026-09-19 当次裁定：不授权真实走查。** 按卡文 (d)「未授权即每环节 `not_run` + SKIP 登记」处理；不在本证据包中充当环节证据，不用 fixture / 旧存档（D5 / J06）顶替。

| 环节 | 状态 | 原因 | 归属 |
|---|---|---|---|
| ① vault 准备 | `not_run` | 未授权写 live vault | 授权侧（用户当次） |
| ② `/board-recap` | `not_run` | 同上 | 授权侧 |
| ③ `search_notes` | `not_run` | 同上 | 授权侧 |
| ④ `/start-exam-board` | `not_run` | 同上 | 授权侧 |
| ⑤ `/quiz-answer` | `not_run` | 同上 | 授权侧 |
| ⑥ 次日总览页 | `not_run` | 同上（只读 GET 可行，但因六环节链断，未单独跑） | 授权侧 |

- 未授权分支下已跑：`02-live-snapshot-before.txt` + `04-live-snapshot-after.txt`（只读），零静默改写门 `changed=0 outside=0`（`silent-rewrite-gate-*.txt`）。
- 六环节若后续授权走查，按 `00-README.md` 顺序执行并在本区逐条补登；届时若改动 evidence/manifest ⇒ 按卡文 §一(n) 再送 Codex 一轮绑新 HEAD。
