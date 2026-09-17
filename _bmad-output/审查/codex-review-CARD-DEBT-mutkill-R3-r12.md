> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-12
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r12.md)"`
> 审查绑定: `142363a2`（提交时 HEAD；B0 H1 M2 L1 —— 本轮全部整改并另起 round-13，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 `142363a2`；仅只读检查及纯内存复现，未运行 pytest。

- **HIGH 多条失败被 nodeid 去重后绕过位置守卫，仍可拼出假 KILLED** — [mutation_kill_identity.py:1026](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1026) — 两条摘要使用相同长前缀 `test_x[1100个a]`，分别接 ` - EXPECT]first`、` - EXPECT]second`，位置分别为门内 `OTHER`、helper 内 `EXPECT`；实测失败记录为 2、去重 nodeid 为 1，最终仍为 `KILLED`。

- **MEDIUM 新位置守卫越过弱位置边界，拒绝已满足唯一 expect_loc 的正常失败** — [mutation_kill_identity.py:1027](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1027) — 同门两参数失败的摘要与位置消息均含 `EXPECT`，一条命中唯一 `stmt:`、另一条落在 helper；实测锚有效、`_loc_identity=True`，却由 r11 的 `KILLED` 变为 `HARNESS-ERROR`，即使 `require_gate_file=False` 也如此。

- **MEDIUM AST 分母仍漏掉通过参数传递或别名执行的就地改表** — [mutation_verdict_reconcile.py:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:195) — 对内存源码 `MUTATIONS=[1,2,3]; list.append(MUTATIONS,4)`，计数逻辑静默返回 3、实际长度为 4；`alias=MUTATIONS; alias.append(4)` 同样绕过，仍能让部分表冒充全量。

- **LOW reconcile 的解析契约注释仍说得比代码宽** — [mutation_verdict_reconcile.py:247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:247) — 注释声称 `^…$` 整行锚定，实际第 252 行没有行尾锚；第 237 行仍称“三套形态互不相同”，实际 g32cb/g32ccr1 共用同一形态。

补充：g33 信号与末次还原路径未发现新增缺陷；当前独立分母确为 **138/9/11/18**。本轮 g32cb 已完成 9/9，g32ccr1 最后采样仍在运行；七层负控存档绑定旧 SHA，不能代替 r12 全层验证。D-28 的文本歧义根治不另计缺陷，上述 HIGH 属于本轮多实例检查的漏计。

BLOCKER=0 HIGH=1 MEDIUM=2 LOW=1


