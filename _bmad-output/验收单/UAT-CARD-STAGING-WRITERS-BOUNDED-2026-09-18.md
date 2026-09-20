# UAT — CARD-STAGING-WRITERS-BOUNDED

> 批次: `BATCH-2026-09-18-第十五批` · 车道 `card-p2-outbox`（分支 `card/p2-outbox`）· 本车道第 **2/3** 张
> `PREV` = `ac0993b4`（`ac0993b450480ea95153daf9067c35dd2b5dad34`，P2-A CARD-DEADLETTER-PATH-ANCHOR 末 commit，第 0 分钟取一次）
> `B15_BASE` = `9c4e7e82`（`git merge-base --is-ancestor 9c4e7e82 HEAD` → rc=0）
> 本卡**单 commit**（多轮 `--amend` 收敛）。SHA 变迁：`2a921e77`（Codex r1 审）→ `3fb1557e`（r2 审）
> → `5bb52629`（r3 审）→ `d56d8128` → `732d2a96`（r4 审）→ `80295391`（r4 后；r5 送审两次 0 字节）→ `d2ebf694`（2026-09-19 amend，含 r5 失败档与本文更新；补审 r6 绑）→ **`4621946f`（H1 整改；r7 绑；最终代码 HEAD）**
> 补审（协议 §2.4.2）：ZCode × GLM-5.3 round-6 绑终态 `d2ebf694` — **B 0 / H 1** / M 0 / L 3 ⇒ 未达 B/H=0；只审不改、零代码改动，停报主 session（存档 `zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md`，见文末补审节）
> H1 整改（2026-09-20，主 session 裁「整改」）：死信链行边界防护（`store` + `write_dead_letter` 复用 `ensure_line_boundary`）；Codex r7 绑 `4621946f` — **B 0 / H 0** / M 0 / L 3 ⇒ 收口（LOW×3 登记后续小补丁；见文末「H1 整改」节）
> 证据目录 `_bmad-output/审查/evidence-staging-writers-bounded/`

## 〇 一句话

`failed_writes.jsonl` 的**第三个**写者（`agent_service._record_failed_write`）切到有界追加；
`dead_letter_episodes.jsonl` 写侧接上同一个轮转原语；
回灌窗口守卫从「只看锁着没」加上时间维度；
批次写失败从「只等 `cleanup()` 刷盘」改成「即时落盘 + `cleanup()` 兜底」，并把失败语义分流成
「磁盘故障留着重试 / 序列化与编码失败逐条丢弃」；新增 `ensure_line_boundary` 防「半行尾巴吞掉下一条记录」；
3 处被 `Path.exists()` 吞掉的 `PermissionError` 改成 `stat` / `iterdir` 显式分流。
**e3（`outbox/events.jsonl` 有界）按卡文「可退子项」退回第十六批**，理由见 §六 r1-HIGH-3。

---

## 一 §〇 事实复核 —— 卡文 → 实测（漂移逐条登记）

P2-A 改过 `episode_worker.py` / `failure_counters.py` / `traces.py` / `test_failure_observability.py`，
卡文里基于旧主干的行号必漂。逐条按**符号名**重定位：

| 卡文 | 实测（PREV `ac0993b4` 上） | 判定 |
|---|---|---|
| `agent_service._record_failed_write` `:98–136`，写者段 `:128–132`，裸 `open` `:130` | AST `:98–136`；`mkdir` `:128` / `with failed_writes_lock:` `:129` / `open(FAILED_WRITES_FILE, "a"` **`:130`** / `f.write` `:131` | ✅ 一致 |
| `failed_writes_constants._replay_in_flight` `:36–85`，`return bool(_sync_all_lock.locked())` `:83` | AST `:36–85`；`locked()` 行 **`:83`** | ✅ 一致 |
| `append_failed_writes_bounded` `:192–284` | AST `:192–284` | ✅ 一致 |
| `failure_counters` `.exists()` 在 `:110` / `:142` | AST Call 实测 **`:121` / `:153`** | ⚠️ **漂 +11**：P2-A 插入了 `DEAD_LETTER_EPISODES_PATH` 锚（11 行注释 + 1 行常量） |
| `episode_worker` `.exists()` 在 `:271` | AST Call 实测 **`:276`** | ⚠️ **漂 +5**（P2-A 改动） |
| `episode_worker.DeadLetterStore` `:199–274` | AST `:200–279` | ⚠️ 漂 +1/+5 |
| `event_bus._write_outbox` `:342–366`，裸 `open` `:359` | AST `:342–366`；`open(OUTBOX_FILE, "a"` **`:359`** | ✅ 一致（e3 已退，本卡对该文件**零改动**） |
| `fallback_sync_service._sync_all_lock` `:84`，`sync_all_fallbacks` `:93–111` | `grep` 命中 `:84 / :101 / :110`；AST `:93–111` | ✅ 一致 |
| finalize「只增不减」判据 `:365` | `if len(current_lines) > len(lines):` 实测 **`:365`** | ✅ 一致 |
| `memory_service._pending_failed_writes` 6 命中：init `:273` / append `:1423` / 刷盘 `:2846–2847` | `grep` 实测同 | ✅ 一致 |
| `_flush_pending_failed_writes` `:2855–2886` | AST `:2855–2886` | ✅ 一致 |
| T6-C docstring 自称三写者在 `memory_service:515 / :2871 / agent_service:131` | 持锁行实测 `:515 / :2872 / :129` | ⚠️ 卡文 §〇⑤ 已预告的注释漂移；本卡改写该段时**改用符号名**，不再写行号 |
| 既有门 `test_dead_letter_bounded_t6c.py` 39 个 `test_` | AST 实测 **39** | ✅ 一致（收工仍 39 全绿） |
| unit 红基线 `evidence-b15/unit-red-baseline-9c4e7e82.txt` `grep -vc '^#'` | **33** | ✅ 一致 |

**改后**（末态 `80295391`）符号区间，供 P2-C 引用（⚠️ 一律按**符号名**引用，不要抄行号）：
`agent_service._record_failed_write` `:102–145`；
`failed_writes_constants`：`REPLAY_WINDOW_MAX_SECONDS` `:43`、`_replay_in_flight` `:46–157`、
`ensure_line_boundary`（新增）、`append_failed_writes_bounded`（入口首行调 `ensure_line_boundary`）；
`failure_counters.overflow_siblings` / `_unique_overflow_target`；
`fallback_sync_service._sync_all_started_at` `:97`、`sync_all_fallbacks` `:106–137`；
`memory_service` 即时刷盘调用 `:1435`、`_flush_pending_failed_writes`；
`episode_worker.DeadLetterStore`。

---

## 二 DoD-3 段 4-A：Claude 已代验（逐条贴证据）

### (a) 第 0 分钟

```
ac0993b4            ← PREV
1                   ← log -1 %s 含 CARD-DEADLETTER-PATH-ANCHOR
0                   ← git status --porcelain | wc -l
anc=0               ← git merge-base --is-ancestor 9c4e7e82 HEAD
33                  ← grep -vc '^#' "$BASE"
pyright OK / pytest-ok / env-ok
```

开工 unit 基线（跑法与基线头第 3 行逐字同，不带 `--ignore`）：
`unit-open-20260918T180141.txt` → `32 failed, 5736 passed, 44 skipped, 13 xfailed … rc=1`。
`diff base.nodeids open.nodeids` 只有一行 `<`：
`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`
（基线头第 4 行自己标注的 flaky，本轮转绿）。**差集只有 `<`，登记不阻断开工。**

### (b)(f) 结构判据 —— 成对 + 对照锚

`struct-before-20260918T180420.txt` / `struct-after-r3b-*.txt`：

