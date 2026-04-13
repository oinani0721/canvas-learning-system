# Story 5.6: 多信号融合

Status: ready-for-dev

## Story

As a 系统,
I want 将 5-6 核心信号（BKT+FSRS+考察评分+校准偏差+自信度自评）融合为单维掌握度,
so that 精通度评估更全面准确。

## Acceptance Criteria

1. **AC-1: N 信号动态接入架构**
   - **Given** 系统定义了信号注册接口
   - **When** 开发者需要接入新信号源
   - **Then** 通过实现 `MasterySignal` 协议（Protocol class）即可注册新信号：
     - `signal_name: str` — 信号标识（如 "bkt", "fsrs", "exam_score"）
     - `get_value(node_id: str) -> float | None` — 返回 0.0~1.0 归一化信号值，无数据时返回 None
     - `get_weight(node_id: str) -> float` — 返回该信号在当前节点的权重（可基于数据量动态调整）
     - `get_reliability(node_id: str) -> float` — 返回信号可靠度 0.0~1.0（数据越多越可靠）
   - **And** 信号注册表（SignalRegistry）支持动态注册和注销
   - **And** 融合引擎从注册表中获取所有活跃信号进行融合
   - **And** 架构支持后续 Phase 2 Beta-Bayesian 升级（当前 MVP 使用加权平均）

2. **AC-2: MVP 5 核心信号定义**
   - **Given** 系统启动
   - **When** 默认信号注册完成
   - **Then** 以下 5 个信号自动注册：
     - **BKT 掌握概率** (bkt_mastery): ConceptState.p_mastery，权重基础值 0.30
     - **FSRS 可提取性** (fsrs_retrievability): FSRS Card 当前 R 值，权重基础值 0.25
     - **考察评分均值** (exam_score_avg): 近 N 次 AutoSCORE 4 维均分归一化，权重基础值 0.25
     - **校准偏差** (calibration_bias): Story 5.5 的 signed_bias 反转（-signed_bias，偏差越大掌握度越不可靠），权重基础值 0.10
     - **自信度自评** (self_confidence_avg): 近 N 次自信度均值，权重基础值 0.10
   - **And** 权重总和始终归一化为 1.0
   - **And** 信号无数据时（get_value 返回 None）该信号权重重新分配给其他信号

3. **AC-3: 加权平均融合算法（MVP）**
   - **Given** 节点有 K 个信号有数据（K <= 5）
   - **When** 融合引擎计算单维掌握度
   - **Then** 执行加权平均融合：
     - 过滤掉 value = None 的信号
     - 重新归一化剩余信号权重：`w_i_norm = w_i / Σw_j (for all j where value_j is not None)`
     - 融合值：`fused_mastery = Σ(w_i_norm * value_i)`
   - **And** 融合值钳位在 [0.0, 1.0]
   - **And** 若所有信号均无数据（K == 0），返回 0.0（未评估）
   - **And** 融合结果替代 Story 5.1 的 `effective_proficiency = min(p_mastery, R)`（向后兼容：5.1 的 min 策略作为 fallback 当融合引擎不可用时）

4. **AC-4: 信号互补性验收（r < 0.7）**
   - **Given** 系统积累了 30+ 条融合记录
   - **When** 运行信号互补性诊断
   - **Then** 任意两个信号的皮尔逊相关系数 r < 0.7
   - **And** 若 r >= 0.7（两个信号高度相关），系统日志告警"信号 X 和 Y 高度相关（r=0.XX），建议审查是否冗余"
   - **And** 互补性检查为诊断工具（不阻塞融合计算），结果输出到日志和健康面板
   - **And** 验收测试使用真实考察数据（非合成数据）

5. **AC-5: 融合结果与下游集成**
   - **Given** 融合引擎产出 fused_mastery 值
   - **When** 下游系统读取精通度
   - **Then** fused_mastery 替代 effective_proficiency 用于：
     - 节点颜色映射（Story 5.2 mastery_level 阈值不变）
     - 学习档案面板展示（Story 5.3）
     - FSRS 待复习排序（Story 5.4）
     - 出题优先级计算（Story 6.3）
   - **And** MasteryEngine.effective_proficiency() 方法内部切换为调用融合引擎（接口不变，内部实现升级）
   - **And** API 响应增加 `fusion_details` 字段：各信号名称+权重+值（供调试和透明性）

6. **AC-6: 多维精通度远期预留**
   - **Given** 当前 MVP 实现单维融合
   - **When** 架构设计
   - **Then** 数据模型预留多维扩展字段（如 conceptual_mastery, procedural_mastery, metacognitive_mastery）
   - **And** 当前这些字段不计算不展示，仅预留 schema
   - **And** 多维精通度为 Phase 3+ 远期研究目标，本 Story 不实现

7. **AC-7: 单元测试覆盖**
   - **Given** 融合引擎模块
   - **When** 运行测试
   - **Then** N 信号注册/注销测试
   - **And** 加权平均融合正确性测试（已知权重+值 → 预期融合值）
   - **And** 信号缺失时权重重新归一化测试（1/2/3/4/5 个信号有数据各测）
   - **And** 全部信号无数据时返回 0.0 测试
   - **And** 融合值钳位 [0.0, 1.0] 边界测试
   - **And** 信号互补性 Pearson 相关系数计算正确性测试
   - **And** 向后兼容测试：融合引擎不可用时 fallback 到 min(p_mastery, R)

