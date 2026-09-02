# CARD-TEST-isolate-lifespan-R1 验收单

- 批次：`[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]`
- 车道：`.claude/worktrees/card-w4-safety-r2` / `card/w4-safety-r2`
- 起始祖先：`2cacbb0c`（第八批 Bark 收口）→ HEAD 含第九批 Bark 三个 commit（终审 B/H=0）
- 定点带入：`cdd77274`（实现）、`b54b4735`（验收单回填），二者均**无冲突**
- 工具链：`/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`
  → `Python 3.14.4 (main, Apr  7 2026, 13:13:20) [Clang 21.0.0 (clang-2100.0.123.102)]`

---

## 0. 这一轮在修什么

第八批终裁 **1 BLOCKER / 9 HIGH**，核心指控是：这套「测试进程零连现网 Neo4j」的护栏
**证明不了自己有效**。本轮逐条整改，并把每条整改都配上「拆掉这一层就必须翻转」的负控。

---

## 1. 完成条件 (a)–(l) 逐条对照

| 条 | 要求 | 状态 | 证据（round-1 整改后的终态） |
|---|---|---|---|
| (a) | Bark 后只带入 cdd77274、b54b4735 | ✅ | 两个 commit 顺序落地、cherry-pick 无冲突、树 clean |
| (b) | 负控钉死 Neo4j 假环境 | ✅ | `_child_env()` 清全部 `NEO4J*` → 钉死受拦 loopback URI + 假凭据；`W4_GUARD_REQUIRE_BLOCKED_TARGET=1` 装门时核对；preflight **逐项精确比对七个解析值** |
| (c) | 承重层覆盖底层 socket 旁路 | ✅ | 承重 = `sys.addaudithook("socket.connect")`（摘不掉）；`socket.socket` / `_socket.socket` / `SocketType` / `connect_ex` / `__index__` 端口 / TOCTOU 端口 六条探针全 fail-closed |
| (d) | 安装与用例边界核方法身份 | ✅ | `assert_guard_live()` = **走完整条阻断路径的自证**（合成受拦地址）+ belt 方法身份 + 受拦端口集下界 + uvloop 双重检查；install 与每个用例进入/退出各一次；`extract-port-mutation` 探针证明自证承重 |
| (e) | cleanup 后迟到连接令 rc 非零 | ✅ | 最终结算置**不可逆** `_FINALIZING`，此后命中即 `os._exit(3)`；`late-connection-rc`(3) + `late-after-finalizing`(3) + 摘掉该层的负控 `late-connection-negctl`(0) |
| (f) | total=blocked 且无 advisory | ✅ | 汇总行整行唯一解析 + 账本交叉比对；实测 `(7, 7, 0, 0)`、`exempt_disabled=true` |
| (g) | AST 追踪来源、顺序与重绑定 | ✅ | 作用域有序绑定表 +「所有先前绑定必须一致」+ 每条 return 逐一判定 + 工厂按类限定 + 实例追踪进 `with`/`enter_context`；**17 绕过全抓 / 9 验伪锚全净 / 371 文件 0 违规** |
| (h) | SHA 门不受 shell 环境劫持 | ✅ | `env -u BASH_ENV -u ENV -u BASH_FUNC_*` 重新 exec（判据用 `case` 而非 `[`）+ 清 alias/trap + 函数表复核 + builtin 身份复核 + **数据管道摘要自证** + **控制流自证**；5 条注入探针全关 |
| (i) | BDD 只承诺 route-availability | ✅ | Given 改为 route-availability 且**实际断言路由已挂载**；`components` 从「有才断言」改为「必须存在且非空 dict」 |
| (j) | 负控 runner 用 sys.executable，正控先绿 | ✅ | `sys.executable -m pytest`；正控出 junit，要求三条 exact nodeid **各一次且全 passed**（skip 不算绿）+ 门账全零 + 运行时零写 |
| (k) | 覆盖 `__index__`、门前窗口与 nodeid | ✅ | `operator.index()` + `port_is_trustworthy()` 双层；guard_plugin **import 期**装门；三条**完整 nodeid** 集合全等 |
| (l) | 全门与新终审 B/H=0 | ⛔ **不成立** | 全门 ✅；但 round-2 终审因 **Codex 用量上限**未产出裁定（正文 0 字节，配额 09-07 恢复）。按「正文为空不合并」处置，见 §6 裁决点 ① |

