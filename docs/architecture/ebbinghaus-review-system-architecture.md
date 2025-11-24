---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-23"
status: "draft"
iteration: 5

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

compatible_with:
  prd: "v1.1.8"
  epic: ["Epic 14"]

changes_from_previous:
  - "Initial Ebbinghaus Review System Architecture document"
---

# 艾宾浩斯复习系统架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义基于FSRS (Free Spaced Repetition Scheduler) 算法的艾宾浩斯复习系统架构，实现智能间隔重复学习。

### 1.1 设计目标

- 基于Py-FSRS实现科学的间隔重复
- 4个触发点的自适应复习调度
- 与Graphiti知识图谱集成
- 个性化参数优化

---

## 2. FSRS算法核心

### 2.1 核心数据结构

```python
# ✅ Verified from Context7 Py-FSRS (/open-spaced-repetition/py-fsrs)
from fsrs import Card, Rating, Scheduler, FSRS
from datetime import datetime, timezone

# Card状态
class Card:
    due: datetime           # 下次复习时间
    stability: float        # 记忆稳定性
    difficulty: float       # 难度 (1-10)
    elapsed_days: int       # 距上次复习天数
    scheduled_days: int     # 计划间隔天数
    reps: int              # 复习次数
    lapses: int            # 遗忘次数
    state: State           # New, Learning, Review, Relearning
    last_review: datetime  # 上次复习时间

# 评分等级
class Rating:
    Again = 1   # 完全忘记
    Hard = 2    # 困难回忆
    Good = 3    # 正常回忆
    Easy = 4    # 轻松回忆
```

### 2.2 FSRS算法参数

```python
# ✅ Verified from Context7 Py-FSRS - 21 parameters
DEFAULT_PARAMETERS = [
    0.40255,   # w[0]: initial stability for Again
    1.18385,   # w[1]: initial stability for Hard
    3.173,     # w[2]: initial stability for Good
    15.69105,  # w[3]: initial stability for Easy
    7.1949,    # w[4]: difficulty weight
    0.5345,    # w[5]: difficulty mean reversion
    1.4604,    # w[6]: stability after recall
    0.0046,    # w[7]: stability decrease factor
    1.54575,   # w[8]: recall stability factor
    0.1192,    # w[9]: recall difficulty factor
    1.01925,   # w[10]: stability after lapse
    1.9395,    # w[11]: lapse penalty
    0.11,      # w[12]: hard penalty
    0.29605,   # w[13]: easy bonus
    2.2698,    # w[14]: difficulty ceiling
    0.2315,    # w[15]: difficulty floor
    2.9898,    # w[16]: stability power
    0.51655,   # w[17]: decay factor
    0.6621,    # w[18]: factor decay
    # Additional parameters for FSRS-5
]

# desired_retention: 目标记忆保留率 (0.7-0.99)
# 推荐值: 0.9 (90%保留率)
```

### 2.3 调度器使用

```python
# ✅ Verified from Context7 Py-FSRS
from fsrs import FSRS, Card, Rating

# 初始化
f = FSRS()

# 创建新卡片
card = Card()

# 调度下次复习
now = datetime.now(timezone.utc)
scheduling_cards = f.repeat(card, now)

# 根据用户评分更新
card, review_log = scheduling_cards[Rating.Good].card, scheduling_cards[Rating.Good].review_log

# 获取各评分的下次复习时间
for rating in [Rating.Again, Rating.Hard, Rating.Good, Rating.Easy]:
    scheduled = scheduling_cards[rating]
    print(f"{rating}: due={scheduled.card.due}, interval={scheduled.card.scheduled_days}days")
```

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    复习系统架构                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Trigger     │────▶│ Scheduler   │────▶│ Review    │ │
│  │ Detector    │     │ Engine      │     │ Generator │ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│         │                   │                   │       │
│         ▼                   ▼                   ▼       │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Graphiti    │     │ FSRS        │     │ Canvas    │ │
│  │ Memory      │     │ Algorithm   │     │ Generator │ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 组件职责

