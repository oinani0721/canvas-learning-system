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
