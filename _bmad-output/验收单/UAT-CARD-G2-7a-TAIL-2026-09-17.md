# UAT — CARD-G2-7a-TAIL（部署校验器 hotkeys 无写端 FIFO 挂起先修）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-G2-7a-TAIL]` · 车道 **T7 skills-writer** `card-t7-skills`（本车道第 **4/4** 张，**T7 末卡**）
> `PREV`（= T7-C `CARD-SKILL-PORT-LINT-PARSER` 末 commit）= `09567e35bf393c34d1ab185e89e6b9effede7141`
> 证据目录 `_bmad-output/审查/evidence-g27a-tail/`（`.txt` 存档，`*.stderr*` 不入库）
> 卡文（**feature 主干树那份**，含本批回写）：`.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T7-D.md`
> 协议与手册同样只读主干树那份（车道树自己那份是 `08100483` 版、不含本批回写）

---

## 一 这张卡修的是什么（一句话）

部署校验器 `scripts/verify_vault_install.py` 的 `_check_hotkeys` 在读 `.obsidian/hotkeys.json`
之前**没有验形态**：`Path.read_text()` 内部是**阻塞** open，当这个文件是**无写端 FIFO** 时，
open 会一直等写者、**永久停在打开阶段** —— 包在外面的 `except (OSError, UnicodeDecodeError)`
根本到不了，`--vault` 连 rc=2 都跑不出来（UAT-CARD-G2-7a 的 MEDIUM-2）。
本卡在读内容前补一道**非阻塞形态门**，特殊文件归 `unreadable` ⇒ rc=2。

---

## 二 第 0 分钟（(a)）

| 项 | 实测 |
|---|---|
| `pwd` 末段 | `card-t7-skills` ✅ |
| `git rev-parse --abbrev-ref HEAD` | `card/t7-skills` ✅ |
| `PREV=$(git rev-parse HEAD)` | `09567e35bf393c34d1ab185e89e6b9effede7141`（= T7-C 末 commit）✅ |
| `git status --porcelain` 空 | ⚠️ **开工时非空 1 行**，处置见下 §二.1 ✅（处置后为空） |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 均在 ✅ |
| `$BASE` 存在 + `grep -vc '^#'` | **64** ✅（R-B14-2 口径） |
| 手册 §一 地盘核（§三 三分支） | **分支 ①**：命中且归属 **T7-D** ✅（口径更正：卡文记 §一 `:65` → 实测 **`:67`**，`:65` 是「只 T6」行） |

存档：`evidence-g27a-tail/judge1-preflight-20260917T025205.txt`

### 二.1 开工时 `git status --porcelain` 非空的处置（如实）

开工瞬间有 **1 个未跟踪 0 字节文件**：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-PARSER-r2.md`。
它是 **T7-C 配额耗尽那次 r2 的产物**（T7-C 已由 r1 绑最终 HEAD、B/H/M=0 收官，r2 不再需要）。
处置：**移入本 session scratchpad 保留**（0 字节、零数据损失、完全可逆），**未删除、未入库**；
移动后 `git status --porcelain` 空，第 0 分钟前提成立。登记为台账条目。

> ⚠️ 裁判 1 存档里那行 `status_lines=1` 是**存档自指**：证据目录 `evidence-g27a-tail/` 在该命令
> 执行的同一刻被创建、尚未跟踪。「status 空」在建该目录**之前**已证（见存档 [注1]）。

### 二.2 §〇 逐条复测结果（口径更正全部登记）

| 卡文锚点 | 实测 | 结论 |
|---|---|---|
| `_check_hotkeys` 主流程调用 `:1166` | `:1166` | 逐字同 |
| `hotkeys_state = _entry_state` `:1293` | `:1293` | 逐字同 |
| `raw = hotkeys_path.read_text(...)` `:1312` | `:1312` | 逐字同 |
| `main_js_kind = _resolved_kind` `:1332` / `== "unreadable"` `:1333` / `!= "file"` `:1341` / `read_text` `:1345` | 全部逐字同 | 逐字同 |
| rc 四档 docstring `:53-59` | 逐字同 | 逐字同 |
| AST 端点 `_entry_state :503-522` / `_resolved_kind :556-572` / `_probe_regular_readable :732-760` / `_check_hotkeys :1272-1374` | 全部相同 | 逐字同 |
| `grep -cnE -e 'S_ISFIFO' -e 'O_NONBLOCK'` 开工 = 0 | **0** | ✅（验伪锚：同形态 grep 对 `S_ISREG`/`os.fstat` 命中 **4**，证明 grep 写法有效） |
| `grep -cF 'APFS'` = 0；`macOS` 在 `:16` / `:1494` | 均同 | 逐字同 |
| 测试文件 3239 行 / `VERIFIER` `:84` / `import subprocess` `:75` / `HOTKEYS_REL_IN_VAULT` `:305` / `os.mkfifo` `:953`,`:1938` | 全部同 | 逐字同 |
| `def test_.*fifo` = 0、`def test_.*hang` = 0、`def test_` = 131 | 全部同 | ✅ 新测试名与既有名集合交集空 |
| 基线含该测试文件 0 条 nodeid | **0** | ✅ 既有门不在红基线 |
| **手册地盘段行号** | 卡文 §一 `:65` → 实测 **`:67`** | ⚠️ **口径更正** |
| **`--report` 输出格式** | 卡文 (f)/裁判 3 写「JSON」→ 实测 `render()` `:1397` 产出**纯文本**报告 | ⚠️ **口径更正**，判据改为文本三处断言（见 §四） |

---

## 三 改了什么（(c)(d)）

### 三.1 `scripts/verify_vault_install.py` — 只在 `_check_hotkeys` 内插形态门

原 `:1311-1316` 的「`try: raw = hotkeys_path.read_text(...)`」替换为四段（最终行号）：

| 行 | 内容 | 为什么 |
|---|---|---|
| `:1311-1326` | 形态门注释块 | (d) 平台/FIFO 文案：同时含 `FIFO`（`:1312/:1316/:1320/:1324/:1343/:1353`）与 `macOS/APFS`（`:1325`） |
| `:1328` | `hotkeys_fd = os.open(hotkeys_path, os.O_RDONLY \| os.O_NONBLOCK)` | 无写端 FIFO 上 `O_RDONLY\|O_NONBLOCK` **立即**返回 fd，不等写者 ⇒ open 阶段不再挂 |
| `:1334` | `hotkeys_is_regular = stat.S_ISREG(os.fstat(hotkeys_fd).st_mode)` | **同一个 fd** 的 `fstat`：判形态的对象与随后读内容的对象是同一个 inode（不用路径 `stat` 预判，避免 TOCTOU） |
| `:1339-1346` | `if not hotkeys_is_regular:` → `os.close(fd)` + `_unreadable(...)` + `return` | 非普通文件（FIFO/设备/目录/socket）归 **unreadable ⇒ rc=2**；⛔ **不照搬** main.js 侧 `:1341 != "file"` 的置 note=rc0 分支（那是 UAT MEDIUM-3 既有缺口，本卡不扩面） |
| `:1354-1355` | `with os.fdopen(hotkeys_fd, "r", encoding="utf-8") as fh: raw = fh.read()` | 从**同一 fd** 读；`"r" + encoding="utf-8"` 与原 `read_text(encoding="utf-8")` 同一套 io 默认值（`newline=None` 通用换行 / errors 严格）⇒ 读到的字符串逐字等价 |

fd 所有权：`os.fdopen` 构造**成功**由 `with` 关、构造**失败**它自己已关 ⇒ 上面两条早退各自显式 `os.close`，
`fdopen` 之后一次都不再关。**每个时刻恰好一个所有者**，不漏关也不双关。

rc 四档语义（docstring `:53-59`）**未改**；`_entry_state` / `_resolved_kind` / `_probe_regular_readable`
**未改**；`_check_hotkeys` 内形态门之外的早退/分支/文案**未改**。

### 三.2 `backend/tests/unit/test_vault_install_manifest.py` — 新门 + 一处既有门的**收紧扩展**

| 位置 | 内容 |
|---|---|
| `:3172` | `HOTKEYS_FIFO_TIMEOUT_S = 60`（取值实证：同命令正常路径本机连跑 5 次最慢 **0.052s** ⇒ >1000× 余量） |
| `:3175-3189` | `_report_section()` — 从渲染报告取 `## <title>` 段的明细行 |
| `:3192-3267` | **`test_hotkeys_fifo_does_not_hang_and_reports_unreadable`**（(f) 承重回归门） |
| `:758-768` / `:771-787` / `:790-829` | `_is_os_open()` / `_os_open_flag_names()` / `_is_readonly_open()` 的 **`os.open` 分支**（见 §三.3） |
| `:643-745` 内 | `test_verifier_write_calls_are_confined_to_write_report` 加 **10 条验伪锚** |

