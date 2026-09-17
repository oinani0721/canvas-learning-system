# UAT — CARD-TOOLCHAIN-UNIFY（lefthook 版本三岔 install-free 收口 + `scripts/` 补必错级 ruff select）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-TOOLCHAIN-UNIFY]` · 车道 **T8** 第 **5/7** 卡（前 T8-D，后 T8-F）
> 树 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools` · 分支 `card/t8-tools`
> 前提 commit `PREV` = `7aacbc87`（T8-D 末 commit） · 本卡 commit = `99e15a4e`（单独一条）
> 证据目录 `_bmad-output/审查/evidence-toolchain-unify/`（全部 `.txt`，末行 `rc=`）
> **不 push**。台账未改（只主 session 改），待登记条目见 §六。

---

## 〇 第 0 分钟自证

存档 `evidence-toolchain-unify/state-selfcheck-20260917T124628.txt` + `state-selfcheck-part2-20260917T124646.txt`（末行 `rc=0`）。

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-t8-tools` ✅ |
| 分支 | `card/t8-tools` ✅ |
| `PREV = git rev-parse HEAD` | `7aacbc87cc0241130ddcc55c40892c4e95d8dbbe`（短 `7aacbc87`） |
| `git merge-base --is-ancestor 08100483 HEAD` | yes（B14_BASE 是祖先） |
| `backend/.venv/bin/pytest` / `ruff` / `backend/.env` / `pyright` | 四项皆在；ruff **0.15.9** |
| 基线自证（**R-B14-2** 唯一口径 `grep -vc '^#' $BASE`） | **64** ✅ |
| `which lefthook` | `/opt/homebrew/bin/lefthook` |
| `lefthook version`（**裸**，R-B14-1） | `2.1.6`，rc=0 |
| `node_modules/.bin/lefthook` | `No such file or directory`（无 live npx） |
| `node_modules/lefthook/package.json` | absent |
| `git diff --stat 08100483 HEAD -- package.json package-lock.json ruff.toml` | **空**（本卡三文件在 `B14_BASE` 与开工点间零改动） |

### 〇.1 `git status --porcelain | wc -l` = 1 —— 拆证（不是前卡留脏）

裁判 1 的 tee 文件在**它自己运行的那一刻**已被创建，于是 `git status` 数到 1。拆开看（`state-selfcheck-part2-*.txt`）：

- `git status --porcelain --untracked-files=no` → **空**（跟踪文件零改动 ⇒ T8-D 收工态干净）；
- 唯一未跟踪项 = `_bmad-output/审查/evidence-toolchain-unify/`，即本卡自己的证据目录。

本 session 的**第一条命令**（进任何目录、建任何文件之前）跑的 `git status --porcelain` 输出为空——该次未 tee，故不作依据，以上面两条可复核的拆证为准。

### 〇.2 卡文 §〇 十行逐条核（无漂移，**一处措辞补强**）

| 卡文 §〇 事实 | 实测 | 结论 |
|---|---|---|
| `package.json:19 "lefthook": "^1.6.0"`；`:7 "prepare": "lefthook install"` | 逐字同 | ✅ |
| `package-lock.json:14` 声明 range `^1.6.0`；`:1491` resolved `lefthook-1.13.6.tgz` | 逐字同；另实测 `:1489 "node_modules/lefthook"` / `:1490 "version": "1.13.6"` | ✅ |
| node_modules 未安装、无 live npx | 逐字同 | ✅ |
| brew lefthook `2.1.6` 在 PATH | 逐字同，rc=0 | ✅ |
| `pre-commit` 的 `call_lefthook()` 优先级 ①`$LEFTHOOK_BIN` ②PATH 上 `lefthook` ③`node_modules/...` | 逐字同；`git rev-parse --git-common-dir` = 主仓 `.git`（三树共享） | ✅ |
| root `ruff.toml` `:36 line-length = 120` / `:38 [lint]` / `:39 select = []` | 逐字同 | ✅ |
| `backend/ruff.toml` `:6 line-length` / `:7 target-version = "py39"` / `:9 [lint]` / `:10 select = ["E9", "F63", "F7", "F82"]` | 逐字同 | ✅ |
| `lefthook.yml:118` python-lint glob `{backend,src,scripts}/*.py` | `:117 python-lint:` / `:118 glob:` 逐字同 | ✅ |
| 卡文说 python-lint「跑 `ruff check` + `ruff format --check`」 | 实测 `:124 ruff check` + `:126 ruff format --check` 两段都在 | ✅ |
| `ruff check scripts/`（select=[]）= 24 invalid-syntax | 见 §四-A.1 判据 2 | ✅ |

**补记（不是漂移，是新发现的旁证）**：`lefthook.yml:113-116` 有一段前卡（Z7-A / CARD-TOOL-lint-glob）留下的注释，原文写着「真正拦住 `scripts/` 的是下面的 `ruff format --check`。开 `scripts/` 必错级规则集（对齐 `backend/ruff.toml` 的 E9,F63,F7,F82）= 另一张卡, 已登台账。」——**本卡就是那张卡**，口径与该注释逐字一致。

---

## 一 本卡改了什么（地盘 = 恰三文件，4 增 3 删）

```
 package-lock.json | 2 +-
 package.json      | 2 +-
 ruff.toml         | 3 ++-
```

