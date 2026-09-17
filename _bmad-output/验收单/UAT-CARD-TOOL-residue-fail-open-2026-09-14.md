# UAT — CARD-TOOL-residue-fail-open（2026-09-14）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-TOOL-residue-fail-open]` · 车道 **T8**（首卡）
> 车道树 `…/.claude/worktrees/card-t8-tools`（分支 `card/t8-tools`）
> 基线 `08100483`（B14_BASE）→ r1 `cd31cffd` → r2 `f9e31034` → r3 `9020a1a5` → r4 `158e5a60` → **r5 `b09e85e3`**
> 地盘：**只 `lefthook.yml` 一个文件**（外加 `_bmad-output/` 下的存档）。未 push。

---

## 1. 🎯 一句话目标

提交代码前有一道自检，专门拦"把自检工具改坏的痕迹不小心留在代码里"。这道自检以前有**十种情况会一声不吭地放行**——它自己某一步失败了，却照样打印"通过"。本卡把这十种全部改成"拦下来并说清是哪一步没跑完"。

## 2. 📖 你的视角

作为每天要提交代码的人，我想要：提交前那道检查**要么真的检查过了，要么明确告诉我它没跑完**——而不是把"我坏了"和"我没发现问题"说成同一句话。

## 3. 🖥️ 交互流程

```
你在编辑器里改完代码 → 提交
   ↓
屏幕上滚过一串检查名，其中一行是 mutant-residue-scan
   ↓
情况 A：一切正常          → 那行打勾，提交完成（和以前一样）
情况 B：真有残留痕迹      → 那行变红，提交被挡住，屏幕上列出是哪个文件哪一行
情况 C：检查本身没跑完    → ⭐ 本卡的改动：那行也变红，并写明是哪一步没跑完
                            （以前这种情况会打勾放行，你看不出区别）
```

---

## 4-A. 🤖 Claude 已代验（技术项，全部已跑，附存档路径与末行）

> 存档目录：`_bmad-output/审查/evidence-residue-fo/`（后缀一律 `.txt`/`.sh`，无 `.log`，无 `*.stderr*` 入库）

| # | 裁判 | 结果 | 存档（全文件名，不用 glob） |
|---|---|---|---|
| 1 | 第 0 分钟核锚：HEAD=`08100483`、`git status` 空、lefthook `2.1.6` 裸调用 rc=0、基线 `grep -vc '^#'`=**64** | ✅ | `a0-anchors-20260914T195106.txt` |
| 2 | 抽块语法门（锚点现求）`bash -n`/`sh -n` 改前改后各 rc=0 + 坏语法验伪锚 rc=2 | ✅ | `b-syntax-before-20260914T195146.txt` / `r5-b-syntax-20260914T212206.txt` |
| 3 | 十条 fail-open + 追加四条的对照，**16 个 CASE**，每个跑 `bash` 与 `sh` 两种解释器 | ✅ 15 双 SEALED / 6-5 见 §6 | `r5-out-case-*.txt`（逐条见下表） |
| 4 | 允许名单对账：`git grep -l` 每项在 `case…esac` 区间恰 1；验伪锚 `no-such-file.py)`=0；`continue ;;`=7 | ✅ | `r5-judges-20260914T212842.txt` |
| 5 | 注释块对账：5 文件名 + 计数 `151 / 11 / 11 / 2 / 13` 逐项对齐；旧计数 `153`/`10` 残留=0 | ✅ | `j67-allowlist-comment-20260914T200058.txt` / `r5-judges-20260914T212842.txt` |
| 6 | 真 hook 三控（完整绑定存档：lefthook.yml sha256 + HEAD + 探针 blob OID + 完整输出 + rc） | ✅ OK rc=0 / BLOCKED rc=1 / BLOCKED rc=1 | `r5-hook-controls-20260914T212244.txt` |
| 7 | 不碰邻块（承重门）：验伪锚 ≥1 且真判据 **=0**；`python-typecheck` 块与 HONESTY 段逐字节相同 | ✅ | `r5-judges-20260914T212842.txt` |
| 8 | 地盘门 `git diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` → **只 `lefthook.yml`** | ✅ | 同上 |
| 9 | 回归哨兵 `tests/unit`（带 `--ignore tests/unit/test_deploy_vault_sh.py`）对 64 基线 diff **完全为空**；验伪锚有效 | ✅ | `r5-unit-after-20260914T212307.txt` / `r5-j9-j10-20260914T212907.txt` |
| 10 | 四门未被污染 + 11 个受保护文件 sha 对 `08100483` 全 SAME（含零写者 `fsrs_bridge.py`/`decay_beta.py`）+ 验伪锚有效 | ✅ | `r5-j9-j10-20260914T212907.txt` |
| 11 | 自指不变量：`MUT""ANT`=1 / 拼接标记=0 / 命令名=1 / YAML 键 `priority:`=0 | ✅ | `r5-b-syntax-20260914T212206.txt` |
| 12 | Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH=0 | ✅ 见 §5 | `codex-review-CARD-TOOL-residue-fail-open[-rN].md` |

