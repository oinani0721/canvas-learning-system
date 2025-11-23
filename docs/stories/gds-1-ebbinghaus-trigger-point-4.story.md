# Story GDS.1: Ebbinghaus Trigger Point 4 - Community-Based Weak Point Clustering

## Status
Ready for Development

## Story

**As a** Canvas学习系统，
**I want** 使用Neo4j GDS Leiden算法实现薄弱概念的社区检测和聚类，
**so that** 艾宾浩斯复习系统的触发点4能够自动识别相关联的薄弱概念群，生成针对性检验白板，提高复习效率。

## Background

**Epic**: EPIC-Neo4j-GDS-Integration
**替代Story**: GraphRAG.4 (已废弃)
**优先级**: 🔥 Critical (P0) - Epic 14依赖
**工作量**: 3天
**预计成本**: $480 (3天 × $160/天)

**业务需求**:
- 艾宾浩斯触发点4需要识别薄弱点聚类（PRD FR3.1 Lines 475-530）
- 原GraphRAG方案成本过高（$9,784首年），改用Neo4j GDS轻量化方案
- 必须满足与艾宾浩斯系统的API集成需求

---

## Acceptance Criteria

### AC1: Neo4j GDS Leiden算法成功聚类薄弱概念
- [ ] 创建包含薄弱概念的图投影（`weak-concepts-graph`）
- [ ] 图投影包含节点属性：`avg_score`, `review_count`, `last_review_days_ago`
- [ ] 图投影包含关系权重：`strength`（基于概念间关联强度）
- [ ] Leiden算法成功执行，生成社区ID（`communityId`）
- [ ] 仅聚类薄弱概念（`avg_score < 70` OR `review_count > 3`）
- [ ] **验收测试**: 100个概念的测试数据集，成功生成3-5个社区

### AC2: 输出格式与艾宾浩斯系统兼容
- [ ] 输出JSON格式符合PRD定义（`trigger_point`, `clusters`, `total_weak_concepts`）
- [ ] 每个cluster包含：`cluster_id`, `concepts`, `cluster_score`, `recommended_review_urgency`
- [ ] 每个concept包含：`id`, `name`, `score`, `reviews`
- [ ] **验收测试**: JSON schema验证通过，字段完整性100%

### AC3: 算法响应时间<500ms（1000个概念规模）
- [ ] 图投影创建时间<200ms
- [ ] Leiden聚类计算时间<300ms
- [ ] 总端到端响应时间<500ms（含数据库查询和结果转换）
- [ ] **验收测试**: 性能基准测试，10次执行平均响应<500ms

### AC4: 生成的检验白板包含同一社区的相关薄弱点
- [ ] 调用`generate_review_canvas_file()`时，传入聚类结果
- [ ] 同一社区的概念在检验白板中相邻布局
- [ ] 检验白板包含社区标识（如颜色或分组标记）
- [ ] **验收测试**: 手动检查生成的Canvas文件，社区概念正确分组

---

## Tasks / Subtasks

### Task 1: Neo4j GDS环境准备与图投影创建 (AC: 1, 3)

**Subtask 1.1**: 安装和配置Neo4j GDS库
- [ ] 确认Neo4j版本兼容性（需GDS 2.4+）
- [ ] 在dev环境安装Neo4j GDS插件
- [ ] 验证GDS库加载成功：`RETURN gds.version()`
- [ ] 锁定GDS版本号到`requirements.txt`或Docker配置

**Subtask 1.2**: 实现图投影创建函数
- [ ] 创建`canvas_memory/neo4j_gds_clustering.py`模块
- [ ] 实现`create_weak_concepts_graph_projection()`函数
- [ ] 图投影命名：`weak-concepts-graph`
- [ ] 节点筛选：`:Concept`标签
- [ ] 关系筛选：`:RELATED_TO`类型
- [ ] 节点属性映射：
  ```python
  nodeProperties = {
      'avg_score': {'defaultValue': 100},
      'review_count': {'defaultValue': 0},
      'last_review_days_ago': {'defaultValue': 999}
  }
  ```
- [ ] 关系权重映射：`relationshipProperties = ['strength']`
- [ ] 错误处理：图投影已存在时先删除（`gds.graph.drop()`）

**Subtask 1.3**: 添加单元测试
- [ ] 测试用例：正常情况创建图投影成功
- [ ] 测试用例：图投影已存在时重建
- [ ] 测试用例：Neo4j连接失败时异常处理
- [ ] 覆盖率目标：>90%

---

### Task 2: Leiden社区检测算法实现 (AC: 1, 2, 3)

