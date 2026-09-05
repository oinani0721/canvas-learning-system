# UAT — CARD-TOOL-typecheck-glob「D-1 丙落地：python-typecheck glob 收窄到 backend/app」

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-typecheck-glob]`
> 车道 `card/z7-tool`（本车道第 2 卡；前置 Y4-A / CARD-RV-E 已独立 commit，起点 HEAD `4cc4824c`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-B.md`
> 2h；代码面**只有 `lefthook.yml`**，三个 commit：`64498c26`（门定稿：glob + 注释）、
> `bdf15fba`（Codex round-1 整改，纯注释）、本次收尾（内部复核整改，纯注释 + 存档）。
> 后两次对 `lefthook.yml` 的改动**与 `64498c26` 结构等价**（判据见 §等价性）。
> 外审：Codex round-1（1 轮）+ 本卡内部对抗性复核（17 agent，只读）

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化（提交代码前的类型检查只看后端应用目录，
不再因为测试文件里的旧问题把提交拦下；主仓那台机器上这项检查依旧显示「跳过」，
不是「通过」）。**

系统里有一道"交作业前的检查"，会在每次提交代码时挑一遍类型错误。这道检查在上一批
被装好之后，出现了一个谁都没料到的副作用：**19 次提交里有 18 次被它拦住**，而拦住的
理由几乎都跟这次要提交的改动没关系——报错来自测试文件里堆了很久的旧问题。
（"几乎都没关系"这句是**推断**，本卡没有逐条翻看过那 18 次的报错内容。）

原因不在检查工具本身，在于**它被喂了哪些文件**。这道检查有一份配置，写明"只看这三个
地方"；但调用它的那行命令又把"这次要提交的文件"直接列在了后面。工具的规矩是：
**一旦你在命令里点名了文件，那份配置里的清单就作废**。于是配置上写着 304 个文件的范围，
实际可以送进来的却有 844 个（其中 493 个是测试文件）——每次真正检查的只是你这次提交的
那几个文件，但它们可以从这 844 个里来，包括那些你根本没碰的测试文件。

这张卡按你的裁定（D-1 选丙）把"能送进来的文件"收窄到**只有后端应用目录**（263 个），
让它重新落回配置声明的范围之内。测试文件的旧账**没有清**，只是不再由这道门来拦——
清账是另一张卡的事。

**有两点必须分开说，不能合成一句**：

- 在**你的主仓库**上，这道检查依赖的工具至今没有安装（它会找的两个位置都没有），
  所以它一直显示"跳过"。这次收窄**不会**让它开始运行——主仓上仍然显示"跳过"，
  而"跳过"不等于"通过"。
- 装了那个工具的机器上，这道检查**会**真正运行——目前只有开发用的临时工作树借用了
  一份装好的环境，本卡自己的提交就是在那种树上做的，运行记录已存档。但**装了工具**
  只是条件之一：还得这次提交的文件落在"这道门该看的范围"里，两个条件同时成立才会跑。
  本卡自己的三次提交改的都是配置和文档，不在那个范围里，所以即使在装了工具的树上，
  这道检查照样显示"跳过"。

**这次没有声称任何文件的类型是对的。** 后端应用目录里原有的报错一条没修，测试文件的
旧账也一条没清。改的只是"这道门该看哪些文件"。

你不需要做任何事。

---

## 4-A 技术验收

### 证据索引（协议 §2.2：本单的每个数字都指向下面某个存档，不自述）

