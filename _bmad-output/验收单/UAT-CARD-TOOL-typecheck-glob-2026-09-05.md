# UAT — CARD-TOOL-typecheck-glob「D-1 丙落地：python-typecheck glob 收窄到 backend/app」

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-typecheck-glob]`
> 车道 `card/z7-tool`（本车道第 2 卡；前置 Y4-A / CARD-RV-E 已独立 commit，起点 HEAD `4cc4824c`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-B.md`
> 2h；代码 commit `64498c26`（唯一代码提交，只改 `lefthook.yml`）；Codex 1 轮

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化（提交代码前的类型检查只看后端应用目录，
不再因为测试文件里的旧问题把提交拦下；主仓那台机器上这项检查依旧显示「跳过」，
不是「通过」）。**

系统里有一道"交作业前的检查"，会在每次提交代码时挑一遍类型错误。这道检查在上一批
被装好之后，出现了一个谁都没料到的副作用：**19 次提交里有 18 次被它拦住**，而拦住的
理由几乎都跟这次要提交的改动没关系——报错来自测试目录里堆了很久的旧问题。

原因不在检查工具本身，在于**它被喂了多少文件**。这道检查有一份配置，写明"只看这三个
目录"；但调用它的那行命令又把"这次要提交的文件"直接列在了后面。工具的规矩是：
**一旦你在命令里点名了文件，那份配置里的目录清单就作废**。于是配置上写着 304 个文件，
实际每次都可能拿 backend 下 844 个文件（其中 493 个是测试文件）去检查。

这张卡按你的裁定（D-1 选丙）把命令这一侧收窄到**只挑后端应用目录**（263 个文件），
让它重新落回配置声明的范围之内。测试目录的旧账**没有清**，只是不再由这道门来拦——
清账是另一张卡的事。

**有两点必须分开说，不能合成一句**：

- 在**你的主仓库**上，这道检查所依赖的工具至今没有安装，所以它一直显示"跳过"。
  这次收窄**不会**让它开始运行——主仓上的显示仍然是"跳过"，而"跳过"不等于"通过"。
- 只有在**开发用的临时工作树**上（那里借用了一份装了该工具的环境），这道检查才真正
  运行。本卡自己的这次提交就是在那种树上做的，运行记录已存档。

**这次没有声称任何文件的类型是对的。** 后端应用目录里原有的报错一条没修，测试目录的
旧账也一条没清。改的只是"这道门该看哪些文件"。

你不需要做任何事。

---

## 4-A 技术验收

### 证据索引（协议 §2.2：本单的每个数字都指向下面某个存档，不自述）

| 存档（`_bmad-output/审查/evidence-typecheck-glob/`） | 内容 | 末行/判读 |
|---|---|---|
| `judge1-counts-20260905T173653.txt` | 裁判 1：`git ls-files` 全部实数 | `rc=0` |
| `judge2-env-20260905T173657.txt` | 裁判 2：lefthook 版本 / 两树 pyright / pyrightconfig 原文 | 主干 `pyright: No such file` `rc=1` |
| `probe-HIT-backend_app_main.py.txt` | 探针①根级命中 | `rc=1`（pyright 1 err，门真跑） |
| `probe-HIT-backend_app_mcp_server.py.txt` | 探针②1 级命中 | `rc=0`（0 err 6 warn，门真跑） |
| `probe-HIT-backend_app_api_v1_endpoints_health.py.txt` | 探针③3 级命中 | `rc=1`（4 err，门真跑） |
| `probe-NEG-backend_mutmut_config.py.txt` | 负控①backend 一级文件 | `(skip) no files for inspection` `rc=0` |
| `probe-NEG-backend_tests_conftest.py.txt` | 负控②测试目录文件 | `(skip) no files for inspection` `rc=0` |
| `probe-OLDGLOB-flip.txt` | **承重**：新旧 glob 对撞（含作者自查勘误） | 旧 glob 下 conftest.py `exit status 1` |
| `judge456-postedit-20260905T174156.txt` | 裁判 4/5/6：改后未提交态全量核对 | `rc=0` |
| `judge7-commit-hook-20260905T174323.txt` | 裁判 7：提交期 hook 全程原始输出 | `commit_rc=0` |
| `judge-postcommit-20260905T174344.txt` | 提交后复核（绑定 `4cc4824c..64498c26`） | `diff_rc=0` |
| `judge8-codex-r1-remeasure-*.txt` | **Codex round-1 整改**：旧 glob 真实可达面直接计数 + SKIP 解析链 + 主干 PATH 实测 | `844`；`command -v pyright` rc=1 |
| `judge9-equivalence-*.txt` | **失绑等价性**：审后注释改动与 `64498c26` 的行为面等价证明 | run 块 / 剥注释后 sha 两版相同 |
| `codex-review-CARD-TOOL-typecheck-glob.md` | Codex round-1 正文（6134 字节） | 首部按协议 §2.1 |

