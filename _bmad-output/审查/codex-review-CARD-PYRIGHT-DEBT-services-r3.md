> 批次: BATCH-2026-09-07-第十三批 · 车道 U1 `card-u1-pyright-svc` · 卡 CARD-PYRIGHT-DEBT-services round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-services-r3.md)"`
> 审查绑定: `82d15aac`（本轮不绑最终 HEAD —— 送审后又按其 MEDIUM 整改，见 r4）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

已绑定 `82d15aac1b7931bc250c10c356b4d6a8fec4b8e0`。**本轮实际是 10 处 assert、7 个文件；全部 cast 替换正确，原异常类型和消息均恢复。** 去除 cast 后，这 10 个完整函数的 AST 与基线一致；纯内存异常演算也一致。但 MEDIUM 尚未闭环。

**BLOCKER**

该节无发现。

**HIGH**

该节无发现。

**MEDIUM**

1. **异常消息仍有确定漏项。** [conversation_distiller.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/conversation_distiller.py:319)：`content=None` 仍将带消息的 `AttributeError` 改成空消息 `AssertionError`，同文件调用者在 `:164–166` 捕获并格式化进日志，属于已证实的可观察变化。

   日志仍会从：
   ```
   [Story 3.8] Distillation failed: 'NoneType' object has no attribute 'strip'
   ```
   变成：
   ```
   [Story 3.8] Distillation failed:
   ```
   回退返回值没有因此改变，但日志消息丢失尚未修复。

2. **剩余 assert 的等价性不能仅靠登记移交关闭。** [signal_registry.py:187](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/signal_registry.py:187)，以及 `:228/:268`：真实类方法可以产生 `count=None`，因此“计数键恒写 int”的注释不是无条件成立，新增异常类型变化可复现。

   对三个对应类分别执行：
   ```python
   sig = C()
   sig.preload_from_calibration_records("x_count", [])
   sig.get_reliability("x")
   ```
   基线均为带消息的除法 `TypeError`，目标均为 `AssertionError("")`。缓存键碰撞是基线缺陷；本卡新增的是异常类型和消息变化，未证明这是线上实际触发场景。

   审计方法除了漏掉上述调用者 handler，还会漏掉 `logger.exception()`、`exc_info=True`、裸重抛、异常链、对象传递或存储后的格式化，以及上下文管理器退出处理。**这些是方法边界，并非断言当前代码全部存在这些问题。**

**LOW**

1. **新增两处显式类型放宽。** [canvas_projection_sync.py:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/canvas_projection_sync.py:162)、[rag_service.py:323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/rag_service.py:323)：`cast(Any, ...)` 保持运行行为，但让对应使用点绕过静态成员及调用约束；本轮未核验旧推断强度，不声称丢失了某条已确认有效的诊断。

2. **新注释和证据分类仍不准确。** [exam_service_ext.py:382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/exam_service_ext.py:382)：异常消息只进入日志，回退文案仅由 `level` 决定；类似误述还有 `autoscore.py:391`、`error_classifier.py:287/:356`。`rag_service.py:321` 则实际是日志加带 cause 的重抛，并非返回字段。[审计证据:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/审查/evidence-pyright-svc/assert-message-leak-audit-20260908T081412.txt:8)及其 `:10–14` 的“返回值+日志”分类也应校正。

3. **送审计数需更正。** [审计证据:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/审查/evidence-pyright-svc/assert-message-leak-audit-20260908T081412.txt:7)开始列出的 12 个组合对应 **10 个独立 assert**；当前剩余 **26 个，其中 25 个不在函数内的词法 try 中**。[agent_routing_engine.py:577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/agent_routing_engine.py:577)位于 `try/except Exception` 内。数字错误来自送审说明，证据文件自身没有写“9 处”。

4. **`CanvasRAGConfig` 属性面变化继续保留。** [rag_service.py:51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/rag_service.py:51)：成功导入时该模块属性消失，失败分支 `:75/:83` 却仍定义它；没有仓内消费者不能证明属性面未变。可以作为明确的 LOW 待主 session 裁定，但不能算严格零行为变化已满足；恢复显式重导出属于保留既有行为。

关于两项移交判断：**可以登记为待裁定事项，不能仅凭登记就关闭纯类型卡的等价性要求。** 已证明不可达或局部等价的 assert 可以保留；已证实的差异应在本卡恢复，或由主 session 明确接受行为例外。

副作用维度也有具体条件性例子：[graphiti_belief_service.py:207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/graphiti_belief_service.py:207)在 `occurred_at=None` 时提前失败，基线会继续到索引初始化及旧边处理。该输入违反 `datetime` 注解，尚未证明实际调用者会传入，因此不据此定为正常输入回归或升级 HIGH。

未发现本轮新增死 import；`rag_service` 单行调用保持同一表达式。未运行 Ruff、Pyright 或服务测试，不将 AST 验证表述为格式检查通过；此前 LOW-1 的追加更正文件不在指定读取面内，本轮未核验。全程未修改文件、连接数据库或运行集成/e2e。

**总判：本轮 BLOCKER=0、HIGH=0；MEDIUM 仍未闭环。**