## 4-B. 👤 你来验（3 分钟，全在你平时提交代码的地方完成）

- [ ] 我像平时一样改一点东西然后提交 → 我看到检查照常通过、提交成功 → 我感觉**和以前没有区别**（这一条最重要：这次改动不应该让你多做任何事）
- [ ] 我留意一下检查列表里那一行的名字有没有变 → 我看到它还叫原来那个名字、还在原来的位置 → 我感觉**没有东西被挪动**
- [ ] 如果哪天它真的拦住了我 → 我看到屏幕上明确写着是"发现了痕迹"还是"这一步没跑完" → 我感觉**知道该找谁、该看哪里**，而不是一头雾水

> 这一节全在你平时写代码、提交代码的那个界面里完成，不用去别的地方、也不用看任何记录文件。上面第 3 条大概率你这阵子碰不到——那是好事。

---

## 5. 🚦 验收结果

**Codex `gpt-6-astra` + `ultra`，共 5 轮（上限 5），逐轮收敛：**

| 轮 | 绑定 HEAD | B | H | M | L | 本轮处置 |
|---|---|---|---|---|---|---|
| r1 | `cd31cffd` | 0 | **1** | 2 | 1 | 四条全部实测坐实后整改 |
| r2 | `f9e31034` | 0 | **0** | 2 | 1 | 门已达成；三条仍全部整改 |
| r3 | `9020a1a5` | 0 | 0 | 1 | 1 | 两条全部整改 |
| r4 | `158e5a60` | 0 | 0 | **0** | 1 | Codex：「没有必须继续修改可执行代码才能封住的项」 |
| **r5** | **`b09e85e3`** | **0** | **0** | **0** | **0** | Codex：**「本卡可以收口」** |

- **末轮绑定**：r5 存档正文自证 `复核绑定 b09e85e32f863bd2ee288320342f61d3fa102367；当前 lefthook.yml 与该提交逐字节一致`，且 `b09e85e3` = 车道 HEAD。
- 五份存档首部均含 `模型` / `reasoning_effort` / `codex` 三字段（协议 §2.1），会话头自证抄自各自 `.stderr` 的版本行 / model 行 / reasoning 行并括注行号；`*.stderr*` **不入库**。
- 下一步：本卡独立 commit 且工作树干净，车道串下一张 **T8-B**。

## 6. 九条（+`-s hits`）逐条处置表

> 对照口径：**同一个输入**，旧版块打 `[Mutant-Scan] OK` 且 rc=0，新版块不打 OK 且 rc=1。
> 只证明"新版会红"不算封住。抽块行范围由锚点现求，不写死行号。存档见 `r5-out-case-<id>-20260914T212248.txt`。

