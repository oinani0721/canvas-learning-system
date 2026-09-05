> ⚠️ 本文件是 CARD-TOOL-openapi-R2 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y5-C 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-openapi-R2]`。车道：`card-y5-review`（分支 `card/y5-review`，HEAD `03ac8bf8` + Y5-A/Y5-B 的 commit，主 session 已预合主干 03ac8bf8，venv symlink 已建），**前提 Y5-B（CARD-RV-B）已独立 commit 且工作树干净**。只读 `--add-dir /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x8-openapi`（X8 取证树 `377d289c`；只读取证，不复用——merge-tree 对主干 16 行冲突）。**用户裁决 D-14（已按默认）**：Y4-B 合入前，pyright 拦下的报错文件若不在本卡改动行且不在 `backend/app/**`，允许 `LEFTHOOK_EXCLUDE=python-typecheck git commit`，验收单须贴 pyright 原始输出 + 「报错不在本卡改动行」证明。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 / §2.2 / §2.3 / §3 裁判最低覆盖）。

# CARD-TOOL-openapi-R2 — 并卡：check-openapi-drift.py FIX 提示（cwd + 裸 python）修复 + round-3 三原形回归锁 fixture（23→26 门）

## 〇 事实
| 事实 | 位置 |
|---|---|
| FIX 串在 `scripts/spec-tools/check-openapi-drift.py:254`（台账 :42 ⑥ 写的 `:257` 是过期锚）：`"FIX: python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json  (禁手改快照)"`，`print(..., file=sys.stderr)` :253-256，仅在 `--snapshot` 判出漂移时打（随后 `return 1`）。两缺陷同一行：① 解析器是裸 `python`——本仓 lefthook 侧刚修掉的同型缺陷在本脚本自身未封堵；② 相对路径 cwd 敏感——在 `backend/` 下跑时 `scripts/spec-tools/…` 与 `backend/openapi.json` 双双不存在 | `scripts/spec-tools/check-openapi-drift.py:253-256` |
| 脚本已有 `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` :65、`BACKEND_DIR = REPO_ROOT / "backend"` :66；`X_GENERATOR_NAME = "scripts/spec-tools/check-openapi-drift.py --write"` :69 被 `test_snapshot_carries_generator_provenance` :83 依赖——**不可改** | 同文件 :65-69；`backend/tests/contract/test_openapi_snapshot_drift.py:83` |
| lefthook 侧的已修口径（本卡对齐它）：`if [ -f "backend/.venv/bin/python" ]; then PY="backend/.venv/bin/python"; else PY="python3"; fi` :54 + `"$PY" scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json` :56 / :67；:25-33 注释记录裸 `python` 为何是静默空转的三处之一 | `lefthook.yml:25-33,:54,:56,:67` |
| `_normalize` :120-134：docstring :121-129 写明**三轮终局结论**（round-1/2 键名/形状守卫被 enum 实例证伪；round-3 语境切分被 Schema 扩展 `x-*` 与 Link Object 字面 `requestBody` 证伪，反向又把名叫 `value` / `enum` 的合法属性误判为数据）故**刻意不做 required 排序**；实现 :130-134 = dict 按 key 排序、list **一律保序**、标量走 `_tag_leaf`（:103）；`canonicalize` :137；`VOLATILE_INFO_KEYS = ("x-generated-at", "x-generator")` :68 | 同文件 |
| `--snapshot` :287 无漂移打 `DRIFT: none (paths=N schemas=M)` :233；`--write` :288 打 `WROTE: <path> (paths=… schemas=…, x-generated-at=…)` :280，恒写（每次刷新 `info.x-generated-at`）；HEAD `backend/openapi.json` 静态计数 paths=193 / schemas=353，`x-generated-at` 在 :15682 | 同文件 :233,:280,:287-288；`backend/openapi.json:15682` |
| `backend/tests/contract/test_openapi_snapshot_drift.py`：`grep -c '^def test_'` = **23**；`DRIFT_TOOL = REPO_ROOT / "scripts" / "spec-tools" / "check-openapi-drift.py"` :33；`_load_drift_module()` :38-50 用 `importlib.util.spec_from_file_location` 加载（脚本无 `@dataclass`，`sys.modules` 陷阱不适用，改动 loader 不在本卡）；required / enum 族门集中在 :156-259（`test_required_order_is_drift` :156 … `test_required_bare_schema_order_is_drift` :243 … `test_enum_value_change_is_drift` :259）；末两门 :333 / :349 | 同文件 |
| 台账 :42 X8（CARD-DEBT-openapi-sync-R1，`7ba8fc07`）残留 ⑥ = FIX 提示两种 cwd 都不可照抄；⑦ = Codex LOW-3「23 门无 fixture 钉住 round-3 三原形（x-extension 字面 required / Link requestBody / 属性名 enum·value），机制删了防重引入的门没建」 | `未合卡追踪台账.md:42` |
| `tests/contract` **目录级不可跑**：同目录 `test_openapi_contract.py`（schemathesis，`from app.main import app` :18，206 operations）Z7-C 实测单 operation 整 session 208.70s 且门下 exit 3；另有 pact 文件。本卡的面级裁判 = 本文件 26 门 + `--collect-only -q tests/contract` 收集无错 | `_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:209-210`；`backend/tests/contract/` 目录清单 |
| 车道 lefthook：改 `backend/tests/**/*.py` 触发 `python-typecheck`（glob `{backend,src}/**/*.py` :147，共享 venv 含 pyright 1.1.411 ⇒ **真跑**）→ D-14 口径；`scripts/` 不在 lint/typecheck glob 内，仍自查 ruff | `lefthook.yml:147`；设计稿 §0 |
| 跨卡地盘：`check-openapi-drift.py` / `test_openapi_snapshot_drift.py` 本批**只 Y5-C 写**；`backend/openapi.json` Y5-C 仅允许 `--write` 再生且只变 `x-generated-at`；Y9-B 若形状变化须同批更新快照并声明（集成期主 session 再生一次）；`lefthook.yml` 只 Y4 | 设计稿 §5 |

## 一 完成条件（AND）
- (a) **修 :254 FIX 串两缺陷**（同一 hunk）：解析器改为「仓内 venv 解析器，存在则用、否则回落 `python3`」——与 lefthook.yml:54 同口径，用 `BACKEND_DIR / ".venv" / "bin" / "python"` 判存在；路径改为 **cwd 无关**：脚本用 `Path(__file__).resolve()`、快照用 `BACKEND_DIR / "openapi.json"`（绝对路径），或在提示里显式带 `cd <REPO_ROOT> &&`；保留尾注「(禁手改快照)」；`X_GENERATOR_NAME` :69 一字不改。
- (b) **判据 = 逐字复制实打的 FIX 串两个 cwd 各跑一次都成功**：先取真实输出——把 `backend/openapi.json` 复制到 scratch，改其中一处 `description` 后跑 `.venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --snapshot <scratch 副本>` 取 stderr 的 `FIX:` 行（rc=1 属预期）；把 `FIX: ` 之后到 `  (禁手改快照)` 之前那段**原样**在 ① 仓库根、② `backend/` 下各执行一次，两次 rc=0 且 stdout 含 `WROTE:`；两次输出 tee 进 `evidence-openapi-r2/`。**不得只做静态阅读**。
- (c) **三原形回归锁**各补 1 条 fixture 门到 `test_openapi_snapshot_drift.py`（建议紧随 :243 `test_required_bare_schema_order_is_drift` 之后，形态参照该门）：① Schema 位置的 `x-*` 扩展里携带字面 `required` 数组；② Link Object 的字面 `requestBody`；③ 名叫 `value` / `enum` 的**合法属性名**。三者的**数组顺序变化都必须报漂移**（`canonicalize` 前后不等）。`grep -c '^def test_'` 23 → **26**。
- (d) 三条 docstring **必须**写明：这是「防止重新引入 required 排序启发式」的**回归锁**；当前实现（`_normalize` :130-134 一切数组保序）下三门**本来就绿**；引用 `check-openapi-drift.py:121-129` 的三轮结论。验收单与 commit message **不得**把三门描述成「修复了漏检」「补齐了覆盖缺口」等任何暗示历史行为改变的措辞（`grep -c '漏检'` 在验收单 4-A/4-B 与 commit body 里 = 0）。
- (e) `_normalize` / `canonicalize` / `_tag_leaf` / `VOLATILE_INFO_KEYS` **行为一字不改**：`git diff HEAD -- scripts/spec-tools/check-openapi-drift.py` 只含 :253-256 附近 FIX 相关 hunk（允许为拼路径新增常量/一行 helper，但不得触及 :68 / :103-134 / :137-160）；26 门全绿；`--snapshot openapi.json` → `DRIFT: none (paths=193 schemas=353)`。
- (f) **`backend/openapi.json` 处置**：(b) 的两次 `--write` 会改写快照；跑完 `git diff backend/openapi.json | grep -E '^[-+] ' | grep -vc 'x-generated-at'` 必须 = 0（只有时间戳变），然后二选一并在验收单写明：① 用 `git checkout HEAD -- backend/openapi.json` 还原（仅在该文件**未暂存**时；此命令同时写 index 与工作树）；② 如实提交只含 `x-generated-at` 变化的再生快照。禁手改。
- (g) **面级裁判**（协议 §3）：本文件 26 门 + `--collect-only -q tests/contract` 收集无错（不执行 schemathesis）；`ruff check` 与 `ruff format --check` 两文件（先对 HEAD 版跑一次基线，只对本卡引入的漂移负责）；pyright 按 D-14：本卡改动行 0 报错，存量报错走 `LEFTHOOK_EXCLUDE=python-typecheck` 并贴原始输出。
- (h) **Codex 一轮**，prompt `_bmad-output/审查/prompts/codex-prompt-CARD-TOOL-openapi-R2.md` 五分节：§一 最小读取面写死 = `git diff <Y5-B 末 commit> HEAD -- scripts/spec-tools/check-openapi-drift.py backend/tests/contract/test_openapi_snapshot_drift.py` + 脚本 :60-160 + 测试 :30-60 与新增三门；§二 作者自述（本卡 commit message + 三门 docstring）标「请独立核对」；§三 按重要性：① FIX 串在 CI（无 venv）与本机两种环境下是否都可照抄；② 三门是否真能在「有人重新引入 required 排序」时变红（请给出会让它们红的最小改动位置，只描述不实施）；③ 三门 docstring 有没有夸大成「修复」；④ `_normalize` 等四处是否零行为改动；§四 输出格式 + 末行「BLOCKER/HIGH 清零：是/否」；§五 边界。prompt 按协议 §2 禁用词清单 grep 计数 = 0，协议 §2 点名的旧模型名 grep 计数 = 0。存档首部按协议 §2.1；`.stderr` 不入库。
- (i) **「本卡未证明什么」必填**：三门在当前实现下本来就绿——不证明任何历史漏检被修；不证明 CI 环境上 FIX 串可用（无 venv 时回落 `python3`，未在 GitHub 实跑）；不跑 `tests/contract` 目录级（schemathesis 面归 Y5-D）；不证明 openapi.json 内容正确（只证明与 `app.openapi()` 归一化后一致）。**「台账待登记条目」必填**：X8 ⑥⑦ 关闭；勘误「FIX 串锚 :257 → :254」；23→26 门；openapi.json 处置方式（还原 / 时间戳再生提交）。

## 二 裁判命令
（`<树>` = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review`；`PYTEST=$(pwd)/backend/.venv/bin/pytest` 在树根设；承重裁判 `2>&1 | tee <树>/_bmad-output/审查/evidence-openapi-r2/<name>-$(date +%Y%m%dT%H%M%S).txt`，末行 `rc=${pipestatus[1]}`（zsh）/ `${PIPESTATUS[0]}`（bash））
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/contract/test_openapi_snapshot_drift.py` → `26 passed`（开工先跑一次 HEAD 版 → `23 passed` 作基线）。
2. `grep -c '^def test_' <树>/backend/tests/contract/test_openapi_snapshot_drift.py` → `26`。
3. 取真实 FIX 串：`cp <树>/backend/openapi.json <scratch>/stale.json`，用 python 改一处 `description` 后 `cd <树>/backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --snapshot <scratch>/stale.json` → rc=1、stderr 含 `FIX: `（原文抄进验收单）。
4. FIX 串在仓库根：`cd <树> && <逐字复制 FIX 串>` → rc=0，stdout `WROTE: … (paths=193 schemas=353, x-generated-at=…)`。
5. FIX 串在 backend/：`cd <树>/backend && <同一 FIX 串逐字>` → rc=0，stdout `WROTE:`。
6. `cd <树> && git diff backend/openapi.json | grep -E '^[-+] ' | grep -vc 'x-generated-at'` → `0`；随后按 (f) 处置。
7. `cd <树>/backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --snapshot openapi.json` → `DRIFT: none (paths=193 schemas=353)`，rc=0。
8. 零行为改动：`cd <树> && git diff <Y5-B 末 commit> HEAD -- scripts/spec-tools/check-openapi-drift.py | grep -E '^@@'` → 每个 hunk 头的行号都落在 :240-297 区间之内（或新增常量所在的 :60-70 区间），**不得**出现 :100-160 的 hunk。
9. 收集面：`cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST --collect-only -q -p no:cacheprovider tests/contract 2>&1 | tail -3` → 无 `error`（不执行）。
10. `cd <树> && ruff check scripts/spec-tools/check-openapi-drift.py backend/tests/contract/test_openapi_snapshot_drift.py && ruff format --check <同两文件>`（用 `backend/.venv/bin/ruff`）→ 与 HEAD 基线比较，本卡零新增。
11. `git -c core.quotepath=false ls-files --cached | grep -c '\.stderr'` = 0；`git status --porcelain | grep -v '^??'` 为空。

## 三 禁改与隔离
- 禁手改 `backend/openapi.json`（只许 `--write` 再生且只变 `x-generated-at`，见 (f)）。
- 禁改 `_normalize` / `canonicalize` / `_tag_leaf` / `VOLATILE_INFO_KEYS` / `X_GENERATOR_NAME` 的行为；禁改 `_load_drift_module` :38-50。
- 禁把三原形 fixture 描述成「修复漏检」；禁在 commit message 里写自己的 hash。
- 禁改 `lefthook.yml`（Y4 独占）；禁接 CI / 改 `.github/workflows/**`；禁改 `backend/app/**`（openapi 形状由 Y9-B 负责）。
- 禁跑 `tests/contract` 目录级执行（只 `--collect-only`）、`tests/integration` / `tests/e2e`、`tests/unit` 目录级。
- 禁连 7691 / 7687（`--snapshot` / `--write` 只 import `app.main` 取 `app.openapi()`，不起 lifespan；如门计数行出现 blocked，如实记录并登记）；live vault 只读。
- pyright 拦下时按 D-14：只对**不在本卡改动行且不在 `backend/app/**`** 的存量报错用 `LEFTHOOK_EXCLUDE=python-typecheck`，验收单贴原始输出与 diff 行号求交证明；本卡改动行必须 0 报错。
- 台账不改；`*.stderr*` 不入库；不 push。

## 四 Codex / 验收单
命令：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-TOOL-openapi-R2.md)" > <树>/_bmad-output/审查/codex-review-CARD-TOOL-openapi-R2.md 2> <树>/_bmad-output/审查/codex-review-CARD-TOOL-openapi-R2.stderr </dev/null`（1 轮；0 字节重发一次后主 session 人审）。顺序固定：**代码与门定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`**；审后再改代码 = 失绑须登记。存档首部按协议 §2.1。验收单 `<树>/_bmad-output/验收单/UAT-CARD-TOOL-openapi-R2-<日期>.md`：DoD-3 双段（4-A Claude 已代验：裁判 1-11 原始输出引用 + Codex 逐条采信/驳回；4-B 你来验：「无变化（一条给开发者看的『怎么修』提示以前在某些目录下照抄会失败，现在两处都能照抄；另外给一个已经删掉的旧机制加了三道『别再加回来』的门）」零技术词）；「本卡未证明什么」「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100（`wc -m`）；不 push；**独立 commit 后同一标签页粘 Y5-D**；跑完说「复核第十二批 Y5」。
