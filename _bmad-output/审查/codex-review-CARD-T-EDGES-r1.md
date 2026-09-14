**调用修复正确，但本卡有 1 项 HIGH、1 项 MEDIUM、1 项 LOW，不能无保留通过。** 审查绑定 `c9c73f57ebf8fa3992ff01e9a670a24b7874e6e4`；指定代码片段与该提交一致。未修改文件、运行测试或连接数据库。

**BLOCKER：无。**

**HIGH：1 项。**

- [backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:107)：连通性探针只按字符串排除 `:7691`／`:7687`，且在 **:127 模块收集阶段**执行，早于全部注入锚，未保证目标只能是 7692。  
  **显现条件：** `NEO4J_TEST_URI=bolt://localhost` 省略端口时可落到默认 7687；即使仅选择降级门也会执行探针，外部保护未拦截时可能触达现网。

  建议在任何探针、客户端构造之前解析并严格限制测试目标，将探针移入真库门的 fixture。这里证明的是**测试自身存在保护缺口**，不是历史运行曾连接现网；作者提到的 W4 不在允许读取面内。

**MEDIUM：1 项。**

- [backend/app/api/v1/endpoints/edges.py:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:141)：新增的 `AttributeError` 捕获覆盖整个函数，包括模型字段读取、参数构造及客户端内部执行，会把编程缺陷也归为 Neo4j 写入失败。  
  **显现条件：** 例如模型将 `source_node_id` 政名、这里仍访问旧字段，且 LanceDB 侧成功、错误日志所需的 `edge_id` 仍存在时，会返回 207。

  **对⓪的判断：保留成功侧结果合理，但当前范围偏宽，建议收窄。** 它没有伪装成全部成功——仍有 `success=False` 和错误日志——但降低了内部缺陷的可辨识度。若确需兼容客户端缺少方法，只针对确认属于该客户端缺失 `run_query` 的属性解析错误降级；模型准备和方法内部的 `AttributeError` 应保持可诊断。单纯将 `try` 缩到整个 `await` 调用，仍会捕获方法内部缺陷。

  此外，签名不匹配通常抛 `TypeError`，当前不会捕获；`:110–111` 所说“任何方法名／签名错配都降级”不准确。

**LOW：1 项。**

- [backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:380](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:380)：两个客户端的释放串行执行，首个释放异常会跳过第二个。  
  **显现条件：** `await verifier.cleanup()` 抛错时，`:381` 的 `injected_client.cleanup()` 不会执行；应通过嵌套 `finally` 保证两者都获得释放机会。

其余问题与自述核对如下：

| 项目 | 独立结论 |
|---|---|
| **① 连接断开／超时／重试耗尽** | **不能完整确认。** [neo4j_client.py:536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/clients/neo4j_client.py:536) 至 :560 恰好截止于 `try` 内的分支开头，未包含分发及异常转换；`:554` 还会先调用 `initialize()`。只能确认：最终异常若属于当前捕获元组，就返回失败状态；其他类型可能上抛。需要 `run_query` 余下完整函数、`initialize()` 及实际执行／重试函数，才能判定。 |
| **② 裸 FastAPI 门** | **覆盖目标 handler 内部传播路径。** 它挂载真实 router，执行真实 `_write_neo4j_triplet` 和未设置 `return_exceptions=True` 的 `gather`；`raise_server_exceptions=False` 允许测试观察未处理异常的 HTTP 响应。但未覆盖生产应用的 middleware、异常处理器、lifespan，也没有验证真实 LanceDB 已完成落盘。完整等价性需生产 app 的装配代码。 |
| **③ 隔离与清理** | UUID 后缀进入 record/group，清理按本组删除，正常并发可以隔离；`:354` 后的断言失败仍进入 `finally`。但 **`finally` 保证尝试，不保证删除成功**：写入后断网、DELETE 失败或进程被终止都可能留数据。12 位十六进制后缀也只是概率隔离。 |
| **④ OpenAPI** | **未变。** 两提交的 `backend/openapi.json` blob 均为 `a89b8088047260b716ec902fbe69cd5b2ab2d68d`；限定 diff 也没有路由、`response_model` 或 `responses` 声明变更。 |
| **⑤ pyright** | 原调用上的 ignore **确实删除**，新调用与可见签名匹配；但不能由此认证“没有新增诊断”或 `0 errors, 81 warnings`。需要绑定该 SHA 的完整诊断输出与基线，本次未运行全项目检查。 |

另有三项可以明确确认：

- **14 个参数全部保持一致**：已用 AST 比较键名及值表达式，逐项相同；Cypher 未变，`group_id` 仍经过 `to_physical_group_id()`。异常元组确实只新增 `AttributeError`。
- **注入锚成立**：两门均未替换被测函数；源模块 patch 正确。降级门使用独立 probe，并有请求前零计数、请求后非零计数、响应 sentinel、调用方法与参数键集检查，**没有仅凭 500／207 认定注入成功**。
- **历史实跑声明尚未验证**：注释不足以证明红绿实跑、真实落库或从未误连；既有文件“9 处 patch”、getter 恒不返 `None`、`.env` 和 W4 行为均超出指定读取面。真库门的三条前置检查确实存在，但 fallback 检查发生在可能的 `initialize()` 之前，不能仅凭这一点认证后续始终使用真库。


