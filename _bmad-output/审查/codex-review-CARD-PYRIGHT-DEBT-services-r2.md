> 批次: BATCH-2026-09-07-第十三批 · 车道 U1 `card-u1-pyright-svc` · 卡 CARD-PYRIGHT-DEBT-services round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-services-r2.md)"`
> 审查绑定: `958f20a3`（本轮不绑最终 HEAD —— 送审后又按其 MEDIUM 整改，见 r3/r4）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

复核绑定 **`958f20a3`**。四文件整改的核心处理成立，但累计补丁的 assert 行为等价性仍未闭环。

**BLOCKER**

该节无发现。

**HIGH**

该节无发现。

[batch_orchestrator.py:506](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/batch_orchestrator.py:506) 及同文件 `:569–570`：**ignore 仍抑制真实诊断，运行期取消缺陷仍在**；撤掉 cast 消除了新增的错误窄化保证，原有返回类型和列表注解仍会向下游呈现业务对象类型。

Python 3.14.4 独立实证与新注释一致：被取消的子任务经 `gather(return_exceptions=True)` 返回 `CancelledError`，绕过 `isinstance(..., Exception)`，随后污染结果列表或在 `.success` 抛 `AttributeError`。累计 diff 保留了基线运行行为，因此可以按明确登记的既有债务移交，不重复计作本轮 HIGH；不能称为“类型正确”或“取消问题已修复”。

**MEDIUM**

1. **剩余 assert 已有可观察的返回内容变化，except 覆盖不能证明等价。**  
   [autoscore.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/autoscore.py:310)：`content=None` 时，原来的 `TypeError` 变成空消息的 `AssertionError`，而 `:335–340` 将异常消息写入返回 evidence；这是本卡引入的行为变化，定为 MEDIUM。

   从两版 diff 抽取实际表达式及 handler 返回表达式进行内存验证：

   ```text
   基线：Evidence extraction failed: the JSON object must be str, bytes or bytearray, not NoneType
   当前：Evidence extraction failed:
   ```

   同类位置还有 [question_generator.py:778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/question_generator.py:778) 的 `difficulty_rationale`，以及 [scoring_faithfulness.py:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/scoring_faithfulness.py:269)、同文件 `:351` 对应返回的 `reason`。

   **25 处无 try 也需要逐项审计，不能直接判等价。**例如 [conversation_distiller.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/conversation_distiller.py:319) 在 `content=None` 时向调用方抛出的异常类型已改变；当前同文件调用方虽捕获两者，日志原因仍会变化。反之，有先行 None 检查或可靠非空不变量的位置，不应仅因存在 assert 就报回归。

   对审计方法的结论：

   - 独立 AST 核对当前 **36 处＝11 处位于函数内 try body＋25 处无函数内 try**，未发现当前这批因嵌套、别名 handler 或 `except/else/finally` 归属而漏数。
   - 但“最内层 try＋handler 集合”不足以证明行为等价：还需比较原异常与新异常命中的 handler、外层传播、重抛、返回字段、日志和副作用。
   - 无 try 时还需检查调用方异常契约；有可靠非空不变量才可保留 assert，不能以“原来也会抛异常”替代证明。指定材料没有审计脚本，故不能认证脚本对一般嵌套或别名情形的实现。

**LOW**

1. **验证标题仍把显式抑制写成诊断可见。**  
   [r1-fix-verification-20260908T075315.txt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/审查/evidence-pyright-svc/r1-fix-verification-20260908T075315.txt:10) 写“pyright 仍能看见该缺陷”，下一行却确认被 ignore 挡住；应改为“代码注释保留缺陷说明，诊断被显式抑制”，属于证据措辞错误。

2. **`rag_service` 属性面差异仍未满足严格的纯类型约束。**  
   [rag_service.py:51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/rag_service.py:51)：删除成功导入路径上的 `CanvasRAGConfig` 模块属性，是累计补丁引入的兼容性变化；登记不能证明与基线等价，故保留 LOW。若坚持零运行行为变化，建议保留显式重导出。“全仓无消费者”可降低实际影响，但本次限定读取面未独立验证该声明。

其余整改核对结果：

| 位置及 None 情形 | 基线 | round-1 | `958f20a3` |
|---|---|---|---|
| [error_extractor.py:259](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/error_extractor.py:259) | `AttributeError`，被捕获 | `AssertionError`，逃逸 | `AttributeError`，被捕获 |
| [intelligent_parallel_service.py:293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/intelligent_parallel_service.py:293) | `AttributeError`，逃逸 | `AssertionError`，逃逸 | `AttributeError`，逃逸 |

两处均恢复了基线异常类型和捕获结果。第二处恢复的是**逃逸异常的类型**，并非恢复本地捕获；`:290–291` 的注释宜据此说得更准确。cast 本身不验证非空。

- `AgentType cast → ignore` 处置成立；相关 `AgentType`、`cast` import 已正确清理，未发现本轮新增死 import。
- Graphiti 排序注释已撤掉错误理由；新的论证以 `created_at` 非空模型契约为前提，该依赖定义不在本次读取面。
- YAML `Any` 可以按**已知未修的类型放宽**移交，本卡不必新增 `isinstance` 分支；不能把诊断消失计作输入验证已完成。
- 数量独立重算全部一致：**14 cast、11 个新增 TYPE_CHECKING 文件、36 assert、16 ignore；53 文件，366/124**。

全程只读，未导入项目运行、连接数据库或运行集成/E2E 测试。

**总判：本轮 BLOCKER=0、HIGH=0，两者均为 0；但累计补丁仍有上述 MEDIUM 未闭环。**
