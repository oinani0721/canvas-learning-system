# UAT — CARD-EPW-COVERAGE（第十四批 / 车道 card-t10-red / 本车道第 4 张）

> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-EPW-COVERAGE]`
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T10-D.md`（feature 主干树）
> 开工 HEAD（`$PREV`）= `15fddbc1`（T10-C CARD-Y4-D-TAIL 末 commit）
> 证据目录：`_bmad-output/审查/evidence-epw-coverage/`
> 日期：2026-09-15

---

## 〇 一句话结论

给 `GraphitiEpisodeWorker` 新建了 **33 个测试函数**（参数展开后 **47 条**、171 条 assert）的等价覆盖文件，逐条承接
CARD-RED-C1 登记的 37 条缺口里归本卡的 21 条（另 1 条登记退役、15 条归 T10-C）；
`test_story_38_6_scoring_reliability.py` 里指向本卡的 **3 条 xfail 全部去标**（2 条改写对齐真
worker 后 PASS、1 条主题永久删除故删除用例）；全程**未改 `backend/app` 一行**。

---

## 一 第 0 分钟核对（完成条件 (a)）

| 项 | 期望 | 实测 | 结论 |
|---|---|---|---|
| `pwd` | `…/worktrees/card-t10-red` | 同左 | ✅ |
| `git branch --show-current` | `card/t10-red` | 同左 | ✅ |
| `PREV=$(git rev-parse HEAD)` | T10-C 末 commit | `15fddbc1bbaf2c47e8b6c08c216d36e02d110668` | ✅ |
| `git log -1 --format=%s` 含 `CARD-Y4-D-TAIL` | 1 | 1 | ✅ |
| `git status --porcelain \| wc -l` | 0 | 0 | ✅ |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 存在 | 均存在 | ✅ |
| **T10-C 前置①** `grep -c 'pytestmark = pytest.mark.skip' test_graphiti_json_dual_write.py` | 0 | **0** | ✅ 已删 |
| **T10-C 前置②** `grep -c '@pytest.mark.skip' test_story_38_6_scoring_reliability.py` | 0 | **0** | ✅ 已删 |
| **基线自证** `grep -vc '^#' $BASE`（feature 主干树绝对路径） | 64 | **64** | ✅ |

**§〇 file:line 现场复核（AST 实测，存档 `epw-ast-anchors-20260915T115429.txt`）**：
`episode_worker.py` 681 行；`EpisodeTask:73` / `can_retry:94-95` / `backoff_seconds:98-102` /
`WorkerMetrics:125` / `to_dict:154` / `_redact:189-196` / `DeadLetterStore:199-274`
（`__init__:224-226`、`_store_full_body_enabled:229-231`、`store:233-268`、`count:270-274`）/
`GraphitiEpisodeWorker:282-658`（`__init__:303-313`、`start:443`、`stop:454`、`enqueue:496`、
`metrics:518`、`is_ready:524`、`_run:530`、`_process_episode:562`、`_handle_failure:635-658`）/
`get_episode_worker:668-673` / `cleanup_episode_worker:676-681`——**与卡文逐条一致，零漂移**。
默认死信路径 `grep -nF 'data/dead_letter_episodes.jsonl'` → `:207`(docstring) / `:224` / `:306`，与卡文一致。

**xfail 口径复核**：`grep -rn 'CARD-EPW-COVERAGE' backend/tests/` = **4 行**（卡文口径更正 1 成立，
设计稿「5 条」不成立）：`test_qa_38_4_dual_write_extra.py:57` ×1（**不在 T10 地盘**，移交）+
`test_story_38_6_scoring_reliability.py:44/:57/:84` ×3（在地盘，本卡处置）。

**卡文预测与实测的一处偏差（如实登记）**：卡文 §二.11 预测「38_6 非 strict 门 = PASS **+1 ADVISORY**」，
实测 **PASS + 0 ADVISORY**。原因：T10-C 的重写在 `ready_worker` fixture 里加了
`monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: w)`，源码里出现了
patch 目标串，启发式因此不再告警。卡文那个数字测于 B14_BASE（T10-C 之前）。

---

## 二 交付物

| # | 文件 | 性质 | 说明 |
|---|---|---|---|
| 1 | `backend/tests/unit/test_episode_worker_coverage_epw.py` | **新增**（地盘） | **33 个测试函数 / 参数展开后 47 条 / 171 条 assert**，A–I 九组（r1 定稿 31 个 → Codex r1 HIGH-1 加 1 → Codex r2 LOW-1 加 1） |
| 2 | `backend/tests/unit/test_story_38_6_scoring_reliability.py` | **修改**（地盘） | 去标 3 条 xfail（2 改写 + 1 删除）+ 加 `EpisodeTask` import + 类 docstring 记录决策 |
| 3 | `_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md` | 证据 | 37 行覆盖矩阵 + 附录 A（三条 xfail 决策）+ 附录 B（新文件用例清单） |
| 4 | `_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py` | 门 | 死信路径三入口 AST 门（逐 Call） |
| 5 | `_bmad-output/审查/evidence-epw-coverage/coverage_matrix_check.py` | 门 | 矩阵自校门（37 行 + 集合对齐 + 四类计数 + 自述一致） |
| 6 | `_bmad-output/审查/evidence-epw-coverage/epw_negctl.py` | 门 | 负控驱动（18 条对照输入 + 逐条还原 + shasum） |
| 7 | `_bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md` | 证据 | Codex 五分节 prompt |

⛔ **`backend/app` 零改动**（地盘门证据见 §四.5）。

---

## 三 三条 xfail 的去标决策（完成条件 (e)）

| 原用例 | 决策 | 依据 | 改后状态 |
|---|---|---|---|
| `TestAC1TimeoutRetryAlignment::test_inner_per_attempt_timeout_increased` | **B（删除）** | 现 worker 对 `add_episode` **无任何超时包装**：`_process_episode:613` 直接 `await`；全文件 `asyncio.wait_for` 只在 `:366`（连通性探针）与 `:480`（`stop()` 排空）。per-attempt timeout 语义**无等价**，不伪造 | nodeid 从收集面消失（`--collect-only` grep = **0**） |
| `TestAC1TimeoutRetryAlignment::test_retry_backoff_base_is_1_second` | **A（改写）** | 旧「base=1.0s」的等价不变量 = `EpisodeTask.backoff_seconds` 在 `retry_count=0` 时的区间 `[0, 1]`；patch `random.uniform` 捕获实参做确定性断言 | **PASSED** |
| `TestAC1TimeoutRetryAlignment::test_backoff_progression` | **A（改写）** | 旧「1s/2s/4s 定值序列」的等价不变量 = 上界序列 `[1, 2, 4]`，并新增钉 60s 封顶 | **PASSED** |

