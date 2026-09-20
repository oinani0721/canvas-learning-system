# 00 — CARD-G8-7 两白板全旅程走查 · 证据包 README

> **卡**：[BATCH-2026-09-18-第十五批 / CARD-G8-7] · 车道 `card-p3-deploy`（分支 `card/p3-deploy`）· 起点 HEAD = `9d4f7bf0`（P3-B CARD-DEBT-10 末 commit）
> **目的**：用**当前已上线能力**真实走一遍「原白板 → 检验白板」全旅程，逐环节留命令 / 产物 sha256 / 截图 / skill 版本 hash，供 G1-8 备料。
> **边界**：不做 ChatGPT 终审（唯一 owner G1-8）；不做跨日复习旅程（G6-13 J07）；不部署 / 不同步 skills（走查窗口冻结）。
> **prior art**：本卡前，端到端旅程证据仅 D5 单环节盲测（`_bmad-output/审查/d5-evidence-2026-08-27/`）与 J06 底稿（`_bmad-output/审查/2026-09-14-G3-9-J06-evidence-draft.md`），二者均非 E2E（不在本证据包中充当本卡环节证据，仅作已知前置引用）。

## 六环节表（用户入口 → 预期产物 → 只读判据 → 断点归属切片候选）

| # | 环节 | 用户入口（vault 内会话） | 预期产物路径 | 只读判据（存在 + sha256 + 截图） | 断点归属切片候选 |
|---|---|---|---|---|---|
| ① | vault 准备（现 vault 新材料） | 在 Obsidian 手工操作 | `原白板/<选定板>.md`（+1 批注）或 `节点/<新材料>.md`（新增） | 文件存在且在 `02-live-snapshot-before.txt` 之外；截图 `shot-1-<ts>.png` | G2（多 vault）/ G6（UI） |
| ② | `/board-recap <板>` | Claudian 侧栏直输 | `outputs/回顾-<板名>-<日期>.md`（+ `.recap-manifest-*.json` + `.recap-scan-*.json` 共三写面） | 新文件存在 + sha256；报告头有无 `FALLBACK` 如实记；截图 `shot-2-<ts>.png` | G5（Skills）/ G4（RAG·Graphiti） |
| ③ | 检索 `search_notes` | Claudian 经 MCP 调用（`mcp__canvas-learning-mcp__search_notes`） | `search-<ts>.json`（返回体保存） | 返回体条目须命中环节①新材料的**完整 vault 相对路径 + 内容 sha256 前 16 位**（⛔ 不接受仅同名/同标题字符串命中，防旧材料顶替）；Claudian 输出截图 `shot-3-<ts>.png` | G4（RAG） |
| ④ | `/start-exam-board from <板>` | Claudian 侧栏直输 | `检验白板/<板>-<yyyy-mm-dd-hhmm>.md`（frontmatter `type: exam_board`） | 新文件存在 + `type: exam_board`；截图 `shot-4-<ts>.png` | G5（Skills）/ G3（FSRS 选点） |
| ⑤ | `/quiz-answer` | 用户手答后输入 | 被答节点 md frontmatter `mastery_score`/`mastery_a`/`mastery_b`（+ `fsrs_*`）；检验白板 md 分数 | 跑前跑后 `grep -n -e mastery_ -e fsrs_ <节点>` 两份；若仅 `mastery_*` 变化而无 `fsrs_*`，如实登记「本地掌握度更新，**不证明** `fsrs_bridge` 调度」；截图 `shot-5-<ts>.png` | G3（FSRS） |
| ⑥ | 次日总览页 | 浏览器打开 `http://127.0.0.1:8011/api/v1/review/overview/page`（**只读 GET**） | `overview-page-<ts>.html` + `overview-curl-<ts>.txt` | `http=200` + 截图 `shot-6-<ts>.png` | G6（UI）/ G3（FSRS 桶） |

## 口径（卡文 (c)① / (d) 明写）

- **「vault 准备」= 现 vault 新材料**：在本批 live vault 的 **6 块原白板**（递归与分治 / 特征值与特征向量 / 线性代数 / CS 61B / CS / CS188 lecture 2）中选 **1 板（默认 `CS 61B`，用户可改）**，由用户在 Obsidian 新增 **1 个节点 md** 或 **1 条批注**。⛔ **不跑** `scripts/deploy-vault.sh`（本批零写者，缺陷登记 C1-02）。
- **环节⑥只读打开总览页**：⛔ **不手动触发** `scripts/daily_review_run.py`（会写 state + 推 Bark，与 :05 档争抢；P5 唯一写者）。跨日「刚答的板进入次日清单」归 **G6-13 J07**。
- **产品口径默认**：出题板默认 `CS 61B`、只答 **1** 道题、任何 env 默认（含 `DEAD_LETTER_STORE_FULL_BODY`）不动。
- **授权前提**：真实旅程写 live vault 只能由**用户当次授权**（标签页说「G8-7 授权走查」）并在 **vault 内会话**执行（readonly guard R2 拦车道 session）。**未授权即每环节 `not_run` + SKIP 登记**，不得用 fixture / 旧存档顶替。
- **走查窗口冻结部署**：车道零 cp / 零改 live / 零改 skills；8 处 dev↔live 差异只双列登记（见 `01-skill-versions.md`）。

## 证据包文件索引

| 文件 | 内容 |
|---|---|
| `00-README.md` | 本文件（六环节表 + 口径） |
| `00-prefix-red-*.txt` | 先红：建目录前 `evidence-g87-journey` / `CARD-G8-7` 均 0 命中 + 验伪锚 1 |
| `01-skill-versions.md` | skill 版本表，dev 树 13 文件 ↔ live 副本逐文件 sha256（DIFF=8）+ fsrs_bridge/decay_beta 两行 |
| `02-live-snapshot-before.txt` | live 跑前快照（四目录 + 主仓 daily-review state，只读，49 行） |
| `manifest.json` | 借 `docs/release-evidence/manifest.schema.json` 字段的证据登记（⛔ 不进 `docs/release-evidence/`，P10 唯一写者） |
| `03-breakpoints.md` | 断点归属表 |
| `04-live-snapshot-after.txt` | 跑后只读收尾快照（**未授权也做**，与 before 同口径；未授权时预期与 before 相同） |
| `04-journey-log.md` | 授权走查时：六环节命令原文 + 执行者 + 产物路径（**未授权不产出**） |
| `05-g18-material.md` | G1-8 备料：截图清单 + 审查任务书素材要点（不写终审结论） |