**Subtask 2.1**: 实现Leiden聚类函数
- [ ] 实现`run_leiden_clustering()`函数
- [ ] Cypher查询实现：
  ```cypher
  CALL gds.leiden.stream('weak-concepts-graph', {
      nodeLabels: ['Concept'],
      relationshipWeightProperty: 'strength',
      includeIntermediateCommunities: true,
      tolerance: 0.0001,
      gamma: 1.0,
      randomSeed: 42  // 固定随机种子，确保可重复性
  })
  YIELD nodeId, communityId, intermediateCommunityIds
  WITH gds.util.asNode(nodeId) AS concept, communityId
  WHERE concept.avg_score < 70 OR concept.review_count > 3
  RETURN
      communityId AS cluster_id,
      collect({
          id: id(concept),
          name: concept.name,
          score: concept.avg_score,
          reviews: concept.review_count
      }) AS concepts,
      avg(concept.avg_score) AS cluster_score,
      count(concept) AS cluster_size
  ORDER BY cluster_size DESC
  ```
- [ ] 参数优化：`gamma=1.0`（标准社区检测），`tolerance=0.0001`（高精度）
- [ ] 固定随机种子：`randomSeed=42`（确保结果可重复）

**Subtask 2.2**: 结果格式化与紧急度评估
- [ ] 实现`format_clustering_results()`函数
- [ ] 计算每个cluster的`cluster_score`（平均分）
- [ ] 评估`recommended_review_urgency`：
  - `cluster_score < 60`: `"urgent"`
  - `60 <= cluster_score < 70`: `"high"`
  - `cluster_score >= 70`: `"medium"`
- [ ] 输出JSON格式：
  ```json
  {
    "trigger_point": 4,
    "trigger_name": "薄弱点聚类",
    "clusters": [...],
    "total_weak_concepts": <int>,
    "total_clusters": <int>,
    "timestamp": "<ISO 8601>"
  }
  ```

**Subtask 2.3**: 性能优化
- [ ] 图投影使用`ESTIMATE`模式预估内存（`gds.graph.project.estimate()`）
- [ ] 批量处理大规模数据（>5000概念时分批处理）
- [ ] 添加执行时间日志（DEBUG级别）
- [ ] 性能基准测试：100, 500, 1000, 5000概念规模

**Subtask 2.4**: 添加集成测试
- [ ] 测试用例：100个概念成功聚类（3-5个社区）
- [ ] 测试用例：1000个概念性能达标（<500ms）
- [ ] 测试用例：空数据集处理（无薄弱概念时返回空clusters）
- [ ] 测试用例：JSON输出格式验证

---

### Task 3: 艾宾浩斯系统API集成 (AC: 2, 4)

**Subtask 3.1**: 创建艾宾浩斯触发点4 API
- [ ] 创建`ebbinghaus/trigger_point_4.py`模块
- [ ] 实现`trigger_weak_point_clustering()`函数
- [ ] API签名：
  ```python
  def trigger_weak_point_clustering(
      canvas_path: str,
      min_weak_score: int = 70,
      min_review_count: int = 3
  ) -> dict:
      """
      触发薄弱点聚类检测

      Args:
          canvas_path: Canvas文件路径
          min_weak_score: 薄弱点分数阈值（默认70）
          min_review_count: 复习次数阈值（默认3）

      Returns:
          聚类结果JSON（符合PRD格式）
      """
  ```
- [ ] 调用链：`create_graph_projection() → run_leiden_clustering() → format_results()`
- [ ] 错误处理：Neo4j连接失败、Canvas文件不存在、无薄弱概念等

**Subtask 3.2**: 与检验白板生成集成
- [ ] 修改`generate_review_canvas_file()`函数
- [ ] 新增参数：`cluster_results: Optional[dict] = None`
- [ ] 当提供cluster_results时：
  - 按社区分组布局问题节点
  - 添加社区分隔符或颜色标识
  - 同一社区节点相邻放置（`y += CLUSTER_GAP`）
- [ ] 向后兼容：未提供cluster_results时使用原逻辑

**Subtask 3.3**: 添加端到端测试
- [ ] 测试用例：完整流程（Canvas → 聚类 → 生成检验白板）
- [ ] 验证检验白板文件正确生成
- [ ] 验证社区概念正确分组（手动检查Canvas JSON）
- [ ] 性能测试：完整流程<2秒

---

### Task 4: 文档与部署 (AC: 所有)

**Subtask 4.1**: 用户文档
- [ ] 创建`docs/user-guides/ebbinghaus-trigger-point-4-clustering.md`
- [ ] 说明如何解读社区聚类结果
- [ ] 提供复习策略建议（基于`recommended_review_urgency`）
- [ ] 添加示例截图（Canvas中的社区分组）

