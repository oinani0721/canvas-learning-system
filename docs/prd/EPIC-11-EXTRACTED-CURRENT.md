---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial PRD with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 0
  fr_count: 0
  nfr_count: 0
---

# Epic 11 当前版本内容（从PRD提取）

**提取时间**: 2025-11-13
**来源行**: 第4385-4553行

---

### Epic 11: FastAPI后端基础架构搭建

**Epic ID**: Epic 11
**优先级**: P0
**预计时间**: 2周 (43小时)
**依赖**: Epic 0（技术验证基础设施）
**阻塞**: Epic 12, 13, 14

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/fastapi_tiangolo` (22,734 snippets)
- 查询主题示例: "dependency injection", "async operations", "APIRouter"

**验证检查点**:
- SM Agent编写Story时必须查询并记录API用法
- Dev Agent开发时必须在代码中添加文档引用注释
- Code Review必须验证所有API调用的正确性

#### 目标
搭建高性能、可扩展的FastAPI后端基础架构，作为Canvas学习系统Web化的核心API层。采用4层架构设计（API Layer → Service Layer → Core Layer → Infrastructure Layer），实现19个RESTful API endpoints，集成现有canvas_utils.py，支持异步操作和后台任务。

#### Story列表

| Story ID | Story名称 | 预计时间 | 优先级 |
|----------|----------|---------|--------|
| Story 11.1 | FastAPI应用初始化和基础配置 | 4-6小时 | P0 |
| Story 11.2 | 路由系统和APIRouter配置 | 5-7小时 | P0 |
| Story 11.3 | 依赖注入系统设计 | 6-8小时 | P0 |
| Story 11.4 | 中间件和错误处理 | 5-7小时 | P1 |
| Story 11.5 | 异步操作和后台任务 | 6-9小时 | P1 |
| Story 11.6 | API文档和测试框架 | 4-6小时 | P1 |

**总时间**: 30-43小时

#### 核心架构

**4层架构设计**:
```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理（Pydantic Settings）
│   ├── dependencies.py         # 全局依赖项（DI）
│   ├── api/v1/endpoints/       # API endpoints
│   │   ├── canvas.py           # Canvas操作 (6 endpoints)
│   │   ├── agents.py           # Agent调用 (9 endpoints)
│   │   └── review.py           # 检验白板 (3 endpoints)
│   ├── models/                 # Pydantic模型 (31个)
│   ├── services/               # 业务逻辑层
│   ├── core/                   # 核心层（canvas_utils.py集成）
│   └── middleware/             # 中间件
└── tests/                      # 测试
```

#### 关键交付物

**规划文档** (已完成):
- ✅ Sprint Kick-off: `docs/SPRINT-KICKOFF-EPIC-11.md`
- ✅ Epic 11详细规划: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`
- ✅ 技术架构设计: `docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md`
- ✅ API接口规范: `docs/api/EPIC-11-API-SPECIFICATION.md`
- ✅ 数据模型设计: `docs/architecture/EPIC-11-DATA-MODELS.md`
- ✅ PM-SM交接文档: `docs/PM-TO-SM-HANDOFF-EPIC-11.md`

**代码交付物** (待开发):
- [ ] FastAPI应用核心代码（`app/main.py`, `app/config.py`）
- [ ] 19个API endpoints实现
- [ ] 31个Pydantic数据模型
- [ ] 中间件系统（日志、错误处理、CORS）
- [ ] 异步服务层
- [ ] pytest测试套件（覆盖率 ≥ 85%）

#### API Endpoints概览

**Canvas操作** (6 endpoints):
- `GET /api/v1/canvas/{canvas_name}` - 读取Canvas文件
- `POST /api/v1/canvas/{canvas_name}/nodes` - 创建节点
- `PUT /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 更新节点
- `DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 删除节点
- `POST /api/v1/canvas/{canvas_name}/edges` - 创建边
- `DELETE /api/v1/canvas/{canvas_name}/edges/{edge_id}` - 删除边

