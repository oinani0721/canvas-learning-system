# Dredd / schemathesis 接 CI —— 可行性判据与成本

> 卡：`CARD-TOOL-dredd-prereq`（`[BATCH-2026-09-05-第十二批]`）· 车道 `card-y5-review`
> 代码树：`67ee147c`（Y5-C 末 commit）+ 一个未入库的临时探针（跑完已删）
> 环境：本机 macOS / Python 3.14.4 / pytest 9.0.2 / schemathesis 4.14.3 / hypothesis 6.151.10
> 前作：`_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md`（Z7-C，已裁「Dredd 退役 + schemathesis 接 CI」，两个前置未解）
> 本页**零 CI 改动、零生产改动**，只出证据与判据。原始输出全部在 `evidence-dredd-prereq/`。
>
> **本版是 Codex round-1（`gpt-6-astra` / `ultra`）审后整改版**（送审版 sha256 `c8f75787…8a55`）：
> 0 BLOCKER / 2 HIGH / 8 MEDIUM / 3 LOW **全部采信**，逐条处置见
> `_bmad-output/验收单/UAT-CARD-TOOL-dredd-prereq-2026-09-06.md` §五。**整改后的措辞未再送审。**

---

## 〇 一句话结论

单次 `case.call()` 的墙钟（十个样本 **23.117–37.045s**）**绝大部分**落在 `with asgi.get_client(app) as client:`
这个包装区间的两头——进入（中位 19.082s，run-2）与退出（中位 12.256s，run-2）；
schemathesis 自身的请求段中位 9ms，hooks 与序列化两段各自中位在显示精度下都是 0.000s。
六段之和与整次墙钟的残差为 0.000193–0.001099s。

**那两头里 lifespan 占多少**：同一探针、同一边界，把 lifespan 换成 no-op 后，进入段中位 **0.001s**、退出段中位 **0.001s**
（干净进程里两段中位都是 0.000s）。⇒ 进入/退出段里**非 lifespan 的部分（TestClient 构造 + portal 建/收）在毫秒量级**，
其余是 app lifespan。

**门那一侧**：同一支 `no_lifespan` 探针在**干净进程**里单独跑，整个 session `blocked=0`、`rc=0`、1.03s 跑完。
⇒ Z7-C 留下的两个前置（耗时 / 门下退出码非零）**指向同一个原因，也指向同一条候选处置路径**——
但那条路径的代价（被测对象等价性）本卡**未测**，见判据 C。

---

## 一 分段 profile（完成条件 a）

### 1.0 探针出处（⚠️ 两轮不同源，如实登记）

存档：`evidence-dredd-prereq/profile_harness.py`，sha256 `70378e38…fce1`。

- 该 sha **只与 run-2 / 干净进程对照组的工作树文件逐字节相同**（`harness-sha256-20260906T104022.txt` 是跑 run-2 **之前**当场取的）。
- **run-1 由更早一版探针产出**，三处差异：① 只有 1 个用例，没有 `no_lifespan` 对照组
  （独立证据：`collect-only-20260906T103437.txt` 是 `1 test collected`，`collect-only-20260906T104022.txt` 是 `2 tests collected`）；
  ② 没有 `_reset_ledger()`；③ 「未归类」的打印精度是 3 位小数（run-1 因此显示 `0.000s`），run-2 起改成 6 位。
- 前两处不进主用例的测量路径（`_reset_ledger()` 在首次使用时是空操作），第三处只影响显示。
  但**「同一脚本逐字节产出两轮」这个说法本页不主张**：run-1 的角色是先导复现性对照，
  **承重数字以 run-2 与干净进程对照组为准**。

### 1.1 分段边界（先说清楚量的到底是什么）

固定 Case = `GET /api/v1/health`；schema 用与 `backend/tests/contract/test_openapi_contract.py:27` **逐字相同**的
`schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)`；同一 ASGI transport，不换 httpx。