- 改前：`1 failed, 14 passed, **3 xfailed**`（存档 `epw-38_6-baseline-20260915T115602.txt`，`-rx` 可见三条 XFAIL 的 reason 含本卡 ID）
- 改后：`1 failed, **16 passed**`（存档 `epw-38_6-after-20260915T120414.txt`）——3 xfail → 2 PASS + 1 删除，`14+2=16` 自洽
- 那 1 条 failed = `TestAC4MergedView::test_get_learning_history_merges_failed_scores`，**在 64 条红基线里**（`$BASE:59`），非本卡引入、非本卡处置面
- `grep -c 'CARD-EPW-COVERAGE' tests/unit/test_story_38_6_scoring_reliability.py` = **0** ✅

---

## 四 段 4-A：Claude 代验的技术 assert

### 4-A.1 新文件单跑全绿（核心裁判 1）

```
tests/unit/test_episode_worker_coverage_epw.py → 47 passed, 10 warnings in 1.37s ; rc=0   # r3 终稿
（r1 定稿 45 passed → r2 整改后 46 → r3 整改后 47；三份存档分别是
 epw-newfile-20260915T120514.txt / epw-r2-rerun-20260915T183704.txt / epw-r3-rerun-*.txt）
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
```
存档：`epw-newfile-20260915T120514.txt`（r1 定稿）/ `epw-r2-rerun-20260915T183704.txt`（r2 定稿）

### 4-A.2 负控验伪锚：18 条对照输入逐条先红后绿（完成条件 (f)）

形态＝**编辑 `$NEW` 自身的断言期望值**（⛔ 不是只在运行时 patch 生产符号——那样文件不变、
`shasum` 判据恒真），还原一律用**跑前 `cp` 副本**（⛔ 不用 `git show HEAD:` —— 负控跑在 commit
之前，HEAD 里没有这个对象）。

| 组（对应完成条件 (c) 的六组） | 声称会红的用例 | 对照输入 | rc | 该用例出现在 FAILED 行 |
|---|---|---|---|---|
| (1) 成功入队→处理 + metrics | `test_metrics_snapshot_covers_all_counters` | `success_rate == 0.2` → `0.9` | 1 | ✅ |
| (2) 退避上界序列 | `test_backoff_upper_bound_series_is_1_2_4` | `[(0,1),(0,2),(0,4)]` → `(0,8)` | 1 | ✅ |
| (2) 退避单调 + 60s 封顶 | `test_backoff_upper_bound_is_monotonic_and_capped_at_60` | `…,32,60]` → `…,32,64]` | 1 | ✅ |
| (3) 重试耗尽→落死信 | `test_all_attempts_timeout_then_dead_letter` | `await_count == 4` → `5` | 1 | ✅ |
| (4) 确定性错跳重试 | `test_deterministic_validation_error_skips_retry_and_dead_letters` | `await_count == 1` → `4` | 1 | ✅ |
| (5) 死信隐私 | `test_dead_letter_omits_full_body_by_default` | `not in record` → `in record` | 1 | ✅ |
| (6) `DeadLetterStore.count` | `test_dead_letter_store_count_matches_appended_lines` | `count() == 1` → `2` | 1 | ✅ |
| (6) `_redact` | `test_redact_scrubs_known_secret_patterns` | `in scrubbed` → `not in scrubbed` | 1 | ✅ |
| **r2 新增** (2′) 实际重试用了该公式 | `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` | `slept_with == [2,4,8]` → `[2,4,9]` | 1 | ✅ |
| **r2 新增** (1′) 重试成功也记 info | `test_success_after_one_retry` | `len(processed_infos) == 1` → `== 2` | 1 | ✅ |
| **r2 新增** (I′) 死信落的是原对象 | `test_retry_reuses_same_task_and_preserves_timestamps` | `args[0] is task` → `is not task` | 1 | ✅ |
| **r2 新增** (1″) metrics 的 `queue_depth` 值 | `test_metrics_snapshot_covers_all_counters` | `queue_depth == 0` → `== 1` | 1 | ✅ |
| **r3 新增** (2′a) 抽样区间下界 = 0 | `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` | `uniform_calls == [(0,2),(0,4),(0,8)]` → `[(1,2),…]` | 1 | ✅ |
| **r3 改写** (2′b) sleep 收到的就是抽到的值 | 同上 | `slept_with == [0.5,1.0,2.0]` → `[0.5,1.0,2.5]` | 1 | ✅ |
| **r3 新增** (G-4) warning 逐条编号 | `test_retry_warning_includes_attempt_number_and_error_message` | 三条全 True → 中间改 False | 1 | ✅ |
| **r3 新增** (F-4) `to_dict` 序列化真值 | `test_worker_metrics_to_dict_serializes_nonzero_depth_and_times` | `avg == 1000.0` → `== 999.0` | 1 | ✅ |
| **r4 改写** (2′b) sleep 收到的 = `uniform` 返回值 | `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` | `slept_with == sentinels` → `sentinels[::-1]` | 1 | ✅ |
| **r4 新增** (2′c) 属性不得二次加工返回值 | `test_backoff_upper_bound_is_monotonic_and_capped_at_60` | `returned == bounds` → `[b+1 …]` | 1 | ✅ |

- **共 18 条对照输入**（r1 定稿 8 → r1 整改 +4 = 12 → r2 整改 +3 = 15 → r3 整改 +1 = 16 → r4 整改 +2 = **18**；
  另有两条因断言被改写 / 被 `ruff format` 折行而同步更新了变异串，不计入新增），
  **每条都让声称的那条用例变红**。
  ⚠️ **这个数字我写错过一次**（曾写「17」，实为 16）。终稿口径由驱动脚本 `MUTATIONS` 的
  **AST 实测**与驱动输出里的 `── 负控` 块数**双向核对**得出 = **18**；
  并按 Codex r5 LOW-4 给每条负控的详细红档加了序号，实测 **18 块 ↔ 18 份独立红档**。
- **每份负控存档恰 1 条 `FAILED`**（证明打中的就是声称的那条，不是「某处失败」）；唯一例外
  `test_redact_scrubs_known_secret_patterns` 是 **5 条**——它是 5 参数的参数化用例，5 个参数全红，
  仍然全部是同一个用例函数。
