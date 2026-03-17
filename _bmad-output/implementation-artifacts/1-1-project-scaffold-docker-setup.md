# Story 1.1: 项目脚手架与 Docker 环境搭建

Status: ready-for-dev

## Story

As a 开发者,
I want 搭建 Obsidian 插件项目结构（Svelte 5 + esbuild + TypeScript）和 Docker Compose 环境（Neo4j + FastAPI + Ollama），
so that 后续所有 Story 有可运行的基础环境。

## Acceptance Criteria

1. **AC-1: Docker Compose 三容器启动**
   - **Given** 开发者克隆项目仓库
   - **When** 执行 `docker-compose up`
   - **Then** Neo4j、FastAPI、Ollama 三个容器正常启动，各自通过健康检查
   - **And** Neo4j 可通过 `localhost:7476`（HTTP）/ `localhost:7689`（Bolt）访问
   - **And** FastAPI 可通过 `localhost:8001` 访问
   - **And** Ollama 可通过 `localhost:11434` 访问
   - **And** 容器间通过 `canvas-learning-network` 内网通信

2. **AC-2: FastAPI 健康检查端点**
   - **Given** FastAPI 容器正常运行
   - **When** 前端或开发者请求 `GET /api/v1/system/health`
   - **Then** 返回 HTTP 200 及 JSON 健康状态（包含 Neo4j/Ollama/LanceDB 连通性检测结果）

3. **AC-3: Obsidian 插件加载并显示图标**
   - **Given** Obsidian v1.4+ 安装了本插件
   - **When** Obsidian 启动并加载插件
   - **Then** 侧边栏 Ribbon 区域出现 Canvas Learning System 图标
   - **And** 点击图标在右侧面板打开主视图（MainView，ItemView 子类）
   - **And** 插件启动 < 3s（NFR-PERF-07）

4. **AC-4: 前端可访问后端健康检查**
   - **Given** 插件已加载且 Docker 容器已启动
   - **When** 插件初始化时调用 `http://localhost:8001/api/v1/system/health`
   - **Then** 返回 200 且插件内部标记后端为"在线"状态
   - **And** 后端不可达时标记为"离线"状态

5. **AC-5: 项目结构符合架构规范**
   - **Given** 项目根目录
   - **When** 检查文件结构
   - **Then** 前端目录结构：`obsidian-canvas-learning/src/{components,stores,services,views,utils,types}/`
   - **And** 后端目录结构：`backend/app/{api,services,models,core,db,mcp}/`
   - **And** Docker 配置：`backend/docker-compose.yml`（或根目录，保持现有路径）
   - **And** 所有命名遵循架构文档规范（Python snake_case, TS camelCase/PascalCase, CSS cl- 前缀）

6. **AC-6: 开发工具链可用**
   - **Given** 前端项目目录
   - **When** 执行 `npm run build`
   - **Then** esbuild + esbuild-svelte 成功构建出 `main.js`
   - **And** TypeScript 编译无错误
   - **And** 构建产物可被 Obsidian 加载

## Tasks / Subtasks

