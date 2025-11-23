# Epic 10 真实实现待办清单

**创建日期**: 2025-11-04
**优先级**: 中 (可选功能)
**预估工作量**: 3.5-4.5天
**依赖**: Epic 1-5已完成

---

## 📋 执行摘要

Epic 10 (智能并行处理系统) 在文档中被标记为"完成"，但经过完整审计发现**零实现**。本文档提供真实的实现路线图和工作量估算。

**审计报告**: `docs/HONEST_STATUS_REPORT_EPIC10.md`

---

## 🎯 预估工作量

| 阶段 | 工作内容 | 预估时间 | 优先级 |
|------|---------|---------|--------|
| 核心实现 | IntelligentParallelCommandHandler | 2-3天 | 高 |
| 记忆集成 | 三层记忆系统真实调用 | 0.5天 | 高 |
| Canvas修改 | 蓝色节点创建和连接 | 0.5天 | 高 |
| 测试验证 | E2E测试和验证 | 1天 | 高 |
| 文档更新 | Story文件和用户文档 | 0.5天 | 中 |
| **总计** | | **3.5-4.5天** | |

---

## ✅ 必须实现的功能

### 1. IntelligentParallelCommandHandler (核心)

**文件**: `command_handlers/intelligent_parallel_handler.py`

**必需功能**:
- [ ] 创建核心Handler类
- [ ] 实现黄色节点扫描 (color="6")
- [ ] 实现智能分组算法
  - [ ] 基于内容的语义相似度聚类
  - [ ] 基于评分的学习阶段分组
  - [ ] Agent适配推荐引擎
- [ ] 实现Agent调用 (通过Task tool)
  - [ ] clarification-path
  - [ ] comparison-table
  - [ ] memory-anchor
  - [ ] oral-explanation
  - [ ] example-teaching
  - [ ] four-level-explanation
- [ ] 实现文档生成 (调用真实Agent)
- [ ] 实现Canvas文件修改
  - [ ] 添加蓝色AI解释节点
  - [ ] 创建边连接 (黄色→蓝色)
- [ ] 实现错误处理和回滚
- [ ] 实现进度报告和日志

**核心代码框架**:
```python
class IntelligentParallelCommandHandler:
    def __init__(self):
        self.canvas_ops = CanvasJSONOperator()
        self.max_concurrent = 12

    def execute(self, canvas_path, options):
        # 1. 扫描黄色节点
        yellow_nodes = self._scan_yellow_nodes(canvas_path)

        # 2. 智能分组
        task_groups = self._intelligent_grouping(yellow_nodes)

        # 3. 并行执行 (真实Agent调用)
        results = self._execute_parallel(task_groups)

        # 4. 修改Canvas (添加蓝色节点)
        self._update_canvas(canvas_path, results)

        # 5. 存储记忆 (三层系统)
        self._store_to_memory(results)

        return results

    def _intelligent_grouping(self, nodes):
        # 语义相似度聚类
        # Agent推荐引擎
        # 负载均衡
        pass

    def _execute_parallel(self, task_groups):
        # 使用Task tool调用真实Agent
        # 收集生成的.md文档
        pass

    def _update_canvas(self, canvas_path, results):
        # 为每个生成的.md文档创建蓝色节点
        # 创建边: 黄色节点 -> 蓝色节点
        pass

    def _store_to_memory(self, results):
        # 调用 mcp__graphiti_memory__add_episode
        # 调用 TemporalMemoryManager.store_event
        # 调用 SemanticMemoryManager.store_vector
        pass
```

---

### 2. 三层记忆真实集成

**必需实现**:

#### 2.1 Graphiti/Neo4j集成
- [ ] 每次处理后调用 `mcp__graphiti_memory__add_episode`
- [ ] 存储处理计划 (智能分组结果)
- [ ] 存储执行过程 (进度和状态)
- [ ] 存储生成文档 (文件路径和摘要)
- [ ] 验证Neo4j中有数据

**示例代码**:
```python
from mcp__graphiti_memory import add_episode

def _store_to_graphiti(self, results):
    episode_content = {
        "operation": "intelligent-parallel",
        "canvas_path": self.canvas_path,
        "yellow_nodes_count": len(results["nodes"]),
        "task_groups": results["task_groups"],
        "generated_docs": results["generated_docs"],
        "execution_time": results["execution_time"]
    }

    add_episode(
        content=json.dumps(episode_content, ensure_ascii=False),
        metadata={
            "importance": 8,
            "tags": ["intelligent-parallel", "canvas-learning"]
        }
    )
```

#### 2.2 Temporal记忆集成
- [ ] 调用 `TemporalMemoryManager.store_event` 存储时间序列事件
- [ ] 记录每个Agent调用的时间戳
- [ ] 记录Canvas修改的版本历史