### 三.3 为什么动了既有门 `test_verifier_write_calls_are_confined_to_write_report`（必须交代）

加完 `os.open` 之后，这道「校验器是只读的，写调用只许在 `_write_report` 里」的既有护栏**立刻变红**：
`FAILED ... 写调用出现在 _write_report 之外: [('open', 1328)]`。

根因是该门的豁免 helper `_is_readonly_open` 有个**既有盲点**：它按 `isinstance(node.func, ast.Attribute)`
判「绑定方法」，于是把 `os.open(path, flags)` 当成 `path.open(mode)`、把 **path**（`args[0]`）当模式读 ——
不是字符串字面量 ⇒ 结论恒 `False`。任何只读的 `os.open` 都会被误报成写调用。

处置：**收紧后扩展，不放宽**。给 `os.open` 单开一条分支，判据仍是「**只按字面量放行**」：
旗标必须是纯 `os.O_*` 字面（可用 `|` 连），且**全部**落在只读白名单
`{O_RDONLY, O_NONBLOCK, O_CLOEXEC, O_NOFOLLOW, O_DIRECTORY, O_NOCTTY}` 内；
**缺旗标 / 算出来的旗标 / 混进任一写旗标，一律仍判违规**。

并在门里补 **10 条验伪锚**（证明这条豁免不是放水）：

```
os.open(p, os.O_RDONLY | os.O_NONBLOCK) -> True      os.open(p, os.O_WRONLY | os.O_CREAT) -> False
os.open(p, os.O_RDONLY)                 -> True      os.open(p, os.O_RDONLY | os.O_TRUNC) -> False
p.open()                                -> True      os.open(p, flags)                    -> False
open(p, 'rb')                           -> True      os.open(p)                           -> False
                                                     p.open('wb+')                        -> False
                                                     open(p, 'w')                         -> False
```

后四条是**原有主张不得被削弱**的回归锚（`p.open('wb+')` 那条正是 U3-A 零写门被捅开过的原案）。

---

## 四 DoD-3

### 4-A Claude 已代验（证据在 `evidence-g27a-tail/`）

