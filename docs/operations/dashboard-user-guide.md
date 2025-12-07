# Canvas Learning System - Dashboard 使用指南

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 4]
**Dashboard 设计来源**: [Source: docs/architecture/performance-monitoring-architecture.md:401-440]

---

## 目录

1. [Dashboard 概述](#1-dashboard-概述)
2. [概览面板](#2-概览面板)
3. [API 性能面板](#3-api-性能面板)
4. [Agent 性能面板](#4-agent-性能面板)
5. [记忆系统面板](#5-记忆系统面板)
6. [资源监控面板](#6-资源监控面板)
7. [自定义查询](#7-自定义查询)

---

## 1. Dashboard 概述

### 1.1 访问方式

- **Grafana 地址**: http://localhost:3000
- **默认账户**: admin / admin (首次登录需修改)
- **Dashboard 路径**: Dashboards > Canvas Learning System

### 1.2 面板布局

```
┌─────────────────────────────────────────────────────────────────┐
│                      Canvas Learning System                      │
├───────────────────────┬─────────────────────────────────────────┤
│    概览面板 (Row 1)    │     告警状态 (Row 1)                     │
│   - 请求量            │     - 活跃告警列表                        │
│   - 错误率            │     - 告警趋势                           │
│   - P95 延迟          │                                         │
├───────────────────────┴─────────────────────────────────────────┤
│                    API 性能面板 (Row 2)                          │
│   - 各端点响应时间分布                                           │
│   - 请求量趋势                                                   │
│   - 错误分布                                                     │
├─────────────────────────────────────────────────────────────────┤
│                   Agent 性能面板 (Row 3)                         │
│   - 各 Agent 执行时间对比                                        │
│   - Agent 调用量趋势                                             │
│   - 执行成功率                                                   │
├─────────────────────────────────────────────────────────────────┤
│                   记忆系统面板 (Row 4)                           │
│   - 各层查询延迟                                                 │
│   - 缓存命中率                                                   │
│   - 连接状态                                                     │
├─────────────────────────────────────────────────────────────────┤
│                   资源监控面板 (Row 5)                           │
│   - CPU 使用率                                                   │
│   - 内存使用率                                                   │
│   - 磁盘 IO                                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 时间范围选择

| 快捷选项 | 说明 | 使用场景 |
|----------|------|---------|
| Last 5 minutes | 实时监控 | 排查进行中的问题 |
| Last 1 hour | 近期趋势 | 日常检查 |
| Last 6 hours | 中期趋势 | 值班交接 |
| Last 24 hours | 全天视图 | 每日复盘 |
| Last 7 days | 周趋势 | 周报分析 |

---

## 2. 概览面板

### 2.1 请求量 (Requests/sec)

**面板类型**: Stat / Graph

**指标说明**:
- **当前值**: 最近 1 分钟的平均 RPS
- **趋势图**: 展示请求量随时间变化

**PromQL 查询**:
```promql
# 每秒请求数
rate(canvas_api_requests_total[1m])

# 按端点分组
sum by (endpoint) (rate(canvas_api_requests_total[1m]))
```

**健康标准**:
| 状态 | 条件 | 颜色 |
|------|------|------|
| 正常 | RPS 在基线 ±50% | 绿色 |
| 警告 | RPS 偏离基线 50-100% | 黄色 |
| 异常 | RPS 偏离基线 >100% | 红色 |

**如何解读**:
- **突然升高**: 可能是流量高峰或攻击
- **突然降低**: 可能是上游问题或服务异常
- **持续波动**: 检查负载均衡是否正常

### 2.2 错误率 (Error Rate)

**面板类型**: Gauge / Graph

**指标说明**:
- **当前值**: 5xx 错误占总请求的百分比
- **趋势图**: 错误率随时间变化

**PromQL 查询**:
```promql
# 错误率百分比
sum(rate(canvas_api_requests_total{status=~"5.."}[5m]))
/
sum(rate(canvas_api_requests_total[5m]))
* 100
```

**健康标准**:
| 状态 | 条件 | 颜色 |
|------|------|------|
| 正常 | < 1% | 绿色 |
| 警告 | 1% - 5% | 黄色 |
| 严重 | > 5% | 红色 |

**如何解读**:
- **持续 > 1%**: 检查最近部署或依赖服务
- **突然飙升**: 立即查看错误日志
- **缓慢上升**: 可能是资源泄漏

### 2.3 P95 延迟 (Latency)

**面板类型**: Stat / Heatmap

**指标说明**:
- **P95**: 95% 请求在此时间内完成
- **P99**: 99% 请求在此时间内完成
- **Avg**: 平均响应时间

**PromQL 查询**:
```promql
# P95 延迟 (秒)
histogram_quantile(0.95, rate(canvas_api_request_latency_seconds_bucket[5m]))

# P99 延迟
histogram_quantile(0.99, rate(canvas_api_request_latency_seconds_bucket[5m]))

# 平均延迟
rate(canvas_api_request_latency_seconds_sum[5m])
/
rate(canvas_api_request_latency_seconds_count[5m])
```

**健康标准**:
| 指标 | 正常 | 警告 | 严重 |
|------|------|------|------|
| P95 | < 500ms | 500ms - 1s | > 1s |
| P99 | < 1s | 1s - 2s | > 2s |
| Avg | < 200ms | 200ms - 500ms | > 500ms |

**如何解读**:
- **P95 高但 Avg 正常**: 存在少量慢请求
- **Avg 高**: 整体性能下降
- **P99 远高于 P95**: 存在极端异常值

---

## 3. API 性能面板

### 3.1 端点响应时间分布

**面板类型**: Heatmap / Table

**展示内容**:
- 各 API 端点的响应时间分布
- 按延迟区间分组的请求计数

**PromQL 查询**:
```promql
# 各端点 P95 延迟
histogram_quantile(0.95,
  sum by (endpoint, le) (
    rate(canvas_api_request_latency_seconds_bucket[5m])
  )
)

# 按端点分组的请求量
sum by (endpoint) (rate(canvas_api_requests_total[5m]))
```

**如何解读**:
- **红色区域**: 高延迟请求集中区
- **端点对比**: 识别最慢端点
- **时间趋势**: 观察延迟变化

### 3.2 请求量趋势

**面板类型**: Graph (Stacked)

**展示内容**:
- 各端点请求量堆叠图
- 按状态码分布

**PromQL 查询**:
```promql
# 按端点和状态码分组
sum by (endpoint, status) (rate(canvas_api_requests_total[5m]))
```

**常见端点**:
| 端点 | 说明 | 预期 RPS |
|------|------|---------|
| `/health` | 健康检查 | 0.1-1 |
| `/metrics` | Prometheus 抓取 | 0.1 |
| `/api/v1/canvas/*` | Canvas 操作 | 1-10 |
| `/api/v1/agents/*` | Agent 调用 | 0.5-5 |

### 3.3 错误分布

**面板类型**: Pie Chart / Table

**展示内容**:
- 按错误类型分布
- 按端点分布

**PromQL 查询**:
```promql
# 按状态码分组的错误
sum by (status) (increase(canvas_api_requests_total{status=~"[45].."}[1h]))

# 按端点分组的错误
sum by (endpoint) (increase(canvas_api_requests_total{status=~"5.."}[1h]))
```

---

## 4. Agent 性能面板

### 4.1 Agent 执行时间对比

**面板类型**: Bar Chart / Heatmap

**指标来源**: `canvas_agent_execution_seconds`

**PromQL 查询**:
```promql
# 各 Agent 类型 P95 执行时间
histogram_quantile(0.95,
  sum by (agent_type, le) (
    rate(canvas_agent_execution_seconds_bucket[5m])
  )
)

# 各 Agent 平均执行时间
sum by (agent_type) (rate(canvas_agent_execution_seconds_sum[5m]))
/
sum by (agent_type) (rate(canvas_agent_execution_seconds_count[5m]))
```

**Agent 类型参考**:
| Agent | 说明 | 预期 P95 |
|-------|------|---------|
| basic-decomposition | 基础拆解 | < 5s |
| scoring-agent | 评分 | < 3s |
| oral-explanation | 口语化解释 | < 8s |
| example-teaching | 例题教学 | < 10s |
| comparison-table | 对比表格 | < 5s |

### 4.2 Agent 调用量趋势

**面板类型**: Graph (Stacked)

**展示内容**:
- 各 Agent 类型调用量
- 调用趋势变化

**PromQL 查询**:
```promql
# 各 Agent 调用次数
sum by (agent_type) (increase(canvas_agent_execution_seconds_count[1h]))
```

### 4.3 执行成功率

**面板类型**: Gauge / Table

**展示内容**:
- 各 Agent 成功率
- 失败原因分布

**PromQL 查询**:
```promql
# 成功率
sum(rate(canvas_agent_execution_seconds_count{status="success"}[5m]))
/
sum(rate(canvas_agent_execution_seconds_count[5m]))
* 100
```

---

## 5. 记忆系统面板

### 5.1 各层查询延迟

**面板类型**: Graph / Stat

**三层记忆系统**:
- **Graphiti**: 知识图谱 (Neo4j)
- **Temporal**: 时序记忆 (LangGraph)
- **Semantic**: 语义搜索 (ChromaDB)

**PromQL 查询**:
```promql
# 各层 P95 延迟
histogram_quantile(0.95,
  sum by (layer, le) (
    rate(canvas_memory_query_seconds_bucket[5m])
  )
)

# 各层平均延迟
sum by (layer) (rate(canvas_memory_query_seconds_sum[5m]))
/
sum by (layer) (rate(canvas_memory_query_seconds_count[5m]))
```

**健康标准**:
| 层 | P95 正常 | P95 警告 |
|----|---------|---------|
| Graphiti | < 500ms | > 1s |
| Temporal | < 200ms | > 500ms |
| Semantic | < 300ms | > 800ms |

### 5.2 缓存命中率

**面板类型**: Gauge / Graph

**PromQL 查询**:
```promql
# 缓存命中率
sum(rate(canvas_cache_hits_total[5m]))
/
(sum(rate(canvas_cache_hits_total[5m])) + sum(rate(canvas_cache_misses_total[5m])))
* 100
```

**健康标准**:
| 状态 | 命中率 |
|------|--------|
| 优秀 | > 90% |
| 正常 | 70% - 90% |
| 需优化 | < 70% |

### 5.3 连接状态

**面板类型**: Status Panel

**展示内容**:
- Neo4j 连接状态
- ChromaDB 连接状态
- 连接池使用率

**PromQL 查询**:
```promql
# 连接状态 (1=正常, 0=异常)
up{job=~"canvas-.*"}

# 活跃连接数
canvas_db_connections_active
```

---

## 6. 资源监控面板

### 6.1 CPU 使用率

**面板类型**: Graph / Gauge

**PromQL 查询**:
```promql
# 进程 CPU 使用率
rate(process_cpu_seconds_total[1m]) * 100

# 系统 CPU 使用率 (需要 node_exporter)
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**健康标准**:
| 状态 | CPU 使用率 |
|------|-----------|
| 正常 | < 70% |
| 警告 | 70% - 90% |
| 严重 | > 90% |

### 6.2 内存使用率

**面板类型**: Graph / Gauge

**PromQL 查询**:
```promql
# 进程内存使用 (字节)
process_resident_memory_bytes

# 内存使用率 (需要 node_exporter)
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

**健康标准**:
| 状态 | 内存使用率 |
|------|-----------|
| 正常 | < 80% |
| 警告 | 80% - 95% |
| 严重 | > 95% |

### 6.3 磁盘 IO

**面板类型**: Graph

**PromQL 查询**:
```promql
# 磁盘读写速率 (需要 node_exporter)
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])

# IO 利用率
rate(node_disk_io_time_seconds_total[5m]) * 100
```

---

## 7. 自定义查询

### 7.1 PromQL 基础语法

```promql
# 即时查询 - 当前值
canvas_api_requests_total

# 范围查询 - 过去 5 分钟
canvas_api_requests_total[5m]

# 聚合 - 求和
sum(canvas_api_requests_total)

# 聚合 - 按标签分组
sum by (endpoint) (canvas_api_requests_total)

# 速率计算
rate(canvas_api_requests_total[5m])

# 百分位数
histogram_quantile(0.95, rate(canvas_api_request_latency_seconds_bucket[5m]))
```

### 7.2 常用查询示例

**请求分析**:
```promql
# 最慢的 5 个端点 (P95)
topk(5,
  histogram_quantile(0.95,
    sum by (endpoint, le) (
      rate(canvas_api_request_latency_seconds_bucket[5m])
    )
  )
)

# 错误最多的端点
topk(5, sum by (endpoint) (increase(canvas_api_requests_total{status=~"5.."}[1h])))
```

**Agent 分析**:
```promql
# 最慢的 Agent 类型
topk(5,
  histogram_quantile(0.95,
    sum by (agent_type, le) (
      rate(canvas_agent_execution_seconds_bucket[5m])
    )
  )
)

# Agent 调用占比
sum by (agent_type) (increase(canvas_agent_execution_seconds_count[1h]))
```

**趋势分析**:
```promql
# 与昨天同期对比
sum(rate(canvas_api_requests_total[5m]))
-
sum(rate(canvas_api_requests_total[5m] offset 1d))

# 与上周同期对比
sum(rate(canvas_api_requests_total[5m]))
/
sum(rate(canvas_api_requests_total[5m] offset 7d))
```

### 7.3 在 Grafana 中添加查询

1. 点击面板右上角的 **Edit**
2. 在 **Query** 标签页中输入 PromQL
3. 选择合适的 **Visualization**
4. 配置 **Panel options** (标题、描述等)
5. 点击 **Apply** 保存

### 7.4 创建告警规则

1. 进入 **Alerting > Alert rules**
2. 点击 **Create alert rule**
3. 配置:
   - **Name**: 告警名称
   - **Query**: PromQL 表达式
   - **Condition**: 触发条件
   - **Folder**: 告警分组
   - **Labels**: 告警标签 (severity 等)
4. 配置通知渠道
5. 保存规则

---

## 附录

### A. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `d` | Dashboard 设置 |
| `s` | 保存 Dashboard |
| `r` | 刷新 |
| `t` | 时间范围选择 |
| `Ctrl+Z` | 撤销更改 |
| `Esc` | 退出编辑模式 |

### B. 常见问题

| 问题 | 解决方案 |
|------|---------|
| 数据不显示 | 检查 Prometheus 数据源配置 |
| 图表为空 | 检查时间范围是否有数据 |
| 延迟显示 NaN | 检查 bucket 配置是否正确 |
| 告警不触发 | 检查告警规则和通知渠道 |

### C. 相关文档

- [操作手册](./monitoring-operations-guide.md)
- [告警响应手册](./alert-runbook.md)
- [监控架构文档](../architecture/performance-monitoring-architecture.md)
- [Grafana 官方文档](https://grafana.com/docs/)
- [PromQL 参考](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