**示例代码**:
```python
from memory_system.temporal_memory_manager import TemporalMemoryManager

temporal_mgr = TemporalMemoryManager()

for result in results:
    temporal_mgr.store_event(
        session_id=self.session_id,
        event_type="agent_execution",
        event_data={
            "agent": result["agent"],
            "node_id": result["node_id"],
            "doc_path": result["doc_path"]
        }
    )
```

#### 2.3 Semantic记忆集成
- [ ] 调用 `SemanticMemoryManager.store_vector` 存储语义向量
- [ ] 为每个黄色节点的内容生成embedding
- [ ] 为每个生成的解释文档生成embedding

---

### 3. Canvas文件修改 (真实实现)

**必需功能**:
- [ ] 读取生成的.md文档列表
- [ ] 为每个.md文档创建蓝色文件节点 (color="5")
- [ ] 创建边连接: 黄色节点 -> 蓝色节点
- [ ] 计算合理的节点位置 (避免重叠)
- [ ] 保存修改后的Canvas文件

**示例代码**:
```python
def _update_canvas(self, canvas_path, results):
    canvas_ops = CanvasJSONOperator()
    canvas_data = canvas_ops.read_canvas(canvas_path)

    for result in results["generated_docs"]:
        # 创建蓝色AI解释节点
        blue_node_id = f"ai-explanation-{result['node_id']}-{timestamp()}"

        # 获取原黄色节点位置
        yellow_node = canvas_ops.find_node_by_id(
            canvas_data,
            result['node_id']
        )

        # 计算蓝色节点位置 (右侧偏移400px)
        blue_x = yellow_node['x'] + 400
        blue_y = yellow_node['y']

        # 添加蓝色节点
        canvas_ops.add_node(
            canvas_data,
            node_id=blue_node_id,
            node_type="file",
            file_path=result['doc_path'],
            x=blue_x,
            y=blue_y,
            width=350,
            height=200,
            color="5"  # 蓝色
        )

        # 创建边连接
        canvas_ops.add_edge(
            canvas_data,
            from_node=result['node_id'],
            to_node=blue_node_id,
            label="AI解释"
        )

    # 保存修改
    canvas_ops.write_canvas(canvas_path, canvas_data)
```

---

### 4. 端到端验证

**必需测试**:
- [ ] 创建真实的E2E测试文件: `tests/test_intelligent_parallel_e2e.py`
- [ ] 测试场景1: 单个黄色节点处理
- [ ] 测试场景2: 多个黄色节点并行处理
- [ ] 测试场景3: Canvas文件被修改 (蓝色节点存在)
- [ ] 测试场景4: 文档文件被创建 (验证.md文件)
- [ ] 测试场景5: Neo4j有数据 (查询验证)
- [ ] 测试场景6: 节点连接正确 (边验证)

**E2E测试框架**:
```python
def test_intelligent_parallel_e2e():
    # 准备测试Canvas
    test_canvas = create_test_canvas_with_yellow_nodes(count=3)

    # 执行intelligent-parallel
    handler = IntelligentParallelCommandHandler()
    results = handler.execute(test_canvas, {"auto": True})

    # 验证1: 文档生成
    assert len(results["generated_docs"]) == 3
    for doc in results["generated_docs"]:
        assert os.path.exists(doc["path"])

    # 验证2: Canvas修改
    canvas_data = CanvasJSONOperator().read_canvas(test_canvas)
    blue_nodes = [n for n in canvas_data["nodes"] if n["color"] == "5"]
    assert len(blue_nodes) == 3

    # 验证3: Neo4j数据
    neo4j_count = query_neo4j("MATCH (n) RETURN count(n)")
    assert neo4j_count > 0

    # 验证4: 边连接
    edges = [e for e in canvas_data["edges"]
             if e["label"] == "AI解释"]
    assert len(edges) == 3
```

---

### 5. 文档更新

**必需更新**:
- [ ] 更新所有Story状态 (25个文件)
  - [ ] 10.1.story.md → Status: IMPLEMENTED
  - [ ] 10.7.story.md → Status: IMPLEMENTED
  - [ ] 10.8.story.md → Status: IMPLEMENTED
  - [ ] 10.9.story.md → Status: IMPLEMENTED
  - [ ] 10.10.story.md → Status: IMPLEMENTED
  - [ ] 10.11.*.md (5个) → Status: IMPLEMENTED
  - [ ] 10.12.story.md → Status: IMPLEMENTED
  - [ ] 10.13.story.md → Status: IMPLEMENTED
- [ ] 更新CLAUDE.md (移除警告banner)
- [ ] 更新intelligent-parallel.md (移除警告,更新为实际功能)
- [ ] 创建用户指南: `docs/USER_GUIDE_INTELLIGENT_PARALLEL.md`

---

## 🚧 实现策略

### Phase 1: 核心功能 (2天)

**目标**: 实现最小可用版本 (MVP)

**任务**:
1. 创建 `command_handlers/intelligent_parallel_handler.py`
2. 实现黄色节点扫描
3. 实现简单的分组算法 (按数量均分)
4. 实现1-2个Agent调用 (clarification-path, memory-anchor)
5. 实现基本的Canvas修改 (蓝色节点)
6. 实现基本的记忆存储 (Graphiti only)

