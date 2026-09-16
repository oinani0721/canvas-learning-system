# evidence-switchvault — CARD-T-SWITCHVAULT 证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-T-SWITCHVAULT]` · 车道 `card-t5-bugs`
> PREV = `6d7eb683` · 终审 HEAD = `59e0d766`
> 本索引回应 Codex round-3 的一条批评：「存档没有完整变异 diff、执行命令及 pytest 输出，
> 不能视为独立复现」——下面给出每条判据的**复现命令**，使第三方能重跑而不必读我的脚本。

⚠️ 本目录只放**输出**。变异脚本在 session scratchpad（不入库），但每组变异的**具体改法**
都写在下表，可据此逐字重建。

---

## 一 承重门（绑终审 HEAD `59e0d766`）

| 存档 | 判据 | 复现命令（仓根起） |
|---|---|---|
| `allgates-selfbound-59e0d766-*.txt` | 五道门一次跑完 + **绑定自证**（HEAD + 两文件工作树/HEAD blob 双侧 sha256 + `BOUND_TO_HEAD`） | 见该文件每段标题下的命令；核心五条见下 |
| `switchvault-red-*.txt` | **改前**：test① FAILED 在「has no attribute」、test② passed | `cd backend && .venv/bin/pytest -q -p no:cacheprovider tests/unit/test_mcp_switch_vault_tool.py`（在 `6d7eb683` 的树上） |
| `switchvault-green-*.txt` | **改后**：2 passed | 同上（在 `ab99f130` 及之后） |
| `pyright-app-baseline-*.txt` / `pyright-app-after-*.txt` | pyright 保持 0 errors | `( cd backend && "$P" app 2>&1 \| grep -E '^[0-9]+ errors?, ' )`，`$P` = `card-v5-lance/backend/.venv/bin/pyright`（R-B14-10：cwd 必须是 `backend/`） |
| `ruff-anchor-*.txt` | ruff check + **同配置面验伪锚** | `"$R" check -- <两文件>`；锚：`printf 'x = undefined_name_t5c\n' \| "$R" check --stdin-filename backend/app/mcp/tools/infra_tools.py -`（必 rc=1） |
| `territory-*.txt` / `territory-anchor-*.txt` | 地盘核恰两文件 + `':(exclude)…'` 写法有效性反证 | `git --no-pager diff --stat --no-color 6d7eb683 HEAD -- . ':(exclude)_bmad-output'` |
| `no-mock-ast-*.txt` | DD-03 禁 mock（**AST 口径**，非 grep） | 见文件内说明；grep 口径会命中 docstring 里的反-mock 声明（文件里同时打印了两种口径的差值） |
| `unit-close-r5-*.txt` + `close-r5.nodeids` | tests/unit 目录级 red-diff | `cd backend && .venv/bin/pytest tests/unit -q -p no:cacheprovider --ignore tests/unit/test_deploy_vault_sh.py`（R-B14-3：`--ignore` 用相对路径） |

---

## 二 负控 / 探针（十四组）

口径：**每组跑整文件两条测试**。还原基准 = 变异前实测副本，EXIT trap 无条件还原，
跑前/跑后 `shasum -a 256` 双判据（`RESTORE_IDENTICAL` + `MATCHES_HEAD`）。
⛔ 全程未用 `git stash` / `git checkout` 还原。

存档：`negctl-r3-8mutants-*.txt`（A–H）、`negctl-r4-6mutants-*.txt`（I–M）、
`negctl-r4-mockshapes-*.txt` 与 `probe-detail-and-fullassert-*.txt`（N）。

