> ⚠️ 本文件是 CARD-U9C-EVAL 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T4-D 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-U9C-EVAL]`。车道 **T4**（worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`，分支 `card/t4-g3`，NEW @ `B14_BASE = 081004834e37b1b0253cf81dc7b44e784646c934`，`backend/.venv` 目录级 symlink 已建、`backend/.env` 已拷），本车道第 **4/4** 张（A CARD-G3-9 → B CARD-G6-10 → C CARD-U9B-OPENSPEC → **D 本卡**，末张）。前提：**前一卡 T4-C CARD-U9B-OPENSPEC 已独立 commit 且 `git status --porcelain` 空**（HEAD 此时已含 T4-A+T4-B+T4-C 三卡 commit，不是 `08100483`）。用户已裁相关：**R-07**（U9 系列为第十四批产品动作/评估面的授权来源）；**D-38**（U9-C 以评估卡落地：前提改写 + 口径测试 + 评估文档，legacy 兼容重做作为**设计级**议题不排本批）；**D-15**（Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH=0，上限 5）。勘探日期与树：2026-09-11 于主干 `feature-obsidian-hybrid-dev`（代码 = B14_BASE `08100483`；HEAD 已多一个纯文档 commit `e58d5c5c`——`review_service.py`/`exception_handlers.py`/`main.py` 在两 commit 间 diff 为空，行号一致）。勘探来源：recon C §10（U9-C）+ §10.4/§10.5；设计稿 §4 T4-D。协议（绝对路径，只读 feature 树那份）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + 「不入库的复核不作依据」/ §2 Codex 命令 + §2.1 存档首部 + §2.2 裁判落盘 `--no-color`/`.txt`/`rc=$pipestatus[1]` / §3 最低覆盖）。手册（绝对路径）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 本批纪律 / §三 T4-D /goal / §四 队列）。
> ⚠️ **车道树 `card-t4-g3` @ `B14_BASE` 里那份协议是 `08100483` 版**；本批对协议的回写（§2.1 首部改「抄含版本行+model 行+reasoning 行」/ §2.2 ruff zsh 数组 + pyright 绝对路径 + 禁 `| tail -1` / §3 W4 哨兵改绑）由 T8-G/T9-C 等卡出 patch、**只改 `--add-dir` 的 feature 树那份**——凡本卡引协议条款，一律读上面这条绝对路径的 feature 树那份，禁写相对路径。

# CARD-U9C-EVAL — U9-C「VaultScopeUnresolved 拒启」前提改写 + 口径测试钉（真拒启面 = 首个命中 get_review_service() 的请求；进程不崩、请求 500、CARD-G3-5 消息在异常与日志但被通用异常处理器从 500 响应体屏蔽）+ 评估文档（legacy 兼容重做作为设计级议题登记不排）· 零生产改动

