# UAT — CARD-RUNTIME-SHA-SURFACE（runtime_sha 运行时文件门扩面 + noexec 调用方自证契约）

> 批次：`[BATCH-2026-09-11-第十四批 / CARD-RUNTIME-SHA-SURFACE]` · 车道 `card-t9-w4`（T9 第 4/4 张）
> 地盘基准 `PREV = 5fa2d401`（= T9-C `CARD-W4-SENTINEL-REBIND` 末 commit）
> 本卡代码 commit（两个，都只改 `backend/scripts/lifespan_isolation_runtime_sha.sh`）：
> `b191a085` 扩面（语义面 7 行）→ `1f63d216` 按 Codex r1 的**纯注释**尾巴（D-32，非注释行 diff 为空）
> 最终 HEAD = `1f63d216`
> 证据目录：`_bmad-output/审查/evidence-runtime-sha-surface/`
> 日期：2026-09-15（机器本地时区，D-18）

---

## 〇 本卡做了什么（一句话）

给「运行时文件门」补上三个原先漏列的已知受害者——`app/data/lancedb_pending_index__*.jsonl`（glob）、
`data/neo4j_memory.json`、`data/llm_call_logs.db`——并同步两个计数常量；`SHELLOPTS=noexec`
那条假绿**如实维持「脚本内不可防」的登记**，只把给调用方的硬要求注释写成可粘贴的断言配方。

**语义面改动恰 7 行**：3 个新监视项 + 2 个计数常量（`EXPECTED_FIXED_COUNT` 3→5、
`EXPECTED_GLOB_COUNT` 1→2）。`git diff` 共 64 增 7 删，其余 57 行全是注释。

---

## 一 三面注入 before/after 对照表

judge = `evidence-runtime-sha-surface/inject_probe.zsh`（`$TMPDIR` 内搭 fake backend，
EXIT trap 无条件 `rm -rf`）。

> ⚠️ **端点观测，不是过程结论（Codex round-2 LOW-4，已采纳收窄）**：每次注入跑前跑后都比了
> 真实工作树**那一个门文件**的 sha，两次都「相同=yes」——它证明的是**该文件的两个采样时刻
> 字节相同**，**不是**「整棵工作树一字节没碰」。全树端点等价另有两条独立证据：
> `git status --porcelain backend/` 全程空，以及 `forbidden-files-unchanged-20260915T193232.txt`
> 里七个禁改文件对 HEAD blob 与 PREV blob 的逐字节核（带能真报 DIFF 的验伪锚）。

| 注入的运行时文件 | 生产写点（默认路径） | 扩面前门 | 扩面后门 |
|---|---|---|---|
| `app/data/lancedb_pending_index__probe.jsonl` | `lancedb_index_service.py` 的 `_journal_stem="lancedb_pending_index"` 经 `namespaced_state_path()` | `unchanged` rc=0 | **`CHANGED` rc=1** |
| `data/neo4j_memory.json` | `neo4j_client.py::DEFAULT_STORAGE_PATH` | `unchanged` rc=0 | **`CHANGED` rc=1** |
| `data/llm_call_logs.db` | `cost_tracker.py::_DEFAULT_DB_PATH` | `unchanged` rc=0 | **`CHANGED` rc=1** |
| **验伪锚** `app/data/not_watched_probe.txt`（不在清单） | —（本来就不该被看） | `unchanged` rc=0 | `unchanged` rc=0 |

- 改前存档：`inject-before-20260915T120909.txt`（末行「工作树门 sha … 相同=yes」，`INJECT-SUMMARY want=unchanged bad=0`、`rc=0`）
- 改后存档：`inject-after-20260915T182248.txt`（同上，`want=CHANGED bad=0`、`rc=0`）

### 1.1 harness 正锚（防「全 unchanged 其实是 harness 坏了」）

只有上表左列会让人担心一件事：**四行全 `unchanged`，也可能是 fake backend 搭错、门根本没跑、
或者结论行 grep 恒不命中**。所以另跑一组正锚：拿**扩面前**的门，对**改前就已在清单里**的
四个形态注入。

| 注入 | 期望 | 实得 |
|---|---|---|
| `data/bug_log.jsonl` | CHANGED rc=1 | CHANGED rc=1 |
| `data/outbox/events.jsonl` | CHANGED rc=1 | CHANGED rc=1 |
| `app/data/vault_index_pending.jsonl` | CHANGED rc=1 | CHANGED rc=1 |
| `app/data/vault_index_pending__probe.jsonl`（glob 分支） | CHANGED rc=1 | CHANGED rc=1 |

存档 `posctl-before-20260915T120935.txt`（`POSCTL-SUMMARY bad=0`、`rc=0`）。
⇒ 上表「三面改前 unchanged」是**监视面的事实**，不是 harness 的假绿。

### 1.2 收窄正证据（证明新 glob 是窄的，不是宽的）

新 glob 必须是**双下划线** `lancedb_pending_index__*.jsonl`。写成单下划线会把人手放的
旁文件收进监视面——那正是 M14（CARD-W4-3b）刚刚收窄掉的假红面。

