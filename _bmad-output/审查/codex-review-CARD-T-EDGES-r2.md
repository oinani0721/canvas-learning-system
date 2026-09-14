结论：**原 `execute_query` 缺陷已修复，但不能据此认定所有真库失败都会返回 207。** 当前 HEAD 确为 `9764cceb`，所审代码与该提交一致。本轮未修改文件、未运行测试、未连接数据库。

**BLOCKER：无。**

**HIGH**

1. **真实驱动异常仍可穿透为 500。**  
   位置：[neo4j_client.py:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/clients/neo4j_client.py:639)、[edges.py:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:148)、`edges.py:332`。  
   问题：`Neo4jError` 被原样重新抛出，`run_query` 只记账，没有统一转换为端点所捕获的异常。  
   显现条件：查询执行或结果消费时发生非重试的权限、数据库、约束等 Neo4j 错误，即使 LanceDB 成功，也会跳过状态合并而回到 500。

2. **round-1 端口防护仅部分关闭：白名单约束入口 URI，未约束路由后的连接目标。**  
   位置：[test_edges_dual_write_neo4j_t5b.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:125)、同文件 `:143`、`:329`。  
   问题：当前放行 `neo4j://`、`neo4j+s://` 路由 URI，入口端口为 7692 不足以保证后续目标仍为 7692。  
   显现条件：使用这些 URI，且服务端路由表公布 7687／7691 等地址时，URI 白名单本身无法阻止后续连接；**现有 socket guard 是否补防仍未决，不能据此认定本次连接过现网**，需要追加读取驱动路由实现及实际加载的 guard／conftest。

**MEDIUM：无新增确认项。**

round-1 的宽 `AttributeError` 捕获，**在本卡限定改动面内可接受注释整改并移交，不要求本卡收窄**。`edges.py:115–120` 已如实说明 `TypeError` 不受保护及参数组装期的宽捕获；但“已登记移交”目前仅见注释，登记本身不在读取面，未独立核验。

**LOW**

1. **三门通过存档缺少承诺的退出码。**  
   位置：[edges-r2-allgates-20260914T225401.txt:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-t-edges/edges-r2-allgates-20260914T225401.txt:15)。  
   问题：正文确有三个 `PASSED`、无 skip，但文件止于 `3 passed in 0.46s`，没有 `rc=`。  
   显现条件：将该档作为完整进程退出成功证据时缺证；这不等于三门实际失败。

2. **Pyright 汇总不足以证明“没有新增诊断”。**  
   位置：[pyright-final-20260914T224710.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-t-edges/pyright-final-20260914T224710.txt:1)。  
   问题：文件只有 `0 errors, 81 warnings, 0 informations` 和 `rc=0`，没有逐项诊断、命令、cwd 或源码绑定。  
   显现条件：诊断一增一减时汇总仍可能相同，因此只能确认存档中的汇总，不能确认 ignore 删除前后逐项无新增。

3. **新增测试仍有一处说明错误。**  
   位置：[test_edges_dual_write_neo4j_t5b.py:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:322)。  
   问题：注释称旧黑名单对前三种输入“全都会放行”，实际仅前两种。  
   显现条件：第三种 `bolt://host-7692.example:7687` 含字面 `:7687`，旧黑名单也会拒绝，所给归一化存档第 4 行同样记录为 `False`。

**六个问题的具体结论**

**① 异常链不是统一降级。**

