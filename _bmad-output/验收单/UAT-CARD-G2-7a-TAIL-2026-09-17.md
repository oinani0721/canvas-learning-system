# UAT — CARD-G2-7a-TAIL（部署校验器 hotkeys 无写端 FIFO 挂起先修）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-G2-7a-TAIL]` · 车道 **T7 skills-writer** `card-t7-skills`（本车道第 **4/4** 张，**T7 末卡**）
> `PREV`（= T7-C `CARD-SKILL-PORT-LINT-PARSER` 末 commit）= `09567e35bf393c34d1ab185e89e6b9effede7141`
> 证据目录 `_bmad-output/审查/evidence-g27a-tail/`（`.txt` 存档，`*.stderr*` 不入库）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T7-D.md`（feature 主干树那份）

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
2. **未穷尽全部读点**。已实测的是 Codex 问题 ④ 点名的四处（main.js 侧、copy 件无/有 `--source`、源侧
   copy 件），四格**都没挂**；`_leaf_digest` 的 `lstat`+`S_ISREG` 前置也已读过代码确认。但我**没有**
   对脚本里每一个 `open`/`read_*` 调用逐个挂 FIFO 探针，也没有覆盖 `--harness-tree` / `--backend-url`
   这些本卡未触及的参数组合。
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

| 判据 | 实测 |
|---|---|
| 地盘门 `git --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output'` | ⊆ {`scripts/verify_vault_install.py`, `backend/tests/unit/test_vault_install_manifest.py`}（见 §七） |
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
9. **Codex 各轮**：存档路径 / 绑定 SHA / B-H-M-L 计数 — 见 §八。
10. **目录级 diff 结果**：base 64 / close 65，1 条 `>`（既有 flaky，§六.2）；既有门 175 → 176；回归门 1 passed。

---

## 八 Codex 复核

<!-- CODEX_PLACEHOLDER -->
