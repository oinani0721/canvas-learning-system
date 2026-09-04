FAIL（1 BLOCKER / 9 HIGH / 8 MEDIUM / 2 LOW）

## Findings

1. [BLOCKER] [live_port_guard.py:638](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:638) — `NEO4J_TEST_URI` 的正面判据仍接受端口 `0`。场景：`bolt://127.0.0.1:0` 通过 session 预检，Neo4j driver 将 `0` 归一化为默认 `7687`，integration/e2e 又在 `is_exempt()` 走 advisory、不抛，因而可能真实连接开发库。建议拒绝 `port <= 0` 及越界端口，最好只允许测试端口 `7692`，并按 driver canonical address 加契约测试。验收单 §7.6c-bis 对 A 的“已自我证伪”漏算了 exemption 路径。

2. [HIGH] [live_port_guard.py:318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:318) — tuple 子类通过可重载的 `len()`/`address[1]` 取端口，与 CPython socket 读取底层 tuple 槽的语义不一致。场景：底层端口为 `7691`，但 `__getitem__(1)` 返回精确整数 `1`，guard 判安全且账本为零，C socket 仍使用 7691。建议用 `tuple.__len__`/`tuple.__getitem__`；不能直接拒绝 tuple 子类，因为 Neo4j `Address` 本身也是 tuple 子类。

3. [HIGH] [live_port_guard.py:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:392) — 两条 `os._exit(3)` 路径在退出前执行可能失败的 `repr`、`print` 或 I/O。场景：较晚注册的 atexit 回调先关闭 `stderr`，finalizer 置 `_FINALIZING` 后，较早回调发起受拦连接；诊断先抛 `ValueError`，`os._exit` 不可达，实测可得到 rc=0。建议所有诊断置于 best-effort `try`，以 `finally: os._exit(3)` 无条件收口。

4. [HIGH] [live_port_guard.py:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:392) — `_FINALIZING` 检查、`STATE.record()` 和 ledger snapshot 没有同锁线性化。场景：worker 读到 False 后暂停，finalizer 置 True 并取得零账快照，worker 随后落账且异常被调用方吞掉，最终 `blocked=1/unaccounted=1`、rc=0。该复现不需篡改内部状态，因此 §7.6f 对 F 的降格不成立。建议把 finalizing 纳入 `STATE`，同锁执行两侧状态转换。

5. [HIGH] [lifespan_isolation_runtime_sha.sh:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:112) — Bash 3.2 的 `compgen -e` 不枚举原始环境中的 `BASH_FUNC_name%%`，声称的导出函数清洗不成立。只读复核得到 `compgen=0`、`/usr/bin/env=1`。场景：导出的 `builtin` 函数穿过 re-exec，伪造或隐藏后续 `compgen`、函数表和控制流检查，使文件已变化仍可输出 `unchanged`、rc=0。建议由非 Bash 启动器过滤原始环境，或使用 `env -i` 加明确允许表，并补 exported `builtin`/`exec` 探针。

6. [HIGH] [lifespan_isolation_negative_control.py:489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:489) — TestClient provenance 被压成一个字符串和 app 名，无法表达分支来源或对象身份。场景：production client 在条件分支中可能被 local client 覆盖，合流结果为 `unknown`，而 line 962 对 unknown 直接放行；或旧 client 包住 production app，同名变量随后重绑 local app，门错误认为外层隔离覆盖了旧对象。建议保留候选来源集合和构造点 definition token；候选中存在 main client 时必须证明隔离的是同一对象。

7. [HIGH] [lifespan_isolation_negative_control.py:669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:669) — 自建包装器资格是“存在一个受保护 yield”的函数名级摘要，不是“每条可达 yield 均受支配”。场景：一个分支在 `no_lifespan` 内 yield，另一个分支裸 yield，裸分支仍被判安全；安全同名定义后再重定义为裸 wrapper 也会继承旧资格。建议逐 definition 做控制流支配检查，并按使用点解析实际绑定。

8. [HIGH] [lifespan_isolation_negative_control.py:1050](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1050) — `enter_context` 只扫描第一个位置参数。场景：合法的 `stack.enter_context(cm=TestClient(app))` 中 `node.args` 为空，直接漏检；任意对象只要方法同名又会被反向误认作 ExitStack。建议支持 `cm=`，并追踪 receiver 确为 `ExitStack`/`AsyncExitStack`。

9. [HIGH] [lifespan_isolation_negative_control.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:400) — “所有先于使用点的绑定必须一致”只登记了少数 statement 类型。场景：`app=FastAPI()` 后用 `app := production_app` 重绑，或用同一 `with` 前项、pattern、实例属性覆盖 `self.make`，分析器仍沿用旧安全来源并返回零违规。建议补齐 `NamedExpr`、pattern、with-item 逐项绑定和属性重绑定，或收窄该声明。

