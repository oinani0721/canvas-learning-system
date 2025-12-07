# Canvas Learning System - 生产就绪检查清单

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 5]
**性能目标来源**: [Source: docs/architecture/performance-monitoring-architecture.md:516-524]

---

## 使用说明

本检查清单用于验证 Canvas Learning System 监控系统是否满足生产环境上线条件。

**检查执行人**: _______________
**检查日期**: _______________
**环境**: ☐ Staging ☐ Production

**评审状态**: ☐ 通过 ☐ 有条件通过 ☐ 未通过

---

## 1. 功能完整性验证 ☐

### 1.1 监控端点可访问性

> **验证来源**: [Source: specs/api/canvas-api.openapi.yml:605-691]

| 检查项 | 端点 | 预期响应 | 实际结果 | 状态 |
|--------|------|---------|---------|------|
| 健康检查 | `GET /health` | `{"status": "healthy"}` | | ☐ |
| Prometheus 指标 | `GET /metrics` | text/plain (Prometheus 格式) | | ☐ |
| 指标摘要 | `GET /metrics/summary` | JSON with timestamp | | ☐ |
| 告警列表 | `GET /metrics/alerts` | `{"alerts": [...], "total": N}` | | ☐ |

**验证命令**:
```bash
# 健康检查
curl -sf http://localhost:8000/health | jq '.status'
# 预期: "healthy"

# 指标端点
curl -sf http://localhost:8000/metrics | head -5
# 预期: # HELP canvas_api_requests_total ...

# 指标摘要
curl -sf http://localhost:8000/metrics/summary | jq '.timestamp'
# 预期: ISO 8601 时间戳

# 告警端点
curl -sf http://localhost:8000/metrics/alerts | jq '.total'
# 预期: 数字
```

### 1.2 组件健康状态

| 组件 | 检查方式 | 预期状态 | 实际状态 | 状态 |
|------|---------|---------|---------|------|
| API 服务 | `/health` components.api | healthy | | ☐ |
| 数据库连接 | `/health` components.database | healthy | | ☐ |
| 记忆系统 | `/health` components.memory | healthy | | ☐ |
| 缓存系统 | `/health` components.cache | healthy | | ☐ |

**验证命令**:
```bash
curl -sf http://localhost:8000/health | jq '.components'
```

---

## 2. 性能达标验证 ☐

> **性能目标来源**: [Source: docs/architecture/performance-monitoring-architecture.md:516-524]

### 2.1 API 性能指标

| 指标 | 目标 | 实测值 | 状态 |
|------|------|--------|------|
| P95 响应延迟 | < 500ms | _______ ms | ☐ |
| P99 响应延迟 | < 1000ms | _______ ms | ☐ |
| 平均响应时间 | < 200ms | _______ ms | ☐ |
| 错误率 | < 1% | _______ % | ☐ |

**验证命令**:
```bash
# 从指标摘要获取
curl -sf http://localhost:8000/metrics/summary | jq '.api'

# 或从 Prometheus 查询
curl -sf 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(canvas_api_request_latency_seconds_bucket[5m]))'
```

### 2.2 Agent 性能指标

| 指标 | 目标 | 实测值 | 状态 |
|------|------|--------|------|
| Agent P95 执行时间 | < 5s | _______ s | ☐ |
| Agent 成功率 | > 99% | _______ % | ☐ |
| 最大并发任务 | < 100 | _______ | ☐ |

### 2.3 监控系统开销

| 指标 | 目标 | 实测值 | 状态 |
|------|------|--------|------|
| 监控中间件延迟增加 | < 5ms | _______ ms | ☐ |
| CPU 开销增加 | < 5% | _______ % | ☐ |
| 内存开销增加 | < 100MB | _______ MB | ☐ |

**验证方式**: 参考 Story 17.5 测试报告 `tests/performance/test_monitoring_overhead.py`

---

## 3. 告警配置验证 ☐

> **告警规则来源**: [Source: docs/architecture/performance-monitoring-architecture.md:281-323]

### 3.1 告警规则配置

