---
story_id: "5.3"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 10
depends_on: ["5.1", "5.2"]
blocks: ["5.4", "5.6", "8.1"]
trace:
  - "FR-MAST-03"
  - "FR-MAST-06"
---

# Story 5.3: 5 信号融合 + 仅考察更新

Status: ready-for-dev

## Story
As a 系统,
I want 融合 5 个信号（BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度）为单维掌握度,
So that 掌握度评估全面稳健，且仅通过考察表现更新而非自评直接修改（Canvas PRD FR-MAST-06）。

## Acceptance Criteria

1. **Given** BKT p_mastery（信号 1）和 FSRS Retrievability（信号 2）已更新 **When** 系统调用 `query_mastery` MCP 工具 **Then** 返回融合后的单维 `mastery_level`（0-1）**And** 融合算法使用 `MasteryFusionEngine.compute_fused_mastery()` 加权平均 **And** 结果 clamp 到 [0.0, 1.0]

2. **Given** 5 个信号中有部分缺失（如新概念只有 BKT 无 FSRS）**When** 融合引擎计算 **Then** 自动过滤无数据信号（get_value == None）**And** 在有数据的信号之间重归一化权重 `w_i_norm = w_i / sum(w_j for active j)` **And** 返回 `active_signal_count` 和 `is_fallback` 标志

3. **Given** 全部 5 信号有数据 **When** 验证信号互补性 **Then** 任意两信号间 Pearson 相关系数 r < 0.7（信号不冗余）**And** 如果某对信号 r >= 0.7 则日志警告"信号冗余"

4. **Given** 融合后掌握度 + 考察实际表现数据 **When** 计算 Spearman rank correlation **Then** rho > 0.6（融合预测能力与考察结果一致性验收标准）**And** 验收测试用至少 30 个样本点

5. **Given** 学习者在 UI 上自行调整自评置信度 **When** 自评值变化 **Then** 掌握度 mastery_level 不直接更新（FR-MAST-06: 仅考察更新）**And** 自评值仅作为融合输入信号之一（权重 0.10）**And** 下次考察评分后掌握度才会重新计算

6. **Given** `MasteryFusionEngine` 不可用或所有信号为空 **When** 系统查询 mastery **Then** 降级为 `min(p_mastery, R)` 的经典公式 **And** 返回 `is_fallback=True`

7. **Given** 融合完成 **When** 写回 frontmatter **Then** `mastery_level` 字段更新为融合值 **And** `mastery_updated_at` 更新 **And** 5 个独立信号字段保持各自最新值（不被融合覆盖）

## Tasks / Subtasks

