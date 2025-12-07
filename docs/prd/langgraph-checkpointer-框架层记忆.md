# LangGraph Checkpointer (框架层记忆)

**职责范围**:
- ✅ 存储CanvasLearningState对象（Agent执行的中间状态）
- ✅ 支持多轮对话上下文持久化（thread_id维度）
- ✅ 提供回滚能力（通过checkpoint ID和timestamp）
- ✅ 自动管理（LangGraph框架自动调用，开发者无需手动触发）

**不存储**:
- ❌ Canvas文件内容（由write_to_canvas直接写入文件系统）
- ❌ 知识图谱数据（由Graphiti管理）
- ❌ 学习事件时间线（由Temporal记忆管理）
- ❌ 文档向量（由Semantic记忆管理）

**数据示例**:
```json
{
  "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875",
  "thread_id": "canvas_离散数学_session_20250115_143025",
  "timestamp": "2025-01-15T14:30:25Z",
  "state": {
    "session_id": "session_20250115_143025",
    "canvas_path": "Canvas/Math53/离散数学.canvas",
    "current_concept": "逆否命题",
    "last_operation": "decomposition",
    "decomposition_results": ["什么是逆否命题？", "它与原命题有何关系？"],
    "write_history": [...]
  }
}
```

**何时使用**:
- Agent节点执行完毕自动触发（LangGraph框架行为）
- 多轮对话需要恢复上下文时读取（通过thread_id）
- 回滚操作时查询历史checkpoint

---
