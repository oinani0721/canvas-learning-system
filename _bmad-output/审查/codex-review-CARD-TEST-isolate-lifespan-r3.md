总体裁定：**FAIL（1 BLOCKER / 9 HIGH / 6 MEDIUM）**。当前不能合卡或标记完成。

### Findings

[BLOCKER] [backend/scripts/lifespan_isolation_negative_control.py:484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:484) 变异子进程继承调用者全部环境，却未钉死 `NEO4J_URI`。实测 `NEO4J_URI=bolt://127.0.0.1:45678` 会被 `Settings` 原样采用；摘掉 `no_lifespan` 后会先尝试真实连接/DDL，7691/7687 门不拦，脚本只会事后因 `blocked=0` 失败，runtime SHA 也看不到数据库侧改动。建议清理全部 Neo4j 环境并强制使用确定受拦的 loopback URI、假凭据及禁止豁免模式，再允许变异。

[HIGH] [backend/tests/support/live_port_guard.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:53) round-2 H5 是表面整改：`_socket_mod` 实际仍是高层 `socket` 模块，`:293` patch 的是 `socket.socket` 子类，不是 `_socket.socket`/`socket.SocketType`。Python 3.14 实测直接 `SocketType.connect()` 完成回环连接，`attempts=0 blocked=0`。建议以 `sys.addaudithook("socket.connect")` 或 OS/父进程网络隔离承重，并加入 `_socket.socket`、`SocketType` 实连负探针；仅改 import 会因 C 类型不可变而失败。

[HIGH] [backend/tests/support/live_port_guard.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:291) `install()` 只信 `STATE.installed`。实测安装后把 `connect` 恢复为原函数，再调用 `install()`，结果仍为 `installed=True`、`connect_guarded=False`；session fixture 也只检查布尔值。建议每次安装和用例边界验证真实方法身份，漂移即失败；更稳妥的是换成不能被普通 monkeypatch 拆除的承重层。

[HIGH] [backend/tests/conftest.py:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/conftest.py:171) session 总账仍有 `pytest_cmdline_main` 返回后的盲区。复现得到 `PYTEST_MAIN_RC 0`，随后 atexit 连接被拦成 `blocked=1/unaccounted=1`，最终进程仍 exit 0。连接虽被挡住，但“任何未结账尝试都令测试失败”的承诺不成立。建议由外层父进程收口，或增加真正位于所有清理动作之后且能强制非零退出的最终总账。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:512](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:512) 正证据只解析 `total/blocked` 并要求 `blocked>=1`；`attempts=7 (blocked=3, advisory=4, unaccounted=0)` 会通过该检查，而 advisory 已调用原始 connect。建议唯一、整行解析最终汇总，并要求 `total == blocked > 0`、`advisory == 0`、`unaccounted == 0`；负控运行时应彻底禁用豁免。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:153) round-2 H7 未闭环：`helper_aliases` 是全模块名字集合。真实 import helper 后，在局部重定义同名 no-op `no_lifespan`，AST 仍判合法。建议按词法作用域、语句位置和实际绑定追踪 helper；任何重绑定必须使 import provenance 失效。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:165) round-2 H6 仍 fail-open：索引先扁平扫描整个作用域，且无条件信任任何名为 `FastAPI` 的调用。`with TestClient(app)` 后置 `app=FastAPI()`、class body 污染、伪造本地 `FastAPI()` 均被误判为局部应用。建议做按语句位置的 reaching-definition 分析，并验证 `FastAPI` 的真实 import 来源；不能证明时一律违规。

[HIGH] [backend/scripts/lifespan_isolation_negative_control.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:125) `_call_name()` 只识别 `Name`；`import fastapi.testclient as tc; with tc.TestClient(app)` 完全不进入扫描。建议解析来源明确的 `Attribute`、赋值别名和 Starlette/FastAPI TestClient 导入链。

[HIGH] [backend/scripts/lifespan_isolation_runtime_sha.sh:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_runtime_sha.sh:36) round-2 H10 仅清理 `shasum/awk/grep` 函数。导出假 `dirname` 后，脚本监视 `///data/...` 等错误路径，三项均 absent，rc=0 且输出 `unchanged`；伪造 `printf` 也能令摘要全为零。建议门内命令全部使用绝对路径或 `builtin`，清除 `BASH_ENV`/相关导出函数，并仅给 wrapped command 恢复调用者 PATH。

