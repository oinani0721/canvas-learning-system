# UAT — CARD-HYGIENE-conftest

> 批次: `BATCH-2026-09-07-第十三批` · 车道 `card-u10-red-a`（分支 `card/u10-red-a`）· CODE_BASE `da690bf8`
> 卡文: `…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-A.md`
> 地盘: **只** `backend/tests/unit/conftest.py`（本卡零生产代码改动）
> evidence: `_bmad-output/审查/evidence-hyg-conftest/`（全部 `.txt`，末行 `rc=`）
> 日期: 2026-09-08

---

## 〇 一句话

`tests/unit` 的卫生门原先把**全机共享** `/tmp` 里新出现的 `test-vault*` 目录无条件判成本车道回归；
本卡按「能不能归属到本 worktree」把信号分成两类 —— 可归属的继续硬 fail（并**新增**一道树内源码
字面量硬门），不可归属的降为「环境受干扰」告警。既有骨架 / tracked sha 两个硬 fail 面一字未动。

---

## 一 完成条件逐条对照

> ⚠️ **本节 (c)(d)(f)(g)(h)(i) 记录的是 round-1（`13a138c9`）那一轮的存档与数字。**
> ⚠️⚠️ **(d) 一节转述的告警文案是 round-1 旧版，其中「不是本次运行新增的回归」这句
> 已在 round-1 整改中撤回**（Codex round-1 HIGH #2）；当前实际文案见 §三·五 / §三·七。
> 保留旧文只为对照，**不得据以引用**。
> Codex round-1 给出 2 条 HIGH + 1 条 MEDIUM，代码已整改 ⇒ **全部裁判已重跑**，
> r2 的存档与结果见 **§三·五**，末轮以那一组为准。此处保留 round-1 数字是为了让
> 「整改前后」可对照，不是遗漏更新。(e) 一节已直接按整改后的实现改写。

### (a) 第 0 分钟 + §〇 逐条实测 + 开工 `/tmp` 清单

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-u10-red-a` ✅ |
| `git branch --show-current` | `card/u10-red-a` ✅ |
| `git rev-parse HEAD` | `da690bf8817adc4a84b20d59a1b8d8db4a578969` ✅ |
| `git status --porcelain` | 空 ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 都在 ✅（venv 是目录级 symlink → `card-v5-lance/backend/.venv`） |

**§〇 每条 file:line 实测与规划稿一致，无一处需要写「规划稿 :X → 实测 :Y」**：
`:46` `_HYGIENE_SKELETON_PATHS` / `:49` `_HYGIENE_TRACKED_FILES` / `:51` `_HYGIENE_TMP_GLOB` /
`:54-61` `_hygiene_backend_root()` / `:64-86` `_hygiene_snapshot()`（`:77` sha、`:82` tmp glob、`:83-84` except）/
`:89-134` fixture（`:114-116` 差集判据、`:117-124` 归属提示、`:126-134` `pytest.fail`）/
`:137` `_stub_vault_identity_registry`；文件 **218** 行。

**§〇 第 4 行的 grep 事实复验**（⚠️ 结论收窄，Codex round-3 HIGH #2）：
**在这两条搜索的命中里未发现写者** —— 这**不等于**「本树已无 `/tmp` 根写者」。
文本搜索与 (e) 的 AST 门有同一组盲区（路径运算 / 运行期拼接 / bytes / `tempfile` 分参数 /
相对路径 / 外部来源），它们看不见的写者，这两条 grep 同样看不见。
- `grep -rn '/tmp/test-vault' backend/tests --include='*.py'` = **4** 行，**无一是写者**
  （`conftest.py:118` 门自己的提示文案 + `test_startup_health_check.py:56/:58/:66` 三条 `#` 注释）;
- `grep -rn 'test-vault' …` = **14** 行，其余 10 行不含 `/tmp/` 前缀（`tmp_path / "test-vault…"` 六处、
  非路径串三处、`conftest.py:51` glob 常量一处）。

**开工 `/tmp/test-vault*` 清单**：`evidence-hyg-conftest/tmp-listing-open-20260908T064505.txt` —— **12 个既有目录**
（`test-vault` / `test-vault-wizard` 及 `.h1/.h2after/.h2d/.n1/.n2/.pre` 后缀族，mtime 09-05~09-08）。
**只看不动、不改名、不删**。U11-A 于 06:58 独立实测同样是 12 个，第二源交叉一致。

> ⚠️ 存档里同时记了一条 `find /tmp -maxdepth 1 -name 'test-vault*'` **返回空**。这不是与 `ls` 矛盾：
> macOS `/tmp → /private/tmp` 是 symlink，而 `find` 默认 `-P` 不跟随任何 symlink（含命令行参数），
> 于是 `maxdepth 1` 只看到链接本身。shell glob 与 `Path("/tmp").glob()` 都走 `opendir("/tmp")`，
> 由内核解析 symlink ⇒ 门看到的确实是这 12 个。**这条同时是「本卡未证明什么」⑤ 的实测素材。**

### (b) 开工基线（改任何文件之前，四个门下目录级）

| 目录级 | 汇总行 | rc | nodeid 判据 |
|---|---|---|---|
| `tests/unit` | `173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors in 253.34s` | 1 | **与 202 基线 diff 为空** ✅（`red-diff-open.txt` 零行） |
| `tests/api` | `268 passed, 40 warnings in 1.61s` | 0 | 零红 nodeid |
| `tests/regression` | `1464 passed, 6 skipped, 10 xfailed, 556 warnings in 339.92s` | 0 | 零红 nodeid |
| `tests/skills` | `369 passed, 22 warnings in 39.57s` | 0 | 零红 nodeid |

- 基线文件（绝对路径，不在本车道树）：
  `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/unit-red-baseline-da690bf8.txt`，`grep -cE '^(FAILED|ERROR) tests/'` = **202**。
- 开工 unit 的汇总行与基线抬头记录的 `173 failed / 4749 passed / 48 skipped / 29 errors` **逐字一致**。
- 三个「零影响」目录级的**预期依据**（写进存档抬头，**不替代实跑**）= `conftest.py:34-41` 覆盖面注释
  + 本卡 (d)(e) 两处改动都在该 fixture 内。收工实跑结果见 (i)。
- ⛔ 全程未用 `wc -l` 当分母。

### (c) 修前负控 N1 —— 实证「此刻 `/tmp` 信号是硬 fail」

存档 `negctl-n1-before-20260908T065914.txt` / 窗口 `window-n1-before-20260908T065914.txt`

```
8 passed, 10 warnings, 1 error in 12.43s      rc=1
ERROR at teardown of TestCheckRequiredPlugins.test_no_obsidian_dir
  新出现 /tmp/test-vault* 目录: /tmp/test-vault-negctl-43048
mkdir_done=2026-09-08T06:59:27  dir=/tmp/test-vault-negctl-43048
```

- **前提断言满足**：存档里**看得见**那条 ERROR（不是「理论上会红」）。
- 判据：`ERROR tests/` = 1、`新出现 /tmp/test-vault* 目录` = 1、负控目录名在正文出现 3 次、`rc=1`。
- 跑完 `rmdir /tmp/test-vault-negctl-43048`（`rmdir` 非递归，只删自己建的空目录）。

> **⚠️ 与卡文 §二.3 的执行偏离（等价性已论证，登记）**：卡文写 `( sleep 2; mkdir … ) &`。
> 实测该写法**必然失效**：单文件跑总耗时 ~11.5s，其中 pytest 内部只有 **0.45s** —— 约 11s 全在
> Python 启动 + conftest import + collection，于是 session fixture 首尾两次 `/tmp` 快照之间只有
> **~0.5s** 的洞。`sleep 2` 的 mkdir 落在 before 快照**之前**，目录进 before 集合，差集为空 ⇒
> **静默不红**（负控假 SURVIVED，且成败随机取决于机器负载 = 不可复现）。
> 处置：外部 mkdir 仍由**独立后台进程**建（保持「非本 pytest 进程所建」的形态不变），另加一个
> 只做 `time.sleep` 的外部插件 `-p widen_window` 把窗口从 0.45s 拉到 12s，外部 mkdir 排在 t0+13s。
> 该插件**不 import 被测模块、不碰 conftest / fixture / 门逻辑、不建不删任何文件**，唯一可观测
> 副作用是「慢了 12 秒」；源码见 `evidence-hyg-conftest/widen_window.py.txt`。
> **等价性**：负控要证的输入形态（`/tmp` 根在 session 窗口内出现新的 `test-vault*` 目录、非本进程所建）
> 逐字未变，只是把「靠运气命中 0.5s」换成「时序可断言」⇒ 对该症状等价且**更强**。
> ⚠️ (n) 的 N2/N2' 用**真目录级**（窗口 235~253s），**不需要也没有用**这个插件 —— 承重判据那一侧是纯净的。

### (d) `/tmp` 信号降「环境受干扰」告警

- `:114-124` 的差集逻辑**保留**，出口从 `violations.append(...)` 改为
  `warnings.warn(pytest.PytestWarning(...), stacklevel=1)`。
- `_HYGIENE_TMP_GLOB` 与 `_hygiene_snapshot()` 的 `tmp` 字段**保留不删**（观测照做，只换出口）。
- 渲染文案**逐字保留**原归属提示三行（`stat -f '%Sm'` / `ps -ww -p` / `lsof -a -p -d cwd`），
  并追加三行。⛔ **以下为 round-1 旧文案，最后一句已撤回，勿引用**：
  「`/tmp` 全机共享归属不可判 ⇒ 本 session 不判红；本树自身写者由源码字面量门守（硬 fail）；
  这条告警 = 环境受干扰需要重跑、~~不是本次运行新增的回归~~」。
  当前文案改为「**归属未知**：可能来自本 session，也可能来自任何别的进程 ⇒ 不判红，
  但**请核查或重跑**」，并明说源码门只看字符串常量、**不能**证明本树没有写者。
- 固定判据串 **`环境受干扰`** 在文案第一行。
- **整段字面量已拆**：`_TMP_LITERAL = "/tmp/" + "test-vault"`（`+` 号形态，实测保持 `BinOp` 两个 `Constant`）。
  ⛔ 未用相邻字面量 —— 实测 `ast.parse('"/tmp/" "test-vault"')` 在词法期折叠成**单个** `Constant`，
  拆了等于没拆（前提自证存档 `selfprobe-const-premise-20260908T071236.txt`）。

**告警不会被升级成错误（独立核对）**：`backend/pytest.ini` 无 `filterwarnings`、无 `-W error`、
无 `--disable-warnings`，`addopts` 只有 `-v --tb=short`。另跑最小实验实证 session fixture teardown
里的 `warnings.warn` **确实**被 pytest 捕获、进 warnings summary、归到最后一个 item、`rc=0`、
多行消息完整渲染（不是推理 `_pytest/warnings.py` 的 hookwrapper 覆盖范围）。

### (e) 新增源码字面量硬门（可归属，硬 fail）—— **以 Codex round-1 整改后的实现为准**

`_hygiene_scan_tmp_literals()`（fixture **setup 段**调用，`yield` 之前）：

