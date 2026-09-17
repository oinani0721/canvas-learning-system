> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r4.md)"`
> 审查绑定: `a09c2b96`（该轮 HEAD；结论 BLOCKER=0 / HIGH=2 / MEDIUM=2 / LOW=1，五条全部采纳，整改在 `6acec0e4`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`a09c2b969021004357a95ce9c98e0838a2aeae92`**。

**结论：BLOCKER=0 HIGH=2 MEDIUM=2 LOW=1。** 仍有独立于已登记祖先替换窗口的问题，不能判定 round-4 已闭合。

以下竞态均为静态可达性分析，未进行写盘复现。

## HIGH

### H1．失败清理仍可能删除换入的手写文件（K／M）

位置：[scripts/deploy-vault.sh:1214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1214)，实际删除在 `1216`。

`stat` 与 `unlink(base, dir_fd=dfd)` 是两个操作；目录 fd 固定父目录，不能固定随后删除的叶子。因此“没有任何一步按名字再找一次”在清理阶段不成立。

**复现思路：**让 `fsync` 失败进入清理，在身份检查返回本次 inode 后、`unlink` 前，把手写文件换入 `AGENTS.md`，清理就会删除它。

身份核不上时保留并报告是正确处置；身份相等只证明检查瞬间，不能保证随后删除的仍是本次文件。

### H2．`ln -s` 的目录语义可绕过已登记叶子（6／O）

位置：[scripts/deploy-vault.sh:1041](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1041)，前置存在性检查在 `1037`。

检查后若 `$link` 出现为目录或目录软链，`ln -s "$tgt" "$link"` 会把它当目标目录，实际创建 `$link/<name>`。这个实际写对象没有经过前面的叶子判据；后置失败也撤不回写入。

**复现思路：**在 `1037` 判不存在后，将该叶子建成指向保护目录的软链，`1041` 会在保护目录内新增 `<name>`。

这是**叶子参数被重新解释为目录**的问题，与已登记的 `$VAULT` 祖先替换窗口不同。

## MEDIUM

### M1．“存在即拒”的说明分支可能永久阻塞（K／L）

位置：[scripts/deploy-vault.sh:1128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1128)。

`1116` 检查普通文件后，`1128` 又按名字打开；`O_NOFOLLOW` 不阻止打开 FIFO。另有 `1133` 的无界 `readline()`，读取巨大无换行文件也可能耗尽内存。

**复现思路：**已有普通文件通过 `1116` 后，将它换成没有写端的 FIFO，发布器会卡在 `open`，无法返回 rc 73。

### M2．新静态门不能证明 flags 生效或没有额外文件（N）

位置：[backend/tests/unit/test_deploy_vault_sh.py:4401](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4401)，相关断言在 `4404`、`4407`。

当前起点和精确结束符各出现一次，**本版本没有截错**。但：

- 切片不包含 `PYPUB` 后面的函数尾部。
- 三个禁串只覆盖三种调用拼法。
- flags 在包含注释的 `body` 中查找，可由注释维持通过。

**复现思路：**仅在内存字符串中删除实际代码的 `O_EXCL`／`O_NOFOLLOW`，或在函数尾部加入额外写操作，再复算该静态门，两种变体仍通过。

上述内存负控已核实；没有修改文件，也没有执行变体。此结论针对这道静态门，不代表整套测试都会通过。

## LOW

### L1．生成文案仍承诺“重跑覆盖”（4／L）

位置：[scripts/deploy-vault.sh:1245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1245)。

正文仍说“重跑会被覆盖”“删第一行后才拒绝覆盖”，与本轮任何已有目标均拒绝的行为冲突。

**复现思路：**对照 `1245–1246` 的输出与 `1181` 开始的 `FileExistsError` 分支，即可看到矛盾。

## 其余问题的裁定

| 问题 | 结论 |
|---|---|
| **0．技能发现** | 按题给的“读取两处根、按 frontmatter `name` 去重”前提，两条路径可产生两次候选读取，但最终同名技能只有一项；即使 `.agents` 一侧忽略目录软链，普通 `.claude` 路径仍提供原件。文件树测试不能独立证明 OpenCode 扫描器跟随软链，本轮不把它当作运行验收。 |
| **1．dry 零写** | 静态控制流未发现本卡新增的 dry 写路径：发布 heredoc 位于函数内，调用被 apply 分支隔开。没有运行全过程文件监控；前后快照本身无法证明不存在“创建后删除”。 |
| **2．子串约束** | 实际扫描非注释行，字面 `opencode.json` 命中 **0**。运行期拼接仅用于输出指引，未发现对应配置写操作。当前用途合理，但这种词法门不能承担“禁止实际写配置”的完整证明。 |
| **3．D-26(i)** | `cls_forbidden_paths.py:270` 是普通布局下唯一明确登记该目录的代码；其他保护目标重叠或解析失败时，删行后仍可能拒绝。“唯一承重”应限定负控布局。`under():239` 明确处理 `/`，未见所问根退化旁路。 |
| **4．MCP 指引** | 明确要求在 vault 根创建项目配置，给出了运行期生成的完整文件名、`remote` 类型及 `/mcp` 端点，也明确禁止改用户级配置；接线文案未发现所问误导。另有 L1。 |
| **5．相对落点** | 从 `$VAULT/.agents/skills` 回跳两级，落到 `$VAULT/.claude/skills/<name>`；`.git` 是目录还是文件不参与该计算。 |
| **6／7．登记与旧门** | 静态登记对应当前对象：现为 **2 个新增 label**，删除 tmp 登记正确；条件 append 仍在扫描范围内，精确集合仍用 `==`，两个既有门保留其余拒绝项。manifest 两项及四处常量更新一致。属于按门登记；实际竞态写路径仍有 H2。 |

### L：不可重入取舍成立，但返回码和可达性说明过强

“存在即拒”可以成立，**已有目标分支并非不可达**：installer 成功返回前留下 `AGENTS.md`，或并发创建该文件，都能让步 3 遇到已有目标；新增预置文件测试本身就在覆盖前一种情形。

“第二次必然 rc 73／72”也不准确：默认环境文件目录下，重跑可能先被 [scripts/deploy-vault.sh:670](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:670) 的 `ACTIVE_VAULT` 碰撞检查拦成 **71**。原生 installer 的防覆盖实现不在指定读取面内，本轮未扩读验证。

### K：直写目标确实解决的部分

`O_EXCL` 保证创建瞬间不覆盖已有叶子，后续通过同一 fd 写入也不会转写换入的另一 inode。末尾的身份与链接数检查属于时点检查；它没有消除 H1 的按名清理窗口。

**验证范围：**已完成 Bash 语法、Python AST／内嵌程序编译、JSON 解析及上述内存负控；目标文件与绑定提交一致。未运行会创建临时文件的 pytest，未连接数据库，未运行 OpenCode／Codex 模型。


