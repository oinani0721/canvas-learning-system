> ⚠️ 本文件是 CARD-T-SWITCHVAULT 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T5-C 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-T-SWITCHVAULT]`。车道：`card-t5-bugs`（分支 `card/t5-bugs`，NEW @ `08100483`，`backend/.venv` 目录级 symlink → `card-v5-lance/backend/.venv`（含 pytest + pyright 1.1.411）、`backend/.env` 在、`_bmad-output/审查/prompts/` 在树内）。本车道第 **3/5** 张，前提：**前一卡 T5-B CARD-T-EDGES 已独立 commit 且 `git status --porcelain` 空**（第 0 分钟 `HEAD` 即 T5-B 末 commit）；之后串 **T5-D CARD-SEC-DANGLING**。用户已裁：**D-15**（有代码改动的卡 Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0，上限 5）；**本批 pyright 规则（取代 D-16 甲，设计稿 §0.2.1）**——`08100483` 上 `pyright app` = 0，语义车道必须保持 0，hook `python-typecheck` 正常拦，本卡新增 error 自清，⛔ **不得 `LEFTHOOK_EXCLUDE=python-typecheck`**；「改行为 = 产品裁定，已登 TAIL」——本卡**不解除** P0-3 vault 隔离，只把误导性错误文案改成透传真实原因（bug 修复非行为变化，见 §〇）。勘探 2026-09-11 于主干 `286178d8`（recon A §B.1「T-SWITCHVAULT」；U2 §五「T-SWITCHVAULT」），⚠️ **`infra_tools.py` 在 286178d8→08100483 的 U2 波 0 commit 里被改过（+11/-4，加 pyright ignore 注释）**，所有行号已在 `08100483` 树复测（见 §〇「口径更正」）。协议（⛔ 必须读 **feature 主干树 `--add-dir` 那份**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color + ruff zsh 数组 + pyright 绝对路径 / §3 最低覆盖）。手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **车道树 `card-t5-bugs` 自己的 `.claude/rules/*.md` 与手册是 `08100483` 版**，本批回写只在 `--add-dir` 的 feature 主干树那份——引用协议/手册一律读主干树绝对路径，别读车道树那份。

# CARD-T-SWITCHVAULT — switch_vault MCP 工具解析 JSONResponse.body 透传真实原因（不再把 `result.vault_name` 的 AttributeError 吞成误导错误）+ 真测试直接 await 工具协程打真实隔离端点 + pyright 保持 0

## 〇 事实
| 事实 | 位置 / 实测命令 |
|---|---|
| **路径更正**：勘探/设计稿 §3 地盘写 `backend/app/mcp/infra_tools.py`，实测真路径 = **`backend/app/mcp/tools/infra_tools.py`**（`find backend/app -name infra_tools.py` 唯一命中，在 `mcp/tools/` 子目录，不是 `mcp/`）。**在 `backend/app` ⇒ 触发 lefthook `python-typecheck`（glob `backend/app/*.py`）⇒ 计长度门 ⑩「pyright 保持 0」** | `find backend/app -name infra_tools.py` |
| **行号更正**：勘探 A/U2 §五 写缺陷在 `infra_tools.py:56/57`，实测 `08100483` 上缺陷**访问**在 `:63`（`vault_name=result.vault_name`）与 `:64`（`vault_id=result.vault_id`），两行各带 `# pyright: ignore[reportAttributeAccessIssue]`；`:56-60` 是缺陷说明注释块，`:58` = `# vault_name / vault_id ⇒ 下面两行运行期必 AttributeError, 被本函数的`。（286178d8→08100483 的 U2 波 0 commit 加了 ignore 注释 +11/-4，行号整体下移；勘探 `:56/57` 是 286178d8 口径，作废） | `sed -n '30,34p;51,67p' backend/app/mcp/tools/infra_tools.py` |
| **缺陷本体** `switch_vault :51-67`（`async def switch_vault(input: SwitchVaultInput) -> Dict[str, Any]`）：`:52` `from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch`（**惰性 import**，仅调用时才拉 vault 端点）；`:55` `result = await _switch(VaultSwitchRequest(vault_path=input.vault_path))`；`:61-65` `return SwitchVaultOutput(success=True, vault_name=result.vault_name, vault_id=result.vault_id).model_dump()`；`:66-67` `except Exception as e: return SwitchVaultOutput(success=False, error=str(e)[:200]).model_dump()`。`result` 静态类型 = `JSONResponse`（`_switch` 注解 `-> JSONResponse`），**无 `.vault_name`/`.vault_id`** ⇒ `:63` 运行期 `AttributeError` → 被 `:66` 吞成 `success=False, error="'JSONResponse' object has no attribute 'vault_name'"` | `sed -n '51,67p' backend/app/mcp/tools/infra_tools.py` |
| **⛔ 口径更正（承重）**：设计稿「做：解析 `JSONResponse.body`（json.loads）」隐含「body 里有 vault_name/vault_id」——**不成立**。`_switch` = `vault.py:91 switch_vault`（`@vault_router.post("/switch", deprecated=True, summary="QUARANTINED (410)…")`）被 **P0-3 写侧隔离**，`:97-108` 恒返回 `JSONResponse(status_code=410, content={"error":"gone","detail":"Runtime vault switch is quarantined (P0-3, 2026-07-31)… edit ACTIVE_VAULT in .env … docker compose up -d backend …"})`。**body 只有 `error`/`detail`，无 vault_name/vault_id**。⇒ 正确修法 = 解析 body 把 410/gone 的**真实原因**透传为 `error`（success=False），不是去取不存在的 vault_name | `sed -n '30,38p;79,108p' backend/app/api/v1/endpoints/vault.py` |
| **⛔ 死代码更正（承重，交主 session 裁）**：`switch_vault` ∈ `QUARANTINED_MCP_TOOLS`（`server.py:367`），`/mcp/tools/switch_vault` 路由是 `_register_quarantined_routes`（`:371-405`）产的 **410 stub**；`server.py:277-281` 只 `import`+ `:283-297` 只**注册** `check_backend_health` 一条 live 路由，**`infra_tools.switch_vault` 函数未被注册为任何 live 路由**。⇒ 该函数是 route-quarantined **死代码**（保留待 Tier B 物删）。本卡按设计稿修它（使其正确、去掉掩盖 bug 的 ignore），但「修好保留 vs 直接物删」是产品/退役裁定，登「台账待登记条目 ④」交主 session | `grep -n 'switch_vault\|QUARANTINED_MCP_TOOLS' backend/app/mcp/server.py`；`sed -n '277,297p;353,405p' backend/app/mcp/server.py` |
| **同型先例（本卡照它抄形态，不改它）**：同文件 `check_backend_health :37-48` 已用 `if hasattr(resp,"body"): import json; return json.loads(resp.body)["data"] …`（`:47` 带 `# pyright: ignore[reportAttributeAccessIssue]`，因其 `resp` 静态类型是 `dict`——与本卡 `result` 是 `JSONResponse` **不同**，本卡不需要那条 ignore，见下） | `sed -n '37,48p' backend/app/mcp/tools/infra_tools.py` |
| **B14_BASE 实测缺陷输出（改前红的目标）**：直接 `await switch_vault(SwitchVaultInput(vault_path="/tmp/x"))` 返回 `{'success': False, 'vault_name': '', 'vault_id': '', 'error': "'JSONResponse' object has no attribute 'vault_name'"}`（端点先 `logger.warning [VAULT-SWITCH-QUARANTINE]`）；`_switch(VaultSwitchRequest(vault_path="/tmp/x"))` 的 `.status_code == 410`、`json.loads(bytes(resp.body)) == {'error':'gone','detail':…}`（写卡实测，无 mock、无 7691） | 写卡 2026-09-12 于 `08100483` 内容树实跑（`backend/.venv/bin/python` await 协程）|
| **pyright 修法约束（写卡实测）**：`json.loads(result.body)` pyright **报错**（`result.body` 类型 `bytes \| memoryview[int]`，`json.loads` 要 `str\|bytes\|bytearray`，memoryview 不收）；必须 `json.loads(bytes(result.body))` + 对 payload 加 `isinstance(payload, dict)` 守卫，实测该形态 `pyright` = **0 errors, 0 warnings**。`08100483` 上 `pyright app` = **0 errors, 81 warnings**（单文件 `infra_tools.py` = 0 errors, 1 warning） | 写卡实测（scratch 探针 + `"$P" app/mcp/tools/infra_tools.py`）|
| **既有测试面**：`tests/unit` 无 switch_vault 工具真测试（`test_g25_journal_namespace.py:38` 的 `_switch_vault` 是本地夹具 helper，无关）；`tests/regression/test_mcp_quarantine.py` 测的是**路由层** 14 隔离工具返 410（用 TestClient 打 `/mcp/tools/*`），**不测** `infra_tools.switch_vault` 函数——⇒ 用 TestClient 打 `/mcp/tools/switch_vault` 只命中 410 stub，测不到本函数。真测试须**直接 await 工具协程**（打真实隔离端点，无 mock），新文件名 `test_mcp_switch_vault_tool.py`（`ls backend/tests/unit/test_mcp_switch_vault_tool.py` 不存在，free）| `grep -rn 'switch_vault' backend/tests/`；`sed -n '35,55p' backend/tests/regression/test_mcp_quarantine.py` |
| **地盘对齐**：本卡地盘 = `backend/app/mcp/tools/infra_tools.py`（独占改 `switch_vault`）+ 新文件 `backend/tests/unit/test_mcp_switch_vault_tool.py`（独占新建）。`infra_tools.py` 改前 `ruff format --check` = `1 file already formatted`、`ruff check` = `All checks passed!`（rc=0）⇒ **不落 462 ruff-format 漂移集**，本卡不需协议 §2.3 过渡条款 | 写卡实测 `ruff format --check` / `ruff check` |
| **本批纪律**（协议 / 手册 §零）：**pyright 保持 0**（绝对路径 + `test -x` 自证，⛔ 不得 `LEFTHOOK_EXCLUDE=python-typecheck`，新增 error 本卡自清）；判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 用 `.txt` 不 `.log`（仓根 `.gitignore` 有 `*.log`）；承重裁判末行 `rc=$pipestatus[1]`（zsh）；ruff 判据用 zsh 数组（协议 §2.2）；**批中禁装/升任何包**（不往共享 venv 装）；`fsrs_bridge.py`/`decay_beta.py` 零写者；live vault / 7691 / 7687 / 现网 LanceDB 只读 | 协议 §2.1/§2.2/§2.3；手册 §零 |

## 一 完成条件（AND）
- (a) **第 0 分钟**：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`；`git branch --show-current` = `card/t5-bugs`；`git status --porcelain | wc -l` → 0（T5-B 已独立 commit 且树干净，非空即停下报主 session）；`PREV=$(git rev-parse HEAD)`（= T5-B 末 commit，**本卡地盘核基线**，落进验收单）；`test -x backend/.venv/bin/pytest && test -e backend/.env`；`P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright; test -x "$P" || { echo "pyright 缺席"; exit 1; }`。**开工基线自证**：`P` 在的前提下 `(cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')` → `0 errors, 81 warnings`（不是 0 errors ⇒ 停下报主 session，说明前置卡污染）。开工先 `sed -n` 核 §〇 每条 file:line（行号漂移则验收单写「卡文 :X → 实测 :Y」）。
- (b) **先红**（新文件 `backend/tests/unit/test_mcp_switch_vault_tool.py`，在**未改生产代码**时先跑一次，tee `switchvault-red-<ts>.txt`）：至少两条测试——
  ① `test_switch_vault_surfaces_quarantine_not_attribute_error`（承重，先红后绿）：`res = asyncio.run(switch_vault(SwitchVaultInput(vault_path="/tmp/nonexistent-vault-t5c")))`；断言 `res["success"] is False`（改前改后都成立）**且** `"has no attribute" not in res["error"]`（⛔ 改前**必红**：B14 上 `error` 恒含 `'JSONResponse' object has no attribute 'vault_name'`）**且** `res["error"]` 小写后含 `"quarantin"` 或 `"p0-3"` 或 `"active_vault"`（透传真实隔离原因；断言消息把 `res` 整个打出来）。
  ② `test_switch_vault_hits_real_quarantine_endpoint`（**验伪锚 / 无 mock 自证**，改前改后都绿）：`from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch`；`resp = asyncio.run(_switch(VaultSwitchRequest(vault_path="/tmp/x")))`；断言 `resp.status_code == 410`（证明本测试打的是**真实 P0-3 隔离端点**、不是 mock，DD-03）。
  ⛔ 禁 mock `_switch` / 禁 monkeypatch 掉端点；用 `asyncio.run(...)` 在同步 test 内驱动协程（不引入新的 asyncio fixture/插件依赖）。取名与既有 `tests/unit` / `tests/regression` 测试零重名（`grep -rn 'def test_switch_vault_surfaces\|def test_switch_vault_hits' backend/tests` 交集空）。
- (c) **最小修法**（只碰 `backend/app/mcp/tools/infra_tools.py` 的 `switch_vault :51-67`，其余函数一行不动）：把 `:61-65` 的「直接读 `result.vault_name`/`result.vault_id`」改为**解析 body**，形态照 `check_backend_health` 但按本函数 `result` 是 `JSONResponse` 的真实类型做 pyright-clean 与守卫（写卡已实测 0/0）：
  ```python
  async def switch_vault(input: SwitchVaultInput) -> Dict[str, Any]:
      import json
      from app.api.v1.endpoints.vault import VaultSwitchRequest, switch_vault as _switch

      try:
          result = await _switch(VaultSwitchRequest(vault_path=input.vault_path))
          # vault.switch_vault 被 P0-3 写侧隔离后恒返回 410 JSONResponse
          # (body = {"error": "gone", "detail": ...}, 无 vault_name / vault_id)。
          # 解析 body 把真实原因透传给调用方, 不再让 result.vault_name 的
          # AttributeError 被 except 吞成 "'JSONResponse' object has no attribute 'vault_name'"。
          payload = json.loads(bytes(result.body))
          if result.status_code >= 400 or (isinstance(payload, dict) and "error" in payload):
              detail = (payload.get("detail") or payload.get("error")) if isinstance(payload, dict) else None
              return SwitchVaultOutput(success=False, error=str(detail)[:200]).model_dump()
          return SwitchVaultOutput(
              success=True,
              vault_name=payload.get("vault_name", "") if isinstance(payload, dict) else "",
              vault_id=payload.get("vault_id", "") if isinstance(payload, dict) else "",
          ).model_dump()
      except Exception as e:
          return SwitchVaultOutput(success=False, error=str(e)[:200]).model_dump()
  ```
  ⛔ **同批删除 `:63`/`:64` 的两处 `# pyright: ignore[reportAttributeAccessIssue]`**（缺陷访问已不在，ignore 随之删除，否则可能触发 unnecessary-ignore）；⛔ 禁用 `cast(...)`（cast 等于声明「它就是那个类型」，会把真缺陷永久盖住——原注释 `:60` 已如此警告）；⛔ 禁 mock、禁 TODO 空函数。`check_backend_health` / `SwitchVaultOutput` 模型 / 隔离端点本体一律不动。
- (d) **后绿**：(b) 两条测试改后全 `passed`（tee `switchvault-green-<ts>.txt`，rc=0）。
- (e) **pyright 保持 0**（承重）：`(cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')` 改后仍 `0 errors, 81 warnings`（warning 数以实测为准、只核 `0 errors`）；ruff：`F=(${(f)"$(git diff --name-only --diff-filter=AM $PREV HEAD -- 'backend/**/*.py')"}); print -r -- "files=${#F}"; (( ${#F} )) || exit 1; "$R" check -- "${F[@]}"; echo rc=$?` → rc=0（`R` = `card-v5-lance` venv 的 ruff 绝对路径）；验伪锚：把某个已知含 `F401` 的临时文件喂 `ruff check` 必 rc=1（证判据能红）。
- (f) **负控**（承重，证测试锁住修复）：改后临时把 (c) 的 body 解析退回缺陷写法 `vault_name=result.vault_name`（其余不动）→ 重跑 (b) 测试 ① **必红**且红在 `"has no attribute" not in res["error"]` 那条；还原用 `git show HEAD:backend/app/mcp/tools/infra_tools.py > /tmp/t5c-orig.py` 逐字比对（⛔ **禁 `git stash` / 禁 `git checkout` 还原**——会清暂存区/污染共享 stash），EXIT trap 无条件还原，`shasum -a 256 backend/app/mcp/tools/infra_tools.py` 负控跑前/跑后两行逐字相同（都贴进验收单，tee `switchvault-negctl-<ts>.txt` 末行 `rc=$pipestatus[1]`）。
- (g) **地盘核**：`git diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'`（⛔ 写法必须 `':(exclude)…'` 不是 `':!…'`）只列 `backend/app/mcp/tools/infra_tools.py` 与 `backend/tests/unit/test_mcp_switch_vault_tool.py` 两个文件（验伪锚：去掉 exclude 应多出 `_bmad-output/` 路径）；⛔ diff 里出现 `edges.py`/`background_task_manager.py`/`config.py`/`security.py`/`system.py`/`main.py`/`boards.py`/`board_manifest_tools.py`/`test_openapi_contract.py` 等 T5 其它卡的面 = 越界，停下。
- (h) **tests/unit 目录级 diff 只许 `<`**（收工一次；本卡不修红，预期 diff 为空）：基线（feature 主干树绝对路径）`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（**64 条**，nodeid 口径，带 `--ignore tests/unit/test_deploy_vault_sh.py`）；开工先 `test -f "$BASE" && grep -vc '^#' "$BASE"` → 64（不是 64 ⇒ 停下报主 session）；`TS=$(date +%Y%m%dT%H%M%S); RUN=$EV/unit-close-$TS.txt`（⛔ 承重那跑文件名先固定成变量，禁 glob）；`cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" tests/unit -q -p no:cacheprovider --ignore tests/unit/test_deploy_vault_sh.py 2>&1 | tee "$RUN"; echo rc=$pipestatus[1] | tee -a "$RUN"; cd ..`（⛔ **禁写成 `( … | tee "$RUN" )` 子 shell 形**——zsh 实测 `( false | tee f ); echo $pipestatus[1]` 打 **0**（记的是 tee 的 rc，不是 pytest 的），pytest 整场崩在收集期会被记成 rc=0 的假绿、且 close.nodeids 为空令 diff 只剩 `<` 行；本行须与 §二⑧ 逐字同形）；`grep -E '^(FAILED|ERROR) tests/' "$RUN" | sed 's/ - .*//' | sort -u > $EV/close.nodeids; grep -v '^#' "$BASE" | sort -u > $EV/base.nodeids; diff $EV/base.nodeids $EV/close.nodeids` → **只允许 `<` 行**（我的新文件两条测试必须不在红集里；任何 `>` = 阻断）。（W4 门在 `08100483` 树已含，目录级 tests/unit 可跑；`tests/integration`/`tests/e2e` 走 advisory 会真连——本卡不跑它们。）
- (i) **Codex**：顺序固定「代码 + 两测试定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`」；`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（本卡有代码改动 ⇒ 多轮，上限 5；见 §四）。
- (j) **提交**：单独 commit（T5-D 开工前工作树必须干净）；header ≤100 含 `[BATCH-2026-09-11-第十四批 / CARD-T-SWITCHVAULT]`（含卡号），body 行 ≤100（`wc -m` 计字符）；`*.stderr*` 不入库；不 push；不改台账。
- (k) **「本卡未证明什么」必填**（≥4，见 §四）+ **「台账待登记条目」必填**（≥4，见 §四）。

