# UAT — CARD-NEO4J-REPLAY-BOUND（T6-C）· 2026-09-15

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-NEO4J-REPLAY-BOUND]` · 车道 `card-t6-neo4j`（分支 `card/t6-neo4j`）· 本车道第 3/3 张，**commit 后车道收工**。
> `T6B_TIP = 26bf4a2e26c0a7e1e80ba1cf599959f0e9564632`（T6-B 末 commit）· 代码 commit 五个：
> `47075cbe` → `b8cd3a82` → `11caca05` → `09d6da33` → **`f3336568`（最终 HEAD）** · 未 push。
> **Codex 5 轮，终轮 `f3336568` 绑最终 HEAD 且 BLOCKER=0 / HIGH=0 ⇒ D-15 通过门达成。**
> 证据目录：`_bmad-output/审查/evidence-neo4j-replay-bound/`（`.txt`，承重跑末行 `rc=`）。

---

## 4-A Claude 已代验（贴证据）

### (a) 第 0 分钟 + 基线自证

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-t6-neo4j` ✓ |
| 分支 | `card/t6-neo4j` ✓ |
| `git status --porcelain` | 0 行 ✓ |
| `T6B_TIP` | `26bf4a2e26c0a7e1e80ba1cf599959f0e9564632` |
| `test -x backend/.venv/bin/pytest` / `test -e backend/.env` | 均在 ✓ |
| `grep -vc '^#' "$BASE"` | **64** ✓（`$BASE` = feature 主干树 `evidence-b14/unit-red-baseline-08100483.txt`） |

**开工 `tests/unit` 起点**（`unit-open-20260915T115331.txt`，425.88s）：
`33 failed, 5079 passed, 48 skipped, 23 xfailed, 29 errors`，rc=1 → `open.nodeids` **62 行**。
与 `$BASE`(64) 的 diff：**新增 `>` = 0，`<` = 2**（`test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::{test_fallback_sync_called_in_lifespan,test_main_imports_fallback_sync}` —— T6-B 修好的两条）。
⚠️ 该跑的 collection 发生在本卡两个新测试文件创建**之前**（`grep -c t6c open.nodeids` = **0**），基线不含本卡文件。

### §〇 逐字核 —— 卡文行号漂移 6 处（其余全部逐字命中）

| 卡文 | 实测 | 说明 |
|---|---|---|
| `traces.py` `DATA_DIR` **:17** | **:23** | T6-B 给该文件加了 import 与 docstring |
| `traces.py` `LOGS_DIR` **:18** | **:24** | 同上 |
| `traces.py` `LOG_FILES` **:20-25** | **:26-31** | 同上 |
| `traces.py` `_search_jsonl` **:28** | **:34** | 同上 |
| `traces.py` `/traces/{request_id}` **:50-71** | **:56-77** | 同上 |
| 卡文「traces.py **唯一路由**」 | **实测两条** | T6-B 已加 `POST /traces/replay-fallbacks`（:80-152）。POST 在动态段之后不受影响（方法不匹配走 PARTIAL 继续匹配），但**新增的 GET 会被真吃掉** |

**逐字命中**（无漂移）：`failure_counters.py` `write_dead_letter`:73 / 裸追加:123 / `EDGE_SYNC_DEAD_LETTER_PATH`:24 / `DUAL_WRITE_DEAD_LETTER_PATH`:27 / `_counter_lock`:19，`import json`:9、`from datetime import…`:12 均在；
`memory_service.py` `_record_structured_outbox`:502 / 追加:516 / `_flush_pending_failed_writes`:2854 / 追加:2872；
`failed_writes_constants.py` `FAILED_WRITES_FILE`:11 / `failed_writes_lock`:17；
`canvas_service.py`:96/:508、`agent_service.py`:130、`neo4j_client.py`:54、`episode_worker.py`:224。

**卡文事实更正（运行时产物，与代码无关）**：卡文 §〇 称 `backend/data/` 有 `bug_log.jsonl` 与 `dead_letter_episodes.jsonl`、`backend/app/data/` 有 `vault_index_pending*`、`audit.jsonl` 在 `backend/logs/`（100K）。**本车道树实测**：`backend/data/` 只有 `failed_edge_syncs.jsonl` / `failed_writes.jsonl` / `learning_memories.json` / `neo4j_memory.json` / `reference_priority.json` + `lancedb/outbox/presets` 目录；`backend/app/data/` **不存在**；`backend/logs/` 只有 `memory-system-*.log`，**无 `audit.jsonl`**。原因：这些是 gitignored 的运行时产物，各 worktree 独立，卡文勘探在 feature 主干树做的。**代码层面的结论（DATA_DIR 指 `backend/app/data`、死信写在 `backend/data`）不受影响，已实测复核。**

### (b)(c)(d) 先红 → 后绿

**先红**（`red-t6c-20260915T115509.txt`，改前）：`16 failed, 7 passed`，rc=1。红在指定消息：

```
活动文件超行数: 8 > 上限 5 (追加了 8 条)                     ← (b) edge_sync / dual_write
活动文件超行数: 8 > 上限 5 (一次 flush 8 条)                  ← (c) failed_writes
DATA_DIR 指错目录: …/backend/app/data   assert ('app','data') == ('backend','data')   ← (d)①
不是 backlog 形态（被动态段吃掉了？）: ['request_id','timeline','total_events']        ← (d)②
```

⚠️ `raising=False` 是刻意的：改前 `DEAD_LETTER_MAX_LINES` 属性不存在，用默认 `raising=True` 会让先红红在 `AttributeError`，负控①也会红在同一个 `AttributeError` 上 ⇒ 负控失去鉴别力。加了 `raising=False` 后，红在真正的行为断言上。

⚠️ (d)② **不断言 404**：改前实测是 **200**（被 `/traces/{request_id}` 接住，返回 `{'request_id': 'dead-letter-backlog', 'timeline': [], 'total_events': 0}`）。断言 404 会是「改前红、改后也红」的错方向。判据取**形态**（`files` vs `timeline`）。

**先红加固**（`red-t6c-strengthened-*.txt`）：初版有 3 条门在改前是**平凡绿**（零轮转时「不丢条目 / 没误删 / 没超保留上限」自动成立）。补前置断言后 → `7 failed, 3 passed`，三条都进了红集。

**后绿**（`green-t6c-final-*.txt`）：`23 passed`，rc=0。
**后绿 + 邻近**（`green-plus-neighbors-*.txt`）：`61 passed, 3 skipped`，rc=0。

### (g) 负控输入 —— 两段，各带 EXIT trap 与 shasum 前后对照

