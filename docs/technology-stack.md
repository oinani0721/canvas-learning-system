# 技术栈文档

> Generated: 2026-03-24 | Scan: exhaustive | Mode: initial_scan

## Part: Frontend (Desktop — Tauri+React)

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 运行时 | Tauri 2 | ^2.10.1 | 桌面应用壳，Rust 后端 |
| UI框架 | React | ^19.1.0 | 前端组件框架 |
| 状态管理 | Zustand | ^5.0.12 | 轻量状态管理 |
| 画布引擎 | @xyflow/react (ReactFlow) | ^12.8.2 | 节点图/画布渲染 |
| 样式 | TailwindCSS | ^4.1.8 | 原子化 CSS |
| 构建 | Vite | ^6.3.5 | 开发服务器+打包 |
| 语言 | TypeScript | ~5.8.3 | 类型安全 |
| 本地存储 | Dexie (IndexedDB) | ^4.3.0 | 客户端离线数据 |
| Markdown | react-markdown + rehype-katex + remark-math | ^10.1.0 | LaTeX 公式+Markdown 渲染 |
| Tauri 插件 | @tauri-apps/plugin-fs, plugin-shell | ^2.2.0 | 文件系统+Shell 访问 |
| Rust 后端 | tauri 2, tauri-plugin-shell/fs, serde | 2.x | IPC 桥接+原生能力 |

**架构模式**: Component-based SPA + Tauri IPC 桥接到本地文件系统和 Docker 后端

## Part: Backend (FastAPI Python)

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | FastAPI | >=0.104.0 | REST API 服务 |
| ASGI | Uvicorn | >=0.24.0 | ASGI 服务器 |
| AI/LLM | Anthropic SDK | >=0.40.0 | Claude API 调用 |
| AI/LLM | google-genai | >=0.3.0 | Gemini API (Embedding/LLM) |
| AI/LLM | LiteLLM | >=1.40.0 | 统一 LLM 网关 |
| 向量数据库 | LanceDB | >=0.25.0 | 向量检索 |
| 图数据库 | Neo4j | >=5.18.0 | 知识图谱 |
| 知识图谱 | graphiti-core | >=0.28.2 | 时序图谱 (计划集成) |
| Embedding | FlagEmbedding (bge-m3) | >=1.2.0 | 中英双语 1024d 向量 |
| Agent 框架 | LangGraph | >=0.3.10 | Agentic RAG StateGraph |
| 间隔重复 | FSRS | >=6.0.0,<7.0.0 | 遗忘曲线调度 |
| MCP | fastapi-mcp | >=0.1.0 | MCP Tool 暴露 |
| 数据验证 | Pydantic | >=2.5.0 | 数据模型 |
| 监控 | prometheus-client | >=0.17.0 | 指标收集 |
| 日志 | structlog | >=23.0.0 | 结构化日志 |
| 多模态 | Pillow, PyMuPDF | >=10.0.0 | 图片/PDF 处理 |
| 异步存储 | aiosqlite | >=0.19.0 | 会话历史持久化 |

**架构模式**: Service-oriented API + Agentic RAG pipeline + 多数据库 (Neo4j+LanceDB+SQLite)

## Part: Src-Legacy (Python)

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 核心 | Python 标准库 | 3.x | canvas_utils.py 等 |
| 图谱 | graphiti-core, neo4j | >=0.28.2 | 知识图谱操作 |
| 向量 | LanceDB, FlagEmbedding | >=0.25.0 | RAG 检索 |
| NLP | jieba, sentence-transformers | >=0.42.1 | 中文分词+语义向量 |
| ML | scikit-learn, numpy, pandas | >=1.3.0 | 数据分析 |
| 可视化 | matplotlib, plotly, networkx | >=3.7.0 | 图表+网络图 |

**架构模式**: 脚本式模块集合，部分功能已迁移至 backend/app/

## 基础设施

| 类别 | 技术 | 用途 |
|------|------|------|
| 容器 | Docker Compose | 服务编排 (Neo4j, Backend) |
| CI Hooks | Lefthook | pre-commit lint/typecheck, pre-push smoke test |
| Lint | Ruff | Python lint+format |
| TypeCheck | Pyright | Python 类型检查 |
| 包管理 | npm (前端), pip/uv (后端) | 依赖管理 |
