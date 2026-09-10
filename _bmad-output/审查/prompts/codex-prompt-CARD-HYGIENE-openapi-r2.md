# 独立审查请求（round-2） — CARD-HYGIENE-openapi（schemathesis 合约测试排除写端点）

## 一 背景与最小读取面

本仓是 Canvas Learning System（FastAPI 后端 + schemathesis 4.14.3 合约测试）。本卡两件事：

1. 把**全部写方法**（POST/PUT/PATCH/DELETE）排除出 schemathesis 生成面
   （`.include(method_regex=r"^(GET|HEAD)$")`），并追加排除 1 条会写盘的只读端点
   （`.exclude(path_regex=r"^/api/v1/health/lancedb$")`）；
2. 新增 `backend/tests/contract/conftest.py` 的 autouse 零写门。

**round-1 已完成的整改**：round-1 提出 1 条 LOW —— 文件注释里的覆盖面数字写成
「保留 93 / 排除 113」，那是追加排除 lancedb **之前**的值。已改为实测的 **92 / 114**
（commit `dddfc598`，纯注释修改；`collect-only` 结果与整改前逐行相同，行为未变）。

**round-1 的三点回应**（请据此复核，不必重复 round-1 已确认的部分）：

- 你在 round-1 问题 4 指出「conftest 并没有三条排除规则」—— **你是对的，是我问题问错了**。
  `.venv/` `.hypothesis/` `__pycache__/` 三条排除属于**验收判据里的 `find -newer` 命令**，
  不是 fixture 的逻辑。本轮问题 4 已按实际改写。
- 问题 2（间接写）与问题 5（历史配置块）你判为「读取面不足，未验证」。
  本轮**已把你需要的文件加进读取面**。

**请只读下面这些**：