- 还原后整跑 **rc=0**；`shasum -a 256` 跑前 A = 跑后 B **逐字节同** ✅
  （r1 轮 `16fde42f…` / r2 轮 `0de531dc…` / r3 轮 `bcdb4029…` / **终稿轮 `ba3cefc5d24fa6c630961e6c41ea50f5f98fa16ccc255c4156d64ae545855711`**）
- 还原形态：**跑前 `cp` 到 `/tmp` 的副本**回写（⛔ 不用 `git show HEAD:` / `git checkout` / `git stash`）。
- 存档：`epw-negctl-driver-20260915T120610.txt`（r1 轮 8 条）+
  `epw-negctl-driver-r2-20260915T183847.txt`（r2 轮 12 条）+ 每条一份 `epw-negctl-test_*.txt` +
  `epw-negctl-restored-*.txt`

### 4-A.3 覆盖矩阵 37 行 + 四类和 = 37（核心裁判 3）

```
red-align: C1=33 原本绿=4 合计=37
matrix: rows=37
N1(新文件)=21 N2(已有 retry 测试)=0 T10-C=15 N3(退役)=1
EPW-MATRIX-GATE: PASS   (21 + 0 + 15 + 1 = 37)
```

矩阵门**四枚验伪锚全部发火**（存档 `epw-matrix-gate-20260915T121101.txt`）：
A 删一行 → 行数 36 ≠ 37 FAIL；B 换成 red-align 没有的 nodeid → 缺 1 多 1 FAIL；
C 改一行的承接方 → 与统计段自述不符 FAIL；D 改统计段自述数 → 与表内实数不符 FAIL。

> **N2 = 0 的说明**：凡 `test_episode_worker_retry.py` 也触及的行（如 #28），新文件都写了更强的
> 等价断言，故承接方记「新文件」，参照文件的同向用例在「依据」列作交叉引用而不另计承接——
> 一条缺口不重复记账两次。

### 4-A.4 死信路径三入口 AST 门（完成条件 (c) 静态判据）

| 对象 | 命令 | 结果 |
|---|---|---|
| 新文件 | `epw_path_gate.py --strict-ms` | `worker=3 deadletter=5 singleton=0 imports_memory_service=False` → **PASS rc=0** |
| `test_story_38_6…` | `epw_path_gate.py`（非 strict） | `worker=1 deadletter=0 singleton=0 imports_memory_service=True` → **PASS rc=0**（0 ADVISORY） |

**门经两轮加固，共 9 枚验伪锚 + 1 枚反向锚，全部按预期发火**
（存档 `epw-path-gate-probes-20260915T120334.txt` / `epw-path-gate-v2-*.txt` /
`epw-path-gate-v2-rcfix-*.txt` / `epw-path-gate-v3-*.txt`）：

| # | 对照输入 | 期望 | 实测 |
|---|---|---|---|
| ① | 漏传 kwarg + 直调单例（strict） | FAIL rc=1、❌ 2 行 | ✅ |
| ② | import memory_service 无 patch 串（strict） | FAIL rc=1 | ✅ |
| ②b | 同一探针**非** strict | ⚠️ ADVISORY、PASS rc=0 | ✅ |
| ③ | `DeadLetterStore` 位置参数形态 | FAIL rc=1 | ✅ |
| ④ | 真实参照文件 `test_episode_worker_retry.py` | PASS rc=0 | ✅ |
| ⑤ | kwarg 在场但值 = 写死的真坟场路径（r1 M-4） | FAIL rc=1 | ✅ |
| ⑥ | `import get_episode_worker as get_w` 后调 `get_w()`（r1 M-4） | FAIL rc=1 | ✅ |
| ⑦ | `str("data/dead_letter_episodes.jsonl")` 包一层（r2 L-2） | FAIL rc=1 | ✅ |
| ⑧ | 从 **`app.services.memory_service`** 转出的别名调单例（r2 L-2） | FAIL rc=1 | ✅ |
| ⑨ | f-string 拼出的危险路径 | FAIL rc=1 | ✅ |
| **反向锚** | `str(tmp / "dead_letter.jsonl")` 正常写法 | **PASS rc=0**（防误杀） | ✅ |

⚠️ **门自己 docstring 里如实列了三条仍未封的路径**：① 值经变量中转时不看取值；
② `memory_service` 启发式只查源码是否**出现** `get_episode_worker` 这个串（注释里的同名串也算）；
③ 不追调用链。**本门是必要条件、不是充分条件**，运行期后置防线是 (i) 的 sentinel，
而 sentinel 又抓不到「建了默认路径 worker 但这次没落死信」——两层各有盲区。

### 4-A.5 地盘门（完成条件 (h) / 核心裁判 5）

`PREV=15fddbc1` → `HEAD=a8e31623`（终稿；本卡共三笔代码 commit：`65a84a91` → `366835b8` → `a8e31623`，后两笔是 Codex r1/r2 整改）

```
git -c core.quotepath=false --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output'
 backend/tests/unit/test_episode_worker_coverage_epw.py    | 949 ++++++++++++++++++++
 backend/tests/unit/test_story_38_6_scoring_reliability.py | 122 ++-
 2 files changed, 1031 insertions(+), 40 deletions(-)
```

- **地盘外文件数 = 0**（清单逐行核，恰好是允许的两份）
- `backend/app/**` = **0**；`test_qa_38_4_dual_write_extra.py` / `test_cache_configuration.py` /
  `test_memory_service_write_retry.py` / `test_failure_observability.py` /
  `test_qa_38_6_scoring_reliability_extra.py` / `test_episode_worker_retry.py` / 任何 `conftest.py` /
  `requirements.txt` **逐个 grep 全 0**；`fsrs_bridge` / `decay_beta` = **0**

**⚠️ 验伪锚第一次失效（已更正并留档）**：初版锚 `git diff --name-only … | grep -c '^_bmad-output/'`
得 **0**，看上去像「exclude 没起作用 / 命令没跑成」，其实是**假阴性**：git 默认把非 ASCII 路径
加引号并转义成八进制（`"_bmad-output/\345\256\241\346\237\245/…"`），行首是 `"`，`^_bmad-output/`
恒不命中。改用 `git -c core.quotepath=false` 后：

| 命令 | `^_bmad-output/` 命中数 | 判读 |
|---|---|---|
| 不带 `':(exclude)_bmad-output'` | **95**（终稿） | exclude 之外确有 95 份证据/存档文件 |
| 带 `':(exclude)_bmad-output'` | **0** | exclude 语法**真的在起作用** ✅ |

