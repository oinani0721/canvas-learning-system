> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r7.md)"`
> 审查绑定: `aea80a63`（提交时 HEAD；B0 H0 M3 L6 —— 九条全部整改并另起 round-8，故本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

**`aea80a63` 尚未达到 MEDIUM 清零。** 以下结论经只读代码核对及内存探针复现；未运行 pytest、变异 harness 或连接数据库，文件未修改。

- **MEDIUM 普通 reason 中的 ` - ` 仍会制造非法候选，导致唯一摘要被判二义** — [mutation_kill_identity.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:307) — 输入 `FAILED tests/gate.py::test_x - AssertionError: expected - actual`，第二切点左侧虽不符合 `_nodeid_shaped`，仍因方括号 `0 == 0` 入选，最终返回 `HARNESS-ERROR`；这是本卡尚未收口的既有问题。

- **MEDIUM 逐条还原路径未执行 SHA 自检，却打印“未检出漂移”** — [g33_mutation_gates.py:671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:671)、[450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:450) — 逐条还原首次 `OSError`、收到 SIGINT、守卫重试成功、末次成功时，实测 `rc=130 / restore=3 / verify=0 / restore_failures=[]`；逐条调用遗漏 `verify`，而报告把 `None` 当成空漂移列表。

- **MEDIUM AST 分母漏拦直接列表改动，部分表仍能冒充全量** — [mutation_verdict_reconcile.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:100) — 内存源码 `MUTATIONS=[1,2,3]; MUTATIONS.__imul__(2)` 实际长度为 6，AST 返回 3，配合 3/3/3 JSON 对账仍通过；`__delitem__` 也漏检。

- **LOW 非还原异常被信号盖住时，会误报“本轮还原报过错”** — [g33_mutation_gates.py:458](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:458) — 让门运行的 `TimeoutExpired` 正在展开、末次还原期间收到 SIGINT，三次还原全部成功仍出现该文案；忽略 `__suppress_context__` 的代价已声明，但不能据此把异常归因于还原。

- **LOW 末次调用点仍宣称失败必升 rc=3，遗漏 `was_exiting` 前置条件** — [g33_mutation_gates.py:716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:716) — `final=True`、`exiting()` 恒 False、还原抛 `OSError` 时，实际自检后原样重抛；函数 docstring 已修，此处注释未同步。

- **LOW 模块说明仍宣称关闭 captured 区后，整个判据面没有被测进程可控字节** — [mutation_kill_identity.py:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:50) — `assert r.returncode == 0, r.stderr[:250]` 仍能把子进程文本带入异常消息与摘要；与已修正的 `judge_flags()` 说明矛盾。

- **LOW 模块说明声称逐次检查 COLUMNS，实际没有宽度或截断检查** — [mutation_kill_identity.py:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:71) — 保留位置行、提供无 reason 的 FAILED 摘要，`judge_surface_missing(..., need_location=True)` 返回 `None`，消息不命中则判 `SURVIVED`。

- **LOW g33 注释仍将消息判据写成只取 `E ` 行** — [g33_mutation_gates.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:73) — 仅 `E ` 行含 EXPECT、摘要 reason 不含 EXPECT 时仍判 `SURVIVED`；实际裁决取摘要 reason，`E ` 行仅用于诊断记录。

- **LOW reconcile 注释夸大了三套共有的输出格式** — [mutation_verdict_reconcile.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:65) — g32b 合成样本的实际行是 `KILLED-UNBOUND (说明): 0`，并非所称的 `档名: N`；代码也为它单列了正则。

核验补充：同门多条参数化失败仍可判 KILLED；括号不成对的放宽路径仍被 `_boundary_ok` 拦住；14 份真实 stdout 均解析正常。`m1b` 补直接用例合理，但清单内最新负控存档仍绑定 `34473ebd`，不能据此确认当前 SHA 的“22 层”覆盖。

BLOCKER=0 HIGH=0 MEDIUM=3 LOW=6