| 同目录同前缀的旁文件 | 期望 | 实得 |
|---|---|---|
| `app/data/lancedb_pending_index_backup.jsonl`（单下划线） | unchanged | unchanged rc=0 |
| `app/data/lancedb_pending_index.jsonl`（裸名无分隔符） | unchanged | unchanged rc=0 |
| `app/data/lancedb_pending_index__x.jsonl.old`（后缀不是 `.jsonl`） | unchanged | unchanged rc=0 |
| `data/neo4j_memory.json.bak` | unchanged | unchanged rc=0 |
| `data/llm_call_logs.db-wal`（SQLite 边车） | unchanged | unchanged rc=0 |
| **正锚** `app/data/lancedb_pending_index__probe.jsonl` | CHANGED | CHANGED rc=1 |

存档 `narrowness-after-20260915T182319.txt`（`NARROWNESS bad=0`、`rc=0`）。

### 1.3 计数自检同步（带负控输入）

| 场景 | 固定计数 GATE-BROKEN | glob 计数 GATE-BROKEN | `unchanged` | rc |
|---|---|---|---|---|
| 改后门·正常命令 | 0 | 0 | 1 | 0 |
| **负控①** `EXPECTED_FIXED_COUNT` 改成 99 | 1 | 0 | 0 | 1 |
| **负控②** `EXPECTED_GLOB_COUNT` 改成 99 | 0 | 1 | 0 | 1 |

存档 `count-selfcheck-20260915T182320.txt`（`COUNT-SELFCHECK bad=0`、`rc=0`）。
两条负控的变异是否真的落上，脚本内先用 `grep -qE '^EXPECTED_\*_COUNT=99$'` 自证过。
⇒「正常跑没出现 GATE-BROKEN」不是因为计数自检被绕开了，它还活着。

---

## 二 `SHELLOPTS=noexec` 的调用方自证契约

### 2.1 为什么脚本内不可防（不是没修，是修不了）

`SHELLOPTS=noexec` 让 bash **只解析不执行**。门自己的代码——包括它换干净解释器的那句
`exec`、包括所有 fail-closed 分支——正是那个不会执行的东西。实测（`noexec_contract.py`）：

```
[g 先红·真门] rc=0 no_verdict=True out_len=0
```

rc=0、stdout+stderr 长度 0、**没有任何 `RUNTIME-FILES:` 行**，被包裹命令也没跑。
只看 rc 的调用方会把「门压根没跑」读成「通过」。

在脚本里写一个**看起来**能防 noexec 的分支，只会制造假安全感（那个分支同样不会执行），
比如实登记更糟。所以本卡在脚本内**只**做了一件事：把给调用方的硬要求注释写成可粘贴的
断言配方。真正的强制必须落在**免疫 noexec 的进程**里。

### 2.2 断言原文 —— Python 版（推荐，免疫 noexec）

```python
import re, subprocess

# ⛔ 整行精确匹配，不能只判 "RUNTIME-FILES:" 子串
VERDICT = re.compile(r'^RUNTIME-FILES: (unchanged|CHANGED)$', re.M)

p = subprocess.run(["bash", GATE, "--", *cmd], capture_output=True, text=True)
if not VERDICT.search(p.stdout + p.stderr):
    raise SystemExit(f"门未自报结论行 ⇒ 门没跑或已损坏；rc={p.returncode} 不作数")
raise SystemExit(p.returncode)   # 有结论行只说明门跑过了，过没过仍看 rc
```

**两处细节都是承重的（Codex round-1 MEDIUM-1，已采纳）**：

1. **整行精确匹配**。初版只判 `"RUNTIME-FILES:"` 子串——`RUNTIME-FILES: GATE-BROKEN …`
   同样含这个子串，而它是**门损坏**、不是结论。只判子串等于把门自己喊出来的「我坏了」
   读成「门跑过了」。
2. **rc 必须继续传播**。「有结论行」只证明门运行到了终点，**不**代表通过：`CHANGED` 是 rc=1，
   被包裹命令自己的退出码也从这里透出。断言只负责堵住「门没跑」这一类，不替代 rc 判定。

### 2.3 断言原文 —— shell 版（够用，但挡不住 noexec 这一条）

```sh
out="$(bash "$GATE" -- "$@" 2>&1)"; rc=$?
printf '%s\n' "$out" | grep -qE '^RUNTIME-FILES: (unchanged|CHANGED)$' \
  || { printf 'GATE-DID-NOT-RUN\n' >&2; exit 1; }
exit "$rc"
```

### 2.4 实测结论表

| 场景 | rc | 有无合法结论行 | 断言判定 |
|---|---|---|---|
| 验伪锚·空输入 | — | 无 | **1（红）** |
| 验伪锚·`RUNTIME-FILES: unchanged` | — | 有 | 0（放行） |
| 验伪锚·`RUNTIME-FILES: CHANGED` | — | 有 | 0（放行） |
| 验伪锚·`RUNTIME-FILES: GATE-BROKEN — 固定监视项有 3 个, 期望 5 个` | — | **无**（门损坏 ≠ 结论） | **1（红）** |
| 验伪锚·`RUNTIME-FILES: unchanged-ish`（前缀碎片） | — | 无 | **1（红）** |
| 验伪锚·`foo RUNTIME-FILES: unchanged`（非行首） | — | 无 | **1（红）** |
| 验伪锚·`=== RUNTIME-FILES before (x) ===`（快照表头） | — | 无 | **1（红）** |
| rc 传播·`CHANGED` + 门 rc=1 | — | 有 | 透出 **1** |
| rc 传播·`unchanged` + 门 rc=0 | — | 有 | 透出 **0** |
| rc 传播·`unchanged` + 被包裹命令 rc=7 | — | 有 | 透出 **7**（不被吞成 0） |
| **(g) 先红** 真门 + `SHELLOPTS=noexec` | 0 | **无** | **1（红）** |
| **(h) 对照** 正常 run（fake backend） | 0 | 有 `unchanged` | 0（放行） |
| shell 版 · 同一 noexec 环境 | 0 | 无输出 | — （**它自己也没执行**） |
| shell 版 · 正常环境 | 0 | `GATE-RAN rc=0` | 放行 |
| shell 版 · 验伪锚：哑门（rc=0、零输出） | 1 | 无 | **红** |

