FAIL（1 BLOCKER / 8 HIGH / 7 MEDIUM / 2 LOW）

已确认分支为 `card/w4-safety-r2`、实现最终态为 `de57e375bbf53e3aff8e91a81eee3dfed3c7487b`；`de57e375..HEAD` 排除 `_bmad-output/` 后代码 diff 为空。审查全程只读，未改动已有 dirty review 文件。

## Findings

1. [BLOCKER] [backend/tests/support/live_port_guard.py:638](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:638) — `NEO4J_TEST_URI` 的正面判据仍接受端口 `0`。本地实测预检输出 `GUARD_ACCEPTED`，但当前 Neo4j driver 在 [neo4j/_addressing.py:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/lib/python3.14/site-packages/neo4j/_addressing.py:175) 将 `127.0.0.1:0` 归一化为默认 `7687`。具体场景：`NEO4J_TEST_URI=bolt://127.0.0.1:0` → session 预检通过 → integration/e2e 在 [is_exempt():779](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:779) 被豁免 → `STATE.record()` 只记 advisory、不抛 → 真连开发库。建议拒绝 `port <= 0` 和越界端口，最好只允许项目测试端口 `7692`，并以 driver canonical address 做端到端契约测试。验收单 §7.6c-bis 对 A 的“自我证伪”漏算了 exemption，结论错误。

2. [HIGH] [backend/tests/support/live_port_guard.py:318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:318) — 地址是 tuple 子类时，guard 用可重载的 `len(address)`、`address[1]` 读取端口，而 CPython socket 使用 tuple 底层槽位。具体场景：底层端口为 `7691`，但覆写的 `__getitem__(1)` 返回精确整数 `1` → guard 判安全、账本为零，C socket 仍向 7691 建连；隔离探针已观察到请求越过 guard 到达 OS 网络层。建议用 `tuple.__len__`/`tuple.__getitem__` 取得与 CPython 相同的值，并加入真实 socket 回归；不能简单拒绝所有 tuple 子类，因为 Neo4j `Address` 本身也是 tuple 子类。

3. [HIGH] [backend/tests/support/live_port_guard.py:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:392) — 两条 `os._exit(3)` 路径都先执行可能失败的 `repr`、`print` 和 I/O。具体场景：finalizer 置 `_FINALIZING` 后，较早注册的回调关闭 `stderr`，再有回调触发受拦事件 → `print` 先抛 `ValueError`，`os._exit` 永远到不了；我用正常 atexit LIFO、未修改 guard 状态的子进程复现了 `LATE_CAUGHT ValueError` 且 rc=0。`_final_accounting()` 的 [line 750/758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:750) 同样受影响。建议将诊断全部置于 best-effort `try` 中，并以 `finally: os._exit(3)` 无条件收口。

4. [HIGH] [backend/tests/support/live_port_guard.py:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:392) — `_FINALIZING` 检查、`STATE.record()` 与最终 ledger snapshot 没有同锁线性化。具体场景：worker 在线 392 读到 False 后暂停 → finalizer 在线 743–744 置 True 并取得零账快照 → worker 在线 405 才落账，异常被调用方吞掉 → 最终 `blocked=1/unaccounted=1` 但进程 rc=0。该调度不需要 unregister、手调 finalizer 或重置内部状态，因此 §7.6f 对 F 的降格不成立。建议把 finalizing 状态纳入 `STATE`，在同一锁内完成“检查并记账”和“置 finalizing 并快照”。

5. [HIGH] [backend/scripts/lifespan_isolation_runtime_sha.sh:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:112) — 声称的 `BASH_FUNC_*` 清洗在绑定环境 Bash 3.2 上不成立：`compgen -e` 不枚举导出函数对应的 `BASH_FUNC_name%%` 环境键，但 `/usr/bin/env` 可以看到它，因此函数会穿过 re-exec。具体场景：导出的 `builtin` 函数隐藏函数表或伪造 `compgen`，并保留导出的 `exit` → namespaced journal 已变化，门仍可输出 `unchanged`、rc=0。此函数是在脚本执行后被脚本自身调用，不属于 §7.6f B 的“第 1 行前立即退出”不可防边界。建议使用非 Bash 启动器过滤原始环境，或 `env -i` 后显式传递允许变量，并加入 exported `builtin`/`exit` 探针。

6. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:489) — TestClient 实例 provenance 被压成单一字符串和 app 名，无法表达分支来源及对象身份。具体场景一：先构造 production client，再在条件分支改成 local client；production 分支实际跑真实 lifespan，但 `resolve_name()` 得到 `unknown`，而 [line 962](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:962) 对 unknown 直接放行。场景二：client 包住旧 production `app`，随后同名 `app` 重绑为 `FastAPI()`，外层只隔离新对象；名字相等仍被判覆盖。两种输入均由当前 `analyze_source()` 返回空。建议保存 reaching-definition 候选集合和构造点 definition token；任何候选为 main client 时必须证明隔离的是同一对象。

7. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:669) — 隔离包装器资格不是控制流/定义级，而是“存在一个受保护 yield”的函数名级摘要。具体场景：一个分支在 `no_lifespan` 内 yield，另一个分支裸 yield → 裸分支运行真实 lifespan，但 `has_yield = any(...)` 仍将整个包装器标安全。先定义安全包装器、后用同名裸包装器覆盖时也会保留旧资格。建议要求每条可执行 yield 都被同一 helper 支配，并按具体 definition/reaching binding 解析；重复定义不能共享单一 key。

8. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:1050](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1050) — `ExitStack.enter_context` 仅扫描位置参数。具体场景：合法的 `stack.enter_context(cm=TestClient(app))` 中 `node.args` 为空，代码直接 `continue`，真实 `__enter__` 会跑 lifespan，分析器返回空。反方向上，任意对象只要方法名叫 `enter_context` 又会被当作 ExitStack，产生误拒。建议支持 `cm=`/不确定参数的 fail-closed，并追踪接收者确为 `contextlib.ExitStack`。

9. [HIGH] [backend/scripts/lifespan_isolation_negative_control.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:400) — “所有先于 use 的绑定”实际只覆盖少数 statement 类型。具体场景：`app = FastAPI()` 后通过 walrus `app := production_app` 重绑，再进入 `TestClient(app)`；`ast.NamedExpr` 没进绑定表，分析器仍把 app 当局部应用并返回空。类似地，`self.make` 被实例属性覆盖后，[line 526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:526) 仍按类方法 key 判为安全工厂。建议索引 NamedExpr、pattern binding 和属性重绑定；不能继续使用“所有绑定”这一过宽措辞。

10. [MEDIUM] [backend/tests/support/live_port_guard.py:382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/support/live_port_guard.py:382) — 实现比“只拦 TCP”声明更严：没有检查 socket family/type。具体场景：UDP socket 对端口 7687/7691 调用 `connect()`，同样触发 audit event并被当作 Neo4j TCP 连接判红。建议核对 `args[0].family` 和 `.type`，限定 `AF_INET/AF_INET6 + SOCK_STREAM`；若有意拦全部协议，应同步更正文档和错误信息。

11. [MEDIUM] [backend/scripts/lifespan_isolation_runtime_sha.sh:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:273) — “`compgen -G` 已按 collating sequence 排序”不成立。绑定环境 Bash 3.2 的实际输出明显无序。具体场景：存在两个以上 namespaced journals，文件系统枚举顺序在两次快照间变化但路径集合和内容完全相同 → 快照字符串因行序不同而误报 `CHANGED`。建议显式使用锁定路径及 locale 的 `sort`，或以 path→digest 集合比较。

12. [MEDIUM] [backend/scripts/lifespan_isolation_runtime_sha.sh:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_runtime_sha.sh:243) — `vault_index_pending*.jsonl` 比正式命名语法过宽。具体场景：普通代码修改 `vault_index_pending_backup.jsonl` 或 `vault_index_pending.tmp.jsonl` → shell 门无谓报 CHANGED；Python 负控还可能把该文件写入当成“真实 durable journal 被写”的承重证据。建议将旧名作为精确固定项，新名仅匹配 `vault_index_pending__*.jsonl`。后缀在 `.jsonl` 之后的 `.jsonl.tmp` 当前不会匹配。

13. [MEDIUM] [backend/scripts/lifespan_isolation_guard_probes.py:790](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_guard_probes.py:790) — 29 条探针没有验证 shell glob 的 absent→present 分支；唯一 CHANGED 锚只写固定项 `data/bug_log.jsonl`。具体场景：删除或错误缓存 `runtime_sha.sh:300-304` 的 glob 展开后，29 probes、Python 负控和 expected-unchanged judge 仍可全绿，新 journal 却漏检。建议在 fake backend 新建 `vault_index_pending__probe.jsonl`，要求唯一 CHANGED 和 rc=1。

14. [MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:619](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:619) — E 的永久失格名单在固定点知识收敛前即不可逆生效，产生新误拒。具体场景：安全前向工厂 `outer() → inner() → FastAPI()`；首轮尚未识别 inner 时 outer 被永久失格，后续即使已证明安全仍报违规。建议先完成 provenance 固定点，再处理真正的重复定义；最好按定义位置解析活动 definition。

15. [MEDIUM] [backend/scripts/lifespan_isolation_negative_control.py:881](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:881) — 多种普通、安全的 `no_lifespan` 写法被误拒。具体场景包括 `no_lifespan(app=app)`、`with no_lifespan(app) as isolated_app: TestClient(isolated_app)`，以及 `client=TestClient(app); with no_lifespan(app), client:`；后者我在当前树实测被报违规，虽然上下文按左到右进入、真实 lifespan 已被关掉。建议支持 helper 的 `app=`、yield alias provenance，以及实例形式的同一 with 前置 sibling 覆盖。

