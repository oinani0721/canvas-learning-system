# 冻结审查请求 — CARD-TEST-isolate-lifespan-R1

你是独立审查方。请对下面这一组**测试基础设施**改动做对抗性审查，并给出正式裁定。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2`
（只读；不要修改任何文件）。

审查对象绑定：分支 `card/w4-safety-r2`，**实现最终态 = commit `de57e375`**。

> 📌 round-2 于 2026-09-04 发了三次都没拿到正文（网络 / 被误杀 / 内容过滤），但从
> 第 3 次的 stderr 抢救到了阶段性结论与可复现命令。**那一轮抢救出的阻断项已在本轮
> 逐条处置完毕**，处置结果见 `_bmad-output/审查/CARD-TEST-isolate-lifespan-R1-验收单.md`
> §7.6b–§7.6f。请把它们当作**已知已处置项**，重点复核处置是否真的关闭了问题、以及
> 处置本身有没有引入新缺陷（本轮就有过一次「改进反而降低强度」并回退的记录）。
本文件与验收单之后还有一个 docs-only 尾巴 commit（只动 `_bmad-output/`），它**不改变
代码树**；判据可自行复核：`git diff --stat de57e375 HEAD -- . ':(exclude)_bmad-output'`
输出为空。

审查面分三段（分开给，是因为本分支上还并行着另一张卡 Bark-R1，`git diff 1f249b33..HEAD`
会把它的 900 余行探针一并卷进来 —— **那部分不属本卡**）：

```
# ① 本卡 round-1/round-2 实现面（与历轮同基线 4a25578e）
git diff 4a25578e..0684e0fa
# ② 并入主干（见下方「本轮的三件新事」第 1 条）
git show d5f96344 --stat
# ③ 连库测试转 mock + 运行时锚点修复
git diff d5f96344..2b160897
# ④ round-2 抢救出的阻断项处置（compgen 自检 / shell 门声称更正 / 同名工厂失格名单）
git diff 2b160897..de57e375 -- backend/
```

⚠️ 上一轮（配额耗尽、未取得裁定的那次）绑的是一个**更早**的 commit —— 位于
`8380adac` 之前，因而**漏掉了** `8380adac`（AST 门重写 +434/-95）与 `0684e0fa`
（新增 2 条探针 +134）。本轮绑定已推进到实现最终态，这两个 commit 现在在审查面
**之内**，请一并审。

（本文件与验收单刻意不再出现那个旧短 SHA：本卡的裁判 1 是一条机械 grep，要求这两个
文件全文不含旧绑定串，防的就是"改了一处、别处还留着"的陈旧绑定。历史链在 `git log`
里，没有丢。）

## ⛔ 本轮的三件新事（上一轮绑定点之后发生的，请重点看）

1. **并入主干 `1f249b33`**（commit `d5f96344`）。唯一冲突面
   `backend/tests/unit/test_vault_scope_409.py` 双侧改动自动合并：车道侧的
   `no_lifespan(app)` 保留，主干侧新增的 module-scope `_no_real_index_orchestrator`
   fixture 一并保留（在 `no_lifespan` 下已冗余，但无害，未动）；自动合并产生的重复
   `import pytest` 已去重。**主干 `1f249b33` 自身的内容不在本卡审查范围**，但它改变
   了本卡门的前提 —— 见第 3 条。
2. **连库测试转 mock**（commit `f6c86ef4`）。装门后干跑抓到一条**主干既有**的连库
   测试：`test_story_38_3_fsrs_init_guarantee.py::TestCodeReviewC2ReviewServiceSingleton`
   经 `review_service.py:2330 _get_mem()` → `memory_service.py:2914 initialize()` →
   `:278 self.neo4j.initialize()` → `neo4j_client.py:402 health_check()` →
   `:523 verify_connectivity()` → 7691。连接异常被 `health_check` 吞成
   "Falling back to JSON storage mode"，用例照样绿 —— 它一直在偷连开发库。
   打桩打在**类级 autouse**：两条用例**各自单跑都红**（分别实测），一起跑时只有第一条
   触发 `initialize()`（MemoryService 单例是进程级闩）。只改该测试文件。
3. **运行时文件锚点跟随 G2-5 journal 改名**（commit `2b160897`）。主干的 CARD-G2-5 把
   orchestrator 的 durable journal 从 `app/data/vault_index_pending.jsonl` 改成了
   vault 命名空间下的 `vault_index_pending__<vault_key>.jsonl`
   （`app/core/vault_state_paths.py::namespaced_state_path`），而两道门的监视清单还锚在
   旧的固定文件名上。同一个锚点失效、两道门朝**相反**方向坏掉：负控那侧「变异态必须
   写至少一个运行时文件」的正证据消失 → `NEGATIVE-CONTROL: FAIL`（fail-closed）；
   `runtime_sha.sh` 那侧断言的是 `unchanged`，`absent == absent` 恒成立 → **假绿**。
   修法是按 stem 前缀 glob（新旧文件名一并收）+ **每次快照重新展开**（缓存一次就等于
   看不见跑完后才创建的文件）。修后负控 `[5b]` 实际写出的文件是
   `app/data/vault_index_pending__canvas_vault.jsonl` —— 根因当场坐实。
   **这一条是本轮最值得核的地方**：glob 判据是否引入了新的误判面？见 §4 第 7 条。

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
(2) 核**整改本身引入的新缺陷**（更严的判据是否产生误拒？隔离副本是否引入了新的不一致面？
    `os._exit(3)` 是否会掩盖别的信息？`case` 判据的覆盖面与 docstring 说法是否一致？）。

当前门规模（2026-09-04 于实现最终态逐条实测，不是抄上一轮的数）：探针 **29**、
AST 负控 **22 绕过 / 11 验伪锚**、guard 契约单测 **35**。

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
- `backend/tests/support/lifespan.py`（`no_lifespan`）
- `backend/tests/unit/test_vault_scope_409.py`（本卡改造 + 本轮的 merge 结果）
- `backend/tests/unit/test_story_38_3_fsrs_init_guarantee.py` 里**只有**本轮新增的
  `stub_memory_service` fixture（同文件其余内容是主干既有，不在范围内）

**明确不在范围内**（已由卡文裁决，重复提出不计为发现）：

- `backend/app/main.py` 与任何生产 service —— 本轮**生产 lifespan 零改**是既定裁决。
- `backend/tests/integration/`、`backend/tests/e2e/` 的内容 —— 卡文裁决为"只登记、
  本轮不改"。它们按路径豁免（只记录不拦截），这是**有意的设计**，不是遗漏。
- CI workflow、OpenAPI、`.gitignore` —— 本轮禁改面。
- **主干 `1f249b33` 自身携带的一切改动**（CARD-G2-4 / G2-5 / G3-6b / G6-2 / G8-2 /
  DEBT-8 等）—— 它们各有自己的卡与审查轮次，本卡只负责「并入后本卡的门还成不成立」。
- **同分支上 Bark-R1 卡的文件**：`backend/tests/regression/bark_*.py`、
  `backend/tests/regression/conftest.py`、`scripts/send_bark.py`、
  `backend/scripts/bark_r1_*.py`。同一条分支但不同卡，已另行审查（round-4 的
  6 MEDIUM + 1 LOW 已登记在验收单「登记级残留」表，不修）。
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

**本轮（上一轮绑定点之后）新增的四条声称，同样请逐条证伪：**

(m) merge 后 `test_vault_scope_409.py` 不再起 `app.main` 的 lifespan：文件内已无
    `with TestClient(app.main.app)` 形态，只有 `no_lifespan(app)` 包住的 client
    fixture；装门下 collect-only 38 条（= 合并前车道侧 38 条），收集期
    `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。