## 〇 事实
| 事实 | 位置 / 实测命令（主干 `feature-obsidian-hybrid-dev`，2026-09-11；代码 = B14_BASE `08100483`） |
|---|---|
| **抛出点 2 处，均在 `__init__` 的构造链上（行号更正）** | `grep -n 'raise VaultScopeUnresolved(' backend/app/services/review_service.py` → **`:570`**（None 分支：legacy 裸键存在 + `_resolve_vault` 返 None）与 **`:593`**（同名冲突分支：作用域解析成功但 legacy 与桶内同名）。**勘探 recon C :573/:596 → 实测 :570/:593**（recon C 取自 286178d8，B14_BASE 该区 −3）。两条消息体均以 `f"CARD-G3-5: ..."` 开头（`:571`/`:594` 起），并含 `migrate_fsrs_card_states_vault_key_g35.py` 裁定指引 |
| **构造链（行号更正）** | `def from_persisted` **`:521`**（recon C :524）；`self._card_states: ... = self._load_card_states()` **`:850`**（recon C :853，在 `ReviewService.__init__` 内，`__init__` 签名 `:776`）；`def _load_card_states` **`:876`**（recon C :879）；`states = _VaultScopedCardStates.from_persisted(loaded)` **`:893`**（recon C :896）；`class _VaultScopedCardStates` **`:352`**（recon C :356，批次注释 `CARD-G3-5 (BATCH-2026-09-07-第十三批)` `:348`）；`def _resolve_vault` **`:388`**（recon C :391） |
| **⛔ 前提更正（设计稿 §10.5 必落 §〇）：U9-C 原「CLI/后台无 vault 上下文拒启」前提不成立** | `git --no-pager grep -c --no-color "ReviewService(" -- 'scripts/*' 'backend/scripts/*'` → **无输出（rc=1，0 命中）**；`git --no-pager grep -n --no-color "ReviewService(" -- '*.py' | grep -v '/tests/' | wc -l` → **1**（⛔ §〇 记录的命令形态与 §二 判据逐字同口径，两处都带 `--no-color`——协议 §2.2：多 worktree 共用 `.git/config`，`color.ui` 会被并发改写，重定向到文件不豁免），唯一生产构造点 `backend/app/services/review_service.py:2996`（recon C :2978；在 `async def get_review_service` `:2939`（recon C :2921）双检锁工厂内；`reset_review_service_singleton` `:3006`（recon C :2988））。**没有任何 CLI/后台脚本会在无 vault 上下文下构造 ReviewService** ⇒ 真正的拒启面是 **HTTP 请求路径上首个命中 `get_review_service()` 的请求**，不是「CLI 启动崩溃」 |
| **lifespan 不预构造 ReviewService ⇒ 进程启动不崩** | `grep -nc 'get_review_service\|ReviewService(\|review_service' backend/app/main.py` → **0**（`main.py` 启动/lifespan 段既不调工厂也不构造 ReviewService）⇒ 含 legacy 坏数据时后端**仍能起来**，异常只在请求期抛，worker 不死 |
| **⚠ 本卡关键发现 / 口径更正：CARD-G3-5 消息被通用异常处理器从 500 响应体屏蔽** | `VaultScopeUnresolved` 是裸 `Exception` 子类（`backend/app/core/vault_scope.py:359 class VaultScopeUnresolved(Exception):`），**无专用处理器**（`grep -n 'VaultScopeUnresolved' backend/app/main.py backend/app/core/exception_handlers.py backend/app/dependencies.py` = 空）。它逸出请求处理器后落到 `generic_exception_handler`（`backend/app/core/exception_handlers.py:200` 定义，`:312 app.add_exception_handler(Exception, generic_exception_handler)` 注册），该处理器**刻意不暴露内部细节**：响应体 = `{"code": 500, "message": "Internal server error", "bug_id": ...}`（`:262-266`；`return JSONResponse(` 在 **`:268`**，`:267` 是空行——勘探写的「返回 :267」经本树 `awk 'NR>=266&&NR<=268'` 实测更正），消息原文只进 `logger.error(... error_message=str(exc) ...)` 与 `bug_tracker.log_error(...)`（bug_log.jsonl）。⇒ 设计稿「请求 500 **带 CARD-G3-5 消息**」一半成立：**500 成立、CARD-G3-5 进日志/bug_log 成立、进 HTTP 响应体不成立**（被屏蔽）。本卡据此改测试口径，不改生产去暴露消息（零生产改动） |
| **工厂先构造重依赖再构造 ReviewService ⇒ 真工厂路径测试会连真服务** | `sed -n '2939,3002p' review_service.py`：工厂在 `:2996` 构造 ReviewService **之前**先 `await get_memory_service()`、`CanvasService(...)`、`get_graphiti_temporal_client()`（Neo4j/LanceDB 面）。`_review_service_singleton = ReviewService(...)` 是**最后一步**且赋值只在构造成功时发生 ⇒ 构造抛异常则 singleton 恒 None、后续每个 review 请求重入工厂重抛（持续 500 直到运维跑迁移脚本）。⇒ HTTP 层口径测试**不得调真工厂**（会连 7691），改用最小 app 直接让真实 `from_persisted` 抛出、走真实 `generic_exception_handler`，离线钉「屏蔽 + 进程不崩」 |
| **构造层抛出已有测试覆盖，但未断言消息含 CARD-G3-5** | `backend/tests/regression/test_g3_5_vault_keyed_card_states.py`：`test_conflicting_legacy_is_fail_fast_not_silently_skipped`（同名分支，`with vault_scope("vault_a"): ... from_persisted({"vault_a": {"c": "A-new"}, "c": "legacy-unknown"})`，只断言 `"同名" in str`）；`test_legacy_without_scope_is_fail_fast_not_silently_dropped`（None 分支，`monkeypatch subject_config.get_current_subject_id→DEFAULT_SUBJECT_ID` + `default_vault_group_id→抛`，只断言 `pytest.raises(VaultScopeUnresolved)`，**无** CARD-G3-5 消息断言）；正控 `test_non_conflicting_legacy_is_adopted_normally` / `test_pure_nested_snapshot_is_loaded_as_is`。⇒ 本卡新测试的增量 = 两分支**显式断言消息含 `CARD-G3-5`** + **HTTP 层屏蔽/进程不崩**（既有测试都在构造层、无 HTTP 面） |
| **tests/unit 红基线**（本卡**不碰** tests/unit，用作覆盖损失守门） | `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt` = **64 条 nodeid**（带 `--ignore tests/unit/test_deploy_vault_sh.py`，R-15；文件 67 行含 3 行 `#` 头注，`grep -vc '^#' 文件`=**64**（R-B14-2 唯一口径；⛔ 禁 `grep -c '::'`——基线第 3 行注释里逐字引了一条 flaky nodeid，该写法=**65**））。绝对路径写死（在 **feature 主干树**，**车道树里没有这个文件**，引用前先 `test -f`） |
| **本批纪律**（§三/手册 §零逐条对照） | 本卡**不触及 `backend/app` 生产代码**（只加 `backend/tests/regression/` 新测试 + `_bmad-output/` 评估文档），故**不在 APP_CARDS、不触发 `python-typecheck`、不计长度门 ⑩**（若实测发现必须碰 `backend/app`，**停下**在验收单写明、不自行扩面）。新测试 `.py` 会过 lefthook `python-lint`（ruff），判据用 **zsh 数组写法**（协议 §2.2）。判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 用 `.txt` 不 `.log`（仓根 `.gitignore` 有全局 `*.log`）；承重裁判末行 `rc=$pipestatus[1]`（zsh）。**批中禁装工具**（不往共享 venv 装/升任何包；若 venv 缺 `fastapi.testclient`/`starlette` 则探针已就位，照常）。`fsrs_bridge.py`/`decay_beta.py` **零写者**；live vault / 7691 / 7687 / 现网 LanceDB **只读禁连**（本测试零真实服务连接）。**主 session 排批期裁定 R-B14 逐条对照（本卡已核）**：**R-B14-2 适用**——基线自证唯一口径 `grep -vc '^#'`=**64**，禁 `grep -c '::'`（=65），已落 §一(a)/§二；**R-B14-3 适用**——`cd backend` 后 `--ignore` 写相对路径，§一(h)/§二 已合规；**R-B14-1 不适用**——本卡不直接调 lefthook（只经 commit 钩子过 `python-lint`，判据用 `backend/.venv/bin/ruff check`；全卡零 lefthook 裸/带 flag 调用，故 R-B14-1 点名的那个 1.x flag 在本卡无落点）；**R-B14-4 不适用**——地盘扩充表不含本卡，本卡地盘仍是单个新测试文件；**R-B14-5/6/7 不适用**——分属 T9/T8 面 |