| 判据 | 改前 | 改后 | 期望 |
|---|---|---|---|
| `append_failed_writes_bounded(` @ `agent_service.py` | **0** | **1** | 0→1 ✅ |
| `append_failed_writes_bounded(` @ `memory_service.py`（**验伪锚**） | **2** | **2** | 恒 2 ✅ 证明计数器只随 agent_service 变 |
| `open(FAILED_WRITES_FILE, "a"` @ `agent_service.py` | **1** | **0** | 1→0 ✅ |
| `rotate_if_over_limit(` @ `episode_worker.py` | **0** | **1** | 0→1 ✅ |
| `rotate_if_over_limit(` @ `event_bus.py` | **0** | **0** | **e3 已退 ⇒ 0**（如实，非 1） |
| `_sync_all_started_at` @ `fallback_sync_service.py` / `failed_writes_constants.py` | **0 / 0** | **4 / 1** | ≥3 / ≥1 ✅ |
| `REPLAY_WINDOW_MAX_SECONDS` @ `failed_writes_constants.py` | **0** | **6** | ≥2 ✅ |
| `ensure_line_boundary` @ `failed_writes_constants.py` / `memory_service.py` | **0 / 0** | **≥2 / 3** | 新增原语已接线 ✅ |
| `_flush_pending_failed_writes()` @ `memory_service.py` | 1 行（`:2847`） | 2 行（**`:1435`** / `:2860` 附近） | 新行 ∈ `[1423,1470]` ✅ |
| `.exists()` AST Call @ `failure_counters.py` | **2** `[121,153]` | **0** `[]` | 2→0 ✅ |
| `.exists()` AST Call @ `episode_worker.py` | **1** `[276]` | **0** `[]` | 1→0 ✅ |
| `.exists()` AST Call @ `event_bus.py`（**对照锚**） | **1** `[376]` | **1** `[376]` | 恒 1 ✅ |
| `.exists()` AST Call @ `fallback_sync_service.py`（**对照锚**） | **9** | **9** | 恒 9（回灌侧未动） ✅ |
| `diff <(git show ac0993b4:event_bus.py) event_bus.py`（**e3 退回自证**） | — | **空** | 逐字节同 PREV ✅ |

### (b)(g) 行为门 —— 先红后绿，收集数核对

- **先红** `staging-red-20260918T181003.txt` → **`9 failed, 4 passed`**（首版 13 条）。
  9 条红**全部**落在行为断言，无一条 `ImportError` / `AttributeError`：
  `活动文件超行数：8 > 5`（第三写者 / dead-letter / outbox 三条）、`锁挂住超过上限后仍未轮转`、
  `持锁期间没有打时间戳: ['missing']`、`未调 cleanup() 前文件里找不到该 episode_id`、
  `权限错误被吞成了空列表: []`、`探测被权限错误拦下的名字仍被交了出去`、`权限错误被吞成了行数: 1`。
  改前即绿的 4 条是**对照输入**：`respects_fresh_window` / `treats_direct_lock_holder_as_in_flight`
  / AST 常驻门 / 扫描器验伪锚。
- **后绿（末态）** → **`26 passed`**。
- **收集数核对**：`passed` 数 26 = 本文件 AST `test_` 数 26。非 `rc=5`、非 `0 selected`。

26 条组成（相对首版 13 条）：**−1** `test_outbox_events_is_bounded`（e3 退）、
**+14** 全部来自 Codex 五轮与车道五视角自审发现的整改（见 §六）。

```
test_agent_service_third_writer_is_bounded
test_third_writer_does_not_concatenate_onto_dangling_tail          ← r4 新增
test_replay_guard_times_out_when_lock_stuck
test_replay_guard_respects_fresh_window
test_replay_guard_treats_direct_lock_holder_as_in_flight
test_sync_all_fallbacks_stamps_and_clears_started_at
test_batch_failed_writes_hit_disk_before_cleanup
test_flush_keeps_pending_when_disk_write_fails                     ← r2 新增
test_flush_drops_unserializable_pending_writes                     ← r2 新增
test_flush_repairs_dangling_tail_before_retry                      ← r3 新增
test_flush_keeps_good_entries_when_one_is_unserializable           ← r3 新增
test_flush_drops_unencodable_entry_without_raising                 ← r4 新增
test_flush_does_not_glue_when_boundary_repair_fails                ← 自审新增
test_flush_still_writes_when_boundary_probe_is_unreadable          ← 自审新增（回归门）
test_unobservable_replay_state_is_false_even_while_locked          ← 自审新增（鉴别门）
test_replay_window_open_keeps_whole_multiline_batch_unrotated      ← 自审新增
test_replay_guard_logs_error_when_window_times_out                 ← 自审新增
test_started_at_is_not_stamped_while_waiting_for_the_lock          ← r5 新增（鉴别门）
test_no_glue_when_probe_fails_on_a_dangling_tail                   ← r5 新增
test_sep_is_dropped_after_a_real_rotation                          ← r5 新增
test_dead_letter_episodes_is_bounded
test_overflow_siblings_does_not_swallow_permission_error
test_unique_overflow_target_does_not_swallow_stat_error
test_dead_letter_store_count_does_not_swallow_permission_error
test_every_staging_test_isolates_live_files
test_isolation_scanner_can_actually_detect_an_offender
```

### ⚠️ exists 门的注入点被更正 —— 如实登记（卡文给的范式在本 Python 上无效）

卡文 (g)⑥ 与既有 T6-C 门的范式是 `monkeypatch type(path).stat`。**首跑实测该范式对本卡三条 exists 门无效**：

```
python 3.14.4
def exists(self, *, follow_symlinks=True):
    if follow_symlinks:
        return os.path.exists(self)      # ← 不经过 Path.stat
    return os.path.lexists(self)
```

`Path.exists()` 走 `os.path.exists` → `genericpath.exists` → `os.stat`，吞异常发生在
`genericpath.exists` 自己的 `except (OSError, ValueError): return False` 里。
打 `type(path).stat` 时改前代码**根本看不到注入的故障** —— 首跑
`test_overflow_siblings_…` 因此**误绿**（绿在 `iterdir` 那条更靠后的判据上，不是它声称的那条）。
更正后的注入点是 `os.stat`（+ `os.scandir`，`Path.iterdir` 用它）。
实测三行自证：`sub.exists() => False` / `iterdir raised PermissionError` / `Path.stat raised PermissionError`。
更正后三条门改前**全红**。T6-C 的 `test_count_lines_does_not_swallow_permission_error`
打 `type(path).stat` 是**正确**的 —— `count_lines` 调的就是 `path.stat()`，层不同，那条门不受影响（收工仍绿）。

### (h) pyright 保持 0 —— 成对

- 改前 `pyright-open-20260918T181703.txt` → **`0 errors, 80 warnings, 0 informations`**
  （改前态用 `git show ac0993b4:<path> > <path>` 就地还原 7 个 app 文件后跑，EXIT trap 无条件还原；
  存档贴三组 sha256：跑前(改后态) / 还原到 PREV 后 / trap 还原后，**第一组与第三组逐行逐字同**）
- 改后 `pyright-close-r5-*.txt` → **`0 errors, 80 warnings, 0 informations`**
- 命令带 `cd backend`，绝对路径 + `test -x` 自证，**未用 `| tail -1`**
- 本卡**零** `# pyright: ignore` / `# type: ignore` 新增；未用 `LEFTHOOK_EXCLUDE=python-typecheck`
  （hook 实测通过：`[Python] Typecheck done (exit: 0)`）

### ruff —— 本卡改动文件

`ruff-r5-*.txt`：`files=7`（e3 退回后 `event_bus.py` 不在 diff 面内），
`ruff check` → **`All checks passed!` rc=0**。
**验伪锚**（`backend/ruff.toml` 的 `select` 不含 F401，故用 **F821**）：
喂 `def f(): return undefined_name_xyz` → `F821` + `rc=1`。

### (o) `ruff format --check` 门与 `LEFTHOOK_EXCLUDE=python-lint`

手册 §零.3：`ruff format --check` 自 T8-G 起**硬禁**、**改动行自己 format**，
整仓 462 文件 format 归主 session 末位（D-40）。本卡实况：

1. **本卡新文件**（`test_staging_writers_bounded.py`）已 `ruff format`，hook 判 `already formatted`。
2. **被 hook 拦下的 5 个文件是 B15_BASE 上就已 dirty 的**（`git archive 9c4e7e82` 到临时目录跑
   `ruff format --check` 实测同样 5 个 `Would reformat`）。本卡 dirty 集 = 基线 dirty 集，**未新增一个文件**。
3. **改动行零格式漂移**（逐行判据 `ruff-format-changed-lines-r5-*.txt`）：对每个文件取
   「本卡改动行号集合」（`git diff -U0 ac0993b4` 的 `+` 侧）与「`ruff format` 会改的行号集合」，
   **交集必须为空** → **PASS**，验伪锚（已知格式不合规的两行）能抓到漂移 ✅。
   ⚠️ 该判据**两次抓到本卡自己的行**：`agent_service.py:142-144`（多行调用）、
   `memory_service.py:2906`（`logger.warning` 多行）。两处改成单行后复跑 PASS。判据真在抓本卡的行。
4. ⚠️ **中途出过一次真越界并已还原（如实登记）**：我对两个**生产**文件跑了整文件 `ruff format`，
   `memory_service.py` 因此多出约 20 个界外 hunk，其中 4 个（`@@ -1832/-1865/-1971/-2013`）落在卡文
   要求**零 hunk** 的 `:1788–2060`（P1 G4-5 面）。抓到它的是行号判据：
   `_flush_pending_failed_writes()` 从 1437 跳到 1425。处置：`git show HEAD:<file> > <file>` 还原
   （sha256 回到 `889640f9195f` / `11ca758c3312`，与负控 `before=` 逐字同），再逐处重贴本卡改动，
   **不再对共享文件跑整文件 format**。末态 `memory_service.py` 只有 3 个 hunk，全部在声明区间内。
