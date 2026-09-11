> 批次: BATCH-2026-09-07-第十三批 · 车道 U1 `card-u1-pyright-svc` · 卡 CARD-PYRIGHT-DEBT-services round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-services-r4.md)"`
> 审查绑定: `8dcfac8e`（阶段 1 最终代码 HEAD；此后只改 `_bmad-output`，`git diff --stat 8dcfac8e HEAD -- . ':(exclude)_bmad-output'` 为空 = 仍绑定）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

本次结论绑定 **`8dcfac8e`**。复核期间 HEAD 已推进到 `5dc6a72a`，后续提交不包含在本结论内。

**BLOCKER**

该节无发现。

**HIGH**

该节无发现。

**MEDIUM**

该节无发现。

本轮 **6 处运行时代码修改均正确恢复基线行为**：

- `conversation_distiller.py:322`：恢复 `AttributeError`，消息为 `'NoneType' object has no attribute 'strip'`。移除类型层 `cast` 后，整个 `_llm_distill` 的 AST 与基线一致。
- `signal_registry.py:112/:151/:188/:229/:269`：全部恢复原除法运算。五类各验证 8 组输入，返回值或异常类型、消息均与基线一致；三个 calibration 类的 `preload_from_calibration_records("x_count", [])` 路径也独立复现通过。

剩余 **20 个 assert**，按现有生产入口和对象构造约束，未发现其他已证实的可观察行为差异：

| 文件与当前行号 | 数量 | 保留依据 |
|---|---:|---|
| `agent_routing_engine.py:577` | 1 | 两类异常均被捕获，固定日志、返回值相同 |
| `agent_selector.py:296` | 1 | 构造时将 `previous_agents=None` 归一为 `[]` |
| `alert_manager.py:286` | 1 | 创建 PENDING 状态时同时写入 `pending_since` |
| `graphiti_belief_service.py:207/:300` | 2 | 现有任务入口补齐时间；历史边反序列化验证必填时间 |
| `extraction_validator.py:485/:490/:495` | 3 | 无分组、无 HAVING 的 `COUNT(*)` 成功执行恒有一行 |
| `retrieval_reranker.py:232` | 1 | 前置检查已对任何缺失分数返回 |
| `rollback_service.py:188/:207/:224/:253/:272/:302/:325/:368/:406` | 9 | 均受组件初始化门约束 |
| `wikilink_graph_service.py:135/:156` | 2 | 同步方法前置排除空图，闭包不逃逸 |

其中 `graphiti_belief_service.py:207` 的依据是实际调用方 `:356–358` 补齐时间；**`datetime` 注解本身并不提供运行时验证**。

**LOW**

1. **新增两处注释错误**——[signal_registry.py:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/signal_registry.py:109)、同文件 `:148`。

   BKT、FSRS 两类没有 `preload_from_calibration_records`，实际生产方法是 `preload(concept)`。复制另外三个类的实证说明，错误描述了本类写入路径。修改后的运算正确，定级为注释问题；应更正这两处说明。

2. **累计行为例外仍待接受**——[rag_service.py:51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/rag_service.py:51)。

   基线成功导入时绑定 `CanvasRAGConfig`；当前成功路径不再绑定，仅异常分支设置为 `None`。因此旧模块属性访问或重导出导入会失效。未发现仓库内实际消费者，维持 LOW；这是累计变化，须由主 session **明确接受取消该重导出**，仅登记移交尚不等于接受。

五处 handler 注释校正均准确；保留的 autoscore、question_generator、scoring_faithfulness 消息去向说明也与代码相符。本轮未发现新死 import、新 `Any` 放宽或无关格式漂移。指定 SHA 的六文件语法编译、Ruff `F401/F821`、`git diff --check` 均通过。全程只读，未连接数据库，未运行 integration/e2e，也未重判你排除的类型错误。

**总判：本轮 BLOCKER=0、HIGH=0；阶段 1 可条件收尾，正式关闭前应更正两处 LOW 注释，并由主 session 明确接受 `CanvasRAGConfig` 重导出变化。**
