# UAT-CARD-W4-GUARD-TAIL-R2（2026-09-18）

> **批次** `[BATCH-2026-09-18-第十五批 / CARD-W4-GUARD-TAIL-R2]` · 车道 `card-p9-testinfra`（分支 `card/p9-testinfra`）· 本车道第 1/3 张
> **B15_BASE** `9c4e7e82` · **本卡 = 单个 commit**（代码定稿于 `009c61d2`；证据、prompt 与本单以 `--amend` 并入同一 commit，
> 因此 SHA 随之前移。**末轮 Codex 绑定 SHA = `ec245c8c`（见 §6）**；最终 commit 的 SHA 无法写在它自己里，
> 按协议 §1 以**代码树**判绑定：`git --no-pager diff --stat --no-color ec245c8c HEAD -- . ':(exclude)_bmad-output'`
> 为空即仍绑定（收工实测为空）。代码面自 `009c61d2` 起零改动，历次 `--amend` 只动 `_bmad-output/`）
> **终态字段（收工重算）**：代码改动 5 文件 / 660 insertions / 25 deletions；新增用例 **24** 条（契约 6 + sentinel 13 + 回归锁 5，按 pytest item 数）；Codex 轮次见 §5
> **证据目录** `_bmad-output/审查/evidence-w4-guard-tail-r2/`
> **来源** 台账 `:105`（T9-A「4 行修复无常驻门」）+ T9-A/T9-B/T9-C 三份验收单的「台账待登记」段 + 裁定书第十四批 §2.7（CARD-W4-A-REGRESSION-LOCK 并入本卡）

---

## 0 第 0 分钟

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-p9-testinfra` ✅ |
| 分支 | `card/p9-testinfra` ✅ |
| `git rev-parse --short=8 HEAD`（开工） | `9c4e7e82` = B15_BASE ✅ |
| `git status --porcelain`（开工） | 空（0 行）✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均存在 ✅ |
| pyright 自证 | `test -x /…/card-v5-lance/backend/.venv/bin/pyright` → 存在 ✅（本卡不改 `backend/app`，自证只为环境完整性） |
| `backend/.venv/bin/python --version` | **Python 3.14.4**（`ast.TypeAlias` 门依赖它） |
| unit 红基线自证 | `grep -vc '^#' evidence-b15/unit-red-baseline-9c4e7e82.txt` → **33** ✅ |
| 手册 P9 行（只读主干树，未改） | `2026-09-18-第十五批开跑手册-11车道33卡.md:455`：`\| **P9** \| card-p9-testinfra \| **P9-A**（CARD-W4-GUARD-TAIL-R2） \| P9-A → P9-B → P9-C \| C2-07 首张（W4 是离线测试禁连 7691 的唯一防线）；判据绑 blocked= 次数 + 失败正文唯一（协议 §3），不绑 nodeid。两个 conftest 唯一写者 = 本车道…` |

**§〇 事实逐条复核**：卡文 §〇 的 11 行 file:line 全部 `sed -n` / `grep -nF` 实测**逐字一致，零漂移**
（`契约 :1334/:1366/:1395-1402/:1861/:1897`、`guard :1467/:1470-1471/:1494/:1500-1501/:1531/:1544/:1551/:1556`、
`sentinel :77-82/:89-93/:102/:173/:195/:335`、`hygiene_snapshot_tristate.py:27`、
`grep -c TypeAlias live_port_guard.py` → **0**、两套件 `def test_` = 102 / 64、
`test_w4_a_regression_lock.py` 不存在、`evidence-w4-guard-tail-r2/` 与 `codex-review-CARD-W4-GUARD-TAIL-R2*` 主干均不存在）。

---

## 1 DoD-3 §4-A（Claude 已代验，逐条贴证据）

### 1.1 TypeAlias：先红 → 后绿 + AST 门验伪锚

| | 存档 | 实测 |
|---|---|---|
| 先红 | `typealias-red-20260918T165609.txt` | `python: 3.14.4` / `TypeAlias nodes: 2` / **`VERDICT: not raised (漏面在位)`** |
| 后绿 | `typealias-green-20260918T171257.txt` | `TypeAlias nodes: 2` / **`VERDICT: raised install() 里出现了延迟执行体 ['type H', 'type R']`** |
| AST 门（改前） | `ast-gate-before-20260918T165646.txt` | `HEAD deferred` 8 项、**不含** TypeAlias；`BASE deferred` 同 8 项 |
| AST 门（改后） | `ast-gate-after-20260918T172651.txt` | `HEAD deferred` 9 项、含 `getattr(ast, 'TypeAlias', ())`；**`BASE deferred` 仍 8 项不含**；`FALSIFICATION-ANCHOR: OK（BASE 恒不含）` |

**为什么不能用 grep**：契约文件 docstring 里改前就有 **2 处** `ast.TypeAlias` 字样（Codex r5 的登记原文），
`grep -c TypeAlias` 改前即非 0 ⇒ 文本判据恒假绿。门脚本 `evidence-w4-guard-tail-r2/ast-gate.py`
只数 `_refuse_to_guess_on_deferred_execution` 体内 `isinstance(node, …)` 第二实参的**类型表达式集合**。

### 1.2 回归锁三格 + 负控 A 红

| | 存档 | 实测 |
|---|---|---|
| 改前（修法在位） | `lock-green-before-20260918T171059.txt` | `collected 5 items` / **`5 passed`** —— 锁绑的是**当前**修法，且父进程零账 |
| 负控段②（删掉 T9-A 那层嵌套 try） | `negctl-2-20260918T171143.txt` | 跑前 `c395951a…` → 变异后 `2657214828…` → 还原后 `c395951a…`（三态四行）；**A 格 `FAILED … assert 0 == 3`**、B/C `passed`（`1 failed, 4 passed`） |

三格构造：A = 账本指向目录 **且** stderr 已关闭（缺陷恰落此格）/ B = 只坏落盘 / C = 只坏 stderr。
DD-03：真子进程 + 真 `atexit` + 真文件系统；受拦事件由 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))`
**合成**，不建立任何真实连接；账本路径由 `tmp_path_factory` 派生；子进程显式 `pop` 掉 `W4_GUARD_REQUIRE_BLOCKED_TARGET`。
CHILD 正文与冻结脚本 `three-run-abc.py` **逐字相同**（程序化比对 `True`；只有三引号定界符因 `ruff format` 由 `r'''` 变 `r"""`）。