16. [MEDIUM] [_bmad-output/审查/CARD-TEST-isolate-lifespan-R1-验收单.md:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/CARD-TEST-isolate-lifespan-R1-验收单.md:22) — 冻结证据自身没有统一绑定最终态：表头仍称 `2b160897` 为实现最终态，顶表仍是 17/9/371 且声称 shell 环境劫持已关闭；后文才改称 `de57e375`。原始 [negative-control-final.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/evidence-isolate-lifespan-r1/negative-control-final.txt:3) 最后提交于 `0684e0fa`，仍写 371 文件和旧 journal；其余 raw receipts 也早于最后两次修复。具体后果：按表头或 raw receipt 签字会把 compgen/E 修复后的状态误当已实测。建议统一 SHA/规模/隔离副本/glob 口径，并附一份明确绑定 `de57e375` 的完整原始 receipt。

17. [LOW] [backend/scripts/lifespan_isolation_guard_probes.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_guard_probes.py:78) — 父进程只检查唯一裁定行第二个 token 是 `PASS`，不核对裁定行 probe name。具体场景：子探针误输出另一探针的 PASS 标签，当前探针仍被记为成功。建议精确匹配 `PROBE-RESULT: PASS <expected-name>`。

18. [LOW] [backend/scripts/lifespan_isolation_negative_control.py:1100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/lifespan_isolation_negative_control.py:1100) — E 的同名工厂场景没有进入常设 `_AST_MUST_FLAG`。具体场景：删除 `disqualified_factory_keys` 修复后，当前 22/11 自证仍能全绿。建议把 E 和本轮四类 AST HIGH 加入永久 must-flag 集。

## 已知处置项复核

- C：精确的“干净解释器中 compgen 整体失效”已关闭，字面路径自检会在 wrapped command 前 fail-closed；但 Finding 5、13 表明整体 shell/glob 证据仍未闭合。
- B：把“脚本第 1 行前已经执行并退出”改为不可自防边界，这个判断成立；把所有非立即污染都宣称由 re-exec 清除，不成立。
- D：归为 tuple/container 元素级 provenance 盲区是恰当的，声明与实现一致，不重复计 HIGH。
- E：精确的“安全定义在前、不安全同名工厂在后”已关闭；整体只能算 PARTIAL，因为包装器同名重定义仍漏、固定点永久失格又引入误拒。
- F：归为“必须先有不篡改内部状态的复现才能定性”不成立；真实 check→record 竞态已经存在并可产生 rc=0。

## 放行维度

确认成立：

- 分支、最终实现 SHA、docs-only 尾巴判据成立；审查后 worktree 仍只有原有两项 dirty review 状态。
- 当前只读实跑：`AST-NEGATIVE-CONTROL: PASS (22/22 + 11/11)`，`AST-GATE: PASS (0/377)`。这证明现有样例通过，不推翻上述未入样例的反例。
- round-1 代码层面已关闭：3、4、6、7、10 的原始多-return反例、12、14、15、16。部分关闭：8、11、13、17。未关闭：1、2、5、9。
- `(i)` BDD 口径成立：只承诺 route availability，且 `components` 必须存在、为非空 dict。
- `(j)` 的结构成立：`sys.executable -m pytest`、tracked-only tmp 副本、正控先行、JUnit 多重集各一次且全 passed 的判据都在。
- `(m)` 静态成立：`test_vault_scope_409.py` 的 client 位于 `no_lifespan(app)` 内，合并带入的 module fixture 无冲突。
- `(n)` 静态成立：patch 位于函数体内 import 的源命名空间；两个 autouse fixture 的任一合法顺序都不会先构造单例；Graphiti 路径只构造 client、未见 initialize。
- 当前 glob 对“匹配项 absent→present”和“present→absent”会判 CHANGED，因为每次快照重新展开；空→空仍为 unchanged。若未来正式文件名完全移出 pattern，则会重现“空集合恒绿”。
- Audit 会经过 CPython `socket.socket`、`_socket.socket`、`SocketType` 的 `connect/connect_ex`，以及委托这些方法的 `create_connection`、标准 selector asyncio、SSL/HTTP/Neo4j 路径。不会覆盖已建立连接复用、子进程、uvloop/libuv、直接 libc/ctypes/cffi/原生 syscall、`sendto/sendmsg`。
- `assert_guard_live()` 能证明当前合成 audit event 经过 audit 分发、精确 int 端口提取、受拦集合判定和 sentinel 异常，也核 belt/uvloop 身份；不能证明真实 C 调用、地址子类、`STATE.record`、豁免/账本、finalization 或两次边界间持续不漂移。其函数 docstring 对这一有限范围基本诚实。
- `os._exit(3)` 会覆盖原退出码并跳过其余 callbacks；这是 fail-closed 取舍，不单独计缺陷。缺陷是现实现不能保证它必然可达。

没有核：

- 按请求未运行完整负控。
- 未运行完整 29 probes、runtime SHA、38 条 collect-only、story 文件 21/单条三种跑法或 551 条文件集；这些只能按附带材料登记，不能视作本轮 final-SHA 独立实测。
- 未复审明确排除的 integration/e2e 内容、主干卡、Bark-R1、生产 service 与 CI。
- 审查采用三条独立证据轨并由主审重开 BLOCKER/HIGH；未访问 live Neo4j、Vault 或生产数据。

BLOCKER/HIGH 清零：否


