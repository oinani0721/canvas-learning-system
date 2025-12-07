# Canvas Learning System - 混沌工程计划

**版本**: v1.0.0
**更新日期**: 2025-12-03
**文档来源**: [Story 17.6 - Task 6]
**架构参考**: [Source: docs/architecture/performance-monitoring-architecture.md]

---

## 1. 概述

### 1.1 目的

本计划定义 Canvas Learning System 监控系统的混沌工程实践，通过主动注入故障来验证系统的弹性和告警响应能力。

### 1.2 目标

- 验证监控系统在故障场景下的正确性
- 测试告警触发和通知的及时性
- 确保 Runbook 的可操作性
- 培训团队的故障响应能力

### 1.3 范围

| 组件 | 包含 | 排除 |
|------|------|------|
| API 服务 | 延迟注入、错误注入 | 数据损坏 |
| Agent 系统 | 执行超时、资源耗尽 | 外部 LLM 服务中断 |
| 记忆系统 | 连接中断、响应延迟 | 数据丢失 |
| 基础设施 | CPU/内存压力、网络延迟 | 物理硬件故障 |

---

## 2. 混沌实验类别

### 2.1 API 性能退化

#### 实验 CE-001: API 延迟注入

**目标**: 验证 HighAPILatency 告警触发

**场景描述**:
```
注入 API 响应延迟，观察监控系统是否正确捕获并触发告警
```

**实验步骤**:
1. **准备阶段** (5 分钟)
   - 确认 Prometheus 和 AlertManager 运行正常
   - 确认当前无活跃告警
   - 记录基线 P95 延迟

2. **注入阶段** (10 分钟)
   ```python
   # 在中间件中注入延迟
   import asyncio
   import random

   async def chaos_latency_middleware(request, call_next):
       # 注入 1-3 秒随机延迟
       await asyncio.sleep(random.uniform(1.0, 3.0))
       return await call_next(request)
   ```

3. **观察阶段** (15 分钟)
   - 监控 Grafana 仪表板
   - 等待 HighAPILatency 告警触发 (阈值: P95 > 1s for 5m)
   - 验证告警通知到达

4. **恢复阶段** (5 分钟)
   - 移除延迟注入
   - 确认指标恢复正常
   - 确认告警自动解除

**预期结果**:
- [ ] P95 延迟超过 1 秒
- [ ] 5 分钟内触发 HighAPILatency 告警
- [ ] 告警通知发送到配置的渠道
- [ ] 移除注入后 5 分钟内告警解除

**回滚计划**:
```bash
# 紧急回滚：重启服务
sudo systemctl restart canvas-learning

# 或移除中间件配置并重载
# 修改配置文件后：
sudo systemctl reload canvas-learning
```

---

#### 实验 CE-002: API 错误率注入

**目标**: 验证 HighErrorRate 告警触发

**场景描述**:
```
注入随机 500 错误，观察错误率告警
```

**实验步骤**:
1. **准备阶段** (5 分钟)
   - 确认基线错误率 < 0.1%
   - 准备错误注入脚本

2. **注入阶段** (10 分钟)
   ```python
   # 错误注入中间件
   import random
   from fastapi import HTTPException

   async def chaos_error_middleware(request, call_next):
       # 10% 概率返回 500 错误
       if random.random() < 0.10:
           raise HTTPException(status_code=500, detail="Chaos injection")
       return await call_next(request)
   ```

3. **观察阶段** (10 分钟)
   - 监控错误率指标
   - 等待 HighErrorRate 告警 (阈值: > 5% for 2m)

4. **恢复阶段** (5 分钟)
   - 移除错误注入
   - 验证恢复

**预期结果**:
- [ ] 错误率上升到 ~10%
- [ ] 2 分钟内触发 HighErrorRate 告警
- [ ] Runbook 链接包含在告警中
- [ ] 恢复后告警解除

---

### 2.2 Agent 系统故障

#### 实验 CE-003: Agent 执行超时

**目标**: 验证 AgentExecutionSlow 告警

**场景描述**:
```
模拟 Agent 执行超时，验证监控和告警
```

**实验步骤**:
1. **准备阶段**
   - 记录基线 Agent 执行时间 (P95 < 5s)

2. **注入阶段**
   ```python
   # 模拟 Agent 超时
   async def slow_agent_execution():
       await asyncio.sleep(15)  # 强制 15 秒延迟
       return {"result": "delayed"}
   ```

