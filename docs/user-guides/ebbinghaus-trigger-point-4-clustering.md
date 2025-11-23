# 艾宾浩斯触发点4: 薄弱点聚类使用指南

**Story**: GDS.1 - Ebbinghaus Trigger Point 4 Community-Based Weak Point Clustering
**版本**: 1.0.0
**更新日期**: 2025-11-14

---

## 📚 目录

1. [功能概述](#功能概述)
2. [核心概念](#核心概念)
3. [使用方法](#使用方法)
4. [解读聚类结果](#解读聚类结果)
5. [复习策略建议](#复习策略建议)
6. [常见问题](#常见问题)

---

## 功能概述

**艾宾浩斯触发点4: 薄弱点聚类**是Canvas学习系统的智能复习触发点，使用Neo4j Graph Data Science库的Leiden社区检测算法，自动识别相关联的薄弱概念群，生成针对性检验白板，提高复习效率。

### 核心优势

- **智能聚类**: 自动识别相关联的薄弱概念（而非孤立的单个概念）
- **社区检测**: 使用Leiden算法（优于传统Louvain算法）发现概念间的隐含关联
- **复习优化**: 按社区组织复习内容，一次性突破相关概念群
- **紧急度评估**: 自动评估每个社区的复习紧急程度（urgent/high/medium）

### 与传统复习的区别

| 维度 | 传统复习方式 | 薄弱点聚类复习 |
|------|------------|---------------|
| 复习单位 | 单个概念 | 概念社区（关联概念群） |
| 识别方式 | 手动标记 | 自动聚类 |
| 关联发现 | 依赖人工经验 | 算法自动发现隐含关联 |
| 复习效率 | 低（孤立复习） | 高（批量突破） |
| 优先级判断 | 主观判断 | 算法评分+紧急度评估 |

---

## 核心概念

### 1. 薄弱概念 (Weak Concept)

满足以下任一条件的概念视为"薄弱概念"：

- **平均分数 < 70分** - 理解不充分
- **复习次数 > 3次** - 多次复习仍未掌握

### 2. 社区 (Community/Cluster)

通过Leiden算法识别的**相关联的薄弱概念群**。同一社区内的概念通常具有：

- 知识上的相互依赖关系
- 结构上的关联（通过Canvas关系边连接）
- 语义上的相似性

### 3. 社区分数 (Cluster Score)

社区内所有概念平均分数的均值，反映该社区的整体掌握程度。

### 4. 复习紧急度 (Review Urgency)

基于社区分数自动评估的复习优先级：

| 紧急度 | 社区分数范围 | 含义 | 建议行动 |
|--------|------------|------|---------|
| **urgent** | < 60分 | 严重薄弱 | 🔴 **立即复习**，优先级最高 |
| **high** | 60-69分 | 理解不足 | 🟠 **尽快复习**，优先级高 |
| **medium** | ≥ 70分 | 轻度薄弱 | 🟡 **安排复习**，优先级中等 |

---

## 使用方法

### 方式1: Python API调用 (推荐开发者)

```python
from ebbinghaus.trigger_point_4 import trigger_weak_point_clustering

# 对Canvas执行薄弱点聚类
result = trigger_weak_point_clustering(
    canvas_path="笔记库/离散数学/离散数学.canvas",
    min_weak_score=70,     # 薄弱点分数阈值（默认70）
    min_review_count=3     # 复习次数阈值（默认3）
)

# 查看结果
print(f"薄弱概念总数: {result['total_weak_concepts']}")
print(f"社区总数: {result['total_clusters']}")

for cluster in result['clusters']:
    print(f"\n社区 {cluster['cluster_id']}:")
    print(f"  平均分数: {cluster['cluster_score']}")
    print(f"  社区大小: {cluster['cluster_size']}")
    print(f"  复习紧急度: {cluster['recommended_review_urgency']}")
    print(f"  包含概念:")
    for concept in cluster['concepts']:
        print(f"    - {concept['name']} (分数: {concept['score']}, 复习: {concept['reviews']}次)")
```

### 方式2: 命令行调用

```bash
# 进入项目目录
cd "C:/Users/ROG/托福"

# 执行薄弱点聚类
python ebbinghaus/trigger_point_4.py
```

---

## 解读聚类结果

### 输出JSON格式

```json
{
  "trigger_point": 4,
  "trigger_name": "薄弱点聚类",
  "clusters": [
    {
      "cluster_id": 42,
      "concepts": [
        {"id": 123, "name": "逆否命题", "score": 65, "reviews": 4},
        {"id": 124, "name": "充分必要条件", "score": 68, "reviews": 3},
        {"id": 125, "name": "逻辑等价", "score": 62, "reviews": 5}
      ],
      "cluster_score": 65.0,
      "cluster_size": 3,
      "recommended_review_urgency": "high"
    },
    {
      "cluster_id": 108,
      "concepts": [
        {"id": 200, "name": "真值表", "score": 55, "reviews": 6}
      ],
      "cluster_score": 55.0,
      "cluster_size": 1,
      "recommended_review_urgency": "urgent"
    }
  ],
  "total_weak_concepts": 4,
  "total_clusters": 2,
  "timestamp": "2025-11-14T12:30:45.123456"
}
```

### 关键字段说明

| 字段 | 含义 | 示例 |
|------|------|------|
| `trigger_point` | 触发点编号 | 4 |
| `trigger_name` | 触发点名称 | "薄弱点聚类" |
| `total_weak_concepts` | 薄弱概念总数 | 4 |
| `total_clusters` | 识别的社区数量 | 2 |
| `cluster_id` | 社区ID（由Leiden算法分配） | 42 |
| `cluster_score` | 社区平均分数 | 65.0 |
| `cluster_size` | 社区包含的概念数量 | 3 |
| `recommended_review_urgency` | 复习紧急度 | "high" |
| `concepts` | 社区包含的概念列表 | [...] |
| `timestamp` | 聚类执行时间（ISO 8601格式） | "2025-11-14T12:30:45" |

### 如何解读社区

**示例社区**:

```json
{
  "cluster_id": 42,
  "concepts": [
    {"name": "逆否命题", "score": 65, "reviews": 4},
    {"name": "充分必要条件", "score": 68, "reviews": 3},
    {"name": "逻辑等价", "score": 62, "reviews": 5}
  ],
  "cluster_score": 65.0,
  "cluster_size": 3,
  "recommended_review_urgency": "high"
}
```

**解读**:

1. **社区关联性**: 这3个概念（逆否命题、充分必要条件、逻辑等价）在知识结构上紧密关联
2. **整体掌握度**: 社区平均分65分，属于"理解不足"水平
3. **复习建议**: 紧急度为"high"，应该尽快安排复习
4. **复习策略**:
   - 这3个概念应该**一起复习**（而非孤立复习单个概念）
   - 重点理解它们之间的**逻辑关系**和**相互转换**
   - 寻找它们的**共同底层原理**（如命题逻辑的真值判断）

---

## 复习策略建议

### 基于紧急度的复习顺序

#### 🔴 Urgent级别 (<60分)

**特征**:
- 严重不理解
- 多次复习仍未掌握
- 分数低于及格线

**复习策略**:
1. **立即复习**，优先级最高
2. 调用**basic-decomposition** Agent拆解为更简单的引导问题
3. 调用**oral-explanation** Agent获取口语化解释
4. 调用**example-teaching** Agent学习具体例题
5. 每个概念至少复习**2-3次**，直到理解评分≥70分
6. 重点关注**基础定义**和**核心原理**

**示例行动**:
```python
# 对Urgent社区的每个概念进行深度学习
for concept in urgent_cluster['concepts']:
    # 1. 基础拆解
    basic_questions = call_basic_decomposition_agent(concept['name'])

    # 2. 口语化解释
    oral_explanation = call_oral_explanation_agent(concept['name'])

    # 3. 例题教学
    example_tutorial = call_example_teaching_agent(concept['name'])

    # 4. 填写理解 + 评分
    fill_understanding_and_score(concept['name'])
```

---

#### 🟠 High级别 (60-69分)

**特征**:
- 似懂非懂
- 理解不够深入
- 容易混淆

**复习策略**:
1. **尽快复习**，优先级高
2. 调用**deep-decomposition** Agent进行深度拆解
3. 调用**clarification-path** Agent获取系统化澄清
4. 调用**comparison-table** Agent对比易混淆概念
5. 重点关注**概念间的差异**和**应用场景**
6. 生成**检验白板**进行知识复现

**示例行动**:
```python
# 对High社区进行深度学习
for concept in high_cluster['concepts']:
    # 1. 深度拆解
    deep_questions = call_deep_decomposition_agent(concept['name'], user_understanding)

    # 2. 澄清路径
    clarification = call_clarification_path_agent(concept['name'])

    # 3. 对比易混概念
    comparison = call_comparison_table_agent([concept['name'], similar_concept])

    # 4. 优化理解 + 重新评分
    optimize_understanding_and_rescore(concept['name'])

# 生成检验白板进行复现
generate_review_canvas_for_cluster(high_cluster)
```

---

#### 🟡 Medium级别 (≥70分)

**特征**:
- 基本理解
- 但复习次数过多（>3次）
- 可能存在记忆问题

**复习策略**:
1. **安排复习**，优先级中等
2. 调用**memory-anchor** Agent生成记忆锚点（类比、故事、口诀）
3. 调用**four-level-explanation** Agent获取渐进式解释
4. 重点关注**长期记忆**和**应用迁移**
5. 适当间隔复习（艾宾浩斯曲线）

**示例行动**:
```python
# 对Medium社区进行巩固学习
for concept in medium_cluster['concepts']:
    # 1. 记忆锚点
    memory_aid = call_memory_anchor_agent(concept['name'])

    # 2. 四层次解释（从专家层开始）
    four_level = call_four_level_explanation_agent(concept['name'], start_level='expert')

    # 3. 应用练习
    practice_application(concept['name'])

# 间隔复习
schedule_spaced_repetition(medium_cluster, interval_days=7)
```

---

### 按社区整体复习的策略

**核心原则**: **同一社区的概念应该一起复习**

#### 步骤1: 识别社区的核心主题

```python
# 分析社区概念的共同点
common_theme = analyze_cluster_theme(cluster['concepts'])
print(f"社区主题: {common_theme}")

# 示例输出
# 社区主题: "命题逻辑的推理规则"（包含逆否命题、充分必要条件、逻辑等价）
```

#### 步骤2: 从核心概念开始复习

```python
# 1. 找到社区的核心概念（分数最高或最基础的概念）
core_concept = find_core_concept(cluster['concepts'])

# 2. 先彻底理解核心概念
deep_learn_concept(core_concept)

# 3. 逐步扩展到关联概念
for related_concept in cluster['concepts']:
    if related_concept != core_concept:
        learn_with_connection(related_concept, core_concept)
```

#### 步骤3: 构建概念间的关联网络

```python
# 使用对比表理解概念间的关系
comparison_table = call_comparison_table_agent(cluster['concepts'])

# 绘制概念关系图
draw_concept_map(cluster['concepts'], relationships)
```

#### 步骤4: 整体检验

```python
# 生成社区检验白板
review_canvas = generate_cluster_review_canvas(cluster)

# 在检验白板上复现知识网络
reproduce_knowledge_network(review_canvas)
```

---

### 跨社区复习顺序

如果识别出多个社区，建议按以下顺序复习：

1. **Urgent社区** → **High社区** → **Medium社区** （按紧急度）
2. **小社区** → **大社区** （先突破小社区建立信心）
3. **基础社区** → **高级社区** （先掌握基础概念）

**示例复习计划**:

```python
clusters = result['clusters']

# 1. 按紧急度排序
urgent_clusters = [c for c in clusters if c['recommended_review_urgency'] == 'urgent']
high_clusters = [c for c in clusters if c['recommended_review_urgency'] == 'high']
medium_clusters = [c for c in clusters if c['recommended_review_urgency'] == 'medium']

# 2. 在每个紧急度内，按社区大小排序（小→大）
urgent_clusters.sort(key=lambda c: c['cluster_size'])
high_clusters.sort(key=lambda c: c['cluster_size'])
medium_clusters.sort(key=lambda c: c['cluster_size'])

# 3. 执行复习
for cluster in urgent_clusters:
    review_cluster_deeply(cluster)

for cluster in high_clusters:
    review_cluster_systematically(cluster)

for cluster in medium_clusters:
    review_cluster_lightly(cluster)
```

---

## 常见问题

### Q1: 为什么某些概念被聚类到一起？

**A**: Leiden算法基于Canvas中的**关系边（edges）**进行社区检测。如果两个概念被聚类到同一社区，说明：

1. 它们在Canvas中有直接或间接的关系边连接
2. 它们在知识网络中处于同一个"社区结构"
3. 它们通常具有知识依赖关系或语义相似性

**示例**: "逆否命题"和"充分必要条件"被聚类到一起，是因为它们都涉及命题逻辑的推理规则，且在Canvas中存在关联边。

---

### Q2: 为什么有些薄弱概念没有被聚类？

**A**: 可能的原因：

1. **孤立节点**: 该概念在Canvas中没有与其他薄弱概念建立关系边
2. **阈值过滤**: 该概念的分数≥70且复习次数≤3，不满足薄弱概念条件
3. **社区太小**: Leiden算法可能过滤掉了社区大小=1的孤立概念

**解决方法**: 调整`min_weak_score`和`min_review_count`参数，或手动为孤立概念建立关系边。

---

### Q3: 如何调整薄弱点阈值？

**A**: 根据个人学习水平调整参数：

```python
# 严格模式（适合追求高分的学生）
result = trigger_weak_point_clustering(
    canvas_path="path/to/canvas.canvas",
    min_weak_score=80,      # 80分以下视为薄弱
    min_review_count=2      # 复习2次以上就需要关注
)

# 宽松模式（适合初学者）
result = trigger_weak_point_clustering(
    canvas_path="path/to/canvas.canvas",
    min_weak_score=60,      # 60分以下视为薄弱
    min_review_count=5      # 复习5次以上才需要重点关注
)
```

---

### Q4: 如何在Obsidian Canvas中可视化社区？

**A**: 当前版本的薄弱点聚类功能返回JSON结果，暂不支持自动在Canvas中标记社区。

**未来规划** (Story GDS.1 - Subtask 3.2):
- 自动为同一社区的节点添加相同颜色标记
- 在检验白板中按社区分组布局
- 添加社区分隔符或分组标识

**当前手动方法**:
1. 根据JSON结果手动为同一社区的节点添加相同颜色
2. 使用Obsidian Canvas的分组功能（Groups）将同一社区节点分组
3. 在Canvas中添加文本节点标注社区信息

---

### Q5: 为什么复习紧急度评估结果与我的预期不同？

**A**: 复习紧急度基于**社区平均分数**计算，而非单个概念分数：

- **Cluster Score** = 社区内所有概念分数的平均值
- **Urgency** = f(Cluster Score)

**示例**:
```python
# 社区A: 包含3个概念
concepts = [
    {"name": "概念1", "score": 55},  # Urgent
    {"name": "概念2", "score": 68},  # High
    {"name": "概念3", "score": 72}   # Medium
]

# Cluster Score = (55 + 68 + 72) / 3 = 65.0
# Urgency = "high" (60-69范围)
```

即使社区包含一个urgent概念（55分），但整体评估为"high"，因为平均分为65分。

**如何理解**:
- 紧急度评估是**社区整体水平**，而非单个概念
- 如果需要关注单个概念，可以查看`concepts`列表中的`score`字段

---

### Q6: Leiden算法的参数如何影响聚类结果？

**A**: 默认参数（不可在用户API中修改，仅供理解）:

| 参数 | 默认值 | 含义 | 影响 |
|------|-------|------|------|
| `gamma` | 1.0 | 分辨率参数 | 越大→社区越小越多 |
| `tolerance` | 0.0001 | 收敛阈值 | 越小→精度越高 |
| `randomSeed` | 42 | 随机种子 | 固定值→结果可重复 |

**示例**:
- `gamma=0.5`: 识别更大的社区（更宽泛的关联）
- `gamma=2.0`: 识别更小的社区（更紧密的关联）

**当前版本**: 参数已在代码中优化为最佳值，用户无需调整。

---

## 附录: 示例输出

### 示例1: 离散数学薄弱点聚类

**输入**:
```python
result = trigger_weak_point_clustering(
    canvas_path="笔记库/离散数学/离散数学.canvas",
    min_weak_score=70,
    min_review_count=3
)
```

**输出**:
```
薄弱点聚类结果
============================================================
触发点: 4
触发点名称: 薄弱点聚类
薄弱概念总数: 8
社区总数: 3
时间戳: 2025-11-14T12:30:45.123456

社区详情:

社区 1:
  - ID: 42
  - 平均分数: 65.0
  - 社区大小: 3
  - 复习紧急度: high
  - 概念列表:
    * 逆否命题 (分数: 65, 复习: 4次)
    * 充分必要条件 (分数: 68, 复习: 3次)
    * 逻辑等价 (分数: 62, 复习: 5次)

社区 2:
  - ID: 108
  - 平均分数: 55.0
  - 社区大小: 2
  - 复习紧急度: urgent
  - 概念列表:
    * 真值表 (分数: 55, 复习: 6次)
    * 合取范式 (分数: 55, 复习: 7次)

社区 3:
  - ID: 217
  - 平均分数: 72.0
  - 社区大小: 3
  - 复习紧急度: medium
  - 概念列表:
    * 集合运算 (分数: 75, 复习: 4次)
    * 笛卡尔积 (分数: 70, 复习: 4次)
    * 幂集 (分数: 71, 复习: 5次)
============================================================
```

**复习建议**:

1. **立即复习社区2**（urgent）- 真值表、合取范式（命题逻辑的表示方法）
2. **尽快复习社区1**（high）- 逆否命题、充分必要条件、逻辑等价（命题逻辑的推理规则）
3. **安排复习社区3**（medium）- 集合运算、笛卡尔积、幂集（集合论基础）

---

## 相关文档

- [Neo4j GDS Leiden算法参数调优](../technical-guides/neo4j-gds-leiden-parameters.md)
- [艾宾浩斯复习系统架构](../architecture/ebbinghaus-review-system.md)
- [Canvas学习系统用户指南](./canvas-learning-system-guide.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-14
**Story**: GDS.1 - Subtask 4.1
