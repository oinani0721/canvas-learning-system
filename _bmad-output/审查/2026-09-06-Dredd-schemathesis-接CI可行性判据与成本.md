# Dredd / schemathesis 接 CI —— 可行性判据与成本

> 卡：`CARD-TOOL-dredd-prereq`（`[BATCH-2026-09-05-第十二批]`）· 车道 `card-y5-review`
> 代码树：`67ee147c`（Y5-C 末 commit）+ 一个未入库的临时探针（跑完已删）
> 环境：本机 macOS / Python 3.14.4 / pytest 9.0.2 / schemathesis 4.14.3 / hypothesis 6.151.10
> 前作：`_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md`（Z7-C，已裁「Dredd 退役 + schemathesis 接 CI」，两个前置未解）
> 本页**零 CI 改动、零生产改动**，只出证据与判据。原始输出全部在 `evidence-dredd-prereq/`。
>
> **版本沿革**：v1（送审 Codex，sha256 `c8f75787…8a55`）→ **v2**（Codex round-1 整改，sha256 `ad06f0d5…0f86`）
> → **v3 = 本版**（Claude 多代理二轮内部复核整改，77 agent / 35 条初审 / 18 条存活 + 完整性批判 10 条）。
> ⚠️ **v3 未再送外审。** 逐条处置见 `_bmad-output/验收单/UAT-CARD-TOOL-dredd-prereq-2026-09-06.md` §五。
> v2 引入过两处**新的事实错误**（启动链条件绑定绑错、减法归属过强），由二轮复核抓出，本版已修——见 §四①.3 与 §1.3。

---

## 〇 一句话结论

单次 `case.call()` 的墙钟（十个样本 **23.117–37.045s**）**绝大部分**落在 `with asgi.get_client(application) as client:`
这个包装区间的两头——进入（中位 19.082s，run-2）与退出（中位 12.256s，run-2）；
schemathesis 自身的请求段中位 9ms（run-2），hooks 与序列化两段的中位在显示精度下都是 0.000s（序列化实测 max 0.011s）。
六段之和与整次墙钟的残差为 0.000193–0.001099s。

**那两头里 lifespan 占多少——只能说到这一步**：同一探针、同一边界，把 lifespan 换成 no-op 后，
进入段中位 0.001s、退出段中位 0.001s（干净进程里两段中位都是 0.000s）。
⇒ ①④ 里毫秒量级之外的部分**由「跑了 app lifespan」引发**。
⚠️ 但其中**多少发生在 `app.main.lifespan` 函数体内、多少发生在 portal / 事件循环收尾去排干 lifespan 期间
`asyncio.create_task` 派生的后台任务，本卡未分离**——对照组的 lifespan 是 no-op，那些后台任务根本不存在，
减法在物理上看不见它们。详见 §1.3 末段。

**门那一侧**：同一支 `no_lifespan` 探针在**干净进程**里单独跑，整个 session `blocked=0`、`rc=0`、1.03s 跑完。
⚠️ 但这一个 operation（`GET /api/v1/health`）恰好在未启动态下会**跳过它自己那次 Neo4j 调用**
（`backend/app/api/v1/endpoints/health.py:148-154` 的 `is_real_neo4j` 三合一判断不成立 ⇒ 不发 ping），
所以 `blocked=0` 里有多少是 `no_lifespan` 的功劳、多少是这个端点自身的条件分支，**本卡分不开**。

⇒ Z7-C 留下的两个前置（耗时 / 门下退出码非零）**是两个互相独立的接入条件**（治好一个不自动治好另一个），
但它们**有同一个根源**（每次 `call()` 跑一遍完整 lifespan），所以存在一条**候选**路径能同时压住两者。
该路径的代价（被测对象等价性）本卡**未测**，见判据 C。

---

## 一 分段 profile（完成条件 a）

### 1.0 探针出处（⚠️ 三轮不同源程度不同，逐轮登记）

存档：`evidence-dredd-prereq/profile_harness.py`，sha256 `70378e38…fce1`。

| 轮次 | 时刻 | 与存档探针的同源性 | 证据 |
|---|---|---|---|
| **run-1** | 10:35:04 | **不同源**（更早一版） | 见下方三处差异 |
| **run-2 + 对照组-A** | 10:40:54 | **逐字节同源** | `harness-sha256-20260906T104022.txt`（10:40:22 取，早于本轮开跑） |
| **对照组-B** | 10:56:37 | 由「从存档副本复制回工作树」这一动作保证，**无存档级证据** | 见下方说明 |

- **run-1 的三处差异**：① 只有 1 个用例，没有 `no_lifespan` 对照组
  （独立证据：`collect-only-20260906T103437.txt` 是 `1 test collected`，`collect-only-20260906T104022.txt` 是 `2 tests collected`）；
  ② 没有 `_reset_ledger()`；③「未归类」的打印精度是 3 位小数（run-1 因此显示 `0.000s`），run-2 起改成 6 位。
  前两处不进主用例的测量路径（`_reset_ledger()` 在首次使用时是空操作），第三处只影响显示。
  **「同一脚本逐字节产出两轮」这个说法本页不主张。**