### 一.1 npm 侧 install-free 锁到 exact `1.13.6`

| 文件:行 | 改前 | 改后 |
|---|---|---|
| `package.json:19` | `"lefthook": "^1.6.0"` | `"lefthook": "1.13.6"` |
| `package-lock.json:14` | `"lefthook": "^1.6.0"` | `"lefthook": "1.13.6"` |
| `package-lock.json:1490-1491` | `"version": "1.13.6"` / `resolved …lefthook-1.13.6.tgz` | **未动** |
| `integrity` / 10 个平台 optionalDependencies | — | **未动** |

结果：package.json exact == lock 声明 == lock resolved == `1.13.6`，npm 侧**内部自洽**。
⛔ 未跑 `npm install`、未升 brew、未改 `.git/hooks`、未装任何包。

### 一.2 runner-of-record = **brew 2.1.6**（判定依据，不是偏好）

`call_lefthook()` 的三级优先级里第 ② 级是 PATH 上的 `lefthook`；`node_modules` 缺席使第 ③ 级永不可达 ⇒ 机器上真实执行 hook 的恒是 brew 2.1.6。**本卡提交时 lefthook 自己打印的横幅就是 `🥊 lefthook v2.1.6  hook: post-commit`**（见 §四-A.1 判据 8），这是一次不依赖推断的运行期确认。

### 一.3 `ruff.toml` 的 `[lint] select`

```diff
 [lint]
-select = []
+# CARD-TOOLCHAIN-UNIFY [BATCH-2026-09-11-第十四批]: 与 backend/ruff.toml 同步必错级(语法/错误比较/if-tuple/未定义名); 存量风格规则(2000+)不在此启用
+select = ["E9", "F63", "F7", "F82"]
```

`line-length = 120` 未动；**未新增** `target-version`（该文件 `:23-35` 的注释解释了为什么刻意不写——py312 会放行 CI 跑不了的语法）；未启用任何风格规则（F401/I/C4 的 2000+ 存量另开卡）。新 `select` 行与 `backend/ruff.toml:10` **逐字相同**（判据 8 做了字符串等值断言）。

---

## 四-A 🤖 Claude 已代验（证据全在 `_bmad-output/审查/evidence-toolchain-unify/`）

### 四-A.1 裁判逐条回执

| # | 裁判 | 存档（全文件名，不用 glob） | 结果 |
|---|---|---|---|
| 1 | 状态 + §〇 逐字核 | `state-selfcheck-20260917T124628.txt` / `state-selfcheck-part2-20260917T124646.txt` | ✅ 见 §〇 |
| 2 | ruff **先红**（当前配置，⛔ 不加 `--select`） | `ruff-scripts-before-20260917T124705.txt`（rc=1） | `24  invalid-syntax` / `Found 24 errors.`；显式负断言 `grep -cF 'F821'` = **0**（落档于 `ruff-before-assertions-20260917T124705.txt`） |
| 3 | ruff **对照输入**（验伪锚，命令行 `--select E9,F63,F7,F82`） | `ruff-scripts-probe-20260917T124705.txt`（rc=1） | `24 invalid-syntax` + `1 F821` = `Found 25 errors.` ⇒ **select 真改变可见面** |
| 4 | F82 定位 | `ruff-scripts-f82-locate-20260917T124705.txt`（rc=1） | `scripts/validate-source-citations.py:392:4  F821 Undefined name 'technology'` |
| 5 | ruff **改后** | `ruff-scripts-after-20260917T124753.txt`（rc=1） | `24 invalid-syntax` + `1 F821` = `Found 25 errors.`；正断言 `grep -cF 'F821'` = **1** |
| 6 | before/after 唯一差 | `ruff-before-after-diff-20260917T124809.txt`（rc=0） | 见 §四-A.2 |
| 7 | lefthook 版本三处 + 残留 range | `version-grep-before-20260917T124731.txt`（改前锚，命中 2 行）/ `version-grep-after-20260917T124753.txt`（rc=0） | 改后 `grep -rnF '"lefthook": "^1.6.0"'` 两文件 **0 命中**（grep_rc=1）；`package.json:19` 与 `package-lock.json:14` 各命中 `"lefthook": "1.13.6"`；`:1491` resolved 仍在；裸 `lefthook version` → `2.1.6`（rc=0） |
| 8 | `select` 行逐字同 backend | 同上文件 | `root : 40:select = ["E9", "F63", "F7", "F82"]` / `backend: 10:select = ["E9", "F63", "F7", "F82"]` → **逐字相同: YES** |
| 9 | JSON / TOML 合法性 | `json-toml-validity-20260917T124753.txt`（rc=0） | `json ok` / `toml ok`；另打印 tomllib 解析回的 `lint.select` = `["E9","F63","F7","F82"]`、`line-length` = 120、`has target-version: False` |
| 10 | ruff zsh 数组判据（协议 §2.2） | `ruff-array-and-rootsurface-20260917T125826.txt`（rc=0） | `files=0`（本卡零 `backend/**/*.py` 改动，该判据对本卡不适用）；**双侧锚**：同一文件 `--select F821` rc=1、`--select F401` rc=0 ⇒ 锚不是恒红 |
| 11 | root 治理面改前/改后普查 | `rootsurface-before-after-v2-20260917T125857.txt`（rc=0） | 见 §四-A.3 |
| 12 | `tests/unit` 目录级 | `unit-close-20260917T124820.txt`（末行 rc=1）+ `unit-diff-20260917T125806.txt`（rc=0）+ `base.nodeids` / `close.nodeids` | `35 failed, 5161 passed, 48 skipped, 23 xfailed, 29 errors`；nodeid 集 **64 vs 64**，`diff` 完全相同（**0 新增、0 消失**） |
| 13 | 地盘门（post-commit） | `territory-gate-20260917T130018.txt`（rc=0） | 见 §四-A.4 |

