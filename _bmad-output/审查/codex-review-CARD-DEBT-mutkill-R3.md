> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3.md)"`
> 审查绑定: `223beed7`（提交时 HEAD；本轮之后按 D-15 做了整改并另起 round-2，故本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 `223beed7`；以下反例均用原函数在内存中复现，未修改文件、运行 pytest 或连接数据库。

- **MEDIUM** 文件路径中的方括号被误当参数段，导致合法无 reason 摘要新增假红 — [mutation_kill_identity.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:203) — 输入 `FAILED tests/test_[x].py::test_x`，完整裁决由旧版 `KILLED-UNBOUND` 变为 `HARNESS-ERROR`。

- **MEDIUM** stdout 尾四／五档重复时静默覆盖，冲突计数仍可通过对账 — [mutation_verdict_reconcile.py:174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:174) — 在完整 g32cb 存档原有 `SURVIVED: 0` 前加入同形的 `SURVIVED: 7`，后者被覆盖，仍得到 `9/9/9`；这些档没有经过 `_one()`。

- **MEDIUM** 计数未限定为非负整数，小数截断或负数抵消会产生假绿 — [mutation_verdict_reconcile.py:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:204) — 将 g33 样本改为 `KILLED=18.9`，或 `KILLED=19、SURVIVED=-1`，均通过 AST 分母为 18 的对账。

- **LOW** 正常末次还原期间的首次信号被误报为还原失败 — [g33_mutation_gates.py:456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:456) — 在真实 `RestoreGuard.critical()` 内调用 `_handler(SIGTERM, None)`，两次还原成功、验证无漂移、rc=130，却打印“末次还原失败／不得当成干净”。

- **LOW** “有 ` - ` 切点时只会 True→False”的更正仍不成立 — [mutation_kill_identity.py:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:233) — 对 `FAILED a::b[[c] - boom`、nodeid=`a::b[[c]`，旧版返回 False、新版 True；端到端确由 `_boundary_ok` 拒绝，未形成新增假杀。

BLOCKER=0 HIGH=0 MEDIUM=3 LOW=2


