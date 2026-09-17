> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r2.md)"`
> 审查绑定: `c228b745`（该轮 HEAD；结论 BLOCKER=0 / HIGH=1 / MEDIUM=1 / LOW=1，三条全部采纳，整改在 `4ad30472`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

## 结论

**本轮 BLOCKER=0 / HIGH=1 / MEDIUM=1 / LOW=1。**

审查绑定 `c228b74506882f7a5c482b702b29bc16afdf1dbb`；结束时 HEAD 与限定文件均未变化。

Round-1 整改判断：**H1 静态祖先软链问题已修；H2 部分修复；M1 已修；M2 修好了指定负控，但仍有覆盖缺口。**

## 分级发现

### HIGH — H2 发布仍未绑定检查过的文件身份

位置：[deploy-vault.sh:1138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1138)、`:1150–1153`、`:1083`。

`O_EXCL|O_NOFOLLOW` 保证的是**打开那一刻**新建的末段文件：

- 写完关闭 fd 后，`os.replace(tmp, dst)` 又按路径寻找 tmp；tmp 被换成普通文件时，会发布掉包后的正文。
- 最后一次 `refuse_reason(dst)` 与替换之间，仍可能出现手写目标并被覆盖。
- 父目录也没有通过目录 fd 固定；`O_NOFOLLOW` 不保护祖先路径。

后置检查仅要求 AGENTS.md 为普通非软链文件，不能发现无标记正文被发布。因而“紧邻再查”缩短了窗口，**没有闭合 H2**。

**复现思路：** 在 tmp 写完、替换前将其换成无标记普通文件，或在末次目标检查后放入手写 AGENTS.md，分别观察错误正文被发布或手写文件被覆盖。

### MEDIUM — M2 快照未覆盖实际 `$TMPDIR`

位置：[test_deploy_vault_sh.py:4247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4247)、`:4248–4250`；关联 `:84–88`、`:3266–3277`。

快照覆盖 `tmp_path`，但 `_tx_env()` 没有设置 `TMPDIR`，`_run()` 继承宿主环境。真正的临时目录可能在快照之外，**即使临时文件保留下来，门也看不见**。

**复现思路：** 在隔离负控中令 dry 分支向位于 `tmp_path` 外的 `${TMPDIR:-/tmp}` 写一个保留文件，两次快照仍相等。

应在拍摄 before 快照前，把测试的 `TMPDIR` 显式固定到 `tmp_path` 内。此项是测试漏面，**不是发现当前 dry 分支已经发生写入**。

### LOW — 源码捕获失败仍可能被空 Python 程序吞掉

位置：[deploy-vault.sh:1099](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1099)、`:1162–1163`、`:1083`。

`src="$(cat …)"` 没有检查返回码。条件调用上下文抑制了 `set -e`；捕获失败且 `src` 为空时，`python3 -c ""` 返回 0，发布程序及标记检查完全没执行。若已有普通 AGENTS.md，后置存在性检查仍可通过。

**复现思路：** 对已有普通 AGENTS.md、小技能清单的输入，令源码捕获失败并输出空串，检查发布函数是否仍返回 0。

已用只读控制流实验确认“失败捕获 → 空程序 → rc 0”；未进行文件系统 I/O 故障注入。建议显式检查源码捕获状态。

## 问题 0–7

