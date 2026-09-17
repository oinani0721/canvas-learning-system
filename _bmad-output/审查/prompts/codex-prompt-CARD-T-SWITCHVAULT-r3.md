你是独立复核者。请只读、不改任何文件、不连任何数据库或网络端口。

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`
分支 `card/t5-bugs`，审查绑定 SHA = `3ecf2c5e9e163a3daecc14797a28cdab80d82380`（HEAD），
地盘基线 PREV = `6d7eb683f126ec4ae142426ad7be34d33cad0e27`。

---

## ① 背景与最小读取面（请逐个读完再下结论）

本卡 `CARD-T-SWITCHVAULT`（BATCH-2026-09-11-第十四批）修一个真缺陷：MCP 工具
`switch_vault` 直接读 `result.vault_name` / `result.vault_id`，而被调用的端点注解并
实际返回 `JSONResponse`，它没有这两个属性 ⇒ 运行期 `AttributeError` 被本函数的
`except Exception` 吞成
`{'success': False, 'error': "'JSONResponse' object has no attribute 'vault_name'"}`。
调用方看到的是一句与真实原因无关的内部类型错误；真实原因是该端点被 P0-3 写侧隔离、
恒返回 410，改 vault 要在部署配置里改。

请读以下内容（写死的最小读取面）：

1. `git --no-pager diff --no-color 6d7eb683f126ec4ae142426ad7be34d33cad0e27 3ecf2c5e9e163a3daecc14797a28cdab80d82380 -- . ':(exclude)_bmad-output'`
   —— 本卡全部代码改动（应恰两个文件）。
2. `backend/app/mcp/tools/infra_tools.py` **全文**（含未改动的 `check_backend_health`，
   它是本卡参照的同型先例，本卡不改它）。
3. `backend/app/api/v1/endpoints/vault.py` 第 30–108 行 —— `VaultSwitchRequest` 模型
   与 P0-3 隔离端点本体（恒 410）。
4. `backend/app/mcp/server.py` 第 277–297 行（`check_backend_health` 的 live 路由注册面）
   与第 353–405 行（`QUARANTINED_MCP_TOOLS` 清单 + 410 stub 注册循环）。
5. `backend/tests/unit/test_mcp_switch_vault_tool.py` **全文** —— 本卡新增的两条测试。

---

## ② 作者自述（请独立核对，不要采信）

作者声称：

- (a) `switch_vault` 现在解析 `JSONResponse.body`，与同文件 `check_backend_health` 同型；
- (b) `bytes(result.body)` 是为静态类型准备的：`body` 的静态类型是 `bytes | memoryview[int]`，
  而 `json.loads` 不接受 `memoryview`；
- (c) 对 `payload` 加了 `isinstance(payload, dict)` 守卫，且**非 dict 一律判失败**，
  不落进 `success=True` 分支；
- (d) 410 / `error` 分支把端点 body 里的 `detail` 透传为 `error`；`detail` 缺失时不落成
  字符串 `"None"`；
- (e) 原先 `:63` / `:64` 两处 `# pyright: ignore[reportAttributeAccessIssue]` 已随缺陷访问删除，
  `switch_vault` 函数体内现在零 pyright ignore（`check_backend_health` 的那条保留、非本卡地盘）；
- (f) 两条新测试**直接 await 真协程**、不 mock、不 monkeypatch，打的是真实隔离端点；
  第二条测试是第一条的自证锚，断言 `status_code == 410` 且 body 里没有 `vault_name` / `vault_id`；
- (g) 实测：`pyright app` = `0 errors, 81 warnings`（与本卡开工基线逐字相同）；
  `ruff check` / `ruff format --check` 两文件 rc=0；两条测试 2 passed；
  `tests/unit` 目录级红集与批基线 64 条逐条相同（零新增、零减少）。

---

## ③ 请按重要性排序回答这些问题

⓪ **payload 非 dict 的路径**：`json.loads` 可能返回数字 / 字符串 / 列表 / null。
   现在的分支排列下，是否存在**未被拦下的输入**能触达某个未加守卫的 `.get(...)`，
   或者能让调用方拿到 `success=True`？请逐条走分支，不要只看 `isinstance` 那一行。

① `bytes(result.body)` 在 `body` 为 `memoryview` 时是否恒成功？若 `body` 是别的类型
   （例如被中间件替换），会落到哪个 `except`、调用方看到的文案是否仍有信息量？

② `success=True` 分支在当前隔离态**永不执行**（端点恒 410）。这是否属于
   **门未覆盖的路径**？若是，本卡的两条测试对它有无任何约束力？请直说没有。

③ 外层 `except Exception as e` 是否仍会吞掉本该显形的错误？特别是：端点若抛异常
   而不是返回 `JSONResponse` 时，调用方拿到的文案是否又变回一句与真实原因无关的内部错误？

④ 修好之后，这个函数在运行期是否仍然是**无人可达的死代码**？请以
   `server.py` 的注册面为准给出判断（`switch_vault` 是否在 `QUARANTINED_MCP_TOOLS` 内、
   是否有任何 live 路由指向 `infra_tools.switch_vault` 本体）。

