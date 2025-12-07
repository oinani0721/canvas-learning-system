# Canvas Learning System - 监控系统部署指南

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 2]

---

## 目录

1. [系统要求](#1-系统要求)
2. [环境变量配置](#2-环境变量配置)
3. [Prometheus 配置](#3-prometheus-配置)
4. [日志系统配置](#4-日志系统配置)
5. [健康检查验证](#5-健康检查验证)
6. [回滚流程](#6-回滚流程)

---

## 1. 系统要求

### 1.1 软件依赖

| 软件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.9 | 3.11+ | 运行环境 |
| pip | 21.0 | 24.0+ | 包管理器 |
| Node.js | 16.0 | 20.0+ | 前端构建 (可选) |
| Git | 2.30 | 2.40+ | 版本控制 |

### 1.2 Python 依赖包

> **依赖文件**: `requirements.txt`

**核心监控依赖**:

```text
# ✅ Verified from requirements.txt
prometheus-client>=0.17.1    # Prometheus 指标采集
structlog>=23.1.0            # 结构化日志
psutil>=5.9.0                # 系统资源监控
httpx>=0.24.0                # HTTP 客户端
fastapi>=0.100.0             # Web 框架
uvicorn>=0.23.0              # ASGI 服务器
orjson>=3.9.0                # 高性能 JSON (优化用)
```

### 1.3 硬件需求

| 资源 | 最低配置 | 推荐配置 | 生产配置 |
|------|---------|---------|---------|
| CPU | 2 核 | 4 核 | 8 核 |
| 内存 | 4 GB | 8 GB | 16 GB |
| 磁盘 | 20 GB SSD | 50 GB SSD | 100 GB SSD |
| 网络 | 100 Mbps | 1 Gbps | 10 Gbps |

### 1.4 外部服务依赖

| 服务 | 用途 | 必需性 | 默认端口 |
|------|------|--------|---------|
| Neo4j | Graphiti 知识图谱 | 必需 | 7687 |
| ChromaDB | 语义向量存储 | 必需 | 8000 |
| Prometheus | 指标存储/查询 | 推荐 | 9090 |
| Grafana | 可视化面板 | 推荐 | 3000 |
| AlertManager | 告警管理 | 推荐 | 9093 |

---

## 2. 环境变量配置

### 2.1 核心配置

```bash
# ================================
# Canvas Learning System 环境变量
# ================================

# 应用配置
CANVAS_ENV=production          # 环境: development/staging/production
CANVAS_DEBUG=false             # 调试模式
CANVAS_LOG_LEVEL=INFO          # 日志级别: DEBUG/INFO/WARNING/ERROR

# 服务端口
CANVAS_API_PORT=8000           # API 服务端口
CANVAS_METRICS_PORT=8001       # 独立指标端口 (可选)

# 数据存储路径
CANVAS_DATA_DIR=/var/lib/canvas
CANVAS_LOG_DIR=/var/log/canvas
CANVAS_CACHE_DIR=/var/cache/canvas
```

### 2.2 监控配置

```bash
# ================================
# 监控系统配置
# ================================

# Prometheus 配置
PROMETHEUS_ENABLED=true
PROMETHEUS_METRICS_PATH=/metrics
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# 告警配置
ALERTING_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/xxx
ALERT_EMAIL_TO=ops@example.com

# 性能阈值
ALERT_LATENCY_THRESHOLD_MS=1000     # P95 延迟告警阈值
ALERT_ERROR_RATE_THRESHOLD=0.05     # 错误率告警阈值 (5%)
ALERT_CONCURRENT_TASKS_MAX=100      # 最大并发任务数
```

### 2.3 外部服务配置

```bash
# ================================
# 外部服务连接
# ================================

# Neo4j (Graphiti)
# ✅ Verified from Graphiti Skill (SKILL.md - Configuration)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Prometheus (可选 - 用于查询)
PROMETHEUS_URL=http://localhost:9090

# AlertManager (可选)
ALERTMANAGER_URL=http://localhost:9093
```

### 2.4 日志配置

```bash
# ================================
# 日志系统配置
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:75-114
# ================================

# 日志级别
LOG_LEVEL=INFO
LOG_FORMAT=json                     # json/text
LOG_TIMESTAMP_FORMAT=iso            # iso/unix

# 日志轮转
LOG_MAX_SIZE_MB=10                  # 单文件最大大小
LOG_BACKUP_COUNT=5                  # 保留文件数
LOG_COMPRESSION=gzip                # 压缩格式

# 性能日志
PERFORMANCE_LOG_ENABLED=true
PERFORMANCE_LOG_THRESHOLD_MS=100    # 记录超过此阈值的请求
```

---

## 3. Prometheus 配置

### 3.1 Prometheus 配置示例

> **配置文件**: `/etc/prometheus/prometheus.yml`

```yaml
# ✅ Verified from prometheus_client documentation (Context7)
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  # Canvas Learning System 主服务
  - job_name: 'canvas-api'
    static_configs:
      - targets: ['canvas-app:8000']
    metrics_path: /metrics
    scrape_interval: 10s
    scrape_timeout: 5s

  # Canvas 多实例配置 (如使用负载均衡)
  - job_name: 'canvas-cluster'
    static_configs:
      - targets:
        - 'canvas-app-1:8000'
        - 'canvas-app-2:8000'
        - 'canvas-app-3:8000'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

### 3.2 告警规则配置

> **配置文件**: `/etc/prometheus/rules/canvas-alerts.yml`
> **告警规则来源**: [Source: docs/architecture/performance-monitoring-architecture.md:281-323]

```yaml
groups:
  - name: canvas-api
    rules:
      # 高 API 延迟告警
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(canvas_api_request_latency_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
          description: "P95 latency is {{ $value | humanizeDuration }} (threshold: 1s)"

      # 高错误率告警
      - alert: HighErrorRate
        expr: sum(rate(canvas_api_requests_total{status=~"5.."}[5m])) / sum(rate(canvas_api_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Agent 执行缓慢告警
      - alert: AgentExecutionSlow
        expr: histogram_quantile(0.95, rate(canvas_agent_execution_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Agent execution is slow"
          description: "P95 execution time is {{ $value | humanizeDuration }} (threshold: 10s)"

      # 记忆系统不可用告警
      - alert: MemorySystemDown
        expr: up{job="canvas-memory"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Memory system is down"
          description: "Memory system has been unreachable for more than 1 minute"

      # 高并发任务告警
      - alert: HighConcurrentTasks
        expr: canvas_concurrent_tasks > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of concurrent tasks"
          description: "Current concurrent tasks: {{ $value }} (threshold: 100)"
```

### 3.3 Grafana Dashboard 导入

```bash
# 导入 Canvas 监控 Dashboard
# Dashboard JSON 位置: config/grafana/canvas-dashboard.json

curl -X POST -H "Content-Type: application/json" \
  -d @config/grafana/canvas-dashboard.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

---

## 4. 日志系统配置

### 4.1 structlog 配置

> **ADR引用**: [Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:75-187]

**生产环境日志配置**:

```python
# config/logging.py
# ✅ Verified from ADR-010:75-114

import structlog
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_production_logging(
    log_dir: str = "/var/log/canvas",
    log_level: str = "INFO"
):
    """配置生产环境日志系统"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 时间戳处理器
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # 共享处理器
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 配置 structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # JSON 格式化器 (生产环境)
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    # 主日志处理器
    main_handler = RotatingFileHandler(
        log_path / "canvas-main.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    main_handler.setFormatter(json_formatter)
    main_handler.setLevel(logging.INFO)

    # 错误日志处理器
    error_handler = RotatingFileHandler(
        log_path / "canvas-error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)

    # 性能日志处理器
    perf_handler = RotatingFileHandler(
        log_path / "canvas-performance.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    perf_handler.setFormatter(json_formatter)
    perf_handler.setLevel(logging.INFO)
    perf_handler.addFilter(lambda record: record.name == "performance")

    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    logging.getLogger("performance").addHandler(perf_handler)
```

### 4.2 systemd 日志集成

```ini
# /etc/systemd/system/canvas-learning.service
[Unit]
Description=Canvas Learning System
After=network.target neo4j.service

[Service]
Type=simple
User=canvas
Group=canvas
WorkingDirectory=/opt/canvas-learning
ExecStart=/opt/canvas-learning/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# 日志配置
StandardOutput=append:/var/log/canvas/canvas-stdout.log
StandardError=append:/var/log/canvas/canvas-stderr.log

# 环境变量
EnvironmentFile=/opt/canvas-learning/.env

[Install]
WantedBy=multi-user.target
```

### 4.3 logrotate 配置

```conf
# /etc/logrotate.d/canvas-learning
/var/log/canvas/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 canvas canvas
    sharedscripts
    postrotate
        systemctl reload canvas-learning > /dev/null 2>&1 || true
    endscript
}
```

---

## 5. 健康检查验证

### 5.1 部署后检查脚本

```bash
#!/bin/bash
# scripts/verify-deployment.sh
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:665-691)

set -e

BASE_URL="${CANVAS_API_URL:-http://localhost:8000}"
TIMEOUT=30

echo "=== Canvas Learning System 部署验证 ==="
echo "目标: $BASE_URL"
echo ""

# 1. 健康检查
echo "1. 检查健康状态..."
HEALTH=$(curl -sf --max-time $TIMEOUT "$BASE_URL/health" || echo '{"status":"error"}')
STATUS=$(echo "$HEALTH" | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
    echo "   ✅ 健康检查通过"
else
    echo "   ❌ 健康检查失败: $STATUS"
    exit 1
fi

# 2. 指标端点检查
echo "2. 检查指标端点..."
METRICS=$(curl -sf --max-time $TIMEOUT "$BASE_URL/metrics" | head -1)
if [[ "$METRICS" == *"#"* ]]; then
    echo "   ✅ 指标端点正常"
else
    echo "   ❌ 指标端点异常"
    exit 1
fi

# 3. 指标摘要检查
echo "3. 检查指标摘要..."
SUMMARY=$(curl -sf --max-time $TIMEOUT "$BASE_URL/metrics/summary")
TIMESTAMP=$(echo "$SUMMARY" | jq -r '.timestamp')
if [ -n "$TIMESTAMP" ] && [ "$TIMESTAMP" != "null" ]; then
    echo "   ✅ 指标摘要正常 (timestamp: $TIMESTAMP)"
else
    echo "   ❌ 指标摘要异常"
    exit 1
fi

# 4. 告警端点检查
echo "4. 检查告警端点..."
ALERTS=$(curl -sf --max-time $TIMEOUT "$BASE_URL/metrics/alerts")
TOTAL=$(echo "$ALERTS" | jq -r '.total')
if [ -n "$TOTAL" ]; then
    echo "   ✅ 告警端点正常 (活跃告警: $TOTAL)"
else
    echo "   ❌ 告警端点异常"
    exit 1
fi

# 5. 组件状态检查
echo "5. 检查组件状态..."
COMPONENTS=$(echo "$HEALTH" | jq -r '.components')
for comp in $(echo "$COMPONENTS" | jq -r 'keys[]'); do
    comp_status=$(echo "$COMPONENTS" | jq -r ".[\"$comp\"].status")
    if [ "$comp_status" = "healthy" ]; then
        echo "   ✅ $comp: healthy"
    else
        echo "   ⚠️ $comp: $comp_status"
    fi
done

echo ""
echo "=== 部署验证完成 ==="
```

### 5.2 验证检查项

| 检查项 | 端点 | 预期结果 |
|--------|------|---------|
| 健康状态 | `GET /health` | `{"status": "healthy"}` |
| 指标采集 | `GET /metrics` | Prometheus 格式文本 |
| 指标摘要 | `GET /metrics/summary` | JSON with timestamp |
| 告警列表 | `GET /metrics/alerts` | `{"alerts": [], "total": 0}` |
| API 组件 | `/health` components | api: healthy |
| 记忆组件 | `/health` components | memory: healthy |
| 数据库组件 | `/health` components | database: healthy |

---

## 6. 回滚流程

### 6.1 标准回滚流程

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

PREVIOUS_VERSION="${1:-HEAD~1}"
BACKUP_DIR="/opt/canvas-learning/backups"

echo "=== Canvas Learning System 回滚 ==="
echo "目标版本: $PREVIOUS_VERSION"
echo ""

# Step 1: 确认回滚
read -p "确认要回滚到 $PREVIOUS_VERSION? (y/N) " confirm
if [ "$confirm" != "y" ]; then
    echo "已取消"
    exit 0
fi

# Step 2: 停止服务
echo "停止服务..."
systemctl stop canvas-learning

# Step 3: 备份当前状态
echo "备份当前配置..."
BACKUP_NAME="rollback-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
cp -r config "$BACKUP_DIR/$BACKUP_NAME/"
cp .env "$BACKUP_DIR/$BACKUP_NAME/"

# Step 4: 回滚代码
echo "回滚代码..."
git checkout "$PREVIOUS_VERSION"

# Step 5: 恢复配置 (如有备份)
if [ -d "$BACKUP_DIR/pre-upgrade/config" ]; then
    echo "恢复配置..."
    cp -r "$BACKUP_DIR/pre-upgrade/config" .
fi

# Step 6: 重新安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# Step 7: 重启服务
echo "重启服务..."
systemctl start canvas-learning

# Step 8: 验证
echo "验证服务..."
sleep 5
bash scripts/verify-deployment.sh

echo ""
echo "=== 回滚完成 ==="
```

### 6.2 紧急回滚流程

```bash
# 紧急回滚 - 最快恢复服务

# 1. 立即停止服务
systemctl stop canvas-learning

# 2. 恢复上一个已知稳定版本
git checkout stable-release

# 3. 重启服务
systemctl start canvas-learning

# 4. 验证
curl -sf http://localhost:8000/health
```

### 6.3 数据回滚注意事项

| 数据类型 | 回滚方式 | 注意事项 |
|----------|---------|---------|
| 应用代码 | Git checkout | 标准流程 |
| 配置文件 | 文件恢复 | 注意敏感信息 |
| 日志数据 | 不回滚 | 保留用于排查 |
| 监控数据 | 不回滚 | Prometheus 自动保留 |
| 业务数据 | 数据库备份恢复 | 需单独评估 |

---

## 附录

### A. 部署检查清单

- [ ] Python 版本 >= 3.9
- [ ] 所有依赖包已安装
- [ ] 环境变量已配置
- [ ] Neo4j 服务已启动
- [ ] ChromaDB 服务已启动
- [ ] Prometheus 配置已更新
- [ ] 告警规则已部署
- [ ] 日志目录已创建
- [ ] systemd 服务已配置
- [ ] logrotate 已配置
- [ ] 健康检查通过
- [ ] 指标采集正常
- [ ] 告警通道已测试

### B. 故障排查快速参考

| 问题 | 检查命令 | 可能原因 |
|------|---------|---------|
| 服务启动失败 | `journalctl -u canvas-learning` | 配置错误、依赖缺失 |
| 指标为空 | `curl /metrics` | Middleware 未启用 |
| 告警不触发 | 检查 Prometheus rules | 规则配置错误 |
| 日志无输出 | 检查权限和路径 | 目录不存在、权限不足 |

### C. 相关文档

- [操作手册](../operations/monitoring-operations-guide.md)
- [生产就绪检查清单](./production-readiness-checklist.md)
- [监控架构文档](../architecture/performance-monitoring-architecture.md)
- [ADR-010 日志系统](../architecture/decisions/ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md)

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
