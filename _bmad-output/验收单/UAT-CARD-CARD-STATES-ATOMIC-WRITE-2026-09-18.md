# UAT — CARD-CARD-STATES-ATOMIC-WRITE

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-CARD-STATES-ATOMIC-WRITE]` · 车道 P4（`card-p4-fsrs` / 分支 `card/p4-fsrs`）· 本车道第 1/3 张
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P4-A.md`（feature 主干树 `--add-dir` 那份）
> 证据目录：`_bmad-output/审查/evidence-card-states-atomic/`

## 〇 终态（收工重算，以命令输出为准）

| 字段 | 值 | 取值命令 |
|---|---|---|
| B15_BASE | `9c4e7e82` | `git rev-parse --short=8 9c4e7e82` |
| 最终 commit SHA | 以 `git log -1` 为准（本文件回填自身会再触发一次 `--amend`，故不写死） | `git rev-parse --short=8 HEAD` |
| **代码树身份（跨 amend 稳定）** | `review_service.py` blob `bd5109e201e4` · `test_g3_7_truth_source.py` blob `7febf9ad7725` · `concept-identity/spec.md` blob `f6f0a187bcd1` | `git rev-parse HEAD:<path>` |
| 本卡 commit 数 | `1` | `git --no-pager log --no-color --oneline 9c4e7e82..HEAD \| wc -l` |
| Codex 轮次 | `5（第 5 轮未取得，见下）` | `ls _bmad-output/审查/codex-review-CARD-CARD-STATES-ATOMIC-WRITE*.md \| wc -l` |
| 地盘 | 3 文件 · `review_service.py` 恰 **4** hunk | `territory-ruff-v2-*.txt` |
| 新增回归门 | **16** 条 `concept_identity_*`（文件 21 → **37** test） | `grep -c 'def test_concept_identity'` |
| spec Scenario | 5 → **7** | `grep -c '^#### Scenario'` |

## 一 第 0 分钟（(a)）

| 项 | 实测 |
|---|---|
| `pwd` / 分支 / HEAD | `…/card-p4-fsrs` · `card/p4-fsrs` · `9c4e7e82` ✅ |
| `git status --porcelain \| wc -l` | `0` ✅ |
| `backend/.venv/bin/pytest` · `backend/.env` | 均在 ✅ |
| pyright 自证 | `test -x $P`（`card-v5-lance/backend/.venv/bin/pyright`）通过 ✅ |
| 红基线 | `grep -vc '^#' "$BASE"` → **33** ✅ |
| 开工 `tests/unit` 目录级 | `32 failed, 5731 passed, 44 skipped, 13 xfailed in 758.40s`，`rc=1` — `unit-open-20260918T164954.txt` |
| 开工 `backend/data` | **空**（`git status` + `find` 双口径 + 一条 find 验伪锚）— `data-dir-after-unit-open-20260918T164954.txt` |

**开工基线 vs 红基线 diff（只允许 `<`）**：`3d2 < FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`
——33 → 32，唯一差异是基线头第 4 行已登记的 flaky 那条本次转绿，**无 `>`**。

**⚠️ 卡文 §〇 一条「推断」未复现（如实记录）**：§〇「tmp 不被 ignore」行推断「不隔离的 unit 用例
在旧实现下会往车道 `backend/data/` 留 `fsrs_card_states.json.tmp`」。实测：`backend/data/` 下
**既无** `fsrs_card_states.json`、**也无** `.json.tmp`（两个口径都查——`git status` 看未忽略文件，
`ls`/`find` 看被 `.gitignore:8` 忽略的那个）。按**未复现**登记，不作为任何判据。

**手册地盘核**（只读 feature 主干树那份，未改）——`2026-09-18-第十五批开跑手册-11车道33卡.md:450` 原文：

> \| **P4** \| `card-p4-fsrs` \| **P4-A**（CARD-CARD-STATES-ATOMIC-WRITE） \| P4-A → P4-B → P4-C \| C1-06 首张（FSRS 真相源 = 数据面）；review_service.py 触及 backend/app ⇒ pyright 0。C1-06 修完再 G3-8（迁移前先修原子写）。

**§〇 逐条核对**：`:920` / `:974-976` / `:981` / `:993` / `:2660` / import 段 `:62-65` /
`_CARD_STATES_FILE:124` / spec 114 行 5 Scenario / `test_g3_7` 681 行 21 test /
`sync_board_concepts.py:582-611` / `atomic_io.py:47-91` / lefthook 四个 glob /
`git check-ignore` json(rc=0) 与 json.tmp(rc=1) —— **全部逐字一致，零行号漂移**。

**登记的口径差**：手册 `:133` 写「concept-identity **5** Scenario」，卡文 §一(d)(e) 与 /goal 写 **6**。
本卡按卡文执行；Codex **五轮**整改后最终落成 **7 个 Scenario / 16 条门**（多出的门全部是 Codex
r2/r3 的两条 HIGH 与 r4 的 MEDIUM 修复所必须，见 §七）。

## 二 先红（(b)）

### ① 结构基线（AST，改前）— `ast-before-20260918T165154.txt`

`to_thread=2`（首参 `tmp_file.write_text` / `tmp_file.replace`）· `write_text_attr_refs=1` ·
`encode_before_to_thread=False` · `helper=absent` · `import_os=False`；
文本锚 `grep -c 'fsync'` = **0**、`grep -cF 'tmp_file.write_text'` = **1**。

> ⚠️ 门口径：`write_text` 数的是 **Attribute 引用**而非 Call —— 改前形态
> `asyncio.to_thread(tmp_file.write_text, …)` 里它是被当作**值**传递的 `Attribute`，
> 数 Call 则改前改后同为 0 = 恒绿（假绿）。

