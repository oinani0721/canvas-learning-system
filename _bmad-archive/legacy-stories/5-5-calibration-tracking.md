# Story 5.5: Calibration 校准追踪

Status: ready-for-dev

## Story

As a 用户,
I want 系统追踪我的元认知校准——识别"以为会了其实不会"的危险盲区,
so that 我能发现自己的认知偏差。

## Acceptance Criteria

1. **AC-1: Area9 式 2x2 置信度矩阵记录**
   - **Given** 用户在检验白板中被考察，评分完成后
   - **When** 系统记录校准数据
   - **Then** 系统记录一对 (self_confidence, actual_performance) 数据点：
     - self_confidence: Agent 在评分前顺带询问用户"你觉得自己答得怎么样"，收集自信度评估（0.0~1.0 量化值，如 high=0.8 / medium=0.5 / low=0.2）
     - actual_performance: AutoSCORE 4 维平均分归一化到 0.0~1.0
   - **And** 每次考察交互产生一条 CalibrationRecord（node_id, session_id, self_confidence, actual_performance, timestamp）
   - **And** CalibrationRecord 持久化到 Neo4j（mastery_calibration_* 前缀属性）或 SQLite 追加表

2. **AC-2: 四种状态分类**
   - **Given** 一条 CalibrationRecord
   - **When** 系统计算该条记录的校准象限
   - **Then** 按阈值分类为四种状态：
     - **掌握（Mastered）**: self_confidence >= 0.6 且 actual_performance >= 0.6 — 确定且正确
     - **误解（Misconception）**: self_confidence >= 0.6 且 actual_performance < 0.6 — 确定但错误，**最危险**
     - **运气（Lucky）**: self_confidence < 0.6 且 actual_performance >= 0.6 — 不确定但正确
     - **未学（Unlearned）**: self_confidence < 0.6 且 actual_performance < 0.6 — 不确定且错误
   - **And** 分类结果附加到 CalibrationRecord.quadrant 字段
   - **And** 误解象限的记录标记 is_dangerous = True，供后续出题优先考察

3. **AC-3: 三阶段渐进评估**
   - **Given** 某个节点累积了 N 条 CalibrationRecord
   - **When** 系统计算该节点的校准评估
   - **Then** 按数据量分三阶段：
     - **阶段 1（< 10 条）**: 仅收集数据，不产出校准评估结论，UI 显示"数据收集中（N/10）"
     - **阶段 2（10-20 条）**: 初步趋势展示——显示四象限分布百分比 + 签名偏差（signed_bias = mean(self_confidence - actual_performance)），标注"初步趋势，仅供参考"
     - **阶段 3（20+ 条）**: 可靠评估——产出完整校准报告：四象限分布 + 签名偏差 + 绝对偏差（absolute_bias = mean(|self_confidence - actual_performance|)）+ 校准评级（Well-Calibrated / Over-Confident / Under-Confident）
   - **And** 校准评级阈值：|signed_bias| < 0.15 → Well-Calibrated; signed_bias > 0.15 → Over-Confident; signed_bias < -0.15 → Under-Confident

4. **AC-4: 签名偏差与绝对偏差计算**
   - **Given** 节点有 N >= 10 条 CalibrationRecord
   - **When** 计算偏差指标
   - **Then** signed_bias = mean(self_confidence_i - actual_performance_i) for all i
   - **And** absolute_bias = mean(|self_confidence_i - actual_performance_i|) for all i
   - **And** 偏差值保留到小数点后 3 位
   - **And** Over-Confident（signed_bias > 0）表示用户系统性高估自己，Under-Confident（signed_bias < 0）表示用户系统性低估自己

5. **AC-5: 校准数据与 FR-MAST-05 集成**
   - **Given** 校准追踪系统运行中
   - **When** 用户通过学习档案面板（Story 5.3）或 Dashboard（Story 5.4）查看
   - **Then** 校准信息可作为学习档案面板的一个展示模块（校准状态卡片）
   - **And** 误解象限（Misconception）节点在 Dashboard 待复习列表中优先排序
   - **And** 校准偏差作为信号源供 Story 5.6 多信号融合消费（calibration_bias 字段）

6. **AC-6: 校准数据 API 端点**
   - **Given** 后端 FastAPI 运行
   - **When** 调用校准 API
   - **Then** 以下端点正常工作：
     - `POST /mastery/{id}/calibration` — 记录一条 CalibrationRecord（self_confidence + actual_performance）
     - `GET /mastery/{id}/calibration/summary` — 返回校准摘要（阶段/象限分布/偏差/评级）
     - `GET /mastery/calibration/dangerous` — 返回所有误解象限节点列表（供出题优先选择）
   - **And** 所有端点返回结构化 Pydantic 响应模型

7. **AC-7: 单元测试覆盖**
   - **Given** calibration_tracker.py 模块
   - **When** 运行测试
   - **Then** 四象限分类边界值测试（0.59/0.60/0.61 各象限精确边界）
   - **And** 三阶段渐进测试（9/10/20/21 条数据时的行为差异）
   - **And** signed_bias / absolute_bias 计算正确性
   - **And** 校准评级阈值测试（|signed_bias| = 0.14/0.15/0.16 时的评级）
   - **And** 空数据 / 单条数据时的安全处理