### 1.3 截断门（真实文件权限，非 monkeypatch）

存档 `truncation-gate-before-20260918T171544.txt`：`id -u = 501`（**非 root**）、
`collected 158 items / 157 deselected / 1 selected`、**`PASSED`**（不是 skip、不是 rc=5 空收集）。

- 该行为主干已具备、只是**无门** ⇒ 本条属「补常驻门」，其「先红」形态由负控段③给出。
- 权限打在**账本文件自身** `chmod 0o400`（`try/finally` 恢复 `0o600`）——不是父目录：对已存在的文件
  `open(path,"w")` 只查文件自身写权限，目录 `0o500` 挡不住截断。
- 既有 `test_publish_ledger_refuses_stale_even_after_a_failed_write` 用 monkeypatch 让 `write_ledger` 抛，
  文件**根本不存在**（它自己末条断言就是 `assert not Path(path).exists()`），钉不到「旧内容保留」。

### 1.4 迟到路径：红 → 绿

| | 存档 | 实测 |
|---|---|---|
| 先红 | `named-red-20260918T171502.txt` | `2 failed, 156 passed`；红在 `_CustomBaseException: 落盘期 BaseException` 与 `assert ['Exception'] == ['BaseException']` |
| 后绿 | `late-path-green-20260918T171703.txt` | `collected 158 items` / **`158 passed`** |
| 负控段⑤（`:1501` 拆回 `except Exception`） | `negctl-5-20260918T173630.txt` | `290fc5b1…` → `a6bbf15d…` → `290fc5b1…`；**两条迟到路径用例红**（行为面 + 结构面），print 排查那条绿（对照） |

`live_port_guard.py` 的 diff **恰 4 行**（`grep -c '^[-+][^-+]'` → 4）：`:1494` docstring 一句 ± + `:1501` 一行 ±。

**全文件 print 排查**（新契约用例 `test_every_print_on_forced_exit_paths_sits_in_a_baseexception_try_body`）：
对 `_final_accounting` / `_audit_hook` / `_rewrite_ledger_after_late_record` 三函数建父指针表，
逐个 `print` Call 找**最近的 `ast.Try` 祖先**并报出它落在哪个**字段**，要求 `slot == "body"` 且该 Try 至少一个
handler 是 `BaseException`。这是对冻结裁判 `ast-protected.py:17`（`a.lineno < n.lineno <= a.end_lineno`
= 落在**整个 Try 行区间**即判 protected）的口径收窄——`handlers` / `orelse` / `finalbody` 是它的盲区。
实测三函数全部合规。**冻结脚本本身不改不删**，保留为历史证据、不再作裁判。

### 1.5 sentinel 五条（+ 对照）：红 → 绿

先红存档 `sentinel-red-20260918T172006.txt`（`7 failed, 73 passed`），红的落点逐条如下：

| 用例 | 先红落点 |
|---|---|
| `test_record_echo_without_closing_paren_is_not_an_orphan` | `W4LedgerConflict: 记录块自报 1 条，紧随其后还有一条记录行` ← 前缀匹配把回显当记录（假红 rc=2） |
| `test_second_owner_separator_makes_the_boundary_unjudgeable` | `DID NOT RAISE` |
| `test_second_on_thread_separator_makes_the_boundary_unjudgeable` | `DID NOT RAISE` |
| `test_truncated_final_ledger_line_is_refused_not_parsed` | `DID NOT RAISE` |
| `test_corrupted_summary_line_is_refused_not_silently_dropped` | `DID NOT RAISE` |
| `test_summary_line_missing_a_field_is_refused` | `DID NOT RAISE` |
| `test_verbatim_echo_of_a_claimed_record_is_not_an_orphan` | `W4LedgerConflict: 有 1 条完整的记录行不属于任何自报条数的记录块` ← 孤儿兜底误伤逐字回显 |

后绿：`named-green-postfmt-20260918T172853.txt` → `collected 243 items` / **`243 passed`**
（= 开工 219 + 新增 24；开工侧 `named-open-20260918T170504.txt` 为 `219 passed`）。
补记进程 rc 的同口径一跑见 `named-close-rc-*.txt`（首部带 HEAD 与两个 support 文件的 sha256，末行 `rc=0`）。

