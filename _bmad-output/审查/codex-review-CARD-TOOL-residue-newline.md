> 批次: BATCH-2026-09-05-第十二批 · 车道 Y4 · 卡 CARD-TOOL-residue-newline round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-residue-newline.md)"`
> 审查绑定: 本卡唯一代码 commit `9b4acf62`（代码面只有 `lefthook.yml`，
> sha256 = `e116df5b23bfa49fc0a03fbb61c84852b308d62297d0a35870dfbae18b938afa`）。
> **审后未再改 `lefthook.yml`**——整改只落在 `_bmad-output/`（c2 重跑、b3x 勘误、验收单），
> 故仍绑定；判据 `git diff --stat 9b4acf62 HEAD -- . ':(exclude)_bmad-output'` 为空。
> ⚠️ **prompt 第 6 问写的“修后 sha = cf1346a2…”是陈旧值**（那是被后续整改取代的中间块）。
> 外审当场发现并拒绝继承，改绑当前 `e116df5b…`（见正文「对象绑定差异」）。本单结论按 `e116df5b` 读。
> 会话头自证（抄 .stderr 会话头块，stderr 本身不入库；字面前三行是
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`
> `session id: 01a0747f-2e01-70c1-9e70-f9c00d79bd3d` · `sandbox: read-only`

---

**换行文件名的修复成立；“扫描未完成必定阻断”的整体声明不成立，仍有修前已有的缺口。另有对象版本差异：本次实际审到的终稿不是题面给出的 SHA。**

全程未修改文件、暂存区或配置。现场执行的是只读核验和内存／管道探针，没有重跑需要创建暂存文件的完整 hook 场景。

**1. NUL 读取覆盖：成立，限本次验证的解释器与完整 NUL 记录流。**

依据：[lefthook.yml:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:370)、`:377–390`。

实际用 Python `subprocess.run` 向四种 shell 注入 12 条 NUL 记录，运行：

```sh
set -u
while IFS= read -r -d '' f; do printf '%s\000' "$f"; done
```

另将循环体换成真实子进程调用，核对收到的 argv：

```sh
"$1" -c 'import os,sys; os.write(1,os.fsencode(sys.argv[1])+bytes([0]))' "$f"
```

输入覆盖换行、TAB、CR、反斜杠、单双引号、前导 `-`、`./`、中文及其他非 ASCII、255 字节单个名字、1023 字节路径、首尾空白，以及：

```python
bytes(i for i in range(1, 256) if i != 47)
```

关键输出；以下结果在 `LC_ALL=C` 和 `en_US.UTF-8` 下相同：

```text
/bin/sh   read+printf     rc=0 records=12 bytes_equal=True bad=[]
/bin/sh   read+child-argv rc=0 records=12 bytes_equal=True bad=[]
/bin/bash read+printf     rc=0 records=12 bytes_equal=True bad=[]
/bin/bash read+child-argv rc=0 records=12 bytes_equal=True bad=[]
/bin/zsh  read+printf     rc=0 records=12 bytes_equal=True bad=[]
/bin/zsh  read+child-argv rc=0 records=12 bytes_equal=True bad=[]
/bin/dash                rc=0 records=0
stderr: read: Illegal option -d
```

因此，在支持该读法的已测 shell 中，**未发现任何所列名字类别在读取或传参时丢失、转义或拆分**。`IFS=` 保留空白，`-r` 保留反斜杠，NUL 分隔保留换行；`"$f"` 保持一个参数，后续 `--literal-pathspecs` 与 `--` 分别防止 pathspec 解释和选项解释。

我还实际运行了：

```awk
BEGIN { F = ENVIRON["F"]; printf "%s", F }
```

换行名、反斜杠名和上述 254 字节载荷在两个 locale 下均：

```text
equal=True rc=0
```

边界：没有逐一创建这些真实 Git 文件；验证的是读取、argv 和 ENVIRON 的字节保持。超过文件系统长度限制的名字不属于该文件系统的合法输入；1023 字节探针也不是任意长度保证。`dash` 的失败由第 4 问的自证拦截。

**2. FAILED 路径：部分成立。已有显式守卫未退化，但完整 fail-closed 声明不成立。**

实际逐行读取命令：

```sh
git diff HEAD~1 HEAD -- lefthook.yml
awk 'NR>=345 && NR<=405 {print NR": "$0}' lefthook.yml
git show HEAD~1:lefthook.yml |
  awk 'NR>=345 && NR<=393 {print NR": "$0}'