- **对照组-B 的同源性如实说**：那一轮的工作树探针是从存档副本 `profile_harness.py` **复制**回
  `backend/tests/contract/` 后跑的，复制后当场做过 `shasum`——但**那次 shasum 的输出没有落盘**，
  只存在于作业记录里；跑完探针又被删除。唯一落盘的 sha 快照取于 10:40:22，比对照组-B 早 16 分钟。
  ⇒ 同源性由「复制」这一动作保证，**不由存档证据保证**。下次跑承重对照组，前后各落一份 shasum。
- **承重数字以 run-2 与对照组-B 为准**；run-1 的角色是先导复现性对照。

### 1.1 分段边界（先说清楚量的到底是什么）

固定 Case = `GET /api/v1/health`；schema 用与 `backend/tests/contract/test_openapi_contract.py:27` **逐字相同**的
`schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)`；同一 ASGI transport，不换 httpx。

⚠️ 下表**按实际时序排**。段名前缀里的 `1_`/`2_`/`3_`/`4_` 只是探针里的**分组记号**，不是时序序号——
`2_hooks_before_call` 实际发生在 `1_client_construct` **之前**（见表下的调用顺序）。

| 时序 | 段 | 探针实际计时的**是什么** | 源码锚 |
|---|---|---|---|
| 1 | `2_hooks_before_call` | `schemathesis.generation.case` 模块级的 `dispatch("before_call", …)`（**只有这一个**） | `generation/case.py:362-363` |
| 2 | `1_client_construct` | `starlette_testclient.TestClient(app)` 的构造 | `schemathesis/python/asgi.py:9-12` |
| 3 | `1_lifespan_startup` | **`client.__enter__()` 整体** = portal（线程 + 事件循环）建起 **+** app lifespan startup | `schemathesis/transport/asgi.py:21` 的 `with` 进入 |
| 4 | `2_serialize_case` | `RequestsTransport.serialize_case` | `transport/requests.py:146` |
| 5 | `3_request` | `_request(**data)`（= 那个 TestClient 的 `request`），**含应用处理本身** | `transport/requests.py:195,197` |
| 6 | `4_lifespan_shutdown` | **`client.__exit__()` 整体** = app lifespan shutdown **+** portal / 事件循环 / 线程收尾 | `schemathesis/transport/asgi.py:21-22` 的 `with` 退出 |

⚠️ **第 3 段与第 6 段不等于「纯 app lifespan」**，它们是包装区间；第 5 段也不等于「纯 schemathesis 开销」，它含应用处理。
把 lifespan 单独摘出来靠的是 §1.3 的对照组，而那个减法**有它自己的边界**（§1.3 末段）。

**串行性由源码顺序读出**（`Case.call()` :362 `dispatch("before_call")` → :380 `transport_.send` →
`with` 进入（construct + startup）→ `super().send` 内 serialize → `_request` → `with` 退出）：六段首尾相接、无嵌套。
残差小是**补充旁证，不是独立证明**——残差 = 漏计量 − 重复计量，两者可以互相抵消。
本次调用链读源码未见重叠，但该结论只覆盖**当前这条固定成功路径**，不推广到 hook 重入或并发调用。

### 1.2 主用例（门下、完整 lifespan）—— 两次独立运行

存档：`evidence-dredd-prereq/profile-20260906T103504.txt:516-569`（run-1）
　　　`evidence-dredd-prereq/profile-both-20260906T104054.txt:516-570`（run-2）

| 段 | run-1 中位 / 极差 | run-2 中位 / 极差 |
|---|---|---|
| client construct | 0.000s / 0.000s | 0.000s / 0.000s |
| **`__enter__` 整体** | **23.016s** / 15.133s（min 10.467 / max 25.601） | **19.082s** / 3.551s（min 18.092 / max 21.643） |
| hooks before_call | 0.000s / 0.000s | 0.000s / 0.000s |
| serialize_case | 0.000s / 0.006s | 0.000s / 0.011s |
| request（含应用处理） | 0.008s / 0.006s | 0.009s / 0.005s |
| **`__exit__` 整体** | **12.638s** / 2.678s（min 11.339 / max 14.017） | **12.256s** / 2.372s（min 11.150 / max 13.523） |
| 整次 `case.call()` | 中位 35.630s（min 23.117 / max 37.045） | 中位 31.636s（min 30.133 / max 33.907） |
| 未归类（总 − 六段和） | ≤ 0.001s（run-1 只打到 3 位小数） | 0.000193–0.001099s（逐轮 0.001099 / 0.000343 / 0.000199 / 0.000193 / 0.000245） |
| `from_asgi` 建 schema **+ operation 查找** | 0.626s（blocked+0，paths=193） | 1.322s（blocked+0，paths=193） |

n=5/段/轮次，两轮共 10 个样本，整次墙钟的全体区间是 **23.117–37.045s**。
⚠️ `__enter__` 段的**单样本**跨度比中位数宽得多（run-1 low 到 10.467s）；说「进入段是 19–23s」指的是**两轮的中位数**，不是样本区间。

**三条读表须知**：

1. **中位数不能相加**——本页不写「某几段合计中位 X」。可直接读的是：request 段中位 9ms（run-2）；
   hooks 与序列化两段的中位在显示精度下是 0.000s（序列化 max 0.011s，即 `0.000s` 只是舍入后的显示值）。
