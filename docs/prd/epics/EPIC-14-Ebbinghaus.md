# Epic 14: 艾宾浩斯复习系统迁移+UI集成

**版本**: 1.0 (从PRD v1.1.8提取)
**创建日期**: 2025-11-21
**Epic性质**: 🔄 **迁移+集成+3层记忆整合** (基于已有ebbinghaus_review.py 870行代码)
**预计时间**: 5.5-8周 (含v1.1.8检验历史关联增强功能)

---

## 背景说明

### 已有实现
`ebbinghaus_review.py` (870行, 2025-01-22完成)
- ✅ SQLite数据库 (3表: review_schedules, review_history, user_review_stats)
- ✅ 经典艾宾浩斯遗忘曲线算法 R(t)=e^(-t/S)
- ✅ 基础CRUD操作 (添加概念、查询到期、更新复习记录)

### 本Epic目标 (v1.1.6扩展)
1. **算法升级**: 从经典公式迁移到Py-FSRS (准确性提升20-30%)
2. **Obsidian UI集成**: 创建侧边栏复习面板 (基于FR3.3 Mockup)
3. **FastAPI接口封装**: 将Python函数封装为REST API
4. **LangGraph集成**: 复习推送接入LangGraph Supervisor路由
5. **⭐ v1.1.6新增: 3层记忆系统数据整合**
   - 集成Temporal Memory学习行为数据
   - 集成Graphiti概念关系网络
   - 集成Semantic Memory文档交互数据
   - 实现多维度优先级计算（4维度综合评分）
   - 实现行为监控触发机制（触发点4）
   - 实现FSRS参数自适应优化

---

## 迁移策略

```python
# 阶段1: 保留现有SQLite schema,新增Py-FSRS字段 (向后兼容)
ALTER TABLE review_schedules ADD COLUMN fsrs_card_json TEXT;  # 存储FSRSCard序列化

# 阶段2: 双算法并行运行 (1周观察期)
if USE_FSRS_ALGORITHM:
    card = fsrs.review_card(card, rating)  # 使用Py-FSRS
else:
    retention_rate = calculate_retention_rate(time_elapsed, memory_strength)  # 经典公式

# 阶段3: 完全切换到Py-FSRS (保留经典算法作为fallback)
```

---

## Story列表 (15个)

### Phase 1: 核心迁移 (Story 14.1-14.8)

| Story ID | Story名称 | 预计时间 | 说明 |
|----------|----------|---------|------|
| 14.1 | Py-FSRS算法迁移 | 2-3天 | 数据库扩展、双算法A/B测试 |
| 14.2 | FastAPI接口封装 | 1-2天 | REST API endpoints |
| 14.3 | 复习面板视图 | 3-4天 | Obsidian侧边栏UI |
| 14.4 | 今日复习列表与交互 | 2-3天 | 按钮、右键菜单 |
| 14.5 | 一键生成检验白板集成 + 复习模式选择 | 1.5天 | fresh/targeted模式 |
| 14.6 | 复习历史查看 + 多次检验趋势分析 | 1.5-2.5天 | 图表、趋势分析 |
| 14.7 | 复习提醒通知 | 1天 | Obsidian Notice API |
| 14.8 | 复习统计图表 | 2天 | Chart.js可视化 |

### Phase 2: 3层记忆整合 (Story 14.9-14.12) - v1.1.6新增

| Story ID | Story名称 | 预计时间 | 说明 |
|----------|----------|---------|------|
| 14.9 | 3层记忆系统查询工具集成 | 2-3天 | 4个新查询工具 |
| 14.10 | 行为监控触发机制（触发点4） | 3-4天 | 定时扫描、自动添加 |
| 14.11 | 多维度优先级计算 | 2天 | 4维度综合评分 |
| 14.12 | FSRS参数优化功能（FR3.6） | 3-4天 | 梯度下降优化 |

### Phase 3: 检验历史关联增强 (Story 14.13-14.15) - v1.1.8新增

| Story ID | Story名称 | 预计时间 | 说明 |
|----------|----------|---------|------|
| 14.13 | 检验历史记录存储到Graphiti | 2天 | 关系持久化 |
| 14.14 | 针对性复习问题生成算法 | 3天 | 智能权重计算 |
| 14.15 | 复习模式选择UI组件 | 1.5天 | Settings + Modal |

---

## Story详细说明

### Story 14.1: Py-FSRS算法迁移 (2-3天)
- 数据库schema扩展 (新增fsrs_card_json列)
- FSRSCard <-> SQLite序列化/反序列化
- 双算法A/B测试框架
- 数据迁移脚本 (历史复习记录转换)

### Story 14.2: FastAPI接口封装 (1-2天)
- POST /api/review/add-concept
- GET /api/review/today-summary
- POST /api/review/complete
- GET /api/review/history

### Story 14.3: 复习面板视图 (Obsidian Plugin) (3-4天)
- 侧边栏View注册
- Canvas卡片列表渲染 (基于FR3.3 Mockup)
- 紧急程度样式 (urgent/high/medium/low)
- 响应式布局

### Story 14.4: 今日复习列表与交互 (2-3天)
- "开始复习"按钮 → 调用generate_review_canvas_file()
- "推迟1天"按钮 → 调整Card.due时间
- 右键菜单 ("标记为已掌握" / "重置进度")
- Canvas卡片点击 → 打开原白板