### (a) glob 定稿 + 五档探针（scratch worktree，禁在车道/主干造 commit）

探针环境：`git worktree add --detach <scratchpad>/y4b-probe-173743 HEAD`，内建 `backend/.venv`
**目录级** symlink → `card-v5-lance/backend/.venv`（pyright 1.1.411）；lefthook
`/opt/homebrew/bin/lefthook` 2.1.6；每档 `echo '# probe' >> <f> && git add <f>` →
`lefthook run pre-commit --command python-typecheck --no-auto-install` → `git reset -q HEAD -- <f>
&& git checkout HEAD -- <f>`（每档还原后 `git status --porcelain` 0 行）；收尾
`git worktree remove --force`，`git worktree list` 已无该条。

**命中判据 = 块内 `[Python] Running pyright type check (backend/.venv/bin/pyright)...` 字面出现**
（不是 rc——pyright 对存量报错 rc≠0 属预期）。

| 档 | 文件 | 深度 | 判据字面 | 门 rc | 判定 |
|---|---|---|---|---|---|
| ① | `backend/app/main.py` | 根级（0 层） | 出现 | 1（1 err 2 warn） | 命中 ✅ |
| ② | `backend/app/mcp/server.py` | 1 层 | 出现 | 0（0 err 6 warn） | 命中 ✅ |
| ③ | `backend/app/api/v1/endpoints/health.py` | 3 层 | 出现 | 1（4 err） | 命中 ✅ |
| 负控① | `backend/mutmut_config.py` | backend 一级 | **未出现** | 0 | `(skip) no files for inspection` ✅ |
| 负控② | `backend/tests/conftest.py` | 测试目录 | **未出现** | 0 | `(skip) no files for inspection` ✅ |

**根级 ① 命中 ⇒ (a) 路径成立，不触发 (b) 的两条命令退化**：单 `*` 确实跨任意层级，
X8 矩阵里的"根文件 skip"是花括号子目录 `{api,models,schemas,mcp}` 造成的，不是单星本身。
命令名集合与次序因此完全没动。

#### 承重补强：新旧 glob 对撞（卡文未要求，本卡自加）

只证"新 glob 不命中"是不够的——那与"这些文件本来就不在门内"无法区分。故把 scratch 的
glob 还原为旧值 `{backend,src}/**/*.py` 再跑同两个文件：

| 文件 | 旧 glob | 新 glob | 翻转 |
|---|---|---|---|
| `backend/tests/conftest.py` | **真跑**（`Running pyright` + 块内 `exit status 1`，1 err） | `(skip)` | ✅ 收窄确实改变了可达面 |
| `backend/mutmut_config.py` | `(skip)` | `(skip)` | ➖ 无翻转——旧 glob 本来就漏它，见 (d) |

> ⚠️ **作者自查勘误（已写进 `probe-OLDGLOB-flip.txt` 存档尾部）**：该对照命令把 lefthook
> 输出接进了 `| head -30`，而取 rc 用的 `${PIPESTATUS[0]:-$?}` 是 **bash** 语法，本机 shell
> 为 zsh（对应变量是小写 `pipestatus` 且下标从 1 起）⇒ 取值为空、回落到 `$?` = **head 的 rc**。
> 该文件里那两行 `rc=0` **不是 lefthook 的退出码**，真值以块内 lefthook 自打的
> `exit status 1` / `(skip)` 为准。五份主 transcript 无管道，其 `rc=` 行不受影响。

### (c) 注释实数（全部出自 `judge1-counts-*.txt`，禁写 258/35）

