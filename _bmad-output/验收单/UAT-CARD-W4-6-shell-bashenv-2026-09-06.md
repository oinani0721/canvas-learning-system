# UAT · CARD-W4-6-shell-bashenv

> 批次: `BATCH-2026-09-05-第十二批` · 车道 `Y7-B`（`card/y7-w4-settle`）
> 开工 SHA: `39407e97`（Y7-A = CARD-W4-4-settle-atomic 的收工 commit）
> 本卡 commit: `4d56beb0`（round-1，Codex 审的就是它）+ `03e96721`（round-2，Codex 整改）+ round-3（对抗复核整改）——后两者均在 Codex 审后，见 §九.1 失绑声明
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y7-B.md`
> 证据目录: `_bmad-output/审查/evidence-w4-6/`

## 〇 一句话

那道「跑测试有没有偷改生产数据」的门，原先声称会在重启自己时把调用者注入的 shell
函数摘干净——**实际上一个都没摘**（用错了枚举方式），今天全靠第二道防线兜住；而且
调用者只要设一个环境变量就能让整段清洗被跳过。本卡把这两件事都修好，并补了 13 条
探针把它们钉住；复核过程中又查出并修掉一个**存量**的静默假红（`SHELLOPTS`）。

## 一 DoD-3 双段

### 1-A 用户能看见什么（产品体验口径）

**无变化。** 那道「测试有没有偷改数据文件」的检查，结论和以前一样（`RUNTIME-FILES:
unchanged`）。差别在它现在是**在真正干净的环境里**得出这个结论的，而且别人不能靠设
一个环境变量让它跳过清洗。跑测试的命令、输出格式、退出码都没变。

### 1-B 技术上改了什么

| # | 改动 | 位置 |
|---|---|---|
| 1 | `BASH_FUNC_*` 收集不再用 `compgen -e`（它看不见 `BASH_FUNC_f%%` 这种名字），改为枚举 `/usr/bin/env -0` 的 NUL 分隔条目 | `runtime_sha.sh` exec 段 |
| 2 | 重入标记从环境变量 `W4_SHA_GATE_REEXEC=1` 改为 argv 前哨 `--w4-reexec <串>` + PID 一致性比对；比对通过后再验环境（`BASH_ENV`/`ENV` 为空、无 `BASH_FUNC_*` 残留） | 同上 |
| 3 | 拒绝路径进入即 `builtin trap -`（否则落在注入者 `EXIT` trap 射程，rc 被改写成 0） | 同上 |
| 4 | 环境枚举补完成哨兵：枚举失败/截断与「零个残留」区分开，fail-closed | 同上 |
| 5 | `exec`/`export`/`unset`/`trap` 一律加 `builtin` 前缀（裸 `exec` 可被同名函数劫持） | 同上 |
| 6 | 注释改到不宽于实现（含把「5 条 / 11 条 / 15 条探针」的数字错误改成逐条列名） | `runtime_sha.sh` 前言 |
| 7 | exec 参数补 `-u SHELLOPTS -u BASHOPTS`：修掉**存量**的静默假红（见 §二.4） | `runtime_sha.sh` exec 段 |
| 8 | 两趟枚举的完成检查**分开钉**（`-pass1` / `-pass2` 两条探针 + 检查站点锚） | `guard_probes.py` |
| 9 | 花名册门：把「由 **N 条** shell 探针承重」这句声明变成 AST 判据 | `guard_probes.py` |
| 10 | `probe_shell_injections()` 新增 13 条探针（6 → 19 条 shell 探针，总数 41 → 54） | `guard_probes.py` |

**唯一 hunk**：`guard_probes.py` 的全部改动落在 `probe_shell_injections()` 函数体内
（`git diff -U0` 只有一个 `@@ … def probe_shell_injections()` 的插入 hunk）。
`main()` / `live_port_guard.py` / `conftest.py` / `guard_plugin.py` / `negative_control.py`
零改动。

## 二 改前的缺陷是**实测复现**的，不是推理

### 2.1 exec 层对 `BASH_FUNC_*` 不承重

```
/bin/bash --noprofile --norc -c 'f(){ :; }; export -f f;
    /usr/bin/env | grep "^BASH_FUNC"; builtin compgen -e | grep -c BASH_FUNC'