### ② 行为先红 — `s-red-20260918T165543.txt`

`8 selected`（≥6，非 rc=5）· `3 failed, 5 passed` · `rc=1`。三条红及断言落点：

| 红的 test | 断言文案 |
|---|---|
| `…s3_encoding_failure_rolls_back_and_creates_no_tmp` | 「`.json.tmp` 不存在：编码必须发生在打开任何文件之前」（实得 size=0 残留） |
| `…s6_failure_after_tmp_leaves_no_residue` | 「`.json.tmp` 不存在：…必须由 finally 清掉」 |
| `…s6_fsync_precedes_replace` | 「fsync 调用序列非空」（实得 `[('replace', …json.tmp)]`） |

> **同批第一次先红跑（`s-red-20260918T165437.txt`，4 failed）如实保留**：第 4 条红是**我写的测试
> 的 bug**——`build_vault_group_id()` 过 `sanitize_subject_name()`，后者 `lower()`
> （`subject_config.py:152`），于是 `"A"` 落桶其实叫 `"a"`，硬写 `("A", cid)` 断言的是一个**永远
> 不存在的键**。已改小写并把该实测写进测试注释。两份存档都在库里可对读。

### ③ `openspec validate` 改前 — `openspec-validate-before-20260918T165211.txt` `valid`/`rc=0`。
**结构门不是鉴别门**（改前就 PASS），只作「改后没把 spec 写坏」的对照。

## 三 实现（(c)(d)(e)）

### (c) `backend/app/services/review_service.py` —— 恰 4 个 hunk

| hunk | 内容 |
|---|---|
| `@@ -60` | stdlib import 段加 `import itertools` / `import os` / `import threading`（字母序） |
| `@@ -656` | `_card_states_file_lock = threading.Lock()` · `_card_states_seq = itertools.count(1)` · `_card_states_published_seq = 0` · 模块级同步 helper `_persist_card_states_bytes(target, payload, seq)`（放在 `_card_states_count` 之后、`class ReviewStatus` 之前，与形态分派 helper 同段） |
| `@@ -925` | `_save_card_states` docstring：`atomic write (temp file + rename)` → `(temp + fsync + replace + finally cleanup)` |
| `@@ -971` | 替换段：`payload = data.encode("utf-8")` + `seq = next(_card_states_seq)` + `await asyncio.to_thread(_persist_card_states_bytes, _CARD_STATES_FILE, payload, seq)` |

helper 体（沿 `sync_board_concepts.py:582-611` 范式 + 两轮 Codex HIGH 整改）：

```
with _card_states_file_lock:              # 线程级串行（asyncio 锁被取消时会释放，覆盖不到已启动的线程）
    if seq <= _card_states_published_seq: # 过期写丢弃（互斥 ≠ 顺序）
        return
    try:
        open(tmp,"wb") → write → flush → os.fsync(fh.fileno())
        os.replace(tmp, target); _card_states_published_seq = seq
        os.open(target.parent) → os.fsync(dir_fd) → os.close(dir_fd)
    finally:
        tmp.unlink(missing_ok=True)
```

**保留未动**：`mkdir` / `json.dumps` / debug 日志 / `_unpersisted_concepts.clear()` /
`except (TypeError, ValueError)` 与 `except OSError` 两分支 / `_card_states_payload` 形态分派。

**一处刻意保留并声明**：替换段正上方的注释 `# Atomic write: write to temp file then rename` 未改
——地盘约束把本文件增删行限定在四处，改它会产生第 5 处 `-`/`+`。该注释现在**描述不全**，
已在 Codex prompt 主动声明并登记建议随后续卡收。

### (d) `openspec/specs/concept-identity/spec.md`

Requirement 改写为实现态（先编码再开文件 / bytes 写 tmp / flush / fsync / `os.replace` / 目录 fsync /
一次 `to_thread` / 每条失败路径 MUST attempt to remove 且 `missing_ok=True` 只吞 `FileNotFoundError` /
整段另持 `threading.Lock` 且只覆盖进程内 / **互斥不等于顺序 ⇒ 单调 seq + 过期写丢弃**）；
锁那一段补一句「asyncio.Lock 不覆盖被取消后仍在跑的线程」；Scenario 1 追加「调用后无 `.json.tmp`
残留」并把 `Path.replace` 改为 `os.replace`；Scenario 3 追加「未建过 tmp」；
**新增 Scenario 6**「失败零残留 + 目标逐字节不变 + fsync 先于 replace」与
**Scenario 7**「过期快照不得覆盖已落盘的更新快照」。114 → 167 行，Scenario 5 → **7**，Requirement 恒 **1**，
`:4 ## Purpose` TBD 未动。

**`:34-57` 三段一字未动（自证）**：spec diff 的**全部 `-` 行**只落在 `@@ -14`（Requirement 改写）、
`@@ -25`（锁那句的延长）、`@@ -69`（`Path.replace` → `os.replace`）三处，**受保护区零 `-`**；
另用整段字符串包含比对（base `sed -n '34,57p'` 的 22 个非空行作为子串）→ `True`。
`openspec validate --strict` 改后 `valid`/`rc=0`（`openspec-validate-r4-*.txt`）。

### (e) `backend/tests/regression/test_g3_7_truth_source.py` —— **16** 条门（21 → **37** test）

