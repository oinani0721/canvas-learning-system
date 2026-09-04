结论先行：**FAIL**。共发现 **1 BLOCKER、11 HIGH、7 MEDIUM、1 LOW**。审查绑定当前 `card/w4-micro` 工作树；终态 HEAD 为 `2cacbb0c`，本卡实现仍是 dirty/untracked bytes。

## Findings

[BLOCKER] `backend/scripts/lifespan_isolation_negative_control.py:220` 子进程安全前置只检查根 `conftest.py` 文本含 `live_port_guard`，随后继承 `PYTEST_ADDOPTS`。设置 `--rootdir=. --confcutdir=tests/api` 后可收集目标 19 条、无 guard summary；实际变异运行会跳过根 socket 门并保留真实 `NEO4J_URI`。建议：清理全部 pytest/Neo4j 控制环境，强制加载独立门插件并在子进程验证包装身份；变异应在临时副本且配合 OS 网络隔离，不能依赖文本 grep 保护现网。

[HIGH] `backend/tests/conftest.py:98` uvloop 只在 session fixture 首次 setup 自证一次；随后导入 uvloop 即可绕过。随机 loopback 受拦端口实验中 `uvloop.run(asyncio.open_connection(...))` 成功连接，`STATE.total=0`。建议：在 pytest 最早阶段禁止整个 session 导入/启用 uvloop，或将门下沉到 uvloop/OS 层；事后检查不能证明零连接。

[HIGH] `backend/tests/conftest.py:132` 哨兵没有 session 总账。collection/session 期记录落在 `"<session>"`，teardown report 生成后的迟到线程也无人结账；两类机制实验均得到 `1 passed`、`blocked=1`、pytest exit 0。建议：增加承重的 `pytest_sessionfinish`，任何非 advisory blocked 或残余 pending 都强制非零退出，并显式核对每条记录已归属、已结账。

[HIGH] `backend/tests/support/live_port_guard.py:94` owner/exempt 是全进程共享的单值。豁免用例运行期间，另一个非豁免后台线程会被误记为 advisory，并调用原始 `connect`。建议：用可传播但来源受控的上下文 token 绑定豁免；未知或迟到线程一律 fail-closed。

[HIGH] `backend/tests/conftest.py:428` 根 `client` 只关闭 lifespan，没有隔离请求期连接。实测 `test_health_ai_returns_valid_status` 和 `test_bug_bug_84f00404` 均尝试 `::1:7691`，各为 `1 failed / attempts=1`；后者即使最终响应 422，也会先解析 `AgentServiceDep → CanvasService → MemoryService`。建议：逐个根-client 消费者提供接口完整的请求期依赖覆盖，并把全部消费者纳入裁判集。

[HIGH] `backend/tests/smoke/test_health_smoke.py:16` 声称验证 “app boots” 的 FIRST gate 实际使用 no-lifespan 根 client。设置冲突的 `LANCEDB_DATA_PATH`/`LANCEDB_PATH` 后，smoke 加 BDD 仍 `3 passed`，而真实 startup 在 `app/main.py:98-106` 必然抛错。建议：建立外部依赖安全但真正执行关键 startup 的专用 smoke；否则移除 boot/running/FIRST-gate 声明并另补启动门。

[HIGH] `backend/tests/unit/test_vault_scope_409.py:343` chat 成功路径将 memory service patch 成裸 `MagicMock`；生产代码会 await `search_error_memories`，实际得到 `TypeError` 和 HTTP 500，但测试只排除两个字符串而假绿。建议：提供 `search_error_memories=AsyncMock(return_value=[])` 的接口桩，并强断言 200、响应契约及 `assert_awaited_once()`。

[HIGH] `backend/scripts/lifespan_isolation_negative_control.py:263` `mutated_ok` 在 `write_bytes()` 返回后才设真；SIGINT 可落在 truncate/写入或返回到赋值之间，SIGTERM 默认也不执行 `finally`，会留下被变异的跟踪文件。建议：彻底取消工作树原地变异，在临时副本/worktree 中运行；flag、trap、atexit 均不足以覆盖崩溃/SIGKILL。

