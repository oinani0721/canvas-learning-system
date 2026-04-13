---
story_id: "5.2"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["5.1"]
blocks: ["5.3", "7.1"]
trace:
  - "FR-MAST-02"
---

# Story 5.2: FSRS 复习间隔计算

Status: ready-for-dev

## Story
As a 系统,
I want 使用 FSRS（Free Spaced Repetition Scheduler）算法计算最优复习间隔,
So that 学习者在记忆衰退前得到科学安排的复习提醒（Ye et al. 2024, 比 SM-2 减少 20-30% 复习次数）。

## Acceptance Criteria

1. **Given** BKT 更新完成（Story 5.1 产生的 pipeline_token 有效）**When** 系统调用 `update_fsrs` MCP 工具 **Then** FSRS DSR 三元组更新：Difficulty（难度）、Stability（记忆稳定性/天）、Retrievability（即时检索概率）**And** 计算 `next_review_at` 日期 **And** pipeline_token 被消费并产生新 token 供下游校准步骤使用

2. **Given** FSRS 更新完成 **When** 系统写回 frontmatter **Then** 以下字段全部更新：`fsrs_difficulty`、`fsrs_stability`、`fsrs_retrievability`、`fsrs_next_review_at`、`mastery_updated_at` **And** 写入原子性（中途失败不留半截数据）

3. **Given** 学习者对某概念连续 grade=4（Fluent）**When** FSRS 计算复习间隔 **Then** Stability 持续增长，next_review_at 间隔越来越长（自适应特性）**And** Difficulty 逐步下降

4. **Given** 学习者对某概念 grade=1（Forgot）**When** FSRS 计算复习间隔 **Then** Stability 大幅下降（接近重置）**And** next_review_at 设为近期（1-2 天内）**And** Difficulty 上升

5. **Given** FSRSManager 不可用（导入失败）**When** 系统尝试 FSRS 更新 **Then** 降级为仅 BKT 更新（不中断流程）**And** 日志记录降级事件 **And** frontmatter fsrs_* 字段保持上一次值不变

6. **Given** `update_fsrs` 被调用但缺少上一步（score_answer）的 pipeline_token **When** 后端验证 token **Then** 返回 PIPELINE_TOKEN_INVALID 拒绝执行（AR8）

## Tasks / Subtasks

