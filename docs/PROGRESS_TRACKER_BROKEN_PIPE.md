# ProgressTrackerView 断裂链路记录

## 问题描述

ProgressTrackerView（学习进度追踪面板）的 3 个数据面板全部无法加载数据，原因是前端调用的 API 端点在后端不存在。

## 断裂详情

| 前端调用 | 期望端点 | 后端实际端点 | 状态 |
|---------|---------|------------|------|
| `loadData()` line 187 | `GET /api/v1/progress/analyze` | 不存在 | BROKEN |
| `loadData()` line 201 | `GET /api/v1/progress/history` | 不存在 | BROKEN |
| concept trends line 199 | `GET /api/v1/progress/history` | 不存在 | BROKEN |

## 后端已有的相关端点

后端 `review.py` 中存在类似功能但路径不同的端点：

```
GET /api/v1/review/progress/multi/{original_canvas_path:path}
```

- 返回多次复习的进度对比数据
- 路径格式和请求参数与前端期望不匹配

## 受影响的 UI 面板

1. **当前进度** (`renderCurrentProgress()` line 357) — 显示本次复习评分分布
2. **历史对比** (`renderHistoryComparison()` line 513) — 对比多次复习分数变化
3. **概念趋势图** (`renderConceptTrends()` line 678) — 知识点掌握度变化曲线

## 文件位置

- 前端: `obsidian-plugin/src/views/ProgressTrackerView.ts` (27KB)
- 后端: `backend/app/api/v1/endpoints/review.py` (line 1128+)
- 前端类型: `SingleReviewProgress` (lines 33-41), `MultiReviewProgressData` (lines 72-77)

## 修复方案

### 方案 A：修改前端路由（推荐，改动小）

将前端 API 调用对齐到后端已有端点：
- `GET /progress/analyze` → `GET /review/progress/multi/{canvas_path}` + 取最新一次
- `GET /progress/history` → `GET /review/progress/multi/{canvas_path}` 全量

### 方案 B：新增后端端点

在后端新增 `/progress/analyze` 和 `/progress/history` 端点，匹配前端期望的请求/响应格式。

## 对核心功能的影响

**无影响**。Canvas 右键 → AI Agent 解释 → 知识图谱记录 的核心链路完全正常。ProgressTracker 是复习闭环的"可视化报告"部分，属于增强功能。

## 记录时间

2026-03-08
