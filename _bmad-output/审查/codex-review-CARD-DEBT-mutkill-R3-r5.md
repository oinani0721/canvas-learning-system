> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-5（D-15 上限轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r5.md)"`
> 审查绑定: `34473ebd`（= **最终 HEAD**；本轮 BLOCKER=0 HIGH=0 ⇒ D-15 达标。本轮 3 MEDIUM + 1 LOW 按协议 §1 登记不阻断，其中「负控存档只有 17 层且绑旧哈希」已补跑 19 层重新绑定 `34473ebd`——纯证据补齐，未改代码，故本轮仍绑最终 HEAD）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 `34473ebd`。全程只读，未运行 pytest、变异 harness 或数据库操作。

- **MEDIUM AST 对未支持写法仍静默少算，部分表可再次冒充全量** — [mutation_verdict_reconcile.py:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:121) — 在内存中将真实 g32b 的 36 段 `+=` 包入 `if True:`，实际条数仍为 138，但原 `reconcile_one()` 对既有 6/6/6 部分样本返回无问题，打印 `AST=6 ✓`；列表展开也存在同型漏算。

- **MEDIUM 信号触发的成功重试仍能掩盖真实还原失败，绕过记账及自检** — [g33_mutation_gates.py:482](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:482)，联动 [mutation_kill_identity.py:1052](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1052) — 在真实 `RestoreGuard.critical()` 内登记 SIGINT 后抛 `OSError`，令守卫重试成功；内存复现实得退出码 130、自检零次、stderr 为空，首次错误被当成干净信号退出。

- **MEDIUM 当前存档不足以支持“19 层负控已锁住审 SHA”的声明** — [r3-negctl-final-m2d-20260915T000004.txt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-mutkill-r3/r3-negctl-final-m2d-20260915T000004.txt:4) — 枚举指定目录仅得 17 层，缺 `rc6`、`m2e`；已有五行跑前后哈希相同，但 g33/reconcile 仍绑定旧哈希，与当前源码不同，不能证明本轮两项整改的负控承重性。

- **LOW 末次还原成功时仍误报“末次还原失败”** — [g33_mutation_gates.py:509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:509) — 传入成功还原回调、空漂移结果及 `pending_failures=["M3"]`，函数返回 `True`，stderr 却明确声称末次失败。

已确认当前四套分母为 **138 / 9 / 11 / 18**；正常空账不会额外自检或误报，所列 H1 放宽被 `_boundary_ok` 阻断，同门多参数失败仍可判 KILLED。当前 14 种 reconcile 坏法均非零，两份合成验伪锚均通过。

BLOCKER=0 HIGH=0 MEDIUM=3 LOW=1


