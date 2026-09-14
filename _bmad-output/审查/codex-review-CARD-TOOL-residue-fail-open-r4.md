> 批次: BATCH-2026-09-11-第十四批 · 车道 T8 · 卡 CARD-TOOL-residue-fail-open round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-residue-fail-open-r4.md)"`
> 审查绑定: `9020a1a5..158e5a60`（本轮送审时 HEAD = `158e5a60`，与该轮存档正文自述的绑定一致）
> 会话头自证（抄 .stderr 的 codex 版本行 / model 行 / reasoning 行，带行号；stderr 本身不入库）:
> `:4 OpenAI Codex v0.153.3` / `:7 model: gpt-6-astra` / `:11 reasoning effort: ultra`

---

**r3 的同 inode MEDIUM 已封住，未发现 r4 改坏已有封堵；注释 LOW 仍未完全整改。代码封堵可以收口，但目前不能签“两项整改均完成”。**

复核绑定 `158e5a601ca2e61f2a4c39a784bc6b9142e95508`。当前 `lefthook.yml` 与该提交逐字节一致。全程未运行 hook、对照脚本或测试，未修改、暂存文件。

[级别 LOW] “rc 覆盖面的确切清单”仍不完整，删掉了旧版已经登记的两个例外。  
文件:行　[lefthook.yml:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:409)，“rc 覆盖面的确切清单”。  
依据　逐条核对发现：

- **未核清单漏了 `rm`、`cat`**：433 行 trap 内的 `rm`、587 行命中分支的 `cat` 均未单独核 rc；r3 注释原本列出了它们。
- **已核清单漏了 `:` 重定向**：511–512 行明确有 `|| { …; exit 1; }`。
- 若要覆盖全部 shell 命令，还需界定 `set -u`、纯赋值、`continue` 等固定操作；两次 `read` 的状态用于循环条件，但没有分别识别 EOF／读取错误。
- “期望值那个 `$(printf …)`、两次 probe 的 printf”重复包含同一次调用。实际 probe 共两个 `printf`：498、501 行。

建议　**仅补全注释即可**：恢复 `rm`、`cat`，补入已守卫的 `:`；明确 `read` 与固定 shell 操作的范围，并把 probe 写成“生成载荷的 printf、生成期望值的命令替换”。无需为此增加代码守卫。

你要求的其余核对结果如下。

**已列出的“核了 rc”项目全部属实：**

| 声明 | 实现位置及守卫 |
|---|---|
| `mktemp` | 431–432，赋值后的 `||` |
| 两处 `git` | 435–437、531–534，`if !` |
| `tail`、`od`、`wc` | 453–457、477–478，`if !` |
| 哨兵 `printf` | 472–473，`||` |
| NUL 计数 `tr` | 474–475，`if !` |
| NUL 归一化 `tr` | 547–548，`if !` |
| `awk` | 560–568，`||` 设置 `FAILED=1` |

已列的未单独核 rc 项也与实现对应：两次 `tr` 赋值、probe 的 `printf`、trap 注册、各处 `echo`、两个 `while` 的终止状态及 `[` 的错误／false 区分。末尾 `echo` 确实决定正常完成路径的退出状态。

“`tr` 可能输出有效数字后非零退出，语义检查只是部分兜底”的修订准确。明确列出的 `tail/od/tr/awk` 也全部设置了 `LC_ALL=C`。

**文件类型检查时机描述准确。** `d` 在 Git 写后、`tr` 读前检查（539）；`dn` 在归一化写后、awk 读前检查（550）。`hits` 的类型检查只有596行，且仅在未提前阻断、`-s hits` 为假时到达；初始化、追加及可能的命中读取都在此前。

**`-ef` 的位置足以封住本次反例，没有发现正常误判。**

[557–558 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:557)位于两处类型检查之后、awk 之前。同文件时，虽然归一化已经截空了 diff，但仍会先 `FAILED=1` 再 `continue`；580–582 行必然阻断，后续没有清零操作。因此，对“禁止错误放行”而言，不必移到写前才算封住。