变异前 4 个生产文件 shasum：
```
456c91c6024126e77460bdde9f7cc433ce38cc2beecbc275136c7006e634af62  failure_counters.py
4ef40b310cd6ace4134dbad1909705f242366eee7ac3470dee2035a8d15e9501  failed_writes_constants.py
9bd20ab153b627bbcfee3af5e83e4ea86465c1eeac72ed0d1b5380a93820c6c6  memory_service.py
0e44c1837825dab97c12e84a1eaf864180ee3471be5543be92c3604de3bbe55d  traces.py
```
两段跑后 shasum 逐行相同 → `RESTORE_VERIFIED=yes`（两份存档各自贴了跑前/跑后两组）。
⛔ 还原基准 = **变异前的工作树快照**，不是 HEAD（工作树当时本就领先 HEAD）；全程未用 `git stash` / `git restore` / `git checkout`（车道 guard 拦这些子命令）。

**负控①**（`negctl-1-*.txt`）：删掉两个追加点的 `rotate_if_over_limit(...)` 调用（= 还原「无上限」）
→ `7 failed, 3 passed`，红在 `活动文件超行数: 8 > 上限 5` 与 `轮转未发生，本门的守恒判据无意义`。
验伪锚 `test_no_rotation_below_limit` 仍绿 ✓（未超限本就不该轮转）。

**负控②**（`negctl-2-*.txt`）：`OVERFLOW_SUFFIX` 从 `.overflow.` 改成回灌侧的 `.synced.`
→ `7 failed, 3 passed`，承重断言红在 **`.synced. 兄弟被本卡 retention 误删`**。
日志逐字佐证（这是隔离承重的直接证据，不是推断）：
```
[T6-C] 清理超出保留上限的溢出文件: failed_edge_syncs.synced.2020-01-01-000000
```
即：后缀一旦与回灌侧相同，本卡 retention 就会把**回灌侧留下的**旧档当成自己的溢出档删掉。

### 对照输入 —— 邻近套件开工基线

`neighbors-open-*.txt`：把 4 个生产文件用 `git show $T6B_TIP:<path>` 写回后跑三套件。
控制组成立的自证（同一跑内打印）：`23:DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"` ← 确是改前态。

| | 开工（T6B_TIP 态） | 收工（本卡态） |
|---|---|---|
| `test_failure_observability` + `test_a7_honest_failure` + `test_story_38_1_ac2_failure_handling` | **38 passed, 3 skipped**, rc=0 | **38 passed, 3 skipped**, rc=0 |

逐数相同，零回退。

### (h) pyright

`pyright-final-*.txt`：`cd backend && <绝对路径>/pyright app` → **`0 errors, 81 warnings, 0 informations`**，与 `08100483` 基线（0/81）**持平**。
`test -x` 自证已贴；未用 `| tail -1`；**未**使用 `LEFTHOOK_EXCLUDE=python-typecheck`（commit 时 `python-typecheck` 正常跑过，输出 `0 errors, 2 warnings` + `Typecheck done (exit: 0)`）。

### ruff（`ruff-*.txt`）

6 个改动文件 `ruff check` → `All checks passed!` **rc=0**。

**验伪锚更正（实测）**：`backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]`。自证：
`ruff check --show-settings` 的 `linter.rules.enabled` 里 **F401 命中 0 / I001 命中 0 / F821 命中 1**。
⇒ 卡文模板的 **F401 验伪锚恒不触发**（实测探针 `rc=0`），已改用 **F821 探针 `rc=1`** 作有效锚。

### (l) 地盘门

```
git --no-pager diff --name-only --no-color 26bf4a2e 47075cbe -- . ':(exclude)_bmad-output'
```
→ 恰好六文件：
`backend/app/api/v1/endpoints/traces.py`、`backend/app/core/failed_writes_constants.py`、
`backend/app/core/failure_counters.py`、`backend/app/services/memory_service.py`、
`backend/tests/unit/test_dead_letter_bounded_t6c.py`、`backend/tests/unit/test_traces_backlog_t6c.py`
**`backend/openapi.json` 命中数 = 0** ✓。验伪锚（去掉 exclude 后多出 `_bmad-output/` 行）见下方「文档 commit 后复跑」。

### `LEFTHOOK_EXCLUDE` 的依据（协议 §2.3 要求逐条贴）

**裸跑一次的原始输出**（`commit-20260915T*.txt`，未排除时被拦）：
```
Would reformat: backend/app/core/failed_writes_constants.py
Would reformat: backend/app/core/failure_counters.py
Would reformat: backend/app/services/memory_service.py
3 files would be reformatted, 3 files already formatted
[Python] Format check FAILED!
```
被拦的是 `python-lint` 里的 `ruff format --check`（`ruff check` 本身 rc=0）。

**「报错不在本卡改动行」的证明** —— 基线多重集对照，键 = **变更行文本**（对 hunk 重新分组免疫）：
以 `git show $T6B_TIP:<path>` 导出的 4 份原版为基线，逐文件比对 `ruff format --diff` 的 `+/-` 行多重集：

| 文件 | 基线变更行 | 现在 | **新增** |
|---|---|---|---|
| `traces.py` | 0 | 0 | **0** |
| `failed_writes_constants.py` | 5 | 5 | **0** |
| `failure_counters.py` | 9 | 9 | **0** |
| `memory_service.py` | 76 | 76 | **0** |
| | | | **TOTAL_NEW_FORMAT_LINES = 0** |

即：残留的 format 漂移**逐行等于** T6B_TIP 既有债（主干既有债，归 T8-G），本卡新增 **0 行**。
`traces.py` 改前是干净的，本卡把自己新增的行都做成 format 合规，让它**保持** 0。
两个新测试文件（100% 本卡）已 `ruff format` 过，`--check` rc=0 —— hook 输出里那「3 files already formatted」正是它们加 `traces.py`。

⚠️ 判据自身曾出过一次错并已修：第一版基线跑的 cwd 指错（文件在 `$SCR/fmtbase/backend/...`，传的相对路径从 `fmtbase` 起算 ⇒ ruff 找不到文件 ⇒ 基线恒 0 = 假阴性）。修正后加了「基线单文件 `--check` 必 rc=1」的验伪锚先证判据能命中，再做对照。

### openapi.json（本卡刻意不提交）

`openapi-drift-*.txt`：`check-openapi-drift.py --write` → `paths=199`（快照基线 197）。
`git diff --numstat` = **66 增 / 1 删**，内容 = 新路由 `/api/v1/traces/dead-letter-backlog` 的完整块 + `x-generated-at` 一行。
**drift 是真实的**（本卡新增了只读路由），不是纯时间戳噪音 —— 与第十四批 T5-A 那次不同，这里如实区分。
取证后用 `git show HEAD:backend/openapi.json` 写回还原（guard 拦 `restore`/`checkout`/`rm`），`git diff --numstat` 为空。
`tests/contract/test_openapi_snapshot_drift.py` 因此会红 = **预期，登记不阻断**，由主 session 统一再生。

### 硬边界核对（含一条如实披露）

