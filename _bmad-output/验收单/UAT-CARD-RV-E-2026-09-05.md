# UAT — CARD-RV-E「Z7-A 门重写 870e52b3 复审 + 换行残孔定性」

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-RV-E]`
> 车道 `card/z7-tool`（本车道首卡，无前置；起点 HEAD `df39bf21`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-A.md`
> 2h，**纯复审，零代码改动**；Codex 1 轮

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化（把上一批改过的一道提交前检查重新读了一遍，
确认它现在拦得住什么、拦不住什么；发现一种极端文件名会漏过去，安排下一张卡修）。**

系统里有一道"交作业前的自查"：每次提交代码，它会翻一遍这次要提交的内容，
看有没有把测试时临时打的记号忘在里面没擦掉。上一批有人把这道自查重写过一次，
说补上了六个"该拦没拦"的漏子——但那次重写**没有人复查过**。

这张卡就是去复查。结论是：**六个漏子里有五个半确实补上了，而且是当场量出来的**——
把重写前和重写后的两份自查放在同一批"故意做坏的作业"上跑，
重写前只挑出 4 份，重写后挑出 8 份；其中最严重的一个漏子（某种显示设置下，
整道自查会一份都挑不出来还报"全部合格"）确认已经堵住。

**剩下半个没补上**：如果有人给文件起了一个"名字里带回车"的名字，这道自查还是会漏过去。
不过这需要人为去起这种名字（正常写代码不会出现），也不涉及丢数据、不涉及线上数据库，
所以定为"记账、下一张卡修"，不拦本批。

**顺带发现一条重写时没注意到的**：当文件名里带反斜杠时，自查**能挑出来**，
但**打印出来的文件名是错的**（反斜杠被吃掉了）。它会叫你去修一个不存在的文件。
同样定为记账级，一并交给下一张卡。

**还有三种情况这道自查也看不见**（复查时顺手翻出来的）：图片压缩包这类"不是文字"的
文件、把一个文件换成快捷方式、以及它自己中途读文件列表失败时——都会照样报"全部合格"。
同样是记账级，一起交给下一张卡。

另外请了外部审查（Codex）独立看了一遍，结论和这边**对上了**：六处确实补上了，
换行不是唯一漏子。它还指出**说明文字里有一句话说过头了**（那份配置文件的注释说
"这些报错跟版本无关"，实际有 3 条就是跟版本有关的）——这条本卡认了，已当场重测更正，
但它**不影响**那次撤回决定本身。

**代码一行没改**，`git status` 是空的。你不需要做任何事。

---

## 4-A 技术验收

### 证据索引（协议 §2.2：本单的每个数字都指向下面某个存档，不自述）

