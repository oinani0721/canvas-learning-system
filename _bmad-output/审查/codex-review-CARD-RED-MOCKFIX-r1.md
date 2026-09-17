> 批次: BATCH-2026-09-11-第十四批 · 车道 T10 · 卡 CARD-RED-MOCKFIX round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-MOCKFIX.md)"`
> 审查绑定: `f6e4f8a1`（送审时 HEAD = f6e4f8a1，审后仅改 _bmad-output，代码树仍绑定）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，按字段各自找行并括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(L2) / `model: gpt-6-astra`(L5) / `reasoning effort: ultra`(L9)

---

**七处补桩可接受，未发现本卡引入的代码缺陷。** 以下有 2 条 LOW，分别涉及既有断言覆盖和归因表述。已核对 HEAD 与三文件内容对应 `f6e4f8a1`；本次仅静态检查、复算保存的日志，未运行测试或连接服务。

BLOCKER：该级别 0 条。HIGH：该级别 0 条。MEDIUM：该级别 0 条。

0. **`[]` 没有预先满足现有业务断言；非空对照确有一处敏感断言。**  
   nodeid：`tests/unit/test_story_30_11_batch_parallel.py::TestBatchNeo4jDegradation::test_neo4j_unavailable_still_processes_to_memory`。其 [test_story_30_11_batch_parallel.py:401](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_30_11_batch_parallel.py:401) 的 `len(_episodes) >= 1`，会被一条成功恢复的历史记录提前满足，失去验证本批次落内存的能力。**本次选择 `[]` 正好避免该问题。**其余内存断言按本批次 ID 或 `canvas_path` 筛选，普通 recovered 条目不会预先满足它们。  
   自验：对照生产 `memory_service.py:413–424` 构造恢复条目，在批处理前求值该长度断言。

   自述“逐字节等价”只能限定为 `_episodes` 仍为空；完整初始化状态并不等价，因为新桩会抵达 `memory_service.py:430`，设置 `_episodes_recovered=True`。指定批处理函数不读取该标志。

1. **未发现其他直接 Neo4j 异步漏桩。**  
   指定生产片段直接 await 的子属性仅为 `initialize:281`、`get_all_recent_episodes:384`、`record_episode:1393`。Semaphore fixture 虽未设置 `record_episode`，其唯一使用用例已在 [test_story_30_11_batch_parallel.py:313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_30_11_batch_parallel.py:313) 补好后才调用批处理。  
   自验：逐项对照这三个 await 与 fixture、测试体赋值；范围外辅助函数的传递调用未作保证。

2. **写侧降级与恢复桩正交的定性成立，但有一项既有覆盖不足。**  
   恢复段不读 `stats`；写入分支由 `memory_service.py:1384–1386` 控制。保存的三个 flip 负控也显示，将 `initialized=False` 改成 `True` 后，均在 `record_episode.assert_not_called()` 失败。

   **LOW-1 — 两条“仍落内存”用例没有直接验证内存内容。**  
   [test_memory_service_batch.py:167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_memory_service_batch.py:167) 与 [test_story_30_13_batch_idempotency.py:334](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_30_13_batch_idempotency.py:334) 仅检查返回计数及未调用 Neo4j，不能独立证明事件进入 `_episodes`。这是既有弱点，本次 `[]` 没有引入或放大它。  
   自验：静态假设生产 `:1359` 的内存追加缺失、其余计数保持执行，这两组断言仍可通过。

3. **未发现过度修法。**  
   指定 diff 仅增加七行 `AsyncMock(return_value=[])` 和说明注释；没有整体替换 `MagicMock`、放宽断言或改变 skip 标记。七处覆盖为：第一文件 `:31`，30.11 文件 `:37/:154/:276/:356/:421`，30.13 文件 `:29`。  
   自验：重读指定的 `08100483..f6e4f8a1` diff 即可逐处计数。

4. **本次“只有 `<`”判据没有静默失效，但不能只数符号。**  
   从原始目录日志重新提取失败身份后，与保存的 nodeids 一致：基线 **64** 条、第二轮 **37** 条，删除恰为本卡 **27** 条，新增 **0** 条。nodeids 无重复、ANSI 或 CR，路径前缀一致；重算 diff 与 [diff-base-close2.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-red-mockfix/diff-base-close2.txt:1) 完全一致。  
   自验：同时核对原始日志的 `FAILED/ERROR` 总数、提取集合及双向差集；仅检查零个 `>` 无法防止输入提取为空或不完整。

   自述第 5、6 条也获日志支持：配置用例前后均 PASSED；三文件从 **27 ERROR＋1 PASSED** 变为 **28 PASSED**。

5. **未误改 conftest，也未引入 autouse。**  
   指定 diff 的变更路径只有这三个测试文件，三文件均无 `autouse`。  
   自验：检查 diff 路径及 fixture 装饰器即可。

6. **LOW-2 — “与本卡无直接关系”有支持，但 W4 偶发原因尚未证实。**  
   [unit-close-20260914T200513.txt:384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-red-mockfix/unit-close-20260914T200513.txt:384) 明确记录了到 `::1:7691` 的连接尝试被拦截；第二轮未复现，不能据此称为哨兵误报。实际执行日志中 candidate 确实先于本卡三文件，加上新增赋值仅位于后续 fixture 函数体内，支持排除这些 fixture 执行造成的直接污染。**精确收集序号 `670/2899/4341/4370` 没有对应原始证据，无法独立确认。**  
   自验：对照首轮 `:383–410`、第二轮 candidate 结果及两轮执行顺序；结论宜限定为“偶发连接尝试被正确拦截，与本卡改动无直接因果的证据较强，具体原因未确认”。

**计数汇总：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2；其中本卡新增代码缺陷 0。**