## 一 完成条件（AND）
- **(a) 第 0 分钟（环境自证 + 勘探复核）**：`pwd` 末段 = `card-t4-g3`；`git branch --show-current` = `card/t4-g3`；`git rev-parse HEAD` = **T4-C CARD-U9B-OPENSPEC 的末 commit**（记下此 SHA，(g) 的地盘核前提 commit 就用它；**不是** `08100483`，也不是 T4-A/T4-B 的 commit）；`git status --porcelain` 空；`test -e backend/.venv/bin/pytest && test -e backend/.env`；`B14BASELINE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt; test -f "$B14BASELINE" || 停下`（`grep -vc '^#' "$B14BASELINE"` 自证 **64**，R-B14-2 唯一口径；⛔ 禁 `grep -c '::'`=65）；`mkdir -p _bmad-output/审查/evidence-u9c-eval`。再用 `sed -n`/`grep -nF` 逐条复核 §〇 每个 file:line（尤其 `review_service.py:570/:593/:521/:850/:876/:893/:352/:388/:2939/:2996`、`exception_handlers.py:200/:262-266/:312`、`vault_scope.py:359`、`main.py` grep=0、`scripts/` grep=0），与实测不一致处以实测为准并写进验收单「勘探 :X → 实测 :Y」。
- **(b) 评估文档落盘**（本卡主交付物）：写 `_bmad-output/审查/<开工日 YYYY-MM-DD>-U9C-VaultScopeUnresolved-拒启-评估.md`，至少含五节，每条结论旁附**本卡实测命令 + 输出**（禁凭勘探转抄，禁「待实测」）：
  ① **前提更正**：U9-C 原立面「CLI/后台无 vault 上下文构造 ReviewService ⇒ 拒启」——实测 `scripts/` 与 `backend/scripts/` 对 `ReviewService(` **0 命中**（git grep rc=1），生产唯一构造点在 HTTP 依赖链 `:2996`；`main.py` lifespan 对 `get_review_service`/`ReviewService(` **0 命中** ⇒ 真拒启面 = **启动后首个命中 `get_review_service()` 的请求**，进程启动本身不崩。
  ② **双抛出点**：`from_persisted :521` → None 分支 `:570`（作用域解析不出）/ 同名冲突分支 `:593`（解析成功但 legacy 撞桶内），均在 `ReviewService.__init__ :850 → _load_card_states :876 → :893` 链上；消息均 `CARD-G3-5:` 前缀 + 迁移脚本指引。
  ③ **消息屏蔽（关键发现）**：`VaultScopeUnresolved(Exception)`（`vault_scope.py:359`）无专用处理器 → `generic_exception_handler`（`exception_handlers.py:200`，`:312` 注册 `Exception`）返回 `{"code":500,"message":"Internal server error","bug_id":...}`（`:262-266`），CARD-G3-5 原文**只进** `logger.error(error_message=...)` + `bug_tracker`（bug_log.jsonl），**不进 HTTP 响应体**。贴 `generic_exception_handler` body 原文 + (d) 测试响应体实测。
  ④ **进程不崩 + 持续 500**：请求期抛异常 worker 不死；但 `_review_service_singleton` 只在构造成功时赋值（`:2996` 是工厂最后一步），构造抛则 singleton 恒 None ⇒ review 面后续每请求重入重抛、持续 500，直到运维跑 `migrate_fsrs_card_states_vault_key_g35.py` 裁定归属。
  ⑤ **legacy 兼容重做 = 设计级议题（D-38，不排本批）**：两条出路——(α) 生产加 `VaultScopeUnresolved` 专用处理器把 CARD-G3-5 指引友好暴露进 500 响应体；(β) legacy 兼容整体重做（隔离区/保留键命名空间/多份候选/毒条目预检，Codex r2→r5 反复长新缺陷那一套）。两者均影响产品行为、需用户裁，**本卡只登记移交，不动代码**。
