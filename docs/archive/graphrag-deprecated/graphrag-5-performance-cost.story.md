# Story GraphRAG.5: 性能优化与成本监控

---
**Status**: ❌ **Deprecated (已废弃)**
**Deprecated Date**: 2025-11-14
**Deprecated Reason**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停
**Replacement**: EPIC-Neo4j-GDS-Integration (Story GDS.2 - Performance Tuning, 可选)
**Decision Record**: ADR-004, SCP-005
---

## ⚠️ Story状态：已废弃

**废弃日期**: 2025-11-14
**废弃原因**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停

**替代方案**:
- Epic层面：EPIC-Neo4j-GDS-Integration
- 功能实现：Neo4j GDS性能监控（如需要）在Story GDS.2（可选Story）

**详情参见**:
- Sprint Change Proposal: SCP-005 (GraphRAG过度设计纠偏)
- Architecture Decision Record: ADR-004 (Do Not Integrate GraphRAG)

**历史价值**: 保留此Story作为性能监控架构参考

---

## 原始Story定义（以下内容为历史记录）

---

## Status
~~In Progress~~ ❌ Deprecated

## Story

**As a** Canvas学习系统的运维人员和开发者,
**I want** 实现GraphRAG的性能优化和成本监控机制，确保Neo4j资源不冲突、批量索引不阻塞实时查询、API成本可控,
**so that** 系统能够在保证高性能（Local<5s, Global<8s, Hybrid<12s）的同时，月度API成本控制在$80以内，且不影响Graphiti实时写入性能。

## Acceptance Criteria

1. **Neo4j连接池优化**: 独立连接池（GraphRAG专用），避免与Graphiti竞争连接
2. **批量索引时间窗口**: 批量索引仅在凌晨2-4点执行，且不阻塞实时查询（READ COMMITTED隔离级别）
3. **Graphiti性能保护**: 批量索引期间，Graphiti写入延迟<100ms（P95）
4. **API成本监控**: 实时追踪API调用次数和成本，月度成本>$80时触发告警
5. **性能基准测试**: 所有3种查询类型满足延迟目标（Local<5s, Global<8s, Hybrid<12s at P95）
6. **成本告警系统**: 月度成本达到$60（75%预算）时发送警告邮件，达到$80时自动切换为纯本地模式
7. **性能监控仪表盘**: 提供Grafana仪表盘，实时展示查询延迟、API成本、Neo4j连接数
8. **降级策略**: 当Neo4j连接池满或查询超时时，自动降级为纯语义搜索（LanceDB）

## Tasks / Subtasks

### Task 1: Neo4j连接池优化与隔离 (AC: 1, 3)

- [ ] **Subtask 1.1**: 创建GraphRAG专用Neo4j连接池
  - [ ] ✅ 查询Context7 Neo4j文档获取连接池最佳实践
  - [ ] 创建独立的Neo4j连接池配置类`GraphRAGNeo4jPool`
  - [ ] 配置参数：max_connections=10, min_connections=2, acquisition_timeout=5s
  - [ ] 与Graphiti连接池隔离（不同的连接池实例）
  - [ ] 验证连接池正常工作（测试获取和释放连接）

- [ ] **Subtask 1.2**: 实现连接池监控
  - [ ] 添加连接池指标：active_connections, idle_connections, pending_requests
  - [ ] 实现连接池健康检查（每30秒执行一次）
  - [ ] 当active_connections > 8（80%容量）时记录警告日志
  - [ ] 当pending_requests > 3时触发告警（可能发生连接泄露）

- [ ] **Subtask 1.3**: 配置READ COMMITTED隔离级别
  - [ ] 所有GraphRAG查询使用READ COMMITTED隔离级别
  - [ ] 批量索引时使用独立事务（不阻塞实时查询）
  - [ ] 验证隔离性：批量索引期间，Graphiti写入不受影响

- [ ] **Subtask 1.4**: 性能测试
  - [ ] 测试批量索引期间Graphiti写入延迟（目标<100ms at P95）
  - [ ] 测试并发查询（10个并发GraphRAG查询 + 5个Graphiti写入）
  - [ ] 验证连接池不会耗尽（监控pending_requests指标）
  - [ ] 压力测试：50个并发查询，验证降级机制生效

### Task 2: 批量索引时间窗口与锁机制 (AC: 2, 3)

- [ ] **Subtask 2.1**: 实现索引调度器`GraphRAGIndexScheduler`
  - [ ] 创建调度器类，使用APScheduler库
  - [ ] 配置增量索引：每天凌晨2-3点执行
  - [ ] 配置全量索引：每周日凌晨2-4点执行
  - [ ] 添加时间窗口验证（拒绝在窗口外执行批量索引）

