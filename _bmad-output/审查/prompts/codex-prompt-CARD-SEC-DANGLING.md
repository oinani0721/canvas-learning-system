# 独立复核请求 — CARD-SEC-DANGLING（第十四批 T5-D）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`（分支 `card/t5-bugs`）。
本卡把 OpenAPI 契约里 31 处 per-operation `security` 的悬空方案名 `APIKeyHeader` 统一成已声明的 `InternalApiKey`，并新增一条进程内契约断言、再生 committed 快照。

**请只读下面这些面，不要跑测试、不要跑 hook、不要连任何数据库：**

1. 本卡全部代码改动：`git diff 2287e2583c54472d238e8b8eec87bb1e9e95c9e8 c5e30cfc5e6681076d9bac8cc37c8792545eb1c6 -- . ':(exclude)_bmad-output'`
2. `backend/app/security.py:40-80`（`APIKeyHeader` 定义与本卡改动）
3. `backend/app/main.py:538-572`（`_custom_openapi`：`get_openapi` → 覆盖 `securitySchemes` → 写全局 `security`）
4. `backend/app/api/v1/system.py:28-40`（router 级 `Depends(require_internal_api_key)`，/system/* 16 处的来源）
5. 新增断言全文：`backend/tests/contract/test_openapi_contract.py` 末尾 `Security scheme 悬空引用门` 整段（注释块 + `_load_drift_module_for_security` + `_iter_security_refs` + `test_security_schemes_cover_all_security_refs`）
6. `backend/tests/contract/test_openapi_snapshot_drift.py`（既有快照漂移门，本卡只跑不改）
7. `scripts/spec-tools/check-openapi-drift.py` 的 `socket_connect_lockdown()` / `load_live_schema()` / `write_snapshot()` 段
8. 证据目录 `_bmad-output/审查/evidence-sec-dangling/`（全部 `.txt`），验收单 `_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md`

## ② 作者自述（请独立核对，不要采信）

- **根因链**：`security.py` 的 `APIKeyHeader(...)` 原先不传 `scheme_name=`，FastAPI 按类名把方案命名为 `APIKeyHeader` 并写进每个 operation 的 `security`；而 `main.py:_custom_openapi` 在 `:554` 把 `components.securitySchemes` **整体覆盖**成只含 `InternalApiKey` ⇒ 31 处 per-op 引用在 securitySchemes 里无定义。
- **修法（方案 A）**：只在 `security.py` 的 `APIKeyHeader(...)` 调用里加 `scheme_name="InternalApiKey"`（一个 keyword + 一段注释），**不碰 `main.py`**。
- **运行时鉴权未变**：`APIKeyHeader.__call__` 只读 `self.model.name`；作者用 AST 逐节点比对证明 `require_internal_api_key` / `verify_websocket_internal_key` 两个函数体 AST 完全相同，唯一 AST 差异是那一个 keyword（剔除它后与改前 AST 逐字相同）。运行时实测 `model.name='X-CLS-Internal-Key'`、`auto_error=False` 均未变。
- **覆盖面**：作者普查了 schema 里每一个 `security` 键，得 31 per-op + 1 全局共 32 处，无 `webhooks`/`callbacks`/`pathItems`；WebSocket 路由不产出 OpenAPI operation。新断言两处都覆盖。
- **快照再生**：用 `check-openapi-drift.py --write`（socket 禁闭、不起 lifespan）。作者逐叶子比对再生前后，得「31 个 `…>security[i]>APIKeyHeader` 消失 / 31 个 `…>security[i]>InternalApiKey` 出现 / 两侧无任何未被这两式解释的键 / 唯一值变动是易变键 `info.x-generated-at`」。
- **先红后绿**：断言在改源前必红（31 / /system/* 16 / `APIKeyHeader`），改源+再生后转绿；负控（把 `security.py` 还原成改前版）使其复红，跑前跑后 `shasum -a 256` 逐字相同。
- **pyright** `app` = 0 errors / 81 warnings（与 B14_BASE 同）。

## ③ 请按重要性排序回答的问题

- **⓪** 方案 A 是否真把 31 处（含 /system/* 16 处）全部解悬空？新断言 `_iter_security_refs` 的枚举面是否有遗漏 —— 是否存在它看不见、但 OpenAPI 规范允许出现 `security` 的位置（例如 `components` 下的 pathItems、callbacks、webhooks，或非标准 operation 键）？如果有，那是**门未覆盖的路径**，请点名。
- **①** `scheme_name` 在本机 fastapi 版本（0.135.3）下是否确实只影响 OpenAPI 命名？有没有任何路径让它改变运行时行为（header 名、fail-closed 判定、`auto_error` 语义）？
- **②** 新断言的两条防 vacuous-pass 前置断言是否够？有没有**对照输入**（例如 securitySchemes 非空但 per-op 全空、或 `security: []` 空列表）会让这条门在真有缺陷时仍然绿？
- **③** 再生 `backend/openapi.json` 是否把与安全无关的既有漂移一并扫入？作者的「逐叶子比对」判据本身是否可靠 —— 特别是它对**空容器**（`{"APIKeyHeader": []}` 的空列表）的处理是否正确？（作者第一版判据在这里出过错并已修，见 `evidence-sec-dangling/regen-diff-surface-*.txt` 首部说明。）
- **④** 新断言取 schema 的路径（复用 `load_live_schema()`）是否真的不连库、是否与 committed 快照同源？注意该测试文件在模块层还有一个**不在 socket 禁闭内**的 `from app.main import app`（既有代码，非本卡新增）—— 这是否构成**未被拦下的输入**？
- **⑤** 作者不以全量 schemathesis 门的 before/after 作为「悬空已解」的证据（理由：W4 端口门下每 op 真实请求 16–19s 超过 `deadline=10000`，恒 `DeadlineExceeded`，该门对「方案名是否被声明」这条纯静态性质不产生信号）。这个取舍是否成立？
- **⑥** `security.py` 的 `ruff format --check` 为红。作者主张这是主干既有漂移（协议 §2.3 的 462 文件条款），并给了多重集对照（改前改后漂移内容行多重集相同，0 新增）与行号不交集两条判据。这两条判据是否足以支撑「本卡零新增格式漂移」？
- **⑦** 作者发现 lefthook 的 `spec-sync-flat` / `spec-sync-root` 两个 glob 都不覆盖 `backend/app/security.py`，因此改它不会触发快照自动再生。这个结论是否成立？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句**复核思路**（说明你会怎样独立确认这条，用中性说法）。没有问题的级别请显式写 0 条。

## ⑤ 边界

- 只读；不跑测试、不跑 lefthook、不连 7691/7687/7692、不写任何文件。
- 不评运行时 403/503 行为门（归本批 T10-E `CARD-RED-HYGIENE`），不评 `system.py` 的端点语义（本卡不编辑该文件）。
- 不评 `main.py:386-404` 段（那是本批 T6-B 的地盘）。
- 不评 `_bmad-output` 下的批次流程文档本身，只把它们当证据读。
