# 独立复核请求 — CARD-G2-9 双 vault 数据隔离 canary

## 一 背景与最小读取面

本仓是一个 Tauri + FastAPI + Neo4j + LanceDB 的本地学习系统。它支持多个「vault」（知识库），
数据分散在三个存储：Neo4j 业务节点（按 `group_id` 属性隔离）、同一 Neo4j 库里由
`graphiti_core` 写入的节点（也按 `group_id`）、LanceDB 向量表（按**表名前缀**隔离）。

在本卡之前，跨 vault 隔离只有两处**单点单测**（LanceDB 表名前缀契约、写侧不回落默认组），
没有任何一处把三个存储串起来端到端验证过。本卡新增一个 canary 脚本补这一段。

请只读以下文件/行段，不必通读全仓：

| 路径 | 读什么 |
|---|---|
| `backend/scripts/g29_dual_vault_canary.py` | **全文**（本卡新增，1201 行，主要审查对象） |
| `backend/tests/regression/test_g29_dual_vault_fsrs_isolation.py` | **全文**（本卡新增，184 行） |
| `backend/tests/support/live_port_guard.py` | `:118`、`:145`、`:581-616`、`:865-918`、`:986-1053` |
| `backend/app/core/vault_scope.py` | `:596-620`（`read_scope_params`）、`:623-647`（`read_group_filter`）、`:650-681`（`group_in_read_scope`） |
| `backend/app/graphiti/group_id_compat.py` | `:64-87`、`:140-185` |
| `backend/lib/agentic_rag/clients/lancedb_client.py` | `:627-660`、`:762-792`、`:949-968`、`:3629-3694` |
| `backend/app/clients/neo4j_client.py` | `create_learning_relationship`（约 `:977-1037`）、`create_canvas_node_relationship`（约 `:1430-1460`） |
| `.claude/rules/cypher-read-contract.md` / `cypher-write-contract.md` | R1-R5 / W1-W5 的口径 |
| `_bmad-output/审查/evidence-g29/` | 本卡全部裁判输出（下方自述引用的数字都出自这里） |

## 二 作者自述（请独立核对，不要采信）

1. **装门**：脚本在 `from __future__` + stdlib import 之后、任何 `app.` / `lib.` /
   `neo4j` / `lancedb` / `graphiti_core` import **之前**调 `live_port_guard.install()`
   与 `register_final_accounting()`。理由：pytest 侧的端口门由 `conftest.py` 装，裸脚本
   不经 pytest，不装门则账本 `blocked` 恒 0 = 假绿。

2. **判据**（12 条，见 `run_canary` 的 `verdicts`）：A/B 两个 vault 用**完全相同**的
   资产标识（同 canvas 路径 / 同 node ID / 同 concept 名 / 同 user ID / 同 doc_id）
   顺序写入三存储，然后核对：计数 A==B>0、交叉 0 命中、A 的计数不因 B 写入而变、
   同名 Concept 在库里被拆成两个物理节点、删 A 后 B 计数等于**删之前记下的**那个数。

3. **交叉查询**三个存储各用各的形状：Neo4j 用生产的 `read_group_filter` 作用域过滤
   **叠加**「归属为对方」的条件；Graphiti 用 `get_by_group_ids` 并额外用生产的
   `group_in_read_scope` 数「返回了但不该被本作用域看见」的条数；LanceDB 把对方的
   物理表名当逻辑表名交给本方 client 的 `resolve_table_name` 去解析。

4. **负控**七条全部 rc=2，且每条都打印 `NEGCTL_REJECTED_BY` / `NEGCTL_REJECTED_SOURCE`
   标明被哪一层拒。其中 4 条由 `live_port_guard.assert_test_uri_not_blocked` 拒
   （含省略端口与 `:0` 两种会被驱动归一成 7687 的写法、以及 routing 多地址），
   3 条由脚本自己的 LanceDB 路径前置检查拒。

