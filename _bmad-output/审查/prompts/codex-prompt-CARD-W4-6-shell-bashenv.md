# 复核请求 — CARD-W4-6-shell-bashenv（BATCH-2026-09-05-第十二批 / 车道 Y7-B）

## 一 背景与最小读取面

本仓有一道「运行时文件门」：`backend/scripts/lifespan_isolation_runtime_sha.sh`。它在跑测试**前后**各给一小份具名文件清单算 sha256，前后逐字节相同就打印 `RUNTIME-FILES: unchanged`，不同就 `CHANGED` 并 exit 1。它的自我定位写在文件开头「这道门不比什么」一节：**它防的是开发者手滑，不防主动伪造门的输出**——能在脚本第 1 行之前执行代码的人可以完全伪造它的输出，这一类**明确不在防御范围内**。

这道门有两层「地基清理」：

- **第一层（exec 层）**：把自己用一个干净解释器重新 `exec` 一遍，`/usr/bin/env` 摘掉 `BASH_ENV` / `ENV` 和环境里全部 `BASH_FUNC_*` 变量（bash 把 `export -f` 的函数放在这些变量里）。
- **第二层（纵深）**：`unset BASH_ENV ENV CDPATH`、关别名、清 trap、`compgen -A function` 枚举并 `unset -f` 全部函数，再复核函数表是否真的空了。

本卡（CARD-W4-6）处理的问题是：**第一层此前对 `BASH_FUNC_*` 不承重**。本机 `/bin/bash` 是 GNU bash 3.2.57(1)-release (arm64-apple-darwin25)，导出函数的环境变量名形如 `BASH_FUNC_f%%`，含 `%%`、不是合法 shell 标识符；旧实现用 `compgen -e` 列举导出变量名来找它们，而 `compgen -e` 看不见这类名字，于是 `-u` 列表恒为空，一个导出函数都没摘。今天的正确结论完全由第二层给出。

**请只读下面这几处**（read-only，不需要也请不要运行这道门）：