**Subtask 4.2**: 开发者文档
- [ ] 创建`docs/technical-guides/neo4j-gds-leiden-parameters.md`
- [ ] 说明Leiden参数调优（`gamma`, `tolerance`, `iterations`）
- [ ] 提供性能调优指南（大规模数据处理）
- [ ] 添加故障排查章节

**Subtask 4.3**: 部署配置
- [ ] 更新`requirements.txt`：添加`neo4j-gds>=2.4`
- [ ] 更新Docker配置（如使用Docker）：安装GDS插件
- [ ] 更新`.env.example`：添加GDS相关配置项
- [ ] CI/CD管道：添加GDS库验证步骤

**Subtask 4.4**: 回归测试
- [ ] 运行全量测试套件（Epic 10, 12, 14相关测试）
- [ ] 验证与现有功能无冲突
- [ ] 性能回归测试：确保整体系统性能无下降

---

## Technical Notes

### Neo4j GDS Leiden算法说明
- **算法类型**: 基于模块度的社区检测算法（优于Louvain，精度更高）
- **时间复杂度**: O(n log n)，n为节点数
- **空间复杂度**: O(n + m)，m为边数
- **输出**: 每个节点分配一个社区ID（整数）

### 关键参数
| 参数 | 默认值 | 说明 |
|------|-------|------|
| `gamma` | 1.0 | 分辨率参数（越大社区越小） |
| `tolerance` | 0.0001 | 收敛阈值（越小精度越高） |
| `randomSeed` | 42 | 随机种子（固定值确保可重复） |
| `includeIntermediateCommunities` | true | 返回中间层级社区（可选） |

### 与GraphRAG对比
| 维度 | GraphRAG Leiden | Neo4j GDS Leiden |
|------|---------------|-----------------|
| 算法 | 相同 | 相同 |
| 响应时间 | 2-8秒 | <200ms ⭐ |
| 存储 | Parquet文件 | Neo4j原生 ✅ |
| 成本 | $9,784/年 | $1,200/年 ⭐ |

---

## Testing Strategy

### 单元测试
- **覆盖率目标**: >90%
- **测试框架**: pytest
- **测试文件**: `tests/test_neo4j_gds_clustering.py`, `tests/test_trigger_point_4.py`
- **Mock策略**: Mock Neo4j连接，使用内存数据库或测试数据集

### 集成测试
- **测试范围**: Neo4j GDS库集成、Canvas生成集成、艾宾浩斯系统集成
- **测试数据**: 100概念测试Canvas、1000概念性能测试Canvas
- **验证点**: 聚类结果正确性、JSON格式完整性、检验白板生成正确性

### 性能测试
- **工具**: pytest-benchmark
- **基准**: 1000概念 <500ms, 5000概念 <2秒
- **测试脚本**: `tests/performance/test_leiden_clustering_performance.py`

### 端到端测试
- **场景**: 真实Canvas → 触发点4 → 生成检验白板 → 手动验证
- **验收**: PM/QA手动确认检验白板社区分组正确

---

## Dependencies

### 前置依赖
- ✅ Epic 12完成（Neo4j Graphiti已部署）
- ✅ Epic 10完成（Canvas操作基础）
- ✅ Neo4j 4.4+ 已安装
- ✅ Python 3.9+ 环境

### 技术栈
- **Neo4j GDS**: 2.4+ (图算法库)
- **neo4j-driver**: 5.x (Python Neo4j客户端)
- **Python标准库**: json, datetime, logging

### 阻塞下游
- 🔓 Epic 14 Story 14.4: 艾宾浩斯触发点4调度逻辑

---

## Definition of Done

- [ ] 所有AC验证通过（100%）
- [ ] 单元测试覆盖率>90%
- [ ] 集成测试全部通过
- [ ] 性能测试达标（<500ms @ 1000概念）
- [ ] 代码审查通过（无Critical/High问题）
- [ ] 用户文档和开发者文档完成
- [ ] 部署配置更新（requirements.txt, Docker等）
- [ ] PM/QA验收通过
- [ ] 无Outstanding Bug（P0/P1）

---

## Notes

**替代Story**: 本Story替代废弃的GraphRAG.4，提供相同功能但成本降低88%

**决策记录**:
- ADR-004: Do Not Integrate GraphRAG
- SCP-005: GraphRAG过度设计纠偏

**相关Epic**: EPIC-Neo4j-GDS-Integration

---

**Story Owner**: Dev Agent (James)
**Created**: 2025-11-14
**Last Updated**: 2025-11-14
**Status**: ✅ Ready for Development