| 存档（`_bmad-output/审查/evidence-typecheck-glob/`） | 内容 | 判读 |
|---|---|---|
| `judge1-counts-20260905T173653.txt` | 裁判 1：`git ls-files` 计数（263 / 0 / 41 / 846 / 493 / 一级 2 文件名 / 根级 5 文件名） | `rc=0` |
| `judge2-env-20260905T173657.txt` | 裁判 2：lefthook 版本 / 两树 pyright / pyrightconfig 原文 | 主干 `pyright: No such file` `rc=1` |
| `probe-HIT-backend_app_main.py.txt` | 探针①根级命中（新 glob） | `rc=1`（1 err，门真跑） |
| `probe-HIT-backend_app_mcp_server.py.txt` | 探针②1 级命中（新 glob） | `rc=0`（0 err 6 warn，门真跑） |
| `probe-HIT-backend_app_api_v1_endpoints_health.py.txt` | 探针③3 级命中（新 glob） | `rc=1`（4 err，门真跑） |
| `probe-NEG-backend_mutmut_config.py.txt` | 负控①（v1，**判据不足**，见 §内部复核 F3） | `(skip) no files for inspection` |
| `probe-NEG-backend_tests_conftest.py.txt` | 负控②（v1，同上） | `(skip) no files for inspection` |
| `probe-OLDGLOB-flip.txt` | **承重**：新旧 glob 翻转对照（含作者自查勘误） | 旧 glob 下 conftest.py `exit status 1` |
| `judge456-postedit-20260905T174156.txt` | 裁判 4/5/6：改后未提交态核对 | `rc=0` |
| `judge7-commit-hook-20260905T174323.txt` | 裁判 7：`64498c26` 提交期 hook 全程原文 | 末尾 `[card/z7-tool 64498c26]`（见 §(g) 勘误） |
| `judge-postcommit-20260905T174344.txt` | `4cc4824c..64498c26` 提交后复核 | `diff_rc=0` |
| `judge8-codex-r1-remeasure-*.txt` | Codex r1 整改：844 计数 + SKIP 解析链 + PATH | `844`；`command -v pyright` rc=1 |
| `judge9-equivalence-*.txt` | 失绑等价性 v1（**判据有盲区**，已被 v2 取代，见 §等价性） | run 块 / 剥注释后 sha 相同 |
| `judge10-final-*.txt` | 收尾裁判 + 禁写串逐条判读 | `rc=0` |
| `judge11-commit2-hook-*.txt` | `bdf15fba` 提交期 hook 全程原文 | 末尾 `[card/z7-tool bdf15fba]` |
| `judge12-mechanism-proof-*.txt` | **核心机制直接实证** + Codex 存档字节数 + PATH 原样输出 | `rc=0` |
| `judge13-structural-equiv-*.txt` | **结构等价判据 + 验伪锚**（取代 judge9 三条 sha 判据） | 唯一差异 = glob；验伪锚 ✅ |
| `judge14-negctl-binding-*.txt` | 负控绑定性重测 **v1（作废）**：sed 行号硬编码致 YAML 崩 | 六档全废，正控暴露 |
| `judge14-negctl-binding-v2-*.txt` | 负控绑定性重测 **v2**：2 正控 + 4 负控，每档三行暂存自证 | `FAILED=0` |
| `judge15-final-equiv-*.txt` | 注释批改后结构等价 + 最终行锚实测 | `rc=0` |
| `judge16-commit3-hook-*.txt` | 本次收尾 commit 的 hook 全程原文 + rc | 见文件末行 |
| `_bmad-output/审查/codex-review-CARD-TOOL-typecheck-glob.md` | Codex round-1 正文（**7096 字节**，含协议 §2.1 首部） | 绑定 `4cc4824c..64498c26` |

### (a) glob 定稿 + 探针

探针环境：scratch worktree（`git worktree add --detach`），内建 `backend/.venv` **目录级**
symlink → `card-v5-lance/backend/.venv`（pyright 1.1.411）；`/opt/homebrew/bin/lefthook` 2.1.6；
每档 `echo '# probe' >> <f> && git add <f>` → `lefthook run pre-commit --command
python-typecheck --no-auto-install` → `git reset -q HEAD -- <f> && git checkout HEAD -- <f>`；
两个 scratch worktree 收尾均已 `git worktree remove --force`，`git worktree list` 无残留。

**命中判据 = 块内 `[Python] Running pyright type check (backend/.venv/bin/pyright)...` 字面出现**
（不是 rc——pyright 对存量报错 rc≠0 属预期）。

| 档 | 文件 | 深度 | glob | 判据字面 | 门 rc | 判定 |
|---|---|---|---|---|---|---|
| ① | `backend/app/main.py` | 0 | 新 | 出现 | 1 | 命中 ✅ |
| ② | `backend/app/mcp/server.py` | 1 | 新 | 出现 | 0 | 命中 ✅ |
| ③ | `backend/app/api/v1/endpoints/health.py` | 3 | 新 | 出现 | 1 | 命中 ✅ |
| 翻转 | `backend/tests/conftest.py` | — | **旧** | 出现 | 1（`exit status 1`） | 命中 ✅ |
| 翻转 | `backend/tests/conftest.py` | — | 新 | 未出现 | 0 | 跳过 ✅ |

**根级 ① 命中 ⇒ (a) 路径成立，不触发 (b) 的两条命令退化。**

