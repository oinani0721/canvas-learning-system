> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-5（**轮次上限**）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r5.md)"`
> 审查绑定: `6acec0e4`（**最终 HEAD**，代码自此未再改动 —— 5 轮用满后改代码会让最终 HEAD 失去绑定）
> 结论: BLOCKER=0 / **HIGH=2** / MEDIUM=1 / LOW=1 ⇒ 按 D-15「第 5 轮仍有 HIGH → 停下交主 session 人审」，车道不自判通过。
> 车道独立核验见 `evidence-hosts-opencode/selfcheck-r5-findings-20260916T125808.txt`（HIGH-1 / MEDIUM-1 实证 CONFIRMED；LOW-1 两成立一不成立；HIGH-2 严重度存疑，理由已写、裁定权交主 session）。
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

## 结论

**本轮 BLOCKER=0 HIGH=2 MEDIUM=1 LOW=1。** 不能认定“只剩已登记的 `$VAULT` 祖先替换窗口”。

绑定 HEAD：`6acec0e432504c8b8feff1451a47916d897d9c8c`；复核结束时仍一致，限定文件无未提交修改。

### HIGH-1：技能名在过检后被改写，能生成禁写的 `.git` 条目

位置：[scripts/deploy-vault.sh:1079](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1079)，实际创建在 `:1134`。

`LINK_WRITES` 登记原始名称，Python 却通过 `splitlines()+strip()` 重新解释名称。例如，` .git` 带前导空格，原名通过判据，实际创建的名称变成 `.git`，触犯 `cls_forbidden_paths.py:518` 的禁写规则。后续解析失败发生在创建之后，残链已经留下。

**一句复现：** installer 留下 `$VAULT/.claude/skills/ .git`，绑定过程会先创建未过检的 `$VAULT/.agents/skills/.git`，随后才因目标不存在报错。

已做只读纯函数核验：名称转换得到 `.git`；同一判据对 ` .git` 放行、对 `.git` 拒绝。无需竞态。

### HIGH-2：失败清理的链接数检查仍有 TOCTOU

位置：[scripts/deploy-vault.sh:1344](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1344)。

`fstat(nlink == 1)` 与 `ftruncate`、写标记是分开的操作。检查之后新增硬链接，后续操作仍会修改共享 inode；固定 fd 不会固定链接数。影响范围是**本次新建 inode 及其新增硬链接**。

**一句复现：** 令正文写后的 `fsync` 失败，并在清理的 `fstat` 返回 1 后、`ftruncate` 前建立第二个硬链接，第二个名字下的内容也会被截断并写成残件标记。

这是系统调用顺序推演，未在真实文件系统实施竞态。

### MEDIUM-1：整改后的静态门仍未绑定真实安全措施

位置：[backend/tests/unit/test_deploy_vault_sh.py:4420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4420)，以及 `:1309`。

“去注释”只过滤整行注释，行尾注释仍参与 flags 检查；截断计数和旧三处链接数计数，也没有锁住新增清理分支的链接数检查。

**一句复现：** 在内存源码中删除真实 `O_EXCL`、改在行尾注释留下该词，发布静态门仍 PASS；删除新增的 `:1344–1345` 链接数检查，写入门和发布门也仍 PASS。

这些负控已实际执行，但没有修改文件；结论限于上述静态门，不代表全部功能测试也会通过。

### LOW-1：接受的裁定更正仍有注释未落实

位置：[scripts/deploy-vault.sh:1304](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1304)，以及测试文件 `:4388`。

仍写着“重跑先被步 2 拦成 rc 72、已有目标分支不可达”。测试文件 `:3712` 也仍写新增三项、包含 `.tmp`，当前实际新增只有两项。

**一句复现：** 对照测试 `:4393–4397` 的 installer 预置文件案例，已有目标分支明确可达，预期返回 rc 73。

## 对其余问题的裁定

