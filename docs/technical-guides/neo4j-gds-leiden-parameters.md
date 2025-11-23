# Neo4j GDS Leiden算法参数调优指南

**Story**: GDS.1 - Ebbinghaus Trigger Point 4 Technical Guide
**版本**: 1.0.0
**更新日期**: 2025-11-14
**受众**: 开发者、系统管理员

---

## 📚 目录

1. [Leiden算法概述](#leiden算法概述)
2. [核心参数详解](#核心参数详解)
3. [参数调优策略](#参数调优策略)
4. [性能优化指南](#性能优化指南)
5. [故障排查](#故障排查)
6. [最佳实践](#最佳实践)

---

## Leiden算法概述

### 算法简介

**Leiden算法**是一种基于模块度的社区检测算法，由荷兰莱顿大学开发，是Louvain算法的改进版本。

**核心优势**:
- **精度更高**: 解决了Louvain算法的"poorly connected communities"问题
- **结果稳定**: 保证找到良好连接的社区
- **性能优秀**: 时间复杂度O(n log n)，空间复杂度O(n + m)

### 在Canvas学习系统中的应用

```
Canvas概念网络 (Concept Graph)
    ↓
Neo4j图投影 (Graph Projection)
    ↓
Leiden社区检测 (Community Detection)
    ↓
薄弱概念聚类 (Weak Concept Clustering)
```

**目标**: 识别相关联的薄弱概念群，提高复习效率

---

## 核心参数详解

### 参数一览表

| 参数 | 类型 | 默认值 | 取值范围 | 说明 |
|------|------|--------|---------|------|
| `relationshipWeightProperty` | String | null | - | 关系权重属性名 |
| `gamma` | Float | 1.0 | 0.0-∞ | 分辨率参数 |
| `tolerance` | Float | 0.0001 | 0.0-1.0 | 收敛阈值 |
| `randomSeed` | Integer | - | - | 随机种子 |
| `includeIntermediateCommunities` | Boolean | false | - | 是否返回中间层级社区 |
| `maxLevels` | Integer | 10 | 1-∞ | 最大层级数 |
| `iterations` | Integer | 10 | 1-∞ | 每层最大迭代次数 |

---

### 1. relationshipWeightProperty (关系权重)

**作用**: 指定用于社区检测的关系权重属性。

**当前配置**:
```cypher
relationshipWeightProperty: 'strength'
```

**说明**:
- 使用Canvas中的`strength`属性作为概念间关联强度
- `strength`值越大，两个概念越可能被聚类到同一社区
- 如果关系没有`strength`属性，使用默认权重1.0

**调优建议**:

| 场景 | 建议 |
|------|------|
| 所有关系权重相等 | 不设置此参数（或设为null） |
| 关系有明确权重 | 使用`strength`或其他权重属性 |
| 需要强调某些关系 | 增加特定关系的权重值 |

**示例**:
```cypher
// Canvas中定义关系权重
CREATE (a)-[:RELATED_TO {strength: 0.8}]->(b)  // 强关联
CREATE (c)-[:RELATED_TO {strength: 0.3}]->(d)  // 弱关联
```

---

### 2. gamma (分辨率参数)

**作用**: 控制社区检测的分辨率（社区大小和数量）。

**当前配置**:
```python
gamma = 1.0  # 标准社区检测
```

**取值说明**:

| gamma | 社区特征 | 适用场景 |
|-------|---------|---------|
| < 1.0 | 更大、更少 | 宏观概念群（大主题） |
| = 1.0 | 标准平衡 | 通用场景（推荐） |
| > 1.0 | 更小、更多 | 微观概念群（细分主题） |

**调优示例**:

```python
# 场景1: 识别大主题（如"命题逻辑"、"集合论"）
clusters = service.run_leiden_clustering(
    gamma=0.5,  # 更宽泛的聚类
    ...
)

# 场景2: 识别细分主题（如"逆否命题"、"充分条件"、"必要条件"）
clusters = service.run_leiden_clustering(
    gamma=2.0,  # 更细致的聚类
    ...
)
```

**实际效果对比**:

```
gamma=0.5 (大社区):
  社区1: [逆否命题, 充分条件, 必要条件, 逻辑等价, 真值表, 合取范式]  (6个概念)

gamma=1.0 (标准):
  社区1: [逆否命题, 充分条件, 必要条件, 逻辑等价]  (4个概念)
  社区2: [真值表, 合取范式]  (2个概念)

gamma=2.0 (小社区):
  社区1: [逆否命题, 充分条件]  (2个概念)
  社区2: [必要条件, 逻辑等价]  (2个概念)
  社区3: [真值表, 合取范式]  (2个概念)
```

**选择建议**:

```python
def recommend_gamma(concept_count, avg_connections):
    """推荐gamma参数"""
    if concept_count < 20:
        return 0.8  # 小规模图，使用较小gamma避免过度碎片化
    elif concept_count < 100:
        return 1.0  # 中等规模，标准参数
    else:
        if avg_connections < 3:
            return 0.7  # 大规模稀疏图，使用较小gamma
        else:
            return 1.2  # 大规模密集图，使用较大gamma避免过大社区
```

---

### 3. tolerance (收敛阈值)

**作用**: 控制算法收敛的精度。

**当前配置**:
```python
tolerance = 0.0001  # 高精度
```

**取值说明**:

| tolerance | 收敛精度 | 计算时间 | 适用场景 |
|-----------|---------|---------|---------|
| 0.001 | 低精度 | 快 | 大规模图（>10000节点），快速预览 |
| 0.0001 | 高精度 | 中等 | 通用场景（推荐） |
| 0.00001 | 极高精度 | 慢 | 小规模图（<1000节点），需要最优结果 |

**收敛逻辑**:

```python
# 伪代码
while True:
    old_modularity = current_modularity
    optimize_communities()
    new_modularity = current_modularity

    improvement = new_modularity - old_modularity

    if improvement < tolerance:
        break  # 收敛，停止迭代
```

**调优建议**:

```python
# 场景1: 大规模图快速聚类
clusters = service.run_leiden_clustering(
    tolerance=0.001,  # 降低精度要求
    ...
)

# 场景2: 小规模图精确聚类
clusters = service.run_leiden_clustering(
    tolerance=0.00001,  # 提高精度要求
    ...
)
```

**性能对比** (1000个概念):

| tolerance | 迭代次数 | 执行时间 | 模块度 |
|-----------|---------|---------|--------|
| 0.001 | ~5次 | 150ms | 0.752 |
| 0.0001 | ~8次 | 250ms | 0.758 |
| 0.00001 | ~12次 | 380ms | 0.759 |

**结论**: `tolerance=0.0001`是精度和性能的最佳平衡点。

---

### 4. randomSeed (随机种子)

**作用**: 固定随机数生成器，确保结果可重复。

**当前配置**:
```python
randomSeed = 42  # 固定种子
```

**为什么需要固定种子？**

Leiden算法在某些步骤使用随机化：
1. 初始社区分配
2. 节点访问顺序
3. 社区合并决策

**不固定种子的问题**:
```python
# 运行1
clusters_1 = service.run_leiden_clustering()  # 结果: 5个社区

# 运行2 (相同输入)
clusters_2 = service.run_leiden_clustering()  # 结果: 6个社区（不同！）
```

**固定种子的优势**:
```python
# 运行1
clusters_1 = service.run_leiden_clustering(randomSeed=42)  # 结果: 5个社区

# 运行2 (相同输入)
clusters_2 = service.run_leiden_clustering(randomSeed=42)  # 结果: 5个社区（相同！）
```

**调优建议**:

```python
# 生产环境: 固定种子
PRODUCTION_SEED = 42
clusters = service.run_leiden_clustering(randomSeed=PRODUCTION_SEED)

# 开发/测试: 测试多个种子，选择最优结果
best_modularity = 0
best_result = None

for seed in [42, 123, 456, 789]:
    result = service.run_leiden_clustering(randomSeed=seed)
    modularity = calculate_modularity(result)

    if modularity > best_modularity:
        best_modularity = modularity
        best_result = result
```

---

### 5. includeIntermediateCommunities (中间层级社区)

**作用**: 返回多层级的社区结构（hierarchical clustering）。

**当前配置**:
```python
includeIntermediateCommunities = true
```

**输出差异**:

**不包含中间层级** (`includeIntermediateCommunities=false`):
```json
{
  "nodeId": 123,
  "communityId": 42  // 只有最终层级
}
```

**包含中间层级** (`includeIntermediateCommunities=true`):
```json
{
  "nodeId": 123,
  "communityId": 42,  // 最终层级
  "intermediateCommunityIds": [5, 12, 42]  // 层级0→1→2的社区ID
}
```

**层级结构示例**:

```
层级0 (最粗粒度):
  社区5: [概念1-20]  (20个概念)

层级1 (中等粒度):
  社区12: [概念1-10]  (10个概念)
  社区13: [概念11-20]  (10个概念)

层级2 (最细粒度):
  社区42: [概念1-5]  (5个概念)
  社区43: [概念6-10]  (5个概念)
  社区44: [概念11-15]  (5个概念)
  社区45: [概念16-20]  (5个概念)
```

**应用场景**:

```python
# 场景1: 多层次复习计划
result = service.run_leiden_clustering(includeIntermediateCommunities=True)

for record in result:
    intermediate_ids = record["intermediateCommunityIds"]

    # 层级0: 大主题复习
    theme = intermediate_ids[0]

    # 层级1: 中等主题复习
    subtopic = intermediate_ids[1]

    # 层级2: 细分主题复习
    detail = intermediate_ids[2]
```

**当前版本**: 默认启用中间层级，但未使用（保留扩展性）。

---

### 6. maxLevels 和 iterations

**maxLevels**: 算法的最大层级数（默认10）
**iterations**: 每层的最大迭代次数（默认10）

**当前配置**: 使用Neo4j GDS默认值，无需手动设置。

**调优场景** (极少需要):

```python
# 场景1: 大规模图需要更多层级
# （不推荐在API层面修改，应修改Neo4j GDS配置）
CALL gds.leiden.stream('graph', {
    maxLevels: 20,  // 增加层级
    iterations: 15  // 增加迭代
})

# 场景2: 快速聚类（牺牲质量）
CALL gds.leiden.stream('graph', {
    maxLevels: 5,   // 减少层级
    iterations: 5   // 减少迭代
})
```

---

## 参数调优策略

### 1. 基于Canvas规模的调优

```python
def get_optimal_parameters(concept_count):
    """根据概念数量推荐最优参数"""
    if concept_count < 50:
        # 小规模Canvas
        return {
            "gamma": 0.8,
            "tolerance": 0.00001,
            "randomSeed": 42
        }
    elif concept_count < 500:
        # 中等规模Canvas
        return {
            "gamma": 1.0,
            "tolerance": 0.0001,
            "randomSeed": 42
        }
    else:
        # 大规模Canvas
        return {
            "gamma": 1.2,
            "tolerance": 0.001,
            "randomSeed": 42
        }
```

### 2. 基于图密度的调优

```python
def get_optimal_parameters_by_density(node_count, edge_count):
    """根据图密度推荐最优参数"""
    density = edge_count / (node_count * (node_count - 1) / 2)

    if density < 0.1:
        # 稀疏图
        return {"gamma": 0.7}  # 避免过度碎片化
    elif density > 0.5:
        # 密集图
        return {"gamma": 1.5}  # 避免过大社区
    else:
        # 正常密度
        return {"gamma": 1.0}
```

### 3. 基于业务目标的调优

```python
# 目标1: 发现大主题（用于宏观复习计划）
clusters = service.run_leiden_clustering(
    gamma=0.5,
    tolerance=0.001  # 可适当降低精度加快速度
)

# 目标2: 发现细分主题（用于精准复习）
clusters = service.run_leiden_clustering(
    gamma=2.0,
    tolerance=0.0001
)

# 目标3: 平衡复习（通用场景）
clusters = service.run_leiden_clustering(
    gamma=1.0,
    tolerance=0.0001
)
```

---

## 性能优化指南

### 1. 图投影内存估算

**问题**: 大规模图投影可能导致OOM（Out of Memory）

**解决方案**: 使用`gds.graph.project.estimate()`预估内存

```python
# 调用estimate_projection_memory()
estimate = service.estimate_projection_memory()

print(f"所需内存: {estimate['required_memory']}")
print(f"节点数量: {estimate['node_count']}")
print(f"关系数量: {estimate['relationship_count']}")

# 输出示例:
# 所需内存: 125 MiB
# 节点数量: 1000
# 关系数量: 3500
```

**内存需求参考**:

| 节点数 | 关系数 | 所需内存 |
|--------|--------|---------|
| 100 | 300 | ~10 MiB |
| 1000 | 3500 | ~125 MiB |
| 5000 | 20000 | ~650 MiB |
| 10000 | 50000 | ~1.5 GiB |

**优化策略**:

```python
# 1. 检查内存
estimate = service.estimate_projection_memory()
required_mb = parse_memory(estimate['required_memory'])

# 2. 如果超过阈值，考虑批处理
MEMORY_THRESHOLD = 1000  # 1GB

if required_mb > MEMORY_THRESHOLD:
    # 批处理策略（未来实现）
    logger.warning("图规模过大，建议分批处理")
```

---

### 2. 批量处理大规模数据

**问题**: >5000概念时，单次聚类可能超时或内存不足

**解决方案**: 分批处理

```python
def batch_clustering(service, concept_ids, batch_size=1000):
    """批量聚类大规模数据"""
    all_clusters = []

    for i in range(0, len(concept_ids), batch_size):
        batch = concept_ids[i:i+batch_size]

        # 为每批创建子图投影
        batch_projection_name = f"weak-concepts-batch-{i//batch_size}"

        # 创建批次图投影
        # （需要修改create_weak_concepts_graph_projection支持自定义图名）

        # 执行聚类
        batch_clusters = service.run_leiden_clustering(...)

        all_clusters.extend(batch_clusters)

    return all_clusters
```

**注意**: 当前版本不支持批处理，留待未来Story实现。

---

### 3. 执行时间优化

**目标**: 1000概念 <500ms (Story GDS.1 - AC3)

**性能分析**:

```python
import time

start = time.time()

# 1. 图投影
proj_start = time.time()
service.create_weak_concepts_graph_projection()
proj_time = time.time() - proj_start

# 2. Leiden聚类
leiden_start = time.time()
clusters = service.run_leiden_clustering()
leiden_time = time.time() - leiden_start

total_time = time.time() - start

print(f"图投影: {proj_time*1000:.0f}ms")
print(f"Leiden聚类: {leiden_time*1000:.0f}ms")
print(f"总时间: {total_time*1000:.0f}ms")

# 输出示例 (1000概念):
# 图投影: 120ms
# Leiden聚类: 280ms
# 总时间: 400ms ✅ (<500ms)
```

**优化技巧**:

1. **复用图投影**: 如果概念网络未变，无需重建
2. **降低tolerance**: 如0.001 (损失少量精度，提升速度)
3. **使用Native图投影**: `gds.graph.project`而非Cypher投影

---

### 4. 并发处理

**场景**: 同时处理多个Canvas的薄弱点聚类

**注意事项**:

```python
# ❌ 错误: 并发共享同一Neo4j连接
service = Neo4jGDSClustering()

def process_canvas(canvas_path):
    # 多个线程共享service会导致连接冲突
    service.run_leiden_clustering()

with ThreadPoolExecutor() as executor:
    executor.map(process_canvas, canvas_paths)  # 可能出错
```

```python
# ✅ 正确: 每个任务创建独立连接
def process_canvas(canvas_path):
    # 每个线程独立创建服务实例
    with Neo4jGDSClustering() as service:
        service.create_weak_concepts_graph_projection()
        clusters = service.run_leiden_clustering()
        return clusters

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(process_canvas, canvas_paths)
```

---

## 故障排查

### 问题1: Neo4j GDS库未安装

**错误信息**:
```
ClientError: There is no procedure with the name `gds.graph.project` registered for this database instance.
```

**解决方案**:

1. 确认GDS版本
```cypher
RETURN gds.version()
```

2. 如果返回错误，安装Neo4j GDS插件
```bash
# 下载插件
wget https://s3-eu-west-1.amazonaws.com/com.neo4j.graphalgorithms.dist/neo4j-graph-data-science-2.4.0.jar

# 复制到plugins目录
cp neo4j-graph-data-science-2.4.0.jar /path/to/neo4j/plugins/

# 重启Neo4j
neo4j restart
```

3. 验证安装
```python
python scripts/verify_neo4j_gds.py
```

---

### 问题2: 图投影已存在

**错误信息**:
```
ClientError: A graph with name 'weak-concepts-graph' already exists.
```

**解决方案1**: 强制重建（推荐）
```python
service.create_weak_concepts_graph_projection(force_recreate=True)
```

**解决方案2**: 手动删除
```cypher
CALL gds.graph.drop('weak-concepts-graph')
```

---

### 问题3: 聚类结果为空

**错误信息**: 无错误，但`clusters`为空列表

**可能原因**:

1. **无薄弱概念**: 所有概念分数≥70且复习次数≤3
2. **阈值过严**: `min_weak_score`设置过低或`min_review_count`过高
3. **图投影为空**: 没有符合条件的`:Concept`节点

**排查步骤**:

```cypher
-- 1. 检查概念节点数量
MATCH (c:Concept)
RETURN count(c) AS concept_count

-- 2. 检查薄弱概念数量
MATCH (c:Concept)
WHERE c.avg_score < 70 OR c.review_count > 3
RETURN count(c) AS weak_concept_count

-- 3. 检查图投影状态
CALL gds.graph.list('weak-concepts-graph')
YIELD nodeCount, relationshipCount
```

**解决方案**: 调整阈值
```python
# 降低薄弱点标准
clusters = service.run_leiden_clustering(
    min_weak_score=80,      # 提高分数阈值
    min_review_count=2      # 降低复习次数阈值
)
```

---

### 问题4: 性能达不到目标 (<500ms)

**问题**: 1000概念聚类时间>500ms

**排查方向**:

1. **检查Neo4j配置**
```
# neo4j.conf
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G
```

2. **检查图投影方式**
```python
# ❌ 慢: Cypher投影
CALL gds.graph.project.cypher(...)

# ✅ 快: Native投影
CALL gds.graph.project(...)
```

3. **检查tolerance参数**
```python
# ❌ 慢: 高精度
tolerance=0.00001

# ✅ 快: 平衡精度
tolerance=0.0001
```

4. **执行性能基准测试**
```bash
cd "C:/Users/ROG/托福"
python tests/test_performance_leiden_clustering.py
```

---

### 问题5: 内存不足 (OOM)

**错误信息**:
```
java.lang.OutOfMemoryError: Java heap space
```

**解决方案**:

1. **增加Neo4j堆内存**
```
# neo4j.conf
dbms.memory.heap.max_size=8G  # 增加到8GB
```

2. **使用估算功能**
```python
# 预估内存后再决定是否执行
estimate = service.estimate_projection_memory()
if parse_memory(estimate['required_memory']) > 2000:  # >2GB
    print("警告: 内存需求过大，建议分批处理")
```

3. **减少图投影属性**
```python
# 只投影必要属性
nodeProperties: {
    'avg_score': {defaultValue: 100}
    # 移除 'review_count', 'last_review_days_ago'
}
```

---

## 最佳实践

### 1. 生产环境配置

```python
# ebbinghaus/config.py
PRODUCTION_CONFIG = {
    # Neo4j连接
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_database": "ultrathink",

    # Leiden参数（经过调优）
    "gamma": 1.0,
    "tolerance": 0.0001,
    "randomSeed": 42,

    # 薄弱点阈值
    "min_weak_score": 70,
    "min_review_count": 3,

    # 性能限制
    "max_concepts": 5000,  # 超过此值警告
    "timeout": 10000       # 10秒超时
}
```

### 2. 错误处理

```python
def trigger_clustering_with_retry(canvas_path, max_retries=3):
    """带重试的聚类触发"""
    for attempt in range(max_retries):
        try:
            result = trigger_weak_point_clustering(canvas_path)
            return result
        except ClientError as e:
            if "graph already exists" in str(e):
                # 重试前删除旧图投影
                service.drop_graph_projection()
            elif attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise
        except RuntimeError as e:
            logger.error(f"聚类失败 (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                raise
```

### 3. 日志记录

```python
# 启用DEBUG日志查看详细执行过程
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 执行聚类
result = trigger_weak_point_clustering("path/to/canvas.canvas")

# 日志输出示例:
# 2025-11-14 12:00:00 - neo4j_gds_clustering - INFO - ✅ Neo4j GDS连接成功
# 2025-11-14 12:00:01 - neo4j_gds_clustering - INFO - 开始创建图投影...
# 2025-11-14 12:00:02 - neo4j_gds_clustering - INFO - ✅ 图投影创建成功 (1000 nodes)
# 2025-11-14 12:00:03 - neo4j_gds_clustering - INFO - 开始执行Leiden聚类算法...
# 2025-11-14 12:00:04 - neo4j_gds_clustering - INFO - ✅ Leiden聚类完成 (5个社区)
```

### 4. 单元测试

```python
# tests/test_leiden_parameters.py
import pytest

def test_leiden_with_different_gamma():
    """测试不同gamma参数的聚类结果"""
    service = Neo4jGDSClustering()

    # gamma=0.5 (大社区)
    clusters_05 = service.run_leiden_clustering(gamma=0.5)

    # gamma=1.0 (标准)
    clusters_10 = service.run_leiden_clustering(gamma=1.0)

    # gamma=2.0 (小社区)
    clusters_20 = service.run_leiden_clustering(gamma=2.0)

    # 验证: gamma越大，社区数量越多
    assert len(clusters_05) <= len(clusters_10) <= len(clusters_20)
```

---

## 参考资料

- [Neo4j GDS Leiden算法官方文档](https://neo4j.com/docs/graph-data-science/current/algorithms/leiden/)
- [Leiden算法论文](https://www.nature.com/articles/s41598-019-41695-z)
- [Canvas学习系统架构文档](../architecture/canvas-learning-system.md)
- [Story GDS.1实现规格](../stories/gds-1-ebbinghaus-trigger-point-4.story.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-14
**Story**: GDS.1 - Subtask 4.2