> ⚠️ **限定（内部复核 F8 整改）**：实测只抽了深度 **0 / 1 / 3** 三档，**深度 2 及更深未测**。
> "单 `*` 跨任意层级"是对这三个样本的**规则归纳**，不是穷举；同理"收窄后门面 = 263"是
> 按该规则对 263 条路径的**外推**，不是逐条枚举。外审 codex-review §1 写下过同一限定
> （"'任意层级'是对此的规则归纳，并非穷举所有深度"），本单初版在 Codex 处置表里把这条
> 限定丢掉了，现补回并同步进 lefthook.yml 注释与"本卡未证明什么"。

#### 负控绑定性（v1 判据不足 → v2 重测，内部复核 F3 整改）

**v1 的缺陷**：lefthook 的 `(skip) no files for inspection` 只表示"交给该命令的文件列表为空"，
`git add` 没生效、暂存区本来就空，都会产生**逐字节相同**的输出；而 v1 的 transcript 里
对暂存只有一个**无标签的裸文件名**，无法自证。⇒ 负控不绑定 glob，844 的实测锚点悬空。

**v2 重测**（`judge14-negctl-binding-v2-*.txt`，`FAILED=0`）：每档显式打印三行暂存自证
（`git diff --cached --name-only` / `git status --porcelain` / `git diff --cached --numstat`），
并在同一轮里放两档**正控**：

| 档 | 文件 | glob | 类型 | 暂存自证 | 结果 |
|---|---|---|---|---|---|
| 1 | `backend/app/main.py` | 新 | **正控** | `M  backend/app/main.py` + `1 0` | 命中 ✅ |
| 2 | `backend/app/main.py` | 旧 | **正控** | 同上 | 命中 ✅ |
| 3 | `backend/mutmut_config.py` | 新 | 负控 | `M  backend/mutmut_config.py` + `1 0` | 跳过 ✅ |
| 4 | `backend/start_server.py` | 新 | 负控 | `M  backend/start_server.py` + `1 0` | 跳过 ✅ |
| 5 | `backend/mutmut_config.py` | **旧** | 负控 | 同上 | 跳过 ✅（证 `**` 要求跨一级） |
| 6 | `backend/start_server.py` | **旧** | 负控 | 同上 | 跳过 ✅（补 Codex 4' 缺档） |

正控排除了"`git add` 没生效"与"配置解析失败"这两种会产生相同 skip 字样的假因 ⇒
第 3-6 档的空列表**只能**来自 glob 过滤，负控绑定成立。

> ⚠️ **v1 的第一次重测（`judge14-negctl-binding-*.txt`，无 v2 后缀）整轮作废并保留存档**：
> 脚本把 `sed` 的行号硬编码成 147，而当时 base 已是 `bdf15fba`、glob 行早漂到 190 ⇒
> 往 `python-lint` 块里插进第二个 `glob:` 键 ⇒ `Error: yaml: unmarshal errors`，六档全没跑成。
> 而当时的判据"`Running pyright` 未出现 = 未命中"把**配置炸了**与**glob 没匹配**判成同一结果。
> **是矩阵里那两档正控（本该命中却报未命中）暴露了它**——若只放负控，这份 transcript 会被
> 当成"负控全部通过"归档。v2 的修法：行号 `grep -n` 动态取 + 每档先验 YAML 可解析 +
> 正控不命中即整轮作废。（本仓既有教训"行号必须实测不能推算"与"判据必须绑定被哪一层
> 拒的"在同一次里各现形一遍。）

### (c) 实数与出处（禁写 258/35）

| 量 | 命令 | 实测 | 出处存档 |
|---|---|---|---|
| `backend/app` .py | `git ls-files backend/app \| grep -c '\.py$'` | **263** | judge1 |
| `src` tracked | `git ls-files src \| wc -l` | **0**（目录不存在 ⇒ 死枝） | judge1 |
| 仓库根 `tests` .py | `git ls-files tests \| grep -c '\.py$'` | **41** | judge1 |
| pyrightconfig include 面 | 263 + 0 + 41 | **304** | judge1 |
| `backend` **目录总量** .py | `git ls-files backend \| grep -c '\.py$'` | **846** | judge1 |
| backend **一级** .py（计数） | `git ls-files backend \| grep -cE '^backend/[^/]+\.py$'` | **2** | **judge8** |
| **旧 glob 可达面** | `git ls-files backend \| grep '\.py$' \| grep -vcE '^backend/[^/]+\.py$'` | **844** | **judge8** |
| `backend/tests` .py | `git ls-files backend/tests \| grep -c '\.py$'` | **493** | judge1 |
| `backend/app` 根级 .py | — | 5 | judge1 |

