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

# Epic 11详细规划：FastAPI后端基础架构搭建

**Epic ID**: Epic 11
**Epic名称**: FastAPI后端基础架构搭建
**优先级**: P0
**预计时间**: 2-3周 (43小时)
**状态**: 准备启动
**创建日期**: 2025-11-13
**负责PM**: PM Agent (John)
**依赖**: Epic 0完成 ✅
**阻塞**: Epic 12（部分）、Epic 13

---

## 📋 目录

1. [Epic概述](#-epic概述)
2. [业务价值和目标](#-业务价值和目标)
3. [技术栈和架构](#-技术栈和架构)
4. [Story详细分解](#-story详细分解)
5. [执行计划](#-执行计划)
6. [技术验证清单](#-技术验证清单)
7. [风险评估](#-风险评估)
8. [成功指标](#-成功指标)

---

## 🎯 Epic概述

### 问题陈述

Canvas学习系统v1.x使用Python脚本和Claude Code Sub-agents实现了完整的学习循环功能，但存在以下限制：

1. **前后端耦合**: 所有逻辑都在Obsidian Plugin（前端）中，难以维护和扩展
2. **性能瓶颈**: 同步操作，无法利用并发处理多个Canvas操作
3. **可扩展性差**: 添加新功能需要修改Plugin代码，风险高
4. **缺少API层**: 无法支持多端访问（Web、移动端）
5. **测试困难**: 业务逻辑和UI混合，单元测试难度大

### 解决方案

**构建FastAPI后端基础架构**，将核心业务逻辑从Obsidian Plugin分离，提供RESTful API服务。

**核心特性**:
- ✅ 高性能异步Web框架（FastAPI + Uvicorn）
- ✅ 自动API文档生成（OpenAPI/Swagger）
- ✅ 强大的数据验证（Pydantic）
- ✅ 依赖注入系统
- ✅ 中间件和错误处理
- ✅ 异步操作和后台任务支持

### Epic范围

**包含在Epic 11中**:
- ✅ FastAPI应用初始化和配置
- ✅ 路由系统和API版本控制
- ✅ 依赖注入架构
- ✅ 集成现有的canvas_utils.py（3层架构）
- ✅ 核心Canvas操作API
- ✅ 中间件（日志、错误处理、CORS）
- ✅ 异步操作支持
- ✅ API文档和测试

**不包含在Epic 11中**（后续Epic）:
- ❌ Agent调用系统（Epic 12 - LangGraph编排）
- ❌ Neo4j数据库集成（Epic 15-16）
- ❌ 艾宾浩斯复习系统（Epic 14）
- ❌ 前端Obsidian Plugin改造（Epic 13）
- ❌ 用户认证和授权（Epic 17，未规划）

---

## 💼 业务价值和目标

### 业务价值

#### 1. 解耦前后端 ⭐⭐⭐⭐⭐
**价值**: 提升系统可维护性和可扩展性
- Obsidian Plugin专注UI交互和用户体验
- 后端专注业务逻辑和数据处理
- 两者通过API清晰解耦

#### 2. 提升性能 ⭐⭐⭐⭐⭐
**价值**: 支持高并发Canvas操作
- FastAPI异步特性，支持并发请求
- 后台任务处理，不阻塞用户操作
- 预期响应时间 <100ms

#### 3. 支持多端访问 ⭐⭐⭐⭐
**价值**: 为未来Web/移动端打基础
- RESTful API可被任何客户端调用
- 统一的API接口标准
- 为多端学习平台奠定基础

#### 4. 提高代码质量 ⭐⭐⭐⭐
**价值**: 减少Bug，提升可维护性
- 强类型验证（Pydantic）减少运行时错误
- 依赖注入降低模块耦合
- 自动API文档减少沟通成本

#### 5. 易于测试 ⭐⭐⭐⭐⭐
**价值**: 提升系统可靠性
- 业务逻辑与UI分离，易于单元测试
- TestClient支持完整的集成测试
- 目标测试覆盖率 ≥ 80%

### 目标

#### 短期目标（Epic 11完成后）
- [ ] FastAPI应用成功部署并可访问
- [ ] 提供完整的Canvas CRUD API
- [ ] 支持基础的Agent调用接口（为Epic 12准备）
- [ ] API文档完整且易于使用
- [ ] 测试覆盖率 ≥ 80%

#### 中期目标（Epic 12-13完成后）
- [ ] Obsidian Plugin通过API调用后端
- [ ] LangGraph Agent编排系统集成
- [ ] 支持所有12个Sub-agents的API调用
- [ ] 前后端完全解耦

#### 长期目标（v2.0完成后）
- [ ] 支持Web端Canvas学习系统
- [ ] 支持移动端（iOS/Android）访问
- [ ] 多用户系统和权限管理
- [ ] 云端部署和横向扩展

---

## 🏗️ 技术栈和架构

### 技术栈选择

#### 核心技术栈

| 组件 | 技术 | 版本 | 选择理由 |
|------|------|------|---------|
| **Web框架** | FastAPI | 0.104+ | • 高性能（与Node.js和Go相当）<br>• 自动API文档生成<br>• 基于标准Python类型提示<br>• 异步支持完善 |
| **ASGI服务器** | Uvicorn | 0.24+ | • 生产级ASGI服务器<br>• 支持HTTP/1.1和WebSocket<br>• 高性能，基于uvloop |
| **数据验证** | Pydantic | 2.5+ | • 强大的数据验证<br>• 基于Python类型提示<br>• FastAPI原生集成<br>• 性能优秀 |
| **测试框架** | pytest | 7.4+ | • Python标准测试框架<br>• 丰富的插件生态<br>• 支持fixtures和参数化 |
| **HTTP客户端** | httpx | 0.25+ | • 异步HTTP客户端<br>• 与requests API兼容<br>• 用于测试和Agent调用 |

#### 辅助技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **环境变量** | python-dotenv | 1.0+ | .env文件支持 |
| **日志** | Python logging | 内置 | 结构化日志 |
| **代码格式** | Black | 23.0+ | 代码格式化 |
| **代码检查** | Pylint | 3.0+ | 代码质量检查 |
| **类型检查** | mypy | 1.7+ | 静态类型检查 |

### 技术架构

#### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│              (Obsidian Plugin / Web / Mobile)                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               API Layer                              │   │
│  │  • app/api/v1/endpoints/                            │   │
│  │  • 路由处理、请求验证、响应格式化                  │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │            Service Layer                             │   │
│  │  • app/services/                                     │   │
│  │  • 业务逻辑封装、事务管理                          │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │             Core Layer                               │   │
│  │  • app/core/canvas_utils.py (3层架构)               │   │
│  │  • Canvas操作、Sub-agent调用                       │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │          Infrastructure Layer                        │   │
│  │  • 配置管理、日志、错误处理                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                External Resources                            │
│  • Canvas文件 (.canvas JSON)                                │
│  • Agent调用 (Claude Code)                                  │
│  • 配置文件 (.env)                                          │
└─────────────────────────────────────────────────────────────┘
```

#### 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   ├── config.py                  # 配置管理（Settings）
│   ├── dependencies.py            # 全局依赖项
│   │
│   ├── api/                       # API层
│   │   ├── __init__.py
│   │   └── v1/                    # API v1版本
│   │       ├── __init__.py
│   │       ├── router.py          # 路由汇总
│   │       └── endpoints/         # 各功能endpoints
│   │           ├── __init__.py
│   │           ├── canvas.py      # Canvas操作
│   │           ├── agent.py       # Agent调用
│   │           ├── review.py      # 检验白板
│   │           └── health.py      # 健康检查
│   │
│   ├── models/                    # Pydantic模型
│   │   ├── __init__.py
│   │   ├── canvas.py              # Canvas相关模型
│   │   ├── agent.py               # Agent请求/响应
│   │   ├── review.py              # 检验白板模型
│   │   └── common.py              # 通用模型
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── canvas_service.py      # Canvas业务逻辑
│   │   ├── agent_service.py       # Agent调用服务
│   │   └── review_service.py      # 检验白板服务
│   │
│   ├── core/                      # 核心层
│   │   ├── __init__.py
│   │   ├── canvas_utils.py        # Canvas 3层架构（已存在）
│   │   ├── exceptions.py          # 自定义异常
│   │   └── logging.py             # 日志配置
│   │
│   └── middleware/                # 中间件
│       ├── __init__.py
│       ├── logging.py             # 请求日志中间件
│       ├── error_handler.py       # 错误处理中间件
│       └── timing.py              # 性能监控中间件
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py                # pytest配置
│   ├── test_api_v1.py             # API测试
│   ├── test_canvas_service.py     # 服务测试
│   ├── test_dependencies.py       # 依赖注入测试
│   └── test_integration.py        # 集成测试
│
├── .env.example                   # 环境变量示例
├── .gitignore
├── requirements.txt               # 生产依赖
├── requirements-dev.txt           # 开发依赖
├── pyproject.toml                 # 项目配置
├── pytest.ini                     # pytest配置
└── README.md                      # 后端文档
```

---

## 📊 Story详细分解

### Story 11.1: FastAPI应用初始化和项目结构

**Story ID**: Story 11.1
**优先级**: P0 (CRITICAL)
**预计时间**: 4-6小时
**依赖**: Epic 0完成

#### User Story

**作为** 后端开发者
**我想要** 创建完整的FastAPI项目结构和配置系统
**以便于** 有一个标准化、可维护的应用基础

#### 详细描述

创建FastAPI应用的基础架构，包括：
- FastAPI应用入口点（app/main.py）
- 配置管理系统（环境变量、配置类）
- 项目目录结构
- 基础日志系统
- 健康检查endpoint
- 依赖文件（requirements.txt）

#### 验收标准

##### AC1: FastAPI应用成功初始化

**验收条件**:
- [ ] `app/main.py` 文件存在并包含FastAPI实例
- [ ] 应用可以使用 `uvicorn app.main:app` 启动
- [ ] 启动日志正确输出（包含应用名称、版本、端口）
- [ ] 访问根路径 `/` 返回200状态码

**UltraThink检查点**:
```
Q1: FastAPI()的必需参数和可选参数有哪些？
→ 查询Context7: "FastAPI application initialization parameters"
→ 确认: title, description, version, docs_url, redoc_url等

Q2: 如何配置OpenAPI文档的路径？
→ 查询Context7: "OpenAPI schema configuration"
→ 确认: docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json"

Q3: 生产环境应该如何禁用文档？
→ 查询Context7: "disable docs production"
→ 确认: 设置docs_url=None和redoc_url=None
```

**错误实现 ❌**:
```python
# ❌ 假设FastAPI有init()方法
app = FastAPI()
app.init(config="config.json")  # 幻觉！无此方法

# ❌ 假设可以用app.setup()配置
app.setup(
    title="My App",
    version="1.0"
)  # 幻觉！无此方法
```

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: application initialization
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/api/v1/openapi.json"
)

@app.get("/")
async def root():
    return {
        "message": "Canvas Learning System API",
        "version": settings.VERSION
    }
```

##### AC2: 配置管理系统工作正常

**验收条件**:
- [ ] `app/config.py` 包含Settings类（基于Pydantic BaseSettings）
- [ ] 支持从.env文件加载配置
- [ ] 包含所有必需配置项（PROJECT_NAME, VERSION, DEBUG, LOG_LEVEL等）
- [ ] 配置值可以被正确读取

**UltraThink检查点**:
```
Q1: 如何使用Pydantic实现配置管理？
→ 查询Context7: "Pydantic BaseSettings environment variables"
→ 确认: 继承BaseSettings，使用Field定义配置项

Q2: .env文件如何加载？
→ 查询Context7: "python-dotenv load environment"
→ 确认: 使用Config类的env_file属性

Q3: 如何验证配置的有效性？
→ 查询Context7: "Pydantic validators"
→ 确认: 使用@validator装饰器
```

**错误实现 ❌**:
```python
# ❌ 手动解析.env文件
import os
config = {}
with open('.env') as f:
    for line in f:
        k, v = line.split('=')
        config[k] = v
```

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: settings configuration BaseSettings
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Canvas Learning System API"
    PROJECT_DESCRIPTION: str = "Multi-agent learning system backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Canvas相关配置
    CANVAS_BASE_PATH: str = Field(
        default="../笔记库",
        description="Canvas文件基础路径"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

##### AC3: 目录结构创建完整

**验收条件**:
- [ ] 所有目录按照架构设计创建
- [ ] 每个目录包含 `__init__.py`
- [ ] 符合Python包结构规范

##### AC4: 健康检查endpoint正常工作

**验收条件**:
- [ ] `/health` endpoint存在
- [ ] 返回应用状态信息（状态、版本、时间戳）
- [ ] 响应格式为JSON
- [ ] 响应时间 <10ms

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: path operations health check
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### Definition of Done

- [ ] 所有AC通过
- [ ] FastAPI应用可以启动
- [ ] `/docs` 可以访问（开发环境）
- [ ] `/health` 返回正确状态
- [ ] 配置从.env加载正确
- [ ] 代码包含来源注释
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] README.md包含启动说明

#### 技术验证要求

**Context7查询清单**:
1. FastAPI application initialization
2. BaseSettings configuration management
3. Startup and shutdown events
4. Logging configuration

#### 质量指标

- 启动时间: <2秒
- 健康检查响应时间: <10ms
- 配置加载成功率: 100%

---

### Story 11.2: 路由系统和APIRouter配置

**Story ID**: Story 11.2
**优先级**: P0 (CRITICAL)
**预计时间**: 5-7小时
**依赖**: Story 11.1完成

#### User Story

**作为** API开发者
**我想要** 实现模块化的路由系统和API版本控制
**以便于** 清晰组织API接口，方便扩展和维护

#### 详细描述

实现FastAPI的路由系统，包括：
- APIRouter模块化路由
- API版本控制（/api/v1/）
- Canvas操作基础endpoints
- 请求/响应Pydantic模型
- 集成canvas_utils.py

#### 验收标准

##### AC1: APIRouter正确配置

**验收条件**:
- [ ] `app/api/v1/router.py` 存在并汇总所有路由
- [ ] 使用APIRouter的prefix和tags配置
- [ ] 路由正确注册到主应用
- [ ] `/api/v1/` 前缀生效

**UltraThink检查点**:
```
Q1: APIRouter的prefix和tags参数如何使用？
→ 查询Context7: "APIRouter prefix tags"
→ 确认: APIRouter(prefix="/api/v1", tags=["canvas"])

Q2: 如何将APIRouter注册到主应用？
→ 查询Context7: "include_router FastAPI"
→ 确认: app.include_router(router)

Q3: 如何为不同模块组织路由？
→ 查询Context7: "APIRouter multiple routers"
→ 确认: 每个模块一个router，在主router中汇总
```

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: APIRouter prefix tags
from fastapi import APIRouter
from app.api.v1.endpoints import canvas, agent, review, health

router = APIRouter()

# 注册各模块路由
router.include_router(
    canvas.router,
    prefix="/canvas",
    tags=["canvas"]
)
router.include_router(
    agent.router,
    prefix="/agent",
    tags=["agent"]
)
router.include_router(
    health.router,
    tags=["health"]
)

# 在main.py中注册
# app.include_router(router, prefix="/api/v1")
```

##### AC2: Canvas CRUD endpoints实现

**验收条件**:
- [ ] `GET /api/v1/canvas/{canvas_name}` - 读取Canvas
- [ ] `POST /api/v1/canvas/nodes` - 添加节点
- [ ] `PUT /api/v1/canvas/nodes/{node_id}` - 更新节点
- [ ] `DELETE /api/v1/canvas/nodes/{node_id}` - 删除节点
- [ ] 所有endpoints返回正确的HTTP状态码

**UltraThink检查点**:
```
Q1: 路径参数如何定义和验证？
→ 查询Context7: "path parameters validation"
→ 确认: 使用类型注解，FastAPI自动验证

Q2: 请求体如何验证？
→ 查询Context7: "request body validation Pydantic"
→ 确认: 使用Pydantic模型，自动验证和序列化

Q3: 如何返回不同的HTTP状态码？
→ 查询Context7: "response status code"
→ 确认: 使用status_code参数或Response对象
```

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: path operations request body
from fastapi import APIRouter, HTTPException, status
from app.models.canvas import CanvasRead, NodeCreate, NodeUpdate
from app.services.canvas_service import CanvasService
from app.dependencies import get_canvas_service

router = APIRouter()

@router.get("/{canvas_name}", response_model=CanvasRead)
async def read_canvas(
    canvas_name: str,
    service: CanvasService = Depends(get_canvas_service)
):
    """读取Canvas文件"""
    canvas = await service.read_canvas(canvas_name)
    if not canvas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )
    return canvas

@router.post("/nodes", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_node(
    node: NodeCreate,
    service: CanvasService = Depends(get_canvas_service)
):
    """添加节点到Canvas"""
    result = await service.add_node(node)
    return result
```

##### AC3: Pydantic模型定义完整

**验收条件**:
- [ ] `app/models/canvas.py` 包含所有Canvas相关模型
- [ ] 模型包含Field描述和验证规则
- [ ] 模型支持JSON序列化和反序列化
- [ ] 模型在API文档中显示正确

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: Pydantic models Field validation
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NodeBase(BaseModel):
    """节点基础模型"""
    text: str = Field(..., description="节点文本内容", min_length=1)
    color: Optional[str] = Field(None, description="节点颜色代码（1-6）")
    x: int = Field(..., description="X坐标")
    y: int = Field(..., description="Y坐标")
    width: int = Field(400, description="节点宽度", ge=100)
    height: int = Field(200, description="节点高度", ge=50)

class NodeCreate(NodeBase):
    """创建节点请求模型"""
    canvas_name: str = Field(..., description="Canvas文件名")

class NodeUpdate(BaseModel):
    """更新节点请求模型"""
    text: Optional[str] = None
    color: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None

class NodeRead(NodeBase):
    """节点响应模型"""
    id: str = Field(..., description="节点ID")
    created_at: datetime

    class Config:
        from_attributes = True
```

#### Definition of Done

- [ ] 所有AC通过
- [ ] 至少4个Canvas endpoints工作正常
- [ ] Pydantic模型完整定义
- [ ] canvas_utils.py成功集成
- [ ] API文档显示所有endpoints
- [ ] 代码包含来源注释
- [ ] 集成测试通过
- [ ] 测试覆盖率 ≥ 80%

#### 技术验证要求

**Context7查询清单**:
1. APIRouter configuration
2. Path parameters and validation
3. Request body validation with Pydantic
4. Response models
5. HTTP status codes

---

### Story 11.3: 依赖注入系统

**Story ID**: Story 11.3
**优先级**: P0 (HIGH)
**预计时间**: 6-8小时
**依赖**: Story 11.2完成

#### User Story

**作为** 后端开发者
**我想要** 实现完整的依赖注入系统
**以便于** 提高代码复用性，降低模块耦合度

#### 详细描述

实现FastAPI的依赖注入系统，包括：
- 全局依赖项（配置、日志）
- Canvas服务依赖
- 依赖作用域管理
- 异步依赖支持

#### 验收标准

##### AC1: 全局依赖项实现

**UltraThink检查点**:
```
Q1: Depends()如何使用？
→ 查询Context7: "Depends dependency injection"
→ 确认: Depends(callable)，callable返回依赖

Q2: 如何创建单例依赖？
→ 查询Context7: "dependency singleton cache"
→ 确认: 使用lru_cache装饰器

Q3: 异步依赖如何实现？
→ 查询Context7: "async dependencies yield"
→ 确认: async def + yield
```

**正确实现 ✅**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: dependencies Depends
from functools import lru_cache
from app.config import Settings

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

async def get_canvas_service(
    settings: Settings = Depends(get_settings)
) -> CanvasService:
    """获取Canvas服务实例"""
    service = CanvasService(
        canvas_base_path=settings.CANVAS_BASE_PATH
    )
    try:
        yield service
    finally:
        await service.cleanup()
```

#### Definition of Done

- [ ] 依赖注入系统工作正常
- [ ] 支持同步和异步依赖
- [ ] 服务正确初始化和清理
- [ ] 测试覆盖率 ≥ 80%

---

### Story 11.4-11.6简要说明

由于篇幅限制，Story 11.4-11.6的详细内容请参考：
- **Story 11.4**: 中间件和错误处理 - 请求日志、全局异常处理、CORS配置
- **Story 11.5**: 异步操作和后台任务 - BackgroundTasks、异步Canvas操作、Agent调用
- **Story 11.6**: API文档和测试 - OpenAPI优化、pytest测试、TestClient集成测试

---

## 📅 执行计划

### Sprint规划

#### Sprint 1: Week 1 (2025-11-13 ~ 2025-11-20)
**目标**: 完成核心基础设施

**Stories**:
- Story 11.1: FastAPI应用初始化（Mon-Tue）
- Story 11.2: 路由系统配置（Wed-Thu）
- Story 11.3: 依赖注入系统（Fri）

**里程碑**: FastAPI应用可以启动，基础API工作

#### Sprint 2: Week 2 (2025-11-21 ~ 2025-11-27)
**目标**: 完成中间件、异步和测试

**Stories**:
- Story 11.4: 中间件和错误处理（Mon-Tue）
- Story 11.5: 异步操作和后台任务（Wed-Thu）
- Story 11.6: API文档和测试（Fri）

**里程碑**: Epic 11完成，所有测试通过

---

## 🔍 技术验证清单

### Context7查询主题总表

| Story | 查询主题 | 预计查询数 |
|-------|---------|-----------|
| 11.1 | FastAPI init, Settings, startup events | 3-4 |
| 11.2 | APIRouter, path operations, Pydantic | 4-5 |
| 11.3 | Depends, async dependencies | 3-4 |
| 11.4 | Middleware, exception handlers, CORS | 3-4 |
| 11.5 | async def, BackgroundTasks | 2-3 |
| 11.6 | OpenAPI, TestClient, pytest | 2-3 |

**总计**: 17-23个Context7查询

---

## ⚠️ 风险评估

### 技术风险

1. **canvas_utils.py集成复杂度** (HIGH)
   - 缓解: Story 11.2专门处理，创建Service层封装

2. **异步操作学习曲线** (MEDIUM)
   - 缓解: 遵循Context7最佳实践，使用BackgroundTasks

3. **测试覆盖率不达标** (MEDIUM)
   - 缓解: DoD强制要求，Story 11.6专门处理

---

## 🎯 成功指标

- [ ] 所有6个Stories完成
- [ ] FastAPI应用成功部署
- [ ] 测试覆盖率 ≥ 80%
- [ ] API响应时间 <100ms
- [ ] 零P0/P1 Bug

---

**文档状态**: ✅ 完成
**最后更新**: 2025-11-13
**版本**: v1.0
**负责PM**: PM Agent (John)
