**结论：接受 HIGH-1 的范围处置，保留 HIGH 移交；HIGH-2 已关闭。整次“仅降级门 pytest 零网络”仍未证实。**

核对 HEAD 为 `c2e3d53381a88341b98ef411f4a3e016b6118602`，两份代码文件与该提交一致。全程未修改文件、未连接数据库，未重跑 pytest。

**BLOCKER：无。**

**HIGH：1 条。**

- **H1〔缺陷成立，但超出本卡改动面〕** — [edges.py:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:157)：穿透客户端的真实驱动异常仍不会转成 `WriteStatus`，会从 handler 的 `asyncio.gather` 上抛，丢失应返回的部分成功状态。**显现条件：**已初始化的真驱动执行查询时发生非重试的权限／约束 `ClientError`，由 `neo4j_client.py:639-641` 原样抛出；即使 LanceDB 已成功，端点仍可能返回 500。

**MEDIUM：无新增；已接受的清理保证限制继续保留。**

**LOW：3 条，其中前两条为本轮新增说明问题，第三条是新增读取面确认的既存说明问题。**

- **L1〔新增〕** — [edges.py:122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:122)、测试文件 `:42-49`：把“七类异常不匹配端点 except”推成“七类真实失败都会返回 500”，结论过强。**显现条件：**`ServiceUnavailable`／`SessionExpired`／`TransientError` 会先经过客户端重试与 JSON fallback（`:620-638`），初始化失败也有 fallback（`:400-419`），MRO 本身不能证明最终 HTTP 状态。
- **L2〔新增〕** — [test_edges_dual_write_neo4j_t5b.py:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:150)：第一段异常处理的注释误把“非整数端口”归到 `urlsplit()`。**显现条件：**输入 `bolt://host:abc` 时，实际在第二段读取 `parsed.port` 才抛错；功能正确，注释错位。
- **L3〔既存〕** — [test_edges_dual_write_neo4j_t5b.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:54)、`:404`：默认 W4 必阻断及整次运行零网络的表述超过现有保证。**显现条件：**降级门带 `integration` 标记，根 conftest `:143-145` 启用豁免，guard 对该作用域默认只记账、不阻断；其他端口和未审导入链的网络行为也不能由该账本排除。当前注入锚仍有效，不能据此推断本次实际发生过连接。

**① HIGH-1 的范围判断**

**不要求本卡越界修复。** 卡文明确只准增加 `AttributeError`，严重度不会自动扩大授权；与 round-2 的 MEDIUM 应采用同一范围口径：可以接受明确披露并移交，但不能把缺陷记为已关闭，也不能宣布端点完整失败语义通过。

需要纠正的是当前披露措辞，最小表述可为：

> 七类异常均不被本函数的 except 捕获；若穿透客户端内部的重试／回退，仍会导致端点 500。查询权限／约束错误存在该路径。

except 缺口确实在基线存在，但本卡接通 `run_query` 后真实查询路径变得可达，因此风险仍须保留。移交登记按你的说明采用，给定读取面未包含实际登记条目。

**② 双白名单与零网络**

针对“驱动目标端口不得落到 7691／7687”，**未发现剩余绕过**：三种路由 scheme 均拒绝，探针、注入客户端和 verifier 都经过检查。它保证端口范围，不证明任意 `host:7692` 就是指定测试容器；带 userinfo 的输入即使被该 helper 放行，驱动仍可能拒绝，并不构成禁用端口绕过。

可以确认降级门本体没有调用可达性探针，Neo4j 与 LanceDB 写依赖均已替换，裸 app 没有 lifespan；真库 fixture 也不是 autouse。**不能确认整个 pytest 进程零网络**，因为：

- 根 conftest 仍导入 `app.main` 等模块，并调用外部 `configure_logging`、`BugTracker`。
- W4 仅覆盖特定端口的连接事件，且 integration 默认豁免。
- 三门存档的 `blocked=0, advisory=0` 只支持该账本覆盖范围内的零记录。

若继续静态闭合，需要增加 `backend/app/main.py`、`backend/app/config.py`、`backend/app/core/logging.py`、`backend/app/core/bug_tracker.py`、`backend/tests/support/lifespan.py`，检查其初始化及传递导入；证明“存档那一次”整进程零网络则还需要对应运行观测，当前材料不足。

**③ 共享 7692 留数据的其他条件**

未提供 round-2 三种情形原文，以下不能保证与其完全去重：

- **写入组与清理组不一致：**测试 `:475-493` 查回、删除都限定预期 `physical_group_id`。若物理化发生回归，节点写进其他组，查回会红，清理却删除零条；当前参数转换正确，没有发现已发生此问题。
- **写入晚于清理完成：**若连接故障使客户端无法确认提交，而服务端事务在 verifier 删除之后才完成，节点仍可能留下。
- **verifier 转入 JSON fallback：**清理仍调用可回退的 `run_query`，因此 finally 执行完不等于真库 DELETE 已执行。

这些继续属于“未证明删除成功”的边界，不能由三门通过消除。

**④、⑤ 本轮代码与约束**

两段 `try/except ValueError` **都有意义**：第一段处理坏 IPv6 括号、非法 netloc 等解析错误；第二段处理非整数、越界端口。`urlsplit()` 已将 scheme 小写化，`.lower()` 冗余但正确，无须换成 `casefold()`。

独立 AST 对照确认：

- r3 的 `edges.py` **运行代码完全未变**。
- 相对基线，参数仍为 **14 键，全部对应值也一致**。
- 保留 `to_physical_group_id(resolved_group_id)`。
- except 确实只增加 `AttributeError`。

原 round-2 三条 LOW 可关闭：三门档末行是 `rc=0`；pyright 两态哈希分别匹配基线与最终提交，均无 `edges.py` 诊断；黑名单注释已纠正。负控哈希匹配 `9764cceb`，其生产运行代码及降级门测试与最终版一致。三门档自身未记录源码哈希，不能单独完成最终提交绑定；unit-close 则仍是 `rc=1`，但其 64 条失败／错误身份与基线清单一致。
