#!/usr/bin/env bash
# 运行时文件门 —— 证明「跑测试没动生产运行时数据」。
#
# [BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]
#
# 用法:
#   bash backend/scripts/lifespan_isolation_runtime_sha.sh -- <要跑的命令...>
#
# 例:
#   bash scripts/lifespan_isolation_runtime_sha.sh -- .venv/bin/pytest tests/api -q
#
# ⚠️ `--w4-reexec <票据>` 是**保留的内部前哨**，只由本脚本自己在 exec 时传给自己
#    （见「已经重启过」的凭据那一段）。调用者不要传；传了且票据对不上，门会
#    GATE-BROKEN rc=1 拒绝，而不是照常出结论。
#
# 判据: 受监视文件在命令前后 **逐字节相同**（sha256 相等，或前后都不存在）。
#       监视面 = WATCHED_FIXED 的固定项 + WATCHED_GLOBS 每次快照重新展开的 glob 项；
#       任一不同（含 glob 在 after 才展开出来的**新建**文件）→ 打印
#       `RUNTIME-FILES: CHANGED` 并 exit 1。
#
# ## 为什么整段前言这么长（第八批 Codex HIGH 的直接整改）
#
# 上一版只做了「固定 PATH + unset -f shasum awk grep」。2026-09-03 实测三条绕过
# 全部成立、且三条都让门输出 `RUNTIME-FILES: unchanged` 且 rc=0：
#
#   1. `dirname() { printf '///data/nonexistent'; }; export -f dirname`
#      → 脚本监视 `//data/bug_log.jsonl` 等根本不存在的路径，三项 absent，假绿；
#   2. `printf() { builtin printf '%s' "000…0"; }; export -f printf`
#      → 所有摘要输出恒为同一串零，前后必然相等，假绿；
#   3. `BASH_ENV=<注入文件> bash 本脚本`
#      → 注入文件在脚本第 1 行之前被 source，可定义任意函数（含上面两个）。
#
# 本版的收口是「先把地基清干净，再让门证明自己算得对」：
#
#   * 清 `BASH_ENV`/`ENV`/`CDPATH`（它们只影响后续，已被 source 的内容靠下一条清）；
#   * `compgen -A function` 枚举并 `unset -f` **全部**函数（不只是三个名字）——
#     BASH_ENV 已经注入的函数在这一步被连根拔掉；
#   * `enable` 恢复可能被 `enable -n` 关掉的 builtin（printf/echo/test/[）；
#   * 外部命令一律**绝对路径**且逐个校验可执行；`dirname` 直接不用了，
#     改用 bash 参数展开 `${BASH_SOURCE[0]%/*}`；`awk`/`grep` 也不用了，
#     改用 builtin 的 `read` + `[[ =~ ]]`；
#   * **门自证**：先对一个常量串算 sha256 与钉死的期望值比对（见 SELFTEST_*）。
#     任何形式的哈希管道劫持（假 shasum / 假 printf / 假 read）都会让这一步失配。
#     这道自证是本门自己的验伪锚：门算错了要能说出来，而不是安静地判 unchanged。
#
# ## 这道门不比什么（诚实边界）
#
# * 只看 WATCHED_FIXED / WATCHED_GLOBS 这份**具名**清单（5 个固定项 + 2 条 glob）。
#   lifespan 若写了别的路径（新增的日志/缓存/临时文件），本门看不到 —— 它证明的是
#   「这几个已知受害者没被动」，不是「全盘零写入」。
#   ⛔ CARD-RUNTIME-SHA-SURFACE（第十四批）把三个原先漏列的已知受害者补了进来：
#     - `app/data/lancedb_pending_index__*.jsonl`（glob）
#     - `data/neo4j_memory.json`（固定项）
#     - `data/llm_call_logs.db`（固定项）
#   三项各有可追溯的生产写点，逐条记在下面两份清单的上方。扩面是**加**不是放宽：
#   没有放宽任何 glob、没有动任何 fail-closed 分支、没有摘掉任何既有监视项。
#   上一版这段写的是「同族的 `lancedb_pending_index__*.jsonl` **不在**清单里（扩面属
#   另一张卡的范围决策）」—— 那张卡就是本卡，所以这段话跟着清单一起更新了。
#   ⚠️ 这里的「已知受害者」仍是**默认路径**：生产若用 settings 把 storage_path /
#   db_path / state_dir 指到别处，写到别处的那一份本门照样看不到。
# * 只比首尾两个时刻。命令中途写进去、结束前又改回原内容，本门判 unchanged。
# * 不看 live vault、不看 Neo4j **库内**的 schema 与数据。数据库里被 DDL 改了 schema，
#   本门照样绿 —— 那是 socket 门（backend/tests/support/live_port_guard.py）的职责。
#   ⚠️ 别把这一条读成「凡是跟 Neo4j 沾边的都不看」：JSON 降级路径**落在磁盘上**的
#   那份 `data/neo4j_memory.json`（`app/clients/neo4j_client.py::DEFAULT_STORAGE_PATH`）
#   是**文件**不是数据库，它现在就在 WATCHED_FIXED 里。两者的分界是「进程外的数据库
#   服务」vs「本仓 backend/data 下的落盘文件」，不是名字里有没有 neo4j。
# * `absent → absent` 与 `present 且 sha 不变` 同样算 unchanged；两者语义不同，
#   脚本会逐条打印实际状态，不要只看最后一行结论。
# * 被包裹命令在**调用者的 PATH** 下执行（门只给自己锁 PATH）。门不为被包裹
#   命令的环境卫生背书。
# * ⛔ **能在本脚本被读取之前执行代码的人，可以完全伪造本门的输出，本门不防御
#   这一类。** 2026-09-04 round-2 抢救出的复现：
#     BASH_ENV=<(printf '%s\n' "builtin printf 'RUNTIME-FILES: unchanged\n'" \
#                "builtin exit 0") bash 本脚本 -- /usr/bin/false
#   → 打印 `unchanged`、rc=0，而被包裹命令必然失败。注入代码在本文件第 1 行
#   **之前**被 shell source 并 exit，脚本压根没运行 —— 这不是"防线被绕过"，
#   是"根本没到防线"。同类还有 `ENV`、导出函数、`LD_PRELOAD`、以及直接改本文件。
#   注入者**不**立刻 exit、而想篡改脚本行为的那一半，由「换干净解释器重新 exec」
#   + 纵深清洗关掉，并由 **19 条** shell 探针承重（`lifespan_isolation_guard_probes.py`
#   的 `probe_shell_injections()`，名字逐条列全 —— 数字必须与清单条数相等）：
#     既有 6 条 —— `shell-fake-dirname` / `shell-fake-printf` / `shell-bash-env` /
#       `shell-readonly-func`（期望门**照常给出正确答案**）、
#       `shell-alias-test-hijack` / `shell-exit-trap-hijack`（期望门**拒绝空跑**）；
#     CARD-W4-6 新增 12 条 ——
#       1 `shell-bash-env-exec-layer-is-load-bearing`
#       2 `shell-exec-strips-readonly-func`
#       3 `shell-wrapped-cmd-sees-no-injected-func`
#         （以上三条用拆掉纵深第二层的门副本 ⇒ 证明 exec 层自己承重）
#       4 `shell-reexec-sentinel-preset`（照抄旧环境变量不再能跳过清洗）
#       5 `shell-reexec-sentinel-forged`（标记不匹配 ⇒ 按该分支的文案拒绝）
#       6 `shell-forged-ticket-with-injection-refused`（PID 一致但 BASH_ENV 非空）
#       7 `shell-ticket-ok-but-exported-func-refused`（PID 一致、BASH_ENV 已清、
#         只剩导出函数 ⇒ 按**导出函数**分支的文案拒绝）
#       8 `shell-forged-ticket-under-exit-trap`（伪造标记 + EXIT trap ⇒ rc 不被改写）
#       9 `shell-multiline-env-var-not-mistaken-for-func`（值含换行的普通变量
#         **不得**被当成导出函数 ⇒ 正常调用不假红）
#      10 `shell-env-enum-failure-is-fail-closed-pass1`
#      11 `shell-env-enum-failure-is-fail-closed-pass2`
#         （两趟枚举各有一段完成检查，**分开钉**；只钉一趟的话，把另一趟那段删掉
#          全部探针照样绿）
#      12 `shell-shellopts-errexit-does-not-false-red`（调用者导出的 SHELLOPTS
#         不得把正常调用弄成静默 rc=1）
#      13 `shell-probe-roster-matches-declared-count`（**本段声明自己的门**，见下）
#   ⚠️ 「数字与清单不一致」这个错在本文件里已被更正**三次**：最早写「5 条」列 6 个
#      名字；CARD-W4-6 初版写「11 条」漏列 `shell-reexec-sentinel-forged`（Codex
#      round-1 LOW-6 抓到）；round-2 写「15 条」漏列
#      `shell-env-enum-failure-is-fail-closed`（对抗复核抓到）。前两次的处置都是
#      「把注释改对」，然后第三次照旧发生 —— **注释管不住它自己**。所以第 13 条探针
#      现在把这段声明变成判据：解析 `probe_shell_injections()` 函数体的 AST 取
#      `shell-*` 字符串常量的互异集合，其**条数**必须等于上面那个数字，且集合里每个
#      名字都要在本清单里出现（多列、漏列都红）。改探针时它会当场告诉你这里要改。
#   ⚠️ 试过「启动期检测到注入就提前 exit」并**回退**了：提前 exit 会落进注入者的
#   `trap ... EXIT` 射程（rc 被改写成 0，比不加更糟），而 `exec` 之所以有效正是
#   因为它替换进程映像、EXIT trap 不触发。理由写在 exec 那一段的注释里。
#   这条边界与本门的定位一致：它防的是**开发者手滑**，不防**主动伪造门的输出**
#   —— 能设 BASH_ENV 的人同样能直接改这个脚本、改 git 历史、改任何东西。
#   ⚠️ 历史记录：round-1 第 5 条整改曾把「shell 控制流劫持」写成已关闭，那个说法
#   **比实现宽**；本条是对它的更正。
# * ⛔ **调用者控制解释器选项（`SHELLOPTS`）也在这条边界里**（2026-09-06 实测补记，
#   存量、非 CARD-W4-6 引入）。bash 启动会导入环境里的 `SHELLOPTS` 并置位对应选项，
#   而本文件的 `set -uo pipefail` 只加不减。两个已实测的形态：
#     * `SHELLOPTS=errexit` —— **假红**：函数表空（正常情形）时 `compgen -A function`
#       返回 1 + pipefail ⇒ 第二层的 `__leftover=` 赋值 rc=1 ⇒ errexit 静默退出，
#       rc=1、零输出。CARD-W4-6 已在 exec 参数里 `-u SHELLOPTS` 摘掉，**这一个修好了**。
#     * `SHELLOPTS=noexec` —— **假绿且无法从脚本内部防御**：bash 只解析不执行，
#       连 `exec` 那句都不跑，rc=0、零输出、被包裹命令根本没跑。**没有修**，因为
#       脚本自己的代码正是那个不会执行的东西。
#   由此得出一条给**调用方**的硬要求：**判据不能只看 rc**，必须要求 stdout 里出现
#   `RUNTIME-FILES: unchanged` / `CHANGED` 这一行结论；只看 rc 的调用方在 noexec 下
#   会把「门压根没跑」读成「通过」。
#   ⛔ 这条硬要求的可执行形态（CARD-RUNTIME-SHA-SURFACE 实测，第十四批）——
#   取 **stdout+stderr** 合并文本，**没有结论行就判红，不看 rc**：
#     Python（推荐，免疫 noexec）:
#       p = subprocess.run(["bash", GATE, "--", *cmd], capture_output=True, text=True)
#       if "RUNTIME-FILES:" not in (p.stdout + p.stderr):
#           raise SystemExit("门未自报结论行 ⇒ 门没跑（SHELLOPTS=noexec？解释器被换？）")
#     shell（够用但**挡不住 noexec**，见下）:
#       out="$(bash "$GATE" -- "$@" 2>&1)"; rc=$?
#       printf '%s\n' "$out" | grep -qE '^RUNTIME-FILES: (unchanged|CHANGED)$' \
#         || { printf 'GATE-DID-NOT-RUN\n' >&2; exit 1; }
#       exit "$rc"
#   ⛔ 为什么**常驻**强制必须落在非 bash 进程：同一个 `SHELLOPTS=noexec` 环境里，
#      上面那个 shell 版调用方**自己也只解析不执行**（实测 rc=0、零输出）。同理，
#      在 repo 根另建一个 bash launcher 来「防 noexec」是**假安全感** —— 那个壳一样
#      不会执行。所以：断言要么跑在 Python / pytest / make 里，要么它防不住这一条。
#   ⛔ 本脚本内部**没有**、也不会有任何声称能防 noexec 的分支：脚本自己的代码正是
#      那个不会执行的东西，写一个看起来能防的分支比如实登记更糟。这里只有注释与
#      配方，强制在调用方。把它钉成常驻探针属于 guard_probes / 契约测试的面。
#
# 退出码:
#   1  = 文件被改，或门自证失败（门的裁定）
#   2  = 用法错误
#   其它 = 被包裹命令自己的退出码（测试红了照样透出来，不被门吞掉）

