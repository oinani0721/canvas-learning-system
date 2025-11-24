# ADR-010: 日志聚合方案 - structlog

## 状态

**已接受** | 2025-11-24

## 背景

Canvas Learning System 需要完善的日志系统来：

1. **问题排查** - 追踪错误和异常
2. **性能分析** - LLM调用耗时、Token消耗
3. **用户支持** - 帮助用户提供问题信息
4. **开发调试** - Agent状态转换追踪

### 与 ADR-009 的关系

ADR-009 定义了错误存储 (SQLite) 和基础日志配置。本 ADR 扩展日志系统，增加：
- 结构化日志
- 性能追踪
- 双格式输出

## 决策

**采用 structlog 作为日志框架，实现 JSON + 文本双格式输出**

### 核心组件

| 组件 | 方案 | 用途 |
|------|------|------|
| **日志框架** | structlog | 结构化日志 |
| **JSON输出** | 文件 | 程序分析 |
| **文本输出** | 文件 | 人工查看 |
| **性能日志** | 单独文件 | LLM调用追踪 |
| **日志轮转** | RotatingFileHandler | 避免磁盘占满 |

### 依赖

```toml
# pyproject.toml
[project.dependencies]
structlog = ">=24.1"
```

## 实现细节

### 1. 日志目录结构

```
.canvas-learning/
└── logs/
    ├── canvas-learning.log      # 文本格式 (人读)
    ├── canvas-learning.json     # JSON格式 (分析)
    ├── performance.json         # 性能日志
    └── errors.log               # 错误日志 (ADR-009)
```

### 2. structlog 配置

```python
# src/logging_config.py
import structlog
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime

def setup_logging(vault_path: str, debug: bool = False):
    """配置 structlog 日志系统"""
    log_dir = Path(vault_path) / ".canvas-learning" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 时间戳处理器
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # 共享处理器
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # 配置 structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # 1. 文本格式处理器 (人读)
    text_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=False),
        foreign_pre_chain=shared_processors,
    )

    text_handler = RotatingFileHandler(
        log_dir / "canvas-learning.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    text_handler.setFormatter(text_formatter)
    text_handler.setLevel(logging.INFO)
    root_logger.addHandler(text_handler)

    # 2. JSON格式处理器 (分析)
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    json_handler = RotatingFileHandler(
        log_dir / "canvas-learning.json",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    json_handler.setFormatter(json_formatter)
    json_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(json_handler)

    # 3. 错误日志处理器
    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setFormatter(text_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # 4. 性能日志处理器
    perf_logger = logging.getLogger("performance")
    perf_handler = RotatingFileHandler(
        log_dir / "performance.json",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8",
    )
    perf_handler.setFormatter(json_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

    # 5. 控制台处理器 (开发模式)
    if debug:
        console_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

    return structlog.get_logger()
```

### 3. 日志使用示例

```python
# src/example_usage.py
import structlog
from contextlib import contextmanager
import time

logger = structlog.get_logger()

# 基础日志
logger.info("application_started", version="1.0.0")

# 带上下文的日志
logger.info(
    "canvas_loaded",
    canvas_path="学习笔记.canvas",
    node_count=25,
    edge_count=30,
)

# 绑定上下文 (后续日志自动带上)
log = logger.bind(request_id="req-123", user="local")
log.info("analysis_started", node_id="node-1")
log.info("analysis_completed", duration_ms=1500)

# 错误日志
try:
    result = await call_llm(prompt)
except Exception as e:
    logger.error(
        "llm_call_failed",
        error=str(e),
        error_type=type(e).__name__,
        prompt_length=len(prompt),
        exc_info=True,
    )
```

### 4. 性能日志追踪器

```python
# src/performance_tracker.py
import structlog
import time
from contextlib import contextmanager
from typing import Optional
from functools import wraps

perf_logger = structlog.get_logger("performance")

class PerformanceTracker:
    """性能追踪器"""

    @staticmethod
    @contextmanager
    def track(operation: str, **context):
        """追踪操作耗时"""
        start_time = time.perf_counter()
        context["operation"] = operation
        context["start_time"] = time.time()

        try:
            yield context
            context["status"] = "success"
        except Exception as e:
            context["status"] = "error"
            context["error"] = str(e)
            raise
        finally:
            duration = time.perf_counter() - start_time
            context["duration_ms"] = round(duration * 1000, 2)
            perf_logger.info("operation_completed", **context)

    @staticmethod
    def track_llm_call(func):
        """LLM调用装饰器"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with PerformanceTracker.track(
                "llm_call",
                model=kwargs.get("model", "unknown"),
                prompt_length=len(kwargs.get("prompt", "")),
            ) as ctx:
                result = await func(*args, **kwargs)

                # 添加Token信息
                if hasattr(result, "usage"):
                    ctx["input_tokens"] = result.usage.input_tokens
                    ctx["output_tokens"] = result.usage.output_tokens
                    ctx["total_tokens"] = result.usage.total_tokens

                return result
        return wrapper

# 使用示例
class LLMClient:
    @PerformanceTracker.track_llm_call
    async def generate(self, prompt: str, model: str = "claude-3-sonnet"):
        return await self._call_api(prompt, model)

# 手动追踪
async def analyze_node(node_id: str):
    with PerformanceTracker.track(
        "node_analysis",
        node_id=node_id,
        analysis_type="deep",
    ):
        result = await do_analysis(node_id)
        return result
```