⚠️ **一条自述已被 Codex r1 证伪并由本卡独立复现（存档 `codex-r1-medium-verify-*.txt`）**：
送审自述第 5 条写「四条改法全部是收紧，**没有任何输入因此从红变绿**」—— **不成立**。
`_BODY_RE` 由前缀匹配改成全匹配后，**块外被截断的记录行**（缺右括号）从「判孤儿 ⇒ rc=2」
变成「不算记录 ⇒ 被忽略」。实测同一份输入：BASE(`9c4e7e82`) `main([A,B])` → **2**，HEAD → **0**，
而 A 档里那条 `- ('127.0.0.1', 7691) on thread OtherThread (owner=` 携带的**第二身份**被静默丢掉。
这正是卡文 (d)① 明令要求的那一步（「无右括号回显从此不算记录、不算孤儿」，收的是 T9-C 26 的假红），
所以是**有意的方向交换**，不是意外；但「只收紧不放宽」这句话是错的，在此更正。详见 §5 台账 ⑩。

### 1.6 结构判据（改前 X / 改后 Y 成对）

存档 `struct-before-20260918T165626.txt` / `struct-after-20260918T172651.txt`：

| 判据 | 改前 | 改后 |
|---|---|---|
| ① `grep -c 'ast, "TypeAlias"' 契约` | 0 | **3** |
| ② `grep -c '已知但本卡未修的一条' 契约` | 1 | **0** |
| ② `grep -c 'CARD-W4-GUARD-TAIL-R2' 契约` | 0 | **2** |
| ③ `sed -n '1501p' guard` | `except Exception:  # noqa: BLE001 —— 见上：绝不阻断 os._exit` | `except BaseException:  # noqa: BLE001 —— 与 _audit_hook :821 同型：…` |
| ④ `grep -c '\.match(' sentinel` / `'\.fullmatch('` | 9 / 0 | **4 / 8** |
| ⑤ `grep -c 'W4LedgerConflict(' sentinel` | 11 | **15**（⚠️ 卡文预期 14，见 §3 偏离 ②） |
| ⑥ `test -f test_w4_a_regression_lock.py` / `def test_` | false / — | **true / 3**（parametrize 展开 5 item） |
| ⑦ AST 门 `deferred_types` | 不含 TypeAlias | **含**；验伪锚 `BASE deferred` 恒不含 |

### 1.7 负控五段（每段各只拆一层；EXIT trap 无条件还原；跑前/变异后/还原后 shasum 三态）

| 段 | 拆掉的那一层 | shasum 三态 | 结果 |
|---|---|---|---|
| ① | 契约里新加的 `ast.TypeAlias` 分支 | `6d233a37…` → `65618450…` → `6d233a37…` | `4 selected`；`test_type_alias_…` **红在 `DID NOT RAISE <AssertionError>`**；两个顺序门 + 反向锚 **绿**（对照） |
| ② | T9-A 的嵌套 `try/except BaseException`（冻结变异器 `nc-remove-protection.py`） | `c395951a…` → `26572148…` → `c395951a…` | 回归锁 **A 格红在 `assert 0 == 3`**、B/C 绿 |
| ③ | `_PUBLISHED_SEQ = seq` 挪到 `write_ledger` 之后 | `290fc5b1…` → `5a74d638…` → `290fc5b1…` | 新截断门红在「**发布序没有先行推进** `assert 7 == 9`」；既有 `:1776` 同时红在「陈旧快照反而写成功了」；两条对照（`refuses_a_stale_snapshot` / `accepts_a_newer_snapshot`）绿 |
| ④c | (d)① 那一层的**整体**逆操作（`_BODY_RE` 右锚 1 处 + 三处 `fullmatch`） | `eb6cd5aa…` → `eb35b0cb…` → `eb6cd5aa…` | **恰 1 红**：`test_record_echo_without_closing_paren_is_not_an_orphan`，红在「紧随其后还有一条记录行」；其余 **79 绿** |
| ⑤ | `:1501` 拆回 `except Exception` | `290fc5b1…` → `a6bbf15d…` → `290fc5b1…` | 迟到路径两条（行为面 + 结构面）红；print 排查那条绿（对照） |

⚠️ **段④ 与 ④b 是两次失败的拆法，一并入库不删**（`negctl-4-*.txt` / `negctl-4b-*.txt`）：

- **段④（只把三处 `fullmatch` 改回 `match`）→ 80 全绿 = 惰性变异**。`_BODY_RE` 已有 `\)$` 右锚之后，
  对 strip 过的行 `fullmatch` 与 `match` 等价 ⇒ 这一处**不是**承重层，只是纵深写法。
  「负控 PASSED」在这里的正确读法是「拆错了层」，不是「门是假的」。
- **段④b（只去右锚、保留 `fullmatch`）→ 34 红 = 拆了一层半**，树处于不自洽状态（`fullmatch` 对旧正则恒不成立），
  这种全红同样不构成有效负控。
- 段④c 才是 (d)① 那一层的完整逆操作，给出**恰 1 红**的可归因结果。

### 1.8 ruff / format

存档 `gate-ruff-20260918T173730.txt`：`files=5`（zsh 数组，逐个列出）、`ruff check` → `All checks passed! rc=0`、
`ruff format --check` → `5 files already formatted fmt_rc=0`。
**验伪锚**：`backend/tests/unit/_f821_probe.py` 写一行 `print(undefined_name_xyz)` →
`ruff check` **`Found 1 error.` / `probe_ruff_rc=1`**；随后删除，`git status | grep -c _f821_probe` → **0**。
（`backend/ruff.toml:10` `select = ["E9","F63","F7","F82"]` —— **无 F401**，所以锚选 F821。）
`ruff format` 的改动**全部落在本卡自己新增的行上**，未触碰任何既有行（`--diff` 逐段核过）。

### 1.9 地盘门

`git --no-pager diff --stat --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'` ⊆ 白名单五文件：