---

## 2. 4-A 证据段（技术）

### A.1 裁判 1 — 负控（`scripts/lifespan_isolation_negative_control.py`）

```
[0]  AST gate: 0 violations across 371 files
[0b] 隔离副本: <tmp>/iso-backend
[0c] Settings 解析（rc=0）: 七个值逐项精确匹配钉死值
     （neo4j_uri / neo4j_user / neo4j_password / canvas_base_path /
       lancedb_resolved / lancedb_data_path_env / lancedb_path_env）
[1]  预采集 nodeid: 3 条（与钉死完整 nodeid 全等，collect rc=0）
[1b] 正控 rc=0 门汇总=(0, 0, 0, 0) outcomes={3 条全 passed}
[1c] 正控：三条全 passed、门账全零、运行时文件 unchanged
[2]  已在副本里摘掉 no_lifespan
[3]  pytest exit=1（cwd=隔离副本）
[3b] 子进程门汇总: total=7 blocked=7 advisory=0 unaccounted=0
[3c] 账本: total=7 blocked=7 advisory=0 billed=7 unaccounted=0 exempt_disabled=true
[4]  junitxml: total=3 red=3 green=0 red-wrong-reason=0
[5]  真实树运行时文件 untouched=True; 真实目标文件 untouched=True
[5b] 副本里变异态确实写了 app/data/vault_index_pending.jsonl（= 隔离在承重的正证据）
NEGATIVE-CONTROL: PASS
```

> ⚠️ 上面这段是 round-1 之后的形态：**变异做在 tmp 里的隔离副本上**，真实工作树的
> tracked 文件与运行时文件全程**一个字节都不写**（`[5] 真实树运行时文件 untouched=True;
> 真实目标文件 untouched=True`）。这同时消除了 round-1 的两个 HIGH：
> 「写变异体前无 CAS」和「`absent → exists` 就 unlink 可能删掉别人的数据」。

**运行时文件判据方向被更正**（本轮的独立发现）：第八批把「变异运行前后三个运行时
文件 sha 不变」当 PASS 判据 —— 方向反了。socket 门只管连接，**挡不住文件写**；挡住
文件写的是 `no_lifespan`。所以摘掉隔离后运行时文件被写，恰恰是隔离在承重的正证据。
本版改成：正控（隔离态）必须 unchanged（硬判据）＋ 变异态在**副本里**必须确实写了
至少一个（硬判据，防「lifespan 没跑到写路径就 abort」的假负控）＋ 真实树必须纹丝不动。

### A.2 裁判 2 — runtime SHA 门包裹 `tests/api` + `test_vault_scope_409`

```
RUNTIME-FILES: unchanged
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
2 failed, 265 passed, 38 warnings in 1.17s
```

两条失败已在**带入基线 `4a25578e`** 上实跑复现，failure-set 两侧**全等**
（`comm` 三段：基线独有 0 / 新增 0 / 共有 2）：

- `test_metadata_subject_mapping.py::TestGetMetadata::test_metadata_group_id_format`
- `test_recommend_action.py::TestRecommendActionEndpoint::test_history_query_failure_graceful_degradation`

数据目录对账（**比 SHA 门更强的额外度量**）：`backend/data` + `backend/app/data`
**全目录**逐文件 sha256 前后 **零差异** —— 不只是门监视的那三个具名文件。
（SHA 门本身仍只看三个具名文件，这是它声明过的边界；全目录对账是本卡另做的测量。）

### A.2b 更宽集合的回归对账（零回归）

`tests/api tests/unit tests/bdd tests/smoke`（4726 项）在**本卡**与**带入基线
`4a25578e`** 上各跑一次，把 `FAILED` + `ERROR` 的 nodeid 取集合比对：

```
基线 4a25578e : 218 failed, 4481 passed, 1 skipped, 38 errors  → 失败/错误集 256 条
本卡 round-1  : 218 failed, 4508 passed, 1 skipped, 38 errors  → 失败/错误集 256 条
本卡 round-2  : 218 failed, 4516 passed, 1 skipped, 38 errors  → 失败/错误集 256 条
comm（两轮都跑）: 基线独有 0 条 / 新增 0 条
passed 差值 +27 → +35 = 本卡新增的 tests/unit/test_live_port_guard_contract.py 条数
```

