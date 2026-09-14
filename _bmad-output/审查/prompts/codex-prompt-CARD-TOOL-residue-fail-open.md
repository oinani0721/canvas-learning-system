# 只读复核请求 — CARD-TOOL-residue-fail-open（round-1）

## 一 背景 + 最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
分支 `card/t8-tools`，基线 `08100483`（B14_BASE），本卡 commit `cd31cffd`。

`lefthook.yml` 里有一个 pre-commit 命令 `mutant-residue-scan`：变异测试的 harness 会原地改
生产文件再还原，还原失败就把带标记的变异体留在树上；这个块在 commit 前扫暂存区的**新增行**，
命中那个标记就 exit 1 阻断。标记串在块内由两段拼出（`MARKER="MUT""ANT"`），使本文件自身不含
该字面量。本 prompt 与下述文档一律不写该字面量。

上一张卡（CARD-TOOL-residue-newline，存档见下）登记了这个块的**九条存量 fail-open**
（六条 + 三条）外加一行 `-s hits`：某一步失败了，但 `FAILED` 位没有被置上，于是块末照样打
`OK` 并退 0 —— 「门坏了」与「没抓到东西」在输出上一模一样。本卡把它们逐条封住。

**最小读取面（只需要这些，不必通读全仓）**：

1. `git diff 08100483 cd31cffd -- lefthook.yml`（本卡的全部代码改动）
2. `lefthook.yml` 当前版本里 `mutant-residue-scan` 块及其上方注释段的全文。
   行号已因本卡加注释而位移，请用锚点定位：
   - 注释段起点：含 `--- Mutant residue scan` 的那一行
   - 块名行：含 `mutant-residue-scan:` 的那一行（全文件唯一）
   - 块末行：含 `Mutant-Scan] OK` 的那一行（全文件唯一）
3. `_bmad-output/审查/codex-review-CARD-TOOL-residue-newline.md` 的 §2 表与 §4 段
   （九条 fail-open 的原始登记，绑定 `9b4acf62`）
4. 本卡的十份对照脚本与它们的输出：
   `_bmad-output/审查/evidence-residue-fo/case-*.sh` 与同目录 `out-case-*.txt`
5. 真 hook 的两份输出：
   `_bmad-output/审查/evidence-residue-fo/h-poscontrol-raw-20260914T195939.txt`
   `_bmad-output/审查/evidence-residue-fo/h-negcontrol-raw-20260914T195953.txt`

## 二 作者自述（请独立核对，不要采信本节）

### 2.1 九条（+`-s hits`）的处置表：全部判为「封」，各配一份对照

对照口径：**同一个输入**，在**旧版块**（`git show 08100483:lefthook.yml` 抽出）上必须打
`[Mutant-Scan] OK` 且 rc=0；在**新版块**（当前工作树抽出）上必须不打 OK 且 rc=1。
只证明新版会红不算封住。抽块的行范围由锚点现求，不写死行号。

| # | 登记的失败形态 | 封法 | 对照脚本 | 对照里的输入怎么来的 |
|---|---|---|---|---|
| 6-1 | 单文件 diff 缺 `--no-ext-diff` | 补 `--no-ext-diff` | `case-6-1-ext-diff.sh` | `GIT_CONFIG_*` 注入 `diff.external`（一个只 exit 0 的程序）。旧标志集下 git 仍 rc=0 而正文 0 字节 |
| 6-2 | 单文件 diff 缺 `--no-textconv` | 补 `--no-textconv` | `case-6-2-textconv.sh` | 临时仓里 `.gitattributes` 挂 `diff=strip` + `GIT_CONFIG_*` 注入该驱动的 textconv，把标记换成别的字样 |
| 6-3 | 单文件 diff 缺 `--text` | 补 `--text` | `case-6-3-text.sh` | 文件第 1 行带标记、第 2 行以 NUL 开头 ⇒ 旧写法只输出 `Binary files … differ` |
| 6-4 | `--diff-filter=AM` 不含 `T` | 枚举与单文件 diff 都改 `AMT` | `case-6-4-typechange.sh` | 仓里先提交 symlink，再换成同名普通文件并暂存 ⇒ git 判 T |
| 6-5 | `: > "$TMPD/hits"` 无守卫 | 补 `\|\| { …FAILED…; exit 1; }` | `case-6-5-hits-init.sh` | mktemp 垫片在临时目录里预置 444 的 `hits`；暂存面只放允许名单内的文件（否则后面的 `>>` 会失败，而那一步本来就有守卫） |
| 6-6 | awk 文件参数形如 `name=value` 被当变量赋值 | 改成 `< "$TMPD/d"`，不给操作数 | `case-6-6-awk-operand.sh` | `TMPDIR='t=x'`（相对路径、首段含 `=`）；暂存两个文件，带标记的排序在后 |
| 8-1 | 主循环输入重定向打不开 | 枚举后校验「可读的普通文件」 | `case-8-1-redirect.sh` | mktemp 垫片预置 200（只写）的 `names`：写得进、读不出 |
| 8-2 | 主循环 `read` 报错 | `SEEN` 必须等于 `EXPECTED`（清单里的 NUL 个数） | `case-8-2-read-error.sh` | **注入**：旧/新两版在主循环之前同一位置插入同一条语句，把记录流换成目录 |
| 8-3 | 记录流末条无 NUL 终止 | 枚举后校验末字节是 NUL | `case-8-3-no-nul.sh` | git 垫片让枚举那一次调用输出末条缺 NUL 的流，其余 git 调用透传 |
| `-s hits` | `[ -s ]` 为假被当成「没有命中」 | 为假时追核 `hits` 仍是可读普通文件 | `case-9-s-hits.sh` | mktemp 垫片把 `hits` 预置成 `-> /dev/null`：写得进去但写丢，size 恒 0 |

