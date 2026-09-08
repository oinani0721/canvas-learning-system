# D0 修订（正式版）— FSRS 真相源裁定：frontmatter = 唯一 current state，事件账 = 审计/幂等/重放来源

> **来源卡**: BATCH-2026-08-28-第五批 / CARD-G3-1（总账 v2 §g3-fsrs-rest；该文档位于编排 worktree `feature-obsidian-hybrid-dev` 的 `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`，不在本分支 HEAD 内——如实注明防引用悬空）
> **计划书锚点**: `_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md` L275（G3 条目 1 · D0 修订）、L397-400（§7 D2-A）
> **姊妹文档**: `docs/learning-events-schema-v1.md`（事件账 schema v1 冻结契约）
> **状态**: 2026-08-28 落文档生效。方向已在计划书 D0/D2-A 锁定，本文档为正式修订文本。

## 一、修订结论（三条铁律）

1. **frontmatter 是唯一 FSRS current state**。任何节点的当前调度状态（stability / difficulty / due / state / last_review / reps / lapses）以该节点 Markdown 文件的 frontmatter 为唯一真相源。所有视图（picker JSON、Dashboard、总览页、API）只准从 frontmatter 派生投影，不得自行维护可独立推进的状态。
2. **per-vault append-only 事件账是唯一的事件审计 / 幂等 / 重放来源**，且唯一实现收敛于既有 `backend/app/services/learning_event_log.py`（`<vault>/learning_events.jsonl`）及与其 schema 同构的 vault 侧 skill 静态写点。事件账**不是** current state：它回答"发生过什么、是否重复、能否重放重建"，不回答"现在该何时复习"。
3. **禁止后端维护第二套独立调度状态**（计划书 L275 明令）。禁止新建第二套事件账本、禁止出现第三种 `learning_events.jsonl` 直写实现（现网写点全清单见 schema 文档 §写点普查）。

## 二、依据（计划书原文）

- 计划书 L275（G3 条目 1）：
  > 决定并写入 D0 修订：推荐"frontmatter 为 current state；per-vault append-only event ledger 为事件审计与幂等来源"，禁止后端维护第二套独立调度状态。
- 计划书 L397-400（§7 D2 决策项，A 案采纳）：
  > **A（推荐）**：frontmatter 是唯一 current state；per-vault append-only ledger 只负责事件审计、幂等与重放，所有视图读统一 projection。
  > B：后端数据库为 current state，frontmatter 只做投影；事务较强，但削弱本地可读/可迁移性，并推翻现有 D0。

  本修订采纳 **D2-A**。B 案因推翻既有 D0、削弱 vault 本地可读/可迁移性而否决。

## 三、现实基线（2026-08-28 实证）

- 事件账实现已在生产：`backend/app/services/learning_event_log.py`（EVENT_VERSION=1，:31；9 类 EVENT_TYPES 白名单，:35-47；`<vault>/learning_events.jsonl` 落点，:52-56；`append_event()` event_id 幂等 + 永不抛异常，:59-105）。回归测试 `backend/tests/regression/test_learning_event_log.py` 在位。
- 现网账本（live vault `canvas-vault/learning_events.jsonl`，2026-08-28 快照 22 行）：全部行恰为 7 键 schema、时间戳全 timezone-aware、零重复 event_id、覆盖 6 类 event_type。
- 现网写点 8 个（backend 5 调用点 + vault 3 个 skill 静态写点），逐点 file:line 见 `docs/learning-events-schema-v1.md` §写点普查。

## 四、现存偏离登记（如实记录，本卡不修）

