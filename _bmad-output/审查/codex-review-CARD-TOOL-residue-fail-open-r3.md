> 批次: BATCH-2026-09-11-第十四批 · 车道 T8 · 卡 CARD-TOOL-residue-fail-open round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-residue-fail-open-r3.md)"`
> 审查绑定: `f9e31034..9020a1a5`（本轮送审时 HEAD = `9020a1a5`，与该轮存档正文自述的绑定一致）
> 会话头自证（抄 .stderr 的 codex 版本行 / model 行 / reasoning 行，带行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

**原两项 MEDIUM 的指定反例已封住，但 LOW 注释整改仍未完成；同一临时文件故障模型下另有一项 MEDIUM。未发现 r3 改坏已有封堵。**

复核绑定 `9020a1a5ecfdedecf1c80981688d6701e34ea60c`，当前 `lefthook.yml` 与该提交逐字节一致。全程未运行 hook、对照脚本，未修改或暂存文件。以下新反例均为静态推导，未实测。

[级别 MEDIUM] `d` 与 `dn` 指向同一普通文件时，新检查仍会放过被截为空的 diff。  
文件:行　[lefthook.yml:539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:539)，`tr < "$TMPD/d" > "$TMPD/dn"`；两处检查在 531、542 行。  
依据　沿用 [M3 的预置临时对象模型](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/case-m3-dn-dev-null.sh:21)，将预置对象改为 `dn → d`：

1. 正常 Git 写出含标记的 `d`，第一处检查通过。
2. shell 打开 `< d`，随后 `> dn` 截断同一个 inode。
3. 正常 `tr` 读到 EOF、退出 0；`dn` 的 `-f/-r` 跟随链接，第二处检查也通过。
4. awk 空输入、退出 0；`hits` 是正常空文件，计数与哨兵不变，最终 OK。