即：**零新增红、零修好红**，passed 的增量全部来自本卡新增的单测。这一轮跑同样在
runtime SHA 门包裹下，`RUNTIME-FILES: unchanged`。

> ⚠️ `tests/contract` 被**排除**在对账集之外：`test_openapi_contract.py` 用
> schemathesis 对全部端点做属性测试，单次运行超过 15 分钟且会遍历调用每个端点
> （潜在外发副作用面未评估）。它不在卡文裁判范围内。已知事实一条：`tests/contract`
> 的运行会创建 `backend/app/data/vault_index_pending.jsonl`（0 字节），
> 而 `tests/api` / `tests/unit` / `tests/bdd` / `tests/smoke` **不会**。

### A.3 裁判 3 — 底层旁路探针（`scripts/lifespan_isolation_guard_probes.py`）

**27/27** 全部 fail-closed（19 → round-1 后 26 → round-2 自查后 27）。每条核对
**rc + 唯一裁定行**两项：

round-1 新增的 7 条（对应处置表 #2/#3/#4/#5/#17）：

| 探针 | rc | 证明什么 |
|---|---|---|
| `toctou-index-port` | 3 | 有状态 `__index__`（先给受拦端口、再给 1）被拦 |
| `extract-port-mutation` | 0 | 把端口解析打断后，自证**当场翻红**（旧自证会通过） |
| `uvloop-reimport` | 0 | 删掉毒化条目后重新 import uvloop 被 audit 拦下 |
| `late-after-finalizing` | 3 | 在 import 本门**之前**注册的 atexit 回调里发起连接 → rc 非零 |
| `shell-readonly-func` | 0 | `readonly -f` 的注入函数被 re-exec 甩掉 |
| `shell-alias-test-hijack` | 2 | alias 令 `[` 恒假后，门**拒绝空跑**而不是输出 unchanged |
| `shell-exit-trap-hijack` | 2 | EXIT trap 注入后同上 |

round-2 自查新增的 1 条：

| 探针 | rc | 证明什么 |
|---|---|---|
| `isolated-copy-no-data` | 0 | 隔离副本**只含 git tracked 文件**、`.env` 是软链、且副本完整（验伪锚：缺 `app/main.py`/`tests/conftest.py` 即判失败，防「什么都没复制所以恰好没泄漏」） |

原有 19 条：

| 探针 | rc | 证明什么 |
|---|---|---|
| `no-guard-control` | 0 | **验伪锚**：不装门时同一路径确实连得上（探针形态有效） |
| `lowlevel-_socket.socket` | 3 | 底层 C 类型直连被拦 |
| `lowlevel-SocketType` | 3 | `socket.SocketType`（= `_socket.socket`）被拦 |
| `lowlevel-connect_ex` | 3 | `connect_ex` 被拦（抛而不是回 errno） |
| `lowlevel-__index__-port` | 3 | 实现 `__index__` 的端口对象被拦 |
| `real-7691` | 3 | 用**真实受拦端口**走一遍（目标 `192.0.2.1`，RFC 5737，不可路由到任何真库） |
| `drift-reinstall` | 0 | 拆掉 belt 后 `assert_guard_live` 与 `install` **两处**都抛 `GuardDrift` |
| `plugin-import-installs` | 0 | **门前窗口**：import 插件即装门，不等 `pytest_configure` |
| `audit-liveness-control` | 0 | **验伪锚**：装门前 `audit_hook_alive()` 为 False，装门后为 True |
| `require-blocked-target` | 0 | 目标端口不在射程内 ⇒ 拒绝装门 |
| `require-blocked-target-positive` | 0 | **验伪锚**：目标是受拦端口时同一开关下装得上（不是恒拒绝） |
| `late-connection-rc` | 3 | cleanup/atexit 之后的迟到连接令 rc 非零 |
| `late-connection-negctl` | 0 | **验伪锚**：摘掉最终总账，同一场景 rc 退回 0 —— rc=3 是这一层挣来的 |
| `ledger-written` | 3 | 账本落盘且内容与预期一致（父进程复核依据） |
| `shell-selftest-load-bearing` | 1 | **验伪锚**：把钉死摘要改错 ⇒ GATE-BROKEN（自证不是死代码） |
| `shell-can-report-changed` | 1 | **验伪锚**：在 tmp 假 backend 里写受监视文件 ⇒ 判 CHANGED（门能说"变了"） |
| `shell-fake-dirname` | 0 | 导出假 `dirname` 后监视路径仍是真实 backend 路径 |
| `shell-fake-printf` | 0 | 导出假 `printf` 后摘要不再恒零 |
| `shell-bash-env` | 0 | `BASH_ENV` 注入的函数被连根拔掉 |