| # | 登记的失败形态 | 处置 | 封法 | 对照脚本 | bash / sh |
|---|---|---|---|---|---|
| 6-1 | 单文件 diff 缺 `--no-ext-diff`（外部 diff 接管后 git 仍 rc=0 而正文 0 字节） | **封** | 补 `--no-ext-diff` | `case-6-1-ext-diff.sh` | SEALED / SEALED |
| 6-2 | 缺 `--no-textconv`（textconv 把标记换掉） | **封** | 补 `--no-textconv` | `case-6-2-textconv.sh` | SEALED / SEALED |
| 6-3 | 缺 `--text`（只输出 `Binary files … differ`） | **封** | 补 `--text` | `case-6-3-text.sh` | SEALED / SEALED |
| 6-4 | `--diff-filter=AM` 不含 `T` | **封** | 枚举与单文件 diff 都改 `AMT` | `case-6-4-typechange.sh` | SEALED / SEALED |
| 6-5 | `: > hits` 是全块唯一无显式守卫的一步 | **封（收益如实降级）** | 补 `\|\| { …FAILED…; exit 1; }` | `case-6-5-hits-init.sh` | SEALED / **NOT-SEALED** ⚠️ |
| 6-6 | awk 文件参数形如 `name=value` 被当变量赋值 | **封** | 改 `< "$TMPD/dn"`，不给操作数 | `case-6-6-awk-operand.sh` | SEALED / SEALED |
| 8-1 | 主循环输入重定向打不开 | **封** | 枚举后校验「可读的普通文件」 | `case-8-1-redirect.sh` | SEALED / SEALED |
| 8-2 | 主循环 `read` 报错 | **封** | `SEEN == EXPECTED` + 结束哨兵 | `case-8-2-read-error.sh` | SEALED / SEALED |
| 8-3 | 记录流末条无 NUL 终止 | **封** | 枚举后校验末字节是 NUL | `case-8-3-no-nul.sh` | SEALED / SEALED |
| `-s hits` | `[ -s ]` 为假被当成「没有命中」 | **封** | 为假时追核 `hits` 仍是可读普通文件 | `case-9-s-hits.sh` | SEALED / SEALED |

**复核期追加的四条**（Codex 在本卡的封堵之上又找出来的，同样逐条封 + 配对照）：

| # | 来源 | 失败形态 | 封法 | 对照脚本 | bash / sh |
|---|---|---|---|---|---|
| h1 | r1 HIGH | 同一行内 NUL 在标记**之前**：awk 字符串是 NUL 终止的，`--text` 拿回了完整字节而 awk 只看到 NUL 之前那截 | 喂 awk 前 `LC_ALL=C tr '\000' '?'` 等长归一化 | `case-h1-nul-before-marker.sh` | SEALED / SEALED |
| m2 | r2 MEDIUM | 空清单 + read 报错 ⇒ `SEEN==EXPECTED==0` 仍通过 | 结束哨兵 `/__mutant-scan-eof__` 必须真被读到 | `case-m2-empty-read-error.sh` | SEALED / SEALED |
| m3 | r2 MEDIUM | `d` / `dn` 被换成 `/dev/null` 之类，整份 diff 写丢而每步 rc=0 | 写后核「是可读的普通文件」 | `case-m3-dn-dev-null.sh`（`d`/`dn` 两变体） | SEALED / SEALED |
| m4 | r3 MEDIUM | `dn` 是指向 `d` 的链接 ⇒ `< d > dn` 在读之前把同一 inode 截空 | 加 `[ "$TMPD/d" -ef "$TMPD/dn" ]` | `case-m4-d-dn-same-inode.sh`（符号/硬链接两变体） | SEALED / SEALED |

另有 r2 MEDIUM「循环内 git 共享记录流 stdin」→ 循环内 git 加 `</dev/null`（无独立对照；它要求一个会消费 stdin 的 git 包装层，本卡未造；如实登记）。

> ⚠️ **6-5 的收益如实降级**：`:` 是 POSIX 特殊内建，在真实 runner（lefthook 起 `sh -c`，本机解析到 bash 的 POSIX 模式）下这一步重定向失败**本来就会退出 shell**、rc=1（只打一句 `Permission denied`）。所以这条守卫在真实 runner 下的收益是「把静默退出变成有诊断的阻断」，**不是**「把放行变成阻断」；只有在普通 `bash` 下它才真是把 fail-open 变 fail-closed。已写进块内注释。

## 7. 允许名单 before / after

| | 条目 |
|---|---|
| **before（2 项 + 1 glob）** | `g32b_mutation_gates.py` / `g32cb_mutation_gates.py` / `_bmad-output/*` |
| **after（5 项 + 2 glob，`continue ;;` = 7）** | 上述三条 + `backend/scripts/g32ccr1_negative_controls.py` / `backend/scripts/openapi_drift_negative_control.py` / `backend/tests/regression/recap_domain_negverify.py` / `.claude/rules/*.md` |

- 补的三个脚本此前**不在**名单里 ⇒ 它们一旦被暂存修改就会被这道门拦下（fail-closed 误伤）。方向相反的对照（旧版 BLOCKED rc=1 / 新版 OK rc=0）见 `r5-out-case-e-allowlist-20260914T212248.txt`。
- **匹配面实测并写进注释**：`case` 的 `*` **会匹配 `/`**，故 `.claude/rules/*.md` 覆盖该目录下**任意深度**的 `.md`（与既有 `_bmad-output/*` 同口径）。五条验伪锚仍被两版都拦下：`…_copy.py`、`.md.bak`、`notes.txt`、`.claude/rulesX/a.md`、`docs/.claude/rules/a.md`。