10. [HIGH] [lifespan_isolation_negative_control.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1025) — with 扫描只处理根节点为 Call/Name/部分 Attribute 的形态，与顶层“源码里没有裸 TestClient(app.main app)”口径不符。场景：`with (TestClient(app) if use_real else nullcontext()):` 的真分支运行 production lifespan，但当前 `analyze_source()` 返回零违规。建议对 `IfExp`、`NamedExpr` 等上下文结果做 union provenance，未知候选须 fail-closed。

11. [MEDIUM] [live_port_guard.py:382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:382) — 实现比“只拦 TCP”声明更严，没有检查 socket family/type。场景：UDP `SOCK_DGRAM.connect(...,7691)` 也会被记为 Neo4j 连接并令进程 rc=3。建议限定 `AF_INET/AF_INET6 + SOCK_STREAM`，或把契约改成“所有协议的目标端口”。

12. [MEDIUM] [live_port_guard.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:487) — “每次 install 任一漂移均抛 GuardDrift”不成立。场景：首次安装后删除 `sys.modules["uvloop"]`，再次 `install()` 会先重新毒化，再执行断言，静默成功。import audit 仍承重，所以不是直接旁路，但行为与声称不符。建议已安装分支先断言，或明确声明 install 会自愈该项。

13. [MEDIUM] [lifespan_isolation_runtime_sha.sh:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:273) — 注释声称 Bash 3.2 的 `compgen -G` 已按 collating sequence 排序，实测不成立。场景：两个以上 journal 的 path→bytes 集合没变，但目录枚举顺序变化，前后快照字符串不同而误报 `CHANGED`。建议使用锁定 locale 和绝对路径的 `sort`，或按 path→digest 映射比较。

14. [MEDIUM] [lifespan_isolation_runtime_sha.sh:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:243) — `vault_index_pending*.jsonl` 比声称的“旧固定名＋新 `__<key>` 名”更宽。场景：普通代码写 `vault_index_pending_backup.jsonl` 或 `vault_index_pending.tmp.jsonl`，shell 门无谓报 CHANGED，Python 负控还可能把旁文件误当 journal 承重证据。建议把旧名列为精确固定项，新名只用 `vault_index_pending__*.jsonl`；当前模式不会匹配 `.jsonl.tmp` 这种扩展名之后的派生物。

15. [MEDIUM] [lifespan_isolation_guard_probes.py:790](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_guard_probes.py:790) — 29 条探针没有覆盖 shell glob 的 absent→present 承重分支，唯一 CHANGED 锚只写固定的 `bug_log.jsonl`。场景：删除或缓存 shell 中的 glob 重展开，29 probes、Python 负控和 expected-unchanged judge 仍可能全绿，新 journal 却漏检。建议在 fake backend 新建 `vault_index_pending__probe.jsonl`，要求唯一 CHANGED 且 rc=1。

16. [MEDIUM] [lifespan_isolation_negative_control.py:598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:598) — E 的永久失格名单在 factory provenance 固定点收敛前不可逆生效，引入新误拒。场景：安全前向工厂 `outer() → inner() → FastAPI()` 首轮无法解析 inner，outer 被永久失格；早期不安全定义被后续安全定义覆盖也仍失格。建议先完成固定点，再按定义位置和 reaching definition 判定。

17. [MEDIUM] [lifespan_isolation_negative_control.py:881](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:881) — 多种普通且运行时安全的隔离写法被误拒。场景：`no_lifespan(app=app)`、helper yield alias，以及 `client=TestClient(app); with no_lifespan(app), client:` 均安全，但分析器报违规。建议支持 helper keyword、同对象 alias 和同一 with 的前置 sibling 覆盖。

18. [MEDIUM] [验收单.md:22](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/CARD-TEST-isolate-lifespan-R1-验收单.md:22>) — 冻结文档和原始证据没有统一绑定 `de57e375`：表头仍称 `2b160897` 为实现最终态，前表仍是 17/9/371，raw receipt 最后提交于 `0684e0fa`，仍记录旧固定 journal；[conftest.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/conftest.py:184) 和 guard 标题还残留“atexit LIFO 最后执行/所有 atexit 之后”。场景：按表头或 raw receipt 签字，会把 compgen/E 修复后的状态误当成已在最终 SHA 实跑。建议统一 SHA、规模、LIFO、隔离副本和 glob 口径，并附明确绑定 `de57e375` 的原始回执。

19. [LOW] [lifespan_isolation_guard_probes.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_guard_probes.py:78) — 父进程只核第二个 token 为 `PASS`，不核 probe name。场景：子探针误输出另一探针的 PASS 标签，当前探针仍被记成功。建议精确匹配 `PROBE-RESULT: PASS <expected-name>`。