- **(c) 表征钉 · 新测试（构造层，离线无服务）**（⚠️ 名实一致：本卡零生产改动，(c) **没有真「先红」**——改前跑即绿，判据可判定性由 ③ 负控验伪锚承担；全卡唯一的真「先红」在 **(d)** 的临时反向断言）：新文件 `backend/tests/regression/test_u9c_startup_rejection_eval.py`（取名与既有 test 零重名）写两条钉消息的测试，**改前跑即绿**（本卡零生产改动，钉的是既有行为）、**负控/验伪锚**保证判据可判定：
  ① `test_unresolved_scope_raise_carries_card_g3_5`（None 分支）：照 `test_g3_5_vault_keyed_card_states.py::test_legacy_without_scope_is_fail_fast...` 同款 `monkeypatch`（`app.core.subject_config.get_current_subject_id → DEFAULT_SUBJECT_ID`、`default_vault_group_id → 抛`）下 `pytest.raises(VaultScopeUnresolved) as ei: _VaultScopedCardStates.from_persisted({"orphan-c": "legacy-card"})`，断言 `"CARD-G3-5" in str(ei.value)` **且** `"migrate_fsrs_card_states_vault_key_g35.py" in str(ei.value)`。
  ② `test_clobbered_legacy_raise_carries_card_g3_5`（同名分支）：照既有 `with vault_scope("vault_a"):` 同款作用域下 `from_persisted({"vault_a": {"c": "A-new"}, "c": "legacy-unknown"})` 抛，断言 `"CARD-G3-5" in str` 且 `"同名" in str`。
  ③ **负控（验伪锚，承重）**：`test_no_legacy_does_not_raise`——无 legacy 的纯嵌套/纯本桶输入（如 `{"vault_a": {"c1": "A"}}`）在 ① 的 unresolved 环境下**不抛**、正常返回（证明 (c)① 的抛出是 legacy+归不掉触发，不是无条件抛；若改测试误写成无条件，此条必红）。
