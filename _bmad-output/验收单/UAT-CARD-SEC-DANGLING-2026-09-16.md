# UAT — CARD-SEC-DANGLING（第十四批 T5-D）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-SEC-DANGLING]` · 车道 `card-t5-bugs`（分支 `card/t5-bugs`）
> 前提 HEAD（T5-C CARD-T-SWITCHVAULT 末 commit）= `2287e2583c54472d238e8b8eec87bb1e9e95c9e8`
> 证据目录 `_bmad-output/审查/evidence-sec-dangling/`（引用一律写全文件名，不用 glob）
> **采用方案 = A**（`backend/app/security.py` 的 `APIKeyHeader(...)` 加 `scheme_name="InternalApiKey"`）

---

## 〇 第 0 分钟自证

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-t5-bugs` ✅ |
| 分支 | `card/t5-bugs` ✅ |
| HEAD | `2287e2583c54472d238e8b8eec87bb1e9e95c9e8` = T5-C 末 commit ✅；`git merge-base --is-ancestor 08100483 HEAD` 成立 |
| `git status --porcelain` | 空 ✅ |
| venv / env | `test -x backend/.venv/bin/pytest` ✅ · `test -e backend/.env` ✅ · `test -x backend/.venv/bin/pyright` ✅ |
| 基线自证（R-B14-2） | `grep -vc '^#' <BASE>` = **64** ✅（`wc -l` = 67 = 3 注释 + 64 nodeid） |
| pyright 波 0 口径 | `(cd backend && "$P" app)` = **0 errors, 81 warnings** ✅（见 `pyright-app-20260916T195022.txt`） |

**§〇 逐条 file:line 复核（全部与卡文逐字相符，无漂移）**

- `backend/app/security.py:48 INTERNAL_API_KEY_HEADER_NAME = "X-CLS-Internal-Key"`；`:52 INTERNAL_API_KEY_HEADER = APIKeyHeader(`；`grep -n 'scheme_name' backend/app/security.py` = **0 命中**（rc=1）✅
- `backend/app/core/security.py` → `No such file or directory` ✅（R-B14-8 的错名更正成立）；真文件 `backend/app/security.py` 11121 B ✅
- `backend/app/main.py`：`:541 def _custom_openapi():` / `:547 openapi_schema = get_openapi(` / `:554 components["securitySchemes"] = {` / `:555 "InternalApiKey": {` / `:568 openapi_schema["security"] = [{"InternalApiKey": []}]` / `:570 return app.openapi_schema` ✅
- `backend/app/api/v1/system.py`：`:28 router = APIRouter(` / `:29 prefix="/system"` / `:35 dependencies=[Depends(require_internal_api_key)]`；`CARD-RED-A1-sentinel` 注释块首行 = **`:31`** ✅（卡文已更正过勘探稿的 `:30-32`，本次复测与卡文一致）
- 车道代码基线：`git diff --name-only 08100483 HEAD -- . ':(exclude)_bmad-output'` 只含 T5-A/B/C 的 7 个文件，**不含 `security.py` / `main.py` / `system.py` / `openapi.json`** ⇒ 本卡四个承重文件在 `B14_BASE` 原态 ✅

---

## 一 4-A：Claude 已代验的技术证据

### (a) 开工首项 —— contract 三文件基线

`contract-3files-open-20260916T194004.txt`：末行 `2 failed, 75 passed, 577 warnings in 269.07s`，`rc=1`。
两条红与卡文点名的逐字相同，**定性主干既有**：

1. `tests/contract/test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema`
   —— 根因本次实测定死：`FileNotFoundError: … /specs/data/canvas-node.schema.json`（同档 `:20`）。该文件在 `B14_BASE` 上同样不存在（`git cat-file -e 08100483:specs/data/canvas-node.schema.json` → `does not exist`）⇒ 与本卡无关。
2. `tests/contract/test_health_contract.py::test_health_contract[GET /api/v1/health]` —— 卡文 §〇 记的 `DeadlineExceeded`（W4 端口门下真实请求 16–19s > `deadline=10000`）。

同档 W4 行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=19 (blocked=19, advisory=0, unaccounted=0)` —— 与卡文 (j) 预期同值，`advisory` / `unaccounted` 均为 0，是端口门**拦下**而非本卡连库。
`test_committed_snapshot_has_no_drift` 在开工时**绿**（该文件 26 条全 `.`）⇒ T5-A/B/C 未引入快照漂移。

### (b) 悬空实测与门先红

| 口径 | 改前 | 再生后 |
|---|---|---|
| committed `backend/openapi.json`（`dangling-count-before-20260916T194014.txt` / `dangling-count-after-20260916T194629.txt`） | `securitySchemes=['InternalApiKey']` · `dangling=31` · `system=16` · `per_op={'APIKeyHeader':31}` | `dangling=0` · `system=0` · `per_op={'InternalApiKey':31}` |
| 进程内 live schema（本卡新增门） | 红：31 悬空 / `/system/*` 16 | 绿 |
| paths / operations | 197 / 209 | 197 / 209（不变） |

**统计脚本的验伪锚** `dangling-script-falsification-20260916T194039.txt`（三个锚，只在 `/tmp` 副本上注入，committed 快照跑前跑后 sha256 均 `1455eb7d…`）：

- 锚① 往一个**非** `/system/` op 注入未声明方案名 → `dangling 31→32`、`system 16→16`；
- 锚② 往 `POST /api/v1/system/config` 注入 → `dangling 31→32`、`system 16→17`；
- 锚③ 反方向：副本的 `securitySchemes` 补上 `APIKeyHeader` → `dangling=0 system=0`。
  ⇒ 两个计数器都真在数，且「0」是由集合成员判定驱动的可达值，不是恒 0。

**先红（最终版门代码）** `red-and-negctl-final-20260916T195803.txt` 阶段 1：源与快照都用 `git show HEAD:<path>` 还原成 **HEAD 全态**（sha 自证 `8c8c9098…` / `1455eb7d…`），门 `pytest_rc=1`，失败正文含 `31 处` / `/system/* 16 处` / `APIKeyHeader` / 具体 `/system/` op 清单；同档第二口径（committed 快照统计）同时给出 `dangling=31 system=16`，两个口径互证。

> ⚠️ 如实登记：`sec-dangling-red-20260916T194419.txt` 与 `sec-dangling-green-20260916T194658.txt`、`negative-control-20260916T194827.txt`、`negative-control-rc-20260916T194913.txt` 四份是**门改名前**的版本（原名 `test_security_schemes_cover_all_per_op_refs`，覆盖面只有 per-op）。改名与扩覆盖的理由见下方 (c)-补，承重结论一律以 `red-and-negctl-final-20260916T195803.txt` / `sec-dangling-green-v2-20260916T195255.txt` 为准，旧四份保留作过程留痕、不作依据。

### (c) 修法 —— 采用方案 A，理由

`backend/app/security.py` 的 `APIKeyHeader(...)` 调用加一个 keyword：`scheme_name="InternalApiKey"`（另加一段说明注释）。

**选 A 不选 B 的四条理由**

1. **修根因不修症状**：悬空的成因是 FastAPI 按类名命名方案（`fastapi/security/api_key.py:29` `self.scheme_name = scheme_name or self.__class__.__name__`，本机 fastapi **0.135.3** 实测；`fastapi/openapi/utils.py:93` `security_name = security_dependency._security_scheme.scheme_name` 是 per-op 名字的唯一来源）。A 让 FastAPI 一开始就写对；B 是在 `_custom_openapi` 产出之后再遍历改名，底层不一致仍在。
2. **避开 `main.py` 的跨车道交集**：手册 §一「`backend/app/main.py` 声明交集」把 `:568` security 段给 T5-D、`:386-404` 回填门段给 T6-B。走 A 则本卡对 `main.py` **零改动**（实测 `git diff --stat HEAD -- backend/app/main.py` = 0 行），集成期无需判两段 hunk 是否重叠。
3. **运行时零风险可由源码证明**（见下）。
4. `scheme_name` 是该版本 FastAPI 的**公开参数**且语义就是本卡要的：签名 `scheme_name: Annotated[str | None, Doc("Security scheme name. It will be included in the generated OpenAPI …")] = None`（本机 `inspect.signature` 实测）。

> DD-01/DD-04 的查证方式如实说明：本 session 的 **Context7 MCP 连接失败**（`CONNECTION_CLOSED`），故改用**本机已安装版本的源码**（比文档更贴合"本机这个版本是否接受"这一问题）+ FastAPI 官方文档/issue 佐证，两者结论一致。

**运行时鉴权一字未改 —— 三层证据** `runtime-auth-unchanged-20260916T194743.txt` + `auth-behavior-tests-20260916T194754.txt`

- **层 1 AST**：顶层节点序列相同；AST 不同的顶层节点 **只有 1 个**（那条 `INTERNAL_API_KEY_HEADER = APIKeyHeader(...)` 赋值），其 keyword 从 `['name','auto_error','description']` 变为 `['name','scheme_name','auto_error','description']`，**剔除 `scheme_name` 后与改前 AST 逐字相同**；两个顶层函数 `require_internal_api_key` / `verify_websocket_internal_key` 的 AST **完全相同**。
- **层 2 运行时属性**：`model.name='X-CLS-Internal-Key'`（真正决定读哪个 header）、`auto_error=False`、`model.in_=header` 全部未变；新增的只有 `scheme_name='InternalApiKey'`。`APIKeyHeader.__call__` 源码只读 `self.model.name`，不触碰 `scheme_name`。
- **层 3 既有行为门**：`tests/unit/test_sync_batch_auth.py` + `test_system_endpoint_auth.py` + `test_internal_api_key_p0_2_hardening.py` = **30 passed**（含 `TestProductionFailClosed` / `TestHeaderParsing::test_canonical_header_name`），`blocked=0`。

**(c)-补 · 门的覆盖面被扩到全 `security` 面并据此改名（如实登记）**

卡文 (b) 只要求枚举 `paths[p][m].security`。落地中段做了一次普查（`security-key-census-20260916T195206.txt`）：schema 里名为 `security` 的键共 **32** 处 = 31 per-op + **1 处文档根全局**；无 `webhooks`、无 `components.callbacks`/`pathItems`；WebSocket 路由（`main.py:809` `/ws/intelligent-parallel/{session_id}`、`:839` `/ws`）不产出 OpenAPI operation，其鉴权走 `security.py:194 verify_websocket_internal_key` 手工校验，**根本不是 OpenAPI 安全方案**，不在任何 OpenAPI 契约门的覆盖面内。

全局那一处当时实测已声明（不悬空），但它是 (b) 原口径**唯一没盖到**的引用面。遂把门扩成"每一处 `security` 引用"，并按「判据取名面必须恰好等于其主张」把测试改名为 `test_security_schemes_cover_all_security_refs`。这是**加强不是放宽**：per-op 面的断言一字未松（仍断言悬空 **等于 0** 且逐个方案名 ∈ securitySchemes），只是多盖了根节点。先红数字不受影响（根那处已声明 ⇒ 悬空仍是 31/16，见 `red-and-negctl-final-…` 阶段 1 的 `引用总数=32(其中 per-op 31)`）。

### (d) 再生快照

`openapi-regen-20260916T194604.txt`：`( cd backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --write openapi.json )` → `WROTE: openapi.json (paths=197 schemas=357, …)`，`--write rc=0`。sha256 `1455eb7d…` → `9df9f7df…`，字节 917381 → 917443（**+62 = 31 × (len("InternalApiKey") − len("APIKeyHeader"))**，与 31 处重命名自洽）。

**不连库自证（同档原文）**：工具的 socket 禁闭在本次跑中**真的触发过** —— LiteLLM 试图拉取远程 model cost map 被拦：`socket connect blocked during OpenAPI export (target=('127.0.0.1', 1082)) — check-openapi-drift.py 只允许 import, 不允许 lifespan/网络行为`。这比"代码里写了禁闭"强：它是禁闭生效的实跑证据。

**再生 diff 面 = 恰好 31 处重命名 + 1 个易变键** `regen-diff-surface-20260916T194646.txt`：

```
扁平叶子数: 再生前 = 12435  再生后 = 12435
仅在再生前的键 = 31  其中 …>security[i]>APIKeyHeader = 31
仅在再生后的键 = 31  其中 …>security[i]>InternalApiKey = 31
剩余未被该两式解释的键(再生前) = []
剩余未被该两式解释的键(再生后) = []
两侧都有但值变了的键 = ['>info>x-generated-at']
其中 /system/* 面的 APIKeyHeader 消失数 = 16
```

⇒ **未扫入** RED-A1-sentinel §6⑬ 那类与安全无关的既有 docstring 漂移（卡文预期"无"，实测确为无）。

> ⚠️ **判据缺陷自曝（承重）**：本判据的第一版写在 `dangling-count-after-20260916T194629.txt` 里，其 `flat()` 对**空容器**不产出叶子 —— 而 per-op security 恰好是 `{"APIKeyHeader": []}` 这种「键才是信息、值是空列表」的结构，于是方案名那一层整个从比对面上消失，判据报「0 差异」看着像绿，**实际恰好瞎在本卡要测的那一点上**。`regen-diff-surface-20260916T194646.txt` 是修正版，并带一条验伪锚（喂一个已知 `{"APIKeyHeader": []}` 结构，断言 `flat` 能产出 `…>security[0]>APIKeyHeader` 键）。`dangling-count-after-…` 中的 **悬空统计部分（`dangling=0 system=0`）不受影响**（那是另一段独立脚本，锚③ 已证其非恒 0），只有该档内的 diff-面结论作废。

### (e) 契约门先红后绿

| 时点 | `test_committed_snapshot_has_no_drift` | 本卡新增门 | 存档 |
|---|---|---|---|
| 开工（未改源） | **绿** | **红**（31/16） | `contract-3files-open-20260916T194004.txt` · `red-and-negctl-final-20260916T195803.txt` 阶段 1 |
| 改源、**未**再生 | **红** | 绿 | `drift-gate-red-before-regen-20260916T194526.txt` |
| 改源 + 再生 | **绿** | **绿** | `sec-dangling-green-v2-20260916T195255.txt`（`2 passed` rc=0） |

改源未再生那一档的红文正好把 (d) 的必要性说清楚：差异逐条形如
`>paths/…/post>security[0]>APIKeyHeader: 仅在 snapshot(已从 app 移除)` + `…>InternalApiKey: 仅在 app.openapi()(snapshot 缺失)`。

**收工 contract 三文件** `contract-3files-close-20260916T195852.txt`：末行 `2 failed, 75 passed, 577 warnings in 227.90s`，`rc=1` —— 与开工档**逐条相同**：

- 红仍是且只是那两条主干既有（`test_pattern_matches_json_schema` / `test_health_contract[GET /api/v1/health]`），**不增不减、无一由红转绿或由绿转红**；
- `test_openapi_snapshot_drift.py` 26 条全绿（含 `test_committed_snapshot_has_no_drift`）⇒ (d) 的再生把门重新喂绿了；
- W4 行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=19 (blocked=19, advisory=0, unaccounted=0)`，与开工档同值。

### (f) 负控 / 验伪锚（承重）

`red-and-negctl-final-20260916T195803.txt`，一个变异窗口内两段，**EXIT trap 无条件还原**，手法 `git show HEAD:<path> > <工作树文件>`（⛔ 全程未用 `git stash`、未用 `git checkout`）：

- **阶段 1（先红）**：`security.py` + `openapi.json` 双还原为 HEAD ⇒ 门 `pytest_rc=1`，正文含 `31`、`/system/* 16`、`APIKeyHeader`、`/system/` op 清单。
- **阶段 2（负控）**：**只**把源回退、快照保留本卡再生的 0 悬空版 ⇒ 门仍 `FAILED`，`test_committed_snapshot_has_no_drift` 同时 `FAILED`（`2 failed` rc=1）。这一段的信息量在于：**本门读的是 live schema，不是 committed 快照** —— 快照已经"干净"了，源一回退门照样红，门不会被一份好看的快照喂饱。
- **还原自证**：跑前 / 跑后 `shasum -a 256` 三文件逐字相同（`925443dc…` / `9df9f7df…` / `ae5d7e0b…`），`git status --porcelain` 仍是三个 `M`。
- **对照输入（门在无缺陷态是绿的）**：`sec-dangling-green-v2-20260916T195255.txt` 同一条 nodeid `2 passed` rc=0 —— 保证上面的红不是"这条门恒红"。

另有改名前的同型负控 `negative-control-20260916T194827.txt` / `negative-control-rc-20260916T194913.txt`（两条 `pytest_rc=1`），保留作过程留痕。

### (g) pyright 保持 0

`pyright-app-20260916T195022.txt`：绝对路径 + `test -x` 自证（`pyright 1.1.411`）、cwd = `backend/`（R-B14-10）、`grep -E '^[0-9]+ errors?, '` 取汇总（⛔ 未用 `| tail -1`）→ **`0 errors, 81 warnings, 0 informations`**，与 `B14_BASE` 同。本卡零新增 error ⇒ 无需任何 `# pyright: ignore`。**全程未使用 `LEFTHOOK_EXCLUDE=python-typecheck`。**

### (h) tests/unit 目录级

`unit-close-20260916T195010.txt`：`cd backend` 后 `--ignore tests/unit/test_deploy_vault_sh.py`（相对路径，R-B14-3），末行 `35 failed, 5081 passed, 48 skipped, 23 xfailed, 171 warnings, 29 errors in 408.60s`，`rc=1`。

nodeid 口径 diff（`base.nodeids` vs `close.nodeids`，固定 `RUN` 变量防 glob，⛔ 未用 `wc -l` 当判据）：

```
base = 64   close = 64
diff base close → 空（diff_rc=0）；'>' 行数 = 0
```

⇒ **零新增、零消失**，完全落在"只允许 `<`"之内（本卡预期 diff 空，实测即空）。同档 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。

### (i) 地盘核

`territory-precommit-20260916T195334.txt`（commit 前口径）+ 收工后的 commit 范围口径见「收工复核」节。改动文件恰为方案 A 的三项：

```
backend/app/security.py
backend/openapi.json
backend/tests/contract/test_openapi_contract.py
```

- `backend/app/main.py` diff = **0 行** ⇒ 方案 A 不碰 `main.py`，**自然不可能越到 `:386-404`（T6-B 面）**；
- `backend/app/api/v1/system.py` diff = 0 行 ⇒ 禁改面未碰（卡文预言成立：方案名统一后 16 处随之解悬空，无需编辑 system.py）；
- `backend/tests/conftest.py` / `tests/unit/conftest.py` / 三个只读 contract 文件 diff 合计 = 0 行。

### (j) 现网 / 安全只读

- **不连 7691/7687**：本卡自己的两条路径（取 schema、再生快照）在每一次运行里都打印 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`（`sec-dangling-green-v2-…` / `red-and-negctl-final-…` / `security-key-census-…` / `contract-collect-only-…`）；再生工具的 socket 禁闭有实跑触发证据（见 (d)）。contract 三文件跑出的 `blocked=19` 来自 `test_health_contract` 的真实请求被端口门拦下，`advisory=0 / unaccounted=0`，卡文 (j) 已预先定性。
- **零写者门**：`git diff --name-only … | grep -cF -e 'fsrs_bridge' -e 'decay_beta'` = **0**；验伪锚 `git ls-files canvas-vault/.claude/scripts | grep -cF …` = **2**（证明 grep 真在数）。两个 `.py` 改动文件正文命中 = 0；对照：`backend/openapi.json` 正文命中 = **2**（其 description 本来就引用这两个名字，卡文点名不得把它放进违规判据 —— 此处作为"grep 没坏"的正向对照）。
- **live vault**：`git diff --name-only HEAD -- canvas-vault` = 0 行。全程未触发任何 `[readonly-path-guard R…]` 拦截。

### 附加判据（卡文未要求，但与结论相关）

- **全 `security` 面普查** `security-key-census-20260916T195206.txt`：再生后「任何位置的悬空 = `[]`」，全部出现过的方案名 = `['InternalApiKey']` = 声明集。
- **收集面未被破坏** `contract-collect-only-20260916T195536.txt`：`test_openapi_contract.py` `--collect-only -q` = **91 tests collected**（89 条 schemathesis GET 生成面 + `TestCanvasWorkflow` 1 条 + 本卡新增 1 条），本卡新增的 nodeid 在收集面内（grep = 1）。既有 schemathesis 测试**一行未动**。
- **ruff** `ruff-final-20260916T195431.txt`（zsh 数组写法，`files=2`；同目录 `ruff-20260916T195047.txt` 是门改名前那一版测试文件上的旧跑，**已被本档取代**，保留作过程留痕）：`ruff check` → `All checks passed!` rc=0；验伪锚用 **F821**（⛔ 不用 F401：`backend/ruff.toml` `select=["E9","F63","F7","F82"]`，F401 未启用，拿它当锚恒不触发）→ `Found 1 error` rc=1。最长行按**字符**计 = 87（security.py）/ 107（测试文件），无 >120 行（⛔ `awk length()` 按字节，`═` 占 3 字节会假报 239）。

---

## 二 已知偏差与登记不阻断项

### 1. `ruff format --check` 在 `backend/app/security.py` 上为红 —— 主干既有，本卡零新增

`ruff-format-preexisting-20260916T195125.txt`，四条判据：

- **A 多重集对照**（协议 §2.3 规定形态）：改前 / 改后各自的 `ruff format --diff` 内容行多重集大小都是 **27**，`after − before` = **0 新增**，`before − after` = 0 消失。
- **B 行号不交集**：本卡改动行（新文件侧）= `[54…63]`；`ruff format` 想改的行 = `[118…264]`；**交集 = 空**。
- **C 验伪锚**：B 的 `@@` 解析逻辑对两个已知 hunk 头解出 12 行（期望 9+3），证明它真会命中。
- **D**：HEAD 版 `security.py` 在同一配置下同样 `Would reformat`（`head_ver_rc=1`）⇒ 红态先于本卡存在。

`ruff format` 想改的四处全在 `require_internal_api_key` / `verify_websocket_internal_key` 函数体（`:118` / `:153` / `:163` / `:226` 起），**没有一处是本卡写的行**。按协议 §2.3 / 手册 §一.1.7 的 462 文件过渡条款：本卡带存档 `LEFTHOOK_EXCLUDE=python-lint` 提交。⛔ **不得顺手 `ruff format`** 改那 27 行存量 —— 那是 D-40 / T8-G 的面，顺手修 = 同文件双写者。

**被跳过门的原始输出** `lefthook-precommit-20260916T200333.txt`（裸调用 `/opt/homebrew/bin/lefthook run pre-commit`，R-B14-1；`lefthook version` = `2.1.6`，31 个 staged 文件，`rc=1`）：

```
┃  python-lint ❯
[Python] Running ruff lint...
All checks passed!
[Python] Lint OK.
[Python] Checking format...
Would reformat: backend/app/security.py
1 file would be reformatted, 1 file already formatted
[Python] Format check FAILED! Fix: ruff format backend/app/security.py backend/tests/contract/test_openapi_contract.py
```

⇒ 被跳过的这道门里，**`ruff check` 那一半是绿的**（同档原文 `All checks passed!` / `[Python] Lint OK.`），红只来自 `ruff format --check` 的存量漂移一项。

同档还证实 **`python-typecheck` 正常跑且通过**：`[Python] Running pyright type check (backend/.venv/bin/pyright)... 0 errors, 0 warnings, 0 informations / [Python] Typecheck done (exit: 0)`（对 staged 文件口径，故 warnings 为 0；全量 `pyright app` 的 81 warnings 见 (g)）。⛔ 全程未使用 `LEFTHOOK_EXCLUDE=python-typecheck`。

### 2. 新发现 —— lefthook 两条 `spec-sync` glob 都不覆盖 `backend/app/security.py`

`lefthook.yml:52` `spec-sync-flat` glob = `backend/app/{api,models,schemas,mcp}/*.py`；`:63` `spec-sync-root` glob = `backend/app/{main.py,config.py}`。`backend/app/security.py` **两条都不命中** ⇒ 改它不会触发 `check-openapi-drift.py --write` 自动再生 + `git add`。

而本卡恰恰证明了**改 `security.py` 会改变 `app.openapi()`**（31 处 per-op 方案名）。这与该 hook 自己的设计意图直接相抵 —— `lefthook.yml:36-39` 写着「`app.openapi()` 不只由 api/models/schemas 塑造 —— `main.py`(路由挂载)/`config.py`(设置与前缀)/`mcp/**`(工具注册改写 schema)都在其中」，枚举里漏了 `security.py` 这一类"塑造安全面"的根级文件。

**hook 自己的实证**（不只是读 glob）：`lefthook-precommit-20260916T200333.txt` 在 `backend/app/security.py` 与 `backend/openapi.json` **都已 staged** 的情况下，仍打印

```
│  spec-sync-flat (skip) no matching staged files
│  spec-sync-root (skip) no matching staged files
```

⇒ 两条 glob 确实都没命中，结论由 hook 自身输出坐实。

**影响面（如实）**：不是本卡的缺陷（本卡按 (d) 手动再生了），但它意味着**将来**有人改 `security.py` 而忘了再生时，hook 不会出声；兜底只剩 `test_openapi_snapshot_drift.py` 这道门。已登记为台账条目 ③，建议归口 T8 工具链或第十五批单独立卡（`lefthook.yml` 是 **T8 独占地盘**，本卡不得改）。

### 3. 门改名与扩覆盖

见 (c)-补。四份改名前的存档保留但不作依据，承重结论只引最终版两份。

### 4. `info.x-generated-at` 每次再生必变

本卡再生的 `backend/openapi.json` 带本次时间戳。按设计 §2/§3，权威再生由主 session 在全部 openapi 改动卡合入后做两次；本卡再生只为车道内 snapshot-drift 门绿。

---

## 三 收工复核（Codex 前的最终态）

见文末「四 Codex 复核」与「五 提交」两节。

---

## 四 本卡未证明什么（≥4）

1. **未证明全量 `test_openapi_contract.py` 通过**。该文件 `--collect-only` 现测 **91 collected**（生成面为 GET-only：89 条 + `TestCanvasWorkflow` + 本卡 1 条），但全量真跑在 W4 端口门下每 op 数分钟（`B14_BASE` 上第二 op >5 分钟被中止），仍是小时级，且它对「方案名/状态码是否被声明」这条性质**不产生信号**（恒 `DeadlineExceeded`，`status_code_conformance` 在历史存档里出现 0 次，RED-A1-sentinel §6⑮）。本卡只用进程内 `app.openapi()` 断言，不以该门的 before/after 差集作为证据。
2. **未改也未证明运行时鉴权行为的正确性**。本卡证明的是"运行时行为**未变**"（AST + 运行时属性 + 30 条既有测试），不是"它本来就对"。`require_internal_api_key` 的 fail-closed matrix / 403 / 503 行为门归本批 **T10-E `CARD-RED-HYGIENE`**（前身第十三批 U10-E）。
3. **未证明 CI 上的行为**。所有结论都在本机 Python 3.14 / fastapi 0.135.3 下取得；契约测试不在 `.github/workflows/test.yml` 白名单内，`x-generated-at` 与 schema 导出在 CI 的 3.11/3.12 下是否逐字相同**未对跑**（这条缺口是 `test_openapi_snapshot_drift.py` 模块 docstring 自述的既有缺口，本卡未缩小）。
4. **未证明主 session 集成期权威再生的 `openapi.json` 与本卡再生逐字节相同**。本卡再生只为车道内门绿；权威态由主 session 在队列 3 完成后再生两次。
5. **未证明两条 contract 主干既有红的完整根因链**。只定性到：红① = `specs/data/canvas-node.schema.json` 缺失（`B14_BASE` 上同样缺失）；红② = `DeadlineExceeded`。为什么该 schema 文件从未入库、是否该补，未查（红② 与 T10-E 同面）。
6. **未证明 WebSocket 侧鉴权的契约表达**。`/ws` 与 `/ws/intelligent-parallel/{session_id}` 不产出 OpenAPI operation，其鉴权走 `verify_websocket_internal_key` 手工校验 —— 这意味着**第三方工具从 OpenAPI 读不到 WS 鉴权要求**。本卡只核实了"它不在 OpenAPI 覆盖面内、故不构成悬空"，**没有**评估"WS 鉴权是否应当以别的方式进契约"。
7. **未证明除这 31 处外无别的鉴权入口**。插件侧 `main.ts` 手发的 `X-CLS-Internal-Key` 本身是对的、不受本卡影响（RED-A1-sentinel §6⑭）；`kg_health.py` 等仍无鉴权端点的真连点收口（§6⑪）在地盘外，未碰。
8. **未证明 `LEFTHOOK_EXCLUDE=python-lint` 跳过的那次 hook 里没有别的检查项**。已核 `python-lint` 只含 `ruff check` + `ruff format --check` 两步，前者本卡已自跑 rc=0；但未逐行审计 lefthook 在 2.1.6 下对该命令块的完整执行语义。
9. **本门不检测 `securitySchemes` 里的冗余 / 同义方案**（自曝一条覆盖边界）。门的主张是「每一处引用都能找到定义」，是**包含关系**不是**等价关系**。因此若有人用卡文 §三 明令禁止的那条修法 —— 给 `securitySchemes` 补一个 `APIKeyHeader` 别名 —— 悬空同样归 0、本门同样会绿，尽管契约里会留下两个同义方案、与「统一」背道。本卡是**靠选型**（方案 A 从源头改名）而不是靠这道门排除该走法的；门只锁「不悬空」，不锁「不冗余」。同理，一个**被声明但无人引用**的方案也不会被本门发现。
10. **未证明再生后的 `securitySchemes` 定义体本身正确**。门只比方案**名**；`InternalApiKey` 的 `type`/`in`/`name` 三个字段仍由 `main.py:554-566` 手写覆盖，本卡未对它们加任何断言（只在 (c) 层 2 顺带实测 `model.name` 未变）。
11. **门不解析 `$ref`，故它的覆盖面是「全部**内联**位置」而不是「全部合法位置」**（Codex r2 MEDIUM-1 收窄）。Path Item 与 Callback 都可以写成 `$ref`，目标能落在枚举清单之外（根上的 `x-` 扩展、甚至外部文档），那种形状的悬空本门看不见。对**本仓**不构成缺口的依据是实测而非推理：`ref-distribution-census-20260916T204712.txt` —— 全文 `$ref` 736 处（`components` 212 / `paths` 524），**Path Item 级 `$ref`（`$.paths.<path>.$ref`）= 0**，`paths` 下那 524 处全在更深层（operation 的请求/响应 schema），承载不了 Security Requirement。**换生成器或手工拼 spec 时这就是真缺口。**
12. **门与模块级 `pytest.importorskip("schemathesis")` 的耦合未解**（Codex r1 LOW-2 / r2 LOW-2）。schemathesis 缺席时，本卡这条非 schemathesis 的静态门会被一并跳过。⚠️ 理由更正：这**不是**技术上做不到（可把可选导入与 `from_asgi` 初始化收进「依赖可用」分支、静态门独立定义在分支外），而是**范围决策** —— 那要改 `:17`–`:19` 与 `:78`–`:85` 这些既有模块级行，卡文 §三 明写「既有 schemathesis 测试一行不动」。留作移交项。
13. **未证明「整条收集路径无网络行为」，且已实测到反例**。`test_openapi_contract.py:18` 的模块级 `from app.main import app` 不在任何 socket 禁闭内；r3 探针运行时实测该 import 触发了 LiteLLM 对 `raw.githubusercontent.com` 的**真实外联**并 SSL 握手超时（原文见 `enum-coverage-probe-r3-20260916T232823.txt` 运行段首行）。它**不是** 7691/7687（每次跑的 W4 记账仍为 `blocked=0/advisory=0/unaccounted=0`），也**不是本卡引入**（是 `import app.main` 的既有行为，本仓所有测试都走这条路），但它坐实了那条主张必须收窄：本门只主张「断言自身不发 HTTP 请求」+「W4 端口门逐次记账为 0」。

---

## 五 台账待登记条目（≥4）

1. **CARD-SEC-DANGLING：OpenAPI 悬空 security 引用 31 → 0（`/system/*` 16 → 0）**，方案名统一为已声明的 `InternalApiKey`。**采用方案 A**（`backend/app/security.py` 的 `APIKeyHeader(...)` 加 `scheme_name="InternalApiKey"`），理由 = 修根因 / 避开 `main.py` 与 T6-B 的跨车道交集（本卡对 `main.py` 零改动）/ 运行时零影响可由源码与 AST 证明。门 nodeid = `backend/tests/contract/test_openapi_contract.py::test_security_schemes_cover_all_security_refs`。修复 sha 见文末。
2. **`backend/openapi.json` 再生**是车道内 snapshot-drift 门绿的最小必要动作；**权威再生由主 session 在集成期做两次**（与其它 openapi 改动卡同批，设计 §3 交集声明）。本卡再生的 diff 面已实证为「恰好 31 处 per-op 方案名重命名 + `info.x-generated-at`」，无额外漂移扫入。
3. **新发现（建议立卡，归口 T8 / 第十五批）**：lefthook `spec-sync-flat` / `spec-sync-root` 两条 glob 都不覆盖 `backend/app/security.py`，而改该文件确实会改变 `app.openapi()`。与 hook 注释 `lefthook.yml:36-39` 的设计意图相抵。`lefthook.yml` 是 T8 独占地盘，本卡不得改。
4. **全量 schemathesis 契约门的 `DeadlineExceeded` 瞎点问题**（RED-A1-sentinel §6⑮）+ §6⑯ 两处 `-k` 判据坑，本卡未解；建议与 W4 端口门调参 / 契约门重构单独立卡。
5. **两条 contract 主干既有红**定性为 `B14_BASE` 既有、登记不阻断：`test_pattern_matches_json_schema`（根因本次定死 = `specs/data/canvas-node.schema.json` 缺失，`08100483` 上同样缺失）与 `test_health_contract[GET /api/v1/health]`（`DeadlineExceeded`，与 T10-E 同面）。
6. **错名闭环**：排批稿的 `backend/app/core/security.py` 不存在，真名 `backend/app/security.py` —— 已由 R-B14-8 批准、手册 §一 T5 行与设计稿均已回填 ⇒ 台账只登「错名已闭环、无待回填项」。本卡开工复测：`core/security.py` → `No such file or directory`。
7. **`ruff format --check` 过渡条款用例**：本卡带存档 `LEFTHOOK_EXCLUDE=python-lint` 提交，依据 = 多重集对照 0 新增 + 行号不交集（见 §二.1）。归 D-40 / T8-G。
8. **本卡判据自曝一条**：再生 diff 面的第一版判据因 `flat()` 吞空容器而对「`{"APIKeyHeader": []}` 的方案名层」完全失明，报「0 差异」形似绿实为瞎（`dangling-count-after-20260916T194629.txt` 内），已由 `regen-diff-surface-20260916T194646.txt` 修正并加验伪锚。**教训可复用：比对 JSON 契约时，「键才是信息、值是空容器」的结构会被朴素扁平化静默丢弃。**
9. **tests/unit 目录级** diff 对 64 基线**零差集**；**pyright `app` = 0 errors / 81 warnings** 留档。
10. **门覆盖面扩到全 `security` 面并改名**（`…cover_all_per_op_refs` → `…cover_all_security_refs`），依据 = 普查实测根节点是 (b) 原口径唯一未盖的引用面；是加强不是放宽，先红数字不变（31/16）。
11. **移交（建议第十五批立卡）：契约门与 `pytest.importorskip("schemathesis")` 解耦**。现状是 schemathesis 缺席时，同文件里那条**不依赖 schemathesis** 的静态门会被一并跳过。不在本卡修的理由是范围（要动卡文禁改的既有模块级行），不是技术不可能 —— 详见「本卡未证明什么」第 12 条。
12. **移交（同上）：`$ref` 形态的 Path Item / Callback 在契约门里不可见**。本仓当前实测 Path Item 级 `$ref` = 0 所以不构成缺口；若将来换 OpenAPI 生成器或引入手工拼装的 spec，需要补 `$ref` 解析或另立门。详见「本卡未证明什么」第 11 条。
13. **观测留档：`import app.main` 会触发 LiteLLM 对公网的 model-cost-map 拉取**（本次实测为 SSL 握手超时后回落本地备份）。非本卡引入、非 7691/7687、不影响任何判据，但它说明本仓测试进程的「无网络」假设对模块级 import 段并不成立。若将来要把测试环境做成真正离线，这是一个已知外联点。
14. **⛔ round-3 未经独立复核 —— 需主 session 人审**。Codex r3 两次送审均因用量上限产出 0 字节（`codex_rc=1`），按协议 §四「再 0 字节 → 主 session 人审替代，不等配额」处置。**D-15 的合并条件在 r2 即已满足**（绑当时最终 HEAD `76a602c4`，B0/H0），r3 是主动追加的质量整改、改动面只有一个测试文件、全部为收窄主张与加强判据；但这一轮**确实没有第三方复核**，上表裁判是作者自跑的判据。逐条对照口径见 §七 round-3 小节。

---

## 六 4-B：这次改动对你意味着什么（零技术词）

把后端那套"接口说明书"里「要带内部钥匙才能用」的标注，统一成了同一个名字。

原先说明书上有 **31 处**（其中 16 处是系统管理那一块）写了个**没定义过的名字** —— 就像一份合同里反复写"详见附件三"，可附件里根本没有第三条。人看着像漏洞，自动化工具读到这儿只能放弃，没法自动生成"带钥匙"的调用代码，也没法在接口文档页面上正确点亮那个"授权"按钮。

现在这 31 处都指向同一条已经写明白的规则了。**谁能用、要带什么钥匙，这件事本身一点没变**——变的只是说明书上的写法从"指向不存在的条款"变成"指向真实存在的那一条"。

**felt-sense**：之前那种"我知道锁是好的，但合同上写得让人没法信"的别扭感没有了。接口契约终于自洽 —— 可以放心把这份说明书丢给第三方工具去读，而不用先口头解释一句"那个名字你别管，实际是另一个"。

---

## 七 Codex 复核

模型固定 `gpt-6-astra` + `model_reasoning_effort="ultra"`，`--sandbox read-only`，`codex-cli 0.153.3`。每轮存档首部按协议 §2.1 六行 blockquote（含 `.stderr` 会话头三行的行号自证；`.stderr` 本身不入库，`.gitignore:261-264` 覆盖）。

### round-1 — 绑定 `c5e30cfc5e6681076d9bac8cc37c8792545eb1c6`

存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING.md`；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING.md`。

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2。**

Codex 独立确认的部分（原文）：「独立比较指定两份 committed 快照，确认 **31 处悬空全部消失，其中 `/system/*` 16 处**，其他差异仅为生成时间戳」；`scheme_name` 在 FastAPI 0.135.3 下「未发现改变 header、fail-closed 判定或 `auto_error` 语义的路径」；⑤ 取舍成立；⑦ 两个 glob 确实不匹配 `security.py`。

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| M-1 | MEDIUM | ⓪ `_iter_security_refs` 只遍历根 + 直接 `paths`，遗漏 `webhooks` / `components.pathItems` / operation 与 components 两处 `callbacks` —— 都是合法 OpenAPI 3.1 位置（Codex 同时写明「当前快照没有这些面，因此不否定本次 31 处修复」） | **采纳并修**。门改名成 `cover_all_security_refs` 后，枚举面不全 = 名字大于主张。r2 新增 `_iter_path_item_security_refs`，覆盖四处 + `callbacks` 递归 |
| M-2 | MEDIUM | ④ 「取 schema 全程 socket 禁闭」的主张过强：模块级 `:18` 的 `from app.main import app`、`:79` 的 `from_asgi(...)` 都在禁闭外，且 `_custom_openapi` 有缓存；禁闭本身也只换 `socket.socket.connect` 一个入口 | **采纳**。r2 把该段注释改写为如实口径：只主张「断言本身不发 HTTP 请求 + 每次定向跑 W4 记账为 0」，明确不主张「整条收集路径无网络行为」 |
| L-1 | LOW | ⓪② 未筛 HTTP 方法 ⇒ Path Item 同级的 `x-*` 厂商数据若含 `security` 会被算作 per-op 引用（既造成误红，也能满足 `per_op_refs` 非空） | **采纳并修**。r2 加 `_HTTP_METHODS` 白名单；取舍（非标准方法键携真 security 会漏）写进注释 |
| L-2 | LOW | ④ 新门与模块级 `pytest.importorskip("schemathesis")` 耦合，依赖缺失时会连同新门一起跳过 | **登记不修**。卡文 §三 把断言的落点钉死在 `test_openapi_contract.py`，移到独立文件属越界。已记入「本卡未证明什么」 |
| — | 更正 | ② 「两条前置断言」实为三条，注释未同步 | **采纳**。r2 改为「三条」并列出各自守什么 |
| — | 提醒 | ③ 「一般判据还应逐对检查改名位置和值，不能只比较删增数量」 | 本卡的 `regen-diff-surface-…` 判据已是逐键集合比较（非仅数量），Codex 同段亦确认「修正版统计可以支持本次结果」。不另改 |
| — | 提醒 | ⑥ 多重集丢位置、行号不交集不能单独排除远处连带变化；存档缺两份原始 format diff | 如实接受。归因仍成立（本卡在 `security.py` 只单点插入十行，见提交 diff），但「零新增」的独立可重算性确有欠缺，记入台账 |

**r2 整改后的验伪锚** `enum-coverage-probe-final-20260916T201922.txt`：直接向 `_iter_security_refs` 喂合成 schema，**8/8 PASS** ——

- A1 `webhooks[wh].post` / A2 `components.pathItems[pi].get` / A3 operation 的 `callbacks` / A4 `components.callbacks` / A5 callbacks 再套 callbacks（递归）**全部被看见**；
- B1 Path Item 同级 `x-audit-data.security` **不计**、B2 `summary`/`parameters` 等固定字段不计；
- C1 真实快照仍是「引用总数 32 / per-op 31 / root 1 / 悬空 0」——**改枚举面不改本仓结论**。

> ⚠️ 该探针第一版（`enum-coverage-probe-20260916T201836.txt`）有 SyntaxError 却打出 `rc=0` —— 那个 rc 是**管道末端 `grep` 的 rc**，掩盖了 python 的失败（本仓已知坑：管道吃 rc）。修正版把 python 的 rc 在重定向后显式捕获为 `PYTHON_RC=`。两份都留档。

### round-2 — 整改内容与重取的裁判

r2 只改 `backend/tests/contract/test_openapi_contract.py`；`backend/app/security.py` 与 `backend/openapi.json` 自 r1 起**一字未动**（sha 全程 `925443dc…` / `9df9f7df…`，见每份存档首部）。

整改四项：① 新增 `_iter_path_item_security_refs`，把枚举面扩到 `webhooks` / `components.pathItems` / operation 与 components 两处 `callbacks`（含递归）；② 加 `_HTTP_METHODS` 白名单，Path Item 同级的 `x-*` 厂商数据不再冒充 per-op 引用；③ 加 `_as_dict`，畸形结构静默跳过而非抛 `AttributeError`；④ 注释与 docstring 按 r1 的 M-2 与「两条→三条」更正如实收窄措辞。

**r2 重取的全部裁判**

| 判据 | 存档（全文件名） | 结果 |
|---|---|---|
| 枚举面验伪锚（A 组 5 + B 组 2 + D 组 8 + C 组 1） | `enum-coverage-probe-r2c-20260916T202622.txt` | **16/16 PASS**，`PYTHON_RC=0` |
| 先红 / 对照绿 / 负控 | `r2-final-red-green-negctl-20260916T203537.txt` | 对照 `2 passed` rc=0；先红 rc=1 带 `31 处` + `/system/* 16 处` + `APIKeyHeader`；负控 `2 failed` rc=1；跑前跑后三文件 sha 逐字同 |
| contract 三文件 | `contract-3files-close-r2-20260916T202245.txt` | `2 failed, 75 passed in 305.13s`，`blocked=19/advisory=0/unaccounted=0` |
| tests/unit 目录级 | `unit-close-r2-20260916T202245.txt` + `close-r2.nodeids` | `35 failed … 29 errors`；对 64 基线 **diff 空**（`diff_rc=0`，`>` 行 0） |
| ruff / pyright / 收集面 | `r2-final-ruff-pyright-20260916T203640.txt` | `All checks passed!` rc=0；F821 锚 rc=1；`0 errors, 81 warnings`；`91 tests collected` |

> **关于上面两条长跑的适用性（如实）**：`contract-3files-close-r2-…` 与 `unit-close-r2-…` 跑在 `test_openapi_contract.py` 的上一版（sha `9765a69a…`）上，之后该文件又做了 ③ 的 `_as_dict` 加固（现 sha `7bbe7d73…`）。两者结论**不受影响且无需重跑**，理由是可核的命令面而非推测：contract 那条命令**逐个点名**了三个文件、其中不含 `test_openapi_contract.py`；`tests/unit` 只收集 `tests/unit` 目录。pytest 不会收集未被点名的路径，故该文件任何内容都不进这两次运行。（真正随该文件变的三条判据 —— 枚举锚、先红/负控、收集面 —— 都已在加固后重取，见上表。）

**r2 逐条被取代的存档（留痕，不作依据）**

| 被取代 | 为什么 |
|---|---|
| `enum-coverage-probe-20260916T201836.txt` | 探针有 SyntaxError，而档内 `rc=0` 是**管道末端 grep 的 rc**（管道吃 rc），掩盖了 python 失败 |
| `enum-coverage-probe-20260916T201849.txt` | 语法修好、8/8 通过，但位置串未分层（`POST GET /x callbacks[…]` 读着像笔误） |
| `enum-coverage-probe-final-20260916T201922.txt` | 位置串已分层、8/8，但尚无 D 组畸形结构用例 |
| `enum-coverage-probe-r2b-20260916T202522.txt` | **D3 实测 FAIL** —— 抓到 `callbacks` **容器本身**非 dict 时仍抛 `AttributeError`（③ 的由来）。这一份是有价值的红，特意留档 |
| `r2-red-green-negctl-20260916T201958.txt` | **变异基准写错**：用了 `git show HEAD:<path>`，而本卡改动已 commit ⇒ 写回等于没变异，门照常绿 = 假的「先红」。抓到它的是档内 sha 自证行（变异态 sha 仍是 `925443dc…` 而非改前的 `8c8c9098…`）。已改用前提 commit `2287e258` 为基准 |
| `r2-red-green-negctl-fixed-20260916T202118.txt` | 基准已改对、三阶段正确，但跑在 `_as_dict` 加固前的版本上 |
| `r2-ruff-pyright-20260916T202258.txt` | 同上，加固前版本 |

**r2 送审**：prompt `_bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r2.md`，存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING-r2.md`。

> ⚠️ **r2 发过两次，第一次由本车道主动中止（不计轮次，无存档产出）**：首版 prompt 写于 `_as_dict` 加固**之前**，其 ② 自述漏了该项、引用的也是随后被取代的存档。拿陈旧自述去审当前代码会白费一轮，故用 TaskStop 停掉并改写 prompt（补 ③ 加固的来龙去脉、改引承重存档、新增一问 ⑥）后重发。被停的那次**未产出任何存档文件**，按协议 §2.1「缺字段不计配额」的同理不计轮次。

**r2 结果：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 4**，绑定 `76a602c436e25e55c44c690098a4b55ed1f99cfd`（= r2 commit，最终 HEAD）。Codex 独立复算了三个提交文件的 SHA 并确认「r1→r2 确实只改测试文件」，且判定 **⑤ 本轮无需重新生成生产源或快照，推断成立**。

⇒ **按 D-15，本卡的合并条件在 r2 即已满足**（绑最终 HEAD 的一轮 B=0 / H=0）。下面 r3 是车道**主动**追加的质量整改，不是被 HIGH 逼出来的。

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| M-1 | MEDIUM | ⓪ 「全部合法位置」仍过强：`$ref` 不解析 ⇒ Path Item / Callback 的引用目标可落在遍历清单之外（例如根上的 `x-` 扩展、外部文档），那种形状的悬空看不见 | **采纳（收窄主张 + 补实测依据）**。docstring 改为「全部**内联**位置」，并写明 `$ref` 不解析是**已知边界**；同时补一条本仓实测：全文 `$ref` 736 处（`components` 212 / `paths` 524），但 **Path Item 级 `$ref`（`$.paths.<path>.$ref`）= 0** ⇒ 对本仓不构成缺口，换生成器就是真缺口。证据 `ref-distribution-census-20260916T204712.txt` |
| M-2 | MEDIUM | ② 16/16 验伪锚只有 PASS 标签，没有合成输入、断言原文与 `run_no_raise` 实现 ⇒ 无法独立判断 B 组比的是完整结果还是「某个名字没出现」，也指认不出哪条恒真 | **采纳并重写探针**。新版每条用例打印**合成输入 / 实际完整产出 / 精确期望集合**，断言一律是**集合相等**；生成器用 `list()` 消费；每条标注 `能区分加固 = True/False`；存档**逐字收录探针全文** |
| L-1 | LOW | ① `x-*` 误计只修了 Path Item 层：Paths Object 与 Callback Object **容器层**的 `x-*` 仍会被当 Path Item（`paths["x-audit-data"]`） | **采纳并修**。新增 `_named_entries()`，在 `paths` / `webhooks` / `components.pathItems` / `components.callbacks` / callback 名与表达式**五个容器层**统一跳过 `x-*` |
| L-2 | LOW | ④ 「必须留在同文件所以不能修」不充分 —— 也可以把 schemathesis 的可选导入与 schema 初始化限制在依赖可用的分支，静态门独立定义 | **采纳意见、维持不修，但更正理由**。见下方「理由更正」 |
| L-3 | LOW | ⑥ 两条长跑的复用理由把「未收集」推成了「任何内容都不进运行」—— conftest / `pytest_plugins` / `-p` / 自动加载插件都可能加载未被收集的模块 | **采纳，且直接消除争点**：r3 在最终 sha 上**重跑**了这两条长跑，不再依赖「可复用」的推断 |
| L-4 | LOW | ③ 「每次定向跑均为零」超出承重档可确认的范围：最终红绿档只在对照阶段留了 W4 零记账行，红阶段与负控阶段没有 | **采纳并修**。r3 的红绿档**逐阶段**打印 W4 行 |
| — | 更正 | ① 「同一 operation 可能以两个位置串各记一次」的解释不准确（引用处被跳过，只有组件定义处产出） | **采纳**，docstring 已按此改写 |
| — | 提醒 | ① `.lower()` 接受 `GET`/`Get` 属宽松容错；OpenAPI 固定字段区分大小写，大写用例不能证明标准 operation 覆盖 | 接受。新探针把该用例标为 `能区分加固 = False` 并注明它只说明「本门不因大小写漏掉」 |

**L-2 的理由更正（Codex 说得对）**：原写法「卡文把落点钉死在该文件 ⇒ 技术上只能迁移文件」是**不成立**的。技术上确有不迁文件的做法（把 `pytest.importorskip("schemathesis")`、`from_asgi` 初始化与 `@schema.parametrize()` 收进「依赖可用」分支，静态门独立定义在分支外）。不做的真实理由是**范围**：那要改动 `:17`–`:19` 与 `:78`–`:85` 这些**既有模块级行**，而卡文 §三 明写「既有 schemathesis 测试一行不动」。这是范围决策，不是技术不可能 —— 已按此更正措辞，并留作移交项。

### round-3 — 主动追加的质量整改与重取的裁判

r3 同样只改 `backend/tests/contract/test_openapi_contract.py` 与文档；`backend/app/security.py`、`backend/openapi.json` 自 r1 起 sha 全程 `925443dc…` / `9df9f7df…` 未变（Codex r2 已独立复算确认）。

**改动三项 + 两处措辞**：① 新增 `_named_entries()`，在 `paths` / `webhooks` / `components.pathItems` / `components.callbacks` / callback 名层 / callback 表达式层**六个容器层**统一跳过 `x-*` 扩展键（r2 LOW-1）；② docstring 把覆盖面主张从「全部合法位置」收窄为「全部**内联**位置」，并把 `$ref` 不解析写成**已知边界** + 本仓实测依据（r2 MEDIUM-1）；③ 重写验伪锚探针使其可独立复核（r2 MEDIUM-2）。另：红绿档逐阶段打 W4 行（r2 LOW-4）、两条长跑在最终 sha 上重跑（r2 LOW-3）。

| 判据 | 存档（全文件名） | 结果 |
|---|---|---|
| 枚举面对抗输入台（A5 + B6 + C6 + D2 + E1 = 20 条） | `enum-coverage-probe-r3-20260916T232823.txt`（21931 B，**末尾逐字收录探针全文**） | **20/20 PASS**，`PYTHON_RC=0`；分类由脚本自算并带自洽断言：**能区分本卡加固 15 / 覆盖性 4 / 回归锁 1 = 20** |
| 先红 / 对照绿 / 负控（**逐阶段** W4 行） | `r3-red-green-negctl-20260916T232904.txt` | 阶段 0 `2 passed` rc=0；阶段 1 rc=1 带 `31 处` + `/system/* 16 处` + `APIKeyHeader`；阶段 2 `2 failed` rc=1；**三阶段 W4 均为 `blocked=0/advisory=0/unaccounted=0`**；跑前跑后三文件 sha 逐字同 |
| `$ref` 分布实测（M-1 收窄的依据） | `ref-distribution-census-20260916T204712.txt` | `$ref` 736（`components` 212 / `paths` 524）；**Path Item 级 `$ref` = 0**；无 `webhooks`；`components` 只有 `schemas`/`securitySchemes`；`callbacks` 子树 `$ref` = 0；`paths` 下 `x-*` 键 = 0 |
| contract 三文件（**最终 sha 上重跑**） | `contract-3files-close-r3-20260916T232959.txt` | `2 failed, 75 passed in 218.40s`，`blocked=19/advisory=0/unaccounted=0` |
| tests/unit 目录级（**最终 sha 上重跑**） | `unit-close-r3-20260916T232959.txt` + `close-r3.nodeids` | `35 failed … 29 errors`；对 64 基线 **diff 空**（`diff_rc=0`，`>` 行 0，close-r3 = 64 条） |
| ruff / F821 锚 / pyright | `r3-ruff-pyright-20260916T233009.txt` | `All checks passed!` rc=0；锚 rc=1；`0 errors, 81 warnings` |
| **收尾 docstring 尾巴的等价证明** | `r3-docstring-ast-equivalence-20260916T234342.txt` | 见下 |

> **收尾的一行 docstring 改动与它的等价证明（D-32 口径）**：上表全部裁判跑在 `test_openapi_contract.py` sha `ae32c3c7…` 上；之后为口径一致，又把 `_iter_security_refs` docstring 首句的「每一处」改成「每一处**内联**」。该档证明这是纯文案：**去掉全部 docstring 后两版 AST 逐字相同**（`True`），**验伪锚**（把一处真代码 `x-` → `y-`）在同一比对下给出 `False`（= 该比对确实看得见代码改动）；并补上最关键的一环 —— **重建的「旧版」sha256 实测 = `ae32c3c7…` = 上表裁判所绑的那个**，所以 AST 等价证的不是两个我自己编的版本。⇒ 上表裁判对当前文件仍然绑得住。

**r3 被取代的中间档（留痕，不作依据）**：`enum-coverage-probe-r3-20260916T204806.txt` —— 新探针的首跑，`PYTHON_RC=1`，A5 用例的多层花括号没配平（`SyntaxError: closing parenthesis ')' does not match opening parenthesis '{'`）。**同一处栽了两次**（r2 的 `enum-coverage-probe-20260916T201836.txt` 也是它），第二次起改为逐层显式变量构建，并在脚本里留了注释说明原因。该档的 `PYTHON_RC=1` 是**显式捕获**的 python rc，不再是管道末端 grep 的 rc —— 这正是它能被当场看出来失败的原因。

### round-3 送审 —— ⛔ 未能完成，按协议交主 session 人审

prompt 已写好并绑定 r3 commit：`_bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r3.md`（五分节，四个禁用措辞各 0，绑 `9861c59598ca350ca7df10921744292b0deffb41`）。

**两次发送均失败**，记录 `codex-r3-quota-failure-20260916T235911.txt`：两次都是 `codex_rc=1`、产出 `.md` **0 字节**，stderr 逐字为 `ERROR: You've hit your usage limit.`；会话头自证 `.stderr:2/:5/:9` 为 `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（即模型与 effort 都对，是配额不是配置问题）。

**第三次：跨时段独立复测 + 排除替代解释**，记录 `codex-r3-quota-recheck-20260917T001432.txt`。按本仓教训「外部服务报的重置时间是**一次观测**不是不变量」（R-05），没有继承 23:58 那两次的结论，而是在约 15 分钟后用一个极小 prompt 重探：

- `probe_rc=1`，最终仍落在 `usage limit`；过程中先出现数分钟 `ERROR: Reconnecting... waiting for network` 循环（stderr 持续写入 = 活着但不推进，本仓已知形态）。
- **排除「网络问题」这一替代解释**：同一时刻 `curl` 实测 `chatgpt.com` http=403 / 1.29s、`raw.githubusercontent.com` http=301 / 1.19s —— 网络秒级响应。⇒ `Reconnecting` 是 codex 侧重试噪声，根因是配额。
- **旁证（非本卡因素）**：该时刻本机 **39 个 codex 进程** —— 本批 10 条车道并发共用同一账号配额。同批 T7-C 也撞上同一堵墙。

⇒ 三次独立观测一致，且第三次带网络对照。本车道做到「1 次重发 + 1 次跨时段复测 + 1 条替代解释排除」，超出协议要求的最低限度；**仍不据 `Sep 19th` 那个时刻做任何推断**（它同样只是一次观测）。

按协议 §四「**0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额**」：**本卡 r3 不再重试，交主 session 人审。**

> 那条 0 字节产物已从复核存档命名空间移出并改名为 `evidence-sec-dangling/codex-r3-EMPTY-quota-failed-no-review.md`，且写入了「本文件不是复核意见」的说明行 —— 避免主 session 的 D-15 存档扫描把它当成一轮复核（本树 guard hook 禁 `rm`，故用改名 + 标注代替删除）。
>
> ⚠️ 错误里那个「Sep 19th, 2026 8:16 PM」的重置时刻**不作为结论继承**：本仓已有教训（第十四批「配额耗尽至 09-15」的批级通告被 24 分钟后的实测推翻并撤回，R-05）—— 外部服务报的重置时间是一次观测，不是不变量。接手者若要重试，先实测。

**交给主 session 人审时请对照这三点**（它们决定 r3 的风险面有多窄）：

1. **D-15 的合并条件在 r2 即已满足** —— r2 绑当时的最终 HEAD `76a602c4`，**BLOCKER 0 / HIGH 0**，且 Codex 在该轮独立复算了三个文件 SHA、确认「r1→r2 只改测试文件」、并判定「本轮无需重新生成生产源或快照，推断成立」。
2. **r3 相对 r2 的改动面**：`git diff 76a602c4 9861c595 -- . ':(exclude)_bmad-output'` **只有 `backend/tests/contract/test_openapi_contract.py` 一个文件**。生产源 `backend/app/security.py` 与快照 `backend/openapi.json` 自 r1 起 sha 全程 `925443dc…` / `9df9f7df…` **未变**（每份 r3 存档首部都带这两个 sha，可逐档核）。⇒ **r3 不可能动摇 r1/r2 已成立的生产语义结论**。
3. **r3 的全部改动都是「收窄主张 + 加强判据」，没有一项放宽**：主张从「全部合法位置」收窄为「全部内联位置」；枚举面多跳过六个容器层的 `x-*`；验伪锚从 8 条扩到 20 条且改为集合相等断言、逐条打印输入与期望、存档收录脚本全文；红绿档多打两条 W4 行；两条长跑在最终 sha 上重跑。全部裁判见上表，**无一项由绿转红**。

**考虑过但未采用的另一条路（决策留痕）**：同批 T7-C 遇到同一配额墙时用的解法是「把代码树回审版化，使 `git diff <审SHA> HEAD` 为空」，从而让上一轮复核绑住最终 HEAD。本卡**不取**该解法，理由是它在这里会产生相反的效果：r3 改的每一项**都是 Codex r2 自己提出、且被采纳的意见**（`x-*` 容器层误计、docstring 主张过强、验伪锚不可独立复核、W4 记账缺两阶段、长跑复用理由过强）。把树回退到 r2 版 = 让 r2 的复核绑住一份**仍带着它自己刚指出的那些缺陷**的代码。⇒ 宁可保留改进、如实标注「该轮未复核」交主 session 裁，也不为了让流程好看而把已确认的缺陷改回去。

**未证明（如实）**：r3 这一轮**没有**独立复核。按协议 §1「不入库的复核不作依据」，本车道不以任何未落盘的自查充当该轮复核；上表裁判是**作者自跑的判据**，不是第三方复核。

### ⛳ 一步闭环用的交接（给主 session / 配额恢复后接手的人）

卡文 (k) 的终点是「绑**最终 HEAD** 的一轮 BLOCKER/HIGH = 0」。当前差的就是这一轮。prompt 已在盘上且已绑最终 HEAD，**原样重发即可**，无需重写：

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r3.md)" \
  > _bmad-output/审查/codex-review-CARD-SEC-DANGLING-r3.md \
  2> _bmad-output/审查/codex-review-CARD-SEC-DANGLING-r3.stderr </dev/null
echo "codex_rc=$?"; wc -c _bmad-output/审查/codex-review-CARD-SEC-DANGLING-r3.md
```

**发之前先核这一条**（prompt 里写死的 `__REVIEW_SHA__` 已替换为 `9861c595…`，若此后又有代码 commit 就不再绑最终 HEAD）：

```bash
git --no-pager diff --stat --no-color 9861c59598ca350ca7df10921744292b0deffb41 HEAD -- . ':(exclude)_bmad-output'
# 期望：空。非空 ⇒ 先把 prompt 里的两个 SHA 换成新的最终 HEAD 再发。
```

**三种结果的处置**：

| 结果 | 处置 |
|---|---|
| 存档非 0 字节且 **BLOCKER 0 / HIGH 0** | 补协议 §2.1 六行首部（会话头自证抄 `.stderr` 的 `:2`/`:5`/`:9` 三行并括注行号，与 r1/r2 两份同形），卡文 (k) 即闭合；本卡轮次 = 3，未触 5 轮上限 |
| 存档非 0 字节但有 HIGH | 按 D-15「审后改代码必再送一轮」处理；注意本卡已用 3 轮，剩 2 轮 |
| 仍 0 字节 | 维持本节的人审路径；**不要**为了让流程好看而把 r3 的代码回退成 r2 版（理由见上方「考虑过但未采用的另一条路」） |

**人审时的最小核对面**（若走人审而非重发）：`git diff 76a602c4 <最终 HEAD> -- . ':(exclude)_bmad-output'` 只有一个测试文件；配套判据见上方 round-3 表的六份存档；三条交接要点见上方「交给主 session 人审时请对照这三点」。

## 八 提交

- **代码 commit**：`c5e30cfc5e6681076d9bac8cc37c8792545eb1c6`
  `fix(security): 31 处悬空 APIKeyHeader→InternalApiKey [BATCH-2026-09-11-第十四批 / CARD-SEC-DANGLING]`（header 94 字符 ≤100，含批次标记与卡号；body 无 >100 字符行）
  带存档 `LEFTHOOK_EXCLUDE=python-lint`（理由见 §二.1）；⛔ 未用 `LEFTHOOK_EXCLUDE=python-typecheck`；`*.stderr*` 未入库（精确判据实测 0，验伪锚 21 份工作树 `.stderr` 全部被 `git check-ignore` 确认忽略）。
- **地盘门（commit 范围口径）** `territory-postcommit-20260916T200439.txt`：改动文件恰为 `backend/app/security.py` + `backend/openapi.json` + `backend/tests/contract/test_openapi_contract.py`；`main.py` / `system.py` / 两个 conftest / 三个只读 contract 文件 diff 行数**各为 0**；`canvas-vault` 改动 0 行。
  验伪锚（去掉 `':(exclude)_bmad-output'` 后应多出 `_bmad-output/` 路径）= **29**。
  > ⚠️ 该锚第一次读到 **0** 是假阴性：git 对非 ASCII 路径做 C 引号化（`"_bmad-output/\345\256\241…"`），行首锚 `^_bmad-output/` 恒不命中。加 `-c core.quotepath=false` 后读到 29。两个读数同档并列，便于复核者看出这条坑。
- **r2 commit**：`76a602c436e25e55c44c690098a4b55ed1f99cfd` —— `fix(contract): 按 Codex r1 收 2 MEDIUM+1 LOW 扩枚举面 [BATCH-2026-09-11-第十四批 / CARD-SEC-DANGLING]`（91 字符）
- **r3 commit**：`9861c59598ca350ca7df10921744292b0deffb41` —— `fix(contract): 按 Codex r2 收 2 MEDIUM+4 LOW 收窄主张 [BATCH-2026-09-11-第十四批 / CARD-SEC-DANGLING]`（91 字符）
- **文档尾 commit**：见 git log（只动 `_bmad-output`）。
- 三个代码相关 commit 各自 header ≤100 且含批次标记与卡号，body 无 >100 字符行；均带存档 `LEFTHOOK_EXCLUDE=python-lint`，⛔ 均未用 `LEFTHOOK_EXCLUDE=python-typecheck`。
- **squash 提示给主 session**：本卡是**多 commit**（`c5e30cfc` 代码 → `76a602c4` r1 整改 → `9861c595` r2 整改 → 文档尾），按协议 §4「单卡多 commit 用 `cherry-pick --no-commit <range>`」处理。
- **不 push**（按卡文 (l)）。
