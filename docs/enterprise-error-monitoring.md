# Canvas学习系统企业级错误监控日志系统技术方案

**版本**: v1.0
**创建日期**: 2025-10-18
**作者**: Claude Code
**状态**: 技术设计阶段

---

## 📋 方案概述

### 项目背景

Canvas学习系统当前缺乏完整的错误监控体系，现有错误处理机制主要依赖手动记录的`CANVAS_ERROR_LOG.md`文件。为实现系统的高可用性、可维护性和可扩展性，需要建立企业级错误监控日志系统。

### 核心目标

1. **全面监控**: 覆盖3层架构的所有操作和潜在错误点
2. **实时响应**: 错误发生时立即检测和告警
3. **智能恢复**: 自动识别错误类型并执行恢复策略
4. **性能优化**: 识别性能瓶颈，提供优化建议
5. **数据驱动**: 基于错误数据指导系统升级和优化

### 技术栈选择

- **Loguru**: 结构化日志记录 (156代码示例, 信任度8.0)
- **PySnooper**: 函数级调试追踪 (20代码示例, 信任度9.9)
- **Sentry**: 企业级错误监控平台 (70代码示例, 信任度9.0)
- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化监控面板

---

## 🏗️ 错误监控架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Canvas学习系统                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: CanvasOrchestrator (高级API层)                     │
│  ├─ Sub-agent调用接口                                       │
│  ├─ 完整操作工作流                                          │
│  └─ 错误监控装饰器集成                                      │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: CanvasBusinessLogic (业务逻辑层)                   │
│  ├─ v1.1布局算法                                           │
│  ├─ 上下文提取                                              │
│  ├─ 问题聚类                                                │
│  └─ 业务逻辑监控钩子                                        │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: CanvasJSONOperator (底层JSON操作)                  │
│  ├─ 原子化Canvas文件读写                                    │
│  ├─ 节点/边CRUD操作                                        │
│  └─ 底层操作异常捕获                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  错误监控中间层                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   Loguru    │  │  PySnooper  │  │      Sentry         │   │
│  │ 结构化日志   │  │ 函数追踪     │  │   实时监控告警       │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Prometheus  │  │   Grafana   │  │   错误分析引擎       │   │
│  │  指标收集    │  │  可视化面板  │  │   智能分类恢复       │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   存储和告警层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ 文件系统     │  │    Redis    │  │     邮件/钉钉        │   │
│  │  日志文件     │  │   缓存存储   │  │    告警通知         │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 监控层次设计

#### 1. 基础监控层 (Foundation Layer)
- **目标**: 捕获所有未处理异常
- **范围**: 全局异常处理、系统资源监控
- **工具**: Loguru + Python标准库

#### 2. 业务监控层 (Business Layer)
- **目标**: 监控Canvas特定业务逻辑
- **范围**: 文件操作、节点管理、颜色验证
- **工具**: PySnooper + 自定义装饰器

#### 3. 性能监控层 (Performance Layer)
- **目标**: 性能指标收集和分析
- **范围**: API响应时间、内存使用、操作耗时
- **工具**: Prometheus + Grafana

#### 4. 智能分析层 (Intelligence Layer)
- **目标**: 错误分类、趋势分析、自动恢复
- **范围**: 错误模式识别、恢复策略执行
- **工具**: Sentry + 自定义分析引擎

---

## 📊 Loguru结构化日志系统

### 核心配置

```python
"""
Canvas学习系统结构化日志配置
基于Loguru v0.7.0
"""
import sys
import json
from pathlib import Path
from loguru import logger
from typing import Dict, Any, Optional
from datetime import datetime

class CanvasLogConfig:
    """Canvas日志配置管理器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 移除默认处理器
        logger.remove()

        # 配置格式
        self.log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        self.setup_handlers()

    def setup_handlers(self):
        """设置日志处理器"""

        # 1. 控制台输出 - 开发环境
        logger.add(
            sys.stdout,
            format=self.log_format,
            level="DEBUG",
            colorize=True,
            filter=lambda record: record["extra"].get("env") == "dev"
        )

        # 2. 全部日志文件 - 轮转存储
        logger.add(
            self.log_dir / "canvas_{time:YYYY-MM-DD}.log",
            format=self.log_format,
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )

        # 3. 错误日志文件 - 仅错误和异常
        logger.add(
            self.log_dir / "errors_{time:YYYY-MM-DD}.log",
            format=self.log_format,
            level="ERROR",
            rotation="5 MB",
            retention="90 days",
            compression="zip",
            encoding="utf-8"
        )

        # 4. 结构化JSON日志 - 便于分析
        logger.add(
            self.log_dir / "structured_{time:YYYY-MM-DD}.jsonl",
            format="{message}",
            level="INFO",
            rotation="20 MB",
            retention="60 days",
            filter=self._structured_filter,
            serialize=True
        )

        # 5. Canvas操作专用日志
        logger.add(
            self.log_dir / "canvas_operations_{time:YYYY-MM-DD}.log",
            format=self.log_format,
            level="INFO",
            rotation="15 MB",
            retention="45 days",
            filter=lambda record: "canvas_operation" in record["extra"],
            encoding="utf-8"
        )

    def _structured_filter(self, record):
        """结构化日志过滤器"""
        return record["extra"].get("structured", False)

    @staticmethod
    def log_canvas_operation(
        operation: str,
        canvas_file: str,
        node_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """记录Canvas操作日志"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "canvas_file": canvas_file,
            "node_id": node_id,
            "details": details or {},
            "success": success,
            "error": error
        }

        if success:
            logger.info(
                f"Canvas操作成功: {operation}",
                canvas_operation=True,
                structured=True,
                **log_data
            )
        else:
            logger.error(
                f"Canvas操作失败: {operation} - {error}",
                canvas_operation=True,
                structured=True,
                **log_data
            )

    @staticmethod
    def log_performance(
        operation: str,
        duration_ms: float,
        canvas_file: Optional[str] = None,
        node_count: Optional[int] = None,
        memory_usage: Optional[float] = None
    ):
        """记录性能指标日志"""
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "canvas_file": canvas_file,
            "node_count": node_count,
            "memory_usage_mb": memory_usage
        }

        logger.info(
            f"性能指标: {operation} 耗时 {duration_ms:.2f}ms",
            performance=True,
            structured=True,
            **perf_data
        )

# 全局日志配置实例
canvas_logger = CanvasLogConfig()
```

### 日志级别定义

```python
class CanvasLogLevel:
    """Canvas系统日志级别定义"""

    # 标准级别
    TRACE = 5      # 详细跟踪信息
    DEBUG = 10     # 调试信息
    INFO = 20      # 一般信息
    WARNING = 30   # 警告信息
    ERROR = 40     # 错误信息
    CRITICAL = 50  # 严重错误

    # 业务级别
    CANVAS_READ = 15     # Canvas文件读取
    CANVAS_WRITE = 17    # Canvas文件写入
    NODE_OPERATION = 18  # 节点操作
    AGENT_CALL = 22      # Agent调用
    VALIDATION = 25      # 验证操作
    PERFORMANCE = 28     # 性能监控
```

### 结构化日志模式