set -uo pipefail

# ── 地基清理第一步：换一个干净解释器重新起（R1 Codex HIGH-5）──────────────
#
# 上一版只清了函数。实测仍可绕过：`BASH_ENV` 里 `shopt -s expand_aliases` +
# `alias [=...`（别名在函数之前展开，且 unset -f 管不着）、`readonly -f` 的函数
# （unset -f 直接失败）、以及 `trap ... EXIT`，都能篡改**控制流**而不是数据管道
# —— 摘要自证只覆盖后者。实测形态：让 `[` 恒假 ⇒ 连 `-- 之后没有命令` 这道
# 用法检查都通过，脚本空跑并输出 `RUNTIME-FILES: unchanged`、exit 0。
#
# 干净的解法不是继续往清单里加名字（那是「枚举白名单」式的必输游戏），而是
# **换一个干净解释器 exec 自己**：新解释器不读 BASH_ENV、不带调用者的导出函数、
# 没有别名、没有 trap，也**不继承调用者设置的 readonly 属性**（readonly 不随 env
# 传递 —— 实测 `readonly -f g; export -f g` 之后，子 bash 里 `unset -f g` 成功）。
# 调用者的 PATH 用一个显式变量带过去，只给被包裹命令用。
#
# ⚠️ 刻意**不**用 `env -i`：被包裹命令（通常是 pytest）需要调用者的环境
# （HOME / TMPDIR / locale / 项目自己的变量）。只摘注入面：`BASH_ENV`、`ENV`
# 和环境里**全部 `BASH_FUNC_*` 变量**——导出函数（含 `readonly -f` 过的）就藏在
# 这些变量里。判据用 `case` 而不是 `[` —— `[` 可以被 alias 劫持，而 `case` 是
# shell 语法，劫持不了（这正是 R1 Codex HIGH-5 的攻击面）。
#
# ## 取名为什么不能用 `compgen -e`（CARD-W4-6，2026-09-05 本机实测）
#
# 上一版这里是 `for __v in $(builtin compgen -e); do case "$__v" in BASH_FUNC_*)`。
# 在绑定环境 **GNU bash 3.2.57(1)-release (arm64-apple-darwin25)** 上实测：
#
#     /bin/bash --noprofile --norc -c 'f(){ :; }; export -f f;
#         /usr/bin/env | grep "^BASH_FUNC"; builtin compgen -e | grep -c BASH_FUNC'
#     → BASH_FUNC_f%%=() {  :      ← env 看得见
#     → 0                          ← compgen -e 一个都数不出来
#
# 导出函数的环境变量名形如 `BASH_FUNC_f%%`，**带 `%%`、不是合法 shell 标识符**，
# 而 `compgen -e` 给的是「可以当变量名用的导出名」列表，压根不列它。于是上一版
# 收集到的 `__unset_args` **恒为空串**，那句 exec 一个导出函数都没摘 —— 导出函数
# 原样进了新解释器（实测 `/usr/bin/env /bin/bash --noprofile --norc -c 'type -t f'`
# → `function`），全靠下面**第二层**的 `unset -f` 兜住。也就是说 exec 层对
# `BASH_FUNC_*` **不承重**，而上一版这段注释说得比实现宽。
#
# 现在改成枚举 `/usr/bin/env -0` 的输出取名：环境条目以 **NUL** 分隔，名字取到
# 第一个 `=` 之前。取名锚定 `BASH_FUNC_` 前缀而不是标识符字符 —— 函数名并**不**
# 限于标识符字符，实测 `foo-bar(){ :; }; export -f foo-bar` 产出
# `BASH_FUNC_foo-bar%%`、`a.b` 产出 `BASH_FUNC_a.b%%`，把锚点写成
# `[A-Za-z_][A-Za-z0-9_]*` 就会漏（漏摘 = 导出函数活着进新解释器 = 危险方向）。
#
# ⚠️ **为什么必须是 `-0` 而不是逐行**（Codex round-1 MEDIUM-1，2026-09-06 实测）：
# 换行分隔无法区分「条目边界」与「值里的换行」。初版按行扫，于是一个**普通**的
# 导出变量只要值里有一行以 `BASH_FUNC_` 开头，就会被当成导出函数：
#     CARRIER=$'harmless\nBASH_FUNC_notafunction%%=whatever' bash 本脚本 -- /usr/bin/true
#     → RUNTIME-FILES: GATE-BROKEN — …仍有导出函数: BASH_FUNC_notafunction%%   rc=1
# 完全正常的调用被拒 —— **假红**，而且不需要任何注入。初版注释里「多摘只是多一个
# 无害的 `-u` 空名」这句话**是错的**：多摘在第一趟确实无害（`env -u` 一个不存在的
# 名字实测 rc=0），但同一条规则在第二趟是**残留判据**，多摘就直接变成拒绝。
# `-0` 把这一整类歧义从根上去掉：实测同一个多行变量在 NUL 分隔下只是一个条目，
# 不再命中（见验收单 §M1）。
# 可移植性如实写：`env -0` 是 BSD/GNU 扩展，非 POSIX 必备。本机 `/usr/bin/env -0`
# 实测可用（macOS darwin25）；**不可用时不会静默降级** —— 见下面的枚举完成哨兵。
#
# ⚠️ 枚举失败必须与「零个匹配」区分（Codex round-1 LOW-4）：进程替换拿不到生产者
# 的退出码，`pipefail` 也不覆盖它，于是「`env` 没跑起来 / 输出被截断」会表现成
# 「没有残留」而静默通过。所以生产者末尾补一个 `$__W4_ENV_SENTINEL` 条目，消费端
# 必须看到它才认这次枚举完整；看不到就 GATE-BROKEN。哨兵串不含 `=`，而 `env` 的
# 每个条目必然含 `=`，因此不可能与真实条目相等。
#
# ⚠️ 两处枚举**刻意不抽成 shell 函数**：第一趟跑在尚未清洗的环境里，注入者可以
#    先 `readonly -f` 占住我们要用的函数名，我们的定义就会失败而调用落到他的实现上。
#    重复两段直写代码是这里的正确选择。
#
# ## 「已经重启过」的凭据：为什么不再是一个环境变量（CARD-W4-6）
#
# 上一版用 `W4_SHA_GATE_REEXEC=1` 当标记，而这个标记**调用者可以照抄**：
#   `W4_SHA_GATE_REEXEC=1 BASH_ENV=<注入> bash 本脚本 -- cmd`
# 整段清洗被直接跳过（2026-09-05 实测 before：`readonly -f` 的注入函数活到第二层，
# `unset -f` 对它失败 ⇒ 门打印 GATE-BROKEN、rc=1。不是假绿，但一个环境变量就能让
# 这道门罢工）。
#
# 现在改成 **argv 前哨 + PID 一致性标记**：`exec` 不换 PID（实测），所以第一趟用
# `$$` 造串、第二趟再用 `$$` 比对，两趟必然对得上；而调用者要照抄这个串，得先知道
# 自己**尚未创建**的那个进程的 PID。
#
# ⚠️ 措辞收窄（Codex round-1 LOW-6）：它**不是「一次性票据」**，没有任何消费状态 ——
#    就是一个 `$$` 等值比较，串本身是公开的（`ps` 看得见）。它证明的**只是**
#    「argv 里的串与本进程 PID 一致」，**不证明清洗真的发生过**。
#
# 两条必须写清的边界：
#   1. **残余可伪造面（没关掉）**：调用者若自己 `exec` 本脚本 ——
#      `exec bash 本脚本 --w4-reexec "w4-sha-gate-reexec-v1:$$" -- cmd` ——
#      子进程继承它的 PID，串就对得上。同类还有「猜中 PID」「进程起来后再拼 argv」。
#      这一面落在本文件开头那条「能在本脚本被读取之前执行代码的人可以完全伪造本门的
#      输出」里。本卡关掉的只是「照抄一个常量」这条**不需要任何前置能力**的路。
#   2. 所以比对通过之后**还要验环境**：串声称"已经清洗过"，那 `BASH_ENV`/`ENV`
#      必须为空、环境里必须没有 `BASH_FUNC_*`。
#      ⚠️ 这道检查保证的**仅仅是**「检查成功执行时没有观察到这两类残留」，**不是**
#      「同时注入必然被拒」：启动代码若自己 `unset BASH_ENV` 再留下**非导出**的
#      shell 函数，两项都观察不到（实测）。那一类由下面的纵深第二层
#      （`unset -f` + 函数表复核）接手，不由这里保证。
#
# ⚠️ 这**不是**回到下面那段已否决的「检测到注入就提前 exit」：那一版把检测放在
#    **正常路径**上。本版的检测只在「串声称已清洗」这条分支上跑，正常调用永远走
#    exec 清洗，四条数据管道探针的语义原样保留。理由详见紧接着的注释。
#
# ⚠️ 这条分支上的拒绝是**尚未 exec 时的 exit**，因此落在注入者 `trap ... EXIT` 的
#    射程里 —— 2026-09-06 作者自测实测：不清 trap 时 stderr 打了 GATE-BROKEN，而
#    注入者的 EXIT trap 随后打印 `RUNTIME-FILES: unchanged` 并把 rc 改写成 0
#    （**本卡自己引入的假绿面**）。所以进入本分支的第一件事就是 `builtin trap -`。
#    探针 `shell-forged-ticket-under-exit-trap` 钉住它。
#
# ⚠️ `exec` / `export` / `unset` / `trap` 本身都能被同名函数劫持（实测 `exec(){ :; }`
#    之后裸 `exec cmd` 什么也不做、脚本继续在**脏 shell 里往下跑**），所以本段一律用
#    `builtin` 前缀。`builtin` 自己仍可被同名函数劫持（实测），那一面不在本卡关闭
#    范围内 —— 它与全文件对 `builtin` 的依赖同源，属上面那条已声明的边界。

