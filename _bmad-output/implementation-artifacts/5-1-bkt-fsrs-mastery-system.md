# Story 5.1: BKT+FSRS 双引擎精通度系统

Status: ready-for-dev

## Story

As a 系统,
I want 为每个知识节点维护精通度状态（BKT 管掌握概率 + FSRS 管复习调度），
so that 系统能准确追踪用户的学习进度。

## Acceptance Criteria

1. **AC-1: BKT 贝叶斯知识追踪更新**
   - **Given** 用户在检验白板中被考察某个知识节点，AutoSCORE 评分完成产出 grade 1-4
   - **When** 系统接收到 grade 事件
   - **Then** BKT 执行贝叶斯后验更新 p_mastery：
     - 正确回答（grade >= 3）: `p_posterior = p_prev * (1 - P_S) / (p_prev * (1 - P_S) + (1 - p_prev) * P_G)`
     - 错误回答（grade < 3）: `p_posterior = p_prev * P_S / (p_prev * P_S + (1 - p_prev) * (1 - P_G))`
     - 学习转移: `p_new = p_posterior + (1 - p_posterior) * P_T`
     - Grade 4（Fluent）特殊处理: `P_G = 0`（流利解释无猜测可能）
   - **And** p_mastery 值钳位在 [0.001, 0.999]
   - **And** BKT 参数按难度分级使用默认先验值（easy/medium/hard）

2. **AC-2: FSRS 记忆稳定性与复习调度**
   - **Given** 同一 grade 事件
   - **When** FSRS 引擎处理 grade（1=Again, 2=Hard, 3=Good, 4=Easy）
   - **Then** FSRS Card 状态更新：stability, difficulty, state, reps, lapses, due date
   - **And** FSRS Card 序列化为 JSON 存储在 ConceptState.fsrs_card_data
   - **And** 可随时通过 FSRS Scheduler 计算当前 retrievability R
   - **And** FSRS 不可用时（py-fsrs 未安装）退化为指数衰减估算 R

3. **AC-3: effective_proficiency 融合计算**
   - **Given** 节点有 BKT p_mastery 和 FSRS retrievability R
   - **When** 任何读取精通度的请求
   - **Then** `effective_proficiency = min(p_mastery, R)`（保守策略：取掌握概率和记忆可提取性的较低值）
   - **And** effective_proficiency 为 volatile 值，每次读取时实时计算，永不存储
   - **And** 未考察过的节点（interaction_count == 0）base = 0.0

4. **AC-4: 精通度仅通过考察表现更新**
   - **Given** 任何精通度更新请求
   - **When** 更新来源为考察评分（AutoSCORE grade 1-4）
   - **Then** BKT + FSRS 正常更新
   - **And** 用户自评（Canvas 颜色变化）仅作为辅助信号，权重上限 0.5，指数衰减
   - **And** 显式 override（Sidebar 操作）权重上限 0.8，指数衰减
   - **And** 自评和 override 不可绕过考察直接设定精通度

5. **AC-5: 精通度计算性能**
   - **Given** 单节点精通度计算请求
   - **When** 调用 effective_proficiency() 或 mastery_level()
   - **Then** 计算延迟 < 100ms
   - **And** 算法复杂度 O(1)（不依赖历史交互记录数量，仅依赖当前 ConceptState 快照）
   - **And** 批量查询所有节点精通度时线性扩展 O(n)

6. **AC-6: 默认先验值初始化**
   - **Given** 首次使用系统，无任何考察数据
   - **When** 系统为新节点创建 ConceptState
   - **Then** BKT 使用默认先验值初始化：
     - easy: P_L0=0.3, P_T=0.3, P_G=0.25, P_S=0.05
     - medium（默认）: P_L0=0.1, P_T=0.2, P_G=0.20, P_S=0.10
     - hard: P_L0=0.05, P_T=0.15, P_G=0.15, P_S=0.15
   - **And** FSRS 使用 py-fsrs 默认参数（desired_retention=0.9）
   - **And** 不依赖 E6 考察数据，随考察数据积累逐步精确

7. **AC-7: 5 级精通度分级与颜色映射**
   - **Given** 节点有 effective_proficiency 值
   - **When** 系统计算 mastery_level
   - **Then** 按阈值映射为 5 级：
     - Level 0: Not Assessed（未考察，interaction_count == 0）-> #6c757d（灰）
     - Level 1: Shaky（< 0.40）-> #dc3545（红）
     - Level 2: Developing（0.40 ~ 0.70）-> #fd7e14（橙）
     - Level 3: Proficient（0.70 ~ 0.90）-> #0d6efd（蓝）
     - Level 4: Mastered（>= 0.90 且 fluent_count >= 2）-> #198754（绿）
   - **And** Level 4 需解释门控：高分但 fluent_count 不足时降为 Level 3