| 存档 | 内容 | 末行/判读 |
|---|---|---|
| `evidence-rv-e/j1-j2-audit-face-20260905T164712.txt` | 裁判 1/2：blob 同一性 + 审面 diffstat | `rc=0` |
| `evidence-rv-e/audit-face.diff` | 送审面本体（174 行） | sha256 `f4e42451…` |
| `evidence-rv-e/j4-newline-probe-20260905T164712.txt` | 裁判 4：含换行的不存在路径探针 + 三条对照 | `rc=0` |
| `evidence-rv-e/j4b-falsifier-20260905T164712.txt` | 补的验伪锚（原对照 C 是哑弹，见偏差 3） | `rc=0` |
| `evidence-rv-e/j5-lefthook-run-20260905T164712.txt` | 裁判 5：lefthook 2.1.6 + 空暂存区真跑门 | `[Mutant-Scan] OK` `rc=0` |
| `evidence-rv-e/j6-alpha-order-source-20260905T164712.txt` | 裁判 6：字母序断言出处 grep | `grep rc=1`（零命中） |
| `evidence-rv-e/gate-collide-20260905T164712.txt` | **(b) 的承重证据**：两版门六场景同场对撞 | 每场景末行 `OLD rc=` / `NEW rc=` |
| `evidence-rv-e/extra-paths-20260905T164712.txt` | (b') E1/E2/E3/E4 首轮 | 每项末行 `rc=` |
| `evidence-rv-e/extra-paths-v2-20260905T164712.txt` | (b') E2b/E3b 补严判据后重跑 | 每项末行 `rc=` |
| `evidence-rv-e/gate-old.sh` / `gate-new.sh` / `rv-e-collide.sh` / `rv-e-extra*.sh` | 复现脚本（门块逐字提取 + 驱动） | 一键可重跑 |

### (a) 审面写死，先证可读

| 判据 | 命令 | 实测 |
|---|---|---|
| 两文件 HEAD 与 `870e52b3` 同 blob | `git rev-parse HEAD:lefthook.yml 870e52b3:lefthook.yml` | `17dacb73c22b2c60fdfdd6e80f56536a33044fe0` ×2 ✅ |
| 同上 | `git rev-parse HEAD:ruff.toml 870e52b3:ruff.toml` | `fdc227b0e03cf51202740779c5a38f67a8390d12` ×2 ✅ |
| 审面规模 | `git diff --stat b20fe550 870e52b3 -- lefthook.yml ruff.toml` | `2 files changed, 88 insertions(+), 32 deletions(-)`（lefthook.yml 98 / ruff.toml 22）✅ |
| 送审面落盘 | `git diff b20fe550 870e52b3 -- …` | `evidence-rv-e/audit-face.diff`，174 行，sha256 `f4e42451…` |
| 块锚六处 | `awk 'NR>=286 && NR<=334'` | :286 块头 / :298 `tr` / :301 `while` / :308 `--literal-pathspecs` / :320 `done <` / :334 `OK` **六锚全对** ✅ |

被审 commit 主题：`870e52b3 fix(lint): 变异残留门补 6 处静默放行 + 撤回 target-version`；
基线 `b20fe550 style(scripts): ruff format 落盘 86 个文件…`。

**复审读的是 `audit-face.diff` + `lefthook.yml:250-334` + `ruff.toml` 全文，未读工作区摘要。**

### (b) 六处补法逐条判定 —— 判据不是作者自述，是**两版门同场对撞的实测**

方法（可一键复现，脚本 `scratchpad/rv-e-collide.sh`，日志
`evidence-rv-e/gate-collide-20260905T164712.txt`）：把 `b20fe550:lefthook.yml` 与
`870e52b3:lefthook.yml` 的 `run:` 块**逐字提取**成两个脚本（仅把标记串换成中性的
`ZZPROBEMARKZZ`，提取忠实度自证：与 git blob 逐行 diff 只有 MARKER 那一行差异），
在**隔离 scratch 仓**里造同一批对抗性索引，两版同场跑。
全程不触碰本工作树的 index、live vault、7691/7687。

> 场景 1 总账：索引里 **9 个**带标记文件 → 旧门抓 **4**，新门抓 **8**，
> 新门唯一漏的就是含换行的那个。

| # | 补法 | 行号 | 负控输入 | 旧门 | 新门 | 判定 |
|---|---|---|---|---|---|---|
| ① | `--name-only … -z`（:294-295）+ `tr '\000' '\n'`（:298） | :294-295、:298 | 文件名含 `"` / `\` / TAB | 三个**全部整条漏检**（C 引号化后 pathspec 匹配不到） | 三个全抓 | **补上了**（对 `"` `\` TAB） |
| ①' | 同上，换行分支 | :298 | 文件名含换行 | 漏 | **仍漏** | **没补上** —— 见 (c)；且**补出一个新的可达缺陷**，见「偏差 2」 |
| ② | `--literal-pathspecs` | :308 | 文件名 `:magic.py`（pathspec 魔法前缀） | **整条漏检** | 抓到 `:magic.py:1` | **补上了** |
| ③ | `--no-color`（diff 的**标志**，非 `-c`） | :294、:308 | `color.ui=always` + `color.diff=always` | **整道门 `OK` rc=0** —— 8 个带标记文件全放行 | 全抓，rc=1 | **补上了**（六处里后果最重的一条） |
| ④ | `--no-renames` | :294、:309 | 重命名 + 追加标记行（git 判 `R094`） | 漏 | 抓到 `renamed.py:31` | **补上了** |
| ⑤ | awk `inhunk` 状态机 | :313-315 | (i) 标记在以 `+++` 开头的正文行上；(ii) `+++` 行之后一行带标记 | (i) **整条漏检**；(ii) 抓到但**行号报 1（实为 2）** | (i) 抓到；(ii) 行号 2，正确 | **补上了** |
| ⑥ | `FAILED` 位 + fail-closed 出口 | :293 初值、:310/:319 置位、:321-324 出口；:291/:296/:299 直接 `exit 1` | 枚举命令失败（在非 git 目录跑） | `[Mutant-Scan] OK` **rc=0**（fail-open） | `[Mutant-Scan] FAILED: 枚举暂存文件失败` **rc=1** | **补上了** |
| （七） | `mktemp -d` 0700 | :290-292 | — | 用可预测的 `$$` 路径 | 私有目录 + `trap … EXIT` | 加固，单列不计入六处 |

**③ 的注释断言逐条复现**（:275-278 写的三个数字，本卡在 `color.ui=always` +
`color.diff=always` 下重测）：

```
裸 diff(无 --no-color)          : 0     ← 静默放行
-c color.ui=never (注释称无效)  : 0     ← 注释断言成立: color.diff 盖过 color.ui
--no-color 标志   (注释称有效)  : 3     ← 注释断言成立
```

**④ 的两处都在**：`--no-renames` 同时出现在枚举（:294）与取 diff（:309），
不是只补了一处。

**⑤ 的行号推进在 `-U0` 下正确**：`+` 行推进（:316）、上下文 ` ` 行推进（:317）、
`-` 删除行落到 :318 `{ next }` 不推进 —— 与新文件行号语义一致。

**⑥ 的失败点覆盖**：循环体内两个失败点（:310 取 diff、:319 awk）都置位；
循环外三个（:291 mktemp、:296 枚举、:299 tr）直接 `exit 1`。**无遗漏**。

### (b') 六处之外还有哪些「门未覆盖的路径」—— 本卡独立探针发现三条

卡文没要求这一段，但既然是复审，只核作者点名的六处不够。追加探针
（`evidence-rv-e/extra-paths-*.txt`，脚本 `rv-e-extra.sh` / `rv-e-extra2.sh`）：

| 编号 | 未覆盖路径 | 位置 | 实测 | 定级 |
|---|---|---|---|---|
| E1 | **二进制文件里的标记** | :312-319 | 含 NUL 的文件被 git 判 binary，diff 输出只有 `Binary files /dev/null and b/blob.bin differ`，**没有 `+` 行** → awk 无从命中。同批验伪锚 `control.py` 被抓到，证明门在跑 | 登记级 |
| E2 | **类型改变（`T`）整个文件不进枚举** | :294-295 | 普通文件改成 symlink、symlink 目标串带标记 → 状态字母 `T`；`--diff-filter=AM` **不含 T**，该文件根本不出现在枚举面（实测枚举只输出 `control.py`）。去掉 filter 后能看到 `+target_with_…_inside` 确实是一条新增行 | 登记级 |
| E3 | **`done < "$TMPD/list"` 重定向失败不置 `FAILED`** | :320 | `sh` 下 `while … done < /nonexistent` → 循环体不执行、`rc=1`、但 `FAILED` 仍是 0 → 继续走到 :334 打印 OK。**窗口窄**（`$TMPD/list` 由 :298 的 `tr` 刚建，`tr` 失败会 `exit 1`；要命中需 TMPD 在 :298 与 :320 之间消失），但确属 `FAILED` 位未覆盖的失败点 | 登记级 |

**反向对照（证明门没有过度拦截）**：E4 —— 标记只出现在**删除行**上时，门报
`OK` rc=0。这是**设计正确**的行为（只查新增行），不是缺陷。

> 三条都不改变 (b) 表里六处的判定，也都不构成阻断级（不涉数据丢失 / live 写 / 安全）。
> E1/E2 与换行残孔同属「需要特定文件形态才触发」，建议**一并交 Y4-C**；
> E3 建议在 Y4-C 改 :320 时顺手覆盖（改成读 `$TMPD/names` 后同样需要判重定向）。

### (c) 换行残孔：链条四环全部实测坐实，定**登记级**

| 环 | 位置 | 实测 |
|---|---|---|
| 1 | :294-295 | `-z` 输出里换行**是原始字节**：`od -c` 见 `n e w \n l i n e . p y \0` —— `-z` 本身没问题 |
| 1' | 对照（旧门） | 旧门无 `-z`，同一文件被 C 引号化成一行 `"new\nline.py"` |
| 2 | :298 | 经 `tr '\000' '\n'` 后，NUL 与文件名内的换行**不再可区分**，该名字裂成两行：`3:new` / `4:line.py` |
| 3 | :301-302 | 两段都非空 → 都进循环；:303-307 都不在排除名单 |
| 4 | :308-309 | 两段各自作 pathspec：**无输出、rc=0**（`seg1 rc=0` / `seg2 rc=0`） |
| 4' | 验伪锚 | 同形命令对真实存在的 `plain.py` **有输出**、rc=0 —— 证明上面的空输出是「匹配不到」而非「命令坏了」 |
| 5 | :310 / :319 | `FAILED` **不置位**（rc=0 不进 `if !` 分支）；awk 输入为空、`hits` 为空 |
| 6 | :334 | 打印 `[Mutant-Scan] OK`，rc=0 |

**门级复现**：场景 1 里新门抓到 8/9，唯一漏掉的就是 `new\nline.py`。

**定级：登记级（非阻断级）**，依据现行合并门口径逐条对照——
不涉及数据丢失、不涉及 live vault 或 Neo4j 7691 写入、不涉及安全边界、非指定裁判红、
非负控假绿；触发需要**人为**造出含换行的文件名（正常开发流程不产生）。

**同时如实记录：这与块 :284 自称的「扫描没跑完 = fail-closed」相矛盾**——
这条路径上扫描确实"没跑完"（一个文件根本没被扫），但门报 OK。

**修法（写成 Y4-C `CARD-TOOL-residue-newline` 的输入，本卡不落地）**：
去掉 :298-299 的 `tr` 中转，:301 直接以 NUL 分隔消费 :294-295 已经写好的 `-z` 输出：

```sh
while IFS= read -r -d '' f; do    # :301
  ...
done < "$TMPD/names"              # :320 改读 names，不再需要 list
```

**解释器可行性（本卡已替 Y4-C 探明）**：lefthook 2.1.6 以 `sh` 启动 `run:` 块
（`$0` = `sh`），但 macOS 上该 `sh` 是 **bash 3.2.57**（探针里 `BASH_VERSION`
非空、`ZSH_VERSION` 未设），`read -r -d ''` **实测可用**（`printf 'a\0b\0'` 正确读出两段）。
⚠️ **可移植性告警交 Y4-C**：`read -d` 是 bash 扩展，Linux 上 `/bin/sh` = dash 时**不存在**。
这道 hook 目前只在本机 pre-commit 跑，但若将来进 CI 需改用 `xargs -0` 或显式 `bash`。

### (d) `ruff.toml` 三条结论

**① `target-version` 已撤回，且注释里的三条理由逐条成立。**

撤回本身（精确判据，带验伪锚）：

```
git show b20fe550:ruff.toml | grep -n '^target-version'  → 30:target-version = "py312"   rc=0  ← 验伪锚
git show 870e52b3:ruff.toml | grep -n '^target-version'  → 无命中                        rc=1
grep -n '^target-version' ruff.toml                      → 无命中                        rc=1
```

三条理由的实测：

| 理由 | 注释断言 | 本卡实测 | 成立? |
|---|---|---|---|
| 1 | `pyproject.toml` 的 `requires-python = ">=3.9"` 使 ruff 推断出 py39，故"py39 是无依据的缺省"不成立 | `pyproject.toml:6` 确有 `requires-python = ">=3.9"`；`ruff check --show-settings scripts/send_bark.py` → `linter.unresolved_target_version = 3.9`、`formatter.unresolved_target_version = 3.9` | ✅ |
| 2 | 原证据（`scripts/finalize-iteration.py` 的 3 条 PEP 701 invalid-syntax）已被同卡的 `ruff format` 抹掉 | `ruff check --target-version py39 scripts/finalize-iteration.py` → `All checks passed!` rc=0 | ✅ |
| 3 | CI 用 3.11 / 3.12，抬到 py312 会放行 CI 跑不了的语法 | `api-spec-sync.yml:50 PYTHON_VERSION: '3.11'`；`readme-claims.yml:35` / `release-evidence.yml:39` = `'3.12'` | ✅ |

注释 :33-35 的现状**数字**复现：`scripts/` 的 invalid-syntax
**py39 / py310 / py311 各 24 条、py312 21 条**，且**全部**落在
`scripts/spec-tools/api-reality-dashboard.py`（按 ruff 0.15.9 的 `-->` 行统计，
唯一文件）；该文件在 `backend/.venv`（Python 3.14.4）下 `py_compile` 报
`SyntaxError: unexpected character after line continuation character`。
ruff 版本 = 0.15.9，与注释一致。

> ⚠️ **但注释 :33-35 的推论句「那是真语法错，与目标版本无关」措辞过强 —— 本卡初稿
> 曾写「逐字成立」，由 Codex 打回后重测更正。** 24 与 21 的差额那 3 条，
> 全在 `api-reality-dashboard.py:120`，诊断原文自己写着版本依赖
> （证据 `evidence-rv-e/ruff-version-delta-*.txt`）：
>
> ```
> invalid-syntax: Cannot use an escape sequence (backslash) in f-strings on
>                 Python 3.9 (syntax was added in Python 3.12)      ×2  (:120:38, :120:46)
> invalid-syntax: Cannot reuse outer quote character in f-strings on
>                 Python 3.9 (syntax was added in Python 3.12)      ×1  (:120:39)
> ```
>
> 精确表述应为：**24 条里 21 条与目标版本无关**（py312 下仍报，含
> `f-string: unterminated string` / `expecting }` 这类真语法错），
> **另 3 条确实是目标版本相关的**（PEP 701，py312 才合法）。
> 注释在同一段里既报了 24 vs 21 的差额、又断言"与目标版本无关"，**自相矛盾**。
>
> **这不推翻撤回决定**：即便按 py312 判，该文件仍有 21 条真语法错，
> Python 3.14 `py_compile` 也失败——撤回 `target-version` 的三条理由不依赖这句推论。
> **只是这句话本身要改**，登记交第十三批（与 `select = []` 同批动 `ruff.toml` 时顺手）。

**② `line-length = 120` 保留（D-2 用户裁），三处对齐已核**：
`ruff.toml:36` / `pyproject.toml:101` / `backend/ruff.toml:6` 全为 120。

**③ `[lint] select = []`（`ruff.toml:38-39`）⇒ `scripts/` 仍只有语法级 + 格式级门**，
未定义名之类不报（对照：`backend/ruff.toml:9-10` = `select = ["E9","F63","F7","F82"]`）。
**本卡不动，移交第十三批。**

### (e) 执行时机断言（:259-268）出处复核 —— **无出处，如实登记，不追认**

```
grep -n 'exec_unix\|evilmartians' lefthook.yml   → 零命中, rc=1
```

`lefthook.yml` 全文 435 行，全文无 lefthook 源码或官方文档链接。
`priority:`（带冒号）在全文**唯一命中 :266**，且在注释里——即本仓没有任何命令实际设过
`priority`，那条"任何 priority 值都排到最前"的断言**在本仓无生产反例可对照**。

**但本卡另找到一条审查面内的旁证，可支持该断言的前半句**
（证据 `evidence-rv-e/order-corroboration-*.txt`）：

`pre-commit` 下 8 个 command 的 **YAML 书写顺序**与**字母序完全不同**——

| | 顺序 |
|---|---|
| YAML 书写序（行号 :51 / :62 / :75 / :117 / :146 / :187 / :231 / :286） | `spec-sync-flat` → `spec-sync-root` → `ghost-files` → `python-lint` → `python-typecheck` → `cypher-vault-filter-lint` → `readme-claims-lint` → `mutant-residue-scan` |
| 字母序 | `cypher-vault-filter-lint` → `ghost-files` → `mutant-residue-scan` → `python-lint` → `python-typecheck` → `readme-claims-lint` → `spec-sync-flat` → `spec-sync-root` |
| 注释 :261-263 记录的**观察序** | `c…` → `ghost-files` → `mutant-residue-scan` → `python-lint` → `p…(注释称 pyright 门 = python-typecheck)` → `r…` → 两个 `spec-sync` |

**观察序逐项等于字母序、且不等于 YAML 序** ⇒ 「按 YAML 位置执行」这一假说被排除。
这不是源码出处，但**比"仅本机实测"更强**：它在审查面内可复核。

**注释 :264-266 的时序结论在本仓成立（本卡实测）**：`git add backend/openapi.json`
出现在 `lefthook.yml:60` 与 `:71`，分属 `spec-sync-flat`（:51）/ `spec-sync-root`（:62）
—— 字母序里排第 7、8，`mutant-residue-scan` 排第 3。**该文件确实在扫描之后才被 `git add`。**

**断言的后半句（"任何 `priority` 值都排到最前"）仍无任何旁证**：本仓 8 个 command
无一设过 `priority`（全文 `priority:` 唯一命中 :266 的注释）。
**登记为「前半句有审查面内旁证、后半句仅本机实测、整体无源码出处」，不追认为规格。**

本卡未重新验证该断言本身：
lefthook 2.1.6 的 `run` **没有 `--dry-run`**（`lefthook run --help` 全部 flag 已核），
要观察执行顺序只能真跑整个 `pre-commit`，而那会触发 OpenAPI 快照块的 `git add`
—— 与本卡「零代码改动」硬边界冲突。**改为在本卡收尾 commit 时从真实 hook 输出里捕获**
（见 (g) 段）。

### (f) Codex 1 轮

见「三 Codex 复审」段。

### (g) 零代码改动

见「四 收工判据」段。

---

## 二 偏差登记（三条，如实不擅改）

### 偏差 1 — 卡文 §〇 的**注释子项行号整体偏移 2 行**（代码锚点全对）

卡文 §〇 写「防御注释 :269-285 …`-z + tr`（:269-271）/ `--literal-pathspecs` :272 /
`--no-color` :273-276 / `--no-renames` :277-278 / awk inhunk :279-281 / FAILED 位 :282 /
`mktemp -d` :283」。实测：

| 子项 | 卡文 | 实测 |
|---|---|---|
| 块起始行 | :269 | **:270**（:269 是空注释行 `#`） |
| `-z + tr` | :269-271 | **:271-273** |
| `--literal-pathspecs` | :272 | **:274** |
| `--no-color` | :273-276 | **:275-278** |
| `--no-renames` | :277-278 | **:279-280** |
| awk inhunk | :279-281 | **:281-283** |
| FAILED 位 | :282 | **:284** |
| `mktemp -d` | :283 | **:285** |

**代码块的六个锚点（:286/:298/:301/:308/:320/:334）与七项补法行号（:290-295/:298/:301/
:308-309/:313-319/:321-324）实测全对**，偏移只发生在注释区。
**这条要交给 Y4-C**：它要改的正是 :286-340，若照卡文的注释行号定位会错位 2 行。

### 偏差 2 — 卡文把 ① 的换行分支写作「补出新洞」，实测应为「**没补上**」；
但**另有**一条真正的、由本次重写变为可达的新缺陷

- **换行**：旧门也漏（C 引号化 → pathspec 匹配不到）、新门也漏（tr 拆段 → pathspec
  匹配不到）。**结局相同，路径不同**。`-z` 本身是正确的，收益被 :298 的 `tr` 当场抵消。
  精确表述是「**没补上**」，不是「补出新洞」。（不影响 (c) 的定级与修法。）
- **真正的新可达缺陷**：`awk -v F="$f"`（:312）—— awk 的 `-v` 赋值**做转义序列处理**。
  实测（BWK awk 20200816，macOS 系统 awk）：

  ```
  awk -v F='back\slash.py'  →  F=[backslash.py]      ← 反斜杠被吃掉
  awk -v F='a\nb.py'        →  F=[a<换行>b.py]        ← 报告行直接裂成两行
  awk 'BEGIN{...}' 'back\slash.py' (位置参数)  →  F=[back\slash.py]   ← 对照, 不做转义
  ```

  场景 1 的新门输出里可直接看到：文件真名是 `back\slash.py`，
  BLOCKED 报告打印的是 **`backslash.py`**（一个不存在的路径）。

  **为什么算"新"**：`-v F=` 在旧门里也是这么写的，但旧门**根本扫不到**含反斜杠的
  文件名，这个缺陷不可达；`-z` 修好检测后它才变成可达。
  **影响**：只在**显示层**（`F` 仅用于打印，检测用 `index($0, M)`、排除用 `case "$f"`，
  两者都直接用 `$f`，**不受影响**）。但 BLOCKED 文案紧接着叫人
  「先 restore 被改的生产文件」——**报出的路径是错的，会把人指向不存在的文件**。
  **定级：登记级**（不漏检、不误拦），**并入 Y4-C**：把 `F` 改用位置参数
  （`awk '…' F="$f"` 形式或 `ARGV` 传参）而非 `-v`。

### 偏差 3 — 卡文裁判 4 的对照项里有一个**哑弹**，本卡自行补了验伪锚

卡文裁判 4 只要求「`git --literal-pathspecs diff --cached -- <含换行的不存在路径>`
→ 无输出 rc=0」。本卡首轮加的对照 C
（`git --literal-pathspecs diff --stat df39bf21 03ac8bf8 -- lefthook.yml`）**证明不了任何事**：
`df39bf21:lefthook.yml` 与 `03ac8bf8:lefthook.yml` 本就是同一 blob（`17dacb73…`），
空输出 rc=0 是必然的。**「空输出 = 匹配不到」这个推论在那条对照下恒真，等于没验。**

补的验伪锚：`git --literal-pathspecs diff --stat b20fe550 870e52b3 -- lefthook.yml`
→ 输出 `1 file changed, 74 insertions(+), 24 deletions(-)`，rc=0。
**同形命令在有差异时确实出输出**，(c) 环 4 的空输出才成立。
场景 5 里对 `plain.py` 也加了同类锚点。

---

## 三 Codex 复审（1 轮，`gpt-6-astra` + `ultra`，rc=0）

存档 `_bmad-output/审查/codex-review-CARD-RV-E.md`（首部按协议 §2.1 六行，
绑定 `b20fe550..870e52b3`；`.stderr` 按 `.gitignore` 不入库）。
**总判：`PASS with findings`** —— 「六个定向修补均已落实，但完整的 fail-closed
声明不成立，换行也不是唯一残孔」。

### 收敛（Codex 独立得出、与本卡实测一致的六条）

Codex 只做静态阅读（未跑 hook），本卡只做隔离仓实测（未读它的结论），两条路线各自到达：

| 结论 | Codex（静态） | 本卡（实测） |
|---|---|---|
| 六处补法 ①-⑥ 全部「补上了」 | 逐条核到行号，并明确核对 ③ 的 `--no-color` 在 diff 标志位、④ 两处都有 `--no-renames`、⑤ 在 `-U0` 下行号推进正确 | 对撞：旧门 4/9 → 新门 8/9，每条各有翻转用例 |
| ⑥「补上了原管道吞码，全部失败覆盖没补上」 | `:301` 读取错误被当 EOF、`:320` 重定向失败不进失败出口 | E3：`done < /nonexistent` → `FAILED=0` → 打印 OK |
| 类型改变 `T` 不进枚举 | `:295`/`:309` 仅接受 `AM` | E2b：`t.txt` 状态 `T`，枚举面只有验伪锚 `control.py` |
| 二进制不进扫描 | 二进制差异通知没有 `@@` | E1：`Binary files … differ`，无 `+` 行，漏检 |
| `awk -v F` 反斜杠失真 | `:312` 会解释转义 → 报告路径失真 | 场景 1：`back\slash.py` 报成 `backslash.py` |
| 换行残孔链条成立 | 逐环推导 | 四环实测 + 验伪锚 |

### Codex 提出、本卡采纳并已处理的四条

1. **`ruff.toml:33-35` 推论过强** —— [LOW]「编译失败被过度归因」。**Codex 是对的**：
   24 vs 21 的差额那 3 条诊断自己写着 `(syntax was added in Python 3.12)`。
   本卡初稿写「注释 :33-35 逐字成立」，**已重测更正**，见 (d) 段的告警块。
2. **`:316` 只做子串匹配 → 合法引用会被误拦** —— [LOW]。属既有设计边界
   （排除名单 `_bmad-output/*` 正是为此），但**排除名单之外**的文档/字符串合法引用
   仍会被拦，且 `:330` 的文案会把它说成「harness 没还原干净」。**登记，交 Y4-C 一并考虑**。
3. **`:334` 的 OK 不覆盖最终暂存区（时序）** —— Codex 说「不能确认为本仓已发生的漏报」。
   **本卡实测确认它在本仓成立**：`git add backend/openapi.json`（:60/:71）属
   `spec-sync-flat`/`spec-sync-root`，字母序第 7/8，晚于本块（第 3）。见 (e) 段。
4. **`:301` 中途读取错误被当 EOF** —— 本卡 E3 只测了 `:320` 的重定向失败，
   Codex 补了「中途读取错误」这一形态。**并入 E3 登记**。

### Codex 标「无法确认」、本卡在审查面之外已实测的五条

（Codex 的读取面是本卡在 prompt 里**写死**的三处，它按边界如实声明「不能判定」，
这是正确行为；下列不是分歧，是**补齐**。）

| Codex 的声明 | 本卡实测 |
|---|---|
| 「本仓生效 py39 未独立确认」 | `ruff check --show-settings` → `linter.unresolved_target_version = 3.9`；`pyproject.toml:6` = `requires-python = ">=3.9"` |
| 「formatter 改写前后的历史事实未确认」 | `ruff check --target-version py39 scripts/finalize-iteration.py` → `All checks passed!` rc=0 |
| 「实际 workflow 版本未确认」 | `api-spec-sync.yml:50 PYTHON_VERSION: '3.11'`；`readme-claims.yml:35` / `release-evidence.yml:39` = `'3.12'` |
| 「另两份配置与用户裁定记录未确认」 | `ruff.toml:36` / `pyproject.toml:101` / `backend/ruff.toml:6` 全为 120（用户裁定 D-2 在批次台账，不在代码树） |
| 「Git 属性 / textconv / 外部 diff 是否启用未确认」 | 本仓 `.gitattributes` **只有行尾归一化 + `binary` 标注，无任何 `diff=` 驱动、无 `textconv`**；`git config --get-regexp '^diff\.'` rc=1（零配置）。⇒ **textconv/外部 diff 这条路径在本仓当前配置下不可达**；但 `*.png/*.jpg/*.pdf/*.gz/*.zip` 的 `binary` 标注使 **E1（二进制漏检）在本仓可达**。证据 `evidence-rv-e/codex-followup-*.txt` |

### 分级口径的差异（不是分歧）

Codex 把换行残孔判 **MEDIUM**，并声明「不能认证符合本项目登记级判据——审查面里
没有分级规程」。**这是边界正确的说法**：协议
`.claude/rules/card-batch-protocol.md` §1 不在它的读取面内。

两套口径不冲突：Codex 的 MEDIUM 是**通用严重度**；本项目的「阻断级 / 登记级」是
**合并门口径**（§1：阻断级 = 数据丢失 / live vault 或 Neo4j 7691 写入 / 安全 /
指定裁判红 / 负控假绿，其余登记不阻断）。按 §1 逐条对照，换行残孔与 E1/E2/E3
**均不落在五类阻断级里** ⇒ 登记级，**不阻断本批合并**。

Codex 的完整发现清单（4 MEDIUM + 5 LOW）全部为「下卡修 / 只登记」，
**零 BLOCKER / 零 HIGH ⇒ 阻断级 = 0，合并门通过。**

---

## 四 收工判据

| 判据 | 命令 | 实测 |
|---|---|---|
| 工作树干净 | `git status --porcelain` | （见 commit 后附） |
| 零代码改动 | `git diff --stat df39bf21 HEAD -- . ':(exclude)_bmad-output'` | （见 commit 后附）|
| lefthook 版本 | `/opt/homebrew/bin/lefthook version` | `2.1.6` ✅ |
| 门真跑（空暂存区） | `lefthook run pre-commit --command mutant-residue-scan --force --no-auto-install` | `[Mutant-Scan] OK (staged additions carry no mutation marker).` **rc=0** ✅ |

> 写法注意（协议 §1）：排除写 `':(exclude)…'`。`':!…'` 在 zsh / git 2.50 下
> rc=128、stdout 空，「空即通过」会假绿。

**本卡未用 `LEFTHOOK_EXCLUDE`**（D-14 绕过口径对本车道不适用）；
提交时 hook 真跑，每个 command 的 SKIP/PASS 与 rc 见「五 提交期 hook 实况」。

---

## 五 提交期 hook 实况

（本段在 commit 后填写；同时用来捕获 (e) 段所需的**实际执行顺序**。）

---

## 六 本卡未证明什么

1. **没有修换行残孔** —— 只定性 + 写成 Y4-C 输入。这道门在本卡收工时**仍然**对含换行的
   文件名 fail-open。
2. **没有修 `awk -v` 显示层缺陷**（偏差 2）—— 同样只登记，并入 Y4-C。
3. **没动 `scripts/` 的 lint 规则集** —— `[lint] select = []` 保持原样，移交第十三批。
   本卡只证明了"它现在是空集"，没证明"应该开哪些规则"。
4. **没碰 pyright 门**（`lefthook.yml:147` 及 `pyrightconfig.json`）—— 那是 Y4-B。
5. **没有在本仓暂存区跑过一次真实 BLOCKED**。本卡的 BLOCKED 全部来自**隔离 scratch 仓**
   里的复刻脚本（逐字提取 + 中性标记串）。「主干这道门在真实 index 上会拦下带标记的
   提交」这句话，本卡**只证到 OK 分支**（空暂存区 rc=0），阻断分支由 Y4-C (b) 做。
6. **未重新验证 :259-268 的字母序断言本身**（无 dry-run，真跑全 pre-commit 会触发
   `git add`，与零改动边界冲突）。收尾 commit 的 hook 输出只能给出**本次实际跑到的
   命令顺序**，不等于对"任何 priority 值都排到最前"那半句的验证——那半句在本仓
   **无生产反例**，仍是未验证断言。
7. **字母序断言无源码/文档出处** —— 本卡 grep 零命中，登记为"仅本机实测"，**不追认为规格**。
8. **两版门的对撞只覆盖本机环境**（macOS / git 2.50 / BWK awk 20200816 / bash 3.2.57）。
   Linux + gawk + dash 下的行为**未测**（⑤ 的 awk 语义、Y4-C 的 `read -d` 都可能不同）。
9. **(b') 的三条未覆盖路径也没修**（E1 二进制 / E2 类型改变 / E3 重定向失败）——
   只登记，交 Y4-C。
10. **(b') 不是穷举**。本卡只探了「二进制 / 类型改变 / 重定向失败 / 删除行」四类，
   **没有**系统枚举 `--diff-filter` 其余状态字母（`C` `U` `X` `B`）、子模块、
   `core.autocrlf` 等可能改变 diff 文本形态的配置。
   （`textconv` / 外部 diff 已在收尾时核为**本仓未配置**，见 §三；
   但"未配置"是**今天的快照**，有人加 `.gitattributes` 条目它就回来了。）
   「除这几条外没有别的洞」**本卡不主张**。
10b. **`:301` 的"中途读取错误"形态未实测**（Codex 静态提出，本卡 E3 只实测了
   `:320` 重定向失败）。两者同属 `FAILED` 未覆盖面，但**是两个不同的触发条件**。
10c. **本卡初稿在 (d) 段把 `ruff.toml:33-35` 判成「逐字成立」，是错的**，
   由 Codex 打回后重测更正。**这说明本卡的静态判读也会过头**——
   台账登记以更正后的 (d) 告警块为准，不以初稿措辞为准。
11. **未审 `870e52b3` 里 lefthook.yml `:95-115` 那两段 python-lint 注释改动**的事实性
   （送审 diff 含这 2 个 hunk，但卡文 (b)(c)(d) 未点名；本卡只核了它们与 (d) 的
   `select = []` 结论一致，未逐条复验其中的 91/49/845 等计数）。

---

## 七 台账待登记条目（本卡不改台账，交主 session）

1. **Z7-A 行补**：`870e52b3` 已由 CARD-RV-E 复审（第十二批）。六处判定 =
   **②③④⑤⑥ 补上（各有旧门放行 / 新门拦下的对撞实测）；① 对 `"` `\` TAB 补上、
   对换行没补上**。旧门 4/9 → 新门 8/9。
2. **§五.7 换行残孔**：链条四环实测坐实，**定登记级** → **Y4-C 修**
   （修法 + 解释器可行性已写进 `UAT-CARD-RV-E-2026-09-05.md` (c) 段）。
3. **新增登记项（本卡发现）**：`lefthook.yml:312` 的 `awk -v F="$f"` 转义处理导致
   BLOCKED 报告打印错误路径（含 `\` 的文件名）→ **并入 Y4-C**，登记级。
4. **卡文行号勘误**：第十二批 Y4-A 卡文 §〇 的**注释**子项行号整体偏移 2 行
   （代码锚点全对）→ **Y4-C 定位 :286-340 时以本验收单「偏差 1」的实测表为准**。
5. **`ruff.toml` `[lint] select = []`** → 移交**第十三批**（开 `scripts/` 必错级规则集，
   对齐 `backend/ruff.toml` 的 `E9,F63,F7,F82`）。
5b. **新增登记项（本卡独立探针，六处之外的三条门未覆盖路径）** → 建议一并交 Y4-C：
   **E1** 二进制文件里的标记漏检（git diff 无 `+` 行）；
   **E2** 类型改变 `T` 不在 `--diff-filter=AM` 枚举面内，整个文件不被扫；
   **E3** `:320 done < "$TMPD/list"` 重定向失败不置 `FAILED`（窗口窄，但属 fail-open）。
   三条均为登记级，证据见 `evidence-rv-e/extra-paths-*.txt`。
6. **`lefthook.yml:259-268` 的字母序 / priority 断言无源码出处** → 登记
   「**前半句（字母序）有审查面内旁证**（观察序 = 字母序 ≠ YAML 序）、
   **后半句（任何 priority 值排最前）仅本机实测**、整体无源码/文档出处」，
   **不追认为规格**；若要转正需 lefthook 2.1.6 源码或官方文档出处。
   注释 :264-266 的时序结论**已由本卡实测确认在本仓成立**。
7. **`ruff.toml:33-35` 的推论句要改**（Codex [LOW]，本卡重测确认）：
   「全部…与目标版本无关」对 24 条里的 3 条为假——那 3 条
   （`api-reality-dashboard.py:120:38/:39/:46`）诊断原文写着
   `(syntax was added in Python 3.12)`。**不推翻撤回决定**，只是措辞自相矛盾
   （同段既报 24 vs 21 差额、又说无关）→ **随第十三批动 `ruff.toml` 时顺手改**。
8. **Codex 另提两条登记项** → 交 Y4-C 一并考虑：
   `:316` 的子串匹配会把**排除名单之外**的合法标记引用判成「harness 没还原干净」
   （`:330` 文案随之失真）；`:301` 的**中途读取错误**被当作 EOF（与 E3 同族，
   本卡只实测了 `:320` 的重定向失败形态）。
9. **`.gitattributes` 现状已核**：本仓无 `diff=` 驱动、无 `textconv`
   （`git config --get-regexp '^diff\.'` rc=1）⇒ textconv/外部 diff 路径**当前不可达**；
   但 `*.png/*.jpg/*.pdf/*.gz/*.zip` 的 `binary` 标注使 **E1 二进制漏检在本仓可达**。
10. **本卡不引台账 Z3-A 行的任何「+962」类数字。**
