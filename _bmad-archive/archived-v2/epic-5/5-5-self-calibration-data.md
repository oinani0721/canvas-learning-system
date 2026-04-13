---
doc_type: story
story_id: "5.5"
aliases: ["5.5"]
epic_id: "EPIC-5"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 2
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 5.5: 自我评估校准数据记录

## Story

As a 系统,
I want 记录学习者的自我评估校准数据,
so that 系统可以衡量学习者的元认知准确性。

## Acceptance Criteria

1. **Given** 学习者完成答题后
   **When** 系统提示学习者自评"你觉得自己答得怎么样？"
   **Then** 学习者选择自评等级（高/中/低信心）
   **And** 自评结果与实际评分结果对比存储
   **And** 校准偏差（自评 vs 实际）纳入 5 信号融合（Story 5.3）

2. **Given** 学习者跳过自评（不作答）
   **When** 系统等待自评超过 10 秒或学习者明确跳过
   **Then** 本次记录 `self_rating: null`
   **And** 校准偏差在该次不计入 5 信号融合（信号缺失处理）
   **And** 不影响其他信号和 mastery_score 更新

3. **Given** 连续 10 次及以上的校准数据可用
   **When** 系统计算校准偏差
   **Then** 偏差 = mean(|self_rating_normalized - actual_score|)（滚动窗口最近 10 次）
   **And** 偏差值归一化到 [0, 1]（0=完美校准，1=完全偏离）
   **And** 偏差值存入 frontmatter `calibration_bias` 字段

## Tasks / Subtasks

- [ ] Task 1: 自评数据模型 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/schemas/calibration.py` 定义 `SelfRatingLevel` enum：`HIGH = "high"`, `MEDIUM = "medium"`, `LOW = "low"`
  - [ ] 1.2 定义 `SelfRatingRecord` Pydantic 模型：`note_id: str, question_id: str, self_rating: Optional[SelfRatingLevel], actual_score: float, timestamp: datetime`
  - [ ] 1.3 定义 self_rating 到数值映射：`HIGH=1.0, MEDIUM=0.5, LOW=0.0`（用于偏差计算）

- [ ] Task 2: 校准偏差计算服务 (AC: #3)
  - [ ] 2.1 在 `backend/app/services/calibration_service.py` 实现 `compute_calibration_bias(records: list[SelfRatingRecord]) -> Optional[float]`
  - [ ] 2.2 过滤掉 `self_rating=null` 的记录
  - [ ] 2.3 滚动窗口：只取最近 10 条有效记录（`self_rating` 非 null）
  - [ ] 2.4 有效记录 < 3 条时返回 None（数据不足，不计算偏差）
  - [ ] 2.5 偏差公式：`bias = mean([abs(self_numeric_i - actual_score_i) for i in window])`

- [ ] Task 3: frontmatter 读写 (AC: #1, #3)
  - [ ] 3.1 扩展 `backend/app/services/frontmatter_service.py`：`append_calibration_record(note_path: str, record: SelfRatingRecord) -> None`
  - [ ] 3.2 `calibration_history` 数组最多保留最近 20 条（超出时删除最旧）
  - [ ] 3.3 实现 `update_calibration_bias(note_path: str, bias: Optional[float]) -> None` 更新 `calibration_bias` 字段
  - [ ] 3.4 `calibration_bias` 字段在 5 信号融合前由 mastery_service 读取（配合 Story 5.3）

- [ ] Task 4: API 端点 (AC: #1, #2)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/mastery.py` 创建 `POST /api/v1/mastery/self-rating` 端点
  - [ ] 4.2 请求体：`note_id: str, question_id: str, self_rating: Optional[SelfRatingLevel], actual_score: float`
  - [ ] 4.3 响应体：`calibration_bias: Optional[float], records_used: int`（告知前端当前偏差值和样本量）
  - [ ] 4.4 `self_rating=null` 时端点仍接受请求，正常返回（允许跳过自评）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3)
  - [ ] 5.1 `tests/unit/test_calibration_bias.py`：验证偏差计算（完美校准=0，最差校准=1，含 null 记录过滤）
  - [ ] 5.2 `tests/unit/test_calibration_insufficient_data.py`：验证少于 3 条有效记录时返回 None
  - [ ] 5.3 `tests/integration/test_self_rating_endpoint.py`：验证跳过自评时端点正常响应

## Dev Notes

- **元认知校准依据**：Flavell (1979) 元认知理论 + Kruger & Dunning (1999) 自我评估偏差研究，校准准确性是学习质量的重要指标
- **HIGH/MEDIUM/LOW 三级**：相比 5 级量表更符合快速自评场景（Likert 量表降维），减少决策负担
- **滚动窗口 10 次**：平衡数据新鲜度与统计稳定性；不足 3 条时返回 None 避免过少样本噪声太大
- **与 5.3 的耦合**：`calibration_bias` 是 Story 5.3 的 5 信号之一，本 Story 只负责数据记录，5.3 负责读取使用
- **estimate 2h**：较小因为不依赖复杂算法，主要是数据管道和模型定义

### Project Structure Notes

- 校准服务：`backend/app/services/calibration_service.py`（新建）
- Pydantic 模型：`backend/app/schemas/calibration.py`（新建）
- frontmatter 扩展：`backend/app/services/frontmatter_service.py`（扩展 append_calibration_record）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（新增 /self-rating）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.5] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR24] — 自我评估校准需求
- [Story: 5.3] — calibration_bias 的消费方（5 信号融合）

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证答完题后出现自评提示** (AC: #1)
   - 完成任意一道考察题（无论对错）
   - 系统评分结果展示后，应该出现"你觉得自己答得怎么样？"的提示
   - 提示应有三个选项：高信心 / 中等信心 / 低信心
   - 如果没有出现此提示，记录 Story 5.5

2. **验证可以跳过自评** (AC: #2)
   - 看到自评提示后，找到跳过按钮或等待
   - 跳过后系统应该正常继续（不卡住、不报错）
   - 如果跳过后出现错误或界面卡住，记录 Story 5.5

3. **验证校准偏差随时间更新** (AC: #3)
   - 连续完成 10 道题并都做自评
   - 打开概念笔记，frontmatter 中应有 `calibration_bias` 字段
   - 如果少于 10 次自评后 `calibration_bias` 就有了数值，或超过 10 次后还是空值，记录 Story 5.5

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.5.1 | pytest | `.venv/bin/pytest tests/unit/test_calibration_bias.py -x -q` | 0 failed |
| CP-5.5.2 | pytest | `.venv/bin/pytest tests/unit/test_calibration_insufficient_data.py -x -q` | 0 failed |
| CP-5.5.3 | pytest | `.venv/bin/pytest tests/integration/test_self_rating_endpoint.py -x -q` | 0 failed |

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