- [ ] Task 1: 实现 update_fsrs MCP 工具端点 (AC: #1, #6)
  - [ ] 在 `backend/app/mcp/tools/mastery_tools.py` 创建 `update_fsrs` 工具函数
  - [ ] 定义 `UpdateFsrsInput`（node_id, session_id, answer_quality, pipeline_token）和 `UpdateFsrsOutput` Pydantic schema
  - [ ] 调用 `MasteryEngine._fsrs_update()` 执行 FSRS DSR 计算
  - [ ] 验证 pipeline_token（score_answer → update_fsrs 合法转移）
  - [ ] 返回 updated DSR + next_review_at + 新 pipeline_token

- [ ] Task 2: 实现 frontmatter 写回 (AC: #2)
  - [ ] 创建 `write_fsrs_to_frontmatter(node_id, difficulty, stability, retrievability, next_review_at, timestamp)` 函数
  - [ ] 使用原子写入模式（写临时文件 → rename）
  - [ ] 单个写操作更新所有 5 个 fsrs_* 字段 + mastery_updated_at
  - [ ] 单元测试：写入后读回验证所有字段值正确

- [ ] Task 3: 自适应间隔验证 (AC: #3, #4)
  - [ ] 单元测试：连续 grade=4 后 stability 递增、next_review_at 间隔递增
  - [ ] 单元测试：grade=1 后 stability 大幅下降、next_review_at 近期
  - [ ] 单元测试：difficulty 随 grade 变化正确调整

- [ ] Task 4: FSRS 不可用降级 (AC: #5)
  - [ ] 验证 `FSRS_ENGINE_AVAILABLE` 标志位已存在于 mastery_engine.py
  - [ ] 在 update_fsrs MCP 工具中检查 FSRS 可用性，不可用时返回降级响应
  - [ ] 降级时 status="degraded"，message 说明原因
  - [ ] 单元测试：mock FSRS_ENGINE_AVAILABLE=False 时降级路径正确

- [ ] Task 5: MCP server 注册 + 集成测试 (AC: #1, #2)
  - [ ] 在 `backend/app/mcp/server.py` 注册 update_fsrs 路由
  - [ ] 集成测试：score_answer → update_fsrs 完整 token 链
  - [ ] 集成测试：frontmatter 写回后 Dataview 可查询 next_review_at

## Dev Notes

### Architecture
- FSRS 是 Ye et al. (2024) 的开源间隔复习调度器，19 参数神经网络模型
- DSR 三元组：Difficulty（概念对该学生的难度）、Stability（记忆半衰期/天）、Retrievability（当前即时检索概率，随时间衰减）
- 现有 `FSRSManager` 在 `backend/lib/memory/temporal/fsrs_manager.py` 已封装 FSRS 核心算法
- `MasteryEngine._fsrs_update()` 已实现 FSRS Card/State 更新逻辑
- 本 Story 的核心工作是 MCP 工具包装 + frontmatter 写回 + 自适应验证

### File Paths
- FSRS 管理器：`backend/lib/memory/temporal/fsrs_manager.py`
- FSRS 更新逻辑：`backend/app/services/mastery_engine.py` (MasteryEngine._fsrs_update)
- ConceptState FSRS 字段：`backend/app/models/mastery_state.py` (fsrs_stability, fsrs_difficulty, fsrs_state, line 86-88)
- Pipeline token：`backend/app/mcp/pipeline_token.py` (PIPELINE_STEPS: score_answer → update_fsrs)
- MCP 工具目录：`backend/app/mcp/tools/`
- frontmatter schema：anchor PRD §1.5 (line 632-648)

### Testing
- 单元测试覆盖：DSR 计算正确性、自适应间隔特性、降级路径
- 集成测试覆盖：MCP token 链（score_answer → update_fsrs）、frontmatter 写回
- 属性测试：任意 grade 序列后 stability 始终 >= 0、next_review_at 始终在未来

### References
- **From PRD**: §1.5 BKT+FSRS+5 信号融合 (line 599-681)
- Ye et al. (2024): Free Spaced Repetition Scheduler, open-source
- `backend/app/mcp/pipeline_token.py`: PIPELINE_STEPS 定义 score_answer → [update_fsrs, update_bkt]

## UAT Script

> 1. 完成一道考察题（grade 3），确认 frontmatter 出现 fsrs_stability 和 fsrs_next_review_at
> 2. 连续答对 3 道题（grade 4），观察 fsrs_stability 持续增长
> 3. 确认 fsrs_next_review_at 间隔越来越远（如从 3 天 → 7 天 → 14 天）
> 4. 故意答错 1 道题（grade 1），确认 fsrs_stability 大幅下降
> 5. 确认 fsrs_next_review_at 回到近期（1-2 天内）
> 6. 用 Dataview 查询 `WHERE fsrs_next_review_at <= date(today)` 确认可检索到需复习的概念

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| FSRS DSR 计算 | unit | `pytest tests/unit/test_fsrs_update.py -x` | 0 failures |
| 自适应间隔 | unit | `pytest tests/unit/test_fsrs_adaptive.py -x` | 0 failures |
| FSRS 降级 | unit | `pytest tests/unit/test_fsrs_degradation.py -x` | 0 failures |
| Pipeline token 链 | unit | `pytest tests/unit/test_pipeline_token_fsrs.py -x` | 0 failures |
| MCP → frontmatter | integration | `pytest tests/integration/test_fsrs_mcp_chain.py -x` | 0 failures |

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