```
backend/tests/support/live_port_guard.py            |   4 +-
backend/tests/support/w4_sentinel_identity.py       | 112 ++++++++--
backend/tests/unit/test_live_port_guard_contract.py | 228 ++++++++++++++++++++-
backend/tests/unit/test_w4_a_regression_lock.py     | 167 +++++++++++++++
backend/tests/unit/test_w4_sentinel_rebind.py       | 174 +++++++++++++++-
5 files changed, 660 insertions(+), 25 deletions(-)
```

**未出现**：`guard_plugin.py` / 两个 `conftest.py` / `hygiene_snapshot_tristate.py` / `pytest.ini` / `setup.cfg` /
任何 `backend/app/**` / 任何别车道文件。`lefthook.yml` 未改；`spec-sync-*` 未触发（`git status` 无 `backend/openapi.json`）。

### 1.10 四目录级 + contract 三文件（开工/收工两侧）

存档 `dirlevel-diff-20260918T182941.txt`。⚠️ **开工侧的取法**：`tests/api` / `tests/regression` / `tests/skills` /
`tests/contract` 的「开工」是把两个 support 文件用 `git show 9c4e7e82:<path> > <path>` 退回 BASE 后跑的
（EXIT trap 无条件还原到 HEAD，还原后 shasum 与 HEAD 版逐字同：`290fc5b1…` / `eb6cd5aa…`）。
`tests/unit` 的开工侧是真正的改动前那一跑。

| 套件 | open | close | 红集 diff | 哨兵 |
|---|---|---|---|---|
| `tests/unit` | `32 failed, 5731 passed, 44 skipped, 13 xfailed`（710.40s） | `32 failed, **5755** passed, 44 skipped, 13 xfailed`（678.35s） | **逐条相同（diff_rc=0）**；新增 24 个 passed = 本卡新用例 | `blocked=` 行 1 条，`(0,0,0,0)` |
| `tests/api` | `269 passed` | `269 passed` | 两侧红集皆空 | `(0,0,0,0)` |
| `tests/regression` | `1913 passed, 6 skipped, 1 xfailed`（564.93s） | `1913 passed, 6 skipped, 1 xfailed`（574.57s） | 两侧红集皆空 | `(0,0,0,0)` |
| `tests/skills` | `555 passed`（53.50s） | `555 passed`（48.56s） | 两侧红集皆空 | `(0,0,0,0)` |
| `tests/contract`（3 个非 pact 文件） | `2 failed, 75 passed`（509.38s） | `2 failed, 75 passed`（527.91s） | **逐条相同**（`test_node_id_patterns::test_pattern_matches_json_schema` + `test_health_contract[GET /api/v1/health]` = 主干既有 2 红） | **`blocked=19`（19,19,0,0）两侧相同** |

`tests/unit` 收工红集 vs B15 基线：`diff` 只有一条 `<`
（`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` —— 基线头第 4 行已登记为 flaky），
**零 `>`**。所有目录级 **≤ 12 分钟**跑完，无中止。

### 1.11 哨兵端到端自证（改后的判据自己跑自己的存档）

存档 `sentinel-selfcheck-rc-20260918T183851.txt`（管道里只有 `tee`，`rc` 直接取被测命令）：

```
--- unit : rc=0        W4-IDENTITY: CONSISTENT-ZERO files=2 quad=[(0, 0, 0, 0)]
--- api : rc=0         W4-IDENTITY: CONSISTENT-ZERO files=2 quad=[(0, 0, 0, 0)]
--- regression : rc=0  W4-IDENTITY: CONSISTENT-ZERO files=2 quad=[(0, 0, 0, 0)]
--- skills : rc=0      W4-IDENTITY: CONSISTENT-ZERO files=2 quad=[(0, 0, 0, 0)]
--- contract : rc=0    W4-IDENTITY: CONSISTENT files=2 blocked=19 quad=[(19, 19, 0, 0)]
```

⭐ **contract 那一对是非退化输入**：`blocked=19`、存档里有真实的记录块，
正文身份两侧同为 `["('::1', 7691, 0, 0) on thread asyncio-portal-<id>"]`。
也就是说改后的判据（`fullmatch` + 右锚 + 三类拒判 + 孤儿集合语义）在**真实**的非零存档上
既不误拒也不漏读，且 BASE 侧与本卡侧给出同一个身份 —— 本卡没有改变门拦下了多少、拦下了谁。

### 1.12 现网只读

存档 `readonly-live-20260918T175021.txt`：

- 本卡五个改动文件 `grep -rn -e fsrs_bridge -e decay_beta` → **零命中**（`grep_rc=1`）
- live vault 两份复习链脚本 shasum（未触）：
  `fsrs_bridge.py` `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0`
  `decay_beta.py` `3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90`
- `7691` 在本卡新文件里只出现在 `sys.audit(...)` 的**合成**地址元组与 docstring 里，不建立连接；
  子进程 `os.environ.pop("W4_GUARD_REQUIRE_BLOCKED_TARGET", None)` ⇒ 预检不连库。
- **跑后**复测同两份（与上面跑前逐字同 ⇒ 全程未触）：
  `fsrs_bridge.py` `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0`
  `decay_beta.py` `3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90`
- 本卡零数据库连接（不连 7691 / 7687 / 7692），零 live vault 写入。

---

## 2 DoD-3 §4-B（零技术词）

