---
doc_type: story
story_id: "5.2"
epic_id: "EPIC-5"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 5.2: FSRS 复习间隔计算

## Story

As a 系统,
I want 使用 FSRS（Free Spaced Repetition Scheduler）算法计算每个概念的最优复习间隔,
so that 学习者可以在记忆衰退前得到复习提醒。

## Acceptance Criteria

1. **Given** 学习者完成某概念的考察
   **When** 评分结果写入
   **Then** FSRS 算法根据难度、稳定性、可提取性计算下次 due_date
   **And** due_date 写入概念笔记的 frontmatter
   **And** 多次练习后 FSRS 参数根据实际表现动态调整

2. **Given** 某概念第一次考察（无 FSRS 历史）
   **When** 需要计算 due_date
   **Then** 使用 FSRS 初始参数（difficulty=5.0, stability=1.0, retrievability=1.0）
   **And** 第一次间隔固定为 1 天（FSRS 新卡片规则）

3. **Given** 学习者答题评分为 1（Again）/ 2（Hard）/ 3（Good）/ 4（Easy）
   **When** FSRS 更新触发
   **Then** stability 和 difficulty 按 FSRS v5 公式更新
   **And** 间隔 = stability * ln(FSRS_REQUEST_RETENTION) / ln(0.9)（可配置 REQUEST_RETENTION，默认 0.9）
   **And** due_date = today + interval（四舍五入到整天）

4. **Given** FSRS 参数写入 frontmatter 时文件锁定
   **When** 写入失败
   **Then** 操作回滚，不留中间状态（NFR-INT-1）
   **And** 写入失败不影响当前考察会话继续

## Tasks / Subtasks

