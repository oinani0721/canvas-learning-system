# 独立复核请求 — CARD-NEO4J-REPLAY-CENSUS（Neo4j 离线暂存链零代码普查）

## 一 背景与最小读取面

本卡是**零代码纯只读 census**：普查 Canvas Learning System 后端在 Neo4j 离线期间产生的「暂存链」（fallback / dead-letter 文件），逐链落档「写侧 / 读侧 / 回灌 / 有界」四列，产出「接通 vs 退役」处置表，交给同车道后续两张卡落地（T6-B 接通面、T6-C 有界与可观测面）。本卡**不改任何 `.py`**，产物只有 `_bmad-output/` 下的文档与证据。

仓库根: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
绑定: `HEAD` = `081004834e37b1b0253cf81dc7b44e784646c934`（`08100483`），代码树与 `B14_BASE` 逐字节相同。

**最小读取面（请只读这些，不必通读全仓）**：

1. 本卡 census 文档全文：`_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md`
2. 本卡证据目录：`_bmad-output/审查/evidence-neo4j-replay-census/*.txt`（每条判据的实跑输出）
3. 被普查的生产文件（只读，核对 file:line 是否与 census 所述一致）：
   - `backend/app/services/fallback_sync_service.py`
   - `backend/app/services/memory_service.py`（重点 `:460-510`、`:2680-2800`）
   - `backend/app/services/episode_worker.py`（重点 `:80-120`、`:200-270`、`:300-315`、`:630-660`）
   - `backend/app/services/canvas_service.py`（重点 `:90-100`、`:120-165`、`:260-270`、`:355-370`、`:495-520`）
   - `backend/app/services/agent_service.py`（重点 `:95-140`）
   - `backend/app/core/failure_counters.py`、`backend/app/core/failed_writes_constants.py`
   - `backend/app/api/v1/endpoints/traces.py`、`backend/app/api/v1/endpoints/tips.py`（重点 `:615-640`）
   - `backend/app/clients/neo4j_client.py`（重点 `:50-60`、`:470-490`）、`backend/app/clients/neo4j_edge_client.py`（重点 `:38-50`、`:755-830`）
   - `backend/app/main.py`（重点 `:380-408`）
   - `backend/app/config.py`（重点 `:470-515`、`:920-945`）
   - `backend/.env`（`:85`）、`backend/.env.example`（`:226`）

## 二 作者自述（请独立核对，不要默认为真）

1. **七条暂存链的四列事实**（census §一 总表 + §二）。卡文原列 5 条，本卡全域普查后补为 7 条（新增 `failed_dual_writes.jsonl`、`learning_memories.json`）。
2. **两个重放器零非测试调用方**：`MemoryService.recover_failed_writes`（`memory_service.py:2687`）与 `FallbackSyncService.sync_all_fallbacks`（`fallback_sync_service.py:53`）及其工厂 `get_fallback_sync_service`（`:656`）在**非测试代码中零调用**。判据用「调用形态枚举 + 全命中逐条归类 + 验伪锚」，非计数（census §三）。
3. **`FallbackSyncService` 在生产从不被实例化**：唯一非测试实例化点 `:661` 在工厂内部，而工厂零调用；`domains/canvas/gateway.py:19` 的 import 是纯 re-export 且该模块零 import 者。
4. **启动回填门行号更正**：`main.py` 的 `if _worker_graphiti is not None:` 实测在 `:387`（勘探稿写 `:386`，`:386` 是其上一行的取值语句），`backfill_vault` 调用 `:392`，跳过日志 `:404`。
5. **双写开关二态**：`config.py:477-479` field `default=False`；`backend/.env:85` 为注释态（变量未设）；`backend/.env.example:226` 为生效态 `=true`。结论：本机=关、按 example 部署=开，且**运行时无第三态**（census §五.1 逐候选排查）。
6. **「接通」不等于「有界」**：`sync_all_fallbacks:64-75` 在 Neo4j 不可用时两道早退直接 `skipped`，因此离线期（坟场增长期）回灌器一行都不清理；census 据此判定 T6-C 的有界必须落在写侧（census §六.1 c1）。

## 三 请按重要性排序回答的问题

1. **census 是否漏了某条暂存链，或漏了某条链的回灌调用路径**？特别是未被「调用形态枚举」覆盖的写法（例如经由别名、动态属性访问、字符串驱动的调度、任务注册表、依赖注入容器、模块级副作用等途径触达 `sync_all_fallbacks` / `recover_failed_writes` 的路径）。判据 19 的全域扫描只覆盖三种路径拼接形态（`/ "data" / "x.jsonl"` 拼接、`_APP_DATA_DIR /` 拼接、`"data/x.jsonl"` 字面量），请指出是否存在这三种形态之外的暂存文件定义方式。
2. **孤儿判据的枚举形态 `(await |\.)<name>\(` 是否覆盖所有调用写法**？请作为对照输入检查：有没有不带 `await`、不带 `.` 前缀的调用形态被漏掉（census §三 已补跑裸形态 / 直接实例化 / 反射 / 字符串四种补充枚举，请判断补充是否充分）。
3. **双写开关二态结论是否站得住**？`canvas_service` 六处消费点写的是 `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True)`（回落默认 `True`），与 field `default=False` 方向相反。census 判定回落分支永不触发（字段已定义 ⇒ 属性恒存在）。请检查是否存在某条 `Settings` 装载路径（例如 `reload_settings` 的 overrides、测试注入、`extra="ignore"` 的交互）使得该属性缺席或取值与 census 结论不同。
4. **处置表「接通 vs 退役」的依据是否完整**？接通后的幂等与有界由 T6-B/T6-C 保证（不在本卡范围），但 census 是否漏登记了前置风险？特别是：链 7 `learning_memories.json` 被判「接通回灌但禁止轮转」（理由：它同时是 `LearningMemoryClient` 的运行时查询源）——这个判断是否成立？若成立，T6-C 一刀切轮转是否确实会造成运行时数据丢失？
5. **启动门行号更正 `:386 → :387` 是否影响 T6-B 的地盘声明**？设计稿声明 T6-B「只改 `:386-404`」，census 建议校正为 `:387-404`。请判断按 `:387-404` 划界是否会漏掉必须一起改的行（例如 `:386` 的 `_worker_graphiti` 取值语句、或 `:405-406` 的 `except` 块）。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 一句话结论
- `file:line`（指向实际代码或 census 文档的具体位置）
- 一句复现思路（说明用什么只读命令能看到同样的事实）

若某项自述经核对为真，请明确写「核对通过」并给出你据以核对的 `file:line`，不要沉默略过。

## 五 边界

- **只读**：请勿修改任何文件，勿执行写操作。
- **不连库**：本卡不连 Neo4j（7691/7687/7692）、不连 LanceDB、不起应用 lifespan。请勿尝试。
- **不评落地设计**：T6-B 的接通实现方式、T6-C 的有界实现方式均不在本卡范围，请勿对它们的设计方案提出实现建议；只评 census 的**事实正确性与完整性**。
- **不评完整回灌幂等性**：那是 T6-B 的端到端验证面。
- 本卡为零代码卡，请不要提出需要改动 `.py` 的整改要求；若发现 census 事实错误，请指出错误本身，由作者修正文档。