> ⚠️ **846 是目录总量，不是旧 glob 的匹配量**（差 2）。注释初版把两者混为一谈，被 Codex
> round-1 抓到。
>
> ⚠️ **844 的证据强度，如实说明（内部复核 F4 整改）**：本单初版写"judge8 的直接计数与
> 846−2 **互相印证**"——这句**不成立**。`grep -vc` 与"总数减命中数"是**同一次过滤的两种
> 写法**，对同一集合做同一次划分，把一个数算两遍不构成两条独立证据。而且它数的是
> "backend 下深度 ≥1 的 tracked .py"这个**模型集**，其定义本身就来自待验的那条规则
> （`**` 至少跨一级），不是 lefthook 匹配器对 846 条路径的枚举。Codex 的原话
> （"这是推算，原始记录没有直接计数旧 glob 命中集"）**没有被推翻**。
> 844 目前的实测支撑是：v2 的第 5、6 两档——`mutmut_config.py` 与 `start_server.py`
> 在**旧** glob 下确实被跳过（带正控与三行暂存自证），即 depth-0 侧的两个样本全覆盖；
> 其余 844 条是按规则外推。

**"位置实参取代 include" 的直接实证（内部复核 F9 补，此前只是背景断言）**：
`pyrightconfig.json` 的 `include = ["backend/app","src","tests"]`，**不含 `backend/tests`**；
而 `probe-OLDGLOB-flip.txt` 里 `backend/tests/conftest.py` 在旧 glob 下被 pyright **真的
分析并报出 4 条诊断**。若语义是取交集，它会被 include 排除、零诊断。⇒ 位置实参取代
include 成立（`judge12-mechanism-proof-*.txt`）。这是整张卡价值主张所依赖的那一句，
初版把它当既定背景写进了 Codex prompt，导致外审无法挑战它；现补上独立证据。

**注释净增行数 N = 59**（`git diff --numstat 4cc4824c -- lefthook.yml` = `60 1`，其中 1 行是
被替换的 glob 行）。**行锚偏移通报 Y4-C / Y4-D 以下表为准**（全部 `grep -n` 实测）：

| 锚 | `4cc4824c` | 最终 |
|---|---|---|
| `mutant-residue-scan:`（Y4-C 面） | 286 | **345** |
| `pre-push:`（Y4-D 面） | 383 | **442** |
| `python-typecheck:` | 146 | 205 |
| glob 行 | 147 | **206** |

> ⚠️ **通报口径如实说明（内部复核 F10）**：所谓"通报"目前只以**自述**形式存在于 commit
> body 与本验收单里，没有独立的跨卡交接动作。且前两次自述的数值（+36 / +43）已被本次
> 的 +59 取代，而错值永久留在 git history 里——按 `git log --grep` 找行锚的人会先撞到旧值。
> 实际风险由 Y4-C 卡文自带的防御压住（它要求开工时用 `grep -n` 动态取块头行，不照抄 N）。

### (d) 死枝登记（有意不收，非疏漏）

1. **`src/`** — 仓库内零 tracked 文件。旧 glob 的 `src` 分支与 `pyrightconfig.json` 的
   `"src"` 条目**都是死枝**；本卡去掉 glob 侧的死枝，`pyrightconfig.json` 侧按硬边界一字不改。
2. **`backend/mutmut_config.py` / `backend/start_server.py`** — backend 一级的 2 个 `.py` 不在
   `backend/app` 下。**旧 glob 本来就漏掉它们**（v2 第 5、6 档直接实测，两个文件各一档），
   本卡不借收窄之机扩面。

### (e) 主干 SKIP 与车道真跑（两句并列，禁合并）

**跑不跑取决于两个条件同时成立**（内部复核 F1 整改——本单初版为修 Codex 第 3 问，
写成了"跑不跑取决于工具装没装，不取决于这次改的 glob"，这句**反向过宽**且与本卡核心
结论自相矛盾）：

1. **有暂存文件命中 `glob: "backend/app/*.py"`**——否则 lefthook 在**命令层**就
   `(skip) no files for inspection`，run 脚本一行都不执行；
2. **解析链能找到 pyright**——`backend/.venv/bin/pyright` → `command -v pyright`(PATH) → 空，
   **两个入口都解析不到**才走 SKIP 分支。

