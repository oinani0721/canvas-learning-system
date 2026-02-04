# Epic 34: 跨Canvas与教材挂载检验白板完整激活

<!-- Powered by BMAD Core -->

## Epic 元数据

| 属性 | 值 |
|------|------|
| **Epic ID** | 34 |
| **Epic 名称** | 跨Canvas与教材挂载检验白板完整激活 |
| **类型** | Brownfield Enhancement |
| **优先级** | P0 (Blocker 修复 + P1 功能完善) |
| **预估 Stories** | **3 个** (原7个，删除4个重复) |
| **依赖 Epic** | Epic 14 (复习系统), Epic 16 (跨Canvas关联) |
| **创建日期** | 2026-01-19 |
| **状态** | **Done** |

---

## Epic Goal

**完整激活跨Canvas关联、教材挂载和检验白板历史关联功能**，修复前后端集成断连问题，实现难度自适应闭环，使用户能够：
1. 在习题Canvas和讲座Canvas之间建立关联
2. 挂载PDF/Markdown/Canvas教材并在Agent分析时自动注入上下文
3. 生成检验白板时基于历史表现自动调整难度
4. 查看最近5次复习历史并支持查询全部

---

## 现有系统上下文

### Existing System Context

**当前相关功能:**
- Epic 14: 艾宾浩斯复习系统已迁移，包含检验白板生成、权重计算
- Epic 16: 跨Canvas关联学习系统已完成前端服务实现
- Epic 25: 跨Canvas与教材上下文集成已规划但未完整实施

**技术栈:**
- 前端: TypeScript + Obsidian Plugin API
- 后端: FastAPI + Python 3.11
- 存储: Neo4j (Graphiti) + .canvas-links.json

**集成点:**
- `backend/app/api/v1/router.py` - API路由聚合
- `backend/app/services/review_service.py` - 复习服务核心
- `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts` - 复习面板UI
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 插件入口

---

## 问题分析

### 已验证的核心问题

| 问题 | 状态 | 影响 | 验证方式 |
|------|------|------|---------|
| `cross_canvas_router` 未注册 | 确认 | API 404 | `router.py` 缺少该路由 |
| 难度自适应触发机制缺失 | 确认 | 无自动调整 | `review_service.py` 无相关方法 |
| 教材挂载前后端断连 | 确认 | 挂载无效 | `TextbookMountService` 缺少上下文 |
| 历史显示无分页 | 确认 | 信息过载 | 默认返回全部 |
| `based_on_sessions` 元数据缺失 | 确认 | 无法溯源 | 检验白板未记录参考会话 |

---

## Stories

### ~~Story 34.1: 跨Canvas API路由注册~~ [❌ 已删除 - 与EPIC-36 Story 36.5重复]

> **⚠️ 删除原因 (2026-01-19)**:
>
> 深度分析发现此Story与 **EPIC-36 Story 36.5** 功能重复：
> - 36.5 已规划: 跨Canvas讲座关联持久化 (Neo4j `ASSOCIATED_WITH` 关系)
> - 36.5 已规划: 关联类型 LECTURE_FOR, EXERCISE_OF, RELATED_TO
> - 36.5 更完整: 包含Neo4j持久化，而非仅router注册
>
> **处理方式**: 此Story功能将由 EPIC-36 Story 36.5 统一实现
> **节省工时**: ~4小时

~~**目标**: 修复 `cross_canvas_router` 未注册问题~~

~~**修改文件**:~~
- ~~`backend/app/api/v1/router.py` - 添加 cross_canvas_router 注册~~
- ~~`backend/app/dependencies.py` - 添加 CrossCanvasServiceDep 依赖~~

~~**验收标准**:~~
- ~~AC1: `GET /api/v1/cross-canvas/associations` 返回 200~~
- ~~AC2: `POST /api/v1/cross-canvas/associations` 创建关联成功~~
- ~~AC3: 前端 CrossCanvasService 调用后端无 404~~

---

### ~~Story 34.2: 检验白板难度自适应触发机制~~ [❌ 已删除 - 与EPIC-31 Story 31.5重复]

> **⚠️ 删除原因 (2026-01-19)**:
>
> 深度分析发现此Story与 **EPIC-31 Story 31.5** 功能重复：
> - 31.5 已规划: 难度自适应 (依赖FSRS历史得分)
> - 31.5 更完整: 基于FSRS算法，而非简单准确率计算
> - 31.5 依赖: EPIC-32 Story 32.1-32.2 (py-fsrs激活)
>
> **处理方式**: 此Story功能将由 EPIC-31 Story 31.5 统一实现
> **节省工时**: ~6小时