### ⚠️ 待用户确认（独立一行）

**`.claude/rules/*.md` 入允许名单 = 按默认补，待用户确认。** 依据：手册 §零.7 / 协议「`.claude/rules/*.md` 不在 `mutant-residue-scan` 允许名单」——本批任何卡在规则文里写残留标记字面量都会被这道门拦下（第十二批复核报告 §五.10 已登记）。当前三份规则文的标记计数实测为 `0 / 0 / 0`，即**现在还拦不到它们**，补名单是前瞻性的。若用户不认可，删掉那一条 `continue ;;` 即可，不影响其余九条封堵。

### ⚠️ T8-G patch（独立一行）

**T8-G 的 `CARD-PYRIGHT-GATE` patch 由主 session 在本卡之后套用。** HONESTY 注释里那半句过时文字在 `:134-135`（`backend/pyproject.toml` 不存在，pyright 声明在根 `pyproject.toml`），归 T8-G 的同一份 patch，本卡**只登记不改**；已用逐字节比对自证 `python-typecheck` 块（:205 起 27 行）与 HONESTY 段（:133 起 13 行）与 `08100483` 相同。

## 8. 本卡未证明什么

1. **不检测无标记的变异残留。** 这道门只是最弱那层网；唯一可靠的锚点仍是「跑前对所有会被变异的文件取全文件 sha 基线、跑完逐个复核」。块内 `HONESTY CONTRACT` 段（:302 起）已写明这一点，本卡一字未改。
2. **非 macOS、以及 `/bin/sh` 不是 bash 的环境未验证。** dash 分支只有块内自证段，没有真环境实测。本机 `sh` 实测是 bash 3.2.57；lefthook 起的 `sh` 由其进程 PATH 查找，**不是**硬编码 `/bin/sh`。
3. **子模块与符号链接两类没有真实暂存对照。** `T`(typechange) 有对照但只在临时仓里做（`case-6-4`），不是在本仓的真实暂存面上。
4. **不证明 lefthook 1.13.6（npx）下的行为。** 本卡一切验证只用 `/opt/homebrew/bin/lefthook` 2.1.6 裸调用。
5. **不证明 `.claude/rules/*.md` 入名单是用户想要的**（按默认补，见 §7 待裁）。
6. **不改 `python-typecheck` 块，因此不证明 pyright 门的任何性质**；本卡也未跑 pyright（不触 `backend/app`）。
7. **不动 T8-B/C 的四套 harness 与 `mutation_kill_identity.py`、不动 T8-D 的负控脚本**——只读运行，跑前跑后 sha 全 SAME。
8. **以下放行路径本卡封不住，如实登记**（r5 存档 §4 的分类）：扫描时点限制（枚举与逐文件读取之间索引变化、扫描后再次暂存）；临时对象被**持续并发**替换；git / awk 等工具本身被替换成伪造结果并返回 0。本卡封住的是「有限预置故障」那一类（m3 / m4 即其实例）。
9. **两处 `$(LC_ALL=C tr -d ' \n' < …)` 的 rc 未单独核**（`tr` 先输出后报错，可能既给出有效数字又非零退出）。兜底是 `!= "0"`、`EXPECTED` 的 `case` 校验与末尾 `SEEN/EXPECTED` 比较，那是**部分**兜底，不是与核 rc 等价的保证。块内注释已逐条列清 rc 覆盖面。
10. **`case-e-allowlist.sh` 只跑 bash**（其余 14 条跑双解释器）。允许名单的匹配是 `case` 语句语义、与解释器无关，故未跑双解释器——脚本内已如实声明，不当双解释器证据。

## 9. 台账待登记条目（车道不改台账，请主 session 登记）

