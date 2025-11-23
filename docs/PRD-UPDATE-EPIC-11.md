# PRD更新报告 - Epic 11规划完成

**报告日期**: 2025-11-13
**PM Agent**: Sarah
**状态**: ⚠️ **需要更新PRD文件**

---

## 📋 更新摘要

Epic 11 PM阶段已完成所有规划文档（6个文件，~5,500行），但**PRD主文件尚未更新**以反映最新的Epic 11详细规划。

**需要更新的文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**需要更新的行数**: 第4385-4406行（Epic 11部分）

---

## 🔍 当前PRD内容 vs. 最新规划对比

### ❌ 当前PRD中的Epic 11（旧版本）

**位置**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` 第4385-4406行

```markdown
### Epic 11: FastAPI后端基础架构搭建

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/fastapi_tiangolo` (22,734 snippets)
- 查询主题示例: "dependency injection", "async operations", "APIRouter"

**验证检查点**:
- SM Agent编写Story时必须查询并记录API用法
- Dev Agent开发时必须在代码中添加文档引用注释
- Code Review必须验证所有API调用的正确性

---

**Story序列**:
- Story 11.1: FastAPI项目初始化和基础配置
- Story 11.2: canvas_utils.py集成到FastAPI
- Story 11.3: 核心API endpoints (拆解、评分、解释)
- Story 11.4: 艾宾浩斯复习系统API
- Story 11.5: 跨Canvas关联API
- Story 11.6: Docker Compose环境配置
```

**问题**:
1. ❌ **Story序列过时**: 列出的6个Story与最新规划完全不同
2. ❌ **缺少详细信息**: 没有Epic目标、关键交付物、API概览、数据模型等
3. ❌ **缺少文档引用**: 没有引用新创建的6个规划文档

---

### ✅ 最新Epic 11规划（应更新为）

**来源**: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`, `docs/SPRINT-KICKOFF-EPIC-11.md`

```markdown
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
```

---

## 📊 主要变更对比

| 方面 | 旧版本（当前PRD） | 新版本（应更新为） |
|------|-----------------|------------------|
| **Story数量** | 6个 | 6个 |
| **Story内容** | 项目初始化、集成canvas_utils、API、复习系统、关联、Docker | 应用初始化、路由系统、依赖注入、中间件、异步操作、API文档 |
| **Epic信息** | 仅技术验证要求和Story列表 | 完整Epic描述、目标、架构、交付物、成功标准 |
| **API Endpoints** | 未定义 | 19个endpoints详细列出 |
| **数据模型** | 未定义 | 31个Pydantic模型详细列出 |
| **架构设计** | 未定义 | 4层架构完整说明 |
| **规划文档引用** | 无 | 引用6个新创建的规划文档 |
| **估算时间** | 未明确 | 30-43小时（2周） |

---

## 🔧 Story序列详细对比

### 旧版本Story序列（当前PRD）❌

1. **Story 11.1**: FastAPI项目初始化和基础配置
2. **Story 11.2**: canvas_utils.py集成到FastAPI
3. **Story 11.3**: 核心API endpoints (拆解、评分、解释)
4. **Story 11.4**: 艾宾浩斯复习系统API
5. **Story 11.5**: 跨Canvas关联API
6. **Story 11.6**: Docker Compose环境配置

**问题**:
- Story 11.2-11.6混合了基础设施、业务功能和部署配置
- 没有明确的技术分层（路由、依赖注入、中间件等）
- Story 11.3-11.5是业务功能（应该在后续Epic中实现）
- 缺少测试框架Story

---

### 新版本Story序列（应更新为）✅

1. **Story 11.1**: FastAPI应用初始化和基础配置 (4-6小时, P0)
   - FastAPI应用实例创建
   - Pydantic Settings配置管理
   - .env环境变量
   - 健康检查endpoint

2. **Story 11.2**: 路由系统和APIRouter配置 (5-7小时, P0)
   - APIRouter模块化路由
   - 路由版本控制 (`/api/v1/`)
   - 路由前缀和tags
   - include_router集成

3. **Story 11.3**: 依赖注入系统设计 (6-8小时, P0)
   - `Depends()`依赖注入
   - 单例配置管理
   - 服务生命周期管理
   - canvas_utils.py集成为依赖服务

4. **Story 11.4**: 中间件和错误处理 (5-7小时, P1)
   - 自定义中间件（日志、CORS）
   - 全局异常处理器
   - HTTPException标准化
   - 错误响应格式统一

5. **Story 11.5**: 异步操作和后台任务 (6-9小时, P1)
   - async/await异步endpoint
   - BackgroundTasks后台任务
   - 异步服务层设计
   - 性能优化

6. **Story 11.6**: API文档和测试框架 (4-6小时, P1)
   - FastAPI自动文档配置（Swagger/ReDoc）
   - pytest测试框架搭建
   - 测试夹具（fixtures）
   - API集成测试

**优势**:
- ✅ 严格遵循技术分层（基础设施 → 架构 → 测试）
- ✅ 每个Story聚焦单一技术关注点
- ✅ P0 Stories (11.1-11.3) 完成后即可开始业务开发
- ✅ 包含完整的测试基础设施（Story 11.6）
- ✅ 业务功能（Agent调用、检验白板等）延后到Epic 12-14

---

## 📝 需要更新的PRD文件位置

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`