| # | 判据 | 实测 | 存档 |
|---|---|---|---|
| 1 | 开工状态 + §〇 逐字核 + `S_ISFIFO\|O_NONBLOCK` 开工 **0** | ✅ 见 §二 | `judge1-preflight-20260917T025205.txt` |
| 1b | 同一 grep 收工 **≥1** | **4**（`:1316/:1320/:1328/:1353`） | `fifo-fixed-after-20260917T025533.txt` |
| 2 | **先挂（改前）**：mkfifo hotkeys + `subprocess timeout=15` ⇒ 必 `TimeoutExpired` | ✅ `TimeoutExpired`；**并用 `-X faulthandler` + SIGABRT 把挂点钉死**：Python 栈 `verify_vault_install.py:1312 _check_hotkeys` ← `:1166 verify`，C 栈停在 `libsystem_kernel.dylib open` ← `_io_FileIO___init__` ⇒ 挂的是 **open 系统调用本身**，不是「某处挂了」 | `fifo-hang-before-20260917T025312.txt`；最终探针版本复证见 `before-baseline-20260917T025607.txt` |
| 3 | **改后**：同探针 rc=**2**、无挂起、hotkeys 归 `unreadable`、note 含「不是普通文件」 | ✅ `[A] returned rc=2`；`unreadable : 3`；`## unreadable` 段含 `.obsidian/hotkeys.json — 快捷键文件不是普通文件(FIFO/设备等特殊文件), 无法核对快捷键`；`hotkeys : not evaluated (不是普通文件)` | `fifo-fixed-after-20260917T025533.txt` |
| 4 | **既有门改前** | **175 passed**，rc=0 | `before-baseline-20260917T025607.txt` |
| 4b | **既有门改后**（应 +1） | **176 passed**，rc=0 ✅ 恰 175+1 | `existing-gate-after-20260917T030042.txt` |
| 5 | **FIFO 回归门单跑** | **1 passed**，rc=0 | `fifo-gate-single-20260917T025820.txt` |
| 6 | **负控-1**（删形态门 ⇒ 还原裸 `read_text`） | 门 **rc=1 红**，红在 `subprocess.TimeoutExpired: ... timed out after 60 seconds` ✅ | `negctl-20260917T030322.txt` + `negctl-nc1-raw-*.txt` |
| 6b | **负控-2**（形态门 `if False:` 恒放行） | 门 **rc=1 红**，红在**身份断言**：`实得 ['.obsidian/hotkeys.json — 不是合法 JSON…']` ✅ | 同上 + `negctl-nc2-raw-*.txt` |
| 6c | 两段 `shasum -a 256` 跑前跑后共 **4 行逐字同** | 四行均 `f47606cf17b7319f3415ae3e9039b22945faffae054912c406862c895d27ff2d` ✅；还原后计数回到 **4** | `negctl-20260917T030322.txt` |
| 7a | **读取等价（Codex ①）** | 14 样本 **14/14 逐字同**，含 CRLF 归一、5 MiB 无短读、两类 `UnicodeDecodeError` | `read-equivalence-20260917T032212.txt` |
| 7b | **形态覆盖面（Codex ②）** | 七种形态（FIFO/目录/软链→字符设备/软链→FIFO/socket/悬空软链/普通文件对照）**全部 rc=2、无一挂起** | `special-kinds-20260917T032120.txt` |
| 7c | **门未覆盖的路径（Codex ④）** | main.js 侧 / copy 件无 source / copy 件有 source / 源侧 copy 件 **四格全部在预算内返回，无一挂起**；机制：`_leaf_digest:690-729` 先 `os.lstat` + `S_ISREG` **才** `read_bytes()`，FIFO 落「类型位」分支、根本不 open | `other-read-points-20260917T032258.txt` |
| 8 | **平台/FIFO 文案** | `FIFO` 新增命中 `:1312/:1316/:1320/:1324/:1343/:1353`；`macOS/APFS` 新增 `:1325`（原 `:16`/`:1537` 之外） | §三.1 |
| 9 | **地盘门** ⊆ {`scripts/verify_vault_install.py`, `backend/tests/unit/test_vault_install_manifest.py`} | ✅ 2 files changed, +219 / -1 | 见 §六 |
| 10 | **manifest / `backend/app` 零改**；`manifest-ruling.md` 未改 | 均空 ✅；`fsrs_bridge`/`decay_beta` 在两个改动文件里各 **0** 命中 | 见 §六 |

#### 补充判据：新读法与原 `read_text` 的逐字等价（14 个样本实测）

存档 `read-equivalence-20260917T032212.txt`（探针 `probe_read_equivalence.py`）。
对同一批样本各读一次并**逐字符**比对，抛异常的样本比对**异常类型**：

| 样本 | 字节 | `read_text` | 新读法 | 判定 |
|---|---|---|---|---|
| `empty` | 0 | 0 字符 | 0 字符 | 逐字同 |
| `lf-only` | 9 | 9 字符 | 9 字符 | 逐字同 |
| **`crlf`** | 16 | **13 字符** | **13 字符** | 逐字同（通用换行归一两边一致） |
| `cr-only` | 13 | 13 字符 | 13 字符 | 逐字同 |
| `mixed-newlines` | 14 | 13 字符 | 13 字符 | 逐字同 |
| `no-trailing-newline` | 8 | 8 字符 | 8 字符 | 逐字同 |
| `utf8-cjk` | 29 | 17 字符 | 17 字符 | 逐字同 |
| `utf8-bom` | 12 | 10 字符 | 10 字符 | 逐字同 |
| `embedded-nul` | 11 | 11 字符 | 11 字符 | 逐字同 |
| `lone-surrogate-bytes` | 3 | **UnicodeDecodeError** | **UnicodeDecodeError** | 逐字同 |
| `invalid-utf8-tail` | 11 | **UnicodeDecodeError** | **UnicodeDecodeError** | 逐字同 |
| `u2028-line-sep` | 15 | 13 字符 | 13 字符 | 逐字同 |
| **`large-5mib`** | 5 242 890 | 5 242 890 字符 | 5 242 890 字符 | 逐字同（**无短读**） |
| `many-crlf-lines` | 268 890 | 248 890 字符 | 248 890 字符 | 逐字同 |

**14 / 14 逐字同，0 不同。**

> ⚠️ 这条**必须测、不能论证**：`crlf` 那一行 16 字节 → 13 字符，是 `newline=None` 通用换行归一的结果。
> 若新读法写成更直觉的 `os.read()` + `.decode("utf-8")`，该行会读成 16 字符 —— 两条路**静默分叉**，
> 而 `json.loads` 对 CRLF 不敏感，既有测试永远抓不到。选 `os.fdopen(fd, "r", encoding="utf-8")`
> 正是因为它与 `Path.read_text` 共用同一套 `io.open` 默认值。
> `UnicodeDecodeError` 两行证明「解码失败仍从同一个 `except` 出去」；5 MiB 那行证明普通文件上
> `O_NONBLOCK` 不会造成短读。

#### 补充判据：形态门对 FIFO 之外的非普通文件（七种形态实测）

存档 `special-kinds-20260917T032120.txt`（探针 `probe_special_kinds.py`，全程 `subprocess` + `timeout=15`，
任何一种若挂住都会以 `TimeoutExpired` 显形）：