2. **最后一行的名字**：探针的计时器在 `operation = schema[path][method]` **之后**才停
   （`profile_harness.py:290-300`），所以那个数是「`from_asgi` + operation 查找」，不是 `from_asgi` 单独耗时。
3. **存档里印的是「四段和」，实际求和的是六段**——那是脚本变量名 `four` 留下的错名
   （`profile_harness.py:255` 的元组有 6 个元素）。按 §1.2 给的行号去追溯的读者会看到「四段和」，不是抄错。
4. **存档里的实时账印 `unaccounted=11`**（run-1:569 / run-2:570），因为那一行打印在结账哨兵 `take()` **之前**；
   session 收口行（run-1:1213 / run-2:1257）才是 `unaccounted=0`。§三 抄的是收口行。

**未归类的构成**：探针只包住了 `generation/case.py` 模块级的那一个 `dispatch("after_call", …)`；
同函数 `:413-414` 还有 `self.operation.schema.hooks.dispatch("after_call", …)` **没有**被包，
它与 config 读取、`Response.from_requests()`、`_freeze_metadata` 等一起落在残差里。
被包住的那个 global dispatch 逐轮 ≤ 0.000009s；**其余探针外工作合计形成残差，未逐项计时**。

### 1.3 `no_lifespan` 对照组 —— 两次，其中一次是干净进程

唯一**被人为改动**的变量 = `tests/support/lifespan.py:63-83` 的 `no_lifespan(app)` 把
`app.router.lifespan_context` 临时换成 no-op；其余（schema 构造、Case、transport、`call()`）与主用例逐字相同。
（进程新鲜度等其余变量并未控制——见下方两组各自的限制。）

| 段 | 对照组-A（run-2 同进程，`profile-both-…txt:580-613`） | 对照组-B（**干净进程**，`control-fresh-process-20260906T105637.txt`） |
|---|---|---|
| `__enter__` 整体 | 中位 0.001s（max 0.004s） | 中位 0.000s（max 0.001s） |
| serialize_case | 0.000s | 0.000s（max 0.003s） |
| request | 中位 0.005s | 中位 0.002s |
| `__exit__` 整体 | 中位 0.001s（max 0.002s） | 中位 0.000s（max 0.001s） |
| 整次 `case.call()` | 中位 0.008s（0.006–0.011） | 中位 0.003s（0.002–0.007） |
| 该用例 blocked/轮 | `[0,0,0,0,0]` | `[0,0,0,0,0]` |
| session 门总账 | `=11 (blocked=11, advisory=0, unaccounted=0)`（11 全部来自主用例） | **`=0 (blocked=0, advisory=0, unaccounted=0)`** |
| pytest 结果 / rc | `1 failed, 1 passed`（failed 是主用例）/ rc=1 | **`1 passed, 1 deselected … in 1.03s` / rc=0** |
| `from_asgi` + 查找 | 0.022s（同进程第二次，热） | 0.629s（冷，与 run-1 的 0.626s 一致） |

⚠️ `3_request` 段在三种配置下是 0.009 / 0.005 / 0.002s 三个不同的中位数。
本页凡写「request 段中位 9ms」处，指的都是 **run-2 主用例**那一个。三者为何不同（进程热度？未启动态下端点走了更短的分支？）**本卡未解释**。

**对照组-A 的限制**：它跑在主用例之后的**同一进程**里，复用同一个 `app.main.app`
（`tests/support/lifespan.py:67-70` 明写它是进程级单例），探针**没有**重建 app、没有清理
`app.state` / 模块级单例 / 缓存。所以 A 能证明的只是「该轮 `call()` 期间没有跑 lifespan，且没有新增被拦连接」。

**对照组-B 补上「进程新鲜度」这一维，但它同时翻转了两个变量**（lifespan + 进程），
且「干净进程」≠「没 import 过 app」——`backend/tests/conftest.py:22-31` 在收集期就 `from app.main import app`。
它能证明的是：**在一个没跑过任何 lifespan 的新进程里，这条路径不触发门、且是毫秒级**。

⚠️ **对照组-B 的 `blocked=0` 有一部分不是 `no_lifespan` 的功劳。**
被测的 `GET /api/v1/health` 端点里，`backend/app/api/v1/endpoints/health.py:148-152` 先算
`is_real_neo4j = initialized and mode == "NEO4J" and health_status`，`:154` 只有它为真才发
`RETURN 1 AS ping`（`:157-160`）。未启动态下这三个条件不成立 ⇒ **该端点自己跳过了它唯一一次 Neo4j 调用**，
走 `:171-172` 的 `not_initialized` 分支。⇒ 不能由这一个 operation 推出「`no_lifespan` 能把整轮打到 blocked=0」——
仓内是否存在没有这层条件保护的端点，本卡未逐个核查。

**⛔ 减法的边界（这一段是 v3 新加的，v2 在这里说过头了）**

由 A/B 反推「lifespan 在 ①④ 里的占比」时，隐含前提是：**同一边界下，portal 建/收的成本与 lifespan 是否跑无关。**
这个前提**本卡未验证**，且本页数据从两个方向对它不利：

1. 连**不含** portal 建/收的 `3_request` 段都在三种配置下 0.002 / 0.005 / 0.009s 地变，
   「同一段名 = 同一成本」这个隐含假设整体不成立。