## Tasks / Subtasks

- [ ] **Task 1: 数据模型定义** (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/models/mastery_models.py` 中定义 CalibrationRecord Pydantic 模型（node_id, session_id, self_confidence, actual_performance, quadrant, is_dangerous, timestamp）
  - [ ] 1.2 定义 CalibrationQuadrant 枚举（MASTERED / MISCONCEPTION / LUCKY / UNLEARNED）
  - [ ] 1.3 定义 CalibrationSummary 响应模型（stage, record_count, quadrant_distribution, signed_bias, absolute_bias, calibration_rating）
  - [ ] 1.4 定义 CalibrationRating 枚举（WELL_CALIBRATED / OVER_CONFIDENT / UNDER_CONFIDENT / INSUFFICIENT_DATA）

- [ ] **Task 2: 核心算法实现** (AC: #2, #3, #4)
  - [ ] 2.1 创建 `backend/app/services/calibration_tracker.py`
  - [ ] 2.2 实现 classify_quadrant(self_confidence, actual_performance) → CalibrationQuadrant，阈值 0.6
  - [ ] 2.3 实现 compute_signed_bias(records) → float
  - [ ] 2.4 实现 compute_absolute_bias(records) → float
  - [ ] 2.5 实现 compute_calibration_rating(signed_bias, record_count) → CalibrationRating（含三阶段渐进逻辑）
  - [ ] 2.6 实现 get_calibration_summary(node_id) → CalibrationSummary（聚合四象限分布+偏差+评级）
  - [ ] 2.7 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 3: 持久化层** (AC: #1, #6)
  - [ ] 3.1 在 `backend/app/services/mastery_store.py` 中添加 CalibrationRecord 存取方法：
    - save_calibration_record(record: CalibrationRecord)
    - get_calibration_records(node_id: str, group_id: str) → List[CalibrationRecord]
    - get_dangerous_nodes(group_id: str) → List[str]（返回误解象限节点 ID 列表）
  - [ ] 3.2 Neo4j 存储方案：CalibrationRecord 作为 Relationship 或 Node 属性追加（mastery_calibration_records JSON 序列化）
  - [ ] 3.3 编辑后运行 `ruff check`

- [ ] **Task 4: API 端点** (AC: #6)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/mastery.py` 中添加三个校准端点
  - [ ] 4.2 POST /mastery/{id}/calibration — 接收 CalibrationRequest，调用 calibration_tracker.record_calibration()
  - [ ] 4.3 GET /mastery/{id}/calibration/summary — 返回 CalibrationSummary
  - [ ] 4.4 GET /mastery/calibration/dangerous — 返回误解节点列表
  - [ ] 4.5 编辑后运行 `ruff check`

- [ ] **Task 5: 与 MCP 工具集成** (AC: #5)
  - [ ] 5.1 在 MCP 工具中添加 record_calibration 工具——Agent 评分完成后可调用记录自信度+实际表现
  - [ ] 5.2 确保 calibration_bias 字段可被 mastery_engine 消费（供 Story 5.6 多信号融合读取）

- [ ] **Task 6: 单元测试** (AC: #7)
  - [ ] 6.1 创建 `backend/tests/unit/test_calibration_tracker.py`：
    - 四象限分类边界值测试
    - 三阶段渐进逻辑测试
    - signed_bias / absolute_bias 计算测试
    - 校准评级阈值边界测试
    - 空数据安全处理测试
  - [ ] 6.2 创建 `backend/tests/unit/test_calibration_api.py`：
    - 三个 API 端点集成测试（FastAPI TestClient）
  - [ ] 6.3 运行全部测试确认通过

- [ ] **Task 7: 集成验证** (AC: #1-#6)
  - [ ] 7.1 端到端测试：记录 5 条 → 确认阶段 1（仅收集）
  - [ ] 7.2 端到端测试：记录 15 条 → 确认阶段 2（初步趋势 + signed_bias）
  - [ ] 7.3 端到端测试：记录 25 条 → 确认阶段 3（完整报告 + 评级）
  - [ ] 7.4 端到端测试：模拟过度自信用户（高自信+低实际）→ 确认 Over-Confident 评级 + 误解节点列表
  - [ ] 7.5 运行 `ruff check backend/app/services/calibration_tracker.py backend/app/api/v1/endpoints/mastery.py` 确认 lint 通过

## Dev Notes

### Area9 2x2 置信度矩阵（学术参考）

**来源**: Area9 Rhapsode 自适应学习平台（元认知校准追踪）

```
                     实际表现高           实际表现低
                  ┌──────────────────┬──────────────────┐
  自信度高       │   ✅ 掌握         │   ⚠️ 误解（最危险）│
  (>= 0.6)      │   Mastered        │   Misconception    │
                  ├──────────────────┼──────────────────┤
  自信度低       │   🍀 运气         │   📚 未学          │
  (< 0.6)       │   Lucky           │   Unlearned        │
                  └──────────────────┴──────────────────┘
```

**关键洞见**：
- 误解象限（高自信+低表现）是最危险的——学习者"不知道自己不知道"，传统系统无法识别
- 运气象限（低自信+高表现）提示学习者低估自己，需要鼓励性反馈
- Area9 研究显示约 20-30% 的自评与实际表现存在显著偏差

### 三阶段渐进设计理据

- **< 10 条**: 统计学上样本不足以产出有意义的趋势，强制仅收集
- **10-20 条**: 可初步计算均值但置信区间宽，标注"仅供参考"
- **20+ 条**: 根据中心极限定理，20+ 样本的均值趋于正态，偏差估计可靠

### 偏差计算公式

```
给定 N 条记录，每条有 (c_i, p_i) 其中 c = self_confidence, p = actual_performance:

signed_bias   = (1/N) * Σ(c_i - p_i)    # 正值=过度自信，负值=过度谦虚
absolute_bias = (1/N) * Σ|c_i - p_i|    # 校准精度，越小越好

校准评级:
  |signed_bias| < 0.15 → Well-Calibrated
  signed_bias > 0.15   → Over-Confident（系统性高估）
  signed_bias < -0.15  → Under-Confident（系统性低估）
```

### Brownfield 上下文

`calibration_tracker.py` 在架构文档目录结构中列出但**尚未创建**。本 Story 为 greenfield 实现。

- 需新建 `backend/app/services/calibration_tracker.py`
- 需在已有 `mastery_models.py` 中追加 Calibration 相关模型
- 需在已有 `mastery.py` API 端点文件中追加校准端点
- 需在已有 `mastery_store.py` 中追加 CalibrationRecord 存取方法

### 与其他 Story 的依赖关系

| 依赖 | 方向 | 说明 |
|------|------|------|
| Story 5.1 (BKT+FSRS) | 前置依赖 | 需要 ConceptState 数据模型和 mastery_store 基础 |
| Story 5.3 (学习档案面板) | 后续消费 | 校准状态卡片展示在学习档案面板 |
| Story 5.4 (Dashboard) | 后续消费 | 误解节点优先排序在待复习列表 |
| Story 5.6 (多信号融合) | 后续消费 | calibration_bias 作为融合信号源之一 |
| Story 6.3 (AI 精准出题) | 后续消费 | 误解象限节点优先考察 |
| Story 6.4 (AutoSCORE) | 前置依赖 | 需要 actual_performance 来自 AutoSCORE 评分 |

### 6 阶段增量算法集成（Phase 3 位置）

本 Story 处于 **Phase 3: 校准追踪**：

| Phase | 内容 | 本 Story 涉及 |
|-------|------|-------------|
| Phase 0 | MVP 核心 BKT+FSRS | Story 5.1 |
| Phase 1 | 策略适配算法 | — |
| Phase 2 | 融合算法 Beta-Bayesian | Story 5.6 部分基础 |
| **Phase 3** | **校准追踪 Calibration Tracking** | **是 — 本 Story** |
| Phase 4 | 高级分析 SOLO 量表 | — |
| Phase 5 | 实验性功能 | — |

### 性能约束

- 校准记录写入：追加操作，O(1)
- 校准摘要计算：遍历该节点所有记录，O(N)，N 通常 < 100，可接受
- 不需要实时性（非关键路径），可异步计算

### Project Structure Notes

- `calibration_tracker.py` 位于 `backend/app/services/`，符合架构文档目录结构
- CalibrationRecord 模型追加到 `backend/app/models/mastery_models.py`（加法编辑）
- API 端点追加到 `backend/app/api/v1/endpoints/mastery.py`（加法编辑）
- EventBus 事件 `CALIBRATION_RECORDED` 追加到 `models/canvas_events.py`（追加式编辑）
- 测试文件在 `backend/tests/unit/` 目录下创建

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#能力域5] — Area9 式 2x2 置信度矩阵 + 三阶段渐进 + 5-6 信号→单维掌握度
- [Source: _bmad-output/planning-artifacts/architecture.md#项目结构] — calibration_tracker.py 在 services/ 目录
- [Source: _bmad-output/planning-artifacts/architecture.md#EventBus] — EventBus 事件定义规范
- [Source: _bmad-output/planning-artifacts/epics.md#Story5.5] — AC 原文：Area9 四种状态 + 三阶段渐进
- [Source: _bmad-output/planning-artifacts/prd.md#能力域5] — FR-MAST-05: Area9 式 2x2 置信度矩阵追踪元认知校准

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/calibration_tracker.py` — 新建（核心算法）
- `backend/app/models/mastery_models.py` — 追加 Calibration 相关模型
- `backend/app/services/mastery_store.py` — 追加 CalibrationRecord 存取方法
- `backend/app/api/v1/endpoints/mastery.py` — 追加校准 API 端点
- `backend/app/models/canvas_events.py` — 追加 CALIBRATION_RECORDED 事件
- `backend/tests/unit/test_calibration_tracker.py` — 新建
- `backend/tests/unit/test_calibration_api.py` — 新建