十份全部报 `SEALED`。其中 `case-9-s-hits` 是唯一一条**旧版打 OK 的同时确有真命中**的对照。

### 2.2 允许名单：由 2 项补到 6 项

新增 `backend/scripts/g32ccr1_negative_controls.py`、`backend/scripts/openapi_drift_negative_control.py`、
`backend/tests/regression/recap_domain_negverify.py`（三个负控本体，此前**不在**名单里，一旦被暂存
修改就会被这道门拦下）＋ `.claude/rules/*.md`（按默认补，待用户确认）。

对账算法（`out-case-e-allowlist-20260914T200044.txt`）：
- `git grep -l "$MARK" -- . ':(exclude)_bmad-output'` 得到的每一项，在 `case … esac` 区间内**恰出现 1 次**
  （区间由 `grep -n` 现求，不写死行号；验伪锚 `no-such-file.py)` = 0）。
- 四条新分支各跑一份**方向相反**的对照：旧版 BLOCKED rc=1 / 新版 OK rc=0。
- 五条验伪锚必须**仍被两版都拦下**：`…_copy.py`、`.md.bak`、`notes.txt`、`.claude/rulesX/a.md`、
  `docs/.claude/rules/a.md`。
- 实测并写进注释：`case` 的 `*` **会匹配 `/`**，所以 `.claude/rules/*.md` 覆盖该目录下任意深度的 `.md`
  （与既有的 `_bmad-output/*` 同口径）。

### 2.3 两份真 hook 输出

- 正控：允许名单内的路径放一个带标记的文件并暂存 → `[Mutant-Scan] OK`，lefthook rc=0。
- 负控：`backend/scripts/_t8a_probe.py`（不在名单内）→ `[Mutant-Scan] BLOCKED`，lefthook rc=1。
  跑完 `git reset HEAD -- <path>` + 删文件，`git status` 无残留。
- lefthook 一律**裸调用** `/opt/homebrew/bin/lefthook`（2.1.6）。

### 2.4 注释更正

排除名单注释里两处计数过时：`g32b` 写 153 → 实测 **151**；`g32cb` 写 10 → 实测 **11**。
五个文件的计数（151 / 11 / 11 / 2 / 13）均为 `08100483` 上逐文件 `grep -c` 实测。
另把 `-z + tr` 三行改写为现行事实（记录按 NUL 逐条消费，不经 `tr`）。

### 2.5 不碰邻块

`python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)` 注释段归另一张卡
（T8-G），本卡一行不改；已用逐字节比对自证两段与 `08100483` 相同。命令名与 `priority` 未动
（命令按名字母序执行，改名会改执行位次）。

## 三 请按重要性回答的问题

1. 十条里有没有哪一条的「封」其实**没有改变失败路径**——也就是新版之所以 rc=1，是被对照
   输入里的**别的**原因满足的，而不是那一条守卫？（尤其 6-5 与 `-s hits` 这两条用了 mktemp
   垫片，8-2 用了注入。）
2. 新加的守卫本身有没有引入**新的静默放行**？例如 `||` 分支里再跑一个可能失败的命令、
   `EXPECTED` 的统计管道在某种输入下给出错误但非空的数字、`tail -c 1 | od | tr` 这条链在
   某个 locale 或某种文件形态下给出非预期的值。
3. 允许名单的匹配面是否比它要豁免的对象**更宽**？`.claude/rules/*.md` 在 `case` 里的语义
   （`*` 匹配 `/`）是否会把不该豁免的路径放进来？五条验伪锚够不够？
4. `--text` / `--no-textconv` / `--no-ext-diff` / `--diff-filter=AMT` 在 git 2.50 上的实际
   行为与本卡的断言是否一致？特别是：`--text` 是否也覆盖 `-diff` gitattribute 标成二进制的
   情形（本卡只实测了「前若干字节含 NUL」这一种，没实测 `-diff` 属性那一种）？
   `AMT` 的加入会不会让某些本不该进扫描面的改动进来？
5. 「命令名未改 ⇒ 执行位次不变」这条是否仍成立？本卡只加了注释行与块体行，没改 YAML 键名。
6. dash 自证块的取舍声明是否与实现一致？本卡只改了它上方的注释（把「连干净暂存面也会被
   阻断」写实），判定逻辑逐字节未动——请核对注释里的说法与那几行代码确实对得上。

另外欢迎指出：本卡把 awk 的操作数改成 stdin 重定向，而不是卡文原先建议的 `-- "$TMPD/d"`。
理由是本机 awk（version 20200816）实测不认 `--`（报 `can't open file --`，且 `a=b/d` 仍被
当赋值）。这个判断是否正确、是否有更稳妥的写法？

## 四 输出格式

每条发现写成：

```
[级别 BLOCKER/HIGH/MEDIUM/LOW] <一句话结论>
  文件:行  <锚点>
  依据    <你从只读材料里看到的具体事实>
  建议    <最小改法>
```

只读判定不了的，写「未验证」并说明需要什么才能判定。最后给一行
`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**。不要跑 hook、不要暂存任何文件、不要修改任何文件。
- `python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)` 注释段归 T8-G，不在本卡面内。
- `backend/scripts/mutation_kill_identity.py` 与四套变异 harness（g32b / g32cb / g32ccr1 / g33）
  归 T8-B / T8-C，本卡只读运行未改。
- `backend/scripts/lifespan_isolation_negative_control.py` 与 `lifespan_isolation_guard_probes.py`
  归 T8-D，本卡只读运行未改。
- `backend/tests/**` 归 T9 / T10。
- 本卡地盘只有 `lefthook.yml` 一个文件（外加 `_bmad-output/` 下的存档）。