并同机实测协议 §1 那条提醒成立：`':!_bmad-output'` 写法 → `fatal: Unimplemented pathspec magic '_'`
（所以判据一律用 `':(exclude)…'`）。另实测 `*.stderr*` **入库数 = 0**。
存档：`epw-territory-20260915T182*.txt` / `epw-territory-fixed-*.txt` / `epw-territory-final-*.txt`。

### 4-A.6 目录级红集 diff 只许 `<`（完成条件 (g) / 核心裁判 4）

命令（承重文件名固定成变量、⛔ 无 glob、⛔ 不用 `wc -l` 当判据）：
`cd backend && pytest -q -p no:cacheprovider -rfE --ignore tests/unit/test_deploy_vault_sh.py tests/unit`

| 时点 | 汇总行 | 红集（`-rfE` 抽 FAILED/ERROR nodeid） |
|---|---|---|
| 开工（改任何文件前） | `34 failed, 5116 passed, 35 skipped, **23 xfailed** … in 390.00s` | **34 条** |
| 收工（r1 定稿） | `34 failed, 5163 passed, 35 skipped, **20 xfailed** … in 530.29s` | **34 条** |
| 收工（r2 整改后） | `34 failed, 5164 passed, 35 skipped, 20 xfailed … in 354.63s` | **34 条** |
| **收工（r3 终稿）** | `34 failed, **5165 passed**, 35 skipped, **20 xfailed** … in 465.39s` | **34 条** |

- **收工红集 vs 64 条红基线**：`<` 行 **30**、`>` 行 **0** ✅（30 行 `<` 是 T10-A/B/C 在本车道已修掉的，
  不是本卡的功劳；本卡不向红集增项）
- **收工红集 vs 开工红集**：`diff` 输出**空**，**本卡 delta = 0** ✅（协议 §5 口径）
- **三次收工跑的红集逐条相同**（`diff` rc=0）⇒ 两轮整改都没动红集 ✅
- **passed 差账**：5116 → 5163（+47 = 新文件 45 + 去标改写转绿 2）→ 5164（+1 = Codex r1 HIGH-1 新增用例）
  → **5165**（+1 = Codex r2 LOW-1 新增用例）✅ 每一笔都对得上
- **xfailed 差 = 20 − 23 = −3** = 本卡去标的三条，**一条不多一条不少** ✅
- **验伪锚**：往收工红集里塞一条基线没有的假 nodeid，`diff` 立刻吐出 `>` 行 ⇒ 该判据会发火 ✅

存档：`epw-unit-open-20260915T115641.txt` / `epw-unit-close-20260915T121044.txt` /
`epw-reddiff-20260915T181944.txt` / `diff-base-vs-close.txt` / `diff-open-vs-close.txt`

**⚠️ 一次作废跑，如实留档**：按 Codex r1 改完代码后重跑收工目录级，那一跑在 **14%** 处被中断
（存档只有 54 行、`rc=1`）。⛔ 若直接按「`grep '^FAILED\|^ERROR'` 抽出 0 条」读，会得到
「红集 0 条、对基线全是 `<`」这种**看起来最漂亮**的结论——而实际上它只是没跑完。
识别手段：**汇总行缺失**（`=+ … in …s =+` 一行都没有）＋ 文件行数与进度百分比对不上。
该存档已改名为 `VOID-epw-unit-close2-20260915T184254-interrupted-at-14pct.txt` 保留，
**不作任何判据依据**；判据用重跑的 `epw-unit-close3-*.txt`（下表）。

### 4-A.6b 去标后的两条改写用例也做了负控（卡文未强制，本卡自加）

| 用例 | 对照输入 | 结果 |
|---|---|---|
| `test_retry_backoff_base_is_1_second` | `seen == [(0,1)]` → `[(0,2)]` | `E assert [(0, 1)] == [(0, 2)]` → 该用例 FAILED ✅ |
| `test_backoff_progression` | `bounds[:3] == [1,2,4]` → `[1,2,5]` | `E assert [1, 2, 4] == [1, 2, 5]` → 该用例 FAILED ✅ |

还原（跑前 `cp` 副本）后 `TestAC1TimeoutRetryAlignment` **4 passed**，`shasum` A == B
`c55451223956de55a088f455f007da5dd3db20cc61057060395946bfc5a27cdb` 逐字节同 ✅
存档：`epw-negctl-386-20260915T182014.txt`。
⇒ 去标不是「把标记删了让它恒绿」，两条改写用例对被测公式是**咬合**的。

### 4-A.7 现网只读 sentinel（完成条件 (i)）

**Stage A（本卡归因面，承重）**：新 sentinel → 只跑本卡三文件
（新文件 + 38_6 + retry 参照）→
`find (backend/data | data | backend/app/data) -maxdepth 1 -type f -newer sentinel` = **0 行** ✅
（存档 `epw-sentinel-stageA-20260915T121009.txt`）

**验伪锚（证门会发火）**：`: > backend/data/.epw-probe.jsonl` → 同一条 find = **1**（且列出该文件）；
`unlink` 后回 **0** ✅。并实测 `git check-ignore -v backend/data/dead_letter_episodes.jsonl` →
`backend/data/.gitignore:5:*.jsonl` 命中 ⇒ **(h) 的 git diff 抓不到对它的 stray write，本门是唯一防线**。

**真死信坟场**：`backend/data/dead_letter_episodes.jsonl` 与树根 `data/dead_letter_episodes.jsonl`
**开工不存在、收工仍不存在**（NEW 车道树刚 `git worktree add`，gitignored 文件未带过来）。
开工坟场清单存档 `epw-graveyard-open-20260915T115422.txt`。

**Stage B（全局 sentinel ≠ 0 的归因，地盘外 → 登记不代修）**：
`backend/data/failed_edge_syncs.jsonl`（11:57:55）与 `backend/data/failed_writes.jsonl`（11:59:26）
比开工 sentinel（11:54:18）新。归因证据（存档 `epw-sentinel-attribution-20260915T120305.txt`）：

