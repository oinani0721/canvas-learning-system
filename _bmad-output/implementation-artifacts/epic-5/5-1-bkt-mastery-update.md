---
story_id: "5.1"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["4.6"]
blocks: ["5.2", "5.3"]
trace:
  - "FR-MAST-01"
---

# Story 5.1: BKT 掌握概率更新

Status: ready-for-dev

## Story
As a 系统,
I want 使用 BKT（Bayesian Knowledge Tracing）模型实时更新每个概念的掌握概率,
So that 掌握度 p_mastery 反映学习者对该概念的真实水平（Corbett & Anderson 1995）。

## Acceptance Criteria

1. **Given** 考察评分完成（grade 1-4 由 Story 4.6 AutoSCORE 产生）**When** 系统调用 `update_bkt` MCP 工具 **Then** p_mastery 基于 BKT 贝叶斯后验公式更新：correct 时 `p_posterior = p_prev*(1-P_S) / (p_prev*(1-P_S) + (1-p_prev)*P_G)`，incorrect 时 `p_posterior = p_prev*P_S / (p_prev*P_S + (1-p_prev)*(1-P_G))`，之后学习转移 `p_new = p_posterior + (1-p_posterior)*P_T` **And** 结果 clamp 到 [0.001, 0.999]

2. **Given** 一个从未被考察过的新概念 **When** 首次调用 `update_bkt` **Then** p_mastery 初始先验为 0.30（而非 mastery_state.py 中 ConceptState 默认的 0.1）**And** 先验值来自 `DEFAULT_BKT_PARAMS[difficulty]["P_L0"]` 配置 **And** 难度默认为 "easy"（P_L0=0.30）除非 frontmatter 指定其他难度

3. **Given** BKT 更新完成 **When** 系统写回 frontmatter **Then** `bkt_p_mastery` 字段更新为新的 p_mastery 值 **And** `mastery_updated_at` 更新为当前 UTC 时间戳 **And** 写入原子性（中途失败不留半截数据）

4. **Given** grade=4（Fluent）**When** BKT 更新 **Then** P_G 设为 0.0（学生流利解释时不存在猜对）**And** p_mastery 上升幅度大于 grade=3 的情况

5. **Given** 高 p_mastery（>0.7）的概念答错（grade 1 或 2）**When** BKT 更新 **Then** surprise_failures 计数器 +1 **And** 该信号可被下游 5.3 融合引擎使用

6. **Given** `update_bkt` 被调用但缺少上一步的 pipeline_token **When** 后端验证 token **Then** 返回 PIPELINE_TOKEN_INVALID 拒绝执行（AR8 评分链完整性，详见 Story 5.4）

## Tasks / Subtasks

