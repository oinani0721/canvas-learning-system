# Canvas Learning System - 监控系统操作手册

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 1]

---

## 目录

1. [系统架构概述](#1-系统架构概述)
2. [日常运维任务](#2-日常运维任务)
3. [常见故障排查](#3-常见故障排查)
4. [维护窗口操作](#4-维护窗口操作)
5. [监控系统升级](#5-监控系统升级)

---

## 1. 系统架构概述

> **架构文档引用**: [Source: docs/architecture/performance-monitoring-architecture.md:87-124]

### 1.1 监控系统组件

```
┌─────────────────────────────────────────────────────────────────┐
│                    Canvas Learning System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ FastAPI App  │───►│ Metrics MW   │───►│ Prometheus   │      │
│  │              │    │ (Story 17.1) │    │ /metrics     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Agent Layer  │───►│ Agent Metrics│───►│ AlertManager │      │
│  │ (14 Agents)  │    │ (Story 17.2) │    │ (Story 17.3) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Memory Layer │───►│Memory Metrics│───►│ Dashboard    │      │
│  │ (3-Layer)    │    │ (Story 17.2) │    │ (Story 17.3) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心指标采集

| 指标类型 | Prometheus 名称 | 描述 | Story |
|----------|-----------------|------|-------|
| API 请求计数 | `canvas_api_requests_total` | 总请求数 (按端点/方法/状态码) | 17.1 |
| API 延迟 | `canvas_api_request_latency_seconds` | 请求延迟直方图 | 17.1 |
| Agent 执行 | `canvas_agent_execution_seconds` | Agent 执行时间 (按类型) | 17.2 |
| 记忆查询 | `canvas_memory_query_seconds` | 记忆系统查询延迟 (按层) | 17.2 |
| 并发任务 | `canvas_concurrent_tasks` | 当前并发任务数 | 17.2 |
| 错误计数 | `canvas_errors_total` | 错误总数 (按类型) | 17.1 |

### 1.3 日志系统配置

> **ADR引用**: [Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:75-187]

**日志目录结构**:
```
.canvas-learning/logs/
├── canvas-main.log       # 主日志 (INFO+)
├── canvas-error.log      # 错误日志 (ERROR+)
├── canvas-performance.log # 性能日志
└── canvas-debug.log      # 调试日志 (DEBUG模式)
```

**日志轮转配置**:
- 单文件最大: 10MB
- 保留文件数: 5
- 轮转策略: RotatingFileHandler

---

## 2. 日常运维任务

### 2.1 每日检查清单

| 时间 | 任务 | 检查项 | 操作 |
|------|------|--------|------|
| 09:00 | 健康检查 | `/health` 返回 healthy | `curl http://localhost:8000/health` |
| 09:00 | 告警检查 | 无 Critical 告警 | 查看 AlertManager 面板 |
| 12:00 | 性能检查 | P95 延迟 < 500ms | 查看 Grafana 概览面板 |
| 18:00 | 错误率检查 | 错误率 < 1% | 查看 `/metrics/summary` |
| 18:00 | 日志检查 | 无异常错误堆栈 | 查看 `canvas-error.log` |

### 2.2 指标检查命令

```bash
# 检查健康状态
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:665-691)
curl -s http://localhost:8000/health | jq .

# 获取指标摘要
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:630-642)
curl -s http://localhost:8000/metrics/summary | jq .

# 获取活跃告警
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:644-662)
curl -s http://localhost:8000/metrics/alerts | jq .

# 获取原始 Prometheus 指标
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:605-628)
curl -s http://localhost:8000/metrics
```

### 2.3 日志轮转管理

```bash
# 检查日志文件大小
ls -lh .canvas-learning/logs/

# 手动触发日志轮转 (如需要)
# structlog 自动处理，无需手动操作

# 清理过期日志 (保留最近5个)
find .canvas-learning/logs/ -name "*.log.*" -mtime +7 -delete
```

### 2.4 存储管理

```bash
# 检查监控数据存储使用
du -sh .canvas-learning/

# 清理缓存数据 (如需要)
# ⚠️ 注意: 会影响缓存命中率
rm -rf .canvas-learning/cache/*

# 检查 Neo4j 存储 (Graphiti)
# ✅ Verified from Graphiti Skill (SKILL.md - Storage Management)
neo4j-admin store-info --store-path /var/lib/neo4j/data
```

---

## 3. 常见故障排查

### 3.1 连接失败排查

**症状**: API 请求超时或连接被拒绝

**排查步骤**:

```bash
# Step 1: 检查服务状态
systemctl status canvas-learning

# Step 2: 检查端口监听
netstat -tlnp | grep 8000

# Step 3: 检查防火墙
iptables -L -n | grep 8000

# Step 4: 检查日志
tail -100 .canvas-learning/logs/canvas-error.log

# Step 5: 测试本地连接
curl -v http://127.0.0.1:8000/health
```

**常见原因与解决**:

| 原因 | 解决方案 |
|------|---------|
| 服务未启动 | `systemctl start canvas-learning` |
| 端口被占用 | `kill -9 $(lsof -t -i:8000)` |
| 防火墙阻挡 | `iptables -A INPUT -p tcp --dport 8000 -j ACCEPT` |
| 配置错误 | 检查 `.env` 文件配置 |

### 3.2 指标丢失排查

**症状**: Prometheus 无法拉取指标或指标值为空

**排查步骤**:

```bash
# Step 1: 检查 /metrics 端点
curl -s http://localhost:8000/metrics | head -20

# Step 2: 检查 Prometheus 配置
cat /etc/prometheus/prometheus.yml | grep canvas

# Step 3: 检查 Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="canvas")'

# Step 4: 检查网络连通性
curl -v http://canvas-app:8000/metrics

# Step 5: 检查指标注册
grep -r "REGISTRY" backend/app/middleware/metrics.py
```

**常见原因与解决**:

| 原因 | 解决方案 |
|------|---------|
| Middleware 未启用 | 检查 `main.py` 中 `add_middleware` 调用 |
| 指标未注册 | 检查 `prometheus_client` 初始化 |
| Prometheus 配置错误 | 更新 `scrape_configs` |
| 网络隔离 | 配置容器网络或代理 |

### 3.3 告警误报排查

**症状**: 收到告警但系统实际正常

**排查步骤**:

```bash
# Step 1: 检查告警详情
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="HighAPILatency")'

# Step 2: 检查原始指标值
curl -s http://localhost:8000/metrics | grep canvas_api_request_latency

# Step 3: 检查历史数据 (Prometheus)
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(canvas_api_request_latency_seconds_bucket[5m]))'

# Step 4: 检查告警规则配置
cat config/alerts.yaml

# Step 5: 验证阈值设置
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:281-323)
# P95 > 1s for 5min = HighAPILatency
```

**常见原因与解决**:

| 原因 | 解决方案 |
|------|---------|
| 阈值过低 | 调整 `config/alerts.yaml` 阈值 |
| 窗口太短 | 增加 `for` 持续时间 |
| 数据波动 | 使用 `rate()` 或 `avg_over_time()` 平滑 |
| 测试流量干扰 | 添加标签过滤排除测试请求 |

### 3.4 内存/CPU 高占用排查

**症状**: 系统响应变慢，资源使用率高

**排查步骤**:

```bash
# Step 1: 检查系统资源
top -p $(pgrep -f "uvicorn")

# Step 2: 检查 Python 内存
python -c "import psutil; print(psutil.Process().memory_info())"

# Step 3: 检查并发任务数
curl -s http://localhost:8000/metrics | grep canvas_concurrent_tasks

# Step 4: 检查缓存命中率
curl -s http://localhost:8000/metrics/summary | jq '.cache'

# Step 5: 检查慢查询
grep "duration_ms" .canvas-learning/logs/canvas-performance.log | awk '$NF > 1000'
```

**常见原因与解决**:

| 原因 | 解决方案 |
|------|---------|
| 内存泄漏 | 重启服务，检查代码 |
| 并发过高 | 配置限流 (`config/optimization.yaml`) |
| 缓存失效 | 检查缓存配置，预热缓存 |
| Agent 阻塞 | 检查 Agent 超时配置 |

---

## 4. 维护窗口操作

### 4.1 计划维护流程

**维护前准备** (T-24h):
1. 发送维护通知给所有用户
2. 确认维护窗口时间 (建议: 周日凌晨 2:00-6:00)
3. 准备回滚方案

**维护执行** (T-0):

```bash
# Step 1: 静默告警 (避免维护期间误报)
curl -X POST http://alertmanager:9093/api/v2/silences \
  -d '{"matchers":[{"name":"job","value":"canvas"}],"startsAt":"2025-01-01T02:00:00Z","endsAt":"2025-01-01T06:00:00Z","createdBy":"ops","comment":"Planned maintenance"}'

# Step 2: 优雅停止服务
systemctl stop canvas-learning
# 或使用信号
kill -SIGTERM $(pgrep -f "uvicorn")

# Step 3: 执行维护操作
# (数据库迁移、配置更新等)

# Step 4: 重启服务
systemctl start canvas-learning

# Step 5: 验证服务状态
curl -s http://localhost:8000/health | jq .

# Step 6: 解除告警静默
curl -X DELETE http://alertmanager:9093/api/v2/silence/{silence_id}
```

### 4.2 紧急维护流程

**紧急维护标准**:
- 安全漏洞修复
- 数据损坏修复
- 服务完全不可用

**执行步骤**:

```bash
# Step 1: 评估影响范围
curl -s http://localhost:8000/metrics/alerts | jq '.alerts | length'

# Step 2: 通知相关人员
# (通过 PagerDuty/钉钉/企业微信)

# Step 3: 快速修复或回滚
# 选项A: 热修复
git cherry-pick {commit_hash}
systemctl reload canvas-learning

# 选项B: 回滚
git checkout {previous_version}
systemctl restart canvas-learning

# Step 4: 验证修复
curl -s http://localhost:8000/health | jq .

# Step 5: 记录事件
# 创建 Post-Mortem 文档
```

---

## 5. 监控系统升级

### 5.1 升级前检查

```bash
# Step 1: 备份当前配置
cp -r config/ config.bak.$(date +%Y%m%d)

# Step 2: 备份监控数据
# Prometheus 数据 (如使用外部存储)
prometheus-backup --output /backup/prometheus-$(date +%Y%m%d).tar.gz

# Step 3: 检查兼容性
# 阅读 CHANGELOG-MONITORING.md 中的 Breaking Changes

# Step 4: 在测试环境验证
pytest tests/integration/test_monitoring_e2e.py -v

# Step 5: 准备回滚脚本
cat > rollback.sh << 'EOF'
#!/bin/bash
git checkout {previous_version}
cp -r config.bak.* config/
systemctl restart canvas-learning
EOF
chmod +x rollback.sh
```

### 5.2 升级执行

```bash
# Step 1: 拉取新版本
git pull origin main

# Step 2: 更新依赖
pip install -r requirements.txt --upgrade

# Step 3: 运行数据迁移 (如有)
python scripts/migrate_monitoring.py

# Step 4: 重启服务
systemctl restart canvas-learning

# Step 5: 验证升级
curl -s http://localhost:8000/health | jq .
pytest tests/integration/test_monitoring_e2e.py -v

# Step 6: 更新文档
# 记录升级版本和变更
```

### 5.3 升级后验证

| 检查项 | 预期结果 | 验证命令 |
|--------|---------|---------|
| 健康检查 | status: healthy | `curl /health` |
| 指标采集 | 有新数据 | `curl /metrics` |
| 告警系统 | 无误报 | `curl /metrics/alerts` |
| Dashboard | 正常显示 | 打开 Grafana |
| 日志系统 | 正常写入 | `tail -f logs/canvas-main.log` |

---

## 附录

### A. 常用命令速查

```bash
# 服务管理
systemctl start/stop/restart canvas-learning
systemctl status canvas-learning

# 健康检查
curl http://localhost:8000/health

# 指标查询
curl http://localhost:8000/metrics
curl http://localhost:8000/metrics/summary

# 告警查询
curl http://localhost:8000/metrics/alerts

# 日志查看
tail -f .canvas-learning/logs/canvas-main.log
tail -f .canvas-learning/logs/canvas-error.log

# 性能分析
curl http://localhost:8000/metrics | grep quantile
```

### B. 联系人列表

| 角色 | 职责 | 联系方式 |
|------|------|---------|
| 运维负责人 | 日常运维、告警响应 | ops@example.com |
| 开发负责人 | 故障排查、代码修复 | dev@example.com |
| 架构师 | 架构决策、性能优化 | arch@example.com |

### C. 相关文档

- [部署指南](../deployment/monitoring-deployment-guide.md)
- [告警响应手册](./alert-runbook.md)
- [Dashboard使用指南](./dashboard-user-guide.md)
- [故障演练计划](./chaos-engineering-plan.md)
- [监控架构文档](../architecture/performance-monitoring-architecture.md)

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