## 二 裁判命令
```zsh
# ── 第 0 分钟 ──
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs
git branch --show-current            # card/t5-bugs
git status --porcelain | wc -l       # 0
PREV=$(git rev-parse HEAD)           # = T5-B 末 commit（地盘核基线），记进验收单
test -x backend/.venv/bin/pytest && test -e backend/.env && echo "env ok"
P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright
R=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/ruff
test -x "$P" || { echo "pyright 缺席"; exit 1; }
test -x "$R" || { echo "ruff 缺席"; exit 1; }
PYTEST=$(pwd)/backend/.venv/bin/pytest
EV=$(pwd)/_bmad-output/审查/evidence-switchvault; mkdir -p "$EV"
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
test -f "$BASE" && grep -vc '^#' "$BASE"        # 64（非 64 停下报主 session）

# ① 事实核（逐字同 §〇）
sed -n '30,34p;51,67p' backend/app/mcp/tools/infra_tools.py
sed -n '30,38p;79,108p' backend/app/api/v1/endpoints/vault.py
grep -n '"switch_vault"' backend/app/mcp/server.py              # 期望 367:（switch_vault ∈ QUARANTINED_MCP_TOOLS）
grep -n 'QUARANTINED_MCP_TOOLS' backend/app/mcp/server.py       # :353 定义、:399 注册 410 stub 循环

# ② 改前红（未改生产代码，新测试先跑）：承重裁判 tee
cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" -q -p no:cacheprovider \
  tests/unit/test_mcp_switch_vault_tool.py 2>&1 | tee "$EV/switchvault-red-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望：test_switch_vault_surfaces_quarantine_not_attribute_error FAILED（红在 "has no attribute"）；
#         test_switch_vault_hits_real_quarantine_endpoint passed；rc=1
cd ..

# ③ 改代码（§一 c）后：绿
cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" -q -p no:cacheprovider \
  tests/unit/test_mcp_switch_vault_tool.py 2>&1 | tee "$EV/switchvault-green-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望：2 passed；rc=0
cd ..

# ④ pyright 保持 0（承重，绝对路径 + test -x 已在第 0 分钟自证）
( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' ) | tee "$EV/pyright-app-$(date +%Y%m%dT%H%M%S).txt"
#   期望：0 errors, 81 warnings（只核 0 errors）

# ⑤ ruff（zsh 数组；改动文件）
F=(${(f)"$(git diff --name-only --diff-filter=AM $PREV HEAD -- 'backend/**/*.py')"})
print -r -- "files=${#F}"; (( ${#F} )) || exit 1
"$R" check -- "${F[@]}"; echo rc=$?     # 期望 rc=0
# 验伪锚：printf 'import os\n' > /tmp/t5c_f401.py && "$R" check /tmp/t5c_f401.py; echo rc=$?  # 必 rc=1

# ⑥ 负控（承重）：退回缺陷写法 result.vault_name → 测试 ① 必红 → 还原逐字节相同
shasum -a 256 backend/app/mcp/tools/infra_tools.py | tee "$EV/negctl-sha-$(date +%Y%m%dT%H%M%S).txt"
#  （手工把 :61-65 退回 vault_name=result.vault_name 后）重跑测试 ①，tee negctl-<ts>.txt，末行 echo rc=$pipestatus[1]；
#   还原：git show HEAD:backend/app/mcp/tools/infra_tools.py > /tmp/t5c-orig.py; 逐字比对后覆盖；再 shasum 两行逐字同
#   ⛔ 禁 git stash / git checkout 还原

# ⑦ 地盘核（--no-color；':(exclude)…' 写法）
git diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'
#   期望恰两行：backend/app/mcp/tools/infra_tools.py、backend/tests/unit/test_mcp_switch_vault_tool.py
#   验伪锚：去掉 ':(exclude)_bmad-output' 应多出 _bmad-output/ 路径

# ⑧ tests/unit 目录级 diff 只许 <（收工一次；本卡不修红，预期空）
TS=$(date +%Y%m%dT%H%M%S); RUN=$EV/unit-close-$TS.txt
cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" tests/unit -q -p no:cacheprovider \
  --ignore tests/unit/test_deploy_vault_sh.py 2>&1 | tee "$RUN"; echo rc=$pipestatus[1] | tee -a "$RUN"; cd ..
grep -E '^(FAILED|ERROR) tests/' "$RUN" | sed 's/ - .*//' | sort -u > $EV/close.nodeids
grep -v '^#' "$BASE" | sort -u > $EV/base.nodeids
diff $EV/base.nodeids $EV/close.nodeids      # 只允许 < 行；任何 > = 阻断

# ⑨ Codex 后：绑定核
git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'   # 空即仍绑最终 HEAD
```

