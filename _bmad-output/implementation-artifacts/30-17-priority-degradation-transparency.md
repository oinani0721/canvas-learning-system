# Story 30.17: Priority 计算记忆降级透明化

Status: done

## Story

As a Canvas学习系统用户,
I want 当FSRS数据不可用时能清楚看到优先级计算是降级的预估值,
so that 我不会基于不完整的优先级数据做出错误的复习决策.

## Acceptance Criteria

1. **AC-30.17.1**: PriorityCalculatorService 当 fsrsState 为 null 时，console.warn 记录降级信息（不依赖 debugMode），并在 PriorityResult 中填充 `degradedDimensions: string[]` 字段标识哪些维度降级
2. **AC-30.17.2**: ReviewDashboardView 当 `fsrsUnavailable === true` 时，在优先级显示旁添加 "⚠️" 降级标记，title 属性说明 "FSRS数据不可用，优先级为预估值"
3. **AC-30.17.3**: ReviewDashboard 统计摘要中显示 "X/Y 个概念缺少FSRS数据"，超过 50% 时显示全局降级警告
4. **AC-30.17.4**: ReviewDashboardView 和 TodayReviewListService 的 FSRS 查询失败日志从 debugMode-only 升级为始终 console.warn
5. **AC-30.17.5**: 单元测试覆盖所有降级路径 — fsrsState=null、memoryResult=null、混合降级场景

## Tasks / Subtasks

- [x] Task 1: PriorityCalculatorService 降级日志和 degradedDimensions 字段 (AC: 1)
  - [x] 1.1 在 PriorityResult 接口添加 `degradedDimensions: string[]` 字段
  - [x] 1.2 calculateFSRSUrgency() 中 fsrsState=null 时 console.warn
  - [x] 1.3 calculatePriority() 收集所有降级维度并填充 degradedDimensions
- [x] Task 2: ReviewDashboardView FSRS 查询降级日志升级 (AC: 4)
  - [x] 2.1 queryFSRSState() 移除 debugMode 条件限制，始终 console.warn
  - [x] 2.2 batchQueryFSRSStates() 同理
- [x] Task 3: TodayReviewListService 降级日志升级 (AC: 4)
  - [x] 3.1 queryFSRSStateForPriority() 始终 console.warn
- [x] Task 4: ReviewDashboardView UI 降级标记和统计 (AC: 2, 3)
  - [x] 4.1 Task 渲染中传递 fsrsUnavailable + degradedDimensions
  - [x] 4.2 优先级显示旁添加 ⚠️ 标记和 title tooltip
  - [x] 4.3 统计摘要中计算并显示降级概念数量
  - [x] 4.4 超过 50% 降级时显示全局警告
- [x] Task 5: 单元测试覆盖降级路径 (AC: 5)
  - [x] 5.1 测试 fsrsState=null → degradedDimensions 包含 'fsrs'
  - [x] 5.2 测试 memoryResult=null → degradedDimensions 包含 'behavior', 'network', 'interaction'
  - [x] 5.3 测试混合降级场景
  - [x] 5.4 测试 console.warn 被调用
- [x] Task 6: 编译部署验证 (CLAUDE.md 强制规则)
  - [x] 6.1 npm run build 成功
  - [x] 6.2 vault main.js 手动同步确认
  - [x] 6.3 grep vault main.js 确认降级代码存在 (13 occurrences)

## Dev Notes

### 架构约束
- CLAUDE.md 强制规则: "禁止静默降级 — if service is None: return default 不记录日志"
- PriorityCalculatorService 是 Obsidian 插件前端代码 (TypeScript)
- 所有修改在 canvas-progress-tracker/obsidian-plugin/ 目录
- 修改后必须 npm run build → vault 部署 → npm run verify

### 当前降级行为 (待修复)
- PriorityCalculatorService L286-292: fsrsState=null → score:50, 无 console.warn
- ReviewDashboardView L297-299: FSRS 查询失败只在 debugMode 下 warn
- TodayReviewListService L719-735: FSRS 查询降级完全静默

### 关键代码位置
- `src/services/PriorityCalculatorService.ts:285` — calculateFSRSUrgency()
- `src/views/ReviewDashboardView.ts:287-303` — queryFSRSState()
- `src/views/ReviewDashboardView.ts:313-329` — batchQueryFSRSStates()
- `src/services/TodayReviewListService.ts:718-735` — queryFSRSStateForPriority()
- `tests/services/PriorityCalculatorService.test.ts` — 现有测试文件

### References
- [Source: docs/epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md#Story-30.17]
- [Source: CLAUDE.md#死代码/静态模板/未注入依赖检测]
- [Source: Story 38.3 AC-2 — fsrsUnavailable 标志已存在]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References

### Completion Notes List
- 61/61 tests pass (45 existing + 16 new Story 30.17 tests)
- All 4 dimension degradation paths now have console.warn (previously silent)
- degradedDimensions field tracks exactly which dimensions used fallback values
- UI shows ⚠️ badge per-task with tooltip, stats summary count, and >50% global warning
- esbuild outfile still points to source dir (not vault); manual copy required

### Change Log
- 2026-02-10: Story 30.17 implemented — all 6 tasks complete

### File List
- `src/services/PriorityCalculatorService.ts` — degradedDimensions + console.warn in all 4 dimensions
- `src/views/ReviewDashboardView.ts` — FSRS query warn upgrade + UI degradation markers + stats
- `src/services/TodayReviewListService.ts` — FSRS query warn upgrade (debug→warn)
- `src/types/UITypes.ts` — ReviewTask.degradedDimensions field added
- `tests/services/PriorityCalculatorService.test.ts` — 16 new tests for degradation transparency