```python
class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self):
        self.logger = logger

    def log_canvas_event(
        self,
        event_type: str,
        canvas_path: str,
        layer: str,
        operation: str,
        status: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录Canvas事件"""
        event_data = {
            "event_type": event_type,
            "canvas_path": canvas_path,
            "layer": layer,  # Layer1/2/3
            "operation": operation,
            "status": status,  # success/failure/partial
            "duration_ms": duration_ms,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        level = "ERROR" if status == "failure" else "INFO"
        getattr(self.logger, level.lower())(
            f"Canvas {event_type}: {operation} - {status}",
            structured=True,
            **event_data
        )

    def log_error_context(
        self,
        error: Exception,
        context: Dict[str, Any],
        recovery_attempted: bool = False,
        recovery_successful: bool = False
    ):
        """记录错误上下文"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "stack_trace": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

        self.logger.error(
            f"系统错误: {type(error).__name__}",
            structured=True,
            **error_data
        )
```

---

## 🔍 PySnooper函数级调试追踪系统

### 核心配置

```python
"""
Canvas学习系统函数级调试追踪配置
基于PySnooper v1.2.0
"""
import pysnooper
import functools
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

class CanvasDebugger:
    """Canvas系统调试追踪管理器"""

    def __init__(self, debug_dir: str = "debug"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self.trace_files = {}

    def get_trace_file(self, component: str) -> str:
        """获取组件追踪文件路径"""
        if component not in self.trace_files:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.trace_files[component] = str(
                self.debug_dir / f"{component}_trace_{timestamp}.log"
            )
        return self.trace_files[component]

def canvas_trace(
    component: str = "canvas",
    watch_vars: Optional[list] = None,
    depth: int = 1,
    prefix: Optional[str] = None
):
    """Canvas操作追踪装饰器"""
    def decorator(func: Callable) -> Callable:
        debugger = CanvasDebugger()
        trace_file = debugger.get_trace_file(component)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 配置PySnooper参数
            snooper_config = {
                'output': trace_file,
                'depth': depth,
                'prefix': prefix or f"[{component}] ",
                'overwrite': False,
                'thread_info': True,
                'custom_repr': (
                    (dict, lambda d: f"dict({len(d)} items)"),
                    (list, lambda l: f"list({len(l)} items)"),
                    (str, lambda s: f"str({len(s)} chars)"),
                )
            }

            if watch_vars:
                snooper_config['watch'] = watch_vars

            return pysnooper.snoop(**snooper_config)(func)(*args, **kwargs)

        return wrapper
    return decorator

class CanvasLayerTracer:
    """Canvas层级追踪器"""

    @staticmethod
    def trace_layer1():
        """Layer1: JSON操作追踪"""
        return canvas_trace(
            component="layer1_json",
            watch_vars=['canvas_data', 'node_id', 'operation'],
            depth=2,
            prefix="[L1-JSON] "
        )

    @staticmethod
    def trace_layer2():
        """Layer2: 业务逻辑追踪"""
        return canvas_trace(
            component="layer2_business",
            watch_vars=['canvas_path', 'nodes', 'cluster_result'],
            depth=1,
            prefix="[L2-BIZ] "
        )

    @staticmethod
    def trace_layer3():
        """Layer3: Agent调用追踪"""
        return canvas_trace(
            component="layer3_agent",
            watch_vars=['agent_name', 'input_data', 'response'],
            depth=1,
            prefix="[L3-AGENT] "
        )

# 使用示例
@CanvasLayerTracer.trace_layer1()
def read_canvas(canvas_path: str) -> Dict[str, Any]:
    """读取Canvas文件 - 带追踪"""
    # 实现逻辑...
    pass

@CanvasLayerTracer.trace_layer2()
def cluster_questions_by_topic(nodes: list) -> Dict[str, list]:
    """问题聚类 - 带追踪"""
    # 实现逻辑...
    pass
```

### 智能追踪配置

```python
class SmartTracer:
    """智能追踪器 - 根据操作类型动态调整追踪级别"""

    def __init__(self):
        self.operation_configs = {
            'file_io': {
                'component': 'file_operations',
                'watch_vars': ['file_path', 'file_size', 'operation'],
                'depth': 2
            },
            'node_operations': {
                'component': 'node_ops',
                'watch_vars': ['node_id', 'node_type', 'position', 'color'],
                'depth': 1
            },
            'agent_calls': {
                'component': 'agent_calls',
                'watch_vars': ['agent_name', 'input_length', 'response_length'],
                'depth': 1
            },
            'layout_calculations': {
                'component': 'layout',
                'watch_vars': ['node_count', 'canvas_width', 'positions'],
                'depth': 3
            }
        }

    def smart_trace(self, operation_type: str):
        """智能追踪装饰器"""
        config = self.operation_configs.get(operation_type, {})
        return canvas_trace(**config)

# 使用示例
tracer = SmartTracer()

@tracer.smart_trace('file_io')
def write_canvas(canvas_path: str, canvas_data: Dict[str, Any]):
    """写入Canvas文件 - 智能追踪"""
    pass

@tracer.smart_trace('layout_calculations')
def calculate_layout(nodes: list) -> Dict[str, Any]:
    """布局计算 - 智能追踪"""
    pass
```

### 追踪数据分析

```python
class TraceAnalyzer:
    """追踪数据分析器"""

    def __init__(self, trace_dir: str = "debug"):
        self.trace_dir = Path(trace_dir)

    def analyze_performance_bottlenecks(self, component: str) -> Dict[str, Any]:
        """分析性能瓶颈"""
        trace_file = self._get_latest_trace(component)
        if not trace_file:
            return {}

        # 解析追踪文件，识别慢操作
        bottlenecks = []
        with open(trace_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 分析逻辑...
        return {
            'component': component,
            'bottlenecks': bottlenecks,
            'recommendations': self._generate_recommendations(bottlenecks)
        }

    def analyze_error_patterns(self, component: str) -> Dict[str, Any]:
        """分析错误模式"""
        # 实现错误模式分析逻辑
        pass

    def _generate_recommendations(self, bottlenecks: list) -> list:
        """生成优化建议"""
        recommendations = []
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'file_io':
                recommendations.append("考虑使用缓存减少文件读写")
            elif bottleneck['type'] == 'computation':
                recommendations.append("考虑算法优化或并行处理")
        return recommendations
```

---

## 🚨 Sentry实时监控告警系统

### Sentry配置