→ BASH_FUNC_f%%=() {  :        ← env 看得见
→ 0                            ← compgen -e 一个都数不出来
```

旧实现按 `compgen -e` 的输出找名字 ⇒ `__unset_args` 恒为空串 ⇒ `env -u BASH_ENV -u ENV`
一个导出函数都没摘。**决定性对照**（`evidence-w4-6/e-before-after-*.txt`）：同样注入、
同样拆掉第二层 `unset -f` 循环的门副本——

* before（`39407e97` 的门，sha `280cfadb…998a`）→ `RUNTIME-FILES: GATE-BROKEN — 清不掉的 shell 函数仍在: dirname printf`、rc=1
* after（本卡的门，定稿 sha `6ccae56c…42ae`）→ `RUNTIME-FILES: unchanged`、rc=0

拆的是**另一层**（第二层），不是把被测物改坏，所以 after 的绿只可能来自 exec 层。

### 2.2 哨兵可被调用者照抄

```
W4_SHA_GATE_REEXEC=1 BASH_ENV=<readonly -f 注入文件> bash 门 -- /usr/bin/true
→ RUNTIME-FILES: GATE-BROKEN — 清不掉的 shell 函数仍在: dirname     rc=1
```

整段清洗被跳过，`readonly -f` 的注入函数活到第二层，`unset -f` 对它失败。**不是假绿，
但一个环境变量就能让这道门罢工。** 修复后同一条命令 → rc=0 + 真实监视路径 + `unchanged`。

### 2.3 本卡 round-1 自己引入的两个面（如实登记，已在 round-2 修掉）

| 面 | 实测 before | 处置 |
|---|---|---|
| 伪造标记的拒绝路径落在注入者 `EXIT` trap 射程 —— stderr 打了 GATE-BROKEN，trap 随后打印 `RUNTIME-FILES: unchanged` 并把 **rc 改写成 0** | `evidence-w4-6/a-selftest-exit-trap-*.txt` A1/A2 | 进入该分支先 `builtin trap -`；探针 `shell-forged-ticket-under-exit-trap` 钉住 |
| 按行扫 `env` 无法区分「条目边界」与「值里的换行」⇒ 一个**普通**多行环境变量就让正常调用 GATE-BROKEN（**假红**，不需要任何注入） | `CARRIER=$'harmless\nBASH_FUNC_notafunction%%=whatever' bash 门 -- /usr/bin/true` → rc=1 | 改 `env -0` NUL 分隔；探针 `shell-multiline-env-var-not-mistaken-for-func` 钉住 |

第一条是我自己对抗自测抓到的（Codex 没提）；第二条是 Codex round-1 MEDIUM-1 抓到的。

### 2.4 对抗复核抓到的**存量**缺陷：`SHELLOPTS` 让门方向反了（本卡顺手修掉）

bash 启动会读环境里的 `SHELLOPTS` 并置位对应选项，而本文件的 `set -uo pipefail`
**只加不减**，关不掉它。实测（`evidence-w4-6/shellopts-*.txt`）：

| 命令 | 结果 |
|---|---|
| `SHELLOPTS=errexit /bin/bash --noprofile --norc -c 'set -o \| grep errexit'` | `errexit on`（确实被导入） |
| `builtin compgen -A function`（函数表**空**时） | rc=**1** |
| `set -o pipefail; x="$(compgen -A function \| tr …)"` | 赋值 rc=**1** |
| `SHELLOPTS=errexit bash 门 -- /usr/bin/true`（**开工 SHA** 的门） | rc=1、**零输出** |
| 同上（本卡 round-2 的门） | rc=1、**零输出** |
| 同上（本卡 round-3 修好后） | **rc=0** + `RUNTIME-FILES: unchanged` |

**方向是反的**：函数表干净（= 正常情形）才死在第二层 `__leftover=` 那句；留着清不掉的
函数（= 异常情形）时 `compgen` rc=0，反而顺利走到 GATE-BROKEN 把话说出来。而 rc=1
正是门文档里「文件被改」的码 —— 调用方会把「门被环境噎死」读成「运行时数据被动过」。

**这是存量缺陷，不是本卡引入**（开工 SHA 同样复现）。修法是在 exec 参数里
`-u SHELLOPTS`（顺带 `-u BASHOPTS`），一行，落在本卡本来就拥有的那个列表里。
探针 `shell-shellopts-errexit-does-not-false-red` + 变异 `M-shellopts-strip` 钉住。

## 三 每条判据都做了**定向拆门**实测（「跑了没红」不算门成立）

`evidence-w4-6/branch-mutation-harness.py` —— 只在 **after 基线**上动一处，每次拆掉
**一条**判据，断言**指定的那一条**探针翻红。三态判定（`ANCHOR-DRIFT` / `NO-OP` /
`SYNTAX-INVALID` / `SURVIVED` / `KILLED`），跑前跑后基线门 sha256 逐字节相同。

| 变异 | 期望翻红 | 结果 | 本轮实际红 |
|---|---|---|---|
| `M-exec-collect`（exec 层不摘 `BASH_FUNC_*`） | 三条 exec 层探针 | KILLED | 3 条 + 5 条连坐 |
| `M-ticket-check`（拆 PID 一致性比对） | `shell-reexec-sentinel-forged` | KILLED | **恰好 1 条** |
| `M-bashenv-check`（拆 `BASH_ENV`/`ENV` 检查） | `shell-forged-ticket-with-injection-refused` | KILLED | **恰好 1 条** |
| `M-exported-func-check`（拆导出函数残留检查） | `shell-ticket-ok-but-exported-func-refused` | KILLED | **恰好 1 条** |
| `M-trap-clear`（拆拒绝路径清 trap） | `shell-forged-ticket-under-exit-trap` | KILLED | **恰好 1 条** |
| `M-nul-delimited`（忠实退回按行扫，生产端+消费端同改） | `shell-multiline-env-var-not-mistaken-for-func` | KILLED | 1 条 + 1 条连坐 |
| `M-enum-sentinel`（让**两趟**枚举完成检查恒真） | `…-pass1` + `…-pass2` | KILLED | 2 条 |
| `M-enum-check-pass2-only`（只拆第二趟的拒绝动作，保留 case 形状） | `…-pass2` | KILLED | **恰好 1 条** |
| `M-shellopts-strip`（不摘 `SHELLOPTS`） | `shell-shellopts-errexit-does-not-false-red` | KILLED | **恰好 1 条** |
| `M-roster-count`（把门头声称的条数改错） | `shell-probe-roster-matches-declared-count` | KILLED | **恰好 1 条** |

**KILLED 10/10**（存档 `evidence-w4-6/mut-branches-r4-*.txt`）。其中**七条是精确单杀**
——这正是「判据绑定被哪一层拒的」需要的证据（Codex MEDIUM-2 / MEDIUM-3 与对抗复核
F1b 的直接整改）。

两处连坐的解释（不是同源就得说清楚）：

* `M-exec-collect` 连带四条既有 pipeline 探针 + `shell-reexec-sentinel-preset` 变红：因为
  第二趟的环境自洽检查**同时也是第一趟工作成果的复核**——`BASH_FUNC_*` 没被摘掉时，
  它在正常路径上就会 GATE-BROKEN。这是设计内的额外强度，不是判据串味。
* `M-nul-delimited` 连带 `…-pass1` / `…-pass2` 两条变红：它们的锚点是 `env -0` 那段文本，
  变异体里已不存在 ⇒ 探针**自报锚点脱节 FAIL**，拒绝在看不见目标时报绿。设计内行为。

### 三.1 两次**假杀**的更正（同一形态犯了两回，写下来免得后人重犯）

| # | 变异 | 初版怎么错的 | 修法 |
|---|---|---|---|
| 1 | `M-nul-delimited` | 只把消费端 `read -r -d ''` 改回 `read -r`，生产端仍是 `env -0` ⇒ NUL 流被按行读，完成哨兵永远读不到，门死在「环境枚举未完整产出」。指定探针**确实翻红**，但红的原因不是它声称的那条 | 生产端与消费端同改，变异体是**忠实的旧设计** |
| 2 | `M-enum-check-pass2-only` | 把整个 `case "$__w4_env_ok" in … esac` 删掉 ⇒ 探针的**锚点自检**（`_check_hits == 2`）先失败，`-pass1` 与 `-pass2` **两条**都以「锚点脱节」报红，而不是各自的行为断言 | 只把第二趟的**拒绝动作**换成空分支，`case` 形状原样保留 ⇒ 现在是 `-pass2` 单红 |

**共同规矩**：变异只能拆**被测的那道防线**，判据赖以成立的脚手架（锚点、形状、
上游产物）必须原样留着。verdict 字母对不代表因果链对 —— 判定 KILLED 之前必须能说出
「红的是哪一条断言」。

## 四 裁判（只引用路径与末行）

| 裁判 | 存档 | 末行 |
|---|---|---|
| J1 探针 | `evidence-w4-6/j1-guard-probes-r3-*.txt` | `GUARD-PROBES: PASS — 54/54 条全部 fail-closed` / `rc=0` |
| 解释器选项面（存量） | `evidence-w4-6/shellopts-interpreter-opts-*.txt` | 见 §二.4 与 §五.10 |
| J2 只读实证 + 被包裹命令函数表 | `evidence-w4-6/j2-j3-j4-r2-*.txt` | `BASH_FUNC_f%%=() {  :` / `0`（与修复前相同）；被包裹命令 `type -t` → `builtin` / `file`（不含 `function`） |
| J3 哨兵预设 | 同上 | `RUNTIME-FILES: unchanged` / `rc=0` |
| J4a 门包 `pytest tests/api` | `evidence-w4-6/j4-api-regression-r3-*.txt` | `268 passed` + `RUNTIME-FILES: unchanged` |
| J4b/J4c | `evidence-w4-6/j2-j3-j4-r2-*.txt` | `unchanged`/rc=0；无 `--` → `用法:` / rc=2 |
| J5 CHANGED 面 + glob 族 | J1 存档内 | `shell-can-report-changed` / `shell-selftest-load-bearing` / 6 条 `runtime-glob-*`·`runtime-legacy-journal-watched` 逐行 `[PASS]` |
| J6 常量不动 + sha | `evidence-w4-6/j6-constants-*.txt` | 见 §四.1 |
| J7 工作树/hunk 归属 | `evidence-w4-6/j6-j7-*.txt` | 单 hunk 在 `probe_shell_injections()` 内 |
| before/after | `evidence-w4-6/e-before-after-final-*.txt` | before 红 9/10、after 红 0/10 |
| 定向变异 | `evidence-w4-6/mut-branches-r4-*.txt` | `KILLED 10/10`；跑后基线门 sha 与跑前相同 |
| 对抗自测（EXIT trap） | `evidence-w4-6/a-selftest-exit-trap-*.txt` | A1/A2 rc=0（缺陷）→ C1/C2 rc=1（修好） |

### 四.1 J6 常量不动（卡文原判据会数上下文行，此处给修正版）

卡文写的 `git diff … | grep 'SELFTEST_EXPECTED\|WATCHED_\|EXPECTED_'` **不为空**——但命中的
是一行**上下文**（`#  监视面 = WATCHED_FIXED 的固定项 + WATCHED_GLOBS …`，diff hunk 自带的
±3 行上下文），不是变更行。修正判据只看 `^[+-]` 且排除 `---`/`+++` 头 ⇒ **空**。另加两条
独立证据：

* 五个常量行在 before/after 上逐行**完全相同**（`SELFTEST_EXPECTED='82e87819…baa1c'` /
  `WATCHED_FIXED=(` / `WATCHED_GLOBS=(` / `EXPECTED_FIXED_COUNT=3` / `EXPECTED_GLOB_COUNT=1`）；
* `WATCHED_FIXED=(` 到 `EXPECTED_GLOB_COUNT=` **整块** sha256 前后相同：
  `98a208684177ddd1154a2145cf3621c3f479c2a56cc3d4c5772ccee2e061467b`。

### 四.2 sha256（改前 / 改后）

| | 值 |
|---|---|
| 改前（`39407e97`） | `280cfadb874845cd3cf7e30e0a707f8ebb0a5c2629a43636485045886a5a998a`（与卡文一致） |
| 改后（本卡定稿） | `6ccae56c4697b4db33681470d6f73eaef0cd5e59664e257ebdca5978e6da42ae` |
| round-1（`4d56beb0`，仅供追溯） | `d033b19fbd5228da4dc9aa3bde50d8c5aad704c9217451fa7cf123af6d905277` |
| round-2（`03e96721`，仅供追溯） | `6d206df8eaea6e68c3da94f0dbdac8848f0080fa5efd3d6ceba648bb7fdb53b7` |

### 四.3 before/after 的红要**分类**看（Codex MEDIUM-3 整改）

本卡新增 10 条，before 侧红 9 条。但它们的红**不是同一回事**：

| 类别 | 探针 | before 红的原因 |
|---|---|---|
| **旧门真实缺陷显形** | `shell-bash-env-exec-layer-is-load-bearing` / `shell-exec-strips-readonly-func` / `shell-wrapped-cmd-sees-no-injected-func` / `shell-reexec-sentinel-preset` | 导出函数没被摘 / 预设环境变量跳过清洗 ⇒ GATE-BROKEN |
| **协议差异**（只算新协议回归测试） | `shell-reexec-sentinel-forged` / `shell-forged-ticket-with-injection-refused` / `shell-ticket-ok-but-exported-func-refused` / `shell-forged-ticket-under-exit-trap` / `shell-env-enum-failure-is-fail-closed` | 旧门不认识 `--w4-reexec`（rc=2 用法错误）／旧门没有那段代码（锚点脱节） |
| **不红**（本卡自伤回归门） | `shell-multiline-env-var-not-mistaken-for-func` | 旧门根本不扫环境残留，扫不出假红。它防的是**本卡自己**可能引入的回归，承重证据来自 `M-nul-delimited`（KILLED） |

**这五条协议差异的承重证据来自 §三 的定向变异，不来自 before/after。** 把「参数不认识」
说成「旧缺陷复现」是不成立的，harness 的 docstring 已同步改口径。

## 五 本卡未证明什么（如实）

1. **跨 bash 版本**：本机 `command -v bash` 只有 `/bin/bash`（3.2.57(1)-release,
   arm64-apple-darwin25），`/opt/homebrew/bin/bash` 不存在，**没有第二个 bash 可对照**。
   「bash 4.3+/5.x 的导出函数变量名同为 `BASH_FUNC_x%%`、`compgen -e` 同样看不见」是
   **跨版本推断，未验**。
2. **`env -0` 的可移植性**：`-0` 是 BSD/GNU 扩展，非 POSIX 必备。本机 `/usr/bin/env -0`
   实测可用；**别的平台未验**。不可用时不会静默降级（完成哨兵读不到 ⇒ GATE-BROKEN），
   但那等于门在那台机器上停摆——这一面只做了 fail-closed，没做兼容。
3. **PID 标记的残余可伪造面（没关掉）**：调用者自己 `exec` 本脚本继承 PID、猜中 PID、
   或进程起来后再拼 argv，标记都能对上。本卡只关掉「照抄一个常量」这条**不需要任何前置
   能力**的路。危害被环境自洽检查缩小，但**没有消除**。
4. **环境自洽检查保证的范围**：它保证的仅仅是「检查成功执行时没有观察到 `BASH_ENV`/`ENV`
   与 `BASH_FUNC_*` 这两类残留」。启动代码若自己 `unset BASH_ENV` 再留下**非导出**的 shell
   函数，两项都观察不到（实测 A3/A4）——那一类由纵深第二层接手，不由这里保证。
   「同时注入必然被拒」这句话**不成立**，措辞已收窄。
5. **`builtin` 本身可被同名函数劫持**（实测：`builtin(){ :; }` 之后 `builtin printf` 走到
   那个函数）。本段全部 `builtin` 前缀在这种情况下同样失效。这一面与全文件对 `builtin` 的
   依赖同源，属已声明边界，**本卡没关**。
6. **取名的残余误判面**：`env -0` 之后，条目边界是明确的，多行值不再被误判（实测）。
   但若某个真实环境变量的**名字本身含 NUL**——POSIX 不允许，未构造——本卡未验。
7. **不证明 W4-④（Y7-A / CARD-W4-4）与 W4-⑤（Y8-B）**：那两面不在本卡范围。
8. **监视面未动**：`T-1`（`lancedb_pending_index__*.jsonl`）/ `T-13` / `T-15`
   （`neo4j_memory.json`·`llm_call_logs.db`）按 D-9c 本批不做。
9. **`shell-env-enum-failure-is-fail-closed-pass1/2` 用门副本模拟枚举失败**：真实的
   `env -0` 失败在本机不可达，所以这两条测的是「检查存在且会按该趟的文案拒绝」，
   不是「真实故障下的端到端行为」。
10. **调用者控制解释器选项这一整类，只关掉了一个**（对抗复核带出，全部为**存量**面）：

    | 形态 | 实测结果 | 本卡处置 |
    |---|---|---|
    | `SHELLOPTS=errexit` | 正常调用静默 rc=1、零输出（假红，方向反） | ✅ **修了**（`-u SHELLOPTS`） |
    | `SHELLOPTS=noexec` | rc=0、零输出、**被包裹命令根本没跑**（假绿） | ❌ **没修，不可从脚本内防御**：noexec 下 `exec` 那句本身就不执行 |
    | `POSIXLY_CORRECT=1` | bash 进 posix 模式禁用进程替换 ⇒ rc=2、语法错误、无结论行 | ❌ 没修。**开工 SHA 的门同样在 posix 模式下崩**（死在 :409，且是在跑完被包裹命令**之后**）；本卡因为引入了 `< <(…)`，改成死在 :301、**跑被包裹命令之前**。两版都不给结论、rc 都非 0，**不构成新的假绿类**，但门对「非 posix 模式的 bash」有硬依赖这件事此前没写下来，现在写下来 |

    由此得出一条给**调用方**的硬要求（已写进门头注释）：**判据不能只看 rc**，
    必须要求 stdout 里出现 `RUNTIME-FILES: unchanged` / `CHANGED` 这一行结论。
    只看 rc 的调用方在 `noexec` 下会把「门压根没跑」读成「通过」。
11. **`BASHOPTS` 只是顺手摘，不是已证实的向量**：本机 3.2.57 实测
    `BASHOPTS=expand_aliases … -c 'shopt expand_aliases'` → `off`，即它**没有**被导入。
12. **`SHA_ARGS=()` 的空数组展开**（`set -u` 下会炸）是**存量**面，本卡未动：本机
    `/usr/bin/shasum` 存在 ⇒ 走 `SHA_ARGS=(-a 256)` 分支，空数组路径不可达；只在缺
    `shasum`、走 `sha256sum` 的机器上才会碰到。登记不修。

## 六 台账待登记条目（车道不改台账，由主 session 登记）

1. `runtime_sha.sh` sha256：改前 `280cfadb…998a` → 改后 `6d206df8…53b7`
   （round-1 中间态 `d033b19f…5277`，对应 commit `4d56beb0`）。
2. 探针总数 **41 → 54**（Y7-A 收工 41 + 本卡 13）；其中 shell 探针 **6 → 19**。
3. 标记形态：argv 前哨 `--w4-reexec <串>` + PID 一致性比对 + 环境自洽复核 + 拒绝路径清 trap。
   **残余可伪造面（未关闭）**：调用者自己 `exec` 继承 PID / 猜中 PID / 进程创建后拼 argv。
4. 新依赖：`/usr/bin/env -0`（BSD/GNU 扩展）。不可用时 fail-closed 停摆，非静默降级。
   同时门对「bash 非 posix 模式」有硬依赖（`< <(…)` 进程替换）——两版皆然，见 §五.10。
5. 扫描面 T-1 / T-13 / T-15 按 D-9c **本批不做**（登记）。
6. pyright 例外提交（D-14）：两次 commit 均用 `LEFTHOOK_EXCLUDE=python-typecheck`，
   原始输出与「报错不在本卡改动行」证明见 §八。
7. Codex round-1 结论：**0 BLOCKER / 0 HIGH / 3 MEDIUM / 3 LOW**；6 条全部整改。
   ⚠️ **整改在审后，属失绑，未复审**（见 §九）。
8. 本卡 round-2 修掉两个**自己引入**的面（EXIT trap 射程假绿、多行变量假红），
   前者是作者自测发现、Codex 未提。
9. round-3 由本地对抗复核（27 agent）带出：修掉**存量**的 `SHELLOPTS=errexit` 静默假红；
   登记 `SHELLOPTS=noexec`（假绿，不可从脚本内防御）与 `POSIXLY_CORRECT`（两版皆崩）。
10. 新增花名册门 `shell-probe-roster-matches-declared-count`：门头承重声明与实际探针
    对不上就红（同一种错已犯三次，注释管不住它自己）。

## 七 环境与例外

* live vault、7691/7687 全程未碰；`tests/integration` / `tests/e2e` 未跑；`backend/.env` 未改。
* 所有写测试只在 `tempfile.mkdtemp()` 的 tmp 假 backend 里；真实 `backend/app/data` /
  `backend/data` 一个字节未碰（J4 的门自己也报 `unchanged`）。
* `*.stderr*` 未入库（`.gitignore:261` 覆盖，`git check-ignore` 实测命中）。
* 未 push。

## 八 pyright（D-14）

`.venv/bin/pyright scripts/lifespan_isolation_guard_probes.py` → `6 errors`，行号
`531 / 532`（×3）与 `616 / 617`（×3），全部是 `importlib.util.spec_from_file_location`
返回 `ModuleSpec | None` 的既有写法。

**「报错不在本卡改动行」的证明**（存档 `evidence-w4-6/d14-pyright-*.txt`）：

* 本卡在该文件的改动是**单个插入 hunk**：`@@ -763,0 +764,… @@ def probe_shell_injections()`；
* 报错行 531/532/616/617 **全部 < 764**，与改动区间不相交；
* 把 `39407e97` 的同一文件单独跑 pyright，**同样 6 errors**（存在于本卡之前）。

故按 D-14 带存档 `LEFTHOOK_EXCLUDE=python-typecheck` 提交。本卡不改 `backend/app/**`，
未往共享 venv 装任何东西。

## 九 Codex round-1 逐条处置（⚠️ 含**失绑**声明）

命令与存档首部见 `_bmad-output/审查/codex-review-CARD-W4-6-shell-bashenv.md`。
审查绑定 `4d56beb0`。结论 **0 BLOCKER / 0 HIGH / 3 MEDIUM / 3 LOW ⇒ 阻断级 0**。

| 条 | 结论 | 处置 |
|---|---|---|
| M-1 按行解析环境有歧义，普通多行变量致**假红** | **成立，且我 round-1 的「多摘无害」是错的** | 改 `env -0` NUL 分隔；新增探针 `shell-multiline-env-var-not-mistaken-for-func`；变异 `M-nul-delimited` KILLED |
| M-2 末条伪票探针没钉住导出函数分支，别的拒绝原因也能满足 | **成立** | 三条拒绝分支各绑**自己的文案**（`_refusal_case` 的 `expect_msg`）；新增 `shell-ticket-ok-but-exported-func-refused` 专走那条分支；变异 `M-bashenv-check` / `M-exported-func-check` 各**精确单杀** |
| M-3 两条票据探针的 before 红是协议差异，不算旧缺陷显形 | **成立** | §四.3 分类表；harness docstring 改口径；承重证据改由定向变异提供 |
| L-4 进程替换拿不到 `env` 退出状态，空输出被当成没残留 | **成立** | 加枚举完成哨兵；新增探针 `shell-env-enum-failure-is-fail-closed`；变异 `M-enum-sentinel` KILLED |
| L-5 `builtin`/`file` 子串搜整个 stdout 不可靠 | **成立**（Codex 自陈不推翻当前 PASS） | 新增 `_wrapped_output()` 按门的分节标记切片，判据改为**精确列表相等** `["builtin","file"]` |
| L-6 文案仍宽于实现（「一次性票据」「必然拒绝」「没有 readonly 变量」）+ **探针数字又错一次** | **全部成立** | 逐条改写；探针清单改成**逐条列名 15→16**（数字与清单条数相等）。⚠️ 我 round-1 刚把「5 条 vs 6 个名字」改对，转头把「11 条」写漏了一个名字——同一种错连犯两次，所以现在不写概数、只列名 |

**Codex 没抓到的一条（作者自测发现）**：伪造标记的拒绝路径落在注入者 `EXIT` trap 射程里，
rc 被改写成 0 + stdout 假绿（§二.3）。这正是脚本里 `:103-112` 那段**早就写着的**警告
——「提前 exit 会落进注入者的 EXIT trap 射程」——而我在新增拒绝分支时又踩了一次。
教训：**写在注释里的教训不等于判据**；现在它是 `shell-forged-ticket-under-exit-trap`。

### 九.1 ⚠️ 失绑声明（协议 §1）

Codex round-1 审的是 `4d56beb0`。上述 6 条整改 + EXIT trap 修复**发生在审后**，
落在独立 commit `03e96721`，代码树已变（`git diff --stat 4d56beb0 HEAD -- backend/` 非空）。
按协议：

> **本轮整改未复审。** 轮次按卡族累计计 1 轮。是否补第 2 轮由主 session 裁。

回退点：`git revert 03e96721` 回到 `4d56beb0`（= Codex 审过的状态）；再 revert
`4d56beb0` 回到开工 SHA `39407e97`。两个 commit 都只动
`backend/scripts/lifespan_isolation_{runtime_sha.sh,guard_probes.py}` 两个文件。

## 十 完成条件对照（卡文 §一）

| 条 | 状态 | 证据 |
|---|---|---|
| (a) `BASH_FUNC_*` 收集不依赖 `compgen -e`，实测 exec 后函数表空、被包裹命令 `type -t` 不含 `function` | ✅ | §二.1；J2-2 → `builtin` / `file` |
| (b) `:95-99` 注释不宽于实现，写入 3.2.57 实测事实，同 commit | ✅ | §一 1-B #6；`readonly -f 的也一样` 已实测保留并加了对照探针 `shell-exec-strips-readonly-func` |
| (c) 哨兵不可外部预设；预设仍清洗、伪造明确拒绝不重入不假绿、残余面如实写 | ✅ | J3；`shell-reexec-sentinel-forged`；§五.3 |
| (d) 新增 shell 探针 ≥4，全在 `probe_shell_injections()`，不改 `main()` | ✅ **13 条** | J1 54/54；J7 单 hunk |
| (e) 每条给「拆掉修复 ⇒ 转红」的 before/after | ✅ | §三（定向变异 7/7 KILLED）+ §四.3（分类说明哪几条 before 红不算承重） |
| (f) 自证与监视面常量逐字节不变 | ✅ | §四.1 |
| (g) 改前/改后 sha 入验收单，本机实测与跨版本推断分开写 | ✅ | §四.2；§五.1 |
| (h) 「本卡未证明什么」「台账待登记条目」必填 | ✅ | §五（12 条）/ §六（10 条） |

## 十一 对抗性复核（本地 27 agent，4 视角 + 逐条反驳）

Codex round-1 之后另跑了一轮本地多视角复核（视角：门 shell 正确性 / 探针判据是否
空洞 / 注释是否宽于实现 / 变异 harness 是否证明了它声称的东西），每条指控再派独立
agent **尽力反驳**。提出 23 条，反驳后**存活 4 条**（1 MEDIUM + 3 LOW，其中两条 LOW
是同一件事被两个视角各报一次）。

| 条 | 结论 | 处置 |
|---|---|---|
| **MEDIUM** `SHELLOPTS=errexit` 让**健康**路径静默 rc=1，方向反 | **成立**（我独立复现，且确认是**存量**面） | ✅ `-u SHELLOPTS -u BASHOPTS`；探针 + 变异各一。连带查出 `noexec` 假绿与 `POSIXLY_CORRECT` 崩溃，两者如实登记于 §五.10 |
| **LOW** 门头写「15 条」实际 16 条，漏列 `shell-env-enum-failure-is-fail-closed`（**第三次**犯同一种错） | **成立** | ✅ 改为逐条列 19 条 **+ 把这句声明变成探针**（`shell-probe-roster-matches-declared-count`，AST 口径）。前两次的处置都是「把注释改对」，然后第三次照旧发生 —— 注释管不住它自己 |
| **LOW** `expect_msg` 只取两趟的公共前缀 ⇒ 绑定不了是哪一趟；且删掉第二趟那段检查**全部探针照样绿** | **成立**（与 Codex MEDIUM-2 同类，换位置复发） | ✅ 拆成 `-pass1` / `-pass2` 两条，各绑该趟独有文案；锚点自检从「只数产出站点」补上「也数**检查**站点」；变异 `M-enum-check-pass2-only` 精确单杀 |

**被反驳掉的 19 条**里有几条机理属实但不构成本卡缺陷，值得记一笔：posix 模式崩溃
（两版都崩，见 §五.10）、`readonly -f "["` 击穿函数表复核（两条已声明边界的合取）、
`SHA_ARGS` 空数组（本机不可达，见 §五.12）。

**⚠️ 花名册门上线第一跑就抓到一处真漂移**：门头注释里还留着拆分前的旧名
`shell-env-enum-failure-is-fail-closed`。这也暴露了判据初版**比它的主张宽** ——
取名面是整份文件，于是「历史记录里提到当年漏列的那个名字」被当成「注释列了但不存在」。
已收窄为**只取清单区**（声明句 → 「数字与清单不一致」那段之间），并做了三向验伪
（改数字 / 删一个名字 / 破坏区间锚点，各自报出不同的原因；还原后逐字节相同）。