| 树 | `backend/.venv` 内 | PATH 上 | 本门实际行为 |
|---|---|---|---|
| **主干** | **无**（`ls` → `No such file or directory`，rc=1，judge2/judge12） | **无**（`command -v pyright` rc=1，judge12 留原样输出） | 两入口皆空 ⇒ SKIP 分支（`SKIP: typecheck did NOT run -- this is NOT a pass`），**收窄 glob 后仍不真跑** |
| **车道** | symlink → `card-v5-lance/backend/.venv`，**有** 1.1.411 | （未走到） | 命中第一个入口 ⇒ 条件 2 满足；条件 1 视本次暂存内容而定 |

> ⚠️ **PATH 判据的作用域，如实声明（内部复核 F6/F7）**：`command -v pyright` 是在**车道树的
> 交互 shell** 里跑的，不是主仓 hook 执行时的 PATH。hook 会先 `source backend/.venv/bin/activate`，
> 车道树里那是含 pyright 的共享 venv。所以这条只能证"本交互 shell 的 PATH 无 pyright"，
> **不能**证"主仓 hook 运行时 PATH 无 pyright"。judge12 已改留 `command -v pyright` 的原样
> 输出与 rc（judge8 那一行是脚本自写的结论句，属自抄字段，已弃用为判据）。
> 主仓上从未真实触发过一次 commit 验证——见"本卡未证明什么"第 2 条。
>
> **本卡不声称任何文件的类型是对的。** `pyrightconfig.json` 注释里的 592 err 是**整个
> include 面 304 文件**的数（Z7-B 在 pythonVersion 3.11 下实测），不是 `backend/app` 单独的数。
> "类型已检查 / 已通过 / 收窄并通过"一律不成立。

### (f) `pyrightconfig.json` 一字不改

`git diff 4cc4824c HEAD -- pyrightconfig.json` → **空**。

### (g) 代码面只有 lefthook.yml + hook 真跑（无 LEFTHOOK_EXCLUDE）

`git diff --stat 4cc4824c HEAD -- . ':(exclude)_bmad-output'` → 仅 `lefthook.yml`
（`':(exclude)…'` 写法，非 zsh 会吞的 `':!…'`）。

> ⚠️ **判据绑 SHA 不绑 HEAD（内部复核 F5 整改）**：本单初版把 commit-1 时刻的数字挂在
> `git diff HEAD~1 HEAD …` 下。HEAD 前进后这条命令含义就变了，照抄复跑得到的输出与文档
> 不符，无法区分"文档过期"与"判据不成立"。所有判据已改绑显式 SHA（`4cc4824c` / `64498c26`
> / `bdf15fba`）。本仓既有教训：判据要绑不变量。

三次提交的 pre-commit 摘要**逐项相同**（原文见 judge7 / judge11 / judge16）：
`cypher-vault-filter-lint (skip)` / `ghost-files ✔️` / `mutant-residue-scan ✔️` /
`python-lint (skip)` / **`python-typecheck (skip) no files for inspection`** /
`readme-claims-lint (skip)` / `spec-sync-flat (skip)` / `spec-sync-root (skip)`；
commit-msg：`commitlint ✔️`（`0 problems, 1 warnings`，`subject-case` 为 level 1）+
`spec-reference ✔️`。三次均**未**使用 `LEFTHOOK_EXCLUDE`。

`python-typecheck` 三次都 skip 是**正常且预期**的：本卡改的是 `.yml` / `.md` / `.txt`，
不在其 glob 内——这同时也是 (e) 条件 1 的一个实例。

> ⚠️ **`commit_rc` 勘误（内部复核 F2）**：本单初版在证据索引里把 judge7 / judge11 的判读
> 写成 `commit_rc=0`，但**那两份存档里没有任何 rc 行**（`grep -c 'rc=' judge7…` = 0）——
> `echo "commit_rc=…"` 写在了 `tee` 管道**之外**，只进了终端没进文件。存档里能自证提交
> 成功的是末尾的 `[card/z7-tool 64498c26]` / `[card/z7-tool bdf15fba]` 行。索引已改为引用
> 该行。本次收尾 commit 的 rc 已改为在 `tee` **内部**捕获（judge16）。
>
> 卡文裁判 7 要求的 `echo rc=$?` 在前两次提交上**没有落盘**，如实登记，不追认。

### 等价性（审后改 lefthook.yml = 失绑，协议 §1 / §四）

