# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / round-1）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`，审查 SHA = **`cd1b5ae9`**（本卡代码 commit），上一张卡末 commit = `310eef31`（T6-A，零代码）。

本卡要解决的问题：`FallbackSyncService.sync_all_fallbacks`（`backend/app/services/fallback_sync_service.py:53`）实现完整，但**生产侧零调用方** —— Neo4j 离线时四条降级暂存链持续写入，却没有任何回灌消费者，数据事实上丢失。本卡把它接进两处真实路径，并把启动回填门的离线分支从「静默跳过」改为「登记待回灌」。

**最小读取面（只读这些，不要全仓扫）**：

1. 本卡改动面：`git diff 310eef31 cd1b5ae9 -- . ':(exclude)_bmad-output'`
2. `backend/app/services/fallback_sync_service.py:1-110`（`sync_all_fallbacks` 全貌 + 新增的 `count_fallback_backlog`）
3. `backend/app/main.py:378-450`（回填门 try/if/else/except 全段，改后行号）
4. `backend/app/api/v1/endpoints/traces.py` 新增的 POST 端点全段
5. `backend/app/security.py:64-166`（`require_internal_api_key` 完整五分支矩阵：503 配置缺失 / 503 DEBUG 无 bypass / 403 缺 header / 403 key 不匹配 / 允许。403 分支在 :135 之后、DEBUG bypass 尾在 :110 之后，截到 :110 会漏）
6. 新测试全文：`backend/tests/integration/test_neo4j_replay_wire_t6b.py`
7. T6-A 普查：`_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md`

## ② 作者自述（请独立核对，不要采信）

1. 接线后 `sync_all_fallbacks` 的产品调用方从 0 到 2（`main.py` 启动恢复触发 + `traces.py` 管理端点），孤儿门判据：`git grep -nF '.sync_all_fallbacks()' -- backend/app | grep -v '/tests/' | grep -vF 'Replaced by'`，改前 0 / 改后 2。
2. 管理端点的鉴权与 `/system/*` 逐字同口径：端点级 `dependencies=[Depends(require_internal_api_key)]`，`security.py` 一字未改（只 import）。
3. 离线分支只做「一条日志 + 一个只读计数」，不做有界/轮转、不往 `/traces` 加积压字段（那是下一张卡 T6-C 的面）。
4. 端到端门真连 7692 测试容器，不打桩 sync 路径（DD-03 禁 mock）；三条暂存文件与 checkpoint 全部 monkeypatch 到 `tmp_path`。
5. `main.py` 的两个 hunk 都是纯插入（`@@ -402,0 +403,22 @@` 与 `@@ -404,0 +427,17 @@`），既有 import 块与外层 `except` 段一字未动。
6. `count_fallback_backlog` 的 `pending_total` 刻意只累加 `failed_writes` 与 `canvas_events`：`learning_memories.json` 回灌成功后不轮转，其条目数是本地记录总数而非待回灌数。

## ③ 问题（按重要性排序）

⓪ **端到端门是否真证明了「回灌后图内可查」，而不是夹具自己写进去的图？** 负控输入②（摘掉两处 `sync_all_fallbacks()` 调用、端点改为返回形状相同但不回灌的 stats）实测让承重用例红在 `:302` 的图查询断言、端点仍返回 200 —— 这个负控输入是否足以排除「门其实在验夹具」？门未覆盖的路径在哪里？

① **幂等断言是否真挡得住重复回灌产生重复数据？** 作者的判断是：挡住重复的不是 Cypher MERGE，而是 `_sync_failed_writes` 成功后的 `_rotate_file`（文件搬走 ⇒ 第二轮无输入）——因为 `neo4j_client.record_score_history` 是 `CREATE (e:Episode {id: randomUUID()})`，同一条目真被重放两次会多出 Episode。请核这个判断是否成立；若成立，「第二次 `recovered == 0` + 门前缀节点数逐标签相同」这组断言是否足够，还是存在一条对照输入能让它假绿。

② **启动恢复触发放在回填门成功分支，是否有异常吞没或并发风险？** 作者加了内层 `try/except` 把回灌异常与外层 `:445` 的 backfill except 分开。请核：是否仍存在某类异常路径会让「回灌失败」在日志里表现为成功或表现为回填问题；以及 lifespan 期间 `get_fallback_sync_service()` 建单例是否与别处的单例装配次序冲突。

③ **管理端点返回 stats 是否泄漏敏感信息？** 返回的是 `sync_all_fallbacks` 的原样 dict。请核其中是否可能带出文件路径、条目内容或其他不该出现在鉴权端点响应里的东西（注意 `{"error": str(e)}` 那几支）。

④ **离线登记的只读计数是否会连 Neo4j 或读现网文件？** 作者的依据是 `Neo4jClient.__init__` 只存配置、`_driver=None`，连接要到 `initialize()` 才建。请核这条依据，以及 `count_fallback_backlog` 读的三个路径常量在生产进程里指向哪里。

⑤ **pyright 0 errors 是否靠 ignore 掩盖了真类型问题？** 本卡未新增任何 `# pyright: ignore`。请核新增代码的类型正确性（尤其 `replay.values()` 的 `isinstance(v, dict)` 收窄与 `_count_json_list` 的 `data.get` 分支）。

⑥ 三条鉴权用例挂 `gate_client` 的理由是否成立：正常态下鉴权在 handler 之前拒掉请求、端点体不执行；但负控输入①要拆的正是那层鉴权，拆掉后未被拦下的输入会落进端点体，用进程默认单例去连 `backend/.env` 里的 `bolt://localhost:7691`。挂上隔离夹具是否确实把这条路径堵住了。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略 —— 这些明确不在本卡范围。
- 不评 `backend/app/security.py` 本身的设计（别卡地盘，本卡只 import）。
- `backend/openapi.json` 未再生是刻意的（本卡 commit 不含它，由主 session 集成期统一再生），不必作为缺陷提出。