- 扫描根 `Path(__file__).resolve().parent`（= `backend/tests/unit/`）；
- 遍历用 **`os.walk(scan_root, onerror=_on_walk_error)`**（`followlinks=False` 默认），
  目录枚举失败进 `unchecked` —— ⚠️ round-1 用的是 `Path.rglob`，那是**假绿**，见 §四；
- **排除自身**：`py.resolve() == Path(__file__).resolve()` 则 `continue`；
- **符号链接越界拦截**：走 `_hygiene_within_root(resolved, scan_root)` 三态判定 ——
  `False` ⇒ 进 `unchecked`（报「链接目标在扫描根之外」），`None`（无法判定）⇒ 也进 `unchecked`，
  既不当普通树内源码读，也不静默跳过（Codex round-1 MEDIUM + **round-2 MEDIUM** 整改）；
  ⚠️ round-2 前用的是**字面** `is_relative_to`，在本机大小写不敏感文件系统上会把
  `tests/UNIT/conftest.py` 这种合法别名判成越界（假红）；现在先试字面包含，不成立再逐级向上用
  `samefile` 做**文件系统身份**比对，比对本身失败一律返回 `None`；
- 只看 `ast.Constant` 且 `isinstance(node.value, str)` 且 `_TMP_LITERAL in node.value` → 记 `file:lineno`；
- 读不了 / 解析不了 / 枚举不了 / 越界的一律进 `unchecked`（**不算通过**），与 hits 同一出口
  并入 teardown 的 `violations` ⇒ 末尾一条 ERROR、`rc!=0`；
- fixture 仍**不创建 / 不删除 / 不写入任何文件**、不 `os.chdir`、不 `import app.*`（既有那处
  `import app.services.vault_identity_registry` 属 `_stub_vault_identity_registry`，本卡未动）、不依赖 cwd。

**为什么必须 AST 而不是 grep 全文**：`test_startup_health_check.py:56-66` 那三条 `#` 注释记录 Y6-A
改前的旧硬编码值，grep 形态会把它们判成回归；且 conftest 自己的告警文案含同一段路径 ⇒ grep 形态必然自指。

**这道门证明的是「源码里没有这种硬编码常量」，不是「本树没有 `/tmp` 写者」。**
盲区清单（Codex round-1 HIGH #2 逐条实测，已写进函数 docstring）：路径运算分段、运行期拼接、
**前缀被拆开的** f-string（⚠️ 前缀完整的 f-string 反而**会**命中）、`"/tmp//…"` / `"/tmp/./…"`
等价写法、`bytes` 字面量、`tempfile.mkdtemp(prefix=…, dir=…)` 分参数、cwd 恰为 `/tmp` 时的相对路径、
值来自环境或扫描面外模块；以及本文件**整体**被排除 ⇒ 本文件其他 fixture 里将来出现的完整硬编码路径同样漏检。

扫描成本实测：**252 个文件 / 0.535 秒 / 零解析失败**（round-1 测得，整改未改变量级）。

### (f) 修后负控 N1'

存档 `negctl-n1-after-20260908T070910.txt` / 窗口 `window-n1-after-20260908T070910.txt`

```
8 passed, 11 warnings in 13.00s               rc=0
conftest.py:212: PytestWarning: [hygiene] 环境受干扰: 新出现 /tmp/test-vault* 目录: /tmp/test-vault-negctl-72013
mkdir_done=2026-09-08T07:09:23  dir=/tmp/test-vault-negctl-72013
```

判据：`ERROR tests/` = **0** ✅ · `grep -c '环境受干扰'` = **2**（≥1）✅ · 负控目录名在正文 3 次 ✅ · `rc=0` ✅
（对照 (c)：同一输入形态，`1 error / rc=1` → `0 error / rc=0` 且告警可见 —— 不是静默吞掉。）

### (g) 正控 P1 —— 源码门承重

存档 `negctl-p1-red-20260908T070947.txt` / `negctl-p1-green-20260908T071028.txt`

- 探针：在 `test_vault_init_service.py` 末尾临时追加 `_HYGIENE_PROBE = "/tmp/test-vault-probe"`（不入 commit）。
- 红：`8 passed, 1 error`、`rc=1`，门文案**指名**
  `…/backend/tests/unit/test_vault_init_service.py:140`（原 137 行 + 2 空行 + 探针行，行号对得上）。
- 还原：`git show HEAD:backend/tests/unit/test_vault_init_service.py > …`（⛔ 未用 `git checkout` / `git restore` / `git stash`）。
- 对账：`sha_before` = `sha_after` = `c6214bde945d1e9ecb7cd4be14964e2a2e81ae75f8a9557804cba14ed2478031` ✅ ·
  `git diff --quiet` rc=**0** ✅。
- 绿：还原后复跑 `8 passed`、`ERROR tests/` = 0、`rc=0` ✅。

### (h) 正控 P2 —— 既有骨架硬 fail 面不回退

存档 `negctl-p2-red-20260908T071051.txt`

- 探针：临时追加一个用例执行 `Path(__file__).resolve().parents[2].joinpath("raw/_probe").mkdir(parents=True)`。
- 红：`9 passed, 1 error`、`rc=1`，门文案**指名** `backend/raw`（出现 2 次）✅ —— 骨架面**没有**被本卡放宽。
- 清理：`rmdir backend/raw/_probe` + `rmdir backend/raw`（只删自己建的，非递归）✅
- 还原对账：sha 前后同（`c6214bde…`）、`git diff --quiet` rc=0、`git status --porcelain backend` 只剩本卡的 conftest ✅

### (i) 收工目录级（四个门下目录，与开工逐个 diff）

| 目录级 | 汇总行 | rc | diff |
|---|---|---|---|
| `tests/unit` | `173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors in 242.69s` | 1 | **对 202 基线 diff 为空** ✅（`red-diff-after.txt` 零行，无 `>` 也无 `<`） |
| `tests/api` | `268 passed, 40 warnings in 1.68s` | 0 | 与开工**红** nodeid 集 diff **为空** ✅ |
| `tests/regression` | `1464 passed, 6 skipped, 10 xfailed, 556 warnings in 350.53s` | 0 | 与开工**红** nodeid 集 diff **为空** ✅ |
| `tests/skills` | `369 passed, 22 warnings in 43.03s` | 0 | 与开工**红** nodeid 集 diff **为空** ✅ |

- 每份存档末都有 `rc=` 行与 pytest 汇总行 ✅
- ⛔ 全程未用 `wc -l` 当分母；`tests/integration` / `tests/e2e` 按手册 §一.1.5 **未跑**。
- `tests/unit` 那一跑即 N2'（(n)④ 允许兼用，此处写明是同一次）—— 它是**带 treeB 干扰**的一轮，
  仍与 202 基线 diff 为空，比一次无干扰的收工跑更强。
- 三个非 unit 目录级的 `grep -c '环境受干扰'` 均为 **0** —— 实证该 fixture 确实只在 `tests/unit`
  被收集时加载（`conftest.py:34-41` 覆盖面注释的预期成立），但这只是本次两轮的观测，
  不构成结构性证明（见「本卡未证明什么」⑧）。

### (j) 地盘门 + ruff

| 判据 | 结果 |
|---|---|
| `git diff --name-only --no-color da690bf8 HEAD -- . ':(exclude)_bmad-output'` | 只有 `backend/tests/unit/conftest.py` ✅ |
| `git diff --stat --no-color da690bf8 HEAD -- backend/tests/conftest.py backend/tests/support backend/app` | 空 + rc=0 ✅ |
| `:(exclude)` 写法验伪锚 | 排除 `backend` 后输出为空且 rc=0 ⇒ 排除真的生效，不是 zsh 下 `':!…'` 的 rc=128 假绿 ✅ |
| `ruff check backend/tests/unit/conftest.py` | `All checks passed!` rc=0 ✅ |
| `ruff format --check backend/tests/unit/conftest.py` | rc=0 ✅ |

> **ruff format 的存量基线先查过**（U1-A §二.5 口径）：`git show HEAD:…conftest.py` 喂给
> `ruff format --check --stdin-filename` 得 **rc=0**，即 HEAD 版**无存量漂移** ⇒ 本卡引入的漂移
> 必须自己修干净，不适用「只 `--range` 改动行」的例外。实际 `ruff format` 只改了本卡新增的两处
> （一个 `if` 条件的换行、warning 文案的 `+` 折行），`--diff` 已确认不触及存量。
> ⚠️ 期间发现并纠正过一次**判据自身的假绿**：`ruff format --check … | tail -3` 之后取 `$?` 拿到的是
> `tail` 的 rc（恒 0）。改为直接取 rc，并加验伪锚（故意喂坏格式 → rc=1）确认该判据真的会红。

---

## 二 §二.7 自指验伪锚（四小条）

| 小条 | 判据 | 修前 | 修后 |
|---|---|---|---|
| **7a** | `grep -c '/tmp/test-vault' backend/tests/unit/conftest.py` | **1**（唯一命中 `:118` 整段文案） | **0** ✅ |
| **7b** | 门承重（不靠 grep） | — | 由 (g) P1 证明：探针在 → 红且指名行号；还原 → 绿 ✅ |
| **7c①** | conftest 末尾加**注释** `# selfprobe: /tmp/test-vault` → 单文件跑 | — | **仍绿** rc=0 / 0 ERROR ✅（门只看 `ast.Constant`，不看注释 ⇒ `test_startup_health_check.py:56-66` 三条注释不会被误报） |
| **7c②** | conftest 末尾加**相邻字面量常量** `_SELFPROBE = "/tmp/" "test-vault"` → 单文件跑 | — | **仍绿** rc=0 / 0 ERROR ✅（⇒ `Path(__file__).resolve()` 排除自身生效） |
| **7d** | `python3 -c "import ast;ast.parse(open('…conftest.py').read())"` | — | rc=0 ✅ |

- **7a 是会翻转的判据，不是恒 0 的死判据**：修前实测 = 1，靠 (d) 拆字面量才变 0。
  ⛔ 卡文点名禁用的旧写法 `grep -c '"/tmp/test-vault'`（带前引号）在 `da690bf8` 上就已经是 **0**
  （双引号并不紧邻 `/tmp`，对 `:118` 那条真实存在的整段字面量失明）—— 实测确认它是恒 0 死判据。
- **7c② 的前提已自证**（否则它是死探针 —— 「仍绿」可能只是因为门根本看不见那个形态）：
  存档 `selfprobe-const-premise-20260908T071236.txt` 实测
  ① `ast.parse('"/tmp/" "test-vault"')` → **单个 `Constant '/tmp/test-vault'`**（确被折叠）；
  ② 用门的判据扫它 → **hits=[1]**（若不排除自身，门确实会命中）；
  ③ 对照 `+` 号形态 → `BinOp`、hits=[]（不折叠，符合 conftest 的写法）。
  ⇒ 三条同时成立，7c② 的「仍绿」唯一解释就是排除自身生效。
