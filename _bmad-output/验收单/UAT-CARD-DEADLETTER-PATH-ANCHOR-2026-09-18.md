# UAT — CARD-DEADLETTER-PATH-ANCHOR

> 批次: `BATCH-2026-09-18-第十五批` · 车道 `P2-A`（`card-p2-outbox` / 分支 `card/p2-outbox`）· 本车道第 1/3 张
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P2-A.md`
> 起点 B15_BASE: `9c4e7e82` · **最终代码 SHA**: `bfeefadd` · **commit 数**: 代码面 **2**（`7f5e53d2` 主改动 + `bfeefadd` openapi 还原）+ 文档 commit（`83910c89` 起，零代码面） · **Codex 轮次**: `1（round-1 即 BLOCKER=0 / HIGH=0 且绑最终 HEAD）`
> 证据目录: `_bmad-output/审查/evidence-deadletter-path-anchor/`

## 〇 一句话

后端「没能存进知识库的学习记录」（死信）原先写到**相对当前工作目录**的 `data/dead_letter_episodes.jsonl`，
而追踪页 `/traces` 读的是 backend 的绝对路径 —— 两边只有在恰好从 backend 目录启动时才对得上。
本卡把写侧锚定成 `app.core.failure_counters.DEAD_LETTER_EPISODES_PATH`，读侧直接 import **同一个对象**，
并给 `tests/unit` 里两条会往真死信文件追加记录的用例打了桩。

---

## 一 §〇 事实复核 —— 卡文 → 实测（漂移逐条登记）

开工第 0 分钟按卡文 (a) 逐条 `sed -n` / `grep -nF` 复核。**行号零漂移**，另有 5 条事实漂移：

| # | 卡文写 | 本树实测 | 处置 |
|---|---|---|---|
| 1 | 本树 `backend/data/` 现存 4 个 jsonl（dead_letter 99915 B 等） | **四个全部不存在**（只有 `.gitignore` / `presets/` / `reference_priority.json`） | 本车道是 NEW worktree，卡文那条是在主干树 `feature-obsidian-hybrid-dev` 实测的。snap 改为显式输出 `ABSENT` 并加末行验伪锚（读一个已知存在的文件），避免「命令没跑成」与「结果为零」共用空串 |
| 2 | (b)③/(g)③ 定向 `-k "increments_counter or logs_warning"` → `collected 2` | **collected 29 / 25 deselected / 4 selected**（2 passed + 2 skipped） | `-k` 匹配 nodeid 子串，另有 2 条同名片段的用例被 skip。判据改看「跑前跑后行数差」，收集数如实贴档 |
| 3 | (i) 名单套件「0 failed」 | **1 failed** = `test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores` | **主干既有红**，双重证据：① 在第十五批红基线第 25 行；② 在本树**改代码前**的 `tests/unit` 目录级红名单第 24 行。本卡未引入 |
| 4 | §〇 pyright `81 warnings` | **80 warnings**（errors 恒 0） | 改前改后同为 `0 errors, 80 warnings, 0 informations` |
| 5 | §〇 tests/unit 写脏候选集 10 文件 | 真实写者里有 **2 个不在该候选集内**（见 §三） | 候选集是按 `write_dead_letter` 等**直接**调用 grep 出来的，漏掉了经 `service._sync_edge_to_neo4j` **间接**触发的写者 = 该候选集的假阴面，如实登记 |

AST 门报告的行号是 `FunctionDef.lineno`（`def` 那一行）而非默认值所在行，故改前输出为 `('__init__', 224, …)` 与 `('__init__', 303, …)`，
对应卡文所称的 `:224` / `:306`。两者指同一对默认值。

---

## 二 DoD-3 段 4-A：Claude 已代验（逐条贴证据）

> 跑法纪律：git 输出一律 `--no-color`；含 `exit`/`cd` 的块包 `( … )` 子 shell；
> 承重跑 `2>&1 | tee <file>.txt` 后 `echo rc=$pipestatus[1]`；ruff 判据 zsh 数组 + F821 锚。

### (a) 第 0 分钟

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-p2-outbox` ✅ |
| `git branch --show-current` | `card/p2-outbox` ✅ |
| `git rev-parse --short=8 HEAD` | `9c4e7e82` = B15_BASE ✅ |
| `git status --porcelain \| wc -l` | `0` ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在（venv 为目录级 symlink → `card-v5-lance/backend/.venv`）✅ |
| pyright `test -x "$P"` | `EXEC_OK` ✅ |
| 红基线 `grep -vc '^#' "$BASE"` | **33** ✅ |

### (b)(f) 结构判据 —— 成对 + 验伪锚