2. 主用例退出段的采样栈顶是 `threading.py:1133 join` / `ssl.py:1140 read` / transformers 模型装载（§二）——
   那是 portal / 事件循环收尾在**排干 lifespan 期间 `asyncio.create_task` 派生的后台工作**
   （`backend/app/main.py:334` 是 fire-and-forget，`:447-513` 的 shutdown 块逐行读下来**没有一处 await 它**）。
   这既不在 `app.main.lifespan` 函数体内，也不是对照组里量到的那个「≤1ms 的 portal 收尾」——
   **对照组里没有 lifespan，就没有东西可排，减法在物理上看不见它。**

⇒ 因此本页只主张：**①④ 里毫秒量级之外的部分由「跑了 app lifespan」引发**；
其中「lifespan 函数体内」与「portal 收尾等待 lifespan 派生的后台任务」两者的比例，**本卡未拆**。
（Codex round-1 HIGH-1 要的是把两者**分别计时**；本卡没有做到，v2 曾用这个减法冒充了分离，v3 撤回。）

---

## 二 「20–50s 里 7.1s 之外的部分是什么」（完成条件 a 的必答项）

**段级归属：已定位到「进入段 / 退出段」，残差在毫秒量级。**
落在 schemathesis 的 hooks 与序列化上的部分不超过毫秒量级（序列化实测 max 0.011s、hooks max 0.000s）；
请求段（含应用处理）中位 9ms（run-2）。绝大部分在 `with` 的进入与退出两头。
**再往下的组件归属（lifespan 函数体 vs portal 收尾）本卡未拆**，见 §1.3 末段。

对 Z7-C 那两个 7.1s 的处置：

1. **本卡没有复现 Z7-C 的 7.1s，也不反推它的组成。**
   本卡实测进入段中位 19.082s（run-2）/ 23.016s（run-1）。
   Z7-C 用的是 `fastapi.testclient.TestClient`，本卡链路上是 `starlette_testclient.TestClient`；
   vault 内容、缓存热度、计时起止边界均不受控。**这个 2.7–3.2 倍的中位数差本页不解释**，
   只主张「本机这条链路上，进入段的中位数是 19–23s」（单样本可以低到 10.467s，见 §1.2）。
   ⚠️ 曾想用「本卡实测 `from_asgi` 只要 0.6s ⇒ 那 7.1s 的主项是 `import app.main`」做减法——**已撤回**：
   本卡的 0.626s 里还含 operation 查找（§1.2），且本卡**根本没有测 import**
   （探针在计时之前就 `from app.main import app` 了，conftest 更早就导过），Z7-C 的计时边界也未知。

2. **Z7-C 的计时表里没有「退出段」这一项。**（不写「从来没被量过」——它那行「`TestClient` 跑一次 lifespan」
   是否含退出，从表上看不出来。）本卡量到的是：退出段中位 12.256s（run-2）/ 12.638s（run-1），与进入段同量级，
   而它**每次调用都要付一遍**。

**段内归因（采样证据，强度明显低于 §1 的分段计时，如实标注）：**

采样器每 0.2s 读一次 `sys._current_frames()`，把该时刻所有线程的栈顶、以及每个线程最内层的 `backend/app` 帧，
按「当前段落」计数。⚠️ 三条已知限制：
(i) 段落标签先读、`sys._current_frames()` 后取，两者之间可能跨段，且标签切换与计时起止不同步 ⇒ **存在错桶**；
(ii) 所有线程共用一个标签；
(iii)「app 帧」的分母只含**当时有 app 帧的线程样本**，是条件分母。
⇒ 下面只能读作「采到的这一桶里，帧主要落在哪」，**不能换算成墙钟份额**；
错桶误差的上界本卡**没有**给出（0.2s 是采样休眠间隔，不是误差上界）。

- **进入段**（下列计数均取自 **run-2**，`profile-both-…txt:539-566`）：采到的 `backend/app` 帧几乎只有一处——
  `backend/app/services/wikilink_graph_service.py` 的 `_build_sync`：该桶共 **453** 个 app 帧样本，其中 **447** 个在
  `_build_sync`（`:73` 446 + `:71` 1）。run-1 同一处是 **474** 个，该桶共 **480** 个。
  对应 `backend/app/main.py:303` 的 `await wikilink_svc.build(settings.canvas_base_path)`。
  同桶的第三方栈顶帧（`bs4/builder/_lxml.py:494 feed` 85、`obsidiantools/md_utils.py:251` 40、
  `markdown/treeprocessors.py` 45、`html/parser.py` + `_markupbase.py` 18）都是 markdown 解析。
- **退出段**（同为 **run-2**）：栈顶按计数降序完整列出——`threading.py:1133 join` 512 /
  `selectors.py:548 select` 512 / `ssl.py:1140 read` 436 / `threading.py:373 wait` 231 /
  `httpcore/_backends/sync.py:128 read` 33 / `ssl.py:1372 do_handshake` 22 /
  `httpcore/_utils.py:37 is_socket_readable` 15 / `transformers/core_model_loading.py:787 _materialize_copy` 12 /
  `transformers/models/xlm_roberta/tokenization_xlm_roberta.py:81 __init__` 10。
  日志侧：run-1 的 5 轮里 `Load pretrained SentenceTransformer: BAAI/bge-m3` 出现在 20 行上
  （其中 10 行是 structlog `"event"` 形态）⇒ **每轮观察到两条模型装载日志**。
  ⚠️ 这些都是**观测**。「是 `backend/app/main.py:320-334` 那个
  `asyncio.create_task(_eager_init_lancedb_singleton())` 在阻塞退出」是**推断，本卡未证明**：
  采样输出丢掉了线程身份与等待关系，因此装载**完成**次数、具体 task 身份、以及「谁在等谁」都没有闭合。
  TLS 读 / 握手的对端同样未确认（未设 `HF_HUB_OFFLINE`，未抓包）。整条任务归因都属「线索，不是结论」。

