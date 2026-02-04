# Epic 32: Ebbinghaus Review System Enhancement
# 艾宾浩斯复习系统增强

**Epic ID**: EPIC-32
**类型**: Brownfield Enhancement (棕地增强)
**优先级**: P1 (High)
**状态**: Ready for Implementation
**创建日期**: 2026-01-18
**预计工时**: ~44小时
**实施周期**: 3周

---

## Epic Goal

**激活Py-FSRS算法**替换简化版Ebbinghaus调度器，提供基于个人学习表现的科学优化复习间隔，同时完成多学科隔离功能。

**价值陈述**: 用FSRS-4.5算法替换固定间隔的Ebbinghaus调度器，将根据实际记忆衰减模式提供个性化复习间隔，预计提升记忆效率15-25%。

---

## Background & Context

### 深度调研发现

此Epic基于对Canvas Learning System艾宾浩斯复习系统的深度调研，发现以下关键组件**已实现但未激活**：

| 组件 | 文件 | 行数 | 实现状态 | 激活状态 |
|------|------|------|----------|----------|
| Py-FSRS Manager | `src/memory/temporal/fsrs_manager.py` | 397 | ✅ 100% | ❌ 未用 |
| Ebbinghaus调度器 | `src/ebbinghaus_review.py` | 871 | ✅ 100% | ✅ 使用中 |
| Review Service | `backend/app/services/review_service.py` | 1099 | ✅ 100% | ✅ 使用中 |
| 复习Dashboard | `ReviewDashboardView.ts` | 3100+ | ✅ 95% | ✅ 使用中 |
| 多学科隔离 | Story 30.8 | - | ⚠️ 60% | ⚠️ 部分 |

### 核心问题

1. **Py-FSRS未集成**: `fsrs_manager.py`完整实现但未被`review_service.py`调用
2. **py-fsrs依赖缺失**: `requirements.txt`中未添加py-fsrs库
3. **Dashboard统计不完整**: `reviewCount`和`streakDays`字段是TODO
4. **多学科隔离未完成**: GraphitiTemporalClient和插件UI未实现

### 与Epic 30的关系

| Epic 30 Story | 状态 | Epic 32依赖 |
|---------------|------|-------------|
| 30.1 (Neo4j Docker) | ✅ 已完成 | 基础设施 |
| 30.2 (Neo4jClient) | ✅ 已完成 | 基础设施 |
| 30.7 (插件记忆服务初始化) | ✅ 已完成 | Story 32.3需要 |
| 30.8 (多学科隔离) | ⚠️ 部分完成 | **Story 32.6直接依赖** (~~32.5已删除~~) |

**前置条件**: Epic 30的Stories 30.1, 30.2, 30.7, 30.8必须在开始Epic 32 Phase 3之前完成。

> **⚠️ 重复功能已合并 (2026-01-18)**:
> - ~~Story 32.5~~ 与 Story 30.8 功能完全重复，已删除
> - Story 32.6 现在直接依赖 Story 30.8 的后端实现

---

## Stories

### Story 32.1: Py-FSRS依赖激活 [P0 BLOCKER]

**目标**: 添加py-fsrs到requirements.txt并验证FSRSManager使用真实库正常工作

**验收标准**:
- AC-32.1.1: 添加`py-fsrs>=1.0.0`到`backend/requirements.txt`
- AC-32.1.2: 更新`fsrs_manager.py`使用真实库（移除/更新fallback代码）
- AC-32.1.3: 单元测试通过（`FSRS_AVAILABLE=True`环境）
- AC-32.1.4: `FSRSManager.review_card()`返回有效调度数据
- AC-32.1.5: `get_retrievability()`返回准确遗忘曲线值

**修改文件**:
- `backend/requirements.txt` (添加py-fsrs)
- `src/memory/temporal/fsrs_manager.py` (验证/更新imports)
- `backend/tests/unit/test_fsrs_manager.py` (新建 - 10个测试用例)