| test | Scenario | 关键断言 |
|---|---|---|
| `…s1_snapshot_published_by_atomic_replace` | S1 | 目标 0 次写模式 open（spy 包 `builtins.open` **与** `io.open`）+ 探针存活正控锚 + 落盘 JSON == `_card_states_payload()` + tmp 不残留 |
| `…s2_unresolvable_scope_fails_closed_without_fs_write` | S2 | `False` + dirty + **父目录不存在**（mkdir 未跑） |
| `…s3_encoding_failure_rolls_back_and_creates_no_tmp` | S3 | `False` + key 被 pop + dirty + **tmp 从未被写模式打开过** + tmp 不存在 |
| `…s3_rollback_restores_previous_value` | S3 | 先前有值 ⇒ 恢复旧值（不是 pop） |
| `…s4_successful_snapshot_clears_every_dirty_marker` | S4 | `True` + `_unpersisted_concepts == set()` + 快照**不含**被回滚的键 |
| `…s5_dirty_marker_is_vault_scoped` | S5 | `("a","c")` 在集内；vault b 下 `_dirty_key == ("b","c")` 且 `_is_unpersisted is False`；回 a 仍 `True`。**刻意不在 b 下做成功保存**（会 clear 掉 a 的标记 ⇒ 判据恒绿） |
| `…s6_failure_after_tmp_leaves_no_residue` | S6 | replace 失败 ⇒ `False` + dirty + tmp 不存在 + 目标**逐字节**等于旧快照 |
| `…s6_fsync_precedes_replace` | S6 | 首个 `fsync` 早于 `replace`；且 **fsync 时 `os.fstat(fd).st_size == len(payload)`**（钉 flush 先于 fsync） |
| `…s6_write_phase_failure_leaves_no_residue` | S6 | 文件 fsync 失败 ⇒ 目标原封不动 + 无残留 |
| `…s6_write_failure_leaves_no_residue` | S6 | **`write` 本身**失败（`_WriteRefusingFile` 薄代理）⇒ 无残留（钉清理覆盖 open/write 段） |
| `…s6_directory_fsync_failure_is_reported_not_swallowed` | S6 | 只让**父目录**的 fsync 失败（按 `S_ISDIR(os.fstat(fd).st_mode)` 判定 + 断言父目录 inode 确被 fsync + 文件先于目录）⇒ `False` + 脏标记保留 + 目标**确实**已是新快照 |
| `…s6_cleanup_failure_is_normalized_not_swallowed` | S6 | `unlink` 抛 `OSError` ⇒ 归一为 `False` + dirty（`missing_ok=True` 吞不掉它） |
| `…s6_persist_is_serialized_across_threads` | S6 | 四线程直跑 helper，临界区取**锁本身**（`_TrackingLock` 包真锁记录持有区间）⇒ **零重叠** + `entered == 4` 确定性存活锚 + 终态文档**恰好一个键** |
| `…s6_stale_publish_is_discarded` | S7 | 大 seq 先落盘 → 小 seq 再试 ⇒ 目标不变 + 无 tmp；末尾**探针存活锚**（更大的 seq 必须真的落盘） |
| `…s7_failed_publish_does_not_advance_the_watermark` | S7 | 大 seq 的发布在 `os.replace` 失败 ⇒ 水位不得推进，随后一个**更小**且从未发布过的 seq 仍须落盘 |
| `…s7_seq_is_allocated_before_dispatch` | S7 | 从**生产调用方**观测 `asyncio.to_thread`：被派发的必须是 helper、seq 必须是**已算好的 int 实参**、连续两次严格递增（同时钉住「换成同步直调」） |

DD-03：失败注入只包装真 `os.replace` / `os.fsync` / `pathlib.Path.unlink` / 真文件对象
（`_WriteRefusingFile` 只拦 `write`、其余 `__getattr__` 转发），**不 mock** `ReviewService`
内部方法；`svc` 复用本文件既有 fixture。未改既有 21 个 test、未改 `:74-85` autouse fixture、
未动 `tests/unit/**`、未动任何 conftest。

> 段首注明：本段任何用例**不得**调用 `monkeypatch.undo()`——那会把 autouse fixture 对
> `_CARD_STATES_FILE` 的重定向一起撤掉，后续写入落到车道树 `backend/data/`（零写门破）。

## 四 DoD-3

### 4-A Claude 已代验（证据，均在 `evidence-card-states-atomic/`）

**1. AST 结构门 + 验伪锚** — `ast-v2-*.txt`（首部带 HEAD + 完整命令 + 源码 sha256）

| | to_thread | 首参 | write_text 引用 | encode 先于 to_thread | helper | fsync | replace | unlink | unlink 在 finally | import os |
|---|---|---|---|---|---|---|---|---|---|---|
| 改前 | **2** | `tmp_file.write_text` / `tmp_file.replace` | 1 | False | absent | 0 | 0 | 0 | — | False |
| 改后（绑最终 HEAD） | **1** | `_persist_card_states_bytes` | 0 | **True** | present `681-740` | **2** | **1** | **1** | **True**（`at=[740]`） | True |
| 验伪锚（同一次执行内，同脚本 × `git show 9c4e7e82:…` 副本） | **2** | 同改前 | 1 | False | absent | 0 | 0 | 0 | — | False |

**2. 先红 → 后绿** — 先红见 §二.②；后绿 `g37-full-r5-*.txt` **37 passed**。

**3. 对照输入（把实现整体换回 `9c4e7e82` 形态）** — `redbind-r5-*.txt`：`16 selected` ·
**11 failed / 5 passed** · `rc=1`；`shasum` 跑前跑后逐字相同（`14018aa4…`），`git status` 空。
**11 红 = 绑本卡新行为**（其中 3 条是接口错误——base 没有 helper/counter，如实声明它们靠
负控段 4/7/8/9/10/11 提供行为证据）；**5 绿 = 既有行为的回归门**（S1 原子 replace、
S2 fail-closed、S3b 回滚、S4 清标记、S5 跨 vault 键），如实声明它们不绑本卡引入的行为。

