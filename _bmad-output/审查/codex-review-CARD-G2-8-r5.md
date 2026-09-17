> 批次: BATCH-2026-09-11-第十四批 · 车道 T2 · 卡 CARD-G2-8 round-5（卡文允许的最后一轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8-r5.md)"`
> 审查绑定: `4309757b`（该轮 HEAD）。⛔ **本轮有 HIGH 且已按 Codex 要求在本卡整改**，整改 commit 在本档之后 ⇒ **本档不绑最终 HEAD**，且轮次已达卡文上限 5 ⇒ 按协议 §1「第 5 轮仍有 HIGH → 停下交主 session 人审」处理，见验收单。
> 会话头自证（抄 .stderr，行号如实标；.stderr 本身不入库）:
> `.stderr:2` `OpenAI Codex v0.153.3` / `.stderr:5` `model: gpt-6-astra` / `.stderr:9` `reasoning effort: ultra`

---

**r5 结论：1 项 HIGH、2 项 LOW。r4 的 HIGH 尚未闭合，必须在本卡修；两项 LOW 可登记移交。**审查绑定 `4309757b`，全程只读，未连接 Docker／Neo4j，未重跑 pytest。

- **HIGH — [deploy-vault.sh:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:452)**：现有门未覆盖“`assert_writable_now` 已通过、`lstat` 尚未采样时，阶段账已成为 `nlink=2` 的共享对象”这一输入，此时 `want=got=dev:ino:2` 仍通过第 470 行比较，后续写入会落到复查未认可的共享对象。
- **LOW — [test_deploy_vault_sh.py:3826](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3826)**：非法超时值动态门覆盖 `0/000/8a`，尚未覆盖 `86401`、六位／二十一位数字及非 ASCII 数字这些边界输入。
- **LOW — [test_deploy_vault_sh.py:3968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3968)**：新增 `up` 失败门只预置兄弟项目，而桩在 `up` 非零时不加入本项目，因此尚未覆盖“本项目已部分创建后失败、随后确被清理”的对照。

**HIGH 必须本卡修的理由**：它正是本轮声称关闭的开账写对象保护边界；当前身份快照发生在复查之后，不能代表“复查当时的对象”。这是 r4 原问题的剩余路径，轮次上限不能作为移交理由。

其余自述逐项核对：

| 项目 | 结论与依据 |
|---|---|
| 回滚只拆本项目、兄弟存活 | **核对通过**。[测试:3063](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3063) 的兄弟返回依赖同一项目清单，缺项返回非零；健康失败和新增 `up` 失败门均检查前后兄弟存活，**r4 LOW 原要求已补齐**。 |
| Graphiti 三失败面 | **核对通过**。[测试:3439](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3439) 覆盖 curl 非零、缺字段、解析失败、明确未就绪及嵌套干扰，同时要求 skipped 出现、ready 不出现，另有就绪正控。 |
| `--also-push` 去重及字节保留 | **核对通过**。[测试:3517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3517) 及后续门覆盖混合分隔、缺键、空值、引号、CRLF 和无末尾换行；`ACTIVE_VAULT` 保留原字节，命中已有名称时整份文件不变。 |
| 未授权激活的 SKIP | **核对通过**。[脚本:1342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1342) 返回 SKIP，证据明确“未进入真 activate”；整跑 `rc=0` 不表示激活已执行。 |
| 步 1～4、名称门 | **核对通过**。与 `677fa112` 逐字节比较，四步函数完整区段相同；[测试:3605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3605) 使用真实 harness 分别钉住连字符拒绝、下划线放行。 |
| 写入面与硬化计数 | **核对通过，但上述 HIGH 除外**。新增记账使用已申报的 compose-config／deploy／tmp；[脚本:1571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1571) 的 `.env` 虽未进步 1 清单，但具有独立禁写检查、复查、`open_pinned`、fd 硬链接检查及 `write_all`，达到既有 Python 写点同级；四个严格计数 `2→3` 对应真实第三写点。 |
| Lance 超时取值 | **实现核对通过**。[脚本:1372](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1372) 在启动前完成 ASCII、长度、剥零及 `1..86400` 校验，curl 和 sleep 均受剩余预算约束；未发现取值导致不终止或数值上限失效，动态覆盖缺口见 LOW。 |
| journal 路径与 Lance 记账 | **核对通过**。[脚本:1448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1448) 调 harness 的真实路径模块计算两条 journal；Lance 单独记录耗时与 `table_count`，未就绪记录非零及 unknown。 |

r4 的 fd 推理**部分成立**：核对 `fstat(9)` 正确，持有 fd 后单纯替换路径不会改变写入 inode，③④之间没有同类路径重解析窗口。本轮用只读 `/dev/null` 对照确认当前 Bash 3.2 的命令替换内 Python 能继承 fd 9；环境若关闭 fd 或使 `fstat` 失败，[第 470 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:470) 会关闭并拒绝。`nlink` 能发现两次采样间的数量变化，但不能拒绝“两次均为同一共享 inode、链接数均大于 1”的输入。

**17 段单层负控核对通过**：[最终存档:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/negctl-final-r4-17seg-20260915T000551.txt:129) 仅撤复查条件，`:305` 仅撤身份条件；全部 17 段分别有对应变异和断言 KILLED，恢复哈希与当前脚本一致。它们证明两层各自承重，不能证明上述夹缝已覆盖。

证据边界：步 5 失败会直接退出，阶段账只留 compose-config，**不会进入步 6 双份落账**。[文件级存档:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/unit-deploy-r4fix-20260915T000945.txt:55) 的结果是历史运行 **190 passed、9 skipped**；本轮另做 Bash 语法、Python AST 和字节／哈希核验，均通过。