## 三 禁改与隔离
- **本卡地盘（只允许改这两个文件）**：
  - `backend/app/mcp/tools/infra_tools.py` —— **只改 `switch_vault :51-67`**（body 解析 + 删两处 `# pyright: ignore`）；`check_backend_health`、`SwitchVaultInput/Output` 及其余定义一行不动。
  - `backend/tests/unit/test_mcp_switch_vault_tool.py` —— 新建（独占）。
- **禁改面**：`backend/app/api/v1/endpoints/vault.py`（P0-3 隔离端点本体，只读引用）；`backend/app/mcp/server.py`（QUARANTINED 注册面，只读）；`check_backend_health`（同文件另一函数，本卡不扩面）。
- **T5 车道其它卡的面禁碰**（串行地盘互斥）：`backend/app/core/background_task_manager.py`、`backend/app/core/config.py`（T5-A）；`backend/app/api/v1/endpoints/edges.py`（T5-B）；`backend/app/core/security.py`、`backend/app/api/v1/system.py`、`backend/app/main.py`、`backend/app/api/v1/endpoints/boards.py`、`backend/app/mcp/tools/board_manifest_tools.py`、`backend/tests/contract/test_openapi_contract.py`（T5-D/E）。⛔ diff 里出现它们 = 越界。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 7691/7687（本卡真测试只 await 协程打 410 隔离端点，不触发任何库连接——若测试意外要连库 = 写法错，停下）；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（本卡零关联，`grep -rn 'fsrs_bridge\|decay_beta' backend/app/mcp/tools/infra_tools.py backend/tests/unit/test_mcp_switch_vault_tool.py` 应 0 命中）；⛔ 现网 LanceDB 目录只读；⛔ 禁 `git stash`（共享栈）；⛔ 禁 `LEFTHOOK_EXCLUDE=python-typecheck`（本卡触及 `backend/app`，pyright 保持 0，新增 error 自清）；⛔ 不改台账（只主 session 改，卡在验收单写「台账待登记条目」）；⛔ 不 push；`*.stderr*` 不入库；`.log` 后缀不用；批中禁装/升任何包。
- **禁放宽判据**：测试 ① 不得改成「只断言 success is False」（改前改后都成立、锁不住修复）——必须保留 `"has no attribute" not in error` + 透传原因两条；负控必须红在指定断言；pyright 判据必须绝对路径 + `test -x` 自证（车道树 `backend/.venv/bin/pyright` 虽可用，仍以绝对路径写死为准）。

