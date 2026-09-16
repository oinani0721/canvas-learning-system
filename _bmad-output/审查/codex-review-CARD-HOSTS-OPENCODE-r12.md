> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-12
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r12.md)"`
> 审查绑定: `953b8e5e`（结论 BLOCKER=0 / **HIGH=0** / MEDIUM=1 / LOW=1；MEDIUM 的复现车道实测**成立**，整改在 `ff9e0156`——但**刻意只做到结果层面的收工核**，整类窗口按 POSIX 边界如实登记，见验收单）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`953b8e5e0a9f714cb8ac9b52527858f099adf5ef`**，本轮结论：**BLOCKER=0 HIGH=0 MEDIUM=1 LOW=1**。尚不能判为“只剩已登记窗口”。

全程只读，未运行部署、pytest、模型或数据库连接。`bash -n`、两段嵌入 Python 的语法解析通过；以下竞态复现均为静态推导，未实际注入。

**MEDIUM-1：目录 fd 仍只能证明身份，部分后核却将它作为当前位置证明。**

主要位置：[scripts/deploy-vault.sh:1139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1139)、`:1201`、`:1223–1231`。

目标侧 `sfd` 从建链到后核一直复用，没有重新确认它仍对应当前 `$VAULT/.agents/skills`。源父链整改不会发现目标目录被搬走。

**一句复现思路：**取得 `sfd` 后，将 `.agents/skills` 改名为同级 `skills-old` 并重建空 `skills`，继续执行时软链写入旧目录、相对目标仍正确且绑定函数可返回 0，但规定的 `.agents/skills` 为空。

同根因的 E1/E3 情形合并计入这一条：

- **E1：r11 那个具体调度已挡住，但整类搬移未闭合。** [脚本:1259](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1259) 打开 `_s2` 后、`:1263` 查询前，仍可搬走源父目录；此时 `_s2` 又成为旧目录 fd。
- **`vfd` 自身搬走是另一时间窗口。** 它发生在 `:1129` 成功打开之后；当前 `:1126–1127` 登记的只是打开之前的祖先替换。旧树可以完成绑定，随后按原路径打开的 publisher 却面对另一棵树。
- **publisher 也复用旧 `dfd`。** [脚本:1464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1464) 验的是旧目录里的叶子；`:1064` 的绝对路径后检只看文件类型，没有把当前路径与刚写入 inode 绑定起来。
- `src_fds[name]` 用于保存**期望身份**是正确用途，不属于应去掉的旧 fd。

**LOW-1：仍有一处随本轮实现变化而过时的注释。**

[scripts/deploy-vault.sh:1191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1191) 仍称 `csfd`“留到后核用”，实际后核已使用 `_s2`，旧 `csfd` 此后只被关闭。测试更名和“不删除、只报告”的说明本身已修正。

**一句复现思路：**列出 `PYBIND` 内全部 `csfd` 引用，对照 `:1263` 的 `dir_fd=_s2` 即可确认。

**E2：每条重开父链没有引入新的身份接受漏洞，但也不提供整批一致性。** 两个临时 fd 每条都会关闭，并非同时多持有 `2N` 个；各条仍与自己的固定源 inode 比较。不同条目可能看到不同时间的目录状态，已通过的条目之后也能变化，因此不能声称 N 条在同一瞬间全部成立。

原问题的其余核对结果如下：

| 问题 | 独立结论 |
|---|---|
| 0．OpenCode 发现与去重 | 按本次查到的官方源码，扫描启用软链跟随，两条路径**可能各读、解析一次**；随后按 frontmatter `name` 存入同一映射，最终只有一项，可能产生重复名称告警。条目软链不会被代码主动排除。[技能源码](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/skill/index.ts)、[glob 实现](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/util/glob.ts)。这是源码静态结论，未绑定本机 OpenCode 版本，也未越界检查全部技能 frontmatter。 |
| 1．dry 零写 | 许可范围内未发现新增写入口：hosts 解析无 here-string，新增 heredoc 只在 apply 调用的函数中执行，已禁 Python 字节码缓存。前后快照不能证明短暂创建后删除或同内容重写；本轮未重跑作者的 dry 实验。 |
| 2．字面子串 | 实际扫描非注释行，`opencode.json` 命中为零。`:1516` 的运行期拼接只进入说明正文，没有流入配置写操作。此次用法无越界写入；**词法门自身无法证明运行期不生成配置文件**。 |
| 3．D-26(i) | `cls_forbidden_paths.py:270` 是唯一专属注册。普通、无保护目标重叠的树中删它便失去该目录保护；若目录解析到其他保护根，通用规则仍可能拒绝。`:239–240` 对保护根 `/` 明确返回真，未发现所问根退化旁路。 |
| 4．AGENTS 文案 | 明确要求 vault 根目录、完整 `/mcp`、`remote` 类型，并明确禁止修改用户级目录；生成后显示完整 `opencode.jsonc`，没有绕述不清的问题。[官方配置说明](https://opencode.ai/docs/config/)、[MCP 说明](https://opencode.ai/docs/mcp-servers/#remote)。 |
| 5．相对软链落点 | 静止文件树下，两次 `..` 从 `.agents/skills` 回到 vault，随后进入 `.claude/skills/<n>`；`.git` 是文件还是目录不参与这个解析，落点一致。 |
| 6．写入登记与发布 | 根、AGENTS、动态叶子及构建中间段都有对应判据；未发现静态漏登记对象。但登记不消除 MEDIUM-1 的位置竞态。最终实现已经没有 `AGENTS.md.tmp → mv`，而是独占创建目标本身。 |
| 7．三条门 | rc 64 门仍覆盖 `codex`、`dsh`、`claude,codex`；字面门仍保留三个禁串；写面门仍为精确集合相等。最终新增的是 **2 个 label，不是 3 个**，属于按实际写面登记。 |
| claude 单宿主 | 不进入 OpenCode append、生成及状态追加分支；未发现该路径新增行为。本轮未执行 PREV/HEAD dry 输出 diff，不替作者背书“实测逐字相同”。 |

**E4：验收单应完整列明以下限制，其中第 2 项尚不能算已登记闭合：**

1. preflight 判据完成至打开 vault 之前，祖先路径可能被替换。
2. 打开之后，vault 本身、源父链、目标父链及 publisher 父目录仍可能被搬移；若以“部署期间禁止并发目录迁移”为前提，必须明确并落实这一前提。
3. 逐条后核不是整批原子快照，也不约束检查完成后的变化。
4. 绑定失败可留下已建目录和软链，只报告、不自动删除。
5. AGENTS 直接创建，写入非原子可见；失败可能留下半成品，半成品标记本身也可能失败。
6. **任何**已有 AGENTS 都拒绝覆盖，包括带生成标记的旧产物；重跑不能视作自动修复。
7. Phase B 不构成跨文件事务，失败可能留下部分更新；完整部署重跑也可能先被安装防覆盖检查拒绝。
8. 本轮未验证宿主实际加载、live/worktree 实跑或全过程写入事件；静态门与快照不能替代这些证据。