| 实际路径 | 当前结果 |
|---|---|
| 原样抛出元组中的五类异常 | 生成 `WriteStatus(False)`；另一侧成功才是 207 |
| `_driver` 起初不存在，`:595–596` | 转成 `RuntimeError`，可捕获 |
| `ServiceUnavailable`／`SessionExpired`／`TransientError` | 按 `:57`、`:598–603` 重试，不能当作内建 `ConnectionError` |
| 重试耗尽且尚未 fallback，`:622–629` | 切 JSON 并执行 JSON 查询；**若正常返回，端点记成功，而非失败** |
| 到达 `:627`／`:635` 时已被并发请求切为 fallback | `:630`／`:638` 原样抛 `RetryError` 或相应驱动异常，可漏出 |
| 其他 `Neo4jError`，`:639–641` | 原样上抛，可回到 500 |
| 重试期间 driver 变为 `None`，`:611` | `AssertionError` 漏出 |
| `TypeError`、`ValueError`、`KeyError` | 若出现，同样不在元组内 |

fallback helper 在 `except` 内抛出的异常，也不会被同级后续 `except` 再捕获。初始化失败时，`initialize()` 可以返回 `False`，但 `run_query:554` 没有检查该返回值。

要确定断连、超时及重试耗尽后的**最终结果**，还需同文件的 `health_check`、`_close_driver`、`_initialize_json_fallback`、尤其 `_run_query_json_fallback` 全函数；当前不能确定 JSON 分支如何处理本次 `CREATE (:EdgeRationale …)`。`CancelledError` 则属于取消传播，不应一概描述为普通 HTTP 500。

**② 本文件的探针惰性化成立，整次 pytest 零网络尚不能确认。**

探针唯一调用点已在真库测试体 `:365`；降级门的请求前注入也成立。标准库纯解析核对结果如下：

| URI 形态 | 白名单结果 |
|---|---|
| IPv6 `[::1]:7692` | 放行；缺省端口、`:0`、`:7687`、错误括号拒绝 |
| user-info | 按最后 `@` 后的目标端口判断 |
| scheme／主机大小写 | 不改变端口判定 |
| 尾随普通空格 | 拒绝 |
| tab／换行 | 可能被解析器剥离，解析成 7692 后放行；未证明存在现网端口绕过 |
| 全角／阿拉伯文数字 | 拒绝 |
| `:07692` | 放行，数值为 7692 |

但 `:61–62`、`:235–236` 的导入先于依赖替换。排除其他连接需要实际加载的各级 `conftest.py`、`backend/pytest.ini`、`backend/tests/support/live_port_guard.py`，以及相关导入模块顶层与 `resolve_vault_group_id` 实现。日志中的 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` 也不等于全部网络动作为零。

**③ round-1 串行 cleanup 已修复，但 UUID 和 finally 不保证删除成功。**

`:451–454` 保证 verifier cleanup 抛错后仍尝试 injected cleanup。以下情况仍可能留数据：

- 真写成功后，查回或 DELETE 阶段断连、失败，或客户端切入 JSON fallback。
- 进程被强杀，或清理过程未能完成。
- 被测代码回归写入错误 group，而 `:445` 只删除预期 group。

是否会出现 DELETE“静默成功”仍取决于未提供的 JSON helper。当前 CREATE 只建 `EdgeRationale`；同组内重试产生的重复节点，只要真库 DELETE 成功，也能一起清掉。

**④ OpenAPI 确实未变。** 两端 `backend/openapi.json` 的 Git blob 完全相同：`a89b8088047260b716ec902fbe69cd5b2ab2d68d`。

**⑤ 汇总已核实，逐项无新增未证实。** 需要同配置、绑定前后代码版本的完整诊断清单，才能关闭上述 LOW。

**⑥ 14 个键及值表达式逐一对应。** `group_id` 仍调用 `to_physical_group_id(resolved_group_id)`；调用正确改为 `run_query(query, **params)`；except 元组确实只新增 `AttributeError`。round-1 后生产文件仅改注释。

其余证据吻合：两份有效红档分别红在 500／`AttributeError`，均 `rc=1`；两条负控红在目标断言，跑前、跑后及当前 `edges.py` 哈希一致。两份 nodeids 各 64 条且字节相同，但 unit 实际为 **35 failed + 29 errors，rc=1**，只证明相对所给列表没有新增失败节点；作废存档未作为验收依据。