| 量 | 命令 | 实测 |
|---|---|---|
| `backend/app` .py | `git ls-files backend/app \| grep -c '\.py$'` | **263** |
| `src` tracked | `git ls-files src \| wc -l` | **0**（目录不存在 ⇒ 死枝） |
| 仓库根 `tests` .py | `git ls-files tests \| grep -c '\.py$'` | **41** |
| pyrightconfig include 面 | 263 + 0 + 41 | **304** |
| `backend` **目录总量** .py | `git ls-files backend \| grep -c '\.py$'` | **846** |
| 其中 backend **一级** .py | `git ls-files backend \| grep -cE '^backend/[^/]+\.py$'` | **2** |
| **旧 glob 真实可达面** | `git ls-files backend \| grep '\.py$' \| grep -vcE '^backend/[^/]+\.py$'` | **844** |
| `backend/tests` .py | `git ls-files backend/tests \| grep -c '\.py$'` | **493** |
| `backend/app` 根级 .py | — | 5（`__init__` / `config` / `dependencies` / `main` / `security`） |

> ⚠️ **846 是目录总量，不是旧 glob 的匹配量**（差 2）。注释初版把两者混为一谈，被 Codex
> round-1 抓到；844 已由 `judge8-codex-r1-remeasure-*.txt` **直接计数**（`grep -vc`），
> 与 846−2 的推算互相印证，不是单靠减法。详见 §Codex 复核。

**机制（写进注释）**：`lefthook.yml` 的 run 块把 `{staged_files}` 当**位置实参**传给 pyright，
位置实参**取代** `pyrightconfig.json` 的 `include` 而非与之取交集 ⇒ 改前门的真实可达面 =
**844** 个 .py（含 backend/tests 493），**大于** include 面 304。这就是第十一批
CARD-TOOL-pyright 台账记的 18/19 ≈ 95% 提交被拦的机制。收窄后门面 = 263 ⊂ include 面 304。
（上述计数均为 **tracked `.py`**，不等于 pyright 实际分析的文件数——它还会拉入被 import 的文件。）

**注释新增行数 N = 43**（`git diff --numstat 4cc4824c -- lefthook.yml` = `44 1`，其中 1 行是
被替换的 glob 行；commit `64498c26` 时为 36，Codex 整改又 +7）。**行锚偏移通报 Y4-C / Y4-D
以下表为准**：

| 锚 | 改前（`4cc4824c`） | 改后（最终） |
|---|---|---|
| `mutant-residue-scan:`（Y4-C 面） | 286 | **329** |
| `pre-push:`（Y4-D 面） | 383 | **426** |
| `python-typecheck:` | 146 | 189 |
| glob 行 | 147 | **190** |

### (d) 死枝登记（有意不收，非疏漏）

1. **`src/`** — 仓库内零 tracked 文件。旧 glob 的 `src` 分支与 `pyrightconfig.json` 的
   `"src"` 条目**都是死枝**；本卡收窄时一并去掉 glob 侧的死枝，`pyrightconfig.json` 侧
   按硬边界一字不改（留给另卡）。
2. **`backend/mutmut_config.py` / `backend/start_server.py`** — backend 一级的 2 个 `.py`
   不在 `backend/app` 下。**旧 glob 本来就漏掉它们**（`**` 要求至少跨一级，已由负控①
   在旧 glob 下复现为 `(skip)`），本卡不借收窄之机扩面。

### (e) 主干 SKIP 与车道真跑（两句并列，禁合并）

**先说清 SKIP 的真实条件**（Codex round-1 第 3 问整改）：run 块的解析链是
`backend/.venv/bin/pyright` → `command -v pyright`（PATH）→ 空，**两个入口都解析不到**才走
SKIP。所以"主仓 venv 没有 ⇒ SKIP"这句话**条件不足**，必须把 PATH 那一侧也算上。同理
"只有 symlink 到共享 venv 的树才真跑"按字面**不成立**——任何一侧装上 pyright 都会真跑。

