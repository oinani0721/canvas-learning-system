> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-11
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE-r11.md)"`
> 审查绑定: `a9541247`（结论 BLOCKER=0 / **HIGH=0** / MEDIUM=1 / LOW=1；D1「不清理只报告」与 D3「无 fd 泄漏」判成立。整改在 `953b8e5e`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

绑定最终 HEAD **`a9541247bf256a766fd4f23f84f364c9cdf78157`**；限定代码文件与该提交一致。

**本轮 BLOCKER=0 HIGH=0 MEDIUM=1 LOW=1。** 不能给出 D4 的全零结论。

1. **MEDIUM — 二次 `lstat` 未验证源父目录仍位于 vault。**  
   [scripts/deploy-vault.sh:1248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1248) 仍相对旧 `csfd` 检查叶子；父目录移走后，这个 fd 也随之指向移走的目录。  
   **一句复现思路：**取得源技能 fd 后、建链前，将整个 `$VAULT/.claude/skills` 同文件系统 rename 到 vault 外，再于原位置建立指回它的软链，此后绑定解析、源 inode 比较及叶子 `lstat` 全部通过，绑定函数返回成功，但落点已在 vault 外。

   这是**后核之前已经形成、后核仍识别不了**的状态，不属于“最后检查到使用之间”的已登记窗口；整体搬移 `.claude` 同理，无需引入 mount 变化。整改需要从 `vfd` 重新逐级验证当前源父链，不能只检查旧 `csfd` 下的叶子。

2. **LOW — 测试名称和说明仍宣称失败清链，与本轮行为相反。**  
   [backend/tests/unit/test_deploy_vault_sh.py:4599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4599) 的名称、docstring 仍写“清掉本次建的链”“零残链”；实际断言已要求禁止删除、必须报告。脚本 `:1134` 的注释也有同样残留。  
   **一句复现思路：**对照该测试 `:4626–4628` 的禁删除断言与脚本 `:1274` 的仅报告分支，即可看到说明与行为相反。

**D1：不清理、只报告的取舍成立，但“存在即拒”不能用于概括软链重跑。** 同目标串的已有链会幂等复用，仍经过前置逐级 `O_NOFOLLOW` 和统一后核，并非仅凭目标串接受。没有并发变化时，源根或源叶子已是外指软链的残链会被拒；恢复成合格真目录的可以复用。完整部署重跑还可能先被既有环境或安装闸门拦住，不能承诺自动恢复。上述 MEDIUM 是仍未覆盖的并发形态。

**D3：未发现 `csfd` 早退泄漏。** `die()` 的 `SystemExit` 会执行 [scripts/deploy-vault.sh:1286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1286) 的关闭分支；打开失败保持 `None`。`cfd`、`tfd`、技能 fd 和其他目录 fd 也有对应 `finally`。

其余问题的复核结论：

| 问题 | 结论 |
|---|---|
| **0．技能发现与去重** | 按题设的多根扫描、frontmatter `name` 去重语义，两条路径指向同一文件，最终只有一个逻辑技能；不能据此断言只发生一次文件读取。即使扫描器忽略 `.agents` 下的软链，直接的 `.claude` 条目仍在。实际扫描器跟链行为未运行验证。 |
| **1．dry 零写** | 新增 heredoc 均在绑定函数内，dry 于 `:1526–1532` 返回，宿主切分使用参数展开；未发现本卡新增的 dry 可达写入。前后树快照仍不能证明不存在“建完即删”的临时文件，本轮结论来自控制流复核。 |
| **2．子串约束** | 非注释行 `opencode.json` 命中 **0**。运行期拼接只用于生成文案，没有成为配置文件写入目标；本次不是写入旁路。不过词法门本身确实不能约束任意动态拼接，不能替代运行期路径判据。 |
| **3．D-26(i)** | `cls_forbidden_paths.py:270` 是唯一专门登记该整树的承重点；删除后，普通无别名输入没有另一条专门规则兜底。若同时命中其他保护规则仍可能被拒。`under('/')` 与根输入补段逻辑均已处理，未发现所问退化旁路。 |
| **4．AGENTS.md 文案** | 最终文案明确给出 vault 根的 `opencode.jsonc`、`remote` 和完整 `/mcp` 地址，并明确禁止修改用户级配置，没有因拼接丢失文件名。已有 `AGENTS.md` **无论是否带标记都拒绝覆盖**。 |
| **5．相对落点** | 稳定目录树下，两级回跳从 `.agents/skills` 回到 vault；`.git` 是目录还是文件不参与解析，落点一致。并发搬移另见 MEDIUM。 |
| **6．写面登记** | 根与文档进入 `PENDING_WRITES`，叶子进入同一 `--outputs` 判据，`.agents` 中间段也受逐段检查。最终版已无 `AGENTS.md.tmp → mv`，采用 `O_EXCL` 直接新建；已登记窗口不重复计数。 |
| **7．既有门更新** | 最终新增的是 **两个 label**。精确集合仍使用 `==`，原 label 保留，并检查条件 append 的位置，属于按用途登记；另外两门仍保留 `codex/dsh/claude,codex` 拒绝及剩余禁件检查。 |

只读验证完成：Bash 语法检查通过；两条纯静态门经内存抽取执行通过。未运行 pytest、部署脚本、数据库或模型；上述竞态是静态系统调用推演，未写盘复现，作者所称两版 dry 输出逐字相同也未动态重做。


