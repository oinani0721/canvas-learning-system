---
story_id: "LITE-5-6"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 2.5
depends_on: ["EXAM-001", "PLUGIN-002", "STORY-2-10-wikilink-graphiti-sync"]
blocks: []
sprint: "Sprint 3+ (V-11 patch 2026-05-26 spec 内部统一)"
supersedes: "_bmad-output/implementation-artifacts/epic-5/5-6-calibration-data-voting.md"
merges_in: "_bmad-output/implementation-artifacts/epic-4/4-9-calibration-vote-data-sync.md"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
saves_hours: 2.5
trace:
  - "FR-MEM-02 (简化版)"
  - "FR-MEM-03 (保留)"
  - "FR-EXAM-15 (来自 4.9 merge)"
  - "FR-EXAM-17 (来自 4.9 merge)"
  - "FR-CALIB-GRAPHITI (V-11 修复 — 异步写 Graphiti 学习事件)"
---

# Story LITE-5.6: 校准投票（合并 4.9 数据同步，简化版）

Status: ready-for-dev

## Story

As a 学习者,
I want 评分结果返回后用 1 click 投票"准 / 偏高 / 偏低 / 跳过",
So that 系统积累 calibration 样本 + 同步回源白板，但**不强制我看复杂的元认知 2x2 矩阵**（400+ 题样本后再加）。

## Acceptance Criteria

1. **Given** `grade_answer` 返回 4 维 `AutoScoreResult` 后 **When** plugin 渲染评分反馈段 **Then** 在 callout 下方显示 4 个 button：`[✓ 准]` / `[↑ 偏高]` / `[↓ 偏低]` / `[⊘ 跳过]`

2. **Given** 用户点击 button **When** plugin 处理 click **Then** **single-write** 到 exam_boards `*.md` frontmatter `calibration_votes[]`：
   ```yaml
   calibration_votes:
     - timestamp: "2026-05-24T14:30:00Z"
       question_id: "q-xyz-001"
       grade_value: 0.65
       vote: "too_high"
   ```

3. **Given** vote 写入 exam_boards Then **同步**到源白板（4.9 merge）frontmatter `calibration_votes[]`：
   - 源白板路径从 `exam_boards/*.md` 的 frontmatter `source_canvas` 字段读
   - 同步操作走 `frontmatter_writeback_service.sync_to_source_canvas(question_id)`
   - 失败时不阻塞 plugin，记 structlog warning

4. **Given** 用户已对该 `question_id` 投过票 **When** 再次点击 **Then** 不重复写入（vote 数组 unique by question_id + vote）

5. **Given** 用户选 `[⊘ 跳过]` **When** plugin 处理 **Then** 写入 `vote: "skip"` 事件（不空跳，用于后续分析"用户对哪类题目最常跳过"）

6. **Given** 多次累计 votes **When** plugin 渲染 Dashboard **Then** **不渲染** 2x2 元认知矩阵图（PRD §1.10 Story 8.3 延后到 400+ 题）

7. **Given** Sprint v3 阶段 **When** vote 写入 **Then** **双写**：(a) 同步写 exam_boards + 源白板 frontmatter（主, 必成功）；(b) **异步写 Graphiti**: `add_episode("calibration_vote", body=vote_data, group_id="vault:<vault_id>")` (不阻塞 UI, 经 STORY-2-10 同一 events_queue 管道) — **2026-05-24 修正**：从"禁 add_episode"改为"异步 add_episode"，因为校准投票本身就是学习事件，必须被 Graphiti 学习历程记录（用户 2026-05-13 核心闭环原话："批注 + 学习过程 + 个人记忆系统"）。Graphiti 不可用时只走 (a) 不抛异常

## Tasks / Subtasks

