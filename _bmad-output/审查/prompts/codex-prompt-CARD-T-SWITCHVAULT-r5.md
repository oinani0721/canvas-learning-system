你是独立复核者。请只读、不改任何文件、不连任何数据库或网络端口。

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`
分支 `card/t5-bugs`，审查绑定 SHA = `59e0d7661f94ece7f217a82fbb675ec3025c6b3c`（HEAD），
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

1. `git --no-pager diff --no-color 6d7eb683f126ec4ae142426ad7be34d33cad0e27 59e0d7661f94ece7f217a82fbb675ec3025c6b3c -- . ':(exclude)_bmad-output'`
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

## ⑥ round-5（本卡最后一轮，轮次上限 5）：round-4 的 2 MEDIUM + 3 LOW 处置

round-4 你给出 BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 3。**五条我核对后全部成立**，逐条处置如下。
增量 diff：
`git --no-pager diff --no-color 27021e85f1d5548a47b8a2e5126be152fe9eac40 59e0d7661f94ece7f217a82fbb675ec3025c6b3c -- . ':(exclude)_bmad-output'`
**本轮只改测试文件 docstring**，生产文件零 diff（AST 剥 docstring 后指纹相同，验伪锚为 True）。

### MEDIUM-1（目录级实为 65，不能声称「diff 空」）—— 接受，已如实更正

验收单 §一(h) 与 §二.5 现在如实记录：在 `27021e85` 上的目录级为 **close=65**，
比基线多一条 `test_candidate_service::test_accept_candidate_already_accepted_returns_422`。
归因（请独立核）：

1. 该次日志 `:601-605` 显示它红的原因是 **W4 门抓到一次到现网 Neo4j `7691` 的连接尝试**
   （`owner=` 字段即该用例），门按设计把它转成用例失败；`:1148` 的计数是
   `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)` ——
   **`blocked=1` 表示连接被拦下、未真连上现网**。
2. 按**协议 §4.3** 目录级的红分三类：主干既有 / **门抓到的既有偷连** / 本批引入（阻断）。
   本条属第二类。
3. 归因依据（不是「后来单跑通过」——你指出那不能改写该次结果，我同意）：
   - `3ecf2c5e → 27021e85` 是**纯 docstring 改动**，AST 剥 docstring 后可执行代码指纹相同；
     同一份可执行代码前一轮跑出 64、这一轮跑出 65 ⇒ **逻辑上排除「代码引起」**；
   - 本卡 `PREV..HEAD` 改动文件只有两个，`grep -ci candidate` = 0；
   - 基线文件自己的第 3 行注释逐字记录该 nodeid 是 **flaky**（第十三批红集含它、第十四批取样时消失）。
4. 已按你的意见登记「若要处理该测试，**需另立卡**」。

### MEDIUM-2（裁判绑旧 SHA）—— 接受，已在最终 SHA 重跑

全部五道门已在 `59e0d766` 上重跑并落档 `evidence-switchvault/allgates-selfbound-59e0d766-*.txt`
（首部含 HEAD + 两文件工作树/HEAD blob 双侧 sha256 + `BOUND_TO_HEAD=True`）：
两条测试 2 passed / `pyright app` 0 errors / `ruff check` rc=0 / `ruff format --check` 已格式化 /
地盘核恰两文件 / DD-03 的 AST 判据 `NO_MOCK_VERDICT=PASS`。
你指出的「AST 等价不能替代对新文本的 ruff 格式检查」已采纳——这次是真跑，不是推。

### LOW-1（N 探针把单条断言扩大成整条测试）—— 接受，且实测结论比你说的更强

我补跑了**每种 mock 形状 × 测试①的全部四条断言**
（`evidence-switchvault/probe-detail-and-fullassert-*.txt`）：

| 形状 | A1 success | A2 无属性错误 | A3 token | A4 逐字 | ①整体 |
|---|---|---|---|---|---|
| M1 dict（无 `.body`） | PASS | FAIL | FAIL | FAIL | 红 |
| M2 有 `.body` 无 `.status_code` | PASS | FAIL | FAIL | FAIL | 红 |
| M3 SimpleNamespace（无 `.body`） | PASS | FAIL | FAIL | FAIL | 红 |
| M4 有 `.body`+`.status_code` | PASS | PASS | **FAIL** | FAIL | 红 |
| M5 坏 JSON body + `.status_code` | PASS | PASS | **FAIL** | FAIL | 红 |

⇒ **实测过的五种形状没有一种能让①整体变绿**。docstring 已据此重写：要让①全绿，
mock 必须返回与真实端点**逐字相同**的 410 body（即 mock 成真端点本身）。
原表述的两处错误（全称断言 + 把单条断言结果说成整条测试结果）都已标注更正。

### LOW-2（负控 A 不依赖 handler）—— 接受

已改为：依赖 handler 的是**失败位置**（红在哪一条断言），不是「A 还能不能杀」——
删掉 handler 后 `AttributeError` 会直接从 `asyncio.run` 抛出，测试仍红。标注为源码推导
（本卡未跑「A + 删 handler」的组合变异）。

### LOW-3（216 字符无存档）—— 接受，已补探针落盘

`probe-detail-and-fullassert-*.txt` 现在打印 `len(detail) = 216`、`> 200 = True`、
被截掉的尾巴 `'to change vault.'`。标注保持【实测-探针】并写明存档名。

### 你另外指出的两点

- **`str(detail)` 标签矛盾**：验收单曾写「源码推导、未跑变异」，与负控 J 记录矛盾 —— 已更正为
  【实测-负控 J】。
- **清单非穷尽**：已新增第 12 条（`input.vault_path` 参数传递未覆盖，你举的例子），
  并在清单末尾显式声明「本清单不是穷尽的」及其原因（端点恒返回同一常量响应）。

### 请重点核

1. 上述每一处更正，是否**仍有**比证据更强的地方？
2. MEDIUM-1 的归因链（尤其「同一份可执行代码两次跑结果不同 ⇒ 排除代码引起」这一步）是否成立？
3. 三级证据标注【实测-负控 X】/【实测-探针】/【源码推导】是否被如实使用？
4. 本轮是否真的没有改动可执行代码？
