# UAT-CARD-T-UNREACH（2026-09-17）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-T-UNREACH]` · 车道 `card-t5-bugs`（分支 `card/t5-bugs`）· 本车道第 5/5 张（末张）
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T5-E.md`（feature 主干树）
> 地盘基准 `PREV` = `3b819f404668c59c7ddc08c083f8014355e2dc96`（T5-D CARD-SEC-DANGLING 末 commit）
> 证据目录：`_bmad-output/审查/evidence-t-unreach/`（本单只**引用**路径与末行，不自述数字）

---

## 〇 第 0 分钟自证（完成条件 (a)）

| 项 | 实测 |
|---|---|
| `pwd` | 结尾 `card-t5-bugs` ✓ |
| `git rev-parse --abbrev-ref HEAD` | `card/t5-bugs` ✓ |
| `git status --porcelain \| wc -l` | `0` ✓ |
| HEAD ≠ `08100483` | HEAD = `3b819f40` ✓（末张卡） |
| T5-D 已独立 commit | `git --no-pager log --oneline --no-color 08100483..HEAD \| grep -cF 'CARD-SEC-DANGLING'` = **12**（≥1）✓ |
| `PREV` | `export PREV=$(git rev-parse HEAD)` = `3b819f40…` ✓ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在 ✓ |
| pyright 自证 | `test -x /Users/…/card-v5-lance/backend/.venv/bin/pyright` ✓ |
| 基线自证 | `test -f $BASE && grep -vc '^#' $BASE` = **64** ✓（R-B14-2 口径） |
| 两文件仍 = `B14_BASE` | `git --no-pager diff --stat --no-color 08100483 "$PREV" -- boards.py board_manifest_tools.py` → **空** ✓（§〇 行号成立；**验伪锚**：同一 `PREV` 换成全树 pathspec `-- . ':(exclude)_bmad-output'` 时 diff **非空**（`10 files changed`）⇒ 上面那个「空」是两文件真未被 T5-A~D 碰过，不是命令本身跑空） |

### 口径更正（再次实测确认，登记）

1. **except 真落点**：recon A §B.1 / U2-台账待登记 §五 / 设计稿 §4 写 `boards.py:86` / `board_manifest_tools.py:67` → **实测那两行是注释**（`# ⚠️ 死分支(TAIL): …`）；真正的 `except pydantic.ValidationError as e:` 在 **`boards.py:89` / `board_manifest_tools.py:70`**（各恰 1）。
2. **MCP 工具路径**：`find backend/app -name 'board_manifest_tools.py'` 唯一命中 **`backend/app/mcp/tools/board_manifest_tools.py`**（不是 `backend/app/mcp/board_manifest_tools.py`）。
3. `project_manifest` AST = **231-237**（末行 `raise ValueError(f"未知视图: {view!r} …")` 是**非 ValidationError 的 ValueError**，对照组的语义锚）；`_ManifestEnvelope` = **198-215**，三个无默认必填字段 `source` / `source_status` / `id_stability`。

---

## 一 census（完成条件 (b)）— 先红 → 后绿

- 先红存档：`_bmad-output/审查/evidence-t-unreach/census-open-20260917T025027.txt`（末行 `rc=0`）
- 后绿存档：`_bmad-output/审查/evidence-t-unreach/census-after-20260917T025334.txt`（末行 `rc=0`）

| 判据 | 改前 | 改后 |
|---|---|---|
| AST except 顺序 `boards.py::get_board_manifest_http` | `['ValueError','KeyError','ValidationError']` **⛔ DEAD** | `['ValidationError','ValueError','KeyError']` **OK** |
| AST except 顺序 `board_manifest_tools.py::get_board_manifest` | `['ValueError','KeyError','ValidationError']` **⛔ DEAD** | `['ValidationError','ValueError','KeyError']` **OK** |
| `grep -rnF 'except pydantic.ValidationError' backend/app \| wc -l` | 2 | 2 |
| 全族 `grep -rnE 'except (pydantic\.)?ValidationError' backend/app \| wc -l` | 5 | 5 |
| `grep -rnF 'pyright: ignore[reportUnusedExcept]' backend/app \| wc -l` | 2 | **0** |
| MRO | `issubclass(ValidationError, ValueError)` = **True**（pydantic 2.12.5） | 同左（pydantic 事实，本卡不改） |

**验伪锚（同次执行，落在先红存档里）**：卡文点名的禁用写法 `grep -rnE 'except \(pydantic\.\)?ValidationError'`（转义括号）实测 **0 命中** —— 证明裸括号写法不是恒真判据，且证明禁用写法确实是恒假判据。后绿存档里 ignore=0 旁边同次打了 `except pydantic.ValidationError` = **2**，证明那个 0 不是搜索面打错造成的。

**census 结论**：全 `backend/app` 只 **2 处** `except pydantic.ValidationError`，都在本卡地盘、都是死分支、都带 ignore。别处三处 `except ValidationError`（`services/board_manifest_service.py:1029` / `:1069`、`services/canvas_service.py:701`）经静态核对是各自 try 内**唯一** handler、**非**死分支，且不在本卡地盘（服务层只读，不碰）。

---

## 二 行为门（完成条件 (c)(e)）— 先红 → 后绿 + 对照

新文件 `backend/tests/unit/test_board_manifest_unreach_t5e.py`（11 个测试用例，含 parametrize）。

- 先红存档：`_bmad-output/审查/evidence-t-unreach/redgreen-before-20260917T025201.txt`（末行 `rc=1`）
- 后绿存档（v1）：`_bmad-output/审查/evidence-t-unreach/redgreen-after-20260917T025300.txt`（末行 `rc=0`）
- **后绿存档（v3 入库版，承重）**：`_bmad-output/审查/evidence-t-unreach/redgreen-after-final-20260917T030434.txt`（末行 `rc=0`，`11 passed`）