| 判据 | 改前 | 改后 | 存档 |
|---|---|---|---|
| `grep -cF '"data/dead_letter_episodes.jsonl"' episode_worker.py` | **2** | **0** | `struct-gate-before-20260918T171020.txt` / `struct-gate-after-20260918T171141.txt` |
| `grep -cF 'DATA_DIR / "dead_letter_episodes.jsonl"' traces.py` | **2** | **0** | 同上 |
| AST：FunctionDef 默认值中以 `data/` 开头的 str 常量 | **2** | **0** | `ast-gate-before-20260918T171020.txt` / `struct-gate-after-…txt` |
| `grep -cF 'DEAD_LETTER_EPISODES_PATH'`（fc / ew / traces） | **0 / 0 / 0** | **1 / 5 / 5** | 同上（卡文要求 ≥1 / ≥3 / ≥3） |
| **验伪锚** `grep -cF 'EDGE_SYNC_DEAD_LETTER_PATH' traces.py` | **2** | **2** | 恒定 ⇒ `grep -cF` 能命中已知正例，上面的 0 不是「没跑成」 |
| **验伪锚** 同一份 AST 门脚本喂已知正例 | **1** | **1** | 恒定 ⇒ 门本身有效 |

> AST 门验伪锚的探针文件放在 session scratchpad 而非卡文所写的仓内 `backend/_astprobe_tmp.py`：
> 用户级 guard hook 拦 `rm` 仓内文件（实测 `PreToolUse:Bash hook error`）。AST 门读的是 `argv[1]` 指定的文件路径，
> 位置不改变判据语义，且彻底消除仓内残留风险。正式判据与验伪锚走**同一份**门脚本（`ast_gate.py`），不是两份手抄。
> 仓内残留自证：`git status --porcelain` 中 `_astprobe` / `_ruffprobe` 命中数 = **0**。

### (b)②(g)① 行为门 —— 先红后绿

| 阶段 | 结果 | 存档 |
|---|---|---|
| 改代码**前** | `collected 5 items` / **5 failed** | `anchor-red-20260918T170921.txt` |
| 改代码**后** | `collected 5 items` / **5 passed**, rc=0 | `anchor-green-20260918T174112（fmt 整改后重跑，为最终态；首次 20260918T171146 同为 5 passed）.txt` |

改前 5 条红在**各自的路径断言**（非 import / 夹具错）——这是刻意设计：常量在改前并不存在，
若顶层 `from … import DEAD_LETTER_EPISODES_PATH` 会让先红档退化成 collection error，
故测试内一律走 `getattr(failure_counters, "DEAD_LETTER_EPISODES_PATH", None)`。改前失败正文摘录：

- `test_default_anchor_is_absolute_under_backend` → `AssertionError: app.core.failure_counters.DEAD_LETTER_EPISODES_PATH 不存在 —— 死信默认路径仍是 cwd 相对串`
- `test_default_store_writes_to_anchor_not_cwd` → `AssertionError: 死信没写到锚上；cwd=/private/var/…/test_default_store_writes_to_a0/elsewhere 下的落点才是真实去向`
- `test_worker_default_resolves_to_same_anchor` → `AssertionError: dead_letter_path 默认值在 def 期就绑定了: 'data/dead_letter_episodes.jsonl'`
- `test_traces_reads_exactly_where_worker_writes` → `AssertionError: 写侧锚 DEAD_LETTER_EPISODES_PATH 不存在，读侧无从同源`
- `test_no_cwd_relative_default_left_in_episode_worker` → `AssertionError: 仍有 cwd 相对默认值: [('__init__', 224, …), ('__init__', 303, …)]`

**新测试自身零写脏**：改前那次跑的前后 snap 逐字相同（chdir 到 tmp_path 保护；第 1/3 条在锚断言处即红，根本不走到落盘）。

### (b)③(g)②(g)③ 写脏门 —— 先有差后全等

| 判据 | 改前 | 改后 |
|---|---|---|
| 定向 `-k "increments_counter or logs_warning"` 跑前后 `failed_edge_syncs.jsonl` | `4 → 6`（**+2**），sha 变 | `8 → 8`，**行数与 sha 逐字同** ✅ |
| `tests/unit` 目录级跑前后四个 jsonl | `ABSENT/ABSENT/ABSENT/ABSENT` → `4 / 3 / ABSENT / ABSENT` | `8 / 6 / ABSENT / ABSENT` → `10 / 9 / ABSENT / ABSENT`，**不全等**（见下方如实说明） |

> 目录级改前档同时是写者 census：`failed_edge_syncs` +4、`failed_writes` +3、
> **`dead_letter_episodes` 与 `bug_log` 零增量**（本卡目标文件在 `tests/unit` 面本就无活写者——
> `test_episode_worker_coverage_epw.py` 的隔离纪律有效）。

### ⚠️ 写脏门 (g)② 不全等 —— 如实说明（不为让门变绿而越界）

卡文 (g)② 要求「收工 `tests/unit` 目录级跑前后四个 jsonl 逐字同」。**本卡地盘内无法达成**，如实报告：