Codex round-1 之后本卡两次修改 `lefthook.yml`（均**纯 YAML 注释**）：`bdf15fba` 修 Codex 的
第 2/3 问，本次收尾修内部复核的 F1/F4/F8/F9。按协议 §1「纯注释尾巴由主 session 逐行核后
可判等价」提供判据。

**v1 判据（judge9）已被判定有盲区，弃用为主判据（内部复核 F5）**：

| v1 判据 | 盲区 |
|---|---|
| 全部 `+`/`-` 行都以 `#` 开头 | `run: \|` 块**内部**的 shell 注释也以 `#` 开头，会被误判为"YAML 注释" |
| 剥掉全部 `^\s*#` 行后整文件 sha 相同 | 同上，file-wide 剥离会把**其它 run 块**里的 shell 注释一并剥掉 |
| `python-typecheck` run 块整段 sha 相同 | 只覆盖**这一个** run 块，另外 7 个 pre-commit run 块 + 其它 hook 的 run 块不在内 |

具体反例：改 `python-lint` 块内的 `# Activate backend venv for ruff`（卡文列为"任一字节"
禁改），上述三条判据**全绿**。

**v2 判据：结构等价（`judge13` / `judge15`）** —— `yaml.safe_load` 两版后逐键递归比较。
原理是这条判据的可见性恰好互补：`run: |` 是**字面块标量**，块内 `#` 行是 run 脚本字符串的
一部分，解析器**保留**它；而 YAML 注释（本卡唯一改动的东西）被解析器**丢弃**。

| 判据 | 结果 |
|---|---|
| `4cc4824c` → 最终工作树：解析后差异 | **1 处**，且恰为 `.pre-commit.commands.python-typecheck.glob`（`{backend,src}/**/*.py` → `backend/app/*.py`）✅ |
| `bdf15fba` → 最终工作树：解析后差异 | **0 处**（本轮只改 YAML 注释）✅ |
| **验伪锚**：把 `python-lint` run 块内一行 shell 注释改掉 | 判据报出 `.pre-commit.commands.python-lint.run` 差异 ✅（v1 三条在此全绿=假绿） |
| 命令名集合与顺序（`4cc4824c` vs 最终） | `diff` 空 ✅ |
| `priority` 键 | 解析后递归查找，**零** ✅ |

**结论**：审后改动仅为 YAML 注释文本；门的**有效配置**与 `64498c26` 唯一差异就是那条 glob
（也就是本卡的目标改动本身）。Codex round-1 对行为面的结论不受影响。轮次仍计 **1 轮**。

---

## Codex 复核（round-1）

存档 `_bmad-output/审查/codex-review-CARD-TOOL-typecheck-glob.md`（**7096 字节**，首部按协议
§2.1，`gpt-6-astra` / `ultra` / `codex-cli 0.153.3`，绑定 `4cc4824c..64498c26`）。
总裁定：**第 1 问成立；第 2、3、4 问部分成立。**

| # | Codex 结论 | 本卡处置 |
|---|---|---|
| 1 | glob 语义**成立**：三档 HIT 均有 `Running pyright` + 实际诊断，两档 NEG `(skip)`，新旧对照有效，作者自查勘误也正确。**但同时写明"'任意层级'是规则归纳，并非穷举所有深度"** | 接受，**含该限定**（初版漏抄，已由内部复核 F8 补回注释与本单 §(a)） |
| 2 | **数字范围误用（承重）**：`846` 是目录总量非匹配量，与本卡自己的死枝登记冲突；应为 **844** | 接受并整改（`bdf15fba`） |
| 2' | `18/19 ≈ 94.74%`，写 `94%` 不精确 | 部分接受：改法**第一版写错了**——把渲染值 95% 归属给台账（台账逐字写 94%）。现改为"台账逐字记 18/19 = 94%，精确值 94.7%" |
| 2'' | `304` 是 tracked 文件计数，非配置直接记载的检查文件数 | 接受，注释与本单均已限定 |
| 3 | 无假绿措辞；但 SKIP 需 venv **与** PATH 皆无、"只有 symlink 才真跑"字面不成立 | 接受并整改，但**第一版整改过度**（写成"不取决于 glob"），已由内部复核 F1 改为两条件 AND |
| 4 | 改动面受限成立；但整个 commit 不止一个文件（另有 9 份证据文件） | 接受措辞：准确说法是「只修改一个既有配置文件，并新增若干存档文件」；代码面判据用 `':(exclude)_bmad-output'` |
| 4' | `start_server.py` 无独立探针，属规则推论 | 接受并**补测**：v2 第 4、6 档为该文件在新旧两套 glob 下各跑一档 |

