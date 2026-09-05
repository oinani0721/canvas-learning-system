# UAT — CARD-TOOL-lint-glob「lint glob 补 scripts/ + 变异残留门 + 存量格式债定性」

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-lint-glob]`
> 车道 `card/z7-tool`（从主干 `304f03ca` 切）· 同车道后续 Z7-B（pyright）→ Z7-C（Dredd）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z7-A.md`
> 本卡三个 commit：`1ffd6d36`（门 + 配置）、`b20fe550`（格式落盘）、
> `870e52b3`（Codex round-1 整改：门补 6 处静默放行 + 撤回 target-version）
> —— 卡文要求的「两个 commit」指**门与格式债不混提**，该约束成立；第三个是复核后的
> 整改 commit，如实分离，不与前两者混揉。
> 环境：macOS 15 / lefthook **2.1.6**（`/opt/homebrew/bin/lefthook`）/ ruff **0.15.9** /
> `backend/.venv` = Python **3.14.4**

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：**

1. **`scripts/` 目录终于进了提交前检查。** 在此之前，提交前的 Python 检查只看
   `backend/` 和 `src/` 两个目录——而 `src/` 下一个 Python 文件都没有（是个空壳分支），
   `scripts/` 下却有 **91 个**。也就是说，这个检查名义上管两个目录，实际上只管了一个。
   现在 `scripts/` 也进来了，顺带把 `backend/` 目录**最外层**那 2 个此前也漏掉的文件
   （`start_server.py` / `mutmut_config.py`）一起收进来。

2. **不小心留在代码里的测试残片，提交时会被拦下。** 做变异测试时会临时把生产代码改坏、
   跑完再改回来。改回来失败过一次——一段带标记的废代码在另一条分支上躺了几天没人发现。
   现在提交前会扫一遍你这次新增的行，发现这类标记就直接拦住，并告诉你是哪个文件第几行。
   （诚实说明：它只认那个特定标记；不带标记的残片它一条也抓不到，这写在了代码注释里。）

3. **`scripts/` 下 86 个脚本被重新排版了一次。** 纯机器排版，没有一处手改。验证分两层：
   全部 91 个文件在排版前后逐个做过"能不能编译"的对账，结果完全一样；另外挑了 5 个
   **真的跑起来**——提交前检查自己要调用的那个 OpenAPI 脚本（跑通，`DRIFT: none`），
   以及另一组后台辅助脚本自带的 48 条测试（全绿）。剩下 81 个只验到"能编译"这一层。

**你需要做什么**：无变化（提交代码前多检查两件事：脚本目录也过格式检查；不小心留下的
测试残片会被拦下）。

**顺带查出来的两个真问题（本卡只登记，没有修）**：

- `scripts/spec-tools/api-reality-dashboard.py` **目前根本跑不起来**——第 120 行有真的
  语法错误，Python 3.14 下连编译都过不去。这不是工具误报。修它需要先决定那行本来想
  输出什么，超出本卡范围。
- `scripts/validate-source-citations.py` 第 402 行有一处未定义的名字，一旦调用到那个
  函数就会报错。现在的检查规则集是空的，所以它不会被拦住。

---

## 4-A 技术验收

### 一 裁判命令逐条（卡文 §二）

| # | 裁判 | 结果 |
|---|---|---|
| 1 | `ruff --version`；`ruff check --show-settings scripts/send_bark.py` | 见 §二（配置口径定性） |
| 2 | `ruff check` / `format --check` 存量基线 | 见 §三（基线与台账对账） |
| 3 | `lefthook run pre-commit --command python-lint` → scripts/ 进命中集 | 见 §四（探针矩阵）+ §七（真 commit 端到端） |
| 4 | `grep -n 'mutant-residue-scan' lefthook.yml`、块内无 `glob`、负控 ②③ | 见 §五、§六 |
| 5 | 同级块零字节改动 | **空 => 通过**，另加语义级复核，见 §八 |

---

### 二 配置口径定性（卡文 (b)）——静态推断成立，且推出两个卡文未预料的事实

```
$ backend/.venv/bin/ruff check --show-settings scripts/send_bark.py
Resolved settings for: ".../scripts/send_bark.py"
Settings path:         ".../ruff.toml"        <- 根 ruff.toml, 不是 pyproject.toml
linter.rules.enabled = []
linter.line_length   = 88
formatter.line_width = 88
linter.unresolved_target_version = 3.9
```

对照 `backend/app/main.py`：`Settings path = backend/ruff.toml`，`rules.enabled = [...]`，
`line_length = 120`。

**结论（卡文推断全部证实）**：ruff 是「同目录 `ruff.toml` 优先于 `pyproject.toml`」，
不是两者合并。所以 `pyproject.toml [tool.ruff]` 里写的 `line-length = 120` 与
`select = [E,W,F,I,B,C4]` 对 `backend/` 之外的全部 tracked `.py`**一个字都没生效**。

**两个卡文未预料的事实（这两条决定了本卡必须动配置）**：

1. **`select = []` 不等于 `ruff check` 恒绿。** 解析器层的 `invalid-syntax` 不受规则集
   控制。扩 glob 前实测 `scripts/` 有 **27 条** `invalid-syntax`。
2. **其中 3 条是缺省 `target-version` 造成的假阳性。** `scripts/finalize-iteration.py`
   用了 Python 3.12 的 PEP 701 f-string，而 ruff 在没有 `target-version` 时按 py39 解析。
   该文件在实际执行它的解释器（`backend/.venv` = 3.14.4）下 `py_compile` **rc=0**。
   若不定死 `target-version` 就扩 glob，等于上线一道**会误杀合法文件**的门。