### 5. 请求上下文管理

```python
# src/request_context.py
import structlog
from contextvars import ContextVar
from uuid import uuid4

# 请求上下文
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
canvas_path_var: ContextVar[str] = ContextVar("canvas_path", default="")

def bind_request_context(canvas_path: str = ""):
    """绑定请求上下文"""
    request_id = str(uuid4())[:8]
    request_id_var.set(request_id)
    canvas_path_var.set(canvas_path)

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        canvas_path=canvas_path,
    )

    return request_id

def clear_request_context():
    """清除请求上下文"""
    structlog.contextvars.clear_contextvars()

# FastAPI 中间件
from fastapi import Request

async def request_context_middleware(request: Request, call_next):
    canvas_path = request.headers.get("X-Canvas-Path", "")
    request_id = bind_request_context(canvas_path)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    clear_request_context()
    return response
```

### 6. Agent 日志集成

```python
# src/agents/logging_mixin.py
import structlog
from typing import Any

class AgentLoggingMixin:
    """Agent日志混入类"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(
            agent=self.__class__.__name__
        )

    def log_state_transition(
        self,
        from_node: str,
        to_node: str,
        state: dict[str, Any],
    ):
        """记录状态转换"""
        self.logger.debug(
            "state_transition",
            from_node=from_node,
            to_node=to_node,
            state_keys=list(state.keys()),
        )

    def log_node_execution(
        self,
        node_name: str,
        input_keys: list[str],
        output_keys: list[str],
        duration_ms: float,
    ):
        """记录节点执行"""
        self.logger.info(
            "node_executed",
            node=node_name,
            input_keys=input_keys,
            output_keys=output_keys,
            duration_ms=duration_ms,
        )

# LangGraph 节点示例
async def scoring_node(state: dict) -> dict:
    logger = structlog.get_logger().bind(node="scoring")

    logger.debug("node_started", input_keys=list(state.keys()))

    start = time.perf_counter()
    result = await perform_scoring(state)
    duration = (time.perf_counter() - start) * 1000

    logger.info(
        "node_completed",
        duration_ms=round(duration, 2),
        scores=result.get("scores"),
    )

    return result
```

### 7. 日志查询工具

```python
# src/log_analyzer.py
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

class LogAnalyzer:
    """日志分析工具"""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)

    def get_recent_logs(
        self,
        minutes: int = 60,
        level: Optional[str] = None,
        event: Optional[str] = None,
    ) -> list[dict]:
        """获取最近的日志"""
        logs = []
        cutoff = datetime.now() - timedelta(minutes=minutes)

        json_log = self.log_dir / "canvas-learning.json"
        if not json_log.exists():
            return logs

        with open(json_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(
                        entry.get("timestamp", "").replace("Z", "+00:00")
                    )

                    if timestamp < cutoff:
                        continue

                    if level and entry.get("level") != level.upper():
                        continue

                    if event and entry.get("event") != event:
                        continue

                    logs.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue

        return logs

    def get_performance_summary(self, hours: int = 24) -> dict:
        """获取性能摘要"""
        perf_log = self.log_dir / "performance.json"
        if not perf_log.exists():
            return {}

        cutoff = datetime.now() - timedelta(hours=hours)
        operations = {}

        with open(perf_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(
                        entry.get("timestamp", "").replace("Z", "+00:00")
                    )

                    if timestamp < cutoff:
                        continue

                    op = entry.get("operation", "unknown")
                    duration = entry.get("duration_ms", 0)

                    if op not in operations:
                        operations[op] = {
                            "count": 0,
                            "total_ms": 0,
                            "min_ms": float("inf"),
                            "max_ms": 0,
                        }

                    operations[op]["count"] += 1
                    operations[op]["total_ms"] += duration
                    operations[op]["min_ms"] = min(operations[op]["min_ms"], duration)
                    operations[op]["max_ms"] = max(operations[op]["max_ms"], duration)

                except (json.JSONDecodeError, ValueError):
                    continue

        # 计算平均值
        for op in operations:
            count = operations[op]["count"]
            if count > 0:
                operations[op]["avg_ms"] = round(
                    operations[op]["total_ms"] / count, 2
                )

        return operations

    def get_error_summary(self, hours: int = 24) -> dict:
        """获取错误摘要"""
        logs = self.get_recent_logs(minutes=hours * 60, level="ERROR")

        summary = {}
        for log in logs:
            error_type = log.get("error_type", "unknown")
            if error_type not in summary:
                summary[error_type] = 0
            summary[error_type] += 1

        return summary
```

