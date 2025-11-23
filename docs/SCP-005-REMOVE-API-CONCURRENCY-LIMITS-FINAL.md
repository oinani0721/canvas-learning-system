# SCP-005: 移除API并发限制后的Epic 10调整（最终版 - 一步到位实施）

**状态**: ✅ 已批准（用户要求一步到位）
**创建日期**: 2025-11-14
**批准日期**: 2025-11-14
**影响范围**: Epic 10, Epic 11, Epic 12, PRD Section 3.4
**实施方式**: **一步到位** （直接到目标值100/50/20，不采用渐进式）

---

## 1. 变更触发和背景

### 1.1 触发事件

**关键信息变化**: 用户确认"迁移到LangGraph后，Agent API调用将不再有并发限制"

**具体含义**:
- 当前假设: GLM-4.6 Max API限制为20并发
- 实际情况: 迁移后API并发无限制
- 成本影响: 并发不影响成本
- 实施时间: 迁移到LangGraph后才能移除

### 1.2 当前问题

**Epic 10并发模型的错误假设**:

| 组件 | 错误假设 | 正确情况 | 影响 |
|------|---------|---------|------|
| Agent级并发限制 | GLM-4.6 Max API限制20并发 | 迁移后无API限制 | 保守限制导致性能未充分利用 |
| 节点级并发限制 | 基于API限制保守设置12 | 可大幅提升 | 批处理性能受限 |
| 任务级并发限制 | 基于复杂度设置5 | 可提升到20 | 复杂工作流效率低 |

**性能损失**:
- 100个节点批处理: 当前需要120秒，理论上可在25秒内完成（4.8倍性能损失）
- 单节点多Agent处理: 限制在20个Agent，理论上可达100个（5倍性能损失）

---

## 2. Epic影响评估

### 2.1 Epic 10: 智能并行处理系统

**影响程度**: 🔴 **重大影响** - 核心架构假设变更

**需要修改的内容**:

#### 2.1.1 并发限制矩阵

**当前值**（基于错误假设）:
```yaml
Agent级: 20   # ❌ 基于GLM-4.6 Max API限制
节点级: 12   # ❌ 基于API限制保守设置
任务级: 5    # ⚠️ 可提升
系统最大: 100
```

**新值**（一步到位，移除API限制）:
```yaml
Agent级: 100   # ✅ 基于系统资源限制（内存、CPU）
节点级: 50    # ✅ 基于用户体验 + CPU资源
任务级: 20    # ✅ 基于依赖关系复杂度
系统最大: 500  # ✅ ResourceAwareScheduler动态保护
```

#### 2.1.2 受影响的Story

| Story | 当前值 | 新值（一步到位） | 修改内容 |
|-------|--------|----------------|---------|
| Story 10.1 | `Semaphore(20)` | `Semaphore(100)` | ReviewBoardAgentSelector并发限制 |
| Story 10.2 | `max_concurrent=12` | `max_concurrent=50` | IntelligentParallelScheduler并发限制 |
| **Story 10.15** (新增) | N/A | ResourceAwareScheduler | 资源感知调度器实现 |

#### 2.1.3 架构文档更新

**文件**: `docs/architecture/epic10-concurrency-definition.md`

**关键变更**:
- Line 38: "基于GLM-4.6 Max API限制" → "基于系统资源限制（内存、CPU）"
- Line 24: `Semaphore(20)` → `Semaphore(100)`
- Line 69: `Semaphore(12)` → `Semaphore(50)`
- Line 142: `max_concurrent_tasks = 5` → `max_concurrent_tasks = 20`
- Line 202-205: 并发限制矩阵表格更新
- Line 476+: **新增** ResourceAwareScheduler完整实现（200+行代码和设计文档）

**状态**: ✅ 已完成更新

---

### 2.2 Epic 11: FastAPI后端实现

**影响程度**: 🟡 **中等影响** - 需要调整API设计

**需要修改的内容**:

#### 2.2.1 API端点并发配置

| 端点 | 当前配置 | 新配置 | 说明 |
|------|---------|--------|------|
| `/api/canvas/parallel-process` | `max_concurrent: 12` | `max_concurrent: 50` | 节点级并发 |
| `/api/agents/execute-multiple` | `max_agents: 20` | `max_agents: 100` | Agent级并发 |
| `/api/health` (新增) | N/A | 返回ResourceAwareScheduler状态 | 资源监控 |

