> 批次: BATCH-2026-09-07-第十三批 · 车道 U1 `card-u1-pyright-svc` · 卡 CARD-PYRIGHT-DEBT-services round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-services-r1.md)"`
> 审查绑定: `2fa89589`（阶段 1 HEAD，**不绑合并态** —— 卡文 §四明示阶段 1 这一轮可不绑最终 HEAD）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：本轮暂不通过。** 固定审查 `da690bf8..2fa89589`，发现真实类型错误被掩盖，以及一处断言改变既有降级路径。本次范围内未发现 **BLOCKER**。

以下行号均对应 `2fa89589`。

- **HIGH — [batch_orchestrator.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/batch_orchestrator.py:503)、`:565`：两个 cast 掩盖真实的取消异常。**  
  `CancelledError` 属于 `BaseException`，不被前面的 `isinstance(result, Exception)` 筛掉；`gather(return_exceptions=True)` 确实会将它放进结果列表。Python **3.11.15** 实证成立：第一处会把取消异常当业务结果返回，第二处随后访问 `result.success` 会抛 `AttributeError`。这是**本卡掩盖的既有缺陷**，不能算正确窄化；注释只考虑 `KeyboardInterrupt/SystemExit`，遗漏了取消异常。

- **MEDIUM — [error_extractor.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/error_extractor.py:255)：断言改变了既有异常处理分支。**  
  `content=None` 时，原来的 `None.strip()` 抛 `AttributeError`，被本方法 `:273` 捕获后正常返回 `[]`；现在 `AssertionError` 越过该捕获块向外传播。公开入口 `:142` 仍有兜底，最终也返回 `[]`，因此不是接口必然崩溃，但辅助方法契约、控制流和日志确实改变，违反本卡约束。

- **MEDIUM — [intelligent_parallel_service.py:649](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/intelligent_parallel_service.py:649)：普通字符串被无依据地声明为枚举实例。**  
  `retry_single_node()` 接受 `agent_type: str`，此处没有转换或验证；“`AgentType` 继承 `str`”不能反向证明普通字符串属于 `AgentType`，cast 后实际对象仍是字符串。读取范围内未核实下游是否兼容字符串，所以不声称必然运行失败，但“值必在 cast 目标类型内”的依据不成立。

- **MEDIUM — [frontmatter_signals.py:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/frontmatter_signals.py:66)、[targeting_material_service.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/targeting_material_service.py:82)：改成 `Any` 隐藏了未验证的可迭代性要求。**  
  YAML 映射的值可以是标量；例如 `tips: 1` 或 `error_candidates: 1`，后面的循环仍会抛 `TypeError`。这不是本卡新增的运行故障，但相关诊断被类型放宽消掉了，应像其他真缺陷一样明确登记，不能作为已经修好的类型问题。

- **LOW — [rag_service.py:51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/rag_service.py:51)：模块属性面确实发生变化。**  
  成功导入时不再有 `rag_service.CanvasRAGConfig`，但异常分支 `:75/:83` 仍将它定义为 `None`。这是可确认的属性面变化；没有外部消费者证据，因此不升级为已证实的调用回归。

- **LOW — [验收单:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-services-2026-09-08.md:252)：修复数量口径需要校正。**  
  AST 实际只有 **15 个 cast 调用＝12 个 ModelResponse＋2 个 gather＋1 个 AgentType**；23 次文本匹配包含了8处注释。固定 diff 实际为 **354 insertions / 123 deletions**；新增 `TYPE_CHECKING` 的文件是11个，也与表中5个不符。

其余逐项核对如下。

1. **litellm cast：该节无发现。**  
   12处 cast 对应的全部调用分支均未传 `stream=True`，也没有 `*args/**kwargs` 透传。上述 gather 和 Enum 两类不能沿用这个结论。

2. **其余 assert：未发现另一处已证实的正常路径回归。**  
   38处已逐项检查。三个重点位置的结论是：
   
   - `graphiti_belief_service.py:207`：对合法 `datetime` 入参，该节无发现；非法 `None` 下断言会提前于索引、旧边保存等操作失败，不能声称非法输入下副作用也完全等价。
   - **LOW — `graphiti_belief_service.py:298`**：“返回 None 时排序同样 TypeError”的注释不普遍成立，单元素 `sort/max` 不需要比较键。不过尚未证明真实 `EntityEdge` 能以两个时间字段均为 `None` 的状态进入此处，因此不判定生产回归。
   - `wikilink_graph_service.py:156`：该节无发现。外层方法同步、无 `await`，闭包不逃逸，现有调用链没有证明守卫之后 `_graph` 能变成 `None`。

3. **考试方法声明：该节无发现，11/11 签名一致。**  
   已比较参数名、顺序、注解、默认值、同步／异步及返回类型；只有排版差异。`get_cognitive_load_message` 为同步方法，其余10个为异步方法。运行期声明块不执行，原有 ext 导入和11个挂载均保留，未发现新引入的 monkeypatch 冲突。  
   `endpoints/exam.py` 两提交 blob 完全相同。受读取边界限制，**未独立核实测试中的“3个文件、0个 patch 站点”**。

4. **12条 ignore：行级、具体 rule 的形式，该节无发现。**  
   第1条保留副作用导入的理由成立。第9—12条原有守卫保留，但 `hasattr` 本身不能证明方法可调用、可等待或返回值类型正确，不能据此作绝对安全保证。可信的接口／属性声明可以减少这些 ignore，但必须先核实实际实现；相关共享文件本轮又禁止修改，保留有范围依据。  
   缺失成员、字段改名、`src.rollback` 缺失等事实依赖范围外的模型和包定义，**本轮不能独立背书这些存在性断言**。

5. **删除 import 的模块内使用：该节无发现；副作用与外部使用仅能判 PARTIAL。**  
   删除的绑定没有残留直接引用，也未发现按这些名称进行动态读取。`memory_service.py` 已没有 `except neo4j.exceptions.*`，其历史说明与现状一致。  
   但指定读取面不足以证明所有依赖初始化／注册副作用均不存在，也不足以证明外部借道 import 为零。`rag_service` 仍导入其他 `agentic_rag` 名称，因此不能把删除 `CanvasRAGConfig` 等同于删除整个包的初始化。

6. **四个既有真缺陷只标注、另卡修复：范围处置恰当，该节无新增发现。**  
   修复它们都会涉及运行行为，不应混进这张纯类型卡。清理调度问题应单独优先处理：若配置属性确实缺失，异常发生在 `await` 入参求值阶段，捕获后无让出执行权的操作，影响可能是阻塞事件循环。它仍不能因为加了 ignore 就算已修复。

另外两项验收主张需要保留限制：

- **`NEW=0` 不足以证明“任何地方都没有弄红”。** 即使计数准确，也只证明相同分析条件下诊断多重集没有新增键／数量；cast、Any、ignore 隐藏的错误以及运行期回归均不在保证范围内。指定证据文件的末行实际只有 `rc=0`，本轮不能据此独立确认 `421/242/0/179`。
- **六处注解调整：补 Optional 的三处，该节无发现；三处具体类收紧未发现局部矛盾，但外部注入方未获核实。** 因而不能认定“全部调用方均满足新注解”已经完成独立验收。

全程未修改文件、未连接数据库、未运行仓库测试或重跑全量 pyright；取消异常反例使用 Python 3.11 标准库验证。


