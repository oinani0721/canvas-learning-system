绑定 **`74742100c62642e45e13780e77ea79c8e5716691`**，相对 `9c4e7e82` 复核。

**本轮发现：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 2。** H1/H2 主修路径成立；round-2 新行数网存在分页导致的误判，部分新增判据仍缺负控覆盖。另保留已登记的其他初始化调用方覆盖缺口。

本轮未修改文件、未连接任何数据库。下面的复现思路和负控结果均为静态推导，未实际运行。

1. **MEDIUM — 行数网把分页之外的已写表当成不存在。**

   位置：[edges.py:305](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:305)、[edges.py:498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:498)。

   **未被拦下的输入：**库内已有十张排序靠前的表，首次写入的目标表排在第十一张。`add_documents` 可以成功建表并返回 `1`，但写后 `table_names()` 的第一页仍不含目标表，行数网得到 `0 → 0`，将真实写入报告为失败。

   这与指定上游源码 `lancedb_client.py:4291` 已记录的分页问题一致；SDK 文档也将默认页长定义为十。[LanceDB API](https://lancedb.github.io/lancedb/python/python/#lancedb.db.DBConnection.table_names)

   **对照输入：**现有真写门缺少“库内已有十张其他表”的同请求对照。

   **一句复现思路：**临时库预建十张排序靠前的表，再写目标记录，比较目标表实际内容与 `WriteStatus`。

   此项是本卡新增确认逻辑的误判；不能据此推断既有第十一张表必然被删除。

2. **MEDIUM — “读取失败”门只覆盖没有连接，未锁住真正的读取异常。**

   位置：[edges.py:308](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:308)、[test_edge_rationale_fallback.py:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:602)。

   **门未覆盖的路径：**`table_names()`、`open_table()` 或 `count_rows()` 抛异常。现有用例令 `_db=None`，只走前面的独立早退分支。

   **负控输入：**仅将 `except` 分支的 `return _ROW_COUNT_UNKNOWN` 改为 `return 0`，现有新增门仍可全绿，而作者特别防范的“读取失败被当成空表”漏洞已经回来。

   **一句复现思路：**预置不兼容历史表，让首次行数读取抛错、后续操作正常；上述负控会跳过前置检查，重建后恰好满足 `1 == 0 + 1`。

   **当前生产分支写法正确；问题是保护历史数据的关键分支没有被门锁住。**

3. **MEDIUM — Neo4j 异常矩阵仍缺两个方向的对照。**

   位置：[test_edges_dual_write_neo4j_t5b.py:638](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:638)、同文件 `:1136`、`:1173`。

   **负控输入：**单独将 `ConfigurationError` 加入 `_NEO4J_WRITE_FAILURES`，配置错误会被端点降为 207，但直接初始化门仍正确上抛，端点门又只注入 `AuthError`，所以本卡相关门仍可全绿。

   **对照输入：**初始化 fallback 只测试 `ServiceUnavailable`。门 1c 的 `SessionExpired` 来自替换后的 `run_query()`，绕过初始化；把初始化中的 `SessionExpired` 改成上抛，现有这些门也不会发现。

   **一句复现思路：**分别做上述单点变异，补跑配置错误端点格，以及 `SessionExpired`／其他非配置 `DriverError` 的初始化 fallback 格。

   当前生产分类没有发现这两处错误；这是对“只收窄 AuthError／ConfigurationError”的证明不足。

4. **LOW — “metadata 十键”主张超过实际断言。**

   位置：[test_edge_rationale_fallback.py:559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:559)。

   **负控输入：**删除生产 metadata 中的 `source_node_id`、`target_node_id`、`confidence` 或 `timestamp`，该门仍可通过，因为实际只核对 `record_id` 与 `edge_id`。

   **一句复现思路：**逐项移除上述字段，观察真写门仍绿；应补断言或收窄“十键”措辞。

5. **LOW — 测试文档仍保留修复前结论。**

   位置：[test_edges_dual_write_neo4j_t5b.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:73)、同文件 `:83`、`:1212`。

   文档仍称 BoltError 未收编、LanceDB 从不真写；None 门说明仍强调“不崩／而不是 AttributeError”，没有同步为“错误文案可分辨”。

   **一句复现思路：**对照生产捕获元组、真实写调用及 None 精确文案断言，即可看到说明与实现不一致。

对你重点问题的裁定如下。

| 问题 | 裁定 |
|---|---|
| 真写门是否由夹具自己写绿 | **不是。**成功门没有预置目标记录；子类只替换路径和 embedding，真实连接、表名解析、写入均被执行，之后另开连接检查固定表及 `doc_id`。恢复 `to_thread` 会因记录未写出而红。它不证明真实 embedding 服务及生产配置。 |
| `返回值 == 1` 是否足够 | **单独不足。**当前代码还要求净增一行。`create_table` 与 `table.add` 都是在同步调用正常返回后才返回数量，未发现另一条明确的“遗漏 await、返回 1 却零执行”路径；但这不证明全部字段正确、并发隔离或断电持久性。docstring 的内容正确性边界合理，“唯一承重信号”已因行数网加入而过时。 |
| 前置拒写与旧表 | 对**枚举可见且有历史**的目标表，两种已知不兼容条件均在写前拒绝，测试还检查旧 `doc_id` 保全；整改成立。非 default vault 不回退裸表。其他旧 schema 仍可能导致上游返 0，不能宣称完成了存量迁移。分页问题见 M1。 |
| BoltError 漂移 | 恒跑门解决了“两边都导不到、测试只 skip”的漏洞；完整运行该门会失败。生产导入失败本身仍没有日志，因此保证是**测试能发现**，不能扩大成生产运行时必有告警。 |
| None 守卫 | 保留防御性文案分流不矛盾。实际工厂构造后返回实例，正常路径不返回 None；删除守卫仍会被 `AttributeError` 捕获而返回 207，但精确文案断言会红。仅靠返回注解和 `return None` 计数本身不足以证明不可达。 |
| append-only 整改 | 同一 `edge_id`、两个 record，并核对两行 metadata 的归属，已修正 round-1 的证明缺口。 |

**其他初始化调用方仍是“已登记、未证明”，不能算覆盖完成。** 实际传播行为也不相同：

- [health.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/health.py:1025)：异常被外层捕获，返回 `status="error"`，并非自动变成 HTTP 500。
- [neo4j_learning_base.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_learning_base.py:186)：直接传播初始化异常。
- [dependencies.py:714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/dependencies.py:714)：初始化在 `try/finally` 之前，异常会阻止依赖 yield。
- [neo4j_edge_client.py:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_edge_client.py:160)、`:218`：初始化在业务异常处理之前。

复现方式是分别向这些入口的真实客户端注入认证失败，检查响应、传播与清理。当前 `ServiceUnavailable`／`SessionExpired` 初始化仍 fallback，未发现本卡把它们改判为部署缺陷；`ConnectionAcquisitionTimeoutError` 查询阶段保留 500 仍是处置策略，不能据此断言根因一定在本方。

**两个 fixture 的整改在本次连接路径上成立，属于同一修复所需的测试接缝迁移。** [test_mock_degradation_transparency.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_mock_degradation_transparency.py:78) 与 [test_review_mode_support.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_review_mode_support.py:68) 替换的是生产查找驱动工厂的位置，因此此次初始化不会创建真驱动；真实初始化分类和 JSON fallback 仍执行。

它们也屏蔽了这些测试期间真实驱动的认证／配置行为，故不能用作认证分类门。恢复旧初始化时这两个套件仍绿是预期的隔离效果，缺陷应由 G2 抓住。仅凭这些 fixture，不能证明 fixture 生效前已有驱动、其他驱动入口或整个测试进程均零连接；本轮也没有独立验证作者声称的 `ATTEMPTS=0`。

最后，证据核对结果是：

- 已独立复算：裸 `to_thread` **3→2**，`asyncio.to_thread` 文本及调用节点均 **3→0**，`asyncio.gather` 调用 **1→1**。
- 六个指定函数的源码片段 SHA-256 改前改后相同；既有测试定义未删除或修改。
- 九个整体打桩用例在撤销真实写修复后仍绿，符合其已声明的 handler 组合覆盖边界。
- G1③-b 删除返回值检查后，行数网仍可能判失败；该门此时依靠 `"returned 0"` 文案变红。这能锁住分支，不能证明“删检查必然谎报成功”；“已写一行但最终返回 0”是更有区分力的对照。
- **未独立验证**7692 本次可达且真跑、负控运行日志、pyright `0 errors / 80 warnings`。
- 指定上游裁定文件在绑定 SHA 中只有 **111 行，不含 §2.4／§2.7**，这两处依据无法核对；指定 UAT 条目已核对。