- **(d) 先红后绿 · 新测试（HTTP 层屏蔽 + 进程不崩，最小 app 离线）**：同文件内 `test_unresolved_scope_surfaces_as_masked_500_not_crash`——`app = FastAPI()` + `register_exception_handlers(app)`（真处理器）；probe 路由 `/_u9c_probe` 在 (c)① 同款 unresolved 环境下调真实 `_VaultScopedCardStates.from_persisted({"orphan-c":"legacy"})`（真异常源，**不调** `get_review_service()` 工厂，避免连真服务）；另一路由 `/_alive` 返 200；`client = TestClient(app, raise_server_exceptions=False)`（⛔ 必须 `raise_server_exceptions=False`，否则 TestClient 会把异常抛进测试而非返回 500 响应）。**验伪锚（先红）**：先临时断言 `"CARD-G3-5" in resp.text` 跑一次，**必红**（证明响应体确实屏蔽了消息）——把这一跑输出 tee 进 evidence（`u9c-antigate-<ts>.txt`）；**再翻成正式断言（后绿）**：`GET /_u9c_probe` → `resp.status_code == 500` 且 `resp.json()["message"] == "Internal server error"` 且 `"CARD-G3-5" not in resp.text`；随后 `GET /_alive` → `200`（证进程不崩、app 仍服务）。**分层说明写进测试 docstring**（防「为验 B 层 mock 掉 A 层」质疑）：构造层抛出由 (c) 的真 `from_persisted` 覆盖，HTTP 屏蔽由本条真 handler 覆盖，工厂重依赖路径由 §〇 grep + 评估文档 ④ 以只读证据覆盖（不执行，避免连 7691），三层各有覆盖、无 mock 掉任何被测层。
- **(e) 测试文件级绿**：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/regression/test_u9c_startup_rejection_eval.py -q -p no:cacheprovider` → rc=0、全绿；跑时 W4 哨兵**无 `blocked=` 行**（哨兵只在「有非豁免拦截 / 迟到连接」时才打印该行，且 blocked>0 而退出码为 0 时会强制改成非 0 退出 ⇒「rc=0 且无该行」= blocked=0 且 unaccounted=0；本测试零真实服务连接，出现该行即误连，停下排查**不得跳过**）。该判据**必须配同次验伪锚**：同口径 `grep -c 'blocked=' tests/support/live_port_guard.py` 在哨兵源码上必 >0（本树实测 **6**）——没有这个锚，「0 命中」既可能是真无拦截、也可能是 pattern 写错或文件路径落空。⛔ 本卡只跑**本新测试文件级**，不跑 `tests/regression` 目录级（目录内含真连真服务的用例，非本卡面）。
- **(f) C §10.4 四条 grep 复现**（评估的可复核锚，全 tee 进 evidence）：见 §二.①~④，期望值逐条写死。
- **(g) 地盘核**：`git diff --stat --no-color <T4-C 末 commit> HEAD -- . ':(exclude)_bmad-output'` 只列本卡允许面（见 §三）——即 `backend/tests/regression/test_u9c_startup_rejection_eval.py` 一个新文件（`_bmad-output/` 下的评估文档与验收单已被 `:(exclude)` 排除，另由 `git status` 核）；⛔ pathspec 必须写 `':(exclude)_bmad-output'`（`':!...'` 在 zsh/本机 git 2.50 下报 `Unimplemented pathspec magic` rc=128、stdout 空，会把没跑成读成绿）。验伪锚：先证该 `git diff` 能列出本新文件（即本卡确有改动面），再断言无其它代码文件。
- **(h) tests/unit 目录级 diff 只许 `<`**（覆盖损失守门；本卡不碰 tests/unit，应无变化）：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`（R-15 同 `--ignore`；⛔ **R-B14-3**：`cd backend` 之后 `--ignore` 必须写**相对路径** `tests/unit/test_deploy_vault_sh.py`，写成 `backend/tests/...` 不匹配任何被收集文件 = 空操作，该重型文件仍会被收集真跑），收 nodeid 口径的 ERROR/FAILED 集合与 `$B14BASELINE`（64 条）`diff`：**只许 `<`（基线有、本跑消失），不许 `>`（本卡新增红）**；出现 `>` 即停下报主 session。**验伪锚（承重）**：比对前先断言两份 nodeids 文件**都非空**（base 期望 **64**、now 期望 **>0**）——两边同时为空会让 `comm -13` 恒空，把「没跑成 / 提取失败」读成绿。
- **(i) Codex 多轮**：本卡有代码改动（新增回归测试 `.py`）⇒ 按 D-15 **Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（上限 5 轮；若某轮后只改 `_bmad-output` 文档/docstring 尾巴按 D-32 不占轮次、不重置）。见 §四。
- **(j)「本卡未证明什么」**：验收单必填 ≥4 条（见 §四示例）。
- **(k)「台账待登记条目」**：验收单必填 ≥4 条（见 §四示例）。

