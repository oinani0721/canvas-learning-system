# 开发指南

> 生成时间: 2026-03-24 | 扫描模式: exhaustive

## 1. 前置要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Node.js | >= 18 | 前端构建 + Sidecar 运行时 |
| npm | >= 9 | 前端包管理 |
| Rust + Cargo | latest stable | Tauri 编译 |
| Python | >= 3.10 | 后端运行时 |
| Docker Desktop | latest | Neo4j + Ollama + Backend 容器 |
| NVIDIA Driver | >= 535 | GPU 加速 Ollama (RTX 4060) |

## 2. 启动流程

### 2.1 后端 (Docker 模式)

```bash
# 1. 进入项目目录
cd canvas-learning-system

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 设置以下关键变量:
#   NEO4J_PASSWORD=<your-password>
#   AI_PROVIDER=google (或 openai/anthropic)
#   GOOGLE_API_KEY=<your-api-key> (如果使用 google)

# 3. 启动所有 Docker 服务
docker compose up -d

# 4. 验证服务健康
curl http://localhost:8001/api/v1/health
# 期望返回: {"status": "healthy", ...}

# 5. 拉取 Ollama 模型 (首次)
docker exec canvas-learning-system-ollama ollama pull bge-m3
docker exec canvas-learning-system-ollama ollama pull qwen3:8b
```

### 2.2 后端 (本地开发模式)

```bash
# 1. 先启动 Neo4j 和 Ollama
docker compose up -d neo4j ollama

# 2. 安装 Python 依赖
cd backend
pip install -r requirements.txt

# 3. 启动 FastAPI (热重载)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2.3 前端

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动 Tauri 开发模式 (含前端 + Rust)
npm run tauri dev

# 前端开发服务器默认在 http://localhost:5173
# Tauri 窗口自动打开
```

## 3. 环境变量

> 完整模板: `backend/.env.example`

### 必需变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NEO4J_URI` | `bolt://localhost:7691` | Neo4j 连接地址 (Docker 映射) |
| `NEO4J_USER` | `neo4j` | Neo4j 用户名 |
| `NEO4J_PASSWORD` | `password` | Neo4j 密码 |
| `AI_PROVIDER` | `google` | AI 提供商 (google/openai/anthropic/custom) |
| `CANVAS_BASE_PATH` | `../笔记库` | Canvas 文件目录路径 |

### AI Provider 配置 (选其一)

| 变量 | 说明 |
|------|------|
| `GOOGLE_API_KEY` | Google Gemini API Key |
| `OPENAI_API_KEY` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key |
| `CUSTOM_API_KEY` + `CUSTOM_API_BASE` | 自定义 OpenAI 兼容 API |

### 可选变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `false` | 调试模式 (启用 Swagger UI) |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CORS_ORIGINS` | (见 .env.example) | CORS 允许的源 |
| `MAX_CONCURRENT_REQUESTS` | `100` | 最大并发请求数 |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 地址 |
| `API_V1_PREFIX` | `/api/v1` | API 前缀 |
| `ENABLE_GRAPHITI_JSON_DUAL_WRITE` | `true` | 启用 JSON 双写降级 |

## 4. 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend (Vite dev) | 5173 | 前端开发服务器 |
| Backend (FastAPI) | 8001 | REST API + MCP + WebSocket |
| Neo4j Browser | 7478 | Neo4j Web 管理界面 |
| Neo4j Bolt | 7691 | Neo4j Bolt 协议连接 |
| Ollama | 11434 | 本地 LLM + Embedding 推理 |

## 5. 测试

### 后端测试

```bash
# 运行所有后端测试
cd backend
pytest tests/ -v

# 运行 src/ legacy 测试
cd ..
pytest src/tests/ -v

# 运行特定测试文件
pytest backend/tests/test_health.py -v
```

### 前端测试

```bash
cd frontend
npm test  # (如配置了 vitest)
```

### 类型检查

```bash
# Python 类型检查
cd backend
pyright app/

# TypeScript 类型检查
cd frontend
npx tsc --noEmit
```

## 6. Lint & Format

### Python

```bash
# Lint 检查
ruff check backend/app/ src/

# 自动修复
ruff check --fix backend/app/ src/

# 格式检查
ruff format --check backend/app/

# 自动格式化
ruff format backend/app/
```

### TypeScript

```bash
cd frontend
npx tsc --noEmit  # 类型检查
```

## 7. Git Hooks (Lefthook)

项目使用 [Lefthook](https://github.com/evilmartians/lefthook) 管理 Git hooks。

### pre-commit

| 检查 | 说明 |
|------|------|
| ruff check | Python lint |
| ruff format --check | Python 格式检查 |
| pyright | Python 类型检查 |

### pre-push

| 检查 | 说明 |
|------|------|
| smoke test | 基础冒烟测试 |

### post-commit

| 动作 | 说明 |
|------|------|
| auto push | 自动推送到 backup 远程仓库 |

## 8. Docker 架构

```
docker-compose.yml
├── neo4j (Neo4j 5.26-community)
│   ├── ports: 7478 (Browser), 7691 (Bolt)
│   ├── volumes: docker/neo4j/data, logs, plugins
│   └── healthcheck: wget http://localhost:7474
├── ollama (ollama/ollama:latest)
│   ├── ports: 11434
│   ├── volumes: docker/ollama/models
│   ├── GPU: NVIDIA all capabilities
│   └── healthcheck: ollama list
└── backend (FastAPI Dockerfile)
    ├── ports: 8001
    ├── depends_on: neo4j (healthy), ollama (healthy)
    ├── volumes: backend/, src/, data/lancedb, vault (ro)
    └── healthcheck: curl http://localhost:8001/api/v1/health
```

### 网络

| 网络 | 说明 |
|------|------|
| `canvas-learning-network` | 内部服务通信 (bridge) |
| `cliproxyapi_default` | 外部网络 (连接代理 API) |

## 9. 常用开发命令

```bash
# 查看 Docker 服务状态
docker compose ps

# 查看服务日志
docker compose logs -f backend
docker compose logs -f neo4j

# 重启后端
docker compose restart backend

# 完全重建
docker compose down && docker compose up -d --build

# Neo4j Cypher Shell
docker exec -it canvas-learning-system-neo4j cypher-shell -u neo4j -p <password>

# Ollama 查看已安装模型
docker exec canvas-learning-system-ollama ollama list
```