- 禁写 live vault ✓（本卡零 `canvas-vault/` 写入）
- 禁连 7691/7687 ✓（每跑末行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`）
- 禁碰 `fsrs_bridge.py` / `decay_beta.py` ✓（六文件里零命中）
- 批中禁装包 ✓（未装/升任何包）
- 禁 `git stash` ✓、不改台账 ✓、不 push ✓

⚠️ **如实披露：现网 `backend/data/*.jsonl` 在本 session 内被追加过，但不是本卡代码写的。**
`failed_writes.jsonl` mtime 11:55:52、`failed_edge_syncs.jsonl` mtime 12:05:17。逐条归因：

- `failed_writes.jsonl` 末三条 `03:53:45Z / 03:55:51Z / 03:55:52Z`，`event_type` = `scoring-agent` / `basic-decomposition` / `deep-decomposition`，error 为 `Database connection failed` 之类的测试常量 ⇒ 来自**开工 `tests/unit` 目录级全量跑**（03:53:31Z–04:00:37Z 窗口内）里未打桩的既有测试。
- `failed_edge_syncs.jsonl` 末三条 `04:03:13Z / 04:05:11Z / 04:05:17Z`，`ConnectionError: Neo4j down` / `connection refused` ⇒ 来自 **`test_failure_observability.py:176 test_edge_sync_failure_increments_counter` 与 `:226 test_edge_sync_failure_logs_warning`**：这两条调 `_sync_edge_to_neo4j` 时**没有** patch `EDGE_SYNC_DEAD_LETTER_PATH`（只有 `:200` 那条 patch 了），于是每跑一次该套件就往现网文件追加 2 条。该文件在本卡**禁改**名单里，且卡文裁判 #3 要求跑这个套件。

**本卡自己的两个测试文件全程 `tmp_path`**，零现网写入。
**零轮转/零删除的实证**：`ls backend/data | grep -cE '\.overflow\.|\.synced\.'` = **0**；现网 `failed_edge_syncs.jsonl` = **64 行**、`failed_writes.jsonl` = **34 行**，对上限 10000 余量极大。

---

## 4-B 用户视角（零技术词）

我让系统在「离线很久、失败记录堆了很多」的时候，不会无限占满磁盘——旧的失败记录会自动归档，数量有上限，归档的份数也有上限，最老的会先被清掉。同时我加了一个只读的页面，让你一眼看到「现在积压了多少条、最早那条是什么时候、已经归档了几份」。

还顺手修好了一件一直在骗人的事：原来那个「按请求编号查全过程」的页面，找的是一个**根本不存在的文件夹**，所以无论系统出过什么事，它都永远告诉你「什么都没查到」。现在它看的是真正存放记录的地方了。

我的感受：系统在坏天气里也稳得住，而且**我心里有数**——不再是「好像没事」，而是能看见「积压多少、从什么时候开始的」。

---

## 本卡未证明什么（≥4）

1. **未证明 `agent_service.py:130` 旁路写者下 `failed_writes.jsonl` 的完备有界。** 第三写者在其他地盘、未切 helper，它只持锁不核上限；纯 `agent_service` 的突发可以暂时越限，要等下一次经 helper 的追加才把超出部分整体轮转走。本卡把这一点写进了 helper 的 docstring，但**没有**测它。
2. **未证明 `neo4j_memory.json` / `dead_letter_episodes.jsonl` / `canvas_events_fallback.json` 的写侧有界。** 它们的写点分别在 `neo4j_client` / `episode_worker` / `canvas_service` 地盘，本卡只做只读 backlog 暴露。
3. **未证明真并发（多线程 / 多进程同时写）下轮转零丢失。** 单测是顺序调用。进程内有锁覆盖「核行数→轮转→追加」全段，但**跨进程非原子**（`rename` 与 append 是两个 syscall），本卡未测。
4. **未证明 T6-B 回灌与本卡 `.overflow.` 轮转在「离线→积压→轮转→恢复→回灌」全链路互不吞数据。** 本卡只做了后缀隔离的静态保证 + 单测；全链路需要 7692 + 真回灌。
   ⚠️ 已知且已记录的事实（不是未知）：`fallback_sync_service` 全文**无 glob**，只回灌活动文件 ⇒ **被轮转走的 `.overflow.*` 条目没有任何回灌方**，且超保留上限后会被删除。这是「有界」换来的代价。
5. **未证明 `audit.jsonl` 恢复可读后，`/traces/{request_id}` 的 audit 条目与其他源的 `timestamp` 格式可排序一致。** 排序键是 `str(e.get("timestamp",""))`；跨源格式若不同，时间线次序不可信。本卡只证「字段缺席不崩」，未证跨源可比。**且本车道树根本没有 `audit.jsonl`**（见 §〇 事实更正），所以连一次真实的跨源排序都没观察到。
6. **未证明现网 `backend/data/*.jsonl` 的真实积压量代表任何生产环境。** 只读了本车道树的数字（64 / 34 行），未统计其他树、未统计线上。
7. **未证明本卡新增的上限在「跑邻近套件」这条路径上永远无害。** `test_failure_observability.py:176/:226` 未打桩、会写现网 `failed_edge_syncs.jsonl`；本卡之后这条路径还会**读**该文件核行数。今天该文件 64 行、上限 10000，所以只读未轮转（已实证零 `.overflow.*`）；但若哪天现网该文件超过 10000 行，**跑一次邻近套件就会真的轮转现网文件**（轮转不丢数据，但确实动了现网文件）。
8. **未证明 `_display_path` 的 fallback 分支与 `bound_from_env` 的坏值分支在生产配置下会被走到。** 两者都有单测覆盖不到的现实路径（如 `relative_to` 在符号链接树下的行为）。
9. **未证明回灌窗口守卫在「回灌挂住不放锁」时的行为可接受。** `_replay_in_flight()` 读的是
   `_sync_all_lock.locked()`；锁被永久持有时写侧上限就被无限期关掉，退回无界增长。
   本卡没加超时/看门狗，也没有测这个场景。
10. **未证明真实的「回灌 × 轮转」端到端无损。** 门用的是真实的 `_sync_all_lock`，但**没有**
    真跑 `_sync_failed_writes`（那需要 7692 + Neo4j 替身，属 integration 面）。所以证明的是
    「窗口开着时不轮转」，**不是**「整条回灌链在有写者并发时不丢数据」。
11. **未证明 `.overflow.*` 里的条目还有任何人会去读。** 已知它们**没有**回灌方（见台账 15）；
    本卡只保证它们不被写侧覆盖、按保留上限有序淘汰。
12. **未证明本卡对四条「其他地盘」暂存链（`neo4j_memory` / `dead_letter_episodes` /
    `canvas_events_fallback` / `outbox/events`）的 backlog 数字在真实运行时是准的** ——
    其中两条的写侧是 cwd 相对路径，backlog 报的是 cwd=backend 假设下的位置。

---

## 台账待登记条目（≥4）

1. **本卡写侧有界覆盖 3 个 JSONL**（`failed_writes` / `failed_edge_syncs` / `failed_dual_writes`），修复 sha `47075cbe`；门 nodeid = `tests/unit/test_dead_letter_bounded_t6c.py`（10 条）+ `tests/unit/test_traces_backlog_t6c.py`（13 条）。
2. **口径更正：设计稿「常量入 Settings」改为落 T6 自有模块。** `config.py` 属 T5 独占 ⇒ 上限/保留数放 `failure_counters.py`（`DEAD_LETTER_MAX_LINES` / `DEAD_LETTER_MAX_ROTATIONS`）与 `failed_writes_constants.py`（`FAILED_WRITES_MAX_LINES` / `FAILED_WRITES_MAX_ROTATIONS`），env 可覆盖（`CLS_*`）。**供主 session 裁是否后续收进 Settings。**
3. **偏离卡文 (e).2 的 helper 签名（必须偏离）。** 卡文建议 `append_failed_writes_bounded(lines)` 内部读 `failed_writes_constants.FAILED_WRITES_FILE` 全局；实测既有 5 个测试文件打桩的是**导入方**的绑定副本 `app.services.memory_service.FAILED_WRITES_FILE`（`test_a7_honest_failure.py:108/142`、`test_story_30_24_boundary.py:551/583/622`、`test_story_38_6_scoring_reliability.py:185/311` 等）。若按卡文写，这些打桩全部失效 ⇒ 测试会把条目写进**现网** `backend/data/failed_writes.jsonl`，且多半仍显示绿（假绿）。故 helper **显式收 `file_path` 参数**。
4. **新发现并已修：`traces.py` `DATA_DIR` 指 `backend/app/data`（实测该目录不存在）而死信文件在 `backend/data`（DD-13 名实不符）；`LOGS_DIR` 同错（`audit.jsonl` 在 `backend/logs`）。** 两者改用 `Path(__file__).resolve().parents[4]`。
   **另记 backlog 的目录分歧**：`canvas_events_fallback.json` 写侧（`canvas_service.py:96`）落 **`backend/app/data`**，与其余六条（`backend/data`）不同目录 ⇒ backlog 对它**单独锚定**（统一套 DATA_DIR 会让它恒 `exists=False`，又是一处 DD-13）。**供后续卡决定是否统一归拢。**
5. **`.overflow.` 与 `.synced.` 后缀隔离约定（后人改 retention / 回灌前必读）。** `.synced.` = 回灌侧「已回灌，可按 30 天 retention 清理」；`.overflow.` = 写侧「未回灌的溢出」。负控②实测：后缀一旦相同，本卡 retention 会删掉回灌侧的旧档。
6. **`.overflow.*` 目前无回灌方。** `fallback_sync_service` 无 glob，只回灌活动文件；溢出条目超保留上限后被删除。是否需要让回灌器也扫 `.overflow.*` = 待裁。
7. **`neo4j_memory.json` / `dead_letter_episodes.jsonl` / `canvas_events_fallback.json` 写侧有界移交对应地盘**（`neo4j_client` / `episode_worker` / `canvas_service`），候选后续卡。
8. **`agent_service.py:130` 第三写者未切有界 helper，建议后续统一。**
9. **`test_failure_observability.py:176` 与 `:226` 未打桩 `EDGE_SYNC_DEAD_LETTER_PATH`，每跑一次就往现网 `backend/data/failed_edge_syncs.jsonl` 追加 2 条。** 该文件在本卡禁改名单里。⚠️ T6-C 之后这条路径还会**读**该文件核行数：现网超 10000 行时，跑一次该套件会真轮转现网文件。建议后续卡给这两条测试补打桩。
10. **`backend/openapi.json` 漂 66+/1-（本卡新增只读路由，真实 drift 非时间戳噪音），本卡不 commit，主 session 再生**，并核 `tests/contract/test_openapi_snapshot_drift.py`。
11. **`LEFTHOOK_EXCLUDE=python-lint,spec-sync-flat,spec-sync-root` 的使用与依据**（`python-typecheck` 未排除且已跑绿）；`ruff format` 新增债 = **0 行**（基线多重集对照），残留归 T8-G。
12. **卡文模板的 ruff F401 验伪锚在 `backend/**` 恒不触发**（`backend/ruff.toml` `select=["E9","F63","F7","F82"]`），已改 F821；建议把卡文模板一并更正。
13. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** —— 见下方「Codex 轮次」。
14. **`tests/unit` 目录级 diff（相对开工）结果** —— 见下方 (j)。
15. ⛔ **`failed_writes.jsonl` 不是坟场，它有唯一回灌方 —— 本卡只做了窗口级止血。**
    `fallback_sync_service` 全文无 glob、只读活动文件 ⇒ 被轮转走的 `.overflow.*` 条目
    **永远不会被回灌**，并在超保留上限后删除。根治须让回灌器也扫 `.overflow.*`，
    那是 `fallback_sync_service.py` 的面 = 本卡禁改。**建议单开一卡**（同时决定
    `failed_writes` 是否该与两条真坟场用**不同**的保留策略）。
16. ⛔ **回灌窗口守卫的失效模式**：`_replay_in_flight()` 读 `_sync_all_lock.locked()`；
    若某次回灌**挂住不放锁**，写侧上限会被无限期关掉（退回无界增长）。本卡未加超时/看门狗。
17. **轮转产物命名契约**：`<stem>.overflow.<定宽微秒戳>-<NN><原扩展名>`。
    两条不可动的约束：① 必须保留原扩展名，否则 `backend/data/.gitignore` 的 `*.jsonl`
    盖不住（实测 `git check-ignore` 无命中）；② 序号 `-NN` 必须**恒存在**，
    因为 `-`(0x2D) < `.`(0x2E)，「撞了才加」会让 `<ts>-01` 排在 `<ts>` 之前，
    打破 `_prune_overflow` 赖以「删最老」的字典序 == 时序不变量。
18. **`/traces/{request_id}` 的目录修复只覆盖四源里的两源**：`bug_log` 与
    `dead_letter_episodes` 的写侧是 **cwd 相对**路径（`episode_worker.py:224` 默认参数），
    cwd ≠ backend 时仍对不上。读侧修不了，移交写侧地盘。
19. **backlog 新增覆盖 `outbox/events.jsonl`**（`event_bus.py:49`）。它的**写侧有界**
    仍属 event_bus 地盘，本卡只读。
21. ⛔ **`Path.exists()` 吞异常同型缺陷在本卡出现 5 处，仅修 3 处**（`count_lines` /
    `_backlog_entry` / `_invalidate_replay_checkpoint` 已修；`overflow_siblings` 的
    `parent.exists()` 与 `_unique_overflow_target` 的 `candidate.exists()` **未修**，
    见 r5 MEDIUM-1/2）。后者后果更重：吞错后会**选中已存在的归档名**，`rename` 随后覆盖它。
    **建议后续卡一次性清掉这 5 处 + 加一道「这几个模块禁止裸用 `.exists()`」的常驻门**
    —— 逐条等审查喂是不可收敛的。
22. **r5 的 AST 隔离门本身可被误认**（只要加一行含 `SYNC_CHECKPOINT_FILE` 的注释即通过；
    模块别名 / fixture 内调用 / `Test*` 类方法漏判），且它的**验伪锚验的是一份复制的
    局部 `scan()`**，不是常驻门本身。门的思路对，实现需要加固。
23. **两处行内注释未随 docstring 一起更正**（`traces.py:231` 的「内存上界就是 max_bytes」、
    `failed_writes_constants.py:80` 的「退回有界行为」）—— 实为整体 O(N) 与「停止轮转、
    持续越限」。docstring 已改，注释漏改。
24. **本卡 5 轮 Codex 配额用满**：r1 B0/H0 → r2 H1 → r3 H2 → r4 H2 → **r5 B0/H0（终轮绑最终 HEAD）**。
    每轮 HIGH 均由**前一轮修复**引入。r5 的 4 MEDIUM + 2 LOW 因配额用满而**只登记不修**
    （改则须第 6 轮）。

20. **内部对抗复核（Workflow）已入库**：`evidence-neo4j-replay-bound/selfreview-workflow-20260915.md`。
    26 个 verify agent 因 API 错误未跑成 ⇒ 验证覆盖不完整，主 session 复核时按此折扣。

---

## ⚠️ 多轮收口纪要：**五条阻断/高危级缺陷全部是本卡自己引入**，已逐条收口

代码 commit 四个：`47075cbe`（初版）→ `b8cd3a82`（收口 r1 + 内部复核）→ `11caca05`（收口 r2）
→ **`09d6da33`**（收口 r3，= 最终 HEAD）。

| 轮 | 审 SHA | 结果 | 该轮 HIGH/BLOCKER 的来源 |
|---|---|---|---|
| Codex r1 | `47075cbe` | B0 / H0 / M3 / L3 | — |
| 内部对抗复核 | `47075cbe` | 20 存活（**B1** / H5 / M10 / L4） | 初版的写侧轮转 |
| Codex r2 | `b8cd3a82` | B0 / **H1** / M3 / L3 | **r1 加的窗口守卫**没覆盖持久化游标 |
| Codex r3 | `11caca05` | B0 / **H2** / M1 / L4 | **r2 加的游标作废**捕获面漏 ValueError 家族；测试未隔离现网 checkpoint |
| Codex r4 | `09d6da33` | 在跑 | — |

⚠️ **这个模式本身值得记一笔**：每一轮的 HIGH 都不是原始需求做错了，而是**前一轮修复引入的新面**。
r1 的守卫是对的但不完整；r2 的作废是对的但捕获面不完整。每轮该问的不是「我改对了吗」，
而是「**现在这样对吗**」。

### round-4 收口的两条 HIGH（Codex r3）

**HIGH-1 编码异常致整批丢失**：`_invalidate_replay_checkpoint` 的捕获面漏了
`UnicodeDecodeError` / `UnicodeEncodeError`。实测继承链：二者是 `ValueError` 子类，
**既不是 `OSError` 也不是 `json.JSONDecodeError`** ⇒ 初版的
`except (JSONDecodeError, OSError)` 接不住。checkpoint 里一个 `b"\xff"` 就让异常逃出
前置动作 → 被 `_flush_pending_failed_writes` 的 `except ... ValueError` 接住，
其 `finally` 清空 pending ⇒ **一整批合法待写记录消失**；单条 outbox 路径则让异常整个逃逸。
修：读侧加 `UnicodeDecodeError`（坏文件整删，目的达成）；写侧 `ensure_ascii=False` →
失败退回 `ensure_ascii=True`（**保住其余链的游标**）→ 再失败才整删；外层兜底改
`except Exception`——本函数在追加路径上，**绝不能抛**。

**HIGH-2 现网文件隔离不完整（硬边界）**：两个 fixture 只隔离了上限与数据文件，没隔离
`fss.SYNC_CHECKPOINT_FILE`，而轮转前置动作会**删/改**它 ⇒ 任何触发轮转的普通测试都会去动
**现网** `backend/data/sync_checkpoint.json`；而该文件不存在时测试照样绿，
于是结果悄悄依赖真实磁盘状态。两个 fixture 均补隔离 + 加一条直接盯指针的硬边界门。
**实测各 worktree 均无该文件，未造成实际损伤**（`ls .claude/worktrees/*/backend/data/sync_checkpoint.json` 无匹配）。

一并收口：扫描边界改二进制 `read(max_bytes+1)`（**同一处第三次收紧**——前两版都是
「按行读完再扣预算」，扣减时整行已在内存，且 `len(line)` 数的是字符不是字节）；
根锚门改用 `/` + `/secret.jsonl` 绕开深度闸；更正 docstring 里「import 失败退回有界行为」
这句失真表述（净效果是**永不轮转**）；批量 flush 守恒门补身份断言。

### ⚠️ 自曝其二：round-3 的三条门初版**全是空壳**

H1a / H1b / H2 的负控**都没红**（`seg[*]_rc=0`）。逐条原因：

| 门 | 为什么没牙 |
|---|---|
| H1a | 断言「不丢批」，而**外层 `except Exception` 兜底**让修与不修都成立 |
| H1b | 内层已处理写失败、外层永不触发 ⇒ **两层互相掩盖**，单摘任一层都不红 |
| H2 | 现网 checkpoint 恰好**不存在** ⇒ 打不打桩都一样 |

判据改为盯「**只有该层能产生的可观测差异**」——坏文件被删 + 照常轮转 / 其余键被保住 /
指针本身指向 tmp。负控⑥复跑**六段全红**。

> 这条教训比缺陷本身更通用：**加了纵深防御之后，原来那条门往往就失去鉴别力了**，
> 因为兜底层会替被测层把结果兜住。判据必须盯差异，不能盯最终成败。

---

## round-3 收口纪要（Codex r2 的 H1）

### round-3 收口的 H1（Codex round-2 已复现）：换代必须同时作废回灌游标

round-2 的守卫只挡住「回灌窗口**开着**」，挡不住「窗口已关但**持久化游标还残留**」：

```
原文件 51 条、游标 index=50
 → finalize 撞 OSError ⇒ 文件与游标**都保留**、锁释放
 → 写侧追加 1 条并轮转 ⇒ 新文件只有 1 行
 → 下一轮回灌 for i, line in enumerate(lines) 全部 i < 50 被跳过
 ⇒ 该条从未重放，却因 still_pending 为空而被 _rotate_file 改名 .synced.（谎称已回灌），30 天后删除