| 告警名称 | 触发条件 | 配置状态 | 测试状态 |
|----------|---------|---------|---------|
| HighAPILatency | P95 > 1s for 5m | ☐ 已配置 | ☐ 已测试 |
| HighErrorRate | Error > 5% for 2m | ☐ 已配置 | ☐ 已测试 |
| AgentExecutionSlow | P95 > 10s for 5m | ☐ 已配置 | ☐ 已测试 |
| MemorySystemDown | Connection fail for 1m | ☐ 已配置 | ☐ 已测试 |
| HighConcurrentTasks | Tasks > 100 for 2m | ☐ 已配置 | ☐ 已测试 |

**验证命令**:
```bash
# 检查 Prometheus 告警规则
curl -sf http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name | startswith("High"))'
```

### 3.2 告警通知渠道

| 渠道 | 配置状态 | 测试状态 | 责任人 |
|------|---------|---------|--------|
| 邮件通知 | ☐ 已配置 | ☐ 已测试 | _______ |
| 即时通讯 (钉钉/企业微信/Slack) | ☐ 已配置 | ☐ 已测试 | _______ |
| 电话告警 (Critical) | ☐ 已配置 | ☐ 已测试 | _______ |
| Webhook | ☐ 已配置 | ☐ 已测试 | _______ |

---

## 4. 日志系统验证 ☐

> **日志配置来源**: [Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:75-187]

### 4.1 日志配置

| 检查项 | 预期值 | 实际值 | 状态 |
|--------|--------|--------|------|
| 日志格式 | JSON | _______ | ☐ |
| 日志级别 | INFO (生产) | _______ | ☐ |
| 时间戳格式 | ISO 8601 | _______ | ☐ |

### 4.2 日志轮转

| 检查项 | 预期值 | 实际值 | 状态 |
|--------|--------|--------|------|
| 单文件最大大小 | 10MB | _______ | ☐ |
| 保留文件数 | 5 | _______ | ☐ |
| 压缩启用 | Yes | _______ | ☐ |

**验证命令**:
```bash
# 检查日志文件
ls -lh /var/log/canvas/

# 检查日志格式
tail -1 /var/log/canvas/canvas-main.log | jq .

# 检查 logrotate 配置
cat /etc/logrotate.d/canvas-learning
```

### 4.3 日志分类

| 日志类型 | 文件路径 | 存在 | 写入正常 |
|----------|---------|------|---------|
| 主日志 | `/var/log/canvas/canvas-main.log` | ☐ | ☐ |
| 错误日志 | `/var/log/canvas/canvas-error.log` | ☐ | ☐ |
| 性能日志 | `/var/log/canvas/canvas-performance.log` | ☐ | ☐ |
| 调试日志 | `/var/log/canvas/canvas-debug.log` | ☐ N/A (生产禁用) | ☐ |

---

## 5. 安全配置验证 ☐

### 5.1 访问控制

| 检查项 | 要求 | 状态 | 备注 |
|--------|------|------|------|
| `/metrics` 端点访问控制 | 仅内网/授权访问 | ☐ | |
| `/health` 端点访问控制 | 公开或受限 | ☐ | |
| 管理端点保护 | 需认证 | ☐ | |
| API 认证机制 | 已启用 | ☐ | |

### 5.2 敏感信息处理

| 检查项 | 要求 | 状态 | 备注 |
|--------|------|------|------|
| 日志中无密码 | 已脱敏 | ☐ | |
| 日志中无 API Key | 已脱敏 | ☐ | |
| 日志中无用户 PII | 已脱敏或哈希 | ☐ | |
| 错误响应无堆栈 | 生产环境禁用 | ☐ | |

**验证命令**:
```bash
# 检查日志中是否有敏感信息
grep -i "password\|api_key\|secret" /var/log/canvas/*.log
# 预期: 无输出或已脱敏

# 检查错误响应
curl -sf http://localhost:8000/nonexistent | jq '.detail'
# 预期: 无堆栈信息
```

### 5.3 网络安全