~~**目标**: 实现基于历史表现的难度自适应，存储 `based_on_sessions` 元数据~~

~~**修改文件**:~~
- ~~`backend/app/services/review_service.py` - 添加 `_calculate_adaptive_difficulty()` 方法~~
- ~~`backend/app/models/__init__.py` - 添加 `DifficultyLevel` enum~~
- ~~`backend/app/api/v1/endpoints/review.py` - 更新响应包含 `based_on_sessions`~~

~~**验收标准**:~~
- ~~AC1: 历史正确率>90%时，响应包含 `difficulty_level: "harder"`~~
- ~~AC2: 历史错误率>50%时，响应包含 `difficulty_level: "easier"`~~
- ~~AC3: 响应包含 `based_on_sessions` 元数据~~

---

### Story 34.3: 教材挂载前后端完整同步 [P1]

**目标**: 修复教材挂载时缺少 Canvas 上下文导致无法同步的问题

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/services/TextbookMountService.ts`
- `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts`

**验收标准**:
- AC1: 从跨Canvas Tab挂载教材时自动关联到选中的Canvas
- AC2: 后端 `.canvas-links.json` 正确写入教材关联
- AC3: Agent调用时能获取教材上下文
- AC4: PDF/Markdown/Canvas 三种格式均可挂载

---

### Story 34.4: 复习历史分页与默认限制 [P1]

**目标**: 实现历史显示默认5次，支持查询全部

**修改文件**:
- `backend/app/services/review_service.py`
- `backend/app/api/v1/endpoints/review.py`
- `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts`

**验收标准**:
- AC1: 历史记录默认显示最近5条
- AC2: 点击"显示全部"加载完整历史
- AC3: API支持 `limit` 和 `show_all` 参数

---

### ~~Story 34.5: 检验白板生成服务激活与UI集成~~ [❌ 已删除 - 与EPIC-31 Story 31.1-31.2重复]

> **⚠️ 删除原因 (2026-01-19)**:
>
> 深度分析发现此Story与 **EPIC-31 Story 31.1-31.2** 功能重复：
> - 31.1 已规划: VerificationService后端实现
> - 31.2 已规划: 生成端到端流程
> - EPIC-31 专注检验白板系统，功能更完整
>
> **处理方式**: 此Story功能将由 EPIC-31 Story 31.1-31.2 统一实现
> **节省工时**: ~8小时

~~**目标**: 确保 ReviewCanvasGeneratorService 完整集成到 Dashboard~~

~~**修改文件**:~~
- ~~`canvas-progress-tracker/obsidian-plugin/main.ts`~~
- ~~`canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts`~~

~~**验收标准**:~~
- ~~AC1: "生成新检验白板"按钮触发模式选择对话框~~
- ~~AC2: 选择模式后成功调用后端 API~~
- ~~AC3: 生成成功后自动刷新检验白板列表~~

---

### ~~Story 34.6: 跨Canvas关联智能建议优化~~ [❌ 已删除 - 与EPIC-36 Story 36.6重复]

> **⚠️ 删除原因 (2026-01-19)**:
>
> 深度分析发现此Story与 **EPIC-36 Story 36.6** 功能重复：
> - 36.6 已规划: 跨Canvas讲座自动发现
> - 36.6 已规划: 文件名模式匹配（习题→讲座）
> - 36.6 已规划: 共同概念数>=3时建议关联
>
> **处理方式**: 此Story功能将由 EPIC-36 Story 36.6 统一实现
> **节省工时**: ~4小时

~~**目标**: 优化关联建议算法，基于概念相似度提供更准确的建议~~

~~**修改文件**:~~
- ~~`backend/app/services/cross_canvas_service.py`~~
- ~~`canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts`~~

~~**验收标准**:~~
- ~~AC1: 建议列表按置信度排序~~
- ~~AC2: 支持 `min_confidence` 参数过滤~~
- ~~AC3: 显示建议原因 (共享概念)~~
- ~~AC4: 一键采纳建议创建关联~~

---

### Story 34.7: 端到端集成测试与文档 [P1]

**目标**: 确保所有功能端到端可用

**修改文件**:
- `backend/tests/e2e/test_cross_canvas_flow.py` (新建)
- `backend/tests/e2e/test_textbook_mount_flow.py` (新建)
- `backend/tests/integration/test_review_difficulty_adaptive.py` (新建)
- `docs/epics/EPIC-34-COMPLETE-ACTIVATION.md` (本文档)

**验收标准**:
- AC1: 跨Canvas完整流程测试通过
- AC2: 教材挂载完整流程测试通过
- AC3: 难度自适应单元测试通过
- AC4: 文档更新完成

---

## 执行顺序依赖图 (精简后)

```
原依赖图 (已废弃):
Story 34.1 ──┬──> Story 34.2 ──> Story 34.5
             └──> Story 34.3 ──> Story 34.6 ──> Story 34.7