| hotkeys 的形态 | rc | hotkeys note | 归桶 |
|---|---|---|---|
| 普通文件（对照） | 2 | `not evaluated (… main.js 缺 — gitignored 构建产物)` | **不在** unreadable 段 ✅ |
| FIFO（无写端） | **2** | `not evaluated (不是普通文件)` | unreadable，明细「不是普通文件(FIFO/设备等特殊文件)」 |
| 目录 | **2** | `not evaluated (不是普通文件)` | 同上 |
| 软链 → 字符设备（`/dev/null`） | **2** | `not evaluated (不是普通文件)` | 同上 |
| 软链 → FIFO | **2** | `not evaluated (不是普通文件)` | 同上 |
| Unix socket | **2** | `not evaluated (读不进去)` | unreadable，明细 `[Errno 102] Operation not supported on socket` —— 走**第一条** `except OSError`（`os.open` 当场报错） |
| 悬空软链 | **2** | `not evaluated (读不进去)` | unreadable，明细 `[Errno 2] No such file or directory` —— 同第一条分支；**与改前 `read_text` 的行为一致**（都归读失败） |

⇒ 七种形态**无一挂起、无一落进「不计退出码」的说明档**，全部 rc=2。
对照那一行证明「rc=2」不是任何输入下都成立（普通文件时 hotkeys 不进 unreadable）。

#### 负控-2 的关键观察（本门真正承重的那一条断言）

`if False:` 变异之后，**rc 仍然是 2、hotkeys 仍然在 `unreadable` 桶里** ——
因为 `O_NONBLOCK` 还在，无写端 FIFO 读到 EOF ⇒ `raw = ""` ⇒ `json.loads("")` 抛 ValueError
⇒ 落到既有的「不是合法 JSON」分支，照样归 unreadable、照样 rc=2。

⇒ **只断言 `rc == 2`、或只断言「hotkeys 在 unreadable 里」的门，在这一变异下会假绿。**
抓住它的是身份断言「unreadable 明细必须说清是**形态**问题而不是别的读失败」。
这也是本门为什么用 `_report_section()` 分段取行、而不是 `in report_text` 做字符串存在性检查。

### 4-B 用户视角（零技术词）

> 当快捷键文件被换成一种会让检查卡死的特殊文件时，部署检查不会再一直转圈、等不到结果，
> 而是很快就告诉我「这个文件查不了」，并且把这次检查判成**不通过**（不会假装一切正常）。
> 我感觉整个部署检查不会再莫名其妙地卡住 —— 以前那种「敲下去以后就没有下文、只能自己去掐掉」
> 的悬着的感觉没有了；现在它要么给我结论，要么明确告诉我哪一项查不了，心里踏实。

---

## 五 本卡未证明什么（必填 ≥4）

> ⚠️ 本节按**实测之后**的口径收紧过一次：有些原本打算写「未证明」的条目，本卡后来补了探针实测，
> 就不能继续写成未证明（那是把已知说成未知）；反过来，实测覆盖不到的边界写得更具体。

1. **未证明「有写端」FIFO（正在被写）下的读行为**。形态门在读之前就拒了它，所以那条路在**当前代码**下
   不可达 —— 但「不可达」是当前代码的性质，不是被验证过的运行时性质。已证的是相邻两件事：
   无写端 FIFO 的阻塞 open 被堵住（负控-1 红在 `TimeoutExpired`）、普通文件读到的内容与原
   `read_text(encoding="utf-8")` **14/14 逐字同**。
2. **只证了「稳定 FIFO」，没证「并发替换」**。已实测的是四处**稳定形态**（main.js 侧、copy 件
   无/有 `--source`、源侧 copy 件），四格都没挂；`_leaf_digest` 的 `lstat`+`S_ISREG` 前置也读码确认。
   但 **Codex r1 §4 指出（我接受）**：普通文件**通过形态检查之后**被换成无写端 FIFO 时，
   `_leaf_digest:719 read_bytes()` / `_probe_regular_readable:756 open()` / main.js 侧 `:1388 read_text()`
   仍可能阻塞，且 `--source` 摘要在 `:1125-1126` 执行、**早于**本卡新加的 hotkeys 门。
   这是 TOCTOU 类竞态，本卡**没有**覆盖、也**没有**为它挂探针（登记移交，见 §七 #12）。
   另外也没有对脚本里每一个 `open`/`read_*` 逐个挂探针，未覆盖 `--harness-tree` / `--backend-url`
   等本卡未触及的参数组合。
3. **未证明跨平台 / 跨文件系统**。所有实测都在 **macOS 26.5（Darwin 25.5.0）/ APFS / CPython 3.14.4**
   单机上。`O_NONBLOCK` 对普通文件读无影响、`os.fdopen` 与 `read_text` 同语义，在 Linux / 网络文件系统
   / 大小写敏感卷上**没有**验证（平台限定已写进 `:1324-1326` 注释）。
4. **未修 main.js 侧 `!= "file"` 置 `note` 而退出码仍 0（UAT MEDIUM-3）**。本卡 A 场景实测复现了它：
   main.js 是 FIFO 时 `hotkeys note` 写「不是普通文件」，但那一项**本身不进 unreadable**。
   本卡刻意**不扩面**去改（hotkeys 侧与 main.js 侧因此**语义不一致**），登记移交。
5. **未修 CLAUDE_MD 骨架过时与双真相源分叉**（`backend/app/services/vault_init_service.py:40`／
   `scripts/install-vault.sh:71`），二者都在硬边界或非本卡地盘。
6. **未裁 `outputs/**` exclude 类型语义**（D-34 本批不动，`manifest-ruling.md` 只读未改）。
7. **未证明 `timeout=60` 在 CI / 慢机上不 flaky**。依据只有单机余量：同命令正常路径 5 连跑最慢 **0.052s**。
   CI 机型、并发度、冷启动都没测过。若将来出现误红，应先量该环境的正常路径耗时再调，而不是直接加大。
8. **未跑「回退代码 + 整目录」那一格**。目录级那条多出的 `>` 已由**同代码第二跑**证明是非确定性的
   （run1 有、run2 无、两跑之间代码 sha 一字未变，§六.3），再加结构零交集、基线自述 flaky、
   单跑与文件级两侧各 3 次全绿。但我**没有**在回退到 `PREV` 的代码上跑整目录 —— 也就是说，
   「它在没有本卡时也会偶发地红」是**推断**（由非确定性 + 零交集得出），不是直接观测。