**4. 负控输入（各只拆一层，红必须落在指定门）** — `negctl-r5-N-*`（**十段**）

| 段 | 变异 | 结果 | 红在哪 |
|---|---|---|---|
| 1 | `finally` 的 `tmp.unlink(...)` → `pass` | **4 failed / 12 passed** | 三条残留门 + 清理失败门 |
| 2 | 删 `os.fsync(fh.fileno())` | **3 failed / 13 passed** | fsync 序门 + 写阶段门 + 目录门 |
| 4 | `threading.Lock()` → `nullcontext()` | **1 failed / 15 passed** | **只**并发门 |
| 5 | 删 `fh.flush()` | **1 failed / 15 passed** | **只** fsync 序门（经 `st_size` 判据） |
| 6 | `os.open(target.parent,…)` → `os.open(target,…)` | **1 failed / 15 passed** | **只**目录门 |
| 7 | 拆掉 `if seq <= _card_states_published_seq: return` | **1 failed / 15 passed** | **只**过期写门 |
| 8 | 不执行 `_card_states_published_seq = seq` | **1 failed / 15 passed** | **只**过期写门 |
| 9 | `next(_card_states_seq)` 挪进 `to_thread` 的 lambda | **1 failed / 15 passed** | **只**派发门 |
| 10 | `to_thread` 换成同步直调 | **1 failed / 15 passed** | **只**派发门 |
| 11 | `_card_states_published_seq = seq` 挪到 `os.replace` **之前** | **1 failed / 15 passed** | **只**水位门 |

十段的 `shasum` 跑前/跑后各自逐字相同（`negctl-r5-N-sha-{before,after}-*.txt`），
还原一律 `git show HEAD:<path> > <path>`（未用 stash / checkout）；变异体 diff 见
`negctl-r5-N-mutant-diff-*.txt`。段 4/5/6/7/8/9/10/11 **各只杀一道门** ⇒ 八个机制彼此独立。

> Codex r4 曾指出「段 1 也会红并发门」是判据耦合（当时并发门的 drain 点是 unlink）。
> 本轮把观测点改到锁本身后，**该耦合已解开**：段 1 现在是 4 failed，并发门不在其中。

**5. pyright** — `pyright-v2-*.txt`（首部带 HEAD + 完整命令 + 检查范围 + 源码 sha256）：
**`0 errors, 80 warnings`**。`# pyright: ignore` 计数 base 6 → after 6，**本卡新增 0**。
未用 `LEFTHOOK_EXCLUDE=python-typecheck`。

**6. ruff** — `territory-ruff-v2-*.txt`：`files=2` · `ruff_check_rc=0` · `ruff_format_rc=0`。
验伪锚 A：已知含 F821 的文件在**同一份** `backend/ruff.toml` 下 `rc=1`；
对照锚 B：已知含 **F401**（该配置未启用）的文件 `rc=0` —— 证明锚 A 的红来自 F82 规则族而非「什么都报」。
**⚠️ `ruff format` 一次**：首次 commit 被 `python-lint` 拦下，诊断为**本卡新增段自身**的格式漂移
（对照输入：base 版该文件 `ruff format --check` = `already formatted`），故**未**用
`LEFTHOOK_EXCLUDE`，直接格式化；格式化后既有 681 行仍是当前文件的**逐字前缀**（`startswith` 自证）。

**7. 既有套件不回退**（三份存档首部含**完整 argv** + 跑前两源码 sha256，末尾含收工时刻 + 收工 sha256，首尾**逐字一致**）

| 面 | base | 收工（绑最终 HEAD） | 判定 |
|---|---|---|---|
| 点名 9 文件 | 该 9 文件在 base 零红（regression 4 文件查 b14 `evidence-b14/integ2/dir-regression-9c4e7e82-20260917T222112.txt`、unit 5 文件查本卡 `unit-open-*.txt`，各 0 命中；验伪锚：同存档 FAILED 行总数 32 ≠ 0） | `suites-r5-*.txt` **159 passed / 0 failed / pytest_rc=0** | ✅ |
| `tests/regression` 目录级 | 1913 passed / 6 skipped / 1 xfailed / rc=0 | `dir-regression-r5-*.txt` **1929 passed / 6 skipped / 1 xfailed / pytest_rc=0**，`FAILED` 行 **0** | +16 = 本卡新增门数，**0 新红** ✅ |
| `tests/unit` 目录级 | 红基线 **33** | `unit-r5b-*.txt` **32** | diff 只有 `<`（flaky 转绿），**无 `>`** ✅ |

> ⚠️ **一次高负载假红如实记录**：`unit-r5-*.txt`（`-r5b-` 的前一次）出现过一条**不在红基线**的
> `>`——`tests/unit/test_deploy_vault_sh.py::test_preflight_accepts_leading_zero_cap`，失败正文是
> 「npm run build 超时（墙钟上限 5s, 已杀 npm 所在进程组）」。归因：**机器高负载**
> （同批 `tests/regression` 该次耗时 981s，其余两次 510s / 606s；另一车道的 codex 同时在跑），
> 5s 墙钟上限被压垮。它是 P3 车道 `scripts/deploy-vault.sh` 的 subprocess 裁判，与本卡三文件
> **无任何交集**（本卡 diff 的文件清单见 §四.8）。单跑 `-k leading_zero` = **2 passed**；
> 空载复测 `unit-r5b-*.txt` 回到 **32 红、diff 只有 `<`**。两份存档都在库里可对读，
> `unit-r5-*.txt` 首部已写明此事。
> ⚠️ **按 Codex r5 收敛口径（采纳）**：「可确认复测未再出现该超时；**高负载是合理推断，
> 尚非独立证实的唯一根因**」——没有 CPU/load 记录，「单跑 2 passed」也只有首部自述。
> 但**现有证据不足以将它归成本卡新增缺陷**（该测试与本卡三文件 `grep` 零交集）。

