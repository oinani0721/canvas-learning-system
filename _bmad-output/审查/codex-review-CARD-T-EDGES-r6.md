**结论：写确认修复有效，但 `[]` 只能表示“写入未确认”，不能断言“没有落盘”。窄 `try` 未发现已证实的新运行回归；测试仍有两处关键覆盖缺口。**

已复核 HEAD `8ff37ea543332fb8aba1a48c5e8ba2d3910f511c`；两文件与 HEAD 一致，`edges.py` SHA256 与负控存档前后一致。本轮未改文件、未连库、未运行 pytest；另外查阅了 Neo4j 官方协议及 **6.1.0** 驱动源码。

## BLOCKER

无。

## HIGH

### H1 — 初始化仍吞掉部署错误，不能宣称真实 AuthError 必然 500

**【缺陷成立但超出本卡改动面；建议 HIGH；非本轮新增】**

[neo4j_client.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/clients/neo4j_client.py:411)：初始化会把 `AuthError`，以及随后 `except Exception` 捕获的配置错误，转成 JSON fallback，端点元组无法再按原异常分类。

**显现条件：**首次初始化遇到上述错误、fallback 初始化成功且 LanceDB 报告成功，后续查询返回 `[]`，本轮结果仍是 **207**。门 1d 直接让 `run_query` 抛异常，只证明“异常穿透客户端之后”的边界。

客户端行为需移交；本卡内应限定“部署错误必须 500”的说明。

## MEDIUM

### M1 — “返回零行＝没有落盘”存在具体反例

[edges.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:190)、同文件 `:211`：注释及响应里的 `write did not land` 把未知提交结果说成了确定失败。

**显现条件：**

`Neo4j 已提交 → 最终响应丢失 → ServiceUnavailable/SessionExpired → 后续重试耗尽 → neo4j_client.py:628–629 fallback → :669 返回 []`。

这是协议与当前控制流支持的路径推导，本轮未做断网实测。自动提交的最终确认由 PULL 的成功消息承载；6.1.0 驱动在对应连接中断时可抛上述异常。[Bolt 协议](https://neo4j.com/docs/bolt/current/bolt/message/)、[6.1.0 驱动断线处理](https://github.com/neo4j/neo4j-python-driver/blob/6.1.0/src/neo4j/_async/io/_bolt.py#L888-L907)

**对①的精确回答：**

- **`session.run → result.data()` 正常完整完成：**当前无过滤的单节点 `CREATE … RETURN` 应返回一行，未发现合法的“已写成功但正常返回零行”路径；`data()` 会完整迭代这个尚未消费的结果。[Cypher CREATE](https://neo4j.com/docs/cypher-manual/current/clauses/create/)、[6.1.0 AsyncResult.data](https://github.com/neo4j/neo4j-python-driver/blob/6.1.0/src/neo4j/_async/work/result.py#L705-L730)
- **整个 `_run_query_neo4j` 最终返回：**存在上面的“已提交但最终返回 `[]`”路径。

保留 `success=False` 的保守处理合理；措辞应改为“未取得写入确认，提交结果可能未知”。本卡无需因此承担整个客户端的幂等重试修复。

### M2 — 类型名断言无法验证生产代码添加了类型名

[test_edges_dual_write_neo4j_t5b.py:509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:509)、同文件 `:516`：注入的异常消息自身已经包含 `type_name`，随后又检查响应包含该名字。

**显现条件：**生产把 `error=f"{type(e).__name__}: {e}"` 改回 `error=str(e)`，这五格仍能通过，无法识别类型前缀丢失。

建议异常消息仅含统一 sentinel，并断言响应 `startswith(f"{type_name}:")`。

### M3 — 16 格没有锁住窄 `try` 边界

[test_edges_dual_write_neo4j_t5b.py:553](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:553)：异常门都从客户端调用处抛错，没有覆盖 getter 或组装阶段抛出原本会被捕获的异常。

**显现条件：**保持新元组和写确认，仅把 `try` 恢复为包整个函数，现有测试输入无法区分这一回归。

至少需要一条 getter 抛 `AttributeError` 必须穿透为 500 的行为门。这是源码确认的覆盖缺口，本轮未运行该突变。

## LOW

### L1 — 异常集合可以作为处理策略，不能作为根因分类器

[edges.py:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:52)、同文件 `:56`：`ConnectionPoolError＝session 泄漏`、新收四类“只描述对端状态”都过于绝对。

**显现条件：**正常慢查询占满连接池即可触发其子类 `ConnectionAcquisitionTimeoutError`；官方也明确说明 `ServiceUnavailable` 可能源于错误配置。[6.1.0 连接池超时路径](https://github.com/neo4j/neo4j-python-driver/blob/6.1.0/src/neo4j/_async/io/_pool.py#L375-L395)、[异常定义](https://github.com/neo4j/neo4j-python-driver/blob/6.1.0/src/neo4j/exceptions.py#L908-L1004)

因此，②的分界作为 **207/500 策略**可以成立；`ConnectionAcquisitionTimeoutError` 是最值得重新裁定的具体类。维持其 500 也可以，但不能以此证明存在泄漏。

### L2 — “从生产读取清单”“身份判据”的说明不准确

[test_edges_dual_write_neo4j_t5b.py:499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:499)、同文件 `:505`：用例清单实际由测试独立维护，`issubclass` 检查的是继承捕获关系，并非直接成员身份。

**显现条件：**生产增加额外异常不会自动增加测试；换成父类也可能让该断言继续成立。

⑤中这种耦合本身合理：**独立预期表＋生产捕获关系＋实际 HTTP 行为**，优于从生产元组动态生成全部用例，否则删生产类型可能同时删掉对应测试。

## 其余问题结论

- **③、⑥：**查询、参数组装顺序、`None` 分支均保留；异步 `initialize()` 仍在 `run_query()` 内，仍受窄 `try` 包围。除预期变化外，成功日志和 `WriteStatus` 构造也移出了捕获范围，未发现可达的新问题。限定读取面不含 getter 定义及同步构造路径，因此不能保证不存在其他运维态由 207 变成 500；要闭合这点，需要补读 `neo4j_client.py` 的 `get_neo4j_client` 及其同步构造路径。
- **④前置锚：**整改基本到位。`:763` 的 URI 原值比较能检查构造器改写；`:767` 的白名单仍是重复断言，但已标为非承重。原 fallback 前置检查已删除，真实查回门仍能识别未写入。
- **证据：**存档确实记录四条负控对应失败、恢复后 **16 passed、rc=0**，真库门记为 PASSED；这些证据没有覆盖 M2、M3，不能据此消除两项缺口。