3. **观察阶段**
   - 监控 Agent 执行时间指标
   - 等待 AgentExecutionSlow 告警 (阈值: P95 > 10s for 5m)

4. **恢复阶段**
   - 移除延迟
   - 验证恢复

**预期结果**:
- [ ] Agent P95 执行时间超过 10 秒
- [ ] 告警触发
- [ ] 按 Runbook 执行故障排查

---

#### 实验 CE-004: Agent 并发过载

**目标**: 验证 HighConcurrentTasks 告警

**场景描述**:
```
模拟大量并发 Agent 任务
```

**实验步骤**:
1. **准备阶段**
   - 确认当前并发任务数 < 20

2. **注入阶段**
   ```bash
   # 使用压测工具生成并发请求
   for i in {1..150}; do
       curl -X POST http://localhost:8000/api/v1/agents/invoke \
            -H "Content-Type: application/json" \
            -d '{"agent_type": "basic-decomposition", "input": "test"}' &
   done
   ```

3. **观察阶段**
   - 监控并发任务数指标
   - 等待 HighConcurrentTasks 告警 (阈值: > 100 for 2m)

4. **恢复阶段**
   - 停止压测
   - 等待任务完成

**预期结果**:
- [ ] 并发任务数超过 100
- [ ] 告警触发
- [ ] 系统限流机制生效

---

### 2.3 记忆系统故障

#### 实验 CE-005: 记忆系统连接中断

**目标**: 验证 MemorySystemDown 告警

**场景描述**:
```
模拟记忆系统 (Neo4j/ChromaDB) 连接中断
```

**实验步骤**:
1. **准备阶段**
   - 确认记忆系统健康
   - 准备服务控制脚本

2. **注入阶段**
   ```bash
   # 方式 1: 停止 Neo4j 服务
   sudo systemctl stop neo4j

   # 方式 2: 使用 iptables 阻断连接
   sudo iptables -A OUTPUT -p tcp --dport 7687 -j DROP
   ```

3. **观察阶段** (5 分钟)
   - 监控记忆系统健康状态
   - 等待 MemorySystemDown 告警 (阈值: 连接失败 > 1m)

4. **恢复阶段**
   ```bash
   # 恢复服务
   sudo systemctl start neo4j

   # 或移除 iptables 规则
   sudo iptables -D OUTPUT -p tcp --dport 7687 -j DROP
   ```

**预期结果**:
- [ ] 健康检查报告记忆系统不可用
- [ ] 1 分钟内触发 MemorySystemDown 告警
- [ ] 系统进入降级模式 (如果实现)
- [ ] 恢复后自动重连

---

### 2.4 基础设施压力

#### 实验 CE-006: CPU 压力测试

**目标**: 验证资源监控和告警

**场景描述**:
```
注入 CPU 压力，观察系统行为和监控
```

**实验步骤**:
1. **准备阶段**
   - 记录基线 CPU 使用率

2. **注入阶段**
   ```bash
   # 使用 stress 工具
   stress --cpu 4 --timeout 300

   # 或使用 Python
   python -c "
   import multiprocessing
   def cpu_stress():
       while True:
           pass

   procs = [multiprocessing.Process(target=cpu_stress) for _ in range(4)]
   for p in procs:
       p.start()
   "
   ```

3. **观察阶段**
   - 监控 CPU 使用率
   - 观察 API 延迟变化
   - 观察是否触发级联告警

4. **恢复阶段**
   ```bash
   # 停止 stress
   pkill stress

   # 或停止 Python 进程
   pkill -f cpu_stress
   ```

**预期结果**:
- [ ] CPU 使用率上升到 90%+
- [ ] API 延迟可能增加
- [ ] 资源监控正确记录
- [ ] 可能触发 HighAPILatency 作为级联效应

---

#### 实验 CE-007: 内存压力测试

**目标**: 验证内存监控和 OOM 预防

**场景描述**:
```
注入内存压力，观察系统行为
```

**实验步骤**:
1. **准备阶段**
   - 记录基线内存使用率
   - 确认 OOM killer 配置

2. **注入阶段**
   ```bash
   # 使用 stress
   stress --vm 2 --vm-bytes 1G --timeout 300

   # 或使用 Python
   python -c "
   data = []
   for i in range(100):
       data.append(' ' * (10 * 1024 * 1024))  # 10MB chunks
       import time
       time.sleep(1)
   "
   ```