跑测试时有一道「不许碰真数据库」的门。以前它有几条缝：检查这道门的那把尺子自己会漏看一种写法；
出事的那一刻，本该留下的那行记录在某些情况下会被跳过；而事后看结果的小工具遇到坏掉的文件时会装作没看见。
现在这些缝都补上了，而且以后再裂开会自动报警——我感觉这道门终于能放心靠了。

**felt-sense**：之前每次看到「测试全绿」，心里都要多问一句「是真的没连，还是没看见」。
这次把「没看见」和「真的没有」分开写进了工具里——它现在会明确说「这份我读不清，不算」，
而不是安安静静地给个零。安心的地方不在于多了几条测试，在于它**不会再替我打圆场**了。

---

## 3 与卡文的偏离（如实记，交主 session 裁定）

1. **(d)① 第二个拒判条件的判法换了**。卡文写「`owner` 组含 ` on thread ` ⇒ 拒判（= 存在第二种切法：
   …地址含 ` on thread ` 都落在这里）」。实测**不成立**：对
   `- ADDR on thread B on thread MainThread (owner=x)`，非贪婪的 `thread` 会一路吃到最后一个 ` (owner=` 之前，
   `owner` 组干净就是 `x` ⇒ 那条字面判据**判不出**这一类；反过来，`owner` 里真含 ` on thread `
   （如 `test_q[a on thread b]`）在只有一个 ` (owner=` 时切法**唯一、不歧义**，照字面拒判等于凭空造假红。
   实现改成：`line.count(" (owner=") > 1`（卡文条件一，逐字采纳）**或**
   `head.count(" on thread ") > 1`（`head` = 第一个 ` (owner=` 之前那一段）——后者才真正判得出卡文点名的两类。
   理由写在 `w4_sentinel_identity._refuse_ambiguous_record` 的 docstring 与 `TestGuardTailR2Closures` 用例里。
2. **(f)⑤ 计数 15 而非卡文预期的 14**。分隔符拒判有**两个** `raise` 点（两个分隔符各报各的事实），
   `11 + 4 = 15`。
3. **(k) 负控还原机制**：卡文写「一律 `git show HEAD:<path> > <path>`」。本卡在跑负控前已把**代码**
   定稿提交（`009c61d2`），因此该写法正确；若按「全部跑完再提交」的顺序照抄，`HEAD` 还停在 `9c4e7e82`，
   还原会把本卡改动一并抹掉。**处置**：先提交代码 → 跑全部裁判 → 证据与本单并入同一 commit（`--amend`，
   只动 `_bmad-output`，不破坏 Codex 的终审绑定）。
4. **(k)④ 拆错层/拆过头两次**（§1.7 已详述），三份存档全部入库不删。
5. **(b)②/(k)③ 的红落点与卡文预测不同**：卡文预测负控段③下新门红在「陈旧发布应返回 False」，
   实测红在其**前一条**「发布序没有先行推进」——两条断言测的是同一根因的两个可观测面，断言顺序决定谁先红。
6. **两条既有 sentinel 用例的输入被本卡收紧所取代，已改写并保留原保护面**（详见 §4 台账 ⑥）。
7. **卡文 §二.7 的负控命令示例有一处会写错位置**：`trap '… > backend/tests/support/live_port_guard.py' EXIT`
   与同一子 shell 里的 `cd backend` 同时存在时，trap 在退出时的 cwd 已是 `backend/`，还原会写到
   `backend/backend/tests/…`。本卡全部改用绝对路径。

---

## 4 本卡未证明什么（≥4）

1. **未证明 AST 看不穿的五类延迟路径已封**（模块级 helper / `functools.partial` / `exec`·`eval` /
   `type("X",(),{})` 动态建类 / 把模块级函数绑成类属性）。本卡只补了 `ast.TypeAlias` 这一类
   **本作用域内 AST 可见**的延迟体；那五类是 T9-B 如实登记的**门未覆盖的路径**，本卡不主张封死。
2. **未证明截断门在 root / 不强制文件写权限的文件系统上有效**。本机 `id -u = 501`、APFS 下
   `PASSED`；root 容器或不强制权限位的文件系统上该用例会 `pytest.skip`——skip 分支本身**没有**被
   任何一跑覆盖过（本机造不出 root 环境），所以「CI 上会不会恒 skip」是未证明的。
3. **未证明分隔符二次出现拒判不会在真实 nodeid 上假红**。只在合成样本与两份真实存档形态
   （R4 / R4B）上验过；真实 parametrize id 里出现 ` (owner=` 或两个 ` on thread ` 的概率**未做统计**。
   这是本卡**引入**的保守假红面（触发条件与处置见 §5 台账 ⑥）。
4. **未证明回归锁三格在 CPython ≠ 3.14.4 下同样 rc=3**。`atexit` LIFO 次序与 `sys.audit` 语义
   按本机；三格全部用 `sys.executable`，换解释器没测过。
5. **未证明 `classify_sha_change` 删文件漏判已修**。地盘外（`hygiene_snapshot_tristate.py:27` 不在 P9
   territory 的 19 项里），本卡**只读不改**，只登记（§5 台账 ⑤）。
6. **未证明判据对 `stderr_tail = ` 前缀回显里的真实总账行能看见**。左锚 `^` 保留（按 T9-C 硬警告
   不改 `final >= summary` 比较），所以被前缀包住的总账行既不取值也不触发拒判——有一条用例把这个
   现状钉住，但它是「现状」不是「已解决」。
7. **未跑 `tests/integration` / `tests/e2e`**。W4 对 `tests/integration` 只记账不拦（协议已登记），
   本卡不改那一面。