## 二 裁判命令
```zsh
# ── 第 0 分钟（(a)）──
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3
pwd; git branch --show-current; git rev-parse HEAD; git status --porcelain
test -e backend/.venv/bin/pytest && test -e backend/.env && echo env-ok
B14BASELINE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
test -f "$B14BASELINE" && grep -vc '^#' "$B14BASELINE"   # 期望 64（R-B14-2 唯一口径；⛔ 禁 grep -c '::' = 65）
mkdir -p _bmad-output/审查/evidence-u9c-eval
EV=_bmad-output/审查/evidence-u9c-eval

# ── §10.4 四条 grep（(f)），全部 tee（承重裁判末行 rc=$pipestatus[1]）──
# ① 抛出点恰 2 处（行号更正 570/593）
grep -n 'raise VaultScopeUnresolved(' backend/app/services/review_service.py \
  2>&1 | tee "$EV/grep-raise-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 570 / 593
# ② scripts/ 与 backend/scripts/ 零构造方
git --no-pager grep -c --no-color "ReviewService(" -- 'scripts/*' 'backend/scripts/*' \
  2>&1 | tee "$EV/grep-scripts-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]  # 期望无输出（rc=1）
# ③ 生产唯一构造点（非测试）
git --no-pager grep -n --no-color "ReviewService(" -- '*.py' | grep -v '/tests/' \
  2>&1 | tee "$EV/grep-prod-ctor-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望恰 1 行：backend/app/services/review_service.py:2996
# 验伪锚（②③ git grep）：同口径 git grep 的 pattern 在已知正例上必命中（证 ② 的 0 命中是真无构造方、非正则失效或 color ANSI 归零）
git --no-pager grep -c --no-color "ReviewService(" -- 'backend/app/services/review_service.py'   # 期望 >0（review_service.py:1）
# ④ lifespan 不预构造
grep -nc 'get_review_service\|ReviewService(\|review_service' backend/app/main.py \
  2>&1 | tee "$EV/grep-main-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]      # 期望 0
# 验伪锚（承重）：⛔ 必须用**与判据逐字相同的三支交替 pattern**——只锚 'get_review_service' 单支
# 证明不了 `\|` 交替语法在本机 grep 下有效，而那恰是「④ 的 0」最可能的失效面（单支锚会恒绿地放行
# 一个把交替读成字面量的 grep ⇒ 假 0）。取名面必须等于主张：同 pattern、换已知正例文件。
grep -nc 'get_review_service\|ReviewService(\|review_service' backend/app/services/review_service.py
#   期望 >0（本树实测 **32**；已在 `/usr/bin/grep` = BSD grep 2.6.0-FreeBSD 上实证 `\|` 交替生效：
#   `/usr/bin/grep -c 'ZZZNOEXIST\|ReviewService(' backend/app/services/review_service.py` → 1）

# ── (c)(d)(e) 新测试文件级绿（承重）──
PYT="$EV/pytest-u9c-$(date +%Y%m%dT%H%M%S).txt"   # ⛔ 绑定单份存档，下面只读这一份；禁用 pytest-u9c-*.txt 通配（重跑后多文件会让 grep -c 变成「路径:计数」逐文件形态，「期望 0」读不出来）
cd backend
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/regression/test_u9c_startup_rejection_eval.py -q -p no:cacheprovider \
  2>&1 | tee "../$PYT"; echo rc=$pipestatus[1]   # 期望 rc=0 全绿
# 同一跑里 W4 哨兵必**无 blocked= 行**：哨兵只在「有非豁免拦截 / 迟到连接」时才打印该行，
# 且 blocked>0 而退出码为 0 时它会强制改成非 0 退出 ⇒「rc=0 且无 blocked= 行」= blocked=0 且 unaccounted=0
grep -c 'blocked=' "../$PYT"; echo rc=$?                            # 期望 0、rc=1（无该行）
# 验伪锚（承重）：同口径 grep 在已知含该字面量的哨兵源码上必 >0——证上面的 0 是真无拦截，
# 不是 pattern 写错 / 文件路径落空（无此锚时「0 命中」什么也证明不了）
grep -c 'blocked=' tests/support/live_port_guard.py                 # 期望 >0（本树实测 6）
cd ..

# ── (h) tests/unit 覆盖损失守门（只许 <）──
UNIT="$EV/unit-$(date +%Y%m%dT%H%M%S).txt"   # ⛔ 绑定单份存档；禁用 unit-*.txt 通配（多文件时 grep -oE 会给每行加「路径:」前缀、下面的 sed 剥不掉 ⇒ comm 全成假 `>`）
cd backend
# ⛔ R-B14-3：cd backend 之后 --ignore 必须写**相对路径**（写 backend/tests/… 不匹配任何被收集文件 = 空操作，重型文件仍会被收集真跑）
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider \
  2>&1 | tee "../$UNIT"; echo rc=$pipestatus[1]
cd ..
# 从本跑提 nodeid 口径 ERROR/FAILED，与基线 diff；> 即本卡引入红
grep -oE '^(ERROR|FAILED) tests/unit/[^ ]+' "$UNIT" | sed -E 's/^(ERROR|FAILED) //' | sort -u > "$EV/unit-now.nodeids"
grep -vE '^#' "$B14BASELINE" | grep -oE 'tests/unit/[^ ]+' | sort -u > "$EV/unit-base.nodeids"
# 验伪锚（承重，防「两边都空 ⇒ comm 恒空 = 假绿」）：两份 nodeids 必须都非空，否则停下排查不得当绿
wc -l < "$EV/unit-base.nodeids"   # 期望 64（本树实测，与 R-B14-2 的 64 同源）
wc -l < "$EV/unit-now.nodeids"    # 期望 >0（=0 说明本跑没收到红或提取失败）
echo "== 本卡新增红（应空）=="; comm -13 "$EV/unit-base.nodeids" "$EV/unit-now.nodeids"

# ── (g) 地盘核（⛔ ':(exclude)…'，不是 ':!…'）──
T4C_SHA=<T4-C 末 commit>   # (a) 记下的值
git --no-pager diff --stat --no-color "$T4C_SHA" HEAD -- . ':(exclude)_bmad-output' \
  2>&1 | tee "$EV/territory-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   期望只列 backend/tests/regression/test_u9c_startup_rejection_eval.py

# ── ruff（新测试过 python-lint；zsh 数组写法，协议 §2.2）──
# ⛔ 同协议 §2.2：喂进数组的 git 输出也必须 --no-color（ANSI 会混进元素，ruff 会拿到不存在的路径）
F=(${(f)"$(git --no-pager diff --no-color --name-only --diff-filter=AM "$T4C_SHA" HEAD -- 'backend/**/*.py')"})
print -r -- "files=${#F}"; (( ${#F} )) || echo "无 py 改动"; (( ${#F} )) && backend/.venv/bin/ruff check -- "${F[@]}"; echo rc=$?
```