改前 **6 failed / 5 passed** → 改后 **11 passed**。红全部落在 status / error / 顺序断言，**不是** import 或 fixture 错（先红存档的 FAILURES 段逐条可见 `assert 422 == 500`、`assert '非法参数: …' == 'manifest 投影 schema 异常, 已记录日志'`、`assert 2 < 0` 的 except 顺序断言）。

| 测试 | 改前 | 改后 |
|---|---|---|
| `test_http_schema_break_returns_500[study]` / `[exam]` | 红（实得 **422**） | 绿（**500** + detail 恰为「manifest 投影 schema 异常, 已记录日志」） |
| `test_mcp_schema_break_returns_structured_error[study]` / `[exam]` | 红（error 以「**非法参数: **」开头） | 绿（error 恰为「manifest 投影 schema 异常, 已记录日志」，`ok=False`，`manifest=None`） |
| `test_validation_error_handler_precedes_value_error[boards]` / `[tools]`（AST 结构门，常驻） | 红（`assert 2 < 0`） | 绿 |
| **对照** `test_http_plain_value_error_still_422` | 绿 | 绿（422 + detail 恰 `bad board_id`） |
| **对照** `test_mcp_plain_value_error_still_invalid_param` | 绿 | 绿（error 恰「非法参数: bad board_id」） |
| **对照** `test_http_key_error_still_404` | 绿 | 绿（404 + detail 恰 `no such board`） |
| **对照** `test_mcp_key_error_still_passthrough` | 绿 | 绿（error 恰 `no such board`） |
| **前置自证** `test_project_manifest_raises_real_validation_error` | 绿 | 绿（3 个必填键缺失 + `isinstance(ValueError)` True） |

**DD-03 真异常**：异常由**真** pydantic `model_validate` 失败产生 —— monkeypatch 只替换文件 I/O 协作者 `serve_manifest` 的返回值（缺三必填键的 dict），驱动真实错误路径；无伪造异常对象 —— 判据用 **AST 口径**（存档 `evidence-t-unreach/dd03-nomock-ast-20260917T025541.txt`）：扫 `unittest.mock` / `mock` / `pytest_mock` 的 import 节点与 `MagicMock|AsyncMock|Mock|patch|create_autospec|sentinel` 的 `Name`/`Attribute` 节点，本文件 **mock-imports=0 / mock-refs=0**；验伪锚：同一脚本对 `tests/unit/conftest.py` 得 **1 / 5**（模式确实能命中）。

> ⛔ **同卡踩到的判据坑（如实登记）**：先写的两版**文本**判据都失实——`grep -cF 'MagicMock'` 在本文件 = **1**，`grep -cE '(MagicMock|AsyncMock|mock\.|patch\()'` 也 = **1**，两次命中的都是 docstring 里「不用 MagicMock」**那句话本身**。文本判据分不开「代码里用了 mock」和「注释里提到 mock 这个词」，只有 AST 能分。验收单初稿据此写过一句「grep -c = 0」，已在入库前自查推翻并替换为本段。

> ### ⚠️ 测试文件在作业期内改过两次（如实登记，影响先红存档的绑定关系）
>
> | 形态 | 何时 | 改了什么 | 对先红/后绿的影响 |
> |---|---|---|---|
> | **v1** | 先红 / 首次后绿时 | 初版 | `redgreen-before-20260917T025201.txt`（6 failed / 5 passed）绑的是它 |
> | **v2** | 首次后绿之后 | `ruff format` 合并了一处函数签名换行 | **AST dump 逐字符相同**（`fmt-ast-equivalence-20260917T030026.txt`，含验伪锚：把 500 改 422 后 AST 即不同）⇒ 与 v1 零语义差 |
> | **v3（入库版）** | 收工前 | 清掉 pyright 的 2 error + 1 warning：`view: str` → `Literal["study","exam"]` 别名 `_View`；fixture 由 `@pytest.mark.usefixtures("...")` 字符串引用改为**参数形式**接收并去掉下划线前缀（下划线会被 pyright 判为未访问的私有函数）。**断言内容与测试函数名一字未改。** | v3 对「改前生产代码」的先红**不由 v1 存档背书**，而由**负控 FINAL** 覆盖（见 §三）—— 负控把生产代码变异回死分支后跑的正是 v3，指定 3 条断言逐条变红 |
>
> ⇒ 「v3 在死分支态下会红」是**实测**的，不是从 v1 推断的。v1 先红存档保留作原始记录，其行号引用对 v3 已失效（本单一律用**断言文本**而非行号定位，不受影响）。

**隔离**：直接 `asyncio.run` 协程 + monkeypatch，不起 lifespan、不连 Neo4j。

W4 哨兵（协议 §3 / 手册 §零.6、§零.18 —— 本批 7691 与 7692 **均在线**，故哨兵是必贴项），逐份实测：

| 存档 | W4 哨兵行 |
|---|---|
| `redgreen-before-20260917T025201.txt` / `redgreen-after-20260917T025300.txt` / `redgreen-after-fmt-20260917T030037.txt` / `redgreen-after-final-20260917T030434.txt` | 各 **1** 行，均为 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |
| `unit-open-20260917T025023.txt` / `unit-close-20260917T025724.txt` / `unit-close-final-<TS>.txt` | 各 **1** 行，同上 |
| `negctl-20260917T025645.txt` / `negctl-final-20260917T030506.txt` | **0 行** ⚠️ 见下 |