```

下表的“旧／新”均为对应版本行号；静态分支核对与现场探针分开说明：

| 扫描失败位置 | 旧／新行号 | 最终结果 |
|---|---|---|
| `mktemp` 失败 | 349–350／相同 | 显式 `exit 1` |
| 枚举命令或 `> names` 失败 | 353–356／相同 | 显式 `exit 1` |
| `tr`、其输入或输出重定向失败 | 357–358／删除 | 旧版 `exit 1`；新版无此操作 |
| 自证得到的串不符 | 无／361–368 | 新版 `exit 1`；dash 现场验证 |
| 初始化 `hits` 失败 | 359／369 | 无显式守卫；本机 sh 退出 1，普通 bash 可继续 |
| 主循环输入重定向失败 | 379／390 | **未置 FAILED，可最终 0** |
| 主循环 `read` 报错或读到未终止记录 | 360、379／370、390 | **未置 FAILED，可最终 0** |
| 单文件 diff 命令或 `> d` 失败 | 367–369／377–379 | `FAILED=1`，最终 1 |
| awk 非零，包括读输入失败、`>> hits` 失败 | 371–378／381–389 | `FAILED=1`，最终 1 |
| 一个文件失败、后续文件成功 | 380–382／391–393 | FAILED 保留，最终 1 |
| `-s hits` 检查不能取得有效状态 | 384／395 | 无错误区分，条件为假可走 OK |
| 已进入命中分支后 `cat hits` 失败 | 387–391／398–402 | 后面仍显式 `exit 1` |

关于 `>> "$TMPD/hits" || ...`，**`||` 检查整个 awk 简单命令的状态，包括重定向失败**。重定向失败时 awk 根本没有启动。

实际故障探针的运行体：

```sh
FAILED=0
awk 'BEGIN { print "AWK_RAN" > "/dev/stderr" }' /dev/null \
  >> /dev/null/no-such-child ||
  { R=$?; printf 'guard_rc=%s\n' "$R"; FAILED=1; }