3. **观察阶段**
   - 监控内存使用率
   - 观察是否触发告警
   - 观察垃圾回收行为

4. **恢复阶段**
   ```bash
   pkill stress
   ```

**预期结果**:
- [ ] 内存使用率上升
- [ ] 监控正确记录内存使用
- [ ] 系统保持稳定 (不触发 OOM)

---

## 3. 季度演练计划

### 3.1 演练频率

| 类型 | 频率 | 参与人员 |
|------|------|---------|
| 桌面演练 | 每月 | 开发 + 运维 |
| 小规模实验 | 每季度 | 运维团队 |
| 全面演练 | 每半年 | 全团队 |

### 3.2 2025 年演练日历

| 季度 | 日期 | 实验 | 负责人 |
|------|------|------|--------|
| Q1 | 2025-03-15 | CE-001, CE-002 | TBD |
| Q2 | 2025-06-15 | CE-003, CE-004 | TBD |
| Q3 | 2025-09-15 | CE-005, CE-006 | TBD |
| Q4 | 2025-12-15 | CE-007 + 全面演练 | TBD |

### 3.3 演练检查清单

#### 演练前 (T-7 天)

- [ ] 确定实验范围和参与人员
- [ ] 通知相关利益相关者
- [ ] 准备回滚计划
- [ ] 在 Staging 环境预演
- [ ] 确认监控和告警系统正常

#### 演练当天 (T-0)

- [ ] 召开简短的启动会议
- [ ] 确认所有参与者就绪
- [ ] 开始实验并记录时间戳
- [ ] 实时监控和记录结果
- [ ] 执行回滚 (如需要)

#### 演练后 (T+1 天)

- [ ] 召开回顾会议
- [ ] 记录发现的问题
- [ ] 更新 Runbook (如需要)
- [ ] 创建改进任务
- [ ] 分享经验教训

---

## 4. 安全注意事项

### 4.1 演练边界

**允许的操作**:
- 延迟注入
- 错误率注入
- 服务重启
- 资源压力测试

**禁止的操作**:
- 数据删除或损坏
- 生产环境未经批准的实验
- 影响外部客户的操作
- 安全漏洞利用

### 4.2 紧急停止程序

如果实验导致意外影响：

1. **立即停止**:
   ```bash
   # 停止所有注入
   pkill -f chaos
   pkill stress
   ```

2. **恢复服务**:
   ```bash
   sudo systemctl restart canvas-learning
   sudo systemctl restart neo4j
   sudo systemctl restart prometheus
   ```

3. **通知团队**:
   - 发送紧急通知到值班群
   - 记录事件时间线

4. **事后分析**:
   - 收集日志和指标
   - 召开事后分析会议

---

## 5. 工具和资源

### 5.1 推荐工具

| 工具 | 用途 | 安装 |
|------|------|------|
| stress | CPU/内存压力 | `apt install stress` |
| tc | 网络延迟 | 内置 Linux |
| iptables | 网络中断 | 内置 Linux |
| chaos-monkey | 自动化混沌 | 参考官方文档 |

### 5.2 监控 Dashboard

演练期间使用专用 Grafana Dashboard:
- URL: `http://grafana:3000/d/chaos-engineering`
- 包含: 实时指标、告警状态、实验时间线

### 5.3 文档链接

- 告警 Runbook: `docs/operations/alert-runbook.md`
- 监控操作手册: `docs/operations/monitoring-operations-guide.md`
- 部署指南: `docs/deployment/monitoring-deployment-guide.md`

---

## 6. 结果记录模板

### 实验记录表

```markdown
# 混沌实验记录

**实验 ID**: CE-XXX
**日期**: YYYY-MM-DD
**执行人**:
**环境**: Staging / Production

## 实验概述
- **目标**:
- **预期结果**:

## 时间线
| 时间 | 事件 | 备注 |
|------|------|------|
| HH:MM | 开始注入 | |
| HH:MM | 告警触发 | |
| HH:MM | 停止注入 | |
| HH:MM | 恢复正常 | |

## 结果
- [ ] 告警正确触发
- [ ] 通知及时送达
- [ ] Runbook 可操作
- [ ] 恢复时间符合 SLA

## 发现的问题
1.
2.

## 改进建议
1.
2.

## 附件
- Grafana 截图:
- 日志文件:
```

---

**文档维护**: 运维团队
**最后更新**: 2025-12-03
**审核状态**: Pending Review