[HIGH] [backend/tests/bdd/test_health_bdd.py:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/bdd/test_health_bdd.py:22) 根 `client` 已无 lifespan，但 BDD 仍声明 “the API server is running” 和系统 healthy。设置必令真实 startup 在 `app/main.py:98-106` 中失败的冲突 LanceDB 环境后，两条 BDD 仍 `2 passed`。round-1 H5 只诚实化 smoke，遗漏了该根 client 消费者。建议改成明确的 route-availability 契约，或使用安全隔离外部依赖但真实执行 startup 的专用测试。

[MEDIUM] [backend/tests/support/live_port_guard.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/live_port_guard.py:218) `extract_port()` 只接受 `int`，但 CPython socket 接受实现 `__index__` 的端口对象；回环实测连接成功且总账为零。当前 Neo4j/httpx 通常传内建整数，故定 MEDIUM。建议用 `operator.index()` 规范化。

[MEDIUM] [backend/tests/support/guard_plugin.py:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/support/guard_plugin.py:25) 显式插件直到 `pytest_configure` 才安装；autoload、`PYTEST_PLUGINS` 和 initial conftest import 位于其前。根 conftest 正常发现时可补上，但独立 belt 仍有门前窗口。建议插件 import 时立即安装，负控子进程清空 `PYTEST_PLUGINS` 并禁用不必要的 autoload。

[MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:458](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:458) 固定 nodeid 用 substring 而非逐字匹配；三个名字加任意后缀后仍满足“身份钉死”。建议常量保存三个完整 nodeid，并直接做集合全等。

[MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:443) 变异前只 collect，不要求三条原始用例全绿。原测试若已失败，而变异后 longrepr 又附带 live-port 文案，仍可能满足现有红因裁判。建议先跑同环境正控，要求三条全绿、rc=0、attempts=0，再变异。

[MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/lifespan_isolation_negative_control.py:407) 原始字节先保存，数分钟后无条件写回；期间的合法并发编辑会被静默覆盖。建议在隔离 worktree 变异；若必须原地，至少增加排他协调、写前及恢复前 CAS，检测到并发版本时保全双方并失败。

[MEDIUM] [_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md:190](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md:190>) 当前没有 subject 含本卡标记的 commit；审查对象实际是 `HEAD 2cacbb0c + 17 个 modified 文件 + untracked 落物`。无法按提示从批次 commit 重建可复现边界。建议先提交实现，再以独立 docs commit 回填实施 SHA 和审查 SHA。

### 放行维度

- **PASS — 13 文件语义**：定向运行 `212 collected`，结果 `202 passed / 10` 条已登记失败；`ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。vault 409、chat 成功路径、mastery store/真实 engine、deep-monitoring 精确采集值均有效，没有恒 503/恒空退化。
- **PASS — 已修 guard 子面**：常规 uvloop 前后时序、ContextVar generation、裸线程/线程池/portal 归属、xfail 强制失败、setup/finalizer 结账、标准路径 advisory 相对化均有效。当前仓库没有依赖 `connect_ex` errno 的 pytest/app 调用方。
- **PASS — 根 conftest 其余影响**：bug_tracker 替换命中 `app.main` 实际消费别名；dependency override 保存/恢复顺序正确。health、production-bugs、smoke、CORS、ping、security、rollback 未发现 lifespan 产物依赖；例外仅为上述 BDD。
- **PARTIAL — 负控/AST/SHA**：锚点当前唯一；JUnit 完整 failure 正文、rc==1、红集全等、普通异常及 INT/TERM/HUP/QUIT 恢复、before snapshot 检错、子壳隔离均有效。但上述绕过使整体控制不能放行。
- 未运行会原地改 tracked 文件的完整负控；运行了 `--ast-only`、内存 AST 反例、socket/pytest 生命周期探针和 SHA shell 注入探针。未修改工作树。integration/e2e 按卡文未复查；Graphiti 工具本轮未暴露。已登记的 health 响应时间阈未重复报告。