| `--target-version` | scripts/ 的 `invalid-syntax` 条数 |
|---|---|
| py39 / py310 / py311 | 27 |
| py312 / py313 | **21**（全部落在 `api-reality-dashboard.py` 一个文件里） |

剩下这 21 条不是误报：

```
$ backend/.venv/bin/python -m py_compile scripts/spec-tools/api-reality-dashboard.py
  File "scripts/spec-tools/api-reality-dashboard.py", line 120
    print(f"    {color(f'{ep[\"method\"]:6}', method_color)} {ep['path']}")
                              ^
SyntaxError: unexpected character after line continuation character   rc=1
```

**commit-1 曾据此在根 `ruff.toml` 补了两行**（`[lint] select` 一字未动）：
`target-version = "py312"` 与 `line-length = 120`。

**其中 `target-version` 已在 commit-3 撤回**——这是本卡最重要的一次自我更正，三条依据
每条都推翻了我 commit-1 时写下的理由：

1. **「py39 是无依据的缺省」不成立。** 根 `pyproject.toml:6` 有
   `requires-python = ">=3.9"`，ruff 由它**推断**出 py39。我实测过 ruff 的裸缺省：在一个
   只有 `ruff.toml`、没有 `requires-python` 的空目录里，`unresolved_target_version` 是
   **3.10**。所以 py39 不是缺省，是仓库自己声明的下限。
2. **原证据已被本卡自己的 commit-2 消灭。** `ruff format` 把 `finalize-iteration.py` 里
   那几处 PEP 701 嵌套同引号 f-string 改写成了旧版本也能解析的形式：

   ```python
   # 格式化前（304f03ca）—— py39 下 invalid-syntax
   print(f"**Validation**: {"✅ Passed" if validation_passed else "⚠️ Warnings"}")
   # 格式化后 —— `ruff check --target-version py39` 得 All checks passed!
   ```

   即：我加 `target-version` 的**唯一**证据，在下一个 commit 里就不存在了。
3. **抬到 py312 反而会放行 CI 跑不了的语法。** `.github/workflows/api-spec-sync.yml:50`
   的 `PYTHON_VERSION: '3.11'` 执行 `scripts/`；`readme-claims.yml` / `release-evidence.yml`
   用 3.12。声明下限是 3.9。把目标版本抬到 3.12 = 让 ruff 对 3.11 上会崩的语法放行。

**撤回后的实测现状**（格式化后，全 91 个文件）：

| `--target-version` | invalid-syntax | 分布 |
|---|---|---|
| py39 / py310 / py311 | 24 | 全部 `api-reality-dashboard.py` |
| py312 | 21 | 全部 `api-reality-dashboard.py` |

即：撤回 `target-version` 后**不会误杀任何合法文件**——剩下的错误全在那个真语法错的文件里，
与目标版本无关。且 `ruff format --check` 仍是 `90 files already formatted`，**零重排**。

> **仍留在仓库里的那一项，是本卡的裁决点**：`line-length = 120` 保留。卡文没点名要改，
> 我改了，依据是「(b) 要求定性哪个行宽 + (c) 允许 commit-1 含必要的配置口径」，且不改
> 就会把 ruff 的缺省 88 永久烤进 86 个文件。代价实测：需重排文件数 83（@88）→ 86（@120），
> 两个口径都要重排绝大多数文件，差别只在换行位置。若不认可，回滚 = 删这一行 + 重跑
> 一次 `ruff format`。

---

### 三 存量基线与台账对账（卡文 (d)）

扩门前，对 `git ls-files scripts/ | grep '\.py$'` 的全部文件实测：

| 度量 | 数值 |
|---|---|
| tracked `.py` 总数 | **91**（卡文写 90，**更正为 91**） |
| 其中一级（`scripts/x.py`） | **49**（与卡文一致） |
| 二级及以上 | 42（`daemon` 15 / `spec-tools` 10 / `lib` 5 / `trace` 4 / `bmad` 3 / `harness` 3 / `sprint` 1 / `ci` 1） |
| `src/` 下 tracked `.py` | **0**（本 SHA 下为空，与卡文一致；不是「恒」空集——建了 `src/` 它就会生效） |
| `ruff check`（现行规则集） | 27 errors，全部为 `invalid-syntax`，分布在 2 个文件 |
| `ruff check --select E9,F63,F7,F82`（假想的必错级） | 28 errors = 27 + **1 条 F821** |
| `ruff format --check` @88（修配置前的生效口径） | **83** files would be reformatted / 7 already formatted / 1 解析失败 |
| `ruff format --check` @120（本卡口径） | **86** would be reformatted / 4 already / 1 解析失败 |
| `ruff format --diff` @120 全量规模 | 878 hunk，`+2974 / -4341` 行 |

> 卡文「90 文件里 80 个含 >88 列行，合计 1450 行」是**代理度量**，本卡按要求全部用
> ruff 自己的文件数与 diff 行数替换，上表即是。

**台账「33 处」对账（卡文 (d) 要求对齐或更正）**

台账 §X5-B 行记：`scripts/daily_review_pick.py` ruff format 存量漂移 **33 处**。

```
line-length=88  target=py39   -> hunk 33   +224 / -106
line-length=88  target=py312  -> hunk 33   +224 / -106
line-length=120 target=py312  -> hunk 22   +90  / -94
```

**判定：台账数字准确，无需更正**，且它**反证了**当时量的是缺省 88 而不是仓库声明的 120
——这正是本卡把 `line-length` 定死的另一个理由。`b20fe550` 之后该文件 `format --check`
通过（`1 file already formatted`）。

---

### 四 glob 逐文件探针矩阵（卡文 (a)）