| 问题 | 结论 |
|---|---|
| **0：发现与去重** | 稳定文件树下成立。两个路径可能各扫描、解析一次，并产生重复名称警告；最终按 frontmatter `name` 保存一个技能条目，不能表述成“只读取一次”。当前官方源码启用软链跟随，随后按名称写入映射。[技能发现源码](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/skill/index.ts)、[glob 实现](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/util/glob.ts)。这不是对本机安装版本的运行验收。 |
| **1：dry 零写** | 本卡新增路径未发现 dry 写入：两个 heredoc 都在函数内，`:1406` 的 dry 返回早于调用；字节码缓存已禁用。未发现新增的判据前写入。前后快照不能证明没有建后删临时文件，测试已明确承认该限制。 |
| **2、4：子串与文案** | 非注释行中 `opencode.json` 命中为零。运行期拼出的 `opencode.jsonc` 只进入说明文字，未成为写入对象；项目根、`remote`、完整 `/mcp` 地址及勿改用户级配置的指引清楚。配置名称和类型符合[官方配置文档](https://opencode.ai/docs/config/)及[MCP 文档](https://opencode.ai/docs/mcp-servers/)。这种拼接可解释为避开文案误报，词法门本身不能证明运行期零写。 |
| **3：D-26(i)** | `:270` 是该目录唯一专属登记。普通、无重叠保护面时，删除它会使两个点名文件失去保护；若路径另含 `.git`、落入其他保护目标或枚举失败，仍可能被其他规则拒绝。`under()` 对 `/` 的特判及 `main()` 的根路径补查未见退化旁路。 |
| **5：live / worktree** | 两级回跳从 `.agents/skills` 起算，`.git` 是文件还是目录不参与软链解析，落点一致。 |
| **6、7：登记及既有门** | 当前新增 **两个** label，条件 append 仍在精确集合门覆盖范围内；属于按门立意登记。manifest 两项及四处常量一致。`codex`、`dsh`、`claude,codex` 的 rc 64 断言仍在，三类禁件检查仍在。叶子登记被 HIGH-1 的名称变化破坏。当前已无 `AGENTS.md.tmp → mv` 路径。 |

## P—T 补充

- **P：** `mkdir → stat → open(O_DIRECTORY|O_NOFOLLOW)` 合并两种存在状态，对类型约束是正确的；换成软链、普通文件或 FIFO 会被最终打开操作拒绝。**fd 固定 inode，不保证该目录一直留在原位置。** 例如取得 `.agents` 的 fd 后将该目录搬走，后续 `mkdir("skills", dir_fd=afd)` 仍写进被搬走的目录。既有 [cls_forbidden_paths.py:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/cls_forbidden_paths.py:131) 已登记目录改名类残余，本轮不重复计新增 HIGH，但不能将它缩述为仅 `$VAULT` 祖先的一个窗口。
- **Q：** `(dev, ino)` 相等证明两次采样指向同一个目录，单独不能证明目录位于 vault 内；两侧共同指向外部也会相等。静态树下，外层 `:1055–1058` 的物理路径核验会补抓这一情况。
- **R：** 完整残件前缀会被认出；前缀只写了一部分或文件为空，会归为“疑手写”，但仍然**存在即拒绝**，没有覆盖旁路。整脚本重跑可能更早被 rc 71/72 拦住。
- **S：** 两处 `write_all` 位置正确，能处理短写。相对可信目录 fd 的 `O_EXCL` 创建保留目录身份、拒绝已有叶子；“比 `open_pinned` 更强”只能在这些具体性质上成立，不能替代其即时路径复查，也不能消除 HIGH-2。
- **T：** 至少 HIGH-1、HIGH-2 仍未闭合，故不满足“仅剩已登记祖先窗口”的结论。

**验证范围：** 全程只读；通过 Bash 语法检查、两个嵌入 Python 块的 AST 检查，以及提取执行的 9 条静态门。未运行部署、pytest、数据库连接或宿主模型；未重做作者 PREV/HEAD 两版 dry 输出比较。