**仍未定位的部分**：进入段内部各步骤的秒数拆分（`main.py:83-446` 约 20 个启动步骤没有各自计时）；
退出段里 TLS 的对端与后台任务的身份 / 等待关系；以及 §1.3 末段那条「lifespan 函数体 vs portal 收尾」的比例。

---

## 三 门下跑（完成条件 b）

不挂任何豁免 marker、不设 `W4_GUARD_NO_EXEMPT`、不改 `conftest.py` / 豁免面。

| 运行 | pytest 结果 | 门计数行（session 收口行） | rc |
|---|---|---|---|
| run-1（`profile-20260906T103504.txt:1213`，倒数第 6 行） | `1 failed … in 168.89s` | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=11 (blocked=11, advisory=0, unaccounted=0)` | **1** |
| run-2（`profile-both-20260906T104054.txt:1257`，倒数第 6 行） | `1 failed, 1 passed … in 160.98s` | 同上 `=11 (blocked=11, advisory=0, unaccounted=0)` | **1** |
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

rc 能停在 1，需要**三**道门都不触发：

- **`:199-200`**：要求有拦截到死没人结账；本次 11 次全部被 `pytest_runtest_makereport`（`:141-158`）的结账哨兵
  `take()` 走并转成用例失败 ⇒ `unaccounted=0`，不触发。
- **`:201-202`**（兜底 belt）：前提是 `status == 0`；此时 `status` 已经是 1（用例被判红）⇒ 也不触发。
- **第三道：`live_port_guard._final_accounting`（atexit）**——`:1038 effective_status = 0 if status is None else status`；
  `:1039 if unaccounted > 0 or (blocked > 0 and effective_status == 0):` → `:1053 os._exit(FINAL_EXIT_CODE)`。
  它没触发，是因为 `conftest.py:203` 把 `reported_status = 1` 回填了过去。
  ⚠️ **若 `reported_status is None`（非 pytest 入口），该层按 0 处理，`blocked>0` 时仍会 `os._exit(3)`。**
  另有 `:511` 的 `os._exit(FINAL_EXIT_CODE)`，用于 `_FINALIZING` 置位之后的迟到连接。

⇒ **正确的口径是「非零，且本卡观测到的形态是 1」**：三条 `exit 3` 路径在本卡的运行里**都没触发**，其行为本卡未验证。
对「能不能进 CI」这个问题结论不变（非零即红），但 Z7-C §3.5 写的「仍然会以 exit 3 收场」在**这一配置下不成立**。

被拦的 11 次全部是 `('::1', 7691, 0, 0)`（现网 Neo4j），发生在进入段内，分布 `[3, 2, 2, 2, 2]`，
owner 全部归到本用例，线程名 `asyncio-portal-*` 且**每轮不同**——印证「每次 `call()` 新建一个客户端、跑一遍 lifespan」。

**门本身不带退避**：`live_port_guard.py:513` 是 `raise RuntimeError(_block_message(address))`，立即抛。
⚠️ 这只证明**门自己**不等待；**调用方**捕获异常后是否重试 / 退避、以及那部分成本有多大，本卡**未测**。
所以不能据此断言「那 30s 与连库无关」。

**实验产物（完成条件 f）**：跑前三条路径**全部不存在**；跑后三条**全部被创建**——

| 路径 | 跑前 | 跑后 | mtime | gitignore 命中 |
|---|---|---|---|---|
| `backend/data/llm_call_logs.db` | ABSENT | 36864 B `53bb3d5f…83c9` | 2026-09-06T10:35:15 | `backend/data/.gitignore:7 *.db` |
| `backend/data/neo4j_memory.json` | ABSENT | 148 B `66bf3abb…f08b` | 2026-09-06T10:35:15 | `backend/data/.gitignore:6 *_memory.json` |
| `backend/app/data/vault_index_pending__canvas_vault.jsonl` | ABSENT（目录都没有） | 0 B `e3b0c442…b855` | 2026-09-06T10:43:40 | `.gitignore:250 backend/app/data/vault_index_pending*.jsonl` |

mtime 分别落在 run-1（10:35:04 起）与 run-2（10:40:54 起）的窗口内，与「本卡跑出来的」一致。
`git status --porcelain` 不含这三条（三条都 gitignored，所以 git 侧恒不可见——这也意味着
**「跑前 ABSENT」的唯一依据是当时那次 `ls`，其原始输出未落盘**，属自述 + mtime 旁证，见验收单 §二 (f) 行）。

⚠️ **这三个文件是 lifespan 的副作用，不是「跑一次合约测试」的必然副作用**：对照组-B（`no_lifespan`）一个都没落。

---

## 四 门侧三问（完成条件 c）

### ① `tests/contract/**` 该不该进豁免面？——**不该**

1. **语义不对。** `live_port_guard.py:159-163` 的注释说明 `EXEMPT_PATH_PREFIXES = ("integration", "e2e")`（`:164`）
   是按路径而非只按 marker 豁免，针对的是 `tests/integration/` 下那些没打 marker 的用例；
   而 `tests/integration/` 下确有「全部跑真实 Neo4j」的文件（例：`test_sync_real_neo4j_gate.py:5` 的模块 docstring）。
   合约测试的语义相反：它验的是**响应体与 OpenAPI schema 相符**，与图数据库里有什么数据无关。
2. **豁免是目录级、且对未来生效的旁路。** `:163` 原注释就写着「⚠️ 这是**有意的旁路**：新写的测试只要放进
   tests/integration/ 就自动免拦」。把 `contract` 加进 `:164`，`tests/contract/` 下现有 6 个文件与今后所有新文件
   一并免拦，远超本次要解决的那一个。
3. **豁免只是把「拦住」换成「不拦」；不拦之后会发生什么，本卡没测。**
   `live_port_guard.py:253-255`：豁免命中 → `advisory += 1` 且 `record()` 返回 `False` ⇒ `:513` 的 `raise` 不执行
   ⇒ **连接尝试得以继续**（⚠️ 这**不等于**连接一定建立成功）。

   ⛔ **启动链上那四条触库调用的条件结构（v2 在这里绑错了，v3 按源码实测更正）**：

   | 调用 | 前置条件 | 连库是否为其前提 |
   |---|---|---|
   | `main.py:173` `ensure_fulltext_index()`（DDL） | `:172 if memory_svc is not None:` | 是（`memory_svc` 由 `:163` 预热产出） |
   | `main.py:343` `get_canvas_schema_gate().verify()` | **无条件**，只被 `:340 try:` 包住 | 否 |
   | `main.py:363` `rel_svc.sync(..., execute=True)`（**写**） | **无条件**，只被 `:351 try:` 包住 | **否** |
   | `main.py:392` `backfill_vault(..., execute=True)`（**写**） | `:387 if _worker_graphiti is not None:`（`:386` 是上一行赋值） | 是（`_worker_graphiti` 由 `:276 initialize_graphiti` 连上库才有值） |

   ⇒ v2 曾写「后两条分别挂在 `if memory_svc is not None:`（`:172`）与 `if _worker_graphiti is not None:`（`:386`）之下」——
   **两处都错**：`:172` 守的是 `:173` 的 DDL，不是 `:363`；`:363` 的写调用**每次 lifespan 无条件进入**。
   方向上这个错误**低估**了暴露面：它让人以为「不连上库就走不到那条写」，而实际相反。

   本卡**没有**去真的放行一次连接来验证（那样会连上用户现网库），所以本条整体是
   **读代码得出的风险判断，不是实测**；上表的条件归属也只做了源码阅读，**未逐条走真实分支**。
   另注：豁免走的是 per-item ContextVar，`conftest.py:124-125` 明写裸线程默认 `<unknown>` 且**永不豁免**，
   所以「加进豁免面」也不等于该用例的**所有**连接都会被放行。

### ② 不豁免时的替代路径，各自代价

| 路径 | 效果（blocked） | 效果（耗时） | 代价 / 证据状态 |
|---|---|---|---|
| **(a) mock Neo4j** | 未测 | 未测 | 连库入口至少 7 处：`main.py:163` `get_memory_service()`、`:173` `ensure_fulltext_index()`、`:216` `recover_outbox()`、`:276` `initialize_graphiti(neo4j_uri=settings.NEO4J_URI, …)`、`:343` `get_canvas_schema_gate().verify()`、`:363` `rel_svc.sync(execute=True)`、`:392` `backfill_vault(execute=True)`；mock 点分散在 `app/clients/neo4j_client.py::get_neo4j_client`、`app/services/memory_service.py::get_memory_service`、`app/services/episode_worker.py::get_episode_worker` 三个单例工厂。⚠️「它解决不了耗时」是**基于采样归因的判断**（进入段的 app 帧主要在 wikilink 图 eager-build），**本卡未做「只屏蔽连接、不动其余」的对照实验** |
| **(b) 复用一个已 startup 的客户端** | 未测；机制上 lifespan 次数从 N 降到 1，**不到 0** ⇒ `conftest.py:141-158` 的哨兵仍会判红 | 未测 | 要改第三方源码 `schemathesis/transport/asgi.py:21` 那个硬编码的 `with`，或在本仓侧注入自定义 transport。**单独用它不足以进 CI**（Z7-C §3.5 这一条判断成立） |
| **(c) `no_lifespan`（仓内已有）** | 该用例 0（A、B 两组各 5/5 轮）；对照组-B 整 session 0、rc=0。⚠️ 但仅 1 个 operation，且该端点在未启动态下会跳过自己那次 Neo4j 调用（§1.3） | 中位 0.008s（A）/ 0.003s（B）——同样只 1 个 operation | `tests/support/lifespan.py:63-83`；需持有到整个 `with TestClient(...)` 之外，而那个 `with` 在第三方 transport 里。本卡探针用的是**函数体内**的 `with no_lifespan(app):` 包住整个循环（`profile_harness.py:352`）；真要挂到 `@schema.parametrize()` 生成的用例上，粒度可能需要更大（module/session 级），**本卡未验证**。**真正的代价在判据 C** |

**(c) 的代价必须说清楚**：`no_lifespan` 不碰 `app.routes` / `app.dependency_overrides` / 端点函数
（`tests/support/lifespan.py:29-31`），所以路由、依赖注入、中间件、响应模型都是真的；
但它**只**替换 `app.router.lifespan_context`，`app.main.app` 仍是进程级单例（`:67-70`）。
本卡只测了 `GET /api/v1/health` 一个 operation，**没有**证明其余 operation 在这个状态下的响应仍与 schema 相符，
也**没有**逐一检查 `app.state.*` 上那些启动期才装配的对象对各 operation 的影响。

### ③ 豁免会不会重开 W4 门想堵的洞？——**会，对命中豁免的那些连接三层一起关**

`conftest.py` 的两条 `status = 3` 各自堵什么：

- **`:199-200`（`state.unaccounted_blocked()`）**：堵「拦截发生了但没有任何用例买单」的窗口——
  迟到线程 / collection 期 / 未知线程（docstring `:179`）。
- **`:201-202`（`state.blocked > 0 and status == 0`）**：兜底 belt，堵「哨兵翻红被 xfail 之类机制吃掉」的残余形态，
  原文「非豁免连接尝试绝不允许以『全绿』收场」（docstring `:180-182`）。

而命中豁免的连接**进不到这两条**：`is_exempt()`（`live_port_guard.py:1061-1083`）返回 True →
`begin_item(nodeid, exempt=True)`（`conftest.py:132-133`）→ `record()` 走 `:253-255` 的 advisory 分支 →
`blocked` 不增、`pending` 不记账 → 哨兵 `:141-158` 无账可结 → 两条 `status = 3` 的前提都不成立，
第三道 `_final_accounting`（`:1039` 看的也是 `blocked`）同样不成立。
**对命中豁免的那些连接，一次关掉的是「拦截 + 结账哨兵 + 三条兜底」全部。**
（不命中豁免的——例如裸线程发起的——仍按原样拦，见 ① 末注。）

`tests/support/lifespan.py:10-17` 早就把这个洞写清楚了（连生产库 + 动生产库 schema + 读用户真实笔记库）。
本卡把它变成了数字：**一次 `case.call()` = 一次完整 lifespan = 2–3 次到 `::1:7691` 的连接尝试**（本卡里全部被拦下）。

---

## 五 接 CI 的可行性判据与成本清单（完成条件 d）

### 5.1 判据（都达标才值得排「接入卡」）

| 判据 | 阈值 | 当前值 | 达标？ |
|---|---|---|---|
| **A · 单次 `case.call()` 墙钟** | 中位 ≤ 0.1s（现测 request 段是 9ms，留一个数量级余量） | 中位 **31.636s**（run-2；十样本区间 23.117–37.045s） | ✗ |
| **B · 门下总账** | 不改 `EXEMPT_PATH_PREFIXES`(`:164`) / `EXEMPT_MARKERS`(`:157`) / 不设 `W4_GUARD_NO_EXEMPT`(`:175`) 的前提下，**整轮** `blocked=0, advisory=0, unaccounted=0` 且 rc=0 | `blocked=11`，rc=1 | ✗ |
| **C · 被测对象等价性** | 若达标手段是 `no_lifespan`，须证明**全部** operation 在该状态下的 failed 集合与启动态一致 | **未测**（本卡只测 1 个 operation） | 未知 |
| **D · 环境可移植** | A/B 的数字须在 CI 镜像（Python 3.11/3.12）上复测 | **未测**（本机 3.14.4） | 未知 |

判据 A 与 B 是**两个互相独立的条件**（治好一个不自动治好另一个），但**同源**：两者都来自「每次 `call()` 跑一遍完整 lifespan」。
§四(c) 的 `no_lifespan` 是目前唯一一条在**一个 operation 上实测**能同时把 A 打到毫秒量级、把 B 打到 blocked=0 的候选路径。
⚠️ 该实测的两条限制：① 只覆盖 `GET /api/v1/health`；② 该端点在未启动态下会跳过它自己那次 Neo4j 调用（§1.3）。
判据 B 的阈值是**整轮**，n=1 的样本不足以宣告达标。代价整个转移到判据 C 上——**这正是下一张卡该做的事，本卡不裁**。

### 5.2 成本清单

| 项 | 内容 |
|---|---|
| 改造工作量（若走 `no_lifespan`） | 测试模块内一个 fixture 持有 `no_lifespan(app)`；本卡探针用函数体内的 `with` 即可（`profile_harness.py:352`），挂到 `@schema.parametrize()` 生成的用例上所需的粒度**本卡未验证**。不改 `conftest.py`、不改 `backend/app/**`、不改第三方库 |
| 举证工作量（判据 C） | 一次「启动态 vs 未启动态」的全 operation 对照跑，逐 operation 比 failed 集合。**启动态那一半在本机跑不成**（门会判红），需要先解决判据 B 或在 CI 镜像上跑 |
| 改造工作量（若走复用客户端） | 需在本仓侧包一层 transport 以避开 `schemathesis/transport/asgi.py:21` 的硬编码 `with`；且**仍不满足判据 B** |
| CI 时间 | **未测，本页不给任何估算**，理由见 §六 |
| 副作用 | **跑一次带完整 lifespan 的合约测试**会落三个文件（§三表）；启动链含对现网库的 DDL 与写调用（`main.py:173/:343/:363/:392`，条件结构见 §四①.3），必须靠 W4 门或 `no_lifespan` 挡住。走 `no_lifespan` 则本卡实测**一个都不落** |
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

**关于 operation 总数**：本卡实测的是 `paths=193`（`from_asgi` 后读 `raw_schema["paths"]`），
**没有**测 operation 总数。Z7-C 记为 206 个，本卡未复测，本批 Y5-C（`67ee147c`）之后是否仍是 206 也未复测。
本页凡写「其余 operation」处，指的是「除 `GET /api/v1/health` 之外的全部」，不带具体数字。

### 6.2 本卡未证明什么

1. **不证明进入段 / 退出段等于「纯 app lifespan」。** 它们是 `TestClient.__enter__/__exit__` 的整体，含构造与 portal 建/收。
2. **不证明「lifespan 函数体内」与「portal 收尾等待 lifespan 派生的后台任务」两者的比例。**
   §1.3 的对照组减法**做不到这个分离**——对照组的 lifespan 是 no-op，不产生那些后台任务，减法在物理上看不见它们。
   减法还有一条**未验证的前提**：portal 建/收的成本与 lifespan 是否跑无关（`3_request` 段在三种配置下 0.002/0.005/0.009s 的差异对它不利）。
3. **不证明启动过程内部每一步各花多少秒。** 约 20 个启动步骤没有各自计时；「主项是 wikilink 图 eager-build」
   是**采样证据**，受错桶、线程混合、条件分母三条限制，**不能换算成墙钟份额**，误差上界未给出。
4. **不证明退出段那个后台任务的身份与等待关系。** 「每轮观察到两条模型装载日志」「退出段采到 TLS 读/握手与
   transformers 帧」是观测；「是 `_eager_init_lancedb_singleton` 在阻塞退出」是推断，未闭合。TLS 对端未确认。
5. **不证明「六段之和 ≈ 墙钟」能独立排除漏计与重复计。** 串行性由读源码得出；残差只是补充旁证，
   且只覆盖当前这条固定成功路径。
6. **不证明残差里剩下的是哪几行。** 探针只包了模块级的 `after_call` dispatch；`case.py:413-414` 的
   `schema.hooks.dispatch` 与其余探针外工作未逐项计时。
7. **不证明三轮由同一字节版本的探针产出。** run-1 是更早一版；对照组-B 的同源性由「从存档复制」保证而非存档证据（§1.0）。
8. **不反推 Z7-C 那个 7.1s 的组成，也不主张它测错了。** 本卡没测 `import app.main`，
   `from_asgi` 那个数还含 operation 查找，两次测量的边界与环境均不可比。
9. **不证明「只屏蔽连接后耗时会怎样」。** 门自身立即抛出，但调用方的重试 / 退避成本未测，
   也没有做「只屏蔽连接、不动其余」的对照实验。
10. **不证明豁免后连接会成功建立、DDL / 写调用会真的执行。** §四①.3 是读代码得出的风险判断，
    本卡没有放行过任何一次连接；上表的**条件归属也只做了源码阅读，未逐条走真实分支**。
11. **不证明 `no_lifespan` 能把判据 B 打到「整轮 blocked=0」。** 实测只覆盖 1 个 operation，
    且该端点在未启动态下会跳过它自己那次 Neo4j 调用（`health.py:148-154`）；
    仓内是否存在没有这层条件保护的端点，本卡未逐个核查。
12. **不证明其余 operation 在未启动态下的响应仍与 schema 相符**（判据 C 未测）。
13. **不证明把 `no_lifespan` 挂到 `@schema.parametrize()` 用例上所需的作用域粒度。** 本卡用的是函数体内的 `with`。
14. **不证明 CI 机器上的数字。** 本机 Python 3.14.4，CI 是 3.11/3.12，未控制。
15. **不证明 rc 在别的配置下也是 1。** 三条 `exit 3` 路径在本卡运行里都没触发，其行为未被本卡验证。
16. **不证明 `3_request` 段三个中位数（0.009 / 0.005 / 0.002s）差异的成因。**
17. **不证明「跑前三条产物 ABSENT」有存档级证据。** 那次 `ls` 的原始输出未落盘，属自述 + mtime 旁证。
18. **不证明本探针与生产用例逐字等价。** 三处已声明差异（不走 hypothesis ⇒ `case._meta is None`、
    用 `call()` 而非 `call_and_validate()`、schema 在函数体内建）写在 `profile_harness.py` 模块 docstring 里。
    正面佐证：实测单次调用落在 Z7-C 观察到的 20–50s 区间内（23.117–37.045s）。
19. **不裁 Dredd 该复活还是该退役**（Z7-C 已裁乙），**不改 CI**——`contract-test` job 维持
    `.github/workflows/api-spec-sync.yml:330` 的 `if: false`；**不改** `conftest.py` / 豁免面 /
    `backend/app/**` / `dredd-hooks.js` / `live_port_guard.py`。
20. **本版（v3）的措辞未经外审。** 见页首「版本沿革」。