**Agent调用** (9 endpoints):
- `POST /api/v1/agents/decompose/basic` - 基础拆解
- `POST /api/v1/agents/decompose/deep` - 深度拆解
- `POST /api/v1/agents/score` - 评分
- `POST /api/v1/agents/explain/oral` - 口语化解释
- `POST /api/v1/agents/explain/clarification` - 澄清路径
- `POST /api/v1/agents/explain/comparison` - 对比表
- `POST /api/v1/agents/explain/memory` - 记忆锚点
- `POST /api/v1/agents/explain/four-level` - 四层次解释
- `POST /api/v1/agents/explain/example` - 例题教学

**检验白板** (3 endpoints):
- `POST /api/v1/review/generate` - 生成检验白板
- `GET /api/v1/review/{canvas_name}/progress` - 获取检验进度
- `POST /api/v1/review/sync` - 同步检验结果

**健康检查** (1 endpoint):
- `GET /api/v1/health` - 健康检查

#### 数据模型概览

**31个Pydantic模型**, 分为4类:
1. **Canvas模型** (10个): `NodeBase`, `NodeCreate`, `NodeUpdate`, `NodeRead`, `EdgeBase`, `EdgeCreate`, `EdgeRead`, `CanvasData`, `CanvasMeta`, `CanvasResponse`
2. **Agent模型** (12个): `DecomposeRequest`, `DecomposeResponse`, `ScoreRequest`, `ScoreResponse`, `ScoreDimensions`, `ScoreFeedback`, `ExplainRequest`, `ExplainResponse`, `AgentType`, `AgentMeta`, `AgentRecommendation`, `ErrorDetail`
3. **Review模型** (5个): `ReviewGenerateRequest`, `ReviewGenerateResponse`, `ReviewProgressResponse`, `ReviewSyncRequest`, `ReviewSyncResponse`
4. **Common模型** (4个): `SuccessResponse`, `ErrorResponse`, `PaginationMeta`, `HealthCheckResponse`

#### 技术栈

**核心框架**:
- FastAPI 0.104+
- Pydantic 2.5+
- Uvicorn 0.24+

**开发工具**:
- pytest 7.4+
- pytest-asyncio
- httpx (async client for testing)
- python-dotenv

**架构模式**:
- 依赖注入（`Depends()`）
- 异步优先（`async/await`）
- API版本控制（`/api/v1/`）
- Pydantic Settings配置管理

#### 成功标准

**功能验收**:
- ✅ 19个API endpoints全部实现并可正常调用
- ✅ 所有endpoints返回符合规范的JSON响应
- ✅ 错误处理覆盖所有预期错误场景（400/404/500）
- ✅ Canvas文件读写操作成功
- ✅ Agent调用成功返回结果

**技术验收**:
- ✅ 所有API调用已通过Context7验证
- ✅ 代码包含文档引用注释
- ✅ 依赖注入系统正常工作
- ✅ 中间件正确处理请求/响应
- ✅ 异步操作无阻塞

**测试验收**:
- ✅ pytest测试覆盖率 ≥ 85%
- ✅ 所有API endpoints有对应的测试用例
- ✅ 异步操作有集成测试
- ✅ 错误处理有单元测试

**文档验收**:
- ✅ FastAPI自动生成的Swagger文档可访问
- ✅ API endpoints有完整的docstring
- ✅ 所有技术实现可追溯到Context7查询

**性能验收**:
- ✅ 单个API请求响应时间 < 500ms
- ✅ Canvas文件读取 < 200ms
- ✅ Agent调用 < 5秒（不含Agent执行时间）

**集成验收**（与Epic 12配合）:
- ✅ FastAPI endpoints可被Epic 12 LangGraph调用
- ✅ 依赖注入系统支持LangGraph集成
- ✅ 异步操作不阻塞LangGraph workflow

**详细文档**: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`

---