### 四-A.2 「唯一差 = F821 由不报变报」——为什么不能只看 diff

`diff before after` 输出的是 `1,2c1,3`，**第 1 行也变了**。如实拆开：

```
< 24		invalid-syntax          ← before
> 24	    	invalid-syntax          ← after（多了几个空格）
```

变的只是**列对齐空白** —— ruff `--statistics` 在出现规则码列（`F821`）后会重排对齐。计数两边都是 **24**。所以这里没有只用 diff 收口，另补了按内容取值的四条计数断言（before `Found 24 errors`=1 / before `F821`=0 / after `Found 25 errors`=1 / after `F821`=1），全部落在同一份存档里。

> 语义上的解释（供复核）：`invalid-syntax` 属**解析器层**，在 AST 建起来之前就报，不受 `select` 支配；这正是卡文 §〇 那句「`select = []` 的 lint 面 = 空集，只剩解析器 invalid-syntax」的含义。

### 四-A.3 root 治理面（288 个非 `backend/` tracked `.py`）的完整普查

卡文只要求核 `ruff check scripts/`。本卡**多做了一步**，把「新 select 到底在整个 root 治理面上多揭出什么」量了出来（只读，零代码改动）：

| | `invalid-syntax` | 其它规则 | 合计 |
|---|---|---|---|
| 改前（内联 `--config 'lint.select=[]'`） | 131 | 0 | `Found 131 errors` |
| 改后（仓内新 `ruff.toml`） | 131 | **2 × F821** | `Found 133 errors` |

新揭出的**恰两处**，零 `E9` / `F63` / `F7`：

1. `scripts/validate-source-citations.py:392:4` — `F821 Undefined name 'technology'`。**落在** lefthook `python-lint` 的 glob 内 ⇒ 将来暂存该文件的提交会被拦。Z7-A 台账已登记的存量真缺陷（`:392` 是一段 Markdown 模板被放进 **f-string**，`**{technology}**` 的花括号被当表达式求值）。⛔ `scripts/*.py` 不在本卡地盘，**登记不修**。
2. `_bmad-output/审查/evidence-w4-5/cases/case-d2.py:6:21` — `F821 Undefined name 'app'`。是 W4-5 卡留下的负控样例文件，**不在** `{backend,src,scripts}/*.py` glob 内 ⇒ 不影响任何提交。

顺带实测的 glob 覆盖面：`src/*.py` tracked 计数 = **0**（glob 的 `src/` 段目前覆盖空集）；`scripts/` 下 tracked `.py` **顶层 52 + 子目录 42 = 递归 94**。

> ⛔ **本节初版在这里写错过两句，已更正，见 §四-A.8**（初版写「`scripts/*.py` 顶层 94 个」「单星 glob 不含子目录 ⇒ `api-reality-dashboard.py` 不被 glob 拦」，两句都不成立）。同名错误也留在已入库的 `rootsurface-before-after-v2-20260917T125857.txt:30-31` 两行里，该存档**不改**（保留原始记录），更正以 §四-A.8 与 `lefthook-glob-empirical-v2-20260917T130857.txt` 为准。

### 四-A.4 地盘门 + 验伪锚

`territory-gate-20260917T130018.txt`：

- `git --no-pager diff --name-only --no-color $PREV HEAD -- . ':(exclude)_bmad-output'` → 恰 **3** 个：`package-lock.json` / `package.json` / `ruff.toml`；子集判定「越界文件: 无」。
- 禁改面逐条显式核，**全部 0**：`lefthook.yml` / `pyrightconfig.json` / `backend/ruff.toml` / 任何 `*.py` / `backend/app` / `canvas-vault/.claude/scripts/{fsrs_bridge,decay_beta}.py`。
- **验伪锚**：去掉 `':(exclude)_bmad-output'` 后文件数 **21**，其中 `_bmad-output/` 前缀 **18** ⇒ 21−18 = 3 = 带 exclude 的数，锚成立（不是空洞判据）。
- **写法自证**：同一命令改用 `':!_bmad-output'` → **rc=128**，实证该写法在本机不可用（协议 §1 点名的假绿形态）。

### 四-A.5 ⛔ 如实登记：本卡的判据**自身**出过两次问题（都已更正并留档）

这两份**有缺陷的**存档**一并入库**（`ruff-array-and-rootsurface-20260917T125826.txt` / `rootsurface-before-after-20260917T125840.txt`），不删，供复核核对更正是否成立。