存档：`noexec-20260915T121020.txt`（改前门·宽判据初版）、
`noexec-after-20260915T182335.txt`（改后门·宽判据初版）、
**`r2-judges-20260915T183912.txt`（最终态·收紧后的整行判据 + 四个新负例 + 三条 rc 传播）**，
三次均 `NOEXEC-CONTRACT: PASS`、`rc=0`。

**⛔ 这一行是本节最要紧的实测**：shell 版断言在同一个 noexec 环境里 **rc=0、输出长度 0**——
它自己也只解析不执行。由此推出本卡的两个「不做」：
1. **不新建 repo 根 bash launcher** 来「防 noexec」：那个壳一样不会执行，立它等于立一个
   看起来有防线、实际没有的东西；
2. **常驻强制不落在 shell 里**：探针 / 契约测试（Python）才是它的家——而那两处**出本卡地盘**，
   登记移交（见 §五.3）。

---

## 三 `llm_call_logs.db` 二进制 sha 稳定性实测结论

门按**逐字节 sha256** 判定。SQLite 的 header 里有 change counter / schema cookie 等字段，
若「只读一次」就让字节变了，把它纳入监视面等于给本门造一个新的假红面——所以这是扩面的
**前提**，不是事后附注。

| 形态 | sha 是否变 |
|---|---|
| 建库 + 写一行（起点） | — |
| ① 默认（读写）连接，只 `SELECT COUNT(*)` | **不变** |
| ② 默认连接再 `SELECT *`（证明不是「只有第一次才变」） | **不变** |
| ③ `file:…?mode=ro` 只读 URI `SELECT` | **不变** |
| ④ **验伪锚**：真 `INSERT` 一行 | **变**（证明本判据不是恒「相同」） |
| ⑤ **验伪锚**：`/usr/bin/shasum -a 256` 与 `hashlib` 结果一致 | 一致（证明本实测代表门的判据） |

存档 `sqlite-sha-stability-20260915T121115.txt`：`SQLITE-SHA-STABILITY: STABLE`、`rc=0`。

**⚠️ 结论的边界（Codex round-1 LOW-2，已采纳并写回门内注释）**：本项只比**主 `.db` 文件**
的字节，`-wal` / `-shm` 边车**不在清单**（收窄表里 `llm_call_logs.db-wal` 判 unchanged 即是
此事实的一条实证）。上面这组实测是在**默认 journal 模式、单连接、无并发**下做的——
换日志模式（如 WAL）或出现并发写者后，覆盖面与误报/漏报边界**需要重新验证，本卡未测**。
初版注释把「将来换 WAL」直接定性成「新的假红面」，那是**超出实测的定性**，已改掉。

**真实长跑下的旁证**：本卡收工那次 `tests/unit` 目录级（5000+ 用例、9 分钟）跑前跑后
对真实工作树的三面各取一次 sha，结果见 §四-A 判据 ⑧ 的 `realtree-before/after` 对照。

---

## 四 DoD-3

### 4-A Claude 已代验（判据 + 存档 + 末行）