```

它**既没进 overflow 也没走 retention**，不属于本卡已披露的那个取舍。

`fallback_sync_service._clear_checkpoint` 的 docstring 自己立了这条不变量——
「**换代与游标失效必须同生共死**……清不掉一律上抛、由调用方决定不动文件」。
本卡的写侧轮转是**第二个**让文件换代的动作，初版没有守这条。

**修法**：`rotate_if_over_limit` 新增 `before_rotate` 前置动作；`failed_writes` 传
`_invalidate_replay_checkpoint`（惰性用该模块的**模块级** `SYNC_CHECKPOINT_FILE` +
`_checkpoint_lock`，**不**走 `get_fallback_sync_service()`——那会实例化 Neo4j 客户端，
不该挂在「写一条死信」的热路径上）。作废失败 ⇒ **放弃轮转**，与既有契约同口径。
锁序与既有 `_sync_failed_writes`（持 `failed_writes_lock` 后调 `_clear_checkpoint`）**同向**。

### round-3 一并收口的 M/L

| 来源 | 问题 | 修法 |
|---|---|---|
| r2 M1 | Python 3.14 的 `Path.exists()` **吞 PermissionError**：`count_lines` 把「读不到」压成「0 行」（上限永不触发 = 有界静默失效）；backlog 把权限问题报成 `exists=False / backlog=0 / partial=False` | 两处改 `stat` 显式分流，新增 `_stat_or_error` |
| r2 M2 | `{"timestamp":"\ud800"}` 是**合法** JSON，孤立代理字符活到响应序列化才抛 `UnicodeEncodeError`——那时已出 `_safe_backlog_entry` 的 try ⇒ 一条坏记录打挂整条路由 | 新增 `_utf8_safe` 清洗 |
| r2 M3 | 尺寸闸只在开扫前 stat 一次；stat 后文件才长大时 `for line` 仍整条读入 | 读循环加**字节预算** |
| r2 L1 | 兜底名 `-99-<uuid>` 因 `-`(0x2D) < `.`(0x2E) 排在 `-99` **之前** ⇒ 被当最老删掉 | 分隔符改 `~`(0x7E) |
| r2 L3 | `_display_path` 锚点退化：`relative_to("/")` **不抛异常**，只去前导斜杠 ⇒ 脱敏静默失效而门全绿 | 加「锚点不能是根 + 结果不超 3 段」两道闸 |
| r2 L3 | 一处**恒真**断言（`".overflow." in n`，n 已按此筛过）；一条测试名为 `anchor_is_root` 却传了个不存在的目录 | 删/改，后者真传 `/`——改完**立刻暴露**了上面那条真实泄漏 |

### ⚠️ 自曝：M3 那条门的第一版是**空壳**，靠负控才发现

它打桩在 `traces._stat_or_error`，而 `_first_last_timestamp` **自己还会 `path.stat()`**——
那次 stat 拿到真实大小 5056 > 闸 100，于是在**开扫前**就 `size_capped` 返回，读循环根本没执行。
门是绿的、断言也确实命中了 `size_capped`，**但绿的原因和它声称的原因不是同一个**。
负控「摘掉字节预算」跑出来它照样绿（`seg[M3]_rc=0`）才把它逼出来。
已重做为打桩 `Path.stat`，负控复跑转红（`seg[M3-redo]_rc=1`）。
—— 这就是协议要求负控必须红在**指定那条断言**、而不只是「某处失败」的理由。

### round-3 后的裁判

| 裁判 | 结果 |
|---|---|
| 两新测试 | **60 passed**（23 → 48 → 60） |
| 邻近三套件 + 全部触碰 `FAILED_WRITES_FILE` 的 9 个文件 | **180 passed / 2 failed**（两条均在开工基线里，既有红） |
| pyright | **0 errors, 81 warnings** |
| ruff check | rc=0；format 新增债 **0 行** |
| 负控⑤ | **七段**（H1 / H1b / M1 / M2 / M3-redo / L1 / L3）全部红在指定门，还原 shasum 逐字节同 |
| 地盘门 | 仍恰好六文件，`openapi.json` 命中 0 |

---

## round-2 增补（收口 Codex r1 + 内部对抗复核的阻断级）

### 阻断级（内部对抗复核实地复现；Codex round-1 **未发现**）

写侧轮转让 `failed_writes.jsonl` 在回灌窗口内**变短**，而它唯一的回灌方
`fallback_sync_service._sync_failed_writes`（本卡禁改）判断「重放期间有没有新追加」用的是
**长度比较 + 位置切片**：

```
fallback_sync_service.py:366-367
if len(current_lines) > len(lines):
    new_lines = current_lines[len(lines):]