1. 两次写入发生在 **开工目录级跑**（11:56:41 起）期间；
2. 本卡新文件的 mtime = **12:01:43**、38_6 去标的 mtime = **12:00:52**，**都晚于**两次写入；
3. 开工跑的存档里 `grep -c 'test_episode_worker_coverage_epw'` = **0**（该文件根本不在那次收集面）；
4. 这两个路径在生产侧是 `Path(__file__).parent.parent.parent / "data" / …` 派生的**绝对**路径
   （`app/core/failed_writes_constants.py:12`、`app/core/failure_counters.py:25`），与 cwd 无关，
   且与死信坟场 `dead_letter_episodes.jsonl` **是不同文件**；
5. 同两文件在开工前就带着 09-14 23:19/23:20 的 mtime（上一张卡跑测试时就在写）。

⇒ **非本卡引入、非本卡地盘**，按卡文 (i) 归因程序**登记移交主 session，不代修、不自判**（§六 条目 ④）。

### 4-A.8 既有套件不回退（完成条件 (j)）

| 时点 | 命令 | 结果 |
|---|---|---|
| 开工 | 目录级跑里 `tests/unit/test_episode_worker_retry.py` | `.....` = **5 passed, 0 failed**（存档 `epw-unit-open-…txt:88`） |
| 收工 | `pytest -q tests/unit/test_episode_worker_retry.py` | **5 passed, rc=0**（存档 `epw-retry-regress-20260915T120514.txt`） |

新文件自带 fixture（`dead_letter_path` / `worker`），不 import 跨 conftest，与参照文件无 fixture 名冲突
（两文件各自定义同名 `worker` fixture 于模块作用域，互不可见）。

### 4-A.9 ruff（核心裁判 6）

- 正例：本卡两份地盘文件 → `All checks passed! rc=0`
- **验伪锚（第一次做错、已更正并留档）**：初次把 F821 探针放 `/tmp` 得 `rc=0` —— **假阴性**：
  仓外目录没有本仓 ruff 配置，命中的是另一套默认规则（存档 `epw-ruff-20260915T121130.txt`）。
  改把探针落在**仓内** `backend/_epw_ruff_probe.py` 后 → `F821 Undefined name … Found 1 error. rc=1` ✅
  （存档 `epw-ruff-20260915T121213.txt`；探针当场 `unlink`，`git status` 不含它）。
- 并落了本仓 `backend/**` 的**完整启用规则表**：`E902 / F631 / F632 / F633 / F634 / F701 / F702 /
  F704 / F706 / F707 / F722 / F821 / F822 / F823` —— 证明 **F401 不在其中**（卡文模板常用的 F401
  验伪锚在本仓恒不触发），F821 在其中。

---

## 五 段 4-B：用户产品体验（⛔ 零技术词）

- **我做 X**：我让系统记一条学习笔记，但这次后台正好连不上记忆库。
  **我看到 Y**：系统没有把这条笔记丢掉，而是隔一小会儿自己重试，前后一共试四次；四次都不成
  才把它收进一个"待处理"的小本子，并且写明它是哪一条、什么时候失败的。
  **我感觉 Z**：踏实——偶尔的网络抽风不会让我白写一条笔记。

- **我做 X**：我在笔记里不小心粘进了一串私密口令，而这条笔记恰好失败了、被收进那个"待处理"小本子。
  **我看到 Y**：小本子里没有留下我的整段原文，那串口令的位置被替换成了一串星号；连系统自己的
  运行记录里也只写了"这是什么类型的失败"，没有把我的口令抄一遍。
  **我感觉 Z**：放心——出问题时留下的痕迹，不会变成我隐私外泄的地方。

- **我做 X**：我一口气连着记了很多条，多到后台一时忙不过来。
  **我看到 Y**：系统当场告诉我这条没收下，而不是假装收下然后悄悄丢掉；忙过去之后新的还能继续记。
  **我感觉 Z**：清楚——我知道哪条没成，可以补，而不是事后才发现少了东西。

- **我做 X**：我等着看这次"给后台补测试"的活到底有没有白做。
  **我看到 Y**：每一条新写的检查都被故意弄错一次，结果它们都当场报警；改回来以后又全部恢复正常。
  **我感觉 Z**：信得过——这些检查是真的在看着，而不是摆在那里好看的。

---

## 六 台账待登记条目（≥4）

1. **设计稿/勘探 A §B.3「5 条 xfail」勘误 → 实测 4 处装饰器**：`grep -rn 'CARD-EPW-COVERAGE' backend/tests/`
   = 4 行 = `test_qa_38_4_dual_write_extra.py:57` ×1 + `test_story_38_6_scoring_reliability.py:44/:57/:84` ×3，
   **仅 3 处在 T10 §3 地盘**。本卡已处置 3 处，`grep` 归 0。
2. **`test_qa_38_4_dual_write_extra.py` 那条 xfail 移交主 session 裁**：不在本卡地盘；且它断言
   `ENABLE_GRAPHITI_JSON_DUAL_WRITE is True`，而 `daa9fd37` 起该字段 `[DEPRECATED] default=False`
   ⇒ 即使去标也只会变红；主题是 config 默认值、非 EpisodeWorker 覆盖。候选归 `CARD-CONFIG-CLEANUP`
   或扩 T10 地盘。**本卡未碰该文件。**
3. **覆盖矩阵四类计数**：N1（新文件）= **21**、N2（已有 retry 测试）= **0**、T10-C 承接 = **15**、
   N3（语义已删·登记退役）= **1**，合计 37。退役的那 1 条 =
   `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_record_temporal_event_uses_retry_method`
   （删除 sha `59586af1`）。矩阵路径：`_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md`。
4. **`backend/data` 两个 jsonl 被 `tests/unit` 里**别的**用例写脏（地盘外，本卡不代修）**：
   `failed_edge_syncs.jsonl` / `failed_writes.jsonl` 在**开工**目录级跑期间即被写（11:57:55 / 11:59:26，
   早于本卡任何文件进入收集面）。生产侧这两个路径是 `__file__` 派生的绝对路径
   （`app/core/failed_writes_constants.py:12`、`app/core/failure_counters.py:25`），未打桩的用例会直接写真文件。
   建议另立卡把这两个常量改成可注入形态，或给相关测试补 fixture 级 patch。
   ⚠️ 与死信坟场 `dead_letter_episodes.jsonl` 无关，后者开工收工均不存在。
5. **开工 / 收工目录级红集**：开工 `epw-unit-open-20260915T115641.txt` → **34 条**（对 64 条红基线
   diff 只有 30 行 `<`、**0 行 `>`** ⇒ T10-A/B/C 已修掉 30 条，本卡开工时没有新增红）；
   收工见 §四.6。