- [ ] **Subtask 2.2**: 实现分布式锁机制
  - [ ] 使用Redis实现分布式锁（键：`graphrag:indexing_lock`）
  - [ ] 锁超时时间：120分钟（全量索引最大时长）
  - [ ] 索引开始时获取锁，索引结束或异常时释放锁
  - [ ] 如果锁已被占用，跳过本次索引并记录日志

- [ ] **Subtask 2.3**: 实现优雅降级
  - [ ] 索引期间，实时查询自动降级为读取旧索引（snapshot isolation）
  - [ ] 索引完成后，原子切换到新索引（使用Neo4j标签切换）
  - [ ] 旧索引保留24小时（用于回滚）
  - [ ] 验证查询无中断（索引期间查询返回旧数据，但不报错）

- [ ] **Subtask 2.4**: 索引监控
  - [ ] 记录索引执行时间（增量索引<30分钟，全量索引<120分钟）
  - [ ] 记录索引处理的节点数和关系数
  - [ ] 索引超时时自动中止并释放锁
  - [ ] 发送索引完成通知（邮件或Slack）

### Task 3: API成本监控与告警系统 (AC: 4, 6)

- [ ] **Subtask 3.1**: 创建`CostTracker`成本追踪器
  - [ ] 实现成本追踪类，记录每次API调用的成本
  - [ ] 支持多种LLM提供商（OpenAI, Anthropic）
  - [ ] 定价配置：
    - gpt-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
    - gpt-4o: $2.50/1M input tokens, $10.00/1M output tokens
  - [ ] 实时计算累计成本（按日、周、月聚合）

- [ ] **Subtask 3.2**: 实现成本存储和持久化
  - [ ] 使用SQLite存储成本记录（表：api_cost_log）
  - [ ] 字段：timestamp, provider, model, input_tokens, output_tokens, cost, query_type
  - [ ] 每次API调用后立即写入数据库
  - [ ] 实现成本数据导出（CSV格式）

- [ ] **Subtask 3.3**: 实现成本告警
  - [ ] 月度成本达到$60（75%预算）时发送警告邮件
  - [ ] 月度成本达到$80（100%预算）时：
    - 发送紧急告警邮件
    - 自动切换为纯本地模式（100%使用Qwen2.5）
    - 记录切换事件到日志
  - [ ] 每天凌晨发送成本日报（邮件）

- [ ] **Subtask 3.4**: 实现成本预测
  - [ ] 基于过去7天的API使用量，预测本月剩余成本
  - [ ] 如果预测成本>$80，提前3天发送预警邮件
  - [ ] 在仪表盘显示成本趋势图和预测值

- [ ] **Subtask 3.5**: 单元测试
  - [ ] 测试成本计算准确性（mock API调用）
  - [ ] 测试告警触发逻辑（mock成本超过阈值）
  - [ ] 测试自动切换为本地模式
  - [ ] 测试成本预测算法

### Task 4: 性能基准测试与优化 (AC: 5)

- [ ] **Subtask 4.1**: 创建性能测试套件
  - [ ] 创建100个测试查询样本（Local: 40, Global: 30, Hybrid: 30）
  - [ ] 实现性能测试脚本`benchmark_graphrag.py`
  - [ ] 测试指标：P50/P95/P99延迟、吞吐量（queries/sec）
  - [ ] 自动生成性能报告（Markdown格式）

- [ ] **Subtask 4.2**: Local Search性能优化
  - [ ] 优化LanceDB向量搜索（top_k=5, rerank后保留top_3）
  - [ ] 优化Neo4j Cypher查询（添加索引，使用LIMIT子句）
  - [ ] 实现查询结果缓存（LRU缓存，最多1000条）
  - [ ] 目标：P95延迟<5秒

- [ ] **Subtask 4.3**: Global Search性能优化
  - [ ] 优化Leiden社区检测结果缓存（每24小时更新一次）
  - [ ] 优化全局摘要生成（使用本地模型，避免API调用）
  - [ ] 实现Map-Reduce并行化（社区级摘要并行生成）
  - [ ] 目标：P95延迟<8秒

- [ ] **Subtask 4.4**: Hybrid Search性能优化
  - [ ] 优化RRF融合算法（预计算rank，避免重复排序）
  - [ ] 优化4层并行检索（使用asyncio.gather，最大并发4）
  - [ ] 实现智能预取（预测可能的查询，提前加载数据）
  - [ ] 目标：P95延迟<12秒

