---
story_id: "10.6"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["10.5"]
blocks: ["10.7"]
trace: ["FR-DEEP-06", "S3", "M7", "M8", "M12", "UX-5"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 7"
target_date: "2026-05-13"
block_type_added: "MASTERY_DASHBOARD"
uat_sheet: "_bmad-output/验收单/Story-10.6-day7-mastery-dashboard.md"
---

# Story 10.6: Day 7 MasteryDashboard Block + BKT/FSRS 接入

**Status**: ready-for-dev (target Day 7, 2026-05-13)

## Story（用户故事）

As a 学习者, I want to see my learning curve over time (BKT mastery + FSRS stability) so that I know exactly which concepts I've mastered vs which need review — and the system uses Anki's proven FSRS algorithm (700M training records) instead of a homegrown estimator.

> **映射对**: M7（批注/标记理解程度 → 原白板核心 1）+ M8（FSRS 推送复习）+ M12（5 大核心）+ UX-5（FSRS 是成熟方案）
> **核心动作**: BlockType Enum 第 1 批扩展（仅加 MASTERY_DASHBOARD，分批降低 R1 风险）

## 通俗化解释（给学习者）

> **一句话说**: 答完几道题后，能看到一个"学习成绩单"页面，每个概念有掌握度百分比 + 下次复习时间。

**你会遇到的场景**:
- 在某 book 里答了 5 道题（含对的、错的）
- 进入 Dashboard 看进度
- 期望看到："递归 80%"、"动态规划 45%"，下次复习时间提示

**这个功能帮你**:
- 知道哪些掌握了（不用再复习）
- 知道哪些没掌握（重点投入）
- 系统帮你算下次复习时间（不用自己定计划）

**用个比喻**: 📊 就像 Anki 的统计面板——但加了"概念之间的依赖关系"维度（递归没掌握 → 数学归纳法也没掌握）。

## Acceptance Criteria

### AC #1: BlockType Enum 扩展（第 1 批，1 块）

- **Given** fork `deeptutor/book/models.py` line 55-73 BlockType enum 现有 14 块
- **When** 加 `MASTERY_DASHBOARD = "mastery_dashboard"`
- **Then** Enum 仍可用，14 个原 BlockType 不破裂
- **And** `pytest tests/book/test_models.py` 通过
- **And** Pydantic validation 不抛错

### AC #2: MasteryDashboardBlock 前端

- **Given** fork 前端加新 block 组件
- **When** book page 含 MASTERY_DASHBOARD block
- **Then** 渲染 4 列 cards（today_due / day_0 / day_3 / day_7）
- **And** 每张 card 显示 `node_id, title, bkt_mastery, fsrs_stability, next_review`
- **And** mastery 着色（≥80% 绿、50-80% 黄、<50% 红）

### AC #3: Canvas BKT/FSRS 接入

- **Given** Canvas backend `mastery_engine.py` 已实装 BKT + FSRS
- **When** fork 调 `GET /api/v1/mastery/concept/:id/history` 通过 mastery_proxy
- **Then** 返回时间序列 + FSRS difficulty/stability/retrievability
- **And** Recharts 渲染掌握度曲线（X 轴时间，Y 轴 mastery 0-1）
- **And** 数据来自真实 Canvas（**0 mock**）

### AC #4: 验证场景 S3 通过

- **Given** Day 7 收官时
- **When** 用户答 quiz 题（即使 LLM placeholder 不调真实 OpenAI，也能记 is_correct）
- **Then** mastery.value 通过 BKT 公式更新
- **And** Dashboard 立刻显示新值（websocket 或 polling）

## Tasks / Subtasks

### Backend

- [ ] Task 1: BlockType Enum + Pydantic schema (AC: #1)
  - [ ] 1.1: Edit `deeptutor/book/models.py` BlockType 加 `MASTERY_DASHBOARD = "mastery_dashboard"`
  - [ ] 1.2: 新建 `deeptutor/book/schemas/mastery_dashboard.py`
    - `MasteryDashboardBlock(BlockBase)` + `MasteryDashboardPayload(BaseModel)`
    - 字段：`today_due, day_0_due, day_3_due, day_7_due, last_updated`
  - [ ] 1.3: `MasteryCard(BaseModel)`: `node_id, title, bkt_mastery, fsrs_difficulty/stability/retrievability, next_review, last_review_grade`

- [ ] Task 2: mastery_proxy router
  - [ ] 2.1: 新建 `deeptutor/api/routers/mastery_proxy.py`
  - [ ] 2.2: route `GET /api/v1/mastery/concept/:concept_id/history` 代理到 Canvas
  - [ ] 2.3: route `GET /api/v1/mastery/batch` 批量查多节点
  - [ ] 2.4: register 到 main.py (alphabetical 位置)

- [ ] Task 3: CanvasClient 扩展
  - [ ] 3.1: 加方法 `get_mastery_history(concept_id) -> list[MasteryRecord]`
  - [ ] 3.2: 加方法 `get_mastery_batch(concept_ids) -> dict[id, mastery]`
  - [ ] 3.3: 缓存 5min (in-memory dict)

### Frontend

- [ ] Task 4: MasteryDashboardBlock 组件 (AC: #2)
  - [ ] 4.1: 新建 `web/app/(workspace)/book/components/blocks/MasteryDashboardBlock.tsx`
  - [ ] 4.2: 4 列 grid 布局 (today / day_0 / day_3 / day_7)
  - [ ] 4.3: MasteryCard 组件渲染 mastery + next_review

- [ ] Task 5: 学习曲线图 (AC: #3)
  - [ ] 5.1: `npm install recharts`
  - [ ] 5.2: `MasteryChartPanel.tsx` 用 LineChart 画 mastery 时间序列
  - [ ] 5.3: X 轴 datetime, Y 轴 mastery (0-1)

- [ ] Task 6: BlockRenderer 加 case
  - [ ] 6.1: Edit `BlockRenderer.tsx` switch 加 `case BlockType.MASTERY_DASHBOARD: return <MasteryDashboardBlock />`

### Test (R1 缓解关键)

- [ ] Task 7: BlockType Enum 不破裂测试 (AC: #1)
  - [ ] 7.1: 跑 `pytest tests/book/` 全套
  - [ ] 7.2: 跑 `pytest tests/api/test_book.py` 验证现有 quiz/flash_cards 仍工作
  - [ ] 7.3: 序列化测试：`Block.model_dump()` 含新 block_type 时 round-trip 正确

- [ ] Task 8: E2E (AC: #4)
  - [ ] 8.1: 创建 mastery_dashboard block 含 mock 用户数据
  - [ ] 8.2: 答 5 题 → 验证 mastery 更新
  - [ ] 8.3: Recharts 曲线显示 ✓

## Dev Notes

### R1 风险缓解（分批加 Enum）
- **Day 7 仅加 MASTERY_DASHBOARD 1 块** → 跑全 fork test → 验证无破裂
- **Day 8 再加 EXAM_WHITEBOARD + ERROR_CANDIDATE 2 块** → 同样跑全测试
- 主报告 §六 R1: "先加 1 个块（ORIGIN）跑全部 DeepTutor 测试，再加第 2 个"

### Canvas 接入（零改动）
- `backend/app/services/mastery_engine.py` 已实装 BKT P(L)/P(G)/P(S) + FSRS difficulty/stability/retrievability
- `backend/app/services/mastery_fusion.py` `fuse_5_signals()` 融合多信号
- fork 仅作 HTTP proxy，不重实现

### 选 Recharts 而非 D3
- D3 过重 + 配置繁琐
- Recharts React 原生 + 轻量 + 足够功能
- 与 fork tech stack（Next.js + React）天然兼容

### UX-3 降级
- 用户痛点："3 周前 admissibility 错 → 今天触发类似题"是 🔴 学术研究活跃，生产 near-zero
- Day 7 AC 仅做"看 mastery 趋势"，跨时间错误重现降为 P2 写入 Risks
- Day 7 不强求 UX-3 最高目标

## UAT 验收

详见 `_bmad-output/验收单/Story-10.6-day7-mastery-dashboard.md`

## References

- Deep Explore §1.4 学习追踪机制（DeepTutor 完全缺失）
- Deep Explore §3.3 Day 7 路线
- Canvas backend `mastery_engine.py` (复用 0 改动)

## 下一步

→ Story 10.7 Day 8 ExamWhiteboard + ErrorCandidate（分批 Enum 第 2 批 + AutoSCORE）