8. **AC-8: Neo4j 持久化与序列化**
   - **Given** BKT/FSRS 更新后的 ConceptState
   - **When** 保存到 Neo4j
   - **Then** 所有 stable 属性以 `mastery_` 前缀存储在 EntityNode 属性上
   - **And** MERGE upsert 模式（mastery_concept_id 唯一键）
   - **And** 支持 group_id 多学科隔离
   - **And** 支持从 Neo4j 属性反序列化恢复 ConceptState

9. **AC-9: API 端点完整性**
   - **Given** 后端 FastAPI 运行
   - **When** 调用精通度 API
   - **Then** 以下端点正常工作：
     - `GET /mastery/batch` — 批量查询所有节点精通度（含 volatile 字段）
     - `POST /mastery/{id}/grade` — 记录考察 grade 并更新 BKT+FSRS
     - `POST /mastery/{id}/override` — 设置显式 override
     - `POST /mastery/{id}/self-assess` — 记录自评信号
     - `DELETE /mastery/{id}/override` — 清除 override
     - `POST /mastery/graphiti-sync` — Graphiti 误解/陷阱桥接
   - **And** 所有端点以完整的 concept_to_response 格式响应（含 volatile 字段）

10. **AC-10: 单元测试 100% 覆盖**
    - **Given** mastery_engine.py + mastery_state.py + mastery_store.py
    - **When** 运行测试
    - **Then** BKT 贝叶斯更新公式测试覆盖：正确/错误/Grade4 特殊/边界值 0/1/除零保护
    - **And** FSRS 更新测试覆盖：新卡创建/4 种 rating/序列化反序列化/retrievability 计算
    - **And** effective_proficiency 测试覆盖：min(p,R) 逻辑/未考察/override 衰减/自评衰减
    - **And** mastery_level 测试覆盖：5 级阈值边界/解释门控
    - **And** freshness 测试覆盖：4 种状态
    - **And** false_mastery_risk 测试覆盖：三因子/交互不足
    - **And** 测试使用确定性数据，不依赖外部服务

## Tasks / Subtasks