| 组 | 变异的**具体改法**（对 `backend/app/mcp/tools/infra_tools.py`） | 实测 |
|---|---|---|
| A | 整个文件退回 `git show 6d7eb683:backend/app/mcp/tools/infra_tools.py` | 1 failed（**has-no-attribute 断言**）+ 1 passed |
| B | 删掉 `if result.status_code >= 400 or "error" in payload:` 到 `return SwitchVaultOutput(\n success=True,` 之间的整段 | 1 failed（**success 断言**，返回 `{'success': True,…}` = 谎报成功）|
| C | `reason = str(detail) if detail else f"vault switch failed with HTTP {…}"` → `reason = "quarantined"` | 1 failed（**逐字比对断言**；token 断言命中 0）|
| D | `json.loads(bytes(result.body))` → `json.loads(result.body)` | 2 passed |
| E | 外层 except 两行 → `return SwitchVaultOutput(success=False, error=str(e)[:200]).model_dump()` | 2 passed |
| F | `if result.status_code >= 400 or "error" in payload:` → `if result.status_code >= 400:` | 2 passed |
| G | 同上 → `if result.status_code >= 400 and "error" in payload:` | 2 passed |
| H | 在 `result = await _switch(...)` 前插入 `return SwitchVaultOutput(success=False, error=<完整 detail[:200] 字面量>).model_dump()` | 2 passed |
| I | `if result.status_code >= 400 or "error" in payload:` → `if "error" in payload:` | 2 passed |
| J | `reason = str(detail) if detail else …` → `reason = detail if detail else …` | 2 passed |
| K | 删失败分支（同 B）**且** `vault_name=str(payload.get("vault_name") or "")` → `vault_name=payload["vault_name"]`（`vault_id` 同） | 1 failed（**token 断言**）|
| L | 失败分支的 `error=reason[:200]` → `error=reason` | 1 failed（**逐字比对断言**）|
| M | 同 D，但跑的是 **pyright** 而非 pytest | `0 errors` → **`1 error`**，报在 `:66` 的 `json.loads` 实参 |
| N | **不改仓库文件**；在探针进程内 `monkeypatch` `app.api.v1.endpoints.vault.switch_vault`，对五种假返回值形状逐条跑测试①的**全部四条**断言 | 五种形状**无一种**能让①整体变绿 |

---

## 三 专项证明

| 存档 | 证明了什么 |
|---|---|
| `openapi-noop-proof-*.txt` | 本卡定向排除 `spec-sync-flat` hook 的依据：其产出去掉 `info.x-generated-at` / `x-generator` 后与 HEAD 版**归一化 sha256 相同**；验伪锚（插入假 path）能分辨真实契约变更。⚠️ 同名早一份是一次失败尝试的报错输出（转义错误），保留以示过程 |
| `body-runtime-type-probe-*.txt` | `JSONResponse.body` 在当前端点正常返回路径上的**运行期**类型是 `bytes`（一次观测） |
| `probe-detail-and-fullassert-*.txt` | (1) `len(detail) == 216 > 200`、截掉的尾巴 `'to change vault.'`；(2) N 组的全断言矩阵 |
| `ast-equiv-r2r3-*.txt` | D-32 口径：剥 docstring 后代码指纹相同 ⇒ 纯文案改动；带「改真实断言值则判据变 False」的验伪锚 |
| `flaky-attribution-*.txt` | 目录级那次 65 的归因：两轮之间可执行代码 AST 指纹相同 ⇒ 逻辑上排除代码引起；本卡零触碰 candidate 面；该测试单跑 8 次 + 整文件跑 3 次全 passed |
| `flaky-blocked-detail-*.txt` | 该次红的直接根因：W4 门抓到一次到现网 `7691` 的连接尝试（`blocked=1` = **被拦下、未真连上**），门按设计转成用例失败 |

---

## 四 已知的证据边界（如实）

1. 变异脚本本身不在本目录（在 session scratchpad）。上表给出了每组的具体改法，可据此重建，
   但**这不等于第三方已独立复现**。
2. 两份早期 pyright 存档的**归属**（实测时序，验伪锚已核）：
   `baseline` 跑于 `01:34:27`、`after` 跑于 `01:38:29`，修复提交 `ab99f130` 在 `01:42:16` ——
   **两份都早于该提交**。故 `baseline` 是**改前**代码的 `0 errors`；`after` 是**已改但尚未
   提交**的工作树（已带 `bytes()`）的 `0 errors`。⚠️ 两份**都不是**「删掉 `bytes()`」的
   D 变异体 —— 这正是 Codex round-2 LOW-3 指出「缺『删 `bytes()` 后 pyright 报错』的记录」
   的原因，该缺口由后来的 **M 组**补上。
   （早先我把这条粗略写成「两份都是带着 `bytes()` 跑的」，对 `baseline` 不成立，已更正。）
3. 目录级共跑五次，其中一次为 65 —— 见验收单 §二.5 的完整归因，**不是**「每次都 64」。
4. 单文件跑的零偷连计数只覆盖**测试体**，不覆盖模块 import 期副作用。