| 文件 | 改前目录级 | 收工目录级 | 判定 |
|---|---|---|---|
| `dead_letter_episodes.jsonl` | ABSENT → ABSENT | ABSENT → ABSENT | ✅ **全等**（本卡目标文件） |
| `bug_log.jsonl` | ABSENT → ABSENT | ABSENT → ABSENT | ✅ 全等 |
| `failed_edge_syncs.jsonl` | `+4` | `+2` | **本卡负责的那 2 行已归零**，剩余 2 行来自地盘外 |
| `failed_writes.jsonl` | `+3` | `+3` | 本卡零责任面（全部来自地盘外） |

**「剩余增量全部来自地盘外」有两条互相独立的证据**，不是「我只打扫到这里」：

1. **定向判据**：`-k "increments_counter or logs_warning"` 跑本卡打桩的两条，改前 `4 → 6`（+2）、改后 `8 → 8`（**全等**）。
2. **整文件判据**（本卡补充，卡文未要求）：跑**整个** `test_failure_observability.py`（`collected 29`、26 passed / 3 skipped），
   前后 snap **逐字同** ⇒ 该文件内没有第三个写点（`tfo-full-after-20260918T173801.txt`）。这同时回答了 Codex 问题③。
3. **归因对账**：写者定位得地盘外 4 个文件的 delta 之和 = `(1+1) + (1+2)` = `+2 / +3`，与收工目录级实测的
   `+2 / +3` **逐数对上**；改前的 `+4` 减去本卡打桩的 tfo 两条 = `+2`，也对上。

按 (e)②「地盘外只登记不改」，这 4 个文件未改（详见 §三）。**绝不为把门刷绿而去改白名单外的文件。**

### (o) 附：`ruff format` 门与 `LEFTHOOK_EXCLUDE=python-lint` 的使用与证明

首次 commit 被 lefthook `python-lint` 阻断（`🥊 python-lint (0.03 seconds)`）。该 hook 分两段：
`ruff check`（通过）与 **`ruff format --check`**（失败）—— 即协议 §2.3 记载的「主干既有 462 文件格式漂移」条款。

**归属诊断**（先诊断再动手，没有直接 EXCLUDE）：

- dirty 集初判 = `{failure_counters.py, test_dead_letter_path_anchor.py}`。
- `test_dead_letter_path_anchor.py` 是**本卡新增**，无「主干既有」可言 ⇒ 不享受过渡条款，直接 `ruff format` 修好（`1 file reformatted`）。
- `failure_counters.py`：把它在 **B15_BASE `9c4e7e82`** 上的原版取到临时目录单独跑 `ruff format --check` → **同样 dirty** ⇒ 主干既有。

**但这里有个真实的两难**：卡文 (c)① 要求新常量「与 `:32-34` **同形锚**」，而那个「同形」（多行括号）**本身就是主干的既有漂移**；
照抄 = **在本卡改动行上新增漂移**，而过渡条款要的证明恰恰是「漂移不在本卡改动行」。
处置：把新常量写成**单行**（`ruff format` 的终态形态），并在代码注释里写明排版差异的原因。
锚的构造方式（三层 `.parent` → `data` → 文件名）与既有两条**完全相同**，丢的只是排版；
D-40 定的整仓 format 落地后既有两条也会变成单行，届时三条自然一致 —— 单行是**提前对齐终态**，不是不一致。

**整改后的证明**（协议 §2.3 要求的形态）：

- 本卡 5 个文件 `ruff format --check` → `1 file would be reformatted, 4 files already formatted`；
- `ruff format --diff backend/app/core/failure_counters.py` 的全部改写落在 **`EDGE_SYNC_DEAD_LETTER_PATH` 与
  `DUAL_WRITE_DEAD_LETTER_PATH` 这两条既有行**上，**本卡改动行零漂移** ⇒ dirty 集 ⊆ 主干既有集 ✅
- 因 lefthook 把 `ruff check` 与 `ruff format --check` 绑在同一个 hook 里、无法只跳过后者，
  故以 `LEFTHOOK_EXCLUDE=python-lint` 提交；**`ruff check` 部分已单独跑过并 `rc=0`**（`ruff-after-fmt-…txt`），跳过的只是 format 检查。
- ⛔ **全程未跳过 `python-typecheck`**（卡文硬禁），该 hook 在两次 commit 中均为 `✔️`。
- ⛔ 未改既有两行的排版 —— 那属「顺手修存量」，归 D-40 主 session 末位整仓 format。

**fmt 整改改动了代码，故按本批新条在当前 HEAD 重跑了全套承重裁判**：结构门 `0/0/1/5/5`、验伪锚 `2/1`、
AST 门 `0`、行为门 `collected 5 / 5 passed` 且零写脏、pyright `0 errors, 80 warnings`、ruff check `rc=0`
（存档后缀 `-fmt-20260918T174112`）。

### (h) pyright 保持 0

`(cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')`（绝对路径 + `test -x` 自证；⛔ 未用 `| tail` 取汇总）