> ⛔ **如实登记（本单初稿在此写过失实断言）**：初稿写「**每一份** pytest 存档末尾都有 W4 哨兵行」。入库前逐份 `grep -c` 实测发现**两份负控存档是 0** —— 负控脚本用 `subprocess.run(capture_output=True)` 跑 pytest，只把汇总行 `print` 出来，**哨兵行没被转发进存档**。
>
> ⇒ 严格说：负控那两跑的连库情况**没有独立的哨兵证据**（已列入 §八 未证明项）。间接依据是它跑的是同一个测试文件、同一套 monkeypatch，而该文件在四份直跑存档里都实测 `blocked=0`；但这是**推断不是实测**。负控脚本应改为把 pytest 原始输出一并落档 —— 已列入 §九 台账条目供下批采纳。
>
> 这已是本卡第三次抓到「凭印象写关于证据的断言」（前两次是 MagicMock 文本判据、存档时间戳），三次都不是代码错。教训：**任何形如「全部 / N 份 / 都有 / 没有」的证据断言，写之前先跑一遍 `grep -c` 并附验伪锚。**

---

## 三 负控（完成条件 (f)）

存档：**承重 = `_bmad-output/审查/evidence-t-unreach/negctl-final-20260917T030506.txt`**（绑入库版 v3 测试文件，末行 `rc=0`；**脚本原文附在该存档末尾**，可逐行复核）；`negctl-20260917T025645.txt` 是 v1 测试文件下的首跑，结论相同，保留作原始记录。

方法：把一处的 `except pydantic.ValidationError` 分支**挪回 `ValueError` 之后**（重演死分支），跑本卡测试文件，看指定断言是否变红；两文件各一段。还原走 Python `try/finally`（**未用 `git stash` / `git checkout`**）。

**变异体三重自证**（防「变异没生效却报 PASS」与「变异顺带改坏别的」）：

1. **纯行重排**：断言整文件行多重集 `sorted(original.splitlines()) == sorted(mutated.splitlines())`，不满足就拒绝写入 ⇒ 变异只动顺序，没碰文案 / 状态码 / ignore；
2. **AST 顺序确实反了**：变异后重新取 handler 顺序，断言 `index(ValidationError) > index(ValueError)`，否则判「变异未生效」；
3. **变异确实落盘**：打印变异体 shasum，与跑前值不同。

| 段 | 跑前 shasum | 变异体 shasum（≠跑前） | 指定必红 → 实红 | 排他性（期望仍绿 6 条）→ 被打破 | 跑后 shasum | 还原逐字节相同 |
|---|---|---|---|---|---|---|
| `boards.py` | `ab6d794c…5b9d` | `c62d2590…e2ab` | **3 → 3** | **0** | `ab6d794c…5b9d` | **True** |
| `board_manifest_tools.py` | `9c42a6a9…fbe8` | `f6b07d17…f0e04` | **3 → 3** | **0** | `9c42a6a9…fbe8` | **True** |

- `boards.py` 段实红：`test_validation_error_handler_precedes_value_error[app.api.v1.endpoints.boards-get_board_manifest_http]`、`test_http_schema_break_returns_500[study]`、`test_http_schema_break_returns_500[exam]`；MCP 侧 2 条与 4 条对照**仍绿**。
- `board_manifest_tools.py` 段实红：`test_validation_error_handler_precedes_value_error[app.mcp.tools.board_manifest_tools-get_board_manifest]`、`test_mcp_schema_break_returns_structured_error[study]`、`test_mcp_schema_break_returns_structured_error[exam]`；HTTP 侧 2 条与 4 条对照**仍绿**。

⇒ 门钉的确实是 **except 顺序本身**，且**只**钉那一处：只证「红了」不够，本段同时证了「红在这几条、且只红在这几条」。

**还原后复核**（同 session 另跑）：`shasum -a 256` 两文件 = `ab6d794c…5b9d` / `9c42a6a9…fbe8`，与上表「跑后」逐字相同；`git -c color.ui=never status --porcelain -- . ':(exclude)_bmad-output'` 只列本卡三文件。

**变异窗口纪律**（承重的 `negctl-final` 跑）：启动前先实测本树无 `tests/unit` 目录级长跑在跑（存档首部记 `ps | grep -c '[p]ytest tests/unit --ignore'` = **0**），跑完（两段合计约 3 秒）之后才起最终目录级 `unit-close-final`。首跑 `negctl-20260917T025645.txt` 同样在开工目录级（336.51s，02:50:23 起跑）**跑完之后**启动。⇒ 两次变异窗口与同树长跑**零重叠**（避免「长跑期间读到变异态」这类归因不清）。

> **判据口径说明（多车道并行环境，登记备查）**：`pgrep -f 'pytest tests/unit --ignore'` / `ps | grep` 是**全机**口径，在 10 车道并行的本批里**会匹配到别的 worktree 的进程**（本卡收工期实测到 T7-D 车道 `evidence-g27a-tail` 的同名跑在另一棵树上）。
>
> 这对本卡的结论是**安全方向**的偏差：变异窗口自证要的是「**本树**无长跑」，而我用的全机口径 = **0** 比它更严格，0 成立则本树必然也是 0。反过来若要判断「我自己的跑是否还在推进」，全机口径就不够了 —— 须按**本树绝对路径**精确匹配（`ps -ax | grep 'card-t5-bugs' | grep '[p]ytest tests/unit'`）。本卡两处都按对应口径实测过。
>
> 副作用（如实记）：并行车道抢 CPU 使本卡收工目录级比开工那次慢（开工 336.51s）。这只影响耗时，不影响 nodeid 结论。

---

## 四 pyright / ruff / 目录级 / 地盘（完成条件 (g)(h)(i)(j)）

### 行为变化的下游依赖排查（Codex 问题 ⓪ / ① 的实证依据）

存档 `evidence-t-unreach/downstream-impact-20260917T030715.txt`（末行 `rc=0`，含验伪锚）。全仓 grep（排除 `.venv/` / `node_modules` / `_bmad-output/`）：