| 偏离 | 位置 | 处置 |
|---|---|---|
| 后端 `_card_states[concept_id]` 仍独立推进 FSRS 状态（第二调度真相源） | `backend/app/services/review_service.py`（G3-7 卡档案锚 :1017/:2025 区段） | **G3-7** 收敛为单一调度内核；本文档先行裁定其为**非真相源** |
| `fsrs_card_states.json` / MasteryStore 裸 `concept_id` 键近休眠链 | backend 存储层 | **G3-5**（键化）+ G3-7 裁定降级投影/缓存 |
| 旧 `next_review` 字段散布 10+ 后端文件 | neo4j_client / mastery_tools / schemas 等 | **G3-8** 对账迁移 |
| 复习评分链写序为"先 frontmatter 后事件"（非 write-ahead） | `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 评分链 | **G3-2** 改为先追加事件再更新 frontmatter |

> 本卡边界（总账 v2 G3-1）：只产文档 + schema + 校验脚本，**不动任何生产写路径与 learning_event_log 代码行为**。上表偏离由各归属卡收敛，本文档提供裁定依据。

> **锚点勘误（2026-09-06 追加，CARD-G3-7）**：上表第 1 行的档案锚「`:1017/:2025` 区段」写于 2026-08-28，主干前进后已失效。今日实测（车道 `card-y9-maingoal`，主干预合 `03ac8bf8`）对应位置为 **`review_service.py:1087`**（`record_review_result` → `_save_card_states`）与 **`review_service.py:2189`**（`get_fsrs_state` auto-create 写盘）。原句不改，以本注为准。另：G3-7 实测补全的写路径不止两条，完整四写点清单见 §六「G3-7 裁定结果」。

## 五、约束条款（对新代码即刻生效）

- **T1 唯一 current state**：读取"某节点当前该何时复习"必须最终溯源到 frontmatter；不得以数据库/JSON 状态文件为准。frontmatter 与任何后端状态不一致时，**以 frontmatter 为准**，分歧须以 degraded 信号如实透出（G3-7 落实测试）。
- **T2 唯一事件账**：学习事件的追加统一走 `learning_event_log.append_event()`（backend 侧）或已登记的 skill 静态写点模式（vault 侧，schema 同构、幂等约定相同）。
- **T3 禁第二套**：禁止新建平行账本文件、平行事件 schema、或对 `learning_events.jsonl` 的未登记直写。新增写点必须在 schema 文档 §写点普查登记。
- **T4 白名单对账**：新增 event_type 必须走 EVENT_TYPES 白名单对账评审（`learning_event_log.py:33-34` 既有约定），且只许加性扩展；评审记录落 schema 文档。
- **T5 投影只读派生**：一切复习视图/推送/排序均为 frontmatter 的确定性投影，投影层不得回写状态。

## 六、交接指针

- **G3-2**：复习写路径接入事件账（write-ahead 顺序 + 复习 payload 扩展键），按 schema 文档 §复习域扩展规则执行。
- **G3-3**：per-node CAS 与乱序事件隔离（乱序只进账本标 out_of_order，不改 current state）。
- **G3-7**：`/review/record`、`/fsrs-state` auto-create、mastery grade 三条遗留写路径收敛单一调度内核。

### G3-7 裁定结果（2026-09-06，BATCH-2026-09-05-第十二批）

裁定表全文（含逐条理由与消费方 census）：`_bmad-output/审查/evidence-g37/decision.md`。回归门：`backend/tests/regression/test_g3_7_truth_source.py`（**21 用例**，`grep -cE '^(async )?def test_|^    (async )?def test_'` 实测，2026-09-08；含 Codex 两轮复核抓到的 3 条 HIGH 的回归锁）。

实测写路径为**四条**（§六原文列的三条 + 一条 backend/app 零调用方的死路径）：

| # | 写点 | 裁定 | 落地 |
|---|---|---|---|
| ① | `review_service.py:1087`（`PUT /review/record`） | **改造** | 写点降格为投影缓存；API 加 `truth_source="projection-cache"`；分歧时 `degraded_reason` 追加 `truth_source_divergence`。**不覆盖** `next_review_date` —— T1 约束的是「读取当前态」，而该字段是本次评分算出的新排期，用 frontmatter 的旧值覆盖它是用 T1 的名义制造错误 |
| ② | `review_service.py:2189`（`GET /fsrs-state` auto-create） | **保留 + 门锁边界** | 该 concept 被判为「归 frontmatter 管」（`governed`：`.md` 有 `fsrs_due`，**或**文件/目录读不出来的 fail-closed 情形）时，本次调用不写盘、不推进 `_card_states`，`due` 以 frontmatter 为准。**两处未消除，措辞不得说成「一律」**（Codex r2 MEDIUM-2）：(a) 无真相源分支仍写盘（HTTP safe-method 违规被收窄未根治）；(b) 门锁判定在本次调用入口读一次，其后跨越 `await`，**若这期间 vault 侧刚写出 `fsrs_due`，本次仍会按旧判定推进投影**（TOCTOU 窗口，登记不修，理由见 decision.md） |
| ③ | `mastery_engine.py:276 _fsrs_update`（MasteryStore／Neo4j） | **隔离** | 仅加注释标非真相源。改造须写 Neo4j 7691（G3-7 硬边界禁连）；下线会摘掉 5 处在线读方的掌握度信号。**隔离不等于无害**：收敛卡落地前该域 FSRS 仍独立推进 |
| ④ | `save_card_state`（退役前主干实测 `review_service.py:2364`；此处原写的 `:2119` 是更早车道树的行号，已作废） | **已退役（CARD-G3-7-R2，第十三批）** | `backend/app` 零调用方，定义已删（DD-13：零调用方的投影写入口不留在生产代码里）。原按名引用它的两条单测（`tests/unit/test_review_service_fsrs.py:619/:640`）改指真实持久化通道 `_save_card_states`，G-FAKE-007 防复活锁覆盖面不变窄；主 spec `openspec/specs/concept-identity/spec.md` 的那条 Requirement 与实现**从未一致**（`_legacy_card_states` / `is_uuid_v4` 全仓 0 且 `git log -S` 空），处置与消费方 census 见 `_bmad-output/审查/evidence-g37r2/`。仓外调用仍不可证 |

**落实 T1 的关键实现**：`review_service._read_frontmatter_fsrs()` 是 backend 侧 frontmatter FSRS 真相源的**唯一**读入口（本卡之前 `backend/app` 对它零读取，这正是双真相源的物理成因）。

解析口径要同时对齐**两件事**，缺一不可（Codex r1 HIGH-2 证伪了只对齐前者的初版）：

1. **字段正则**与既有两个生产 reader（`canvas-vault/.claude/scripts/fsrs_bridge.py:151` / `scripts/daily_review_pick.py:341`）逐字相同的纯 stdlib 正则，**不走 PyYAML**（会把未加引号的 `fsrs_due` 解析成 `datetime`，与整条投影链的 UTC-Z 字符串口径不同源）；
2. **输入面**必须是**已切出的 frontmatter 块**，而不是整份 `.md` —— 两个生产 reader 收到的参数就是切好的 `fm`。初版把同一个正则作用在整份文件上，结果正文里顶格写的 `fsrs_due:`（最典型的就是讲解该字段怎么写的文档节点）会被当成权威 due 且毫无提示。块切分复用 `daily_review_pick.py::scan_nodes` 的正则（BOM/CRLF 容忍；无 frontmatter 时取空串）。

> ⚠️ **可复用的教训**：**口径 =（正则 + 输入面）**。「正则一字不差」听上去像铁证，但只证明了一半；下次再用「与生产同口径」作为论据时，必须把两半都验到。

**「找不到」与「看不见」必须分开**（Codex r1 HIGH-1 + r2 HIGH）：`Path.exists()` 会**自己吞掉 OSError 返回 False**，所以「确实没有这个节点」与「目录/文件不可读所以看不见」在路径解析的返回值里不可区分。本实现对这两态分别给出 `no_node_file`（放行）与 `node_lookup_unreadable` / `node_file_unreadable`（**fail-closed，拦**）。原则：**内容未知 ≠ 没有内容**；在真相源判定这条路径上，「不知道」必须按最保守的一侧处理。

**分歧比较归一到整秒**（`_whole_second_utc`）：frontmatter 按构造是整秒 UTC-Z（`fsrs_bridge` 的 `_whole_second()`），后端投影 due 带微秒；逐字节比较会让 `truth_source_divergence` **恒真**，那比没有信号更糟。

**T5 未完全落实（如实登记）**：`GET /fsrs-state` 在无真相源分支上仍回写投影状态，严格说仍是「投影层回写」。本卡把它收窄到 frontmatter 说不出话的场景，根治归退役卡。
