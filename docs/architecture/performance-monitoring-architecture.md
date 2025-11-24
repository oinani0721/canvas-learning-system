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
  prd: "v1.1.9"
  epic: ["Epic 17"]

changes_from_previous:
  - "Initial Performance Monitoring Architecture document"
---

# 性能监控与优化架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义Canvas Learning System的性能监控、指标采集、告警和优化策略架构，覆盖Epic 17的所有性能相关需求。

### 1.1 设计目标

- 实时监控系统关键性能指标
- 自动化告警和异常检测
- 性能瓶颈识别和优化建议
- 资源使用追踪和成本控制

### 1.2 关联文档

- PRD Epic 17: 性能优化和监控
- `epic10-concurrency-definition.md`: 并发限制矩阵
- `COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md`: 记忆系统性能要求

---

## 2. 监控指标体系

### 2.1 核心性能指标 (KPIs)

| 指标类别 | 指标名称 | 目标值 | 告警阈值 |
|---------|---------|--------|---------|
| **API响应** | 单API请求响应时间 | <500ms | >1000ms |
| **Canvas操作** | Canvas文件读取 | <200ms | >500ms |
| **Agent执行** | Agent调用时间 | <5s | >10s |
| **并行处理** | 智能分组分析 | <3s | >5s |
| **记忆查询** | Graphiti查询 | <200ms | >500ms |
| **向量搜索** | LanceDB语义搜索 | <100ms | >300ms |

### 2.2 资源使用指标

```python
# 资源监控数据结构
class ResourceMetrics:
    cpu_usage_percent: float      # CPU使用率
    memory_usage_mb: float        # 内存使用量
    memory_usage_percent: float   # 内存使用率
    disk_io_read_mb: float        # 磁盘读取
    disk_io_write_mb: float       # 磁盘写入
    network_io_mb: float          # 网络IO
    active_connections: int       # 活跃连接数
    thread_count: int             # 线程数
```

### 2.3 业务指标

| 指标 | 描述 | 采集频率 |
|------|------|---------|
| `canvas_operations_total` | Canvas操作总数 | 实时 |
| `agent_invocations_total` | Agent调用总数 | 实时 |
| `concurrent_tasks` | 并发任务数 | 每秒 |
| `error_rate` | 错误率 | 每分钟 |
| `user_sessions_active` | 活跃用户会话 | 每分钟 |

---

## 3. 监控架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Canvas Learning System                    │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  FastAPI    │  LangGraph  │  Obsidian   │   Memory System   │
│  Backend    │   Agents    │   Plugin    │   (3-Layer)       │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       └─────────────┴─────────────┴────────────────┘
                            │
                   ┌────────▼────────┐
                   │  Metrics Agent  │
                   │  (采集层)        │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
       │  Prometheus │ │  Logs   │ │   Traces    │
       │  (Metrics)  │ │ (JSON)  │ │ (OpenTel)   │
       └──────┬──────┘ └────┬────┘ └──────┬──────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                   ┌────────▼────────┐
                   │   Dashboard     │
                   │  (Grafana/UI)   │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  Alert Manager  │
                   │  (告警系统)       │
                   └─────────────────┘
```

### 3.2 技术选型

| 组件 | 技术方案 | 说明 |
|------|---------|------|
| **指标采集** | Prometheus Python Client | 轻量级，与FastAPI集成良好 |
| **日志系统** | Python logging + JSON格式 | 结构化日志，便于分析 |
| **链路追踪** | OpenTelemetry (可选) | 分布式追踪 |
| **可视化** | Grafana / 内置Dashboard | 实时监控面板 |
| **告警** | AlertManager / 自定义 | 多渠道通知 |

---

## 4. 指标采集实现

### 4.1 FastAPI中间件

```python
# ✅ Verified from Context7 FastAPI (Middleware)
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge
import time

