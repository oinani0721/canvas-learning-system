> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-8（终轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r8.md)"`
> 审查绑定: `39cdd761aa547dd9e856939ff80f3f84e198d1a8`（**绑最终 HEAD**；审查者自证三份送审文件与该提交逐字节一致）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> **本轮 MEDIUM 0 / LOW 0**；剩余 BLOCKER 1 + HIGH 1 均由审查者自己写明「只能交人裁、范围判断不变」。
> 此后代码零改动 ⇒ 本存档**绑最终 HEAD 且代码树 diff 为空**。

---

本轮绑定 **`39cdd761aa547dd9e856939ff80f3f84e198d1a8`**；三份送审文件已与该提交逐字节核对一致。

**结论：BLOCKER 1 / HIGH 1 / MEDIUM 0 / LOW 0。r7 的 MEDIUM 已关闭，未发现新增问题；两项既有人裁事项仍开放。**

**BLOCKER**

- **并发目录变更仍可能让已打开 fd 的写入落入禁写面；范围判断不变。**  
  位置：[scripts/deploy-vault.sh:1917](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1917)。  
  怎么看出来的：落点检查通过后，将所属目录搬入用户级 Codex 目录，随后 `write_all` 仍跟随原 inode；新增 `flock` 不约束目录重命名。

**HIGH**

- **历史探针曾写入真实 Codex 状态目录，后续配置 SHA 相同不能追认整目录零写；范围判断不变。**  
  位置：[hard-boundaries-codex-attribution-20260917T031631.txt:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:32)。  
  怎么看出来的：存档明确承认探针启动产生 `sessions`、`skills` 写入；这是历史探针验收问题，不是部署脚本调用 Codex。

**MEDIUM：无。**

**LOW：无。**

r8 的锁修复核对结果：

- [新建锁 :1863](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1863) 覆盖正文写入、`fsync`、身份检查及失败清理，直到关闭 fd；[已有文件锁 :1876](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1876) 覆盖实际读取。r7 的“先报 `kept`、后被创建者清理”交错已关闭。
- `O_EXCL` 创建至取锁之间，另一部署仍可能抢先读到空文件，但会明确失败，不会假报成功。
- 本轮未改变 opencode 发布逻辑；整卡对其增加的创建锁与 Codex AGENTS 使用同一文件锁，未发现回归。
- [锁敏感性门 :5462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5462) 是 AST 调用计数门；删锁变红证明结构敏感性，不能替代真实并发故障注入。

其余问题逐项确认：

| 问题 | 核对结果 |
|---|---|
| 0．用户级配置写入 | 除既有并发命名空间风险外，未发现新增写入路径。脚本中的 Codex 命令均为输出正文，没有执行调用。 |
| 1．负控是否为空判据 | `030813` 已明确作废；有效的 `030951` 记录目录跑前、跑后均不在 trust 表，并有成功完成的真实执行事件。SHA 仅证明该次前后内容相同。 |
| 2．执行凭据 | 原始 JSONL 第 5 行确为 `item.completed`＋`command_execution`，退出码为 0；没有采信模型消息。零事件改判“未测出”正确。未保留解析器源码，不能扩大为所有解析分支均已验证。 |
| 3．端口 | 新模板和说明直接使用 `$PORT`，与 Claude 使用同一变量，首跑不会漏替换 `8011`。已有模板及完整段按设计保留，不自动更新端口。 |
| 4．生成后在位判 | 放在生成后合理；缺失、非普通文件或叶子软链均失败，并向上传播。 |
| 5．AGENTS 追加 | 拒绝无生成标记的手写文件、软链及预存多硬链接；协作锁覆盖判重、追加和回滚，半截段有拒绝诊断。**并发新增硬链接仍受既有命名空间稳定性风险限制**，不能声称所有硬链接场景都已阻断。 |
| 6．manifest `exclude` | 确实放弃部署后的形态校验，不能视为与 `generate` 等价；[manifest :91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:91) 已明确披露损失。按本轮范围不重复计为新增问题。 |
| 7．写入面清单 | `.codex` 目录、`config.toml`、`AGENTS.md` 三个对象对应正确；双宿主时 AGENTS 只登记一次，没有新增锁文件。 |

旧门换例保住了单值和“合法值＋未实现值”组合。测试存档为 **242 passed / 9 skipped**；全量仍有 **35 failed / 29 errors**，独立复算其 64 个失败节点与基线一致。

本轮仅做只读核查，未修改文件、未运行部署或测试、未调用 Codex 探针、未连接数据库。