printf 'FAILED=%s\n' "$FAILED"
if [ "$FAILED" -ne 0 ]; then exit 1; fi
```

本机 `/bin/sh` 输出：

```text
Not a directory
guard_rc=1
FAILED=1
rc=1
```

没有 `AWK_RAN`。dash 的重定向错误状态为 2，但最终同样是 1。

我用 `os.pipe`／`pass_fds` 提供两条记录，实际运行 `done < /dev/fd/N`；第一个 awk `exit 2`，第二个成功：

```text
/bin/sh   awk_rc=2  n=2 FAILED=1  rc=1
/bin/bash awk_rc=2  n=2 FAILED=1  rc=1
/bin/dash awk_rc=2  n=2 FAILED=1  rc=1
```

所以 **`done < file` 不产生管道子 shell，FAILED 的赋值留在当前 shell**；第 4 问的 PROBED／PROBE_ACC 探针也验证了这一点。

**HIGH，存量：主循环输入／读取错误可以被当成扫描完成。** 实际执行：

```sh
FAILED=0
while IFS= read -r f; do FAILED=1; done < /dev/null/no-such-child
R=$?
printf 'loop_rc=%s FAILED=%s\n' "$R" "$FAILED"
if [ "$FAILED" -ne 0 ]; then exit 1; fi
printf 'OK\n'
```

本机 sh 输出：

```text
Not a directory
loop_rc=1 FAILED=0
OK
rc=0
```

另将 NUL 循环输入重定向到指定 evidence 目录，制造真实读取错误：

```text
read: read error: 0: Is a directory
loop_rc=0 FAILED=0
OK
rc=0
```

输入 `a\0partial` 则得到：

```text
N=1 tail=partial FAILED=0
OK
rc=0
```

触发条件是**名字列表打不开、读取报错或记录流被截断**，不是普通合法文件名字节。上述是故障语义探针，没有声称正常成功的 Git 枚举会生成损坏记录。旧版同样缺少主循环守卫。位置：[lefthook.yml:390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:390)。

**MEDIUM，存量、依赖解释器：`hits` 初始化失败没有统一出口。** 对真实失败目标执行 `: > /dev/null/no-such-child`，本机 sh 退出 1；普通 bash 则继续到 `OK`、rc=0。如果随后没有命中其他失败守卫，就可放行。当前实测的 bash-as-sh 会阻断，因此不能把普通 bash 结果说成本机 hook 已发生的漏检。

此外，实际验证了 UAT 提到的 awk 参数问题：让 awk 接收 `x=value/d`，它把参数当赋值并消费循环 stdin；两条 NUL 记录只循环一次：

```text
N=1 FAILED=0
OK
rc=0
```

这证实了 awk 语义；**相对 TMPDIR 导致整个门触发该路径的场景，本次没有落盘复现**。

删除“文件名解码失败”守卫本身合理：`tr` 操作和其守卫一起消失，没有把仍存在的 `tr` 错误改成成功。但这不能支持“所有未完成路径都已覆盖”。

**3. 其他输入形态：部分成立。排除匹配已验证；子模块和符号链接缺少完整实测。**

我通过 `subprocess.run(['/bin/sh','-c',script,'probe',*paths])` 实际执行原样三条 case：

```sh
for f do
  case "$f" in
    backend/scripts/g32b_mutation_gates.py) printf 'EXEMPT_EXACT\n'; continue ;;
    backend/scripts/g32cb_mutation_gates.py) printf 'EXEMPT_EXACT\n'; continue ;;
    _bmad-output/*) printf 'EXEMPT_TREE\n'; continue ;;
  esac
  printf 'DIFF_BRANCH\n'
done
```

关键结果：

| 输入 | 实测分支 |
|---|---|
| 两个脚本的精确路径 | `EXEMPT_EXACT` |
| `_bmad-output/a.txt`、`_bmad-output/nested/a.txt` | `EXEMPT_TREE` |
| `./_bmad-output/a.txt` | `DIFF_BRANCH` |
| `./backend/scripts/g32b_mutation_gates.py` | `DIFF_BRANCH` |
| `foo/_bmad-output/a.txt` | `DIFF_BRANCH` |
| `_bmad-output-copy/a.txt`、`has_bmad-output.txt` | `DIFF_BRANCH` |
| `_bmad-output` 这个单文件 | `DIFF_BRANCH` |
| `backend/scripts/g32b_mutation_gates.py.copy` | `DIFF_BRANCH` |
| `submodule/a.txt`、`symlink.txt` | `DIFF_BRANCH` |
| 人工输入 `_bmad-output/../production.txt` | `EXEMPT_TREE` |

最后一项只说明 glob 不规范化路径，**没有证明它能成为 Git 枚举输出，不能据此报 Git 绕过**。

针对 `./`，实际运行：

```sh
git --no-pager --literal-pathspecs diff HEAD~1 HEAD -- lefthook.yml
git --no-pager --literal-pathspecs diff HEAD~1 HEAD -- ./lefthook.yml
```

输出比较：

```text
两者 rc=0 bytes=2599
equal=True
```

因此 `./` 不会利用这三条 case 逃掉扫描；人工加前缀反而可能使豁免路径进入 diff。引用：[lefthook.yml:372](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:372)。

对象类型方面：

- **子模块**：case 没有特殊豁免；父仓暂存的是 gitlink，子仓内部文件并不是父仓逐文件暂存的新增行。本块没有递归扫描。不能直接把子仓内容未扫描判成父仓新增行漏扫。
- **符号链接 A/M**：case 没有特殊豁免；需区分链接目标字符串与被链接文件内容。现有证据没有真实暂存符号链接探针，**本次无法验证其完整阻断结果**。
- **类型转换 T**：修前修后的枚举和单文件 diff 都只选 `AM`，静态确定没有包含 `T`。普通文件与符号链接互换的真实暂存场景，本次未构造，不能报成现场复现。

UAT [第 227 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-residue-newline-2026-09-06.md:227)也明确写了“子模块路径 / 符号链接未测”。所以能确认三条设计内豁免及相似名字不会误豁免，不能签“所有对象形态均覆盖”。

**4. 解释器证据：部分成立。足以支撑该次本机运行，不能推广到所有 sh。**

实际读取：

```sh
nl -ba _bmad-output/审查/evidence-residue-newline/a-shell-probe-20260906T025356.txt
nl -ba _bmad-output/审查/evidence-residue-newline/d-selftest-mutation-matrix-20260906T100939.txt
```

a-shell 的关键行：

```text
11 PROBE-0=sh
12 PROBE-BASH_VERSION=3.2.57(1)-release
14 PROBE-args=sh -c ...
28 PROBE-rec1=[a
29 b]
30 PROBE-rec2=[c]
31 PROBE-nul-records=2
37 rc=0
```

它支持“该次 lefthook 2.1.6 真 hook 所起的 sh 能保持内嵌换行并读出两条记录”。它没有固定所有机器的 sh 实现，也没有证明未来 lefthook 版本或 PATH 不变。

本次另现场确认：

```text
/bin/sh   BASH_VERSION=3.2.57(1)-release  posix on
/bin/bash BASH_VERSION=3.2.57(1)-release  posix off
/bin/dash BASH_VERSION=none
/bin/zsh  ZSH_VERSION=5.9
```

**当前代码已经没有 PROBED，也没有数值期望 2。** [lefthook.yml:361](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:361)实际是：

```sh
printf 'a\\\nb\000 c\000' > "$TMPD/probe"
PROBE_ACC=""
while IFS= read -r -d '' _p; do PROBE_ACC="$PROBE_ACC|$_p"; done < "$TMPD/probe"
if [ "$PROBE_ACC" != "$(printf '|a\\\nb| c')" ]; then
```

我实际运行各 shell 的旧／新 `printf`，再经 `< /dev/fd/N` 执行相应判据：

```text
所有四种 shell：
旧载荷 hex = 61006200
新载荷 hex = 615c0a6200206300

/bin/sh   旧：PROBED=2 PASS rc=0；新：PASS rc=0
/bin/bash 旧：PROBED=2 PASS rc=0；新：PASS rc=0
/bin/dash 旧：PROBED=0 FAILED rc=1；新：FAILED rc=1
/bin/zsh  旧：PROBED=2 PASS rc=0；新：PASS rc=0
dash stderr：read: Illegal option -d
```

所以：

- `printf 'a\000b\000'` 在已测 dash 中正确产生两个 NUL；问题不在 printf。
- 旧方案中 `PROBED=0` 时，`[ "$PROBED" -ne 2 ]` 确实为真并退出 1；数字 `2` 是独立字面量。
- 当前期望是另一份字面量，不由 `PROBE_ACC` 派生；但载荷和期望共用 printf 解码，不能宣称对 printf 本身构成完全独立的验证。
- “非 bash”不等于失败：zsh 也通过；其他未测实现不作结论。
- 自证验证自己的读取循环，不能保证主循环后来没有被改坏。

实际运行 `bash -n`、`sh -n`、`dash -n` 检查 `g-blk-extract-postfix.sh`，均 rc=0。这也证实语法通过不能发现 dash 的运行期 `read -d` 问题。

**MEDIUM，兼容性限制：**当实际执行该块的 sh 不支持 `read -d`，例如本次 dash，连干净暂存面也会被自证阻断。这符合 fail-closed 方向，但不能表述成跨平台正常提交行为不变。

**5. 卡文符合性与越界：部分成立。硬边界通过；有轻微文字偏差及读取范围限制。**

实际命令：

```sh
nl -ba '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-C.md'
git diff HEAD~1 HEAD -U0 -- lefthook.yml
```

关键输出：

```text
@@ -357,2 +357,12 @@
@@ -360 +370 @@
@@ -371 +381,2 @@
@@ -379 +390 @@
```

| hunk | 修前区间 | 修后区间 |
|---|---:|---:|
| tr／自证 | 357–358 | 357–368 |
| 读取方式 | 360 | 370 |
| ENVIRON | 371 | 381–382 |
| 输入文件 | 379 | 390 |

**所有新旧 hunk 坐标均在 345–399 内。**尾部原有代码平移到 404，不等于修改了窗口外的原代码。

对新旧版本字节执行 Python 不变量核对，输出：

```text
marker_count=0
priority_entries=0
command_names_equal=True
marker_and_exclusions_equal=True
HEAD_equals_worktree=True
```

自证与 ENVIRON **不构成功能越界**：

- [卡文:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-C.md:15)明确称三处修改为“修法草案”。
- 自证直接服务于 `:19` 的解释器选择及 `:23` 的失败语义。
- ENVIRON 直接服务于 `:20` 的换行名阻断、真实路径报告。
- `:41–42` 没有将草案列为允许改动的穷尽清单。

**LOW，文字符合性：**卡文 `:24` 写“可加一行”注释，实际新增四行，位于 `lefthook.yml:357–360`。按字面严格核对，不能说完全一致；没有运行时错误。UAT 自报“登记不阻断”不等于独立授权依据。

另外，本读取面只提供 `lefthook.yml` 的 diff，**不能据此独立认证整个提交没有修改其他文件**。

**6. transcript 可信度：部分成立。现存终稿没有绑修前 SHA，但题面 SHA 已不对应当前对象。**

实际执行：

```sh
git show HEAD~1:lefthook.yml | shasum -a 256
git show HEAD:lefthook.yml | shasum -a 256
shasum -a 256 lefthook.yml
rg -n 'sha|SHA|^rc=|^###|ASSERTED|commit ' \
  _bmad-output/审查/evidence-residue-newline
```

现场结果：

```text
P / HEAD~1:
f3aa7fecde1dd4b4310aad8cdb6fccae5cba9857e214f163206cb03ac3f28377

F / HEAD 与工作树:
e116df5b23bfa49fc0a03fbb61c84852b308d62297d0a35870dfbae18b938afa
```

中间态记为 I：

```text
c57a7b7e7367b96c214b3d70e27368b4293d89adcedbfb8824e3ab5951a5e092
```

以下文件均在指定 evidence 目录；名字按唯一前缀缩写，行号对应完整文件：

| 文件 | SHA 行／值 | 标签核对 | 末行 |
|---|---|---|---|
| a-shell-probe…025356 | 无 | 环境探针，不能文件级绑定 | :37 rc=0 |
| b1-prefix-newline…025543 | :3、20 P | 修前一致 | :21 rc=0 |
| b2-prefix-plainname…025553 | :3、24 P | 修前一致 | :25 rc=1 |
| b3-postfix-newline…100906 | :2 F | 终稿一致 | :29 rc=1 |
| b3x-interim-awkV…025752 | :9、30 I | :1 明确中间态 | :31 rc=1 |
| b4i-postfix-empty…100906 | :2 F | 终稿一致 | :24 rc=0 |
| b4ii-postfix-normalface…100906 | :2 F | 终稿一致 | :21 rc=0 |
| c1-literal-pathspecs…100906 | :2 F | 终稿一致 | :30 rc=1 |
| c2-no-color…100906 | :2 F | 终稿一致 | :51 rc=1 |
| c3-no-renames…100906 | :2 F | 终稿一致 | :25 rc=1 |
| c4-diff-filter-AM…100906 | :2 F | 终稿一致 | :66 rc=1 |
| c5-mktemp…100906 | :2 F | 终稿一致 | :21 rc=1 |
| c6-awk-filehead…100906 | :2 F | 终稿一致 | :31 rc=1 |
| c7-z-tabname…100906 | :2 F | 终稿一致 | :27 rc=1 |
| c8-backslash-name…100906 | :2 F | 终稿一致 | :27 rc=1 |
| d-selftest-mutation-matrix…100939 | 无 | 不能文件级绑定 | :26 rc=0 |
| g-syntax…100955 | :3 F | 终稿一致 | :10 rc=0 |
| g-blk-extract-postfix.sh | 无 | 现场比对等于当前 run 体 | 脚本，无 rc |
| judge-135-postcommit…101434 | 无；:1 记 commit | `9b4acf62` 与当前 HEAD 一致 | :20 rc=0 |

提取当前 347–404 行、删除八空格缩进后，与 `g-blk` 实际逐字节比较：

```text
EXTRACT_CURRENT_347_404_LINES 58
EXTRACT_BYTE_EQUAL True
双方 SHA256:
94481ca9099e78af3581f4370e772afbd6ad2114615733de69359898d7b1f52b
```

**MEDIUM，对象绑定差异：**题面 `cf1346…093e3` 在当前证据目录中出现次数为 0，当前文件也不是该 SHA。若把本次结论用于它，会错绑对象。本次结论只绑定当前 `e116df…938afa`；UAT [第 47 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-residue-newline-2026-09-06.md:47)也记录这个终稿 SHA。

**LOW，c2 基线证据矛盾。**实际读取：

```sh
nl -ba _bmad-output/审查/evidence-residue-newline/c2-no-color-20260906T100906.txt
```

关键行：

```text
10 基线: 不设 color 配置
11 # color.ui=always color.diff=always
29 # hits 计数(基线) = 2 ; rc=1
30 color.ui=always + color.diff=always
31 # color.ui=always color.diff=always
49 # hits 计数(color always) = 2 ; rc=1
```

两跑结果相等有记录，但**第一跑确实没有设置颜色配置**，不能由这份记录独立证明。

**LOW，失效引用：**`b3x:5` 指向不存在的 `b3…025916.txt`；现存终稿是 `b3…100906.txt`。中间态头部标识清楚，因此不是终稿冒充。

最后，SHA 头部与 `[ASSERTED == 修后终稿]` 的一致性已经核对；**文本声明本身不能证明历史生成脚本确实执行过硬断言**。本次未复跑历史暂存场景，a-shell 与 d-selftest 又没有文件 SHA，因此对它们保留上述绑定限制。