9. **未证明 `_is_readonly_open` 的 `os.open` 白名单是完备的**。白名单是**枚举**的六个 `O_*`；
   用白名单外的只读旗标（如 `O_SYMLINK`）或 `getattr(os, "O_RDONLY")` 这类写法会被判违规 ——
   **偏保守、是假红不是假绿**，但确实会让将来写这类代码的人多一道坎（已在 helper docstring 写明）。
10. **未证明本卡对 `_check_hotkeys` 之外的行为零影响**。证据是「既有门 175→176 全绿」+「目录级 diff
    只多出一条既有 flaky」，这是**测试覆盖范围内**的零影响，不是全量行为等价证明。

## 六 目录级与地盘（(h)(i) + 裁判 7/9/10）

### 六.1 目录级跑法与结果

跑法**与 `$BASE` 文件头 `:2` 逐字同**：
`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`

> ⚠️ **口径更正（重要）**：卡文 §二.7 写的是 `"$PYTEST"`（即 `.venv/bin/pytest`），但同段又要求
> 「跑法必须与 `$BASE` 文件头 `:2` 逐字同」，而 `:2` 记的是 **`.venv/bin/python -m pytest`**。
> 二者 `sys.path[0]` 不同（`-m` 会把 CWD 压进 `sys.path`）⇒ 收集面可不同。**逐字同优先**，
> 本卡目录级取 `.venv/bin/python -m pytest`。(e)/(f) 的单文件门与基线无对比关系，runner 选择不影响归因。

| 项 | 实测 |
|---|---|
| 第一跑 | `36 failed, 5077 passed, 48 skipped, 23 xfailed, 29 errors in 542.34s`，rc=1 |
| 验伪锚 `grep -c 'test_deploy_vault_sh' "$RUN"` | **0** ✅（`--ignore` 真生效，且用的是相对路径，R-B14-3） |
| nodeid 集 | base **64** / close **65** |
| `diff base close` | **1 条 `>`**：`FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`（归因见 §六.2） |
| **新门在收集面内** | ✅ `--collect-only` 下 `grep -c test_hotkeys_fifo_does_not_hang_and_reports_unreadable` = **1**；同次 `grep -c test_deploy_vault_sh` = **0**；共收集 5213 项 |
| live 端口 | 第一跑 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)` —— **blocked=1 表示被 W4 门拦下**，未真连 7691/7687；本卡改动文件与该次尝试无关 |

> ⚠️ 裁判 7 存档里 `grep -c 'test_hotkeys_fifo' "$RUN"` = 0 **不是**「新门没跑」的证据 ——
> `-q` 模式下通过的测试根本不打名字。所以另跑了 `--collect-only` 补锚（`collect-anchor-*.txt`）。

### 六.2 那条 `>` 的归因（不靠一句话断言）

存档 `flaky-attribution-20260917T031504.txt`：

| 证据 | 结果 |
|---|---|
| **基线自述**：`$BASE` 文件头 `:3` 原文点名这个 nodeid | 「对 b13 的 65 条**新增 0 / 消失 1**（**flaky** `test_candidate_service::test_accept_candidate_already_accepted_returns_422`）」—— 基线作者自己标的 flaky，且它在 b13 那份里**本来就是红的** |
| **结构归因**：本卡改动文件 vs 该测试的依赖面 | `grep -cE 'verify_vault_install\|test_vault_install_manifest' test_candidate_service.py` = **0**（验伪锚：同一 grep 对 `candidate` 命中 **81**，证明 grep 有效） |
| **行为归因 A**（当前树，含本卡改动）单跑该 nodeid ×3 | **3/3 passed**，rc=0 |
| **行为归因 B**（代码回退到 `PREV`，EXIT trap + sha 前后同）单跑该 nodeid ×3 | **3/3 passed**，rc=0 |
| **文件级**（当前树） | `14 passed`，rc=0，该 nodeid 未红 |
| **同代码第二跑（整目录）** | 见 §六.3 |

⇒ 该红**只在整套执行上下文下出现**，且在「有/无本卡改动」两侧的隔离运行中表现完全一致。
结合结构零交集与基线自述，判为**既有 flaky，非本卡引入**。
未做的那一格（回退代码 + 整目录）已如实写进 §五 #7。

### 六.3 同代码第二跑（整目录）

存档 `unit-close-run2-20260917T031752.txt`（**代码一字未改**：两跑之间
`scripts/verify_vault_install.py` sha256 = `f47606cf…`、`test_vault_install_manifest.py` sha256 = `ef22ae42…`，
存档首部各自记了这两个值；跑法与第一跑逐字同）：

| 项 | 第一跑 | 第二跑 |
|---|---|---|
| 汇总 | `36 failed, 5077 passed, 48 skipped, 23 xfailed, 29 errors in 542.34s` | `35 failed, 5078 passed, 48 skipped, 23 xfailed, 29 errors in 382.37s` |
| nodeid 计数 | **65** | **64** |
| `diff base close` | 1 条 `>` | **完全为空（rc=0）** ✅ |
| `grep -c test_deploy_vault_sh` 验伪锚 | 0 | **0** ✅ |

`diff close.nodeids close2.nodeids` 的**唯一**差异就是那一条：

```
33d32
< FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
```

⇒ **同一份代码、同一条命令，两跑的红集不同**，差的恰好是被基线作者标注为 flaky 的那一条。
这是非确定性的直接证据 —— 它不可能是「本卡引入」的（本卡改动在两跑之间一字未变）。
**(h) 的判据在第二跑上完全满足：`diff base close2` 为空，连 `<` 都没有。**

> 口径声明：这不是 §五 #8 说的那个 2×2 的完整四格（缺「回退代码 + 整目录」那一格）。
> 但它证明的是一个更直接的命题：**在代码固定的条件下该红会自行出现/消失**，
> 于是「run1 出现了它」就不能被归给任何代码改动，包括本卡的。

### 六.4 地盘 / 边界

存档 `territory-gate-20260917T032703.txt`。**审 SHA（本卡代码 commit）= `b3baf7d967692db0b172f5ebb4de9e4ae6357923`**
（`PREV` 与它都经 `git cat-file -t` 验证为真实 commit —— 短 SHA 绝不手工补全）。

| 判据 | 实测 |
|---|---|
| 地盘门 `git --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output'` | **2 files, +217 / -1**，恰为 {`scripts/verify_vault_install.py`, `backend/tests/unit/test_vault_install_manifest.py`} ✅ |
| **地盘门的验伪锚** | 带 exclude **2** 个文件 vs 不带 exclude **41** 个，其中 **39** 条是 `_bmad-output/` 路径 ⇒ exclude 真的在起作用 ✅<br>⚠️ 该锚必须 `git -c core.quotepath=false`：中文路径会被 git 转义成 `\345\256\241…`，`grep '^_bmad-output/'` 会恒 0 = 假阴性。<br>⚠️ 且该锚**只在 commit 之后有效**：commit 前证据文件是未跟踪的，`git diff` 根本不显示它们，锚恒空洞。 |
| commit header 长度（`wc -m`） | **90**（`wc -m` 读进管道时含换行故显示 91）≤ 100 ✅ |
| commit body 每行 ≤ 100（`wc -m`） | 无超限行 ✅ |
| 入库文件含 `*.stderr*` / `*.log` | **0 / 0** ✅（`.gitignore:264` `_bmad-output/审查/**/*.stderr*` 已覆盖，`git check-ignore` 自证） |
| `scripts/vault-install-manifest.json` + `backend/app` | **零改**（`--name-only` 空） |
| `_bmad-output/审查/evidence-g27a/manifest-ruling.md` | **未改**（`git status --porcelain` 空） |
| `outputs/**` exclude 语义 | **未动**（D-34） |
| `fsrs_bridge.py` / `decay_beta.py` | 两个改动文件各 **0** 命中 |
| live vault / 7691 / 7687 | 未写、未连（`blocked=1` 是门拦下，未建立连接） |
| `python-typecheck`（glob `backend/app/*.py`） | **未触发**（不碰 `backend/app`） |
| 批中装包 | **无** |