### A.4 AST 门负控

**17 类绕过全部被抓、9 条验伪锚全部干净**（round-1 之后从 10/5 扩到 17/9）。

绕过：属性式 `tc.TestClient` / 局部重定义同名 `no_lifespan` / `with` 之后才
`app = FastAPI()` / class body 污染 / 伪造本地 `FastAPI()` 工厂 / helper 顺序在
`TestClient` 之后 / `TestClient` 名字被本地遮蔽 / `import app.main as m; m.app` 裸用 /
外部对象冒充局部工厂 / 工厂名被重绑定 / **`client = TestClient(app)` 后 `with client:`** /
**`ExitStack.enter_context(TestClient(app))`** / **`enter_context(先前构造的实例)`** /
**分支里才赋局部 app** / **工厂里局部 app 被覆盖成生产 app** / **同名方法跨类污染** /
**`TestClient(app=...)` 关键字形态**。

验伪锚：标准隔离形态 / 函数级 import + 别名 TestClient / 局部 `FastAPI()` /
helper 返回局部 app 后解包 / 同类方法工厂 `self._make()` / **外层 `with no_lifespan(app)`
支配内层** / **完整属性链 `fastapi.testclient.TestClient`** / **裸 `TestClient(app)` 不进
`with`（不跑 lifespan，不该报）** / **局部 app 构造的实例进 `with`**。

真实仓库扫描：**371 文件 0 违规**。

### A.4b guard 契约单测

`tests/unit/test_live_port_guard_contract.py`：**35 条全绿**（round-1 之后从 27 扩到 35）。
新增面：`NEO4J_TEST_URI` 缺端口必须被拒、`port_is_trustworthy` 四种端口形态、
uvloop 毒化条目被删必须翻红、uvloop 重新 import 被 audit 拦下。

### A.5 关键机制的实测（本轮的证据基础，均于本车道 venv 实跑）

| 现象 | 实测结果 |
|---|---|
| `socket.SocketType is _socket.socket` | `True`；`socket.SocketType is socket.socket` 为 `False` |
| 给 `_socket.socket.connect` 赋值 | `TypeError: cannot set 'connect' attribute of immutable type` |
| 只 patch `socket.socket.connect` 后用 `_socket.socket` 直连 | **连接成功，门的账面 blocked=0** |
| audit hook 拦 4 条路径 | 全部拦下（`socket.socket` / `_socket.socket` / `SocketType` / `connect_ex`） |
| `sys.removeaudithook` | **不存在** —— 装上即不可摘 |
| `sock.connect(("127.0.0.1", <实现 __index__ 的对象>))` | **连接成功**（旧 `isinstance(port, int)` 整条漏掉） |
| 最早注册的 atexit + `os._exit(3)` | 进程 rc 确实为 3 |
| 假 `dirname` / 假 `printf` / `BASH_ENV` 注入（加固前） | 三条**全部**让门输出 `unchanged` 且 rc=0 |
| audit hook 开销 | 3000 次 `open` + 30 万次加法：0.034s → 0.036s |

---

## 2.5 UAT 七段（你可以自己走一遍）

> 本卡改的是**开发期的安全护栏**，产品功能零改动。所以 UAT 能看见的东西只有一件：
> 「跑测试的时候，机器不再偷偷动你的东西」。技术指标已由我代跑，见 §2。