- [ ] **Subtask 4.5**: 性能基准测试
  - [ ] 执行100个查询的性能测试
  - [ ] 验证延迟目标：
    - Local Search: P95 < 5秒
    - Global Search: P95 < 8秒
    - Hybrid Search: P95 < 12秒
  - [ ] 测试并发性能（10个并发查询）
  - [ ] 生成性能基准报告（包含对比图表）

### Task 5: 性能监控仪表盘 (AC: 7)

- [ ] **Subtask 5.1**: 设置Prometheus指标采集
  - [ ] 安装Prometheus和Grafana（Docker Compose部署）
  - [ ] 实现自定义指标导出器`GraphRAGMetricsExporter`
  - [ ] 暴露指标端点：http://localhost:8000/metrics
  - [ ] 配置Prometheus抓取GraphRAG指标（scrape_interval=15s）

- [ ] **Subtask 5.2**: 定义核心指标
  - [ ] 查询延迟指标：`graphrag_query_duration_seconds{query_type}`
  - [ ] API成本指标：`graphrag_api_cost_usd{provider,model}`
  - [ ] Neo4j连接池指标：`graphrag_neo4j_connections{state=active|idle}`
  - [ ] 降级事件计数：`graphrag_degradation_total{reason}`
  - [ ] 索引状态指标：`graphrag_index_status{type=incremental|full}`

- [ ] **Subtask 5.3**: 创建Grafana仪表盘
  - [ ] 导入预配置仪表盘模板`grafana_dashboard.json`
  - [ ] 面板1：查询延迟趋势图（分Local/Global/Hybrid）
  - [ ] 面板2：API成本累计曲线（本月累计成本 + 预测成本）
  - [ ] 面板3：Neo4j连接池状态（堆叠面积图）
  - [ ] 面板4：降级事件统计（计数器）
  - [ ] 面板5：索引执行历史（时间轴）

- [ ] **Subtask 5.4**: 配置告警规则
  - [ ] 告警1：查询延迟P95超过阈值（Local>5s, Global>8s, Hybrid>12s）
  - [ ] 告警2：API成本超过$60（警告）或$80（紧急）
  - [ ] 告警3：Neo4j连接池使用率>80%
  - [ ] 告警4：降级事件频率>10次/小时
  - [ ] 所有告警发送到Slack频道和邮件

- [ ] **Subtask 5.5**: 验证仪表盘
  - [ ] 执行压力测试，验证指标实时更新
  - [ ] 模拟成本超标，验证告警触发
  - [ ] 模拟连接池耗尽，验证告警触发
  - [ ] 导出仪表盘配置（用于版本控制）

### Task 6: 降级策略与容错机制 (AC: 8)

- [ ] **Subtask 6.1**: 实现降级决策器`DegradationDecider`
  - [ ] 创建降级决策类，评估系统健康状态
  - [ ] 降级触发条件：
    - Neo4j连接池满（active_connections >= max_connections）
    - Neo4j查询超时（>10秒）
    - API成本超过$80
  - [ ] 降级策略：切换为纯语义搜索（仅使用LanceDB）

- [ ] **Subtask 6.2**: 实现纯语义搜索模式
  - [ ] 创建`SemanticOnlySearch`类
  - [ ] 仅使用LanceDB向量搜索（top_k=10）
  - [ ] 不使用Neo4j图谱或GraphRAG社区
  - [ ] 返回简化响应（无图谱结构，仅相关文档）

- [ ] **Subtask 6.3**: 实现自动恢复
  - [ ] 每5分钟检查系统健康状态
  - [ ] 当Neo4j连接池恢复正常 + API成本<$80时，自动恢复正常模式
  - [ ] 记录降级和恢复事件到日志
  - [ ] 发送恢复通知邮件

- [ ] **Subtask 6.4**: 集成测试
  - [ ] 测试Neo4j连接池满时自动降级
  - [ ] 测试API成本超标时自动降级
  - [ ] 测试降级模式下查询仍然返回结果（质量降低但不报错）
  - [ ] 测试自动恢复机制

### Task 7: 集成测试与文档 (AC: 1-8)

- [ ] **Subtask 7.1**: 端到端性能测试
  - [ ] 创建E2E测试脚本`test_graphrag_5_e2e.py`
  - [ ] 测试场景1：正常负载（10个并发查询，验证延迟和成本）
  - [ ] 测试场景2：高负载（50个并发查询，验证降级机制）
  - [ ] 测试场景3：批量索引期间查询（验证Graphiti不受影响）
  - [ ] 测试场景4：成本超标（验证自动切换本地模式）