[HIGH] `backend/scripts/lifespan_isolation_negative_control.py:188` AST resolver 永远收到 `[tree]`，函数级 import 分支不可达，`unknown` 又被直接放行。函数内 `from app.main import app`、`import app.main as m`、`TestClient` alias、未知 fixture 来源都可漏报；当前“局部 FastAPI 正例”也只是 unknown 放行。建议：实现按语句顺序的词法作用域和 alias 解析；unknown 必须 fail-closed 或进入人工复核违规。

[HIGH] `backend/scripts/lifespan_isolation_negative_control.py:172` 同一 `with` 内出现任意同名 helper 就跳过整条语句，不校验来源、目标或顺序；`with TestClient(app), no_lifespan(app)` 会先启动真实 lifespan，却得到零违规。建议：验证 helper 的真实绑定、与 TestClient 使用同一 app，且必须排在对应 TestClient 之前。

[HIGH] `backend/scripts/lifespan_isolation_runtime_sha.sh:67` `shasum | awk` 的失败被外层 `printf` 成功状态吞掉。让 `shasum` 返回 7 后，digest 为空，脚本仍打印 `RUNTIME-FILES: unchanged`、exit 0。建议：独立检查 hash pipeline 状态，并验证结果严格为 64 位十六进制。

[HIGH] `backend/scripts/lifespan_isolation_runtime_sha.sh:81` 被包裹命令直接运行在门自身 shell。`-- exit 0` 可跳过 after；`eval 'snapshot(){ printf x; }; BEFORE=x'` 可篡改门后仍正式输出 unchanged。建议：在子 shell `( "$@" )` 中运行命令，由父 shell保存 rc、重新计算并裁定。

[MEDIUM] `backend/tests/conftest.py:104` session fixture 原地修改 core `bug_tracker.log_path`，使既有 `test_global_singleton_default_path` 稳定失败：实际为 pytest tmp，期望 `data/bug_log.jsonl`，attempts=0。建议：创建临时 `BugTracker`，只 patch `app.main.bug_tracker` 及 exception-handler 消费别名，不修改 core 单例契约。

[MEDIUM] `backend/tests/test_deep_monitoring.py:87` 关闭 lifespan 后不启动后台资源采集，但 import 时注册的 Gauge 和宽松的 `or "HELP"` 已足以恒绿；未采集时 CPU/memory 样本仍为 0，disk 只有 HELP/TYPE。建议：显式触发或 spy `collect_metrics()`，断言具体 sample；JSON summary 因每请求主动采集可放行。

[MEDIUM] `backend/tests/unit/test_mastery_api.py:45` store getter patch 正确，但 engine 桩仍写入生产代码不读取的 `mastery_mod._engine`，真正的 service `_engine_instance` 也未复位。无 lifespan 时会使用裸惰性 engine 或继承前序 fusion singleton。建议：patch endpoint 命名空间的 `get_mastery_engine`，保存/恢复真实 singleton；若测启动后 fusion 语义则实际使用 `lifespan_lite`。

[MEDIUM] `backend/tests/support/live_port_guard.py:270` 绝对路径 fallback 在整条路径中做 substring。`/tmp/tests/integration/project/backend/tests/unit/test_x.py` 会令 unit 测试被判为 integration advisory。建议：先相对固定的 `backend/tests` 根规范化，再只检查首级目录。

[MEDIUM] `backend/scripts/lifespan_isolation_negative_control.py:350` 最终裁定不要求 `pytest_rc == 1`，也不锁定基线 nodeid 集或期望 19 条；收集缩水到一个正确原因失败、或 rc=3 且已有正确 failure，都可能 PASS。建议：变异前固定完整 nodeid 集，要求集合严格相等、总数准确且退出码恰为 tests-failed。

[MEDIUM] `backend/scripts/lifespan_isolation_negative_control.py:153` AST 目录范围只扫描 `test_*.py`，漏掉 `tests/unit/conftest.py` 和 `tests/unit/grouping/conftest.py`。当前两文件无 TestClient，但未来共享 fixture 可旁路。建议：范围内扫描全部 `.py`，至少显式纳入所有层级 conftest。