| 段 | 内容 |
|---|---|
| 1 前置 | 打开终端，进到 `backend` 目录。不需要启动任何服务，也不需要开着数据库。 |
| 2 操作 | 跑一次接口测试：`.venv/bin/python -m pytest tests/api -q` |
| 3 预期 | 最后一行之前会有一句 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` —— 「这一趟一次都没往你的数据库上连」。整趟约 1 秒。 |
| 4 反例（证明闸门是真的） | 跑 `.venv/bin/python scripts/lifespan_isolation_guard_probes.py`。它会用 19 种方式**试图绕过**这道闸门，每一种都必须被挡住，最后一行应是 `GUARD-PROBES: PASS — 19/19 条全部 fail-closed`。其中 6 种是「把闸门拆掉，看它是不是真的会漏」——如果闸门是摆设，这 6 种会暴露它。 |
| 5 你的数据有没有被动 | 跑 `bash scripts/lifespan_isolation_runtime_sha.sh -- .venv/bin/python -m pytest tests/api -q`，最后应打印 `RUNTIME-FILES: unchanged`。它会在跑之前和跑之后各给三个运行时文件按内容取指纹并比对。 |
| 6 回滚 | 本卡只动 `backend/tests/` 与 `backend/scripts/` 下的文件，产品代码一行没改。`git revert 86329c49` 即可完全撤销，不影响任何已上线行为。 |
| 7 不覆盖 | 见 §4.2。最重要的三条：跑 `tests/integration` 与 `tests/e2e` **仍然会连你的真库**（那是设计如此）；子进程里发起的连接不在闸门射程内；这套东西只在本机验证过，没在 CI 上验证过。 |

---

## 3. 4-B 用户段（零技术词）

跑测试的时候，程序不会再偷偷连上你自己那台数据库、也不会去改你笔记库里的东西。

这次做的是三件事：

1. **把「不许连」这条规矩换成了拆不掉的那种**。原来那道拦截，只要换一种写法就能绕
   过去，等于形同虚设；现在换成了系统层面的检查，装上就摘不掉，绕不过去。
2. **让检查自己证明自己还活着**。每跑一条测试之前和之后，都会验一次「拦截还在不在」，
   一旦被人动过手脚，测试当场就红，而不是安安静静地继续跑。
3. **把说得比做到的话改回来**。原来有一条测试写着「服务器正在运行」，但它其实根本没
   启动服务器——把这句话改成了它真正检查的东西。

另外还发现并修好了一个之前没人注意到的问题：验证脚本里有一处判断方向搞反了，导致它
在一种情况下会「看起来通过了、其实什么都没验到」。

**范围**：这一次只动了检查用的东西，产品本身一行没改，你用起来不会有任何差别。

### D3-A 零技术词自检

对 4-B 正文段（标题行至本小节前）grep
`Neo4j|pytest|API|lifespan|socket|DDL|LanceDB|schema|prometheus|conftest|mock|7691|7692|sha256|bug_tracker`
（`-i`）→ **计数 = 0**（2026-09-03 实测，见下方命令与结果）。

---

## 4. 诚实边界

### 4.1 这道门不比什么

- 只拦**本进程**内的连接。子进程（`subprocess` 起的 python）没有本进程的 audit hook，
  不在射程内。
- 只拦 TCP **连接建立**那一刻。复用一条门装上之前就已建立的连接，本门看不到。
- 只按**目标端口**判定（7691/7687），不解析 bolt 协议。连到别的端口的现网库拦不住
  —— 这正是负控必须钉死 `NEO4J_URI` 指向受拦端口的原因。
- `integration` / `e2e` 按路径与 marker **豁免**（只记录不拦截）。这是卡文裁决的既定
  设计：那些测试本来就要连真库。豁免只在负控里被 `W4_GUARD_NO_EXEMPT=1` 关掉。
- uvloop 走 libuv，**不触发** `socket.connect` 审计事件。本门靠**毒化 import** 关死
  这扇门，而不是靠拦截。
- 最终总账之后（解释器 finalization 期间）发起的连接仍会被拦下，但已无人能把它变成
  非零 rc —— 这段窗口无法在进程内闭合。
- runtime SHA 门只看三个**具名**文件、只比首尾两个时刻、不看 vault 与 Neo4j。
- AST 门是**静态**分析，不证明「运行时真的没连」。

### 4.2 本卡未证明什么

- **UDS 与既有连接**：本门只看 TCP connect 事件；Unix domain socket 与门装上之前
  已建立的连接不在射程内，未测。
- **`lsof` 只是采样**：第八批的 `lsof` 证据是时点采样，不是连续监控；本轮未重复。
- **`tests/integration` 与 `tests/e2e` 未复查**：按卡文裁决只登记不改。它们仍会跑真实
  lifespan、连真库，这是有意的。
- **全 19 条用例与其余 12 个改造文件未逐一变异**：负控只对 1 个代表文件的 3 条代表性
  nodeid 做原地变异（变异态每条要完整跑一遍真实 lifespan，全量 ≈ 35 分钟）。其余由
  「fixture 形态同构」+ 本子集实证共同背书。
- **CI 环境未验**：全部证据均在本机 macOS + 本车道 venv 上取得。
- **`app/data/vault_index_pending.jsonl` 的路径不可重定向**（`vault_index_orchestrator.py:101`
  硬编码），所以变异运行必然会创建它；本脚本事后删除以复原现场，但**跑的过程中**它
  确实存在过。
- **`tests/unit` 的更宽运行确实会写 `backend/data/` 下的文件**（本轮实测到
  `failed_edge_syncs.jsonl`、`failed_writes.jsonl`、`learning_memories.json`、
  `llm_call_logs.db`、`neo4j_memory.json` 五个，全部 git-ignored，工作树保持 clean）。
  它们**不在** runtime SHA 门的三文件监视清单里 —— 门从来只声明看那三个。
  本卡**只主张**：卡文列明的 `tests/api` + `tests/unit/test_vault_scope_409.py` 集合
  对 `backend/data` 与 `backend/app/data` **全目录零写入**（已实测）。`tests/unit`
  全量的写入面**未在本卡收敛**，登记移交。
- **`tests/contract` 未纳入任何对账**（schemathesis 属性测试，单跑 >15 分钟、遍历
  调用全部端点，外发副作用面未评估）。

---

## 5. Codex 处置表

### round-1（2026-09-03，绑定 commit `86329c49`）：**FAIL — 1 BLOCKER / 11 HIGH / 3 MEDIUM / 2 LOW**

全部 17 条**逐条整改**，无一条按「已声明边界」推掉。

| # | 级别 | 指控 | 处置 |
|---|---|---|---|
| 1 | BLOCKER | `assert_test_uri_not_blocked` 用子串判断；`bolt://127.0.0.1`（**不写端口**）通过检查，而驱动默认端口就是受拦的 7687 | 改为**正面判据**：解析 URI → 端口必须存在 → 且不在受拦集合。缺端口一律拒绝。新增 2 条单测 |
| 2 | HIGH | 「最早注册 ⇒ 所有 atexit 之后」不成立：本模块 import **之前**注册的 atexit 回调排在最终结算**之后**；实测 `LATE_BLOCKED_AFTER_FINAL True` 且 exit 0 | 最终结算进入即置**不可逆** `_FINALIZING`；此后 audit 命中受拦端口就地 `os._exit(3)`。文档撤回过宽表述。新增探针 `late-after-finalizing`（rc=3） |
| 3 | HIGH | token 只验私有事件分支，不验阻断分支；把 `extract_port` 改成恒返 `None` 后自证照样通过、连接照样成功 | 自证改为**发一次真的 `socket.connect` 审计事件**（哨兵主机名 + 受拦端口），走完 `extract_port` → 受拦判定 → 抛，只在最后按哨兵分流。新增探针 `extract-port-mutation` |
| 4 | HIGH | uvloop 毒化可 `del` 后重新 import；完整 policy 检查实际没被调用 | 承重换成 audit `import` 事件拦截（摘不掉）；毒化检查改为「key **必须存在且为 None**」；policy 复核并入 `assert_guard_live` 因而真的会跑。新增探针 `uvloop-reimport` + 2 条单测 |
| 5 | HIGH | `BASH_ENV` 注入的 alias / `readonly -f` 函数 / EXIT trap 未清；摘要自证只覆盖数据管道不覆盖控制流（令 `[` 恒假即可空跑出 `unchanged`） | 用 `env -u BASH_ENV -u ENV -u BASH_FUNC_*` **重新 exec 自己**（判据用 `case` 而非可被 alias 劫持的 `[`）；再加 `unalias -a` / `trap -` / 函数表复核 / builtin 身份复核 / **控制流自证**。新增 3 条探针 |
| 6 | HIGH | `absent → exists` 不能证明文件属于负控，却直接 `unlink()`，可能删掉别的进程写入的真实数据 | **结构性消除**：变异改到 tmp 里的隔离副本做，运行时文件落在副本里随 tmp 消失；真实树下的同名文件本脚本**永不删除**，只做「必须纹丝不动」的断言 |
| 7 | HIGH | 写入变异体前没有 CAS：collect/正控期间的合法编辑会被旧变异体覆盖 | 同上 —— 真实 tracked 文件**一个字节都不写**，这条链根本不存在；另加「副本与工作树逐字节一致」前置断言 |
| 8 | HIGH | AST 门只查 `with` 项本身是 TestClient 调用；`client = TestClient(app); with client:` 与 `ExitStack.enter_context(TestClient(app))` 零违规 | 新增 TestClient **实例**来源追踪（`O_TESTCLIENT_INSTANCE_MAIN`），覆盖 `with client:`、`enter_context(TestClient(app))`、`enter_context(client)` 三种形态。新增 3 条负控 |
| 9 | HIGH | 「文本上最后绑定」不是控制流分析：`if` 分支里赋局部 app 会被判安全 | 解析口径改为「**所有**先于使用点的绑定必须来源一致」，有分歧即 unknown（更保守）。新增负控 R1-9 |
| 10 | HIGH | 工厂只要**曾**赋过局部 FastAPI 就算安全：`a=FastAPI(); a=production_app; return a` 被判安全 | 改为「**每一条** return 都在自己的位置上解析为局部 app」且至少有一条 return。新增负控 R1-10 |
| 11 | HIGH | `self.make()` 只按全模块方法名判定，A 类的安全 `make` 污染 B 类的生产 `make` | 工厂身份改为 `类名.方法名`，`self.make()` 按**调用点所在类**限定。新增负控 R1-11 |
| 12 | HIGH | 正控只查 rc=0，`pytest.skip()` 同样 rc=0/零门账 ⇒ 整条负门变假 PASS | 正控也出 junitxml，要求三个 exact nodeid **各一次且全 `passed`**（skip/error 都不算绿），并核 collect rc |
| 13 | MEDIUM | 外层 `with no_lifespan(app):` 支配内层 `with TestClient(app):` 被误报；`app=` 关键字与完整属性链也误报 | 新增支配性外层隔离识别、`app=` 关键字取参、属性链**递归**解析。新增验伪锚 6/7 |
| 14 | MEDIUM | BDD 的 "contains component status" 在字段缺失时一个断言都不执行 | 改为断言字段存在、是 dict、且非空（实测键为 `batch_orchestrator/batch_sessions/fsrs/neo4j`） |
| 15 | MEDIUM | preflight 只精确核对 Neo4j URI；LanceDB 只要求非空，canvas 路径完全不查 | 改为**结构化输出 + 逐项精确比对**七个值（URI/用户/密码/canvas 路径/LanceDB 解析值/两个 LanceDB env） |
| 16 | LOW | audit hook 不是进程级 TCP 防火墙，`ctypes`/原生扩展可绕过 | 接受为边界，并把承诺**收窄写进 docstring**：「只覆盖 CPython 的 socket API」 |
| 17 | LOW | 有状态 `__index__` 的二次求值 TOCTOU（第一次给受拦端口、第二次给 1） | 新增 `port_is_trustworthy()`：端口不是**精确 int** 一律按受拦处理（fail-closed）。新增探针 `toctou-index-port` + 4 条单测 |