- [ ] **Task 1: 审查并验证已有代码** (AC: #1-#9)
  - [ ] 1.1 对 `backend/app/services/mastery_engine.py` 执行对抗性代码审查：验证 BKT 公式实现是否与学术标准一致（Corbett & Anderson 1994），检查是否有 stub 或占位符
  - [ ] 1.2 对 `backend/app/models/mastery_state.py` 审查：验证 ConceptState 数据模型、DEFAULT_BKT_PARAMS 先验值合理性、序列化/反序列化完整性
  - [ ] 1.3 对 `backend/app/services/mastery_store.py` 审查：验证 Neo4j MERGE upsert 正确性、group_id 隔离、查询性能
  - [ ] 1.4 对 `backend/app/api/v1/endpoints/mastery.py` 审查：验证 6 个 API 端点是否为真实实现（非占位符）
  - [ ] 1.5 对 `src/memory/temporal/fsrs_manager.py` 审查：验证 py-fsrs 集成正确性、序列化/反序列化、fallback 实现
  - [ ] 1.6 产出 `[Code-Review]` 结果：每个文件标注「可复用 / 需修复 / 需重写」
  - [ ] 1.7 记录审查结果到 Graphiti `[Code-Review] 5.1 BKT+FSRS 已有代码审查`

- [ ] **Task 2: 修复已有代码缺陷** (AC: #1-#5)
  - [ ] 2.1 修复 Task 1 审查发现的所有问题（如有）
  - [ ] 2.2 确认 `mastery_engine.py` 的 FSRSManager import 路径在新架构下正确（当前 sys.path hack 需改为标准 import 或包安装）
  - [ ] 2.3 消除 `mastery_store.py` 中写死的 `cs188` group_id 默认值，改为配置化参数
  - [ ] 2.4 确认 `mastery_engine.py` 中 Grade 4 P_G=0 逻辑的学术合理性（Corbett & Anderson 1994 扩展）
  - [ ] 2.5 编辑后运行 `ruff check` + `ruff format --check` 确认 lint 通过

- [ ] **Task 3: 补充缺失功能** (AC: #3, #7)
  - [ ] 3.1 验证 `effective_proficiency()` 中 override/self-assess 衰减逻辑与 PRD FR-MAST-02「精通度仅通过考察表现更新」一致（override/self-assess 为辅助信号不可替代考察）
  - [ ] 3.2 验证 `mastery_level()` 中 Level 4 解释门控（fluent_count >= 2）是否正确实现
  - [ ] 3.3 验证 `freshness()` 分级阈值（0.90/0.70/0.50）是否合理
  - [ ] 3.4 验证 `false_mastery_risk()` 三因子权重（0.4/0.3/0.3）是否有学术依据

- [ ] **Task 4: 性能验证** (AC: #5)
  - [ ] 4.1 编写 benchmark 测试：单次 `effective_proficiency()` 调用 < 1ms（远低于 100ms 阈值）
  - [ ] 4.2 编写 benchmark 测试：批量 1000 节点 `concept_to_response()` < 100ms 总耗时
  - [ ] 4.3 确认所有计算路径为 O(1)——不涉及数据库查询或历史记录遍历

- [ ] **Task 5: 单元测试 100% 覆盖** (AC: #10)
  - [ ] 5.1 创建 `backend/tests/unit/test_mastery_engine_bkt.py`：
    - BKT 正确回答后 p_mastery 上升（各难度级别）
    - BKT 错误回答后 p_mastery 下降（各难度级别）
    - Grade 4 P_G=0 特殊路径验证
    - 边界值测试：p_mastery 接近 0 和 1 时不越界
    - 分母为 0 保护验证
    - 学习转移 P_T 正确应用
  - [ ] 5.2 创建 `backend/tests/unit/test_mastery_engine_fsrs.py`：
    - FSRS 新卡创建后首次 review
    - 4 种 rating 分别测试（Again/Hard/Good/Easy）
    - Card 序列化后反序列化后 review 完整链路
    - retrievability 计算（有 FSRS 数据 / 无 FSRS 数据 fallback）
    - FSRS 不可用时的降级路径
  - [ ] 5.3 创建 `backend/tests/unit/test_mastery_engine_effective.py`：
    - effective_proficiency = min(p_mastery, R) 核心逻辑
    - interaction_count == 0 时 base = 0.0
    - override 衰减计算（时间推移权重递减）
    - self_assess 衰减计算（2x 速度衰减）
    - override + self_assess 叠加
  - [ ] 5.4 创建 `backend/tests/unit/test_mastery_engine_level.py`：
    - 5 级阈值精确边界测试（0.399 yields L1, 0.400 yields L2, 0.699 yields L2, 0.700 yields L3, 0.899 yields L3, 0.900 yields L4）
    - 解释门控：高分但 fluent_count < 2 yields L3
    - 解释门控：高分且 fluent_count >= 2 yields L4
    - 未考察节点 yields L0
  - [ ] 5.5 创建 `backend/tests/unit/test_mastery_engine_misc.py`：
    - freshness 4 种分类
    - false_mastery_risk 三因子计算
    - set_override / clear_override / set_self_assess
    - concept_to_response 序列化完整性
    - get_review_candidates 筛选逻辑
    - apply_external_signal 三种 signal_type
  - [ ] 5.6 创建 `backend/tests/unit/test_mastery_state.py`：
    - ConceptState 默认值验证
    - to_neo4j_props 序列化所有字段
    - from_neo4j_props 反序列化所有字段（含 datetime 解析）
    - MasteryConfig 默认值验证
    - DEFAULT_BKT_PARAMS 三种难度级别参数
    - MASTERY_COLORS / MASTERY_LABELS 映射完整性
    - OVERRIDE_LEVEL_MAP / SELF_ASSESS_COLOR_MAP 映射完整性
  - [ ] 5.7 创建 `backend/tests/unit/test_mastery_store.py`（使用 stub Neo4j client）：
    - get_concept 查询正确时有结果 / 查询无结果时为 None
    - save_concept MERGE upsert
    - get_all_concepts 批量查询
    - get_or_create_concept 存在时读取 / 不存在时创建
    - record_interaction_event / record_override_event / record_self_assess_event
    - find_concept_by_name 模糊匹配
    - group_id 隔离验证
  - [ ] 5.8 创建 `backend/tests/unit/test_mastery_api.py`：
    - 6 个 API 端点集成测试（FastAPI TestClient）
    - grade 端点：grade 1-4 各测试，验证 effective_proficiency 变化方向正确
    - override 端点：设置/清除/无效 level 错误处理
    - self-assess 端点：6 种颜色映射
    - graphiti-sync 端点：3 种 signal_type + 无效 signal 错误处理
    - batch 端点：空结果 / 多概念 / topic_summary 聚合
  - [ ] 5.9 运行全部测试确认通过，生成覆盖率报告达到 100%（mastery 模块）

- [ ] **Task 6: 集成验证** (AC: #1-#9)
  - [ ] 6.1 端到端测试：创建新概念 -> grade=1 -> 验证 p_mastery 下降 -> grade=4 -> 验证 p_mastery 上升 -> 验证 effective_proficiency 正确
  - [ ] 6.2 端到端测试：连续 5 次 grade=4 -> 验证 p_mastery 收敛至高值 -> 验证 mastery_level = 4
  - [ ] 6.3 端到端测试：grade 后间隔时间 -> 验证 retrievability 衰减 -> effective_proficiency 下降
  - [ ] 6.4 运行 `ruff check backend/app/services/mastery_engine.py backend/app/models/mastery_state.py backend/app/services/mastery_store.py backend/app/api/v1/endpoints/mastery.py` 确认 lint 通过

## Dev Notes

### Brownfield 上下文——已有代码资产

本 Story 是 **Brownfield** 实施。以下模块已存在且包含**真实实现**（非占位符）：

| 文件 | 状态 | 说明 |
|------|------|------|
| `backend/app/services/mastery_engine.py` | 已实现 | BKT 贝叶斯更新 + FSRS 集成 + effective_proficiency + 5 级 mastery_level + freshness + false_mastery_risk + override/self-assess 衰减 |
| `backend/app/models/mastery_state.py` | 已实现 | ConceptState dataclass + MasteryConfig + DEFAULT_BKT_PARAMS + 颜色/标签映射 + Neo4j 序列化 |
| `backend/app/services/mastery_store.py` | 已实现 | Neo4j MERGE upsert + get/save/get_all + get_or_create + find_by_name + 事件记录 |
| `backend/app/api/v1/endpoints/mastery.py` | 已实现 | 6 个 REST 端点（batch/grade/override/self-assess/delete-override/graphiti-sync） |
| `src/memory/temporal/fsrs_manager.py` | 已实现 | py-fsrs 4.5 集成 + Card CRUD + serialization + fallback |

**核心工作**：本 Story 的主要工作是 **审查 -> 修复 -> 补测试 -> 验证**，而非从零实现。

### 已知需修复项

1. **FSRSManager import 路径**：`mastery_engine.py` 使用 `sys.path.insert` hack 导入 `src/memory/temporal/fsrs_manager.py`，需改为标准包安装或正式 import 路径
2. **group_id 固定值**：`mastery_store.py` 多处默认 `group_id="cs188"`，需改为配置化或参数传递
3. **单元测试缺失**：mastery 模块目前无专属单元测试，需从零编写达到 100% 覆盖

### BKT 贝叶斯更新公式（学术参考）

**来源**: Corbett & Anderson, "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge", 1994

```
给定:
  p_prev   = 先验 P(mastered)
  P_S      = 滑失概率 P(incorrect | mastered)
  P_G      = 猜测概率 P(correct | not mastered)
  P_T      = 转移概率 P(learn | not mastered)

Step 1 — 后验更新:
  正确回答: p_posterior = p_prev * (1-P_S) / [p_prev * (1-P_S) + (1-p_prev) * P_G]
  错误回答: p_posterior = p_prev * P_S / [p_prev * P_S + (1-p_prev) * (1-P_G)]

Step 2 — 学习转移:
  p_new = p_posterior + (1 - p_posterior) * P_T

特殊: Grade 4 (Fluent) -> P_G = 0（流利解释排除猜测）
钳位: p_new in [0.001, 0.999]
```

### FSRS 调度算法（学术参考）

**来源**: py-fsrs 库，FSRS-4.5 算法（Anki 默认算法）

- 基于遗忘曲线的记忆稳定性模型
- 4 级评分: Again(1) / Hard(2) / Good(3) / Easy(4)
- 输出: stability（记忆稳定性）、difficulty（材料难度）、due（下次复习日期）
- Retrievability R = 当前记忆可提取概率，随时间衰减

### effective_proficiency 设计理据

```
effective_proficiency = min(p_mastery, R)

- p_mastery 高但 R 低: "学过但忘了" -> effective 跟随 R 下降
- p_mastery 低但 R 高: "刚学还没掌握" -> effective 跟随 p_mastery
- 保守策略：取两者较低值，避免高估
```

**FSRS-BKT 角色边界**（[Source: architecture.md#算法架构]）：
- **FSRS** 管复习调度（假设知识项孤立，纯时间维度记忆衰减）
- **BKT** 管掌握度追踪（利用 KG 关联，贝叶斯推断掌握概率）
- 两者互补、角色不重叠

### 6 阶段增量算法集成（Phase 0 位置）

本 Story 处于 **Phase 0: MVP 核心**。搭建空框架使用默认先验值：

| Phase | 内容 | 本 Story 涉及 |
|-------|------|-------------|
| **Phase 0** | MVP 核心 6 项 + 基础 LLM+KG+FSRS | 是 — BKT+FSRS 双引擎 |
| Phase 1 | 策略适配算法 | — |
| Phase 2 | 融合算法（Beta-Bayesian） | — |
| Phase 3 | 校准追踪（Calibration Tracking） | Story 5.5 |
| Phase 4 | 高级分析（SOLO 量表等） | — |
| Phase 5 | 实验性功能 | — |

### 默认 BKT 先验值说明

| 难度 | P_L0（初始掌握） | P_T（学习率） | P_G（猜测率） | P_S（滑失率） |
|------|-----------------|-------------|-------------|-------------|
| easy | 0.30 | 0.30 | 0.25 | 0.05 |
| medium | 0.10 | 0.20 | 0.20 | 0.10 |
| hard | 0.05 | 0.15 | 0.15 | 0.15 |

来源: BKT 文献标准范围，具体值取保守中位数。新节点默认 medium。

### 性能约束

- NFR-PERF-06: 精通度更新 < 100ms（单节点 BKT+FSRS 计算）
- 算法 O(1): 仅依赖 ConceptState 当前快照，不遍历历史
- effective_proficiency 为 volatile 值，每次读取实时计算

### Project Structure Notes

- 所有已有文件路径已验证存在且非空
- `mastery_engine.py` 位于 `backend/app/services/`，符合架构文档后端目录结构
- `mastery_state.py` 位于 `backend/app/models/`，符合规范
- API 端点在 `backend/app/api/v1/endpoints/mastery.py`，路由前缀 `/mastery`
- 测试文件在 `backend/tests/unit/` 目录下创建

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#算法架构] — BKT+FSRS 双引擎设计、FSRS-BKT 角色边界、6 阶段增量算法集成
- [Source: _bmad-output/planning-artifacts/architecture.md#评分完成流] — SCORE_SUBMITTED -> mastery_engine(BKT+FSRS) -> BKT_UPDATED 事件流
- [Source: _bmad-output/planning-artifacts/prd.md#能力域5] — FR-MAST-01~06 精通度需求
- [Source: _bmad-output/planning-artifacts/prd.md#性能] — NFR-PERF-06 精通度更新 < 100ms
- [Source: _bmad-output/planning-artifacts/prd.md#可维护性] — NFR-MAINT-03 算法单元测试 100% 覆盖
- [Source: _bmad-output/planning-artifacts/epics.md#Story5.1] — AC 原文
- [Source: backend/app/services/mastery_engine.py] — BKT+FSRS 已有实现
- [Source: backend/app/models/mastery_state.py] — ConceptState + BKT 参数
- [Source: backend/app/services/mastery_store.py] — Neo4j 持久化层
- [Source: backend/app/api/v1/endpoints/mastery.py] — REST API 端点
- [Source: src/memory/temporal/fsrs_manager.py] — FSRS py-fsrs 集成

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/mastery_engine.py` — 审查+修复
- `backend/app/models/mastery_state.py` — 审查+修复
- `backend/app/services/mastery_store.py` — 审查+修复
- `backend/app/api/v1/endpoints/mastery.py` — 审查+修复
- `src/memory/temporal/fsrs_manager.py` — 审查（import 路径修复）
- `backend/tests/unit/test_mastery_engine_bkt.py` — 新建
- `backend/tests/unit/test_mastery_engine_fsrs.py` — 新建
- `backend/tests/unit/test_mastery_engine_effective.py` — 新建
- `backend/tests/unit/test_mastery_engine_level.py` — 新建
- `backend/tests/unit/test_mastery_engine_misc.py` — 新建
- `backend/tests/unit/test_mastery_state.py` — 新建
- `backend/tests/unit/test_mastery_store.py` — 新建
- `backend/tests/unit/test_mastery_api.py` — 新建