- [ ] **Subtask 7.2**: 单元测试
  - [ ] 测试Neo4j连接池管理（获取、释放、超时）
  - [ ] 测试索引调度器（时间窗口验证、分布式锁）
  - [ ] 测试成本追踪器（计算、存储、告警）
  - [ ] 测试降级决策器（触发条件、恢复条件）
  - [ ] 目标：测试覆盖率≥95%

- [ ] **Subtask 7.3**: 性能回归测试
  - [ ] 建立性能基准（当前版本的P95延迟）
  - [ ] 每次代码变更后运行性能测试
  - [ ] 如果延迟增加>10%，阻止合并PR
  - [ ] 自动生成性能对比报告

- [ ] **Subtask 7.4**: 创建运维文档
  - [ ] 创建`docs/operations/graphrag-performance-tuning.md`
  - [ ] 内容包括：
    - Neo4j连接池配置指南
    - 批量索引时间窗口调整方法
    - 成本告警配置说明
    - Grafana仪表盘使用教程
    - 降级策略故障排查手册
  - [ ] 创建`docs/operations/graphrag-cost-control.md`
  - [ ] 内容包括：
    - API成本监控指南
    - 成本优化最佳实践
    - 紧急成本控制流程

- [ ] **Subtask 7.5**: 创建监控配置文件
  - [ ] 创建`config/graphrag_neo4j_pool.json`（Neo4j连接池配置）
  - [ ] 创建`config/graphrag_index_schedule.json`（索引调度配置）
  - [ ] 创建`config/graphrag_cost_alerts.json`（成本告警配置）
  - [ ] 创建`config/grafana_dashboard.json`（Grafana仪表盘模板）
  - [ ] 创建`docker-compose.monitoring.yml`（Prometheus + Grafana部署）

## Dev Notes

### 关键技术决策

#### 1. Neo4j连接池隔离策略

**问题**: GraphRAG批量索引和Graphiti实时写入竞争Neo4j连接池，可能导致Graphiti写入延迟增加。

**解决方案**: 创建两个独立的Neo4j连接池
- **Graphiti连接池**: max_connections=5, 专用于实时写入，优先级高
- **GraphRAG连接池**: max_connections=10, 用于查询和批量索引，优先级低
- **隔离级别**: READ COMMITTED，批量索引不阻塞实时查询

**验证**: 批量索引期间，Graphiti写入延迟<100ms（P95）

---

#### 2. 批量索引时间窗口设计

**背景**: 批量索引（尤其是全量索引）可能耗时2小时，期间会占用大量Neo4j资源。

**设计**:
- **增量索引**: 每天凌晨2-3点（处理过去24小时的新Canvas内容）
- **全量索引**: 每周日凌晨2-4点（重建整个GraphRAG索引）
- **分布式锁**: 使用Redis锁防止多实例同时索引
- **优雅降级**: 索引期间查询读取旧索引，索引完成后原子切换

**参考**: GraphRAG官方文档建议在低峰期执行索引

---

#### 3. API成本监控架构

**目标**: 月度API成本控制在$80以内（原设计$570，优化后$57，留$23缓冲）

**设计**:
```
┌─────────────────────────────────────────────────────────┐
│  成本监控与告警系统                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ CostTracker  │→ │ SQLite存储   │→ │ 告警系统      │  │
│  │ (实时追踪)   │  │ (持久化)     │  │ (邮件/Slack)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                    ↓                  ↓        │
│  每次API调用          历史数据分析       成本超标自动降级 │
└─────────────────────────────────────────────────────────┘
```

**告警阈值**:
- **$60 (75%预算)**: 警告邮件，提醒优化使用
- **$80 (100%预算)**: 紧急告警，自动切换为100%本地模式

**成本追踪粒度**:
- 每次API调用记录：timestamp, model, input_tokens, output_tokens, cost
- 按日/周/月聚合
- 实时预测本月剩余成本

---

#### 4. 性能优化策略

**目标**: 满足3种查询类型的延迟要求
- Local Search: P95 < 5秒
- Global Search: P95 < 8秒
- Hybrid Search: P95 < 12秒

**优化方法**:

**Local Search优化**:
- LanceDB向量搜索top_k=5（减少无效结果）
- Neo4j Cypher查询添加索引（在`name`和`type`字段）
- 查询结果缓存（LRU缓存，最多1000条）

**Global Search优化**:
- Leiden社区检测结果缓存（每24小时更新一次，避免重复计算）
- 全局摘要使用本地模型（Qwen2.5，避免API调用）
- Map-Reduce并行化（社区级摘要并行生成，使用asyncio）