- 两文件都不存在：正常会先被类型检查拒绝；`-ef` 本身也不会把“两者不存在”判成同文件。
- `$TMPD` 的父路径经过符号链接：不会把两个独立文件判为同一个。
- Bash 比较的是 **设备号与 inode 的组合**，不是跨文件系统仅比较 inode 数字；符号链接会解析到目标。[Bash 官方文件测试语义](https://www.gnu.org/software/bash/manual/html_node/Bash-Conditional-Expressions.html)
- **POSIX 要区分版本**：Issue 8／POSIX.1-2024 已纳入 `-ef`；旧版 POSIX 不保证。不能笼统称它“非 POSIX”，也不能仅凭解释器名为 `sh` 就保证支持。[Austin Group 最终采纳记录](https://www.austingroupbugs.net/view.php?id=375#c6040)
- 特殊文件系统的身份报告异常、检查期间对象变化：**未验证**，需要具体文件系统、挂载配置及复现场景。

M4 存档的 symlink／hardlink × bash／sh 四组合都进入了同文件诊断并退 1，支持本机两个解释器下的整改结论。

**未发现 r4 控制流回归。** 去除注释比较，唯一可执行改动就是这条 `if -ef` 分支。允许名单、哨兵与计数逻辑、stdin 隔离均未改变。整个 residue 注释及代码块之外的文件字节与 `08100483` 相同，包括指定 T8-G 邻居；这里只做了字节比较。

**剩余放行边界，按所需前提排列：**

| 所需前提 | 能只读论证的结果 | 分类 |
|---|---|---|
| 无标记、标记仅在旧行或允许名单内 | 可以放行 | 已声明扫描范围 |
| 两次未守卫的 `tr` 输出可接受数字后非零退出 | 可以继续执行；**仅此尚不能推出标记漏扫** | 本块已披露的 rc 覆盖缺口 |
| 扫描后另一个进程或后续 hook 再暂存内容 | 最终提交可能包含未扫描内容 | 扫描时点限制；330–339 行已有披露 |
| 能在检查与读取之间替换 `dn`，或在最终判断前清空 `hits` | 路径检查无法保证随后读取的对象、内容不变 | 临时对象并发替换边界 |
| 能替换 Git／awk，使其伪造空结果且返回 0 | 可以骗过后续检查 | 工具可信边界 |

最后两类不能表述成“任何检查都无能为力”：有限预置故障仍能补检查，M4 就是实例；但当前路径检查不承诺抵御任意持续替换或伪造工具。**在正常工具、独立稳定临时对象、固定索引的前提下，本轮未再静态论证出扫描范围内的新增行漏检。**

**证据绑定：基础代码字节成立，全部历史执行字节仍为 PARTIAL。**

独立重算与所有 r4 对照日志一致：

| 对象 | SHA-256 |
|---|---|
| `158e5a60:lefthook.yml` | `7a2761597535957b81faf0a7bbc4b2c59721eca3041b58a41b8f01fb255df8c7` |
| 173 行抽块 | `b1bfdf1f600ac90ab569c42d29a6c901cd18fcbe71b62f6b509c734e6940f523` |

[M4 日志](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r4-out-case-m4-20260914T210559.txt:2)的旧块摘要也与 `9020a1a5` 一致。日志记录提交前 HEAD 为 `9020a1a5`，不妨碍按内容绑定最终提交。

仍缺两类证据：

- **8-2／M2 注入后执行字节：未验证。** [_lib.sh:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/_lib.sh:48)先记录摘要，随后注入覆写脚本，没有再记录执行前摘要。可按存档重建，缺当时摘要供比对。
- **真 hook 三控的完整执行绑定：未验证。** [210647 成功日志](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r4-controls-judges-20260914T210647.txt:2)有路径清单及 `0/1/1`，仍缺当次配置摘要、完整调用、暂存探针 blob OID／字节及完整原始输出。正控路径属于允许名单，只证明该正控放行。[210625 日志](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r4-controls-judges-20260914T210625.txt:2)是命令找不到的失败尝试，不能计入成功证据。

14 个故障对照、16 个 CASE、15 条双 SEALED，以及 6-5 的 bash SEALED／sh NOT-SEALED，汇总准确。另有 `case-e`，实际只跑 bash；统一打印的“解释器 bash sh”不能证明它跑过双解释器。

**收口意见：M4 代码整改可收口；本卡尚需完成上述一项 LOW 的注释补全。没有发现必须继续修改可执行代码才能封住的项。历史执行绑定应保留“未验证”，不应写成全部完整绑定。**

BLOCKER=0 HIGH=0 MEDIUM=0 LOW=1


