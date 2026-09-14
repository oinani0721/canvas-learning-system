> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r2.md)"`
> 审查绑定: `767f4b6a`（提交时 HEAD；本轮报出 1 HIGH + 3 MEDIUM，已全部整改并另起 round-3，故本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核绑定 `767f4b6a`，发现以下四条；均以只读探针复现，未运行 pytest、修改文件或连接数据库。

- **HIGH 参数 ID 内的 `::` 被误当结构分隔，重新造成假 KILLED** — [mutation_kill_identity.py:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:209) — 输入 `FAILED tests/gate.py::test_target[case] - EXPECT[x :: y]] - AssertionError: other`，位置行也只含 `other`，以基础门名、`expect_msg="EXPECT"`、`require_gate_file=True` 裁决，实得 KILLED；真实参数读法被漏掉，截断 nodeid 却通过 `_boundary_ok`。同输入在 `223beed7` 被拒绝，确认是本轮整改引入的回归。

- **MEDIUM `guard_exit` 将还原失败的 131 也认作正常信号退出，跳过末次 SHA 自检** — [g33_mutation_gates.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:461) — 末次还原的 critical 区登记 SIGINT，再让真实 `RestoreGuard` 的还原重试抛 OSError，实得退出码 131、`verify()` 调用零次；守卫原有失败日志仍在，但本卡承诺的末次逐字节自检缺失。

- **MEDIUM stdout 计数仍接受非法数字前缀，非整数可假通过对账** — [mutation_verdict_reconcile.py:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:140)（125 行同型） — 将合法 g32b 样本的 `SURVIVED: 0` 改成 `SURVIVED: 0.5`，正则仍取到整数 0，真实 reconcile CLI 返回 rc=0、四数均为 6；`_nonneg_int` 未覆盖此输入路径。

- **MEDIUM JSON 重复键仍被后值静默覆盖，冲突计数与分母可假通过** — [mutation_verdict_reconcile.py:215](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:215) — 将 g33 样本改成 `"SURVIVED":5,"SURVIVED":0`，真实 CLI 仍返回 rc=0、四数均为 18；重复 `"total":5,"total":18` 同样通过。

H2、M①未发现新增问题；合法整数 `total`、完整真实 tee 的逐条进度行均未见误伤，AST 分母确实拦截 5/5/5。补充直接测试隔离 m1b 冗余层的做法合理，但现有 11 层负控未覆盖上述组合。

BLOCKER=0 HIGH=1 MEDIUM=3 LOW=0
