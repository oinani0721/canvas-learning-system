> 批次: BATCH-2026-09-18-第十五批 · 车道 P9（card-p9-testinfra） · 卡 CARD-DEBT-1 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-1.md)"`
> 审查绑定: `f595562e6d5450c20c1a87c01113039dfb17da63`（该轮的 HEAD；本卡后续按 D-15 继续整改，HEAD 已前进，故本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

**复核结论：PARTIAL。未发现 BLOCKER；1 项 HIGH、6 项 MEDIUM。** 普通、路径稳定的收集下，新增打标没有扩大 W4 advisory 面；但“所有路径均中性”和“timeout 保证终止挂起”都不能签为通过。

全程只读，未运行项目测试、连接数据库或启动容器。下文 `E/` 指 `_bmad-output/审查/evidence-debt1/`。

1. **HIGH — `signal` 只抛超时异常，不保证 item／进程按时结束，特定 asyncio 输入甚至可能把异常留在日志中而测试通过。**

   位置：[backend/pytest.ini:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/pytest.ini:48)、[test_debt1_default_gate.py:237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:237)、`E/hang-census.md:223`。

   `pytest-timeout 2.4.0` 的 signal handler 调用 `pytest.fail()`，不会直接杀掉 portal、executor 或进程。现有存档也显示：`E/contract3-close-20260918T222224.txt:159` 是 Hypothesis 聚合异常，`:207-221` 中 Timeout 只是其中一个子异常。因此“触发过 timeout”不等于“该 item 在 300 秒结束”。[插件源码](https://github.com/pytest-dev/pytest-timeout/blob/2.4.0/pytest_timeout.py#L453-L469)

   **对照输入：**
   - async 测试安排 `loop.call_soon(time.sleep, 6)`，主体等待短暂 `asyncio.sleep`，timeout 设为 1 秒。信号落在回调中时，`Handle._run()` 可捕获 `Failed` 并交给异常日志处理；主体可能继续通过，或后来红在另一条断言上。普通 `except Exception` 接不住它，不能泛称业务异常处理都会吞掉 Timeout。[CPython 实现](https://github.com/python/cpython/blob/v3.14.4/Lib/asyncio/events.py#L85-L102)
   - portal／executor 中运行无法及时取消的任务：主线程超时后，清理仍可能等待线程退出。
   - 主线程执行不检查 Python signals 的长 C 运算：handler 要等 C 返回才执行；现有同步 sleep 探针不能证明这种输入可终止。[Python signal 文档](https://docs.python.org/3/library/signal.html#execution-of-python-signal-handlers)

   后两类意味着**探针绿了，真实挂起仍可能存在**；不代表这次已完成的默认门存档是假绿。上述对照未在本次执行。

2. **MEDIUM — W4 中性结论依赖路径目标稳定；收集后改变软链目标是门未覆盖的路径。**

   位置：[conftest.py:1083](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/conftest.py:1083)、`:1092`；对照 `live_port_guard.py:1575-1579`。

   **门未覆盖的路径：**用例路径在 collection 时解析到 integration，hook 添加 `integration`；随后软链改指 unit。旧门在运行期按新路径判定不豁免，新门却先凭已经保存的 marker 返回豁免。相同的 `resolve()` 算法不能证明两个时刻的目标相同。

   这是条件性源码反例，**未发现实际发生实例、未执行复现**。静态软链本身不构成扩面；pytest 的路径处理也不能一概假定已经消除了软链。[pytest 路径实现](https://github.com/pytest-dev/pytest/blob/9.0.2/src/_pytest/pathlib.py#L918-L924)

3. **MEDIUM — “映射增加第四目录就会红”不成立，W4 门只覆盖两个样本文件。**

   位置：[test_debt1_default_gate.py:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:178)、`:189`、`:197`。

   **未被拦下的输入：**映射增加 `"regression": "real_neo4j"`；现有五条门不收集 regression，因此可以全部通过，而该目录实际获得新增豁免。当前三项映射正确，问题在回归门覆盖范围及其保证措辞。

4. **MEDIUM — 收集子进程出错且没有 nodeid，会被当成“成功排除所有用例”。**

   位置：[test_debt1_default_gate.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:197)、`:198`；同类检查见 `:169-170`。

   **负控输入：**仅在豁免表达式 `e2e or integration or real_neo4j` 下触发 collection/internal error；子进程没有 nodeid，`:198` 仍绿。前面的无 `-m` anchor 是另一次进程，不能证明这次成功。应区分正常全 deselect 与 collection/internal error，而不是只检查 stdout；正常全 deselect 也不能简单要求 rc=0。

5. **MEDIUM — census 的若干根因结论强于存档，尤其“唯一元凶”“不是 pact”和“就是连接重试”。**

   位置：[hang-census.md:306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-debt1/hang-census.md:306)、`:318`、`:373-375`、`:415-422`。

   | 条目 | 存档实际支持的程度 |
   |---|---|
   | C-1 超长 teardown | **直接证据充分。** `census-stackprobe-studyq-20260918T210537.txt:30-113`、`:441-455` 显示 portal join → executor shutdown → SentenceTransformer/HuggingFace HTTP 等待，不只是模型加载起始日志。 |
   | C-1b regression | 正常结束、1175.32 秒属实；不能把本次未触发写成以后“不可能改变结果”。 |
   | C-2 collection | `contract-collect-20260918T202937.txt:239` 证明 196 条、123.57 秒；没有阶段计时证明这两分钟全部用于 schema 参数化。 |
   | C-2b／“不是 pact” | `census-contract-pact-20260918T212833.txt:18` 的 provider 两条均 skipped，`:68` 为 25 passed、2 skipped。只能排除**本次配置下**的 pact 探针，不能反证历史批次或 provider 真正执行时的行为。 |
   | contract 执行慢 | `census-contract-schemathesis-20260918T210833.txt:32-49` 的超时快照是 Vault 图构建及 BeautifulSoup/lxml 解析；没有证明时间消耗在 Neo4j 连接重试。 |
   | C-3／C-4 | collect-only 期间发生受拦连接、rc=3，以及 health 的 19 次拦截有实证；连接拦截与慢请求共现，不等于重试耗时因果已证。 |
   | 默认门新增 preflight 红 | `hang-census.md:182-199` 的“变量是负载、与本卡无关”仍是推断。目录级与全量同时改变了顺序、导入集、共享状态及持续时间。 |

   **对照输入：**固定选集、顺序与 examples，分别测量生命周期各阶段；验证负载归因时只改变负载。当前宜写成“本次 openapi 单文件超过 20 分钟，触发一次 item timeout；pact provider 在本次配置下跳过”。一次 item timeout 也不能证明单个 HTTP 请求／Hypothesis example 超过 300 秒。

6. **MEDIUM — `196 = 196` 属实，但不能单靠数量证明排除集合完全一致。**

   位置：[hang-census.md:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-debt1/hang-census.md:160)。

   默认门存档 `:16` 确为 `9453 collected / 196 deselected / 9257 selected`；contract 独立收集存档 `:239` 确为 196。其他目录具名存档的收集数合计也吻合 9257，属于支持性证据。

   **未被拦下的输入：**两次收集集合变化后，195 条 contract 加一条目录外带排除 marker 的用例，同样满足这个等式。缺少同次 deselected nodeid 清单，不能签“集合已独立核对”。**本次没有发现可点名的额外排除用例。**

7. **MEDIUM — 缺插件时“只警告、不失败”应限定为本次默认配置，grep 依据不充分。**

   位置：[backend/pytest.ini:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/pytest.ini:76)。

   `E/census-control-rootfiles-20260918T204620.txt:1801`、`:1806` 确有两个 Unknown config warning，失败集合也未变，足以支持本次控制组结论。

   **对照输入：**禁用插件后增加 `-o strict_config=true`、`-o strict=true`，或 pytest 的 `-W error::pytest.PytestConfigWarning`，未知键可以导致失败。`--strict-markers` 不负责未知 ini 键；仓内 grep 也不能排除命令行注入。[pytest 9.0.2 配置检查](https://github.com/pytest-dev/pytest/blob/9.0.2/src/_pytest/config/__init__.py#L1318-L1358)

其余核对结果：

- **⓪ 常规路径：通过。** 映射恰三条，没有 `real_neo4j`；稳定软链与旧门使用相同解析口径。解析到 tests 外不会新增 marker；hook 未执行只会漏标。限定读取面不足以排除其他 conftest 或根文件未授权部分的同名 hook，不能声称已完成全仓排查。
- **改动范围：通过。** 指定 diff 确为 3 files、364 insertions、0 deletions；根 conftest 仅追加，`addopts:19-21` 未变。
- **300 秒标定：有据。** `unit-open-20260918T192142.txt:1006`、`:1026` 对应 217.38 秒 teardown 和 5.02 秒 call；约 1.35 倍余量的披露属实。
- **默认门：完成但未达时长目标。** `census-default-gate-20260918T212851.txt:3180`、`:3184-3185` 确为 47 分 33 秒、147 failed、rc=1。
- **⑤ 控制组设计成立，历史负控尚不能完整认证。** 第三条删 hook 仍绿、第五条因 CLI `--timeout=1` 而在删 ini timeout 后仍绿，均符合代码。已读的 `gate-before-r2-20260918T195344.txt:13-15`、`:116-118` 确实红在所述两处，但其 `:214` 是 **2 failed / 1 passed / 2 skipped**，不是所述变异负控的 **2 failed / 3 passed**。两段变异负控及还原 SHA256 的精确存档名称尚未提供，因此没有用这份旧档替代认证。