- 两条自指探针的还原：⚠️ 靶子是 conftest **本身**，而本卡对它的改动**尚未 commit** ⇒ 照抄卡文的
  `git show HEAD:… > …` 会把本卡工作成果整个静默覆盖（与「`git checkout HEAD` 清掉暂存区」同族）。
  改用**探针前的工作区快照**还原，并同样做逐字节对账：两条的 `sha_before` = `sha_after` =
  `5e9765c7d3c582f048951c4507f0659a041f33ef09f799b845ec0f99259645ab`，`cmp -s` rc=0 ✅。
  两条探针**全部还原之后**才复跑 7a（= 0），符合卡文对顺序的要求。

---

## 三 (n) 双树并发正负控（手册 §四.5 D-27 裁 (乙) 保留的承重判据）

**批级通告（协议 §2.3）已做，且不止写在手册里**：
- 手册 `§零.14` 追加了完整通告行（时刻 / 目录名前缀 / 影响面 / 清理方式 / 临时 worktree 名）；
- 另用 SendMessage **逐条直达当时在线的全部 10 条并行车道 session**（U1~U9、U11），说明窗口内跑
  `tests/unit` 目录级可能多出的那条 ERROR 是环境噪音、不是各自卡的回归。
  已收到 U5 / U7 / U8 / U9 / U11 五条回执，各自登记了处置口径。

**树 B**：`git worktree add --detach ../u10a-treeB-negctl da690bf8` + 目录级 venv symlink + `.env` 拷贝
+ **只在树 B** 放临时探针 `backend/tests/unit/test_zzz_treeb_probe.py`（建**空目录** `/tmp/test-vault-treeB-<pid>`，
`rmdir` 可清）。⛔ 未用 `15653787^` 的真骨架写者：它更忠实，但会在 `/tmp` 留下一份真 vault 骨架，
而本卡禁递归删除 ⇒ 清不干净。此取舍如实登记。

### N2（修前，树 A 一个文件都还没改）

| 前提断言（缺一即负控没生效） | 实测 |
|---|---|
| ① 树 B 那一跑**真的建出了**该目录 | `treeB-probe-n2-20260908T070034.txt`：`1 passed, 1 error`（树 B 被它自己的旧门判红，预期）+ 跑完立刻 `ls -ld` 显示 `drwxr-xr-x … Sep 8 07:01 /tmp/test-vault-treeB-49484` ✅ |
| ② 树 A 的 ERROR 正文出现**同一个**目录名 | `grep -c "$DIRNAME"` = **1**，正文：`新出现 /tmp/test-vault* 目录: /tmp/test-vault-treeB-49484` ✅ |
| ③ 两侧 `date` 显示窗口交叠 | 树 A `[07:00:34, 07:04:41]`，树 B launch `07:01:34` / mkdir 完成 `07:01:45` ⇒ **落在窗口内** ✅ |

结果：`173 failed, 4749 passed, 48 skipped, 121 warnings, 30 errors in 235.29s`、`rc=1`、
`ERROR tests/` = **30**（= 基线 29 + 1 条 session teardown）。

**与 202 基线 diff 恰好多一条 `>` 行**：
`> ERROR tests/unit/test_wikilink_parser.py::TestExtractAllWikilinks::test_empty_text`
—— 按协议 §5，`>` 行就是**阻断级**信号，而它其实是**别的树**建的目录造成的。症状真实复现。

> ⚠️ 按卡文，N2 这一轮的**红** nodeid 集**不进**「diff 为空」判据（开工基线用 (b) 那次干净的跑）。

### N2'（(e) 落地之后）

| 前提断言 | 实测 |
|---|---|
| ① 树 B 真的建出了该目录 | `treeB-probe-n2p-20260908T071312.txt`：`1 passed, 1 error` + `ls -ld` 显示 `/tmp/test-vault-treeB-88464` ✅ |
| ② 树 A 正文出现同一个目录名 | `grep -c "$DIRNAME"` = **1** ✅ |
| ③ 两侧 `date` 窗口交叠 | 树 A `[07:13:12, 07:17:29]`，树 B launch `07:14:12` / mkdir 完成 `07:14:25` ⇒ 落在窗口内 ✅ |

结果：`173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors in 242.69s`、
`ERROR tests/` = **29**、`环境受干扰` = **2**、**与 202 基线 diff 为空** ✅
（本轮同时充当 (i) 的收工 `tests/unit` 那一跑 —— 与卡文 (n)④ 允许的一致，此处写明是同一次。）

告警正文（`conftest.py:212` PytestWarning）：
`[hygiene] 环境受干扰: 新出现 /tmp/test-vault* 目录: /tmp/test-vault-treeB-88464` + 原归属提示三行 + 新增三行。

#### ⚠️ 判据修正：卡文 §二.9 期望的 N2' `rc=0` **不可达**，已换成能翻转的量（登记）

`tests/unit` 目录级带着 **202 条既有红**，`rc` 恒为 1 —— **干净的开工基线（无任何 treeB 干扰）
本身就是 `rc=1`**。卡文把**单文件**负控的期望值（N1' 8 用例全绿 ⇒ rc=0）套到了**目录级**上；
盲从它会把成功的一轮误判成失败。替代判据取三端点对照：

| 轮次 | 门 `pytest.fail` 触发 | `ERROR tests/` | `环境受干扰` | rc | vs 202 基线 diff |
|---|---|---|---|---|---|
| **开工基线**（无 treeB，纯净） | 0 | 29 | 0 | 1 | 空 |
| **N2 修前**（+treeB） | **1** | **30** | 0 | 1 | **多一条 `>`** |
| **N2' 修后**（+treeB） | 0 | 29 | **2** | 1 | 空 |

三个端点缺一不可：
- 没有第一行，「rc=1」既能读成「没修好」也能读成「既有红」，两种解释分不开；
- 没有第三行的「环境受干扰 = 2 + 目录名出现 1 次」，N2' 的绿可能只是「树 B 那一轮没生效」；
- 能翻转的量是 `ERROR tests/` 30→29、nodeid diff「多一条 `>`」→ 空、门 fail 1→0、告警 0→2。

原始 rc 值一律如实落盘（三份存档末行都有 `rc=1`），不改判据以外的任何数字。

### 一条来自并发车道的独立观察（对门语义的重要澄清）

U5-A 报告它在 07:02–07:06 跑了一次 `tests/unit` 目录级，**未中招**（202 基线 diff 为空、无 teardown ERROR）。
这与本卡结论**不矛盾**，恰恰印证门的语义：树 B 的目录建于 **07:01:45**，落在 U5 那次 session 的
before 快照**之前** ⇒ 进了它的基线集合 ⇒ 差集为空。
**假红只在目录于 session 窗口"内"新建时发生**，这也正是 (c) 那条执行偏离要解决的问题（`sleep 2` 太早 = 同一个道理）。

**由此得到的一条判据方法论（U8-B 车道回执带来的第二源印证）**：把窗口通告发给并行车道后，
U8 与 U11 各自定了「若出现 `ERROR tests/unit/<末个用例>` 且正文含 `/tmp/test-vault` 就当噪音」的
**症状判据**。它只能证明「这次没红」，证明不了「这次不可能红」—— 若某车道恰好起跑于目录建出之后，
症状判据同样不成立（目录进了它的 before 快照），此时把「没红」读成「窗口没影响我」就是错误归因。
补上**机制判据**（比对本方 session 起止时刻与本卡 4 个目录的建出时刻是否交叠）才是完备的：
U8-B 据此把结论从「没观察到症状」升级为「窗口 06:59:14–07:18:58 与本方跑 **06:52:30–06:56:28**
（238.04s）无交集 ⇒ 结构上不可能中招」。这个区别本身就是这道门要修的语义 ——
**它以前逼着每个人做归因，现在它自己说清楚**。

> ⛔ **更正（Codex round-2 HIGH #3 抓到）**：本单初版把结束时刻写成 `07:56:28`，
> 那是**我的抄写错误**（正确值 `06:56:28`，U8-B 原文与 238.04s 时长都能对上）。
> 一个字符之差，让两个区间从「无交集」变成「窗口被完整包含」—— 于是「结构上不可能中招」
> 这个结论在**我写下的数字上**是自我否定的。更正后结论仍成立（`06:56:28` < `06:59:14`），
> 但**依据换成了正确数字**。
> 附带一条口径修正：这里比较的是**进程运行窗口**，而门比的是 **fixture 两次快照的窗口**，
> 后者内含于前者。严格说「无交集」应针对快照窗口断言；进程窗口无交集是它的**充分条件**，
> 本例中充分条件成立，所以结论可用 —— 但两者不是一回事，不能互换着写。

### 清理与归位

存档 `treeB-cleanup-20260908T071858.txt`

**窗口实际时段 06:59:14 – 07:18:58**（比通告的 60 分钟短）。期间建过且**仅**建过 4 个**空目录**：

| 目录 | 建于 | 用途 | 清理 |
|---|---|---|---|
| `/tmp/test-vault-negctl-43048` | 06:59:27 | N1 修前 | 该轮跑完即 `rmdir` |
| `/tmp/test-vault-treeB-49484` | 07:01:45 | N2 修前 | 07:18:58 `rmdir` |
| `/tmp/test-vault-negctl-72013` | 07:09:23 | N1' 修后 | 该轮跑完即 `rmdir` |
| `/tmp/test-vault-treeB-88464` | 07:14:25 | N2' 修后 | 07:18:58 `rmdir` |

- ⛔ 全程 `rmdir`（非递归），**未用**递归删除；既有 12 个目录**一个没动、没改名**。
- `git worktree remove --force ../u10a-treeB-negctl` + `git worktree prune` → rc 均 0，
  `git worktree list | grep -c 'u10a-treeB-negctl'` = **0** ✅
- 与 (a) 开工清单逐条对照：**12 = 12，diff 为空** ✅

> ⚠️ 第一次对照时 diff 报了一行 `< /tmp/test-vault*`，**是判据坏了不是没归位**：我的
> `grep -oE '/tmp/test-vault[^ ]*'` 把开工存档的**标题行**与 `ls -ld /tmp/test-vault*` 的
> **命令回显**里的通配符文本也当成了目录条目。更正为 `awk '/^d/ {print $NF}'`（只取 `ls -ld`
> 的目录行）后 12 = 12、rc=0；并加验伪锚（往清单里塞一个假条目 → diff rc=1）确认该判据活着。
> 更正过程已追加进同一份清理存档的 §6b。

**批级闭环**：窗口关闭后再次 SendMessage 通知全部 9 条在线车道，附上上表 4 个目录名的完整清单
（U8 明确要求「把噪音面写死而不是写成疑似」）。已收到 U7 回执确认转交 U7-B。

---

## 三·五 Codex round-1 与整改（round-1 存档 `codex-review-CARD-HYGIENE-conftest.md`）

**round-1 绑定 `13a138c9`**（Codex 自行核对了 HEAD 与文件 sha）。结论：**BLOCKER 0 / HIGH 2 / MEDIUM 1**，
「不建议原样合并」。两条 HIGH 都成立，逐条整改如下；MEDIUM 一并修（属整改范围，非扩面）。

### HIGH #1 — 目录枚举失败不进 `unchecked`，新增硬门可静默通过（**成立，是本卡新引入的假绿**）