6. **三条 xfail 各自的决策与依据**：见 §三（A/A/B）。矩阵附录 A 有同一张表的完整版。
7. **生产侧隐患移交（本卡不改 `backend/app`）**：`get_episode_worker()`（`episode_worker.py:668-673`）
   无 `dead_letter_path` 入参、`:672` 无参实例化 ⇒ `backend/app` 内 8 处 `get_episode_worker()`
   （`main.py:274/:386`、`tips.py:635`、`question_generator.py:1047`、`memory_service.py:462/:1540/:1821/:1957`）
   + 1 处 `cleanup_episode_worker()`（`main.py:498`）恒用 **cwd 相关的相对路径**
   `data/dead_letter_episodes.jsonl`。候选：改成 Settings 注入的绝对路径。
8. **跨卡提醒（T10-C 面，本卡只登记不代修）**：T10-C 重写的 `TestAC3StartupRecovery` 走
   `_enqueue_episode → get_episode_worker()`；本卡实测它**已经**用
   `monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: w)` 打了桩
   （`test_story_38_6_scoring_reliability.py:200`），故 AST 门对它 0 ADVISORY、sentinel Stage A 也为 0。
   这一条从「预警」降为「已确认无问题」，但卡文 §二.11 与手册 §一.3 T10 行的预测数字（+1 ADVISORY）
   需要在台账里更正。
9. **新工程坑（建议进坑索引）：被中断的 pytest 存档读成「零红」= 最漂亮的假绿**。
   本卡 r2 重跑收工目录级时，那一跑在 14% 被中断（54 行、`rc=1`），存档里 `FAILED/ERROR` 抽出
   **0 条** —— 若按既定判据流程照抽，会得出「红集 0、对基线 64 全是 `<`」这个**比真结果还好看**的
   结论。**识别锚：汇总行 `=+ … in …s =+` 必须存在**（没有汇总行 = 没跑完），且行数/进度百分比要对得上。
   建议把「先断言汇总行存在，再抽红集」写进卡文模板的目录级判据，而不是只写「抽 FAILED/ERROR」。
10. **新工程坑（建议进坑索引）：中文路径让 `git diff --name-only | grep '^<前缀>'` 类判据恒 0**。
   git 默认 `core.quotepath=true`，非 ASCII 路径会被输出成 `"…/\345\256\241\346\237\245/…"`——行首是
   双引号，任何 `^` 锚定的 grep 都不命中。本卡地盘门的验伪锚第一次就因此读成「exclude 没起作用」。
   判据写法：`git -c core.quotepath=false --no-pager <cmd> --no-color`。本仓 `_bmad-output/审查/`
   `_bmad-output/验收单/` 全是中文目录名，所有车道都会踩。
   ⚠️ **如实：这不是新发现**——第十四批 **T9-B（2026-09-14）**已经记录过**完全同形**的一次
   （同样是 `grep -c '^_bmad-output/'` 在实有 4 条时返回 0，同样被当成验伪锚）。本卡隔一张卡
   又原样踩一次 ⇒ 这两条应当写进卡文模板的判据写法里当**默认动作**，而不是靠每张卡各自重新发现。
11. **本卡自身的「数字没数就写」共 3 次，建议进 feedback 类记忆**：① 矩阵附录写「26 条」（计划数
    当实测数，Codex r1 LOW-1 抓）；② 重叠表写「剩余 14 行参照文件均未触及」（Codex r1 LOW-1 + r2 LOW-3
    连抓两轮，实际是 8 同题 / 6 部分同题 / 7 未触及）；③ 负控条数写「17」（实测 16）。
    三次都不是代码错，是**关于证据的断言没有先数一遍**。可用的机械对策：凡写「N 条 / 全部 / 均未」
    之前，先跑一条能产出该数字的命令（`ast` 数节点、`grep -c`、`--collect-only` 尾行），把命令和输出
    一起写进文档。
12. **Codex r5 LOW-3 移交（需改 `backend/tests`，轮次已到上限 5）**：
    `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` 的三个哨兵 `[0.37, 1.23, 4.56]` 都 ≥ 0.1，
    因此**调用端**若改成 `await asyncio.sleep(max(backoff, 0.1))` 不会被抓住（属性侧的 `0.001`
    断言只覆盖属性内部）。修法一行：把某个哨兵换成 `< 0.1` 的值（如 `0.05`）。建议归 T10-E 或后续卡。
13. **卡文 §二.9 的 ruff 验伪锚写法在本仓不成立**：`backend/**` 只启用 14 条必错级规则，**F401 不在其中**
   （完整列表见 §四.9），用 F401 当验伪锚恒不触发；本卡改用 **F821** 并且**必须把探针放在仓内**
   （放 `/tmp` 会因吃不到本仓配置而得到假阴性——本卡第一次就踩了，已留档）。
   ⚠️ **同样不是新发现**：T9-B（2026-09-14）已记录「锚文件放 `/tmp` ⇒ ruff 解析不到本仓配置 ⇒ 锚哑火」。
   本卡隔一张卡又踩一次。建议把「锚必须落在被判据真正覆盖的那片地上」写进卡文 §二 的判据模板。

---

## 七 本卡未证明什么（≥4）

1. **不证明**新文件的 21 条等价用例**逐条等强于**被 skip 的原用例。等价是语义层映射，不是断言逐字复刻；
   worker 的语义与旧 `memory_service` 已有 5 处公开声明的收窄/反转（退避定值→上界、无 per-attempt
   超时、错误类型区分位置迁移、重试身份反转、失败计数器归属迁移），见新文件头 §1–§5。
2. **不证明** `59586af1` 删除旧退避常量**之前**那些用例曾经是绿的——本卡没有回溯历史 commit 跑过它们。
3. **不证明** `GraphitiEpisodeWorker` 的全抖动退避在**生产负载**下的时序正确性。本卡只测上界、单调、
   60s 封顶、耗尽落死信，`asyncio.sleep` 全程被打桩为不真睡，**零真实时延**被验证。
4. **不 un-skip、也不评** `test_memory_service_write_retry.py` / `test_failure_observability.py` /
   `test_qa_38_6_scoring_reliability_extra.py` 三个文件本身的缺陷——它们仍被 skip，属非 T10 面。
   本卡只在新文件提供等价覆盖并在矩阵登记映射。
