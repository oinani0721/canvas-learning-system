# CARD-G3-7 独立复核（round-1）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal`

本卡把「FSRS 复习调度状态」的多真相源问题收敛为单一真相源。项目已有的书面裁定（`docs/fsrs-truth-source-d0-revision.md`）规定：节点 Markdown 文件 frontmatter 里的 `fsrs_due` 是唯一的「当前该何时复习」真相源；后端任何 JSON/数据库状态都只是投影；两者不一致时以 frontmatter 为准，并须以 degraded 信号如实透出（禁止谎报成功）。

**请只读下列文件与行段，不要扩展到其他目录：**

| 文件 | 行段 | 内容 |
|---|---|---|
| `backend/app/services/review_service.py` | 105-230 | 存储层锚点降格注释 + 新增 `_whole_second_utc` / `_read_frontmatter_fsrs` |
| 同上 | 440-540 | `_load_card_states` / `_save_card_states` |
| 同上 | 1095-1320 | `record_review_result`（写路径 ①） |
| 同上 | 2244-2300 | `save_card_state`（写路径 ④） |
| 同上 | 2301-2508 | `get_fsrs_state`（写路径 ②，含新门锁） |
| `backend/app/api/v1/endpoints/review.py` | 1028-1145 | `PUT /review/record` 端点 |
| 同上 | 1374-1476 | `GET /review/fsrs-state/{concept_id}` 端点 |
| `backend/app/models/schemas.py` | 938-1075 | `FSRSStateQueryResponse` / `RecordReviewResponse` |
| `backend/app/services/mastery_engine.py` | 276-300 | `_fsrs_update`（写路径 ③，本卡只加注释） |
| `_bmad-output/审查/evidence-g37/decision.md` | 全文 | 四写点裁定表 + 消费方 census |
| `backend/tests/regression/test_g3_7_truth_source.py` | 全文 | 本卡新增回归门（12 用例） |

参考（可读，本卡未改）：`canvas-vault/.claude/scripts/fsrs_bridge.py:149-160`、`scripts/daily_review_pick.py:340-345`、`backend/app/services/frontmatter_signals.py:33-41`、`backend/tests/regression/test_debt8_fsrs_fallback_honest.py:171-211`。

## 二 作者自述（请独立核对，不要默认采信）

1. **四个写点的裁定**：① `record_review_result` = 改造（保留写、加真相源标注与分歧信号、**不覆盖** `next_review_date`）；② `get_fsrs_state` auto-create = 保留 + 门锁（该 concept 有 frontmatter 真相源时不写盘、不推进内存缓存，且 due 以 frontmatter 为准）；③ mastery grade = 隔离（仅注释）；④ `save_card_state` = 隔离（仅注释）。理由与消费方 census 见 `decision.md`。作者称 census 覆盖 `backend/app`、`frontend/obsidian-plugin/src`、`canvas-vault/.claude/skills`、`scripts/` 四个目录。
2. **degraded 信号语义**：作者称 `persisted`（投影是否落盘）与 `truth_source`（这个 concept 的调度归谁管）正交，互不冒充；门锁拦下的「未持久化」用独立 reason `truth_source_gate_no_projection_write` 描述，以免谎报一次并不存在的写失败。
3. **分歧注入以 frontmatter 为准**：作者称读侧（`get_fsrs_state`）在分歧时返回 frontmatter 的 due 并标 `truth_source_divergence`；写侧（`record_review_result`）**故意不**覆盖本次算出的排期，只报信号，理由是 T1 约束的是「读取当前态」而该字段是本次计算结果。
4. **解析口径**：作者称新增的 frontmatter reader 采用与 `fsrs_bridge.py:151` / `daily_review_pick.py:341` 逐字相同的纯 stdlib 正则，不走 PyYAML，理由是 PyYAML 会把未加引号的 `fsrs_due` 解析成 datetime，与投影链的 UTC-Z 字符串口径不同源。
5. **分歧比较归一到整秒**：作者称 frontmatter 的 fsrs_due 按其写侧实现恒为整秒 UTC-Z 而投影 due 带微秒，逐字节比较会让分歧信号恒真。

## 三 请回答的问题（按重要性排序）

1. **裁定是否覆盖全部写点、census 是否完整**：`review_service.py` / `mastery_engine.py` 的读取面内，是否还有本裁定表未列出的、会推进 FSRS 调度状态的写点？`save_card_state`（作者称 `backend/app` 零调用方）与 mastery 侧的裁定理由是否站得住？census 的四个目录是否足以支撑「零在线消费方」这一说法，还是有作者未覆盖的调用面？
2. **信号是否可能假成功**：`persisted` / `reason` / `truth_source` / `degraded_reason` 四者在各分支上的取值组合，是否存在某条路径会让调用方误以为「真相源已更新」或「写成功了」？特别关注：门锁分支的 `persisted=False`、多个 degraded 原因的逗号拼接、以及 `get_fsrs_state` 里 `truth_source="frontmatter"` 而 `due` 为 null 的组合。
3. **新测试的分歧注入是否经生产 reader**：`test_g3_7_truth_source.py` 的种子是否真的走了生产解析路径，而不是用替身自证？其中哪些断言在被测逻辑被移除后仍会通过（即哪些断言不承重）？特别请评估 `test_gate_blocks_write_when_truth_source_exists` 与 `test_gate_allows_write_when_no_truth_source` 这一对负例/正控是否足以区分「门锁生效」与「这条路径本来就写不动」。
4. **GET 门锁是否有未覆盖路径**：进入 `get_fsrs_state` 后，是否存在某种输入或状态组合，使得该 concept 明明有 frontmatter 真相源，却仍然推进了内存缓存或写了盘？（例如缓存命中分支、异常分支、并发路径。）
5. **OpenAPI 变化是否纯加性**：`backend/openapi.json` 的改动是否只有新增可选字段与时间戳，没有删字段、没有新增必填、没有改类型？

## 四 输出格式

按严重度分级（BLOCKER / HIGH / MEDIUM / LOW），每条给出：`文件:行号` + 一句话结论 + 判断依据（引用你实际读到的代码或文档原文）。若某条作者自述与代码不符，请直接指出不符之处。最后给一段总评，说明哪些自述你**核实成立**、哪些**不成立**、哪些**读取面内无法判定**。

## 五 边界

- 不评 G3-5 的 `{vault_id, concept_id}` 键化、不评 G3-9 的跨视图对账 —— 两者是后续卡的范围。
- 不要求也不需要提供任何攻击性内容；本次复核只针对上述读取面内的正确性、诚实性与门的有效性。
- 不必运行测试；如需佐证请引用源码行。