## 四 Codex / 验收单
命令（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT[-rN].md)" > _bmad-output/审查/codex-review-CARD-T-SWITCHVAULT[-rN].md 2> _bmad-output/审查/codex-review-CARD-T-SWITCHVAULT[-rN].stderr </dev/null`。
- **轮次**：`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（本卡有代码改动 ⇒ **多轮，上限 5**；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；车道对 HIGH 的驳回写理由但不能自判通过；0 字节存档重发一次，再 0 字节 → 主 session 人审）。
- **存档首部**（协议 §2.1，每份 `codex-review-CARD-T-SWITCHVAULT[-rN].md` 首部 blockquote + `---`）：`批次/车道/卡 round-N`、`模型 gpt-6-astra · reasoning_effort ultra · codex <codex --version 实测值>`、`审查绑定 <审SHA 或 A..B>`、`会话头自证`抄 `.stderr` 会话头里含 codex 版本行 / model 行 / reasoning_effort 行的那三行（行号不限、逐行写明实测行号；`.stderr` 本身不入库）。缺 `模型 / reasoning_effort / codex` 任一字段该轮不计配额。
- **prompt 五分节**：① 背景 + **最小读取面写死** = `git diff $PREV <审SHA> -- . ':(exclude)_bmad-output'` + `backend/app/mcp/tools/infra_tools.py` 全文 + `backend/app/api/v1/endpoints/vault.py:30-108`（VaultSwitchRequest + P0-3 隔离端点）+ `backend/app/mcp/server.py:277-297`（check_backend_health 先例 + 注册面）与 `:353-405`（QUARANTINED_MCP_TOOLS + 410 stub）+ 新测试全文；② 作者自述请独立核对：switch_vault 解析 body 与 check_backend_health 同型、`bytes(result.body)` 保 pyright 0、`isinstance(payload,dict)` 守卫、410/gone 分支透传 detail、两处 pyright ignore 已删、真测试直接 await 协程打真实隔离端点无 mock、端点恒 410（验伪锚 `status_code == 410`）；③ 按重要性排序的问题：⓪ payload 非 dict（body 是数字/字符串 JSON）时是否有**未被拦下的输入**触达未守卫的 `.get`；① `bytes(result.body)` 在 memoryview body 下是否恒成功；② success 分支（读 vault_name/vault_id）在隔离态永不执行，是否属**门未覆盖的路径**（无真实成功响应可测）；③ `except Exception` 是否仍会吞掉本该显形的错误（端点抛非 JSONResponse 时）；④ 修好后运行期是否仍是 route-quarantine 死代码；⑤ check_backend_health 是否同型隐患（本卡不改，仅问是否需并批）；④ 输出格式（BLOCKER/HIGH/MEDIUM/LOW + file:line + 一句复现思路）；⑤ 边界（只读、不连库、不评 P0-3 隔离决策本身、不评 check_backend_health 既有 ignore、不要求解除隔离）。
- **禁用四措辞**（协议 §2）：prompt 与存档不得出现协议 §2 点名的那四个禁用措辞（cyber 拦截在任务边界、不在措辞本身）——一律改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
- **验收单** `_bmad-output/验收单/UAT-CARD-T-SWITCHVAULT-<日期>.md`（DoD-3 双段）：4-A Claude 已代验贴证据（pyright 0 / 两测试红→绿 / 负控红 / 地盘核 / tests/unit diff / Codex B/H/M/L）；4-B 零技术词 + felt-sense，一句例：「我让助手『切换到另一个资料库』——以前它只会回一句看不懂的报错，现在它会明明白白告诉我『切换已停用，要在部署设置里改』——我做这个动作 → 我看到清楚的说明 → 我感觉不再被莫名其妙的失败搞糊涂」。
- **本卡未证明什么**（≥4）：① 未证明该 MCP 工具在 live MCP 路由上可达——`switch_vault` ∈ QUARANTINED_MCP_TOOLS（server.py:367），`/mcp/tools/switch_vault` 是 410 stub，函数未注册 live 路由 ⇒ 本卡修的是 route-quarantine 死代码，运行期是否有真实调用方触达它本卡不证（交主 session 裁：修好保留 vs Tier B 物删）；② 未证明 `vault.switch_vault` 端点将来「解除隔离」后 body 会带 vault_name/vault_id——success 分支在当前隔离态**永不执行**（恒走 410/gone），其正确性只靠 check_backend_health 同型先例佐证，无真实成功响应可测；③ 未证明 P0-3 隔离决策本身该改（改行为=产品裁定，已登 TAIL）——本卡只把误导性 AttributeError 文案改成透传真实原因，不解除隔离、不恢复 runtime 切换；④ 未跑 MCP JSON-RPC 层（fastapi-mcp）调用，真测试只直接 await 协程（那条路由本就是 410 stub）；⑤ 未证明 check_backend_health（同文件、live-registered、同 body-parse 形态但 `resp` 类型是 dict）无同类隐患，本卡不扩面到它。
- **台账待登记条目**（≥4）：① T-SWITCHVAULT 真缺陷（switch_vault 恒报 `'JSONResponse' object has no attribute 'vault_name'`）→ 本卡修复 commit sha + 两测试 nodeid + 实测缺陷字符串原文；② **路径更正**：勘探/地盘写 `backend/app/mcp/infra_tools.py`，实测真路径 `backend/app/mcp/tools/infra_tools.py`（`find` 唯一命中）；勘探行号 `:56/57` → 实测 `08100483` 缺陷访问在 `:63/:64`（U2 波 0 commit 286178d8→08100483 +11/-4 下移）；③ **口径更正**：设计稿「解析 body 取 vault_name」不成立——端点 P0-3 隔离恒 410 `{error,detail}`、body 无 vault_name/vault_id；本卡改为解析 body 透传隔离原因（success=False）；④ **route-quarantine 死代码**：switch_vault ∈ QUARANTINED_MCP_TOOLS、函数未注册 live 路由 ⇒ 交主 session 裁「保留 vs Tier B 物删」（与 PYRIGHT-TAIL / 死代码 census 同族）；⑤ 两处 `# pyright: ignore[reportAttributeAccessIssue]`（:63/:64）随缺陷访问一并删除，`pyright app` 保持 0；⑥ Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数；⑦ tests/unit 目录级 diff 结果（只 `<`，本卡不修红）。
- commit header ≤100 含批次标记且含卡号；`*.stderr*` 不入库；不 push；**独立 commit 后同车道继续 T5-D**；跑完说「复核第十四批 T5」。
