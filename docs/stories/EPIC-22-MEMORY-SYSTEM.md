> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](../epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic 22: 记忆系统验证与启用 - 棕地增强

**优先级**: P1
**关联Bug**: Bug 3 (编码问题)
**创建日期**: 2026-01-15
**状态**: 待实施

---

## Epic标题
**记忆系统验证与启用 - Brownfield Enhancement**

## Epic目标
验证Canvas Learning System现有记忆系统（Epic 12.A）实现的正确性，修复数据编码问题，并确保学习记忆能够正确持久化和检索，使Obsidian Canvas的记忆功能真正可用。

---

## Epic描述

### 现有系统上下文
- **当前相关功能**: Epic 12.A已实现记忆注入(12.A.4)和事件记录(12.A.5)，30个单元测试通过
- **技术栈**: FastAPI + JSON存储(Neo4j fallback) + LearningMemoryClient
- **集成点**: `agent_service.py:1020-1086`, `memory_service.py`, `neo4j_client.py`

### 增强详情
**要更改的内容**:
1. 修复`neo4j_memory.json`中的编码乱码问题
2. 确保`learning_memories.json`正确写入
3. 验证端到端学习事件流程

**集成方式**: 修复现有实现中的Bug，不改变架构

**成功标准**:
- 4个Memory API端点全部返回正确数据
- 学习事件能够持久化到JSON文件
- Agent调用时能够注入历史学习记录

---

## Stories

| Story | 描述 | 优先级 | 关键文件 |
|-------|------|--------|----------|
| **22.1** | **Neo4j数据清理** - 清理`neo4j_memory.json`中的编码乱码数据，重置为干净状态 | P0 | `backend/data/neo4j_memory.json` |
| **22.2** | **Memory API端点验证** - 验证POST/GET episodes, review-suggestions, concept history四个端点正确工作 | P0 | `backend/app/api/v1/endpoints/memory.py` |
| **22.3** | **学习事件持久化修复** - 确保`record_learning_event()`正确写入`learning_memories.json` | P1 | `backend/app/services/memory_service.py` |

---

## 关键文件清单

| 文件 | 用途 | 行数 |
|------|------|------|
| `backend/app/services/memory_service.py` | 核心记忆服务 | 380+ |
| `backend/app/clients/neo4j_client.py` | JSON fallback存储 | 498 |
| `backend/app/clients/graphiti_client.py` | LearningMemoryClient | 754 |
| `backend/app/services/agent_service.py:1020-1086` | 记忆注入实现 | - |
| `backend/app/api/v1/endpoints/memory.py` | API端点 | 289 |

### 数据文件

| 文件 | 当前状态 | 预期状态 |
|------|---------|---------|
| `backend/data/neo4j_memory.json` | 有数据但用户ID乱码 | 需要清理/修复 |
| `backend/data/learning_memories.json` | 空 | 验证后应有数据 |

---

## 兼容性要求

- [x] 现有API保持不变（仅修复Bug）
- [x] 数据库Schema向后兼容（JSON结构不变）
- [x] UI变更遵循现有模式（无UI变更）
- [x] 性能影响最小（仅数据清理）

---

## 风险缓解

| 风险类型 | 描述 | 缓解措施 |
|----------|------|----------|
| **主要风险** | 清理数据可能丢失有效学习记录 | 先备份`backend/data/*.json`文件 |
| **回滚计划** | 从备份恢复JSON文件 | - |

---

## 完成定义

- [ ] 所有Stories完成，验收标准满足
- [ ] 现有功能通过测试验证
- [ ] 集成点正确工作
- [ ] 文档更新完成
- [ ] 无现有功能回归

---

## 验证检查清单

| Phase | Step | 测试项 | 状态 |
|-------|------|--------|------|
| 1 | 1.1 | 后端启动 | [ ] |
| 1 | 1.2 | 健康检查 | [ ] |
| 2 | 2.1 | POST episodes | [ ] |
| 2 | 2.2 | GET episodes | [ ] |
| 2 | 2.3 | GET review-suggestions | [ ] |
| 2 | 2.4 | GET concept history | [ ] |
| 3 | 3.1 | 记忆服务单元测试 | [ ] |
| 3 | 3.2 | Agent记忆注入测试 | [ ] |
| 4 | 4.1 | E2E学习流程 | [ ] |
| 4 | 4.2 | 记忆上下文注入 | [ ] |

---

## 发现的问题（深度调研结果）

1. **P1: neo4j_memory.json编码问题** - 用户ID存储为乱码
2. **P2: learning_memories.json未被写入** - 记忆从未持久化
3. **P3: memory_service.start_monitoring()被注释** - 监控未启动

---

## Story Manager交接

> "请为此棕地Epic开发详细的用户故事。关键考虑事项:
>
> - 这是对运行FastAPI + JSON存储的现有系统的增强
> - 集成点: `memory_service.py`, `neo4j_client.py`, `graphiti_client.py`
> - 需要遵循的现有模式: 500ms超时 + 30秒缓存 (12.A.4实现)
> - 关键兼容性要求: 不改变API接口，仅修复数据问题
> - 每个Story必须包含验证现有功能保持完整的内容
>
> Epic应在交付记忆系统验证与启用的同时保持系统完整性。"

---

## 备注

- 此Epic**不需要真正的Neo4j数据库** - 系统使用JSON fallback
- 验证完成后，可以考虑连接真正的Neo4j（未来增强）
- 编码问题可能与Epic 12.I相关（日志编码UTF-8配置）