| # | 判据 | 存档（`_bmad-output/审查/evidence-runtime-sha-surface/`） | 末行 / 结论 |
|---|---|---|---|
| ① | 锚点现求 + 三面生产写点 + T-13 四方法 + 三面 git-ignored | `anchors-20260915T120752.txt` | `rc=0`；四锚命中、三写点命中、`def .*_with_status` 恰 4 行、`check-ignore` 三行全命中、非忽略文件 rc=1（验伪锚） |
| ② | 三面注入·改前（先红） | `inject-before-20260915T120909.txt` | `INJECT-SUMMARY want=unchanged bad=0` / `rc=0` / 工作树门 sha「相同=yes」 |
| ②′ | harness 正锚（改前门 × 已监视四形态） | `posctl-before-20260915T120935.txt` | `POSCTL-SUMMARY bad=0` / `rc=0` |
| ③ | 三面注入·改后（后绿）+ not_watched 验伪锚 | `inject-after-20260915T182248.txt` | `INJECT-SUMMARY want=CHANGED bad=0` / `rc=0` / 工作树门 sha「相同=yes」 |
| ③′ | 收窄正证据（5 旁文件 unchanged + 1 正锚 CHANGED） | `narrowness-after-20260915T182319.txt` | `NARROWNESS bad=0` / `rc=0` |
| ③″ | **既有监视项未被摘掉**（改后门 × 原四形态仍须 CHANGED） | `posctl-after-20260915T182846.txt` | `POSCTL-SUMMARY bad=0` / `rc=0`，四条全 `CHANGED` rc=1 |
| ④ | 计数自检一致 + 两条负控 | `count-selfcheck-20260915T182320.txt` | `COUNT-SELFCHECK bad=0` / `rc=0` |
| ⑤ | noexec 先红 + 调用方自证后绿（改前门 / 改后门 / **最终态含端到端 rc 传播**） | `noexec-20260915T121020.txt`、`noexec-after-20260915T182335.txt`、`r2-judges-20260915T183912.txt`、**`noexec-e2e-20260915T193310.txt`** | 均 `NOEXEC-CONTRACT: PASS` / `rc=0`；e2e 那份首尾各记门 sha 且相同，`门包 exit 7 ⇒ 外层调用方进程退出码=7`、验伪锚`哑门 ⇒ 外层退出码=1` |
| ⑥ | SQLite 二进制 sha 稳定性（含两条验伪锚） | `sqlite-sha-stability-20260915T121115.txt` | `SQLITE-SHA-STABILITY: STABLE` / `rc=0` |
| ⑦ | 探针契约 file-level 改前 / 改后 / 最终态 | `probe-contract-before-20260915T120815.txt`、`probe-contract-after-20260915T182335.txt`、`probe-contract-final-20260915T183936.txt` | 三次均 `152 passed`（改前那份未 tee 进 `rc=` 行，会话内 rc=0，见 §五.6；另两份 `rc=0`），三次均 `blocked=0, advisory=0, unaccounted=0` |
| ⑦′ | **门探针族真执行**（Codex r1 LOW 的补证，见下方 ⚠️） | `gate-probes-after-20260915T183715.txt`（绑 `b191a085`，33 行完整）、**`gate-probes-final2-20260915T193320.txt`（绑最终 HEAD，37 行完整）** | 两份均 `GATE-PROBES total=27 failed=0` / `rc=0`，各自首尾记门 sha 且相同；final2 另核 `guard_probes` 工作树 sha == HEAD blob sha（证明只 import、没写它） |

> ⚠️ **存档更正（Codex round-2 LOW-1，属实）**：`gate-probes-final-20260915T183936.txt` 那一份
> 被我误经 `tail -4` 过滤，只剩 6 行、没有结束 sha，**不足以支撑**验收单原先「首末各记一次且
> 相同」的说法。已按最终 HEAD **完整重跑**成 `gate-probes-final2-20260915T193320.txt`（37 行，
> 首尾 sha 齐全）；**旧存档保留不删**，⛔ 不事后往历史存档里补写结束 sha。
| ⑧ | `tests/unit` 目录级 开工 / 收工 + 真实树三面 sha 对照 | `unit-open-20260915T120846.txt`、`unit-close-20260915T182504.txt`、`realtree-before-20260915T182504.txt` + `realtree-after-20260915T182504.txt` | 见 §四-A.1 |
| ⑨ | 地盘核（`$PREV..HEAD`，含三条验伪锚） | `scope-20260915T182442.txt`（绑 `b191a085`）、**`scope-final-20260915T184430.txt`（绑最终 HEAD `1f63d216`）** | 两次都只列 `backend/scripts/lifespan_isolation_runtime_sha.sh` 一行；验伪锚①`':(exclude)backend'` rc=0 且输出空（证明 exclude 写法真生效、不是命令没跑成，本机 git 2.50 对 `':!…'` 会 rc=128 空 stdout）；验伪锚② `b191a085..HEAD` 非注释 +/- = **0**（D-32）；验伪锚③ 同一过滤器对 `PREV..b191a085` = **7** 行并逐行打印（证明它不是恒空） |

> ⚠️ **存档更正（如实登记）**：`scope-final-20260915T184400.txt` 那一份把验伪锚③的期望写成
> 「3 行」，实测 7 行 —— **7 是对的**（3 个新监视项 + 2 个计数常量各出现一次 `-` 和 `+`），
> 错的是我写的期望值，不是判据。已另跑 `scope-final-20260915T184430.txt` 更正并逐行打印；
> **旧存档保留不删**（事后改证据比当场写错更糟）。
| ⑩ | negctrl 镜像漂移（只读登记，不改 T8 文件） | `negctrl-mirror-20260915T121031.txt` | `RUNTIME_FILE_RELPATHS` 仍 3、`RUNTIME_FILE_GLOBS` 仍 1，`:128`「与 runtime_sha.sh 监视清单保持一致」已断裂 |
| ⑪ | Codex 多轮（gpt-6-astra / ultra） | `_bmad-output/审查/codex-review-CARD-RUNTIME-SHA-SURFACE[-r2].md` | 见 §七 |

