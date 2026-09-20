**复核结论：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 2。H1、H2 核心修复成立；round-2 的整改尚未全部闭合。**

绑定 `ab1c258ba1a1e5c982fb154f293e9ae3dcbe982d`。三路并行复核，全程只读，未连接数据库、未运行数据库测试。以下行为结论来自源码；已有运行记录另标为存档证据。

1. **MEDIUM — 分页整改只覆盖首次建表，分页之外的既有表仍不能追加。**

   定位：[test_edge_rationale_fallback.py:827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:827)、[lancedb_client.py:4423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:4423)。

   **门未覆盖的路径**：G1⑨ 预置十一张其他表，然后只写目标表一次。第二次写时，调用方已通过 `_all_table_names()` 认出目标表，但 `add_documents` 仍用默认分页的 `table_names()`，误走 `create_table`。默认创建模式遇到同名表会报错，随后返回 0；调用方诚实报告失败，但没有追加。[LanceDB API](https://lancedb.github.io/lancedb/python/python/#lancedb.db.DBConnection.create_table)

   **对照输入**应是“分页之外、已经存在且兼容的目标表”。现有 append-only 门没有分页前提，分页门没有第二次追加。

   **一句复现思路**：在 G1⑨ 首次成功后再写第二个 `record_id`，要求第二次成功且表有两行，当前调用链会停在 `add_documents returned 0`。

   这里报告的是本卡分页验收缺口，不重报上游吞异常机制；当前返回值处置本身正确。

2. **MEDIUM — 首次 embedding 返回错误维度，仍能建立一张被确认成功的错误维度表。**

   定位：[edges.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:429)、[edges.py:453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:453)。

   **未被拦下的输入**：embedding 正常返回八个有效浮点数。调用方未检查约定的 1024 维；目标表不存在时也没有既有维度检查，因而可以创建八维表，满足 `written == 1`、`0 → 1` 并报告成功。之后恢复正常的 1024 维输出，反而被前置拒写持续挡住。

   真实 `embed()` 只检查结果是否为 `None`；其 Ollama 分支原样返回第一条向量。确定性夹具固定返回 1024 维，失败格只覆盖抛异常，缺少“成功返回错误形状”的**对照输入**。

   **一句复现思路**：令测试 `embed` 首次返回八维向量、第二次返回 1024 维，检查第一次成功建错维度表、第二次被拒写。

   这部分应在本卡闭合；不要求在线验证真实模型或语义质量，只需锁住调用方接受的向量维度契约。

3. **MEDIUM — 共享初始化接口改约，其他生产入口的错误契约仍未验收。**

   定位：[health.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/health.py:1025)、[neo4j_learning_base.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_learning_base.py:186)、[neo4j_edge_client.py:159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_edge_client.py:159)、[dependencies.py:714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/dependencies.py:714)。

   **门未覆盖的路径**：健康端点会捕获新抛出的异常，返回 `status="error"`；learning base 原样传播；edge 初始化及依赖初始化发生在各自业务 `try`／`yield` 之前，会直接中止调用。G2 的端到端门只经过 rationale 端点，不能证明上述入口的约定。

   **负控输入**：让 learning base 吞掉初始化异常，或者让依赖捕获后继续 `yield`，本卡 G2 仍不会变红。

   **一句复现思路**：复用 G2 的驱动注入点，分别经过这三个入口，核对 `AuthError`／`ConfigurationError` 的响应或传播，并配对 `ServiceUnavailable` 的 fallback 输入。

   这是验收缺口，尚非已证实的生产回归；共享接口由本卡改变，最低限度的调用方契约应在本卡闭合。

4. **LOW — “metadata 十键逐键核值”仍少两个值。**

   定位：[test_edge_rationale_fallback.py:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:591)。

   键集确实断言恰为十键，但没有比较 `source_concept`、`target_concept` 的值；`timestamp` 也只是非空检查。

   **负控输入／一句复现思路**：仅将生产 metadata 中两个 concept 的值互换，保留键名，当前真写门仍绿。

   当前生产赋值正确；未闭合的是作者声称已补齐的断言。

5. **LOW — None 守卫的测试名称和不可达证明措辞仍有残留矛盾。**

   定位：[test_edges_dual_write_neo4j_t5b.py:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:60)、[同文件:1228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:1228)。

   模块说明仍写“非 Optional ⇒ 死守卫”，G3 又承认这些证据不足；测试名仍称“而不是崩”，正文则正确说明删除守卫不会崩。

   **负控输入／一句复现思路**：删除 None 守卫，HTTP 207 和写失败断言仍绿，仅精确错误文案断言变红。

   保留防御守卫与测试本身一致；它锁住的是错误文案，不能充当生产可达性证明。

**其余关键问题的裁定：**

- **真写门确实经过生产写路径。**正常夹具没有预写目标记录，只替换路径和 embedding；直接调用门经过生产工厂及真实 `connect_lightweight`、`add_documents`、`resolve_table_name`，随后用新连接读出本次 `doc_id`。负控①因目标表不存在而红，能够捕获原来的 async 空转缺陷。端点门替换工厂的边界由直接调用门补足。
- **`返回 1` 单独不足；目前并非只靠它。**本地 LanceDB 0.30.2 的建表和追加都通过 `LOOP.run` 等待操作完成，未发现“只排队、尚未执行便返回”的依据。返回值、前置拒写、写后行数三层各有作用；但它们不证明断电耐久、全部字段正确或跨进程并发下的历史完整性。docstring 对“返回 1”的主要限制说明合理。
- **旧表风险不要求本次连接现网才能闭合。**含历史且缺 `doc_type`／维度不符的目标表会前置拒写；非 default vault 不接管同名裸表。空旧表仍可能因其他 schema 不兼容而返回 0，代码没有承诺迁移成功。现网存量调查可以继续保留为部署验收项。
- **BoltError 漂移旧问题已闭合到测试层。**虽然 1c 单格仍会 skip，但 [1c2:606](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:606) 在不可导入时明确 fail，因此不能再报“整套静默绿”。生产导入失败没有运行时告警，仍是已注明的限制。
- **Neo4j 新增方向对照成立。**ConfigurationError 端点格、三类初始化 fallback 格均存在。连接获取超时在初始化 fallback、查询阶段 500 的策略已锁住；正常慢查询也可能触发该类，所以不能据此认定部署有缺陷。

**负控和作者自述的证据边界：**

- 六个指定函数体的 SHA-256 已独立重算，改前改后全部一致；既有九个端点用例及三个响应模型用例均未删改。
- AST：`to_thread` 调用 `3 → 0`，`gather` 始终为 1。严格文本计数则是 `asyncio.to_thread` 为 `3 → 0`，裸词 `to_thread` 为 `3 → 2`，剩余两处在说明文字中。
- 存档支持 7692 错密码门实际执行过：负控②出现真实 `Security.Unauthorized`，结果为四红三绿；本次没有独立重跑。两份 pyright 存档均写 `0 errors, 80 warnings`，但其内容本身不构成完整的命令与 SHA 绑定证明。
- 负控③、⑥红在错误文案，`success=False` 仍被后续防线保住；④先在“refused”断言失败，`2 → 1` 来自运行日志。③⑤⑥⑦各自只选择一格执行，不能扩写成“全套恰好只红一格”。

最后有一项上游依据**无法核对**：当前 checkout 的指定《第十四批复核裁定与待裁决登记》只有 111 行、仅 §1，没有题面引用的 §2.4／§2.7；指定 UAT 条目已核对。