- `git diff ce1e085b dddfc598 -- . ':(exclude)_bmad-output'`
- `backend/tests/contract/test_openapi_contract.py`（全文）
- `backend/tests/contract/conftest.py`（全文）
- `_bmad-output/审查/evidence-hyg-openapi/collect-before.txt`
- `_bmad-output/审查/evidence-hyg-openapi/collect-after.txt`
- `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
- `_bmad-output/审查/evidence-hyg-openapi/get-handler-write-primitive-scan-20260909T161754.txt`
- `_bmad-output/审查/evidence-hyg-openapi/zero-write-verdict-20260909T162042.txt`
- `_bmad-output/审查/evidence-hyg-openapi/find-newer-attribution-20260909T211708.txt`
- **`backend/app/api/v1/endpoints/health.py`（为问题 2 新增：GET handler 最密集的文件）**
- **`backend/app/api/v1/endpoints/` 下任何你为回答问题 2 需要跟进的 GET handler 与其调用的
  service（为问题 2 新增；跟到写盘点为止即可，不必通读全仓）**
- **`pyproject.toml`（为问题 5 新增：根配置，含 `[tool.ruff]` 与 `[tool.schemathesis]`）**
- **`backend/.venv/lib/python3.14/site-packages/schemathesis/` 下与配置加载相关的源码
  （为问题 5 新增）**
- `backend/app/api/v1/system.py` 的 430-476 行
- `backend/app/services/vault_init_service.py` 的 18-23 行与 93-104 行

不要读 `.env` 或任何含凭据的文件。

## 二 作者自述（请独立核对，不要采信）

1. **收窄面**：改前 206 条 `test_api_contract[...]`，其中 GET/HEAD **93**（HEAD 面为 0）；
   改后 **92**；差集 **114** 条（POST 96 / DELETE 9 / PUT 6 / PATCH 2 / GET 1）。
   对账 `206 == 92 + 114`；点名的只读 nodeid `test_api_contract[GET /]` 改后仍在。
2. **GET 面写原语扫描**：对 `backend/app` 全树 `<任意名>.get(...)` 装饰的 handler 做 AST 扫描，
   得 **93** 个（与收集到的 GET 数相等，用以自证扫描面没被划窄），
   正则命中 **1** 条：`health.py` 的 `check_lancedb_health`
   （`lancedb_path` 默认相对路径 `./data/lancedb` + `mkdir`），已追加排除。
   **该扫描只覆盖 handler 函数体一层文本，间接写未覆盖 —— 这正是问题 2 要请你查的。**
3. **零写判据实测结果（如实，其中一条未通过）**：
   - `git status --porcelain` 排除本卡两文件后 **为空** ✅
   - `backend/` 顶层五项骨架 **全不存在** ✅
   - `find backend -type f -newer <哨兵>`（排除 `.venv/` `.hypothesis/` `__pycache__/`）
     **命中 6 条，判据未通过** ❌。6 条已逐条归因：全部被 gitignore 覆盖、
     全部不在五项骨架内；其中 `.ruff_cache/...` 是作者自己跑 ruff 造成的。
     其余 5 条（`app/data/vault_index_pending__canvas_vault.jsonl`、`logs/memory-system-*.log`、
     `data/llm_call_logs.db`、`data/qa_metrics.db`、`data/fsrs_card_states.json`）
     出现在全跑期间，作者判断是 app lifespan 与运行期写入。
4. **改后全跑**：`92 failed, 1 skipped`，用时 4:55:14，`rc=1`。作者判断 GET 面契约红是存量。

## 三 请按重要性排序回答的问题

1. **（本轮重点）剩余 92 条 GET 里的间接写**：哪些 GET handler 自身没有写原语，
   但调用的 service 会写盘？请给出具体的 `file:line` 调用链。
   特别是自述 3 里那 5 个文件（`vault_index_pending__canvas_vault.jsonl`、
   `memory-system-*.log`、`llm_call_logs.db`、`qa_metrics.db`、`fsrs_card_states.json`）
   —— 它们究竟是 app 启动时一次性写的，还是某个 GET 端点在请求处理中写的？
   如果是后者，那条 GET 是否也应该像 `health/lancedb` 一样被排除？
2. **（本轮重点）`[tool.schemathesis]` 历史配置块**：它对 schemathesis 4.14.3 有实际影响吗？
   会不会与文件里的 `@settings(max_examples=10, deadline=10000, phases=[...])` 冲突或互相覆盖？
   4.x 是否还读这个配置节？
3. `.include(method_regex=r"^(GET|HEAD)$")` 与 `.exclude(path_regex=...)` 的组合，
   是否把本应保留的只读 operation 也排掉了？`excluded-operations.txt` 的 114 条里，
   有没有哪一条其实是只读语义而不该被排除？
   （round-1 你已指出「即使确属纯查询，排除也符合本卡目标」，本轮只需指出你认为**明确**是纯读、
   且排除它会造成实质覆盖损失的条目。）
4. **零写门的检测边界**：`conftest.py` 只检查 `backend/` 顶层五个名称。
   自述 3 承认 `find` 判据命中 6 条而未通过。
   在你看来，这个「五项顶层名称」的检测面，对本卡声称要防的污染（vault 骨架写进代码目录）
   是否**充分**？有没有 `VaultInitService` 会产生、但不在这五项里的产物？
5. `_BACKEND_ROOT = Path(__file__).resolve().parents[2]` 在 round-1 已确认与 cwd 无关。
   本轮只问：module-scope 的 autouse fixture，在 `tests/contract` 下有多个 test module 时，
   会各跑一次跑前/跑后检查 —— 前一个 module 留下的产物会不会被后一个 module 的
   **跑前**检查误判成「污染现场已存在」并导致连锁失败？这是想要的行为吗？

## 四 输出格式

对每个发现给出：

- 等级：BLOCKER / HIGH / MEDIUM / LOW
- 位置：`file:line`
- 一句话说明：在什么条件下这个问题会真的发生

按等级从高到低排列。没有发现就明确写「本节无」。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库或外部服务，也不要真的发起 HTTP 请求。
- 不评价 `system.py` 的 `vault_path` 校验设计本身（归另一张卡），
  也不评价是否应把合约测试接入 CI（已有独立裁决）。
- 不评价 `_bmad-output/` 下的文档写法。
- 不要求作者重跑那 4 小时 55 分的全量测试来回答问题（如需该证据，请说明理由）。