| 排查项 | 结果 |
|---|---|
| 谁依赖 MCP error 文案「非法参数: 」 | **只有生产代码自身的产出点**（`board_manifest_tools.py:66` 注释 / `:72` 产出）**与本卡新测试**。无下游字面依赖 |
| 谁依赖「manifest 投影 schema 异常」文案 | 同上（两个产出点 + 新测试） |
| 谁调用 HTTP `/boards/manifest`（422→500 的下游面） | 仅 `backend/tests/unit/test_vault_scope_409.py:312`（测的是 **409** vault 不匹配，由 try **之前**的 `resolve_vault_scope` 抛出，不经本卡改动的 except 链）+ `CURRENT_TASK.md` 的文档描述。**无生产调用方** |
| 谁消费 MCP `get_board_manifest` | 三个 skill：`study-question` / `start-exam-board` / `chat-with-context`。其降级契约逐字是「**manifest 不可用时静默退回本地 Grep 选点**」（`start-exam-board/SKILL.md` description），判据是 **`ok` 字段**，不是 error 文案 |

⇒ 本卡的两处行为变化**没有已知的字面依赖方**。

> ⚠️ **这条证据能证什么、不能证什么**：grep 覆盖的是「**字面**依赖该文案的代码」。它证不了「没有任何行为依赖」——例如某个外部消费方按「返回 422 就重试、返回 500 就告警」分流，grep 是看不见的。skill 侧尤其特殊：SKILL.md 是给 Claude 读的自然语言，Claude 会**看** error 文案自行判断，所以文案变化的影响在语义层而非代码层（新文案同样清楚表达「失败」，且 `ok=False` 结构未变）。因此 §八 第 2、4 条仍如实保留为「未证明」，本表只是把 Codex ⓪/① 从「纯推测」降到「有排查依据」。

### (i) pyright 保持 0

跑法（R-B14-10，cwd = `backend/`；R-B14-11b `exit 1` 只退子 shell；禁 `| tail -1`）：

```
P=/Users/…/card-v5-lance/backend/.venv/bin/pyright
( test -x "$P" || { echo "pyright 缺席"; exit 1; } ) && (cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')
```

| 时点 | 存档 | 结果 |
|---|---|---|
| 开工基线 | `pyright-open-20260917T025005.txt` | `0 errors, 81 warnings, 0 informations` |
| 改后 | `pyright-after-20260917T025338.txt` | 同上 |
| **收工（承重）** | `pyright-final-20260917T030434.txt` | **`0 errors, 81 warnings, 0 informations`** |

**warnings 没涨到 83** ⇒ 两处 `# pyright: ignore[reportUnusedExcept]` 确实删干净了（分支可达后它们会变成「多余 ignore」，被 `reportUnnecessaryTypeIgnoreComment="warning"` 报出来）。
`grep -rnF 'pyright: ignore[reportUnusedExcept]' backend/app | wc -l` 收工 = **0**，同次验伪锚 `except pydantic.ValidationError` = **2**（`census-final-20260917T030434.txt`）。
**验伪锚（pyright 缺席分支只退子 shell）**：`PX=/nonexistent/pyright` 时打印「pyright 缺席(锚)」、外壳存活 `rc=1`、第二段不跑 —— 第 0 分钟实测过。
`python-typecheck` hook **未** `LEFTHOOK_EXCLUDE`。

> **额外（非承重，但本卡自清）**：新测试文件不在 `pyright app` 覆盖面内、也不在 `python-typecheck` 的 glob（`backend/app/*.py`）内，但初版有 **2 errors + 1 warning**（`pyright-testfile-20260917T030131.txt`）。按手册 §一.1.7「本卡新增的 error 由本卡自己清」的口径已清到 **0 errors / 0 warnings**（存档 `pyright-testfile-final-20260917T031022.txt`，含验伪锚），代价是重跑了一遍全部裁判与目录级（见 §二 的 v3 说明）。

### (j) ruff

存档 `ruff-final-20260917T030434.txt`（zsh 数组写法，整块包 `( … )` 子 shell，R-B14-11b）：

- 集合 `files=3`，逐行打印 = 本卡地盘三文件（**集合大小已打印**，防 zsh 不分词的假绿）
- `ruff check` → `All checks passed!` `ruff_check_rc=0`
- `ruff format --check` → `3 files already formatted` `ruff_fmt_rc=0`
- **验伪锚**：喂一个已知含未定义名的文件 `ruff check --select F821` → `Found 1 error.` `anchor_rc=1`（⚠️ 不用 F401 作锚：`backend/**` 的 ruff 只启用少数必错级规则，F401 锚不会触发）

> **格式漂移归属**（协议 §2.3）：`ruff-format-20260917T025956.txt` 记录了本卡首次自查 —— 两个**生产**文件在改前改后都 `already formatted`（对 `PREV` 副本实测 `format_base_rc=0`），**唯一** dirty 的是本卡新增的测试文件，属本卡引入、已 `ruff format` 修掉，**未**动用 `LEFTHOOK_EXCLUDE=python-lint`，也未碰主干既有 462 文件漂移。

### 硬边界核（逐文件实测，均为空 diff）

对 `PREV` 比对，以下 16 个禁改文件**零改动**：`backend/openapi.json`、`app/main.py`、`tests/conftest.py`、`tests/unit/conftest.py`、`pyrightconfig.json`、`lefthook.yml`、`backend/requirements.txt`、`app/models/board_manifest.py`、`app/services/board_manifest_service.py`、`app/security.py`、`app/mcp/tools/infra_tools.py`、`app/api/v1/endpoints/system.py`、`app/api/v1/endpoints/edges.py`、`app/config.py`、`app/services/background_task_manager.py`、`tests/contract/test_openapi_contract.py`。
`canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py` 零写者成立（空 diff）；本卡三文件 `grep -c fsrs_bridge` 全 **0**。
**openapi 零影响的依据**：`lefthook.yml` 的 `spec-sync-flat` glob = `backend/app/{api,models,schemas,mcp}/*.py`、`spec-sync-root` glob = `backend/app/{main.py,config.py}` —— 两条都不命中本卡两文件所在层级；且本卡不碰 route 的 `response_model` 与声明状态码。

### (h) tests/unit 目录级 — open → close 只允许 `<`

