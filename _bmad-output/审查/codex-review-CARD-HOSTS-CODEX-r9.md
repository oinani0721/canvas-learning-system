> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r9.md)"`
> 审查绑定: `b47eea11336ea33dd10dd46dbeccade7bef32fc8`（绑最终 HEAD；审查者自证三份送审文件逐字节一致）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> **本轮 BLOCKER = 0**：原 BLOCKER 由审查者**降级为 MEDIUM（登记不阻断）**。剩 HIGH 1（历史探针写入）。

---

绑定 **`b47eea11336ea33dd10dd46dbeccade7bef32fc8`**，三份送审文件与该提交逐字节一致。

**判断：本轮改动正确，未发现新增实质问题。原 BLOCKER 降为 MEDIUM，登记不阻断；历史 HIGH 范围不变。**

**BLOCKER：无。**

**HIGH：1 条，历史遗留。**

- **历史探针的整目录零写仍未获证明，范围判断不变。**  
  位置：[hard-boundaries-codex-attribution-20260917T031631.txt:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:32)。  
  怎么看出来的：记录承认探针启动产生 `sessions`、`skills` 写入；后续配置 SHA 相同不能追认这部分。它属于历史探针验收问题。

**MEDIUM：1 条，由原 BLOCKER 降级，并非新增。**

- **并发改名仍能突破落点检查，但现有场景不足以证明阻断级损害。**  
  位置：[deploy-vault.sh:1920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1920)、[清理分支 :1964](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1964)。  
  怎么看出来的：落点检查后搬走目录，后续写入仍跟随原 inode。

  **降级理由：**模板使用 `O_EXCL` 新建；改名不会让其 fd 自动指向既有用户配置。要用它替换原配置，攻击者必须先凭目标目录权限实施覆盖或移除，这一步本身已经足以造成损害。在题设权限前提下，我没有找到脚本额外造成的既有数据损失、权限扩大或安全边界突破，不能仅凭“存在越界写路径”继续判 BLOCKER。

  **但不能把降级理由写成“保护面恒留 0 字节”：**若 `write_all`／`fsync` 在后置检查前失败，`displaced` 仍为假；若搬走整棵 vault，相对 `vfd`／`dfd` 的检查仍可能成功。这些场景仍可能留下正文或标记。因此，**D-26(i) 的绝对零写保证仍未成立**。

**LOW：无。**

本轮整改的具体核对：

- [位移判断 :1935](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1935) 正确处理目标消失和 inode 替换；成功截空后不再写标记。
- 普通正文写入、`fsync` 失败仍走原来的标记路径。后置 `stat` 的其他 `OSError` 也会跳过标记，但 stderr 保留具体异常，空文件下次在 [:1885](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1885) 明确拒绝，没有变成 `kept` 假绿。
- [AGENTS :2227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2227) 保留新建失败截空、追加失败恢复原长度的行为；新增异常处理没有破坏它们。

其余问题核对如下：

| 问题 | 结论 |
|---|---|
| 0．用户级配置写入 | 未发现直接调用 Codex 或静态穿链写入的新路径；上述并发残留意味着作者“任何路径零写”的绝对表述不成立。 |
| 1–2．负控与执行凭据 | 有效负控目录跑前、跑后均不在 trust 表；[原始事件第 5 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-readonly-events-20260917T030951.jsonl:5) 确为完成的 `command_execution`，退出码 0。`030813` 已明确作废；零事件判“未测出”正确。SHA 只证明该次前后内容一致。 |
| 3．端口 | 新模板和说明直接使用同一个 `$PORT`，不会漏留固定 `8011`；已有模板和完整段按设计保留。 |
| 4．后置在位判 | 放在生成之后合理；失败向上传播，终止步骤 3。 |
| 5．AGENTS 追加 | 拒绝无生成标记的手写文件、软链、预存多硬链接；协作锁覆盖判重和追加，半截段有诊断。并发恶意变更仍属上述残留。 |
| 6．manifest | `exclude` 确实放弃部署后的独立形态检查；[登记项 :91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:91) 已明确披露，不能视为与 `generate` 等价，本轮不重复计项。 |
| 7．写面清单 | 目录、模板、AGENTS 三个对象对应正确；双宿主时 AGENTS 去重。旧门换例保留原有组合形状。 |

测试存档为 **243 passed / 9 skipped**；全量的 **35 failed / 29 errors** 与基线失败节点一致。新增位移测试是结构门，不能替代真实竞态验证。本轮未运行测试、部署或探针，未修改文件、未连接数据库。

**原 B 可按登记不阻断处理；历史 H 仍保持原有人裁状态，不能据此宣布全卡问题清零。**


