# Temporal时序记忆 (业务层记忆 - 学习历程)

**职责范围**:
- ✅ 存储学习事件时间线（拆解时间、评分时间、复习时间）
- ✅ 支持学习进度分析和统计（Epic 14复习系统依赖）
- ✅ 支持学习习惯分析（学习时段、学习频率）

**不存储**:
- ❌ 事件的详细内容（仅存储元数据和时间戳）
- ❌ 知识图谱关系（由Graphiti管理）

**数据示例**:
```json
{
  "event_id": "evt_20250115_143025_001",
  "session_id": "session_20250115_143025",
  "event_type": "decomposition_completed",
  "timestamp": "2025-01-15T14:30:25Z",
  "metadata": {
    "canvas_path": "离散数学.canvas",
    "concept": "逆否命题",
    "question_count": 5
  }
}
```

**何时调用**:
- `store_to_temporal_memory()`: 每次Canvas操作后记录事件

---
