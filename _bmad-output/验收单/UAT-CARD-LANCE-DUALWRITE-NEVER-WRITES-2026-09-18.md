# UAT — CARD-LANCE-DUALWRITE-NEVER-WRITES

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage`（分支 `card/p1-storage`）· 本车道第 **1/4** 张（首卡）
> 基线 `B15_BASE = 9c4e7e82`
> **最终代码 SHA = `efaece7fc899d408d58a80485b5e8e467d5ccccc`**（= r5 的审查绑定 SHA）
> commit 数 **3**：代码 `10bc2803` + openapi 还原 `efaece7f` + 本文档 commit（**只含 `_bmad-output/`**）
> ⚠️ 第 3 个 commit 按协议 §1「只改 `_bmad-output` 不算」——**不破坏终审绑定**：
> `git --no-pager diff --stat --no-color efaece7f HEAD -- . ':(exclude)_bmad-output'` 实测 **为空**。
> **Codex 轮次 = 5**（末轮 `r5` 绑最终代码 SHA，**BLOCKER 0 / HIGH 0** ⇒ D-15 达成）
> 卡文 `…/goal-cards/第十五批-goals/P1-A.md` · 证据目录 `_bmad-output/审查/evidence-lance-dualwrite/`

---

## 〇 本卡到底改了什么（一句话）

给白板连线写下的「理由」，以前只有一半真的存了下来——图谱那半存了，向量库那半**一次都没存过**，
而系统每次都回报「双写成功」。同时，后台数据库密码配错时，系统会假装成「部分成功」继续往前跑。
本卡让向量库那半真的落盘、让配错的部署**响亮地报错**，并在这次写入会毁掉已有历史时**宁可不写**。

---

## 一 第 0 分钟（AC-a）

| 判据 | 实测 |
|---|---|
| `pwd` / `git branch --show-current` | `…/worktrees/card-p1-storage` / `card/p1-storage` ✅ |
| `git rev-parse --short=8 HEAD` | `9c4e7e82` ✅（= B15_BASE，首卡前提成立） |
| `git status --porcelain \| wc -l` | `0` ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均存在 ✅ |
| pyright 自证 `( test -x "$P" \|\| exit 1 )` | rc=0 ✅ |
| `grep -vc '^#' <unit-red-baseline-9c4e7e82.txt>` | **33** ✅ |
| 手册地盘核 | 手册 §一:8 / §二:29 / §三:46 / :447 / :463-474 均命中；⛔ 未改手册 |

**开工基线**：`unit-open-20260918T164904.txt` → `32 failed, 5731 passed, 44 skipped, 13 xfailed (716.94s)`，rc=0，
末行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。
`diff base.nodeids open.nodeids` → 只有 1 条 `<`（flaky `test_accept_candidate_already_accepted_returns_422`，红基线头第 5 行已注明「已在集内」）。

### §〇 卡文事实复核 — 漂移登记（5 条）

1. `asyncio.gather(` 卡文写「:427 段」，**实测 :424**。
2. `return _client_instance` 卡文写 `:2809`，**实测 :2808**。
3. 卡文 (c)(1) 说工厂「与 `index.py:116 vault_id=vault_id` 同口径」，**实测 `index.py:116` 是
   `logger.info("vault.index_deleted", vault_id=vault_id, …)` 的日志 kwarg，不是客户端构造**；
   `backend/app` 内 6 处 `LanceDBClient(` 构造**没有一处**传 `vault_id`。本卡按构造器签名实现。
4. 卡文 (e)③-1 要求的 `# pyright: ignore[reportPrivateImportUsage]` **实测不需要**（见 §三 e）。
5. 卡文 (k) 说负控段① 应「红在 `count_rows()`」，**实测红在表存在性断言** —— 改回 `to_thread` 后表
   根本不会被创建，`count_rows` 那行不可达。判据链上更早一环红，语义等价。

---

## 二 先红（AC-b）

### b① 结构基线 — `struct-before-20260918T165339.txt`

`asyncio.to_thread` **3** / `hasattr(client` **4** / 段内 `_fallback_to_json()` **3** / `health_check()` **1** /
`raise` **0**；验伪锚 `asyncio.gather(` **1**；AST `to_thread`/`gather` Call **3/1** —— 与卡文 (b)① 逐条相符。

### b② 行为先红 A — `lancedb-red-20260918T165634.txt`（rc=1）

`collected 17 / 12 deselected / **5 selected**` → **5 failed**。核心失败正文即**谎报证据**：

```
AssertionError: 表 'p1adualwrite_edge_rationales' 不存在 ⇒ LanceDB 侧没有真写。库内表: []。
⚠️ 同一次调用返回的 WriteStatus.success = True (error=None) —— success=True + 表不存在 = 端点在谎报写成功
```

同档另两条独立自证：生产日志 `LanceDB write succeeded for edge …`（**自称**成功）；
`RuntimeWarning: coroutine 'LanceDBClient.add_documents' was never awaited`（协程从未被 await = 机制直证）。
端点级两格改前红在 `AttributeError: … has no attribute '_lancedb_client_for'` —— **是 setup 阶段的
AttributeError 不是断言失败**，如实登记。

### b③ 行为先红 B — `init-red-20260918T170026.txt`（rc=1）

`collected 25 / 20 deselected / **5 selected**` → **4 failed, 1 passed**：
`[AuthError]` `[ConfigurationError]` 两格 `DID NOT RAISE`；端到端 `assert 207 == 500`；真库 7692 错密码
`DID NOT RAISE AuthError`；**对照格**（对端不可达）✅ 绿（改前本就该绿）。

### b④ 真库先红

**7692 测试容器本次可达**（真库两门均为 FAILED 而非 skipped）⇒ 卡文预留的 skip 分支**未触发**，真库门真跑。

---

## 三 实现（AC-c / AC-d / AC-e）

### c — H2：`_write_lancedb` 单一真写路径 + 三层写入保护

`_lancedb_client_for(vault_id)` → `connect_lightweight()` → `await client.embed()` → **向量规范化** →
**前置拒写** → `await client.add_documents()` → `written != 1` 判败 → **写前/写后行数网**。
删掉 delete / upsert / get_db **三条死分支**与 4 处 `hasattr` 探测（`LanceDBClient` 的 `def delete` 计数 = 0）。
AC-5 delete-before-insert 去重**不做**，append-only，已登记。

> **本卡逐层挖出来的缺陷链**（每修好一层，下一层才第一次可达）：
>
> | # | 缺陷 | 发现者 | 处置 |
> |---|---|---|---|
> | ① | `to_thread` 调 `async def` ⇒ 零写入却恒报成功 | 卡文 | 改为直接 `await` |
> | ② | 表缺 `doc_type` 列 ⇒ **第二次**写入 drop 重建整表（append-only 失效） | **本卡真写门**（`gates-close-20260918T170350.txt` 红在「期望 2 行实得 1」、表 `version=1`） | 写侧带 `doc_type` 键 |
> | ③ | **既有旧表**缺 `doc_type`/维度不符 ⇒ 首次真写即 drop 全部历史，仍返 1 | Codex r1 HIGH | **前置拒写**（主防线，旧行一条不动）+ **行数网**（第二层，只发现不预防） |
> | ④ | `table_names()` 默认 `limit=10` ⇒ 目标表排第 11 张后，**已写成功**被读成失败 | Codex r2 MEDIUM | 改走 `_all_table_names()`；临时库实测 12 张表时 `table_names()` 恰返回 10 张、目标表缺席 |
> | ⑤ | `embed` **成功返回**坏向量（8 维 / 1024 字符串）⇒ 建出坏表，此后正常向量被永久挡住 | Codex r3+r4 MEDIUM | **规范化** `[float(x) for x in vector]` —— 能归一的列类型恒为 float，归不了的拒写 |
>
> ⑤ 的收敛法值得单记：继续枚举坏形状是**加一格**（我实测 `sum()` 挡得住字符串与嵌套，却**漏 `bytes`**）；
> 改成规范化是**换一维** —— 不问「是不是坏形状」，而问「能不能归一成 float 序列」。

### d — H1：初始化对部署缺陷 fail-closed

`_initialize_neo4j_driver` 不再调 `health_check`（它的 `except Exception` 全捕获会把 `AuthError` 压成
`health_ok=False`，与「对端连不上」不可分辨），改为自己 `verify_connectivity()` 并分类：

| 异常族 | 处置 | 门 |
|---|---|---|
| `AuthError` / `ConfigurationError`（部署缺陷） | 关驱动 + 置空 + `_initialized=False` + **re-raise** | G2①② + 真库 G2⑤ |
| `ServiceUnavailable` / `SessionExpired` / `ConnectionAcquisitionTimeoutError` | **维持** fallback 返 True | G2③ **三格对照（承重）** |
| 其余 `Exception` | 维持 fallback，日志升 `error` 带 `type(e).__name__` | —（无独立门，见 §七 #7） |

> **勘探 → 实测更正（决定修法）**：裁定书写的吞点是 `except AuthError` 那一支。实测**该支对真实凭据
> 错误不可达** —— 真实 `AuthError` 由 `verify_connectivity()` 抛，先被 `health_check` 的全捕获吃掉。
> ⇒ 真正的吞点是 **health_check 的全捕获 + 其后的 fallback 调用**。

> **⚠️ 本卡引入并已修的 W4 回归（自查发现，Codex 未提）**：初始化不再经 `health_check` ⇒
> `test_mock_degradation_transparency.py` 与 `test_review_mode_support.py` 的
> `stub_neo4j_singleton_health_check` **打桩缝失效** ⇒ 测试进程真的对现网 7691 发起连接。
> **实测账本**：开工 `ATTEMPTS=0` → 收工 **`=2 (blocked=2)`**（`final-unit-20260918T173605.txt`）。
> ⚠️ 这两条红**同时**带 W4 哨兵，长得和「已知哨兵红在 nodeid 间翻转」一模一样 ——
> **区分它们的是账本数字**：翻转只换 nodeid，不换总数。
> **处置**：两个 fixture 叠加驱动工厂打桩（`driver()` 返回 `verify_connectivity` 抛 `ServiceUnavailable`
> 的假驱动），**保留**原 `health_check` 打桩 ⇒ 对「初始化经不经 health_check」这个实现细节不敏感。
> 收工目录级复测 `ATTEMPTS=0 (blocked=0)`、两条红消失。

### e — 四件尾巴

| 尾巴 | 处置 | 门 |
|---|---|---|
| ③-1 `BoltError` 族 | 守卫式导入 → `_BOLT_PROTOCOL_FAILURES` → 进元组（207）；packstream 裸 `ValueError`/`struct.error` **刻意不收**（与我方缺陷不可分辨） | 门 1c `BoltError` 格 + **门 1c2 恒跑漂移门**（导不到时 `pytest.fail` 而非静默 skip） |
| ③-2 `ConnectionAcquisitionTimeoutError` | **维持 500，零行为改动**；门 1d 由「只钉父类」改为**显式钉子类**；初始化阶段仍 fallback（阶段相关策略，两者不是同一条判据）；**待用户裁** | 门 1d + G2③ 对照格 |
| ③-3 `neo4j is None` 守卫 | **保留**；注释按 Codex 三轮 LOW 改准（删掉**不会崩** —— `AttributeError` 仍被元组接住仍 207；变的是**错误文案的可分辨性**） | `test_neo4j_客户端为_None_时端点给出可分辨的错误文案` |
| ③-4 9 处整体 patch | **不删**，只在文件 docstring 写明覆盖边界与两块缺口各自的门在哪 | 本文件「真写面」段 + t5b |

**⚠️ 与卡文不符并登记**：卡文 (e)③-1 要求的 `# pyright: ignore[reportPrivateImportUsage]` **实测不需要**
（pyright 1.1.411 / `basic` 对 `neo4j._exceptions` 不报该规则；加了反而触发
`reportUnnecessaryTypeIgnoreComment`，warnings 80→81）。故**未加**；本卡改动的生产文件内
`pyright: ignore` 计数 = **0**（改前 edges.py 有 2 条，随死分支一并删除）。

---

## 四 判据结果（全部绑最终 HEAD `efaece7f`）

### f — 结构判据成对 + AST 门 + 验伪锚（`final-struct-*.txt`）

| 判据（**出现次数**口径，不是行数） | 改前 → 改后 |
|---|---|
| `asyncio.to_thread` | **3 → 0** ✅ |
| 裸 `to_thread` | **3 → 2**（docstring 里解释缺陷时提到两次） |
| `hasattr(client` | **4 → 0** ✅ |
| `await client.add_documents(` | **0 → 1** ✅ |
| `_lancedb_client_for(` | **0 → 2** ✅ |
| `BoltError` | **3 → 9** ✅ |
| **验伪锚** `asyncio.gather(` | **1 → 1**（恒 1） |
| **AST Call** `to_thread` / `gather` | **3 → 0** / **1 → 1** ✅ |
| **AST Call** `add_documents`/`connect_lightweight`/`embed`/`resolve_table_name`/`_all_table_names` | 各 **0 → 1**（新路径五环齐备） |
| neo4j_client 段内 `_fallback_to_json()` / `health_check()` / `raise` | **3→2 / 1→0 / 0→2** ✅ |
| **AST Call** `health_check`/`verify_connectivity`/`_fallback_to_json`/`_close_driver` | 1→0 / **1→2** / 5→4 / 2→3 |

> **判据自身的两个坑，如实记**：
> 1. 首次写完后段内 `grep -cF 'health_check()'` 得 **1 而不是 0** —— 命中的是我**自己新写的注释**。
>    这正是「结构门必须数 AST Call 节点，不是文本」。两边都修：注释去括号 + 补 AST 判据。
>    其中 `verify_connectivity` **1→2**（health_check 本体那条保留 + init 新增）是验伪锚：
>    若 AST 跑在空/错文件上，三个数会一起归零。
> 2. **Codex r1 LOW#6 更正（我的自述不实）**：我曾自述「`to_thread` 文本计数由 3 变 0」。复算见上表 ——
>    **裸 `to_thread` 是 3 → 2**，只有带前缀的 `asyncio.to_thread` 与 AST Call 才是 3 → 0。判据没错，**自述写宽了**。

### g — 承重行为门（DD-03 禁 mock）

`final-gates-*.txt`（rc=0）：`collected 249 items` → **249 passed, 0 failed, 0 skipped**。

| 门 | 内容 | 结果 |
|---|---|---|
| **G1①** 真写门 | 真 LanceDB(`tmp_path`)：表恰 1 行、`doc_id == record_id`、`content` 含 `rationale_text`、`len(vector)==1024`、`metadata_json` **键集恰 10 键且逐键核值**（含两个 concept 的值且断言互不相等，使互换可分辨）、`timestamp` 可被 `fromisoformat` 解析、schema 含 `doc_type` | ✅ |
| **G1②** append-only | **同一个 `edge_id`** 写两条 record → 2 行，且两行 `metadata_json.edge_id` 相同 | ✅ |
| **G1③-a/b** | 连接未就绪 ⇒ 拒写不调 `add_documents`；连接正常但 `add_documents` 返 0 ⇒ `not confirmed` 且带 `returned 0` | ✅ |
| **G1④** 端点级 ×2 | `neo4j-ok-200` / `neo4j-down-207`：HTTP 码 + **表内行数 1 + doc_id == 响应体 record_id** | ✅ |
| **G1⑤** 新打通分支 ×2 | `connect` 失败 / `embed` **抛异常** ⇒ 记失败且零建表 | ✅ |
| **G1⑥** 拒毁历史 ×2 | 预置含 2 行历史的表（缺 `doc_type` / 维度 8）⇒ 拒写、错误串含 `2 existing rows` + 具体原因、**旧 2 行一条不少** | ✅ |
| **G1⑧** 行数网 | 模拟上游未知 drop ⇒ `not confirmed`，错误串含 `2 -> 1 … expected 3` | ✅ |
| **G1⑨** 分页门 | 预置 11 张排序靠前的表（前提锚 `len(table_names()) == 10`）⇒ 写入仍被正确确认 | ✅ |
| **G1⑩** 读异常门 | 读表名/表抛异常 ⇒ 拒写，**不得**被当成空表 | ✅ |
| **G1⑪** 向量契约 ×2 | `embed` **成功返回** 8 维 / 1024 字符串 ⇒ 拒写且零建表 | ✅ |
| **G1⑫** 分页外二次追加 | **登记性门**：第二次追加**响亮失败**且第一条仍在（门 docstring 明写「绿不代表功能可用」） | ✅ |
| **G2①②** | 离线 `AuthError`/`ConfigurationError` ⇒ 抛 + `_use_json_fallback is False` + `_driver is None` + `close_calls ≥ 1` + **fallback storage 未被建出** | ✅ |
| **G2③ 对照 ×3（承重）** | `ServiceUnavailable` / `SessionExpired` / `ConnectionAcquisitionTimeoutError` ⇒ 返 True + fallback True | ✅ |
| **G2④** 端到端 | POST → **500**（非 207）；第二次 `raise_server_exceptions=True` 证明该 500 来源确是 `AuthError` | ✅ |
| **G2⑤ 真库** | 7692 + 错密码 ⇒ `initialize()` 抛 `AuthError`，不转 fallback | ✅ **真跑** |
| **G3** 尾巴 | 1c `BoltError` / **1c2 漂移恒跑门** / 1d 含 `ConfigurationError` 与 `ConnectionAcquisitionTimeoutError` 显式格 / None 守卫文案格 | ✅ |

> **G2④ 为什么发两次请求（措辞边界）**：Starlette 的 `ServerErrorMiddleware` 在
> `raise_server_exceptions=False` 下只回纯文本 `Internal Server Error`，异常类型**不进响应体** ——
> 「状态码是 500」与「这个 500 的来源是 AuthError」必须分两次证。卡文原话「失败正文含 AuthError」
> 在该运行模式下不可达，已按可证形态实现并登记。

### h — pyright 保持 0

| | 结果 | 存档 |
|---|---|---|
| 改前 | `0 errors, 80 warnings, 0 informations` | `pyright-open-20260918T165355.txt` |
| 改后（最终） | `0 errors, 80 warnings, 0 informations` | `final-pyright-*.txt` |

> **中途曾到 83，如实记**：向量契约初版用 `isinstance(vector, list)`，pyright 按 `embed()` 的注解
> `-> List[float]` 判它多余（`reportUnnecessaryIsInstance` ×3）。而这里要防的**正是注解说谎**。
> 改成规范化 `[float(x) for x in vector]` 后 warnings 回到 80。
> ⛔ **零** `LEFTHOOK_EXCLUDE=python-typecheck`（每次 commit 的 hook 输出均为 `✔️ python-typecheck`）。

### i — 既有套件不回退（全部绑 `efaece7f`，存档首行写入 `HEAD=<sha>`）

| 套件 | 结果 | 存档 |
|---|---|---|
| 点名 4 套 + 2 个 fixture 文件 + 2 个门文件（合跑） | `collected 249` → **249 passed** | `final-gates-*.txt` |
| `tests/regression` 目录级 | **1913 passed, 6 skipped, 1 xfailed**，rc=0 | `close-regression-20260918T191427.txt` |
| `tests/api` 目录级 | **269 passed**，rc=0 | `close-api-20260918T191427.txt` |
| `tests/unit` 目录级（收工） | **32 failed, 5748 passed, 44 skipped, 13 xfailed**，rc=1 | `close-unit-20260918T191427.txt` |

`tests/unit` nodeid diff（红基线 vs 收工）：**只有 1 条 `<`**（flaky `candidate422`），**零 `>`** ✅
W4 账本（收工）：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` ✅
`grep -rlE 'Neo4jClient|neo4j_client' backend/tests/unit` → **45 个文件**，全部 ⊂ `tests/unit`，由目录级 + nodeid diff 覆盖。

### j — openapi + `python-lint` 跳过一次（协议 §2.3 / D-40）

本卡**不改端点契约**。`spec-sync-flat` glob 含 `edges.py` 且 `--write` 恒刷新 `x-generated-at`
⇒ 它被塞进代码 commit，净差实测**恰 1 行**（只有 volatile 键）⇒ (j) 的「非 volatile 漂移就停下报
主 session」**未触发**。紧接一个**只含 `backend/openapi.json` 的还原 commit**（`efaece7f`）：
只 stage 该文件 ⇒ `spec-sync-flat` 自行 `skip (no matching staged files)` ⇒ **零 LEFTHOOK_EXCLUDE / 零 `--no-verify`**。
`git diff --stat 9c4e7e82 HEAD -- backend/openapi.json` → **空**。

代码 commit 用了 `LEFTHOOK_EXCLUDE=python-lint`（⛔ **不是** `python-typecheck`）。
被跳过门的**原始输出**：`lefthook-python-lint-blocked-20260918T172638.txt`
（`[Python] Lint OK.`；`Would reformat:` 恰是 3 个主干既有文件；同跑 `✔️ python-typecheck (exit: 0)`）。
归因证据 `r3-ruff-format-drift-*.txt`（7 文件口径）—— **两层判据**：

1. **集合层**：HEAD(9c4e7e82) 版 7 文件 dirty 集 = 工作树 dirty 集 =
   {`neo4j_client.py`, `test_edge_rationale_fallback.py`, `test_neo4j_client.py`,
   `test_mock_degradation_transparency.py`, `test_review_mode_support.py`}，**B \ A = ∅**。
2. **行号层**（集合层挡不住「在本来就脏的文件里又写脏几行」）：残留漂移 hunk 与本卡改动 hunk
   **逐文件无交集** —— `neo4j_client.py` 漂移在 :808+（本卡改 :27 与 :368-436）；
   `test_neo4j_client.py` :1201+（本卡改 :432-500）；`test_edge_rationale_fallback.py` 只剩 :239
   （本卡新增区从 :364 起）；两个 fixture 文件漂移在 :107+/:166+（本卡改 :43-78 / :53-88）。

> **⚠️ 中途曾一度不成立，如实记**：加完 BoltError 漂移门后我**没重跑 `ruff format` 就提交**，
> 导致提交态的 `t5b` 带上了本卡新引入的漂移。我先前「本卡零新增漂移」的结论当时是拿**更早的**
> 证据下的。发现后已清掉（`t5b` 与 `edges.py` 最终均 format-clean），并把归因口径从 5 文件扩到 7 文件重测。

**ruff check**：`files=7` → `All checks passed!`，rc=0。
**验伪锚**：临时文件 `print(undefined_name_zzz)` → `F821 Undefined name`，rc=**1** ✅
（⛔ 锚点用 **F821** 不用 F401 —— `backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 不含 F401）。

### k — 负控输入（**8 段**，每段只拆一层）

前提：代码已 commit、工作树干净 ⇒ HEAD = 变异前基准。每段 EXIT trap 无条件
`git show HEAD:<path> > <path>` 还原；**四行 shasum 全对**（跑前工作树 = 跑前 HEAD ≠ 变异后 = 还原后），
跑后 `git diff --stat` 为空。

| 段 | 拆掉的那一层 | 被选中判据的结果 | 存档 |
|---|---|---|---|
| ① | 真写（改回 `to_thread`） | 8 failed / 8 passed，红在 `表 … 不存在` | `negctl-1-to_thread-*` |
| ② | 初始化 fail-closed（`raise` 换回 fallback） | 4 failed / 3 passed；`DID NOT RAISE AuthError` ×2 + 端到端 `实得 207`；**三格对照仍绿** | `negctl-2-raise-to-fallback-*` |
| ③ | 写确认（删 `written != 1`） | 红在「错误串未带 `add_documents returned 0`」 | `negctl-3-drop-return-value-check-*` |
| ④ | 前置拒写（预防） | 红在 `assert 'refused' in '… went 2 -> 1'` | `negctl-4-drop-preflight-refusal-*` |
| ⑤ | 行数网（发现） | 红在 `整表被重建却报了成功: WriteStatus(success=True)` | `negctl-5-drop-rowcount-net-*` |
| ⑥ | 读失败哨兵（改成当空表） | 红在「读取失败被当成了空表」，错误串变 `add_documents returned 0` | `negctl-6-read-failure-as-empty-*` |
| ⑦ | 分页判据（改回 `table_names()`） | 红在 `分页把已写成功的表读成不存在` | `negctl-7-paginated-table-names-*` |
| ⑧ | 向量规范化 | 两格全红，红在 `错误维度的向量被写进去了: WriteStatus(success=True)` | `negctl-8-drop-vector-dim-contract-*` |

> **⚠️ 对负控结论的措辞更正（Codex r4 LOW，我先前写过强）**：我曾写「段③⑤⑥⑧ **各只红 1 格**」。
> 那四段日志都是 `N deselected / 1~2 selected` —— `-k` 本来就只选中那几格。正确表述只能是
> **「被选中的那条判据变红」**，**不能**推出「全套只红一格、没有连坐」。
>
> 另需区分两类红，它们的强度不同：
> - **③⑥ 红在错误文案**，`success=False` 仍绿 —— 说明**后续防线接住了失败**（分层生效的证据）；
> - **⑤⑧ 红在谎报 `success=True`** —— 那才是「防线没了就会说谎」。
> - **② 的三格对照仍绿是正确结果**：它们锁的是**应当保留**的 fallback，不是应当变红的东西。

### l — 地盘核（`r2-territory-*.txt` + 最终复核）

`git --no-pager diff --stat --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'` → **7 个文件**：

```
backend/app/api/v1/endpoints/edges.py
backend/app/clients/neo4j_client.py
backend/tests/integration/test_edges_dual_write_neo4j_t5b.py
backend/tests/unit/test_edge_rationale_fallback.py
backend/tests/unit/test_neo4j_client.py                    ← 地盘外追加 #1（卡文 (d)(4) 明确授权）
backend/tests/unit/test_mock_degradation_transparency.py   ← 地盘外追加 #2（本卡引入的 W4 回归的修复）
backend/tests/unit/test_review_mode_support.py             ← 地盘外追加 #3（同上）
```

- `openapi.json` 净差 **0**；`lancedb_client.py` **未出现**（本卡零改动）✅
- 禁改面逐条 = 0：`index.py`（P1-B）/ `memory_service.py` / `episode_worker.py`（P1-C）/ `models/**` /
  `main.py` / `security.py` / `lefthook.yml` / `tests/conftest.py` / `tests/unit/conftest.py` /
  `tests/support/live_port_guard.py` / `canvas-vault/` ✅
- **验伪锚（post-commit 才有效）**：带 exclude 时 `_bmad-output` 路径条数 = **0**，去掉 = **32** ⇒ exclude 真在起作用。
  ⚠️ 如实记：**commit 前这条锚恒空洞** —— evidence 当时是未跟踪文件，`git diff` 不显示它们。

`neo4j_client.py` 三个 hunk：`@@ -27,6 +27,7 @@`（import 块加 `ConfigurationError`，卡文 (l) 明列的
唯一段外改动）、`@@ -368,6 +369,15 @@`、`@@ -397,24 +407,39 @@`，全在 `initialize` +
`_initialize_neo4j_driver` 内。**比行号区间更强的自证**（行号会随本卡自己的改动漂移，函数体哈希不会）：

```
health_check  fec253443ab95536 → 同   _fallback_to_json  e919a5d6f519c97c → 同
run_query     8596a8fcdb019109 → 同   _run_query_neo4j   56ab4851f320b943 → 同
_close_driver d23eda3cbf0b699b → 同   _initialize_json_fallback 31f8b055ee8b1bd8 → 同
[验伪锚] initialize / _initialize_neo4j_driver → CHANGED（预期）        VERDICT: PASS
```

**三个地盘外追加项的改动面同样用 AST 钉死**：两个 fixture 文件各**只改了
`stub_neo4j_singleton_health_check` 一个函数**，且**函数集合无增删**（`set(before) == set(after)` 为 True）。
**请主 session 集成期核这三项。**

### m — 现网只读

- 新测试的 Neo4j 连接行全走 `NEO4J_TEST_URI` 白名单 **7692**；LanceDB 只在 `tmp_path`
  （测试子类把 `db_path` 钉死 + 0→≥1 注入锚证明用的不是指向 `LANCEDB_DATA_PATH` 的真客户端）。
- **W4 账本是本卡的承重判据之一**（见 §三 d）：收工 `tests/unit` 末行 `ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。
  ⚠️ 读法：**账本计入的、受其覆盖的连接尝试**；它只覆盖 7691/7687，不等于「整进程零网络」。
- `grep -rnE 'fsrs_bridge|decay_beta' <本卡 7 个改动文件>` → **0** ✅
- ⛔ 未写 live vault；⛔ 未连 7691/7687；⛔ 未碰现网 LanceDB 数据目录。

---

## 五 Codex（5 轮，末轮绑最终 HEAD）

| 轮 | 绑定 SHA | B / H / M / L | 存档 |
|---|---|---|---|
| r1 | `ddcaad55` | 0 / **1** / 3 / 2 | `codex-review-CARD-LANCE-DUALWRITE-NEVER-WRITES.md` |
| r2 | `74742100` | 0 / 0 / 3 / 2 | `…-r2.md` |
| r3 | `ab1c258b` | 0 / 0 / 3 / 2 | `…-r3.md` |
| r4 | `3260d720` | 0 / 0 / 3 / 3 | `…-r4.md` |
| **r5** | **`efaece7f`（= 最终 HEAD）** | **0 / 0** / 1 / 2 | `…-r5.md` |

**D-15 达成**：末轮绑最终 HEAD 且 BLOCKER = 0、HIGH = 0。轮次 5，在上限内。

存档首部按协议 §2.1；`.stderr` 自证三行（每轮相同）：
`L2 OpenAI Codex v0.153.3` / `L5 model: gpt-6-astra` / `L9 reasoning effort: ultra`。
命令：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`。
⛔ `*.stderr*` 未入库（`git diff --cached --name-only | grep -c stderr` = 0）；⛔ 无 0 字节存档。

**r1 的 HIGH（既有表被 drop、历史丢失却返回 1）已修**并由 r2/r3/r4/r5 连续确认成立。
r2→r5 的 MEDIUM/LOW 处置见 §三 c 的缺陷链表与 §八 台账。

---

## 六 DoD-3

### 4-A（Claude 已代验，贴证据）

见 §二（先红两份存档）、§四 g（249 passed，含真写门表行数 / fail-closed 门 + 三格对照 / 真库 7692 /
拒毁历史门 / 分页门 / 向量契约门）、§四 f（结构判据 + 两处判据自身的坑）、§四 h（pyright 0）、
§四 k（**8 段**负控 + 措辞更正）、§四 l（地盘门 + 函数体哈希 + AST 改动面）、
§四 i（三套目录级 + nodeid diff + W4 账本，存档首行绑 SHA）、§四 j（openapi 还原 + lint 跳过的两层归因）。

### 4-B（零技术词）

> 我给白板上一条连线写下理由后，它现在**真的**被存进了两个地方——以后搜得到、图谱里也有。
> 要是后台连知识库的密码配错了，页面会明确报错而不是假装成功。
> 而且万一这次保存会把我以前写过的理由一起冲掉，它会**宁可不保存**，先告诉我。
> 我感觉系统不再对我说谎了。

**felt-sense**：以前那句"双写成功"是空的，像把东西放进一个没有底的抽屉；现在抽屉有底了，
坏掉的时候它会当场告诉我，而且它不会为了塞进一张新纸就把整个抽屉倒空。

---

## 七 本卡未证明什么（9 条）

1. **未证明现网存量表的状态**：没查现网是否已存在裸表 `edge_rationales` 或旧 schema 的
   `<vault>_edge_rationales`（现网只读）。前置拒写会挡住不兼容的**非空**既有表，但
   **「现网到底是哪种状态」本卡未测**；空的旧 schema 表仍可能因其他不兼容让 `add_documents` 返 0。
2. **未证明真实 Ollama 路径下的向量与延迟**：门用覆写 `embed` 的确定性 1024 维子类（零网络）。
   真实 `client.embed`（Ollama GPU → sentence-transformers CPU fallback）**本卡未跑**。
3. **未证明「写进去的内容是对的」**：三层确认（返回值 / 前置拒写 / 行数网）证明的是
   「这次调用净增一行且没毁历史」，**不证明**断电持久性、跨进程可见性、并发下的历史完整性。
4. **未证明前置拒写覆盖了全部 drop 触发条件**：它只挡住**已知的两条**（缺 `doc_type` / 维度不符）。
   上游若新增第三条，只由行数网**事后发现**（历史已丢）。
5. **未证明 lazy-init 上抛 `AuthError` 对其他调用方的行为**（Codex r4 给出的逐条实况，本卡**未加门**）：
   `health.py:1025` 外层捕获后返 `status="error"`（**不是** HTTP 500）；
   `neo4j_learning_base.py:186` 直接传播；`neo4j_edge_client.py:160` 初始化在业务 `try` 外，直接传播；
   `dependencies.py:714` 初始化在 `yield` 的 `try/finally` 前，异常会阻止依赖 yield。
   这四个文件都在本卡禁改面内。
6. **未证明 `edge_rationales` 有任何生产读者**：`grep -rn 'edge_rationales' backend/app` 命中全在
   `endpoints/edges.py` ⇒ 写通之后仍是 **G-PIPE（只写不读）**。
7. **未证明「其余 `DriverError` 子类维持 fallback」是正确分类**：只对三类建了显式对照格，
   其余落通用 `except Exception`，**那一支没有独立的门**。
8. **未证明 packstream 裸 `ValueError`/`struct.error` 的归属**（刻意未收）；
   **未证明 `ConnectionAcquisitionTimeoutError` 维持 500 合产品预期**（零行为改动，**待用户裁**）。
9. **未证明整个 pytest 进程零网络**：W4 门对 `tests/integration` 只记账不拦，账本只覆盖 7691/7687。

---

## 八 台账待登记条目（主 session 登记，⛔ 车道不改台账）

1. **修复 sha**：代码 `10bc2803` + openapi 还原 `efaece7f`（HEAD）。结构判据
   `asyncio.to_thread` 3→0（文本 + AST 双口径）/ `hasattr(client` 4→0 / 段内 `health_check()` 1→0、`raise` 0→2；
   先红存档 `lancedb-red-20260918T165634.txt` / `init-red-20260918T170026.txt`；8 段负控见 §四 k。
2. **地盘外追加项 ×3，请集成期核**：① `test_neo4j_client.py` 反向用例改写 + 新增对端不可达对照
   （卡文 (d)(4) 授权）；② `test_mock_degradation_transparency.py`、③ `test_review_mode_support.py`
   的 `stub_neo4j_singleton_health_check` 叠加驱动工厂打桩 —— **本卡引入的 W4 回归的修复**，卡文未预见。
   三项均由 AST 判据钉死（只改指定函数、函数集合无增删）。
3. **openapi 还原 commit** `efaece7f` + hook 原始输出（净差恰 1 行 volatile 键）。
4. **`ConnectionAcquisitionTimeoutError` 归属待用户裁** —— 初始化阶段 fallback、查询阶段 500 是
   **阶段相关策略**（两者不是同一条判据）；门 1d 已显式钉子类；裁 207 只需入元组一行。
5. **私有 `BoltError` 导入登记** —— 守卫式导入 + **门 1c2 恒跑漂移门**（导不到时 `pytest.fail`）。
   ⚠️ 边界：该门保证的是**测试能发现漂移**，**不等于生产运行时会告警**（生产导入失败无日志）。
6. **`edge_rationales` 零读者（G-PIPE）** —— 写通之后仍无生产读者，接读侧或退役**另立卡**。
7. **⛔ 新发现 ①：`add_documents` 的 `doc_type` 列 drop 陷阱** —— 任何往 LanceDB 写**新表**的调用方，
   若文档不带 `doc_type` 键，第二次写入就会把整张表 drop 重建。本卡在写侧带上该键规避；
   **drop 机制本体（G2-9 族）未改**，建议排一张卡横扫全部 `add_documents` 调用方。
8. **⛔ 新发现 ②（Codex r1 HIGH）：既有表被静默 drop** —— 旧表缺 `doc_type` 或维度不符时，
   一次普通写入会毁掉整表历史而 `add_documents` 仍返回 1。本卡加了**前置拒写 + 行数网**两层自保；
   `_check_and_fix_dimension_mismatch` 的「自愈即删表」语义本身仍在，建议另立卡裁定。
9. **⛔ 新发现 ③（Codex r2 MEDIUM）：`table_names()` 默认 `limit=10` 分页** —— 临时库实测建 12 张表
   只返回 10 张、排序靠后的目标表缺席。本卡的行数判据已改走 `_all_table_names()`。
   **但上游 `add_documents` 自己仍用分页的 `table_names()` 判存在性** ⇒
   **分页之外的既有表第二次追加会失败**（误走 `create_table` 撞同名表 ⇒ 返 0）。
   本卡侧无可行绕法（传已解析表名也没用），门 `…_second_append_beyond_pagination_fails_loudly`
   只钉住「响亮失败 + 第一条仍在」。**⛔ 真正修复需另立卡改上游走 `_all_table_names()`；
   在那之前，表数 >10 的 vault 上本功能只能写第一条。**
10. **⛔ 遗留 MEDIUM（Codex r5，未修）：向量规范化漏 `OverflowError`** ——
    `embed()` 返回 `[10**309]*1024` 时 `float()` 抛 `OverflowError`，它**不在**内层
    `(TypeError, ValueError)` 也不在外层 `(RuntimeError, ConnectionError, OSError, ValueError)`
    （实测 `OverflowError` 的 MRO 是 `ArithmeticError → Exception`）⇒ 逸出成 **500**。
    异常发生在写入前，**不污染表也不删历史**，故 Codex 未升 HIGH。
    **未修原因**：Codex 轮次已用满 5 轮（协议上限），再改代码会打破 r5 对最终 HEAD 的终审绑定。
    修法是一处：把 `OverflowError` 加进内层捕获。
11. **⛔ 遗留 LOW（Codex r5，未修）：t5b 措辞残留** ——
    `test_edges_dual_write_neo4j_t5b.py:60` 仍写「**永不返 None**」、`:1233` 仍写「生产不可达」，
    与紧邻的「注解与计数不足以证明不可达」自相矛盾。纯 docstring，可由主 session 按 D-32 顺手改。
    **未修原因同 #10**（保住 r5 的终审绑定；协议对 LOW 是登记不阻断）。
12. **`health_check` 的 `except Exception` 全捕获仍是 H1 的另一处吞点** —— 本卡在 init 路径**不经**它，
    未改其本体（它服务 `/health` 周期探测，fail-closed 返 False 是对的）。
13. **勘探 → 实测更正（5 条）**：`add_documents` 卡文 `:3787` → 实测 `:4344`；「`:411` 吞 AuthError」
    实测**吞点是 `health_check` 全捕获 + 其后 fallback**；`asyncio.gather(` `:427` → `:424`；
    `return _client_instance` `:2809` → `:2808`；卡文 (c)(1) 引的 `index.py:116` 实为**日志 kwarg**。
14. **卡文 (e)③-1 的 `# pyright: ignore[reportPrivateImportUsage]` 实测不需要**，未加。
15. **`python-lint` 跳过一次（协议 §2.3 / D-40）** —— 原始输出 + **两层归因**（集合层 B\A = ∅ +
    行号层逐文件无交集）已落档 `r3-ruff-format-drift-*.txt`；
    ⚠️ 过程中曾一度因「加门后未重跑 format 就提交」而真的引入过漂移，已清并重测，见 §四 j。
    ⛔ `python-typecheck` 每次 commit 均为 `✔️`，零 exclude。
16. **Codex 各轮**：见 §五 表（5 轮，末轮 `r5` 绑 `efaece7f`，B/H = 0）。