- 改前：`0 errors, 80 warnings, 0 informations`（`pyright-before-20260918T170953.txt`）
- 改后：`0 errors, 80 warnings, 0 informations`（`pyright-after-20260918T171252.txt`）—— **逐字相同**
- ⛔ 全程未用 `LEFTHOOK_EXCLUDE=python-typecheck`

### ruff（本卡改动文件）

`files=5`、`All checks passed!`、`rc=0`（`ruff-after-20260918T171252.txt`）。
**验伪锚用 F821 而非 F401** —— `backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 不含 F401，
用 F401 做锚会恒不触发（= 锚选在没启用的规则上）。实测 F821 探针 `锚rc=1` ✅

### (i) 既有套件

| 套件 | 结果 |
|---|---|
| 名单 8 文件（收工） | `1 failed, 177 passed, 3 skipped` —— 该 1 red 为**主干既有**（见 §一 #3 双重证据） |
| `tests/regression` 目录级 | **1913 passed, 6 skipped, 1 xfailed, rc=0**，FAILED/ERROR 集合为**空**（`regression-close-20260918T171328.txt`） |
| `tests/unit` 目录级 diff（base vs close） | `base(33) vs close(32)`：唯一差异是一个 `<`（flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`，基线注释已标注）⇒ **零 `>`**。
`open(32) vs close(32)`：**rc=0，逐字相同** —— 这是最严口径（同一棵树、改代码前 vs 改代码后），说明本卡既未引入新红也未意外修好任何既有红。
passed 数 `5731 → 5736`（+5 = 本卡新增的 5 条门）。W4 哨兵 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |

开工 `tests/unit` 目录级（改代码**前**）：`32 failed, 5731 passed, 44 skipped, 13 xfailed`，
与第十五批红基线 diff **只有一个 `<`**（`test_candidate_service::test_accept_candidate_already_accepted_returns_422`，
基线注释已标注为 flaky），**零 `>`** ⇒ 本树开工无新红。W4 哨兵：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。

### (k) 负控输入三段

三段各只拆一层，EXIT trap `git show HEAD:<path> > <path>` 还原（HEAD 自证 = `bfeefadd`，**已含本卡代码**）：

| 段 | 拆掉的那一层 | 变红 | 仍绿（承重） | 还原自证 |
|---|---|---|---|---|
| ① | 绝对锚（常量改成 `Path("data/…")`） | **1 failed**：`test_default_anchor_is_absolute_under_backend`，正文 `AssertionError: 锚不是绝对路径: data/dead_letter_episodes.jsonl` + `where False = is_absolute()` | 其余 **4 条 passed** ⇒ 该门只绑锚，不靠别的门陪红 | shasum 前后逐字同 **且** 相对串 `grep -cF` 由 1 → **0** |
| ② | 运行时解析同一常量（`else` 分支改回相对字面量） | **3 failed**：`test_default_anchor_is_absolute_under_backend` / `test_default_store_writes_to_anchor_not_cwd`（正文含 `cwd=…/elsewhere`）/ `test_worker_default_resolves_to_same_anchor` | `test_no_cwd_relative_default_left_in_episode_worker`（AST）与 `test_traces_reads_exactly_where_worker_writes` **仍 passed** ⇒ 结构门与行为门测的不是同一件事 | shasum 前后逐字同 |
| ③ | 本卡在 tfo 加的两处 patch | 写脏门红：`failed_edge_syncs.jsonl` `10 → 12`（**+2**），sha 变 | — | shasum 前后逐字同 |

**三段变红的 nodeid 集合互不相同**，故不是「一道门穿了三件衣服」。

> ⚠️ **负控① 首轮是假绿，必须记进来**：首轮脚本里的变异串仍是**多行括号**形式（见 §二.补 的 fmt 整改），
> 而文件已被改成单行 ⇒ `assert s.count(old) == 1` 抛 `AssertionError`，**变异根本没写进文件**，
> 测试却照跑并打出 `5 passed`。若只扫汇总行，这会被读成「门覆盖不到这一层」甚至「已验证」。
> 尤其要注意：**跑前/跑后 shasum 相同在这种情况下也不是还原正确的证据** —— 它同样可以是「压根没改过」，
> 两种情况的数字一模一样。重跑版（`negctl-1-anchor-r2-20260918T174446.txt`）因此加了两道自证：
> 注入后 `grep -cF` 相对串 = **1**（证明真的改进去了）、还原后 = **0**（证明真的改回来了），
> 并让注入失败**硬退出**（`|| { echo "!!! 变异注入失败 —— 本段作废，不跑门"; exit 9; }`）而不是继续跑门。
> 首轮存档 `negctl-1-anchor-20260918T174306.txt` 一并入库，作为该假绿形态的实物。

### (l) 地盘门

`git --no-pager -c core.quotepath=false diff --stat --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'`（`territory-20260918T174255.txt`）：

