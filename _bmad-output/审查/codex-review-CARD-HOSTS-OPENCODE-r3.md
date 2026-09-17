> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r3.md)"`
> 审查绑定: `4ad30472`（该轮 HEAD；结论 BLOCKER=0 / HIGH=3 / MEDIUM=1 / LOW=0，四条全部采纳，整改在 `a09c2b96`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

## 结论

**本轮 BLOCKER=0 HIGH=3 MEDIUM=1 LOW=0。round-3 的发布整改尚未闭合。**

绑定 HEAD：`4ad30472369c5cd8b0b466f809c87166c4e56e0b`。核对了 PREV 总差异及 `c228b745 → 4ad30472` 整改差异；以下竞态结论来自静态调用顺序分析，未实际执行文件替换、部署或 pytest。

## HIGH

### H1：EEXIST 分支仍可能删除刚出现的手写文件

位置：[deploy-vault.sh:1216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1216)

第二次 `refuse_reason()` 与随后的 `unlink(base)` 没有绑定同一文件身份。`link` 返回 EEXIST，只证明**此刻存在目标**，不能证明它是刚检查过的生成件；检查时目标甚至可以不存在。

**复现思路：**在第二次检查通过后放入无标记的手写 `AGENTS.md`，首次 `link` 返回 EEXIST，随后无条件 `unlink` 删除手写件，第二次 `link` 发布成功。

因此，“不覆盖任何已存在的东西由内核保证”不成立：`link` 的保证被前面的删除操作绕开了。

### H2：tmp 身份检查没有绑定实际发布源

位置：[deploy-vault.sh:1209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1209)、同文件 `:1190–1197`、`:1217`

检查比较了 `tfd` 与当时 `tmpbase` 的 inode，但实际发布仍调用 `os.link(tmpbase, …)`，重新按名称寻找源文件。目录 fd 固定了父目录，未固定这个名称对应的文件。

**复现思路：**在 tmp 身份检查通过后，把 `AGENTS.md.tmp` 换成零字节普通文件，随后按名称发布该文件；`:1083` 只检查普通文件在位，可以继续通过。

空正文守卫检查的是读入的 `body`，无法阻止此后换入的空文件被发布。

### H3：父目录 fd 可以固定到已经被重定向的目录

位置：[deploy-vault.sh:1163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1163)

步 1 的物理路径判定与这里的目录打开之间没有身份绑定。fd 能防止**打开之后**的路径替换改变操作目标，不能保证打开时选中的就是检查过的目录。

**复现思路：**通过路径检查后、打开目录前，将 `$VAULT` 移走并换成指向已有禁写目录的软链，发布器便会在那个目录创建 tmp 和 AGENTS；后置失败也撤销不了已经发生的外部写入。

同类窗口也存在于 `.agents` 祖先检查之后的 `mkdir -p`／`ln -s`（`:1021`、`:1039`）。加 `O_NOFOLLOW` 能挡住 `$VAULT` 末段软链，**仍不能单独解决祖先替换**。

## MEDIUM

### M1：tmp 清理失败被静默吞掉

位置：[deploy-vault.sh:1228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1228)

成功发布后，删除 tmp 的所有 `OSError` 都被忽略；此时 `published=True`，发布函数仍返回成功，后置检查也不检查 tmp 残留。

**复现思路：**在 `link` 成功后使 tmp 删除返回 EACCES／EPERM，发布器仍成功返回并留下链接数为 2 的 AGENTS 与 tmp，恢复权限后重试会被 `O_EXCL` 或前置链接数判据拒绝。

所以 `finally` 目前只能保证“尝试清理”，不能保证“总是清掉”；清理失败至少需要明确报告。

## 问题 0–7 的核对结果

