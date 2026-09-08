# CARD-PYRIGHT-DEBT-rest — 阶段 1 ignore 清单（**28 条**，基线 da690bf8 为 0 条）

> ⚠️ **Codex r1 整改后从 25 更正为 28**：`claude_client.py` 三处从 `isinstance(block, TextBlock)` **退回 `hasattr`** 并各加一条行级 ignore（等价性证明被 Codex 推翻，见下表 #26-28 与验收单 §7-bis）。

> 判据：`grep -rn 'pyright: ignore' backend/app --include='*.py' | wc -l` = **28**；
> `git grep -c 'pyright: ignore' da690bf8 -- backend/app` = 0（全部为本卡新增）。
> 每条都是**行级**（无文件级 ignore）、带具体 rule、带一句理由。

| # | file:line | rule | 理由摘要 | 性质 | TAIL |
|---|---|---|---|---|---|
| 1 | `api/v1/endpoints/rollback.py` `from src.rollback` | reportMissingImports | `src/` 全仓不存在（`git ls-files src`=0），端点恒 503 | 死管道 | T1 |
| 2 | `api/v1/endpoints/edges.py` `neo4j.execute_query` | reportAttributeAccessIssue | **真缺陷**：`Neo4jClient` 只有 `run_query`；`except` 元组不含 `AttributeError` ⇒ 端点 500 | **真缺陷** | T-EDGES |
| 3 | `api/v1/endpoints/edges.py` `client.delete` | reportAttributeAccessIssue | `LanceDBClient` 只有 `add_documents`，`hasattr` 守卫的死分支 | 死分支 | T10 |
| 4 | `api/v1/endpoints/edges.py` `client.upsert` | reportAttributeAccessIssue | 同上 | 死分支 | T10 |
| 5 | `api/v1/endpoints/edges.py` `client.get_db()` | reportAttributeAccessIssue | 同上 | 死分支 | T10 |
| 6 | `api/v1/endpoints/metadata.py` `drop_table(..., ignore_missing=True)` | reportCallIssue | **假阳**：pyright 读抽象基类 `DBConnection`，运行期实现 `LanceDBConnection` 确有该参数（lancedb 0.30.2 `inspect.signature` 实测） | 假阳 | — |
| 7 | `mcp/tools/infra_tools.py` `json.loads(resp.body)` | reportAttributeAccessIssue | `detailed_health_check` 注解 `-> dict`，该防御分支对检查器恒不可达；保留以防端点改回 JSONResponse | 死分支 | — |
| 8-9 | `mcp/tools/infra_tools.py` `result.vault_name` / `.vault_id` | reportAttributeAccessIssue | **真缺陷**：`vault.switch_vault` 被 P0-3 隔离后恒返回 `JSONResponse`，两行运行期必 `AttributeError` 被 `except` 吞成 `success=False`（该 MCP 工具恒报失败）。**刻意不用 `cast`**——cast 会声明"它就是那个类型"，把真缺陷永久盖住 | **真缺陷** | T-SWITCHVAULT |
| 10-11 | `api/v1/endpoints/boards.py` / `mcp/tools/board_manifest_tools.py` `except pydantic.ValidationError` | reportUnusedExcept | **真死分支**：`pydantic.ValidationError` 是 `ValueError` 子类（pydantic 2.12.5 实测 MRO），已被上面的 `except ValueError` 先接走；调顺序 = 改行为 | 死分支 | T-UNREACH |
| 12 | `api/v1/endpoints/suggestions.py` `content.strip()` | reportAttributeAccessIssue, reportOptionalMemberAccess | 未传 `stream=True` ⇒ 运行期恒 `ModelResponse`；`content=None` 时原本就 `AttributeError`，本卡不改 | 假阳 + 存量 | — |
| 13-14 | `api/v1/endpoints/exam_grade.py` / `index_image.py` `.choices[0]` | reportAttributeAccessIssue | 同上（未传 stream） | 假阳 | — |
| 15-16 | `api/v1/endpoints/health.py:615` / `index.py` `return JSONResponse` | reportReturnType | FastAPI 允许路由直接返回 Response 子类；改注解会改 openapi 生成面 | 框架惯用法 | — |
| 17 | `api/v1/endpoints/health.py` `len(tables)` | reportArgumentType | lancedb 0.30.2 `table_names()` 运行期返回 `list`（实测 `__len__` 在），声明面写 `Iterable[str]` | 假阳 | — |
| 18 | `api/v1/endpoints/multimodal.py` `= ...` | reportArgumentType | FastAPI「必填 body」惯用法；换 `Body(...)` 会动 openapi 生成面 | 框架惯用法 | — |
| 19 | `api/v1/endpoints/tips.py` `tips=tips` | reportArgumentType | 元素来自 `TipItem(...).model_dump()`，pydantic 校验期还原 | 假阳 | — |
| 20 | `dependencies.py` `canvas_base_path=` | reportArgumentType | 根因是 `services/canvas_service.py` 的隐式 Optional（`str = None`）——**U1 地盘**；U1 修好后本条会被 `reportUnnecessaryTypeIgnoreComment` 自曝，阶段 2 清理 | 跨车道 | 阶段2复核 |
| 21-22 | `clients/provider_factory.py:256/:261` | reportAttributeAccessIssue | `Settings` 无 `OPENAI_API_KEY`（`config.py` grep=0）+ `extra="ignore"` ⇒ `hasattr` 恒 False、openai provider 分支恒不激活；加字段 = 运行期行为变化 | 产品裁定 | **T14** |
| 23 | `middleware/agent_metrics.py` `await func(...)` | reportGeneralTypeIssues | `R` 是 sync/async 两条包装路径共用的类型变量；运行期只有 `iscoroutinefunction(func)` 为真才返回本包装器 | 假阳 | — |
| 24 | `middleware/llm_call_logger.py` `.timestamp()` | reportAttributeAccessIssue | pyright 在 `A and B` 否定分支保留「A 真 B 假」⇒ 仍含 `int\|float`；运行期已被上一分支 return 掉 | 假阳 | — |
| 25 | `middleware/metrics.py` `MetricsMiddleware(app=None)` | reportArgumentType | 只为借用 `_normalize_endpoint` 造实例，从不挂进 ASGI 链 | 结构性 | — |
| 26-28 | `clients/claude_client.py` `response_text += block.text` ×3 | reportAttributeAccessIssue | `hasattr` 守卫无法用类型表达：`ContentBlock` 12 个成员**全部** `extra='allow'`，非 `TextBlock` 的块可携带未声明的 `text` ⇒ 只关类型、不动判断 | 保行为 | — |
| — | `clients/neo4j_client.py` `driver` | （非 ignore）| Codex r1 MEDIUM 整改：`driver = self._driver` 从闭包外移入 `_execute_with_retry` 内，恢复"每次重试重读" | **行为修正** | — |