- [ ] Task 1: 实现 update_bkt MCP 工具端点 (AC: #1, #4, #6)
  - [ ] 在 `backend/app/mcp/tools/mastery_tools.py` 创建 `update_bkt` 工具函数
  - [ ] 定义 `UpdateBktInput`（node_id, session_id, grade, pipeline_token）和 `UpdateBktOutput` Pydantic schema
  - [ ] 调用 `MasteryEngine.update_on_interaction()` 执行 BKT 更新
  - [ ] 验证 pipeline_token（调用 `PipelineTokenManager.validate_token`）
  - [ ] grade=4 时验证 P_G=0.0 特殊路径
  - [ ] 返回 updated p_mastery + 新 pipeline_token 供下游 FSRS 使用

- [ ] Task 2: 实现新概念默认先验 0.30 逻辑 (AC: #2)
  - [ ] 修改 `MasteryEngine._bkt_update` 或调用方，检测首次考察（interaction_count == 0）
  - [ ] 首次考察时使用 `DEFAULT_BKT_PARAMS[difficulty]["P_L0"]` 作为 p_prev
  - [ ] 默认难度为 "easy"（P_L0=0.30），可被 frontmatter `bkt_difficulty` 覆盖
  - [ ] 单元测试：新概念首次更新后 p_mastery 基于 0.30 先验计算

- [ ] Task 3: 实现 frontmatter 写回 (AC: #3)
  - [ ] 创建 `write_bkt_to_frontmatter(node_id, p_mastery, timestamp)` 函数
  - [ ] 使用原子写入模式（写临时文件 → rename）
  - [ ] 更新 `bkt_p_mastery` 和 `mastery_updated_at` 两个字段
  - [ ] 单元测试：写入后读回验证字段值正确

- [ ] Task 4: surprise_failures 追踪 (AC: #5)
  - [ ] 验证 `MasteryEngine.update_on_interaction` 中已有的 surprise_failures 逻辑
  - [ ] 确保 surprise_failures 写入 ConceptState 并持久化
  - [ ] 单元测试：p_mastery>0.7 + grade<3 时 surprise_failures 递增

- [ ] Task 5: MCP server 注册 + 集成测试 (AC: #1, #6)
  - [ ] 在 `backend/app/mcp/server.py` 注册 update_bkt 路由
  - [ ] 集成测试：完整调用链 MCP → MasteryEngine → frontmatter 写回
  - [ ] 集成测试：无 pipeline_token 时拒绝

## Dev Notes

### Architecture
- BKT 是 Corbett & Anderson (1995) 的标准实现，4 参数模型：P_L0（初始先验）、P_T（学习转移）、P_G（猜对率）、P_S（失误率）
- 现有 `MasteryEngine._bkt_update()` 已实现完整的贝叶斯后验更新，本 Story 的核心工作是将其包装为 MCP 工具 + frontmatter 写回
- 先验 0.30 的变更：PRD §1.5 要求新概念 BKT=0.30，但 `ConceptState.p_mastery` 默认 0.1——需要区分"系统默认"和"首次考察先验"

### File Paths
- BKT 核心算法：`backend/app/services/mastery_engine.py` (MasteryEngine._bkt_update, line 216-264)
- BKT 参数：`backend/app/models/mastery_state.py` (DEFAULT_BKT_PARAMS, line 25-29)
- ConceptState：`backend/app/models/mastery_state.py` (line 69-89)
- Pipeline token：`backend/app/mcp/pipeline_token.py` (PipelineTokenManager)
- MCP server：`backend/app/mcp/server.py`
- MCP 工具目录：`backend/app/mcp/tools/`

### Testing
- 单元测试覆盖：贝叶斯更新公式正确性、先验 0.30、grade=4 P_G=0 特殊路径、surprise_failures
- 集成测试覆盖：MCP 工具 → MasteryEngine → frontmatter 写回完整链路
- 边界测试：p_mastery 极值 0.001/0.999 clamp、重复更新幂等性

### References
- **From PRD**: §1.5 BKT+FSRS+5 信号融合 (line 599-681)
- Corbett & Anderson (1995): Bayesian Knowledge Tracing, UMUAI 4(4):253-278
- `backend/app/mcp/pipeline_token.py`: PIPELINE_STEPS 定义 score_answer → update_bkt 合法转移

## UAT Script

> 1. 打开一个新的 wiki/concepts/ 笔记（从未被考察过）
> 2. 触发考察并完成一道题（获得 grade 3）
> 3. 检查笔记 frontmatter，确认 `bkt_p_mastery` 从默认值更新（基于 0.30 先验）
> 4. 再做一道题获得 grade 4（Fluent）
> 5. 确认 `bkt_p_mastery` 上升幅度明显大于 grade 3 时的上升
> 6. 故意答错一道题（grade 1），确认 `bkt_p_mastery` 下降
> 7. 确认 `mastery_updated_at` 每次都更新为最新时间

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| BKT 贝叶斯更新 | unit | `pytest tests/unit/test_bkt_update.py -x` | 0 failures |
| 先验 0.30 | unit | `pytest tests/unit/test_bkt_prior.py -x` | 0 failures |
| Grade 4 P_G=0 | unit | `pytest tests/unit/test_bkt_fluent.py -x` | 0 failures |
| Pipeline token 验证 | unit | `pytest tests/unit/test_pipeline_token_bkt.py -x` | 0 failures |
| MCP → frontmatter | integration | `pytest tests/integration/test_bkt_mcp_chain.py -x` | 0 failures |

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