> ⚠️ 作废/过期存档如实标注：`unit-r2-20260918T180241.txt` 首部写明**作废**——它跑到约 22% 时
> 主 session 为整改 Codex r2 的 HIGH 改了 `review_service.py`，而 `tests/unit` 内有
> `importlib.reload` 会从磁盘重载 ⇒ 前后半程不是同一份代码，已 TaskStop 中止、不作判据。
> `suites-r2` / `dir-regression-r2` 首部标注「绑 `d7ab47c8`，已被后续取代」。
> `-final-` 系列绑 `b173eb44`（r3 态），`-v2-` 系列绑最终 HEAD。

**8. 地盘** — `territory-ruff-v2-*.txt`：恰 3 文件；验伪锚（去掉 `':(exclude)_bmad-output'`）
多出 **104** 条 `_bmad-output/` 路径；禁区（`openapi.json` / `atomic_io.py` / `review.py` /
`models/**` / `tests/unit/**` / `conftest.py` / `openspec/changes`）diff **全空**；
`review_service.py` 恰 **4** 个 hunk，与卡文 (l) 声明的四处一一对应。

**9. 现网只读 / 零残留** — 本卡零连接（无 Neo4j / LanceDB / HTTP，未设任何指向 7691/7687 的
环境变量）。本卡**新增行**里 `fsrs_bridge|decay_beta|7691|7687` 命中 **0**（验伪锚：同口径
`fsync` 命中 24，证明 grep 在「新增行」这个面上有分辨力）；既有的 7 处 `fsrs_bridge` 只读注释
base/after 同为 **7**，未动。收工 `git status --porcelain backend/data` **0 行**（`data-dir-v2-*.txt`）。

**10. 取消/线程前提实测** — `probe-cancel-thread-20260918T175340.txt`：协程取消后
`lock.locked()=False`、锁可被重获、`to_thread` 的线程照跑完、先到者的 `finally` **确实**删掉了
后来者新建的 tmp、两者 inode 不同。这是两轮 HIGH 修法的依据（**不是**采信审查意见）。

**11. 字节等价** — `byte-equivalence-write-20260918T171111.txt`：同一份
`json.dumps(..., ensure_ascii=False, indent=2)` 文本，旧写法 `Path.write_text(data,"utf-8")` 与新写法
`open(tmp,"wb").write(data.encode("utf-8"))` 落盘 **sha256 完全相同**（`1cd4369d…`，181 B；
`os.linesep='\n'`）；验伪锚：改一个字节后 sha 立刻不同。边界见 §五.9。

### 4-B 你来验（零技术词）

- [ ] 我答完一道复习题 → 我看到系统说「已记住」→ 我感觉这句「已记住」是可信的，不是客气话。
- [ ] 我在答题过程中直接关掉页面、或者电脑突然断电 → 我下次打开 → 我看到的要么是上一次完整的
      进度、要么是这一次完整的进度，**不会**是一份空白的或者写坏一半的进度 → 我感觉踏实。
- [ ] 我连着快速答好几道题、中途还切走过一次 → 我看到进度停在**最新**那一次上 →
      我感觉它没有把新的覆盖回旧的。
- [ ] 万一真的存不上（比如磁盘满了）→ 我看到系统**明说**这次没存上，而不是假装成功 →
      我感觉它诚实，我知道该重试。

felt-sense：以前是「它说保存成功了，但我不确定那份进度到底有没有真的落到盘上」；现在是
**复习进度终于是可信的**——成功就是真的成功，失败就明明白白说失败，中间没有第三种含糊状态，
也不会在后台留下一个没人管的临时文件。

## 五 本卡未证明什么（≥4）

1. **未证明跨进程 / 多 worker 并发写安全**。`_card_states_file_lock` 与 `_card_states_seq` 都是
   **进程内**的；`.json.tmp` 是确定性 sibling 名（卡文硬边界**不许换随机名**）。两个 uvicorn
   worker 同时落盘仍会在同一路径上互相截断。本仓实际 worker 数**未核**，登记待查。
2. **未做掉电 / 内核崩溃实验**。持久性只按 `os.fsync` 语义**推断**；macOS 上 `fsync` 不保证把
   数据刷出磁盘缓存，真正的强保证要 `fcntl(F_FULLFSYNC)`，本卡**未用**。
3. **未证明线程锁在高并发下的行为**。持锁线程卡在慢 I/O 时，后续（含已被取消协程的）worker 会
   阻塞在 `Lock.acquire()`，积累到线程池容量会拖住无关的 `to_thread`（Codex r3 MEDIUM）。
   本卡不改线程池配置（不在地盘），**未压测**。
4. **目录 fsync 失败 / 清理失败时文件其实已落位、却返回 `False`**（保守诚实面）。真实介质上的
   发生率与用户可见影响**未验**，产品口径待裁（§六.8）。
5. **`ConceptState.fsrs_*` 标注子项未做**（`models/**` 本批零写者，卡文明令剔除）。
6. **现网 `backend/data/` 是否已有历史 `.json.tmp` 残留未巡检**（现网只读，本卡零连接）。
7. **`atomic_io.py:47-91` 的同型缺陷未修**（写入阶段异常不清 tmp），四消费方
   `review.py:540` / `neo4j_client.py:478` / `neo4j_edge_client.py:820` / `canvas_service.py:678`
   仍在同一残留面上。不在本卡地盘。