```python
"""
Canvas学习系统Sentry配置
基于Sentry SDK v1.40.0
"""
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk import configure_scope, set_tag
import os

class CanvasSentryConfig:
    """Canvas系统Sentry配置管理器"""

    def __init__(self, dsn: Optional[str] = None, environment: str = "development"):
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.setup_sentry()

    def setup_sentry(self):
        """配置Sentry"""
        if not self.dsn:
            print("Warning: Sentry DSN not configured, monitoring disabled")
            return

        # 配置日志集成
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # 捕获INFO及以上级别
            event_level=logging.ERROR  # 发送ERROR及以上级别到Sentry
        )

        # 配置线程集成
        sentry_threading = ThreadingIntegration(
            propagate_hub=True,
            watchdog_thread_enabled=True
        )

        sentry_sdk.init(
            dsn=self.dsn,
            environment=self.environment,
            integrations=[
                sentry_logging,
                sentry_threading,
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,  # 10%的性能追踪采样率
            profiles_sample_rate=0.1,  # 10%的性能分析采样率

            # 错误过滤器
            before_send=self._before_send,
            before_breadcrumb=self._before_breadcrumb,

            # 自定义标签
            release="canvas-learning-system@1.0.0",
            server_name=os.getenv("HOSTNAME", "localhost"),
        )

    @staticmethod
    def _before_send(event, hint):
        """发送前过滤器 - 排除敏感信息"""
        # 移除敏感信息
        if 'request' in event:
            if 'headers' in event['request']:
                event['request']['headers'].pop('authorization', None)

        # 添加Canvas系统特定信息
        with configure_scope() as scope:
            scope.set_context("canvas_system", {
                "version": "1.0.0",
                "component": "learning_system"
            })

        return event

    @staticmethod
    def _before_breadcrumb(breadcrumb, hint):
        """面包屑过滤器"""
        # 过滤掉不重要的面包屑
        if breadcrumb.get('category') == 'http' and breadcrumb.get('data', {}).get('url', '').endswith('/health'):
            return None
        return breadcrumb

    @staticmethod
    def capture_canvas_error(
        error: Exception,
        canvas_file: Optional[str] = None,
        operation: Optional[str] = None,
        node_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """捕获Canvas系统错误"""
        with configure_scope() as scope:
            # 设置标签
            set_tag("component", "canvas_learning_system")
            if operation:
                set_tag("operation", operation)

            # 设置额外上下文
            scope.set_context("canvas_operation", {
                "canvas_file": canvas_file,
                "node_id": node_id,
                "operation": operation,
                "error_context": context or {}
            })

        # 发送到Sentry
        sentry_sdk.capture_exception(error)

    @staticmethod
    def capture_canvas_message(
        message: str,
        level: str = "info",
        canvas_file: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """捕获Canvas系统消息"""
        with configure_scope() as scope:
            scope.set_context("canvas_info", {
                "canvas_file": canvas_file,
                "operation": operation,
                **kwargs
            })

        sentry_sdk.capture_message(message, level=level)

    @staticmethod
    def start_transaction(operation: str, canvas_file: Optional[str] = None):
        """开始性能事务"""
        transaction = sentry_sdk.start_transaction(
            name=f"canvas.{operation}",
            op="canvas.operation"
        )

        with configure_scope() as scope:
            scope.set_tag("canvas_file", canvas_file or "unknown")

        return transaction

# 全局Sentry配置实例
canvas_sentry = CanvasSentryConfig(
    environment=os.getenv("ENVIRONMENT", "development")
)
```

### 告警规则配置

```python
class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alert_rules = self._setup_alert_rules()

    def _setup_alert_rules(self) -> Dict[str, Any]:
        """设置告警规则"""
        return {
            # 错误率告警
            'error_rate': {
                'threshold': 5.0,  # 5%错误率
                'window': '5m',
                'severity': 'warning'
            },

            # Canvas文件操作失败
            'canvas_file_errors': {
                'threshold': 3,  # 3次失败
                'window': '1m',
                'severity': 'critical'
            },

            # Agent调用失败
            'agent_call_failures': {
                'threshold': 2,  # 2次失败
                'window': '30s',
                'severity': 'warning'
            },

            # 响应时间告警
            'response_time': {
                'threshold': 5000,  # 5秒
                'window': '5m',
                'severity': 'warning'
            },

            # 内存使用告警
            'memory_usage': {
                'threshold': 80.0,  # 80%
                'window': '1m',
                'severity': 'warning'
            }
        }

    def check_alerts(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        alerts = []

        for rule_name, rule_config in self.alert_rules.items():
            if self._evaluate_rule(rule_name, rule_config, metrics):
                alert = self._create_alert(rule_name, rule_config, metrics)
                alerts.append(alert)

        return alerts

    def _evaluate_rule(self, rule_name: str, rule_config: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        """评估告警规则"""
        # 实现规则评估逻辑
        if rule_name == 'error_rate':
            error_rate = metrics.get('error_rate', 0)
            return error_rate > rule_config['threshold']

        # 其他规则评估...
        return False

    def _create_alert(self, rule_name: str, rule_config: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警"""
        return {
            'rule': rule_name,
            'severity': rule_config['severity'],
            'message': f"告警: {rule_name} 超过阈值 {rule_config['threshold']}",
            'metrics': metrics,
            'timestamp': time.time()
        }

# 告警通知配置
class NotificationService:
    """通知服务"""

    def __init__(self):
        self.webhook_url = os.getenv("DINGTALK_WEBHOOK")
        self.email_config = {
            'smtp_server': os.getenv("SMTP_SERVER"),
            'smtp_port': int(os.getenv("SMTP_PORT", "587")),
            'username': os.getenv("EMAIL_USERNAME"),
            'password': os.getenv("EMAIL_PASSWORD"),
            'recipients': os.getenv("ALERT_RECIPIENTS", "").split(',')
        }

    def send_alert(self, alert: Dict[str, Any]):
        """发送告警通知"""
        # 钉钉通知
        if self.webhook_url:
            self._send_dingtalk_alert(alert)

        # 邮件通知
        if self.email_config['smtp_server']:
            self._send_email_alert(alert)

    def _send_dingtalk_alert(self, alert: Dict[str, Any]):
        """发送钉钉告警"""
        # 实现钉钉Webhook通知逻辑
        pass

    def _send_email_alert(self, alert: Dict[str, Any]):
        """发送邮件告警"""
        # 实现邮件通知逻辑
        pass
```

---

## 🤖 智能错误分类和自动恢复机制

### 错误分类系统