| 段 | 探针实际计时的**是什么** | 源码锚 |
|---|---|---|
| ① `1_client_construct` | `starlette_testclient.TestClient(app)` 的构造 | `schemathesis/python/asgi.py:9-12` |
| ① `1_lifespan_startup` | **`client.__enter__()` 整体** = portal（线程 + 事件循环）建起 **+** app lifespan startup | `schemathesis/transport/asgi.py:21` 的 `with` 进入 |
| ② `2_hooks_before_call` | `schemathesis.generation.case` 模块级的 `dispatch("before_call", …)`（**只有这一个**） | `generation/case.py:362-363` |
| ② `2_serialize_case` | `RequestsTransport.serialize_case` | `transport/requests.py:146` |
| ③ `3_request` | `_request(**data)`（= 那个 TestClient 的 `request`），**含应用处理本身** | `transport/requests.py:195,197` |
| ④ `4_lifespan_shutdown` | **`client.__exit__()` 整体** = app lifespan shutdown **+** portal / 线程收尾 | `schemathesis/transport/asgi.py:21-22` 的 `with` 退出 |

⚠️ **① 与 ④ 不等于「纯 app lifespan」**，它们是包装区间；③ 也不等于「纯 schemathesis 开销」，它含应用处理。
把 lifespan 单独摘出来靠的是 §1.3 的对照组，不是这张表。

**串行性由源码顺序读出**（`Case.call()` :362 → :380 `transport_.send` → `with` 进入 → `super().send` 内 serialize →
`_request` → `with` 退出）：六段首尾相接、无嵌套。
残差小是**补充旁证，不是独立证明**——残差 = 漏计量 − 重复计量，两者可以互相抵消。
本次调用链读源码未见重叠，但该结论只覆盖**当前这条固定成功路径**，不推广到 hook 重入或并发调用。

### 1.2 主用例（门下、完整 lifespan）—— 两次独立运行

存档：`evidence-dredd-prereq/profile-20260906T103504.txt:516-569`（run-1）
　　　`evidence-dredd-prereq/profile-both-20260906T104054.txt:516-570`（run-2）

| 段 | run-1 中位 / 极差 | run-2 中位 / 极差 |
|---|---|---|
| ① client construct | 0.000s / 0.000s | 0.000s / 0.000s |
| ① **`__enter__` 整体** | **23.016s** / 15.133s | **19.082s** / 3.551s |
| ② hooks before_call | 0.000s / 0.000s | 0.000s / 0.000s |
| ② serialize_case | 0.000s / 0.006s | 0.000s / 0.011s |
| ③ request（含应用处理） | 0.008s / 0.006s | 0.009s / 0.005s |
| ④ **`__exit__` 整体** | **12.638s** / 2.678s | **12.256s** / 2.372s |
| — 整次 `case.call()` | 中位 35.630s（min 23.117 / max 37.045） | 中位 31.636s（min 30.133 / max 33.907） |
| — 未归类（总 − 六段和） | ≤ 0.001s（run-1 只打到 3 位小数） | 0.000193–0.001099s（逐轮 0.001099 / 0.000343 / 0.000199 / 0.000193 / 0.000245） |
| — `from_asgi` 建 schema **+ operation 查找** | 0.626s（blocked+0，paths=193） | 1.322s（blocked+0，paths=193） |

n=5/段/轮次，两轮共 10 个样本，整次墙钟的全体区间是 **23.117–37.045s**。

⚠️ **中位数不能相加**：本页不写「三段合计中位 X」。可直接读的是：**request 段中位 9ms（run-2）**；
hooks 与序列化两段的中位在显示精度下是 0.000s（序列化 max 0.011s，即 `0.000s` 只是舍入后的显示值）。

⚠️ **最后一行的名字**：探针的计时器在 `operation = schema[path][method]` **之后**才停，
所以那个数是「`from_asgi` + operation 查找」，不是 `from_asgi` 单独耗时。

⚠️ **「未归类」的构成**：探针只包住了 `generation/case.py` 模块级的那一个 `dispatch("after_call", …)`；
同函数 `:413-414` 还有 `self.operation.schema.hooks.dispatch("after_call", …)` **没有**被包，
它与 config 读取、`Response.from_requests()`、`_freeze_metadata` 等一起落在残差里。
被包住的那个 global dispatch 逐轮 ≤ 0.000009s；**其余探针外工作合计形成残差，未逐项计时**。

### 1.3 `no_lifespan` 对照组 —— 两次，其中一次是干净进程

唯一改动 = `tests/support/lifespan.py:63-83` 的 `no_lifespan(app)` 把 `app.router.lifespan_context` 临时换成 no-op；
其余（schema 构造、Case、transport、`call()`）与主用例逐字相同。