5. **验伪**：`--verify-judges` 注入 5 条已知会破坏隔离的变异，要求 `expect_red` 点名的
   判据当场变红，实测 5/5 KILLED；`(c)` 的两条 pytest 测试另有 3 条原地变异，3/3 KILLED
   且文件 sha 逐字节还原。

6. **一处首跑实测到的假绿面已修**：Cypher 的分组聚合在空输入下返回 0 行，导致计数
   dict 为空，而 `all(x > 0 for x in {}.values())` 与 `all(x == 0 ...)` **同时为真**。
   现在 facet 按固定键集补 0，另有 `_assert_shape` 形状门，变异 M4 钉住它。

7. **一条附带发现，登记移交、本卡不修**（硬边界禁改生产代码）：
   `lancedb_client.py:962-968` 的 `_cache_tables` 对 `db.table_names()` 的**全部**表跑
   `_check_and_fix_dimension_mismatch`，该集合含**别的 vault 前缀**的表。实测 vault A 的
   `initialize()` 删掉了 schema 与 A 的期望不符的 vault B 的表。

8. **本卡不改任何生产代码**：`git status --porcelain` 只有两个新文件 + 证据目录。

## 三 请按重要性排序回答的问题

1. **装门时机**：脚本第一段可执行代码到 `install()` 之间，有没有任何一条 import 会
   间接把 `uvloop` 或会发起出站连接的模块拉进进程？`install()` 的 uvloop 前置检查
   在本脚本的 import 顺序下是否真的有效？
2. **负控的判据是否绑定到了正确的那一层**：`NEGCTL_REJECTED_BY` 报告的来源，与实际
   抛出异常的代码位置是否一致？有没有哪条负控其实是被更早的某个检查（例如路径检查
   先于端口检查）拦下的，而报告却归因给了端口门？
3. **交叉查询是否真的覆盖了 Graphiti 面**，还是实质上只查了业务 Concept？
   `GraphitiFacet.count` 的 `outside_read_scope` 验伪锚在什么情况下会非 0，
   它是否可能是一条恒 0 的死判据？
4. **两次运行的等价判据**：`normalize()` 剥掉的 volatile 键集是否剥得过多，
   以致 diff 恒空是因为报告被剥成了空壳，而不是因为两次运行真的等价？
   保留下来的 228 行里，哪些是真正承重的内容？
5. **删 A 后 B 不变**：B 的计数是否确实在删 A **之前**先记录，还是某个路径上
   变成了「删后拿现在的 B 跟现在的 B 比」的自证？另外 `Neo4jFacet.delete` 刻意
   不删 User 节点（因为生产的 `MERGE (u:User {id})` 不带 group_id，A/B 共用同一个
   物理 User 节点）——这个取舍是否让判据变松了？
6. **验伪的 5 条变异是否足够**：有没有哪条判据是「怎么变都不会红」的恒真判据？
   `MUTATION_SPECS` 的 `expect_red` 有没有点错目标（红的是别的判据，目标判据其实没红）？

## 四 输出格式

请按 `BLOCKER / HIGH / MEDIUM / LOW` 分级列出发现，每条给出：
- 一句话结论
- 涉及的文件与行号
- 你据以判断的事实（读到的代码/证据文件里的哪一行）
- 建议的处置

若某一条你无法从给定读取面判断，请明说「读取面不足」，不要推测。
最后请给一句整体结论。

## 五 边界与已裁决事项

以下**不在**本次审查范围（已由主 session 裁决，不必提出）：
- 不做备份恢复半边、不做规模化 / 并发压测、不验证仓外调用方（MCP / Obsidian 插件）
- 不改任何生产代码：发现隔离缺陷 → 登记移交，不在本卡修
- `(c)` 的两条测试与 C1a 同源，两库跑在同一进程，只证投影与 state 隔离，
  **不证**生产「一库一进程」契约（后者由 wrapper shell 层保证）
- 只在测试容器 7692 与临时目录上跑，未验证现网 7691 上存量数据的隔离

请**不要**在回答中提供任何用于削弱隔离或端口防护的具体操作步骤；本次需要的是
「判据是否承重、结论是否被证据支撑」的评估。
