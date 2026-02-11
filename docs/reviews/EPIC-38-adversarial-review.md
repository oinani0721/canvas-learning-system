# 对抗性验证报告: EPIC-38 Infrastructure Reliability Fixes

> **审查日期**: 2026-02-08
> **审查类型**: Adversarial Review (General)
> **审查结论**: 🔴 不通过 — 3 个阻塞级问题

---

## 发现汇总

| # | 严重程度 | 问题描述 | 位置 |
|---|---------|---------|------|
| 1 | 🔴 阻塞 | 文档严重过时——多数 Story 已实现但文档仍描述"待修复" | 全局 |
| 2 | 🔴 阻塞 | AC 之间逻辑矛盾 (AC-1 vs AC-4) | 38.3 |
| 3 | 🔴 阻塞 | 架构空洞：降级→恢复的 JSON→Neo4j 同步机制不存在 | 38.7 AC-5 |
| 4 | 🟡 重要 | 缺乏可量化的可靠性目标 (SLA/SLO/RTO/RPO) | 全局 |
| 5 | 🟡 重要 | JSON fallback 并发安全未定义 | 38.5, 38.6 |
| 6 | 🟡 重要 | 语义耦合：`ENABLE_GRAPHITI_JSON_DUAL_WRITE` 被过度复用 | 38.5 AC-1 |
| 7 | 🟡 重要 | pending queue 持久化循环依赖 | 38.1 AC-3 |
| 8 | 🟡 重要 | 前后端混合在基础设施 EPIC 中 | 38.3 AC-2 |
| 9 | 🟢 建议 | JSON 文件无容量限制和轮转策略 | 38.5, 38.6 |
| 10 | 🟢 建议 | 数据冲突解决策略未定义 | 38.7 AC-5 |
| 11 | 🟢 建议 | FR 编号是 Story 的虚假别名 | Requirements Covered |
| 12 | 🟢 建议 | 缺乏监控告警，仅依赖日志 | 全局 |

---

## 详细发现

### 1. 🔴 文档严重过时——多数 Story 已实现但文档仍描述"待修复"

代码现实检查表明，EPIC-38 的 6/7 个 Story 的核心功能**已经在代码中实现**：

| Story | 文档声称的"当前行为" | 代码实际状态 |
|-------|-------------------|------------|
| 38.1 | Canvas CRUD 无 LanceDB 触发 | `lancedb_index_service.py` 已存在，`ENABLE_LANCEDB_AUTO_INDEX` 配置已定义 |
| 38.2 | `self._episodes` 总是空启动 | `_recover_episodes_from_neo4j()` 已实现 (memory_service.py:L166)，lazy recovery 已有 (L526-527) |
| 38.3 | 无 FSRS 卡片时返回 `{found: False}` | 自动创建默认 FSRS 卡片逻辑已实现 (review_service.py:L1736-1760) |
| 38.4 | `default=False` | 已改为 `default=True` (config.py:L409) |
| 38.5 | `if _memory_client is None: return` 静默跳过 | `_fallback_file_path` 已定义 (canvas_service.py:L87) |
| 38.6 | `timeout=2.0` 太短 | `MEMORY_WRITE_TIMEOUT=15.0` + `_record_failed_write()` 已实现 (agent_service.py:L45-86) |

文档没有任何状态标记区分"计划中"和"已完成"。一个开发者读到这份文档会以为这些都是**待做工作**，浪费时间重复实现或产生困惑。

**建议**: 将 EPIC-38 标记为已实现，或在每个 Story 头部添加 `Status: ✅ Implemented` 标签。

### 2. 🔴 Story 38.3 AC-1 与 AC-4 逻辑矛盾

- AC-1 定义：无 FSRS 卡片时返回 `{found: false, reason: "no_card_created"}`
- AC-4 定义：无 FSRS 卡片时**自动创建**默认卡片，后续返回 `{found: true}`

如果 AC-4 总是自动创建卡片，那 AC-1 的 `"no_card_created"` 分支**永远不会被触发**（除非自动创建本身失败，但这个失败路径不在 AC-1 的定义中）。这两个 AC 相互矛盾，无法同时测试。

**建议**: AC-1 应修改为 "if auto-creation fails, return `{found: false, reason: 'auto_creation_failed'}`"，与 AC-4 形成清晰的成功/失败决策树。

### 3. 🔴 架构空洞：JSON fallback → Neo4j 同步机制不存在

Story 38.7 AC-5 写道：*"JSON fallback events are eventually synced to Neo4j (if sync mechanism exists)"*

这个 "(if sync mechanism exists)" 暴露了一个致命架构空洞：

- Stories 38.4、38.5、38.6 都将数据写入 JSON fallback 文件
- 但**没有任何 Story 定义了从 JSON fallback 同步回 Neo4j 的机制**
- 降级期间的数据**永久留在 JSON 文件中，永远不会回到知识图谱**
- EPIC 的目标是"可靠性"，但降级数据的最终一致性没有保障