**round-1 之后的门规模**：探针 19 → **26** 条；AST 负控 10 绕过/5 验伪锚 → **17 绕过/9 验伪锚**；
guard 契约单测 27 → **35** 条。

---

### round-2（2026-09-03，绑定 commit `4e099b95`）：⛔ **未能取得裁定 —— Codex 用量上限**

```
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
       to purchase more credits or try again at Sep 7th, 2026 11:47 AM.
tokens used 198,766
```

正文文件 **0 字节**，rc=0。⚠️ 按既有教训（`reference_codex_content_filter_neutralize`）：
**rc=0 + 0 字节 ≠ 通过**。本轮没有裁定，因此**完成条件 (l) 不成立**。

**从 stderr 抢救出的线索（未成正式 finding，但我逐条自查并当场证实/整改了两条）**：

推理标题里出现了 `Identifying .env copy privacy flaw` /
`Detecting backend data copy with secrets exposure` / `Investigating duplicate nodeid execution` /
`Inspecting shell probe logic for false negatives` 等。我按这些线索自查：

| 线索 | 自查结果 | 处置 |
|---|---|---|
| 隔离副本把数据带出去 | **证实**：整目录 `copytree` 把 `backend/data/` 下 **12 个 git-ignored 运行时文件**搬进 `/tmp`，含 `llm_call_logs.db`(36KB)、`neo4j_memory.json`、`learning_memories.json`；`.env` 虽最终被换成软链，但拷贝过程中曾落盘 | 改为**只复制 git tracked 文件**（内容取自工作树）+ `.env` 全程软链；新增探针 `isolated-copy-no-data` 把这一面钉成门（含「副本必须完整」的验伪锚，防「什么都没复制所以恰好没泄漏」） |
| junit 重复 nodeid 被合并 | **证实形态**：`_parse_junit` 返回 dict，同名 nodeid 出现两次会被悄悄合并，「三条各跑一次」实际只验到「三个名字出现过」 | 改为返回**列表**，正控与红集判据都改成**多重集**比较（各恰好一次） |
| shell 控制流探针假阴 | **证实形态**：判据只是「没出现假绿」，门因**别的原因**崩掉也算过 | 收紧为「必须是门自己认得出来的拒绝」：rc=2 且 stderr 含用法文案，或 rc=1 且含 `GATE-BROKEN` |

