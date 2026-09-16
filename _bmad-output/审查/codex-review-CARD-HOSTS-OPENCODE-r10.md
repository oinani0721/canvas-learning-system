> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-10
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r10.md)"`
> 审查绑定: `d86f0bc4`（结论 BLOCKER=0 / **HIGH=1** / MEDIUM=1；⚠️ 那条 HIGH 是**车道 r9 的修复自己引入的**（失败清理会误删他人文件）。两条全采纳，整改在 `a9541247`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`d86f0bc46c508082ba4da6481e831080f10f83a3`**：本轮 **BLOCKER=0 HIGH=1 MEDIUM=1 LOW=0**。还不能签成只剩两个已登记窗口。

以下是静态复核结论及可复现调度；本轮没有实际制造文件系统竞态、运行部署或 pytest，没有写文件、连接数据库或运行模型。

1. **HIGH-1｜C2：失败清理可能删除别人刚放入的普通文件。**  
   位置：[scripts/deploy-vault.sh:1258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1258)，实际删除在 `:1263`。

   `made` 在 `:1202` 只保存名称。清理时检查“是软链、目标串相同”，无法识别**同名同串、不同 inode** 的替代软链，因此这种替代品会被误删。更严重的是，`readlink` 与 `unlink` 之间仍可换入普通文件，随后被删除；`dir_fd=sfd` 只固定父目录，没有固定叶子对象。

   **一句复现：**触发绑定后核失败，在清理的 `readlink` 成功返回后把该名字替换成普通文件，再恢复执行，`:1263` 会删除该文件。

   仅补一次 inode 比较也不能消除最后一次检查到 `unlink` 的窗口；同文件 `:1434–1436` 已准确描述过这种机制。

2. **MEDIUM-1｜C1：固定源 inode 没有保证它仍位于 vault 内。**  
   位置：[scripts/deploy-vault.sh:1185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1185)，后核在 `:1231–1244`。

   `src_fds[name]` 确实固定了**成功 `open` 时**的目录 inode，换成另一 inode 会被拒绝。但把原目录移到 vault 外不会改变这个身份；旧位置若改成指向原目录的新软链，后核仍然相等，最终 `ok=True`。

   **一句复现：**源 fd 打开后，将 `.claude/skills/a` rename 到同文件系统的 vault 外，再在原位置创建指向它的软链，后核会通过，而新绑定实际解析到 vault 外。

   这个窗口发生在源 fd 打开之后，不属于已登记的“打开 vault 前祖先替换”。

**C1/C3 的其余结论：**已有 fd 不会因 rename 或删除原名称自动转向替代品；目录成功删除后，其对象也会保留到引用关闭。因此 fd 固定身份的前提成立，但不能据此推导位置固定。[POSIX fstat](https://pubs.opengroup.org/onlinepubs/009696699/functions/fstat.html)、[rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)、[rmdir](https://pubs.opengroup.org/onlinepubs/009696799/functions/rmdir.html)

没有发现正常返回或 `die()`／`SystemExit` 路径上的 fd 泄漏：`:1190–1193`、`:1242–1243`、`:1266–1276` 的 `finally` 覆盖已打开资源。数量为 O(N)，源检查阶段约为 N+5 个目录 fd，另加标准流及继承 fd；11 条没有已知容量问题。大量条目可能触发 `EMFILE`，但会在建链循环之前失败并关闭已取得的 fd。

其余问题的复核结果如下：

| 问题 | 结论 |
|---|---|
| **0：OpenCode 发现与去重** | 官方 `v1.18.10` 会跟随条目软链扫描两个根。两个路径串分别读取、解析，随后按 frontmatter `name` 覆盖同一记录，最终只有一个技能，可能出现重复名称警告。应表述为“同一文件可能读取两次、最终登记一次”，不能说只读一次或按 inode 去重。[技能源码](https://raw.githubusercontent.com/anomalyco/opencode/v1.18.10/packages/opencode/src/skill/index.ts)、[Glob 实现](https://raw.githubusercontent.com/anomalyco/opencode/v1.18.10/packages/core/src/util/glob.ts) |
| **1：dry 零写** | 静态未发现本卡新增 dry 可达写点。`deploy-vault.sh:1506–1512` 提前返回；两个 heredoc 均在 apply 才调用的函数内部；`:213` 提前禁止 Python 字节码写入。未独立实跑全过程，不能背书“整个 tmp 根绝无瞬时创建”。 |
| **2：字面子串** | 非注释行中 `opencode.json` 命中 **0**。`:971、1477、1495` 拼出的完整名称只用于说明文案，当前没有配置写入。这个做法符合当前文案用途，但词法门本来就无法证明运行期没有拼接路径写入。 |
| **3：D-26(i)** | `cls_forbidden_paths.py:270` 确为该目录的唯一专属承重点；删掉后，普通非别名布局没有另一条 opencode 专属规则兜底。不过与其他保护目标重叠、经过 `.git` 或枚举失败时，仍可能被其他规则拦住。`:239–240` 对根直接返回 True，根退化旁路未复现。 |
| **4：AGENTS.md 文案** | `:1494–1498` 明确要求 vault 根的项目配置，并禁止修改用户级目录；运行时展示完整 `opencode.jsonc`，`remote`、`url` 和 `/mcp` 指引准确。[项目配置](https://opencode.ai/docs/config/#per-project)、[remote MCP](https://opencode.ai/docs/mcp-servers/#remote) |
| **5：live／worktree 落点** | 静态正常树下均从 `$VAULT/.agents/skills` 回跳两级至 `$VAULT`；`.git` 是目录还是文件不参与相对软链解析。并发源搬移的例外见 MEDIUM-1。 |
| **6：写面登记／发布** | 当前清单 `:611–612` 实际新增 **2 个 label**；`.agents` 中间段由逐段判据覆盖，叶子在 `:1005、1011–1013` 补判。`:1396` 已直接 `O_CREAT\|O_EXCL\|O_NOFOLLOW` 创建 `AGENTS.md`，不存在背景所述的 `.tmp → mv` 发布路径；已有文件一律拒绝覆盖。 |
| **7：既有三条门** | `test_deploy_vault_sh.py:176–198` 仍锁定不支持宿主的 rc64／E-1；`:883–887` 保留三种禁件；`:3727–3752` 仍用精确集合相等并约束 append 位置。属于登记实际新增对象，没有改成宽松比较。manifest 两项及四处登记常量相符。 |

`--hosts claude` 的新增 opencode 行为均有条件隔离；但头注／usage 已变化，因此“所有行为逐字相同”过强。本轮没有重跑作者所述的两版普通 dry 输出 diff。

新测试 `test_deploy_vault_sh.py:4599–4622` 只锁定源码片段，不能验证上述两种调度。只读语法与静态检查通过，不等于竞态验收通过；OpenCode 结论也限定于已查官方版本及有效 frontmatter。

**C4：上述 HIGH-1、MEDIUM-1 应在本卡内处理后复核。** 已登记的 `fstat→ftruncate` 和打开 vault 前祖先替换仍然存在，可沿既有移交边界处理，本轮不重复计为新增 finding；它们不能涵盖本轮发现的两个窗口。