**预计工时**: 4小时

---

### Story 32.2: ReviewService FSRS集成 [P0 BLOCKER]

**目标**: 在复习工作流中用`FSRSManager`替换`EbbinghausReviewScheduler`

**验收标准**:
- AC-32.2.1: `review_service.py`导入并使用`FSRSManager`替代`EbbinghausReviewScheduler`
- AC-32.2.2: 复习记录使用FSRS评分 (1=Again, 2=Hard, 3=Good, 4=Easy)
- AC-32.2.3: 下次复习日期由FSRS算法计算（非固定间隔）
- AC-32.2.4: 向后兼容：现有复习记录仍可加载
- AC-32.2.5: 文档说明现有SQLite数据迁移路径

**修改文件**:
- `backend/app/services/review_service.py` (重构~150行)
- `backend/app/api/v1/endpoints/review.py` (更新使用新服务方法)
- `backend/app/models/__init__.py` (添加FSRS相关schemas如需要)

**预计工时**: 10小时

**技术说明**:
```python
# 当前实现 (Ebbinghaus)
from ebbinghaus_review import EbbinghausReviewScheduler
_scheduler = EbbinghausReviewScheduler()
next_date = _scheduler.calculate_next_review(item_id)  # 固定间隔: [1,3,7,15,30]

# 目标实现 (FSRS)
from src.memory.temporal.fsrs_manager import FSRSManager
_fsrs = FSRSManager()
card = _fsrs.review_card(card, rating)  # 动态间隔，基于记忆强度
next_date = _fsrs.get_due_date(card)
```

---

### Story 32.3: 插件FSRS状态集成 [P1]

**目标**: 将真实FSRSCardState传递给PriorityCalculatorService（当前传递null）

**验收标准**:
- AC-32.3.1: `TodayReviewListService.ts`从后端API查询FSRS卡片状态
- AC-32.3.2: 后端提供`GET /api/v1/review/fsrs-state/{concept_id}`端点
- AC-32.3.3: `PriorityCalculatorService.calculatePriority()`接收有效FSRSCardState
- AC-32.3.4: Dashboard显示FSRS优先级计算结果
- AC-32.3.5: FSRS数据不可用时优雅降级（保留当前行为）

**修改文件**:
- `backend/app/api/v1/endpoints/review.py` (添加fsrs-state端点)
- `canvas-progress-tracker/obsidian-plugin/src/services/TodayReviewListService.ts` (添加FSRS查询)
- `canvas-progress-tracker/obsidian-plugin/src/services/PriorityCalculatorService.ts` (小调整)

**预计工时**: 8小时

**当前问题** (PriorityCalculatorService.ts):
```typescript
// 当前：传递null，导致FSRS权重（40%）使用中性分数0.5
const fsrsScore = this.calculateFSRSScore(null);  // 总是返回0.5

// 目标：传递真实FSRS状态
const fsrsState = await this.fetchFSRSState(conceptId);
const fsrsScore = this.calculateFSRSScore(fsrsState);  // 基于实际记忆强度
```

---

### Story 32.4: Dashboard统计补全 [P1]

**目标**: 实现Dashboard中缺失的TODO统计项

**验收标准**:
- AC-32.4.1: `reviewCount`字段填充实际复习历史次数（每个概念）
- AC-32.4.2: `streakDays`字段计算连续复习天数
- AC-32.4.3: 复习历史跨会话持久化（SQLite或后端存储）
- AC-32.4.4: 统计卡片显示准确的周/月趋势

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts` (实现TODOs)
- `canvas-progress-tracker/obsidian-plugin/src/services/TodayReviewListService.ts` (添加历史追踪)
- `canvas-progress-tracker/obsidian-plugin/src/database/ReviewRecordDAO.ts` (添加streak计算)

**预计工时**: 6小时

**当前TODO位置**:
```typescript
// ReviewDashboardView.ts:159
reviewCount: 1, // TODO: Track review count