5. 提交实际用 `LEFTHOOK_EXCLUDE=python-lint`（**零** `--no-verify`、**零**
   `LEFTHOOK_EXCLUDE=python-typecheck`），与本车道 P2-A 同口径。**这条记为待裁决**，见 §五.3。

### (i) 既有套件不回退

- 点名套件（10 个 + 本卡新增关注的 `test_story_30_24_boundary.py`）`named-close-r5-*.txt` →
  `2 failed, 255 passed, 5 skipped, 5 xfailed`。两条红：
  `test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores`
  与 `test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first`
  —— **`grep -F` 实测两条同时在 `base.nodeids`（B15 基线）与 `open.nodeids`（本卡开工基线）里 = 主干既有红**。
  验伪锚：`grep -cF 'test_staging_writers_bounded' base.nodeids` → **0**。
  `test_dead_letter_bounded_t6c.py` AST 计数仍 **39**，本轮**全绿**（含两条真锁门）。
  ⚠️ 「开工同跑一次 `named-open-*`」未单独跑：这些文件全在 `tests/unit` 下，开工全量基线
  `unit-open-*`（同跑法、同 nodeid 口径）已覆盖，两条红的归属由它判定。
- `tests/regression` 目录级：多轮均 **`1913 passed, 6 skipped, 1 xfailed`** rc=0 `blocked=0`。
- agent_service 写者面（W4 只记账不拦）：
  ⚠️ 卡文给的 `-k record_failed_write` **实测只选中 1 条**（卡文预期 ≥3）——
  另两条打桩用例叫 `test_failed_write_contains_all_required_fields` /
  `test_multiple_failed_writes_are_appended_not_overwritten`，名字里没有 `record_`。
  两次都落档：`1 selected / 1 passed` 与 **`-k failed_write` → 3 selected / 3 passed**，
  两次均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。
- `tests/unit` 收工：见 §三。

### ⚠️ 收工 unit 出现过 5 条新红 —— 归因为环境，非本卡引入（如实登记）

`unit-close-r3` 那一轮出现 5 条 `tests/unit/test_deploy_vault_sh.py` 新红
（`test_preflight_npm_build_*` / `test_preflight_accepts_leading_zero_cap`）。归因链：

1. **无因果通路**：该测试文件 AST 实测 **零 `app.*` import**，而本卡 6 个生产文件全在 `backend/app/` 下。
2. **被测对象未改**：`backend/tests/unit/test_deploy_vault_sh.py` 与 `scripts/deploy-vault.sh`
   两者 sha256 均与 `PREV` **逐字节相同**。
3. **失败正文即证据**：`preflight: FAIL npm run build 超时（墙钟上限 5s, 已杀 npm 所在进程组）` ——
   5 秒**墙钟**上限打死了本该很快的假 npm。
4. **负载对照**：那一轮本机 `load averages: 15.16`（另一车道 `card-p3-deploy` 同时在跑自己的测试），
   该文件单跑耗时 **33 分钟**（平时几分钟）。
5. **决定性复跑**：同一 HEAD 上单独跑这 5 条 → **`5 passed in 14.91s`**；
   随后负载回落时的 `unit-close-r4` / `r5` / `r6` 全量跑，这 5 条**均未复现**。

### ⚠️ W4 哨兵 `blocked=` 在 0 / 1 之间翻转 —— 归因为基线那条 flaky，非本卡引入

