---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Epic 11: FastAPI后端技术架构设计

**文档类型**: Technical Architecture Document
**Epic**: Epic 11 - FastAPI后端基础架构搭建
**版本**: v1.0
**创建日期**: 2025-11-13
**负责人**: PM Agent (John) + Architect Agent (Morgan)
**状态**: 已批准

---

## 📋 目录

1. [架构概览](#-架构概览)
2. [分层架构设计](#-分层架构设计)
3. [目录结构详解](#-目录结构详解)
4. [核心模块设计](#-核心模块设计)
5. [数据流设计](#-数据流设计)
6. [API路由设计](#-api路由设计)
7. [依赖注入架构](#-依赖注入架构)
8. [错误处理策略](#-错误处理策略)
9. [中间件设计](#-中间件设计)
10. [性能优化方案](#-性能优化方案)
11. [安全考虑](#-安全考虑)
12. [部署架构](#-部署架构)

---

## 🏗️ 架构概览

### 设计原则

#### 1. 分层架构 (Layered Architecture)
将系统分为API层、服务层、核心层和基础设施层，每层职责清晰，降低耦合度。

#### 2. 依赖注入 (Dependency Injection)
使用FastAPI的Depends机制实现依赖注入，提高代码复用性和可测试性。

#### 3. 异步优先 (Async First)
所有I/O操作使用async/await，充分利用Python异步特性提升性能。

#### 4. 单一职责 (Single Responsibility)
每个模块、类、函数只负责一个功能，便于维护和扩展。

#### 5. API版本控制 (API Versioning)
使用URL路径版本控制（/api/v1/），为未来API升级预留空间。

### 整体架构图

```
┌────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Obsidian   │  │  Web Client  │  │Mobile Client │        │
│  │   Plugin     │  │   (Future)   │  │   (Future)   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │ HTTP/REST API                      │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ↓
┌────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                   API Gateway Layer                     │   │
│  │  • CORS Middleware                                      │   │
│  │  • Request Logging                                      │   │
│  │  • Error Handling                                       │   │
│  └──────────────────────────┬─────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼─────────────────────────────┐   │
│  │                    API Layer (v1)                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │   │
│  │  │  Canvas    │  │   Agent    │  │  Review    │      │   │
│  │  │  Endpoints │  │  Endpoints │  │  Endpoints │      │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘      │   │
│  └────────┼───────────────┼───────────────┼─────────────┘   │
│           │               │               │                   │
│  ┌────────▼───────────────▼───────────────▼─────────────┐   │
│  │               Service Layer                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │Canvas Service│  │Agent Service │  │Review Svc│  │   │
│  │  │              │  │              │  │          │  │   │
│  │  │• CRUD ops    │  │• Agent call  │  │• Review  │  │   │
│  │  │• Validation  │  │• Async wrap  │  │  gen     │  │   │
│  │  │• Business    │  │• Result proc │  │• Progress│  │   │
│  │  │  logic       │  │              │  │  track   │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └─────┬────┘  │   │
│  └─────────┼──────────────────┼────────────────┼────────┘   │
│            │                  │                │              │
│  ┌─────────▼──────────────────▼────────────────▼────────┐   │
│  │                   Core Layer                          │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │       canvas_utils.py (3层架构)              │   │   │
│  │  │  • CanvasJSONOperator (JSON操作)            │   │   │
│  │  │  • CanvasBusinessLogic (业务逻辑)           │   │   │
│  │  │  • CanvasOrchestrator (高级API)             │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │  ┌──────────────┐  ┌───────────────┐              │   │
│  │  │  exceptions  │  │   logging     │              │   │
│  │  └──────────────┘  └───────────────┘              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Infrastructure Layer                        │   │
│  │  • Configuration (Settings)                           │   │
│  │  • Logging (Structured logs)                          │   │
│  │  • Error Handling (Global handlers)                   │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                   External Resources                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Canvas     │  │   Agent      │  │    .env      │        │
│  │   Files      │  │   Calls      │  │   Config     │        │
│  │  (.canvas)   │  │ (Claude Code)│  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
```

### 技术栈组件

| 层次 | 组件 | 技术选型 | 职责 |
|------|------|---------|------|
| **网关层** | Web Server | Uvicorn 0.24+ | ASGI服务器，HTTP请求处理 |
| **网关层** | CORS | CORSMiddleware | 跨域资源共享 |
| **网关层** | Logging | Custom Middleware | 请求/响应日志 |
| **API层** | Web Framework | FastAPI 0.104+ | RESTful API框架 |
| **API层** | Data Validation | Pydantic 2.5+ | 请求/响应验证 |
| **服务层** | Business Logic | Python Classes | 业务逻辑封装 |
| **核心层** | Canvas Operations | canvas_utils.py | Canvas 3层架构 |
| **基础设施层** | Configuration | pydantic-settings | 配置管理 |
| **基础设施层** | Logging | Python logging | 结构化日志 |

---

## 📐 分层架构设计

### Layer 1: API层 (app/api/v1/)

**职责**:
- HTTP请求处理
- 请求参数验证（路径、查询、请求体）
- 响应格式化
- API文档生成

**技术**:
- FastAPI路径操作装饰器（@router.get, @router.post等）
- Pydantic模型验证
- OpenAPI schema生成

**设计原则**:
- 薄API层：只做请求/响应转换，不包含业务逻辑
- 所有业务逻辑委托给Service层
- 使用依赖注入获取Service实例

**示例**:
```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: path operations dependency injection
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.canvas import CanvasRead, NodeCreate
from app.services.canvas_service import CanvasService
from app.dependencies import get_canvas_service

router = APIRouter()

@router.get("/{canvas_name}", response_model=CanvasRead)
async def read_canvas(
    canvas_name: str,
    service: CanvasService = Depends(get_canvas_service)
):
    """
    读取Canvas文件

    - **canvas_name**: Canvas文件名（不含.canvas后缀）
    """
    canvas = await service.read_canvas(canvas_name)
    if not canvas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )
    return canvas
```

---

### Layer 2: 服务层 (app/services/)

**职责**:
- 业务逻辑实现
- 数据验证和转换
- 调用核心层API
- 事务管理（如果需要）
- 错误处理和日志

**技术**:
- Python类封装
- 异步方法（async def）
- 依赖注入

**设计原则**:
- 单一职责：每个Service只负责一个业务领域
- 可测试：Service方法易于单元测试
- 无状态：Service实例不保存请求状态
- 使用依赖注入获取配置和核心层实例

**示例**:
```python
# app/services/canvas_service.py
from app.core.canvas_utils import CanvasJSONOperator, CanvasBusinessLogic
from app.config import Settings
from typing import Optional, Dict, Any
import asyncio

class CanvasService:
    """Canvas业务逻辑服务"""

    def __init__(self, canvas_base_path: str):
        self.canvas_base_path = canvas_base_path
        self.operator = CanvasJSONOperator()
        self.logic = CanvasBusinessLogic()

    async def read_canvas(self, canvas_name: str) -> Optional[Dict[str, Any]]:
        """读取Canvas文件（异步）"""
        canvas_path = f"{self.canvas_base_path}/{canvas_name}.canvas"

        # 使用asyncio.to_thread在线程池中运行同步操作
        canvas_data = await asyncio.to_thread(
            self.operator.read_canvas,
            canvas_path
        )

        return canvas_data

    async def add_node(self, canvas_name: str, node_data: Dict) -> Dict:
        """添加节点到Canvas（异步）"""
        canvas_path = f"{self.canvas_base_path}/{canvas_name}.canvas"

        # 读取Canvas
        canvas_data = await self.read_canvas(canvas_name)
        if not canvas_data:
            raise ValueError(f"Canvas '{canvas_name}' not found")

        # 添加节点（在线程池中运行）
        result = await asyncio.to_thread(
            self.operator.add_node,
            canvas_path,
            node_data
        )

        return result

    async def cleanup(self):
        """清理资源"""
        # 释放资源（如果有）
        pass
```

---

### Layer 3: 核心层 (app/core/)

**职责**:
- Canvas文件操作（canvas_utils.py的3层架构）
- 核心算法实现
- 数据持久化
- 无业务逻辑

**技术**:
- canvas_utils.py（已存在）
- CanvasJSONOperator（JSON读写）
- CanvasBusinessLogic（布局、聚类）
- CanvasOrchestrator（Agent调用）

**设计原则**:
- 保持现有canvas_utils.py的3层架构不变
- 只做封装，不做修改
- Service层负责异步转换

---

### Layer 4: 基础设施层

**职责**:
- 配置管理（Settings）
- 日志系统
- 错误处理
- 工具函数

**技术**:
- pydantic-settings（配置）
- Python logging（日志）
- 自定义异常类

---

## 📁 目录结构详解

### 完整目录树

```
backend/
├── app/
│   ├── __init__.py                 # 包初始化
│   ├── main.py                     # FastAPI应用入口 ⭐
│   ├── config.py                   # 配置管理 ⭐
│   ├── dependencies.py             # 全局依赖项 ⭐
│   │
│   ├── api/                        # API层
│   │   ├── __init__.py
│   │   └── v1/                     # API v1版本
│   │       ├── __init__.py
│   │       ├── router.py           # 路由汇总 ⭐
│   │       └── endpoints/          # 各功能endpoints
│   │           ├── __init__.py
│   │           ├── canvas.py       # Canvas操作API ⭐
│   │           ├── agent.py        # Agent调用API
│   │           ├── review.py       # 检验白板API
│   │           └── health.py       # 健康检查 ⭐
│   │
│   ├── models/                     # Pydantic数据模型
│   │   ├── __init__.py
│   │   ├── canvas.py               # Canvas相关模型 ⭐
│   │   ├── agent.py                # Agent请求/响应模型
│   │   ├── review.py               # 检验白板模型
│   │   └── common.py               # 通用模型（Response等）
│   │
│   ├── services/                   # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── canvas_service.py       # Canvas业务逻辑 ⭐
│   │   ├── agent_service.py        # Agent调用服务
│   │   └── review_service.py       # 检验白板服务
│   │
│   ├── core/                       # 核心层
│   │   ├── __init__.py
│   │   ├── canvas_utils.py         # Canvas 3层架构（已存在）⭐
│   │   ├── exceptions.py           # 自定义异常 ⭐
│   │   └── logging.py              # 日志配置 ⭐
│   │
│   └── middleware/                 # 中间件
│       ├── __init__.py
│       ├── logging.py              # 请求日志中间件
│       ├── error_handler.py        # 错误处理中间件
│       └── timing.py               # 性能监控中间件
│
├── tests/                          # 测试
│   ├── __init__.py
│   ├── conftest.py                 # pytest配置 ⭐
│   ├── test_api_v1.py              # API测试
│   ├── test_canvas_service.py      # 服务测试
│   ├── test_dependencies.py        # 依赖注入测试
│   └── test_integration.py         # 集成测试
│
├── .env.example                    # 环境变量示例 ⭐
├── .gitignore                      # Git忽略规则
├── requirements.txt                # 生产依赖 ⭐
├── requirements-dev.txt            # 开发依赖
├── pyproject.toml                  # 项目配置
├── pytest.ini                      # pytest配置
└── README.md                       # 后端文档 ⭐

⭐ = Story 11.1-11.3必须创建的文件
```

### 关键文件说明

#### app/main.py
**职责**: FastAPI应用入口点
**内容**:
- FastAPI实例创建
- 路由注册
- 中间件注册
- 启动/关闭事件
- CORS配置

#### app/config.py
**职责**: 配置管理
**内容**:
- Settings类（继承BaseSettings）
- 环境变量加载
- 配置验证

#### app/dependencies.py
**职责**: 全局依赖项
**内容**:
- get_settings()
- get_canvas_service()
- get_agent_service()
- 其他依赖工厂函数

#### app/api/v1/router.py
**职责**: API路由汇总
**内容**:
- 汇总所有endpoints的router
- 统一注册到主应用

#### app/api/v1/endpoints/canvas.py
**职责**: Canvas操作API
**内容**:
- GET /canvas/{canvas_name}
- POST /canvas/nodes
- PUT /canvas/nodes/{node_id}
- DELETE /canvas/nodes/{node_id}

#### app/models/canvas.py
**职责**: Canvas相关Pydantic模型
**内容**:
- CanvasRead
- NodeCreate
- NodeUpdate
- NodeRead

#### app/services/canvas_service.py
**职责**: Canvas业务逻辑
**内容**:
- read_canvas()
- add_node()
- update_node()
- delete_node()

#### app/core/exceptions.py
**职责**: 自定义异常
**内容**:
- CanvasNotFoundException
- NodeNotFoundException
- ValidationError

---

## 🔧 核心模块设计

### 1. FastAPI应用初始化 (app/main.py)

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: FastAPI application initialization
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import router as api_v1_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.core.logging import setup_logging

# 配置日志
setup_logging(log_level=settings.LOG_LEVEL)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/api/v1/openapi.json"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# 注册路由
app.include_router(api_v1_router, prefix="/api/v1")

# 根路径
@app.get("/")
async def root():
    return {
        "message": "Canvas Learning System API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
```

### 2. 配置管理 (app/config.py)

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: settings configuration BaseSettings
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os

class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    PROJECT_NAME: str = "Canvas Learning System API"
    PROJECT_DESCRIPTION: str = "Multi-agent learning system backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的CORS来源"
    )

    # Canvas配置
    CANVAS_BASE_PATH: str = Field(
        default="../笔记库",
        description="Canvas文件基础路径"
    )

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        description="最大并发请求数"
    )

    @validator("CANVAS_BASE_PATH")
    def validate_canvas_path(cls, v):
        """验证Canvas路径存在"""
        if not os.path.exists(v):
            raise ValueError(f"Canvas base path does not exist: {v}")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

# 创建配置单例
settings = Settings()
```

### 3. 依赖注入 (app/dependencies.py)

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: dependencies Depends
from functools import lru_cache
from typing import AsyncGenerator
from app.config import Settings, settings
from app.services.canvas_service import CanvasService
from app.services.agent_service import AgentService

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return settings

async def get_canvas_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[CanvasService, None]:
    """获取Canvas服务实例（异步依赖）"""
    service = CanvasService(
        canvas_base_path=settings.CANVAS_BASE_PATH
    )
    try:
        yield service
    finally:
        await service.cleanup()

async def get_agent_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[AgentService, None]:
    """获取Agent服务实例（异步依赖）"""
    service = AgentService()
    try:
        yield service
    finally:
        await service.cleanup()
```

---

## 🌊 数据流设计

### 请求处理流程

```
1. 客户端请求
   ↓
2. CORS Middleware (允许跨域)
   ↓
3. Logging Middleware (记录请求)
   ↓
4. Error Handler Middleware (错误捕获)
   ↓
5. FastAPI路由匹配
   ↓
6. 请求验证 (Pydantic模型)
   ↓
7. 依赖注入 (Depends)
   ↓
8. API Layer (endpoint函数)
   ↓
9. Service Layer (业务逻辑)
   ↓
10. Core Layer (canvas_utils.py)
    ↓
11. 文件系统 / Agent调用
    ↓
12. 返回结果到Service Layer
    ↓
13. Service处理结果
    ↓
14. API Layer返回响应
    ↓
15. 响应序列化 (Pydantic)
    ↓
16. Error Handler (如果有错误)
    ↓
17. Logging Middleware (记录响应)
    ↓
18. 返回给客户端
```

### 数据流图

```
┌────────────┐
│   Client   │
└──────┬─────┘
       │ HTTP Request
       ↓
┌────────────────────────┐
│   Middleware Chain     │
│ • CORS                 │
│ • Logging              │
│ • Error Handler        │
└──────┬─────────────────┘
       │
       ↓
┌────────────────────────┐
│   API Endpoint         │
│ • Request Validation   │──→ HTTPException (400)
│ • Dependency Injection │
└──────┬─────────────────┘
       │
       ↓
┌────────────────────────┐
│   Service Layer        │
│ • Business Logic       │──→ ValueError → HTTPException (500)
│ • Data Processing      │
└──────┬─────────────────┘
       │
       ↓
┌────────────────────────┐
│   Core Layer           │
│ • canvas_utils.py      │──→ FileNotFoundError → NotFoundException
│ • Canvas Operations    │
└──────┬─────────────────┘
       │
       ↓
┌────────────────────────┐
│   External Resources   │
│ • Canvas Files         │
│ • Agent Calls          │
└────────────────────────┘
```

---

## 🛣️ API路由设计

### 路由结构

```
/                               # 根路径
/docs                           # Swagger UI (DEBUG模式)
/redoc                          # ReDoc (DEBUG模式)
/api/v1/openapi.json           # OpenAPI schema

/api/v1/                        # API v1前缀
    /health                     # 健康检查
    /canvas/                    # Canvas操作
        GET    /{canvas_name}           # 读取Canvas
        POST   /nodes                   # 添加节点
        PUT    /nodes/{node_id}         # 更新节点
        DELETE /nodes/{node_id}         # 删除节点
        POST   /edges                   # 添加边
        DELETE /edges/{edge_id}         # 删除边

    /agent/                     # Agent调用
        POST   /decompose/basic         # 基础拆解
        POST   /decompose/deep          # 深度拆解
        POST   /score                   # 评分
        POST   /explain/oral            # 口语化解释
        POST   /explain/clarification   # 澄清路径
        POST   /explain/comparison      # 对比表
        POST   /explain/memory          # 记忆锚点
        POST   /explain/four-level      # 四层次解释
        POST   /explain/example         # 例题教学

    /review/                    # 检验白板
        POST   /generate                # 生成检验白板
        GET    /progress/{canvas_name}  # 获取进度
        POST   /sync                    # 同步学习进度
```

### 路由注册示例

```python
# app/api/v1/router.py
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: APIRouter include_router
from fastapi import APIRouter
from app.api.v1.endpoints import canvas, agent, review, health

router = APIRouter()

# Canvas操作
router.include_router(
    canvas.router,
    prefix="/canvas",
    tags=["canvas"],
    responses={404: {"description": "Canvas not found"}}
)

# Agent调用
router.include_router(
    agent.router,
    prefix="/agent",
    tags=["agent"],
    responses={500: {"description": "Agent call failed"}}
)

# 检验白板
router.include_router(
    review.router,
    prefix="/review",
    tags=["review"]
)

# 健康检查
router.include_router(
    health.router,
    tags=["health"]
)
```

---

## 💉 依赖注入架构

### 依赖层次结构

```
Configuration (Settings)
    ↓ (依赖)
Service Instance (CanvasService)
    ↓ (依赖)
API Endpoint Function
```

### 依赖作用域

| 依赖类型 | 作用域 | 生命周期 | 示例 |
|---------|-------|---------|------|
| **配置** | 应用级单例 | 应用启动到关闭 | `get_settings()` |
| **服务** | 请求级 | 单次请求 | `get_canvas_service()` |
| **资源** | 请求级 | 单次请求 | 文件句柄、数据库连接 |

### 依赖注入示例

```python
# 单例依赖（配置）
@lru_cache()
def get_settings() -> Settings:
    return Settings()

# 请求级依赖（服务）
async def get_canvas_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[CanvasService, None]:
    service = CanvasService(settings.CANVAS_BASE_PATH)
    try:
        yield service
    finally:
        await service.cleanup()

# API endpoint使用依赖
@router.get("/{canvas_name}")
async def read_canvas(
    canvas_name: str,
    service: CanvasService = Depends(get_canvas_service),
    settings: Settings = Depends(get_settings)
):
    # service和settings自动注入
    canvas = await service.read_canvas(canvas_name)
    return canvas
```

---

## ⚠️ 错误处理策略

### 异常层次结构

```python
# app/core/exceptions.py
class CanvasException(Exception):
    """Canvas操作基础异常"""
    pass

class CanvasNotFoundException(CanvasException):
    """Canvas文件未找到"""
    pass

class NodeNotFoundException(CanvasException):
    """节点未找到"""
    pass

class ValidationError(CanvasException):
    """数据验证错误"""
    pass

class AgentCallError(Exception):
    """Agent调用错误"""
    pass
```

### 全局异常处理器

```python
# app/middleware/error_handler.py
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: exception handlers
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    CanvasNotFoundException,
    NodeNotFoundException,
    ValidationError
)

def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(CanvasNotFoundException)
    async def canvas_not_found_handler(
        request: Request,
        exc: CanvasNotFoundException
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Canvas not found",
                "detail": str(exc)
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request,
        exc: ValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation error",
                "detail": str(exc)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.DEBUG else "An error occurred"
            }
        )
```

---

## 🛡️ 中间件设计

### 1. 日志中间件

```python
# app/middleware/logging.py
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: middleware custom middleware
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求
        logger.info(f"Request: {request.method} {request.url}")

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应
        logger.info(
            f"Response: {response.status_code} "
            f"({process_time:.3f}s)"
        )

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response
```

### 2. 性能监控中间件

```python
# app/middleware/timing.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录慢请求
        if process_time > 1.0:  # >1秒
            logger.warning(
                f"Slow request: {request.method} {request.url} "
                f"took {process_time:.3f}s"
            )

        return response
```

---

## ⚡ 性能优化方案

### 1. 异步I/O

**策略**: 所有I/O操作使用async/await

```python
# 文件操作异步化
async def read_canvas(self, canvas_name: str):
    canvas_path = f"{self.base_path}/{canvas_name}.canvas"
    # 在线程池中运行同步文件操作
    return await asyncio.to_thread(
        self.operator.read_canvas,
        canvas_path
    )

# Agent调用异步化
async def call_agent(self, agent_name: str, prompt: str):
    # 使用httpx异步HTTP客户端
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_API_URL}/{agent_name}",
            json={"prompt": prompt}
        )
        return response.json()
```

### 2. 后台任务

**策略**: 使用BackgroundTasks处理非阻塞操作

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: BackgroundTasks
from fastapi import BackgroundTasks

@router.post("/review/generate")
async def generate_review_canvas(
    canvas_name: str,
    background_tasks: BackgroundTasks,
    service: ReviewService = Depends(get_review_service)
):
    """生成检验白板（后台任务）"""

    # 立即返回任务ID
    task_id = str(uuid.uuid4())

    # 添加后台任务
    background_tasks.add_task(
        service.generate_review_canvas,
        canvas_name,
        task_id
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Review canvas generation started"
    }
```

### 3. 并发限制

**策略**: 使用asyncio.Semaphore限制并发

```python
# 限制最大并发Agent调用
MAX_CONCURRENT_AGENTS = 5
agent_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)

async def call_agent_limited(agent_name: str, prompt: str):
    async with agent_semaphore:
        return await call_agent(agent_name, prompt)
```

### 4. 响应时间目标

| API类型 | 目标响应时间 | 优化策略 |
|---------|------------|---------|
| **健康检查** | <10ms | 内存操作 |
| **Canvas读取** | <50ms | 异步文件I/O |
| **节点添加** | <100ms | 异步写入 |
| **Agent调用** | <5s | 后台任务 |
| **检验白板生成** | 后台任务 | BackgroundTasks |

---

## 🔒 安全考虑

### 1. 输入验证

**策略**: 使用Pydantic强类型验证

```python
class NodeCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    color: str = Field(None, regex=r"^[1-6]$")
    x: int = Field(..., ge=0, le=10000)
    y: int = Field(..., ge=0, le=10000)
```

### 2. 路径遍历防护

```python
def validate_canvas_name(canvas_name: str) -> str:
    """防止路径遍历攻击"""
    if ".." in canvas_name or "/" in canvas_name:
        raise ValueError("Invalid canvas name")
    return canvas_name
```

### 3. CORS配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 白名单
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 限制方法
    allow_headers=["*"],
)
```

---

## 🚀 部署架构

### 开发环境

```bash
# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
# 使用Gunicorn + Uvicorn workers
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Docker部署（未来）

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**文档状态**: ✅ 完成
**最后更新**: 2025-11-13
**版本**: v1.0
**负责人**: PM Agent (John) + Architect Agent (Morgan)