| 问题 | 结论 |
|---|---|
| **0：发现与去重** | 按题设的 frontmatter `name` 去重语义，两个入口指向同一 SKILL.md，最终只保留一份同名技能。**可能扫描读取两次**；静态文件树不能证明扫描器是否跳过软链。即使 `.agents` 一侧跳过，真实 `.claude/skills` 根仍提供入口。 |
| **1：dry 零写** | 本卡新增控制流未发现 dry 写点：`:1279` 提前返回，发布 heredoc 只在 apply 调用函数时执行。TMPDIR 已在 before 快照之前建立并强制传入。快照仍不能证明创建后删除、同内容重写等全过程行为；既有 harness imports／省略 harness 时的 Docker 调用也不在本次可独立核验实现范围内。 |
| **2：子串约束** | 实际扫描结果：非注释行字面 `opencode.json` **零命中**。拼接后的变量只用于输出说明文案，没有作为配置文件写入路径使用。当前不是隐藏写面；这种拆字仅能兼容词法门，不能成为“不写配置”的证明。 |
| **3：D-26(i)** | `cls_forbidden_paths.py:270` 是该目录唯一的**专门登记点**。普通、无保护路径重叠的输入删掉它后，没有其他专门规则兜底；特殊输入仍可能被 `.git`、其他保护目标或枚举失败规则拒绝。`:239` 已处理根 `/`，本轮纯函数检查确认没有 `//` 前缀退化旁路。 |
| **4：AGENTS 文案** | `:1265–1271` 输出完整 `/mcp` 端点，明确在 vault 根创建 `opencode.jsonc`，并明确不要改用户级配置。运行期输出的文件名完整，源码拼接没有让实际文案含糊。未运行 OpenCode 验证接线。 |
| **5：相对软链** | `:1026` 的基目录是 `$VAULT/.agents/skills`，回跳两级到 `$VAULT`；`.git` 是文件还是目录不参与这条解析，静态落点一致。 |
| **6：写入面登记** | 静态名称层面完整：三个条件 label、叶子 `LINK_WRITES`、中间目录逐段判据均在；manifest 两项及对应常量吻合。**登记完整不等于实际写入对象身份已绑定**，H1–H3 正是剩余缺口。 |
| **7：三道门更新** | 属于按原意登记：测试 `:197` 仍严格要求 rc 64，`:883–887` 保留三项禁件，`:3712` 仍为精确集合相等，三个新 label 在扫描切片内。没有改成宽松包含关系；但这些门不验证发布竞态。 |

`--hosts claude` 的正常 dry 消息在差异中保持原样，新消息均受 `HOST_OPENCODE` 条件控制；未复跑作者的两版输出 diff，且 `--help` 头注确实变化，不能泛称所有输出逐字相同。

## round-3：F–J

- **F：确实存在“两者皆无”的失败路径。**删除旧 AGENTS 后，第二次 `link` 抛错，再由 `finally` 成功删除 tmp，即两者都不存在。正常成功的 `link → unlink tmp` 不会截断 AGENTS，因为两个名称指向同一 inode。SIGKILL 则不执行 `finally`，可能留下 tmp。另有两种不完整正文来源：H2 的源文件替换；正文生产者输出部分内容后失败，发布器仍可能接受非空前缀并发布。
- **G：不加 O_NOFOLLOW 的现有理由不成立，见 H3。**另作事实更正：本机只读检查显示 `os.replace` 签名接受 `src_dir_fd`／`dst_dir_fd`；仅凭它不在 `os.supports_dir_fd` 集合中，不能推出“不支持目录 fd”。
- **H：管道非零传播成立，但不提供回滚。**`pipefail → prc → return 1 → rc 73` 可以传递失败；生产者 stderr 未被右侧的 `2>&1` 捕获进 `perr`，仍会输出到外层 stderr。源码捕获的新守卫有效。真正被静默吞掉的是 M1 的清理异常；管道最终失败也不能撤回已发布的部分正文。
- **I：ino／nlink 没有正常重跑假红问题。**比较发生在同一次 dry 测试前后，不跨测试比较 inode。普通读取不会改变两者；替换 inode 或增加链接本来就应被发现。不能因此把快照升级为全过程零写证明。
- **J：仍有 H1–H3 与 M1 所列未覆盖路径，不能给出 HIGH=0。**

你对两次负控措辞的更正均正确：**rc 73 不证明外部零污染；在守卫之后注入空源码，只证明下游门敏感，不证明守卫承重。**

本轮完成 Bash 语法检查、嵌入 Python 编译检查、字面扫描及 `under()` 纯函数边界检查；未改文件、未连接数据库、未运行模型。


