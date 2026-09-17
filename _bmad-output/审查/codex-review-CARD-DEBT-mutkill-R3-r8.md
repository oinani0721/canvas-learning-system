> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-8
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r8.md)"`
> 审查绑定: `7ae2c543`（提交时 HEAD；B0 H1 M4 L4 —— 本轮全部整改并另起 round-9，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 **`7ae2c543`**：尚未收口。以下基于只读检查、纯内存复现及前后 SHA 对照；未运行 pytest、未修改文件、未连接数据库。

### HIGH

- **HIGH H1 最新整改重新引入假 KILLED** — [mutation_kill_identity.py:327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:327) — 将失败函数导出为 `globals()["test_x[case] - EXPECT"]`，摘要为 `FAILED tests/gate.py::test_x[case] - EXPECT - AssertionError: OTHER`；目标为 `…::test_x`、期望消息为 `EXPECT` 时，名字中的文本被误作 reason：同输入在 `aea80a63` 返回 `HARNESS-ERROR`，当前返回 `KILLED`，括号守卫没有挡住。该动态名称的收集和按基础名称选中，可由 [pytest 9.0.2 收集源码](https://github.com/pytest-dev/pytest/blob/9.0.2/src/_pytest/python.py#L390)及[选择源码](https://github.com/pytest-dev/pytest/blob/9.0.2/src/_pytest/main.py#L932)确认。

### MEDIUM

- **MEDIUM AST 白名单仍允许变异分母静默少算** — [mutation_verdict_reconcile.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:192) — 源码为 `MUTATIONS=[1,2,3]; MUTATIONS.__class__.__imul__(MUTATIONS,2)` 时，实际长度为 **6**，AST 返回 **3**；`__class__` 被放行，外层调用漏检，别名调用也能绕过。

- **MEDIUM 逐条正则会把真实诊断内容重复计为裁决** — [mutation_verdict_reconcile.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:239) — 断言消息含 `diagnostic ⇒ KILLED`、期望消息不命中时，真实裁决返回 `SURVIVED` 并在 why 中保留该消息；一条 `⇒ SURVIVED (...⇒ KILLED...)` 被数成两条，合法聚合因此对账失败。

- **MEDIUM JSON 中显式损坏的逐条字段被降级为“未核”并放行** — [mutation_verdict_reconcile.py:368](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:368) — 保留合法六档及 `total=18`，把 `results` 改为 `"broken"` 或 `{}`，`reconcile_one()` 仍返回空问题列表并打印 ✓；错误类型不应与字段缺失合并处理。

- **MEDIUM 新增补偿篡改单测没有覆盖真正的拒绝分支** — [test_mutation_kill_identity_r3.py:976](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/tests/unit/test_mutation_kill_identity_r3.py:976) — 删除 `reconcile_one()` 的聚合与逐条比较，现有用例仍只断言解析结果不同；静态调用检查确认，本测试文件没有调用 `reconcile_one()` 或 `main()`，因此这层失效不会显形。

### LOW

- **LOW 还原日志仍把外层异常归因给还原** — [g33_mutation_gates.py:470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:470) — 外层 `TimeoutError` 展开、还原成功且自检返回 `[]` 时，标题虽写“未必来自还原本身”，后缀仍写“本轮还原报过错”。

- **LOW docstring 仍声称候选判据采用并集** — [mutation_kill_identity.py:288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:288) — 对照第 327 行，实际只用 `_nodeid_shaped`，这里及第 237、311 行仍宣称“方括号成对 ∪ nodeid 形”。

- **LOW 现行开关说明仍要求裸 `-rf`** — [mutation_kill_identity.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:73) — 按该“配套硬约束”配置会再次遗漏 ERROR，与新增 `-rfE` 契约冲突。

- **LOW 重复声明同一套会夸大核验套数** — [mutation_verdict_reconcile.py:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:452) — 使用 `--expect g33,g33` 和一份合法输入，返回 0，并把同一来源重复核验说成“2 套”。

**其余重点核对：**`-rfE` 未见需要撤回的反向回归；同门多条消息均命中的失败仍可 KILLED，混入无法配对的 ERROR 后降为 HARNESS-ERROR 有依据。首次干净信号保 130、末次新失败自检后升 3 的路径成立。缺少逐条记录可以明确降级为仅核聚合，但不能视为完整五项通过。补充 `m1b` 本体用例的做法恰当；指定负控日志的前后 SHA 相同，但较早 SHA 的存档不能证明当前新增比较层已受保护。

BLOCKER=0 HIGH=1 MEDIUM=4 LOW=4