#### 2.2.2 依赖库

**新增依赖**:
```txt
psutil>=5.9.0  # 系统资源监控
```

---

### 2.3 Epic 12: LangGraph集成

**影响程度**: 🟢 **轻微影响** - 主要是性能优势保留验证

**需要修改的内容**:

#### 2.3.1 LangGraph Supervisor配置

| 配置项 | 当前值 | 新值 | 说明 |
|-------|--------|------|------|
| `max_parallel_agents` | 20 | 100 | Supervisor并发调度能力 |
| `checkpoint_retention` | 100 | 500 | 检查点保留数量 |

#### 2.3.2 性能验证测试

**测试场景更新**:
- 100节点批处理: 120秒 → **目标25秒**（一步到位）
- 单节点深度分析: 8秒 → **目标2秒**（一步到位）
- 并发Agent数: 20 → **100**（一步到位）

---

## 3. 新并发限制矩阵（一步到位）

### 3.1 完整矩阵

| 并发层级 | 迁移前限制 | 迁移后限制（一步到位） | 控制对象 | 配置方式 | 说明 |
|---------|-----------|---------------------|----------|----------|------|
| **Agent级** | 20 | **100** | 单节点的Agent数量 | 系统资源限制 | 基于内存（100×200MB=20GB）、CPU |
| **节点级** | 12 | **50** | 并行处理的节点组 | --max参数 | 基于用户体验 + CPU资源 |
| **任务级** | 5 | **20** | 有依赖的任务组 | 调度器内置 | 基于依赖关系复杂度 |
| **系统最大** | 100 | **500** | 总并发Agent实例 | ResourceAwareScheduler | 资源感知动态调整 |

### 3.2 性能提升预期（一步到位）

| 场景 | 迁移前性能 | 迁移后性能 | 性能提升 |
|------|-----------|----------|---------|
| **轻量任务**（CPU<30%） | 20 agents | **100 agents** | **5倍** ⚡ |
| **标准任务**（CPU 50-70%） | 20 agents | **60 agents** | **3倍** ⚡ |
| **重度任务**（CPU>80%） | 20 agents | **10-20 agents** | **持平（保护）** ✅ |
| **100节点批处理** | 12组 × 3agent = 36并发 | **50组 × 5agent = 250并发** | **7倍** ⚡ |

### 3.3 资源保护机制

**引入ResourceAwareScheduler** (Story 10.15):

```python
class ResourceAwareScheduler:
    """资源感知调度器 - 移除API限制后的核心保护机制"""

    def __init__(
        self,
        max_memory_percent: float = 80.0,
        max_cpu_percent: float = 80.0,
        initial_agent_concurrency: int = 100,  # 一步到位
        initial_node_concurrency: int = 50,    # 一步到位
        initial_task_concurrency: int = 20,    # 一步到位
        min_concurrency: int = 10
    ):
        # 初始化配置

    async def _adjust_concurrency_by_resources(self):
        """基于实时资源动态调整并发数"""
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 紧急降低（Memory > 90% OR CPU > 90%）
        if memory_percent > 90 or cpu_percent > 90:
            self.agent_concurrency = self.min_concurrency  # 降到10
            logging.warning(f"Emergency reduction: Memory={memory_percent}%, CPU={cpu_percent}%")

        # 降低并发（Memory > 80% OR CPU > 80%）
        elif memory_percent > 80 or cpu_percent > 80:
            self.agent_concurrency = max(self.min_concurrency, int(self.agent_concurrency * 0.7))

        # 提升并发（Memory < 50% AND CPU < 60%）
        elif memory_percent < 50 and cpu_percent < 60:
            self.agent_concurrency = min(100, int(self.agent_concurrency * 1.3))
```

**核心特性**:
- ✅ 实时监控系统资源（每秒检查内存、CPU）
- ✅ 动态调整并发数（× 0.7降低，× 1.3提升）
- ✅ 紧急保护机制（Memory/CPU > 90%时降到最小值10）
- ✅ 优雅退出支持（asyncio.CancelledError）

---

## 4. 故事修改清单（一步到位）

### 4.1 新增Story

#### Story 10.15: ResourceAwareScheduler实现

**文件**: `docs/stories/10.15.resource-aware-scheduler.story.md`

**状态**: ✅ 已创建

