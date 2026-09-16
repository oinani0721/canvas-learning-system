> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-13
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r13.md)"`
> 审查绑定: `e57475e4`（提交时 HEAD；B0 H0 M2 L1 —— 本轮全部整改并另起 round-14，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核 SHA：`e57475e4`。全程只读，未运行 pytest、harness 或连接数据库；当前四套分母仍为 **138/9/11/18**。

- **MEDIUM 多条同门失败全部落在门外时，被误判为 HARNESS-ERROR** — [mutation_kill_identity.py:1034](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1034) — 同一参数化门两条失败、位置均在 helper、消息均为 `boom`，实测返回 HARNESS-ERROR；该守卫遮住了后面的全门外 SURVIVED 分支，此时没有门内位置可借用。

- **MEDIUM 读白名单仍允许传出并修改 MUTATIONS，独立分母可静默少算** — [mutation_verdict_reconcile.py:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:199) — 令 `Sink()[MUTATIONS]` 的 `__getitem__` 追加元素，或重定义 `len` 后调用 `len(MUTATIONS)`，两例均实测 AST=3、运行时=4；下标分支未核实操作数位置，调用分支未核实内建函数绑定。

- **LOW H1 仍把受限候选判据宣称为全部合法读法的穷举** — [mutation_kill_identity.py:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:268) — 对照同文件 :854 已承认测试名可含任意字符，即可看到“全部合法读法”与无空白前缀限制矛盾；本条仅要求收窄声明，剩余身份歧义要靠 `expect_loc`，属 T8-C。

BLOCKER=0 HIGH=0 MEDIUM=2 LOW=1