**判据设计**：不看 `lefthook` 的退出码——`scripts/` 有 83 个文件的存量格式债，rc 会被
它喂饱，测不出「是否命中」。判据绑定的是 `python-lint` 的 run 体**自己 echo 的那一行**
`[Python] Running ruff lint...`：出现 = 该命令真的被执行（命中 glob），不出现 = lefthook
判定无匹配文件而跳过。

**方法**：逐个真实 tracked 文件追加一个空行 → `git add` → `lefthook run pre-commit
--command python-lint --no-auto-install`（**不加 `--force`**，否则跳过语义失真；实测
`--force` 会让 `{staged_files}` 空展开，`ruff check` 无参扫全树报 23 条无关错误）→
`git reset` + 从备份 `cp` 回 + 逐文件 sha 复核。`lefthook.yml` 的 glob 由脚本改写，
带 `trap ... EXIT INT TERM` 的无条件还原 + sha 比对。

| 探针（真实 tracked 文件） | A 单星（本卡采用） | B `**`（卡文禁用） | C 主干 `304f03ca` 原值 |
|---|---|---|---|
| `scripts/send_bark.py`（一级） | **HIT** | **skip** | skip |
| `scripts/lib/planning_utils.py`（二级） | HIT | HIT | skip |
| `scripts/spec-tools/check-openapi-drift.py`（二级） | HIT | HIT | skip |
| `scripts/daemon/tests/test_qa_gate_generator.py`（三级） | HIT | HIT | skip |
| `backend/start_server.py`（一级） | **HIT** | **skip** | **skip** |
| `backend/app/main.py`（二级） | HIT | HIT | HIT |
| `backend/app/api/v1/endpoints/ping.py`（五级） | HIT | HIT | HIT |
| `tests/bdd/conftest.py`（阴性：三根之外的 `.py`） | skip | skip | skip |
| `docs/architecture.md`（阴性：非 `.py`） | skip | skip | skip |

```
A = {backend,src,scripts}/*.py        <- 本卡采用
B = {backend,src,scripts}/**/*.py     <- 卡文禁用的天真写法
C = {backend,src}/**/*.py             <- 主干 304f03ca 原值
[restore] lefthook.yml 还原逐字节相同  sha=7157d21b74da614f
```

**结论**：

- X8 钉死的引擎矩阵在本机、用**本卡的候选 glob**复现成立（不是引用，是重跑）。
- 天真写法 B 会漏 `scripts/send_bark.py` 与 `backend/start_server.py` 两类一级文件
  ——正是卡文警告的 49 + 2。
- 主干原值 C 除了漏掉 `scripts/` 全部 91 个，**还漏掉 `backend/` 一级那 2 个**
  （`start_server.py` / `mutmut_config.py`）；这是本卡顺带修掉的、卡文只在事实表提了
  一句的缺口。
- 两个阴性对照在 A 下仍 `skip` ⇒ 新 glob **没有过宽**。

---

### 五 `mutant-residue-scan` 门（卡文 (e)）

位置 `lefthook.yml:254`，`pre-commit.commands` 段**最后一块**；YAML 解析后该块的键
只有 `['run']`，**无 `glob` 键**（刻意：残留可以落在 `.md` / `.yml` / `.sh`）。

```
$ grep -n 'mutant-residue-scan' lefthook.yml
254:    mutant-residue-scan:
$ python -c "...yaml..."
在 pre-commit 段内: True; 键: ['run']; 有 glob: False; 是最后一个块: True
```

实现要点（**下列形态是 commit-3 整改后的**；commit-1 的初版有 6 处静默放行，见 §十）：

- 扫描面 = `git diff --cached -U0 --diff-filter=AM --no-renames --no-color` 的**新增行**。
- 文件枚举用 `--name-only -z` + `tr '\000' '\n'`（**不是** `core.quotepath=false`），
  逐文件查询加 `--literal-pathspecs`。
- 行号由 awk 的 hunk 状态机从 `@@` 头推算，只有 `@@` 之前的行才算文件头；
  输出形如 `文件:行号: 原行内容`。
- git / awk 任一失败置 FAILED 位 → **fail-closed 阻断**，不再报 OK。
- 临时文件放在 `mktemp -d` 出来的 0700 目录里，`trap ... EXIT` 清理。
- 排除名单硬编码在 `case` 里：两个变异 harness 本体 + `_bmad-output/*`。
- **标记串在运行时由两段字符串拼出**，使 `lefthook.yml` 自身不含该字面量。否则每次编辑
  这个块，它都会拦下自己的提交（判据自指）。实测 `grep -c` 该字面量于 `lefthook.yml` = **0**。
- 块内注释写死诚实契约：X7-A 那轮里 `fsrs_bridge.py` 被追加的 `_s.exit(9)` **不带标记**，
  三裁判全绿、按标记 grep = 0，本门**一条也抓不到**；唯一可靠锚点是全文件 sha 基线。

**行号算法专项验证**（awk 从 `-U0` hunk 头推算新文件行号，是这个实现里最容易错的一处）：

对已 tracked 的 `scripts/send_bark.py`（156 行）人为制造 3 个位置的改动——靠前纯插入、
中部「删 2 行 + 插 1 行」、靠后连续插 2 行——刚好覆盖到三种 hunk 头形态：

```
@@ -5,0 +6 @@                                      <- 新侧无逗号（单行 hunk）
@@ -79,2 +80 @@ def load_key() ...                 <- 删除与插入混合，新侧无逗号
@@ -151,0 +152,2 @@ def main():                    <- 多行插入
```

**期望值取自独立来源**（`git show :<file> | grep -n`，直接读暂存 blob，不复用被测的 awk）：