5. **不处置** `test_qa_38_4_dual_write_extra.py` 的那条 xfail（不在地盘，且 `daa9fd37` 后永不 XPASS）。
6. **只在 `tests/unit` 目录级验证**，未跑 `tests/integration` / `tests/e2e`（卡文禁止；那两处走 advisory 仍会真连）。
7. **不证明** T10-C 对 graphiti 11 条 + AC3 4 条的 un-skip **重写质量**——本卡只核了「两处 skip 已删」
   这个事实，并据此在矩阵里把 15 条记到 T10-C 名下。
8. **不证明** AST 路径门能看见经 `memory_service` 的**间接**入口。它只做「import 了 memory_service
   （三种写法）就必须出现 patch 目标串 `get_episode_worker`」的**启发式**，不追调用链；对 38_6 该启发式
   还只是 ADVISORY 级。运行期唯一防线是 sentinel，而 sentinel 又抓不到「建了默认路径 worker 但这次没落死信」
   ——两层都有各自的盲区，本卡如实声明。
9. **不证明**第 30 行（`test_full_cycle_fail_record_recover_merge`）的**全循环**。新文件只承接
   「失败 → 记账（可重放字段 + count）」半程；「恢复 → 合并视图」半程属 `MemoryService.recover_failed_writes`
   / `load_failed_scores` 面，不在 worker 内。
10. **不证明**收工目录级跑里 `backend/data` 被写脏的那两个文件**具体由哪几个用例**写的——本卡只用
    时序 + 收集面证据把它归到「非本卡引入」，没有做逐用例二分归因（那是地盘外的活）。
11. **不证明**「静态门 PASS ⇒ 隔离成立」。路径门自带三条**已声明的未覆盖路径**（值经变量中转、
    `memory_service` 字符串启发式、不追调用链）；运行期的 sentinel 又抓不到「建了默认路径 worker
    但这次没落死信」。两层都是必要条件，合起来也不是充分条件。
12. **不证明**负控等同于生产变异测试。本卡的负控改的是**测试自己的期望值**（证明断言在执行、
    且观测值就是断言的那个值），**没有**对 `backend/app` 做变异（卡文禁改生产）。
    「把生产改成 X 会不会被抓住」这类结论，只在 Codex 逐条做**静态对照推演**的范围内成立。
13. **不证明**外层 `MEMORY_WRITE_TIMEOUT` 覆盖真实重试总耗时。worker 是后台队列、`enqueue` 非阻塞，
    与 `agent_service` 的外层超时不在同一条同步路径上；本卡没有、也不该在测试侧编造这层关系
    （38_6 里 `test_outer_timeout_covers_inner_total` 仍用本文件的模块级本地桩，非本卡处置面）。
14. **不证明**「21 条全部完整等价」。逐行重叠表显示其中 8 行参照文件已同题、6 行部分同题；
    本卡的增量是**具体的、可逐条列举的**（见矩阵 §统计段），而不是「21 条都从无到有」。

---

## 八 Codex 复核

### 8.1 轮次与绑定（D-15）

| 轮 | 绑定 SHA | B | H | M | L | 之后是否改了代码 | 存档 |
|---|---|---|---|---|---|---|---|
| r1 | `65a84a91` | 0 | **1** | 4 | 2 | 是（HIGH-1 等） | `codex-review-CARD-EPW-COVERAGE-r1.md` |
| r2 | `366835b8` | 0 | **0** | 1 | 4 | 是（M1+L4） | `…-r2.md` |
| r3 | `a8e31623` | 0 | **0** | 1 | 3 | 是（M1+L3） | `…-r3.md` |
| r4 | `f3190f13` | 0 | **0** | **0** | 4 | 是（L4，含两条本卡自引缺陷） | `…-r4.md` |
| **r5（末轮）** | `99958aa8` = **最终 HEAD** | **0** | **0** | **0** | 5 | 否（只改 `_bmad-output`，D-32 不占轮次） | `…-r5.md` |

- **通过线**：D-15 要求「末轮绑最终 HEAD 且 BLOCKER=0、HIGH=0」。**r2 起每一轮都是 B0/H0**；
  末轮 r5 绑 `99958aa8`（= 最终 HEAD），终审绑定判据见 §8.3。
- **为什么 r2 达线后还跑到 r5**：每轮的 MEDIUM/LOW 都是**可在测试侧关闭的真缺口**，而不是措辞问题；
  其中 r4 的两条更是本卡自己引入的缺陷（路径门**误杀** + 新用例隐含 Python≥3.13）。
  按 D-15「审后改代码必再送一轮」，每次整改后都重新送审。协议上限 5 轮，r5 即末轮。
- 每份存档首部按协议 §2.1 抄了「模型 / reasoning_effort / codex 版本 / 命令 / 审查绑定 /
  会话头自证」，自证三行**逐行括注 `.stderr` 行号**（`:2` / `:5` / `:9`——⛔ 不是机械抄前三行，
  codex 0.153.3 把 `model:` 排在第 5 行）。`*.stderr*` 不入库（实测入库数 = 0）。

### 8.2 Codex 逐条提了什么、我怎么改的（14 条全部关闭或如实登记）

