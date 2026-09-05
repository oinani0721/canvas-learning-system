# 对抗性代码审查 — CARD-W4-3a round-1（NEO4J_TEST_URI 端口判据改正面白名单）

你是独立审查者。工作树只读：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4`

**审查面 = 本卡的未提交改动**（`HEAD` = `004e08cc` 是上一张卡 CARD-W4-3b，不在本轮范围）：

```
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4
git diff -- backend/
```

只有三个文件：
- `backend/tests/support/live_port_guard.py`（判据本体）
- `backend/tests/unit/test_live_port_guard_contract.py`（契约测试）
- `backend/scripts/lifespan_isolation_guard_probes.py`（新增 1 条探针）

## 一、背景：被修的是什么

`live_port_guard.py` 是一道测试期的 socket 门：pytest 进程里任何指向现网 Neo4j 端口
（7691 / 7687）的 `socket.connect` 都被 CPython audit hook 拦下并记账。
`NEO4J_TEST_URI`（测试容器，应为 7692）另有一道**配置预检** `assert_test_uri_not_blocked()`，
在 session fixture 里跑。

上一张卡（X4）的两轮独立终审给出**同一条 BLOCKER**，且修复前它仍在树上：

- 预检判据是**黑名单**：解析出端口 → 端口非 None → 端口不在 `BLOCKED_PORTS` 就放行；
- `bolt://127.0.0.1:0` 的端口 `0` 既非 None、又不在黑名单里 ⇒ **放行**；
- 而 neo4j 驱动把 `:0` 归一成 **7687**（`_addressing.py` 的 `port = port or default_port`，
  `int("0")` 是 falsy；`_sync/driver.py::_Direct._default_port = 7687`）；
- 再经 `is_exempt()` 对 `tests/integration` / `tests/e2e` 的 advisory 路径（只记不拦），
  误配 `:0` 的那些用例会**真连开发库**。

## 二、本卡怎么改的（作者自述，**请独立核对，不要采信**）

1. 新增 `ALLOWED_TEST_PORTS = frozenset({7692})`，预检判据由「端口不在黑名单」改成
   「**驱动 canonical 端口 ∈ 白名单**」，显式三分：没配 URI = 射程外；解析不出 int 端口
   = 拒；端口在白名单 = 放行；其余一律拒。
2. canonical 端口不再自己推断，改为按**驱动自己的解析链**复算：
   `urlparse(uri)` → 检查 userinfo（驱动的 `parse_neo4j_uri` 对它直接 ConfigurationError）
   → `Address.parse(parsed.netloc, default_host='localhost', default_port=7687)`。
   `neo4j.Address` 与 `urlparse` 都是**函数体内延迟 import**（该模块刻意不在模块层
   import 任何重物，因为装门必须早于业务 import；而预检只在 session fixture 才被调）。
3. `BLOCKED_PORTS` / `REQUIRED_BLOCKED_PORTS` 取值与 `_audit_hook` 的黑名单语义
   **完全不变**（理由写在注释里：hook 上做白名单会把 Ollama 11434 等一并拦死；
   黑名单常量还是 `audit_hook_alive` / `assert_guard_live` 的自证锚点）。
4. 加了一道**无条件**自检：`ALLOWED_TEST_PORTS & BLOCKED_PORTS` 非空即抛
   （防「把 7687 加进白名单」这种拆门方式），配一条新探针钉住。
5. 顺带修另一条 HIGH：`extract_port` / `port_is_trustworthy` 对 tuple **子类**一律
   按不可信处理（子类可重载 `__len__` / `__getitem__`，而 CPython socket 读底层槽位）。

契约测试从 35 个用例增到 66 个（含 13 条「合法容器写法不得被误拒」的正例）。

## 三、请你回答的问题（按重要性排序）

1. **BLOCKER 真的堵住了吗？** 有没有**任何** `NEO4J_TEST_URI` 取值，能通过新预检、
   而驱动实际会连到 7691 或 7687？请从 `neo4j/_api.py::parse_neo4j_uri` 与
   `neo4j/_addressing.py::Address.parse` 的实际代码出发核对，不要只看作者的注释。
   特别注意：作者的复算与驱动真实链路之间**有没有分叉**（他刻意用 `parsed.netloc`
   而不是自己切字符串，理由写在 `canonical_target_port` 的 docstring 里 —— 这个理由成立吗？）。
2. **反方向：有没有把合法配置误拒？** 白名单语义是默认拒绝，代价是误拒。
   `bolt+s://`、`neo4j+ssc://`、带 query（`?routing=...`）、IPv6、大小写 scheme、
   末尾斜杠这些形态，新判据与驱动的口径一致吗？
3. **延迟 import 的时序安全**：`neo4j` 在预检时被 import 进测试进程。这会不会
   影响装门时机（门必须早于业务 import）？`tests/conftest.py` 的装门在第 28 行附近，
   预检调用在第 106 行 —— 这个先后关系够吗？import neo4j 本身会不会发起连接？
4. **新自检（白名单 ∩ 黑名单）放在函数最前、且不受"有没有配 URI"影响** —— 位置对吗？
   有没有哪条调用路径不经过它？
5. **tuple 子类的处置**：`extract_port` 改成 `type(address) is tuple`、
   `port_is_trustworthy` 对子类返回 False。这两处**必须一起看**才成立
   （单改一处等于放行）。核对 `_audit_hook` 的判据
   `if port in BLOCKED_PORTS or not port_is_trustworthy(address)` 在子类地址上确实会拦。
   另外：这个改动有没有误伤 `_is_selftest_address`、`audit_hook_alive` 的自证路径，
   或者任何真实使用的地址形态（`socket.connect` 传的到底是不是精确 tuple）？
6. **新探针够不够？** `guard-allowed-test-ports-cannot-admit-live` 的三段判据
   （A 污染白名单必拒且拒因是相交自检 / B 白名单干净时 `:0` 必拒且文案含 7687 /
   C 7692 必放行）—— 有没有哪一段可能被别的原因满足？
7. **声明与实现是否一致**：新写的注释/docstring 有没有比代码实际做到的更宽的说法？

## 四、边界

- 只读，不修改任何文件，不运行会写盘的命令。
- 不连接 7691 / 7687 / 7692 任何数据库端口。
- `is_exempt()` 的豁免**覆盖面**本身（`EXEMPT_MARKERS` / `EXEMPT_PATH_PREFIXES`）
  不在本卡范围（放宽/收紧另裁）；但「advisory 路径 + 本卡新判据」的组合是否仍有洞，
  在范围内。
- `live_port_guard.py:392` 的 `os._exit(3)` 前 IO 可抛、以及 `_FINALIZING`/`record()`/
  ledger 未同锁 —— **已另立卡（W4-④）**，不在本轮，除非本卡改动让它更糟。
- `scripts/lifespan_isolation_negative_control.py` 与 `lifespan_isolation_runtime_sha.sh`
  是上一张卡的面，本轮不看。

## 五、输出格式

按级别（BLOCKER / HIGH / MEDIUM / LOW）列出发现，每条给：位置（`文件:行`）、
一句话结论、**你据以判断的依据**（读到的具体代码）、建议修法。
无法在只读环境下判定的，明说「未验证」并写清需要什么才能判定。
最后给一句整体裁定：本卡的阻断级问题数量。