- **Codex 的证据**：在 Python 3.14.4 里只提取本文件的实际函数，用进程内审计钩子让 `os.scandir`
  在真实目录访问前抛 `PermissionError`，结果 `actual_helper_return=([], [])` —— **两次枚举均被拒，
  异常却被 `rglob` 抑制**，函数把「未检查」返回成「无命中、无检查失败」。
- **我的复核**：成立。`Path.rglob` 在**遍历期**吞掉 `PermissionError`，我那圈 `try/except OSError`
  只包住了 `resolve()` 与 `read_bytes()`，**够不着目录枚举这一层**。
  讽刺的是这道门的 docstring 里就写着「『没命中』≠『没检查』」，而它恰恰在枚举层违反了自己那句话。
- **整改**：改用 `os.walk(scan_root, onerror=_on_walk_error)`，回调把失败目录记进 `unchecked`；
  `followlinks=False`（默认）同时挡住目录符号链接把扫描面拐出树外。
- **承重验证（两层，缺一不可）**：
  - **N3b 同根对撞**（`negctl-n3b-enum-denied-samefixture-20260908T073956.txt`）：把 **round-1 的旧实现
    当变异体**，两版放进**内容逐字节相同**的两个扫描根（各含一个顶层命中样本 + 一个子目录命中样本），
    同一审计钩子条件下跑 ——

    | 版本 | baseline（正常条件） | denied（枚举被拒） | 判定 |
    |---|---|---|---|
    | 旧 `13a138c9`（`rglob`） | hits=**2** / unchecked=0 | `([], [])` | **SILENT_PASS 假绿** |
    | 新（`os.walk`+`onerror`） | hits=**2** / unchecked=0 | `([], [1])` | **RECORDED_UNCHECKED** |

    baseline 两边都是 2 ⇒ 扫描根可比、两版正常行为一致 ⇒ **只有枚举失败这一个维度变了**。
    > ⚠️ 第一版对撞（`negctl-n3b-enum-denied-20260908T073843.txt`）是**坏的**，如实留档：两版各从
    > 所在目录加载，扫描根 = 各自的 `__file__.parent`，baseline 一个 11 一个 0，**不可比**。
    > 「对照组存在」不等于「对照组前提成立」。
  - **N3c 端到端**（`negctl-n3c-enum-e2e-20260908T074041.txt`）：在 `backend/tests/unit/` 下建一个空
    子目录并 `chmod 000`（前提断言：先证当前用户确实枚举不了它），跑单文件 pytest →
    `ERROR tests/` = **1**、「无法检查」×2、「目录枚举失败」×2、`rc=1`；conftest sha 前后一致、
    探针目录无残留（`trap` 无条件清理）。
    **必须有这一层**：N3b 只证明「函数返回了正确的值」，N3c 才证明「门会因此变红」——
    整改前 `unchecked` 这条路径其实是**死的**（实测 252 文件零失败，只有单文件读/解析失败能进），
    整改后它才第一次真正可达。

### HIGH #2 — 漏检范围超过已登记，且把「归属未知」写成了「已排除本树回归」（**成立**）

- **Codex 的证据**：按实际判据做内存 AST 验算，列出七类漏检形态（见 (e) 的盲区清单），
  并指出告警文案写「**不是**本次运行新增的回归」、验收单写「这是别人弄的」—— **结论超出证据**。
- **我的复核**：成立，而且这正是「声明比证据宽」。门只能证明**归属不可判**，我却写成了**一定是别人**。
- **整改**：
  1. 告警文案改为「`/tmp` 全机共享 ⇒ **归属未知**：可能来自本 session，也可能来自任何别的进程 ⇒
     本 session 不判红，但**请核查或重跑**，不要直接当成「别人弄的」」，并明说源码门**不能**证明
     本树没有写者（它只看字符串常量）。判据串「环境受干扰」保留。
  2. docstring 盲区清单补齐七类，并**更正**一处我原先的技术不准确：我写「f-string 变量段漏网」，
     实际 `f"…完整前缀…{变量}"` **会**命中，只有前缀被拆开的才漏。
  3. fixture docstring 同步收窄「补偿」的措辞。
- ⚠️ **同型错误当天复发第二次**：整改完代码文案后，我在给并行车道的 `/tmp` 窗口通告里又写了
  「目录名不在这 6 个里 ⇒ 与本卡无关、**该当真回归查**」。U7-A 车道当场指出中间缺一步
  「没有别的车道在 `/tmp` 建同名目录」。我去 grep 了本批 32 份卡文（**只有 `U10-A.md` 命中**），
  但那只能证明**卡文层面**本批只有本卡计划建，不足以支撑「⇒ 是回归」——
  反证有三：那 12 个既有目录本身来源未判；`conftest.py` 注释记着 2026-09-06 01:55
  `card-y9-maingoal` 车道**确实**产出过这类目录；我 §〇 那条「本树无 `/tmp` 根写者」的 grep
  只在本树跑过（U11-A 本批就改了 4 个 `tests/unit/*.py`）。已更正为三分法口径。
  **一天之内同一个坑两次，一次在代码里、一次在协作消息里** —— 登记见 §六。

### MEDIUM — 文件符号链接可让「树内扫描」读到树外源码（**成立，一并修**）

`py.resolve()` 原先只用来判断是否为 conftest 自身，没有校验目标仍在扫描根内。已加
`resolved.is_relative_to(scan_root)`，越界进 `unchecked`。修它属整改范围，不算扩面。
（Codex 与本卡都未检查实际是否存在此类链接 —— 记入「本卡未证明什么」。）

### Codex 对我自述的逐条核对里，我接受的三处收窄

1. **自述 #1「告警不会升级」**：Codex 判「本次存档成立，普遍保证不成立」——
   `pytest.ini` 不在它的允许读取面，且我没有固定过滤策略，不能排除其他启动参数升级/隐藏 warning。
   **接受**：round-2 的 prompt 已把 `backend/pytest.ini` 加进读取面。
2. **自述 #8「四目录 nodeid diff 为空」**：Codex 判「**红** nodeid 口径成立」，但存档只有文件级
   进度点，不能证明**全部用例**的 nodeid 集相同。**接受**：本单凡涉及处一律写「红 nodeid 集」。
3. **P1 证明力**：Codex 指出 P1 的探针是个**未执行写入的常量**，所以它证明的是**源码规则承重**，
   不是写入归属。**接受**，(g) 与「未证明什么」已按此措辞。

### 整改后全部裁判复跑（代码改动 ⇒ 全部重跑，不复用 round-1 的存档）

| 裁判 | 结果 |
|---|---|
| N1' r2 `negctl-n1-after-20260908T074442.txt` | `8 passed, 11 warnings`、`ERROR tests/`=0、`环境受干扰`≥1、`rc=0` ✅ |
| P1 r2 red `negctl-p1-red-20260908T074127.txt` | 1 error、指名 `test_vault_init_service.py:<行>`、`rc=1`、还原 sha 一致 ✅ |
| P1 r2 green `negctl-p1-green-20260908T074420.txt` | `8 passed`、0 ERROR、`rc=0` ✅ |
| P2 r2 `negctl-p2-red-20260908T074140.txt` | `9 passed, 1 error`、指名 `backend/raw`×2、`rc=1`、清理+还原 ✅ |
| 7c① r2 `selfprobe-comment-20260908T074233.txt` | 仍绿、sha 还原一致 ✅ |
| 7c② r2 `selfprobe-const-20260908T074245.txt` | 仍绿、sha 还原一致 ✅ |
| 7a / 7d | `grep -c` = **0**、`ast.parse` rc=0 ✅ |
| N2' r2 `unit-n2p-20260908T074540.txt` | 树 B `/tmp/test-vault-treeB-79823`、`ERROR tests/`=**29**、`环境受干扰`=1、目录名命中 1、**对 202 基线 diff 为空** ✅；窗口 A`[07:45:40,07:49:40]` vs B mkdir `07:46:50` ✅ |
| ruff check / format --check | 均 rc=0 ✅ |

三端点对照（r2，仍成立）：

| 轮次 | 门 `pytest.fail` | `ERROR tests/` | `环境受干扰` | rc | vs 基线 diff |
|---|---|---|---|---|---|
| 开工基线（无 treeB） | 0 | 29 | 0 | 1 | 空 |
| N2 修前（+treeB） | **1** | **30** | 0 | 1 | **多一条 `>`** |
| N2' 修后 r2（+treeB） | 0 | 29 | **1** | 1 | 空 |

---

## 三·六 Codex round-2 与整改（存档 `codex-review-CARD-HYGIENE-conftest-r2.md`）

**round-2 绑定 `2c799422`**（Codex 自行核对 HEAD 与文件 sha `6ab7e0ac…`，并与本轮 N3c / N2' 存档第 2 行对上）。
结论：**BLOCKER 0 / HIGH 3 / MEDIUM 2**，仍不建议原样合并。
Codex 同时确认：round-1 的枚举假绿**已修复**，N3b/N3c 足以证明该具体修复；三端点
**202 → 203 → 202** 的红 nodeid 多重集对照**成立**（它独立重算过）。

**五条我全部判为成立，无驳回项。**

### HIGH #1 — 诊断结论越界：三类信号共用一句「运行污染了工作树」+ 同一份写者推定

- **Codex 的证据**：P1 只添加**从不执行**的常量（`negctl-p1-red-…:7`），输出却说「运行污染了工作树」
  并推定写者（同档 :22–29）；N3c 仅因**无法枚举**而红，同样输出污染断言（`…074041.txt:26–32`）。
  验收单 4-B 段还留着「这是别人弄的」，而同一份文件 :550–551 声称已改正 —— **自相矛盾**。
- **我的复核**：成立。round-1 我给 `violations` 加了两类**新语义**（源码规则命中、检查无法完成），
  却没动写在它出口上、原本只为第三类（骨架污染）写的标题和写者推定。
- **整改**：三类分开收集、分开报，标题改为「tests/unit **卫生门未通过**」：
  - 【工作树被写坏】首尾快照真的变了 ⇒ 本次运行确实写了东西。**写者推定只留在这一段**。
  - 【源码规则命中】静态规则，明写「**不表示本次运行写了任何东西**」。
  - 【检查无法完成】明写「这**不是**已经发生写入的证据，只是这道门这次没能看全」。
  验收单 4-B 段同步改掉「这是别人弄的」。
- **承重验证**（r3 实跑，三类各自落到正确分段）：

  | 探针 | 落入分段 | 含「运行污染了工作树」 | 含「最可能的写者」 |
  |---|---|---|---|
  | P1（源码常量，不执行） | 【源码规则命中】 | **0** ✅ | **0** ✅ |
  | P2（真建骨架目录） | 【工作树被写坏】 | 0（标题已换） | **1** ✅（仅此类保留） |
  | N3c（目录枚举被拒） | 【检查无法完成】 | **0** ✅ | **0** ✅ |

### HIGH #2 — 「全部裁判重跑」缺三个目录的本轮存档（**我的表述超出实际**）

