> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-19
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r19.md)"`
> 审查绑定: `338fc0e0`（提交时 HEAD；B0 H0 M0 L3 —— 本轮全部整改并另起 round-20，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核绑定 `338fc0e0`。限定读取面内，未发现新的运行期缺陷；仍有三处说明与代码不符：

- **LOW** `_nodeid_shaped` 把启发式限制写成 pytest 合法性要求 — [mutation_kill_identity.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:240) — 对照现有真 pytest 用例中的 `test_x[d] - EXPECT`：它可被收集，该函数却返回 False，因此只能称“不满足此启发式”，不能称“不合法”。

- **LOW** 测试注释把守卫置位时序写反 — [test_mutation_kill_identity_r3.py:525](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/tests/unit/test_mutation_kill_identity_r3.py:525) — 对照 `RestoreGuard._finish`：1274 行先置 `_finishing=True`，1285 行才调用还原，并非“还原之后置位”。

- **LOW** 对账注释误称前四项全部来自聚合来源 — [mutation_verdict_reconcile.py:589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:589) — 对照 572、584 行，AST 分母来自源码且实际参与比较；准确表述应是“四个数只约束总量，不能识别档间补偿”。

r18 五条更正的主体与实现相符。`old_rule` 主体与旧版一致；新增锚能挡住相等性检查遗漏，但不能单独检出 `left` 非空守卫被删除，不能视为穷尽等价证明。未发现其余整改把问题转移成新的缺陷；26 层存档也不等于防线覆盖完备性证明。

全程只读，未运行 pytest、变异 harness 或连接数据库。

BLOCKER=0 HIGH=0 MEDIUM=0 LOW=3


