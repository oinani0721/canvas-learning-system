# UAT — CARD-EXC-HANDLER-WIRE-REDACT

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-EXC-HANDLER-WIRE-REDACT]` · 车道 P8（`card-p8-backend`，分支 `card/p8-backend`）· 本车道第 1/3 张
> **终态字段（收工重算，2026-09-18）**：最终代码 SHA **`6d8e4ee056c0538c81a4e028b866453f9bde7ac7`** · 代码 commit 数 **6**（另 1 个 `_bmad-output` commit）· Codex 轮次 **5**（上限用满，末轮绑最终 HEAD，B/H=0） · evidence 文件数 **72**（含 README 与两份已标注作废的存档）
> **B15_BASE**：`9c4e7e82`（开工 HEAD = B15_BASE，工作树干净）

## 一 卡文事实核对（§〇 逐条实测；漂移如实登记）

| 卡文写 | 实测 | 处置 |
|---|---|---|
| `exception_handlers.py` 四行 `add_exception_handler` 在 **:306-309**、`logger.info` 在 **:311** | 实测 **:309-312** / **:314**（:306-308 是 TAIL T6 的 `cast` 说明注释三行） | 漂移 +3 行，按实测执行 |
| `main.py:807` `safe_message[:500]`、`:808` `error_type`、`:818-824` 层序注释、`:825` `add_middleware(CORSExceptionMiddleware)` | 全部一致 | — |
| `review.py:1413` 路由装饰器、`:1423` `async def get_fsrs_state`、`:1507` `except`、`:1515` `reason=f"error: {e}"` | 全部一致 | — |
| `test_production_bugs.py` xfail 在 **:51-54** | 一致（`@pytest.mark.xfail(` :51，`def test_bug_bug_1cbf9ae9` :55） | — |
| `test_u9c_startup_rejection_eval.py:376` 用例名 / `:437` 断言 | 一致（文件共 442 行） | — |
| (g)① 身份断言写 `m.app.exception_handlers[HTTPException]`（`fastapi.HTTPException`） | **实测 KeyError** —— 生产表里的键是 `starlette.exceptions.HTTPException`；`fastapi.HTTPException` 根本不在表里 | 门改为：starlette 键身份 `is` FastAPI 默认函数 **且** `fastapi.HTTPException` **不在**表里（后者是更强的排他锁）。证据 `evidence-exc-handler-wire/wire-runtime-before-*.txt` 首份 |
| 卡文 (g)⑥ / §〇：去掉 `1cbf9ae9` 的 xfail 后该用例会 **XPASS（变 passed）** | **不成立**。去 xfail 后它**真红**，但红在本文件 autouse fixture 的同步 `MagicMock`（`TypeError: 'MagicMock' object can't be awaited`）—— 请求走不到 `CanvasNotFoundException` | xfail **保留**并改 `reason` 为实况；生产 app 的 404 化改由新门 `test_production_app_maps_core_canvas_not_found_to_404` 证明（真生产 app + 真接线 + async 上游替身）。修 fixture 越界，登记移交 |
| core 族 raise 站点参数是否含服务端绝对路径 | 7 个站点实测传的都是**调用方输入**（`canvas_name` / `node_id` / `original_canvas_path`）；`canvas_service.py:190` 本身就拒绝绝对路径 | 4xx 体回显调用方输入，不含服务端秘密；「反射面未证明」登记在 §未证明 ① |

## 二 DoD-3

### 4-A 技术验收（Claude 已代验，逐条贴证据路径）

> evidence 目录：`_bmad-output/审查/evidence-exc-handler-wire/`

**1. 结构门（改前 / 改后同一脚本）** — `struct-before-*.txt` / `struct-after-*.txt`

| 判据 | 改前 | 改后 |
|---|---|---|
| `register_exception_handlers(app, override_fastapi_defaults=False)` | 0 | **1** |
| `safe_message[:500]` | 1 | **0** |
| `"message": "Internal server error"`（main.py） | 0 | **1** |
| `最外层，捕获所有异常` | 1 | **0** |
| `reason=f"error: {e}"` | 1 | **0** |
| `reason=f"error: {type(e).__name__}"` | 0 | **1** |
| `core_canvas_exception_handler`（exception_handlers.py） | 0 | **2** |
| AST：`dispatch` 内 `JSONResponse(content=…)` 的 `"message"` 值节点 | `Subscript` | **`Constant`** |
| 验伪锚 `CORSExceptionMiddleware`（同次执行，已知正例） | 5（≥4） | 7（≥4） |

**2. 运行期接线自证** — `wire-runtime-before-*.txt` / `wire-runtime-after-*.txt`

- 改前键集 = `starlette.exceptions.HTTPException` / `RequestValidationError` / `WebSocketRequestValidationError`（**无** `Exception`、无任何 `CanvasException`）
- 改后键集增 `app.core.exceptions.CanvasException` + `app.exceptions.canvas_exceptions.CanvasException` + `builtins.Exception`
- 两侧 `starlette HTTPException` / `RequestValidationError` 的处理器**身份** `is` FastAPI 默认函数 → `True`；`fastapi.HTTPException` 两侧都**不在**表里（排他锁）
- `user_middleware` 两侧同为 `[Metrics, CORS, Encoding, CORSException]`（外→内）

**3. 新门红 → 绿（核收集数）** — `wire-red-*.txt` → `wire-green-postfmt-*.txt` → `wire-green-r1fix-*.txt`

- 先红（**未改生产代码**）：collected 6 → **5 failed / 1 passed**，5 条红各落在指定断言（接线键缺席 / `message` 非泛化串 / 开关不存在 ×2 / `reason` 口径），层序用例如预期**就绿**（它锁事实不锁修复）
- 改后：collected 6 → 6 passed；r1 整改后 collected 8 → **8 passed = 文件内 `def test_` 数 8**

**4. 口径钉翻转 + 1cbf9ae9** — `pin-before-full-*.txt` / `pin-after-*.txt` / `wire-green2-*.txt`

- 改前：11 passed / 5 skipped / **1 xfailed**（XFAIL = `test_bug_bug_1cbf9ae9`）
- 改后：u9c 用例改名 `test_production_stack_redacts_message_in_500_body` 仍 passed；`1cbf9ae9` **仍 xfailed**
- ⚠️ **与卡文预期不符，如实登记**：卡文 (g)⑥ 预期去 xfail 后该用例变 passed。实测去 xfail 后它**真红**，但根因不是 canvas 不存在 —— 是该文件 autouse fixture 把 `get_canvas_service` 覆盖成**同步** `MagicMock`，端点 `await canvas_service.sync_all_edges_to_neo4j(...)` 先抛 `TypeError: 'MagicMock' object can't be awaited`，请求走不到 `CanvasNotFoundException`。⇒ 该用例**测不到它声称的那个 bug**。处置：xfail 保留（结果与基线一致），只把 `reason` 改成实况；生产 app 上的 404 化改由 `test_production_app_maps_core_canvas_not_found_to_404`（真生产 app + 真接线 + async 上游替身）证明。修 fixture 越界，登记移交。

**5. 负控（五段，各只拆一层；HEAD 已含修复 ⇒ `git show HEAD:` 还原可靠）**

| 段 | 变异 | 指定断言变红 | 收集数 | shasum 前/后 |
|---|---|---|---|---|
| ① | main.py 体改回 `safe_message[:500]` | `test_middleware_500_body_is_redacted_and_bounded` + u9c `..._redacts_message_in_500_body` | 2 selected / 10 deselected | 逐字同 |
| ② | 删 main.py 接线行 | `..._wires_core_and_generic_handlers` + `..._maps_core_canvas_not_found_to_404` | 3 selected / 16 deselected | 逐字同 |
| ③ | review.py 改回 `reason=f"error: {e}"` | `test_fsrs_state_error_reason_is_redacted` | 1 selected / 6 deselected | 逐字同 |
| ④ | 删 `NodeNotFoundException → 404` 映射 | `..._core_family_status_mapping_and_500_redaction` 红在 `NodeNotFoundException: 期望 404，实得 500` | 1 selected / 7 deselected | 逐字同 |
| ⑤ | core 500 体 `message` 改回 `str(exc)` | 同上，红在 `CanvasException: core 500 未脱敏` | 1 selected / 7 deselected | 逐字同 |

段②如实登记：`1cbf9ae9` 在该段**仍 xfailed**（它走不到那条链，见上面第 4 条），所以段②的第二重证据换成了生产 app 404 门。存档 `negctl-{1,2,3,4,5}-full-*.txt`（含 pre/post shasum 两行与还原后 `git status` 空）。

**6. pyright / ruff** — `pyright-open-*.txt` / `pyright-close-*.txt` / `territory-*.txt`

- `(cd backend && "$P" app)`：改前 **0 errors, 80 warnings** → 改后 **0 errors, 80 warnings**（逐字同；`$P` 绝对路径 + `test -x` 自证）
- ruff（zsh 数组）：`files=6`，`ruff check` All checks passed（rc=0）、`ruff format --check` 6 files already formatted（rc=0）
- F821 验伪锚（stdin 喂入，按 `backend/tests/unit/` 路径解析配置、不落盘）：命中 `F821` 且 `probe_rc=1`；对照（合法代码）`control_rc=0`

**7. 既有套件 + 目录级**

- 点名 6 文件：开工 **106 passed** → 收工 **106 passed**（`named-open-*.txt` / `named-close-*.txt`）
- `tests/regression` 目录级：**1913 passed / 6 skipped / 1 xfailed / rc=0**，与 B14 基线（`evidence-b14/integ2/dir-regression-9c4e7e82-*.txt`）**逐字相同**（`regression-close-*.txt`）
- `tests/unit` 目录级：开工 32 failed（`unit-open-*.txt`），与 B15_BASE 33 条的 diff **只有 `<`**（缺的那条正是基线头自述的已知 flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`）；收工见下表
- W4 哨兵：各跑均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` —— 本卡全程进程内 `TestClient`，不连 7691/7687/7692

**`tests/unit` 目录级收工（绑最终 HEAD `6d8e4ee0`，存档 `unit-close-final-*.txt`）**

| 项 | 开工（B15_BASE 面） | 收工（`6d8e4ee0`） |
|---|---|---|
| 汇总 | 32 failed / 5731 passed / 44 skipped / 13 xfailed | **32 failed / 5739 passed / 44 skipped / 13 xfailed** |
| W4 哨兵 | `blocked=0` | **`blocked=0`** |
| nodeid diff vs `unit-red-baseline-9c4e7e82.txt`（33 条） | 只有 `<`（1 条已知 flaky） | **只有 `<`（同一条 flaky），零 `>`** |

passed 从 5731 增到 5739 = 本卡新门 8 条。

**⚠️ 中途出现过一次 `>` 并已修复（全过程如实登记）**：绑 `7d3bdc2b` 的那次目录级跑里
`test_production_app_maps_core_canvas_not_found_to_404` 报红 —— 断言全过，红在 W4 哨兵
（`blocked` 0→1）。第一次修法（`8c4a66a8`）**无效**，第二次（`9e034d60`，覆盖键改取路由绑定对象）才真正修好。
三次目录级跑的哨兵读数依次是 `blocked=1` → `blocked=1` → `blocked=0`。

**点名 6 文件 + 两份 regression 收工**（`named-close-final-*.txt`）：**117 passed / 5 skipped / 1 xfailed**
（1 xfailed = `1cbf9ae9`，与基线同身份）。

**`tests/contract/test_openapi_snapshot_drift.py`**：26 passed / rc=0（`contract-drift-*.txt`）。

**`tests/regression` 目录级收工（绑最终 HEAD `6d8e4ee0`，存档 `regression-close-final-*.txt`）**

**1913 passed / 6 skipped / 1 xfailed / rc=0**，与 B14 基线
（`evidence-b14/integ2/dir-regression-9c4e7e82-20260917T222112.txt` = `1913 / 6 / 1`）**逐字相同**；
哨兵 `blocked=0`。

⚠️ **与卡文预期的差异（如实）**：卡文 (i) 预期「若基线那 1 xfailed 即 `1cbf9ae9`，收工应为 0 xfailed + passed +1」。
实测**仍是 1 xfailed** —— 因为本卡**保留**了该 xfail（理由见第 4 条）。数字与基线完全一致，不是回退。
（本卡对 regression 面的改动只有两份点名测试；u9c 用例改名后仍 passed，所以总数不变。）

绑 `0707be32` 的那次 regression 目录级同样是 `1913 / 6 / 1`（`regression-close-20260918T172438.txt`），
两次一致。

**8. 地盘门 + openapi** — `territory-*.txt` / `openapi-drift-*.txt`

- `git --no-pager -c core.quotepath=false diff --stat --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'` = **恰 6 文件**，全部在 (l) 白名单内；`main.py` 的 `+` 行落在 **807-808 / 819-829**（⊆ :702-830），`review.py` 落在 **1508-1509 / 1516-1517**（⊆ :1505-1518），`test_production_bugs.py` 只改 :51-54 那个装饰器
- `git diff … -- backend/openapi.json` **空**；`git show --stat HEAD` 里 `openapi.json` 命中 **0**
- `check-openapi-drift.py --write` 原始输出：`WROTE: backend/openapi.json (paths=199 schemas=357, x-generated-at=2026-09-18T09:16:24…)`，再生 diff = `1 file changed, 1 insertion(+), 1 deletion(-)`，逐行只有 `x-generated-at` 一行变化；`git show HEAD:backend/openapi.json > backend/openapi.json` 还原后 `git status --porcelain backend/openapi.json` **空**
- 提交用 `LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root`，commit 日志里两 hook 显示 `(skip) name`；`python-lint` / `python-typecheck` 均 ✔️（未 exclude）

**地盘门验伪锚（`_bmad-output` 入库后才跑，避免 commit 前的空洞）**：同一对 SHA，
带 `':(exclude)_bmad-output'` = **6 文件**，不带 = **90 文件**（多出的 84 个全是 `_bmad-output/`）
⇒ exclude 确实在起作用，判据不是恒空。

**终审绑定**：`git --no-pager -c core.quotepath=false diff --stat --no-color 6d8e4ee0 HEAD -- . ':(exclude)_bmad-output'`
= **空**（`6d8e4ee0` = r5 审查绑定 SHA = 最后一个动代码的 commit）；同一对 SHA 不带 exclude = 84 文件
（验伪锚，证明这条「为空」不是命令没跑成）。

⚠️ **判据自身的一次修正（如实）**：入库前核「staged 里有没有混入代码文件」时写的是
`git diff --cached --name-only | grep -vc '^_bmad-output/'`，得到 83（= 全部）。原因是**中文路径被 git
quotepath 转义成 `"_bmad-output/\345…"`**，行首是引号不是 `_`，锚点恒不命中。加 `-c core.quotepath=false`
后重跑：非 `_bmad-output` 文件 **0**，`_bmad-output` 文件 **83**，总数 83 —— 三个数自洽。

**9. Codex（gpt-6-astra · ultra · codex-cli 0.153.3）**

| 轮 | 绑定 | 结论 | 存档 |
|---|---|---|---|
| r1 | `0707be32`（= 当时 HEAD） | **0 BLOCKER / 0 HIGH** + 4 MEDIUM + 2 LOW | `codex-review-CARD-EXC-HANDLER-WIRE-REDACT.md` |
| r2 | `7d3bdc2b` | **0 BLOCKER / 0 HIGH** + 3 MEDIUM + 2 LOW | `…-r2.md` |
| r3 | `8c4a66a8` | **0 BLOCKER / 0 HIGH** + 3 MEDIUM + 4 LOW | `…-r3.md` |
| r4 | `9e034d60` | **0 BLOCKER / 0 HIGH** + 3 MEDIUM + 5 LOW | `…-r4.md` |
| r5（末轮） | `6d8e4ee0`（= **最终 HEAD**，代码树自此零改动） | **0 BLOCKER / 0 HIGH** + 3 MEDIUM + 4 LOW，并明确「没有证据需要把此前 MEDIUM/LOW 升级」「命中断言未引入新问题」 | `…-r5.md` |

r1 采纳三条（**只改新门文件，生产代码零改动**，独立 commit `7d3bdc2b`）：MEDIUM-3 core 族六档映射 + 500 脱敏门、MEDIUM-4 处理器**绑定身份**断言、LOW-5 `bug_log` 断言升为全文。r2 已独立确认「round-1→round-2 只有一个提交、仅测试文件 +106/-2、生产代码零改动」且「三项整改成立」。

r2 剩余 3 MEDIUM + 2 LOW **全部登记不改**，逐条理由：

1. **MEDIUM（`app.exceptions` 族 500 走 `to_dict()` 原文）**：卡文 (c)(2) 明示 `override_fastapi_defaults=False` 分支**仍注册**该族。Codex 指出「`test_middleware.py` 约束的是默认 True 分支」——**这条反驳成立**，故本卡不再以该套件为理由；保留的真实理由是**卡文指定** + 该族在 `backend/app` 的 `raise` 站点实测为 0（`git grep` 只有 `canvas_exceptions.py:157` 的 docstring 示例）。改注册形态超出卡文 scope，移交。
2. **MEDIUM（响应头泄漏的负控门未覆盖）**：当前代码的头只有 `X-Request-ID`（来自 `request.state.request_id`）与 CORS 两头（来自 Origin 白名单/固定值），无异常文本数据流；这是**门的缺口**不是缺陷。补门需再一轮，权衡后登记（见「未证明什么 ⑧」）。
3. **MEDIUM（core 4xx `details` 白名单未被门锁）**：`_core_exception_details` 当前是三键白名单（不是 `vars(exc)`），把它改成全量导出会多出属性 —— 同样是**门的缺口**。登记（见「未证明什么 ⑨」）。
4. **LOW（动态生成的类名进 `error_type` / `reason`）**：理论面，生产无此形态。
5. **LOW（u9c `:283-284` / `:315-317` / `:338` 仍写「生产当前没接它」）**：**真文档退化**，但这三处**不在**卡文 (l) 给 u9c 的白名单行段（`:15-60` / `:280-300` / `:376-446`）内。已在允许的 `:280-300` 处追加「第二次翻转」段明确宣告前两条描述失效；越界行段登记移交（与 `:248-255` 同批）。

**r2 → r3 之间做了什么（`8c4a66a8`，仍只改新门文件，生产代码零改动）**：`tests/unit` **目录级**跑抓到本卡引入的
一条红 —— `test_production_app_maps_core_canvas_not_found_to_404` 的**断言全过**（404、由 `core_canvas_exception`
处理器产出），但被 conftest 的 W4 哨兵判红：canvas 端点的 DI 链在请求期惰性 `initialize()` 一个真
`MemoryService`，它对 `NEO4J_URI` 跑 driver health_check，命中 `('::1', 7691)` 被拦下（`blocked` 由基线 0 变 1）。
**单文件跑看不到**（该单例已被同文件别的用例初始化过 ⇒ 单跑 `blocked=0`、目录级 `blocked=1`）—— 这正是
「目录级套件必跑」的价值，也是本卡唯一一条真正被门抓住的自伤。修法与
`test_production_bugs.py::stub_lazy_service_dependencies` 同型（`get_memory_service` 覆盖成哑对象），并对两个
override **保存并恢复**原值而不是直接 `pop`（直接 pop 会删掉别的测试事先设好的覆盖）。代价如实登记：该用例
因此不再覆盖真实 `MemoryService` 初始化链。

**r3 结论与处置**：0 BLOCKER / 0 HIGH；r3 独立确认两段提交链「各只有一个提交、均只改新门文件、生产代码
零改动」，并确认 `finally` 保存/恢复在异常路径下成立、memory 哑对象未掩盖被测的分派命题。r3 的 3 MEDIUM
与 4 LOW 中，**唯一采纳的是 LOW-4 的后半条**：新门文件头 docstring 自称「替换了哪些真实现（如实全列）」
却漏列 `get_canvas_service` / `get_memory_service` 两个 DI 覆盖（用例级 docstring 已列）。该修正是
**纯 docstring 改动**，按 **D-32** 不计入 D-15 轮次、不触发再审；等价证明：去掉全部 docstring 后
`ast.dump` 逐字符相同 = **True**（非 docstring 行 diff 为空）。其余条目登记不改，理由与 r2 同族（另新增两条
门缺口，已进「本卡未证明什么 ⑫⑬」）。

**r3 → r4 之间（`c2789bd2` 纯 docstring + `9e034d60`）**：`9e034d60` 是本卡最重要的一次自我纠错。
`8c4a66a8` 那版 W4 修法**无效**（目录级 `blocked` 仍为 1），而我当时把根因判成「少覆盖了一个依赖」。
真根因是**覆盖键的对象身份漂移**：`tests/unit/test_cross_canvas_removal.py:39` 会
`importlib.reload(app.dependencies)`，字母序在本文件之前 ⇒ 目录级跑里
`app.dependencies.get_canvas_service` 已是**新**对象，而 `canvas.py` 的路由在 import 时绑定的是**旧**对象。
拿新对象当键 = 覆盖了一个没人要的键，请求照样走真 `CanvasService`（它读 `settings.canvas_base_path`，
并在依赖里惰性初始化真 `MemoryService` 连 7691）。⚠️ **断言仍然全过** —— 真 `CanvasService` 对不存在的
白板抛的是同一个异常 —— 所以只有 W4 哨兵看得见。两层修法：覆盖键改取 `canvas.py` 路由**自己绑定**的那个
函数对象（`CanvasServiceDep.__metadata__[0].dependency`，对 reload 免疫）+ `monkeypatch` 换掉
`app.services.memory_service.get_memory_service` 模块属性兜底（`get_canvas_service` 体内是运行时 import）。

**r4 → r5（`6d8e4ee0`）**：采纳 r4 LOW-1 —— 上面那条用例**分不清 404 是替身产出的还是真服务产出的**，
于是「覆盖键失配」这种情况可以让门保持全绿（`8c4a66a8` 那次正是如此）。加**排他命中断言**：
替身记录调用，在状态码断言**之前**先断 `substitute_calls == ["exc-wire-missing"]`。负控段⑥重跑证明：
把键改回「现取」并拆掉兜底后，红落在这条命中断言上，文案直指「覆盖键失配了，这个 404 是真
CanvasService 产出的」。

**措辞纠正（采纳 r5 的最后一句）**：本验收单先前把剩余条目笼统写成「全部只是门缺口」并不准确。
准确表述是：**`app.exceptions` 族的 500 确有现存的条件性原文直出路径**（`to_dict()` 不脱敏），
本卡未证明的是**它在当前生产是否可达**（`backend/app` 内该族 `raise` 站点实测为 0）。其余条目才是
门未覆盖的路径。

**为什么在第 5 轮停下**：D-15 的轮次上限是 5，本卡**用满 5 轮**：r5 绑最终 HEAD `6d8e4ee0`、BLOCKER/HIGH = 0，且 r5 明确回答了
「有没有哪一条应当升级为 BLOCKER/HIGH」—— 没有。协议 §1 对 MEDIUM/LOW 是**登记不阻断**。
r5 同时确认延期处置的两条理由（协议允许登记、部分行段越界）**作为延期理由成立**，只是不能当作严重性判断。
继续补门会把判据变成开放式（每轮都能再举出一个没锁的反事实），而每轮整改都要重跑全套承重裁判并重新绑定终审。

### 4-B 用户侧（零技术词）

后端出错时给到我这边的提示，不再把电脑里的文件路径和内部报错原文整段抖出来了，只告诉我出了哪一类错、外加一个可以拿去报修的编号；白板不存在的时候也不再被当成「服务器崩了」，而是明确说「没找到这块白板」。

- **我做 X → 我看到 Y → 我感觉 Z**（1）：我去打开一块并不存在的白板 → 界面回的是「没找到」而不是一片红色的崩溃提示 → 我感觉这是我自己点错了、不是软件坏了，知道下一步该干嘛。
- **我做 X → 我看到 Y → 我感觉 Z**（2）：我在复习面板上碰到一次后台故障 → 提示里只剩一句「出错了」加一串编号 → 我感觉安心，因为屏幕上不再出现我电脑里的目录名，截图发给别人也不尴尬。
- **我做 X → 我看到 Y → 我感觉 Z**（3）：我把那串编号报给维护的人 → 对方说照着编号能在日志里查到完整原因 → 我感觉「信息没丢，只是不给我看」，这比什么都不说更让人放心。

## 二b 卡文完成条件 (a)-(p) 对照

| 条 | 要求 | 状态 | 证据 |
|---|---|---|---|
| (a) | 第 0 分钟 | ✅ | HEAD=`9c4e7e82`、`git status` 空、BASE 33、`test -x $P` 自证、unit 开工基线跑法与基线头第 3 行逐字同 |
| (b) | 先红 | ✅ | 接线门 grep 0 行、脱敏门 1、新门 5 红 1 绿（层序用例如期就绿）、`1cbf9ae9` 改前 xfailed |
| (c) | core 族处理器 + 开关 | ✅ | `core_canvas_exception_handler` + `_CORE_STATUS_RULES` + `override_fastapi_defaults` keyword-only |
| (d) | main.py 体脱敏 + 注释 + 接线 | ✅ | `+` 行 807-808 / 819-829 ⊆ :702-830 |
| (e) | review.py reason 泛化 | ✅ | `+` 行 1508-1509 / 1516-1517 ⊆ :1505-1518 |
| (f) | 结构判据成对 + AST + 验伪锚 | ✅ | 九项全部翻转，锚 5→7（≥4） |
| (g) | 新门 7 组 | ✅ **8 组** | 卡文 7 项中 ⑥（`1cbf9ae9` 转正）前提不成立，换成「生产 app 404 化」用例；另按 Codex r1 加 core 族六档门 |
| (h) | pyright 保持 0 | ✅ | 改前改后同为 `0 errors, 80 warnings`；未用 `LEFTHOOK_EXCLUDE=python-typecheck` |
| (i) | 点名套件 + regression/unit 目录级只减 | ✅ | 见 §二 4-A 第 7 节（含中途一次 `>` 的完整登记与修复） |
| (j) | openapi 不入 commit | ✅ | 六个 commit 命中数全 0，累计 diff 空，再生仅 `x-generated-at` |
| (k) | 负控三段 | ✅ **六段** | ①②③（卡文指定）+ ④⑤（core 族门）+ ⑥（覆盖键） |
| (l) | 地盘核 | ✅ | 恰 6 文件，全部在白名单内 |
| (m) | 现网只读 | ✅ | 全程进程内 `TestClient`；终局哨兵 `blocked=0`；live vault 零改动 |
| (n) | Codex 多轮 | ✅ | 五轮用满，末轮绑最终 HEAD，BLOCKER/HIGH = 0 |
| (o) | 提交 | ✅ | 6 个代码 commit，header 全 ≤100，`*.stderr*` 未入库，未 push |
| (p) | 未证明/台账各 ≥4 | ✅ | 未证明 13 条、台账 17 条 |

## 三 本卡未证明什么（≥4）

1. **未证明 4xx 业务文案在恶意输入下无反射面**。core 族 404/400 体的 `message` 与 `details` 回显的是调用方传入的 `canvas_name` / `node_id`（实测 7 个 raise 站点传的都是调用方输入，`canvas_service.py:190` 明确拒绝绝对路径），但本卡**没有**对该回显做转义 / 长度 / 内容审查的门。
2. **未证明真实 uvicorn 下的表现**。`Exception` 处理器接上后「外三层中间件自身抛异常」这条路径只在 `TestClient` 下验过（`ServerErrorMiddleware` 调用 handler 后仍 `raise exc` 是 Starlette 的既有行为，改前改后一致）；未在真实 uvicorn 进程上观测过。
3. **未证明插件 / 前端没有把「500 + 原文」当功能依赖**。只在仓内测试面证明无依赖（`safe_message` 在 `backend/tests` 的 6 处命中全是 docstring / 注释，零断言）；仓外消费者（Obsidian 插件、前端）未核。
4. **未证明 `ErrorHandlerMiddleware`（`app/middleware/error_handler.py`）与 `test_cors_exception.py` 里两份复刻中间件的去留**。两者同样零接线 / 非生产类，本卡登记不改。
5. **未证明 `review.py` 另 7 处 `HTTPException(detail=…str(e))` 的 `detail` 是否泄漏路径**（:1605/:1661/:1717/:1802/:1812/:1900/:1907）——相邻面，本卡硬边界禁碰。
6. **未证明 `openapi.json` 再生 diff 在主 session 集成期确实只有 `x-generated-at`**。车道只能跑一次 `check-openapi-drift.py --write` 取输出作证，集成期的再生结果由主 session 复核。
7. **未证明 β（D-38 legacy 兼容重做）方向**——不排本批。
8. **未证明响应头零泄漏**（Codex r2 MEDIUM-2）。本卡的门只断言 CORS 头**存在**；把 core 500 的头改成
   `headers={"X-Request-ID": str(exc)[:100]}` 这类对照输入，状态码 / JSON 体 / 日志全不变，现有断言照过。
   当前代码的头无异常文本数据流（`X-Request-ID` 取自 `request.state.request_id`，CORS 取自 Origin 白名单），
   但**没有门锁住这一点**。
9. **未证明 core 4xx `details` 的属性白名单被锁住**（Codex r2 MEDIUM-3）。`_core_exception_details` 当前是
   `canvas_name` / `node_id` / `field` 三键白名单，但把它换成 `vars(exc)` 不会让任何现有用例变红 ——
   给异常挂一个白名单外的属性（如 `exc.server_path = "/srv/private/…"`）就会随 4xx 体出去。
10. **未证明 `test_bug_bug_1cbf9ae9` 声称的那个 bug 现在是什么状态**。该用例被本文件 autouse fixture 的
   同步 `MagicMock` 挡在 `TypeError` 上，既证不了旧 bug 还在、也证不了已修；本卡只把它的 `reason` 改成实况，
   没有修 fixture（越界）。
12. **未证明 core 族「已登记异常的子类继承状态码」在另外两支上也成立**（Codex r3 LOW-2）。六档门只给
   `CanvasNotFoundException` 造了子类；把 `NodeNotFoundException` / core `ValidationError` 两支的
   `isinstance` 换成精确类型查表，它们的子类会从 404/400 掉到 500，而现有门不红。
13. **未证明 core 500 体与 `generic_exception_handler` 的「逐字同形」**（Codex r3 LOW-3）。六档门没有比较
   完整键集；给 core 500 体加一个不含哨兵的额外字段仍会全绿。长消息在 core 500 这条记录路径上的诊断完整性
   也未覆盖（6000 字符样本走的是中间件那条记录调用）。
14. **未证明 u9c 越界行段（`:248-255` / `:283-284` / `:315-317` / `:338`）的过期描述不会被后人当成当前证据**
   （Codex r2 LOW-5）。已在允许改的 `:280-300` 处宣告前述两条描述失效，但那几处文字本身未改。

## 四 台账待登记条目（≥4）

1. **修复 SHA**：代码面六个 commit `0707be32` → `7d3bdc2b` → `8c4a66a8` → `c2789bd2`(纯 docstring) →
   `9e034d60` → `6d8e4ee0`（终）。结构门 0→1 / 1→0 的成对证据见 §二 4-A 第 1 节；
   新门 nodeid = `tests/unit/test_exception_handlers_wire.py`（8 条，全绿）；
   u9c 用例改名 `test_production_stack_exposes_message_in_500_body` →
   `test_production_stack_redacts_message_in_500_body`；
   ⚠️ **`1cbf9ae9` 的 xfail 是「保留 + 改 reason」，不是卡文预期的「去标转正」**（理由见 §二 4-A 第 4 条）。
2. **手册 §零.8「`backend/app/main.py` 本批零写者」与 §一.2 / 清单「P8 唯一写者，只改 :702-830」口径冲突**，本卡按后者执行，请主 session 统一手册文案。
3. **清单 territory 漏列两份必改测试**（`test_u9c_startup_rejection_eval.py` / `test_production_bugs.py`），已进本卡 (l) 白名单。
4. **G-FAKE 同族登记**：`exception_handlers.py:28` 绑的 `app.exceptions.CanvasException` 与生产 raise 的 `app.core.exceptions` 族是两套层级；`app.exceptions/**` 在 `backend/app` 只剩 2 处 import（`exception_handlers.py:28`、`middleware/error_handler.py:26`）且原先都未接线。本卡只新增 core 族处理器，**不删**旧层级；退役 / 合并另立卡。
5. `ErrorHandlerMiddleware` 零接线 + `test_cors_exception.py` 两份复刻中间件（DD-03 面）登记不改。
6. **openapi 待主 session 集成期再生**：本卡 commit 不含 `backend/openapi.json`，`LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root` 的原始输出见 §二 4-A。
7. `review.py` 另 7 处 `detail=…str(e)` 相邻面移交。
8. **α 若用户后裁「保留原文」**，回退点 = 本卡 commit 的两处 dict 字面量（`main.py` 中间件体、`exception_handlers.py` core 族 500 体）+ 一行 f-string（`review.py` 的 `reason`）。
9. **u9c `_build_probe_app` 的 :248-255 注释已随本卡失实**（它写「生产 main.py 的注释写 CORSExceptionMiddleware ← 最外层是错的」——生产注释本卡已更正）。该行段**不在**本卡 (l) 白名单，未改；移交主 session 或下一张碰该文件的卡。
10. **Codex 两轮**：r1 存档 `_bmad-output/审查/codex-review-CARD-EXC-HANDLER-WIRE-REDACT.md`（绑 `0707be32`，
    0B/0H/4M/2L）；r2 存档 `…-r2.md`（绑 **`7d3bdc2b`** = 最终 HEAD，0B/0H/3M/2L）。r1 采纳三条（只改新门文件）
    即 commit `7d3bdc2b`；r2 五条全部登记不改，逐条理由见验收单 §二 4-A 第 9 节。
11. **`test_production_bugs.py::test_bug_bug_1cbf9ae9` 是一道测不到自己命题的门**（本卡实测）：本文件 autouse
    fixture 把 `get_canvas_service` 覆盖成**同步** `MagicMock`，端点 `await` 它先抛 `TypeError`，请求走不到
    `CanvasNotFoundException`。本卡只改了它的 `reason` 文案（白名单内），**未修 fixture**（越界）。
    建议下一张碰该文件的卡把 fixture 换成 `AsyncMock` 并重验该 bug 的真实状态。
12. **卡文行号漂移登记**：`exception_handlers.py` 的四行 `add_exception_handler` 实测在 **:309-312**（卡文写
    :306-309），`logger.info` 在 **:314**（卡文写 :311）—— 差额是 TAIL T6 的三行 `cast` 说明注释。
13. **卡文 (g)① 的身份断言写法有误**：`m.app.exception_handlers[HTTPException]` 用 `fastapi.HTTPException` 当键会
    `KeyError`，生产表里的键是 `starlette.exceptions.HTTPException`。本卡门改为「starlette 键身份 `is` FastAPI
    默认函数 **且** `fastapi.HTTPException` 不在表里」。
14. **⚠️ 跨卡可复用的工程教训（建议进批级手册）**：`app.dependency_overrides` 的键是**函数对象**，
    而 `tests/unit/test_cross_canvas_removal.py:39` 会 `importlib.reload(app.dependencies)` —— 字母序在它之后的
    任何测试，若用 `from app.dependencies import X` 现取当键，覆盖会**静默失效**（端点模块 import 时绑的是旧对象）。
    症状是**单文件跑绿、目录级红**，且**断言可能全部通过**（真依赖对同一输入抛同一异常），只有副作用门
    （W4 哨兵的 `blocked` 计数）看得见。修法：键取路由自己绑定的 `XxxServiceDep.__metadata__[0].dependency`，
    被覆盖依赖体内若是运行时 import 则再用 `monkeypatch` 换模块属性兜底，并给替身加**命中断言**。
15. **Codex 五轮用满**（D-15 上限）：r1 `0707be32` 0B/0H/4M/2L → r2 `7d3bdc2b` 0B/0H/3M/2L →
    r3 `8c4a66a8` 0B/0H/3M/4L → r4 `9e034d60` 0B/0H/3M/5L → r5 `6d8e4ee0`（末轮，绑最终 HEAD）0B/0H/3M/4L。
    代码 commit 共 6 个（其中 `c2789bd2` 为纯 docstring，D-32 判等价：去 docstring 后 `ast.dump` 逐字符相同 = True）。
16. **协议 §2 禁用措辞的口径冲突（如实登记）**：卡文 (n) 要求「prompt **与存档**不得出现四个禁用措辞」。
    实测 —— 五份 prompt 侧命中 **0**（我控制的部分合规）；但 Codex **回复正文**里出现了「构造」×3、
    「绕过」×4（例如「需要代码动态构造这种类型」「绕过 generic 500 脱敏」），全是它自己的行文。
    协议 §2.1 同时要求存档「正文一字不改」。两条相冲时按 §2.1 处理：**不修改审查存档原文**
    （篡改审查记录比措辞更严重）。请主 session 裁定该条文的准确口径。
17. **u9c 的三处越界过期注释**（`:248-255` / `:315-317` / `:338`，以及 `:283-284` 的 1./2. 条目）仍写「生产从未调用
    `register_exception_handlers`」「生产注释写最外层是错的」——生产已接线、注释已更正，这些描述已失实。
    不在本卡 (l) 白名单，移交。
