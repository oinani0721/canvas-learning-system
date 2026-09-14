> 批次: BATCH-2026-09-11-第十四批 · 车道 T2 · 卡 CARD-G2-8 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8-r2.md)"`
> 审查绑定: `53eca445`（prompt 的最小读取面写死该 SHA；prompt 另一处仍残留 r1 的 `bb070e6f`，Codex 已自行指出并按 `53eca445` 复核，见正文首段。本轮后有 r2 整改 commit，故本档**不绑**最终 HEAD）
> 会话头自证（抄 .stderr，行号如实标；.stderr 本身不入库）:
> `.stderr:4` `OpenAI Codex v0.153.3` / `.stderr:7` `model: gpt-6-astra` / `.stderr:11` `reasoning effort: ultra`

---

**r2 尚未全部闭合：1 HIGH / 2 MEDIUM / 2 LOW，未发现 BLOCKER。**

实际 HEAD 为 `53eca445`，`bb070e6f` 是整改前提交。本轮按指定 diff 终点复核；未写文件、未运行 pytest 或部署、未连接服务，边界验证仅在内存中执行。

- **HIGH** — [scripts/deploy-vault.sh:442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:442)：现有门只覆盖复查前对象变化，未覆盖复查通过后至 `>>` 重新打开路径之间的变化，该路径仍可能写入未经检查的对象且不设置 `ACT_JOURNAL_ERR`。
- **MEDIUM** — [scripts/deploy-vault.sh:1413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1413)：前导零输入 `08`、`09` 通过范围校验后会在实例启动后的 Bash 算术中直接退出 `1`、跳过正常步骤收尾和步 6，而 `010` 静默按 `8` 秒计算，现有门未覆盖。
- **MEDIUM** — [scripts/deploy-vault.sh:1435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1435)：上限 `1` 秒且探测立即返回未就绪的对照输入仍执行完整 `sleep 2`，抽取原循环实测记录 `elapsed=2`，剩余休眠未受预算约束。
- **LOW** — [backend/tests/unit/test_deploy_vault_sh.py:3393](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3393)：参数门缺少“合法 JSON 对象但无顶层 `status`”的输入，`garbage` 只覆盖解析失败，不能证明 `no-status-field` 分支受门约束。
- **LOW／证据不足** — [negctl-r1fix-7seg-20260914T230041.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/negctl-r1fix-7seg-20260914T230041.txt:3)：七段仅存变异名称、返回码、断言短语与恢复摘要，缺少变异差异和原始失败输出，无法独立确认每段确实只拆一层防线。

r1 七条整改逐项结论如下：

| 原项 | 核对结果 |
|---|---|
| HIGH-1 顶层 JSON | **核对通过。** 非 JSON／非对象返回 `3`，缺键返回 `4`；`null`、`false`、对象值返回 `0` 表示键存在，输出均不会匹配就绪值；顶层失败配嵌套 `ready` 仍判未就绪。见 [脚本:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:455)。 |
| HIGH-2 紧邻复查 | **部分通过。** 复查失败、追加失败都会设置错误标志并加入失败阶段记录；检查与打开之间的窗口仍在，见上述 HIGH。 |
| MEDIUM-3 失败证据面 | **核对通过。** 步 5 失败由 `run_step` 直接退出 `75`，与只查 compose-config、禁止出现 deploy 报告的断言一致。见 [测试:3317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3317)。 |
| MEDIUM-4 Lance 预算 | **部分通过。** `curl -m` 确实取剩余预算与 `10` 的较小值；普通十进制 `1`／`86400` 未发现仅因取值导致无限循环，但前导零和固定休眠仍有上述问题。 |
| MEDIUM-5 字节保持 | **核对通过，限当前变换语义。** CR 行尾、无末尾换行、空文件、重复目标键均已做内存对照；重复键仅更新最后一次定义，缺键且无末尾换行时补 LF 后追加，原有字节保持完整前缀。见 [脚本:1523](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1523)。 |
| MEDIUM-6 失败返回码 | **核对通过。** 进入步 6 后，阶段账与 also-push 同时失败仍发布 `rc=76`、退出 `76`；阶段账失败记录保留在报告中。见 [脚本:1641](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1641)。 |
| LOW-7 混合分隔／空值 | **核对通过。** 两类输入已补门，断言实际清单结果，对对应行为敏感。见 [测试:3705](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3705)。 |

其余自述：

- **兄弟实例判据核对通过，限桩模型。** 兄弟端口结果依赖同一 `CLS_FAKE_STATE` 中的 `cls-sibling`，测试同时检查前后端口、本实例消失及兄弟实例存活，并非恒 200。见 [测试:3064](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3064)。
- **Graphiti 双侧断言及正控核对通过。** 已覆盖的失败输入同时要求 skipped、禁止 ready，另有明确就绪正控；缺键覆盖缺口如上。见 [测试:3417](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3417)。
- **SKIP 标记核对通过。** 未授权路径返回 `2`，步状态保留 SKIP，报告注明未进入真 activate；最终流程 `rc=0` 没有将该步改记为 OK。见 [脚本:1291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1291)。
- **步 1～4 未改核对通过。** 两提交间相关函数全文字节一致；连字符拒绝、下划线通过的门使用真实 harness。
- **写面及计数核对通过。** 新增阶段账使用已申报的 compose-config／deploy 对象；harness `.env` 属新增写对象，虽不在 `PENDING_WRITES`，调用处具备同一 outputs 判据、复查、`open_pinned`、硬链接检查及 `write_all`，四个计数 `2→3` 对应实际第三处写入。见 [脚本:1491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1491)。
- **journal 路径计算核对通过。** 两条路径调用 harness 的真实模块计算；Lance 耗时及进度字段已记录，但 `table_count` 仅检查键存在，未验证数值类型。见 [脚本:1378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1378)。

**新增八个用例未发现恒绿**：两条 Graphiti 参数、Lance 嵌套状态、慢探测、阶段账失败、CRLF、混合分隔、空值均依赖实际输出、文件内容或计时。存档记录由 `166 passed / 9 skipped` 增至 `174 passed / 9 skipped`，数量相符；这是存档结果，本轮未重跑。七段存档的恢复哈希与当前脚本一致，但仍不足以证明各段变异的独立性。
