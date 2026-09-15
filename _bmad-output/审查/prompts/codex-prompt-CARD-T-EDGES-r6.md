# 独立复核请求 round-6 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**用户 2026-09-15 裁定放开 D-15 的 5 轮上限（「增加 codex 的审查轮次继续来修」），
故 round-5 之后本卡继续修，并突破了卡文 §三「只加 `AttributeError` 一个类型」去修 H1。**

**当前 HEAD = `8ff37ea5`**。本卡代码 commit 链：
`c9c73f57`(r1审) → `9764cceb`(r2审) → `c2e3d533`(r3审) → `caf8180e`(r4审)
→ `7c63c5eb`(r5审) → `5bffce4f`(r5 尾) → `8ff37ea5`(**本轮，H1 修复**)。

**最小读取面**：

1. `git --no-pager diff --no-color 5bffce4f 8ff37ea5 -- . ':(exclude)_bmad-output'`
   （**本轮全部改动**）
2. `backend/app/api/v1/endpoints/edges.py`：`:65-95`（`_NEO4J_WRITE_FAILURES` 常量与
   其说明）、`:86-219`（`_write_neo4j_triplet` 全文）、`:361-435`（handler）
3. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（817 行，16 格）
4. `backend/app/clients/neo4j_client.py`：`:57`（`RETRYABLE_EXCEPTIONS`）、
   `:351-433`（`initialize` / `_initialize_neo4j_driver` / `_fallback_to_json`）、
   `:536-641`（`run_query` + `_run_query_neo4j`）、
   **`:643-669`（`_run_query_json_fallback` 的关键词分发与 `else` 分支）** ← 本轮核心
5. 实跑存档 `_bmad-output/审查/evidence-t-edges/`（每份末行 `rc=`）：
   - `fallback-200-falsegreen-20260915T120325.txt`（**本轮最重的实证**，离线不连库）
   - `negctl-r6-newgates-20260915T120705.txt`（四条负控 + 跑前跑后 `shasum`）
   - `edges-r6-allgates-20260915T120944.txt`（16 格全绿，末行 pytest 真 rc）
   - `neo4j-exception-mro-20260914T230328.txt`（驱动异常 MRO 实测）

## ② 本轮改了什么，以及**为什么把前几轮的结论推翻了**

round-5 你把 H1 判为「缺陷成立但超出本卡改动面」。放开轮次后，车道做了一次 29-agent
的对抗复核（4 视角提案 → 合成裁决 → 3 路反驳 → 4 路残余扫描 → 逐条核验），
**三路反驳全部命中，并推翻了卡文与前五轮对 H1 的共同前提**：

> **H1 描述的伤害在活线路上根本不发生，发生的是更糟的那个。**
> `ServiceUnavailable` 走不到端点的 `except`：重试耗尽 → `RetryError`
> → `neo4j_client.py:628-629` `_fallback_to_json()` → `_run_query_json_fallback`
> 对 `CREATE (er:EdgeRationale …)` 三个关键词分支全不命中 ⇒ 落 `else:`
> `logger.warning("Unhandled query pattern"); return []` —— **不抛异常**
> ⇒ `run_query` 正常返回 `[]` ⇒ 旧代码**丢弃返回值**直接 `WriteStatus(success=True)`
> ⇒ **HTTP 200「双写全部成功」，而图库里什么都没有。**
> 而这条路是**本卡接通 `run_query` 才打通的**（改前恒死在 `AttributeError`，
> 走不到 `run_query`）。离线实证见第 5 项第一份存档。

于是本轮做了三件事（都在本卡两文件内）：

**(1) 收窄 `try` 到只包 `await neo4j.run_query(query, **params)` 那一行。**
之前 `try` 包整个函数体，于是 `get_neo4j_client()` 的配置缺陷、`episode_body` 的
f-string、`params` 里 14 次 `rationale.<field>` 取值、`to_physical_group_id` 的
punycode 路径，任一处的编程缺陷都会被记成「Neo4j 写失败」⇒ 每请求静默 207
⇒ 5xx 恒 0 ⇒ 前端 Outbox 把 207 当「部分成功已保留」继续投递 ⇒ 数据永久丢失。
收窄是「加宽类型集」能保持安全的**前提**。

**(2) 写确认。** Cypher 以 `RETURN er.record_id AS record_id` 收尾 ⇒ 真写成功恒返
**恰 1 行**；返回 0 行 = 没落盘 ⇒ `WriteStatus(success=False)` ⇒ 207，而不是 200。