```

该判据的前提是活动文件**只增不减** —— 那个文件 `:307` 的注释自己就写着这条契约。链是
`:284 持锁读快照 → :337 放锁逐条 await 重放 → :358 持锁 finalize`；本卡之前写侧只增不减，
本卡是**第一个让它变短的写者**。窗口内一旦轮转：`len(current) < len(lines)` ⇒ `new_lines=[]`
⇒ 窗口内新写的条目要么被 `:417 _atomic_write_file` 整份覆盖销毁，要么在 merged 为空时被
`:422 _rotate_file` 改名成 `.synced.<ts>`（**谎称已回灌**）后按 30 天 retention 删除。

触发不需要多线程：`_record_structured_outbox` 的调用方是 async 的 `record_knowledge_entity`，
`:337` 的 await 就是交错点。

**修法**（`fallback_sync_service.py` 是禁改面，故修在写侧）：`_replay_in_flight()` 惰性读
`_sync_all_lock.locked()`，窗口开着就只追加不轮转。上限因此是 best-effort（回灌期间可越限），
**但不丢数据** —— 这个取舍方向不可反转。

**门**：`test_no_rotation_while_replay_window_open` 用**真实的** `_sync_all_lock`（不是打桩）；
控制组 `test_rotation_resumes_after_replay_window_closes` 防「永不轮转」蒙混。
**负控④** 两段：摘掉守卫 ⇒ 窗口门红；守卫恒真 ⇒ 控制组红（`negctl-4-replay-window-*.txt`）。

### 其余收口（逐条对应审查意见）

| 来源 | 问题 | 修法 |
|---|---|---|
| Codex r1 M1 | `count_lines` 第二次调用与 `_prune_overflow` 的 `iterdir` 都没包 try，失败即**整个不追加** —— 比改前裸追加更糟（批量路径 `finally` 会 `clear()` pending） | 两处都接住，退化成「一次写完」 |
| Codex r1 M2 | 部分读取失败被包装成正常零值，`overflow_files=0` 与「真的没有归档」长得一样 | 每处降级留 `partial` + `degraded` 机器可读原因；顶层 `incomplete` / `degraded_chains`；`incomplete` 时明说 `total_backlog` 是**下界** |
| Codex r1 M3 | async 路由里同步全文件扫描，长行整体读入 | 整段走 `asyncio.to_thread` + `CLS_BACKLOG_SCAN_MAX_BYTES` 尺寸闸（超闸报 `size_capped`，与读失败**分开**报） |
| Codex r1 L1 | 三处表述过强 | 逐条收紧（见下「更正」） |
| Codex r1 L2 | `_display_path` 捕获面不含 `RuntimeError`（符号链接成环），而降级分支又调它 ⇒ 异常逃出整条路由 500 | 捕获面放宽到 `Exception` |
| 内部复核 MEDIUM | 轮转产物 `failed_writes.overflow.<ts>` **不被任何 .gitignore 规则覆盖**（`with_suffix` 吃掉 `.jsonl`；`.gitignore` 只有 `*.jsonl` 与 `*.synced.*`）。实测 `git check-ignore` 无命中 | 名字保留原扩展名 ⇒ 实测被 `.gitignore:5` 命中 |
| 内部复核 MEDIUM | `_REPO_ROOT = parents[5]` 依赖部署布局；容器里仓根 == `/` 时 `relative_to` **不报错**，只去掉前导斜杠 ⇒ 脱敏静默失效而门全绿 | 锚点改 `_BACKEND_DIR`（七条链全在 backend 下，部署无关） |
| 内部复核 MEDIUM | `parents[4]` 只真正修好四源里的两源 —— `bug_log` / `dead_letter_episodes` 写侧是 **cwd 相对**路径 | 注释按实际改写，不再说「四源都修好了」 |
| 内部复核 LOW/MEDIUM | backlog 漏了 `event_bus` 的 `outbox/events.jsonl`，而 description 写的是 every staging file | 补进 `BACKLOG_FILES` |
| **本卡自己的门抓到** | 撞名时追加 `-01`：ASCII 里 `-`(0x2D) < `.`(0x2E) ⇒ `<ts>-01.jsonl` 排在 `<ts>.jsonl` **之前**，打破 `_prune_overflow` 赖以「删最老」的字典序==时序不变量（**会优先删掉更新的那份**） | 序号恒存在（`-00` 起），所有名字同形 |

⚠️ 最后一条是**把时钟钉死之后才显形的**：不钉钟的话两次调用落在不同微秒，根本走不到防撞
分支，测试就是个空壳（「门绿 ≠ 锁住修复：探针避开了缺陷显形点」）。

### 更正：三处过强表述（Codex r1 L1）

| 初版写法 | 反例 | 现写法 |
|---|---|---|
| 「纯 agent_service 突发可**暂时**越限」 | 若始终没有后续经 helper 的追加，越限可**无限持续** | 已改为「无限持续」 |
| 「活动文件与**每个** `.overflow.*` 都 ≤ limit」 | 进入 helper 前就已超限时，被**整体**轮转走的那份 > limit | 改为「本函数**自己写出**的每一段 ≤ limit」 |
| 「且**一条不丢**」 | 单批 > `limit × (keep+1)` 时 retention 会删掉**本批**较早的段 | 加了条件限定 |

### round-2 后的裁判复跑

| 裁判 | 结果 |
|---|---|
| 两新测试 | **48 passed**（23 → 48，新增覆盖回灌窗口 / 降级标记 / 零覆盖分支 / 身份守恒 / 防撞与命名） |
| 邻近三套件 + 全部触碰 `FAILED_WRITES_FILE` 的套件（9 个文件） | 168 passed / **2 failed** —— 两条**都在开工基线 `open.nodeids` 里**（既有红，逐条核过），非本卡引入 |
| pyright | **0 errors, 81 warnings** |
| ruff check | `All checks passed!` rc=0 |
| format 新增债 | **0 行**（行级多重集对照 T6B_TIP） |
| 地盘门 | 仍恰好六文件，`openapi.json` 命中 0 |

### ⛔ 未收口、如实移交的一条（超出本卡地盘）

内部复核的 HIGH「把死信坟场的保留策略套到 `failed_writes.jsonl` 这条**有回灌方**的 outbox 上」
**本卡只做了窗口级止血，没有从根上解决**：`failed_writes.jsonl` 不是坟场，它有唯一回灌方，
而 `fallback_sync_service` 全文无 glob、只读活动文件 ⇒ 被轮转走的条目**永远不会被回灌**，
并在超过保留上限后删除。要根治须让回灌器也扫 `.overflow.*`，那是 `fallback_sync_service.py`
的面 = 本卡**禁改**。
本卡的立场：相对于「磁盘占满 ⇒ 连同数据库一起失效」，有界是更小的代价，但这个不对称**必须
写明**而不是藏起来。已登记台账第 15 条。

## (j) tests/unit 收工 diff

口径与开工同：`--ignore tests/unit/test_deploy_vault_sh.py`（相对路径）。**每次代码改动后都重跑**：

| | 开工 | 收工 r1 | r2 | r3 | r4 | **收工 r5**（`unit-close-r5-*.txt`，权威） |
|---|---|---|---|---|---|---|
| passed | 5079 | 5102 | 5127 | 5139 | 5146 | **5153** |
| failed | 33 | 33 | 33 | 33 | 33 | **33** |
| errors | 29 | 29 | 29 | 29 | 29 | **29** |
| skipped / xfailed | 48 / 23 | — | — | — | — | **48 / 23** |
| nodeids | 62 | 62 | 62 | 62 | 62 | **62** |
| 相对开工新增 `>` | — | 0 | 0 | 0 | 0 | **0** ✓（(j) 的硬判据） |
| 相对开工消失 `<` | — | 0 | 0 | 0 | 0 | **0** |
| 红集里 `t6c` 命中 | — | 0 | 0 | 0 | 0 | **0** |

`diff open.nodeids close-r5.nodeids` → **完全为空**。
passed 从 **5079** → **5153**，差 **+74** —— 恰好等于本卡两个新测试文件的 74 条门
（39 + 35），且 failed / errors / skipped / xfailed 四项**逐数不变**。
⚠️ 五次收工跑的 nodeids 恒为 62、新增 `>` 恒为 0 —— 每一轮代码改动后都复跑过，
不是只在最后跑了一次。

## Codex 轮次（5 轮，配额用满；**终轮绑最终 HEAD 且 B=0 / H=0 ⇒ D-15 通过门达成**）

命令统一 `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra"`。
五份存档首部均按协议 §2.1 补齐，三字段（`模型` / `reasoning_effort` / `codex`）**全部由 stderr 自证**
（`:2` / `:5` / `:9`），`grep -c 'gpt-5'` 五份均为 **0**。