### 8. API 端点

```python
# src/api/logs.py
from fastapi import APIRouter
from src.log_analyzer import LogAnalyzer

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("/recent")
async def get_recent_logs(
    minutes: int = 60,
    level: str | None = None,
):
    """获取最近日志"""
    analyzer = LogAnalyzer(log_dir)
    return analyzer.get_recent_logs(minutes=minutes, level=level)

@router.get("/performance")
async def get_performance_summary(hours: int = 24):
    """获取性能摘要"""
    analyzer = LogAnalyzer(log_dir)
    return analyzer.get_performance_summary(hours=hours)

@router.get("/errors")
async def get_error_summary(hours: int = 24):
    """获取错误摘要"""
    analyzer = LogAnalyzer(log_dir)
    return analyzer.get_error_summary(hours=hours)
```

## 配置汇总

### 日志文件配置

| 文件 | 格式 | 大小限制 | 保留数量 | 用途 |
|------|------|----------|----------|------|
| canvas-learning.log | 文本 | 10MB | 5 | 人工查看 |
| canvas-learning.json | JSON | 10MB | 5 | 程序分析 |
| performance.json | JSON | 10MB | 3 | 性能追踪 |
| errors.log | 文本 | 5MB | 3 | 错误记录 |

### 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 开发调试 | 状态转换、变量值 |
| INFO | 正常操作 | API调用、任务完成 |
| WARNING | 潜在问题 | 重试、降级 |
| ERROR | 错误 | 异常、失败 |

### 性能日志字段

| 字段 | 类型 | 说明 |
|------|------|------|
| operation | string | 操作名称 |
| duration_ms | float | 耗时 (毫秒) |
| status | string | success/error |
| input_tokens | int | 输入Token数 |
| output_tokens | int | 输出Token数 |
| model | string | 模型名称 |

## 日志示例

### 文本格式 (canvas-learning.log)

```
2025-11-24T10:30:15.123Z [INFO] canvas_loaded canvas_path=学习笔记.canvas node_count=25
2025-11-24T10:30:16.456Z [INFO] analysis_started request_id=abc123 node_id=node-1
2025-11-24T10:30:18.789Z [INFO] llm_call_completed request_id=abc123 duration_ms=2300 tokens=150
2025-11-24T10:30:18.901Z [INFO] analysis_completed request_id=abc123 duration_ms=3500
```

### JSON格式 (canvas-learning.json)

```json
{"timestamp": "2025-11-24T10:30:15.123Z", "level": "INFO", "event": "canvas_loaded", "canvas_path": "学习笔记.canvas", "node_count": 25, "edge_count": 30}
{"timestamp": "2025-11-24T10:30:16.456Z", "level": "INFO", "event": "analysis_started", "request_id": "abc123", "node_id": "node-1", "analysis_type": "deep"}
{"timestamp": "2025-11-24T10:30:18.789Z", "level": "INFO", "event": "llm_call_completed", "request_id": "abc123", "duration_ms": 2300, "input_tokens": 100, "output_tokens": 50}
```

### 性能日志 (performance.json)

```json
{"timestamp": "2025-11-24T10:30:18.789Z", "operation": "llm_call", "model": "claude-3-sonnet", "duration_ms": 2300, "input_tokens": 100, "output_tokens": 50, "status": "success"}
{"timestamp": "2025-11-24T10:30:25.123Z", "operation": "embedding_generate", "text_length": 500, "duration_ms": 150, "status": "success"}
{"timestamp": "2025-11-24T10:30:30.456Z", "operation": "node_analysis", "node_id": "node-1", "duration_ms": 3500, "status": "success"}
```

## 理由

### 为什么选择 structlog

1. **结构化优先** - 原生支持结构化日志
2. **灵活处理器** - 可配置多种输出格式
3. **上下文绑定** - 自动携带请求上下文
4. **性能优秀** - 比标准库更快
5. **类型安全** - 更好的IDE支持

### 为什么双格式输出

1. **JSON** - 便于程序解析、搜索、聚合
2. **文本** - 人工查看更直观
3. **分离存储** - 不同用途不同文件

### 为什么单独性能日志

1. **专注追踪** - LLM调用、耗时、Token
2. **便于分析** - 计算平均值、趋势
3. **成本控制** - Token消耗统计

## 影响

### 正面影响

1. **问题排查** - 结构化日志便于搜索
2. **性能优化** - 清晰的性能数据
3. **成本控制** - Token使用追踪
4. **开发体验** - 上下文自动绑定

### 负面影响

1. **存储空间** - 双格式占用更多空间
2. **学习成本** - structlog 语法需要学习

### 缓解措施

1. **日志轮转** - 自动清理旧日志
2. **文档完善** - 提供使用示例

## 参考资料

- [structlog Documentation](https://www.structlog.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging in Python](https://www.structlog.org/en/stable/why.html)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