---

## 内部对抗性复核（本卡自发，非卡文要求）

Codex 之后本卡又跑了一轮**只读**多视角复核（17 个 agent：5 个视角找 + 12 个反驳验证，
2,081,221 token）。视角为：数字与出处 / 声称是否比证据宽 / 卡文完成条件逐条对账 /
硬边界 / **判据本身是否可靠**。

**如实说明覆盖度**：共产出 **32 条** finding，脚本设了 CAP=6，只有 **6 条**进了反驳验证，
**26 条未经反驳验证**（脚本已 `log()` 声明并原样返回，未静默截断）。下表是本卡逐条人判后
**采纳并整改**的部分；其余多为重复、措辞偏好或已被反驳。

| # | 来源 | 缺陷 | 处置 |
|---|---|---|---|
| F1 | survivor | 4-B「跑不跑不取决于这次改的 glob」= **我修 Codex 第 3 问时新引入的反向过宽**，与本卡核心结论自相矛盾 | 已改为两条件 AND，并在 §(e) 写明 |
| F2 | O2 | 证据索引写 `commit_rc=0`，但两份存档里**没有 rc 行**（`echo` 在 `tee` 管道外） | 索引改引 `[card/z7-tool <sha>]` 行；本次 rc 在 `tee` 内捕获；卡文裁判 7 的 `echo rc` 前两次未落盘，如实登记 |
| F3 | O3 | 负控判据 `(skip) no files for inspection` **不绑定 glob**（`git add` 没生效会产生相同输出），v1 transcript 无暂存自证 | **v2 重测**：6 档，每档三行暂存自证 + 2 档正控 |
| F4 | O4/O11 | 「844 由直接计数与 846−2 互相印证」= **同一次划分算两遍**，不构成独立证据 | 已撤回该说法，改写 844 的真实证据强度 |
| F5 | O5/O8/O13/O16/O22 | 等价性三条判据对**其它 run 块内的 `#` 行**全部失明；且判据绑 `HEAD~1` 而非 SHA | 改用**结构等价 + 验伪锚**；所有判据改绑显式 SHA |
| F6 | O6/O12 | 「台账记 ≈95%」= 把自己的四舍五入归属给台账（台账写 94%）；「报错与改动无关」是零样本归因 | 注释与本单均改；归因已标注为推断 |
| F7 | O10/O23 | judge8 的 PATH 行是脚本自写结论句（自抄字段），且 PATH 取自车道 shell 非主仓 | judge12 留原样输出 + rc；作用域限定写进 §(e) |
| F8 | O15/O26 | 「单 `*` 跨**任意**层级」是 3 个深度样本的规则归纳，Codex 已写明限定而本单初版丢掉 | 限定补回注释、§(a)、Codex 处置表、未证明清单 |
| F9 | O19 | 核心机制「位置实参取代 include」被当**既定背景**喂给唯一外审，存档里没有判据指认它 | 用**已有存档**补上直接实证（judge12），并写进注释 |
| F10 | O20 | 「通报 Y4-C/Y4-D」只是自述，且错值留在 git history | 如实说明现状 + 指出 Y4-C 卡文自带动态取行锚的防御 |
| F11 | O7/O21 | (c) 小节标题称数字「全部出自 judge1」，但 `2` 与 `844` 出自 judge8；Codex 存档字节数 6134 → 实为 **7096**（补首部前量的） | 表格逐行标出处；字节数已重量 |
| F12 | O9/O18/O24 | 4-B 段出现技术词 `backend` / `glob`（卡文要求零技术词），且「每次拿 844 个文件去检查」不准确 | 已改写 4-B |
| — | O17 | **卡文本身**（Y4-B.md :12、:22）写的是 846，实做按 Codex 改成 844 | 不改卡文（只读），登记为台账条目 |
| — | 未验证 26 条 | 含重复与措辞偏好 | 未逐条处置，如实登记 |

**子代理越权写入对账**：工作流启动前钉了全部 15 份 evidence + `lefthook.yml` +
`pyrightconfig.json` + `commitlint.config.js` 的 sha256 基线，跑完逐个复核 → **零差异**，
`HEAD` 未动。（本仓既有教训：审查类 workflow 子代理会顺手改源码，且改动会静默混进
下一个 commit。）