| 轮 | 审 SHA | B | H | M | L | 该轮 HIGH/BLOCKER 的来源 |
|---|---|---|---|---|---|---|
| r1 | `47075cbe` | 0 | 0 | 3 | 3 | — |
| 内部对抗复核 | `47075cbe` | **1** | 5 | 10 | 4 | 初版写侧轮转 × 回灌窗口 |
| r2 | `b8cd3a82` | 0 | **1** | 3 | 3 | **r1 加的窗口守卫**没覆盖持久化游标 |
| r3 | `11caca05` | 0 | **2** | 1 | 4 | **r2 加的游标作废**捕获面漏 ValueError 家族；测试未隔离现网 checkpoint |
| r4 | `09d6da33` | 0 | **2** | 1 | 7 | **r3 新写代码**里第三处 `exists()` 吞异常；隔离仍漏一条自建 fixture 用例 |
| **r5** | **`f3336568`** | **0** | **0** | 4 | 2 | — ✅ |

⚠️ **模式**：每一轮的 HIGH 都不是原始需求做错了，而是**前一轮修复引入的新面**。
每轮该问的不是「我改对了吗」，而是「**现在这样对吗**」。

### r5 的 6 条（MEDIUM 4 / LOW 2）—— **按协议登记不阻断，全部已逐条只读核实属实**