**(i) `git ls-files` 的中文路径 quoting ⇒ 129 条 `E902 io-error` 假命中。**
第一版普查用 `git ls-files '*.py'` 取文件集，git 默认对非 ASCII 路径做 C-quoting（输出成 `"_bmad-output/\345\256\241\346\237\245/…"`），ruff 拿这个字面量去 open 必然失败，于是报 129 条 `E902`——**恰好等于 `_bmad-output` 下的文件数**。如果不查根因，会得出「本卡新增 129 条必错级命中」的相反结论。
更正：`git -c core.quotepath=false ls-files`。更正后 root 治理面 288 文件、零 `E902`。

**(ii) 把「改前」配置写到会话临时目录再 `--config` 指过去 ⇒ 两侧不可比。**
第二版用 `--config <scratchpad>/ruff-before-equivalent.toml` 表达「改前的 `select = []`」，结果 `invalid-syntax` 改前 **127** / 改后 **131**，差 4 条。根因：root `ruff.toml` **刻意不写 `target-version`**，ruff 靠同目录 `pyproject.toml:6` 的 `requires-python = ">=3.9"` 推断出 py39；配置文件一旦搬到别处，这条推断链就断了，目标版本变化直接改写「哪些 f-string 算语法错」（该文件 `:33-35` 的注释正记着 py39/py310/py311 各 24 条、py312 21 条）。**这不是 select 的差，是目标版本的差。**
更正：改用**内联覆写** `--config 'lint.select=[]'`，仓内 `ruff.toml` 仍被正常发现，只换 `select` 一个键。更正后两侧 `invalid-syntax` 都是 131，差额恰为 2 条 F821。同一跑里带了验伪锚（内联换回 `select=["E9",…]` 必须重新出现 F821，实测出现）。

### 四-A.6 一处存档含 `No such file`，是**故意的阴性探针**，不是跑失败

协议 §2.2 有「正文含 `No such file` 的一律不入库」。本卡 `state-selfcheck-20260917T124628.txt` 命中 1 次：

```
--- node_modules live npx probe ---
ls: node_modules/.bin/lefthook: No such file or directory
```

这行**就是判据本身要的结果**（证明没有可跑的 npm 侧二进制，因而 `call_lefthook()` 永远走不到第 ③ 级）。该文件其余部分是本卡的承重状态核。**显式声明后入库**，不按失败产物剔除。

### 四-A.7 卡文 §三 的「只改 `[lint] select` + 上方一行注释」被严格遵守——代价登记

`ruff.toml:2` 仍写着 `# NOTE: Lint rules temporarily disabled due to 2000+ pre-existing violations.`，而本卡已启用四条必错级规则 ⇒ 该行现在是**半失实**的。

按卡文 §三 对 `ruff.toml` 的允许面（「只改 `[lint] select` + 上方一行注释」），本卡**没有**动 `:2`。文件内的纠正在 `:39`（本卡新增的那行注释明确写了「同步必错级 / 存量风格规则不在此启用」），读者自上而下读到 `:39` 会被纠正，但头部单看仍会误导。**登记为待处置**（§六 ⑨），并在 Codex prompt 问题 ⑥ 里请其独立定级。

### 四-A.8 ⛔ 第三处判据问题：由 Codex round-1 MEDIUM 指出，本卡独立复测后**确认自己错了**

**Codex 的指控**：我把 `scripts/*.py` 的 94 记成「顶层」，且据此断言单星 glob 不含子目录、`scripts/spec-tools/api-reality-dashboard.py` 不被 hook 拦。

**我没有直接采信，分两步自己测：**

**(1) 计数 —— 确认我错了。** `git ls-files 'scripts/*.py'` = 94，但 git pathspec **不带 `:(glob)` 时 `*` 是跨 `/` 的**；`git ls-files ':(glob)scripts/*.py'` = **52**，子目录 42，52+42=94。所以 94 是**递归数**，不是顶层数。

> 这与 §四-A.5 的两处是**同一类**错误：用了一个 glob 语义与我假设不同的工具。更糟的是我当时跑了两条命令「交叉验证」（`scripts/*.py` 与 `scripts/**/*.py`），两条**用的是同一个引擎、带同一个坑**，于是一致地给出 94——并列的同层判据不构成独立验证。

**(2) glob 是否跨目录 —— 不读文档，直接在 lefthook 2.1.6 上实测。** 用 `lefthook run --job python-lint --file <文件>` 喂单个文件看作业是否被选中。⚠️ 安全措施：带 `--no-auto-install`（防隐式重装**跨三树共享**的 `.git/hooks`）+ `--no-stage-fixed`，并落跑前/跑后 `shasum -a 256`（`.git/hooks/pre-commit` / `lefthook.yml` / 两个目标 `.py`）**逐字节相同**，被跑的两条命令（`ruff check` / `ruff format --check`）本身只读。

> ⚠️ 顺带更正一条口径细节（**不推翻 R-B14-1**）：`--no-auto-install` 在 2.1.6 里**仍存在**，但它是 `lefthook run` 的**子命令 flag**，不是全局 flag。R-B14-1 实测的是 `lefthook --no-auto-install version`（全局位置）⇒ `Incorrect Usage` + rc=1，该裁定与「批内 `lefthook version` 一律裸调用」的结论**完全成立**；本节只是记下「`run` 子命令下该 flag 可用」这一实测事实。