```python
"""
Canvas学习系统智能错误分类和自动恢复
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import time
import traceback
from dataclasses import dataclass

class ErrorCategory(Enum):
    """错误分类枚举"""
    FILE_IO = "file_io"                    # 文件输入输出错误
    JSON_PARSE = "json_parse"              # JSON解析错误
    VALIDATION = "validation"              # 验证错误
    AGENT_CALL = "agent_call"              # Agent调用错误
    LAYOUT_CALCULATION = "layout_calc"     # 布局计算错误
    NETWORK = "network"                    # 网络错误
    MEMORY = "memory"                      # 内存错误
    PERMISSION = "permission"              # 权限错误
    BUSINESS_LOGIC = "business_logic"      # 业务逻辑错误
    UNKNOWN = "unknown"                    # 未知错误

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 1        # 轻微错误，可自动恢复
    MEDIUM = 2     # 中等错误，需要用户干预
    HIGH = 3       # 严重错误，需要立即处理
    CRITICAL = 4   # 致命错误，系统不可用

@dataclass
class ErrorInfo:
    """错误信息"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception]
    context: Dict[str, Any]
    timestamp: float
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3

class ErrorClassifier:
    """错误分类器"""

    def __init__(self):
        self.classification_rules = self._setup_classification_rules()

    def _setup_classification_rules(self) -> Dict[str, Any]:
        """设置分类规则"""
        return {
            # 文件IO错误
            'FileNotFoundError': {
                'category': ErrorCategory.FILE_IO,
                'severity': ErrorSeverity.MEDIUM,
                'keywords': ['file', 'path', 'directory', 'not found']
            },
            'PermissionError': {
                'category': ErrorCategory.PERMISSION,
                'severity': ErrorSeverity.HIGH,
                'keywords': ['permission', 'denied', 'access']
            },

            # JSON错误
            'json.JSONDecodeError': {
                'category': ErrorCategory.JSON_PARSE,
                'severity': ErrorSeverity.MEDIUM,
                'keywords': ['json', 'decode', 'parse']
            },

            # 网络错误
            'ConnectionError': {
                'category': ErrorCategory.NETWORK,
                'severity': ErrorSeverity.MEDIUM,
                'keywords': ['connection', 'network', 'timeout']
            },

            # 内存错误
            'MemoryError': {
                'category': ErrorCategory.MEMORY,
                'severity': ErrorSeverity.CRITICAL,
                'keywords': ['memory', 'out of memory']
            },

            # Canvas特定错误
            'CanvasValidationError': {
                'category': ErrorCategory.VALIDATION,
                'severity': ErrorSeverity.MEDIUM,
                'keywords': ['canvas', 'validation', 'invalid']
            },
            'AgentCallError': {
                'category': ErrorCategory.AGENT_CALL,
                'severity': ErrorSeverity.HIGH,
                'keywords': ['agent', 'call', 'response']
            }
        }

    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """分类错误"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # 查找匹配的分类规则
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM

        for rule_name, rule_config in self.classification_rules.items():
            if error_type == rule_name or any(keyword in error_message for keyword in rule_config['keywords']):
                category = rule_config['category']
                severity = rule_config['severity']
                break

        # 特殊处理逻辑
        if context:
            category, severity = self._apply_context_rules(category, severity, context)

        return ErrorInfo(
            category=category,
            severity=severity,
            message=str(error),
            exception=error,
            context=context or {},
            timestamp=time.time()
        )

    def _apply_context_rules(self, category: ErrorCategory, severity: ErrorSeverity, context: Dict[str, Any]) -> tuple:
        """应用上下文规则"""
        # 如果是临时文件操作，降低严重程度
        if category == ErrorCategory.FILE_IO and context.get('is_temp_file'):
            severity = ErrorSeverity.LOW

        # 如果是测试环境，降低严重程度
        if context.get('environment') == 'test':
            severity = min(severity, ErrorSeverity.MEDIUM)

        return category, severity
```

### 自动恢复系统

```python
class RecoveryStrategy:
    """恢复策略基类"""

    def __init__(self, name: str):
        self.name = name

    def can_recover(self, error_info: ErrorInfo) -> bool:
        """判断是否可以恢复"""
        raise NotImplementedError

    def recover(self, error_info: ErrorInfo) -> bool:
        """执行恢复操作"""
        raise NotImplementedError

class FileIORecoveryStrategy(RecoveryStrategy):
    """文件IO恢复策略"""

    def __init__(self):
        super().__init__("FileIORecovery")

    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.FILE_IO

    def recover(self, error_info: ErrorInfo) -> bool:
        """文件IO错误恢复"""
        file_path = error_info.context.get('file_path')
        if not file_path:
            return False

        try:
            # 策略1: 检查文件路径
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                return True

            # 策略2: 检查文件权限
            if not os.access(file_path, os.W_OK):
                # 尝试修改权限
                os.chmod(file_path, 0o644)
                return True

            # 策略3: 创建临时文件
            if error_info.context.get('operation') == 'write':
                temp_path = file_path + '.tmp'
                with open(temp_path, 'w') as f:
                    f.write('{}')
                os.rename(temp_path, file_path)
                return True

        except Exception:
            pass

        return False

class JSONParseRecoveryStrategy(RecoveryStrategy):
    """JSON解析恢复策略"""

    def __init__(self):
        super().__init__("JSONParseRecovery")

    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.JSON_PARSE

    def recover(self, error_info: ErrorInfo) -> bool:
        """JSON解析错误恢复"""
        json_content = error_info.context.get('json_content')
        if not json_content:
            return False

        try:
            # 策略1: 尝试修复常见JSON问题
            import re
            fixed_content = json_content

            # 移除末尾多余的逗号
            fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)

            # 尝试解析修复后的内容
            import json
            json.loads(fixed_content)

            # 如果解析成功，更新上下文
            error_info.context['fixed_json_content'] = fixed_content
            return True

        except Exception:
            # 策略2: 返回默认空结构
            error_info.context['fixed_json_content'] = '{"nodes": [], "edges": []}'
            return True

class AgentCallRecoveryStrategy(RecoveryStrategy):
    """Agent调用恢复策略"""

    def __init__(self):
        super().__init__("AgentCallRecovery")

    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.category == ErrorCategory.AGENT_CALL

    def recover(self, error_info: ErrorInfo) -> bool:
        """Agent调用错误恢复"""
        agent_name = error_info.context.get('agent_name')
        retry_count = error_info.context.get('retry_count', 0)

        if retry_count >= 3:
            return False

        # 策略1: 延迟重试
        time.sleep(2 ** retry_count)  # 指数退避

        # 策略2: 使用备用Agent
        backup_agents = {
            'oral-explanation': 'clarification-path',
            'clarification-path': 'four-level-explanation',
            'basic-decomposition': 'deep-decomposition'
        }

        if agent_name in backup_agents:
            error_info.context['backup_agent'] = backup_agents[agent_name]
            return True

        # 策略3: 使用缓存结果
        cache_key = error_info.context.get('cache_key')
        if cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                error_info.context['cached_result'] = cached_result
                return True

        return False

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        # 实现缓存逻辑
        return None

class AutoRecoveryManager:
    """自动恢复管理器"""

    def __init__(self):
        self.strategies = [
            FileIORecoveryStrategy(),
            JSONParseRecoveryStrategy(),
            AgentCallRecoveryStrategy(),
        ]
        self.recovery_stats = {}

    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """尝试自动恢复"""
        if error_info.recovery_attempts >= error_info.max_recovery_attempts:
            return False

        for strategy in self.strategies:
            if strategy.can_recover(error_info):
                try:
                    success = strategy.recover(error_info)
                    error_info.recovery_attempts += 1

                    # 记录恢复统计
                    strategy_name = strategy.name
                    if strategy_name not in self.recovery_stats:
                        self.recovery_stats[strategy_name] = {'attempts': 0, 'successes': 0}

                    self.recovery_stats[strategy_name]['attempts'] += 1
                    if success:
                        self.recovery_stats[strategy_name]['successes'] += 1

                    return success

                except Exception as recovery_error:
                    # 记录恢复失败
                    logger.error(f"恢复策略 {strategy.name} 执行失败: {recovery_error}")
                    continue

        return False

    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计"""
        stats = {}
        for strategy_name, data in self.recovery_stats.items():
            success_rate = data['successes'] / data['attempts'] if data['attempts'] > 0 else 0
            stats[strategy_name] = {
                'attempts': data['attempts'],
                'successes': data['successes'],
                'success_rate': success_rate
            }
        return stats
```

---

## 📈 性能监控和瓶颈识别系统