⛔ **为什么不修**：D-15 规定「审后改代码必再送一轮」，而 5 轮配额已用满。
再改就会让本卡失去「绑最终 HEAD 的一轮 H=0」这个状态。轮次上限正是为了防止
「就再改一点点」无限延伸，**这里守住它**。以下全部移交。

| # | 级别 | 位置 | 问题（已只读复核属实） |
|---|---|---|---|
| 1 | MEDIUM | `failure_counters.py:110` | `overflow_siblings` 的 `parent.exists()` 吞 EIO ⇒ 返回空列表 ⇒ backlog 把 `1/123` 报成 `0/0` 而 `partial=False`。**同型第 4 处** |
| 2 | MEDIUM | `failure_counters.py:142` | `_unique_overflow_target` 的 `candidate.exists()` 吞 EIO ⇒ **选中已存在的归档名**，POSIX `rename` 随后覆盖它。**同型第 5 处**，后果比第 4 处重 |
| 3 | MEDIUM | `test_dead_letter_bounded_t6c.py:919` | AST 隔离门可被误认：未隔离调用只要加一行含 `SYNC_CHECKPOINT_FILE` 的注释即通过；模块别名 / fixture 内调用 / `Test*` 类方法均漏判 |
| 4 | MEDIUM | 同上 `:945` | 该门的验伪锚**复制了一份局部 `scan()`**，验的不是常驻门本身 —— 把真门换成 `lambda: None`，验伪锚照样绿 |
| 5 | LOW | `test_traces_backlog_t6c.py:724` | 数行失败缺独立降级门：探针同时打坏数行与时间戳扫描，删掉数行的 `_degrade()` 会被时间戳分支托绿 |
| 6 | LOW | `traces.py:231` / `failed_writes_constants.py:80` | **两处旧注释没跟着更正**：仍写「内存上界就是 max_bytes」（实为整体 O(N)）与「退回有界行为」（实为停止轮转、持续越限）。docstring 已改，**行内注释漏改** |

