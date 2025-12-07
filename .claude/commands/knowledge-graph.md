---
name: knowledge-graph
description: Enable Graphiti-based time-aware knowledge graph memory system
---

# Graphiti Knowledge Graph System

## Metadata
- **Command**: /knowledge-graph
- **Description**: Enable Graphiti-based time-aware knowledge graph memory system
- **Bmad Pattern**: Persistent memory with semantic relationships
- **Keywords**: *graph, *memory, *knowledge

## Usage

### Graph Operations
```bash
/knowledge-graph           # Show knowledge graph status
/knowledge-graph *enable   # Enable knowledge graph features
/knowledge-graph search    # Search concepts in graph
/knowledge-graph visualize # Show learning relationships
```

### Memory Management
```bash
/knowledge-graph export    # Export graph data
/knowledge-graph import    # Import graph data
/knowledge-graph backup    # Backup knowledge graph
/knowledge-graph reset     # Clear graph data
```

## Implementation

基于Graphiti的时间感知知识图谱系统，为每个学习会话创建持久记忆痕迹。

**核心技术**: Graphiti + Neo4j (Trust Score: 8.2/10)

**智能记忆**:
- 自动关联: Canvas节点间智能语义关联
- 时间感知: 记录学习时间线和遗忘曲线
- 语义搜索: 基于向量化概念的智能检索
- 学习分析: 个人知识图谱可视化

**数据模型**:
```python
@dataclass
class KnowledgeNode:
    concept: str
    embedding: List[float]
    timestamp: datetime
    mastery_level: float
    relationships: List[str]

@dataclass
class LearningEpisode:
    session_id: str
    concepts: List[str]
    duration: int
    performance_score: float
```

**智能功能**:
- 概念推荐: 基于关联度的相关概念推荐
- 学习路径: 智能规划最优学习顺序
- 知识检测: 识别知识盲区和薄弱环节
- 复习提醒: 基于遗忘曲线的智能复习

**查询性能**:
- 概念搜索: <0.3秒
- 关系查询: <0.5秒
- 路径分析: <1.0秒
- 推荐生成: <0.8秒

**数据安全**:
- 本地存储: Neo4j本地数据库
- 数据加密: 敏感信息加密存储
- 备份恢复: 自动备份和恢复机制
- 隐私保护: 本地处理，数据不上传

为Canvas学习提供持久化智能记忆基础。
