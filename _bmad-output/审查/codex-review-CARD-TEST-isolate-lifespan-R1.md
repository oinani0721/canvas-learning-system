FAIL（1 BLOCKER / 11 HIGH / 3 MEDIUM / 2 LOW）

冻结不放行。

## Findings

1. [BLOCKER] [backend/tests/support/live_port_guard.py:550](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:550) — `NEO4J_TEST_URI` 用字符串包含判断，漏掉驱动默认端口。场景：`bolt://127.0.0.1` 通过检查，但当前 Neo4j 6.1 驱动解析为 `127.0.0.1:7687`；在有意 advisory 的 integration/e2e/real_neo4j 用例中，guard 会委托真实连接，正中开发库。建议解析 URI 并要求显式、确认安全的测试端口（当前契约应为 7692），缺端口或解析不明一律拒绝。

2. [HIGH] [backend/tests/support/live_port_guard.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:618)、[guard_plugin.py:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/guard_plugin.py:27) — “最早注册、在所有 atexit 后执行”不成立。场景：先注册连接回调，再 import guard plugin；最终总账先看见零账并返回，旧回调随后被 audit 拦截，但进程仍 rc=0。已实际复现 `LATE_BLOCKED_AFTER_FINAL True`、exit 0。建议最终总账开始即置不可逆 finalization 标志，此后 audit 命中直接 `os._exit(3)`，并撤回“所有 atexit 之后”的文档表述。

3. [HIGH] [backend/tests/support/live_port_guard.py:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:340)、[live_port_guard.py:472](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:472) — token 只验证 selftest 分支，不验证 socket 阻断分支。场景：将 `extract_port` 改为恒返 `None` 后，`audit_hook_alive()` 和 `assert_guard_live()` 都通过，受拦随机 loopback 端口连接成功、账本仍全零。建议 liveness 自证必须实际穿过端口解析、判定和阻断路径，而非独立私有事件。

4. [HIGH] [backend/tests/support/live_port_guard.py:402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:402)、[live_port_guard.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:521)、[conftest.py:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/conftest.py:92) — uvloop 毒化可在用例内删除后恢复，且完整 policy 检查实际上没有调用。场景：删除 `sys.modules["uvloop"]`、导入并设置 uvloop policy、再恢复根 sentinel 为 `None`；边界自证通过，但 `uvloop.Loop` 连接受拦 listener 成功，账本为零、rc=0。建议拦截 uvloop import audit 事件、检查 key 必须存在且为 `None`，恢复调用 policy 检查；若要求强保证，应移除该依赖或下沉至 OS 层。

5. [HIGH] [backend/scripts/lifespan_isolation_runtime_sha.sh:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:62) — `BASH_ENV` 已注入的 alias、trap、readonly function 未被清除，摘要自证只覆盖数据管道，不覆盖控制流。场景：`BASH_ENV` 启用 alias expansion 并令 `[` 恒假；脚本未给 `--` 或命令，仍输出 `RUNTIME-FILES: unchanged`、exit 0。建议由清环境的外层 launcher 重新 exec bash，并清 aliases/traps、复核函数表和关键 builtin 身份，补 alias/readonly-function/EXIT-trap 负控。

6. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:914](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:914) — `absent → exists` 无法证明文件属于负控，却直接 `unlink()`。场景：负控期间另一个开发进程创建并写入 `bug_log.jsonl`，finally 会把真实数据当作本脚本产物删除，同时还能伪造“变异态确实写文件”的证据。建议在隔离副本运行完整负控；不能证明 ownership 时保留文件并 FAIL，禁止自动删除。

7. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:1028](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1028)、[negative_control.py:1144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1144) — tracked 测试文件在写入变异体前没有 CAS。场景：读取原文后，collect/正控运行期间开发者编辑目标文件；脚本随后用旧变异体覆盖，finally 又恢复旧原文，现有“还原前 CAS”看不出合法编辑曾存在。建议紧邻写入重新比较 exact bytes，并以锁和原子替换完成变异。

8. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:529) — AST 门只检查 `with` 项自身是 `TestClient(...)` 的调用。场景：`client = TestClient(app); with client:` 和 `ExitStack.enter_context(TestClient(app))` 均返回零违规；真实 TestClient 复现确实执行 startup/shutdown。建议扫描所有 TestClient 构造，并追踪实例到 `with`、`__enter__` 和 ExitStack。

9. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:473) — “文本上最后绑定”不是控制流分析。场景：函数内先令 `app=production_app`，再在 `if use_local:` 中赋 `FastAPI()`；`use_local=False` 时启动生产 app，扫描器却按后一个文本绑定判安全。建议在分支汇合点合并全部可达来源；仅所有路径均 local 时放行。

10. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:435) — 工厂只要曾给变量赋局部 FastAPI，就会把该变量的返回认成 local。场景：`a=FastAPI(); a=production_app; return a` 被标为安全，调用方裸启生产 lifespan。建议逐个 return 做 reaching-definition，并要求所有可达返回值均可证明为 local。

11. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:221)、[negative_control.py:384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:384) — `self.make()` 只按全模块方法名判定。场景：Class A 的 `make` 返回 local app，会污染 Class B 同名、返回 production app 的 `make`；扫描零违规。建议用类、作用域和定义节点限定工厂身份，receiver 不可证明时返回 unknown。

12. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:1106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1106) — 正控只检查 pytest rc=0，没有证明“三条全绿”。场景：三条用例在 client fixture yield 后 `pytest.skip()`，正控仍是 rc0/零门账；变异态可在 setup 阶段按预期红，最终形成假 PASS。建议正控也生成 JUnit，并要求三个 exact nodeid 各一次、无 skipped/error/failure，同时检查 collect rc。

13. [MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:565) — 安全普通写法会被误报。场景：外层 `with no_lifespan(app):` 包住内层 `with TestClient(app):`，真实 lifespan 未启动，但扫描报违规；`app=` keyword 和 `fastapi.testclient.TestClient(...)` 也误报。建议识别支配性的外层隔离、对象别名、keyword 参数及完整属性链。

14. [MEDIUM] [backend/tests/bdd/test_health_bdd.py:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/bdd/test_health_bdd.py:62) — “contains component status” 在字段缺失时不做任何断言。场景：响应仅为 `{"status":"healthy"}`，第二个 BDD 场景仍绿，与字段形状契约不符。建议先断言 `components` 存在，再检查 dict 及必要字段。

15. [MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:977](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:977) — preflight 只精确核对 Neo4j URI；LanceDB 只要求非空，Canvas 路径完全未核对。场景：配置解析漂移到任意非空 live LanceDB 或真实 vault，前置检查仍通过，变异 lifespan 可写生产数据。当前版本实测解析到临时路径，但门没有锁住这一性质。建议结构化输出并逐项精确比较 URI、凭据、vault、两项 LanceDB 路径。

16. [LOW] [backend/tests/support/live_port_guard.py:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:340) — audit hook 不是进程级 TCP 防火墙。场景：`ctypes.CDLL(None).connect(...)` 或原生扩展直接调用 libc，可连接受拦 listener 且账本为零。当前 Neo4j 驱动使用 CPython socket，因此按非攻击者威胁模型定 LOW；建议将承诺收窄到 CPython socket API，或使用 OS 层出站约束。

17. [LOW] [backend/tests/support/live_port_guard.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:303) — stateful `__index__` 会发生二次求值 TOCTOU。场景：第一次返回受拦 listener 端口供 CPython 构造 sockaddr，第二次给 audit hook 返回 1；连接成功、账本零。已复现两次求值及 rc0。建议非 exact-int 端口对象直接 fail closed，或避免对原对象二次求值。

## 放行维度

已验证成立：

- 分支和 HEAD 正确：`card/w4-safety-r2` / `86329c49`；范围内文件与该 commit 一致。
- `(a)` 两组 twin commit 的 stable patch-id 分别相等；内容等价成立。“无冲突”是历史过程，无法由最终对象独立证明。
- `_child_env()` 确实清空全部 `NEO4J*` 并钉死 URI、测试 URI和假凭据；当前 Settings 解析值正确。
- 标准 `socket.socket`、`_socket.socket`、`SocketType`、`connect_ex`、稳定 `__index__` 探针成立。
- 汇总行唯一解析、`total == blocked > 0`、零 advisory/unaccounted 和账本四元组交叉检查的代码口径成立。
- BDD Given 确实断言 `/api/v1/health` 已挂载。
- 实跑结果：AST 负控 10/10、正例 5/5；仓库 AST 0/371；guard probes 19/19；新增合同和 BDD 29 passed；runtime 裁判为声明中的 2 failed / 265 passed、门账全零、三文件 unchanged。

未验证：

- 按要求未运行会原地变异 tracked 文件的完整负控。
- 未在 `4a25578e` 重新跑基线，故“两侧 failure-set 全等”只核对了附带证据；目标侧两条失败名称已复现。
- 未跑整套 CI、integration/e2e 内容或生产入口；没有连接真实 7687/7691。
- 子进程、预建连接、非目标端口和 plugin import 前窗口仍按声明边界保留。
- 当前整个工作树并非 clean：审查材料下有 2 modified、2 untracked；范围内代码 clean，我以 commit exact bytes 审查，未把审查封装器产物计入 finding。
- 当前会话未暴露 `graphiti-canvas`，无法执行项目要求的 Graphiti 查询。


