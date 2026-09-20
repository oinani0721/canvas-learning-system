绑定 `3260d720fa200556dc7a313220d8f45506492197` 的裁定：**BLOCKER 0 / HIGH 0；新增 MEDIUM 1，既有 MEDIUM 2 继续保留；LOW 3。**

本轮未修改文件、未连接数据库、未运行 pytest。证据来自源码、存档、独立 AST/hash 复算及纯内存数据转换。

1. **MEDIUM｜新增：长度正确的非向量输入仍能穿过维度判据。**

   位置：[edges.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:443)、`lancedb_client.py:4373、4429、4435`。

   **未被拦下的输入**：首次 `embed()` 成功返回 `"x" * 1024`。它满足长度检查，随后原样传入没有显式 schema 的建表路径；返回值与行数增量均不能识别错误列类型。

   我独立复算了安装版 LanceDB 0.30.2 的纯内存转换：

   ```text
   正常浮点向量 → 1 行，fixed_size_list<float>[1024]
   1024 字符串  → 1 行，string
   按 string schema 再转换正常向量 → ArrowNotImplementedError
   ```

   **对照输入**：`test_edge_rationale_fallback.py:874` 只覆盖“成功返回 8 维浮点数组”，缺少“长度相同、类型或层级错误”。负控⑧变红不能补足此缺口。

   **复现思路**：在临时库令首次 embedding 返回上述字符串，检查状态和 `vector` 列类型，再恢复正常浮点 embedding 追加。**本轮证明了转换行为；实际落表结果是依据生产路径推导，未连接数据库复现。**

2. **MEDIUM｜保留：其他初始化调用方的错误契约仍未验收。**

   **门未覆盖的路径**及实际行为：

   | 位置 | 首次初始化抛 `AuthError` 后 |
   |---|---|
   [health.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/health.py:1025) | 被外层捕获，返回 `status="error"` |
   `backend/app/clients/neo4j_learning_base.py:186` | 直接传播 |
   `backend/app/clients/neo4j_edge_client.py:160` | 初始化位于业务 `try` 外，直接传播 |
   `backend/app/dependencies.py:714` | 初始化位于 `yield` 的 `try/finally` 前，直接传播 |

   现有成功委托测试不能证明这些错误契约。登记不修符合本卡边界，但不能标成已验收。

   **复现思路**：分别让这些入口首次 `verify_connectivity()` 抛 `AuthError`，核对响应或传播结果。

3. **MEDIUM｜保留：分页之外的第二次追加仍不可用；调用方已正确报告失败。**

   位置：[test_edge_rationale_fallback.py:898](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:898)、`lancedb_client.py:4423`。

   G1⑫确实检查了首次成功、第二次 `not confirmed`、第一条仍在。其“**绿不代表功能可用**”措辞诚实，没有把失败告警冒充追加功能修复。

   **负控输入**：删掉 `written != 1` 后，此门仍可能通过——行数网同样返回 `not confirmed`；它不能单独证明返回值判据存在，也没有这样主张。

   **复现思路**：预置 11 张排序靠前的表，对目标表连续写两次，检查第二次失败及第一条保留。本项作为既有功能限制保留，不要求本卡越界修改上游。

4. **LOW｜“两项已完整登记进验收单”的自述不成立。**

   位置：[本卡验收单:380](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/_bmad-output/验收单/UAT-CARD-LANCE-DUALWRITE-NEVER-WRITES-2026-09-18.md:380)、`:390、405、427`。

   当前验收单没有分页第二次追加失败的登记；其他初始化调用方只有笼统“未加门”，未逐条写入传播行为，只有 health 单独说明了 `status="error"`。最终 SHA、部分结果也仍是占位符。

   **复现思路**：在绑定 SHA 的验收单检索“分页、第二次追加、直接传播”，并检查 `__FINAL_SHA__`。测试 docstring 的边界准确，但验收单尚未同步。

5. **LOW｜定向负控不能支持“其余门没有连坐”。**

   位置：[本卡验收单:298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/_bmad-output/验收单/UAT-CARD-LANCE-DUALWRITE-NEVER-WRITES-2026-09-18.md:298)；最新负控③⑤⑥⑧日志各自 `:17`。

   四份日志均为 **`26 deselected / 1 selected`**。只能说所选判据变红，不能说全套仅红一格。

   **负控输入**还需准确解读：

   - ③删除返回值检查：`success=False` 仍绿，红的是缺少 `returned 0` 文案；行数网接住了失败。
   - ⑥读取失败当空表：`success=False` 仍绿，红的是缺少 `refused`；后续返回值检查仍接住失败。
   - ⑤、⑧确实红在错误的 `success=True`。
   - ②三个不可达对照仍绿是正确结果：它们锁的是应保留的 fallback。

   **复现思路**：对照日志选择数量与失败断言，区分“诊断或拒写边界退化”与“谎报成功”。

6. **LOW｜None 守卫的绝对措辞仍有残留。**

   位置：[edges.py:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/edges.py:145)、`test_edges_dual_write_neo4j_t5b.py:60、1233`。

   保留防御守卫与测试错误文案是自洽的；但文本仍一面用注解和返回计数推出“生产不可达”，一面承认这些证据不足。改名已完成，措辞整改未完全完成。

   **复现思路**：注入 `get_neo4j_client() -> None` 后删守卫，HTTP 207 仍绿，`:1268` 的精确错误文案断言变红。

其余重点问题的裁定：

- **真写门有效，未发现夹具代写正控目标表。** 正常子类仅替换路径和 embedding；生产写函数执行后，测试另开连接读取表、行数、记录 ID 和字段。端点门替换 factory 的局限，由直接调用真实 factory 的门补足。负控①能检出 `to_thread` 回退。
- **`return 1` 单独不足，现有双层确认合理但有限。** `create_table`、`table.add` 都同步调用完成后才返回计数，没有看到本层另行延迟提交的路径；这不证明内容正确或断电持久性。docstring 的内容正确性边界合理，但“返回值是唯一承重信号”已不准确，因为还有行数网。
- **Neo4j 初始化收窄符合声明。** `AuthError/ConfigurationError` 上抛；三个不可达对照保持 fallback。`ConnectionAcquisitionTimeoutError` 初始化 fallback、查询阶段 500 是明确的阶段策略；**500 不能反推一定是部署缺陷**。
- **BoltError 漂移不会使完整套件静默全绿。** 虽然 1c 会 skip，但 [1c2:608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:608) 在不可导入时明确 fail。生产导入失败仍无运行时告警，这是已注明的边界。
- **旧表处置基本正确。** 非 default vault 不触及裸表；非空前缀旧表缺 `doc_type` 或维度不符时前置拒写、保留历史。空旧 schema 表仍可能因不兼容返回 0，不能称存量迁移完成。
- **metadata 整改成立。** 两个 concept 的值已分别核对，互换会红；timestamp 只证明可被 ISO 解析，没有证明时间准确。

独立复算确认：六个指定 Neo4j 函数体 hash 全部相同；既有 12 个测试函数 AST 全部保留且未变，其中包含九个整体打桩用例。计数应准确写成：**裸 `to_thread` 为 3→2；`asyncio.to_thread` 文本及 AST Call 为 3→0；`gather` 为 1→1。**

存档记录了 **248 passed、无 skip**，最终 pyright 为 **0 errors / 80 warnings**；但正常门与 pyright 日志没有 SHA/hash 绑定，不能据此独立证明最终 SHA 的完整实跑。指定第十四批文件在本 checkout 缺少 §2.4/§2.7，该上游依据仍未核实。