(n) 连库测试转 mock 之后，`test_story_38_3_fsrs_init_guarantee.py` 全文件 21 passed，
    且**三种跑法**（全文件 / 单跑第一条 / 单跑第二条）门账均为 0。打桩点选的是
    **源命名空间** `app.services.memory_service.get_memory_service` —— 依据是工厂内
    那句 import 在**函数体内**，每次调用重新取名字（若它是模块顶层 import，就必须
    改 patch 已绑定的引用，这是同类打桩最容易错的地方）。同链的
    `review_service.py:2351 get_graphiti_temporal_client()` 已核：它经
    `dependencies.py:748` 只**构造** Neo4jClient、不 `initialize()`，不发起连接 ——
    打桩后计数仍为 0 即是证据，故未同法 mock。

(o) 运行时文件锚点修复后三道裁判全绿（负控 PASS / 探针 29/29 / RUNTIME-FILES:
    unchanged），且 `runtime_sha.sh` 的清单自检从单一 count 拆成
    fixed(2) / glob(1) 两条 —— glob 条数为 0 同样是「零比较恒绿」，只是更隐蔽。
    覆盖面刻意与合并前**等价**：只跟随这一个 journal 的改名，不新增监视项；同族的
    `lancedb_pending_index__<key>.jsonl`（`lancedb_index_service.py:76`）合并前就不在
    清单里，本卡只登记移交（扩面会让 `runtime_sha` 变严，属另一张卡的范围决策）。

