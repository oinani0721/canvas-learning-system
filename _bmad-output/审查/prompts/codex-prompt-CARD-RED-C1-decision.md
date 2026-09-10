# 独立裁定请求 — CARD-RED-C1 遗留的架构判断（非代码复核轮）

## 一 背景与最小读取面（只读这些，不要扩大扫描面）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`

**这不是一轮代码复核**（那两轮已做完，绑定 `343fce8e` / `401e792c`，BLOCKER/HIGH 均为 0）。本轮请你**独立裁定几个架构判断** —— 它们是上一张卡留下的、代码复核解答不了的开放问题。项目负责人是非技术背景，需要一个能直接据以决策的结论。

**一句话背景**：2026-03 的 Phase 2 重构宣称「用 `GraphitiEpisodeWorker` 取代了 JSON dual-write」，并据此（a）删掉了启动期的 JSON 兜底同步调用，（b）把配置项 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 的默认值从 `True` 翻成 `False` 并标 `[DEPRECATED]`。而 Story 38.4 当初把该默认值定为 `True` 的**书面理由**是「safe default for **Neo4j offline resilience**」（Neo4j 离线时的数据韧性）。

**请只读下列，逐项**：

1. 替代者本体：`backend/app/services/episode_worker.py`
2. 被孤立的回收服务：`backend/app/services/fallback_sync_service.py`（尤其文件头 `:1-40` 的三文件说明、`:54` `sync_all_fallbacks`、`:657` `get_fallback_sync_service`）
3. 活着的写侧之一：`backend/app/services/agent_service.py:5013-5110`（`_trigger_memory_write` 及其两个 except 分支里的 `_record_failed_write`）
4. 活着的写侧之二 + 另一条被孤立的回收：`backend/app/services/memory_service.py:495-520`（`_record_structured_outbox`）与 `:2679-2700`（`recover_failed_writes` 及其 deprecated docstring）
5. 启动期实际做了什么：`backend/app/main.py:82-260`（整个 lifespan）
6. 被翻转的配置项：`backend/app/config.py:470-482`
7. 用于区分「另一个 outbox」：`backend/app/services/event_bus.py:40-60`
8. 两个关键 commit：`git show 59586af1 --stat` 与 `git show 59586af1 -- backend/app/main.py`；`git show daa9fd37 -- backend/app/config.py`
9. 作者的证据整理：`_bmad-output/审查/evidence-red-c1/c1-verdicts.md` 的 **§2**（(e) 移交论证的 8 条源码事实）

## 二 作者自述，请独立核对（不要采信下列任何一句，请自己去证）

1. `failed_writes.jsonl` 的**写侧仍在生产热路径上**：`agent_service.py:5085/:5101` 在评分记忆写超时/异常时调 `_record_failed_write`；`memory_service.py:1662` 调 `_record_structured_outbox`。
2. 该文件的**两条回收路径都没有生产调用方**：`FallbackSyncService.sync_all_fallbacks` 与 `MemoryService.recover_failed_writes`，在 `backend/app` 下的命中只有自身定义与 docstring 文字引用。
3. **替代者未接管**：`episode_worker.py` 对 `failed_writes` / `FAILED_WRITES_FILE` / `outbox` 零引用。
4. **启动期那个「恢复」是另一个机制**：`main.py:216` 的 `event_bus.recover_outbox()` 恢复的是 `event_bus.py:49` 的 `data/outbox`（Story 5.7 EventBus Tier-2），与 `data/failed_writes.jsonl`（Story 38.6）不是同一文件、不是同一机制。
5. `59586af1` 的 commit message 自述删的是「Story 38.4/38.8 dual-write blocks」，但被删的 Story 38.8 块调用的 `sync_all_fallbacks` 同步的是**三个**文件，其中 `failed_writes.jsonl` 属 Story 38.6 评分失败回收，是另一条机制。

## 三 请按重要性排序回答下列问题

1. **核心问题：「Phase 2 用 GraphitiEpisodeWorker 取代了 JSON dual-write」这句话，在代码上到底覆盖了多少？**
   具体请回答：Story 38.4 当初写下的那个能力——**「Neo4j 离线/写失败时数据不丢」**——在当前代码里由**哪些**组件承担？逐个点名并给出 file:line。有没有哪一条路径是「有人写、没人读」的？请把完整的「写入 → 暂存 → 重放 → 落库」链路画出来，标明每一环的现状（活 / 断 / 被替代）。

2. **基于问题 1：作者把两条测试判为「数据面回归」并移交给另一张定性卡（而不是判为「契约演进」挂 xfail），这个判断成立吗？**
   如果你认为应该判「演进」，请说明是哪一环让「数据不丢」这个能力仍然完整。如果你认为「回归」成立，请评估**严重度**：在什么使用场景下会真的丢数据、丢什么数据、用户能不能察觉。

3. **基于问题 1：`daa9fd37` 把 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 从 `True` 翻成 `False` 的前提是否成立？**
   即：「已被 GraphitiEpisodeWorker 取代」这个理由，是否足以支撑关掉一个当初以「离线韧性」为由默认打开的开关？作者让 3 条测试跟着翻成断言 `is False`——这是「测试跟上了正确的契约」，还是「测试同意了一个有问题的默认值」？

4. **两个交接缺口的真实严重度**（作者已分别命名为 `CARD-EPW-COVERAGE` 与 `CARD-CONFIG-CLEANUP`，但两张卡尚未排期）：
   - `backend/tests/unit/test_episode_worker_retry.py` 的 5 个用例，相对被退役的旧重试/超时契约，覆盖缺口有多大？值不值得单独排一张卡？
   - `config.py:644/:650` 的 `MEMORY_RETRY_BASE_DELAY` / `MEMORY_RETRY_MAX_DELAY` 在 `backend/app` 下零消费方——这属于「无害的死配置」还是「有人以为它生效但其实不生效」的风险项？

5. **如果你只能给项目负责人提一条建议**（他不懂代码，只能决定「排不排卡、先做哪个」），那条建议是什么？

## 四 输出格式

请分两段输出：

**第一段：技术裁定**（给工程侧看）
每条结论给出 file:line 依据。问题 1 的链路图请用文字分级列出，不要省略「断」的那一环。严重度请用 高 / 中 / 低 并说明判据。

**第二段：给非技术负责人的一段话**（**这一段是本轮的主要交付物**）
用日常语言写 150–300 字，**不得出现**函数名、文件名、行号、commit 号、英文技术词。要讲清楚三件事：(a) 现在到底有没有东西在悄悄丢；(b) 如果有，会丢什么、什么时候能被发现；(c) 建议他现在做什么决定。可以用比喻，但比喻必须对应真实机制，不要为了通俗而说得比证据更严重或更轻。

## 五 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- **不要连数据库**（本仓有 Neo4j 7691/7687，本轮不涉及）。
- **不要重新复核已完成的两轮代码审查结论**（那两轮 BLOCKER/HIGH 已为 0）；本轮只裁定上述架构判断。
- 不要给出修复补丁；如需说明修法，一两句方向即可。
- 若某个判断你认为**证据不足以下结论**，请直接说「证据不足」并指出缺什么，不要为了给答案而下推测性结论。