#: 本进程的 PID 一致性标记。exec 不换 PID ⇒ 第一趟造的串，第二趟比得上。
__W4_TICKET="w4-sha-gate-reexec-v1:$$"
#: 环境枚举完成哨兵。不含 `=`，而 env 的每个条目必含 `=` ⇒ 不可能与真实条目相等。
__W4_ENV_SENTINEL="W4-SHA-GATE-ENV-DUMP-COMPLETE"
__w4_claimed=0
__w4_ticket_seen=""
case "${1:-}" in
  --w4-reexec)
    __w4_claimed=1
    # 用 case 而不是 `[` 判参数个数：`[` 在这里还可能是别名/函数。
    case "$#" in
      0|1) ;;
      *) __w4_ticket_seen="$2"; shift 2 ;;
    esac
    ;;
esac

case "$__w4_claimed" in
  0)
    # ⛔ 这里**刻意不做「检测到注入就提前 exit」**（2026-09-04 试过并回退，
    #    原因值得留着，免得后人再试一次）：
    #    1. 提前 `exit` 会落进注入者的 `trap ... EXIT` 射程 —— 探针
    #       `shell-exit-trap-hijack` 当场把 `exit 1` 改写成 rc=0，比不加更糟；
    #       下面这条 `exec` 之所以有效，正是因为 **exec 替换进程映像、EXIT trap
    #       根本不触发**，新解释器干净、无 trap，之后的用法检查才拒得干净。
    #    2. 「发现即拒」还会把 `shell-fake-dirname` / `shell-fake-printf` /
    #       `shell-bash-env` / `shell-readonly-func` 四条探针的语义从
    #       「门**抗污染并仍给出正确答案**」降级成「门罢工」—— 后者是更弱的能力。
    #    结论：换干净解释器 + 纵深清洗，比在脏环境里自我了断强。
    W4_SHA_GATE_CALLER_PATH="${PATH:-}"
    builtin export W4_SHA_GATE_CALLER_PATH
    # 数组恒非空（前几对固定项）：bash 3.2 在 `set -u` 下展开**空**数组
    # `"${a[@]}"` 会报 unbound variable（本机实测），非空就绕开了这个坑。
    #
    # `-u W4_SHA_GATE_REEXEC`：该变量已退役（见上），顺手摘掉残值，免得后人
    # 看见它还以为能靠它跳过清洗。
    #
    # ⚠️ `-u SHELLOPTS`（2026-09-06 实测，**存量缺陷**，非本卡引入）：bash 启动时会
    #    读环境里的 `SHELLOPTS` 并把里面列的选项置位 —— 实测
    #    `SHELLOPTS=errexit /bin/bash --noprofile --norc -c 'set -o | grep errexit'`
    #    → `errexit on`。而本文件 `set -uo pipefail` **只加不减**，关不掉它。
    #    后果是一条**方向反了的假红**：第二层复核函数表那句
    #    `__leftover="$(builtin compgen -A function … | … tr …)"`，在函数表**空**
    #    （= 正常情形）时 `compgen -A function` 返回 1，叠加 pipefail ⇒ 赋值 rc=1
    #    ⇒ errexit 当场退出。实测 `SHELLOPTS=errexit bash 本脚本 -- /usr/bin/true`
    #    → **rc=1、stdout/stderr 全空**；而留着清不掉的函数（= 异常情形）时
    #    compgen rc=0，反而顺利走到 GATE-BROKEN 把话说出来。rc=1 正是本门文档里
    #    「文件被改」的码，调用方会把「门被环境噎死」读成「运行时数据被动过」。
    #    摘掉之后实测回到 rc=0（探针 `shell-shellopts-errexit-does-not-false-red`）。
    #    `BASHOPTS` 一并摘作防御深度 —— 但如实写：本机 3.2.57 实测它**没有**被导入
    #    （`BASHOPTS=expand_aliases … -c 'shopt expand_aliases'` → `off`），
    #    所以它是「顺手」，不是已证实的向量。
    #
    # ⛔ 这一手**关不掉 `SHELLOPTS=noexec`**（如实登记，见文件开头的边界一节）：
    #    noexec 下 bash 只解析不执行，下面这句 `exec` 本身就不会跑，脚本没有任何
    #    自我防御的机会。实测 `SHELLOPTS=noexec bash 本脚本 -- <cmd>` → rc=0、
    #    零输出、**被包裹命令没跑**。能改解释器选项的人等于能让本门不运行。
    __w4_env_args=(-u BASH_ENV -u ENV -u W4_SHA_GATE_REEXEC -u SHELLOPTS -u BASHOPTS)
    __w4_env_ok=0
    while IFS= builtin read -r -d '' __w4_entry; do
      case "$__w4_entry" in
        "$__W4_ENV_SENTINEL") __w4_env_ok=1 ;;
        BASH_FUNC_*) __w4_env_args+=(-u "${__w4_entry%%=*}") ;;
      esac
    done < <({ /usr/bin/env -0 && builtin printf '%s\0' "$__W4_ENV_SENTINEL"; } 2>/dev/null)
    builtin unset __w4_entry
    case "$__w4_env_ok" in
      1) ;;
      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 环境枚举未完整产出（/usr/bin/env -0 失败或被截断）；拒绝在不知道注入面的情况下继续\n' >&2
        builtin exit 1
        ;;
    esac
    builtin exec /usr/bin/env "${__w4_env_args[@]}" \
      /bin/bash --noprofile --norc "$0" --w4-reexec "$__W4_TICKET" "$@"
    ;;
  *)
    # ── 串声称「已经清洗过」：比对 + 验环境 ────────────────────────────
    # ⛔ 第一件事就是清 trap：本分支的 exit 发生在 exec **之前**，不清就落在注入者
    #    `trap ... EXIT` 的射程里，rc 会被改写成 0（实测，见上方注释）。
    builtin trap - EXIT HUP INT QUIT TERM ERR DEBUG RETURN 2>/dev/null || true
    case "$__w4_ticket_seen" in
      "$__W4_TICKET") ;;
      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — --w4-reexec 标记与本进程 PID 不一致；拒绝在未经清洗的环境里给出结论\n' >&2
        builtin exit 1
        ;;
    esac
    case "${BASH_ENV:-}${ENV:-}" in
      "") ;;
      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 标记声称已清洗，但 BASH_ENV/ENV 仍有值；拒绝给出结论\n' >&2
        builtin exit 1
        ;;
    esac
    __w4_stale=""
    __w4_env_ok=0
    while IFS= builtin read -r -d '' __w4_entry; do
      case "$__w4_entry" in
        "$__W4_ENV_SENTINEL") __w4_env_ok=1 ;;
        BASH_FUNC_*) __w4_stale="${__w4_stale} ${__w4_entry%%=*}" ;;
      esac
    done < <({ /usr/bin/env -0 && builtin printf '%s\0' "$__W4_ENV_SENTINEL"; } 2>/dev/null)
    builtin unset __w4_entry
    case "$__w4_env_ok" in
      1) ;;
      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 环境枚举未完整产出（/usr/bin/env -0 失败或被截断）；拒绝把「没看见残留」当成「没有残留」\n' >&2
        builtin exit 1
        ;;
    esac
    case "$__w4_stale" in
      "") ;;
      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 标记声称已清洗，但环境里仍有导出函数:%s\n' "$__w4_stale" >&2
        builtin exit 1
        ;;
    esac
    builtin unset __w4_stale
    ;;