- **Codex 的证据**：§三·五 的复跑表里没有 api / regression / skills；目录里对应的 after 存档
  时间戳是 07:13:30 / 07:13:44 / 07:19:45 —— **全是上一轮的**。
- **我的复核**：成立。这是措辞与事实不符，不是那三个目录真有回归。
- **整改**：**补跑**（不是改措辞了事）。r3 实跑结果：

  | 目录级 | 汇总行 | rc | 与开工红 nodeid 集 diff |
  |---|---|---|---|
  | `tests/api` | `268 passed, 40 warnings in 1.61s` | 0 | **空** ✅ |
  | `tests/regression` | `1464 passed, 6 skipped, 10 xfailed, 556 warnings in 327.60s` | 0 | **空** ✅ |
  | `tests/skills` | `369 passed, 22 warnings in 42.53s` | 0 | **空** ✅ |

  存档 `{api,regression,skills}-after-r3-20260908T081114.txt`；三轮的 `环境受干扰` 计数均为 **0**。

### HIGH #3 — 「无交集 ⇒ 结构上不可能中招」被我自己列的时刻反证（**抄错一个数字**）

- **Codex 的证据**：验收单同一句里列出窗口 `06:59:14–07:18:58` 与另一轮运行 `06:52:30–07:56:28`，
  后者**完整包含**前者，却得出「无交集」。
- **我的复核**：成立，而且根因是**抄写错误** —— 正确值是 `06:56:28`（U8-B 原文，238.04s 时长可交叉验），
  我写成了 `07:56:28`。一个字符让两个区间从「无交集」翻成「被完整包含」，
  于是支撑「结构上不可能中招」的那组数字在**我写下的版本里是自我否定的**。
- **整改**：更正数字；结论仍成立（`06:56:28` < `06:59:14`）但**依据换成正确数字**。
  同时按 Codex 的第二点补上口径区分：我比的是**进程运行窗口**，门比的是 **fixture 两次快照的窗口**，
  后者内含于前者 ⇒ 进程窗口无交集是快照窗口无交集的**充分条件**（本例成立故结论可用），
  但两者不是一回事，不能互换着写。该口径已同步给 U7-B 车道（它要用来写基线三分法）。
- **一般化（U7-A 车道提的，我采纳）**：**支撑结论的数字应当由判据独立重算，而不是从别处抄一遍。**
  一旦经过「我记得是 xx:xx」这一步，数字就和结论脱钩了，而且脱钩方向往往**恰好支持我想要的结论** ——
  这种错最难自查。可执行的形态：把文档里所有 `*-2026*T*.txt` 引用拿去和目录实有文件求差。

### MEDIUM #1 — 大小写别名可能把合法树内链接判成越界（**条件性假红**）

- **Codex 的证据**：把 `backend/tests/unit/conftest.py` 里的 `unit` 改成 `UNIT`，
  `alias.samefile(original) = True`（同一个文件），但 `alias.resolve().is_relative_to(scan_root) = False`
  ⇒ 合法目标被记为越界。
- **整改**：新增 `_hygiene_within_root()` 三态判定 —— 先试字面 `is_relative_to`（快），
  不成立再逐级向上用 `samefile` 做**文件系统身份**比对；比对本身失败（权限 / 竞态换链 / 目标消失）
  一律返回 `None` ⇒ 进「检查无法完成」。**「问不出来」既不压成「在根外」，也不压成「在根内」。**
- **承重验证**（`probe-case-alias-20260908T081030.txt`，带反向验伪锚）：

  | 输入 | 字面 `is_relative_to` | 新 `_hygiene_within_root` | 期望 |
  |---|---|---|---|
  | `tests/UNIT/conftest.py`（大小写别名） | **False（假红源）** | **True** ✅ | True |
  | `/etc/hosts` | — | **False** ✅ | False |
  | `backend/tests/api`（同 worktree 但扫描根外） | — | **False** ✅ | False |
  | `backend/app` | — | **False** ✅ | False |
  | `tests/unit/test_vault_init_service.py` | — | **True** ✅ | True |
  | 树外不存在路径 | — | `None`（不崩、不判 True）✅ | 非 True |

  反向验伪锚是必须的：只验「别名不再假红」会漏掉「修法把门弄松了」这一面。
- **顺带明确 Codex 提的边界**：扫描根是 `tests/unit`，所以链到**同一 worktree 的其他目录**
  （如 `tests/api`）**也会**被拒 —— 不能笼统描述成「只拒绝 worktree 外」。(e) 已按此改写。

### MEDIUM #2 — N3c 的前提 rc 记录与验收条件相反（**判据自己坏了**）

- **Codex 的证据**：存档写「非 0 = 确实不可枚举」，实际记录 `ls_rc=0`。
- **我的复核**：成立，根因是 `ls $PROBE 2>&1 | head -1` 之后取 `$?` 拿到的是 **`head` 的 rc**（恒 0）。
  ⚠️ **同一天早些时候我在 `ruff format --check | tail -3` 上已经踩过一模一样的坑并加了验伪锚**，
  写这个脚本时又犯一遍 —— **发现一个坑不等于以后不会再踩，除非把它变成检查项**。
- **整改**：先存变量再取 rc（`LSOUT=$(ls …); LSRC=$?`），另加一个**不经 shell 管道**的
  Python 侧独立第二源。r3 实测：`ls_rc=1` + `py_scandir=PermissionError` ✅
- Codex 同时确认这条**不推翻 N3c 的端到端证明**（pytest 自己在正文里指名了同一目录的枚举
  `PermissionError`，并给出 1 ERROR / rc=1）。

### 自述核对里的两处处置

- **#11「nodeid 集已一律改成红 nodeid 集」判「未完全落实」** —— 成立，仍有 5 处旧措辞。已全部改，
  并在「未证明什么」⑧ 补上「存档只有文件级进度点，**不能**证明全部通过用例的 nodeid 集也相同」。
- **#14「§六 所列三次之外没有更多同型错误」判「不成立」** —— 成立。已把计数从三次改为**六次**
  （见 §六 第 12 条），并且承认这个数字仍然只是「**已被发现的**次数」，不是「全部」。

---

## 三·七 Codex round-3 与整改（存档 `codex-review-CARD-HYGIENE-conftest-r3.md`）

**round-3 绑定 `459190f0`**。结论：**BLOCKER 0 / HIGH 2 / MEDIUM 1**。
Codex 同时确认：三态路径判定与三类失败出口**未发现新增假绿**；三个遗漏目录**确实补跑**；
红 nodeid 多重集 **202 → 203 → 202** 成立（它第三次独立重算）。**三条我全部判成立，无驳回项。**

### HIGH #1 — 分段已隔开，但**分段内部**仍把观测推断成确定写入

这是 round-2 HIGH #1 的**未闭合部分**：我把三类信号拆开了，却在**每一段新写的话里**又各埋了一个越界断言。

| 位置 | round-3 前（越界） | 现在 |
|---|---|---|
| 快照段标题 | 「…**即本次运行确实写了东西**」 | 「【**快照差异**】…发生了变化；⚠️ 差异本身**不指认写者**，也不单独证明写入内容 —— 例如 sha 侧读取失败会记 `None`，`None ↔ hash` 的差异未必是内容改变（既有边界，已移交）」 |
| 快照段提示 | 「**最可能的写者**: …」 | 「**最常见**的成因（**是排查起点，不是结论**）: …」 |
| 源码段 | 「它拦的是「**将来会**往全机共享 /tmp 写」」 | 「它只说明源码里出现了被禁止的硬编码常量，**既不表示本次运行写了什么，也不预言将来一定会写**（常量可能从不执行 —— 本卡 P1 正控用的就是这种）」 |
| 无法检查段标题 | 「以下目标**既没通过也没违规**」 | 「以下目标**是否违规尚不能判定**」 |
| 无法检查段说明 | 「这**不是**已经发生写入的证据」 | 「这**既不是**已经发生写入的证据，**也不表示这些目标没有问题**」 |

⚠️ 同一句话还写在**收集处的注释**里（`:271`），是本卡 patch 脚本的自校验（越界措辞黑名单）抓到的，
不是我读出来的。静态存档 `static-gates-r4-20260908T084107.txt` 记录四条越界串**全部归零**、
两条新串（`尚不能判定` / `不指认写者`）各出现 2 次。

### HIGH #2 — 验收单仍把「未发现写者 / 归属未知」写成已排除本树回归

- **Codex 点名三处**：`U:42`「本树已无 `/tmp` 根写者」、`U:107-108`（(d) 节转述的 round-1 旧告警文案，
  含已撤回的「不是本次运行新增的回归」）、`U:772-774`（方案依据仍以「本树没有写者」为前提）。
  并指出 `U:21-24` 的历史说明只列了 (c)(f)(g)(h)(i)，**漏了 (d)**。
- **整改**：
  - `U:42` → 「**在这两条搜索的命中里未发现写者**」，并写明文本搜索与 AST 门**共享同一组盲区**；
  - 历史说明补上 **(d)**，并在 (d) 节就地把那句话标成 ~~删除线~~ + 「已撤回，勿引用」；
  - 方案依据重写为**三条不依赖「本树没有写者」的理由**：① 前缀改不了别的树往 `/tmp` 根写；
    ② 门读的是全机 glob 结果（**这一条与本树有没有写者无关，单独就足以推翻原方案**）；
    ③ (n) 双树并发实证。
- 复查后「本树已无 `/tmp` 根写者」在全单只剩 **3 处否定式出现**（收窄说明 / 未证明清单 / 「不再当依据」），
  没有一处仍在把它当依据。

### MEDIUM — 清理对账判据**第三次**复发

- `treeB-cleanup-20260908T082507.txt` 又记录了 `13d12 / < /tmp/test-vault*`，且这次**没有**追加更正。
- **根因是我自己**：前两次我只在**存档里追加更正**，**没修脚本本体** ⇒ 第三次原样复发。
  这正是本卡反复登记的「**写下教训 ≠ 变成判据**」，只不过这次的受害者是我自己的对账。
- **整改**：从根上改 `cleanup.sh`（`grep -oE '/tmp/test-vault[^ ]*'` → `awk '/^d/ {print $NF}'`），
  并按 Codex 建议**保留原始失败记录**、在同一存档追加 §6b：更正判据（12 = 12、rc=0）
  + **验伪锚**（塞一个假条目 → rc=1，证明判据活着）+ worktree 残留 0。
- Codex 已独立抽取双方目录行确认「**相同的 12 项，双向差为空**」，即目录确实归位。

### 自述核对里我接受的补充

- **#3「全部裁判重跑」仍只能部分确认** —— 7a / 7d / ruff 缺 r3 独立存档。已补
  `static-gates-r4-20260908T084107.txt`（含 7a 的**双向**验伪锚：当前版 = 0、`da690bf8` 版 = 1）。
- **#4 缺独立命名的 r3 P1-green** —— 已在 r4 补齐独立存档。
- **#7 `_hygiene_within_root` docstring 措辞** —— 已收窄：**目标文件本身消失不一定返回 `None`**，
  只要父目录仍在且字面包含成立就返回 `True`，由后续 `read_bytes()` 的 `OSError` 收进 `unchecked`。