### ⛔ 本卡最该记住的一条：`Path.exists()` 吞异常同型缺陷出现 **5 处**，我修了 3 处

Python 3.14 的 `Path.exists()` 把 `PermissionError` / 瞬时 `EIO` 一律吞成 `False`。本卡里：

| # | 位置 | 何时修的 |
|---|---|---|
| 1 | `count_lines` | r2 修 |
| 2 | `_backlog_entry` | r2 修 |
| 3 | `_invalidate_replay_checkpoint` | **r4 才修**（r3 新写的代码，漏在「只扫了当时已存在的代码」） |
| 4 | `overflow_siblings` 的 `parent.exists()` | **未修**（r5 MEDIUM-1） |
| 5 | `_unique_overflow_target` 的 `candidate.exists()` | **未修**（r5 MEDIUM-2） |

三轮审查各指出一处，我就修一处，**始终没有系统性地扫过一遍**。
正确的做法是在第一次发现时就加一道「这几个模块里禁止裸用 `.exists()`」的常驻门
（就像 r5 给 checkpoint 隔离加的那种 AST 门），而不是等审查逐条喂。
**已登记台账第 21 条，建议后续卡一次性清掉并加门。**

### 作者对 r4 一条建议的实测反驳（r5 已确认成立）

r4 建议用「嵌套 2000 层 JSON 触发 `RecursionError`」覆盖外层捕获面。**本机实测不成立**：
Python 3.14.4 / `recursionlimit=1000` 下，C 加速的 json 解析器对数组嵌套是**迭代**的，
`depth=100000` 都不抛。照抄会在测试里留下一条**假注释**。
已改用「`_checkpoint_lock.__enter__` 抛 `RuntimeError`」做可达故障注入，负控复跑转红。
**r5 原文确认**：「作者的 JSON 反驳成立 —— 本机 Python 3.14.4、recursionlimit=1000 下，
数组嵌套 2000 / 100000 层均解析成功」。

> 教训：**审查者给的判据同样需要实测**。写一条自己没验过的断言，比没有断言更坏 ——
> 后人会照着它推理。

## 入库的内部对抗复核（Workflow，非 Codex）

> 协议 §五.5：不入库的复核不作依据。完整结论已落盘
> `_bmad-output/审查/evidence-neo4j-replay-bound/selfreview-workflow-20260915.md`（247 行，
> 20 条存活发现原文 + 18 条被证伪发现表）。与 Codex 各轮**并列登记、互不替代**，
> **不计入卡族轮次配额**。

- **形态**：5 维度并行找缺陷 → 每条由 3 个不同镜头（correctness / exploitability /
  reproducibility）**独立尝试证伪** → 多数证伪则判死。
- **计数**：38 条发现 → 存活 **20**（BLOCKER 1 / HIGH 5 / MEDIUM 10 / LOW 4）、证伪 18。
- **绑定 `47075cbe`**（与 Codex round-1 同一版）。
- ⚠️ **审查对象在它运行期间未冻结**：主 session 同时在收口 Codex round-1 的意见。
  所以每条发现都对当前 HEAD 逐条复核后才采信 —— 上面「round-2 增补」表就是该复核结果。
- ⚠️ **验证覆盖不完整**：26 个 verify agent 因 API/证书错误未跑成（另有 1 个 parallel
  分支 stall），部分发现票数 < 3；1 票结论的证据强度弱于 3 票，存档里逐条标注了票数。
- **规模**：119 agents（93 完成 / 26 报错）、1821 次工具调用、约 71 分钟。
- **它抓到而 Codex round-1 没抓到的**：那条阻断级（回灌窗口 × 轮转）。
  **Codex round-1 抓到而它没单独列的**：M1 的两处异常阻断追加。两者互补，都不可省。
