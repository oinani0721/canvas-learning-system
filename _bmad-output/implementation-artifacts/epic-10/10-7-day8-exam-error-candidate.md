---
story_id: "10.7"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["10.6"]
blocks: ["10.8"]
trace: ["FR-DEEP-07", "S2", "S5", "M3", "M6", "UX-6"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 8"
target_date: "2026-05-14"
block_type_added: "EXAM_WHITEBOARD, ERROR_CANDIDATE"
uat_sheet: "_bmad-output/验收单/Story-10.7-day8-exam-error-candidate.md"
---

# Story 10.7: Day 8 ExamWhiteboard + ErrorCandidate + AutoSCORE

**Status**: ready-for-dev (target Day 8, 2026-05-14)

## Story（用户故事）

As a 学习者, I want exam mode with 4-way error classification (misconception / careless / computational / slip) where **I select the error type myself** (not AI infers) so that I understand not just what I got wrong, but why I made the mistake — and the system learns from my self-attribution.

> **映射对**: M3（测验生成 → 检验白板）+ M6（测试+闪卡块 → 检验白板挂钩）+ S2/S5（验证场景）+ UX-6（Agent 询问而非替决定）

## 通俗化解释（给学习者）

> **一句话说**: 答错题后，系统弹出 4 个选项让"你自己选"是哪种错——不是 AI 替你判断。

**你会遇到的场景**:
- 在 exam whiteboard 答题（隔离不嵌套 OriginWhiteboard）
- 答错 → 4 选项弹窗：misconception（不懂）/ careless（粗心）/ computational（算错）/ slip（手滑）
- 你选 → 后端记录到 Canvas 的 error_loop 表

**这个功能帮你**:
- 错题分类不被 AI 误判（你最清楚自己为啥错）
- 长期收集错误模式 → FSRS 排程时优先刷"misconception 类"
- 检验白板与原白板隔离（不污染原始拆解笔记）

**用个比喻**: 🎯 就像高考模拟题，老师不会直接说"你这道是哪种错"，是问"你觉得是知识漏洞还是粗心？"——你的自我归因比 AI 推断更准。

## Acceptance Criteria

### AC #1: BlockType Enum 第 2 批扩展

- **Given** Story 10.6 已加 MASTERY_DASHBOARD 验证无破裂
- **When** 加 `EXAM_WHITEBOARD = "exam_whiteboard"` + `ERROR_CANDIDATE = "error_candidate"`
- **Then** 17 个 BlockType 全部可用（14 原 + 3 新）
- **And** `pytest tests/book/` 全过
- **And** quiz/flash_cards 渲染不破

### AC #2: ExamWhiteboard 块（隔离不可嵌套）

- **Given** Pydantic schema `ExamWhiteboardBlock`
- **When** 渲染该 block
- **Then** 全屏或 modal quiz 界面（不在普通 page 流中）
- **And** payload 含 `quiz_id, canvas_pipeline_token, acp_context, question_text`
- **And** `constraint_no_nesting: Literal[True]` 字段保证不嵌套 OriginWhiteboard（D14 哲学底线）

### AC #3: ErrorCandidate 4 类对话框

- **Given** 用户答错 quiz
- **When** 提交错误答案
- **Then** 弹出对话框含 4 选项：`PROBLEM_FRAMING / REASONING_FALLACY / KNOWLEDGE_GAP / SUPERFICIAL`
- **And** 用户选择后 POST 到 Canvas `error_loop_detector`
- **And** 可选 `user_note` 文本字段（用户自由批注）

### AC #4: AutoSCORE 4 维评分（接 Canvas）

- **Given** Canvas backend `autoscore.py:30 AutoScorer + RUBRIC_DIMENSIONS`
- **When** 用户提交答案
- **Then** fork 调 `POST :8011/api/v1/exam/score` 通过 exam_proxy
- **And** Canvas 返回 4 维分数（correctness / clarity / rigor / process）
- **And** Feedback modal 显示 4 维 + 用户答案 vs 标准答案 diff

### AC #5: 验证场景 S2 + S5 通过

- **Given** Day 8 收官时
- **When** 用户答题 → 错误分类 → 系统记错误日志
- **Then** S2: 调 Canvas `/exam/start` + `/exam/score` 全链路
- **And** S5: 错误日志触发 Day 0/3/7 推送（console 显示 `[REVIEW DUE]`）

## Tasks / Subtasks

### Backend (BlockType + Schema + Router)

- [ ] Task 1: BlockType Enum 第 2 批 (AC: #1)
  - [ ] 1.1: Edit `deeptutor/book/models.py` 加 2 个 enum 值
  - [ ] 1.2: 跑 `pytest tests/book/` 立即验证
  - [ ] 1.3: 如果有破裂 → rollback + 单独修

- [ ] Task 2: Pydantic schemas (AC: #2, #3)
  - [ ] 2.1: 新建 `deeptutor/book/schemas/exam_whiteboard.py` 含 `ExamWhiteboardBlock` + `ExamWhiteboardPayload`
  - [ ] 2.2: 新建 `deeptutor/book/schemas/error_candidate.py` 含 `ErrorCandidateBlock` + `ErrorCandidatePayload` + `ErrorCandidateType` Literal
  - [ ] 2.3: payload 含 `acp_context: dict` (Canvas 5 层 ACP 上下文)

- [ ] Task 3: exam_proxy router 激活 (AC: #4, #5)
  - [ ] 3.1: 修复 staging cp 进的 `deeptutor/api/routers/exam_proxy.py` import（与 Story 10.2 wikilink_proxy 同模式）
  - [ ] 3.2: 实现 endpoint:
    - `POST /api/v1/exam/start` → Canvas `/exam/start`
    - `POST /api/v1/exam/score` → Canvas `/exam/score` (AutoSCORE 4 维)
    - `POST /api/v1/exam/error-classify` → Canvas `error_loop_detector`
  - [ ] 3.3: register 到 main.py

### Frontend (UI 组件)

- [ ] Task 4: ExamWhiteboardBlock (AC: #2)
  - [ ] 4.1: 新建 `web/app/(workspace)/book/components/blocks/ExamWhiteboardBlock.tsx`
  - [ ] 4.2: 全屏 modal 布局（不在 PageReader 流中）
  - [ ] 4.3: 答案输入 + 提交按钮 + 计时器（可选）

- [ ] Task 5: ErrorCandidateDialog (AC: #3)
  - [ ] 5.1: 新建 `web/app/(workspace)/book/components/blocks/ErrorCandidateDialog.tsx`
  - [ ] 5.2: 4 个明显按钮（不是 dropdown）+ 选项 i 图标 hover 显示解释
  - [ ] 5.3: 可选文本框 user_note
  - [ ] 5.4: 提交后 POST `/api/v1/exam/error-classify`

- [ ] Task 6: FeedbackModal (AC: #4)
  - [ ] 6.1: 新建 `web/components/Exam/FeedbackModal.tsx`
  - [ ] 6.2: 显示 4 维 score（correctness / clarity / rigor / process）
  - [ ] 6.3: diff 视图：用户答案 vs 标准答案
  - [ ] 6.4: 按钮 "Next Question" / "Finish Exam"

### Test (R1 关键缓解)

- [ ] Task 7: BlockType Enum 第 2 批不破裂 (AC: #1)
  - [ ] 7.1: `pytest tests/book/` 全套
  - [ ] 7.2: `pytest tests/api/test_book.py`
  - [ ] 7.3: 现有 14 个 BlockType 序列化 round-trip 正确

- [ ] Task 8: E2E (AC: #5)
  - [ ] 8.1: 答错题 → 弹出 ErrorCandidate 对话框
  - [ ] 8.2: 选 misconception → 后端记录到 Canvas
  - [ ] 8.3: 看到 4 维分数 panel
  - [ ] 8.4: 30 秒后看 console `[REVIEW DUE]` 推送

## Dev Notes

### R1 风险分批管理
- Day 7 已加 1 块 MASTERY_DASHBOARD（验证无破裂）
- Day 8 加 2 块 EXAM_WHITEBOARD + ERROR_CANDIDATE
- 总计 3 块新增，远低于 R1 预警的"30+ Pydantic 失败"风险

### UX-6 落地（Agent 询问而非替决定）
- ErrorCandidate 4 选项**用户自己选**（不是 AI 推断后自动落库）
- 用户原话（Round-14 L30）："agent 能亲自检测到错误后向我增量提问，问我是否需要把我的这个错误描述列为批注"
- 设计哲学：Claude Code "询问权限" 模式

### D14 哲学底线（隔离不可嵌套）
- ExamWhiteboard 必须**隔离**于 OriginWhiteboard
- 不能在 OriginWhiteboard 内嵌套 ExamWhiteboard（破坏笔记纯净度）
- payload `constraint_no_nesting: Literal[True]` 是 type-level 保证

### Canvas 接入（零改动）
- `autoscore.py:30 AutoScorer + RUBRIC_DIMENSIONS` 已实装
- `error_loop_detector.py` 4 类错误已定义：PROBLEM_FRAMING / REASONING_FALLACY / KNOWLEDGE_GAP / SUPERFICIAL
- `exam_service.py` 完整 ACP 流（assemble_acp + start + score）
- fork 只做 HTTP proxy

### S5 复习推送
- Canvas `notification_channels.py` 8 通道（已实装）
- DeepTutor 用 APScheduler 每分钟拉 Canvas due 列表
- console 通道是 MVP 默认（不连 Telegram，避免 token 配置）

## UAT 验收

详见 `_bmad-output/验收单/Story-10.7-day8-exam-error-candidate.md`

## References

- Deep Explore §1.4 学习追踪缺失（DeepTutor 完全无错误归因）
- Deep Explore §3.3 Day 8 路线
- Canvas `autoscore.py` + `error_loop_detector.py`

## 下一步

→ Story 10.8 Day 9 UserNote 现场编辑（修复 Agent 2.3 发现的"UserNote 仅展示"瓶颈）