- **#13 `U:569` 仍写「nodeid 口径」** —— 已改「**红** nodeid 口径」。
- **#14「加 pytest.ini 后告警不会升级已解决」仍只能条件成立** —— 接受。round-1 那条意见的原因
  **不只是**它没被允许读 ini，还包括「外部启动参数与运行期过滤器仍可能升级或隐藏 warning」。
  我 round-2 把它窄化理解成「只是没读 ini」，是**对前意见原因的收窄**，已更正。
- **#15「七次之外没有更多」不能成立** —— 接受。本轮 MEDIUM 即第 **8** 次，且**计数无法穷尽**。

---

## 三·八 ⚠️ r4 收工跑出现一个 `>` 行（W4 哨兵归属漂移）—— 如实定性，未完全排除本卡影响

r4 收工 `tests/unit`（`unit-after-r4-20260908T084422.txt`）与 202 基线 diff **不为空**：

```
65a66   > FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
119d119 < FAILED tests/unit/test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning
```

按协议 §5，`>` 行是**阻断级**信号，所以逐条取证而不是引用别人的结论。

### 已经证明的（本树实测）

| 事实 | 证据 |
|---|---|
| 失败正文是 **W4 哨兵**（越界连接现网 Neo4j），不是业务断言 | `('::1', 7691, 0, 0) on thread MainThread (owner=…candidate…)` + `Neo4j health check failed: live Neo4j port connect attempted` |
| **越界连接的量没变** | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=12, advisory=0, unaccounted=0)` —— 与开工基线**逐字相同** |
| 红总数没变 | 两轮都是 **202**，`173 failed / 4749 passed / 48 skipped / 29 errors` |
| **同一份代码连跑两次，归属就会变** | r4 = `candidate422`（diff 有 1 增 1 减）；r4b = `mock_warning`（**diff 为空**）。存档 `unit-after-r4b-20260908T084934.txt`，conftest sha 与 r4 完全相同 |
| 换回 `da690bf8` 原版 conftest 在本树跑，归属为 `mock_warning` | `probe-baseline-swap-20260908T085441.txt`；换/还原走备份 + `trap` 无条件还原，前后 sha 逐字节一致 |

⇒ **这不是稳定的新增红**：它在同一代码状态下自己就会翻转，而承载它的量（连接次数、总数、失败正文）全部恒定。

### ⛔ 没有证明的（不写成「与本卡无关」）

**本卡在 session setup 段新增了一次 `os.walk` + AST 扫描（252 文件、实测 ~0.5s）。
如果越界连接来自 lifespan 里的异步任务，setup 多花 0.5s 确实可能改变它相对于用例边界的落点。
我没有排除这一点。**

- 基线对照只跑了 **1 次**且**未触发** `candidate422` —— 按 U1-A 车道的措辞，
  **「没触发」与「不会触发」是两回事**，1 次未触发不能当反面证据。
- 要真正排除，需要「无后台负载 + **交错** base/work/base/work + 记墙钟耗时作负载指标 + n≥10」的
  对照采样（U1-A 的 v2 设计）。**本卡没做**，因为单轮 4 分钟、20 轮约 80 分钟，
  成本远超这条信号的严重度（非阻断级四类之一，且量与正文均恒定）。
- ⚠️ **外部数据一律不引用为参照**：U1-A 曾提供 v1 的 `0/6 vs 2/6`，经它自查发现整组采样跑在
  一次后台全量 tests 的负载下、且是「先 6 次基线再 6 次本卡」而非交错，**组间不可比**，
  已被它自己作废；其 v2（10×2 干净采样）两边**完全相同**，但 20 次里 `candidate` 一次都没红
  ⇒ 那一轮根本没进入漂移窗口，**同样帮不了我排除**。两份都不写进本单当依据。

### 处置

1. **交付轮取 r4b**（diff 为空），但 **r4 那一轮原样留档**并在此说明 —— 不删、不重跑挑好的。
2. **判据改绑**（与本仓既有教训一致）：对这条信号，`逐 nodeid diff 为空` **自带 flaky**；
   可靠判据是 **`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 计数 + 失败正文**，两者本卡前后恒定。
3. 登记进「本卡未证明什么」与「台账待登记条目」，供主 session 复核时裁定。

---

## 四 DoD-3

### 4-A Claude 已代验（技术面）

- 四个门下目录级开工/收工各一轮，**红** nodeid 口径逐个 `diff`；`tests/unit` 对 202 条红基线 diff 为空。
- 负控 N1 / N1'（单文件，时序可断言）+ N2 / N2'（**真双树并发**，三条前提断言逐条落盘自证）。
- 正控 P1（新增源码门承重，指名 file:line）+ P2（既有骨架硬 fail 面不回退）。
- 自指验伪锚 7a/7b/7c①/7c②/7d 五条，其中 7c② 另附前提自证（防死探针）。
- 地盘门（只一个文件）+ 禁改面为空 + ruff check/format 全绿 + `:(exclude)` 写法验伪锚。
- 全部裁判存档在 `evidence-hyg-conftest/`，`.txt` 后缀、末行 `rc=`。

### 4-B 你来验（一句话 + 感觉）

**无变化。**

别人同时在跑测试的时候，我这边的测试不会再被误判成失败了；如果公共临时目录里真多出了东西，
你会看到**一条提醒**，而不是一片红。

**你要做的**：什么都不用做。下次看测试结果时，如果末尾多了一句带「环境受干扰」的黄色提醒 ——
那句话的意思是「公共临时目录变了，但**说不清是谁弄的**（可能是别人，也可能是这次跑自己），
重跑一次看看」，**不是**「你的东西坏了」，也**不是**「一定是别人弄的」。

**felt-sense**：以前的感觉是「跑完一看红了，得先花十分钟弄清楚这红到底是不是我造成的」；
现在的感觉应该是「哦，这条是环境噪音，它自己说了」。如果你仍然会为某条红发愣、分不清是谁的锅，
那就是这张卡没做到位，请直接说。

---

## 五 本卡未证明什么

1. **未证明能观测别的 worktree 的写入归属** —— 放弃了这条路（Codex Y6-A HIGH #1 已实证 `mtime` /
   进程 cwd / `lsof` 都不能单独证明**历史**写入归属），改判「环境受干扰」。
2. **未证明源码门能抓「非单个字符串常量」形态的写者**（Codex round-1 HIGH #2 逐条实测后**扩充并更正**）——
   门只看单个 `ast.Constant` 字符串常量，以下形态一律漏网：路径运算分段（`Path("/tmp") / (…)`）、
   运行期拼接（`"/tmp/" + name`、`os.path.join(…)`）、**前缀被拆开的** f-string、
   `"/tmp//…"` / `"/tmp/./…"` 等价写法、`bytes` 字面量、`tempfile.mkdtemp(prefix=…, dir=…)` 分参数、
   cwd 恰为 `/tmp` 时的相对路径、值来自环境/配置/扫描面外模块；以及**本文件整体被排除** ⇒
   本文件其他 fixture 里将来出现的完整硬编码路径同样漏检。
   > ⚠️ **更正我 round-1 的一处技术不准确**：我原先写「f-string 变量段漏网」，实际
   > `f"…完整前缀…{变量}"` **会**命中，只有前缀被拆开的才漏。
   > ⚠️ 一个现成的漏检实例就在本卡自己的存档里：树 B 探针用的正是
   > `Path("/tmp") / ("test-vault-treeB-" + str(os.getpid()))`，它**真的建出了目录**却不会被这道门看见。
   > 但这不能反过来说明树 A 现在存在同形写者。
2b. **未证明「本树已无 `/tmp` 根写者」这一前提在整改后仍充分** —— §〇 那条依据是**文本搜索**
   （`grep -rn 'test-vault' backend/tests`），而按 ② 的盲区清单，文本搜索同样看不见上述形态。
   本卡对这条前提的态度已收窄：告警文案不再据此断言「不是本次运行新增的回归」。
3. **未修 Codex Y6-A MEDIUM #5**（`:77` 读失败记 `None` ⇒ `None ↔ hash` 会被报成「文件改写」、
   `/tmp` 任一侧 `None` 直接跳过 ——「内容改变」与「检查无法完成」未区分）。同一函数，**故意不扩面**，
   只登记移交。⚠️ 注意本卡新增的源码门**自己**做了这个区分（`unchecked` 独立成条且不算通过），
   但**没有**回头把既有的 sha / tmp 两路也改成同一口径。
4. **未证明 `tests/contract` 的属性输入污染链**（`test_openapi_contract.py` → setup-wizard）—— 那是
   U5-D `CARD-HYGIENE-openapi` 的面，且不在本 fixture 的覆盖范围内（`conftest.py:34-41` 已写明）。
5. **未证明 `/tmp` → `/private/tmp` symlink 差异下的完整 glob 行为** —— 只实测到
   `Path("/tmp").glob()` 与 shell glob 都能看见那 12 个目录（走 `opendir` 由内核解析 symlink），
   而 `find -P` 看不见。未测其他工具 / 其他挂载形态 / `TMPDIR` 被改写时的行为。
6. **未证明 xdist 多 worker 下 session fixture 的快照边界** —— 本批不用 `-n`。多 worker 下每个
   worker 各有一个 session fixture 实例，`/tmp` 差集与源码扫描会各跑一遍，行为未测。
7. **(n) 已覆盖「两 worktree 真并发」的时序面**（N2 / N2' 两轮各自落盘，三条前提断言自证），
   但**未证明**：三棵及以上树同时跑；树 B 用**别的写法**（运行期拼接 / 非 pytest 进程 / 别的目录级套件）；
   以及**真实批次调度下两 session 窗口交叠的概率与频次**。树 B 的写者是本卡临时放的探针文件，
   **不是**别的车道的真实测试代码。
   ⚠️ 补充一条本轮实测到的边界：U5-A 在 07:02–07:06 跑 `tests/unit` **未中招**，因为树 B 的目录建于
   它的 before 快照之前 ⇒ **窗口交叠的"方向"也是条件**，本卡只证了「目录在窗口内新建 → 修前红/修后不红」，
   未系统性刻画各种交叠姿态。
8. **未证明 `tests/api` / `tests/regression` / `tests/skills` 三个目录级的「零影响」是结构性的** ——
   只证明了本次开工 / 收工两轮**红** nodeid 集相同（存档只有文件级进度点，
   **不能**证明全部通过用例的 nodeid 集也相同 —— Codex round-2 自述 #11 的收窄）。
   `conftest.py:34-41` 的覆盖面注释是**预期依据，不是证明**。
9. **未证明 `widen_window` 插件对 N1/N1' 结论无影响的"充分性"** —— 只论证了它不 import 被测模块、
   不碰门逻辑与 fixture、不建不删文件，且 (n) 的承重判据那一侧**完全没用它**。未做「同一负控在
   不用插件、靠多次重试命中 0.5s 窗口时也给出同样结论」的对照跑（那正是它不可复现所以要避免的）。
10. **未检查树内是否实际存在指向树外的 `*.py` 符号链接** —— MEDIUM 整改加了越界拦截，但
   Codex 与本卡都只证明了「若存在则会被记进 `unchecked`」，没有普查现状。
