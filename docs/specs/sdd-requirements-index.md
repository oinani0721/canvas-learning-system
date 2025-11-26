# SDD需求索引 (SDD Requirements Index)

**生成时间**: 2025-11-25 20:29:02
**生成脚本**: scripts/extract-sdd-requirements.py

---

## 📊 覆盖率总览

| 类别 | 总数 | 已覆盖 | 覆盖率 | 状态 |
|------|------|--------|--------|------|
| API端点 | 19 | 17 | 89.5% | ✅ |
| 数据模型 | 31 | 31 | 100.0% | ✅ |
| **总体** | 50 | 48 | 96.0% | ✅ |

**质量门禁**: 覆盖率需达到 ≥80% 才能通过Planning Finalize

---

## 🔗 API端点清单 (来自PRD Epic 15)

| 端点 | 方法 | 描述 | PRD位置 | OpenAPI状态 | 覆盖率 |
|------|------|------|---------|-------------|--------|

### Canvas操作

| /api/v1/canvas/{canvas_name} | `GET` | 读取Canvas文件 | EPIC-15-FastAPI.md:L94 | ✅已定义 | 100% |
| /api/v1/canvas/{canvas_name}/nodes | `POST` | 创建节点 | EPIC-15-FastAPI.md:L95 | ✅已定义 | 100% |
| /api/v1/canvas/{canvas_name}/nodes/{node_id} | `PUT` | 更新节点 | EPIC-15-FastAPI.md:L96 | ✅已定义 | 100% |
| /api/v1/canvas/{canvas_name}/nodes/{node_id} | `DELETE` | 删除节点 | EPIC-15-FastAPI.md:L97 | ✅已定义 | 100% |
| /api/v1/canvas/{canvas_name}/edges | `POST` | 创建边 | EPIC-15-FastAPI.md:L98 | ✅已定义 | 100% |
| /api/v1/canvas/{canvas_name}/edges/{edge_id} | `DELETE` | 删除边 | EPIC-15-FastAPI.md:L99 | ✅已定义 | 100% |

### Agent调用

| /api/v1/agents/decompose/basic | `POST` | 基础拆解 | EPIC-15-FastAPI.md:L102 | ✅已定义 | 100% |
| /api/v1/agents/decompose/deep | `POST` | 深度拆解 | EPIC-15-FastAPI.md:L103 | ✅已定义 | 100% |
| /api/v1/agents/score | `POST` | 评分 | EPIC-15-FastAPI.md:L104 | ✅已定义 | 100% |
| /api/v1/agents/explain/oral | `POST` | 口语化解释 | EPIC-15-FastAPI.md:L105 | ✅已定义 | 100% |
| /api/v1/agents/explain/clarification | `POST` | 澄清路径 | EPIC-15-FastAPI.md:L106 | ✅已定义 | 100% |
| /api/v1/agents/explain/comparison | `POST` | 对比表 | EPIC-15-FastAPI.md:L107 | ✅已定义 | 100% |
| /api/v1/agents/explain/memory | `POST` | 记忆锚点 | EPIC-15-FastAPI.md:L108 | ✅已定义 | 100% |
| /api/v1/agents/explain/four-level | `POST` | 四层次解释 | EPIC-15-FastAPI.md:L109 | ✅已定义 | 100% |
| /api/v1/agents/explain/example | `POST` | 例题教学 | EPIC-15-FastAPI.md:L110 | ✅已定义 | 100% |

### 检验白板

| /api/v1/review/generate | `POST` | 生成检验白板 | EPIC-15-FastAPI.md:L113 | ✅已定义 | 100% |
| /api/v1/review/{canvas_name}/progress | `GET` | 获取检验进度 | EPIC-15-FastAPI.md:L114 | ❌未定义 | 0% |
| /api/v1/review/sync | `POST` | 同步检验结果 | EPIC-15-FastAPI.md:L115 | ❌未定义 | 0% |

### 健康检查

| /api/v1/health | `GET` | 健康检查 | EPIC-15-FastAPI.md:L118 | ✅已定义 | 100% |

---

## 📦 数据模型清单 (来自PRD Epic 15)

| 模型名称 | 分类 | PRD位置 | Schema状态 | 覆盖率 |
|----------|------|---------|------------|--------|

### Canvas模型

| `NodeBase` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅node-base.schema.json | 100% |
| `NodeCreate` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅node-create.schema.json | 100% |
| `NodeUpdate` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅node-update.schema.json | 100% |
| `NodeRead` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅node-read.schema.json | 100% |
| `EdgeBase` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅edge-base.schema.json | 100% |
| `EdgeCreate` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅edge-create.schema.json | 100% |
| `EdgeRead` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅edge-read.schema.json | 100% |
| `CanvasData` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅canvas-data.schema.json | 100% |
| `CanvasMeta` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅canvas-meta.schema.json | 100% |
| `CanvasResponse` | Canvas模型 | EPIC-15-FastAPI.md:L126 | ✅canvas-response.schema.json | 100% |

