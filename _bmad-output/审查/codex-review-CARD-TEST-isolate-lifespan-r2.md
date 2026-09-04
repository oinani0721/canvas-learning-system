总体裁定：**FAIL（0 BLOCKER / 10 HIGH / 5 MEDIUM / 1 LOW）**。

审查现场为 `card/w4-micro`，HEAD `2cacbb0c`。CARD-TEST-isolate-lifespan 当前仍是未提交工作树改动。

### Findings

[HIGH] [backend/tests/conftest.py:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/conftest.py:145) 哨兵把 xfail 用例的 report 改成 FAILED，却保留 `wasxfail`；实测 `blocked=1, unaccounted=0`、终端显示 FAILED，但 `pytest.main()` 返回 0，因为 pytest 不把带 `wasxfail` 的 report 计入失败。建议强制失败时删除 `wasxfail`，并在 session 收口时只要 `STATE.blocked > 0 && status == 0` 就返回非零，避免已结账记录从总账消失。

[HIGH] [backend/tests/conftest.py:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/conftest.py:89) `pytest_unconfigure` 在 `pytest_cmdline_main` wrapper 恢复前卸门；迟到非 daemon 线程实测可在同一 pytest 进程退出前连接本机临时端口，结果 `attempts=0, rc=0`。`guard_plugin.py:29` 有同样问题。建议 CLI 测试进程保持门到进程退出，并显式 stop/join 后台线程；不能先恢复 socket 再结账。

[HIGH] [backend/tests/support/live_port_guard.py:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:121) ContextVar 豁免可被复制后永久保留。实测在 `begin_item(exempt=True)` 后复制 context、再 `end_item()`，旧 context 仍能连接临时端口，并记成 `advisory=1, blocked=0`。这与 line 178 宣称“迟到连接归 unknown”矛盾。建议 ContextVar 存 generation/token，STATE 同时维护当前有效 token；`end_item` 撤销后，旧副本一律 blocked。

[HIGH] [backend/tests/support/live_port_guard.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:240) uvloop 若在 `install()` 前已加载，代码不会毒化它，只等 session fixture 才报错；此前 collection/import 阶段已经存在连接窗口。fresh-process 临时端口实测 uvloop 成功连接且 `STATE.total=0`。建议 `install()` 发现已加载 uvloop 或 uvloop policy 时立即失败；若要求覆盖早于 pytest 插件加载的阶段，需要 OS 层网络隔离。

[HIGH] [backend/tests/support/live_port_guard.py:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:251) 门只 patch Python 的 `socket.socket` 子类；Python 3.14 中公开的 `socket.SocketType`/`_socket.socket` 是未修改的基类。临时端口实测可直接连接，`attempts=0`。当前 Neo4j/httpx 路径未使用它，但“本进程硬门”主张不成立。建议下沉到 OS/firewall/syscall 层；至少登记该边界并加入负探针。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:258) H8 未真实修复：注释声称 unknown 按违规处理，实际 `origin != _ORIGIN_MAIN` 全部放行。`target = app; TestClient(target)`、`import app.main; TestClient(app.main.app)`、晚绑定和 class-scope 污染均实测 ALLOW。建议仅明确证明为真实 FastAPI 局部实例时放行；unknown 必须违规，并按语句顺序传播赋值来源。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:265) H9 只验证 helper 名字、顺序及同名参数，不验证来源；本地定义一个什么也不做的 `no_lifespan` 即可让裸 `app.main.app` 通过 AST 门。建议追踪 helper 必须导入自 `tests.support.lifespan`，支持合法别名，并拒绝局部重绑定/未知来源。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:451) 红因裁判是 fail-open：只有匹配 `FAILED nodeid - reason` 的行才可能进入 wrong 集；没有 reason 的 `FAILED nodeid` 被直接算作正确原因。三个长 nodeid 在 pytest 80 列输出中会省略 reason，因此验收单的“三条逐项同因”并未被证明。建议输出 JUnit XML/结构化报告，要求每个预期 nodeid 的 failure 正文都包含 `BLOCK_REASON`；缺正文必须失败。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:349) 原地变异仅 trap SIGTERM/SIGINT；SIGHUP/SIGQUIT 会直接终止，`finally`/`atexit` 不运行，留下裸 TestClient。目标文件原本已经是 `M`，残留后 `git status` 也不会“一眼可见”新增异常。建议至少捕获 HUP/QUIT；更稳妥的是隔离 worktree/副本中变异。