- [ ] **Task 1: 扩展 Docker Compose 配置** (AC: #1, #2)
  - [ ] 1.1 在现有 `docker-compose.yml` 中新增 FastAPI service（基于 `backend/Dockerfile`，端口 8001，depends_on neo4j healthy + ollama healthy）
  - [ ] 1.2 在现有 `docker-compose.yml` 中新增 Ollama service（镜像 `ollama/ollama`，端口 11434，GPU passthrough 可选，健康检查 `curl localhost:11434`）
  - [ ] 1.3 配置 Ollama 启动后自动拉取 bge-m3 模型（entrypoint 脚本或 init 容器）
  - [ ] 1.4 确保三个 service 都在 `canvas-network` 网络中
  - [ ] 1.5 添加 `.env.example` 包含所有可配置环境变量（NEO4J_PASSWORD, FASTAPI_PORT, OLLAMA_HOST 等）

- [ ] **Task 2: FastAPI 后端骨架与健康检查** (AC: #2)
  - [ ] 2.1 确认 `backend/app/main.py` 存在并可启动（已有则检查/适配）
  - [ ] 2.2 创建 `backend/app/api/v1/system.py`：`GET /api/v1/system/health` 端点，检测 Neo4j（Bolt 连接）、Ollama（HTTP /api/tags）、LanceDB（目录存在）
  - [ ] 2.3 创建 `backend/app/core/config.py`：Pydantic Settings 集中管理配置（NEO4J_URI, OLLAMA_HOST 等）
  - [ ] 2.4 创建 `backend/app/core/dependencies.py`：FastAPI 依赖注入占位
  - [ ] 2.5 确认 `backend/app/models/` 目录存在，创建健康检查响应模型 `HealthResponse(BaseModel)`
  - [ ] 2.6 确认 `backend/requirements.txt` 包含必要依赖（fastapi, uvicorn, neo4j, pydantic-settings, aiosqlite, litellm, lancedb）
  - [ ] 2.7 创建 `backend/Dockerfile`（如不存在）：Python 3.11-slim, pip install requirements.txt, uvicorn 启动

- [ ] **Task 3: 前端 Obsidian 插件骨架** (AC: #3, #5, #6)
  - [ ] 3.1 创建 `obsidian-canvas-learning/` 目录结构：
    ```
    obsidian-canvas-learning/
    ├── manifest.json          (minAppVersion: "1.4.0")
    ├── package.json           (svelte 5, esbuild, typescript)
    ├── tsconfig.json
    ├── esbuild.config.mjs
    ├── svelte.config.js
    ├── styles.css             (cl- 前缀基础样式 + Obsidian CSS 变量映射)
    ├── main.ts                (Plugin 入口: onload/onunload + ItemView 注册)
    └── src/
        ├── components/
        │   ├── chat/          (空目录占位)
        │   ├── exam/
        │   ├── dashboard/
        │   ├── profile/
        │   ├── canvas/
        │   ├── system/
        │   └── global/
        ├── stores/
        ├── services/
        │   └── api-client.ts  (基础 REST 封装 + snake↔camelCase 转换)
        ├── views/
        │   └── main-view.ts   (ItemView 子类, Svelte mount/unmount)
        ├── utils/
        └── types/
            └── api.d.ts       (HealthResponse 类型定义)
    ```
  - [ ] 3.2 编写 `manifest.json`：id `canvas-learning-system`, minAppVersion `1.4.0`
  - [ ] 3.3 编写 `main.ts`：继承 `Plugin`，onload 注册 Ribbon icon + MainView，onunload 清理
  - [ ] 3.4 编写 `src/views/main-view.ts`：继承 `ItemView`，Svelte 5 `mount()` / `unmount()` 挂载空白占位组件
  - [ ] 3.5 编写 `src/services/api-client.ts`：基础 HTTP 封装，`checkHealth()` 方法调用后端健康检查
  - [ ] 3.6 编写 `esbuild.config.mjs`：配置 esbuild-svelte + svelte-preprocess + TypeScript
  - [ ] 3.7 编写 `package.json`：含 build/dev/typecheck scripts

- [ ] **Task 4: 前端连接后端健康检查** (AC: #4)
  - [ ] 4.1 在 `main.ts` 的 `onload` 中调用 `api-client.checkHealth()` 检测后端状态
  - [ ] 4.2 后端可达时 console.log + 设置内部状态 `backendOnline = true`
  - [ ] 4.3 后端不可达时 console.warn + 设置 `backendOnline = false`（不阻塞插件加载）
  - [ ] 4.4 使用 Obsidian `Notice` 组件显示连接状态（非模态，3秒自动消失）

- [ ] **Task 5: 后端目录结构补全** (AC: #5)
  - [ ] 5.1 确认并补全 `backend/app/` 下的标准子目录：`api/v1/`, `services/`, `models/`, `core/`, `db/`, `mcp/`, `middleware/`, `audit/`
  - [ ] 5.2 在各子目录创建 `__init__.py`
  - [ ] 5.3 创建 `backend/tests/unit/` 和 `backend/tests/integration/` 目录结构
  - [ ] 5.4 创建 `backend/prompts/` 和 `backend/scripts/` 目录

- [ ] **Task 6: 验证与文档** (AC: #1-#6)
  - [ ] 6.1 本地执行 `docker-compose up` 验证三容器启动
  - [ ] 6.2 `curl http://localhost:8001/api/v1/system/health` 验证 200 响应
  - [ ] 6.3 前端 `npm run build` 成功
  - [ ] 6.4 Obsidian 中加载插件验证 Ribbon 图标 + MainView 打开
  - [ ] 6.5 运行 `ruff check backend/app/` 确认 lint 通过
  - [ ] 6.6 运行 TypeScript 编译确认无错误

## Dev Notes

### Brownfield 上下文

这是一个 **Brownfield 项目**，已有部分代码基础：
- `docker-compose.yml` 已存在，当前只有 Neo4j service（端口 7476/7689，已配置避免与其他项目冲突）
- `backend/` 已存在，包含已有的 `app/` 目录（含 api, services, agentic_rag, memory 等子目录）
- `src/` 已存在，但这是旧的后端代码目录，**不是前端目录**
- 前端 Obsidian 插件目录 `obsidian-canvas-learning/` 需要**新建**
- 根目录 `package.json` 是 monorepo 工具配置，不是前端插件的

### 已有 Docker Compose 适配

现有 `docker-compose.yml` 使用：
- Neo4j 5.26-community，端口 **7476:7474**（HTTP）和 **7689:7687**（Bolt）
- 网络 `canvas-learning-network`
- 数据持久化到 `./docker/neo4j/{data,logs,plugins}`

新增 FastAPI 和 Ollama service 时：
- **保持现有 Neo4j 配置不变**
- FastAPI 端口 `8001`（避免与常见服务冲突）
- Ollama 端口 `11434`（默认端口）
- 所有 service 加入同一 `canvas-network`

### 技术栈与版本

| 组件 | 版本要求 | 来源 |
|------|---------|------|
| Obsidian | v1.4+ | NFR-COMPAT-01 |
| Svelte | 5.x（mount/unmount API） | Architecture - Frontend |
| esbuild | 最新稳定版 | Architecture - Build |
| esbuild-svelte | 最新稳定版（Svelte 5 兼容） | Architecture - Build |
| TypeScript | 5.x | Architecture - Frontend |
| Python | 3.11+（Docker 容器内） | NFR-COMPAT-04 |
| FastAPI | 最新稳定版 | Architecture - Backend |
| Neo4j | 5.x Community | NFR-COMPAT 已配置 5.26 |
| Ollama | 0.3+ | NFR-COMPAT |
| LanceDB | 0.4+ | NFR-RET-COMPAT-02 |
| Docker Compose | v3.8 语法 | 现有配置 |

### 关键架构约束

1. **前端入口**：`main.ts` 继承 `obsidian.Plugin`，使用 `registerView` 注册 `ItemView`
2. **Svelte 5 挂载**：在 `ItemView.onOpen` 中使用 `mount(Component, { target: containerEl })`，在 `onClose` 中使用 `unmount()`
3. **CSS 隔离**：所有自定义 CSS 类名使用 `cl-` 前缀，Svelte scoped CSS，引用 Obsidian CSS 变量
4. **FastAPI 端口**：8001（前端硬编码 `localhost:8001`，后续通过设置面板可配置）
5. **manifest.json 的 `minAppVersion`**：必须设为 `1.4.0`（非 0.15.0）
6. **Python 依赖**：使用 `requirements.txt`（非 pyproject.toml 管理运行时依赖）
7. **API 响应格式**：`{"data": {...}, "meta": {"timestamp": "..."}}` / `{"error": {"code": "...", "message": "..."}}`
8. **前后端分离**：前端在 `obsidian-canvas-learning/`，后端在 `backend/`，互不侵入

### 命名规范速查

- Python 文件名：`snake_case.py`（如 `health_monitor.py`）
- Python 函数/变量：`snake_case`
- Python 类名：`PascalCase`
- Python API 端点：`/api/v1/snake_case_plural`
- TypeScript 组件文件：`PascalCase.svelte`
- TypeScript store 文件：`kebab-case.svelte.ts`
- TypeScript 工具文件：`kebab-case.ts`
- CSS 类名：`cl-kebab-case`

### 不做的事项（防蔓延）

- 不实现 SetupWizard（Story 1.2）
- 不实现 Settings Tab / 模型配置（Story 1.3）
- 不实现 Canvas 白板渲染（Story 1.4）
- 不实现 IndexedDB / Dexie 初始化（Story 1.4/1.5）
- 不实现 WebSocket 连接（后续 Story）
- 不实现 MCP Server 暴露（Story 3.2）
- 不创建 Svelte 组件内容（仅创建目录结构占位）
- 不实现 LiteLLM 配置（Story 1.3）

### FastAPI 健康检查实现指引

```python
# backend/app/api/v1/system.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/system", tags=["system"])

class ComponentStatus(BaseModel):
    name: str
    status: str  # "healthy" | "unhealthy" | "unknown"
    message: str | None = None

class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    components: list[ComponentStatus]
    timestamp: str

@router.get("/health")
async def health_check() -> dict:
    components = []
    # 检测 Neo4j（Bolt 连接测试）
    # 检测 Ollama（GET http://ollama:11434/api/tags）
    # 检测 LanceDB（检查数据目录是否存在）
    overall = "healthy" if all(c.status == "healthy" for c in components) else "degraded"
    return {
        "data": HealthResponse(
            status=overall,
            components=components,
            timestamp=datetime.utcnow().isoformat() + "Z"
        ).model_dump(),
        "meta": {"timestamp": datetime.utcnow().isoformat() + "Z"}
    }
```

### 前端 main.ts 实现指引

```typescript
// obsidian-canvas-learning/main.ts
import { Plugin, WorkspaceLeaf } from 'obsidian';
import { MainView, VIEW_TYPE_CANVAS_LEARNING } from './src/views/main-view';

export default class CanvasLearningPlugin extends Plugin {
    async onload() {
        // 注册视图
        this.registerView(VIEW_TYPE_CANVAS_LEARNING, (leaf) => new MainView(leaf));

        // Ribbon 图标
        this.addRibbonIcon('graduation-cap', 'Canvas Learning System', () => {
            this.activateView();
        });

        // 初始化时检测后端
        this.checkBackendHealth();
    }

    async onunload() {
        // 清理
    }

    async activateView() {
        const { workspace } = this.app;
        let leaf = workspace.getLeavesOfType(VIEW_TYPE_CANVAS_LEARNING)[0];
        if (!leaf) {
            leaf = workspace.getRightLeaf(false)!;
            await leaf.setViewState({ type: VIEW_TYPE_CANVAS_LEARNING, active: true });
        }
        workspace.revealLeaf(leaf);
    }

    private async checkBackendHealth() {
        // 调用 api-client.checkHealth()
    }
}
```

### Project Structure Notes

- 前端 `obsidian-canvas-learning/` 是**全新目录**，需要完整创建
- 后端 `backend/app/` 是**已有目录**，需要检查现有结构并补全缺失的子目录（`api/v1/`, `core/`, `db/`, `mcp/`, `middleware/`, `audit/`）
- 已有的 `src/` 目录是旧后端代码（`agentic_rag`, `api`, `canvas` 等），**不是前端代码**——前端目录命名为 `obsidian-canvas-learning/` 以明确区分
- 根目录 `package.json` 只管 monorepo 工具（lefthook, commitlint），不管前端构建

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation] — 技术栈选型表
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries] — 完整目录结构
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — 命名规范
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment] — Docker Compose 配置
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — REST 端点前缀
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — 版本兼容性 + 启动顺序
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1] — Story 需求和 AC
- [Source: docker-compose.yml] — 现有 Neo4j Docker 配置（端口 7476/7689）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