| 树 | `backend/.venv` 内 | PATH 上 | 本门实际行为 |
|---|---|---|---|
| **主干** `canvas-learning-system/backend/.venv` | **无**（`ls` → `No such file or directory`，rc=1） | **无**（`command -v pyright` rc=1，`judge8-*.txt`） | 两入口皆空 ⇒ 走 SKIP 分支（`[Python] SKIP: pyright not installed` + `SKIP: typecheck did NOT run -- this is NOT a pass`），**收窄 glob 后仍不真跑** |
| **车道** `card-z7-tool/backend/.venv` | symlink → `card-v5-lance/backend/.venv`，**有** 1.1.411 | （未走到） | 命中第一个入口 ⇒ 真跑（本卡五档探针即在此环境） |

> 这是**当前环境的实测**，不是 glob 决定的。往主仓 venv 或 PATH 任一侧装上 pyright，
> 主干上这道门就会开始真跑——本卡不做这件事（用户裁定 D-1 丙：主干 venv 暂不装）。
> PATH 一侧的实测取自本卡运行时的交互 shell；hook 实际执行时的 PATH 由 git 调用链决定，
> 本卡**未**在主仓上真实触发过一次 commit 来验证，故第 2 条"未证明"如实保留。

> **本卡不声称任何文件的类型是对的。** `pyrightconfig.json` 注释里的 592 err 是**整个
> include 面 304 文件**的数（Z7-B 在 pythonVersion 3.11 下实测），不是 `backend/app` 单独的数，
> 本卡没有单独测过。"类型已检查 / 已通过 / 收窄并通过"一律不成立。

### (f) `pyrightconfig.json` 一字不改

`git diff HEAD~1 HEAD -- pyrightconfig.json` → **空**（`judge-postcommit-*.txt`）。

### (g) commit 只改 lefthook.yml + hook 真跑（无 LEFTHOOK_EXCLUDE）

`git diff HEAD~1 HEAD --stat -- . ':(exclude)_bmad-output'` → `lefthook.yml | 38 +++-`，
**1 file changed**（`':(exclude)…'` 写法，非 zsh 会吞的 `':!…'`）。

提交期 lefthook 摘要（原文见 `judge7-commit-hook-*.txt`，`commit_rc=0`）：

| hook | command | 结果 |
|---|---|---|
| pre-commit | `cypher-vault-filter-lint` | `(skip) no matching staged files` |
| pre-commit | `ghost-files` | ✔️ `[Ghost Files] No untracked docs found.` |
| pre-commit | `mutant-residue-scan` | ✔️ `[Mutant-Scan] OK (staged additions carry no mutation marker).` |
| pre-commit | `python-lint` | `(skip) no files for inspection` |
| pre-commit | **`python-typecheck`** | `(skip) no files for inspection` — **正常**：本卡改的是 `.yml`，不在其 glob 内 |
| pre-commit | `readme-claims-lint` | `(skip) no matching staged files` |
| pre-commit | `spec-sync-flat` / `spec-sync-root` | `(skip) no matching staged files` |
| commit-msg | `commitlint` | ✔️ `found 0 problems, 1 warnings`（`subject-case` 为 level 1 警告，非阻断） |
| commit-msg | `spec-reference` | ✔️ `[Spec Ref] OK.` |

`header` 92 字符（≤100，commitlint `header-max-length` 100）；body 最长行 ≤100 字符
（按 JS `.length` 同口径的 Python 码点计——`awk length()` 在本 locale 下按**字节**，
不是 commitlint 的口径）。

### 硬边界自查

| 边界 | 判据 | 实测 |
|---|---|---|
| 命令名集合与次序不变 | `diff <(git show HEAD~1:lefthook.yml \| grep -E '^    [a-z-]+:$') <(...)` | `diff_rc=0`（空） |
| 未加 `priority` | `grep -n 'priority:'` | 仅注释里提到该词，**无键** |
| 禁改块未动 | `git diff HEAD~1 HEAD -U0` hunk | 仅 `@@ -145,0 +146,36 @@` 与 `@@ -147 +183 @@` 两处 |
| 未装/未升 pyright | 共享 venv 版本 | 1.1.411（改前=改后，本卡零安装动作） |
| 未连 7691/7687 | 本卡零 pytest、零 DB 调用 | ✅ |
| scratch 清理 | `git worktree list` | 已无 `y4b-probe-*` |
| `*.stderr*` 不入库 | `.gitignore:257-261` | ✅ |
| 台账未改 | `git diff HEAD~1 HEAD --name-only` | 无台账文件 |

