> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r3.md)"`
> 审查绑定: `41ddf0d0`（送审时 HEAD；本轮整改后 HEAD 再前进，见 round-4）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

审查绑定 `7a8d50e2 → 41ddf0d0`。结论：**BLOCKER 1 / HIGH 2 / MEDIUM 3 / LOW 0**。全程只读；未运行部署、Codex 探针或写盘测试。

**BLOCKER**

- **fd 守卫检查之后仍可发生目录改名，使后续写入落进 Codex 用户级配置。**  
  位置：[scripts/deploy-vault.sh:1769](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1769)、[1797](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1797)。  
  场景：守卫通过并打开 `cfd` 后，同文件系统内将该 `.codex` 目录移动为原本不存在的 `$HOME/.codex`，后续相对 `cfd` 创建、写入的就是用户级 `config.toml`；inode/nlink 检查仍可通过，最终按旧路径报错也已晚。`F_GETPATH` 只是当次路径查询，不能冻结之后的目录位置。[Apple 实现](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_descrip.c#L3613)

**HIGH**

- **探针的认证文件软链仍保留写穿 `$HOME/.codex` 的路径，重定向 `CODEX_HOME` 没有完成整目录隔离。**  
  位置：[codex-sandbox-2x2-20260917T034556.txt:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-sandbox-2x2-20260917T034556.txt:8)。  
  场景：使用文件认证存储且 ChatGPT 令牌触发刷新时，0.153.3 会沿 `scratch/auth.json` 的软链截写真实认证文件；只检查 `config.toml` SHA 看不到这个写入。精确版本源码确认了[刷新后保存](https://github.com/openai/codex/blob/rust-v0.153.3/codex-rs/login/src/auth/manager.rs#L2828)和[跟随软链的写入方式](https://github.com/openai/codex/blob/rust-v0.153.3/codex-rs/login/src/auth/storage.rs#L188)。这里判定的是存在写入路径，不声称存档那次已经触发。

- **AGENTS 新建分支没有参与互斥，失败清理能删除另一部署进程成功追加的内容。**  
  位置：[scripts/deploy-vault.sh:2001](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2001)、[2068](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2068)。  
  场景：A 新建并短写至合法生成首行，B 进入已有文件分支、取得锁并完成追加，A 随后写失败而截零，B 的正文也被删除。`grown > append_len` 不保护新建清理分支；这是脚本自身的不协作写者。

**MEDIUM**

- **模板仍会把“尚未落下清理标记的半截正文”当成正常文件保留。**  
  位置：[scripts/deploy-vault.sh:1819](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1819)、[1855](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1855)。  
  场景：正文只写入 `# 由 deploy-vault.sh…` 就中断，或写失败后截断清理也失败，下一次既不判空也不命中两向标记判断，直接报 `kept`；在位检查仍通过。

- **AGENTS 回滚失败后留下的半截段首，下次仍无法识别。**  
  位置：[scripts/deploy-vault.sh:2037](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2037)、[2089](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2089)。  
  场景：已有生成文件末尾留下 `\n<!-- cls-codex`，因不存在完整 `sec_mark`，下次直接追加完整新段并报 `appended`，残片被永久保留。

- **守卫调用门和加锁门仍把注释当成真实调用，存在已验证的假绿。**  
  位置：[backend/tests/unit/test_deploy_vault_sh.py:5323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5323)、[5362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5362)。  
  场景：仅在内存中把两处守卫和 `flock` 调用改成 `pass # 原调用`，两个程序块语法有效、真实调用数变为零，但调用门、锁门及副本一致门全部通过。存档中的删除变异变红，不能证明这些门检查了真实执行。

**LOW：无。**

其余核对：`030951` 原始 JSONL 确有一条成功完成的命令执行事件；`030813` 的零事件结论已明确作废。端口模板化、三条旧门改例、步 1 对象登记、生成后在位检查的时机均未发现新问题；脚本没有实际调用 `codex`。manifest 已知开放项不重复列出。