- [ ] Task 1: 验证 SignalRegistry 5 信号注册 (AC: #1, #2)
  - [ ] 确认 `backend/app/services/signal_registry.py` 已注册 5 个信号适配器
  - [ ] 信号 1 BKT: 权重 0.30，来源 ConceptState.p_mastery
  - [ ] 信号 2 FSRS: 权重 0.25，来源 FSRS Retrievability
  - [ ] 信号 3 错误历史: 权重 0.20，来源 error_history 聚合
  - [ ] 信号 4 校准偏差: 权重 0.15，来源 calibration_bias
  - [ ] 信号 5 自评置信度: 权重 0.10，来源 confidence_self_report
  - [ ] 单元测试：权重总和 = 1.0

- [ ] Task 2: 实现信号互补性检验 (AC: #3)
  - [ ] 创建 `validate_signal_complementarity(signal_data: Dict[str, List[float]]) -> SignalCorrelationResult`
  - [ ] 计算每对信号的 Pearson r
  - [ ] r >= 0.7 时返回 warning + 冗余信号对名称
  - [ ] 单元测试：构造高相关（r=0.9）和低相关（r=0.3）数据验证阈值

- [ ] Task 3: 实现 Spearman rho 验收测试 (AC: #4)
  - [ ] 创建 `tests/validation/test_fusion_spearman.py`
  - [ ] 用至少 30 个样本点（历史考察数据或合成数据）
  - [ ] 计算融合 mastery_level vs 考察 grade 的 Spearman rho
  - [ ] 断言 rho > 0.6

- [ ] Task 4: 实现仅考察更新约束 (AC: #5)
  - [ ] 在 `query_mastery` MCP 工具中，禁止直接写 mastery_level
  - [ ] 自评变化时：更新 confidence_self_report frontmatter 字段但不触发重融合
  - [ ] 仅在 `update_bkt`/`update_fsrs` 调用链完成后才触发融合重计算
  - [ ] 单元测试：直接修改自评 → mastery_level 不变 → 下次考察后 mastery_level 变化

- [ ] Task 5: 降级路径 + frontmatter 写回 (AC: #6, #7)
  - [ ] 验证 `MasteryEngine.effective_proficiency()` 的 fallback 到 min(p_mastery, R)
  - [ ] 融合写回同时更新 mastery_level + mastery_updated_at
  - [ ] 5 个独立信号字段由各自的 Story（5.1 BKT、5.2 FSRS 等）独立写回
  - [ ] 单元测试：fusion_engine=None 时 fallback 正确

- [ ] Task 6: MCP query_mastery 工具端点 (AC: #1, #2, #6)
  - [ ] 在 `backend/app/mcp/tools/mastery_tools.py` 创建 `query_mastery` 工具函数
  - [ ] 返回值包含：mastery_level、active_signal_count、is_fallback、signal_details[]
  - [ ] 在 `backend/app/mcp/server.py` 注册路由
  - [ ] 集成测试：query_mastery 返回完整融合结果

## Dev Notes

### Architecture
- 5 信号融合是 Canvas PRD 的核心学术创新点（FR-MAST-03, FR-MAST-06）
- 现有 `MasteryFusionEngine`（mastery_fusion.py）已实现 MVP 加权平均算法
- `SignalRegistry`（signal_registry.py）管理信号适配器的注册和获取
- 关键约束：FR-MAST-06 要求"掌握度仅通过考察更新"——自评是信号输入但不直接触发掌握度变化
- Phase 2+ 预留 Beta-Bayesian 融合升级路径

### File Paths
- 融合引擎：`backend/app/services/mastery_fusion.py` (MasteryFusionEngine)
- 信号注册表：`backend/app/services/signal_registry.py` (SignalRegistry)
- 融合模型：`backend/app/models/mastery_models.py` (FusionResult, SignalDetail, SignalCorrelationResult)
- MasteryEngine 集成：`backend/app/services/mastery_engine.py` (set_fusion_engine, effective_proficiency)
- frontmatter schema：anchor PRD §1.5 (line 632-648)

### Testing
- 单元测试：权重归一化、信号过滤、降级路径、仅考察更新约束
- 验收测试：Spearman rho > 0.6（30+ 样本）
- 统计测试：信号互补性 r < 0.7
- 边界测试：0 信号、1 信号、全部 5 信号场景

### References
- **From PRD**: §1.5 Signal Fusion 验收标准 (line 610-613)
- **From PRD**: FR-MAST-06 掌握度仅通过考察更新
- Canvas PRD L801: 5 个核心信号定义
- `backend/app/services/mastery_fusion.py`: compute_fused_mastery 算法

## UAT Script

> 1. 完成 5 道不同概念的考察题（产生 BKT + FSRS 数据）
> 2. 调用 query_mastery 查看某概念的融合掌握度
> 3. 确认返回值包含 mastery_level 和 5 个 signal_details
> 4. 在 frontmatter 手动修改 confidence_self_report 为 0.99
> 5. 再次调用 query_mastery，确认 mastery_level 未变化（仅考察更新）
> 6. 做一道该概念的考察题
> 7. 确认 mastery_level 此时更新（融合了新的自评权重）
> 8. 检查 frontmatter mastery_level 字段已更新

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 信号权重归一化 | unit | `pytest tests/unit/test_signal_registry.py -x` | 0 failures |
| 融合计算 | unit | `pytest tests/unit/test_mastery_fusion.py -x` | 0 failures |
| 信号互补性 r<0.7 | validation | `pytest tests/validation/test_signal_complementarity.py -x` | 0 failures |
| Spearman rho>0.6 | validation | `pytest tests/validation/test_fusion_spearman.py -x` | 0 failures |
| 仅考察更新 | unit | `pytest tests/unit/test_exam_only_update.py -x` | 0 failures |
| MCP query_mastery | integration | `pytest tests/integration/test_query_mastery_mcp.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