---

## 七 台账待登记条目（必填 ≥4）

1. **G2-7a MEDIUM-2（FIFO 挂起面）→ 本卡已修**：形态门 `scripts/verify_vault_install.py:1328`（`os.open` + `O_NONBLOCK`）/
   `:1334`（同 fd `os.fstat` + `S_ISREG`）/ `:1339-1346`（非普通文件 ⇒ `_unreadable` ⇒ rc=2）；
   常驻回归门 nodeid `backend/tests/unit/test_vault_install_manifest.py::test_hotkeys_fifo_does_not_hang_and_reports_unreadable`。
2. **地盘补登（已批，R-B14-8）**：`backend/tests/unit/test_vault_install_manifest.py` 是 verify 的**唯一**测试文件
   （`grep -rln verify_vault_install backend/tests` 仅此一文件）、全批无其他车道写它；主 session 第二批裁定 R-B14-8
   已放行并回写手册 §一 T7 行（卡文记 `:65` → **实测 `:67`**）。**设计稿 §3 `:78` 未同步**（仍只列
   `verify_vault_install.py`），请主 session 合并前决定是否回填设计稿（登记项、非阻断；本卡不改设计稿/手册）。
   强制要它的是 **(f) 的常驻 FIFO 回归门**（(e)「既有门全绿」只需跑、不需改）。
3. **设计稿 §4 T7-D `:228` 的『做』列了「CLAUDE_MD 骨架更新」，与 §3 `:78` 地盘及「不碰 backend/app」自相矛盾**。
   骨架在 `backend/app/services/vault_init_service.py:40`（硬边界），R-B14-4 / R-B14-8 均未给 T7-D 任何
   `backend/app` 面 ⇒ 本卡按边界优先**只登记**：CLAUDE_MD 骨架过时 + **脚本建 8 目录
   （`scripts/install-vault.sh:71 SKELETON_DIRS` 实测 8 项；`manifest-ruling.md:70` 记 6 项**已过时**）
   vs 后端建 4 目录（`vault_init_service.py:18`）**的双真相源分叉，需独立卡统一。
4. **`outputs/**` exclude 类型语义三条出路**（`evidence-g27a/manifest-ruling.md` §二.2.2）D-34 本批不动，移交独立卡。
   > 上面 #3 的三个数字**已复测、非照抄卡文**（存档 `registered-only-facts-20260917T032849.txt`）：
   > `install-vault.sh:71` 逐项枚举 **8** 项（原白板/检验白板/节点/outputs/raw/templates/wiki/concepts/wiki/canvases）；
   > `vault_init_service.py:18` **4** 项；`manifest-ruling.md:70` 只列 **6** 项（漏后两项）。
   > 这三个文件本卡**一行未改**（`install-vault.sh` 与 `backend/app` 不在地盘，`manifest-ruling.md` 只读）。
5. **main.js 侧 `:1341 != "file"` 只置 `hotkeys_note`、rc 仍 0（UAT MEDIUM-3 既有缺口）本卡未扩面修**，登记移交。
   本卡的 hotkeys 侧**刻意不照搬**该分支（特殊文件走 `_unreadable` ⇒ rc=2）—— 两侧现在**语义不一致**，
   统一口径需由那张卡裁。
6. **`_is_readonly_open` 的既有盲点已修（顺带，属本卡地盘）**：它此前把 `os.open(path, flags)` 当
   `path.open(mode)` 判、恒返 `False`。本卡加 `os.open` 分支 + 10 条验伪锚（见 §三.3）。
   该 helper 只服务于 `test_verifier_write_calls_are_confined_to_write_report` 这一道门，无其他调用方。
