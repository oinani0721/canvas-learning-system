# 独立审查请求 — CARD-HYGIENE-openapi（schemathesis 合约测试排除写端点）

## 一 背景与最小读取面

本仓是 Canvas Learning System（FastAPI 后端 + schemathesis 4.14.3 合约测试）。
本卡只做两件事：

1. 把**全部写方法**（POST/PUT/PATCH/DELETE）排除出 schemathesis 的生成面
   （`test_openapi_contract.py` 的 `.include(method_regex=r"^(GET|HEAD)$")`），
   并追加排除 1 条直接写盘的只读端点；
2. 新增 `backend/tests/contract/conftest.py` 的 autouse 零写门，
   在合约测试跑前/跑后各查一次 `backend/` 顶层是否出现 vault 骨架。

动因：`POST /api/v1/system/setup-wizard` 会按请求体 `vault_path` 建整套 vault 骨架，
从 `backend/` 起跑的合约测试因此在代码目录里留下 `raw/ wiki/ outputs/ CLAUDE.md`。

**请只读下面这些，不要扩大读取面**：

- `git diff ce1e085b <AUDIT_SHA> -- . ':(exclude)_bmad-output'`
- `backend/tests/contract/test_openapi_contract.py`（全文）
- `backend/tests/contract/conftest.py`（全文）
- `_bmad-output/审查/evidence-hyg-openapi/collect-before.txt`
- `_bmad-output/审查/evidence-hyg-openapi/collect-after.txt`
- `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
- `_bmad-output/审查/evidence-hyg-openapi/get-handler-write-primitive-scan-*.txt`
- `backend/app/api/v1/system.py` 的 430-476 行
- `backend/app/services/vault_init_service.py` 的 18-23 行与 93-104 行

不要读 `.env` 或任何含凭据的文件。

## 二 作者自述（请独立核对，不要采信）

1. **收窄面 = 全部写方法 + 1 条只读例外**。实测数字：改前收集 `test_api_contract[...]`
   共 **206** 条，其中 GET/HEAD **93** 条（HEAD 面为 0）；改后 **92** 条；
   差集 `excluded-operations.txt` **114** 条（POST 96 / DELETE 9 / PUT 6 / PATCH 2 / GET 1）。
   对账 `206 == 92 + 114` 成立；点名的只读 nodeid `test_api_contract[GET /]` 改后仍在。
2. **GET 面写原语复核**：对 `backend/app` 全树 `<任意名>.get(...)` 装饰的 handler 做 AST 扫描，
   命中 **93** 个（与收集到的 GET 数逐一对齐，用以自证扫描面没被划窄），
   正则 `mkdir|write_text|write_bytes|os.replace|save_state|add_documents|drop_table|append_event|subprocess`
   命中 **1** 条：`app/api/v1/endpoints/health.py:1139` 的 `check_lancedb_health`
   （`lancedb_path` 默认值是相对路径 `./data/lancedb`，随后 `mkdir`），已追加 `path_regex` 排除。
   **该扫描只覆盖 handler 函数体一层文本，handler → service → 写盘的间接路径未覆盖。**
3. **fixture 自身零写**：只做 `Path.exists()` 与 `os.stat()`，不 touch、不 mkdir；
   跑前命中即 fail（归因不清拒绝开跑），跑后命中即 fail 并列出 mtime。
4. **负控只用 `--collect-only`**：改前态的真跑只在一次性 scratch worktree 里做过一次
   （跑完即 `worktree remove --force`），车道树与任何长期树上不真跑写端点。

## 三 请按重要性排序回答的问题

1. `.include(method_regex=r"^(GET|HEAD)$")` 与 `.exclude(path_regex=...)` 的组合，
   是否把**本应保留的只读 operation** 也排掉了？`excluded-operations.txt` 的 114 条里，
   有没有哪一条其实是只读语义（例如以 POST 形态实现的纯查询）而不该被排除？
2. 剩余的 92 条 GET 里，有没有**间接写**——handler 本身没有写原语，但调用的 service 层
   会写盘、或触发 LanceDB 的自愈式重建？请指出具体的 file:line。
3. `conftest.py` 里 `_BACKEND_ROOT = Path(__file__).resolve().parents[2]` 的推导，
   在从仓根起跑、从 `backend/` 起跑、或经 symlink 起跑时，是否都仍指向同一个 `backend/`？
4. 零写判据排除了 `.venv/`、`.hypothesis/`、`__pycache__/` 三类路径。
   这三条排除是否掩盖了别的写面（例如某个端点恰好写进这些目录）？
5. 根 `pyproject.toml` 的 `[tool.schemathesis]` 历史配置块（`schema_path` / `max_examples` /
   `hypothesis_deadline` / `stateful` / `checks`）对 schemathesis 4.14.3 的实际影响是什么？
   它会不会与文件里的 `@settings(max_examples=10, ...)` 冲突或互相覆盖？

## 四 输出格式

对每个发现给出：

- 等级：BLOCKER / HIGH / MEDIUM / LOW
- 位置：`file:line`
- 一句话说明：在什么条件下这个问题会真的发生

按等级从高到低排列。没有发现就明确写「本节无」。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库或外部服务。
- 不评价 `system.py` 的 `vault_path` 校验设计本身（归另一张卡），
  也不评价是否应把合约测试接入 CI（已有独立裁决）。
- 不评价 `_bmad-output/` 下的文档写法。