| 轮·级别 | 问题 | 处置 |
|---|---|---|
| r1 HIGH-1 | 退避公式测对了，但「实际重试用了它」没被钉住（把生产改成 `sleep(0)` 也全绿）；且 `retry_count` **先递增**未声明 | 新增 `test_retry_actually_sleeps_backoff_seconds_series_2_4_8`；38_6 两条改写补注「属性层 1/2/4 ≠ 实际重试 2/4/8」 |
| r1 M-1 | 「重试成功日志」被拆在两个用例里，都没真断言 | `test_success_after_one_retry` 内补 logger 断言 |
| r1 M-2 | 身份断言不排除「最后一次换成副本」 | `patch.object(w._dead_letter,"store",wraps=…)` 断言落进死信的 task `is` 原对象 |
| r1 M-3 | 矩阵 #16 措辞过强（「接线语义已删」） | 改为「旧符号退役 + 新接线覆盖移交、未验证」，并写明 38_6 的 `ready_worker` 就是现成可写范式 |
| r1 M-4 | 路径门 PASS 不证明隔离（危险字面量 / import 别名） | 封两条 + docstring 如实列出仍未封的三条 |
| r1 L-1 | 矩阵「26 条」「剩余 14 行未触及」不实 | 重数为 32 函数/46 条 + 逐行重叠表 |
| r1 L-2 | metrics 十字段只断言七个 | 补 `queue_depth` / 耗时样本数 / `max>=avg` |
| r2 M-1 | 上界桩分辨不出 `uniform(0,cap)` 与 `uniform(cap/2,cap)` | 桩改 1/4 点 + 断言 `uniform` 实参下界 = 0 |
| r2 L-1 | `to_dict()` 把 `queue_depth`/耗时写死成 0 也能过 | 新增 `test_worker_metrics_to_dict_serializes_nonzero_depth_and_times` |
| r2 L-2 | 门放行 `str("危险字面量")` 与跨模块别名 | 递归扫子树常量 + 别名收集不限模块 |
| r2 L-3 | 重叠表低估参照文件（#1 有等式、#20 已覆盖） | 逐行重数：同题 8 / 部分同题 6 / 未触及 7 |
| r2 L-4 | warning 只验首尾两条 | 改逐条核 `attempt 1/3`、`2/3`、`3/3` |
| r3 M-1 | 1/4 点桩仍是 `(low,high)` 的函数 ⇒「按区间重算 sleep」不红 | 桩改**与区间无关的哨兵串** `[0.37,1.23,4.56]` |
| r3 L-1 | 封顶用例丢掉属性返回值 ⇒ `min(uniform,5.0)` 不红 | 断言 `returned == bounds` |
| r3 L-2 | 门放行 `str("data/"+"dead_letter_"+"episodes.jsonl")` | 加常量拼接检查（此法在 r4 被证明有缺陷，见下） |
| r3 L-3 | 矩阵附录数字未随整改同步 | 附录 B 改为终稿实测 |
| r4 L-1 | 上界/哨兵样本都 ≥0.37 ⇒ `max(uniform,0.1)` 的**下限抬升**不红 | 封顶用例加 `0.001` 样本 |
| r4 L-2 | 我 r3 加的拼接检查**既漏检四段拼接、又误杀** `str(tmp_path / ("data/" + …))` | **重写为正向规则**：值必须依赖变量；`ast.walk` 是广度遍历、本就不是求值顺序 |
| r4 L-3 | 矩阵 #2 声称的等式，用例其实只等 `>= 1` | 补精确计数断言 |
| r4 L-4 | 新用例隐含 Python≥3.13（生产容器是 3.11） | 加 `skipif` + 版本边界 docstring；生产分支不改，登记移交 |

### 8.3 终审绑定

```
git -c core.quotepath=false --no-pager diff --stat --no-color 99958aa8 HEAD -- . ':(exclude)_bmad-output'
（输出为空 —— 0 行）

- **0 行 ⇒ r5 仍绑最终 HEAD**，D-15 通过线成立（存档 `epw-binding-final-20260916T020304.txt`）。
- 同次实测：工作树里**非 `_bmad-output` 的改动 = 0**；`git diff --stat -- backend/tests` = **0 行**
  ⇒ 18 条负控对被测文件的临时改写**已逐字节还原**（`shasum` A==B 之外的第二重证据）。
- ⚠️ **这里那条「去掉 exclude 应多出 _bmad-output 路径」的验伪锚是空转的**：审 SHA 就是 HEAD，
  两边比自己、任何 pathspec 都得 0。有效的 exclude 验伪锚在 §4-A.5（`PREV`→HEAD，95 → 0）。
```

### 8.4 末轮仍登记（不阻断）

末轮 r5 给出 5 条 LOW。其中 **4 条只需动 `_bmad-output`，已在本轮后关闭**
（按 D-32 不占轮次、不破坏终审绑定，证据见上）：

| r5 LOW | 问题 | 处置 |
|---|---|---|
| 1 | `from pathlib import Path as P` 后 `P("data/"+"dead_"+…)`：包装**别名**被当成路径来源变量 ⇒ 门放行 | 已修：包装名收 `pathlib`/`os` 的 import 别名；锚实测 FAIL ✅ |
| 2 | 危险片段表里的**裸文件名**把 `str(tmp_path / "dead_letter_episodes.jsonl")` **误杀** | 已修：片段表收窄成只认路径前缀 `data/dead_letter`；锚实测 PASS ✅ |
| 4 | 18 条负控只留 14 份详细红档（同一用例多条负控共用文件名互相覆盖） | 已修：存档名加序号；重跑实测 **18 块 ↔ 18 份** ✅ |
| 5 | 矩阵附录仍写 169 assert，AST 实测 171 | 已修：按收工重取值同步 ✅ |

**仍登记不阻断的 1 条**（需要改 `backend/tests`，会破坏终审绑定且**轮次已到上限 5**）：

| r5 LOW | 问题 | 为什么不在本卡关 |
|---|---|---|
| 3 | 低值样本只贯穿到**属性**，没贯穿到**调用端**：若 `_handle_failure` 改成 `await asyncio.sleep(max(backoff, 0.1))`，三个哨兵 `[0.37, 1.23, 4.56]` 全都 ≥0.1、不受影响，属性侧的 `0.001` 断言也观察不到调用端这处加工 | 修法很小（把哨兵之一换成 <0.1 的值，如 `0.05`），但**要改 `backend/tests`** ⇒ 按 D-15 必须再送一轮，而 r5 已是协议上限的第 5 轮。本卡按「B=0 且 H=0」交付，此条**登记移交**，建议在 T10-E 或后续卡一行改掉 |

> 另：r5 总评重申的边界与本单 §七 一致——静态门 PASS、47 passed、负控变红，**都不足以**证明
> 完整调用链隔离或「所有语义变异都会被抓住」。本卡不作此主张。

---

## 九 收尾

- **代码 commit**：`65a84a91` —— header
  `test(epw): GraphitiEpisodeWorker 等价覆盖 + 去标 3 条 xfail [BATCH-2026-09-11-第十四批 / CARD-EPW-COVERAGE]`
  （`wc -m` = **96** ≤ 100，含批次标记与卡 ID；⛔ 用 `wc -m` 而不是 `awk length()`——后者按字节，
  对中文会差约 3 倍）。lefthook 全绿：`ghost-files` / `mutant-residue-scan` / `python-lint`（ruff lint +
  format 均 OK）通过，`python-typecheck` **自动 skip**（本卡零 `backend/app` 文件）
  ⇒ **全程没有也不需要 `LEFTHOOK_EXCLUDE`**。`commitlint` 0 problems（1 warning: subject-case，
  与本仓既有中文 header 一致）。
- **文档 commit**：见下（验收单 + Codex 存档，仅 `_bmad-output`，不影响终审绑定）
- `*.stderr*` 不入库：`find evidence-epw-coverage -name '*.stderr*'` = **0**
- 不改台账（`未合卡追踪台账.md` 只主 session 改）✅
- **不 push** ✅