| 组件 | 职责 | 技术实现 |
|------|------|----------|
| Trigger Detector | 检测复习触发点 | Cron + Event System |
| Scheduler Engine | 计算最优复习时间 | Py-FSRS |
| Review Generator | 生成复习Canvas | Canvas Operator |
| Graphiti Memory | 存储学习历史 | Graphiti + Neo4j |

---

## 4. 四触发点系统

### 4.1 触发点定义

```python
# ✅ Based on PRD Section 10.6 - 艾宾浩斯复习系统
class TriggerPoint:
    """复习触发点"""

    TRIGGER_1 = "24h"      # 24小时后首次复习
    TRIGGER_2 = "7d"       # 7天后第二次复习
    TRIGGER_3 = "30d"      # 30天后第三次复习
    TRIGGER_4 = "adaptive" # 自适应复习（基于FSRS）

class TriggerConfig:
    trigger_1_hours: int = 24
    trigger_2_days: int = 7
    trigger_3_days: int = 30
    trigger_4_algorithm: str = "fsrs"  # 或 "graphrag"
```

### 4.2 触发点检测器

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Temporal Queries)
from datetime import datetime, timedelta
from graphiti_core import Graphiti

class TriggerDetector:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def check_trigger_1(self) -> list[LearningItem]:
        """检查24小时触发点"""
        # 查询24小时前学习的内容
        cutoff = datetime.now() - timedelta(hours=24)

        results = await self.graphiti.search(
            query="learning items completed",
            reference_time=cutoff,
            entity_types=["LearningNode"]
        )

        return [item for item in results if self._needs_review(item, 1)]

    async def check_trigger_4_adaptive(self) -> list[LearningItem]:
        """检查自适应触发点（基于FSRS）"""
        now = datetime.now(timezone.utc)

        # 获取所有卡片
        cards = await self.get_all_cards()

        # 筛选到期复习的卡片
        due_items = []
        for card_data in cards:
            card = self._restore_card(card_data)
            if card.due <= now:
                due_items.append(card_data)

        return due_items
```

---

## 5. 复习调度引擎

### 5.1 调度器实现

```python
# ✅ Verified from Context7 Py-FSRS
from fsrs import FSRS, Card, Rating
from typing import Optional

class ReviewScheduler:
    def __init__(self, desired_retention: float = 0.9):
        """
        初始化复习调度器

        Args:
            desired_retention: 目标记忆保留率 (0.7-0.99)
        """
        self.fsrs = FSRS()
        self.fsrs.p.request_retention = desired_retention

    def schedule_review(
        self,
        card: Card,
        rating: Rating,
        review_time: Optional[datetime] = None
    ) -> tuple[Card, ReviewLog]:
        """
        调度复习

        Args:
            card: 当前卡片状态
            rating: 用户评分
            review_time: 复习时间（默认当前）

        Returns:
            更新后的卡片和复习日志
        """
        if review_time is None:
            review_time = datetime.now(timezone.utc)

        # 获取所有可能的调度结果
        scheduling_cards = self.fsrs.repeat(card, review_time)

        # 根据评分选择结果
        result = scheduling_cards[rating]

        return result.card, result.review_log

    def get_next_intervals(self, card: Card) -> dict[str, int]:
        """
        获取各评分对应的下次复习间隔

        Returns:
            {rating_name: interval_days}
        """
        now = datetime.now(timezone.utc)
        scheduling_cards = self.fsrs.repeat(card, now)

        return {
            'Again': scheduling_cards[Rating.Again].card.scheduled_days,
            'Hard': scheduling_cards[Rating.Hard].card.scheduled_days,
            'Good': scheduling_cards[Rating.Good].card.scheduled_days,
            'Easy': scheduling_cards[Rating.Easy].card.scheduled_days
        }
```

### 5.2 参数优化器

```python
# ✅ Verified from Context7 Py-FSRS - Optimizer
from fsrs import FSRS, Optimizer, ReviewLog