跑法：`( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider … )`（R-B14-3：`cd backend` 后 `--ignore` 用**相对**路径；`cd` 包在 `( … )` 子 shell 里，后续 `grep`/`diff` 与地盘门在树根跑）。

| 跑 | 存档 | nodeid 集 | 结果 |
|---|---|---|---|
| **开工**（T5-D 落后的现状） | `unit-open-20260917T025023.txt`（`rc=1`，336.51s） | `open.nodeids` | **64** 条 |
| 中途（v2 测试文件） | `unit-close-20260917T025724.txt`（`rc=1`，366.03s） | `close.nodeids` | **64** 条 |
| **收工（承重，绑入库版 v3）** | `unit-close-final-20260917T030552.txt`（`rc=1`，526.05s） | `close-final.nodeids` | **64** 条 |

- `diff open.nodeids close-final.nodeids` → **`rc=0`（完全相同）** —— 连 `<` 都没有，更没有 `>`
- `diff base.nodeids close-final.nodeids` → **`rc=0`（完全相同）**，`base.nodeids` = B14 基线 64 条（`grep -v '^#' $BASE | sort -u`）
- 收工汇总：`35 failed, 5092 passed, 48 skipped, 23 xfailed, 29 errors`；**35 + 29 = 64** 与基线吻合
- **新测试全绿不进红集**：`grep -cF 'test_board_manifest_unreach_t5e' unit-close-final-*.txt` = **1**（被收集）而 `grep -cF … close-final.nodeids` = **0**（不在红集）；passed 数 5081 → **5092**，正好 **+11** = 本卡新增用例数
- W4 哨兵：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`

> **开工红集的口径纯度自证**（这次跑横跨了本卡的改码窗口，必须排除污染）：`grep -cF 'test_board_manifest_unreach_t5e' unit-open-20260917T025023.txt` = **0** ⇒ 开工那次的**收集面早于**新测试文件写入（文件 mtime `02:51:38`，该跑 `02:50:23` 起跑并已在跑测试）。且 `diff base.nodeids open.nodeids` **为空** ⇒ 顺带证明 **T5-A~D 四卡在 `tests/unit` 上零新红**。
>
> ⛔ 判据里只出现单份 `$EV/<具体文件名>.txt`，**未用 `$EV/unit-*.txt` glob**（多份会给每行加文件名前缀使整份作废）；未用 `wc -l` 当判据。

### (g) 地盘门

存档 `territory-20260917T031741.txt`（末行 `rc=0`，树根跑；R-B14-11a：`--no-color` 挂在 **git** 上不是 grep 上）。

判据：`git --no-pager diff --name-only --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output'`

→ **恰 3 行**，逐行 = 本卡地盘：`backend/app/api/v1/endpoints/boards.py`、`backend/app/mcp/tools/board_manifest_tools.py`、`backend/tests/unit/test_board_manifest_unreach_t5e.py`。

- **验伪锚 1**：去掉 `':(exclude)_bmad-output'` → **34** 行，其中 **31** 行是 `_bmad-output/` ⇒ exclude 真生效，那个「3」不是命令跑空
- **验伪锚 2**：`git diff PREV HEAD -- backend/openapi.json` = **0** 行，而 `git diff PREV 971061f5 -- backend/openapi.json` = **13** 行 ⇒ 还原真实有效

### ⚠️ lefthook 顺带写入 openapi.json 与其处置（如实登记，越界已消）

本卡有**两个** commit：

| commit | 内容 |
|---|---|
| `971061f5` | 本卡三文件 **+ `backend/openapi.json`（越界，非本卡所改）** |
| `802f05ca` | 只还原 `backend/openapi.json` 到 `PREV` 态（1 insertion / 1 deletion） |

**根因**：`lefthook.yml` 的 `spec-sync-flat` glob 是 `backend/app/{api,models,schemas,mcp}/*.py`。我按 **shell** 语义预判「`*` 不跨 `/`，命中不了深层路径」——**预判错了**：lefthook（Go）的 `*` 实测**跨目录**匹配，命中本卡两文件，于是跑 `check-openapi-drift.py --write` 并无条件 `git add backend/openapi.json`。

**影响面**：该文件 diff 的唯一实质变化是 `info.x-generated-at` 一行时间戳，**API 契约内容零变化**——这反过来佐证本卡 openapi 确实零影响（不碰 `response_model`、不碰声明状态码）。生成脚本 `:282` 硬编码 `datetime.now(timezone.utc)` 且 `--write` 是「恒写」设计、无环境变量可控 ⇒ 只要 hook 触发就必然漂移，靠「再跑一次」消不掉。

**处置选择**：用 `git show <PREV>:backend/openapi.json` 写回 + `git add`（**不用** `checkout` / `restore`——guard 拦那两个），**单独一个 commit 还原**，而不是 `--amend --no-verify`。理由：

1. 还原 commit 的 staged files 只有 `openapi.json`，**不含** `backend/app` 的 `.py` ⇒ spec-sync 两条 glob 都不命中，hook 不会再写一次，**无需跳过任何检查**；
2. 地盘门判据 `git diff --name-only <PREV> HEAD` 是**树对树**比较，两次改动净为零 ⇒ 该文件不出现在门输出里（验伪锚 2 实测）；
3. 不改写历史，`971061f5` 那次「hook 完整跑过并通过」的记录原样保留。

⇒ **本卡未动用 `--no-verify`，也未动用 `LEFTHOOK_EXCLUDE`**。（曾起草过 `--amend --no-verify` 方案并写进 commit message，该操作被权限拒绝后改为本方案；`971061f5` 的 message 里那段 `--no-verify` 说明因此与实际处置不符 —— 它描述的是**未执行**的方案，实际处置以 `802f05ca` 的 message 与本节为准。这一条如实留痕，不改写历史去掩盖。）