1. **Y4-C 行补**：「存量 fail-open 六 + 三 + `-s hits` 共十项**全部封**，各配一条『旧版 OK rc=0 / 新版 rc=1』对照；复核期 Codex 又追出四条同族缺口（h1 / m2 / m3 / m4）亦全部封 + 配对照。16 个 CASE：15 个双解释器 SEALED，6-5 `bash=SEALED / sh=NOT-SEALED`（收益降级见 §6）。」
2. **允许名单由 2 项补到 6 项**（三个负控本体 + `.claude/rules/*.md`），**且 `.claude/rules/*.md` 待用户确认**。
3. **`:312-314` 注释数字更正**：g32b `153 → 151`、g32cb `10 → 11`（后者 U8-C 已登记，前者是 recon_C §2.2 新发现）；并补齐五项文件清单与各自计数（`151 / 11 / 11 / 2 / 13`，`08100483` 实测）。
4. **`:330-332` 的 `-z + tr` 注释更正** + dash 自证块取舍声明写实（「连干净暂存面也会被阻断」是明知的取舍，「跨平台正常提交不受影响」那句不成立）。
5. **T8-G 的 lefthook patch 待主 session 在本卡之后套用**；HONESTY 过时半句在 `:134-135`，归 T8-G。
6. **lefthook 双版本口径（R-B14-1）**：`--no-auto-install` 是 1.x flag，brew 2.1.6 实测报 `Incorrect Usage … -no-auto-install` 且 rc=1；本卡一切验证一律**绝对路径裸调用**。U8-C 原卡与第十三批手册的旧口径作废。
7. **本卡未做真实暂存对照的三类面**：子模块 / 符号链接 / `T`（后者只在临时仓里做过）。
8. **裁判 8 的四个词在 `lefthook.yml` 里非 T8-G 面独有**：`HONESTY` 在 `:133`（T8-G 面）与 `:302`（本块自己的注释头），`python-typecheck` 在 `:8` / `:138` / `:205`。门命中需先按行号分诊；本卡实测真判据 = 0。
9. **⚠️ 新登记 — 卡文推荐的 6-6 封法之一无效**：卡文 (c) 建议「把 awk 的文件参数改成 `-- "$TMPD/d"`」。本机 awk（`version 20200816`）**不认 `--`**：实测 `awk '…' -- 'a=b/d'` 报 `can't open file --` 且 `a=b/d` 仍被当变量赋值。另一个建议（`cd "$TMPD"` 后用 `./d`）会把循环内 git 的 cwd 一起改掉，同样不可用。本卡改用 stdin 重定向（不给操作数）。**后续卡文不要再照抄那两个写法。**
10. **⚠️ 新登记 — 零暂存面下 lefthook 把整块 skip 掉**：实测 `mutant-residue-scan (skip) no matching staged files`，根本不打印 `[Mutant-Scan] OK`。卡文裁判 4 写的「干净暂存面」必须理解为「暂存面**非空**但不含标记」，否则那是一条永远看不到 OK 的死判据。
11. **⚠️ 新登记 — 工具链**：(a) 用户级 `guard-hook.sh` 拦截行首/管道后的裸 `rm`，本卡撤探针改用 `/bin/rm -f <绝对路径>`（窄口径、单文件、已在此登记）；(b) **zsh 里给变量 `path` 赋值会直接覆盖 `PATH`**（`path` 与 `PATH` 绑定）——本卡因此有一次判据整批 `command not found`，已弃跑重来，判据本身未改；(c) 负控 B 的探针含 NUL，`ruff` 报语法错误时原样回显，**含 NUL 的文档会被 git 判成二进制、diff 里看不到内容**，三控存档已把 NUL 等长换成 `?` 并写明。
12. **⚠️ 新登记 — `.claude/rules/*.md` 的匹配面比字面更宽**：`case` 的 `*` 匹配 `/`，故它覆盖该目录**任意深度**的 `.md`（与既有 `_bmad-output/*` 同口径）。已写进注释并配五条验伪锚。

## 10. 🔗 技术引用

- 卡文：`…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T8-A.md`
- 排批期裁定：`…/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-14-第十四批排批期裁定-R-B14.md`（适用 R-B14-1 / R-B14-2 / R-B14-3 / R-B14-11）
- Codex 存档：`_bmad-output/审查/codex-review-CARD-TOOL-residue-fail-open.md` / `-r2.md` / `-r3.md` / `-r4.md` / `-r5.md`
- Codex prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-TOOL-residue-fail-open.md`（及 `-r2` ~ `-r5`）
- 对照脚本与存档：`_bmad-output/审查/evidence-residue-fo/`
- 改动面：`lefthook.yml` 的 `mutant-residue-scan` 块及其上方注释段（行号随本卡改动位移，一律用锚点定位：`--- Mutant residue scan` / `mutant-residue-scan:` / `Mutant-Scan] OK`）
