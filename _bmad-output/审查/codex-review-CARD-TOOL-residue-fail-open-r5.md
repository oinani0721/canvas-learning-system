> 批次: BATCH-2026-09-11-第十四批 · 车道 T8 · 卡 CARD-TOOL-residue-fail-open round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-residue-fail-open-r5.md)"`
> 审查绑定: `158e5a60..b09e85e3`（本轮送审时 HEAD = `b09e85e3`，与该轮存档正文自述的绑定一致）
> 会话头自证（抄 .stderr 的 codex 版本行 / model 行 / reasoning 行，带行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

**本卡可以收口。round-4 的 LOW 已整改，未发现新增的必改项，也未发现需要继续修改可执行代码才能封住的路径。**

复核绑定 `b09e85e32f863bd2ee288320342f61d3fa102367`；当前 `lefthook.yml` 与该提交逐字节一致。全程只读，未运行 hook、对照脚本或测试，未修改、暂存文件。

**1. r4→r5 确实只有注释改动，没有任何可执行语句被修改。**

指定 diff 只有一个 hunk：`@@ -408,11 +408,14 @@`，共删除四行、增加七行。所有变更行均为四格缩进后的 YAML 注释，位于 [mutant-residue-scan 命令键之前](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:409)。

作者的“非 `#` 开头增删行数为零”**不能单独作为通用判据**：YAML 块标量、shell 多行引号、heredoc 中的 `#` 可能是数据；续行及缩进语境也必须核对。行内注释则应连同整条语句判断。

本次另核实了：

- 变更位于 YAML 注释区，没有改变 `run: |`、缩进结构或命令边界。
- r4、r5 抽出的完整 **173 行执行块逐字节相同**，SHA-256 均为：
  `b1bfdf1f600ac90ab569c42d29a6c901cd18fcbe71b62f6b509c734e6940f523`
- 相对 B14_BASE，整个 residue 注释及命令块之外的文件字节相同。指定邻居仅做字节比较，未扩展审查。

**2. rc 清单已完整回应 round-4，没有发现仍需补列的独立 shell 调用。**

[已核清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:410)逐项对应如下：

| 项目 | 当前 `lefthook.yml` 行号与守卫 |
|---|---|
| `mktemp` | 434–435，赋值后的 `||` |
| 两处 `git` | 438–440、534–537，`if !` |
| `tail`、`od`、`wc` | 456、459、480，均为 `if !` |
| 哨兵 `printf` | 475–476，`||` |
| NUL 计数 `tr` | 477–478，`if !` |
| NUL 归一化 `tr` | 550–551，`if !` |
| `awk` | 563–571，`||` 设置 `FAILED=1` |
| hits 初始化 `:` | 514–515，`||` |

[未单独核清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:412)也与实际对应：

| 项目 | 当前行号 |
|---|---|
| 两次 `tr` 命令替换 | 464、483 |
| probe 载荷、期望值的两个 `printf` | 501、504；没有重复计数 |
| trap 注册与其 `rm` | 436 |
| 命中分支的 `cat` | 590 |
| 全部 `echo` | 包括决定正常完成状态的604行 |
| 两个 `while` 及两处 `read` | 503、518–572 |
| 全部 `[` | 使用真假结果，没有独立区分测试错误 |

两处 `read` 的状态确实被循环条件使用；“没单独核”指没有区分 EOF／读错误。具体兜底须分清：**probe 由504行的结果比较检查，主循环由573、578行的哨兵和计数检查。**

`set -u`、纯赋值、算术展开、`continue` 的固定操作分类合理。`exit 1` 是显式终止结果；`if/case` 是控制语法；568行的 `printf` 属于 awk 内部操作，已经归入 awk 进程检查，不是遗漏的第三个 shell `printf`。

**3. 三处证据补强均回应了 r4；证明范围仍需保留。**

**8-2／M2：注入后摘要缺口已补齐。** [_lib.sh:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/_lib.sh:125)先覆写脚本，131–132行再记录摘要。按提取规则及注入原文在内存重建，四项全部匹配：

| 执行对象 | 重算 SHA-256 |
|---|---|
| 8-2 old | `16b6abd5645f489f1edeae30fad47b9cd3e2bab1eb520e4fccf4d6f66af0b82d` |
| M2 old | `fe78acd4390ffcfdd4878f152e788d1f6a1061f0983e240749c6f066157f71fd` |
| 两者 new | `9c6cec629231ccd62747dfcc54727f21178fcfddc7c55ded4b1182373bb96845` |