### Story 14.5: 一键生成检验白板集成 + 复习模式选择 (1.5天) ✅ v1.1.8扩展
- 复用Epic 4已有generate_review_canvas_file()
- 传入Canvas文件路径和到期概念列表
- **[v1.1.8新增] 支持mode参数**: "fresh" (全新检验) 或 "targeted" (针对性复习)
  - "fresh"模式: 不使用历史数据，盲测式检验
  - "targeted"模式: 调用query_review_history_from_graphiti()和calculate_targeted_review_weights()
- **[v1.1.8新增] 生成时存储关系**: 创建(review)-[:GENERATED_FROM]->(original)到Graphiti

### Story 14.6: 复习历史查看 + 多次检验趋势分析 (1.5-2.5天) ✅ v1.1.8扩展
- 历史记录列表 (最近7天/30天切换)
- 每日复习统计图表 (复习概念数、平均评分)
- 单个概念的复习轨迹查看
- **[v1.1.8新增] 同一原白板的多次检验趋势图表**:
  - 调用analyze_multi_review_progress(original_canvas_path)
  - 显示每次检验的通过率曲线 (折线图)
  - 显示薄弱概念的改善趋势 (柱状图)
  - 显示整体进步率 (百分比+趋势箭头)
- **[v1.1.8新增] 检验模式标签**: 历史记录显示"全新检验"或"针对性复习"徽章

### Story 14.9: 3层记忆系统查询工具集成 (2-3天) - v1.1.6新增
实现4个新查询工具:
- `query_temporal_learning_behavior(filter_type, ...)` - 查询时序学习行为数据
- `query_graphiti_concept_network(analysis_type, ...)` - 查询概念关系网络
- `query_semantic_document_interactions(pattern, ...)` - 查询文档交互模式
- `track_learning_behavior(operation_type, ...)` - 记录学习行为数据

### Story 14.10: 行为监控触发机制（触发点4）(3-4天) - v1.1.6新增
- **背景**: 现有触发点1-3仅被动响应用户操作，无法主动检测"长期未访问的已掌握概念"
- **目标**: 实现每日凌晨2:00自动扫描3层记忆系统
- 实现定时任务调度器 (Cron: `0 2 * * *`)
- 实现3个检测条件:
  - **条件1 (Temporal)**: 已掌握但7天未访问的概念
  - **条件2 (Graphiti)**: 前置概念已掌握但后续概念长期未学的知识断层
  - **条件3 (Semantic)**: 相关文档频繁访问但概念本身未复习的隐性需求

### Story 14.11: 多维度优先级计算 (2天) - v1.1.6新增
```python
def calculate_multidimensional_priority(concept_id: str) -> float:
    # 维度1: FSRS紧迫性 (40%)
    fsrs_urgency = calculate_fsrs_urgency(concept_id)

    # 维度2: 行为权重 (30%) - 从Temporal Memory
    behavior_weight = calculate_behavior_weight(...)

    # 维度3: 网络中心性 (20%) - 从Graphiti
    network_centrality = calculate_network_centrality(...)

    # 维度4: 交互权重 (10%) - 从Semantic Memory
    interaction_weight = calculate_interaction_weight(...)

    return (
        fsrs_urgency * 0.4 +
        behavior_weight * 0.3 +
        network_centrality * 0.2 +
        interaction_weight * 0.1
    )
```

### Story 14.12: FSRS参数优化功能（FR3.6）(3-4天) - v1.1.6新增
- 从Temporal Memory提取历史复习记录
- 使用梯度下降优化17个FSRS参数
- A/B测试框架对比默认/优化参数
- 定期优化任务（每月1日凌晨3:00触发）

### Story 14.13: 检验历史记录存储到Graphiti (2天) - ✅ v1.1.8新增
```python
def store_review_canvas_relationship(
    review_canvas_path: str,
    original_canvas_path: str,
    mode: str,  # "fresh" | "targeted"
    results: Dict
):
    """将检验白板关系存储到Graphiti"""
    # 创建Cypher查询
    cypher = """
    MATCH (original:Canvas {path: $original_path})
    CREATE (review:ReviewCanvas {...})
    CREATE (review)-[:GENERATED_FROM $relationship_data]->(original)
    """
```

### Story 14.14: 针对性复习问题生成算法 (3天) - ✅ v1.1.8新增
```python
def calculate_targeted_review_weights(
    weak_concepts: List[str],
    mastered_concepts: List[str],
    config: Dict = None
) -> List[Tuple[str, float]]:
    """计算针对性复习的概念权重

    默认配置: {"weak_ratio": 0.7, "mastered_ratio": 0.3}
    - 70%薄弱概念（最近失败的权重最高）
    - 30%已掌握概念（防止遗忘）
    """
```

### Story 14.15: 复习模式选择UI组件 (1.5天) - ✅ v1.1.8新增
- Settings面板选项（默认复习模式）
- Modal对话框（临时覆盖）
- 徽章显示（历史记录中显示模式）

---

## 工作量估算

| 版本 | 估算时间 | 说明 |
|------|---------|------|
| 原估算 (新开发) | 6-8周 | - |
| v1.1.6调整 (迁移+UI) | 2-4周 | 代码复用率~70% |
| v1.1.6新增 (14.9-14.12) | 2-2.5周 | 3层记忆整合 |
| v1.1.8新增 (14.13-14.15) | +1.5周 | 检验历史关联 |
| **总估算 (v1.1.8)** | **5.5-8周** | 完整功能 |

---

**文档结束**

**提取来源**: PRD v1.1.8 (Lines 6114-6498)
**提取日期**: 2025-11-21