[HIGH] [backend/scripts/lifespan_isolation_runtime_sha.sh:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_runtime_sha.sh:69) SHA 门继续信任调用者的 shell function/PATH。导出一个返回 64 个零的 `shasum` 后，脚本正式输出 `RUNTIME-FILES: unchanged` 并返回 0，文件真实变化也可被隐藏。建议使用锁定的绝对系统工具路径，并清除同名导出函数；wrapped command 的 PATH 与门自身工具解析应隔离。

[MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:381) M5 只要求红集等于动态预采集集，没有锁定三条指定 nodeid 的固定身份和数量；删掉或改名一条后，剩余 1–2 条仍可能自洽 PASS。建议定义完整的三个 nodeid 常量并严格比较。当前现场收集结果确为预期 3/19。

[MEDIUM] [backend/scripts/lifespan_isolation_runtime_sha.sh:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_runtime_sha.sh:85) 前置 snapshot 失败不会阻止 wrapped command，因为此时未启用 `set -e`；实测先输出 `GATE-BROKEN`，随后仍执行 `WRAPPED-RAN`，最终才返回 1。建议在运行命令前显式检查 `BEFORE="$(snapshot)"` 的状态。

[MEDIUM] [backend/tests/test_deep_monitoring.py:99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/test_deep_monitoring.py:99) M2 仍是假阴：Prometheus Gauge 在未采集时已暴露 `0.0` 样本；把 `collect_metrics()` patch 成 no-op 后，lines 105/108 的数字正则仍全部通过。建议把 psutil 返回值固定为非默认哨兵值并断言精确 exposition，或 spy 两个 Gauge 的 `.set()` 参数。

[MEDIUM] [backend/tests/smoke/test_health_smoke.py:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/smoke/test_health_smoke.py:19) H5 诚实化不完整：文档已声明不是 boot test，但 pytest 节点仍叫 `TestAppBoot::test_app_starts`，违反 DD-13 名实一致。建议改成 `TestRouteAvailability::test_health_route_responds`，不要重新开启 lifespan。

[MEDIUM] [_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md:166](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md:166>) M7 尚未落实：`git log` 没有本卡/批次 commit，HEAD 是 CARD-TEST-bark-autostub，全部实现仍为 modified/untracked。当前审查对象缺不可变锚点。建议先提交带批次标记的实现 commit，再以独立 docs commit 回填 SHA 并复跑裁判。

[LOW] [backend/tests/unit/test_mastery_api.py:41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/unit/test_mastery_api.py:41) fixture 新建并返回的 `engine` 从未注入 `_engine_instance`；路由实际使用随后惰性创建的另一个实例，27 个测试也都把该返回值解包为 `_`。建议删除死对象/第三返回项，或明确注入并断言实例身份。

### 已核验并放行

- 393 用例终验重跑：`382 passed / 11 failed`，失败集与验收单一致；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`，三个运行时文件 SHA unchanged，`git diff --check` 通过。
- `no_lifespan` 只替换 `router.lifespan_context` 并在 `finally` 恢复；13 个文件仍走真实 app 路由。vault_scope 38 条、mastery 27 条均通过且 attempts=0。
- H4/H6/M1/M3 主体有效：健康与 production-bug 请求期 DI 已隔离；chat AsyncMock 接口和 200 强断言有效；bug_tracker 仅替换 `app.main` 别名；mastery store getter 和 engine 单例恢复命中真实消费点。
- 标准 `socket.create_connection`、默认 asyncio、SSL、requests/httpx、当前 Neo4j 驱动、裸线程及 ThreadPool 均经过包装；仓内没有依赖 `connect_ex` errno 的调用方。
- 路径 advisory 使用相对化后的首段精确匹配；rootdir 外路径 fail-closed，未发现 substring 误豁免。
- setup 期记录可在 call/teardown 结账，同步 fixture finalizer 可在 teardown 结账；普通 unknown/session 账能令 rc=3。
- B1 的显式 `-p guard_plugin`、PYTHONPATH 注入和清除 PYTEST_ADDOPTS 有效；H7 的普通异常、KeyboardInterrupt、TERM/INT 恢复有效；H10 的空/非法 digest 检查有效；H11 的 `exit`/`eval` 子壳隔离有效。
- 按要求未重复报告两个 `test_health` 响应时间阈问题。rollback 用例的失败来自仓内缺少 `src.rollback`，发生于 client/lifespan 之前，不归因本卡。

完整负控未执行：其原地变异恢复和红因裁判已被上述反例证伪，继续运行不能提供可信闭环且会扩大脏工作树风险。本会话也未暴露 AGENTS.md 要求的 Graphiti/Sequential Thinking MCP；报告以当前工作树的静态检查、定向 pytest 和安全临时端口探针为依据。