### Agent模型

| `DecomposeRequest` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅decompose-request.schema.json | 100% |
| `DecomposeResponse` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅decompose-response.schema.json | 100% |
| `ScoreRequest` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅score-request.schema.json | 100% |
| `ScoreResponse` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅score-response.schema.json | 100% |
| `ScoreDimensions` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅score-dimensions.schema.json | 100% |
| `ScoreFeedback` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅score-feedback.schema.json | 100% |
| `ExplainRequest` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅explain-request.schema.json | 100% |
| `ExplainResponse` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅explain-response.schema.json | 100% |
| `AgentType` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅agent-type.schema.json | 100% |
| `AgentMeta` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅agent-meta.schema.json | 100% |
| `AgentRecommendation` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅agent-recommendation.schema.json | 100% |
| `ErrorDetail` | Agent模型 | EPIC-15-FastAPI.md:L128 | ✅error-detail.schema.json | 100% |

### Review模型

| `ReviewGenerateRequest` | Review模型 | EPIC-15-FastAPI.md:L130 | ✅review-generate-request.schema.json | 100% |
| `ReviewGenerateResponse` | Review模型 | EPIC-15-FastAPI.md:L130 | ✅review-generate-response.schema.json | 100% |
| `ReviewProgressResponse` | Review模型 | EPIC-15-FastAPI.md:L130 | ✅review-progress-response.schema.json | 100% |
| `ReviewSyncRequest` | Review模型 | EPIC-15-FastAPI.md:L130 | ✅review-sync-request.schema.json | 100% |
| `ReviewSyncResponse` | Review模型 | EPIC-15-FastAPI.md:L130 | ✅review-sync-response.schema.json | 100% |

### Common模型

| `SuccessResponse` | Common模型 | EPIC-15-FastAPI.md:L132 | ✅success-response.schema.json | 100% |
| `ErrorResponse` | Common模型 | EPIC-15-FastAPI.md:L132 | ✅error-response.schema.json | 100% |
| `PaginationMeta` | Common模型 | EPIC-15-FastAPI.md:L132 | ✅pagination-meta.schema.json | 100% |
| `HealthCheckResponse` | Common模型 | EPIC-15-FastAPI.md:L132 | ✅health-check-response.schema.json | 100% |

---

## 🔍 追溯矩阵

### PRD需求 → OpenAPI端点 → JSON Schema → Story

| PRD需求 | OpenAPI路径 | 相关Schema | Story引用 |
|---------|-------------|-----------|----------|
| 读取Canvas文件 | `GET /api/v1/canvas/{canvas_name}` | `CanvasResponse`, `DecomposeRequest` | _待关联_ |
| 创建节点 | `POST /api/v1/canvas/{canvas_name}/nodes` | `CanvasResponse`, `DecomposeRequest` | _待关联_ |
| 更新节点 | `PUT /api/v1/canvas/{canvas_name}/nodes/{node_id}` | `CanvasResponse`, `DecomposeRequest` | _待关联_ |
| 删除节点 | `DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id}` | `CanvasResponse`, `DecomposeRequest` | _待关联_ |
| 创建边 | `POST /api/v1/canvas/{canvas_name}/edges` | `CanvasResponse`, `DecomposeRequest` | _待关联_ |

_(追溯矩阵持续更新中...)_

---

## 📋 待创建SDD清单

### 缺失的OpenAPI端点
- [ ] `GET /api/v1/review/{canvas_name}/progress` - 获取检验进度 (❌未定义)
- [ ] `POST /api/v1/review/sync` - 同步检验结果 (❌未定义)

### 缺失的JSON Schema
_✅ 所有数据模型已定义Schema_

---

## 🛠️ 使用指南

### Architect创建OpenAPI端点

```bash
# 1. 读取本Index，确认待创建端点
# 2. 执行创建命令（含Context7验证）
@architect *create-openapi "/api/v1/canvas/{canvas_name}"

# 3. Index会自动更新覆盖率
```

### Architect创建JSON Schema

```bash
# 1. 读取本Index，确认待创建Schema
# 2. 执行创建命令（含Context7验证）
@architect *create-schemas "NodeCreate"

# 3. Index会自动更新覆盖率
```

### SM创建Story时检查

```bash
# SM Agent自动执行：
# 1. 读取SDD Index
# 2. 检查Story涉及的端点/模型是否已有SDD
# 3. 缺失则HALT，通知Architect补充
```

---

## 📌 注意事项

1. **本文件自动生成** - 请勿手动编辑统计数据
2. **更新频率** - 每次运行`scripts/extract-sdd-requirements.py`自动更新
3. **质量门禁** - Planning Finalize时检查覆盖率 ≥80%
4. **追溯完整性** - 确保每个SDD都能追溯到PRD需求

---

**文档版本**: 1.0
**最后更新**: {datetime.now().strftime('%Y-%m-%d')}
