> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r7.md)"`
> 审查绑定: `ce236cc82e76d9af5235fee4cf39683f808d8753`（绑最终 HEAD；审查者自证三份送审文件与该提交逐字一致）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> 本轮确认 r6 指定的四项「本卡可修」**全部关闭**；新发现一条模板发布器缺互斥（MEDIUM，可修，已于 r8 修）。

---

本轮绑定 **`ce236cc82e76d9af5235fee4cf39683f808d8753`**；三份送审文件均与该提交逐字一致。

**结论：BLOCKER 1 / HIGH 1 / MEDIUM 1 / LOW 0，不能通过。**

- **本卡可修：MEDIUM 1。** r6 指定的四项可修问题均已关闭，但发现一项配置发布竞争。
- **只能交人裁：BLOCKER 1 / HIGH 1。** 两项范围判断不变。

**BLOCKER**

1. **守卫通过后的并发目录 rename 仍可能让 fd 写入落入禁写面；只能交人裁。**  
   位置：[scripts/deploy-vault.sh:1908](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1908)。  
   怎么看出来的：文件落点检查通过后，把所属目录搬入真实 `~/.codex/`，后续 fd 写入仍跟随原 inode。维持 r6 判断：本卡内未找到已验证的闭合方案，需要裁定目录稳定性或隔离前提。

**HIGH**

1. **历史探针确实写过真实 Codex 状态目录，不能以配置 SHA 相同追认整目录零写；仍需人裁。**  
   位置：[hard-boundaries-codex-attribution-20260917T031631.txt:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:32)。  
   怎么看出来的：存档承认探针启动后写入 `sessions`、`skills`；后续重定向 home 不撤销历史写入。范围仍是历史探针验收，不是部署脚本调用 Codex。

**MEDIUM**

1. **配置发布器缺少读写互斥，另一部署可能把随后被清理成残件的模板报告为成功；本卡可修。**  
   位置：[scripts/deploy-vault.sh:1864](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1864)，关联 `1900、1911、1941–1944、2292`。  
   怎么看出来的：A 写完正文、尚未完成 `fsync`；B 无锁读到完整正文并返回 `kept`；A 随后 `fsync` 失败，将文件截断并写入 `INCOMPLETE`；B 的最终检查仅验证普通文件及非软链，仍能通过。此交错无需目录 rename，也无需用户修改文件。  
   配置的新建、失败清理与已有文件读取应遵守同一把锁。上述结论来自源码时序，本轮未做写盘故障注入。

**LOW：无。**

其余核验结果：

| 核对项 | 结论 |
|---|---|
| 四项 r7 修复 | 两个平台门均早于各发布器的目录打开/创建；三处清理解禁紧跟守卫正常返回，所有清理分支均检查开关。四处 flags 检查及真分支 `else` 剪枝已补齐；四种变异在内存复演中均打红。 |
| 用户级配置写入 | 未发现除上述既有 rename 风险外的新写入路径；部署脚本没有执行 Codex，相关命令仅为输出正文。 |
| 负控与执行凭据 | `030813` 已作废。`030951` 记录目录跑前、跑后 trust 命中均为 0；原始 JSONL 第 5 行确为完成且退出码为 0 的执行事件，没有采信模型自述。零事件判“未测出”正确。SHA 只能证明该次前后内容相同。 |
| 端口 | 新模板和说明直接使用 `$PORT`，首跑不会漏替换 `8011`；已有模板与完整段按设计保留。 |
| 生成后在位判 | 放在生成后合理，缺失或叶子软链会失败；不能发现上述并发残件问题。 |
| AGENTS 追加 | 静态状态下拒手写文件、软链和多硬链接；协作锁覆盖判重、追加及回滚，已覆盖的半截段会明确拒绝。 |
| manifest | `exclude` 确实放弃部署后形态校验，损失已明确披露；按本轮范围不重复计入旧问题。 |
| 写入面与旧门换例 | 三个新增对象对应正确，双宿主 AGENTS 只登记一次；旧门保住单值和“合法值＋未实现值”组合。 |

文件级存档为 **242 passed / 9 skipped**；全量单测仍有 **35 failed / 29 errors**，其失败节点集合与基线相同。本轮未重跑写盘测试，未修改文件、未连接数据库。