**核心AC**:
1. 资源监控: psutil监控Memory%和CPU%
2. 动态调整: 紧急降低（>90%）、降低（>80%）、提升（<50%）
3. 系统集成: ReviewBoardAgentSelector、IntelligentParallelScheduler
4. 性能验证: 轻量场景5倍提升，标准场景3倍提升，100节点7倍提升

**实施方式**: 一步到位，初始并发直接设置为100/50/20

---

### 4.2 修改Story

#### Story 10.1: ReviewBoardAgentSelector

**文件**: `docs/stories/10.1.story.md`

**修改内容**:
- Line 24: `Semaphore(20)` → `Semaphore(100)`（注释："迁移后: 一步到位"）
- Line 141: 并发执行时间 < 5秒（20个Agent） → < 3秒（100个Agent）

**状态**: ✅ 已更新

---

#### Story 10.2: IntelligentParallelScheduler

**文件**: `docs/stories/10.2.story.md`

**修改内容**:
- Line 144-148: `max_concurrent: int = 12` → `max_concurrent: int = 50`
- 添加`resource_scheduler: ResourceAwareScheduler`参数
- Line 295-298: 调度配置更新（一步到位）:
  ```yaml
  default_max_concurrent: 50  # 12 → 50
  max_concurrent_agents_per_node: 100  # 新增
  max_concurrent_tasks: 20  # 新增
  resource_aware_scheduling: true  # 新增
  ```

**状态**: ✅ 已更新

---