// ReviewDashboardView.ts:243
streakDays: 0, // TODO: Calculate streak
```

---

### ~~Story 32.5: 多学科GraphitiClient完成~~ [❌ 已删除 - 合并到EPIC-30 Story 30.8]

> **⚠️ 删除原因 (2026-01-18)**:
>
> 深度分析发现此Story与 **EPIC-30 Story 30.8** 完全重复：
> - 30.8 已实现: `GraphitiTemporalClient` 的 `group_id` 支持
> - 30.8 已实现: 学科自动推断 (`extract_subject_from_canvas_path()`)
> - 30.8 已实现: API `?subject=` 查询参数过滤
>
> **请参阅**: [Story 30.8](../stories/30.8.story.md) 了解完整实现细节
>
> **Story 32.6 现在直接依赖 Story 30.8**

~~**目标**: 完成Story 30.8 Task 2 - GraphitiTemporalClient的group_id支持~~

~~**验收标准**:~~
- ~~AC-32.5.1: `GraphitiTemporalClient.__init__()`接受`default_group_id`参数~~ → **已在30.8实现**
- ~~AC-32.5.2: `add_learning_episode()`在所有实体创建中包含`group_id`~~ → **已在30.8实现**
- ~~AC-32.5.3: `search_by_time_range()`按`group_id`过滤~~ → **已在30.8实现**
- ~~AC-32.5.4: `/api/v1/memory/review-suggestions?subject=X`返回学科感知建议~~ → **已在30.8实现**
- ~~AC-32.5.5: 集成测试验证多学科隔离~~ → **已在30.8实现**

~~**预计工时**: 6小时~~ → **节省6小时**

---

### Story 32.6: 插件学科映射UI [P2]

**依赖**: EPIC-30 Story 30.8 (多学科隔离后端支持)

**目标**: 完成Story 30.8 Task 4 - 插件设置面板的学科映射配置

**验收标准**:
- AC-32.6.1: 设置面板显示"多学科隔离"开关
- AC-32.6.2: 学科映射表编辑器（pattern + subject列）
- AC-32.6.3: "默认学科"下拉/输入框
- AC-32.6.4: 设置持久化到`data.json`
- AC-32.6.5: 保存前验证pattern语法

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` (添加UI区段 ~100行)
- `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` (验证已有接口)

**预计工时**: 6小时

**已存在的接口** (settings.ts):
```typescript
interface SubjectMapping {
  pattern: string;   // Canvas路径模式 (glob)
  subject: string;   // 映射的学科名称
}

interface PluginSettings {
  enableSubjectIsolation: boolean;
  subjectMappings: SubjectMapping[];
  defaultSubject: string;
}
```

---

### Story 32.7: OpenAPI规范更新 [P2]

**目标**: 在OpenAPI规范中文档化所有新增/修改的端点

**验收标准**:
- AC-32.7.1: 文档化`GET /api/v1/review/fsrs-state/{concept_id}`端点
- AC-32.7.2: 文档化Memory API端点的`subject`查询参数
- AC-32.7.3: 添加FSRS相关Schema (FSRSCardState, Rating enum)
- AC-32.7.4: 更新review端点文档为FSRS响应格式
- AC-32.7.5: 在线验证器验证OpenAPI规范通过

**修改文件**:
- `specs/api/fastapi-backend-api.openapi.yml` (添加~100行)

**预计工时**: 4小时

---

## Implementation Phases

```
Phase 1: 核心FSRS激活 [Week 1] - P0 BLOCKERS
├─ Story 32.1: Py-FSRS依赖激活 [4h]
└─ Story 32.2: ReviewService FSRS集成 [10h] (依赖32.1)

Phase 2: 插件集成 [Week 2] - P1
├─ Story 32.3: 插件FSRS状态集成 [8h] (依赖32.2)
└─ Story 32.4: Dashboard统计补全 [6h] (可并行)

Phase 3: 多学科UI [Week 3] - P2
├─ [前置] EPIC-30 Story 30.8 完成 (多学科后端支持)
├─ ~~Story 32.5~~ [❌ 已删除 - 合并到30.8]
└─ Story 32.6: 插件学科映射UI [6h] (依赖EPIC-30 Story 30.8)

Phase 4: 文档 [Week 3] - P2
└─ Story 32.7: OpenAPI规范更新 [4h] (可并行)
```