---

## Codex 复核（round-1）

存档 `_bmad-output/审查/codex-review-CARD-TOOL-typecheck-glob.md`（首部按协议 §2.1，
`gpt-6-astra` / `ultra` / `codex-cli 0.153.3`，绑定 `4cc4824c..64498c26`）。
总裁定：**第 1 问成立；第 2、3、4 问部分成立。**

| # | Codex 结论 | 本卡处置 |
|---|---|---|
| 1 | glob 语义**成立**：三档 HIT 均有 `Running pyright` + 实际诊断（"证据不止启动提示"），两档 NEG 第 12 行 `(skip)`，新旧对照有效，**作者自查勘误也正确** | 接受，无改动 |
| 2 | **数字范围误用（承重）**：`:151` 称"旧 glob 可达面 = backend 全部 846"，与同文件死枝登记、与 NEG① 旧 glob 实测**直接冲突**；应为 **844** | **接受并整改**（见下） |
| 2' | `18/19 ≈ 94.74%`，写 `94%` 不精确；`258/35` 在读取面内无佐证 | 接受：改为「台账记 18/19 ≈ 95%」；258/35 保留但已标明是过期数、不要照抄 |
| 2'' | `304` 是本次 tracked 文件计数，非配置直接记载的"检查文件数" | 接受：注释补「均为 tracked `.py` 计数，不等于 pyright 实际分析的文件数」 |
| 3 | 无假绿措辞（`:176` 明言不声称类型正确）；但**两处条件写得过强**：SKIP 需 venv **与** PATH 皆无；"只有 symlink 才真跑"字面不成立 | **接受并整改**（注释与本单 (e) 段均已补条件链） |
| 4 | 改动面受限成立（命令名集合/顺序不变、无 `priority`、run 未改、`pyrightconfig.json` 未改）；但**整个 commit 不止一个文件**——另有 9 份证据文件 | 接受措辞：准确说法是「**只修改一个既有配置文件，并新增九份证据文件**」；本单 (g) 用的判据是 `':(exclude)_bmad-output'` 下的**代码面**，与该说法不冲突，已在此写明 |
| 4' | `start_server.py` 无独立探针，其被旧 glob 漏掉属同层级规则推论 | 如实接受：`judge8` 已补**直接计数**（`grep -vcE '^backend/[^/]+\.py$'` = 844），但确实**未**为该文件单跑探针 |

### ⚠️ 审后改动（失绑登记，协议 §1 / §四）

Codex 第 2、3 问是**真缺陷**，且第 2 问是本卡核心目标（钉实数）的自相矛盾，故审后修正。
按协议 §四「审后再改 lefthook.yml = 失绑须登记」如实登记；按协议 §1「纯注释尾巴由主
session 逐行核后可判等价」提供下列判据（`judge9-equivalence-*.txt`）：

| 等价性判据 | 结果 |
|---|---|
| 全部 `+`/`-` 行是否都是注释行（`^\s*#`） | ✅ 无非注释改动 |
| glob 行逐字节 | ✅ 审 SHA 与最终版同为 `      glob: "backend/app/*.py"` |
| `python-typecheck` **run 块** sha256 | ✅ `6af93378…` 两版相同 |
| **剥掉全部注释行后整文件** sha256 | ✅ `d6ebf8bd…` 两版相同 ⇒ **行为面逐字节等价** |
| 命令名集合与顺序 | ✅ diff 空 |
| YAML 可解析 + glob 值 | ✅ `backend/app/*.py` |

> 两条判据合起来才严密：「剥注释后 sha 相同」单独用会漏掉 run 块**内部**的 shell 注释
> （它们也以 `#` 开头会被一并剥掉），故另配「run 块整段 sha」逐字节兜住那一面。

**结论**：审后改动**仅为注释文本**，门的行为面与 `64498c26` 逐字节等价；Codex round-1 对
行为面的四项结论（glob 语义 / 改动面受限 / 无假绿 / pyrightconfig 未改）**不受影响**，
被推翻的两点正是本次整改所修。轮次仍计 1 轮。

---

## 本卡未证明什么

