# 复核任务：CARD-T-UNREACH（BATCH-2026-09-11-第十四批 · 车道 T5 第 5/5 · 末张）

你是独立复核者。只读审查，不要修改任何文件，不要运行会连接数据库或写文件的命令。

## ① 背景与最小读取面

本卡修的是一个**死分支**：`boards.py` 的 HTTP 端点与 `board_manifest_tools.py` 的 MCP 工具，各有一处
`except pydantic.ValidationError` 写在 `except ValueError` **之后**。因为 `pydantic.ValidationError`
是 `ValueError` 的子类（pydantic 2.12.5，`issubclass(ValidationError, ValueError) is True`），该分支
**永不可达**——两处注释宣称的「schema 契约被破 → 诚实 500 / 结构化错误」纵深兜底从未生效，实际返回
的是 422 /「非法参数: ...」。

本卡把两处 `except pydantic.ValidationError` **调到 `except ValueError` 之前**，删掉该行上多余的
`# pyright: ignore[reportUnusedExcept]`（分支可达后该 ignore 变成「多余 ignore」，仓根
`pyrightconfig.json` 的 `reportUnnecessaryTypeIgnoreComment="warning"` 会报），并改写注释。
pyright 保持 `0 errors / 81 warnings`。

**最小读取面（只读这些，不要扩散到其它文件）**：

- `git diff 3b819f404668c59c7ddc08c083f8014355e2dc96 802f05ca352afc3d432b1511f7e2e38869f19eb3 -- . ':(exclude)_bmad-output'`（本卡完整代码改动面）
- `backend/app/api/v1/endpoints/boards.py` 的 `get_board_manifest_http`（约 :53-95）
- `backend/app/mcp/tools/board_manifest_tools.py` 的 `get_board_manifest`（约 :47-76）
- `backend/tests/unit/test_board_manifest_unreach_t5e.py` 全文
- `backend/app/models/board_manifest.py` :198-237（`_ManifestEnvelope` :198-215 的三个必填字段
  `source` / `source_status` / `id_stability`；`project_manifest` :231-237，末行是一条
  **非 ValidationError 的** `raise ValueError(f"未知视图: ...")`，是对照语义锚）

## ② 作者自述，请独立核对（不要采信，请自己看代码）

1. 两处 `except pydantic.ValidationError` 已排在 `except ValueError` 之前，AST 里
   `order.index("ValidationError") < order.index("ValueError")` 成立；`KeyError` 留在原相对位置。
2. 两处 `# pyright: ignore[reportUnusedExcept]` 已删；`grep -rnF 'pyright: ignore[reportUnusedExcept]'
   backend/app | wc -l` = 0，同次验伪锚 `grep -rnF 'except pydantic.ValidationError' backend/app | wc -l` = 2。
   pyright（cwd=backend）`0 errors, 81 warnings`，与改前基线一致（未涨到 83）。
3. 行为变化有先红后绿证据：改前 6 failed / 5 passed，改后 11 passed。红落在 status/error/顺序断言，
   不是 import 或 fixture 错。
4. 对照组在改前改后**两态都绿**：非 ValidationError 的普通 `ValueError("bad board_id")` 仍 HTTP 422 /
   MCP「非法参数: bad board_id」；`KeyError("no such board")` 仍 HTTP 404 / MCP 原样 detail。
5. 异常由**真** pydantic `model_validate` 失败产生——monkeypatch 只替换文件 I/O 协作者
   `serve_manifest` 的返回值（缺三个必填键的 dict），没有伪造异常对象，没有用 MagicMock。
6. 负控：把任一文件的 ValidationError 分支挪回 `ValueError` 之后（重演死分支），该文件对应的
   后绿断言变红、**另一个文件的断言仍绿**；还原后全绿，跑前跑后全文件 `shasum -a 256` 逐字相同。
7. 本卡只改三个文件：两个生产文件 + 一个新测试文件。不碰 `openapi.json`、不碰 route 的
   `response_model` 与声明状态码。

## ③ 请按重要性排序回答的问题

0. 把「service 产出的数据过不了自身 response schema」归为 **500** 而不是 422，是否符合
   「客户端没传错、是服务端自己产出的数据不合格」的语义？是否存在调用方依赖旧的
   「ValidationError → 422」行为（HTTP 侧）？
1. MCP 侧 error 文案从「非法参数: ...」变成「manifest 投影 schema 异常, 已记录日志」后，
   skill 侧「curl 失败静默退回 Grep」的降级契约是否仍成立（返回仍是 `ok=False`，只是文案变）？
2. 是否存在**其它**被上游宽异常遮蔽的 except？本卡只修 census 出的 2 处；
   `backend/app/services/board_manifest_service.py:1029` / `:1069` 与
   `backend/app/services/canvas_service.py:701` 的三处 `except ValidationError` 作者判断为
   各自 try 内唯一 handler、非死分支——请独立核对该判断。
3. 调顺序后 `KeyError` 分支是否仍正确？（`KeyError` 不是 `ValueError` 子类，作者判断不受影响。）
4. 测试里 monkeypatch `serve_manifest` / `resolve_vault_scope` 配合 `asyncio.run`，是否可能污染
   事件循环或泄漏到同一进程内的其它测试？两个 patch 目标不同（前者 patch 消费模块、后者 patch
   源模块 `app.core.vault_scope`，因为它是函数内 import）——这个区分是否正确？
5. 删掉两处 `# pyright: ignore[reportUnusedExcept]` 是否会在某种 pyright 配置下反而触发新诊断？
6. 新测试文件里的 AST 结构门（断言 handler 索引顺序）是否有会让它**看起来绿但实际没断言到**的路径？

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 与一句说明。说明请用
「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类描述方式来指出问题在哪里。
若某级别为空请明确写「无」。结尾给各级计数。

## ⑤ 边界

只读审查；不连数据库、不起服务、不跑 lifespan；不评价本车道其它四张卡的面
（`backend/app/security.py`、`backend/app/mcp/tools/infra_tools.py`、
`api/v1/endpoints/system.py`、`edges.py`、`config.py`、`services/background_task_manager.py`、
`tests/contract/test_openapi_contract.py`），也不评价 service 层
（`services/board_manifest_service.py`）本体实现——那些不在本卡地盘。