其余线索（`Analyzing false positives in no_lifespan wrappers`、
`Identifying false accept and reject patterns in client context tracking`、
`Consolidating documentation contradictions`）**只有标题、没有正文**，无法据此定位具体缺陷，
如实登记为**未处置线索**，留给下一轮。

**门规模（round-2 自查后）**：探针 26 → **27** 条；其余不变。

---

## 6. 待你裁决

### ⛔ 裁决点 ①（阻断合并）：完成条件 (l) 无法在本 session 满足

卡文 (l) 要求「全部安全/语义门与**新独立终审 B/H=0**」。现状：

- round-1 终审拿到了正式裁定（FAIL，17 条），**已全部整改**；
- round-2 终审**没有产出裁定** —— Codex 侧返回
  `You've hit your usage limit ... try again at Sep 7th, 2026 11:47 AM`，
  正文 0 字节。这是**外部配额限制**，不是内容被拒，也不是我这边的失败。

按手册 §四.2「新审查绑定最终 committed HEAD，正文非空，BLOCKER/HIGH=0」——
**正文为空 ⇒ 不合并**。我不把「没有裁定」当作「裁定通过」。

**三个可选出口，请你选**：

| 选项 | 含义 | 代价 |
|---|---|---|
| **A（默认建议）** | 保持当前状态**不合并**，等 09-07 配额恢复后**只跑 round-2 终审**（代码已冻在 `4ad?????`，不再改动），拿到 B/H=0 再进合并队列 | 等 4 天；期间 W4 安全车道不进干净集成树 |
| **B** | 换一个审查方（如另一账号/另一模型）跑 round-2 | 换审查方会改变「独立终审」的口径，历史几轮都是 gpt-5.6-sol |
| **C** | 你人工复核 round-1 的 17 条整改后直接授权合并 | 少一道独立终审；本卡的历史是「每一轮都抓出真缺陷」，跳过这道的风险不低 |