| # | 期望行号 | 门报出的行号 | 内容 |
|---|---|---|---|
| probe-A | 6 | **6** | 一致 |
| probe-B | 80 | **80** | 一致 |
| probe-C1 | 152 | **152** | 一致 |
| probe-C2 | 153 | **153** | 一致 |

4/4 行号与内容全部吻合；跑完 `send_bark.py` 还原逐字节相同，`git status` 干净。

---

### 六 负控（卡文 (f)）

> 负控产物全部当次还原：临时文件 `mv` 到 scratchpad，`g32b_mutation_gates.py` 从备份
> `cp` 回并 sha 逐字节比对，最终 `git status --porcelain` 只剩本卡该有的改动。

#### ① python-lint 负控 —— 拆成三个变体，绑定「被哪一层拒的」

单一个「rc≠0」是粗判据：`scripts/` 的存量格式债足以把它喂饱，测不出 lint 那一层是否
承重。所以拆成三个各带**一种**缺陷的样本：

| 变体 | 样本 | 结果 |
|---|---|---|
| ①a 未定义名，格式合规 | `print(z7_undefined_symbol_that_does_not_exist)` | **门完全放行（rc=0）** |
| ①b 纯格式漂移 | `x    =    1` | 门阻断，拒因层 = `ruff format --check` |
| ①c 语法错误 | `def broken( :` | 门阻断，拒因层 = `ruff check`（invalid-syntax） |

**①a 的样本有效性验伪**（证明它是真缺陷而不是无效样本）：

```
现行配置(根 ruff.toml, select=[]):   All checks passed!
--select E9,F63,F7,F82:              F821 Undefined name `z7_undefined_symbol_...`
格式:                                 1 file already formatted
```

**⇒ 如实结论：本卡给 `scripts/` 扩的是「语法 + 格式」门，不是「lint 规则」门。**
未定义名一类的违规**不会**被拦。原因是 `scripts/` 解析到根 `ruff.toml`，其
`[lint] select = []` 让规则集为空——而打开它是卡文的硬边界之一（2000+ 存量，只定性）。
这条已写进 `lefthook.yml` 的块注释与 commit-1 的 body，并登记为台账条目。

#### ② 普通文件新增标记行 → 必须阻断

```
[Mutant-Scan] BLOCKED — 暂存的新增行里带变异残留标记:
  scripts/_z7_negctl_residue.py:2:     if False:  # MUT+ANT: negative control z7
[Mutant-Scan] 变异 harness 没还原干净。先 restore 被改的生产文件,
[Mutant-Scan] 再拿变异前的全文件 sha 基线逐个复核 —— 标记只是最弱那道网。
exit status 1
-> 输出含文件名: 1   含行号: 1
```

（上面 `MUT+ANT` 是本文档为免自触发而写的分写形式；实际输出是连写的那个大写标记。）

#### ③ 排除名单：harness 自身 → 必须放行

**第一版是弱判据**——「门没报」也可能是因为什么都没进暂存区（vacuous pass）。加固后
先断言标记行**确实在暂存区新增行里**，再看门的判定：

```
=== ③ 排除名单：harness 自身 ===
  [前置断言] backend/scripts/g32b_mutation_gates.py   新增行带标记 1 条
  [门判定] 放行

=== ④ _bmad-output 排除 ===
  [前置断言] _bmad-output/_z7_negctl_doc.md           新增行带标记 1 条
  [门判定] 放行

=== ④b 反证：同一份内容移出 _bmad-output → 必须阻断 ===
  [前置断言] scripts/_z7_negctl_residue.py            新增行带标记 1 条
  [门判定] 阻断
      scripts/_z7_negctl_residue.py:3: 审查正文引用 `if False:  # MUT+ANT` 作为例子。

=== ③b 混合：harness(放行) 与普通文件(阻断) 同时暂存 ===
  [门判定] 阻断；报了 harness 吗(期望 0): 0
```

④b 与 ③b 是③④「放行」的**验伪锚**：同一份字节移出排除目录立刻被阻断，证明放行来自
排除名单，而不是门本身失效。

#### ⑤ 自指验伪（卡文没要求，但不做就会在 commit-1 当场翻车）

把本卡改过的 `lefthook.yml` + `ruff.toml` 自己暂存：

```
  暂存 diff 行数: 99
  [前置断言] lefthook.yml 新增行带标记 0 条 / ruff.toml 新增行带标记 0 条
  [门判定] 放行
  lefthook.yml 大写字面量计数(期望 0): 0
```

---

### 七 真 commit 路径端到端（不是 `lefthook run` 模拟）

`b20fe550` 提交时 `git commit` 自己打印的 hook 输出（`.git/hooks/pre-commit` 由 lefthook
安装，`core.hooksPath` 指向主仓，worktree 共用）：

```
│  cypher-vault-filter-lint (skip) no matching staged files
┃  mutant-residue-scan ❯
[Mutant-Scan] OK (staged additions carry no mutation marker).
┃  python-lint ❯
[Python] Running ruff lint...
All checks passed!
[Python] Lint OK.
[Python] Checking format...
86 files already formatted
[Python] Format OK.
│  python-typecheck (skip) no files for inspection
│  readme-claims-lint (skip) no matching staged files
✔️ mutant-residue-scan (1.18 seconds)
✔️ python-lint (0.05 seconds)
```

同一屏里 `(skip) no matching staged files` 就是扩 glob 前 `python-lint` 面对 86 个
`scripts/` 文件时会打印的形态——对照成立。

---

### 八 禁改边界（卡文 (g)）

卡文裁判 5 原命令：

```
$ git diff 304f03ca HEAD -- lefthook.yml | grep -E '^[-+]' \
    | grep -E 'python-typecheck|spec-sync|cypher-vault|readme-claims'