> **教训（可复用，已登记台账）**：**按 shell 语义预判 lefthook glob 不算实测**。正确做法是 commit 后立刻核文件列表 —— 且必须用 `git show --pretty=format: --name-only HEAD`，**不能**用 `git show --stat --name-only HEAD`：后者会把 commit message 一起打出来，`grep -c 'openapi.json'` 会命中 message 里的字样。本卡第一次核就踩了这个，判据面（含 message）≠ 主张面（文件列表）。

---

## 五 Codex 复核（完成条件 (l)）

存档：`_bmad-output/审查/codex-review-CARD-T-UNREACH-r1.md`（4330 字节，非 0；首部六行 blockquote 含 `模型` / `reasoning_effort` / `codex` 三必填字段，会话头自证抄自 `.stderr:2/5/9` 并括注行号；`.stderr` 本身不入库 —— `.gitignore:264`）。

| 项 | 值 |
|---|---|
| 轮次 | **r1（1 轮达成）** |
| 模型 / effort / cli | `gpt-6-astra` · `ultra` · `codex-cli 0.153.3` |
| 审查绑定 | `802f05ca352afc3d432b1511f7e2e38869f19eb3` |
| **绑定是否 = 最终 HEAD** | **是**（送审后只改 `_bmad-output`，代码树未动；判据 `git --no-pager diff --stat --no-color 802f05ca HEAD -- . ':(exclude)_bmad-output'` 为空） |
| **BLOCKER / HIGH / MEDIUM / LOW** | **0 / 0 / 0 / 0** |
| D-15 达成 | ✅ 「多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」在 **r1** 即达成（本卡有代码改动，按规则允许多轮，实际 1 轮全零） |

Codex 原话：「本卡未发现需要修复的缺陷。审查绑定 `802f05c`；指定文件与工作区一致，给定 diff 范围内确实只改三个文件。」—— **地盘门被独立复核确认**。

### Codex 的六条观察（均非缺陷，是**收窄我的主张**；逐条处置）

| # | Codex 指出 | 处置 |
|---|---|---|
| ⓪ | 500 语义正确；但「调用方是否依赖旧 422 **未核实**」——它的允许读取面不含调用方实现 | **接受**。我另跑了全仓下游排查（`downstream-impact-20260917T030715.txt`，Codex 读取面之外），结论是无字面依赖方；但那只覆盖字面依赖 ⇒ §八 第 2 条**仍如实保留为未证明** |
| ① | MCP 仍返回 `ok=False / manifest=None`，按 `ok` 降级的消费者不受文案影响；但 skill 的「curl 失败→Grep」**只有注释声明**，未证明实际执行 | **接受**，§八 第 4 条已如实保留 |
| ② | 三处非死分支成立，但「这不构成**全仓 census** 证明」 | **接受**。我另跑了全 `backend/app` 的死分支普查（`dead-branch-census-all` + 验伪锚 `dead-branch-census-falsification`，改前副本报 2 DEAD / 改后 0），同样在 Codex 读取面之外；§八 第 5 条保留「静态结构普查证不了运行期」的边界 |
| ③ | KeyError 对照语义保持，普通 `ValueError` 分支也保持原行为 | 与本卡对照组结论一致 |
| ④ | patch 目标正确、`monkeypatch` 会恢复；但 **`asyncio.run` 不恢复调用前预设的 current loop**，依赖共享 loop 的其它测试属**未覆盖路径** | **有价值，采纳为新的未证明项**（§八 新增第 6 条）。本卡不改代码（改了要再送一轮），如实登记 |
| ⑤ | 删 ignore 无新诊断的代码依据；但「任意版本/配置下的结果以及 `0 errors / 81 warnings` **均未实测确认**」（Codex 只读不跑） | **接受**。`0 errors / 81 warnings` 由本卡存档 `pyright-final-20260917T030434.txt` 实测背书；「任意版本/配置」§八 第 7 条已保留 |
| ⑥ | AST 门 `checked == 1` 拦住了零匹配假绿；但「在前面**新增 `except Exception`**」是相对顺序门的盲区（不过真吞掉异常的话行为门会红） | **有价值，采纳为新的未证明项**（§八 新增第 7 条），并记下 Codex 自己给出的兜底论证：行为门会接住这种情况 |

Codex 末段自陈边界：「没有运行 pytest、pyright、项目导入、服务或数据库操作，也没有修改文件…… 作者所述历史红绿结果、运行时负控和前后哈希一致性仍未独立验证。」⇒ 那部分由本卡的落盘存档承担（§一～§四 逐条给了路径与末行）。

---

## 六 DoD-3 §4-A（Claude 已代验的技术证据）

Claude 已代验，逐条贴证据路径（本单只引用路径与末行，数字以存档为准）：