8. **未证明 `tests/contract` 的 `blocked=19` 是「应该的」**。本卡只证明了它在 BASE 侧与本卡侧
   **完全相同**（19/19/0/0、同一条正文身份）⇒ 不是本卡引入；那 19 次到现网 7691 的连接尝试
   本身是否合理，属 contract 套件自己的面，未评。
9. **未证明既有 `test_cli_refuses_when_a_file_has_no_summary_line` 仍打在它声称的那道门上**。
   实测它在**改前**就已经先撞上孤儿拒判（rc=2 来自 CONFLICT 而非缺四元组门），本卡收紧后
   仍是 rc=2、测试仍绿 —— 覆盖影子是**既有的**，不是本卡造成的；r4 已另立
   `test_missing_quad_gate_is_actually_reached` 真正打在那道门上。登记不修（§5 台账 ⑦）。

10. **未证明 `_FINAL_RE` 的退出码组严格等于 `FINAL_EXIT_CODE`**。按卡文 (d)② 写成
    `(0|[1-9][0-9]*)`，因此 `…退出码 0 结束…` / `…退出码 4 结束…` 同样全匹配 —— 右锚锁的是
    **文案形状**，不是那个数的值域。（Codex r1 问题 5 指出，成立。）
11. **未证明新用例 `test_type_alias_is_in_the_deferred_reject_set` 在 3.11 及更早可跑**。
    判据本体用 `getattr(ast, "TypeAlias", ())` 对旧解释器安全，但**该用例本身**无条件
    `ast.parse` 了 PEP 695 语法，3.11 会 `SyntaxError`。本仓锁 3.14.4，未在别的解释器上跑过。
12. **未证明 `_final_accounting` 里 `:1529` 的 `except Exception` 不需要同型收口**。
    本卡只改迟到路径那一处（卡文 (l) 把 guard diff 限死为恰 4 行）。那里仍是既有的
    **门未覆盖的路径**（Codex r1 问题 6 同判）。
13. **未证明 `TestJudgeIsBoundToTheRealProducers` 的源码锚覆盖 `_FINAL_RE` 的新尾巴**。
    `:628-632` 的锚只查旧前缀，`:670-674` 是手抄的尾巴 —— 产出方若改尾巴文案，源码锚仍真
    而正则已不匹配（Codex r1 问题 5 的**门未覆盖的路径**，属既有形态，本卡未扩）。

---

## 5 台账待登记条目（≥4）

1. **台账 `:105` T9-A 行「4 行修复无常驻门（唯一裁判零断言、rc 恒 0）」→ 可关闭**。
   常驻锁 = `backend/tests/unit/test_w4_a_regression_lock.py`，
   nodeid：`test_forced_exit_survives_a_broken_report_path[A|B|C-…]` ×3 +
   `test_three_cells_share_one_guard_source` + `test_the_three_cells_are_distinguishable_by_construction`。
   负控段② 存档 `evidence-w4-guard-tail-r2/negctl-2-20260918T171143.txt`；修复 sha `009c61d2`（含证据后为最终 commit）。
   冻结脚本 `three-run-abc.py` / `ast-protected.py` **保留为历史证据，不再作裁判**。
2. **T9-B 台账 10（`ast.TypeAlias` 漏面）→ 关闭**。修复 sha 同上；AST 门存档
   `ast-gate-before-*.txt` / `ast-gate-after-*.txt`（含 BASE 验伪锚）。
   **T9-B 台账 4（白名单门全称封闭未成立：动态 `getattr(self,name)` / `__getattribute__` /
   `partial` / 容器取出再调）维持登记，本卡不做。**
3. **T9-B 台账 6（`_publish_ledger` 截断前失败保留旧内容缺运行时门）→ 关闭**。
   nodeid `TestSingleLedgerSnapshot::test_publish_ledger_keeps_old_content_when_open_fails_before_truncation`；
   本机 `PASSED`（非 skip）；skip 分支未被覆盖，见 §4-2。
4. **T9-A 台账 ⑥（迟到路径「未评估」）→ 关闭**：`:1501` 收成 `except BaseException`，
   nodeid `TestForcedExitPathsAreFailOpen::test_late_rewrite_swallows_base_exception_like_the_exit_guard`
   + `::test_late_rewrite_handler_is_baseexception`；全文件 print 排查名单由
   `::test_every_print_on_forced_exit_paths_sits_in_a_baseexception_try_body` 常驻输出。
   **台账 ⑨（AST 判据 `protected` 应收窄到 `try.body`）→ 关闭**（同上一条用例，落在契约套件，冻结脚本未改）。
   **台账 ⑩（`three-run-abc.py` 零断言 rc 恒 0）→ 关闭**（见本节 ①）。
5. **`classify_sha_change` 删文件漏判 → 地盘外，建议下批 P9 同车道一卡**。
   定义 `backend/tests/support/hygiene_snapshot_tristate.py:27`（`before is None or after is None ⇒ UNCHECKED`），
   采集侧 `backend/tests/unit/conftest.py:99-101` 的 `except OSError: sha[rel] = None` 把「文件不存在」与
   「读失败」压成同一个 `None`。修法需跨两文件：采集侧区分 `FileNotFoundError` 与其它 `OSError`，
   三态扩四态。本卡只读未改（`hygiene_snapshot_tristate.py` 不在手册 §一.1 的 P9 地盘 19 项里）。