(p) 装门下跑 **20 个显式文件**（本卡改造过的 tests/unit 文件 + 主干带入的同族文件 +
    W4 卡文点名的那批）共 551 条用例：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` 且
    `RUNTIME-FILES: unchanged` —— **门没有再抓到别的连库用例**。其中 9 条红全在
    `test_sync_batch_auth` / `test_system_endpoint_auth` /
    `test_sync_exception_classification`，根因是 `Settings` 校验
    （`INTERNAL_API_KEY required outside local dev`）抛 ValidationError 被中间件转成
    500 而用例期望 503 —— 与门无关（`blocked=0`），且 merge **未改动**这条链上的任何
    生产文件或测试文件（`git diff --stat 9d1ef1a9..HEAD -- app/config.py app/main.py
    app/core/exception_handlers.py app/security.py app/api/v1/endpoints/sync.py
    app/api/v1/endpoints/system.py` 及那三个测试文件，输出均为空），故判为既有失败面。

## 3. 可复现的证据命令（只读，可自行重跑）

```
cd backend
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_negative_control.py --ast-negative-control
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_negative_control.py --ast-only
PYTHONDONTWRITEBYTECODE=1 <python> scripts/lifespan_isolation_guard_probes.py
bash scripts/lifespan_isolation_runtime_sha.sh -- <python> -m pytest tests/api tests/unit/test_vault_scope_409.py -q -p no:cacheprovider
# 本轮新增（(n)/(p) 的证据）
PYTHONDONTWRITEBYTECODE=1 <python> -m pytest tests/unit/test_story_38_3_fsrs_init_guarantee.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 <python> -m pytest tests/unit/test_story_38_3_fsrs_init_guarantee.py -k test_singleton_creates_review_service -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 <python> -m pytest tests/unit/test_story_38_3_fsrs_init_guarantee.py -k test_singleton_returns_same_instance -q -p no:cacheprovider
```

⚠️ `PYTHONDONTWRITEBYTECODE=1` 不是装饰：`tests/unit/test_vault_lint.py::test_bytecode_guard_is_armed`
会断言它在环境里（`sys.dont_write_bytecode` 兜底之外的第二道）。本轮跑 (p) 那批时漏
设过一次，当场被这条门抓红 —— 如实记在这里，因为它正好证明那道门是活的。

⚠️ 完整负控（不带 `--ast-only`）会在 tmp 里建一份 git-tracked-only 的 backend 副本并在
**副本**上做变异（真实树不写）。你处于只读沙箱，仍请**不要**运行它；本仓库已附带完整输出。

## 4. 规范符合性对照（本轮请按这个框架逐条核）

这是一次**代码正确性与文档口径**的审阅。请对下面每一条做「声称 ↔ 实现」的逐条对照，
指出两类不一致：**(甲) 实现比声称松** —— 声称覆盖到的情形，实现实际漏检（漏网）；
**(乙) 实现比声称严** —— 声称之外的普通写法被判红（误拒）。甲计 HIGH 起步，乙计 MEDIUM。
请以**阅读代码 + 已附输出**为依据，不需要你运行任何东西，也不需要构造任何示例输入。

1. **(c) 的承重范围**：docstring 说承重层是 `sys.addaudithook("socket.connect")`。
   Python 标准库里发起 TCP 连接的调用路径，是否都会经过这个审计事件？把「会经过」
   与「不会经过」各列一个清单，与 docstring 已声明的边界比对。
2. **(d) 的身份验证语义**：每次 `install()` 与每个用例边界做的那次自证，它**能证明
   什么、不能证明什么**？docstring 的措辞与这个范围是否一致？
3. **(e) 的残余窗口**：最终总账之后的残余窗口，代码实际留下多大、docstring 声明多大，
   两者是否一致（这一条是文档口径题，不是攻防题）。
4. **(g) 的静态分析口径**：AST 门的判定规则与它 docstring 里列的「覆盖形态 / 已知盲区」
   两张清单，是否逐条对得上？有没有清单里写了但代码没实现的（甲）、代码判红但清单
   没说会判红的普通写法（乙）？
5. **(h) 的自证覆盖面**：摘要自证与控制流自证各自覆盖哪一类改动、各自覆盖不了哪一类，
   与 docstring 的说法是否一致。
6. **文档与实现的口径差（本轮最重要的一类）**：任何 docstring / 验收单里"说得比做到的
   宽"的句子。本卡历史上已经因此栽过两次（round-1 第 5 条、以及本轮 §7.6f 记的 B），
   所以这一类**优先于**新缺陷。
7. **glob 判据的边界（本轮新增，请重点核）**：把固定路径换成 stem 前缀 glob 之后：
   glob 展开为空时快照里**没有那一行**，而固定路径不存在时会打一行 `absent` —— 这个
   不对称在什么情形下会让本该判 CHANGED 的变成 unchanged？`compgen -G` 的展开顺序
   是否稳定到可以不加 `sort`？`vault_index_pending*.jsonl` 这个模式会不会把不该监视的
   同前缀文件（将来的 `.tmp` / `.bak` 派生物）一并收进来，从而制造无谓的 CHANGED？
8. **(n) 的打桩点绑定时机**：`monkeypatch.setattr` 打在源命名空间上，对**函数体内**的
   `from ... import ... as ...` 是否每次调用都生效？类级 autouse fixture 与同类已有的
   `reset_singleton` autouse fixture 的执行顺序，会不会留出「先建单例、后打桩」的窗口？
9. **本轮处置的复核（见验收单 §7.6f）**：C（compgen 自检）、E（同名工厂失格名单）两处
   修复是否真的关闭了对应问题、有没有引入新的误拒；B（改声称而非改代码）这个判断是否
   成立；D 被归入「容器/解包元素级别名分析」盲区族是否恰当；F 被判为「复现依赖人为篡改
   内部状态、需要不篡改的复现才能定性」是否恰当。

## 5. 输出格式

先给一行总体裁定：`PASS` 或 `FAIL（n BLOCKER / n HIGH / n MEDIUM / n LOW）`。
然后逐条列 findings，每条给 `[级别] file:line` + 一句缺陷陈述 + 一个**具体的**
失败场景（什么输入/状态 → 什么错误结果）+ 建议。
再给「放行维度」：你实际核过、认为成立的面，以及你**没有**核的面。

如果某一条你检查后认为确实成立，请明确写出来 —— 这份裁定既要抓问题，也要如实
记录哪些面已经站得住。

**最后一行必须是下面两行之一，不要加别的字**：

```
BLOCKER/HIGH 清零：是
```
或
```
BLOCKER/HIGH 清零：否
```