**(3) `_NEO4J_WRITE_FAILURES` 模块级常量**（`edges.py:65-95`）：
原四类内建 + `AttributeError` + 对端四类（`ServiceUnavailable` / `SessionExpired` /
`TransientError` / `DatabaseError`）+ tenacity `RetryError`。
⛔ **刻意不收 `Neo4jError` / `ClientError` 族**：`ClientError` 的语义是「**你发来的
请求不对**」（`ParameterMissing` / `CypherSyntaxError` / `AuthError` / `ConstraintError`），
收进 207 等于把我方缺陷伪装成对端故障并永久静默。同理不收 `ConnectionPoolError`
（我方 session 泄漏）、`ConfigurationError` 族（部署坏了）。

**门从 3 道加到 16 格**（参数化）：
- `1c` 逐类钉住新收的 5 类 —— 类型清单**从生产模块读并逐类断言它确实在生产元组里**。
- `1d` **反向门**：被排除的 5 类（ClientError / AuthError / ConnectionPoolError /
  TypeError / KeyError）必须仍然 **500**。这是「加宽」的护栏。
- `1e` 写确认 + 对照组（返回 1 行必须仍 200，防「把 success 永远设 False」作弊）。
- `1f` 用**真的** `Neo4jClient(use_json_fallback=True)`（零网络）证明 1e 模拟的
  「返回 []」形态确实是真实客户端在 fallback 态下的行为。

**四条负控各自精确命中**（存档第 5 项第二份）：
NC-A 删掉新收 5 类 → 1c 红 5 格；NC-B 删掉写确认 → 1e/1f 红 2 格；
NC-C 把 `Neo4jError` 加进元组（泛化）→ 1d 的 ClientError/AuthError 红 2 格；
NC-D 删掉 `AttributeError` → 原降级门红 1 格。跑前跑后 `shasum -a 256` 逐字相同。

**两条如实登记移交（不在本卡可改面）**：
- `neo4j._exceptions.BoltError` 族与 packstream 解码层的裸 `ValueError` / `struct.error`
  仍会逃出元组而 500（驱动自己的连接池写的是 `except (Neo4jError, DriverError, BoltError)`，
  但 `BoltError` 在私有模块里，本卡不引私有 API）。
- `_write_lancedb` **从不真写**：`LanceDBClient.add_documents` 是 `async def`
  （`backend/lib/agentic_rag/clients/lancedb_client.py:3787`），而它用
  `await asyncio.to_thread(client.add_documents, ...)` 调 —— `to_thread` 只在线程里
  **调用**它拿到协程对象就返回，函数体一行不执行、也不抛异常 ⇒ 恒返
  `WriteStatus(success=True)` 而零写入。⇒「LanceDB 侧已经写成功的那一半」是不实陈述，
  两文件措辞已绕开。该函数是卡文 §三 明令禁碰的面。

## ③ 请按重要性排序回答的问题

- **①（本轮最重要）** 写确认判据是否可靠？具体问：**在真 Neo4j 上，
  `CREATE (…) RETURN er.record_id AS record_id` 经 `_run_query_neo4j`
  （`session.run` → `await result.data()`）之后，有没有任何一种「写其实成功了但
  返回 0 行」的情形**？若有，本判据会把成功误判成失败（假红，方向比假绿安全但仍是缺陷）。
- **②** 「收 `DatabaseError` / `TransientError` / `ServiceUnavailable` / `SessionExpired`
  / `RetryError`，排除 `ClientError` 族与 `ConnectionPoolError` / `ConfigurationError` 族」
  这条分界线，在语义与可枚举性上是否站得住？有没有你认为分错边的具体类？
- **③** 收窄 `try` 之后，`get_neo4j_client()` / `episode_body` / `params` 组装 /
  `to_physical_group_id` 的异常一律 500 —— 这是有意的。它有没有引入新的坏后果
  （例如某个原本被兜住的运维态现在会 500）？
- **④** 16 格门里还有没有**不可证伪**的断言（恒真 / 恒假）？本轮已按上一轮的同类发现
  改掉了真库门里两条不可证伪的「前置锚」，请核对改法是否到位。
- **⑤** `_NEO4J_WRITE_FAILURES` 提成模块级常量并被测试 `import` 做身份判据 ——
  这个耦合是否合适？有没有更好的钉法？
- **⑥** 本轮 diff 有没有引入回归？特别是 `_write_neo4j_triplet` 从「整体 try」改成
  「先取 client、再组装、最后窄 try」之后，控制流是否仍与原语义等价（除有意的那几处）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。
若某条你认为是「缺陷成立但超出本卡改动面」，请**明确标注**并给出建议级别。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评**：「生产是否应默认真连 Neo4j」这个产品裁定（已登记移交）。
  `_write_lancedb` 的**修法**不在本卡可改面（但它导致的**不实陈述**在本卡面内，欢迎指出）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
