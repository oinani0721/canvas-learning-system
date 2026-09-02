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

| 条 | 要求 | 状态 | 证据 |
|---|---|---|---|
| (a) | Bark 后只带入 cdd77274、b54b4735 | ✅ | `git log` 两个 commit 顺序落地，`git status` clean，cherry-pick 无冲突 |
| (b) | 负控钉死 Neo4j 假环境 | ✅ | `_child_env()` 清全部 `NEO4J*` → 钉死 `bolt://127.0.0.1:7691` + 假凭据；`W4_GUARD_REQUIRE_BLOCKED_TARGET=1` 装门时核对；step 0c 实测 `Settings` 解析结果 |
| (c) | 承重层覆盖底层 socket 旁路 | ✅ | 承重换成 `sys.addaudithook("socket.connect")`；探针 4 条底层路径全部 fail-closed |
| (d) | 安装与用例边界核方法身份 | ✅ | `assert_guard_live()`：audit token round-trip + belt 方法身份 + 受拦端口集下界 + uvloop 毒化；install 与每个用例进入/退出各一次 |
| (e) | cleanup 后迟到连接令 rc 非零 | ✅ | `_final_accounting`（atexit LIFO 最后执行）→ `os._exit(3)`；负控 `late-connection-rc` rc=3，摘掉该层的负控 rc=0 |
| (f) | total=blocked 且无 advisory | ✅ | 汇总行整行唯一解析 + 账本交叉比对；实测 `(7, 7, 0, 0)` |
| (g) | AST 追踪来源、顺序与重绑定 | ✅ | `_ModuleIndex` 重写为按作用域的有序绑定表；10 类绕过全抓 / 5 条验伪锚全净；真实仓库 371 文件 0 违规 |
| (h) | SHA 门不受 shell 环境劫持 | ✅ | 清 `BASH_ENV` + `compgen -A function` 全清 + 绝对路径 + 参数展开代替 `dirname` + builtin 代替 `awk/grep` + **摘要自证** |
| (i) | BDD 只承诺 route-availability | ✅ | Given 改为「health 路由挂在 lifespan-free 客户端上」并**实际断言路由已挂载** |
| (j) | 负控 runner 用 sys.executable，正控先绿 | ✅ | `_base_cmd()` 用 `sys.executable -m pytest`；正控 rc=0 / 门账 `(0,0,0,0)` / 运行时文件 unchanged |
| (k) | 覆盖 `__index__`、门前窗口与 nodeid | ✅ | `operator.index()` 规范化 + 单测；guard_plugin **import 期**装门 + 探针；三条**完整 nodeid** 集合全等 |
| (l) | 全门与新终审 B/H=0 | ⏳ | 见 §5 Codex 处置表 |

---

## 2. 4-A 证据段（技术）

### A.1 裁判 1 — 负控（`scripts/lifespan_isolation_negative_control.py`）

```
[0]  AST gate: 0 violations across 371 files
[0c] Settings 解析出的 NEO4J_URI = 'bolt://127.0.0.1:7691'  LanceDB = <tmp>/lancedb  (rc=0)
[1]  预采集 nodeid: 3 条（与钉死完整 nodeid 全等）
[1b] 正控 rc=0 门汇总=(0, 0, 0, 0)
[1c] 正控运行时文件: unchanged（隔离态零副作用）
[2]  已摘掉 no_lifespan
[3]  pytest exit=1
[3b] 子进程门汇总: total=7 blocked=7 advisory=0 unaccounted=0
[3c] 账本: total=7 blocked=7 advisory=0 billed=7 unaccounted=0 exempt_disabled=true
[4]  junitxml: total=3 red=3 green=0 red-wrong-reason=0
[5]  还原完成; byte-identical=True; 运行时现场已复原=True
[5b] 变异态确实写了 app/data/vault_index_pending.jsonl（= 隔离在承重的正证据）
[5c] 已删除本脚本造成的新增运行时文件
NEGATIVE-CONTROL: PASS
```

**运行时文件判据方向被更正**（本轮的独立发现）：第八批把「变异运行前后三个运行时
文件 sha 不变」当 PASS 判据 —— 方向反了。socket 门只管连接，**挡不住文件写**；挡住
文件写的是 `no_lifespan`。所以摘掉隔离后运行时文件被写，恰恰是隔离在承重的正证据。
本版改成：正控（隔离态）必须 unchanged（硬判据）＋ 变异态必须**确实写了**至少一个
（硬判据，防「lifespan 没跑到写路径就 abort」的假负控）＋ 现场复原。

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
基线: 218 failed, 4481 passed, 1 skipped, 38 errors   → 失败/错误集 256 条
本卡: 218 failed, 4508 passed, 1 skipped, 38 errors   → 失败/错误集 256 条
comm: 基线独有 0 条 / 新增 0 条
passed 差值 +27 = 本卡新增的 tests/unit/test_live_port_guard_contract.py
```

即：**零新增红、零修好红**，passed 的增量全部来自本卡新增的单测。这一轮跑同样在
runtime SHA 门包裹下，`RUNTIME-FILES: unchanged`。

> ⚠️ `tests/contract` 被**排除**在对账集之外：`test_openapi_contract.py` 用
> schemathesis 对全部端点做属性测试，单次运行超过 15 分钟且会遍历调用每个端点
> （潜在外发副作用面未评估）。它不在卡文裁判范围内。已知事实一条：`tests/contract`
> 的运行会创建 `backend/app/data/vault_index_pending.jsonl`（0 字节），
> 而 `tests/api` / `tests/unit` / `tests/bdd` / `tests/smoke` **不会**。

### A.3 裁判 3 — 底层旁路探针（`scripts/lifespan_isolation_guard_probes.py`）

19/19 全部 fail-closed。每条核对 **rc + 唯一裁定行**两项：

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

10 类绕过全部被抓、5 条验伪锚全部干净：

绕过：属性式 `tc.TestClient` / 局部重定义同名 `no_lifespan` / `with` 之后才
`app = FastAPI()` / class body 污染 / 伪造本地 `FastAPI()` 工厂 / helper 顺序在
`TestClient` 之后 / `TestClient` 名字被本地遮蔽 / `import app.main as m; m.app` 裸用 /
外部对象冒充局部工厂 / 工厂名被重绑定。

验伪锚：标准隔离形态 / 函数级 import + 别名 TestClient / 局部 `FastAPI()` /
helper 返回局部 app 后解包 / 同类方法工厂 `self._make()`。

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

（待填 —— 见 §6）

---

## 6. 待你裁决

（待填）