8. **S1「never opened in write mode」的 spy 只覆盖 Python 层两个 `open` 绑定**，不覆盖
   「直接用 C 层 `os.open` 写目标」的假想实现（本仓无此写法）。
9. **字节等价只在本机 `os.linesep='\n'` 上实测**。Windows 下 `Path.write_text` 的
   `newline=None` 会把 `\n` 译成 `\r\n`，新写法不会——那种平台上两者**不等价**（新写法更正确）。
10. **没有一条门检查事件循环是否被阻塞**。⚠️ 本条前半句原写「『同步直调』只由 AST 门覆盖」，
    已被**独立复核推翻**——`negctl-r5-10`（`to_thread` 换同步直调）的失败正文正是派发门的断言
    「两次落盘都必须经 asyncio.to_thread 派发…实得 `[]`」，即**有行为门覆盖**。仍未证明的只剩
    「事件循环响应性」本身。
11. **未证明目录 fsync 真的成功同步了目录**：目录门在调用真实 `fsync` **之前**就注入失败，
    它证明的是「确实对父目录 fd 发起过 fsync 并如实报告失败」，不是「同步成功」（Codex r3 指出）。
12. **`_card_states_published_seq` 是进程级单调量**，多个 `ReviewService` 实例共享它。Codex r4
    指出：两个实例各持**独立**的 `_card_states` 容器，B 的较大 seq 可以用一个**不含** A 内容的
    容器覆盖文件——这是基线既有的多实例缺口（生产入口是 singleton），本卡**未修**，登记。
13. **`_card_states_published_seq` 是全局水位，不绑定目标文件**（Codex r4 LOW-6，本卡**未修**）：
    若同一进程里目标路径被切换（测试用 `isolate_card_states` 重定向即属此形），目标 A 的低序号
    worker 可能被目标 B 已推进的水位误丢。需要「旧 worker 存活 + 切换目标」这一额外前提；
    生产目标固定，普通跨测试/跨事件循环的单调递增本身不会误丢。**登记，不阻断。**
14. **「更新的快照天然包含旧的」只在同一容器内成立**（Codex r4 更正）：同一 concept 的旧值会被
    后续值正常替代；跨实例不成立。过期写丢弃的正确性因此依赖「单实例」这个前提。
15. **`unlink` 自身失败这条路径的残留面**：spec 已如实写明「保证的是每条失败路径都**尝试**移除」，
    清理失败门只覆盖「replace 已成功、tmp 已移走」之后的清理失败；「write/fsync/replace 先失败、
    随后 unlink 又抛 EACCES」这条复合路径**没有门**（Codex r4 LOW）。

## 六 台账待登记条目（≥4）

