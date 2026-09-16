> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r4.md)"`
> 审查绑定: `1d2d4b5b`（送审时 HEAD；本轮整改后 HEAD 再前进，见 round-5）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

结论：**仍有 1 BLOCKER、1 HIGH、3 MEDIUM、1 LOW。** 已只读核对指定提交、证据及内存变异；未运行部署、Codex、pytest 或数据库操作。

**BLOCKER**

1. **新增写入仍能随目录搬移进入用户级配置，风险窗口并不止于 `openat`。**  
   位置：[scripts/deploy-vault.sh:1804](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1804)、[1851](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1851)。  
   场景：cfd 检查通过、1814 已打开文件之后，把该 `.codex` 搬成 `$HOME/.codex`（目的名空闲或原目录已被移开），1851 仍经原 fd 写用户级 `config.toml`；之后报错也撤不回越界写入。

   对作者三项判断：① 新检查确实拦住了**检查前已经搬走**的情况，但打开文件后的搬移仍有效；② 旧模块已有同类局限属实，**本卡新增了受其影响的写入路径**，不能据此免责；③ 在允许并发恶意 rename 的前提下，继续增加路径检查、普通 fd 或协作锁不能真正闭合，需要强制阻止搬移的权限条件或内核隔离。我未验证到可在本卡直接落地的闭合方案。

**HIGH**

1. **Codex 的锁仍挡不住同脚本中未取锁的 OpenCode 发布者，追加内容可能被覆盖或清零。**  
   位置：[scripts/deploy-vault.sh:2068](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2068)、[2095](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2095)。  
   场景：A 的 OpenCode 发布器短写到合法首行后暂停；B 的 Codex 发布器取得锁、接受 `oc_mark` 并追加成功；A 不遵守该锁，继续从原偏移写入会覆盖 Codex 段，失败清理也可能截掉它。另一写者见 1523、1553；这是新增追加行为带来的互操作问题。两个发布器应共同遵守同一把锁。

**MEDIUM**

1. **`[mcp_servers.` 子串不能证明模板完整，r3 的残件误收仍未关闭。**  
   位置：[scripts/deploy-vault.sh:1843](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1843)。  
   场景：写入截断在 `[mcp_servers.`，或完整段头之后、`url` 写出之前，且清理失败；重跑仍报 `kept`，后置普通文件检查也通过。已在内存中用实际 AST 条件确认这两个反例均不会被拒。

2. **结构门仍会把字符串当成真实调用，剥注释没有关闭假绿问题。**  
   位置：[backend/tests/unit/test_deploy_vault_sh.py:5340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5340)、[5385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5385)。  
   场景：把三处守卫、两处 flock 调用换成同文本的 Python 字符串表达式；纯内存验证得到真实调用数为零、Python 与 Bash 语法有效，但四条相关结构门仍全部通过。

3. **新增 `exclude` 登记确实放弃了独立校验器的配置形态检查。**  
   位置：[scripts/vault-install-manifest.json:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:89)。  
   场景：部署后把 `.codex/config.toml` 换成目录或软链，独立校验器仅记 `intentionally-excluded`，不会因此失败。note 已如实披露，不能说仍在隐瞒，但“其他门会红”没有解决这个验收缺口；生成后的当次检查也不能覆盖后续漂移。

**LOW**

1. **段首阈值 5 仍漏掉可与正常换行区分的短残片。**  
   位置：[scripts/deploy-vault.sh:2088](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2088)。  
   场景：末尾只留下 `\n<`、`\n<!` 或 `\n<!-`，下次会追加并保留残片。阈值取 2 即可识别这些情况，也不会误拒单独的正常末尾换行；影响主要是残片遗留。

其余指定项的核对结果：

- **有效负控不是空判据。** `030951` 记录跑前目录不在 trust 表中；[原始事件第 5 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-readonly-events-20260917T030951.jsonl:5) 确有成功完成的 `command_execution`。`030813` 的零事件结论已明确作废。
- **auth 副本整改的存档记录了真实 auth/config SHA 不变**，但未附探针源码及原始事件，无法独立核查副本创建、清零的异常分支；不能扩大成任意情形下零写入的证明。
- **首次生成的端口直接使用 `$PORT`，与 Claude 同源。** 但已有模板走 `kept`，不会检查或改掉其中的旧 `:8011`。
- **在位判放在生成之后合理**，缺失或叶子软链会失败；它证明的是文件形态，不能补足上述内容完整性和竞争窗口。
- **两个 Codex 写者之间原先的破坏时序已关闭。** `open→flock` 仍有窗口，但抢先取得锁的另一个 Codex 写者会因空文件缺标记而拒绝，并非一定等待创建者。
- 静态手写无标记文件、已有软链、多硬链接 AGENTS.md 均有拒绝路径；三条旧门替换保留了原有输入形状，步 1 新增对象登记也一致。