- [ ] Task 1: plugin UI 4 button 渲染 (AC: #1)
  - [ ] `frontend/obsidian-plugin/src/exam-quick.ts::buildFeedbackAppend()` 加 4 button 行
  - [ ] CSS: 按钮 inline 排列，hover 高亮
  - [ ] 点击事件 binding 到 handler

- [ ] Task 2: vote write to exam_boards frontmatter (AC: #2)
  - [ ] handler 读 exam_boards md frontmatter，append calibration_votes[]
  - [ ] 用 `obsidian.processFrontMatter()` 保 yaml 格式
  - [ ] 单元测试：append 不破坏现有字段

- [ ] Task 3: sync 到源白板（4.9 merge 逻辑） (AC: #3)
  - [ ] backend 加 endpoint `POST /api/v1/calibration/vote {exam_board, question_id, vote, source_canvas}`
  - [ ] `frontmatter_writeback_service.sync_to_source_canvas()` 实现
  - [ ] structlog 记录同步失败（不阻塞）

- [ ] Task 4: 防双击 + skip 记录 (AC: #4, #5)
  - [ ] vote 数组 dedup by `(question_id, vote)`
  - [ ] skip 也写入（不 short-circuit）
  - [ ] 单元测试：连点 2 次只写 1 条

- [ ] Task 5: 不渲染 2x2 矩阵 (AC: #6)
  - [ ] **不实施**任何 plotly / Dataview chart / mermaid 矩阵
  - [ ] Dashboard 段只显示 vote 计数（如 "本周校准 12 次"）

- [ ] **Task 6: 异步写 Graphiti 校准事件 (V-11 修复 2026-05-26, AC: #7 副段 b)**
  - [ ] backend endpoint **同步**写 (a) exam_boards + 源白板 frontmatter (主, 必成功)
  - [ ] backend endpoint **异步**触发 (b) 写 `calibration_events` 表 (并列 STORY-1-16-hook 的 `callout_events`, 复用 STORY-2-10 events_queue 管道)
  - [ ] **不直接**调 `add_episode` (由 STORY-2-10 hourly sweep 统一消费 calibration_events 表)
  - [ ] sweep 时 episode_body 自然语言化:
    ```python
    f"用户在节点 [[{node_id}]] 答题后, 对评分 {grade_value:.2f} 投票为 '{vote}', "
    f"反映用户认为系统的评分 {'准确' if vote == 'accurate' else ('偏高' if vote == 'too_high' else '偏低')}."
    ```
  - [ ] (a) 必成功, (b) 失败时不抛异常, 仅 structlog warning (用户无感知)
  - [ ] 单元测试: 4 用例 (写 calibration_events 成功 / Graphiti 不可用时 (a) 仍成功 / sweep 消费 calibration_events / dedup query_id+vote)

- [ ] Task 7: 测试 + UAT
  - [ ] 单元测试：vote 写入 + sync
  - [ ] e2e 测试：答题 → 评分 → vote → 看到源白板 frontmatter 更新
  - [ ] 性能：vote 写入 + sync < 500ms

## Simplification Rules（vs 旧 5.6 完整版 + 4.9 合并 + 2026-05-26 V-11 内部统一）

| 旧 5.6 完整 (5h) + 4.9 (6h) = 11h | LITE-5.6（2.5h，含 4.9 同步 + V-11 异步 Graphiti） | 决策 |
|---|---|---|
| ✅ 4 选项投票 (accurate/too_high/too_low/skip) | ✅ **保留** | 单人 calibration 仍有价值 |
| ✅ 2x2 元认知矩阵渲染 (Story 8.3) | ❌ **砍** | 用户 3A 决策：400+ 题样本后回头 |
| ✅ Dunning-Kruger 红区警告 | ❌ **砍** | 同上，依赖 8.3 矩阵 |
| ✅ 同步到源白板 (4.9 核心) | ✅ **保留** | 4 方共识不可砍，否则 calibration 数据孤岛 |
| ✅ Graphiti add_episode 写学习事件 | ✅ **异步保留** (**V-11 修复 2026-05-26**) | 用户 2026-05-13 核心闭环原话: "**批注+学习过程+个人记忆系统**" — 校准投票本身就是学习事件, 必须入 Graphiti 学习历程; 异步走 STORY-2-10 sweep 不阻塞 UI |
| ✅ confidence × actual_score 二维统计 | ❌ **砍** | 同 2x2 矩阵砍 |
| ✅ dual-write (frontmatter + Graphiti) | ✅ **保留** (frontmatter 同步主 + Graphiti 异步副, **V-11 修复**) | 旧 spec 内部 4 处自相矛盾 (AC#7 说双写 / Task 6 说禁 / Simplification 表说砍 / Checkpoints grep 0 matches) → 必然让 dev 实现成单写, 校准数据无法进 Graphiti |

**禁实施的具体功能** (V-11 修复后清单):
- ❌ 任何 2x2 矩阵图渲染（plotly / Chart.js / Dataview chart / mermaid）
- ✅ `add_episode` 调用 (**V-11 修复**: 允许且必须, 由 STORY-2-10 sweep 异步执行, 不在 calibration endpoint 直接调)
- ❌ Dunning-Kruger / confidence 校准统计可视化

## Background Decision Trace

- **Sprint v3 决策 2** (2026-05-21 ChatGPT v2 + Agent A/B/C 验证, 用户 2026-05-22 锁 B): Story 5.6 保留 lite 版（原 5h → 2h，节省 60%）
- **用户 3A 决策** (2026-05-22): 8.3 元认知 2x2 矩阵 sprint 1+2 砍，400+ 题样本后回头加
- **4.9 合并**: 4.9 校准投票数据同步回源白板 + 5.6 评分投票是**同一闭环**（4 方共识合并简化），不分两 spec
- **2026-05-24 修正 (single-write → dual-write)**: AC#7 改为 "frontmatter 主写 + Graphiti 异步写" — 但 Tasks/Simplification/Checkpoints 3 处未同步, 引入 V-11 内部矛盾
- **2026-05-26 V-11 修复 (CRITICAL)**: ChatGPT Deep Research 审计发现 LITE-5-6 spec 自身 4 处自相矛盾 (AC#7 双写 vs Task 6 禁 vs Simplification 砍 vs Checkpoint grep=0 matches) → dev 接手必按 grep 检查实现成 single-write, AC#7 死字 → 校准投票完全无法入 Graphiti 学习历程, 违背用户 2026-05-13 核心闭环 → 必须 4 处全部统一为 "异步 dual-write 经 STORY-2-10 管道"

## Dev Notes

### Architecture (V-11 修复 2026-05-26)
- plugin 侧渲染层：`exam-quick.ts::buildFeedbackAppend()` 注入 vote button HTML
- vote button click → 调 backend `POST /api/v1/calibration/vote`
- backend **dual-write**:
  - (a) **同步主写**：先写 exam_boards frontmatter, 再 sync 源白板 frontmatter (async, 不阻塞 plugin) — 必成功
  - (b) **异步副写**：写 `calibration_events` LanceDB 表 (复用 STORY-2-10 events_queue 管道), hourly sweep 统一 `add_episode` 写 Graphiti
- **接** Graphiti (V-11 修复后已通管道): STORY-1-16-hook + STORY-2-10 + LITE-5-6 三者共用同一 events_queue + sweep cron, 零额外基础设施

### File Paths
- plugin: `frontend/obsidian-plugin/src/exam-quick.ts`
- backend endpoint: `backend/app/interfaces/api/calibration.py`（新建）
- service: `backend/app/services/frontmatter_writeback_service.py`（加 `sync_to_source_canvas`）

### Testing
- 单元测试：`backend/tests/unit/test_calibration_vote_writeback.py`
- 集成测试：`backend/tests/integration/test_calibration_sync_to_source.py`
- e2e：`backend/tests/e2e/test_calibration_full_loop.py`

### Project Structure Notes
- vote 数组 schema 严格遵循 yaml 数组规范
- frontmatter writeback 用 obsidian `processFrontMatter` 避免破坏其他字段（如 `tips[]` / `errors[]`）

### References
- **From PRD**: §1.10 元认知 2x2 校准矩阵 (Story 8.3，已砍)
- **From PRD**: §2.4 校准投票 + 数据回源 (Story 4.9 核心)
- **From Sprint v3**: `_bmad-output/research/2026-05-21-sprint-plan-v3.md` Lite 重编清单
- **From 2026-05-22 答疑 v2**: `_bmad-output/研究/2026-05-22-3批注答疑v2-我的认知校准.md` §决策 3A
- 旧 spec（[DEPRECATED]）：`epic-5/5-6-calibration-data-voting.md`
- 旧 spec（[MERGED]）：`epic-4/4-9-calibration-vote-data-sync.md`

## UAT Script（用户视角验证）

> 1. 在 canvas-vault 答完一道题，Cmd+S 触发评分
> 2. 看 callout 下方应出现 4 个 button：`[✓ 准]` `[↑ 偏高]` `[↓ 偏低]` `[⊘ 跳过]`
> 3. 点 `[↑ 偏高]` button
> 4. 打开 exam_boards 对应 md，frontmatter 应出现 `calibration_votes:` 数组（含本次 vote）
> 5. 打开**源白板** md（同名 / source_canvas frontmatter 指向），frontmatter 应也出现同一条 vote
> 6. 再次点 `[↑ 偏高]` button，应**不重复写**（frontmatter vote 仍 1 条）
> 7. 确认 Dashboard md **没有** 2x2 矩阵图 (3A 决策延后)

## Automated Checkpoints (V-11 修复后)

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| vote write to frontmatter | unit | `pytest backend/tests/unit/test_calibration_vote_writeback.py -x` | 0 failures |
| sync to source canvas | unit | `pytest backend/tests/unit/test_sync_to_source_canvas.py -x` | 0 failures |
| **V-11 calibration_events 写入** | unit | `pytest backend/tests/unit/test_calibration_events_queue.py -x` | 0 failures (assert 异步写入成功 + endpoint return 不等待) |
| **V-11 STORY-2-10 sweep 消费** | unit | `pytest backend/tests/unit/test_sweep_calibration.py -x` | 0 failures (assert sweep 能读 calibration_events 调 add_episode) |
| **V-11 Graphiti 不可用降级** | unit | `pytest backend/tests/unit/test_calibration_graphiti_unavailable.py -x` | 0 failures (assert (a) 仍成功, (b) structlog warning) |
| **V-11 endpoint 异步语义** | static | `grep -E "background_tasks\.add_task\|asyncio\.create_task" backend/app/interfaces/api/calibration.py` | ≥ 1 match (异步触发副写) |
| 禁 2x2 矩阵渲染 | static | `grep -rE "plotly\|Chart\.js\|mermaid" frontend/obsidian-plugin/src/exam-quick.ts` | 0 matches |
| 防双击 dedup | unit | `pytest backend/tests/unit/test_vote_dedup.py -x` | 0 failures |
| **V-11 e2e Graphiti 闭环** | e2e | `pytest backend/tests/e2e/test_calibration_to_graphiti_e2e.py -x` | 0 failures (assert vote → sweep → `search_facts(query="calibration_vote")` 能查到) |

## Dev Agent Record

待 dev 填充。

## Change Log

- 2026-05-24: spec 创建（Plan `EPIC1-BMAD-DEV-ASSESS-2026-04-17`），合并 5-6-calibration-data-voting.md + 4-9-calibration-vote-data-sync.md 为单 Lite spec
- 2026-05-24 (晚): AC#7 从 "禁 add_episode" 改为 "frontmatter 主 + Graphiti 异步副", 但 Tasks/Simplification/Checkpoints 未同步 → 引入 V-11 内部矛盾
- **2026-05-26 V-11 修复** (ChatGPT Deep Research 审计 HIGH `CALIBRATION_SPLIT_BRAIN`): spec 4 处统一为 "dual-write 经 STORY-2-10 异步管道":
  - Task 6: "禁 Graphiti 路径" → "异步写 Graphiti 校准事件" (调 calibration_events 表)
  - Simplification Rules: "Graphiti add_episode 砍" → "异步保留" + "禁实施清单"删去 add_episode
  - Architecture: "不接 Graphiti" → "dual-write (同步 frontmatter + 异步 calibration_events)"
  - Automated Checkpoints: "禁 Graphiti 调用" → 5 个新 checkpoint (events_queue 写入 / sweep 消费 / 降级 / 异步语义 / e2e Graphiti 闭环)
  - depends_on 加 `STORY-2-10-wikilink-graphiti-sync` (共用 events_queue 管道)
  - estimate_hours 2 → **2.5** (+0.5h for calibration_events 表 schema + sweep 扩展)