6. **本卡引入的保守假红面（两条）+ 两条既有用例的输入改写**：
   - 分隔符二次出现拒判：记录行里 ` (owner=` 出现两次，或第一个 ` (owner=` 之前 ` on thread ` 出现两次
     ⇒ `W4LedgerConflict`（CLI rc=2）。触发方：含 ` (owner=` 的 nodeid、含 ` (owner=` 的线程名、
     含 ` on thread ` 的地址 repr。
   - `_BODY_RE` 全匹配：记录行必须以 `)` 收尾。产出方三处都以 `)` 收尾，故对**真实**产出零影响；
     被拒的只有**不完整的回显**。
   - 既有 `TestFailureBodyIdentities::test_owner_containing_on_thread_does_not_leak_into_identity`
     的输入原含**两个** ` (owner=`，落进上面第一条 ⇒ 改成只含 ` on thread `、切法唯一的 owner，
     原本要证的「owner 不得漏进身份」一字不变；旧输入移到
     `TestGuardTailR2Closures::test_second_owner_separator_makes_the_boundary_unjudgeable` 钉拒判。
   - 既有 `TestRound4Closures::test_orphan_record_outside_any_block_is_refused` 原让漂移块携带与正常块
     **逐字节相同**的记录行，落进本卡的集合语义豁免 ⇒ 改成携带**不同**记录（`('127.0.0.1', 7687)`），
     r4 MEDIUM-2 的门（「另一块抬头漂了、记录静默消失」）保持有效；豁免边界另由
     `test_one_byte_different_record_outside_a_block_is_still_refused` 与
     `test_echo_of_an_unclaimed_record_is_still_an_orphan` 两条对照钉住。
7. **既有 `TestCliActuallyUsesWhatItClaims::test_cli_refuses_when_a_file_has_no_summary_line` 的覆盖影子
   （既有，非本卡引入）**：它的两份样本都含**块外裸记录行**，在**改前**就已先撞孤儿拒判 ⇒ rc=2 来自
   CONFLICT 而不是它声称的「缺四元组门」。本卡收紧后仍 rc=2、仍绿。r4 已另立
   `test_missing_quad_gate_is_actually_reached` 真正打在那道门上。**登记不修**。
8. **目录级四套 + contract 三文件的存档名与红集 diff**：
   - `unit-open-20260918T165208.txt` / `unit-close-20260918T174956.txt` —— 红集**逐条相同**（32/32）；
     对 B15 基线只有一条 `<`（已登记 flaky `test_accept_candidate_already_accepted_returns_422`）。
   - `api-open-20260918T173828.txt` / `api-close-20260918T174956.txt` —— 两侧红集皆空（269 passed）。
   - `regression-open-20260918T173828.txt` / `regression-close-20260918T174956.txt` —— 皆空（1913 passed）。
   - `skills-open-20260918T173828.txt` / `skills-close-20260918T174956.txt` —— 皆空（555 passed）。
   - `contract-open-20260918T182916.txt` / `contract-close-20260918T174956.txt` —— **主干既有 2 红**
     逐条相同；哨兵 `blocked=19` 两侧相同。
   - 无任何目录 >20 分钟中止（最长 `tests/unit` 11m18s）。
9. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** —— 见 §6。

10. **本卡引入的第三条方向交换（红 → 绿，唯一一条）**：`_BODY_RE` 全匹配后，
    **块外被截断的记录行**（缺右括号）不再判孤儿。实测同输入 BASE `main()` = **2**、HEAD = **0**，
    被丢掉的是那条截断记录携带的**第二身份**。触发条件：存档里出现一条 `- <addr> on thread <t> (owner=`
    **没有右括号收尾**、且不属于任何自报条数的块。方向是「**记录消失**」不是「记录错认」。
    复现存档 `evidence-w4-guard-tail-r2/codex-r1-medium-verify-*.txt`。
    **本卡登记不修**：这一步是卡文 (d)① 明令要求（收 T9-C 26 登记的假红），改回去等于把假红放回来，
    而「既不假红、又不漏截断记录」需要区分「回显」与「截断」——那正是本模块 r1/r2/r3 连栽三轮的
    开放式规则。**建议下一张 W4 卡专题处置**（可行方向：块外行按「前缀匹配成功但全匹配失败」
    单独归一类 `TRUNCATED`，与 `ORPHAN` 分开报，而不是二选一）。
11. **Codex prompt 的台账引用路径有歧义（本卡引入，已更正口径）**：prompt 第 9 条写
    `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:105`，在**车道树**里解析到
    冻结于 `9c4e7e82` 的副本（sha `db9397fb…`，`:105` = Y4-A RV-E），而卡文引的是 **feature 主干树**
    那份活台账（sha `4fb1cf24…`，`:105` = T9-A W4-FINAL-ACCOUNTING 行，本卡已实测确认）。
    Codex r1 末段据此报「台账 :105 不是本卡来源行」——**结论不成立，根因是 prompt 路径歧义**。
    建议下批 prompt 模板对台账一律写**绝对路径**。prompt 保持送审原样未改。
12. **Codex r1 的 LOW-2 / LOW-3 / LOW-4 三条**（截断门 skip 分支把「发布锁超时返回 False」也吞了 /
    四目录 open 档缺进程 rc 与源码哈希绑定 / `ast-gate.py` rc 恒 0 不能当门）——逐条处置见 §6 表，
    其中 LOW-3 已由 `named-close-rc-*.txt` 部分补齐，另两条**登记不修**（LOW = 登记）。

---

## 6 Codex 复核