⑤ 同文件 `check_backend_health` 是否有同型隐患？**本卡不改它**，只问是否需要另立卡。

⑥ 两条测试是否存在**假绿面**：有没有哪条断言在修复被退回后仍然会通过？
   （作者做过两组负控：退回 `result.vault_name` 时红在「has no attribute」那条；
   删掉 410 透传分支时红在 success 那条。请判断这两组是否足以支撑「测试锁住了修复」。）

---

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- 一句问题陈述；
- `file:line`（用你实际读到的行号）；
- 一句说明「在什么输入或什么状态下会显形」。

若某级别没有问题，请显式写 `BLOCKER: 0` / `HIGH: 0` 等，不要省略。

---

## ⑤ 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接任何数据库或端口。
- **不要评价 P0-3 隔离决策本身**——是否该解除隔离是产品裁定，不在本卡范围；
  本卡只把误导性的错误文案改成透传真实原因。
- **不要评价 `check_backend_health` 既有的那条 pyright ignore**（`:47` 附近），
  它不在本卡地盘；如认为需要处理，只在 ⑤ 里说「建议另立卡」即可。
- 不要要求本卡恢复 runtime vault 切换能力。
- 不要要求扩大本卡地盘：本卡只允许改
  `backend/app/mcp/tools/infra_tools.py` 与 `backend/tests/unit/test_mcp_switch_vault_tool.py`
  两个文件。若你的建议需要改别的文件，请标注「需另立卡」。

---

## ⑥ round-3 增量：round-2 四条 LOW 的处置（本轮**只改 docstring**）

round-2 你给出 BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4。处置如下，**请独立核对**：

**已实测确认你的三条声称全部成立**，并按此更正了文档。为此跑了八组负控，
每组都跑**整文件两条测试**（修正你 LOW-3 指出的证据口径问题）：

| 组 | 变异 | 实测 | 对应你的哪条 |
|---|---|---|---|
| A | 退回 `result.vault_name` | 1 failed（红在 has-no-attribute 断言）+ 1 passed | — |
| B | 删 410/error 失败分支 | 1 failed（红在 success 断言）+ 1 passed | — |
| C | error 硬编码成短常量 `"quarantined"` | 1 failed（红在逐字比对断言）+ 1 passed | — |
| D | 删 `bytes()` | **2 passed** | ①：确认本文件不守它 |
| E | 外层 except 退回 `str(e)[:200]` | **2 passed** | ③：确认 E 无行为门 |
| F | 删失败判据的 `status_code >= 400` 一侧 | **2 passed** | **LOW-2 成立** |
| G | 失败判据 `or` 改 `and` | **2 passed** | **LOW-2 成立** |
| H | 工具跳过端点、直接硬编码完整 `detail[:200]` | **2 passed** | **LOW-1 成立** |

据此更正的文档内容（全部在 `test_mcp_switch_vault_tool.py` 的模块 docstring
与①末尾的行内注释里）：

1. **LOW-1**：删掉「逐字比对同时证明①调用了该端点 / 两条测试之间有真实数据依赖」
   这句过强表述，改为如实写明：它只锁「文案与端点当前 body 逐字一致」，
   调用链由源码（函数体内无替换、无 mock）保证，不由该断言保证。附负控 H 依据。
2. **LOW-2**：「本文件不证明什么」新增第 8 条（失败判据两侧各自无门，附 F/G 实测）
   与第 9 条（内层异常兜底、`detail` → `error` → HTTP 文案的回退链均不可达）。
3. **LOW-3**：docstring 里所有「2 passed」改为标注来自**整文件两条测试**的负控跑，
   并写明证据文件路径；同时如实记下「早一版只跑测试①、日志是 1 failed/1 passed，
   却被表述成两条全绿」这一口径错误。
4. **你在 ① 里指出的两处归因不准**已更正：`bytes | memoryview[int]` 改记为
   **Starlette `Response.body` 的推导类型**（不再写成「typeshed 把它标成……」，
   typeshed 提供的是 `json.loads` 的签名）；「运行期恒为 bytes」加了限定
   「当前端点正常返回、body 未被中间层替换的路径上」，并注明依据是
   `starlette.responses.JSONResponse.render` 返回编码后的 bytes。
5. **LOW-4**（`check_backend_health` 同型缺口）：接受「另立卡」，本卡不处理，
   已登进验收单的移交条目。

**本轮是纯 docstring 改动**，已用 AST 证明：剥掉全部 docstring 后
`ast.dump` 逐字相同（`CODE_IDENTICAL_AFTER_STRIPPING_DOCSTRINGS = True`，
且该判据带验伪锚——改一个真实断言值时判据变 False）；
`backend/app/mcp/tools/infra_tools.py` 在 `b355f7b7 → 3ecf2c5e` 区间零 diff。

请核对：
- 更正后的每一句表述是否仍有**比证据更强**的地方（这是本卡连续两轮的失分点）；
- 「本文件不证明什么」9 条是否仍有遗漏的未覆盖改动；
- 本轮是否真的没有改动可执行代码。