# 定义指标
REQUEST_COUNT = Counter(
    'canvas_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'canvas_api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

CONCURRENT_REQUESTS = Gauge(
    'canvas_api_concurrent_requests',
    'Number of concurrent requests'
)

app = FastAPI()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """性能监控中间件"""
    CONCURRENT_REQUESTS.inc()
    start_time = time.time()

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        CONCURRENT_REQUESTS.dec()

        # 记录指标
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

    return response
```

### 4.2 Agent性能追踪

```python
# Agent执行指标
AGENT_EXECUTION_TIME = Histogram(
    'canvas_agent_execution_seconds',
    'Agent execution time',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

AGENT_ERRORS = Counter(
    'canvas_agent_errors_total',
    'Agent execution errors',
    ['agent_type', 'error_type']
)

def track_agent_execution(agent_type: str):
    """Agent执行追踪装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                AGENT_ERRORS.labels(
                    agent_type=agent_type,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start
                AGENT_EXECUTION_TIME.labels(
                    agent_type=agent_type
                ).observe(duration)
        return wrapper
    return decorator
```

### 4.3 记忆系统性能监控

```python
# 记忆系统指标
MEMORY_QUERY_LATENCY = Histogram(
    'canvas_memory_query_seconds',
    'Memory system query latency',
    ['memory_type', 'operation'],  # graphiti/temporal/semantic
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)

MEMORY_STORAGE_SIZE = Gauge(
    'canvas_memory_storage_bytes',
    'Memory system storage size',
    ['memory_type']
)

# 使用示例
async def query_graphiti(query: str):
    with MEMORY_QUERY_LATENCY.labels(
        memory_type='graphiti',
        operation='search'
    ).time():
        result = await graphiti_client.search(query)
    return result
```

---

## 5. 告警策略

### 5.1 告警级别

| 级别 | 颜色 | 触发条件 | 响应时间 |
|------|------|---------|---------|
| **Critical** | 红色 | 服务不可用、数据丢失风险 | 立即 |
| **Warning** | 橙色 | 性能下降、资源紧张 | 15分钟 |
| **Info** | 蓝色 | 异常但不影响服务 | 1小时 |

### 5.2 告警规则

```yaml
# 告警规则配置
alerts:
  - name: HighAPILatency
    expr: canvas_api_request_latency_seconds{quantile="0.95"} > 1.0
    for: 5m
    severity: warning
    annotations:
      summary: "API响应时间过高"
      description: "95分位API响应时间超过1秒，当前值: {{ $value }}s"

  - name: HighErrorRate
    expr: rate(canvas_api_requests_total{status=~"5.."}[5m]) / rate(canvas_api_requests_total[5m]) > 0.05
    for: 2m
    severity: critical
    annotations:
      summary: "错误率过高"
      description: "5分钟内错误率超过5%，当前值: {{ $value | humanizePercentage }}"

  - name: AgentExecutionSlow
    expr: canvas_agent_execution_seconds{quantile="0.95"} > 10
    for: 5m
    severity: warning
    annotations:
      summary: "Agent执行过慢"
      description: "Agent {{ $labels.agent_type }} 95分位执行时间超过10秒"

  - name: MemorySystemDown
    expr: up{job="memory_system"} == 0
    for: 1m
    severity: critical
    annotations:
      summary: "记忆系统不可用"
      description: "{{ $labels.memory_type }} 记忆系统连接失败"

  - name: HighConcurrentTasks
    expr: canvas_api_concurrent_requests > 100
    for: 2m
    severity: warning
    annotations:
      summary: "并发任务过多"
      description: "当前并发任务数: {{ $value }}，可能导致性能下降"
```

### 5.3 通知渠道

| 渠道 | 用途 | 配置 |
|------|------|------|
| 控制台日志 | 开发调试 | 默认启用 |
| 文件日志 | 历史记录 | `logs/alerts.log` |
| Obsidian通知 | 用户提醒 | Plugin内置 |
| Webhook | 自定义集成 | 可选 |

---

## 6. 性能优化策略

### 6.1 Canvas操作优化

| 优化点 | 策略 | 预期收益 |
|--------|------|---------|
| **文件读取** | 增量读取 + 缓存 | -50%延迟 |
| **JSON解析** | orjson替代json | -30%CPU |
| **批量写入** | 合并多次写入 | -60%IO |

```python
# 文件读取缓存
from functools import lru_cache
import orjson

@lru_cache(maxsize=100)
def read_canvas_cached(canvas_path: str, mtime: float):
    """带缓存的Canvas读取"""
    with open(canvas_path, 'rb') as f:
        return orjson.loads(f.read())

def read_canvas(canvas_path: str):
    mtime = os.path.getmtime(canvas_path)
    return read_canvas_cached(canvas_path, mtime)
```

### 6.2 Agent并行优化

```python
# 资源感知并行调度
class ResourceAwareScheduler:
    def __init__(self):
        self.max_concurrent = 50  # 最大并发
        self.semaphore = asyncio.Semaphore(50)

    async def schedule(self, tasks: List[Coroutine]):
        """根据资源动态调整并发"""
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent

        # 动态调整并发数
        if cpu_usage > 80 or memory_usage > 85:
            effective_limit = max(10, self.max_concurrent // 2)
        else:
            effective_limit = self.max_concurrent

        semaphore = asyncio.Semaphore(effective_limit)

        async def limited_task(task):
            async with semaphore:
                return await task

        return await asyncio.gather(*[limited_task(t) for t in tasks])
```

### 6.3 记忆系统优化

| 系统 | 优化策略 | 实现 |
|------|---------|------|
| **Graphiti** | 查询结果缓存 | Redis/本地缓存 |
| **LanceDB** | 向量索引预热 | 启动时加载 |
| **Temporal** | 时间范围索引 | 按日期分区 |

---

## 7. 监控Dashboard

### 7.1 Dashboard布局

```
┌─────────────────────────────────────────────────────────┐
│  Canvas Learning System - Performance Dashboard         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ API请求/秒  │  │ 平均延迟    │  │ 错误率      │     │
│  │   156.3    │  │   234ms    │  │   0.12%    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         API响应时间分布 (最近1小时)              │   │
│  │  [Histogram Chart]                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │  Agent执行时间       │  │  记忆系统延迟        │   │
│  │  [By Agent Type]     │  │  [By Memory Type]    │   │
│  └──────────────────────┘  └──────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         资源使用趋势 (CPU/Memory)               │   │
│  │  [Line Chart]                                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 7.2 关键面板

1. **概览面板**: 请求量、延迟、错误率
2. **API性能**: 各端点响应时间分布
3. **Agent性能**: 各Agent执行时间对比
4. **记忆系统**: 各层查询延迟
5. **资源监控**: CPU、内存、磁盘IO

---

## 8. API端点

### 8.1 监控API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/metrics` | GET | Prometheus格式指标 |
| `/health` | GET | 健康检查（已在canvas-api中） |
| `/metrics/summary` | GET | JSON格式指标摘要 |
| `/metrics/alerts` | GET | 当前活跃告警 |

### 8.2 OpenAPI定义

详见 `specs/api/canvas-api.openapi.yml` - 需要添加以下端点：

```yaml
/metrics:
  get:
    summary: 获取Prometheus格式指标
    operationId: getMetrics
    tags: [Monitoring]
    responses:
      '200':
        description: Prometheus格式指标
        content:
          text/plain:
            schema:
              type: string

/metrics/summary:
  get:
    summary: 获取指标摘要
    operationId: getMetricsSummary
    tags: [Monitoring]
    responses:
      '200':
        description: JSON格式指标摘要
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MetricsSummary'
```

---

## 9. 实施计划

### 9.1 Phase 1: 基础监控 (Week 1)

- [ ] 实现FastAPI性能中间件
- [ ] 添加基础指标（请求量、延迟、错误率）
- [ ] 配置日志系统

### 9.2 Phase 2: 深度监控 (Week 2)

- [ ] Agent执行时间追踪
- [ ] 记忆系统性能监控
- [ ] 资源使用监控

### 9.3 Phase 3: 告警和Dashboard (Week 3)

- [ ] 配置告警规则
- [ ] 实现通知渠道
- [ ] 构建Dashboard

### 9.4 Phase 4: 优化 (Week 4+)

- [ ] 性能瓶颈分析
- [ ] 实施优化策略
- [ ] 持续监控和调优

---

## 10. 成功标准

| 指标 | 目标 | 验收条件 |
|------|------|---------|
| API响应时间 | P95 <500ms | 95%请求在500ms内完成 |
| 错误率 | <1% | 每日错误率低于1% |
| Agent执行 | P95 <5s | 95%Agent调用在5秒内完成 |
| 告警准确率 | >95% | 误报率低于5% |
| Dashboard可用性 | 99.9% | 监控系统稳定运行 |

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