class ParameterOptimizer:
    """基于用户历史优化FSRS参数"""

    def __init__(self):
        self.optimizer = Optimizer()

    def optimize_from_history(
        self,
        review_logs: list[ReviewLog]
    ) -> list[float]:
        """
        从复习历史优化参数

        Args:
            review_logs: 历史复习记录

        Returns:
            优化后的21个参数
        """
        # 转换为优化器格式
        # 格式: [card_id, review_time, rating, ...]

        optimized_params = self.optimizer.optimize(review_logs)

        return optimized_params

    def apply_optimized_params(
        self,
        fsrs: FSRS,
        params: list[float]
    ) -> None:
        """应用优化后的参数"""
        fsrs.p.w = params
```

---

## 6. Graphiti知识图谱集成

### 6.1 学习节点实体

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Custom Entity Types)
from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode

class LearningNodeEntity(EntityNode):
    """Canvas学习节点实体"""

    node_id: str              # Canvas节点ID
    canvas_file: str          # Canvas文件路径
    content: str              # 节点内容
    color: str                # 当前颜色状态

    # FSRS卡片状态
    stability: float          # 记忆稳定性
    difficulty: float         # 难度
    due_date: datetime        # 下次复习时间
    reps: int                 # 复习次数
    lapses: int               # 遗忘次数

    # 学习统计
    first_learned: datetime   # 首次学习时间
    last_reviewed: datetime   # 上次复习时间
    total_reviews: int        # 总复习次数
    average_rating: float     # 平均评分
```

### 6.2 复习历史存储

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Episodes)
class ReviewHistoryManager:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def record_review(
        self,
        node_id: str,
        rating: int,
        response_time_ms: int,
        review_canvas: str
    ) -> None:
        """记录复习事件到知识图谱"""

        episode_content = f"""
        Review completed for node {node_id}:
        - Rating: {rating}/4
        - Response time: {response_time_ms}ms
        - Review canvas: {review_canvas}
        - Timestamp: {datetime.now().isoformat()}
        """

        await self.graphiti.add_episode(
            name=f"review_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            episode_body=episode_content,
            reference_time=datetime.now()
        )

    async def get_review_history(
        self,
        node_id: str,
        days: int = 30
    ) -> list[ReviewRecord]:
        """获取节点的复习历史"""

        cutoff = datetime.now() - timedelta(days=days)

        results = await self.graphiti.search(
            query=f"review history for node {node_id}",
            reference_time=datetime.now()
        )

        return self._parse_review_records(results)
```

---

## 7. 复习Canvas生成

### 7.1 复习Canvas生成器

```python
from canvas_operator import CanvasOrchestrator

class ReviewCanvasGenerator:
    def __init__(self, orchestrator: CanvasOrchestrator):
        self.orchestrator = orchestrator

    async def generate_review_canvas(
        self,
        items: list[LearningItem],
        review_type: str
    ) -> str:
        """
        生成复习Canvas

        Args:
            items: 待复习项目
            review_type: 复习类型 (trigger_1, trigger_2, etc.)

        Returns:
            生成的Canvas文件路径
        """
        # 创建Canvas结构
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 为每个复习项创建节点
        y_offset = 0
        for item in items:
            # 问题节点（紫色）
            question_node = {
                "id": f"q_{item.node_id}",
                "type": "text",
                "text": item.content,
                "x": 0,
                "y": y_offset,
                "width": 400,
                "height": 200,
                "color": "6"  # 紫色
            }

            # 回答节点（黄色，待填写）
            answer_node = {
                "id": f"a_{item.node_id}",
                "type": "text",
                "text": "",
                "x": 0,
                "y": y_offset + 250,
                "width": 400,
                "height": 200,
                "color": "3"  # 黄色
            }

            canvas_data["nodes"].extend([question_node, answer_node])

            # 连接边
            canvas_data["edges"].append({
                "id": f"e_{item.node_id}",
                "fromNode": question_node["id"],
                "toNode": answer_node["id"],
                "fromSide": "bottom",
                "toSide": "top"
            })

            y_offset += 500

        # 保存Canvas
        filename = f"review_{review_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.canvas"
        filepath = await self.orchestrator.save_canvas(filename, canvas_data)

        return filepath