## 三 禁改与隔离
- **地盘（只允许改/新建这些文件）**：
  - `backend/tests/regression/test_u9c_startup_rejection_eval.py`（**新文件**，本卡独占；取名与既有 test 零重名——开工 `grep -rn 'test_u9c_startup_rejection' backend/tests` 应空）。
  - `_bmad-output/审查/<开工日>-U9C-VaultScopeUnresolved-拒启-评估.md`（评估文档）+ `_bmad-output/审查/evidence-u9c-eval/**`（裁判存档）+ `_bmad-output/验收单/UAT-CARD-U9C-EVAL-<开工日>.md`（验收单）。
- **禁改面（只读，违反 = 集成冲突 / 扩面）**：`backend/app/**` 全部（尤其 `review_service.py` / `core/exception_handlers.py` / `core/vault_scope.py` / `main.py` / `dependencies.py`——**只读核锚，零生产改动**）；`backend/app/models/**`（零写者）；`openspec/**`、`docs/project-status/fr-exploration/A6-phase0-reference-card.md`、`backend/tests/regression/test_g3_7_truth_source.py`（T4-C 地盘，已收口）；`scripts/daily_review_pick.py`、`backend/tests/regression/test_daily_review_pick.py`、`backend/scripts/g39_three_view_reconcile.py`、`backend/scripts/g610_dual_vault_interaction_canary.py`（T4-A/B 地盘）；`backend/tests/regression/test_daily_review_run.py`（T3 地盘）；其余所有车道地盘（T1/T2/T3/T5~T10）。
- **硬边界**：零生产改动（若实测发现钉口径**必须**改 `backend/app` 才能绿，**停下**在验收单/notes 写明，不自作主张扩面）；禁写 **live vault**；禁连 **7691 / 7687 / 现网 LanceDB**（本测试零真实服务连接，用最小 app + `from_persisted` 离线钉；跑出 `blocked=`>0 即误连，停下排查不得跳过）；禁碰 `fsrs_bridge.py` / `decay_beta.py`（零写者）；禁 `git stash`（共享栈，用 WIP commit 代替）；**批中禁装工具**（不 `npm install`、不往共享 venv 装/升任何包）；**不改台账**（台账只主 session 改，本卡在验收单写「台账待登记条目」）；commit header ≤100 含批次标记 `[BATCH-2026-09-11-第十四批 / CARD-U9C-EVAL]` 且含卡号 `CARD-U9C-EVAL`、body 行 ≤100；`*.stderr*` **不入库**；**不 push**。

## 四 Codex / 验收单
- **Codex 复核命令**（协议 §2 固定；prompt 先写好在 `_bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md`）：
  ```zsh
  codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
    "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)" \
    > _bmad-output/审查/codex-review-CARD-U9C-EVAL-r1.md \
    2> _bmad-output/审查/codex-review-CARD-U9C-EVAL-r1.stderr </dev/null
  ```