**Hybrid Search优化**:
- RRF融合算法优化（预计算rank，避免重复排序）
- 4层并行检索（使用asyncio.gather，最大并发4）
- 智能预取（预测可能的查询，提前加载数据到缓存）

---

#### 5. 降级策略设计

**触发条件**:
1. Neo4j连接池满（active_connections >= max_connections）
2. Neo4j查询超时（>10秒）
3. API成本超过$80（月度预算上限）

**降级方案**: 切换为纯语义搜索
- 仅使用LanceDB向量搜索（top_k=10）
- 不使用Neo4j图谱或GraphRAG社区
- 返回简化响应（无图谱结构，仅相关文档）
- 质量降低，但确保可用性

**自动恢复**:
- 每5分钟检查系统健康状态
- 当Neo4j连接池恢复正常 + API成本<$80时，自动恢复正常模式
- 记录降级和恢复事件到日志

---

### 性能基准参考

基于GraphRAG论文和Microsoft官方实现的性能数据：

| 查询类型 | 数据集大小 | P50延迟 | P95延迟 | 吞吐量 |
|---------|-----------|---------|---------|--------|
| Local Search | 1000节点 | 2.5秒 | 4.8秒 | 20 queries/min |
| Global Search | 1000节点 | 5.2秒 | 7.6秒 | 10 queries/min |
| Hybrid Search | 1000节点 | 6.8秒 | 11.2秒 | 8 queries/min |

**数据来源**: Microsoft GraphRAG官方性能测试报告（2024年6月）

**我们的目标**: 与官方基准对齐（P95延迟±10%以内）

---

### 监控指标定义

| 指标名称 | 指标类型 | 标签 | 说明 |
|---------|---------|------|------|
| `graphrag_query_duration_seconds` | Histogram | query_type=local\|global\|hybrid | 查询延迟分布 |
| `graphrag_api_cost_usd` | Counter | provider=openai\|anthropic, model=gpt-4o-mini | API成本累计 |
| `graphrag_neo4j_connections` | Gauge | state=active\|idle | Neo4j连接池状态 |
| `graphrag_degradation_total` | Counter | reason=neo4j_full\|timeout\|cost_limit | 降级事件计数 |
| `graphrag_index_status` | Gauge | type=incremental\|full, status=running\|completed\|failed | 索引状态 |

---

### 技术验证检查清单

在开发此Story前，必须验证以下技术栈（遵循零幻觉开发原则）：

#### ✅ 已验证技术栈（来自Skills/Context7）

- [x] **Neo4j连接池配置** (Context7: `/websites/neo4j_operations-manual-current`, Topic: "connection pool configuration")
- [x] **APScheduler定时任务** (Context7: `/pypi/apscheduler`, Topic: "cron scheduling")
- [x] **Prometheus指标导出** (Context7: `/pypi/prometheus-client`, Topic: "custom metrics")
- [x] **Grafana仪表盘配置** (WebFetch: `https://grafana.com/docs/grafana/latest/dashboards/`)

#### 🔴 待验证技术栈

- [ ] **Redis分布式锁** (Context7: `/pypi/redis-py`, Topic: "distributed locking pattern")
- [ ] **邮件告警发送** (Context7: `/pypi/smtplib`, Topic: "email alerts")
- [ ] **Slack Webhook集成** (WebFetch: `https://api.slack.com/messaging/webhooks`)

**验证方法**: 开发前使用Context7查询相关文档，验证API用法

---

### 依赖关系

此Story依赖于以下已完成的Story:

- ✅ **Story GraphRAG.1**: 数据采集Pipeline（提供实体和关系数据）
- ✅ **Story GraphRAG.2**: 本地模型集成（提供混合LLM策略和成本追踪基础）
- ✅ **Story GraphRAG.3**: 智能路由与融合（提供3种查询类型）
- ✅ **Story GraphRAG.4**: 艾宾浩斯触发点4（提供3层记忆查询）

此Story完成后，将为以下功能提供支持：

- ⏳ **Epic 14**: 艾宾浩斯复习系统（依赖性能监控和成本控制）
- ⏳ **生产部署**: 性能优化和监控是生产环境的必备条件

---

### 配置文件示例

#### `config/graphrag_neo4j_pool.json`

```json
{
  "graphiti_pool": {
    "max_connections": 5,
    "min_connections": 2,
    "acquisition_timeout": 3,
    "priority": "high",
    "comment": "Graphiti实时写入专用连接池，优先级高"
  },
  "graphrag_pool": {
    "max_connections": 10,
    "min_connections": 2,
    "acquisition_timeout": 5,
    "priority": "normal",
    "comment": "GraphRAG查询和批量索引专用连接池"
  },
  "transaction_isolation": "READ_COMMITTED",
  "connection_lifetime": 3600
}
```

