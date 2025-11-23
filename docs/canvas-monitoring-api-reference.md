# Canvas监控系统 API参考文档

**文档版本**: v1.0
**最后更新**: 2025-11-02
**适用版本**: Canvas Learning System v1.1
**作者**: Canvas Learning System Dev Team

---

## 目录

1. [概述](#概述)
2. [数据存储API](#数据存储api)
3. [查询接口](#查询接口)
4. [回调接口](#回调接口)
5. [健康检查API](#健康检查api)
6. [错误处理](#错误处理)
7. [性能指标](#性能指标)

---

## 概述

Canvas监控系统提供了一套完整的API用于：
- **数据存储**: 记录Canvas学习事件到热数据存储和冷数据存储
- **数据查询**: 查询学习历史、统计数据、趋势分析
- **回调机制**: 监听Canvas变更事件，触发自定义处理逻辑
- **系统监控**: 检查系统健康状态、性能指标

**核心组件**:
- `HotDataStore`: 热数据存储（内存 + JSON文件）
- `ColdDataStore`: 冷数据存储（SQLite数据库）
- `AsyncCanvasProcessor`: 异步Canvas处理器
- `LearningAnalyzer`: 学习数据分析器

---

## 数据存储API

### HotDataStore

热数据存储，基于内存+JSON文件，用于最近7天的学习数据。

#### 初始化

```python
from canvas_progress_tracker.data_stores import HotDataStore

# 创建HotDataStore实例
hot_store = HotDataStore(
    data_dir="path/to/data",  # 数据目录（默认: .learning_sessions/）
    retention_days=7           # 数据保留天数（默认: 7天）
)
```

#### 方法列表

##### `add_event(event_data: dict) -> None`

添加学习事件到热数据存储。

**参数**:
- `event_data` (dict): 学习事件数据，必需字段：
  - `canvas_id` (str): Canvas文件ID
  - `event_type` (str): 事件类型（canvas_change, node_added, color_changed, etc.）
  - `timestamp` (str): 时间戳（ISO 8601格式）
  - `node_id` (str, optional): 节点ID
  - `changes` (dict, optional): 变更详情

**示例**:
```python
event = {
    "canvas_id": "离散数学",
    "event_type": "node_color_changed",
    "timestamp": "2025-11-02T14:30:00",
    "node_id": "node-1234",
    "changes": {
        "old_color": "1",  # 红色
        "new_color": "3"   # 紫色
    }
}
hot_store.add_event(event)
```

**返回**: None

**异常**:
- `ValueError`: 如果event_data缺少必需字段

---

##### `get_events(canvas_id: str = None, days: int = 7) -> List[dict]`

获取学习事件列表。

**参数**:
- `canvas_id` (str, optional): Canvas文件ID，如果为None则返回所有Canvas的事件
- `days` (int): 查询最近N天的数据（默认: 7）

**返回**:
- `List[dict]`: 学习事件列表，按时间倒序排列

**示例**:
```python
# 获取所有Canvas的最近7天事件
all_events = hot_store.get_events()

# 获取特定Canvas的事件
math_events = hot_store.get_events(canvas_id="离散数学", days=3)
```

---

##### `get_statistics(canvas_id: str = None, days: int = 7) -> dict`

获取统计数据。

**参数**:
- `canvas_id` (str, optional): Canvas文件ID
- `days` (int): 统计最近N天的数据

**返回**:
- `dict`: 统计数据，包含：
  - `total_events` (int): 总事件数
  - `events_by_type` (dict): 按事件类型分组的计数
  - `color_transitions` (dict): 颜色流转统计
  - `daily_activity` (list): 每日活跃度

**示例**:
```python
stats = hot_store.get_statistics(canvas_id="离散数学", days=7)
print(f"总事件数: {stats['total_events']}")
print(f"颜色流转: {stats['color_transitions']}")
```

---

##### `cleanup_old_data() -> int`

清理超过保留期的旧数据。

**返回**:
- `int`: 删除的事件数量

**示例**:
```python
deleted_count = hot_store.cleanup_old_data()
print(f"已清理 {deleted_count} 个旧事件")
```

---

### ColdDataStore

冷数据存储，基于SQLite数据库，用于长期存储所有学习数据。

#### 初始化

```python
from canvas_progress_tracker.data_stores import ColdDataStore

# 创建ColdDataStore实例
cold_store = ColdDataStore(
    db_path="path/to/canvas_learning.db"  # 数据库文件路径
)
```

#### 方法列表

##### `add_event(event_data: dict) -> int`

添加学习事件到数据库。

**参数**:
- `event_data` (dict): 学习事件数据（同HotDataStore）

**返回**:
- `int`: 新插入记录的ID

**示例**:
```python
event_id = cold_store.add_event(event)
print(f"事件已保存，ID: {event_id}")
```

**异常**:
- `sqlite3.Error`: 数据库错误

---

##### `query_events(canvas_id: str = None, start_date: str = None, end_date: str = None, limit: int = 100) -> List[dict]`

查询学习事件。

**参数**:
- `canvas_id` (str, optional): Canvas文件ID
- `start_date` (str, optional): 开始日期（YYYY-MM-DD格式）
- `end_date` (str, optional): 结束日期（YYYY-MM-DD格式）
- `limit` (int): 返回记录数上限（默认: 100）

**返回**:
- `List[dict]`: 学习事件列表

**示例**:
```python
# 查询离散数学Canvas在2025年11月的事件
events = cold_store.query_events(
    canvas_id="离散数学",
    start_date="2025-11-01",
    end_date="2025-11-30",
    limit=500
)
```

---

##### `get_daily_stats(canvas_id: str, days: int = 30) -> dict`

获取每日统计数据。

**参数**:
- `canvas_id` (str): Canvas文件ID
- `days` (int): 统计最近N天（默认: 30）

**返回**:
- `dict`: 每日统计数据，包含：
  - `dates` (list): 日期列表
  - `event_counts` (list): 每日事件数
  - `color_transitions` (list): 每日颜色流转数
  - `learning_time` (list): 每日学习时间（估算）

**示例**:
```python
daily_stats = cold_store.get_daily_stats("离散数学", days=30)
```

---

##### `get_color_transition_history(canvas_id: str, node_id: str) -> List[dict]`

获取节点颜色流转历史。

**参数**:
- `canvas_id` (str): Canvas文件ID
- `node_id` (str): 节点ID

**返回**:
- `List[dict]`: 颜色流转历史，每条记录包含：
  - `timestamp` (str): 时间戳
  - `old_color` (str): 旧颜色
  - `new_color` (str): 新颜色
  - `trigger` (str): 触发原因

**示例**:
```python
history = cold_store.get_color_transition_history("离散数学", "node-1234")
for transition in history:
    print(f"{transition['timestamp']}: {transition['old_color']} → {transition['new_color']}")
```

---

##### `vacuum_database() -> None`

压缩和优化数据库。

**返回**: None

**示例**:
```python
cold_store.vacuum_database()
```

---

## 查询接口

### LearningAnalyzer

学习数据分析器，提供高级查询和分析功能。

#### 初始化

```python
from canvas_progress_tracker.learning_analyzer import LearningAnalyzer

analyzer = LearningAnalyzer()
```

#### 方法列表

##### `generate_daily_report(canvas_id: str = None, date: str = None) -> dict`

生成每日学习报告。

**参数**:
- `canvas_id` (str, optional): Canvas文件ID，如果为None则生成所有Canvas的报告
- `date` (str, optional): 日期（YYYY-MM-DD格式），如果为None则使用今天

**返回**:
- `dict`: 每日报告，包含：
  - `summary` (dict): 概要统计
  - `events` (list): 当日事件列表
  - `color_transitions` (dict): 颜色流转统计
  - `productivity` (dict): 效率分析
  - `recommendations` (list): 学习建议

**示例**:
```python
report = analyzer.generate_daily_report(canvas_id="离散数学")
print(report['summary'])
```

---

##### `generate_weekly_report(canvas_id: str = None, weeks: int = 1) -> dict`

生成每周学习报告。

**参数**:
- `canvas_id` (str, optional): Canvas文件ID
- `weeks` (int): 统计最近N周（默认: 1）

**返回**:
- `dict`: 每周报告，包含：
  - `summary` (dict): 概要统计
  - `daily_breakdown` (list): 每日细分
  - `trends` (dict): 趋势分析
  - `heatmap` (dict): 学习热力图
  - `efficiency` (dict): 效率分析

**示例**:
```python
weekly_report = analyzer.generate_weekly_report(canvas_id="离散数学", weeks=4)
```

---

##### `analyze_learning_pattern(canvas_id: str, days: int = 30) -> dict`

分析学习模式。

**参数**:
- `canvas_id` (str): Canvas文件ID
- `days` (int): 分析最近N天（默认: 30）

**返回**:
- `dict`: 学习模式分析，包含：
  - `peak_hours` (list): 高峰学习时段
  - `learning_frequency` (str): 学习频率（daily/weekly/sporadic）
  - `focus_topics` (list): 重点学习主题
  - `mastery_rate` (float): 掌握率（0-1）
  - `struggling_areas` (list): 困难知识点

**示例**:
```python
pattern = analyzer.analyze_learning_pattern("离散数学", days=30)
print(f"掌握率: {pattern['mastery_rate'] * 100:.1f}%")
```

---

##### `get_canvas_health_score(canvas_id: str) -> dict`

获取Canvas健康度评分。

**参数**:
- `canvas_id` (str): Canvas文件ID

**返回**:
- `dict`: 健康度评分，包含：
  - `overall_score` (float): 总体评分（0-100）
  - `dimensions` (dict): 各维度评分
    - `coverage` (float): 覆盖度（节点完整性）
    - `understanding` (float): 理解度（绿色节点占比）
    - `activity` (float): 活跃度（最近更新频率）
    - `progress` (float): 进度（颜色流转趋势）
  - `suggestions` (list): 改进建议

**示例**:
```python
health = analyzer.get_canvas_health_score("离散数学")
print(f"健康度评分: {health['overall_score']}/100")
```

---

## 回调接口

Canvas监控系统支持注册回调函数，在Canvas变更时自动触发。

### AsyncCanvasProcessor回调

#### 注册回调

```python
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor

processor = AsyncCanvasProcessor()

# 定义回调函数
def on_canvas_change(canvas_path: str, event_data: dict):
    """
    Canvas变更回调

    Args:
        canvas_path: Canvas文件路径
        event_data: 事件数据
    """
    print(f"Canvas变更: {canvas_path}")
    print(f"事件类型: {event_data['event_type']}")

    # 处理特定事件类型
    if event_data['event_type'] == 'node_color_changed':
        old_color = event_data['changes']['old_color']
        new_color = event_data['changes']['new_color']

        # 检测绿色节点（已掌握）
        if new_color == "2":  # 绿色
            print(f"节点已掌握: {event_data['node_id']}")
            # 触发艾宾浩斯复习系统
            # add_to_review_queue(event_data['node_id'])

# 注册回调
processor.register_callback(on_canvas_change)
```

#### 回调函数签名

```python
def callback_function(canvas_path: str, event_data: dict) -> None:
    """
    回调函数签名

    Args:
        canvas_path (str): Canvas文件完整路径
        event_data (dict): 事件数据，包含：
            - canvas_id (str): Canvas文件ID
            - event_type (str): 事件类型
            - timestamp (str): 时间戳
            - node_id (str, optional): 节点ID
            - changes (dict, optional): 变更详情

    Returns:
        None
    """
    pass
```

#### 支持的事件类型

| 事件类型 | 描述 | event_data.changes |
|---------|------|-------------------|
| `canvas_change` | Canvas文件整体变更 | `{"nodes": [...], "edges": [...]}` |
| `node_added` | 添加新节点 | `{"node": {...}}` |
| `node_removed` | 删除节点 | `{"node_id": "..."}` |
| `node_color_changed` | 节点颜色变更 | `{"old_color": "...", "new_color": "..."}` |
| `node_text_updated` | 节点文本更新 | `{"old_text": "...", "new_text": "..."}` |
| `edge_added` | 添加边 | `{"edge": {...}}` |
| `edge_removed` | 删除边 | `{"edge_id": "..."}` |

---

## 健康检查API

### HealthChecker

健康检查器，用于监控系统状态。

#### 初始化

```python
from canvas_progress_tracker.health_checker import HealthChecker

health_checker = HealthChecker(
    processor=processor,  # AsyncCanvasProcessor实例
    hot_store=hot_store,  # HotDataStore实例
    cold_store=cold_store  # ColdDataStore实例
)
```

#### 方法列表

##### `check_health() -> dict`

检查系统健康状态。

**返回**:
- `dict`: 健康检查结果，包含：
  - `status` (str): 整体状态（healthy/degraded/unhealthy）
  - `processor` (dict): 处理器状态
    - `running` (bool): 是否运行中
    - `queue_length` (int): 队列长度
    - `worker_count` (int): 工作线程数
  - `hot_store` (dict): 热数据存储状态
    - `accessible` (bool): 是否可访问
    - `event_count` (int): 事件数量
  - `cold_store` (dict): 冷数据存储状态
    - `connected` (bool): 数据库连接状态
    - `table_count` (int): 表数量
  - `last_processed` (str): 最后处理时间
  - `response_time` (float): 响应时间（毫秒）

**示例**:
```python
health = health_checker.check_health()

if health['status'] == 'healthy':
    print("✅ 系统健康")
else:
    print(f"⚠️ 系统状态: {health['status']}")
    print(f"队列长度: {health['processor']['queue_length']}")
```

---

##### `get_performance_metrics() -> dict`

获取性能指标。

**返回**:
- `dict`: 性能指标，包含：
  - `avg_processing_time` (float): 平均处理时间（毫秒）
  - `p50_processing_time` (float): P50处理时间
  - `p95_processing_time` (float): P95处理时间
  - `p99_processing_time` (float): P99处理时间
  - `throughput` (float): 吞吐量（事件/秒）
  - `error_rate` (float): 错误率（0-1）

**示例**:
```python
metrics = health_checker.get_performance_metrics()
print(f"P95处理时间: {metrics['p95_processing_time']:.2f}ms")
```

---

## 错误处理

### 异常类型

Canvas监控系统定义了以下异常类型：

```python
from canvas_progress_tracker.exceptions import (
    CanvasMonitoringError,      # 基础异常
    DataStoreError,              # 数据存储错误
    ProcessorError,              # 处理器错误
    CallbackError,               # 回调执行错误
    HealthCheckError             # 健康检查错误
)
```

### 错误处理示例

```python
try:
    hot_store.add_event(event_data)
except DataStoreError as e:
    logger.error(f"数据存储失败: {e}")
    # 自动重试3次
    for attempt in range(3):
        try:
            hot_store.add_event(event_data)
            break
        except DataStoreError:
            if attempt == 2:
                raise
            time.sleep(1)
```

### 超时控制

| 操作 | 超时时间 |
|------|---------|
| 单个回调执行 | 2秒 |
| Canvas文件解析 | 5秒 |
| 数据库查询 | 10秒 |
| 优雅关闭 | 30秒 |

---

## 性能指标

### 目标指标

| 指标 | 目标值 |
|------|--------|
| 端到端处理延迟（P50） | < 800ms |
| 端到端处理延迟（P95） | < 1200ms |
| 端到端处理延迟（P99） | < 2000ms |
| 热数据查询响应时间 | < 50ms |
| 冷数据查询响应时间 | < 200ms |
| 数据库写入吞吐量 | > 1000 events/s |
| 内存占用（稳态） | < 200MB |

### 性能监控

```python
import time

# 监控处理延迟
start_time = time.time()
processor.process_canvas_change(canvas_path)
elapsed = (time.time() - start_time) * 1000  # 转换为毫秒

# 监控查询响应时间
start_time = time.time()
events = hot_store.get_events(canvas_id="离散数学")
query_time = (time.time() - start_time) * 1000

print(f"处理延迟: {elapsed:.2f}ms")
print(f"查询响应: {query_time:.2f}ms")
```

---

## 完整示例

### 端到端使用示例

```python
from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor
from canvas_progress_tracker.learning_analyzer import LearningAnalyzer

# 1. 初始化组件
hot_store = HotDataStore(data_dir=".learning_sessions")
cold_store = ColdDataStore(db_path="canvas_learning.db")
processor = AsyncCanvasProcessor()
analyzer = LearningAnalyzer()

# 2. 注册回调
def on_node_mastered(canvas_path, event_data):
    """节点掌握回调"""
    if event_data.get('event_type') == 'node_color_changed':
        if event_data['changes']['new_color'] == "2":  # 绿色
            print(f"✅ 节点已掌握: {event_data['node_id']}")
            # 添加到艾宾浩斯复习队列
            # ebbinghaus_system.add_to_review_queue(event_data)

processor.register_callback(on_node_mastered)

# 3. 启动监控
processor.start()

# 4. 模拟Canvas变更
event = {
    "canvas_id": "离散数学",
    "event_type": "node_color_changed",
    "timestamp": "2025-11-02T14:30:00",
    "node_id": "node-1234",
    "changes": {"old_color": "3", "new_color": "2"}
}

hot_store.add_event(event)
cold_store.add_event(event)

# 5. 生成报告
daily_report = analyzer.generate_daily_report(canvas_id="离散数学")
print(f"今日学习事件: {daily_report['summary']['total_events']}")
print(f"颜色流转: {daily_report['color_transitions']}")

# 6. 分析学习模式
pattern = analyzer.analyze_learning_pattern("离散数学", days=30)
print(f"掌握率: {pattern['mastery_rate'] * 100:.1f}%")

# 7. 健康检查
health = processor.check_health()
if health['status'] == 'healthy':
    print("✅ 系统运行正常")

# 8. 关闭
processor.shutdown()
```

---

## 更新日志

| 版本 | 日期 | 更改内容 |
|------|------|---------|
| v1.0 | 2025-11-02 | 初始版本，包含完整API文档 |

---

## 许可证

MIT License

---

**文档反馈**: 如有问题或建议，请提交Issue到项目仓库。