11. **未修 `_hygiene_snapshot()` 骨架检查的同族缺陷**（U3-A 车道复审提示 + 本卡实测确认，
   存档 `probe-pathlib-swallow-20260908T075350.txt`）：那里用的是 `Path.exists()`，
   **行为实测**（祖先目录 `chmod 000`）确认它把「问不出来」压成「不存在」并返回 `False` ⇒
   若 `backend/` 因权限问题 stat 不到骨架路径，门会判「骨架不存在」= 通过（假绿）。
   这是**既有**代码（Y6-A 引入），与 Codex Y6-A MEDIUM #5 的 `None ↔ hash` 同族，
   卡文禁止本卡扩面 ⇒ **只登记移交，不修**。本卡**新增**的扫描函数不吃这一坑
   （`os.walk(onerror=)` + 显式 try/except；`is_relative_to()` 是纯路径运算不碰文件系统）。
   > ⚠️ 方法学附注：我先用 `inspect.getsource` 做源码级检测，它对 `Path.exists` / `is_symlink`
   > 报「不吞 OSError」，与行为实测**矛盾**；以行为实测为准。源码 grep 不能替代行为实测。
13. **未证明本卡的 session-setup 扫描（~0.5s）不影响 W4 哨兵的归属分布** —— 见 §三·八。
    已证明「同一代码连跑两次归属就会翻转」「连接次数与失败正文恒定」，
    **未证明**「本卡不改变漂移概率」。需要无负载 + 交错 + n≥10 的对照采样，本卡未做（成本理由已写明）。
    ⚠️ 也**不引用**任何外部车道的采样作参照：U1-A 的 v1 组间不可比（已被其自己作废），
    v2 虽干净但 20 次未触发该窗口 ⇒ 「没触发」不等于「不会触发」。

12. **未证明「本批只有 U10-A 会建 `/tmp/test-vault*`」** —— 只 grep 了本批 32 份卡文
   （只有 `U10-A.md` 命中），那是**卡文层面**的证据，不覆盖运行期的实际写者（反证见 §六 第 12 条）。

---

## 六 台账待登记条目

> ⚠️ 本卡**不改台账**（台账只有主 session 写）。以下为待登记条目。

1. **Y6-A 行 Codex #1 残留 → 已按第三选项处置**：`/tmp` 硬 fail 降为「环境受干扰」告警 +
   新增树内 AST 源码字面量硬门。可归属信号（骨架 / tracked sha / 源码字面量）一律硬 fail 不变。
2. **Codex Y6-A MEDIUM #5 移交**（`None ↔ hash`「内容改变」vs「检查无法完成」未区分）——
   第十四批候选微卡。本卡故意不扩面。
3. **`/tmp/test-vault*` 既有目录清单与 mtime**：开工 12 个，存档
   `evidence-hyg-conftest/tmp-listing-open-20260908T064505.txt`。**不删、不改名、归属未判**。
   U11-A 于 06:58 独立实测同为 12 个。
4. **源码字面量门的已知盲区**：运行期拼接形态（见「本卡未证明什么」②）。若将来要覆盖，需要的是
   数据流分析而不是常量扫描 —— 属另开卡范围。
5. **Codex 轮次与每轮绑定 SHA**：见 §七。round-1 绑 `13a138c9`（BLOCKER 0 / HIGH 2 / MEDIUM 1，
   不建议原样合并）→ 整改 → round-2 绑整改后 commit。

12. **【本卡新增登记 · 判据比证据宽，同型当天已发现八次】**
    ⚠️ 「八」是**已被发现的**次数，**不是「全部」，而且这个计数无法穷尽**。
    每一轮外审都在我声称「没有更多了」之后又找出新的：round-2 判我「三次之外没有更多」不成立
    （+3，第 4~6 次），round-3 判「七次之外没有更多」不成立（+1，第 8 次）。
    ⇒ **「我已经找完了」这句话本身就是同一型错误的一个实例。**
    - 第 1 次（代码里，Codex round-1 HIGH #2 抓到）：告警文案写「**不是**本次运行新增的回归」、
      验收单写「这是别人弄的」，而门只能证明「归属不可判」。已改为「归属未知，请核查或重跑」。
    - 第 2 次（协作消息里，U7-A 车道抓到）：`/tmp` 窗口关闭通告写「目录名不在这 6 个里 ⇒
      与本卡无关、**该当真回归查**」，中间缺一步「没有别的车道在 `/tmp` 建同名目录」。
      我 grep 了本批 32 份卡文（只有 `U10-A.md` 命中），但那只证明**卡文层面**；反证三条：
      12 个既有目录来源未判、`conftest.py` 注释记着 `card-y9-maingoal` 车道 2026-09-06 01:55
      **确实**产出过、我那条「本树无写者」的 grep 只在本树跑过。已更正为三分法口径。
    - 第 3 次（同一条消息末尾，U7-A 同批抓到）：写「各车道现在都有窗口时刻表了」，
      实际只有本卡按协议 §2.3 发过窗口通告，别家未必。
    - 第 4 次（验收单里，Codex round-2 HIGH #1）：给 `violations` 加了两类**新语义**
      （源码规则命中、检查无法完成），却沿用为第三类（骨架污染）写的标题「运行污染了工作树」
      与写者推定 ⇒ P1 那个**从不执行**的常量被报成「工作树被污染」。已改三分段各自报。
    - 第 5 次（验收单里，Codex round-2 HIGH #2）：写「整改后**全部**裁判重跑」，
      而 api/regression/skills 三个目录级用的其实是上一轮存档。已**补跑**而非改措辞。
    - 第 6 次（验收单里，Codex round-2 HIGH #3）：把 U8-B 的运行区间 `06:52:30–06:56:28`
      **抄成** `06:52:30–07:56:28`，一字之差让「无交集」变「被完整包含」，
      而我据此写了「结构上不可能中招」。
    - **教训**：整改代码里的越界措辞，不会自动修好我在别处的同型表述。
      六次的共同形状是**判据能证到的，比它被拿去主张的窄**；前三次是「把『我这边排除了』
      写成『那就是对方的问题』」，后三次是「把『这一部分做了』写成『全部做了』」。
    - 第 7 次（**真实事故**，见下条 17）：窗口三通告只发 5 条车道，打红了无辜的 U6-A。
    - 第 8 次（存档里，Codex round-3 MEDIUM）：清理对账判据**第三次**复发 —— 前两次我只在
      存档追加更正、**没修脚本本体**，所以第三次原样复发，且这次连更正都没追加。
    - **一般化（U7-A 车道提，已采纳）**：**支撑结论的数字应当由判据独立重算，而不是从别处抄一遍。**
      一旦经过「我记得是 xx:xx」这一步，数字就和结论脱钩，且脱钩方向往往**恰好支持我想要的结论**。
      可执行形态：把文档里所有 `*-2026*T*.txt` 引用拿去和目录实有文件求差。

15. **【本卡新增登记 · 方法论，来自 U11-A + U7-A 的第二源验证】**
    U11-A 用**存档文件名 TS + 汇总行 `in <n>s`**（均取实测，不取转述）重算出自己三轮目录级的
    区间，再套本卡的 8 条目录清单 —— 不仅自洽，还解释了一件本卡自己没注意的现象：
    **为什么只有两个 `treeB` 打红、两个 `negctl` 没有** —— `negctl` 恰好落在它两轮**之间**，
    进了下一轮的 before 快照。这是门语义（比首尾快照差集，不比存在性）的直接后果。
    - U7-A 点出该模型最强处**不是**「多处可证伪点未被证伪」，而是**它解释了事前没人注意的现象**：
      只能解释**已知**结果的模型可能是照结果凑的；能解释**没注意过**的现象的模型很难是凑的。
      ⇒ 判据形态：**区间模型必须能解释「哪些红了、哪些没红」的全部分布，不能只解释红的那几个。**
    - U11-A 另一处正确示范：它的终审轮其实与本卡窗口一有约 94 秒**交叠**，结论不受影响
      （靠实测量 `新出现 /tmp/test-vault` 计数 = 0，非区间推理），它主动在存档写明
      「干净是实测结果、不是区间推理」⇒ **实测判据承重，区间推理只做辅助**；
      结论正确但依据可能被误读时，把依据写清楚比把结论写强更有价值。

17. **【本卡新增登记 · 真实事故：窗口通告漏发，打红了一条无辜车道】**
    窗口三（08:19:52–08:24:5x）开启时，我把通告发送面从窗口一的 **10 条车道缩到 5 条**
    （只发给「最近在跑目录级」的那几条），漏了 U6 / U1 / U2 / U4。
    **U6-A 恰好在 08:20:44–08:24:35 跑 `tests/unit` 目录级，被 `treeB-57658` 打红**，
    且它手上那份 07:50:26 的清单里没有这个目录（那是**窗口二结束时**的阶段性快照，只有 6 个），
    于是它不得不回头来问「这是不是你们建的」。
    - **两个错叠加**：① 通告覆盖面缩窄；② 给出的清单是阶段性的，却没标明「截止到哪个时刻」。
    - **与本卡主线是同一型**：判据/声明能证到的范围，比它被拿去使用的范围窄。
      前面六次是我写在文档里，这次是**真的让别人付出了代价**。
    - **修法**：立即确认归属 + 补发全部漏发车道 + 清单更正为 8 个并标注三段窗口。
      口径登记：**批级环境通告必须发全，且任何阶段性清单必须写明截止时刻。**
    - ⚠️ U6-A 的判断全部正确，无需它做任何更正：那条 ERROR 是窗口噪音、非其回归；
      它挂在末尾用例 teardown 上、归属随执行顺序漂移 —— 因为门比的是 session 首尾快照差集。

18. **【本卡新增登记 · 「未被撞上」≠「不会被撞上」（U11-A 的自我降级）】**
    U11-A 原本可以写「本卡文件级裁判全程未受窗口影响」，看到本卡「0.45s 窗口太窄、
    mkdir 落进去全靠运气」后主动降级为：它的文件级跑是 **0.78s / 0.54s / 0.41s** 量级，
    干净**不是因为有任何保护，而是因为窗口窄到撞不上**；同一份代码换成目录级（约 4 分钟）
    跑在同一时段，命中概率完全不同 —— 事实上它三轮目录级里有两轮真被撞了。
    ⇒ **「未被撞上」是这几次的采样结果，「不会被撞上」需要「窗口宽度 × 建目录频率」的论证。**
    与本卡 HIGH #3 同向：一个用错数字下强结论，一个差点用对数字下强结论；
    修法相同 —— **把依据的采样性质写出来，而不是把结论写强**。
    U11-A 另提醒：其时序模型用**进程区间**近似 fixture 快照区间，两者差一个收集期
    （目录级约几秒）。该近似对 4 分钟量级无害，但**对 0.45s 那种窄窗会翻转结论**，引用须写明。

