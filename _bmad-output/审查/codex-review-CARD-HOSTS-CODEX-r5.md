> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-5（协议轮次上限）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r5.md)"`
> 审查绑定: `afacca52`（送审时 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> ⚠️ 本轮意见**已在 r5 之后继续整改**（BLOCKER-1 前半实测确认并修、MEDIUM-1 的 `if False` 变异已关），
> 故本存档**不绑最终 HEAD**。协议轮次上限为 5 ⇒ 不再发起第 6 轮，终态交主 session 人审。

---

**结论：仍有 2 条 BLOCKER、2 条 MEDIUM，不能按“全部整改完成”关闭。** 已核对送审 `afacca52`；未修改文件、运行部署或 pytest、连接数据库。

**BLOCKER**

1. **中间软链仍可导致禁写面创建文件，且守卫拒绝后清理仍继续写；本卡内可修。**  
   位置：[scripts/deploy-vault.sh:1826](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1826)、[清理路径 :1906](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1906)。  
   **怎么看出来的：**1802 的 `lstat` 后，将 `.codex` 换成指向 `$HOME/.codex` 的软链，且目标 `config.toml` 尚不存在；1826 会先创建它，1877 虽然拒绝，`finally` 仍执行截断及 `write_all(incomplete)`。这是守卫已经拒绝后确定发生的写入。

   可落地修法有两部分：这两处多段路径 `open` 使用 **`O_NOFOLLOW_ANY` 替换 `O_NOFOLLOW`**；安全检查拒绝后只关闭 fd，不执行写入或截断清理。AGENTS 新建分支的 2150 也需同样处理。本机只读探针已验证：中间软链在普通打开时成功，使用 `O_NOFOLLOW_ANY` 时返回 `ELOOP`；两个 flag 同时设置则返回 `EINVAL`，与 [Apple 内核实现](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/vfs/vfs_vnops.c)一致。

2. **候选 B 没有关闭文件打开后的目录搬移窗口；仍需人裁处理范围。**  
   位置：[scripts/deploy-vault.sh:1877](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1877)。  
   **怎么看出来的：**1877 检查通过后、1878 写入前，将 `.codex` 搬进 `$HOME/.codex/` 下，文件 fd 仍指向原 inode，下一次写入便发生在禁写面。

   B 确实消除了“叶子打开前目录已搬走、原位置没有替代物”的旧路径；`O_NOFOLLOW_ANY` 也只能关闭软链解析窗口。任意并发搬移仍缺少本卡内已验证的闭合方案，需要主 session 裁定是否扩大隔离整改范围，不能仅登记残留便宣布满足 D-26(i)。

**HIGH：无。**

**MEDIUM**

1. **AST 门仍把不可达调用算作有效保护，r4 的判据整改不充分。**  
   位置：[backend/tests/unit/test_deploy_vault_sh.py:5312](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5312)。  
   **怎么看出来的：**纯内存将全部 5 个路径守卫、3 个锁调用改为 `if False: 原调用`，Bash/Python 语法仍有效，两条结构门仍 PASS。另插入通过 `getattr` 调用的未登记写操作，相关计数门也未发现；这些写入代码未被执行。应验证保护调用与实际写入的控制流关系，不能用调用数量代表保护已执行。

2. **manifest 的 `exclude` 仍放弃生成模板的形态检查；r4 遗留项继续开放。**  
   位置：[scripts/vault-install-manifest.json:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:89)。  
   **怎么看出来的：**部署后把 `.codex/config.toml` 换成目录或软链，独立校验器只登记 `intentionally-excluded`，不会报生成件形态错误。说明已如实披露损失，但绿测不能恢复这项覆盖；按既定边界跨卡移交。

**LOW：无。**

其余核对结果：

- 有效负控 `030951` 的原始 JSONL 确有一条完成且退出码为 0 的 `command_execution`；报告记录目录跑前、跑后均未受信，SHA 相同。`030813` 的零事件阴性已明确作废，没有把模型自述当执行凭据。
- 新建模板直接使用 `$PORT`，未发现缺省 `:8011` 漏替换；生成后在位判的位置合理，但不能抵消上述写入竞态。
- opencode 新增同一把锁足以阻止所述短写交错，未发现此次加锁回归。普通手写文件、静态软链、多硬链接的追加拒绝，以及重复段、已知半截段检查均有对应路径。
- 新增正常写对象与步 1 登记一致，AGENTS.md 去重正确；三条旧宿主反例保留了单值与混合列表形状；部署脚本没有实际调用 `codex`。

证据限制：历史探针确曾写入真实 `.codex` 的运行期目录；后续隔离整改不能倒推此前全过程零写。有效负控支持该次 `config.toml` 未变，不支持整目录从未发生写入。