| 段 | 对照组-A（run-2 同进程，`profile-both-…txt:580-613`） | 对照组-B（**干净进程**，`control-fresh-process-20260906T105637.txt`） |
|---|---|---|
| ① `__enter__` 整体 | 中位 0.001s（max 0.004s） | 中位 0.000s（max 0.001s） |
| ② serialize_case | 0.000s | 0.000s（max 0.003s） |
| ③ request | 中位 0.005s | 中位 0.002s |
| ④ `__exit__` 整体 | 中位 0.001s（max 0.002s） | 中位 0.000s（max 0.001s） |
| 整次 `case.call()` | 中位 0.008s（0.006–0.011） | 中位 0.003s（0.002–0.007） |
| 该用例 blocked/轮 | `[0,0,0,0,0]` | `[0,0,0,0,0]` |
| session 门总账 | `=11 (blocked=11, advisory=0, unaccounted=0)`（11 全部来自主用例） | **`=0 (blocked=0, advisory=0, unaccounted=0)`** |
| pytest 结果 / rc | `1 failed, 1 passed`（failed 是主用例）/ rc=1 | **`1 passed, 1 deselected … in 1.03s` / rc=0** |
| `from_asgi` + 查找 | 0.022s（同进程第二次，热） | 0.629s（冷，与 run-1 的 0.626s 一致） |

**对照组-A 的两条限制**：它跑在主用例之后的**同一进程**里，复用同一个 `app.main.app`
（`tests/support/lifespan.py:67-70` 明写它是进程级单例），探针**没有**重建 app、没有清理
`app.state` / 模块级单例 / 缓存。所以 A 能证明的只是「该轮 `call()` 期间没有跑 lifespan，且没有新增被拦连接」，
**不能**证明被测对象等于「从未启动过的 app」。

**对照组-B 补上了「干净进程」这一维**：`-k no_lifespan_control` 把主用例 deselect 掉，整个 session
从头到尾 `blocked=0`、rc=0。它证明的是：**在一个没跑过任何 lifespan 的新进程里，这条路径同样不触发门、同样是毫秒级。**
它仍**不**证明「其余 205 个 operation 在这个状态下响应仍与 schema 相符」——那是判据 C，本卡未测。

**由 A/B 反推 lifespan 在 ①④ 里的占比**：同一探针、同一边界、同一段名，唯一变量是 lifespan。
① 的非 lifespan 余量（TestClient 构造 + portal 建）中位 ≤ 0.001s；④ 的非 lifespan 余量（portal 收）中位 ≤ 0.001s。
⇒ run-2 主用例 ① 的 19.082s 与 ④ 的 12.256s 里，毫秒量级之外的部分是 app lifespan。
（这是**同一 harness 内的减法**，不是跨测量反推。）

---

## 二 「20–50s 里 7.1s 之外的部分是什么」（完成条件 a 的必答项）

**段级归属：已定位，残差在毫秒量级。** 墙钟没有任何**可观测的**部分落在 schemathesis 的 hooks 或序列化上；
请求段（含应用处理）中位 9ms。绝大部分在 `with` 的进入与退出两头，
而那两头扣掉毫秒量级的 TestClient 构造与 portal 开销之后就是 app lifespan（§1.3）。

对 Z7-C 那两个 7.1s 的处置：

1. **本卡没有复现 Z7-C 的 7.1s，也不反推它的组成。**
   本卡实测 `__enter__` 整体中位 19.082s（run-2）/ 23.016s（run-1）。
   Z7-C 用的是 `fastapi.testclient.TestClient`，本卡链路上是 `starlette_testclient.TestClient`；
   vault 内容、缓存热度、计时起止边界均不受控。**这个 2.7–3.2 倍差本页不解释**，
   只主张「本机这条链路上，进入段是 19–23s」。
   ⚠️ 曾想用「本卡实测 `from_asgi` 只要 0.6s ⇒ 那 7.1s 的主项是 `import app.main`」做减法——**已撤回**：
   本卡的 0.626s 里还含 operation 查找（§1.2），且本卡**根本没有测 import**
   （探针在计时之前就 `from app.main import app` 了，conftest 更早就导过），Z7-C 的计时边界也未知。