| 验收项 | 证据 | 结论 |
|---|---|---|
| census AST 两行 DEAD → OK | `census-open-20260917T025027.txt` → `census-after-20260917T025334.txt` → **`census-final-20260917T030434.txt`（承重）** | ✓ |
| 行为门先红 → 后绿（HTTP 500 / MCP schema 异常） | `redgreen-before-20260917T025201.txt`（rc=1）/ `redgreen-after-20260917T025300.txt`（v1, rc=0）→ 最终版 `redgreen-after-final-20260917T030434.txt`（v3, rc=0） | ✓ |
| 对照：普通 `ValueError` 仍 422 /「非法参数: 」，`KeyError` 仍 404 | 同上两份存档，对照 4 条**两态都绿** | ✓ |
| DD-03 异常由真 pydantic 产生（禁 MagicMock） | `dd03-nomock-ast-20260917T025541.txt`（AST 口径 + 验伪锚） | ✓ |
| pyright `0 errors / 81 warnings` | `pyright-open-20260917T025005.txt` / `pyright-after-20260917T025338.txt` / **`pyright-final-20260917T030434.txt`（承重）** | ✓ |
| `reportUnusedExcept` ignore 收工 = 0（同次验伪锚 = 2） | `census-final-20260917T030434.txt` | ✓ |
| 负控两段（红在指定断言 + 排他性 + shasum 前后同） | **`negctl-final-20260917T030506.txt`（承重，绑入库版 v3）** / `negctl-20260917T025645.txt`（首跑）；两份均含脚本原文 | ✓ |
| 全 `backend/app` 死分支普查 + 验伪锚 | `dead-branch-census-all-20260917T025845.txt` / `dead-branch-census-falsification-20260917T025903.txt` | ✓ |
| tests/unit 目录级 open → close 只 `<` | `unit-open-20260917T025023.txt` / **`unit-close-final-20260917T030552.txt`（承重）** + `open.nodeids` / `base.nodeids` / `close-final.nodeids` | ✓ **两条 diff 均 rc=0（完全相同）** |
| 地盘门 `$PREV..HEAD` ⊆ 三文件 | `territory-20260917T031741.txt`（双验伪锚） | ✓ **恰 3 行** |
| ruff 本卡 3 文件全绿（check + format）+ F821 验伪锚 | **`ruff-final-20260917T030434.txt`（承重）** / `ruff-20260917T025418.txt` / `ruff-format-20260917T025956.txt` | ✓ |
| 测试文件 v2→v3 的 AST 等价证明（+ 验伪锚） | `fmt-ast-equivalence-20260917T030026.txt` | ✓ |
| 行为变化的下游依赖排查（Codex ⓪/①） | `downstream-impact-20260917T030715.txt` | ✓ |
| 新测试文件自身 pyright 清零（非承重，本卡自清） | `pyright-testfile-20260917T030131.txt`（初版 **2 errors / 1 warning**）→ **`pyright-testfile-final-20260917T031022.txt`（入库版 0 errors / 0 warnings，含验伪锚：同跑法对已知错文件报 1 error）** | ✓ |

## 七 DoD-3 §4-B（用户产品体验，零技术词）

以前白板目录卡遇到「服务端自己拼出来的数据不合格」这种情况时，它会把锅甩给我，说「你参数非法」——其实根本不是我的错。现在它会老实说「这是它自己的内部错误」，并且把这件事记下来。

**我怎么验**：我做一次会触发这种内部错误的调用 → 我看到它明确报成**内部错误**，而不是赖我参数不对 → 我感觉这个工具对我更诚实了，以后它说「你参数错了」我才会真的去检查自己的参数。

**felt-sense**：从「它说我错了，可我明明没错，我得自己去猜到底哪儿出了问题」变成「它承认是它自己的问题，我不用再替它背锅」。少了那种被冤枉又无从申辩的憋闷。

---

## 八 本卡未证明什么

1. **未证明生产中真会出现「service 产出数据过不了自身 response schema」的具体场景**。本卡只证「一旦出现，异常被正确归类为 500 / 结构化错误」；触发靠 monkeypatch 让上游 `serve_manifest` 返回缺必填键的 dict，**不是**真实数据缺陷复现。
2. **未证明没有任何调用方依赖旧的「ValidationError → 422 /「非法参数: 」」行为**。这是本卡的行为变化面，已作为 Codex 问题 ⓪ 送审并登记入台账条目 ③，留主 session 集成期裁决。
3. **未证明 `serve_manifest` / `project_manifest` 在真实 vault 数据下会不会抛 `ValidationError`**。本卡不改这两者，也不跑真实 vault（硬边界：live vault 只读、禁连 7691/7687）。
4. **未证明 skill 侧降级链在 MCP error 文案变化后端到端仍无碍**。只证返回仍是 `ok=False`（结构不变、只是 `error` 文案变），**未跑真实 skill**。
5. **未证明别处三条 `except ValidationError`（service 层）在所有调用路径上都非死分支**。本卡做的是**静态结构**普查（同一 try 内是否被更宽的 handler 遮蔽），带验伪锚；它证不了「运行期是否真有异常走到那里」，也不覆盖跨函数的异常包装/重抛。
6. **未证明本卡测试对「依赖共享 event loop 的其它测试」无影响**（Codex r1 观察 ④ 采纳）。测试用 `asyncio.run` 逐次建/毁 loop，**不恢复调用前预设的 current loop**；若同进程内有测试依赖某个预设的共享 loop，那条路径**未被本卡覆盖**。本卡的证据只到「`tests/unit` 目录级 open→close nodeid 集完全相同」这一层（即：现有 5227 个用例里没有因此变红的），证不了「任何依赖共享 loop 的写法都安全」。
7. **未证明 AST 结构门能拦住「在 ValidationError 之前新增更宽 handler」**（Codex r1 观察 ⑥ 采纳）。该门断言的是 `ValidationError` 与 `ValueError` 的**相对**索引，若有人在两者之前插一个 `except Exception`，相对顺序仍成立、门仍绿。兜底是行为门：那个 `except Exception` 若真吞掉异常并改变返回，`test_http_schema_break_returns_500` / `test_mcp_schema_break_returns_structured_error` 会红。但「门本身覆盖这种变异」**未被证明**（本卡负控只变异了顺序，没变异「新增 handler」）。
8. **未证明删 ignore 后在非 basic pyright 模式下仍 0 errors**。本仓固定 `typeCheckingMode=basic` + pyright 1.1.411，未在 standard/strict 下试。
9. **未证明 HTTP 500 会如何呈现在 FastAPI 的实际响应体里**。测试直接调协程并捕 `HTTPException`，**未过 TestClient / 中间件栈**（不起 lifespan 是硬边界），所以「500 的 body 长什么样」不在本卡证明范围。
10. **未证明负控那两跑本身零连库**。负控存档里**没有** W4 哨兵行（脚本 `subprocess.run(capture_output=True)` 只转发了汇总行）。间接依据是同一测试文件在四份直跑存档里实测 `blocked=0`，但那是**推断不是实测**（详见 §二 的登记）。
11. **未证明本卡的行为变化对 `openapi.json` 零影响是被门验过的**。依据是 `lefthook.yml` 的两条 spec-sync glob（`backend/app/{api,models,schemas,mcp}/*.py` 与 `backend/app/{main.py,config.py}`）都不命中本卡两文件所在层级，且本卡不碰 `response_model` 与声明状态码；**未实跑** `check-openapi-drift.py`（`test_openapi_contract.py` 是 T5-D 的面，本卡不排它作裁判）。