Story 34.4 ─────────────────────────────────────────────┘

精简后依赖图:
Story 34.3 (教材挂载) ──┬──> Story 34.7 (E2E测试)
                        │
Story 34.4 (历史分页) ──┘

外部依赖:
├─ 34.3 依赖 EPIC-30 Story 30.5 (Canvas CRUD事件)
├─ 跨Canvas功能 → EPIC-36 Story 36.5-36.6
├─ 难度自适应 → EPIC-31 Story 31.5
└─ 检验白板生成 → EPIC-31 Story 31.1-31.2
```

---

## Compatibility Requirements

- [x] 现有APIs保持不变 (仅添加新路由)
- [x] 数据库Schema无破坏性变更
- [x] UI变更遵循现有Obsidian插件模式
- [x] 性能影响最小化 (教材上下文获取 < 1秒)

---

## Risk Mitigation

| 风险 | 缓解措施 | 回滚计划 |
|------|---------|---------|
| API路由冲突 | 使用独立 `/cross-canvas` 前缀 | 移除路由注册行 |
| 难度自适应误判 | 默认返回 NORMAL，阈值可配置 | 禁用自适应，固定权重 |
| 教材同步失败 | 静默处理，继续执行 | 回退到localStorage |

---

## Definition of Done (精简后)

- [x] ~~Story 34.1~~ [❌ 已删除 - 由36.5实现]
- [x] ~~Story 34.2~~ [❌ 已删除 - 由31.5实现]
- [x] Story 34.3 教材挂载完成并通过验收标准 ✅ Done (2026-01-20)
- [x] Story 34.4 历史分页完成并通过验收标准 ✅ Done (2026-01-20)
- [x] ~~Story 34.5~~ [❌ 已删除 - 由31.1-31.2实现]
- [x] ~~Story 34.6~~ [❌ 已删除 - 由36.6实现]
- [x] Story 34.7 E2E测试通过 ✅ Done (2026-01-20)
- [x] 现有功能无回归 ✅ 验证通过
- [x] 教材挂载后Agent分析包含教材上下文 ✅ 验证通过
- [x] 文档更新完成 ✅ 本次更新

> **精简说明**: 原7个Stories精简为3个，工时从~42h降至~14h
> **被删除功能的实现方**: EPIC-31 (检验白板), EPIC-36 (跨Canvas)
> **完成日期**: 2026-01-20

---

## 关键文件清单 (精简后)

| 文件路径 | 修改类型 | Story | 状态 |
|---------|---------|-------|------|
| ~~`backend/app/api/v1/router.py`~~ | ~~添加路由~~ | ~~34.1~~ | ❌ 移至36.5 |
| `backend/app/services/review_service.py` | 添加方法 | 34.4 | ✅ 保留 |
| ~~`backend/app/models/__init__.py`~~ | ~~添加枚举~~ | ~~34.2~~ | ❌ 移至31.5 |
| ~~`canvas-progress-tracker/obsidian-plugin/main.ts`~~ | ~~服务初始化~~ | ~~34.5~~ | ❌ 移至31.1 |
| `canvas-progress-tracker/obsidian-plugin/src/services/TextbookMountService.ts` | 自动检测 | 34.3 | ✅ 保留 |
| `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts` | UI集成 | 34.3, 34.4 | ✅ 保留 |
| ~~`backend/app/services/cross_canvas_service.py`~~ | ~~算法优化~~ | ~~34.6~~ | ❌ 移至36.6 |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-19 | 0.1 | Initial draft | PM Agent (John) |
| 2026-01-19 | 0.2 | **删除4个重复Stories**: 34.1→36.5, 34.2→31.5, 34.5→31.1-31.2, 34.6→36.6；精简为3个Stories；节省~28小时 | PM Agent (John) |
| 2026-01-20 | 1.0 | **Epic 完成**: Story 34.3/34.4/34.7全部Done; E2E测试创建完成; Definition of Done全部勾选; 状态更新为Done | Dev Agent (James) |