**验收标准**:
- 能够处理单个Canvas的黄色节点
- 能够调用至少2个Agent
- 能够修改Canvas添加蓝色节点
- Neo4j中有数据

### Phase 2: 完整功能 (1天)

**目标**: 实现所有文档承诺的功能

**任务**:
1. 实现智能分组算法 (语义相似度)
2. 实现所有6个Agent调用
3. 实现Temporal和Semantic记忆存储
4. 实现错误处理和回滚
5. 实现详细的进度报告

**验收标准**:
- 智能分组算法工作正常
- 6个Agent都能被正确调用
- 三层记忆系统完全集成
- 错误能够被捕获和处理

### Phase 3: 测试和文档 (1.5天)

**目标**: 确保质量和可维护性

**任务**:
1. 编写E2E测试 (6个测试场景)
2. 编写单元测试 (覆盖核心函数)
3. 更新所有Story文件
4. 创建用户指南
5. 更新CLAUDE.md和PROJECT.md

**验收标准**:
- E2E测试全部通过
- 单元测试覆盖率 ≥ 80%
- 所有文档更新完成
- 用户指南清晰易懂

---

## 🔍 验收清单

实现完成后，必须通过以下所有验收项:

### 代码验收
- [ ] `command_handlers/intelligent_parallel_handler.py` 存在且 > 500行
- [ ] 能够通过 `from command_handlers.intelligent_parallel_handler import IntelligentParallelCommandHandler` 导入
- [ ] 核心函数有完整的docstring
- [ ] 有错误处理和日志记录

### 功能验收
- [ ] 能够扫描并识别黄色节点
- [ ] 能够进行智能分组
- [ ] 能够调用6种Agent (通过Task tool)
- [ ] 能够生成.md文档文件
- [ ] 能够修改Canvas文件 (添加蓝色节点)
- [ ] 能够创建边连接
- [ ] 能够存储到Graphiti (Neo4j有数据)
- [ ] 能够存储到Temporal
- [ ] 能够存储到Semantic

### 测试验收
- [ ] E2E测试存在: `tests/test_intelligent_parallel_e2e.py`
- [ ] 至少6个E2E测试场景
- [ ] 所有E2E测试通过
- [ ] 单元测试覆盖率 ≥ 80%

### 文档验收
- [ ] CLAUDE.md警告banner已移除
- [ ] intelligent-parallel.md警告已移除
- [ ] 25个Epic 10 Story文件状态更新为IMPLEMENTED
- [ ] 用户指南已创建: `docs/USER_GUIDE_INTELLIGENT_PARALLEL.md`

### 真实性验证
- [ ] **关键验证**: 在一个真实Canvas上运行 `/intelligent-parallel --auto`
- [ ] 验证Canvas文件的修改时间戳改变
- [ ] 验证生成的.md文件存在且有实际内容
- [ ] 验证Neo4j数据库: `MATCH (n) RETURN count(n)` > 0
- [ ] 验证蓝色节点存在于Canvas中
- [ ] 验证边连接存在于Canvas中

---

## 🎯 实现决策

现在有三个选项:

### **A) 完整实现** (推荐用于长期项目)

**工作量**: 3.5-4.5天
**优点**: 完整功能，文档和实现一致
**缺点**: 时间投入较大
**适用场景**: 计划长期使用Canvas学习系统

### **B) 暂时冻结** (推荐用于时间紧迫)

**工作量**: 0天
**优点**: 无时间成本
**缺点**: Epic 10功能不可用
**适用场景**: 优先级较低，可以先用手动方式

### **C) 简化版快速实现** (推荐用于快速验证)

**工作量**: 1-2天
**优点**: 快速获得核心功能
**缺点**: 功能简化，部分文档承诺未实现
**实现范围**:
- 只实现核心Handler
- 只支持2-3个Agent
- 基本的Canvas修改
- 只集成Graphiti记忆
- 简化的分组算法

---

## 📝 后续步骤

1. **确定实现策略**: 选择 A/B/C
2. **创建实现分支**: `git checkout -b epic-10-real-implementation`
3. **按Phase顺序实施**: Phase 1 → Phase 2 → Phase 3
4. **持续验证**: 每完成一个Phase运行验收清单
5. **最终验证**: 运行完整的真实性验证清单

---

## 💡 实现建议

1. **从MVP开始**: 先实现最小可用版本，确保核心流程通
2. **增量开发**: 每天提交，确保进度可追踪
3. **真实验证优先**: 每个功能都要在真实Canvas上验证
4. **避免模拟**: 绝不使用print模拟，必须有真实的文件/数据变化
5. **Neo4j验证**: 每次都要查询Neo4j确认数据存在

---

**文档版本**: 1.0
**创建日期**: 2025-11-04
**维护者**: PM Agent (John)
**参考**: `docs/HONEST_STATUS_REPORT_EPIC10.md`