**(3) 第一版测试自己也有混淆项，也更正了。** 初测给对照组加了 `--force`（"文件没变也不跳过"）——那正是被测的跳过机制本身，控制组因此不成立（存档 `lefthook-glob-empirical-20260917T130842.txt`，保留）。去掉 `--force` 重跑得到干净的 2×2（`lefthook-glob-empirical-v2-20260917T130857.txt`）：

| 输入 | python-lint | rc | 结论 |
|---|---|---|---|
| A′ `scripts/spec-tools/api-reality-dashboard.py`（子目录 `.py`） | **跑了**，输出该文件的 invalid-syntax | 1 | glob **确实跨目录** ⇒ Codex MEDIUM 成立，我的登记错了 |
| B′ `scripts/validate-source-citations.py`（顶层 `.py`） | **跑了**，输出 `F821 Undefined name 'technology'` | 1 | 本卡新 `select` 在**真 hook** 上确实会拦 |
| C′ `ruff.toml`（非 `.py`） | `python-lint (skip) no files for inspection` | **0** | 正常路径**整作业跳过** |
| D′ 本卡真实三文件全给 | `python-lint (skip) no files for inspection` | **0** | **本卡提交确实不受新 select 影响** |

**更正后的结论**（取代 §四-A.3 初版与 §六 ④ 初版）：`scripts/spec-tools/api-reality-dashboard.py` 的 24 条 invalid-syntax **在** `python-lint` 的覆盖面内，将来暂存它的提交**会被拦**——但那与本卡无关（`invalid-syntax` 属解析器层，`select = []` 时就已可见，本卡的 `select` 没有改变它的可见性）。

**副产品：一条值得登记的真实风险。** 带 `--force` 的那次误跑显示：当 `{staged_files}` 过滤为空、而作业又**没有**被跳过时，`lefthook.yml:124` 的 `ruff check {staged_files}` 会展开成**不带文件参数的 `ruff check`**，即**从 cwd 扫全树**（实测它扫到了 `_bmad-output/审查/evidence-ast-flag/rounds2.py`）。正常提交路径有 C′/D′ 证明的跳过兜底，触不到；但 `--force` / `--all-files` / 或将来任何改动使该跳过失效时就会触发。本卡的新 `select` 不是它的成因，却**放大了它的影响半径**（全树扫描现在会额外报 `_bmad-output` 下的 F821）。登记见 §六 ⑫。

---

## 四-B 👤 你来验（2 分钟，只读这一段）

**这张卡解决了什么：**

你的仓库里有个「提交前自动检查」的工具叫 lefthook。它的版本以前在三个地方写得不一样：项目清单里写「1.6 以上都行」，锁定文件里实际钉的是 1.13.6，而你电脑上真正在跑的是 brew 装的 2.1.6。三个数字对不上，就意味着换台电脑、或者哪天重装依赖，跑的可能是另一个版本，检查结果就会不一样。

这张卡把**项目清单和锁定文件统一到同一个数字（1.13.6）**，并且明确写下「这台机器上真正干活的是 brew 的 2.1.6」。剩下那件事——把 brew 和 npm 两边彻底并成一个数字——需要联网装东西，属于会影响所有并行开发分支的动作，按规矩得先报备再做，所以这次**只做了不用装任何东西就能做的那一半**，另一半原样登记移交。

另一件事：你的 `scripts/` 目录（放各种小工具脚本的地方）以前**几乎没有检查**——只有「语法写错了」会被拦，「用了一个根本不存在的变量名」这种会在运行时炸掉的问题会一路放行。这张卡把后端一直在用的那套「最严重的四类错误」原样搬了过来。搬过来之后立刻就照出一个真问题：`scripts/validate-source-citations.py` 第 392 行用了一个不存在的名字。这个文件不归这张卡管，所以**只记录、没有动它**。

**一句话：** 我不用再担心同一个检查工具在不同地方装了不同版本、结果对不上；脚本目录也终于和后端一样会拦住最严重的那类错误——我感觉工具链终于一条心、可以放心提交。

**felt-sense**：以前提交时心里有个模糊的「不知道这次跑的是哪一版」的悬空感，现在落地了；另外知道了 `scripts/` 那片地方一直是"裸奔"的，虽然这次只堵上了一个口子，但至少**看得见**了——看不见的风险才是最难受的。

**如果你只想抽查一条**：打开 `_bmad-output/审查/evidence-toolchain-unify/ruff-before-after-diff-20260917T124809.txt`，最后几行是一组数字对照——改之前"未定义名"这类错误被数到 **0** 次，改之后数到 **1** 次。就这一个数字从 0 变 1，说明门确实从"看不见"变成了"看得见"。

---

## 五 本卡未证明什么

1. **未证明 brew 2.1.6 与 npm 1.13.6 两 runner 行为等价**。本卡只证明了 npm 侧**三个数字自洽**与 brew 侧**实际执行者身份**，没有证明两个版本跑同一份 `lefthook.yml` 会得到相同结果。
   > ⛔ **措辞更正（Codex round-1 ⓪）**：初版写「统一到单一 SSoT **需** `npm install --save-exact --package-lock-only lefthook@2.1.6` 或改 brew」，这句隐含了「只有这两条路」。Codex 指出：把 npm 声明**与完整 lock 解析元数据**（version / resolved / integrity / 10 个平台包）一并对齐到 2.1.6，**原则上可以是纯文件变更**，不必然要求当场安装。本卡**没有**展开或验证这条备选路径的可行性（手写 integrity 极易产非法 lock，这是卡文 §一 (d) 明令不动 `:1491` 的理由）。因此正确的表述是：**本批不做**（需 §2.3 授权 + 无法在禁装前提下完成「两套实际 runner 同版」的实测验收），而不是「技术上无路可走」。