## Tasks / Subtasks

- [ ] **Task 1: 信号协议与注册表定义** (AC: #1)
  - [ ] 1.1 在 `backend/app/models/mastery_models.py` 中定义 MasterySignal Protocol class（signal_name, get_value, get_weight, get_reliability）
  - [ ] 1.2 在 `backend/app/models/mastery_models.py` 中定义 FusionResult Pydantic 模型（fused_mastery, signal_details, timestamp）
  - [ ] 1.3 在 `backend/app/models/mastery_models.py` 中预留多维扩展字段
  - [ ] 1.4 编辑后运行 `ruff check`

- [ ] **Task 2: 信号注册表实现** (AC: #1, #2)
  - [ ] 2.1 创建 `backend/app/services/signal_registry.py`（或在 mastery_engine.py 内新增类 SignalRegistry）
  - [ ] 2.2 实现 SignalRegistry.register(signal: MasterySignal) / unregister(signal_name: str)
  - [ ] 2.3 实现 SignalRegistry.get_active_signals(node_id: str) → List[Tuple[str, float, float]]（返回有数据的信号列表）
  - [ ] 2.4 编辑后运行 `ruff check`

- [ ] **Task 3: 5 个 MVP 信号适配器** (AC: #2)
  - [ ] 3.1 实现 BKTMasterySignal（读取 ConceptState.p_mastery）
  - [ ] 3.2 实现 FSRSRetrievabilitySignal（读取 FSRS Card 当前 R 值）
  - [ ] 3.3 实现 ExamScoreSignal（读取近 N 次 AutoSCORE 均分，归一化到 0-1）
  - [ ] 3.4 实现 CalibrationBiasSignal（读取 Story 5.5 的 signed_bias，反转为信号值）
  - [ ] 3.5 实现 SelfConfidenceSignal（读取近 N 次自信度均值）
  - [ ] 3.6 所有信号实现 MasterySignal 协议
  - [ ] 3.7 编辑后运行 `ruff check`

- [ ] **Task 4: 融合引擎核心算法** (AC: #3)
  - [ ] 4.1 创建 `backend/app/services/mastery_fusion.py`（或在 mastery_engine.py 内新增 MasteryFusionEngine 类）
  - [ ] 4.2 实现 compute_fused_mastery(node_id: str) → FusionResult
  - [ ] 4.3 实现权重归一化逻辑（信号缺失时自动重新分配）
  - [ ] 4.4 实现钳位逻辑 [0.0, 1.0]
  - [ ] 4.5 编辑后运行 `ruff check`

- [ ] **Task 5: 与 MasteryEngine 集成** (AC: #5)
  - [ ] 5.1 修改 `mastery_engine.py` 的 effective_proficiency() 方法，内部调用融合引擎
  - [ ] 5.2 保留 min(p_mastery, R) 作为 fallback（融合引擎初始化失败或无信号数据时）
  - [ ] 5.3 在 concept_to_response() 中增加 fusion_details 字段
  - [ ] 5.4 确保 mastery_level() 阈值和行为不变（向后兼容）
  - [ ] 5.5 编辑后运行 `ruff check`

- [ ] **Task 6: 信号互补性诊断工具** (AC: #4)
  - [ ] 6.1 实现 compute_signal_correlation(signal_a, signal_b, records) → float（Pearson r）
  - [ ] 6.2 实现 run_complementarity_check() → Dict[Tuple[str,str], float]（所有信号对的相关系数）
  - [ ] 6.3 r >= 0.7 时写入日志告警
  - [ ] 6.4 编辑后运行 `ruff check`

- [ ] **Task 7: 单元测试** (AC: #7)
  - [ ] 7.1 创建 `backend/tests/unit/test_mastery_fusion.py`：
    - 信号注册/注销测试
    - 加权平均融合计算正确性
    - 信号缺失时权重重新归一化（1-5 个信号各测）
    - 全部无数据返回 0.0
    - 钳位边界测试
    - fallback 到 min(p_mastery, R) 测试
  - [ ] 7.2 创建 `backend/tests/unit/test_signal_correlation.py`：
    - Pearson r 计算正确性
    - 完全相关 (r=1.0) / 完全无关 (r≈0.0) / 高相关 (r=0.75) 测试
    - 样本不足（< 3 条）时的安全处理
  - [ ] 7.3 运行全部测试确认通过

- [ ] **Task 8: 集成验证** (AC: #3, #5)
  - [ ] 8.1 端到端测试：仅 BKT 有数据 → 融合值 = BKT 值
  - [ ] 8.2 端到端测试：BKT+FSRS 有数据 → 融合值 = 加权平均（权重重新归一化后）
  - [ ] 8.3 端到端测试：5 信号全有数据 → 融合值正确
  - [ ] 8.4 端到端测试：融合值替代 effective_proficiency 后，mastery_level 映射不变
  - [ ] 8.5 运行 `ruff check backend/app/services/mastery_engine.py backend/app/services/mastery_fusion.py` 确认 lint 通过

## Dev Notes

### 信号融合设计理据

**核心问题**：BKT 掌握概率和 FSRS 可提取性各自仅捕获学习的一个维度。Story 5.1 的 `min(p_mastery, R)` 是保守的二信号融合，但丢弃了考察评分、校准偏差等有价值信息。

**MVP 方案：加权平均**
- 简单、可解释、易调试
- 权重可基于信号可靠度动态调整（数据越多权重越高）
- 向后兼容 5.1 的 min 策略（作为 fallback）

**Phase 2+ 远期：Beta-Bayesian 融合**（[Source: architecture.md#Deferred Decisions]）
- 每个信号更新一个 Beta 分布的 α/β 参数
- 融合为后验分布的期望值
- 优势：概率论原理更严谨，能给出置信区间
- 当前不实现，但架构预留接口

### 信号互补性验收原理

**来源**: 多指标融合最佳实践——若两个信号高度相关（r >= 0.7），则其中一个是冗余的，不增加信息量反而增加计算成本。

**Pearson 相关系数 r**:
```
r = Σ((x_i - x̄)(y_i - ȳ)) / sqrt(Σ(x_i - x̄)² * Σ(y_i - ȳ)²)

判定标准:
  |r| < 0.3  → 弱相关（优秀互补）
  0.3 <= |r| < 0.7 → 中等相关（可接受）
  |r| >= 0.7 → 高度相关（告警，可能冗余）
```

### 权重动态调整策略

```
基础权重（默认）:
  BKT:         0.30
  FSRS:        0.25
  ExamScore:   0.25
  Calibration: 0.10
  Confidence:  0.10

信号缺失时重新归一化:
  例如仅 BKT + FSRS 有数据:
    w_bkt_norm = 0.30 / (0.30 + 0.25) = 0.545
    w_fsrs_norm = 0.25 / (0.30 + 0.25) = 0.455
    fused = 0.545 * bkt_value + 0.455 * fsrs_value
```

### Brownfield 上下文

- `mastery_engine.py` 已有 `effective_proficiency()` 方法（min(p_mastery, R)），需修改为调用融合引擎
- `mastery_fusion.py` / `signal_registry.py` 为新建文件
- 5 个信号适配器需要读取不同模块的数据（mastery_state, fsrs_manager, calibration_tracker）
- CalibrationBiasSignal 依赖 Story 5.5 完成

### 与其他 Story 的依赖关系

| 依赖 | 方向 | 说明 |
|------|------|------|
| Story 5.1 (BKT+FSRS) | 前置依赖 | BKT p_mastery + FSRS R 值作为信号源 |
| Story 5.5 (Calibration) | 前置依赖 | calibration_bias 作为信号源 |
| Story 5.2 (节点颜色) | 向后兼容 | mastery_level 阈值和颜色映射不变 |
| Story 5.3 (学习档案) | 后续消费 | 融合详情展示在档案面板 |
| Story 6.4 (AutoSCORE) | 间接依赖 | exam_score 信号来自 AutoSCORE 评分历史 |

### 性能约束

- 融合计算：O(K)，K = 信号数量（5），实际 O(1) 常量级
- 信号互补性诊断：O(K² * N)，K=5, N=记录数，仅诊断时运行（非关键路径）
- 不影响 NFR-PERF-06 精通度更新 < 100ms

### Project Structure Notes

- 融合引擎可选独立文件 `mastery_fusion.py` 或嵌入 `mastery_engine.py` 内——推荐独立文件，职责更清晰
- 信号适配器可选独立文件 `signal_registry.py` 或在融合引擎内定义——推荐独立文件
- 所有文件位于 `backend/app/services/` 目录
- 模型追加到 `backend/app/models/mastery_models.py`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#能力域5] — 5-6 核心信号→单维掌握度，信号互补性验收 r<0.7，N 信号动态接入架构，Phase 2 Beta-Bayesian，多维精通度 Phase 3+ 远期
- [Source: _bmad-output/planning-artifacts/architecture.md#Deferred Decisions] — N 信号→5 维 Beta-Bayesian 融合（Phase 3+）
- [Source: _bmad-output/planning-artifacts/epics.md#Story5.6] — AC 原文：信号互补性 r<0.7 + N 信号动态架构
- [Source: _bmad-output/planning-artifacts/prd.md#能力域5] — FR-MAST-06: 5-6 核心信号融合为单维掌握度

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/mastery_fusion.py` — 新建（融合引擎核心算法）
- `backend/app/services/signal_registry.py` — 新建（信号注册表 + 5 个信号适配器）
- `backend/app/models/mastery_models.py` — 追加 MasterySignal Protocol + FusionResult 模型 + 多维预留字段
- `backend/app/services/mastery_engine.py` — 修改 effective_proficiency() 调用融合引擎
- `backend/tests/unit/test_mastery_fusion.py` — 新建
- `backend/tests/unit/test_signal_correlation.py` — 新建