**建议**: 增加一个 Story 38.8 定义 JSON→Neo4j 同步机制（启动时回放、定时任务、或手动触发端点），或明确声明 fallback 数据为只读存档，不回写。

### 4. 🟡 缺乏可量化的可靠性目标

一个标题为 "Infrastructure Reliability Fixes" 的 EPIC，没有定义任何可靠性指标：
- 没有 SLA/SLO（如数据持久化率 99.9%）
- 没有 RTO（Recovery Time Objective）
- 没有 RPO（Recovery Point Objective）
- 没有性能基线（降级模式下延迟上限）

没有可量化目标，就无法判断"修复"是否成功。

### 5. 🟡 JSON fallback 文件并发安全未定义

多个 Story 写入 JSON 文件（`canvas_events_fallback.json`、`failed_writes.jsonl`），但文档**没有提到任何并发控制**：
- 多个异步任务同时写 `failed_writes.jsonl` 会不会数据损坏？
- 多个 Canvas CRUD 同时触发 fallback 写入会不会 race condition？
- `agent_service.py` 用了 `threading.Lock()`（L52），但 `canvas_service.py` 的 fallback 是否也有？

### 6. 🟡 语义耦合：`ENABLE_GRAPHITI_JSON_DUAL_WRITE` 被过度复用

Story 38.5 复用 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 标志来控制 Canvas CRUD 的 JSON 降级。但这个标志的原始语义是"Graphiti 学习事件双写"（Story 36.9），不是"Canvas 事件降级存储"。一个标志控制两个不同功能域的行为，导致无法独立控制。

**建议**: 引入独立的 `ENABLE_CANVAS_EVENT_FALLBACK` 配置项。

### 7. 🟡 Story 38.1 AC-3 的 pending queue 持久化是循环依赖

AC-3 要求"应用重启后重试 pending index updates"。但 pending queue 持久化到哪里？
- 如果存内存 → 重启后丢失，AC-3 永远无法满足
- 如果存 Neo4j → Neo4j 不可用可能正是 index 失败的原因
- 如果存 JSON 文件 → 又多一个 fallback 文件，但文档没有指定路径/格式

### 8. 🟡 Story 38.3 AC-2 将前端 UI 变更混入基础设施 EPIC

AC-2 要求前端 UI 显示 "FSRS data unavailable" 指示器，引用了 TypeScript 文件（`PriorityCalculatorService.ts`、`TodayReviewListService.ts`）。这是 UX 层面的变更，不属于"基础设施可靠性"范畴。

**建议**: 拆分到独立 Story 或引用 EPIC-32（Ebbinghaus Review System Enhancement）。

### 9. 🟢 JSON 文件无容量限制和轮转策略

`failed_writes.jsonl` 和 `canvas_events_fallback.json` 没有定义：
- 最大文件大小
- 日志轮转策略（按大小或按时间）
- 清理机制

在长期运行的系统中，这些文件会无限增长，存在磁盘空间风险。

### 10. 🟢 降级恢复时数据冲突解决策略未定义

Story 38.7 AC-5 描述 Neo4j 恢复后 replay failed writes，但没有定义：
- 如果 Neo4j 中已有相同 concept_id 的更新版数据，replay 时谁赢？
- Last-write-wins？还是版本号比较？
- 重复 replay 的幂等性保证？

### 11. 🟢 FR 编号是 Story 编号的虚假映射

Requirements Covered 表中 FR-38.1 ↔ Story 38.1 完全一一对应。这不是真正的需求追踪——FR 只是 Story 的别名，没有提供独立的需求定义。

### 12. 🟢 仅依赖 WARNING 日志，缺乏可观测性

所有 Story 的失败处理都只写 WARNING 日志。没有：
- Prometheus/Grafana 指标
- 告警阈值（如 5 分钟内失败超过 10 次）
- Story 38.6 的 "Consider adding a metric counter" 只是一个"考虑"，不是 AC

---

## 验证结论

**🔴 不通过** — 存在 3 个阻塞级问题，必须修复后重新验证：

1. **文档过时**: 必须添加 Story 实现状态标记，或将整个 EPIC 标记为已完成
2. **AC 逻辑矛盾**: Story 38.3 的 AC-1 和 AC-4 必须协调，定义清晰的决策树
3. **架构空洞**: 必须增加 JSON fallback → Neo4j 同步机制的 Story，或明确声明 fallback 数据不回写

## 验证深度自检
- 审查了 7 个 Story + 1 个全局结构
- 交叉验证了 6 个代码引用（config.py, memory_service.py, review_service.py, agent_service.py, canvas_service.py, lancedb_index_service.py）
- 提出了 12 个质疑（3 阻塞 + 5 重要 + 4 建议）