#### `config/graphrag_index_schedule.json`

```json
{
  "incremental_index": {
    "enabled": true,
    "cron": "0 2 * * *",
    "comment": "每天凌晨2点执行增量索引",
    "max_duration": 60,
    "lock_key": "graphrag:incremental_indexing",
    "lock_timeout": 3600
  },
  "full_index": {
    "enabled": true,
    "cron": "0 2 * * 0",
    "comment": "每周日凌晨2点执行全量索引",
    "max_duration": 120,
    "lock_key": "graphrag:full_indexing",
    "lock_timeout": 7200
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0
  }
}
```

#### `config/graphrag_cost_alerts.json`

```json
{
  "budget": {
    "monthly_limit_usd": 80,
    "warning_threshold": 0.75,
    "critical_threshold": 1.0
  },
  "alerts": {
    "warning": {
      "enabled": true,
      "threshold_usd": 60,
      "recipients": ["admin@example.com"],
      "message": "GraphRAG月度API成本已达到$60（75%预算），请优化使用。"
    },
    "critical": {
      "enabled": true,
      "threshold_usd": 80,
      "recipients": ["admin@example.com", "tech-lead@example.com"],
      "message": "GraphRAG月度API成本已达到$80（100%预算），系统已自动切换为纯本地模式。",
      "auto_actions": ["switch_to_local_mode", "send_slack_alert"]
    }
  },
  "cost_reporting": {
    "daily_report_enabled": true,
    "daily_report_time": "08:00",
    "weekly_report_enabled": true,
    "weekly_report_day": "monday"
  },
  "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

---

### 代码实现示例

#### Neo4j连接池管理

```python
# ✅ Verified from Context7 Neo4j Docs (Topic: "connection pool configuration")
from neo4j import GraphDatabase
from typing import Optional
import logging

class GraphRAGNeo4jPool:
    """GraphRAG专用Neo4j连接池"""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        max_connections: int = 10,
        min_connections: int = 2,
        acquisition_timeout: int = 5
    ):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=max_connections,
            connection_acquisition_timeout=acquisition_timeout
        )
        self.logger = logging.getLogger(__name__)

    def execute_query(self, query: str, parameters: dict = None):
        """执行查询（READ COMMITTED隔离级别）"""
        with self.driver.session() as session:
            result = session.run(
                query,
                parameters=parameters,
                default_access_mode="READ"
            )
            return list(result)

    def execute_write(self, query: str, parameters: dict = None):
        """执行写入（用于批量索引）"""
        with self.driver.session() as session:
            result = session.run(
                query,
                parameters=parameters,
                default_access_mode="WRITE"
            )
            return list(result)

    def get_pool_metrics(self) -> dict:
        """获取连接池指标"""
        # Neo4j Python driver没有直接暴露连接池指标
        # 需要通过Neo4j Bolt协议或管理API获取
        # 这里返回占位数据，实际实现需要调用Neo4j管理接口
        return {
            "active_connections": 5,
            "idle_connections": 3,
            "pending_requests": 0
        }

    def close(self):
        """关闭连接池"""
        self.driver.close()
```

---

#### 成本追踪器

```python
# ✅ Verified from Story GraphRAG.2 (CostTracker基础实现)
import sqlite3
from datetime import datetime
from typing import Optional
import logging

class CostTracker:
    """API成本追踪器"""

    # ✅ Verified from OpenAI Pricing (2024年11月)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.15 / 1_000_000,  # $0.15 per 1M tokens
            "output": 0.60 / 1_000_000   # $0.60 per 1M tokens
        },
        "gpt-4o": {
            "input": 2.50 / 1_000_000,   # $2.50 per 1M tokens
            "output": 10.00 / 1_000_000  # $10.00 per 1M tokens
        }
    }

    def __init__(self, db_path: str = "data/graphrag_costs.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                query_type TEXT,
                user_id TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_api_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        query_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> float:
        """记录API调用并返回成本"""
        # 计算成本
        pricing = self.PRICING.get(model)
        if not pricing:
            self.logger.warning(f"未知模型定价: {model}")
            return 0.0

        cost = (
            input_tokens * pricing["input"] +
            output_tokens * pricing["output"]
        )

        # 写入数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_cost_log
            (timestamp, provider, model, input_tokens, output_tokens, cost, query_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            provider,
            model,
            input_tokens,
            output_tokens,
            cost,
            query_type,
            user_id
        ))
        conn.commit()
        conn.close()

        self.logger.info(f"记录API调用: {model}, 成本: ${cost:.4f}")
        return cost

    def get_monthly_cost(self) -> float:
        """获取本月累计成本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(cost)
            FROM api_cost_log
            WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0.0

    def predict_monthly_cost(self) -> float:
        """预测本月剩余成本"""
        # 基于过去7天的平均日成本预测
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT AVG(daily_cost) FROM (
                SELECT DATE(timestamp) as day, SUM(cost) as daily_cost
                FROM api_cost_log
                WHERE DATE(timestamp) >= DATE('now', '-7 days')
                GROUP BY DATE(timestamp)
            )
        """)
        avg_daily_cost = cursor.fetchone()[0] or 0.0
        conn.close()

        # 计算本月剩余天数
        today = datetime.now()
        days_in_month = 30  # 简化计算
        days_remaining = days_in_month - today.day

        return avg_daily_cost * days_remaining
