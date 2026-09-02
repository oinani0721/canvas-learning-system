# 冻结审查请求 — CARD-TEST-isolate-lifespan-R1

你是独立审查方。请对下面这一组**测试基础设施**改动做对抗性审查，并给出正式裁定。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2`
（只读；不要修改任何文件）。

审查对象绑定：分支 `card/w4-safety-r2`，实现 commit **`b64a9c44`**（最终态）。
`git diff 4a25578e..b64a9c44` 是完整 diff；`git diff 86329c49..b64a9c44` 只看 round-1 之后的整改。

## ⛔ 这是第 2 轮：round-1 的 17 条已全部整改

你在 round-1 给出 FAIL（1 BLOCKER / 11 HIGH / 3 MEDIUM / 2 LOW）。**17 条全部逐条
整改，无一条以「已声明边界」推掉**。摘要（细节见 `_bmad-output/审查/CARD-TEST-isolate-lifespan-R1-验收单.md` §5）：

1. BLOCKER `NEO4J_TEST_URI` 子串判断 → 改为正面判据：解析 URI、端口必须存在且不在受拦集合。
2. 「所有 atexit 之后」不成立 → 最终结算进入即置**不可逆** `_FINALIZING`，此后命中就地 `os._exit(3)`；文档撤回该表述。
3. 自证不穿过阻断路径 → 改为**发一次真的 `socket.connect` 审计事件**，走完 `extract_port` → 受拦判定 → 抛，只在最后按哨兵主机名分流。
4. uvloop 毒化可删 → 承重换成 audit `import` 事件拦截；毒化检查改为「key 必须存在且为 None」；policy 复核并入边界自证。
5. shell 控制流劫持 → `env -u BASH_ENV -u ENV -u BASH_FUNC_*` 重新 exec（判据用 `case` 不用 `[`）+ `unalias -a`/`trap -`/函数表复核/builtin 身份复核/控制流自证。
6+7. `unlink` 误删 与 变异前无 CAS → **变异改到 tmp 隔离副本上做**，真实 tracked 文件与运行时文件全程不写。
8. `with client:` / `enter_context` 漏检 → 新增 TestClient **实例**来源追踪，覆盖三种形态。
9. 「最后一次绑定」不是控制流 → 改为「**所有**先于使用点的绑定必须一致」。
10. 工厂「存在一条 return 安全」→ 改为「**每一条** return 都解析为局部 app」。
11. `self.make()` 跨类污染 → 工厂身份按 `类名.方法名` 限定。
12. 正控只查 rc=0 → 正控出 junitxml，三条 exact nodeid **各一次且全 passed**。
13. 外层隔离/关键字/属性链误报 → 支配性外层 `with`、`app=` 关键字、属性链递归解析。
14. BDD `components` 不断言 → 改为必须存在、是 dict、且非空。
15. preflight 只核对 URI → 结构化输出 + 逐项精确比对七个解析值。
16. `ctypes` 绕过 → 承诺收窄进 docstring：「只覆盖 CPython 的 socket API」。
17. `__index__` TOCTOU → `port_is_trustworthy()`：端口不是**精确 int** 一律按受拦处理。

**本轮请重点做两件事**：
(1) 逐条复核上面 17 条是否**真的**关闭了（尤其 2/3/5/6/9 —— 这几条最容易「改了措辞没改行为」）；
(2) 找**整改本身引入的新缺陷**（更严的判据是否产生误拒？隔离副本是否引入了新的不一致面？
    `os._exit(3)` 是否会掩盖别的信息？`case` 判据是否还有别的劫持面？）。

当前门规模：探针 **27**、AST 负控 **17 绕过 / 9 验伪锚**、guard 契约单测 **35**。

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
(d) 每次 `install()` 与**每个用例边界**都验证门的真实身份：**发一次真的
    `socket.connect` 审计事件走完整条阻断路径**（不是读布尔值、也不是独立私有事件）、
    belt 方法身份逐个比对、受拦端口集只许加不许减、uvloop「key 必须存在且为 None」
    + policy 复核。任一漂移抛 `GuardDrift`。
(e) 最终结算（`atexit`）进入即置**不可逆** `_FINALIZING`，此后 audit 命中受拦端口
    就地 `os._exit(3)` —— **不**声称「在所有 atexit 之后执行」（LIFO 下更早注册的
    回调排在它后面）。账本同时落盘供父进程复核。
(f) 负控判据改为「门汇总行**整行唯一**匹配，且 `total == blocked > 0`、
    `advisory == 0`、`unaccounted == 0`」，并与子进程落盘的账本交叉比对。
(g) 静态门重写为按作用域、按语句位置的绑定表：追踪真实 import 来源、语句顺序、
    重绑定；类体是独立作用域；属性式 `tc.TestClient(app)` 进入扫描。
(h) shell 门用 `env -u BASH_ENV -u ENV -u BASH_FUNC_*` **重新 exec 自己**（判据用
    `case` 而非可被 alias 劫持的 `[`），再叠 `unalias -a` / `trap -` / 函数表复核 /
    builtin 身份复核；外部命令走绝对路径、用参数展开代替 `dirname`、用 builtin 代替
    `awk`/`grep`；并有**数据管道摘要自证**与**控制流自证**两道。
(i) BDD 的 Given 从 "the API server is running" 改为 route-availability 契约，并在
    步骤里实际断言路由已挂载。
(j) 负控子进程用 `sys.executable -m pytest`，**变异做在 tmp 里的 git-tracked-only
    隔离副本上**（真实树全程不写）；变异前先跑同环境正控，用 junit 要求三条 exact
    nodeid **各恰好一次且全 passed**、rc=0、门账全零、运行时零写。
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

⚠️ 完整负控（不带 `--ast-only`）会在 tmp 里建一份 git-tracked-only 的 backend 副本并在
**副本**上做变异（真实树不写）。你处于只读沙箱，仍请**不要**运行它；本仓库已附带完整输出。

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