```
 backend/app/api/v1/endpoints/traces.py             |  27 ++---
 backend/app/core/failure_counters.py               |  11 ++
 backend/app/services/episode_worker.py             |  13 ++-
 backend/tests/unit/test_dead_letter_path_anchor.py | 116 +++++++++++++++++++++
 backend/tests/unit/test_failure_observability.py   |  38 +++++--
 5 files changed, 178 insertions(+), 27 deletions(-)
```

⊆ (l) 白名单 ✅。禁改文件（`main.py` / `memory_service.py` / `tips.py` / `question_generator.py` / `bug_tracker.py` / `openapi.json`）diff **全空** ✅。

**验伪锚**：去掉 `':(exclude)_bmad-output'` 后多出 **35** 个 `_bmad-output/` 路径 ⇒ exclude 确实在起作用，上面的白名单结果不是「diff 恒空」造成的（post-commit 跑，锚非空洞）。

**`episode_worker.py:600` 零改动**：`git --no-pager diff --no-color -U0 9c4e7e82 HEAD -- backend/app/services/episode_worker.py` 的全部 hunk 头为
`@@ -32,0 +33 @@`、`@@ -207 +208,2 @@`、`@@ -224,2 +226,5 @@`、`@@ -306 +311 @@` —— 触及旧文件的最大行是 **:306**，:600 不在任何 hunk 的覆盖区间内 ✅（P1 G4-5 的交集行未被碰）

### (j) openapi

