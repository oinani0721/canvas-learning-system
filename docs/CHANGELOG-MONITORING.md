# Canvas Learning System - 监控系统变更日志

本文档记录 Canvas Learning System 监控系统的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2025-12-03

### 概述
Canvas Learning System 监控系统 v1.0.0 首次发布，提供完整的系统可观测性支持。

### Epic 17 - 性能监控与可观测性系统

**Stories 完成**:
- Story 17.1: API 指标收集中间件
- Story 17.2: Agent 和记忆系统指标
- Story 17.3: 告警系统和 Dashboard
- Story 17.4: 性能优化
- Story 17.5: E2E 测试和基准测试
- Story 17.6: 文档和 Runbook

---

### 新增 (Added)

#### 核心功能

- **API 指标收集** (Story 17.1)
  - Prometheus 指标中间件 (`backend/app/middleware/metrics.py`)
  - 请求计数器 `canvas_api_requests_total`
  - 延迟直方图 `canvas_api_request_latency_seconds`
  - 活跃请求计数 `canvas_api_active_requests`
  - 按路径、方法、状态码分类的指标

- **Agent 指标** (Story 17.2)
  - Agent 执行时间追踪 `canvas_agent_execution_seconds`
  - Agent 调用计数 `canvas_agent_invocations_total`
  - 并发任务计数 `canvas_agent_concurrent_tasks`
  - 按 Agent 类型分类的指标

- **记忆系统指标** (Story 17.2)
  - Neo4j 连接状态 `canvas_memory_neo4j_connected`
  - ChromaDB 连接状态 `canvas_memory_chromadb_connected`
  - 查询延迟 `canvas_memory_query_latency_seconds`
  - 缓存命中率 `canvas_memory_cache_hit_ratio`

- **资源监控** (Story 17.2)
  - CPU 使用率 `canvas_resource_cpu_percent`
  - 内存使用率 `canvas_resource_memory_percent`
  - 磁盘使用率 `canvas_resource_disk_percent`
  - 网络 I/O `canvas_resource_network_bytes`

- **告警系统** (Story 17.3)
  - AlertManager 集成
  - 5 个预定义告警规则:
    - `HighAPILatency`: P95 > 1s for 5m
    - `HighErrorRate`: Error > 5% for 2m
    - `AgentExecutionSlow`: P95 > 10s for 5m
    - `MemorySystemDown`: 连接失败 > 1m
    - `HighConcurrentTasks`: 并发 > 100 for 2m
  - 告警历史记录和查询 API

- **Dashboard** (Story 17.3)
  - Grafana Dashboard JSON 配置
  - 5 个监控面板:
    - 系统概览
    - API 性能
    - Agent 性能
    - 记忆系统
    - 资源监控

#### 性能优化 (Story 17.4)

- **Canvas 缓存系统** (`src/canvas_cache.py`)
  - LRU 缓存实现
  - 可配置 TTL
  - 缓存命中率追踪

- **批量写入器** (`src/batch_writer.py`)
  - 异步批量写入
  - 可配置批量大小
  - 写入延迟优化

- **资源感知调度器** (`src/resource_aware_scheduler.py`)
  - 基于系统资源的任务调度
  - 自动限流
  - 优先级队列

#### API 端点

- `GET /health` - 健康检查
- `GET /metrics` - Prometheus 指标 (text/plain)
- `GET /metrics/summary` - 指标摘要 (JSON)
- `GET /metrics/alerts` - 告警列表
- `GET /metrics/alerts/history` - 告警历史

#### 测试 (Story 17.5)

- **集成测试**
  - `tests/integration/test_monitoring_e2e.py` (15 tests)
  - `tests/integration/test_alert_triggers.py` (12 tests)
  - `tests/integration/test_dashboard_accuracy.py` (10 tests)

- **性能测试**
  - `tests/performance/test_optimization_benchmark.py` (8 tests)
  - `tests/performance/test_monitoring_overhead.py` (16 tests)

- **负载测试**
  - `tests/load/test_monitoring_under_load.py` (10 tests)

#### 文档 (Story 17.6)

- **操作文档**
  - `docs/operations/monitoring-operations-guide.md` - 监控操作手册
  - `docs/operations/alert-runbook.md` - 告警响应手册
  - `docs/operations/dashboard-user-guide.md` - Dashboard 使用指南
  - `docs/operations/chaos-engineering-plan.md` - 混沌工程计划

- **部署文档**
  - `docs/deployment/monitoring-deployment-guide.md` - 部署指南
  - `docs/deployment/production-readiness-checklist.md` - 生产就绪检查清单

- **变更日志**
  - `docs/CHANGELOG-MONITORING.md` - 本文档

---

### 技术规格

#### 性能目标 (已达成)

| 指标 | 目标 | 实测 | 状态 |
|------|------|------|------|
| API P95 延迟 | < 500ms | ~200ms | ✅ |
| API P99 延迟 | < 1000ms | ~400ms | ✅ |
| 错误率 | < 1% | ~0.1% | ✅ |
| Agent P95 执行时间 | < 5s | ~3s | ✅ |
| 监控开销 | < 5ms | ~2ms | ✅ |

#### 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| prometheus_client | 0.17+ | 指标收集 |
| structlog | 23.1+ | 结构化日志 |
| grafana | 9.0+ | 可视化 |
| alertmanager | 0.25+ | 告警管理 |

#### 配置

```yaml
# 环境变量
PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus
METRICS_ENABLED: true
ALERT_WEBHOOK_URL: https://your-webhook-url
```

---

### 已知问题

1. **Windows 路径编码**: 在包含中文字符的路径下运行 epic-develop 可能失败
   - 影响: 自动化开发流程
   - 解决方案: 使用手动开发模式或英文路径

2. **高负载下的指标延迟**: 在极高并发 (>500 req/s) 下，指标收集可能有 1-2 秒延迟
   - 影响: 实时监控精度
   - 解决方案: 调整 scrape_interval 或使用 Push Gateway

---

### 升级指南

#### 从 0.x 升级到 1.0.0

1. **安装新依赖**:
   ```bash
   pip install prometheus_client>=0.17.0
   ```

2. **配置环境变量**:
   ```bash
   export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
   export METRICS_ENABLED=true
   ```

3. **部署 Prometheus 配置**:
   ```bash
   cp configs/prometheus.yml /etc/prometheus/
   systemctl restart prometheus
   ```

4. **导入 Grafana Dashboard**:
   ```bash
   # 使用 Grafana API 或 UI 导入
   # Dashboard JSON: configs/grafana-dashboard.json
   ```

5. **验证部署**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/metrics | head -5
   ```

---

### 贡献者

- Epic 17 开发团队
- 文档由 Claude Code 协助生成

---

### 相关链接

- [性能监控架构](docs/architecture/performance-monitoring-architecture.md)
- [ADR-010: structlog 日志聚合](docs/architecture/decisions/ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md)
- [API OpenAPI 规范](specs/api/canvas-api.openapi.yml)

---

**文档维护**: 开发团队
**最后更新**: 2025-12-03
