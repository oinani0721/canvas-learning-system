# Canvas监控系统开发者指南

**文档版本**: v1.0
**最后更新**: 2025-11-02
**适用版本**: Canvas Learning System v1.1
**作者**: Canvas Learning System Dev Team

---

## 目录

1. [架构设计](#架构设计)
2. [代码结构](#代码结构)
3. [开发环境设置](#开发环境设置)
4. [核心组件详解](#核心组件详解)
5. [测试指南](#测试指南)
6. [贡献指南](#贡献指南)
7. [编码规范](#编码规范)
8. [故障排除](#故障排除)

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Canvas Learning System                    │
│                                                              │
│  ┌────────────┐      ┌───────────────┐     ┌─────────────┐ │
│  │            │      │               │     │             │ │
│  │  Obsidian  │─────▶│ File Watcher  │────▶│  Async      │ │
│  │  Canvas    │      │   (watchdog)  │     │  Processor  │ │
│  │            │      │               │     │             │ │
│  └────────────┘      └───────────────┘     └──────┬──────┘ │
│                                                     │         │
│                                                     ▼         │
│                                            ┌────────────────┐│
│                                            │  Event Queue   ││
│                                            │  (多线程处理)   ││
│                                            └────────┬───────┘│
│                                                     │         │
│                           ┌─────────────────────────┼─────┐  │
│                           ▼                         ▼     │  │
│                    ┌─────────────┐         ┌─────────────┐│ │
│                    │ Hot Store   │         │ Cold Store  ││ │
│                    │ (JSON)      │────────▶│ (SQLite)    ││ │
│                    │ 7天热数据    │         │ 长期存储     ││ │
│                    └─────────────┘         └─────────────┘│ │
│                                                     │        │
│                                                     ▼        │
│                                            ┌────────────────┐│
│                                            │  Learning      ││
│                                            │  Analyzer      ││
│                                            │  (分析&报告)    ││
│                                            └────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 架构原则

1. **异步优先**: 使用异步处理机制，避免阻塞Obsidian操作
2. **分层设计**: 热数据/冷数据分离，提高查询性能
3. **松耦合**: 使用回调机制，组件间解耦
4. **容错机制**: 错误隔离，单个事件失败不影响整体系统

### 数据流

```
Canvas变更 → 文件监控 → 事件队列 → 异步处理 → 数据存储 → 分析报告
   (1)        (2)         (3)        (4)        (5)        (6)

(1) 用户在Obsidian中编辑Canvas文件
(2) watchdog检测到文件变更，触发事件
(3) 事件加入队列（多线程安全）
(4) 工作线程从队列取出事件，解析Canvas JSON
(5) 同时写入热数据存储（JSON）和冷数据存储（SQLite）
(6) LearningAnalyzer查询数据，生成学习报告
```

---

## 代码结构

### 目录结构

```
C:/Users/ROG/托福/
├── canvas_progress_tracker/          # 主包
│   ├── __init__.py
│   ├── async_processor.py            # 异步Canvas处理器 (核心)
│   ├── data_stores.py                # 数据存储 (HotDataStore + ColdDataStore)
│   ├── learning_analyzer.py          # 学习数据分析器
│   ├── health_checker.py             # 健康检查器
│   ├── exceptions.py                 # 自定义异常
│   ├── utils.py                      # 工具函数
│   └── start_monitoring.py           # 启动脚本
│
├── canvas_utils.py                   # Canvas工具库 (3层架构)
│   ├── Layer 1: CanvasJSONOperator   # JSON操作
│   ├── Layer 2: CanvasBusinessLogic  # 业务逻辑
│   └── Layer 3: CanvasOrchestrator   # 高级API
│
├── deployment/
│   ├── testing/
│   │   ├── deploy.sh                 # Linux部署脚本
│   │   ├── start-local.bat           # Windows本地启动
│   │   └── config.yaml               # 配置文件
│   └── production/
│       └── start-monitoring.bat      # Windows生产部署
│
├── tests/                            # 测试套件
│   ├── test_async_processor.py       # 异步处理器测试
│   ├── test_data_stores.py           # 数据存储测试
│   ├── test_learning_analyzer.py     # 分析器测试
│   ├── test_integration_end_to_end.py # 端到端集成测试
│   ├── test_agent_integration.py     # Agent集成测试
│   ├── test_ebbinghaus_integration.py # 艾宾浩斯集成测试
│   └── test_performance_benchmarks.py # 性能基准测试
│
├── docs/                             # 文档
│   ├── architecture/                 # 架构文档 (8个)
│   ├── prd/                          # PRD文档
│   ├── stories/                      # Story文件 (26个)
│   ├── canvas-monitoring-api-reference.md
│   ├── canvas-monitoring-developer-guide.md  # 本文件
│   └── project-brief.md              # 项目简报
│
├── .claude/
│   ├── agents/                       # 14个AI Agent定义
│   ├── commands/                     # 斜杠命令
│   └── PROJECT.md                    # 项目上下文
│
├── CLAUDE.md                         # Claude Code配置
├── CHANGELOG.md                      # 变更日志
├── README.md                         # 项目README
└── requirements.txt                  # Python依赖
```

### 核心文件说明

#### `async_processor.py` (异步处理器)

**职责**:
- 监听Canvas文件变更
- 管理事件队列
- 多线程异步处理
- 回调机制

**关键类**:
```python
class AsyncCanvasProcessor:
    def __init__(self, config: dict = None):
        self.task_queue = queue.Queue()
        self.workers = []
        self.callbacks = []
        self.running = False

    def start(self) -> None:
        """启动监控"""

    def shutdown(self, timeout: int = 30) -> None:
        """优雅关闭"""

    def register_callback(self, callback: Callable) -> None:
        """注册回调函数"""

    def process_canvas_change(self, canvas_path: str) -> None:
        """处理Canvas变更（队列入口）"""
```

**线程模型**:
- 主线程: 文件监控 (watchdog)
- 工作线程池: 2-4个线程异步处理事件
- Poison Pill模式: 优雅关闭工作线程

---

#### `data_stores.py` (数据存储)

**职责**:
- 热数据存储 (JSON文件)
- 冷数据存储 (SQLite)
- 数据清理和归档

**HotDataStore**:
```python
class HotDataStore:
    """热数据存储 (内存 + JSON)"""
    def __init__(self, data_dir: str, retention_days: int = 7):
        self.data_dir = Path(data_dir)
        self.events = []  # 内存缓存
        self.retention_days = retention_days

    def add_event(self, event_data: dict) -> None:
        """添加事件 (写入内存 + JSON文件)"""

    def get_events(self, canvas_id: str = None, days: int = 7) -> List[dict]:
        """查询事件 (从内存读取)"""

    def cleanup_old_data(self) -> int:
        """清理超过保留期的数据"""
```

**ColdDataStore**:
```python
class ColdDataStore:
    """冷数据存储 (SQLite)"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)

    def add_event(self, event_data: dict) -> int:
        """添加事件到数据库"""

    def query_events(self, canvas_id: str = None,
                     start_date: str = None,
                     end_date: str = None) -> List[dict]:
        """查询事件 (支持时间范围)"""

    def get_daily_stats(self, canvas_id: str, days: int = 30) -> dict:
        """获取每日统计"""
```

**数据同步策略**:
- 所有事件同时写入热存储和冷存储
- 热存储自动清理7天前的数据
- 冷存储永久保留所有数据

---

#### `learning_analyzer.py` (学习分析器)

**职责**:
- 生成每日/每周报告
- 分析学习模式
- 计算健康度评分
- 提供学习建议

**关键方法**:
```python
class LearningAnalyzer:
    def generate_daily_report(self, canvas_id: str = None) -> dict:
        """生成每日报告"""

    def generate_weekly_report(self, canvas_id: str = None, weeks: int = 1) -> dict:
        """生成每周报告"""

    def analyze_learning_pattern(self, canvas_id: str, days: int = 30) -> dict:
        """分析学习模式"""

    def get_canvas_health_score(self, canvas_id: str) -> dict:
        """计算Canvas健康度评分"""
```

**分析算法**:
- **掌握率计算**: `绿色节点数 / 总节点数`
- **学习频率**: 基于事件间隔判断（daily/weekly/sporadic）
- **效率分析**: `掌握节点数 / 学习事件数`
- **健康度评分**: 4个维度加权平均（coverage, understanding, activity, progress）

---

## 开发环境设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd 托福
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**主要依赖**:
```
watchdog==5.0.4       # 文件监控
loguru==0.7.3         # 日志系统
pytest==8.4.2         # 测试框架
pytest-cov==7.0.0     # 测试覆盖率
sqlite3               # 数据库 (内置)
```

### 4. 配置Claude Code

将项目添加到Claude Code工作区：
```bash
# 确保.claude/目录存在
ls .claude/

# 查看PROJECT.md确认项目配置
cat .claude/PROJECT.md
```

### 5. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_async_processor.py -v

# 测试覆盖率
pytest --cov=canvas_progress_tracker tests/
```

### 6. 启动监控系统

```bash
# Windows
deployment\testing\start-local.bat

# Linux/Mac
./deployment/testing/deploy.sh
```

---

## 核心组件详解

### AsyncCanvasProcessor详解

#### 启动流程

```python
def start(self):
    """启动监控系统"""
    # 1. 创建工作线程
    for i in range(self.worker_count):
        worker = threading.Thread(
            target=self._worker_loop,
            name=f"CanvasWorker-{i}",
            daemon=True
        )
        worker.start()
        self.workers.append(worker)

    # 2. 启动文件监控
    self.observer = Observer()
    self.observer.schedule(
        event_handler=self._file_event_handler,
        path=self.canvas_directory,
        recursive=True
    )
    self.observer.start()

    self.running = True
    logger.info("Canvas监控系统启动成功")
```

#### 工作线程循环

```python
def _worker_loop(self):
    """工作线程主循环"""
    thread_name = threading.current_thread().name

    while self.running:
        try:
            # 从队列获取任务（0.1秒超时）
            task = self.task_queue.get(timeout=0.1)

            # Poison Pill检测
            if task is None:
                logger.debug(f"{thread_name} 收到poison pill，准备退出")
                self.task_queue.task_done()
                break

            # 处理任务
            canvas_path = task['canvas_path']
            self._process_canvas_file(canvas_path)

            self.task_queue.task_done()

        except queue.Empty:
            continue  # 队列为空，继续循环
        except Exception as e:
            logger.error(f"{thread_name} 处理任务失败: {e}")
            self.task_queue.task_done()
```

#### 优雅关闭

```python
def shutdown(self, timeout: int = 30):
    """优雅关闭监控系统"""
    logger.info("开始关闭Canvas监控系统...")
    self.running = False

    # 1. 停止文件监控
    if self.observer:
        self.observer.stop()
        self.observer.join(timeout=5)

    # 2. 发送Poison Pill
    for _ in self.workers:
        self.task_queue.put(None, block=False)

    # 3. 等待工作线程结束
    start_time = time.time()
    for worker in self.workers:
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            logger.warning("等待工作线程超时，强制退出")
            break
        worker.join(timeout=remaining)

    logger.info("Canvas监控系统已关闭")
```

---

### 数据存储架构

#### 热数据存储设计

**文件结构**:
```
.learning_sessions/
├── hot_data_2025-11-01.json    # 每日JSON文件
├── hot_data_2025-11-02.json
└── hot_data_2025-11-03.json
```

**JSON格式**:
```json
{
  "date": "2025-11-02",
  "events": [
    {
      "canvas_id": "离散数学",
      "event_type": "node_color_changed",
      "timestamp": "2025-11-02T14:30:00",
      "node_id": "node-1234",
      "changes": {
        "old_color": "1",
        "new_color": "3"
      }
    }
  ]
}
```

**查询性能**:
- 内存缓存: O(n)遍历
- 最近7天数据: 通常 < 10000条事件
- 典型查询时间: < 50ms

---

#### 冷数据存储设计

**数据库Schema**:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canvas_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    node_id TEXT,
    changes TEXT,  -- JSON字符串
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_canvas_id (canvas_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type)
);

CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canvas_id TEXT NOT NULL,
    date TEXT NOT NULL,
    total_events INTEGER,
    color_transitions INTEGER,
    learning_time_minutes INTEGER,
    UNIQUE(canvas_id, date)
);
```

**索引策略**:
- 单列索引: `canvas_id`, `timestamp`, `event_type`
- 组合索引: `(canvas_id, timestamp)` (用于时间范围查询)
- 分区表: 按月分区 (未来优化)

**查询优化**:
```python
# 使用索引的查询
query = """
    SELECT * FROM events
    WHERE canvas_id = ?
      AND timestamp BETWEEN ? AND ?
    ORDER BY timestamp DESC
    LIMIT ?
"""

# 预聚合统计
query_stats = """
    SELECT date, total_events, color_transitions
    FROM daily_stats
    WHERE canvas_id = ?
      AND date >= ?
"""
```

---

## 测试指南

### 测试策略

Canvas监控系统采用分层测试策略：

1. **单元测试** (Unit Tests): 测试单个类/方法
2. **集成测试** (Integration Tests): 测试组件间交互
3. **端到端测试** (E2E Tests): 测试完整工作流
4. **性能测试** (Performance Tests): 验证性能指标

### 测试文件组织

```
tests/
├── unit/                                     # 单元测试
│   ├── test_data_stores_unit.py
│   ├── test_learning_analyzer_unit.py
│   └── test_async_processor_unit.py
│
├── integration/                              # 集成测试
│   ├── test_agent_integration.py            # ✅ 已完成
│   ├── test_ebbinghaus_integration.py       # ✅ 已完成
│   └── test_integration_end_to_end.py       # ✅ 已完成
│
└── performance/                              # 性能测试
    └── test_performance_benchmarks.py       # ⏳ 待实现
```

### 编写测试

#### 单元测试示例

```python
import pytest
from canvas_progress_tracker.data_stores import HotDataStore

class TestHotDataStore:
    """HotDataStore单元测试"""

    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        cls.data_dir = Path("test_data")
        cls.data_dir.mkdir(exist_ok=True)

    def setup_method(self):
        """每个测试前初始化"""
        self.store = HotDataStore(data_dir=str(self.data_dir))

    def teardown_method(self):
        """每个测试后清理"""
        # 清理测试数据
        for file in self.data_dir.glob("*.json"):
            file.unlink()

    def test_add_event(self):
        """测试添加事件"""
        event = {
            "canvas_id": "测试Canvas",
            "event_type": "test_event",
            "timestamp": "2025-11-02T14:30:00"
        }

        self.store.add_event(event)
        events = self.store.get_events()

        assert len(events) == 1
        assert events[0]['canvas_id'] == "测试Canvas"

    def test_get_events_filtered(self):
        """测试按Canvas ID过滤事件"""
        # 添加多个Canvas的事件
        self.store.add_event({"canvas_id": "Canvas1", "event_type": "test", "timestamp": "2025-11-02T10:00:00"})
        self.store.add_event({"canvas_id": "Canvas2", "event_type": "test", "timestamp": "2025-11-02T11:00:00"})

        # 查询Canvas1的事件
        canvas1_events = self.store.get_events(canvas_id="Canvas1")

        assert len(canvas1_events) == 1
        assert canvas1_events[0]['canvas_id'] == "Canvas1"
```

#### 集成测试示例

```python
import pytest
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor
from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore

class TestEndToEndIntegration:
    """端到端集成测试"""

    def setup_method(self):
        """测试前初始化"""
        self.hot_store = HotDataStore(data_dir="test_data")
        self.cold_store = ColdDataStore(db_path=":memory:")  # 内存数据库
        self.processor = AsyncCanvasProcessor()

    def test_canvas_change_workflow(self):
        """测试完整的Canvas变更工作流"""
        # 1. 启动处理器
        self.processor.start()

        # 2. 模拟Canvas变更
        canvas_path = "test.canvas"
        self.processor.process_canvas_change(canvas_path)

        # 3. 等待处理完成
        self.processor.task_queue.join()

        # 4. 验证数据存储
        hot_events = self.hot_store.get_events()
        cold_events = self.cold_store.query_events()

        assert len(hot_events) > 0
        assert len(cold_events) > 0

        # 5. 关闭
        self.processor.shutdown()
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定类别测试
pytest tests/unit/ -v
pytest tests/integration/ -v

# 运行单个测试文件
pytest tests/test_async_processor.py -v

# 运行单个测试方法
pytest tests/test_async_processor.py::TestAsyncProcessor::test_start -v

# 测试覆盖率报告
pytest --cov=canvas_progress_tracker --cov-report=html tests/

# 性能测试
pytest tests/performance/ -v --benchmark-only
```

### 测试覆盖率目标

| 组件 | 目标覆盖率 |
|------|----------|
| AsyncCanvasProcessor | ≥ 90% |
| HotDataStore | ≥ 95% |
| ColdDataStore | ≥ 90% |
| LearningAnalyzer | ≥ 85% |
| 整体覆盖率 | ≥ 90% |

---

## 贡献指南

### 贡献流程

1. **Fork项目**: 从主仓库Fork到个人账号
2. **创建分支**: `git checkout -b feature/your-feature-name`
3. **开发**: 编写代码和测试
4. **测试**: 确保所有测试通过
5. **提交**: `git commit -m "feat: add your feature"`
6. **Push**: `git push origin feature/your-feature-name`
7. **创建PR**: 提交Pull Request到主仓库

### Commit Message规范

采用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 代码重构
- `perf`: 性能优化
- `chore`: 构建工具/依赖更新

**示例**:
```
feat(data-store): add batch insert support

- 实现批量插入API
- 提升写入性能10倍
- 添加批量插入测试

Closes #123
```

### 代码审查清单

提交PR前，请确保：

- [ ] 所有测试通过
- [ ] 测试覆盖率 ≥ 85%
- [ ] 代码符合PEP 8规范
- [ ] 添加必要的文档字符串
- [ ] 更新CHANGELOG.md
- [ ] 更新相关文档

---

## 编码规范

### Python代码规范

遵循[PEP 8](https://pep8.org/)规范：

```python
# 1. 导入顺序
import os  # 标准库
import sys

from pathlib import Path  # 标准库

import watchdog  # 第三方库
from loguru import logger

from canvas_progress_tracker import utils  # 本地模块

# 2. 类定义
class MyClass:
    """类文档字符串

    Args:
        param1 (str): 参数1说明
        param2 (int): 参数2说明
    """

    def __init__(self, param1: str, param2: int):
        self.param1 = param1
        self.param2 = param2

    def my_method(self) -> dict:
        """方法文档字符串

        Returns:
            dict: 返回值说明
        """
        pass

# 3. 命名规范
# 类名: PascalCase
class AsyncCanvasProcessor:
    pass

# 函数名: snake_case
def process_canvas_file():
    pass

# 常量: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# 变量: snake_case
canvas_id = "离散数学"
```

### 文档字符串规范

使用[Google风格](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)文档字符串：

```python
def add_event(self, event_data: dict) -> None:
    """添加学习事件到热数据存储

    Args:
        event_data (dict): 学习事件数据，必需字段：
            - canvas_id (str): Canvas文件ID
            - event_type (str): 事件类型
            - timestamp (str): 时间戳（ISO 8601格式）

    Returns:
        None

    Raises:
        ValueError: 如果event_data缺少必需字段

    Example:
        >>> event = {
        ...     "canvas_id": "离散数学",
        ...     "event_type": "node_added",
        ...     "timestamp": "2025-11-02T14:30:00"
        ... }
        >>> store.add_event(event)
    """
    pass
```

### 日志规范

使用[loguru](https://github.com/Delgan/loguru)进行日志记录：

```python
from loguru import logger

# 级别: DEBUG < INFO < WARNING < ERROR < CRITICAL

# DEBUG: 详细的调试信息
logger.debug(f"处理Canvas文件: {canvas_path}")

# INFO: 关键操作记录
logger.info("Canvas监控系统启动成功")

# WARNING: 警告信息
logger.warning(f"队列长度过高: {queue_length}")

# ERROR: 错误信息
logger.error(f"Canvas解析失败: {e}")

# CRITICAL: 严重错误
logger.critical("数据库连接失败，系统停止")
```

---

## 故障排除

### 常见问题

#### 1. 监控系统无法启动

**症状**: `start-monitoring.bat`运行后立即退出

**排查步骤**:
```bash
# 1. 检查Python环境
python --version  # 应该 ≥ 3.9

# 2. 检查依赖
pip list | grep watchdog
pip list | grep loguru

# 3. 手动启动并查看错误
python canvas_progress_tracker/start_monitoring.py
```

**常见原因**:
- Python版本过低
- 缺少依赖包
- 配置文件路径错误

---

#### 2. 测试失败

**症状**: `pytest tests/`运行失败

**排查步骤**:
```bash
# 1. 查看详细错误信息
pytest tests/ -v --tb=long

# 2. 运行单个失败测试
pytest tests/test_xxx.py::test_method -v

# 3. 检查测试数据
ls test_data/
```

**常见原因**:
- 测试数据未清理
- 数据库文件被锁定
- 端口占用

---

#### 3. 性能问题

**症状**: 处理延迟 > 2秒

**排查步骤**:
```bash
# 1. 检查队列长度
# 查看日志中的queue_length

# 2. 检查数据库大小
ls -lh canvas_learning.db

# 3. 运行性能测试
pytest tests/test_performance_benchmarks.py -v
```

**优化建议**:
- 增加工作线程数
- 清理旧数据
- 优化数据库索引

---

#### 4. 数据丢失

**症状**: 某些学习事件未被记录

**排查步骤**:
```bash
# 1. 检查日志
cat logs/canvas_monitor_*.log | grep ERROR

# 2. 检查热数据存储
cat .learning_sessions/hot_data_*.json

# 3. 检查数据库
sqlite3 canvas_learning.db "SELECT COUNT(*) FROM events;"
```

**预防措施**:
- 启用事务日志
- 定期数据备份
- 监控磁盘空间

---

### 性能调优

#### 数据库优化

```python
# 1. 批量插入
def batch_insert_events(events: List[dict]):
    """批量插入，提升性能10倍"""
    conn = sqlite3.connect("canvas_learning.db")
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT INTO events (canvas_id, event_type, timestamp, node_id, changes)
        VALUES (?, ?, ?, ?, ?)
    """, [(e['canvas_id'], e['event_type'], e['timestamp'],
           e.get('node_id'), json.dumps(e.get('changes')))
          for e in events])

    conn.commit()
    conn.close()

# 2. 添加索引
CREATE INDEX idx_canvas_timestamp ON events(canvas_id, timestamp);

# 3. 定期VACUUM
sqlite3 canvas_learning.db "VACUUM;"
```

#### 内存优化

```python
# 1. 限制热数据缓存大小
class HotDataStore:
    MAX_CACHE_SIZE = 10000  # 最多缓存10000条事件

    def add_event(self, event_data: dict):
        self.events.append(event_data)

        # 超过限制时清理最旧的事件
        if len(self.events) > self.MAX_CACHE_SIZE:
            self.events = self.events[-self.MAX_CACHE_SIZE:]

# 2. 使用生成器而非列表
def query_events_generator(self, canvas_id: str):
    """使用生成器避免一次性加载所有数据"""
    for event in self.events:
        if event['canvas_id'] == canvas_id:
            yield event
```

---

## 发布流程

### 版本号规范

采用[语义化版本](https://semver.org/)：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的Bug修复

**示例**: `v1.2.3`

### 发布清单

发布新版本前，确保：

1. **代码质量**:
   - [ ] 所有测试通过 (420/420)
   - [ ] 测试覆盖率 ≥ 90%
   - [ ] 代码审查完成

2. **文档更新**:
   - [ ] 更新CHANGELOG.md
   - [ ] 更新README.md版本号
   - [ ] 更新API文档

3. **性能验证**:
   - [ ] 运行性能基准测试
   - [ ] 验证性能指标达标

4. **用户测试**:
   - [ ] UAT场景测试通过
   - [ ] 用户反馈收集

5. **发布**:
   - [ ] 创建Git tag: `git tag v1.2.3`
   - [ ] 推送tag: `git push origin v1.2.3`
   - [ ] 发布Release Notes

---

## 参考资源

### 内部文档

- [项目简报](../project-brief.md)
- [PRD文档](../prd/FULL-PRD-REFERENCE.md)
- [架构文档](../architecture/)
- [Story文件](../stories/)

### 外部资源

- [Watchdog文档](https://pythonhosted.org/watchdog/)
- [Loguru文档](https://loguru.readthedocs.io/)
- [Pytest文档](https://docs.pytest.org/)
- [SQLite文档](https://www.sqlite.org/docs.html)

### 联系方式

- **Issue Tracker**: GitHub Issues
- **开发团队**: Canvas Learning System Dev Team
- **项目地址**: C:/Users/ROG/托福/

---

**最后更新**: 2025-11-02
**文档版本**: v1.0
**许可证**: MIT License
