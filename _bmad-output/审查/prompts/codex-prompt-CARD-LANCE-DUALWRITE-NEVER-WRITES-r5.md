# 独立复核任务 round-5 — CARD-LANCE-DUALWRITE-NEVER-WRITES（BATCH-2026-09-18-第十五批 / 车道 P1）

## ① 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage`
基线 SHA：`9c4e7e82`　审查绑定 SHA：`efaece7fc899d408d58a80485b5e8e467d5ccccc`

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

1. `git diff 9c4e7e82 efaece7fc899d408d58a80485b5e8e467d5ccccc -- . ':(exclude)_bmad-output'` —— 本卡全部改动
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

## ⑥ round-4 之后改了什么（**本卡最后一轮**，代码已冻结）

round-4 判 **BLOCKER 0 / HIGH 0** / MEDIUM 3 / LOW 3。处置：

### 已修

1. **MEDIUM（新）「长度正确的非向量输入仍能穿过维度判据」—— 已修，用的是收敛法而不是加一格。**
   round-4 指出 `"x" * 1024` 满足长度判据，会把 vector 列建成 `string`，此后正常 float 向量
   插进来 `ArrowNotImplementedError`，这张表从此写不进去。
   ⛔ 继续枚举坏形状关不住（我实测：`sum()` 能挡住字符串/嵌套，但**漏 `bytes`**，因为 bytes
   是 int 序列）。所以改成**规范化**：`vector = [float(component) for component in vector]` ——
   能归一的，写进去的列类型**必为 float**；归不了的（字符串 / 嵌套 list / None）抛
   `TypeError`/`ValueError` 被接住拒写。实测覆盖面：
   `[0.5]*1024 → 放行` / `'x'*1024 → ValueError 拒` / `[[0.1,0.2]]*1024 → TypeError 拒` /
   `None → TypeError 拒` / `b'x'*1024 → 归一成 float 放行` / `['1']*1024 → 归一成 float 放行`。
   门参数化为两格：`embed-returns-8-dim` 与 `embed-returns-1024-char-string`。
   负控段⑧（删掉该判据）实测两格全红，红在 `错误维度的向量被写进去了: WriteStatus(success=True)`。
2. **LOW「None 守卫的绝对措辞残留」—— 已修**：`edges.py` 的守卫注释与 t5b 模块 docstring
   都去掉了「生产不可达 / 死守卫」，改为「注解与 `return None` 计数**只是线索，不构成证明**」。
3. **LOW「验收单自述不成立」「定向负控不能支持『其余门没有连坐』」—— 已在验收单改正**（见下）。
   特别是后者：那四段日志都是 `N deselected / 1 selected`，`-k` 本来就只选中一格，所以只能说
   **被选中的那条判据变红**，不能推出「全套只红一格」。验收单已按这个口径重写，并区分
   「③⑥ 红在错误文案、`success=False` 仍由后续防线接住」与「⑤⑧ 红在谎报 `success=True`」。

### 登记不修（与 round-4 裁定一致）

4. 分页之外的第二次追加不可用 —— 根因在 `add_documents` 内部的分页 `table_names()`，卡文硬边界
   禁改；已有门钉住「响亮失败 + 第一条仍在」，门 docstring 明写「绿不代表功能可用」。
5. 其他初始化调用方（`health.py` / `neo4j_learning_base.py` / `neo4j_edge_client.py` /
   `dependencies.py`）的错误契约未加门 —— 四个文件都在禁改面内；round-4 给出的逐条传播行为
   已抄进验收单「本卡未证明什么」。

### 另外回应 round-4 的证据绑定意见

收工的 `tests/unit` / `tests/regression` / `tests/api` 存档**首行已写入 `HEAD=<sha>`**，
使日志与绑定 SHA 可对账。

请在 round-5 只判一件事：**上述整改本身有没有引入 BLOCKER / HIGH**；
若只剩 MEDIUM / LOW，请直接说明，本卡将按协议登记不阻断。