1. **修复 sha `见上表。
3. **`backend/app/utils/atomic_io.py:47-91` 同型残留面建议立卡**：`NamedTemporaryFile(delete=False)`
   下写入阶段异常不清 tmp，只在 `os.replace` 失败时 unlink。四消费方见 §五.7。
4. **现网 `backend/data/*.tmp` 只读巡检**待主 session（本卡零连接、不碰现网）。
5. **卡文 §〇「tmp 会残留」推断未复现**（§一）。若要追，属 P2 C2-02「tests/unit 写脏
   `backend/data`」面，不属本卡。
6. **Codex 各轮存档路径 / 绑定 SHA / B·H·M·L 计数**：见 §七。
7. **卡文 `:X → 实测 :Y` 更正**：**无**。另登手册 `:133`「5 Scenario」与卡文「6 Scenario」的口径差，
   以及最终落成 **7 Scenario / 16 门**（Codex 两轮 HIGH + 一轮 MEDIUM 整改的必然结果）。
8. **产品口径待裁（两条）**：(a) 目录 fsync 失败时文件已落位却报 `persisted=False`；
   (b) 清理（`unlink`）自身失败同样把一次成功发布报成 `False`。Codex r2 明确**不建议**改成
   返回 `True`，建议改 spec 触发条件；但那句话（`spec.md`「On a successful replace … MUST clear …」）
   落在卡文规定的**一字不动**区间，本卡无权改动 ⇒ **该 spec 句与实现的失真如实登记，请裁**。
   本卡已用目录 fsync 门与清理失败门把该失真做成可观测。
9. **`_save_card_states` 替换段上方注释描述不全**（`# Atomic write: write to temp file then rename`），
   因地盘约束未改，建议随 P4-B 或 C2-14 的注释漂移一并收。
10. **本卡新增 `threading.Lock` 的运维含义**：落盘线程现在会互相阻塞。若后续出现「复习接口变慢」
    类反馈，这是第一个该看的地方（Codex r3 MEDIUM 的线程池饥饿面）。
11. **本批环境观察（供主 session 排批参考）**：`tests/unit` 里 P3 的
    `test_deploy_vault_sh.py::test_preflight_accepts_leading_zero_cap` 用 **5s 墙钟**上限跑
    `npm run build`，多车道并发时会假红。本卡实测一次（`unit-r5-*.txt`），空载复测即恢复。
    建议登记为「负载敏感门」，避免后续卡把它误判成本卡引入。
13. **独立复核 MEDIUM-1（登记，不阻断）**：把 `seq = next(_card_states_seq)` 从
    `async with _card_states_lock:` 内提到 `_save_card_states` 首行，两条新门仍全绿，而行为已坏
    （A 取小 seq 后阻塞、B 先发布，A 随后带着**更全**的快照被判过期丢弃且返回 `True`）。
    当前代码把取号放在 `json.dumps` **之后**、锁**之内**，seq 单调性与快照新旧严格同向——
    **这个不变量没有门钉住**。建议下一张卡加一条「取号点在锁内且在 `json.dumps` 之后」的
    AST 结构断言，或补该负控输入。
14. **独立复核 LOW-1 / LOW-2（登记）**：两段负控的 KILLED 落在**非声称断言**上——
    `negctl-r5-4`（拆线程锁）红在 `errors == []`（线程先抛 `FileNotFoundError`），`overlaps`
    根本没被求值；`negctl-r5-11`（记账前移）红在 `FileNotFoundError`（该门不预置目标文件），
    分不清「被误丢」与「根本没写」。建议：把 `overlaps` 断言排到 `errors` 之前 + 给水位门
    预置目标内容。本卡不改（协议对 LOW 是登记；改动会打破独立复核的绑定）。
15. **独立复核 LOW-5（登记）**：spec 仍有两处超出实现——`:166`「no `.json.tmp` is left behind」
    （丢弃分支在 try/finally **之前** return，不清理既有 tmp）与 `:44`「still reports success」
    （丢弃只在协程被取消时可达，而被取消的协程抛 `CancelledError`、永不返回 `True`，
    该返回值**无调用方可观测**）。
17. **Codex r5 MEDIUM-1（登记）**：并发门把观测点从文件操作换到锁之后，`overlaps == []` 只证明
    **锁持有区间**互斥，看不见锁外的文件操作。复现：把 `review_service.py:734-738` 的目录
    `open/fsync/close` 移到锁外，写入/replace/记账/清理留在锁内 ⇒ 16 条门仍可全绿，却不再满足
    「整段持锁」。建议补一条「文件操作全部发生在锁持有区间内」的观测。
18. **Codex r5 MEDIUM-2（登记）**：两条新门仍有未覆盖路径——① 水位赋值移到目录 close 之后
    （高序号 replace 成功、目录 fsync 失败，再发布低序号即覆盖新快照）；② 在 `:1060` 原有
    `to_thread` **之前**加一次同参数同步调用（真正写入在 MainThread 完成，派发门的名称/参数/
    递增断言仍全过）；③ `<=` 改 `<`（测试没有重复使用相等序号）。Codex 用内存边界探针证实了
    前两条，**不是整套 pytest 实测**；当前生产代码没有这些问题。
19. **Codex r5 LOW-2（登记）**：`spec.md:165`（Scenario 7）仍有未限定的「无 tmp 残留」承诺——
    过期丢弃分支在 try/finally **之前** return，不清理**既存**残留。复现：n 已发布；n+1 写入
    失败且清理自身也失败留下 tmp；旧 worker 随后以 m<n 进入 helper 直接过期返回，残留仍在。
20. **`_card_states_seq` / `_card_states_published_seq` 是新的进程级全局状态**：任何后续给
    `_persist_card_states_bytes` 加调用方的卡，必须自己取号（否则会被当成过期写丢弃）。

## 七 Codex

| 轮次 | 存档 | 绑定 SHA | 判定 | 本轮做了什么 |
|---|---|---|---|---|
| r1 | `codex-review-CARD-CARD-STATES-ATOMIC-WRITE.md` | `7a5081f1…` | **B0 H1 M3 L1** | HIGH：协程取消后线程仍跑完 + 锁已释放 ⇒ 新加的 `finally` 会删掉**下一次**落盘的 tmp |
| r2 | `…-r2.md` | `d7ab47c8…` | **B0 H1 M5 L0** | 我上一轮用 inode 认领修，被驳回：B 若在 A replace **之前** `open(tmp,"wb")` 会 truncate 同一个 inode，认领认不出来 |
| r3 | `…-r3.md` | `b173eb44…` | **B0 H1 M3 L1** | 我**撤回**认领层、改 `threading.Lock` 真串行；新 HIGH：互斥 ≠ 顺序，被取消那次的旧 payload 可**晚于**新快照落盘 = 静默丢更新 |
| r4 | `…-r4.md` | `5d69728a…` | **B0 H0 M4 L3** ✅ | 我加单调 `seq` + 过期写丢弃；**HIGH 清零**。r4 指出我本轮引入了一条 flaky 门（并发门的存活锚被过期丢弃破坏） |
| r5 | `…-r5.md` | `28d484b9…` | **B0 H0 M4 L2** ✅ | 修 r4 的 flaky + 用行为门覆盖 r4 MEDIUM-1 + 关 LOW-5/7；前两次送审撞 401（记录 `…-r5-auth-blocked-attempts-1-2.md`），鉴权恢复后第三次取得 |

**✅ D-15 达标**：末轮 `codex-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md` 判
**`BLOCKER=0 HIGH=0 MEDIUM=4 LOW=2`**，绑 `28d484b9…`，原话「**可以按你指定的
`BLOCKER=0 且 HIGH=0` 标准收官**」。Codex 自核了绑定（「已核实 HEAD=…，全量 diff 恰三文件，
生产实现与 r4 逐字节相同」）、十段负控各只拆一个机制、对照输入 5 绿 + 8 断言红 + 3 接口错误。

**⚠️ 前两次送审被鉴权挡住（如实记录，见 `…-r5-auth-blocked-attempts-1-2.md`）**：
`.stderr` 末行 `401 Unauthorized`，`codex login status` = **`Not logged in`**，
`~/.codex/auth.json` **不存在**——**不是配额**。约 20 分钟后复测变成
`Logged in using ChatGPT`，第三次即成功。教训已入记忆：**0 字节先跑 `codex login status`，
401 未登录与配额耗尽同形、处置相反**；也再次印证「外部服务状态是一次观测不是不变量」。

**r5 新提出、本卡不修只登记的 5 条**（协议对 MEDIUM/LOW 是登记不阻断；本轮已是上限第 5 轮，
再改代码就没有可绑定的复核了）：

| r5 条目 | 内容 | 去处 |
|---|---|---|
| MEDIUM-1 | 并发门换观测点后，`overlaps` 只证明**锁持有区间**互斥，看不见锁外的文件操作（把目录 fsync 段移出锁，16 门仍可全绿） | §六.17 |
| MEDIUM-2 | 两条新门仍有未覆盖路径：① 水位赋值移到目录 close 之后 ② 在 `to_thread` 前加一次同参数同步调用 ③ `<=` 改 `<` | §六.18 |
| MEDIUM-3 / 4 | 线程池饥饿 · `spec.md:78` 失真 | 维持 §五.3 / §六.8 |
| LOW-1 | 全局水位未绑定目标文件（= r4 LOW-6） | 已登记 §五.13 |
| LOW-2 | Scenario 7 仍有未限定的「无 tmp 残留」承诺（过期丢弃分支直接 return，不清既存残留） | §六.19 |

**其间由独立 agent 代行过一次（不冒充 Codex）**：按项目 `CLAUDE.md` 铁律 #3「代码审查必须独立
Agent」，用一个**全新上下文**的 Claude agent 做了对抗性复核，报告
`_bmad-output/审查/independent-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md`，
判定 **`BLOCKER=0 HIGH=0 MEDIUM=3 LOW=5`**（只计本轮新发现 `B0 H0 M1 L5`），结论
「**可以收官，没有必须在本卡内解决的条目**」。它自核了绑定（含一条我没核的：`5d69728a` 是被
amend 掉的**兄弟** commit，父同为 `9c4e7e82`，`--is-ancestor` 为否但 diff 对照仍有效）、
AST 测试集合比对（35→37，**REMOVED=[]** ⇒ 本轮没有静默删掉任何测试）、十段负控的单一语义层
与 `sha-before/after` 全等，并**独立佐证了 unit 新红的负载归因**（四条，含 `grep` 证明该测试
与本卡三文件零交集、墙钟 2639s vs 1106s）。⛔ 它**不是 Codex 判定**，供主 session 裁定。

两份结论一致（都判可收官）。**它抓到的 8 条我逐条自核后全部属实**，处置如下
（协议对 LOW/MEDIUM 是**登记不阻断**，且改测试/spec 会打破复核绑定 ⇒ **代码侧一行不动**）：

| 条目 | 性质 | 处置 |
|---|---|---|
| MEDIUM-1 `seq` 取号移出 asyncio 锁仍可全绿 | 本轮新增、未证实（只读判断） | **登记** §六.13，附建议修法 |
| MEDIUM-2 线程池饥饿 | r4 已登记 | 维持 §五.3 / §六.10 |
| MEDIUM-3 `spec.md:78` 失真 | r4 已登记、卡文锁死 | 维持 §六.8「请裁」 |
| LOW-1 负控 4 的 KILLED 落在 `errors` 不是 `overlaps` | 判据归因不精确 | **登记** §六.14 |
| LOW-2 负控 11 的 KILLED 落在 `FileNotFoundError` | 同上 | **登记** §六.14 |
| LOW-3 r4 LOW-6 未登记 | 文档遗漏 | **已补** §五.13 |
| LOW-4 验收单数字过时/自相矛盾 | 文档错误 | **已改** §三(e)、§五.10、§六.7 |
| LOW-5 spec 两处仍超出实现 | 措辞 | **登记** §六.15 |

**轮次状态如实**：r4 已判 `B0 H0`，绑 `5d69728a`。r4 之后本卡**生产代码一行未动**——
`git diff --stat 5d69728a HEAD -- backend/app/services/review_service.py` = **空**（逐字节相同）；
改动只在 `test_g3_7_truth_source.py` 与 `concept-identity/spec.md`，内容是**修 r4 自己指出的问题**
（flaky 门 + MEDIUM-1 的行为门 + LOW-5/7）。按 D-15「审后再改代码 ⇒ 必再送一轮」，
**这一轮是欠的**，已在 `…-r5.md` 里如实记录并列出建议聚焦的 5 个复核面。

**存档首部**：r1–r4 四份均按协议 §2.1 补齐 blockquote（批次/车道/卡/round、模型 `gpt-6-astra`、
`reasoning_effort ultra`、`codex-cli 0.153.3`、命令、审查绑定 SHA、`.stderr` 会话头三行自证并括注行号）。
`*.stderr*` 被 `.gitignore:264` 覆盖，未入库。r5 那份首部如实写「未取得」。


## 八 提交

单卡**独立 commit**（多次 `--amend` 折叠为一条，未 push）：

- header（**95** 字符 ≤100，含批次标记与卡号）：
  `fix(review): 卡状态原子写补 fsync 与 finally 清理 [BATCH-2026-09-18-第十五批 / CARD-CARD-STATES-ATOMIC-WRITE]`
- body 每行 ≤100 字符（`wc -m` 逐行自检，0 行超限）；含 `@spec: concept-identity` 与
  `Co-Authored-By`（commit-msg hook 的 spec-reference 需要其一）。
- lefthook 全程未绕过：`python-typecheck ✔️ (exit: 0)`、`python-lint` 通过、
  `ghost-files` / `mutant-residue-scan` 通过；`spec-sync-flat` / `spec-sync-root` 因 glob 不含
  `backend/app/services/` 而 skip ⇒ **`backend/openapi.json` 未被塞进本 commit**（(j) 不适用，
  收工 `git diff --stat 9c4e7e82 HEAD -- backend/openapi.json` 为空作证）。
- `*.stderr*` 未入库（`.gitignore:264`）；0 字节存档未入库（r5 那份已换成如实的「未取得」记录）。
- **未 push**。工作树干净 ⇒ P4-B 可直接开工。