---

## 本卡未证明什么

1. **未证明 `backend/app` 这 263 个文件的类型是正确的。** 存量报错一条没修（探针里
   `main.py` 1 err、`health.py` 4 err 就是活证据）。`pyrightconfig.json` 注释里的 592 err 是
   整个 include 面 304 文件的数，不是 backend/app 单独的数。
2. **未让主干上的这道门开始运行，也未在主仓上真实触发过一次 commit 验证。**
   主仓两个解析入口当前都无 pyright，但 PATH 一侧是在**车道交互 shell** 里测的，
   不是主仓 hook 运行时的 PATH。"主干 SKIP" ≠ "主干通过"。
3. **未接 CI。** `.github/workflows/**` 一字未改；CI 上 pyright 跑不跑、跑什么面，未测。
4. **未清 `backend/tests` 493 个文件的类型债。** 收窄只是让门不再拦它们，债还在。
5. **`backend/mutmut_config.py` / `backend/start_server.py` 不在门内**（旧 glob 也不在，
   v2 第 5、6 档已直接实测）。
6. **探针只证 glob 命中/不命中，不证 pyright 的结论。** pyright 报的 err/warn 未逐条核实。
7. **未证明收窄后 94% 拦截率会降到多少。** 没有做提交样本重放；机制成立 ≠ 实测比例已知。
8. **未证明「那 18 次被拦的报错与改动无关」。** 这是归因，本卡零样本核查——没有检视过
   那 18 次里任何一次的报错内容。
9. **深度 2 及更深的 glob 行为未测。** 实测抽样 = 深度 0 / 1 / 3；"跨任意层级"与
   "门面 = 263"都是按规则外推，不是枚举。
10. **844 不是 lefthook 匹配器的枚举结果**，是按"`**` 至少跨一级"规则划分出的模型集；
    实测支撑只有 depth-0 侧的两个样本（v2 第 5、6 档）。
11. **内部复核 32 条 finding 里有 26 条未经反驳验证**（CAP=6），其中可能仍有真缺陷。

## 台账待登记条目

1. **Z7-B 行 D-1 丙**：已落地，代码面 commit `64498c26`（glob + 注释）+ `bdf15fba` +
   本次收尾（后两次纯注释，结构等价）。
2. **勘误**：`258 / 0 / 35` → **`263 / 0 / 41` = include 面 304**；`backend` 目录总量 **846**、
   **旧 glob 可达面 844**（差 2）、`backend/tests` **493**。⚠️ 846 ≠ 844，别当同一个数用。
3. **「pyright 装进主干 venv」仍悬**：用户裁定暂不装 ⇒ 主干门继续 honest-SKIP。
4. **`backend/tests` 类型债卡待排**（493 文件）。
5. **行锚偏移 +59（最终值）**：`mutant-residue-scan` 286→**345**（Y4-C 面）、
   `pre-push` 383→**442**（Y4-D 面）、`python-typecheck` 146→**205**、glob 147→**206**。
   ⚠️ git history 里的 +36 / +43 是过程值，**已作废**；Y4-C/Y4-D 请动态 `grep -n` 取。
6. **`pyrightconfig.json` 的 `"src"` 死枝未清**（本卡硬边界禁改该文件）。
7. **`.github/workflows` 侧的 pyright 口径未核**。
8. **台账 Z7-B 行「门可达面 843 文件」需更新为 844**（并注明测量 SHA）；同行 `2089 err`
   属旧主干快照，本卡未重测，不追认。「include 面 304 / 592 err」与本卡实测一致。
9. **审后失绑登记**：Codex round-1 绑定 `64498c26`，其后本卡两次改 `lefthook.yml` 注释文本。
   等价性见 §等价性（结构等价 + 验伪锚），请主 session 按协议 §1 逐行核后判等价。轮次计 1 轮。
10. **卡文 Y4-B.md 自身带错数**（:12、:22 写「可达面 846」）：实做按 Codex 意见写 844，
    是对卡文的**正确偏离**。卡文是后人照抄的模板，建议主 session 更正，否则 846 会被复写。
11. **卡文裁判 7 的 `echo rc=$?` 在前两次提交上未落盘**（写在 `tee` 管道外），如实登记。
12. **内部复核 26 条 finding 未经反驳验证**，原始输出在
    `subagents/workflows/wf_1122526b-bc6/journal.jsonl`，供后续卡取用。