> **工时调整**: 原预估44小时 → **38小时** (删除32.5节省6小时)

---

## Risk Assessment

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| py-fsrs API不兼容 | 低 | FSRSManager已有fallback处理 |
| Ebbinghaus数据迁移 | 中 | 保留EbbinghausReviewScheduler作为fallback |
| 性能回归 | 低 | FSRS计算是O(1) |
| 破坏现有复习记录 | 中 | 迁移脚本 + 向后兼容 |
| 插件UI复杂度 | 低 | 使用Obsidian原生Setting API |

**回滚计划**:
- 设置`USE_FSRS=false`环境变量切换回Ebbinghaus
- 保留原有SQLite表结构，FSRS数据存储在新表

---

## Compatibility Requirements

- [ ] 现有API保持兼容（添加新端点，不修改现有端点签名）
- [ ] SQLite数据库向后兼容（添加新表，不删除旧表）
- [ ] 插件设置向后兼容（新字段有默认值）
- [ ] 性能影响最小（FSRS计算<1ms）

---

## Definition of Done

- [ ] 所有6个Stories完成 (~~32.5已删除~~)
- [ ] 所有AC通过验证
- [ ] 单元测试覆盖率 > 90%
- [ ] 集成测试全部通过
- [ ] py-fsrs在requirements.txt中
- [ ] Dashboard显示FSRS计算的优先级
- [ ] 多学科隔离在插件设置中可配置
- [ ] OpenAPI规范更新并验证通过
- [ ] 文档更新（README, CHANGELOG）

---

## Key File Locations

| 功能模块 | 文件路径 | 行数 |
|---------|---------|------|
| FSRS管理器 | `src/memory/temporal/fsrs_manager.py` | 397 |
| Ebbinghaus调度器 | `src/ebbinghaus_review.py` | 871 |
| 复习服务 | `backend/app/services/review_service.py` | 1099 |
| 复习API | `backend/app/api/v1/endpoints/review.py` | 522 |
| 学科配置 | `backend/app/core/subject_config.py` | ~100 |
| 记忆服务 | `backend/app/services/memory_service.py` | 684 |
| Graphiti客户端 | `src/agentic_rag/clients/graphiti_temporal_client.py` | 789 |
| Dashboard视图 | `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts` | 3100+ |
| 今日复习服务 | `canvas-progress-tracker/obsidian-plugin/src/services/TodayReviewListService.ts` | 790 |
| 优先级计算器 | `canvas-progress-tracker/obsidian-plugin/src/services/PriorityCalculatorService.ts` | 627 |
| 插件设置 | `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` | ~400 |
| 设置类型 | `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` | ~200 |
| OpenAPI规范 | `specs/api/fastapi-backend-api.openapi.yml` | ~500 |

---

## Story Manager Handoff

当准备实施时，请按以下顺序执行：

1. **Week 1**: Story 32.1 → Story 32.2 (顺序依赖)
2. **Week 2**: Story 32.3 + Story 32.4 (可并行)
3. **Week 3**: Story 32.5 → Story 32.6 + Story 32.7 (32.5后可并行)

使用 `/BMad:agents:dev` 或 `*create-brownfield-story` 开始实施具体Story。

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-18 | 0.1 | Initial draft based on deep research | PM Agent (John) |
| 2026-01-18 | 0.2 | **删除Story 32.5** (与EPIC-30 Story 30.8重复)，节省6小时；更新Story 32.6依赖 | PM Agent (John) |

---