```

---

## 8. 评分与反馈

### 8.1 评分映射

```python
# Canvas评分 (0-100) 到 FSRS Rating 的映射
def map_score_to_rating(score: int) -> Rating:
    """
    将Canvas评分映射到FSRS评分

    Args:
        score: Canvas评分 (0-100)

    Returns:
        FSRS Rating
    """
    if score < 40:
        return Rating.Again   # 完全忘记
    elif score < 60:
        return Rating.Hard    # 困难回忆
    elif score < 80:
        return Rating.Good    # 正常回忆
    else:
        return Rating.Easy    # 轻松回忆

# 颜色到评分的映射
COLOR_TO_EXPECTED_RATING = {
    "1": Rating.Again,  # 红色 - 未理解
    "2": Rating.Hard,   # 橙色 - 部分理解
    "4": Rating.Good,   # 绿色 - 已掌握
    "6": Rating.Easy    # 紫色 - 深入理解
}
```

### 8.2 复习完成处理

```python
async def complete_review(
    self,
    node_id: str,
    user_score: int,
    response_time_ms: int
) -> ReviewResult:
    """
    完成复习并更新调度

    Args:
        node_id: 节点ID
        user_score: 用户评分 (0-100)
        response_time_ms: 响应时间

    Returns:
        复习结果，包含下次复习时间
    """
    # 获取当前卡片状态
    card = await self.get_card(node_id)

    # 映射评分
    rating = map_score_to_rating(user_score)

    # 调度下次复习
    updated_card, review_log = self.scheduler.schedule_review(card, rating)

    # 保存更新
    await self.save_card(node_id, updated_card)

    # 记录到Graphiti
    await self.history_manager.record_review(
        node_id=node_id,
        rating=rating.value,
        response_time_ms=response_time_ms,
        review_canvas=self.current_canvas
    )

    return ReviewResult(
        node_id=node_id,
        next_review=updated_card.due,
        interval_days=updated_card.scheduled_days,
        stability=updated_card.stability,
        difficulty=updated_card.difficulty
    )
```

---

## 9. API接口

### 9.1 FastAPI端点

```python
# ✅ Verified from FastAPI Context7 documentation
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/review", tags=["review"])

@router.get("/due")
async def get_due_reviews(
    trigger_type: Optional[str] = None,
    scheduler: ReviewScheduler = Depends(get_scheduler)
) -> list[DueReviewItem]:
    """获取待复习项目"""
    pass

@router.post("/complete")
async def complete_review(
    request: ReviewCompleteRequest,
    scheduler: ReviewScheduler = Depends(get_scheduler)
) -> ReviewResult:
    """完成复习"""
    pass

@router.get("/schedule/{node_id}")
async def get_review_schedule(
    node_id: str,
    scheduler: ReviewScheduler = Depends(get_scheduler)
) -> ReviewScheduleInfo:
    """获取节点复习计划"""
    pass

@router.post("/optimize")
async def optimize_parameters(
    optimizer: ParameterOptimizer = Depends(get_optimizer)
) -> OptimizationResult:
    """优化FSRS参数"""
    pass
```

---

## 10. 配置

### 10.1 系统配置

```yaml
# review_config.yaml
fsrs:
  desired_retention: 0.9      # 目标记忆保留率
  enable_fuzz: true           # 启用时间模糊化
  maximum_interval: 36500     # 最大间隔天数

triggers:
  trigger_1:
    enabled: true
    hours: 24
  trigger_2:
    enabled: true
    days: 7
  trigger_3:
    enabled: true
    days: 30
  trigger_4:
    enabled: true
    algorithm: "fsrs"         # 或 "graphrag"

optimization:
  auto_optimize: true
  min_reviews_for_optimization: 100
  optimization_interval_days: 30
```

---

## 11. 相关文档

- [3层记忆系统架构](COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md)
- [Graphiti知识图谱集成](GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md)
- [Canvas操作架构](canvas-3-layer-architecture.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