| 轮 | 存档 | 模型 / effort / codex | 绑定 SHA | B / H / M / L |
|---|---|---|---|---|
| r1 | `_bmad-output/审查/codex-review-CARD-W4-GUARD-TAIL-R2.md`（7671 字节，非 0） | `gpt-6-astra` / `ultra` / `codex-cli 0.153.3` | `ec245c8c`（送审时 HEAD；Codex 正文首句自报 `ec245c8ce105dc67103ce70b6fcff41b9e447801`「首尾未变」） | **0 / 0 / 1 / 3** |

**D-15 满足**：本卡有代码改动 ⇒ 多轮制；**r1 即绑最终 HEAD 且 BLOCKER = 0、HIGH = 0**，
审后**未再改任何代码**（`git --no-pager diff --stat --no-color ec245c8c HEAD -- . ':(exclude)_bmad-output'` 为空，
见 §7），故 r1 即末轮，不需 r2。MEDIUM / LOW 按协议 §1 **登记不阻断**，逐条处置见下。

| 级别 | Codex 结论 | 本卡处置 |
|---|---|---|
| MEDIUM-1 | `w4_sentinel_identity.py:422` 块外过滤会漏掉不同身份，实测 `rc=2 → rc=0`；「全部收紧、没有红转绿」不成立 | **成立，已独立复现**（`codex-r1-medium-verify-*.txt`：BASE rc=2 / HEAD rc=0）。这一步是卡文 (d)① 明令要求（收 T9-C 26 的假红），**登记不修**（改它要么回到被连打三轮的开放式规则，要么违卡文）。更正见 §1.5、登记见 §5 ⑩。另接受其两点措辞更正：豁免比较发生在 **ANSI 清理 + `strip()` 之后**，应说「归一化后逐字相同」而非「逐字节相同」 |
| LOW-2 | 截断门把「`_publish_ledger` 返回 `False`（发布锁超时）」也归成「权限不受强制」而 skip | **成立，登记不修**（LOW = 登记；该路径需另一线程占 `_PUBLISH_LOCK` 满 5s，单线程用例里不可达）。下一张 W4 卡可把 `else` 分支收成「返回值必须是 `False` 之外」再 skip |
| LOW-3 | 三文件绿档缺进程 rc；api/regression/skills 的 open 档亦然；目录档无源码哈希绑定 | **已部分补**：新增 `named-close-rc-*.txt`（首部带 HEAD + 两个 support 文件 sha256，末行 `rc=0`）。四目录 open 档的 rc 未补（重跑成本 ≈ 23 分钟且会改变时间戳，登记） |
| LOW-4 | `ast-gate.py` 无论判词如何都 `return 0`，rc 不能当门 | **成立，登记**。本卡从未把它的 rc 当判据——§1.1 引的是它**打印的判词**（`GATE head_has_typealias=…` / `FALSIFICATION-ANCHOR: …`）。下一张卡若要自动化，应让它按判词置 rc |
| （Codex 末段） | 「指定台账 `:105` 当前是 **Y4-A RV-E**，不是本卡来源行」 | **不成立（读错了文件）**。Codex 读的是**车道树**里冻结于 `9c4e7e82` 的台账副本（sha `db9397fb…`），其 `:105` 确为 Y4-A RV-E；卡文引的是 **feature 主干树**那份活台账（sha `4fb1cf24…`），其 `:105` 实测正是 `\| **T9-A W4-FINAL-ACCOUNTING**（3109a278）\| 4 行修复无常驻门…\|`。根因是 prompt 第 9 条写了**相对路径**，在车道树里解析到冻结副本 —— 登记为 prompt 路径歧义（§5 ⑪），prompt 保持送审原样不改 |

**Codex 另行确认的要点**（本卡自述被独立核对为 PASS 的部分）：
A 格归因成立（当前 HEAD 内存负控：A `3→0`、B `3→3`，出口追踪只到 `_final_accounting`，未到迟到出口 `:823`）；
`ast.TypeAlias` 在 3.14.4 下普通 / 泛型 / `*Ts` / `**P` / 默认类型参数 / 中文名 **均得 `ast.Name`**，真实 `install()` 通过；
`chmod 0o400` 在 Darwin + UID 501 下确实截断前拒绝写打开，存档是 **PASS 非 skip**；
改 `BaseException` 后退出语义不变（唯一生产调用点 `:813/:821` 本就吞 `SystemExit`/`KeyboardInterrupt` 并退 3）；
四目录 + contract 的 open→close 红集**无新增也无减少**、三文件 +24 与 unit 收集数 +24 吻合；
五组真实 open/close 存档用当前判据重比**均返回 0**；两处口径更正**均成立**（`W4LedgerConflict(` 实数 11→15）；
指定生产者 / 两个 conftest / `guard_plugin.py` / `hygiene_snapshot_tristate.py` **均零 diff**。

---

## 7 合并门自检（协议 §1）

| 项 | 状态 |
|---|---|
| 数据丢失 | 无（本卡只改测试面与测试支持模块，零 `backend/app` 改动） |
| live vault / Neo4j 7691 写入 | 无（§1.12 shasum 自证；零数据库连接） |
| 安全 | 无 |
| 指定裁判红 | **无** —— Codex r1 绑最终 HEAD，BLOCKER = 0 / HIGH = 0（MEDIUM 1 / LOW 3 按协议 §1 登记不阻断，逐条处置见 §6） |
| 负控假绿（窄口径：负控本身谎报 PASS） | 无 —— 段④的 PASSED 已识别为**拆错层**并补跑段④c，三份存档全部入库 |
| 本批引入的新红 | **0**（四目录级 + contract 红集两侧逐条相同） |