- [ ] Task 1: 集成 FSRS v5 算法库 (AC: #1, #2, #3)
  - [ ] 1.1 安装 `fsrs` Python 库（`pip install fsrs`），版本锁定到 `fsrs>=1.0.0`
  - [ ] 1.2 在 `backend/app/services/mastery_service.py` 实现 `fsrs_update(fsrs_params: FSRSParams, rating: int) -> FSRSParams`
  - [ ] 1.3 rating 映射：correct=3(Good), partial=2(Hard), incorrect=1(Again)（与 BKT Story 5.1 对齐）
  - [ ] 1.4 实现 `calculate_due_date(stability: float, request_retention: float = 0.9) -> date`
  - [ ] 1.5 REQUEST_RETENTION 可通过 `backend/app/core/config.py` 中 `FSRS_REQUEST_RETENTION` 配置

- [ ] Task 2: FSRSParams Pydantic 模型 (AC: #1, #2)
  - [ ] 2.1 在 `backend/app/schemas/mastery.py` 定义 `FSRSParams`：`difficulty: float, stability: float, retrievability: float, due_date: Optional[date], last_review: Optional[date], review_count: int`
  - [ ] 2.2 初始值常量：`FSRS_INITIAL_PARAMS = FSRSParams(difficulty=5.0, stability=1.0, retrievability=1.0, due_date=None, last_review=None, review_count=0)`
  - [ ] 2.3 first-review 逻辑：`review_count == 0` 时 interval=1（固定 1 天），跳过 stability 公式

- [ ] Task 3: 读写 frontmatter fsrs_params (AC: #1, #4)
  - [ ] 3.1 扩展 `backend/app/services/frontmatter_service.py`：`read_fsrs_params(note_path: str) -> FSRSParams`
  - [ ] 3.2 实现 `write_fsrs_params(note_path: str, fsrs_params: FSRSParams) -> None`（原子写入，同 Story 5.1 机制）
  - [ ] 3.3 frontmatter 缺失 fsrs_params 时注入 FSRS_INITIAL_PARAMS 默认值
  - [ ] 3.4 due_date 序列化为 ISO 8601 字符串（`"2026-04-15"`）存入 frontmatter

- [ ] Task 4: API 端点 (AC: #1, #3)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/mastery.py` 创建 `POST /api/v1/mastery/fsrs-update` 端点
  - [ ] 4.2 请求体：`NoteId, rating: Literal[1, 2, 3, 4]`（1=Again, 2=Hard, 3=Good, 4=Easy）
  - [ ] 4.3 响应体：`fsrs_params: FSRSParams, due_date: date, interval_days: int`
  - [ ] 4.4 同时更新 frontmatter 中的 `last_reviewed` 字段为当天日期

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 `tests/unit/test_fsrs_algorithm.py`：验证 FSRS 公式对四种 rating 的数值输出（基准值与 fsrs 官方测试向量对齐）
  - [ ] 5.2 `tests/unit/test_fsrs_first_review.py`：验证第一次评分 interval=1 固定规则
  - [ ] 5.3 `tests/unit/test_fsrs_due_date.py`：验证 due_date 计算（stability=7.0, retention=0.9 → interval≈7天）
  - [ ] 5.4 `tests/integration/test_mastery_fsrs_update.py`：端到端 POST 请求验证 frontmatter 更新

## Dev Notes

- **FSRS v5 算法**：来自 Jarrett Ye (L-M-Sheep) 的 FSRS-5 论文，PyPI 包 `fsrs` 是官方 Python 实现
- **间隔公式**：I(r, S) = S * (r^(1/c) - 1)，其中 c 由 REQUEST_RETENTION 决定。简化版：interval = S * ln(REQUEST_RETENTION) / ln(0.9)
- **stability vs retrievability**：stability 是长期记忆强度（天），retrievability = e^(-t/S) 是当前记忆可提取概率
- **fsrs 库版本**：截至 2026-04，fsrs 包最新为 v1.x，API 为 `fsrs.FSRS().next_card(card, rating)`
- **与 BKT 并行**：FSRS 和 BKT 是独立计算，都在 Story 5.3 中融合。两个更新可以在同一个 API 调用中串联执行

### Project Structure Notes

- 核心服务：`backend/app/services/mastery_service.py`（与 Story 5.1 共享同一文件）
- Pydantic 模型：`backend/app/schemas/mastery.py`（与 Story 5.1 共享）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（与 Story 5.1 共享文件，新增端点）
- 配置项：`backend/app/core/config.py`（添加 FSRS_REQUEST_RETENTION=0.9）
- 参考样式：`backend/app/services/rag_service.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.2] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR20] — FSRS 复习间隔需求
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — fsrs_params 字段定义
- [Algorithm: FSRS-5 Paper] — https://github.com/open-spaced-repetition/fsrs5

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证复习日期自动设置** (AC: #1)
   - 完成某概念的一次考察并给出评分
   - 打开该概念笔记，frontmatter 中应有 `due_date` 字段，显示一个未来日期
   - 如果 `due_date` 是今天或过去的日期，记录 Story 5.2

2. **验证全新概念第一次复习间隔为 1 天** (AC: #2)
   - 对一个从未考察过的概念完成第一次考察
   - 打开笔记，`due_date` 应该是明天的日期
   - 如果 `due_date` 是一周后或更远，记录 Story 5.2

3. **验证多次练习后间隔延长** (AC: #3)
   - 对同一概念连续答对 3 次（每次都给"答对"评分）
   - 比较每次考察后的 `due_date`：第 1 次→1天后，第 2 次→几天后，第 3 次→更长
   - 如果间隔没有递增，记录 Story 5.2 和每次的 due_date

4. **验证答错后间隔缩短** (AC: #3)
   - 找一个已有较长间隔（due_date 在很远将来）的熟练概念
   - 故意答错一次，再查看 due_date
   - due_date 应该比之前近了（间隔缩短）
   - 如果 due_date 没有变近，记录 Story 5.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.2.1 | pytest | `.venv/bin/pytest tests/unit/test_fsrs_algorithm.py -x -q` | 0 failed |
| CP-5.2.2 | pytest | `.venv/bin/pytest tests/unit/test_fsrs_first_review.py -x -q` | 0 failed |
| CP-5.2.3 | pytest | `.venv/bin/pytest tests/unit/test_fsrs_due_date.py -x -q` | 0 failed |
| CP-5.2.4 | pytest | `.venv/bin/pytest tests/integration/test_mastery_fsrs_update.py -x -q` | 0 failed |

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
