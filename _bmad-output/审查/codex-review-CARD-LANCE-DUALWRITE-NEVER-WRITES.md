**核心 H1/H2 修复成立，但整卡只能判 PARTIAL：BLOCKER 0、HIGH 1、MEDIUM 3、LOW 2。**

绑定 HEAD 已确认是 `ddcaad55e6b03723c1d5ceeb95a417c2b3ada625`。本次只读、未运行测试、未连接数据库；以下负控结果均为源码推导，不能替代实际负控记录。

先回答最重要的两点：

- **真写门没有由夹具代写。** [夹具:422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:422) 的正常子类仅固定路径、替换嵌入；写入后，[断言:513](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:513) 重新连接临时库，检查具体表、行数、内容及 `record_id`。它证明了这条写入链，不能证明真实嵌入服务及旧表兼容性。只把调用恢复成 `to_thread`，G1①②会因没有记录而红，判据有效。
- **`written == 1` 足以作为当前调用的正常写完成确认，不能作为内容正确、旧历史保留的确认。** 本地 LanceDB 0.30.2 的同步 `add`、`create_table` 都等待底层操作完成；这里没有使用忽略已有表数据的 `exist_ok=True`，也没有选择丢弃坏向量的模式。未发现正常路径“返回 1，但该行仍等待另一次显式提交”的形态。官方也区分了读一致性与写操作一致性。[LanceDB 文档](https://lancedb.github.io/lancedb/python/python/#lancedb.connect)  
  [edges.py:323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:323) 的措辞边界基本合适；它没有证明断电持久性，也不能覆盖下面的历史丢失条件。

1. **HIGH — 未被拦下的输入：不兼容的既有目标表，或漂移的嵌入维数。**

   [edges.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:367) 未验证向量维数，随后直接调用 `add_documents`，只凭返回 1 报成功。新文档带 `doc_type` **不会补齐旧表 schema**：非空目标表缺该列时，[检查:4315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:4315) 会进入 drop，再建仅含本次记录的新表，最后返回 1。已有 1024 维表、下一次嵌入返回 384 维也一样。

   **对照输入**缺少“已有历史＋不兼容 schema/维数”；目前 G1 全部从空库开始且固定 1024 维。

   **一句复现思路：** 临时库预置一张含两条历史、向量有效但缺 `doc_type` 的目标表，再调用 `_write_lancedb`，检查返回成功而旧两行消失。

   这是**本卡新调用方未拦截危险前提**，不重复裁判 G2-9 的 drop 机制；现网是否满足前提仍未知。

2. **MEDIUM — 负控输入：BoltError 私有导入漂移，门不会变红。**

   [edges.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:38) 导入失败后静默缩小捕获集合；[门 1c:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:565) 同时 `pytest.skip`。因此“版本漂移由门 1c 钉住”不成立。

   守卫足以避免模块导入失败，不能保证异常处置契约。pytest 会显示跳过，不能说完全无信号；但测试仍可成功退出，生产也没有专门的漂移告警。

   **一句复现思路：** 令生产与测试两处私有导入都失败，观察捕获集合失去 BoltError，而该格只跳过。

3. **MEDIUM — 对照输入缺失：append-only 门没有验证同一 edge 的历史。**

   [测试:551](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:551) 使用两个不同 suffix，而 [构造器:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:474) 据此生成两个不同 `edge_id`。两行断言证明跨 edge 累积、第二次写未整表清空，证明不了同一 edge 的版本历史。

   **负控输入／一句复现思路：** 将写路径改成“每个 edge 只保留最新记录”，现有 G1②仍会保留两个不同 edge，其行数和 ID 断言全部绿。

   当前实现确实追加；问题在门的主张超过了覆盖范围。

4. **MEDIUM — 门未覆盖的路径：初始化异常契约传播到其他调用方。**

   [run_query:578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_client.py:578) 的 lazy 初始化确在 `try` 外。G2 覆盖了真实初始化链及 edges 的 AuthError→500，但不能据此概括所有调用方：

   | 调用方 | 凭据错误后的行为 |
   |---|---|
   | [health.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/health.py:1025) | 外层捕获，返回结构化 `status="error"`，不是 HTTP 500 |
   | [neo4j_learning_base.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_learning_base.py:186) | 异常直接传播 |
   | [neo4j_edge_client.py:159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/clients/neo4j_edge_client.py:159) | 初始化在操作的 `try` 外，异常直接传播 |
   | [dependencies.py:713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/dependencies.py:713) | 初始化在 `yield/finally` 外；未发现该依赖的活跃端点引用，不能声称已造成另一入口回归 |

   实际路径是 `app/clients/neo4j_learning_base.py`、`app/dependencies.py`，与任务中的两处路径不同。

   **负控输入：** 恢复旧 fallback 后，现有[健康接口测试:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_memory_health_api.py:98) 接受 `ok/error` 两者，仍绿。

   **一句复现思路：** 复用 G2 假驱动在 `verify_connectivity()` 抛 AuthError，分别调用这些真实调用方，断言各自错误契约及初始化状态。

5. **LOW — None 守卫保留一致，但“删掉会崩”的解释不准确。**

   正常 getter 的实际控制流支持返回实例；注解及 `return None` 文本计数本身不够构成证明。保留防御分支不矛盾。

   但删掉 [守卫:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:151) 后，`None.run_query` 的 `AttributeError` 仍会被 [既有捕获:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:222) 接住。G3 实际锁的是明确文案及防御分支。

   **一句复现思路：** 删除守卫并注入 None，状态仍为 207，只有 [G3:1197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:1197) 的精确错误文案断言变红。

6. **LOW — 作者③的文本计数不实。**

   [edges.py:313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:313) 的 docstring 仍包含两次 `to_thread`。独立复算为：**文本 3→2，AST Call 3→0，gather Call 1→1**。不影响功能修复。

   **一句复现思路：** 对两个 SHA 的文件分别执行字符串计数和 `ast.Call` 计数。

其余问题的裁定：

- **旧裸表：** 非 default vault 会新建前缀表，裸表保持原样，不会自动迁移；default/空 vault 仍使用裸表。旧目标表缺列或维数不同见 HIGH；空表或其他 schema 不兼容不一定触发 drop，写失败返回 0 时，本卡正确记失败。
- **异常归属：** 未发现常规连接拒绝、会话失效被新代码误送入 Auth/Configuration 分支。`ConfigurationError` 的子类也会被上抛，包括不支持的服务器产品/协议，不能把它解释成仅本机配置格式错误。`ConnectionAcquisitionTimeoutError` 在初始化阶段仍 fallback，在已初始化后原样到达端点时按 500 处置；这是阶段相关策略，根因归属仍待裁。
- **其他负控边界：** 恢复 `to_thread` 时，G1③“未确认即失败”和原九个整体打桩用例仍可绿；删除返回值检查时，G1③才承担变红责任。恢复 H1 吞异常时，G2 Auth/Configuration 门应红，ServiceUnavailable 对照仍绿。这种分工合理。另，G1④对完整旧版本可能先因工厂不存在而在夹具安装处红，不能单凭该红证明落表判据有效。
- **静态自述确认：** 六个指定 Neo4j 函数体 SHA-256 前后一致；原九个整体打桩测试全文保留。7692 当次确实执行、负控实际结果、pyright 两端 `0 errors, 80 warnings`，本次均未独立确认。
- **上游证据缺口：** 指定裁定文档在绑定提交中止于[第 111 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:111)，不存在 §2.4/§2.7；UAT 指定条目已核对，不能替代缺失的裁定段落。