### 性能指标收集

```python
"""
Canvas学习系统性能监控
基于Prometheus指标收集
"""
import time
import psutil
import threading
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps

class CanvasMetrics:
    """Canvas系统指标收集器"""

    def __init__(self):
        # 操作计数器
        self.operation_counter = Counter(
            'canvas_operations_total',
            'Canvas操作总数',
            ['operation', 'status', 'layer']
        )

        # 响应时间直方图
        self.response_histogram = Histogram(
            'canvas_operation_duration_ms',
            'Canvas操作响应时间(毫秒)',
            ['operation', 'layer'],
            buckets=[10, 50, 100, 500, 1000, 5000, 10000, 30000]
        )

        # 内存使用量仪表盘
        self.memory_gauge = Gauge(
            'canvas_memory_usage_mb',
            'Canvas系统内存使用量(MB)'
        )

        # 文件大小仪表盘
        self.file_size_gauge = Gauge(
            'canvas_file_size_bytes',
            'Canvas文件大小(字节)',
            ['canvas_file']
        )

        # 节点数量仪表盘
        self.node_count_gauge = Gauge(
            'canvas_node_count',
            'Canvas节点数量',
            ['canvas_file', 'node_type']
        )

        # Agent调用指标
        self.agent_calls_counter = Counter(
            'canvas_agent_calls_total',
            'Agent调用总数',
            ['agent_name', 'status']
        )

        self.agent_response_histogram = Histogram(
            'canvas_agent_response_time_ms',
            'Agent响应时间(毫秒)',
            ['agent_name'],
            buckets=[1000, 5000, 10000, 30000, 60000, 120000]
        )

        # 错误计数器
        self.error_counter = Counter(
            'canvas_errors_total',
            'Canvas错误总数',
            ['error_type', 'severity', 'layer']
        )

        # 缓存指标
        self.cache_hits_counter = Counter(
            'canvas_cache_hits_total',
            '缓存命中次数',
            ['cache_type']
        )

        self.cache_misses_counter = Counter(
            'canvas_cache_misses_total',
            '缓存未命中次数',
            ['cache_type']
        )

    def record_operation(self, operation: str, status: str, layer: str, duration_ms: float):
        """记录操作指标"""
        self.operation_counter.labels(
            operation=operation,
            status=status,
            layer=layer
        ).inc()

        self.response_histogram.labels(
            operation=operation,
            layer=layer
        ).observe(duration_ms)

    def record_agent_call(self, agent_name: str, status: str, response_time_ms: float):
        """记录Agent调用指标"""
        self.agent_calls_counter.labels(
            agent_name=agent_name,
            status=status
        ).inc()

        self.agent_response_histogram.labels(
            agent_name=agent_name
        ).observe(response_time_ms)

    def record_error(self, error_type: str, severity: str, layer: str):
        """记录错误指标"""
        self.error_counter.labels(
            error_type=error_type,
            severity=severity,
            layer=layer
        ).inc()

    def update_memory_usage(self):
        """更新内存使用量"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_gauge.set(memory_mb)

    def update_file_metrics(self, canvas_file: str, file_size: int, node_counts: Dict[str, int]):
        """更新文件指标"""
        self.file_size_gauge.labels(canvas_file=canvas_file).set(file_size)

        for node_type, count in node_counts.items():
            self.node_count_gauge.labels(
                canvas_file=canvas_file,
                node_type=node_type
            ).set(count)

# 全局指标收集器
canvas_metrics = CanvasMetrics()

def performance_monitor(operation: str, layer: str = "unknown"):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                canvas_metrics.record_error(
                    error_type=type(e).__name__,
                    severity="high",
                    layer=layer
                )
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                canvas_metrics.record_operation(operation, status, layer, duration_ms)

        return wrapper
    return decorator
```

### 系统资源监控

```python
class ResourceMonitor:
    """系统资源监控器"""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """开始监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._collect_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"资源监控异常: {e}")

    def _collect_metrics(self):
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用情况
        memory = psutil.virtual_memory()

        # 磁盘使用情况
        disk = psutil.disk_usage('/')

        # 更新指标
        canvas_metrics.update_memory_usage()

        # 记录到日志
        logger.info(
            f"系统资源监控 - CPU: {cpu_percent}%, "
            f"内存: {memory.percent}%, "
            f"磁盘: {disk.percent}%"
        )

class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.bottleneck_thresholds = {
            'response_time': 5000,  # 5秒
            'memory_usage': 500,    # 500MB
            'error_rate': 0.05,     # 5%
            'agent_response_time': 30000  # 30秒
        }

    def analyze_performance(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能数据"""
        bottlenecks = []
        recommendations = []

        # 分析响应时间
        if 'response_times' in metrics_data:
            avg_response_time = sum(metrics_data['response_times']) / len(metrics_data['response_times'])
            if avg_response_time > self.bottleneck_thresholds['response_time']:
                bottlenecks.append({
                    'type': 'slow_response',
                    'value': avg_response_time,
                    'threshold': self.bottleneck_thresholds['response_time']
                })
                recommendations.append("考虑优化算法或增加缓存")

        # 分析内存使用
        if 'memory_usage' in metrics_data:
            memory_usage = metrics_data['memory_usage']
            if memory_usage > self.bottleneck_thresholds['memory_usage']:
                bottlenecks.append({
                    'type': 'high_memory',
                    'value': memory_usage,
                    'threshold': self.bottleneck_thresholds['memory_usage']
                })
                recommendations.append("考虑优化内存使用或增加流式处理")

        # 分析错误率
        if 'operations' in metrics_data:
            total_ops = metrics_data['operations'].get('total', 0)
            error_ops = metrics_data['operations'].get('errors', 0)
            error_rate = error_ops / total_ops if total_ops > 0 else 0

            if error_rate > self.bottleneck_thresholds['error_rate']:
                bottlenecks.append({
                    'type': 'high_error_rate',
                    'value': error_rate,
                    'threshold': self.bottleneck_thresholds['error_rate']
                })
                recommendations.append("检查错误处理逻辑，增加重试机制")

        return {
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'overall_health': self._calculate_health_score(bottlenecks)
        }

    def _calculate_health_score(self, bottlenecks: list) -> float:
        """计算系统健康分数"""
        base_score = 100.0

        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'slow_response':
                base_score -= min(30, (bottleneck['value'] / bottleneck['threshold'] - 1) * 30)
            elif bottleneck['type'] == 'high_memory':
                base_score -= min(25, (bottleneck['value'] / bottleneck['threshold'] - 1) * 25)
            elif bottleneck['type'] == 'high_error_rate':
                base_score -= min(40, (bottleneck['value'] / bottleneck['threshold'] - 1) * 40)

        return max(0, base_score)
```

---

## 📊 自动化错误报告生成系统

### 报告生成器

