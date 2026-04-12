---
doc_type: story
story_id: "5.6"
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

# Story 5.6: AI 评分投票反馈

## Story

As a 学习者,
I want 对 AI 评分投票反馈（准确 / 偏高 / 偏低）,
so that 评分系统可以根据我的反馈持续改进。

## Acceptance Criteria

1. **Given** 系统展示评分结果
   **When** 学习者看到分数
   **Then** 出现三个投票按钮：准确 / 偏高 / 偏低
   **And** 学习者点击后投票结果存储到 Graphiti
   **And** 投票是可选的（可以不投票直接继续）

2. **Given** 学习者点击投票按钮
   **When** Graphiti 写入触发
   **Then** 投票结果立即（乐观更新）在 UI 显示为已选中状态
   **And** Graphiti 写入异步执行（不阻塞 UI）
   **And** Graphiti 写入失败时 UI 显示静默失败（不弹错误框，只更改按钮状态为灰色）

3. **Given** 学习者已经投票
   **When** 学习者尝试再次投票（点击不同选项）
   **Then** 允许修改投票（覆盖上一次投票）
   **And** Graphiti 更新对应 episode 的投票字段

4. **Given** Graphiti 存储了足量投票数据（某评分标准 >= 20 票）
   **When** 开发者查询投票统计
   **Then** 可通过 `GET /api/v1/mastery/vote-stats` 查询特定评分标准的"偏高/准确/偏低"分布
   **And** 用于未来 prompt 优化决策（本 Story 不自动调整 prompt）

## Tasks / Subtasks

- [ ] Task 1: 投票数据模型 (AC: #1, #3)
  - [ ] 1.1 在 `backend/app/schemas/vote.py` 定义 `VoteValue` enum：`ACCURATE = "accurate"`, `TOO_HIGH = "too_high"`, `TOO_LOW = "too_low"`
  - [ ] 1.2 定义 `ScoreVote` Pydantic 模型：`question_id: str, note_id: str, vote: VoteValue, actual_score: float, voter_timestamp: datetime`
  - [ ] 1.3 定义 `VoteUpdate` 模型（用于覆盖更新）：`question_id: str, new_vote: VoteValue`

- [ ] Task 2: Graphiti episode 写入 (AC: #1, #2)
  - [ ] 2.1 在 `backend/app/services/graphiti_service.py` 实现 `write_score_vote(vote: ScoreVote) -> str`（返回 episode_uuid）
  - [ ] 2.2 episode 内容格式：`"AI对[note_id]的评分[actual_score]被学习者投票为[vote]"`
  - [ ] 2.3 Graphiti 写入通过异步队列（Story 5.8 机制），不阻塞调用方
  - [ ] 2.4 实现 `update_score_vote(episode_uuid: str, new_vote: VoteValue) -> None` 处理修改投票

- [ ] Task 3: API 端点 (AC: #1, #2, #3, #4)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/mastery.py` 创建 `POST /api/v1/mastery/score-vote` 端点
  - [ ] 3.2 请求体：`ScoreVote`；响应体：`{"episode_id": str, "status": "queued"}`（乐观响应）
  - [ ] 3.3 创建 `PUT /api/v1/mastery/score-vote/{question_id}` 端点处理修改投票
  - [ ] 3.4 创建 `GET /api/v1/mastery/vote-stats` 端点，query param `note_id` 或 `question_id`，返回三类投票计数

- [ ] Task 4: 前端投票组件（接口定义）(AC: #1, #2)
  - [ ] 4.1 定义前端投票组件的 props 接口：`{ questionId: string, noteId: string, actualScore: number, onVote?: (vote: VoteValue) => void }`
  - [ ] 4.2 定义前端状态：`pendingVote: VoteValue | null, submittedVote: VoteValue | null, isSubmitting: boolean, hasFailed: boolean`
  - [ ] 4.3 乐观更新逻辑：点击后立即设置 `submittedVote`，异步确认后保持；失败时设置 `hasFailed=true` 将按钮置灰
  - [ ] 4.4 前端组件实现在 `frontend/src/components/ScoreVoteWidget.tsx`（本 Story 仅定义接口，实现在 Epic 4）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 `tests/unit/test_score_vote_service.py`：验证 Graphiti 写入和更新逻辑
  - [ ] 5.2 `tests/unit/test_vote_stats.py`：验证投票统计聚合（各类计数正确）
  - [ ] 5.3 `tests/integration/test_score_vote_endpoint.py`：验证 POST/PUT/GET 端点的完整 HTTP 流程

## Dev Notes

- **乐观更新**：前端不等 Graphiti 写入确认就显示"已选中"状态，提升体验。失败时降级为静默灰色（不弹 toast 打断学习流）
- **estimate 2h**：投票逻辑简单，主要工作是 Graphiti episode 格式设计和乐观更新状态机
- **投票数据用途**：本 Story 只存储，不自动调整 prompt。20 票阈值是统计可靠性下限（p < 0.05 二项分布）
- **修改投票**：允许修改避免误点情况。Graphiti 更新用 `edit_memory_facts` 或直接创建新 episode 覆盖（根据 Graphiti API 实际能力决定）
- **与 Story 5.8 的关系**：写入通过 AsyncQueue，失败重试由 5.8 机制处理，本 Story 不直接实现重试

### Project Structure Notes

- Pydantic 模型：`backend/app/schemas/vote.py`（新建）
- Graphiti 扩展：`backend/app/services/graphiti_service.py`（扩展 write_score_vote）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（新增 /score-vote, /vote-stats）
- 前端接口定义：`frontend/src/components/ScoreVoteWidget.tsx`（接口定义，实现在 Epic 4）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.6] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR25] — AI 评分投票反馈需求
- [Story: 5.8] — 异步写入队列机制

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证评分后出现三个投票按钮** (AC: #1)
   - 完成任意一道考察题并看到 AI 评分
   - 评分结果下方应出现三个按钮："准确" / "偏高" / "偏低"
   - 如果没有这三个按钮，记录 Story 5.6

2. **验证投票可选（可以不投票）** (AC: #1)
   - 看到三个按钮后，不点任何按钮，直接点"继续"或开始下一题
   - 系统应该正常继续，不强制要求投票
   - 如果系统阻止继续或报错，记录 Story 5.6

3. **验证点击投票后按钮高亮** (AC: #2)
   - 点击"偏高"按钮
   - 该按钮应立即变为选中状态（颜色高亮）
   - 如果点击后没有任何反应或需要等待才高亮，记录 Story 5.6

4. **验证可以修改投票** (AC: #3)
   - 先点"偏高"（变为高亮），再点"准确"
   - "准确"应变高亮，"偏高"应取消高亮
   - 如果不能切换，记录 Story 5.6

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.6.1 | pytest | `.venv/bin/pytest tests/unit/test_score_vote_service.py -x -q` | 0 failed |
| CP-5.6.2 | pytest | `.venv/bin/pytest tests/unit/test_vote_stats.py -x -q` | 0 failed |
| CP-5.6.3 | pytest | `.venv/bin/pytest tests/integration/test_score_vote_endpoint.py -x -q` | 0 failed |

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