- **prompt 五分节要点**：① 范围（本卡 = 评估卡，零生产改动，改 2 个文件：新测试 + 评估文档）；② 声明（真拒启面 = 首个命中 `get_review_service()` 的请求，非 CLI；CARD-G3-5 消息被 `generic_exception_handler` 从 500 响应体屏蔽，只进日志/bug_log）；③ 请复核项（测试是否真钉了两抛出点消息 + HTTP 屏蔽 + 进程不崩；负控/验伪锚是否真能判定；评估文档结论是否都有本卡实测证据而非转抄；是否误碰 `backend/app`）；④ 最小读取面（`backend/tests/regression/test_u9c_startup_rejection_eval.py`、评估文档、`backend/app/services/review_service.py:352-600` 与 `:2939-3002`（只读锚）、`backend/app/core/exception_handlers.py:200-312`）；⑤ 输出格式（按级别列 finding）。**⛔ prompt 措辞纪律（协议 §2 任务边界）**：prompt 全文禁用**协议 §2 点名的那四个禁用措辞**（本卡文按同一纪律不逐字列举它们，写 prompt 前照读协议 §2 原文）；描述负控/对照时只用中性说法「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」，不用攻防类动词。**替换词表（本卡高频面，写 prompt 时照用）**：`:2996` 那一行写「唯一生产**实例化点**」或「工厂内新建 `ReviewService` 的那一行」；`__init__ → _load_card_states → from_persisted` 写「**实例化链**」或「该调用链」；`main.py` 那条写「lifespan 不预先**实例化** `ReviewService`」。⛔ **不要把本卡文 §〇/§一 的原句直接粘进 prompt**——那两段用的是另一套措辞、只供车道自己读；prompt 按上表改写后再落盘。
- **存档首部**（协议 §2.1，每份 `codex-review-CARD-U9C-EVAL-rN.md` 首部 blockquote + 一行 `---`）：含 `批次/车道/卡/round`；`模型 gpt-6-astra · reasoning_effort ultra · codex <codex --version 实测值>`（抄 `.stderr` 前三行含 version 行 + model 行 + reasoning 行，**括注各自行号**，`.stderr` 本身不入库）；`审查绑定 <审SHA 或 A..B>`（末轮须绑最终 HEAD）。
- **轮次（D-15）**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（上限 5 轮；本卡有代码改动——新增回归测试 `.py`——按多轮，末轮 `git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空且该轮 BLOCKER=0/HIGH=0，MEDIUM/LOW 登记；审后再改代码须再送一轮，只改 `_bmad-output` 文档/docstring 尾巴按 D-32 不占轮次不重置；第 5 轮仍有 HIGH → 停下交主 session 人审）。
- **验收单**：`_bmad-output/验收单/UAT-CARD-U9C-EVAL-<开工日>.md`，**DoD-3 双段**（段 4-A「Claude 已代验」收技术 assert：grep/pytest/响应体；段 4-B「你来验」只用 Obsidian/浏览器可做的产品体验语言，禁技术词），含：
  - **「本卡未证明什么」≥4 条**，示例：① 未证明真工厂路径（`get_review_service()` 建立 memory/graphiti 依赖后到 `:2996`）在真服务环境下的端到端 500——本卡用最小 app + `from_persisted` 离线钉屏蔽契约，工厂中段只以只读 grep 覆盖；② 未证明 legacy 坏数据在**现网** `fsrs_card_states.json` 实际存在（未连 live，未读现网文件）；③ 未证明迁移脚本 `migrate_fsrs_card_states_vault_key_g35.py --apply` 能真正解开拒启（属迁移器卡面，本卡只引其名）；④ 未证明 `logger.error`/`bug_tracker` 真把 CARD-G3-5 写进日志/bug_log.jsonl（本卡只断言响应体屏蔽 + 异常自身含消息，未断言日志落盘侧）；⑤ 未证明多 vault 同进程下的真相源串库（§〇 既有注释登记的前提缺口）是否影响本拒启面。
  - **「台账待登记条目」≥4 条**，示例：① U9-C 前提更正（CLI 拒启 → 首个命中 `get_review_service()` 的请求拒启）；② 关键发现：CARD-G3-5 消息被 `generic_exception_handler` 从 500 响应体屏蔽（设计级议题 α：是否加 `VaultScopeUnresolved` 专用处理器暴露指引）；③ legacy 兼容重做（议题 β）作为设计级议题登记不排本批（D-38）；④ 实例化抛出导致 singleton 恒 None、review 面持续 500 直到运维跑迁移脚本（可用性观察）；⑤ 新测试 `test_u9c_startup_rejection_eval.py` 登记为 U9-C 口径钉（后续若生产改 α/β 须同步翻转本测试断言）。
- **收尾**：裁判输出 tee 进 `evidence-u9c-eval/`（`.txt`，末行 `rc=$pipestatus[1]`）；commit header ≤100 含批次标记且含卡号；`*.stderr*` 不入库；**不 push**；跑完说「**复核第十四批 T4**」。
