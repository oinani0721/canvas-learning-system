---
doc_type: story
story_id: "5.1"
aliases: ["5.1"]
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
# Story 5.1: BKT 模型实时更新掌握概率

## Story

As a 系统,
I want 使用 BKT（Bayesian Knowledge Tracing）模型实时更新每个概念的掌握概率,
so that 系统始终拥有学习者对每个概念的最新掌握估计。

## Acceptance Criteria

1. **Given** 学习者完成一道关于概念 X 的考察题
   **When** 评分结果产生（正确/部分正确/错误）
   **Then** 系统用贝叶斯更新公式计算 X 的新 mastery_score
   **And** 更新后的 mastery_score 写入 X 笔记的 frontmatter
   **And** 更新过程原子性保证（NFR-INT-1）

2. **Given** 学习者第一次考察某概念（无历史数据）
   **When** BKT 更新触发
   **Then** 系统使用默认先验参数（p_know=0.1, p_guess=0.25, p_slip=0.1, p_transit=0.3）初始化 bkt_params
   **And** 贝叶斯更新在默认先验基础上正常执行

3. **Given** frontmatter 写入失败（IO 错误或文件锁定）
   **When** 原子写入尝试失败
   **Then** 系统回滚到前一个 mastery_score（不留中间状态）
   **And** 记录错误日志，不向学习者显示崩溃界面

## Tasks / Subtasks

- [ ] Task 1: 实现 BKT 贝叶斯更新核心算法 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/mastery_service.py` 实现 `bkt_update(p_know, p_guess, p_slip, p_transit, is_correct: bool) -> float`
  - [ ] 1.2 贝叶斯更新公式：P(Know|correct) = P(correct|Know)*P(Know) / P(correct)，其中 P(correct) = P(Know)*(1-p_slip) + (1-P(Know))*p_guess
  - [ ] 1.3 实现负向（答错）更新：P(Know|incorrect) = P(slip)*P(Know) / P(incorrect)
  - [ ] 1.4 实现 `transit_update(p_know_posterior) -> float`：P(Know_t+1) = P(Know_posterior) + (1-P(Know_posterior)) * p_transit

- [ ] Task 2: 读写 frontmatter bkt_params (AC: #1, #2)
  - [ ] 2.1 在 `backend/app/services/frontmatter_service.py` 实现 `read_bkt_params(note_path: str) -> BKTParams` 解析 YAML frontmatter
  - [ ] 2.2 实现 `write_mastery_score(note_path: str, score: float, bkt_params: BKTParams) -> None` 原子写（先写临时文件再 rename）
  - [ ] 2.3 BKTParams Pydantic 模型：`p_know: float, p_guess: float, p_slip: float, p_transit: float`
  - [ ] 2.4 frontmatter 缺失 bkt_params 时自动注入默认值（不覆盖现有字段）

- [ ] Task 3: 集成评分结果触发器 (AC: #1)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/mastery.py` 创建 `POST /api/v1/mastery/bkt-update` 端点
  - [ ] 3.2 请求体：`NoteId, score_result: Literal["correct", "partial", "incorrect"]`
  - [ ] 3.3 "partial" 答案映射为 0.5 概率正确（is_correct=True with weight 0.5）
  - [ ] 3.4 响应体：`new_mastery_score: float, bkt_params: BKTParams, updated_at: datetime`

- [ ] Task 4: 原子写入保护 (AC: #3)
  - [ ] 4.1 frontmatter 写入使用 Python `tempfile.NamedTemporaryFile` + `os.replace` 确保原子性
  - [ ] 4.2 获取文件锁（`filelock` 库）防止并发写入冲突
  - [ ] 4.3 写入失败时 `structlog` 记录 error 级别日志（含 note_path, previous_score, attempted_score）
  - [ ] 4.4 写入失败返回 500 with `{"error": "mastery_write_failed", "current_score": <previous_value>}`

- [ ] Task 5: 编写测试 (AC: #1, #2, #3)
  - [ ] 5.1 `tests/unit/test_bkt_algorithm.py`：验证贝叶斯更新公式数值正确性（正确/错误/partial 三种路径）
  - [ ] 5.2 `tests/unit/test_frontmatter_service.py`：验证原子写入、缺失字段补全、文件锁保护
  - [ ] 5.3 `tests/integration/test_mastery_bkt_update.py`：端到端验证 POST 请求更新 frontmatter

## Dev Notes

- **BKT 算法来源**：Corbett & Anderson (1994) "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge"，标准四参数模型
- **原子写入**：Python `os.replace()` 在 POSIX 系统上是原子操作（POSIX rename 语义），Windows 需 `pathlib.Path.replace`
- **文件锁**：使用 `filelock` 库（`pip install filelock`）避免多进程同时写入同一笔记的竞态条件
- **partial 答案**：概率权重 0.5 是保守估计；可通过配置调整（`settings.bkt.partial_correct_weight`）
- **NFR-INT-1**：frontmatter 损坏将导致整个 Dataview/BKT 管道失效，原子写入是最高优先级保护

### Project Structure Notes

- 核心服务：`backend/app/services/mastery_service.py`（新建）
- frontmatter 工具：`backend/app/services/frontmatter_service.py`（已存在，需扩展）
- API 端点：`backend/app/api/v1/endpoints/mastery.py`（新建）
- Pydantic 模型：`backend/app/schemas/mastery.py`（新建）
- 参考样式：`backend/app/services/rag_service.py`（服务层结构）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.1] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR19] — BKT 更新需求
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — mastery_score / bkt_params 字段定义
- [Algorithm: Corbett & Anderson 1994] — BKT 四参数贝叶斯公式

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证答对时掌握度上升** (AC: #1)
   - 打开一个概念笔记（例如"递归"），记录顶部 frontmatter 中的 `mastery_score` 数值
   - 完成该概念的一道考察题并答对
   - 重新打开笔记，`mastery_score` 数值应该比之前更高
   - 如果数值没有变化或变低了，记录 Story 5.1 和前后数值

2. **验证答错时掌握度下降** (AC: #1)
   - 记录某概念笔记当前 `mastery_score`
   - 故意答错该概念的考察题
   - 重新检查笔记，`mastery_score` 应该比之前更低
   - 如果数值升高或不变，记录 Story 5.1

3. **验证新概念自动初始化** (AC: #2)
   - 对一个从未考察过的全新概念进行第一次考察
   - 完成后打开该概念笔记，frontmatter 中应出现 `bkt_params` 字段（含 p_know/p_guess/p_slip/p_transit）
   - 如果没有 bkt_params 字段，记录 Story 5.1 和概念名称

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.1.1 | pytest | `.venv/bin/pytest tests/unit/test_bkt_algorithm.py -x -q` | 0 failed |
| CP-5.1.2 | pytest | `.venv/bin/pytest tests/unit/test_frontmatter_service.py -x -q` | 0 failed |
| CP-5.1.3 | pytest | `.venv/bin/pytest tests/integration/test_mastery_bkt_update.py -x -q` | 0 failed |

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