末轮 unit 的哨兵行是 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)`，
而前几轮多为 `blocked=0`。归因链（协议 §3：哨兵绑 `blocked=` 次数 + 失败正文，**不绑 nodeid**）：

1. **哨兵自己打印了归属**（`unit-close-r5f-*.txt:380-384`，最强形态的证据 —— 不是我推断的）：

   ```
   ______________ test_accept_candidate_already_accepted_returns_422 ______________
   live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
     - ('::1', 7691, 0, 0) on thread MainThread
       (owner=tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422)
   ```

2. 这条用例正是 **B15 基线头第 4 行自己标注的 flaky**：
   「flaky test_candidate_service::test_accept_candidate_already_accepted_returns_422 已在集内」。
3. 两个方向**都在基线账内**，且与失败数机械对应：
   - 它这一轮尝试连库 ⇒ 哨兵把它转成失败 ⇒ `33 failed` + `blocked=1` + `diff base close` **为空**（`diff_rc=0`）；
   - 它这一轮没尝试 ⇒ `32 failed` + `blocked=0` + `diff` 出现一行 `<`。
   九轮 unit 实测全部符合这个对应关系。
4. **无因果通路**：本卡 7 个改动文件里没有 `candidate_service` 及其测试；
   `grep` 实测该测试文件与被测服务均与 `PREV` 无关（不在本卡 diff 面内）。

⇒ `blocked=` 的 0/1 翻转是**基线已登记的 flaky 的两个面**，不是本卡引入的偷连；
末轮那次 `blocked=1` 反而让 `diff` 与 33 条基线**完全一致**。

### (k) 负控输入十二段（各只拆一层，EXIT trap `git show HEAD:<path>` 还原 + sha256 前后比对）

⚠️ 十二段全部在**末态 HEAD `80295391`** 上重跑（协议 §3 :73），每段 `before=` 与 `restored=` 逐段相同；
跑完 7 个源文件均与 HEAD 逐字节一致（逐文件 sha256 核过）。

| 段 | 变异 | 指定断言必红（失败正文） |
|---|---|---|
| ① `agent_service.py` | 有界 helper 换回裸 `open(..., "a")` | `third_writer_is_bounded` — `活动文件超行数：8 > 5` |
| ② `failed_writes_constants.py` | 删 `_replay_in_flight` 超时分支 | `times_out_when_lock_stuck` — `锁挂住超过上限后仍未轮转`；同时 `logs_error_when_window_times_out` 红 |
| ③ `memory_service.py` | 删即时刷盘调用 | `hit_disk_before_cleanup` — `未调 cleanup() 前文件里找不到该 episode_id` |
| ④ `memory_service.py` | `OSError` 分支改回无条件 `clear()` | `flush_keeps_pending_when_disk_write_fails` — `磁盘写失败后 pending 被清空` |
| ⑤ `failed_writes_constants.py` | 删入口的 `ensure_line_boundary` | `third_writer_does_not_concatenate_onto_dangling_tail` — 正文即粘连行 `'{"episo{"timestamp": …}'` |
| ⑥ `memory_service.py` | 逐条序列化改「一条坏就整批丢」 | `keeps_good_entries_when_one_is_unserializable` — `好条目跟着坏条目一起被丢了: set()` |
| ⑦b `memory_service.py` | 恢复「边界保不住就拒写」分支 | `flush_does_not_glue_when_boundary_repair_fails` — `记录没有成为一条可解析的行` |
| ⑧ `memory_service.py` | 删 `line.encode("utf-8")` 编码预验 | `flush_drops_unencodable_entry_without_raising` — `好条目没落盘: set()` |
| ⑨ `failed_writes_constants.py` | 保留补边界但删 `sep` 前缀机制 | `flush_does_not_glue_when_boundary_repair_fails` — 正文即粘连行 `'{"episo{"episode_id": "sep-A"}'` |
| ⑩ `failed_writes_constants.py` | import 改回 `from app.services import fallback_sync_service` | `unobservable_replay_state_is_false_even_while_locked` — `观测不到回灌状态却没判 False` |
| ⑪ `failed_writes_constants.py` | 探测失败分支改回 `return True`（按「没有半行」处理） | `no_glue_when_probe_fails_on_a_dangling_tail` — 正文即粘连行 `'{"episo{"episode_id": "blind-glue-A"}'` |
| ⑫ `failed_writes_constants.py` | 删「真轮转后清 `sep`」 | `sep_is_dropped_after_a_real_rotation` — `轮转后的新文件多了一个空行 —— 首段 2 行 > 上限 1` |

存档 `negctl-all-r10-*.txt`（前序轮次 `negctl-all-r9-*.txt` 保留）。

> ⚠️ **三段曾经 SURVIVED，验伪后发现是门的真缺口（不是变异没跑到）**，补门后才转红：
> 一条被**冗余掩盖**（另一处调用替它兜住了）；一条的**注入点过宽**（连追加一起打死，
> 判据分不清是哪一环救的）；一条是**数据顺序**（坏条目排在好条目之后，好条目在异常前已落盘）。
> 教训：行为门里「输入的**顺序**」和「输入的内容」同样是判据的一部分。

> ⚠️ **三份负控存档作废，勿引用**（教训各不相同，逐条登记）：
> ① `negctl-1-20260918T181742.txt` —— 在 commit **之前**跑，`trap 'git show HEAD:…'` 把尚未提交的
> 真改动一并还原掉（`before=1794028e…` / `restored=e943423f…` 两行不同即是证据），rc 仍为 0。
> ② `negctl-1-r4` 段① —— 变异脚本经 `python3 -c` 时转义层数不对，写成了**字面 `\n`** 而非换行，
> 红的断言从「超行数」变成「没有 overflow」。改用**脚本文件**避开转义层后重跑，红回指定断言。
> ③ `negctl-all-r8` —— 同 ① 的复发：又在未提交状态下跑，把 r5 的代码改动抹掉了。
> **教训（付了两次学费）：协议 §一(k) 的 `git show HEAD:` 还原默认代码已 commit；
> 负控必须在 commit 之后跑。**

### (l) 地盘门

末态 `git --no-pager diff --stat --no-color ac0993b4 HEAD -- . ':(exclude)_bmad-output'` = **7 个文件**
（e3 退回后 `event_bus.py` 退出 diff 面），全部在卡文 (l) 白名单内。
**未出现** `main.py` / `traces.py` / `neo4j_client.py` / `canvas_service.py` / 任何 conftest / 任何别车道文件。
**验伪锚**：去掉 `':(exclude)_bmad-output'` 后 `_bmad-output/` 路径多出 19 条 ⇒ exclude 真的在生效。

逐 hunk：

- `memory_service.py`：3 个 hunk `@@ +1428` / `@@ +2865` / `@@ +2892`，全部 ∈ `[1423,1686] ∪ [2672,2900]`。
  **`:1788–2060`（P1 G4-5）零 hunk** ✅
  ⚠️ **越出卡文 prose 的一处，如实登记**：卡文写「只 `:2855–2866` docstring」，而 Codex r1 HIGH-2 的修复
  必须动 `_flush_pending_failed_writes` 的 `finally: clear()`。该 hunk 仍落在卡文 §二 9 的
  **自动判据区间** `[2672,2900]` 内，但超出 prose 的「docstring only」。请主 session 裁定（§五.7）。
  ⚠️ 另：`ensure_line_boundary` 采用**方法体内局部 import**而非模块顶部 import —— 顶部 import 块（`:60`）
  不在声明区间内，局部 import 是为了不越界，理由已写进代码注释。
- `fallback_sync_service.py`：hunk 旧侧起始行 83 / 107，均 ≤111。hunk 2 全文核过：
  `async def _sync_all_fallbacks_locked` 只作**上下文行**（行首空格，非 `+`/`-`），**`:113` 起一行未改** ✅
- `episode_worker.py`：hunk 全在 import 块与 `DeadLetterStore` 内。P1 G4-5 的 `group_id` 那行按符号
  重定位在 **`:611`**，**无 hunk 覆盖** ✅。`__init__` 的默认路径（P2-A 定稿面）未改。
- `event_bus.py`：**零 hunk**（逐字节同 PREV，e3 退回自证）。
- `failed_writes_constants.py` / `failure_counters.py` / `agent_service.py`：均在白名单，无行区间限制
  （`agent_service.py` 只改 `_record_failed_write` 体内 3 行 + import 块 1 处）。

### (j) openapi

本卡只碰 `backend/app/services/` + `backend/app/core/` + `backend/tests/`，
`spec-sync-flat`（glob `backend/app/{api,models,schemas,mcp}/*.py`）与 `spec-sync-root`
（`backend/app/{main.py,config.py}`）hook 实测 **`(skip) no matching staged files`**。
`git show --name-only HEAD | grep -c openapi.json` → **0**。**不适用，未发生塞入。**

### (m) 现网只读 —— 含 sha256 兜底（`git status` 在这里是瞎的）

- 新门所有文件路径**均为 `tmp_path`**；每个 fixture 都额外把
  `fallback_sync_service.SYNC_CHECKPOINT_FILE` 指向 `tmp_path`。未设任何指向现网的环境变量。
- 未写 live vault；**本卡零连库**（新门与负控全程 `blocked=0 / advisory=0 / unaccounted=0`）。
- 改动面**代码层**（tokenize 去掉注释与字符串后）对 `7691` / `7687` / `fsrs_bridge` / `decay_beta`
  的命中 = **全部 0**。文本层 2 处命中均为注释/docstring（`memory_service.py:346` 本卡未改；
  新测试文件 docstring 里「不连 7691/7687」这句声明本身）。
- ⛔ **`git status --porcelain backend/data/` 不是有效兜底**（Codex r2 更正）：
  `backend/data/.gitignore` 的 `*.jsonl` 把这些文件连同 `*.overflow.*.jsonl` 一起忽略，status 恒空。
  改用 **`backend/data/` 逐文件 sha256 跑前/跑后快照**（`backend-data-snapshot-*.txt`）。
- **该兜底立刻抓到了东西**：跑完整 `tests/unit` 后 `failed_writes.jsonl` / `failed_edge_syncs.jsonl`
  / `outbox/events.jsonl` 三个现网文件被改写。定位：
  - **本卡新门单跑 → `backend/data/` 零变化 ✅**（`backend-data-mygate-*.txt`）
  - 写者是 **P2-A 验收单 §三 已定位并登记的 4 个地盘外既有测试**
    （`test_canvas_edge_bulk_sync.py` / `test_canvas_edge_sync.py` / `test_agent_memory_trigger.py`
    / `test_story_30_22_agent_trigger_deep.py`），P2-A 已修自己地盘内的 2 个、其余只登记不改。
  - 本卡补测到**第五个**：**`tests/unit/test_event_bus.py` 写脏 `backend/data/outbox/events.jsonl`**
    （定向实测 `events.jsonl` sha256 前后不同）—— 既有、地盘外，登记见 §五.8。
    ⚠️ 这也**反证 e3 退回是对的**：若当时接了 outbox 有界，这条既有测试会直接在现网
    `backend/data/` 里轮转出 `.overflow.*` 代际。
- `ls backend/data/*.overflow.*` → **无匹配**（本卡零产物）。

### (o) 提交自检

```
git log -1 --format=%s | wc -m          → 87      （≤101 ✅）
… | grep -c CARD-STAGING-WRITERS-BOUNDED → 1      （含卡号 ✅）
git show --name-only HEAD | grep -c stderr        → 0
git show --name-only HEAD | grep -c openapi.json  → 0
```

单卡单 commit（多次 `--amend` 收敛为一个），type = `fix`，body 逐行 `wc -m` 最大 **78**（≤100）。**未 push。**

---

## 三 末态裁判汇总

| 裁判 | 结果 | 存档 |
|---|---|---|
| 新门（19 条） | **19 passed**，= AST `test_` 数 | `staging-green-*` |
| 负控八段 | 各红在指定断言，对照同轮全绿，八段 sha256 前后逐字同 | `negctl-all-r6/r7-*` |
| pyright `app` | **0 errors, 80 warnings** | `pyright-close-r5-*` |
| ruff check（7 文件） | `All checks passed!` rc=0 | `ruff-r5-*` |
| 改动行格式漂移 | **交集全空 PASS** + 验伪锚有效 | `ruff-format-changed-lines-r5-*` |
| 点名 11 套件 | `2 failed(主干既有), 255 passed` | `named-close-r5-*` |
| `tests/regression` 目录级 | `1913 passed`，`blocked=0` | `regression-close-r5-*` |
| `tests/unit` 收工 | `diff base close` **只允许 `<`** —— 见下 | `unit-close-r6-*` / `close-r6.nodeids` |
| `backend/data/` sha256 | 本卡新门单跑零变化；全量跑的变化归既有地盘外写者 | `backend-data-snapshot-*` |
| 地盘门 | 7 文件 ⊆ 白名单，逐 hunk 在区间内，验伪锚 19 | `territory-r5-*` |

---

## 四 本卡未证明什么（≥4）

1. **未证明**守卫超时到期、而回灌**确实**还在跑（只是慢，不是挂住）时不会丢条目。恰恰相反：
   Codex r1/r2/r3 连续三轮确认**本卡为了换回「有界」重新打开了一条缝** —— 超时放行轮转会让活动文件变短，
   `_sync_failed_writes` finalize 的 `if len(current_lines) > len(lines)` 算出 `new_lines=[]`，
   窗口内新条目被整份覆盖或被改名成 `.synced.`（谎称已回灌）。`_invalidate_replay_checkpoint`
   只作废游标，**挡不住**这次 finalize。本卡只把「无限期」改成「有上限」，移交 P2-C。
2. **未证明** 1800 秒默认值对现网回灌量级合适。只按 10000 行上限逐条 await 重放估的量级，**未在现网实测**。
3. **「上限至多失效 N 秒」不成立**：超时只覆盖「经 `sync_all_fallbacks` 打过时间戳」这一种持锁。
   其余三条路径上越限仍可无限持续：① 直接持锁者（时间戳 `None`）无论多久都判窗口开着；
   ② 轮转持续失败（权限等）时调用方仍继续追加；③ import 不到依赖时
   `_invalidate_replay_checkpoint` 返回 False，净效果是**永不轮转**。
4. **时间戳量的是耗时，不是存活性**：一次又慢又健康的回灌和一次挂死的回灌在守卫眼里长得一模一样。
5. **未证明**「时间戳只由 `sync_all_fallbacks` 打」这条前提将来仍成立：任何新增的
   `async with _sync_all_lock:` 直接持锁点都会得到 `None` 语义，本卡**没有**加门锁住它。
6. **即时刷盘的同步 IO 未做异步化**：新调用点在 async 的 `record_batch_learning_events` 里，
   数行/轮转/追加期间事件循环不调度别的协程。**未测调度延迟**。
7. **`ensure_line_boundary` 的覆盖是「行边界」不是「记录完整性」**：截断发生在 UTF-8 多字节字符
   **内部**时，补上换行后那一行仍然整体不可解码（本卡的半行门只覆盖 ASCII 截断）。
   补换行只保证**下一条**记录完好，不保证救回残缺那条。
8. **完整行部分写入后的重复未消除**：`append_failed_writes_bounded` 若已写进若干完整行才抛 OSError，
   保留 pending 会在重试时产生**重复**条目。死信文件里重复远比丢失轻，但确实未消除。
9. **e3 退回 ⇒ `outbox/events.jsonl` 仍无界**（`_write_outbox` 逐字节同 PREV）。
10. `canvas_events_fallback.json`（截断最旧式「有界」）与 `neo4j_memory.json`（整份原子写）两面**未改**。
11. 轮转出去的 `dead_letter_episodes.overflow.*` 代际**本卡无回灌方**（与 T6-C 三条链同语义）。
12. 即时刷盘只覆盖 `record_batch_learning_events` 这**一个** append 站点（AST 实测全文件唯一 append），
    **未证明**将来第二个 append 站点也会即时落盘 —— 没有门锁它。
13. **跨进程**并发写同一 JSONL 仍非原子：三条链各自的锁都是**进程内**的。
14. **AST 常驻门是名字层的必要条件，不是充分条件**：它证明不了路径**真的**指向 `tmp_path`；
    真正的兜底是 `backend/data/` 的 sha256 快照（本卡已作为裁判落档）。
15. **锁序结论只在最小读取面内成立**：未证明全仓所有外部调用链都无反序嵌套。
16. **超时还带回了第二条、后果更重的路径：游标复活**（车道自审发现，与 §四.1 是**不同**的因果链）。
    轮转的前置动作 `_invalidate_replay_checkpoint` 作废游标，靠的是「换代与游标失效同生共死」；
    而改前 `_replay_in_flight` 在整次回灌期间恒 True，轮转根本不可能与重放循环重叠 ——
    这条不变量是**靠构造**保证的。超时把这个前提拿掉了：轮转后仍在跑的重放循环会在下一个
    checkpoint 间隔重新 `_save_checkpoint`，把属于**上一代文件**的下标重新绑到新一代活动文件上；
    若进程在 finalize 的 `_clear_checkpoint` 之前退出，重启后整份新一代 `failed_writes.jsonl`
    会被 `if i < checkpoint_idx: continue` **全部跳过**，还因 still_pending 为空而被改名成 `.synced.`。
    写侧挡不住（游标是回灌侧自己写回的），移交 P2-C。
17. **「核行数 → 轮转 → 追加」对进程内三写者原子这条不变量零并发覆盖**：23 条门全是单线程的，
    没有任何并发门证明那把 `failed_writes_lock` 真的护住了这一段。
18. **`DeadLetterStore.store` 现在每写一条先全文件扫一遍**（`count_lines`），同步 IO 跑在事件循环上
    且持 `_dead_letter_io_lock`。死信量大时这是按文件大小线性增长的新开销，本卡**未做增量计数优化**。
19. **`ensure_line_boundary` 的三态划分未穷举**：只覆盖「空 / 以 `\n` 结尾 / 半行 / 不存在 / 探测失败 /
    补换行失败」六种；未证明没有别的组合（如目录被替换成文件、文件在两次 open 之间被换掉）。

---

## 五 台账待登记条目（≥4）

1. **第三写者切 helper**：结构判据 0→1 成对存档；新门 19 条 nodeid 见 §二 (b)(g)。
2. **守卫超时语义**：三态 + 新 env `CLS_REPLAY_WINDOW_MAX_SECONDS`（默认 **1800**）。
   **⛔「超时后 finalize 误判面」移交 P2-C CARD-REPLAY-REWRITE**，Codex 三轮均判它是
   **本卡引入的安全退化**（不是旧账）。P2-C 卡文须引用本条与 `_replay_in_flight` 的 docstring。
   已登记的三条候选修法：① 让 finalize 变成 generation-aware；
   ② 让超时路径把新条目写进**旁路文件**而不缩短活动文件；
   ③ **Codex r2 提出的替代方案**：超时后只 `logger.error` 告警但**仍返回 True**（不放行轮转），
   把「恢复上限」整体推迟到 P2-C —— 代价是继续接受越限。
   ⚠️ ③ 与卡文 §一(d)「超时分支返回 False（允许轮转）」的规格**相反**，属改变卡的决定，
   **车道不自判，交主 session / 用户裁定**。
3. **`ruff format --check` 与地盘门的冲突待裁**：手册 §零.3 判「硬禁」，但被拦的 5 个文件是
   B15_BASE 既有 dirty，整文件 format 会越出卡文 (l) 白名单（`agent_service.py` 一个文件 497 行）
   并与 D-40 撞车。本卡用 `LEFTHOOK_EXCLUDE=python-lint` + 「改动行零漂移」逐行证明 +
   「dirty 集 ⊆ 基线 dirty 集」，与 P2-A 同口径。**请主 session 裁定第十五批的统一口径。**
4. **`Path.exists()` 注入点更正**（建议进工程坑索引）：Python 3.14 的 `Path.exists()` 走
   `os.path.exists` → `os.stat`，**不经过 `Path.stat`** ⇒ 打 `type(path).stat` 对 `exists()` 类门无效
   （本卡首跑因此误绿一条）。T6-C 里打 `type(path).stat` 的那条门**不受影响**。
5. **卡文 `-k record_failed_write` 欠选**：实测只选中 1 条（卡文预期 ≥3），正确表达式是
   `-k failed_write`（3 条）。建议回写卡文模板。
6. **e3（outbox 有界）退回第十六批**：Codex r1 HIGH 实测「上限为 1 时，`recover_outbox` 读出 A →
   `await publish(A)` 期间写入 B → 轮转 → 读取器看不到新文件里的 B → 最终以 A 覆盖 B」，
   即**轮转与 `recover_outbox` 的读-改-写窗口互撞**；修它必须动 `recover_outbox`（P2-C / G4-6 地盘）。
   卡文 e3 本就是「可退子项」，故整段退回，`event_bus.py` 逐字节同 PREV。
   ⇒ `events.overflow.*` 代际问题**不存在**（没有轮转），outbox 仍无界，第十六批处理。
7. **`_flush_pending_failed_writes` 失败语义变更 + 越出 prose 地盘**（Codex r1 HIGH-2 起）：
   `finally: clear()` → OSError 保留重试 / TypeError·ValueError 逐条丢弃 / 成功只删本批。
   该 hunk 越出卡文 prose 的「docstring only」（仍在自动判据区间 `[2672,2900]` 内），请主 session 裁定。
8. **`tests/unit` 写脏现网 `backend/data/` 的第五个写者**：**`tests/unit/test_event_bus.py`**
   → `backend/data/outbox/events.jsonl`（本卡定向实测）。P2-A 验收单 §三 已登记另外 4 个
   （`test_canvas_edge_bulk_sync.py` / `test_canvas_edge_sync.py` / `test_agent_memory_trigger.py`
   / `test_story_30_22_agent_trigger_deep.py`）。建议 patch 目标串
   `app.services.event_bus.OUTBOX_FILE` + `OUTBOX_DIR`。**地盘外，只登记不改。**
9. **`git status` 不能当「现网只读」的兜底**：`backend/data/.gitignore` 的 `*.jsonl` 让它恒空。
   本卡改用 `backend/data/` 逐文件 sha256 跑前/跑后快照，建议写进协议 §2.2 的落盘判据模板。
10. **墙钟上限类测试在并发车道下会假红**：`tests/unit/test_deploy_vault_sh.py` 的 5 条
    `preflight_npm_build_*` 在 `load≈15` 时整批红（5 秒墙钟上限打死假 npm），负载回落后单跑
    `5 passed in 14.91s`。建议排批时把这类测试与其它车道的长跑错开，或给它们更宽的上限。
11. **`canvas_events_fallback.json` 截断改轮转** + **`neo4j_memory.json` 有界语义** → 第十六批候选。
12. **`failed_dual_writes.jsonl` 链退役或接线待产品裁定**（T6-A 链6：`write_dead_letter(` 零调用方）。
13. **`DeadLetterStore.count()` 零调用方** + 本卡把它改成 `count_lines` 口径 ⇒ 是否退役归 G-PIPE 清单。
14. **Codex 各轮**存档路径、绑定 SHA、B/H/M/L 计数：见 §六。
15. **P2-A 之后的行号漂移表**（§一）：`failure_counters` `.exists()` +11、`episode_worker` `.exists()` +5、
    `DeadLetterStore` +1/+5；其余卡文行号实测一致。
16. **⛔ 游标复活（P2-C 必修）**：见 §四.16。P2-C 的 generation-aware finalize 必须**同时**解决
    「finalize 覆盖窗口内新条目」与「重放循环把旧代下标写回新代文件」两条路径 ——
    只修前者，重启后整份新文件仍会被跳过并错标 `.synced.`。
17. **既有常驻门会被生产侧的 import 形式改名架空**（车道自审发现，建议进工程坑索引）：
    t6c 的两条门靠拦 `builtins.__import__` 的 `name == "app.services.fallback_sync_service"` 工作；
    生产侧一旦改成 `from app.services import fallback_sync_service`，`name` 变成 `"app.services"`，
    拦截失效而门**照样绿**（绿在「锁本来就没被占」这条完全不同的判据上）。
    本卡已改回点分形式并新增一条**在真持锁前提下**验的鉴别门。
18. **`DeadLetterStore.count()` 每写一条全文件扫描的代价**（§四.18）：是否做增量计数，登记待裁。
19. **Codex 各轮共同的证据面偏差**：四轮都报「裁定书 `2026-09-15-第十四批复核裁定与待裁决登记.md`
    在此 checkout 只有 111 行，核不到所指 `:158/:186`」—— 那两个行号来自卡文 §四，与本 worktree 的
    实际文件不符，**建议下批排批时校正该引用**。
20. **补审 r6（ZCode × GLM-5.3，协议 §2.4.2）结果**：B 0 / **H 1** / M 0 / L 3 ⇒ 未达 B/H=0。
    H-1 = 死信链 `DeadLetterStore.store`（`episode_worker.py:276`）缺行边界防护（同类「半行粘连」缺陷漏到第四个写者；
    死信无重试缓冲 = 该条静默丢失）；L-1 = `_isolation_offenders` 证据面过宽（`test_staging_writers_bounded.py:1018`）；
    L-2 = `REPLAY_WINDOW_MAX_SECONDS` 下限 1 秒可把已登记的缝常态化（`failed_writes_constants.py:43`）；
    L-3 = 「模块内禁裸 `.exists()`」常驻门未落地（T6-C 台账 21）。
    **建议主 session：先修 H-1（持 `_dead_letter_io_lock` 复用 `ensure_line_boundary` 或把分隔符并进首行）+ 补门，
    再送 `-r7` 绑新 HEAD**；同型残留 `failure_counters.write_dead_letter`（:363-366，T6-C 面）一并议。
    存档 `zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md`。

---

## 六 Codex 复核

四轮均：模型 `gpt-6-astra` · `reasoning_effort: ultra` · `codex-cli 0.153.3`；首部三字段齐，
会话头三行抄自 `.stderr` 并括注行号（`.stderr` **未入库**，`git show --name-only HEAD | grep -c stderr` → 0）；
每份存档 `wc -c` > 0；旧复核模型名计数 **0**。

| 轮 | 绑定 SHA | B / H / M / L | 存档 |
|---|---|---|---|
| r1 | `2a921e77` | 0 / **3** / 3 / 1 | `codex-review-…-r1.md` |
| r2 | `3fb1557e` | 0 / **2** / 3 / 0 | `codex-review-…-r2.md` |
| r3 | `5bb52629` | 0 / **2** / 3 / 0 | `codex-review-…-r3.md` |
| r4 | `732d2a96` | 0 / **2** / 3 / 1 | `codex-review-…-r4.md` |
| r5 | — | **未跑成**（配额） | 见下方 ⛔ |

### ⛔ r5 未跑成 —— 末轮未绑定最终 HEAD，按协议交主 session 人审

r4 之后按其 MEDIUM/LOW 又改了代码（见下表最后三行），因此**必须再送一轮**。
r5 连发两次，两次都返回 **0 字节**，`.stderr` 均为：

```
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
or try again at Sep 23rd, 2026 11:05 AM.
```

按协议 §四「0 字节存档重发一次，再 0 字节 → 主 session 人审替代，且 0 字节文件不入 commit」：
两份 0 字节 `.md` **未入库**（`.stderr` 被 `.gitignore` 覆盖，本来就不入库）。

**⇒ 本卡的末轮 Codex 没有绑定最终 HEAD `80295391`，按 D-15 不构成「通过」。**
车道**不自判通过**，整卡交主 session 人审裁定。可替代的证据：

1. r4 已绑定 `732d2a96`，B/H/M/L = 0 / 2 / 3 / 1；两条 HIGH 都是**同一条**已升交裁定的
   超时取舍（见 §五.2 / §五.16），其余 MEDIUM/LOW 在 r5 前已逐条修完并各配了负控。
2. r4 → 末态的代码差只有三处（`ensure_line_boundary` 返回值语义再收窄一次 + 真轮转后清 `sep`
   + 三条新门），每处都有**专属负控段**（⑪⑫ 与时间戳鉴别门），失败正文即缺陷产物。
3. 车道另跑了一轮**五视角对抗自审**（见下），它发现的问题比 r4 更深（含一条我 r4 修复
   自己引入的回归），全部已修并补门。

⚠️ 工程坑提醒（已有先例）：Codex 报的「重置时间」是**一次观测，不是不变量** ——
第十四批曾报「6 天后重置」而 24 分钟后即恢复。主 session 接手时**先复测一次**，
不要直接继承「9/23 才能跑」这个结论。

> ⏩ **后记（2026-09-19 补审收工）**：补审（ZCode × GLM-5.3 round-6，绑终态 `d2ebf694`）已完成 —— 结果 **B 0 / H 1** / M 0 / L 3，**仍未达 B/H=0**；车道零代码改动，处置建议见**文末补审节**（先修 H-1 + 补门，再送 `-r7` 绑新 HEAD）。

### 逐条处置

| 轮 | 级别 | 位置 | 结论 | 处置 |
|---|---|---|---|---|
| r1 | HIGH | `event_bus.py:378` | 轮转与 `recover_outbox` 的读-改-写窗口互撞，会覆盖未恢复条目 | **已退 e3 整段**（卡文「可退子项」），`event_bus.py` 逐字节同 PREV |
| r1 | HIGH | `memory_service.py:1437` | 即时刷盘提前触发既有的失败后无条件 `clear()`，瞬时 IO 故障 = 永久丢记录 | **已修**：OSError 保留重试 / 序列化失败丢弃 / 成功只删本批；+2 门 +负控④ |
| r1 | MEDIUM ×3 / LOW ×1 | 文案过强 / 同步 IO / AST 门漏类方法 / `"-00"` 误匹配 UTC 零点 | — | 文案已收紧；同步 IO 如实登记；AST 门扩到类方法；`-00` 改按序号后缀精确匹配 |
| r2 | HIGH | `memory_service.py:2927` | 半行写入失败后重试会**粘成一行**，重试记录被吞、pending 仍被删 | **已修**：新增 `ensure_line_boundary`；+1 门 +负控⑤ |
| r2 | MEDIUM | 混合批次一条坏就整批丢 | — | **已修**：逐条序列化；+1 门 +负控⑥ |
| r2 | MEDIUM ×2 | 「至多失效 N 秒」未清干净 / AST 门漏嵌套类 + 「空 git status 是兜底」失实 | — | 文案逐条收紧；扫描改**递归**；兜底改 sha256 快照并作为裁判落档 |
| r3 | HIGH | `memory_service.py:2922` | `ensure_line_boundary` **返回值被忽略**；另两个写者未接边界修复 | **已修**：返回 False 则不写不清 pending；边界修复上移到三写者共用入口 `append_failed_writes_bounded`；+2 门 +负控⑤⑦ |
| r3 | MEDIUM | `memory_service.py:2926` | 捕获收窄成 `OSError` 后，`UnicodeEncodeError`（属 `ValueError`）会逃出去改变返回语义 | **已修**：序列化阶段 `line.encode("utf-8")` 预验 + 写侧 `except ValueError` 纵深；+1 门 +负控⑧ |
| r3 | MEDIUM ×2 | 同步 IO 未解决 / 验收单严重落后于所述 round-3 更新 | — | 同步 IO 如实登记；**验收单已整体重写**（即本文件） |
| r4 | MEDIUM | `failed_writes_constants.py:332` | 「探测失败 + 实际半行 + 追加成功」仍粘连（PREV 也有，属修复遗漏） | **已修**：返回值语义收窄成「知不知道」，探测失败 ⇒ False ⇒ 加分隔符但**照常写**；+1 门 +负控⑪ |
| r4 | MEDIUM | `test_…py:337` | 时间戳门证不了「赋值在取锁之后」 | **已修**：新增「先占锁、再启动调用、断言等锁期间戳不变」的鉴别门 |
| r4 | MEDIUM | 验收单 `:469` | 4-B 承诺过强 + 提交内登记落后于代码 | **已修**：4-B 改成有条件表述并写明「还没做完的」；§四/§五 补齐并随本 commit 提交 |
| r4 | LOW | `failed_writes_constants.py:435` | 补换行失败后若成功轮转，遗留 `sep` 往新空文件多写一行 | **已修**：真轮转后清 `sep`；+1 门 +负控⑫ |
| r4 | 更正 | `test_…py` 注释 | 我写「换 `time.time()` ⇒ 恒判超时」方向反了（实为巨大**负数** ⇒ **恒不超时**） | **已改**；断言本身不变 |
| r1–r3 | HIGH（同一条，三轮重复） | `failed_writes_constants` 超时分支 | 超时放行轮转会破坏正在进行的健康慢回灌 —— **本卡引入的安全退化** | **未修，车道不自判通过**：卡文 §一(d) 明确规定该分支「返回 False（允许轮转）」，Codex 的替代方案与卡的规格相反，属**改变卡的决定**，按协议交主 session / 用户裁定。登记见 §四.1 与 §五.2（含三条候选修法） |

### 车道自审（workflow，5 视角对抗复核 + 逐条验伪）

除 Codex 外，另跑了一轮车道内多视角对抗复核（正确性 / 并发与锁 / 门的有效性 / 契约与调用方 / 文档诚实性
五个独立视角各自找问题，再对每条发现派一个**以反驳为默认立场**的验伪 agent）。结果见 §六末。

---

## 七 DoD-3 段 4-B：用户侧（零技术词）

> 系统连不上它的记忆库的时候，会把学习记录先攒在电脑本地。以前这些攒下来的东西有三个毛病：
> 一是某几条路攒进来的会一直堆下去，堆到把硬盘塞满都不会停；
> 二是如果程序被强制退出，攒在内存里那一批就整批没了；
> 三是万一存到一半电脑出岔子，下一条记录会跟没写完的那半条黏在一起，两条都读不出来。
> 这一轮把前面两条路和第三个毛病都处理了：这几条路攒进来的不会再把文件写到撑爆；
> 平时被强退也不会整批不见（记录写完就落到盘上了）；黏在一起这件事现在不会再发生。
> 存的那一下要是正好出岔子，这批记录会留着等下次再存，而不是当场消失。
>
> 还没做完的，我也知道：还有一条路（另一个攒东西的文件）这次没动，留到下一批；
> 而且要是硬盘一直写不进去、期间又被强退，那批还在内存里的记录仍然会没。
> 但比起以前，我心里有底多了。

**felt-sense**：以前看到「已保存到本地」这句提示，心里其实是悬的 —— 不知道它到底落没落地、会不会越堆越多。
现在这句提示读起来是踏实的：东西真的在盘上，有人管着它别长疯，存不下的时候也会再等一等 ——
剩下没做完的那部分，也明明白白写着，不用我自己猜。


---

## 补审（GLM-5.3 × ZCode，协议 §2.4.2）

> **批次 / 通道**：BATCH-2026-09-18-第十五批 补审（D-43 附款「补审用 zcode」）。轮次 **round-6**
> （接既有 Codex r1–r5 与 r5 两次 0 字节失败档）。⛔ 本通道**非 Codex**；结论转述**不得**简写成
> 「Codex 通过 / 审查通过」。

### 绑定与自证

| 项 | 值 |
|---|---|
| 审查绑定 | `d2ebf694`（= 本卡末次改动 commit = 送审时 HEAD = 现 HEAD；`git --no-pager diff --stat --no-color d2ebf694 HEAD -- <7 文件>` = 空 ⇒ 绑定成立；原文 `evidence-staging-writers-bounded/zcode-r6-binding-*.txt`） |
| 模型 | `glm-5.3`（`provider_config.defaultModelSelection` = `zai-coding-plan` / `glm-5.3` + `max`） |
| 工具 | `zcode-app-cli 3.12.3-26 / runtime 0.16.5`（`--mode build` = 只读：Bash / Write 被阻断） |
| 命令 | `zcode --prompt "$(cat _bmad-output/审查/prompts/zcode-review-prompt-CARD-STAGING-WRITERS-BOUNDED-r6.md)" --cwd "$(pwd)" --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md 2> _bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.stderr`（rc=0；2026-09-19 21:04:46 → 21:17:46） |
| 自证（`--json` 原文抄） | `sessionId=sess_494e656e-ca27-4ead-b1ff-26e3409d5b77` · `traceId=3d199322-770a-4bf5-8b4f-3e1326a68a91`（另 `turnId=turn_4cefa4b2-2eb9-4b0e-8fdb-de2f1d421fcb`；usage 5 请求 / 539,440 tokens；JSON 解析通过、非空） |
| 存档 | `_bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md`（首部五字段 + 评审正文 + 原始 --json）；`.stderr` 不入库；留痕 `evidence-staging-writers-bounded/zcode-r6-{minute0,prompt-check,binding,session,findings,archive-finalize}-*.txt` |

送审阅读面（build 模式无 Bash ⇒ git 输出内嵌）：7 文件变更集全量 diff `ac0993b4..d2ebf694`（1,759 行）内嵌为 prompt 附录 A；
prompt = `_bmad-output/审查/prompts/zcode-review-prompt-CARD-STAGING-WRITERS-BOUNDED-r6.md`（1,846 行 / 109,596 字节，sha256 `40dedc496cddc46eed190da526af47799fedb51b7d4b4e95d38418acc5a0b126`；五分节自卡文 §一(n)/§四 转写，两处按终态更正：e3 已整段退回、exists 门注入点已由 `type(path).stat` 更正为 `os.stat`/`os.scandir`）。

### 裁定：**BLOCKER 0 / HIGH 1** / MEDIUM 0 / LOW 3 ⇒ 未达「B/H = 0」

- **② 作者自述 6/6 成立**；其中第 4 条「实质成立、措辞过宽」（「回灌侧零改动」应表述为「回灌**算法本体**一行未改」—— 打戳/清零在变更集内，已核 `:142-194` / `:302-456`）。
- **③ ⓪–⑤ 逐项通过**：⓪ 超时双路径（finalize 误判 / 游标复活）已如实登记移交 P2-C、无过强声称；① 同步 IO 新面如实登记、返回语义未变；② 锁序无反序嵌套；③ exists 门注入点命中、失配时响亮红；④ env 全走 `bound_from_env`、导入期不崩；⑤ 0 条新增 pyright ignore（仅沿用 1 条 `# noqa: BLE001`）。
- **HIGH 1 为唯一阻断级**：本卡新收口的死信链 `DeadLetterStore.store` 只加轮转、未加行边界防护（同类「半行粘连」缺陷漏到第四个写者），死信无重试缓冲 ⇒ 该条**静默丢失** ⇒ **主 session 裁定项**。

### 分级问题（逐字；仅标题降一级，正文未动）

**HIGH**

1. `backend/app/services/episode_worker.py:276` — `DeadLetterStore.store` 在 `_dead_letter_io_lock` 下仍裸 `f.write(json.dumps(record) + "\n")`，无 `ensure_line_boundary` 等价防护：上次 store 在 ENOSPC/EIO 下写半行后，下一条死信直接粘在残缺尾巴后成不可解析行，且死信无重试缓冲 = 该条**静默丢失**（与本卡 `append_failed_writes_bounded` 入口修的是同一缺陷类，`test_third_writer_does_not_concatenate_onto_dangling_tail` 的论证逐字适用于它）；负控输入：向死信文件预置 `b'{"epi'` 半行尾巴后再 `store(task, err)` 一条，断言新记录自成可解析行——现实现会粘尾；对照输入：同一输入走 failed_writes 链会先补换行；这是**门未覆盖的路径**（新门 26 条无一条盖死信链粘连）。修复面在本卡内：持 `_dead_letter_io_lock` 复用 `ensure_line_boundary` 或把分隔符并进首行。同型残留顺带指出：`failure_counters.write_dead_letter`（:363-366，T6-C 面、本卡未动）也无边界防护，建议一并修。

**LOW**

1. `backend/tests/unit/test_staging_writers_bounded.py:1018（_isolation_offenders）` — `evidence = literals | identifiers | args` 把 docstring/注释里的字符串字面量计入隔离证据；负控输入：`def test_x(service):` + docstring 含 "bounded_memory_writes" 字样 + 直接调 `service._record_structured_outbox(...)`（未真正隔离）→ 门放行（**未被拦下的输入**）。门自身 docstring 已登记「必要不充分」且有 sha256 快照兜底，且 T6-C 台账 22 已登记同型弱点，故仅 LOW。
2. `backend/app/core/failed_writes_constants.py:43` — `REPLAY_WINDOW_MAX_SECONDS` 的 `minimum=1` 允许把窗口上限调到 1 秒；负控输入：`CLS_REPLAY_WINDOW_MAX_SECONDS=1` 时任何超过 1 秒的**健康**回灌都会触发 [C2-01] 并放行轮转，把已登记移交 P2-C 的丢记录缝从「1800 秒才开」放大到「常态化开着」。缝隙本身已登记、默认值安全，建议抬高下限或显著警示，故 LOW。
3. `_bmad-output/验收单/UAT-CARD-NEO4J-REPLAY-BOUND-2026-09-15.md:255（台账 21）` — T6-C 建议的「这几个模块禁止裸用 `.exists()`」常驻门未随本卡落地：残余 3 处已按卡文修掉，但这些模块内**再引入**裸 `exists()` 无门拦截（**门未覆盖的路径**）；回灌侧 9 处与 `recover_outbox` 1 处按卡文归下一张卡，不在此列。

### 计数

`BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 3`

### 与卡文 (n) 的关系（措辞硬约束）

本补审 = **绑最终态 `d2ebf694` 的一轮复核**（协议 §2.4.2 / D-43 附款，**非 Codex**），结果 **B 0 / H 1** ⇒ **未达**「绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」。
按补审硬边界「报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session」：车道**零代码改动**；本卡**仍未通过**，处置由主 session 裁定（建议：先修 H-1 + 补门，再送 `-r7` 绑新 HEAD；3 条 LOW 按协议 §1 登记不阻断）。

### word-scan 留档（诚实登记）

协议 §2 四个禁用措辞：prompt **撰写段（1–84 行）0/0/0/0**；prompt 全文「构造」=1（第 214 行，∈ 附录 A diff 段 = 被引 git 原文）；评审 response 全文 **0/0/0/0**。证据：`zcode-r6-prompt-check-*.txt`、`zcode-r6-findings-*.txt`。

### ⛔ 终态字段重算（收工）

- 头部「SHA 变迁」更正：`80295391（末态，r5 审）` → `80295391（r4 后；r5 送审两次 0 字节）→ d2ebf694（末态；2026-09-19 amend，含 r5 失败档与本文更新；补审 r6 绑）`（原「r5 审」表述不实 —— r5 从未审完）。
- 头部新增「补审（协议 §2.4.2）」行：B 0 / H 1 / M 0 / L 3 与存档指针。
- §六 新增「后记」：补审结果与「仍未达 B/H=0」现状 → 指向本节；Codex 轮次口径不变（r5 未跑成）。
- §五 新增第 20 条（补审结果 + H-1 处置建议 + 3 条 LOW 登记）。
- evidence 计数：`ls _bmad-output/审查/evidence-staging-writers-bounded | wc -l` 收工实测 **122**（补审前 116；新增 6 份 `zcode-r6-*` 留痕）。
- 本卡**单 commit 数不变**（`d2ebf694` = 本卡唯一代码 commit；本轮补审只增文档，零代码改动）。

### 本补审未证明什么

1. **未证明 zcode 通道复核的覆盖面与 Codex 等价**（读取面 / 提示词 / 失败模式皆不同，无对照实验）。
2. **未证明 HIGH-1 无害**：它是一条**可触达**的数据丢失路径（死信无重试缓冲），未修即未通过；3 条 LOW 亦未处置。
3. 复核者依赖树内 Read + 内嵌 diff 完成判断；**未独立复跑 git diff**（通道限制；其自证面 = `--json` sessionId 非空）。
4. **未证明修复面之外已无事可做**：H-1 的修复面（`ensure_line_boundary` 复用 / 分隔符并入首行）与同型残留（`failure_counters.write_dead_letter`）均未动，等待主 session 裁定。


---

## H1 整改（2026-09-20 · 主 session 裁「整改」）

> **来源**：zcode 补审 r6 HIGH（`zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md`）——
> `DeadLetterStore.store` 在 `_dead_letter_io_lock` 下裸追加、无行边界防护（半行尾巴吞掉
> 无重试缓冲写者 ⇒ 静默丢失）；同型残留 `failure_counters.write_dead_letter`。
> **主 session 裁定：整改**（本轮修复 + Codex r7 复核）。

### 修复（commit `4621946f`，3 文件 +99/−2）

- `episode_worker.DeadLetterStore.store`：持 `_dead_letter_io_lock` 复用 `ensure_line_boundary`；
  **先轮转、后探边界**；False（不能确定）⇒ `sep="\n"` 并进本条第一行（不拒写）；局部 import 收 diff 于段内。
- `failure_counters.write_dead_letter`：同型残留一并修（惰性 import 破 `failed_writes_constants` 反向依赖环）。
- 测试 3 条（`test_staging_writers_bounded.py`）：两负控（预置 `b'{"epi'` 半行尾巴 ⇒ 尾巴原样保留 +
  新记录自成可解析行）+ 一对照（同输入走 failed_writes 链先补换行）；文件本地隔离扫描器过。

### 证据（`evidence-staging-writers-bounded/`）

| 判据 | 结果 | 存档 |
|---|---|---|
| 先红演示（还原旧裸写） | 两负控 **FAILED**、对照 **PASSED**；还原后 sha 逐字同 | `h1fix-red-demo-*` |
| staging 全文件 | **29 passed**（26+3） | `h1fix-green-*` |
| 点名套件 | **189 passed / 3 skipped** | `h1fix-named-*` |
| unit 目录级 | **32F / 5778P**（+3），对基线 diff 只 `<`，W4 `blocked=0` | `h1fix-unit-close-*` |
| pyright 成对 | open `0 errors, 82 warnings` / close 同 | `h1fix-pyright-open/close-*` |
| jev 分诊 | 3/3 REVIEW（episode_worker 2.81 / failure_counters 2.33 / test 1.75） | `jev-triage-4621946f.json` |

### Codex r7（绑 `4621946f`，首部 §2.4 齐）

**裁决：生产语义 PASS —— B 0 / H 0 / M 0 / L 3**；「r6 HIGH 的两处死信裸追加问题已在进程内写者语义上修复」；
「H1 生产整改成立；可收口」。LOW×3（均为测试/门收口缺口，**登记为后续小补丁**）：

1. store 新负控未覆盖 `ensure_line_boundary` 返回 False ⇒ `sep="\n"` 的调用方分支（LOW）；
2. write_dead_letter 新负控同样未覆盖 False 分支（LOW）；
3. 文件本地 AST 隔离门的 `_DEAD_LETTER_CHAIN` 不识别 `fc.write_dead_letter`（LOW）。

### ⛔ 终态字段重算（收工）

- 头部「SHA 变迁」延展：`… → d2ebf694（补审 r6 绑）→ 4621946f（H1 整改；r7 绑；最终代码 HEAD）`；新增「H1 整改」行。
- 本卡代码 commit 数：+1（`4621946f`；本卡历史 = d2ebf694 单 squash + 本整改 commit）。
- 轮次：Codex +1（r7 绑 4621946f）；zcode 补审仍 1（r6）。
- evidence：新增 **9 份**（`h1fix-*` × 8 + `jev-triage-4621946f.json`）；目录计数 132。
- 台账：新增 LOW×3 登记（后续小补丁：补两条 False 分支负控 + 扫描器链集加 `write_dead_letter`）。

### 本整改未证明什么

1. 未证明「探测失败 ⇒ 多写前导空行」在死信链计数侧的提前轮转副作用（`count_lines` 按 `b"\n"` 计数）——
   方向保守（提前轮转 > 粘连/拒写），未量化；
2. 未证明跨进程（多 worker）下「轮转与追加」非原子的既有边界（原实现已明示，本修复未扩大）；
3. LOW×3 未修（登记为后续小补丁）；
4. 未在真库环境复跑（本修复零连库；7692 门与本修复无交集）。