20. [LOW] [lifespan_isolation_negative_control.py:1100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1100) — E 的同名工厂反例未进入常设 `_AST_MUST_FLAG`。场景：删除 `disqualified_factory_keys` 修复后，当前 22/11 自证仍可全绿。建议把 E 及本轮 AST HIGH 的最小反例加入永久 must-flag。

## 已知处置项与 17 条整改复核

- C：精确问题已关闭。`app/main.py` 字面匹配自检可在 wrapped command 运行前抓住损坏/禁用的 `compgen`；但不覆盖 HIGH #5 的 `builtin` 污染，也没有证明实际 glob 分支承重。
- B：只有“脚本第一行前立即 exit 无法由脚本自防”成立；“非立即污染均被 re-exec 清除”不成立。
- D：归入容器/解包元素级 provenance 盲区是恰当的，简单把 `any` 改成 `all` 不能解决元素来源传播。
- E：原“安全定义后同名不安全定义”反例已关闭，但修复产生 MEDIUM #16，且没有 LOW #20 的永久验伪锚，只能裁为 PARTIAL。
- F：降格不成立；HIGH #4 是正常线程调度与 atexit LIFO 可达的复现，不依赖篡改状态。

Round-1 17 条中：

- 已关闭原始反例：#3、#4、#6、#7、#10、#11、#12、#14、#15、#16。
- 部分关闭：#8、#13、#17。
- 未关闭：#1、#2、#5、#9。

## 放行维度

以下面已实际核对并认为成立：

- 当前分支为 `card/w4-safety-r2`；`de57e375` 是所述实现态，当前 `HEAD=1a4059b5…`；`de57e375..HEAD` 排除 `_bmad-output/` 后代码 diff 为空。
- CPython `socket.socket`、`_socket.socket`、`SocketType` 的 `connect/connect_ex`，以及本机上委托它们的 `socket.create_connection`、selector asyncio、SSL/HTTP/Neo4j 路径会触发 `socket.connect` audit event。
- 不覆盖已建连接复用、子进程新解释器、uvloop/libuv、ctypes/cffi/原生 syscall、`sendto/sendmsg`；这些边界基本与 docstring 一致。
- `assert_guard_live()` 能证明合成审计事件经过 audit 分发、普通 tuple/int 端口提取、blocked membership 和 sentinel 异常，并核 belt identity、受拦集合下界及 uvloop key/policy；它不能证明真实 C 调用、tuple 子类、`STATE.record`、豁免、账本、finalizer或两个边界之间持续不漂移。
- 汇总行唯一解析、`total == blocked > 0`、零 advisory/unaccounted、ledger 交叉比对的代码结构成立。
- tmp tracked-only 隔离副本结构性消除了真实树原地变异、CAS 和误删；正控 JUnit 的 exact nodeid 多重集、全 passed、零账/零运行时写判据成立。
- BDD route-availability、`components` 必须为非空 dict 的实现成立。
- (m) 静态成立：`test_vault_scope_409.py` 的唯一 client 由先进入的 `no_lifespan(app)` 包住。
- (n) 静态成立：两个 autouse fixture 无论合法执行顺序都在 test call 前完成，`reset_singleton` 不构造实例；函数体内 import 会在每次 `get_review_service()` 调用时读取被 monkeypatch 的源命名空间。
- glob 空展开本身不会把简单 absent→present 或 present→absent 判成 unchanged：每次重新展开会使整行出现/消失。仍会假绿的是“创建后在第二次快照前删回”（已声明首尾边界）、正式命名漂出 pattern、或 glob 展开链被破坏；排序问题则会造成反向误报 CHANGED。
- `os._exit(3)` 覆盖原退出码并跳过余下 callback 是可接受的 fail-closed 取舍；缺陷是当前实现无法保证它必然可达。

未实际核的面：

- 按要求未运行完整负控；也未重跑 29 probes、runtime SHA 全门、21/单条三种 pytest、38 条 collect-only 或 551 条套件。因此 (o)/(p) 的运行数字仅作为附带陈述，不能由本次审查重新背书。
- 未连接 Neo4j、未访问 live vault、未写运行时文件；只做了源码检查、Git 对象核验及最小只读 AST/Bash 环境复核。
- integration/e2e 内容、Bark-R1、生产 service、CI/OpenAPI 等明确排除面未审。
- 工作树已有的 `_bmad-output` 修改/未跟踪文件为审查开始前状态，本次未修改任何文件。

审查采用 `canvas-adversarial-audit` 的只读、多轨证据矩阵方法，并由主审重新打开高危入口验证；既往记忆只用于确定最终 SHA 绑定和 fail-closed 方法，当前结论均以本次工作树重新核对。

BLOCKER/HIGH 清零：否


