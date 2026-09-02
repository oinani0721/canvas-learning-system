# 冻结审查请求 — CARD-TEST-isolate-lifespan-R1

你是独立审查方。请对下面这一组**测试基础设施**改动做对抗性审查，并给出正式裁定。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2`
（只读；不要修改任何文件）。

## 0. 这是什么，为什么存在

这是一套**测试侧的安全护栏**，目标只有一个：让本机跑 pytest 时**不会连上开发者
自己的那台 Neo4j 开发库**（bolt 端口 7691/7687），也不会去动生产运行时数据文件。
它防的是「开发者手滑」，不是任何形式的攻击者。所有代码都在 `backend/tests/` 与
`backend/scripts/` 下，不在产品运行路径上。

上一轮（第八批）的独立审查给了 1 BLOCKER / 9 HIGH，指出这套护栏当时**证明不了
自己有效**：底层 socket 类型不经过它、拆掉后重装仍报告"已安装"、汇总数字口径太
松、静态检查可被普通改写骗过、shell 门的工具解析可被环境变量改写、BDD 的措辞比
它实际验证的东西宽。本轮就是逐条整改这些。

## 1. 审查范围（严格边界，超出范围的请不要计入裁定）

**在范围内**（本轮改动面）：

- `backend/tests/support/live_port_guard.py`
- `backend/tests/support/guard_plugin.py`
- `backend/tests/conftest.py` 中与 live-port guard 相关的 hook 与 fixture
- `backend/scripts/lifespan_isolation_negative_control.py`
- `backend/scripts/lifespan_isolation_guard_probes.py`
- `backend/scripts/lifespan_isolation_runtime_sha.sh`
- `backend/tests/bdd/test_health_bdd.py`、`backend/tests/bdd/features/health.feature`
- `backend/tests/unit/test_live_port_guard_contract.py`

**明确不在范围内**（已由卡文裁决，重复提出不计为发现）：

- `backend/app/main.py` 与任何生产 service —— 本轮**生产 lifespan 零改**是既定裁决。
- `backend/tests/integration/`、`backend/tests/e2e/` 的内容 —— 卡文裁决为"只登记、
  本轮不改"。它们按路径豁免（只记录不拦截），这是**有意的设计**，不是遗漏。
- CI workflow、OpenAPI、`.gitignore` —— 本轮禁改面。
- 两条**既存失败**：`test_metadata_subject_mapping.py::TestGetMetadata::test_metadata_group_id_format`
  与 `test_recommend_action.py::TestRecommendActionEndpoint::test_history_query_failure_graceful_degradation`。
  已在带入基线 `4a25578e` 上实跑复现（failure-set 两侧全等，2 failed / 265 passed），
  与本轮改动无关。
- 「子进程里的连接不受保护」「只按端口判定、不解析协议」「只比首尾两个时刻」
  等**已在 docstring 中明确声明的边界**。如果你认为某条声明**与实现不符**（说得比
  做到的宽），那是有效发现；如果只是"这个边界本身不够强"，请归到 LOW 或不提。

## 2. 本轮声称做到了什么（请逐条证伪）

(a) 只定点带入 `cdd77274`、`b54b4735` 两个 commit，无冲突。
(b) 负控子进程环境被钉死：清空全部 `NEO4J*`、重设为受拦端口的 loopback 地址 +
    假凭据；`W4_GUARD_REQUIRE_BLOCKED_TARGET=1` 让装门时就核对目标端口在射程内，
    不在就拒绝装门；另有一步用同一份环境实际构造 `Settings` 打印解析结果。
(c) 承重层换成 `sys.addaudithook("socket.connect")`，覆盖
    `socket.socket` / `_socket.socket` / `socket.SocketType` / `connect_ex`。
    `socket.socket.connect` 上的包装**降级为身份锚点**（不拦截、不记账，只委托），
    文档已明确声明它不承重。
(d) 每次 `install()` 与**每个用例边界**都验证门的真实身份：audit hook 用一次性
    token 走 round-trip（不是读布尔值）、belt 方法身份逐个比对、受拦端口集只许加
    不许减、uvloop 毒化在位。任一漂移抛 `GuardDrift`。
(e) `atexit`（最早注册⇒最后执行）里有一道最终总账：`pytest_cmdline_main` 返回之后
    的迟到连接会让进程 `os._exit(3)`；账本同时落盘供父进程复核。
(f) 负控判据改为「门汇总行**整行唯一**匹配，且 `total == blocked > 0`、
    `advisory == 0`、`unaccounted == 0`」，并与子进程落盘的账本交叉比对。
(g) 静态门重写为按作用域、按语句位置的绑定表：追踪真实 import 来源、语句顺序、
    重绑定；类体是独立作用域；属性式 `tc.TestClient(app)` 进入扫描。
(h) shell 门清掉 `BASH_ENV`/全部函数、恢复 builtin、外部命令走绝对路径、用参数
    展开代替 `dirname`、用 builtin 代替 `awk`/`grep`，并对常量串做**摘要自证**。
(i) BDD 的 Given 从 "the API server is running" 改为 route-availability 契约，并在
    步骤里实际断言路由已挂载。
(j) 负控子进程用 `sys.executable -m pytest`；变异前先跑同环境正控，要求三条全绿、
    rc=0、门账全零。
(k) 覆盖 `__index__` 端口对象、插件 import 期装门（门前窗口）、精确完整 nodeid 集合全等。
(l) 见下方证据清单。

## 3. 可复现的证据命令（只读，可自行重跑）

```
cd backend
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_negative_control.py --ast-negative-control
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_negative_control.py --ast-only
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_guard_probes.py
bash scripts/lifespan_isolation_runtime_sha.sh -- <python> -m pytest tests/api tests/unit/test_vault_scope_409.py -q -p no:cacheprovider
```

⚠️ 完整负控（不带 `--ast-only`）会**原地修改**一个 tracked 测试文件再还原。
你处于只读沙箱，请**不要**运行它；本仓库已附带它的完整输出。

## 4. 我特别希望你攻击的点

1. **(c) 的承重声明**：audit hook 真的覆盖了所有会发起 TCP 连接的路径吗？有没有
   哪条 Python 层的连接方式不触发 `socket.connect` 审计事件？
2. **(d) 的身份验证**：token round-trip 真的能证明 hook 在位吗？有没有它证明不了
   但确实已失效的情形？
3. **(e) 的窗口**：最终总账之后还剩多大的窗口？文档声明的残余窗口是否与实现一致？
4. **(g) 的静态分析**：还有哪些**普通写法**（不是刻意构造的攻击）会被误判为合规，
   或被误判为违规？误判为合规的算 HIGH，误判为违规的算 MEDIUM。
5. **(h) 的自证**：摘要自证能覆盖哪些劫持形态、覆盖不了哪些？
6. **文档与实现的口径差**：任何 docstring / 验收单里"说得比做到的宽"的句子。

## 5. 输出格式

先给一行总体裁定：`PASS` 或 `FAIL（n BLOCKER / n HIGH / n MEDIUM / n LOW）`。
然后逐条列 findings，每条给 `[级别] file:line` + 一句缺陷陈述 + 一个**具体的**
失败场景（什么输入/状态 → 什么错误结果）+ 建议。
最后给「放行维度」：你实际验证过、认为成立的面，以及你**没有**验证的面。

如果某一条你检查后认为确实成立，请明确写出来 —— 这份裁定既要抓问题，也要如实
记录哪些面已经站得住。