```python
"""
Canvas学习系统自动化错误报告生成
"""
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns

class ErrorReportGenerator:
    """错误报告生成器"""

    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)

    def generate_daily_report(self, date: Optional[datetime] = None) -> str:
        """生成日报"""
        target_date = date or datetime.now().date()

        # 收集数据
        report_data = {
            'date': target_date.isoformat(),
            'summary': self._generate_summary(target_date),
            'error_analysis': self._analyze_errors(target_date),
            'performance_metrics': self._get_performance_metrics(target_date),
            'trends': self._analyze_trends(target_date),
            'recommendations': self._generate_recommendations(target_date)
        }

        # 生成报告文件
        report_path = self._save_report(report_data, f"daily_report_{target_date.strftime('%Y%m%d')}")

        # 生成可视化图表
        self._generate_charts(report_data, target_date)

        return report_path

    def generate_weekly_report(self, week_start: Optional[datetime] = None) -> str:
        """生成周报"""
        start_date = week_start or (datetime.now() - timedelta(days=datetime.now().weekday()))
        end_date = start_date + timedelta(days=6)

        # 收集周数据
        weekly_data = self._collect_weekly_data(start_date, end_date)

        report_data = {
            'week_start': start_date.isoformat(),
            'week_end': end_date.isoformat(),
            'weekly_summary': self._generate_weekly_summary(weekly_data),
            'error_patterns': self._analyze_weekly_errors(weekly_data),
            'performance_trends': self._analyze_weekly_performance(weekly_data),
            'system_health': self._calculate_system_health(weekly_data),
            'improvement_plan': self._generate_improvement_plan(weekly_data)
        }

        report_path = self._save_report(report_data, f"weekly_report_{start_date.strftime('%Y%m%d')}")
        self._generate_weekly_charts(report_data, start_date)

        return report_path

    def _generate_summary(self, date: datetime) -> Dict[str, Any]:
        """生成日报摘要"""
        # 从日志文件收集数据
        log_file = Path(f"logs/canvas_{date.strftime('%Y-%m-%d')}.log")

        if not log_file.exists():
            return {'status': 'no_data'}

        # 分析日志文件
        summary = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'error_rate': 0.0,
            'average_response_time': 0.0,
            'top_errors': [],
            'peak_usage_time': None
        }

        # 实现日志分析逻辑
        # ...

        return summary

    def _analyze_errors(self, date: datetime) -> Dict[str, Any]:
        """分析错误"""
        error_file = Path(f"logs/errors_{date.strftime('%Y-%m-%d')}.log")

        if not error_file.exists():
            return {'status': 'no_errors'}

        # 错误分析
        error_analysis = {
            'total_errors': 0,
            'error_categories': {},
            'error_trend': [],
            'critical_errors': [],
            'recovered_errors': 0,
            'recovery_rate': 0.0
        }

        # 实现错误分析逻辑
        # ...

        return error_analysis

    def _get_performance_metrics(self, date: datetime) -> Dict[str, Any]:
        """获取性能指标"""
        performance_metrics = {
            'response_times': {
                'min': 0,
                'max': 0,
                'avg': 0,
                'p95': 0,
                'p99': 0
            },
            'memory_usage': {
                'avg': 0,
                'peak': 0,
                'min': 0
            },
            'agent_performance': {},
            'canvas_file_metrics': {}
        }

        # 实现性能指标收集
        # ...

        return performance_metrics

    def _analyze_trends(self, date: datetime) -> Dict[str, Any]:
        """分析趋势"""
        # 获取过去7天的数据
        trend_data = {
            'error_rate_trend': [],
            'performance_trend': [],
            'usage_pattern': []
        }

        # 实现趋势分析
        # ...

        return trend_data

    def _generate_recommendations(self, date: datetime) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于错误分析生成建议
        error_analysis = self._analyze_errors(date)
        if error_analysis.get('total_errors', 0) > 10:
            recommendations.append("建议增加错误监控和告警机制")

        # 基于性能指标生成建议
        performance = self._get_performance_metrics(date)
        if performance['response_times']['avg'] > 5000:
            recommendations.append("建议优化响应时间，考虑使用缓存")

        # 基于使用模式生成建议
        recommendations.extend(self._generate_usage_recommendations(date))

        return recommendations

    def _generate_usage_recommendations(self, date: datetime) -> List[str]:
        """生成使用建议"""
        # 分析使用模式，生成针对性建议
        return [
            "建议定期清理临时文件",
            "建议优化大文件的加载策略",
            "建议增加用户操作指导"
        ]

    def _save_report(self, data: Dict[str, Any], filename: str) -> str:
        """保存报告"""
        # 保存JSON格式
        json_path = self.report_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 生成HTML格式报告
        html_path = self.report_dir / f"{filename}.html"
        html_content = self._generate_html_report(data)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(html_path)

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Canvas学习系统错误报告</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }
                .error { color: red; }
                .success { color: green; }
                .warning { color: orange; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Canvas学习系统错误报告</h1>
                <p>生成时间: {generation_time}</p>
                <p>报告日期: {report_date}</p>
            </div>

            {content}

        </body>
        </html>
        """

        # 生成报告内容
        content = self._generate_html_content(data)

        return html_template.format(
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            report_date=data.get('date', data.get('week_start', 'Unknown')),
            content=content
        )

    def _generate_html_content(self, data: Dict[str, Any]) -> str:
        """生成HTML内容"""
        content = ""

        # 摘要部分
        if 'summary' in data:
            content += "<div class='section'><h2>系统摘要</h2>"
            summary = data['summary']
            if summary.get('status') != 'no_data':
                content += f"""
                <div class="metric">总操作数: {summary.get('total_operations', 0)}</div>
                <div class="metric success">成功操作: {summary.get('successful_operations', 0)}</div>
                <div class="metric error">失败操作: {summary.get('failed_operations', 0)}</div>
                <div class="metric">错误率: {summary.get('error_rate', 0):.2%}</div>
                <div class="metric">平均响应时间: {summary.get('average_response_time', 0):.2f}ms</div>
                """
            content += "</div>"

        # 错误分析部分
        if 'error_analysis' in data:
            content += "<div class='section'><h2>错误分析</h2>"
            error_analysis = data['error_analysis']
            if error_analysis.get('status') != 'no_errors':
                content += f"""
                <div class="metric error">总错误数: {error_analysis.get('total_errors', 0)}</div>
                <div class="metric success">已恢复错误: {error_analysis.get('recovered_errors', 0)}</div>
                <div class="metric">恢复率: {error_analysis.get('recovery_rate', 0):.2%}</div>
                """
            content += "</div>"

        # 建议部分
        if 'recommendations' in data:
            content += "<div class='section'><h2>改进建议</h2><ul>"
            for recommendation in data['recommendations']:
                content += f"<li>{recommendation}</li>"
            content += "</ul></div>"

        return content

    def _generate_charts(self, data: Dict[str, Any], date: datetime):
        """生成图表"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 生成错误分布图
        if 'error_analysis' in data:
            self._generate_error_chart(data['error_analysis'], date)

        # 生成性能趋势图
        if 'performance_metrics' in data:
            self._generate_performance_chart(data['performance_metrics'], date)

    def _generate_error_chart(self, error_data: Dict[str, Any], date: datetime):
        """生成错误分布图"""
        if not error_data.get('error_categories'):
            return

        categories = list(error_data['error_categories'].keys())
        counts = list(error_data['error_categories'].values())

        plt.figure(figsize=(10, 6))
        plt.bar(categories, counts)
        plt.title(f'错误分布 - {date.strftime("%Y-%m-%d")}')
        plt.xlabel('错误类别')
        plt.ylabel('错误数量')
        plt.xticks(rotation=45)
        plt.tight_layout()

        chart_path = self.report_dir / f"error_distribution_{date.strftime('%Y%m%d')}.png"
        plt.savefig(chart_path)
        plt.close()

    def _generate_performance_chart(self, performance_data: Dict[str, Any], date: datetime):
        """生成性能图表"""
        if 'response_times' not in performance_data:
            return

        response_times = performance_data['response_times']

        plt.figure(figsize=(10, 6))
        metrics = ['最小值', '最大值', '平均值', 'P95', 'P99']
        values = [
            response_times['min'],
            response_times['max'],
            response_times['avg'],
            response_times['p95'],
            response_times['p99']
        ]

        plt.bar(metrics, values)
        plt.title(f'响应时间分布 - {date.strftime("%Y-%m-%d")} (毫秒)')
        plt.ylabel('响应时间 (ms)')

        chart_path = self.report_dir / f"performance_metrics_{date.strftime('%Y%m%d')}.png"
        plt.savefig(chart_path)
        plt.close()
```

