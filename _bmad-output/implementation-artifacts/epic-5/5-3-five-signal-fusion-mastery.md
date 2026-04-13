---
doc_type: story
story_id: "5.3"
aliases: ["5.3"]
epic_id: "EPIC-5"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: ["5.1", "5.2"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 5.3: 5 信号融合掌握度评估

## Story

As a 系统,
I want 维护 5 信号融合的掌握度评估,
so that 掌握度评估比单一指标更准确全面。

## Acceptance Criteria

1. **Given** 某概念有多维度学习数据
   **When** 系统计算综合掌握度
   **Then** 融合 5 个信号：BKT mastery、FSRS stability、答题准确率、提示使用率、校准偏差
   **And** 每个信号有配置权重（可调整但有合理默认值）
   **And** 融合结果作为最终 mastery_score 写入 frontmatter

2. **Given** 部分信号数据缺失（如新概念无校准历史）
   **When** 计算融合分数
   **Then** 缺失信号权重重分配给其余信号（归一化），不报错
   **And** 缺失信号在融合时记录为 null（不视为 0）

3. **Given** 融合权重配置
   **When** 管理员修改 `settings.mastery_fusion_weights` 配置
   **Then** 新权重立即生效（下一次计算时使用）
   **And** 权重总和不等于 1.0 时系统自动归一化并记录 warning 日志

## Tasks / Subtasks

- [ ] Task 1: 定义 5 信号规范化接口 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/mastery_service.py` 定义 `FiveSignalInput` Pydantic 模型：`bkt_mastery: Optional[float], fsrs_stability: Optional[float], accuracy_rate: Optional[float], hint_rate: Optional[float], calibration_bias: Optional[float]`（均为 0.0-1.0 归一化范围）
  - [ ] 1.2 定义信号方向：bkt_mastery(高=好), fsrs_stability(高=好), accuracy_rate(高=好), hint_rate(低=好，需反转), calibration_bias(接近 0=好，需转换为 abs 后反转)
  - [ ] 1.3 实现 `normalize_signal(value: Optional[float], direction: Literal["higher_better", "lower_better"]) -> Optional[float]` 统一将信号转为"高=好"方向

- [ ] Task 2: 实现加权融合算法 (AC: #1, #2, #3)
  - [ ] 2.1 实现 `compute_fused_mastery(signals: FiveSignalInput, weights: MasteryFusionWeights) -> float`
  - [ ] 2.2 缺失信号处理：过滤 None 值，对现有信号权重重新归一化（`w_i / sum(present_weights)`）
  - [ ] 2.3 融合公式：`fused = sum(normalized_signal_i * weight_i for i in present_signals)`
  - [ ] 2.4 输出 clamp 到 [0.0, 1.0]

- [ ] Task 3: 默认权重配置 (AC: #1, #3)
  - [ ] 3.1 在 `backend/app/core/config.py` 添加 `MasteryFusionWeights` 配置：`bkt=0.35, fsrs=0.25, accuracy=0.20, hint=0.10, calibration=0.10`
  - [ ] 3.2 权重和检查：启动时验证 sum(weights) ≈ 1.0（±0.001），否则自动归一化并 structlog warning
  - [ ] 3.3 权重可通过环境变量覆盖：`MASTERY_WEIGHT_BKT=0.4` 等

- [ ] Task 4: 集成到 mastery 更新流程 (AC: #1)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/mastery.py` 添加 `POST /api/v1/mastery/fused-update` 端点
  - [ ] 4.2 该端点串联调用：读 frontmatter → BKT 更新（Story 5.1）→ FSRS 更新（Story 5.2）→ 5 信号融合 → 写 frontmatter
  - [ ] 4.3 请求体包含全部 5 信号原始值（由调用方提供），端点内部完成归一化
  - [ ] 4.4 响应体：`fused_mastery: float, signal_contributions: dict[str, float]`（每个信号的贡献值，用于调试）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3)
  - [ ] 5.1 `tests/unit/test_five_signal_fusion.py`：验证各信号组合的融合结果（含缺失信号的权重重分配）
  - [ ] 5.2 `tests/unit/test_signal_normalization.py`：验证 hint_rate/calibration_bias 方向反转正确
  - [ ] 5.3 `tests/unit/test_fusion_weights_validation.py`：验证不合法权重自动归一化

## Dev Notes

- **5 信号来源**：
  1. `bkt_mastery`：来自 Story 5.1 的 BKT 后验概率
  2. `fsrs_stability`：来自 Story 5.2 的稳定性参数，需映射到 [0,1]（`min(stability/30, 1.0)`，30 天视为"完全稳定"）
  3. `accuracy_rate`：近 N 次考察的正确率（从 frontmatter error_history 计算）
  4. `hint_rate`：近 N 次考察中使用提示的比例（hint_used/total_attempts），越低越好
  5. `calibration_bias`：自评与实际评分的平均偏差（|自评-实际| 的均值），越低越好
- **depends_on 5.1 和 5.2**：BKT 和 FSRS 更新必须先完成，融合才能读取最新参数
- **权重设计依据**：BKT+FSRS 合计 60% 体现算法核心，accuracy 20% 是直观指标，hint+calibration 各 10% 是元认知补充
- **信号缺失策略**：新概念前期只有 BKT+accuracy，缺失 3 个信号是正常状态，系统应优雅降级

### Project Structure Notes

- 核心服务：`backend/app/services/mastery_service.py`（与 5.1/5.2 共享）
- Pydantic 模型：`backend/app/schemas/mastery.py`（扩展 FiveSignalInput + MasteryFusionWeights）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（添加 /fused-update）
- 配置：`backend/app/core/config.py`（添加 MasteryFusionWeights）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.3] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR21] — 5 信号融合需求
- [Story: 5.1] — BKT mastery 信号来源
- [Story: 5.2] — FSRS stability 信号来源
- [Story: 5.5] — calibration_bias 信号来源

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证综合分数比单一答题正确率更稳定** (AC: #1)
   - 找一个你"偶尔答对但经常忘记"的概念
   - 答对一次后查看 mastery_score
   - mastery_score 不应直接跳到很高（因为 FSRS stability 和 hint_rate 信号会拉低）
   - 如果一次答对后分数超过 0.8，记录 Story 5.3

2. **验证新概念（无历史数据）可以正常计算** (AC: #2)
   - 对一个全新概念完成第一次考察
   - 应该可以看到一个 mastery_score 数值（不应报错或显示 0）
   - 如果出现错误提示或 mastery_score=0，记录 Story 5.3

3. **验证多次答对后综合分数持续上升** (AC: #1)
   - 对同一概念连续答对 5 次（都不使用提示）
   - 每次答对后记录 mastery_score
   - 分数应该单调上升（每次都比上次高）
   - 如果中途下降，记录 Story 5.3 和每次的分数

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.3.1 | pytest | `.venv/bin/pytest tests/unit/test_five_signal_fusion.py -x -q` | 0 failed |
| CP-5.3.2 | pytest | `.venv/bin/pytest tests/unit/test_signal_normalization.py -x -q` | 0 failed |
| CP-5.3.3 | pytest | `.venv/bin/pytest tests/unit/test_fusion_weights_validation.py -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-5]]
- PRD: [[PRD14]]
- Depends on: [[5.1]], [[5.2]]
