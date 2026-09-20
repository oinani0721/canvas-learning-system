# 独立复核任务 round-2 — CARD-LANCE-DUALWRITE-NEVER-WRITES（BATCH-2026-09-18-第十五批 / 车道 P1）

## ① 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage`
基线 SHA：`9c4e7e82`　审查绑定 SHA：`74742100c62642e45e13780e77ea79c8e5716691`

本卡修两处生产缺陷 + 四件尾巴：

- **H2**：`POST /api/v1/edges/record-rationale` 的双写端点里，LanceDB 那一半**从不真写**。
  `LanceDBClient.add_documents` 是 `async def`，而改前把它交给 `asyncio` 的 `to_thread`
  去跑——工作线程里只是调用它拿到一个协程对象就返回，函数体一行都不执行也不抛异常，
  于是 `_write_lancedb` 恒返 `WriteStatus(success=True)` 而零写入。
- **H1**：`Neo4jClient` 初始化把凭据/配置错误吞成 JSON fallback。真实 `AuthError` 由
  `verify_connectivity()` 抛，被 `health_check` 的全捕获压成 `health_ok=False`，随即
  `_fallback_to_json()` 返 True；后续查询返回 `[]`，端点按写确认判据记 207 半成功。
- **尾巴**：`neo4j._exceptions.BoltError` 族逃逸；`ConnectionAcquisitionTimeoutError` 归属；
  `neo4j is None` 守卫可达性；`test_edge_rationale_fallback.py` 9 处整体打桩的零覆盖。

**请只读以下范围**（不必通读全仓）：

1. `git diff 9c4e7e82 74742100c62642e45e13780e77ea79c8e5716691 -- . ':(exclude)_bmad-output'` —— 本卡全部改动
2. `backend/app/api/v1/endpoints/edges.py`：文件头 40-135 行（策略 docstring + `_NEO4J_WRITE_FAILURES`
   元组 + `neo4j is None` 守卫）与改后的 `_lancedb_client_for` / `_write_lancedb` 全段
3. `backend/app/clients/neo4j_client.py`：改后的 `initialize()` + `_initialize_neo4j_driver()`；
   以及**只读对照**的 `health_check()`（未改）、`run_query()`（未改，含 lazy 初始化那两行）
4. `backend/lib/agentic_rag/clients/lancedb_client.py`：`add_documents`（含它开头调的
   `_check_and_fix_dimension_mismatch`）、`connect_lightweight`、`embed`、`resolve_table_name`
5. 两个测试文件的新增段全文：
   `backend/tests/unit/test_edge_rationale_fallback.py`（「真写面」段）
   `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py`（门 G2 段 + 1c/1d 参数表变化）
6. `backend/tests/unit/test_neo4j_client.py` 的 `test_driver_initialization_fail_closed_on_auth_error`
   与新增的 `test_driver_initialization_fallback_on_peer_unreachable`