> ⚠️ **⑦ 的措辞更正（Codex round-1 LOW，作者复核后确认它是对的）**：
> `tests/unit/test_live_port_guard_contract.py` 里对 `lifespan_isolation_guard_probes.py`
> 的两处提及**都在 docstring**（`:8` / `:939`），它**不调用** `probe_shell_injections()`。
> 所以「152 passed」只证明 live_port_guard 那套契约绿，**证明不了**门头那 19 条 shell 探针
> 与 M15 glob 探针族还绿——那些探针的聚合驱动是 **`lifespan_isolation_guard_probes.py`
> 自己的 `main()`**（`:2155` 起逐条列出，`:2179` `results.extend(probe_shell_injections())`），
> 那是 `__main__` 脚本态，**不被任何 pytest 套件收集**。
> ⚠️ 本条我一度写成「驱动方是 `negative_control.py`」——**写反了**（Codex round-2 LOW-3
> 抓到）：`negative_control.py` 只在 docstring `:82` / `:190` 里提到 guard_probes，并不调用它。
> 补救 = ⑦′：`run_gate_probes.py` 只 **import**（不改）guard_probes，只调用与本门有关的
> 那几支——`probe_shell_injections()`（19 条）+ `shell-selftest-load-bearing` +
> `shell-can-report-changed` + 五条 `runtime-glob-*` + `runtime-legacy-journal-watched`，
> **刻意不跑 socket / 端口族探针**（其中一条用真实受拦端口号，本批禁连）。
> 实得 **27 条全 ok、failed=0**，含 `shell-probe-roster-matches-declared-count`
> （门头「19 条」声明与 AST 实测一致）与 `runtime-glob-pattern-neutralized`
> （把原 glob 换成永不匹配后门确实变瞎 ⇒ 那条 glob 项承重、没被本卡的新 glob 顶替）。

#### 四-A.1 `tests/unit` 目录级（R-B14-3 口径：先 `cd backend`，`--ignore` 用相对路径）

- 基线 `evidence-b14/unit-red-baseline-08100483.txt`，`grep -vc '^#'` = **64**（R-B14-2 唯一口径；
  同次验伪锚 `grep -c '::'` = **65**，证明两口径确实不同、不是随便取一个数）。
- **开工对齐**：`35 failed, 5145 passed, 48 skipped, 23 xfailed, 29 errors in 548.69s`，
  抽 nodeid 共 **64** 条，与基线 `diff` **完全为空**（rc=0）。
- **收工**：见下方「收工结果」小节（本卡零 test/app 改动、只动 `backend/scripts/**`，预期 diff 空）。

#### 四-A.2 收工结果

- **收工跑**：`35 failed, 5145 passed, 48 skipped, 23 xfailed, 29 errors in 512.76s`，
  存档 `unit-close-20260915T182504.txt`（末行 `rc=1` —— 红基线本身非空，rc=1 是预期，
  判据是 nodeid 集合而不是 rc）。
- 抽 nodeid 共 **64** 条。
  - `diff base.nodeids close.nodeids` → **空**（rc=0）：与红基线逐条相同，**零 `>` 行**。
  - `diff open.nodeids close.nodeids` → **空**（rc=0）：与本卡开工那跑逐条相同。
  ⇒ 本卡**没有引入任何新红**，也没有掩盖任何既有红（数量与身份两侧都对上了，
  不是只对数量——64 条 nodeid 逐条一致）。
- ⚠️ 判据里只出现 `$RUN` / `$BASE` 两个变量，未用 `unit-close-*.txt` 这类 glob
  （多份存档时 `grep` 会加文件名前缀，`close.nodeids` 会作废、`diff` 全 `>` 假阻断）。
- **真实工作树三面 sha 跑前 / 跑后对照**（`realtree-before-20260915T182504.txt` vs
  `realtree-after-20260915T182504.txt`，`diff` 空 ⇒ `REALTREE-STABLE`）：

  | 文件 | 跑前 | 跑后 |
  |---|---|---|
  | `backend/data/neo4j_memory.json` | `7fc2217a…3efd1` | `7fc2217a…3efd1`（**未变**） |
  | `backend/data/llm_call_logs.db` | absent | absent |
  | `backend/app/data/lancedb_pending_index__*.jsonl` | absent（glob 无匹配） | absent |

  ⚠️ **诚实读法（Codex round-2 LOW-4 收窄后）**：这是**两个采样时刻**的端点比较，不是过程结论。
  后两行「跑前跑后均不存在」**不能排除**期间被创建后又删除；`neo4j_memory.json` 那一行也只是
  「两个端点字节相同」，中途写进去又改回原内容同样会得到这个结果（门本身也只比首尾两个时刻，
  这是它既有的诚实边界）。所以这一跑支持的主张只有：**这三个路径在跑前与跑后的端点状态一致**。
  见 §五.2。
- 两跑（开工 548.69s / 收工 512.76s）期间另一条车道 `card-t1-lance` 在同机跑同一套件、
  共用同一个 `card-v5-lance/backend/.venv` —— 耗时不可跨批直接比较，但判据不受影响
  （`-p no:cacheprovider` + `PYTHONDONTWRITEBYTECODE=1`，且判据是 nodeid 集合）。