### 裁决点 ②：round-2 stderr 里的三条未处置线索

`no_lifespan wrapper 误报` / `client 实例追踪的 false accept/reject` /
`文档自相矛盾` —— 只有推理标题、没有正文，我无法据此定位具体缺陷。
**建议**：并入 round-2 重跑时一并解决，不单独立卡。

### 裁决点 ③：`tests/unit` 全量的写入面未收敛（登记移交）

本卡只主张卡文列明的 `tests/api` + `tests/unit/test_vault_scope_409.py` 集合对
`backend/data` / `backend/app/data` **全目录零写入**（已实测）。但 `tests/unit` 全量
运行**确实会写** 5 个 git-ignored 的运行时文件（见 §4.2）。
**建议**：另立卡收敛，不塞进本卡。

### 裁决点 ④：`tests/contract` 完全未纳入任何门与对账

schemathesis 属性测试，单跑 >15 分钟、遍历调用全部端点、外发副作用面未评估。
本卡未碰。**建议**：单独评估其外发面之后再决定是否纳入 AST 射程与对账集。

### 裁决点 ⑤：本卡新增的两处「更严可能误拒」的判据

1. `port_is_trustworthy()`：端口不是**精确 int** 一律按受拦处理 —— 会连带拦掉
   「用 numpy 整数等对象连**非受拦**端口」的写法（本仓库零例）。
2. AST 解析改成「所有先前绑定必须一致」—— 会把「先赋 A 后无条件覆盖成 B」也判
   unknown（本仓库 371 文件零例）。

两处都是**朝更严的方向**误拒，且当前零误报。**建议**：保留，出现真实误拒时再放宽。