19. **【本卡新增登记 · 共享夹具的顺序依赖（U5-A 第三变种）】**
    为让「夹具坏」与「缺陷仍在」可区分而改用共享 module-scope fixture 后，
    把缺陷锁定义在前提门**之前**（等价于 `-k` 过滤或随机化插件改变顺序），
    前提门里那次**实时**查询就读到已被改动的状态 ⇒ 假红。
    ⇒ **共享夹具消除了一种不可区分，同时引入了一种顺序依赖。**
    判据里凡「实时查询共享状态」的那一行，都要问「在我之前跑的用例改过它吗」。

20. **【本卡新增登记 · 移交主 session 裁定】W4 哨兵归属漂移让「逐 nodeid diff 为空」自带 flaky**
    （详见 §三·八）。本卡 5 次 `tests/unit` 目录级里出现 1 次 `candidate422 ↔ mock_warning` 互换，
    总数恒 202、`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 恒 12、失败正文同为 W4 越界连接。
    - **建议协议级口径**：凡以 `tests/unit` 目录级 nodeid diff 作合并门的卡，
      对 **W4 哨兵类** 失败应改绑「连接次数 + 失败正文」，不绑 nodeid；
      出现 1 增 1 减且两条正文同为哨兵、计数不变时，按 flaky 处理并留双份存档。
    - **本卡未排除的部分**：新增的 session-setup 扫描（~0.5s）是否改变漂移概率。请主 session 裁定
      是否需要补 n≥10 的交错对照采样（约 80 分钟）后再合。
    - 同一现象 U1-A 车道亦独立观察到（其 v1 采样因混杂因素作废、v2 未触发该窗口）。

16. **【本卡新增登记 · 跨车道复用价值】** 本卡 round-1 的 `Path.rglob` 教训在两条车道各挖出一处**真缺陷**：
    - U8-B `backend/scripts/mutation_kill_identity.py::check_expect_msg_unique` —— 生产侧扫描面用
      `root.rglob("*")`，承载的判据是「expect_msg 在生产文件里出现 **0 次**」，
      枚举被吞后 0 次退化成「我没看见」= 变异身份证明的地基塌了。已改 `os.walk(onerror=...)`
      并把枚举失败**收进返回列表**（消费方只看列表，只打印等于没说）。
    - U3-A `Path.exists()` 吞 `OSError` ⇒ 祖先目录缺搜索权限时与「压根没这个文件」不可区分；
      它 round-2 的修复只补了 `_walk`，调用方入口先 `exists()` 提前 return，**修了一半**。

13. **【本卡新增登记 · 协议级教训候选，与 U11-A 归并】**
    > 凡「扫描 / 抽取 → 比对 → 无差异即通过」的判据，必须先断言**抽取本身非空且命中数符合预期**，
    > 再谈比对结果。「没输出」是歧义：既可能是「没问题」，也可能是「根本没测到」。
    - 实例 A（本卡，文件系统版）：`Path.rglob` 抑制遍历期 `PermissionError` ⇒ 函数返回 `([], [])`
      ＝「无命中、无检查失败」。修法 `os.walk(onerror=...)`。
    - 实例 B（U11-A，文本版）：按旧行号 `sed` 抽取，插入 27 行后**抓空**，而「抓到的内容没差异」
      被当成「标记未被改动」。修法：内容锚定抽取 + 实测行号自证。
    - 本卡的落地形式：N3b 对撞里 **baseline 两边都必须是 2 个命中**，那 2 个就是「先断言抽取非空」。
    - 延伸（U3-A 车道补充，本卡实测确认）：pathlib 一批谓词把「问不出来」压成「不存在」——
      `Path.exists()` / `is_dir()` / `is_file()` / `is_symlink()` / `rglob()`。
      ⇒ 凡拿这些谓词判「这里没有东西」的地方，都要问一句「如果我根本看不见呢」。
      三态谓词（present / absent / unreadable）用 `os.lstat` 显式区分。

14. **【本卡新增登记 · 与 U2-A / U3-A 三方交叉确认的判据事实】**
    nodeid 差集判据必须带 `tests/` 前缀。实测：同一份 `tests/unit` 原始输出里，
    `^ERROR +[a-z_.]+:[a-z_]+\.py:[0-9]+` 形态的 logger 噪音行有 **42 条**；
    宽判据 `^(FAILED|ERROR) ` 收 **244** 行（虚报 42），本卡用的 `^(FAILED|ERROR) tests/`
    收 **202** 行且**全部含 `::`**（非 nodeid 行 0）。U2-A 与 U3-A 各自独立报出同一数字 42。
    ⇒ 判据太宽造**假红**，与太窄造假绿同样会误导。
6. **【方案级偏离 · 已按手册 §四.5 D-27 裁定 (乙) 处置 · 登记不阻断】**
   - **原方案**（设计稿 §9.E.5 / 任务书 W7）：「按 worktree 唯一前缀 或 `tmp_path_factory`」，
     正负控 =「两 worktree 同时跑，修前假红 / 修后不见，落盘两份」。
   - **本卡方案**：不加前缀；改为「可归属信号硬 fail（树内骨架 + 树内 tracked sha + **新增**树内
     源码字面量门，三者天然 worktree 唯一）+ 全机共享 `/tmp` 信号降 `warnings.warn`（判据串「环境受干扰」）」。
   - **依据（Codex round-3 HIGH #2 后已改为不依赖「本树没有写者」）**：
     ① 前缀只能改「本树自己写哪儿」，改不了「别的树写进 `/tmp` 根」，而假红恰恰只来自后者
     ⇒ 原方案对本卡症状**无效**；
     ② 门读的是 `Path("/tmp").glob("test-vault*")` 的**全机**结果，不是本进程产物 ——
     这一条与「本树有没有写者」**无关**，单独就足以推翻原方案；
     ③ (n) 的双树并发实证：树 B 在树 A 的 session 窗口内建目录 → 修前树 A 硬红、修后只告警。
     ⚠️ **不再**把「本树已无 `/tmp` 根写者」当依据 —— 那是文本搜索结论，证不到那么宽。
   - **等价的部分**：(c)/(f) 的 N1/N1' 与原正负控要证的是同一件事（别的树的 `/tmp` 写入不再让本树变红），
     输入形态同一、判据同一条差集逻辑，修前红 rc=1 / 修后 rc=0 且告警可见。
   - **不等价的部分**（原样登记，不说成等价）：原方案还覆盖「两 worktree **真并发**下 session 首尾
     快照窗口交叠」的时序面 —— 该面**已由 (n) 的 N2 / N2' 补跑覆盖**（真起第二棵 worktree、两侧
     `date` 自证交叠、修前红修后不红）。(n) 之外仍未覆盖的面见「本卡未证明什么」⑦。
   - **唯一放宽面**：不可归属的 `/tmp` 信号 硬 fail → 告警。**补偿** = 新增源码字面量硬门 +
     骨架 / tracked sha 面一字未动。**revert 点 = 本卡单 commit**。
   - **另请主 session 一并处理两件文档面事项（不阻断本卡合并，D-27 未涉及）**：
     ① 设计稿 §9.E.5 措辞仍是「按 worktree 唯一前缀 / `tmp_path_factory`」，未随 D-27 同步，
     建议改成「可归属 / 不可归属分流 + 双树并发验证」，免得下一张卡照旧稿再写一遍无效方案；
     ② 记录本卡唯一放宽面及其补偿与 revert 点。
7. **【流程瑕疵 · 登记不阻断】车道上一版卡文曾在无出处的情况下自称「核验裁定 = (乙)」**。
   协议 §1 明写车道不能自判通过，而 D-27 是主 session 2026-09-07 复核 32 卡时**才**作出的。
   本版卡文已把四处「核验裁定」一律改引「手册 §四.5 D-27」。结论未变（机制仍为 (乙)，
   (n) 双树并发仍是承重判据）。
8. **【本卡新增登记】卡文 §二.3 的 `sleep 2` 负控写法在本树上必然失效**（单文件 session 窗口只有
   ~0.45s，`sleep 2` 落在 before 快照之前 ⇒ 静默不红）。本卡的处置与等价性论证见 (c) 的偏离说明。
   建议后续卡文凡写「后台 mkdir + 单文件跑」的负控，一律先测 session 窗口宽度再定时序，
   或直接改用目录级（窗口 200s+）。
9. **【本卡新增登记】卡文 §二.7c 的还原指令 `git show HEAD:… > …` 对 conftest 自身不适用**
   （本卡改动尚未 commit 时会静默覆盖工作成果）。本卡改用工作区快照还原 + `cmp` 对账，见 §二。
10. **【本卡新增登记】卡文 (l) 的 `git ls-tree -r HEAD --name-only | grep -c stderr` = 0 判据口径过宽**
    （U8-B 车道先报，本卡实测复验）：该判据在 `da690bf8` 上**就已经是 1** ——
    命中 `_bmad-output/审查/G4-9-evidence/census-stderr.txt`（第五批遗留，与本卡无关）。
    根因是判据口径**比它要防的东西宽**：`.gitignore:261-264` 四条规则都是 `*.stderr*` 形态，
    要求 `.stderr` 作为扩展名出现，而该文件是 `-stderr.txt`（连字符不是点），
    `git check-ignore` rc=1 确认未被忽略；判据却用纯子串 `grep stderr`，于是抓到一个
    `.gitignore` 根本不打算管的文件。**正确口径 = 本 commit 引入数**：
    本卡 `git diff --cached --name-only | grep -c stderr` = **0**，
    evidence 目录里 stderr 文件数 = **0**。建议后续卡文改成引入数口径。

11. **【本卡新增登记 · 环境事实】11 条车道共享同一个 `backend/.venv` symlink 目标（`card-v5-lance`）**
    ⇒ 用 `ps` 里的**可执行文件路径**归因「谁在跑 pytest」会张冠李戴（相对 `.venv/bin/python` 启动的
    进程显示为共享路径）。正确维度是进程 **cwd**（`lsof -a -p <pid> -d cwd`）—— 这恰是门自己那段
    归属提示文案教的方法。本卡排批期一度据此误判过并发车道身份，已纠正。

---

## 七 Codex 复核

模型固定 `gpt-6-astra` · `model_reasoning_effort=ultra` · `codex-cli 0.153.3`（`codex --version` 实测）。
prompt 五分节 + 最小读取面写死；禁用措辞自检 4 项全 0、`grep -c 'gpt-5'` = 0。

| 轮次 | 绑定 SHA | 结果 | 处置 |
|---|---|---|---|
| round-1 | `13a138c9` | **BLOCKER 0 / HIGH 2 / MEDIUM 1**，「不建议原样合并」 | 两条 HIGH + 一条 MEDIUM 全部整改，逐条见 §三·五；全部裁判重跑 |
| round-2 | 整改后 commit | 见 `codex-review-CARD-HYGIENE-conftest-r2.md` | — |

- round-2 的 prompt 相对 round-1 增补：把 `backend/pytest.ini` 加进读取面（round-1 判我自述 #1
  「普遍保证不成立」的直接原因就是它不在允许读取面内）、把整改点与 N3b/N3c 存档列入、
  把我接受的三处收窄写明。
- ⛔ 车道不对 HIGH 自判通过：两条 HIGH 我都判**成立并整改**，没有驳回项。
- D-15：有代码改动 ⇒ 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0，上限 5。
