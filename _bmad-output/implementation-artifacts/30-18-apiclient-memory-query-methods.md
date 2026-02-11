# Story 30.18: ApiClient Memory 查询方法补全

**Story ID**: 30.18
**Epic**: EPIC-30 (Memory System Complete Activation)
**Priority**: P1
**Status**: done
**Estimated Hours**: 6

---

## Story

作为 Obsidian 插件的开发者，我需要 ApiClient 中包含完整的 Memory API 查询方法，以便 MemoryQueryService 和其他组件可以通过统一的 API 客户端访问后端记忆系统端点，而不是各自直接发起 HTTP 请求。

## Background

当前 ApiClient (`canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`) 只有 1 个 Memory 方法 (`recordLearningEvent`)，
但后端 `backend/app/api/v1/endpoints/memory.py` 有 6 个端点。缺失 5 个查询方法导致 MemoryQueryService 需要绕过 ApiClient 直接使用 `requestUrl`，
破坏了统一 API 层的架构设计。

**后端 Memory API 端点清单:**
| 端点 | 方法 | ApiClient 状态 |
|------|------|---------------|
| `POST /memory/episodes` | `recordLearningEvent()` | ✅ 已有 |
| `GET /memory/episodes` | ❌ 缺失 | 需要补全 |
| `GET /memory/concepts/{id}/history` | ❌ 缺失 | 需要补全 |
| `GET /memory/review-suggestions` | ❌ 缺失 | 需要补全 |
| `GET /memory/health` | ❌ 缺失 | 需要补全 |
| `POST /memory/episodes/batch` | ❌ 缺失 | 需要补全 |

## Acceptance Criteria

- AC-30.18.1: ApiClient 新增 `getLearningHistory()` 方法，调用 `GET /memory/episodes`，支持 user_id, subject, concept, 分页参数
- AC-30.18.2: ApiClient 新增 `getConceptHistory()` 方法，调用 `GET /memory/concepts/{id}/history`
- AC-30.18.3: ApiClient 新增 `getReviewSuggestions()` 方法，调用 `GET /memory/review-suggestions`，支持 subject 过滤
- AC-30.18.4: ApiClient 新增 `getMemoryHealth()` 方法，调用 `GET /memory/health`
- AC-30.18.5: ApiClient 新增 `recordBatchLearningEvents()` 方法，调用 `POST /memory/episodes/batch`
- AC-30.18.6: 所有新增方法的 TypeScript 类型定义在 `types.ts` 中
- AC-30.18.7: 编译通过 (`npm run build` 成功)

## Tasks/Subtasks

- [x] Task 1: 在 `types.ts` 中添加 Memory API TypeScript 类型定义
  - [x] 1.1: LearningHistoryItem, LearningHistoryResponse 类型
  - [x] 1.2: ConceptHistoryTimeline, ScoreTrend, ConceptHistoryResponse 类型
  - [x] 1.3: ReviewSuggestionItem 类型
  - [x] 1.4: MemoryHealthResponse (含 LayerHealthStatus) 类型
  - [x] 1.5: BatchEventItem, BatchEpisodesRequest, BatchEpisodesResponse 类型
- [x] Task 2: 在 `ApiClient.ts` 中实现 5 个 Memory 查询方法
  - [x] 2.1: `getLearningHistory()` — GET /memory/episodes
  - [x] 2.2: `getConceptHistory()` — GET /memory/concepts/{id}/history
  - [x] 2.3: `getReviewSuggestions()` — GET /memory/review-suggestions
  - [x] 2.4: `getMemoryHealth()` — GET /memory/health
  - [x] 2.5: `recordBatchLearningEvents()` — POST /memory/episodes/batch
- [x] Task 3: 编译验证
  - [x] 3.1: `npm run build` 无编译错误
  - [x] 3.2: vault main.js 已更新 (907653 bytes, 2026-02-10T02:08)

## Dev Notes

### Architecture Requirements
- 所有新方法遵循 ApiClient 现有的 `this.request<T>()` 模式
- GET 请求使用 URLSearchParams 构建查询字符串
- fire-and-forget 模式仅适用于 recordLearningEvent，查询方法应正常抛出错误
- 类型定义必须与后端 Pydantic 模型 `backend/app/models/memory_schemas.py` 一致

### Key Files
- `canvas-progress-tracker/obsidian-plugin/src/api/types.ts` — 类型定义
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` — API 客户端
- `backend/app/models/memory_schemas.py` — 后端 Pydantic 模型 (参考)
- `backend/app/api/v1/endpoints/memory.py` — 后端端点 (参考)

## Dev Agent Record

### Implementation Plan
1. 在 types.ts 中添加 16 个 Memory API TypeScript 接口（带 `Memory` 前缀避免命名冲突）
2. 在 ApiClient.ts 中添加 5 个查询方法，遵循 `this.request<T>()` 模式
3. GET 方法使用 URLSearchParams 构建查询字符串
4. 编译验证 + vault main.js 部署

### Debug Log
无错误。tsc + esbuild 一次编译通过。

### Completion Notes
- 所有 17 个类型使用 `Memory` 前缀（如 `MemoryLearningHistoryItem`）避免与 MemoryQueryService 中已有类型冲突
- 查询方法使用 10s 超时 + try-catch + graceful degradation (Code Review H1 修复)
- batch 方法使用 30s 超时 + 客户端 max 50 校验 (Code Review M2 修复)
- 所有查询方法统一使用 query object 模式 (Code Review M1 修复)
- `getConceptHistory()` 使用 `encodeURIComponent` 编码 conceptId 路径参数
- 添加了 `LearningHistoryQuery`, `ConceptHistoryQuery`, `ReviewSuggestionsQuery` 参数接口

## File List
- `canvas-progress-tracker/obsidian-plugin/src/api/types.ts` — 新增 17 个 Memory API 类型接口
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` — 新增 5 个 Memory 查询方法 + import 更新

## Change Log
- 2026-02-10: Story 30.18 实现完成 — 5 个 Memory API 查询方法补全到 ApiClient
- 2026-02-10: Code Review 修复 — 超时控制、graceful degradation、API 风格统一、batch 校验