**case-e：单 bash 的限制已如实声明。** [脚本12–14行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/case-e-allowlist.sh:12)和日志均明确取消统一“双解释器”抬头对此案例的适用性。普通 `case` 模式的匹配规则有规范依据，但不能把“模式语义相同”扩写为“所有解释器运行整个块都相同”。[POSIX shell 模式匹配规则](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)

**三控：配置内容、探针字节和结果绑定成立。** [日志4行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r5-hook-controls-20260914T212241.txt:4)的配置摘要：

`35ec222712dfefe3a8d00cf55ec697fc3d469a7ac71545c031d7a7197d9b34f7`

与当前文件及最终提交对象相同。因此，日志中的提交前 HEAD `158e5a60` 不妨碍绑定 r5 内容。两种探针按脚本重建、重算 blob OID，并读取实际 Git blob，全部一致。三控明确呈现本块 `OK／BLOCKED／BLOCKED`，总 rc 为 `0／1／1`；负控 B 不是仅靠 ruff 失败获得阻断。

**NUL 转换保留了这些结论，但归档不是无损原始流。**

[run-hook-controls.sh:41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/run-hook-controls.sh:41)转换的是 **lefthook 合并 stdout／stderr 中所有 `0x00` 字节**，不限于 ruff 行；转换为 `0x3F`，其余字节在该转换中不变。因此不会删掉 ASCII 标记、BLOCKED 诊断或退出状态。

但原生 `?` 与原来的 NUL 此后无法区分。日志131行的 `?` 已由扫描块自身归一化产生；139、142、149行与“ruff 原来回显三个 NUL”的解释相容，**现存材料不能独立证明历史原始流恰有三个 NUL**。探针输入确含 NUL，则由 blob 字节独立证明。

以下仍为**未验证**，不构成本卡必改项：

- 配置、HEAD、工具身份只在批次开头采样一次，并非逐控重新采样；差异记录也是 `--stat`。要证明每控期间对象不变，需要逐控快照或执行期间绑定。
- 输出过滤器的 `PIPESTATUS[1]` 未记录，也没有原始流或替换位置记录。要证明无损完整性，需要保留原始字节及可核对的转换记录。
- 存档执行的是 `lefthook run pre-commit`；实际 `git commit` 入口是否调用该 hook，需要入口检查或获准后的实际提交验收。
- 故障对照的 [_lib.sh:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/_lib.sh:72)只归档前25行，不能与三控一样称为完整输出。

CASE 汇总核对准确：**16个故障 CASE，15个双 SEALED；6-5 为 bash SEALED／sh NOT-SEALED**。后者表示旧 sh 已经阻断，不表示新版 sh 放行。

**4. 剩余放行边界，按所需前提排序。**

| 所需前提 | 能只读论证的结果 | 分类 |
|---|---|---|
| 无标记、标记只在旧行或允许名单内 | 可以放行 | 已声明扫描范围，非新缺口 |
| 未守卫的数字提取 `tr` 输出可接受值后非零退出 | 可以继续执行；**单凭这一点不能推出标记漏扫** | 本块已披露的 rc 覆盖边界，464、483行 |
| 枚举、逐文件读取之间索引变化，或扫描后再次暂存 | 最终内容可能未被完整扫描 | 扫描时点限制，438、534行及330–339行注释 |
| 检查后替换 `dn`，或最终判断前清空／替换 `hits` | 当前路径检查不能保证随后读取的内容不变 | 临时对象并发替换边界，553–599行 |
| 控制 Git／awk 等执行工具，令其伪造结果并返回0 | 可以欺骗依赖这些工具的判断 | 工具可信边界 |

**不能把“临时对象被预置”笼统归为任何检查都无能为力。** 有限预置故障仍可封堵，r4 的 `d -ef dn` 就是实例；任意持续替换、任意工具伪造才超出当前块所建立的保证。

在工具按约定工作、索引固定、临时对象独立且稳定的前提下，本轮没有再静态论证出扫描范围内新增行的漏检路径。

**5. 收口判定：可以。** 无“改了才算封住”的剩余项；上述未验证内容限制证据声明的范围，不应转成继续修改本块的前置要求。本轮无分级发现。

BLOCKER=0 HIGH=0 MEDIUM=0 LOW=0