## 非 ignore 的结构性修复（更值得看的部分）

| 文件 | 消错数 | 做法 |
|---|---|---|
| `clients/claude_client.py` | 35 → 0 | `messages` 注解 `List[MessageParam]`；`content_blocks` 收紧成 `List[ContentBlockParam]`（**不需要 cast**）。⛔ 三处 `hasattr(block,"text")` **保持不动**（#26-28 各一条行级 ignore）——曾改成 `isinstance(block, TextBlock)` 并自称"已实证等价"，Codex r1 Q8 推翻：12 个块类型 `model_config.extra` 全为 `'allow'`，`ThinkingBlock.model_validate({...,"text":"x"})` 得 `hasattr=True` / `isinstance=False` ⇒ 换 `isinstance` 会静默漏文本 |
| `api/v1/endpoints/intelligent_parallel.py` | 9 → 0 | 一处根因：`Optional["IntelligentParallelService"]` 的前向引用在模块作用域解析不了 ⇒ 退化成 `Optional[Unknown]`。改 `if TYPE_CHECKING:` 导入（运行期一行不执行，循环 import 顾虑原样保留）+ `get_service()` 返回注解 + 一处 `assert` |
| `api/v1/endpoints/rollback.py` | 6 → 0 | 五个名字标 `Any`（而不是留裸 `None` 让每个使用点各报一次）+ import 行 ignore；**端点与 503 行为一字未动**（运行期实证 `_rollback_available=False`） |
| `middleware/{error_handler,logging_middleware}.py` | 2 → 0 | `call_next: Callable[[Request], Response]` → `RequestResponseEndpoint`（原注解漏了 `Awaitable`） |
| `middleware/llm_call_logger.py` | 1 → 0 | 条件基类改 `if TYPE_CHECKING:` 分叉；**降级路径负控实测**：litellm 在 → base=`CustomLogger`，模拟缺席 → base=`object` |
| `core/exceptions.py`, `core/memory_system_logger.py` | 6 → 0 | 隐式 Optional（`str = None`）补 `Optional[...]` |
| `api/v1/endpoints/websocket.py` | 2 → 0 | `Optional[callable]` → `Optional[Callable[..., Any]]`（`callable` 是内建**函数**不是类型） |
| `core/exception_handlers.py` | 3 → 0 | starlette stub 的 handler 形参逆变过严 → `cast(ExceptionHandler, ...)`（T6） |
| `clients/neo4j_client.py` | 3 → 0 | 守卫后就地绑定 `driver`（窄化不进闭包）+ `cast(LiteralString, query)`（T8）+ 删死 `import asyncio` |
| 8 文件死 import / 2 处未用变量 | 10 → 0 | 删 import；未用变量加 `_` 前缀（**`chat.py` 那处右边有副作用**：`resolve_vault_scope` 注入 ContextVar + 跑 vault 一致性检查，删调用 = 删掉 CARD-G2-2 的跨 vault 写修复） |
