---
story_id: "1.10"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["1.7"]
blocks: []
trace:
  - "FR-SYS-06"
  - "FR-OPS-01"
---

# Story 1.10: 健康端点统一 + Plugin 状态指示

Status: ready-for-dev

## Story

As a 开发者/学习者,
I want 一个统一的健康检查端点能告诉我"哪些组件正常、哪些降级、哪些挂了",
So that 我能快速定位问题（是 Neo4j 没启动？还是 Ollama 模型没下载？还是 MCP 工具注册失败？）而不是到处翻日志猜。

## 通俗化解释（给学习者）

> **一句话说**: 给你一个"仪表盘"，一眼看出系统哪里绿灯（正常）、哪里黄灯（勉强能用）、哪里红灯（挂了）。

**你会遇到的场景**:
- 你打开 Canvas 应用，AI 回答变得很慢或完全不回答，你不知道是哪里出了问题
- 你问了一个问题，返回的错误信息是"Internal Server Error"，完全看不出是什么服务挂了
- 你想帮同学排查问题，但需要逐个检查 Neo4j、Ollama、LanceDB 是否正常，很麻烦

**这个功能帮你**:
- 访问一个 URL 就能看到所有组件状态：Neo4j ✅ / Ollama ⚠️(degraded) / MCP ✅ / LanceDB ❌
- 降级模式说明：比如 Ollama 没启动时，系统仍能工作但没有 AI 功能（用缓存结果）
- 每个红灯组件附带修复建议（如"运行 `ollama pull bge-m3` 安装模型"）

**用个比喻**: 就像车的仪表盘 — 油量低了亮黄灯提醒加油，发动机坏了亮红灯告诉你别开了。而不是车突然熄火让你猜原因。

## Acceptance Criteria

1. **Given** 后端正在运行
   **When** 发送 `GET /api/v1/health/detailed`
   **Then** 返回所有组件的 3 级状态：`ready`（正常）/ `degraded`（可用但受限）/ `unavailable`（不可用）
   **And** 每个组件包含：`{name, status, latency_ms, detail, fix_hint}`

2. **Given** Neo4j 连接正常但 Graphiti worker 未启动
   **When** 查询详细健康检查
   **Then** `neo4j.status = "ready"` 且 `graphiti.status = "degraded"`
   **And** `graphiti.detail = "Episode worker not started"` + `graphiti.fix_hint = "检查 Phase 2 启动日志"`

3. **Given** Ollama 服务不可达
   **When** 查询详细健康检查
   **Then** `ollama.status = "unavailable"` 且 `ollama.fix_hint = "确保 Ollama 正在运行: ollama serve"`
   **And** 总体状态为 `degraded`（不是 `unavailable`，因为其他组件仍可用）

4. **Given** 现有 6 个健康相关端点
   **When** 审查路由表
   **Then** `/health`（基础）+ `/health/detailed`（新增，含 3 级状态）+ `/metrics`（Prometheus） 三个端点清晰分工
   **And** Docker healthcheck 仍使用 `/health`（快速响应，不含外部依赖检测）

5. **Given** 健康检查响应
   **When** 所有组件都是 `ready`
   **Then** 总体 `overall_status = "ready"` 且 HTTP 200
   **When** 任一组件 `degraded`
   **Then** 总体 `overall_status = "degraded"` 且 HTTP 200
   **When** 核心组件（Neo4j）`unavailable`
   **Then** 总体 `overall_status = "unavailable"` 且 HTTP 503

6. **Given** 健康检查运行
   **When** 检测每个组件
   **Then** 每个组件检测有 5 秒超时
   **And** 超时的组件标记为 `unavailable`，不阻塞其他组件检测

## Tasks / Subtasks