1. 本卡 diff：`git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle show 4d56beb0`
2. 门脚本全文：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh`
3. 探针函数全文：同树 `backend/scripts/lifespan_isolation_guard_probes.py` 的 `probe_shell_injections()`（约 :661-940）
4. 参考（可选）：同树 `_bmad-output/审查/evidence-w4-6/` 下的裁判输出与 `before-after-harness.py`

## 二 作者自述（请独立核对，不要默认为真）

### 本机实测（bash 3.2.57，命令都跑过）

| 断言 | 实测结果 |
|---|---|
| `f(){ :; }; export -f f` 后 `env \| grep ^BASH_FUNC` | `BASH_FUNC_f%%=() {  :` |
| 同上 `builtin compgen -e \| grep -c BASH_FUNC` | `0` |
| 导出函数经 `/usr/bin/env` 传给子 bash 后 `type -t f` | `function` |
| `readonly -f g; export -f g` 后，子 bash 里 `unset -f g` | 成功（readonly 属性不随 env 传递） |
| `foo-bar` / `a.b` 作函数名导出 | 产出 `BASH_FUNC_foo-bar%%` / `BASH_FUNC_a.b%%` |
| `env -u NO_SUCH_VAR_XYZ /usr/bin/true` | rc=0，无副作用 |
| `set -u` 下展开**空**数组 `"${a[@]}"` | 报 `unbound variable` |
| `exec(){ :; }` 之后裸 `exec cmd` | 不替换进程，脚本继续在原 shell 里往下跑 |
| `builtin(){ :; }` 之后 `builtin printf` | 走到那个同名函数 |
| `exec` 前后 `$$` | 相同 |

### 跨版本推断（**未验**，本机只有一个 bash）

bash 4.3+/5.x 的导出函数环境变量名同为 `BASH_FUNC_x%%`，`compgen -e` 大概率同样看不见。本机 `command -v bash` 只有 `/bin/bash`，`/opt/homebrew/bin/bash` 不存在，**没有第二个 bash 可对照**。上表以外的任何跨版本说法都属推断。

### 本卡改了什么

1. `BASH_FUNC_*` 取名改成读 `/usr/bin/env` 输出逐行取：行首为 `BASH_FUNC_` 的行，第一个 `=` 之前整段当名字，装进数组传给 `env -u`。取名刻意取最宽（漏摘是危险方向，多摘只是一个无害的 `-u` 空名）。数组带三对固定项保证非空（避开 `set -u` + 空数组）。
2. `:95-99` 一段注释改到不宽于实现，写入上表实测事实；并更正原注释「5 条 shell 探针」与实际列出的 6 个名字不一致。
3. 重入标记从环境变量 `W4_SHA_GATE_REEXEC=1` 改成 argv 前哨 `--w4-reexec <票据>` + PID 派生票据（`exec` 不换 PID，所以第一趟造的票第二趟验得过）。票据声称「已清洗」时**再验环境**：`BASH_ENV`/`ENV` 须为空、环境中不得残留 `BASH_FUNC_*`，否则 GATE-BROKEN rc=1。
4. `exec` / `export` / `unset` 在该段一律加 `builtin` 前缀。
5. 探针 41 → 47：`probe_shell_injections()` 内新增 6 条。其中三条用 `_fake_backend(gate_text=…)` 造一份**删去第二层 `unset -f` 循环**的门副本，让判据绑定「是被第一层拦下的」；锚点命中数必须恰好 1，否则探针自报 FAIL。
6. 作者声明**未关闭**的一面：调用者若自己 `exec` 本脚本，子进程继承其 PID，票据即可对上。作者的处理是让这一面**无害化**（伪票 + 注入 ⇒ 环境自洽检查 GATE-BROKEN），并新增一条探针钉住它。

### 作者自报的 before/after

`_bmad-output/审查/evidence-w4-6/before-after-harness.py` 两侧用**同一份探针代码**，只把被测门在 `before`（父 commit `39407e97`，门 sha256 `280cfadb…998a`）与 `after`（本卡，`d033b19f…5277`）之间切换。自报结果：6 条新探针 before 全红、after 全绿；6 条既有 shell 探针两侧全绿。

## 三 请按重要性排序回答

1. **第一层是否真的承重了**：新的取名规则在什么输入下会**取不到**一个真实存在的 `BASH_FUNC_*` 变量名？「拆掉第二层的门副本」这个对照是否真能把结论绑定到第一层，还是仍可能被别的因素满足？
2. **取名规则的残余面**：多行函数体的续行、含特殊字符的函数名、`env` 输出中值里带换行的普通变量——这几类会不会让判断出错？多摘的方向真的无害吗？
3. **票据新形态的残余面**：除了作者已登记的「继承 PID」一条，还有没有别的路径能让门在**未经清洗**的环境里照常给出结论？票据不匹配那条分支会不会重新进入 `exec`（无界重入）？环境自洽检查本身有没有能被满足的空档？
4. **注释是否仍宽于实现**：门脚本开头「这道门不比什么」一节、`:95-` 一段、以及新增的票据一段，有没有哪句话说的比代码实际做到的多？
5. **六条新探针会不会被别的原因满足**：特别是 `shell-wrapped-cmd-sees-no-injected-func` 用的否定判据（stdout 里没有 `function`）——作者加了「`builtin` 与 `file` 都必须在」防空输出，这够不够？`shell-reexec-sentinel-forged` 与 `shell-forged-ticket-with-injection-refused` 在 before 侧转红的原因是「旧门不认识这个参数」而不是缺陷本身显形，这样的 before 算不算有效证据？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：结论一句 + 依据（文件:行）+ 你认为会出问题的**输入形态**（描述即可，不需要给出可运行内容）+ 建议处置。最后给一段「作者哪些自述我核对后不成立」。若某条你无法从只读材料判定，请写「材料不足」并说明还需要看什么。

## 五 边界

- 只读复核，不要修改任何文件，不要运行这道门或测试。
- 车道 Y7-A（`CARD-W4-4-settle-atomic`，父 commit `39407e97`：结算原子性、账本、install 顺序）与 Y8-B（`lifespan_isolation_negative_control.py`）**不在本卡范围**，请不要就那些面提意见。
- `SELFTEST_EXPECTED` / `WATCHED_FIXED` / `WATCHED_GLOBS` / `EXPECTED_FIXED_COUNT` / `EXPECTED_GLOB_COUNT` 五个常量本卡禁改，已实测逐字节未动；监视面的扩缩属另一张卡。
- 本仓的既有边界声明（「能在脚本被读取之前执行代码的人可以完全伪造本门的输出」）是**已接受的定位**，请在这个前提下评估本卡是否把该说的都说清楚了，而不是要求本卡去覆盖那一整类。
