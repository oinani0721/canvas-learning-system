# Canvas Learning System - 告警响应手册 (Runbook)

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 3]
**告警规则来源**: [Source: docs/architecture/performance-monitoring-architecture.md:281-323]

---

## 目录

1. [告警概述](#1-告警概述)
2. [HighAPILatency - 高API延迟](#2-highapilatency---高api延迟)
3. [HighErrorRate - 高错误率](#3-higherrorrate---高错误率)
4. [AgentExecutionSlow - Agent执行缓慢](#4-agentexecutionslow---agent执行缓慢)
5. [MemorySystemDown - 记忆系统不可用](#5-memorysystemdown---记忆系统不可用)
6. [HighConcurrentTasks - 高并发任务](#6-highconcurrenttasks---高并发任务)
7. [告警升级矩阵](#7-告警升级矩阵)
8. [On-Call流程](#8-on-call流程)

---

## 1. 告警概述

### 1.1 告警级别定义

| 级别 | 含义 | 响应时间 | 通知方式 |
|------|------|---------|---------|
| **Critical** | 服务不可用或严重降级 | 5分钟内 | 电话 + 短信 + 即时通讯 |
| **Warning** | 性能下降或异常趋势 | 30分钟内 | 即时通讯 + 邮件 |
| **Info** | 信息性通知 | 工作时间处理 | 邮件 |

### 1.2 告警汇总

| 告警名称 | 触发条件 | 持续时间 | 级别 |
|----------|---------|---------|------|
| HighAPILatency | P95延迟 > 1s | 5分钟 | Warning |
| HighErrorRate | 错误率 > 5% | 2分钟 | Critical |
| AgentExecutionSlow | Agent P95 > 10s | 5分钟 | Warning |
| MemorySystemDown | 连接失败 | 1分钟 | Critical |
| HighConcurrentTasks | 并发 > 100 | 2分钟 | Warning |

### 1.3 常用查询命令

```bash
# 获取当前活跃告警
# ✅ Verified from OpenAPI Spec (canvas-api.openapi.yml:644-662)
curl -s http://localhost:8000/metrics/alerts | jq .

# 按级别过滤
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.severity=="critical")'

# 查看原始指标
curl -s http://localhost:8000/metrics | grep canvas_
```

---

## 2. HighAPILatency - 高API延迟

### 告警信息

- **名称**: HighAPILatency
- **严重级别**: Warning
- **触发条件**: `histogram_quantile(0.95, rate(canvas_api_request_latency_seconds_bucket[5m])) > 1`
- **持续时间**: 5分钟
- **影响**: 用户体验下降，请求超时

### 症状描述

用户报告:
- API 响应缓慢
- 请求超时错误
- 页面加载时间过长
- Canvas 操作卡顿

### 可能原因

1. **数据库查询缓慢**
   - Neo4j 复杂查询
   - 索引缺失
   - 连接池耗尽

2. **Agent 执行阻塞**
   - LLM API 响应慢
   - Agent 内部死锁

3. **资源不足**
   - CPU 使用率过高
   - 内存不足导致 swap
   - 网络带宽饱和

4. **外部服务问题**
   - ChromaDB 响应慢
   - OpenAI API 限流

### 排查步骤

```bash
# Step 1: 确认告警状态
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="HighAPILatency")'

# Step 2: 检查当前 P95 延迟
curl -s http://localhost:8000/metrics | grep "canvas_api_request_latency_seconds" | grep "quantile=\"0.95\""

# Step 3: 识别慢端点
curl -s http://localhost:8000/metrics | grep "canvas_api_request_latency_seconds_bucket" | \
  awk -F'{' '{print $2}' | awk -F',' '{print $1}' | sort | uniq -c | sort -rn

# Step 4: 检查数据库性能
# Neo4j 查询延迟
curl -s http://localhost:8000/metrics | grep "canvas_memory_query_seconds"

# Step 5: 检查系统资源
top -bn1 | head -20
free -m
iostat -x 1 3

# Step 6: 检查性能日志
tail -100 /var/log/canvas/canvas-performance.log | jq 'select(.duration_ms > 1000)'

# Step 7: 检查外部服务
curl -w "@curl-format.txt" -o /dev/null -s http://chromadb:8000/api/v1/heartbeat
```

### 缓解措施

**临时措施** (快速恢复):
```bash
# 1. 重启服务 (清理可能的内存泄漏)
systemctl restart canvas-learning

# 2. 清理缓存 (如果缓存异常)
curl -X POST http://localhost:8000/admin/cache/clear

# 3. 降级非核心功能 (如开启)
curl -X POST http://localhost:8000/admin/features/disable/non-essential
```

**永久措施** (根本解决):
1. 优化慢查询
   - 添加数据库索引
   - 重写复杂查询
2. 扩容资源
   - 增加服务实例
   - 升级硬件配置
3. 优化代码
   - 添加缓存
   - 并行化处理

### 升级路径

- **15分钟未解决**: 通知开发负责人
- **30分钟未解决**: 升级至架构师
- **1小时未解决**: 启动紧急响应流程

### 相关资源

- **Dashboard**: Grafana > Canvas API > Latency Panel
- **日志查询**: `jq 'select(.duration_ms > 1000)' canvas-performance.log`
- **相关文档**: [监控架构文档](../architecture/performance-monitoring-architecture.md)

---

## 3. HighErrorRate - 高错误率

### 告警信息

- **名称**: HighErrorRate
- **严重级别**: Critical
- **触发条件**: `sum(rate(canvas_api_requests_total{status=~"5.."}[5m])) / sum(rate(canvas_api_requests_total[5m])) > 0.05`
- **持续时间**: 2分钟
- **影响**: 服务部分或完全不可用

### 症状描述

用户报告:
- API 返回 500 错误
- 功能不可用
- 数据保存失败
- Canvas 无法加载

### 可能原因

1. **代码错误**
   - 新部署引入 bug
   - 未处理的异常

2. **依赖服务故障**
   - Neo4j 连接失败
   - ChromaDB 不可用
   - LLM API 错误

3. **资源耗尽**
   - 内存溢出
   - 磁盘空间不足
   - 文件描述符耗尽

4. **配置问题**
   - 环境变量错误
   - 凭据过期

### 排查步骤

```bash
# Step 1: 确认告警状态
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="HighErrorRate")'

# Step 2: 计算当前错误率
curl -s http://localhost:8000/metrics | grep "canvas_api_requests_total" | \
  awk '/status="5/ {s+=$NF} /requests_total/ {t+=$NF} END {print "Error rate:", s/t*100, "%"}'

# Step 3: 识别错误类型
curl -s http://localhost:8000/metrics | grep 'status="5' | head -20

# Step 4: 检查错误日志
tail -200 /var/log/canvas/canvas-error.log | jq '.exception'

# Step 5: 检查依赖服务
# Neo4j
cypher-shell -u neo4j -p password "RETURN 1"

# ChromaDB
curl -sf http://chromadb:8000/api/v1/heartbeat

# Step 6: 检查系统资源
df -h
free -m
ulimit -n

# Step 7: 检查最近部署
git log --oneline -5
```

### 缓解措施

**临时措施** (快速恢复):
```bash
# 1. 如果是新部署引起，立即回滚
bash scripts/rollback.sh stable-release

# 2. 重启服务
systemctl restart canvas-learning

# 3. 检查并重启依赖服务
systemctl restart neo4j
systemctl restart chromadb
```

**永久措施** (根本解决):
1. 修复代码 bug
2. 添加错误处理
3. 增加重试机制
4. 添加断路器

### 升级路径

- **5分钟未解决**: 通知开发负责人 + 架构师
- **15分钟未解决**: 启动紧急响应流程
- **30分钟未解决**: 通知管理层

### 相关资源

- **Dashboard**: Grafana > Canvas API > Error Rate Panel
- **日志查询**: `tail -f canvas-error.log | jq '.exception'`
- **相关文档**: [ADR-009 Error Handling](../architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md)

---

## 4. AgentExecutionSlow - Agent执行缓慢

### 告警信息

- **名称**: AgentExecutionSlow
- **严重级别**: Warning
- **触发条件**: `histogram_quantile(0.95, rate(canvas_agent_execution_seconds_bucket[5m])) > 10`
- **持续时间**: 5分钟
- **影响**: 学习功能响应缓慢，用户等待时间长

### 症状描述

用户报告:
- Agent 操作超时
- Canvas 节点生成缓慢
- 分析结果等待时间长
- "正在处理" 状态持续很久

### 可能原因

1. **LLM API 问题**
   - API 响应慢
   - 触发限流
   - Token 超限

2. **复杂任务**
   - Canvas 节点过多
   - 复杂推理任务
   - 大量数据处理

3. **资源竞争**
   - 并发 Agent 过多
   - 共享资源争用

4. **网络问题**
   - 外部 API 网络延迟
   - DNS 解析慢

### 排查步骤

```bash
# Step 1: 确认告警状态
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="AgentExecutionSlow")'

# Step 2: 检查 Agent 执行时间分布
curl -s http://localhost:8000/metrics | grep "canvas_agent_execution_seconds" | grep "quantile"

# Step 3: 识别慢 Agent 类型
curl -s http://localhost:8000/metrics/summary | jq '.agents.by_type'

# Step 4: 检查并发任务数
curl -s http://localhost:8000/metrics | grep "canvas_concurrent_tasks"

# Step 5: 检查 LLM API 状态
curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.error'

# Step 6: 检查 Agent 日志
grep "agent_type" /var/log/canvas/canvas-performance.log | jq 'select(.duration_s > 10)'

# Step 7: 检查网络延迟
ping -c 5 api.openai.com
traceroute api.openai.com
```

### 缓解措施

**临时措施** (快速恢复):
```bash
# 1. 降低并发度
curl -X POST http://localhost:8000/admin/config \
  -d '{"max_concurrent_agents": 5}'

# 2. 启用缓存
curl -X POST http://localhost:8000/admin/cache/enable

# 3. 取消超时任务
curl -X POST http://localhost:8000/admin/tasks/cancel-stale
```

**永久措施** (根本解决):
1. 优化 Agent 逻辑
2. 实现流式响应
3. 添加任务队列
4. 升级 LLM API 配额

### 升级路径

- **15分钟未解决**: 通知开发负责人
- **30分钟未解决**: 检查 LLM API 状态页面
- **1小时未解决**: 考虑降级方案

### 相关资源

- **Dashboard**: Grafana > Canvas Agents > Execution Time Panel
- **日志查询**: `jq 'select(.agent_type != null and .duration_s > 10)'`
- **相关文档**: [ADR-004 Async Execution](../architecture/decisions/ADR-004-ASYNC-EXECUTION-ENGINE.md)

---

## 5. MemorySystemDown - 记忆系统不可用

### 告警信息

- **名称**: MemorySystemDown
- **严重级别**: Critical
- **触发条件**: `up{job="canvas-memory"} == 0` 或健康检查失败
- **持续时间**: 1分钟
- **影响**: 学习历史无法访问，知识图谱功能不可用

### 症状描述

用户报告:
- 无法访问学习历史
- Canvas 无法加载已保存内容
- 搜索功能不可用
- 关联知识无法显示

### 可能原因

1. **Neo4j 故障**
   - 服务崩溃
   - 端口不可达
   - 认证失败

2. **ChromaDB 故障**
   - 服务停止
   - 索引损坏
   - 磁盘空间不足

3. **网络问题**
   - 容器网络隔离
   - 防火墙规则变更

4. **资源问题**
   - 内存不足导致 OOM
   - 磁盘满导致写入失败

### 排查步骤

```bash
# Step 1: 确认告警状态
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="MemorySystemDown")'

# Step 2: 检查健康端点中的记忆组件
curl -s http://localhost:8000/health | jq '.components.memory'

# Step 3: 检查 Neo4j 服务
# ✅ Verified from Graphiti Skill (SKILL.md - Health Check)
systemctl status neo4j
cypher-shell -u neo4j -p password "RETURN 1"

# Step 4: 检查 ChromaDB 服务
curl -sf http://chromadb:8000/api/v1/heartbeat

# Step 5: 检查网络连通性
nc -zv neo4j-host 7687
nc -zv chromadb-host 8000

# Step 6: 检查资源使用
docker stats neo4j chromadb
df -h /var/lib/neo4j
df -h /var/lib/chromadb

# Step 7: 检查日志
docker logs neo4j --tail 100
docker logs chromadb --tail 100
```

### 缓解措施

**临时措施** (快速恢复):
```bash
# 1. 重启 Neo4j
systemctl restart neo4j
# 或 docker
docker restart neo4j

# 2. 重启 ChromaDB
systemctl restart chromadb
# 或 docker
docker restart chromadb

# 3. 启用降级模式 (如果支持)
curl -X POST http://localhost:8000/admin/mode/degraded
```

**永久措施** (根本解决):
1. 配置高可用 (HA)
2. 设置自动重启
3. 增加监控覆盖
4. 实现故障转移

### 升级路径

- **1分钟未解决**: 自动尝试重启
- **5分钟未解决**: 通知运维 + 开发
- **15分钟未解决**: 启动紧急响应

### 相关资源

- **Dashboard**: Grafana > Canvas Memory > Connection Status Panel
- **日志查询**: `docker logs neo4j 2>&1 | grep -i error`
- **相关文档**: [Graphiti Skill - Troubleshooting](.claude/skills/graphiti/SKILL.md)

---

## 6. HighConcurrentTasks - 高并发任务

### 告警信息

- **名称**: HighConcurrentTasks
- **严重级别**: Warning
- **触发条件**: `canvas_concurrent_tasks > 100`
- **持续时间**: 2分钟
- **影响**: 系统负载过高，响应变慢，可能导致资源耗尽

### 症状描述

用户报告:
- 新请求排队等待
- 任务执行缓慢
- 系统整体变慢
- 偶发超时错误

### 可能原因

1. **流量突增**
   - 用户活动高峰
   - 批量操作触发
   - 爬虫或滥用

2. **任务积压**
   - 下游服务变慢
   - 任务处理阻塞
   - 重试风暴

3. **资源泄漏**
   - 任务未正确完成
   - 连接未释放

4. **配置问题**
   - 并发限制过高
   - 超时设置过长

### 排查步骤

```bash
# Step 1: 确认告警状态
curl -s http://localhost:8000/metrics/alerts | jq '.alerts[] | select(.name=="HighConcurrentTasks")'

# Step 2: 检查当前并发数
curl -s http://localhost:8000/metrics | grep "canvas_concurrent_tasks"

# Step 3: 检查请求分布
curl -s http://localhost:8000/metrics | grep "canvas_api_requests_total" | \
  awk -F'{' '{print $2}' | sort | uniq -c | sort -rn | head -10

# Step 4: 识别长时间运行任务
curl -s http://localhost:8000/admin/tasks/active | jq '.tasks[] | select(.duration_s > 60)'

# Step 5: 检查系统负载
uptime
vmstat 1 5

# Step 6: 检查网络连接
netstat -an | grep 8000 | wc -l

# Step 7: 检查队列状态 (如使用)
redis-cli llen canvas:task_queue
```

### 缓解措施

**临时措施** (快速恢复):
```bash
# 1. 启用限流
curl -X POST http://localhost:8000/admin/rate-limit/enable \
  -d '{"max_requests_per_second": 50}'

# 2. 拒绝新请求 (熔断)
curl -X POST http://localhost:8000/admin/circuit-breaker/open

# 3. 取消积压任务
curl -X POST http://localhost:8000/admin/tasks/cancel-all-pending

# 4. 扩容 (如果使用 K8s)
kubectl scale deployment canvas-api --replicas=5
```

**永久措施** (根本解决):
1. 实现负载均衡
2. 配置自动扩缩容
3. 优化任务处理效率
4. 添加请求队列

### 升级路径

- **5分钟未解决**: 通知运维
- **15分钟未解决**: 考虑扩容
- **30分钟未解决**: 启动降级方案

### 相关资源

- **Dashboard**: Grafana > Canvas System > Concurrent Tasks Panel
- **日志查询**: `grep "concurrent_tasks" canvas-main.log`
- **相关文档**: [性能优化文档](../architecture/performance-monitoring-architecture.md)

---

## 7. 告警升级矩阵

### 7.1 升级时间表

| 告警 | L1 (运维) | L2 (开发) | L3 (架构) | 管理层 |
|------|-----------|-----------|-----------|--------|
| HighAPILatency | 0分钟 | 15分钟 | 30分钟 | 1小时 |
| HighErrorRate | 0分钟 | 5分钟 | 15分钟 | 30分钟 |
| AgentExecutionSlow | 0分钟 | 15分钟 | 30分钟 | - |
| MemorySystemDown | 0分钟 | 5分钟 | 15分钟 | 30分钟 |
| HighConcurrentTasks | 0分钟 | 15分钟 | 30分钟 | - |

### 7.2 联系人列表

| 级别 | 角色 | 联系方式 | 职责 |
|------|------|---------|------|
| L1 | 运维值班 | oncall@example.com | 初步排查、重启服务 |
| L2 | 开发负责人 | dev-lead@example.com | 代码排查、紧急修复 |
| L3 | 架构师 | architect@example.com | 架构决策、根因分析 |
| 管理 | 技术总监 | cto@example.com | 资源协调、对外沟通 |

---

## 8. On-Call流程

### 8.1 值班安排

- **轮值周期**: 每周轮换
- **值班时间**: 7x24
- **交接时间**: 每周一 10:00

### 8.2 值班职责

1. **响应告警**: 收到告警后 5 分钟内确认
2. **初步排查**: 按 Runbook 执行排查步骤
3. **升级决策**: 无法解决时及时升级
4. **记录事件**: 在事件管理系统中记录
5. **事后复盘**: 参与 Post-Mortem

### 8.3 告警响应流程

```
┌──────────────┐
│ 收到告警通知 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5分钟内确认  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ 查看Runbook  │────►│ 执行排查步骤 │
└──────────────┘     └──────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 问题已定位   │     │ 需要更多信息 │     │ 无法解决     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 执行缓解措施 │     │ 收集日志数据 │     │ 升级到 L2/L3 │
└──────┬───────┘     └──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│ 验证恢复状态 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 记录事件报告 │
└──────────────┘
```

### 8.4 事件报告模板

```markdown
## 事件报告

**事件ID**: INC-2025-001
**告警名称**: HighErrorRate
**发生时间**: 2025-01-15 14:30:00
**恢复时间**: 2025-01-15 15:00:00
**持续时间**: 30分钟
**影响范围**: 50% 用户请求失败

### 时间线
- 14:30 - 告警触发
- 14:35 - 值班确认告警
- 14:40 - 定位到数据库连接问题
- 14:50 - 重启数据库连接池
- 15:00 - 服务恢复正常

### 根因分析
数据库连接池配置过小，在流量高峰期耗尽

### 改进措施
1. 增加连接池大小 (20 → 50)
2. 添加连接池监控指标
3. 设置连接池使用率告警

### 后续行动
- [ ] 更新配置 (负责人: XX, 截止: 2025-01-20)
- [ ] 添加监控 (负责人: XX, 截止: 2025-01-25)
```

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