7. **T7-C 残骸**：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-PARSER-r2.md`（0 字节，配额耗尽那次 r2）
   已移入本 session scratchpad 保留，**未删除、未入库**。请主 session 决定是否需要在别处留档。
8. **两份被取代的存档已加注不删**：`fifo-fixed-after-20260917T025453.txt`（探针变量遮蔽 ⇒ 清理断言空洞真）
   与 `negctl-20260917T030121.txt`（`( pytest ) | grep` 让 `$?` 取到 grep 的 rc ⇒ 两行 rc 数字是假的）。
   两份的**结论**都不受影响，但数字/断言有瑕疵，已各自重跑并以较新一份为准。
9. **ruff format 漂移归属（本卡自引入，未走 `LEFTHOOK_EXCLUDE` 旁路）**：首次 commit 被
   `python-lint` 的 `ruff format --check` 拦下（`Would reformat: test_vault_install_manifest.py`）。
   归属判据是一条命令：把 **HEAD 版**的同一文件喂给同一个 `ruff format --check` ⇒ **rc=0 干净**
   ⇒ 漂移是**本卡引入**（我把一行 117 字符的 `frozenset(...)` 拆成了三行，而限长是 120）。
   于是**直接改自己那一行**合回单行，**没有**用协议 §2.3 的过渡旁路 —— 那条旁路是给**存量**漂移的，
   拿它掩盖自己的漂移正是那道存档判据要防的事。存档 `ruff-precheck-*.txt` +
   `existing-gate-postformat-*.txt`（合行后 176 passed 复跑）。
10. **证据目录整理**：`--collect-only` 的全量清单 379K 未入库，代之以 `collect-anchor-extract.txt`
    （判据行摘录 + 末两行），全量移入本 session scratchpad；7 份原本以 `.` 开头的隐藏原始输出
    已改名为 `flaky-single-*.txt` / `flaky-filelevel.txt` 正常入库。证据目录最终 500K。
11. **Codex 各轮**：存档路径 / 绑定 SHA / B-H-M-L 计数 — 见 §八。
12. **【Codex r1 §4 指出的既有缺口，本卡不扩面，登记移交】并发替换下仍有阻塞 open 的路径**：
    普通文件**通过形态检查之后**被换成无写端 FIFO 时，`_leaf_digest:719 read_bytes()`、
    `_probe_regular_readable:756 open()`、main.js 侧 `:1388 read_text()` 仍可能阻塞；
    且 `--source` 摘要在 `:1125-1126` 执行，**早于**本卡新加的 hotkeys 形态门。
    这是 TOCTOU 类竞态，与本卡修的「稳定 FIFO」不是同一个失效面；本卡地盘只允许改两个文件、
    卡文也只点了 hotkeys 侧那一处读点，故**不扩面**。建议独立卡统一处理（对所有读点采用
    「同 fd fstat 之后从该 fd 读」的形态，而不是路径预判 + 另开一次）。
13. **【Codex r2 MEDIUM-3，既有，登记移交】零写门按「表面调用名」筛选，下列写调用根本不进判定**：
    别名 `_open = os.open` 后 `_open(p, os.O_WRONLY | os.O_TRUNC)`；动态取属性
    `getattr(os, "open")(p, os.O_WRONLY | os.O_TRUNC)`；间接调用
    `functools.partial(os.open, p, os.O_WRONLY | os.O_TRUNC)()`；以及 `write_names` 名单本身的遗漏
    （如 `os.ftruncate(fd, 0)`）。三版（PREV / r1 / r2）均存在，属该门的**重新设计**（要静态追踪
    别名与间接调用），不在本卡范围。本卡只做了两件不扩面的事：① 把 docstring 里「`os.*` 全族」
    这句**过强措辞**改成如实表述并逐条列出上述四类未覆盖输入（DD-13 名实一致）；② 在 §五 #9 声明它。
14. **目录级 diff 结果**：run1 base 64 / close 65（1 条既有 flaky，§六.2-六.3）；
    **run2 base 64 / close 64，diff 完全为空**；既有门 175 → 176；回归门 1 passed。

---

## 八 Codex 复核

命令（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" ...`
模型 `gpt-6-astra` · reasoning_effort `ultra` · codex `codex-cli 0.153.3`（`codex --version` 实测）。

### round-1 — `BLOCKER=0 HIGH=0 MEDIUM=1 LOW=0`

- 存档：`_bmad-output/审查/codex-review-CARD-G2-7a-TAIL.md`（已按协议 §2.1 补六行首部，
  会话头自证抄 `.stderr` 的 `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`）
- prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL.md`
- 审查绑定：`b3baf7d967692db0b172f5ebb4de9e4ae6357923`（该轮跑完时即当时 HEAD）
- 五个问题的核对结论：①读取等价成立 ②非普通 hotkeys 均有阻断分支、无「只写 note」的新放行
  ③60 秒合理但偏保守、超时路径不留 FIFO 残留 ④稳定 FIFO 被拦住（`:1388` 不可达）
  ⑤归桶如实、fd 生命周期在当前固定参数下无漏关/双关

**唯一 MEDIUM（已接受并修，0 驳回）**：只读豁免会把展开后的写入旗标误判为只读。

| 项 | 内容 |
|---|---|
| 未被拦下的输入 | `os.open(*[p, os.O_WRONLY \| os.O_TRUNC], os.O_RDONLY)` |
| 为什么成立 | 展开后 `flags = O_WRONLY\|O_TRUNC`（写且截断）、`mode = O_RDONLY`；而 helper 按 AST 的 `args[1]` 读 flags，读到的是 `os.O_RDONLY` ⇒ 判成只读并放行 |
| **独立复现** | 我没有照单全收：单独取出 helper 源码实跑 —— 修前返 `True`；同时把 Codex 那句「旧分支会拒绝 `Starred`」也跑了一遍 —— 旧 helper 对同一输入返 `False`。**「本卡新增缺口」这个定性属实** |
| **自查补出的同族第二例** | `os.open(p, os.O_RDONLY, **kw)` —— 修前放行、旧 helper 拒绝，同一根因（Codex 未点到） |
| 根因 | 加 `os.open` 分支**之前**，展开形态是被「mode 不是字符串字面量」这条**顺带**挡住的；新分支更精确，却把那条附带保证删掉了。**精确性提高 ≠ 强度提高** |
| 修法 | 在 `_is_readonly_open` 的**所有分支之前**拒绝带 `*args` / `**kwargs` 的调用 —— 参数展开时位置绑定静态不可知，与原有「算出来的模式证明不了只读」同一主张 |
| 不误伤的证明 | AST 实测 `verify_vault_install.py` 里**零处**带展开的写名调用 ⇒ 纯增强 |
| 配套 | 验伪锚 **10 → 16** 条；另落 **17 例判定矩阵**（4 正例 / 13 反例，**0 例不符**）：`r1-medium-fix-20260917T033410.txt` |
| 整改后实测 | 文件级 **176 passed 0 failed**；`ruff check` / `ruff format --check` 均过 |
| 整改 commit | `1946e40d` |

### round-2 — `BLOCKER=0 HIGH=0 MEDIUM=5 LOW=1`

- 存档：`codex-review-CARD-G2-7a-TAIL-r2.md`（已补协议 §2.1 六行首部）
- prompt：`prompts/codex-prompt-CARD-G2-7a-TAIL-r2.md`
- 审查绑定：`3735b565b2ada7606aa1294c2d82e0520d7b3a64`；Codex 自述「结束时 HEAD 未变，两个地盘文件无未提交差异」
  ⇒ **该轮绑最终 HEAD 且 B=0 H=0，D-15 条件已满足**
- 五个问题的回答：①展开拒绝本身完整（两条锚 PREV/r1/r2 = False/True/False）②会假红、符合「宁可假红」的保守口径，
  并指出 `**kw` 在真实 `os.open` 上不能覆盖已绑定的 `flags`（重复传参会 TypeError）⇒ 那条锚应理解为**保守拒绝**而非
  「成功覆盖写旗标的实例」——这个更正我接受并照录 ③16 条锚无空判据、但工程覆盖有重叠 ④`offenders == []` 的证明边界未扩大
  ⑤本轮未改 FIFO/hotkeys 逻辑，生产文件两版 blob 完全相同

**逐条分诊（全部先独立复现，未照单全收）**：

| 条目 | 定性 | 处置 |
|---|---|---|
| **M1** `os.open` 被 `functools.partial` 重绑定后仍按位置判 | **本卡新增**（Codex 给的 PREV/r1/r2 = False/True/True，我实跑复现） | **修** |
| **M2** 所有 Attribute 调用都当绑定方法 ⇒ `io.open("log","w")` 判成只读 | 三版均存在（既有） | **修**（4 行、纯增强、Codex 给了确切输入） |
| **M3** 名字筛选漏别名 / `getattr` / `partial` / 名单遗漏（`os.ftruncate`） | 三版均存在（既有，属门的重新设计） | **登记移交**；另把 docstring 里「`os.*` 全族」这句**过强措辞**改成如实表述并列出四类未覆盖输入（DD-13 名实一致） |
| **M4** 非普通 main.js 只记 note、不计退出码 | 既有 **UAT-G2-7a MEDIUM-3**，卡文 §三明令不扩面 | **登记移交**（§七 #5） |
| **M5** main.js 形态检查与内容读取之间的并发替换窗口 | 既有，Codex 自述「不是本卡新引入」 | **登记移交**（§七 #12） |
| **LOW-1** FIFO 门的路径断言与理由断言可由**两条不同的行**分别满足 | **本卡新增**（我自己写的门） | **修** |

**LOW-1 的分量比它的级别大**——Codex 给的对照报告：

```text
## unreadable
  .obsidian/hotkeys.json.bak  — 读不进去                      ← 满足「路径」那条(startswith 是前缀不是相等)
  other-file  — 不是普通文件(FIFO/设备等特殊文件)              ← 满足「理由」那条(另一行)
```

实测三条断言**全过**，而报告里**没有任何一条 finding** 是「hotkeys 因形态不可读」。
这正是本卡 §四「负控-2 的关键观察」里自己写下的原则——**判据要绑到同一个身份**——却在同一道门上没做到。
修法：先按**路径相等**筛出 hotkeys 那一行、断言**恰好一条**，再要求**那一条**含形态理由。

**整改后实测**（`r2-fix-20260917T034409.txt` / `negctl-postr2-*`）：

| 判据 | 结果 |
|---|---|
| 判定矩阵 | **20 例 0 不符**（正例 5 / 反例 15；新增 `io.open`/`builtins.open` 三例） |
| LOW-1 对照报告 | 按路径相等筛出 **0** 行 ⇒ `len(...)==1` 断言变红 ✅；真实报告筛出 **1** 行且理由匹配 ✅ |
| M1 重绑定判据的误伤面 | 生产脚本 **0** 命中 ✅（一刀切会误伤 `:899` 的局部变量 `link = cur / rel`，故只拦 `<owner>.<写名> = …` 与遮蔽内置 `open` 两类） |
| 文件级 | **176 passed 0 failed** |
| 正控 / 负控-1 / 负控-2 | 绿 / 红在 `TimeoutExpired` / 红在**新的同条 finding 身份断言** ✅ |
| ruff | check + format 均过（format 漂移又是本卡自引入、已改回单行） |

> ⚠️ **负控重跑时先出了一次假绿，已识别并重跑，两份都留档**：
> `negctl-postr2-*.txt` 的 NC1 用 `git show HEAD:…` 取「改前版本」——**代码提交之后 HEAD 已含修复**，
> 于是「还原到改前」成了空操作（`变异态计数(应 0)=4`、门 rc=0）。根因是把 `HEAD` 当还原基准，
> 而 `HEAD` 是**位置锚**、一 commit 就移动。改用**值锚** `09567e35` 重跑（`negctl-postr2-nc1-redo-*.txt`）：
> 变异计数 0、门 rc=1 红在 `raise TimeoutExpired`、sha 前后逐字同。
> （首轮 `negctl-20260917T030322.txt` 那次跑在提交**之前**，当时 HEAD 就是 T7-C 末 commit，那次有效。）

### round-3 — 待送（因 r2 后又改了代码，D-15 要求重绑）

> **D-15 状态**：r1 已经满足「绑最终 HEAD 且 B=0 H=0」，MEDIUM 本可只登记不修。
> 之所以仍然修：那条 MEDIUM 是**本卡自己造成的护栏削弱**（旧代码拒绝、新代码放行），
> 把一道零写门留得比接手时更弱，代价会在后面的卡上复利。改代码 ⇒ 按 D-15 必再送一轮。