| 问题 | 独立复核结果 |
|---|---|
| **0：发现与去重** | **软链方案成立，但会双读。** 官方固定版本 v1.18.31 跟随技能软链，按路径字符串收集匹配，两条别名会分别解析；随后按 frontmatter `name` 覆盖登记，最终一个技能条目，可能出现重复名称警告。不能解释为“只解析一次”。[扫描与登记源码](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/opencode/src/skill/index.ts#L96-L226)、[跟随软链实现](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/core/src/util/glob.ts#L12-L22)。未检查本地安装版本。 |
| **1：dry 零写** | 本卡新增写入均在 apply 分支后；新 heredoc 在函数执行时才展开，dry 提前返回。未找到新增的 preflight 前写入路径。**不能用现有快照证明全过程零写**，见 MEDIUM 和 E。 |
| **2：子串门** | 非注释行 `opencode.json` **零命中**。`:1170` 拼出的完整文件名仅在 `:1187` 输出到文案，没有作为配置文件写入目标。此次没有隐藏写路径；但拼接确实超出词法门能力，属于绕开文案误报的技巧，不能充当运行期零写证明。 |
| **3：D-26(i)** | `cls_forbidden_paths.py:270` 是唯一**专门登记该保护目录**的代码。删除后，普通无重叠路径没有替代保护；但含 `.git`、解析到其他保护目标、保护目标为 `/` 或 HOME 枚举失败时，仍可能被其他规则拒绝。`:239–240` 显式处理 `/`，`:589–590` 补齐根入口，未发现所问旁路。 |
| **4：文案** | M1 已修。实际正文给出完整 `opencode.jsonc` 文件名、vault 根位置、`remote` 和完整 `/mcp` URL，明确不要修改用户级配置；没有因源码拼接而让读者看不到文件名。格式符合[项目配置](https://opencode.ai/docs/config/#per-project)与[remote MCP](https://opencode.ai/docs/mcp-servers/#remote)要求；未验证实际连通或认证。 |
| **5：相对落点** | 相对路径从**软链所在目录**起算：`.agents/skills/../../.claude/skills/<n>` 落到同 vault 的技能源目录；祖先 `.git` 是目录还是文件不参与解析。此结论是路径语义判断，没有部署到 live vault/worktree 实测。 |
| **6：写面登记** | `:610–614` 登记根、AGENTS 和 tmp；`:991、997–999` 补判叶子；`.agents` 中间段由判据逐段检查覆盖。未发现静态写对象两层都漏登。**登记完整不等于发布安全**，TOCTOU 见 HIGH。manifest 两项及 origin 例外说明自洽。 |
| **7：既有门** | 属于按授权登记。E-1 仍断言 `codex/dsh/claude,codex` 为 rc 64；禁件门仍保留其余三项；写面门仍是旧 14＋新 3 label 的**精确集合相等**，append 留在扫描切片内。没有改成宽松集合关系；这些词法门本身不证明所有运行期写操作都已登记。 |

补充：抽取实际解析代码验证了两种宿主顺序均得到双开关，其他值仍 rc 64。`--hosts claude` 不触发新增绑定分支；**本轮没有重跑作者声称的 PREV/HEAD 完整 dry 输出 diff**，不将其记为独立实测通过。

## Round-2 A–E

- **A：两层都有作用，但保护性质不同。**  
  `deploy-vault.sh:1010` 的前置检查防止静态祖先软链造成外部写入；`:1064–1079` 的后置检查发现错误物理落点，也能发现技能源条目解析到别处。后者不是死代码。**只删前置后仍 rc 73，不代表仍保住外部零污染**：此时 mkdir、软链及 AGENTS 发布已经可能发生。

- **B：残片会持续导致失败。**  
  `:1138–1141` 对已有 tmp 返回 EEXIST，直到有人核实并移走它；属于合理的 fail-closed，但有人工恢复成本，不能称为自动自愈。直接删除未知 tmp 并不合适。

- **C：取得整条管道最右侧非零 rc。**  
  `:113` 开启 `pipefail`，所以 producer 最终非零不会被 publisher 的成功吞掉。不过 `write_agents_md` 内较早的 printf 失败、最后一条成功，理论上会被函数返回规则掩盖；未发现正常管道下可靠的独立触发场景，不单列缺陷。另需区分：**传播失败状态不会撤销 publisher 已发布的部分正文**。

- **D：无法解析会拒绝。**  
  `:1076–1077` 对文件目标、断链或无搜索权限目录，`cd` 失败进入 `return 1`；解析成功但目标不等进入 `:1078` 拒绝。`:1068` 赋值即使带 `/$name` 后缀，仍保留命令替换的失败状态，未把“问不出来”压成成功。

- **E：空目录已覆盖，元数据和瞬时写未覆盖。**  
  `test_deploy_vault_sh.py:4180–4190` 记录空目录 `"D"`；不记录权限、mtime、inode、硬链接数及根目录自身属性，也看不到相同内容重写、短暂建删或树外写入。若继续把此门称为“零写门”，建议补 root 与条目的必要 `lstat` 元数据；**atime 不宜入判据，快照读取本身可能改变它**。即便补齐，前后快照仍不能证明中途完全没有写操作。

**验证边界：** 已完成限定差异审阅、Bash 语法、Python AST、字面量扫描、抽取宿主解析及正文 stdout 校验；未修改文件、未运行部署或 pytest、未连接数据库、未启动模型。上述文件竞争复现均为静态可构造序列，未实际执行。


