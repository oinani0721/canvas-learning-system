> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r6.md)"`
> 审查绑定: `0e7d7ee7`（提交时 HEAD；B0 H0 M4 L4 —— 八条全部整改并另起 round-7，故本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

绑定 `0e7d7ee7`；仅作只读检查与内存复现，未修改文件、运行 pytest 或连接数据库。

- **MEDIUM** AST 分母仍漏算切片增删，可让部分结果冒充全量 — [mutation_verdict_reconcile.py:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:163) — 在九条字面列表后添加 `MUTATIONS[:0]=[9]`，实际已有十条，但配合真实九条 tee，对账仍输出四数皆为九并通过；`__imul__`、`__delitem__` 也未被拦截。

- **MEDIUM** r5 M-2 的漏报仍存在于逐条还原入口 — [g33_mutation_gates.py:533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:533) — 用真实 `RestoreGuard` 复现“逐条还原收到信号并首次抛 OSError→守卫重试成功→末次还原成功”，实得 `130`、空失败账、空 stderr、零次 `verify`；默认 `final=False` 的调用在记账前直接重抛，新测试只覆盖了 `final=True`。

- **MEDIUM** `_swallowed_cause` 只沿优先链前进，会漏掉同时存在的 context — [g33_mutation_gates.py:414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:414) — 在处理 OSError 时执行 `raise SystemExit(130) from SystemExit(130)`，函数返回 `None`，末次包装将其视为干净退出，不报告也不调用 `verify`。

- **MEDIUM** H1 仍会把路径中的 `::[` 误认成参数段，误伤合法普通 Python 门 — [mutation_kill_identity.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:228) — pytest 对象生成的 nodeid `tests/foo::[x]/test_gate.py::test_x` 配合 reason `AssertionError: [1, 2]`，旧版判 KILLED，新版误加“整行无 reason”候选而判 HARNESS-ERROR。

- **LOW** “末次失败升到 3”的 docstring 缺少进入时已在退出流程中的条件 — [g33_mutation_gates.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:487) — 令 `exiting()` 始终为 False，末次回调抛 OSError，实际报告后原样重抛，并不升为 `SystemExit(3)`。

- **LOW** JSON 注释错误声称 `restore_identical` 只看最终 SHA — [g33_mutation_gates.py:886](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:886) — `drift=[]`、`restore_failures=["M3"]` 时，第 720 行计算的 `ok_restore` 为 False，该 JSON 字段同样为 False。

- **LOW** `--show-capture=no` 的说明仍夸大为判据区不含任何被测进程可控字节 — [mutation_kill_identity.py:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:407) — 文件自身第 30–38 行的 `assert r.returncode == 0, r.stderr[:250]` 就能将子进程文字带入异常消息；关闭 Captured 区不会移除这些文字。

- **LOW** stdout 解析文档声称三套形态互异，实际只有两组 — [mutation_verdict_reconcile.py:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:251) — 对照两套真实 tee 与第 261–267 行，g32cb、g32ccr1 共同使用 `_CB_*` 正则。

四套现源码分母确认仍为 **138/9/11/18**；H2、锚检查早退次序及 H1 放宽后的 `_boundary_ok` 兜底未发现新问题。19 层档案的显形记录和前后 SHA 一致，但缺少逐层补丁，不能仅凭档案独立证明每次只拆一层。

BLOCKER=0 HIGH=0 MEDIUM=4 LOW=4