2. **Z7-C 的计时表里没有「退出段」这一项。** （不写「从来没被量过」——它那行「`TestClient` 跑一次 lifespan」
   是否含退出，从表上看不出来。）本卡量到的是：退出段中位 12.256s / 12.638s，与进入段同量级，
   而它**每次调用都要付一遍**。

**段内归因（采样证据，强度明显低于 §1 的分段计时，如实标注）：**

采样器每 0.2s 读一次 `sys._current_frames()`，把该时刻所有线程的栈顶、以及每个线程最内层的 `backend/app` 帧，
按「当前段落」计数。⚠️ 三条已知限制：
(i) 段落标签先读、栈帧后取，两者之间可能跨段，且标签切换与计时起止不同步 ⇒ **存在错桶**；
(ii) 所有线程共用一个标签；
(iii) 「app 帧」的分母只含**当时有 app 帧的线程样本**，是条件分母。
⇒ 下面只能读作「采到的这一桶里，帧主要落在哪」，**不能换算成墙钟份额**；
错桶误差的上界本卡**没有**给出（0.2s 是采样休眠间隔，不是误差上界）。

- **进入段**：采到的 `backend/app` 帧几乎只有一处——`backend/app/services/wikilink_graph_service.py` 的
  `_build_sync`（run-2：该桶共 453 个 app 帧样本，447 个在 `_build_sync`，`:73` 446 + `:71` 1；run-1 是 474 / 480），
  对应 `backend/app/main.py:303` 的 `await wikilink_svc.build(settings.canvas_base_path)`。
  同桶的第三方栈顶帧（`bs4/builder/_lxml.py:494 feed` 85、`obsidiantools/md_utils.py:251` 40、
  `markdown/treeprocessors.py` 45、`html/parser.py` + `_markupbase.py` 18）都是 markdown 解析。
- **退出段**：栈顶前四是 `threading.py:1133 join`(512) / `selectors.py:548 select`(512) /
  `ssl.py:1140 read`(436) / `threading.py:373 wait`(231)，其后是 `httpcore/_backends/sync.py:128 read`(33)、
  `transformers/core_model_loading.py:787 _materialize_copy`(12)、
  `transformers/models/xlm_roberta/tokenization_xlm_roberta.py:81 __init__`(10)。
  日志侧：run-1 的 5 轮里 `Load pretrained SentenceTransformer: BAAI/bge-m3` 出现在 20 行上
  （其中 10 行是 structlog `"event"` 形态）⇒ **每轮观察到两条模型装载日志**。
  ⚠️ 这些都是**观测**。「是 `backend/app/main.py:320-334` 那个
  `asyncio.create_task(_eager_init_lancedb_singleton())` 在阻塞退出」是**推断，本卡未证明**：
  采样输出丢掉了线程身份与等待关系，因此装载**完成**次数、具体 task 身份、以及「谁在等谁」都没有闭合。
  TLS 读的对端同样未确认（未设 `HF_HUB_OFFLINE`，未抓包）。整条任务归因都属「线索，不是结论」。

**仍未定位的部分**：进入段内部各步骤的秒数拆分（`main.py:83-446` 约 20 个启动步骤没有各自计时）；
退出段里 TLS 读的对端与后台任务的身份 / 等待关系。

---

## 三 门下跑（完成条件 b）

不挂任何豁免 marker、不设 `W4_GUARD_NO_EXEMPT`、不改 `conftest.py` / 豁免面。

