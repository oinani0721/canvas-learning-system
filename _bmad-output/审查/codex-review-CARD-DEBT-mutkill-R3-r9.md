> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r9.md)"`
> 审查绑定: `00ff16e3`（提交时 HEAD；B0 H1 M3 L0 —— 本轮全部整改并另起 round-10，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

绑定 **`00ff16e3`**，不包含审中出现的外部未提交修改。**r8 回滚理由成立，但收口仍有以下缺陷。**

- **HIGH 候选并集仍漏掉合法动态测试名，假 KILLED 未封闭** — [mutation_kill_identity.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:341) — 用动态名 `test_x[case] - EXPECT]tail`、真实消息 `OTHER` 的对应摘要调用裁决器，实得 `KILLED`：完整名字被两种候选判据同时排除，误截出的 `test_x[case]` 却通过 `_boundary_ok`。

- **MEDIUM g32b 逐条输出整批漏数，补偿式篡改仍能通过** — [mutation_verdict_reconcile.py:320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:320) — 按真实形态构造 138 条 `→ KILLED` 记录，聚合改成 KILLED=137、SURVIVED=1，`reconcile_one()` 返回空问题列表，因为记录没有 `rc=… ⇒`，整批降为“未核”。

- **MEDIUM `rc=` 前缀仍可被诊断文字注入，计数污染只是换了入口** — [mutation_verdict_reconcile.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:244) — 在真实 g32cb tee 的一条诊断中加入 `diagnostic rc=1 ⇒ KILLED`，9 条被数成 10 条，一致的聚合因此对账假红。

- **MEDIUM 只读方法仍暴露原列表，AST 分母白名单可绕过** — [mutation_verdict_reconcile.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:193) — `MUTATIONS=[1,2,3]; MUTATIONS.copy.__self__.append(4)` 的实际长度为 4，`ast_mutation_count()` 仍返回 3，未按承诺拒绝无法计数的改表。

核验：当前四套分母仍为 **138/9/11/18**；完整 g32cb/g32ccr1 存档逐条计数正常。H2、锚检查与 g33 还原主路径未发现新缺陷。上述裁决反例已在固定提交的内存调用中验证；新动态名字的 pytest 可收集性由存档机制推导，本轮未跑 pytest、未写文件、未连数据库。

BLOCKER=0 HIGH=1 MEDIUM=3 LOW=0