2. **未证明 `npm ci` 在锁 exact 1.13.6 后于无 brew 的 CI 里真能装出可跑的 hook**。本卡不跑 `npm install` / `npm ci`、不验 CI。特别地，`package.json:7` 的 `"prepare": "lefthook install"` 会在 `npm ci` 时执行、且那时 `node_modules/.bin` 在 PATH 前部 ⇒ 装出的 hook 由 **1.13.6** 生成——这条只在文档里推断，**没有实测**。
3. **未修**被新 select 揭出的两处 F821（`scripts/validate-source-citations.py:392` 的 `technology`、`evidence-w4-5/cases/case-d2.py:6` 的 `app`），也**未修** `scripts/spec-tools/api-reality-dashboard.py` 的 24 条 invalid-syntax（`:120` 真语法错，与目标版本无关）。本卡只证明了 select 让门**看得见**它们。
4. ~~未真跑 pre-commit hook 做对照~~ —— **已在 §四-A.8 补测，本条降为**：已实测 `lefthook run --job python-lint --file <文件>` 的四档（子目录 `.py` / 顶层 `.py` / 非 `.py` / 本卡三文件），证明 C′D′ 两档整作业跳过、rc=0。**仍未证明**的是：(i) 未跑**完整的** `pre-commit`（只跑了 `python-lint` 一个 job，其余 7 个作业与本卡三文件的交互仍只有「本次提交实际通过」这一条旁证）；(ii) `lefthook run --file` 与真实 `git commit` 走的文件来源不同（前者是显式文件列表，后者是 staged 列表），两者在 glob 过滤上同形但未逐字节比对实现。
5. **未证明把 select 抬到风格规则（F401 / I / C4）后 `scripts/` 的存量规模**。`ruff.toml:2` 记的「2000+」是历史数字，本卡没有复测它在今天是多少（另开卡）。
6. **root 治理面普查的「改前」是用内联 `--config 'lint.select=[]'` 模拟的，不是真的回退文件再跑**。虽然带了验伪锚（换回 select 必须重现 F821），但严格说它证明的是「内联覆写等价于 `select=[]`」而非「回退文件后逐字节同」。`scripts/` 面的 before/after 则是**真配置**两跑，无此限制。
7. **未证明 `mutant-residue-scan` 等其余 pre-commit 作业与本卡三文件无交互**。本卡只核了 `spec-sync-flat` / `spec-sync-root`（glob 限 `backend/app`）、`ghost-files`（限 `docs/{stories,epics}` 未跟踪项）、`python-lint` / `python-typecheck` / `cypher-vault-filter-lint`（限 `.py`）；其余靠「提交实际通过」这一条旁证。

---

## 六 台账待登记条目