---

## 🔧 集成配置和使用指南

### 统一监控配置

```python
"""
Canvas学习系统统一监控配置
"""
import os
import logging
from .canvas_logger import CanvasLogConfig
from .canvas_sentry import CanvasSentryConfig
from .error_classifier import ErrorClassifier
from .auto_recovery import AutoRecoveryManager
from .performance_monitor import CanvasMetrics, ResourceMonitor
from .report_generator import ErrorReportGenerator

class CanvasMonitoringSystem:
    """Canvas学习系统统一监控管理"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()

        # 初始化各个组件
        self.logger = CanvasLogConfig()
        self.sentry = CanvasSentryConfig(
            environment=self.config.get('environment', 'development')
        )
        self.error_classifier = ErrorClassifier()
        self.recovery_manager = AutoRecoveryManager()
        self.metrics = CanvasMetrics()
        self.resource_monitor = ResourceMonitor()
        self.report_generator = ErrorReportGenerator()

        # 启动监控
        self._start_monitoring()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'sentry_dsn': os.getenv('SENTRY_DSN'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'monitoring_enabled': os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            'auto_recovery_enabled': os.getenv('AUTO_RECOVERY_ENABLED', 'true').lower() == 'true',
            'performance_monitoring_enabled': os.getenv('PERFORMANCE_MONITORING_ENABLED', 'true').lower() == 'true',
            'report_generation_enabled': os.getenv('REPORT_GENERATION_ENABLED', 'true').lower() == 'true'
        }

    def _start_monitoring(self):
        """启动监控"""
        if self.config.get('performance_monitoring_enabled'):
            self.resource_monitor.start_monitoring()

        # 启动Prometheus HTTP服务器
        if self.config.get('prometheus_enabled', True):
            from prometheus_client import start_http_server
            start_http_server(8000)
            print("Prometheus metrics server started on port 8000")

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """统一错误处理"""
        # 分类错误
        error_info = self.error_classifier.classify_error(error, context)

        # 记录日志
        self.logger.log_error_context(error, context)

        # 发送到Sentry
        self.sentry.capture_canvas_error(
            error=error,
            canvas_file=context.get('canvas_file'),
            operation=context.get('operation'),
            node_id=context.get('node_id'),
            context=context
        )

        # 记录指标
        self.metrics.record_error(
            error_type=type(error).__name__,
            severity=error_info.severity.name,
            layer=context.get('layer', 'unknown')
        )

        # 尝试自动恢复
        if self.config.get('auto_recovery_enabled'):
            recovery_success = self.recovery_manager.attempt_recovery(error_info)
            if recovery_success:
                logger.info(f"错误自动恢复成功: {error}")
                return True

        return False

    def record_operation(self, operation: str, status: str, layer: str, duration_ms: float, **kwargs):
        """记录操作"""
        # 记录日志
        self.logger.log_canvas_operation(
            operation=operation,
            canvas_file=kwargs.get('canvas_file'),
            node_id=kwargs.get('node_id'),
            details=kwargs.get('details'),
            success=(status == 'success')
        )

        # 记录指标
        self.metrics.record_operation(operation, status, layer, duration_ms)

        # 记录性能日志
        self.logger.log_performance(
            operation=operation,
            duration_ms=duration_ms,
            canvas_file=kwargs.get('canvas_file'),
            node_count=kwargs.get('node_count')
        )

    def generate_daily_report(self, date: datetime = None) -> str:
        """生成日报"""
        if not self.config.get('report_generation_enabled'):
            logger.warning("报告生成功能未启用")
            return ""

        return self.report_generator.generate_daily_report(date)

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        # 收集各种指标
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {
                'logging': 'healthy',
                'error_handling': 'healthy',
                'performance': 'healthy',
                'recovery': 'healthy'
            },
            'metrics': {
                'error_rate': 0.0,
                'average_response_time': 0.0,
                'memory_usage': 0.0,
                'recovery_success_rate': 0.0
            },
            'alerts': []
        }

        # 获取恢复统计
        recovery_stats = self.recovery_manager.get_recovery_stats()
        health_status['metrics']['recovery_success_rate'] = recovery_stats.get('success_rate', 0.0)

        return health_status

    def shutdown(self):
        """关闭监控系统"""
        if self.resource_monitor:
            self.resource_monitor.stop_monitoring()
        logger.info("Canvas监控系统已关闭")

# 全局监控实例
canvas_monitoring = CanvasMonitoringSystem()
```

### 使用示例

```python
"""
Canvas监控系统使用示例
"""
from canvas_monitoring import canvas_monitoring
from canvas_utils import CanvasJSONOperator

# 使用示例1: 自动错误处理
try:
    # Canvas操作
    canvas_op = CanvasJSONOperator()
    result = canvas_op.read_canvas("example.canvas")
except Exception as e:
    # 自动错误处理和恢复
    recovered = canvas_monitoring.handle_error(e, {
        'canvas_file': 'example.canvas',
        'operation': 'read_canvas',
        'layer': 'layer1'
    })

    if not recovered:
        # 手动处理或通知用户
        print(f"操作失败，无法自动恢复: {e}")

# 使用示例2: 性能监控装饰器
@canvas_monitoring.performance_monitor(operation="agent_call", layer="layer3")
def call_agent(agent_name: str, input_data: dict):
    """Agent调用 - 带性能监控"""
    # Agent调用逻辑
    pass

# 使用示例3: 手动记录操作
canvas_monitoring.record_operation(
    operation="create_node",
    status="success",
    layer="layer1",
    duration_ms=150.5,
    canvas_file="example.canvas",
    node_id="node123",
    node_type="question"
)

# 使用示例4: 生成报告
report_path = canvas_monitoring.generate_daily_report()
print(f"日报已生成: {report_path}")

# 使用示例5: 检查系统健康
health = canvas_monitoring.get_system_health()
print(f"系统健康状态: {health['overall_status']}")
```

---

## 📋 部署和配置清单

### 环境变量配置

