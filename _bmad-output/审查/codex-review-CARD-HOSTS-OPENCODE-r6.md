> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r6.md)"`
> 审查绑定: `d9f68261`（结论 **BLOCKER=0 / HIGH=0** / MEDIUM=4 / LOW=2；原 HIGH-2 经 Codex 主动降级为 LOW —— 车道的驳回理由被接受。六条全部采纳，整改在 `5af9c7ff`）
> 本轮**未绑最终 HEAD**（审后又改了代码）⇒ 按规则再送 r7。
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定 **`d9f68261c58b75db9fe09d2560cb5edec8366a63`**：**本轮 BLOCKER=0 HIGH=0；MEDIUM=4 LOW=2**，其中一项 LOW 是原 HIGH-2 的重新定级。目前还不能说“只剩两个已登记窗口”。

审查使用提交内 blob；读取期间出现的未提交测试修改未计入结论。全程未改文件、未连接数据库、未运行模型。以下负控均在内存中进行，没有执行会创建文件的部署或 pytest。

1. **MEDIUM — 技能名中的冒号使判据检查另一条路径。**  
   [deploy-vault.sh:993](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:993) 把原名嵌入 label，而 `scripts/cls_forbidden_paths.py:573` 按第一个 `:` 拆分。名字 `a:~` 会让真实目标 `/vault/.agents/skills/a:~` 被检查成 `~:/vault/.agents/skills/a:~`，随后被字面 `~` 规则误拒。因此 **U 所问的判据与实际路径一致性尚未整类闭合**；未证明能借此写穿保护面。  
   **复现：**用 `a:~` 构造现有 `LINK_WRITES`，观察 `partition(":")` 得到以 `~` 开头的错误路径。  
   建议 label 使用固定值或序号，原名只进入 path。

2. **MEDIUM — `basename` 的命令替换仍会吃掉技能名末尾 LF。**  
   [deploy-vault.sh:991](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:991) 的 `$(basename "$d")` 将 `alpha\n` 变为 `alpha`。这发生在判据之前，属于双方共同使用错误名称：没有 `alpha` 时会留下悬链后失败；同时存在 `alpha` 时会合并绑定、遗漏原条目。无写 Bash 实验已确认字节丢失，落盘后果由控制流推导。  
   **复现：**给取名表达式输入 `$'/vault/.claude/skills/alpha\n/'`，捕获结果为 `b'alpha\0'`。  
   应保真取名或在写入前明确拒绝不支持的名字；同时处理 `:1059` 的 `$(pwd -P)` 同类尾换行问题。

3. **MEDIUM — 注释仍能替已经删除的安全措施满足静态门。**  
   [test_deploy_vault_sh.py:4418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4418) 的 `splitlines()` 与 tokenizer 的行坐标不一致：真实 U+2028 会造成挖错位置、遗留注释；此外，`:4467–4468` 又把未剥行尾注释的 shell 尾部并入必要 flag 判据。  
   **复现：**内存删除 `deploy-vault.sh:1312` 的 `O_EXCL` 后原测试变红，但在该行追加 `# <真实 U+2028>O_EXCL`，或在 `:1386` shell 调用末尾追加 `# O_EXCL`，原测试均恢复绿色。  
   应保持与 tokenizer 一致的行界，并让 Python 必要条件仅由对应 Python 代码满足。

4. **MEDIUM — 新增清理前链接数断言不承重。**  
   [test_deploy_vault_sh.py:4479](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4479) 搜索整个发布程序中的 `st_nlink != 1`，所以写后检查 `deploy-vault.sh:1339、1342` 足以替清理检查满足它。  
   **复现：**内存删除 `deploy-vault.sh:1360–1361` 的清理 guard，直接执行原静态测试仍为 GREEN。  
   应限定失败清理分支，并核对检查与 `ftruncate` 的先后关系。

5. **LOW — 原 HIGH-2 降级，窗口仍存在。**  
   [deploy-vault.sh:1360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1360) 到 `:1362` 的检查与截断不是原子操作，但 fd 确实来自本次 `O_EXCL` 新建文件；受影响的共享关系必须随后建立，不能直接等同于截断他人原有文件。**同意车道的影响面区分，本轮不维持 HIGH，也不要求为此另加路径清理。**  
   **复现思路：**触发发布失败，并在清理 `fstat` 后、`ftruncate` 前给新建 inode 增加硬链接。