| 运行 | pytest 结果 | 门计数行 | rc |
|---|---|---|---|
| run-1（`profile-20260906T103504.txt` 末 5 行） | `1 failed … in 168.89s` | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=11 (blocked=11, advisory=0, unaccounted=0)` | **1** |
| run-2（`profile-both-20260906T104054.txt` 末 5 行） | `1 failed, 1 passed … in 160.98s` | 同上 `=11 (blocked=11, advisory=0, unaccounted=0)` | **1** |
| 对照组-B（`control-fresh-process-20260906T105637.txt` 末 4 行） | `1 passed, 1 deselected … in 1.03s` | `=0 (blocked=0, advisory=0, unaccounted=0)` | **0** |
| collect-only（`collect-only-20260906T104022.txt`） | `2 tests collected in 0.06s` | `=0 (…)` | 0 |

⛔ **rc 是 1，不是卡文预期的 3 —— 如实记，并给机制。**
`backend/tests/conftest.py:175-204` 的 `pytest_cmdline_main` wrapper 收口是（逐字）：

```python
197:    status = yield
198:    state = live_port_guard.STATE
199:    if state.unaccounted_blocked():
200:        status = 3
201:    elif state.blocked > 0 and status == 0:
202:        status = 3
203:    state.reported_status = status
204:    return status
```

`:199-200` 那条要求**有拦截到死没人结账**；本次 11 次全部被 `pytest_runtest_makereport`（`:141-158`）的结账哨兵
`take()` 走并转成用例失败 ⇒ `unaccounted=0`，不触发。
`:201-202` 那条是**兜底 belt**，前提是 `status == 0`；此时 `status` 已经是 1（用例被判红）⇒ 也不触发。
⇒ **正确的口径是「非零，且本卡观测到的形态是 1」**：`:202` 的 `status = 3` 只在「哨兵翻红被吃掉」的残余形态下才出现；
`:200` 那条在本卡的运行里**从未触发**，其行为本卡未验证。
对「能不能进 CI」这个问题结论不变（非零即红），但 Z7-C §3.5 写的「仍然会以 exit 3 收场」在**这一配置下不成立**。

被拦的 11 次全部是 `('::1', 7691, 0, 0)`（现网 Neo4j），发生在进入段内，分布 `[3, 2, 2, 2, 2]`，
owner 全部归到本用例，线程名 `asyncio-portal-*` 且**每轮不同**——印证「每次 `call()` 新建一个客户端、跑一遍 lifespan」。

**门本身不带退避**：`live_port_guard.py:513` 是 `raise RuntimeError(_block_message(address))`，立即抛。
⚠️ 这只证明**门自己**不等待；**调用方**捕获异常后是否重试 / 退避、以及那部分成本有多大，本卡**未测**。
所以不能据此断言「那 30s 与连库无关」。

**实验产物（完成条件 f）**：跑前三条路径**全部不存在**；跑后三条**全部被创建**——

| 路径 | 跑前 | 跑后 | gitignore 命中 |
|---|---|---|---|
| `backend/data/llm_call_logs.db` | ABSENT | 36864 B `53bb3d5f…83c9` | `backend/data/.gitignore:7 *.db` |
| `backend/data/neo4j_memory.json` | ABSENT | 148 B `66bf3abb…f08b` | `backend/data/.gitignore:6 *_memory.json` |
| `backend/app/data/vault_index_pending__canvas_vault.jsonl` | ABSENT（目录都没有） | 0 B `e3b0c442…b855` | `.gitignore:250 backend/app/data/vault_index_pending*.jsonl` |

`git status --porcelain` 不含这三条。**这本身是成本的一部分**：跑一次会在工作树里落三个文件。

---

## 四 门侧三问（完成条件 c）

### ① `tests/contract/**` 该不该进豁免面？——**不该**

1. **语义不对。** `live_port_guard.py:159-163` 自陈 `EXEMPT_PATH_PREFIXES = ("integration", "e2e")`（`:164`）
   对应的是「本来就要连真库」的两类测试。合约测试的语义相反：它验的是**响应体与 OpenAPI schema 相符**，
   与图数据库里有什么数据无关。
2. **豁免是目录级、且对未来生效的旁路。** `:163` 原注释就写着「⚠️ 这是**有意的旁路**：新写的测试只要放进
   tests/integration/ 就自动免拦」。把 `contract` 加进 `:164`，`tests/contract/` 下现有 6 个文件与今后所有新文件
   一并免拦，远超本次要解决的那一个。
3. **豁免只是把「拦住」换成「不拦」；不拦之后会发生什么，本卡没测。**
   `live_port_guard.py:253-255`：豁免命中 → `advisory += 1` 且 `record()` 返回 `False` ⇒ `:513` 的 `raise` 不执行
   ⇒ **连接尝试得以继续**（⚠️ 这**不等于**连接一定建立成功）。
   如果连上了，lifespan 后续要跑的是 `main.py:173` 的 `CREATE FULLTEXT INDEX`（DDL）、`:343` 的
   `get_canvas_schema_gate().verify()`、`:363` 的 `rel_svc.sync(..., execute=True)`、`:392` 的
   `backfill_vault(..., execute=True)`；后两条是**写**路径，且分别挂在 `if memory_svc is not None:`（`:172`）与
   `if _worker_graphiti is not None:`（`:386`）之下——**连上库正是让这些条件成立的前提**。
   本卡**没有**去真的放行一次来验证（那样会连上用户现网库），
   所以这一条是**读代码得出的风险判断，不是实测**。
   另注：豁免走的是 per-item ContextVar，`conftest.py:124-125` 明写裸线程默认 `<unknown>` 且**永不豁免**，
   所以「加进豁免面」也不等于该用例的**所有**连接都会被放行。

### ② 不豁免时的替代路径，各自代价

| 路径 | 效果（blocked） | 效果（耗时） | 代价 / 证据状态 |
|---|---|---|---|
| **(a) mock Neo4j** | 未测 | 未测 | 连库入口至少 7 处：`main.py:163` `get_memory_service()`、`:173` `ensure_fulltext_index()`、`:216` `recover_outbox()`、`:276` `initialize_graphiti(neo4j_uri=settings.NEO4J_URI, …)`、`:343` `get_canvas_schema_gate().verify()`、`:363` `rel_svc.sync(execute=True)`、`:392` `backfill_vault(execute=True)`；mock 点分散在 `app/clients/neo4j_client.py::get_neo4j_client`、`app/services/memory_service.py::get_memory_service`、`app/services/episode_worker.py::get_episode_worker` 三个单例工厂。⚠️「它解决不了耗时」是**基于采样归因的判断**（进入段的 app 帧主要在 wikilink 图 eager-build），**本卡未做「只屏蔽连接、不动其余」的对照实验** |
| **(b) 复用一个已 startup 的客户端** | 未测；机制上 lifespan 次数从 N 降到 1，**不到 0** ⇒ `conftest.py:141-158` 的哨兵仍会判红 | 未测 | 要改第三方源码 `schemathesis/transport/asgi.py:21` 那个硬编码的 `with`，或在本仓侧注入自定义 transport。**单独用它不足以进 CI**（Z7-C §3.5 这一条判断成立） |
| **(c) `no_lifespan`（仓内已有）** | **0**（对照组-A 该用例 5/5 轮；对照组-B **整 session** blocked=0，rc=0） | **中位 0.008s / 0.003s**（实测） | 一行 fixture（`tests/support/lifespan.py:63-83`；需持有到整个 `with TestClient(...)` 之外，而那个 `with` 在第三方 transport 里 ⇒ 实际要在测试模块里持一个 module/session 级的 `no_lifespan(app)`）。**真正的代价在判据 C** |

**(c) 的代价必须说清楚**：`no_lifespan` 不碰 `app.routes` / `app.dependency_overrides` / 端点函数
（`tests/support/lifespan.py:29-31`），所以路由、依赖注入、中间件、响应模型都是真的；
但它**只**替换 `app.router.lifespan_context`，`app.main.app` 仍是进程级单例（`:67-70`）。
本卡只测了 `GET /api/v1/health` 一个 operation，**没有**证明其余 205 个 operation 在这个状态下的响应仍与 schema 相符，
也**没有**逐一检查 `app.state.*` 上那些启动期才装配的对象对各 operation 的影响。

### ③ 豁免会不会重开 W4 门想堵的洞？——**会，对命中豁免的那些连接三层一起关**

`conftest.py` 的两条 `status = 3` 各自堵什么：

- **`:199-200`（`state.unaccounted_blocked()`）**：堵「拦截发生了但没有任何用例买单」的窗口——
  迟到线程 / collection 期 / 未知线程（docstring `:179`）。
- **`:201-202`（`state.blocked > 0 and status == 0`）**：兜底 belt，堵「哨兵翻红被 xfail 之类机制吃掉」的残余形态，
  原文「非豁免连接尝试绝不允许以『全绿』收场」（docstring `:180-182`）。

而命中豁免的连接**进不到这两条**：`is_exempt()`（`live_port_guard.py:1061-1083`）返回 True →
`begin_item(nodeid, exempt=True)`（`conftest.py:132-133`）→ `record()` 走 `:253-255` 的 advisory 分支 →
`blocked` 不增、`pending` 不记账 → 哨兵 `:141-158` 无账可结 → 两条 `status = 3` 的前提都不成立。
**对命中豁免的那些连接，一次关掉的是「拦截 + 结账哨兵 + 两条兜底」三层。**
（不命中豁免的——例如裸线程发起的——仍按原样拦，见 ① 末注。）

`tests/support/lifespan.py:10-17` 早就把这个洞写清楚了（连生产库 + 动生产库 schema + 读用户真实笔记库）。
本卡把它变成了数字：**一次 `case.call()` = 一次完整 lifespan = 2–3 次到 `::1:7691` 的连接尝试**（本卡里全部被拦下）。

---

## 五 接 CI 的可行性判据与成本清单（完成条件 d）

### 5.1 判据（都达标才值得排「接入卡」）

| 判据 | 阈值 | 当前值 | 达标？ |
|---|---|---|---|
| **A · 单次 `case.call()` 墙钟** | 中位 ≤ 0.1s（现测 request 段是 9ms，留一个数量级余量） | 中位 **31.636s**（run-2；十样本区间 23.117–37.045s） | ✗ |
| **B · 门下总账** | 不改 `EXEMPT_PATH_PREFIXES`(`:164`) / `EXEMPT_MARKERS`(`:157`) / 不设 `W4_GUARD_NO_EXEMPT`(`:175`) 的前提下，整轮 `blocked=0, advisory=0, unaccounted=0` 且 rc=0 | `blocked=11`，rc=1 | ✗ |
| **C · 被测对象等价性** | 若达标手段是 `no_lifespan`，须证明**全部** operation 在该状态下的 failed 集合与启动态一致 | **未测**（本卡只测 1 个 operation） | 未知 |
| **D · 环境可移植** | A/B 的数字须在 CI 镜像（Python 3.11/3.12）上复测 | **未测**（本机 3.14.4） | 未知 |

判据 A 与 B **同源**：两者都来自「每次 `call()` 跑一遍完整 lifespan」。
§四(c) 的 `no_lifespan` 是目前唯一一条**已实测**能同时把 A 打到毫秒量级、把 B 打到 blocked=0 的路径
（对照组-B：干净进程、整 session blocked=0、rc=0）。
⚠️ 但该实测只覆盖 `GET /api/v1/health` 一个 operation；其余 operation 的耗时与门总账**未测**。
代价整个转移到判据 C 上——**这正是下一张卡该做的事，本卡不裁**。

### 5.2 成本清单

| 项 | 内容 |
|---|---|
| 改造工作量（若走 `no_lifespan`） | 测试模块内一个 module/session 级 fixture 持有 `no_lifespan(app)`；不改 `conftest.py`、不改 `backend/app/**`、不改第三方库 |
| 举证工作量（判据 C） | 一次「启动态 vs 未启动态」的全 operation 对照跑，逐 operation 比 failed 集合。**启动态那一半在本机跑不成**（门会判红），需要先解决 B 或在 CI 镜像上跑 |
| 改造工作量（若走复用客户端） | 需在本仓侧包一层 transport 以避开 `schemathesis/transport/asgi.py:21` 的硬编码 `with`；且**仍不满足判据 B** |
| CI 时间 | **未测，本页不给任何估算**，理由见 §六 |
| 副作用 | 每跑一次落三个文件（§三表）；启动链含对现网库的 DDL 与写调用（`main.py:173/:343/:363/:392`，后两条有前置条件），必须靠 W4 门或 `no_lifespan` 挡住 |
| 依赖维护 | `test_openapi_contract.py:76-83` 的 `load_all_checks()` + `CHECKS.get_by_names()` 是 **4.x 专用**（`:74-75` 已声明依赖下限须 ≥4.0）；生产用例还带 `max_examples=10` 与 `phases=[explicit, generate]`（`:38-41`），且走 `call_and_validate`（`:83`）而非 `call()` |
| Dredd | `scripts/spec-tools/dredd-hooks.js` 仍在树上（6643 B）。**本卡不裁它的去留**，Z7-C 已裁「退役」，执行归别的卡 |

---

## 六 口径边界与「本卡未证明什么」

### 6.1 数字口径

**关于 Z7-C 的 208.70s**（沿用其 round-2 的收窄，不放宽）：

- `in 208.70s` 是**整个 pytest session** 的耗时，含收集（约 36s）、fixture、执行与报告，不是单个 operation 的耗时。
- 那次是 `1 failed, 186 deselected`（`-k` 过滤 + `-x` early stop），**分母不是 206**。
- 那 9 个是 **explicit** example：不计入 `max_examples`，且失败后不进入随机生成阶段。
- **本页不对它做任何形式的倍数外推。**

**关于本卡的单次 `case.call()` 数字**：同样**不做倍数外推**，但理由与上面**不同**——
本卡的单次数字**已经排除**了一次性的 schema 构造，所以「乘起来会重复计一次性成本」这个理由**在这里不成立**。
真正的理由是：本卡只测了 `GET /api/v1/health` 一个 operation、只跑了 `call()` 而非生产用例的 `call_and_validate()`、
没有覆盖 `max_examples` 与 explicit/generate 两阶段，**跨 operation 的耗时差异、每 operation 的实际 example 次数、
校验开销均未测**，因此任何「全部跑完要多久」的数字都没有依据。
同理，**本页不给「复用客户端后每 operation 约 X 毫秒」或「blocked 会从 11 降到 2~3」这类数字**——
它们都是未实施方案的推测。

### 6.2 本卡未证明什么

1. **不证明 ①④ 两段等于「纯 app lifespan」。** 它们是 `TestClient.__enter__/__exit__` 的整体，含构造与 portal 建/收。
   lifespan 的占比由 §1.3 的对照组减法给出（非 lifespan 余量在毫秒量级），不是直接测量。
2. **不证明启动过程内部每一步各花多少秒。** 约 20 个启动步骤没有各自计时；「主项是 wikilink 图 eager-build」
   是**采样证据**，且受错桶、线程混合、条件分母三条限制（§二），**不能换算成墙钟份额**，误差上界未给出。
3. **不证明退出段里那个后台任务的身份与等待关系。** 「每轮观察到两条模型装载日志」「退出段采到 TLS 与
   transformers 帧」是观测；「是 `_eager_init_lancedb_singleton` 在阻塞退出」是推断，未闭合。TLS 对端未确认。
4. **不证明「六段之和 ≈ 墙钟」能独立排除漏计与重复计。** 串行性由读源码得出；残差只是补充旁证，
   且只覆盖当前这条固定成功路径。
5. **不证明残差里剩下的是哪几行。** 探针只包了模块级的 `after_call` dispatch；`case.py:413-414` 的
   `schema.hooks.dispatch` 与其余探针外工作未逐项计时。
6. **不证明两轮由同一字节版本的探针产出。** run-1 用的是更早一版（§1.0），承重数字以 run-2 与对照组-B 为准。
7. **不反推 Z7-C 那个 7.1s 的组成，也不主张它测错了。** 本卡没测 `import app.main`，
   `from_asgi` 那个数还含 operation 查找，两次测量的边界与环境均不可比。
8. **不证明「屏蔽连接后耗时会怎样」。** 门自身立即抛出（`live_port_guard.py:513`），但调用方的重试 / 退避成本未测，
   也没有做「只屏蔽连接、不动其余」的对照实验。
9. **不证明豁免后连接会成功建立、DDL / 写调用会真的执行。** §四① 第 3 条是读代码得出的风险判断；
   本卡没有放行任何一次连接。
10. **不证明 `no_lifespan` 下其余 205 个 operation 的响应仍与 schema 相符**（判据 C 未测）。
    对照组-A 还额外受「同进程、复用已被启动过的 app 单例」限制；对照组-B 解决了进程新鲜度，但仍只测 1 个 operation。
11. **不证明 CI 机器上的数字。** 本机 Python 3.14.4，CI 是 3.11/3.12，未控制。
12. **不证明 rc 在别的配置下也是 1。** `conftest.py:199-200` 那条在本卡的运行里从未触发，其行为未被本卡验证。
13. **不证明本探针与生产用例逐字等价。** 三处已声明差异（不走 hypothesis ⇒ `case._meta is None`、
    用 `call()` 而非 `call_and_validate()`、schema 在函数体内建）写在 `profile_harness.py` 模块 docstring 里。
    正面佐证：实测单次调用落在 Z7-C 观察到的 20–50s 区间内（23.117–37.045s）。
14. **不裁 Dredd 该复活还是该退役**（Z7-C 已裁乙），**不改 CI**——`contract-test` job 维持
    `.github/workflows/api-spec-sync.yml:330` 的 `if: false`；**不改** `conftest.py` / 豁免面 /
    `backend/app/**` / `dredd-hooks.js` / `live_port_guard.py`。