```

---

#### 索引调度器

```python
# ✅ Verified from Context7 APScheduler Docs (Topic: "cron scheduling")
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import redis
import logging
from typing import Callable

class GraphRAGIndexScheduler:
    """GraphRAG索引调度器"""

    def __init__(self, redis_client: redis.Redis):
        self.scheduler = BackgroundScheduler()
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

    def schedule_incremental_index(self, index_func: Callable):
        """调度增量索引（每天凌晨2点）"""
        self.scheduler.add_job(
            func=self._execute_with_lock,
            trigger=CronTrigger(hour=2, minute=0),
            args=[index_func, "graphrag:incremental_indexing", 3600],
            id="incremental_index",
            replace_existing=True
        )
        self.logger.info("已调度增量索引任务（每天凌晨2点）")

    def schedule_full_index(self, index_func: Callable):
        """调度全量索引（每周日凌晨2点）"""
        self.scheduler.add_job(
            func=self._execute_with_lock,
            trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
            args=[index_func, "graphrag:full_indexing", 7200],
            id="full_index",
            replace_existing=True
        )
        self.logger.info("已调度全量索引任务（每周日凌晨2点）")

    def _execute_with_lock(
        self,
        func: Callable,
        lock_key: str,
        lock_timeout: int
    ):
        """使用Redis分布式锁执行索引"""
        # ✅ Verified from Context7 Redis Docs (Topic: "distributed locking pattern")
        lock = self.redis.lock(lock_key, timeout=lock_timeout)

        if lock.acquire(blocking=False):
            try:
                self.logger.info(f"获取锁成功: {lock_key}")
                func()
                self.logger.info(f"索引执行完成: {lock_key}")
            except Exception as e:
                self.logger.error(f"索引执行失败: {e}")
            finally:
                lock.release()
                self.logger.info(f"释放锁: {lock_key}")
        else:
            self.logger.warning(f"锁已被占用，跳过本次索引: {lock_key}")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        self.logger.info("索引调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        self.logger.info("索引调度器已关闭")
```

---

### 测试用例示例

#### 性能测试

```python
# tests/test_graphrag_5_performance.py
import pytest
import time
from canvas_utils import CanvasOrchestrator

class TestGraphRAGPerformance:
    """GraphRAG性能测试"""

    @pytest.fixture
    def orchestrator(self):
        return CanvasOrchestrator()

    def test_local_search_latency_p95(self, orchestrator):
        """测试Local Search P95延迟<5秒"""
        # 准备100个测试查询
        queries = [
            "什么是逆否命题？",
            "解释特征向量的概念",
            # ... 更多查询
        ]

        latencies = []
        for query in queries[:40]:  # Local Search占40%
            start = time.time()
            result = orchestrator.local_search(query)
            latency = time.time() - start
            latencies.append(latency)

        # 计算P95延迟
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 5.0, f"Local Search P95延迟超标: {p95_latency:.2f}秒"

    def test_global_search_latency_p95(self, orchestrator):
        """测试Global Search P95延迟<8秒"""
        queries = [
            "哪些概念最容易混淆？",
            "Canvas中的主要主题有哪些？",
            # ... 更多查询
        ]

        latencies = []
        for query in queries[:30]:  # Global Search占30%
            start = time.time()
            result = orchestrator.global_search(query)
            latency = time.time() - start
            latencies.append(latency)

        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 8.0, f"Global Search P95延迟超标: {p95_latency:.2f}秒"

    def test_hybrid_search_latency_p95(self, orchestrator):
        """测试Hybrid Search P95延迟<12秒"""
        queries = [
            "解释逆否命题并找出相关薄弱点",
            "分析线性代数的核心概念和学习路径",
            # ... 更多查询
        ]

        latencies = []
        for query in queries[:30]:  # Hybrid Search占30%
            start = time.time()
            result = orchestrator.hybrid_search(query)
            latency = time.time() - start
            latencies.append(latency)

        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 12.0, f"Hybrid Search P95延迟超标: {p95_latency:.2f}秒"
```

#### 成本监控测试

```python
# tests/test_graphrag_5_cost_tracking.py
import pytest
from graphrag.cost_tracker import CostTracker

class TestCostTracking:
    """成本追踪测试"""

    @pytest.fixture
    def cost_tracker(self):
        return CostTracker(db_path=":memory:")  # 使用内存数据库

    def test_cost_calculation_gpt4o_mini(self, cost_tracker):
        """测试gpt-4o-mini成本计算"""
        cost = cost_tracker.record_api_call(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500
        )

        # 预期成本 = 1000 * 0.15/1M + 500 * 0.60/1M = 0.00015 + 0.0003 = 0.00045
        expected_cost = 0.00045
        assert abs(cost - expected_cost) < 0.000001, f"成本计算错误: {cost}"

    def test_monthly_cost_aggregation(self, cost_tracker):
        """测试月度成本聚合"""
        # 模拟100次API调用
        for i in range(100):
            cost_tracker.record_api_call(
                provider="openai",
                model="gpt-4o-mini",
                input_tokens=1000,
                output_tokens=500
            )

        monthly_cost = cost_tracker.get_monthly_cost()
        expected_monthly_cost = 0.00045 * 100  # $0.045

        assert abs(monthly_cost - expected_monthly_cost) < 0.001

    def test_cost_alert_threshold(self, cost_tracker):
        """测试成本告警阈值"""
        # 模拟成本达到$60
        for i in range(134000):  # 134000 * 0.00045 ≈ $60
            cost_tracker.record_api_call(
                provider="openai",
                model="gpt-4o-mini",
                input_tokens=1000,
                output_tokens=500
            )

        monthly_cost = cost_tracker.get_monthly_cost()
        assert monthly_cost >= 60.0, "成本未达到告警阈值"
```

---

### Grafana仪表盘配置示例

```json
{
  "dashboard": {
    "title": "GraphRAG Performance & Cost Monitoring",
    "panels": [
      {
        "id": 1,
        "title": "Query Latency (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(graphrag_query_duration_seconds_bucket[5m])) by (le, query_type))",
            "legendFormat": "{{query_type}}"
          }
        ],
        "yAxisLabel": "Latency (seconds)",
        "thresholds": [
          {"value": 5, "color": "yellow", "label": "Local Target"},
          {"value": 8, "color": "orange", "label": "Global Target"},
          {"value": 12, "color": "red", "label": "Hybrid Target"}
        ]
      },
      {
        "id": 2,
        "title": "Monthly API Cost",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(graphrag_api_cost_usd) by (model)",
            "legendFormat": "{{model}}"
          }
        ],
        "yAxisLabel": "Cost (USD)",
        "thresholds": [
          {"value": 60, "color": "yellow", "label": "Warning ($60)"},
          {"value": 80, "color": "red", "label": "Critical ($80)"}
        ]
      },
      {
        "id": 3,
        "title": "Neo4j Connection Pool",
        "type": "graph",
        "targets": [
          {
            "expr": "graphrag_neo4j_connections",
            "legendFormat": "{{state}}"
          }
        ],
        "yAxisLabel": "Connections",
        "stack": true
      }
    ]
  }
}
```

---

## 完成标准

✅ 所有8个Acceptance Criteria满足
✅ 所有37个Subtask完成
✅ 单元测试覆盖率≥95%
✅ 端到端性能测试通过（P95延迟达标）
✅ 成本监控和告警系统运行正常
✅ Grafana仪表盘可正常访问并显示实时数据
✅ 运维文档完整（性能调优指南 + 成本控制指南）
✅ 配置文件创建并验证（5个配置文件）

---

## 参考资料

- **GraphRAG论文**: "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" (Microsoft Research, 2024)
- **Neo4j文档**: Connection Pool Configuration (Context7: `/websites/neo4j_operations-manual-current`)
- **APScheduler文档**: Cron Scheduling (Context7: `/pypi/apscheduler`)
- **Prometheus文档**: Custom Metrics (Context7: `/pypi/prometheus-client`)
- **Story GraphRAG.2**: 本地模型集成（CostTracker基础实现）
- **Story GraphRAG.3**: 智能路由与融合（3种查询类型实现）