1. **未证明 `backend/app` 这 263 个文件的类型是正确的。** 存量报错一条没修；探针里
   `main.py` 1 err、`health.py` 4 err 就是活证据。`pyrightconfig.json` 注释里的 592 err
   是整个 include 面 304 文件的数，不是 backend/app 单独的数，本卡没有单独测过。
2. **未让主干上的这道门开始运行。** 主仓 `backend/.venv` 无 pyright，改 glob 后它仍走
   honest-SKIP 分支。"主干 SKIP" ≠ "主干通过"。
3. **未接 CI。** 本卡只动 lefthook 本地 hook，`.github/workflows/**` 一字未改；CI 上
   pyright 是否跑、跑什么面，本卡没有测过。
4. **未清 `backend/tests` 493 个文件的类型债。** 收窄只是让这道门不再拦它们，债还在，
   属另卡。
5. **`backend/mutmut_config.py` / `backend/start_server.py` 不在门内**（旧 glob 也不在）。
6. **探针只证 glob 命中/不命中，不证 pyright 的结论。** 判据是 `Running pyright` 字面出现，
   pyright 报的那些 err/warn 本卡未逐条核实。
7. **未证明收窄后 94% 拦截率会降到多少。** 本卡没有做提交样本重放；机制成立不等于
   实测比例已知。

## 台账待登记条目

1. **Z7-B 行 D-1 丙**：已落地 `64498c26`（glob → 单条 `backend/app/*.py`，注释 +36 行）。
2. **勘误**：`258 / 0 / 35` → **`263 / 0 / 41` = include 面 304**；第十一批手册旧数作废。
   同时登记 `backend` **目录总量 846** / **旧 glob 真实可达面 844**（差 2 = backend 一级的
   `mutmut_config.py` + `start_server.py`，`**` 要求跨一级）/ `backend/tests` 493。
   ⚠️ **846 ≠ 844，别当同一个数用**——本卡注释初版混用过一次，由 Codex round-1 抓出。
3. **「pyright 装进主干 venv」仍悬**：用户裁定暂不装 ⇒ 主干门继续 honest-SKIP。此条不关闭。
4. **`backend/tests` 类型债卡待排**（493 文件；本卡只是移出门面，未清账）。
5. **行锚偏移 +43**（注意：非 +36——Codex 整改又加了 7 行注释，**以此为准**）：
   `mutant-residue-scan` 286→**329**（Y4-C 面）、`pre-push` 383→**426**（Y4-D 面）、
   `python-typecheck` 146→**189**、glob 147→**190**。四个数均 `grep -n` 实测，非推算。
6. **`pyrightconfig.json` 的 `"src"` 死枝未清**（本卡硬边界禁改该文件）——建议与 (d) 一并
   交给动 pyrightconfig 的那张卡。
7. **`.github/workflows` 侧的 pyright 口径未核**（本卡未证明第 3 条）。
8. **台账 Z7-B 行「门可达面 843 文件」需更新**：843 是 Z7-B 当时（第十一批）在旧主干上的
   值；本卡在 `4cc4824c` 上实测 backend 目录总量 **846**、**旧 glob 真实可达面 844**。
   台账那个位置说的是"门可达面"，故应更新为 **844**（并注明测量 SHA）。同行的 `2089 err`
   属旧主干快照，本卡未重测，不追认。（引用的历史数字会随主干前进过期——每次都要写清
   测量时的 SHA。）「include 面 304 / 592 err」与本卡实测一致。
9. **审后失绑登记**：Codex round-1 绑定 `64498c26`，其后本卡按其第 2/3 问**修改了
   `lefthook.yml` 的注释文本**（commit 见收尾提交）。等价性判据见
   `judge9-equivalence-*.txt`：run 块 sha 与"剥掉全部注释后整文件 sha"两版均相同 ⇒
   行为面逐字节等价，请主 session 按协议 §1 逐行核后判等价。轮次仍计 1 轮。
10. **`backend/start_server.py` 无独立探针**（Codex 4' 指出）：它被旧 glob 漏掉是同层级
   规则推论 + `judge8` 的直接计数（844），未单独跑过一档探针。若后续要把 backend 一级
   文件纳入门面，需先补该探针。
