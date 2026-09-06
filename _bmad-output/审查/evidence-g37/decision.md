# CARD-G3-7 裁定表 — 四条遗留 FSRS 写路径

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-G3-7]`。车道 `card-y9-maingoal`，勘探基点 HEAD `7c9a6706`（Y9-A 末 commit，主干预合 `03ac8bf8`）。
> 裁定依据：`docs/fsrs-truth-source-d0-revision.md` §一 三条铁律 + §五 T1/T3/T5；卡文 `Y9-B.md` §一 (a)(d)。
> **裁定口径声明**：本表的「保留/隔离」不是偏好选择，每条都由下面列出的**实测反对证据**逼出；无反对证据的地方一律选了收敛动作。

## 〇 共同前提：消费方 census（`git grep`，2026-09-06 于 HEAD `7c9a6706`）

四条路径在**产品侧三个目录全部零消费方**：

| 目录 | ① `/review/record` | ② `/review/fsrs-state` | ③ mastery grade | ④ `save_card_state` |
|---|---|---|---|---|
| `frontend/obsidian-plugin/src`（live 插件） | 0 | 0 | 0 | 0 |
| `canvas-vault/.claude/skills` | 0 | 0 | 0 | 0 |
| `scripts/` | 0 | 0 | 0 | 0 |
| `backend/app` | 见下逐条 | 见下逐条 | 见下逐条 | **0**（只有定义） |

旁证（非本卡地盘，只读登记）：
- `_archive/canvas-progress-tracker/obsidian-plugin/src/services/FSRSStateQueryService.ts:135` 是 `/review/fsrs-state` 的**唯一**插件调用方，位于 `_archive/` = 已归档，不是 live 插件。
- `CURRENT_TASK.md:148` 已把「`/review/record` + `fsrs-state` + history」登记为 **Tier B 退役移交（未做）**。

⇒ 三条 HTTP 路径当前**没有任何在线消费方**。这不改变本卡的裁定动作（禁用/删除属于退役卡范围，且会撞 (d)），但它是「为什么现在只做降级标注而不做行为下线」的关键事实：**收益侧为零，破坏面非零**。

---

## ① `PUT /review/record` → `review_service.py:1087 _save_card_states(pending=...)`

- **链路**：`review.py:1029 @put("/record")` → `:1034 record_review_result` → `:1085` → `review_service.py:977 record_review_result` → `:1087`。
- **census（backend/app）**：`review.py:1085` 唯一调用点；`review.py:1032` operation_id；无其他。
- **裁定：改造（保留写，降格为投影缓存写；加真相源标注 + 分歧信号）**
- **理由**：
  1. `PUT` 是写方法，更新投影缓存本身不违反 T5（T5 禁的是「投影层回写**状态**」，这里回写的对象已被本卡显式降格为缓存，不再自称状态）。
  2. **不覆盖 `next_review_date`**——这是本卡最容易被误判为「①没照 T1 做」的地方，故理由前置：T1 约束的是「**读取**某节点当前该何时复习」。`record_review_result` 返回的 `next_review_date` 是「本次评分算出来的排期」，而此刻 frontmatter 里还是**旧** due（vault 侧 `quiz-answer × fsrs_bridge` 的写是另一条链、另一时刻）。若在此用 frontmatter 覆盖，会把刚算出的新排期换成陈旧值——那不是诚实，是**用 T1 的名义制造错误**。
  3. 诚实义务由信号承担：响应加性字段 `truth_source="projection-cache"`；frontmatter 侧存在且与本次结果分歧时 `degraded_reason` 追加 `truth_source_divergence` + `logger.warning`，让调用方知道**真相源尚未被本次调用更新**，须走 vault 写链。
- **本次落地**：`:1087` 写点加「非 FSRS 调度真相源」注释；service 返回值加 `truth_source` / 分歧时扩 `degraded_reason`；`review.py:1117-1126` 加性转发；`schemas.py::RecordReviewResponse` 加 `truth_source` 可选字段。

## ② `GET /review/fsrs-state/{concept_id}` → `review_service.py:2189` auto-create 写盘

- **链路**：`review.py:1365 @get("/fsrs-state/{concept_id}")` → `:1376 get_fsrs_state` → `:1413` → `review_service.py:2137 get_fsrs_state` → `:2185-2192` auto-create + `_save_card_states`。
- **census（backend/app）**：`review.py:1413` 唯一调用点。产品侧 0（见 §〇）。
- **裁定：保留 + 门锁边界（GET 写盘仅在「该 concept 在 frontmatter 侧无真相源」时放行）**
- **门锁边界的精确定义**：
  > 当 `_read_frontmatter_fsrs(concept_id)` 判定该 concept **有** frontmatter 真相源（`.md` 存在且 `fsrs_due` 非空）时，`get_fsrs_state` **一律不写盘、不改 `_card_states`**，并以 frontmatter 的 due 覆盖返回值、标 `truth_source="frontmatter"`；分歧时 `degraded_reason="truth_source_divergence"`。
  > 只有在**无**真相源（`.md` 不存在，或存在但无 `fsrs_due`）时，才沿用既有 auto-create + 写盘语义，标 `truth_source="projection-cache"`。
- **为什么不是「下线」——实测反对证据**（这条是被 (d) 逼出的，如实声明）：
  1. `backend/tests/unit/test_fsrs_state_query.py:376-394 test_auto_create_reports_persisted_flag_honestly` 断言 auto-create 后 `persisted is True`（即**确实写了盘**）；
  2. 同文件 `:397-403 test_existing_card_reports_persisted_true` 注释明写「auto-create + 落盘」并依赖它；
  3. 同文件 `:408-423 test_cached_after_failed_write_stays_not_persisted` 依赖写**尝试**发生。
  ⇒ 任何形态的「下线写盘」都会打红这三条，直接违反卡文 (d)「既有六套件本卡引入红 = 0」。**在 (d) 不放宽的前提下，「保留 + 门锁」是唯一可落地解**。
- **仍如实登记的缺陷**：GET 在无真相源分支上**依然写盘**，仍是 HTTP safe-method 语义违规。本卡把它**收窄**到「frontmatter 说不出话时」，未消除。彻底下线须与既有测试同批改，归退役卡。

## ③ mastery grade → `mastery_engine.py:276-310 _fsrs_update`

- **链路**：`mastery.py:265 @post("/mastery/{concept_id}/grade")` → `:266 record_grade` → `mastery_engine.py:175 self._fsrs_update(concept, grade)` → `:276-310` 写 `concept.fsrs_stability / fsrs_difficulty / fsrs_state / fsrs_reps / fsrs_lapses / fsrs_card_data`。**落点是 MasteryStore（Neo4j EntityNode），不经 `fsrs_card_states.json`** —— 这是与 ①②④ 完全独立的第三份 FSRS 推进。
- **census（backend/app）**：`mastery_engine.py:175` 唯一写调用；下游读方 `mastery_tools.py:187-190 / :274-277`（MCP）、`signal_registry.py:148`、`event_handlers.py:102-103 / :332-333`、`mastery_engine.py:326 / :651`。产品侧 0。
- **裁定：隔离（加性标注非真相源 + 登记立卡收敛）**
- **理由（实测反对证据）**：
  1. 「改造」= 改 MasteryStore 写侧，须连 Neo4j 7691 验证 —— 卡文硬边界「7691/7687 只读」，本卡不可做；
  2. 「下线」会摘掉 mastery 域的 FSRS 信号，而它有 **5 处在线读方**（上列），破坏面远超本卡；
  3. 该域的 FSRS 服务于**掌握度信号**（`signal_registry`）而非复习排期投影，与 frontmatter 调度面不直接重叠——但它**仍是独立推进的 FSRS 状态**，隔离不等于无害。
- **本次落地**：仅在 `mastery_engine.py:276 _fsrs_update` docstring 加「非 FSRS 调度真相源（D0 修订 T1，G3-7）」标注 + 交接指针，**零行为改动**。按卡文地盘条款「`mastery.py` / `mastery_engine.py` 仅在裁定表声明时」——**在此声明**：本卡 diff 含 `backend/app/services/mastery_engine.py`，改动限注释。

## ④ `review_service.py:2086 save_card_state` → `:2119`（backend/app 零调用方）

- **census**：`backend/app` 内 `git grep 'save_card_state('` **只命中定义**（`:2086`）；产品侧 0。
- **裁定：隔离（保留定义 + 标注非真相源 + 登记 G-PIPE 待退役）**
- **为什么不是「下线」——实测反对证据**：
  1. `backend/tests/unit/test_review_service_fsrs.py:619` 与 `:640` **两条既有测试直接调用它** ⇒ 删除必红 ⇒ 撞 (d)；
  2. `openspec/specs/concept-identity/spec.md:14` 与 `:39`（**主 spec**，非 archive）按名引用它的行为契约 ⇒ 删除会让主 spec 悬空，且 `openspec/specs/` 不在本卡地盘。
- **如实声明**：仓外（未纳入本仓的调用方）调用**不可证**，本裁定只覆盖本仓四个目录的 census 面。

---

## 结果汇总

| # | 写点 | 裁定 | 行为是否改变 |
|---|---|---|---|
| ① | `review_service.py:1087`（PUT /record） | **改造** | 是（加性信号；不改 `next_review_date`） |
| ② | `review_service.py:2189`（GET /fsrs-state auto-create） | **保留 + 门锁边界** | 是（有 frontmatter 真相源时不再写盘 + due 以 frontmatter 为准） |
| ③ | `mastery_engine.py:276 _fsrs_update` | **隔离** | 否（仅注释） |
| ④ | `review_service.py:2119 save_card_state` | **隔离** | 否（仅注释） |

**统一动作（全部四点）**：`fsrs_card_states.json` 及其内存镜像 `_card_states` 在代码里显式降格为「非 FSRS 调度真相源」（投影/缓存），锚点见 `review_service.py:109 / :315 / :335 / _save_card_states / :1087 / :2119 / :2189` 与 `mastery_engine.py:276`。