### 4.3 PRD修改

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`

**修改位置**:
1. **Line 1356**: FR2.1核心能力
   - 修改前: "最多12个Agent并发执行（Epic 10.2的8倍性能提升）"
   - 修改后: "最多50个节点组并行，每组最多100个Agent（相比迁移前性能提升3-7倍）"

2. **Line 1426+**: **新增** 并发限制矩阵表格（迁移后版本）
   - 完整的并发限制矩阵（100/50/20）
   - 性能提升对比表（5倍/3倍/7倍）
   - 关键变化说明

3. **Line 4202**: LangGraph性能优势
   - 修改前: "最多12个Agent同时运行，8倍性能提升完全保留"
   - 修改后: "最多50个节点组并行，性能提升3-7倍，引入ResourceAwareScheduler"

4. **Line 5955**: 测试场景
   - 修改前: "测试并发场景（最多12个Agent同时运行）"
   - 修改后: "测试高并发场景（最多50个节点组，每组最多100个Agent）"

**状态**: ✅ 已更新

---

### 4.4 架构文档修改

**文件**: `docs/architecture/epic10-concurrency-definition.md`

**修改内容**:
- ✅ Line 24: `Semaphore(20)` → `Semaphore(100)`
- ✅ Line 38-41: 删除"基于GLM-4.6 Max API限制"，改为"基于系统资源限制（内存、CPU）"
- ✅ Line 69: `Semaphore(12)` → `Semaphore(50)`
- ✅ Line 100-106: 节点级并发限制更新（12 → 50）
- ✅ Line 142: `max_concurrent_tasks = 5` → `max_concurrent_tasks = 20`
- ✅ Line 190-194: 任务级并发限制更新（5 → 20）
- ✅ Line 202-205: 并发限制矩阵表格更新
- ✅ Line 218-233: 并发计算示例更新（50组 × 5agent = 250并发）
- ✅ Line 257-295: 动态并发调整代码更新（移除API限制检查）
- ✅ Line 364-385: 监控指标更新（添加system_level）
- ✅ Line 391-411: 告警阈值更新（100/50/20/500）
- ✅ Line 419-441: 最佳实践配置更新（extreme场景100/50/20）
- ✅ **Line 476+**: **新增** ResourceAwareScheduler完整设计和实现（200+行）

**状态**: ✅ 已完成更新

---

## 5. 实施策略（一步到位）

### 5.1 实施方式

**❌ 拒绝渐进式**:
- ~~Phase 1: 20 → 30 (Week 1)~~
- ~~Phase 2: 30 → 60 (Week 2)~~
- ~~Phase 3: 60 → 100 (Week 3)~~

**✅ 采用一步到位**:
- **迁移完成后立即**: 100/50/20（用户明确要求）
- **ResourceAwareScheduler保护**: 自动降低到10（紧急情况）
- **监控和调整**: 基于实际运行数据持续优化

### 5.2 实施时间表

| 阶段 | 任务 | 时间 | 负责人 | 状态 |
|------|------|------|--------|------|
| **Phase 1** | 文档更新 | 2025-11-14 | PM | ✅ 已完成 |
| - | epic10-concurrency-definition.md | 1小时 | Architect | ✅ 已完成 |
| - | Story 10.15创建 | 2小时 | PM | ✅ 已完成 |
| - | PRD Section 3.4更新 | 1小时 | PM | ✅ 已完成 |
| - | Story 10.1/10.2更新 | 1小时 | PM | ✅ 已完成 |
| **Phase 2** | ResourceAwareScheduler实现 | 迁移后Week 1 | Dev | ⏳ 待实施 |
| - | resource_aware_scheduler.py | 1天 | Dev | ⏳ 待实施 |
| - | 单元测试 | 1天 | QA | ⏳ 待实施 |
| - | 集成测试 | 1天 | QA | ⏳ 待实施 |
| **Phase 3** | 系统集成 | 迁移后Week 2 | Dev | ⏳ 待实施 |
| - | ReviewBoardAgentSelector集成 | 0.5天 | Dev | ⏳ 待实施 |
| - | IntelligentParallelScheduler集成 | 0.5天 | Dev | ⏳ 待实施 |
| - | IntelligentParallelCommandHandler集成 | 0.5天 | Dev | ⏳ 待实施 |
| **Phase 4** | 性能验证 | 迁移后Week 3 | QA | ⏳ 待实施 |
| - | 100节点批处理测试 | 1天 | QA | ⏳ 待实施 |
| - | 压力测试（Memory > 90%） | 1天 | QA | ⏳ 待实施 |
| - | 性能报告 | 1天 | QA | ⏳ 待实施 |

**总时间**: 2周（迁移完成后）

---

## 6. 风险评估和缓解策略

### 6.1 性能风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| 系统资源过载 | 高 | 中 | ResourceAwareScheduler紧急保护（降到10） |
| 内存不足导致OOM | 极高 | 低 | Memory > 90%时紧急降低并发 |
| CPU过载影响用户体验 | 高 | 中 | CPU > 80%时降低并发 × 0.7 |
| 并发调整响应慢 | 中 | 低 | 每秒监控，100ms内完成调整 |

### 6.2 实施风险

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|--------|---------|
| ResourceAwareScheduler实现复杂 | 中 | 低 | 详细Story 10.15，完整代码示例 |
| 测试覆盖不足 | 高 | 中 | 单元测试 + 集成测试 + 压力测试 |
| 性能提升未达预期 | 中 | 低 | 性能基准测试，目标明确（3-7倍） |
| 向后兼容性问题 | 高 | 低 | 保留所有现有API，仅扩展参数 |

---

## 7. 成功标准

### 7.1 功能标准

- ✅ ResourceAwareScheduler实现完成并通过所有测试
- ✅ 与ReviewBoardAgentSelector/IntelligentParallelScheduler集成无回归
- ✅ 资源监控正常（Memory%、CPU%每秒更新）
- ✅ 动态并发调整正常（紧急降低、降低、提升三种场景）

### 7.2 性能标准

| 场景 | 目标性能 | 验证方法 |
|------|---------|---------|
| 轻量任务（CPU<30%） | **5倍** 提升（20 → 100 agents） | 性能基准测试 |
| 标准任务（CPU 50-70%） | **3倍** 提升（20 → 60 agents） | 性能基准测试 |
| 100节点批处理 | **7倍** 提升（120s → 25s） | E2E集成测试 |
| 资源过载场景 | 保护系统稳定性（降到10） | 压力测试 |

### 7.3 质量标准

- ✅ 测试覆盖率 > 90%
- ✅ 所有现有测试通过（无回归）
- ✅ 新增测试覆盖ResourceAwareScheduler所有场景
- ✅ 文档完整性100%（PRD、Architecture、Stories全部更新）

---

## 8. 交付物清单

### 8.1 文档（✅ 已完成）

- ✅ **SCP-005最终文档**（本文件）
- ✅ **epic10-concurrency-definition.md** - 完全更新（100/50/20 + ResourceAwareScheduler）
- ✅ **Story 10.15** - ResourceAwareScheduler完整实现文档
- ✅ **PRD Section 3.4** - 并发限制矩阵（迁移后版本）
- ✅ **Story 10.1** - 更新并发限制到100
- ✅ **Story 10.2** - 更新并发限制到50

### 8.2 代码（⏳ 待实施）

- ⏳ `resource_aware_scheduler.py` - ResourceAwareScheduler实现
- ⏳ `review_board_agent_selector.py` - 集成resource_scheduler参数
- ⏳ `intelligent_parallel_scheduler.py` - 集成resource_scheduler参数
- ⏳ `intelligent_parallel_command_handler.py` - 初始化scheduler

### 8.3 测试（⏳ 待实施）

- ⏳ `test_resource_aware_scheduler.py` - 单元测试
- ⏳ `test_epic10_integration.py` - 集成测试
- ⏳ `test_epic10_performance.py` - 性能测试
- ⏳ `test_epic10_stress.py` - 压力测试

---

## 9. 最终确认和批准

### 9.1 用户最终确认

**用户要求**（2025-11-14）:
> "全部同意，但不用渐进式提升，一步到位"

**理解确认**:
- ✅ 同意移除API并发限制
- ✅ 同意并发值提升到100/50/20
- ✅ 同意引入ResourceAwareScheduler
- ✅ **要求**: 不采用渐进式提升（20→30→60→100），而是直接到100/50/20
- ✅ **接受**: 一步到位带来的潜在风险（通过ResourceAwareScheduler缓解）

### 9.2 最终批准签字

**PM (Sarah)**: ✅ 批准
**Architect (Morgan)**: ✅ 批准
**Dev (James)**: ⏳ 待审阅
**QA (Quinn)**: ⏳ 待审阅
**User**: ✅ **批准**（一步到位实施）

---

## 10. 附录

### 10.1 参考文档

- [Epic 10并发定义](../architecture/epic10-concurrency-definition.md) - ✅ 已更新
- [Story 10.15 ResourceAwareScheduler](../stories/10.15.resource-aware-scheduler.story.md) - ✅ 已创建
- [PRD Section 3.4](../prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md#L1426) - ✅ 已更新
- [Story 10.1](../stories/10.1.story.md) - ✅ 已更新
- [Story 10.2](../stories/10.2.story.md) - ✅ 已更新

### 10.2 并发限制对比表（最终版）

| 层级 | 迁移前 | 迁移后（一步到位） | 提升倍数 | 说明 |
|------|--------|------------------|---------|------|
| Agent级 | 20 | **100** | **5倍** | 移除API限制，基于系统资源 |
| 节点级 | 12 | **50** | **4.2倍** | 基于用户体验 + CPU资源 |
| 任务级 | 5 | **20** | **4倍** | 基于依赖关系复杂度 |
| 系统最大 | 100 | **500** | **5倍** | ResourceAwareScheduler保护 |

### 10.3 性能提升计算（一步到位）

**100节点批处理示例**:

迁移前（保守并发）:
```
节点分组: 100节点 / 12组 ≈ 9节点/组
每组Agent: 平均3个
总并发: 12组 × 3agent = 36个Agent
总耗时: ~120秒
```

迁移后（一步到位）:
```
节点分组: 100节点 / 50组 = 2节点/组
每组Agent: 平均5个
总并发: 50组 × 5agent = 250个Agent
总耗时: ~25秒
性能提升: 120秒 / 25秒 = 4.8倍 ≈ 5倍 ⚡
```

**资源保护场景**:
- Memory > 90% OR CPU > 90%: 紧急降低到10并发
- Memory > 80% OR CPU > 80%: 降低到原值 × 0.7
- Memory < 50% AND CPU < 60%: 提升到原值 × 1.3（不超过100）

---

## 11. 结论

本SCP-005提案完成了从"错误假设（API并发限制）"到"正确实现（资源感知调度）"的全面调整，采用用户要求的**一步到位实施方式**，将并发值直接提升到100/50/20，预期性能提升3-7倍（不同场景）。

**核心成果**:
- ✅ 完整的文档更新（Architecture + PRD + Stories）
- ✅ 新增Story 10.15 ResourceAwareScheduler完整设计
- ✅ 明确的实施路径（一步到位，2周完成）
- ✅ 完善的风险缓解策略（ResourceAwareScheduler保护机制）

**下一步行动**:
1. **立即**: 文档审查和批准（Dev、QA签字）
2. **迁移完成后Week 1**: ResourceAwareScheduler实现
3. **迁移完成后Week 2**: 系统集成
4. **迁移完成后Week 3**: 性能验证和报告

---

**文档版本**: v1.0 Final (一步到位版本)
**最后更新**: 2025-11-14
**状态**: ✅ 已批准（用户确认）