| 检查项 | 要求 | 状态 | 备注 |
|--------|------|------|------|
| HTTPS 启用 | 生产必需 | ☐ | |
| CORS 配置 | 仅允许白名单域 | ☐ | |
| 请求速率限制 | 已配置 | ☐ | |

---

## 6. 备份恢复验证 ☐

### 6.1 配置备份

| 检查项 | 备份位置 | 频率 | 已验证 |
|--------|---------|------|--------|
| 应用配置 | _______ | _______ | ☐ |
| 告警规则 | _______ | _______ | ☐ |
| Grafana Dashboard | _______ | _______ | ☐ |
| Prometheus 配置 | _______ | _______ | ☐ |

### 6.2 数据备份

| 检查项 | 备份位置 | 频率 | 保留期 | 已验证 |
|--------|---------|------|--------|--------|
| Neo4j 数据 | _______ | _______ | _______ | ☐ |
| ChromaDB 数据 | _______ | _______ | _______ | ☐ |
| Prometheus 数据 | _______ | _______ | _______ | ☐ |

### 6.3 恢复测试

| 测试项 | 上次测试日期 | 结果 | 状态 |
|--------|-------------|------|------|
| 配置恢复 | _______ | _______ | ☐ |
| 服务回滚 | _______ | _______ | ☐ |
| 数据恢复 | _______ | _______ | ☐ |

---

## 7. 文档完整性验证 ☐

| 文档 | 路径 | 存在 | 已审核 |
|------|------|------|--------|
| 操作手册 | `docs/operations/monitoring-operations-guide.md` | ☐ | ☐ |
| 部署指南 | `docs/deployment/monitoring-deployment-guide.md` | ☐ | ☐ |
| 告警 Runbook | `docs/operations/alert-runbook.md` | ☐ | ☐ |
| Dashboard 指南 | `docs/operations/dashboard-user-guide.md` | ☐ | ☐ |
| 故障演练计划 | `docs/operations/chaos-engineering-plan.md` | ☐ | ☐ |
| 变更日志 | `docs/CHANGELOG-MONITORING.md` | ☐ | ☐ |

---

## 8. 团队准备度验证 ☐

### 8.1 培训完成

| 培训内容 | 参与人员 | 完成日期 | 状态 |
|----------|---------|---------|------|
| Dashboard 使用培训 | 运维团队 | _______ | ☐ |
| 告警响应培训 | 值班人员 | _______ | ☐ |
| 故障排查培训 | 开发 + 运维 | _______ | ☐ |

### 8.2 On-Call 就绪

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 值班排班已确定 | ☐ | |
| 值班联系方式已更新 | ☐ | |
| 升级路径已明确 | ☐ | |
| 事件响应流程已演练 | ☐ | |

### 8.3 工具就绪

| 工具 | 用途 | 访问权限已配置 |
|------|------|---------------|
| Grafana | 监控面板 | ☐ |
| AlertManager | 告警管理 | ☐ |
| 日志系统 | 日志查询 | ☐ |
| 事件管理系统 | 事件跟踪 | ☐ |

---

## 检查结果汇总

### 各模块状态

| 模块 | 通过项 | 总项数 | 状态 |
|------|--------|--------|------|
| 1. 功能完整性 | ___/8 | 8 | ☐ |
| 2. 性能达标 | ___/10 | 10 | ☐ |
| 3. 告警配置 | ___/10 | 10 | ☐ |
| 4. 日志系统 | ___/12 | 12 | ☐ |
| 5. 安全配置 | ___/11 | 11 | ☐ |
| 6. 备份恢复 | ___/9 | 9 | ☐ |
| 7. 文档完整性 | ___/12 | 12 | ☐ |
| 8. 团队准备度 | ___/10 | 10 | ☐ |
| **总计** | ___/82 | 82 | |

### 最终评审

**评审结果**: ☐ 通过 ☐ 有条件通过 ☐ 未通过

**未通过项说明**:
```
1. _______________
2. _______________
3. _______________
```

**整改计划**:
| 问题 | 负责人 | 截止日期 |
|------|--------|---------|
| | | |
| | | |

**评审人签字**: _______________
**评审日期**: _______________

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