空 => 通过
```

> **这条判据在本卡被同一个陷阱假红了两次**，都因为它是纯文本 grep：
> 第一次，我在 `python-lint` 注释里**提到**了 `python-typecheck` / `spec-sync`；
> 第二次（commit-3），我把 lefthook 的真实执行顺序写进注释，又点了那四个块名。
> 两次都改写措辞规避（「下方 pyright 块」「本文件 OpenAPI 快照块」「以 c 开头的
> Cypher 门」…），判据恢复为空。
> 这是「判据不能自指」的同型陷阱——**判据把「文档提到 X」和「改动了 X」当成同一件事**。
> 教训不是「注释别提块名」，而是**这条判据本身不够格**，所以下面那条语义级判据不是锦上
> 添花，是它的替代品。
>
> 另：`ruff.toml` 的注释里出现了 `api-spec-sync.yml` / `readme-claims.yml` ——那是
> **CI workflow 的文件名**，不是 hook 块名。卡文的裁判 5 限定了 `-- lefthook.yml`，
> 不受影响；但若有人去掉路径限制跑那条 grep，会看到这两行，特此说明。

因为上面这条判据可以被**注释文本**喂饱，另加一条不依赖措辞的语义级判据——把
`304f03ca` 与 HEAD 的 `lefthook.yml` 分别 YAML 解析后，对每个冻结块取内容 sha 比对：

| 块 | base | now | 判定 |
|---|---|---|---|
| `spec-sync-flat` | `4cafa014e489291c` | 同 | UNCHANGED |
| `spec-sync-root` | `e9feff2fe4102852` | 同 | UNCHANGED |
| `ghost-files` | `6ffb126e293829a0` | 同 | UNCHANGED |
| `python-typecheck` | `ff3f9c9b3dfb53dc` | 同 | UNCHANGED |
| `cypher-vault-filter-lint` | `86277e976b7e81a6` | 同 | UNCHANGED |
| `readme-claims-lint` | `7c2fa3ab760a6b5f` | 同 | UNCHANGED |
| `[segment] commit-msg` | `0a6b06ea93ae62f7` | 同 | UNCHANGED |
| `[segment] pre-push` | `f47d2ea57b553c48` | 同 | UNCHANGED |

新增块仅 `mutant-residue-scan`；`python-lint` 的 `run` 体**逐字节未变**，只改了 `glob`
一行 + 注释。

> 该判据的已知盲区（如实声明）：YAML 解析会丢注释，所以它证明的是**行为等价**，不是
> 「字节未动」。注释层面的字节由上面那条 grep 判据 + `git diff --stat`（`98 insertions,
> 1 deletion`，唯一那一行删除就是旧 glob）交叉覆盖。

---

### 九 commit-2 的安全性对账

`ruff format` 落盘：`86 files reformatted, 4 files left unchanged`，1 个解析失败。
git 侧 `86 files changed, 3270 insertions(+), 4356 deletions(-)`。

落盘**前后**对全部 91 个文件逐个 `py_compile`，输出逐行 diff：

```
before: OK=90  ERR=1   (ERR = scripts/spec-tools/api-reality-dashboard.py)
after:  OK=90  ERR=1
diff:   无差异 => 格式化未改变任何文件的可编译性
```

> 副作用如实登记：`py_compile` 对账在 `scripts/**` 下生成了 `__pycache__`。这些目录被
> `.gitignore:2` 覆盖，**`git status` 看不见**（正是「gitignore 让 git 判据恒绿」的盲区），
> 已在收尾时全部移出工作树，`find scripts -type d -name __pycache__ | wc -l` = 0。

**补一条真运行时验证**（`py_compile` 只证明「能编译」，不证明「能跑」）：commit-2 重排的
86 个文件里，有一个是 **lefthook 自己要调用的** `scripts/spec-tools/check-openapi-drift.py`
（`spec-sync-flat` / `spec-sync-root` 两个块都用它）。重排后真跑一遍它的只读比对模式：

```
$ backend/.venv/bin/python scripts/spec-tools/check-openapi-drift.py --snapshot backend/openapi.json
...
DRIFT: none (paths=193 schemas=353)
rc=0
跑完 git status（tracked 部分）: 空 —— 只读模式未落盘
```

即：X8 那道 OpenAPI 漂移门在本卡两个 commit 之后**仍然是绿的**，而且它依赖的那个脚本
被重排后功能完好。

**第二条运行时验证**：`scripts/daemon/tests/` 下 3 个测试文件也在重排范围内，且它们测的
`qa_gate_generator.py` / `story_file_updater.py` / `post_process_hook.py` 同样被重排。跑一遍：

```
$ backend/.venv/bin/python -m pytest scripts/daemon/tests/ -q --no-header \
      -p no:cacheprovider --override-ini="addopts="
48 passed in 0.21s
```

副作用对账（`find . -newer <标记>`，排除 `.git` / `__pycache__` / venv）：唯一新文件是
`.hypothesis/unicode_data/16.0.0/charmap.json.gz`，落在 `.gitignore:106` 覆盖的子树里
（注：`.hypothesis/constants/**` 在本仓是**已 tracked** 的，但本次未触及）；
`git status` 的 tracked 部分为空。`__pycache__` 已同批移出工作树。

⇒ 合计真实执行覆盖 `scripts/` 下 **5 个**被重排的模块（1 个 hook 脚本 + 3 个被测模块 +
其测试自身），另外 81 个仍只有 `py_compile` 级证据。

---

### 十 Codex 复核（卡文 (h)）—— 一轮已完成，9 条全部本机复现，修 7 条

**模型**：`gpt-6-astra` + `model_reasoning_effort=ultra`（用户 09-05 裁定的口径），
`codex-cli 0.153.3`，`--sandbox read-only`，审查面 `304f03ca..b20fe550`。
产物 `_bmad-output/审查/codex-review-CARD-TOOL-lint-glob.md`（9246 字节，75,869 tokens）。

**终裁摘要**：**BLOCKER 0 / HIGH 0 / MEDIUM 8 / LOW 1**。按 `card-batch-protocol.md` §1
的合并门（阻断级 = 数据丢失 / live vault 或 7691 写入 / 安全 / 指定裁判红 / 负控假绿），
**阻断级 = 0**。Codex 原文最后一句：「有条件性的数据丢失／安全风险：临时文件创建可能在
共享目录与符号链接条件下越权截断目标；**未发现已经发生的数据丢失或越权写入证据**。」

> ⚠️ 纪律声明：以下每条我都**自己跑了一遍**再采信，不因为它是审查者说的就当真。
> 反过来，它推翻我结论的两条（⑥ 执行顺序、⑧ target-version 依据）我也没辩护，直接改。

| # | 严重度 | Codex 指出 | 我的独立复现 | 处置 |
|---|---|---|---|---|
| 1 | MEDIUM | git/awk 失败被管道吞成 0，扫描没跑完却报 OK | 成立 | ✅ 修（FAILED 位 + fail-closed），负控 R6 |
| 2 | MEDIUM | `core.quotepath=false` ≠ 原始路径；`"`/`\`/TAB 仍被引用 → 静默放行 | 成立（**本卡在收到复核前已独立发现并验过修法**） | ✅ 修（`-z`+`tr`+`--literal-pathspecs`），负控 R2 |
| 3 | MEDIUM | 正文里以 `++` 开头的新增行被当文件头吞掉，且行号少 1 | 成立：喂 `+++<标记>` 得**空输出**，下一行报成第 1 行（应为 2） | ✅ 修（hunk 状态机），负控 R3 |
| 4 | MEDIUM | `color.ui=always` 下 `^+` 失配 → 静默放行 | 成立：同一 diff 命中数 **90 → 0** | ✅ 修（`--no-color` **标志**；`-c color.ui=never` 不够，被更具体的 `color.diff=always` 盖过，实测命中仍为 0），负控 R4 |
| 5 | MEDIUM | `--diff-filter=AM` 漏掉被判 `R` 的重命名+改动 | 成立：真 fixture 得 `R099`，旧写法枚举该文件 **0** 次 | ✅ 修（`--no-renames`，转成 `A` 后枚举 1 次并阻断），负控 R5 + 验伪锚 |
| 6 | MEDIUM | YAML 段末 ≠ 最后执行；2.1.6 按名字排序，本块在 OpenAPI 快照块**之前** | 成立，**而且我 commit-2 的 hook 输出里就摆着这个顺序，我读过没看出来** | ⚠️ 部分修：实测加 `priority:` 会把它排到**最前**（带 priority 的整体先于不带的），在不动同级块的前提下做不到「最后」→ **改窄声明**并登台账 |
| 7 | MEDIUM（条件性安全） | 可预测的 `$$` 临时路径 + `: >` 截断，有符号链接条件下的越权写风险 | Codex 自己已声明「当前 TMPDIR 是本人 0700 私有目录，不能据此称已可利用」 | ✅ 修（`mktemp -d` 0700 + EXIT trap） |
| 8 | MEDIUM | `target-version` 的两条依据均不实 | **成立，且我另找到第三条更强的理由**（见 §二） | ✅ **整项撤回** |
| 9 | LOW | F821 注释行号 402 已过期 | 成立：现为 **392**，是我自己 commit-2 的重排推的 | ✅ 修（不再写死行号） |

**Codex 对我五项自称的裁定**（原文表格，摘要）：

| 自称 | Codex 判定 |
|---|---|
| 1. glob 正确 | **成立**（限 2.1.6 默认引擎）。另指出引擎**忽略大小写**、会匹配三个根下的隐藏目录/vendor/fixture；`src` 的「恒空集」应改为「本 SHA 下为空」（已改） |
| 2. 配置口径 | **部分成立**。独立数出 **185/185** 个 backend 外 tracked Python 全部解析根配置（scripts 91 + 其余 94，与我一致） |
| 3. 残留门 | **部分成立**——无 glob / 标记拼接 / 普通阻断成立，上述漏检使「完整保证」不成立（已修） |
| 4. 诚实性 | **部分成立**。`845/91/49/2/0`、其余 94、harness 的 **153/10** 处标记、lefthook 的 **0** 处字面量、**83→86** 全部独立重现吻合。指出「sha 比较只能证明纳入集合的文件与跑前一致，不能证明跑前已干净」——采纳 |
| 5. 纯格式化 | **成立，且证据强于我的抽查**：它把 86 个父提交文件用 ruff 0.15.9 **重放**，86/86 与最终 blob **逐字节一致**；忽略位置的 **AST 86/86 一致**；无文件增删或权限变化 |

**commit-3 后的回归矩阵**（11 条，每条「期望放行」都先断言标记行确实入暂存，防空跑）：

| 用例 | 期望 | 实际 |
|---|---|---|
| 普通文件带标记 | 阻断 | 阻断 |
| harness 本体（排除名单） | 放行 | 放行 |
| `_bmad-output/` 文档（排除名单） | 放行 | 放行 |
| 文件名含 `"` | 阻断 | 阻断 |
| 文件名含 `*` | 阻断 | 阻断 |
| 文件名含中文 | 阻断 | 阻断 |
| 文件名含空格 | 阻断 | 阻断 |
| 新增行以 `++` 开头 | 阻断且行号 2/3 | 阻断，报 `:2:` `:3:` |
| `color.ui=always` | 阻断 | 阻断 |
| 重命名(`R099`)+改动 | 阻断 | 阻断（`:158:`） |
| `mktemp` 失败 | FAILED（fail-closed） | FAILED |
| 暂存门配置文件自身（自指） | 放行 | 放行 |

跑完 `g32b_mutation_gates.py` 与 `send_bark.py` 均**还原逐字节相同**，工作树只剩本卡改动。

---

### 十·附 CLI 阻塞与其处置（过程记录）

```
$ codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" ...
rc=0，正文 0 字节，stderr 5916 字节，尾部：
  warning: Model metadata for `gpt-6-astra` not found. Defaulting to fallback metadata...
  ERROR: {"status":400,"error":{"message":"The 'gpt-6-astra' model requires a newer
         version of Codex. Please upgrade to the latest app or CLI and try again."}}
```

本机 `codex-cli 0.147.0`（homebrew cask，symlink 到 `Caskroom/codex/0.147.0`，安装于
Aug 16）；npm registry 最新为 **0.153.3**。

**这不是内容被 cyber 拦截**（prompt 已按历史教训扫过「构造 / 可复现 / 打穿 / 绕过」类
措辞，零命中），是模型在该 CLI 版本上不可用。

**处置**：向用户提了 D-1（甲=升级 / 乙=换模型 / 丙=人审替代），用户选**甲**，
`brew upgrade --cask codex` → 0.153.3，400 解除，复核跑通（见 §十）。

> ⚠️ **这个提问的前提是不完整的，如实登记。** 我查了 `which -a codex`、`npm ls -g`、
> `ls /opt/homebrew/bin/codex*`，都没照到本机 `~/.npm/_npx/` 缓存里**早已存在**的
> `codex-cli 0.153.3`（另一条车道 Z1 先撞上并装了它，用绝对路径直接调即可，
> 零风险、不动共享二进制）。npx 缓存不在 PATH 上，所以我的三条查法一条也照不到它。
> **结果是用户在缺一个选项的前提下做了决定。** 升级本身没出问题（反而让全批口径统一，
> 实测另一条车道的 codex 进程也已在用 0.153.3），但代价是 brew **purge 了 0.147.0**，
> 回退需重新下载指定版本。
> **方法论教训**：查「本机有没有别的 X」时，只查 PATH + 包管理器不够——
> `~/.npm/_npx/` / pipx / Caskroom / node_modules 全在 PATH 之外。**漏查 ≠ 不存在。**

---

## 本卡未证明什么

1. **未跑 CI。** 全部验证只在本机（macOS / lefthook 2.1.6 / ruff 0.15.9 / Python 3.14.4）。
   CI 上是否装了 ruff、走的哪份配置，本卡没有查证。
2. **86 个重排文件里，只有 5 个被真正执行过**（见 §九 末尾：`check-openapi-drift.py`
   + `scripts/daemon/tests/` 的 48 条测试及其 3 个被测模块）。**其余 81 个只有
   `py_compile` 级证据**（能编译 ≠ 能跑）。`scripts/daily_review_*.py` 一族有对外推送
   副作用，刻意没执行。
3. **86 个重排文件未逐行人审。** 依据是「`ruff format` 是确定性格式化器」这一属性 +
   `py_compile` 对账，不是逐行阅读。
4. **`mutant-residue-scan` 不检测不带标记的残留。** 这是设计上的已知空洞，X7-A 的
   `_s.exit(9)` 就属于抓不到的那一类；唯一可靠锚点仍是全文件 sha 基线。
5. **未证明该门在 `parallel: true` 下的行为。** 本 hook 是 `parallel: false`（X8 定的）；
   临时目录已改 `mktemp -d`（天然唯一），但并发场景未实测。
6. **未证明排除名单足够窄。** `_bmad-output/*` 是整目录放行；若将来有人把生产代码放进
   该目录，门对它失效。
7. **未修那两个查出来的真缺陷**（`api-reality-dashboard.py` 语法错、
   `validate-source-citations.py` F821），只登记。
8. **未验证 `line-length` 从 88 改到 120 对 `backend/` 之外、且不受 lint 门覆盖的
   其余 94 个 tracked `.py` 的影响**——它们不进 glob，但有人手动跑 `ruff` 时会看到不同结果。
9. **未跑任何变异 harness**（卡文硬边界禁止）。因此「这道新门本身有多强」没有变异证据，
   只有上面那 12 条回归 + 验伪锚。
10. **本门扫不到 OpenAPI 快照块随后 staged 的文件。** lefthook 2.1.6 按命令名字母序执行，
    本块在那两个块**之前**跑；它们之后 `git add` 的 `backend/openapi.json` 不在扫描面内
    （该文件由 `app.openapi()` 机器生成，其源头 `backend/app/**` 本身在扫描面内）。
    实测加 `priority:` 会把本块排到**最前**而非最后，故在不动同级块的前提下无法修，已登台账。
11. **只在 lefthook 2.1.6 上验过，而仓库 `package-lock.json` 锁的是 1.13.6。**（Codex 指出）
    本机 git hook 走的是 homebrew 2.1.6，但走标准 `npm install` 路径的人拿到的是 1.13.6，
    **glob 语义与命令排序在该版本下均未验证**。
12. **glob 的过宽面未逐项验证。**（Codex 指出）2.1.6 的引擎**忽略大小写**，且
    `{backend,src,scripts}/*.py` 会匹配这三个根下**任何**层级的 staged `.py`，包括隐藏目录、
    vendor、fixture。本卡只跑了 2 个阴性对照，不足以枚举所有边界。
13. **sha 基线只能证明「跑完与跑前一致」，不能证明「跑前已干净」。**（Codex 指出，采纳）
    本卡对 `g32b` / `send_bark.py` 的还原验证属这一类。
14. **X7-A 那段「三裁判全绿 + grep = 0 全没抓到」是转述，不是本卡的独立证据。**
    （Codex 指出）它来自台账与源码注释，本卡没有当轮日志。

---

## 台账待登记条目

> 台账只由主 session 写入，本卡不改。以下为建议登记内容。

| # | 条目 | 建议归属 |
|---|---|---|
| 1 | **`scripts/` 的 lint 规则集仍为空**：本卡只扩了「语法 + 格式」门。建议新增 `scripts/ruff.toml`，对齐 `backend/ruff.toml` 的必错级 `select = ["E9","F63","F7","F82"]`。实测存量阻力 = **1 条 F821**（`validate-source-citations.py`，格式化后位于 `:392`）+ 21~24 条 `invalid-syntax`（全在下面第 2 条那个文件里） | 新卡（小） |
| 2 | **`scripts/spec-tools/api-reality-dashboard.py` 真语法错误**：L120 在 f-string 替换字段里用反斜杠转义，Python 3.14 `py_compile` rc=1，脚本**当前无法运行**。因此未被 `ruff format` 覆盖。修复需先决定该行预期输出 | 新卡（小） |
| 3 | **`scripts/validate-source-citations.py` F821**：`generate_report()` 的多行 f-string 里有 `{technology}`，调用即 NameError。疑似应写 `{{technology}}`。⚠️ 别写死行号——它已被本卡 commit-2 的重排从 402 推到 **392**，任何后续重排还会推 | 与第 1 条合并 |
| 4 | ~~`backend/ruff.toml` 的 py39 已失真~~ —— **本卡自我更正：这条不成立**。py39 与根 `pyproject.toml:6` 的 `requires-python = ">=3.9"` 一致，是仓库声明的**支持下限**，不是"实际解释器版本"。真正的口径问题是：CI 用 3.11（`api-spec-sync.yml`）与 3.12（另两个 workflow）执行 `scripts/`，本机 venv 是 3.14——**声明下限 3.9 是否仍要维持**是个产品决定，不是配置 bug | 需用户/主 session 拍板，非 bug |
| 5 | **根 `ruff.toml` 的 `line-length` 由缺省 88 显式改为 120**（口径统一），影响 `backend/` 之外全部 tracked `.py` 的手动 `ruff` 结果。若主 session 不认可，回滚 = 删该行 + 重跑 `ruff format` | 本卡裁决点 |
| 6 | **`codex` CLI 已从 0.147.0 升级到 0.153.3**（用户 2026-09-05 裁 D-1 甲），`gpt-6-astra` 的 HTTP 400 解除。⚠️ brew 在升级时 **purge 了 0.147.0**，Caskroom 旧目录已不存在，回退需重新下载指定版本。⇒ **第十一批其余 6 条车道现在可直接重跑各自的 Codex 轮次**（Z1-A 的 (f)(g) 亦可补） | **已处置，批级周知** |
| 7 | 台账 §X5-B「`daily_review_pick.py` 33 处」**经实测确认准确**（@88 口径），本卡已清零，可标已处置 | 台账维护 |
| 8 | **`mutant-residue-scan` 想真正排到最后，只能改命令名的字母序**（如加 `zz-` 前缀）。实测 lefthook 2.1.6 的 `priority:` 会把它排到**最前**——带 priority 的命令整体先于不带的，不存在"排到最后"的 priority 值。本卡选择改窄声明而非改名（改名会波及 `--command` 引用与文档） | 新卡（微） |
| 9 | **仓库 `package-lock.json:1490` 锁的是 lefthook 1.13.6，而本机 git hook 跑的是 homebrew 2.1.6**（Codex 指出）。本卡的 glob 矩阵与命令排序**只在 2.1.6 上验过**。走标准 `npm install` 路径的人/CI 拿到的是 1.13.6，语义可能不同 → 要么统一版本，要么在 1.13.6 上补同一份矩阵证据 | 新卡（小），跨车道 |
| 10 | **`codex` CLI 已升到 0.153.3 且 brew 已 purge 0.147.0**——本机不再有旧版可原地回退。若后续发现 0.153.3 有行为回归，需重新下载指定版本 | 环境记录 |

---

## 待你裁决

**D-1（批级）Codex 复核路线 —— ✅ 已裁已执行。** 用户 2026-09-05 选**甲**：
`brew upgrade --cask codex` → **0.147.0 → 0.153.3**，`gpt-6-astra` 的 HTTP 400 解除，
本卡按你 09-05 的裁定用 `-m gpt-6-astra -c model_reasoning_effort="ultra"` 跑完一轮。

> 一处**自我更正**：我在提问时说「可回退，`Caskroom/codex/0.147.0` 仍在」——brew 实际
> 在升级时打印了 `Purging files for version 0.147.0`，旧目录**已被删除**。回退需重新
> 下载指定版本，不是原地切 symlink。提问时的那句话是错的。

**D-2（本卡）根 `ruff.toml` 的 `line-length = 120` 是否保留？** 见台账条目 5。默认保留。
这是卡文没点名、由我判断加进 commit-1 的一项，理由与代价写在 §二 末尾的引用块里。

---

*生成时间 2026-09-05 · 车道 `card/z7-tool` · commit `1ffd6d36` + `b20fe550` + `870e52b3`
（第三个为 Codex round-1 整改）· 未 push*