7. 上游依据：`_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §2.4 第 6 条、§2.7 表行；
   `_bmad-output/验收单/UAT-CARD-T-EDGES-2026-09-14.md` 的「未证明」#2/#3/#11 与台账 #3/#4/#5/#10/#11

## ② 作者自述（请独立核对，不要采信）

1. LanceDB 侧从「恒 `success=True`」变成「按 `add_documents` 返回值确认」，且真实表里确实有行；
2. 初始化只对 `AuthError` / `ConfigurationError` fail-closed 上抛，对端不可达
   （`ServiceUnavailable` / `SessionExpired` / 其余）**仍然**转 JSON fallback（有对照用例）；
3. `edges.py` 里 `to_thread` 的文本计数与 AST Call 节点计数都由 3 变 0，`asyncio.gather` 恒为 1；
4. 既有 9 个整体打桩用例**未删**，只在文件 docstring 写明它们的覆盖边界；
5. 真库门走 7692 测试容器（非 mock），本次运行中它可达且真跑；
6. `neo4j_client.py` 的 `health_check` / `_fallback_to_json` / `run_query` / `_run_query_neo4j` /
   `_close_driver` / `_initialize_json_fallback` 六个函数体 sha256 改前改后逐字节相同；
7. pyright `backend/app` 改前改后都是 `0 errors, 80 warnings`。

## ③ 请按重要性排序回答的问题

0. **真写门是否真的证明了「写进了表」而不是夹具自己写的？** 测试子类继承自真
   `LanceDBClient`，只覆写 `embed`（确定性 1024 维）与把 `db_path` 钉在 `tmp_path`；
   `connect_lightweight` / `add_documents` / `resolve_table_name` 原样真跑。这个安排是否留下了
   「门绿在了另一条路径上」的可能？负控（把 `add_documents` 的调用改回交给 `to_thread`）是否
   覆盖了这一点？
1. **`add_documents` 返回值 == 1 作为写确认是否足够？** 它对内部异常一律 `return 0` 而不抛。
   除此之外，还有没有**返回 1 却没有真正落盘**的形态？（例如事务语义、延迟提交、
   `create_table` 与 `table.add` 两条分支的差异。）作者在 docstring 里写了措辞边界，
   请判断该边界是否写得过强或过弱。
2. **lazy 初始化路径上抛 `AuthError` 的影响面。** `run_query` 的
   `if not self._initialized: await self.initialize()` 在 try 之外。生产上还有三个显式调用方：
   `app/api/v1/endpoints/health.py`、`app/services/neo4j_learning_base.py`、
   `app/clients/neo4j_edge_client.py`（经 `app/api/dependencies.py`）。
   这些调用方在「凭据配错」时的新行为是否被现有套件覆盖？有没有把「对端不可达」误判成
   「部署缺陷」的输入？
3. **私有模块 `neo4j._exceptions.BoltError` 的导入。** 守卫式 try/except ImportError 是否足够？
   驱动版本漂移时会不会出现「悄悄退回旧行为而没有任何信号」？门 1c 的那一格在导不到时
   `pytest.skip` —— 这个处置是否掩盖了漂移？
4. **`<vault>_edge_rationales` 前缀表与 `_check_and_fix_dimension_mismatch` 的关系。**
   作者往文档里加了 `doc_type` 键以避免每次写入触发 drop+重建。这个做法是否稳妥？
   现网若已存在同名裸表或旧 schema 表，第一次真写会发生什么？（本卡未查现网存量，已登记。）
5. **`neo4j is None` 守卫保留是否自相矛盾？** 作者断言生产不可达（`get_neo4j_client` 函数体内
   `return None` 计数为 0、返回注解非 Optional），却又保留守卫并为它写了一条打桩用例。
   请判断这个处置的一致性。
6. 门与负控是否存在「判据的取名面不等于它的主张」的问题；有没有哪条断言在本卡改动被撤销后
   仍然会绿。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与**一句复现思路**。
请特别用这四个措辞组织你的发现：

- **未被拦下的输入**（哪种输入能穿过新写的判据）
- **对照输入**（哪一条断言缺少与之配对的反向用例）
- **负控输入**（把某处改回缺陷态后，哪道门**不会**变红）
- **门未覆盖的路径**（哪条生产路径没有任何门看着）

## ⑤ 边界

- 只读审查，不要修改任何文件，不要连接任何数据库。
- 不评价本车道后续卡的面：`app/api/v1/endpoints/index.py` 的 DELETE 三态（P1-B）、
  `app/services/memory_service.py` 与 `app/services/episode_worker.py`（P1-C）。
- 不评价 `lancedb_client.py` 自身的 `add_documents` 吞异常返 0 与自动 drop 重建机制
  （G2-9 族，已登记另立卡）——只评价本卡调用方对它们的处置是否正确。
- `edge_rationales` 表目前零生产读者，本卡只登记不接读侧，不必把「没有读者」当缺陷报。

## ⑥ round-1 之后改了什么（请独立核对这些整改本身是否引入新问题）

round-1 给出 BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2，全部已处置：

1. **HIGH（既有表被 drop 重建、历史丢失却返回 1）—— 已修，两层**：
   - **前置拒写（主防线）**：`_lancedb_incompatible_reason()` 在 `add_documents` **之前**检查
     既有表（`doc_type` 列是否存在、首行向量维度是否等于本次），不兼容就返回
     `WriteStatus(success=False, error="LanceDB write refused (would destroy N existing rows …)")`，
     **不调** `add_documents`，旧行一条不动。
   - **写前/写后行数网（第二层）**：`_lancedb_row_count()` 在写前写后各取一次，要求
     `after == before + 1`。它不认原因只认形状，用来兜住上游将来新增、本卡没复刻的 drop
     触发条件。**它只发现不预防**，这一点在代码注释与门 docstring 里都写明了。
   - 「读不出来」用哨兵 `_ROW_COUNT_UNKNOWN = -1` 与「表不存在(0 行)」分开，因为合并会造
     假绿（写前读失败当成 0 行，drop 重建后的 1 行正好等于 0+1）。
   - 新门：`test_lancedb_real_write_refuses_to_destroy_existing_history`（2 格：缺 doc_type /
     维度不符；断言**旧 2 行仍在**）、`test_lancedb_real_write_row_count_net_catches_silent_rebuild`。
2. **MEDIUM（BoltError 漂移只 skip 无信号）**：新增恒跑门
   `test_BoltError_私有导入漂移必须可见而不是静默收窄`，对账「生产收编状态 == 本进程可导入性」，
   都不可导入时 `pytest.fail` 而不是 skip。
3. **MEDIUM（append-only 门用了两个不同 edge_id）**：改为同一个 `edge_id` 写两条 record，
   并断言两行的 `metadata_json.edge_id` 相同。
4. **MEDIUM（初始化异常传播到其他调用方无门）**：**未加门，如实登记为「本卡未证明」**。
   同时接受 round-1 对路径的更正：实际是 `app/clients/neo4j_learning_base.py` 与
   `app/dependencies.py`（不是先前自述的 `app/services/…` / `app/api/dependencies.py`）。
5. **LOW（None 守卫「删掉会崩」措辞过强）**：注释改为「删掉不会崩——`AttributeError` 仍被
   既有元组接住仍是 207；变掉的是**错误文案的可分辨性**」。
6. **LOW（作者自述的 to_thread 计数不实）**：复算并更正 —— 裸 `to_thread` 文本 **3 → 2**
   （docstring 里解释缺陷时提到两次），`asyncio.to_thread` 文本 **3 → 0**，AST Call **3 → 0**。

**另有一处 round-1 未提、本卡自查发现并已修的回归（请重点核对）**：
初始化路径不再经 `health_check` ⇒ `backend/tests/unit/test_mock_degradation_transparency.py`
与 `backend/tests/unit/test_review_mode_support.py` 里的 `stub_neo4j_singleton_health_check`
这条打桩缝失效，`tests/unit` 目录级实测 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 从 **0** 变成
**2 (blocked=2)** —— 测试进程真的对现网 7691 发起了连接（被 W4 拦下）。处置：两个 fixture
叠加一层驱动工厂打桩（`AsyncGraphDatabase.driver()` 返回 `verify_connectivity` 抛
`ServiceUnavailable` 的假驱动），**保留**原 `health_check` 打桩。请判断：这个处置是否
真的消除了连接尝试、有没有把别的东西一起挡掉、以及这两个地盘外文件的改动是否越界。

请在 round-2 中同时回答：**这些整改本身有没有引入新的未被拦下的输入 / 缺失的对照 / 门未覆盖的路径。**