这不需要伪造 Git/tr/awk 输出，也不需要并发竞争；**需要能够预置私有临时目录中的对象**，与本卡既有故障注入前提相同。[Bash 重定向语义](https://www.gnu.org/s/bash/manual/html_node/Redirections.html)、[文件测试语义](https://www.gnu.org/software/bash/manual/html_node/Bash-Conditional-Expressions.html)支持上述推导。  
建议　在写入前拒绝已有符号链接，并在归一化前拒绝 `d -ef dn`，保留写后类型检查。单加 `-L` 不覆盖硬链接造成的同 inode 情形；这些检查仍不承诺抵御持续并发替换。

[级别 LOW] “确切范围”注释仍有失实保证和遗漏，不能判为整改完成。  
文件:行　[lefthook.yml:406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:406)，rc 范围说明；另见 386、441、451、493 行。  
依据　逐条核对结果如下：

| 注释声明 | 实现核对 |
|---|---|
| tail / od / wc 分段核 rc | **成立**：445、448、469 行均有 `if !`。 |
| tr 分段核 rc | **部分成立**：466、539 行有守卫；453、472 行两次赋值没有。 |
| awk 核 rc | **成立**：553 行 `||` 设置 `FAILED=1`。 |
| tail / od / tr / awk 固定 C | **成立**：这些调用均显式设置。 |
| 未核 rc 的 `$()`“只有两处” | **不成立**：493 行的 `$(printf …)`也是一处。全块共四处命令替换，另一个是已受守卫的 424 行 `mktemp`。若只指字节规范化，应明确限定。 |
| tr 失败“只会给出空串或非数字” | **不成立**：输出完整数字或数字前缀后，仍可能因后续错误或信号非零退出。输出有效不能证明命令成功。 |
| 没单独核 rc 的命令清单完整 | **不完整**：遗漏 426 行的 **trap 注册本身**以及各处 `echo`。 |
| 三个临时文件都在“用之前”核类型 | **不成立**：`hits` 类型检查只有末尾 581 行，写入和命中读取都在此前。 |

此外，441 行仍保留“每一段……逐段核 rc”的无例外声明；451 行又重复了错误的失败输出保证。Apple 的 `tr` 实现也是先输出、后检查错误，不能推出“非零退出必然没有有效数字”。[Apple tr 源码](https://raw.githubusercontent.com/apple-oss-distributions/text_cmds/main/tr/tr.c)

为完整区分：`read`、`[` 的状态被循环或条件使用，但没有分别区分 EOF／错误、false／测试错误；固定的 `set -u`、纯赋值及 `continue` 也没有另设守卫。诊断 `echo` 失败通常不改变后续阻断，最后的 586 行 `echo` 则直接决定正常结束状态。

**上述 tr 问题本身尚不足以证明另一条标记漏检**：数字前缀通常会被 LASTB 或最终计数检查挡住，因此合并计一项 LOW，不另算 MEDIUM。  
建议　给两次 `tr` 赋值直接补失败退出；统一修正 406、441、451 行说明，补全例外清单，并把 `hits` 写成“末尾复核”。

其余问题的判定如下。

**1．检查位置与正常误判。**  
两处检查都位于写成功后、下游读取前，针对 `/dev/null` 的位置正确。没有使用 `-s`，所以 **0 字节可读普通文件会通过**。检查失败先设 `FAILED=1` 再跳过文件，最终必然阻断，不会把跳过算作扫描成功。

`-f/-r` 确实跟随符号链接：指向 `/dev/null` 被拒，指向普通文件被接受；后者造成上述同 inode 缺口。`$TMPDIR` 目录本身经过符号链接、含空格或相对路径首段含 `=`，不因新增谓词而误判。特殊文件系统的权限、可见性及 `stat/open` 一致性**未验证**，需要指定文件系统和挂载配置才能判断。

**2．循环内 stdin 已正确隔离。**

| 命令／操作 | 位置 | stdin |
|---|---|---|
| `read` | 507 | `names`，预期消费者 |
| `git` | 523–525 | `/dev/null` |
| `tr` | 539 | `d` |
| `awk` | 545–553 | `dn` |
| `[` | 509、510、531、542 | 继承 `names`，正常实现不读取 |
| `echo` | 526、532、540、543、553 | 继承 `names`，正常实现不读取 |
| `continue`、赋值、算术及控制结构 | 循环各分支 | 不额外消费 stdin |

`tr/awk` 的显式 `<` 足够；打开失败会进入错误分支，不会回退读取 `names`。awk 内的 `printf` 是输出操作。572 行 `cat` 已在循环之外。**未找到另一个遗漏隔离的正常 stdin 消费者。**

**4．awk 固定 C 未见识别副作用。**  
实际还用了 `substr()`、ASCII 正则前缀及数字转换。`substr($0,2)` 只剥掉 ASCII `+`。结合纯 ASCII 标记、hunk 格式，以及同为 `20200816` 的 Apple 官方实现中的字节读取、比较和截取逻辑，未见 C locale 导致高位正文丢失或标记漏检。[Apple awk 实现](https://raw.githubusercontent.com/apple-oss-distributions/awk/main/src/run.c)

本机 runner 实际选中的二进制与源码的严格绑定、全部高位字节运行验收仍为**未验证**，不能把源码分析当作实测。

**5．EXPECTED 与既有封堵未见回归。**  
正常情况下，`wc -c → 文件 → tr` 得到相同计数。哨兵先追加再统计，`SEEN` 又先于哨兵分支递增，两边仍为 `N+1`。新增检查不会拒绝正常空 diff，也不会在失败后放行。

已独立比较：允许名单及计数注释 r2→r3 不变；NUL 自证判定体与基线一致；整个 residue 注释及代码块之外的 `lefthook.yml` 与 `08100483` 逐字节相同，包括指定 T8-G 邻居，仅比较字节，未审查其内容。

**6．剩余放行路径，按所需前提排列。**

| 所需前提 | 可得结论 | 分类 |
|---|---|---|
| 标记位于允许名单，或只在未新增的旧行 | 按设计不扫描 | 明示范围，不计缺陷 |
| 两次未守卫的 tr 非零退出，但已输出可接受数字 | 可继续执行；单独造成残留漏检未证明 | 上述 LOW |
| 能预置 `d/dn` 为同一普通文件 | 可静态推出含标记仍 OK | 上述 MEDIUM，本块可补的检查缺口 |
| 同用户进程能在检查与读取之间改动临时对象，例如扫描后清空 `hits` | 当前路径检查不保证对象或内容稳定 | 并发边界；本轮未实测 |
| 能任意替换 Git/awk，使其伪造空输出并返回 0 | 本块无法从受骗输出恢复真实内容 | 工具可信边界，不能与有限故障检查混为一谈 |

在工具正常、临时对象独立稳定、索引不变的前提下，**本轮未再论证出扫描范围内普通文件新增行的其他漏检路径**。

存档方面，13 个故障对照脚本的汇总准确：12 个双解释器 SEALED，6-5 为 bash SEALED／sh NOT-SEALED；M3 两个变体使实际 CASE 结果为 14 条。6-5 的 sh 旧版本来就阻断，新版增加诊断，未夸大收益。额外 `case-e` 实际只跑 bash。

当前 165 行抽块的 SHA-256 为：

`073fe964a8b7e23b5ed17c9b63657c128082f5fab44340777d88226601750a0f`

它及全文件摘要均与 r3 对照日志匹配；M3 旧块也与 `f9e31034` 匹配。不过，**真 hook 三控的历史执行绑定仍未验证**：[三控存档](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r3-controls-judges-20260914T204658.txt:1)只有 `0/1/1` 摘录，缺当次配置摘要、完整调用及原始输出。另外 8-2、M2 在抽块摘要之后注入故障，基础块可绑定，实际执行的注入后文件摘要未保存。这些是证据限制，不另算代码缺陷。

BLOCKER=0 HIGH=0 MEDIUM=1 LOW=1