1. **lefthook 版本三岔现状 → 本卡 install-free 收口**：`package.json` range `^1.6.0` / lock 声明 `^1.6.0` / lock resolved `1.13.6` / brew `2.1.6`，且 `node_modules` 未安装（无 live npx）。本卡 commit `99e15a4e` 把 npm 侧两处声明锁到 exact `1.13.6`，**runner-of-record = brew 2.1.6**。（承接台账 §一.b `Z7-A` 行的「package-lock 锁 lefthook 1.13.6 vs 本机 2.1.6」与 §一 X8 登记行的「lefthook 三版本统一」。）
2. **⛔ brew(2.1.6) ↔ npm(1.13.6) 跨 runner 统一到单一 SSoT —— 移交**：候选路径至少三条 —— (i) `npm install --save-exact --package-lock-only lefthook@2.1.6`（联网重算 lock）；(ii) 改 brew 侧降到 1.13.6；(iii) **纯文件手写** lock 的全部 2.1.6 解析元数据（Codex round-1 ⓪ 指出这在原则上 install-free 可达，但需手写 integrity + 10 个平台包，本卡未验证其可行性，风险是产非法 lock）。三条都触及**跨车道共享的 `.git/hooks`** 或需联网 ⇒ **升 lefthook = 协议 §2.3 批级事件** + §0.2.5 批中禁装，请主 session 按 §2.3 通告并授权后另起卡。本卡只交 install-free 子集。
3. **新 select 揭出的两处 F821（登记不修）**：`scripts/validate-source-citations.py:392` `technology`（Z7-A 已登记的存量；**在** lefthook glob 内，将来暂存它的提交会被拦）；`_bmad-output/审查/evidence-w4-5/cases/case-d2.py:6` `app`（W4-5 负控样例，**不在** glob 内）。`scripts/*.py` 与 `_bmad-output/**` 都不在本卡地盘，修复另立卡。
4. **`scripts/spec-tools/api-reality-dashboard.py` 的 24 条 invalid-syntax（`:120` 真语法错）**：与 `target-version` 无关，py39/310/311 各 24、py312 21。⛔ **本条初版写「它在子目录里 ⇒ 不被 hook 拦」是错的**（Codex round-1 MEDIUM 指出，本卡实测确认）：lefthook 的 `{backend,src,scripts}/*.py` **跨目录匹配**，该文件**在** `python-lint` 覆盖面内，暂存它的提交会被拦。但这与本卡无关——`invalid-syntax` 属解析器层，`select = []` 时就已可见。实测见 §四-A.8 与 `lefthook-glob-empirical-v2-20260917T130857.txt`。修复另立卡。
5. **root `ruff.toml` 新 select 的真实生效面 = 288 个非 backend tracked `.py`**（按顶层目录：`_bmad-output` 129 / `scripts` 94 / `tests` 41 / `_bmad-archive` 10 / `canvas-vault` 8 / `.gdr` 3 / `docs` 2 / `tools` 1）。其中落在 `python-lint` glob 内的是 `scripts/` 下**全部** 94 个 tracked `.py`（顶层 52 + 子目录 42；glob 跨目录，见 §四-A.8）加上 `backend/` 面（受 `backend/ruff.toml` 管，非本卡面）；`src/*.py` tracked = **0**，glob 该段覆盖空集。
6. **设计稿判据「brew version == npx version」install-free 不可达**，卡文 §〇 已更正；本卡按更正后的口径执行（版本判据改为「npm 侧三处自洽 + brew 落档为 runner-of-record」）。
7. **lefthook 裸调用口径（R-B14-1）在改后树上的实测确认值**：`/opt/homebrew/bin/lefthook version` → `2.1.6`、rc=0（`version-grep-after-20260917T124753.txt`）；本卡提交时 hook 横幅 `🥊 lefthook v2.1.6`。手册 §四.1 第 8 条已按 R-B14-1 更正 ⇒ **本卡无手册待更正移交项**。
8. **`tests/unit` 目录级结果**：改后 64 条红与 `08100483` 基线**逐条相同**（0 新增 0 消失），存档 `unit-close-20260917T124820.txt` / `unit-diff-20260917T125806.txt`。
9. **`ruff.toml:2` 的文案半失实（本卡未改，卡文允许面不含该行）**：`# NOTE: Lint rules temporarily disabled due to 2000+ pre-existing violations.` 在本卡启用四条必错级后不再完全成立。修文案需扩 `ruff.toml` 的允许面，请主 session 定夺（可并入「风格规则另开卡」）。
10. **本卡判据自身出过两次问题并已更正**（§四-A.5）：`git ls-files` 中文路径 quoting 致 129 条 `E902` 假命中；`--config` 指向树外文件致 `target-version` 推断丢失、两侧不可比。两份缺陷存档一并入库供核。
11. **`lefthook run` 下 `--no-auto-install` 仍存在（子命令 flag），与 R-B14-1 不矛盾**：R-B14-1 实测的是**全局位置** `lefthook --no-auto-install version` ⇒ `Incorrect Usage` + rc=1，裁定「批内 lefthook 验证一律裸调用」成立且本卡照办；但 `lefthook run --no-auto-install ...` 在 2.1.6 可用，本卡用它来保护**跨三树共享**的 `.git/hooks` 不被隐式重装（§四-A.8）。登记供后续卡参考，**不改裁定**。
12. **⚠️ `{staged_files}` 为空且作业未被跳过时 `ruff check` 扫全树**：`lefthook.yml:124` 的 `ruff check {staged_files}` 在文件列表为空时展开成不带参数的 `ruff check` = 从 cwd 递归扫描（实测扫到 `_bmad-output/审查/evidence-ast-flag/rounds2.py`）。正常提交路径有「`(skip) no files for inspection`」兜底（§四-A.8 C′/D′ 实测 rc=0），触不到；`--force` / `--all-files` 或将来任何使该跳过失效的改动会触发。**本卡不是成因，但新 `select` 放大了它的影响半径**（全树扫描现在会额外报 `_bmad-output` 下的 F821）。`lefthook.yml` 是 T8-A 唯一写者、不在本卡地盘 ⇒ 登记不改。
13. **Codex round-1 的 MEDIUM 成立，本卡文档已更正**：我把 `git ls-files 'scripts/*.py'` 的 94 误记为「顶层」（git pathspec 不带 `:(glob)` 时 `*` 跨 `/`，真顶层 52 / 子目录 42），并据此错误断言 lefthook 单星 glob 不含子目录。两处更正见 §四-A.8；已入库的 `rootsurface-before-after-v2-20260917T125857.txt:30-31` 保留原始错误行不改，更正以 §四-A.8 为准。
14. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数**：见 §七。

---

## 七 Codex 独立审查（`gpt-6-astra` · `ultra` · 多轮，依 D-15）

### round-1 — 绑定 `99e15a4e`，**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 1**

- prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-TOOLCHAIN-UNIFY.md`（6856 字符；禁用措辞四项各 0；无旧模型名）
- 存档：`_bmad-output/审查/codex-review-CARD-TOOLCHAIN-UNIFY.md`（7514 B → 补首部后更大；协议 §2.1 六行首部齐：模型 / reasoning_effort / codex 三字段 + 会话头自证抄 `.stderr` 的 `:2` / `:5` / `:9` 三行）
- codex：`codex-cli 0.153.3`；`.stderr` 不入库

| 级别 | 条数 | 内容 | 处置 |
|---|---|---|---|
| BLOCKER | **0** | — | — |
| HIGH | **0** | — | — |
| MEDIUM | 1 | 「单星不含子目录」的覆盖结论错误，且把递归 94 误记为顶层 94（`lefthook.yml:118`、`rootsurface-before-after-v2-*.txt:31`） | **确认成立**。本卡未采信其文档引用，独立实测复核（§四-A.8）：计数 52/42/94 属实；`lefthook run --job python-lint --file <子目录 .py>` 实测**作业被选中**。文档已更正（§四-A.3 / §六 ④⑤ / §五 4），**代码零改动** ⇒ 绑定不破 |
| LOW | 1 | `ruff.toml:2` 「Lint rules temporarily disabled」与实际不符，属文案债；Codex 同时认定「考虑本卡只允许改 `select` 及其上方注释，登记后续更正合适，不应因此擅自扩地盘，也不构成本卡阻断」 | **登记不改**（§六 ⑨）。与本卡 §四-A.7 的自述判断一致 |

**Codex 对六个提问的裁定（摘）**

- **⓪**：不能确认「install-free 下不存在统一路径」——把 npm 声明与完整 lock 解析元数据对齐到 brew 已有版本**可以是纯文件变更**，不必然要求当场安装；但 npm runner 本机不存在，禁装意味着无法完成「两套实际 runner 同版」的**实测验收**。⇒ 本卡登记为 §六 ②，措辞按此更正：不再声称「技术上无路可走」，而是「本批不做 + 无法实测验收」。
- **①**：分叉**真实存在且早于本卡**——`npm ci` 的 `prepare` 用前置于 PATH 的本地 1.13.6 执行 `lefthook install`，而本机普通 git 环境优先跑 brew 2.1.6；**生成 hook 的版本 ≠ 随后执行 hook 的版本**。`runner-of-record` 判定成立，但不能证明跨环境行为一致。⇒ 与本卡 §五 1/2 的声明一致。
- **②**：288 计数成立、两条 F821 在报告内穷尽、tracked 配置中无另一份子目录 ruff 配置；但应称「本次 tracked `.py` 普查集合」而非「所有运行入口的完整治理面」；另指出第二处更正的**精确原因**是「显式传入配置文件会停止缺省 `target-version` 推断」，不只是临时目录位置不对。⇒ 采纳，措辞已按此收窄（§五 6）。
- **③**：登记 `technology` 存量 F821、本卡不修，**恰当**；「禁止修改 `.py` 的范围应保持」。
- **④**：三个非 `.py` 文件不会启动 `python-lint`，静态推断**成立**；2.1.6 在构造命令阶段直接跳过，不会把空参数交给 `ruff check`。⇒ 本卡随后**实测确认**（§四-A.8 C′/D′：`(skip) no files for inspection`、rc=0）。
- **⑤**：本次编辑**不会**造成 manifest/lock 失配；除 root 声明这一处预期编辑外整个 lock 内容相同，已解析版本正好满足 exact `1.13.6`；但这不等于未执行的完整 `npm ci` 已通过。

**Codex 自述边界**：全程未修改文件、未安装、未运行 hook、未连库；`tests/unit` 的「64 条红逐条相同」只核对了 evidence，未独立复跑；root 治理面未重新读取 288 个源码文件复跑 ruff。

### D-15 达成判定

本卡**一轮**达成：round-1 即 **BLOCKER 0 / HIGH 0**，且**绑最终 HEAD**——审后本卡仅改 `_bmad-output`（验收单更正、Codex 存档首部、两份新 evidence），**零代码改动**，`git diff --stat 99e15a4e HEAD -- . ':(exclude)_bmad-output'` 为空（见 §四-A.9）。MEDIUM/LOW 按协议 §1 登记不阻断，其中 MEDIUM 已在文档层更正。

### 四-A.9 收官绑定核

存档 `evidence-toolchain-unify/final-binding-20260917T131027.txt`（rc=0）。本卡共 **2 条 commit**：

| commit | 面 | header `wc -m` |
|---|---|---|
| `99e15a4e` | **代码**（`ruff.toml` / `package.json` / `package-lock.json`）+ 首批 evidence | 91 |
| `6775302d` | **仅 `_bmad-output`**（验收单 / Codex r1 存档 / prompt / 三份 evidence） | 89 |

| 判据 | 实测 |
|---|---|
| D-15 终审绑定 `git diff --stat 99e15a4e HEAD -- . ':(exclude)_bmad-output'` | **0 行** ✅ |
| 同判据的验伪锚（去掉 exclude） | **6** 个文件（证判据非恒空） |
| 全卡地盘门 `$PREV..HEAD` 排除 `_bmad-output` | 恰 **3** 个：`package-lock.json` / `package.json` / `ruff.toml` ✅ |
| index 内 `*.stderr*` 文件数 / 本卡引入数 | **0 / 0** ✅ |
| 两条 commit header ≤100（`wc -m`） | 91 / 89 ✅ |
| 卡号 `CARD-TOOLCHAIN-UNIFY` / 批次标记出现的 commit 数 | **2 / 2** ✅ |
| 工作树 | 干净（T8-F 开工前提满足） |
| 是否 push | **否**（依卡文） |