- [ ] Task 1: 统一健康检查模型 (AC: #1, #5)
  - [ ] 1.1: 定义 `ComponentHealth(name, status: Literal["ready","degraded","unavailable"], latency_ms, detail, fix_hint)` Pydantic 模型
  - [ ] 1.2: 定义 `DetailedHealthResponse(overall_status, components: List[ComponentHealth], checked_at)` 模型
  - [ ] 1.3: 实现 overall_status 聚合逻辑（最差组件决定总体状态，核心 vs 非核心区分）

- [ ] Task 2: 组件探针实现 (AC: #2, #3, #6)
  - [ ] 2.1: Neo4j 探针 — bolt 连接 + `RETURN 1 AS ping` 查询（复用现有 `health.py:141-149` 的模式感知逻辑）
  - [ ] 2.2: Ollama 探针 — `GET http://localhost:11434/api/tags` 检查 bge-m3 模型存在
  - [ ] 2.3: LanceDB 探针 — 检查 data/lancedb 目录可访问 + 表数量
  - [ ] 2.4: Graphiti/EpisodeWorker 探针 — 检查 `app.state.episode_worker` 状态（参考 `main.py:263-285` Phase 2）
  - [ ] 2.5: MCP 探针 — 检查注册工具数量
  - [ ] 2.6: 每个探针独立 5 秒超时（`asyncio.wait_for`）

- [ ] Task 3: 新端点注册 (AC: #4)
  - [ ] 3.1: 在 `health.py` 中新增 `GET /health/detailed` 端点
  - [ ] 3.2: 保持现有 `GET /health` 不变（Docker healthcheck 依赖它）
  - [ ] 3.3: 整理现有端点注释，说明分工

- [ ] Task 4: 修复建议数据库 (AC: #2, #3)
  - [ ] 4.1: 为每个组件的常见错误维护 fix_hint 映射
  - [ ] 4.2: Neo4j: "连接被拒绝" → "运行 docker-compose up neo4j"
  - [ ] 4.3: Ollama: "模型不存在" → "运行 ollama pull BAAI/bge-m3"
  - [ ] 4.4: 用 structlog 记录每次降级/不可用事件

- [ ] Task 5: 测试 (AC: #1, #5, #6)
  - [ ] 5.1: `backend/tests/unit/test_health_detailed.py` — 各组件状态组合 + overall 聚合
  - [ ] 5.2: 超时场景测试 — 某组件 >5s 应标记 unavailable
  - [ ] 5.3: 现有 `/health` 端点回归测试

## Dev Notes

- **现有 health 端点**: `health.py` 已有 `/health`（基础）、`/metrics`（Prometheus）、`/metrics/summary`（JSON），但缺乏组件级 3 级状态
- **R12 [I1] Health vs Availability**: 现有端点混淆了"服务在运行"和"服务可用"—— Neo4j 连接正常不代表 Graphiti 可用（Phase 2 可能 degraded）
- **Phase 2 降级模式**: `main.py:263-285` 已实现 Graphiti degraded 模式，但没暴露给健康端点
- **Docker healthcheck**: `docker-compose.yml:170-175` 用 `curl /api/v1/health`，必须保持快速响应（<1s），不能依赖外部探针
- **4-way Neo4j 分类**: `health.py:141-149` 已有 NEO4J ok / NEO4J degraded / JSON_FALLBACK / unavailable 逻辑，可复用
- **R9 冷启动数据**: 冷启动 120-150s，健康检查超时应考虑冷启动期（start_period）
- **QA 来源**: R10 Part D（健康检查方案）+ R12 [I1]（Health vs Availability 混淆）

### Project Structure Notes

- 修改文件: `backend/app/api/v1/endpoints/health.py`（新增 `/health/detailed`）
- 新建文件: `backend/app/services/health_probes.py`（组件探针集合）
- 修改文件: `backend/app/models/schemas.py`（新增健康检查 Pydantic 模型）
- 测试文件: `backend/tests/unit/test_health_detailed.py`

### References

- [Source: backend/app/api/v1/endpoints/health.py] — 现有 6 个健康端点
- [Source: docker-compose.yml:170-175] — Docker healthcheck 配置
- [Source: backend/app/main.py:263-285] — Phase 2 Graphiti degraded 模式
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — R10 Part D, R12 [I1]

## UAT Script

> 非技术用户验收脚本

1. **验证详细健康检查** (AC: #1)
   - 打开浏览器访问 `http://localhost:8001/api/v1/health/detailed`
   - 应看到每个组件的状态（绿色 ready / 黄色 degraded / 红色 unavailable）
   - 每个组件还显示响应时间

2. **验证降级提示** (AC: #2, #3)
   - 故意关闭 Ollama（`pkill ollama`），再次访问健康检查
   - Ollama 应显示红色 unavailable，附带修复建议
   - 总体状态应变为黄色 degraded（不是红色，因为 Neo4j 还正常）

3. **验证快速端点不受影响** (AC: #4)
   - 访问 `http://localhost:8001/api/v1/health`（基础端点）
   - 应在 1 秒内返回，不检查外部组件

4. **验证修复建议** (AC: #2)
   - 找到一个红色/黄色组件，按照 fix_hint 操作
   - 修复后再次检查，该组件应变绿

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.10.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_health_detailed.py -x -q` | 0 failed |
| CP-1.10.2 | ruff | `ruff check backend/app/api/v1/endpoints/health.py backend/app/services/health_probes.py` | exit 0 |
| CP-1.10.3 | curl | `curl -sf http://localhost:8001/api/v1/health/detailed` | HTTP 200 或 503 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R10 Part D**: 健康检查方案 — 需要细粒度组件状态，不是笼统的 "healthy/unhealthy"
2. **R12 [I1]**: 承认 Health vs Availability 混淆 — 服务在运行 ≠ 服务可用，需要 3 级状态区分
3. **R9 冷启动**: 数据量 20-50MB / 冷启动 120-150s — 健康检查超时设计需考虑

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