esac
builtin unset __w4_env_ok __W4_ENV_SENTINEL
builtin unset __W4_TICKET __w4_claimed __w4_ticket_seen

# ── 地基清理第二步：纵深防御（即使上面的 exec 被人绕过也照做一遍）──────────
unset BASH_ENV ENV CDPATH
builtin shopt -u expand_aliases 2>/dev/null || true
builtin unalias -a 2>/dev/null || true
builtin trap - EXIT HUP INT QUIT TERM ERR DEBUG RETURN 2>/dev/null || true
# 枚举并清掉**全部** shell 函数（含 BASH_FUNC_* 导出进来的）。compgen 是 builtin。
for __fn in $(builtin compgen -A function 2>/dev/null); do
  builtin unset -f "$__fn" 2>/dev/null || true
done
unset __fn
# readonly 的函数 unset 不掉 —— 清完之后必须复核函数表是否真的空了。
__leftover="$(builtin compgen -A function 2>/dev/null | /usr/bin/tr '\n' ' ')"
if [ -n "${__leftover// /}" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 清不掉的 shell 函数仍在: %s\n' "$__leftover" >&2
  exit 1
fi
unset __leftover
# 恢复可能被 `enable -n` 关掉的 builtin —— 否则 printf/echo 会落到 PATH 上。
builtin enable printf echo test [ read cd pwd 2>/dev/null || true
# 门自身的工具解析锁死在系统目录；被包裹命令另行恢复调用者 PATH（见下）。
CALLER_PATH="${W4_SHA_GATE_CALLER_PATH:-${PATH:-}}"
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH

# ── 控制流自证：在信任任何条件判断之前，先证明条件判断本身没被改写 ──────────
# 摘要自证（见下）只覆盖**数据管道**；这一段覆盖**控制流**。
if [ "x" = "y" ] || ! [ "x" != "y" ] || [ -f "/nonexistent/w4-gate-probe" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 条件判断被改写（test/[ 不可信），本门的每一道判据都失效\n' >&2
  exit 1
fi
for __b in printf echo test read cd pwd; do
  if [ "$(builtin type -t "$__b" 2>/dev/null)" != "builtin" ]; then
    builtin printf 'RUNTIME-FILES: GATE-BROKEN — %s 不是 builtin（当前是 %s）\n' \
      "$__b" "$(builtin type -t "$__b" 2>/dev/null)" >&2
    exit 1
  fi
done
unset __b

# ── 外部命令：绝对路径 + 存在性校验（不用 dirname/awk/grep）──────────────
SHA_CANDIDATES=(/usr/bin/shasum /usr/bin/sha256sum /bin/sha256sum)
SHA_BIN=""
SHA_ARGS=()
for __c in "${SHA_CANDIDATES[@]}"; do
  if [ -x "$__c" ]; then
    SHA_BIN="$__c"
    case "$__c" in
      */shasum) SHA_ARGS=(-a 256) ;;
      *) SHA_ARGS=() ;;
    esac
    break
  fi
done
unset __c
if [ -z "$SHA_BIN" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 找不到可执行的 sha256 工具 (%s)\n' "${SHA_CANDIDATES[*]}" >&2
  exit 1
fi
DATE_BIN=/bin/date
DIFF_BIN=/usr/bin/diff
# ⛔ 排序是**承重**的，不是装饰（M13，见 snapshot() 里的实测记录）：glob 展开顺序
#    不稳定时 before/after 会因**排列不同**而字符串不等 ⇒ 门判 CHANGED 假红。
#    所以 SORT_BIN 缺席必须 fail-closed，不能像 DIFF_BIN 那样软降级。
SORT_BIN=/usr/bin/sort
if [ ! -x "$SORT_BIN" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 找不到可执行的 %s；glob 展开无法稳定排序，拒绝给出结论\n' \
    "$SORT_BIN" >&2
  exit 1
fi

# ── 门自证：常量串的 sha256 必须等于钉死值 ──────────────────────────────
# 这一步同时验证 SHA_BIN、builtin printf、builtin read 三者都没被掉包。
SELFTEST_INPUT='w4-runtime-sha-gate-selftest-v1'
SELFTEST_EXPECTED='82e87819dac824b894684638a188059759c99d793641765853e5c5cae20baa1c'

hash_stdin() {
  # 从 stdin 读内容，回显 64 位十六进制摘要；失败回显空串。
  local out digest rest
  out="$("$SHA_BIN" "${SHA_ARGS[@]}")" || return 1
  builtin read -r digest rest <<<"$out"
  builtin printf '%s' "$digest"
}

SELFTEST_ACTUAL="$(builtin printf '%s' "$SELFTEST_INPUT" | hash_stdin)"
if [ "$SELFTEST_ACTUAL" != "$SELFTEST_EXPECTED" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 门自证失败：sha256(%s) 期望 %s，实得 %s。\n' \
    "$SELFTEST_INPUT" "$SELFTEST_EXPECTED" "${SELFTEST_ACTUAL:-<空>}" >&2
  builtin printf '  哈希管道被劫持（假 shasum / 假 printf / 假 read / PATH 注入），本门的结论不可信。\n' >&2
  exit 1
fi

# ── 路径解析：不用 dirname（它可被导出函数劫持），用参数展开 ─────────────
__src="${BASH_SOURCE[0]}"
case "$__src" in
  */*) SCRIPT_DIR_RAW="${__src%/*}" ;;
  *) SCRIPT_DIR_RAW="." ;;
esac
SCRIPT_DIR="$(builtin cd "$SCRIPT_DIR_RAW" && builtin pwd -P)" || {
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 无法解析脚本目录 %s\n' "$SCRIPT_DIR_RAW" >&2
  exit 1
}
BACKEND_DIR="$(builtin cd "${SCRIPT_DIR}/.." && builtin pwd -P)" || {
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 无法解析 BACKEND_DIR\n' >&2
  exit 1
}
unset __src SCRIPT_DIR_RAW
# BACKEND_DIR 必须是一个**真的**后端目录，否则说明路径解析被人做了手脚
# （第八批的 dirname 劫持正是把它变成 `//`，三项 absent 假绿）。
if [ ! -f "${BACKEND_DIR}/app/main.py" ] || [ ! -d "${BACKEND_DIR}/tests" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — BACKEND_DIR=%s 不像后端目录（缺 app/main.py 或 tests/）\n' \
    "$BACKEND_DIR" >&2
  exit 1
fi

# 受监视文件 —— 均 git-ignored 的运行时产物，均由 app/main.py 的 lifespan 链写。
#   bug_log.jsonl                <- app/core/bug_tracker.py
#   outbox/events.jsonl          <- app/services/event_bus.py
#   app/data/vault_index_pending.jsonl
#       <- app/core/vault_state_paths.py::legacy_state_path（G2-5 之前的旧固定名）。
#          它以前是被下面那条过宽 glob 顺带收进来的；M14 收窄后 glob 只认命名空间
#          形态，所以旧名必须**显式**列在这里，否则监视面会悄悄变窄。
#   data/neo4j_memory.json       <- app/clients/neo4j_client.py::DEFAULT_STORAGE_PATH
#          （CARD-RUNTIME-SHA-SURFACE 补入，第十四批。Neo4j 不可用时的 JSON 降级落盘；
#          `Path(__file__).parent.parent.parent / "data" / "neo4j_memory.json"` 展开
#          恰是 backend/data/ 下这一份，与 BACKEND_DIR 同基。）
#   data/llm_call_logs.db        <- app/middleware/cost_tracker.py::_DEFAULT_DB_PATH
#          （CARD-RUNTIME-SHA-SURFACE 补入，第十四批。⚠️ 它是 **SQLite 二进制**：门按
#          逐字节 sha256 判定，所以先实测过「只读不写不会改字节」——默认连接 SELECT、
#          再 SELECT、只读 URI SELECT 三种形态 sha 均不变，真写入才变（验伪锚）。
#          若将来换 WAL 或有别的写者，这一项会变成新的假红面，届时查这里。）
# ⚠️ 上面五项都只盯**默认**路径。生产若用 settings 覆盖了 storage_path / db_path，
#    写到别处的那一份本门看不到 —— 这与本门「具名清单、不是全盘零写入」的定位一致。
WATCHED_FIXED=(
  "${BACKEND_DIR}/data/bug_log.jsonl"
  "${BACKEND_DIR}/data/outbox/events.jsonl"
  "${BACKEND_DIR}/app/data/vault_index_pending.jsonl"
  "${BACKEND_DIR}/data/neo4j_memory.json"
  "${BACKEND_DIR}/data/llm_call_logs.db"
)

# ⛔ orchestrator 的 durable journal 不能写成固定文件名（2026-09-04 主干合并后
#    当场抓到的假门）：CARD-G2-5（第七批）把它改成了 vault 命名空间下的
#    vault_index_pending__<vault_key>.jsonl（app/core/vault_state_paths.py::
#    namespaced_state_path），vault_key 还会因 NAME_MAX 的**字节**预算被 hash
#    截断 —— 文件名不可预先硬编码。锚点落空的后果就是本门恒 unchanged 的**假绿**：
#    它断言的是"没变"，而一个永远不存在的路径永远 absent==absent。
#   vault_index_pending__*.jsonl <- app/services/vault_index_orchestrator.py:131
#
# ⛔ M14 收窄（CARD-W4-3b，2026-09-05）：上一版是 `vault_index_pending*.jsonl`，
#    比写侧**实际能产出的形态更宽** —— 单下划线的 `vault_index_pending_backup.jsonl`
#    这类人手放的旁文件也会进监视面，让本门对「有人在 app/data 放了个备份」判 CHANGED
#    （假红）。门以「会误报」出名，下一个人就会去放宽它。现在只认两条**可由写侧证明**
#    的形态：旧固定名进上面的 WATCHED_FIXED，命名空间形态进本 glob。
#    `NAMESPACE_SEP` 是双下划线（vault_state_paths.py:36），`sanitize_vault_id` 保证
#    key 只含 \w、压缩形态是 `<前缀>-<sha12>`，两者都不含 `/` —— `__*` 恰好覆盖全部
#    可能的 key。收窄是**放松**方向，逐文件证据见验收单 §M14。
#
# ⛔ 第二条 glob（CARD-RUNTIME-SHA-SURFACE，第十四批）：LanceDB 索引队列的 durable
#    journal。`app/services/lancedb_index_service.py` 的
#    `_journal_stem: str = "lancedb_pending_index"` 经**同一个**
#    `vault_state_paths.py::namespaced_state_path()` 落成
#    `app/data/lancedb_pending_index__<vault_key>.jsonl` —— 与上面那条**同命名空间
#    形态、同一个双下划线 `NAMESPACE_SEP`、同一套 `sanitize_vault_id`**。
#    所以它的收窄口径逐字照搬上面：**必须**双下划线 `__*`。写成单下划线
#    `lancedb_pending_index*.jsonl` 会把人手放的 `lancedb_pending_index_backup.jsonl`
#    这类旁文件收进监视面 —— 正是 M14 刚刚收窄掉的那种假红，别再造一遍。
#    在此之前本门**不**看这一族（文件开头的边界一节旧版写着「扩面属另一张卡的
#    范围决策」），那一段已随本次扩面同步更新。
WATCHED_GLOBS=(
  "${BACKEND_DIR}/app/data/vault_index_pending__*.jsonl"
  "${BACKEND_DIR}/app/data/lancedb_pending_index__*.jsonl"
)
EXPECTED_FIXED_COUNT=5
EXPECTED_GLOB_COUNT=2

# 自检: 监视清单不能悄悄变空/变短 —— 空清单会让本门「零比较、恒绿」。
# 两类分别自检: glob 项数为 0 同样是「零比较」，只是更隐蔽。
if [ "${#WATCHED_FIXED[@]}" -ne "${EXPECTED_FIXED_COUNT}" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 固定监视项有 %s 个, 期望 %s 个\n' \
    "${#WATCHED_FIXED[@]}" "${EXPECTED_FIXED_COUNT}" >&2
  exit 1
fi
if [ "${#WATCHED_GLOBS[@]}" -ne "${EXPECTED_GLOB_COUNT}" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — glob 监视模式有 %s 条, 期望 %s 条\n' \
    "${#WATCHED_GLOBS[@]}" "${EXPECTED_GLOB_COUNT}" >&2
  exit 1
fi

if [ "${1:-}" != "--" ]; then
  builtin printf '用法: bash %s -- <command...>\n' "$0" >&2
  builtin printf "  ('--' 之后的一切原样作为命令执行)\n" >&2
  exit 2
fi
shift
if [ "$#" -eq 0 ]; then
  builtin printf "RUNTIME-FILES: GATE-BROKEN — '--' 之后没有命令; 拒绝空跑（空跑必然 unchanged, 是假绿）\n" >&2
  exit 2
fi

snapshot() {
  # 逐行输出 "<sha256|absent>  <path>"；固定项在前（顺序与 WATCHED_FIXED 一致），
  # glob 项在后，**显式按字节序排序**（`LC_ALL=C sort`）。
  #
  # ⛔ M13 更正（CARD-W4-3b，2026-09-05 实测）：上一版这里写的是「compgen -G 的展开
  #    结果本身就按 collating sequence 排好序，所以不必引入外部 sort」——**这句是错的**，
  #    而且它是**未经实测**就写下的断言。在绑定环境 GNU bash 3.2.57(1)-release
  #    (arm64-apple-darwin25) 上实测（六个文件 p__{zeta,alpha,Mid,beta,10,2}.jsonl）：
  #      * `compgen -G "p__*.jsonl"`  → alpha, 2, Mid, zeta, beta, 10   ← **readdir 顺序**
  #      * `for f in p__*.jsonl`      → 10, 2, alpha, beta, Mid, zeta   ← 排序（同 ls）
  #    `LC_ALL=C` 与默认 locale 下 compgen 的输出**完全一致**，可见它压根没走排序。
  #    也就是说 pathname expansion 排序、`compgen -G` 不排序，两者不能互相推断。
  #    后果：目录里增删文件会让 readdir 顺序重排，同一批内容在 before/after 排成不同
  #    顺序 ⇒ 字符串不等 ⇒ 判 CHANGED，**假红**。假红比假绿轻，但会把门推向「大家都
  #    知道它爱误报」，下一个人就来放宽它 —— 所以照样得修。
  #    修法用 `LC_ALL=C` 钉死字节序：locale 会改变 sort 的比较规则，不钉死的话
  #    before/after 之间只要环境变量不同就能排出两个顺序（本仓吃过这个亏）。
  # hash 管道任何一环失败（shasum 出错 / 结果非 64 位十六进制）都判门损坏，
  # 不允许「空 digest 前后相等 = unchanged」的假绿。
  local f digest g
  local -a targets=("${WATCHED_FIXED[@]}")

  # ⛔ compgen 可用性自检 —— 必须先于任何 `|| true` 的容错。
  #    初版把展开写成 `compgen -G "$g" || true`：`|| true` 本意只是吞掉「无匹配」
  #    （compgen -G 无匹配时返回 1，这是正常情形），但它**同时吞掉了「compgen 本身
  #    坏了/被劫持」**——两种情况在返回码上不可区分。后果是 glob 项**整组静默消失**，
  #    快照退化成只剩固定项，门照样打印 `unchanged` ⇒ 假绿。
  #    自检用一个**必然匹配**的字面路径（脚本开头已断言 app/main.py 存在）：它既不含
  #    通配符、又必须原样回显，compgen 一旦不是真 builtin 就对不上。
  local __cg_probe __cg_expect="${BACKEND_DIR}/app/main.py"
  __cg_probe="$(builtin compgen -G "$__cg_expect" 2>/dev/null)" || __cg_probe=""
  if [ "$__cg_probe" != "$__cg_expect" ]; then
    builtin printf 'RUNTIME-FILES: GATE-BROKEN — compgen 自检失败（期望 %s，得到 %s）；glob 展开不可信，拒绝给出 unchanged\n' \
      "$__cg_expect" "${__cg_probe:-<空>}" >&2
    exit 1
  fi

  # ⛔ glob 必须**每次快照都重新展开**：命令跑完后才被创建出来的 journal，只有
  #    在 after 这一次展开里才看得见。把展开结果算一次缓存起来 = 新建文件永远
  #    进不了 after 快照，本门就退化成只盯固定项。
  # ⛔ 排序**不能**直接串进 `compgen … | sort || true` 那条管道：`|| true` 是给
  #    「compgen 无匹配（rc=1，正常情形）」用的，串进去之后 **sort 自己坏掉**也会被
  #    同一个 `|| true` 吞掉 —— glob 项整组静默消失、门照样打印 unchanged，正是上面
  #    compgen 自检要防的那类假绿的翻版。所以分两步：无匹配照旧容错，排序失败 fail-closed。
  local __raw __sorted
  for g in "${WATCHED_GLOBS[@]}"; do
    __raw="$(builtin compgen -G "$g" || true)"
    [ -n "$__raw" ] || continue
    __sorted="$(builtin printf '%s\n' "$__raw" | LC_ALL=C "$SORT_BIN")" || {
      builtin printf 'RUNTIME-FILES: GATE-BROKEN — glob 展开排序失败（%s），拒绝给出结论\n' \
        "$SORT_BIN" >&2
      exit 1
    }
    while IFS= read -r f; do
      [ -n "$f" ] && targets+=("$f")
    done <<<"$__sorted"
  done
  for f in "${targets[@]}"; do
    if [ -f "$f" ]; then
      digest="$(hash_stdin <"$f")" || {
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — sha256 失败: %s\n' "$f" >&2
        exit 1
      }
      if [[ ! "$digest" =~ ^[0-9a-f]{64}$ ]]; then
        builtin printf "RUNTIME-FILES: GATE-BROKEN — sha256 结果非 64-hex: '%s' (%s)\n" "$digest" "$f" >&2
        exit 1
      fi
      builtin printf '%s  %s\n' "$digest" "$f"
    else
      builtin printf 'absent  %s\n' "$f"
    fi
  done
}

# snapshot 失败必须**先于** wrapped command 拦截 —— 此时还没有 set -e，
# $( ) 内的 exit 1 不会中止脚本，必须显式查赋值返回码。
if ! BEFORE="$(snapshot)"; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — before snapshot 失败，拒绝执行被包裹命令\n' >&2
  exit 1
fi
builtin printf '=== RUNTIME-FILES before (%s) ===\n' "$("$DATE_BIN" '+%Y-%m-%d %H:%M:%S %z')"
builtin printf '%s\n' "${BEFORE}"
builtin printf '=== 执行被包裹命令 ===\n'
builtin printf '$ %s\n' "$*"

set +e
# 子壳执行：builtin（`exit 0`）/ eval / 函数定义都死在子壳里，无法篡改本壳的
# snapshot 函数、BEFORE 变量或跳过 after 快照。PATH 只在子壳里恢复成调用者的
# ——门自己的工具解析始终锁在系统目录（卡文 (h)：仅给 wrapped command 恢复 PATH）。
(
  PATH="${CALLER_PATH}"
  export PATH
  "$@"
)
CMD_RC=$?
set -e

if ! AFTER="$(snapshot)"; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — after snapshot 失败\n' >&2
  exit 1
fi
builtin printf '=== RUNTIME-FILES after (%s) ===\n' "$("$DATE_BIN" '+%Y-%m-%d %H:%M:%S %z')"
builtin printf '%s\n' "${AFTER}"
builtin printf 'WRAPPED-COMMAND-EXIT: %s\n' "${CMD_RC}"

if [ "${BEFORE}" != "${AFTER}" ]; then
  builtin printf 'RUNTIME-FILES: CHANGED\n'
  builtin printf -- '--- diff (before vs after) ---\n'
  if [ -x "$DIFF_BIN" ]; then
    "$DIFF_BIN" <(builtin printf '%s\n' "${BEFORE}") <(builtin printf '%s\n' "${AFTER}") || true
  fi
  exit 1
fi

builtin printf 'RUNTIME-FILES: unchanged\n'
exit "${CMD_RC}"