- 两跑均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` ⇒ 零偷连。

### 4-B 你来验（零技术词）

> 我做 X → 我看到 Y → 我感觉 Z

**我做 X**：跑一次完整的自动检查。
**我看到 Y**：如果这一轮检查过程中，那几份平时由程序自己记录、本来不该被碰的记录文件
（包括那份用来记花销的、那份在后台连不上时顶替用的、还有那份排队用的）被悄悄改动了，
现在系统会明确说一声「这些被改了」，并且当场停下来，而不是一声不吭地说「一切正常」。
我另外放了一个**本来就不该被管**的文件在同一个地方试，系统没有去管它，说明它不是见谁都拦。
**我感觉 Z**：踏实。以前这几份记录被动过我是看不出来的；现在它会当面告诉我，而且不会乱喊。

---

## 五 本卡未证明什么（≥4，必填）

1. **未证明「生产一定写默认路径」**。本卡只证明了**默认**路径被监视：
   `neo4j_client.py::DEFAULT_STORAGE_PATH` / `cost_tracker.py::_DEFAULT_DB_PATH` /
   `lancedb_index_service.py` 的 stem。生产若用 settings 把 storage_path / db_path /
   state_dir 指到别处，写到别处的那一份本门看不到。这与本门「具名清单、不是全盘零写入」
   的定位一致，但**不能**被读成「这三类数据被全面保护了」。
2. **`llm_call_logs.db` 在真实长跑下的稳定性只有一次观测，且是在它 absent 的前提下**。
   本卡的 STABLE 结论来自 fake backend 与受控的 SQLite 只读实验；真实工作树上这个文件
   **当前不存在**（`absent`），所以 §四-A ⑧ 的真实树对照实际上只证明了「这一跑没有把它
   创建出来」，**没有**证明「它存在且被读时也稳定」。换 WAL 模式、或将来有别的写者，
   都可能让它变成新的假红面。
3. **noexec 的常驻强制没有落地**。本卡只把断言写成注释里的配方并实测过它成立；把它钉成
   一条常驻探针（`guard_probes.py` 新探针 + 门头花名册 19→20 + 契约测试用例）**出本卡地盘**，
   见 §六「台账待登记」3。⇒ 今天仍然没有任何自动化的东西拦得住「调用方只看 rc」这个错法。
4. **negctrl 镜像未同步，扩面后门与镜像的覆盖面不再等价**。
   `lifespan_isolation_negative_control.py` 仍是 3 固定项 + 1 glob，门已是 5 + 2。
   该文件属别的车道地盘（T8），本卡只登记不改。⇒ 负控脚本对新增三面**没有**正证据锚点。
5. **`*_with_status` 四个兼容壳（T-13）本卡未实现任何检测**。它是「补丁/mock 落在兼容壳
   而非真实路径」的**源码/AST 扫描面**，与本门的「运行时文件字节快照」不同类，无法进本门；
   另立卡（见「台账待登记」4）。
6. **改前那次探针契约 file-level 的 rc 未进存档**。`probe-contract-before-…txt` 的末行是
   pytest 自己的汇总行 `152 passed … in 1.39s`（该行本身即判据），但 `rc=` 那一行当时只打到
   会话里、没有 `tee -a` 进文件。门改后已无法在同一棵树上复现「改前」状态，故**不追补**——
   如实登记，而不是事后往存档里补一个数字。
7. **未证明门的监视面对「中途改回」免疫**。门只比首尾两个时刻，这是它既有的诚实边界
   （文件开头已写），本卡三个新面同样继承这条边界，未做任何改善。
8. **`run_gate_probes.py` 只覆盖门相关探针族，不是「全部探针绿」**。它跑的是
   `probe_shell_injections()`（19 条）+ selftest + can-report-changed + 五条 runtime-glob +
   legacy-journal，共 27 条；`guard_probes.py` 里的 **socket / 端口 / ledger / install-order
   等族本卡刻意没跑**（其中一条用真实受拦端口号，本批禁连 7691/7687）。
   同样地，`lifespan_isolation_negative_control.py` 自己那套驱动（含变异族）**本卡未跑**。
   ⇒ 「27 条全绿」的主张面就是这 27 条，不要外推成「负控脚本仍与门等价」——那条恰恰
   已经断了（见「台账待登记」2）。
9. **`llm_call_logs.db` 的 WAL / 并发形态未测**（见 §三 边界）。
10. **三个新面在「非默认 journal 模式」「settings 覆盖路径」「多写者并发」下的表现均未测**——
   本卡的全部实测都在单进程、fake backend 或受控临时库里完成。

---

## 六 台账待登记条目（≥4，必填，主 session 代录）

1. **口径更正①（已裁，登记时引编号即可）**：地盘 token `scripts/runtime_sha.sh` 在主干
   **不存在**，真门 = `backend/scripts/lifespan_isolation_runtime_sha.sh`。依 **R-B14-5**
   （真名 + 归 T9）与 **R-B14-4**（地盘扩充已逐文件批准）；手册 §一 `:66` 已同步。
   **仅设计稿 §3 `:78` 的旧字面待主 session 归档时更正**（车道不改设计稿）。
2. **negctrl 镜像同步（归 T8 / 主 session）**：`lifespan_isolation_negative_control.py` 的
   `RUNTIME_FILE_RELPATHS` 需 3→5、`RUNTIME_FILE_GLOBS` 需 1→2，连带 `:271` 的
   `{len(...)} 固定项 + {len(...)} glob` 文案与 `:128`「与 runtime_sha.sh 监视清单保持一致」
   这条不变量。⚠️ 该文件 `:158-160` 附近的注释现在自相矛盾：它写着「同族的
   `lancedb_pending_index__<key>.jsonl` … 本卡只登记移交，不在此扩面（扩面会让 runtime_sha
   变严，属于另一张卡的范围决策）」——那张卡（本卡）已经扩了，这段注释需一并更新。
3. **noexec permanent 强制移交**：新探针 `shell-shellopts-noexec-caller-requires-sentinel`
   （落 `lifespan_isolation_guard_probes.py`）+ 门头花名册 **19→20** + 对应
   `test_live_port_guard_contract.py` 用例（R-B14-4 已判归 T9-B 的面）。
   ⛔ 归属前置条件：`guard_probes.py` **全批仍无地盘归属**，需主 session 先裁。
   实现要点已实测：断言必须跑在**非 bash 进程**里（Python/pytest），因为 shell 版调用方
   在同一 noexec 环境下自己也不执行（§二.4 实测行）。
4. **T-13 源码扫描卡（另立）**：`*_with_status` 四个兼容壳的「补丁/mock 落壳而非真实路径」
   检测——`rag_service.py:344 get_weak_concepts_with_status` /
   `memory_service.py:1087 get_review_suggestions_with_status` /
   `memory_service.py:2282 search_memories_with_status` /
   `memory_service.py:2485 search_error_memories_with_status`。
   它是源码/AST 扫描面，与 runtime_sha 的运行时文件字节快照**不同类**，不进本门。
5. **`lifespan_isolation_guard_probes.py` 全批无地盘归属**（`test_live_port_guard_contract.py`
   已由 R-B14-4 判归 T9-B，此条只剩 guard_probes）。建议主 session 明确其归属车道——
   第 3 条的落地被它卡着。
6. **LanceDB 恢复路径的两类清单外写点（Codex round-1 MEDIUM 移交，本卡不扩面）**：
   `backend/app/services/lancedb_index_service.py:226` 在恢复时会隔离出**裸名**
   `lancedb_pending_index.jsonl`，并经 `backend/app/core/vault_state_paths.py:197` 改名为
   `.pre-g25.bak[.N]`——**两者都不在**当前门的监视面（本卡的 glob 是双下划线命名空间形态）。
   ⚠️ 这与 `vault_index_pending.jsonl` 当年的处境**同型**：那个旧固定名正是因为 M14 收窄后
   glob 不再覆盖它，才被显式补进 `WATCHED_FIXED` 的。
   ⛔ 本卡**不自行扩**：卡文 (d) 把扩面面写死为三项 + 计数 3→5 / 1→2，加第四个固定项属越界；
   Codex 自己也判「另卡决定是否增加精确项，保留本卡双下划线 glob」。⇒ 另立卡评估。
7. **`test_live_port_guard_contract.py` 不驱动那 19 条 shell 探针**（实测：两处提及均在
   docstring `:8` / `:939`）。⇒ 目前唯一的聚合驱动是 **`guard_probes.py` 自己的 `main()`**
   （`:2155` / `:2179`），那条路径**不被任何 pytest 套件收集**。建议主 session 评估把门探针族
   接进某个常驻套件（与「台账待登记」3 的 noexec 常驻探针是同一个落点问题）。
8. **批级环境观察（非缺陷，供排批参考）**：本卡两次 `tests/unit` 目录级期间，另一条车道
   （`card-t1-lance`）在同机跑同一套件、共用同一个 `card-v5-lance/backend/.venv`。
   两跑各约 9 分钟（548s / 收工那跑见 §四-A.1）。并发不影响判据（`-p no:cacheprovider`
   + `PYTHONDONTWRITEBYTECODE=1`），但**目录级耗时不可跨批直接比较**。

---

## 七 Codex 轮次与裁定（gpt-6-astra / `ultra` / codex-cli 0.153.3）

| 轮 | 绑定 | 存档 | BLOCKER | HIGH | MEDIUM | LOW | 处置 |
|---|---|---|---|---|---|---|---|
| r1 | `5fa2d401..b191a085` | `codex-review-CARD-RUNTIME-SHA-SURFACE.md` | **0** | **0** | 1（本卡面） | 1（本卡面）+ 2 条证据限制 | 两条**全部采纳并修**（见下） |
| r2 | `5fa2d401..1f63d216`（**最终 HEAD**，审毕时 HEAD 未变、工作树门文件与该提交逐字节一致） | `codex-review-CARD-RUNTIME-SHA-SURFACE-r2.md` | **0** | **0** | **0** | 4（全在证据/措辞面） | 四条**全部采纳并修**，见下 |

> **⇒ D-15 条件满足**：绑最终 HEAD 的这一轮 **BLOCKER = 0、HIGH = 0**（MEDIUM 也是 0）。
> r2 结论原文：「源码复核 PASS；补充证据 PARTIAL。原 MEDIUM-1、门内 LOW-2 均已修好，
> 未发现新的 BLOCKER / HIGH / MEDIUM。」
> 四条 LOW 的整改**只动 `_bmad-output/`**（判据脚本 + 本验收单），门文件一字未改
> ⇒ 按协议「只改 `_bmad-output` 不算」，不触发新一轮，最终 HEAD 仍是 `1f63d216`。

### r2 四条 LOW 的处置（均采纳，无驳回）

| 级别 | 意见 | 判断 | 处置 |
|---|---|---|---|
| LOW-1 | `gate-probes-final-…183936.txt` 只有 6 行、无结束 sha，与「首末各记一次且相同」不符 | **属实**——我误加了 `tail -4` | 按最终 HEAD **完整重跑** → `gate-probes-final2-20260915T193320.txt`（37 行，首尾 sha 齐全 + guard_probes sha 对 HEAD blob 核）；旧存档保留不删 |
| LOW-2 | rc=7 传播只用人工构造的 `CompletedProcess`，未端到端 | **属实** | 函数级那组明确改标为「人工结果对象」，**另加真端到端**：真门包 `exit 7` ⇒ 外层调用方进程退出码 **7**；验伪锚哑门 ⇒ 外层 **1**（存档 `noexec-e2e-20260915T193310.txt`） |
| LOW-3 | runner 注释把探针驱动入口写成 `negative_control.py`，实际是 `guard_probes.py` 自己的 `main()`（`:2155`/`:2179`） | **属实，我写反了** | 实测复核后更正 runner 注释与验收单两处说法；`negative_control.py` 只在 docstring `:82`/`:190` 提及、不调用 |
| LOW-4 | 「门 sha 相同＝工作树零碰」「absent→absent」把端点观测放大成过程结论 | **属实** | 两处均收窄为端点结论，并写明「期间创建后删除 / 中途改回」都不能被这组观测排除；全树端点等价改引 `git status` 与七文件 blob 核 |

> **轮次口径**：`1f63d216` 相对 `b191a085` 是**纯注释尾巴**（非注释行 diff 为空，
> 过滤器带验伪锚自证），按 **D-32 不占轮次、不重置**；送 r2 是为了让**末轮绑最终 HEAD**。

### r1 两条本卡面意见的处置（均采纳，非驳回）

| 级别 | 意见 | 判断 | 处置 |
|---|---|---|---|
| MEDIUM-1 | Python 配方只判 `RUNTIME-FILES:` 子串（`GATE-BROKEN` 也满足）且不传 `p.returncode` | **成立，两点都对** | 改为整行精确匹配 + 原样传播 rc，并写明两者承重；判据脚本同步收紧并补四个负例 + 三条 rc 传播实测 |
| LOW-2 | WAL 措辞把未验证行为直接定性为「假红面」 | **成立** | 改为「只比主 `.db` 字节；`-wal`/`-shm` 不在清单；实测限默认 journal 模式单连接无并发，换模式需重新验证」 |

### r1 两条「证据限制」的补正

| r1 的话 | 作者复核 | 现状 |
|---|---|---|
| 「`realtree-before` 没有配对 after」 | **当时属实**——after 是在 Codex 开审之后、目录级长跑结束时才落盘的 | 两份都在，`diff` 为空；但**不据此**主张「整棵树一字节未碰」（三行里两行前后都是 `absent`），§五.2 已如实登记 |
| 「`152 passed` 不能当 shell/glob 探针执行证明」 | **完全正确**，实测契约测试对 guard_probes 的两处提及都在 docstring（`:8`/`:939`），不调用 `probe_shell_injections()` | 补 `run_gate_probes.py`（只 import 不改 guard_probes，只跑门相关族）⇒ **27 条全 ok、failed=0**，首末各记门 sha 且相同 |

### r1 两条移交（不计本卡缺陷）

已分别收进「台账待登记」2（negctrl 镜像 3+1 未同步）与 6（LanceDB 恢复路径的裸名与
`.pre-g25.bak[.N]` 不在监视面）。

---

## 八 硬边界自证

| 禁改项 | 实测 |
|---|---|
| `lifespan_isolation_guard_probes.py`（含门头「19 条」花名册） | 未改；门内「由 **19 条** shell 探针承重」那句逐字未动（`:80`），花名册区间的结束锚「数字与清单不一致」仍在其后（`:105`），区间顺序未被本卡的编辑打乱 |
| `lifespan_isolation_negative_control.py`（T8 地盘） | 未改，只 `grep` 只读登记漂移 |
| `test_live_port_guard_contract.py`（T9-B 面） | 未改，只跑（改前 / 改后 / 最终态共三次，均 152 passed） |
| `guard_probes.py` 被 `run_gate_probes.py` **import** | 只 import 不改：跑前跑后该文件 sha 未取（如实登记），但 `git status --porcelain` 全程无 `backend/` 条目、地盘核也只列门一个文件 ⇒ 未被写入 |
| `live_port_guard.py` / `guard_plugin.py` / 两个 conftest（T9-A~C 交付） | 未改 |
| `backend/app/**`、`backend/tests/**` | 未改 |
| 任何 fail-closed 分支 | 门自证 `SELFTEST_EXPECTED`、两条计数自检、compgen 自检、glob 排序 fail-closed、before/after 判定段、`-u SHELLOPTS`——逐条 `grep` 仍在且未被改成放行 |
| 脚本内 noexec「防御」 | 未新增任何分支；`bash -n` rc=0；语义面改动逐行列出 = 3 监视项 + 2 计数常量 |
| repo 根 bash launcher | 未新建（理由见 §二.4） |
| live vault / 7691 / 7687 / `fsrs_bridge.py` / `decay_beta.py` | 未触及；两次 unit 跑均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |
| 台账 / push / `*.stderr*` 入库 | 未改台账、未 push、`.stderr` 由 `.gitignore` 覆盖不入库 |