不改端点 —— `traces.py` 只改了 import、两处 dict value 与两段注释，路由（`:389` / `:441` GET、`:465` POST）
与 response 形状零改动，`BACKLOG_FILES` 键集合仍是 8 项。⚠️ 但 lefthook `spec-sync-flat`（glob `backend/app/{api,models,schemas,mcp}/*.py`）**递归**匹配到了
`backend/app/api/v1/endpoints/traces.py`，于是在第一次 commit 时重生成并 stage 了 `backend/openapi.json`
（hook 原始输出：`WROTE: backend/openapi.json (paths=199 schemas=357, x-generated-at=2026-09-18T09:39:08.605948+00:00)` /
`[Spec Sync] + backend/openapi.json staged`；`spec-sync-root (skip) no matching staged files`）。
实测该文件相对 `9c4e7e82` 的**非 `x-generated-at` 变更行数 = 0**（只有时间戳一行），
故按卡文 (j) 走**单独一个只含 openapi.json 的还原 commit** `bfeefadd`（零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`）。
核：`git --no-pager diff --stat --no-color 9c4e7e82 HEAD -- backend/openapi.json` → **空** ✅

### (m) 现网只读

本卡不连任何 Neo4j（7691 / 7687 / 7692 一概不连 —— 全部判据为静态 grep/AST 或 tmp_path 内的单元测试），
不写 live vault，不碰 `fsrs_bridge.py` / `decay_beta.py`。本树 `backend/data/*.jsonl` 只做 `wc -l` / `shasum` 读取，
**不删不清不改**。判据：`grep -rn -e 'fsrs_bridge' -e 'decay_beta' -e '7691' -e '7687' -e 'canvas-vault' <本卡改动文件>` → **全 0**（`fsrs_bridge` / `decay_beta` / `7691` / `7687` / `canvas-vault` 各 0 命中，`readonly-grep-20260918T171621.txt`）。
**验伪锚**：同一组文件里 `DEAD_LETTER_EPISODES_PATH` 命中 **13** 行（>0）⇒ grep 确实读到了这些文件，上面的 0 是真 0。

### (n) Codex

**round-1**：`gpt-6-astra` · `model_reasoning_effort=ultra` · `codex-cli 0.153.3`，
存档 `_bmad-output/审查/codex-review-CARD-DEADLETTER-PATH-ANCHOR.md`（3585 B，非 0 字节）。
审查绑定 `bfeefadd` = **当前 HEAD**；`git --no-pager diff --stat --no-color bfeefadd HEAD -- . ':(exclude)_bmad-output'` → **空** ⇒ 仍绑定 ✅
自检：首部 `模型 / reasoning_effort / codex` 三字段齐；存档内协议 §2 禁用的旧复核模型名计数 = **0**；
`No such file` / `does not exist` 计数 = 0；`.stderr` 由 `.gitignore:264` 覆盖、未入库。

**结果：BLOCKER = 0、HIGH = 0**，MEDIUM × 2、LOW × 6 ⇒ **D-15 满足（绑最终 HEAD 的那一轮 B/H 归零），本卡 1 轮收敛**。
按协议 §1「其余 BLOCKER/HIGH/MEDIUM/LOW 登记不阻断」，且「修一条已判通过的 LOW = 亲手打破终审绑定」，
以下逐条**登记不改**（无一条被驳回为「不成立」而不给理由）：

| # | 级别 | 位置 | Codex 的意见 | 车道裁定 |
|---|---|---|---|---|
| 1 | MEDIUM | `test_dead_letter_path_anchor.py:44` | 门硬编码目录名 `backend`，在 `/app/app/core/…` 布局下会误拒正确落点 `/app/data/…` | **成立，登记不改**。① 卡文 (e)③ 写死了 `parts[-3:] == ("backend","data","dead_letter_episodes.jsonl")`；② 这是**既有模式**——`test_traces_backlog_t6c.py:228-243` 对同一批文件用的是同一条断言；③ 该门是 unit 门、只在开发树跑。改它 = 偏离卡文且与既有门不一致，建议与 §四 未证明 #2（容器布局）合并成一张后续卡 |
| 2 | MEDIUM | `test_…anchor.py:82,113` / `episode_worker.py:677` | 单例工厂是**门未覆盖的路径**：若工厂改为显式传相对串，五条门仍会全绿 | **成立，登记不改**。卡文 (e)③ ⛔ 明文禁止在新门里调 `get_episode_worker()` / `cleanup_episode_worker()`（模块级 `_worker_instance` 跨用例残留）。当前工厂确为无参实例化（Codex 亦确认），`sed -n '673,678p'` 可证。建议后续用 AST 门覆盖「工厂调用点的实参必须为空」，登记 |
| 3 | LOW | `episode_worker.py:230-231` / `test_…anchor.py:70-74` | **若**负控只是把 `else` 换成**字符串**字面量，转红会来自 `.parent` 的 `AttributeError`，不足以证明检测到 cwd 回归 | **前提不成立（澄清，非驳回）**。Codex 用的是条件句，因为限定读取面里没有负控脚本。实际负控② 注入的是 **`Path("data/dead_letter_episodes.jsonl")`（保持 `Path` 类型）**，正是 Codex 说的合格形态；实际失败正文是 `AssertionError: 死信没写到锚上；cwd=…/elsewhere 下的落点才是真实去向` + `where False = exists()`，**不是** `AttributeError`。证据：`negctl-2-runtime-20260918T174306.txt`。Codex 同时确认「现有门确实检查真实写出及 cwd 下无 `data/`，并非夹具自行创建目标文件」 |
| 4 | LOW | `failure_counters.py:48` / `traces.py:51,58,65` | `/app/app -> /release/app` 这类符号链接下，词法锚与 `resolve()` 锚会分叉 | **成立，登记不改**。Codex 自己指出「episode 两张表直接引用共同常量，不受此差异影响」⇒ 本卡目标面无问题；分叉风险落在**既有** `failed_edge_syncs` 面。已写入 §四 未证明 #2 |
| 5 | LOW | `test_…anchor.py:46` / `episode_worker.py:231` | 未打桩的默认构造器会 `mkdir` 真实 `backend/data`，故文件头「全部落 tmp_path」的声明不成立 | **成立，登记不改**。该 `mkdir(parents=True, exist_ok=True)` 在本树是 no-op（`backend/data/` 已存在，含 `.gitignore`/`presets`/`reference_priority.json`），四份 JSONL 的 `wc -l`+`sha` 确实覆盖不到「目录创建」这件事。⚠️ 这是一条**真实的文档不实**（docstring 说得比代码管用）。**不改的理由**：协议对 LOW 是登记不是修，而改 docstring 会让终审绑定从「逐字空」变成「需主 session 按 D-32 逐行等价核」——为一句文案换掉一个干净的绑定不划算。**建议回写卡文**：把该句改为「除 `test_default_anchor_is_absolute_under_backend` 会构造默认 store（只 `mkdir`、不建文件）外，其余落 tmp_path」 |
| 6 | LOW | `episode_worker.py:226,230,311,316` | 显式 `None` 与不传当前语义一致、旧实现也已转 `Path`，但限定读取面未覆盖全部调用方，故 pyright 0 不能证明 15 处调用均已独立核验 | **成立（核验边界声明），登记**。本卡对这 15 处的证据是静态的：`git grep -n -e 'dead_letter_path=' -e 'DeadLetterStore('  -- backend/tests` → 17 行 = 15 处调用 + 2 行 docstring，**全部显式传 `str(...)`**，走 `file_path is not None` 分支，与改前逐字同语义。已写入 §四 未证明 #7 |
| 7 | LOW | `test_failure_observability.py:196,220,250,338` | `:338` 只给了签名，限定读取面不足以确认 DUAL_WRITE 方法体、排除第三类真实写点、或验证目录级前后行数与哈希 | **已用独立证据补上（登记）**。本卡补跑了卡文未要求的**整文件**判据：跑完整个 `test_failure_observability.py`（`collected 29`、26 passed / 3 skipped），前后四 jsonl snap **逐字同** ⇒ 该文件内**没有第三类真实写点**（`tfo-full-after-20260918T173801.txt`）。目录级前后 snap 见 `data-{before,after}-unit-close-20260918T171328.txt` |
| 8 | LOW | `traces.py:55,82` | 注释与范围核验，**无新增问题**：`bug_log` 仍依赖 cwd 已如实说明；「每一条都是导入常量」限定于 `BACKLOG_FILES` 且与代码相符；`main.py`/`memory_service.py`/`bug_tracker.py`/`openapi.json` 零改动 | **确认，无待办** |

> **未改任何代码 ⇒ 未触发再审**。审后本卡只改 `_bmad-output`（存档 + 验收单），符合卡文 (n) 的顺序要求。

---

## 三 tests/unit 写脏 backend/data —— 写者定位结果

写者集合**完备**（各文件 delta 之和 = 目录级实测总增量，不是「我只找到了这几个」）：

| 写者 | delta | 归属 | 处置 |
|---|---|---|---|
| `tests/unit/test_failure_observability.py` `:176` `test_edge_sync_failure_increments_counter` | +1 | **本卡地盘** | 已打桩（`tmp_path` + `patch("app.services.canvas_service.EDGE_SYNC_DEAD_LETTER_PATH", dl_path)`，与同文件 `:208` 那条逐字同形） |
| `tests/unit/test_failure_observability.py` `:234` `test_edge_sync_failure_logs_warning` | +1 | **本卡地盘** | 已打桩（与 `caplog.at_level` 并列写在一个括号 with 里，同文件 `:338` 已有的并列风格） |
| `tests/unit/test_canvas_edge_bulk_sync.py` | +1 | 地盘外 | **只登记不改**；建议 patch 目标串 `app.services.canvas_service.EDGE_SYNC_DEAD_LETTER_PATH` |
| `tests/unit/test_canvas_edge_sync.py` | +1 | 地盘外 | 同上 |
| `tests/unit/test_agent_memory_trigger.py` | +1 | 地盘外 | 写的是 `failed_writes.jsonl`；建议 patch 目标串 `app.core.failed_writes_constants.FAILED_WRITES_FILE`（消费方模块属性） |
| `tests/unit/test_story_30_22_agent_trigger_deep.py` | +2 | 地盘外 | 同上 |

合计 `2 + 1 + 1 + 1 + 2 = 7` = 目录级实测 `failed_edge_syncs +4` + `failed_writes +3` ✅ 对上。

定位方法：先按落盘记录的内容字段（`edge_id` / `canvas_name` / `error` / `concept`）反查候选文件，
再逐候选文件跑 pytest 比对三个 jsonl 的总行数（`writer-locate-20260918T170505.txt`）。
**验伪锚**：同一脚本对 `test_failure_observability.py` 在打桩前必须打出 `WRITER … delta=2` ✅（改前定向跑实测 4→6）。

---

## 四 本卡未证明什么（≥4）

1. **未证明 `bug_log` 的同型缺陷已修**。`backend/app/core/bug_tracker.py:89` 的 `def __init__(self, log_path: str = "data/bug_log.jsonl")`
   + `:257` 模块级单例 `bug_tracker = BugTracker()` 是与本卡**完全同型**的 cwd 相对缺陷，且 `traces.py` 的 `LOG_FILES["bug_log"]`
   读的仍是绝对锚。该文件不在任何车道 territory（manifest 全文零命中），本卡**只在注释里如实标注 + 登记**，未修。
2. **未证明容器 / 打包布局下三层 `.parent` 锚仍指向可写目录**。锚是在本机 worktree 布局（`backend/app/core/` → 三层 `.parent` → `backend`）下实测的；
   生产镜像 `python:3.11-slim` 的 `/app` 布局未跑。同理未证明 `failure_counters` 的 `Path(__file__).parent…`（无 `resolve()`）
   与 `traces.py` 的 `Path(__file__).resolve().parents[4]`（有 `resolve()`）在存在符号链接的部署下不会分叉 —— 本卡两处都只在同一棵树上比对过值相等。
3. **未证明 `tests/unit` 地盘外的 4 个写者已止写**。它们每跑一次仍会往本树 `backend/data/` 追加（见 §三），本卡只登记 nodeid 与建议 patch 目标串。
4. **未证明本树既有 `backend/data/*.jsonl` 的内容正确性与去向**。本卡对它们只读（`wc -l` / `shasum`），不删不清，清理归 G4-6 / 主 session。
5. **未证明别处 cwd 下的历史残留已被回收**。缺陷期内从非 backend 目录启动的进程会把死信写到那个目录的 `data/` 下
   （`scripts/memory-health.sh:20` 至今仍同时数 `$WT/data/` 与 `$WT/backend/data/` 两个位置，正是这一点的运维侧痕迹）。本卡只改**今后**的落点。
6. **未证明 `backend/scripts/census_dead_letter_episodes.py:462` 的 `--dlq` 默认相对串在其调用处 cwd 下的实际落点**。该脚本不在本卡地盘，未改。
7. **未证明 `get_episode_worker()` 的 8 处调用在运行时行为一致** —— 本卡的证据是「这 8 处源码零改动」+「默认值解析到同一个绝对锚」，
   属静态论证；未起真实进程从不同 cwd 各跑一遍端到端。

---

## 五 台账待登记条目（≥4）

1. **修复 sha** `bfeefadd`；结构门 `2→0`（episode_worker 相对串）、`2→0`（traces `DATA_DIR` 拼接）、AST `2→0`；
   行为门 5 条 nodeid（`tests/unit/test_dead_letter_path_anchor.py::{test_default_anchor_is_absolute_under_backend,
   test_default_store_writes_to_anchor_not_cwd, test_worker_default_resolves_to_same_anchor,
   test_traces_reads_exactly_where_worker_writes, test_no_cwd_relative_default_left_in_episode_worker}`）；
   写脏门 snap 存档 `data-before-unit-close-20260918T171328.txt` / `data-after-unit-close-20260918T171328.txt`。
2. **`bug_tracker.py:89` 的 `bug_log` cwd 相对 = 同型缺陷，无车道 territory，归属待主 session 裁**
   （相邻面是 P8 的 `exception_handlers.py`，或顺延第十六批）。消费点：`main.py:57/:789`、`exception_handlers.py:27/:243`、`debug.py:20`（+ `:92/:144/:219` 三处只读）。
3. **tests/unit 写者定位结果**（见 §三表）：地盘内已打桩 2 条；地盘外 4 个文件只登记 —— `test_canvas_edge_bulk_sync.py`(+1)、
   `test_canvas_edge_sync.py`(+1)、`test_agent_memory_trigger.py`(+1)、`test_story_30_22_agent_trigger_deep.py`(+2)。
   另登记：卡文 §〇 给的 10 文件候选集**漏了前两个**（它们经 `service._sync_edge_to_neo4j` 间接触发，不直接 grep 命中 `write_dead_letter`）。
4. **本卡跑判据期间真追加到本树 gitignored jsonl 的行数**（未删，如实登记）：本卡开工时本树 `backend/data/` 四个 jsonl **全部不存在**；跑完全部判据后
`failed_edge_syncs.jsonl` = **12 行**、`failed_writes.jsonl` = **9 行**（合计 **21 行**），
`dead_letter_episodes.jsonl` 与 `bug_log.jsonl` 仍 **不存在**。
其中负控③ 刻意追加 **2 行**（`10 → 12`）。全部为 gitignored 本树数据，**未删未清**（清理归 G4-6 / 主 session）。
按来源拆：开工目录级 `+4/+3`、定向 tfo 改前 `+2`、写者定位逐文件跑 `+5`、收工目录级 `+2/+3`、负控③ `+2`。
5. **`census_dead_letter_episodes.py:462`（CLI `--dlq` 默认相对串）与 `scripts/memory-health.sh:20`（双位置计数）两处收敛移交**。
6. **`test_episode_worker_coverage_epw.py:46-47` 的 docstring 已过时**：它写「默认值都是**相对路径** `"data/dead_letter_episodes.jsonl"`」，
   本卡改后默认值是 `None` + 运行时锚。该文件不在 (l) 白名单，**未改**，登记。其隔离纪律本身仍然正确且仍应遵守。
7. **Codex 各轮**：round-1 存档 `_bmad-output/审查/codex-review-CARD-DEADLETTER-PATH-ANCHOR.md`（3585 B）；
模型 `gpt-6-astra` / `ultra` / `codex-cli 0.153.3`；绑定 SHA `bfeefadd`（= 最终 HEAD，diff 逐字空）；
计数 **B=0 / H=0 / M=2 / L=6**，全部登记不改，逐条裁定见验收单 §二 (n) 表。
其中 **LOW #3 的前提不成立**（负控② 实际注入的是保持 `Path` 类型的形态，失败正文为 `AssertionError` 而非 `AttributeError`，存档可证）；
**LOW #5 成立且为真实文档不实**，建议回写卡文 (e)③ 的 docstring 措辞；
**MEDIUM #1 / #2 建议合成一张后续卡**（容器布局下的锚断言 + 工厂调用点实参的 AST 门）。
8. **卡文 5 条事实漂移**（见 §一）建议回写卡文 / 手册。

---

## 六 DoD-3 段 4-B：用户侧（零技术词）

后端有时会把一条学习记录存不进知识库，这种「没存成」的记录会被单独记到一个文件里，追踪页面就是靠读那个文件来告诉我哪些记录掉队了。

以前这份记录放在哪，取决于**程序是从哪个文件夹启动的** —— 换个启动方式，它就落到另一个地方，而追踪页面永远只看固定的那一处，所以那些掉队的记录等于凭空消失了，页面上什么都不显示，看起来像「一切正常」。

现在它固定放在同一个位置，追踪页面读的就是它写的那一份。我感觉这些记录终于不会因为启动方式不同而失踪了 —— 更重要的是，如果以后页面上显示「0 条掉队」，我可以相信那是真的 0 条，而不是「又找错地方了」。

顺带修掉了一件小事：跑测试的时候，有两条用例会把假的失败记录真的写进这份线上文件里，越跑越多。现在它们写到临时目录去了，不再污染真实数据。

**felt-sense**：之前那种「报表说没问题，但我不确定它是真的没问题还是根本没看对地方」的不踏实感消失了。