[MEDIUM] `_bmad-output/审查/CARD-TEST-isolate-lifespan-验收单.md:3` 本卡没有实现 commit 锚；`git log --grep` 命中的只是 Bark commit 正文所写“将随本卡合并”，目标脚本和 support 目录仍 untracked。审查期间 HEAD 从 `e9984cd3` 前进到仅改 Bark 文档的 `2cacbb0c`，backend 无差异。建议：提交带本批次/卡号标记的完整 exact bytes，再重新生成并绑定所有证据。

[LOW] `backend/tests/conftest.py:23` `app.main.app` 在 `pytest_configure` 安装门之前已导入，因此 import-time connect 不受保护。当前 fresh-import 探针为零连接，故只构成覆盖窗口。建议：将安装动作移到导入 `app.main` 之前，或使用更早加载的独立 pytest plugin。

## 13 文件语义核对

| 文件 | 裁定 | 核对结果 |
|---|---|---|
| `test_agents_dedup.py` | PASS | 真实 agents router/409 信封；DI 桩未替换断言对象。 |
| `test_fsrs_state_api.py` | PASS | 真实 review/health router，既有 service patch 保持有效。 |
| `test_metadata_subject_mapping.py` | PASS | 真实 metadata router，resolver 读写断言保留。 |
| `test_fsrs_state_query.py` | PASS | 真实 review router及 service 调用断言保留。 |
| `test_mastery_api.py` | PARTIAL | store 真桩有效；engine 隔离失效。 |
| `test_subjects_group_isolation.py` | PASS | 真实 subjects router，断言来自 stub 记录的 Cypher/group 参数。 |
| `test_sync_batch_auth.py` | PASS | schema gate 桩不绕过鉴权矩阵。 |
| `test_sync_exception_classification.py` | PASS（本卡增量） | no-lifespan 未改变异常 patch/分类路径。 |
| `test_sync_group_isolation.py` | PASS | 真实 sync router，物理 group 断言仍来自 driver 记录。 |
| `test_system_endpoint_auth.py` | PASS | 真实 system/auth router；LLM/runtime manager 已隔离。 |
| `test_vault_scope_409.py` | FAIL | 409 路径有效，但同-vault chat 成功路径固定 500 假绿。 |
| `test_debug.py` | PASS | 真实 debug router，使用独立 tmp BugTracker。 |
| `test_deep_monitoring.py` | PARTIAL | summary 有效；raw resource 指标不再证明后台采集。 |

## 其余放行面

- `socket.create_connection`、默认 asyncio、httpx/requests、TLS 底层连接、TestClient portal、裸线程和 `ThreadPoolExecutor` 均命中类属性包装。
- `connect_ex` 抛 `RuntimeError` 是明确的 fail-closed 选择；测试树无依赖 errno 返回值的调用方。
- `install/uninstall` 重复调用幂等，原始 `connect/connect_ex` 可准确恢复。
- `no_lifespan` 在正常、异常退出和严格 LIFO 嵌套中均恢复原 lifespan；真实 routes、middleware、DI 未被替换。
- 标准 setup 期连接会在 call/teardown 结账，同步 fixture finalizer 会在 teardown report 前被捕获；问题仅在 session/collection 和 report 后迟到窗口。
- 正常 checkout 下 integration/e2e 前缀匹配正确，误放到 unit 且无 marker 的 integration 测试会 fail-closed；上述祖先路径 substring 是唯一新增旁路。
- 负门当前 anchor 恰好一次；畸形/缺失 JUnit、green、skip/error、错误失败原因能被拒绝。当前 `--ast-only` 的 `0/253` 仅说明现状扫描结果，不证明扫描器可靠。
- `isolate_dependency_overrides` 与 module/function fixture 的正常 setup/teardown 顺序未发现覆盖泄漏。

总体裁定：**FAIL**。BLOCKER 与多项 HIGH 已直接推翻“负门永不真连”“uvloop 引入必失败”“任意 blocked 尝试最终必令 pytest 非零”以及“13 文件均无假绿”的核心验收主张。