```bash
# 环境配置
ENVIRONMENT=production                    # 环境: development/production
LOG_LEVEL=INFO                          # 日志级别: DEBUG/INFO/WARNING/ERROR

# Sentry配置
SENTRY_DSN=https://your-sentry-dsn     # Sentry DSN
SENTRY_ENVIRONMENT=production           # Sentry环境

# 监控功能开关
MONITORING_ENABLED=true                 # 启用监控
AUTO_RECOVERY_ENABLED=true              # 启用自动恢复
PERFORMANCE_MONITORING_ENABLED=true     # 启用性能监控
REPORT_GENERATION_ENABLED=true          # 启用报告生成

# 告警配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@example.com,dev@example.com

# Prometheus配置
PROMETHEUS_ENABLED=true                 # 启用Prometheus指标
PROMETHEUS_PORT=8000                   # Prometheus端口
```

### 依赖包清单

```txt
# requirements.txt 追加内容
loguru>=0.7.0
pysnooper>=1.2.0
sentry-sdk>=1.40.0
prometheus-client>=0.19.0
psutil>=5.9.0
matplotlib>=3.7.0
seaborn>=0.12.0
pandas>=2.0.0
redis>=4.6.0
```

### 目录结构

```
C:/Users/ROG/托福/
├── canvas_monitoring/                 # 监控系统模块
│   ├── __init__.py
│   ├── canvas_logger.py              # Loguru日志配置
│   ├── canvas_sentry.py              # Sentry配置
│   ├── error_classifier.py           # 错误分类器
│   ├── auto_recovery.py              # 自动恢复系统
│   ├── performance_monitor.py        # 性能监控
│   ├── report_generator.py           # 报告生成器
│   └── monitoring_system.py          # 统一监控系统
│
├── logs/                              # 日志文件目录
│   ├── canvas_YYYY-MM-DD.log         # 全部日志
│   ├── errors_YYYY-MM-DD.log         # 错误日志
│   ├── structured_YYYY-MM-DD.jsonl   # 结构化日志
│   └── canvas_operations_YYYY-MM-DD.log  # Canvas操作日志
│
├── debug/                             # 调试追踪文件
│   ├── layer1_json_trace_YYYYMMDD_HHMMSS.log
│   ├── layer2_business_trace_YYYYMMDD_HHMMSS.log
│   └── layer3_agent_trace_YYYYMMDD_HHMMSS.log
│
├── reports/                           # 错误报告目录
│   ├── daily_report_YYYYMMDD.html    # 日报
│   ├── daily_report_YYYYMMDD.json    # 日报数据
│   ├── weekly_report_YYYYMMDD.html   # 周报
│   └── charts/                        # 图表文件
│       ├── error_distribution_YYYYMMDD.png
│       └── performance_metrics_YYYYMMDD.png
│
└── monitoring_config/                 # 监控配置文件
    ├── prometheus.yml                # Prometheus配置
    ├── grafana/                      # Grafana仪表板
    │   └── canvas-dashboard.json
    └── alert_rules.yml               # 告警规则
```

### 初始化脚本

```python
"""
monitoring_init.py - 监控系统初始化脚本
"""
import os
import sys
from pathlib import Path

def setup_monitoring():
    """初始化监控系统"""
    print("初始化Canvas学习系统监控...")

    # 创建必要目录
    directories = [
        "logs",
        "debug",
        "reports",
        "reports/charts",
        "monitoring_config",
        "monitoring_config/grafana"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

    # 检查环境变量
    required_env_vars = [
        "ENVIRONMENT",
        "SENTRY_DSN"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  警告: 缺少环境变量: {', '.join(missing_vars)}")
    else:
        print("✓ 环境变量检查通过")

    # 创建示例配置文件
    create_sample_configs()

    print("✓ 监控系统初始化完成")
    print("\n使用方法:")
    print("1. 在代码中导入: from canvas_monitoring import canvas_monitoring")
    print("2. 错误处理: canvas_monitoring.handle_error(error, context)")
    print("3. 性能监控: @canvas_monitoring.performance_monitor(operation='xxx')")

def create_sample_configs():
    """创建示例配置文件"""
    # Prometheus配置
    prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'canvas-learning-system'
    static_configs:
      - targets: ['localhost:8000']
"""

    with open("monitoring_config/prometheus.yml", "w") as f:
        f.write(prometheus_config)

    print("✓ 创建Prometheus配置文件")

if __name__ == "__main__":
    setup_monitoring()
```

---

## 🎯 总结和建议

### 系统优势

1. **全面监控**: 覆盖3层架构的所有关键操作和潜在错误点
2. **实时响应**: 错误发生时立即检测、记录和尝试自动恢复
3. **智能分析**: 自动分类错误，识别模式，提供针对性恢复策略
4. **性能优化**: 实时监控性能指标，识别瓶颈，提供优化建议
5. **数据驱动**: 基于历史数据生成报告，指导系统升级和优化

### 实施建议

1. **分阶段部署**:
   - 第一阶段: 部署基础日志监控和错误处理
   - 第二阶段: 集成Sentry实时监控和告警
   - 第三阶段: 启用性能监控和自动报告生成
   - 第四阶段: 完善智能恢复和预测分析

2. **监控重点**:
   - Canvas文件读写操作
   - Agent调用成功率
   - 系统响应时间
   - 内存使用情况
   - 错误恢复成功率

3. **告警配置**:
   - 错误率超过5%时告警
   - 响应时间超过5秒时告警
   - Agent调用失败时立即告警
   - 内存使用超过80%时告警

### 维护建议

1. **定期检查**: 每周检查监控数据和报告
2. **配置优化**: 根据实际使用情况调整监控阈值
3. **日志清理**: 定期清理过期日志文件
4. **性能调优**: 基于监控数据持续优化系统性能
5. **功能扩展**: 根据需求增加新的监控指标和分析功能

这个企业级错误监控日志系统将为Canvas学习系统提供完整的可观测性，帮助及时发现和解决问题，为系统的稳定运行和持续优化提供强有力的支持。
```
TodoWrite
<arg_key>todos</arg_key>
<arg_value>[{"content": "设计企业级错误监控架构，集成到现有3层Python架构", "status": "completed", "activeForm": "设计企业级错误监控架构，集成到现有3层Python架构"}, {"content": "创建基于Loguru的结构化日志系统配置", "status": "completed", "activeForm": "创建基于Loguru的结构化日志系统配置"}, {"content": "设计基于PySnooper的函数级调试追踪系统", "status": "in_progress", "activeForm": "设计基于PySnooper的函数级调试追踪系统"}, {"content": "创建基于Sentry的实时监控告警系统", "status": "pending", "activeForm": "创建基于Sentry的实时监控告警系统"}, {"content": "设计智能错误分类和自动恢复机制", "status": "pending", "activeForm": "设计智能错误分类和自动恢复机制"}, {"content": "创建性能监控和瓶颈识别系统", "status": "pending", "activeForm": "创建性能监控和瓶颈识别系统"}, {"content": "设计自动化错误报告生成系统", "status": "pending", "activeForm": "设计自动化错误报告生成系统"}, {"content": "编写完整的错误监控配置和使用文档", "status": "pending", "activeForm": "编写完整的错误监控配置和使用文档"}]
