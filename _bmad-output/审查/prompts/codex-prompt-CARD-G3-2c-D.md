你是本次工作的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line
与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c`

⚠️ **本轮不审 harness 本体**（`g32b_mutation_gates.py` 一个字节没改，请自行 `git diff` 确认）。
本轮只审两件事：

1. **`M2b-R2-drop-utc-offset-check` 的裁定**是否站得住；
2. **138 条全量杀灭表的定性**是否如实、有没有把「没测到」说成「测过了」。

证据文件（都在 `_bmad-output/审查/evidence-g32b/`）：
- `g32b-full-run.txt` —— 单进程串行一次跑完的原始输出；
- `kill-table-138.md` —— 我按 `MUTATIONS` 顺序整理的 138 行杀灭表；
- `sha-before.txt` / `sha-after.txt` —— 四个生产文件跑前跑后的 SHA-256。

本卡的**代码改动为零**：`git status --porcelain` 只有上述证据目录。

## 背景

`g32b_mutation_gates.py` 有 138 条变异，每条「故意弄坏一处防线，看指定的那道门会不会变红」。
上一张卡（X7-C）跑到中途出过事故：用 `pgrep -f` 判进程存活时**自匹配**（模式串出现在自己的
命令行里）导致误判「进程已死」，于是又起了一个，**两个进程同时原地变异同一批文件**，
回归从 `330 passed` 掉到 `7 failed`。那次中断前看到 `M2b-R2-drop-utc-offset-check`
**SURVIVED**，悬而未决——如果属实，说明它绑定的门
`test_r2_non_whole_second_durable_review_time_fail_closed` 是一道**假门**。

## 本次结果

- 单进程、`nohup`、串行一次跑完；存活判据用 `ps -ax -o args= | grep -F`（不再用 `pgrep -f`）。
- **KILLED 134 / SURVIVED 0 / ANCHOR-ERROR 4，合计 138。**
- 四个生产文件跑前跑后 SHA-256 **逐字节相同**（`diff sha-after.txt sha-before.txt` 为空）。

### 我对 `M2b` 的裁定（请重点复核）

**它这次是 KILLED，不是 SURVIVED。** 两次独立观测：
1. 全量跑里：`[M2b-R2-drop-utc-offset-check] test_r2_non_whole_second_durable_review_time_fail_closed → KILLED (1 failed)`；
2. 我另做了一次单条复现（同一 `MUTATIONS` 条目，mutate→run→restore）：绿态前提 `rc=0`，
   变异后 `rc=1` KILLED，还原后 `SKILL.md` 的 SHA-256 与跑前相同。

因此我判：那道门**不是假门，它承重**；上次的 SURVIVED **未能复现**。
对上次那个观测，我给的解释是「并发污染下变异可能根本没生效」——
⚠️ 这是**推断**，不是证明：那次的现场已经不存在了。

### 4 条 ANCHOR-ERROR 的定性（请重点复核）

「锚点命中 0 次」= 变异**没有写进文件** ⇒ 那一条**什么都没测**。四条都是锚点指向
round-17 **之前**的旧代码：

| tag | 锚点（旧） | 现状 | 我的定性 |
|---|---|---|---|
| `M142-dup-uses-global-w` | `bool(_rc_dup_applied) if _rc_dup is not None` | `SKILL.md:2098` 现为 `(_rc_dup_applied is True) if _rc_dup is not None` | 锚点漂移；那段赋值逻辑仍在 `:2097-2100` |
| `M143-missing-applied-flag-tolerated` | `if _rc_dup is not None and _rc_dup_applied is None:` | `:2085` 现为 `... and _rc_dup_applied is False and W_inst is not None ...` | 锚点漂移；该性质现由 `type(_rc_dup_applied) is not bool` 那道判据承担，`g32cb` 的 M1 打它并 KILLED |
| `M145-recovery-does-not-promote-flag` | `fm = _fa_pat.sub(lambda m: m.group(1) + "true", fm, count=1)` | 已抽成函数 `_promote_applied()`（`:463` 定义，`:2486` / `:2609` 调用）| 锚点漂移（重构）；`g32cb` 的 M2 打该性质并 KILLED |
| `M157-anchor-direction-unchecked` | **主锚命中 1**，失败的是**同层锚** `and _na_a >= …` | 同层锚命中 0 | 层锚漂移；主性质由 `g32cb` 的 M3 承重并 KILLED |

另有 2 条 `kind="complete"` 的层声明问题（`M100-no-tri-instant-binding`、
`M151-exam-board-bare-json-in-yaml`）：脚本报「声明为 complete 但变异体单独即可杀
⇒ 层是多余的」。我的定性是**层声明过度**，不是防线缺陷。

**本卡不修这 6 条**（卡文硬边界：不改 g32b 的判据逻辑 / 不删变异凑全绿），只定性 + 移交。

## 请重点回答的问题

1. **`M2b` 的裁定是否站得住**：请自己按 `MUTATIONS` 里那一条做一次 mutate→run→restore，
   确认它 KILLED，并说明**失败的是哪一条断言**。如果你能让它 SURVIVED，请说明条件。
2. **「上次是并发污染」这个解释**：我明说了它是推断。你认为还有别的、同样能解释
   「当时 SURVIVED、现在 KILLED」的原因吗？（例如那期间生产代码被改过。）
   如果有，请指出可查证的痕迹。
3. **4 条 ANCHOR-ERROR 的定性是否准确**：逐条核对锚点文本与当前代码，确认
   「锚漂移、防线仍在」这个判断；特别是我说「该性质由 g32cb 的 M1/M2/M3 承重」，
   请核对那三条打的是不是**同一处**防线——如果不是同一处，我的说法就过宽了。
4. **杀灭表有没有把「没测到」说成「测过了」**：`kill-table-138.md` 里 134 条 KILLED
   是否都能在 `g32b-full-run.txt` 里找到对应行？有没有 tag 被算了两次或漏算？
5. **零污染的证据是否充分**：我用的是四个文件的全量 SHA-256 前后比对，而不是
   `grep MUTANT`。这个判据够不够？有没有它看不见的污染面？
6. **138 这个总数**：请自己从 `MUTATIONS` 数一遍，确认是 138，且杀灭表逐条对得上。

## 我已经跑过的（请独立复核，不要采信）

- 全量：`KILLED 134 / SURVIVED 0 / ANCHOR-ERROR 4`，合计 138。
- 四文件 SHA-256 跑前跑后 `diff` 为空。
- `git status --porcelain` 只有证据目录；`grep -rn 'MUTANT' canvas-vault/` = 0。
- `M2b` 单条复现：绿态 `rc=0` → 变异 `rc=1` KILLED → 还原 sha 相同。

## 输出格式

先给一行结论（`通过` / `需整改`），然后按 `[级别] file:line — 一句话` 列出问题，
每条附你的观测值与可执行的建议。级别用 BLOCKER / HIGH / MEDIUM / LOW。
判断标准以「有没有把『没测到』写成『测过了』」为最高优先级；
其次是「`M2b` 的裁定会不会掩盖一道真的假门」。