6. **LOW — 两处注释尚未同步。**  
   `scripts/deploy-vault.sh:1072` 仍称“stdin 每行一个”，实际已改 NUL；[test_deploy_vault_sh.py:4390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4390) 仍称已有产物分支“走不到、先 rc72”，而该测试自己就在验证到达步 3 后返回 rc73。  
   **复现：**分别对照 `:1023/:1090` 的 NUL 传递，以及该测试 `:4396–4399` 的预置与断言。

其余问题的裁定：

| 问题 | 结论 |
|---|---|
| **0：OpenCode 发现与去重** | 按已核的 **v1.18.25** 实现，扫描跟随软链，两条路径可能分别读取同一个文件并产生重复名称警告，最终按 frontmatter `name` 留一个技能；不能表述成“文件只读一次”。[官方源码](https://raw.githubusercontent.com/anomalyco/opencode/v1.18.25/packages/opencode/src/skill/index.ts) |
| **1：dry 零写** | 所读控制流中未发现新增 dry 写入路径：生成函数在 apply 分支内，heredoc 不在顶层执行，TMPDIR 已进入前置判据。**本轮未执行完整 dry，也未重做作者与 PREV 的 stdout diff**；不能把静态结论写成端到端实测。 |
| **2、4：文件名字串与文案** | 非整行注释的源码中，字面 `opencode.json` 命中 **0**。拼接结果只被打印进指引，生成文案明确给出 vault 根目录的 `opencode.jsonc`、remote MCP 和完整 `/mcp` 地址，并明确禁止修改用户级目录。拼接作为兼容既有文本门的做法可接受，但该门本身不能证明“没有配置写入”。 |
| **3：D-26(i)** | `build_targets:270` 是该目录唯一的**专项整根登记**。删掉后普通配置文件没有专项兜底；但 `.git` 段、与其他保护根重叠、枚举失败等仍可能拒绝，不能说所有后代都会放行。`under():239–240` 和 `main():589–590` 覆盖根路径退化，未发现该旁路。 |
| **5：live / worktree** | 相对软链从 `.agents/skills` 回退两级，落到同一 vault 的 `.claude/skills`；`.git` 是目录还是文件不参与解析。 |
| **6、7：写面与既有门** | 当前实际新增登记是 **2 个 label**，不是背景中的 3 个；`AGENTS.md.tmp → mv` 已不存在。中间 `.agents` 目录由分段判据覆盖，叶子仍调用同一判据，但存在上述冒号协议问题。manifest 两项及常量更新与实际对象一致；精确集合门仍是 `==`，属于登记，没有改成宽松包含判断。E-1 与剩余禁件断言也保留。 |

对 **U–X** 再明确几项：

- **U/V：**NUL + `fsdecode` 修复本身成立；固定格式 `printf '%s\0'` 不会解释名字里的 `%`。本机为 `utf-8 / surrogateescape`，非法 UTF-8 样本满足 `fsencode(fsdecode(bytes)) == bytes`，传给文件系统 API 时可恢复原字节；底层文件系统是否接受该名字是另一层，本轮未创建文件验证。[Python 官方说明](https://docs.python.org/3/library/os.html#file-names-command-line-arguments-and-environment-variables)
- **W：**普通字符串、f-string 文本、三引号字符串中的 `#` 当前处理正确；问题是第 3 条的行坐标失配。`_heredoc_body` 取首个独占行收标记符合当前 shell 语义，后面再出现同名收标记本身不构成错误。
- **X：**直接删除 NUL `printf`、NUL `split` 或 `fsdecode`，名字静态门会红；但清理 guard 门不会。新增行为门针对前导空格回归有效，未覆盖上述尾 LF 与冒号，本轮未执行其端到端负控。

OpenCode 结论有版本边界：未核用户安装版本，官方 V2 已采用路径 ID 语义，不能把 v1 的名称去重结论推广到所有版本。[V2 技能文档](https://opencode.ai/v2/docs/skills)