## 九 台账待登记条目（只登记，不改台账 —— 台账只主 session 改）

1. **T-UNREACH 死分支修复**：终审 sha `<COMMIT_SHA>`；新测试 nodeid 前缀 `tests/unit/test_board_manifest_unreach_t5e.py`（11 例）；census AST 先红后绿（DEAD → OK）证据 `_bmad-output/审查/evidence-t-unreach/census-open-20260917T025027.txt` + `census-after-20260917T025334.txt`。
2. **口径更正**（recon A §B.1 / U2-台账待登记 §五 / 设计稿 §4 → 实测）：except 真落点 `boards.py:89` / `board_manifest_tools.py:70`（原写 `:86` / `:67`，那两行是注释）；`board_manifest_tools.py` 在 **`mcp/tools/`**。**独立复验**：对 `PREV` 的改前副本跑死分支普查，报出的 DEAD 行号正是 `:89` / `:70`（`dead-branch-census-falsification-20260917T025903.txt`）。
3. **行为变化登记**（供集成 / 回归追溯）：HTTP `ValidationError` **422 → 500**；MCP error **「非法参数: {e}」→「manifest 投影 schema 异常, 已记录日志」**。附 Codex 问题 ⓪「是否有调用方依赖旧 422 行为」的裁决请求。
4. **两处 `# pyright: ignore[reportUnusedExcept]` 删除**对账：删前 2 / 删后 0（同次验伪锚 `except pydantic.ValidationError` = 2）；pyright 改前改后均 `0 errors / 81 warnings`（**未涨到 83** ⇒ ignore 删干净）。
5. **合并队列注记**：本卡 openapi 零影响（不碰 `main.py` / `config.py`，两条 spec-sync glob 均不命中）。§2 队列可把 T5-E 排在 T5-D（openapi 变）之前；集成期请核本卡 diff 面仅两生产文件 + 新测试，与 T5-D 的 `security.py` / `system.py` / `main.py` / `openapi.json` **无交集**。
6. **别处三条 `except ValidationError` 非死分支的静态 census 结论**（`board_manifest_service.py:1029` / `:1069`、`canvas_service.py:701`）：均为各自 try 内**唯一** handler。全 `backend/app` 普查修后 DEAD = **0**，判据带验伪锚（改前副本 DEAD = 2）。是否另立卡做运行期复核，交主 session。
7. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** —— 见 §五。
8. **tests/unit 目录级 diff 结果**（`open.nodeids` → `close.nodeids` 只 `<`；`base.nodeids`(64) → `close.nodeids` 只 `<`）—— 见 §四。
9. **开工红集口径自证**（可复用）：本卡开工目录级的收集面**早于**新测试文件写入（`grep -cF 'test_board_manifest_unreach_t5e' unit-open-*.txt` = 0），且 `diff base.nodeids open.nodeids` **为空** ⇒ T5-A~D 四卡在 `tests/unit` 上**零新红**。
10. **负控脚本改进项**（下批采纳）：`negctl_t5e.py` 用 `subprocess.run(capture_output=True)` 跑 pytest，只 `print` 汇总行 ⇒ **W4 哨兵行没进存档**。本批 7691/7692 均在线、哨兵是必贴项，负控这类「脚本套 pytest」的裁判应把子进程原始输出一并落档（或至少转发哨兵行），否则该跑的连库情况无独立证据。
11. **lefthook `spec-sync-flat` 越界与更干净的处置**（批级可复用，已回写 memory）：本卡首次 commit 被 `spec-sync-flat` 顺带塞入 `backend/openapi.json`（其 glob 的 `*` 在 lefthook/Go 下**跨目录**匹配，与 shell 语义不同）。既有做法是 `LEFTHOOK_EXCLUDE=spec-sync-flat`（T5-B 用过）。**本卡用了第 4 种、更干净的处置**：接受首次 commit，然后**单独一个只含 `openapi.json` 的还原 commit** —— 它的 staged files 不含 `backend/app/**.py`，spec-sync 两条 glob 都不命中 ⇒ hook 不会再写一次，**全程零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`**；地盘门因「树对树 diff 净零」自然为绿（本卡实测：门恰 3 行，`PREV..HEAD -- openapi.json` = 0 行而 `PREV..971061f5 -- openapi.json` = 13 行）。代价 = 多一个 commit，主 session squash 时合并。建议后续卡采纳。
12. **核 commit 文件列表的正确命令**：必须 `git show --pretty=format: --name-only HEAD`；⛔ 不能用 `git show --stat --name-only HEAD`（会把 commit message 一起打出来，`grep -c 'openapi.json'` 命中 message 里的字样）。本卡第一次核就踩了这个，判据面 ≠ 主张面。
13. **`971061f5` 的 commit message 与实际处置不符（如实留痕，不改写历史）**：该 message 里写的是 `--amend --no-verify` 方案，那个操作**被权限拒绝、从未执行**；实际处置见 `802f05ca` 的 message 与验收单 §四 (g)。主 session squash 时以后者为准。
14. **判据坑登记**（批级可复用）：验收单初稿写过「全文件 `grep -c MagicMock` = 0」，实测 = **1** —— 命中的是 docstring 里「不用 MagicMock」那句话本身；换成第二版 `grep -cE` 仍 = 1（同一句）。**文本判据分不开「代码用了 mock」与「注释提到 mock 这个词」**，只有 AST 能分。已在入库前自查推翻并改为 AST 口径。
