> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-DEBT-mutkill-R3 round-11
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutkill-R3-r11.md)"`
> 审查绑定: `de999779`（提交时 HEAD；B0 H2 M3 L0 —— 本轮全部整改并另起 round-12，故**不绑最终 HEAD**）
> 会话头自证（抄 .stderr 含版本/model/reasoning 三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查固定于 `de999779`；以下均以纯内存探针复现，未运行 pytest、未写文件。后续测试提交未纳入。

- **HIGH 位置与消息仍能跨失败实例拼成假 KILLED** — [mutation_kill_identity.py:1006](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1006) — 第一条沿用 r10 长名摘要 `test_x[<1100a>] - EXPECT]tail`，实际门内消息为 OTHER；第二条正常参数化失败的消息为 EXPECT、位置在门外 helper；弱位置路径从第一条借位置、第二条借消息，两条摘要又都被解析为消息命中，最终仍判 KILLED。

- **HIGH 切分仍能把另一道门误认成目标门，消息交叉核无法证明门身份** — [mutation_kill_identity.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:341) — 声明 `test_x`，实际动态测试名为 `test_x - suffix]tail`，摘要追加真实 reason `AssertionError: EXPECT`、门内位置消息也为 EXPECT；完整实际 nodeid 不命中目标门，但解析器截成 `test_x`，最终判 KILLED。

- **MEDIUM 两侧均未命中消息时，正常 SURVIVED 被改判 HARNESS-ERROR** — [mutation_kill_identity.py:1005](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1005) — 声明 `expect_msg="EXPECT"`，摘要与门内位置行均为 `AssertionError: OTHER`；交叉核先于摘要命中判断执行，返回 HARNESS-ERROR，并错误声称“只在摘要区命中”。

- **MEDIUM 白名单方法当场调用后仍可取回原列表，独立分母静默少算** — [mutation_verdict_reconcile.py:207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:207) — 对源码 `MUTATIONS=[1,2,3]` 加上 `MUTATIONS.__iter__().__reduce__()[1][0].append(4)`，原 AST 计数器返回 **3**，实际长度为 **4**；外层属性链以调用表达式为根，逃过检查。

- **MEDIUM JSON 额外裁决档被静默忽略，冲突计数仍通过对账** — [mutation_verdict_reconcile.py:398](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_verdict_reconcile.py:398) — 在合法 g33 JSON 中新增 `"UNEXPECTED-VERDICT":1`，保留六档合计及逐条记录各 18；原始计数和为 **19**，解析后却按 **18** 与 AST 分母通过比较。

BLOCKER=0 HIGH=2 MEDIUM=3 LOW=0