**需要替换的行范围**: 第4385-4406行

**替换前内容**（22行）:
```
### Epic 11: FastAPI后端基础架构搭建
⚠️ **技术验证要求**: ...
**强制文档来源**: ...
**验证检查点**: ...
---
**Story序列**:
- Story 11.1: FastAPI项目初始化和基础配置
- Story 11.2: canvas_utils.py集成到FastAPI
- Story 11.3: 核心API endpoints (拆解、评分、解释)
- Story 11.4: 艾宾浩斯复习系统API
- Story 11.5: 跨Canvas关联API
- Story 11.6: Docker Compose环境配置
```

**替换后内容**（约180行）:
完整的Epic 11描述（包含目标、Story列表表格、核心架构、关键交付物、API Endpoints概览、数据模型概览、技术栈、成功标准）

---

## ✅ 更新后的好处

1. **信息完整性**: PRD将包含Epic 11的完整信息，不需要跳转到其他文档
2. **Story清晰性**: 新Story序列更加技术化、模块化
3. **文档一致性**: PRD与详细规划文档保持一致
4. **可追溯性**: 引用所有6个新创建的规划文档
5. **架构可见性**: 在PRD中直接看到4层架构和19个API endpoints

---

## 🚀 建议的更新流程

### 选项A: 手动更新（推荐）

1. 打开 `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
2. 定位到第4385行（`### Epic 11: FastAPI后端基础架构搭建`）
3. 选择第4385-4406行（共22行）
4. 替换为本文档中的"✅ 最新Epic 11规划（应更新为）"部分的完整内容
5. 保存文件

### 选项B: 使用备份恢复（如果需要）

1. 备份当前PRD: `cp docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md.backup`
2. 执行更新
3. 如有问题，从备份恢复

### 选项C: 让SM Agent更新（推荐给非技术用户）

在开始Story 11.1编写前，让SM Agent (Bob) 先更新PRD文件，确保PRD与最新规划一致。

---

## 📌 后续行动

**立即行动**:
- [ ] 更新PRD文件（第4385-4406行）
- [ ] 验证更新后的PRD文档格式正确
- [ ] 确认PRD与`EPIC-11-FASTAPI-BACKEND-DETAILED.md`一致

**SM Agent (Bob) 行动**:
- [ ] 阅读更新后的PRD Epic 11部分
- [ ] 开始编写Story 11.1（基于更新后的PRD和Sprint Kick-off文档）

---

## 📚 相关文档

**新创建的Epic 11规划文档**（全部已完成）:
1. `docs/SPRINT-KICKOFF-EPIC-11.md` - Sprint启动指南
2. `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md` - Epic 11详细规划
3. `docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md` - 技术架构设计
4. `docs/api/EPIC-11-API-SPECIFICATION.md` - API接口规范
5. `docs/architecture/EPIC-11-DATA-MODELS.md` - 数据模型设计
6. `docs/PM-TO-SM-HANDOFF-EPIC-11.md` - PM-SM交接文档

**当前需要更新的文档**:
- `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` (主PRD)

---

**报告创建者**: PM Agent (Sarah)
**报告日期**: 2025-11-13
**状态**: ⚠️ **等待PRD更新**
**下一步**: 更新PRD后，交接给SM Agent (Bob)开始Story编写

---

## 附录：完整替换文本

为了方便更新，以下是完整的替换文本（可以直接复制粘贴）：

```markdown
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
```

**替换说明**:
1. 打开PRD文件
2. 定位到第4385行
3. 选中第4385-4406行（"### Epic 11..." 到 "- Story 11.6: Docker Compose环境配置"）
4. 删除选中内容
5. 粘贴上面的完整替换文本
6. 保存文件

**验证**:
- 确认Epic 12的开头（"### Epic 12: LangGraph多Agent编排系统"）紧跟在Epic 11之后
- 确认文档格式正确（markdown表格、代码块等）
- 确认所有链接指向正确的文档路径
